"""
Example Usage Guide - Crash Game Analytics Database
Complete examples for integrating the database into your bot
"""

from decimal import Decimal
from datetime import datetime
import json
import logging

# Import database components
from backend.database.connection import DatabaseConnection, init_db, session_scope, get_session
from backend.database.logger import (
    log_crash_round,
    log_round_multiplier_analytics,
    log_round_signal,
    log_round_outcome,
    log_error,
    log_ocr_validation,
    create_session_log,
    update_session_log,
)
from backend.database.models import (
    BotVMRegistration,
    CrashGameRound,
    AnalyticsRoundMultiplier,
    SessionLog,
)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================================
# EXAMPLE 1: INITIALIZE DATABASE
# ============================================================================

def example_init_database():
    """
    Initialize the database and create all tables.
    Run this once before using the bot.
    """
    print("\n" + "="*80)
    print("EXAMPLE 1: Initialize Database")
    print("="*80)

    # Initialize database (creates tables if they don't exist)
    init_db(drop_existing=False)

    # Test connection
    if DatabaseConnection.test_connection():
        print("✅ Database is ready to use!")
    else:
        print("❌ Failed to connect to database")

# ============================================================================
# EXAMPLE 2: REGISTER A BOT
# ============================================================================

def example_register_bot():
    """
    Register a new bot instance in the database.
    Call this before starting a bot session.
    """
    print("\n" + "="*80)
    print("EXAMPLE 2: Register Bot")
    print("="*80)

    with session_scope() as session:
        # Create bot registration
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
        print(f"✅ Registered bot: {bot.bot_id}")
        print(f"   - Strategy: {bot.strategy_name}")
        print(f"   - Initial Balance: ${bot.initial_balance}")

# ============================================================================
# EXAMPLE 3: LOG A WINNING ROUND
# ============================================================================

def example_log_winning_round():
    """
    Log a complete winning round with all analytics.
    """
    print("\n" + "="*80)
    print("EXAMPLE 3: Log Winning Round")
    print("="*80)

    # Step 1: Log main round
    round_id = log_crash_round(
        bot_id="aviator_bot_001",
        session_id="session_20251121_001",
        game_name="aviator",
        platform_code="dafabet",
        round_number=1,
        stake_value=Decimal("10.00"),
        crash_multiplier=Decimal("2.45"),
        cashout_multiplier=Decimal("1.33"),  # Won at 1.33x
        round_outcome="WIN",
        profit_loss=Decimal("3.30"),  # (1.33 - 1) * 10
        running_balance_before=Decimal("1000.00"),
        running_balance_after=Decimal("1003.30"),
        ocr_text="1.33x",
        ocr_confidence=0.95,
        metadata={
            "strategy_applied": "compound_1.33x",
            "prediction_correct": True,
            "volatility": 0.75,
        }
    )

    if round_id:
        print(f"✅ Round logged: ID {round_id}")

        # Step 2: Log multiplier analytics (for training)
        log_round_multiplier_analytics(
            round_id=round_id,
            round_external_id="ext_001",
            multiplier=Decimal("1.33"),
            bot_id="aviator_bot_001",
            game_name="aviator",
            platform_code="dafabet",
            is_crash=False,
            is_cashout=True,
            is_max=False,
            ocr_confidence=0.95,
            data_quality_score=0.98,
        )
        print("✅ Logged multiplier analytics")

        # Step 3: Log outcome statistics
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
            bet_amount=Decimal("10.00"),
            winnings=Decimal("13.30"),
            loss_amount=None,
            target_multiplier=Decimal("1.33"),
            actual_multiplier=Decimal("1.33"),
            hit_target=True,
            win_streak=1,
            loss_streak=0,
            outcome_category="small_win",
            duration_seconds=4.2,
        )
        print("✅ Logged outcome statistics")

        # Step 4: Log signal for ML training
        log_round_signal(
            round_id=round_id,
            round_number=1,
            bot_id="aviator_bot_001",
            game_name="aviator",
            signal_type="early_flight",
            confidence_score=0.92,
            signal_strength=0.87,
            time_to_crash_ms=3200,
            volatility=0.65,
            momentum=0.78,
            pattern_type="exponential",
            similar_rounds=145,
            feature_vector={
                "pre_flight_variance": 0.12,
                "acceleration_rate": 0.089,
                "price_distance": 0.35,
                "player_density": 0.67,
            }
        )
        print("✅ Logged signal data")

# ============================================================================
# EXAMPLE 4: LOG A LOSING ROUND
# ============================================================================

def example_log_losing_round():
    """
    Log a losing round (crashed before cashout).
    """
    print("\n" + "="*80)
    print("EXAMPLE 4: Log Losing Round")
    print("="*80)

    round_id = log_crash_round(
        bot_id="aviator_bot_001",
        session_id="session_20251121_001",
        game_name="aviator",
        platform_code="dafabet",
        round_number=2,
        stake_value=Decimal("10.55"),  # Increased stake after win
        crash_multiplier=Decimal("1.15"),  # Crashed early
        cashout_multiplier=None,  # Didn't get to cashout
        round_outcome="LOSS",
        profit_loss=Decimal("-10.55"),
        running_balance_before=Decimal("1003.30"),
        running_balance_after=Decimal("992.75"),
        ocr_text="1.15x",
        ocr_confidence=0.94,
        metadata={
            "strategy_applied": "compound_1.33x",
            "prediction_correct": False,
            "early_crash": True,
        }
    )

    if round_id:
        print(f"✅ Loss round logged: ID {round_id}")

        # Log the analytics
        log_round_multiplier_analytics(
            round_id=round_id,
            round_external_id="ext_002",
            multiplier=Decimal("1.15"),
            bot_id="aviator_bot_001",
            game_name="aviator",
            is_crash=True,
            ocr_confidence=0.94,
            data_quality_score=0.97,
        )

        log_round_outcome(
            round_id=round_id,
            round_number=2,
            bot_id="aviator_bot_001",
            game_name="aviator",
            platform_code="dafabet",
            strategy_name="compound_1.33x",
            outcome="LOSS",
            profit_loss=Decimal("-10.55"),
            roi_percent=-1.05,
            bet_amount=Decimal("10.55"),
            winnings=None,
            loss_amount=Decimal("10.55"),
            target_multiplier=Decimal("1.33"),
            actual_multiplier=Decimal("1.15"),
            hit_target=False,
            win_streak=0,
            loss_streak=1,
            outcome_category="small_loss",
            duration_seconds=2.1,
        )

        print("✅ Loss analytics logged")

# ============================================================================
# EXAMPLE 5: HANDLE ERRORS
# ============================================================================

def example_log_error():
    """
    Log errors that occur during betting.
    """
    print("\n" + "="*80)
    print("EXAMPLE 5: Log Error")
    print("="*80)

    error_id = log_error(
        bot_id="aviator_bot_001",
        session_id="session_20251121_001",
        round_id=None,
        error_type="ocr_error",
        error_message="Failed to read multiplier from screen",
        error_trace="Traceback: ...",
        recovery_action="Retry OCR with enhanced preprocessing",
    )

    if error_id:
        print(f"✅ Error logged: ID {error_id}")

# ============================================================================
# EXAMPLE 6: LOG OCR VALIDATION DATA
# ============================================================================

def example_log_ocr_validation():
    """
    Log OCR validation data for quality assessment.
    """
    print("\n" + "="*80)
    print("EXAMPLE 6: Log OCR Validation")
    print("="*80)

    log_ocr_validation(
        bot_id="aviator_bot_001",
        raw_ocr_text="1.33x",
        round_id=1,
        cleaned_value=Decimal("1.33"),
        confidence=0.95,
        validation_status="VALID",
    )
    print("✅ OCR validation logged")

# ============================================================================
# EXAMPLE 7: CREATE AND UPDATE SESSION
# ============================================================================

def example_session_logging():
    """
    Create and update a session log.
    """
    print("\n" + "="*80)
    print("EXAMPLE 7: Session Logging")
    print("="*80)

    # Create session
    session_id = create_session_log(
        bot_id="aviator_bot_001",
        session_id="session_20251121_001",
        game_name="aviator",
        initial_balance=Decimal("1000.00"),
    )
    print(f"✅ Session created: {session_id}")

    # Later, update session with final stats
    update_session_log(
        session_id="session_20251121_001",
        final_balance=Decimal("1050.25"),
        status="completed",
        notes="Successful session with 5% ROI",
    )
    print("✅ Session updated")

# ============================================================================
# EXAMPLE 8: QUERY ROUNDS
# ============================================================================

def example_query_rounds():
    """
    Query and analyze logged rounds.
    """
    print("\n" + "="*80)
    print("EXAMPLE 8: Query Rounds")
    print("="*80)

    with session_scope() as session:
        # Get all rounds for a bot
        rounds = session.query(CrashGameRound).filter_by(
            bot_id="aviator_bot_001"
        ).all()

        print(f"Total rounds: {len(rounds)}")

        # Calculate statistics
        wins = sum(1 for r in rounds if r.round_outcome == "WIN")
        losses = sum(1 for r in rounds if r.round_outcome == "LOSS")
        total_profit = sum(r.profit_loss_amount for r in rounds if r.profit_loss_amount)

        print(f"Wins: {wins}, Losses: {losses}")
        print(f"Total Profit/Loss: ${total_profit:.2f}")

        if rounds:
            print("\nLast 5 rounds:")
            for r in rounds[-5:]:
                print(f"  Round {r.round_number}: {r.round_outcome} - Multiplier: {r.final_multiplier}")

# ============================================================================
# EXAMPLE 9: EXPORT DATA FOR ML TRAINING
# ============================================================================

def example_export_for_ml():
    """
    Export analytics data for ML training.
    """
    print("\n" + "="*80)
    print("EXAMPLE 9: Export Data for ML Training")
    print("="*80)

    with session_scope() as session:
        # Get multiplier data
        multipliers = session.query(AnalyticsRoundMultiplier).filter_by(
            bot_id="aviator_bot_001"
        ).all()

        print(f"Total multiplier records: {len(multipliers)}")

        # Export to format suitable for ML
        training_data = []
        for m in multipliers[:10]:  # First 10 for example
            training_data.append({
                "round_id": m.round_id,
                "multiplier": float(m.multiplier),
                "timestamp": m.timestamp.isoformat(),
                "bot_id": m.bot_id,
                "game_name": m.game_name,
                "is_crash": m.is_crash_multiplier,
                "is_cashout": m.is_cashout_multiplier,
                "confidence": float(m.ocr_confidence) if m.ocr_confidence else None,
            })

        print("✅ Training data exported:")
        print(json.dumps(training_data[:2], indent=2))

# ============================================================================
# EXAMPLE 10: COMPLETE BOT INTEGRATION
# ============================================================================

def example_bot_integration():
    """
    Complete example of integrating logging into a bot loop.
    This shows how to use the database in real bot code.
    """
    print("\n" + "="*80)
    print("EXAMPLE 10: Bot Integration")
    print("="*80)

    # Initialize database
    DatabaseConnection.initialize()

    # Start session
    session_id = create_session_log(
        bot_id="aviator_bot_001",
        session_id="session_20251121_001",
        game_name="aviator",
        initial_balance=Decimal("1000.00"),
    )

    print(f"Starting bot session: {session_id}")

    # Simulate bot rounds
    current_balance = Decimal("1000.00")
    stake = Decimal("10.00")
    round_number = 0

    for i in range(3):  # Simulate 3 rounds
        round_number += 1

        # Simulate round result
        import random
        crash_mult = Decimal(str(round(random.uniform(1.0, 5.0), 2)))
        target_mult = Decimal("1.33")

        if crash_mult >= target_mult:
            # WIN
            outcome = "WIN"
            profit = (target_mult - 1) * stake
            current_balance += profit
        else:
            # LOSS
            outcome = "LOSS"
            profit = -stake
            current_balance += profit

        # Log the round
        log_crash_round(
            bot_id="aviator_bot_001",
            session_id=session_id,
            game_name="aviator",
            platform_code="dafabet",
            round_number=round_number,
            stake_value=stake,
            crash_multiplier=crash_mult,
            cashout_multiplier=target_mult if outcome == "WIN" else None,
            round_outcome=outcome,
            profit_loss=profit,
            running_balance_before=current_balance - profit,
            running_balance_after=current_balance,
            metadata={"round_sequence": i},
        )

        print(f"Round {round_number}: {outcome} - Balance: ${current_balance}")

    # Close session
    update_session_log(
        session_id=session_id,
        final_balance=current_balance,
        status="completed",
    )

    print(f"✅ Session completed with final balance: ${current_balance}")

# ============================================================================
# RUN ALL EXAMPLES
# ============================================================================

if __name__ == "__main__":
    print("\n" + "="*80)
    print("CRASH GAME ANALYTICS DATABASE - USAGE EXAMPLES")
    print("="*80)

    try:
        # Initialize database first
        example_init_database()

        # Register bot
        example_register_bot()

        # Log rounds
        example_log_winning_round()
        example_log_losing_round()

        # Handle errors and OCR
        example_log_error()
        example_log_ocr_validation()

        # Session management
        example_session_logging()

        # Query data
        example_query_rounds()

        # Export for ML
        example_export_for_ml()

        # Complete integration
        example_bot_integration()

        print("\n" + "="*80)
        print("✅ ALL EXAMPLES COMPLETED SUCCESSFULLY")
        print("="*80)

    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
