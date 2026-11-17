@echo off
chcp 65001 >nul
title 小红书一站式智能运营平台 (XHS_ALL_IN_ONE)
cd /d "%~dp0"

echo ===============================================================
echo     正在启动 小红书一站式智能运营平台 (XHS_ALL_IN_ONE)
echo ===============================================================
echo.

echo [1/3] 正在启动后端服务 (FastAPI - 端口 8000)...
start "XHS_Backend" /min cmd /c "cd /d %~dp0 && call .\venv\Scripts\activate.bat && python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000"

echo [2/3] 正在启动前端控制台 (React - 端口 5173)...
start "XHS_Frontend" /min cmd /c "cd /d %~dp0frontend && npm run dev"

echo [3/3] 正在等待服务启动并自动打开浏览器...
timeout /t 3 /nobreak >nul
start http://127.0.0.1:5173

echo.
echo ===============================================================
echo  🎉 服务已成功在后台启动！
echo  控制台网址: http://127.0.0.1:5173
echo  如需关闭服务，可直接关闭后台弹出的命令窗口或任务管理器结束进程。
echo ===============================================================
echo.
timeout /t 5 >nul
exit
