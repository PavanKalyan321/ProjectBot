"""
Google Sheets Cloud Sync Setup
Quick setup script for connecting your Aviator bot to Google Sheets
"""

import os
import sys

def main():
    print("="*60)
    print("☁️ AVIATOR BOT - GOOGLE SHEETS SETUP")
    print("="*60)
    
    print("\n📋 STEP-BY-STEP SETUP GUIDE:")
    print("\n1️⃣ INSTALL REQUIRED PACKAGES")
    print("   Run this command:")
    print("   pip install gspread google-auth")
    
    print("\n2️⃣ CREATE GOOGLE CLOUD PROJECT")
    print("   • Go to: https://console.cloud.google.com/")
    print("   • Create new project or select existing")
    print("   • Enable Google Sheets API")
    
    print("\n3️⃣ CREATE SERVICE ACCOUNT")
    print("   • Go to: APIs & Services > Credentials")
    print("   • Click 'Create Credentials' > 'Service Account'")
    print("   • Fill in service account details")
    print("   • Click 'Create and Continue'")
    
    print("\n4️⃣ DOWNLOAD CREDENTIALS")
    print("   • Click on your service account")
    print("   • Go to 'Keys' tab")
    print("   • Click 'Add Key' > 'Create New Key'")
    print("   • Choose 'JSON' format")
    print("   • Save as 'credentials.json' in this folder")
    
    print("\n5️⃣ CREATE GOOGLE SHEET")
    print("   • Go to: https://sheets.google.com/")
    print("   • Create a new spreadsheet")
    print("   • Name it 'Aviator Bot Data' (or any name)")
    
    print("\n6️⃣ SHARE SHEET WITH SERVICE ACCOUNT")
    print("   • Open your credentials.json file")
    print("   • Find the 'client_email' field")
    print("   • Copy that email address")
    print("   • In Google Sheets, click 'Share'")
    print("   • Paste the service account email")
    print("   • Give 'Editor' permissions")
    print("   • Click 'Send'")
    
    print("\n7️⃣ TEST CONNECTION")
    print("   • Run: python backend/cloud_sync.py")
    print("   • Choose option 2 to test connection")
    
    print("\n" + "="*60)
    print("🎯 QUICK START COMMANDS")
    print("="*60)
    
    print("\n# Install packages")
    print("pip install gspread google-auth")
    
    print("\n# Test cloud sync")
    print("cd backend")
    print("python cloud_sync.py")
    
    print("\n# Start bot with cloud sync")
    print("python bot_modular.py")
    
    print("\n" + "="*60)
    print("📁 FILE STRUCTURE")
    print("="*60)
    
    print("\nAfter setup, you should have:")
    print("📁 Project/")
    print("├── credentials.json          ← Google service account key")
    print("├── backend/")
    print("│   ├── cloud_sync.py        ← Cloud sync module")
    print("│   ├── cloud_sync_config.json ← Auto-generated config")
    print("│   └── aviator_rounds_history.csv ← Your data")
    
    print("\n" + "="*60)
    print("⚠️ TROUBLESHOOTING")
    print("="*60)
    
    print("\n❌ 'gspread not found'")
    print("   → Run: pip install gspread google-auth")
    
    print("\n❌ 'credentials.json not found'")
    print("   → Download from Google Cloud Console")
    print("   → Save in Project/ folder (same level as this script)")
    
    print("\n❌ 'Permission denied' on Google Sheets")
    print("   → Share sheet with service account email")
    print("   → Give 'Editor' permissions")
    
    print("\n❌ 'Spreadsheet not found'")
    print("   → Check spreadsheet ID in cloud_sync_config.json")
    print("   → Make sure sheet is shared with service account")
    
    print("\n" + "="*60)
    print("🚀 WHAT HAPPENS NEXT")
    print("="*60)
    
    print("\n✅ Your CSV data will sync to Google Sheets every 8 seconds")
    print("✅ You can view real-time data from anywhere")
    print("✅ Data is automatically backed up in the cloud")
    print("✅ You can create charts and analysis in Google Sheets")
    print("✅ Multiple people can view the same data")
    
    print("\n" + "="*60)
    print("🎉 READY TO START!")
    print("="*60)
    
    print("\nOnce setup is complete:")
    print("1. Run your bot normally: python backend/bot_modular.py")
    print("2. Cloud sync will start automatically")
    print("3. Check your Google Sheet for live data!")
    
    print("\n📊 Your Google Sheet will contain:")
    print("   • Timestamp of each round")
    print("   • Multiplier values")
    print("   • Bet information")
    print("   • Profit/loss data")
    print("   • ML predictions")
    print("   • And much more!")


if __name__ == "__main__":
    main()