@echo off
echo.
echo ========================================
echo   RESTARTING DASHBOARD
echo ========================================
echo.
echo Stopping any running dashboard...
taskkill /F /FI "WINDOWTITLE eq Aviator Dashboard*" 2>nul
timeout /t 2 /nobreak >nul

echo Starting dashboard...
start "Aviator Dashboard" cmd /k "cd /d %~dp0 && python run_dashboard.py"

echo.
echo ========================================
echo   DASHBOARD RESTARTED!
echo ========================================
echo.
echo URL: http://localhost:5001
echo.
pause
