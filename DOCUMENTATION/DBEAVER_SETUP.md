# DBeaver Setup Guide - Connect to DigitalOcean PostgreSQL

Complete step-by-step guide to connect DBeaver to your crash game analytics database.

## Prerequisites

1. **DBeaver installed** - Download from [dbeaver.io](https://dbeaver.io/download/) (Community Edition is free)
2. **DigitalOcean PostgreSQL credentials** (from your database):
   - Host: `db-main-do-user-28557476-0.h.db.ondigitalocean.com`
   - Port: `25060`
   - Database: `defaultdb`
   - Username: `pk`
   - Password: `YOUR_PASSWORD_HERE` (Replace with actual password)
   - SSL Mode: `require`

## Step 1: Open DBeaver

Launch DBeaver and wait for it to fully load (may take a minute on first launch).

## Step 2: Create New Database Connection

1. Click **Database** menu at the top
2. Select **New Database Connection**
3. A dialog will open asking you to choose a database

## Step 3: Select PostgreSQL

In the "New Database Connection" dialog:
1. Search for or find **PostgreSQL**
2. Click on **PostgreSQL** icon
3. Click **Next**

## Step 4: Configure Connection Details

You'll see the connection configuration form. Fill in these fields:

### Main Tab Fields

| Field | Value |
|-------|-------|
| **Server Host** | `db-main-do-user-28557476-0.h.db.ondigitalocean.com` |
| **Port** | `25060` |
| **Database** | `defaultdb` |
| **Username** | `pk` |
| **Password** | Your actual DigitalOcean password |
| **Save password locally** | ☑ (Check this box) |

**Example:**
```
Server Host: db-main-do-user-28557476-0.h.db.ondigitalocean.com
Port: 25060
Database: defaultdb
Username: pk
Password: [your-password]
```

## Step 5: Disable SSH Tunnel (Important!)

**This is a common issue - make sure to do this:**

1. Click the **SSH** tab
2. **UNCHECK** "Use SSH Tunnel"
   - DigitalOcean connections don't need SSH tunneling
   - Having this checked causes "SSHJ tunnel" errors
3. Leave all other SSH settings as default

## Step 5b: Enable SSL/TLS

1. Click the **SSL** tab
2. Check **Use SSL**
3. Set **SSL Mode** to `require`
4. Leave other SSL options as default

## Step 6: Test Connection

1. Click **Test Connection** button (or **Test Connection Settings...**)
2. Wait for the test to complete

**If successful:** You'll see a "Connected" message
**If failed:** Check your credentials and network connectivity

## Step 7: Finish Setup

1. Give your connection a name like "Crash Game Analytics DB"
2. Click **Finish**
3. DBeaver will save the connection

## Step 8: Browse Your Database

Once connected:

1. In the left sidebar under **Database Connections**, expand your new connection
2. Expand **Databases** → **defaultdb**
3. Expand **Schemas** → **public**
4. You'll see all your tables:
   - `bot_vm_registration`
   - `game_platform_config`
   - `crash_game_rounds`
   - `analytics_round_multipliers` ✓
   - `analytics_round_signals` ✓
   - `analytics_round_outcomes` ✓
   - `error_logs`
   - `ocr_validation_logs`
   - `session_logs`

## Common Tasks in DBeaver

### View Table Data

1. Right-click any table
2. Select **View Data**
3. Browse rows in the result panel

### Run SQL Queries

1. Click **SQL Editor** → **New SQL Script**
2. Write your SQL query:
   ```sql
   SELECT * FROM crash_game_rounds LIMIT 10;
   ```
3. Press **Ctrl+Enter** or click Execute

### View Table Schema

1. Click a table name
2. Click the **DDL** tab to see CREATE TABLE statement
3. Click **Columns** tab to see field definitions

### Export Data

1. Right-click table
2. **Export Data** → Choose format (CSV, JSON, SQL, etc.)
3. Follow export wizard

## Example Queries

### View All Bot Statistics
```sql
SELECT
    bot_id,
    COUNT(*) as total_rounds,
    SUM(CASE WHEN round_outcome = 'WIN' THEN 1 ELSE 0 END) as wins,
    ROUND(100.0 * SUM(CASE WHEN round_outcome = 'WIN' THEN 1 ELSE 0 END) /
          COUNT(*), 2) as win_rate_percent,
    SUM(profit_loss_amount) as total_profit
FROM crash_game_rounds
GROUP BY bot_id;
```

### View Analytics Data (Table 1 - Multipliers)
```sql
SELECT
    round_id,
    multiplier,
    timestamp,
    bot_id,
    game_name,
    ocr_confidence,
    data_quality_score
FROM analytics_round_multipliers
ORDER BY timestamp DESC
LIMIT 20;
```

### View Signals (Table 2)
```sql
SELECT
    round_id,
    signal_type,
    confidence_score,
    signal_strength,
    pattern_match_type,
    feature_vector,
    timestamp
FROM analytics_round_signals
ORDER BY timestamp DESC;
```

### View Outcomes (Table 3)
```sql
SELECT
    round_id,
    outcome,
    profit_loss,
    roi_percent,
    strategy_name,
    hit_target,
    win_streak_length,
    outcome_category
FROM analytics_round_outcomes
ORDER BY timestamp DESC;
```

### Session Summary
```sql
SELECT
    session_id,
    bot_id,
    game_name,
    initial_balance,
    final_balance,
    (final_balance - initial_balance) as profit_loss,
    ROUND(100.0 * (final_balance - initial_balance) / initial_balance, 2) as roi_percent,
    status,
    start_time,
    end_time
FROM session_logs
ORDER BY start_time DESC;
```

## ⚠️ Common Issues & Quick Fixes

### SSH Tunnel Error - "Error establishing SSHJ tunnel"

**Quick Fix:**
1. Go to **SSH** tab in connection settings
2. **UNCHECK** "Use SSH Tunnel"
3. Click **Test Connection** again

✓ This solves 95% of connection issues!

**Why?** DigitalOcean PostgreSQL doesn't need SSH tunneling. Having it enabled causes timeout errors.

For detailed troubleshooting, see [DBEAVER_TROUBLESHOOTING.md](DBEAVER_TROUBLESHOOTING.md)

---

## Troubleshooting

### Connection Timeout / SSHJ Tunnel Error
**Problem:** "Connect timed out" or "Error establishing SSHJ tunnel"

**Quick Fix:**
1. SSH Tab: **UNCHECK** "Use SSH Tunnel" ← This is usually the fix
2. SSL Tab: **CHECK** "Use SSL" with Mode = `require`
3. Test again

**Detailed Help:** See [DBEAVER_TROUBLESHOOTING.md](DBEAVER_TROUBLESHOOTING.md#ssh-tunnel-error---error-establishing-sshj-tunnel)

### SSL/TLS Errors
**Problem:** "SSL error" or "certificate verify failed"

**Solutions:**
1. Ensure SSL Mode is set to `require` (not `disable`)
2. Try setting **SSL Mode** to `prefer` instead
3. Uncheck **Validate Server Certificate** if testing locally
4. Download DigitalOcean CA certificate and add it

**Full guide:** See [DBEAVER_TROUBLESHOOTING.md](DBEAVER_TROUBLESHOOTING.md#ssl-error-certificate-verify-failed)

### Authentication Failed
**Problem:** "Authentication failed" or "role pk does not exist"

**Solutions:**
1. Verify username is exactly `pk` (case-sensitive)
2. Verify password is correct
3. Check for leading/trailing spaces in credentials
4. Try resetting password in DigitalOcean console

### Database Not Found
**Problem:** "Database defaultdb does not exist"

**Solutions:**
1. Verify database name is exactly `defaultdb`
2. In DigitalOcean console, verify the database exists
3. Try connecting without specifying database (leave blank), then select it after connecting

## Advanced Features

### Create Saved Queries

1. Open SQL Editor
2. Write your query
3. Press **Ctrl+S** to save
4. Name it (e.g., "Bot Statistics")
5. Access saved queries from left sidebar

### View Query Execution Plan

1. Write SQL query
2. Click **Explain** button or press **Ctrl+Alt+E**
3. View execution plan to optimize slow queries

### Monitor Database Activity

1. Right-click connection
2. **Server** → **Session Manager**
3. See all active sessions and queries

### Backup Data

1. Right-click database
2. **Tools** → **Backup**
3. Select tables to backup
4. Choose backup location

## Next Steps

1. ✓ Connect to database with DBeaver
2. Browse the 9 tables with sample data
3. Run the example queries above
4. Verify all analytics tables have data
5. Integrate database credentials into your bot code
6. Start logging real rounds

## Connection String (for reference)

If you need to use the connection string format:

```
postgresql://pk:YOUR_PASSWORD_HERE@db-main-do-user-28557476-0.h.db.ondigitalocean.com:25060/defaultdb?sslmode=require
```

---

**Status:** Ready to use with DBeaver

**Database:** 9 tables with sample data verified

**Next:** Open DBeaver and follow Step 1 above →
