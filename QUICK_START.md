# 🚀 Quick Start Guide

## 1️⃣ Install Dependencies (One Time)

```bash
pip install flask flask-socketio pandas numpy
```

## 2️⃣ Start Dashboard (Every Time)

```bash
python run_dashboard.py
```

## 3️⃣ Arrange Your Screen

```
┌─────────────────────┬─────────────────────┐
│                     │                     │
│   AVIATOR GAME      │   DASHBOARD         │
│   (Left Half)       │   (Right Half)      │
│                     │                     │
│                     │   localhost:5001    │
│                     │                     │
└─────────────────────┴─────────────────────┘
```

## 🧹 Cleanup Data (When Needed)

```bash
python cleanup_data.py
```

## 📊 What You'll See

- **Current Round**: Actual vs Predicted multiplier
- **All 16 Models**: Real-time predictions
- **Trend Signal**: ↑ ↓ → with BET/SKIP/WAIT
- **Top 3 Models**: Best performers
- **Rules**: Active patterns detected
- **Recent 20 Rounds**: History + chart

## 🎯 Signal Meanings

- **STRONG_BET** 🎯: High confidence - bet now
- **BET** ✅: Good opportunity
- **OPPORTUNITY** 💡: Consider betting
- **CAUTIOUS** ⚠️: Bet carefully
- **WAIT** ⏸: Wait for better signal
- **SKIP** ⛔: Skip this round

## 🏆 Model Accuracy Colors

- **🟢 Green (80%+)**: Excellent
- **🟡 Yellow (60-80%)**: Good
- **🔴 Red (<60%)**: Poor

## ⚡ Hotkeys

- **F5**: Refresh browser
- **Ctrl+F5**: Hard refresh
- **Ctrl+-**: Zoom out
- **Ctrl++**: Zoom in

## 🆘 Problems?

1. **Dashboard won't start**: Install dependencies
2. **No data showing**: Run `python cleanup_data.py`
3. **Old data**: Choose option 4 in cleanup
4. **Port in use**: Change port in `run_dashboard.py`

## 📖 Full Documentation

See [DASHBOARD_README.md](DASHBOARD_README.md) for complete guide.

---

**That's it! You're ready to go! 🎉**
