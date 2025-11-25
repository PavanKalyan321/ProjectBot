# DBeaver Quick Fix - SSH Tunnel Error

## Problem You're Seeing
```
Error initializing tunnel
Error establishing SSHJ tunnel
Connect timed out
```

## The Fix (2 Steps)

### Step 1: Disable SSH Tunnel ← THIS IS THE KEY

1. In DBeaver connection settings dialog
2. Click the **SSH** tab
3. **UNCHECK** the box next to "Use SSH Tunnel"
4. Click **OK** or **Apply**

### Step 2: Enable SSL

1. Click the **SSL** tab
2. **CHECK** "Use SSL"
3. Set SSL Mode to `require`
4. Click **OK**

### Step 3: Test Connection
- Click **Test Connection** button
- ✓ Should work now!

---

## Why This Works

**The Problem:** DBeaver was trying to create an SSH tunnel, which:
- Times out (SSH connection blocked or unavailable)
- Isn't needed for DigitalOcean PostgreSQL
- Only needed if you're connecting through a bastion host

**The Solution:** Use direct SSL connection instead (DigitalOcean supports this)

---

## If That Doesn't Work

See [DBEAVER_TROUBLESHOOTING.md](DBEAVER_TROUBLESHOOTING.md) for:
- SSL certificate errors
- Authentication failures
- Network debugging
- Alternative connection methods

---

**TL;DR:** Uncheck SSH Tunnel, enable SSL, test again ✓
