"""Web 交互页面：浏览器里连接本地 MySQL(aj_report)，写 SQL、看结果、一键导出。

对应作业功能要求第 3 点「通过简单的界面操作触发导出功能」的网页形态：
用户在浏览器里选表、写 SQL、看结果，再用「导出 CSV / JSON / HTML 报表」按钮
一键导出——无需记命令、无需命令行。

实现要点（与参考项目 web.py 的差异 —— 效果/思路不同）：
  - 零额外框架依赖：仅用 Python 标准库 http.server（唯一外部依赖是 pymysql，
    用于连 MySQL），比 Flask/Django 更轻、更易交付。
  - 导出格式更全：除 CSV / JSON 外，Web 页面也能直接导出 **HTML 可视化报表**
    （带表格+统计+SVG 柱状图），而参考项目的 Web 只支持 CSV/JSON。
  - 表结构自发现：打开页面自动列出 aj_report 的表并支持点击预览，无需预先知道表名。

启动：python run.py   或   python -m db_query_tool.web
"""

from __future__ import annotations

import html
import json
import os
import tempfile
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

from . import config, database, exporter

# 导出文件临时落盘目录（用完即删，避免残留）
_EXPORT_DIR = os.path.join(tempfile.gettempdir(), "aj_report_exports")
os.makedirs(_EXPORT_DIR, exist_ok=True)


def _normalize(value: Any) -> Any:
    """把非 JSON 原生类型（datetime/Decimal/bytes 等）转为字符串。"""
    if isinstance(value, (bytes, bytearray)):
        try:
            return value.decode("utf-8")
        except Exception:  # noqa: BLE001
            return repr(value)
    return value


# --------------------------------------------------------------------------- #
# 内嵌单页前端（自包含 HTML/CSS/JS，无外部 CDN，离线可用）
# --------------------------------------------------------------------------- #
PAGE_HTML = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>aj_report · 智能查询与导出</title>
<style>
  :root{--brand:#2563eb;--brand2:#1e40af;--bg:#f1f5f9;--card:#fff;--line:#e2e8f0;--ink:#0f172a;--muted:#64748b;--ok:#16a34a;--bad:#dc2626;}
  *{box-sizing:border-box;}
  body{margin:0;background:var(--bg);color:var(--ink);font-family:-apple-system,"Segoe UI",Roboto,"PingFang SC","Microsoft YaHei",sans-serif;}
  header{background:linear-gradient(135deg,var(--brand),var(--brand2));color:#fff;padding:18px 24px;display:flex;align-items:center;gap:14px;flex-wrap:wrap;}
  header h1{margin:0;font-size:19px;}
  header .sub{font-size:12px;opacity:.9;}
  .pill{margin-left:auto;font-size:12px;background:rgba(255,255,255,.18);padding:5px 12px;border-radius:999px;}
  .pill.ok{background:rgba(22,163,74,.25);} .pill.bad{background:rgba(220,38,38,.3);}
  .wrap{max-width:1180px;margin:0 auto;padding:20px;display:grid;grid-template-columns:240px 1fr;gap:18px;}
  .side,.main{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:16px;}
  .side h3{margin:0 0 10px;font-size:14px;color:var(--muted);}
  .tbl{cursor:pointer;padding:8px 10px;border:1px solid var(--line);border-radius:8px;margin-bottom:8px;font-size:13px;transition:.15s;}
  .tbl:hover{background:#eff6ff;border-color:var(--brand);}
  .hint{font-size:12px;color:var(--muted);line-height:1.7;}
  textarea{width:100%;min-height:96px;resize:vertical;padding:10px;border:1px solid var(--line);border-radius:10px;font-family:"SFMono-Regular",Consolas,monospace;font-size:13px;}
  .bar{display:flex;gap:10px;flex-wrap:wrap;margin:12px 0;}
  button{background:var(--brand);color:#fff;border:0;border-radius:9px;padding:9px 16px;font-size:13px;cursor:pointer;}
  button.ghost{background:#fff;color:var(--brand);border:1px solid var(--brand);}
  button:hover{filter:brightness(1.05);}
  .out{margin-top:8px;}
  .msg{font-size:13px;padding:10px 12px;border-radius:9px;margin-bottom:12px;}
  .msg.err{background:#fef2f2;color:var(--bad);border:1px solid #fecaca;}
  .msg.info{background:#eff6ff;color:var(--brand2);border:1px solid #bfdbfe;}
  .scroll{max-height:460px;overflow:auto;border:1px solid var(--line);border-radius:10px;}
  table{border-collapse:collapse;width:100%;font-size:13px;}
  th,td{border:1px solid var(--line);padding:7px 10px;text-align:left;white-space:nowrap;}
  th{background:#f1f5f9;position:sticky;top:0;}
  tbody tr:nth-child(even){background:#fbfdff;}
  .meta{font-size:12px;color:var(--muted);margin-bottom:8px;}
  @media(max-width:820px){.wrap{grid-template-columns:1fr;}}
</style>
</head>
<body>
<header>
  <div>
    <h1>📊 aj_report 智能查询与导出</h1>
    <div class="sub">本地 MySQL · 库 <code id="dbname">aj_report</code> · 只读模式</div>
  </div>
  <div id="status" class="pill">连接中…</div>
</header>

<div class="wrap">
  <aside class="side">
    <h3>数据表</h3>
    <div id="tables"><span class="hint">加载中…</span></div>
    <hr style="border:none;border-top:1px solid var(--line);margin:14px 0;">
    <div class="hint">
      • 点击表名自动预览前 100 行<br>
      • 在右侧写任意只读 SQL<br>
      • 用导出按钮一键落盘<br>
      • 支持 CSV / JSON / HTML 报表
    </div>
  </aside>

  <main class="main">
    <div id="msg" class="msg info">连接本地 MySQL 后，输入 SQL 并点击「查询」。</div>
    <textarea id="sql" placeholder="例如：SELECT * FROM report_daily LIMIT 100">SELECT * FROM report_daily LIMIT 100</textarea>
    <div class="bar">
      <button onclick="doQuery()">🔍 查询</button>
      <button class="ghost" onclick="doExport('csv')">⬇ 导出 CSV</button>
      <button class="ghost" onclick="doExport('json')">⬇ 导出 JSON</button>
      <button class="ghost" onclick="doExport('html')">⬇ 导出 HTML 报表</button>
      <button class="ghost" onclick="doExport('all')">⬇ 全部格式</button>
    </div>
    <div class="meta" id="meta"></div>
    <div class="scroll"><table id="result"><thead></thead><tbody></tbody></table></div>
  </main>
</div>

<script>
const $ = s => document.querySelector(s);
function showMsg(text, cls){const m=$('#msg');m.textContent=text;m.className='msg '+(cls||'info');}

async function loadStatus(){
  try{
    const r = await fetch('/api/status'); const j = await r.json();
    const el = $('#status');
    if(j.ok){el.textContent='● 已连接 '+j.host+' / '+j.database;el.className='pill ok';}
    else{el.textContent='● 未连接';el.className='pill bad';showMsg('无法连接 MySQL：'+j.error+'。请确认本地 MySQL 已启动、aj_report 库存在，且账号 root/123456 可访问。','err');}
  }catch(e){$('#status').textContent='● 状态未知';}
}
async function loadTables(){
  try{
    const r = await fetch('/api/tables'); const j = await r.json();
    const box = $('#tables');
    if(j.error){box.innerHTML='<span class="hint">'+j.error+'</span>';return;}
    if(!j.tables.length){box.innerHTML='<span class="hint">库内暂无表</span>';return;}
    box.innerHTML='';
    j.tables.forEach(t=>{
      const d=document.createElement('div');d.className='tbl';d.textContent=t;
      d.onclick=()=>{$('#sql').value='SELECT * FROM `'+t+'` LIMIT 100';doQuery();};
      box.appendChild(d);
    });
  }catch(e){}
}

async function doQuery(){
  const sql=$('#sql').value.trim();
  if(!sql){showMsg('请输入 SQL。','err');return;}
  showMsg('查询中…','info');
  try{
    const r=await fetch('/api/query',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({sql})});
    const j=await r.json();
    if(!r.ok){showMsg('查询失败：'+(j.error||'未知错误'),'err');return;}
    render(j);
    showMsg('查询成功，返回 '+j.row_count+' 行。可点击上方按钮导出。','info');
  }catch(e){showMsg('请求异常：'+e,'err');}
}

function render(j){
  const thead=$('#result thead'), tbody=$('#result tbody');
  thead.innerHTML='<tr>'+j.columns.map(c=>'<th>'+esc(c)+'</th>').join('')+'</tr>';
  tbody.innerHTML=j.rows.map(row=>'<tr>'+row.map(c=>'<td>'+(c===null?'<i style="color:#94a3b8">NULL</i>':esc(String(c)))+'</td>').join('')+'</tr>').join('');
  $('#meta').textContent='字段：'+j.columns.length+' ｜ 行数：'+j.row_count+' ｜ SQL：'+j.sql;
}

async function doExport(fmt){
  const sql=$('#sql').value.trim();
  if(!sql){showMsg('请先输入 SQL。','err');return;}
  try{
    const r=await fetch('/api/export',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({sql,format:fmt})});
    if(!r.ok){const j=await r.json().catch(()=>({}));showMsg('导出失败：'+(j.error||r.status),'err');return;}
    const blob=await r.blob();
    const fn='query_result.'+(fmt==='all'?'zip':fmt);
    const a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download=fn;a.click();
    showMsg('已触发下载：'+fn+'（若浏览器拦截，请允许下载）。','info');
  }catch(e){showMsg('导出异常：'+e,'err');}
}

function esc(s){return String(s).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));}

loadStatus();loadTables();
</script>
</body>
</html>
"""


class _Handler(BaseHTTPRequestHandler):
    # —— 工具方法 —— #
    def _send_json(self, code: int, obj: Any) -> None:
        body = json.dumps(obj, ensure_ascii=False, default=str).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_file(self, path: str, fmt: str) -> None:
        with open(path, "rb") as f:
            data = f.read()
        os.remove(path)
        self.send_response(200)
        mime = {
            "csv": "text/csv; charset=utf-8",
            "json": "application/json; charset=utf-8",
            "html": "text/html; charset=utf-8",
        }.get(fmt, "application/octet-stream")
        self.send_header("Content-Type", mime)
        self.send_header("Content-Length", str(len(data)))
        self.send_header(
            "Content-Disposition",
            f'attachment; filename="{os.path.basename(path)}"',
        )
        self.end_headers()
        self.wfile.write(data)

    def _serve_page(self) -> None:
        data = PAGE_HTML.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _read_payload(self) -> dict:
        length = int(self.headers.get("Content-Length", 0) or 0)
        raw = self.rfile.read(length) if length else b"{}"
        try:
            return json.loads(raw or b"{}")
        except Exception:  # noqa: BLE001
            return {}

    # —— 路由 —— #
    def do_GET(self) -> None:
        path = urllib.parse.urlparse(self.path).path
        if path in ("/", "/index.html"):
            self._serve_page()
            return
        if path == "/api/status":
            self._send_json(200, database.test_connection())
            return
        if path == "/api/tables":
            try:
                self._send_json(200, {"tables": database.list_tables()})
            except Exception as exc:  # noqa: BLE001
                self._send_json(200, {"tables": [], "error": str(exc)})
            return
        self._send_json(404, {"error": "not found"})

    def do_POST(self) -> None:
        path = urllib.parse.urlparse(self.path).path
        payload = self._read_payload()

        if path == "/api/query":
            sql = payload.get("sql", "")
            try:
                result = database.run_query(sql)
                self._send_json(200, {
                    "columns": result.columns,
                    "rows": [[_normalize(v) for v in row] for row in result.rows],
                    "row_count": result.row_count,
                    "sql": result.sql,
                })
            except Exception as exc:  # noqa: BLE001
                self._send_json(400, {"error": str(exc)})
            return

        if path == "/api/export":
            sql = payload.get("sql", "")
            fmt = str(payload.get("format", "csv")).lower()
            try:
                if fmt == "all":
                    # 一次导出全部格式，打包为 zip 下载
                    paths = self._export_all(sql)
                    self._send_zip(paths)
                elif fmt in exporter.SUPPORTED_FORMATS:
                    result = database.run_query(sql)
                    out_path = os.path.join(_EXPORT_DIR, exporter.suggest_filename(fmt))
                    exporter.export(result, fmt, out_path)
                    self._send_file(out_path, fmt)
                else:
                    self._send_json(400, {"error": f"不支持的格式：{fmt}"})
            except Exception as exc:  # noqa: BLE001
                self._send_json(400, {"error": str(exc)})
            return

        self._send_json(404, {"error": "not found"})

    # —— 多格式打包 —— #
    def _export_all(self, sql: str) -> list[str]:
        import zipfile

        result = database.run_query(sql)
        paths = []
        for fmt in exporter.ALL_FORMATS:
            p = os.path.join(_EXPORT_DIR, exporter.suggest_filename(fmt))
            exporter.export(result, fmt, p)
            paths.append(p)
        return paths

    def _send_zip(self, paths: list[str]) -> None:
        import io
        import zipfile

        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
            for p in paths:
                z.write(p, os.path.basename(p))
                os.remove(p)
        data = buf.getvalue()
        self.send_response(200)
        self.send_header("Content-Type", "application/zip")
        self.send_header("Content-Length", str(len(data)))
        self.send_header(
            "Content-Disposition", 'attachment; filename="query_result.zip"'
        )
        self.end_headers()
        self.wfile.write(data)

    # 安静日志
    def log_message(self, *_args) -> None:  # noqa: D401
        return


def run_web(host: str | None = None, port: int | None = None) -> None:
    """启动 Web 交互服务（默认监听 config.WEB_HOST:WEB_PORT）。"""
    host = host or config.WEB_HOST
    port = port or config.WEB_PORT
    server = ThreadingHTTPServer((host, port), _Handler)
    url = f"http://{host}:{port}/"
    print("╔════════════════════════════════════════════════════════╗")
    print("║   aj_report 智能查询与导出 · Web 页面已启动            ║")
    print(f"║   在浏览器打开：{url}")
    print("║   按 Ctrl+C 停止服务                                   ║")
    print("╚════════════════════════════════════════════════════════╝")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n已停止 Web 服务。")
    finally:
        server.server_close()


if __name__ == "__main__":
    run_web()
