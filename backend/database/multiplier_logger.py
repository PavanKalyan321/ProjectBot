"""
Multiplier Logger - Real-time multiplier tracking to database
Saves live multiplier values from the dashboard to AnalyticsRoundMultiplier table
"""

import logging
from datetime import datetime
from decimal import Decimal
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any

from backend.database.config import SQLALCHEMY_CONFIG
from backend.database.models import Base, AnalyticsRoundMultiplier, CrashGameRound

logger = logging.getLogger(__name__)


class MultiplierLogger:
    """Logs real-time multiplier values to the database."""

    def __init__(self):
        """Initialize database engine and session."""
        try:
            self.engine = create_engine(
                SQLALCHEMY_CONFIG["url"],
                echo=SQLALCHEMY_CONFIG.get("echo", False),
                pool_size=SQLALCHEMY_CONFIG.get("pool_size", 10),
                max_overflow=SQLALCHEMY_CONFIG.get("max_overflow", 20),
                pool_recycle=SQLALCHEMY_CONFIG.get("pool_recycle", 3600),
                pool_pre_ping=SQLALCHEMY_CONFIG.get("pool_pre_ping", True),
                connect_args=SQLALCHEMY_CONFIG.get("connect_args", {})
            )
            # Test connection
            with self.engine.connect() as conn:
                pass
            logger.info("✅ Database connection established for MultiplierLogger")
        except Exception as e:
            logger.error(f"❌ Failed to connect to database: {e}")
            self.engine = None

    def log_multiplier(
        self,
        bot_id: str,
        round_id: Optional[int] = None,
        multiplier: float = 1.0,
        timestamp: Optional[datetime] = None,
        is_crash: bool = False,
        is_cashout: bool = False,
        ocr_confidence: Optional[float] = None,
        game_name: str = "aviator",
        platform_code: str = "demo"
    ) -> Optional[int]:
        """
        Log a multiplier value to the database.

        Args:
            bot_id: Bot identifier
            round_id: ID of the crash game round (optional if creating new round)
            multiplier: The multiplier value (e.g., 1.23)
            timestamp: When the multiplier was recorded (defaults to now)
            is_crash: Whether this is the crash multiplier
            is_cashout: Whether this is a cashout multiplier
            ocr_confidence: OCR confidence score (0-1)
            game_name: Game type (aviator, aviatrix, jetx)
            platform_code: Platform code (demo, pmbetting, etc.)

        Returns:
            ID of the created AnalyticsRoundMultiplier record, or None if failed
        """
        if not self.engine:
            logger.warning("⚠️ Database engine not initialized, skipping multiplier log")
            return None

        if timestamp is None:
            timestamp = datetime.utcnow()

        try:
            with Session(self.engine) as session:
                # Create the multiplier record
                multiplier_record = AnalyticsRoundMultiplier(
                    round_id=round_id,
                    multiplier=Decimal(str(multiplier)),
                    timestamp=timestamp,
                    bot_id=bot_id,
                    game_name=game_name,
                    platform_code=platform_code,
                    is_crash_multiplier=is_crash,
                    is_cashout_multiplier=is_cashout,
                    ocr_confidence=Decimal(str(ocr_confidence)) if ocr_confidence else None,
                    date_bucket=timestamp.strftime("%Y-%m-%d")
                )

                session.add(multiplier_record)
                session.commit()

                logger.info(
                    f"✅ Multiplier logged: bot_id={bot_id}, "
                    f"multiplier={multiplier}x, round_id={round_id}, "
                    f"timestamp={timestamp.isoformat()}"
                )

                return multiplier_record.id

        except Exception as e:
            logger.error(f"❌ Error logging multiplier: {e}")
            return None

    def create_round(
        self,
        bot_id: str,
        round_number: int,
        stake_value: float,
        strategy_name: str = "custom",
        game_name: str = "aviator",
        platform_code: str = "demo",
        session_id: str = "demo_session"
    ) -> Optional[int]:
        """
        Create a new crash game round record.

        Args:
            bot_id: Bot identifier
            round_number: Round number
            stake_value: Stake amount
            strategy_name: Strategy being used
            game_name: Game type
            platform_code: Platform code
            session_id: Session identifier

        Returns:
            ID of the created round, or None if failed
        """
        if not self.engine:
            logger.warning("⚠️ Database engine not initialized, skipping round creation")
            return None

        try:
            with Session(self.engine) as session:
                round_record = CrashGameRound(
                    bot_id=bot_id,
                    session_id=session_id,
                    game_name=game_name,
                    platform_code=platform_code,
                    round_number=round_number,
                    round_start_timestamp=datetime.utcnow(),
                    stake_value=Decimal(str(stake_value)),
                    strategy_name=strategy_name
                )

                session.add(round_record)
                session.commit()

                logger.info(
                    f"✅ Round created: bot_id={bot_id}, "
                    f"round_number={round_number}, round_id={round_record.id}"
                )

                return round_record.id

        except Exception as e:
            logger.error(f"❌ Error creating round: {e}")
            return None

    def get_latest_round(self, bot_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the latest round for a bot that hasn't ended.

        Args:
            bot_id: Bot identifier

        Returns:
            Round data dict with 'id' and 'number', or None if no active round
        """
        if not self.engine:
            return None

        try:
            with Session(self.engine) as session:
                # Get the most recent round without an end timestamp
                round_record = session.query(CrashGameRound).filter(
                    CrashGameRound.bot_id == bot_id,
                    CrashGameRound.round_end_timestamp.is_(None)
                ).order_by(CrashGameRound.round_number.desc()).first()

                if round_record:
                    return {
                        'id': round_record.id,
                        'number': round_record.round_number
                    }
                return None

        except Exception as e:
            logger.error(f"❌ Error getting latest round: {e}")
            return None
