@echo off
title Aviator Bot - Production Mode

echo ========================================
echo 🚀 AVIATOR BOT - PRODUCTION STARTUP
echo ========================================

cd /d "%~dp0"

echo 📊 Starting dashboard server...
start "Dashboard" python run_dashboard.py

echo ⏳ Waiting for dashboard to initialize...
timeout /t 5 /nobreak >nul

echo 🤖 Starting bot in production mode...
python backend/bot_modular.py

echo.
echo ⏹️ Bot stopped. Press any key to restart...
pause >nul
goto :start