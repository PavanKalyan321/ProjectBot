"""
Test Cloud Sync Connection
Quick test to verify Google Sheets integration is working
"""

import os
import sys
import time
from datetime import datetime

# Add backend to path
sys.path.append('backend')

try:
    from cloud_sync import CloudSync
    print("✅ Cloud sync module imported successfully")
except ImportError as e:
    print(f"❌ Could not import cloud sync: {e}")
    print("💡 Install required packages: pip install gspread google-auth")
    sys.exit(1)

def test_connection():
    """Test Google Sheets connection."""
    print("\n🧪 Testing Google Sheets connection...")
    
    sync = CloudSync("aviator_rounds_history.csv", sync_interval=5)
    
    # Test setup
    if sync.setup_google_sheets():
        print("✅ Google Sheets connection successful!")
        print(f"📊 Spreadsheet URL: {sync.spreadsheet_url}")
        return sync
    else:
        print("❌ Google Sheets connection failed!")
        return None

def test_sync(sync):
    """Test data sync."""
    print("\n📤 Testing data sync...")
    
    # Create test CSV if it doesn't exist
    csv_file = "aviator_rounds_history.csv"
    if not os.path.exists(csv_file):
        print("📝 Creating test CSV file...")
        import csv
        with open(csv_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                'timestamp', 'round_id', 'multiplier',
                'bet_placed', 'stake_amount', 'cashout_time',
                'profit_loss', 'model_prediction', 'model_confidence',
                'model_predicted_range_low', 'model_predicted_range_high'
            ])
            
            # Add test data
            for i in range(5):
                writer.writerow([
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    f"test_{i}",
                    round(2.0 + i * 0.5, 2),
                    i % 2 == 0,
                    25,
                    2.5,
                    10 if i % 2 == 0 else -25,
                    2.3,
                    75.5,
                    1.8,
                    2.8
                ])
        print("✅ Test CSV created with sample data")
    
    # Test manual sync
    if sync.manual_sync():
        print("✅ Manual sync successful!")
        print(f"📊 Check your spreadsheet: {sync.spreadsheet_url}")
        return True
    else:
        print("❌ Manual sync failed!")
        return False

def test_auto_sync(sync):
    """Test automatic sync."""
    print("\n🔄 Testing automatic sync...")
    print("This will run for 30 seconds and sync every 5 seconds")
    print("Press Ctrl+C to stop early")
    
    if not sync.start_sync():
        print("❌ Could not start auto sync")
        return False
    
    try:
        for i in range(6):  # 30 seconds / 5 second intervals
            print(f"⏰ Auto sync running... {i*5}s elapsed")
            time.sleep(5)
            
            status = sync.get_status()
            print(f"   Last sync: {status['last_sync']}")
            print(f"   Rows synced: {status['last_row_count']}")
    
    except KeyboardInterrupt:
        print("\n⏹️ Stopped by user")
    
    sync.stop_sync()
    print("✅ Auto sync test completed")
    return True

def main():
    print("="*60)
    print("🧪 CLOUD SYNC CONNECTION TEST")
    print("="*60)
    
    print("\n📋 This test will:")
    print("1. Test Google Sheets connection")
    print("2. Test manual data sync")
    print("3. Test automatic sync (30 seconds)")
    
    print("\n⚠️ Prerequisites:")
    print("• credentials.json file in project root")
    print("• Google Sheet created and shared with service account")
    print("• Required packages installed (gspread, google-auth)")
    
    input("\nPress Enter to start test...")
    
    # Test 1: Connection
    sync = test_connection()
    if not sync:
        print("\n❌ Connection test failed. Please check setup.")
        return
    
    # Test 2: Manual sync
    if not test_sync(sync):
        print("\n❌ Manual sync test failed.")
        return
    
    # Test 3: Auto sync
    print(f"\n🎯 All tests passed! Your data will sync to:")
    print(f"📊 {sync.spreadsheet_url}")
    
    auto_test = input("\nRun auto-sync test? (y/n): ").strip().lower()
    if auto_test == 'y':
        test_auto_sync(sync)
    
    print("\n" + "="*60)
    print("🎉 CLOUD SYNC TEST COMPLETE!")
    print("="*60)
    
    print("\n✅ Your bot is ready for cloud sync!")
    print("✅ Data will automatically sync every 8 seconds when bot runs")
    print("✅ You can view live data in your Google Sheet")
    
    print(f"\n📊 Spreadsheet: {sync.spreadsheet_url}")
    
    print("\n🚀 Next steps:")
    print("1. Run your bot: python backend/bot_modular.py")
    print("2. Cloud sync will start automatically")
    print("3. Watch your Google Sheet update in real-time!")

if __name__ == "__main__":
    main()