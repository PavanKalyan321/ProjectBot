# 🤖 Bot Monitoring Guide

## Setup Complete! ✅

Your bot now has **dual-output logging** - everything displays on your terminal AND saves to a log file that I can monitor.

---

## 🚀 How to Start the Bot

### Step 1: Open Your Terminal
```bash
cd backend
python bot.py
```

### Step 2: Configure the Bot
When prompted, use these settings:

1. **Mode Selection**:
   - `1` = LIVE (real bets)
   - `2` = DRY RUN (testing, recommended first!)
   - `3` = OBSERVATION (no bets)

2. **Coordinates**: `1` (Use existing)

3. **Settings**:
   - Initial stake: `25`
   - Max stake: `1000`
   - Target multiplier: `2.0` (ML will adjust)
   - Use AutoML: `y` (YES)
   - Model selection: `1` (All models)

4. **Confirm**: Type `yes` to start

---

## 👁️ Monitoring Options

### **Option A: You Monitor in Terminal**
- You'll see everything live in your terminal
- All output is ALSO saved to a log file automatically
- Log file format: `bot_session_YYYYMMDD_HHMMSS.log`

### **Option B: I Monitor the Log File**
Run this command in a SECOND terminal window:
```bash
cd backend
python monitor_bot.py
```

This will:
- Show the last 30 lines of the log
- Stream new updates in real-time
- Highlight important events (bets, wins, losses)

### **Option C: Both of Us Monitor**
- **You**: Watch the main terminal where bot runs
- **Me**: I'll periodically check the log file and analyze

---

## 📊 What Gets Logged

Everything you see in terminal is saved, including:

✅ **ML Predictions & Recommendations**
```
🤖 AUTOML MODEL PREDICTIONS (Recent Focus)
Model Name           Multiplier    Range        Confidence
H2O AutoML          2.50x         2.0-2.5x     68.50%
```

✅ **Betting Decisions**
```
🤖 ML Recommendation: PLACE BET ✅
   ML Target: 2.50x → Adjusted Target: 2.13x
   Confidence: 68.5%
   Risk Level: MEDIUM
```

✅ **Balance Tracking**
```
📊 Balance before cashout: 970.00
📊 Balance after cashout: 1030.00
📊 Change: +60.00 | Expected: +60.00
📊 Stake: 30.00 | Multiplier: 2.00x
✅ Balance validation: WIN confirmed (+60.00)
```

✅ **Round Results**
```
🎮 ROUND #001
💥 Round ended at 2.50x (observed)
✅ WIN: +60.00 (cashed out at 2.00x, round ended at 2.50x)
```

✅ **Statistics**
```
📊 FINAL STATISTICS
Rounds played:     10
Wins:              7
Losses:            3
Net profit:        +150.00
Win rate:          70.0%
```

---

## 🔍 What I'll Monitor For

When you run the bot, I can check the log file for:

1. **Are bets being placed?**
   - Looking for "ML Recommendation: PLACE BET"
   - If seeing only "SKIP BET", thresholds might be too high

2. **Is balance validation working?**
   - Checking balance before/after comparison
   - Making sure wins are detected correctly

3. **Are ML predictions accurate?**
   - Comparing predicted vs actual multipliers
   - Tracking prediction errors

4. **Any errors or issues?**
   - Watching for exceptions
   - Coordinate reading problems
   - Balance reading failures

---

## 📁 Log File Locations

After running, you'll find:

- **Session Log**: `backend/bot_session_YYYYMMDD_HHMMSS.log`
- **Bet History**: `backend/bet_history.csv`
- **Performance**: `backend/bot_automl_performance.csv`
- **Round History**: `backend/aviator_rounds_history.csv`

---

## 🆘 Quick Commands

### Check Latest Log File
```bash
# Windows
type backend\bot_session_*.log | more

# View last 50 lines
powershell -Command "Get-Content backend\bot_session_*.log -Tail 50"
```

### Find Current Session
```bash
cd backend
dir /O-D bot_session_*.log
```

---

## ✨ Ready to Start!

1. **Open Terminal 1**: Run `python bot.py`
2. **Open Terminal 2** (optional): Run `python monitor_bot.py`
3. **I'll monitor**: The log file automatically

Let me know when you start it, and I'll begin monitoring! 🚀
