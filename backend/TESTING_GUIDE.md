# Testing Guide

## Overview

This guide explains how to test all components of the Aviator Bot system to ensure everything is working correctly.

---

## Quick Test (Recommended)

### Run the System Test Suite

```bash
cd backend
python test_system.py
```

**What it tests:**
- ✅ All Python imports and dependencies
- ✅ File structure and required files
- ✅ CSV operations and data integrity
- ✅ History tracker functionality
- ✅ ML models and predictions
- ✅ Signal generator
- ✅ Dashboard components
- ✅ Utility scripts
- ✅ Configuration system

**Expected Output:**
```
╔══════════════════════════════════════════════════════════════════════════════╗
║                    AVIATOR BOT - SYSTEM TEST SUITE                           ║
╚══════════════════════════════════════════════════════════════════════════════╝

================================================================================
  1. TESTING IMPORTS
================================================================================

  ► Import pandas... ✓ PASS
  ► Import numpy... ✓ PASS
  ► Import scikit-learn... ✓ PASS
  ► Import Flask... ✓ PASS
  ► Import Flask-SocketIO... ✓ PASS
  ...

================================================================================
  TEST SUMMARY
================================================================================

  Total tests:     42
  ✓ Passed:        42
  ✗ Failed:        0
  Time elapsed:    3.45s

✓ ALL TESTS PASSED! System is ready.
```

---

## Dashboard Test (Simulated Data)

### Test the Dashboard Without Real Game

```bash
python test_dashboard.py
```

**What it does:**
- Starts a test web server on port 5000
- Simulates game rounds every 5 seconds
- Generates fake multipliers and model predictions
- Updates dashboard in real-time

**Expected Output:**
```
================================================================================
  DASHBOARD TEST - Simulated Data Mode
================================================================================

✓ Test server starting...
✓ Simulating game rounds every 5 seconds
✓ Dashboard available at:
  - Basic:    http://localhost:5000
  - Advanced: http://localhost:5000/advanced

Press Ctrl+C to stop

Round 1: 2.34x | Pred: 2.45x | Bet: Yes | P/L: +40.00
Round 2: 1.12x | Pred: 1.23x | Bet: No  | P/L: +40.00
Round 3: 3.67x | Pred: 3.52x | Bet: Yes | P/L: +80.00
...
```

**How to test:**
1. Run `python test_dashboard.py`
2. Open browser to `http://localhost:5000/advanced`
3. Watch metrics and charts update every 5 seconds
4. Verify all 6 metrics update
5. Verify all 4 charts populate with data
6. Press Ctrl+C to stop

---

## Individual Component Tests

### 1. Test CSV Operations

```bash
python clean_csv.py
```

**Verifies:**
- CSV file exists and is readable
- Correct column count (16 columns)
- No corrupted rows
- Data integrity

**Expected:**
```
================================================================================
CSV CLEANING UTILITY
================================================================================
Input file: aviator_rounds_history.csv
Backup file: aviator_rounds_history.csv.backup_20251017_150030
[OK] Backup created

[INFO] Analysis:
   Expected columns: 16
   Valid lines: 1912
   Invalid lines: 0

[OK] Cleaned data written to: aviator_rounds_history.csv
[OK] Verification: Pandas can read 1912 rows successfully

================================================================================
CLEANING COMPLETE
================================================================================
```

---

### 2. Test Model Training

```bash
python train_models.py
```

**Verifies:**
- CSV can be loaded
- Feature engineering works
- Models can be trained
- Models can be saved

**Expected:**
```
================================================================================
AVIATOR ML MODEL TRAINING
================================================================================

================================================================================
TRAINING ML MODELS
================================================================================
[OK] Loaded 1914 rounds from aviator_rounds_history.csv
[OK] After cleaning: 1682 valid rounds
[OK] Engineered 37 features from 1662 samples

Training Set: 1329 samples
Test Set: 333 samples

Target Range: 0.20x - 6060.00x
Target Mean: 14.85x | Std: 165.41x

--------------------------------------------------------------------------------
1. Training Random Forest...
   [OK] R2 Score: -0.4131

2. Training Gradient Boosting...
   [OK] R2 Score: -0.3950

3. Training LightGBM...
   [OK] R2 Score: -0.6136

[OK] Models saved to models/

================================================================================
MODEL TRAINING COMPLETE
================================================================================

SUCCESS!
```

---

### 3. Test Manual History Addition

```bash
python add_manual_history.py
```

**What it tests:**
- Manual history input system
- CSV writing with correct schema
- Data validation

**How to test:**
1. Choose option 1 (Paste mode)
2. Enter test multipliers:
   ```
   2.5
   3.2
   1.8
   4.5
   ```
3. Press Enter twice
4. Check output confirms 4 multipliers saved

---

### 4. Test Bot Initialization (Dry Run)

```bash
python bot_modular.py
```

**What to test:**
- Configuration loading
- Component initialization
- Mode selection prompt
- Choose "Observation Mode" for safe testing

**Expected:**
```
================================================================================
✈️  AVIATOR BOT - ML MODE WITH ENHANCED LOGGING
================================================================================

🎯 Features:
  ✓ Manual history input for better predictions
  ✓ Individual model predictions
  ✓ Enhanced cashout progress indicator
  ✓ Detailed round-by-round logging

✓ Config loaded

Options:
  1. Use existing config
  2. New setup
  3. Exit

Choice (1/2/3): 1

🎮 OPERATING MODE
════════════════════════════════════════════════

Choose mode:
  1. BETTING MODE - Place bets based on ML predictions
  2. OBSERVATION MODE - Collect data without betting

Choice (1/2, default: 1): 2

📊 OBSERVATION MODE - Bot will only collect data

Press Enter to start...
```

---

## Common Test Scenarios

### Scenario 1: Fresh Installation

**Steps:**
```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run system tests
python test_system.py

# 3. Expected failures (OK):
#    - No trained models
#    - Empty/missing CSV (will be created)

# 4. Create initial CSV structure
python migrate_csv_header.py

# 5. Add some test data
python add_manual_history.py

# 6. Train models
python train_models.py

# 7. Test dashboard
python test_dashboard.py

# 8. Rerun system tests
python test_system.py  # Should now pass all tests
```

---

### Scenario 2: After Code Updates

**Steps:**
```bash
# 1. Run system tests
python test_system.py

# 2. If CSV tests fail:
python clean_csv.py
python migrate_csv_header.py

# 3. If model tests fail:
python train_models.py

# 4. Test dashboard
python test_dashboard.py

# 5. Quick bot test (observation mode)
python bot_modular.py
# Choose: Observation Mode
# Run for 5-10 rounds
# Press Ctrl+C
```

---

### Scenario 3: CSV Corruption Issues

**Steps:**
```bash
# 1. Run CSV cleaner
python clean_csv.py

# 2. Check output for errors
# 3. If header mismatch:
python migrate_csv_header.py

# 4. Verify with system test
python test_system.py
# Focus on "TESTING CSV OPERATIONS" section
```

---

### Scenario 4: Dashboard Not Updating

**Steps:**
```bash
# 1. Test with simulated data
python test_dashboard.py

# 2. Open browser to:
http://localhost:5000/advanced

# 3. Check browser console (F12) for errors

# 4. Verify:
#    - Metrics update every 5 seconds
#    - Charts populate with data
#    - WebSocket connection active (green dot)

# 5. If working with test data but not with bot:
#    - Check bot is emitting round_update events
#    - Verify signal contains 'models' key
```

---

## Automated Test Checklist

Use this checklist before deploying or after major changes:

```
[ ] System test passes (python test_system.py)
[ ] Dashboard test works (python test_dashboard.py)
[ ] CSV can be read without errors
[ ] Models can be trained
[ ] Bot starts without errors
[ ] Observation mode runs for 10 rounds successfully
[ ] Dashboard updates in real-time
[ ] All 6 metrics display correctly
[ ] All 4 charts populate with data
[ ] Configuration persists across restarts
```

---

## Troubleshooting Test Failures

### Import Errors

**Problem:** `✗ FAIL - Cannot import pandas`

**Solution:**
```bash
pip install pandas numpy scikit-learn flask flask-socketio
# Or
pip install -r requirements.txt
```

---

### File Not Found Errors

**Problem:** `✗ FAIL - File not found: core/ml_models.py`

**Solution:**
- Ensure you're running tests from `backend/` directory
- Check file actually exists
- Verify file paths in test script

---

### CSV Errors

**Problem:** `✗ FAIL - Cannot read CSV: ParserError`

**Solution:**
```bash
python clean_csv.py
python migrate_csv_header.py
```

---

### Model Loading Errors

**Problem:** `⚠ SKIP (no trained models)`

**Solution:**
```bash
# This is OK if you haven't trained models yet
python train_models.py
```

---

### Dashboard Template Errors

**Problem:** `✗ FAIL - Template not found`

**Solution:**
- Check `dashboard/templates/advanced_dashboard.html` exists
- Verify Flask template folder path
- Restart test

---

## Performance Benchmarks

Expected performance on typical hardware:

| Test Suite | Duration | CPU | Memory |
|------------|----------|-----|---------|
| System Tests | 3-5s | Low | 100MB |
| Dashboard Test | Ongoing | Low | 150MB |
| CSV Clean | 1-3s | Low | 50MB |
| Model Training | 10-30s | High | 500MB |
| Bot (Observation) | Ongoing | Low | 200MB |

---

## Continuous Testing

### Daily Checks
```bash
# Quick health check
python test_system.py
```

### Weekly Checks
```bash
# Full system validation
python test_system.py
python test_dashboard.py
python train_models.py
```

### After Updates
```bash
# Complete test cycle
python test_system.py
python clean_csv.py
python train_models.py
python test_dashboard.py
```

---

## Test Coverage

### What's Tested
- ✅ All imports and dependencies
- ✅ File structure
- ✅ CSV read/write operations
- ✅ Data integrity
- ✅ History tracker methods
- ✅ ML model initialization
- ✅ Feature engineering
- ✅ Signal generation
- ✅ Dashboard template
- ✅ Configuration management

### What's NOT Tested
- ❌ Actual game coordinates detection
- ❌ Bet placement (requires game)
- ❌ Cashout execution (requires game)
- ❌ Real-time clipboard reading
- ❌ Browser automation (PyAutoGUI)

**Note:** These require actual game connection and are tested during live operation.

---

## Summary

### Quick Test Commands

```bash
# Full system test
python test_system.py

# Dashboard test
python test_dashboard.py

# CSV health check
python clean_csv.py

# Retrain models
python train_models.py
```

### Expected Results

**All tests passing:**
```
✓ ALL TESTS PASSED! System is ready.
```

**Some failures:**
```
⚠ X test(s) failed (YY% passed)
```
→ Check failure details and follow troubleshooting guide

---

## Getting Help

If tests fail and you can't resolve:

1. Check the specific error message
2. Review [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
3. Run with verbose output: `python test_system.py -v`
4. Check log files in `backend/` directory
5. Verify all dependencies installed correctly

---

**Happy Testing!** 🧪✅
