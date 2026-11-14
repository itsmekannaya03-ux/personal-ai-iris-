@echo off
title IRIS AIOS - Backend Server (Port 8001)
cd /d "%~dp0"
echo ========================================================
echo   Starting IRIS AIOS Backend (FastAPI + Neon PostgreSQL)
echo ========================================================
echo.
if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" -m uvicorn backend.main:app --host 127.0.0.1 --port 8001 --reload
) else (
    python -m uvicorn backend.main:app --host 127.0.0.1 --port 8001 --reload
)
pause

