# /export-query — 自动化导出命令（AI Agent Command 模板）

> 作用：把"执行查询 + 导出结果"合并为一个自然语言命令，一键触发。
> 适用：Claude Code / WorkBuddy 等支持自定义 Command 的 AI 编程工具。
> 与参考项目 `commands/export-query.md` 的差异：本模板默认**多格式一次性导出**
> （csv,json,html），并显式要求 Agent 按"获取→格式化→写文件"三步拆解并汇报。

## 触发方式

```
/export-query <SQL> [formats]
```

- `<SQL>`：只读 SELECT 语句（必填）。
- `[formats]`：可选，逗号分隔，取值 `csv,json,html` 或 `all`（默认 `all`）。

示例：

```
/export-query "SELECT title, author FROM books WHERE category='文学'" csv,html
/export-query "SELECT * FROM borrows WHERE status='借阅中'" all
```

## Agent 执行步骤（任务分解）

收到命令后，Agent 应：

1. **获取查询结果**：调用 `database.run_query(sql)`，确认返回列与行数；若 SQL 非只读（含 INSERT/UPDATE/DELETE 等），直接拒绝并说明安全约束。
2. **格式化数据**：对每个目标格式，调用 `exporter.export(result, fmt, path)` 内部完成格式化。
3. **创建文件**：确认 `exports/` 目录已创建，把每个格式落盘，并打印最终路径与行数。

## 本地等价实现（无需 AI 工具也能跑）

```bash
# 方式 A：Python 模块
python -m db_query_tool.pipeline --sql "SELECT * FROM books" --formats all

# 方式 B：Makefile
make export SQL="SELECT * FROM books" FORMATS=csv,json,html

# 方式 C：一键脚本
./scripts/export_now.sh "SELECT * FROM borrows WHERE status='借阅中'" all
```

## 设计收益

- 用户无需记忆多参数，一句自然语言即可完成"查询→多格式导出"；
- 编排逻辑（`pipeline.run_pipeline`）与命令模板解耦——换工具只需改模板，
  不动底层函数，印证「Cursor 实现层 / AI 命令 流程层」的分工。
