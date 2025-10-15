import pyautogui
import time
from PIL import Image
import cv2
import numpy as np
import keyboard
import json
import os
import re
from datetime import datetime

class GameStateDetector:
    """Detect game states: Awaiting, Active, Crashed"""
    
    def __init__(self, region):
        self.region = region  # (x, y, width, height)
        
        # Import tesseract
        try:
            import pytesseract
            self.pytesseract = pytesseract
            self.tesseract_available = True
        except ImportError:
            print("⚠️  Warning: pytesseract not installed. Install with: pip install pytesseract")
            self.tesseract_available = False
    
    def capture_region(self):
        """Capture screenshot of multiplier region"""
        screenshot = pyautogui.screenshot(region=self.region)
        return screenshot
    
    def read_text_in_region(self):
        """Read any text in the multiplier region"""
        if not self.tesseract_available:
            return None
        
        try:
            # Capture image
            image = self.capture_region()
            img_array = np.array(image)
            
            # Convert to grayscale
            gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
            
            # Try multiple preprocessing methods
            methods = []
            
            # Method 1: Simple threshold
            _, thresh1 = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)
            methods.append(thresh1)
            
            # Method 2: Inverted threshold
            _, thresh2 = cv2.threshold(gray, 100, 255, cv2.THRESH_BINARY_INV)
            methods.append(thresh2)
            
            # Method 3: Adaptive threshold
            thresh3 = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                           cv2.THRESH_BINARY, 11, 2)
            methods.append(thresh3)
            
            # Try OCR on each preprocessed image
            for processed in methods:
                text = self.pytesseract.image_to_string(processed, config='--oem 3 --psm 6')
                
                if text:
                    text = text.strip().upper()
                    text = text.replace('0', 'O').replace('1', 'I')
                    
                    if any(keyword in text for keyword in ['AWAITING', 'AWAIT', 'NEXT', 'FLIGHT']):
                        return 'AWAITING'
            
            # Check if multiplier is visible (white/bright colors = game active)
            hsv = cv2.cvtColor(img_array, cv2.COLOR_RGB2HSV)
            lower_white = np.array([0, 0, 200])
            upper_white = np.array([180, 30, 255])
            mask = cv2.inRange(hsv, lower_white, upper_white)
            white_pixels = cv2.countNonZero(mask)
            total_pixels = mask.shape[0] * mask.shape[1]
            white_ratio = white_pixels / total_pixels
            
            # If significant white text is visible, game is likely active
            if white_ratio > 0.1:
                return 'ACTIVE'
            
            return 'UNKNOWN'
            
        except Exception as e:
            return None
    
    def is_awaiting_next_flight(self):
        """Check if 'AWAITING NEXT FLIGHT' message is displayed"""
        state = self.read_text_in_region()
        return state == 'AWAITING'
    
    def is_game_active(self):
        """Check if game round is active"""
        state = self.read_text_in_region()
        return state == 'ACTIVE'
    
    def wait_for_awaiting_message(self, timeout=60):
        """Wait for 'AWAITING NEXT FLIGHT' message"""
        print("  Waiting for 'AWAITING NEXT FLIGHT'...")
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            if self.is_awaiting_next_flight():
                print("  ✓ 'AWAITING NEXT FLIGHT' detected!")
                return True
            
            time.sleep(0.5)
        
        print("  ⚠️  Timeout - message not detected")
        return False
    
    def wait_for_game_start(self, timeout=10):
        """Wait for game to start (white multiplier appears)"""
        print("  Waiting for game to start...")
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            if self.is_game_active():
                print("  ✓ Game started!")
                return True
            
            time.sleep(0.2)
        
        print("  ⚠️  Game didn't start")
        return False


class AviatorBot:
    """Aviator bot using timer-based cashout"""
    
    def __init__(self):
        self.stake_coords = None
        self.bet_button_coords = None
        self.cashout_coords = None
        self.multiplier_region = None
        
        self.initial_stake = 25
        self.current_stake = 25
        self.max_stake = 1000
        self.stake_increase_percent = 20  # Increase by 20% on win
        
        self.cashout_delay = 2.0  # Cashout after X seconds
        self.is_betting = False
        
        self.detector = None
        self.config_file = "aviator_config.json"
        
        # Statistics
        self.stats = {
            "rounds_played": 0,
            "successful_cashouts": 0,
            "failed_cashouts": 0,
            "total_bet": 0,
            "total_return": 0,
            "current_streak": 0,
            "max_stake_reached": 25
        }
    
    def save_config(self):
        """Save configuration to file"""
        config = {
            "stake_coords": self.stake_coords,
            "bet_button_coords": self.bet_button_coords,
            "cashout_coords": self.cashout_coords,
            "multiplier_region": self.multiplier_region,
            "cashout_delay": self.cashout_delay,
            "initial_stake": self.initial_stake,
            "max_stake": self.max_stake,
            "stake_increase_percent": self.stake_increase_percent
        }
        with open(self.config_file, 'w') as f:
            json.dump(config, f, indent=2)
        print("✓ Configuration saved!")
    
    def load_config(self):
        """Load configuration from file"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                
                self.stake_coords = tuple(config["stake_coords"]) if config.get("stake_coords") else None
                self.bet_button_coords = tuple(config["bet_button_coords"]) if config.get("bet_button_coords") else None
                self.cashout_coords = tuple(config["cashout_coords"]) if config.get("cashout_coords") else None
                self.multiplier_region = tuple(config["multiplier_region"]) if config.get("multiplier_region") else None
                self.cashout_delay = config.get("cashout_delay", 2.0)
                self.initial_stake = config.get("initial_stake", 25)
                self.max_stake = config.get("max_stake", 1000)
                self.stake_increase_percent = config.get("stake_increase_percent", 20)
                self.current_stake = self.initial_stake
                
                print("✓ Configuration loaded!")
                return True
            except Exception as e:
                print(f"⚠️  Error loading config: {e}")
                return False
        return False
    
    def setup_coordinates(self):
        """Interactive setup to capture screen coordinates"""
        print("\n" + "="*60)
        print("COORDINATE SETUP")
        print("="*60)
        print("\nPosition your mouse over each element and press SPACE\n")
        
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
        
        print("\n4. Define multiplier region (for detecting 'AWAITING NEXT FLIGHT'):")
        print("   Hover over TOP-LEFT corner of the text area...")
        keyboard.wait('space')
        x1, y1 = pyautogui.position()
        print(f"   ✓ Top-left: ({x1}, {y1})")
        time.sleep(0.5)
        
        print("\n   Hover over BOTTOM-RIGHT corner of the text area...")
        keyboard.wait('space')
        x2, y2 = pyautogui.position()
        print(f"   ✓ Bottom-right: ({x2}, {y2})")
        
        self.multiplier_region = (x1, y1, x2-x1, y2-y1)
        print(f"\n✓ Region: {self.multiplier_region}")
        
        # Initialize detector
        self.detector = GameStateDetector(self.multiplier_region)
        
        # Save configuration
        self.save_config()
        
        print("\n" + "="*60)
        print("✓ Setup complete!")
        print("="*60 + "\n")
    
    def test_detection(self, duration=15):
        """Test the awaiting message detection"""
        if not self.detector:
            if self.multiplier_region:
                self.detector = GameStateDetector(self.multiplier_region)
            else:
                print("❌ Multiplier region not configured!")
                return
        
        print(f"\n🔍 Testing detection for {duration} seconds...")
        print("Watch the game go through: AWAITING → ACTIVE → CRASHED\n")
        
        input("Press Enter to start test...")
        
        start_time = time.time()
        awaiting_count = 0
        active_count = 0
        
        try:
            while time.time() - start_time < duration:
                state = self.detector.read_text_in_region()
                
                if state == 'AWAITING':
                    awaiting_count += 1
                    print(f"✓ AWAITING detected", end='   \r')
                elif state == 'ACTIVE':
                    active_count += 1
                    print(f"✓ ACTIVE (game running)", end='   \r')
                else:
                    print(f"• Checking...", end='   \r')
                
                time.sleep(0.5)
        
        except KeyboardInterrupt:
            print("\n\nTest stopped by user")
        
        print("\n\n" + "="*60)
        print("TEST RESULTS")
        print("="*60)
        print(f"'AWAITING' detections:  {awaiting_count}")
        print(f"'ACTIVE' detections:    {active_count}")
        print("="*60 + "\n")
    
    def set_stake(self, amount):
        """Set stake amount in the input field"""
        try:
            pyautogui.click(self.stake_coords)
            time.sleep(0.2)
            
            # Clear existing value
            pyautogui.hotkey('ctrl', 'a')
            time.sleep(0.1)
            pyautogui.press('backspace')
            time.sleep(0.1)
            
            # Type new amount
            pyautogui.typewrite(str(amount), interval=0.05)
            time.sleep(0.2)
        except Exception as e:
            print(f"⚠️  Error setting stake: {e}")
    
    def place_bet(self):
        """Click place bet button"""
        try:
            pyautogui.click(self.bet_button_coords)
            self.is_betting = True
            self.stats["rounds_played"] += 1
            self.stats["total_bet"] += self.current_stake
            print(f"✓ Bet placed: {self.current_stake} | Round: {self.stats['rounds_played']}")
        except Exception as e:
            print(f"⚠️  Error placing bet: {e}")
    
    def cashout(self):
        """Click cashout button"""
        try:
            pyautogui.click(self.cashout_coords)
            self.is_betting = False
            self.stats["successful_cashouts"] += 1
            self.stats["current_streak"] += 1
            print(f"✓ CASHED OUT after {self.cashout_delay}s")
        except Exception as e:
            print(f"⚠️  Error cashing out: {e}")
            self.stats["failed_cashouts"] += 1
    
    def increase_stake(self):
        """Increase stake by percentage after successful cashout"""
        old_stake = self.current_stake
        
        # Calculate new stake with percentage increase
        new_stake = self.current_stake * (1 + self.stake_increase_percent / 100)
        
        # Cap at max stake
        if new_stake > self.max_stake:
            new_stake = self.max_stake
        
        self.current_stake = int(new_stake)
        
        # Track max stake reached
        if self.current_stake > self.stats["max_stake_reached"]:
            self.stats["max_stake_reached"] = self.current_stake
        
        if self.current_stake != old_stake:
            print(f"  💰 Stake increased: {old_stake} → {self.current_stake} (+{self.stake_increase_percent}%)")
            
            if self.current_stake >= self.max_stake:
                print(f"  🎯 MAX STAKE REACHED: {self.max_stake}")
        else:
            print(f"  🎯 At MAX STAKE: {self.max_stake}")
    
    def reset_stake(self):
        """Reset stake to initial amount after a loss"""
        old_stake = self.current_stake
        self.current_stake = self.initial_stake
        self.stats["current_streak"] = 0
        
        if old_stake != self.current_stake:
            print(f"  ⚠️  Stake reset: {old_stake} → {self.current_stake}")
    
    def estimate_multiplier(self, elapsed_time):
        """
        Estimate multiplier based on elapsed time
        Uses exponential growth curve similar to Aviator
        """
        import math
        # Approximate formula: multiplier ≈ e^(0.15 * time)
        multiplier = math.exp(0.15 * elapsed_time)
        return round(multiplier, 2)
    
    def print_stats(self):
        """Print bot statistics"""
        print("\n" + "="*60)
        print("BOT STATISTICS")
        print("="*60)
        print(f"Rounds played:        {self.stats['rounds_played']}")
        print(f"Successful cashouts:  {self.stats['successful_cashouts']}")
        print(f"Failed cashouts:      {self.stats['failed_cashouts']}")
        print(f"Current streak:       {self.stats['current_streak']}")
        
        if self.stats['rounds_played'] > 0:
            success_rate = (self.stats['successful_cashouts'] / self.stats['rounds_played']) * 100
            print(f"Success rate:         {success_rate:.1f}%")
        
        print(f"\nStake progression:")
        print(f"  Initial stake:      {self.initial_stake}")
        print(f"  Current stake:      {self.current_stake}")
        print(f"  Max stake reached:  {self.stats['max_stake_reached']}")
        print(f"  Max stake limit:    {self.max_stake}")
        
        print(f"\nFinancial summary:")
        print(f"  Total bet:          {self.stats['total_bet']:.2f}")
        print(f"  Total return:       {self.stats['total_return']:.2f}")
        
        profit = self.stats['total_return'] - self.stats['total_bet']
        print(f"  Profit/Loss:        {profit:+.2f}")
        
        if self.stats['total_bet'] > 0:
            roi = (profit / self.stats['total_bet']) * 100
            print(f"  ROI:                {roi:+.1f}%")
        
        print("="*60 + "\n")
    
    def run(self):
        """Main bot loop with timer-based cashout and progressive staking"""
        print("\n" + "="*60)
        print("AVIATOR BOT - PROGRESSIVE STAKE")
        print("="*60)
        print(f"Strategy: Cashout after {self.cashout_delay}s")
        print(f"Initial stake: {self.initial_stake}")
        print(f"Max stake: {self.max_stake}")
        print(f"Increase: +{self.stake_increase_percent}% on win")
        print(f"Estimated target: ~{self.estimate_multiplier(self.cashout_delay)}x")
        print("="*60)
        print("\nPress Ctrl+C to stop\n")
        
        try:
            while True:
                # Step 1: Wait for "AWAITING NEXT FLIGHT"
                print(f"\n--- Round {self.stats['rounds_played'] + 1} | Stake: {self.current_stake} | Streak: {self.stats['current_streak']} ---")
                print("Waiting for 'AWAITING NEXT FLIGHT'...")
                
                if not self.detector.wait_for_awaiting_message(timeout=60):
                    print("⚠️  Timeout - retrying...")
                    continue
                
                # Step 2: Place bet with current stake
                print(f"  Placing bet: {self.current_stake}")
                self.set_stake(self.current_stake)
                time.sleep(0.4)
                self.place_bet()
                
                # Step 3: Wait for game to start
                if not self.detector.wait_for_game_start(timeout=10):
                    print("⚠️  Game didn't start - assuming loss")
                    self.is_betting = False
                    self.reset_stake()
                    continue
                
                # Step 4: Start timer and countdown
                print(f"  Game started! Counting down {self.cashout_delay}s...")
                round_start = time.time()
                cashout_successful = True
                
                while True:
                    elapsed = time.time() - round_start
                    remaining = self.cashout_delay - elapsed
                    
                    if remaining <= 0:
                        break
                    
                    # Show countdown with estimated multiplier
                    est_mult = self.estimate_multiplier(elapsed)
                    print(f"  {remaining:.1f}s remaining... (~{est_mult:.2f}x)", end='\r')
                    time.sleep(0.1)
                
                # Step 5: Cashout
                print(" " * 50, end='\r')  # Clear line
                
                try:
                    final_mult = self.estimate_multiplier(self.cashout_delay)
                    self.cashout()
                    
                    # Update stats
                    estimated_return = self.current_stake * final_mult
                    self.stats["total_return"] += estimated_return
                    
                    print(f"  Estimated multiplier: {final_mult}x")
                    print(f"  Return: {estimated_return:.2f} (Profit: +{estimated_return - self.current_stake:.2f})")
                    
                    # Increase stake on successful cashout
                    self.increase_stake()
                    
                except Exception as e:
                    print(f"⚠️  Cashout failed - game may have crashed")
                    cashout_successful = False
                    self.reset_stake()
                
                # Step 6: Show current progress
                current_profit = self.stats['total_return'] - self.stats['total_bet']
                print(f"  Total P/L: {current_profit:+.2f}")
                
                # Step 7: Wait a bit before next round
                time.sleep(3)
        
        except KeyboardInterrupt:
            print("\n\n⏹️  Bot stopped by user")
            self.print_stats()


def main():
    """Main function"""
    print("="*60)
    print("AVIATOR BOT - TIMER BASED CASHOUT")
    print("="*60)
    
    bot = AviatorBot()
    
    # Load or setup configuration
    if bot.load_config() and bot.multiplier_region:
        print(f"\nCurrent configuration:")
        print(f"  Stake coords:      {bot.stake_coords}")
        print(f"  Bet button:        {bot.bet_button_coords}")
        print(f"  Cashout button:    {bot.cashout_coords}")
        print(f"  Multiplier region: {bot.multiplier_region}")
        print(f"  Cashout delay:     {bot.cashout_delay}s")
        
        print("\nOptions:")
        print("  1. Use existing config")
        print("  2. New setup")
        print("  3. Test detection only")
        
        choice = input("\nChoice (1/2/3): ").strip()
        
        if choice == '2':
            bot.setup_coordinates()
        elif choice == '3':
            if not bot.detector:
                bot.detector = GameStateDetector(bot.multiplier_region)
            bot.test_detection(duration=20)
            return
    else:
        bot.setup_coordinates()
    
    # Initialize detector if not already done
    if not bot.detector and bot.multiplier_region:
        bot.detector = GameStateDetector(bot.multiplier_region)
    
    # Test detection before running
    print("\n" + "="*60)
    test = input("Test detection before running bot? (y/n): ").strip().lower()
    if test == 'y':
        bot.test_detection(duration=15)
    
    # Get bot parameters
    print("\n" + "="*60)
    print("BOT PARAMETERS")
    print("="*60)
    
    initial = input(f"\nInitial stake (default 25): ").strip()
    if initial:
        bot.initial_stake = int(initial)
        bot.current_stake = bot.initial_stake
    
    max_stake = input(f"Max stake limit (default 1000): ").strip()
    if max_stake:
        bot.max_stake = int(max_stake)
    
    increase = input(f"Stake increase % on win (default 20): ").strip()
    if increase:
        bot.stake_increase_percent = int(increase)
    
    delay = input(f"Cashout delay in seconds (default 2.0): ").strip()
    if delay:
        bot.cashout_delay = float(delay)
    
    # Show strategy summary
    estimated_mult = bot.estimate_multiplier(bot.cashout_delay)
    
    print("\n" + "="*60)
    print("STAKE PROGRESSION PREVIEW")
    print("="*60)
    
    # Calculate stake progression
    stake = bot.initial_stake
    rounds_to_max = 0
    print(f"Round 1:  Stake = {stake}")
    
    while stake < bot.max_stake and rounds_to_max < 20:
        rounds_to_max += 1
        stake = int(stake * (1 + bot.stake_increase_percent / 100))
        if stake > bot.max_stake:
            stake = bot.max_stake
        print(f"Round {rounds_to_max + 1}:  Stake = {stake}")
        if stake >= bot.max_stake:
            print(f"  ✓ Max stake reached!")
            break
    
    print("="*60)
    
    # Confirm and start
    print("\n" + "="*60)
    print("READY TO START")
    print("="*60)
    print(f"Initial stake:     {bot.initial_stake}")
    print(f"Max stake:         {bot.max_stake}")
    print(f"Increase on win:   +{bot.stake_increase_percent}%")
    print(f"Cashout after:     {bot.cashout_delay}s")
    print(f"Target multiplier: ~{estimated_mult}x")
    print("="*60)
    
    input("\nPress Enter to start bot...")
    
    # Save config with new settings
    bot.save_config()
    
    # Run bot
    bot.run()


if __name__ == "__main__":
    main()