@echo off
title IRIS AI - Master Autonomous Launcher
color 0B
cls

echo.
echo  ================================================================
echo                    IRIS AI - AUTONOMOUS LAUNCHER
echo              Backend (:5743) + Web UI (:3001)
echo  ================================================================
echo.

:: 1. Navigate to Project Root
cd /d "%~dp0"
set "PROJECT_ROOT=%~dp0"
if exist "%PROJECT_ROOT%iris.1 model\backend" (
    set "IRIS_MODEL_DIR=%PROJECT_ROOT%iris.1 model"
) else (
    set "IRIS_MODEL_DIR=%PROJECT_ROOT%AI model (iris)"
)
set "IRIS_BACKEND=%IRIS_MODEL_DIR%\backend"
set "IRIS_FRONTEND=%IRIS_MODEL_DIR%\frontend"

:: 2. Check Prerequisites
echo [1/5] Checking system environment...

where python >nul 2>&1
if errorlevel 1 goto :no_python

where npm >nul 2>&1
if errorlevel 1 goto :no_npm

echo       Python and Node.js detected.
goto :check_python_env

:no_python
echo.
echo  [ERROR] Python was not found in your system PATH.
echo  Please install Python 3.11+ and check "Add to PATH".
echo.
pause
exit /b 1

:no_npm
echo.
echo  [ERROR] Node.js / npm was not found in your system PATH.
echo  Please install Node.js LTS from https://nodejs.org.
echo.
pause
exit /b 1

:check_python_env
:: 3. Python Environment Selection
echo [2/5] Preparing Python environment...
set "PY_CMD=python"

if exist "%IRIS_MODEL_DIR%\.venv\Scripts\activate.bat" goto :act_iris_venv
if exist "%PROJECT_ROOT%.venv\Scripts\activate.bat" goto :act_root_venv
echo       Using system Python.
goto :clear_ports

:act_iris_venv
call "%IRIS_MODEL_DIR%\.venv\Scripts\activate.bat"
set "PY_CMD=%IRIS_MODEL_DIR%\.venv\Scripts\python.exe"
echo       Using Iris virtual environment (.venv).
goto :clear_ports

:act_root_venv
call "%PROJECT_ROOT%.venv\Scripts\activate.bat"
set "PY_CMD=%PROJECT_ROOT%.venv\Scripts\python.exe"
echo       Using virtual environment (.venv).
goto :clear_ports

:clear_ports
:: Validate selected Python command
"%PY_CMD%" -c "import sys" >nul 2>&1
if errorlevel 1 (
    echo.
    echo       [WARN] The selected Python environment is invalid or bound to another machine.
    echo       Attempting to use system Python...
    set "PY_CMD=python"
    python -c "import sys" >nul 2>&1
    if errorlevel 1 (
        echo.
        echo  [ERROR] Python cannot execute!
        echo  Please run "install.ps1" or "install.bat" to automatically configure IRIS on this PC.
        echo.
        pause
        exit /b 1
    )
)

:: 4. Free Ports 5743 and 3001
echo [3/5] Freeing occupied ports (5743, 3001)...
"%PY_CMD%" -c "import subprocess; [subprocess.run(f'taskkill /F /PID {p[-1]}', shell=True, capture_output=True) for port in (5743, 3001, 8001) for l in subprocess.run('netstat -ano', shell=True, capture_output=True, text=True).stdout.splitlines() if f':{port}' in l and 'LISTENING' in l and (p := l.strip().split()) and p[-1].isdigit() and p[-1] != '0']" >nul 2>&1

:: 5. Launch Backend and Frontend Services
echo [4/5] Starting Iris services...

echo       [1/2] Starting Iris Backend Server (Port 5743)...
pushd "%IRIS_BACKEND%"
start "Iris Engine [5743]" /B "%PY_CMD%" -u run_server.py --port 5743 > "%PROJECT_ROOT%engine_server.log" 2>&1
popd

if not exist "%IRIS_FRONTEND%\package.json" goto :verify_health
echo       [2/2] Starting Iris Web UI (Port 3001)...
if not exist "%IRIS_FRONTEND%\node_modules" goto :install_frontend_deps
goto :start_frontend_dev

:install_frontend_deps
echo       Installing frontend dependencies...
pushd "%IRIS_FRONTEND%"
call npm install >nul 2>&1
popd

:start_frontend_dev
pushd "%IRIS_FRONTEND%"
start "Iris Web UI [3001]" /B npm run dev > "%PROJECT_ROOT%frontend_server.log" 2>&1
popd

:verify_health
:: 6. Wait & Verify Live Endpoints
echo.
echo [5/5] Verifying system health...

set /a RETRIES=0

:poll_loop
ping -n 2 127.0.0.1 >nul
curl.exe -s -f http://127.0.0.1:5743/health >nul 2>&1
if not errorlevel 1 goto :backend_ready

set /a RETRIES+=1
if %RETRIES% geq 35 goto :backend_timeout
goto :poll_loop

:backend_ready
echo       [OK] Iris Backend API is LIVE at http://127.0.0.1:5743
goto :open_ui

:backend_timeout
echo       [WARN] Backend is taking time to start. Check engine_server.log for details.

:open_ui
ping -n 3 127.0.0.1 >nul
echo       Launching Iris Desktop Application Window...
start "Iris Desktop App" /B "%PY_CMD%" "%PROJECT_ROOT%run_app.py"

echo.
echo  ================================================================
echo                 IRIS AI IS FULLY OPERATIONAL!
echo  ================================================================
echo   * Web UI Dashboard : http://localhost:3001
echo   * Iris Engine API  : http://127.0.0.1:5743
echo.
echo   [!] Keep this console window open while using Iris.
echo   [!] Close this window to stop all services.
echo  ================================================================
echo.

:keepalive
ping -n 3600 127.0.0.1 >nul
goto :keepalive
