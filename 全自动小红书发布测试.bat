@echo off
chcp 65001 >nul
title 小红书全自动工作流测试
cd /d "%~dp0"

echo ===================================================
echo     小红书 + AliasMode 防封内核 全自动工作流
echo ===================================================
echo.
echo [特性] 
echo  1. 调起 D 盘 Camoufox C++ 防封浏览器内核
echo  2. 自动生成 3:4 比例高清笔记卡片
echo  3. 全自动导航、填入标题正文、上传图片
echo  4. 智能安全哨所：遇人机滑块自动挂起，手动通过后无缝继续！
echo.

.\venv\Scripts\python.exe scripts\xhs_mcp_workflow.py --demo

echo.
pause
