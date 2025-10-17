# Advanced Analytics Dashboard Guide

## Overview

The Advanced Analytics Dashboard provides comprehensive pictorial visualization of your bot's performance with 6 key metrics and 4 interactive charts showing model predictions, actual results, and spike detection.

---

## Accessing the Dashboard

### Option 1: At Bot Startup
```
Start web dashboard? (y/n, default: n): y

🌐 Starting dashboard...
✅ Dashboard: http://localhost:5000
```

Then navigate to: **http://localhost:5000/advanced**

### Option 2: Direct URL
If dashboard is running, open browser to:
```
http://localhost:5000/advanced
```

---

## Dashboard Layout

```
┌─────────────────────────────────────────────────────────────────┐
│                       TOP HEADER                                 │
│  Status • Bot Name • Current Time                               │
└─────────────────────────────────────────────────────────────────┘

┌────────┬────────┬────────┬────────┬────────┬────────┐
│ Total  │Success │Failed  │  Win   │Highest │ P/L   │
│Rounds  │Cashouts│Rounds  │  Rate  │ (1h)   │       │
└────────┴────────┴────────┴────────┴────────┴────────┘

┌──────────────┬──────────────────────┬──────────────────────┐
│  Ensemble    │  Chart 1: Ensemble   │ Chart 2: 3 Models    │
│  Model Info  │  vs Actual Round     │ vs Actual Round      │
│              │                      │                      │
│  • RF        │                      │                      │
│  • GB        │                      │                      │
│  • LightGBM  │                      │                      │
│  • Ensemble  │                      │                      │
└──────────────┴──────────────────────┴──────────────────────┘

┌──────────────────────────┬──────────────────────────┐
│  Chart 3: Spike          │  Chart 4: Multiplier     │
│  Predictor vs Actual     │  Time Series (Spikes)    │
│                          │                          │
│                          │                          │
└──────────────────────────┴──────────────────────────┘
```

---

## Top Metrics Row (6 Metrics)

### 1. **Total Rounds** 🎯
- **What**: Count of all rounds observed/played
- **Includes**: Both BET and SKIP rounds
- **Updates**: Real-time after each round

### 2. **Success Cashouts** ✅
- **What**: Number of successful cashouts
- **Color**: Green (positive metric)
- **Formula**: `successful_cashouts / total_bets`

### 3. **Failed Rounds** ❌
- **What**: Rounds where bet was placed but crashed before cashout
- **Color**: Red (negative metric)
- **Updates**: After each crash

### 4. **Win Rate** 📊
- **What**: Percentage of successful bets
- **Formula**: `(successful_cashouts / ml_bets_placed) × 100%`
- **Example**: 15 wins out of 20 bets = 75%

### 5. **Highest Multiplier (1 Hour)** 🚀
- **What**: Highest multiplier observed in last 60 minutes
- **Updates**: Tracks rolling 1-hour window
- **Example**: Shows `47.53x` if that's the highest in last hour

### 6. **Profit/Loss** 💰
- **What**: Total profit or loss since bot started
- **Color**:
  - Green if positive profit
  - Red if negative (loss)
  - Yellow if break-even
- **Formula**: `total_return - total_bet`

---

## Row 1: Ensemble Info + 2 Charts

### Left Panel: Ensemble Model Info 🤖

**Purpose**: Show individual model statistics and last predictions

**Displays:**
```
🤖 Random Forest
   Accuracy: 58.3%
   Last Pred: 2.45x

🤖 Gradient Boosting
   Accuracy: 61.2%
   Last Pred: 2.52x

🤖 LightGBM
   Accuracy: 55.7%
   Last Pred: 2.38x

🤖 Ensemble
   Confidence: 68.4%
   Last Pred: 2.45x
```

**Updates**: After each round with model prediction

---

### Chart 1: Ensemble Prediction vs Actual Round 📈

**Purpose**: Compare ensemble model predictions with actual multipliers

**Display**:
- **Blue Line**: Ensemble predictions
- **Green Line**: Actual multipliers that occurred
- **X-Axis**: Time (HH:MM format)
- **Y-Axis**: Multiplier value

**Example**:
```
Pred: 2.45x, Actual: 3.12x → Model underestimated
Pred: 5.67x, Actual: 1.23x → Model overestimated
Pred: 2.10x, Actual: 2.08x → Model accurate
```

**Shows last 30 rounds**

---

### Chart 2: 3 Models Prediction vs Actual Round 📊

**Purpose**: Compare individual model predictions against actual results

**Display**:
- **Orange Line**: Random Forest predictions
- **Pink Line**: Gradient Boosting predictions
- **Purple Line**: LightGBM predictions
- **Green Line** (thick): Actual multipliers

**Analysis**:
- **Convergence**: When all 3 models predict similar values → High confidence
- **Divergence**: When models disagree → Low confidence, unreliable
- **Accuracy**: How close predictions track actual line

**Shows last 30 rounds**

---

## Row 2: Spike Detection Charts

### Chart 3: Actual Result vs Spike Predictor ⚡

**Purpose**: Identify high multiplier spikes (≥10x) and compare with actual results

**Display**:
- **Green Bars**: Actual multiplier for each round
- **Red Bars**: Spike detected (when multiplier ≥ 10x)

**Use Cases**:
- **Spike Detection**: Red bars show when spikes occurred
- **Frequency Analysis**: Count red bars to see spike frequency
- **Pattern Recognition**: Look for spike clustering or spacing

**Example**:
```
Rounds: 1.2x | 2.5x | 15.3x | 1.8x | 22.7x | 3.4x
Spikes:  -   |  -   | SPIKE |  -   | SPIKE |  -
```

---

### Chart 4: Multiplier Time Series (Spike Detection) 📉

**Purpose**: Visualize multiplier trends over time with spike highlighting

**Display**:
- **Green Line/Area**: Normal multipliers (< 10x)
- **Red Line/Points**: Spikes (≥ 10x) highlighted with larger dots
- **Red Dashed Line**: Spike threshold at 10x
- **Shaded Area**: Visual emphasis of value ranges

**Features**:
- **Time Series**: Shows chronological progression
- **Visual Spikes**: Red dots make spikes immediately obvious
- **Trend Analysis**: See if multipliers are trending up/down
- **Volatility**: Wide swings = high volatility

**Shows last 30 rounds**

---

## Real-Time Updates

### Update Frequency

| Element | Update Trigger |
|---------|---------------|
| Metrics | After each round completes |
| Charts | After each round with prediction |
| Ensemble Info | When new prediction is made |
| Spike Detection | After each round completes |

### WebSocket Connection

Dashboard uses **Socket.IO** for real-time updates:
- **No page refresh needed**
- **Instant updates** when bot processes rounds
- **Automatic reconnection** if connection drops

---

## Interpreting the Visualizations

### Good Model Performance

**Chart 1 & 2**: Prediction lines closely track actual line
```
✅ Predictions: 2.1x, 2.3x, 2.5x
✅ Actuals:     2.0x, 2.4x, 2.6x
→ Models are performing well
```

**Chart 3 & 4**: Spikes are rare and predictions handle normal range well
```
✅ 28 normal rounds, 2 spikes
→ Good pattern recognition
```

---

### Poor Model Performance

**Chart 1 & 2**: Large gaps between predictions and actuals
```
❌ Predictions: 5.2x, 4.8x, 5.5x
❌ Actuals:     1.2x, 1.5x, 1.8x
→ Models consistently overestimating
```

**Solution**: Retrain models with more recent data

---

### High Agreement (Reliable)

**Chart 2**: All 3 model lines converge
```
RF:  2.4x ─┐
GB:  2.5x ─┼─ Close agreement
LGB: 2.4x ─┘
→ High confidence prediction
```

---

### Low Agreement (Unreliable)

**Chart 2**: Model lines diverge widely
```
RF:  1.8x ─┐
GB:  4.2x ─┼─ Large disagreement
LGB: 2.5x ─┘
→ Low confidence, skip betting
```

---

## Spike Analysis

### Identifying Patterns

**Chart 4 - Time Series:**

**Pattern 1: Spike Clustering**
```
Timeline: __|__|__|15x|__|__|18x|__|__|
                 └─── Cluster ───┘
→ Spikes occurring close together
```

**Pattern 2: Spike Spacing**
```
Timeline: __|15x|__|__|__|__|__|__|22x|__
          └──── Long gap ─────┘
→ Spikes spaced far apart
```

**Pattern 3: Pre-Spike Behavior**
```
Before: 1.2x | 1.5x | 1.3x | 15.7x ← spike
→ Low multipliers before spike
```

### Using Spike Data

**Chart 3 - Spike Predictor:**
- Count red bars = spike frequency
- Check spacing between red bars
- Correlate with bet outcomes

**Strategy Adjustment:**
- High spike frequency → Consider higher targets
- Low spike frequency → Stick to safe multipliers
- After spike → Possible "cool down" period

---

## Technical Details

### Charts Technology
- **Library**: Chart.js 4.4.0
- **Type**: Responsive HTML5 Canvas
- **Performance**: Optimized for 30-50 data points
- **Update**: Non-blocking animations

### Data Flow
```
Bot Round Complete
      ↓
Extract Model Predictions
      ↓
Package Round Data
      ↓
WebSocket Emit
      ↓
Dashboard Receives
      ↓
Update Metrics + Charts
      ↓
User Sees Update (< 100ms)
```

### Browser Requirements
- **Modern Browser**: Chrome, Firefox, Edge, Safari
- **JavaScript**: Must be enabled
- **WebSocket**: Required for real-time updates
- **Canvas**: HTML5 canvas support

---

## Troubleshooting

### Charts Not Updating

**Problem**: Dashboard loads but charts don't update

**Solutions**:
1. Check bot is running
2. Check browser console for errors (F12)
3. Refresh page (Ctrl+R)
4. Check WebSocket connection indicator

### Missing Data

**Problem**: Charts show "Waiting for data..."

**Cause**: Not enough rounds played yet

**Solution**: Wait for bot to complete at least 5-10 rounds

### Lag or Delay

**Problem**: Updates take several seconds

**Possible Causes**:
- Network latency
- Too many data points
- Browser performance

**Solutions**:
- Reduce data retention (modify `maxPoints` in HTML)
- Close other tabs
- Use faster network

---

## Customization

### Changing Data Retention

Edit `advanced_dashboard.html` line ~700:
```javascript
const maxPoints = 30;  // Change to 50, 100, etc.
```

### Adjusting Spike Threshold

Edit line ~800:
```javascript
const isSpike = data.multiplier >= 10;  // Change 10 to 15, 20, etc.
```

### Chart Colors

Edit chart configuration:
```javascript
borderColor: '#60a5fa',  // Change to any hex color
backgroundColor: 'rgba(96, 165, 250, 0.1)'
```

---

## Quick Reference

| Metric/Chart | What It Shows | Update Frequency |
|--------------|---------------|------------------|
| Total Rounds | Count of all rounds | After each round |
| Win Rate | Success percentage | After each bet |
| Highest (1h) | Max mult in 60min | Rolling window |
| Chart 1 | Ensemble vs Actual | Real-time |
| Chart 2 | 3 Models vs Actual | Real-time |
| Chart 3 | Spike Detection | After each round |
| Chart 4 | Time Series | Real-time |

---

## Summary

The Advanced Analytics Dashboard provides:

✅ **6 Key Metrics** at a glance
✅ **Ensemble Model Info** with accuracy stats
✅ **2 Prediction Charts** showing model performance
✅ **2 Spike Detection Charts** for pattern analysis
✅ **Real-time updates** via WebSockets
✅ **Professional visualizations** with Chart.js
✅ **Responsive design** for all screen sizes

Perfect for monitoring bot performance and understanding ML model behavior! 🚀
