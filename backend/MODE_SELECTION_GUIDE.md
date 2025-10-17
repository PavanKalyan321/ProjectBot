# Mode Selection Guide

## Overview

The bot now has **two operating modes** to choose from at startup:

1. **BETTING MODE** - Place bets based on ML predictions (default)
2. **OBSERVATION MODE** - Collect data without betting

---

## When to Use Each Mode

### 🎰 BETTING MODE

**Use when:**
- You have at least 20+ rounds of historical data
- Models are trained (ran `train_models.py`)
- You want the bot to place actual bets
- You're comfortable with the risk

**What it does:**
- Generates ML predictions for each round
- Places bets when confidence exceeds threshold
- Executes cashouts at configured timing
- Tracks profit/loss
- Updates history with bet results

**Requirements:**
- Minimum 20 rounds in CSV for predictions
- Trained models in `models/` directory
- Sufficient balance for betting

---

### 📊 OBSERVATION MODE

**Use when:**
- You're starting fresh with no historical data
- You want to build a dataset before betting
- You want to test coordinate setup without risk
- You want to retrain models with more data
- You don't want to place bets yet

**What it does:**
- Observes each round's multiplier
- Logs all data to CSV immediately
- Shows what predictions WOULD be (no betting)
- Displays model confidence (for learning)
- Perfect for data collection

**Benefits:**
- **Zero risk** - No bets placed
- **Fast data collection** - Build history quickly
- **Coordinate validation** - Test setup is working
- **Training preparation** - Get 100+ rounds for model training

---

## Startup Flow

```
Start Bot (python bot_modular.py)
     ↓
Configuration Setup
     ↓
Load/Add Manual History (optional)
     ↓
Set Parameters (stake, cashout, threshold)
     ↓
📍 MODE SELECTION ← YOU ARE HERE
     ↓
┌────────────┬────────────┐
│  Choice 1  │  Choice 2  │
│  BETTING   │ OBSERVATION│
└────────────┴────────────┘
     ↓              ↓
  Run ML Mode   Run Observe Mode
```

---

## Example: Starting with Observation Mode

### Scenario: Fresh Start (No History)

**Step 1: Choose Observation Mode**
```
🎮 OPERATING MODE
════════════════════════════════════════════════

Choose mode:
  1. BETTING MODE - Place bets based on ML predictions
  2. OBSERVATION MODE - Collect data without betting (build history for training)

Note: Models need at least 20 rounds of data before they can make predictions.

Choice (1/2, default: 1): 2

📊 OBSERVATION MODE - Bot will only collect data, no bets will be placed

Press Enter to start...
```

**Step 2: Observe Rounds**
```
🎯 ROUND #001
════════════════════════════════════════════════
  ⏳ Waiting for AWAITING state...
  ✅ AWAITING confirmed
  📝 Checking for previous round...
  ✅ Round observed: 3.45x (saved to history)

  🤖 Generating predictions (no bet will be placed)...

  📊 OBSERVATION ONLY - No bet placed
  🎯 Model would predict: 2.15x
  📈 Confidence: 45.2%
  🎲 Decision would be: SKIP

  ⏳ Waiting for current round to complete...
  ✅ Round complete: 2.67x
```

**Step 3: After 50-100 Rounds**
```
  📈 Progress: 100 rounds collected
  💾 Data saved to: aviator_rounds_history.csv

  [Press Ctrl+C to stop]

⏹️  Observation stopped by user

📊 Total rounds observed: 100
💾 Data saved to: aviator_rounds_history.csv

You can now train models with: python train_models.py
```

**Step 4: Train Models**
```bash
python train_models.py
```

**Step 5: Run in Betting Mode**
```bash
python bot_modular.py
# Choose mode: 1 (BETTING MODE)
```

---

## Example: Betting Mode with History

### Scenario: Have 200+ Rounds, Models Trained

**Step 1: Choose Betting Mode**
```
🎮 OPERATING MODE
════════════════════════════════════════════════

Choose mode:
  1. BETTING MODE - Place bets based on ML predictions
  2. OBSERVATION MODE - Collect data without betting (build history for training)

Note: Models need at least 20 rounds of data before they can make predictions.

Choice (1/2, default: 1): 1

💰 BETTING MODE - Bot will place bets based on ML predictions

Press Enter to start...
```

**Step 2: Bot Analyzes and Bets**
```
🎯 ROUND #001
════════════════════════════════════════════════
  ✅ Previous round: 3.45x (added to history)
  💾 Updated history for real-time predictions

  🤖 Analyzing patterns with latest round data...

  ✅ DECISION: PLACE BET
  💰 Stake: 25
  🎯 Target: 4.5s (~1.68x)
  📊 Ensemble Confidence: 68.3%

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

  💰 Setting stake: 25...
  ✅ Stake set
  💵 Placing bet...
  ✅ Bet placed!

  ⏳ Waiting for game start...
  🚀 Game started!

  ⏱️  CASHOUT COUNTDOWN - TARGET: 4.5s
  ...
```

---

## Features by Mode

| Feature | Betting Mode | Observation Mode |
|---------|--------------|------------------|
| Read round data | ✅ | ✅ |
| Log to CSV | ✅ | ✅ |
| Generate predictions | ✅ | ✅ (display only) |
| Place bets | ✅ | ❌ |
| Execute cashouts | ✅ | ❌ |
| Track profit/loss | ✅ | ❌ |
| Risk money | ⚠️ Yes | ✅ No |
| Build dataset | ✅ | ✅ |
| Show model predictions | ✅ | ✅ |

---

## Typical Workflow

### First Time Setup

```bash
Day 1: Observation Mode (2-3 hours)
  → Collect 100-200 rounds
  → Build aviator_rounds_history.csv

Day 1: Training
  → python train_models.py
  → Models learn patterns

Day 2+: Betting Mode
  → Bot uses trained models
  → Places smart bets
  → Continues learning
```

### Ongoing Usage

```bash
Week 1-2: Betting Mode
  → Collect more data while betting
  → Track performance

Week 3: Retrain
  → python train_models.py
  → Update models with new patterns

Week 4+: Back to Betting
  → Use improved models
```

---

## Tips

### For Observation Mode

1. **Duration**: Run for 50-100 rounds minimum
2. **Best Time**: During active game hours for varied multipliers
3. **Multitasking**: Let it run in background while you do other things
4. **Validation**: Check CSV file periodically to ensure data is being saved

### For Betting Mode

1. **Start Small**: Use minimum stake to test predictions
2. **Monitor First**: Watch first 10-20 rounds before leaving unattended
3. **Check Balance**: Ensure sufficient funds for multiple rounds
4. **Set Limits**: Use max stake to cap risk

---

## Frequently Asked Questions

### Q: Can I switch modes mid-run?

**A:** No, you need to stop the bot (Ctrl+C) and restart to change modes.

### Q: How long should I run Observation Mode?

**A:** Minimum 50 rounds, recommended 100-200 rounds for good training data.

### Q: Do I lose prediction accuracy in Observation Mode?

**A:** No! Models still update in real-time. You can see what they would predict without risking money.

### Q: Can I use Betting Mode with no history?

**A:** The bot will still run but predictions will be poor (need 20+ rounds minimum for any predictions).

### Q: What happens if I have < 20 rounds?

**A:**
- **Betting Mode**: Bot will skip all rounds (confidence will be 0%)
- **Observation Mode**: Bot will collect data until you have 20+ rounds

---

## Quick Reference

| Task | Command |
|------|---------|
| Start bot | `python bot_modular.py` |
| Choose betting | Select `1` at mode prompt |
| Choose observation | Select `2` at mode prompt |
| Stop bot | Press `Ctrl+C` |
| Train models | `python train_models.py` |
| Add manual history | `python add_manual_history.py` |

---

## Code Changes

### Main Entry Point ([bot_modular.py:957-984](bot_modular.py#L957-L984))

```python
# Ask user about betting mode
print("\n🎮 OPERATING MODE")
mode_choice = input("\nChoice (1/2, default: 1): ").strip()

if mode_choice == '2':
    observation_mode = True
    print("📊 OBSERVATION MODE - Bot will only collect data")
else:
    observation_mode = False
    print("💰 BETTING MODE - Bot will place bets")

# Run appropriate mode
if observation_mode:
    bot.run_observation_mode()
else:
    bot.run_ml_mode()
```

### Observation Mode Implementation ([bot_modular.py:425-512](bot_modular.py#L425-L512))

- Observes rounds without betting
- Logs all data to CSV
- Shows predictions (no action taken)
- Displays progress every 10 rounds

---

## Summary

✅ **Mode selection added at startup**
✅ **Observation mode for risk-free data collection**
✅ **Betting mode for ML-powered betting**
✅ **Clear prompts guide user choice**
✅ **Both modes collect data for model improvement**

Choose wisely based on your needs! 🚀
