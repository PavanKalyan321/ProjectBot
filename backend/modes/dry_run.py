"""Dry run mode for AviatorBot - simulation without real bets."""

import time
from utils.betting_helpers import increase_stake, reset_stake


def run_dry_run_mode(bot):
    """DRY RUN MODE - Simulates betting without placing real bets."""
    print("\n" + "="*80)
    print("🧪 DRY RUN MODE - SIMULATION")
    print("="*80)
    print("🎭 Simulating all betting decisions WITHOUT placing real bets")
    print(f"💾 Hypothetical results will be saved to: {bot.history_file}")
    print("Press Ctrl+C to stop.\n")

    round_number = 0
    cumulative_profit = 0

    try:
        while True:
            round_number += 1
            print(f"\n{'='*80}")
            print(f"🎭 DRY RUN ROUND #{round_number:03d}")
            print(f"{'='*80}")

            # Wait for AWAITING state
            if not bot._wait_for_awaiting_state():
                print("⚠️  Skipping round - couldn't detect awaiting state")
                continue

            time.sleep(0.3)

            # Simulate betting decision
            print(f"\n🎲 SIMULATED DECISION: WOULD PLACE BET")
            print(f"   💰 Simulated Stake: {bot.current_stake}")
            print(f"   🎯 Target Multiplier: {bot.target_multiplier:.2f}x")

            # Wait for round to start
            print("\n⏳ Waiting for round to start...")
            if not bot._wait_for_round_start(timeout=20):
                print("⚠️  Round didn't start - simulated bet would be cancelled")

                loss = -bot.current_stake
                cumulative_profit += loss
                bot.hypothetical_balance += loss

                bot.stats["cancelled_bets"] += 1
                bot.stats["rounds_played"] += 1

                print(f"\n❌ SIMULATED RESULT: BET CANCELLED")
                print(f"   💸 Hypothetical Loss: {loss:.2f}")
                print(f"   💰 Hypothetical Balance: {bot.hypothetical_balance:.2f}")
                print(f"   📊 Cumulative P/L: {cumulative_profit:+.2f}")

                # Log to history
                bot._log_to_history(
                    multiplier=0,
                    bet_placed=True,
                    stake=bot.current_stake,
                    profit_loss=loss,
                    balance=bot.hypothetical_balance,
                    cumulative_profit=cumulative_profit,
                    result="CANCELLED"
                )

                # Reset stake
                bot.current_stake = reset_stake(bot.initial_stake, bot.stats)
                continue

            print("🚀 Game started! (simulated bet active)")

            # Reset multiplier reader for new flight
            bot.multiplier_reader.reset()

            # Wait for round to complete
            print(f"\n⏳ Monitoring for target {bot.target_multiplier:.2f}x...")
            success, observed_mult = bot._wait_for_crash_and_read_multiplier(timeout=60)

            if not success:
                observed_mult = 2.0  # Default fallback

            # Calculate hypothetical result
            stake_used = bot.current_stake

            if observed_mult >= bot.target_multiplier:
                # Would have won
                hypothetical_return = stake_used * bot.target_multiplier
                hypothetical_profit = hypothetical_return - stake_used
                cumulative_profit += hypothetical_profit
                bot.hypothetical_balance += hypothetical_profit

                bot.stats["successful_cashouts"] += 1
                bot.stats["rounds_played"] += 1
                bot.stats["total_bet"] += stake_used
                bot.stats["total_return"] += hypothetical_return
                bot.stats["current_streak"] += 1

                print(f"\n✅ SIMULATED RESULT: WIN")
                print(f"   🎯 Actual: {observed_mult:.2f}x | Target: {bot.target_multiplier:.2f}x")
                print(f"   💰 Hypothetical P/L: +{hypothetical_profit:.2f}")
                print(f"   💵 Hypothetical Balance: {bot.hypothetical_balance:.2f}")
                print(f"   📊 Cumulative P/L: {cumulative_profit:+.2f}")
                print(f"   🔥 Win Streak: {bot.stats['current_streak']}")

                # Log to history
                bot._log_to_history(
                    multiplier=observed_mult,
                    bet_placed=True,
                    stake=stake_used,
                    profit_loss=hypothetical_profit,
                    balance=bot.hypothetical_balance,
                    cumulative_profit=cumulative_profit,
                    result="WIN"
                )

                # Increase stake
                old_stake = bot.current_stake
                bot.current_stake = increase_stake(
                    bot.current_stake,
                    20,  # 20% increase
                    bot.max_stake,
                    bot.stats
                )
                if bot.current_stake > old_stake:
                    print(f"   📈 Next stake increased: {old_stake} → {bot.current_stake}")
            else:
                # Would have lost
                hypothetical_loss = -stake_used
                cumulative_profit += hypothetical_loss
                bot.hypothetical_balance += hypothetical_loss

                bot.stats["failed_cashouts"] += 1
                bot.stats["rounds_played"] += 1
                bot.stats["total_bet"] += stake_used
                bot.stats["current_streak"] = 0

                print(f"\n❌ SIMULATED RESULT: LOSS")
                print(f"   💥 Crashed at {observed_mult:.2f}x (target: {bot.target_multiplier:.2f}x)")
                print(f"   💸 Hypothetical P/L: {hypothetical_loss:.2f}")
                print(f"   💵 Hypothetical Balance: {bot.hypothetical_balance:.2f}")
                print(f"   📊 Cumulative P/L: {cumulative_profit:+.2f}")

                # Log to history
                bot._log_to_history(
                    multiplier=observed_mult,
                    bet_placed=True,
                    stake=stake_used,
                    profit_loss=hypothetical_loss,
                    balance=bot.hypothetical_balance,
                    cumulative_profit=cumulative_profit,
                    result="LOSS"
                )

                # Reset stake
                old_stake = bot.current_stake
                bot.current_stake = reset_stake(bot.initial_stake, bot.stats)
                if bot.current_stake < old_stake:
                    print(f"   📉 Next stake reset: {old_stake} → {bot.current_stake}")

            # Reset multiplier reader for next round
            bot.multiplier_reader.reset()

            if round_number % 10 == 0:
                print(f"\n📈 DRY RUN SUMMARY:")
                print(f"   💵 Hypothetical Balance: {bot.hypothetical_balance:.2f}")
                print(f"   📊 Cumulative P/L: {cumulative_profit:+.2f}")
                print(f"   📝 Data logged to: {bot.history_file}")

            time.sleep(0.5)

    except KeyboardInterrupt:
        print("\n\n⛔ Dry run stopped by user.")
        print_dry_run_stats(bot, cumulative_profit)
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        print_dry_run_stats(bot, cumulative_profit)


def print_dry_run_stats(bot, cumulative_profit):
    """Print dry run statistics."""
    print("\n" + "="*80)
    print("📊 DRY RUN FINAL STATISTICS")
    print("="*80)
    print(f"Rounds played:        {bot.stats['rounds_played']}")
    print(f"Simulated wins:       {bot.stats['successful_cashouts']}")
    print(f"Simulated losses:     {bot.stats['failed_cashouts']}")
    print(f"Cancelled bets:       {bot.stats['cancelled_bets']}")
    print(f"Total stake:          {bot.stats['total_bet']:.2f}")
    print(f"Total returns:        {bot.stats['total_return']:.2f}")

    print(f"\n💰 HYPOTHETICAL RESULTS:")
    print(f"Starting balance:     1000.00")
    print(f"Final balance:        {bot.hypothetical_balance:.2f}")
    print(f"Net profit/loss:      {cumulative_profit:+.2f}")

    if bot.stats['rounds_played'] > 0:
        win_rate = (bot.stats['successful_cashouts'] / bot.stats['rounds_played']) * 100
        print(f"Win rate:             {win_rate:.1f}%")
        avg_bet = bot.stats['total_bet'] / bot.stats['rounds_played']
        print(f"Average bet:          {avg_bet:.2f}")

    print(f"\n💾 Data saved to: {bot.history_file}")
    print("="*80)
