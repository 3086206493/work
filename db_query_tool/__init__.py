"""智能数据库查询与导出工具 · 包入口。

项目主题：校园图书馆借阅系统（演示库）。
核心能力：对只读 SQLite 演示库执行 SELECT，并把结果导出为
CSV / JSON / HTML 可视化报告 三种格式。

设计原则（与「代码库理解与扩展」练习呼应）：
  - 查询层（database）只负责"连接 + 只读执行"，产出统一的 QueryResult；
  - 导出层（exporter）只负责"格式化 + 写文件"，与查询解耦；
  - 编排层（pipeline）把"导出数据"拆成可观察的子任务并协调。
"""

from __future__ import annotations

__version__ = "1.0.0"
__project__ = "智能数据库查询与导出工具（图书馆主题）"
