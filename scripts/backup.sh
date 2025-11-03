#!/bin/bash
#
# Aviator Bot - Backup Script
# Backs up CSV data files, configuration, and logs
#
# Usage:
#   ./backup.sh [--destination /path/to/backup] [--keep 7]
#
# Setup as cron job:
#   0 */6 * * * /opt/aviator-bot/scripts/backup.sh >> /var/log/aviator-backup.log 2>&1
#

# Default configuration
APP_DIR="/opt/aviator-bot"
BACKUP_ROOT="/opt/backups/aviator"
KEEP_BACKUPS=7
BACKUP_DEST=""

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --destination)
            BACKUP_DEST="$2"
            shift 2
            ;;
        --keep)
            KEEP_BACKUPS="$2"
            shift 2
            ;;
        *)
            shift
            ;;
    esac
done

# Set backup destination
if [ -z "$BACKUP_DEST" ]; then
    BACKUP_DEST="$BACKUP_ROOT"
fi

# Color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Logging
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Create backup directory
create_backup_dir() {
    if [ ! -d "$BACKUP_DEST" ]; then
        log "Creating backup directory: $BACKUP_DEST"
        mkdir -p "$BACKUP_DEST"
    fi
}

# Backup function
perform_backup() {
    local timestamp=$(date +%Y%m%d_%H%M%S)
    local backup_file="$BACKUP_DEST/aviator_backup_$timestamp.tar.gz"

    log "Starting backup..."
    log "Backup destination: $backup_file"

    # Create temporary staging directory
    local temp_dir=$(mktemp -d)
    local staging_dir="$temp_dir/aviator_backup_$timestamp"
    mkdir -p "$staging_dir"

    # Copy CSV data files
    log "Backing up CSV data files..."
    if [ -d "$APP_DIR/backend" ]; then
        mkdir -p "$staging_dir/backend"
        cp "$APP_DIR/backend"/*.csv "$staging_dir/backend/" 2>/dev/null || log_warning "No CSV files found"
    fi

    # Copy configuration files
    log "Backing up configuration files..."
    cp "$APP_DIR/.env" "$staging_dir/" 2>/dev/null || log_warning ".env not found"
    cp "$APP_DIR/backend/aviator_ml_config.json" "$staging_dir/backend/" 2>/dev/null || log_warning "Config JSON not found"

    # Copy log files (last 1000 lines only to save space)
    log "Backing up recent logs..."
    mkdir -p "$staging_dir/logs"
    for log_file in /var/log/aviator-*.log; do
        if [ -f "$log_file" ]; then
            tail -1000 "$log_file" > "$staging_dir/logs/$(basename $log_file)"
        fi
    done

    # Copy bot session logs (last 3 sessions)
    if ls "$APP_DIR/backend"/bot_session_*.log 1> /dev/null 2>&1; then
        ls -t "$APP_DIR/backend"/bot_session_*.log | head -3 | xargs -I {} cp {} "$staging_dir/logs/"
    fi

    # Create backup metadata
    cat > "$staging_dir/backup_info.txt" << EOF
Aviator Bot Backup
==================
Timestamp: $(date)
Hostname: $(hostname)
Backup Script Version: 1.0

Files Included:
---------------
$(find "$staging_dir" -type f | sed "s|$staging_dir/||")

System Info:
------------
$(uname -a)
$(df -h "$APP_DIR" | grep -v Filesystem)
$(free -h | grep Mem)
EOF

    # Create compressed archive
    log "Creating compressed archive..."
    tar -czf "$backup_file" -C "$temp_dir" "aviator_backup_$timestamp" 2>/dev/null

    # Check if backup was successful
    if [ -f "$backup_file" ]; then
        local backup_size=$(du -h "$backup_file" | cut -f1)
        log_success "Backup created successfully: $backup_file ($backup_size)"

        # Cleanup temp directory
        rm -rf "$temp_dir"

        return 0
    else
        log_error "Backup failed!"
        rm -rf "$temp_dir"
        return 1
    fi
}

# Cleanup old backups
cleanup_old_backups() {
    log "Cleaning up old backups (keeping last $KEEP_BACKUPS)..."

    local backup_count=$(ls -1 "$BACKUP_DEST"/aviator_backup_*.tar.gz 2>/dev/null | wc -l)

    if [ "$backup_count" -gt "$KEEP_BACKUPS" ]; then
        local to_delete=$((backup_count - KEEP_BACKUPS))
        log "Deleting $to_delete old backup(s)..."

        ls -t "$BACKUP_DEST"/aviator_backup_*.tar.gz | tail -n +$((KEEP_BACKUPS + 1)) | xargs rm -f

        log_success "Old backups cleaned up"
    else
        log "No old backups to clean up (current count: $backup_count)"
    fi
}

# List existing backups
list_backups() {
    log "Existing backups:"
    echo ""

    if ls "$BACKUP_DEST"/aviator_backup_*.tar.gz 1> /dev/null 2>&1; then
        ls -lh "$BACKUP_DEST"/aviator_backup_*.tar.gz | awk '{print $9, "("$5")", $6, $7, $8}'
    else
        log_warning "No backups found in $BACKUP_DEST"
    fi

    echo ""
}

# Verify backup integrity
verify_backup() {
    local backup_file="$1"

    log "Verifying backup integrity: $backup_file"

    if tar -tzf "$backup_file" > /dev/null 2>&1; then
        log_success "Backup integrity verified"
        return 0
    else
        log_error "Backup integrity check failed!"
        return 1
    fi
}

# Calculate total backup size
calculate_backup_size() {
    local total_size=$(du -sh "$BACKUP_DEST" 2>/dev/null | cut -f1)
    log "Total backup storage used: $total_size"
}

# Main function
main() {
    log "=== Aviator Bot Backup Script ==="

    # Check if app directory exists
    if [ ! -d "$APP_DIR" ]; then
        log_error "Application directory not found: $APP_DIR"
        exit 1
    fi

    # Create backup directory
    create_backup_dir

    # Perform backup
    if perform_backup; then
        # Get the latest backup file
        latest_backup=$(ls -t "$BACKUP_DEST"/aviator_backup_*.tar.gz | head -1)

        # Verify backup
        verify_backup "$latest_backup"

        # Cleanup old backups
        cleanup_old_backups

        # Show summary
        echo ""
        log "=== Backup Summary ==="
        list_backups
        calculate_backup_size

        log_success "Backup completed successfully!"
        exit 0
    else
        log_error "Backup failed!"
        exit 1
    fi
}

# Run main function
main
