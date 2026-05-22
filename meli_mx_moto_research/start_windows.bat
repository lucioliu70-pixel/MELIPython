@echo off
setlocal
cd /d "%~dp0"

REM Try UTF-8 code page; ignore failure on minimal systems
chcp 65001 >nul 2>nul

echo [INFO] Checking Python...
python --version >nul 2>nul
if errorlevel 1 (
  py --version >nul 2>nul
  if errorlevel 1 (
    echo [ERROR] Python not found. Install Python 3.11+ and enable "Add Python to PATH".
    echo [HINT] Reopen terminal after installation, then run this script again.
    pause
    exit /b 1
  ) else (
    set "PY_CMD=py"
  )
) else (
  set "PY_CMD=python"
)

echo [INFO] Using interpreter: %PY_CMD%
echo [INFO] Running one-click deploy...
%PY_CMD% deploy.py
if errorlevel 1 (
  echo [ERROR] Startup failed. Check logs above.
  pause
  exit /b 1
)

endlocal
