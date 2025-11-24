#!/bin/bash
################################################################################
#                    DEBIAN AUTOMATED SETUP SCRIPT
#                   Aviator Round Logger Installation
################################################################################
#
# This script automates the complete setup on Debian Linux
#
# Usage:
#   chmod +x debian_setup.sh
#   ./debian_setup.sh
#
# What it does:
#   1. Updates package manager
#   2. Installs system dependencies
#   3. Installs Tesseract OCR
#   4. Creates Python virtual environment
#   5. Installs Python packages
#   6. Prompts for environment configuration
#   7. Verifies everything works
#
################################################################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
print_header() {
    echo ""
    echo -e "${BLUE}================================================================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}================================================================================${NC}"
    echo ""
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

# Check if running on Debian/Ubuntu
check_os() {
    print_header "Checking Operating System"

    if [ -f /etc/os-release ]; then
        . /etc/os-release
        if [[ "$ID" == "debian" || "$ID" == "ubuntu" || "$ID_LIKE" == *"debian"* ]]; then
            print_success "Running on Debian-based system ($PRETTY_NAME)"
            return 0
        else
            print_error "This script is for Debian/Ubuntu only"
            print_error "Detected: $PRETTY_NAME"
            exit 1
        fi
    else
        print_error "Cannot detect OS"
        exit 1
    fi
}

# Check if running as root
check_sudo() {
    if [ "$EUID" -eq 0 ]; then
        print_error "Please do NOT run this script as root"
        print_info "Run without sudo: ./debian_setup.sh"
        exit 1
    fi
}

# Update package manager
update_packages() {
    print_header "Step 1: Updating Package Manager"

    print_info "Running: sudo apt-get update"
    sudo apt-get update -qq
    print_success "Package manager updated"
}

# Install system dependencies
install_dependencies() {
    print_header "Step 2: Installing System Dependencies"

    print_info "Installing: python3, python3-pip, python3-venv, build-essential, libpq-dev"

    sudo apt-get install -y -qq \
        python3 \
        python3-pip \
        python3-venv \
        build-essential \
        libpq-dev

    print_success "System dependencies installed"

    # Verify Python
    python3_version=$(python3 --version 2>&1 | awk '{print $2}')
    print_success "Python version: $python3_version"

    if [[ $python3_version < "3.8" ]]; then
        print_warning "Python version is older than 3.8, some packages may not work"
        print_warning "Consider installing Python 3.9+ from deadsnakes PPA"
    fi
}

# Install Tesseract OCR
install_tesseract() {
    print_header "Step 3: Installing Tesseract OCR"

    print_info "Installing: tesseract-ocr, libtesseract-dev"

    sudo apt-get install -y -qq \
        tesseract-ocr \
        libtesseract-dev

    print_success "Tesseract OCR installed"

    # Verify Tesseract
    tesseract_version=$(tesseract --version 2>&1 | head -1 | awk '{print $2}')
    print_success "Tesseract version: $tesseract_version"
}

# Install screen for background processes
install_screen() {
    print_header "Step 4: Installing Screen (for background processes)"

    print_info "Installing: screen"

    sudo apt-get install -y -qq screen

    print_success "Screen installed"
}

# Create virtual environment
create_venv() {
    print_header "Step 5: Creating Python Virtual Environment"

    if [ -d "venv" ]; then
        print_warning "Virtual environment already exists at venv/"
        read -p "Overwrite? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            rm -rf venv
        else
            print_info "Keeping existing venv"
            return 0
        fi
    fi

    print_info "Creating venv directory..."
    python3 -m venv venv

    print_success "Virtual environment created at venv/"
}

# Activate and upgrade venv
upgrade_pip() {
    print_header "Step 6: Upgrading pip"

    print_info "Activating venv and upgrading pip..."
    source venv/bin/activate

    pip install --upgrade pip --quiet

    print_success "pip upgraded"
}

# Install Python packages
install_python_packages() {
    print_header "Step 7: Installing Python Packages"

    source venv/bin/activate

    # Check if requirements.txt exists
    if [ ! -f "requirements.txt" ]; then
        print_warning "requirements.txt not found"
        print_info "Installing packages manually..."

        pip install --quiet \
            pytesseract==0.3.10 \
            opencv-python==4.8.1.78 \
            mss==9.0.1 \
            pillow==10.0.1 \
            psycopg2-binary==2.9.9 \
            python-dotenv==1.0.0 \
            numpy
    else
        print_info "Installing from requirements.txt..."
        pip install --quiet -r requirements.txt
    fi

    print_success "Python packages installed"

    # Verify key packages
    python3 -c "import pytesseract; print('  ✓ pytesseract OK')" 2>/dev/null || true
    python3 -c "import cv2; print('  ✓ opencv-python OK')" 2>/dev/null || true
    python3 -c "import mss; print('  ✓ mss OK')" 2>/dev/null || true
    python3 -c "import psycopg2; print('  ✓ psycopg2 OK')" 2>/dev/null || true
}

# Configure .env file
configure_env() {
    print_header "Step 8: Configuring Environment Variables"

    if [ -f ".env" ]; then
        print_info ".env file already exists"
        read -p "Overwrite? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            print_info "Keeping existing .env"
            return 0
        fi
    fi

    print_info "Creating .env file..."

    read -p "Enter DB_HOST (zofojiubrykbtmstfhzx.supabase.co): " db_host
    db_host=${db_host:-"zofojiubrykbtmstfhzx.supabase.co"}

    read -p "Enter DB_PORT (5432): " db_port
    db_port=${db_port:-"5432"}

    read -p "Enter DB_NAME (postgres): " db_name
    db_name=${db_name:-"postgres"}

    read -p "Enter DB_USER (postgres): " db_user
    db_user=${db_user:-"postgres"}

    read -sp "Enter DB_PASSWORD: " db_password
    echo

    # Write .env file
    cat > .env << EOF
DB_HOST=$db_host
DB_PORT=$db_port
DB_NAME=$db_name
DB_USER=$db_user
DB_PASSWORD=$db_password
EOF

    # Secure permissions
    chmod 600 .env

    print_success ".env file created (permissions: 600)"
}

# Run test script
run_tests() {
    print_header "Step 9: Running System Tests"

    source venv/bin/activate

    if [ -f "TEST_LOGGER.py" ]; then
        print_info "Running TEST_LOGGER.py..."
        python TEST_LOGGER.py
    else
        print_warning "TEST_LOGGER.py not found"
        print_info "Skipping tests"
    fi
}

# Final summary
print_summary() {
    print_header "Setup Complete!"

    print_success "All system dependencies installed"
    print_success "Python virtual environment created"
    print_success "Python packages installed"
    print_success "Environment configured"

    echo ""
    echo "Next steps:"
    echo ""
    echo "1. Activate virtual environment:"
    echo "   source venv/bin/activate"
    echo ""
    echo "2. Run tests (optional):"
    echo "   python TEST_LOGGER.py"
    echo ""
    echo "3. Start the logger:"
    echo "   python standalone_round_logger.py"
    echo ""
    echo "4. Or run in background with screen:"
    echo "   screen -S logger"
    echo "   python standalone_round_logger.py"
    echo "   (Ctrl+A then D to detach)"
    echo ""
    echo "5. Monitor in Supabase:"
    echo "   Go to: https://app.supabase.com"
    echo "   SQL Editor: SELECT * FROM \"AviatorRound\" LIMIT 10;"
    echo ""
}

################################################################################
#                            MAIN EXECUTION
################################################################################

main() {
    print_header "Aviator Round Logger - Debian Setup"

    print_info "This script will install and configure the Aviator Round Logger"
    print_info "It will install system packages, Python dependencies, and Tesseract OCR"
    print_warning "You will be asked for your sudo password"

    echo ""
    read -p "Continue with installation? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_info "Setup cancelled"
        exit 0
    fi

    # Run all steps
    check_os
    check_sudo
    update_packages
    install_dependencies
    install_tesseract
    install_screen
    create_venv
    upgrade_pip
    install_python_packages
    configure_env

    # Optionally run tests
    echo ""
    read -p "Run system tests now? (Y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Nn]$ ]]; then
        run_tests
    fi

    print_summary
}

# Run main function
main
