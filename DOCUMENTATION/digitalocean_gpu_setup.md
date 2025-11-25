# 🚀 DigitalOcean GPU Setup - Aviator Bot

## 🎯 GPU Droplet Configuration

### **Recommended GPU Droplet**
```
Plan: GPU-Optimized
Size: g-2vcpu-8gb-nvidia-rtx-4000-ada (RTX 4000 Ada)
Region: NYC1, SFO3, or AMS3
OS: Ubuntu 22.04 LTS
Storage: 50GB SSD
```

### **Alternative Options**
```
Budget: g-2vcpu-8gb-nvidia-rtx-a4000 (RTX A4000)
Performance: g-4vcpu-16gb-nvidia-rtx-4000-ada (RTX 4000 Ada)
```

---

## 🛠️ Initial Server Setup

### **1. Create Droplet**
```bash
# Via DigitalOcean Control Panel:
# 1. Click "Create" → "Droplets"
# 2. Choose "GPU-Optimized"
# 3. Select RTX 4000 Ada configuration
# 4. Choose Ubuntu 22.04 LTS
# 5. Add SSH key or password
# 6. Create droplet
```

### **2. Connect to Server**
```bash
ssh root@your-droplet-ip
```

### **3. Update System**
```bash
apt update && apt upgrade -y
apt install -y curl wget git python3 python3-pip
```

---

## 🖥️ Desktop Environment Setup

### **Install Desktop Environment**
```bash
# Install XFCE (lightweight)
apt install -y xfce4 xfce4-goodies

# Install VNC Server
apt install -y tightvncserver

# Install Chrome
wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | apt-key add -
echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list
apt update
apt install -y google-chrome-stable
```

### **Configure VNC**
```bash
# Start VNC server (will prompt for password)
vncserver :1

# Kill VNC to configure
vncserver -kill :1

# Edit VNC startup script
nano ~/.vnc/xstartup
```

### **VNC Startup Script**
```bash
#!/bin/bash
xrdb $HOME/.Xresources
startxfce4 &
```

```bash
# Make executable
chmod +x ~/.vnc/xstartup

# Start VNC server
vncserver :1 -geometry 1920x1080 -depth 24
```

---

## 🐍 Python Environment Setup

### **Install Python Dependencies**
```bash
# Install system packages
apt install -y python3-opencv tesseract-ocr libtesseract-dev

# Install Python packages
pip3 install flask flask-socketio pandas numpy opencv-python
pip3 install pytesseract mss pyautogui keyboard
pip3 install gspread google-auth requests discord-webhook
pip3 install scikit-learn xgboost lightgbm catboost
```

### **Clone Bot Repository**
```bash
cd /root
git clone https://github.com/your-repo/aviator-bot.git
cd aviator-bot
pip3 install -r requirements.txt
```

---

## 🔧 GPU Configuration

### **Install NVIDIA Drivers**
```bash
# Check GPU
nvidia-smi

# If drivers not installed:
apt install -y nvidia-driver-535
reboot
```

### **Install CUDA (Optional)**
```bash
# For ML acceleration
wget https://developer.download.nvidia.com/compute/cuda/12.2.0/local_installers/cuda_12.2.0_535.54.03_linux.run
sh cuda_12.2.0_535.54.03_linux.run
```

---

## 🌐 Remote Access Setup

### **VNC Access**
```bash
# Start VNC server
vncserver :1 -geometry 1920x1080 -depth 24

# Access via VNC client:
# Address: your-droplet-ip:5901
# Password: your-vnc-password
```

### **SSH Tunnel (Secure)**
```bash
# From your local machine:
ssh -L 5901:localhost:5901 root@your-droplet-ip

# Then connect VNC to: localhost:5901
```

### **Web-based VNC (noVNC)**
```bash
# Install noVNC
apt install -y novnc websockify

# Start web VNC
websockify --web=/usr/share/novnc/ 6080 localhost:5901

# Access: http://your-droplet-ip:6080/vnc.html
```

---

## 🚀 Bot Deployment

### **Configure Bot**
```bash
cd /root/aviator-bot

# Set display for GUI apps
export DISPLAY=:1

# Run bot setup
python3 backend/bot_modular.py
```

### **Create Systemd Service**
```bash
nano /etc/systemd/system/aviator-bot.service
```

```ini
[Unit]
Description=Aviator Bot
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/aviator-bot
Environment=DISPLAY=:1
ExecStart=/usr/bin/python3 backend/bot_modular.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
# Enable and start service
systemctl enable aviator-bot
systemctl start aviator-bot
systemctl status aviator-bot
```

---

## 🔒 Security Configuration

### **Firewall Setup**
```bash
# Install UFW
apt install -y ufw

# Allow SSH, VNC, Dashboard
ufw allow 22
ufw allow 5901
ufw allow 5000
ufw allow 6080

# Enable firewall
ufw enable
```

### **Secure VNC**
```bash
# Create VNC service with authentication
nano /etc/systemd/system/vncserver@.service
```

```ini
[Unit]
Description=Start TightVNC server at startup
After=syslog.target network.target

[Service]
Type=forking
User=root
Group=root
WorkingDirectory=/root
ExecStartPre=-/usr/bin/vncserver -kill :%i > /dev/null 2>&1
ExecStart=/usr/bin/vncserver -depth 24 -geometry 1920x1080 :%i
ExecStop=/usr/bin/vncserver -kill :%i

[Install]
WantedBy=multi-user.target
```

```bash
systemctl enable vncserver@1.service
systemctl start vncserver@1.service
```

---

## 📊 Monitoring Setup

### **Install Monitoring Tools**
```bash
# Install htop, nvidia monitoring
apt install -y htop nvtop

# Create monitoring script
nano /root/monitor.sh
```

```bash
#!/bin/bash
echo "=== System Status ==="
date
echo "CPU Usage:"
top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1
echo "Memory Usage:"
free -h
echo "GPU Status:"
nvidia-smi --query-gpu=utilization.gpu,memory.used,memory.total --format=csv,noheader,nounits
echo "Bot Status:"
systemctl is-active aviator-bot
echo "====================="
```

```bash
chmod +x /root/monitor.sh

# Add to crontab for regular monitoring
crontab -e
# Add: */5 * * * * /root/monitor.sh >> /var/log/aviator-monitor.log
```

---

## 💰 Cost Optimization

### **GPU Droplet Costs**
```
RTX A4000: $0.952/hour (~$686/month)
RTX 4000 Ada: $1.19/hour (~$857/month)
```

### **Cost Saving Tips**
```bash
# 1. Use snapshots for backup instead of always-on
# 2. Scale down during low-activity periods
# 3. Use reserved instances for long-term (if available)
# 4. Monitor usage and optimize
```

---

## 🎯 Quick Start Commands

### **Complete Setup**
```bash
# 1. Create GPU droplet on DigitalOcean
# 2. SSH into server
ssh root@your-droplet-ip

# 3. Run setup script
curl -sSL https://raw.githubusercontent.com/your-repo/setup.sh | bash

# 4. Configure VNC
vncserver :1 -geometry 1920x1080

# 5. Access via VNC client
# Connect to: your-droplet-ip:5901
```

### **Access Points**
```
VNC: your-droplet-ip:5901
Web VNC: http://your-droplet-ip:6080/vnc.html
Dashboard: http://your-droplet-ip:5000
SSH: ssh root@your-droplet-ip
```

---

## 🔧 Troubleshooting

### **VNC Issues**
```bash
# Kill all VNC sessions
vncserver -kill :*

# Restart VNC
vncserver :1 -geometry 1920x1080 -depth 24

# Check VNC logs
cat ~/.vnc/*.log
```

### **Bot Issues**
```bash
# Check bot logs
journalctl -u aviator-bot -f

# Restart bot
systemctl restart aviator-bot

# Check display
echo $DISPLAY
export DISPLAY=:1
```

### **GPU Issues**
```bash
# Check GPU status
nvidia-smi

# Check drivers
nvidia-detector

# Reinstall drivers if needed
apt purge nvidia-*
apt install nvidia-driver-535
reboot
```

Your GPU-powered Aviator bot will be running 24/7 with remote access! 🚀