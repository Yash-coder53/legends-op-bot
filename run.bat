@echo off
echo Starting Legend Ultimate Bot...
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python not found! Install Python 3.8+
    pause
    exit /b 1
)

REM Check virtual environment
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate venv
call venv\Scripts\activate.bat

REM Install requirements
echo Installing requirements...
pip install -r requirements.txt

REM Check .env file
if not exist ".env" (
    echo Creating .env file from example...
    copy .env.example .env
    echo Please edit .env file and add your BOT_TOKEN!
    pause
    exit /b 1
)

REM Run bot
echo Starting bot...
python bot.py

pause
