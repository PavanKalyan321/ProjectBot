"""
Standalone Coordinate Validation Script
Perfect for VM setup and testing coordinate accuracy
"""

import time
import csv
import re
import pyautogui
import pyperclip
from datetime import datetime
from config import ConfigManager
from readregion import MultiplierReader


def validate_coordinates(duration=30):
    """
    Continuously read and log all coordinate values for validation.

    Args:
        duration: How long to run validation (seconds)
    """
    print("\n" + "="*80)
    print("🔍 COORDINATE VALIDATION TOOL")
    print("="*80)
    print("\nThis tool will:")
    print("  ✓ Load coordinates from your config")
    print("  ✓ Continuously read multiplier and balance")
    print("  ✓ Log all readings to CSV")
    print("  ✓ Display live readings in console")
    print("="*80)

    # Load configuration
    config_manager = ConfigManager()
    if not config_manager.load_config():
        print("\n❌ No configuration found!")
        print("Please run the main bot to setup coordinates first.")
        return

    print("\n📍 Loaded Configuration:")
    print(f"   Multiplier Region: {config_manager.multiplier_region}")
    print(f"   Balance Region: {config_manager.balance_region}")
    print(f"   Stake Coords: {config_manager.stake_coords}")
    print(f"   Bet Button: {config_manager.bet_button_coords}")
    print(f"   Cashout Button: {config_manager.cashout_coords}")

    # Initialize multiplier reader
    if not config_manager.multiplier_region:
        print("\n❌ Multiplier region not configured!")
        return

    x, y, w, h = config_manager.multiplier_region
    region_dict = {"left": x, "top": y, "width": w, "height": h}
    multiplier_reader = MultiplierReader(region_dict, enable_logging=False)

    balance_coords = config_manager.balance_region

    print(f"\n⏱️  Running validation for {duration} seconds...")
    print("Make sure the game window is visible!")

    input("\nPress ENTER when ready to start...")

    # Create validation log file
    validation_file = f"coordinate_validation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

    with open(validation_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([
            'Timestamp',
            'Iteration',
            'Multiplier_Reading',
            'Multiplier_Status',
            'Balance_Reading',
            'Balance_Raw_Text',
            'Region_Capture_Success',
            'Frame_Shape',
            'Multiplier_Region',
            'Balance_Region',
            'All_Coords'
        ])

    start_time = time.time()
    iteration = 0

    print("\n" + "="*80)
    print("📊 LIVE READINGS (updating every 0.5s)")
    print("="*80)
    print(f"{'Iter':<6} {'Time':<12} {'Multiplier':<15} {'Status':<10} {'Balance':<12} {'Raw Balance':<20}")
    print("-" * 80)

    try:
        while time.time() - start_time < duration:
            iteration += 1
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
            elapsed = time.time() - start_time
            time_str = f"{elapsed:6.1f}s"

            # Read multiplier
            mult_reading = "N/A"
            mult_status = "UNKNOWN"
            frame_shape = "N/A"
            capture_success = False

            try:
                frame = multiplier_reader.capture_region()
                if frame is not None:
                    capture_success = True
                    frame_shape = str(frame.shape)

                    # Try to read multiplier
                    value = multiplier_reader.fast_extract_multiplier_or_status(frame)
                    if value == "AWAITING NEXT FLIGHT":
                        mult_reading = "AWAITING"
                        mult_status = "AWAITING"
                    elif value:
                        mult_reading = f"{value:.2f}x" if isinstance(value, (int, float)) else str(value)
                        mult_status = "ACTIVE" if isinstance(value, (int, float)) else "TEXT"
                else:
                    mult_reading = "CAPTURE_FAIL"
                    mult_status = "ERROR"
            except Exception as e:
                mult_reading = f"ERROR"
                mult_status = "ERROR"

            # Read balance
            balance_reading = "N/A"
            balance_raw = "N/A"

            try:
                if balance_coords:
                    x1, y1, x2, y2 = balance_coords
                    # Click to select
                    pyautogui.click((x1 + x2) // 2, (y1 + y2) // 2, clicks=3)
                    time.sleep(0.08)
                    # Copy
                    pyautogui.hotkey('ctrl', 'c')
                    time.sleep(0.08)
                    balance_raw = pyperclip.paste().strip()

                    # Try to parse
                    if balance_raw:
                        if 'K' in balance_raw.upper():
                            match = re.search(r'([\d.]+)\s*K', balance_raw.upper())
                            if match:
                                balance_reading = f"{float(match.group(1)) * 1000:.2f}"
                        else:
                            match = re.search(r'([\d.]+)', balance_raw)
                            if match:
                                balance_reading = match.group(1)
            except Exception as e:
                balance_reading = "ERROR"

            # Coordinates summary
            all_coords = {
                'mult': config_manager.multiplier_region,
                'bal': balance_coords,
                'stake': config_manager.stake_coords,
                'bet': config_manager.bet_button_coords,
                'cashout': config_manager.cashout_coords
            }

            # Log to CSV
            with open(validation_file, 'a', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    timestamp,
                    iteration,
                    mult_reading,
                    mult_status,
                    balance_reading,
                    balance_raw,
                    capture_success,
                    frame_shape,
                    config_manager.multiplier_region,
                    balance_coords,
                    str(all_coords)
                ])

            # Print to console with color coding
            status_icon = {
                'ACTIVE': '🟢',
                'AWAITING': '🟡',
                'TEXT': '🔵',
                'ERROR': '🔴',
                'UNKNOWN': '⚪'
            }.get(mult_status, '⚪')

            print(f"{iteration:<6} {time_str:<12} {mult_reading:<15} {status_icon}{mult_status:<9} {balance_reading:<12} {balance_raw[:20]:<20}", flush=True)

            time.sleep(0.5)  # Update every 500ms

    except KeyboardInterrupt:
        print("\n\n⚠️  Validation stopped by user (Ctrl+C)")

    print("\n" + "="*80)
    print("✅ VALIDATION COMPLETE!")
    print("="*80)
    print(f"📄 CSV Log: {validation_file}")
    print(f"📊 Total Iterations: {iteration}")
    print(f"⏱️  Duration: {time.time() - start_time:.1f} seconds")
    print("\n💡 Review the CSV file to verify:")
    print("   • Multiplier readings are accurate")
    print("   • Balance readings match displayed balance")
    print("   • Frame captures are successful")
    print("   • All coordinates are correct")
    print("="*80)

    return validation_file


def quick_test():
    """Quick test mode - reads once and displays"""
    print("\n" + "="*80)
    print("⚡ QUICK COORDINATE TEST")
    print("="*80)

    # Load configuration
    config_manager = ConfigManager()
    if not config_manager.load_config():
        print("\n❌ No configuration found!")
        return

    print("\n📍 Configuration Loaded:")
    config = config_manager.get_config_dict()
    for key, value in config.items():
        print(f"   {key}: {value}")

    if not config_manager.multiplier_region:
        print("\n❌ Multiplier region not configured!")
        return

    # Initialize multiplier reader
    x, y, w, h = config_manager.multiplier_region
    region_dict = {"left": x, "top": y, "width": w, "height": h}
    multiplier_reader = MultiplierReader(region_dict, enable_logging=False)

    print("\n🔍 Reading current values...")

    # Test multiplier reading
    try:
        frame = multiplier_reader.capture_region()
        if frame is not None:
            print(f"✅ Frame captured: {frame.shape}")
            value = multiplier_reader.fast_extract_multiplier_or_status(frame)
            print(f"📊 Multiplier: {value}")
        else:
            print("❌ Frame capture failed")
    except Exception as e:
        print(f"❌ Multiplier read error: {e}")

    # Test balance reading
    try:
        if config_manager.balance_region:
            x1, y1, x2, y2 = config_manager.balance_region
            pyautogui.click((x1 + x2) // 2, (y1 + y2) // 2, clicks=3)
            time.sleep(0.1)
            pyautogui.hotkey('ctrl', 'c')
            time.sleep(0.1)
            balance_raw = pyperclip.paste().strip()
            print(f"💰 Balance raw: '{balance_raw}'")
    except Exception as e:
        print(f"❌ Balance read error: {e}")

    print("="*80)


if __name__ == "__main__":
    print("\n" + "="*80)
    print("🔍 COORDINATE VALIDATION TOOL")
    print("="*80)
    print("\nSelect mode:")
    print("  1. Quick test (single reading)")
    print("  2. Continuous validation (recommended for VM)")
    print("  3. Exit")

    choice = input("\nChoice (1/2/3): ").strip()

    if choice == '1':
        quick_test()
    elif choice == '2':
        duration_input = input("\nValidation duration in seconds (default: 30): ").strip()
        duration = int(duration_input) if duration_input and duration_input.isdigit() else 30
        validate_coordinates(duration)
    else:
        print("\n👋 Exiting...")
