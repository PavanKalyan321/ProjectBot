# 🚀 Deployment Guide - Aviator Bot

## 📦 Deployment Options

### **Option 1: VPS/Cloud Server (Recommended)**
- **AWS EC2** / **DigitalOcean** / **Vultr** / **Linode**
- Windows Server with GUI (for screen capture)
- 2GB RAM minimum, 4GB recommended

### **Option 2: Local Server/PC**
- Dedicated Windows PC running 24/7
- Stable internet connection
- Remote desktop access

---

## 🛠️ VPS Setup (Windows Server)

### **1. Create VPS Instance**
```bash
# AWS EC2 - Windows Server 2022
# Instance type: t3.medium (2 vCPU, 4GB RAM)
# Storage: 30GB SSD
# Security Group: RDP (3389), HTTP (80), Custom (5000-5001)
```

### **2. Connect via RDP**
```bash
# Use Remote Desktop Connection
# IP: your-vps-ip
# Username: Administrator
# Password: from-vps-provider
```

### **3. Install Requirements**
```powershell
# Install Python 3.9+
# Download from: https://www.python.org/downloads/

# Install Git
# Download from: https://git-scm.com/download/win

# Install Chrome Browser (for Aviator game)
# Download from: https://www.google.com/chrome/
```

---

## 📁 Application Deployment

### **1. Clone Repository**
```bash
cd C:\
git clone https://github.com/your-repo/aviator-bot.git
cd aviator-bot
```

### **2. Install Dependencies**
```bash
pip install -r requirements.txt
pip install gspread google-auth
```

### **3. Setup Tesseract OCR**
```bash
# Download and install Tesseract
# https://github.com/UB-Mannheim/tesseract/wiki
# Install to: C:\Program Files\Tesseract-OCR\
```

### **4. Configure Bot**
```bash
# Run initial setup
python backend/bot_modular.py

# Configure coordinates for your screen resolution
# Set up Google Sheets credentials (optional)
```

---

## 🔄 Auto-Start Setup

### **Create Startup Script**
```batch
@echo off
cd C:\aviator-bot
python backend/bot_modular.py
pause
```
Save as `start_bot.bat`

### **Windows Task Scheduler**
```powershell
# Open Task Scheduler
# Create Basic Task
# Name: Aviator Bot
# Trigger: At startup
# Action: Start program
# Program: C:\aviator-bot\start_bot.bat
```

---

## 🌐 Web Dashboard Access

### **Setup Remote Access**
```python
# In bot_modular.py, change dashboard port
bot.dashboard = AviatorDashboard(bot, port=5000, host='0.0.0.0')
```

### **Access Dashboard**
```
http://your-vps-ip:5000
```

---

## 🔒 Security Setup

### **1. Windows Firewall**
```powershell
# Allow dashboard port
New-NetFirewallRule -DisplayName "Aviator Dashboard" -Direction Inbound -Port 5000 -Protocol TCP -Action Allow
```

### **2. VPS Security Group**
```bash
# Allow ports: 3389 (RDP), 5000 (Dashboard)
# Restrict RDP to your IP only
```

### **3. Strong Passwords**
```bash
# Change default Administrator password
# Use complex password with 2FA if available
```

---

## 📊 Monitoring & Logs

### **Create Log Directory**
```bash
mkdir C:\aviator-bot\logs
```

### **Log Rotation Script**
```python
# logs/rotate_logs.py
import os
import shutil
from datetime import datetime

def rotate_logs():
    log_dir = "C:/aviator-bot/logs"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Archive old logs
    if os.path.exists("aviator_rounds_history.csv"):
        shutil.copy2("aviator_rounds_history.csv", f"{log_dir}/history_{timestamp}.csv")

if __name__ == "__main__":
    rotate_logs()
```

---

## 🚀 Production Deployment Commands

### **Quick Deploy Script**
```batch
@echo off
echo 🚀 Deploying Aviator Bot...

echo 📦 Installing dependencies...
pip install -r requirements.txt
pip install gspread google-auth

echo 🔧 Setting up Tesseract...
echo Please install Tesseract manually from:
echo https://github.com/UB-Mannheim/tesseract/wiki

echo ⚙️ Configuring bot...
python backend/bot_modular.py

echo ✅ Deployment complete!
echo Access dashboard at: http://localhost:5000
pause
```
Save as `deploy.bat`

### **Run Deployment**
```bash
# On your VPS
cd C:\aviator-bot
deploy.bat
```

---

## 📱 Remote Management

### **TeamViewer (Easy)**
```bash
# Install TeamViewer on VPS
# Access from anywhere with TeamViewer app
```

### **Chrome Remote Desktop**
```bash
# Install Chrome Remote Desktop
# Access via browser from anywhere
```

### **VNC Server**
```bash
# Install TightVNC Server
# Access via VNC client
```

---

## 🔄 Maintenance Scripts

### **Auto-Update Script**
```batch
@echo off
cd C:\aviator-bot
git pull origin main
pip install -r requirements.txt --upgrade
echo ✅ Update complete!
pause
```

### **Backup Script**
```batch
@echo off
set timestamp=%date:~-4,4%%date:~-10,2%%date:~-7,2%_%time:~0,2%%time:~3,2%
mkdir C:\aviator-bot\backups\%timestamp%
copy *.csv C:\aviator-bot\backups\%timestamp%\
copy *.json C:\aviator-bot\backups\%timestamp%\
echo ✅ Backup created: %timestamp%
```

---

## 💰 Cost Estimates

### **VPS Costs (Monthly)**
- **DigitalOcean**: $24/month (4GB RAM)
- **Vultr**: $20/month (4GB RAM)  
- **AWS EC2**: $30-50/month (t3.medium)
- **Linode**: $24/month (4GB RAM)

### **Additional Costs**
- **Domain name**: $10-15/year (optional)
- **SSL certificate**: Free (Let's Encrypt)
- **Backup storage**: $5-10/month (optional)

---

## 🎯 Quick Start Commands

### **Deploy to VPS**
```bash
# 1. Create Windows VPS
# 2. Connect via RDP
# 3. Run these commands:

cd C:\
git clone your-repo
cd aviator-bot
pip install -r requirements.txt
python backend/bot_modular.py
```

### **Access Remotely**
```bash
# Dashboard: http://vps-ip:5000
# RDP: vps-ip:3389
# TeamViewer: ID from VPS
```

Your bot will run 24/7 on the VPS with remote dashboard access!