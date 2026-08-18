#!/usr/bin/env bash
# 一键导出启动脚本（命令行等价）：查询 + 多格式导出一步完成。
# 用法： ./scripts/export_now.sh "SELECT * FROM books" csv,json,html
set -euo pipefail
SQL="${1:-SELECT * FROM books}"
FORMATS="${2:-all}"
python -m db_query_tool.pipeline --sql "$SQL" --formats "$FORMATS"
