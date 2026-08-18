# RUNBOOK.md — 运行手册（智能数据库查询与导出工具）

> 项目：智能数据库查询与导出工具（图书馆主题）
> 适用对象：本机运行 / 评测验收
> 文档版本：v1.0.0

本手册只讲一件事：**怎么把项目跑起来并产出导出文件**。设计思路请看 `FEATURE_EXPORT.md`，使用概览请看 `README.md`。

---

## 1. 环境准备

| 项 | 要求 |
| --- | --- |
| 操作系统 | Windows / macOS / Linux 均可 |
| Python | 3.8+（仅用标准库，无需 `pip install`） |
| 第三方依赖 | **无**（导出与流水线只用 `csv` / `json` / 纯字符串拼 HTML+SVG） |
| 数据库 | 内置 SQLite，无需安装数据库服务 |

零依赖是刻意选择：参考项目接了 MySQL（需 `pymysql` + 本地服务），本作业改为单 SQLite，保证"任何环境一条命令就能跑通"。

```bash
# 进入项目目录
cd 汤豪的作业

# 确认 Python 可用（输出版本即可）
python --version
```

> 首次运行任意命令会自动建库（`sample.db`）并灌入图书馆示例数据（12 本图书 / 8 名读者 / 15 条借阅）。

---

## 2. 三种运行方式

### 方式 A：交互式 REPL（自然语言触发导出）—— 推荐体验

```bash
python run.py
```
启动后：
```
SQL> SELECT * FROM books WHERE category='文学'
```
查询成功后助手会主动询问，直接说自然语言即可触发导出：

| 输入 | 效果 |
| --- | --- |
| `导出csv` | 导出 CSV |
| `生成报表` / `网页` | 导出 HTML 可视化报告 |
| `export json` | 导出 JSON |
| `全部导出` / `e` | 一次导出 CSV+JSON+HTML |
| `n` | 跳过 |

其它指令：`tables`（看表）、`exit`（退出）。

### 方式 B：一键多格式流水线（自动化，脚本/集成用）

```bash
python -m db_query_tool.pipeline \
    --sql "SELECT title, author, stock FROM books ORDER BY stock DESC" \
    --formats all \
    --out-dir exports
```
- `--formats`：`csv,json,html` 任选，或用 `all` 一次全导出（**与参考项目单次只导一种格式不同**）。
- 产物落在 `exports/`：`query_result.csv` / `query_result.json` / `query_result.html`。

### 方式 C：Makefile / 脚本触发（构建流）

```bash
# Makefile
make export SQL="SELECT * FROM borrows WHERE status='借阅中'" FORMATS=csv,json,html

# Linux / macOS
./scripts/export_now.sh "SELECT name FROM members" all

# Windows
scripts\export_now.bat "SELECT name FROM members" all
```

---

## 3. 端到端验证

```bash
python verify.py
```
预期输出（5/5 通过）：
```
✅ 功能① 三格式导出(CSV/JSON/HTML)
✅ 功能② 多格式一键流水线
✅ 功能③ 自然语言导出意图解析
✅ 只读安全约束
✅ 差异化效果 HTML 报表含统计+柱状图
结果：5 项通过，0 项失败，共 5 项
🎉 全部验证通过，作业功能要求已满足。
```
也可：`make verify`（等价封装）。

---

## 4. 各入口一览

| 入口 | 命令 | 用途 |
| --- | --- | --- |
| 交互 REPL | `python run.py` | 探索式查询 + 自然语言导出 |
| 流水线模块 | `python -m db_query_tool.pipeline` | 一键多格式导出 |
| Make 目标 | `make export` / `make verify` | 构建流 |
| 脚本 | `scripts/export_now.sh(.bat)` | 命令行快速触发 |
| 验证 | `python verify.py` | 验收 |

---

## 5. 常见问题（FAQ）

**Q1：报 `No module named db_query_tool`？**
在**项目根目录**运行命令（确保 `db_query_tool/` 与 `run.py` 同级），不要进入子目录再跑。

**Q2：想换查询内容？**
直接在 REPL 里写任意只读 `SELECT`；或把 SQL 传给 `pipeline --sql "..."`。支持 `books` / `members` / `borrows` 三张表，先 `tables` 看结构。

**Q3：导出文件在哪？**
默认 `exports/` 目录（`config.EXPORT_DIR`）。可用 `--out-dir` 指定其他目录。

**Q4：为什么只支持 SELECT？**
安全约束：导出入口强制只读，拦截 `INSERT/UPDATE/DELETE/DROP` 等，并以只读 URI 打开数据库，避免导出功能被误用作写入口。

**Q5：HTML 报告打不开 / 没图表？**
用浏览器直接打开 `exports/query_result.html` 即可。若结果没有数值列（如只查文本字段），报表会显示明细表格但跳过统计与柱状图——这是预期行为，换含数值列的查询（如 `stock`）即可看到图表。

**Q6：和参考项目（程文旭作业）的运行差异？**
参考用 `python run.py`（HR 库）+ `python -m db_query_tool.auto_export --format csv`（单次单格式）+ 需 MySQL；本作业用图书馆库、`pipeline --formats all`（一次多格式）、纯 SQLite 零依赖。

---

## 6. 重置演示数据

删除 `sample.db` 后再运行任意命令即重新建库灌数据：
```bash
rm -f sample.db        # Windows: del sample.db
python run.py
```
