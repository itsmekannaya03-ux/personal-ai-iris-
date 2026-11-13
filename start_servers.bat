@echo off
setlocal EnableDelayedExpansion
title IRIS AI - Server Launcher
cd /d "%~dp0"

echo [1/3] Clearing old processes on ports 5743 and 8001...
powershell -NoProfile -Command "5743, 8001 | ForEach-Object { $p = Get-NetTCPConnection -LocalPort $_ -ErrorAction SilentlyContinue; if ($p) { Stop-Process -Id $p.OwningProcess -Force -ErrorAction SilentlyContinue } }"

echo [2/3] Activating virtual environment...
if exist ".venv\Scripts\activate.bat" (
    call ".venv\Scripts\activate.bat"
) else if exist "venv\Scripts\activate.bat" (
    call "venv\Scripts\activate.bat"
)

echo [3/3] Starting Engine and Backend API...
start "Engine [5743]" /B python runtime/bootstrap.py > engine_server.log 2>&1
timeout /t 3 /nobreak >nul

start "Backend API [8001]" /B python -m uvicorn backend.main:app --host 127.0.0.1 --port 8001 > backend_server.log 2>&1
timeout /t 3 /nobreak >nul

echo.
echo Engine Status (http://127.0.0.1:5743/status):
python -c "import urllib.request; print(urllib.request.urlopen('http://127.0.0.1:5743/status', timeout=5).read().decode())" 2>nul || echo Engine starting...

echo.
echo Backend Health (http://127.0.0.1:8001/health):
python -c "import urllib.request; print(urllib.request.urlopen('http://127.0.0.1:8001/health', timeout=5).read().decode())" 2>nul || echo Backend starting...

echo.
echo All servers launched in background.
pause
