# 智能数据库查询与导出工具（图书馆主题）

基于 AI 辅助编程完成的「数据库查询工具 + 数据导出」实战作业。在原有查询工具之上新增导出模块，把查询结果一键导出为 **CSV / JSON / HTML 可视化报告** 三种格式，并提供自然语言交互与一键自动化流水线。

> 与同班参考项目（HR 主题）刻意做出差异：主题换成图书馆、导出多出 HTML 可视化报表、自动化改为"多格式一次导出"流水线、交互改为自然语言意图识别。设计思路见 `FEATURE_EXPORT.md`。

## 快速开始

```bash
# 端到端验证（确认环境无误，5 项检查）
python verify.py

# 启动交互式查询（首次自动建库灌入图书馆示例数据）
python run.py
# SQL> SELECT * FROM books
# 查询后助手会主动询问，输入「导出csv / 生成报表 / 全部导出 / e」即可导出

# 一键多格式导出（自动化）
python -m db_query_tool.pipeline --sql "SELECT title, stock FROM books ORDER BY stock DESC" --formats all

# Makefile 触发
make export SQL="SELECT * FROM borrows WHERE status='借阅中'" FORMATS=csv,json,html
```

## 功能一览

- **查询**：对内置 SQLite 演示库（books / members / borrows 三张表）执行只读 SELECT。
- **导出**：CSV（Excel 友好 UTF-8-BOM）、JSON（对象数组，保留字段名）、HTML（自包含可视化报表：样式表格 + 数值统计 + 纯 SVG 柱状图）。
- **自然语言交互**：查询后说「导出csv / 生成报表 / export json / 全部导出」或按 `e` 一键导出全部，无需记命令参数。
- **自动化流水线**：单命令触发"获取结果 → 格式化 → 写文件"，一次可导出多种格式。
- **只读安全**：仅接受 SELECT，拦截写/结构变更关键字，并以只读 URI 打开数据库。

## 三种触发导出方式

| 方式 | 命令 | 场景 |
| --- | --- | --- |
| 自然语言 REPL | `python run.py` 后对话导出 | 探索式分析 |
| 一键流水线（Python） | `python -m db_query_tool.pipeline --sql "..." --formats all` | 脚本/集成 |
| Makefile / 脚本 | `make export ...` 或 `./scripts/export_now.sh "..." all` | 构建流 |

## 文档

- `FEATURE_EXPORT.md`：新增功能设计思路、任务分解、工具链整合说明（作业必需提交物）。
- `verify.py`：端到端验证脚本。
- `commands/export-query.md`：AI 命令模板。

## 说明

导出模块仅依赖 Python 标准库；演示库为 SQLite，无需安装数据库服务。运行 `python verify.py` 即可验证全部功能（5/5 通过）。
