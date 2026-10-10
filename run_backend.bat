@echo off
title XHS Backend (Port 8000)
cd /d "%~dp0"
call .\venv\Scripts\activate.bat
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
pause
