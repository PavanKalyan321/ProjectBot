"""
Utility functions for database operations and analytics
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy import func, desc, and_

from .connection import session_scope
from .models import (
    CrashGameRound,
    AnalyticsRoundMultiplier,
    AnalyticsRoundSignal,
    AnalyticsRoundOutcome,
    SessionLog,
)

logger = logging.getLogger(__name__)

# ============================================================================
# ANALYTICS FUNCTIONS
# ============================================================================

def get_bot_statistics(
    bot_id: str,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
) -> Dict[str, Any]:
    """
    Get comprehensive statistics for a bot.

    Args:
        bot_id: Bot identifier
        start_date: Filter start date
        end_date: Filter end date

    Returns:
        dict: Statistics dictionary
    """
    with session_scope() as session:
        query = session.query(CrashGameRound).filter_by(bot_id=bot_id)

        if start_date:
            query = query.filter(CrashGameRound.round_start_timestamp >= start_date)
        if end_date:
            query = query.filter(CrashGameRound.round_start_timestamp <= end_date)

        rounds = query.all()

        if not rounds:
            return {"error": "No rounds found"}

        # Calculate statistics
        total_rounds = len(rounds)
        wins = sum(1 for r in rounds if r.round_outcome == "WIN")
        losses = sum(1 for r in rounds if r.round_outcome == "LOSS")
        errors = sum(1 for r in rounds if r.round_outcome == "ERROR")

        total_stakes = sum(r.stake_value for r in rounds if r.stake_value)
        total_profit = sum(r.profit_loss_amount for r in rounds if r.profit_loss_amount)

        win_rate = (wins / total_rounds * 100) if total_rounds > 0 else 0
        roi = (total_profit / total_stakes * 100) if total_stakes > 0 else 0

        # Multiplier statistics
        multipliers = [r.final_multiplier for r in rounds if r.final_multiplier]
        avg_multiplier = sum(multipliers) / len(multipliers) if multipliers else 0
        max_multiplier = max(multipliers) if multipliers else 0
        min_multiplier = min(multipliers) if multipliers else 0

        return {
            "bot_id": bot_id,
            "total_rounds": total_rounds,
            "wins": wins,
            "losses": losses,
            "errors": errors,
            "win_rate_percent": round(win_rate, 2),
            "total_stakes": float(total_stakes),
            "total_profit": float(total_profit),
            "roi_percent": round(roi, 2),
            "avg_multiplier": round(float(avg_multiplier), 2),
            "max_multiplier": float(max_multiplier),
            "min_multiplier": float(min_multiplier),
            "largest_win": float(max((r.profit_loss_amount for r in rounds if r.profit_loss_amount and r.profit_loss_amount > 0), default=0)),
            "largest_loss": float(min((r.profit_loss_amount for r in rounds if r.profit_loss_amount and r.profit_loss_amount < 0), default=0)),
        }

def get_session_summary(session_id: str) -> Dict[str, Any]:
    """
    Get summary of a complete session.

    Args:
        session_id: Session identifier

    Returns:
        dict: Session summary
    """
    with session_scope() as session:
        session_log = session.query(SessionLog).filter_by(session_id=session_id).first()

        if not session_log:
            return {"error": "Session not found"}

        duration = None
        if session_log.start_time and session_log.end_time:
            duration = (session_log.end_time - session_log.start_time).total_seconds()

        return {
            "session_id": session_id,
            "bot_id": session_log.bot_id,
            "game_name": session_log.game_name,
            "status": session_log.status,
            "start_time": session_log.start_time.isoformat() if session_log.start_time else None,
            "end_time": session_log.end_time.isoformat() if session_log.end_time else None,
            "duration_seconds": duration,
            "initial_balance": float(session_log.initial_balance) if session_log.initial_balance else None,
            "final_balance": float(session_log.final_balance) if session_log.final_balance else None,
            "total_profit_loss": float(session_log.total_profit_loss) if session_log.total_profit_loss else None,
            "roi_percent": float(session_log.total_roi_percent) if session_log.total_roi_percent else None,
            "total_rounds": session_log.total_rounds,
            "win_rate": float(session_log.win_rate) if session_log.win_rate else None,
        }

def get_game_statistics(
    game_name: str,
    platform_code: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
) -> Dict[str, Any]:
    """
    Get statistics for a specific game across all bots.

    Args:
        game_name: Game type (aviator, aviatrix, jetx)
        platform_code: Optional platform filter
        start_date: Start date filter
        end_date: End date filter

    Returns:
        dict: Game statistics
    """
    with session_scope() as session:
        query = session.query(CrashGameRound).filter_by(game_name=game_name)

        if platform_code:
            query = query.filter_by(platform_code=platform_code)
        if start_date:
            query = query.filter(CrashGameRound.round_start_timestamp >= start_date)
        if end_date:
            query = query.filter(CrashGameRound.round_start_timestamp <= end_date)

        rounds = query.all()

        if not rounds:
            return {"error": "No rounds found"}

        # Group by bot
        bots_data = {}
        for r in rounds:
            if r.bot_id not in bots_data:
                bots_data[r.bot_id] = []
            bots_data[r.bot_id].append(r)

        # Calculate aggregate stats
        total_rounds = len(rounds)
        total_profit = sum(r.profit_loss_amount for r in rounds if r.profit_loss_amount)
        wins = sum(1 for r in rounds if r.round_outcome == "WIN")

        return {
            "game_name": game_name,
            "total_bots": len(bots_data),
            "total_rounds": total_rounds,
            "wins": wins,
            "win_rate_percent": round(wins / total_rounds * 100, 2) if total_rounds > 0 else 0,
            "total_profit": float(total_profit),
            "bots": {bot_id: len(rounds) for bot_id, rounds in bots_data.items()},
        }

def get_strategy_performance(strategy_name: str) -> Dict[str, Any]:
    """
    Get performance metrics for a specific strategy.

    Args:
        strategy_name: Strategy name

    Returns:
        dict: Strategy performance data
    """
    with session_scope() as session:
        rounds = session.query(CrashGameRound).filter_by(
            strategy_name=strategy_name
        ).all()

        if not rounds:
            return {"error": "No rounds found for this strategy"}

        wins = sum(1 for r in rounds if r.round_outcome == "WIN")
        losses = sum(1 for r in rounds if r.round_outcome == "LOSS")
        total_profit = sum(r.profit_loss_amount for r in rounds if r.profit_loss_amount)
        total_stakes = sum(r.stake_value for r in rounds if r.stake_value)

        return {
            "strategy": strategy_name,
            "total_rounds": len(rounds),
            "wins": wins,
            "losses": losses,
            "win_rate_percent": round(wins / len(rounds) * 100, 2) if rounds else 0,
            "total_profit": float(total_profit),
            "avg_profit_per_round": float(total_profit / len(rounds)) if rounds else 0,
            "roi_percent": round(total_profit / total_stakes * 100, 2) if total_stakes > 0 else 0,
        }

# ============================================================================
# MULTIPLIER ANALYSIS
# ============================================================================

def get_multiplier_distribution(
    game_name: str,
    limit: int = 1000,
) -> Dict[str, Any]:
    """
    Get distribution of multipliers for a game.

    Args:
        game_name: Game type
        limit: Maximum records to analyze

    Returns:
        dict: Distribution analysis
    """
    with session_scope() as session:
        multipliers = session.query(AnalyticsRoundMultiplier).filter_by(
            game_name=game_name
        ).order_by(desc(AnalyticsRoundMultiplier.timestamp)).limit(limit).all()

        if not multipliers:
            return {"error": "No multiplier data found"}

        values = [float(m.multiplier) for m in multipliers]
        crashes = sum(1 for m in multipliers if m.is_crash_multiplier)
        cashouts = sum(1 for m in multipliers if m.is_cashout_multiplier)

        # Calculate percentiles
        sorted_vals = sorted(values)
        total = len(sorted_vals)
        p10 = sorted_vals[int(total * 0.1)] if total > 0 else 0
        p50 = sorted_vals[int(total * 0.5)] if total > 0 else 0
        p90 = sorted_vals[int(total * 0.9)] if total > 0 else 0

        return {
            "game_name": game_name,
            "total_records": len(multipliers),
            "avg_multiplier": round(sum(values) / len(values), 2),
            "min_multiplier": min(values),
            "max_multiplier": max(values),
            "percentile_10": p10,
            "percentile_50": p50,
            "percentile_90": p90,
            "crashes": crashes,
            "cashouts": cashouts,
        }

def get_signal_effectiveness(
    bot_id: Optional[str] = None,
    signal_type: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Analyze effectiveness of signals.

    Args:
        bot_id: Filter by bot ID
        signal_type: Filter by signal type

    Returns:
        dict: Signal effectiveness metrics
    """
    with session_scope() as session:
        query = session.query(AnalyticsRoundSignal)

        if bot_id:
            query = query.filter_by(bot_id=bot_id)
        if signal_type:
            query = query.filter_by(signal_type=signal_type)

        signals = query.all()

        if not signals:
            return {"error": "No signal data found"}

        # Filter signals with correctness data
        evaluated = [s for s in signals if s.signal_correctness is not None]

        if not evaluated:
            return {"error": "No evaluated signals found"}

        correct = sum(1 for s in evaluated if s.signal_correctness)
        accuracy = (correct / len(evaluated) * 100) if evaluated else 0
        avg_confidence = sum(s.confidence_score for s in signals if s.confidence_score) / len(signals) if signals else 0

        return {
            "total_signals": len(signals),
            "evaluated_signals": len(evaluated),
            "correct_predictions": correct,
            "accuracy_percent": round(accuracy, 2),
            "avg_confidence": round(float(avg_confidence), 2),
            "signal_types": list(set(s.signal_type for s in signals if s.signal_type)),
        }

# ============================================================================
# EXPORT FUNCTIONS
# ============================================================================

def export_rounds_to_json(
    bot_id: str,
    limit: int = 100,
) -> List[Dict[str, Any]]:
    """
    Export rounds in JSON-serializable format.

    Args:
        bot_id: Bot identifier
        limit: Maximum rounds to export

    Returns:
        list: List of round dictionaries
    """
    with session_scope() as session:
        rounds = session.query(CrashGameRound).filter_by(
            bot_id=bot_id
        ).order_by(desc(CrashGameRound.round_number)).limit(limit).all()

        export_data = []
        for r in rounds:
            export_data.append({
                "id": r.id,
                "round_number": r.round_number,
                "game_name": r.game_name,
                "stake": float(r.stake_value),
                "crash_multiplier": float(r.crash_multiplier_detected) if r.crash_multiplier_detected else None,
                "cashout_multiplier": float(r.cashout_multiplier) if r.cashout_multiplier else None,
                "outcome": r.round_outcome,
                "profit_loss": float(r.profit_loss_amount) if r.profit_loss_amount else None,
                "roi_percent": float(r.roi_percent) if r.roi_percent else None,
                "timestamp": r.round_start_timestamp.isoformat() if r.round_start_timestamp else None,
            })

        return export_data

def export_multipliers_for_ml(
    game_name: str,
    bot_id: Optional[str] = None,
    limit: int = 10000,
) -> List[Dict[str, Any]]:
    """
    Export multiplier data formatted for ML training.

    Args:
        game_name: Game type
        bot_id: Optional bot filter
        limit: Maximum records

    Returns:
        list: ML-formatted data
    """
    with session_scope() as session:
        query = session.query(AnalyticsRoundMultiplier).filter_by(game_name=game_name)

        if bot_id:
            query = query.filter_by(bot_id=bot_id)

        multipliers = query.limit(limit).all()

        export_data = []
        for m in multipliers:
            export_data.append({
                "round_id": m.round_id,
                "multiplier": float(m.multiplier),
                "timestamp": m.timestamp.isoformat() if m.timestamp else None,
                "is_crash": m.is_crash_multiplier,
                "is_cashout": m.is_cashout_multiplier,
                "ocr_confidence": float(m.ocr_confidence) if m.ocr_confidence else None,
                "quality_score": float(m.data_quality_score) if m.data_quality_score else None,
            })

        return export_data

# ============================================================================
# CLEANUP & MAINTENANCE
# ============================================================================

def cleanup_old_records(
    days_old: int = 90,
    dry_run: bool = True,
) -> Dict[str, int]:
    """
    Clean up old records (for maintenance).

    Args:
        days_old: Delete records older than this many days
        dry_run: If True, only count records (don't delete)

    Returns:
        dict: Count of records affected
    """
    cutoff_date = datetime.utcnow() - timedelta(days=days_old)

    with session_scope() as session:
        # Count records to delete
        count = session.query(CrashGameRound).filter(
            CrashGameRound.created_at < cutoff_date
        ).count()

        if not dry_run:
            # Delete records
            session.query(CrashGameRound).filter(
                CrashGameRound.created_at < cutoff_date
            ).delete()
            logger.warning(f"Deleted {count} old records")

        return {
            "records_affected": count,
            "cutoff_date": cutoff_date.isoformat(),
            "dry_run": dry_run,
        }

def get_database_size() -> Dict[str, Any]:
    """
    Get current database size statistics.

    Returns:
        dict: Size information
    """
    with session_scope() as session:
        try:
            result = session.execute(
                """
                SELECT
                    COUNT(*) as total_records,
                    table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                GROUP BY table_name
                """
            ).fetchall()

            tables = {}
            for row in result:
                tables[row[1]] = row[0]

            total_records = sum(tables.values())

            return {
                "total_records": total_records,
                "tables": tables,
            }
        except Exception as e:
            logger.error(f"Failed to get database size: {str(e)}")
            return {"error": str(e)}
