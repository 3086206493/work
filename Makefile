# 自动化构建脚本：把「执行查询 + 导出结果」固化为一条 make 命令。
# 这是作业"自动化流程"要求的命令行等价实现（区别于参考的 Claude Code Command）。
#
# 用法示例（数据源：本地 MySQL 的 aj_report 库）：
#   make export SQL="SELECT * FROM report_daily" FORMATS=csv,json,html
#   make export SQL="SELECT region, SUM(revenue) FROM report_daily GROUP BY region" FORMATS=all
#   make verify        # 运行端到端验证
#   make web           # 启动 Web 页面（浏览器操作）

PY ?= python

export:
	$(PY) -m db_query_tool.pipeline --sql "$(SQL)" --formats $(FORMATS)

verify:
	$(PY) verify.py

web:
	$(PY) run.py

.PHONY: export verify web
