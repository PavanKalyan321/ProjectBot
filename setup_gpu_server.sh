#!/bin/bash

# 🚀 Aviator Bot - DigitalOcean GPU Server Setup Script
# Run with: curl -sSL https://raw.githubusercontent.com/your-repo/setup_gpu_server.sh | bash

set -e

echo "🚀 Starting Aviator Bot GPU Server Setup..."

# Update system
echo "📦 Updating system packages..."
apt update && apt upgrade -y

# Install essential packages
echo "🔧 Installing essential packages..."
apt install -y curl wget git python3 python3-pip build-essential

# Install desktop environment
echo "🖥️ Installing desktop environment..."
apt install -y xfce4 xfce4-goodies tightvncserver

# Install Chrome
echo "🌐 Installing Google Chrome..."
wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | apt-key add -
echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list
apt update
apt install -y google-chrome-stable

# Install system dependencies for bot
echo "🐍 Installing Python system dependencies..."
apt install -y python3-opencv tesseract-ocr libtesseract-dev

# Install Python packages
echo "📚 Installing Python packages..."
pip3 install --upgrade pip
pip3 install flask flask-socketio pandas numpy opencv-python
pip3 install pytesseract mss pyautogui keyboard
pip3 install gspread google-auth requests discord-webhook
pip3 install scikit-learn xgboost lightgbm catboost

# Setup VNC
echo "🔧 Configuring VNC server..."
mkdir -p ~/.vnc

# Create VNC password (you'll need to set this manually)
echo "⚠️  You'll need to set VNC password manually after setup"

# Create VNC startup script
cat > ~/.vnc/xstartup << 'EOF'
#!/bin/bash
xrdb $HOME/.Xresources
startxfce4 &
EOF

chmod +x ~/.vnc/xstartup

# Install noVNC for web access
echo "🌐 Installing web VNC access..."
apt install -y novnc websockify

# Setup firewall
echo "🔒 Configuring firewall..."
apt install -y ufw
ufw allow 22      # SSH
ufw allow 5901    # VNC
ufw allow 5000    # Dashboard
ufw allow 6080    # Web VNC
ufw --force enable

# Create bot directory
echo "📁 Creating bot directory..."
cd /root
if [ ! -d "aviator-bot" ]; then
    echo "📥 Please clone your bot repository manually:"
    echo "git clone https://github.com/your-repo/aviator-bot.git"
fi

# Create systemd service for VNC
echo "⚙️ Creating VNC service..."
cat > /etc/systemd/system/vncserver@.service << 'EOF'
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
EOF

# Create monitoring script
echo "📊 Creating monitoring script..."
cat > /root/monitor.sh << 'EOF'
#!/bin/bash
echo "=== Aviator Bot Server Status ==="
date
echo "CPU Usage:"
top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1
echo "Memory Usage:"
free -h
echo "GPU Status:"
if command -v nvidia-smi &> /dev/null; then
    nvidia-smi --query-gpu=utilization.gpu,memory.used,memory.total --format=csv,noheader,nounits
else
    echo "NVIDIA drivers not installed"
fi
echo "VNC Status:"
systemctl is-active vncserver@1 || echo "VNC not running"
echo "================================="
EOF

chmod +x /root/monitor.sh

# Create quick start script
echo "🚀 Creating quick start script..."
cat > /root/start_bot.sh << 'EOF'
#!/bin/bash
export DISPLAY=:1
cd /root/aviator-bot
python3 backend/bot_modular.py
EOF

chmod +x /root/start_bot.sh

echo "✅ Setup complete!"
echo ""
echo "🎯 Next Steps:"
echo "1. Set VNC password: vncserver :1"
echo "2. Clone your bot: git clone https://github.com/your-repo/aviator-bot.git"
echo "3. Start VNC service: systemctl enable vncserver@1 && systemctl start vncserver@1"
echo "4. Access via VNC: your-server-ip:5901"
echo "5. Start web VNC: websockify --web=/usr/share/novnc/ 6080 localhost:5901"
echo "6. Web access: http://your-server-ip:6080/vnc.html"
echo ""
echo "🔧 Useful commands:"
echo "Monitor: /root/monitor.sh"
echo "Start bot: /root/start_bot.sh"
echo "Check GPU: nvidia-smi"
echo ""
echo "Happy trading! 🚀💰"