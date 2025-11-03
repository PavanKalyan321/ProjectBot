# VM Deployment - Quick Start Guide

**Deploy Aviator Bot to a VM in 3 simple steps.**

---

## Choose Your Deployment Method

### 1. Fastest - Automated Ubuntu Setup (10 minutes)
**Best for**: Quick production deployment on Ubuntu/Debian VM

```bash
# SSH into your Ubuntu VM
ssh user@your-vm-ip

# Download and run automated setup
cd /tmp
git clone https://github.com/your-repo/aviator-bot.git
cd aviator-bot
sudo chmod +x setup_vm.sh
sudo ./setup_vm.sh

# Configure and start
cd /opt/aviator-bot
cp .env.template .env
nano .env  # Edit BOT_MODE, INITIAL_STAKE, etc.
./start.sh

# Access dashboard
# Open browser: http://your-vm-ip:5001
```

**What this does**:
- Installs all dependencies (Python, Tesseract, OpenCV, etc.)
- Creates systemd services for auto-start
- Sets up virtual display (Xvfb)
- Configures firewall
- Creates helper scripts

---

### 2. Most Reliable - Docker (15 minutes)
**Best for**: Containerized deployment, any cloud provider

```bash
# SSH into your VM (Ubuntu/Debian/Any)
ssh user@your-vm-ip

# Install Docker
curl -fsSL https://get.docker.com | sudo sh

# Clone repository
git clone https://github.com/your-repo/aviator-bot.git
cd aviator-bot

# Setup environment
cp .env.example .env
nano .env  # Configure settings

# Start with Docker Compose
docker-compose up -d

# Check status
docker-compose ps
docker-compose logs -f

# Access dashboard
# Open browser: http://your-vm-ip:5001
```

**Services started**:
- `xvfb` - Virtual display
- `dashboard` - Web UI (port 5001)
- `bot` - Trading bot

**Docker commands**:
```bash
docker-compose up -d       # Start services
docker-compose down        # Stop services
docker-compose restart     # Restart services
docker-compose logs -f     # View logs
```

---

### 3. Most Control - Manual Installation (20 minutes)
**Best for**: Custom setups, advanced users

#### Ubuntu/Debian VM

```bash
# 1. Install dependencies
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3.9 python3-pip python3-venv \
    tesseract-ocr libgl1-mesa-glx libglib2.0-0 \
    xvfb x11vnc fluxbox git

# 2. Clone repository
git clone https://github.com/your-repo/aviator-bot.git /opt/aviator-bot
cd /opt/aviator-bot

# 3. Setup Python environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
nano .env

# 5. Start virtual display
Xvfb :99 -screen 0 1920x1080x24 &
export DISPLAY=:99

# 6. Start services
python3 run_dashboard.py &  # Dashboard in background
cd backend && python3 bot.py  # Bot (interactive)
```

#### Windows Server VM

```powershell
# 1. Install Python 3.9+
# Download from: https://www.python.org/downloads/

# 2. Install Tesseract OCR
# Download from: https://github.com/UB-Mannheim/tesseract/wiki

# 3. Clone repository
git clone https://github.com/your-repo/aviator-bot.git C:\aviator-bot
cd C:\aviator-bot

# 4. Setup Python environment
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt

# 5. Configure environment
Copy-Item .env.example .env
notepad .env

# 6. Start services
Start-Process python -ArgumentList "run_dashboard.py"
cd backend
python bot.py
```

---

## Cloud Provider Quick Guides

### AWS EC2

```bash
# 1. Launch EC2 instance
# - AMI: Ubuntu Server 22.04 LTS
# - Instance Type: t3.medium (2 vCPU, 4GB RAM)
# - Storage: 20GB
# - Security Group: Allow ports 22, 5001, 5900

# 2. Connect
ssh -i your-key.pem ubuntu@ec2-ip-address

# 3. Run automated setup
cd /tmp
git clone https://github.com/your-repo/aviator-bot.git
cd aviator-bot
sudo ./setup_vm.sh

# 4. Access dashboard
# http://ec2-ip-address:5001
```

**Monthly Cost**: ~$30 (t3.medium on-demand), ~$12 (reserved)

### DigitalOcean

```bash
# 1. Create Droplet
# - Image: Ubuntu 22.04 x64
# - Size: Basic - 2 vCPU, 4GB RAM ($24/mo)
# - Add SSH key

# 2. Connect
ssh root@droplet-ip

# 3. Run automated setup
git clone https://github.com/your-repo/aviator-bot.git /opt/aviator-bot
cd /opt/aviator-bot
sudo ./setup_vm.sh

# 4. Access dashboard
# http://droplet-ip:5001
```

**Monthly Cost**: $24

### Google Cloud Platform

```bash
# 1. Create VM instance
# - Machine type: e2-medium (2 vCPU, 4GB)
# - Boot disk: Ubuntu 22.04 LTS, 20GB
# - Firewall: Allow HTTP, HTTPS, custom TCP 5001

# 2. Connect via SSH (browser or gcloud)
gcloud compute ssh instance-name

# 3. Run automated setup
git clone https://github.com/your-repo/aviator-bot.git /opt/aviator-bot
cd /opt/aviator-bot
sudo ./setup_vm.sh

# 4. Access dashboard
# http://external-ip:5001
```

**Monthly Cost**: ~$25

### Azure

```bash
# 1. Create VM
# - Image: Ubuntu Server 22.04 LTS
# - Size: B2s (2 vCPU, 4GB RAM)
# - Networking: Allow ports 22, 5001

# 2. Connect
ssh azureuser@vm-ip

# 3. Run automated setup
git clone https://github.com/your-repo/aviator-bot.git /opt/aviator-bot
cd /opt/aviator-bot
sudo ./setup_vm.sh

# 4. Access dashboard
# http://vm-ip:5001
```

**Monthly Cost**: ~$30

---

## Post-Deployment Checklist

### 1. Verify Services Running
```bash
# Check status
sudo systemctl status xvfb
sudo systemctl status aviator-dashboard
sudo systemctl status aviator-bot

# Or use helper script
cd /opt/aviator-bot
./status.sh
```

### 2. Access Dashboard
Open browser: `http://your-vm-ip:5001`

Should see:
- Live stats
- Model predictions
- Signal indicators
- Recent rounds chart

### 3. Test Bot in Safe Mode
```bash
# Edit .env
nano /opt/aviator-bot/.env

# Set to dry run mode
BOT_MODE=dry_run

# Restart bot
sudo systemctl restart aviator-bot
```

### 4. Monitor Logs
```bash
# Dashboard logs
tail -f /var/log/aviator-dashboard.log

# Bot logs
tail -f /var/log/aviator-bot.log

# Or use helper script
cd /opt/aviator-bot
./logs.sh dashboard
```

### 5. Setup Automated Backups
```bash
# Add to cron
crontab -e

# Backup every 6 hours
0 */6 * * * /opt/aviator-bot/scripts/backup.sh >> /var/log/aviator-backup.log 2>&1
```

### 6. Enable Health Monitoring
```bash
# Add to cron
crontab -e

# Health check every 5 minutes
*/5 * * * * /opt/aviator-bot/scripts/health_check.sh >> /var/log/aviator-health.log 2>&1
```

---

## Configuration Guide

### Essential .env Settings

```bash
# Display (Linux only)
DISPLAY=:99

# OCR Path
TESSERACT_PATH=/usr/bin/tesseract  # Linux
# TESSERACT_PATH=C:\Program Files\Tesseract-OCR\tesseract.exe  # Windows

# Operating Mode
BOT_MODE=dry_run  # Options: observation, dry_run, live

# Betting Parameters
INITIAL_STAKE=25
MAX_STAKE=1000
STAKE_INCREASE_PERCENT=20

# Dashboard
FLASK_PORT=5001
FLASK_HOST=0.0.0.0
```

### Screen Coordinates Configuration

Edit `backend/aviator_ml_config.json`:
```json
{
  "stake_coords": [361, 797],
  "bet_button_coords": [370, 912],
  "cashout_coords": [370, 912],
  "multiplier_region": [294, 513, 362, 53],
  "history_region": [98, 1108, 591, -5]
}
```

---

## Testing the Deployment

### 1. Test Dashboard
```bash
curl http://localhost:5001
# Should return HTML

curl http://localhost:5001/health
# Should return health status
```

### 2. Test Bot Connection
```bash
# Check bot process
ps aux | grep bot.py

# Check bot logs for errors
tail -50 /var/log/aviator-bot.log | grep -i error
```

### 3. Test Virtual Display
```bash
# Check Xvfb is running
ps aux | grep Xvfb

# Test display
DISPLAY=:99 xdpyinfo
```

---

## Accessing Remotely

### SSH Tunnel (Secure)
```bash
# From your local machine
ssh -L 5001:localhost:5001 user@vm-ip

# Then open in browser
# http://localhost:5001
```

### VNC Access (See the screen)
```bash
# On VM, start VNC server
x11vnc -display :99 -forever -nopw &

# From your local machine
vncviewer vm-ip:5900
```

### Direct Access (Open port)
```bash
# Configure firewall
sudo ufw allow 5001/tcp

# Access directly
# http://vm-ip:5001
```

---

## Common Issues & Solutions

### Dashboard won't start
```bash
# Check if port is in use
sudo netstat -tulpn | grep 5001

# Check Python environment
source /opt/aviator-bot/venv/bin/activate
python3 --version

# Check logs
tail -50 /var/log/aviator-dashboard.error.log
```

### Bot crashes immediately
```bash
# Check Tesseract installation
tesseract --version

# Check display
echo $DISPLAY
ps aux | grep Xvfb

# Check screen coordinates
nano /opt/aviator-bot/backend/aviator_ml_config.json
```

### Can't access dashboard from outside
```bash
# Check firewall
sudo ufw status

# Allow port
sudo ufw allow 5001/tcp

# Check Flask is listening on 0.0.0.0
netstat -tulpn | grep 5001
```

### Out of disk space
```bash
# Check space
df -h

# Clean old logs
sudo journalctl --vacuum-time=7d

# Clean old backups
ls -t /opt/backups/aviator/*.tar.gz | tail -n +8 | xargs rm -f
```

---

## Quick Commands Reference

```bash
# Start services
sudo systemctl start xvfb aviator-dashboard aviator-bot
# or: cd /opt/aviator-bot && ./start.sh

# Stop services
sudo systemctl stop aviator-bot aviator-dashboard xvfb
# or: cd /opt/aviator-bot && ./stop.sh

# Check status
sudo systemctl status aviator-dashboard
# or: cd /opt/aviator-bot && ./status.sh

# View logs
tail -f /var/log/aviator-dashboard.log
# or: cd /opt/aviator-bot && ./logs.sh dashboard

# Restart after config change
sudo systemctl restart aviator-dashboard aviator-bot

# Manual bot start (interactive)
cd /opt/aviator-bot/backend
source ../venv/bin/activate
python3 bot.py
```

---

## Next Steps

1. **Test in Observation Mode** (collect data, no betting)
2. **Test in Dry Run Mode** (simulate betting, no money)
3. **Monitor for 24 hours** to ensure stability
4. **Review performance metrics** in dashboard
5. **Configure betting parameters** based on your strategy
6. **Enable Live Mode** only when confident

---

## Production Recommendations

1. Use **observation mode** first to collect data
2. Use **dry run mode** for testing strategies
3. Enable **automated backups** (every 6 hours)
4. Enable **health monitoring** (every 5 minutes)
5. Setup **alert notifications** (email/Telegram)
6. Monitor **resource usage** regularly
7. Keep **system updated**: `sudo apt update && sudo apt upgrade`
8. Review **logs daily**: Check for errors and anomalies
9. Test **restore process** periodically
10. Don't enable **auto-restart** for bot in live mode

---

## Support Resources

- [Full VM Deployment Guide](VM_DEPLOYMENT_GUIDE.md) - Detailed instructions
- [Systemd Services Guide](systemd/README.md) - Service management
- [Monitoring Scripts](scripts/README.md) - Health checks and backups
- [Start Bot Guide](START_BOT_GUIDE.md) - Bot operation details
- [Dashboard Guide](DASHBOARD_README.md) - Dashboard features
- [Monitoring Guide](MONITORING_GUIDE.md) - Advanced monitoring

---

## Cost Summary

| Provider | Instance Type | RAM | vCPU | Monthly Cost |
|----------|---------------|-----|------|--------------|
| AWS EC2 | t3.medium | 4GB | 2 | $30 (on-demand) |
| AWS EC2 | t3.medium | 4GB | 2 | $12 (reserved) |
| DigitalOcean | Basic Droplet | 4GB | 2 | $24 |
| GCP | e2-medium | 4GB | 2 | $25 |
| Azure | B2s | 4GB | 4 | $30 |

Add $5-10/month for backups and bandwidth.

---

## Security Reminder

1. Change default passwords
2. Use SSH keys (disable password auth)
3. Keep system updated
4. Use firewall (only open necessary ports)
5. Enable fail2ban: `sudo apt install fail2ban`
6. Regular backups
7. Use HTTPS (setup SSL with Let's Encrypt)
8. Never commit `.env` to git
9. Use strong passwords for VNC
10. Monitor access logs

---

**You're ready to deploy! Choose your method above and follow the steps.**

For help: Check logs first, then refer to troubleshooting sections in full guides.
