@echo off
title IRIS AI - Fast Pendrive Transfer
color 0B
cls

echo.
echo  ================================================================
echo             IRIS AI - FAST PENDRIVE BACKUP AND TRANSFER
echo  ================================================================
echo.

cd /d "%~dp0"
set "SRC=%~dp0"
if "%SRC:~-1%"=="\" set "SRC=%SRC:~0,-1%"

:: 1. Detect USB Drive
set "USB_DRIVE=D:"
if not exist "%USB_DRIVE%\" (
    echo  [!] Drive D: was not detected.
    set /p USB_DRIVE="Enter your pendrive letter (e.g. E: or F:): "
)

if not exist "%USB_DRIVE%\" (
    echo  [ERROR] Cannot access drive %USB_DRIVE%
    pause
    exit /b 1
)

set "DEST=%USB_DRIVE%\IRIS-AI"
echo  Source:      %SRC%
echo  Destination: %DEST%
echo.

:: 2. Refresh Memory Backup
echo [1/3] Updating memory backup from ~/.iris...
set "MEM_SRC=%USERPROFILE%\.iris"
if not exist "%MEM_SRC%" set "MEM_SRC=%USERPROFILE%\.iris"
set "MEM_DST=%SRC%data\iris_memory_backup"
if exist "%MEM_SRC%" (
    if not exist "%MEM_DST%" mkdir "%MEM_DST%"
    xcopy /E /I /Y /Q "%MEM_SRC%\*" "%MEM_DST%\" >nul 2>&1
    echo       [OK] Memory database and encryption keys refreshed.
)

:: 3. Robocopy Clean Transfer (Excluding machine-bound .venv & bloated node_modules)
echo.
echo [2/3] Copying project files to %DEST%...
echo       (Excluding machine-specific .venv and temporary cache to copy in seconds)
echo.

robocopy "%SRC%" "%DEST%" /E /XD ".venv" "node_modules" ".next" ".git" "__pycache__" ".pytest_cache" ".qodo" /XF "*.log" "*.tmp" "screenshot_*.png" "*.mp4" "*.docx" /R:1 /W:1 /NP /NDL

:: 4. Verify ONNX Vision Models
echo.
echo [3/3] Verifying critical models & setup scripts on pendrive...
if exist "%DEST%\iris.1 model\vision\data\face_recognition_sface_2021dec.onnx" (
    echo       [OK] SFace Facial Recognition ONNX model transferred.
) else if exist "%DEST%\AI model (iris)\vision\data\face_recognition_sface_2021dec.onnx" (
    echo       [OK] SFace Facial Recognition ONNX model transferred.
) else (
    echo       [WARN] SFace model missing!
)

if exist "%DEST%\requirements.txt" (
    echo       [OK] requirements.txt transferred.
) else (
    echo       [WARN] requirements.txt missing!
)

if exist "%DEST%\setup_portable_new_pc.bat" (
    echo       [OK] setup_portable_new_pc.bat transferred.
)

echo.
echo  ================================================================
echo             TRANSFER COMPLETE!
echo  ================================================================
echo   Your pendrive is now fully loaded at: %DEST%
echo.
echo   To run on any other PC:
echo     1. Plug in this pendrive.
echo     2. Open folder IRIS-AI.
echo     3. Double-click: setup_portable_new_pc.bat
echo  ================================================================
echo.
pause
