# Supabase Integration Setup Guide

Your Aviator Bot project is now configured to use **Supabase** as the PostgreSQL database. This guide walks you through the final setup steps.

## ✅ What's Already Done

1. ✅ Created `.env` file with Supabase credentials
2. ✅ Updated `backend/database/config.py` to load from Supabase
3. ✅ Added `python-dotenv` and database dependencies to `requirements.txt`
4. ✅ Updated `.gitignore` to protect `.env` file
5. ✅ Created schema file ready for Supabase

## 📋 Step 1: Create Schema in Supabase (Manual - No Connection Timeout Issues)

Since there may be firewall/network restrictions preventing direct Python connections, we'll create the schema manually using Supabase's web interface:

### 1.1 Go to Supabase SQL Editor

1. Open [Supabase Dashboard](https://app.supabase.com)
2. Click on your project: `zofojiubrykbtmstfhzx`
3. Click **SQL Editor** in the left sidebar
4. Click **New Query**

### 1.2 Copy & Paste the Schema

The complete schema is in: `backend/database/schema.sql`

**Steps:**
1. Open `backend/database/schema.sql` in a text editor
2. Copy the entire contents
3. Paste into the Supabase SQL Editor
4. Click **Run** (or press Cmd/Ctrl + Enter)

**Expected Result:** All 9 tables created with no errors

```
✓ Tables created:
  - bot_vm_registration
  - game_platform_config
  - crash_game_rounds (51 fields)
  - analytics_round_multipliers
  - analytics_round_signals
  - analytics_round_outcomes
  - session_logs
  - error_logs
  - ocr_validation_logs
```

## 🔧 Step 2: Verify Schema Creation

In Supabase SQL Editor, run this query to verify:

```sql
-- Check all tables exist
SELECT table_name FROM information_schema.tables
WHERE table_schema = 'public'
ORDER BY table_name;
```

You should see 9 tables listed.

## 🚀 Step 3: Update Python Dependencies

Run this in your project directory:

```bash
pip install -r requirements.txt
```

This installs:
- `python-dotenv` - Load credentials from .env
- `sqlalchemy` - ORM for database operations
- `psycopg2-binary` - PostgreSQL driver

## 🔌 Step 4: Test Connection from Python (After Schema Creation)

Once you've created the schema in Supabase, test the connection:

```bash
python migrate_to_supabase.py
```

This will:
1. Test connection to Supabase
2. Verify all 9 tables exist
3. Display connection status

Expected output:
```
======================================================================
SUPABASE MIGRATION SCRIPT
======================================================================

======================================================================
TESTING SUPABASE CONNECTION
======================================================================

✓ Connected to Supabase
✓ PostgreSQL Version: PostgreSQL 15.x...

======================================================================
CREATING SCHEMA
======================================================================

Creating tables...
✓ Schema created successfully

✓ Created 9 tables:
  - analytics_round_multipliers (11 columns)
  - analytics_round_outcomes (22 columns)
  - analytics_round_signals (18 columns)
  ...

======================================================================
VERIFYING SCHEMA
======================================================================

✓ bot_vm_registration (12 columns)
✓ game_platform_config (9 columns)
✓ crash_game_rounds (51 columns)
...

✓ All 9 tables verified!

======================================================================
✓ MIGRATION COMPLETED SUCCESSFULLY!
======================================================================
```

## 📊 Step 5: Start Using Your Bot with Supabase

Once schema is created and connection is verified, your bot is ready to use:

### Option A: Run the Dashboard

```bash
python run_dashboard.py
```

The dashboard will now log data to Supabase instead of CSV files.

### Option B: Run the Bot

```bash
python backend/bot.py --mode dry_run
```

The bot will log all rounds, signals, and analytics to Supabase automatically.

## 📁 Configuration Files

### `.env` (Credentials - Keep Secret!)
```
DB_HOST=zofojiubrykbtmstfhzx.supabase.co
DB_PORT=5432
DB_NAME=postgres
DB_USER=postgres
DB_PASSWORD=a5uxVcLSUpgkDMNo
DB_SSL_MODE=require

SUPABASE_URL=https://zofojiubrykbtmstfhzx.supabase.co
SUPABASE_API_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**⚠️ IMPORTANT:** This file is in `.gitignore` and should NEVER be committed to git.

### `backend/database/config.py` (Updated)
Now loads credentials from `.env`:
```python
from dotenv import load_dotenv
load_dotenv()

DB_HOST = os.getenv("DB_HOST", "...")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
```

## 🔑 Supabase Connection Details

Your Supabase project credentials:
- **Project URL:** https://zofojiubrykbtmstfhzx.supabase.co
- **Database:** postgres
- **User:** postgres
- **Host:** zofojiubrykbtmstfhzx.supabase.co
- **Port:** 5432

## 🚨 Troubleshooting

### Issue: Connection Timeout

If you see "connection to server... timeout expired":

**Solution 1: Check Network**
- Verify your internet connection is working
- Some networks (corporate, VPN) may block PostgreSQL port 5432
- Try connecting from a different network

**Solution 2: Use Supabase Web Interface**
- Use the SQL Editor in Supabase dashboard instead of Python
- This is the recommended approach if direct connections timeout

**Solution 3: Check Credentials**
- Verify `.env` file has correct credentials
- Confirm password and host are exactly right

### Issue: "ERROR: permission denied"

This usually means:
1. Credentials are incorrect
2. Supabase project isn't fully initialized yet

**Solution:**
- Wait 30 seconds after creating the Supabase project
- Double-check password in Supabase dashboard

### Issue: "table already exists"

This happens if you run the schema twice.

**Solution:**
- It's safe to ignore - tables are already created
- To reset: Go to Supabase → SQL Editor → Drop tables manually (if needed)

## 📚 Database Schema Overview

### Main Tables (3)
1. **bot_vm_registration** - Bot/VM configuration
2. **game_platform_config** - Game metadata
3. **crash_game_rounds** - Main round history (51 fields)

### Analytics Tables (3)
4. **analytics_round_multipliers** - ML training data
5. **analytics_round_signals** - Signal generation & ML features
6. **analytics_round_outcomes** - Statistics & reporting

### Supporting Tables (3)
7. **session_logs** - Session tracking
8. **error_logs** - Error debugging
9. **ocr_validation_logs** - OCR quality tracking

### Special Features
- **JSONB fields** for flexible metadata storage
- **Enum types** for data integrity
- **Indexes** for fast queries
- **Triggers** for automatic timestamp updates
- **Materialized view** for daily statistics
- **Stored procedures** for common operations

## 🔗 Next Steps

1. ✅ **Create schema** in Supabase SQL Editor (using `backend/database/schema.sql`)
2. ✅ **Test connection** with `python migrate_to_supabase.py`
3. ✅ **Start using** your bot: `python backend/bot.py`
4. ✅ **View dashboard** with real-time data: `python run_dashboard.py`
5. ✅ (Optional) **Set up backups** in Supabase dashboard
6. ✅ (Optional) **Enable Realtime** for live dashboard updates

## 📖 Documentation

- Supabase docs: https://supabase.com/docs
- PostgreSQL docs: https://www.postgresql.org/docs/
- SQLAlchemy docs: https://docs.sqlalchemy.org/

## ✨ Benefits of Using Supabase

✅ **Cloud Hosted** - No server maintenance needed
✅ **Real-time** - Built-in Realtime subscriptions available
✅ **Scalable** - Automatically scales with your needs
✅ **Secure** - SSL encryption, row-level security (RLS) available
✅ **Integrated** - Free with PostgreSQL, Auth, Storage, Realtime
✅ **Backups** - Automatic daily backups included

## 🎯 Summary

Your Aviator Bot is now configured for Supabase!

**Quick checklist:**
- [ ] Created Supabase project
- [ ] Copied schema to Supabase SQL Editor and ran it
- [ ] All 9 tables created successfully
- [ ] Ran `python migrate_to_supabase.py` and saw success message
- [ ] Ready to run bot with `python backend/bot.py`

**Happy trading! 🚀**
