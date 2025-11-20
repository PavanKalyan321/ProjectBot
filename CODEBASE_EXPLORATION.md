# Aviator Bot - Comprehensive Codebase Exploration Summary

## Executive Summary

This is an **Aviator betting bot** with real-time analytics dashboard, built on a Python-based ML ensemble system. The project contains ~8,600 lines of Python code organized into modular components for game automation, prediction, monitoring, and visualization.

---

## 1. TECHNOLOGY STACK

### Backend Framework
- **Python 3.9+** - Primary language
- **Flask + Flask-SocketIO** - Web server & real-time WebSocket support
- **Jinja2** - Template engine for HTML rendering

### Machine Learning & Data Processing
- **scikit-learn** - Random Forest, Gradient Boosting, Standard Scaler
- **pandas** - Data analysis and CSV handling
- **numpy** - Numerical computations
- **LightGBM** (optional) - Gradient boosting alternative
- **TensorFlow/Keras** (optional) - LSTM and neural network models
- **PyTorch** (optional) - Deep learning support

### Computer Vision & Automation
- **OpenCV (cv2)** - Image processing and screen capture analysis
- **pytesseract** - Optical Character Recognition (OCR)
- **mss** - Fast multi-platform screen capture
- **pyautogui** - Mouse/keyboard automation
- **keyboard** - Cross-platform keyboard control
- **pyperclip** - Clipboard interaction

### Frontend
- **HTML5 + CSS3** - UI markup and styling
- **JavaScript (Vanilla)** - Client-side logic
- **WebSocket** - Real-time server communication

### Deployment
- **Docker + Docker Compose** - Containerization
- **Xvfb (X Virtual Framebuffer)** - Virtual display for headless environments
- **VNC** - Remote desktop access (port 5900)

### Configuration & Environment
- **python-dotenv** - Environment variable management
- **JSON** - Configuration file storage
- **CSV** - Data persistence

---

## 2. DATABASE SCHEMA & DATA TABLES

### Primary Data Files (CSV-based)

#### **aviator_rounds_history.csv**
Game round outcomes - the foundation of all predictions
```
Columns:
- timestamp (ISO format)
- round_id (unique identifier)
- multiplier (final game multiplier)
- bet_placed (boolean)
- stake_amount (bet size)
- cashout_time (when cashout occurred)
- profit_loss (P/L for the round)
- model_prediction (ML ensemble prediction)
- model_confidence (0-100 confidence score)
- model_predicted_range_low/high (range prediction)
- pos2_confidence (Position2 rule confidence)
- pos2_target_multiplier (Position2 target)
- pos2_burst_probability (0-1 probability)
- pos2_phase (cool-down, building, burst)
- pos2_rules_triggered (list of rules that fired)
```

#### **bet_history.csv**
Betting transaction log
```
Columns:
- Timestamp (datetime)
- Round ID (unique identifier)
- Final Multiplier (outcome)
- Cashout Multiplier (if bet placed)
- Bet Placed (yes/no)
- Stake (amount wagered)
- Profit/Loss (result)
- Cumulative P/L (running total)
```

#### **bot_automl_performance.csv**
ML model performance metrics
```
Columns:
- timestamp (when prediction was made)
- round_id (associated round)
- actual_multiplier (ground truth outcome)
- ensemble_prediction (ensemble model output)
- ensemble_range (predicted min/max)
- ensemble_confidence (0-100)
- consensus_range (agreement across models)
- consensus_strength (1-10 scale)
- recommendation_should_bet (boolean)
- recommendation_target (target multiplier)
- recommendation_risk (LOW/MEDIUM/HIGH)
- prediction_error (|predicted - actual|)
- range_correct (if actual within predicted range)
- model_1_pred through model_10_pred (individual model outputs)
```

#### **aviator_history.csv** (Legacy)
Simple historical data
```
Columns:
- timestamp
- multiplier
- source (screen, manual_input)
```

### Configuration Files (JSON)

#### **aviator_ml_config.json**
Runtime configuration stored locally
```json
{
  "stake_coords": [x, y],
  "bet_button_coords": [x, y],
  "cashout_coords": [x, y],
  "multiplier_region": [x, y, width, height],
  "balance_region": [x1, y1, x2, y2],
  "history_region": [x, y, width, height],
  "cashout_delay": 2.0,
  "initial_stake": 25,
  "max_stake": 1000,
  "stake_increase_percent": 20,
  "safety_margin": 0.9
}
```

---

## 3. CURRENT PREDICTION & MONITORING SYSTEMS

### A. AutoML Ensemble Predictor (16 Models)

**Location:** `/home/user/ProjectBot/backend/automl_predictor.py`

The system uses an ensemble of 16 different ML models with weighted voting:

1. **H2O AutoML** - Ensemble approach (balanced focus)
2. **Google AutoML** - Neural network (trend focus)
3. **Auto-sklearn** - AutoML framework (recent data focus)
4. **LSTM Model** - Sequence prediction (sequence focus)
5. **AutoGluon** - Tabular AutoML (stable focus)
6. **PyCaret** - Ensemble wrapper (conservative)
7. **Random Forest** - Tree ensemble (weighted)
8. **CatBoost** - Categorical boosting (volatility)
9. **LightGBM** - Gradient boosting (distribution)
10. **XGBoost** - Extreme gradient boosting (median)
11. **MLP Neural Net** - Multi-layer perceptron (pattern)
12. **TPOT Genetic** - Genetic algorithm (optimal)
13. **AutoKeras** - AutoML for Keras (deep learning)
14. **Auto-PyTorch** - PyTorch AutoML (adaptive)
15. **MLBox** - Meta-learning (robust)
16. **TransmogrifAI** - Spark ML (scalable)

**Key Features:**
- Weighted averaging based on historical accuracy
- Dynamic weight adjustment as models train
- Stores all 16 predictions per round
- Tracks MAE (Mean Absolute Error) for each model
- Auto-reweighting based on recent performance

### B. ML Signal Generator

**Location:** `/home/user/ProjectBot/backend/core/ml_signal_generator.py`

Generates betting recommendations using:
- **Position 1 Strategy**: ML green classifier for 1.5x-2.0x targets (conservative)
- **Position 2 Strategy**: Rule-based logic for 3x+ targets (aggressive)
- **Hybrid Mode**: Combines both strategies intelligently
- **Regression Mode**: Pure ML prediction (legacy)

Returns signal with:
- `should_bet` (boolean)
- `confidence` (0-100%)
- `prediction` (target multiplier)
- `range` (predicted min/max)
- `reason` (explanation)
- `target_multiplier` (specific aim)

### C. Position 2 Rule Engine

**Location:** `/home/user/ProjectBot/backend/core/position2_rule_engine.py`

Pattern-based betting system inspired by Pavan Rules:

**Rules Implemented:**
- **R1**: Low Green Series → detects 4+ consecutive low multipliers (<2.0x)
- **R2**: No 20x Gap → identifies extended periods without high multipliers
- **R3**: Post-High Echo → patterns after 10x+ events
- **R5**: Massive Gap → extreme volatility detection
- **R6**: Cluster Series → grouped multiplier patterns
- **R7**: Series Direction → trending analysis
- **R8**: Delayed Spike → buildup before burst
- **R10**: Confidence Builder → cumulative signal strength

**Outputs:**
- `should_bet` (boolean)
- `confidence` (0-100)
- `target_multiplier` (specific number like 10.0, 50.0)
- `rules_triggered` (list of which rules fired)
- `burst_probability` (0-1 scale)
- `phase` (cool-down, building, burst)
- `insights` (human-readable explanations)

### D. Game State Detector

**Location:** `/home/user/ProjectBot/backend/core/game_detector.py`

Monitors game state using:
- **OCR** via pytesseract - reads multiplier display
- **Clipboard Reading** - copies multiplier value
- **Screenshot Analysis** - OpenCV processing
- Detects states: AWAITING, ENDED, UNKNOWN

### E. History Tracker

**Location:** `/home/user/ProjectBot/backend/core/history_tracker.py`

**Features:**
- Async CSV writing for performance
- In-memory cache with threading lock
- Automatic file creation with headers
- Batch logging with realistic timestamps
- Recent round filtering (configurable window)
- Round-level detail logging

**Async Architecture:**
- Background thread for non-blocking writes
- Write queue for buffering
- Configurable cooldown between writes
- Graceful shutdown handling

---

## 4. API ENDPOINTS & BACKEND STRUCTURE

### Flask Server Setup

**Main Server:** `/home/user/ProjectBot/backend/dashboard/compact_analytics.py`
**Port:** 5001
**Framework:** Flask + Flask-SocketIO with async_mode='threading'

### HTTP Endpoints

#### Dashboard & UI Routes
- `GET /` - Main dashboard (compact_dashboard.html)
- `GET /advanced` - Advanced analytics view
- `GET /logs` - Log viewer

#### Data API Routes
- `GET /api/current_round` - Current round with all 16 model predictions
- `GET /api/live_stats` - Overall statistics (rounds, win rate, P/L, trend)
- `GET /api/model_comparison` - All 16 models side-by-side comparison
- `GET /api/trend_signal` - Trend analysis and trading signals
- `GET /api/recent_rounds?limit=20` - Historical rounds (last N)
- `GET /api/top_models` - Top 3 performers with medals
- `GET /api/rules_status` - Position 2 rule engine status
- `POST /api/cleanup` - Trigger data cleanup operations

### WebSocket Events

**SocketIO Namespace:** Default (`/`)

**Server Emit:**
- `initial_data` - Sends live stats on client connect
- `live_update` - Real-time round updates
- `model_update` - Model performance updates

**Client Handlers:**
- `connect` - Client connection handler
- `disconnect` - Client disconnection
- `request_update` - Client requests immediate update

### Data Response Structures

**Current Round Response:**
```json
{
  "round_id": "string",
  "actual_multiplier": float,
  "prediction": float,
  "confidence": float,
  "range": [min, max],
  "signal": "BET|SKIP|WAIT|CAUTIOUS",
  "all_models": [
    {
      "id": int,
      "name": "string",
      "prediction": float,
      "accuracy": float,
      "color": "green|yellow|red"
    }
  ]
}
```

**Live Stats Response:**
```json
{
  "total_rounds": int,
  "win_rate": float,
  "profit_loss": float,
  "best_model": "string",
  "trend": "UPWARD|DOWNWARD|NEUTRAL",
  "signal": "STRONG_BET|BET|OPPORTUNITY|CAUTIOUS|WAIT|SKIP",
  "confidence": float
}
```

---

## 5. FRONTEND FRAMEWORK & DASHBOARD COMPONENTS

### HTML Templates Location
- `/home/user/ProjectBot/backend/dashboard/templates/compact_dashboard.html` - Main dashboard
- `/home/user/ProjectBot/backend/dashboard/templates/advanced_dashboard.html` - Advanced view
- `/home/user/ProjectBot/backend/dashboard/templates/logs.html` - Logs viewer
- `/home/user/ProjectBot/backend/templates/dashboard.html` - Legacy template

### Dashboard Layout (Half-Screen Optimized)

**Section 1: Live Stats Bar**
- Total Rounds
- Win Rate
- Profit/Loss
- Average Confidence
- Best Performing Model
- Current Trend

**Section 2: Current Round Display**
- Actual Multiplier vs Prediction
- Confidence Meter (visual bar)
- Recommended Target Range
- BET/SKIP Decision indicator
- Signal strength

**Section 3: Model Comparison Grid**
- 16 Models in 4x4 grid
- Individual predictions per model
- Accuracy color coding (green >80%, yellow 60-80%, red <60%)
- Top 3 performers with medals (🥇🥈🥉)
- Real-time updates (5-second refresh)

**Section 4: Trend & Signal Analysis**
- Trend indicator: ↑ UPWARD / ↓ DOWNWARD / → NEUTRAL
- Trend strength (0-100%)
- Trading signals with icons
- Pattern detection status

**Section 5: Rules Engine Status**
- Position 2 rule activation indicators
- Rule names and confidence levels
- Phase indicator (cool-down/building/burst)
- Insights panel with explanations

**Section 6: Recent Rounds Chart**
- Line chart: Actual vs Predicted
- Last 20 rounds
- Win/loss indicators
- Scrollable history table

**Section 7: Data Management**
- One-click cleanup button
- Archive old data option
- Data consolidation tool

### Frontend Technologies
- **Vanilla JavaScript** - No frameworks (lightweight)
- **Canvas/Chart.js** - Charts and visualizations
- **Fetch API** - AJAX requests
- **WebSocket API** - Real-time updates
- **CSS Grid/Flexbox** - Responsive layout
- **SVG** - Icons and indicators

### Styling Features
- Half-screen optimized (50% viewport width)
- Responsive gradients and shadows
- Color-coded accuracy indicators
- Real-time animation on updates
- Dark theme with contrast

---

## 6. ML/PREDICTION RELATED CODE

### ML Models Core

**Location:** `/home/user/ProjectBot/backend/core/ml_models.py`

**Implemented Model Types:**

1. **Regression Models** (Multiplier Value Prediction)
   - Random Forest Regressor
   - Gradient Boosting Regressor
   - LightGBM Regressor (optional)

2. **Classification Models** (Green/Red Prediction)
   - Random Forest Classifier (per target multiplier)
   - Gradient Boosting Classifier (per target multiplier)
   - Multi-target classifiers for 1.5x, 2.0x, 3.0x, etc.

3. **Deep Learning Models** (Optional)
   - LSTM (Long Short-Term Memory) - sequence modeling
   - Multi-layer Perceptron (MLP)
   - Keras Sequential models

**Feature Engineering:**
```python
Features created from 20-round history:
- Mean, median, std dev, min, max
- Exponential moving averages
- Lag features (t-1, t-2, etc.)
- Volatility measures
- Trend indicators
- Autocorrelation features
```

**Model Training:**

**Location:** `/home/user/ProjectBot/backend/train/train_models.py`

```bash
python backend/train/train_models.py
```

- Loads historical CSV data
- Splits into train/test (80/20)
- Cross-validation scoring
- Pickles models to `/backend/models/` directory
- Requires minimum 100 samples
- Tracks accuracy metrics (MAE, MSE, R², F1-score)

**Model Serialization:**
- Saves to: `/backend/models/`
- Format: pickle (.pkl) files
- Auto-loads on bot startup
- Retrainable without restarting

### Data Manager

**Location:** `/home/user/ProjectBot/backend/utils/data_manager.py`

**Operations:**
- Remove duplicates
- Fix CSV headers
- Archive old data (keep last N days)
- Consolidate multiple CSV files
- Data quality validation
- Backup creation

### Data Loggers

**Location:** `/home/user/ProjectBot/backend/utils/data_logger.py`

**Components:**
- `RoundLogger` - Simple 3-field logging (timestamp, multiplier, source)
- `PerformanceLogger` - Model performance metrics (20+ columns)
- `RangePredictor` - Range prediction logging

**Async Features:**
- Non-blocking write queue
- Background thread writer
- Configurable cooldown
- Graceful shutdown

---

## 7. PROJECT DIRECTORY STRUCTURE

```
/home/user/ProjectBot/
├── backend/
│   ├── core/
│   │   ├── ml_models.py (36KB) - ML model implementations
│   │   ├── ml_signal_generator.py (26KB) - Signal generation logic
│   │   ├── position2_rule_engine.py (18KB) - Pattern-based rules
│   │   ├── history_tracker.py (14KB) - CSV history tracking
│   │   ├── game_detector.py (5KB) - Game state detection
│   │   └── __init__.py
│   ├── dashboard/
│   │   ├── compact_analytics.py (550+ lines) - Flask server
│   │   ├── __init__.py
│   │   └── templates/
│   │       ├── compact_dashboard.html - Main UI
│   │       ├── advanced_dashboard.html - Advanced view
│   │       └── logs.html - Logs viewer
│   ├── config/
│   │   ├── config_manager.py - Configuration handling
│   │   └── __init__.py
│   ├── modes/
│   │   ├── dry_run.py - Simulation mode
│   │   ├── observation.py - Data collection mode
│   │   └── __init__.py
│   ├── train/
│   │   └── train_models.py - Model training script
│   ├── utils/
│   │   ├── data_logger.py - Centralized data logging
│   │   ├── data_manager.py - Data cleanup tools
│   │   ├── betting_helpers.py - Bet placement logic
│   │   ├── ocr_utils.py - OCR utilities
│   │   ├── clipboard_utils.py - Clipboard management
│   │   ├── logging_utils.py - Logging setup
│   │   ├── bet_logger.py - Bet logging
│   │   ├── logger.py - General logging
│   │   ├── captureregion.py - Screenshot capture
│   │   └── __init__.py
│   ├── tests/
│   │   ├── test_*.py files (multiple test files)
│   │   └── cleaning utilities
│   ├── data/
│   │   ├── aviator_history.csv - Legacy history
│   │   ├── add_manual_history.py
│   │   ├── extracthistory.py
│   │   ├── migrate_csv_header.py
│   │   └── configs (JSON)
│   ├── bot.py (68KB) - Main bot executable
│   ├── bot_modular.py (83KB) - Modular bot version
│   ├── automl_predictor.py (22KB) - Ensemble predictor
│   ├── readregion.py (16KB) - Screen reading
│   ├── validate_coordinates.py (10KB) - Coordinate validation
│   ├── manual_history_loader.py (19KB) - Manual data loading
│   ├── monitor_bot.py (3KB) - Bot monitoring
│   ├── *.csv files (data files)
│   └── models/ - Trained ML models (pickles)
├── scripts/
│   └── automation scripts
├── systemd/
│   └── service files for Linux
├── templates/
│   └── HTML templates
├── run_dashboard.py - Dashboard launcher
├── cleanup_data.py - Data cleanup utility
├── Dockerfile - Docker image for bot
├── Dockerfile.dashboard - Docker image for dashboard
├── docker-compose.yml - Multi-container setup
├── requirements.txt - Python dependencies
├── .env.example - Environment template
├── setup_vm.sh - VM setup script
├── IMPLEMENTATION_SUMMARY.md
├── DASHBOARD_README.md
├── MONITORING_GUIDE.md
├── VM_DEPLOYMENT_GUIDE.md
├── START_BOT_GUIDE.md
├── LINUX_SETUP.md
└── README.md
```

### File Sizes & Complexity
- **Total Python Code:** ~8,600 lines
- **Largest Files:**
  - `bot_modular.py` - 83 KB (main bot)
  - `bot.py` - 68 KB (alternate bot)
  - `ml_models.py` - 36 KB (ML core)
  - `ml_signal_generator.py` - 26 KB (signal logic)
  - `compact_analytics.py` - 550+ lines (dashboard)

---

## 8. OPERATING MODES

### Live Mode
- Real betting with actual money
- Full automation of bet placement
- Real stake management
- Production use

### Dry Run Mode
- Simulated betting (no money)
- Tests decision logic
- Builds confidence without risk
- Logs hypothetical results

### Observation Mode
- Data collection only
- No betting decisions
- Builds training dataset
- Pure monitoring

### Selection
User selects at bot startup interactively

---

## 9. SUGGESTED LOCATIONS FOR NEW CODE

### For New ML Models
- **Primary:** `/home/user/ProjectBot/backend/core/ml_models.py`
  - Add new model classes to AviatorMLModels
  - Implement `train()` and `predict()` methods
  - Register in model registry

- **Alternative:** Create new file `/home/user/ProjectBot/backend/core/advanced_models.py`
  - For experimental/specialized models
  - Import and integrate in ml_signal_generator.py

### For New Dashboard Features
- **HTML:** `/home/user/ProjectBot/backend/dashboard/templates/compact_dashboard.html`
  - Add new sections/panels
  - Update CSS for styling

- **Backend:** `/home/user/ProjectBot/backend/dashboard/compact_analytics.py`
  - Add new routes with `@self.app.route()`
  - Add SocketIO handlers with `@self.socketio.on()`
  - Add data collection methods

### For New API Endpoints
- **Location:** `/home/user/ProjectBot/backend/dashboard/compact_analytics.py`
  - Lines 55-102 show pattern for adding routes
  - Each route should return `jsonify(dict)` or raw data

### For New Utilities
- **Logger:** `/home/user/ProjectBot/backend/utils/data_logger.py`
- **Helpers:** `/home/user/ProjectBot/backend/utils/` directory
- **Configuration:** `/home/user/ProjectBot/backend/config/config_manager.py`

### For New Operating Modes
- **Location:** `/home/user/ProjectBot/backend/modes/` directory
  - Create `new_mode.py`
  - Export function like `run_new_mode(bot)`
  - Import in bot.py main loop

### For Configuration
- **Runtime Config:** `/home/user/ProjectBot/backend/aviator_ml_config.json`
- **Environment:** `/home/user/ProjectBot/.env.example` → `.env`
- **Config Manager:** `/home/user/ProjectBot/backend/config/config_manager.py`

---

## 10. KEY TECHNOLOGIES & INTEGRATIONS

### External APIs & Services
- None currently - fully self-contained
- Can be extended with API calls in utils/

### Data Flow
```
Game Screen
    ↓ (OCR/Screenshot)
GameStateDetector → AutoML Predictor → Signal Generator
    ↓                   ↓                    ↓
Multiplier Read     16 Models          Position2 Rules
    ↓                   ↓                    ↓
HistoryTracker → CSV Files ← Dashboard Server ← WebSocket ← Frontend
                                         ↓
                                   JSON API Routes
```

### Performance Optimization
- **Async CSV writing** - Non-blocking file I/O
- **In-memory caching** - Reduces disk reads
- **Threading** - Background operations
- **Min-heap tracking** - Efficient top-K performance
- **Batch operations** - Reduces system calls

### Cross-Platform Support
- Windows, Linux, macOS
- Virtual Display (Xvfb) for headless
- Docker containerization
- Environment configuration

---

## SUMMARY

| Category | Details |
|----------|---------|
| **Primary Language** | Python 3.9+ |
| **ML Ensemble** | 16 models with weighted voting |
| **Database** | 3x CSV files (no SQL DB) |
| **Dashboard API** | 8 REST endpoints + WebSocket |
| **Frontend** | Vanilla JavaScript + Canvas |
| **Deployment** | Docker Compose with 3 services |
| **Code Size** | ~8,600 lines of Python |
| **Configuration** | JSON config + .env variables |
| **Data Schema** | 50+ fields across CSV files |
| **Prediction Methods** | Regression, Classification, Rules |
| **Key Components** | Bot, Dashboard, ML, Rules Engine |

This is a **production-ready automated betting system** with comprehensive monitoring, multiple ML models, and pattern-based rules for decision-making.
