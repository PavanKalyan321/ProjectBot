# Quick Reference - Project Structure & New Development Guide

## Key Files You'll Work With

### Core ML/Prediction
- `/home/user/ProjectBot/backend/core/ml_models.py` - ML model implementation (36KB)
- `/home/user/ProjectBot/backend/core/ml_signal_generator.py` - Signal generation (26KB)
- `/home/user/ProjectBot/backend/core/position2_rule_engine.py` - Rule-based patterns (18KB)
- `/home/user/ProjectBot/backend/automl_predictor.py` - Ensemble predictor (22KB)

### Dashboard & API
- `/home/user/ProjectBot/backend/dashboard/compact_analytics.py` - Flask server (550+ lines)
- `/home/user/ProjectBot/backend/dashboard/templates/compact_dashboard.html` - UI
- `/home/user/ProjectBot/run_dashboard.py` - Launcher script

### Data & Configuration
- `/home/user/ProjectBot/backend/config/config_manager.py` - Configuration management
- `/home/user/ProjectBot/backend/utils/data_logger.py` - Data logging (async)
- `/home/user/ProjectBot/backend/utils/data_manager.py` - Data cleanup tools
- `/home/user/ProjectBot/backend/core/history_tracker.py` - CSV tracking

### Main Bot Logic
- `/home/user/ProjectBot/backend/bot.py` - Main bot (68KB)
- `/home/user/ProjectBot/backend/bot_modular.py` - Modular bot (83KB)

---

## Database Tables (CSV-Based, No SQL DB)

### 1. aviator_rounds_history.csv
**15 columns** - Game round outcomes with predictions
```
timestamp, round_id, multiplier, bet_placed, stake_amount, cashout_time,
profit_loss, model_prediction, model_confidence,
model_predicted_range_low, model_predicted_range_high,
pos2_confidence, pos2_target_multiplier, pos2_burst_probability,
pos2_phase, pos2_rules_triggered
```

### 2. bet_history.csv
**8 columns** - Betting transaction log
```
Timestamp, Round ID, Final Multiplier, Cashout Multiplier,
Bet Placed, Stake, Profit/Loss, Cumulative P/L
```

### 3. bot_automl_performance.csv
**20+ columns** - Model performance metrics
```
timestamp, round_id, actual_multiplier, ensemble_prediction,
ensemble_range, ensemble_confidence, consensus_range,
consensus_strength, recommendation_should_bet, recommendation_target,
recommendation_risk, prediction_error, range_correct,
model_1_pred ... model_10_pred (individual model predictions)
```

---

## API Endpoints (Port 5001)

### Dashboard Routes
```
GET /                  - Main dashboard HTML
GET /advanced          - Advanced view
GET /logs              - Logs viewer
```

### Data API Routes
```
GET /api/current_round           - Current round data with all 16 model predictions
GET /api/live_stats              - Overall statistics
GET /api/model_comparison        - All 16 models side-by-side
GET /api/trend_signal            - Trend analysis & signals
GET /api/recent_rounds?limit=20  - Historical rounds
GET /api/top_models              - Top 3 performers
GET /api/rules_status            - Position 2 rule status
POST /api/cleanup                - Trigger data cleanup
```

### WebSocket Events
```
connect    - Client connects
disconnect - Client disconnects
request_update - Client requests update

Server Emit:
- initial_data  - Live stats on connect
- live_update   - Real-time round updates
- model_update  - Model performance updates
```

---

## ML Ensemble System

### 16 Models (with Weighted Voting)
1. H2O AutoML (ensemble)
2. Google AutoML (neural)
3. Auto-sklearn (sklearn)
4. LSTM (sequence)
5. AutoGluon (tabular)
6. PyCaret (ensemble)
7. Random Forest (tree)
8. CatBoost (gradient)
9. LightGBM (gradient)
10. XGBoost (gradient)
11. MLP Neural Net (neural)
12. TPOT Genetic (genetic)
13. AutoKeras (keras)
14. Auto-PyTorch (pytorch)
15. MLBox (ensemble)
16. TransmogrifAI (spark)

### Prediction Strategies
- **Position 1**: ML green classifier for 1.5x-2.0x (conservative)
- **Position 2**: Rule-based for 3x+ multipliers (aggressive)
- **Hybrid**: Combines both intelligently

### Position 2 Rules
- R1: Low Green Series (4+ consecutive <2.0x)
- R2: No 20x Gap (extended time without high)
- R3: Post-High Echo (patterns after 10x+)
- R5: Massive Gap (extreme volatility)
- R6: Cluster Series (grouped patterns)
- R7: Series Direction (trending)
- R8: Delayed Spike (buildup)
- R10: Confidence Builder (cumulative strength)

---

## Frontend Components

### Dashboard Sections
1. **Live Stats Bar** - Rounds, win rate, P/L, trend
2. **Current Round** - Actual vs prediction, confidence
3. **Model Grid** - 16 models (4x4), top 3 with medals
4. **Trend & Signals** - ↑↓→ indicators, trading signals
5. **Rules Status** - Rule activation, phase, insights
6. **Recent Rounds Chart** - Line chart of last 20
7. **Data Management** - Cleanup, archive, consolidate

### Update Frequency
- 5-second auto-refresh for main data
- WebSocket for real-time updates
- Half-screen optimized (50% viewport)

---

## Adding New Code - Quick Start

### Add New ML Model
1. File: `/backend/core/ml_models.py`
2. Add class to `AviatorMLModels`
3. Implement `train()` and `predict()` methods
4. Auto-loads on startup

### Add New Dashboard Feature
1. **Frontend**: Edit `/backend/dashboard/templates/compact_dashboard.html`
2. **Backend**: Add route to `/backend/dashboard/compact_analytics.py`
3. Pattern:
```python
@self.app.route('/api/new_feature')
def get_new_feature():
    data = self._get_new_feature_data()
    return jsonify(data)
```

### Add New Logging
1. File: `/backend/utils/data_logger.py`
2. Create new Logger class
3. Implement async write queue pattern
4. Register in centralized logging

### Add New Operating Mode
1. Create: `/backend/modes/new_mode.py`
2. Export: `run_new_mode(bot)` function
3. Import in: `/backend/bot.py`
4. Add to mode selection menu

---

## Configuration

### Runtime Config (JSON)
```
/home/user/ProjectBot/backend/aviator_ml_config.json
```
Contains screen coordinates and betting parameters

### Environment Variables
```
/home/user/ProjectBot/.env (copy from .env.example)
```
BOT_MODE, INITIAL_STAKE, MAX_STAKE, TESSERACT_PATH, etc.

### ConfigManager Class
```
/backend/config/config_manager.py
```
Handles load/save of coordinates and settings

---

## Development Workflow

### Training Models
```bash
cd /home/user/ProjectBot
python backend/train/train_models.py
```
Loads historical CSV, trains, saves to `/backend/models/`

### Running Dashboard
```bash
python run_dashboard.py
# Opens http://localhost:5001
```

### Running Bot
```bash
cd backend
python bot.py
# Interactive mode selection: Live (1), Dry Run (2), Observation (3)
```

### Data Cleanup
```bash
python cleanup_data.py
# Interactive options: Quick, Archive, Consolidate, Full
```

---

## Performance Optimization

- **Async CSV Writing** - Non-blocking file I/O via background threads
- **In-Memory Cache** - Reduces disk reads (with threading lock)
- **Min-Heap Tracking** - Efficient top-20 multiplier tracking
- **Batch Operations** - Reduces system call overhead
- **Threading** - Background operations don't block main loop

---

## Docker Deployment

### Services (docker-compose.yml)
1. **xvfb** - Virtual X display (port 5900 VNC)
2. **dashboard** - Flask server (port 5001)
3. **bot** - Main bot process

### Build & Run
```bash
docker-compose up -d
docker-compose logs -f bot
```

---

## Testing

Location: `/backend/tests/`
Files:
- test_dashboard.py
- test_modules.py
- test_system.py
- test_realistic_timestamps.py

Run:
```bash
pytest backend/tests/
```

---

## Code Statistics

- **Total Lines**: ~8,600 Python
- **Modules**: 15+
- **Core Classes**: 20+
- **CSV Columns**: 50+ total
- **API Routes**: 11
- **ML Models**: 16 ensemble
- **Rules**: 8+ pattern-based

---

## Key Design Patterns

1. **Singleton**: ConfigManager, DataManager
2. **Strategy**: Multiple prediction modes
3. **Observer**: WebSocket listeners
4. **Factory**: Model creation
5. **Queue**: Async write operations
6. **Cache**: In-memory data cache

---

## Documentation Files

- `/home/user/ProjectBot/README.md` - Overview
- `/home/user/ProjectBot/QUICK_START.md` - 60-second start
- `/home/user/ProjectBot/START_BOT_GUIDE.md` - Complete bot guide
- `/home/user/ProjectBot/DASHBOARD_README.md` - Dashboard docs
- `/home/user/ProjectBot/IMPLEMENTATION_SUMMARY.md` - What was built

