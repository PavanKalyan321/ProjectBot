"""
Structured Bet Logging System
Separate from history tracking - focuses on betting decisions and outcomes
"""

import os
import csv
import threading
from datetime import datetime
from queue import Queue


class BetLogger:
    """
    Structured logger for betting decisions and outcomes.
    Uses async writing for performance.
    """

    def __init__(self, log_file='logs/bet_log.csv'):
        """
        Initialize bet logger.

        Args:
            log_file: Path to bet log CSV file
        """
        self.log_file = log_file
        os.makedirs(os.path.dirname(log_file), exist_ok=True)

        # Async write queue
        self._write_queue = Queue()
        self._write_thread = None
        self._running = False

        # Create CSV with headers if not exists
        if not os.path.exists(log_file):
            self._create_log_file()

        # Start async writer
        self._start_async_writer()

    def _create_log_file(self):
        """Create bet log CSV file with headers."""
        headers = [
            # Timestamp
            'timestamp',

            # Round info
            'round_number',
            'multiplier',

            # Betting decision
            'decision',  # BET, SKIP, CANCEL
            'stake',
            'cashout_target_time',
            'cashout_target_mult',

            # ML signals
            'ml_confidence',
            'ml_prediction',
            'ml_expected_value',
            'ml_agreement',

            # Position 2 signals
            'pos2_confidence',
            'pos2_target_mult',
            'pos2_burst_prob',
            'pos2_phase',
            'pos2_rules',

            # Outcome
            'outcome',  # WIN, LOSS, CANCELLED, SKIPPED
            'actual_cashout_time',
            'actual_mult_at_cashout',
            'profit_loss',

            # Balance tracking
            'balance_before',
            'balance_after',
            'cumulative_profit',

            # Statistics
            'win_streak',
            'total_bets',
            'win_rate',

            # Notes
            'notes'
        ]

        with open(self.log_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(headers)

    def _start_async_writer(self):
        """Start background thread for async writing."""
        if not self._running:
            self._running = True
            self._write_thread = threading.Thread(target=self._write_worker, daemon=True)
            self._write_thread.start()

    def _write_worker(self):
        """Background worker that writes rows asynchronously."""
        while self._running:
            try:
                # Get row from queue (with timeout)
                row = self._write_queue.get(timeout=1.0)

                if row is None:  # Shutdown signal
                    break

                # Write to CSV
                with open(self.log_file, 'a', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow(row)

                self._write_queue.task_done()

            except Exception as e:
                if str(e):  # Ignore timeout exceptions
                    pass

    def log_bet(self, round_num, multiplier, stake, ml_signal, pos2_signal,
                cashout_target_time, outcome, profit_loss, balance_before,
                balance_after, cumulative_profit, stats, notes=''):
        """
        Log a betting round.

        Args:
            round_num: Round number
            multiplier: Actual multiplier
            stake: Stake amount
            ml_signal: ML signal dict
            pos2_signal: Position 2 signal dict
            cashout_target_time: Target cashout time (seconds)
            outcome: WIN, LOSS, CANCELLED
            profit_loss: Profit or loss amount
            balance_before: Balance before bet
            balance_after: Balance after bet
            cumulative_profit: Total cumulative profit
            stats: Bot statistics dict
            notes: Additional notes
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]

        # Extract ML data
        ml_conf = ml_signal.get('confidence', 0) if ml_signal else 0
        ml_pred = ml_signal.get('prediction', 0) if ml_signal else 0
        ml_ev = ml_signal.get('expected_value', 0) if ml_signal else 0
        ml_agree = ml_signal.get('agreement', 0) if ml_signal else 0

        # Extract Position 2 data
        pos2_conf = pos2_signal.get('confidence', 0) if pos2_signal else 0
        pos2_target = pos2_signal.get('target_multiplier', 0) if pos2_signal else 0
        pos2_burst = pos2_signal.get('burst_probability', 0) if pos2_signal else 0
        pos2_phase = pos2_signal.get('phase', 'unknown') if pos2_signal else 'unknown'
        pos2_rules = '|'.join(pos2_signal.get('rules_triggered', [])) if pos2_signal else ''

        # Calculate metrics
        win_streak = stats.get('current_streak', 0)
        total_bets = stats.get('ml_bets_placed', 0)
        successful = stats.get('successful_cashouts', 0)
        win_rate = (successful / total_bets * 100) if total_bets > 0 else 0

        # Determine decision
        decision = 'BET' if stake > 0 else 'SKIP'

        # Estimated target multiplier
        from utils.betting_helpers import estimate_multiplier
        target_mult = estimate_multiplier(cashout_target_time) if cashout_target_time > 0 else 0

        # Actual cashout details
        actual_cashout_time = cashout_target_time if outcome == 'WIN' else 0
        actual_mult = multiplier if outcome in ['WIN', 'LOSS'] else 0

        row = [
            timestamp,
            round_num,
            multiplier,
            decision,
            stake,
            cashout_target_time,
            target_mult,
            ml_conf,
            ml_pred,
            ml_ev,
            ml_agree,
            pos2_conf,
            pos2_target,
            pos2_burst,
            pos2_phase,
            pos2_rules,
            outcome,
            actual_cashout_time,
            actual_mult,
            profit_loss,
            balance_before if balance_before else 0,
            balance_after if balance_after else 0,
            cumulative_profit,
            win_streak,
            total_bets,
            f"{win_rate:.1f}",
            notes
        ]

        # Queue for async write
        self._write_queue.put(row)

    def log_skip(self, round_num, multiplier, ml_signal, pos2_signal, reason=''):
        """
        Log a skipped round.

        Args:
            round_num: Round number
            multiplier: Observed multiplier
            ml_signal: ML signal dict
            pos2_signal: Position 2 signal dict
            reason: Reason for skipping
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]

        # Extract ML data
        ml_conf = ml_signal.get('confidence', 0) if ml_signal else 0
        ml_pred = ml_signal.get('prediction', 0) if ml_signal else 0
        ml_ev = ml_signal.get('expected_value', 0) if ml_signal else 0
        ml_agree = ml_signal.get('agreement', 0) if ml_signal else 0

        # Extract Position 2 data
        pos2_conf = pos2_signal.get('confidence', 0) if pos2_signal else 0
        pos2_target = pos2_signal.get('target_multiplier', 0) if pos2_signal else 0
        pos2_burst = pos2_signal.get('burst_probability', 0) if pos2_signal else 0
        pos2_phase = pos2_signal.get('phase', 'unknown') if pos2_signal else 'unknown'
        pos2_rules = '|'.join(pos2_signal.get('rules_triggered', [])) if pos2_signal else ''

        row = [
            timestamp,
            round_num,
            multiplier,
            'SKIP',
            0,  # stake
            0,  # cashout_target_time
            0,  # cashout_target_mult
            ml_conf,
            ml_pred,
            ml_ev,
            ml_agree,
            pos2_conf,
            pos2_target,
            pos2_burst,
            pos2_phase,
            pos2_rules,
            'SKIPPED',
            0,  # actual_cashout_time
            0,  # actual_mult
            0,  # profit_loss
            0,  # balance_before
            0,  # balance_after
            0,  # cumulative_profit
            0,  # win_streak
            0,  # total_bets
            0,  # win_rate
            reason or ml_signal.get('reason', 'Low confidence') if ml_signal else 'Unknown'
        ]

        # Queue for async write
        self._write_queue.put(row)

    def stop(self):
        """Stop async writer thread."""
        if self._running:
            self._running = False
            self._write_queue.put(None)  # Shutdown signal
            if self._write_thread:
                self._write_thread.join(timeout=2.0)


# Global instance
_bet_logger = None


def get_bet_logger():
    """Get or create global bet logger instance."""
    global _bet_logger
    if _bet_logger is None:
        _bet_logger = BetLogger()
    return _bet_logger
