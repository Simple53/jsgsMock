@echo off
chcp 65001 >nul
title file2quiz 本地刷题服务器
cd /d "%~dp0"
echo 正在启动 file2quiz 本地服务...
python serve.py
pause
