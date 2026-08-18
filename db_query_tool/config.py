"""集中配置：本地 MySQL 连接参数与导出目录。

按作业要求，数据源直接使用本地 MySQL：
  - 用户：root
  - 密码：123456
  - 目标库：aj_report
可用环境变量覆盖（便于在不同机器/容器里不改代码）：
  AJ_MYSQL_HOST / AJ_MYSQL_PORT / AJ_MYSQL_USER / AJ_MYSQL_PASSWORD / AJ_MYSQL_DATABASE
"""

from __future__ import annotations

import os

# 项目根目录（db_query_tool 的上一级）
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# —— 本地 MySQL 连接配置 —— #
MYSQL_HOST = os.environ.get("AJ_MYSQL_HOST", "127.0.0.1")
MYSQL_PORT = int(os.environ.get("AJ_MYSQL_PORT", "3306"))
MYSQL_USER = os.environ.get("AJ_MYSQL_USER", "root")
MYSQL_PASSWORD = os.environ.get("AJ_MYSQL_PASSWORD", "123456")
MYSQL_DATABASE = os.environ.get("AJ_MYSQL_DATABASE", "aj_report")
MYSQL_CHARSET = "utf8mb4"

# 导出产物目录（CSV / JSON / HTML 报表都落在这里）
EXPORT_DIR = os.path.join(BASE_DIR, "exports")

# Web 服务监听地址（python run.py 启动）
WEB_HOST = os.environ.get("AJ_WEB_HOST", "127.0.0.1")
WEB_PORT = int(os.environ.get("AJ_WEB_PORT", "8000"))
