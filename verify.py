"""端到端验证脚本：证明作业三项功能要求 + 三项核心练习均已满足。

用法：python verify.py
退出码：0 全部通过（含环境无关项与 MySQL 实连项），1 有失败项。

设计原则：
  - 导出 / 流水线 / 自然语言解析 / 只读拦截 / Web 页面这几项「环境无关」，
    在任何机器上都应通过；
  - 只连 MySQL(aj_report) 的真实查询与导出项，若本机未启动 MySQL 或
    无 aj_report 库，则标记为 SKIP（不计入失败），并提示如何补测。
"""

from __future__ import annotations

import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from db_query_tool import database, exporter, pipeline, interaction, web
from db_query_tool.database import QueryResult

PASS, FAIL, SKIP = "PASS", "FAIL", "SKIP"
results: list[tuple[str, str, str]] = []


def report(name: str, status: str, detail: str = "") -> None:
    results.append((name, status, detail))
    icon = {"PASS": "✅", "FAIL": "❌", "SKIP": "⏭️"}[status]
    print(f"{icon} {name}: {status} {detail}")


# --------------------------------------------------------------------------- #
# 环境无关项
# --------------------------------------------------------------------------- #
def test_exporter_three_formats() -> None:
    result = QueryResult(
        columns=["title", "stock"],
        rows=[("产品A", 120), ("产品B", 80), ("产品C", 200)],
        sql="SELECT title, stock FROM demo",
    )
    with tempfile.TemporaryDirectory() as tmp:
        csv_p = os.path.join(tmp, "b.csv")
        json_p = os.path.join(tmp, "b.json")
        html_p = os.path.join(tmp, "b.html")

        exporter.export(result, "csv", csv_p)
        exporter.export(result, "json", json_p)
        exporter.export(result, "html", html_p)

        with open(csv_p, "r", encoding="utf-8-sig") as f:
            assert "title" in f.read()
        with open(json_p, "r", encoding="utf-8") as f:
            payload = json.load(f)
            assert payload["row_count"] == 3
        html_text = open(html_p, "r", encoding="utf-8").read()
        assert "<table>" in html_text and "查询结果可视化报表" in html_text

    report("功能① 三格式导出(CSV/JSON/HTML)", PASS,
           "导出层 CSV/JSON/HTML 均生成成功")


def test_html_report_chart() -> None:
    result = QueryResult(
        columns=["region", "revenue"],
        rows=[("华东", 386520.0), ("华南", 263560.0), ("华北", 297840.0)],
        sql="SELECT region, revenue FROM report_daily",
    )
    with tempfile.TemporaryDirectory() as tmp:
        p = os.path.join(tmp, "r.html")
        exporter.export(result, "html", p)
        text = open(p, "r", encoding="utf-8").read()
        assert "最大" in text and "最小" in text and "<rect" in text
    report("差异化效果 HTML 报表含统计+柱状图", PASS,
           "数值列 revenue 生成 Top 柱状图")


def test_multi_format_pipeline() -> None:
    # 用假结果注入 database.run_query，验证流水线编排逻辑（不依赖 MySQL）
    import db_query_tool.database as dbmod

    class FakeResult(QueryResult):
        def __init__(self):
            super().__init__(columns=["region", "revenue"],
                             rows=[("华东", 1.0)], sql="SELECT 1")

    orig = dbmod.run_query
    dbmod.run_query = lambda sql: FakeResult()
    try:
        with tempfile.TemporaryDirectory() as tmp:
            paths = pipeline.run_pipeline("SELECT 1", "all", out_dir=tmp)
            assert len(paths) == 3
            for p in paths:
                assert os.path.exists(p)
    finally:
        dbmod.run_query = orig
    report("功能② 多格式一键流水线", PASS,
           "pipeline 一次导出 csv+json+html（编排逻辑验证）")


def test_nl_export_intent() -> None:
    assert interaction._parse_export_intent("导出csv") == ["csv"]
    assert interaction._parse_export_intent("生成报表") == ["html"]
    assert interaction._parse_export_intent("export json") == ["json"]
    assert set(interaction._parse_export_intent("全部导出")) == {"csv", "json", "html"}
    assert interaction._parse_export_intent("随便看看") is None
    report("功能③ 自然语言导出意图解析", PASS,
           "命中 csv/html/json/all 关键词与否定场景")


def test_readonly_guard() -> None:
    # 只读校验在连库前完成，无需 MySQL
    try:
        database.run_query("DELETE FROM report_daily")
        report("只读安全约束", FAIL, "DELETE 未被拦截")
    except ValueError as exc:
        assert "只读" in str(exc)
        report("只读安全约束", PASS, str(exc))


def test_web_page_present() -> None:
    h = web.PAGE_HTML
    markers = ["/api/query", "/api/export", "导出 CSV", "导出 HTML 报表", "report_daily"]
    missing = [m for m in markers if m not in h]
    assert not missing, f"缺少页面要素：{missing}"
    report("Web 页面操作入口", PASS,
           "内嵌单页含查询/CSV/JSON/HTML报表导出与表预览")


# --------------------------------------------------------------------------- #
# 仅在本机 MySQL(aj_report) 可用时执行
# --------------------------------------------------------------------------- #
def test_mysql_end_to_end() -> None:
    st = database.test_connection()
    if not st.get("ok"):
        report("MySQL 实连端到端(CSV/JSON/HTML)", SKIP,
               f"本机 MySQL 未连接：{st.get('error')}（不影响其余项；"
               "按 README 启动 MySQL 后重跑即可覆盖）")
        return
    try:
        result = database.run_query("SELECT * FROM report_daily LIMIT 100")
        assert result.row_count >= 1
        with tempfile.TemporaryDirectory() as tmp:
            for fmt in ("csv", "json", "html"):
                p = os.path.join(tmp, f"x.{fmt}")
                exporter.export(result, fmt, p)
                assert os.path.exists(p)
        report("MySQL 实连端到端(CSV/JSON/HTML)", PASS,
               f"aj_report.report_daily 实查 {result.row_count} 行并三格式导出")
    except Exception as exc:  # noqa: BLE001
        report("MySQL 实连端到端(CSV/JSON/HTML)", FAIL, str(exc))


def main() -> int:
    print("aj_report 智能查询与导出工具 · 端到端验证")
    print("=" * 54)
    test_exporter_three_formats()
    test_html_report_chart()
    test_multi_format_pipeline()
    test_nl_export_intent()
    test_readonly_guard()
    test_web_page_present()
    test_mysql_end_to_end()
    print("=" * 54)

    passed = sum(1 for _, s, _ in results if s == PASS)
    failed = sum(1 for _, s, _ in results if s == FAIL)
    skipped = sum(1 for _, s, _ in results if s == SKIP)
    print(f"结果：{passed} 通过 ｜ {skipped} 跳过 ｜ {failed} 失败（共 {len(results)} 项）")
    if failed == 0:
        print("🎉 无失败项。作业功能要求已满足"
              + ("（MySQL 实连项已跳过，本机启动 MySQL 后重跑可覆盖）。" if skipped else "。"))
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
