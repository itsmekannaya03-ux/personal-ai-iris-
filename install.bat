@echo off
title IRIS AI - Autonomous Installer
cd /d "%~dp0"
powershell -ExecutionPolicy Bypass -NoProfile -File "%~dp0install.ps1"
if errorlevel 1 (
    echo.
    echo  [!] Installer encountered an issue.
    pause
)
