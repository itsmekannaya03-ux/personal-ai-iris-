@echo off
title IRIS AI - Setup for New PC / Portable Drive
color 0A
cls

echo.
echo  ================================================================
echo             IRIS AI - PORTABLE SETUP & ENVIRONMENT RESTORE
echo  ================================================================
echo.

cd /d "%~dp0"
set "ROOT=%~dp0"

:: 1. Check Python
echo [1/5] Checking Python installation...
where python >nul 2>&1
if errorlevel 1 (
    echo.
    echo  [ERROR] Python is not installed or not in PATH!
    echo  Please install Python 3.11+ from https://www.python.org/downloads/
    echo  IMPORTANT: Make sure to check the box "Add Python to PATH" during installation.
    echo.
    pause
    exit /b 1
)
python --version
echo       [OK] Python detected.

:: 2. Check Node.js
echo.
echo [2/5] Checking Node.js / npm...
where npm >nul 2>&1
if errorlevel 1 (
    echo.
    echo  [ERROR] Node.js is not installed or not in PATH!
    echo  Please install Node.js LTS from https://nodejs.org/
    echo.
    pause
    exit /b 1
)
echo       [OK] Node.js and npm detected.

:: 3. Restore Memory & Profile to new PC (~/.iris)
echo.
echo [3/5] Restoring IRIS Memory, Profile & Encryption Keys to this PC...
set "IRIS_USER_DIR=%USERPROFILE%\.iris"
if not exist "%IRIS_USER_DIR%" mkdir "%IRIS_USER_DIR%"

if exist "%ROOT%data\iris_memory_backup" (
    xcopy /E /I /Y /Q "%ROOT%data\iris_memory_backup\*" "%IRIS_USER_DIR%\" >nul 2>&1
    echo       [OK] Memory database, encryption keys, and profiles restored to:
    echo            %IRIS_USER_DIR%
) else (
    echo       [INFO] No memory backup directory found; fresh profile will be created on start.
)

:: 4. Verify / Setup Python Virtual Environment
echo.
echo [4/5] Checking Python dependencies...
set "VENV_DIR=%ROOT%AI model (iris)\.venv"
set "NEED_INSTALL=0"

if not exist "%VENV_DIR%\Scripts\python.exe" (
    set "NEED_INSTALL=1"
) else (
    :: Test if this venv can execute on this PC (detects broken hardcoded paths)
    "%VENV_DIR%\Scripts\python.exe" -c "import sys" >nul 2>&1
    if errorlevel 1 (
        echo       [WARN] Existing .venv was created on another machine and has broken paths.
        echo       Rebuilding fresh virtual environment for this PC...
        rmdir /S /Q "%VENV_DIR%" >nul 2>&1
        set "NEED_INSTALL=1"
    )
)

if "%NEED_INSTALL%"=="1" (
    echo       Creating clean virtual environment (.venv)...
    python -m venv "%VENV_DIR%"
    echo       Installing required dependencies from requirements.txt...
    "%VENV_DIR%\Scripts\python.exe" -m pip install --upgrade pip >nul 2>&1
    "%VENV_DIR%\Scripts\python.exe" -m pip install -r "%ROOT%AI model (iris)\requirements.txt"
    echo       [OK] Python dependencies installed successfully.
) else (
    echo       [OK] Virtual environment is valid on this PC.
)

:: 5. Setup Frontend Dependencies
echo.
echo [5/5] Checking Web UI frontend...
if not exist "%ROOT%AI model (iris)\frontend\node_modules" (
    echo       Installing frontend npm packages...
    pushd "%ROOT%AI model (iris)\frontend"
    call npm install
    popd
) else (
    echo       [OK] Frontend packages already installed.
)

echo.
echo  ================================================================
echo             PORTABLE SETUP COMPLETE! READY TO LAUNCH
echo  ================================================================
echo.
echo  To start IRIS AI anytime on this PC:
echo    Double-click: start_all.bat
echo.
set /p LAUNCH_NOW="Launch IRIS AI right now? (Y/N, default Y): "
if /I "%LAUNCH_NOW%"=="N" goto :end
call "%ROOT%start_all.bat"

:end
exit /b 0
