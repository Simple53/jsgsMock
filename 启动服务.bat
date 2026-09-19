@echo off
chcp 65001 >nul
title file2quiz 本地刷题服务器
cd /d "%~dp0"
echo 正在启动 file2quiz 本地服务...
if exist ".venv\Scripts\python.exe" goto USE_VENV
python -u serve.py
goto END

:USE_VENV
".venv\Scripts\python.exe" -u serve.py

:END
pause
