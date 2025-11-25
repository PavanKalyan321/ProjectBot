# 🎯 Aviator Bot - Compact Analytics Dashboard

**The Ultimate Half-Screen Dashboard for Real-Time Aviator Bot Monitoring**

## 📋 Table of Contents

- [Features](#features)
- [Quick Start](#quick-start)
- [Dashboard Overview](#dashboard-overview)
- [Data Management](#data-management)
- [API Endpoints](#api-endpoints)
- [Troubleshooting](#troubleshooting)

---

## ✨ Features

### 🎮 Half-Screen Optimized
- **Compact Design**: Perfect for 50% screen width
- **Real-Time Updates**: Live data every 5 seconds
- **Side-by-Side**: Run Aviator on one half, dashboard on the other

### 📊 Live Analytics
- **Current Round Tracking**: See actual vs predicted multipliers
- **16 Model Predictions**: All models displayed in real-time
- **Top Performers**: Automatically ranked best models
- **Confidence Meters**: Visual confidence indicators

### 📈 Trend Analysis
- **Upward/Downward Flow**: Visual trend indicators
- **Trading Signals**: BET, SKIP, CAUTIOUS, OPPORTUNITY
- **Pattern Detection**: Low greens, post-high echo, mean reversion
- **Volatility Tracking**: Real-time volatility analysis

### 🏆 Model Comparison
- **All 16 Models**: View every model's prediction
- **Accuracy Tracking**: Color-coded accuracy levels (green/yellow/red)
- **Best Model**: Auto-highlighted top performer
- **Error Metrics**: MAE, median error for each model

### 📋 Rules Engine
- **Low Green Series**: Detects 3+ rounds < 2x
- **Post-High Echo**: Warns after 10x+ multipliers
- **Mean Reversion**: Identifies deviation from average
- **Active/Inactive Status**: Real-time rule activation

### 📈 Historical View
- **Last 20 Rounds**: Scrollable round history
- **Trend Chart**: Visual actual vs predicted chart
- **Win/Loss Indicators**: Color-coded results
- **Recommendation Tracking**: Shows if bet was recommended

### 🛠️ Data Management
- **One-Click Cleanup**: Remove duplicates and fix headers
- **Archive Old Data**: Keep only recent data
- **Data Quality Check**: Identify issues automatically
- **Consolidate Files**: Merge into single file

---

## 🚀 Quick Start

### Prerequisites

```bash
pip install flask flask-socketio pandas numpy
```

### Option 1: Direct Launch (Recommended)

```bash
python run_dashboard.py
```

This will:
1. Check your data files
2. Ask if you want to cleanup
3. Start the dashboard at http://localhost:5001
4. Auto-open your browser

### Option 2: Cleanup First, Then Launch

```bash
# Step 1: Cleanup your data
python cleanup_data.py

# Step 2: Start dashboard
python run_dashboard.py
```

### Option 3: Manual Start

```bash
cd backend/dashboard
python compact_analytics.py
```

---

## 🖥️ Dashboard Overview

### Screen Layout (Half-Screen View)

```
┌─────────────────────────────────────┐
│  🎯 Aviator Bot Analytics    🔴 LIVE│
├─────────────────────────────────────┤
│  Total Rounds │ Win Rate │ P/L      │ <- Live Stats
├─────────────────────────────────────┤
│  CURRENT ROUND                      │
│  ┌──────────┐  ┌──────────┐        │
│  │ ACTUAL   │  │ PREDICTED│        │ <- Current Multipliers
│  │  2.45x   │  │  2.38x   │        │
│  └──────────┘  └──────────┘        │
│  Confidence: ████████░░ 82%        │ <- Confidence Bar
├─────────────────────────────────────┤
│  ┌────────┐  ┌────────┐            │
│  │ TREND  │  │ SIGNAL │            │ <- Trend & Signal
│  │   ↑    │  │  BET   │            │
│  └────────┘  └────────┘            │
├─────────────────────────────────────┤
│  🏆 TOP PERFORMING MODELS           │
│  🥇 Model 3  - 87.5%               │ <- Top 3 Models
│  🥈 Model 7  - 85.2%               │
│  🥉 Model 1  - 83.8%               │
├─────────────────────────────────────┤
│  📊 ALL 16 MODELS - CURRENT ROUND  │
│  [M1] [M2] [M3] [M4]               │ <- All Model Grid
│  [M5] [M6] [M7] [M8]               │
│  [M9] [M10][M11][M12]              │
│  [M13][M14][M15][M16]              │
├─────────────────────────────────────┤
│  📋 GAME RULES & PATTERNS           │
│  ✅ Low Green Series  - BET        │ <- Active Rules
│  ❌ Post-High Echo    - NEUTRAL    │
│  ✅ Mean Reversion    - STABLE     │
├─────────────────────────────────────┤
│  📈 RECENT 20 ROUNDS               │
│  [Chart showing trend line]        │ <- Visual Chart
│  [Scrollable round history]        │
└─────────────────────────────────────┘
```

### Color Coding

- **Green** (🟢): Good predictions, wins, upward trends
- **Red** (🔴): Poor predictions, losses, downward trends
- **Yellow** (🟡): Medium accuracy, neutral signals
- **Blue** (🔵): Predictions, information
- **Purple** (🟣): Rules section

### Trend Indicators

| Trend | Icon | Meaning |
|-------|------|---------|
| UPWARD | ↑ | Multipliers increasing (be cautious) |
| DOWNWARD | ↓ | Multipliers decreasing (opportunity) |
| NEUTRAL | → | Stable trend |

### Signal Types

| Signal | Icon | Action |
|--------|------|--------|
| STRONG_BET | 🎯 | High confidence bet opportunity |
| BET | ✅ | Normal bet recommended |
| OPPORTUNITY | 💡 | Good betting opportunity |
| CAUTIOUS | ⚠️ | Bet with caution |
| WAIT | ⏸ | Wait for better opportunity |
| SKIP | ⛔ | Skip this round |

---

## 🗂️ Data Management

### Data Files Location

```
backend/
├── aviator_rounds_history.csv    (~1 MB)
├── bet_history.csv                (~0.03 MB)
└── bot_automl_performance.csv     (~0.1 MB)
```

### Cleanup Operations

#### 1. Quick Cleanup

Removes:
- Duplicate round IDs
- Invalid multipliers (< 0 or NaN)
- Empty rows
- Rows with all zeros

```bash
python cleanup_data.py
# Choose option 1
```

#### 2. Archive Old Data

Moves old data to archive folder, keeps only recent data:

```bash
python cleanup_data.py
# Choose option 2
# Enter number of days to keep (default: 30)
```

Archives saved to: `backend/data/archive/`

#### 3. Consolidate Data

Merges all 3 CSV files into a single comprehensive file:

```bash
python cleanup_data.py
# Choose option 3
```

Output: `backend/consolidated_data_YYYYMMDD_HHMMSS.csv`

#### 4. Full Optimization

Runs all cleanup operations:

```bash
python cleanup_data.py
# Choose option 4
```

This will:
1. Clean up duplicates and fix headers
2. Archive data older than 30 days
3. Show final summary

---

## 🔌 API Endpoints

The dashboard exposes these REST APIs:

### GET `/api/current_round`

Returns current round with all model predictions.

**Response:**
```json
{
  "round_id": "20251102123456",
  "actual": 2.45,
  "ensemble_prediction": 2.38,
  "confidence": 82.5,
  "models": [
    {"name": "Model 1", "prediction": 2.40, "accuracy": 85.2},
    ...
  ],
  "best_model": "Model 3",
  "trend": "UPWARD",
  "signal": "CAUTIOUS"
}
```

### GET `/api/live_stats`

Returns live statistics summary.

**Response:**
```json
{
  "total_rounds": 1250,
  "win_rate": 67.5,
  "profit_loss": 245.80,
  "avg_confidence": 78.3,
  "current_streak": 5,
  "streak_type": "WIN"
}
```

### GET `/api/model_comparison`

Compare all 16 models.

**Response:**
```json
{
  "models": [
    {
      "model": "Model 3",
      "avg_error": 0.45,
      "accuracy": 87.5
    },
    ...
  ]
}
```

### GET `/api/trend_signal`

Get trend analysis and trading signal.

**Response:**
```json
{
  "trend": "UPWARD",
  "signal": "CAUTIOUS",
  "strength": 65.2,
  "analysis": "High multiplier phase (avg: 5.23x)",
  "volatility": 2.15,
  "low_greens": 2
}
```

### GET `/api/top_models`

Get top 3 performing models.

**Response:**
```json
{
  "top_models": [
    {"model": "Model 3", "accuracy": 87.5},
    {"model": "Model 7", "accuracy": 85.2},
    {"model": "Model 1", "accuracy": 83.8}
  ]
}
```

### GET `/api/rules_status`

Get game rules status and patterns.

**Response:**
```json
{
  "rules": [
    {
      "name": "Low Green Series",
      "active": true,
      "count": 4,
      "signal": "BET"
    },
    ...
  ],
  "patterns": {
    "avg_multiplier": 2.45,
    "volatility": 1.85,
    "max_recent": 8.50,
    "min_recent": 1.05
  }
}
```

### GET `/api/recent_rounds?limit=20`

Get recent rounds with predictions.

**Query Params:**
- `limit`: Number of rounds (default: 20)

**Response:**
```json
{
  "rounds": [
    {
      "round_id": "20251102123456",
      "actual": 2.45,
      "prediction": 2.38,
      "confidence": 82.5,
      "recommended": true,
      "error": 0.07
    },
    ...
  ]
}
```

### POST `/api/cleanup`

Trigger data cleanup.

**Response:**
```json
{
  "success": true,
  "rows_removed": 45,
  "message": "Cleaned 45 duplicate/empty rows"
}
```

---

## 🎨 Customization

### Change Port

Edit `run_dashboard.py`:

```python
dashboard = CompactAnalyticsDashboard(port=5001)  # Change to your port
```

### Adjust Refresh Rate

Edit `compact_dashboard.html`:

```javascript
setInterval(loadAllData, 5000);  // Change 5000 to your interval (milliseconds)
```

### Modify Color Scheme

Edit CSS in `compact_dashboard.html`:

```css
body {
    background: linear-gradient(135deg, #0f0c29, #302b63, #24243e);
}
```

---

## ❓ Troubleshooting

### Issue: Dashboard won't start

**Solution:**
```bash
# Install missing dependencies
pip install flask flask-socketio pandas numpy

# Check if port 5001 is available
# Change port in run_dashboard.py if needed
```

### Issue: No data showing

**Solution:**
```bash
# Check if CSV files exist
ls backend/*.csv

# Run cleanup to fix headers
python cleanup_data.py
```

### Issue: Old/duplicate data

**Solution:**
```bash
# Run full optimization
python cleanup_data.py
# Choose option 4
```

### Issue: Dashboard too large

**Solution:**
- Use browser zoom: `Ctrl + -` (Windows) or `Cmd + -` (Mac)
- Or resize browser window to 50% screen width

### Issue: Models not showing

**Solution:**
- Ensure `bot_automl_performance.csv` exists
- Check file has `model_1_pred` through `model_16_pred` columns
- Run the bot to generate predictions first

---

## 🔄 Workflow Recommendation

### Daily Usage

1. **Morning**: Run cleanup
   ```bash
   python cleanup_data.py
   # Choose option 1 (Quick Cleanup)
   ```

2. **Start Dashboard**
   ```bash
   python run_dashboard.py
   ```

3. **Arrange Windows**
   - Aviator game: Left half of screen
   - Dashboard: Right half of screen

4. **Monitor**
   - Watch trend signals
   - Follow top model recommendations
   - Check rule activations

### Weekly Maintenance

1. **Archive Old Data**
   ```bash
   python cleanup_data.py
   # Choose option 2 (Archive, keep 7 days)
   ```

2. **Review Performance**
   - Check win rate trends
   - Identify best performing models
   - Analyze pattern detection accuracy

---

## 📊 Understanding the Dashboard

### Confidence Meter

- **0-50%**: Low confidence - be very cautious
- **50-70%**: Medium confidence - moderate risk
- **70-85%**: High confidence - good opportunity
- **85-100%**: Very high confidence - strong signal

### Model Accuracy

- **Green (80%+)**: Excellent prediction
- **Yellow (60-80%)**: Good prediction
- **Red (<60%)**: Poor prediction

### Trend Strength

- **0-30**: Weak trend
- **30-60**: Moderate trend
- **60-100**: Strong trend

---

## 🎯 Pro Tips

1. **Best Viewing**: Use full HD monitor (1920x1080) or larger
2. **Browser**: Chrome/Edge recommended for best performance
3. **Updates**: Dashboard auto-refreshes every 5 seconds
4. **Manual Refresh**: Click "Refresh Data" button for immediate update
5. **Data Cleanup**: Run weekly for optimal performance
6. **Archive**: Keep last 30 days, archive rest

---

## 📝 Files Created

```
c:\Project\
├── run_dashboard.py                          # Main launcher
├── cleanup_data.py                           # Data cleanup tool
├── DASHBOARD_README.md                       # This file
├── backend/
│   ├── dashboard/
│   │   ├── compact_analytics.py             # Backend server
│   │   └── templates/
│   │       └── compact_dashboard.html       # Frontend UI
│   └── utils/
│       └── data_manager.py                  # Data management utilities
```

---

## 🎉 You're All Set!

Your compact analytics dashboard is ready to use!

**Start now:**
```bash
python run_dashboard.py
```

**Questions?** Check the troubleshooting section above.

**Happy Trading! 🚀**
