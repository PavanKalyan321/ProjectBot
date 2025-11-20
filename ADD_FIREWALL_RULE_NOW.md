# Add Firewall Rule for Port 25060 - Your IP: 122.172.80.94

## Your Current IP
**IPv4:** 122.172.80.94 ✓ (Already visible in DigitalOcean!)

---

## Steps to Add Port 25060 Firewall Rule

### Step 1: Find the Firewall Section

You're currently viewing the **Networking** tab. On that same page:

1. **Look for a section that says:**
   - "Database Firewall" or "Firewall Rules" or "IP Whitelist"
   - This is different from "Trusted Sources" (which is for App Platform)

2. **If you see it:** Look for a button like **"Add Rule"**, **"Add Firewall Rule"**, or **"+ Add"**

3. **If you don't see it:**
   - Scroll down on the page (there might be more sections below)
   - Or try the **Settings** tab instead

### Step 2: Click "Add Rule" or Similar Button

When you find the firewall section, click the button to add a new rule.

### Step 3: Fill in the Rule Details

A form should appear. Fill it in like this:

```
Type/Protocol:    PostgreSQL  (or Custom TCP)
Port:             25060
Source Type:      IPv4 Address
IP Address:       122.172.80.94/32
Description:      My Machine (optional)
```

### Step 4: Save the Rule

Click **"Add Rule"**, **"Save"**, or **"Create"** button (depending on UI)

### Step 5: Wait and Test

Wait 30-60 seconds, then run:

```bash
DB_PASSWORD="your_actual_password" python c:\Project\test_connection.py
```

Should show:
```
[OK] Connection successful!
[OK] Found 9 tables (or creating them...)
```

---

## If You Can't Find the Firewall Section

### Option A: Different Tab Location
Your IP (122.172.80.94) is already in the system, so firewall config definitely exists. Try:
1. Click **Settings** tab (instead of Networking)
2. Look for **Firewall** or **Network** section
3. Add rule there

### Option B: Use SQL to Check Current Rules

Connect with superuser credentials and run:
```sql
SELECT * FROM information_schema.table_constraints
WHERE table_schema = 'public';
```

### Option C: Let DigitalOcean Auto-Allow

Since your IP (122.172.80.94) is already in their trusted sources, try:
1. Make sure user `pk` is a superuser (see PERMISSION_FIX_REQUIRED.md)
2. Try connecting immediately - it might already work
3. If not, add the explicit port 25060 rule

---

## Key Details For Reference

**Database Info:**
- Host: db-main-do-user-28557476-0.h.db.ondigitalocean.com
- Port: 25060 (THIS IS WHAT YOU'RE ADDING)
- Database: defaultdb
- User: pk
- Your IP: 122.172.80.94/32

---

## Quick Test After Adding Rule

```bash
# Test 1: Python connection
DB_PASSWORD="your_password" python c:\Project\test_connection.py

# Test 2: Initialize database (after making pk superuser)
python << 'EOF'
import os
os.environ['DB_PASSWORD'] = 'your_password'
from backend.database import init_db
init_db(drop_existing=False)
print("[OK] Tables created!")
EOF

# Test 3: Insert sample data
python c:\Project\test_database_insertion.py
```

---

## Troubleshooting

### Still Can't Find Firewall Section?
- Screenshot the Networking tab and look for any other buttons
- The section might be named: "Database Firewall", "IP Whitelist", "Port Rules", or "Allowed IPs"

### Added Rule But Still Getting Timeout?
1. Wait another 2 minutes (rules can take time to activate)
2. Edit the rule and save it again (sometimes re-triggers activation)
3. Make sure port is exactly `25060` (not `5432`)

### Getting Permission Error After Connection Works?
- See PERMISSION_FIX_REQUIRED.md
- Make user `pk` a superuser in the Users tab

---

## Summary

Your IP is ready: **122.172.80.94** ✓

Next steps:
1. Find and click "Add Firewall Rule" button
2. Enter: Port=25060, IP=122.172.80.94/32
3. Save
4. Wait 30-60 seconds
5. Test with Python script

That's it!
