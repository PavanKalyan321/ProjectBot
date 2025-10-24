"""
Quick script to add manual history to aviator_rounds_history.csv
Uses the ManualHistoryLoader class
"""

from manual_history_loader import ManualHistoryLoader


def main():
    print("\n" + "="*80)
    print("ADD MANUAL HISTORY TO aviator_rounds_history.csv")
    print("="*80)

    # Create loader (automatically uses aviator_rounds_history.csv)
    loader = ManualHistoryLoader()

    print(f"\nUsing file: {loader.csv_file}")

    # Load history interactively
    multipliers = loader.load_from_manual_input()

    if not multipliers:
        print("\nNo multipliers loaded. Exiting.")
        return

    # Save to CSV
    success = loader.save_to_csv(multipliers, append=True)

    if success:
        # Show statistics
        loader.show_statistics(multipliers)

        print("\n" + "="*80)
        print("NEXT STEPS")
        print("="*80)
        print("  1. Train models with new data:")
        print("     python train_models.py")
        print("\n  2. Run the bot:")
        print("     python bot_modular.py")
        print("="*80 + "\n")
    else:
        print("\nFailed to save multipliers. Check errors above.")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user.")
    except Exception as e:
        print(f"\n\nError: {e}")
