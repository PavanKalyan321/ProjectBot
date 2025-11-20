"""
SQLAlchemy ORM Models for Crash Game Analytics Database
Supports: Aviator, Aviatrix, JetX
"""

from datetime import datetime
from typing import Optional
from decimal import Decimal
from sqlalchemy import (
    create_engine, Column, Integer, String, DateTime, Float, Boolean,
    Text, ForeignKey, Numeric, Index, DECIMAL, func, LargeBinary, JSON
)
from sqlalchemy.dialects.postgresql import ENUM, JSONB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, Session
from sqlalchemy.sql import expression

Base = declarative_base()

# ============================================================================
# ENUM DEFINITIONS (matching PostgreSQL enums)
# ============================================================================

GameType = ENUM(
    'aviator', 'aviatrix', 'jetx',
    name='game_type'
)

VMProvider = ENUM(
    'vastai', 'runpod', 'digitalocean', 'aws', 'gcp', 'local',
    name='vm_provider'
)

StrategyType = ENUM(
    'compound_1.33x', 'martingale', 'custom', 'fixed_stake', 'kelly_criterion',
    name='strategy_type'
)

RoundOutcome = ENUM(
    'WIN', 'LOSS', 'SKIP', 'ERROR',
    name='round_outcome'
)

ErrorType = ENUM(
    'bet_failed', 'no_multiplier', 'early_crash', 'ocr_error',
    'network_drop', 'timeout', 'insufficient_balance', 'unknown',
    name='error_type'
)

# ============================================================================
# SECTION 1: BOT / VM REGISTRATION MODEL
# ============================================================================

class BotVMRegistration(Base):
    """
    Bot and VM registration table.
    Identifies unique bot instances and their virtual machine configuration.
    """
    __tablename__ = "bot_vm_registration"

    id = Column(Integer, primary_key=True)
    bot_id = Column(String(50), unique=True, nullable=False, index=True)
    bot_name = Column(String(100), nullable=False)
    vm_name = Column(String(100), nullable=False)
    vm_provider = Column(VMProvider, nullable=False)
    region = Column(String(50), nullable=False)
    session_id = Column(String(100), unique=True, nullable=False)
    strategy_name = Column(StrategyType, nullable=False)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)

    # Configuration
    initial_balance = Column(DECIMAL(15, 2), nullable=True)
    base_stake = Column(DECIMAL(15, 2), nullable=True)
    max_stake = Column(DECIMAL(15, 2), nullable=True)

    # Relationships
    crash_rounds = relationship("CrashGameRound", back_populates="bot_vm")
    error_logs = relationship("ErrorLog", back_populates="bot_vm")

    def __repr__(self):
        return f"<BotVMRegistration(bot_id='{self.bot_id}', strategy='{self.strategy_name}')>"

# ============================================================================
# SECTION 2: GAME PLATFORM CONFIG MODEL
# ============================================================================

class GamePlatformConfig(Base):
    """
    Game and platform configuration.
    Stores information about different crash games and their platforms.
    """
    __tablename__ = "game_platform_config"

    id = Column(Integer, primary_key=True)
    game_name = Column(GameType, nullable=False)
    platform_code = Column(String(50), nullable=False)
    platform_url = Column(String(255), nullable=True)
    round_external_id_format = Column(String(100), nullable=True)
    currency = Column(String(10), default='USD')

    # RTP and game characteristics
    house_edge_percent = Column(DECIMAL(5, 2), nullable=True)
    min_multiplier = Column(DECIMAL(10, 2), default=1.0)
    max_multiplier = Column(DECIMAL(10, 2), default=1000.0)

    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)

    def __repr__(self):
        return f"<GamePlatformConfig(game='{self.game_name}', platform='{self.platform_code}')>"

# ============================================================================
# MAIN ROUNDS TABLE MODEL
# ============================================================================

class CrashGameRound(Base):
    """
    Main rounds table - Complete round history.
    Stores every round detail including stake, multipliers, outcomes, and financials.
    """
    __tablename__ = "crash_game_rounds"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Bot / VM Identification
    bot_id = Column(String(50), ForeignKey("bot_vm_registration.bot_id"), nullable=False, index=True)
    session_id = Column(String(100), nullable=False, index=True)

    # Platform & Game Details
    game_name = Column(GameType, nullable=False, index=True)
    platform_code = Column(String(50), nullable=False)
    round_external_id = Column(String(100), nullable=True)
    currency = Column(String(10), nullable=True)

    # SECTION 3: Round Timing
    round_number = Column(Integer, nullable=False)
    round_start_timestamp = Column(DateTime, nullable=False, index=True)
    round_end_timestamp = Column(DateTime, nullable=True)
    duration_seconds = Column(DECIMAL(10, 3), nullable=True)
    processing_time_ms = Column(Integer, nullable=True)

    # SECTION 4: Stake & Strategy
    stake_value = Column(DECIMAL(15, 2), nullable=False)
    stake_before_update = Column(DECIMAL(15, 2), nullable=True)
    stake_after_update = Column(DECIMAL(15, 2), nullable=True)
    strategy_name = Column(StrategyType, nullable=False)
    target_multiplier = Column(DECIMAL(10, 4), nullable=True)
    manual_override_flag = Column(Boolean, default=False)
    stake_placement_result = Column(String(50), nullable=True)

    # SECTION 5: Multipliers
    crash_multiplier_detected = Column(DECIMAL(10, 4), nullable=True)
    cashout_multiplier = Column(DECIMAL(10, 4), nullable=True)
    final_multiplier = Column(DECIMAL(10, 4), nullable=True)
    multiplier_source = Column(String(50), nullable=True)  # 'ocr', 'api', 'manual'

    # SECTION 6: Financials
    cashout_amount = Column(DECIMAL(15, 2), nullable=True)
    profit_loss_amount = Column(DECIMAL(15, 2), nullable=True)
    running_balance_before = Column(DECIMAL(15, 2), nullable=True)
    running_balance_after = Column(DECIMAL(15, 2), nullable=True)
    expected_profit = Column(DECIMAL(15, 2), nullable=True)
    variance_from_strategy = Column(DECIMAL(15, 2), nullable=True)
    roi_percent = Column(DECIMAL(10, 4), nullable=True)

    # SECTION 7: OCR / Detection Logs
    ocr_raw_text = Column(Text, nullable=True)
    ocr_cleaned_value = Column(DECIMAL(10, 4), nullable=True)
    multiplier_detection_confidence = Column(DECIMAL(5, 4), nullable=True)
    cashout_detection_confidence = Column(DECIMAL(5, 4), nullable=True)
    ocr_timeout_flag = Column(Boolean, default=False)
    screenshot_reference_id = Column(String(100), nullable=True)

    # SECTION 8: Outcome & Errors
    round_outcome = Column(RoundOutcome, nullable=True)
    error_type = Column(ErrorType, nullable=True)
    error_description = Column(Text, nullable=True)
    recovery_action_taken = Column(String(255), nullable=True)
    retry_count = Column(Integer, default=0)

    # SECTION 9: Metadata (JSONB)
    metadata = Column(JSONB, nullable=True)

    # Record management
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    bot_vm = relationship("BotVMRegistration", back_populates="crash_rounds")
    analytics_multipliers = relationship("AnalyticsRoundMultiplier", back_populates="crash_round")
    analytics_signals = relationship("AnalyticsRoundSignal", back_populates="crash_round")
    analytics_outcomes = relationship("AnalyticsRoundOutcome", back_populates="crash_round")

    # Indexes (defined in create_indexes function)

    def __repr__(self):
        return (f"<CrashGameRound(bot_id='{self.bot_id}', "
                f"round={self.round_number}, outcome='{self.round_outcome}')>")

    def to_dict(self):
        """Convert model to dictionary for API responses."""
        return {
            'id': self.id,
            'bot_id': self.bot_id,
            'round_number': self.round_number,
            'game_name': self.game_name,
            'stake_value': float(self.stake_value) if self.stake_value else None,
            'crash_multiplier': float(self.crash_multiplier_detected) if self.crash_multiplier_detected else None,
            'cashout_multiplier': float(self.cashout_multiplier) if self.cashout_multiplier else None,
            'profit_loss': float(self.profit_loss_amount) if self.profit_loss_amount else None,
            'outcome': self.round_outcome,
            'timestamp': self.round_start_timestamp.isoformat() if self.round_start_timestamp else None,
        }

# ============================================================================
# ANALYTICS TABLE 1: ROUND MULTIPLIER DATA
# ============================================================================

class AnalyticsRoundMultiplier(Base):
    """
    Analytics table 1: Round multiplier data for training and signal generation.
    Core fields: roundid, multiplier, timestamp
    """
    __tablename__ = "analytics_round_multipliers"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Core training fields
    round_id = Column(Integer, ForeignKey("crash_game_rounds.id"), nullable=False, index=True)
    round_external_id = Column(String(100), nullable=True)
    multiplier = Column(DECIMAL(10, 4), nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False, index=True)

    # Additional context for ML
    bot_id = Column(String(50), nullable=False, index=True)
    game_name = Column(GameType, nullable=False)
    platform_code = Column(String(50), nullable=True)

    # Multiplier characteristics
    is_crash_multiplier = Column(Boolean, default=False)
    is_cashout_multiplier = Column(Boolean, default=False)
    max_in_round = Column(Boolean, default=False)

    # Confidence and quality
    ocr_confidence = Column(DECIMAL(5, 4), nullable=True)
    data_quality_score = Column(DECIMAL(5, 4), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    date_bucket = Column(String(10), nullable=True)  # YYYY-MM-DD for aggregation

    # Relationships
    crash_round = relationship("CrashGameRound", back_populates="analytics_multipliers")

    def __repr__(self):
        return f"<AnalyticsRoundMultiplier(round_id={self.round_id}, multiplier={self.multiplier})>"

# ============================================================================
# ANALYTICS TABLE 2: ROUND SIGNALS & PREDICTIONS
# ============================================================================

class AnalyticsRoundSignal(Base):
    """
    Analytics table 2: Round signals and predictions for ML feature generation.
    Used for pattern detection and signal generation.
    """
    __tablename__ = "analytics_round_signals"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Link to main round
    round_id = Column(Integer, ForeignKey("crash_game_rounds.id"), nullable=False, index=True)
    round_number = Column(Integer, nullable=False)
    timestamp = Column(DateTime, nullable=False, index=True)

    # Bot context
    bot_id = Column(String(50), nullable=False, index=True)
    game_name = Column(GameType, nullable=False)

    # Signal features (pre-computed for ML)
    signal_type = Column(String(100), nullable=True, index=True)  # 'pre_flight', 'early_flight', etc.
    confidence_score = Column(DECIMAL(5, 4), nullable=True, index=True)
    signal_strength = Column(DECIMAL(5, 4), nullable=True)

    # Timing signals
    time_to_crash_predicted_ms = Column(Integer, nullable=True)
    volatility_measure = Column(DECIMAL(10, 6), nullable=True)
    momentum_score = Column(DECIMAL(5, 4), nullable=True)

    # Pattern recognition
    pattern_match_type = Column(String(100), nullable=True, index=True)  # 'exponential', 'linear', etc.
    similar_rounds_count = Column(Integer, nullable=True)

    # Outcome tracking
    signal_correctness = Column(Boolean, nullable=True)
    actual_multiplier = Column(DECIMAL(10, 4), nullable=True)
    prediction_error = Column(DECIMAL(10, 4), nullable=True)

    # Feature vector (JSON for complex data)
    feature_vector = Column(JSONB, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    date_bucket = Column(String(10), nullable=True)

    # Relationships
    crash_round = relationship("CrashGameRound", back_populates="analytics_signals")

    def __repr__(self):
        return f"<AnalyticsRoundSignal(round_id={self.round_id}, signal_type='{self.signal_type}')>"

# ============================================================================
# ANALYTICS TABLE 3: ROUND OUTCOME & STATISTICS
# ============================================================================

class AnalyticsRoundOutcome(Base):
    """
    Analytics table 3: Round outcomes and statistics.
    Denormalized table for fast reporting and aggregation.
    """
    __tablename__ = "analytics_round_outcomes"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Link to main round
    round_id = Column(Integer, ForeignKey("crash_game_rounds.id"), nullable=False, index=True)
    round_number = Column(Integer, nullable=False)
    timestamp = Column(DateTime, nullable=False, index=True)

    # Bot context
    bot_id = Column(String(50), nullable=False, index=True)
    game_name = Column(GameType, nullable=False)
    platform_code = Column(String(50), nullable=True)
    strategy_name = Column(StrategyType, nullable=True, index=True)

    # Outcome
    outcome = Column(RoundOutcome, nullable=False, index=True)
    profit_loss = Column(DECIMAL(15, 2), nullable=True)
    roi_percent = Column(DECIMAL(10, 4), nullable=True)

    # Statistical metrics
    bet_amount = Column(DECIMAL(15, 2), nullable=True)
    winnings = Column(DECIMAL(15, 2), nullable=True)
    loss_amount = Column(DECIMAL(15, 2), nullable=True)

    # Multiplier data
    target_multiplier = Column(DECIMAL(10, 4), nullable=True)
    actual_multiplier = Column(DECIMAL(10, 4), nullable=True)
    multiplier_error = Column(DECIMAL(10, 4), nullable=True)
    hit_target = Column(Boolean, nullable=True)

    # Streaks
    win_streak_length = Column(Integer, nullable=True)
    loss_streak_length = Column(Integer, nullable=True)

    # Classification
    outcome_category = Column(String(50), nullable=True)  # 'big_win', 'small_win', etc.

    # Timing
    duration_seconds = Column(DECIMAL(10, 3), nullable=True)
    date_bucket = Column(String(10), nullable=True)
    hour_bucket = Column(Integer, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    crash_round = relationship("CrashGameRound", back_populates="analytics_outcomes")

    def __repr__(self):
        return f"<AnalyticsRoundOutcome(round_id={self.round_id}, outcome='{self.outcome}')>"

# ============================================================================
# SUPPORTING TABLE MODELS
# ============================================================================

class OCRValidationLog(Base):
    """OCR validation logs for quality assurance."""
    __tablename__ = "ocr_validation_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    round_id = Column(Integer, ForeignKey("crash_game_rounds.id"), nullable=True, index=True)
    bot_id = Column(String(50), nullable=False, index=True)

    raw_ocr_text = Column(Text, nullable=False)
    cleaned_value = Column(DECIMAL(10, 4), nullable=True)
    confidence = Column(DECIMAL(5, 4), nullable=True)
    validation_status = Column(String(50), nullable=True)

    timestamp = Column(DateTime, default=datetime.utcnow, index=True)

    def __repr__(self):
        return f"<OCRValidationLog(bot_id='{self.bot_id}', confidence={self.confidence})>"

class ErrorLog(Base):
    """Error logs for debugging and analysis."""
    __tablename__ = "error_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    round_id = Column(Integer, ForeignKey("crash_game_rounds.id"), nullable=True, index=True)
    bot_id = Column(String(50), ForeignKey("bot_vm_registration.bot_id"), nullable=False, index=True)
    session_id = Column(String(100), nullable=True)

    error_type = Column(ErrorType, nullable=False, index=True)
    error_message = Column(Text, nullable=True)
    error_trace = Column(Text, nullable=True)
    recovery_action = Column(String(255), nullable=True)

    timestamp = Column(DateTime, default=datetime.utcnow, index=True)

    # Relationships
    bot_vm = relationship("BotVMRegistration", back_populates="error_logs")

    def __repr__(self):
        return f"<ErrorLog(bot_id='{self.bot_id}', error_type='{self.error_type}')>"

class SessionLog(Base):
    """Session logs for tracking bot sessions."""
    __tablename__ = "session_logs"

    id = Column(Integer, primary_key=True)
    bot_id = Column(String(50), nullable=False, index=True)
    session_id = Column(String(100), unique=True, nullable=False)
    game_name = Column(GameType, nullable=False)

    start_time = Column(DateTime, default=datetime.utcnow)
    end_time = Column(DateTime, nullable=True)
    duration_seconds = Column(DECIMAL(10, 3), nullable=True)

    initial_balance = Column(DECIMAL(15, 2), nullable=True)
    final_balance = Column(DECIMAL(15, 2), nullable=True)
    total_profit_loss = Column(DECIMAL(15, 2), nullable=True)
    total_roi_percent = Column(DECIMAL(10, 4), nullable=True)

    total_rounds = Column(Integer, nullable=True)
    winning_rounds = Column(Integer, nullable=True)
    losing_rounds = Column(Integer, nullable=True)
    win_rate = Column(DECIMAL(5, 4), nullable=True)

    largest_win = Column(DECIMAL(15, 2), nullable=True)
    largest_loss = Column(DECIMAL(15, 2), nullable=True)
    average_win = Column(DECIMAL(15, 2), nullable=True)
    average_loss = Column(DECIMAL(15, 2), nullable=True)

    status = Column(String(50), nullable=True)  # 'active', 'completed', 'error', 'interrupted'
    notes = Column(Text, nullable=True)

    def __repr__(self):
        return f"<SessionLog(session_id='{self.session_id}', game='{self.game_name}')>"

    def to_dict(self):
        """Convert model to dictionary for API responses."""
        return {
            'session_id': self.session_id,
            'bot_id': self.bot_id,
            'game_name': self.game_name,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'total_rounds': self.total_rounds,
            'win_rate': float(self.win_rate) if self.win_rate else None,
            'total_profit_loss': float(self.total_profit_loss) if self.total_profit_loss else None,
            'status': self.status,
        }
