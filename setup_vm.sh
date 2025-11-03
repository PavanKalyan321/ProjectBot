#!/bin/bash
#
# Aviator Bot - Automated VM Setup Script
# Supports: Ubuntu 20.04+ / Debian 11+
#
# Usage:
#   wget https://raw.githubusercontent.com/your-repo/setup_vm.sh
#   chmod +x setup_vm.sh
#   sudo ./setup_vm.sh
#

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
APP_DIR="/opt/aviator-bot"
APP_USER="aviator"
VENV_DIR="$APP_DIR/venv"
REPO_URL="https://github.com/your-repo/aviator-bot.git"

# Functions
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

check_root() {
    if [ "$EUID" -ne 0 ]; then
        log_error "Please run as root (use sudo)"
        exit 1
    fi
}

print_banner() {
    echo ""
    echo -e "${GREEN}╔════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║     Aviator Bot - VM Setup Script         ║${NC}"
    echo -e "${GREEN}║     Automated Installation for Linux      ║${NC}"
    echo -e "${GREEN}╚════════════════════════════════════════════╝${NC}"
    echo ""
}

detect_os() {
    log_info "Detecting operating system..."

    if [ -f /etc/os-release ]; then
        . /etc/os-release
        OS=$ID
        VERSION=$VERSION_ID
        log_success "Detected: $PRETTY_NAME"
    else
        log_error "Cannot detect OS. /etc/os-release not found."
        exit 1
    fi

    # Check if supported
    if [[ "$OS" != "ubuntu" && "$OS" != "debian" ]]; then
        log_warning "Untested OS. Script designed for Ubuntu/Debian."
        read -p "Continue anyway? (y/n) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
}

update_system() {
    log_info "Updating system packages..."
    apt-get update -qq
    apt-get upgrade -y -qq
    log_success "System updated"
}

install_dependencies() {
    log_info "Installing system dependencies..."

    # Core dependencies
    apt-get install -y -qq \
        python3.9 \
        python3-pip \
        python3-venv \
        python3-dev \
        git \
        curl \
        wget \
        build-essential \
        software-properties-common

    log_success "Core dependencies installed"

    # Tesseract OCR
    log_info "Installing Tesseract OCR..."
    apt-get install -y -qq \
        tesseract-ocr \
        libtesseract-dev

    log_success "Tesseract OCR installed"

    # OpenCV and image processing dependencies
    log_info "Installing OpenCV dependencies..."
    apt-get install -y -qq \
        libgl1-mesa-glx \
        libglib2.0-0 \
        libsm6 \
        libxext6 \
        libxrender-dev \
        libgomp1 \
        libopencv-dev \
        python3-opencv

    log_success "OpenCV dependencies installed"

    # GUI automation dependencies
    log_info "Installing GUI automation tools..."
    apt-get install -y -qq \
        xvfb \
        x11-utils \
        xdotool \
        scrot \
        fluxbox \
        x11vnc

    log_success "GUI automation tools installed"
}

create_app_user() {
    log_info "Creating application user: $APP_USER"

    if id "$APP_USER" &>/dev/null; then
        log_warning "User $APP_USER already exists"
    else
        useradd -m -s /bin/bash "$APP_USER"
        log_success "User $APP_USER created"
    fi
}

setup_application() {
    log_info "Setting up application directory..."

    # Create app directory
    mkdir -p "$APP_DIR"
    cd "$APP_DIR"

    # Check if this script is being run from the repo
    if [ -d "/tmp/aviator-bot" ] || [ -f "../backend/bot.py" ]; then
        log_info "Copying local files..."
        if [ -d "/tmp/aviator-bot" ]; then
            cp -r /tmp/aviator-bot/* "$APP_DIR/"
        else
            cp -r ../* "$APP_DIR/" 2>/dev/null || true
        fi
    else
        log_info "Cloning repository..."
        log_warning "Using placeholder repo URL. Update REPO_URL in script!"
        # For now, we'll skip cloning since repo might not be public
        log_info "Skipping git clone. Files should be copied manually."
    fi

    # Set permissions
    chown -R "$APP_USER:$APP_USER" "$APP_DIR"
    log_success "Application directory setup complete"
}

setup_python_environment() {
    log_info "Setting up Python virtual environment..."

    # Create virtual environment as app user
    su - "$APP_USER" -c "cd $APP_DIR && python3 -m venv $VENV_DIR"

    # Upgrade pip
    su - "$APP_USER" -c "$VENV_DIR/bin/pip install --upgrade pip setuptools wheel"

    log_success "Python virtual environment created"
}

install_python_packages() {
    log_info "Installing Python packages..."

    if [ -f "$APP_DIR/requirements.txt" ]; then
        su - "$APP_USER" -c "$VENV_DIR/bin/pip install -r $APP_DIR/requirements.txt"
        log_success "Python packages installed"
    else
        log_warning "requirements.txt not found. Skipping Python package installation."
        log_info "You'll need to install packages manually later."
    fi
}

setup_virtual_display() {
    log_info "Configuring virtual display (Xvfb)..."

    # Create Xvfb service
    cat > /etc/systemd/system/xvfb.service << 'EOF'
[Unit]
Description=X Virtual Frame Buffer Service
After=network.target

[Service]
Type=simple
User=aviator
ExecStart=/usr/bin/Xvfb :99 -screen 0 1920x1080x24 -ac +extension GLX +render -noreset
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

    systemctl daemon-reload
    systemctl enable xvfb
    systemctl start xvfb

    log_success "Virtual display configured"
}

setup_systemd_services() {
    log_info "Creating systemd services..."

    # Dashboard service
    cat > /etc/systemd/system/aviator-dashboard.service << EOF
[Unit]
Description=Aviator Bot Dashboard
After=network.target xvfb.service
Wants=xvfb.service

[Service]
Type=simple
User=$APP_USER
WorkingDirectory=$APP_DIR
Environment="DISPLAY=:99"
Environment="PATH=$VENV_DIR/bin:/usr/local/bin:/usr/bin:/bin"
ExecStart=$VENV_DIR/bin/python3 $APP_DIR/run_dashboard.py
Restart=always
RestartSec=10
StandardOutput=append:/var/log/aviator-dashboard.log
StandardError=append:/var/log/aviator-dashboard.error.log

[Install]
WantedBy=multi-user.target
EOF

    # Bot service (disabled by default - requires configuration)
    cat > /etc/systemd/system/aviator-bot.service << EOF
[Unit]
Description=Aviator Bot Service
After=network.target aviator-dashboard.service xvfb.service
Wants=xvfb.service aviator-dashboard.service

[Service]
Type=simple
User=$APP_USER
WorkingDirectory=$APP_DIR/backend
Environment="DISPLAY=:99"
Environment="PATH=$VENV_DIR/bin:/usr/local/bin:/usr/bin:/bin"
ExecStart=$VENV_DIR/bin/python3 $APP_DIR/backend/bot.py
Restart=always
RestartSec=10
StandardOutput=append:/var/log/aviator-bot.log
StandardError=append:/var/log/aviator-bot.error.log

[Install]
WantedBy=multi-user.target
EOF

    # Create log files
    touch /var/log/aviator-dashboard.log /var/log/aviator-dashboard.error.log
    touch /var/log/aviator-bot.log /var/log/aviator-bot.error.log
    chown "$APP_USER:$APP_USER" /var/log/aviator-*.log

    systemctl daemon-reload
    systemctl enable aviator-dashboard
    # Don't auto-enable bot service (requires user configuration)

    log_success "Systemd services created"
}

setup_firewall() {
    log_info "Configuring firewall..."

    if command -v ufw &> /dev/null; then
        # Allow SSH
        ufw allow 22/tcp comment 'SSH'
        # Allow Dashboard
        ufw allow 5001/tcp comment 'Aviator Dashboard'
        # Allow VNC (optional)
        ufw allow 5900/tcp comment 'VNC Server'

        # Enable firewall (with confirmation skip)
        echo "y" | ufw enable

        log_success "Firewall configured"
    else
        log_warning "ufw not found. Skipping firewall configuration."
    fi
}

setup_log_rotation() {
    log_info "Setting up log rotation..."

    cat > /etc/logrotate.d/aviator-bot << 'EOF'
/var/log/aviator-*.log {
    daily
    rotate 7
    compress
    delaycompress
    notifempty
    create 0644 aviator aviator
    sharedscripts
    postrotate
        systemctl reload aviator-dashboard > /dev/null 2>&1 || true
        systemctl reload aviator-bot > /dev/null 2>&1 || true
    endscript
}

/opt/aviator-bot/backend/*.log {
    daily
    rotate 7
    compress
    delaycompress
    notifempty
    create 0644 aviator aviator
}
EOF

    log_success "Log rotation configured"
}

create_helper_scripts() {
    log_info "Creating helper scripts..."

    # Start script
    cat > "$APP_DIR/start.sh" << 'EOF'
#!/bin/bash
sudo systemctl start xvfb
sudo systemctl start aviator-dashboard
echo "Dashboard started on http://localhost:5001"
echo ""
echo "To start the bot:"
echo "  sudo systemctl start aviator-bot    # Auto mode"
echo "  OR"
echo "  cd /opt/aviator-bot/backend && python3 bot.py  # Interactive mode"
EOF

    # Stop script
    cat > "$APP_DIR/stop.sh" << 'EOF'
#!/bin/bash
sudo systemctl stop aviator-bot
sudo systemctl stop aviator-dashboard
echo "Services stopped"
EOF

    # Status script
    cat > "$APP_DIR/status.sh" << 'EOF'
#!/bin/bash
echo "=== Aviator Bot Status ==="
echo ""
echo "Xvfb Display:"
sudo systemctl status xvfb --no-pager | head -3
echo ""
echo "Dashboard:"
sudo systemctl status aviator-dashboard --no-pager | head -3
echo ""
echo "Bot:"
sudo systemctl status aviator-bot --no-pager | head -3
echo ""
echo "Recent logs:"
echo "  tail -f /var/log/aviator-dashboard.log"
echo "  tail -f /var/log/aviator-bot.log"
EOF

    # Logs script
    cat > "$APP_DIR/logs.sh" << 'EOF'
#!/bin/bash
case "$1" in
    dashboard)
        tail -f /var/log/aviator-dashboard.log
        ;;
    bot)
        tail -f /var/log/aviator-bot.log
        ;;
    error)
        tail -f /var/log/aviator-*.error.log
        ;;
    *)
        echo "Usage: $0 {dashboard|bot|error}"
        echo "Example: $0 dashboard"
        ;;
esac
EOF

    chmod +x "$APP_DIR"/*.sh
    chown "$APP_USER:$APP_USER" "$APP_DIR"/*.sh

    log_success "Helper scripts created"
}

create_env_template() {
    log_info "Creating environment template..."

    cat > "$APP_DIR/.env.template" << 'EOF'
# Aviator Bot Configuration
# Copy this file to .env and update values

# Display settings
DISPLAY=:99

# Tesseract OCR path
TESSERACT_PATH=/usr/bin/tesseract

# Bot mode: observation, dry_run, live
BOT_MODE=dry_run

# Betting parameters
INITIAL_STAKE=25
MAX_STAKE=1000
STAKE_INCREASE_PERCENT=20

# Dashboard settings
FLASK_ENV=production
FLASK_APP=run_dashboard.py
EOF

    chown "$APP_USER:$APP_USER" "$APP_DIR/.env.template"
    log_success "Environment template created at $APP_DIR/.env.template"
}

print_completion_message() {
    echo ""
    echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║                 INSTALLATION COMPLETE!                     ║${NC}"
    echo -e "${GREEN}╚════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    log_success "Aviator Bot has been installed successfully!"
    echo ""
    echo -e "${BLUE}Next Steps:${NC}"
    echo ""
    echo "1. Configure environment:"
    echo "   cd $APP_DIR"
    echo "   cp .env.template .env"
    echo "   nano .env"
    echo ""
    echo "2. Configure screen coordinates:"
    echo "   nano backend/aviator_ml_config.json"
    echo ""
    echo "3. Start services:"
    echo "   sudo systemctl start aviator-dashboard"
    echo "   # Or use: cd $APP_DIR && ./start.sh"
    echo ""
    echo "4. Access dashboard:"
    echo "   http://$(hostname -I | awk '{print $1}'):5001"
    echo "   or http://localhost:5001"
    echo ""
    echo "5. Start bot (interactive mode recommended for first run):"
    echo "   su - $APP_USER"
    echo "   cd $APP_DIR/backend"
    echo "   source ../venv/bin/activate"
    echo "   python3 bot.py"
    echo ""
    echo -e "${YELLOW}Important:${NC}"
    echo "  - Bot service is NOT auto-started (requires configuration)"
    echo "  - Always test in 'observation' or 'dry_run' mode first"
    echo "  - View logs: ./logs.sh dashboard"
    echo "  - Check status: ./status.sh"
    echo ""
    echo -e "${BLUE}Helper Scripts:${NC}"
    echo "  $APP_DIR/start.sh   - Start services"
    echo "  $APP_DIR/stop.sh    - Stop services"
    echo "  $APP_DIR/status.sh  - Check status"
    echo "  $APP_DIR/logs.sh    - View logs"
    echo ""
    echo -e "${GREEN}Installation log saved to: /var/log/aviator-setup.log${NC}"
    echo ""
}

# Main installation flow
main() {
    print_banner

    # Redirect output to log file
    exec 1> >(tee -a /var/log/aviator-setup.log)
    exec 2>&1

    log_info "Starting installation at $(date)"

    check_root
    detect_os
    update_system
    install_dependencies
    create_app_user
    setup_application
    setup_python_environment
    install_python_packages
    setup_virtual_display
    setup_systemd_services
    setup_firewall
    setup_log_rotation
    create_helper_scripts
    create_env_template

    print_completion_message
}

# Run main installation
main "$@"
