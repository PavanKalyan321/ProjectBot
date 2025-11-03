#!/bin/bash
set -e

# Start Xvfb (Virtual Frame Buffer) for headless display
if [ ! -z "$DISPLAY" ]; then
    echo "Starting Xvfb on display $DISPLAY..."
    Xvfb $DISPLAY -screen 0 1920x1080x24 &
    XVFB_PID=$!

    # Wait for X server to start
    sleep 2

    echo "Xvfb started with PID $XVFB_PID"
fi

# Execute the main command
exec "$@"
