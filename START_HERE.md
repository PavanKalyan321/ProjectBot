# 🚀 Quick Start - Run the System Now!

## Step 1: Start Backend Server

Open a terminal and run:

```bash
cd c:\Project
python run_dashboard.py --port 5001
```

You should see:
```
✓ Dashboard running at http://localhost:5001
```

## Step 2: Start Frontend Server

Open a new terminal and run:

```bash
cd c:\Project\dashboard-nextjs
npm run dev
```

You should see:
```
▲ Next.js 14.x
- Local:        http://localhost:3000
```

## Step 3: Open Dashboard

```
http://localhost:3000
```

## Step 4: Enable Demo Mode

Click the **"🎮 Demo OFF"** button (it will turn blue)

## Step 5: Watch Console (F12)

Open browser console and you'll see:

```
🔍 Dashboard: Starting iframe multiplier extraction...
✅ Round created: 123
📊 Extracted: 1.05x via regex (85%)
💾 Multiplier 1.05x logged: 456
📊 Extracted: 1.23x via regex (85%)
💾 Multiplier 1.23x logged: 457
🏁 Round ended at 1.89x
```

---

## What's Happening

1. Demo mode simulates game rounds
2. Iframe extraction extracts multiplier values
3. Automatic database logging saves all values
4. Real-time console shows extraction & logging

---

## Verification Checklist

✅ Backend running on port 5001
✅ Frontend running on port 3000
✅ Dashboard loads without errors
✅ Demo mode button toggles
✅ Console shows extraction messages
✅ Multiplier values appear in console
✅ Database records are created

---

## That's It!

The system is now running and extracting multipliers from the iframe in real-time! 🎉

See README_IFRAME_EXTRACTION.md for more details.
