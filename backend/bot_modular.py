"""
Aviator Bot - Enhanced Logging & Model Insights
"""

import sys
import io

# Fix Windows console encoding for emojis
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

import time
from datetime import datetime
import re

# Import configuration
from config import ConfigManager

# Import core modules
from core import GameStateDetector, RoundHistoryTracker, MLSignalGenerator, Position2RuleEngine

# Import dashboard
from dashboard import AviatorDashboard

# Import utilities
from utils.betting_helpers import (
    set_stake_verified,
    place_bet_with_verification,
    cashout_verified,
    estimate_multiplier,
    increase_stake,
    reset_stake
)


class AviatorBotML:
    """Main Aviator Bot with enhanced logging and model insights."""

    def __init__(self):
        """Initialize bot with default settings."""
        self.config_manager = ConfigManager()
        
        # Bot state
        self.current_stake = 25
        self.is_betting = False
        self.bet_state = "IDLE"
        self.active_bet_round = None
        self.last_balance = None
        self.last_logged_mult = None
        
        # Components (initialized after config load)
        self.detector = None
        self.history_tracker = None
        self.ml_generator = None
        self.position2_engine = None
        self.dashboard = None
        
        # Balance coordinates
        self.balance_coords = (626, 149, 694, 152)
        
        # Statistics
        self.stats = {
            "rounds_played": 0,
            "rounds_observed": 0,
            "ml_bets_placed": 0,
            "successful_cashouts": 0,
            "failed_cashouts": 0,
            "ml_skipped": 0,
            "cancelled_bets": 0,
            "total_bet": 0,
            "total_return": 0,
            "current_streak": 0,
            "max_stake_reached": 25
        }
    
    def initialize_components(self):
        """Initialize all bot components after config is loaded."""
        if self.config_manager.multiplier_region:
            self.detector = GameStateDetector(self.config_manager.multiplier_region)

        if self.config_manager.history_region:
            self.history_tracker = RoundHistoryTracker(self.config_manager.history_region)

        if self.history_tracker:
            self.ml_generator = MLSignalGenerator(self.history_tracker)
            self.position2_engine = Position2RuleEngine(self.history_tracker)

        self.current_stake = self.config_manager.initial_stake
    
    def _reset_bet_state(self):
        """Reset betting state completely."""
        self.is_betting = False
        self.bet_state = "IDLE"
        self.active_bet_round = None
    
    def _read_balance(self):
        """Read current balance from balance region."""
        try:
            import pyautogui
            import pyperclip
            
            x1, y1, x2, y2 = self.balance_coords
            
            pyautogui.click((x1 + x2) // 2, (y1 + y2) // 2, clicks=3)
            time.sleep(0.1)
            
            pyautogui.hotkey('ctrl', 'c')
            time.sleep(0.1)
            
            balance_text = pyperclip.paste().strip()
            
            if not balance_text:
                return None
            
            balance_text = balance_text.replace(',', '')
            
            if 'K' in balance_text.upper():
                match = re.search(r'([\d.]+)K', balance_text.upper())
                if match:
                    return float(match.group(1)) * 1000
            else:
                match = re.search(r'[\d.]+', balance_text)
                if match:
                    return float(match.group(0))
            
            return None
        except Exception as e:
            return None
    
    def _verify_bet_placed(self, timeout=3):
        """Verify if bet is already placed by checking button state."""
        try:
            import pyautogui
            from PIL import Image
            import numpy as np
            
            x, y = self.config_manager.bet_button_coords
            screenshot = pyautogui.screenshot(region=(x-50, y-25, 100, 50))
            img_array = np.array(screenshot)
            
            red_channel = img_array[:, :, 0]
            avg_red = np.mean(red_channel)
            
            if avg_red > 150:
                return True
            
            return False
        except Exception as e:
            return False
    
    def _check_existing_bet(self):
        """Check if there's an existing bet from previous round."""
        if self._verify_bet_placed():
            return True
        return False
    
    def _verify_game_running_strict(self):
        """Strict verification that game is actually running."""
        state = self.detector.read_text_in_region()
        multiplier = self.detector.read_multiplier_from_clipboard()
        
        if state == 'FLYING':
            return True
        
        if multiplier and multiplier > 1.0:
            return True
        
        if state and 'x' in str(state).lower() and state not in ['AWAITING', 'FLEW AWAY']:
            return True
        
        return False
    
    def _wait_for_game_start_strict(self, timeout=15):
        """Wait for game to start with strict verification."""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            elapsed = time.time() - start_time
            
            current_state = self.detector.read_text_in_region()
            if current_state == 'AWAITING' and elapsed > 3:
                return False
            
            if self._verify_game_running_strict():
                return True
            
            time.sleep(0.2)
        
        return False
    
    def _wait_for_crash_and_read_multiplier(self, timeout=60):
        """Wait for round to crash and read the final multiplier."""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            if self.detector.has_game_crashed() or self.detector.is_awaiting_next_flight():
                time.sleep(0.3)
                
                success, mult = self.history_tracker.auto_log_from_clipboard(self.detector, force=True)
                
                if success and mult:
                    self.last_logged_mult = mult
                    return True, mult
                else:
                    state = self.detector.read_text_in_region()
                    if state and 'x' in str(state).lower():
                        try:
                            mult_str = state.replace('x', '').strip()
                            mult = float(mult_str)
                            self.last_logged_mult = mult
                            return True, mult
                        except:
                            pass
                    
                    return False, None
            
            time.sleep(0.3)
        
        return False, None
    
    def _show_position2_insights(self, pos2_signal):
        """Display Position 2 rule engine insights."""
        if not pos2_signal:
            return

        print("\n" + "="*85)
        print("🎯 POSITION 2 - BURST CYCLE ANALYSIS")
        print("="*85)

        # Display insights
        for insight in pos2_signal.get('insights', []):
            print(f"  {insight}")

        # Display rules triggered
        rules = pos2_signal.get('rules_triggered', [])
        if rules:
            print(f"\n  🔔 Rules Triggered: {', '.join(rules)}")

        # Display rule scores
        scores = pos2_signal.get('rule_scores', {})
        if scores:
            print(f"\n  📊 Rule Scores:")
            for rule, score in sorted(scores.items(), key=lambda x: x[1], reverse=True):
                bar_len = int(score / 5)
                bar = "█" * bar_len + "░" * (20 - bar_len)
                print(f"     {rule:>3}: [{bar}] {score:.1f}%")

        # Display burst probability
        burst_prob = pos2_signal.get('burst_probability', 0)
        if burst_prob > 0:
            print(f"\n  💥 Burst Probability: {burst_prob*100:.0f}%")

        print("="*85)

    def _show_model_predictions(self, signal):
        """Display individual model predictions in clean table format."""
        if not signal:
            return

        # Get models from signal
        models = signal.get('models', [])

        if not models:
            return

        print("\n🤖 ML MODEL ANALYSIS")

        # Show recent history context
        recent_rounds = self.history_tracker.get_recent_multipliers(10)
        if recent_rounds:
            print(f"📊 History: {', '.join([f'{m:.2f}x' for m in recent_rounds[-10:]])} | Avg: {sum(recent_rounds[-10:]) / len(recent_rounds[-10:]):.2f}x")

        # Pattern analysis
        pattern = self.ml_generator.analyze_recent_patterns(10)
        if pattern:
            print(f"📉 Volatility: {pattern.get('volatility', 0):.2f} | Trend: {pattern.get('trend', 'unknown').upper()}")

        print("")
        print(f"{'MODEL':<15} {'PRED':>8} {'CONFIDENCE':>12} {'STATUS':>8}   {'REASONING':<28}")
        print("-" * 85)

        # Show each model's prediction
        for model in models:
            model_id = model.get('model_id', 'Unknown')
            pred = model.get('prediction', 0)
            conf = model.get('confidence', 0)

            # Status based on confidence
            if conf >= 80:
                status = "HIGH"
                icon = "🟢"
            elif conf >= 65:
                status = "MED"
                icon = "🟡"
            else:
                status = "LOW"
                icon = "🔴"

            # Generate reasoning based on prediction
            if pred >= 2.5:
                reason = "High multiplier expected"
            elif pred >= 2.0:
                reason = "Moderate multiplier likely"
            elif pred >= 1.5:
                reason = "Safe range predicted"
            else:
                reason = "Low multiplier warning"

            print(f"{model_id:<15} {pred:>6.2f}x {conf:>10.1f}% {icon} {status:>6}   {reason:<28}")

        # Ensemble prediction
        ens_pred = signal.get('prediction', 0)
        ens_conf = signal.get('confidence', 0)
        ens_range = signal.get('range', (0, 0))

        if ens_conf >= 80:
            ens_status = "HIGH"
            ens_icon = "🟢"
        elif ens_conf >= 65:
            ens_status = "MED"
            ens_icon = "🟡"
        else:
            ens_status = "LOW"
            ens_icon = "🔴"

        # Ensemble reasoning
        if ens_conf >= self.ml_generator.confidence_threshold:
            ens_reason = "Confidence threshold met"
        else:
            ens_reason = "Below confidence threshold"

        print("-" * 85)
        print(f"{'ENSEMBLE':<15} {ens_pred:>6.2f}x {ens_conf:>10.1f}% {ens_icon} {ens_status:>6}   {ens_reason:<28}")

        # Additional context
        if isinstance(ens_range, tuple) and len(ens_range) == 2:
            print(f"\nRange: {ens_range[0]:.2f}x - {ens_range[1]:.2f}x | Target: {self.config_manager.cashout_delay}s (~{estimate_multiplier(self.config_manager.cashout_delay):.2f}x)")

        # Decision explanation
        if signal.get('should_bet'):
            print(f"\n✅ BET: Confidence {ens_conf:.1f}% > Threshold {self.ml_generator.confidence_threshold}%")
        else:
            print(f"\n⏭️  SKIP: {signal.get('reason', 'Low confidence')}")
    
    def _show_cashout_progress(self, elapsed, target_time):
        """Show cashout progress as scrollable lines (every 0.5s)."""
        remaining = target_time - elapsed

        if remaining <= 0:
            return

        # Only print every 0.5 seconds to make it scrollable
        if not hasattr(self, '_last_progress_print'):
            self._last_progress_print = 0

        if elapsed - self._last_progress_print < 0.5:
            return

        self._last_progress_print = elapsed

        # Calculate progress
        progress_pct = (elapsed / target_time) * 100
        bar_length = 30
        filled = int((progress_pct / 100) * bar_length)
        bar = '█' * filled + '░' * (bar_length - filled)

        # Color and status based on remaining time
        if remaining > 2:
            color = '🟢'
            status = 'SAFE'
        elif remaining > 1:
            color = '🟡'
            status = 'READY'
        elif remaining > 0.5:
            color = '🟠'
            status = 'ALERT'
        else:
            color = '🔴'
            status = 'NOW!'

        # Estimated current multiplier
        current_mult = estimate_multiplier(elapsed)

        print(f"  {color} [{bar}] {elapsed:.1f}s / {target_time:.1f}s | {status:5s} | ~{current_mult:.2f}x")
    
    def _log_round_header(self, round_num):
        """Print round header."""
        print(f"\n{'='*85}")
        print(f"ROUND #{round_num:03d}")
        print(f"{'='*85}")
    
    def _log_decision(self, action, signal, stake=0):
        """Log betting decision with details."""
        self._show_model_predictions(signal)

        # Show action summary
        print("")
        if action == "BET":
            print(f"💰 PLACING BET - Stake: {stake}")
        elif action == "SKIP":
            print(f"⏭️  SKIPPING ROUND")
    
    def _log_round_result(self, round_num, action, stake, result, profit, mult, signal, balance, cumulative):
        """Log round result in a clean format."""
        timestamp = datetime.now().strftime("%H:%M:%S")

        print("\n" + "-" * 85)
        print("ROUND RESULT")
        print("-" * 85)

        # Result icon
        if result == "WIN":
            icon = "✅"
            result_text = "WIN"
        elif result == "CRASH":
            icon = "💥"
            result_text = "CRASHED"
        elif result == "CANCEL":
            icon = "🚫"
            result_text = "CANCELLED"
        elif result == "NOSTART":
            icon = "⚠️"
            result_text = "NO START"
        elif result == "SKIP":
            icon = "⏭️"
            result_text = "SKIPPED"
        else:
            icon = "❓"
            result_text = result

        # Build result line
        result_parts = [f"{icon} {result_text}"]

        if stake > 0:
            result_parts.append(f"Stake: {stake:.0f}")

        if mult > 0:
            result_parts.append(f"Multiplier: {mult:.2f}x")

        if profit != 0:
            profit_sign = "+" if profit > 0 else ""
            result_parts.append(f"P/L: {profit_sign}{profit:.2f}")

        if balance:
            result_parts.append(f"Balance: {balance:.2f}")

        result_parts.append(f"Total P/L: {cumulative:+.2f}")

        if result == "WIN":
            result_parts.append(f"Streak: {self.stats['current_streak']}")

        # Print all in one line
        print(" | ".join(result_parts))
        print("-" * 85)
    
    def _create_round_data(self, multiplier, bet_placed, stake, cashout_time, 
                          profit_loss, signal, cumulative_profit, balance=None):
        """Create round data dictionary for dashboard."""
        return {
            'timestamp': datetime.now().isoformat(),
            'multiplier': multiplier,
            'bet_placed': bet_placed,
            'stake': stake,
            'cashout_time': cashout_time,
            'profit_loss': profit_loss,
            'prediction': signal.get('prediction', 0) if signal else 0,
            'confidence': signal.get('confidence', 0) if signal else 0,
            'cumulative_profit': cumulative_profit,
            'balance': balance,
            'stats': self.stats.copy(),
            'current_stake': self.current_stake
        }
    
    def _emit_dashboard_update(self, round_data):
        """Emit update to dashboard if available."""
        if self.dashboard:
            self.dashboard.emit_round_update(round_data)
    
    def run_ml_mode(self):
        """Main betting loop with enhanced logging."""
        print("\n" + "="*100)
        print("✈️  AVIATOR BOT - ML MODE WITH ENHANCED LOGGING")
        print("="*100)
        print(f"💰 Stake: {self.config_manager.initial_stake}-{self.config_manager.max_stake} | " +
              f"⏱️  Cashout: {self.config_manager.cashout_delay}s | " +
              f"🎯 Threshold: {self.ml_generator.confidence_threshold}%")
        print("="*100)
        
        cumulative_profit = 0
        round_number = 0
        history_read_for_round = False

        try:
            while True:
                round_number += 1
                self._log_round_header(round_number)
                
                # STEP 1: Wait for clean AWAITING state
                print("  ⏳ Waiting for AWAITING state...")
                if not self.detector.wait_for_clean_awaiting_state(timeout=60):
                    print("  ⚠️  Timeout - retrying...")
                    continue
                
                print("  ✅ AWAITING confirmed")
                time.sleep(0.3)
                
                # STEP 2: Check for existing bet
                if self._check_existing_bet():
                    print("  🚫 Orphaned bet detected!")
                    self.stats["cancelled_bets"] += 1
                    self.stats["failed_cashouts"] += 1
                    
                    loss = -self.current_stake
                    cumulative_profit += loss
                    
                    self._log_round_result(round_number, "BET", self.current_stake, "CANCEL",
                                          loss, 0, None, self.last_balance, cumulative_profit)

                    self.history_tracker.log_round(0, True, self.current_stake, 0, loss, 0, 0, 'orphaned', pos2_signal=None)
                    round_data = self._create_round_data(0, True, self.current_stake, 0, loss, 
                                                         None, cumulative_profit, self.last_balance)
                    self._emit_dashboard_update(round_data)
                    
                    self.current_stake = reset_stake(self.config_manager.initial_stake, self.stats)
                    self._reset_bet_state()
                    history_read_for_round = False
                    continue
                
                # STEP 3: Read previous round multiplier
                if not history_read_for_round:
                    print("  📝 Reading previous round...")
                    success, logged_mult = self.history_tracker.auto_log_from_clipboard(self.detector, force=False)
                    
                    if success and logged_mult:
                        self.last_logged_mult = logged_mult
                        print(f"  ✅ Previous round: {logged_mult:.2f}x")
                    else:
                        print("  ℹ️  No previous round data")
                    
                    history_read_for_round = True
                
                time.sleep(0.2)

                # STEP 4: Generate ML signal for Position 1
                print("\n  🤖 Analyzing patterns...")
                signal = self.ml_generator.generate_ensemble_signal()

                # STEP 4.5: Generate Position 2 signal (for higher multiplier opportunities)
                pos2_signal = None
                if self.position2_engine:
                    pos2_signal = self.position2_engine.analyze_position2_signal()
                    self._show_position2_insights(pos2_signal)
                
                if signal['should_bet']:
                    # BETTING ROUND
                    stake_used = self.current_stake
                    self._log_decision("BET", signal, stake_used)
                    
                    # Pre-bet checks
                    if self.detector.is_game_already_running():
                        print("  ⚠️  Game already running - aborting")
                        self.stats["rounds_observed"] += 1
                        self.stats["ml_skipped"] += 1
                        self._reset_bet_state()
                        history_read_for_round = False
                        continue
                    
                    # Set stake
                    print(f"\n  💰 Setting stake: {stake_used}...")
                    if not set_stake_verified(self.config_manager.stake_coords, stake_used):
                        print("  ❌ Stake setting failed")
                        self.stats["rounds_observed"] += 1
                        self.stats["ml_skipped"] += 1
                        self._reset_bet_state()
                        history_read_for_round = False
                        continue
                    
                    print("  ✅ Stake set")
                    time.sleep(0.15)
                    
                    # Place bet
                    print(f"  💵 Placing bet...")
                    bet_success, bet_reason = place_bet_with_verification(
                        self.config_manager.bet_button_coords,
                        self.detector,
                        self.stats,
                        self.current_stake
                    )
                    
                    if not bet_success:
                        print(f"  ❌ Bet failed: {bet_reason}")
                        self.stats["rounds_observed"] += 1
                        self.stats["ml_skipped"] += 1
                        self._reset_bet_state()
                        history_read_for_round = False
                        continue
                    
                    print("  ✅ Bet placed!")
                    self.is_betting = True
                    self.bet_state = "PLACED"
                    self.active_bet_round = round_number
                    
                    time.sleep(0.5)
                    
                    # Wait for game start
                    print("\n  ⏳ Waiting for game start...")
                    game_started = self._wait_for_game_start_strict(timeout=15)
                    
                    if not game_started:
                        print("  ⚠️  Game didn't start - bet cancelled")
                        self.stats["cancelled_bets"] += 1
                        self.stats["failed_cashouts"] += 1
                        
                        loss = -stake_used
                        cumulative_profit += loss
                        
                        self._log_round_result(round_number, "BET", stake_used, "NOSTART",
                                              loss, 0, signal, self.last_balance, cumulative_profit)

                        self.history_tracker.log_round(0, True, stake_used, 0, loss,
                                                      signal['prediction'], signal['confidence'], 'no_start',
                                                      pos2_signal=pos2_signal)
                        
                        round_data = self._create_round_data(0, True, stake_used, 0, loss, 
                                                             signal, cumulative_profit, self.last_balance)
                        self._emit_dashboard_update(round_data)
                        
                        self.current_stake = reset_stake(self.config_manager.initial_stake, self.stats)
                        self._reset_bet_state()
                        self.stats["rounds_observed"] += 1
                        history_read_for_round = False
                        continue
                    
                    print("  🚀 Game started!")
                    
                    # CASHOUT COUNTDOWN
                    print(f"\n  ⏱️  CASHOUT COUNTDOWN - TARGET: {self.config_manager.cashout_delay}s")
                    print("  " + "─"*90)
                    
                    round_start = time.time()
                    cashout_triggered = False
                    last_crash_check = time.time()
                    crash_check_interval = 0.3
                    
                    while True:
                        current_time = time.time()
                        elapsed = current_time - round_start
                        remaining = self.config_manager.cashout_delay - elapsed
                        
                        # Show progress
                        self._show_cashout_progress(elapsed, self.config_manager.cashout_delay)
                        
                        # Check for crash
                        if current_time - last_crash_check >= crash_check_interval:
                            if self.detector.has_game_crashed():
                                print("\n")
                                print(f"  💥 CRASHED at {elapsed:.3f}s (target: {self.config_manager.cashout_delay}s)")
                                
                                self.stats["failed_cashouts"] += 1
                                self.stats["current_streak"] = 0
                                
                                loss = -stake_used
                                cumulative_profit += loss
                                
                                success, crash_mult = self._wait_for_crash_and_read_multiplier(timeout=5)
                                final_mult = crash_mult if success else 0
                                
                                self._log_round_result(round_number, "BET", stake_used, "CRASH",
                                                      loss, final_mult, signal, self.last_balance, cumulative_profit)

                                self.history_tracker.log_round(final_mult, True, stake_used, elapsed, loss,
                                                              signal['prediction'], signal['confidence'], signal['range'],
                                                              pos2_signal=pos2_signal)
                                
                                round_data = self._create_round_data(final_mult, True, stake_used, elapsed, loss, 
                                                                     signal, cumulative_profit, self.last_balance)
                                self._emit_dashboard_update(round_data)
                                
                                self.current_stake = reset_stake(self.config_manager.initial_stake, self.stats)
                                self._reset_bet_state()
                                history_read_for_round = False
                                break
                            
                            last_crash_check = current_time
                        
                        # Trigger cashout
                        if remaining <= 0 and not cashout_triggered:
                            cashout_triggered = True
                            actual_elapsed = time.time() - round_start
                            
                            print("\n")
                            print(f"  💰 EXECUTING CASHOUT at {actual_elapsed:.3f}s...")
                            
                            time.sleep(0.05)
                            
                            # Final crash check
                            if self.detector.has_game_crashed():
                                print(f"  💥 Crashed during cashout attempt!")
                                
                                self.stats["failed_cashouts"] += 1
                                self.stats["current_streak"] = 0
                                
                                loss = -stake_used
                                cumulative_profit += loss
                                
                                success, crash_mult = self._wait_for_crash_and_read_multiplier(timeout=5)
                                final_mult = crash_mult if success else 0
                                
                                self._log_round_result(round_number, "BET", stake_used, "CRASH",
                                                      loss, final_mult, signal, self.last_balance, cumulative_profit)

                                self.history_tracker.log_round(final_mult, True, stake_used, actual_elapsed, loss,
                                                              signal['prediction'], signal['confidence'], signal['range'],
                                                              pos2_signal=pos2_signal)
                                
                                round_data = self._create_round_data(final_mult, True, stake_used, actual_elapsed, loss, 
                                                                     signal, cumulative_profit, self.last_balance)
                                self._emit_dashboard_update(round_data)
                                
                                self.current_stake = reset_stake(self.config_manager.initial_stake, self.stats)
                                self._reset_bet_state()
                                history_read_for_round = False
                                break
                            
                            # Execute cashout
                            cashout_success, cashout_reason = cashout_verified(
                                self.config_manager.cashout_coords,
                                self.detector
                            )
                            
                            if cashout_success:
                                print("  ✅ Cashout successful!")
                                
                                # Read balance
                                time.sleep(0.3)
                                new_balance = self._read_balance()
                                
                                self.stats["successful_cashouts"] += 1
                                self.stats["current_streak"] += 1
                                
                                final_mult = estimate_multiplier(self.config_manager.cashout_delay)
                                returns = stake_used * final_mult
                                profit = returns - stake_used
                                cumulative_profit += profit
                                self.stats["total_return"] += returns
                                
                                self._log_round_result(round_number, "BET", stake_used, "WIN",
                                                      profit, final_mult, signal, new_balance, cumulative_profit)

                                self.history_tracker.log_round(final_mult, True, stake_used,
                                                              self.config_manager.cashout_delay, profit,
                                                              signal['prediction'], signal['confidence'], signal['range'],
                                                              pos2_signal=pos2_signal)
                                
                                round_data = self._create_round_data(final_mult, True, stake_used, 
                                                                     self.config_manager.cashout_delay, profit, 
                                                                     signal, cumulative_profit, new_balance)
                                self._emit_dashboard_update(round_data)
                                
                                self.last_balance = new_balance
                                
                                self.current_stake = increase_stake(
                                    self.current_stake,
                                    self.config_manager.stake_increase_percent,
                                    self.config_manager.max_stake,
                                    self.stats
                                )
                            else:
                                print(f"  ❌ Cashout failed: {cashout_reason}")
                                
                                time.sleep(0.2)
                                if self.detector.has_game_crashed() or cashout_reason == "NO_ACTIVE_BET":
                                    self.stats["failed_cashouts"] += 1
                                    self.stats["current_streak"] = 0
                                    
                                    loss = -stake_used
                                    cumulative_profit += loss
                                    
                                    success, crash_mult = self._wait_for_crash_and_read_multiplier(timeout=5)
                                    final_mult = crash_mult if success else 0
                                    
                                    self._log_round_result(round_number, "BET", stake_used, "CRASH",
                                                          loss, final_mult, signal, self.last_balance, cumulative_profit)

                                    self.history_tracker.log_round(final_mult, True, stake_used, actual_elapsed, loss,
                                                                  signal['prediction'], signal['confidence'], signal['range'],
                                                                  pos2_signal=pos2_signal)
                                    
                                    round_data = self._create_round_data(final_mult, True, stake_used, actual_elapsed, loss, 
                                                                         signal, cumulative_profit, self.last_balance)
                                    self._emit_dashboard_update(round_data)
                                else:
                                    self.stats["failed_cashouts"] += 1
                                    self.stats["current_streak"] = 0
                                    loss = -stake_used
                                    cumulative_profit += loss
                                
                                self.current_stake = reset_stake(self.config_manager.initial_stake, self.stats)
                            
                            self._reset_bet_state()
                            history_read_for_round = False
                            break
                        
                        # Adaptive sleep
                        if remaining > 1:
                            time.sleep(0.1)
                        elif remaining > 0.3:
                            time.sleep(0.05)
                        else:
                            time.sleep(0.01)
                
                else:
                    # SKIP ROUND
                    self._log_decision("SKIP", signal)
                    self.stats["ml_skipped"] += 1
                    self._reset_bet_state()
                    
                    print("\n  ⏳ Waiting for round to complete...")
                    success, observed_mult = self._wait_for_crash_and_read_multiplier(timeout=60)
                    
                    if not success:
                        observed_mult = 2.0
                    
                    print(f"  📊 Observed: {observed_mult:.2f}x")
                    
                    self._log_round_result(round_number, "SKIP", 0, "SKIP",
                                          0, observed_mult, signal, self.last_balance, cumulative_profit)

                    self.history_tracker.log_round(observed_mult, False, 0, 0, 0,
                                                  signal['prediction'], signal['confidence'], signal['range'],
                                                  pos2_signal=pos2_signal)
                    
                    round_data = self._create_round_data(observed_mult, False, 0, 0, 0, 
                                                         signal, cumulative_profit, self.last_balance)
                    self._emit_dashboard_update(round_data)
                    
                    history_read_for_round = False
                
                self.stats["rounds_observed"] += 1
                
                if self.dashboard:
                    self.dashboard.emit_stats_update()
                
                time.sleep(0.3)

        except KeyboardInterrupt:
            print("\n\n⏹️  Bot stopped by user")
            self.print_stats()
        except Exception as e:
            print(f"\n\n❌ Error: {e}")
            import traceback
            traceback.print_exc()
            self.print_stats()

    def print_stats(self):
        """Print final statistics."""
        print("\n" + "="*100)
        print("📊 FINAL STATISTICS")
        print("="*100)
        print(f"Rounds observed:      {self.stats['rounds_observed']}")
        print(f"ML bets placed:       {self.stats['ml_bets_placed']}")
        print(f"Successful cashouts:  {self.stats['successful_cashouts']}")
        print(f"Failed cashouts:      {self.stats['failed_cashouts']}")
        print(f"Cancelled bets:       {self.stats['cancelled_bets']}")
        print(f"Skipped rounds:       {self.stats['ml_skipped']}")
        
        if self.stats['ml_bets_placed'] > 0:
            success_rate = (self.stats['successful_cashouts'] / self.stats['ml_bets_placed']) * 100
            print(f"Success rate:         {success_rate:.1f}%")
        
        print(f"\n💰 Financial:")
        print(f"  Total bet:          {self.stats['total_bet']:.2f}")
        print(f"  Total return:       {self.stats['total_return']:.2f}")
        profit = self.stats['total_return'] - self.stats['total_bet']
        print(f"  Profit/Loss:        {profit:+.2f}")
        
        if self.stats['total_bet'] > 0:
            roi = (profit / self.stats['total_bet']) * 100
            print(f"  ROI:                {roi:+.1f}%")
        
        if self.last_balance:
            print(f"  Final balance:      {self.last_balance:.2f}")
        
        print("="*100 + "\n")


def main():
    """Main entry point."""
    print("="*100)
    print("✈️  AVIATOR BOT - ML MODE WITH ENHANCED LOGGING")
    print("="*100)
    print("\n🎯 Features:")
    print("  ✓ Manual history input for better predictions")
    print("  ✓ Individual model predictions (LSTM, Random Forest, XGBoost, LightGBM)")
    print("  ✓ Enhanced cashout progress indicator")
    print("  ✓ Detailed round-by-round logging")
    print("  ✓ Real-time balance tracking")
    print("="*100)

    bot = AviatorBotML()

    # Load or setup configuration
    if bot.config_manager.load_config() and bot.config_manager.multiplier_region:
        print(f"\n✓ Config loaded")
        print("\nOptions:")
        print("  1. Use existing config")
        print("  2. New setup")
        choice = input("\nChoice (1/2): ").strip()
        
        if choice == '2':
            bot.config_manager.setup_coordinates()
    else:
        bot.config_manager.setup_coordinates()

    # Initialize components
    bot.initialize_components()
    
    # Load manual history for better ML predictions
    from manual_history_loader import integrate_manual_history_with_bot
    rounds_loaded = integrate_manual_history_with_bot(bot)
    
    if rounds_loaded > 0:
        print(f"\n✅ {rounds_loaded} historical rounds loaded")
        print("🤖 ML models will make better predictions with this data")

    # Configure parameters
    print("\n" + "="*100)
    print("⚙️  PARAMETERS")
    print("="*100)
    
    initial = input(f"\nInitial stake (default {bot.config_manager.initial_stake}): ").strip()
    if initial:
        bot.config_manager.initial_stake = int(initial)
        bot.current_stake = bot.config_manager.initial_stake
    
    max_stake = input(f"Max stake (default {bot.config_manager.max_stake}): ").strip()
    if max_stake:
        bot.config_manager.max_stake = int(max_stake)
    
    increase = input(f"Stake increase % (default {bot.config_manager.stake_increase_percent}): ").strip()
    if increase:
        bot.config_manager.stake_increase_percent = int(increase)
    
    delay = input(f"Cashout delay seconds (default {bot.config_manager.cashout_delay}): ").strip()
    if delay:
        bot.config_manager.cashout_delay = float(delay)
    
    threshold = input(f"ML threshold % (default {bot.ml_generator.confidence_threshold}): ").strip()
    if threshold:
        bot.ml_generator.confidence_threshold = float(threshold)

    estimated_mult = estimate_multiplier(bot.config_manager.cashout_delay)
    
    print("\n" + "="*100)
    print("📋 SUMMARY")
    print("="*100)
    print(f"Initial stake:     {bot.config_manager.initial_stake}")
    print(f"Max stake:         {bot.config_manager.max_stake}")
    print(f"Increase on win:   +{bot.config_manager.stake_increase_percent}%")
    print(f"Cashout timing:    {bot.config_manager.cashout_delay}s (~{estimated_mult}x)")
    print(f"ML threshold:      {bot.ml_generator.confidence_threshold}%")
    print(f"Balance tracking:  Enabled")
    print("="*100)
    
    # Start dashboard (optional)
    # start_dash = input("\nStart web dashboard? (y/n, default: n): ").strip().lower()
    # if start_dash == 'y':
        # print("\n🌐 Starting dashboard...")
        # bot.dashboard = AviatorDashboard(bot, port=5000)
        # bot.dashboard.start()
        # print("✅ Dashboard: http://localhost:5000")
    
    # print("\nPress Enter to start...")
    # input()
    
    # Save config and run
    bot.config_manager.save_config()
    bot.run_ml_mode()


if __name__ == "__main__":
    main()