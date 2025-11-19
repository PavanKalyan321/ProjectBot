@echo off
REM Connect to GPU Server and Setup

setlocal enabledelayedexpansion

REM Set your droplet IP
set DROPLET_IP=142.93.158.30
set SSH_KEY=C:\Project\aviator_key

echo.
echo ============================================
echo Connecting to GPU Server
echo IP: %DROPLET_IP%
echo ============================================
echo.

REM Check if SSH key exists
if not exist "%SSH_KEY%" (
    echo ERROR: SSH key not found at %SSH_KEY%
    pause
    exit /b 1
)

REM Connect to server
ssh -i "%SSH_KEY%" root@%DROPLET_IP%

pause
