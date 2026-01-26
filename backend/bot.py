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
from readregion import MultiplierReader, AviatorHistoryLogger
from core import GameStateDetector
from core.history_tracker import RoundHistoryTracker
from core.position2_conservative import Position2ConservativeEngine

# Import operating modes
from modes import run_observation_mode, run_dry_run_mode

# ✨ IMPORT AUTOML PREDICTOR
from automl_predictor import get_predictor, predict_next_round, add_round_result

import time
import pyautogui
import re
import os
import csv
import sys
import logging
from datetime import datetime
from collections import deque

# Model names for AutoML selection
MODEL_NAMES = {
    1: 'H2O AutoML',
    2: 'Google AutoML',
    3: 'Auto-sklearn',
    4: 'LSTM Model',
    5: 'AutoGluon',
    6: 'PyCaret',
    7: 'Random Forest',
    8: 'CatBoost',
    9: 'LightGBM',
    10: 'XGBoost',
    11: 'MLP Neural Net',
    12: 'TPOT Genetic',
    13: 'AutoKeras',
    14: 'Auto-PyTorch',
    15: 'MLBox',
    16: 'TransmogrifAI'
}

class TeeOutput:
    """Duplicates output to both console and log file."""
    def __init__(self, log_file):
        self.terminal = sys.stdout
        self.log = open(log_file, 'a', encoding='utf-8')

    def write(self, message):
        self.terminal.write(message)
        self.log.write(message)
        self.log.flush()

    def flush(self):
        self.terminal.flush()
        self.log.flush()

    def close(self):
        self.log.close()


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

        # Setup logging to file
        self.log_file = f"bot_session_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        self.tee = None
        self._setup_logging()

        # ✨ INITIALIZE AUTOML PREDICTOR
        self.automl_predictor = None  # Will be initialized with config
        self.use_automl_predictions = True  # Flag to enable/disable AutoML

        # COORDINATES - Will be loaded from config or set during setup
        self.MULTIPLIER_REGION = None
        self.STAKE_COORDS = None
        self.BET_BUTTON_COORDS = None
        self.CASHOUT_COORDS = None
        self.balance_coords = None

        # Bot settings (will be loaded from config or set from user input)
        self.initial_stake = self.config_manager.initial_stake
        self.max_stake = self.config_manager.max_stake
        self.target_multiplier = 2.0
        self.current_stake = self.initial_stake
        self.safety_margin = self.config_manager.safety_margin

        # Load previous session's stake if available
        self._load_stake_from_config()

        # Balance tracking
        self.last_balance = None
        self.hypothetical_balance = 10000.0  # For dry run mode
        
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
            "current_streak": 0,
            # Position 2 tracking
            "position2_bets_placed": 0,
            "position2_total_bet": 0,
            "position2_successful_cashouts": 0,
            "position2_failed_cashouts": 0,
            "position2_consecutive_losses": 0,
            "position2_enabled_for_round": False
        }
        
        # History tracking
        self.history_file = "aviator_rounds_history.csv"  # Use the same file as readregion.py
        self.prediction_history = deque(maxlen=10)
        self.history_tracker = RoundHistoryTracker()  # Initialize here
        self.logger = AviatorHistoryLogger(self.history_file)  # Use logger from readregion.py
        self._initialize_history_file()

        # 🎯 Position 2 Timer-based Conservative Engine
        self.position2_engine = None  # Will be initialized after config loaded

    def _load_stake_from_config(self):
        """Load the current stake from config file (persists across sessions)."""
        try:
            config = self.config_manager.get_config_dict()
            if 'current_stake' in config:
                self.current_stake = float(config['current_stake'])
                print(f"📈 Loaded stake from previous session: {self.current_stake}")
        except Exception as e:
            print(f"⚠️ Could not load stake from config: {e}, using initial stake")
            self.current_stake = self.initial_stake

    def _save_stake_to_config(self):
        """Save the current stake to config file for persistence."""
        try:
            self.config_manager.config['current_stake'] = str(self.current_stake)
            self.config_manager.save_config()
        except Exception as e:
            print(f"⚠️ Could not save stake to config: {e}")

    def _setup_logging(self):
        """Setup dual output to console and log file."""
        self.tee = TeeOutput(self.log_file)
        sys.stdout = self.tee
        print(f"\n{'='*80}")
        print(f"📝 LOGGING SESSION STARTED: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"📄 Log file: {self.log_file}")
        print(f"{'='*80}\n")

    def _initialize_history_file(self):
        """Initialize CSV history file if it doesn't exist."""
        if self.history_file and not os.path.exists(self.history_file):
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

    def _is_positive_run_cycle(self):
        """
        Determine if we're in a positive run cycle for Position 2 activation.

        Conditions for positive cycle:
        1. Current win streak >= positive_cycle_threshold (default 3)
        2. Recent profit positive (last 5 rounds average)

        Returns:
            bool: True if in positive cycle, False otherwise
        """
        try:
            # Check win streak condition
            if self.stats.get("current_streak", 0) >= self.config_manager.positive_cycle_threshold:
                return True

            # Check consecutive losses limit for Position 2
            pos2_losses = self.stats.get("position2_consecutive_losses", 0)
            if pos2_losses >= self.config_manager.position2_max_consecutive_losses:
                return False

            # Check if we have recent profitable rounds
            if len(self.prediction_history) >= 3:
                recent_avg_return = sum(
                    [p.get("return", 0) for p in list(self.prediction_history)[-5:]]
                ) / min(5, len(self.prediction_history))

                if recent_avg_return > 0:
                    return True

            return False

        except Exception as e:
            print(f"  ⚠️ Error in positive cycle detection: {e}")
            return False

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

    def validate_coordinates_continuous(self, duration=30):
        """
        Continuously read and log all coordinate values for validation.
        Useful for VM setup and debugging.

        Args:
            duration: How long to run validation (seconds)
        """
        print("\n" + "="*80)
        print("🔍 COORDINATE VALIDATION MODE")
        print("="*80)
        print(f"Running for {duration} seconds...")
        print("This will continuously log all coordinate readings.\n")

        import csv
        from datetime import datetime

        # Create validation log file
        validation_file = f"coordinate_validation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

        with open(validation_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                'Timestamp',
                'Multiplier_Reading',
                'Multiplier_Status',
                'Balance_Reading',
                'Balance_Raw_Text',
                'Region_Capture_Success',
                'Frame_Shape',
                'Coordinates_Summary'
            ])

        start_time = time.time()
        iteration = 0

        print("📊 Live Readings:")
        print("-" * 80)

        while time.time() - start_time < duration:
            iteration += 1
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]

            # Read multiplier
            mult_reading = "N/A"
            mult_status = "UNKNOWN"
            frame_shape = "N/A"
            capture_success = False

            try:
                frame = self.multiplier_reader.capture_region()
                if frame is not None:
                    capture_success = True
                    frame_shape = str(frame.shape)

                    # Try to read multiplier
                    value = self.multiplier_reader.fast_extract_multiplier_or_status(frame)
                    if value == "AWAITING NEXT FLIGHT":
                        mult_reading = "AWAITING"
                        mult_status = "AWAITING"
                    elif value:
                        mult_reading = f"{value:.2f}x" if isinstance(value, (int, float)) else str(value)
                        mult_status = "ACTIVE" if isinstance(value, (int, float)) else "TEXT"
            except Exception as e:
                mult_reading = f"ERROR: {str(e)[:30]}"
                mult_status = "ERROR"

            # Read balance
            balance_reading = "N/A"
            balance_raw = "N/A"

            try:
                import pyperclip
                if self.balance_coords:
                    x1, y1, x2, y2 = self.balance_coords
                    pyautogui.click((x1 + x2) // 2, (y1 + y2) // 2, clicks=3)
                    time.sleep(0.1)
                    pyautogui.hotkey('ctrl', 'c')
                    time.sleep(0.1)
                    balance_raw = pyperclip.paste().strip()

                    # Try to parse
                    if 'K' in balance_raw.upper():
                        match = re.search(r'([\d.]+)\s*K', balance_raw.upper())
                        if match:
                            balance_reading = f"{float(match.group(1)) * 1000:.2f}"
                    else:
                        match = re.search(r'([\d.]+)', balance_raw)
                        if match:
                            balance_reading = match.group(1)
            except Exception as e:
                balance_reading = f"ERROR: {str(e)[:30]}"

            # Coordinates summary
            coords_summary = f"Mult:[{self.config_manager.multiplier_region}] Bal:[{self.balance_coords}]"

            # Log to CSV
            with open(validation_file, 'a', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    timestamp,
                    mult_reading,
                    mult_status,
                    balance_reading,
                    balance_raw,
                    capture_success,
                    frame_shape,
                    coords_summary
                ])

            # Print to console (every iteration)
            print(f"[{iteration:3d}] {timestamp} | Mult: {mult_reading:12s} | Status: {mult_status:8s} | Bal: {balance_reading:10s} | Raw: '{balance_raw[:20]}'")

            time.sleep(0.5)  # Update every 500ms

        print("\n" + "="*80)
        print(f"✅ Validation complete! Log saved to: {validation_file}")
        print("="*80)
        return validation_file

    def initialize_components(self):
        """Initialize multiplier reader and detector with validation."""
        print("\n" + "="*80)
        print("🔧 INITIALIZING COMPONENTS")
        print("="*80)

        # Load coordinates from config
        if self.config_manager.multiplier_region:
            # Convert from tuple (x, y, width, height) to dict format
            x, y, w, h = self.config_manager.multiplier_region
            region_dict = {"left": x, "top": y, "width": w, "height": h}
            print(f"📍 Using multiplier region from config: {region_dict}")
        else:
            print("❌ No multiplier region configured!")
            return False

        # Set coordinates from config
        self.STAKE_COORDS = self.config_manager.stake_coords
        self.BET_BUTTON_COORDS = self.config_manager.bet_button_coords
        self.CASHOUT_COORDS = self.config_manager.cashout_coords
        self.balance_coords = self.config_manager.balance_region

        # Print all loaded coordinates for verification
        print("\n📋 Loaded Coordinates:")
        print(f"   Multiplier Region: {region_dict}")
        print(f"   Balance Region: {self.balance_coords}")
        print(f"   Stake Input: {self.STAKE_COORDS}")
        print(f"   Bet Button: {self.BET_BUTTON_COORDS}")
        print(f"   Cashout Button: {self.CASHOUT_COORDS}")
        
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
        
        # Initialize multiplier reader with logging disabled to avoid duplicate logging
        self.multiplier_reader = MultiplierReader(region_dict, enable_logging=False)

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

        # 🎯 Initialize Position 2 Timer-based Conservative Engine
        if self.config_manager.position2_enabled:
            try:
                self.position2_engine = Position2ConservativeEngine(self.config_manager)
                print("\n✅ Position 2 Timer Engine initialized")
                print(f"   Strategy: Timer-based conservative (1.2x-1.4x cashout)")
                print(f"   Green% threshold: {self.config_manager.position2_min_green_percent}%")
                print(f"   Red% threshold: {self.config_manager.position2_max_red_percent}%")
                print(f"   Timer interval: {self.config_manager.position2_timer_min}-{self.config_manager.position2_timer_max} rounds")
                print(f"   Lookback range: {self.config_manager.position2_lookback_min}-{self.config_manager.position2_lookback_max} rounds")
            except Exception as e:
                print(f"\n❌ Failed to initialize Position 2 engine: {e}")
                self.position2_engine = None
        else:
            print("\n⚠️  Position 2 disabled - only Position 1 will be active")

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
            
            automl_choice = input(f"\nUse AutoML predictions? (y/n, default: y): ").strip().lower()
            if automl_choice == 'n':
                self.use_automl_predictions = False
                print("   📊 AutoML predictions disabled")
            else:
                self.use_automl_predictions = True
                
                print("\n📋 SELECT MODELS TO USE:")
                print("   1. All models (default)")
                print("   2. Select specific models")
                
                model_choice = input("\nChoice (1/2, default: 1): ").strip()
                
                if model_choice == '2':
                    print("\nAvailable models:")
                    for i in range(1, 17):
                        print(f"   {i}. {MODEL_NAMES[i]}")
                    
                    print("\nEnter model numbers separated by commas (e.g., 1,2,5,10)")
                    print("Or press Enter to use all models")
                    
                    models_input = input("Models: ").strip()
                    
                    if models_input:
                        try:
                            self.selected_models = [int(x.strip()) for x in models_input.split(',')]
                            self.selected_models = [m for m in self.selected_models if 1 <= m <= 16]
                            
                            if not self.selected_models:
                                print("   ⚠️  Invalid selection, using all models")
                                self.selected_models = None
                            else:
                                print(f"   ✅ Selected {len(self.selected_models)} models:")
                                for m in self.selected_models:
                                    print(f"      - {MODEL_NAMES[m]}")
                        except:
                            print("   ⚠️  Invalid input, using all models")
                            self.selected_models = None
                    else:
                        self.selected_models = None
                else:
                    self.selected_models = None
                
                if self.selected_models:
                    print(f"   🤖 AutoML enabled with {len(self.selected_models)} selected models")
                else:
                    print(f"   🤖 AutoML enabled with all 16 models")

                # Update automl_predictor with selected models and config model_names
                self.automl_predictor = get_predictor(
                    selected_models=self.selected_models,
                    model_names=self.config_manager.model_names
                )
            
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
        """Read current balance from balance region with improved K suffix handling."""
        try:
            import pyperclip
            
            x1, y1, x2, y2 = self.balance_coords
            
            # Triple-click to select text
            pyautogui.click((x1 + x2) // 2, (y1 + y2) // 2, clicks=3)
            time.sleep(0.15)  # Slightly longer wait for selection
            
            # Copy to clipboard
            pyautogui.hotkey('ctrl', 'c')
            time.sleep(0.15)
            
            balance_text = pyperclip.paste().strip()
            
            if not balance_text:
                print("   ⚠️  Balance text empty")
                return None
            
            # Clean the text
            balance_text = balance_text.replace(',', '').replace(' ', '')
            
            print(f"   📊 Raw balance text: '{balance_text}'")
            
            # Handle K notation (e.g., "1.5K", "10.2K", "1K")
            if 'K' in balance_text.upper():
                # Match patterns like: 1.5K, 10K, 1.23K
                match = re.search(r'([\d.]+)\s*K', balance_text.upper())
                if match:
                    value = float(match.group(1)) * 1000
                    print(f"   💰 Parsed K value: {value:.2f}")
                    return value
                else:
                    print(f"   ⚠️  Could not parse K notation: '{balance_text}'")
            
            # Handle regular numbers (below 1000)
            match = re.search(r'([\d.]+)', balance_text)
            if match:
                value = float(match.group(1))
                print(f"   💰 Parsed regular value: {value:.2f}")
                return value
            
            print(f"   ⚠️  Could not parse balance: '{balance_text}'")
            return None
            
        except Exception as e:
            print(f"   ⚠️  Balance read error: {e}")
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
                        
                        # Wait for balance to update (give it more time)
                        print("   ⏳ Validating balance change...")
                        time.sleep(0.5)
                        new_balance = self._read_balance()

                        # Validate win by checking balance
                        if self.last_balance is not None and new_balance is not None:
                            balance_change = new_balance - self.last_balance
                            expected_profit = stake_used * (cashout_mult - 1)

                            # Debug logging
                            print(f"   📊 Balance before cashout: {self.last_balance:.2f}")
                            print(f"   📊 Balance after cashout: {new_balance:.2f}")
                            print(f"   📊 Change: {balance_change:+.2f} | Expected: {expected_profit:+.2f}")
                            print(f"   📊 Stake: {stake_used:.2f} | Multiplier: {cashout_mult:.2f}x")

                            # Win if balance increased (profit from cashout)
                            # We check if balance increased by at least 50% of stake (conservative check)
                            if balance_change > (stake_used * 0.5):
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
                                print(f"   ⚠️  Expected win but balance didn't increase enough!")
                                
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

    def _log_to_history(self, round_id, final_multiplier, cashout_multiplier, bet_placed, stake, profit_loss):
        """Log round results to CSV history"""
        try:
            import csv
            from pathlib import Path
            from datetime import datetime
            
            # Create history file if it doesn't exist
            history_file = Path('bet_history.csv')
            file_exists = history_file.exists()
            
            with open(history_file, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                
                # Write header if new file
                if not file_exists:
                    writer.writerow([
                        'Timestamp',
                        'Round ID',
                        'Final Multiplier',
                        'Cashout Multiplier',
                        'Bet Placed',
                        'Stake',
                        'Profit/Loss',
                        'Cumulative P/L'
                    ])
                
                # Calculate cumulative P/L from stats
                cumulative_pl = self.stats.get('total_profit', 0)
                
                # Write data
                writer.writerow([
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    round_id,
                    f"{final_multiplier:.2f}",
                    f"{cashout_multiplier:.2f}" if cashout_multiplier else "N/A",
                    "Yes" if bet_placed else "No",
                    f"{stake:.2f}" if stake else "0.00",
                    f"{profit_loss:+.2f}" if profit_loss else "0.00",
                    f"{cumulative_pl:+.2f}"
                ])
                
            print(f"✅ Logged round {round_id} to history")
            
        except Exception as e:
            print(f"⚠️ Failed to log to history: {e}")
            # Don't crash the bot if logging fails
            
    def run(self):
        """Main bot loop - logs ALL completed rounds to CSV with both cashout and final multipliers."""
        print("🚀 AVIATOR BOT STARTED")
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
                print(f"\n{'='*80}")
                print(f"🎮 ROUND #{round_number:03d}")
                print(f"{'='*80}")
                
                # ✨ GET AUTOML PREDICTIONS BEFORE ROUND STARTS
                if self.use_automl_predictions:
                    self.current_automl_prediction, self.current_automl_ensemble, self.current_automl_recommendation = self.get_automl_predictions()

                # Generate unique round_id based on timestamp with milliseconds
                from datetime import datetime
                self.current_round_id = datetime.now().strftime("%Y%m%d%H%M%S%f")[:17]  # YYYYMMDDHHMMSSmmm

                # Reset tracking for new round
                self.bet_placed_this_round = False
                
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
                final_mult = 0.0
                cashout_mult = 0.0

                # Step 1: Wait for AWAITING NEXT FLIGHT
                if not self._wait_for_awaiting_state():
                    print("⚠️  Skipping round - couldn't detect awaiting state")
                    # Log skipped round with zeros
                    self._log_to_history(
                        round_id=self.current_round_id,
                        final_multiplier=0.0,
                        cashout_multiplier=0.0,
                        bet_placed=False,
                        stake=0,
                        profit_loss=0.0
                    )
                    continue
                
                time.sleep(0.3)

                # Step 2: Pre-bet checks - determine if we should skip betting
                should_skip_bet = False
                
                if self._verify_game_running():
                    print("⚠️  Game already running - will observe only")
                    should_skip_bet = True
                elif self.bet_placed_this_round:
                    print("⚠️  Bet already placed for this round - observing")
                    should_skip_bet = True
                else:
                    # ✨ BETTING DECISION BASED ON CONFIGURED MODE
                    if self.use_automl_predictions and self.current_automl_recommendation:
                        betting_mode = self.config_manager.betting_mode.lower()

                        if betting_mode == "ml":
                            # ===== MODE: ML-BASED (Let ML decide when to bet) =====
                            # Check 1: ML Recommendation should_bet flag
                            if not self.current_automl_recommendation.get('should_bet', False):
                                print("🤖 ML Mode: ML says SKIP BET")
                                print(f"   Reason: Consensus: {self.current_automl_recommendation.get('consensus_range', 'N/A')}")
                                print(f"   Confidence: {self.current_automl_recommendation.get('confidence', 0):.1f}%")
                                print(f"   Risk Level: {self.current_automl_recommendation.get('risk_level', 'N/A')}")
                                should_skip_bet = True
                                round_result = "ML_SKIP"
                            else:
                                # ML says yes, will place bet below
                                pass

                        elif betting_mode == "user":
                            # ===== MODE: USER-SET (User threshold, ML picks multiplier) =====
                            if self.current_automl_prediction:
                                threshold = self.config_manager.min_prediction_threshold
                                min_required = self.config_manager.min_models_to_pass

                                passing = [p for p in self.current_automl_prediction if p.get('predicted_multiplier', 0) >= threshold]
                                failing = [p for p in self.current_automl_prediction if p.get('predicted_multiplier', 0) < threshold]

                                if len(passing) < min_required:
                                    print(f"🤖 User Mode: Insufficient Models Pass ({len(passing)}/{min_required} required): SKIP BET")
                                    print(f"   Threshold: {threshold:.2f}x | Required: {min_required} models")
                                    print()
                                    print("   Models PASSING:")
                                    for pred in passing:
                                        print(f"      {pred['model_name']}: {pred.get('predicted_multiplier', 0):.2f}x ✅")
                                    if failing:
                                        print()
                                        print("   Models FAILING:")
                                        for pred in failing:
                                            print(f"      {pred['model_name']}: {pred.get('predicted_multiplier', 0):.2f}x ❌")
                                    should_skip_bet = True
                                    round_result = "LOW_PRED"
                                else:
                                    # Enough models exceed threshold, continue to place bet
                                    pass

                        if not should_skip_bet and self.current_automl_prediction:
                            betting_mode = self.config_manager.betting_mode.lower()
                            threshold = self.config_manager.min_prediction_threshold
                            min_required = self.config_manager.min_models_to_pass
                            passing = [p for p in self.current_automl_prediction if p.get('predicted_multiplier', 0) >= threshold]

                            if betting_mode == "user":
                                print("🤖 User Mode: PLACE BET ✅")
                                print(f"   {len(passing)}/{len(self.current_automl_prediction)} models exceed threshold ({threshold:.2f}x):")
                                for pred in self.current_automl_prediction:
                                    mult = pred.get('predicted_multiplier', 0)
                                    status = "✅" if mult >= threshold else "❌"
                                    print(f"      {pred['model_name']}: {mult:.2f}x {status}")
                            else:
                                print("🤖 ML Mode: PLACE BET ✅")
                                for pred in self.current_automl_prediction:
                                    mult = pred.get('predicted_multiplier', 0)
                                    print(f"      {pred['model_name']}: {mult:.2f}x")

                            ml_target = self.current_automl_recommendation.get('target_multiplier', self.target_multiplier)
                            print(f"   Using Ensemble average: {ml_target:.2f}x ({len(self.current_automl_prediction)} models)")

                            # Apply safety margin (default 10%) and cap it reasonably
                            self.target_multiplier = max(1.5, min(ml_target * self.safety_margin, 5.0))
                            safety_pct = int((1 - self.safety_margin) * 100)
                            print(f"   Adjusted Target ({safety_pct}% safety margin): {self.target_multiplier:.2f}x")
                            print(f"   Confidence: {self.current_automl_recommendation.get('confidence', 0):.1f}%")
                            print(f"   Risk Level: {self.current_automl_recommendation.get('risk_level', 'N/A')}")
                
                # Step 3: Place bet only if not skipped
                if not should_skip_bet:
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

                            # ===== Position 2: High Multiplier Hunter =====
                            # Try to place Position 2 BEFORE waiting (faster!)
                            pos2_bet_placed = False
                            if self.config_manager.position2_enabled and self._is_positive_run_cycle():
                                print("\n" + "="*80)
                                print("🎯 Position 2: HIGH MULTIPLIER HUNTER - Positive Cycle Active!")
                                print("="*80)

                                try:
                                    from utils.betting_helpers import set_stake_verified_pos, place_bet_with_verification_pos

                                    # Set Position 2 stake (smaller amount) - FAST!
                                    pos2_stake = self.config_manager.position2_stake_amount
                                    pos2_set_success = set_stake_verified_pos(
                                        self.config_manager.position2_stake_coords,
                                        pos2_stake,
                                        position=2
                                    )

                                    if pos2_set_success:
                                        # Place Position 2 bet immediately - no extra delays!
                                        pos2_success, pos2_reason = place_bet_with_verification_pos(
                                            self.config_manager.position2_bet_button_coords,
                                            self.detector,
                                            self.stats,
                                            pos2_stake,
                                            position=2
                                        )

                                        if pos2_success:
                                            pos2_bet_placed = True
                                            self.stats["position2_enabled_for_round"] = True
                                            print("✅ Position 2 bet placed successfully!")
                                        else:
                                            print(f"❌ Position 2 bet failed: {pos2_reason}")
                                            self.stats["position2_consecutive_losses"] += 1
                                    else:
                                        print("❌ Failed to set Position 2 stake")
                                        self.stats["position2_consecutive_losses"] += 1

                                except Exception as e:
                                    print(f"⚠️ Position 2 error: {e}")
                                    import traceback
                                    traceback.print_exc()
                                    self.stats["position2_consecutive_losses"] += 1
                            else:
                                self.stats["position2_enabled_for_round"] = False
                                if not self.config_manager.position2_enabled:
                                    pass  # Position 2 disabled
                                elif not self._is_positive_run_cycle():
                                    print("\n⏸️ Position 2 inactive - not in positive run cycle")

                            # Now read balance and wait (Position 2 already placed!)
                            print("⏳ Waiting for bets to register...")
                            time.sleep(0.3)  # Minimal delay

                            # Update last_balance to current balance (after stake deduction)
                            current_balance = self._read_balance()
                            if current_balance is not None:
                                self.last_balance = current_balance
                                print(f"   💰 Balance after bets: {self.last_balance:.2f}")
                else:
                    # Skip betting - just observe
                    round_bet_placed = False
                    print("👁️  Skipping bet placement - will observe this round")
                    self.stats["position2_enabled_for_round"] = False

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
                        final_mult = 0.0
                        
                        print(f"\n❌ RESULT: BET CANCELLED")
                        print(f"   💸 Loss: {round_profit_loss:.2f}")
                        print(f"   📊 Cumulative P/L: {cumulative_profit:+.2f}")
                        
                        # Reset stake on cancelled bet
                        self.current_stake = reset_stake(self.initial_stake, self.stats)
                    
                    # Log to CSV even if we didn't bet
                    self._log_to_history(
                        round_id=self.current_round_id,
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

                    # ===== Position 2 Cashout Monitoring =====
                    if pos2_bet_placed:
                        print("\n" + "="*80)
                        print("🎯 Position 2: Monitoring for High Multiplier...")
                        print("="*80)

                        try:
                            from utils.betting_helpers import cashout_verified_pos

                            # Position 2 target multiplier (from config, default 10x)
                            pos2_target = self.config_manager.position2_target_multiplier

                            # Monitor Position 2 - let it ride longer for higher multiplier
                            # We'll use a simple strategy: try to cashout at target or wait for final crash
                            pos2_cashed_out = False
                            pos2_multiplier = 0.0
                            pos2_profit = 0.0

                            # Wait a bit longer than Position 1 (Position 2 targets higher multiples)
                            start_pos2_monitor = time.time()
                            pos2_timeout = 30  # Monitor for up to 30 seconds

                            while time.time() - start_pos2_monitor < pos2_timeout:
                                current_mult = self.multiplier_reader.get_latest_multiplier()

                                if current_mult and current_mult >= pos2_target and not pos2_cashed_out:
                                    # Try to cashout Position 2 at target
                                    print(f"🎯 Position 2 reached target: {current_mult:.2f}x >= {pos2_target:.2f}x")
                                    success, reason = cashout_verified_pos(
                                        self.config_manager.position2_cashout_coords,
                                        self.detector,
                                        position=2
                                    )

                                    if success:
                                        pos2_cashed_out = True
                                        pos2_multiplier = current_mult
                                        pos2_profit = self.config_manager.position2_stake_amount * (current_mult - 1)
                                        self.stats["position2_successful_cashouts"] += 1
                                        print(f"✅ Position 2 Cashout Success: +{pos2_profit:.2f} at {pos2_multiplier:.2f}x")
                                        print(f"   Return: {current_mult:.2f}x")
                                        self.stats["position2_consecutive_losses"] = 0  # Reset loss counter on win
                                        break
                                    else:
                                        print(f"⚠️ Position 2 cashout command sent but may not have executed")
                                        break

                                # Check if round ended
                                if not pos2_cashed_out and self.detector.is_awaiting_next_flight():
                                    print(f"💥 Position 2 round ended (crashed before reaching target)")
                                    final_mult_detected = self.multiplier_reader.last_valid_multiplier or 0.0
                                    if final_mult_detected > 0:
                                        pos2_multiplier = final_mult_detected
                                        pos2_profit = self.config_manager.position2_stake_amount * (final_mult_detected - 1)
                                        if final_mult_detected < 1.0:
                                            pos2_profit = -self.config_manager.position2_stake_amount
                                            self.stats["position2_failed_cashouts"] += 1
                                            self.stats["position2_consecutive_losses"] += 1
                                            print(f"❌ Position 2 Loss: -{self.config_manager.position2_stake_amount:.2f} (crashed at {final_mult_detected:.2f}x)")
                                        else:
                                            self.stats["position2_successful_cashouts"] += 1
                                            self.stats["position2_consecutive_losses"] = 0
                                            print(f"✅ Position 2 Profit: +{pos2_profit:.2f} (caught at {final_mult_detected:.2f}x)")
                                    break

                                time.sleep(0.1)

                            if not pos2_cashed_out:
                                # Timeout or round ended without positioning
                                print("⏱️ Position 2 monitoring timeout")
                                self.stats["position2_failed_cashouts"] += 1
                                self.stats["position2_consecutive_losses"] += 1

                        except Exception as e:
                            print(f"⚠️ Position 2 cashout error: {e}")
                            import traceback
                            traceback.print_exc()
                            self.stats["position2_failed_cashouts"] += 1
                            self.stats["position2_consecutive_losses"] += 1

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
                            self._save_stake_to_config()  # Persist stake increase
                    else:
                        old_stake = self.current_stake
                        self.current_stake = reset_stake(self.initial_stake, self.stats)
                        if self.current_stake < old_stake:
                            print(f"   📉 Stake reset: {old_stake} → {self.current_stake}")
                            self._save_stake_to_config()  # Persist stake reset
                else:
                    # No bet placed - just observe the round
                    print("👁️  Observing round (no bet placed)...")
                    crashed, final_mult = self._wait_for_crash_and_read_multiplier(timeout=60)
                    
                    if crashed and final_mult and final_mult > 0:
                        print(f"   💥 Round ended at {final_mult:.2f}x (observed)")
                        round_result = "OBSERVED" if round_result != "ML_SKIP" else "ML_SKIP"
                        self.stats["rounds_observed"] = self.stats.get("rounds_observed", 0) + 1
                        self.round_state["completed"] = True
                    else:
                        # Try to get from round state if available
                        if self.round_state["final_multiplier"] > 0:
                            final_mult = self.round_state["final_multiplier"]
                            print(f"   💥 Round ended at {final_mult:.2f}x (observed via state)")
                            round_result = "OBSERVED" if round_result != "ML_SKIP" else "ML_SKIP"
                            self.stats["rounds_observed"] = self.stats.get("rounds_observed", 0) + 1
                            self.round_state["completed"] = True
                        else:
                            print(f"   ⚠️  Could not detect round end")
                            final_mult = 0.0
                            round_result = "OBSERVATION_TIMEOUT"

                # CRITICAL: Use round_state as the source of truth for final multiplier
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
                    
                    # ✨ LOG AUTOML PERFORMANCE
                    if self.current_automl_prediction and self.current_automl_ensemble and self.current_automl_recommendation:
                        add_round_result(
                            final_multiplier_to_log,
                            round_id=self.current_round_id,  # Use timestamp-based round_id
                            predictions=self.current_automl_prediction,
                            ensemble=self.current_automl_ensemble,
                            recommendation=self.current_automl_recommendation
                        )
                
                # Log to CSV with validated multipliers
                if final_multiplier_to_log > 0:
                    self.logger.log_round(final_multiplier_to_log)

                # Reset for next round
                self.multiplier_reader.reset()
                self.bet_placed_this_round = False
                time.sleep(0.2)

        except KeyboardInterrupt:
            print("\n\n⛔ Bot stopped by user.")
            self.print_final_stats(cumulative_profit)
            self._cleanup_logging()
        except Exception as e:
            print(f"\n\n❌ Unexpected error: {e}")
            import traceback
            traceback.print_exc()
            self.print_final_stats(cumulative_profit)
            self._cleanup_logging()

    def _cleanup_logging(self):
        """Restore stdout and close log file."""
        # Cleanup MSS capture context to prevent "unable to auto-find suitable render" error
        if self.multiplier_reader is not None:
            try:
                if hasattr(self.multiplier_reader, 'sct') and self.multiplier_reader.sct is not None:
                    self.multiplier_reader.sct.close()
                    print("✅ Closed MSS capture context")
            except Exception as e:
                print(f"⚠️  Error closing MSS context: {e}")

        if self.tee:
            print(f"\n{'='*80}")
            print(f"📝 LOGGING SESSION ENDED: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"📄 Full log saved to: {self.log_file}")
            print(f"{'='*80}\n")
            sys.stdout = self.tee.terminal
            self.tee.close()


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
    print("   4. VALIDATE COORDINATES - Test coordinate readings (VM setup)")

    mode_choice = input("\nChoice (1/2/3/4, default: 1): ").strip()

    if mode_choice == '2':
        mode = 'dry_run'
        print("\n🧪 DRY RUN MODE selected - No real bets will be placed")
    elif mode_choice == '3':
        mode = 'observation'
        print("\n📊 OBSERVATION MODE selected - Data collection only")
    elif mode_choice == '4':
        mode = 'validation'
        print("\n🔍 VALIDATION MODE selected - Testing coordinate readings")
    else:
        mode = 'live'
        print("\n🚀 LIVE MODE selected - Real betting")

    bot = AviatorBot(mode=mode if mode != 'validation' else 'observation')

    # Setup or load configuration
    if bot.config_manager.load_config() and bot.config_manager.multiplier_region:
        print(f"\n✅ Configuration loaded")

        if mode == 'validation':
            # In validation mode, show coordinates and offer to run test
            print("\n📍 Current Configuration:")
            config = bot.config_manager.get_config_dict()
            print(f"   Multiplier Region: {config['multiplier_region']}")
            print(f"   Balance Region: {config['balance_region']}")
            print(f"   Stake Coords: {config['stake_coords']}")
            print(f"   Bet Button: {config['bet_button_coords']}")
            print(f"   Cashout Button: {config['cashout_coords']}")

            print("\nOptions:")
            print("  1. Run validation with current coordinates")
            print("  2. Reconfigure coordinates first")
            choice = input("\nChoice (1/2): ").strip()

            if choice == '2':
                bot.config_manager.setup_coordinates()
        else:
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

    # ✨ Initialize AutoML predictor with config-loaded selected_models and model_names
    bot.automl_predictor = get_predictor(
        selected_models=bot.config_manager.selected_models,
        model_names=bot.config_manager.model_names
    )

    # Initialize components with validation
    if not bot.initialize_components():
        print("\n❌ Failed to initialize components. Exiting.")
        return

    # If validation mode, run coordinate validation
    if mode == 'validation':
        print("\n" + "="*80)
        print("🔍 COORDINATE VALIDATION MODE")
        print("="*80)
        print("\nThis mode will continuously read and log:")
        print("  • Multiplier values")
        print("  • Balance values")
        print("  • Frame capture status")
        print("  • All coordinate positions")
        print("\nPerfect for VM setup and debugging!")

        duration_input = input("\nValidation duration in seconds (default: 30): ").strip()
        duration = int(duration_input) if duration_input else 30

        print(f"\n🎬 Starting {duration} second validation...")
        print("Make sure the game window is visible!\n")

        time.sleep(2)  # Give user time to position window

        validation_file = bot.validate_coordinates_continuous(duration)

        print(f"\n✅ Validation complete!")
        print(f"📄 CSV log saved to: {validation_file}")
        print("\nReview the CSV file to verify all coordinates are reading correctly.")
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


# ============================================================================
# HELPER FUNCTIONS FOR AUTOML INTEGRATION (From patched version)
# ============================================================================

def _range_band(label: str):
    """Map qualitative range labels to numeric [min, max] bands"""
    mapping = {
        'LOW': (1.00, 1.30),
        'MEDIUM-LOW': (1.30, 1.80),
        'MEDIUM': (1.80, 2.60),
        'MEDIUM-HIGH': (2.60, 3.80),
        'HIGH': (3.80, 999.0),
    }
    return mapping.get(label.upper(), (1.00, 999.0))


def build_model_table(predictions):
    """Return a list of dict rows for logging model predictions as a table"""
    rows = []
    for p in predictions:
        mn, mx = _range_band(p.get('predicted_range', 'LOW'))
        rows.append({
            'Model': p.get('model_name'),
            'Expected x': round(float(p.get('predicted_multiplier', 0.0)), 2),
            'Range': p.get('predicted_range', 'LOW'),
            'Range Min': mn,
            'Range Max': mx,
            'Confidence': f"{int(p.get('confidence', 0))}%"
        })
    return rows


def print_model_table(rows):
    """Pretty-print model predictions in aligned columns"""
    if not rows:
        return ""
    headers = list(rows[0].keys())
    widths = {h: max(len(h), max(len(str(r.get(h, ''))) for r in rows)) for h in headers}
    out = []
    out.append(" " + " | ".join(h.ljust(widths[h]) for h in headers))
    out.append("-" * (len(out[0])))
    for r in rows:
        out.append(" " + " | ".join(str(r.get(h, '')).ljust(widths[h]) for h in headers))
    return "\n".join(out)


def all_models_meet_target(model_rows, user_target):
    """Ensure all models' expected multipliers and ranges exceed user target"""
    try:
        target = float(user_target)
    except:
        target = 1.5
    for row in model_rows:
        pred = float(row.get('Expected x', 0))
        rmax = float(row.get('Range Max', 999.0))
        # model must expect at least the target; also its range's upper bound should be >= target
        if pred < target or rmax < target:
            return False  # Don't bet if not all models meet target
    return True


def log_pattern_hypotheses(automl_predictor, history_tracker):
    """Display upcoming pattern hypotheses in tabular format"""
    try:
        recent = list(history_tracker.get_recent_final_multipliers(limit=200))
    except Exception:
        recent = []

    if not recent or len(recent) == 0:
        print("[PATTERNS] Insufficient data for pattern detection")
        return []

    patterns = automl_predictor.detect_patterns(recent)

    headers = ['Pattern', 'Expected Range', 'Confidence']
    widths = {h: max(len(h), max(len(str(p[h])) for p in patterns)) for h in headers}
    print("\n[PATTERNS] Upcoming hypotheses (top 5):")
    print(" " + " | ".join(h.ljust(widths[h]) for h in headers))
    print("-" * (sum(widths.values()) + 6))
    for p in patterns:
        print(" " + " | ".join(str(p[h]).ljust(widths[h]) for h in headers))
    print()
    return patterns


if __name__ == "__main__":
    main()