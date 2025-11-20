# Complete Integration Guide - Crash Game Analytics Database

Complete guide to integrate the PostgreSQL analytics database into your Aviator/Aviatrix/JetX bots.

## Table of Contents

1. [Quick Start](#quick-start)
2. [Database Architecture](#database-architecture)
3. [Integration Steps](#integration-steps)
4. [Bot Implementation](#bot-implementation)
5. [Analytics Queries](#analytics-queries)
6. [Troubleshooting](#troubleshooting)

## Quick Start

### 1. Install Dependencies

```bash
pip install sqlalchemy psycopg2-binary python-dotenv
```

### 2. Initialize Database

```python
from backend.database import init_db

# Creates all tables on first run
init_db(drop_existing=False)
```

### 3. Log Your First Round

```python
from backend.database import log_crash_round
from decimal import Decimal

round_id = log_crash_round(
    bot_id="my_bot_001",
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
print(f"Logged round: {round_id}")
```

## Database Architecture

### Main Components

```
┌─────────────────────────────────────────┐
│   CRASH_GAME_ROUNDS (Main Table)        │
│  ├─ Bot/VM Identification               │
│  ├─ Platform & Game Details             │
│  ├─ Round Timing                        │
│  ├─ Stake & Strategy                    │
│  ├─ Multipliers                         │
│  ├─ Financials                          │
│  ├─ OCR Logs                            │
│  ├─ Outcome & Errors                    │
│  └─ Metadata (JSONB)                    │
└─────────────────────────────────────────┘
              ↓ ↓ ↓
    ┌─────────────────────┬─────────────────────┬─────────────────────┐
    │                     │                     │                     │
    ▼                     ▼                     ▼                     ▼
ANALYTICS_ROUND_   ANALYTICS_ROUND_   ANALYTICS_ROUND_    SUPPORTING
MULTIPLIERS         SIGNALS             OUTCOMES           TABLES
(Training)          (ML Features)       (Reporting)        (OCR, Errors)
roundid             signal_type         outcome            error_logs
multiplier          confidence          profit_loss        ocr_validation
timestamp           pattern_match       roi_percent        session_logs
```

### 3 Main Analytics Tables

**Table 1: `analytics_round_multipliers`**
- Purpose: ML training and signal generation
- Core fields: roundid, multiplier, timestamp
- Usage: Training ML models, multiplier analysis

**Table 2: `analytics_round_signals`**
- Purpose: Signal generation and pattern recognition
- Core fields: round_id, signal_type, confidence_score, feature_vector
- Usage: Pattern detection, ML features, signal validation

**Table 3: `analytics_round_outcomes`**
- Purpose: Analytics and reporting
- Core fields: outcome, profit_loss, roi_percent, strategy
- Usage: Dashboards, performance tracking, strategy analysis

## Integration Steps

### Step 1: Setup Environment Variables

Create `.env` file in project root:

```env
DB_HOST=db-main-do-user-28557476-0.h.db.ondigitalocean.com
DB_PORT=25060
DB_NAME=defaultdb
DB_USER=pk
DB_PASSWORD=YOUR_PASSWORD_HERE
DB_SSL_MODE=require
```

Or use direct configuration in [backend/database/config.py](backend/database/config.py).

### Step 2: Initialize Database

In your main bot file:

```python
from backend.database import init_db, DatabaseConnection

# Initialize once at startup
try:
    init_db(drop_existing=False)
    print("✅ Database initialized")
except Exception as e:
    print(f"❌ Database error: {e}")
    exit(1)
```

### Step 3: Register Bot Instance

```python
from backend.database import session_scope
from backend.database.models import BotVMRegistration
from decimal import Decimal

with session_scope() as session:
    bot = BotVMRegistration(
        bot_id="aviator_bot_001",
        bot_name="Aviator Main Bot",
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
    print(f"✅ Registered bot: {bot.bot_id}")
```

### Step 4: Create Session Log

```python
from backend.database import create_session_log
from decimal import Decimal

session_id = create_session_log(
    bot_id="aviator_bot_001",
    session_id="session_20251121_001",
    game_name="aviator",
    initial_balance=Decimal("1000.00"),
)
print(f"✅ Session created: {session_id}")
```

### Step 5: Log Rounds in Your Bot Loop

```python
from backend.database import (
    log_crash_round,
    log_round_multiplier_analytics,
    log_round_outcome,
    log_round_signal,
)
from decimal import Decimal

# In your main bot loop
current_balance = Decimal("1000.00")

for round_num in range(1, 1000):
    # Your betting logic here
    stake = Decimal("10.00")

    # Get crash multiplier (from game)
    crash_multiplier = Decimal("2.45")  # Example
    target_multiplier = Decimal("1.33")

    # Determine outcome
    if crash_multiplier >= target_multiplier:
        outcome = "WIN"
        cashout_multiplier = target_multiplier
        profit = (target_multiplier - 1) * stake
    else:
        outcome = "LOSS"
        cashout_multiplier = None
        profit = -stake

    current_balance += profit

    # Log to database
    round_id = log_crash_round(
        bot_id="aviator_bot_001",
        session_id="session_20251121_001",
        game_name="aviator",
        platform_code="dafabet",
        round_number=round_num,
        stake_value=stake,
        crash_multiplier=crash_multiplier,
        cashout_multiplier=cashout_multiplier,
        round_outcome=outcome,
        profit_loss=profit,
        running_balance_before=current_balance - profit,
        running_balance_after=current_balance,
        ocr_text="1.33x",
        ocr_confidence=0.95,
        metadata={
            "strategy": "compound_1.33x",
            "prediction_correct": (outcome == "WIN"),
        }
    )

    # Log analytics (if round successful)
    if round_id:
        # Analytics 1: Multiplier data
        log_round_multiplier_analytics(
            round_id=round_id,
            multiplier=crash_multiplier,
            bot_id="aviator_bot_001",
            game_name="aviator",
            platform_code="dafabet",
            is_crash=True,
            ocr_confidence=0.95,
        )

        # Analytics 2: Signal/patterns
        log_round_signal(
            round_id=round_id,
            round_number=round_num,
            bot_id="aviator_bot_001",
            game_name="aviator",
            signal_type="early_flight",
            confidence_score=0.92,
            pattern_type="exponential",
            feature_vector={"volatility": 0.65, "momentum": 0.78},
        )

        # Analytics 3: Outcome statistics
        log_round_outcome(
            round_id=round_id,
            round_number=round_num,
            bot_id="aviator_bot_001",
            game_name="aviator",
            platform_code="dafabet",
            strategy_name="compound_1.33x",
            outcome=outcome,
            profit_loss=profit,
            roi_percent=(profit / stake * 100),
            target_multiplier=target_multiplier,
            actual_multiplier=crash_multiplier,
            hit_target=(outcome == "WIN"),
        )
```

### Step 6: Close Session at End

```python
from backend.database import update_session_log

# At end of bot session
update_session_log(
    session_id="session_20251121_001",
    final_balance=current_balance,
    status="completed",
    notes="Session completed successfully",
)
print("✅ Session closed")
```

## Bot Implementation

### Minimal Bot Example

```python
#!/usr/bin/env python3
"""
Minimal crash game bot with database logging
"""

from backend.database import (
    init_db,
    create_session_log,
    update_session_log,
    log_crash_round,
)
from decimal import Decimal
import time
import random

def main():
    # Initialize
    init_db()

    # Create session
    session_id = create_session_log(
        bot_id="minimal_bot",
        session_id=f"session_{int(time.time())}",
        game_name="aviator",
        initial_balance=Decimal("500.00"),
    )

    current_balance = Decimal("500.00")
    stake = Decimal("10.00")
    target = Decimal("1.50")

    # Bot loop
    for round_num in range(1, 101):
        # Simulate game
        crash = Decimal(str(round(random.uniform(1.0, 5.0), 2)))
        outcome = "WIN" if crash >= target else "LOSS"
        profit = ((target - 1) * stake) if outcome == "WIN" else -stake
        current_balance += profit

        # Log
        log_crash_round(
            bot_id="minimal_bot",
            session_id=session_id,
            game_name="aviator",
            platform_code="dafabet",
            round_number=round_num,
            stake_value=stake,
            crash_multiplier=crash,
            cashout_multiplier=target if outcome == "WIN" else None,
            round_outcome=outcome,
            profit_loss=profit,
            running_balance_before=current_balance - profit,
            running_balance_after=current_balance,
        )

        print(f"Round {round_num}: {outcome} | Balance: ${current_balance}")
        time.sleep(0.1)

    # Close
    update_session_log(session_id, final_balance=current_balance, status="completed")
    print(f"✅ Final balance: ${current_balance}")

if __name__ == "__main__":
    main()
```

## Analytics Queries

### Get Bot Statistics

```python
from backend.database.utils import get_bot_statistics

stats = get_bot_statistics("aviator_bot_001")
print(f"Win Rate: {stats['win_rate_percent']}%")
print(f"Total Profit: ${stats['total_profit']}")
print(f"ROI: {stats['roi_percent']}%")
```

### Get Session Summary

```python
from backend.database.utils import get_session_summary

summary = get_session_summary("session_20251121_001")
print(f"Duration: {summary['duration_seconds']} seconds")
print(f"Final Balance: ${summary['final_balance']}")
```

### Get Strategy Performance

```python
from backend.database.utils import get_strategy_performance

perf = get_strategy_performance("compound_1.33x")
print(f"Strategy Win Rate: {perf['win_rate_percent']}%")
print(f"Total Profit: ${perf['total_profit']}")
```

### Export for ML Training

```python
from backend.database.utils import export_multipliers_for_ml
import json

data = export_multipliers_for_ml("aviator", limit=5000)
with open("training_data.json", "w") as f:
    json.dump(data, f)
```

## Troubleshooting

### Connection Issues

```python
from backend.database import DatabaseConnection

# Test connection
if DatabaseConnection.test_connection():
    print("✅ Connected")
else:
    print("❌ Connection failed")
```

### Check Database Status

```python
from backend.database.utils import get_database_size

size = get_database_size()
print(f"Total records: {size['total_records']}")
print(f"Tables: {size['tables']}")
```

### Recreate Tables (Development Only)

```python
from backend.database import init_db

# ⚠️ This deletes all data!
init_db(drop_existing=True)
```

### Common Issues

1. **SSL Connection Error**
   - Ensure `sslmode=require` in connection string
   - Check DigitalOcean credentials

2. **Table Not Found**
   - Run `init_db()` to create tables
   - Check database name: `defaultdb`

3. **Slow Queries**
   - Indexes are created automatically
   - Use `bot_id` and `timestamp` in WHERE clauses
   - Batch insert multiple rounds

## Performance Tips

1. **Use batch operations for multiple rounds**
   ```python
   from backend.database import log_batch_rounds
   log_batch_rounds(rounds_data_list)
   ```

2. **Cache bot registration**
   ```python
   # Don't re-query bot details every round
   # Register once and reuse bot_id string
   ```

3. **Async logging (optional)**
   ```python
   # Log in background thread to avoid blocking bot
   from threading import Thread
   Thread(target=log_crash_round, args=(...)).start()
   ```

4. **Regular cleanup**
   ```python
   from backend.database.utils import cleanup_old_records
   cleanup_old_records(days_old=90, dry_run=False)
   ```

## Next Steps

1. ✅ Database initialized
2. ✅ Bot registered
3. ✅ Rounds being logged
4. 📊 Create dashboards with aggregated data
5. 🤖 Train ML models on multiplier data
6. 📈 Generate trading signals from patterns
7. 🔔 Setup alerts for anomalies

## Documentation Links

- [Database README](backend/database/README.md)
- [Schema Reference](backend/database/schema.sql)
- [API Reference](backend/database/logger.py)
- [Example Usage](backend/database/example_usage.py)

## Support

For issues or questions:
1. Check [TROUBLESHOOTING](#troubleshooting) section
2. Review [Example Usage](backend/database/example_usage.py)
3. Check database connection with `DatabaseConnection.test_connection()`

---

**Created:** November 21, 2024
**Database:** DigitalOcean PostgreSQL
**Games Supported:** Aviator (Spribe), Aviatrix (Aviatrix Labs), JetX (SmartSoft)
