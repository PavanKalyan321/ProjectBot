# Manual History Guide

## Where Manual Histories Go

When you add previous round histories manually, they follow this flow:

### 1. **Input Sources**
You can input manual histories in two ways:
- **Paste Mode**: Paste multipliers directly (space-separated, comma-separated, or one per line)
- **File Mode**: Load from a text file containing multipliers

### 2. **Saved to CSV** (`aviator_rounds_history.csv`)
Manual entries are saved to the **same CSV file** as automated rounds:
- File: `backend/aviator_rounds_history.csv`
- Format: Same 16-column schema as automated entries
- Marked: `pos2_phase` field set to `'manual'` to identify them

Example row:
```csv
timestamp,round_id,multiplier,bet_placed,stake_amount,cashout_time,profit_loss,model_prediction,model_confidence,model_predicted_range_low,model_predicted_range_high,pos2_confidence,pos2_target_multiplier,pos2_burst_probability,pos2_phase,pos2_rules_triggered
2025-10-18 12:30:45,20251018123045123456,2.54,False,0,0,0,0,0,0,0,0,0,0,manual,
```

### 3. **Loaded into Memory Cache**
The entries are loaded into:
- **RoundHistoryTracker's in-memory cache**: For fast access during predictions
- **Local history buffer**: For immediate availability

### 4. **Used by ML Models**
The manual history affects predictions through:
- **Feature engineering**: Used as input features for ML models
- **Pattern detection**: Helps identify cold streaks, burst patterns, etc.
- **Green classifier**: Improves probability calculations for hitting targets

---

## How Manual History Affects the Bot

### ✅ **Immediate Effects**

1. **Better Pattern Recognition**
   - More historical data = better pattern detection
   - Helps identify cold streaks (many low rounds)
   - Detects burst patterns (recent high multipliers)

2. **Improved ML Predictions**
   - Position 1 (Green Classifier): Uses recent history to calculate probability
   - Position 2 (Rule-based): Analyzes last 10 rounds for patterns
   - Both strategies benefit from more context

3. **More Accurate Confidence Scores**
   - ML models have more data points to analyze
   - Statistical calculations are more reliable
   - Skip decisions are better informed

### 📊 **Example Impact**

**Without Manual History (20 rounds)**:
```
Position 1 (1.5x): 42.3% confidence - SKIP (need 55%)
Position 2: 4/10 low rounds - SKIP (need 7+)
Decision: SKIP - Not enough pattern data
```

**With Manual History (200 rounds)**:
```
Position 1 (1.5x): 58.2% confidence - BET ✓
Position 2: 8/10 low rounds - BET at 3.0x target
Decision: BET - Strong cold streak pattern detected
```

---

## When to Add Manual History

### ✅ **Good Times to Add**:
1. **Bot startup** - Load previous session's rounds
2. **After breaks** - Add rounds that occurred while bot was off
3. **Initial setup** - Bootstrap with historical data for better first predictions

### ⚠️ **Important Notes**:

1. **Timestamp Issues**
   - All manual entries get the CURRENT timestamp
   - They're not time-aware (can't tell if they happened hours ago)
   - Order matters more than timestamps

2. **No Duplicate Detection**
   - Manual entries are NOT checked against existing data
   - You can accidentally create duplicates
   - **Solution**: Our `clean_duplicates.py` script removes them

3. **Quantity Matters**
   - ML models need at least **20 rounds** to make predictions
   - **50-100 rounds** for decent pattern recognition
   - **200+ rounds** for reliable predictions

---

## How Manual vs Automated Entries Differ

| Feature | Manual Entry | Automated Entry |
|---------|-------------|-----------------|
| **Source** | User input | Clipboard/OCR |
| **Timestamp** | Current time | Actual round time |
| **Bet Info** | All zeros | Actual bet data |
| **Marked As** | `pos2_phase='manual'` | `pos2_phase` varies |
| **Used by ML** | ✅ Yes | ✅ Yes |
| **Used by Stats** | ⚠️ Limited | ✅ Full stats |

---

## Potential Issues with Manual History

### 1. **Timestamp Clustering**
All manual entries added at once get nearly identical timestamps:
```
2025-10-18 12:30:45  <- Entry 1
2025-10-18 12:30:45  <- Entry 2
2025-10-18 12:30:45  <- Entry 3
```

**Impact**: Time-based analysis may be less accurate

### 2. **Duplicate Risk**
If you add the same data twice:
```
Round 1: 2.54x (manual)
Round 2: 2.54x (manual, duplicate!)
```

**Solution**: Run `python clean_duplicates.py` to remove duplicates

### 3. **No Validation**
Manual entries are not validated against game rules:
- Can add impossible multipliers (e.g., 0.5x)
- Can add unrealistic values (e.g., 9999.99x)
- Parser accepts 0.01x to 10000x range

---

## Best Practices

### ✅ **DO**:
1. Add manual history at bot startup for context
2. Keep manual entries to recent rounds (last hour or so)
3. Use clean, well-formatted data
4. Run duplicate cleaning after bulk manual imports

### ❌ **DON'T**:
1. Add the same data multiple times
2. Mix old and new data randomly
3. Add unrealistic multipliers
4. Rely solely on manual data (mix with automated)

---

## Example Usage Flow

```
1. Bot Starts
   ↓
2. Asks: "Add manual history?" → YES
   ↓
3. User pastes: "1.54 2.34 3.21 ..."
   ↓
4. Parser extracts: [1.54, 2.34, 3.21, ...]
   ↓
5. Saved to: aviator_rounds_history.csv
   ↓
6. Loaded into: RoundHistoryTracker cache
   ↓
7. ML models use data for predictions
   ↓
8. Bot makes better-informed betting decisions
```

---

## Verification

To check if manual history was loaded correctly:

```bash
python -c "
import pandas as pd
df = pd.read_csv('aviator_rounds_history.csv')
manual = df[df['pos2_phase'] == 'manual']
print(f'Manual entries: {len(manual)}')
print(f'Total entries: {len(df)}')
"
```

---

## Summary

**Manual history entries**:
- ✅ Go into the same CSV as automated entries
- ✅ Are used by ML models for predictions
- ✅ Help with pattern detection and confidence scores
- ✅ Improve decision-making when sufficient data exists
- ⚠️ Have current timestamps (not actual occurrence time)
- ⚠️ Can create duplicates if added multiple times
- ⚠️ Should be cleaned periodically with `clean_duplicates.py`

**Bottom line**: Manual history is a valuable tool for bootstrapping the bot with context, but should be used carefully to avoid duplicates and data quality issues.
