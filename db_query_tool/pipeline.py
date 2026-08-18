"""自动化流水线：把"执行查询 + 导出结果"合并为一步触发。

对应作业功能要求第 2 点（自动化流程）与核心练习「AI Agent 任务分解」。

设计理念（与参考项目 auto_export 的差异 —— 思路不同）：
  - 参考的 auto_export 一次只导出**一种**格式；
  - 本流水线支持**一次导出多种格式**（csv / json / html / all），
    把"导出数据"显式拆成三步并逐格式协调，更贴合真实分析场景
    （同一份结果往往要同时给人看报表、给程序读 JSON、给表格软件读 CSV）。

子任务分解（与 FEATURE_EXPORT.md 一一对应）：
  ① 获取查询结果  fetch    → database.run_query
  ② 格式化数据    format   → exporter.export 内部按格式组织
  ③ 创建文件      write    → exporter.export 内部落盘
本模块的 run_pipeline 是 Agent 协调三步的"编排函数"，并打印每步日志，
方便观察 Agent 如何分步处理。等价于一条命令 / 一个 AI Command 触发。
"""

from __future__ import annotations

import argparse
import os

from . import config, database, exporter


def _resolve_formats(formats: str) -> list[str]:
    """把 'csv,json,html' / 'all' 解析为格式列表并去重。"""
    raw = [f.strip().lower() for f in formats.split(",") if f.strip()]
    resolved: list[str] = []
    for f in raw:
        if f == "all":
            resolved.extend(exporter.ALL_FORMATS)
        elif f in exporter.SUPPORTED_FORMATS:
            resolved.append(f)
        else:
            print(f"[警告] 忽略不支持的格式：{f!r}")
    # 去重并保持稳定顺序
    seen = set()
    ordered = []
    for f in resolved:
        if f not in seen:
            seen.add(f)
            ordered.append(f)
    return ordered


def run_pipeline(sql: str, formats: str = "all",
                 out_dir: str | None = None) -> list[str]:
    """一键完成「查询 + 多格式导出」的自动化入口。

    数据源为本地 MySQL 的 aj_report 库（见 config / database）。

    Args:
        sql: 只读 SELECT 语句。
        formats: 逗号分隔的格式，或 'all'。
        out_dir: 输出目录；默认 config.EXPORT_DIR。
    Returns:
        写入的文件路径列表。
    """
    out_dir = out_dir or config.EXPORT_DIR
    os.makedirs(out_dir, exist_ok=True)
    fmt_list = _resolve_formats(formats)
    if not fmt_list:
        raise ValueError("没有可用的导出格式，请给出 csv/json/html 或 all。")

    # —— 子任务①：获取查询结果 ——
    print(f"[步骤① 获取结果] 执行只读查询：{sql}")
    result = database.run_query(sql)
    print(f"[步骤① 获取结果] 得到 {result.row_count} 行，"
          f"{len(result.columns)} 列：{', '.join(result.columns)}")

    written: list[str] = []
    for fmt in fmt_list:
        # —— 子任务② + ③：格式化数据 → 创建文件 ——
        out_path = os.path.join(out_dir, exporter.suggest_filename(fmt))
        print(f"[步骤②→③ {fmt.upper()}] 格式化并写入：{out_path}")
        path = exporter.export(result, fmt, out_path)
        written.append(path)
        print(f"[完成 {fmt.upper()}] ✅ {path}（{result.row_count} 行）")

    return written


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="pipeline",
        description="一键执行查询并导出（支持多格式：csv,json,html,all）",
    )
    p.add_argument("--sql", required=True, help="只读 SELECT 语句")
    p.add_argument("--formats", default="all",
                   help="导出格式，逗号分隔：csv,json,html 或 all")
    p.add_argument("--out-dir", default=None, help="输出目录，默认 ./exports")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        paths = run_pipeline(args.sql, args.formats, args.out_dir)
    except Exception as exc:  # noqa: BLE001
        print(f"[错误] {exc}")
        return 1
    print(f"\n[自动化] 共导出 {len(paths)} 个文件：")
    for p in paths:
        print(f"  - {p}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
