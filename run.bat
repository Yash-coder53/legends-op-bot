@echo off
title Rose Ultimate Bot
echo ================================
echo 🌹 Legend Ultimate Bot - Starting
echo ================================
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
    echo Creating .env file...
    copy .env.example .env
    echo.
    echo ⚠️  IMPORTANT: Edit .env file and add your BOT_TOKEN!
    echo Get token from @BotFather on Telegram
    echo.
    notepad .env
    pause
    exit /b 1
)

REM Create data directory
if not exist "data" (
    mkdir data
)

REM Run bot
echo.
echo ================================
echo Starting Legend Ultimate Bot...
echo ================================
echo.
python bot.py

REM If bot stops
pause
