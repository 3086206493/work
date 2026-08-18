"""数据库层：连接本地 MySQL 的 aj_report 库，执行只读查询。

对应作业「AI Agent 任务分解」中的子任务 ① 获取查询结果（fetch）。

与参考项目的差异（思路不同）：
  - 参考支持 SQLite + MySQL 双后端，代码里有两套连接分支；
  - 本作业**只连本地 MySQL（aj_report）**，数据源单一、配置集中，
    并内置「只读白名单」——任何非查询语句（INSERT/UPDATE/DELETE/DROP…）
    在真正连库之前就被拦截，避免通过 Web 页面误改生产报表库。

安全策略：
  - 仅允许以 SELECT / WITH / SHOW / DESCRIBE / EXPLAIN 开头的语句；
  - 其余一律抛 ValueError，绝不执行。
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from . import config

# 只读语句允许的起始关键字（小写）。WITH 用于 CTE 只读查询。
_READONLY_PREFIXES = ("select", "with", "show", "describe", "desc ", "explain")
# 仅允许安全标识符（表名/列名），防止注入
_IDENT_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


@dataclass
class QueryResult:
    """查询结果的统一中间结构，供导出层与交互层消费。"""

    columns: list[str]
    rows: list[tuple]
    sql: str

    @property
    def row_count(self) -> int:
        return len(self.rows)

    def as_dicts(self) -> list[dict[str, Any]]:
        return [dict(zip(self.columns, row)) for row in self.rows]


def _is_readonly(sql: str) -> bool:
    """判断是否为只读查询（在连库前拦截写操作）。"""
    # 去掉开头可能存在的括号与空白，再取首个关键字
    stripped = sql.strip().lstrip("(").lstrip()
    low = stripped.lower()
    return any(low.startswith(p) for p in _READONLY_PREFIXES)


def _safe_identifier(name: str) -> str:
    if not _IDENT_RE.match(name or ""):
        raise ValueError(f"非法的标识符：{name!r}（仅允许字母/数字/下划线）")
    return name


def get_connection():
    """建立到 aj_report 的 MySQL 连接（pymysql 惰性导入，避免无网络时 import 失败）。"""
    import pymysql  # 惰性导入：模块层面不依赖驱动是否安装

    return pymysql.connect(
        host=config.MYSQL_HOST,
        port=config.MYSQL_PORT,
        user=config.MYSQL_USER,
        password=config.MYSQL_PASSWORD,
        database=config.MYSQL_DATABASE,
        charset=config.MYSQL_CHARSET,
        connect_timeout=5,
        cursorclass=pymysql.cursors.Cursor,
    )


def run_query(sql: str) -> QueryResult:
    """执行一条只读查询，返回 QueryResult。

    Args:
        sql: 仅允许 SELECT / WITH / SHOW / DESCRIBE / EXPLAIN 语句。
    Raises:
        ValueError: 语句非只读，或 SQL 语法/连接错误。
    """
    if not _is_readonly(sql):
        raise ValueError(
            "只读模式：仅允许 SELECT / WITH / SHOW / DESCRIBE / EXPLAIN 查询，"
            "已拦截写操作。"
        )

    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(sql)
            columns = [d[0] for d in cur.description] if cur.description else []
            rows = cur.fetchall()
        return QueryResult(columns=columns, rows=list(rows), sql=sql)
    except Exception as exc:  # noqa: BLE001
        # 把底层错误包装成可读提示，便于 Web / REPL 展示
        raise ValueError(f"查询执行失败：{exc}") from exc
    finally:
        conn.close()


def list_tables() -> list[str]:
    """列出 aj_report 库中所有表名。"""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SHOW TABLES")
            return [row[0] for row in cur.fetchall()]
    finally:
        conn.close()


def get_table_columns(table: str) -> list[str]:
    """获取某张表的列名（用于 Web 页面快速构建预览查询）。"""
    _safe_identifier(table)
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(f"SELECT * FROM `{table}` LIMIT 0")
            return [d[0] for d in cur.description] if cur.description else []
    finally:
        conn.close()


def test_connection() -> dict:
    """探测 MySQL 连接是否可用，返回状态字典（供 Web 状态灯使用）。"""
    try:
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT DATABASE()")
                row = cur.fetchone()
            return {
                "ok": True,
                "host": f"{config.MYSQL_HOST}:{config.MYSQL_PORT}",
                "database": config.MYSQL_DATABASE,
                "current": row[0] if row else None,
            }
        finally:
            conn.close()
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": str(exc)}
