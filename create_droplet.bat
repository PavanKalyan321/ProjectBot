@echo off
echo 🚀 DigitalOcean GPU Droplet Creator for Aviator Bot
echo.

REM Check if API token is provided
if "%1"=="" (
    echo ❌ Error: API token required
    echo.
    echo Usage: create_droplet.bat YOUR_API_TOKEN [droplet_name]
    echo.
    echo Get your API token from:
    echo https://cloud.digitalocean.com/account/api/tokens
    echo.
    pause
    exit /b 1
)

set API_TOKEN=%1
set DROPLET_NAME=%2
if "%DROPLET_NAME%"=="" set DROPLET_NAME=aviator-bot-gpu

echo 🔑 Using API token: %API_TOKEN:~0,8%...
echo 📛 Droplet name: %DROPLET_NAME%
echo.

REM Install requests if not available
python -c "import requests" 2>nul || (
    echo 📦 Installing requests library...
    pip install requests
    echo.
)

REM Create the droplet
echo 🚀 Creating GPU droplet...
python create_droplet_api.py --token %API_TOKEN% --name %DROPLET_NAME%

echo.
echo ✅ Droplet creation process completed!
echo.
pause