#!/bin/bash
#
# Aviator Bot - Restore Script
# Restores data from backup archive
#
# Usage:
#   ./restore.sh /path/to/backup_file.tar.gz
#   ./restore.sh --latest
#   ./restore.sh --list
#

# Default configuration
APP_DIR="/opt/aviator-bot"
BACKUP_ROOT="/opt/backups/aviator"

# Color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

# Logging
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
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

# List available backups
list_backups() {
    log "Available backups in $BACKUP_ROOT:"
    echo ""

    if ls "$BACKUP_ROOT"/aviator_backup_*.tar.gz 1> /dev/null 2>&1; then
        local count=1
        for backup in $(ls -t "$BACKUP_ROOT"/aviator_backup_*.tar.gz); do
            local size=$(du -h "$backup" | cut -f1)
            local date=$(stat -c %y "$backup" 2>/dev/null | cut -d' ' -f1,2 | cut -d'.' -f1 || stat -f "%Sm" -t "%Y-%m-%d %H:%M:%S" "$backup" 2>/dev/null)
            echo "  $count. $(basename $backup) - $size - $date"
            count=$((count + 1))
        done
    else
        log_warning "No backups found in $BACKUP_ROOT"
        exit 1
    fi

    echo ""
}

# Get latest backup
get_latest_backup() {
    ls -t "$BACKUP_ROOT"/aviator_backup_*.tar.gz 2>/dev/null | head -1
}

# Inspect backup contents
inspect_backup() {
    local backup_file="$1"

    log "Inspecting backup: $backup_file"
    echo ""

    # Show backup info if exists
    if tar -tzf "$backup_file" | grep -q "backup_info.txt"; then
        log_info "Backup Information:"
        tar -xzOf "$backup_file" "*/backup_info.txt" 2>/dev/null
        echo ""
    fi

    # List contents
    log_info "Backup Contents:"
    tar -tzf "$backup_file" | sed 's|^[^/]*/||' | grep -v '^$' | head -20
    echo ""
}

# Create backup of current state before restore
backup_current_state() {
    log "Creating backup of current state..."

    local timestamp=$(date +%Y%m%d_%H%M%S)
    local pre_restore_backup="$BACKUP_ROOT/pre_restore_backup_$timestamp.tar.gz"

    tar -czf "$pre_restore_backup" \
        -C "$APP_DIR" \
        backend/*.csv \
        backend/aviator_ml_config.json \
        .env \
        2>/dev/null

    if [ -f "$pre_restore_backup" ]; then
        log_success "Current state backed up to: $pre_restore_backup"
    else
        log_warning "Could not create pre-restore backup"
    fi
}

# Restore function
perform_restore() {
    local backup_file="$1"
    local restore_mode="${2:-full}"  # full, data-only, config-only

    log "Starting restore from: $backup_file"

    # Verify backup integrity
    if ! tar -tzf "$backup_file" > /dev/null 2>&1; then
        log_error "Backup file is corrupted or invalid!"
        exit 1
    fi

    log_success "Backup integrity verified"

    # Create temporary extraction directory
    local temp_dir=$(mktemp -d)
    log_info "Extracting to temporary directory..."

    tar -xzf "$backup_file" -C "$temp_dir"

    # Find the extracted directory
    local extracted_dir=$(find "$temp_dir" -maxdepth 1 -type d -name "aviator_backup_*" | head -1)

    if [ -z "$extracted_dir" ]; then
        log_error "Could not find extracted backup directory"
        rm -rf "$temp_dir"
        exit 1
    fi

    # Restore based on mode
    case "$restore_mode" in
        full)
            log_info "Performing full restore..."
            restore_all "$extracted_dir"
            ;;
        data-only)
            log_info "Restoring data files only..."
            restore_data "$extracted_dir"
            ;;
        config-only)
            log_info "Restoring configuration only..."
            restore_config "$extracted_dir"
            ;;
        *)
            log_error "Invalid restore mode: $restore_mode"
            rm -rf "$temp_dir"
            exit 1
            ;;
    esac

    # Cleanup
    rm -rf "$temp_dir"

    log_success "Restore completed!"
}

# Restore all files
restore_all() {
    local source_dir="$1"

    # Restore CSV files
    if [ -d "$source_dir/backend" ]; then
        log_info "Restoring CSV data files..."
        cp -v "$source_dir/backend"/*.csv "$APP_DIR/backend/" 2>/dev/null || log_warning "No CSV files to restore"
    fi

    # Restore configuration
    if [ -f "$source_dir/.env" ]; then
        log_info "Restoring .env configuration..."
        cp -v "$source_dir/.env" "$APP_DIR/"
    fi

    if [ -f "$source_dir/backend/aviator_ml_config.json" ]; then
        log_info "Restoring ML configuration..."
        cp -v "$source_dir/backend/aviator_ml_config.json" "$APP_DIR/backend/"
    fi

    # Restore logs (optional)
    if [ -d "$source_dir/logs" ]; then
        log_info "Restoring log files..."
        mkdir -p "$APP_DIR/restored_logs"
        cp -v "$source_dir/logs"/* "$APP_DIR/restored_logs/" 2>/dev/null
        log_info "Logs restored to: $APP_DIR/restored_logs/"
    fi

    # Fix permissions
    fix_permissions
}

# Restore data files only
restore_data() {
    local source_dir="$1"

    if [ -d "$source_dir/backend" ]; then
        log_info "Restoring CSV data files..."
        cp -v "$source_dir/backend"/*.csv "$APP_DIR/backend/" 2>/dev/null || log_warning "No CSV files to restore"

        fix_permissions
    else
        log_error "No data files found in backup"
        exit 1
    fi
}

# Restore configuration only
restore_config() {
    local source_dir="$1"

    local restored=false

    if [ -f "$source_dir/.env" ]; then
        log_info "Restoring .env configuration..."
        cp -v "$source_dir/.env" "$APP_DIR/"
        restored=true
    fi

    if [ -f "$source_dir/backend/aviator_ml_config.json" ]; then
        log_info "Restoring ML configuration..."
        cp -v "$source_dir/backend/aviator_ml_config.json" "$APP_DIR/backend/"
        restored=true
    fi

    if [ "$restored" = false ]; then
        log_error "No configuration files found in backup"
        exit 1
    fi

    fix_permissions
}

# Fix file permissions
fix_permissions() {
    log_info "Fixing file permissions..."

    if [ -d "$APP_DIR/backend" ]; then
        chown -R aviator:aviator "$APP_DIR/backend" 2>/dev/null || true
        chmod -R 644 "$APP_DIR/backend"/*.csv 2>/dev/null || true
    fi

    if [ -f "$APP_DIR/.env" ]; then
        chown aviator:aviator "$APP_DIR/.env" 2>/dev/null || true
        chmod 600 "$APP_DIR/.env" 2>/dev/null || true
    fi

    log_success "Permissions fixed"
}

# Interactive restore
interactive_restore() {
    echo ""
    log "=== Interactive Restore Mode ==="
    echo ""

    list_backups

    echo "Select a backup to restore:"
    read -p "Enter backup number (or 'q' to quit): " selection

    if [ "$selection" = "q" ]; then
        log "Restore cancelled"
        exit 0
    fi

    # Get the selected backup
    local backup_file=$(ls -t "$BACKUP_ROOT"/aviator_backup_*.tar.gz | sed -n "${selection}p")

    if [ -z "$backup_file" ] || [ ! -f "$backup_file" ]; then
        log_error "Invalid selection"
        exit 1
    fi

    # Inspect backup
    inspect_backup "$backup_file"

    # Confirm restore
    echo ""
    log_warning "This will overwrite current data!"
    read -p "Do you want to create a backup of current state first? (y/n) " -n 1 -r
    echo

    if [[ $REPLY =~ ^[Yy]$ ]]; then
        backup_current_state
    fi

    echo ""
    read -p "Proceed with restore? (yes/no) " -r

    if [ "$REPLY" != "yes" ]; then
        log "Restore cancelled"
        exit 0
    fi

    # Select restore mode
    echo ""
    echo "Restore mode:"
    echo "  1. Full restore (data + configuration)"
    echo "  2. Data only (CSV files)"
    echo "  3. Configuration only (.env, JSON)"
    read -p "Select mode (1-3): " mode_selection

    case "$mode_selection" in
        1)
            perform_restore "$backup_file" "full"
            ;;
        2)
            perform_restore "$backup_file" "data-only"
            ;;
        3)
            perform_restore "$backup_file" "config-only"
            ;;
        *)
            log_error "Invalid mode selection"
            exit 1
            ;;
    esac
}

# Show usage
show_usage() {
    cat << EOF
Aviator Bot - Restore Script

Usage:
  $0 [options] [backup_file]

Options:
  --latest          Restore from latest backup
  --list            List available backups
  --interactive     Interactive restore mode
  --inspect FILE    Inspect backup contents without restoring
  --help            Show this help message

Examples:
  $0 --latest                                  # Restore latest backup
  $0 /path/to/backup.tar.gz                    # Restore specific backup
  $0 --interactive                             # Interactive mode
  $0 --inspect /path/to/backup.tar.gz          # View backup contents

EOF
}

# Main function
main() {
    log "=== Aviator Bot Restore Script ==="

    # Parse arguments
    case "$1" in
        --list)
            list_backups
            exit 0
            ;;
        --latest)
            local latest=$(get_latest_backup)
            if [ -z "$latest" ]; then
                log_error "No backups found"
                exit 1
            fi
            log_info "Using latest backup: $latest"
            inspect_backup "$latest"
            backup_current_state
            perform_restore "$latest" "full"
            ;;
        --interactive)
            interactive_restore
            ;;
        --inspect)
            if [ -z "$2" ]; then
                log_error "Please specify a backup file to inspect"
                show_usage
                exit 1
            fi
            inspect_backup "$2"
            exit 0
            ;;
        --help)
            show_usage
            exit 0
            ;;
        "")
            # No arguments - run interactive mode
            interactive_restore
            ;;
        *)
            # Backup file specified
            if [ ! -f "$1" ]; then
                log_error "Backup file not found: $1"
                exit 1
            fi
            inspect_backup "$1"
            backup_current_state
            perform_restore "$1" "full"
            ;;
    esac

    echo ""
    log_success "Restore operation completed!"
    log_info "You may need to restart services:"
    log_info "  sudo systemctl restart aviator-dashboard"
    log_info "  sudo systemctl restart aviator-bot"
}

# Run main function
main "$@"
