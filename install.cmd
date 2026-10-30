@echo off
rem ==============================================================================
rem skill-boss Windows 双击/命令行一键安装器
rem 自动以 Bypass 策略调用 PowerShell 安装，无需手动修改系统执行策略
rem ==============================================================================
chcp 65001 >nul
title skill-boss 安装向导

echo 正在启动 skill-boss 安装程序...
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0install.ps1"

if %ERRORLEVEL% neq 0 (
    echo.
    echo ❌ 安装过程中出现异常，请检查上方提示。
    pause
    exit /b %ERRORLEVEL%
)

echo.
pause
