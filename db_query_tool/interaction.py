"""交互层：自然语言触发导出 + 交互式查询 REPL。

对应作业功能要求第 3 点（用户交互）。

与参考项目的差异（效果不同）：
  - 参考在查询后只问 "y / csv / json / n"，交互很窄；
  - 本作业支持**自然语言意图识别**：用户可以用中文或英文说
    "导出csv"、"生成报表"、"全部导出"、"export json" 等，
    REPL 解析出要的格式并一次性导出，无需记忆命令参数。
  - 还提供一键快捷键：输入 `e` 直接导出全部格式。
"""

from __future__ import annotations

import os

from . import config, database, exporter

BANNER = """
╔══════════════════════════════════════════════════════════════╗
║   aj_report 智能查询与导出工具 · CLI 模式 · 已集成导出       ║
║   数据源：本地 MySQL 库 aj_report（只读）                    ║
╚══════════════════════════════════════════════════════════════╝
输入 SQL 查询；查询后可用自然语言导出，例如：
  「导出csv」「生成报表」「export json」「全部导出」
其它指令：tables 看表 ｜ e 一键导出全部 ｜ exit 退出
（Web 页面操作请用：python run.py）
"""

# 自然语言 → 格式映射（关键词命中即导出对应格式）
FORMAT_KEYWORDS = {
    "csv": ["csv", "表格", "excel"],
    "json": ["json", "接口", "程序"],
    "html": ["html", "网页", "报表", "报告", "可视化", "report"],
}
ALL_KEYWORDS = ["全部", "all", "都导出", "三种", "所有格式"]


def _parse_export_intent(text: str) -> list[str] | None:
    """把一句自然语言解析成要导出的格式列表；无导出意图返回 None。

    例：
      "导出csv"          -> ["csv"]
      "生成报表"         -> ["html"]
      "全部导出"         -> ["csv","json","html"]
      "export json"      -> ["json"]
      "随便看看"         -> None
    """
    low = text.lower()
    if any(k in low for k in ALL_KEYWORDS):
        return list(exporter.ALL_FORMATS)

    wanted: list[str] = []
    for fmt, kws in FORMAT_KEYWORDS.items():
        if any(k in low for k in kws):
            wanted.append(fmt)
    return wanted or None


def _do_export(result, formats: list[str]) -> None:
    """执行导出（自动落到 exports 目录）。"""
    os.makedirs(config.EXPORT_DIR, exist_ok=True)
    for fmt in formats:
        out_path = os.path.join(config.EXPORT_DIR, exporter.suggest_filename(fmt))
        path = exporter.export(result, fmt, out_path)
        print(f"[助手] ✅ 已导出 {fmt.upper()}：{path}（{result.row_count} 行）")


def _ask_export(result) -> None:
    """查询后主动询问，并支持自然语言触发。"""
    print()
    print(exporter.preview(result))
    print(f"\n[助手] 本次查询返回 {result.row_count} 行。")
    print("[助手] 需要导出吗？可以说「导出csv / 生成报表 / export json / 全部导出」，"
          "或输入 e 一键导出全部，n 跳过。")
    choice = input(">>> ").strip()
    if not choice:
        return
    low = choice.lower()

    if low in ("n", "no", "否", "不用", "跳过", "skip"):
        print("[助手] 已跳过导出。")
        return
    if low in ("e", "export", "全部", "all"):
        formats = list(exporter.ALL_FORMATS)
    else:
        formats = _parse_export_intent(choice)
        if not formats:
            print("[助手] 没听懂你的格式，默认导出全部格式。")
            formats = list(exporter.ALL_FORMATS)

    _do_export(result, formats)


def run_interactive() -> None:
    """交互式查询循环（CLI 入口）。"""
    print(BANNER)
    try:
        tables = database.list_tables()
        print("可用表：", ", ".join(tables))
    except Exception as exc:  # noqa: BLE001
        print(f"[警告] 无法列出表（请确认 MySQL/aj_report 可用）：{exc}")
    print()
    while True:
        try:
            sql = input("SQL> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n再见。")
            break
        if not sql:
            continue
        if sql.lower() in ("exit", "quit", "q", "退出"):
            print("再见。")
            break
        if sql.lower() == "tables":
            try:
                print("可用表：", ", ".join(database.list_tables()))
            except Exception as exc:  # noqa: BLE001
                print(f"[错误] {exc}")
            continue
        try:
            result = database.run_query(sql)
        except Exception as exc:  # noqa: BLE001
            print(f"[错误] {exc}")
            continue
        _ask_export(result)
