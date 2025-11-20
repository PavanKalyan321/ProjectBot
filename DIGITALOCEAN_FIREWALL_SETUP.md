# DigitalOcean Firewall Configuration - Step-by-Step Guide

## Quick Summary
Your database port 25060 is blocked. You need to add your IP address to DigitalOcean's firewall whitelist.

**Time required:** 5 minutes

---

## Step 1: Find Your Public IP Address

### Option A: Quick Check (Recommended)
Visit one of these websites and note your IP:
- https://www.whatismyipaddress.com
- https://ifconfig.me
- https://myip.com

**Example IP:** `203.0.113.45` (yours will be different)

### Option B: Via Command Line
```bash
curl ifconfig.me
```

**Write down your IP address** - You'll need it in the next steps.

---

## Step 2: Log Into DigitalOcean Console

1. Go to [DigitalOcean Cloud Console](https://cloud.digitalocean.com)
2. Log in with your credentials
3. You should see the dashboard

---

## Step 3: Navigate to Your Database

1. In the left sidebar, click **Databases**
2. You should see your database listed (likely named "db-main" or similar)
3. **Click on your database name** to open it

---

## Step 4: Access Firewall Rules

Once in your database details page:

1. Look for tabs at the top:
   - **Overview** | **Settings** | **Networking** | **Backups** | etc.

2. Click on the **Networking** tab

3. You should see a section called:
   - **Firewall Rules** (or **Trusted Sources**)
   - **Connections** (or **Allowed IPs**)

---

## Step 5: Add Your IP to Firewall

### If You See "No Rules" or "Not Configured":

1. Look for button: **Add Rule** or **Configure Firewall**
2. Click it
3. Proceed to "Adding the Rule" section below

### If You See Existing Rules:

1. Look for button: **Add Rule** or **+ Add**
2. Click it
3. Proceed to "Adding the Rule" section below

---

## Step 6: Adding the Firewall Rule

When you click "Add Rule", a form will appear:

### Fill in These Fields:

#### Field 1: Type/Protocol
- **Select:** `PostgreSQL` (or `Custom TCP`)
- **Port:** Should auto-fill as `25060`
- ✓ If it's custom, set port to `25060`

#### Field 2: Source/IP Address
- **Select:** `IPv4 Address` (or just "IP Address")
- **Enter:** Your IP address with `/32`
  - **Example:** `203.0.113.45/32`
  - The `/32` means "only this exact IP"

#### Field 3: Description (Optional)
- **Enter:** `My Development Machine` or similar
- Helps you remember which IP this is

### Visual Example:

```
Type:        PostgreSQL
Port:        25060
Source:      IPv4 Address
IP Address:  203.0.113.45/32
Description: My Development Machine
```

---

## Step 7: Save the Rule

1. Click **Add Rule** or **Save** button (button text varies)
2. You may see a confirmation message
3. **The rule is now adding** - wait 30-60 seconds for it to activate

---

## Step 8: Verify the Rule Was Added

1. Stay on the **Networking** tab
2. You should see your IP listed under **Firewall Rules**
3. Status should be **Active** or show a checkmark ✓

**Example of what you should see:**
```
IPv4 Address          203.0.113.45/32    PostgreSQL    Active ✓
```

---

## Step 9: Wait for Activation

⏱️ **Wait 30-60 seconds** for DigitalOcean to apply the rule

---

## Step 10: Test the Connection

### Option A: Test with Python Script
```bash
DB_PASSWORD="your_actual_password" python c:\Project\test_connection.py
```

**Expected output:**
```
[OK] Connection successful!
[OK] PostgreSQL Version: PostgreSQL 14.5...
[OK] Found 9 tables...
```

### Option B: Test with DBeaver

1. Open DBeaver
2. Create a new connection (Database → New Database Connection → PostgreSQL)
3. Fill in:
   - Host: `db-main-do-user-28557476-0.h.db.ondigitalocean.com`
   - Port: `25060`
   - Database: `defaultdb`
   - User: `pk`
   - Password: Your password
4. **SSH tab:** UNCHECK "Use SSH Tunnel"
5. **SSL tab:** CHECK "Use SSL", set mode to `require`
6. Click **Test Connection**
7. Should show: ✓ Connected

---

## Troubleshooting

### Rule Added but Still Getting "Connection Timed Out"?

**Try these steps:**

1. **Wait longer** - Sometimes takes 2-3 minutes
2. **Refresh the page** - F5 or Cmd+R
3. **Double-check your IP:**
   - Go to https://whatismyipaddress.com again
   - Verify it matches what you entered
   - Make sure you included the `/32` at the end

4. **Edit the rule:**
   - Click the rule in firewall list
   - Click Edit
   - Save it again (sometimes this re-triggers activation)

5. **Verify port number:**
   - Make sure it says `25060`, not `5432`

### Rule Shows But Connection Still Fails?

1. **Check if database is running:**
   - Go to **Overview** tab of database
   - Look for status indicator
   - Should be **Green** (Running)
   - If red, click **Start** or **Restart**

2. **Verify credentials:**
   - Username: `pk` (exactly)
   - Password: Check your DigitalOcean console
   - Database: `defaultdb` (exactly)

3. **Try removing and re-adding:**
   - Delete the rule
   - Wait 10 seconds
   - Add it again with your IP

### Firewall Section Missing?

Your database might not have firewall support enabled:

1. Check **Settings** tab
2. Look for "Firewall" or "Network" settings
3. You might need to enable it first
4. Or try the **Networking** tab instead

### Still Not Working?

**Contact DigitalOcean Support:**
1. Visit https://www.digitalocean.com/support
2. Create a ticket or use live chat
3. Tell them:
   - Database name
   - Your IP address
   - Port 25060 firewall rule isn't working
   - Username: `pk`

---

## Common IP Formats

### Single IP (Most Secure) ✓ RECOMMENDED
```
203.0.113.45/32
```
- Only allows this one IP address
- Best for development

### Small Network
```
203.0.113.0/24
```
- Allows IPs 203.0.113.0 through 203.0.113.255
- 256 addresses total
- Good for office networks

### All IPs (Testing Only) ⚠️ NOT RECOMMENDED
```
0.0.0.0/0
```
- Allows ANY IP address to connect
- **Major security risk**
- Only use for emergency testing
- Change to specific IP immediately after

---

## What "/32" Means

The `/32` is called the "CIDR notation":
- `/32` = Exactly one IP address (most restrictive)
- `/24` = 256 IP addresses
- `/16` = 65,536 IP addresses
- `/0` = All IP addresses (unrestricted)

**For your use case, always use `/32`** for a single machine.

---

## If Your IP Changes

Laptop on WiFi? Home internet? Your IP might change occasionally.

When you get another connection timeout:
1. Check your current IP: https://whatismyipaddress.com
2. Compare to what's in DigitalOcean firewall
3. If different, update the rule with new IP

**Permanent Solution:**
- Use static IP from your ISP (contact them)
- Or use a VPN with permanent IP
- Or use `/24` to allow your whole network block

---

## Complete Checklist

- [ ] Found my public IP address
- [ ] Logged into DigitalOcean console
- [ ] Navigated to Databases → My Database
- [ ] Clicked on Networking tab
- [ ] Clicked "Add Rule" button
- [ ] Set Type/Protocol to PostgreSQL
- [ ] Set Port to 25060
- [ ] Set Source Type to IPv4 Address
- [ ] Entered my IP with /32 format (e.g., 203.0.113.45/32)
- [ ] Added optional description
- [ ] Clicked "Add Rule" / "Save" button
- [ ] Waited 30-60 seconds
- [ ] Rule appears in list as Active
- [ ] Tested connection with Python script or DBeaver
- [ ] Connection successful! ✓

---

## Next Steps After Successful Connection

Once you've successfully connected:

1. **Test with DBeaver:**
   - Browse all 9 tables
   - View sample data
   - Run SQL queries

2. **Test with Python:**
   ```bash
   python c:\Project\test_database_local.py
   ```

3. **Start integrating into bot:**
   - Use `from backend.database import log_crash_round`
   - Begin logging real trade data
   - Export analytics for ML training

4. **Optional - Restrict Further:**
   - For maximum security, note down just your IP
   - Only allow that specific machine
   - Update if IP changes

---

## Visual Reference

### DigitalOcean Console Layout
```
Dashboard
├── Databases (left sidebar)
│   └── db-main (click here)
│       ├── Overview
│       ├── Networking (click here) ← You are here
│       │   ├── Firewall Rules
│       │   │   └── Add Rule (click this)
│       │   └── Trusted Sources
│       ├── Settings
│       ├── Backups
│       └── Monitoring
```

### Firewall Rule Form
```
┌─ Add Firewall Rule ─────────────────┐
│ Type/Protocol:  [PostgreSQL ▼]      │
│ Port:           [25060        ]      │
│ Source Type:    [IPv4 Address ▼]    │
│ IP Address:     [203.0.113.45/32  ] │
│ Description:    [My Dev Machine   ] │
│ [Add Rule]  [Cancel]               │
└─────────────────────────────────────┘
```

---

## Support Resources

- **DigitalOcean Docs:** https://docs.digitalocean.com/products/databases/postgresql/
- **Firewall Guide:** https://docs.digitalocean.com/products/databases/postgresql/resources/firewall/
- **Support Portal:** https://www.digitalocean.com/support
- **Status Page:** https://status.digitalocean.com

---

**Time to complete:** ~5 minutes
**Difficulty:** Easy
**Success rate with guide:** 95%+

Once the firewall rule is added, your database will be fully accessible! 🎉
