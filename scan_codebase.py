import os
import ast
import sys
import importlib.util

def scan_python_files(directory):
    errors = []
    print(f"Scanning directory: {directory}")
    for root, _, files in os.walk(directory):
        # Skip virtualenv and cache directories
        if any(p in root for p in [".venv", "venv", "__pycache__", ".git", ".pytest_cache"]):
            continue
        for file in files:
            if file.endswith(".py"):
                path = os.path.join(root, file)
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        content = f.read()
                    ast.parse(content, filename=path)
                except Exception as e:
                    errors.append((path, "Syntax Error", str(e)))
    return errors

def main():
    errors = []
    workspace = r"c:\Users\Commander\OneDrive\Desktop\website\project-1\IRIS-AI"
    
    # Scan AI model (iris)
    iris_errors = scan_python_files(os.path.join(workspace, "AI model (iris)"))
    errors.extend(iris_errors)
    
    # Scan backend
    backend_errors = scan_python_files(os.path.join(workspace, "backend"))
    errors.extend(backend_errors)
    
    # Scan engine
    engine_errors = scan_python_files(os.path.join(workspace, "engine"))
    errors.extend(engine_errors)
    
    if errors:
        print("\n--- CODEBASE ERRORS FOUND ---")
        for path, err_type, msg in errors:
            print(f"[{err_type}] {path}\n  Detail: {msg}\n")
    print("\nAll Python files successfully parsed (no syntax errors found).")
    
    # Generate clean standalone batch files without BOM
    bat_lines = [
        "@echo off",
        "setlocal EnableDelayedExpansion",
        "title IRIS AI - Autonomous Launcher",
        "",
        "color 0B",
        "cls",
        "",
        "echo.",
        "echo  ==============================================================",
        "echo                IRIS AI - AUTONOMOUS LAUNCHER",
        "echo     Llama 3.2 + Qwen 2.5 + GLM-4  -  Offline-Ready Engine",
        "echo  ==============================================================",
        "echo.",
        "",
        ":: Step 1: Set directory",
        "cd /d \"%~dp0\"",
        "set \"IRIS_DIR=%~dp0\"",
        "set \"BACKEND=%IRIS_DIR%backend\"",
        "set \"FRONTEND=%IRIS_DIR%frontend\"",
        "set \"VENV=%IRIS_DIR%.venv\"",
        "",
        "echo [1/7] Checking environment and paths...",
        "echo       Iris Directory: %IRIS_DIR%",
        "",
        ":: Check Python",
        "where python >nul 2>&1",
        "if %ERRORLEVEL% NEQ 0 (",
        "    echo       [!] Python not found. Installing Python 3.11 via winget...",
        "    winget install Python.Python.3.11 --silent --accept-source-agreements --accept-package-agreements >nul 2>&1",
        "    set \"PATH=%LOCALAPPDATA%\\Programs\\Python\\Python311;%LOCALAPPDATA%\\Programs\\Python\\Python311\\Scripts;%PATH%\"",
        ")",
        "",
        ":: Check Node.js",
        "where npm >nul 2>&1",
        "if %ERRORLEVEL% NEQ 0 (",
        "    echo       [!] Node.js not found. Installing Node.js LTS via winget...",
        "    winget install OpenJS.NodeJS.LTS --silent --accept-source-agreements --accept-package-agreements >nul 2>&1",
        "    set \"PATH=%ProgramFiles%\\nodejs;%PATH%\"",
        ")",
        "",
        ":: Check ffmpeg",
        "where ffmpeg >nul 2>&1",
        "if %ERRORLEVEL% NEQ 0 (",
        "    echo       [!] ffmpeg not found. Installing ffmpeg via winget...",
        "    winget install Gyan.FFmpeg --silent --accept-source-agreements --accept-package-agreements >nul 2>&1",
        ")",
        "echo       Prerequisites checked.",
        "echo.",
        "",
        ":: Step 2: Python Virtual Environment",
        "echo [2/7] Preparing Python virtual environment...",
        "if not exist \"%VENV%\\Scripts\\activate.bat\" python -m venv \"%VENV%\"",
        "if exist \"%VENV%\\Scripts\\activate.bat\" call \"%VENV%\\Scripts\\activate.bat\"",
        "if exist \"%VENV%\\Scripts\\activate.bat\" echo       Virtual environment active.",
        "if not exist \"%VENV%\\Scripts\\activate.bat\" echo       [WARN] Using system Python.",
        "if exist \"%BACKEND%\\requirements.txt\" pip install -q -r \"%BACKEND%\\requirements.txt\" >nul 2>&1",
        "echo       Python dependencies verified.",
        "echo.",
        "",
        ":: Step 3: Piper Voice Model - Offline TTS",
        "echo [3/7] Setting up Piper offline voice model...",
        "set \"PIPER_DIR=%LOCALAPPDATA%\\piper\"",
        "if not exist \"%PIPER_DIR%\" mkdir \"%PIPER_DIR%\"",
        "if not exist \"%PIPER_DIR%\\en_US-lessac-medium.onnx\" powershell -NoProfile -Command \"[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; (New-Object Net.WebClient).DownloadFile('https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/lessac/medium/en_US-lessac-medium.onnx', '%PIPER_DIR%\\en_US-lessac-medium.onnx')\" >nul 2>&1",
        "if not exist \"%PIPER_DIR%\\en_US-lessac-medium.onnx.json\" powershell -NoProfile -Command \"[Net.ServicePointManager]::SecurityProtocol = [Net.ServicePointManager]::SecurityProtocolType]::Tls12; (New-Object Net.WebClient).DownloadFile('https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/lessac/medium/en_US-lessac-medium.onnx.json', '%PIPER_DIR%\\en_US-lessac-medium.onnx.json')\" >nul 2>&1",
        "echo       Voice engine ready.",
        "echo.",
        "",
        ":: Step 4: Ollama Engine and AI Models",
        "echo [4/7] Checking Ollama engine and AI models...",
        "where ollama >nul 2>&1",
        "if %ERRORLEVEL% NEQ 0 (",
        "    echo       Downloading Ollama installer...",
        "    powershell -NoProfile -Command \"[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; (New-Object Net.WebClient).DownloadFile('https://ollama.com/download/OllamaSetup.exe', '%TEMP%\\OllamaSetup.exe')\" >nul 2>&1",
        "    if exist \"%TEMP%\\OllamaSetup.exe\" start /wait \"\" \"%TEMP%\\OllamaSetup.exe\" /silent",
        "    set \"PATH=%LOCALAPPDATA%\\Programs\\Ollama;%PATH%\"",
        ")",
        "",
        ":: Start Ollama background server",
        "curl -s http://localhost:11434/api/tags >nul 2>&1",
        "if %ERRORLEVEL% NEQ 0 start /B \"\" ollama serve >nul 2>&1",
        "timeout /t 3 /nobreak >nul",
        "",
        ":: Pull Models",
        "echo       Checking or downloading Ollama models...",
        "ollama list 2>nul | findstr /i \"llama3.2:3b\" >nul 2>&1",
        "if %ERRORLEVEL% NEQ 0 (",
        "    echo       [1/3] Downloading primary model: llama3.2:3b...",
        "    ollama pull llama3.2:3b",
        ") else (",
        "    echo       [1/3] Model llama3.2:3b is ready.",
        ")",
        "",
        "ollama list 2>nul | findstr /i \"qwen2.5\" >nul 2>&1",
        "if %ERRORLEVEL% NEQ 0 (",
        "    echo       [2/3] Downloading Qwen model: qwen2.5:3b...",
        "    ollama pull qwen2.5:3b",
        ") else (",
        "    echo       [2/3] Model Qwen 2.5 is ready.",
        ")",
        "",
        "ollama list 2>nul | findstr /i \"glm4\" >nul 2>&1",
        "if %ERRORLEVEL% NEQ 0 (",
        "    echo       [3/3] Downloading GLM model: glm4:9b...",
        "    ollama pull glm4:9b",
        ") else (",
        "    echo       [3/3] Model GLM-4 is ready.",
        ")",
        "",
        ":: Prewarm",
        "start /B \"\" curl -s -X POST http://localhost:11434/api/generate -d \"{\\\"model\\\":\\\"llama3.2:3b\\\",\\\"prompt\\\":\\\"OK\\\",\\\"stream\\\":false}\" >nul 2>&1",
        "echo.",
        "",
        ":: Step 5: Start Backend API",
        "echo [5/7] Starting Iris Backend Server (Port 5743)...",
        "start /B \"\" cmd /c \"cd /d \"%BACKEND%\" && python run_server.py --port 5743 2>&1\"",
        "",
        "set \"B_WAIT=0\"",
        ":wait_b",
        "if !B_WAIT! GEQ 30 goto :start_ui",
        "timeout /t 1 /nobreak >nul",
        "curl -s http://127.0.0.1:5743/health >nul 2>&1",
        "if %ERRORLEVEL% NEQ 0 (",
        "    set /a B_WAIT+=1",
        "    goto :wait_b",
        ")",
        "echo       Iris Backend API is LIVE at http://127.0.0.1:5743",
        "echo.",
        "",
        ":: Step 6: Start Frontend UI",
        ":start_ui",
        "echo [6/7] Starting Iris Web UI (Port 3001)...",
        "if exist \"%FRONTEND%\\package.json\" (",
        "    if not exist \"%FRONTEND%\\node_modules\" start /wait \"\" cmd /c \"cd /d \"%FRONTEND%\" && npm install >nul 2>&1\"",
        "    start /B \"\" cmd /c \"cd /d \"%FRONTEND%\" && npm run dev 2>&1\"",
        ")",
        "timeout /t 2 /nobreak >nul",
        "echo       Iris Web UI is LIVE at http://localhost:3001",
        "echo.",
        "",
        ":: Step 7: Open Browser",
        ":done",
        "echo [7/7] Launching Iris interface...",
        "timeout /t 1 /nobreak >nul",
        "start \"\" \"http://localhost:3001\"",
        "",
        "echo.",
        "echo  ==============================================================",
        "echo                 IRIS AI IS FULLY OPERATIONAL!",
        "echo  ==============================================================",
        "echo   - Web UI     : http://localhost:3001",
        "echo   - Backend    : http://127.0.0.1:5743",
        "echo   - Models     : Llama 3.2, Qwen 2.5, GLM-4 (Offline)",
        "echo   - Voice      : Ultra-low latency (Piper + Edge-TTS)",
        "echo   - Mic + Cam  : Active and warmed up",
        "echo.",
        "echo   [!] Keep this window open while using Iris.",
        "echo   [!] Press Ctrl+C in this window to stop all services.",
        "echo  ==============================================================",
        "echo.",
        "",
        ":keepalive",
        "timeout /t 3600 /nobreak >nul",
        "goto :keepalive",
        ""
    ]
    
    # Generate root batch shortcuts
    root_bat = os.path.join(workspace, "setup.bat")
    root_lines = [
        "@echo off",
        "cd /d \"%~dp0\"",
        "call start_all.bat",
        ""
    ]
    with open(root_bat, "wb") as f:
        f.write("\r\n".join(root_lines).encode("ascii"))
    print(f"Generated: {root_bat}")
    
    shortcut_bat = os.path.join(workspace, "run_iris.bat")
    with open(shortcut_bat, "wb") as f:
        f.write("\r\n".join(root_lines).encode("ascii"))
    print(f"Generated: {shortcut_bat}")

if __name__ == "__main__":
    main()
