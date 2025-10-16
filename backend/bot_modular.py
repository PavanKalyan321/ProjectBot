"""
Aviator Bot - Modular Version
Complete bot with modularized components for better maintainability.
"""

import time
from datetime import datetime

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
    """Main Aviator Bot with modular architecture."""

    def __init__(self):
        """Initialize bot with default settings."""
        self.config_manager = ConfigManager()
        
        # Bot state
        self.current_stake = 25
        self.is_betting = False
        self.bet_state = "IDLE"
        
        # Components (initialized after config load)
        self.detector = None
        self.history_tracker = None
        self.ml_generator = None
        self.dashboard = None
        
        # Statistics
        self.stats = {
            "rounds_played": 0,
            "rounds_observed": 0,
            "ml_bets_placed": 0,
            "successful_cashouts": 0,
            "failed_cashouts": 0,
            "ml_skipped": 0,
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
    
    def _create_round_data(self, multiplier, bet_placed, stake, cashout_time, 
                          profit_loss, signal, cumulative_profit):
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
            'stats': self.stats.copy(),
            'current_stake': self.current_stake
        }
    
    def _emit_dashboard_update(self, round_data):
        """Emit update to dashboard if available."""
        if self.dashboard:
            self.dashboard.emit_round_update(round_data)
    
    def run_ml_mode(self):
        """Main betting loop with ML signals."""
        print("\n" + "="*60)
        print("✈️  AVIATOR BOT - MODULAR VERSION")
        print("="*60)
        print(f"Cashout: {self.config_manager.cashout_delay}s | Threshold: {self.ml_generator.confidence_threshold}%")
        print("="*60)
        print("\n🚀 Starting... Press Ctrl+C to stop\n")
        
        cumulative_profit = 0

        try:
            while True:
                print(f"\n{'='*60}")
                print(f"🎯 ROUND {self.stats['rounds_observed'] + 1}")
                print(f"{'='*60}")
                
                # STEP 1: Wait for clean AWAITING state
                print("  🔍 Waiting for AWAITING state...")
                if not self.detector.wait_for_clean_awaiting_state(timeout=60):
                    print("  ⚠️ Timeout")
                    continue
                
                print("  ✅ AWAITING confirmed")
                
                # STEP 2: Log previous round
                print("  📝 Logging previous round...")
                time.sleep(0.5)
                success, logged_mult = self.history_tracker.auto_log_from_clipboard(self.detector)
                
                if success:
                    print(f"  ✅ Logged: {logged_mult}x")
                else:
                    print(f"  ⚠️ Couldn't read multiplier")
                
                time.sleep(0.3)
                
                # STEP 3: Generate ML signal
                print("  🤖 Analyzing...")
                signal = self.ml_generator.generate_ensemble_signal()
                print(f"  📊 Pred: {signal['prediction']}x | Conf: {signal['confidence']}%")
                
                if signal['should_bet']:
                    stake_used = self.current_stake
                    
                    # Verify still in AWAITING
                    if self.detector.is_game_already_running():
                        print("  ⚠️ Game started - skipping")
                        self.stats["rounds_observed"] += 1
                        continue
                    
                    # Set stake
                    print(f"  💰 Setting stake: {stake_used}")
                    if not set_stake_verified(self.config_manager.stake_coords, stake_used):
                        print("  ⚠️ Stake failed")
                        self.stats["rounds_observed"] += 1
                        continue
                    
                    time.sleep(0.2)
                    
                    # Place bet with verification
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
                        continue
                    
                    self.is_betting = True
                    self.bet_state = "PLACED"
                    
                    # Wait for game start
                    print("  ⏳ Waiting for game start...")
                    game_started = False
                    start_wait = time.time()
                    
                    while time.time() - start_wait < 10:
                        state = self.detector.read_text_in_region()
                        if state not in ['AWAITING', 'UNKNOWN', None]:
                            game_started = True
                            print(f"  🚀 Game started!")
                            break
                        time.sleep(0.3)
                    
                    if not game_started:
                        print("  ⚠️ Game didn't start")
                        self.is_betting = False
                        loss = -stake_used
                        cumulative_profit += loss
                        self.history_tracker.log_round(0, True, stake_used, 0, loss,
                                                      signal['prediction'], signal['confidence'], signal['range'])
                        self.current_stake = reset_stake(self.config_manager.initial_stake, self.stats)
                        self.stats["rounds_observed"] += 1
                        continue
                    
                    # Countdown to cashout
                    print(f"  ⏱️  Countdown: {self.config_manager.cashout_delay}s")
                    round_start = time.time()
                    
                    while True:
                        elapsed = time.time() - round_start
                        remaining = self.config_manager.cashout_delay - elapsed
                        
                        # Check if crashed
                        if self.detector.is_awaiting_next_flight():
                            print(f"\n  💥 CRASHED at {elapsed:.1f}s!")
                            
                            self.is_betting = False
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
                            break
                        
                        # Time to cashout
                        if remaining <= 0:
                            print(f"\n  💰 Cashing out...")
                            cashout_success, cashout_reason = cashout_verified(
                                self.config_manager.cashout_coords,
                                self.detector
                            )
                            
                            if cashout_success:
                                self.is_betting = False
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
                                                                     signal, cumulative_profit)
                                self._emit_dashboard_update(round_data)
                                
                                print(f"  ✅ WIN at {final_mult:.2f}x")
                                print(f"  💰 Profit: +{profit:.2f}")
                                print(f"  📊 Total P/L: {cumulative_profit:+.2f}")
                                
                                self.current_stake = increase_stake(
                                    self.current_stake,
                                    self.config_manager.stake_increase_percent,
                                    self.config_manager.max_stake,
                                    self.stats
                                )
                            else:
                                print(f"  ❌ Cashout failed: {cashout_reason}")
                                self.stats["failed_cashouts"] += 1
                                loss = -stake_used
                                cumulative_profit += loss
                                self.current_stake = reset_stake(self.config_manager.initial_stake, self.stats)
                            
                            break
                        
                        # Progress bar
                        progress = int((elapsed / self.config_manager.cashout_delay) * 20)
                        bar = '█' * progress + '░' * (20 - progress)
                        print(f"  ⏱️  [{bar}] {remaining:.1f}s", end='\r')
                        time.sleep(0.1)
                    
                    print()
                
                else:
                    # Skip round
                    print(f"  ⏭️  SKIP: {signal['reason']}")
                    self.stats["ml_skipped"] += 1
                    
                    # Wait for round to end
                    start_wait = time.time()
                    while time.time() - start_wait < 30:
                        if self.detector.is_awaiting_next_flight():
                            break
                        time.sleep(0.5)
                    
                    time.sleep(0.5)
                    
                    # Try to log observed multiplier
                    observed_mult = 2.0
                    try:
                        success, mult = self.history_tracker.auto_log_from_clipboard(self.detector, force=False)
                        if success and mult:
                            observed_mult = mult
                    except:
                        pass
                    
                    if not success:
                        self.history_tracker.log_round(observed_mult, False, 0, 0, 0,
                                                      signal['prediction'], signal['confidence'], signal['range'])
                    
                    round_data = self._create_round_data(observed_mult, False, 0, 0, 0, 
                                                         signal, cumulative_profit)
                    self._emit_dashboard_update(round_data)
                
                self.stats["rounds_observed"] += 1
                self.bet_state = "IDLE"
                
                if self.dashboard:
                    self.dashboard.emit_stats_update()
                
                time.sleep(0.5)

        except KeyboardInterrupt:
            print("\n\n⏹️  Stopped")
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
        
        print("="*60 + "\n")


def main():
    """Main entry point."""
    print("="*60)
    print("✈️  AVIATOR BOT - MODULAR VERSION")
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
