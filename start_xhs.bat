@echo off
title XHS Platform Launcher
cd /d "%~dp0"

echo [1/2] Starting Backend Service on port 8000...
start "XHS_Backend" run_backend.bat

echo [2/2] Starting Frontend Service on port 5173...
start "XHS_Frontend" run_frontend.bat

echo Opening browser at http://127.0.0.1:5173...
ping 127.0.0.1 -n 3 >nul
start http://127.0.0.1:5173
