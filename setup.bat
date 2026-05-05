@echo off
echo ========================================
echo   Event Management System - Setup
echo ========================================
echo.

echo [1/5] Creating virtual environment...
python -m venv venv

echo [2/5] Activating virtual environment...
call venv\Scripts\activate

echo [3/5] Installing requirements...
pip install -r requirements.txt

echo [4/5] Running database migrations...
python manage.py migrate

echo [5/5] Creating superuser...
echo Please create an admin account:
python manage.py createsuperuser

echo.
echo ========================================
echo   Setup Complete!
echo   Run: python manage.py runserver
echo   Open: http://127.0.0.1:8000
echo ========================================
pause
