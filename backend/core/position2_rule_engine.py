"""
Position 2 Rule Engine - Advanced Pattern Analysis for Burst Detection
Based on Pavan Rules and Statistical Observations
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from collections import deque


class Position2RuleEngine:
    """
    Advanced rule engine for Position 2 betting based on Pavan Rules.
    Detects burst cycles, high multiplier opportunities, and volatility phases.
    """

    def __init__(self, history_tracker):
        """
        Initialize Position 2 Rule Engine.

        Args:
            history_tracker: RoundHistoryTracker instance
        """
        self.history_tracker = history_tracker

        # Rule thresholds
        self.LOW_MULTIPLIER_THRESHOLD = 2.0
        self.HIGH_MULTIPLIER_THRESHOLD = 10.0
        self.VERY_HIGH_MULTIPLIER_THRESHOLD = 20.0
        self.RED_THRESHOLD = 1.5

        # Tracking state
        self.last_high_round_index = None
        self.last_20x_timestamp = None
        self.high_multiplier_positions = deque(maxlen=50)  # Track positions of high multipliers

    def analyze_position2_signal(self):
        """
        Main analysis function for Position 2 betting.

        Returns:
            dict: Signal with keys:
                - should_bet: bool
                - confidence: float (0-100)
                - target_multiplier: float
                - rules_triggered: list of rule names
                - insights: list of insight strings
                - burst_probability: float (0-1)
                - phase: str (cool-down, building, burst)
        """
        recent_rounds = self.history_tracker.get_recent_rounds(100)

        if recent_rounds.empty or len(recent_rounds) < 20:
            return self._empty_signal("Insufficient history data")

        multipliers = recent_rounds['multiplier'].values

        # Initialize signal
        signal = {
            'should_bet': False,
            'confidence': 0.0,
            'target_multiplier': 10.0,
            'rules_triggered': [],
            'insights': [],
            'burst_probability': 0.0,
            'phase': 'unknown',
            'rule_scores': {}
        }

        # Apply all rules
        self._apply_rule_r1_low_green_series(multipliers, signal)
        self._apply_rule_r2_no_20x_gap(multipliers, recent_rounds, signal)
        self._apply_rule_r3_post_high_echo(multipliers, signal)
        self._apply_rule_r5_massive_gap(multipliers, signal)
        self._apply_rule_r6_cluster_series(multipliers, signal)
        self._apply_rule_r7_series_direction(multipliers, signal)
        self._apply_rule_r8_delayed_spike(multipliers, signal)
        self._apply_rule_r10_confidence_builder(multipliers, signal)

        # Apply quantitative rules
        self._apply_quantitative_rules(multipliers, signal)

        # Determine phase
        self._determine_volatility_phase(multipliers, signal)

        # Calculate final confidence
        self._calculate_final_confidence(signal)

        # Generate insights
        self._generate_insights(multipliers, signal)

        return signal

    # ===== OBSERVATIONAL RULES (R1-R10) =====

    def _apply_rule_r1_low_green_series(self, multipliers, signal):
        """R1: Low Green Series → High Round"""
        recent_10 = multipliers[-10:]
        low_count = sum(1 for m in recent_10[-6:] if m < self.LOW_MULTIPLIER_THRESHOLD)

        if low_count >= 4:
            confidence = min(60 + (low_count - 4) * 10, 85)
            signal['rules_triggered'].append('R1_LOW_GREEN_SERIES')
            signal['rule_scores']['R1'] = confidence
            signal['insights'].append(
                f"🟢 R1: {low_count} consecutive low multipliers detected. "
                f"High probability of 10×-20× within next 5-6 rounds."
            )

    def _apply_rule_r2_no_20x_gap(self, multipliers, recent_rounds, signal):
        """R2: No 20× for Long Duration → Big Incoming"""
        # Find last 20× occurrence
        high_indices = [i for i, m in enumerate(multipliers) if m >= self.VERY_HIGH_MULTIPLIER_THRESHOLD]

        if high_indices:
            rounds_since_20x = len(multipliers) - high_indices[-1] - 1
        else:
            rounds_since_20x = len(multipliers)

        # Time-based check (if timestamp available)
        try:
            if not recent_rounds.empty and 'timestamp' in recent_rounds.columns:
                high_rounds = recent_rounds[recent_rounds['multiplier'] >= self.VERY_HIGH_MULTIPLIER_THRESHOLD]
                if not high_rounds.empty:
                    last_high_time = pd.to_datetime(high_rounds.iloc[-1]['timestamp'])
                    time_gap = (datetime.now() - last_high_time).total_seconds() / 60

                    if time_gap >= 30:
                        confidence = min(70 + (time_gap - 30), 90)
                        signal['rules_triggered'].append('R2_NO_20X_GAP')
                        signal['rule_scores']['R2'] = confidence
                        signal['insights'].append(
                            f"🔥 R2: No 20× for {time_gap:.1f} minutes! "
                            f"Expect 50×-100× burst soon."
                        )
                        signal['target_multiplier'] = 50.0
        except:
            pass

        # Round-based check
        if rounds_since_20x >= 40:
            confidence = min(65 + (rounds_since_20x - 40) * 2, 85)
            signal['rules_triggered'].append('R2_NO_20X_GAP_ROUNDS')
            signal['rule_scores']['R2'] = max(signal['rule_scores'].get('R2', 0), confidence)
            signal['insights'].append(
                f"⏰ R2: {rounds_since_20x} rounds since last 20×. Big spike imminent."
            )

    def _apply_rule_r3_post_high_echo(self, multipliers, signal):
        """R3: Post-High Round Echo (5th Rule)"""
        recent_20 = multipliers[-20:]

        # Find high multipliers (5×, 10×, 15×+) in recent history
        high_positions = [(i, m) for i, m in enumerate(recent_20) if m >= 5.0]

        for pos, mult in high_positions:
            echo_pos = pos + 5
            if echo_pos < len(recent_20):
                # We already have the echo - check if it matched
                echo_mult = recent_20[echo_pos]
                expected_range = (mult * 0.5, mult * 2.0)

                if expected_range[0] <= echo_mult <= expected_range[1]:
                    signal['insights'].append(
                        f"✓ R3: Echo confirmed at position +5 from {mult:.2f}× (got {echo_mult:.2f}×)"
                    )
            elif echo_pos == len(recent_20):
                # Next round is the 5th position
                expected_range = (mult * 0.5, mult * 2.0)
                confidence = 70
                signal['rules_triggered'].append('R3_ECHO_5TH')
                signal['rule_scores']['R3'] = confidence
                signal['target_multiplier'] = mult
                signal['insights'].append(
                    f"🎯 R3: Next round is 5th after {mult:.2f}×. "
                    f"Expected range: {expected_range[0]:.2f}×-{expected_range[1]:.2f}×"
                )

    def _apply_rule_r5_massive_gap(self, multipliers, signal):
        """R5: Massive Gap Rule (10-20 reds)"""
        recent_30 = multipliers[-30:]

        # Find red streaks
        red_streak = 0
        max_red_streak = 0

        for m in recent_30:
            if m < self.RED_THRESHOLD:
                red_streak += 1
                max_red_streak = max(max_red_streak, red_streak)
            else:
                red_streak = 0

        if max_red_streak >= 10:
            confidence = min(75 + (max_red_streak - 10) * 3, 95)
            signal['rules_triggered'].append('R5_MASSIVE_GAP')
            signal['rule_scores']['R5'] = confidence
            signal['target_multiplier'] = 25.0
            signal['burst_probability'] = min(0.8 + (max_red_streak - 10) * 0.02, 0.95)
            signal['insights'].append(
                f"🚨 R5: MASSIVE RED STREAK ({max_red_streak} rounds)! "
                f"Strong green wave (10×-50×) expected in next 5-10 rounds."
            )

    def _apply_rule_r6_cluster_series(self, multipliers, signal):
        """R6: Cluster Series Rule"""
        recent_15 = multipliers[-15:]

        # Look for green clusters (3-5 consecutive rounds >2×)
        green_streak = 0
        max_green_streak = 0
        cluster_has_10x = False

        for m in recent_15:
            if m >= 2.0:
                green_streak += 1
                if m >= 10.0:
                    cluster_has_10x = True
            else:
                if green_streak >= 3:
                    max_green_streak = max(max_green_streak, green_streak)
                green_streak = 0

        max_green_streak = max(max_green_streak, green_streak)

        if max_green_streak >= 3 and not cluster_has_10x:
            confidence = 65
            signal['rules_triggered'].append('R6_CLUSTER_SERIES')
            signal['rule_scores']['R6'] = confidence
            signal['insights'].append(
                f"📊 R6: Green cluster of {max_green_streak} rounds detected without 10×. "
                f"Expect one round ≥10× in this cluster."
            )

    def _apply_rule_r7_series_direction(self, multipliers, signal):
        """R7: Series Direction Rule"""
        recent_15 = multipliers[-15:]

        # Check for long green series (8-12 rounds)
        green_series = [m for m in recent_15 if m >= 2.0]

        if len(green_series) >= 8:
            first_avg = np.mean(green_series[:3])
            last_avg = np.mean(green_series[-3:])

            if first_avg > 5.0 and last_avg < 3.0:
                # Series started high, ended low
                signal['insights'].append(
                    f"📉 R7: Long series started high ({first_avg:.2f}×) and ended low ({last_avg:.2f}×). Pattern confirmed."
                )
            elif first_avg < 3.0 and last_avg < 3.0:
                # Series started low, expect high end
                confidence = 60
                signal['rules_triggered'].append('R7_SERIES_DIRECTION')
                signal['rule_scores']['R7'] = confidence
                signal['insights'].append(
                    f"📈 R7: Long series started low. Expect high finish (>10×) soon."
                )

    def _apply_rule_r8_delayed_spike(self, multipliers, signal):
        """R8: Delayed Spike Rule (8th, 10th, 14th)"""
        if len(multipliers) < 20:
            return

        # Find last high multiplier (≥10×)
        high_indices = [i for i, m in enumerate(multipliers) if m >= 10.0]

        if not high_indices:
            return

        last_high_idx = high_indices[-1]
        position_from_high = len(multipliers) - last_high_idx - 1

        # Check if we're at echo positions
        echo_positions = [8, 10, 14]

        if position_from_high in echo_positions:
            confidence = 68
            signal['rules_triggered'].append(f'R8_DELAYED_SPIKE_{position_from_high}')
            signal['rule_scores']['R8'] = confidence
            signal['target_multiplier'] = 7.0
            signal['insights'].append(
                f"🔔 R8: Position {position_from_high} from last high. "
                f"Medium-high spike (5×-10×) likely."
            )

    def _apply_rule_r10_confidence_builder(self, multipliers, signal):
        """R10: Confidence Builder Rule"""
        recent_20 = multipliers[-20:]

        # Count low multipliers
        low_count = sum(1 for m in recent_20 if m < 2.0)
        low_ratio = low_count / len(recent_20)

        if low_ratio > 0.6:  # More than 60% are low
            burst_prob = min(low_ratio * 0.8, 0.85)
            signal['burst_probability'] = max(signal['burst_probability'], burst_prob)
            signal['insights'].append(
                f"⚡ R10: {low_ratio*100:.0f}% low multipliers. "
                f"Burst probability building: {burst_prob*100:.0f}%"
            )

    # ===== QUANTITATIVE RULES (Q1-Q8) =====

    def _apply_quantitative_rules(self, multipliers, signal):
        """Apply quantitative/AI-derived rules"""

        # Q1: LowStreak → Big Spike Probability
        recent_10 = multipliers[-10:]
        low_streak = 0
        for m in reversed(recent_10):
            if m < 2.0:
                low_streak += 1
            else:
                break

        if low_streak >= 5:
            q1_confidence = 60 + (low_streak - 5) * 5
            signal['rule_scores']['Q1'] = min(q1_confidence, 80)
            signal['rules_triggered'].append('Q1_LOW_STREAK_SPIKE')

        # Q2: Gap-based Burst Rule
        high_20x_indices = [i for i, m in enumerate(multipliers) if m >= 20.0]
        if len(high_20x_indices) >= 2:
            gap1 = high_20x_indices[-1] - high_20x_indices[-2]
            gap_score = min(gap1 * 0.5, 50)
            signal['rule_scores']['Q2'] = gap_score

        # Q5: Cluster Mode Rule
        recent_20 = multipliers[-20:]
        highs_in_recent = sum(1 for m in recent_20 if m >= 10.0)
        if highs_in_recent >= 3:
            signal['phase'] = 'high_volatility'
            signal['rule_scores']['Q5'] = 70

        # Q6: Session Energy Rule
        session_energy = np.sum(np.log1p(recent_20)) / len(recent_20)
        if session_energy > 1.5:
            signal['rule_scores']['Q6'] = min(session_energy * 30, 75)

    # ===== PHASE DETECTION =====

    def _determine_volatility_phase(self, multipliers, signal):
        """Determine current volatility phase"""
        recent_30 = multipliers[-30:]

        avg_mult = np.mean(recent_30)
        std_mult = np.std(recent_30)
        high_count = sum(1 for m in recent_30 if m >= 10.0)
        low_count = sum(1 for m in recent_30 if m < 2.0)

        if high_count >= 3 and std_mult > 5.0:
            signal['phase'] = 'burst'
        elif low_count > 20:
            signal['phase'] = 'building'
        elif avg_mult < 2.5 and std_mult < 2.0:
            signal['phase'] = 'cool-down'
        else:
            signal['phase'] = 'normal'

    # ===== FINAL CALCULATIONS =====

    def _calculate_final_confidence(self, signal):
        """Calculate final confidence score from all triggered rules"""
        rule_scores = signal['rule_scores']

        if not rule_scores:
            signal['confidence'] = 0.0
            signal['should_bet'] = False
            return

        # Weighted average of rule scores
        weights = {
            'R1': 1.2, 'R2': 1.5, 'R3': 1.0, 'R5': 1.8, 'R6': 0.9,
            'R7': 0.8, 'R8': 1.1, 'R10': 1.0, 'Q1': 1.3, 'Q2': 1.2,
            'Q5': 1.0, 'Q6': 0.9
        }

        weighted_sum = sum(score * weights.get(rule, 1.0) for rule, score in rule_scores.items())
        total_weight = sum(weights.get(rule, 1.0) for rule in rule_scores.keys())

        final_confidence = weighted_sum / total_weight if total_weight > 0 else 0

        # Boost confidence if multiple rules triggered
        if len(rule_scores) >= 3:
            final_confidence *= 1.15
        elif len(rule_scores) >= 2:
            final_confidence *= 1.08

        signal['confidence'] = min(final_confidence, 95.0)

        # Decision threshold for Position 2: Higher confidence required (70%+)
        signal['should_bet'] = signal['confidence'] >= 70.0

    def _generate_insights(self, multipliers, signal):
        """Generate additional insights for logging"""
        recent_10 = multipliers[-10:]

        # Add phase insight
        phase_emoji = {
            'burst': '🔥',
            'building': '⚡',
            'cool-down': '❄️',
            'normal': '➡️',
            'high_volatility': '🌪️'
        }

        emoji = phase_emoji.get(signal['phase'], '❓')
        signal['insights'].insert(0, f"{emoji} PHASE: {signal['phase'].upper()}")

        # Add recent history
        history_str = ', '.join([f"{m:.2f}×" for m in recent_10])
        signal['insights'].insert(1, f"📊 Last 10: {history_str}")

        # Add decision summary
        if signal['should_bet']:
            signal['insights'].append(
                f"\n✅ POSITION 2 RECOMMENDATION: BET for {signal['target_multiplier']:.1f}× target "
                f"(Confidence: {signal['confidence']:.1f}%)"
            )
        else:
            signal['insights'].append(
                f"\n⏭️  POSITION 2: SKIP (Confidence: {signal['confidence']:.1f}% < 70%)"
            )

    def _empty_signal(self, reason):
        """Return empty signal with reason"""
        return {
            'should_bet': False,
            'confidence': 0.0,
            'target_multiplier': 0.0,
            'rules_triggered': [],
            'insights': [f"⚠️ {reason}"],
            'burst_probability': 0.0,
            'phase': 'unknown',
            'rule_scores': {}
        }

    # ===== UTILITY METHODS =====

    def get_burst_cycle_analysis(self):
        """
        Analyze burst cycles for long-term pattern detection.

        Returns:
            dict: Burst cycle analysis
        """
        recent_100 = self.history_tracker.get_recent_rounds(100)

        if recent_100.empty:
            return {'status': 'insufficient_data'}

        multipliers = recent_100['multiplier'].values

        # Find all high multipliers
        high_50x = [i for i, m in enumerate(multipliers) if m >= 50.0]
        high_20x = [i for i, m in enumerate(multipliers) if m >= 20.0]
        high_10x = [i for i, m in enumerate(multipliers) if m >= 10.0]

        analysis = {
            'high_50x_count': len(high_50x),
            'high_20x_count': len(high_20x),
            'high_10x_count': len(high_10x),
            'avg_gap_between_20x': 0,
            'last_50x_position': None,
            'probability_next_burst': 0.0
        }

        if len(high_20x) >= 2:
            gaps = [high_20x[i] - high_20x[i-1] for i in range(1, len(high_20x))]
            analysis['avg_gap_between_20x'] = np.mean(gaps)

        if high_50x:
            analysis['last_50x_position'] = len(multipliers) - high_50x[-1] - 1

        # Calculate burst probability based on gaps
        if high_20x:
            rounds_since_last_20x = len(multipliers) - high_20x[-1] - 1
            analysis['probability_next_burst'] = min(rounds_since_last_20x / 50.0, 0.9)

        return analysis
