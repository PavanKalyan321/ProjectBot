# DBeaver Troubleshooting Guide

## SSH Tunnel Error - "Error establishing SSHJ tunnel"

### Problem
When connecting to DigitalOcean PostgreSQL, you get:
```
Error initializing tunnel
Error establishing SSHJ tunnel
Connect timed out
```

### Root Cause
DBeaver is trying to create an SSH tunnel to connect to the database, but:
1. SSH connection is not configured or unavailable
2. You don't have SSH credentials for the database server
3. SSH tunnel settings are enabled when they shouldn't be

### Solution

#### Option 1: Direct Connection (Recommended)

**Step 1: Go to SSH Tab**
1. In the connection settings dialog
2. Click the **SSH** tab
3. **UNCHECK** "Use SSH Tunnel" checkbox
4. Click **OK** or **Apply**

**Step 2: SSL/TLS Settings Only**
1. Click the **SSL** tab
2. **CHECK** "Use SSL"
3. Set **SSL Mode** to `require`
4. Leave other SSL options as default

**Step 3: Test Connection**
1. Click **Test Connection** button
2. Wait for result

This should now work directly without SSH tunneling.

---

#### Option 2: If You Still Get SSL Errors

If you get SSL certificate errors after disabling SSH:

**Step 1: Disable SSL Verification (for testing)**
1. Go to **SSL** tab
2. Check **Use SSL**
3. Set **SSL Mode** to `prefer` (instead of `require`)
4. **UNCHECK** "Validate Server Certificate"
5. Test connection

**Step 2: If that works, enable SSL properly**
1. Set **SSL Mode** back to `require`
2. Check "Validate Server Certificate"
3. DigitalOcean's SSL should now work

---

#### Option 3: Complete Fresh Connection

If the above doesn't work, delete and recreate the connection:

**Step 1: Remove Old Connection**
1. In DBeaver left sidebar, find your connection
2. Right-click the connection name
3. Select **Delete**
4. Confirm deletion

**Step 2: Create New Connection**
1. **Database** → **New Database Connection**
2. Select **PostgreSQL**
3. Click **Next**

**Step 3: Fill Connection Details**

| Field | Value |
|-------|-------|
| Server Host | `db-main-do-user-28557476-0.h.db.ondigitalocean.com` |
| Port | `25060` |
| Database | `defaultdb` |
| Username | `pk` |
| Password | Your actual password |
| Save password locally | ✓ Checked |

**Step 4: SSH Tab**
- **LEAVE "Use SSH Tunnel" UNCHECKED**

**Step 5: SSL Tab**
- Check "Use SSL"
- SSL Mode: `require`

**Step 6: Test Connection**
- Click **Test Connection**
- Should succeed

---

## Connection Troubleshooting Checklist

### Basic Connectivity

- [ ] Internet connection is working
- [ ] Port 25060 is not blocked by firewall
- [ ] DigitalOcean database is running (check in DigitalOcean console)
- [ ] Database hasn't been deleted/reset

### Credentials

- [ ] Username: exactly `pk` (case-sensitive, no spaces)
- [ ] Password: correct and exactly as in DigitalOcean
- [ ] Database: exactly `defaultdb` (no spaces)
- [ ] Host: exactly `db-main-do-user-28557476-0.h.db.ondigitalocean.com`
- [ ] Port: exactly `25060` (not 5432)

### DBeaver Settings

- [ ] **SSH Tab:** "Use SSH Tunnel" is UNCHECKED
- [ ] **SSL Tab:** "Use SSL" is CHECKED
- [ ] **SSL Tab:** SSL Mode is `require`
- [ ] No proxy settings interfering
- [ ] No special characters in password causing issues

---

## Common Error Messages & Solutions

### "Connect timed out"
**Possible causes:**
- Wrong host or port
- Firewall blocking port 25060
- Database server down
- Network issue

**Solutions:**
1. Verify host: `db-main-do-user-28557476-0.h.db.ondigitalocean.com`
2. Verify port: `25060`
3. Check DigitalOcean console if database is running
4. Check your internet connection

### "Authentication failed"
**Possible causes:**
- Wrong password
- Wrong username
- Password with special characters not escaped

**Solutions:**
1. Copy password from DigitalOcean console carefully
2. Verify username is `pk`
3. If password has special characters, try copying again
4. Reset password in DigitalOcean console

### "SSL error: certificate verify failed"
**Possible causes:**
- DigitalOcean's SSL certificate issue
- Certificate validation too strict
- Outdated certificate bundle

**Solutions:**
1. Uncheck "Validate Server Certificate" for testing
2. Try SSL Mode `prefer` instead of `require`
3. Update DBeaver to latest version
4. Check if DigitalOcean has SSL certificate installed

### "Database does not exist"
**Possible causes:**
- Wrong database name
- Database not created yet
- Database was deleted

**Solutions:**
1. Verify database name is `defaultdb`
2. Check DigitalOcean console for database list
3. Database may need to be created if new account

### "Role does not exist"
**Possible causes:**
- Wrong username
- User not created yet
- User was deleted

**Solutions:**
1. Verify username is `pk`
2. Check DigitalOcean console under Users
3. Create user if missing

---

## Network Debugging

### Test Connection from Command Line

If DBeaver can't connect, test with command line first:

**Windows - Test connection exists:**
```cmd
ping db-main-do-user-28557476-0.h.db.ondigitalocean.com
```

**Windows - Test port open:**
```cmd
Test-NetConnection -ComputerName db-main-do-user-28557476-0.h.db.ondigitalocean.com -Port 25060
```

**Test with psql (if installed):**
```cmd
psql -h db-main-do-user-28557476-0.h.db.ondigitalocean.com -p 25060 -U pk -d defaultdb
```

### Firewall Check

- [ ] Windows Firewall allows outbound on port 25060
- [ ] Corporate/network firewall allows outbound on port 25060
- [ ] VPN not interfering (if using one)

---

## DBeaver Advanced Settings

If you've tried everything above, try these advanced settings:

### Connection Properties Tab

1. Click **Connection Settings** (gear icon)
2. Scroll to **Advanced** section
3. Try these properties:

| Property | Value | Purpose |
|----------|-------|---------|
| `tcpKeepAlives` | `true` | Keep connection alive |
| `connectTimeout` | `30` | Increase timeout to 30 seconds |
| `socketTimeout` | `30` | Increase socket timeout |

### Test again after each change.

---

## Still Not Working?

### Verify Database Exists

1. Log into [DigitalOcean Console](https://cloud.digitalocean.com)
2. Go to **Databases**
3. Click your database
4. Verify:
   - [ ] Database is "Running" (green status)
   - [ ] Host: `db-main-do-user-28557476-0.h.db.ondigitalocean.com`
   - [ ] Port: `25060`
   - [ ] User `pk` exists under **Users** tab
   - [ ] Database `defaultdb` exists under **Databases** tab

### Update DBeaver

1. DBeaver → **Help** → **Check for Updates**
2. Install latest version
3. Restart DBeaver
4. Try connection again

### Test with Alternative Tools

If DBeaver still fails, test with other tools to isolate the issue:

**Using pgAdmin (Web-based):**
- Create free account at [pgAdmin.org](https://www.pgadmin.org)
- Add connection with same credentials
- If pgAdmin works, it's DBeaver-specific

**Using Python:**
```python
import psycopg2

try:
    conn = psycopg2.connect(
        host="db-main-do-user-28557476-0.h.db.ondigitalocean.com",
        port=25060,
        database="defaultdb",
        user="pk",
        password="YOUR_PASSWORD_HERE",
        sslmode="require"
    )
    print("Connection successful!")
    conn.close()
except Exception as e:
    print(f"Connection failed: {e}")
```

---

## SSH Tunnel Setup (Optional)

If you actually NEED SSH tunnel access:

### Prerequisites
- [ ] SSH key pair (public + private key)
- [ ] SSH access to a bastion host
- [ ] DigitalOcean Droplet or other SSH server

### DBeaver SSH Configuration

1. In connection settings, **SSH** tab
2. Check "Use SSH Tunnel"
3. Fill in:
   - **SSH Host:** Your bastion server IP/hostname
   - **SSH Port:** Usually `22`
   - **SSH Username:** Your SSH username
   - **SSH Authentication:**
     - Use **Public Key** method
     - Upload your private key file
4. Test connection

**Note:** Most people don't need this for direct DigitalOcean PostgreSQL connections. Only use if you have a specific reason.

---

## Quick Summary

**99% of connection issues are solved by:**

1. ✓ UNCHECK "Use SSH Tunnel" in SSH tab
2. ✓ CHECK "Use SSL" in SSL tab
3. ✓ Set SSL Mode to `require`
4. ✓ Verify credentials are exactly correct
5. ✓ Click Test Connection

Try this first before anything else!

---

## Contact & Support

If you've gone through this entire guide and still have issues:

1. Check DigitalOcean status page for service alerts
2. Verify database is running in DigitalOcean console
3. Try resetting the database password
4. Contact DigitalOcean support with error message

---

**Last Updated:** November 21, 2025
**Status:** Updated with common solutions
