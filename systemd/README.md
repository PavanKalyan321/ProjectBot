# Systemd Service Files

This directory contains systemd service files for running the Aviator Bot as system services on Linux.

## Services Included

1. **xvfb.service** - Virtual display server (required for GUI automation)
2. **aviator-dashboard.service** - Web dashboard (Flask + SocketIO)
3. **aviator-bot.service** - Main bot service (trading automation)

## Installation

### Option 1: Automatic (via setup_vm.sh)

The [setup_vm.sh](../setup_vm.sh) script automatically installs these services.

### Option 2: Manual Installation

```bash
# Copy service files
sudo cp systemd/*.service /etc/systemd/system/

# Reload systemd
sudo systemctl daemon-reload

# Enable services to start on boot
sudo systemctl enable xvfb
sudo systemctl enable aviator-dashboard
# Note: aviator-bot is NOT auto-enabled (requires configuration first)

# Start services
sudo systemctl start xvfb
sudo systemctl start aviator-dashboard
```

## Usage

### Start Services
```bash
sudo systemctl start xvfb
sudo systemctl start aviator-dashboard
sudo systemctl start aviator-bot  # Only after configuration
```

### Stop Services
```bash
sudo systemctl stop aviator-bot
sudo systemctl stop aviator-dashboard
sudo systemctl stop xvfb
```

### Check Status
```bash
sudo systemctl status xvfb
sudo systemctl status aviator-dashboard
sudo systemctl status aviator-bot
```

### View Logs
```bash
# Real-time logs
sudo journalctl -u aviator-dashboard -f
sudo journalctl -u aviator-bot -f

# Log files
tail -f /var/log/aviator-dashboard.log
tail -f /var/log/aviator-bot.log
tail -f /var/log/aviator-bot.error.log
```

### Restart Services
```bash
sudo systemctl restart aviator-dashboard
sudo systemctl restart aviator-bot
```

### Enable/Disable Auto-Start
```bash
# Enable (start on boot)
sudo systemctl enable aviator-dashboard
sudo systemctl enable aviator-bot

# Disable (don't start on boot)
sudo systemctl disable aviator-bot
```

## Service Dependencies

```
xvfb.service
    ↓
aviator-dashboard.service
    ↓
aviator-bot.service
```

- **xvfb** must run first (provides virtual display)
- **dashboard** should start before bot (provides monitoring)
- **bot** depends on both services

## Configuration

Services load environment variables from `/opt/aviator-bot/.env`

Required `.env` variables:
```bash
DISPLAY=:99
BOT_MODE=dry_run  # or observation, live
INITIAL_STAKE=25
MAX_STAKE=1000
```

See [.env.example](../.env.example) for full configuration options.

## Security Notes

1. Services run as user `aviator` (non-root)
2. Limited write access (only `/opt/aviator-bot/backend` and `/var/log`)
3. Protected system directories
4. Memory and CPU limits enforced

## Troubleshooting

### Service won't start
```bash
# Check status and logs
sudo systemctl status aviator-dashboard
sudo journalctl -u aviator-dashboard -n 50

# Check if display is running
ps aux | grep Xvfb
echo $DISPLAY
```

### Display issues
```bash
# Verify Xvfb is running
sudo systemctl status xvfb

# Test display
DISPLAY=:99 xdpyinfo
```

### Permission errors
```bash
# Fix ownership
sudo chown -R aviator:aviator /opt/aviator-bot
sudo chown aviator:aviator /var/log/aviator-*.log

# Fix permissions
chmod -R 755 /opt/aviator-bot
```

### Bot crashes repeatedly
```bash
# Check error logs
tail -n 100 /var/log/aviator-bot.error.log

# Disable auto-restart during debugging
sudo systemctl stop aviator-bot
sudo systemctl disable aviator-bot

# Run manually for debugging
sudo su - aviator
cd /opt/aviator-bot/backend
source ../venv/bin/activate
python3 bot.py
```

## Modifying Services

After editing service files:

```bash
# Reload systemd configuration
sudo systemctl daemon-reload

# Restart the modified service
sudo systemctl restart <service-name>
```

## Uninstalling Services

```bash
# Stop and disable services
sudo systemctl stop aviator-bot aviator-dashboard xvfb
sudo systemctl disable aviator-bot aviator-dashboard xvfb

# Remove service files
sudo rm /etc/systemd/system/aviator-*.service
sudo rm /etc/systemd/system/xvfb.service

# Reload systemd
sudo systemctl daemon-reload
sudo systemctl reset-failed
```

## Production Recommendations

1. **Always test first** in observation or dry_run mode
2. **Monitor logs** regularly: `tail -f /var/log/aviator-*.log`
3. **Set resource limits** in service files (already configured)
4. **Enable log rotation** (see [VM_DEPLOYMENT_GUIDE.md](../VM_DEPLOYMENT_GUIDE.md))
5. **Don't auto-enable bot service** until thoroughly tested
6. **Use separate staging environment** before production
7. **Implement monitoring** and alerting for failures

## Helper Scripts

Use the helper scripts in `/opt/aviator-bot/` for easier management:

```bash
/opt/aviator-bot/start.sh   # Start all services
/opt/aviator-bot/stop.sh    # Stop all services
/opt/aviator-bot/status.sh  # Check status
/opt/aviator-bot/logs.sh    # View logs (dashboard|bot|error)
```

## Additional Resources

- [VM Deployment Guide](../VM_DEPLOYMENT_GUIDE.md) - Full deployment instructions
- [Monitoring Guide](../MONITORING_GUIDE.md) - Health monitoring setup
- [Start Bot Guide](../START_BOT_GUIDE.md) - Bot operation guide
