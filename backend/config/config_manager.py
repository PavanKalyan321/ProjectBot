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
        self.stake_coords = None
        self.bet_button_coords = None
        self.cashout_coords = None
        self.multiplier_region = None
        self.history_region = None
        self.cashout_delay = 2.0
        self.initial_stake = 25
        self.max_stake = 1000
        self.stake_increase_percent = 20
    
    def save_config(self):
        """Save configuration to JSON file."""
        config = {
            "stake_coords": self.stake_coords,
            "bet_button_coords": self.bet_button_coords,
            "cashout_coords": self.cashout_coords,
            "multiplier_region": self.multiplier_region,
            "history_region": self.history_region,
            "cashout_delay": self.cashout_delay,
            "initial_stake": self.initial_stake,
            "max_stake": self.max_stake,
            "stake_increase_percent": self.stake_increase_percent
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
            
            self.stake_coords = tuple(config["stake_coords"]) if config.get("stake_coords") else None
            self.bet_button_coords = tuple(config["bet_button_coords"]) if config.get("bet_button_coords") else None
            self.cashout_coords = tuple(config["cashout_coords"]) if config.get("cashout_coords") else None
            self.multiplier_region = tuple(config["multiplier_region"]) if config.get("multiplier_region") else None
            self.history_region = tuple(config["history_region"]) if config.get("history_region") else None
            self.cashout_delay = config.get("cashout_delay", 2.0)
            self.initial_stake = config.get("initial_stake", 25)
            self.max_stake = config.get("max_stake", 1000)
            self.stake_increase_percent = config.get("stake_increase_percent", 20)
            
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
        
        print("\n5. Define ROUND HISTORY bar (TOP-LEFT corner)...")
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
            "stake_coords": self.stake_coords,
            "bet_button_coords": self.bet_button_coords,
            "cashout_coords": self.cashout_coords,
            "multiplier_region": self.multiplier_region,
            "history_region": self.history_region,
            "cashout_delay": self.cashout_delay,
            "initial_stake": self.initial_stake,
            "max_stake": self.max_stake,
            "stake_increase_percent": self.stake_increase_percent
        }
