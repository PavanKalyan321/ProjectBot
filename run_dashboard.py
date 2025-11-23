"""
Aviator Bot - Compact Analytics Dashboard Launcher
Quick start script for half-screen dashboard
"""

import sys
import os
import argparse

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from dashboard.compact_analytics import CompactAnalyticsDashboard


def main():
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description='Launch Aviator Bot Dashboard')
    parser.add_argument('--port', type=int, default=5001, help='Port to run dashboard on (default: 5001)')
    parser.add_argument('--host', type=str, default='0.0.0.0', help='Host to bind to (default: 0.0.0.0)')
    parser.add_argument('--no-browser', action='store_true', help='Do not open browser automatically')
    parser.add_argument('--no-cleanup-prompt', action='store_true', help='Skip cleanup prompt')
    args = parser.parse_args()

    print(f"""
    ╔═══════════════════════════════════════════════════════════╗
    ║                                                           ║
    ║       🎯 AVIATOR BOT - COMPACT ANALYTICS DASHBOARD       ║
    ║                                                           ║
    ║   Real-time monitoring optimized for half-screen view    ║
    ║                                                           ║
    ╚═══════════════════════════════════════════════════════════╝

    Configuration:
    - Port: {args.port}
    - Host: {args.host}
    - Browser: {not args.no_browser}

    Features:
    ✓ Live round tracking with all 16 model predictions
    ✓ Trend analysis and trading signals
    ✓ Top performing models ranking
    ✓ Game rules and pattern detection
    ✓ Real-time charts and statistics
    ✓ Data cleanup tools

    """)

    # Check if data files exist
    data_files = [
        'backend/aviator_rounds_history.csv',
        'backend/bet_history.csv',
        'backend/bot_automl_performance.csv'
    ]

    print("Checking data files...")
    for file in data_files:
        exists = "✓" if os.path.exists(file) else "✗"
        print(f"  {exists} {os.path.basename(file)}")

    print()

    # Ask if user wants to cleanup first (only if not skipped and interactive)
    if not args.no_cleanup_prompt and sys.stdin.isatty():
        cleanup = input("Would you like to cleanup data before starting? (y/n): ").lower()

        if cleanup == 'y':
            print("\nRunning data cleanup...")
            from utils.data_manager import DataManager
            manager = DataManager()
            manager.cleanup_all()
            print("\nCleanup complete!")

    # Start dashboard
    print(f"\nStarting dashboard on port {args.port}...")
    print(f"Access at: http://localhost:{args.port}")
    print("\nTIP: Resize your browser to 50% width for optimal half-screen viewing")
    print("     Place Aviator game on the other half of your screen\n")

    dashboard = CompactAnalyticsDashboard(port=args.port)
    dashboard.run(open_browser=not args.no_browser)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nDashboard stopped by user. Goodbye!")
    except Exception as e:
        print(f"\n\nError: {e}")
        print("\nMake sure you have all dependencies installed:")
        print("  pip install flask flask-socketio pandas numpy")
        sys.exit(1)
