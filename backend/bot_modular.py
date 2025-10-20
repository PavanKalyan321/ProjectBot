"""
Aviator Bot - Enhanced Logging & Model Insights
"""

import time
from datetime import datetime
import re

# Import configuration
from config import ConfigManager

# Import core modules
from core import GameStateDetector, RoundHistoryTracker, MLSignalGenerator

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

def flush_print(text):
    """Prints text immediately without buffering."""
    print(text, flush=True)

class AviatorBotML:
    """Main Aviator Bot with enhanced logging and model insights."""

    def __init__(self, dry_run=False):
        """Initialize bot with default settings."""
        self.config_manager = ConfigManager()
        self.dry_run = dry_run

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

        # Prediction history (track last N predictions)
        from collections import deque
        self.prediction_history = deque(maxlen=5)
    
    def initialize_components(self):
        """Initialize all bot components after config is loaded."""
        if self.config_manager.multiplier_region:
            self.detector = GameStateDetector(self.config_manager.multiplier_region)
        
        if self.config_manager.history_region:
            self.history_tracker = RoundHistoryTracker(self.config_manager.history_region)
        
        if self.history_tracker:
            self.ml_generator = MLSignalGenerator(self.history_tracker)
        
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
        """
        Wait for round to crash and read the final multiplier.

        Args:
            timeout: Maximum time to wait for crash

        Returns:
            Tuple (success, multiplier)
        """
        start_time = time.time()

        while time.time() - start_time < timeout:
            if self.detector.has_game_crashed() or self.detector.is_awaiting_next_flight():
                time.sleep(0.3)

                # Read multiplier from clipboard
                success, mult = self.history_tracker.auto_log_from_clipboard(
                    self.detector,
                    force=True
                )

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
    
    def _show_detailed_model_analysis(self, signal):
        """
        Display detailed model analysis with individual reasoning and decision breakdown.
        This shows INDIVIDUAL model predictions and reasoning, not just ensemble.
        """
        strategy = signal.get('strategy', 'unknown')
        print(f"\n  [STATS] STRATEGY: {strategy.upper()}")
        print("  " + "-"*90)

        # Position-based strategies (Hybrid mode)
        if 'position1' in strategy or 'position2' in strategy:
            if 'position1' in strategy:
                # Position 1: ML Green Classifier - Simple Table
                print("\n  [TARGET] POSITION 1: ML Green Classifier")
                target = signal.get('target_multiplier', 0)
                green_prob = signal.get('green_probability', 0)
                accuracy = signal.get('classifier_accuracy', 0)
                confidence = signal.get('confidence', 0)

                print("\n  +--------------------------+------------+")
                print("  | METRIC                   | VALUE      |")
                print("  +--------------------------+------------+")
                print(f"  | Target Multiplier        | {target:6.2f}x    |")
                print(f"  | Green Probability        | {green_prob:6.1f}%    |")
                print(f"  | Model Confidence         | {confidence:6.1f}%    |")
                print(f"  | Historical Accuracy      | {accuracy:6.1f}%    |")
                print("  +--------------------------+------------+")

                # Visual probability bar
                bar_length = 30
                filled = int((green_prob / 100) * bar_length)
                bar = "#" * filled + "-" * (bar_length - filled)
                print(f"\n  Success Probability: [{bar}] {green_prob:.1f}%")

                print(f"\n  [IDEA] REASONING:")
                print(f"     ML classifier detected {green_prob:.1f}% probability of hitting {target:.2f}x")
                print(f"     based on recent pattern analysis.")

            elif 'position2' in strategy:
                # Position 2: Rule-based for high multipliers - Simple Table
                print("\n  [DICE] POSITION 2: Rule-Based Pattern Detection")

                if 'cold_streak' in strategy:
                    cold_streak_len = signal.get('cold_streak_length', 0)
                    target = signal.get('target_multiplier', 0)
                    confidence = signal.get('confidence', 0)

                    # Get last 10 rounds for pattern visualization
                    recent_rounds = self.history_tracker.get_recent_rounds(10)
                    if not recent_rounds.empty and 'multiplier' in recent_rounds.columns:
                        recent_mults = recent_rounds['multiplier'].values[-10:]
                        low_count = sum(1 for m in recent_mults if m < 2.0)
                        high_count = sum(1 for m in recent_mults if m >= 3.0)

                        # Simple table for Position 2
                        print("\n  +--------------------------+------------+")
                        print("  | METRIC                   | VALUE      |")
                        print("  +--------------------------+------------+")
                        print(f"  | Pattern Detected         | COLD STREAK|")
                        print(f"  | Low Rounds (<2x)         | {low_count:2d}/10      |")
                        print(f"  | High Rounds (≥3x)        | {high_count:2d}/10      |")
                        print(f"  | Target Multiplier        | {target:6.2f}x    |")
                        print(f"  | Confidence Level         | {confidence:6.1f}%    |")
                        print("  +--------------------------+------------+")

                        # Last 10 rounds visualization (simple)
                        print("\n  [STATS] LAST 10 ROUNDS:")
                        pattern_str = "  "
                        for i, mult in enumerate(recent_mults, 1):
                            if mult < 2.0:
                                icon = "[RED]"
                            elif mult < 3.0:
                                icon = "[YELLOW]"
                            else:
                                icon = "[GREEN]"
                            pattern_str += f"{icon}{mult:.2f}x "
                        print(pattern_str)

                        print(f"\n  [IDEA] REASONING:")
                        print(f"     Extended cold streak detected - {cold_streak_len}/10 rounds below 2x.")
                        print(f"     Statistical analysis suggests higher multiplier is likely.")
                        print(f"     Targeting {target:.2f}x for better returns.")
                    else:
                        # Fallback if no recent rounds available
                        print("\n  +--------------------------+------------+")
                        print("  | METRIC                   | VALUE      |")
                        print("  +--------------------------+------------+")
                        print(f"  | Pattern Detected         | COLD STREAK|")
                        print(f"  | Streak Length            | {cold_streak_len:2d}/10      |")
                        print(f"  | Target Multiplier        | {target:6.2f}x    |")
                        print(f"  | Confidence Level         | {confidence:6.1f}%    |")
                        print("  +--------------------------+------------+")

                        print(f"\n  [IDEA] REASONING:")
                        print(f"     Extended cold streak detected - {cold_streak_len}/10 rounds below 2x.")
                        print(f"     Targeting {target:.2f}x for better returns.")
                else:
                    print("\n  +--------------------------+------------+")
                    print("  | METRIC                   | VALUE      |")
                    print("  +--------------------------+------------+")
                    print(f"  | Pattern Detected         | NONE       |")
                    print(f"  | Decision                 | SKIP       |")
                    print("  +--------------------------+------------+")
                    print(f"\n  [IDEA] REASONING: No strong pattern found. Waiting for better opportunity.")

        # Regression-based models
        elif 'regression' in strategy and signal.get('models'):
            print("\n  [LAB] REGRESSION ENSEMBLE: Individual Model Predictions")
            predictions = signal['models']

            # Table for regression models
            print("\n  +--------------------------+----------+------------+")
            print("  | MODEL                    |   PRED   | CONFIDENCE |")
            print("  +--------------------------+----------+------------+")

            model_names = {
                'RandomForest': 'Random Forest',
                'GradientBoosting': 'Gradient Boosting',
                'LightGBM': 'LightGBM',
                'LSTM': 'LSTM Neural Net'
            }

            for pred in predictions:
                model_id = pred.get('model_id', 'Unknown')
                display_name = model_names.get(model_id, model_id)
                pred_val = pred.get('prediction', 0)
                conf = pred.get('confidence', 0)
                print(f"  | {display_name:<24} | {pred_val:6.2f}x |  {conf:6.1f}%   |")

            print("  +--------------------------+----------+------------+")

            # Ensemble metrics
            ensemble_pred = signal.get('prediction', 0)
            ensemble_conf = signal.get('confidence', 0)
            print(f"  | ENSEMBLE                 | {ensemble_pred:6.2f}x |  {ensemble_conf:6.1f}%   |")
            print("  +--------------------------+----------+------------+")

            agreement = signal.get('agreement', 0)
            expected_value = signal.get('expected_value', 0)

            if agreement:
                agreement_status = "HIGH" if agreement < 0.5 else "MEDIUM" if agreement < 1.0 else "LOW"
                print(f"\n  Model Agreement: {agreement_status} (σ={agreement:.2f})")

            if expected_value:
                print(f"  Expected Value: {expected_value:.2f}")

            print(f"\n  [IDEA] REASONING:")
            if agreement < 0.5:
                print(f"     Models are in HIGH agreement - strong consensus on prediction.")
            elif agreement < 1.0:
                print(f"     Models show MEDIUM agreement - some variation in predictions.")
            else:
                print(f"     Models have LOW agreement - predictions vary significantly.")

        # Skip decision
        elif 'skip' in strategy:
            print("\n  [SKIP]  DECISION: SKIP ROUND")
            reason = signal.get('reason', 'No reason provided')

            print("\n  +--------------------------+------------+")
            print("  | METRIC                   | VALUE      |")
            print("  +--------------------------+------------+")
            print(f"  | Decision                 | SKIP       |")
            print(f"  | Confidence               | {signal.get('confidence', 0):6.1f}%    |")
            print("  +--------------------------+------------+")

            print(f"\n  [IDEA] REASONING: {reason}")
            print(f"     Waiting for stronger signal before placing bet.")

    def _show_model_predictions(self, signal):
        """Display individual model predictions in a compact format."""
        if not signal or 'models' not in signal:
            return

        predictions = signal['models']
        if not predictions:
            return

        # Store prediction for history
        self.prediction_history.append({
            'ensemble': signal.get('prediction', 0),
            'confidence': signal.get('confidence', 0)
        })

        print("\n  [ML] MODEL PREDICTIONS:")
        print("  +------------------+----------+------------+")
        print("  |      MODEL       |   PRED   | CONFIDENCE |")
        print("  +------------------+----------+------------+")

        # Map model IDs to display names
        model_display_names = {
            'RandomForest': 'Random Forest   ',
            'GradientBoosting': 'Gradient Boost  ',
            'LightGBM': 'LightGBM        ',
            'LSTM': 'LSTM            '
        }

        # Display each model's prediction
        for pred in predictions:
            model_id = pred.get('model_id', 'Unknown')
            display_name = model_display_names.get(model_id, model_id.ljust(16))
            pred_val = pred.get('prediction', 0)
            conf = pred.get('confidence', 0)

            print(f"  | {display_name} | {pred_val:6.2f}x |   {conf:5.1f}%   |")

        print("  +------------------+----------+------------+")

        # Show ensemble prediction
        ensemble_pred = signal.get('prediction', 0)
        ensemble_conf = signal.get('confidence', 0)
        print(f"  | ENSEMBLE         | {ensemble_pred:6.2f}x |   {ensemble_conf:5.1f}%   |")
        print("  +------------------+----------+------------+")

        # Show additional metrics
        if 'expected_value' in signal:
            print(f"  Expected Value: {signal['expected_value']:.2f}")
        if 'agreement' in signal:
            agreement_status = "HIGH" if signal['agreement'] < 0.5 else "MEDIUM" if signal['agreement'] < 1.0 else "LOW"
            print(f"  Model Agreement: {agreement_status} (σ={signal['agreement']:.2f})")

        # Show prediction trend (how predictions evolved)
        if len(self.prediction_history) >= 2:
            print(f"\n  [CHART] PREDICTION TREND (Last {len(self.prediction_history)} rounds):")
            trend_line = "  "
            for i, pred_hist in enumerate(self.prediction_history):
                trend_line += f"[{pred_hist['ensemble']:.2f}x] "
                if i < len(self.prediction_history) - 1:
                    # Show trend arrow
                    next_pred = list(self.prediction_history)[i+1]['ensemble']
                    if next_pred > pred_hist['ensemble']:
                        trend_line += "^ "
                    elif next_pred < pred_hist['ensemble']:
                        trend_line += "v "
                    else:
                        trend_line += "> "
            print(trend_line)
    
    def _show_cashout_progress(self, elapsed, target_time):
        """Show enhanced cashout progress with visual indicator."""
        remaining = target_time - elapsed
        
        if remaining <= 0:
            return
        
        # Calculate progress
        progress_pct = (elapsed / target_time) * 100
        bar_length = 40
        filled = int((progress_pct / 100) * bar_length)
        bar = '#' * filled + '-' * (bar_length - filled)
        
        # Color and status based on remaining time
        if remaining > 2:
            color = '[GREEN]'
            status = 'SAFE'
        elif remaining > 1:
            color = '[YELLOW]'
            status = 'READY'
        elif remaining > 0.5:
            color = '[ORANGE]'
            status = 'ALERT'
        else:
            color = '[RED]'
            status = 'NOW!'
        
        # Estimated current multiplier
        current_mult = estimate_multiplier(elapsed)
        
        print(f"  {color} [{bar}] {remaining:.2f}s | {status:5s} | ~{current_mult:.2f}x", end='\r', flush=True)
    
    def _log_round_header(self, round_num):
        """Print round header."""
        print(f"\n{'='*100}")
        print(f"[TARGET] ROUND #{round_num:03d}")
        print(f"{'='*100}")
    
    def _log_decision(self, action, signal, stake=0):
        """Log betting decision with details."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        if action == "BET":
            print(f"\n  [OK] DECISION: PLACE BET")
            print(f"  [MONEY] Stake: {stake}")
            print(f"  [TARGET] Target: {self.config_manager.cashout_delay}s (~{estimate_multiplier(self.config_manager.cashout_delay):.2f}x)")
            print(f"  [STATS] Ensemble Confidence: {signal['confidence']:.1f}%")
            self._show_model_predictions(signal)
        elif action == "SKIP":
            print(f"\n  [SKIP]  DECISION: SKIP ROUND")
            print(f"  [X] Reason: {signal['reason']}")
            print(f"  [STATS] Ensemble Confidence: {signal['confidence']:.1f}% (Threshold: {self.ml_generator.confidence_threshold}%)")

            # Show detailed skip reasoning from actual models
            if 'skip_reason_detailed' in signal:
                print(f"\n  [NOTE] DETAILED ANALYSIS FROM MODELS:")
                print(f"  {'-'*90}")
                for line in signal['skip_reason_detailed'].split('\n'):
                    print(f"  {line}")
                print(f"  {'-'*90}")

            self._show_model_predictions(signal)
    
    def _log_round_result(self, round_num, action, stake, result, profit, mult, signal, balance, cumulative):
        """Log round result in a clean format."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Result icon
        if result == "WIN":
            icon = "[OK]"
            result_color = "SUCCESS"
        elif result == "CRASH":
            icon = "[CRASH]"
            result_color = "CRASHED"
        elif result == "CANCEL":
            icon = "[CANCEL]"
            result_color = "CANCELLED"
        elif result == "NOSTART":
            icon = "[WARNING]"
            result_color = "NO START"
        elif result == "SKIP":
            icon = "[SKIP]"
            result_color = "SKIPPED"
        else:
            icon = "[?]"
            result_color = result
        
        print(f"\n  {icon} RESULT: {result_color}")
        
        if stake > 0:
            print(f"  [CASH] Stake: {stake:.0f}")
        
        if mult > 0:
            print(f"  [MULT] Multiplier: {mult:.2f}x")
        
        if profit != 0:
            profit_sign = "+" if profit > 0 else ""
            print(f"  [MONEY] P/L: {profit_sign}{profit:.2f}")
        
        if balance:
            print(f"  [BAL] Balance: {balance:.2f}")
        
        print(f"  [STATS] Cumulative P/L: {cumulative:+.2f}")
        
        if result == "WIN":
            print(f"  [STREAK] Win Streak: {self.stats['current_streak']}")
        
        print(f"{'-'*100}")
    
    def _create_round_data(self, multiplier, bet_placed, stake, cashout_time,
                          profit_loss, signal, cumulative_profit, balance=None):
        """Create round data dictionary for dashboard."""
        # Extract individual model predictions
        models_data = {'rf': 0, 'gb': 0, 'lgb': 0}
        if signal and 'models' in signal:
            for model in signal['models']:
                model_id = model.get('model_id', '')
                prediction = model.get('prediction', 0)
                if 'Random' in model_id:
                    models_data['rf'] = prediction
                elif 'Gradient' in model_id:
                    models_data['gb'] = prediction
                elif 'LightGBM' in model_id:
                    models_data['lgb'] = prediction

        return {
            'timestamp': datetime.now().isoformat(),
            'multiplier': multiplier,
            'bet_placed': bet_placed,
            'stake': stake,
            'cashout_time': cashout_time,
            'profit_loss': profit_loss,
            'prediction': signal.get('prediction', 0) if signal else 0,
            'confidence': signal.get('confidence', 0) if signal else 0,
            'models': models_data,
            'cumulative_profit': cumulative_profit,
            'balance': balance,
            'stats': self.stats.copy(),
            'current_stake': self.current_stake
        }
    
    def _emit_dashboard_update(self, round_data):
        """Emit update to dashboard if available."""
        if self.dashboard:
            self.dashboard.emit_round_update(round_data)
    
    def run_observation_mode(self):
        """Observation mode - collect data without placing bets."""
        print("\n" + "="*100)
        print("[STATS] AVIATOR BOT - OBSERVATION MODE (DATA COLLECTION)")
        print("="*100)
        print("[SCAN] Bot will observe rounds and collect data without placing bets")
        print("[SAVE] Data will be saved to aviator_rounds_history.csv for model training")
        print("="*100)

        round_number = 0
        history_read_for_round = False

        try:
            while True:
                round_number += 1
                self._log_round_header(round_number)

                # STEP 1: Wait for clean AWAITING state
                flush_print("  [WAIT] Waiting for AWAITING state...")
                if not self.detector.wait_for_clean_awaiting_state(timeout=60):
                    flush_print("  [WARNING]  Timeout - retrying...")
                    continue

                flush_print("  [OK] AWAITING confirmed")
                time.sleep(0.3)

                # STEP 2: Read previous round multiplier and log it
                if not history_read_for_round:
                    flush_print("  [LOG] Checking for previous round...")

                    success, logged_mult = self.history_tracker.auto_log_from_clipboard(
                        self.detector,
                        force=False
                    )

                    if success and logged_mult and logged_mult != self.last_logged_mult:
                        self.last_logged_mult = logged_mult

                        # Explicitly log this round to CSV
                        self.history_tracker.log_round(
                            multiplier=logged_mult,
                            bet_placed=False,
                            stake=0,
                            cashout_time=0,
                            profit_loss=0
                        )

                        flush_print(f"  [OK] Round observed: {logged_mult:.2f}x (saved to history)")
                        self.stats["rounds_observed"] += 1
                    else:
                        flush_print("  [INFO]  No new round data")

                    history_read_for_round = True

                time.sleep(0.2)

                # STEP 3: Generate predictions (for display only, no betting)
                print("\n  [ML] Generating predictions (no bet will be placed)...")
                signal = self.ml_generator.generate_ensemble_signal()

                print(f"\n  [STATS] OBSERVATION ONLY - No bet placed")
                print(f"  [TARGET] Model would predict: {signal['prediction']:.2f}x")
                print(f"  [CHART] Confidence: {signal['confidence']:.1f}%")
                print(f"  [DICE] Decision would be: {'BET' if signal['should_bet'] else 'SKIP'}")

                # Optionally show full model predictions
                if signal['should_bet']:
                    self._show_model_predictions(signal)

                # Wait for current round to complete
                print("\n  [WAIT] Waiting for current round to complete...")
                success, observed_mult = self._wait_for_crash_and_read_multiplier(timeout=60)

                if success and observed_mult:
                    print(f"  [OK] Round complete: {observed_mult:.2f}x")
                    self.stats["rounds_observed"] += 1
                else:
                    print("  [WARNING]  Could not read round result")

                # Show highest multipliers for different time windows
                self.ml_generator.log_highest_multipliers()

                history_read_for_round = False

                # Show observation stats
                if round_number % 10 == 0:
                    print(f"\n  [CHART] Progress: {self.stats['rounds_observed']} rounds collected")
                    print(f"  [SAVE] Data saved to: aviator_rounds_history.csv")

                time.sleep(0.5)

        except KeyboardInterrupt:
            print("\n\n[STOP]  Observation stopped by user")
            print(f"\n[STATS] Total rounds observed: {self.stats['rounds_observed']}")
            print(f"[SAVE] Data saved to: aviator_rounds_history.csv")
            print(f"\nYou can now train models with: python train_models.py")
        except Exception as e:
            print(f"\n\n[X] Error: {e}")
            import traceback
            traceback.print_exc()

    def run_dry_run_mode(self):
        """
        DRY RUN MODE - Logs all betting decisions without placing actual bets.
        Simulates the full betting flow and tracks hypothetical profit/loss.
        """
        print("\n" + "="*100)
        print("[LOG] AVIATOR BOT - DRY RUN MODE (SIMULATION)")
        print("="*100)
        print("[SCAN] Bot will simulate all betting decisions WITHOUT placing real bets")
        print("[IDEA] All ML predictions, stake management, and outcomes will be logged")
        print("[STATS] Hypothetical profit/loss will be tracked based on actual multipliers")
        print("[SAVE] Data will be saved to CSV for analysis")
        print("="*100)

        cumulative_profit = 0
        hypothetical_balance = 1000.0  # Starting hypothetical balance
        round_number = 0
        history_read_for_round = False

        try:
            while True:
                round_number += 1
                self._log_round_header(round_number)

                # STEP 1: Wait for clean AWAITING state
                flush_print("  [WAIT] Waiting for AWAITING state...")
                if not self.detector.wait_for_clean_awaiting_state(timeout=60):
                    flush_print("  [WARNING]  Timeout - retrying...")
                    continue

                flush_print("  [OK] AWAITING confirmed")
                time.sleep(0.3)

                # STEP 2: Read previous round multiplier
                if not history_read_for_round:
                    flush_print("  [LOG] Checking for previous round...")

                    success, logged_mult = self.history_tracker.auto_log_from_clipboard(
                        self.detector,
                        force=False
                    )

                    if success and logged_mult and logged_mult != self.last_logged_mult:
                        self.last_logged_mult = logged_mult
                        flush_print(f"  [OK] Previous round: {logged_mult:.2f}x (added to history)")
                    else:
                        flush_print("  [INFO]  No new round data")

                    history_read_for_round = True

                time.sleep(0.2)

                # STEP 3: Generate ML signal
                print("\n  [ML] Analyzing patterns (DRY RUN - no bet will be placed)...")
                signal = self.ml_generator.generate_ensemble_signal()

                if signal['should_bet']:
                    # SIMULATED BETTING ROUND
                    stake_used = self.current_stake

                    print(f"\n  [LOG] SIMULATED DECISION: WOULD PLACE BET")
                    print(f"  [MONEY] Simulated Stake: {stake_used}")
                    print(f"  [TARGET] Target: {self.config_manager.cashout_delay}s (~{estimate_multiplier(self.config_manager.cashout_delay):.2f}x)")
                    print(f"  [STATS] Ensemble Confidence: {signal['confidence']:.1f}%")

                    # Show detailed model analysis
                    self._show_detailed_model_analysis(signal)

                    # Wait for current round to complete
                    print("\n  [WAIT] Waiting for round to complete to calculate hypothetical outcome...")
                    success, observed_mult = self._wait_for_crash_and_read_multiplier(timeout=60)

                    if not success:
                        observed_mult = 2.0
                        print("  [WARNING]  Could not read multiplier, using default 2.0x")

                    # Calculate hypothetical outcome
                    target_mult = estimate_multiplier(self.config_manager.cashout_delay)

                    if observed_mult >= target_mult:
                        # SIMULATED WIN
                        hypothetical_return = stake_used * target_mult
                        hypothetical_profit = hypothetical_return - stake_used
                        cumulative_profit += hypothetical_profit
                        hypothetical_balance += hypothetical_profit

                        self.stats["successful_cashouts"] += 1
                        self.stats["ml_bets_placed"] += 1
                        self.stats["total_bet"] += stake_used
                        self.stats["total_return"] += hypothetical_return
                        self.stats["current_streak"] += 1

                        print(f"\n  [OK] SIMULATED RESULT: WIN (would have cashed out at {target_mult:.2f}x)")
                        print(f"  [CASH] Simulated Stake: {stake_used:.0f}")
                        print(f"  [MULT] Actual Multiplier: {observed_mult:.2f}x")
                        print(f"  [TARGET] Target Multiplier: {target_mult:.2f}x")
                        print(f"  [MONEY] Hypothetical P/L: +{hypothetical_profit:.2f}")
                        print(f"  [BAL] Hypothetical Balance: {hypothetical_balance:.2f}")
                        print(f"  [STATS] Cumulative P/L: {cumulative_profit:+.2f}")
                        print(f"  [STREAK] Win Streak: {self.stats['current_streak']}")
                        print(f"{'-'*100}")

                        # Log to history with Position 2 signal if applicable
                        pos2_data = None
                        if 'position2' in signal.get('strategy', ''):
                            pos2_data = signal

                        self.history_tracker.log_round(
                            multiplier=observed_mult,
                            bet_placed=True,
                            stake=stake_used,
                            cashout_time=self.config_manager.cashout_delay,
                            profit_loss=hypothetical_profit,
                            prediction=signal['prediction'],
                            confidence=signal['confidence'],
                            pred_range=(0, 0),
                            pos2_signal=pos2_data
                        )

                        # Increase stake on win
                        self.current_stake = increase_stake(
                            self.current_stake,
                            self.config_manager.stake_increase_percent,
                            self.config_manager.max_stake,
                            self.stats
                        )
                    else:
                        # SIMULATED LOSS
                        hypothetical_loss = -stake_used
                        cumulative_profit += hypothetical_loss
                        hypothetical_balance += hypothetical_loss

                        self.stats["failed_cashouts"] += 1
                        self.stats["ml_bets_placed"] += 1
                        self.stats["total_bet"] += stake_used
                        self.stats["current_streak"] = 0

                        print(f"\n  [CRASH] SIMULATED RESULT: LOSS (crashed before target)")
                        print(f"  [CASH] Simulated Stake: {stake_used:.0f}")
                        print(f"  [MULT] Actual Multiplier: {observed_mult:.2f}x")
                        print(f"  [TARGET] Target Multiplier: {target_mult:.2f}x")
                        print(f"  [MONEY] Hypothetical P/L: {hypothetical_loss:.2f}")
                        print(f"  [BAL] Hypothetical Balance: {hypothetical_balance:.2f}")
                        print(f"  [STATS] Cumulative P/L: {cumulative_profit:+.2f}")
                        print(f"{'-'*100}")

                        # Log to history with Position 2 signal if applicable
                        pos2_data = None
                        if 'position2' in signal.get('strategy', ''):
                            pos2_data = signal

                        self.history_tracker.log_round(
                            multiplier=observed_mult,
                            bet_placed=True,
                            stake=stake_used,
                            cashout_time=self.config_manager.cashout_delay,
                            profit_loss=hypothetical_loss,
                            prediction=signal['prediction'],
                            confidence=signal['confidence'],
                            pred_range=(0, 0),
                            pos2_signal=pos2_data
                        )

                        # Reset stake on loss
                        self.current_stake = reset_stake(self.config_manager.initial_stake, self.stats)

                else:
                    # SKIP ROUND
                    print(f"\n  [SKIP]  SIMULATED DECISION: WOULD SKIP")
                    print(f"  [X] Reason: {signal['reason']}")
                    print(f"  [STATS] Ensemble Confidence: {signal['confidence']:.1f}% (Threshold: {self.ml_generator.confidence_threshold}%)")

                    # Show detailed model analysis for skip decision
                    self._show_detailed_model_analysis(signal)

                    self.stats["ml_skipped"] += 1

                    print("\n  [WAIT] Waiting for round to complete...")
                    success, observed_mult = self._wait_for_crash_and_read_multiplier(timeout=60)

                    if not success:
                        observed_mult = 2.0

                    print(f"\n  [SKIP]  SIMULATED RESULT: SKIPPED")
                    print(f"  [MULT] Observed Multiplier: {observed_mult:.2f}x")
                    print(f"  [MONEY] Hypothetical P/L: 0.00")
                    print(f"  [BAL] Hypothetical Balance: {hypothetical_balance:.2f}")
                    print(f"  [STATS] Cumulative P/L: {cumulative_profit:+.2f}")
                    print(f"{'-'*100}")

                    # Log to history with Position 2 signal if applicable
                    pos2_data = None
                    if 'position2' in signal.get('strategy', ''):
                        pos2_data = signal

                    self.history_tracker.log_round(
                        multiplier=observed_mult,
                        bet_placed=False,
                        stake=0,
                        cashout_time=0,
                        profit_loss=0,
                        prediction=signal['prediction'],
                        confidence=signal['confidence'],
                        pred_range=(0, 0),
                        pos2_signal=pos2_data
                    )

                # Show highest multipliers for different time windows
                self.ml_generator.log_highest_multipliers()

                history_read_for_round = False
                self.stats["rounds_observed"] += 1

                # Show periodic summary
                if round_number % 10 == 0:
                    print(f"\n  [CHART] DRY RUN SUMMARY (after {round_number} rounds):")
                    print(f"  [MONEY] Hypothetical Balance: {hypothetical_balance:.2f}")
                    print(f"  [STATS] Cumulative P/L: {cumulative_profit:+.2f}")
                    if self.stats['ml_bets_placed'] > 0:
                        win_rate = (self.stats['successful_cashouts'] / self.stats['ml_bets_placed']) * 100
                        print(f"  [OK] Win Rate: {win_rate:.1f}%")
                        print(f"  [TARGET] Bets Simulated: {self.stats['ml_bets_placed']}")

                time.sleep(0.3)

        except KeyboardInterrupt:
            print("\n\n[STOP]  Dry run stopped by user")
            self.print_dry_run_stats(cumulative_profit, hypothetical_balance)
        except Exception as e:
            print(f"\n\n[X] Error: {e}")
            import traceback
            traceback.print_exc()
            self.print_dry_run_stats(cumulative_profit, hypothetical_balance)

    def print_dry_run_stats(self, cumulative_profit, hypothetical_balance):
        """Print dry run statistics."""
        print("\n" + "="*100)
        print("[STATS] DRY RUN FINAL STATISTICS")
        print("="*100)
        print(f"Rounds observed:       {self.stats['rounds_observed']}")
        print(f"Simulated bets:        {self.stats['ml_bets_placed']}")
        print(f"Simulated wins:        {self.stats['successful_cashouts']}")
        print(f"Simulated losses:      {self.stats['failed_cashouts']}")
        print(f"Skipped rounds:        {self.stats['ml_skipped']}")

        if self.stats['ml_bets_placed'] > 0:
            success_rate = (self.stats['successful_cashouts'] / self.stats['ml_bets_placed']) * 100
            print(f"Win rate:              {success_rate:.1f}%")

        print(f"\n[MONEY] Hypothetical Financial:")
        print(f"  Total staked:        {self.stats['total_bet']:.2f}")
        print(f"  Total returned:      {self.stats['total_return']:.2f}")
        print(f"  Profit/Loss:         {cumulative_profit:+.2f}")
        print(f"  Final balance:       {hypothetical_balance:.2f}")

        if self.stats['total_bet'] > 0:
            roi = (cumulative_profit / self.stats['total_bet']) * 100
            print(f"  ROI:                 {roi:+.1f}%")

        print("\n[IDEA] This was a simulation - NO REAL BETS WERE PLACED")
        print("[STATS] All data has been logged to CSV for analysis")
        print("="*100 + "\n")

    def run_ml_mode(self):
        """Main betting loop with enhanced logging."""
        print("\n" + "="*100)
        print("[PLANE]  AVIATOR BOT - ML MODE WITH ENHANCED LOGGING")
        print("="*100)
        print(f"[MONEY] Stake: {self.config_manager.initial_stake}-{self.config_manager.max_stake} | " +
              f"[TIMER]  Cashout: {self.config_manager.cashout_delay}s | " +
              f"[TARGET] Threshold: {self.ml_generator.confidence_threshold}%")
        print("="*100)
        
        cumulative_profit = 0
        round_number = 0
        history_read_for_round = False

        try:
            while True:
                round_number += 1
                self._log_round_header(round_number)
                
                # STEP 1: Wait for clean AWAITING state
                flush_print("  [WAIT] Waiting for AWAITING state...")
                if not self.detector.wait_for_clean_awaiting_state(timeout=60):
                    flush_print("  [WARNING]  Timeout - retrying...")
                    continue
                
                flush_print("  [OK] AWAITING confirmed")
                time.sleep(0.3)
                
                # STEP 2: Check for existing bet
                if self._check_existing_bet():
                    flush_print("  [CANCEL] Orphaned bet detected!")
                    self.stats["cancelled_bets"] += 1
                    self.stats["failed_cashouts"] += 1
                    
                    loss = -self.current_stake
                    cumulative_profit += loss
                    
                    self._log_round_result(round_number, "BET", self.current_stake, "CANCEL", 
                                          loss, 0, None, self.last_balance, cumulative_profit)
                    
                    self.history_tracker.log_round(
                        multiplier=0,
                        bet_placed=True,
                        stake=self.current_stake,
                        cashout_time=0,
                        profit_loss=loss,
                        prediction=0,
                        confidence=0,
                        pred_range=(0, 0)
                    )
                    round_data = self._create_round_data(0, True, self.current_stake, 0, loss, 
                                                         None, cumulative_profit, self.last_balance)
                    self._emit_dashboard_update(round_data)
                    
                    self.current_stake = reset_stake(self.config_manager.initial_stake, self.stats)
                    self._reset_bet_state()
                    history_read_for_round = False
                    continue
                
                # STEP 3: Read previous round multiplier and update history in real-time
                if not history_read_for_round:
                    flush_print("  [LOG] Checking for previous round...")

                    # Read from clipboard and immediately add to history for real-time predictions
                    success, logged_mult = self.history_tracker.auto_log_from_clipboard(
                        self.detector,
                        force=False
                    )

                    if success and logged_mult and logged_mult != self.last_logged_mult:
                        self.last_logged_mult = logged_mult
                        flush_print(f"  [OK] Previous round: {logged_mult:.2f}x (added to history)")
                    else:
                        flush_print("  [INFO]  No new round data")

                    history_read_for_round = True

                time.sleep(0.2)

                # STEP 4: Generate ML signal with LATEST data (includes the round we just read)
                print("\n  [ML] Analyzing patterns with latest round data...")
                signal = self.ml_generator.generate_ensemble_signal()
                
                if signal['should_bet']:
                    # BETTING ROUND
                    stake_used = self.current_stake
                    self._log_decision("BET", signal, stake_used)
                    
                    # Pre-bet checks
                    if self.detector.is_game_already_running():
                        print("  [WARNING]  Game already running - aborting")
                        self.stats["rounds_observed"] += 1
                        self.stats["ml_skipped"] += 1
                        self._reset_bet_state()
                        history_read_for_round = False
                        continue
                    
                    # Set stake
                    print(f"\n  [MONEY] Setting stake: {stake_used}...")
                    if not set_stake_verified(self.config_manager.stake_coords, stake_used):
                        print("  [X] Stake setting failed")
                        self.stats["rounds_observed"] += 1
                        self.stats["ml_skipped"] += 1
                        self._reset_bet_state()
                        history_read_for_round = False
                        continue
                    
                    print("  [OK] Stake set")
                    time.sleep(0.15)
                    
                    # Place bet
                    print(f"  [CASH] Placing bet...")
                    bet_success, bet_reason = place_bet_with_verification(
                        self.config_manager.bet_button_coords,
                        self.detector,
                        self.stats,
                        self.current_stake
                    )
                    
                    if not bet_success:
                        print(f"  [X] Bet failed: {bet_reason}")
                        self.stats["rounds_observed"] += 1
                        self.stats["ml_skipped"] += 1
                        self._reset_bet_state()
                        history_read_for_round = False
                        continue
                    
                    print("  [OK] Bet placed!")
                    self.is_betting = True
                    self.bet_state = "PLACED"
                    self.active_bet_round = round_number
                    
                    time.sleep(0.5)
                    
                    # Wait for game start
                    print("\n  [WAIT] Waiting for game start...")
                    game_started = self._wait_for_game_start_strict(timeout=15)
                    
                    if not game_started:
                        print("  [WARNING]  Game didn't start - bet cancelled")
                        self.stats["cancelled_bets"] += 1
                        self.stats["failed_cashouts"] += 1
                        
                        loss = -stake_used
                        cumulative_profit += loss
                        
                        self._log_round_result(round_number, "BET", stake_used, "NOSTART", 
                                              loss, 0, signal, self.last_balance, cumulative_profit)
                        
                        self.history_tracker.log_round(
                            multiplier=0,
                            bet_placed=True,
                            stake=stake_used,
                            cashout_time=0,
                            profit_loss=loss,
                            prediction=signal['prediction'],
                            confidence=signal['confidence'],
                            pred_range=(0, 0)
                        )
                        
                        round_data = self._create_round_data(0, True, stake_used, 0, loss, 
                                                             signal, cumulative_profit, self.last_balance)
                        self._emit_dashboard_update(round_data)
                        
                        self.current_stake = reset_stake(self.config_manager.initial_stake, self.stats)
                        self._reset_bet_state()
                        self.stats["rounds_observed"] += 1
                        history_read_for_round = False
                        continue
                    
                    print("  [ROCKET] Game started!")
                    
                    # CASHOUT COUNTDOWN
                    print(f"\n  [TIMER]  CASHOUT COUNTDOWN - TARGET: {self.config_manager.cashout_delay}s")
                    print("  " + "-"*90)
                    
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
                                print(f"  [CRASH] CRASHED at {elapsed:.3f}s (target: {self.config_manager.cashout_delay}s)")
                                
                                self.stats["failed_cashouts"] += 1
                                self.stats["current_streak"] = 0
                                
                                loss = -stake_used
                                cumulative_profit += loss
                                
                                success, crash_mult = self._wait_for_crash_and_read_multiplier(timeout=5)
                                final_mult = crash_mult if success else 0
                                
                                self._log_round_result(round_number, "BET", stake_used, "CRASH", 
                                                      loss, final_mult, signal, self.last_balance, cumulative_profit)
                                
                                self.history_tracker.log_round(
                                    multiplier=final_mult,
                                    bet_placed=True,
                                    stake=stake_used,
                                    cashout_time=elapsed,
                                    profit_loss=loss,
                                    prediction=signal['prediction'],
                                    confidence=signal['confidence'],
                                    pred_range=(0, 0)
                                )
                                
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
                            print(f"  [MONEY] EXECUTING CASHOUT at {actual_elapsed:.3f}s...")
                            
                            time.sleep(0.05)
                            
                            # Final crash check
                            if self.detector.has_game_crashed():
                                print(f"  [CRASH] Crashed during cashout attempt!")
                                
                                self.stats["failed_cashouts"] += 1
                                self.stats["current_streak"] = 0
                                
                                loss = -stake_used
                                cumulative_profit += loss
                                
                                success, crash_mult = self._wait_for_crash_and_read_multiplier(timeout=5)
                                final_mult = crash_mult if success else 0
                                
                                self._log_round_result(round_number, "BET", stake_used, "CRASH", 
                                                      loss, final_mult, signal, self.last_balance, cumulative_profit)
                                
                                self.history_tracker.log_round(
                                    multiplier=final_mult,
                                    bet_placed=True,
                                    stake=stake_used,
                                    cashout_time=actual_elapsed,
                                    profit_loss=loss,
                                    prediction=signal['prediction'],
                                    confidence=signal['confidence'],
                                    pred_range=(0, 0)
                                )
                                
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
                                print("  [OK] Cashout command sent!")

                                # Wait for balance to update (0.5s delay)
                                print("  [WAIT] Validating balance change...")
                                time.sleep(0.5)
                                new_balance = self._read_balance()

                                # Validate if we actually won by checking balance
                                if self.last_balance is not None and new_balance is not None:
                                    balance_change = new_balance - self.last_balance

                                    # If balance increased, it was a real win
                                    if balance_change > 0:
                                        print(f"  [OK] Balance validation: WIN confirmed (+{balance_change:.2f})")

                                        self.stats["successful_cashouts"] += 1
                                        self.stats["current_streak"] += 1

                                        final_mult = estimate_multiplier(self.config_manager.cashout_delay)
                                        profit = balance_change
                                        returns = stake_used + profit
                                        cumulative_profit += profit
                                        self.stats["total_return"] += returns

                                        self._log_round_result(round_number, "BET", stake_used, "WIN",
                                                              profit, final_mult, signal, new_balance, cumulative_profit)

                                        self.history_tracker.log_round(
                                            multiplier=final_mult,
                                            bet_placed=True,
                                            stake=stake_used,
                                            cashout_time=self.config_manager.cashout_delay,
                                            profit_loss=profit,
                                            prediction=signal['prediction'],
                                            confidence=signal['confidence'],
                                            pred_range=(0, 0)
                                        )

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
                                        # Balance didn't increase - cashout failed, we lost
                                        print(f"  [X] Balance validation: LOST (balance change: {balance_change:.2f})")

                                        self.stats["failed_cashouts"] += 1
                                        self.stats["current_streak"] = 0

                                        loss = -stake_used
                                        cumulative_profit += loss

                                        # Try to read actual crash multiplier
                                        success, crash_mult = self._wait_for_crash_and_read_multiplier(timeout=5)
                                        final_mult = crash_mult if success else 0

                                        self._log_round_result(round_number, "BET", stake_used, "CRASH",
                                                              loss, final_mult, signal, new_balance, cumulative_profit)

                                        self.history_tracker.log_round(
                                            multiplier=final_mult,
                                            bet_placed=True,
                                            stake=stake_used,
                                            cashout_time=actual_elapsed,
                                            profit_loss=loss,
                                            prediction=signal['prediction'],
                                            confidence=signal['confidence'],
                                            pred_range=(0, 0)
                                        )

                                        round_data = self._create_round_data(final_mult, True, stake_used, actual_elapsed, loss,
                                                                             signal, cumulative_profit, new_balance)
                                        self._emit_dashboard_update(round_data)

                                        self.last_balance = new_balance
                                        self.current_stake = reset_stake(self.config_manager.initial_stake, self.stats)
                                else:
                                    # Could not read balance - fallback to estimated profit
                                    print("  [WARNING]  Could not validate balance - using estimated profit")

                                    self.stats["successful_cashouts"] += 1
                                    self.stats["current_streak"] += 1

                                    final_mult = estimate_multiplier(self.config_manager.cashout_delay)
                                    returns = stake_used * final_mult
                                    profit = returns - stake_used
                                    cumulative_profit += profit
                                    self.stats["total_return"] += returns

                                    self._log_round_result(round_number, "BET", stake_used, "WIN",
                                                          profit, final_mult, signal, new_balance, cumulative_profit)

                                    self.history_tracker.log_round(
                                        multiplier=final_mult,
                                        bet_placed=True,
                                        stake=stake_used,
                                        cashout_time=self.config_manager.cashout_delay,
                                        profit_loss=profit,
                                        prediction=signal['prediction'],
                                        confidence=signal['confidence'],
                                        pred_range=(0, 0)
                                    )

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
                                print(f"  [X] Cashout failed: {cashout_reason}")
                                
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
                                    
                                    self.history_tracker.log_round(
                                        multiplier=final_mult,
                                        bet_placed=True,
                                        stake=stake_used,
                                        cashout_time=actual_elapsed,
                                        profit_loss=loss,
                                        prediction=signal['prediction'],
                                        confidence=signal['confidence'],
                                        pred_range=(0, 0)
                                    )
                                    
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
                    
                    print("\n  [WAIT] Waiting for round to complete...")
                    success, observed_mult = self._wait_for_crash_and_read_multiplier(timeout=60)
                    
                    if not success:
                        observed_mult = 2.0
                    
                    print(f"  [STATS] Observed: {observed_mult:.2f}x")
                    
                    self._log_round_result(round_number, "SKIP", 0, "SKIP", 
                                          0, observed_mult, signal, self.last_balance, cumulative_profit)
                    
                    self.history_tracker.log_round(
                        multiplier=observed_mult,
                        bet_placed=False,
                        stake=0,
                        cashout_time=0,
                        profit_loss=0,
                        prediction=signal['prediction'],
                        confidence=signal['confidence'],
                        pred_range=(0, 0)
                    )
                    
                    round_data = self._create_round_data(observed_mult, False, 0, 0, 0,
                                                         signal, cumulative_profit, self.last_balance)
                    self._emit_dashboard_update(round_data)

                    history_read_for_round = False

                # Show highest multipliers for different time windows
                self.ml_generator.log_highest_multipliers()

                self.stats["rounds_observed"] += 1
                
                if self.dashboard:
                    self.dashboard.emit_stats_update()
                
                time.sleep(0.3)

        except KeyboardInterrupt:
            print("\n\n[STOP]  Bot stopped by user")
            self.print_stats()
        except Exception as e:
            print(f"\n\n[X] Error: {e}")
            import traceback
            traceback.print_exc()
            self.print_stats()

    def print_stats(self):
        """Print final statistics."""
        print("\n" + "="*100)
        print("[STATS] FINAL STATISTICS")
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
        
        print(f"\n[MONEY] Financial:")
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
    print("AVIATOR BOT - ML MODE WITH ENHANCED LOGGING")
    print("="*100)
    print("\nFeatures:")
    print("  [OK] Manual history input for better predictions")
    print("  [OK] Individual model predictions (LSTM, Random Forest, XGBoost, LightGBM)")
    print("  [OK] Enhanced cashout progress indicator")
    print("  [OK] Detailed round-by-round logging")
    print("  [OK] Real-time balance tracking")
    print("  [OK] Time-weighted ML training (recent data prioritized)")
    print("="*100)

    bot = AviatorBotML()

    # Load or setup configuration
    if bot.config_manager.load_config() and bot.config_manager.multiplier_region:
        print(f"\n[OK] Config loaded")
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
        print(f"\n[OK] {rounds_loaded} historical rounds loaded")
        print("[OK] ML models will make better predictions with this data")

    # Configure parameters
    print("\n" + "="*100)
    print("PARAMETERS")
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
    print("[NOTE] SUMMARY")
    print("="*100)
    print(f"Initial stake:     {bot.config_manager.initial_stake}")
    print(f"Max stake:         {bot.config_manager.max_stake}")
    print(f"Increase on win:   +{bot.config_manager.stake_increase_percent}%")
    print(f"Cashout timing:    {bot.config_manager.cashout_delay}s (~{estimated_mult}x)")
    print(f"ML threshold:      {bot.ml_generator.confidence_threshold}%")
    print(f"Balance tracking:  Enabled")
    print("="*100)
    
    # Start dashboard (optional)
    start_dash = input("\nStart web dashboard? (y/n, default: n): ").strip().lower()
    if start_dash == 'y':
        print("\nStarting dashboard...")
        bot.dashboard = AviatorDashboard(bot, port=5000)
        bot.dashboard.start()
        print("[OK] Dashboard: http://localhost:5000")

    # Ask user about betting mode
    print("\n" + "="*100)
    print("OPERATING MODE")
    print("="*100)
    print("\nChoose mode:")
    print("  1. BETTING MODE - Place real bets based on ML predictions")
    print("  2. DRY RUN MODE - Simulate betting and log all decisions (NO REAL BETS)")
    print("  3. OBSERVATION MODE - Collect data without betting (build history for training)")
    print("\nNote: Models need at least 20 rounds of data before they can make predictions.")

    mode_choice = input("\nChoice (1/2/3, default: 1): ").strip()

    if mode_choice == '2':
        mode = 'dry_run'
        print("\n[LOG] DRY RUN MODE - Bot will simulate all decisions WITHOUT placing real bets")
    elif mode_choice == '3':
        mode = 'observation'
        print("\n[STATS] OBSERVATION MODE - Bot will only collect data, no bets will be placed")
    else:
        mode = 'betting'
        print("\n[MONEY] BETTING MODE - Bot will place real bets based on ML predictions")

    print("\nPress Enter to start...")
    input()

    # Save config and run
    bot.config_manager.save_config()

    if mode == 'observation':
        bot.run_observation_mode()
    elif mode == 'dry_run':
        bot.run_dry_run_mode()
    else:
        bot.run_ml_mode()


if __name__ == "__main__":
    main()