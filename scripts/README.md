# Aviator Bot - Utility Scripts

Collection of maintenance and monitoring scripts for the Aviator Bot.

## Scripts Overview

| Script | Purpose | Cron-able |
|--------|---------|-----------|
| [health_check.sh](#health_checksh) | Monitor system health and send alerts | Yes |
| [backup.sh](#backupsh) | Backup data and configuration | Yes |
| [restore.sh](#restoresh) | Restore from backup | No |

---

## health_check.sh

Monitors the health of Aviator Bot services and system resources.

### Features
- Checks Xvfb, dashboard, and bot processes
- Monitors disk space and memory usage
- Validates log files and CSV data
- Sends email/Telegram alerts on failures
- Generates detailed health reports

### Usage

```bash
# Basic health check
./health_check.sh

# Verbose output
./health_check.sh --verbose

# With email alerts
./health_check.sh --email your@email.com

# Both
./health_check.sh --verbose --email admin@example.com
```

### Setup Alerts

#### Email Alerts
```bash
# Install mail utility
sudo apt install mailutils

# Set email in environment or script
export ALERT_EMAIL="your@email.com"
```

#### Telegram Alerts
```bash
# Set Telegram credentials
export TELEGRAM_BOT_TOKEN="your_bot_token"
export TELEGRAM_CHAT_ID="your_chat_id"
```

### Automated Monitoring (Cron)

```bash
# Edit crontab
crontab -e

# Add health check every 5 minutes
*/5 * * * * /opt/aviator-bot/scripts/health_check.sh >> /var/log/aviator-health.log 2>&1

# With email alerts every 15 minutes
*/15 * * * * ALERT_EMAIL=admin@example.com /opt/aviator-bot/scripts/health_check.sh >> /var/log/aviator-health.log 2>&1
```

### Health Checks Performed

1. **Xvfb Process** - Virtual display server status
2. **Dashboard Service** - Web UI availability and HTTP response
3. **Bot Process** - Main bot process status
4. **Disk Space** - Storage usage (alerts at 80%, critical at 90%)
5. **Memory Usage** - RAM usage (alerts at 80%, critical at 90%)
6. **Log Files** - Log writing activity and error frequency
7. **CSV Files** - Data file existence and validity
8. **Systemd Services** - Service status and health

### Exit Codes

- `0` - All checks passed
- `1` - Critical failures detected (3+ failures)

---

## backup.sh

Creates compressed backups of bot data, configuration, and logs.

### Features
- Backs up CSV data files
- Includes configuration (.env, JSON)
- Saves recent log entries
- Automatic rotation (keeps last N backups)
- Integrity verification
- Size optimization

### Usage

```bash
# Basic backup (default location)
./backup.sh

# Custom destination
./backup.sh --destination /mnt/external/backups

# Keep last 14 backups instead of 7
./backup.sh --keep 14

# Combined options
./backup.sh --destination /backup --keep 30
```

### What Gets Backed Up

```
aviator_backup_YYYYMMDD_HHMMSS.tar.gz
├── backend/
│   ├── aviator_rounds_history.csv
│   ├── bet_history.csv
│   ├── bot_automl_performance.csv
│   └── aviator_ml_config.json
├── logs/
│   ├── aviator-dashboard.log (last 1000 lines)
│   ├── aviator-bot.log (last 1000 lines)
│   └── bot_session_*.log (last 3 sessions)
├── .env
└── backup_info.txt (metadata)
```

### Automated Backups (Cron)

```bash
# Edit crontab
crontab -e

# Backup every 6 hours
0 */6 * * * /opt/aviator-bot/scripts/backup.sh >> /var/log/aviator-backup.log 2>&1

# Daily backup at 2 AM
0 2 * * * /opt/aviator-bot/scripts/backup.sh --keep 30 >> /var/log/aviator-backup.log 2>&1

# Backup to external storage every 12 hours
0 */12 * * * /opt/aviator-bot/scripts/backup.sh --destination /mnt/nas/backups --keep 60 >> /var/log/aviator-backup.log 2>&1
```

### Default Backup Location

```
/opt/backups/aviator/
├── aviator_backup_20251103_020000.tar.gz
├── aviator_backup_20251103_080000.tar.gz
├── aviator_backup_20251103_140000.tar.gz
└── ...
```

### Backup Rotation

- Automatically keeps last N backups (default: 7)
- Older backups are deleted automatically
- Configurable with `--keep` parameter

### Exit Codes

- `0` - Backup successful
- `1` - Backup failed

---

## restore.sh

Restores data from backup archives with multiple modes and safety features.

### Features
- Interactive and command-line modes
- Three restore modes (full, data-only, config-only)
- Pre-restore backup of current state
- Backup inspection before restore
- Integrity verification
- Permission fixing

### Usage

#### Interactive Mode (Recommended)
```bash
# Start interactive restore
./restore.sh
# or
./restore.sh --interactive
```

#### Command-Line Mode
```bash
# Restore latest backup
./restore.sh --latest

# Restore specific backup
./restore.sh /opt/backups/aviator/aviator_backup_20251103_120000.tar.gz

# List available backups
./restore.sh --list

# Inspect backup without restoring
./restore.sh --inspect /path/to/backup.tar.gz
```

### Restore Modes

1. **Full Restore**
   - CSV data files
   - Configuration (.env, JSON)
   - Log files (to `restored_logs/`)

2. **Data Only**
   - CSV data files only
   - Preserves current configuration

3. **Configuration Only**
   - .env file
   - aviator_ml_config.json
   - Preserves current data

### Safety Features

#### Pre-Restore Backup
Before any restore, the script offers to backup your current state:
```
pre_restore_backup_YYYYMMDD_HHMMSS.tar.gz
```

#### Confirmation Prompts
- Confirms backup selection
- Asks for pre-restore backup
- Requires typing "yes" to proceed

#### Inspection
Shows backup contents and metadata before restoring.

### Examples

#### Restore After Data Corruption
```bash
# List available backups
./restore.sh --list

# Inspect a recent backup
./restore.sh --inspect /opt/backups/aviator/aviator_backup_20251103_120000.tar.gz

# Restore it
./restore.sh /opt/backups/aviator/aviator_backup_20251103_120000.tar.gz
```

#### Quick Restore Latest
```bash
./restore.sh --latest
```

#### Restore Only Data Files
```bash
# Use interactive mode and select option 2
./restore.sh --interactive
```

### After Restore

Restart services to apply changes:
```bash
sudo systemctl restart aviator-dashboard
sudo systemctl restart aviator-bot
```

### Exit Codes

- `0` - Restore successful
- `1` - Restore failed or cancelled

---

## Installation

### Setup Scripts

```bash
# Copy scripts to application directory
sudo cp scripts/*.sh /opt/aviator-bot/scripts/

# Make executable
sudo chmod +x /opt/aviator-bot/scripts/*.sh

# Set ownership
sudo chown -R aviator:aviator /opt/aviator-bot/scripts/
```

### Create Log Files

```bash
sudo touch /var/log/aviator-health.log
sudo touch /var/log/aviator-backup.log
sudo chown aviator:aviator /var/log/aviator-*.log
```

---

## Recommended Cron Schedule

```bash
# Edit crontab
crontab -e

# Health check every 5 minutes
*/5 * * * * /opt/aviator-bot/scripts/health_check.sh >> /var/log/aviator-health.log 2>&1

# Backup every 6 hours
0 */6 * * * /opt/aviator-bot/scripts/backup.sh >> /var/log/aviator-backup.log 2>&1

# Weekly cleanup (optional)
0 3 * * 0 /opt/aviator-bot/cleanup_data.py >> /var/log/aviator-cleanup.log 2>&1
```

---

## Monitoring Dashboard Access

### View Real-Time Logs
```bash
# All scripts log to separate files
tail -f /var/log/aviator-health.log
tail -f /var/log/aviator-backup.log
```

### Check Cron Job Status
```bash
# View cron log
sudo grep CRON /var/log/syslog | tail -20

# Test cron job manually
/opt/aviator-bot/scripts/health_check.sh --verbose
```

### Storage Monitoring
```bash
# Check backup storage usage
du -sh /opt/backups/aviator/

# List all backups with sizes
ls -lh /opt/backups/aviator/
```

---

## Troubleshooting

### Script Won't Execute

```bash
# Check permissions
ls -l /opt/aviator-bot/scripts/*.sh

# Make executable
chmod +x /opt/aviator-bot/scripts/*.sh

# Check ownership
sudo chown aviator:aviator /opt/aviator-bot/scripts/*.sh
```

### Cron Job Not Running

```bash
# Verify cron service
sudo systemctl status cron

# Check cron logs
grep CRON /var/log/syslog

# Test script manually
/opt/aviator-bot/scripts/health_check.sh --verbose
```

### Email Alerts Not Working

```bash
# Install mail utility
sudo apt install mailutils

# Test email
echo "Test" | mail -s "Test Subject" your@email.com

# Check mail logs
tail -f /var/log/mail.log
```

### Telegram Alerts Not Working

```bash
# Verify credentials
echo $TELEGRAM_BOT_TOKEN
echo $TELEGRAM_CHAT_ID

# Test curl
curl -s "https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/getMe"

# Test message
curl -s -X POST "https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/sendMessage" \
  -d chat_id="$TELEGRAM_CHAT_ID" \
  -d text="Test message"
```

### Backup Fails

```bash
# Check disk space
df -h /opt/backups/

# Check permissions
ls -ld /opt/backups/aviator/

# Create backup directory
sudo mkdir -p /opt/backups/aviator
sudo chown aviator:aviator /opt/backups/aviator

# Test backup manually
./backup.sh --verbose
```

### Restore Fails

```bash
# Verify backup integrity
tar -tzf /path/to/backup.tar.gz

# Check permissions on restore destination
ls -ld /opt/aviator-bot/backend

# Test extraction
tar -xzf /path/to/backup.tar.gz -C /tmp
ls -R /tmp/aviator_backup_*
```

---

## Advanced Usage

### Remote Backups

#### Backup to Remote Server (SCP)
```bash
# After local backup, copy to remote
scp /opt/backups/aviator/aviator_backup_*.tar.gz user@remote:/backups/

# Add to cron
0 3 * * * /opt/aviator-bot/scripts/backup.sh && scp /opt/backups/aviator/$(ls -t /opt/backups/aviator/ | head -1) user@remote:/backups/
```

#### Backup to S3
```bash
# Install AWS CLI
sudo apt install awscli

# Configure credentials
aws configure

# Upload after backup
aws s3 cp /opt/backups/aviator/ s3://your-bucket/aviator/ --recursive

# Add to cron
0 3 * * * /opt/aviator-bot/scripts/backup.sh && aws s3 sync /opt/backups/aviator/ s3://your-bucket/aviator/
```

### Custom Health Checks

Extend [health_check.sh](health_check.sh) with custom checks:

```bash
# Add custom check function
check_custom_metric() {
    log_verbose "Checking custom metric..."

    # Your custom check logic here
    if [ condition ]; then
        log_success "Custom check passed"
        return 0
    else
        log_error "Custom check failed"
        return 1
    fi
}

# Add to checks array in main()
checks=(
    "check_xvfb"
    "check_dashboard"
    "check_bot"
    "check_custom_metric"  # Add your custom check
)
```

### Notification Integrations

#### Slack Webhook
```bash
# Add to health_check.sh or backup.sh
send_slack_alert() {
    local message="$1"
    curl -X POST -H 'Content-type: application/json' \
        --data "{\"text\":\"$message\"}" \
        $SLACK_WEBHOOK_URL
}
```

#### Discord Webhook
```bash
send_discord_alert() {
    local message="$1"
    curl -X POST -H 'Content-type: application/json' \
        --data "{\"content\":\"$message\"}" \
        $DISCORD_WEBHOOK_URL
}
```

---

## Best Practices

1. **Regular Health Checks**: Run every 5-15 minutes
2. **Frequent Backups**: Every 4-6 hours minimum
3. **Backup Retention**: Keep at least 7-14 backups
4. **Test Restores**: Periodically test restore process
5. **Monitor Alerts**: Setup email/Telegram notifications
6. **Off-Site Backups**: Copy backups to remote location
7. **Log Monitoring**: Review health/backup logs regularly
8. **Resource Limits**: Monitor disk space in backup location

---

## Security Considerations

1. **File Permissions**: Scripts run as `aviator` user (non-root)
2. **Backup Security**: Backups may contain sensitive data (.env)
3. **Credential Storage**: Use environment variables, not hardcoded
4. **Log Sanitization**: Ensure logs don't contain secrets
5. **Access Control**: Restrict access to backup files (chmod 600)

---

## Performance Impact

- **Health Checks**: Minimal (<1% CPU, <10MB RAM)
- **Backups**: Low impact (uses tar compression)
- **Restore**: Brief service interruption if running

---

## Support

For issues with scripts:
1. Check script logs: `/var/log/aviator-*.log`
2. Run with `--verbose` flag for debugging
3. Verify permissions and ownership
4. Ensure required utilities installed (tar, curl, mail, etc.)

Refer to main documentation:
- [VM Deployment Guide](../VM_DEPLOYMENT_GUIDE.md)
- [Monitoring Guide](../MONITORING_GUIDE.md)
- [Start Bot Guide](../START_BOT_GUIDE.md)
