"""Observation mode for AviatorBot - data collection without betting."""

import time


def run_observation_mode(bot):
    """Observation mode - collect data without placing bets."""
    print("\n" + "="*80)
    print("📊 OBSERVATION MODE - DATA COLLECTION")
    print("="*80)
    print("📝 Collecting multiplier data without placing bets")
    print(f"💾 Data will be saved to: {bot.history_file}")
    print("Press Ctrl+C to stop.\n")

    round_number = 0
    cumulative_profit = 0

    try:
        while True:
            round_number += 1
            print(f"\n{'='*80}")
            print(f"📊 OBSERVING ROUND #{round_number:03d}")
            print(f"{'='*80}")

            # Wait for AWAITING state
            if not bot._wait_for_awaiting_state():
                print("⚠️  Skipping round - couldn't detect awaiting state")
                continue

            time.sleep(0.3)

            # Wait for round to start
            print("\n⏳ Waiting for round to start...")
            if not bot._wait_for_round_start(timeout=20):
                print("⚠️  Round didn't start")
                continue

            print("🚀 Game started! (monitoring)")

            # Reset multiplier reader for new flight
            bot.multiplier_reader.reset()

            # Wait for round to crash and read final multiplier
            print("\n⏳ Waiting for round to complete...")
            success, observed_mult = bot._wait_for_crash_and_read_multiplier(timeout=60)

            if success and observed_mult:
                print(f"\n📊 Round complete: {observed_mult:.2f}x")
                bot.stats["rounds_observed"] += 1

                # Log to history
                bot._log_to_history(
                    multiplier=observed_mult,
                    bet_placed=False,
                    stake=0,
                    profit_loss=0,
                    balance=bot.last_balance,
                    cumulative_profit=0,
                    result="OBSERVED"
                )

                print(f"✅ Data logged to {bot.history_file}")
            else:
                print("⚠️  Could not read round result")
                bot.stats["rounds_observed"] += 1

            # Reset multiplier reader for next round
            bot.multiplier_reader.reset()

            if round_number % 10 == 0:
                print(f"\n📈 Progress: {bot.stats['rounds_observed']} rounds collected")

            time.sleep(0.5)

    except KeyboardInterrupt:
        print("\n\n⛔ Observation stopped by user.")
        print(f"\n📊 Total rounds observed: {bot.stats['rounds_observed']}")
        print(f"💾 Data saved to: {bot.history_file}")
