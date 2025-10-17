# Data Management Guide

## Single Source of Truth: `aviator_rounds_history.csv`

This is your **main data file** for all round history and ML training.

### CSV Schema (16 columns)

```
timestamp,round_id,multiplier,
bet_placed,stake_amount,cashout_time,
profit_loss,model_prediction,model_confidence,
model_predicted_range_low,model_predicted_range_high,
pos2_confidence,pos2_target_multiplier,pos2_burst_probability,
pos2_phase,pos2_rules_triggered
```

---

## Workflow

### 1. Add Manual History

To add previous round multipliers to your database:

```bash
python add_manual_history.py
```

**Options:**
- **Paste Mode**: Copy/paste multipliers (supports various formats)
- **File Mode**: Load from a text file
- **Skip**: Continue without adding history

**Supported Formats:**
```
2.54 3.45                  # Space-separated
2.54 - 3.45               # With dashes
2.54x 3.45x               # With 'x' suffix
2.54, 3.45                # Comma-separated
2.54                      # One per line
3.45
```

### 2. Train ML Models

After adding history or when you have new data:

```bash
python train_models.py
```

**Requirements:**
- Minimum 100 rounds of data
- Models trained: RandomForest, GradientBoosting, LightGBM (optional: LSTM)
- Models saved to `models/` directory

### 3. Run the Bot

```bash
python bot_modular.py
```

The bot will:
- Automatically load trained models
- Read from `aviator_rounds_history.csv`
- Write new rounds to the same file
- Use ML predictions for decision-making

---

## Data Maintenance

### Clean Corrupted CSV

If you get CSV parsing errors:

```bash
python clean_csv.py
```

This will:
- Create a backup with timestamp
- Remove rows with incorrect column counts
- Validate the cleaned file with pandas

### Fix Header Mismatch

If the CSV header doesn't match the 16-column schema:

```bash
python migrate_csv_header.py
```

This will:
- Backup the original file
- Update header to correct 16-column format
- Verify with pandas

---

## File Structure

```
backend/
├── aviator_rounds_history.csv          # Main data file (16 columns)
├── aviator_rounds_history.csv.backup_* # Auto-generated backups
├── add_manual_history.py               # Add history interactively
├── manual_history_loader.py            # History loading utilities
├── train_models.py                     # Train ML models
├── clean_csv.py                        # Clean corrupted CSV
├── migrate_csv_header.py               # Fix header schema
├── bot_modular.py                      # Main bot
├── core/
│   ├── history_tracker.py              # CSV writing/reading
│   ├── ml_models.py                    # ML model training
│   └── ml_signal_generator.py          # Signal generation
└── models/                             # Trained ML models
    ├── random_forest.pkl
    ├── gradient_boosting.pkl
    ├── lightgbm.pkl
    ├── scaler.pkl
    └── metadata.pkl
```

---

## Common Issues

### Issue: "Expected 11 fields, saw 16"

**Cause:** Header has 11 columns but data rows have 16 columns

**Solution:**
```bash
python migrate_csv_header.py
```

### Issue: "Expected 16 fields, saw X"

**Cause:** Some data rows have incorrect column counts (corruption)

**Solution:**
```bash
python clean_csv.py
```

### Issue: Models have negative R² scores

**Explanation:** This is **expected** for Aviator game data. The game uses provably fair RNG that cannot be predicted. Negative R² means the model performs worse than a simple mean prediction, which is normal for truly random data.

---

## Best Practices

1. **Always backup before cleaning/migrating**
   - Automatic backups are created with timestamps
   - Keep recent backups in case of issues

2. **Add manual history before first training**
   - More historical data = better baseline
   - Minimum 100 rounds required
   - Recommended: 500+ rounds

3. **Retrain models periodically**
   - After collecting significant new data
   - When game patterns change
   - At least once per week if actively betting

4. **Monitor CSV file health**
   - Check for corruption after crashes
   - Verify column counts match schema
   - Clean regularly if bot writes bad data

5. **Keep only one CSV file**
   - Don't split data across multiple files
   - `aviator_rounds_history.csv` is the single source
   - All tools read/write to this file

---

## Quick Reference

| Task | Command |
|------|---------|
| Add history | `python add_manual_history.py` |
| Train models | `python train_models.py` |
| Run bot | `python bot_modular.py` |
| Clean CSV | `python clean_csv.py` |
| Fix header | `python migrate_csv_header.py` |

---

## Data Flow

```
Manual Input → add_manual_history.py → aviator_rounds_history.csv
                                              ↓
                                       train_models.py
                                              ↓
                                       models/*.pkl
                                              ↓
Bot (observation) → history_tracker.py → aviator_rounds_history.csv
                                              ↓
Bot (prediction) ← ml_models.py ← models/*.pkl
```

---

## Notes

- All timestamps use format: `YYYY-MM-DD HH:MM:SS`
- Round IDs use format: `YYYYMMDDHHMMSSffffff` (microseconds)
- Position 2 fields are populated when using Position 2 strategy
- Manual entries have `pos2_phase='manual'` to distinguish them
