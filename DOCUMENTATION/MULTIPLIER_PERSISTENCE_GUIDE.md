# Multiplier Persistence Implementation Guide

## Overview
This guide explains how the multiplier persistence system works, allowing real-time multiplier values from the dashboard to be saved to the database automatically.

## Architecture

### Components

1. **Frontend (Next.js React)**
   - Dashboard component tracks live multiplier values
   - Automatically detects round start/end events
   - Sends multiplier data via HTTP POST requests

2. **Backend (Flask + SQLAlchemy)**
   - REST API endpoints accept multiplier data
   - Validates and stores data in Supabase PostgreSQL
   - Integrates with existing database models

3. **Database (Supabase PostgreSQL)**
   - `crash_game_rounds` - Main round records
   - `analytics_round_multipliers` - Individual multiplier values
   - Supports ML training and analytics

## How It Works

### Multiplier Extraction

The multiplier is extracted from the React component state in Dashboard.tsx:

```typescript
const [liveData, setLiveData] = useState<LiveData>({
  multiplier: 1.0,  // <-- Extracted from here
  status: "AWAITING" | "RUNNING" | "CRASHED"
});
```

The multiplier is updated in real-time via:
1. Socket.IO events from backend
2. Demo mode simulation (for testing)
3. Manual handler updates

### Data Flow

```
React State (multiplier)
    ↓
useEffect detects change
    ↓
Create round (if needed)
    ↓
POST /api/multiplier/log
    ↓
Flask Backend
    ↓
SQLAlchemy ORM
    ↓
Supabase PostgreSQL
```

### Round Lifecycle

1. **Round Start**: When `status === "RUNNING"` and `multiplier === 1.0`
   - `POST /api/multiplier/create_round` creates a new record
   - Returns `round_id` for subsequent multiplier logs

2. **Multiplier Updates**: Every time multiplier changes
   - `POST /api/multiplier/log` saves the value
   - Associates with current `round_id`
   - Includes timestamp and flags (is_crash, is_cashout)

3. **Round End**: When `status === "CRASHED"`
   - Last multiplier is logged with `is_crash=true`
   - Round number increments for next round

## API Endpoints

### 1. Create Round
```
POST /api/multiplier/create_round

Request:
{
  "bot_id": "demo_bot_001",
  "round_number": 1,
  "stake_value": 25.0,
  "strategy_name": "custom",
  "game_name": "aviator",
  "platform_code": "demo",
  "session_id": "demo_session_1234567890"
}

Response:
{
  "status": "success",
  "message": "Round 1 created successfully",
  "round_id": 123
}
```

### 2. Log Multiplier
```
POST /api/multiplier/log

Request:
{
  "bot_id": "demo_bot_001",
  "multiplier": 1.23,
  "round_id": 123,
  "is_crash": false,
  "is_cashout": false,
  "ocr_confidence": 0.95,
  "game_name": "aviator",
  "platform_code": "demo",
  "timestamp": "2025-11-25T12:34:56.789Z"
}

Response:
{
  "status": "success",
  "message": "Multiplier 1.23x logged successfully",
  "record_id": 456,
  "timestamp": "2025-11-25T12:34:56.789Z"
}
```

### 3. Get Latest Round
```
GET /api/multiplier/latest_round/{bot_id}

Response:
{
  "status": "success",
  "round": {
    "id": 123,
    "number": 1
  }
}
```

## Files Modified/Created

### Backend

**New Files:**
- `backend/database/multiplier_logger.py` - MultiplierLogger class with DB operations
- `backend/dashboard/multiplier_api.py` - Flask blueprint with API endpoints

**Modified Files:**
- `backend/dashboard/compact_analytics.py` - Integrated MultiplierLogger initialization

### Frontend

**Modified Files:**
- `src/lib/api.ts` - Added multiplier logging functions
  - `logMultiplier()` - POST multiplier data
  - `createRound()` - POST round creation
  - `getLatestRound()` - GET latest round info

- `src/components/Dashboard.tsx` - Added multiplier logging logic
  - Round creation on round start
  - Automatic multiplier logging on each change
  - Round completion detection
  - Debounced requests to avoid flooding the API

## Database Schema

### crash_game_rounds
```sql
CREATE TABLE crash_game_rounds (
  id SERIAL PRIMARY KEY,
  bot_id VARCHAR(50) NOT NULL,
  session_id VARCHAR(100) NOT NULL,
  game_name VARCHAR(50) NOT NULL,
  round_number INTEGER NOT NULL,
  round_start_timestamp TIMESTAMP NOT NULL,
  stake_value DECIMAL(15, 2) NOT NULL,
  strategy_name VARCHAR(50),
  -- ... other fields
);
```

### analytics_round_multipliers
```sql
CREATE TABLE analytics_round_multipliers (
  id SERIAL PRIMARY KEY,
  round_id INTEGER NOT NULL REFERENCES crash_game_rounds(id),
  multiplier DECIMAL(10, 4) NOT NULL,
  timestamp TIMESTAMP NOT NULL,
  bot_id VARCHAR(50) NOT NULL,
  game_name VARCHAR(50) NOT NULL,
  platform_code VARCHAR(50),
  is_crash_multiplier BOOLEAN DEFAULT FALSE,
  is_cashout_multiplier BOOLEAN DEFAULT FALSE,
  ocr_confidence DECIMAL(5, 4),
  created_at TIMESTAMP DEFAULT NOW()
);
```

## Testing

### Option 1: Demo Mode (No Backend Required)
1. Open dashboard
2. Click "🎮 Demo ON" button
3. Watch multipliers being logged in console
4. Check database for records

### Option 2: API Test Script
```bash
# Make sure backend is running
python run_dashboard.py --port 5001

# In another terminal
python test_multiplier_api.py
```

### Option 3: Manual API Testing
```bash
# Create a round
curl -X POST http://localhost:5001/api/multiplier/create_round \
  -H "Content-Type: application/json" \
  -d '{
    "bot_id": "test_bot",
    "round_number": 1,
    "stake_value": 25.0
  }'

# Log a multiplier
curl -X POST http://localhost:5001/api/multiplier/log \
  -H "Content-Type: application/json" \
  -d '{
    "bot_id": "test_bot",
    "multiplier": 1.23,
    "round_id": 123
  }'
```

## Features

✅ **Real-time Logging**
- Multipliers logged immediately as they update
- 300ms debounce to avoid excessive requests

✅ **Automatic Round Management**
- Rounds created on demand
- Round completion detected automatically
- Round numbers increment properly

✅ **Data Quality**
- Multipliers rounded to 2 decimal places
- Timestamps in UTC ISO format
- Optional OCR confidence tracking
- Crash detection flags

✅ **Error Handling**
- Graceful fallback if database unavailable
- Console logging for debugging
- Non-blocking (UI continues even if logging fails)

✅ **Demo Mode Compatible**
- Works with simulated multiplier changes
- Useful for testing without live game
- Can test full round lifecycle

## Console Output

When running with demo mode, you'll see:
```
📊 Dashboard: Multiplier changed { newMultiplier: 1.05, timestamp: '...' }
✅ Round created: 123
💾 Multiplier 1.05x logged: 456
💾 Multiplier 1.23x logged: 457
💾 Multiplier 1.42x logged: 458
💥 ROUND ENDED at 1.89x
🏁 Round ended at 1.89x
```

## Configuration

### Bot ID
Located in `Dashboard.tsx`:
```typescript
const BOT_ID = "demo_bot_001";
```
Change this to identify different bots.

### Session ID
Auto-generated from timestamp:
```typescript
const SESSION_ID = "demo_session_" + Date.now();
```

### API Base URL
From `.env.local`:
```
NEXT_PUBLIC_API_URL=http://localhost:5001
```

## Troubleshooting

**Q: Multipliers not being logged?**
- Check if backend is running on port 5001
- Verify database connection in logs
- Check browser console for errors

**Q: "Database engine not initialized" warning?**
- Ensure environment variables are set (.env file)
- Check Supabase connection credentials
- Verify database tables exist

**Q: API returns 500 error?**
- Check Flask logs for detailed error
- Verify request JSON format is correct
- Ensure required fields are present

**Q: High database load?**
- Reduce logging frequency (increase debounce time)
- Filter multipliers (only log significant changes)
- Batch requests together

## Future Enhancements

- [ ] Batch logging (log multiple values in one request)
- [ ] Compression (reduce payload size)
- [ ] Offline queue (queue logs when offline)
- [ ] Analytics dashboard for logged multipliers
- [ ] Real-time chart updates from logged data
- [ ] Export to CSV for analysis
