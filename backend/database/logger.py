"""
Fast Logging Functions for Crash Game Round Data
Handles insertion of rounds, analytics, and signals into the database
"""

import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
from decimal import Decimal
from json import JSONEncoder

from .connection import DatabaseConnection, session_scope
from .models import (
    BotVMRegistration,
    CrashGameRound,
    AnalyticsRoundMultiplier,
    AnalyticsRoundSignal,
    AnalyticsRoundOutcome,
    SessionLog,
    ErrorLog,
    OCRValidationLog,
)

logger = logging.getLogger(__name__)

# ============================================================================
# ROUND LOGGING FUNCTIONS
# ============================================================================

def log_crash_round(
    bot_id: str,
    session_id: str,
    game_name: str,
    platform_code: str,
    round_number: int,
    stake_value: Decimal,
    crash_multiplier: Optional[Decimal] = None,
    cashout_multiplier: Optional[Decimal] = None,
    round_outcome: str = "SKIP",
    profit_loss: Optional[Decimal] = None,
    running_balance_before: Optional[Decimal] = None,
    running_balance_after: Optional[Decimal] = None,
    ocr_text: Optional[str] = None,
    ocr_confidence: Optional[float] = None,
    error_type: Optional[str] = None,
    error_description: Optional[str] = None,
    strategy_name: str = "custom",
    metadata: Optional[Dict[str, Any]] = None,
) -> Optional[int]:
    """
    Fast logging function for a complete crash game round.

    Args:
        bot_id: Bot identifier
        session_id: Session identifier
        game_name: Game type (aviator, aviatrix, jetx)
        platform_code: Platform code
        round_number: Round number in session
        stake_value: Stake amount
        crash_multiplier: Actual crash multiplier
        cashout_multiplier: Cashout multiplier
        round_outcome: WIN, LOSS, SKIP, ERROR
        profit_loss: Profit or loss amount
        running_balance_before: Balance before round
        running_balance_after: Balance after round
        ocr_text: Raw OCR text
        ocr_confidence: OCR confidence score (0-1)
        error_type: Type of error if occurred
        error_description: Error description
        metadata: Additional metadata as JSON

    Returns:
        int: Round ID if successful, None otherwise
    """
    try:
        with session_scope() as session:
            # Calculate financial metrics
            final_multiplier = cashout_multiplier if cashout_multiplier else crash_multiplier

            # Create round record
            round_record = CrashGameRound(
                bot_id=bot_id,
                session_id=session_id,
                game_name=game_name,
                platform_code=platform_code,
                round_number=round_number,
                round_start_timestamp=datetime.utcnow(),
                round_end_timestamp=datetime.utcnow(),
                stake_value=stake_value,
                strategy_name=strategy_name,
                crash_multiplier_detected=crash_multiplier,
                cashout_multiplier=cashout_multiplier,
                final_multiplier=final_multiplier,
                round_outcome=round_outcome,
                profit_loss_amount=profit_loss,
                running_balance_before=running_balance_before,
                running_balance_after=running_balance_after,
                ocr_raw_text=ocr_text,
                multiplier_detection_confidence=ocr_confidence,
                error_type=error_type,
                error_description=error_description,
                meta_data=metadata or {},
            )

            session.add(round_record)
            session.flush()  # Get the ID without committing
            round_id = round_record.id

            logger.info(f"✅ Logged round {round_number} for bot {bot_id}")
            return round_id

    except Exception as e:
        logger.error(f"❌ Failed to log round: {str(e)}")
        return None

# ============================================================================
# ANALYTICS LOGGING FUNCTIONS
# ============================================================================

def log_round_multiplier_analytics(
    round_id: int,
    round_external_id: Optional[str],
    multiplier: Decimal,
    bot_id: str,
    game_name: str,
    platform_code: Optional[str] = None,
    is_crash: bool = False,
    is_cashout: bool = False,
    is_max: bool = False,
    ocr_confidence: Optional[float] = None,
    data_quality_score: Optional[float] = None,
) -> Optional[int]:
    """
    Log multiplier data to analytics table 1 (for training/signals).

    Args:
        round_id: Link to main round
        round_external_id: External round ID
        multiplier: Multiplier value
        bot_id: Bot ID
        game_name: Game type
        platform_code: Platform code
        is_crash: Is this the crash multiplier?
        is_cashout: Is this the cashout multiplier?
        is_max: Is this the max multiplier in the round?
        ocr_confidence: OCR confidence score
        data_quality_score: Overall data quality

    Returns:
        int: Record ID if successful
    """
    try:
        with session_scope() as session:
            analytics = AnalyticsRoundMultiplier(
                round_id=round_id,
                round_external_id=round_external_id,
                multiplier=multiplier,
                timestamp=datetime.utcnow(),
                bot_id=bot_id,
                game_name=game_name,
                platform_code=platform_code,
                is_crash_multiplier=is_crash,
                is_cashout_multiplier=is_cashout,
                max_in_round=is_max,
                ocr_confidence=ocr_confidence,
                data_quality_score=data_quality_score,
                date_bucket=datetime.utcnow().strftime("%Y-%m-%d"),
            )

            session.add(analytics)
            session.flush()
            analytics_id = analytics.id

            logger.debug(f"✅ Logged multiplier analytics for round {round_id}")
            return analytics_id

    except Exception as e:
        logger.error(f"❌ Failed to log multiplier analytics: {str(e)}")
        return None

def log_round_signal(
    round_id: int,
    round_number: int,
    bot_id: str,
    game_name: str,
    signal_type: Optional[str] = None,
    confidence_score: Optional[float] = None,
    signal_strength: Optional[float] = None,
    time_to_crash_ms: Optional[int] = None,
    volatility: Optional[float] = None,
    momentum: Optional[float] = None,
    pattern_type: Optional[str] = None,
    similar_rounds: Optional[int] = None,
    feature_vector: Optional[Dict[str, Any]] = None,
) -> Optional[int]:
    """
    Log signal data to analytics table 2 (ML features/patterns).

    Args:
        round_id: Link to main round
        round_number: Round number
        bot_id: Bot ID
        game_name: Game type
        signal_type: Type of signal detected
        confidence_score: Confidence in signal (0-1)
        signal_strength: Strength of signal (0-1)
        time_to_crash_ms: Predicted time to crash
        volatility: Volatility measure
        momentum: Momentum score
        pattern_type: Pattern detected (exponential, linear, etc.)
        similar_rounds: Count of similar rounds
        feature_vector: JSON feature vector for ML

    Returns:
        int: Record ID if successful
    """
    try:
        with session_scope() as session:
            signal = AnalyticsRoundSignal(
                round_id=round_id,
                round_number=round_number,
                timestamp=datetime.utcnow(),
                bot_id=bot_id,
                game_name=game_name,
                signal_type=signal_type,
                confidence_score=confidence_score,
                signal_strength=signal_strength,
                time_to_crash_predicted_ms=time_to_crash_ms,
                volatility_measure=volatility,
                momentum_score=momentum,
                pattern_match_type=pattern_type,
                similar_rounds_count=similar_rounds,
                feature_vector=feature_vector or {},
                date_bucket=datetime.utcnow().strftime("%Y-%m-%d"),
            )

            session.add(signal)
            session.flush()
            signal_id = signal.id

            logger.debug(f"✅ Logged signal for round {round_id}")
            return signal_id

    except Exception as e:
        logger.error(f"❌ Failed to log signal: {str(e)}")
        return None

def log_round_outcome(
    round_id: int,
    round_number: int,
    bot_id: str,
    game_name: str,
    platform_code: Optional[str],
    strategy_name: Optional[str],
    outcome: str,
    profit_loss: Optional[Decimal],
    roi_percent: Optional[float],
    bet_amount: Optional[Decimal],
    winnings: Optional[Decimal],
    loss_amount: Optional[Decimal],
    target_multiplier: Optional[Decimal],
    actual_multiplier: Optional[Decimal],
    hit_target: Optional[bool] = None,
    win_streak: Optional[int] = None,
    loss_streak: Optional[int] = None,
    outcome_category: Optional[str] = None,
    duration_seconds: Optional[float] = None,
) -> Optional[int]:
    """
    Log outcome data to analytics table 3 (statistics/reporting).

    Args:
        round_id: Link to main round
        round_number: Round number
        bot_id: Bot ID
        game_name: Game type
        platform_code: Platform code
        strategy_name: Strategy used
        outcome: WIN, LOSS, SKIP, ERROR
        profit_loss: Profit/loss amount
        roi_percent: Return on investment %
        bet_amount: Bet amount
        winnings: Winnings if applicable
        loss_amount: Loss amount if applicable
        target_multiplier: Target multiplier
        actual_multiplier: Actual multiplier
        hit_target: Did it hit target?
        win_streak: Win streak length
        loss_streak: Loss streak length
        outcome_category: Category (big_win, small_loss, etc.)
        duration_seconds: Round duration

    Returns:
        int: Record ID if successful
    """
    try:
        with session_scope() as session:
            outcome = AnalyticsRoundOutcome(
                round_id=round_id,
                round_number=round_number,
                timestamp=datetime.utcnow(),
                bot_id=bot_id,
                game_name=game_name,
                platform_code=platform_code,
                strategy_name=strategy_name,
                outcome=outcome,
                profit_loss=profit_loss,
                roi_percent=roi_percent,
                bet_amount=bet_amount,
                winnings=winnings,
                loss_amount=loss_amount,
                target_multiplier=target_multiplier,
                actual_multiplier=actual_multiplier,
                hit_target=hit_target,
                win_streak_length=win_streak,
                loss_streak_length=loss_streak,
                outcome_category=outcome_category,
                duration_seconds=duration_seconds,
                date_bucket=datetime.utcnow().strftime("%Y-%m-%d"),
                hour_bucket=datetime.utcnow().hour,
            )

            session.add(outcome)
            session.flush()
            outcome_id = outcome.id

            logger.debug(f"✅ Logged outcome for round {round_id}")
            return outcome_id

    except Exception as e:
        logger.error(f"❌ Failed to log outcome: {str(e)}")
        return None

# ============================================================================
# ERROR LOGGING
# ============================================================================

def log_error(
    bot_id: str,
    session_id: Optional[str],
    round_id: Optional[int] = None,
    error_type: Optional[str] = None,
    error_message: Optional[str] = None,
    error_trace: Optional[str] = None,
    recovery_action: Optional[str] = None,
) -> Optional[int]:
    """
    Log an error occurrence.

    Args:
        bot_id: Bot identifier
        session_id: Session identifier
        round_id: Associated round ID
        error_type: Type of error
        error_message: Error message
        error_trace: Stack trace
        recovery_action: Recovery action taken

    Returns:
        int: Error log ID
    """
    try:
        with session_scope() as session:
            error_log = ErrorLog(
                bot_id=bot_id,
                session_id=session_id,
                round_id=round_id,
                error_type=error_type or "unknown",
                error_message=error_message,
                error_trace=error_trace,
                recovery_action=recovery_action,
                timestamp=datetime.utcnow(),
            )

            session.add(error_log)
            session.flush()
            error_id = error_log.id

            logger.warning(f"⚠️  Logged error for bot {bot_id}: {error_message}")
            return error_id

    except Exception as e:
        logger.error(f"❌ Failed to log error: {str(e)}")
        return None

# ============================================================================
# OCR VALIDATION LOGGING
# ============================================================================

def log_ocr_validation(
    bot_id: str,
    raw_ocr_text: str,
    round_id: Optional[int] = None,
    cleaned_value: Optional[Decimal] = None,
    confidence: Optional[float] = None,
    validation_status: Optional[str] = None,
) -> Optional[int]:
    """
    Log OCR validation for quality assurance.

    Args:
        bot_id: Bot identifier
        raw_ocr_text: Raw OCR output
        round_id: Associated round
        cleaned_value: Cleaned/parsed value
        confidence: Confidence score (0-1)
        validation_status: Validation status

    Returns:
        int: Log record ID
    """
    try:
        with session_scope() as session:
            ocr_log = OCRValidationLog(
                bot_id=bot_id,
                round_id=round_id,
                raw_ocr_text=raw_ocr_text,
                cleaned_value=cleaned_value,
                confidence=confidence,
                validation_status=validation_status,
                timestamp=datetime.utcnow(),
            )

            session.add(ocr_log)
            session.flush()
            log_id = ocr_log.id

            logger.debug(f"✅ Logged OCR validation for bot {bot_id}")
            return log_id

    except Exception as e:
        logger.error(f"❌ Failed to log OCR validation: {str(e)}")
        return None

# ============================================================================
# BATCH LOGGING
# ============================================================================

def log_batch_rounds(
    rounds_data: List[Dict[str, Any]]
) -> List[Optional[int]]:
    """
    Log multiple rounds in a single transaction (faster).

    Args:
        rounds_data: List of round data dictionaries

    Returns:
        List of round IDs
    """
    round_ids = []

    try:
        with session_scope() as session:
            for round_data in rounds_data:
                round_record = CrashGameRound(**round_data)
                session.add(round_record)

            session.flush()

            # Collect IDs
            for round_record in session.query(CrashGameRound).all():
                round_ids.append(round_record.id)

            logger.info(f"✅ Logged {len(round_ids)} rounds in batch")

    except Exception as e:
        logger.error(f"❌ Failed to log batch: {str(e)}")

    return round_ids

# ============================================================================
# SESSION LOGGING
# ============================================================================

def create_session_log(
    bot_id: str,
    session_id: str,
    game_name: str,
    initial_balance: Optional[Decimal] = None,
) -> Optional[int]:
    """
    Create a session log entry.

    Args:
        bot_id: Bot identifier
        session_id: Session identifier
        game_name: Game type
        initial_balance: Initial balance

    Returns:
        int: Session log ID
    """
    try:
        with session_scope() as session:
            session_log = SessionLog(
                bot_id=bot_id,
                session_id=session_id,
                game_name=game_name,
                initial_balance=initial_balance,
                start_time=datetime.utcnow(),
                status="active",
            )

            session.add(session_log)
            session.flush()
            log_id = session_log.id

            logger.info(f"✅ Created session log {session_id} for bot {bot_id}")
            return log_id

    except Exception as e:
        logger.error(f"❌ Failed to create session log: {str(e)}")
        return None

def update_session_log(
    session_id: str,
    final_balance: Optional[Decimal] = None,
    status: str = "completed",
    notes: Optional[str] = None,
) -> bool:
    """
    Update a session log with final statistics.

    Args:
        session_id: Session identifier
        final_balance: Final balance
        status: Session status
        notes: Additional notes

    Returns:
        bool: Success flag
    """
    try:
        with session_scope() as session:
            session_log = session.query(SessionLog).filter_by(
                session_id=session_id
            ).first()

            if not session_log:
                logger.error(f"Session log {session_id} not found")
                return False

            session_log.end_time = datetime.utcnow()
            session_log.final_balance = final_balance
            session_log.status = status
            session_log.notes = notes

            logger.info(f"✅ Updated session log {session_id}")
            return True

    except Exception as e:
        logger.error(f"❌ Failed to update session log: {str(e)}")
        return False
