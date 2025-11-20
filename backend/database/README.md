# Crash Game Analytics Database

Complete PostgreSQL database solution for logging and analyzing crash game bot data (Aviator, Aviatrix, JetX).

## Overview

This database system provides:

✅ **Complete Round History** - Every bet, multiplier, outcome, and financial detail
✅ **3 Main Analytics Tables** - Optimized for ML training and signal generation
✅ **Real-time Logging** - Fast insertion of rounds, analytics, and signals
✅ **Error Tracking** - Comprehensive error and OCR validation logs
✅ **Session Management** - Track bot sessions and performance metrics
✅ **DigitalOcean PostgreSQL** - Cloud-native setup with SSL support

## Quick Start

### 1. Setup Database Connection

```python
from backend.database import DatabaseConnection, init_db

# Initialize database (creates all tables)
init_db(drop_existing=False)

# Test connection
DatabaseConnection.test_connection()
```

### 2. Register a Bot

```python
from backend.database import session_scope
from backend.database.models import BotVMRegistration
from decimal import Decimal

with session_scope() as session:
    bot = BotVMRegistration(
        bot_id="aviator_bot_001",
        bot_name="Aviator Compound Bot",
        vm_name="GPU-Instance-1",
        vm_provider="digitalocean",
        region="nyc3",
        session_id="session_20251121_001",
        strategy_name="compound_1.33x",
        initial_balance=Decimal("1000.00"),
        base_stake=Decimal("10.00"),
        max_stake=Decimal("100.00"),
    )
    session.add(bot)
```

### 3. Log a Round

```python
from backend.database import log_crash_round, log_round_outcome
from decimal import Decimal

# Log the main round
round_id = log_crash_round(
    bot_id="aviator_bot_001",
    session_id="session_20251121_001",
    game_name="aviator",
    platform_code="dafabet",
    round_number=1,
    stake_value=Decimal("10.00"),
    crash_multiplier=Decimal("2.45"),
    cashout_multiplier=Decimal("1.33"),
    round_outcome="WIN",
    profit_loss=Decimal("3.30"),
    running_balance_before=Decimal("1000.00"),
    running_balance_after=Decimal("1003.30"),
)

# Log outcome statistics
if round_id:
    log_round_outcome(
        round_id=round_id,
        round_number=1,
        bot_id="aviator_bot_001",
        game_name="aviator",
        platform_code="dafabet",
        strategy_name="compound_1.33x",
        outcome="WIN",
        profit_loss=Decimal("3.30"),
        roi_percent=0.33,
        target_multiplier=Decimal("1.33"),
        actual_multiplier=Decimal("1.33"),
        hit_target=True,
    )
```

## Database Schema

### Main Tables

#### 1. `bot_vm_registration`
Identifies unique bot instances and their configuration.

**Fields:**
- `bot_id` - Unique bot identifier
- `bot_name` - Bot display name
- `vm_name` - Virtual machine name
- `vm_provider` - Provider (vastai, runpod, digitalocean, etc.)
- `region` - VM region
- `session_id` - Current session ID
- `strategy_name` - Strategy type (compound_1.33x, martingale, etc.)
- `initial_balance`, `base_stake`, `max_stake` - Financial config

#### 2. `game_platform_config`
Game and platform configuration.

**Fields:**
- `game_name` - aviator, aviatrix, jetx
- `platform_code` - dafabet, fun88, pmbetting, etc.
- `platform_url` - Game URL
- `currency` - USD, EUR, etc.
- `house_edge_percent` - House edge percentage
- `min_multiplier`, `max_multiplier` - Multiplier bounds

#### 3. `crash_game_rounds` (Main Round History)
Complete record of every round played.

**Sections:**
- **Section 1-2:** Bot/Platform identification
- **Section 3:** Round timing (start, end, duration)
- **Section 4:** Stake & strategy details
- **Section 5:** Multiplier values (crash, cashout, final)
- **Section 6:** Financial metrics (profit/loss, balance, ROI)
- **Section 7:** OCR & detection logs (raw text, confidence)
- **Section 8:** Outcome & errors (result, error type, recovery)
- **Section 9:** Metadata (JSONB field for flexible data)

### Analytics Tables (3 Main Tables)

#### Analytics Table 1: `analytics_round_multipliers`
**Purpose:** Training and signal generation
**Key Fields:**
- `round_id` - Link to main round
- `multiplier` - Multiplier value
- `timestamp` - When detected
- `is_crash_multiplier` - Is this the crash point?
- `is_cashout_multiplier` - Is this the cashout?
- `ocr_confidence` - Confidence score
- `data_quality_score` - Quality metric

**Usage:** ML training, multiplier analysis, OCR validation

#### Analytics Table 2: `analytics_round_signals`
**Purpose:** ML feature generation and pattern detection
**Key Fields:**
- `round_id` - Link to main round
- `signal_type` - Type detected (pre_flight, early_flight, etc.)
- `confidence_score` - Signal confidence
- `time_to_crash_predicted_ms` - Time prediction
- `pattern_match_type` - Pattern (exponential, linear, etc.)
- `feature_vector` - JSON features for ML
- `signal_correctness` - Was prediction correct?

**Usage:** Pattern recognition, signal generation, ML training

#### Analytics Table 3: `analytics_round_outcomes`
**Purpose:** Statistics and reporting
**Key Fields:**
- `outcome` - WIN, LOSS, SKIP, ERROR
- `profit_loss` - Profit/loss amount
- `roi_percent` - Return on investment
- `target_multiplier` - Target vs actual
- `outcome_category` - Classification (big_win, small_loss, etc.)
- `win_streak_length` - Current streak
- `date_bucket` - Date for aggregation

**Usage:** Analytics, dashboards, performance tracking

### Supporting Tables

- **`ocr_validation_logs`** - OCR quality tracking
- **`error_logs`** - Error tracking and debugging
- **`session_logs`** - Session statistics and tracking

## API Reference

### Connection Management

```python
# Initialize database
from backend.database import init_db
init_db(drop_existing=False)

# Get a session
from backend.database import get_session
session = get_session()

# Use context manager (recommended)
from backend.database import session_scope
with session_scope() as session:
    # database operations
    pass

# Test connection
from backend.database import DatabaseConnection
DatabaseConnection.test_connection()
```

### Logging Functions

#### `log_crash_round()`
Log a complete crash game round.

```python
from backend.database import log_crash_round
from decimal import Decimal

round_id = log_crash_round(
    bot_id="bot_001",
    session_id="session_001",
    game_name="aviator",  # aviator, aviatrix, jetx
    platform_code="dafabet",
    round_number=1,
    stake_value=Decimal("10.00"),
    crash_multiplier=Decimal("2.45"),
    cashout_multiplier=Decimal("1.33"),
    round_outcome="WIN",  # WIN, LOSS, SKIP, ERROR
    profit_loss=Decimal("3.30"),
    running_balance_before=Decimal("1000.00"),
    running_balance_after=Decimal("1003.30"),
    ocr_text="1.33x",
    ocr_confidence=0.95,
    metadata={"strategy": "compound_1.33x"}
)
```

#### `log_round_multiplier_analytics()`
Log multiplier data for ML training.

```python
from backend.database import log_round_multiplier_analytics

log_round_multiplier_analytics(
    round_id=round_id,
    multiplier=Decimal("1.33"),
    bot_id="bot_001",
    game_name="aviator",
    is_crash=False,
    is_cashout=True,
    ocr_confidence=0.95,
    data_quality_score=0.98,
)
```

#### `log_round_signal()`
Log signal data for ML features.

```python
from backend.database import log_round_signal

log_round_signal(
    round_id=round_id,
    round_number=1,
    bot_id="bot_001",
    game_name="aviator",
    signal_type="early_flight",
    confidence_score=0.92,
    pattern_type="exponential",
    feature_vector={"acceleration": 0.089, "density": 0.67},
)
```

#### `log_round_outcome()`
Log outcome statistics for analytics.

```python
from backend.database import log_round_outcome

log_round_outcome(
    round_id=round_id,
    round_number=1,
    bot_id="bot_001",
    game_name="aviator",
    strategy_name="compound_1.33x",
    outcome="WIN",
    profit_loss=Decimal("3.30"),
    roi_percent=0.33,
    target_multiplier=Decimal("1.33"),
    actual_multiplier=Decimal("1.33"),
    hit_target=True,
)
```

#### `log_error()`
Log errors for debugging.

```python
from backend.database import log_error

log_error(
    bot_id="bot_001",
    session_id="session_001",
    error_type="ocr_error",
    error_message="Failed to read multiplier",
    recovery_action="Retry with preprocessing",
)
```

#### `log_ocr_validation()`
Log OCR validation data.

```python
from backend.database import log_ocr_validation

log_ocr_validation(
    bot_id="bot_001",
    raw_ocr_text="1.33x",
    cleaned_value=Decimal("1.33"),
    confidence=0.95,
    validation_status="VALID",
)
```

#### `create_session_log()` / `update_session_log()`
Manage session tracking.

```python
from backend.database import create_session_log, update_session_log
from decimal import Decimal

# Create session
session_id = create_session_log(
    bot_id="bot_001",
    session_id="session_001",
    game_name="aviator",
    initial_balance=Decimal("1000.00"),
)

# Update session at end
update_session_log(
    session_id="session_001",
    final_balance=Decimal("1050.00"),
    status="completed",
)
```

## Querying Data

### Query Rounds for a Bot

```python
from backend.database import session_scope
from backend.database.models import CrashGameRound

with session_scope() as session:
    rounds = session.query(CrashGameRound).filter_by(
        bot_id="bot_001"
    ).order_by(CrashGameRound.round_number.desc()).all()

    for round in rounds:
        print(f"Round {round.round_number}: {round.round_outcome}")
```

### Query Analytics Data

```python
from backend.database.models import AnalyticsRoundMultiplier

with session_scope() as session:
    multipliers = session.query(AnalyticsRoundMultiplier).filter_by(
        bot_id="bot_001"
    ).all()

    for m in multipliers:
        print(f"Multiplier: {m.multiplier}, Confidence: {m.ocr_confidence}")
```

### Calculate Session Statistics

```python
from sqlalchemy import func
from backend.database.models import CrashGameRound

with session_scope() as session:
    stats = session.query(
        func.count(CrashGameRound.id).label("total"),
        func.sum(CrashGameRound.profit_loss_amount).label("profit"),
        func.avg(CrashGameRound.profit_loss_amount).label("avg_profit"),
    ).filter_by(bot_id="bot_001").first()

    print(f"Total Rounds: {stats.total}")
    print(f"Total Profit: ${stats.profit}")
    print(f"Average: ${stats.avg_profit}")
```

## Configuration

The database is pre-configured for your DigitalOcean PostgreSQL instance:

```
Host: db-main-do-user-28557476-0.h.db.ondigitalocean.com
Port: 25060
Database: defaultdb
Username: pk
SSL Mode: require
```

To change credentials, modify `.env` or `backend/database/config.py`:

```python
DB_HOST = "db-main-do-user-28557476-0.h.db.ondigitalocean.com"
DB_PORT = 25060
DB_NAME = "defaultdb"
DB_USER = "pk"
DB_PASSWORD = "YOUR_PASSWORD_HERE"
```

## Integration with Bot

### Minimal Bot Integration

```python
from backend.database import (
    init_db,
    create_session_log,
    update_session_log,
    log_crash_round,
    log_round_outcome,
)
from decimal import Decimal

# Initialize once
init_db()

# Start session
session_id = create_session_log(
    bot_id="my_bot_001",
    session_id="session_001",
    game_name="aviator",
    initial_balance=Decimal("1000.00"),
)

# In your bot loop
for round_num in range(1, 100):
    # Your betting logic...
    stake = Decimal("10.00")
    crash_mult = Decimal("2.45")
    target_mult = Decimal("1.33")

    # Determine outcome
    if crash_mult >= target_mult:
        outcome = "WIN"
        profit = (target_mult - 1) * stake
    else:
        outcome = "LOSS"
        profit = -stake

    # Log the round
    round_id = log_crash_round(
        bot_id="my_bot_001",
        session_id=session_id,
        game_name="aviator",
        platform_code="dafabet",
        round_number=round_num,
        stake_value=stake,
        crash_multiplier=crash_mult,
        cashout_multiplier=target_mult if outcome == "WIN" else None,
        round_outcome=outcome,
        profit_loss=profit,
    )

# Close session
update_session_log(session_id=session_id, status="completed")
```

## Performance Tips

1. **Use context managers** - Always use `session_scope()` for proper transaction handling
2. **Batch operations** - Use `log_batch_rounds()` for inserting multiple rounds
3. **Index queries** - Take advantage of pre-built indexes on `bot_id`, `timestamp`, `outcome`
4. **Lazy loading** - Relationships are lazy-loaded by default (good for performance)

## Troubleshooting

### Connection Issues

```python
# Test connection
from backend.database import DatabaseConnection
if DatabaseConnection.test_connection():
    print("✅ Connected")
else:
    print("❌ Connection failed")
```

### Create Tables

```python
from backend.database import DatabaseConnection
DatabaseConnection.create_all_tables()
```

### Drop and Recreate (Development Only)

```python
from backend.database import init_db
init_db(drop_existing=True)  # ⚠️ This deletes all data!
```

## Example Output

After running the bot with logging:

```
Total Rounds: 25
Wins: 18
Losses: 7
Total Profit: $47.50
Win Rate: 72%
Average ROI: 1.9%
```

## License

Part of the Crash Game Bot system.
