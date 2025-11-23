# Next.js Dashboard Setup Guide

Complete setup instructions for the Aviator Bot Next.js Dashboard with 2-iframe layout.

## Overview

The dashboard consists of two main components:

- **Left Iframe**: Bot controller with game status and manual controls
- **Right Iframe**: Analytics panel with ML predictions and statistics

Both communicate with the existing Flask backend via REST APIs and WebSocket (Socket.IO).

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│  Browser (http://localhost:3000)                        │
│  ┌──────────────────────┬────────────────────────────┐  │
│  │  LEFT IFRAME         │  RIGHT IFRAME              │  │
│  │  Bot Controller      │  Analytics & Predictions   │  │
│  │                      │                            │  │
│  │  - Multiplier        │  - 16 Models Grid          │  │
│  │  - Controls          │  - Ensemble Prediction     │  │
│  │  - Stake Input       │  - Trend & Signal          │  │
│  │  - Bet Actions       │  - Live Stats              │  │
│  └──────────────────────┴────────────────────────────┘  │
│         ↓ REST API Calls                                 │
│         ↓ Socket.IO Connection                          │
└─────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────┐
│  Flask Backend (http://localhost:5001)                  │
│  - REST API Endpoints                                   │
│  - Socket.IO Server                                     │
│  - Data Processing                                      │
│  - ML Model Management                                  │
└─────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────┐
│  Data Sources                                           │
│  - CSV Files (aviator_rounds_history.csv, etc.)        │
│  - Supabase PostgreSQL Database                        │
└─────────────────────────────────────────────────────────┘
```

## Installation Steps

### Step 1: Install Node.js (if not already installed)

Download from: https://nodejs.org/en/
- Recommended: LTS version (18+)
- Verify installation:
  ```bash
  node --version
  npm --version
  ```

### Step 2: Install Dashboard Dependencies

```bash
cd c:\Project\dashboard-nextjs
npm install
```

Expected output:
```
added 500+ packages
```

### Step 3: Configure Environment Variables

Edit `c:\Project\dashboard-nextjs\.env.local`:

```env
# API Configuration
NEXT_PUBLIC_API_URL=http://localhost:5001
NEXT_PUBLIC_SOCKET_URL=http://localhost:5001

# App Configuration
NEXT_PUBLIC_APP_NAME=Aviator Bot Dashboard
NEXT_PUBLIC_REFRESH_INTERVAL=1000
```

**For Production:**
Replace localhost with your actual server URL:
```env
NEXT_PUBLIC_API_URL=https://your-server.com
NEXT_PUBLIC_SOCKET_URL=https://your-server.com
```

### Step 4: Verify Flask Backend is Running

The Next.js dashboard requires the Flask backend to be running:

```bash
# Terminal 1 - Backend
cd c:\Project
python run_dashboard.py --port 5001
```

Expected output:
```
* Running on http://localhost:5001
* Debugger PIN: ...
```

### Step 5: Start Next.js Development Server

```bash
# Terminal 2 - Frontend
cd c:\Project\dashboard-nextjs
npm run dev
```

Expected output:
```
  ▲ Next.js 14.0.0
  - Local:        http://localhost:3000
  - Network:      http://192.168.x.x:3000
```

### Step 6: Open Dashboard in Browser

Navigate to: http://localhost:3000

You should see:
- Split-screen layout with 2 iframes
- Left panel: Bot controller
- Right panel: Analytics
- Connection status indicator (green = connected)

## Usage Guide

### Left Iframe (Bot Controller)

**Display Section:**
- Current multiplier in large font
- Game status badge (AWAITING / RUNNING / CRASHED)
- Placeholder for Aviator game embed (optional)

**Controls Section:**
- **Stake Amount**: Enter bet amount ($)
- **Target Multiplier**: Enter cashout multiplier (e.g., 2.0)
- **Place Bet / Cancel Bet**: Place bet or cancel current bet
- **Pause / Resume**: Control bot operation

### Right Iframe (Analytics)

**Current Round Section:**
- Actual multiplier
- Ensemble prediction with confidence

**Trend & Signal Section:**
- Trend indicator (↑ UP, ↓ DOWN, → NEUTRAL)
- Trading signal badge (BET / SKIP / CAUTIOUS / OPPORTUNITY / WAIT)

**Statistics Section:**
- Win rate percentage
- Profit/Loss amount
- Total rounds played

**Models Section:**
- Top 3 performing models
- Model names and confidence scores

**Chart Section:**
- Line chart of last 10 rounds
- Shows prediction vs. actual multiplier
- Helps identify patterns

## Project Structure

```
c:\Project\
├── dashboard-nextjs/                   (NEW - Next.js app)
│   ├── src/
│   │   ├── app/
│   │   │   ├── layout.tsx             (Root layout)
│   │   │   └── page.tsx               (Home page)
│   │   ├── components/
│   │   │   ├── Dashboard.tsx          (Main layout with 2 iframes)
│   │   │   ├── LeftIframe.tsx         (Bot controller)
│   │   │   └── RightIframe.tsx        (Analytics panel)
│   │   ├── lib/
│   │   │   ├── api.ts                 (REST API client)
│   │   │   └── socket.ts              (Socket.IO client)
│   │   └── styles/
│   │       └── globals.css            (Global styles)
│   ├── public/                         (Static assets)
│   ├── package.json
│   ├── tsconfig.json
│   ├── tailwind.config.ts
│   ├── postcss.config.js
│   ├── next.config.ts
│   ├── .env.local                      (Environment variables)
│   ├── .gitignore
│   └── README.md
│
├── backend/                            (Existing - Python/Flask)
│   ├── dashboard/
│   │   ├── compact_analytics.py        (Flask API endpoints)
│   │   └── templates/
│   │       └── compact_dashboard.html  (Original dashboard)
│   ├── database/
│   │   └── models.py                   (Supabase models)
│   └── bot.py                          (Bot logic)
│
├── run_dashboard.py                    (Flask entry point)
└── NEXTJS_DASHBOARD_SETUP.md           (This file)
```

## API Integration

The Next.js dashboard communicates with Flask via:

### REST APIs (for data fetching)

**1. Get Current Round Predictions**
```
GET /api/current_round

Response:
{
  "round_id": "12345",
  "actual_multiplier": 2.45,
  "ensemble_prediction": 2.38,
  "ensemble_confidence": 82,
  "models": [
    {"model_id": "m1", "name": "LightGBM", "prediction": 2.4, "confidence": 85},
    ...
  ],
  "trend": "UP",
  "signal": "BET",
  "target_multiplier": 2.0
}
```

**2. Get Live Statistics**
```
GET /api/live_stats

Response:
{
  "total_rounds": 156,
  "win_rate": 67.5,
  "profit_loss": 245.80,
  "current_streak": "WIN",
  "average_confidence": 78.5,
  "last_updated": "2025-11-23T10:30:45Z"
}
```

**3. Get Recent Rounds**
```
GET /api/recent_rounds?limit=20

Response:
[
  {
    "round_id": "12345",
    "timestamp": "2025-11-23T10:30:45Z",
    "actual_multiplier": 2.45,
    "prediction": 2.38,
    "confidence": 82,
    "result": "WIN"
  },
  ...
]
```

### WebSocket Events (for real-time updates)

**Client connects:**
```javascript
socket.on('connect', () => {
  // Connected to server
});
```

**Receive live updates:**
```javascript
socket.on('live_update', (data) => {
  // New round data
  // Update UI with latest predictions
});
```

**Receive stats updates:**
```javascript
socket.on('stats_update', (data) => {
  // Updated statistics
  // Update win rate, P/L, etc.
});
```

**Request update:**
```javascript
socket.emit('request_update');
```

## Customization

### Change Port Numbers

To run on different ports:

**For Flask:**
```bash
python run_dashboard.py --port 8000
```

**For Next.js:**
```bash
npm run dev -- -p 3001
```

Then update `.env.local`:
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_SOCKET_URL=http://localhost:8000
```

### Customize Colors

Edit `src/styles/globals.css` or `tailwind.config.ts`:

```typescript
theme: {
  extend: {
    colors: {
      'dark': '#0f172a',
      'darker': '#020617',
      // Add your colors here
    },
  },
}
```

### Adjust Refresh Rate

Edit `.env.local`:
```env
NEXT_PUBLIC_REFRESH_INTERVAL=3000  # 3 seconds instead of 1
```

### Add More Models to Display

Edit `src/components/RightIframe.tsx`:
```typescript
// Show top 5 instead of 3
const topModels = useMemo(() => {
  return [...models]
    .sort((a, b) => b.confidence - a.confidence)
    .slice(0, 5);  // Changed from 3 to 5
}, [models]);
```

## Production Deployment

### Option 1: Deploy to Vercel (Recommended)

1. **Install Vercel CLI:**
   ```bash
   npm install -g vercel
   ```

2. **Deploy:**
   ```bash
   cd c:\Project\dashboard-nextjs
   vercel
   ```

3. **Configure environment variables in Vercel dashboard:**
   - Add `NEXT_PUBLIC_API_URL`
   - Add `NEXT_PUBLIC_SOCKET_URL`
   - Point to your production Flask server

### Option 2: Build and Host

1. **Build:**
   ```bash
   npm run build
   ```

2. **Start production server:**
   ```bash
   npm start
   ```

3. **Keep Flask running:**
   ```bash
   python run_dashboard.py --port 5001
   ```

## Troubleshooting

### Issue: Dashboard shows "Loading..." indefinitely

**Causes:**
- Flask backend not running
- Wrong API URL in .env.local
- CORS issues

**Solutions:**
```bash
# Check Flask is running
# Terminal 1:
python run_dashboard.py --port 5001

# Check .env.local has correct URLs
cat c:\Project\dashboard-nextjs\.env.local

# Check browser console for errors (F12)
```

### Issue: Connection shows "Disconnected" (red)

**Causes:**
- Socket.IO connection failed
- Port 5001 not accessible
- Firewall blocking connection

**Solutions:**
```bash
# Verify Flask endpoint is accessible
curl http://localhost:5001/api/live_stats

# Check firewall allows port 5001
# Windows: netstat -an | findstr 5001

# Restart Flask with CORS enabled
python run_dashboard.py --port 5001
```

### Issue: Models not showing data

**Causes:**
- CSV files not available
- No rounds played yet
- API endpoint returns empty

**Solutions:**
```bash
# Check CSV files exist
ls c:\Project\backend\aviator_rounds_history.csv

# Check API response
curl http://localhost:5001/api/model_comparison

# Wait for first round to complete
# Give bot time to play at least one round
```

### Issue: WebSocket errors in console

**Causes:**
- Socket.IO misconfiguration
- CORS not enabled
- Connection timeout

**Solutions:**
- Flask has CORS enabled by default (check run_dashboard.py)
- Check `NEXT_PUBLIC_SOCKET_URL` in .env.local matches Flask host
- Increase connection timeout if needed

## Monitoring & Logs

### View Flask Logs
```bash
# Terminal running Flask
# Will show all API calls and WebSocket events
```

### View Browser Console
```bash
# Press F12 in browser
# Go to Console tab
# Check for API errors or WebSocket messages
```

### View Network Traffic
```bash
# Press F12 → Network tab
# See all REST API calls and WebSocket connections
# Filter by XHR to see API calls
```

## Performance Tips

1. **Optimize API Calls**
   - Reduce refresh interval if not needed
   - Use pagination for recent rounds

2. **Memory Management**
   - WebSocket auto-reconnects on disconnect
   - Components auto-cleanup on unmount

3. **Network Optimization**
   - Use gzip compression (Next.js does by default)
   - Deploy frontend and backend close together (same server/region)

4. **Database Queries**
   - Flask caches CSV data
   - Consider pagination for large datasets

## Next Steps

1. ✅ Install dependencies
2. ✅ Configure environment
3. ✅ Start Flask backend
4. ✅ Start Next.js frontend
5. ✅ Open http://localhost:3000
6. ⚠️ Deploy to production (optional)
7. ⚠️ Customize colors/layout (optional)

## Support

For issues:
1. Check browser console (F12)
2. Check Flask logs
3. Review Flask API endpoints
4. Verify network connectivity
5. Check .env.local configuration

## Additional Resources

- **Next.js Docs**: https://nextjs.org/docs
- **React Docs**: https://react.dev
- **Tailwind CSS**: https://tailwindcss.com/docs
- **Recharts**: https://recharts.org/
- **Socket.IO Client**: https://socket.io/docs/v4/client-api/

---

**Dashboard Setup Complete!** 🎉

Your Next.js dashboard is ready to monitor your Aviator Bot with real-time predictions and analytics.
