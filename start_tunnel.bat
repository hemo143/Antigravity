@echo off
title ProAV - Live Server
color 0A
echo.
echo  ==========================================
echo    ProAV Solutions - Starting Live Server
echo  ==========================================
echo.

REM Activate virtual environment
call venv\Scripts\activate.bat 2>nul

REM Apply any pending migrations
echo [1/3] Checking database...
python manage.py migrate --run-syncdb -v 0

REM Collect static files
echo [2/3] Preparing static files...
python manage.py collectstatic --no-input -v 0 2>nul

REM Start Django in background
echo [3/3] Starting web server...
start /B python manage.py runserver 8000 > django.log 2>&1

REM Wait for Django to start
timeout /t 4 /nobreak >nul

REM Start localtunnel and show URL
echo.
echo  ==========================================
echo   Getting your public URL...
echo  ==========================================
echo.
npx localtunnel --port 8000

pause
