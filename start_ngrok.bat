@echo off
title Pro Event - Live Server (ngrok)
color 0A
echo.
echo  ==========================================
echo    Pro Event - Starting with ngrok
echo  ==========================================
echo.
call venv\Scripts\activate.bat 2>nul
python start_ngrok.py
pause
