@echo off
setlocal
cd /d "%~dp0"

REM 某些精简系统可能没有 chcp，可忽略失败
chcp 65001 >nul 2>nul

echo [INFO] 正在检查 Python...
python --version >nul 2>nul
if errorlevel 1 (
  py --version >nul 2>nul
  if errorlevel 1 (
    echo [错误] 未找到 Python，请先安装 Python 3.11+ 并勾选 Add Python to PATH
    echo [提示] 安装完成后，重新打开命令行再执行本脚本
    pause
    exit /b 1
  ) else (
    set "PY_CMD=py"
  )
) else (
  set "PY_CMD=python"
)

echo [INFO] 使用解释器: %PY_CMD%
echo [INFO] 正在执行一键部署并启动...
%PY_CMD% deploy.py
if errorlevel 1 (
  echo [错误] 启动失败，请检查上方错误日志
  pause
  exit /b 1
)

endlocal