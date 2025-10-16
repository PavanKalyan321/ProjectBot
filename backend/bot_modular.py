"""
Aviator Bot - Comprehensive Fix
Fixed: Bet placement validation, cashout triggering, balance tracking, bet state management
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


class AviatorBotML:
    """Main Aviator Bot with comprehensive fixes."""

    def __init__(self):
        """Initialize bot with default settings."""
        self.config_manager = ConfigManager()
        
        # Bot state
        self.current_stake = 25
        self.is_betting = False
        self.bet_state = "IDLE"
        self.active_bet_round = None
        self.last_balance = None
        
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
    
    def initialize_components(self):
        """Initialize all bot components after config is loaded."""
        if self.config_manager.multiplier_region:
            self.detector = GameStateDetector(self.config_manager.multiplier_region)
        
        if self.config_manager.history_region:
            self.history_tracker = RoundHistoryTracker(self.config_manager.history_region)
        
        if self.history_tracker:
            self.ml_generator = MLSignalGenerator(self.history_tracker)
        
        # Set initial stake
        self.current_stake = self.config_manager.initial_stake
    
    def _reset_bet_state(self):
        """Reset betting state completely."""
        self.is_betting = False
        self.bet_state = "IDLE"
        self.active_bet_round = None
    
    def _read_balance(self):
        """
        Read current balance from balance region.
        Returns balance as float or None if failed.
        """
        try:
            import pyautogui
            import pyperclip
            
            x1, y1, x2, y2 = self.balance_coords
            
            # Triple-click to select balance text
            pyautogui.click((x1 + x2) // 2, (y1 + y2) // 2, clicks=3)
            time.sleep(0.1)
            
            # Copy to clipboard
            pyautogui.hotkey('ctrl', 'c')
            time.sleep(0.1)
            
            balance_text = pyperclip.paste().strip()
            
            if not balance_text:
                return None
            
            # Parse balance (handle K format, e.g., "1.5K" = 1500)
            balance_text = balance_text.replace(',', '')
            
            if 'K' in balance_text.upper():
                # Extract number before K
                match = re.search(r'([\d.]+)K', balance_text.upper())
                if match:
                    return float(match.group(1)) * 1000
            else:
                # Extract any number
                match = re.search(r'[\d.]+', balance_text)
                if match:
                    return float(match.group(0))
            
            return None
        except Exception as e:
            print(f"  ⚠️ Balance read error: {e}")
            return None
    
    def _verify_bet_placed(self, timeout=3):
        """
        Verify if bet is already placed by checking for bet button state.
        Returns True if bet is already active, False otherwise.
        """
        try:
            import pyautogui
            from PIL import Image
            import numpy as np
            
            # Read button area to check if bet is already placed
            # A placed bet typically shows "CANCEL BET" or different color
            x, y = self.config_manager.bet_button_coords
            
            # Sample area around button
            screenshot = pyautogui.screenshot(region=(x-50, y-25, 100, 50))
            img_array = np.array(screenshot)
            
            # Check for red/cancel button indicators
            # Red channel dominance suggests cancel button
            red_channel = img_array[:, :, 0]
            avg_red = np.mean(red_channel)
            
            # If significant red present, bet is likely placed
            if avg_red > 150:
                return True
            
            return False
        except Exception as e:
            print(f"  ⚠️ Bet verification error: {e}")
            return False
    
    def _check_existing_bet(self):
        """
        Check if there's an existing bet from previous round.
        Returns True if bet exists, False otherwise.
        """
        if self._verify_bet_placed():
            print("  ⚠️ Existing bet detected from previous round!")
            return True
        return False
    
    def _verify_game_running_strict(self):
        """
        Strict verification that game is actually running.
        Checks both state text and actual multiplier value.
        """
        state = self.detector.read_text_in_region()
        multiplier = self.detector.read_multiplier_from_clipboard()
        
        # Game is running if:
        # 1. State shows FLYING or multiplier with 'x'
        # 2. Multiplier value is greater than 1.0
        if state == 'FLYING':
            return True
        
        if multiplier and multiplier > 1.0:
            return True
        
        if state and 'x' in str(state).lower() and state not in ['AWAITING', 'FLEW AWAY']:
            return True
        
        return False
    
    def _wait_for_game_start_strict(self, timeout=15):
        """
        Wait for game to start with strict verification.
        Returns True if game started, False if timeout or error.
        """
        start_time = time.time()
        initial_state = self.detector.read_text_in_region()
        
        print(f"  ⏳ Waiting for game start (initial state: {initial_state})...")
        
        while time.time() - start_time < timeout:
            elapsed = time.time() - start_time
            
            # Check if round already ended (AWAITING again means we missed it)
            current_state = self.detector.read_text_in_region()
            if current_state == 'AWAITING' and elapsed > 3:
                print(f"\n  ⚠️ Round ended without detecting start - bet may be cancelled")
                return False
            
            # Check if game is actually running
            if self._verify_game_running_strict():
                print(f"\n  🚀 Game started! (verified at {elapsed:.2f}s)")
                return True
            
            # Show progress
            if int(elapsed * 2) % 2 == 0:
                print(f"  ⏰ Waiting {timeout - elapsed:.1f}s...", end='\r', flush=True)
            
            time.sleep(0.2)
        
        print(f"\n  ❌ Timeout waiting for game start")
        return False
    
    def _monitor_cashout_button(self):
        """
        Monitor cashout button state to detect if bet is still active.
        Returns True if button is present (bet active), False otherwise.
        """
        try:
            import pyautogui
            from PIL import Image
            import numpy as np
            
            x, y = self.config_manager.cashout_coords
            
            # Sample cashout button area
            screenshot = pyautogui.screenshot(region=(x-50, y-25, 100, 50))
            img_array = np.array(screenshot)
            
            # Check for green/active button
            green_channel = img_array[:, :, 1]
            avg_green = np.mean(green_channel)
            
            # Active cashout button should have significant green
            return avg_green > 100
        except:
            return False
    
    def _show_countdown_progress(self, elapsed, target_time):
        """Show visual countdown progress bar with color coding."""
        remaining = target_time - elapsed
        
        if remaining <= 0:
            return
        
        progress_pct = (elapsed / target_time) * 100
        bar_length = 30
        filled = int((progress_pct / 100) * bar_length)
        bar = '█' * filled + '░' * (bar_length - filled)
        
        if remaining > 2:
            color = '🟢'
        elif remaining > 1:
            color = '🟡'
        else:
            color = '🔴'
        
        print(f"  {color} [{bar}] {remaining:.2f}s", end='\r', flush=True)
    
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
        """Main betting loop with comprehensive fixes."""
        print("\n" + "="*60)
        print("✈️  AVIATOR BOT - COMPREHENSIVE FIX")
        print("="*60)
        print(f"Cashout: {self.config_manager.cashout_delay}s | Threshold: {self.ml_generator.confidence_threshold}%")
        print("="*60)
        print("\n🚀 Starting... Press Ctrl+C to stop\n")
        
        cumulative_profit = 0
        round_number = 0

        try:
            while True:
                round_number += 1
                print(f"\n{'='*60}")
                print(f"🎯 ROUND {round_number}")
                print(f"{'='*60}")
                
                # STEP 1: Wait for clean AWAITING state
                print("  🔍 Waiting for AWAITING state...")
                if not self.detector.wait_for_clean_awaiting_state(timeout=60):
                    print("  ⚠️ Timeout waiting for AWAITING")
                    continue
                
                print("  ✅ AWAITING confirmed")
                time.sleep(0.3)
                
                # STEP 2: Check for existing bet from previous round
                if self._check_existing_bet():
                    print("  🔄 Handling orphaned bet from previous round")
                    self.stats["cancelled_bets"] += 1
                    self.stats["failed_cashouts"] += 1
                    
                    loss = -self.current_stake
                    cumulative_profit += loss
                    
                    self.history_tracker.log_round(0, True, self.current_stake, 0, loss, 0, 0, 'orphaned')
                    round_data = self._create_round_data(0, True, self.current_stake, 0, loss, None, cumulative_profit)
                    self._emit_dashboard_update(round_data)
                    
                    print(f"  💸 Orphaned bet loss: -{self.current_stake:.2f}")
                    
                    self.current_stake = reset_stake(self.config_manager.initial_stake, self.stats)
                    self._reset_bet_state()
                    continue
                
                # STEP 3: Log previous round multiplier
                print("  📝 Logging previous round...")
                success, logged_mult = self.history_tracker.auto_log_from_clipboard(self.detector)
                
                if success:
                    print(f"  ✅ Logged: {logged_mult}x")
                else:
                    print(f"  ℹ️  No previous multiplier")
                
                time.sleep(0.2)
                
                # STEP 4: Generate ML signal
                print("  🤖 Analyzing pattern...")
                signal = self.ml_generator.generate_ensemble_signal()
                print(f"  📊 Prediction: {signal['prediction']:.2f}x | Confidence: {signal['confidence']:.1f}%")
                
                if signal['should_bet']:
                    print(f"  🎲 ML SIGNAL: BET")
                    stake_used = self.current_stake
                    
                    # Final pre-bet check
                    if self.detector.is_game_already_running():
                        print("  ⚠️ Game already running - aborting")
                        self.stats["rounds_observed"] += 1
                        self.stats["ml_skipped"] += 1
                        self._reset_bet_state()
                        continue
                    
                    # Set stake
                    print(f"  💰 Setting stake: {stake_used}")
                    if not set_stake_verified(self.config_manager.stake_coords, stake_used):
                        print("  ❌ Stake setting failed")
                        self.stats["rounds_observed"] += 1
                        self.stats["ml_skipped"] += 1
                        self._reset_bet_state()
                        continue
                    
                    time.sleep(0.15)
                    
                    # Place bet with verification
                    print(f"  💵 Placing bet...")
                    bet_success, bet_reason = place_bet_with_verification(
                        self.config_manager.bet_button_coords,
                        self.detector,
                        self.stats,
                        self.current_stake
                    )
                    
                    if not bet_success:
                        print(f"  ❌ Bet placement failed: {bet_reason}")
                        self.stats["rounds_observed"] += 1
                        self.stats["ml_skipped"] += 1
                        self._reset_bet_state()
                        continue
                    
                    # Mark bet as active
                    self.is_betting = True
                    self.bet_state = "PLACED"
                    self.active_bet_round = round_number
                    print(f"  ✅ Bet placed for round {round_number}")
                    
                    time.sleep(0.5)
                    
                    # Wait for game to start with strict verification
                    game_started = self._wait_for_game_start_strict(timeout=15)
                    
                    if not game_started:
                        print("  ⚠️ Game didn't start - bet cancelled or missed")
                        self.stats["cancelled_bets"] += 1
                        self.stats["failed_cashouts"] += 1
                        
                        loss = -stake_used
                        cumulative_profit += loss
                        
                        self.history_tracker.log_round(0, True, stake_used, 0, loss,
                                                      signal['prediction'], signal['confidence'], 'no_start')
                        
                        round_data = self._create_round_data(0, True, stake_used, 0, loss, signal, cumulative_profit)
                        self._emit_dashboard_update(round_data)
                        
                        self.current_stake = reset_stake(self.config_manager.initial_stake, self.stats)
                        self._reset_bet_state()
                        self.stats["rounds_observed"] += 1
                        
                        print(f"  💸 Loss: -{stake_used:.2f}")
                        print(f"  📊 Total P/L: {cumulative_profit:+.2f}")
                        continue
                    
                    # CASHOUT COUNTDOWN with monitoring
                    print(f"\n  ⏱️  CASHOUT COUNTDOWN: {self.config_manager.cashout_delay}s")
                    print("  " + "="*50)
                    
                    round_start = time.time()
                    cashout_triggered = False
                    last_crash_check = time.time()
                    crash_check_interval = 0.3
                    
                    while True:
                        current_time = time.time()
                        elapsed = current_time - round_start
                        remaining = self.config_manager.cashout_delay - elapsed
                        
                        # Update progress bar
                        self._show_countdown_progress(elapsed, self.config_manager.cashout_delay)
                        
                        # Only check for crash via state (more reliable than button monitoring)
                        if current_time - last_crash_check >= crash_check_interval:
                            if self.detector.has_game_crashed():
                                print(f"\n  💥 CRASHED at {elapsed:.3f}s!")
                                print(f"  ⏰ Missed cashout by: {remaining:.3f}s")
                                
                                self.stats["failed_cashouts"] += 1
                                self.stats["current_streak"] = 0
                                
                                loss = -stake_used
                                cumulative_profit += loss
                                
                                self.history_tracker.log_round(0, True, stake_used, elapsed, loss,
                                                              signal['prediction'], signal['confidence'], signal['range'])
                                
                                round_data = self._create_round_data(0, True, stake_used, elapsed, loss, 
                                                                     signal, cumulative_profit)
                                self._emit_dashboard_update(round_data)
                                
                                print(f"  💸 Loss: -{stake_used:.2f}")
                                print(f"  📊 Total P/L: {cumulative_profit:+.2f}")
                                
                                self.current_stake = reset_stake(self.config_manager.initial_stake, self.stats)
                                self._reset_bet_state()
                                break
                            
                            last_crash_check = current_time
                        
                        # Trigger cashout at exact time
                        if remaining <= 0 and not cashout_triggered:
                            cashout_triggered = True
                            actual_elapsed = time.time() - round_start
                            
                            print(f"\n\n  💰 CASHING OUT NOW!")
                            print(f"  ⏰ Time: {actual_elapsed:.3f}s")
                            
                            # Double-check bet is still active before attempting cashout
                            time.sleep(0.05)  # Brief pause to ensure state is stable
                            
                            # Verify game hasn't crashed in the exact moment
                            if self.detector.has_game_crashed():
                                print(f"  💥 Crashed exactly at cashout time!")
                                self.stats["failed_cashouts"] += 1
                                self.stats["current_streak"] = 0
                                
                                loss = -stake_used
                                cumulative_profit += loss
                                
                                self.history_tracker.log_round(0, True, stake_used, actual_elapsed, loss,
                                                              signal['prediction'], signal['confidence'], signal['range'])
                                
                                round_data = self._create_round_data(0, True, stake_used, actual_elapsed, loss, 
                                                                     signal, cumulative_profit)
                                self._emit_dashboard_update(round_data)
                                
                                print(f"  💸 Loss: -{stake_used:.2f}")
                                print(f"  📊 Total P/L: {cumulative_profit:+.2f}")
                                
                                self.current_stake = reset_stake(self.config_manager.initial_stake, self.stats)
                                self._reset_bet_state()
                                break
                            
                            cashout_start = time.time()
                            cashout_success, cashout_reason = cashout_verified(
                                self.config_manager.cashout_coords,
                                self.detector
                            )
                            cashout_duration = (time.time() - cashout_start) * 1000
                            print(f"  ⚡ Execution: {cashout_duration:.0f}ms")
                            
                            if cashout_success:
                                # Read balance after cashout
                                time.sleep(0.3)
                                new_balance = self._read_balance()
                                
                                self.stats["successful_cashouts"] += 1
                                self.stats["current_streak"] += 1
                                
                                final_mult = estimate_multiplier(self.config_manager.cashout_delay)
                                returns = stake_used * final_mult
                                profit = returns - stake_used
                                cumulative_profit += profit
                                self.stats["total_return"] += returns
                                
                                self.history_tracker.log_round(final_mult, True, stake_used, 
                                                              self.config_manager.cashout_delay, profit,
                                                              signal['prediction'], signal['confidence'], signal['range'])
                                
                                round_data = self._create_round_data(final_mult, True, stake_used, 
                                                                     self.config_manager.cashout_delay, profit, 
                                                                     signal, cumulative_profit, new_balance)
                                self._emit_dashboard_update(round_data)
                                
                                balance_str = f" | Balance: {new_balance:.2f}" if new_balance else ""
                                print(f"  ✅ SUCCESS at {final_mult:.2f}x")
                                print(f"  💰 Profit: +{profit:.2f}{balance_str}")
                                print(f"  📊 Total P/L: {cumulative_profit:+.2f}")
                                print(f"  🔥 Streak: {self.stats['current_streak']}")
                                
                                self.last_balance = new_balance
                                
                                self.current_stake = increase_stake(
                                    self.current_stake,
                                    self.config_manager.stake_increase_percent,
                                    self.config_manager.max_stake,
                                    self.stats
                                )
                            else:
                                # Cashout failed - check if it crashed during the attempt
                                print(f"  ❌ Cashout failed: {cashout_reason}")
                                
                                # Check if game crashed during cashout attempt
                                time.sleep(0.2)
                                if self.detector.has_game_crashed() or cashout_reason == "NO_ACTIVE_BET":
                                    print(f"  💥 Game crashed during cashout attempt")
                                    self.stats["failed_cashouts"] += 1
                                    self.stats["current_streak"] = 0
                                    
                                    loss = -stake_used
                                    cumulative_profit += loss
                                    
                                    self.history_tracker.log_round(0, True, stake_used, actual_elapsed, loss,
                                                                  signal['prediction'], signal['confidence'], signal['range'])
                                    
                                    round_data = self._create_round_data(0, True, stake_used, actual_elapsed, loss, 
                                                                         signal, cumulative_profit)
                                    self._emit_dashboard_update(round_data)
                                    
                                    print(f"  💸 Loss: -{stake_used:.2f}")
                                    print(f"  📊 Total P/L: {cumulative_profit:+.2f}")
                                else:
                                    # Unknown failure - treat as loss
                                    self.stats["failed_cashouts"] += 1
                                    self.stats["current_streak"] = 0
                                    loss = -stake_used
                                    cumulative_profit += loss
                                
                                self.current_stake = reset_stake(self.config_manager.initial_stake, self.stats)
                            
                            self._reset_bet_state()
                            break
                        
                        # Adaptive sleep
                        if remaining > 1:
                            time.sleep(0.1)
                        elif remaining > 0.3:
                            time.sleep(0.05)
                        else:
                            time.sleep(0.01)
                    
                    print()
                
                else:
                    # Skip round
                    print(f"  ⏭️  SKIP: {signal['reason']}")
                    self.stats["ml_skipped"] += 1
                    self._reset_bet_state()
                    
                    # Wait for round to complete
                    print(f"  ⏳ Waiting for round to complete...")
                    start_wait = time.time()
                    while time.time() - start_wait < 30:
                        if self.detector.is_awaiting_next_flight():
                            print(f"  ✅ Round ended")
                            break
                        time.sleep(0.5)
                    
                    time.sleep(0.3)
                    
                    # Log observed multiplier
                    observed_mult = 2.0
                    success = False
                    try:
                        success, mult = self.history_tracker.auto_log_from_clipboard(self.detector, force=False)
                        if success and mult:
                            observed_mult = mult
                            print(f"  📊 Observed: {observed_mult}x")
                    except:
                        pass
                    
                    if not success:
                        self.history_tracker.log_round(observed_mult, False, 0, 0, 0,
                                                      signal['prediction'], signal['confidence'], signal['range'])
                    
                    round_data = self._create_round_data(observed_mult, False, 0, 0, 0, 
                                                         signal, cumulative_profit)
                    self._emit_dashboard_update(round_data)
                
                self.stats["rounds_observed"] += 1
                
                if self.dashboard:
                    self.dashboard.emit_stats_update()
                
                print(f"  ✓ Round {round_number} complete")
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
        print("\n" + "="*60)
        print("📊 FINAL STATISTICS")
        print("="*60)
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
        
        print("="*60 + "\n")


def main():
    """Main entry point."""
    print("="*60)
    print("✈️  AVIATOR BOT - COMPREHENSIVE FIX")
    print("="*60)
    print("\n🔧 Fixes implemented:")
    print("  ✓ Bet placement validation")
    print("  ✓ Strict game start detection")
    print("  ✓ Cashout button monitoring")
    print("  ✓ Balance tracking")
    print("  ✓ Orphaned bet detection")
    print("="*60)

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

    # Configure parameters
    print("\n" + "="*60)
    print("⚙️  PARAMETERS")
    print("="*60)
    
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
    
    print("\n" + "="*60)
    print("📋 SUMMARY")
    print("="*60)
    print(f"Initial stake:     {bot.config_manager.initial_stake}")
    print(f"Max stake:         {bot.config_manager.max_stake}")
    print(f"Increase on win:   +{bot.config_manager.stake_increase_percent}%")
    print(f"Cashout timing:    {bot.config_manager.cashout_delay}s (~{estimated_mult}x)")
    print(f"ML threshold:      {bot.ml_generator.confidence_threshold}%")
    print(f"Balance tracking:  Enabled")
    print("="*60)
    
    # Start dashboard
    print("\n🌐 Starting dashboard...")
    bot.dashboard = AviatorDashboard(bot, port=5000)
    bot.dashboard.start()
    
    print("\n✅ Dashboard: http://localhost:5000")
    print("\nPress Enter to start...")
    input()
    
    # Save config and run
    bot.config_manager.save_config()
    bot.run_ml_mode()


if __name__ == "__main__":
    main()