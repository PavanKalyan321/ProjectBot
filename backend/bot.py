# Import utilities
from utils.betting_helpers import (
    set_stake_verified,
    place_bet_with_verification,
    cashout_verified,
    estimate_multiplier,
    increase_stake,
    reset_stake
)

# Import from bot_modular.py components
from config import ConfigManager
from readregion import MultiplierReader
from core import GameStateDetector
from core.history_tracker import RoundHistoryTracker

# Import operating modes
from modes import run_observation_mode, run_dry_run_mode

# ✨ IMPORT AUTOML PREDICTOR
from automl_predictor import get_predictor, predict_next_round, add_round_result

import time
import pyautogui
import re
import os
import csv
from datetime import datetime
from collections import deque

class AviatorBot:
    """Simple Aviator Bot with multiplier-based cashout using MultiplierReader directly."""

    def __init__(self, mode='live'):
        """
        Initialize the bot.
        
        Args:
            mode: 'live', 'dry_run', or 'observation'
        """
        self.mode = mode
        self.config_manager = ConfigManager()
        self.multiplier_reader = None
        self.detector = None

        # ✨ INITIALIZE AUTOML PREDICTOR
        self.automl_predictor = get_predictor()
        self.use_automl_predictions = True  # Flag to enable/disable AutoML

        # HARDCODED COORDINATES - Set these to match your screen
        self.MULTIPLIER_REGION = {"top": 506, "left": 330, "width": 322, "height": 76}
        self.STAKE_COORDS = None  # Will use from config or set manually: (x, y)
        self.BET_BUTTON_COORDS = None  # Will use from config or set manually: (x, y)
        self.CASHOUT_COORDS = None  # Will use from config or set manually: (x, y)
        self.balance_coords = (626, 149, 694, 152)  # UPDATE if needed
        
        # Bot settings (will be set from user input)
        self.initial_stake = 25
        self.max_stake = 1000
        self.target_multiplier = 2.0
        self.current_stake = self.initial_stake

        # Balance tracking
        self.last_balance = None
        self.hypothetical_balance = 1000.0  # For dry run mode
        
        # Round tracking
        self.last_logged_mult = None
        self.bet_placed_this_round = False  # Track if bet already placed
        self.current_round_id = 0  # Track round number
        
        # Round state management - retains multiplier throughout round lifecycle
        self.round_state = {
            "final_multiplier": 0.0,
            "cashout_multiplier": 0.0,
            "bet_placed": False,
            "stake": 0,
            "profit_loss": 0.0,
            "completed": False
        }

        # ✨ AutoML prediction tracking
        self.current_automl_prediction = None
        self.current_automl_ensemble = None
        self.current_automl_recommendation = None

        # Statistics
        self.stats = {
            "rounds_played": 0,
            "rounds_observed": 0,
            "successful_cashouts": 0,
            "failed_cashouts": 0,
            "cancelled_bets": 0,
            "total_bet": 0,
            "total_return": 0,
            "current_streak": 0
        }
        
        # History tracking
        self.history_file = "aviator_rounds_history.csv"
        self.prediction_history = deque(maxlen=10)
        self.history_tracker = RoundHistoryTracker()  # Initialize here
        self._initialize_history_file()

    def _initialize_history_file(self):
        """Initialize CSV history file if it doesn't exist."""
        if not os.path.exists(self.history_file):
            with open(self.history_file, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    'timestamp',
                    'round_id',
                    'multiplier',
                    'bet_placed',
                    'stake_amount',
                    'cashout_time',
                    'profit_loss',
                    'model_prediction',
                    'model_confidence',
                    'model_predicted_range_low',
                    'model_predicted_range_high',
                    'pos2_confidence',
                    'pos2_target_multiplier',
                    'pos2_burst_probability',
                    'pos2_phase',
                    'pos2_rules_triggered'
                ])
            print(f"📝 Created history file: {self.history_file}")

    def _log_to_history(self, round_id, final_multiplier, cashout_multiplier, 
                       bet_placed, stake, profit_loss, cashout_time=None,
                       model_prediction=None, model_confidence=None,
                       model_predicted_range_low=None, model_predicted_range_high=None,
                       pos2_confidence=None, pos2_target_multiplier=None,
                       pos2_burst_probability=None, pos2_phase=None,
                       pos2_rules_triggered=None):
        """
        Log round data to CSV file in the specified format.
        """
        try:
            with open(self.history_file, 'a', newline='') as f:
                writer = csv.writer(f)
                
                # Use cashout_multiplier for cashout_time if not provided
                if cashout_time is None:
                    cashout_time = cashout_multiplier if cashout_multiplier > 0 else ""
                
                print(f"📝 Logging Round #{round_id}: Multiplier={final_multiplier:.2f}x, "
                      f"Cashout={cashout_time if cashout_time else 'N/A'}, "
                      f"Bet Placed={bet_placed}")
                
                writer.writerow([
                    datetime.now().isoformat(),
                    round_id,
                    f"{final_multiplier:.2f}",
                    bet_placed,
                    stake if stake > 0 else "",
                    f"{cashout_time:.2f}" if cashout_time and cashout_time != "" else "",
                    f"{profit_loss:.2f}" if profit_loss != 0 else "",
                    model_prediction if model_prediction is not None else "",
                    f"{model_confidence:.4f}" if model_confidence is not None else "",
                    f"{model_predicted_range_low:.2f}" if model_predicted_range_low is not None else "",
                    f"{model_predicted_range_high:.2f}" if model_predicted_range_high is not None else "",
                    f"{pos2_confidence:.4f}" if pos2_confidence is not None else "",
                    f"{pos2_target_multiplier:.2f}" if pos2_target_multiplier is not None else "",
                    f"{pos2_burst_probability:.4f}" if pos2_burst_probability is not None else "",
                    pos2_phase if pos2_phase is not None else "",
                    pos2_rules_triggered if pos2_rules_triggered is not None else ""
                ])
        except Exception as e:
            print(f"⚠️  Failed to log to history: {e}")

    # ✨ NEW METHOD: Train AutoML and get predictions
    def get_automl_predictions(self):
        """
        Get predictions from AutoML models.
        Returns: (predictions, ensemble, recommendation) or (None, None, None)
        """
        if not self.use_automl_predictions:
            return None, None, None
        
        try:
            print("\n" + "="*80)
            print("🤖 GETTING AUTOML PREDICTIONS...")
            print("="*80)
            
            # Get predictions (this will also print the table)
            predictions, ensemble, recommendation = predict_next_round(self.history_file)
            
            return predictions, ensemble, recommendation
            
        except Exception as e:
            print(f"⚠️  AutoML prediction error: {e}")
            import traceback
            traceback.print_exc()
            return None, None, None

    # ✨ NEW METHOD: Update AutoML with round result
    def update_automl_with_result(self, final_multiplier):
        """
        Update AutoML predictor with the final multiplier from completed round.
        This trains the model incrementally.
        
        Args:
            final_multiplier: The final crash multiplier
        """
        if not self.use_automl_predictions or final_multiplier <= 0:
            return
        
        try:
            print(f"\n🧠 Training AutoML with result: {final_multiplier:.2f}x")
            add_round_result(final_multiplier)
            print("✅ AutoML model updated")
            
        except Exception as e:
            print(f"⚠️  AutoML update error: {e}")

    def initialize_components(self):
        """Initialize multiplier reader and detector with validation."""
        print("\n" + "="*80)
        print("🔧 INITIALIZING COMPONENTS")
        print("="*80)
        
        # Use hardcoded multiplier region
        region_dict = self.MULTIPLIER_REGION.copy()
        print(f"📍 Using hardcoded multiplier region: {region_dict}")
        
        # Override config if using hardcoded values
        if self.config_manager.multiplier_region:
            print("   (Config region exists but using hardcoded values)")
        
        # Set coordinates from config or use hardcoded
        if not self.STAKE_COORDS and self.config_manager.stake_coords:
            self.STAKE_COORDS = self.config_manager.stake_coords
        if not self.BET_BUTTON_COORDS and self.config_manager.bet_button_coords:
            self.BET_BUTTON_COORDS = self.config_manager.bet_button_coords
        if not self.CASHOUT_COORDS and self.config_manager.cashout_coords:
            self.CASHOUT_COORDS = self.config_manager.cashout_coords
        
        # In observation mode, we don't need all coordinates
        if self.mode == 'observation':
            print("   📊 Observation mode - betting coordinates not required")
        else:
            # Validate that we have all required coordinates
            if not self.STAKE_COORDS or not self.BET_BUTTON_COORDS or not self.CASHOUT_COORDS:
                print("\n⚠️  WARNING: Some coordinates are missing!")
                print(f"   Stake coords: {self.STAKE_COORDS}")
                print(f"   Bet button coords: {self.BET_BUTTON_COORDS}")
                print(f"   Cashout coords: {self.CASHOUT_COORDS}")
                
                response = input("\n   Continue anyway? (y/n): ").strip().lower()
                if response != 'y':
                    return False
        
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
                    print(f"⚠️  WARNING: Multiplier region is outside screen bounds!")
                    print(f"   Screen: {primary['width']}x{primary['height']}")
                    print(f"   Region: left={region_dict['left']}, top={region_dict['top']}, "
                          f"width={region_dict['width']}, height={region_dict['height']}")
                    
                    response = input("\n   Continue anyway? (y/n): ").strip().lower()
                    if response != 'y':
                        return False
        except Exception as e:
            print(f"⚠️  Could not validate region: {e}")
        
        # Initialize multiplier reader
        self.multiplier_reader = MultiplierReader(region_dict)

        # Convert region_dict back to [x1, y1, x2, y2] format for detector
        detector_region = [
            region_dict["left"],
            region_dict["top"],
            region_dict["left"] + region_dict["width"],
            region_dict["top"] + region_dict["height"]
        ]

        # Initialize detector (only for bet verification - NOT for game state)
        self.detector = GameStateDetector(detector_region)

        # Initialize history tracker
        self.history_tracker = RoundHistoryTracker()
        
        # Test multiplier reader (3 attempts)
        print("\n🧪 Testing multiplier reader...")
        working = False
        for i in range(3):
            try:
                test_frame = self.multiplier_reader.capture_region()
                if test_frame is not None:
                    print(f"   Attempt {i+1}/3: ✅ Capture successful (shape: {test_frame.shape})")
                    
                    # Use fast_extract_multiplier_or_status to test reading
                    value = self.multiplier_reader.fast_extract_multiplier_or_status(test_frame)
                    
                    if value == "AWAITING NEXT FLIGHT":
                        print(f"   Status: AWAITING NEXT FLIGHT")
                        working = True
                    elif value:
                        print(f"   Current reading: {value}")
                        working = True
                    else:
                        print(f"   Status: No readable text (empty frame)")
                    
                    break
                else:
                    print(f"   Attempt {i+1}/3: ❌ Capture failed")
            except Exception as e:
                print(f"   Attempt {i+1}/3: ❌ Error: {e}")
            time.sleep(0.5)
        
        if not working:
            print("\n⚠️  WARNING: Multiplier reader is not working!")
            print("   💡 Tips:")
            print("      - Make sure game window is visible and not minimized")
            print("      - Run setup again to reconfigure regions")
            
            response = input("\n   Continue anyway? (y/n): ").strip().lower()
            if response != 'y':
                return False
        
        print("\n✅ Components initialized successfully!")
        return True

    def get_user_settings(self):
        """Get stake, max stake, and target multiplier from user."""
        print("\n" + "="*80)
        print("⚙️  CONFIGURATION")
        print("="*80)
        
        try:
            stake_input = input(f"\nInitial stake (default {self.initial_stake}): ").strip()
            if stake_input:
                self.initial_stake = int(stake_input)
            
            max_stake_input = input(f"Max stake (default {self.max_stake}): ").strip()
            if max_stake_input:
                self.max_stake = int(max_stake_input)
            
            target_input = input(f"Target multiplier for cashout (default {self.target_multiplier}): ").strip()
            if target_input:
                self.target_multiplier = float(target_input)
            
            # ✨ ASK ABOUT AUTOML
            automl_choice = input(f"\nUse AutoML predictions? (y/n, default: y): ").strip().lower()
            if automl_choice == 'n':
                self.use_automl_predictions = False
                print("   📊 AutoML predictions disabled")
            else:
                self.use_automl_predictions = True
                print("   🤖 AutoML predictions enabled")
            
            self.current_stake = self.initial_stake
            
            print(f"\n✅ Settings configured:")
            print(f"   Initial Stake: {self.initial_stake}")
            print(f"   Max Stake: {self.max_stake}")
            print(f"   Target Multiplier: {self.target_multiplier}x")
            print(f"   AutoML: {'Enabled' if self.use_automl_predictions else 'Disabled'}")
            
        except ValueError as e:
            print(f"⚠️  Invalid input: {e}. Using defaults.")
            self.current_stake = self.initial_stake

    def _read_balance(self):
        """Read current balance from balance region."""
        try:
            import pyperclip
            
            x1, y1, x2, y2 = self.balance_coords
            
            # Triple-click to select text
            pyautogui.click((x1 + x2) // 2, (y1 + y2) // 2, clicks=3)
            time.sleep(0.1)
            
            # Copy to clipboard
            pyautogui.hotkey('ctrl', 'c')
            time.sleep(0.1)
            
            balance_text = pyperclip.paste().strip()
            
            if not balance_text:
                return None
            
            # Parse balance
            balance_text = balance_text.replace(',', '')
            
            # Handle K notation (e.g., "1.5K")
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

    def _wait_for_awaiting_state(self, timeout=60):
        """
        Wait for AWAITING state using MultiplierReader.has_crashed().
        Returns True when AWAITING is confirmed.
        """
        print("⏳ Waiting for AWAITING NEXT FLIGHT state...")
        start_time = time.time()
        consecutive_awaiting = 0
        last_status_print = 0

        while time.time() - start_time < timeout:
            try:
                # Use has_crashed() which detects "AWAITING NEXT FLIGHT"
                if self.multiplier_reader.has_crashed():
                    consecutive_awaiting += 1
                    # Need 2 consecutive confirmations to be sure
                    if consecutive_awaiting >= 2:
                        print("✅ AWAITING NEXT FLIGHT confirmed")
                        return True
                    time.sleep(0.2)
                else:
                    consecutive_awaiting = 0
                    time.sleep(0.2)
                
            except Exception as e:
                # On error, wait and retry
                time.sleep(0.5)
                continue
            
            # Print status every 5 seconds
            elapsed = time.time() - start_time
            if elapsed - last_status_print >= 5:
                print(f"   Still waiting... ({elapsed:.0f}s)")
                last_status_print = elapsed

        print("⚠️  Timeout waiting for awaiting state")
        return False

    def _verify_game_running(self):
        """
        Check if game is already running using MultiplierReader.read_current_multiplier().
        Returns True if multiplier >= 1.0 (game is flying).
        """
        try:
            current_mult = self.multiplier_reader.read_current_multiplier()
            if current_mult and current_mult >= 1.0:
                return True
        except Exception:
            pass
        
        return False

    def _wait_for_round_start(self, timeout=15):
        """
        Wait for round to start using MultiplierReader.read_current_multiplier().
        Returns True when multiplier >= 1.0 is detected.
        """
        print("⏳ Waiting for round to start...")
        start_time = time.time()

        while time.time() - start_time < timeout:
            try:
                # Read current multiplier
                current_mult = self.multiplier_reader.read_current_multiplier()
                
                if current_mult and current_mult >= 1.0:
                    print(f"✅ Round started! Current multiplier: {current_mult:.2f}x")
                    return True
                
                # Check if still in awaiting state after 3 seconds
                if time.time() - start_time > 3:
                    if self.multiplier_reader.has_crashed():
                        # Still awaiting after 3 seconds, likely won't start
                        print("⚠️  Still in AWAITING state after 3s")
                        return False
            
            except Exception:
                time.sleep(0.2)
                continue
            
            time.sleep(0.1)

        print("⚠️  Timeout waiting for round start")
        return False

    def _wait_for_crash_and_read_multiplier(self, timeout=60):
        """Wait for round to crash and return final multiplier."""
        start_time = time.time()
        last_valid_mult = 0.0
        
        while time.time() - start_time < timeout:
            try:
                # Continuously update last valid multiplier while round is active
                current_mult = self.multiplier_reader.read_current_multiplier()
                if current_mult and current_mult > 0:
                    last_valid_mult = current_mult
                
                # Check if crashed
                if self.multiplier_reader.has_crashed():
                    time.sleep(0.3)  # Brief pause to ensure value is stable
                    final_mult = self.multiplier_reader.last_valid_multiplier
                    if final_mult and final_mult > 0:
                        # Store in round state
                        self.round_state["final_multiplier"] = final_mult
                        return True, final_mult
                    elif last_valid_mult > 0:
                        # Use our tracked value
                        self.round_state["final_multiplier"] = last_valid_mult
                        return True, last_valid_mult
                    # If no valid multiplier, return a default
                    self.round_state["final_multiplier"] = 0.0
                    return True, 0.0
                
                time.sleep(0.2)
            except Exception:
                time.sleep(0.5)
                continue
        
        # Timeout - use last valid multiplier if available
        if last_valid_mult > 0:
            self.round_state["final_multiplier"] = last_valid_mult
            return False, last_valid_mult
        
        self.round_state["final_multiplier"] = 0.0
        return False, 0.0

    def monitor_and_cashout(self, target_multiplier):
        """
        Monitor multiplier and cashout when target reached using MultiplierReader.
        After cashout, continues monitoring to get the final crash multiplier.
        Stores final_multiplier in round_state for reliable CSV logging.
        
        Returns:
            tuple: (success: bool, profit: float, cashout_mult: float, final_mult: float, result_type: str)
        """
        print(f"\n👀 Monitoring multiplier for target: {target_multiplier:.2f}x")
        print("   " + "-"*70)
        
        round_start = time.time()
        cashout_triggered = False
        cashout_mult = 0
        last_displayed_mult = None
        stake_used = self.current_stake
        last_valid_mult = 0.0  # Track last valid multiplier throughout round
        
        while True:
            try:
                # Read current multiplier using MultiplierReader
                current_mult = self.multiplier_reader.read_current_multiplier()
                
                # Update last valid multiplier continuously
                if current_mult and current_mult > 0:
                    last_valid_mult = current_mult
                
                # Display progress
                if current_mult and current_mult != last_displayed_mult:
                    elapsed = time.time() - round_start
                    remaining = target_multiplier - current_mult
                    
                    # Color-coded status
                    if not cashout_triggered:
                        if remaining > 0.5:
                            status = '🟢 SAFE '
                        elif remaining > 0.2:
                            status = '🟡 READY'
                        elif remaining > 0.05:
                            status = '🟠 ALERT'
                        else:
                            status = '🔴 NOW! '
                    else:
                        status = '👁️ WATCH'  # Watching after cashout
                    
                    print(f"   {status} | Current: {current_mult:.2f}x | Target: {target_multiplier:.2f}x", 
                          end='\r', flush=True)
                    last_displayed_mult = current_mult
                
                # Check for crash
                if self.multiplier_reader.has_crashed():
                    print("\n")
                    final_mult = self.multiplier_reader.last_valid_multiplier or last_valid_mult or 0.0
                    
                    # CRITICAL: Store final multiplier in round state
                    self.round_state["final_multiplier"] = final_mult
                    
                    if cashout_triggered:
                        # We already cashed out, just got final multiplier
                        print(f"   🏁 Round ended at {final_mult:.2f}x (cashed out at {cashout_mult:.2f}x)")
                        self.round_state["cashout_multiplier"] = cashout_mult
                        return True, stake_used * (cashout_mult - 1), cashout_mult, final_mult, "WIN"
                    else:
                        # Crashed before we could cashout
                        print(f"   💥 CRASHED at {final_mult:.2f}x (target: {target_multiplier:.2f}x)")
                        
                        self.stats["failed_cashouts"] += 1
                        self.stats["current_streak"] = 0
                        
                        loss = -stake_used
                        self.round_state["cashout_multiplier"] = 0.0
                        return False, loss, 0, final_mult, "CRASH"
                
                # Check if we've reached target (and haven't cashed out yet)
                if current_mult and current_mult >= target_multiplier and not cashout_triggered:
                    print("\n")
                    print(f"   🎯 TARGET REACHED: {current_mult:.2f}x - EXECUTING CASHOUT...")
                    
                    time.sleep(0.05)  # Small delay before cashout
                    
                    # Final crash check before cashout
                    if self.multiplier_reader.has_crashed():
                        print(f"   💥 Crashed during cashout attempt!")
                        
                        self.stats["failed_cashouts"] += 1
                        self.stats["current_streak"] = 0
                        
                        loss = -stake_used
                        final_mult = self.multiplier_reader.last_valid_multiplier or last_valid_mult or 0.0
                        
                        # Store in round state
                        self.round_state["final_multiplier"] = final_mult
                        self.round_state["cashout_multiplier"] = 0.0
                        
                        return False, loss, 0, final_mult, "CRASH"
                    
                    # Execute cashout
                    cashout_success, cashout_reason = cashout_verified(
                        self.CASHOUT_COORDS,
                        self.detector
                    )
                    
                    if cashout_success:
                        print("   ✅ Cashout command sent!")
                        cashout_mult = current_mult  # Store cashout multiplier
                        
                        # Wait for balance to update
                        print("   ⏳ Validating balance change...")
                        time.sleep(0.2)
                        new_balance = self._read_balance()
                        
                        # Validate win by checking balance
                        if self.last_balance is not None and new_balance is not None:
                            balance_change = new_balance - self.last_balance
                            
                            if balance_change > 0:
                                print(f"   ✅ Balance validation: WIN confirmed (+{balance_change:.2f})")
                                
                                self.stats["successful_cashouts"] += 1
                                self.stats["current_streak"] += 1
                                
                                profit = balance_change
                                returns = stake_used + profit
                                self.stats["total_return"] += returns
                                self.last_balance = new_balance
                                
                                # Mark cashout successful and continue monitoring for final multiplier
                                cashout_triggered = True
                                print(f"   👁️  Continuing to monitor for round end...")
                                
                            else:
                                print(f"   ❌ Balance validation: LOST (change: {balance_change:.2f})")
                                
                                self.stats["failed_cashouts"] += 1
                                self.stats["current_streak"] = 0
                                
                                loss = -stake_used
                                final_mult = self.multiplier_reader.last_valid_multiplier or current_mult
                                self.last_balance = new_balance
                                
                                # Continue to get final multiplier even on loss
                                print(f"   👁️  Continuing to monitor for round end...")
                                crashed, final_mult = self._wait_for_crash_and_read_multiplier(timeout=60)
                                if not crashed and last_valid_mult > 0:
                                    final_mult = last_valid_mult
                                
                                # Store in round state
                                self.round_state["final_multiplier"] = final_mult
                                self.round_state["cashout_multiplier"] = 0.0
                                
                                return False, loss, 0, final_mult, "CRASH"
                        else:
                            # Could not validate balance - assume win based on cashout success
                            print("   ⚠️  Could not validate balance - using estimated profit")
                            
                            self.stats["successful_cashouts"] += 1
                            self.stats["current_streak"] += 1
                            
                            returns = stake_used * current_mult
                            profit = returns - stake_used
                            self.stats["total_return"] += returns
                            
                            if new_balance:
                                self.last_balance = new_balance
                            
                            # Mark cashout successful and continue monitoring
                            cashout_triggered = True
                            cashout_mult = current_mult
                            print(f"   👁️  Continuing to monitor for round end...")
                    else:
                        print(f"   ❌ Cashout failed: {cashout_reason}")
                        
                        time.sleep(0.2)
                        # Check if crashed
                        if self.multiplier_reader.has_crashed() or cashout_reason == "NO_ACTIVE_BET":
                            self.stats["failed_cashouts"] += 1
                            self.stats["current_streak"] = 0
                            
                            loss = -stake_used
                            final_mult = self.multiplier_reader.last_valid_multiplier or last_valid_mult or 0.0
                            
                            # Store in round state
                            self.round_state["final_multiplier"] = final_mult
                            self.round_state["cashout_multiplier"] = 0.0
                            
                            return False, loss, 0, final_mult, "CRASH"
                
                time.sleep(0.03)  # Check every 30ms for responsiveness
                
            except Exception as e:
                # On error, check if crashed as fallback
                try:
                    if self.multiplier_reader.has_crashed():
                        print("\n")
                        final_mult = self.multiplier_reader.last_valid_multiplier or last_valid_mult or 0.0
                        
                        # Store in round state
                        self.round_state["final_multiplier"] = final_mult
                        
                        if cashout_triggered:
                            # Already cashed out, just reporting final
                            print(f"   🏁 Round ended at {final_mult:.2f}x (error recovery)")
                            profit = stake_used * (cashout_mult - 1)
                            self.round_state["cashout_multiplier"] = cashout_mult
                            return True, profit, cashout_mult, final_mult, "WIN"
                        else:
                            print(f"   💥 Detected crash (error recovery)")
                            
                            self.stats["failed_cashouts"] += 1
                            self.stats["current_streak"] = 0
                            
                            loss = -stake_used
                            self.round_state["cashout_multiplier"] = 0.0
                            
                            return False, loss, 0, final_mult, "CRASH"
                except:
                    pass
                
                # Otherwise wait a bit and retry
                time.sleep(0.05)
                continue

    def run(self):
        """Main bot loop - logs ALL completed rounds to CSV with both cashout and final multipliers."""
        # print("\n" + "="*80)
        print("🚀 AVIATOR BOT STARTED")
        # print("="*80)
        print("📡 Using MultiplierReader for real-time game state detection")
        print("📝 Logging ALL rounds to CSV (bet or no bet)")
        print("🎯 Tracking both cashout multiplier AND final round multiplier")
        if self.use_automl_predictions:
            print("🤖 AutoML predictions ENABLED - Training after each round")
        print("Press Ctrl+C to stop.\n")

        round_number = 0
        cumulative_profit = 0

        try:
            while True:
                round_number += 1
                # print(f"\n{'='*80}")
                print(f"🎮 ROUND #{round_number:03d}")
                # print(f"{'='*80}")
                
                # ✨ GET AUTOML PREDICTIONS BEFORE ROUND STARTS
                if self.use_automl_predictions:
                    self.current_automl_prediction, self.current_automl_ensemble, self.current_automl_recommendation = self.get_automl_predictions()
                
                # Reset tracking for new round
                self.bet_placed_this_round = False
                self.current_round_id = round_number
                
                # Reset round state for new round
                self.round_state = {
                    "final_multiplier": 0.0,
                    "cashout_multiplier": 0.0,
                    "bet_placed": False,
                    "stake": 0,
                    "profit_loss": 0.0,
                    "completed": False
                }
                
                round_bet_placed = False
                round_stake = 0
                round_result = "NOT_PARTICIPATED"
                round_profit_loss = 0.0
                final_mult = 0.0  # Initialize final multiplier
                cashout_mult = 0.0  # Initialize cashout multiplier

                # Step 1: Wait for AWAITING NEXT FLIGHT
                if not self._wait_for_awaiting_state():
                    print("⚠️  Skipping round - couldn't detect awaiting state")
                    # Log skipped round with zeros
                    self._log_to_history(
                        round_id=round_number,
                        final_multiplier=0.0,
                        cashout_multiplier=0.0,
                        bet_placed=False,
                        stake=0,
                        profit_loss=0.0
                    )
                    continue
                
                time.sleep(0.3)

                # Step 2: Pre-bet checks
                if self._verify_game_running():
                    print("⚠️  Game already running - will observe only")
                    round_bet_placed = False
                elif self.bet_placed_this_round:
                    print("⚠️  Bet already placed for this round - observing")
                    round_bet_placed = False
                else:
                    # Step 3: Try to place bet
                    print(f"\n💰 Setting stake: {self.current_stake}")
                    if not set_stake_verified(self.STAKE_COORDS, self.current_stake):
                        print("❌ Failed to set stake - will observe only")
                        round_bet_placed = False
                    else:
                        print("✅ Stake set")
                        time.sleep(0.15)

                        # Step 4: Place bet
                        print("🎲 Placing bet...")
                        self.stats["ml_bets_placed"] = self.stats.get("ml_bets_placed", 0)
                        
                        bet_success, bet_reason = place_bet_with_verification(
                            self.BET_BUTTON_COORDS,
                            self.detector,
                            self.stats,
                            self.current_stake
                        )

                        if not bet_success:
                            print(f"❌ Bet failed: {bet_reason} - will observe only")
                            round_bet_placed = False
                        else:
                            print("✅ Bet placed successfully!")
                            self.stats["rounds_played"] += 1
                            self.stats["total_bet"] += self.current_stake
                            self.bet_placed_this_round = True
                            round_bet_placed = True
                            round_stake = self.current_stake
                            
                            # Wait for bet to register
                            print("⏳ Waiting for bet to register...")
                            time.sleep(1.0)

                # Step 5: Wait for round to start (whether we bet or not)
                print("\n⏳ Waiting for round to start...")
                round_started = self._wait_for_round_start(timeout=20)
                
                if not round_started:
                    print("⚠️  Round didn't start - timeout")
                    
                    # If we placed bet, it was cancelled
                    if round_bet_placed:
                        self.stats["cancelled_bets"] += 1
                        self.stats["failed_cashouts"] += 1
                        round_profit_loss = -round_stake
                        cumulative_profit += round_profit_loss
                        round_result = "CANCELLED"
                        final_mult = 0.0  # Explicitly set to 0
                        
                        print(f"\n❌ RESULT: BET CANCELLED")
                        print(f"   💸 Loss: {round_profit_loss:.2f}")
                        print(f"   📊 Cumulative P/L: {cumulative_profit:+.2f}")
                        
                        # Reset stake on cancelled bet
                        self.current_stake = reset_stake(self.initial_stake, self.stats)
                    
                    # Log to CSV even if we didn't bet
                    self._log_to_history(
                        round_id=round_number,
                        final_multiplier=final_mult,
                        cashout_multiplier=cashout_mult,
                        bet_placed=round_bet_placed,
                        stake=round_stake,
                        profit_loss=round_profit_loss
                    )
                    
                    self.multiplier_reader.reset()
                    self.bet_placed_this_round = False
                    continue

                print("🚀 Game started!")
                self.multiplier_reader.reset()

                # Step 6: Monitor the round
                if round_bet_placed:
                    # Store bet info in round state
                    self.round_state["bet_placed"] = True
                    self.round_state["stake"] = round_stake
                    
                    # We have a bet - monitor and try to cashout
                    # Now returns 5 values: success, profit, cashout_mult, final_mult, result_type
                    success, profit, cashout_mult, final_mult, result_type = self.monitor_and_cashout(self.target_multiplier)
                    
                    # Update round state
                    self.round_state["profit_loss"] = profit
                    self.round_state["completed"] = True
                    
                    round_profit_loss = profit
                    cumulative_profit += profit
                    round_result = result_type

                    # Update balance if we won
                    if success and self.last_balance:
                        self.last_balance = self.last_balance + profit

                    # Print result
                    if result_type == "WIN":
                        print(f"\n✅ WIN: +{profit:.2f} (cashed out at {cashout_mult:.2f}x, round ended at {final_mult:.2f}x)")
                    else:
                        print(f"\n❌ LOSS: {profit:.2f} (crashed at {final_mult:.2f}x)")
                    
                    if self.last_balance:
                        print(f"   💰 Balance: {self.last_balance:.2f}")
                    
                    print(f"   📊 Cumulative P/L: {cumulative_profit:+.2f}")
                    
                    if result_type == "WIN":
                        print(f"   🔥 Win Streak: {self.stats['current_streak']}")
                    
                    print("-"*80)
                    
                    # Update stake based on result
                    if success:
                        old_stake = self.current_stake
                        self.current_stake = increase_stake(
                            self.current_stake,
                            20,
                            self.max_stake,
                            self.stats
                        )
                        if self.current_stake > old_stake:
                            print(f"   📈 Stake increased: {old_stake} → {self.current_stake}")
                    else:
                        old_stake = self.current_stake
                        self.current_stake = reset_stake(self.initial_stake, self.stats)
                        if self.current_stake < old_stake:
                            print(f"   📉 Stake reset: {old_stake} → {self.current_stake}")
                else:
                    # No bet placed - just observe the round
                    print("👁️  Observing round (no bet placed)...")
                    crashed, final_mult = self._wait_for_crash_and_read_multiplier(timeout=60)
                    
                    if crashed and final_mult and final_mult > 0:
                        print(f"   💥 Round ended at {final_mult:.2f}x (observed)")
                        round_result = "OBSERVED"
                        self.stats["rounds_observed"] = self.stats.get("rounds_observed", 0) + 1
                        self.round_state["completed"] = True
                    else:
                        # Try to get from round state if available
                        if self.round_state["final_multiplier"] > 0:
                            final_mult = self.round_state["final_multiplier"]
                            print(f"   💥 Round ended at {final_mult:.2f}x (observed via state)")
                            round_result = "OBSERVED"
                            self.stats["rounds_observed"] = self.stats.get("rounds_observed", 0) + 1
                            self.round_state["completed"] = True
                        else:
                            print(f"   ⚠️  Could not detect round end")
                            final_mult = 0.0
                            round_result = "OBSERVATION_TIMEOUT"

                # CRITICAL: Use round_state as the source of truth for final multiplier
                # Fallback chain: round_state -> function return -> last_valid_multiplier -> 0
                final_multiplier_to_log = (
                    self.round_state["final_multiplier"] if self.round_state["final_multiplier"] > 0 
                    else final_mult if final_mult > 0 
                    else self.multiplier_reader.last_valid_multiplier if self.multiplier_reader.last_valid_multiplier 
                    else 0.0
                )
                
                cashout_multiplier_to_log = (
                    self.round_state["cashout_multiplier"] if self.round_state["cashout_multiplier"] > 0 
                    else cashout_mult
                )
                
                # ✨ TRAIN AUTOML WITH ROUND RESULT (AFTER ROUND COMPLETES)
                if self.use_automl_predictions and final_multiplier_to_log > 0:
                    self.update_automl_with_result(final_multiplier_to_log)
                
                # Log to CSV with validated multipliers
                self._log_to_history(
                    round_id=round_number,
                    final_multiplier=final_multiplier_to_log,
                    cashout_multiplier=cashout_multiplier_to_log,
                    bet_placed=round_bet_placed,
                    stake=round_stake,
                    profit_loss=round_profit_loss
                )

                # Reset for next round
                self.multiplier_reader.reset()
                self.bet_placed_this_round = False
                time.sleep(0.2)

        except KeyboardInterrupt:
            print("\n\n⛔ Bot stopped by user.")
            self.print_final_stats(cumulative_profit)
        except Exception as e:
            print(f"\n\n❌ Unexpected error: {e}")
            import traceback
            traceback.print_exc()
            self.print_final_stats(cumulative_profit)

    def print_dry_run_stats(self, cumulative_profit):
        """Print dry run statistics."""
        # print("\n" + "="*80)
        print("📊 DRY RUN FINAL STATISTICS")
        print("="*80)
        print(f"Rounds played:        {self.stats['rounds_played']}")
        print(f"Simulated wins:       {self.stats['successful_cashouts']}")
        print(f"Simulated losses:     {self.stats['failed_cashouts']}")
        print(f"Cancelled bets:       {self.stats['cancelled_bets']}")
        print(f"Total stake:          {self.stats['total_bet']:.2f}")
        print(f"Total returns:        {self.stats['total_return']:.2f}")
        
        print(f"\n💰 HYPOTHETICAL RESULTS:")
        print(f"Starting balance:     1000.00")
        print(f"Final balance:        {self.hypothetical_balance:.2f}")
        print(f"Net profit/loss:      {cumulative_profit:+.2f}")
        
        if self.stats['rounds_played'] > 0:
            win_rate = (self.stats['successful_cashouts'] / self.stats['rounds_played']) * 100
            print(f"Win rate:             {win_rate:.1f}%")
            avg_bet = self.stats['total_bet'] / self.stats['rounds_played']
            print(f"Average bet:          {avg_bet:.2f}")
        
        print(f"\n💾 Data saved to: {self.history_file}")
        # print("="*80)

    def print_final_stats(self, cumulative_profit):
        """Print final statistics."""
        print("\n" + "="*80)
        print("📊 FINAL STATISTICS")
        print("="*80)
        print(f"Rounds played:     {self.stats['rounds_played']}")
        print(f"Rounds observed:   {self.stats.get('rounds_observed', 0)}")
        print(f"Wins:              {self.stats['successful_cashouts']}")
        print(f"Losses:            {self.stats['failed_cashouts']}")
        print(f"Cancelled bets:    {self.stats['cancelled_bets']}")
        print(f"Total bet:         {self.stats['total_bet']:.2f}")
        print(f"Total return:      {self.stats['total_return']:.2f}")
        print(f"Net profit:        {cumulative_profit:+.2f}")
        
        if self.last_balance:
            print(f"Final balance:     {self.last_balance:.2f}")
        
        if self.stats['rounds_played'] > 0:
            win_rate = (self.stats['successful_cashouts'] / self.stats['rounds_played']) * 100
            print(f"Win rate:          {win_rate:.1f}%")
            avg_bet = self.stats['total_bet'] / self.stats['rounds_played']
            print(f"Average bet:       {avg_bet:.2f}")
        
        print(f"\n💾 Data saved to: {self.history_file}")
        # print("="*80)


def main():
    """Main entry point with setup and configuration."""
    
    # Ask for mode first
    print("\n📋 SELECT OPERATING MODE:")
    print("   1. LIVE - Real betting (default)")
    print("   2. DRY RUN - Simulate betting without real bets")
    print("   3. OBSERVATION - Collect data only")
    
    mode_choice = input("\nChoice (1/2/3, default: 1): ").strip()
    
    if mode_choice == '2':
        mode = 'dry_run'
        print("\n🧪 DRY RUN MODE selected - No real bets will be placed")
    elif mode_choice == '3':
        mode = 'observation'
        print("\n📊 OBSERVATION MODE selected - Data collection only")
    else:
        mode = 'live'
        print("\n🚀 LIVE MODE selected - Real betting")
    
    bot = AviatorBot(mode=mode)

    # Setup or load configuration
    if bot.config_manager.load_config() and bot.config_manager.multiplier_region:
        print(f"\n✅ Configuration loaded")
        print("\nOptions:")
        print("  1. Use existing coordinates")
        print("  2. New setup (configure coordinates)")
        choice = input("\nChoice (1/2): ").strip()
        
        if choice == '2':
            bot.config_manager.setup_coordinates()
        else:
            print("\n✅ Using existing coordinates")
    else:
        print("\n📍 No existing configuration found. Starting setup...")
        bot.config_manager.setup_coordinates()

    # Initialize components with validation
    if not bot.initialize_components():
        print("\n❌ Failed to initialize components. Exiting.")
        return

    # Get user settings (skip for observation mode)
    if mode != 'observation':
        bot.get_user_settings()

    # ✨ LOAD HISTORICAL DATA FOR AUTOML TRAINING
    if bot.use_automl_predictions:
        print("\n" + "="*80)
        print("🤖 INITIALIZING AUTOML MODELS")
        print("="*80)
        
        # Load from CSV history file if it exists
        if os.path.exists(bot.history_file):
            print(f"📂 Loading historical data from {bot.history_file}...")
            rounds_loaded = bot.automl_predictor.load_history_from_csv(bot.history_file)
            if rounds_loaded > 0:
                print(f"✅ Loaded {rounds_loaded} rounds for training")
                print("🧠 AutoML models are ready with historical context")
            else:
                print("⚠️  No valid historical data found - models will learn from scratch")
        else:
            print("📝 No history file found - models will train as rounds are played")
        
        # Try loading manual history as well
        try:
            from manual_history_loader import integrate_manual_history_with_bot
            manual_rounds = integrate_manual_history_with_bot(bot)
            if manual_rounds > 0:
                print(f"✅ Additionally loaded {manual_rounds} rounds from manual history")
        except Exception as e:
            print(f"ℹ️  Manual history loader not available: {e}")
        
        print("="*80)

    # Confirm before starting
    print("\n" + "="*80)
    print("⚠️  IMPORTANT REMINDERS")
    print("="*80)
    print("   1. Game window must be visible and not minimized")
    print("   2. Make sure coordinates are correctly configured")
    
    if mode == 'live':
        print("   3. Bot will place REAL bets automatically")
        print(f"   4. Target cashout: {bot.target_multiplier:.2f}x")
        print("   5. Using MultiplierReader for game state detection")
    elif mode == 'dry_run':
        print("   3. Bot will SIMULATE bets (no real money)")
        print(f"   4. Target cashout: {bot.target_multiplier:.2f}x")
        print("   5. Results are hypothetical for testing")
    else:  # observation
        print("   3. Bot will ONLY observe and collect data")
        print("   4. No bets will be placed")
        print("   5. Data saved for analysis")
    
    print(f"   6. History will be saved to: {bot.history_file}")
    print("   7. ALL rounds will be logged (bet or observed)")
    print("   8. CSV tracks BOTH cashout multiplier AND final round multiplier")
    
    if bot.use_automl_predictions:
        print("   9. 🤖 AutoML is ENABLED - Training after every round")
        print("   10. Predictions will improve as more data is collected")
    
    confirm = input("\n✅ Ready to start? (yes/no): ").strip().lower()
    if confirm != 'yes':
        print("❌ Bot cancelled.")
        return

    # Save configuration
    bot.config_manager.save_config()

    # Start the bot
    bot.run()


if __name__ == "__main__":
    main()