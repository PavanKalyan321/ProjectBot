"""
Crash Game Analytics Database Package
PostgreSQL-based logging and analytics for Aviator, Aviatrix, JetX bots
"""

from .connection import (
    DatabaseConnection,
    init_db,
    get_session,
    session_scope,
)

from .logger import (
    log_crash_round,
    log_round_multiplier_analytics,
    log_round_signal,
    log_round_outcome,
    log_error,
    log_ocr_validation,
    create_session_log,
    update_session_log,
    log_batch_rounds,
)

from .models import (
    BotVMRegistration,
    GamePlatformConfig,
    CrashGameRound,
    AnalyticsRoundMultiplier,
    AnalyticsRoundSignal,
    AnalyticsRoundOutcome,
    SessionLog,
    ErrorLog,
    OCRValidationLog,
)

from .config import (
    DB_HOST,
    DB_PORT,
    DB_NAME,
    DB_USER,
    SQLALCHEMY_DATABASE_URL,
    GAME_PLATFORMS,
    STRATEGIES,
)

__all__ = [
    # Connection management
    "DatabaseConnection",
    "init_db",
    "get_session",
    "session_scope",

    # Logging functions
    "log_crash_round",
    "log_round_multiplier_analytics",
    "log_round_signal",
    "log_round_outcome",
    "log_error",
    "log_ocr_validation",
    "create_session_log",
    "update_session_log",
    "log_batch_rounds",

    # Models
    "BotVMRegistration",
    "GamePlatformConfig",
    "CrashGameRound",
    "AnalyticsRoundMultiplier",
    "AnalyticsRoundSignal",
    "AnalyticsRoundOutcome",
    "SessionLog",
    "ErrorLog",
    "OCRValidationLog",

    # Configuration
    "DB_HOST",
    "DB_PORT",
    "DB_NAME",
    "DB_USER",
    "SQLALCHEMY_DATABASE_URL",
    "GAME_PLATFORMS",
    "STRATEGIES",
]

__version__ = "1.0.0"
