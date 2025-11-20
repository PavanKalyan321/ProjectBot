#!/usr/bin/env python3
"""
Database Viewer Dashboard Launcher
Launches the database table viewer dashboard for DigitalOcean droplets
"""

import os
import sys
import argparse

# Add backend to path
backend_path = os.path.join(os.path.dirname(__file__), 'backend')
sys.path.insert(0, backend_path)

from dashboard.database_viewer import run_dashboard


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Database Table Viewer Dashboard for DigitalOcean Droplets'
    )
    parser.add_argument(
        '--host',
        type=str,
        default='0.0.0.0',
        help='Host to bind to (default: 0.0.0.0)'
    )
    parser.add_argument(
        '--port',
        type=int,
        default=5002,
        help='Port to bind to (default: 5002)'
    )

    args = parser.parse_args()

    print("=" * 60)
    print("  Database Table Viewer Dashboard")
    print("=" * 60)
    print(f"  Host: {args.host}")
    print(f"  Port: {args.port}")
    print(f"  URL:  http://localhost:{args.port}")
    print("=" * 60)
    print("\nStarting dashboard...")
    print("\nPress CTRL+C to stop the dashboard\n")

    try:
        run_dashboard(host=args.host, port=args.port)
    except KeyboardInterrupt:
        print("\n\nDashboard stopped by user")
    except Exception as e:
        print(f"\n\nError starting dashboard: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
