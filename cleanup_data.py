"""
Quick Data Cleanup Script
Run this to fix headers, remove duplicates, and optimize data files
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from utils.data_manager import DataManager


def main():
    print("""
    ╔═══════════════════════════════════════════════════════════╗
    ║                                                           ║
    ║            🧹 DATA CLEANUP & OPTIMIZATION TOOL           ║
    ║                                                           ║
    ╚═══════════════════════════════════════════════════════════╝
    """)

    manager = DataManager()

    # Show current state
    print("CURRENT DATA STATE:")
    manager.get_data_summary()

    print("\nWhat would you like to do?\n")
    print("1. 🧹 Quick Cleanup (remove duplicates, fix headers)")
    print("2. 📦 Archive Old Data (keep last 30 days)")
    print("3. 🔗 Consolidate Data (merge into single file)")
    print("4. 🔄 Full Optimization (cleanup + archive)")
    print("5. 📊 View Summary Only")
    print("6. ❌ Exit")

    choice = input("\nEnter your choice (1-6): ").strip()

    if choice == '1':
        print("\n" + "="*60)
        print("RUNNING QUICK CLEANUP")
        print("="*60)
        results = manager.cleanup_all()
        print("\n✓ Cleanup complete!")

    elif choice == '2':
        days = input("\nKeep how many days of recent data? (default: 30): ").strip()
        days = int(days) if days.isdigit() else 30
        print(f"\nArchiving data older than {days} days...")
        results = manager.archive_old_data(days)
        print("\n✓ Archiving complete!")

    elif choice == '3':
        print("\n" + "="*60)
        print("CONSOLIDATING DATA")
        print("="*60)
        output_path = manager.consolidate_data()
        if output_path:
            print(f"\n✓ Data consolidated successfully!")
            print(f"  Output: {output_path}")

    elif choice == '4':
        print("\n" + "="*60)
        print("FULL OPTIMIZATION")
        print("="*60)

        # Step 1: Cleanup
        print("\nStep 1: Cleaning up data...")
        manager.cleanup_all()

        # Step 2: Archive
        print("\nStep 2: Archiving old data...")
        manager.archive_old_data(30)

        # Step 3: Show summary
        print("\nStep 3: Final summary...")
        manager.get_data_summary()

        print("\n✓ Full optimization complete!")

    elif choice == '5':
        manager.get_data_summary()

    elif choice == '6':
        print("\nGoodbye!")
        return

    else:
        print("\n✗ Invalid choice")
        return

    # Show final summary
    print("\n" + "="*60)
    print("FINAL STATE:")
    print("="*60)
    manager.get_data_summary()

    print("\n✓ All done! You can now run the dashboard with: python run_dashboard.py")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user. Goodbye!")
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
