"""项目入口。

默认启动 Web 页面（浏览器操作查询与导出）：
    python run.py

想用命令行交互（自然语言触发导出）则加 cli：
    python run.py cli

其它便捷入口：
    python -m db_query_tool.pipeline --sql "..." --formats all   # 一键多格式导出
    make export SQL="..." FORMATS=csv,json,html                   # 构建脚本触发
"""

import sys

from db_query_tool import config, web
from db_query_tool.interaction import run_interactive


def main() -> None:
    mode = sys.argv[1] if len(sys.argv) > 1 else "web"
    if mode == "cli":
        run_interactive()
    elif mode == "web":
        web.run_web(config.WEB_HOST, config.WEB_PORT)
    else:
        print("用法：python run.py [web|cli]   默认 web")
        raise SystemExit(2)


if __name__ == "__main__":
    main()
