#!/bin/bash
#
# Aviator Bot - Health Check Script
# Monitors bot and dashboard health, sends alerts if issues detected
#
# Usage:
#   ./health_check.sh [--verbose] [--email your@email.com]
#
# Setup as cron job:
#   */5 * * * * /opt/aviator-bot/scripts/health_check.sh >> /var/log/aviator-health.log 2>&1
#

# Configuration
DASHBOARD_URL="http://localhost:5001"
ALERT_EMAIL="${ALERT_EMAIL:-}"
TELEGRAM_BOT_TOKEN="${TELEGRAM_BOT_TOKEN:-}"
TELEGRAM_CHAT_ID="${TELEGRAM_CHAT_ID:-}"
VERBOSE=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --verbose)
            VERBOSE=true
            shift
            ;;
        --email)
            ALERT_EMAIL="$2"
            shift 2
            ;;
        *)
            shift
            ;;
    esac
done

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Logging
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

log_verbose() {
    if [ "$VERBOSE" = true ]; then
        log "$1"
    fi
}

log_error() {
    log "${RED}[ERROR]${NC} $1"
}

log_success() {
    log "${GREEN}[OK]${NC} $1"
}

log_warning() {
    log "${YELLOW}[WARNING]${NC} $1"
}

# Alert functions
send_email_alert() {
    local subject="$1"
    local message="$2"

    if [ -n "$ALERT_EMAIL" ] && command -v mail &> /dev/null; then
        echo "$message" | mail -s "$subject" "$ALERT_EMAIL"
        log_verbose "Email alert sent to $ALERT_EMAIL"
    fi
}

send_telegram_alert() {
    local message="$1"

    if [ -n "$TELEGRAM_BOT_TOKEN" ] && [ -n "$TELEGRAM_CHAT_ID" ]; then
        curl -s -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
            -d chat_id="${TELEGRAM_CHAT_ID}" \
            -d text="${message}" \
            -d parse_mode="HTML" > /dev/null
        log_verbose "Telegram alert sent"
    fi
}

send_alert() {
    local subject="$1"
    local message="$2"

    send_email_alert "$subject" "$message"
    send_telegram_alert "$message"
}

# Health checks
check_xvfb() {
    log_verbose "Checking Xvfb..."

    if pgrep -x Xvfb > /dev/null; then
        log_success "Xvfb is running"
        return 0
    else
        log_error "Xvfb is not running"
        return 1
    fi
}

check_dashboard() {
    log_verbose "Checking dashboard..."

    # Check if process is running
    if ! pgrep -f "run_dashboard.py" > /dev/null; then
        log_error "Dashboard process not found"
        return 1
    fi

    # Check if dashboard responds to HTTP
    if curl -s -f -m 5 "$DASHBOARD_URL" > /dev/null 2>&1; then
        log_success "Dashboard is responding"
        return 0
    else
        log_error "Dashboard is not responding at $DASHBOARD_URL"
        return 1
    fi
}

check_bot() {
    log_verbose "Checking bot..."

    if pgrep -f "backend/bot.py" > /dev/null; then
        log_success "Bot process is running"
        return 0
    else
        log_warning "Bot process not found (may be intentionally stopped)"
        return 1
    fi
}

check_disk_space() {
    log_verbose "Checking disk space..."

    local usage=$(df -h /opt/aviator-bot | awk 'NR==2 {print $5}' | sed 's/%//')

    if [ "$usage" -gt 90 ]; then
        log_error "Disk space critical: ${usage}% used"
        return 1
    elif [ "$usage" -gt 80 ]; then
        log_warning "Disk space low: ${usage}% used"
        return 0
    else
        log_success "Disk space OK: ${usage}% used"
        return 0
    fi
}

check_memory() {
    log_verbose "Checking memory..."

    local mem_usage=$(free | awk 'NR==2 {printf "%.0f", $3/$2 * 100}')

    if [ "$mem_usage" -gt 90 ]; then
        log_error "Memory usage critical: ${mem_usage}%"
        return 1
    elif [ "$mem_usage" -gt 80 ]; then
        log_warning "Memory usage high: ${mem_usage}%"
        return 0
    else
        log_success "Memory usage OK: ${mem_usage}%"
        return 0
    fi
}

check_log_files() {
    log_verbose "Checking log files..."

    local log_dir="/var/log"
    local backend_dir="/opt/aviator-bot/backend"
    local issues=0

    # Check if logs are being written
    local dashboard_log="$log_dir/aviator-dashboard.log"
    if [ -f "$dashboard_log" ]; then
        local last_modified=$(stat -c %Y "$dashboard_log" 2>/dev/null || stat -f %m "$dashboard_log" 2>/dev/null)
        local current_time=$(date +%s)
        local diff=$((current_time - last_modified))

        if [ "$diff" -gt 600 ]; then
            log_warning "Dashboard log not updated in $(($diff / 60)) minutes"
            issues=$((issues + 1))
        else
            log_success "Dashboard log is being written"
        fi
    fi

    # Check error logs for recent errors
    local error_log="$log_dir/aviator-bot.error.log"
    if [ -f "$error_log" ]; then
        local recent_errors=$(tail -100 "$error_log" 2>/dev/null | grep -i "error\|exception\|critical" | wc -l)
        if [ "$recent_errors" -gt 10 ]; then
            log_warning "Found $recent_errors recent errors in bot error log"
            issues=$((issues + 1))
        fi
    fi

    if [ "$issues" -eq 0 ]; then
        log_success "Log files are healthy"
        return 0
    else
        return 1
    fi
}

check_csv_files() {
    log_verbose "Checking CSV data files..."

    local backend_dir="/opt/aviator-bot/backend"
    local issues=0

    # Check if CSV files exist and are not empty
    for csv_file in "aviator_rounds_history.csv" "bet_history.csv" "bot_automl_performance.csv"; do
        local file_path="$backend_dir/$csv_file"

        if [ ! -f "$file_path" ]; then
            log_warning "CSV file not found: $csv_file"
            issues=$((issues + 1))
        elif [ ! -s "$file_path" ]; then
            log_warning "CSV file is empty: $csv_file"
            issues=$((issues + 1))
        else
            log_verbose "CSV file OK: $csv_file"
        fi
    done

    if [ "$issues" -eq 0 ]; then
        log_success "CSV files are healthy"
        return 0
    else
        return 1
    fi
}

check_systemd_services() {
    log_verbose "Checking systemd services..."

    local services=("xvfb" "aviator-dashboard")
    local failed=0

    for service in "${services[@]}"; do
        if systemctl is-active --quiet "$service"; then
            log_success "Service $service is active"
        else
            log_error "Service $service is not active"
            failed=$((failed + 1))
        fi
    done

    # Bot service check (warning only, not error)
    if systemctl is-active --quiet "aviator-bot"; then
        log_success "Service aviator-bot is active"
    else
        log_verbose "Service aviator-bot is not active (may be intentional)"
    fi

    return $failed
}

generate_health_report() {
    local status="$1"
    local message="$2"

    cat << EOF
Aviator Bot Health Check Report
================================
Time: $(date)
Status: $status

$message

System Information:
-------------------
$(uptime)
$(free -h | grep Mem)
$(df -h /opt/aviator-bot | grep -v Filesystem)

Services Status:
----------------
Xvfb: $(systemctl is-active xvfb 2>/dev/null || echo "not installed")
Dashboard: $(systemctl is-active aviator-dashboard 2>/dev/null || echo "not installed")
Bot: $(systemctl is-active aviator-bot 2>/dev/null || echo "not installed")

Recent Log Entries:
-------------------
$(tail -5 /var/log/aviator-dashboard.log 2>/dev/null || echo "No logs available")
EOF
}

# Main health check
main() {
    log "=== Aviator Bot Health Check ==="

    local total_checks=0
    local failed_checks=0
    local warnings=0

    # Run all checks
    checks=(
        "check_xvfb"
        "check_dashboard"
        "check_bot"
        "check_disk_space"
        "check_memory"
        "check_log_files"
        "check_csv_files"
        "check_systemd_services"
    )

    for check in "${checks[@]}"; do
        total_checks=$((total_checks + 1))
        if ! $check; then
            failed_checks=$((failed_checks + 1))
        fi
    done

    # Summary
    echo ""
    log "=== Health Check Summary ==="
    log "Total checks: $total_checks"
    log "Failed: $failed_checks"
    log "Passed: $((total_checks - failed_checks))"

    # Send alert if critical failures
    if [ "$failed_checks" -gt 3 ]; then
        local status="CRITICAL"
        local message="Aviator Bot health check FAILED. $failed_checks/$total_checks checks failed."
        log_error "$message"

        send_alert "Aviator Bot CRITICAL Alert" "$(generate_health_report "$status" "$message")"

        return 1
    elif [ "$failed_checks" -gt 0 ]; then
        local status="WARNING"
        local message="Aviator Bot has minor issues. $failed_checks/$total_checks checks failed."
        log_warning "$message"

        if [ "$failed_checks" -gt 1 ]; then
            send_alert "Aviator Bot Warning" "$(generate_health_report "$status" "$message")"
        fi

        return 0
    else
        log_success "All health checks passed!"
        return 0
    fi
}

# Run main function
main
exit $?
