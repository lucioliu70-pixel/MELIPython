@echo off
chcp 65001 >nul
cd /d "%~dp0"

where python >nul 2>nul
if errorlevel 1 (
  echo [错误] 未找到 Python，请先安装 Python 3.11+
  pause
  exit /b 1
)

echo [INFO] 正在执行一键部署并启动...
python deploy.py
if errorlevel 1 (
  echo [错误] 启动失败，请检查日志输出
  pause
  exit /b 1
)
