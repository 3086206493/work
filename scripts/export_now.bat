@echo off
REM 一键导出启动脚本（Windows）：查询 + 多格式导出一步完成。
REM 用法： scripts\export_now.bat "SELECT * FROM books" csv,json,html
set SQL=%~1
if "%SQL%"=="" set SQL=SELECT * FROM books
set FORMATS=%~2
if "%FORMATS%"=="" set FORMATS=all
python -m db_query_tool.pipeline --sql "%SQL%" --formats %FORMATS%
