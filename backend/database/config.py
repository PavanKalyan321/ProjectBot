"""
Database Configuration for DigitalOcean PostgreSQL
Crash Game Analytics & Logging System
"""

import os
from typing import Optional

# ============================================================================
# DATABASE CREDENTIALS (From DigitalOcean)
# ============================================================================

DB_HOST = os.getenv("DB_HOST", "db-main-do-user-28557476-0.h.db.ondigitalocean.com")
DB_PORT = int(os.getenv("DB_PORT", "25060"))
DB_NAME = os.getenv("DB_NAME", "defaultdb")
DB_USER = os.getenv("DB_USER", "pk")
DB_PASSWORD = os.getenv("DB_PASSWORD", "your_password_here")  # Set via environment variable
DB_SSL_MODE = os.getenv("DB_SSL_MODE", "require")

# ============================================================================
# DATABASE URLS
# ============================================================================

# SQLAlchemy connection URL
SQLALCHEMY_DATABASE_URL = (
    f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    f"?sslmode={DB_SSL_MODE}"
)

# psycopg2 connection string
PSYCOPG2_CONNECTION_STRING = (
    f"host={DB_HOST} port={DB_PORT} database={DB_NAME} "
    f"user={DB_USER} password={DB_PASSWORD} sslmode={DB_SSL_MODE}"
)

# ============================================================================
# CONNECTION POOL CONFIGURATION
# ============================================================================

SQLALCHEMY_CONFIG = {
    "url": SQLALCHEMY_DATABASE_URL,
    "echo": False,  # Set to True for SQL logging
    "pool_size": 10,
    "max_overflow": 20,
    "pool_recycle": 3600,  # Recycle connections every hour
    "pool_pre_ping": True,  # Verify connections before using
    "connect_args": {
        "connect_timeout": 10,
        "keepalives": 1,
        "keepalives_idle": 30,
    }
}

# ============================================================================
# GAME & PLATFORM CONFIGURATION
# ============================================================================

GAME_PLATFORMS = {
    "aviator": {
        "provider": "Spribe",
        "platforms": [
            {"code": "pmbetting", "url": "https://pmbetting.com"},
            {"code": "dafabet", "url": "https://dafabet.com"},
            {"code": "fun88", "url": "https://fun88.com"},
        ],
        "currency": "USD",
        "house_edge": 3.5,
    },
    "aviatrix": {
        "provider": "Aviatrix Labs",
        "platforms": [
            {"code": "aviatrix_labs", "url": "https://aviatrix.com"},
        ],
        "currency": "USD",
        "house_edge": 3.5,
    },
    "jetx": {
        "provider": "SmartSoft",
        "platforms": [
            {"code": "smartsoft", "url": "https://smartsoft.com"},
        ],
        "currency": "USD",
        "house_edge": 4.0,
    },
}

# ============================================================================
# STRATEGY CONFIGURATION
# ============================================================================

STRATEGIES = {
    "compound_1.33x": {
        "description": "Compound strategy targeting 1.33x multiplier",
        "min_multiplier": 1.30,
        "max_multiplier": 1.40,
        "stake_increment": 1.05,  # 5% increase per win
    },
    "martingale": {
        "description": "Classic Martingale strategy (double on loss)",
        "stake_multiplier_on_loss": 2.0,
        "min_multiplier": 1.50,
        "max_multiplier": 2.00,
    },
    "custom": {
        "description": "Custom user-defined strategy",
    },
    "fixed_stake": {
        "description": "Fixed stake per round",
        "stake": 10.0,
        "min_multiplier": 1.10,
        "max_multiplier": 3.00,
    },
    "kelly_criterion": {
        "description": "Kelly Criterion optimal sizing",
    },
}

# ============================================================================
# LOGGING CONFIGURATION
# ============================================================================

LOG_CONFIG = {
    "enable_file_logging": True,
    "log_directory": "./logs",
    "log_level": "INFO",
    "csv_logging": {
        "enable_realtime_csv": True,
        "csv_directory": "./data/csv_logs",
        "flush_interval": 100,  # Flush every 100 records
    },
}

# ============================================================================
# TABLE NAMES (For reference)
# ============================================================================

TABLES = {
    # Main tables
    "bot_vm_registration": "bot_vm_registration",
    "game_platform_config": "game_platform_config",
    "crash_game_rounds": "crash_game_rounds",

    # Analytics tables (3 main tables)
    "analytics_round_multipliers": "analytics_round_multipliers",
    "analytics_round_signals": "analytics_round_signals",
    "analytics_round_outcomes": "analytics_round_outcomes",

    # Supporting tables
    "ocr_validation_logs": "ocr_validation_logs",
    "error_logs": "error_logs",
    "session_logs": "session_logs",

    # Views
    "mv_daily_bot_stats": "mv_daily_bot_stats",
}

# ============================================================================
# ENUM TYPES (For reference)
# ============================================================================

ENUMS = {
    "game_type": ("aviator", "aviatrix", "jetx"),
    "vm_provider": ("vastai", "runpod", "digitalocean", "aws", "gcp", "local"),
    "strategy_type": ("compound_1.33x", "martingale", "custom", "fixed_stake", "kelly_criterion"),
    "round_outcome": ("WIN", "LOSS", "SKIP", "ERROR"),
    "error_type": (
        "bet_failed", "no_multiplier", "early_crash", "ocr_error",
        "network_drop", "timeout", "insufficient_balance", "unknown"
    ),
}
