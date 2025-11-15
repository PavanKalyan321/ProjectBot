"""Configuration management for Aviator Bot."""

import json
import os
import time
import pyautogui
import keyboard


class ConfigManager:
    """Manages bot configuration including coordinates and settings."""
    
    def __init__(self, config_file="aviator_ml_config.json"):
        """
        Initialize configuration manager.

        Args:
            config_file: Path to configuration file
        """
        self.config_file = config_file
        # Position 1 (Main)
        self.stake_coords = None
        self.bet_button_coords = None
        self.cashout_coords = None
        # Position 2 (High Multiplier Hunter)
        self.position2_enabled = False
        self.position2_stake_coords = None
        self.position2_bet_button_coords = None
        self.position2_cashout_coords = None
        self.position2_stake_amount = 5
        self.position2_target_multiplier = 10.0
        # General settings
        self.multiplier_region = None
        self.balance_region = None  # NEW: Balance region
        self.history_region = None
        self.cashout_delay = 2.0
        self.initial_stake = 25
        self.max_stake = 1000
        self.stake_increase_percent = 20
        self.safety_margin = 0.9  # NEW: Safety margin (10% reduction)
        self.positive_cycle_threshold = 3  # Win streak needed to activate Position 2
        self.position2_max_consecutive_losses = 3  # Disable Position 2 after 3 losses
        self.verbose_mode = False  # Enable/disable verbose logging
        self.clean_output = True  # Minimal console output
        self.betting_mode = "ml"  # "ml" = ML decides both bet and multiplier, "user" = User sets threshold
        self.min_prediction_threshold = 1.5  # Minimum multiplier all models must predict (for "user" mode)
        self.min_models_to_pass = 2  # Minimum number of models that must exceed threshold (for "user" mode)
        # Model selection for predictions
        self.selected_models = None  # List of model names to display
        self.model_names = {}  # Mapping of model names for display

    def save_config(self):
        """Save configuration to JSON file."""
        config = {
            "position1": {
                "stake_coords": list(self.stake_coords) if self.stake_coords else None,
                "bet_button_coords": list(self.bet_button_coords) if self.bet_button_coords else None,
                "cashout_coords": list(self.cashout_coords) if self.cashout_coords else None
            },
            "position2": {
                "enabled": self.position2_enabled,
                "stake_coords": list(self.position2_stake_coords) if self.position2_stake_coords else None,
                "bet_button_coords": list(self.position2_bet_button_coords) if self.position2_bet_button_coords else None,
                "cashout_coords": list(self.position2_cashout_coords) if self.position2_cashout_coords else None,
                "stake_amount": self.position2_stake_amount,
                "target_multiplier": self.position2_target_multiplier
            },
            "multiplier_region": list(self.multiplier_region) if self.multiplier_region else None,
            "balance_region": list(self.balance_region) if self.balance_region else None,
            "history_region": list(self.history_region) if self.history_region else None,
            "cashout_delay": self.cashout_delay,
            "initial_stake": self.initial_stake,
            "max_stake": self.max_stake,
            "stake_increase_percent": self.stake_increase_percent,
            "safety_margin": self.safety_margin,
            "positive_cycle_threshold": self.positive_cycle_threshold,
            "position2_max_consecutive_losses": self.position2_max_consecutive_losses,
            "verbose_mode": self.verbose_mode,
            "clean_output": self.clean_output,
            "betting_mode": self.betting_mode,
            "min_prediction_threshold": self.min_prediction_threshold,
            "min_models_to_pass": self.min_models_to_pass,
            "selected_models": self.selected_models,
            "model_names": self.model_names
        }

        try:
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving config: {e}")
            return False
    
    def load_config(self):
        """
        Load configuration from JSON file.

        Returns:
            bool: True if successful, False otherwise
        """
        if not os.path.exists(self.config_file):
            return False

        try:
            with open(self.config_file, 'r') as f:
                config = json.load(f)

            # Load Position 1 coordinates (support both old and new format)
            if "position1" in config:
                pos1 = config["position1"]
                self.stake_coords = tuple(pos1["stake_coords"]) if pos1.get("stake_coords") else None
                self.bet_button_coords = tuple(pos1["bet_button_coords"]) if pos1.get("bet_button_coords") else None
                self.cashout_coords = tuple(pos1["cashout_coords"]) if pos1.get("cashout_coords") else None
            else:
                # Backward compatibility: old format without position1 key
                self.stake_coords = tuple(config["stake_coords"]) if config.get("stake_coords") else None
                self.bet_button_coords = tuple(config["bet_button_coords"]) if config.get("bet_button_coords") else None
                self.cashout_coords = tuple(config["cashout_coords"]) if config.get("cashout_coords") else None

            # Load Position 2 coordinates and settings
            if "position2" in config:
                pos2 = config["position2"]
                self.position2_enabled = pos2.get("enabled", False)
                self.position2_stake_coords = tuple(pos2["stake_coords"]) if pos2.get("stake_coords") else None
                self.position2_bet_button_coords = tuple(pos2["bet_button_coords"]) if pos2.get("bet_button_coords") else None
                self.position2_cashout_coords = tuple(pos2["cashout_coords"]) if pos2.get("cashout_coords") else None
                self.position2_stake_amount = pos2.get("stake_amount", 5)
                self.position2_target_multiplier = pos2.get("target_multiplier", 10.0)

            # Load general settings
            self.multiplier_region = tuple(config["multiplier_region"]) if config.get("multiplier_region") else None
            self.balance_region = tuple(config["balance_region"]) if config.get("balance_region") else None
            self.history_region = tuple(config["history_region"]) if config.get("history_region") else None
            self.cashout_delay = config.get("cashout_delay", 2.0)
            self.initial_stake = config.get("initial_stake", 25)
            self.max_stake = config.get("max_stake", 1000)
            self.stake_increase_percent = config.get("stake_increase_percent", 20)
            self.safety_margin = config.get("safety_margin", 0.9)
            self.positive_cycle_threshold = config.get("positive_cycle_threshold", 3)
            self.position2_max_consecutive_losses = config.get("position2_max_consecutive_losses", 3)
            self.verbose_mode = config.get("verbose_mode", False)
            self.clean_output = config.get("clean_output", True)
            self.betting_mode = config.get("betting_mode", "ml")
            self.min_prediction_threshold = config.get("min_prediction_threshold", 1.5)
            self.min_models_to_pass = config.get("min_models_to_pass", 2)

            # Load model selection
            self.selected_models = config.get("selected_models")
            self.model_names = config.get("model_names", {})

            return True
        except Exception as e:
            print(f"Error loading config: {e}")
            return False
    
    def setup_coordinates(self):
        """Interactive coordinate setup using keyboard input."""
        print("\n" + "="*60)
        print("COORDINATE SETUP")
        print("="*60)
        print("\nPosition your mouse and press SPACE\n")

        print("1. Hover over STAKE INPUT field...")
        keyboard.wait('space')
        self.stake_coords = pyautogui.position()
        print(f"   ✓ Stake input: {self.stake_coords}")
        time.sleep(0.5)

        print("\n2. Hover over PLACE BET button...")
        keyboard.wait('space')
        self.bet_button_coords = pyautogui.position()
        print(f"   ✓ Place bet button: {self.bet_button_coords}")
        time.sleep(0.5)

        print("\n3. Hover over CASHOUT button location...")
        keyboard.wait('space')
        self.cashout_coords = pyautogui.position()
        print(f"   ✓ Cashout button: {self.cashout_coords}")
        time.sleep(0.5)

        print("\n4. Define multiplier region (TOP-LEFT corner)...")
        keyboard.wait('space')
        x1, y1 = pyautogui.position()
        print(f"   ✓ Top-left: ({x1}, {y1})")
        time.sleep(0.5)

        print("\n   Define multiplier region (BOTTOM-RIGHT corner)...")
        keyboard.wait('space')
        x2, y2 = pyautogui.position()
        print(f"   ✓ Bottom-right: ({x2}, {y2})")
        self.multiplier_region = (x1, y1, x2-x1, y2-y1)
        print(f"\n✓ Multiplier region: {self.multiplier_region}")

        print("\n5. Define BALANCE region (TOP-LEFT corner)...")
        keyboard.wait('space')
        b1, b2 = pyautogui.position()
        print(f"   ✓ Balance top-left: ({b1}, {b2})")
        time.sleep(0.5)

        print("\n   Define BALANCE region (BOTTOM-RIGHT corner)...")
        keyboard.wait('space')
        b3, b4 = pyautogui.position()
        print(f"   ✓ Balance bottom-right: ({b3}, {b4})")
        self.balance_region = (b1, b2, b3, b4)
        print(f"\n✓ Balance region: {self.balance_region}")

        print("\n6. Define ROUND HISTORY bar (TOP-LEFT corner)...")
        keyboard.wait('space')
        h1, h2 = pyautogui.position()
        print(f"   ✓ History top-left: ({h1}, {h2})")
        time.sleep(0.5)

        print("\n   Define ROUND HISTORY bar (BOTTOM-RIGHT corner)...")
        keyboard.wait('space')
        h3, h4 = pyautogui.position()
        print(f"   ✓ History bottom-right: ({h3}, {h4})")
        self.history_region = (h1, h2, h3-h1, h4-h2)
        print(f"\n✓ History region: {self.history_region}")

        self.save_config()

        print("\n" + "="*60)
        print("✓ Setup complete!")
        print("="*60 + "\n")
    
    def get_config_dict(self):
        """
        Get configuration as dictionary.

        Returns:
            dict: Configuration dictionary
        """
        return {
            "position1": {
                "stake_coords": self.stake_coords,
                "bet_button_coords": self.bet_button_coords,
                "cashout_coords": self.cashout_coords
            },
            "position2": {
                "enabled": self.position2_enabled,
                "stake_coords": self.position2_stake_coords,
                "bet_button_coords": self.position2_bet_button_coords,
                "cashout_coords": self.position2_cashout_coords,
                "stake_amount": self.position2_stake_amount,
                "target_multiplier": self.position2_target_multiplier
            },
            "multiplier_region": self.multiplier_region,
            "balance_region": self.balance_region,
            "history_region": self.history_region,
            "cashout_delay": self.cashout_delay,
            "initial_stake": self.initial_stake,
            "max_stake": self.max_stake,
            "stake_increase_percent": self.stake_increase_percent,
            "safety_margin": self.safety_margin,
            "positive_cycle_threshold": self.positive_cycle_threshold,
            "position2_max_consecutive_losses": self.position2_max_consecutive_losses
        }
