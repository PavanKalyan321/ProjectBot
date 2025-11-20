# Database Permission Issue - FIX REQUIRED

## Problem Found

The user `pk` doesn't have permission to create database objects (ENUM types).

```
Error: permission denied for schema public
Failed to create type: vm_provider
```

This is a **DigitalOcean database privilege issue**.

---

## Root Cause

The user `pk` needs to be a **SUPERUSER** or have explicit **CREATE** permissions on the public schema to create custom types (ENUMs).

---

## Solution Options

### Option 1: Make `pk` a Superuser (Easiest)

**In DigitalOcean Console:**

1. Go to: https://cloud.digitalocean.com
2. Click: **Databases** → Your Database
3. Click: **Users** tab
4. Find user `pk` in the list
5. Click the **...** (menu) next to `pk`
6. Select: **Make Superuser** or **Grant Superuser Privileges**
7. Confirm

**Wait 30 seconds**, then the tables should create successfully.

---

### Option 2: Grant Specific Permissions (More Secure)

If you don't want to make `pk` a superuser, run these SQL commands:

**Connect to the database with admin credentials** (superuser), then run:

```sql
-- Grant schema creation rights
GRANT USAGE ON SCHEMA public TO pk;
GRANT CREATE ON SCHEMA public TO pk;

-- Grant type creation rights
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TYPES TO pk;

-- Grant table creation rights
GRANT CREATE ON DATABASE defaultdb TO pk;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO pk;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO pk;
```

---

## Quick Test After Fix

Once permissions are fixed, run:

```bash
DB_PASSWORD="your_actual_password" python << 'EOF'
import os
os.environ['DB_PASSWORD'] = 'your_actual_password'
from backend.database import init_db
init_db(drop_existing=False)
print("[OK] Database initialized successfully!")
EOF
```

Should show: `[OK] Database initialized successfully!`

---

## Steps in DigitalOcean Console

### Step 1: Navigate to Database
1. Open: https://cloud.digitalocean.com
2. Left sidebar: **Databases**
3. Click your database (db-main)

### Step 2: Go to Users Tab
1. Look for tabs at top: Overview | **Users** | Settings
2. Click **Users**

### Step 3: Find and Update User `pk`
1. In the users list, find row with `pk`
2. Look for status column - might say "Regular User" or similar
3. Click the **...** menu on that row
4. Select **Make Superuser**
5. Confirm the action

### Step 4: Wait
- Wait 30-60 seconds for changes to propagate

### Step 5: Test Again
- Run the Python initialization code above
- Should now work!

---

## Visual Reference

### Users Tab Layout
```
Database Users:

User        | Status           | Privileges | Menu
----------- | --------------- | ---------- | ----
root        | Superuser       | All        | ...
pk          | Regular User    | Limited    | ...  ← Click here
new_user    | Regular User    | Limited    | ...
```

Click the **...** menu next to `pk` and select "Make Superuser"

---

## Alternative: Create New Admin User

If you prefer, you can create a separate admin user:

1. In Users tab, click **Add User**
2. Name: `postgres_admin` (or similar)
3. Create the user
4. Make it a Superuser
5. Use that for table creation, use `pk` for app

But simpler to just make `pk` a superuser.

---

## After Making `pk` Superuser

All these will then work:

```bash
# 1. Initialize database
DB_PASSWORD="your_actual_password" python c:\Project\test_connection.py

# 2. Initialize tables
python << 'EOF'
import os
os.environ['DB_PASSWORD'] = 'your_actual_password'
from backend.database import init_db
init_db(drop_existing=False)
EOF

# 3. Insert test data
python c:\Project\test_database_insertion.py

# 4. Connect with DBeaver
# See: DBEAVER_SETUP.md
```

---

## Troubleshooting

### Can't Find Users Tab?
- Check **Settings** instead
- Or look for **User Management**

### Don't See "Make Superuser" Option?
- Try **Edit** instead
- Look for checkboxes or dropdown for privileges

### Still Getting Permission Error?
1. Go back to Users tab
2. Verify `pk` shows as "Superuser" (not "Regular User")
3. If not, try again - sometimes takes 2-3 minutes
4. Click Edit/Options again and confirm superuser

### Getting Different Error?
Create a support ticket at https://www.digitalocean.com/support

---

## Why This Is Needed

Your database uses PostgreSQL ENUM types for:
- `vm_provider` (vastai, runpod, digitalocean, etc.)
- `game_type` (aviator, aviatrix, jetx)
- `strategy_type` (compound_1.33x, martingale, etc.)
- `round_outcome` (WIN, LOSS, SKIP, ERROR)
- `error_type` (ocr_error, network_drop, etc.)

Creating these custom types requires superuser or schema creation privileges.

---

## Security Note

Making `pk` a superuser is fine for:
- Development environments
- Internal tools
- Single-purpose accounts

For production with multiple apps, use Option 2 (grant specific permissions instead).

---

## Quick Checklist

- [ ] Logged into DigitalOcean console
- [ ] Clicked Databases → Your Database
- [ ] Clicked Users tab
- [ ] Found user `pk` in the list
- [ ] Clicked **...** menu next to `pk`
- [ ] Selected **Make Superuser** (or equivalent)
- [ ] Waited 30-60 seconds
- [ ] Ran test command and saw success

---

## Next Steps After Permission Fix

1. Run initialization: See "Quick Test After Fix" section
2. Run local database test: `python test_database_local.py`
3. Connect with DBeaver: See DBEAVER_SETUP.md
4. Insert sample data: `python test_database_insertion.py`
5. Start logging bot data: See START_HERE.md

---

**Status:** Database connected but needs permission fix
**Action:** Make user `pk` a superuser in DigitalOcean
**Time to fix:** ~2 minutes
**Impact:** Enables full database functionality

---

Once this is fixed, everything will work!
