"""
One-time sync of all existing data to Google Sheets
"""

import sys
import os
sys.path.append('backend')

from cloud_sync import CloudSync

def main():
    print("📤 Syncing all existing data to Google Sheets...")
    
    # Create sync instance
    sync = CloudSync("backend/aviator_rounds_history.csv")
    
    # Setup connection
    if not sync.setup_google_sheets():
        print("❌ Failed to connect to Google Sheets")
        return
    
    # Force full sync of all data
    if sync.sync_to_sheets():
        print("✅ All data synced successfully!")
        print(f"📊 View at: {sync.spreadsheet_url}")
    else:
        print("❌ Sync failed")

if __name__ == "__main__":
    main()