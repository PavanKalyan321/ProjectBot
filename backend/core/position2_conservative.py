"""Position 2: Timer-based Conservative Betting Strategy."""

import random
import time
from typing import Dict, List, Tuple


class Position2ConservativeEngine:
    """
    Position 2 Engine: Timer-based betting with green/red filtering.

    Strategy:
    - Bet every N rounds (random 5-10 interval)
    - Only bet when greens > 60% in last 2-20 rounds
    - Skip when reds > 30% in last 2-20 rounds
    - Cashout at random 1.2x-1.4x
    """

    def __init__(self, config_manager):
        """Initialize Position 2 engine with configuration."""
        self.config = config_manager
        self.rounds_since_last_bet = 0
        self.next_bet_interval = self._generate_random_interval()
        print(f"⏲️  Position 2 Timer: Next bet in {self.next_bet_interval} rounds")

    def _generate_random_interval(self) -> int:
        """Generate random interval between timer_min and timer_max."""
        return random.randint(
            self.config.position2_timer_min,
            self.config.position2_timer_max
        )

    def should_bet_this_round(self, recent_multipliers: List[float]) -> Tuple[bool, str, float]:
        """
        Determine if Position 2 should bet this round.

        Args:
            recent_multipliers: List of recent multiplier values (most recent last)

        Returns:
            Tuple[bool, str, float]: (should_bet, reason, target_multiplier)
        """
        self.rounds_since_last_bet += 1

        # Check timer condition
        if self.rounds_since_last_bet < self.next_bet_interval:
            remaining = self.next_bet_interval - self.rounds_since_last_bet
            return False, f"TIMER_WAIT ({self.rounds_since_last_bet}/{self.next_bet_interval}, {remaining} rounds left)", 0

        # Timer elapsed, check filters
        lookback = random.randint(
            self.config.position2_lookback_min,
            self.config.position2_lookback_max
        )

        recent_subset = recent_multipliers[-lookback:] if len(recent_multipliers) >= lookback else recent_multipliers

        if len(recent_subset) < 2:
            return False, "INSUFFICIENT_HISTORY", 0

        # Calculate green and red percentages
        # Green = multiplier >= 2.0 (profitable)
        # Red = multiplier < 2.0 (loss)
        green_count = sum(1 for m in recent_subset if m >= 2.0)
        red_count = sum(1 for m in recent_subset if m < 2.0)
        total = len(recent_subset)

        green_percent = (green_count / total) * 100
        red_percent = (red_count / total) * 100

        # Apply filters
        if red_percent > self.config.position2_max_red_percent:
            return False, f"HIGH_RED_RATE ({red_percent:.1f}% > {self.config.position2_max_red_percent}%)", 0

        if green_percent < self.config.position2_min_green_percent:
            return False, f"LOW_GREEN_RATE ({green_percent:.1f}% < {self.config.position2_min_green_percent}%)", 0

        # All conditions met - bet!
        target = random.uniform(
            self.config.position2_target_multiplier_min,
            self.config.position2_target_multiplier_max
        )

        # Reset timer for next bet
        self.rounds_since_last_bet = 0
        self.next_bet_interval = self._generate_random_interval()

        reason = f"APPROVED (Lookback: {lookback}R, Green: {green_percent:.1f}%, Red: {red_percent:.1f}%, Next bet in {self.next_bet_interval}R)"
        return True, reason, round(target, 2)

    def reset_timer(self):
        """Reset timer (call if bet was skipped due to external reasons)."""
        self.rounds_since_last_bet = 0
        self.next_bet_interval = self._generate_random_interval()
        print(f"⏲️  Position 2 Timer reset. Next bet in {self.next_bet_interval} rounds")

    def get_timer_status(self) -> str:
        """Get current timer status for logging."""
        remaining = max(0, self.next_bet_interval - self.rounds_since_last_bet)
        return f"Timer: {self.rounds_since_last_bet}/{self.next_bet_interval} (Next bet in {remaining}R)"
