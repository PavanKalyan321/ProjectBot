# Real-Time ML Prediction System

## Overview

The bot now implements **real-time model predictions** that continuously update as new round data is observed. Models are no longer static - they adapt their predictions based on the latest game rounds.

---

## How It Works

### 1. **Continuous Data Feed**

Every time a new round completes:

```
Game Round Ends
     ↓
Read Multiplier from Clipboard
     ↓
Log to aviator_rounds_history.csv IMMEDIATELY
     ↓
Update In-Memory Cache
     ↓
Generate Fresh ML Predictions
     ↓
Display Updated Predictions
```

### 2. **Real-Time History Updates**

**Before** (Static):
- Round completes → Wait until decision time → Log to CSV
- Models use OLD data from previous bot runs

**After** (Real-Time):
- Round completes → **Log IMMEDIATELY** to CSV ([bot_modular.py:453-456](bot_modular.py#L453-L456))
- Models use **LATEST data** including rounds that just finished
- Predictions evolve as patterns change

### 3. **Prediction Evolution Tracking**

The bot now tracks how predictions change over time:

```
📈 PREDICTION TREND (Last 5 rounds):
  [2.45x] ↗ [2.67x] ↗ [2.89x] ↘ [2.75x] ↗ [2.82x]
```

**Arrows indicate:**
- `↗` = Prediction increasing (models expect higher multiplier)
- `↘` = Prediction decreasing (models expect lower multiplier)
- `→` = Prediction stable (no change)

---

## Example Output

### Round 1: Initial Prediction

```
🎯 ROUND #001
═══════════════════════════════════════════════
  📝 Checking for previous round...
  ✅ Previous round: 3.45x (added to history)
  💾 Updated history for real-time predictions

  🤖 Analyzing patterns with latest round data...

  🤖 MODEL PREDICTIONS:
  ┌──────────────────┬──────────┬────────────┐
  │      MODEL       │   PRED   │ CONFIDENCE │
  ├──────────────────┼──────────┼────────────┤
  │ Random Forest    │   2.45x │    58.2%   │
  │ Gradient Boost   │   2.52x │    61.5%   │
  │ LightGBM         │   2.38x │    55.8%   │
  ├──────────────────┼──────────┼────────────┤
  │ ENSEMBLE         │   2.45x │    58.5%   │
  └──────────────────┴──────────┴────────────┘
  Expected Value: 1.43
  Model Agreement: HIGH (σ=0.07)
```

### Round 5: Evolved Prediction with Trend

```
🎯 ROUND #005
═══════════════════════════════════════════════
  📝 Checking for previous round...
  ✅ Previous round: 5.67x (added to history)
  💾 Updated history for real-time predictions

  🤖 Analyzing patterns with latest round data...

  🤖 MODEL PREDICTIONS:
  ┌──────────────────┬──────────┬────────────┐
  │      MODEL       │   PRED   │ CONFIDENCE │
  ├──────────────────┼──────────┼────────────┤
  │ Random Forest    │   3.12x │    62.8%   │
  │ Gradient Boost   │   3.24x │    65.2%   │
  │ LightGBM         │   3.08x │    61.5%   │
  ├──────────────────┼──────────┼────────────┤
  │ ENSEMBLE         │   3.15x │    63.2%   │
  └──────────────────┴──────────┴────────────┘
  Expected Value: 1.99
  Model Agreement: HIGH (σ=0.08)

  📈 PREDICTION TREND (Last 5 rounds):
  [2.45x] ↗ [2.67x] ↗ [2.89x] ↘ [2.75x] ↗ [3.15x]
```

**Notice:**
- Prediction changed from 2.45x → 3.15x as new high multiplier (5.67x) was observed
- Trend shows predictions generally increasing
- Models adapted their expectations based on recent pattern

---

## Key Features

### 1. **Immediate Data Integration**

New rounds are logged to CSV **before** generating predictions:
- [bot_modular.py:453-456](bot_modular.py#L453-L456) - Reads and logs immediately
- [bot_modular.py:470](bot_modular.py#L470) - Generates predictions with updated data

### 2. **In-Memory Cache Updates**

The history tracker uses an async write system with in-memory cache:
- [history_tracker.py:196-221](core/history_tracker.py#L196-L221) - Async write + cache update
- Cache is updated IMMEDIATELY (line 200-221)
- Disk write happens in background thread (non-blocking)
- Models read from cache, so they see updates instantly

### 3. **Feature Recalculation**

Every prediction uses the latest 20 rounds:
- [ml_signal_generator.py:51](core/ml_signal_generator.py#L51) - Gets recent rounds
- [ml_models.py:90-178](core/ml_models.py#L90-L178) - Recalculates 37 features
- Features include: mean, std, volatility, trends, streaks, etc.

### 4. **Prediction History Tracking**

Bot maintains a rolling window of last 5 predictions:
- [bot_modular.py:72-73](bot_modular.py#L72-L73) - Deque with maxlen=5
- [bot_modular.py:242-246](bot_modular.py#L242-L246) - Store each prediction
- [bot_modular.py:286-300](bot_modular.py#L286-L300) - Display trend visualization

---

## Workflow Diagram

```
┌─────────────────────────────────────────────────┐
│  New Round Completes (e.g., 3.45x)              │
└────────────────┬────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────┐
│  Read from Clipboard (auto_log_from_clipboard)  │
│  └─ log_to_history=True                         │
└────────────────┬────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────┐
│  Write to CSV (Async)                           │
│  Update In-Memory Cache (Immediate)             │
└────────────────┬────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────┐
│  Generate ML Signal                             │
│  └─ get_recent_rounds(20) from cache            │
│  └─ engineer_features(37 features)              │
│  └─ predict() from all models                   │
│  └─ ensemble_signal()                           │
└────────────────┬────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────┐
│  Display Predictions                            │
│  ├─ Individual model predictions                │
│  ├─ Ensemble prediction                         │
│  ├─ Expected value                              │
│  ├─ Model agreement                             │
│  └─ Prediction trend (last 5 rounds)            │
└────────────────┬────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────┐
│  Decision: BET or SKIP                          │
│  (Based on updated predictions)                 │
└─────────────────────────────────────────────────┘
```

---

## Benefits

### 1. **Adaptive Predictions**
- Models respond to recent game patterns
- High multipliers → predictions increase
- Low multipliers → predictions decrease

### 2. **Pattern Recognition**
- Detects volatility changes
- Recognizes hot/cold streaks
- Adapts confidence based on stability

### 3. **Transparent Evolution**
- See how predictions change over time
- Understand model behavior
- Track prediction accuracy

### 4. **No Training Delay**
- No need to retrain models between rounds
- Instant feature recalculation
- Real-time inference

---

## Configuration

### Confidence Threshold

Control when to bet based on confidence:
```python
bot.ml_generator.confidence_threshold = 65.0  # Default: 65%
```

- Higher threshold = More selective (fewer bets, higher confidence)
- Lower threshold = More aggressive (more bets, lower confidence)

### Feature Window

Control how many rounds to analyze:
```python
bot.ml_generator.feature_window = 20  # Default: 20 rounds
```

- Larger window = More historical context (smoother predictions)
- Smaller window = More reactive (responds faster to changes)

---

## Technical Details

### Async CSV Writing

Prevents blocking during predictions:
- [history_tracker.py:54-88](core/history_tracker.py#L54-L88) - Background writer thread
- [history_tracker.py:196-197](core/history_tracker.py#L196-L197) - Non-blocking queue
- Cache updated immediately (line 200-221)

### Cache Invalidation Strategy

Smart cache management:
- Read entire CSV once on startup
- Add new rows to cache in-memory
- No disk read for recent rounds
- File modification time tracking

### Feature Engineering

37 features calculated from last 20 rounds:
1. **Basic stats**: mean, std, max, min, median
2. **Trends**: recent avg vs older avg, increasing streak
3. **Patterns**: low count, high count, volatility
4. **Time-based**: time since last high
5. **Distribution**: percentiles (25th, 50th, 75th)
6. **Entropy**: measure of randomness

---

## Monitoring Prediction Quality

### Expected Value

```
Expected Value: 1.43
```

**Calculation**: `prediction × (confidence / 100)`

**Interpretation**:
- EV > 1.0 = Models expect profit
- EV < 1.0 = Models expect loss
- EV ≈ 1.0 = Break-even expectation

### Model Agreement

```
Model Agreement: HIGH (σ=0.07)
```

**Interpretation**:
- HIGH (σ < 0.5) = Models agree → More reliable
- MEDIUM (0.5 ≤ σ < 1.0) = Some disagreement → Moderate confidence
- LOW (σ ≥ 1.0) = Models disagree → Less reliable

### Prediction Accuracy

Track in CSV:
- `model_prediction` = What model predicted
- `multiplier` = What actually happened
- Compare to calculate accuracy over time

---

## Limitations

**Important**: Aviator uses provably fair RNG. ML models cannot predict truly random outcomes. The system shows:

✅ **What it does:**
- Pattern recognition from historical data
- Confidence scoring based on recent trends
- Adaptive feature engineering
- Real-time data integration

❌ **What it doesn't do:**
- Predict the actual RNG seed
- Guarantee winning predictions
- Beat the house edge mathematically
- Exploit game vulnerabilities

**Use responsibly**: Models show PATTERNS, not PREDICTIONS. Negative R² scores are expected for random data.

---

## Troubleshooting

### Predictions Not Updating

**Check:**
1. Is data being logged? Look for `(added to history)` message
2. Is cache working? Check file modification times
3. Are models loaded? Look for model loading messages at startup

### Stale Predictions

**Solution:**
- Clear cache: Restart bot
- Retrain models: `python train_models.py`
- Check CSV integrity: `python clean_csv.py`

### Duplicate Entries

**Cause**: Multiple logging points
**Solution**: Ensure `log_to_history` parameter is used correctly

---

## Summary

Your bot now has **true real-time ML predictions** that:
- Update every round automatically
- Show prediction evolution trends
- Track model agreement
- Display expected values
- Adapt to changing patterns

Enjoy watching your models learn and adapt in real-time! 🚀
