"""
Logging utilities for Aviator Bot.
Centralized logging functions to keep main logic clean.
"""

import time
from datetime import datetime


class BotLogger:
    """Centralized logging for bot operations."""

    @staticmethod
    def log_round_start(round_num):
        """Log the start of a new round."""
        print(f"\n{'='*60}")
        print(f"🎯 ROUND {round_num}")
        print(f"{'='*60}")

    @staticmethod
    def log_awaiting_wait():
        """Log waiting for AWAITING state."""
        print("  🔍 Waiting for AWAITING state...")

    @staticmethod
    def log_awaiting_confirmed():
        """Log AWAITING state confirmed."""
        print("  ✅ AWAITING confirmed")

    @staticmethod
    def log_timeout():
        """Log timeout waiting for state."""
        print("  ⚠️ Timeout")

    @staticmethod
    def log_logging_round():
        """Log logging previous round."""
        print("  📝 Logging previous round...")

    @staticmethod
    def log_round_logged(multiplier):
        """Log successful round logging."""
        print(f"  ✅ Logged: {multiplier}x")

    @staticmethod
    def log_cant_read_multiplier():
        """Log failure to read multiplier."""
        print(f"  ⚠️ Couldn't read multiplier")

    @staticmethod
    def log_analyzing():
        """Log ML analysis start."""
        print("  🤖 Analyzing...")

    @staticmethod
    def log_ml_signal(prediction, confidence):
        """Log ML signal results."""
        print(f"  📊 Pred: {prediction}x | Conf: {confidence}%")

    @staticmethod
    def log_should_bet(stake):
        """Log bet placement."""
        print(f"  💰 Setting stake: {stake}")

    @staticmethod
    def log_stake_failed():
        """Log stake setting failure."""
        print("  ⚠️ Stake failed")

    @staticmethod
    def log_placing_bet():
        """Log bet placement start."""
        print(f"  💵 Placing bet...")

    @staticmethod
    def log_bet_failed(reason):
        """Log bet placement failure."""
        print(f"  ❌ Bet failed: {reason}")

    @staticmethod
    def log_bet_confirmed():
        """Log bet confirmation."""
        print(f"  ✅ Bet confirmed")

    @staticmethod
    def log_waiting_game_start():
        """Log waiting for game start."""
        print("  ⏳ Waiting for game start...")

    @staticmethod
    def log_initial_state(state):
        """Log initial game state."""
        print(f"  🔍 Initial state: {state}")

    @staticmethod
    def log_still_waiting(state, mult):
        """Log still waiting with current state."""
        print(f"  🔍 Still waiting... State: {state}, Mult: {mult}")

    @staticmethod
    def log_game_started(state, mult):
        """Log game start confirmation."""
        print(f"  🚀 Game started! State: {state}, Mult: {mult}")

    @staticmethod
    def log_game_didnt_start():
        """Log game start failure."""
        print("  ⚠️ Game didn't start")

    @staticmethod
    def log_countdown(delay):
        """Log countdown start."""
        print(f"  ⏱️  Countdown: {delay}s")

    @staticmethod
    def log_crashed(elapsed, remaining):
        """Log game crash."""
        print(f"\n  💥 CRASHED at {elapsed:.3f}s ({elapsed*1000:.0f}ms)!")
        print(f"  ⏰ Time remaining: {remaining:.0f}ms")

    @staticmethod
    def log_crash_state(state):
        """Log crash state details."""
        print(f"  🔍 Game state: {state}")

    @staticmethod
    def log_cashout_trigger(actual_elapsed, target, remaining):
        """Log cashout trigger."""
        print(f"\n  💰 Cashing out at {actual_elapsed:.3f}s ({actual_elapsed*1000:.0f}ms)...")
        print(f"  ⏰ Target: {target}s, Remaining: {remaining:.0f}ms")

    @staticmethod
    def log_cashout_duration(duration):
        """Log cashout execution time."""
        print(f"  ⏱️  Cashout execution took: {duration:.0f}ms")

    @staticmethod
    def log_win(multiplier, profit, total_profit):
        """Log successful cashout."""
        print(f"  ✅ WIN at {multiplier:.2f}x")
        print(f"  💰 Profit: +{profit:.2f}")
        print(f"  📊 Total P/L: {total_profit:+.2f}")

    @staticmethod
    def log_loss(stake, total_profit):
        """Log loss."""
        print(f"  💸 Loss: -{stake:.2f}")
        print(f"  📊 Total P/L: {total_profit:+.2f}")

    @staticmethod
    def log_cashout_failed(reason):
        """Log cashout failure."""
        print(f"  ❌ Cashout failed: {reason}")
        print(f"  ⚠️  This might indicate the game crashed during cashout")

    @staticmethod
    def log_skip(reason):
        """Log round skip."""
        print(f"  ⏭️  SKIP: {reason}")

    @staticmethod
    def log_stake_increase(old_stake, new_stake):
        """Log stake increase."""
        print(f"  📈 Stake: {old_stake} → {new_stake}")

    @staticmethod
    def log_stake_reset(stake):
        """Log stake reset."""
        print(f"  📉 Stake reset to: {stake}")

    @staticmethod
    def log_progress_bar(elapsed, delay, remaining, remaining_ms):
        """Log progress bar."""
        progress = int((elapsed / delay) * 20)
        bar = '█' * progress + '░' * (20 - progress)
        print(f"  ⏱️  [{bar}] {remaining:.3f}s ({remaining_ms:.0f}ms)", end='\r')

    @staticmethod
    def log_final_stats(stats):
        """Log final statistics."""
        print("\n" + "="*60)
        print("📊 FINAL STATISTICS")
        print("="*60)
        print(f"Rounds observed:      {stats['rounds_observed']}")
        print(f"ML bets placed:       {stats['ml_bets_placed']}")
        print(f"Successful cashouts:  {stats['successful_cashouts']}")
        print(f"Failed cashouts:      {stats['failed_cashouts']}")

        if stats['ml_bets_placed'] > 0:
            success_rate = (stats['successful_cashouts'] / stats['ml_bets_placed']) * 100
            print(f"Success rate:         {success_rate:.1f}%")

        print(f"\n💰 Financial:")
        print(f"  Total bet:          {stats['total_bet']:.2f}")
        print(f"  Total return:       {stats['total_return']:.2f}")
        profit = stats['total_return'] - stats['total_bet']
        print(f"  Profit/Loss:        {profit:+.2f}")

        if stats['total_bet'] > 0:
            roi = (profit / stats['total_bet']) * 100
            print(f"  ROI:                {roi:+.1f}%")

        print("="*60 + "\n")

    @staticmethod
    def log_stopped():
        """Log bot stop."""
        print("\n\n⏹️  Stopped")
