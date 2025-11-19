@echo off
REM Open 6 Chrome instances in incognito mode across full 4K dual-monitor setup
REM Layout: 3 browsers per monitor in 2x3 grid
REM Assumes dual 4K monitors (7680x2160 total) or single 4K (3840x2160)

echo.
echo ============================================
echo Opening 6 Chrome Instances - Full Screen
echo ============================================
echo.
echo Configuration Options:
echo.
echo Option 1: DUAL 4K MONITORS (7680x2160 total)
echo  - Left Monitor: Browsers 0, 1, 2 (3840x2160)
echo  - Right Monitor: Browsers 3, 4, 5 (3840x2160)
echo.
echo Option 2: SINGLE 4K MONITOR (3840x2160)
echo  - All 6 browsers in 2x3 grid (1920x1080 each)
echo.
echo Which layout do you want?
echo.

set /p CHOICE="Enter 1 for dual monitors, 2 for single monitor: "

if "%CHOICE%"=="1" goto DUAL_MONITOR
if "%CHOICE%"=="2" goto SINGLE_MONITOR
echo Invalid choice. Exiting.
exit /b 1

:DUAL_MONITOR
echo.
echo Setting up for DUAL 4K MONITORS...
echo.

set CHROME_PATH=C:\Program Files\Google\Chrome\Application\chrome.exe

if not exist "%CHROME_PATH%" (
    echo ❌ Chrome not found at: %CHROME_PATH%
    pause
    exit /b 1
)

echo ✅ Chrome found
echo.

REM LEFT MONITOR - Browsers 0, 1, 2 (stacked vertically)
echo Opening LEFT MONITOR browsers (0, 1, 2)...

echo  Browser 0: Top-Left (0, 0) - 1920x720
start "" "%CHROME_PATH%" --incognito --window-position=0,0 --window-size=1920,720 "about:blank"
timeout /t 1 /nobreak

echo  Browser 1: Mid-Left (0, 720) - 1920x720
start "" "%CHROME_PATH%" --incognito --window-position=0,720 --window-size=1920,720 "about:blank"
timeout /t 1 /nobreak

echo  Browser 2: Bottom-Left (0, 1440) - 1920x720
start "" "%CHROME_PATH%" --incognito --window-position=0,1440 --window-size=1920,720 "about:blank"
timeout /t 1 /nobreak

REM RIGHT MONITOR - Browsers 3, 4, 5 (stacked vertically)
echo.
echo Opening RIGHT MONITOR browsers (3, 4, 5)...

echo  Browser 3: Top-Right (1920, 0) - 1920x720
start "" "%CHROME_PATH%" --incognito --window-position=1920,0 --window-size=1920,720 "about:blank"
timeout /t 1 /nobreak

echo  Browser 4: Mid-Right (1920, 720) - 1920x720
start "" "%CHROME_PATH%" --incognito --window-position=1920,720 --window-size=1920,720 "about:blank"
timeout /t 1 /nobreak

echo  Browser 5: Bottom-Right (1920, 1440) - 1920x720
start "" "%CHROME_PATH%" --incognito --window-position=1920,1440 --window-size=1920,720 "about:blank"
timeout /t 1 /nobreak

goto SUCCESS

:SINGLE_MONITOR
echo.
echo Setting up for SINGLE 4K MONITOR...
echo.

set CHROME_PATH=C:\Program Files\Google\Chrome\Application\chrome.exe

if not exist "%CHROME_PATH%" (
    echo ❌ Chrome not found at: %CHROME_PATH%
    pause
    exit /b 1
)

echo ✅ Chrome found
echo.

REM 2x3 GRID - Single 4K Monitor
echo Opening browsers in 2x3 grid (1920x1080 each)...

echo  Browser 0: Top-Left (0, 0) - 1920x1080
start "" "%CHROME_PATH%" --incognito --window-position=0,0 --window-size=1920,1080 "about:blank"
timeout /t 1 /nobreak

echo  Browser 1: Top-Right (1920, 0) - 1920x1080
start "" "%CHROME_PATH%" --incognito --window-position=1920,0 --window-size=1920,1080 "about:blank"
timeout /t 1 /nobreak

echo  Browser 2: Mid-Left (0, 1080) - 1920x1080
start "" "%CHROME_PATH%" --incognito --window-position=0,1080 --window-size=1920,1080 "about:blank"
timeout /t 1 /nobreak

echo  Browser 3: Mid-Right (1920, 1080) - 1920x1080
start "" "%CHROME_PATH%" --incognito --window-position=1920,1080 --window-size=1920,1080 "about:blank"
timeout /t 1 /nobreak

echo  Browser 4: Bottom-Left (0, 2160) - 1920x1080
start "" "%CHROME_PATH%" --incognito --window-position=0,2160 --window-size=1920,1080 "about:blank"
timeout /t 1 /nobreak

echo  Browser 5: Bottom-Right (1920, 2160) - 1920x1080
start "" "%CHROME_PATH%" --incognito --window-position=1920,2160 --window-size=1920,1080 "about:blank"
timeout /t 1 /nobreak

:SUCCESS
echo.
echo ============================================
echo ✅ All 6 browsers opened in incognito mode!
echo ============================================
echo.
echo Next steps:
echo 1. Navigate to your game URL in each browser
echo 2. Run: python backend/multi_readregion.py
echo 3. Follow the interactive setup for each browser
echo 4. All data will be logged to browser_X_data.csv
echo.
pause
