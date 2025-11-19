"""
Google Sheets Cloud Sync for Aviator Bot
Automatically syncs aviator_rounds_history.csv to Google Sheets
"""

import os
import time
import pandas as pd
import threading
from datetime import datetime
import json

try:
    import gspread
    from google.oauth2.service_account import Credentials
    GSPREAD_AVAILABLE = True
except ImportError:
    GSPREAD_AVAILABLE = False
    print("⚠️ Google Sheets sync disabled. Install: pip install gspread google-auth")


class CloudSync:
    """Sync CSV data to Google Sheets in real-time."""
    
    def __init__(self, csv_file="aviator_rounds_history.csv", sync_interval=10):
        """
        Initialize cloud sync.
        
        Args:
            csv_file: Path to CSV file to sync
            sync_interval: Sync interval in seconds (default 10)
        """
        self.csv_file = csv_file
        self.sync_interval = sync_interval
        self.is_running = False
        self.sync_thread = None
        self.last_sync_time = 0
        self.last_row_count = 0
        
        # Google Sheets setup
        self.gc = None
        self.worksheet = None
        self.spreadsheet_url = None
        
        # Config file for storing settings
        self.config_file = "cloud_sync_config.json"
        self.config = self.load_config()
        
        # Set your specific spreadsheet ID
        self.config["spreadsheet_id"] = "1cSluu2sjFA9WZU3fhS2NV220-rBEsy6cQL4Ol4xz31s"
    
    def load_config(self):
        """Load sync configuration."""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    return json.load(f)
        except:
            pass
        return {
            "spreadsheet_id": "1cSluu2sjFA9WZU3fhS2NV220-rBEsy6cQL4Ol4xz31s",
            "worksheet_name": "Aviator_Data",
            "credentials_file": "credentials.json",
            "auto_sync": True
        }
    
    def save_config(self):
        """Save sync configuration."""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            print(f"Error saving config: {e}")
    
    def setup_google_sheets(self):
        """Setup Google Sheets connection."""
        if not GSPREAD_AVAILABLE:
            print("❌ Google Sheets not available. Install required packages.")
            return False
        
        try:
            # Check for credentials file
            creds_file = self.config.get("credentials_file", "credentials.json")
            if not os.path.exists(creds_file):
                print(f"❌ Credentials file not found: {creds_file}")
                print("\n📋 Setup Instructions:")
                print("1. Go to https://console.cloud.google.com/")
                print("2. Create a new project or select existing")
                print("3. Enable Google Sheets API")
                print("4. Create Service Account credentials")
                print("5. Download JSON file as 'credentials.json'")
                print("6. Share your Google Sheet with the service account email")
                return False
            
            # Setup credentials
            scope = [
                'https://spreadsheets.google.com/feeds',
                'https://www.googleapis.com/auth/drive'
            ]
            
            creds = Credentials.from_service_account_file(creds_file, scopes=scope)
            self.gc = gspread.authorize(creds)
            
            # Setup spreadsheet
            if self.config.get("spreadsheet_id"):
                # Use existing spreadsheet
                try:
                    spreadsheet = self.gc.open_by_key(self.config["spreadsheet_id"])
                    print(f"✅ Connected to existing spreadsheet")
                except:
                    print("❌ Could not open existing spreadsheet, creating new one...")
                    spreadsheet = self.create_new_spreadsheet()
            else:
                # Create new spreadsheet
                spreadsheet = self.create_new_spreadsheet()
            
            if not spreadsheet:
                return False
            
            # Get or create worksheet
            worksheet_name = self.config.get("worksheet_name", "Aviator_Data")
            try:
                self.worksheet = spreadsheet.worksheet(worksheet_name)
            except:
                self.worksheet = spreadsheet.add_worksheet(
                    title=worksheet_name, 
                    rows=1000, 
                    cols=20
                )
            
            self.spreadsheet_url = f"https://docs.google.com/spreadsheets/d/{spreadsheet.id}"
            print(f"✅ Google Sheets connected: {self.spreadsheet_url}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error setting up Google Sheets: {e}")
            return False
    
    def create_new_spreadsheet(self):
        """Create a new Google Spreadsheet."""
        try:
            spreadsheet_name = f"Aviator_Bot_Data_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            spreadsheet = self.gc.create(spreadsheet_name)
            
            # Save spreadsheet ID
            self.config["spreadsheet_id"] = spreadsheet.id
            self.save_config()
            
            print(f"✅ Created new spreadsheet: {spreadsheet_name}")
            return spreadsheet
            
        except Exception as e:
            print(f"❌ Error creating spreadsheet: {e}")
            return None
    
    def sync_to_sheets(self):
        """Sync CSV data to Google Sheets."""
        if not self.worksheet:
            return False
        
        try:
            # Check if CSV exists and has new data
            if not os.path.exists(self.csv_file):
                return False
            
            # Read CSV
            df = pd.read_csv(self.csv_file)
            if df.empty:
                return False
            
            # Check if there's new data
            current_row_count = len(df)
            if current_row_count <= self.last_row_count:
                return False  # No new data
            
            # Prepare data for upload
            # Convert DataFrame to list of lists (Google Sheets format)
            headers = df.columns.tolist()
            data = df.values.tolist()
            
            # Clear existing data and upload fresh data
            self.worksheet.clear()
            
            # Upload headers
            self.worksheet.append_row(headers)
            
            # Upload data in batches (Google Sheets has rate limits)
            batch_size = 100
            for i in range(0, len(data), batch_size):
                batch = data[i:i + batch_size]
                self.worksheet.append_rows(batch)
                time.sleep(0.1)  # Small delay to avoid rate limits
            
            self.last_row_count = current_row_count
            self.last_sync_time = time.time()
            
            print(f"✅ Synced {current_row_count} rows to Google Sheets")
            return True
            
        except Exception as e:
            print(f"❌ Error syncing to Google Sheets: {e}")
            return False
    
    def sync_new_rows_only(self):
        """Sync only new rows to Google Sheets (more efficient)."""
        if not self.worksheet:
            return False
        
        try:
            # Check if CSV exists
            if not os.path.exists(self.csv_file):
                return False
            
            # Read CSV
            df = pd.read_csv(self.csv_file)
            if df.empty:
                return False
            
            current_row_count = len(df)
            
            # If first sync, upload all data
            if self.last_row_count == 0:
                return self.sync_to_sheets()
            
            # Check for new rows
            if current_row_count <= self.last_row_count:
                return False  # No new data
            
            # Get only new rows
            new_rows = df.iloc[self.last_row_count:].values.tolist()
            
            # Append new rows
            self.worksheet.append_rows(new_rows)
            
            self.last_row_count = current_row_count
            self.last_sync_time = time.time()
            
            print(f"✅ Synced {len(new_rows)} new rows to Google Sheets")
            return True
            
        except Exception as e:
            print(f"❌ Error syncing new rows: {e}")
            return False
    
    def sync_loop(self):
        """Main sync loop running in background thread."""
        print(f"🔄 Starting cloud sync (every {self.sync_interval}s)")
        
        while self.is_running:
            try:
                if self.config.get("auto_sync", True):
                    self.sync_new_rows_only()
                
                time.sleep(self.sync_interval)
                
            except Exception as e:
                print(f"❌ Error in sync loop: {e}")
                time.sleep(self.sync_interval)
    
    def start_sync(self):
        """Start background sync thread."""
        if not self.setup_google_sheets():
            print("❌ Could not setup Google Sheets connection")
            return False
        
        if self.is_running:
            print("⚠️ Sync already running")
            return True
        
        self.is_running = True
        self.sync_thread = threading.Thread(target=self.sync_loop, daemon=True)
        self.sync_thread.start()
        
        print(f"✅ Cloud sync started")
        print(f"📊 Spreadsheet: {self.spreadsheet_url}")
        return True
    
    def stop_sync(self):
        """Stop background sync."""
        self.is_running = False
        if self.sync_thread:
            self.sync_thread.join(timeout=5)
        print("⏹️ Cloud sync stopped")
    
    def manual_sync(self):
        """Perform manual sync."""
        if not self.worksheet:
            if not self.setup_google_sheets():
                return False
        
        return self.sync_to_sheets()
    
    def get_status(self):
        """Get sync status."""
        return {
            "is_running": self.is_running,
            "last_sync": datetime.fromtimestamp(self.last_sync_time).strftime("%Y-%m-%d %H:%M:%S") if self.last_sync_time else "Never",
            "spreadsheet_url": self.spreadsheet_url,
            "last_row_count": self.last_row_count,
            "sync_interval": self.sync_interval
        }


def main():
    """Setup and test cloud sync."""
    print("="*60)
    print("☁️ AVIATOR BOT - GOOGLE SHEETS SYNC SETUP")
    print("="*60)
    
    if not GSPREAD_AVAILABLE:
        print("\n❌ Required packages not installed!")
        print("Run: pip install gspread google-auth")
        return
    
    sync = CloudSync()
    
    print("\n📋 Setup Options:")
    print("1. Setup new Google Sheets connection")
    print("2. Test existing connection")
    print("3. Manual sync now")
    print("4. Start auto-sync")
    
    choice = input("\nChoice (1-4): ").strip()
    
    if choice == "1":
        print("\n🔧 Setting up Google Sheets...")
        print("\n📋 Prerequisites:")
        print("1. ✅ Google Cloud Console project")
        print("2. ✅ Google Sheets API enabled")
        print("3. ✅ Service Account created")
        print("4. ✅ credentials.json downloaded")
        print("5. ✅ Google Sheet shared with service account email")
        
        input("\nPress Enter when ready...")
        
        if sync.setup_google_sheets():
            print(f"\n✅ Setup complete!")
            print(f"📊 Spreadsheet: {sync.spreadsheet_url}")
        
    elif choice == "2":
        print("\n🧪 Testing connection...")
        if sync.setup_google_sheets():
            print("✅ Connection successful!")
        else:
            print("❌ Connection failed!")
    
    elif choice == "3":
        print("\n📤 Manual sync...")
        if sync.manual_sync():
            print("✅ Sync successful!")
        else:
            print("❌ Sync failed!")
    
    elif choice == "4":
        print("\n🚀 Starting auto-sync...")
        if sync.start_sync():
            print("✅ Auto-sync started!")
            print("Press Ctrl+C to stop...")
            try:
                while True:
                    status = sync.get_status()
                    print(f"\r⏰ Last sync: {status['last_sync']} | Rows: {status['last_row_count']}", end="")
                    time.sleep(5)
            except KeyboardInterrupt:
                sync.stop_sync()
                print("\n⏹️ Stopped")


if __name__ == "__main__":
    main()