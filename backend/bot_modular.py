"""
Aviator Bot - Enhanced with Hot Run Mode & Real Multiplier Cashout
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

# Import multiplier reader
from readregion import MultiplierReader

# Import multiplier reader
from readregion import MultiplierReader

def flush_print(text):
    """Prints text immediately without buffering."""
    print(text, flush=True)

class AviatorBotML:
    """Main Aviator Bot with Hot Run mode and real multiplier cashout."""

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
        self.fixed_cashout_multiplier = 2.0  # User-defined cashout target

        # Components (initialized after config load)
        self.detector = None
        self.history_tracker = None
        self.ml_generator = None
        self.dashboard = None
        self.multiplier_reader = None  # NEW: Real-time multiplier reader

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
        
        # Hot Run mode
        self.hot_run_mode = False
        self.target_cashout_multiplier = 2.0  # Default target for hot run
    
    def initialize_components(self):
        """Initialize all bot components after config is loaded."""
        if self.config_manager.multiplier_region:
            self.detector = GameStateDetector(self.config_manager.multiplier_region)
            
            # Initialize multiplier reader for real-time tracking
            region_dict = {
                "top": self.config_manager.multiplier_region[1],
                "left": self.config_manager.multiplier_region[0],
                "width": self.config_manager.multiplier_region[2] - self.config_manager.multiplier_region[0],
                "height": self.config_manager.multiplier_region[3] - self.config_manager.multiplier_region[1]
            }
            
            # Validate region is within screen bounds
            try:
                import mss
                with mss.mss() as sct:
                    monitors = sct.monitors
                    primary = monitors[1]  # Primary monitor
                    
                    # Check if region is valid
                    if (region_dict["left"] < 0 or region_dict["top"] < 0 or
                        region_dict["left"] + region_dict["width"] > primary["width"] or
                        region_dict["top"] + region_dict["height"] > primary["height"]):
                        print("[WARNING] Multiplier region is outside screen bounds!")
                        print(f"[INFO] Screen: {primary['width']}x{primary['height']}")
                        print(f"[INFO] Region: left={region_dict['left']}, top={region_dict['top']}, "
                              f"width={region_dict['width']}, height={region_dict['height']}")
                        print("[TIP] Run setup again to reconfigure regions")
                        
                        response = input("\nContinue anyway? (y/n): ").strip().lower()
                        if response != 'y':
                            print("[STOP] Exiting...")
                            exit(1)
            except Exception as e:
                print(f"[WARNING] Could not validate region: {e}")
            
            self.multiplier_reader = MultiplierReader(region_dict)
            
            # Test multiplier reader
            print("\n[TEST] Testing multiplier reader...")
            test_frame = self.multiplier_reader.capture_region()
            if test_frame is None:
                print("[WARNING] Cannot capture multiplier region!")
                print("[TIP] Make sure game window is visible and not minimized")
                print("[TIP] Run setup again if coordinates are incorrect")
                
                response = input("\nContinue anyway? (y/n): ").strip().lower()
                if response != 'y':
                    print("[STOP] Exiting...")
                    exit(1)
            else:
                print("[OK] Multiplier reader working correctly")
        
        if self.config_manager.history_region:
            self.history_tracker = RoundHistoryTracker(self.config_manager.history_region)
        
        if self.history_tracker:
            self.ml_generator = MLSignalGenerator(self.history_tracker)
            # Pass bot instance to ML generator for accessing fixed cashout multiplier
            self.ml_generator.bot_instance = self
            
            # Initialize pattern predictor and notifier
            from pattern_predictor import PatternPredictor
            from mobile_notifier import MobileNotifier
            self.pattern_predictor = PatternPredictor(self.history_tracker)
            self.mobile_notifier = MobileNotifier()
            # Setup Discord webhook
            self.mobile_notifier.setup_discord("https://discord.com/api/webhooks/1439324526881144852/mcT-Za8lqaZuqooFjY-ppz3ixyRnYFt010iExTm-4E6aWajHWiuHEQ9tJSe1XZO39OEI")
            
            # Initialize seasonal analyzer
            from seasonal_analyzer import SeasonalAnalyzer
            self.seasonal_analyzer = SeasonalAnalyzer(self.history_tracker)
        
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
        """Strict verification that game is actually running using multiplier reader."""
        if self.multiplier_reader:
            try:
                current_mult = self.multiplier_reader.read_current_multiplier()
                if current_mult and current_mult >= 1.0:
                    return True
                # Check if it's awaiting state
                crashed = self.multiplier_reader.has_crashed()
                if crashed is True:
                    return False
            except Exception as e:
                # On error, fallback to detector
                pass
        
        # Fallback to old detector if multiplier reader fails
        if self.detector:
            state = self.detector.read_text_in_region()
            if state == 'FLYING' or (state and 'x' in str(state).lower() and state not in ['AWAITING', 'FLEW AWAY']):
                return True
        
        return False
    
    def _wait_for_game_start_strict(self, timeout=15):
        """Wait for game to start with strict verification using multiplier reader."""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                if self.multiplier_reader:
                    # Check if game has started (multiplier >= 1.0)
                    current_mult = self.multiplier_reader.read_current_multiplier()
                    if current_mult and current_mult >= 1.0:
                        return True
                    
                    # If still in awaiting state after 3 seconds, likely won't start
                    crashed = self.multiplier_reader.has_crashed()
                    if crashed is True and time.time() - start_time > 3:
                        return False
            except Exception as e:
                # On error, wait a bit and retry
                time.sleep(0.2)
                continue
            
            time.sleep(0.1)
        
        return False
    
    def _wait_for_awaiting_state(self, timeout=60):
        """Wait for AWAITING state using multiplier reader with fallback."""
        start_time = time.time()
        consecutive_awaiting = 0
        
        while time.time() - start_time < timeout:
            try:
                if self.multiplier_reader:
                    crashed = self.multiplier_reader.has_crashed()
                    if crashed is True:
                        consecutive_awaiting += 1
                        # Need 2 consecutive confirmations to be sure
                        if consecutive_awaiting >= 2:
                            return True
                        time.sleep(0.2)
                    elif crashed is False:
                        consecutive_awaiting = 0
                        time.sleep(0.2)
                    else:
                        # Cannot determine, fallback to detector
                        if self.detector:
                            state = self.detector.read_text_in_region()
                            if state == 'AWAITING' or self.detector.is_awaiting_next_flight():
                                consecutive_awaiting += 1
                                if consecutive_awaiting >= 2:
                                    return True
                        time.sleep(0.3)
                else:
                    # No multiplier reader, use detector
                    if self.detector:
                        state = self.detector.read_text_in_region()
                        if state == 'AWAITING' or self.detector.is_awaiting_next_flight():
                            consecutive_awaiting += 1
                            if consecutive_awaiting >= 2:
                                return True
                    time.sleep(0.3)
            except Exception as e:
                # On error, wait and retry
                time.sleep(0.5)
                continue
        
        return False
    
    def _wait_for_crash_and_read_multiplier(self, timeout=60):
        """Wait for round to crash and read the final multiplier."""
        start_time = time.time()

        while time.time() - start_time < timeout:
            if self.detector.has_game_crashed() or self.detector.is_awaiting_next_flight():
                time.sleep(0.3)

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
    
    def _wait_for_multiplier_and_cashout(self, target_multiplier, round_number, signal, stake_used):
        """
        Wait for target multiplier and execute cashout using REAL multiplier values.
        
        Args:
            target_multiplier: Target multiplier to cashout at
            round_number: Current round number
            signal: ML signal data
            stake_used: Stake amount used
            
        Returns:
            tuple: (success, profit, final_multiplier, result_type)
        """
        print(f"\n  [TIMER]  WAITING FOR TARGET: {target_multiplier:.2f}x")
        print("  " + "-"*90)
        
        round_start = time.time()
        cashout_triggered = False
        last_displayed_mult = None
        
        while True:
            try:
                # Read current multiplier
                current_mult = self.multiplier_reader.read_current_multiplier()
                
                # Display progress
                if current_mult and current_mult != last_displayed_mult:
                    elapsed = time.time() - round_start
                    remaining = target_multiplier - current_mult
                    
                    if remaining > 0.5:
                        color = '[GREEN]'
                        status = 'SAFE'
                    elif remaining > 0.2:
                        color = '[YELLOW]'
                        status = 'READY'
                    elif remaining > 0.05:
                        color = '[ORANGE]'
                        status = 'ALERT'
                    else:
                        color = '[RED]'
                        status = 'NOW!'
                    
                    print(f"  {color} Current: {current_mult:.2f}x | Target: {target_multiplier:.2f}x | {status:5s}", 
                          end='\r', flush=True)
                    last_displayed_mult = current_mult
                
                # Check for crash
                crashed = self.multiplier_reader.has_crashed()
                if crashed is True:
                    print("\n")
                    elapsed = time.time() - round_start
                    final_mult = self.multiplier_reader.last_valid_multiplier or 0
                    
                    print(f"  [CRASH] CRASHED at {final_mult:.2f}x (target: {target_multiplier:.2f}x)")
                    
                    self.stats["failed_cashouts"] += 1
                    self.stats["current_streak"] = 0
                    
                    loss = -stake_used
                    
                    # Wait a bit to ensure multiplier is readable
                    time.sleep(0.3)
                    success, crash_mult = self._wait_for_crash_and_read_multiplier(timeout=3)
                    if success and crash_mult:
                        final_mult = crash_mult
                    
                    return False, loss, final_mult, "CRASH"
                
                # Check if we've reached target
                if current_mult and current_mult >= target_multiplier and not cashout_triggered:
                    cashout_triggered = True
                    actual_elapsed = time.time() - round_start
                    
                    print("\n")
                    print(f"  [MONEY] TARGET REACHED: {current_mult:.2f}x - EXECUTING CASHOUT...")
                    
                    time.sleep(0.05)
                    
                    # Final crash check before cashout
                    crashed = self.multiplier_reader.has_crashed()
                    if crashed is True:
                        print(f"  [CRASH] Crashed during cashout attempt!")
                        
                        self.stats["failed_cashouts"] += 1
                        self.stats["current_streak"] = 0
                        
                        loss = -stake_used
                        final_mult = self.multiplier_reader.last_valid_multiplier or 0
                        
                        return False, loss, final_mult, "CRASH"
                    
                    # Execute cashout
                    cashout_success, cashout_reason = cashout_verified(
                        self.config_manager.cashout_coords,
                        self.detector
                    )
                    
                    if cashout_success:
                        print("  [OK] Cashout command sent!")
                        
                        # Wait for balance to update
                        print("  [WAIT] Validating balance change...")
                        time.sleep(0.5)
                        new_balance = self._read_balance()
                        
                        # Validate win by checking balance
                        if self.last_balance is not None and new_balance is not None:
                            balance_change = new_balance - self.last_balance
                            
                            if balance_change > 0:
                                print(f"  [OK] Balance validation: WIN confirmed (+{balance_change:.2f})")
                                
                                self.stats["successful_cashouts"] += 1
                                self.stats["current_streak"] += 1
                                
                                profit = balance_change
                                returns = stake_used + profit
                                self.stats["total_return"] += returns
                                self.last_balance = new_balance
                                
                                return True, profit, current_mult, "WIN"
                            else:
                                print(f"  [X] Balance validation: LOST (balance change: {balance_change:.2f})")
                                
                                self.stats["failed_cashouts"] += 1
                                self.stats["current_streak"] = 0
                                
                                loss = -stake_used
                                final_mult = self.multiplier_reader.last_valid_multiplier or current_mult
                                self.last_balance = new_balance
                                
                                return False, loss, final_mult, "CRASH"
                        else:
                            # Could not validate balance - assume win based on multiplier
                            print("  [WARNING]  Could not validate balance - using estimated profit")
                            
                            self.stats["successful_cashouts"] += 1
                            self.stats["current_streak"] += 1
                            
                            returns = stake_used * current_mult
                            profit = returns - stake_used
                            self.stats["total_return"] += returns
                            
                            if new_balance:
                                self.last_balance = new_balance
                            
                            return True, profit, current_mult, "WIN"
                    else:
                        print(f"  [X] Cashout failed: {cashout_reason}")
                        
                        time.sleep(0.2)
                        crashed = self.multiplier_reader.has_crashed()
                        if crashed is True or cashout_reason == "NO_ACTIVE_BET":
                            self.stats["failed_cashouts"] += 1
                            self.stats["current_streak"] = 0
                            
                            loss = -stake_used
                            final_mult = self.multiplier_reader.last_valid_multiplier or 0
                            
                            return False, loss, final_mult, "CRASH"
                
                time.sleep(0.03)  # Check every 30ms for responsiveness
                
            except Exception as e:
                # On error, check if crashed using detector as fallback
                if self.detector and self.detector.has_game_crashed():
                    print("\n")
                    print(f"  [CRASH] Detected crash (via fallback detector)")
                    
                    self.stats["failed_cashouts"] += 1
                    self.stats["current_streak"] = 0
                    
                    loss = -stake_used
                    final_mult = self.multiplier_reader.last_valid_multiplier or 0
                    
                    return False, loss, final_mult, "CRASH"
                
                # Otherwise wait a bit and retry
                time.sleep(0.05)
                continue
    
    def _show_detailed_model_analysis(self, signal):
        """Display detailed model analysis."""
        strategy = signal.get('strategy', 'unknown')
        print(f"\n  [STATS] STRATEGY: {strategy.upper()}")
        print("  " + "-"*90)

        if 'position1' in strategy or 'position2' in strategy:
            if 'position1' in strategy:
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

                bar_length = 30
                filled = int((green_prob / 100) * bar_length)
                bar = "#" * filled + "-" * (bar_length - filled)
                print(f"\n  Success Probability: [{bar}] {green_prob:.1f}%")

                print(f"\n  [IDEA] REASONING:")
                print(f"     ML classifier detected {green_prob:.1f}% probability of hitting {target:.2f}x")
                print(f"     based on recent pattern analysis.")

            elif 'position2' in strategy:
                print("\n  [DICE] POSITION 2: Rule-Based Pattern Detection")

                if 'cold_streak' in strategy:
                    cold_streak_len = signal.get('cold_streak_length', 0)
                    target = signal.get('target_multiplier', 0)
                    confidence = signal.get('confidence', 0)

                    recent_rounds = self.history_tracker.get_recent_rounds(10)
                    if not recent_rounds.empty and 'multiplier' in recent_rounds.columns:
                        recent_mults = recent_rounds['multiplier'].values[-10:]
                        low_count = sum(1 for m in recent_mults if m < 2.0)
                        high_count = sum(1 for m in recent_mults if m >= 3.0)

                        print("\n  +--------------------------+------------+")
                        print("  | METRIC                   | VALUE      |")
                        print("  +--------------------------+------------+")
                        print(f"  | Pattern Detected         | COLD STREAK|")
                        print(f"  | Low Rounds (<2x)         | {low_count:2d}/10      |")
                        print(f"  | High Rounds (≥3x)        | {high_count:2d}/10      |")
                        print(f"  | Target Multiplier        | {target:6.2f}x    |")
                        print(f"  | Confidence Level         | {confidence:6.1f}%    |")
                        print("  +--------------------------+------------+")

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

        elif 'regression' in strategy and signal.get('models'):
            print("\n  [LAB] REGRESSION ENSEMBLE: Individual Model Predictions")
            predictions = signal['models']

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

            ensemble_pred = signal.get('prediction', 0)
            ensemble_conf = signal.get('confidence', 0)
            print(f"  | ENSEMBLE                 | {ensemble_pred:6.2f}x |  {ensemble_conf:6.1f}%   |")
            print("  +--------------------------+----------+------------+")

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
    
    def _log_round_header(self, round_num):
        """Print round header."""
        print(f"\n{'='*100}")
        print(f"[TARGET] ROUND #{round_num:03d}")
        print(f"{'='*100}")
    
    def _log_decision(self, action, signal, stake=0):
        """Log betting decision with details."""
        if action == "BET":
            print(f"\n  [OK] DECISION: PLACE BET")
            print(f"  [MONEY] Stake: {stake}")
            
            if self.hot_run_mode:
                print(f"  [TARGET] Target Multiplier: {self.target_cashout_multiplier:.2f}x")
            else:
                print(f"  [TARGET] Target: {self.config_manager.cashout_delay}s (~{estimate_multiplier(self.config_manager.cashout_delay):.2f}x)")
            
            print(f"  [STATS] Ensemble Confidence: {signal['confidence']:.1f}%")
            self._show_detailed_model_analysis(signal)
        elif action == "SKIP":
            print(f"\n  [SKIP]  DECISION: SKIP ROUND")
            print(f"  [X] Reason: {signal['reason']}")
            print(f"  [STATS] Ensemble Confidence: {signal['confidence']:.1f}% (Threshold: {self.ml_generator.confidence_threshold}%)")
            self._show_detailed_model_analysis(signal)
    
    def _log_round_result(self, round_num, action, stake, result, profit, mult, signal, balance, cumulative):
        """Log round result."""
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

    def run_hot_run_mode(self):
        """
        HOT RUN MODE - Quick start with existing config, uses real multiplier for cashout.
        ALL BETS ARE PLACED - No ML filtering, pure aggressive betting.
        """
        print("\n" + "="*100)
        print("[ROCKET] AVIATOR BOT - HOT RUN MODE (AGGRESSIVE - ALL BETS)")
        print("="*100)
        print("[FIRE] Using existing configuration and stake values")
        print("[TARGET] Cashout based on REAL multiplier values")
        print("[WARNING] ALL rounds will be bet on (no ML filtering)")
        print("="*100)

        # Set hot run flag
        self.hot_run_mode = True

        cumulative_profit = 0
        round_number = 0
        history_read_for_round = False

        try:
            while True:
                round_number += 1
                self._log_round_header(round_number)

                # STEP 1: Wait for AWAITING state using multiplier reader
                flush_print("  [WAIT] Waiting for AWAITING state...")
                if not self._wait_for_awaiting_state(timeout=60):
                    flush_print("  [WARNING]  Timeout - retrying...")
                    continue

                flush_print("  [OK] AWAITING confirmed (via multiplier reader)")
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

                    self.current_stake = reset_stake(self.config_manager.initial_stake, self.stats)
                    self._reset_bet_state()
                    history_read_for_round = False
                    continue

                # STEP 3: Read previous round multiplier
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

                # STEP 4: Generate ML signal (for target multiplier only, not for filtering)
                print("\n  [ML] Getting target multiplier from ML models...")
                signal = self.ml_generator.generate_ensemble_signal()

                # Use signal's target multiplier if available, otherwise use default
                if 'target_multiplier' in signal:
                    self.target_cashout_multiplier = signal['target_multiplier']
                else:
                    self.target_cashout_multiplier = max(signal.get('prediction', 2.0), 1.5)

                # ALWAYS BET IN HOT RUN MODE
                stake_used = self.current_stake

                print(f"\n  [FIRE] HOT RUN: PLACING BET (no filtering)")
                print(f"  [MONEY] Stake: {stake_used}")
                print(f"  [TARGET] Target Multiplier: {self.target_cashout_multiplier:.2f}x")
                print(f"  [STATS] ML Prediction: {signal.get('prediction', 0):.2f}x (Confidence: {signal.get('confidence', 0):.1f}%)")

                # Show model analysis (informational only)
                self._show_detailed_model_analysis(signal)

                # Pre-bet checks using multiplier reader
                if self._verify_game_running_strict():
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

                # Wait for game start using multiplier reader
                print("\n  [WAIT] Waiting for game start (monitoring multiplier)...")
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

                    self.current_stake = reset_stake(self.config_manager.initial_stake, self.stats)
                    self._reset_bet_state()
                    self.stats["rounds_observed"] += 1
                    history_read_for_round = False
                    continue

                print("  [ROCKET] Game started! (multiplier detected)")

                # Reset multiplier reader for new flight
                self.multiplier_reader.reset()

                # WAIT FOR TARGET MULTIPLIER AND CASHOUT
                success, profit, final_mult, result_type = self._wait_for_multiplier_and_cashout(
                    self.target_cashout_multiplier,
                    round_number,
                    signal,
                    stake_used
                )

                cumulative_profit += profit

                # Update balance if we won
                if success and self.last_balance:
                    new_balance = self.last_balance + profit
                    self.last_balance = new_balance

                self._log_round_result(round_number, "BET", stake_used, result_type,
                                      profit, final_mult, signal, self.last_balance, cumulative_profit)

                # Log to history
                self.history_tracker.log_round(
                    multiplier=final_mult,
                    bet_placed=True,
                    stake=stake_used,
                    cashout_time=0,  # Not time-based anymore
                    profit_loss=profit,
                    prediction=signal['prediction'],
                    confidence=signal['confidence'],
                    pred_range=(0, 0)
                )

                round_data = self._create_round_data(final_mult, True, stake_used, 0, profit,
                                                     signal, cumulative_profit, self.last_balance)
                self._emit_dashboard_update(round_data)

                # Update stake based on result
                if success:
                    self.current_stake = increase_stake(
                        self.current_stake,
                        self.config_manager.stake_increase_percent,
                        self.config_manager.max_stake,
                        self.stats
                    )
                else:
                    self.current_stake = reset_stake(self.config_manager.initial_stake, self.stats)

                self._reset_bet_state()
                history_read_for_round = False

                self.ml_generator.log_highest_multipliers()
                
                # Check for high multiplier sequence prediction
                if self.stats["rounds_observed"] % 5 == 0:  # Check every 5 rounds
                    prediction = self.pattern_predictor.predict_high_sequence()
                    if prediction['prediction'] and prediction['confidence'] >= 70:
                        current_time = time.time()
                        if current_time - self.pattern_predictor.last_notification > self.pattern_predictor.notification_cooldown:
                            self.mobile_notifier.notify_high_sequence_prediction(prediction)
                            # Start tracking this prediction for validation
                            self.pattern_predictor.start_prediction_tracking(prediction)
                            self.pattern_predictor.last_notification = current_time
                            print(f"📱 HIGH SEQUENCE ALERT: {prediction['confidence']}% confidence")
                
                # Validate active predictions with current multiplier
                if hasattr(self, 'pattern_predictor'):
                    self.pattern_predictor.validate_predictions(final_mult)
                    
                    # Send validation results if any completed
                    for result in self.pattern_predictor.validation_results[-5:]:  # Check last 5 results
                        if not hasattr(result, 'sent'):
                            self.mobile_notifier.send_validation_result(result)
                            result['sent'] = True  # Mark as sent
                
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

    def run_observation_mode(self):
        """Observation mode - collect data without placing bets (clipboard/OCR)."""
        print("\n" + "="*100)
        print("[STATS] AVIATOR BOT - OBSERVATION MODE (DATA COLLECTION)")
        print("="*100)
        print("[SCAN] Bot will observe rounds and collect data without placing bets.")
        print("[SAVE] Data will be saved to aviator_rounds_history.csv for model training.")
        print("[SCAN] Round detection and history logging use clipboard/OCR.")
        print("="*100)

        round_number = 0
        history_read_for_round = False

        try:
            while True:
                round_number += 1
                self._log_round_header(round_number)

                flush_print("  [WAIT] Waiting for AWAITING state (via clipboard/OCR)...")
                if not self.detector.wait_for_clean_awaiting_state(timeout=60):
                    flush_print("  [WARNING]  Timeout - retrying...")
                    continue

                flush_print("  [OK] AWAITING confirmed")
                time.sleep(0.3)

                if not history_read_for_round:
                    flush_print("  [LOG] Checking for previous round (via clipboard/OCR)...")

                    success, logged_mult = self.history_tracker.auto_log_from_clipboard(
                        self.detector,
                        force=False
                    )

                    if success and logged_mult and logged_mult != self.last_logged_mult:
                        self.last_logged_mult = logged_mult

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

                print("\n  [ML] Generating predictions (no bet will be placed)...")
                signal = self.ml_generator.generate_ensemble_signal()

                print(f"\n  [STATS] OBSERVATION ONLY - No bet placed")
                print(f"  [TARGET] Model would predict: {signal['prediction']:.2f}x")
                print(f"  [CHART] Confidence: {signal['confidence']:.1f}%")
                print(f"  [DICE] Decision would be: {'BET' if signal['should_bet'] else 'SKIP'}")

                print("\n  [WAIT] Waiting for current round to complete (via clipboard/OCR)...")
                success, observed_mult = self._wait_for_crash_and_read_multiplier(timeout=60)

                if success and observed_mult:
                    print(f"  [OK] Round complete: {observed_mult:.2f}x")
                    self.stats["rounds_observed"] += 1
                    # Log to history
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
                else:
                    print("  [WARNING]  Could not read round result via clipboard/OCR.")
                    self.stats["rounds_observed"] += 1 # Still count as observed

                self.ml_generator.log_highest_multipliers()
                history_read_for_round = False

                if round_number % 10 == 0:
                    print(f"\n  [CHART] Progress: {self.stats['rounds_observed']} rounds collected")
                    print(f"  [SAVE] Data saved to: aviator_rounds_history.csv")

                time.sleep(0.5)

        except KeyboardInterrupt:
            print("\n\n[STOP]  Observation stopped by user")
            print(f"\n[STATS] Total rounds observed: {self.stats['rounds_observed']}")
            print(f"[SAVE] Data saved to: aviator_rounds_history.csv")
        except Exception as e:
            print(f"\n\n[X] Error: {e}")
            import traceback
            traceback.print_exc()
            # self.print_stats() # No stats for observation mode

    def run_dry_run_mode(self):
        """DRY RUN MODE - Simulates betting without placing real bets (clipboard/OCR)."""
        print("\n" + "="*100)
        print("[LOG] AVIATOR BOT - DRY RUN MODE (SIMULATION)")
        print("="*100)
        print("[SCAN] Bot will simulate all betting decisions WITHOUT placing real bets.")
        print("[IDEA] All ML predictions, stake management, and outcomes will be logged.")
        print("[STATS] Hypothetical profit/loss will be tracked based on actual multipliers.")
        print("[SCAN] Round detection and history logging use clipboard/OCR.")
        print("="*100)

        cumulative_profit = 0
        hypothetical_balance = 1000.0
        round_number = 0
        history_read_for_round = False

        try:
            while True:
                round_number += 1
                self._log_round_header(round_number)

                flush_print("  [WAIT] Waiting for AWAITING state (via clipboard/OCR)...")
                if not self.detector.wait_for_clean_awaiting_state(timeout=60):
                    flush_print("  [WARNING]  Timeout - retrying...")
                    continue

                flush_print("  [OK] AWAITING confirmed")
                time.sleep(0.3)

                if not history_read_for_round:
                    flush_print("  [LOG] Checking for previous round (via clipboard/OCR)...")

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

                print("\n  [ML] Analyzing patterns (DRY RUN - no bet will be placed)...")
                signal = self.ml_generator.generate_ensemble_signal()

                if signal['should_bet']:
                    stake_used = self.current_stake

                    print(f"\n  [LOG] SIMULATED DECISION: WOULD PLACE BET")
                    print(f"  [MONEY] Simulated Stake: {stake_used}")
                    
                    if 'target_multiplier' in signal:
                        target_mult = signal['target_multiplier']
                        print(f"  [TARGET] Target Multiplier: {target_mult:.2f}x")
                    else:
                        target_mult = estimate_multiplier(self.config_manager.cashout_delay)
                        print(f"  [TARGET] Target: {self.config_manager.cashout_delay}s (~{target_mult:.2f}x)")
                    
                    print(f"  [STATS] Ensemble Confidence: {signal['confidence']:.1f}%")

                    self._show_detailed_model_analysis(signal)

                    print("\n  [WAIT] Waiting for round to complete to calculate hypothetical outcome (via clipboard/OCR)...")
                    success, observed_mult = self._wait_for_crash_and_read_multiplier(timeout=60)

                    if not success:
                        observed_mult = 2.0

                    if observed_mult >= target_mult:
                        hypothetical_return = stake_used * target_mult
                        hypothetical_profit = hypothetical_return - stake_used
                        cumulative_profit += hypothetical_profit
                        hypothetical_balance += hypothetical_profit

                        self.stats["successful_cashouts"] += 1
                        self.stats["ml_bets_placed"] += 1
                        self.stats["total_bet"] += stake_used
                        self.stats["total_return"] += hypothetical_return
                        self.stats["current_streak"] += 1

                        print(f"\n  [OK] SIMULATED RESULT: WIN")
                        print(f"  [MULT] Actual: {observed_mult:.2f}x | Target: {target_mult:.2f}x")
                        print(f"  [MONEY] Hypothetical P/L: +{hypothetical_profit:.2f}")
                        print(f"  [BAL] Hypothetical Balance: {hypothetical_balance:.2f}")
                        print(f"  [STATS] Cumulative P/L: {cumulative_profit:+.2f}")
                        print(f"{'-'*100}")

                        self.current_stake = increase_stake(
                            self.current_stake,
                            self.config_manager.stake_increase_percent,
                            self.config_manager.max_stake,
                            self.stats
                        )
                    else:
                        hypothetical_loss = -stake_used
                        cumulative_profit += hypothetical_loss
                        hypothetical_balance += hypothetical_loss

                        self.stats["failed_cashouts"] += 1
                        self.stats["ml_bets_placed"] += 1
                        self.stats["total_bet"] += stake_used
                        self.stats["current_streak"] = 0

                        print(f"\n  [CRASH] SIMULATED RESULT: LOSS")
                        print(f"  [MULT] Actual: {observed_mult:.2f}x | Target: {target_mult:.2f}x")
                        print(f"  [MONEY] Hypothetical P/L: {hypothetical_loss:.2f}")
                        print(f"  [BAL] Hypothetical Balance: {hypothetical_balance:.2f}")
                        print(f"  [STATS] Cumulative P/L: {cumulative_profit:+.2f}")
                        print(f"{'-'*100}")

                        self.current_stake = reset_stake(self.config_manager.initial_stake, self.stats)

                    # Log to history for dry run
                    self.history_tracker.log_round(
                        multiplier=observed_mult,
                        bet_placed=True, # Simulated bet
                        stake=stake_used,
                        cashout_time=0, # Not time-based anymore
                        profit_loss=hypothetical_profit,
                        prediction=signal['prediction'],
                        confidence=signal['confidence'],
                        pred_range=(0, 0)
                    )
                    round_data = self._create_round_data(observed_mult, True, stake_used, 0, hypothetical_profit,
                                                         signal, cumulative_profit, hypothetical_balance)
                    self._emit_dashboard_update(round_data)

                else:
                    print(f"\n  [SKIP]  SIMULATED DECISION: WOULD SKIP")
                    print(f"  [X] Reason: {signal['reason']}")

                    self._show_detailed_model_analysis(signal)

                    self.stats["ml_skipped"] += 1

                    print("\n  [WAIT] Waiting for round to complete (via clipboard/OCR)...")
                    success, observed_mult = self._wait_for_crash_and_read_multiplier(timeout=60)

                    if not success:
                        observed_mult = 2.0

                    print(f"\n  [SKIP]  SIMULATED RESULT: SKIPPED")
                    print(f"  [MULT] Observed: {observed_mult:.2f}x")
                    print(f"  [STATS] Cumulative P/L: {cumulative_profit:+.2f}")
                    print(f"{'-'*100}")
                    
                    # Log to history for dry run
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
                                                         signal, cumulative_profit, hypothetical_balance)
                    self._emit_dashboard_update(round_data)


                self.ml_generator.log_highest_multipliers()
                history_read_for_round = False
                self.stats["rounds_observed"] += 1

                if round_number % 10 == 0:
                    print(f"\n  [CHART] DRY RUN SUMMARY:")
                    print(f"  [MONEY] Hypothetical Balance: {hypothetical_balance:.2f}")
                    print(f"  [STATS] Cumulative P/L: {cumulative_profit:+.2f}")

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

        if self.stats['ml_bets_placed'] > 0:
            success_rate = (self.stats['successful_cashouts'] / self.stats['ml_bets_placed']) * 100
            print(f"Win rate:              {success_rate:.1f}%")

        print(f"\n[MONEY] Hypothetical Financial:")
        print(f"  Profit/Loss:         {cumulative_profit:+.2f}")
        print(f"  Final balance:       {hypothetical_balance:.2f}")
        print("="*100 + "\n")

    def run_ml_mode(self):
        """Main betting loop - STANDARD MODE with time-based cashout (clipboard/OCR)."""
        print("\n" + "="*100)
        print("[PLANE]  AVIATOR BOT - STANDARD ML MODE")
        print("="*100)
        print(f"[TIMER]  Cashout based on TIME delay: {self.config_manager.cashout_delay}s")
        print("[SCAN] Round detection and history logging use clipboard/OCR.")
        print("="*100)
        
        cumulative_profit = 0
        round_number = 0
        history_read_for_round = False

        try:
            while True:
                round_number += 1
                self._log_round_header(round_number)
                
                flush_print("  [WAIT] Waiting for AWAITING state (via clipboard/OCR)...")
                if not self.detector.wait_for_clean_awaiting_state(timeout=60):
                    flush_print("  [WARNING]  Timeout - retrying...")
                    continue
                
                flush_print("  [OK] AWAITING confirmed")
                time.sleep(0.3)
                
                if self._check_existing_bet():
                    flush_print("  [CANCEL] Orphaned bet detected!")
                    self.stats["cancelled_bets"] += 1
                    self.stats["failed_cashouts"] += 1
                    
                    loss = -self.current_stake
                    cumulative_profit += loss
                    
                    self._log_round_result(round_number, "BET", self.current_stake, "CANCEL", 
                                          loss, 0, None, self.last_balance, cumulative_profit)
                    
                    self.current_stake = reset_stake(self.config_manager.initial_stake, self.stats)
                    self._reset_bet_state()
                    history_read_for_round = False
                    continue
                
                if not history_read_for_round:
                    flush_print("  [LOG] Checking for previous round (via clipboard/OCR)...")

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

                print("\n  [ML] Analyzing patterns...")
                signal = self.ml_generator.generate_ensemble_signal()
                
                # Get seasonal context and boost confidence if favorable
                seasonal_data = self.seasonal_analyzer.get_seasonal_recommendation()
                if seasonal_data['confidence_boost'] > 0:
                    signal['confidence'] = min(95, signal['confidence'] + seasonal_data['confidence_boost'])
                    print(f"  [SEASON] Seasonal boost: +{seasonal_data['confidence_boost']}% confidence")
                    for rec in seasonal_data['recommendations']:
                        print(f"  [SEASON] {rec}")
                
                if signal['should_bet']:
                    stake_used = self.current_stake
                    self._log_decision("BET", signal, stake_used)
                    
                    # Pre-bet checks using detector (clipboard/OCR)
                    if self.detector.is_game_flying():
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

                    # Wait for game start (using detector)
                    print("\n  [WAIT] Waiting for game start (monitoring detector)...")
                    game_started = self.detector.wait_for_game_start(timeout=15)

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

                        self.current_stake = reset_stake(self.config_manager.initial_stake, self.stats)
                        self._reset_bet_state()
                        self.stats["rounds_observed"] += 1
                        history_read_for_round = False
                        continue

                    print("  [ROCKET] Game started! (detector confirmed)")

                    # Execute time-based cashout
                    print(f"\n  [TIMER] Waiting {self.config_manager.cashout_delay}s for cashout...")
                    time.sleep(self.config_manager.cashout_delay)

                    # Attempt cashout
                    cashout_success, cashout_reason = cashout_verified(
                        self.config_manager.cashout_coords,
                        self.detector
                    )

                    profit = 0
                    final_mult = 0
                    result_type = "CRASH" # Assume crash until proven win

                    if cashout_success:
                        print("  [OK] Cashout command sent!")
                        # Wait for balance to update
                        print("  [WAIT] Validating balance change...")
                        time.sleep(0.5)
                        new_balance = self._read_balance()
                        
                        if self.last_balance is not None and new_balance is not None:
                            balance_change = new_balance - self.last_balance
                            if balance_change > 0:
                                print(f"  [OK] Balance validation: WIN confirmed (+{balance_change:.2f})")
                                self.stats["successful_cashouts"] += 1
                                self.stats["current_streak"] += 1
                                profit = balance_change
                                result_type = "WIN"
                                self.last_balance = new_balance
                            else:
                                print(f"  [X] Balance validation: LOST (balance change: {balance_change:.2f})")
                                self.stats["failed_cashouts"] += 1
                                self.stats["current_streak"] = 0
                                profit = -stake_used
                                self.last_balance = new_balance
                        else:
                            print("  [WARNING]  Could not validate balance - assuming win based on cashout success")
                            self.stats["successful_cashouts"] += 1
                            self.stats["current_streak"] += 1
                            # Estimate profit if balance not readable
                            profit = stake_used * estimate_multiplier(self.config_manager.cashout_delay) - stake_used
                            result_type = "WIN"
                            if new_balance:
                                self.last_balance = new_balance
                    else:
                        print(f"  [X] Cashout failed: {cashout_reason}")
                        self.stats["failed_cashouts"] += 1
                        self.stats["current_streak"] = 0
                        profit = -stake_used
                    
                    # Wait for round to crash and read final multiplier for logging
                    success_read, crash_mult = self._wait_for_crash_and_read_multiplier(timeout=10)
                    if success_read and crash_mult:
                        final_mult = crash_mult
                    else:
                        print("  [WARNING] Could not read final crash multiplier via clipboard/OCR.")
                        final_mult = 0 # Default if cannot read

                    cumulative_profit += profit

                    self._log_round_result(round_number, "BET", stake_used, result_type,
                                          profit, final_mult, signal, self.last_balance, cumulative_profit)

                    # Log to history
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

                    round_data = self._create_round_data(final_mult, True, stake_used, self.config_manager.cashout_delay, profit,
                                                         signal, cumulative_profit, self.last_balance)
                    self._emit_dashboard_update(round_data)

                    # Update stake based on result
                    if result_type == "WIN":
                        self.current_stake = increase_stake(
                            self.current_stake,
                            self.config_manager.stake_increase_percent,
                            self.config_manager.max_stake,
                            self.stats
                        )
                    else:
                        self.current_stake = reset_stake(self.config_manager.initial_stake, self.stats)

                    self._reset_bet_state()
                    history_read_for_round = False
                    self.ml_generator.log_highest_multipliers()
                    self.stats["rounds_observed"] += 1

                    if self.dashboard:
                        self.dashboard.emit_stats_update()
                    
                else: # Should skip
                    self._log_decision("SKIP", signal)
                    self.stats["ml_skipped"] += 1

                    # Still need to observe the round to log history
                    print("\n  [WAIT] Waiting for round to complete (via clipboard/OCR)...")
                    success_read, observed_mult = self._wait_for_crash_and_read_multiplier(timeout=60)

                    if success_read and observed_mult:
                        print(f"  [OK] Round complete: {observed_mult:.2f}x")
                        self.stats["rounds_observed"] += 1
                        # Log to history even if skipped
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
                    else:
                        print("  [WARNING]  Could not read round result via clipboard/OCR.")
                        self.stats["rounds_observed"] += 1 # Still count as observed

                    self.ml_generator.log_highest_multipliers()
                    history_read_for_round = False
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

    def run_diagnostic_mode(self):
        """Diagnostic mode to test clipboard/OCR multiplier reading."""
        print("\n" + "="*100)
        print("[WRENCH] DIAGNOSTIC MODE - Testing Clipboard/OCR Multiplier Reading")
        print("="*100)
        
        if not self.detector:
            print("[X] GameStateDetector not initialized!")
            return
        
        print(f"[INFO] Multiplier region: {self.config_manager.multiplier_region}")
        print(f"[INFO] Testing clipboard/OCR for multiplier and state detection...")
        print("\nPress Ctrl+C to stop\n")
        
        test_count = 0
        success_count = 0
        error_count = 0
        
        try:
            while True:
                test_count += 1
                
                try:
                    # Use detector to read state and multiplier
                    state = self.detector.read_text_in_region()
                    
                    if state == 'AWAITING':
                        success_count += 1
                        print(f"[{test_count:03d}] [OK] State: AWAITING NEXT FLIGHT")
                    elif self.detector.is_game_flying():
                        # Try to read multiplier if game is flying
                        success_read, current_mult = self.history_tracker.auto_log_from_clipboard(
                            self.detector,
                            force=False # Don't force log, just read
                        )
                        if success_read and current_mult:
                            success_count += 1
                            print(f"[{test_count:03d}] [OK] Multiplier: {current_mult:.2f}x")
                        else:
                            # If game is flying but couldn't read multiplier, it's an error for diagnostic
                            error_count += 1
                            print(f"[{test_count:03d}] [X] State: FLYING, but could not read multiplier")
                    else:
                        error_count += 1
                        print(f"[{test_count:03d}] [X] Cannot determine state (Raw: {state})")
                
                except Exception as e:
                    error_count += 1
                    print(f"[{test_count:03d}] [X] Error: {e}")
                
                # Show stats every 10 tests
                if test_count % 10 == 0:
                    success_rate = (success_count / test_count) * 100
                    print(f"\n[STATS] Success: {success_count}/{test_count} ({success_rate:.1f}%)")
                    print(f"[STATS] Errors: {error_count}/{test_count}\n")
                
                time.sleep(0.5)
                
        except KeyboardInterrupt:
            print("\n\n[STOP] Diagnostic stopped")
            success_rate = (success_count / test_count) * 100 if test_count > 0 else 0
            print(f"\n[STATS] Final Results:")
            print(f"  Total tests: {test_count}")
            print(f"  Successful: {success_count} ({success_rate:.1f}%)")
            print(f"  Errors: {error_count}")
            
            if error_count > test_count * 0.3:  # More than 30% errors
                print(f"\n[WARNING] High error rate detected!")
                print(f"[TIP] Possible issues:")
                print(f"  - Game window is minimized or not visible")
                print(f"  - Region coordinates are incorrect")
                print(f"  - Screen resolution changed")
                print(f"  - Tesseract OCR not configured properly")
                print(f"\n[TIP] Run setup again to reconfigure regions")
            elif success_rate > 80:
                print(f"\n[OK] Clipboard/OCR reading is working well!")
            else:
                print(f"\n[WARNING] Success rate is low - check game window visibility")
        # No need for print_stats here, as it's a diagnostic mode.
        # The diagnostic output above is sufficient.


def main():
    """
    Main entry point.
    
    TROUBLESHOOTING MSS ERRORS:
    
    1. gdi32.GetDIBits() failed:
       - Game window is minimized or not visible
       - Region coordinates are outside screen bounds
       - Screen resolution changed since setup
       → Solution: Run DIAGNOSTIC MODE (option 5) to test
       → Solution: Run setup again (option 2) to reconfigure
    
    2. Cannot capture multiplier region:
       - Game window is minimized
       - Game window moved to different position
       - Wrong monitor selected
       → Solution: Make sure game window is visible
       → Solution: Run setup again to reconfigure regions
    
    3. High error rate in diagnostic mode:
       - Tesseract OCR not configured
       - Wrong region selected during setup
       - Game graphics settings changed
       → Solution: Install/configure Tesseract OCR
       → Solution: Run setup again with correct multiplier region
    
    OPERATING MODES:
    
    1. HOT RUN - Quick start, all bets, real multiplier cashout
       → Best for: Aggressive betting with existing config
       → Uses: MSS multiplier reader for precise cashout
       
    2. STANDARD - Time-based cashout (legacy)
       → Best for: Traditional betting approach
       → Uses: OCR detector (more stable but less precise)
       
    3. DRY RUN - Simulation mode, no real bets
       → Best for: Testing strategies safely
       → Uses: OCR detector
       
    4. OBSERVATION - Data collection only
       → Best for: Building training data for ML models
       → Uses: OCR detector
       
    5. DIAGNOSTIC - Test multiplier reader
       → Best for: Troubleshooting MSS capture issues
       → Uses: MSS multiplier reader (shows success rate)
    """
    print("="*100)
    print("AVIATOR BOT - ML MODE WITH HOT RUN")
    print("="*100)
    print("\nFeatures:")
    print("  [ROCKET] HOT RUN MODE - Quick start with existing config")
    print("  [TARGET] Real multiplier-based cashout (no time delays)")
    print("  [OK] Individual model predictions (LSTM, Random Forest, XGBoost, LightGBM)")
    print("  [OK] Enhanced logging and balance tracking")
    print("  [WRENCH] Diagnostic mode for troubleshooting")
    print("="*100)

    bot = AviatorBotML()

    # Initial configuration setup (coordinates only)
    if bot.config_manager.load_config() and bot.config_manager.multiplier_region:
        print(f"\n[OK] Config loaded")
        print("\nOptions:")
        print("  1. Use existing coordinates")
        print("  2. New setup (configure coordinates)")
        choice = input("\nChoice (1/2): ").strip()
        
        if choice == '2':
            bot.config_manager.setup_coordinates()
        else:
            print("\n[OK] Using existing coordinates")
    else:
        print("\n[INFO] No existing configuration found. Starting new setup.")
        bot.config_manager.setup_coordinates()

    # Initialize components
    bot.initialize_components()
    
    # Start cloud sync
    if bot.history_tracker.start_cloud_sync():
        print("☁️ Google Sheets sync started")
    else:
        print("⚠️ Cloud sync not available (install: pip install gspread google-auth)")
    
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

    # Show summary
    print("\n" + "="*100)
    print("[NOTE] SUMMARY")
    print("="*100)
    print(f"Initial stake:     {bot.config_manager.initial_stake}")
    print(f"Max stake:         {bot.config_manager.max_stake}")
    print(f"Increase on win:   +{bot.config_manager.stake_increase_percent}%")
    print(f"Cashout delay:     {bot.config_manager.cashout_delay}s")
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

    # Ask user about operating mode
    print("\n" + "="*100)
    print("OPERATING MODE")
    print("="*100)
    print("\nChoose mode:")
    print("  1. HOT RUN MODE - Real multiplier-based cashout (uses real-time screen capture)")
    print("  2. STANDARD MODE - Time-based cashout (uses clipboard/OCR for round detection)")
    print("  3. DRY RUN MODE - Simulate betting and log all decisions (NO REAL BETS, uses clipboard/OCR)")
    print("  4. OBSERVATION MODE - Collect data without betting (uses clipboard/OCR)")
    print("  5. DIAGNOSTIC MODE - Test clipboard/OCR multiplier reading")

    mode_choice = input("\nChoice (1/2/3/4/5, default: 1): ").strip()

    if mode_choice == '2':
        mode = 'standard'
        print("\n[TIMER] STANDARD MODE - Time-based cashout")
        estimated_mult = estimate_multiplier(bot.config_manager.cashout_delay)
        print(f"[TARGET] Cashout at: {bot.config_manager.cashout_delay}s (~{estimated_mult:.2f}x)")
    elif mode_choice == '3':
        mode = 'dry_run'
        print("\n[LOG] DRY RUN MODE - Simulating all decisions WITHOUT real bets")
    elif mode_choice == '4':
        mode = 'observation'
        print("\n[STATS] OBSERVATION MODE - Data collection only")
    elif mode_choice == '5':
        mode = 'diagnostic'
        print("\n[WRENCH] DIAGNOSTIC MODE - Testing clipboard/OCR multiplier reading")
        print("\nPress Enter to start diagnostics...")
        input()
        bot.run_diagnostic_mode()
        return
    else:
        mode = 'hot_run'
        print("\n[ROCKET] HOT RUN MODE - Real multiplier-based cashout")
        print("[FIRE] ALL BETS WILL BE PLACED (No ML filtering)")
        print("[TARGET] Cashout will be based on ML-predicted multiplier values")
        
        # Set default target multiplier
        default_target = input(f"\nDefault target multiplier (default: 2.0x): ").strip()
        if default_target:
            try:
                bot.target_cashout_multiplier = float(default_target)
            except:
                bot.target_cashout_multiplier = 2.0
        else:
            bot.target_cashout_multiplier = 2.0
        
        print(f"[TARGET] Default target set to: {bot.target_cashout_multiplier:.2f}x")
        print("[NOTE] ML models may override this with dynamic targets")
        print("[WARNING] State detection uses MSS multiplier reader for accuracy")

    print("\nPress Enter to start...")
    input()

    # Save config
    bot.config_manager.save_config()
    
    try:
    
    # Pre-run validation for Hot Run mode
    if mode == 'hot_run':
        print("\n[CHECK] Running pre-flight checks for Hot Run mode...")
        
        # Check if multiplier reader is working
        if bot.multiplier_reader:
            print("[TEST] Testing real-time multiplier reader (3 attempts)...")
            working = False
            for i in range(3):
                try:
                    test_frame = bot.multiplier_reader.capture_region()
                    if test_frame is not None:
                        print(f"  Attempt {i+1}/3: [OK] Capture successful")
                        working = True
                        break
                    else:
                        print(f"  Attempt {i+1}/3: [X] Capture failed")
                except Exception as e:
                    print(f"  Attempt {i+1}/3: [X] Error: {e}")
                time.sleep(0.5)
            
            if not working:
                print("\n[WARNING] Real-time multiplier reader is not working!")
                print("[TIP] Possible solutions:")
                print("  1. Make sure game window is visible and not minimized")
                print("  2. Run setup again to reconfigure regions")
                print("  3. Consider using STANDARD MODE instead (time-based)")
                print("  4. Run DIAGNOSTIC MODE (option 5) to test clipboard/OCR")
                
                response = input("\nContinue anyway? (y/n): ").strip().lower()
                if response != 'y':
                    print("[STOP] Exiting...")
                    return
        
        print("[OK] Pre-flight checks passed!\n")

    if mode == 'observation':
        bot.run_observation_mode()
    elif mode == 'dry_run':
        bot.run_dry_run_mode()
    elif mode == 'hot_run':
        bot.run_hot_run_mode()
    else: # Default to standard mode if no valid choice or '2'
        bot.run_ml_mode()
    
    except KeyboardInterrupt:
        print("\n\n⏹️ Bot stopped by user")
    finally:
        # Stop cloud sync on exit
        bot.history_tracker.stop_cloud_sync()


if __name__ == "__main__":
    main()
