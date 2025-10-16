# Aviator Bot - Modular Architecture

This is the modularized version of the Aviator Bot with improved code organization and maintainability.

## 📁 Project Structure

```
backend/
├── bot.py                      # Original monolithic version (kept for reference)
├── bot_modular.py             # New modular main entry point
├── config/
│   ├── __init__.py
│   └── config_manager.py      # Configuration management
├── core/
│   ├── __init__.py
│   ├── game_detector.py       # Game state detection (OCR, clipboard)
│   ├── history_tracker.py     # Round history tracking (CSV)
│   └── ml_signal_generator.py # ML betting signals
├── dashboard/
│   ├── __init__.py
│   ├── dashboard_server.py    # Flask web dashboard
│   └── templates/
│       └── dashboard.html     # Dashboard UI
├── utils/
│   ├── __init__.py
│   ├── clipboard_utils.py     # Clipboard operations
│   ├── ocr_utils.py          # OCR preprocessing
│   └── betting_helpers.py     # Betting verification & helpers
├── captureregion.py           # Screen region capture utility
├── extracthistory.py          # OCR extraction utility
└── README.md                  # This file
```

## 🚀 Quick Start

### Running the Modular Version

```bash
cd backend
python bot_modular.py
```

### Running the Original Version

```bash
cd backend
python bot.py
```

## 📦 Modules Overview

### 1. **config/** - Configuration Management
- **ConfigManager**: Handles coordinate setup, config save/load
- Manages all bot parameters (stakes, delays, thresholds)

### 2. **core/** - Core Game Logic
- **GameStateDetector**: OCR-based game state detection
  - Read multipliers from clipboard
  - Detect "awaiting" state
  - Check if game is running
  
- **RoundHistoryTracker**: CSV-based history logging
  - Auto-log rounds from clipboard
  - Track betting history
  - Generate statistics
  
- **MLSignalGenerator**: Betting signal generation
  - Ensemble predictions
  - Pattern analysis
  - Confidence-based decisions

### 3. **dashboard/** - Web Interface
- **AviatorDashboard**: Real-time Flask dashboard
  - Live statistics
  - Round history table
  - Recent multipliers visualization
  - SocketIO for real-time updates

### 4. **utils/** - Helper Functions
- **clipboard_utils.py**: Clipboard operations
  - Clear, read, select & copy text
  - Parse multiplier values
  
- **ocr_utils.py**: Image preprocessing
  - Enhance images for OCR
  - Adaptive thresholding
  
- **betting_helpers.py**: Betting operations
  - Bet placement verification
  - Stake management
  - Cashout verification
  - Multiplier estimation

## 🔧 Key Improvements

### ✅ Modularity
- Each component has a single responsibility
- Easy to test individual modules
- Clear separation of concerns

### ✅ Maintainability
- Smaller, focused files
- Better code organization
- Easier to debug and extend

### ✅ Reusability
- Utility functions can be used independently
- Components can be imported separately
- Easy to create variations

### ✅ Testability
- Each module can be tested in isolation
- Mock dependencies easily
- Unit tests can be added per module

## 📝 Usage Examples

### Import Individual Components

```python
from config import ConfigManager
from core import GameStateDetector, RoundHistoryTracker
from utils import clear_clipboard, estimate_multiplier

# Use components independently
config = ConfigManager()
config.load_config()

detector = GameStateDetector(config.multiplier_region)
is_awaiting = detector.is_awaiting_next_flight()
```

### Custom Bot Implementation

```python
from config import ConfigManager
from core import GameStateDetector, MLSignalGenerator, RoundHistoryTracker
from utils.betting_helpers import place_bet_with_verification

# Create custom bot with specific components
config = ConfigManager()
config.load_config()

detector = GameStateDetector(config.multiplier_region)
tracker = RoundHistoryTracker()
ml_gen = MLSignalGenerator(tracker)

# Use components as needed
signal = ml_gen.generate_ensemble_signal()
if signal['should_bet']:
    # Place bet logic
    pass
```

## 🔄 Migration from Original

The original `bot.py` is kept for reference. The modular version (`bot_modular.py`) provides the same functionality with better organization.

### Key Differences:
1. **Imports**: Components are imported from modules
2. **Structure**: Logic is distributed across specialized modules
3. **Flexibility**: Easier to customize individual components
4. **Testing**: Each module can be tested independently

## 🛠️ Development

### Adding New Features

1. **New Utility Function**: Add to appropriate file in `utils/`
2. **New Core Logic**: Add to appropriate file in `core/`
3. **Dashboard Enhancement**: Modify `dashboard/dashboard_server.py`
4. **Configuration Option**: Add to `config/config_manager.py`

### Testing Individual Modules

```python
# Test clipboard utilities
from utils import clear_clipboard, read_clipboard
clear_clipboard()
text = read_clipboard()

# Test game detector
from core import GameStateDetector
detector = GameStateDetector((100, 100, 200, 50))
state = detector.read_text_in_region()

# Test history tracker
from core import RoundHistoryTracker
tracker = RoundHistoryTracker()
recent = tracker.get_recent_rounds(10)
```

## 📊 Statistics & Monitoring

The dashboard provides real-time monitoring at `http://localhost:5000`:
- Live round statistics
- Success rate tracking
- Profit/Loss visualization
- Recent multipliers
- Verification status

## ⚙️ Configuration

All configuration is managed through `ConfigManager`:
- Coordinate setup (interactive)
- Stake parameters
- Cashout timing
- ML thresholds
- Auto-save to JSON

## 🐛 Debugging

Each module has error handling and logging:
- Import errors are caught and reported
- OCR failures are handled gracefully
- Verification failures are logged
- Dashboard errors don't crash the bot

## 📄 License

Same as original Aviator Bot project.

## 🤝 Contributing

When contributing:
1. Keep modules focused and single-purpose
2. Add docstrings to all functions/classes
3. Handle errors gracefully
4. Update this README if adding new modules

## 📞 Support

For issues or questions about the modular architecture, refer to the original `bot.py` for comparison or check individual module documentation.
