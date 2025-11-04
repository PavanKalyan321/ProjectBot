# Linux VM Setup Guide

## 🐧 Quick Setup for Linux

### Step 1: Install System Dependencies
```bash
# Update package list
sudo apt update

# Install Python and system dependencies
sudo apt install -y python3 python3-pip python3-venv git

# Install dependencies for screen capture and OCR
sudo apt install -y tesseract-ocr scrot python3-tk python3-dev xclip

# Install X11 development files (for pyautogui)
sudo apt install -y xdotool libxcb-xinerama0
```

### Step 2: Clone Repository
```bash
# Clone the project
cd ~
git clone https://github.com/PavanKalyan321/ProjectBot.git
cd ProjectBot/backend
```

### Step 3: Create Virtual Environment
```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate
```

### Step 4: Install Python Packages
```bash
# Install from requirements.txt
pip install -r ../requirements.txt

# Or install manually:
pip install numpy pandas opencv-python pytesseract scikit-learn mss pyautogui pyperclip keyboard pillow
```

### Step 5: Run the Bot
```bash
# Make sure virtual environment is activated (you should see (venv) in prompt)
python bot.py
```

---

## 🚀 Complete Installation Script

Save this as `install_linux.sh`:

```bash
#!/bin/bash

echo "Installing Aviator Bot on Linux..."

# Install system dependencies
echo "Installing system packages..."
sudo apt update
sudo apt install -y python3 python3-pip python3-venv git tesseract-ocr scrot python3-tk python3-dev xclip xdotool libxcb-xinerama0

# Navigate to backend
cd ~/ProjectBot/backend || exit

# Create virtual environment
echo "Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install Python packages
echo "Installing Python packages..."
pip install --upgrade pip
pip install -r ../requirements.txt

echo ""
echo "✅ Installation complete!"
echo ""
echo "To run the bot:"
echo "  1. cd ~/ProjectBot/backend"
echo "  2. source venv/bin/activate"
echo "  3. python bot.py"
echo ""
```

Then run:
```bash
chmod +x install_linux.sh
./install_linux.sh
```

---

## 📋 Every Time You Run the Bot

```bash
# 1. Navigate to backend
cd ~/ProjectBot/backend

# 2. Activate virtual environment
source venv/bin/activate

# 3. Run bot
python bot.py
```

---

## 🔧 Convenience Scripts

### Create Run Script
```bash
cat > ~/ProjectBot/backend/run.sh << 'EOF'
#!/bin/bash
cd ~/ProjectBot/backend
source venv/bin/activate
python bot.py
EOF

chmod +x ~/ProjectBot/backend/run.sh
```

**Usage:**
```bash
~/ProjectBot/backend/run.sh
```

### Create Validation Script
```bash
cat > ~/ProjectBot/backend/validate.sh << 'EOF'
#!/bin/bash
cd ~/ProjectBot/backend
source venv/bin/activate
python validate_coordinates.py
EOF

chmod +x ~/ProjectBot/backend/validate.sh
```

**Usage:**
```bash
~/ProjectBot/backend/validate.sh
```

---

## 🎯 Platform Differences

### Clipboard
- **Windows:** Uses `win32clipboard` (native, faster)
- **Linux:** Uses `pyperclip` (cross-platform, works great)

### Screen Capture
- **Windows:** Uses `mss` directly
- **Linux:** Uses `mss` with X11 (requires `xdotool`)

### Keyboard Control
- **Both:** Uses `pyautogui` (works on both platforms)

---

## ⚠️ Common Linux Issues

### Issue 1: "No module named 'Xlib'"
```bash
pip install python3-xlib
```

### Issue 2: "Tesseract not found"
```bash
sudo apt install tesseract-ocr tesseract-ocr-eng
```

### Issue 3: "Permission denied" for screen capture
```bash
# Run with proper display
export DISPLAY=:0
python bot.py
```

### Issue 4: Keyboard/mouse control not working
```bash
# Install xdotool
sudo apt install xdotool

# Check if running in X11 (not Wayland)
echo $XDG_SESSION_TYPE
# Should show "x11"
```

### Issue 5: Virtual environment not activating
```bash
# Make sure you have venv installed
sudo apt install python3-venv

# Recreate virtual environment
rm -rf venv
python3 -m venv venv
source venv/bin/activate
```

---

## 🖥️ Display Server Notes

### X11 (Recommended)
Works perfectly with all automation tools.

### Wayland
May have issues with keyboard/mouse automation. If using Wayland:

```bash
# Switch to X11 session
# Log out → Select "Ubuntu on Xorg" at login
```

Or set environment variable:
```bash
export GDK_BACKEND=x11
```

---

## 📊 Verification

After installation, verify everything works:

```bash
# Test Python
python --version  # Should show Python 3.8+

# Test imports
python -c "import mss, pyautogui, cv2, pytesseract; print('✅ All imports OK')"

# Test tesseract
tesseract --version

# Run validation
python validate_coordinates.py
```

---

## 🔄 Updating

```bash
cd ~/ProjectBot
git pull
cd backend
source venv/bin/activate
pip install --upgrade -r ../requirements.txt
```

---

## 💡 Performance Tips

### 1. Use X11 Instead of Wayland
```bash
# Better automation support
echo $XDG_SESSION_TYPE
# If shows "wayland", switch to X11
```

### 2. Disable Compositor (Optional)
```bash
# For faster screen capture
# In system settings, disable compositor/effects
```

### 3. Increase Process Priority (Optional)
```bash
# Run with higher priority
sudo nice -n -10 python bot.py
```

---

## 🎓 Quick Commands Reference

| Task | Command |
|------|---------|
| **Activate venv** | `source venv/bin/activate` |
| **Deactivate venv** | `deactivate` |
| **Run bot** | `python bot.py` |
| **Run validation** | `python validate_coordinates.py` |
| **Update code** | `git pull` |
| **Check Python** | `python --version` |
| **Install package** | `pip install PACKAGE` |
| **List packages** | `pip list` |

---

## ✅ Installation Checklist

- [ ] System packages installed (`apt install ...`)
- [ ] Tesseract OCR installed
- [ ] Virtual environment created
- [ ] Python packages installed
- [ ] Bot runs without errors
- [ ] Validation mode works
- [ ] Screen capture works
- [ ] Keyboard/mouse control works
- [ ] Clipboard operations work

---

## 🚨 If Everything Fails

Try the minimal installation:

```bash
# Install only core packages
pip install mss pyautogui pyperclip numpy pillow

# Test basic functionality
python -c "import mss, pyautogui, pyperclip; print('OK')"
```

Then add other packages one by one.

---

## 📞 Platform-Specific Help

### Ubuntu/Debian
All commands in this guide work directly.

### Fedora/RHEL
Replace `apt` with `dnf`:
```bash
sudo dnf install python3-devel tesseract xdotool
```

### Arch Linux
Replace `apt` with `pacman`:
```bash
sudo pacman -S python-pip tesseract xdotool
```

---

**The bot is now fully cross-platform compatible!** 🎉
