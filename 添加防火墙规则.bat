@echo off
chcp 65001 >nul
title 添加 jsgsMock 防火墙规则

:: 自动申请管理员权限
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo 正在获取管理员权限，请在弹出的系统提示中点击“是”...
    powershell -Command "Start-Process cmd -ArgumentList '/c \"\"%~f0\"\"' -Verb RunAs"
    exit /b
)

cd /d "%~dp0"
echo 正在配置防火墙，允许局域网/公用网络访问 TCP 8080 端口...
netsh advfirewall firewall delete rule name="jsgsMock" >nul 2>&1
netsh advfirewall firewall add rule name="jsgsMock" dir=in action=allow protocol=TCP localport=8080 profile=any
if %errorlevel% equ 0 (
    echo.
    echo ==========================================================
    echo  防火墙规则配置成功！
    echo  已允许手机通过 Wi-Fi 访问电脑 8080 端口。
    echo ==========================================================
) else (
    echo.
    echo [错误] 添加防火墙规则失败，请右键选择“以管理员身份运行”。
)
pause
