@echo off
REM High-Quality VNC Connection Script for 4 Bot Instances
REM Usage: Run this batch file to connect to all 4 bot instances simultaneously

setlocal enabledelayedexpansion

echo.
echo ════════════════════════════════════════════════════════════
echo     🎯 AVIATOR BOT - Multi-Instance VNC Connector
echo ════════════════════════════════════════════════════════════
echo.

REM Configuration
set HOST=142.93.158.30
set INSTANCE_1=5901
set INSTANCE_2=5902
set INSTANCE_3=5903
set INSTANCE_4=5904

REM Try to find TigerVNC Viewer
set "VIEWER_PATH="
if exist "C:\Program Files\TigerVNC\vncviewer.exe" (
    set "VIEWER_PATH=C:\Program Files\TigerVNC\vncviewer.exe"
) else if exist "C:\Program Files (x86)\TigerVNC\vncviewer.exe" (
    set "VIEWER_PATH=C:\Program Files (x86)\TigerVNC\vncviewer.exe"
) else if exist "C:\Program Files\RealVNC\VNC Viewer\vncviewer.exe" (
    set "VIEWER_PATH=C:\Program Files\RealVNC\VNC Viewer\vncviewer.exe"
) else (
    echo ERROR: VNC Viewer not found!
    echo.
    echo Please install one of:
    echo   1. TigerVNC: https://github.com/TigerVNC/tigervnc/releases
    echo   2. RealVNC: https://www.realvnc.com/download/viewer/
    echo.
    pause
    exit /b 1
)

echo Found VNC Viewer at: !VIEWER_PATH!
echo.
echo Connecting to 4 instances...
echo.

REM High-quality settings for VNC connections
set VNC_OPTS=-geometry 1920x1080 -depth 24

REM Launch all 4 VNC connections
echo Launching Instance 1 - Port %INSTANCE_1% (Web: http://localhost:5001)
start "" "!VIEWER_PATH!" %VNC_OPTS% %HOST%:%INSTANCE_1%

echo Launching Instance 2 - Port %INSTANCE_2% (Web: http://localhost:5002)
start "" "!VIEWER_PATH!" %VNC_OPTS% %HOST%:%INSTANCE_2%

echo Launching Instance 3 - Port %INSTANCE_3% (Web: http://localhost:5003)
start "" "!VIEWER_PATH!" %VNC_OPTS% %HOST%:%INSTANCE_3%

echo Launching Instance 4 - Port %INSTANCE_4% (Web: http://localhost:5004)
start "" "!VIEWER_PATH!" %VNC_OPTS% %HOST%:%INSTANCE_4%

echo.
echo ════════════════════════════════════════════════════════════
echo ✓ All 4 VNC connections launched!
echo ════════════════════════════════════════════════════════════
echo.
echo VNC CONNECTION DETAILS:
echo   Username: root
echo   Password: pavan
echo   Host: %HOST%
echo   Ports: 5901, 5902, 5903, 5904
echo.
echo Arrange the windows side-by-side for best experience:
echo   - Top-left: Instance 1 (Port %INSTANCE_1%)
echo   - Top-right: Instance 2 (Port %INSTANCE_2%)
echo   - Bottom-left: Instance 3 (Port %INSTANCE_3%)
echo   - Bottom-right: Instance 4 (Port %INSTANCE_4%)
echo.
echo SYSTEM STATUS:
echo   - All 4 XFCE desktop environments are running
echo   - All 4 Flask bot dashboards are active
echo   - NVIDIA GPU (RTX 4000 Ada) is available
echo.
echo ALTERNATIVE ACCESS METHODS:
echo   1. Web dashboards (via SSH tunnel):
echo      - Instance 1: http://localhost:5001
echo      - Instance 2: http://localhost:5002
echo      - Instance 3: http://localhost:5003
echo      - Instance 4: http://localhost:5004
echo.
echo   2. Set up SSH tunneling (run in PowerShell/CMD):
echo      ssh -i "C:\Project\aviator_key" -L 5001:localhost:5001 -L 5002:localhost:5002 -L 5003:localhost:5003 -L 5004:localhost:5004 root@%HOST%
echo.
echo QUALITY OPTIMIZATION:
echo   - In VNC Viewer settings, adjust for your connection:
echo     * High Quality: Set Preferred encoding to "Tight" or "ZRLE"
echo     * Fast Connection: Enable compression level 9
echo     * Slow Connection: Lower color depth or resolution
echo   - For RealVNC: View → Options → Experts → Set JPEG Quality to 95
echo   - Display size: 1920x1080 (Full HD) - adjust window size as needed
echo.
echo TROUBLESHOOTING:
echo   - If quality is poor: Adjust VNC viewer compression/encoding settings
echo   - If you see black screens, wait 5-10 seconds for XFCE to fully load
echo   - Check firewall settings if connections time out
echo   - Verify VNC viewer is updated to latest version
echo.
pause

