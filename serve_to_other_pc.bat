@echo off
title IRIS AI - Wi-Fi Network Distribution Server
color 0B
cls

cd /d "%~dp0"

echo.
echo  ================================================================
echo             IRIS AI - WI-FI NETWORK DISTRIBUTION SERVER
echo  ================================================================
echo.
echo  Preparing clean 78 MB package...
node scripts/make_package.js

echo.
echo  Starting local distribution server...
node scripts/dist_server.js
pause

