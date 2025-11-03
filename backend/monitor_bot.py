"""
Bot Log Monitor - Watches the latest bot log file and provides analysis
"""
import os
import time
import glob
from datetime import datetime

def get_latest_log():
    """Find the most recent bot session log file."""
    log_files = glob.glob("bot_session_*.log")
    if not log_files:
        return None
    return max(log_files, key=os.path.getmtime)

def analyze_log_line(line):
    """Analyze individual log lines for important events."""
    alerts = []

    # Check for ML recommendations
    if "ML Recommendation: PLACE BET" in line:
        alerts.append("🎯 BOT PLACING BET!")
    elif "ML Recommendation: SKIP BET" in line:
        alerts.append("⏭️  Bot skipping this round")

    # Check for balance validation
    if "Balance validation: WIN confirmed" in line:
        alerts.append("✅ WIN DETECTED!")
    elif "Balance validation: LOST" in line:
        alerts.append("❌ LOSS DETECTED")

    # Check for errors
    if "ERROR" in line or "⚠️" in line:
        alerts.append("⚠️  WARNING/ERROR")

    # Check for round results
    if "ROUND #" in line:
        alerts.append("🎮 NEW ROUND STARTED")

    return alerts

def monitor_log(log_file, tail_lines=50):
    """Monitor log file and display updates."""
    print(f"\n{'='*80}")
    print(f"👁️  MONITORING BOT LOG: {log_file}")
    print(f"{'='*80}\n")

    # Read existing content
    if os.path.exists(log_file):
        with open(log_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            # Show last N lines
            print("📜 LAST {} LINES:".format(tail_lines))
            print("-" * 80)
            for line in lines[-tail_lines:]:
                print(line.rstrip())
            print("-" * 80)

    print("\n🔴 LIVE MONITORING (Ctrl+C to stop)...\n")

    # Monitor for new lines
    with open(log_file, 'r', encoding='utf-8') as f:
        # Go to end of file
        f.seek(0, 2)

        while True:
            line = f.readline()
            if line:
                # Print the line
                print(line.rstrip())

                # Analyze and highlight important events
                alerts = analyze_log_line(line)
                for alert in alerts:
                    print(f"  >>> {alert}")
            else:
                time.sleep(0.1)  # Wait for new content

def main():
    """Main monitoring function."""
    print("\n" + "="*80)
    print("🤖 BOT LOG MONITOR")
    print("="*80)

    # Find latest log
    log_file = get_latest_log()

    if not log_file:
        print("\n❌ No bot log files found!")
        print("   Start the bot first: python bot.py")
        return

    print(f"\n📄 Found log: {log_file}")
    print(f"📅 Modified: {datetime.fromtimestamp(os.path.getmtime(log_file)).strftime('%Y-%m-%d %H:%M:%S')}")

    try:
        monitor_log(log_file, tail_lines=30)
    except KeyboardInterrupt:
        print("\n\n⛔ Monitoring stopped by user.")
    except Exception as e:
        print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    main()
