"""
Test Database Insertion Script
Creates sample records for all tables to verify database is working
"""

from decimal import Decimal
from datetime import datetime
from backend.database import (
    init_db,
    session_scope,
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
    GamePlatformConfig,
    CrashGameRound,
    AnalyticsRoundMultiplier,
    AnalyticsRoundSignal,
    AnalyticsRoundOutcome,
    SessionLog,
    ErrorLog,
    OCRValidationLog,
)
from sqlalchemy import text, inspect

def print_header(text_str):
    """Print formatted header"""
    print("\n" + "="*80)
    print(f"  {text_str}")
    print("="*80)

def print_success(text_str):
    """Print success message"""
    print(f"[OK] {text_str}")

def print_error(text_str):
    """Print error message"""
    print(f"[ERROR] {text_str}")

def test_database_connection():
    """Test database connection"""
    print_header("STEP 1: Testing Database Connection")

    try:
        init_db(drop_existing=False)
        print_success("Database connection successful")
        print_success("All tables created/verified")
        return True
    except Exception as e:
        print_error(f"Database connection failed: {e}")
        return False

def insert_bot_registration():
    """Insert bot registration record"""
    print_header("STEP 2: Insert Bot Registration")

    try:
        with session_scope() as session:
            bot = BotVMRegistration(
                bot_id="test_bot_001",
                bot_name="Test Aviator Bot",
                vm_name="test-vm-1",
                vm_provider="digitalocean",
                region="nyc3",
                session_id="test_session_001",
                strategy_name="compound_1.33x",
                initial_balance=Decimal("1000.00"),
                base_stake=Decimal("10.00"),
                max_stake=Decimal("100.00"),
            )
            session.add(bot)
            session.flush()
            bot_id = bot.id

        print_success(f"Bot registered: test_bot_001 (ID: {bot_id})")
        return bot_id
    except Exception as e:
        print_error(f"Failed to insert bot: {e}")
        return None

def insert_game_platform_config():
    """Insert game platform config"""
    print_header("STEP 3: Insert Game Platform Config")

    try:
        with session_scope() as session:
            # Aviator
            game1 = GamePlatformConfig(
                game_name="aviator",
                platform_code="dafabet",
                platform_url="https://dafabet.com",
                currency="USD",
                house_edge_percent=Decimal("3.50"),
                min_multiplier=Decimal("1.00"),
                max_multiplier=Decimal("1000.00"),
            )
            session.add(game1)

            # Aviatrix
            game2 = GamePlatformConfig(
                game_name="aviatrix",
                platform_code="aviatrix_labs",
                platform_url="https://aviatrix.com",
                currency="USD",
                house_edge_percent=Decimal("3.50"),
            )
            session.add(game2)

            # JetX
            game3 = GamePlatformConfig(
                game_name="jetx",
                platform_code="smartsoft",
                platform_url="https://smartsoft.com",
                currency="USD",
                house_edge_percent=Decimal("4.00"),
            )
            session.add(game3)
            session.flush()

        print_success("Inserted game platform configs:")
        print("  - Aviator (Dafabet)")
        print("  - Aviatrix (Aviatrix Labs)")
        print("  - JetX (SmartSoft)")
        return True
    except Exception as e:
        print_error(f"Failed to insert game config: {e}")
        return False

def insert_crash_game_round():
    """Insert crash game round record"""
    print_header("STEP 4: Insert Crash Game Round")

    try:
        round_id = log_crash_round(
            bot_id="test_bot_001",
            session_id="test_session_001",
            game_name="aviator",
            platform_code="dafabet",
            round_number=1,
            stake_value=Decimal("10.00"),
            strategy_name="compound_1.33x",
            crash_multiplier=Decimal("2.45"),
            cashout_multiplier=Decimal("1.33"),
            round_outcome="WIN",
            profit_loss=Decimal("3.30"),
            running_balance_before=Decimal("1000.00"),
            running_balance_after=Decimal("1003.30"),
            ocr_text="1.33x",
            ocr_confidence=0.95,
            metadata={
                "strategy": "compound_1.33x",
                "prediction_correct": True,
                "volatility": 0.75,
            }
        )

        if round_id:
            print_success(f"Crash game round inserted (ID: {round_id})")
            return round_id
        else:
            print_error("Failed to insert crash game round")
            return None
    except Exception as e:
        print_error(f"Failed to insert round: {e}")
        return None

def insert_analytics_multipliers(round_id):
    """Insert analytics multiplier record"""
    print_header("STEP 5: Insert Analytics Round Multipliers")

    if not round_id:
        print_error("No round_id provided, skipping")
        return False

    try:
        analytics_id = log_round_multiplier_analytics(
            round_id=round_id,
            round_external_id="ext_001",
            multiplier=Decimal("1.33"),
            bot_id="test_bot_001",
            game_name="aviator",
            platform_code="dafabet",
            is_crash=False,
            is_cashout=True,
            is_max=False,
            ocr_confidence=0.95,
            data_quality_score=0.98,
        )

        if analytics_id:
            print_success(f"Analytics multiplier inserted (ID: {analytics_id})")
            return True
        else:
            print_error("Failed to insert analytics multiplier")
            return False
    except Exception as e:
        print_error(f"Failed to insert analytics multiplier: {e}")
        return False

def insert_analytics_signals(round_id):
    """Insert analytics signal record"""
    print_header("STEP 6: Insert Analytics Round Signals")

    if not round_id:
        print_error("No round_id provided, skipping")
        return False

    try:
        signal_id = log_round_signal(
            round_id=round_id,
            round_number=1,
            bot_id="test_bot_001",
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
            }
        )

        if signal_id:
            print_success(f"Analytics signal inserted (ID: {signal_id})")
            return True
        else:
            print_error("Failed to insert analytics signal")
            return False
    except Exception as e:
        print_error(f"Failed to insert analytics signal: {e}")
        return False

def insert_analytics_outcomes(round_id):
    """Insert analytics outcome record"""
    print_header("STEP 7: Insert Analytics Round Outcomes")

    if not round_id:
        print_error("No round_id provided, skipping")
        return False

    try:
        outcome_id = log_round_outcome(
            round_id=round_id,
            round_number=1,
            bot_id="test_bot_001",
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
            actual_multiplier=Decimal("2.45"),
            hit_target=True,
            win_streak=1,
            loss_streak=0,
            outcome_category="small_win",
            duration_seconds=4.2,
        )

        if outcome_id:
            print_success(f"Analytics outcome inserted (ID: {outcome_id})")
            return True
        else:
            print_error("Failed to insert analytics outcome")
            return False
    except Exception as e:
        print_error(f"Failed to insert analytics outcome: {e}")
        return False

def insert_session_log():
    """Insert session log record"""
    print_header("STEP 8: Insert Session Log")

    try:
        session_id = create_session_log(
            bot_id="test_bot_001",
            session_id="test_session_001",
            game_name="aviator",
            initial_balance=Decimal("1000.00"),
        )

        if session_id:
            print_success(f"Session log created (ID: {session_id})")

            # Update session
            update_session_log(
                session_id="test_session_001",
                final_balance=Decimal("1003.30"),
                status="completed",
                notes="Test session completed successfully",
            )
            print_success("Session log updated")
            return True
        else:
            print_error("Failed to create session log")
            return False
    except Exception as e:
        print_error(f"Failed with session log: {e}")
        return False

def insert_error_log(round_id):
    """Insert error log record"""
    print_header("STEP 9: Insert Error Log")

    try:
        error_id = log_error(
            bot_id="test_bot_001",
            session_id="test_session_001",
            round_id=round_id,
            error_type="ocr_error",
            error_message="Failed to read multiplier from screen",
            error_trace="Traceback: test error trace",
            recovery_action="Retried OCR with enhanced preprocessing",
        )

        if error_id:
            print_success(f"Error log inserted (ID: {error_id})")
            return True
        else:
            print_error("Failed to insert error log")
            return False
    except Exception as e:
        print_error(f"Failed to insert error log: {e}")
        return False

def insert_ocr_validation_log(round_id):
    """Insert OCR validation log record"""
    print_header("STEP 10: Insert OCR Validation Log")

    try:
        ocr_id = log_ocr_validation(
            bot_id="test_bot_001",
            raw_ocr_text="1.33x",
            round_id=round_id,
            cleaned_value=Decimal("1.33"),
            confidence=0.95,
            validation_status="VALID",
        )

        if ocr_id:
            print_success(f"OCR validation log inserted (ID: {ocr_id})")
            return True
        else:
            print_error("Failed to insert OCR validation log")
            return False
    except Exception as e:
        print_error(f"Failed to insert OCR validation log: {e}")
        return False

def verify_all_tables():
    """Verify all tables have data"""
    print_header("STEP 11: Verify All Tables Have Data")

    try:
        with session_scope() as session:
            inspector = inspect(session.get_bind())
            tables = sorted(inspector.get_table_names())

            print("\nTABLE SUMMARY:\n")

            all_have_data = True
            for table_name in tables:
                result = session.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
                row_count = result.scalar()

                if row_count > 0:
                    print(f"  [OK] {table_name:35} | {row_count:5} row(s)")
                else:
                    print(f"  [WARN] {table_name:35} | {row_count:5} row(s) - EMPTY")
                    all_have_data = False

            return all_have_data
    except Exception as e:
        print_error(f"Failed to verify tables: {e}")
        return False

def display_detailed_table_info():
    """Display detailed information about all tables"""
    print_header("STEP 12: Detailed Table Information")

    try:
        with session_scope() as session:
            inspector = inspect(session.get_bind())
            tables = sorted(inspector.get_table_names())

            for table_name in tables:
                columns = inspector.get_columns(table_name)
                result = session.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
                row_count = result.scalar()

                print(f"\nTABLE: {table_name.upper()}")
                print(f"  Rows: {row_count} | Columns: {len(columns)}")
                print(f"  " + "-"*70)

                for col in columns:
                    nullable = "NULLABLE" if col['nullable'] else "NOT NULL"
                    col_type = str(col['type'])
                    print(f"  - {col['name']:32} {col_type:20} {nullable}")

        return True
    except Exception as e:
        print_error(f"Failed to display table info: {e}")
        return False

def main():
    """Main test function"""
    print("\n" + "="*80)
    print("  DATABASE INSERTION TEST - CREATE SAMPLE RECORDS FOR ALL TABLES".center(80))
    print("="*80)

    # Step 1: Test connection
    if not test_database_connection():
        return False

    # Step 2: Insert bot registration
    if not insert_bot_registration():
        return False

    # Step 3: Insert game platform config
    if not insert_game_platform_config():
        return False

    # Step 4: Insert crash game round
    round_id = insert_crash_game_round()
    if not round_id:
        return False

    # Step 5-7: Insert analytics records
    if not insert_analytics_multipliers(round_id):
        return False

    if not insert_analytics_signals(round_id):
        return False

    if not insert_analytics_outcomes(round_id):
        return False

    # Step 8: Insert session log
    if not insert_session_log():
        return False

    # Step 9: Insert error log
    if not insert_error_log(round_id):
        return False

    # Step 10: Insert OCR validation log
    if not insert_ocr_validation_log(round_id):
        return False

    # Step 11: Verify all tables
    all_have_data = verify_all_tables()

    # Step 12: Display detailed info
    if not display_detailed_table_info():
        return False

    # Final status
    print_header("FINAL RESULT")

    if all_have_data:
        print_success("ALL TABLES HAVE DATA - DATABASE IS WORKING!")
        print("\n[OK] Database insertion test completed successfully")
        print("[OK] All 9 tables verified with sample data")
        print("[OK] Ready for production use")
        return True
    else:
        print("[WARN] Some tables are empty - please review above")
        return False

if __name__ == "__main__":
    try:
        success = main()
        exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n[ERROR] Test interrupted by user")
        exit(1)
    except Exception as e:
        print(f"\n[ERROR] Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
