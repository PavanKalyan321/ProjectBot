#!/bin/bash
################################################################################
#                       RESTART XVFB DISPLAY
#
# Purpose: Clear rendering context and restart virtual display
# Usage: Called by systemd before bot starts
# Effect: Fixes "unable to auto-find suitable render" errors
#
# This script:
# 1. Restarts the Xvfb virtual display service
# 2. Clears stale rendering resources
# 3. Gives system time to reinitialize (2 second wait)
# 4. Ready for new bot instance with clean display
#
################################################################################

set -e  # Exit on error

echo "=================================================="
echo "Restarting Xvfb Virtual Display"
echo "=================================================="
echo "Time: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""

# Restart Xvfb service
echo "1. Stopping Xvfb service..."
sudo systemctl stop xvfb 2>/dev/null || echo "   (not running)"

echo "2. Waiting for cleanup..."
sleep 1

echo "3. Starting Xvfb service..."
sudo systemctl start xvfb

echo "4. Waiting for initialization..."
sleep 2

echo ""
echo "=================================================="
echo "✓ Xvfb restarted successfully"
echo "✓ Rendering context cleared"
echo "✓ Ready for bot instance"
echo "=================================================="
echo ""

exit 0
