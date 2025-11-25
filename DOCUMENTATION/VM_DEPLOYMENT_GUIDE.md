# VM Deployment Guide - Aviator Bot

Complete guide for deploying the Aviator Bot to a Virtual Machine.

---

## Table of Contents

1. [Quick Start - Recommended Method](#quick-start---recommended-method)
2. [Option 1: Docker Deployment](#option-1-docker-deployment-recommended)
3. [Option 2: Direct Python Installation](#option-2-direct-python-installation)
4. [Option 3: Cloud VM Setup](#option-3-cloud-vm-with-vncrdp)
5. [Post-Deployment Configuration](#post-deployment-configuration)
6. [Troubleshooting](#troubleshooting)

---

## Quick Start - Recommended Method

For the fastest deployment, use **Ubuntu VM + Automated Script**:

```bash
# 1. SSH into your VM
ssh user@your-vm-ip

# 2. Download and run the automated setup script
wget https://raw.githubusercontent.com/your-repo/setup_vm.sh
chmod +x setup_vm.sh
sudo ./setup_vm.sh

# 3. Start the bot
cd /opt/aviator-bot
python3 run_dashboard.py &  # Dashboard in background
cd backend && python3 bot.py  # Interactive bot
```

**Time to Deploy**: ~10 minutes

---

## Option 1: Docker Deployment (RECOMMENDED)

### Prerequisites
- VM with Ubuntu 20.04+ or Windows Server
- Docker installed
- X11 forwarding (for GUI automation)

### Step 1: Prepare Your VM

#### For Ubuntu VM:
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install X11 and VNC for display
sudo apt install -y xvfb x11vnc fluxbox
```

#### For Windows VM:
```powershell
# Install Docker Desktop
# Download from: https://www.docker.com/products/docker-desktop
```

### Step 2: Clone and Build

```bash
# Clone your repository
git clone https://github.com/your-repo/aviator-bot.git
cd aviator-bot

# Build Docker image
docker build -t aviator-bot:latest .
```

### Step 3: Run with Display Support

#### Linux (with X11):
```bash
# Start virtual display
Xvfb :99 -screen 0 1920x1080x24 &
export DISPLAY=:99

# Run bot container
docker run -d \
  --name aviator-bot \
  -e DISPLAY=$DISPLAY \
  -v /tmp/.X11-unix:/tmp/.X11-unix \
  -v $(pwd)/backend:/app/backend \
  -p 5001:5001 \
  aviator-bot:latest

# View display via VNC (optional)
x11vnc -display :99 -nopw -forever &
```

#### Windows (with Docker Desktop):
```powershell
# Run bot container
docker run -d `
  --name aviator-bot `
  -v ${PWD}/backend:/app/backend `
  -p 5001:5001 `
  aviator-bot:latest
```

### Step 4: Access Dashboard

Open browser: `http://your-vm-ip:5001`

---

## Option 2: Direct Python Installation

### For Ubuntu VM (20.04+)

#### Step 1: System Dependencies
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python and pip
sudo apt install -y python3.9 python3-pip python3-venv

# Install Tesseract OCR
sudo apt install -y tesseract-ocr libtesseract-dev

# Install OpenCV dependencies
sudo apt install -y libgl1-mesa-glx libglib2.0-0 libsm6 libxext6 libxrender-dev

# Install GUI automation tools
sudo apt install -y scrot xdotool xvfb

# Install VNC for remote display (optional)
sudo apt install -y x11vnc xvfb fluxbox
```

#### Step 2: Clone and Setup
```bash
# Create application directory
sudo mkdir -p /opt/aviator-bot
sudo chown $USER:$USER /opt/aviator-bot

# Clone repository
git clone https://github.com/your-repo/aviator-bot.git /opt/aviator-bot
cd /opt/aviator-bot

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

#### Step 3: Configure Environment
```bash
# Create .env file
cat > .env << EOF
TESSERACT_PATH=/usr/bin/tesseract
DISPLAY=:99
BOT_MODE=dry_run
INITIAL_STAKE=25
MAX_STAKE=1000
EOF
```

#### Step 4: Setup Virtual Display
```bash
# Start Xvfb (virtual framebuffer)
Xvfb :99 -screen 0 1920x1080x24 &
export DISPLAY=:99

# Start window manager
fluxbox &

# Start VNC server for remote viewing
x11vnc -display :99 -forever -nopw -listen 0.0.0.0 -xkb &
```

#### Step 5: Start Services
```bash
# Terminal 1: Dashboard
source venv/bin/activate
python3 run_dashboard.py &

# Terminal 2: Bot
cd backend
python3 bot.py
```

### For Windows Server VM

#### Step 1: Install Requirements
```powershell
# Install Python 3.9+
# Download from: https://www.python.org/downloads/

# Install Tesseract OCR
# Download from: https://github.com/UB-Mannheim/tesseract/wiki
# Install to: C:\Program Files\Tesseract-OCR

# Add Tesseract to PATH
$env:Path += ";C:\Program Files\Tesseract-OCR"
```

#### Step 2: Setup Project
```powershell
# Clone repository
git clone https://github.com/your-repo/aviator-bot.git C:\aviator-bot
cd C:\aviator-bot

# Create virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

#### Step 3: Run Services
```powershell
# Start dashboard
Start-Process python -ArgumentList "run_dashboard.py" -NoNewWindow

# Start bot (interactive)
cd backend
python bot.py
```

---

## Option 3: Cloud VM with VNC/RDP

### AWS EC2 Setup

#### Step 1: Launch Instance
```bash
# Instance Type: t3.medium or better (2 vCPU, 4GB RAM)
# AMI: Ubuntu Server 22.04 LTS
# Storage: 20GB minimum
# Security Group: Open ports 22 (SSH), 5001 (Dashboard), 5900 (VNC)
```

#### Step 2: Connect and Setup
```bash
# SSH into instance
ssh -i your-key.pem ubuntu@ec2-ip-address

# Run automated setup
curl -o setup.sh https://your-scripts/ubuntu_setup.sh
chmod +x setup.sh
sudo ./setup.sh
```

### DigitalOcean Droplet Setup

#### Step 1: Create Droplet
```bash
# Size: Basic - 2 vCPU, 4GB RAM ($24/month)
# Image: Ubuntu 22.04 (LTS) x64
# Datacenter: Choose closest to you
# Add SSH key
```

#### Step 2: Initial Setup
```bash
# SSH into droplet
ssh root@droplet-ip

# Create non-root user
adduser aviator
usermod -aG sudo aviator
su - aviator

# Run setup script (see Option 2 above)
```

### VNC Access Setup

```bash
# Install desktop environment (lightweight)
sudo apt install -y xfce4 xfce4-goodies

# Configure VNC server
sudo apt install -y tightvncserver

# Start VNC server
vncserver :1 -geometry 1920x1080 -depth 24

# Set VNC password when prompted
```

**Connect via VNC Viewer**: `your-vm-ip:5901`

---

## Post-Deployment Configuration

### 1. Setup Auto-Start with Systemd

#### Dashboard Service
```bash
sudo nano /etc/systemd/system/aviator-dashboard.service
```

```ini
[Unit]
Description=Aviator Bot Dashboard
After=network.target

[Service]
Type=simple
User=aviator
WorkingDirectory=/opt/aviator-bot
Environment="DISPLAY=:99"
ExecStart=/opt/aviator-bot/venv/bin/python3 /opt/aviator-bot/run_dashboard.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

#### Bot Service
```bash
sudo nano /etc/systemd/system/aviator-bot.service
```

```ini
[Unit]
Description=Aviator Bot Service
After=network.target aviator-dashboard.service

[Service]
Type=simple
User=aviator
WorkingDirectory=/opt/aviator-bot/backend
Environment="DISPLAY=:99"
ExecStart=/opt/aviator-bot/venv/bin/python3 /opt/aviator-bot/backend/bot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

#### Enable Services
```bash
sudo systemctl daemon-reload
sudo systemctl enable aviator-dashboard
sudo systemctl enable aviator-bot
sudo systemctl start aviator-dashboard
sudo systemctl start aviator-bot
```

### 2. Setup Firewall

```bash
# UFW (Ubuntu)
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 5001/tcp  # Dashboard
sudo ufw allow 5900/tcp  # VNC (optional)
sudo ufw enable
```

### 3. Configure Nginx Reverse Proxy (Optional)

```bash
sudo apt install -y nginx

sudo nano /etc/nginx/sites-available/aviator-dashboard
```

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:5001;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
}
```

```bash
sudo ln -s /etc/nginx/sites-available/aviator-dashboard /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### 4. Setup Monitoring

```bash
# Install monitoring script
cp backend/monitor_bot.py /opt/aviator-bot/
chmod +x /opt/aviator-bot/monitor_bot.py

# Add cron job for health checks
crontab -e
```

Add:
```cron
*/5 * * * * /opt/aviator-bot/venv/bin/python3 /opt/aviator-bot/monitor_bot.py >> /var/log/aviator-monitor.log 2>&1
```

### 5. Setup Log Rotation

```bash
sudo nano /etc/logrotate.d/aviator-bot
```

```conf
/opt/aviator-bot/backend/*.log {
    daily
    rotate 7
    compress
    delaycompress
    notifempty
    create 0644 aviator aviator
}
```

---

## Accessing the Bot Remotely

### SSH Access
```bash
ssh -L 5001:localhost:5001 user@vm-ip
# Then open: http://localhost:5001
```

### VNC Access
```bash
# From your local machine
vncviewer vm-ip:5901
```

### Web Dashboard
```
http://vm-ip:5001
```

---

## Troubleshooting

### Issue: "No display found"
```bash
# Ensure Xvfb is running
ps aux | grep Xvfb
# If not, start it:
Xvfb :99 -screen 0 1920x1080x24 &
export DISPLAY=:99
```

### Issue: "Tesseract not found"
```bash
# Ubuntu
sudo apt install -y tesseract-ocr
# Verify installation
tesseract --version
```

### Issue: "Permission denied on files"
```bash
sudo chown -R $USER:$USER /opt/aviator-bot
chmod -R 755 /opt/aviator-bot
```

### Issue: "Port 5001 already in use"
```bash
# Find process using port
sudo netstat -tulpn | grep 5001
# Kill process
sudo kill -9 <PID>
```

### Issue: "Screen capture fails"
```bash
# Install missing dependencies
sudo apt install -y python3-tk python3-dev
pip install --upgrade mss pillow
```

### Issue: "Bot crashes on startup"
```bash
# Check logs
tail -f /opt/aviator-bot/backend/bot_session_*.log

# Check service status
sudo systemctl status aviator-bot
sudo journalctl -u aviator-bot -n 50
```

---

## Performance Optimization

### 1. Increase VM Resources
- **CPU**: 2+ cores recommended for ML models
- **RAM**: 4GB minimum, 8GB recommended
- **Storage**: 20GB minimum

### 2. Optimize Python
```bash
# Use PyPy for better performance (optional)
sudo apt install -y pypy3 pypy3-dev
```

### 3. Database Optimization
```bash
# Run data cleanup regularly
cd /opt/aviator-bot
python3 cleanup_data.py
```

### 4. Monitor Resource Usage
```bash
# Install htop
sudo apt install -y htop
htop

# Monitor logs in real-time
tail -f backend/bot_session_*.log
```

---

## Security Best Practices

1. **Change default passwords**
2. **Use SSH keys** (disable password auth)
3. **Keep system updated**: `sudo apt update && sudo apt upgrade`
4. **Use firewall**: Only open necessary ports
5. **Enable fail2ban**: `sudo apt install fail2ban`
6. **Regular backups**: Backup CSV files and config
7. **Use HTTPS**: Setup SSL certificate with Let's Encrypt
8. **Environment variables**: Never commit `.env` to git

---

## Backup Strategy

### Automated Backup Script
```bash
#!/bin/bash
BACKUP_DIR="/opt/backups/aviator"
mkdir -p $BACKUP_DIR

DATE=$(date +%Y%m%d_%H%M%S)
tar -czf "$BACKUP_DIR/aviator_backup_$DATE.tar.gz" \
  /opt/aviator-bot/backend/*.csv \
  /opt/aviator-bot/backend/*.json \
  /opt/aviator-bot/.env

# Keep only last 7 backups
ls -t $BACKUP_DIR/aviator_backup_*.tar.gz | tail -n +8 | xargs rm -f
```

Save as `/opt/aviator-bot/backup.sh` and add to cron:
```bash
0 */6 * * * /opt/aviator-bot/backup.sh
```

---

## Cost Estimates

### AWS EC2
- **t3.medium**: ~$30/month (on-demand)
- **t3.medium**: ~$12/month (1-year reserved)

### DigitalOcean
- **Basic Droplet (2vCPU, 4GB)**: $24/month

### Azure VM
- **B2s (2vCPU, 4GB)**: ~$30/month

### GCP Compute Engine
- **e2-medium (2vCPU, 4GB)**: ~$25/month

**Note**: Add ~$5-10/month for backup storage and bandwidth.

---

## Next Steps After Deployment

1. Test bot in **Observation Mode** first (collect data, no betting)
2. Test in **Dry Run Mode** (simulate betting, no money)
3. Monitor dashboard for 24 hours to ensure stability
4. Review logs and performance metrics
5. Configure initial stake and limits
6. Enable **Live Mode** when confident

---

## Support & Monitoring

### Health Check Endpoints
```bash
# Dashboard health
curl http://localhost:5001/health

# Bot status
curl http://localhost:5001/api/status
```

### Log Locations
- Bot logs: `/opt/aviator-bot/backend/bot_session_*.log`
- Dashboard logs: `/var/log/aviator-dashboard.log`
- System logs: `/var/log/syslog`

### Monitoring Commands
```bash
# Service status
sudo systemctl status aviator-bot aviator-dashboard

# Resource usage
htop
df -h
free -h

# Network connections
sudo netstat -tulpn | grep python
```

---

## Quick Reference Commands

```bash
# Start services
sudo systemctl start aviator-dashboard aviator-bot

# Stop services
sudo systemctl stop aviator-dashboard aviator-bot

# Restart services
sudo systemctl restart aviator-dashboard aviator-bot

# View logs
sudo journalctl -u aviator-bot -f

# Manual start (for testing)
cd /opt/aviator-bot
source venv/bin/activate
python3 run_dashboard.py &
cd backend && python3 bot.py
```

---

## Conclusion

You now have multiple deployment options:
- **Fastest**: Automated Ubuntu script (~10 min)
- **Most Reliable**: Docker deployment (~15 min)
- **Most Control**: Direct Python installation (~20 min)

Choose based on your comfort level and requirements. For production use, **Docker on Ubuntu VM** is recommended for ease of management and updates.

For support, check logs and refer to the troubleshooting section above.
