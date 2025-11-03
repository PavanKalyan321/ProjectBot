# 🤖 How to Start the Aviator Bot

## Complete Guide: Bot + Dashboard Setup

---

## 🎯 Overview

You have **two main components**:
1. **The Bot** - Automated betting system (backend/bot.py)
2. **The Dashboard** - Analytics visualization (run_dashboard.py)

You can run them:
- **Separately** - Bot in one terminal, dashboard in another
- **Together** - Both running simultaneously (RECOMMENDED)

---

## 🚀 Quick Start (Recommended Method)

### Option A: Bot + Dashboard in Separate Terminals

#### Terminal 1 - Start Dashboard
```bash
cd c:\Project
python run_dashboard.py
```
- Dashboard will open at http://localhost:5001
- Shows real-time analytics

#### Terminal 2 - Start Bot
```bash
cd c:\Project\backend
python bot.py
```
- Bot will start placing bets
- Data feeds into dashboard automatically

---

## 📋 Detailed Bot Startup Guide

### Prerequisites

1. **Install Dependencies**
```bash
pip install flask flask-socketio pandas numpy opencv-python pytesseract mss pyautogui keyboard
```

2. **Install Tesseract OCR**
   - Download from: https://github.com/UB-Mannheim/tesseract/wiki
   - Install to: `C:\Program Files\Tesseract-OCR`
   - Add to PATH

3. **Have Aviator Game Open**
   - Open Aviator in your browser
   - Make sure it's visible on screen

---

## 🎮 Starting the Bot - Step by Step

### Step 1: Open Terminal
```bash
cd c:\Project\backend
```

### Step 2: Run Bot
```bash
python bot.py
```

### Step 3: Choose Operating Mode

You'll see:
```
╔═══════════════════════════════════════════════════════════════╗
║                   🎯 AVIATOR BOT LAUNCHER                     ║
╚═══════════════════════════════════════════════════════════════╝

Select Mode:
  1. 🔴 LIVE MODE     - Real betting with actual money
  2. 🟡 DRY RUN MODE  - Simulation mode (no real bets)
  3. 📊 OBSERVATION   - Data collection only

Enter choice (1/2/3):
```

**Choose:**
- **1** - For real betting (use real money)
- **2** - For testing (simulates bets, no money)
- **3** - For just collecting data (no betting)

### Step 4: Configure Coordinates (First Time Only)

If first time, bot will ask you to set up screen coordinates:

```
📍 COORDINATE SETUP - Click positions when prompted

1. STAKE INPUT BOX
   - Click where you enter bet amount
   - Press 'c' to capture

2. BET BUTTON
   - Click the BET button position
   - Press 'c' to capture

3. CASHOUT BUTTON
   - Click CASHOUT button position
   - Press 'c' to capture

4. MULTIPLIER REGION
   - Click top-left of multiplier display
   - Press 'c' to capture
   - Click bottom-right of multiplier display
   - Press 'c' to capture
```

**Tips:**
- Position your mouse carefully
- Press 'c' when ready
- Coordinates are saved for next time

### Step 5: Bot Settings (If Live or Dry Run Mode)

Bot will ask:
```
Enter initial stake amount (e.g., 25): 25
Enter max stake limit (e.g., 1000): 1000
Enter stake increase % on win (e.g., 20): 20
```

**Recommended Settings:**
- Initial stake: 10-25 (start small)
- Max stake: 1000 (safety limit)
- Increase %: 10-20 (progressive betting)

### Step 6: Bot Starts Running

You'll see:
```
╔═══════════════════════════════════════════════════════════════╗
║                    🎮 BOT IS NOW RUNNING                      ║
╚═══════════════════════════════════════════════════════════════╝

Round #1234 | 10:30:45 AM
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🤖 AutoML Analysis:
   Ensemble Prediction: 2.35x
   Confidence: 78.5%
   Recommended Range: 2.0-2.5x

✅ DECISION: BET
   Target: 2.40x
   Stake: $25.00

📊 Placing bet...
✓ Bet placed successfully
⏳ Monitoring multiplier...
```

---

## 🖥️ Recommended Screen Setup

### Full Setup (3 Windows)

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│  Terminal 1: Bot Running                                    │
│  (Shows bot activity, predictions, results)                 │
│                                                             │
└─────────────────────────────────────────────────────────────┘

┌──────────────────────┬──────────────────────────────────────┐
│                      │                                      │
│  AVIATOR GAME        │  DASHBOARD                           │
│  (Browser)           │  (localhost:5001)                    │
│                      │                                      │
│  Bot interacts here  │  View analytics here                 │
│                      │                                      │
└──────────────────────┴──────────────────────────────────────┘
```

### Compact Setup (2 Windows)

```
┌──────────────────────┬──────────────────────────────────────┐
│                      │                                      │
│  AVIATOR GAME        │  DASHBOARD                           │
│  (Browser)           │  (localhost:5001)                    │
│                      │                                      │
│  + Bot Terminal      │  Real-time stats                     │
│  (minimized below)   │                                      │
│                      │                                      │
└──────────────────────┴──────────────────────────────────────┘
```

---

## 🎯 Operating Modes Explained

### 1. LIVE MODE 🔴
**What it does:**
- Places real bets with actual money
- Interacts with game UI via automation
- Uses AutoML predictions to decide when to bet
- Tracks profit/loss in real-time

**When to use:**
- After testing in Dry Run mode
- When you're confident in the setup
- When you have funds to bet with

**Risks:**
- Real money is used
- Can incur losses
- Requires careful monitoring

### 2. DRY RUN MODE 🟡
**What it does:**
- Simulates betting without real money
- Tracks what would happen if bets were placed
- Tests strategies and predictions
- Shows hypothetical profit/loss

**When to use:**
- First time setup
- Testing new strategies
- Verifying coordinates are correct
- Learning how the bot works

**Benefits:**
- No financial risk
- Test everything safely
- Build confidence

### 3. OBSERVATION MODE 📊
**What it does:**
- Only collects game data
- No betting or simulation
- Records multipliers to CSV
- Builds training data for ML models

**When to use:**
- Building historical dataset
- Improving model accuracy
- Running in background
- No active trading

---

## 🔧 Bot Configuration Files

### Config Location
```
backend/data/aviator_ml_config.json
```

### What's Stored
```json
{
  "stake_coords": [361, 797],
  "bet_button_coords": [370, 912],
  "cashout_coords": [370, 912],
  "multiplier_region": [294, 513, 362, 53],
  "initial_stake": 25,
  "max_stake": 1000,
  "stake_increase_percent": 20
}
```

**To Reconfigure:**
- Delete `aviator_ml_config.json`
- Run bot again
- Go through setup process

---

## 📊 Bot + Dashboard Integration

### How They Work Together

```
┌─────────────────────────────────────────────────────────────┐
│                         BOT (bot.py)                        │
│  - Reads game screen via OCR                                │
│  - Gets AutoML predictions (16 models)                      │
│  - Decides to BET or SKIP                                   │
│  - Places bets & cashouts automatically                     │
│  - Logs everything to CSV files                             │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      │ Writes to CSV files
                      ↓
┌─────────────────────────────────────────────────────────────┐
│                     CSV DATA FILES                          │
│  - aviator_rounds_history.csv                               │
│  - bet_history.csv                                          │
│  - bot_automl_performance.csv                               │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      │ Reads from CSV files
                      ↓
┌─────────────────────────────────────────────────────────────┐
│                   DASHBOARD (Flask)                         │
│  - Loads data from CSV files                                │
│  - Displays real-time analytics                             │
│  - Shows all 16 model predictions                           │
│  - Trend analysis & signals                                 │
│  - Auto-refreshes every 5 seconds                           │
└─────────────────────────────────────────────────────────────┘
```

### Data Flow Timeline

```
Second 0:  Bot detects new round
Second 1:  Bot gets AutoML predictions
Second 2:  Bot decides and places bet
Second 3:  Bot monitors multiplier
Second 4:  Bot cashouts at target
Second 5:  Bot logs result to CSV
Second 6:  Dashboard reads updated CSV
Second 7:  Dashboard shows new data
```

---

## ⚡ Quick Commands Reference

### Start Everything
```bash
# Terminal 1 - Dashboard
python run_dashboard.py

# Terminal 2 - Bot
cd backend
python bot.py
```

### Stop Everything
- Press `Ctrl+C` in each terminal

### Cleanup Data Before Starting
```bash
python cleanup_data.py
# Choose option 4 (Full Optimization)
```

### Reconfigure Bot Coordinates
```bash
cd backend
del data\aviator_ml_config.json
python bot.py
```

---

## 🛠️ Troubleshooting

### Issue: Bot won't start
**Solution:**
```bash
pip install opencv-python pytesseract mss pyautogui keyboard
```

### Issue: Bot can't read multiplier
**Possible causes:**
1. Tesseract not installed
2. Wrong screen coordinates
3. Game window not visible

**Solution:**
1. Install Tesseract OCR
2. Reconfigure coordinates (delete config file)
3. Make sure game is visible on screen

### Issue: Bot not placing bets
**Check:**
1. Are you in LIVE or DRY RUN mode?
2. Is "use_automl_predictions" enabled?
3. Are coordinates correct?
4. Is game window active?

**Solution:**
- Verify mode selection
- Reconfigure coordinates
- Check terminal for error messages

### Issue: Dashboard shows no data
**Solution:**
```bash
# Run bot first to generate data
cd backend
python bot.py

# Let it run for a few rounds
# Then start dashboard
python run_dashboard.py
```

### Issue: Bot keeps skipping rounds
**Cause:** AutoML confidence too low or predictions unfavorable

**Solution:**
- This is normal behavior
- Bot only bets when confident
- Let more data accumulate
- Models improve over time

---

## 📈 Monitoring Bot Performance

### What to Watch in Terminal
```
✅ Good Signs:
   - "Bet placed successfully"
   - "Cashout successful"
   - "Win! Profit: +$X"
   - Confidence levels > 70%

⚠️ Warning Signs:
   - "Failed to place bet"
   - "Cashout button not found"
   - Repeated skips (low confidence)
   - High error rates

❌ Error Signs:
   - "OCR failed to read multiplier"
   - "Cannot find game window"
   - Python exceptions/tracebacks
```

### What to Watch in Dashboard
```
✅ Good Performance:
   - Win rate > 60%
   - Profit/Loss positive
   - Model accuracy > 80%
   - Low prediction errors

📊 Monitor These:
   - Current streak
   - Top model performance
   - Trend signals (↑↓→)
   - Rules activation

⚠️ Red Flags:
   - Win rate < 40%
   - Consistent losses
   - Model accuracy < 60%
   - High volatility without adaptation
```

---

## 🎯 Best Practices

### Before Starting Bot
1. ✅ Clean your data (`python cleanup_data.py`)
2. ✅ Test coordinates in Dry Run mode first
3. ✅ Start with small stakes (10-25)
4. ✅ Set reasonable max stake (1000)
5. ✅ Have Aviator game visible on screen

### While Bot is Running
1. 👀 Monitor terminal output
2. 📊 Check dashboard periodically
3. 🛑 Stop if error rate high
4. 💰 Watch your bankroll
5. ⏸️ Take breaks (don't run 24/7)

### After Session
1. 📈 Review performance in dashboard
2. 🧹 Run data cleanup if needed
3. 📊 Analyze which models performed best
4. 📝 Note any patterns or issues
5. 🔄 Adjust strategy if needed

---

## 🚦 Recommended First-Time Flow

### Day 1: Setup & Testing
```bash
# 1. Cleanup data
python cleanup_data.py

# 2. Start in Observation mode
cd backend
python bot.py
# Choose option 3 (Observation)
# Let run for 20-30 rounds

# 3. Start dashboard
python run_dashboard.py
# View collected data
```

### Day 2: Dry Run Testing
```bash
# 1. Start in Dry Run mode
cd backend
python bot.py
# Choose option 2 (Dry Run)
# Configure coordinates carefully
# Let run for 50-100 rounds

# 2. Monitor in dashboard
# Check prediction accuracy
# Verify bot behavior
```

### Day 3: Live Trading (If Results Good)
```bash
# 1. Start with small stakes
cd backend
python bot.py
# Choose option 1 (Live)
# Initial stake: 10
# Max stake: 100
# Monitor closely!

# 2. Watch dashboard closely
# Stop if losses exceed tolerance
```

---

## 🎉 You're Ready!

### To Start Bot + Dashboard:

**Terminal 1:**
```bash
python run_dashboard.py
```

**Terminal 2:**
```bash
cd backend
python bot.py
```

**Choose mode → Configure (first time) → Let it run!**

---

## 📚 Related Documentation

- **[QUICK_START.md](QUICK_START.md)** - Dashboard quick start
- **[DASHBOARD_README.md](DASHBOARD_README.md)** - Complete dashboard guide
- **[VISUAL_GUIDE.txt](VISUAL_GUIDE.txt)** - Visual reference

---

## ⚠️ Important Reminders

1. **Financial Risk**: Bot uses real money in LIVE mode
2. **No Guarantees**: ML predictions are probabilistic, not guaranteed
3. **Monitoring Required**: Don't leave unattended for long periods
4. **Test First**: Always test in Dry Run before going live
5. **Start Small**: Begin with minimal stakes
6. **Legal Compliance**: Ensure automated betting is allowed in your jurisdiction

---

## 🆘 Need Help?

**Bot won't start?**
→ Check dependencies: `pip list | grep -E "opencv|pytesseract|mss|pyautogui"`

**Coordinates wrong?**
→ Delete config: `del backend\data\aviator_ml_config.json`

**No data in dashboard?**
→ Run bot first to generate data

**Bot keeps losing?**
→ Try Dry Run mode, analyze patterns, adjust strategy

---

## 🎯 Quick Recap

```
START BOT:     cd backend && python bot.py
START DASHBOARD:     python run_dashboard.py
CLEANUP DATA:        python cleanup_data.py
RESET CONFIG:        del backend\data\aviator_ml_config.json

MODES:
  1 = Live (real money)
  2 = Dry Run (simulation)
  3 = Observation (data only)
```

**That's everything! Happy trading! 🚀**
