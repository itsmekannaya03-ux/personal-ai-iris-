@echo off
title Stop Iris AI Services
color 0C
cd /d "%~dp0"

echo.
echo ================================================================
echo               STOPPING IRIS AI SERVICES...
echo ================================================================
echo.

set "PY_CMD=python"
if exist "AI model (iris)\.venv\Scripts\python.exe" set "PY_CMD=AI model (iris)\.venv\Scripts\python.exe"
if not exist "%PY_CMD%" if exist ".venv\Scripts\python.exe" set "PY_CMD=.venv\Scripts\python.exe"

"%PY_CMD%" -c "import subprocess; [subprocess.run(f'taskkill /F /PID {p[-1]}', shell=True, capture_output=True) for port in (5743, 3001, 8001) for l in subprocess.run('netstat -ano', shell=True, capture_output=True, text=True).stdout.splitlines() if f':{port}' in l and 'LISTENING' in l and (p := l.strip().split()) and p[-1].isdigit() and p[-1] != '0']" >nul 2>&1

taskkill /F /FI "WINDOWTITLE eq Iris Engine*" >nul 2>&1
taskkill /F /FI "WINDOWTITLE eq Iris Web UI*" >nul 2>&1
taskkill /F /FI "WINDOWTITLE eq Iris Desktop App*" >nul 2>&1

echo [OK] All Iris AI background services and ports have been stopped.
echo.
ping -n 2 127.0.0.1 >nul
exit /b 0
