@echo off
REM Open 6 Chrome instances in incognito mode with specific window positions for 4K resolution
REM Assumes primary monitor is 4K (3840x2160) and browsers will be positioned on left half
REM Each browser window: 1920x1080 (half of 4K width, full 4K height divided by 3 for each row)

echo.
echo ============================================
echo Opening 6 Chrome Instances in Incognito Mode
echo ============================================
echo.
echo Layout:
echo  - Browsers positioned on left screen (1920x2160)
echo  - 3 rows x 2 columns configuration
echo  - Each window: 1920x1080
echo.
echo Row 1:
echo  Browser 0: Top-Left (0, 0) - 1920x1080
echo  Browser 1: Top-Right (1920, 0) - 1920x1080
echo.
echo Row 2:
echo  Browser 2: Mid-Left (0, 1080) - 1920x1080
echo  Browser 3: Mid-Right (1920, 1080) - 1920x1080
echo.
echo Row 3:
echo  Browser 4: Bottom-Left (0, 2160) - 1920x1080
echo  Browser 5: Bottom-Right (1920, 2160) - 1920x1080
echo.
echo ============================================
echo.

REM Define Chrome path (adjust if Chrome is in different location)
set CHROME_PATH=C:\Program Files\Google\Chrome\Application\chrome.exe

REM Check if Chrome is installed
if not exist "%CHROME_PATH%" (
    echo ❌ Chrome not found at: %CHROME_PATH%
    echo Please install Chrome or update the path in this batch file.
    pause
    exit /b 1
)

echo ✅ Chrome found at: %CHROME_PATH%
echo.

REM Delay between opening windows to prevent conflicts
set DELAY=1000

REM ============================================
REM ROW 1 - Top browsers (0 and 1)
REM ============================================

echo Opening Browser 0 (Top-Left) at position 0,0...
start "" "%CHROME_PATH%" --incognito --window-position=0,0 --window-size=1920,1080 "about:blank"
timeout /t 1 /nobreak

echo Opening Browser 1 (Top-Right) at position 1920,0...
start "" "%CHROME_PATH%" --incognito --window-position=1920,0 --window-size=1920,1080 "about:blank"
timeout /t 1 /nobreak

REM ============================================
REM ROW 2 - Middle browsers (2 and 3)
REM ============================================

echo Opening Browser 2 (Mid-Left) at position 0,1080...
start "" "%CHROME_PATH%" --incognito --window-position=0,1080 --window-size=1920,1080 "about:blank"
timeout /t 1 /nobreak

echo Opening Browser 3 (Mid-Right) at position 1920,1080...
start "" "%CHROME_PATH%" --incognito --window-position=1920,1080 --window-size=1920,1080 "about:blank"
timeout /t 1 /nobreak

REM ============================================
REM ROW 3 - Bottom browsers (4 and 5)
REM ============================================

echo Opening Browser 4 (Bottom-Left) at position 0,2160...
start "" "%CHROME_PATH%" --incognito --window-position=0,2160 --window-size=1920,1080 "about:blank"
timeout /t 1 /nobreak

echo Opening Browser 5 (Bottom-Right) at position 1920,2160...
start "" "%CHROME_PATH%" --incognito --window-position=1920,2160 --window-size=1920,1080 "about:blank"
timeout /t 1 /nobreak

echo.
echo ============================================
echo ✅ All 6 browsers opened in incognito mode!
echo ============================================
echo.
echo Next steps:
echo 1. Navigate to your game URL in each browser
echo 2. Run: python backend/multi_readregion.py
echo 3. Setup Browser 0 coordinates first
echo 4. Then setup remaining browsers one by one
echo.
echo Window Layout:
echo ┌──────────────────┬──────────────────┐
echo │   Browser 0      │   Browser 1      │
echo │  (0, 0)          │  (1920, 0)       │
echo ├──────────────────┼──────────────────┤
echo │   Browser 2      │   Browser 3      │
echo │  (0, 1080)       │  (1920, 1080)    │
echo ├──────────────────┼──────────────────┤
echo │   Browser 4      │   Browser 5      │
echo │  (0, 2160)       │  (1920, 2160)    │
echo └──────────────────┴──────────────────┘
echo.
pause
