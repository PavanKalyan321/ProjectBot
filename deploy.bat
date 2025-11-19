@echo off
echo ========================================
echo 🚀 AVIATOR BOT - DEPLOYMENT SCRIPT
echo ========================================

echo.
echo 📦 Installing Python dependencies...
pip install -r requirements.txt

echo.
echo ☁️ Installing cloud sync dependencies...
pip install gspread google-auth

echo.
echo 🔧 Checking Tesseract OCR...
if exist "C:\Program Files\Tesseract-OCR\tesseract.exe" (
    echo ✅ Tesseract OCR found
) else (
    echo ❌ Tesseract OCR not found!
    echo Please install from: https://github.com/UB-Mannheim/tesseract/wiki
    echo Install to: C:\Program Files\Tesseract-OCR\
    pause
)

echo.
echo 📁 Creating directories...
if not exist "logs" mkdir logs
if not exist "backups" mkdir backups
if not exist "models" mkdir models

echo.
echo ⚙️ Setting up configuration...
echo Ready to configure bot coordinates and settings.
echo.

echo ========================================
echo ✅ DEPLOYMENT COMPLETE!
echo ========================================
echo.
echo Next steps:
echo 1. Run: python backend/bot_modular.py
echo 2. Configure screen coordinates
echo 3. Set up Google Sheets (optional)
echo 4. Access dashboard: http://localhost:5000
echo.
pause