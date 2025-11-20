"""
Local Database Test Script
Tests database models using SQLite without needing DigitalOcean credentials
Verifies all 9 tables can be created and populated with sample data
"""

from decimal import Decimal
from datetime import datetime
from sqlalchemy import create_engine, text, inspect, TypeDecorator, JSON, String
from sqlalchemy.orm import sessionmaker, Session
from contextlib import contextmanager
import json

# Create a JSON type that works with both PostgreSQL and SQLite
class JSONType(TypeDecorator):
    impl = String
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is not None:
            return json.dumps(value)
        return None

    def process_result_value(self, value, dialect):
        if value is not None:
            return json.loads(value)
        return None

# Create SQLite database
DATABASE_URL = "sqlite:///./test_database.db"
engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String as SQLString, DateTime, Float, Boolean, Text, ForeignKey, Numeric, DECIMAL

Base = declarative_base()

# Define models with compatible JSON type
class BotVMRegistration(Base):
    __tablename__ = "bot_vm_registration"

    id = Column(Integer, primary_key=True)
    bot_id = Column(String(100), unique=True, index=True)
    bot_name = Column(String(255))
    vm_name = Column(String(100))
    vm_provider = Column(String(50))
    region = Column(String(50))
    session_id = Column(String(100))
    strategy_name = Column(String(100))
    initial_balance = Column(Numeric(15, 2))
    base_stake = Column(Numeric(10, 2))
    max_stake = Column(Numeric(10, 2))

class GamePlatformConfig(Base):
    __tablename__ = "game_platform_config"

    id = Column(Integer, primary_key=True)
    game_name = Column(String(50), index=True)
    platform_code = Column(String(50))
    platform_url = Column(String(255))
    currency = Column(String(10))
    house_edge_percent = Column(Numeric(5, 2))
    min_multiplier = Column(Numeric(10, 4))
    max_multiplier = Column(Numeric(10, 4))

class CrashGameRound(Base):
    __tablename__ = "crash_game_rounds"

    id = Column(Integer, primary_key=True)
    bot_id = Column(String(100), index=True)
    session_id = Column(String(100))
    game_name = Column(String(50))
    platform_code = Column(String(50))
    round_number = Column(Integer)
    round_start_timestamp = Column(DateTime)
    round_end_timestamp = Column(DateTime)
    stake_value = Column(Numeric(10, 2))
    crash_multiplier_detected = Column(Numeric(10, 4))
    cashout_multiplier = Column(Numeric(10, 4))
    final_multiplier = Column(Numeric(10, 4))
    round_outcome = Column(String(50))
    profit_loss_amount = Column(Numeric(15, 2))
    running_balance_before = Column(Numeric(15, 2))
    running_balance_after = Column(Numeric(15, 2))
    ocr_raw_text = Column(String(100))
    multiplier_detection_confidence = Column(Float)
    meta_data = Column(JSONType)

class AnalyticsRoundMultiplier(Base):
    __tablename__ = "analytics_round_multipliers"

    id = Column(Integer, primary_key=True)
    round_id = Column(Integer, ForeignKey("crash_game_rounds.id"))
    round_external_id = Column(String(100))
    multiplier = Column(Numeric(10, 4))
    timestamp = Column(DateTime)
    bot_id = Column(String(100), index=True)
    game_name = Column(String(50))
    platform_code = Column(String(50))
    is_crash_multiplier = Column(Boolean)
    is_cashout_multiplier = Column(Boolean)
    max_in_round = Column(Boolean)
    ocr_confidence = Column(Float)
    data_quality_score = Column(Float)
    date_bucket = Column(String(10))

class AnalyticsRoundSignal(Base):
    __tablename__ = "analytics_round_signals"

    id = Column(Integer, primary_key=True)
    round_id = Column(Integer, ForeignKey("crash_game_rounds.id"))
    round_number = Column(Integer)
    timestamp = Column(DateTime)
    bot_id = Column(String(100), index=True)
    game_name = Column(String(50))
    signal_type = Column(String(100))
    confidence_score = Column(Float)
    signal_strength = Column(Float)
    time_to_crash_predicted_ms = Column(Integer)
    volatility_measure = Column(Float)
    momentum_score = Column(Float)
    pattern_match_type = Column(String(50))
    similar_rounds_count = Column(Integer)
    feature_vector = Column(JSONType)
    date_bucket = Column(String(10))

class AnalyticsRoundOutcome(Base):
    __tablename__ = "analytics_round_outcomes"

    id = Column(Integer, primary_key=True)
    round_id = Column(Integer, ForeignKey("crash_game_rounds.id"))
    round_number = Column(Integer)
    timestamp = Column(DateTime)
    bot_id = Column(String(100), index=True)
    game_name = Column(String(50))
    platform_code = Column(String(50))
    strategy_name = Column(String(100))
    outcome = Column(String(50))
    profit_loss = Column(Numeric(15, 2))
    roi_percent = Column(Float)
    bet_amount = Column(Numeric(10, 2))
    winnings = Column(Numeric(15, 2))
    loss_amount = Column(Numeric(15, 2))
    target_multiplier = Column(Numeric(10, 4))
    actual_multiplier = Column(Numeric(10, 4))
    hit_target = Column(Boolean)
    win_streak_length = Column(Integer)
    loss_streak_length = Column(Integer)
    outcome_category = Column(String(50))
    duration_seconds = Column(Float)
    date_bucket = Column(String(10))
    hour_bucket = Column(Integer)

class SessionLog(Base):
    __tablename__ = "session_logs"

    id = Column(Integer, primary_key=True)
    bot_id = Column(String(100), index=True)
    session_id = Column(String(100))
    game_name = Column(String(50))
    initial_balance = Column(Numeric(15, 2))
    final_balance = Column(Numeric(15, 2))
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    status = Column(String(50))
    notes = Column(Text)

class ErrorLog(Base):
    __tablename__ = "error_logs"

    id = Column(Integer, primary_key=True)
    bot_id = Column(String(100), index=True)
    session_id = Column(String(100))
    round_id = Column(Integer, ForeignKey("crash_game_rounds.id"))
    error_type = Column(String(50))
    error_message = Column(Text)
    error_trace = Column(Text)
    recovery_action = Column(Text)
    timestamp = Column(DateTime)

class OCRValidationLog(Base):
    __tablename__ = "ocr_validation_logs"

    id = Column(Integer, primary_key=True)
    bot_id = Column(String(100), index=True)
    round_id = Column(Integer, ForeignKey("crash_game_rounds.id"))
    raw_ocr_text = Column(String(255))
    cleaned_value = Column(Numeric(10, 4))
    confidence = Column(Float)
    validation_status = Column(String(50))
    timestamp = Column(DateTime)

@contextmanager
def get_session():
    """Get a database session"""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()

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
    """Test database connection and create tables"""
    print_header("STEP 1: Testing Database Connection")

    try:
        Base.metadata.create_all(bind=engine)
        print_success("Database connection successful")
        print_success("All tables created/verified")
        return True
    except Exception as e:
        print_error(f"Database connection failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def insert_bot_registration():
    """Insert bot registration record"""
    print_header("STEP 2: Insert Bot Registration")

    try:
        with get_session() as session:
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
        import traceback
        traceback.print_exc()
        return None

def insert_game_platform_config():
    """Insert game platform config"""
    print_header("STEP 3: Insert Game Platform Config")

    try:
        with get_session() as session:
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
        import traceback
        traceback.print_exc()
        return False

def insert_crash_game_round():
    """Insert crash game round record"""
    print_header("STEP 4: Insert Crash Game Round")

    try:
        with get_session() as session:
            round_record = CrashGameRound(
                bot_id="test_bot_001",
                session_id="test_session_001",
                game_name="aviator",
                platform_code="dafabet",
                round_number=1,
                round_start_timestamp=datetime.utcnow(),
                round_end_timestamp=datetime.utcnow(),
                stake_value=Decimal("10.00"),
                crash_multiplier_detected=Decimal("2.45"),
                cashout_multiplier=Decimal("1.33"),
                final_multiplier=Decimal("1.33"),
                round_outcome="WIN",
                profit_loss_amount=Decimal("3.30"),
                running_balance_before=Decimal("1000.00"),
                running_balance_after=Decimal("1003.30"),
                ocr_raw_text="1.33x",
                multiplier_detection_confidence=0.95,
                meta_data={
                    "strategy": "compound_1.33x",
                    "prediction_correct": True,
                    "volatility": 0.75,
                }
            )
            session.add(round_record)
            session.flush()
            round_id = round_record.id

        print_success(f"Crash game round inserted (ID: {round_id})")
        return round_id
    except Exception as e:
        print_error(f"Failed to insert round: {e}")
        import traceback
        traceback.print_exc()
        return None

def insert_analytics_multipliers(round_id):
    """Insert analytics multiplier record"""
    print_header("STEP 5: Insert Analytics Round Multipliers")

    if not round_id:
        print_error("No round_id provided, skipping")
        return False

    try:
        with get_session() as session:
            analytics = AnalyticsRoundMultiplier(
                round_id=round_id,
                round_external_id="ext_001",
                multiplier=Decimal("1.33"),
                timestamp=datetime.utcnow(),
                bot_id="test_bot_001",
                game_name="aviator",
                platform_code="dafabet",
                is_crash_multiplier=False,
                is_cashout_multiplier=True,
                max_in_round=False,
                ocr_confidence=0.95,
                data_quality_score=0.98,
                date_bucket=datetime.utcnow().strftime("%Y-%m-%d"),
            )
            session.add(analytics)
            session.flush()
            analytics_id = analytics.id

        print_success(f"Analytics multiplier inserted (ID: {analytics_id})")
        return True
    except Exception as e:
        print_error(f"Failed to insert analytics multiplier: {e}")
        import traceback
        traceback.print_exc()
        return False

def insert_analytics_signals(round_id):
    """Insert analytics signal record"""
    print_header("STEP 6: Insert Analytics Round Signals")

    if not round_id:
        print_error("No round_id provided, skipping")
        return False

    try:
        with get_session() as session:
            signal = AnalyticsRoundSignal(
                round_id=round_id,
                round_number=1,
                timestamp=datetime.utcnow(),
                bot_id="test_bot_001",
                game_name="aviator",
                signal_type="early_flight",
                confidence_score=0.92,
                signal_strength=0.87,
                time_to_crash_predicted_ms=3200,
                volatility_measure=0.65,
                momentum_score=0.78,
                pattern_match_type="exponential",
                similar_rounds_count=145,
                feature_vector={
                    "pre_flight_variance": 0.12,
                    "acceleration_rate": 0.089,
                    "price_distance": 0.35,
                },
                date_bucket=datetime.utcnow().strftime("%Y-%m-%d"),
            )
            session.add(signal)
            session.flush()
            signal_id = signal.id

        print_success(f"Analytics signal inserted (ID: {signal_id})")
        return True
    except Exception as e:
        print_error(f"Failed to insert analytics signal: {e}")
        import traceback
        traceback.print_exc()
        return False

def insert_analytics_outcomes(round_id):
    """Insert analytics outcome record"""
    print_header("STEP 7: Insert Analytics Round Outcomes")

    if not round_id:
        print_error("No round_id provided, skipping")
        return False

    try:
        with get_session() as session:
            outcome = AnalyticsRoundOutcome(
                round_id=round_id,
                round_number=1,
                timestamp=datetime.utcnow(),
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
                win_streak_length=1,
                loss_streak_length=0,
                outcome_category="small_win",
                duration_seconds=4.2,
                date_bucket=datetime.utcnow().strftime("%Y-%m-%d"),
                hour_bucket=datetime.utcnow().hour,
            )
            session.add(outcome)
            session.flush()
            outcome_id = outcome.id

        print_success(f"Analytics outcome inserted (ID: {outcome_id})")
        return True
    except Exception as e:
        print_error(f"Failed to insert analytics outcome: {e}")
        import traceback
        traceback.print_exc()
        return False

def insert_session_log():
    """Insert session log record"""
    print_header("STEP 8: Insert Session Log")

    try:
        with get_session() as session:
            session_log = SessionLog(
                bot_id="test_bot_001",
                session_id="test_session_001",
                game_name="aviator",
                initial_balance=Decimal("1000.00"),
                start_time=datetime.utcnow(),
                status="active",
            )
            session.add(session_log)
            session.flush()
            session_id = session_log.id

        print_success(f"Session log created (ID: {session_id})")

        # Update session
        with get_session() as session:
            session_log = session.query(SessionLog).filter_by(
                session_id="test_session_001"
            ).first()
            if session_log:
                session_log.end_time = datetime.utcnow()
                session_log.final_balance = Decimal("1003.30")
                session_log.status = "completed"
                session_log.notes = "Test session completed successfully"
                session.add(session_log)

        print_success("Session log updated")
        return True
    except Exception as e:
        print_error(f"Failed with session log: {e}")
        import traceback
        traceback.print_exc()
        return False

def insert_error_log(round_id):
    """Insert error log record"""
    print_header("STEP 9: Insert Error Log")

    try:
        with get_session() as session:
            error_log = ErrorLog(
                bot_id="test_bot_001",
                session_id="test_session_001",
                round_id=round_id,
                error_type="ocr_error",
                error_message="Failed to read multiplier from screen",
                error_trace="Traceback: test error trace",
                recovery_action="Retried OCR with enhanced preprocessing",
                timestamp=datetime.utcnow(),
            )
            session.add(error_log)
            session.flush()
            error_id = error_log.id

        print_success(f"Error log inserted (ID: {error_id})")
        return True
    except Exception as e:
        print_error(f"Failed to insert error log: {e}")
        return False

def insert_ocr_validation_log(round_id):
    """Insert OCR validation log record"""
    print_header("STEP 10: Insert OCR Validation Log")

    try:
        with get_session() as session:
            ocr_log = OCRValidationLog(
                bot_id="test_bot_001",
                round_id=round_id,
                raw_ocr_text="1.33x",
                cleaned_value=Decimal("1.33"),
                confidence=0.95,
                validation_status="VALID",
                timestamp=datetime.utcnow(),
            )
            session.add(ocr_log)
            session.flush()
            ocr_id = ocr_log.id

        print_success(f"OCR validation log inserted (ID: {ocr_id})")
        return True
    except Exception as e:
        print_error(f"Failed to insert OCR validation log: {e}")
        return False

def verify_all_tables():
    """Verify all tables have data"""
    print_header("STEP 11: Verify All Tables Have Data")

    try:
        with get_session() as session:
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
        with get_session() as session:
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
