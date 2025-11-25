# Multiplier Persistence - Quick Start

## What Was Implemented

You can now **save live multiplier values to the database** automatically as the game runs.

## How to Use It

### 1. Start the Dashboard
```bash
# In the backend directory
python run_dashboard.py --port 5001
```

### 2. Start the Next.js App
```bash
# In the dashboard-nextjs directory
npm run dev
```

### 3. Open the Dashboard
- Visit `http://localhost:3000`
- Click "🎮 Demo ON" to enable demo mode
- Watch multipliers being logged to the database in real-time

### 4. Check the Logs
Open your browser console (F12) and you'll see:
```
📊 Dashboard: Multiplier changed { newMultiplier: 1.05, ... }
✅ Round created: 123
💾 Multiplier 1.05x logged: 456
💾 Multiplier 1.23x logged: 457
...
💥 ROUND ENDED at 1.89x
```

## Data Flow

```
Game Screen
    ↓
Extract Multiplier (React State)
    ↓
POST to /api/multiplier/log
    ↓
Save to Database
    ↓
Use for ML Training / Analytics
```

## Key Features

✅ **Automatic Detection**
- Detects round start (multiplier = 1.0, status = RUNNING)
- Detects multiplier changes (logs every update)
- Detects round end (status = CRASHED)

✅ **Efficient Logging**
- 300ms debounce to avoid flooding API
- Rounds multiplier to 2 decimal places
- Only logs when multiplier actually changes

✅ **Round Management**
- Auto-creates round record on round start
- Associates all multipliers with round ID
- Tracks which multiplier is the crash

✅ **Demo Mode Compatible**
- Works with simulated multipliers
- Perfect for testing without real game

## Database Records Created

For each round you play, 2 types of records are created:

### 1. Round Record (crash_game_rounds)
```
round_id: 123
bot_id: demo_bot_001
round_number: 1
stake_value: 25.0
timestamp: 2025-11-25T12:34:56.789Z
```

### 2. Multiplier Records (analytics_round_multipliers)
One record per multiplier update:
```
multiplier: 1.05x  → record_id: 456
multiplier: 1.23x  → record_id: 457
multiplier: 1.42x  → record_id: 458
multiplier: 1.89x  → record_id: 459 (is_crash=true)
```

## Test It Out

### Manual Testing
```bash
# Create a round
curl -X POST http://localhost:5001/api/multiplier/create_round \
  -H "Content-Type: application/json" \
  -d '{
    "bot_id": "test_bot",
    "round_number": 1,
    "stake_value": 25
  }'

# Expected response:
# { "status": "success", "round_id": 123 }

# Log a multiplier
curl -X POST http://localhost:5001/api/multiplier/log \
  -H "Content-Type: application/json" \
  -d '{
    "bot_id": "test_bot",
    "multiplier": 1.23,
    "round_id": 123
  }'

# Expected response:
# { "status": "success", "record_id": 456 }
```

### Automated Testing
```bash
python test_multiplier_api.py
```

## Files Created

**Backend:**
- `backend/database/multiplier_logger.py` - Database operations
- `backend/dashboard/multiplier_api.py` - Flask API routes

**Frontend:**
- Added multiplier logging to `src/lib/api.ts`
- Added logging logic to `src/components/Dashboard.tsx`

**Documentation:**
- `MULTIPLIER_PERSISTENCE_GUIDE.md` - Full guide
- `test_multiplier_api.py` - API test script
- `MULTIPLIER_QUICK_START.md` - This file

## Environment Setup

Make sure your `.env` has:
```
DB_HOST=zofojiubrykbtmstfhzx.supabase.co
DB_PORT=5432
DB_NAME=postgres
DB_USER=postgres
DB_PASSWORD=your_password_here
```

And your Next.js `.env.local` has:
```
NEXT_PUBLIC_API_URL=http://localhost:5001
```

## Extracting Multiplier from Iframe

The multiplier is extracted from:

1. **React State** - `liveData.multiplier`
2. **Demo Mode** - Simulated 500ms updates
3. **Socket.IO** - From backend events
4. **Manual Updates** - Via handler callbacks

The floating display on the iframe shows it visually:
```
┌─────────────────┐
│  1.23x          │
└─────────────────┘
```

And the actual value is extracted and logged to the database.

## Next Steps

1. ✅ Test with demo mode running
2. ✅ Verify records appear in database
3. ✅ Connect to real game (replace demo mode)
4. ✅ Build ML models with the logged data
5. ✅ Create analytics dashboards

## Support

If you encounter issues:
1. Check Flask logs for errors
2. Check browser console (F12)
3. Verify database connection
4. Run `test_multiplier_api.py` for diagnostics

Everything is now in place to save live multiplier values! 🚀
