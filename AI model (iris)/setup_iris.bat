@echo off
title IRIS AI - Autonomous Launcher
color 0B
cls

echo.
echo  ==============================================================
echo                IRIS AI - AUTONOMOUS LAUNCHER
echo              Backend (:5743) + Native Desktop Overlay
echo  ==============================================================
echo.

cd /d "%~dp0"
set "IRIS_DIR=%~dp0"
set "BACKEND=%IRIS_DIR%backend"
set "FRONTEND=%IRIS_DIR%frontend"

:: 1. Check Python
echo [1/5] Checking Python environment...

set "PY_CMD=python"
where python >nul 2>&1
if not errorlevel 1 goto :python_found

where py >nul 2>&1
if not errorlevel 1 (
    set "PY_CMD=py"
    goto :python_found
)

echo.
echo  [ERROR] Python is not installed or not in your system PATH.
echo  Please install Python 3.10+ from https://www.python.org/downloads/
echo  (Be sure to check "Add Python to PATH" during installation)
echo.
pause
exit /b 1

:python_found
echo       Python detected (%PY_CMD%).

:: Check Node.js
where npm >nul 2>&1
if errorlevel 1 (
    echo       Note: Node.js not detected. Iris will run with Native Desktop Overlay.
    set "HAS_NPM=0"
) else (
    echo       Node.js and npm detected.
    set "HAS_NPM=1"
)

:: 2. Python Environment Selection
echo [2/5] Preparing Python environment...

if exist "%IRIS_DIR%.venv\Scripts\activate.bat" goto :act_local_venv
if exist "%IRIS_DIR%..\.venv\Scripts\activate.bat" goto :act_parent_venv
goto :check_deps

:act_local_venv
call "%IRIS_DIR%.venv\Scripts\activate.bat"
set "PY_CMD=%IRIS_DIR%.venv\Scripts\python.exe"
echo       Using local virtual environment (.venv).
goto :check_deps

:act_parent_venv
call "%IRIS_DIR%..\.venv\Scripts\activate.bat"
set "PY_CMD=%IRIS_DIR%..\.venv\Scripts\python.exe"
echo       Using parent virtual environment (.venv).
goto :check_deps

:check_deps
echo       Checking dependencies...
"%PY_CMD%" -c "import fastapi, uvicorn" >nul 2>&1
if errorlevel 1 (
    echo       Installing core dependencies from requirements.txt...
    "%PY_CMD%" -m pip install -r "%IRIS_DIR%requirements.txt"
)

:: 3. Free ports 5743 and 3001
echo [3/5] Freeing occupied ports (5743, 3001)...
"%PY_CMD%" -c "import subprocess; [subprocess.run(f'taskkill /F /PID {p[-1]}', shell=True, capture_output=True) for port in (5743, 3001, 8001) for l in subprocess.run('netstat -ano', shell=True, capture_output=True, text=True).stdout.splitlines() if f':{port}' in l and 'LISTENING' in l and (p := l.strip().split()) and p[-1].isdigit() and p[-1] != '0']" >nul 2>&1

:: 4. Start Services
echo [4/5] Starting Iris services...

echo       [1/2] Starting Iris Backend Server (Port 5743)...
pushd "%BACKEND%"
start "Iris Backend [5743]" /B "%PY_CMD%" -u run_server.py --port 5743 > "%IRIS_DIR%backend_server.log" 2>&1
popd

if "%HAS_NPM%"=="0" goto :check_health
if not exist "%FRONTEND%\package.json" goto :check_health

echo       [2/2] Starting Iris Web UI (Port 3001)...
if not exist "%FRONTEND%\node_modules" goto :install_frontend
goto :run_frontend

:install_frontend
echo       Installing frontend dependencies...
pushd "%FRONTEND%"
call npm install >nul 2>&1
popd

:run_frontend
pushd "%FRONTEND%"
start "Iris Web UI [3001]" /B npm run dev > "%IRIS_DIR%frontend_server.log" 2>&1
popd

:check_health
:: 5. Health Check & Open Application
echo.
echo [5/5] Verifying system health...

set /a RETRIES=0

:poll_loop
ping -n 2 127.0.0.1 >nul
curl.exe -s -f http://127.0.0.1:5743/health >nul 2>&1
if not errorlevel 1 goto :backend_live

set /a RETRIES+=1
if %RETRIES% geq 35 goto :timeout_warning
goto :poll_loop

:backend_live
echo       [OK] Iris Backend API is LIVE at http://127.0.0.1:5743
goto :open_ui

:timeout_warning
echo       [WARN] Backend is taking time to start. Check backend_server.log.

:open_ui
ping -n 3 127.0.0.1 >nul
echo       Launching Iris Application...
if exist "%IRIS_DIR%run_app.py" (
    start "Iris Desktop App" /B "%PY_CMD%" "%IRIS_DIR%run_app.py"
) else if exist "%IRIS_DIR%..\run_app.py" (
    start "Iris Desktop App" /B "%PY_CMD%" "%IRIS_DIR%..\run_app.py"
) else if "%HAS_NPM%"=="1" (
    start "" http://127.0.0.1:3001
) else (
    start "" http://127.0.0.1:5743
)

echo.
echo  ==============================================================
echo                 IRIS AI IS FULLY OPERATIONAL!
echo  ==============================================================
echo   - Backend API: http://127.0.0.1:5743
if "%HAS_NPM%"=="1" (
    echo   - Web UI     : http://localhost:3001
)
echo.
echo   [!] Keep this window open while using Iris.
echo   [!] Close this window to stop all services.
echo  ==============================================================
echo.

:keepalive
ping -n 3600 127.0.0.1 >nul
goto :keepalive
