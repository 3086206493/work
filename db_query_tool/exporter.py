"""导出层：把查询结果格式化为 CSV / JSON / HTML 可视化报告。

对应作业「AI Agent 任务分解」中的两个子任务：
  - ② 格式化数据（format）
  - ③ 创建文件（create file）

与参考项目的差异（效果不同）：
  - 参考只做 CSV + JSON 两种"数据文件"；
  - 本作业额外提供 **HTML 可视化报告**：自带样式表格 + 统计摘要 +
    纯 SVG 柱状图，可直接用浏览器打开分享，导出"效果"更直观。
  - 仍只用 Python 标准库，零依赖。
"""

from __future__ import annotations

import csv
import html
import json
import os
from datetime import datetime
from typing import Iterable

from .database import QueryResult

# 支持的格式集合（交互层据此校验与提示）
SUPPORTED_FORMATS = ("csv", "json", "html")
# "all" 作为一个便捷别名，覆盖全部格式
ALL_FORMATS = SUPPORTED_FORMATS


def export(result: QueryResult, fmt: str, out_path: str) -> str:
    """按格式把查询结果导出到文件，返回实际路径。

    Args:
        result: 查询得到的 QueryResult。
        fmt: 目标格式（csv / json / html，大小写不敏感）。
        out_path: 输出文件路径。
    """
    fmt = fmt.lower()
    if fmt not in SUPPORTED_FORMATS:
        raise ValueError(
            f"不支持的导出格式：{fmt!r}，当前支持：{', '.join(SUPPORTED_FORMATS)}"
        )

    parent = os.path.dirname(os.path.abspath(out_path))
    os.makedirs(parent, exist_ok=True)

    if fmt == "csv":
        _write_csv(result, out_path)
    elif fmt == "json":
        _write_json(result, out_path)
    else:
        _write_html(result, out_path)

    return out_path


# --------------------------------------------------------------------------- #
# CSV
# --------------------------------------------------------------------------- #
def _write_csv(result: QueryResult, out_path: str) -> None:
    """格式化 → 写出 CSV（Excel 友好，UTF-8-BOM）。"""
    with open(out_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(result.columns)
        writer.writerows(result.rows)


# --------------------------------------------------------------------------- #
# JSON
# --------------------------------------------------------------------------- #
def _write_json(result: QueryResult, out_path: str) -> None:
    """格式化 → 写出 JSON（对象数组，保留字段名）。"""
    payload = {
        "sql": result.sql,
        "exported_at": datetime.now().isoformat(timespec="seconds"),
        "row_count": result.row_count,
        "columns": result.columns,
        "data": result.as_dicts(),
    }
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2, default=str)


# --------------------------------------------------------------------------- #
# HTML 可视化报告（差异化效果）
# --------------------------------------------------------------------------- #
def _write_html(result: QueryResult, out_path: str) -> None:
    """格式化 → 写出自包含 HTML 报告（表格 + 统计 + SVG 柱状图）。"""
    doc = _build_html(result)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(doc)


def _build_html(result: QueryResult) -> str:
    """拼装 HTML 文档字符串。"""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    rows_html = _render_table(result)
    stats_html, chart_html = _derive_stats_and_chart(result)

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>查询结果报表</title>
<style>
  :root {{ --brand:#2563eb; --bg:#f8fafc; --card:#fff; --line:#e2e8f0; --ink:#0f172a; --muted:#64748b; }}
  * {{ box-sizing:border-box; }}
  body {{ margin:0; background:var(--bg); color:var(--ink); font-family:-apple-system,"Segoe UI",Roboto,"PingFang SC","Microsoft YaHei",sans-serif; }}
  .wrap {{ max-width:980px; margin:0 auto; padding:28px 20px 48px; }}
  header {{ background:linear-gradient(135deg,var(--brand),#1e40af); color:#fff; border-radius:14px; padding:22px 26px; box-shadow:0 8px 24px rgba(37,99,235,.25); }}
  header h1 {{ margin:0 0 6px; font-size:22px; }}
  header .meta {{ font-size:13px; opacity:.92; }}
  header code {{ background:rgba(255,255,255,.18); padding:2px 6px; border-radius:6px; }}
  .cards {{ display:flex; gap:14px; flex-wrap:wrap; margin:22px 0; }}
  .card {{ flex:1 1 160px; background:var(--card); border:1px solid var(--line); border-radius:12px; padding:16px; }}
  .card .k {{ font-size:13px; color:var(--muted); }}
  .card .v {{ font-size:24px; font-weight:700; margin-top:4px; }}
  section {{ background:var(--card); border:1px solid var(--line); border-radius:12px; padding:18px 20px; margin-bottom:18px; }}
  h2 {{ font-size:16px; margin:0 0 12px; }}
  table {{ border-collapse:collapse; width:100%; font-size:13px; }}
  th,td {{ border:1px solid var(--line); padding:8px 10px; text-align:left; }}
  th {{ background:#f1f5f9; position:sticky; top:0; }}
  tbody tr:nth-child(even) {{ background:#fbfdff; }}
  .scroll {{ max-height:360px; overflow:auto; border:1px solid var(--line); border-radius:10px; }}
  .stat {{ display:flex; gap:18px; flex-wrap:wrap; }}
  .stat div {{ font-size:13px; }}
  .stat b {{ font-size:18px; display:block; }}
  footer {{ text-align:center; color:var(--muted); font-size:12px; margin-top:10px; }}
</style>
</head>
<body>
<div class="wrap">
  <header>
    <h1>📊 查询结果可视化报表</h1>
    <div class="meta">生成时间：{now} ｜ 行数：{result.row_count} ｜ 列数：{len(result.columns)}</div>
    <div class="meta" style="margin-top:6px;">SQL：<code>{html.escape(result.sql)}</code></div>
  </header>

  <div class="cards">
    <div class="card"><div class="k">返回行数</div><div class="v">{result.row_count}</div></div>
    <div class="card"><div class="k">字段数</div><div class="v">{len(result.columns)}</div></div>
    <div class="card"><div class="k">导出格式</div><div class="v">HTML</div></div>
  </div>

  <section>
    <h2>📈 数值统计与图表</h2>
    {stats_html}
    {chart_html}
  </section>

  <section>
    <h2>📋 明细数据</h2>
    <div class="scroll">
      <table>
        <thead><tr>{''.join(f'<th>{html.escape(str(c))}</th>' for c in result.columns)}</tr></thead>
        <tbody>
        {rows_html}
        </tbody>
      </table>
    </div>
  </section>

  <footer>由「智能数据库查询与导出工具」自动生成 · 仅含只读查询结果</footer>
</div>
</body>
</html>
"""


def _render_table(result: QueryResult) -> str:
    out = []
    for row in result.rows:
        cells = "".join(f"<td>{html.escape('' if v is None else str(v))}</td>" for v in row)
        out.append(f"<tr>{cells}</tr>")
    return "\n".join(out)


def _derive_stats_and_chart(result: QueryResult) -> tuple[str, str]:
    """挑选第一个数值列，计算统计并生成 SVG 柱状图（top 10）。"""
    num_idx = None
    for i, col in enumerate(result.columns):
        if result.rows and _is_number(result.rows[0][i]):
            num_idx = i
            break

    if num_idx is None:
        return (
            '<p style="color:#64748b;font-size:13px;">结果中没有数值列，'
            "跳过统计与图表。</p>",
            "",
        )

    col_name = result.columns[num_idx]
    values = []
    for row in result.rows:
        v = row[num_idx]
        if _is_number(v):
            values.append((str(row[0]), float(v)))

    if not values:
        return (
            '<p style="color:#64748b;font-size:13px;">数值列无有效数据。</p>',
            "",
        )

    nums = [v for _, v in values]
    mn, mx, avg = min(nums), max(nums), sum(nums) / len(nums)
    stats_html = (
        f'<div class="stat">'
        f'<div>统计列<b>{html.escape(col_name)}</b></div>'
        f'<div>最小<b>{mn:g}</b></div>'
        f'<div>最大<b>{mx:g}</b></div>'
        f'<div>平均<b>{avg:.2f}</b></div>'
        f'<div>样本<b>{len(nums)}</b></div>'
        f"</div>"
    )

    # SVG 柱状图：取数值最大的前 10 项
    top = sorted(values, key=lambda x: x[1], reverse=True)[:10]
    chart_html = _bar_chart(top, col_name)
    return stats_html, chart_html


def _bar_chart(items: list[tuple[str, float]], label: str) -> str:
    """生成纯 SVG 柱状图（无外部依赖）。"""
    w, h = 720, 280
    pad_l, pad_b, pad_t = 40, 40, 20
    plot_w = w - pad_l - 20
    plot_h = h - pad_b - pad_t
    max_v = max(v for _, v in items) or 1
    n = len(items)
    gap = 12
    bar_w = (plot_w - gap * (n - 1)) / n if n > 1 else plot_w

    bars = []
    for i, (name, val) in enumerate(items):
        x = pad_l + i * (bar_w + gap)
        bh = (val / max_v) * plot_h
        y = pad_t + (plot_h - bh)
        bars.append(
            f'<rect x="{x:.1f}" y="{y:.1f}" width="{bar_w:.1f}" height="{bh:.1f}" '
            f'rx="4" fill="#2563eb"></rect>'
        )
        # 数值标签
        bars.append(
            f'<text x="{x + bar_w/2:.1f}" y="{y - 6:.1f}" font-size="11" '
            f'text-anchor="middle" fill="#0f172a">{val:g}</text>'
        )
        # 名称标签（截断）
        disp = name if len(name) <= 6 else name[:6] + "…"
        bars.append(
            f'<text x="{x + bar_w/2:.1f}" y="{h - pad_b + 16:.1f}" font-size="11" '
            f'text-anchor="middle" fill="#64748b">{html.escape(disp)}</text>'
        )
    svg = (
        f'<svg viewBox="0 0 {w} {h}" width="100%" style="max-width:{w}px;">'
        f'<line x1="{pad_l}" y1="{pad_t}" x2="{pad_l}" y2="{h-pad_b}" stroke="#e2e8f0"/>'
        f'<line x1="{pad_l}" y1="{h-pad_b}" x2="{w-20}" y2="{h-pad_b}" stroke="#e2e8f0"/>'
        f'<text x="{pad_l}" y="{pad_t-6}" font-size="12" fill="#64748b">'
        f'{html.escape(label)} Top {n}</text>'
        f"{''.join(bars)}"
        f"</svg>"
    )
    return svg


def _is_number(v) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool)


# --------------------------------------------------------------------------- #
# 工具函数
# --------------------------------------------------------------------------- #
def suggest_filename(fmt: str, base: str = "query_result") -> str:
    """未指定输出名时生成默认文件名。"""
    return f"{base}.{fmt.lower()}"


def preview(result: QueryResult, limit: int = 5) -> str:
    """终端预览，用于交互层"主动询问"前先展示数据。"""
    if not result.columns:
        return "(无返回列)"
    lines = [" | ".join(str(c) for c in result.columns)]
    lines.append("-" * len(lines[0]))
    for row in result.rows[:limit]:
        lines.append(" | ".join("" if v is None else str(v) for v in row))
    if result.row_count > limit:
        lines.append(f"... 共 {result.row_count} 行，仅预览前 {limit} 行")
    return "\n".join(lines)
