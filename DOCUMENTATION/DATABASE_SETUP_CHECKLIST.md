# Database Setup Checklist

Complete step-by-step checklist to get your crash game analytics database running.

## ✅ Pre-Setup Verification

- [x] DigitalOcean PostgreSQL account created
- [x] Database credentials available:
  - Host: `db-main-do-user-28557476-0.h.db.ondigitalocean.com`
  - Port: `25060`
  - Database: `defaultdb`
  - Username: `pk`
  - Password: `YOUR_PASSWORD_HERE`
  - SSL Mode: `require`

## ✅ Project Files Created

Database package structure:

```
backend/database/
├── __init__.py                 ✅ Package initialization
├── config.py                   ✅ Database configuration
├── connection.py               ✅ Connection management
├── models.py                   ✅ SQLAlchemy ORM models
├── logger.py                   ✅ Logging functions
├── utils.py                    ✅ Analytics utilities
├── schema.sql                  ✅ PostgreSQL schema
├── example_usage.py            ✅ Usage examples
└── README.md                   ✅ Documentation
```

## 📋 Installation Steps

### Step 1: Install Dependencies

```bash
pip install sqlalchemy psycopg2-binary
```

**Verification:**
```bash
python -c "import sqlalchemy; import psycopg2; print('✅ Dependencies installed')"
```

### Step 2: Setup Environment Variables (Optional)

Create `.env` file in project root:

```env
DB_HOST=db-main-do-user-28557476-0.h.db.ondigitalocean.com
DB_PORT=25060
DB_NAME=defaultdb
DB_USER=pk
DB_PASSWORD=YOUR_PASSWORD_HERE
DB_SSL_MODE=require
```

Or use configuration in `backend/database/config.py` directly.

### Step 3: Initialize Database

```python
from backend.database import init_db

# Create all tables
init_db(drop_existing=False)
```

**Expected Output:**
```
✅ Database connection initialized successfully
✅ Database connection test passed
✅ All tables created successfully
```

### Step 4: Test Connection

```python
from backend.database import DatabaseConnection

if DatabaseConnection.test_connection():
    print("✅ Connection successful")
else:
    print("❌ Connection failed")
```

## 📊 Database Components

### Main Tables Created

- [x] `bot_vm_registration` - Bot configuration
- [x] `game_platform_config` - Game configuration
- [x] `crash_game_rounds` - Complete round history
- [x] `analytics_round_multipliers` - ML training data
- [x] `analytics_round_signals` - Signal generation data
- [x] `analytics_round_outcomes` - Analytics/reporting data
- [x] `ocr_validation_logs` - OCR quality logs
- [x] `error_logs` - Error tracking
- [x] `session_logs` - Session management

### Features Included

- [x] 12 comprehensive sections for round data
- [x] 3 main analytics tables for training/signals/reporting
- [x] Automatic indexes for performance
- [x] JSONB metadata field for flexibility
- [x] Constraints for data integrity
- [x] Materialized view for daily stats
- [x] Stored procedures for common operations
- [x] Triggers for automatic timestamp updates

## 🚀 Quick Integration

### Minimal Setup (3 steps)

**1. Initialize (once at startup)**
```python
from backend.database import init_db
init_db()
```

**2. Log a round**
```python
from backend.database import log_crash_round
from decimal import Decimal

round_id = log_crash_round(
    bot_id="bot_001",
    session_id="session_001",
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
```

**3. Query results**
```python
from backend.database.utils import get_bot_statistics

stats = get_bot_statistics("bot_001")
print(f"Win Rate: {stats['win_rate_percent']}%")
```

## ✨ Key Features

### Comprehensive Data Logging

- ✅ Round-by-round history
- ✅ OCR validation logs
- ✅ Error tracking
- ✅ Financial metrics
- ✅ Strategy tracking
- ✅ Metadata storage

### Analytics Ready

- ✅ 3 optimized analytics tables
- ✅ Pre-built indexes
- ✅ Aggregation views
- ✅ ML training export
- ✅ Performance queries

### Production Ready

- ✅ Connection pooling
- ✅ Transaction handling
- ✅ Error recovery
- ✅ SSL security
- ✅ Constraint validation

## 🔍 Verification Checklist

After setup, verify:

- [ ] Database connection successful
- [ ] All tables created
- [ ] Can insert bot registration
- [ ] Can log a round
- [ ] Can query rounds back
- [ ] Analytics tables populated
- [ ] No connection errors in logs

**Quick verification script:**

```python
from backend.database import (
    init_db,
    DatabaseConnection,
    log_crash_round,
    session_scope,
)
from backend.database.models import CrashGameRound
from decimal import Decimal

# 1. Initialize
init_db()

# 2. Test connection
assert DatabaseConnection.test_connection(), "Connection failed"
print("✅ Connection OK")

# 3. Log a test round
round_id = log_crash_round(
    bot_id="test_bot",
    session_id="test_session",
    game_name="aviator",
    platform_code="dafabet",
    round_number=1,
    stake_value=Decimal("1.00"),
    crash_multiplier=Decimal("2.00"),
    cashout_multiplier=Decimal("1.50"),
    round_outcome="WIN",
    profit_loss=Decimal("0.50"),
    running_balance_before=Decimal("100.00"),
    running_balance_after=Decimal("100.50"),
)
print(f"✅ Round logged: {round_id}")

# 4. Query back
with session_scope() as session:
    round_data = session.query(CrashGameRound).filter_by(id=round_id).first()
    assert round_data is not None, "Failed to query round"
    print(f"✅ Retrieved round: {round_data.round_number}")

print("\n✅ ALL VERIFICATION TESTS PASSED")
```

## 📖 Documentation Files

Review these for more details:

1. **[INTEGRATION_GUIDE.md](INTEGRATION_GUIDE.md)** - Complete integration steps
2. **[backend/database/README.md](backend/database/README.md)** - API reference
3. **[backend/database/schema.sql](backend/database/schema.sql)** - SQL schema
4. **[backend/database/example_usage.py](backend/database/example_usage.py)** - Code examples

## 🎯 Next Steps After Setup

### Immediate
1. ✅ Initialize database
2. ✅ Register bot instance
3. ✅ Log first round
4. ✅ Verify data in database

### Short Term
1. Integrate logging into bot code
2. Track OCR validation
3. Monitor error logs
4. Export analytics data

### Medium Term
1. Build dashboards
2. Train ML models
3. Generate trading signals
4. Implement alerts

### Long Term
1. Multi-bot coordination
2. Strategy optimization
3. Advanced analytics
4. Real-time monitoring

## 🐛 Troubleshooting

### Connection Failed
```python
# Check database config
from backend.database.config import SQLALCHEMY_DATABASE_URL
print(SQLALCHEMY_DATABASE_URL)

# Test connection directly
from backend.database import DatabaseConnection
DatabaseConnection.test_connection()
```

### Tables Not Created
```python
# Force recreate tables
from backend.database import init_db
init_db(drop_existing=True)  # ⚠️ This deletes all data!
```

### Slow Queries
```python
# Check database size
from backend.database.utils import get_database_size
print(get_database_size())

# Cleanup old records
from backend.database.utils import cleanup_old_records
cleanup_old_records(days_old=90, dry_run=True)
```

## 📞 Support

If you encounter issues:

1. Check database connection:
   ```python
   from backend.database import DatabaseConnection
   DatabaseConnection.test_connection()
   ```

2. Review logs for errors:
   ```python
   import logging
   logging.basicConfig(level=logging.DEBUG)
   ```

3. Verify DigitalOcean credentials in config.py

4. Check network connectivity to PostgreSQL server

## ✅ Final Checklist

- [ ] Dependencies installed
- [ ] Database files created
- [ ] Connection string verified
- [ ] init_db() executed successfully
- [ ] Test round logged
- [ ] Data query successful
- [ ] No error messages
- [ ] Ready to integrate into bot

---

**Status:** ✅ Complete and Ready to Use

**Setup Date:** November 21, 2024

**Database:** DigitalOcean PostgreSQL

**Games Supported:** Aviator, Aviatrix, JetX
