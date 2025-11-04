#!/bin/bash

echo "=========================================="
echo "  Aviator Bot - Linux Installation"
echo "=========================================="
echo ""

# Check if running on Linux
if [[ "$OSTYPE" != "linux-gnu"* ]]; then
    echo "❌ This script is for Linux only"
    echo "   For Windows, see WINDOWS_SETUP.md"
    exit 1
fi

echo "📦 Installing system dependencies..."
sudo apt update
sudo apt install -y python3 python3-pip python3-venv git tesseract-ocr scrot python3-tk python3-dev xclip xdotool libxcb-xinerama0

if [ $? -ne 0 ]; then
    echo "❌ Failed to install system packages"
    exit 1
fi

echo ""
echo "📁 Setting up project..."
cd backend || exit 1

echo ""
echo "🐍 Creating virtual environment..."
python3 -m venv venv

if [ $? -ne 0 ]; then
    echo "❌ Failed to create virtual environment"
    exit 1
fi

echo ""
echo "🔌 Activating virtual environment..."
source venv/bin/activate

echo ""
echo "📥 Installing Python packages..."
pip install --upgrade pip
pip install -r ../requirements.txt

if [ $? -ne 0 ]; then
    echo "❌ Failed to install Python packages"
    exit 1
fi

echo ""
echo "=========================================="
echo "  ✅ Installation Complete!"
echo "=========================================="
echo ""
echo "To run the bot:"
echo "  1. cd backend"
echo "  2. source venv/bin/activate"
echo "  3. python bot.py"
echo ""
echo "Quick start script created: backend/run.sh"
echo ""

# Create run script
cat > run.sh << 'RUNSCRIPT'
#!/bin/bash
cd "$(dirname "$0")"
source venv/bin/activate
python bot.py
RUNSCRIPT

chmod +x run.sh

# Create validation script
cat > validate.sh << 'VALSCRIPT'
#!/bin/bash
cd "$(dirname "$0")"
source venv/bin/activate
python validate_coordinates.py
VALSCRIPT

chmod +x validate.sh

echo "✅ Created run.sh - Run the bot"
echo "✅ Created validate.sh - Validate coordinates"
echo ""
echo "Usage:"
echo "  ./backend/run.sh       # Run the bot"
echo "  ./backend/validate.sh  # Validate setup"
echo ""
