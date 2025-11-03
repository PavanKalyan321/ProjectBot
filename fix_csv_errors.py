"""
Quick Fix for CSV Data Corruption
Repairs the bot_automl_performance.csv file
"""

import pandas as pd
import os

def fix_automl_csv():
    """Fix the corrupted bot_automl_performance.csv file."""

    csv_file = "backend/bot_automl_performance.csv"
    backup_file = "backend/bot_automl_performance_backup.csv"

    if not os.path.exists(csv_file):
        print(f"❌ File not found: {csv_file}")
        return False

    print("\n" + "="*60)
    print("  CSV ERROR FIXER")
    print("="*60 + "\n")

    try:
        # Create backup
        print("1. Creating backup...")
        import shutil
        shutil.copy2(csv_file, backup_file)
        print(f"   ✓ Backup saved to: {backup_file}")

        # Read file with error handling
        print("\n2. Reading file with error handling...")

        # Try reading with on_bad_lines='skip' (pandas >= 1.3.0)
        try:
            df = pd.read_csv(csv_file, on_bad_lines='skip')
            print(f"   ✓ Loaded {len(df)} valid rows (skipped bad lines)")
        except TypeError:
            # Fallback for older pandas versions
            df = pd.read_csv(csv_file, error_bad_lines=False, warn_bad_lines=True)
            print(f"   ✓ Loaded {len(df)} valid rows")

        # Show info
        print(f"\n3. File info:")
        print(f"   - Rows: {len(df)}")
        print(f"   - Columns: {len(df.columns)}")
        print(f"   - Columns: {list(df.columns[:10])}...")

        # Remove duplicates
        print("\n4. Removing duplicates...")
        before = len(df)
        if 'round_id' in df.columns:
            df = df.drop_duplicates(subset=['round_id'], keep='last')
        else:
            df = df.drop_duplicates()
        after = len(df)
        print(f"   ✓ Removed {before - after} duplicate rows")

        # Remove rows with too many NaN values
        print("\n5. Removing invalid rows...")
        before = len(df)
        df = df.dropna(thresh=len(df.columns) * 0.3)  # Keep rows with at least 30% valid data
        after = len(df)
        print(f"   ✓ Removed {before - after} invalid rows")

        # Sort by timestamp
        print("\n6. Sorting by timestamp...")
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
            df = df.sort_values('timestamp')
            print(f"   ✓ Sorted by timestamp")

        # Save cleaned file
        print("\n7. Saving cleaned file...")
        df.to_csv(csv_file, index=False)
        print(f"   ✓ Saved to: {csv_file}")

        # Summary
        print("\n" + "="*60)
        print("  ✓ CSV FILE FIXED SUCCESSFULLY!")
        print("="*60)
        print(f"\n  Final stats:")
        print(f"  - Total rows: {len(df)}")
        print(f"  - Columns: {len(df.columns)}")
        print(f"  - Backup saved at: {backup_file}")
        print("\n  You can now restart the dashboard!")
        print("="*60 + "\n")

        return True

    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nTrying alternative method...")

        # Alternative: Read line by line and rebuild
        try:
            return fix_csv_line_by_line(csv_file, backup_file)
        except Exception as e2:
            print(f"❌ Alternative method also failed: {e2}")
            return False


def fix_csv_line_by_line(csv_file, backup_file):
    """Fix CSV by reading line by line."""

    print("\n" + "="*60)
    print("  ADVANCED CSV REPAIR")
    print("="*60 + "\n")

    valid_lines = []
    header = None
    expected_cols = None
    skipped = 0

    print("1. Reading file line by line...")

    with open(csv_file, 'r', encoding='utf-8', errors='ignore') as f:
        for i, line in enumerate(f, 1):
            line = line.strip()

            if i == 1:
                # Header line
                header = line
                expected_cols = len(line.split(','))
                valid_lines.append(line)
                print(f"   ✓ Header found: {expected_cols} columns")
                continue

            # Count columns in this line
            cols = len(line.split(','))

            if cols == expected_cols:
                valid_lines.append(line)
            else:
                skipped += 1
                if skipped <= 5:
                    print(f"   ⚠ Line {i}: Expected {expected_cols} cols, got {cols} - SKIPPED")

    print(f"\n2. Results:")
    print(f"   ✓ Valid lines: {len(valid_lines) - 1}")  # -1 for header
    print(f"   ⚠ Skipped lines: {skipped}")

    # Write cleaned file
    print("\n3. Writing cleaned file...")
    with open(csv_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(valid_lines))

    print(f"   ✓ Saved to: {csv_file}")

    print("\n" + "="*60)
    print("  ✓ CSV REPAIRED SUCCESSFULLY!")
    print("="*60)
    print(f"\n  Valid rows: {len(valid_lines) - 1}")
    print(f"  Backup: {backup_file}")
    print("\n  Restart dashboard now!")
    print("="*60 + "\n")

    return True


def fix_all_csv_files():
    """Fix all CSV files."""

    files = [
        "backend/bot_automl_performance.csv",
        "backend/aviator_rounds_history.csv",
        "backend/bet_history.csv"
    ]

    print("\n" + "="*60)
    print("  FIXING ALL CSV FILES")
    print("="*60 + "\n")

    for csv_file in files:
        if not os.path.exists(csv_file):
            print(f"⚠ Skipping {csv_file} (not found)")
            continue

        print(f"\n→ Fixing {csv_file}...")

        backup = csv_file.replace('.csv', '_backup.csv')

        try:
            import shutil
            shutil.copy2(csv_file, backup)

            try:
                df = pd.read_csv(csv_file, on_bad_lines='skip')
            except TypeError:
                df = pd.read_csv(csv_file, error_bad_lines=False, warn_bad_lines=False)

            # Remove duplicates
            if 'round_id' in df.columns:
                df = df.drop_duplicates(subset=['round_id'], keep='last')

            # Remove invalid rows
            df = df.dropna(how='all')

            # Save
            df.to_csv(csv_file, index=False)

            print(f"  ✓ Fixed! ({len(df)} valid rows)")

        except Exception as e:
            print(f"  ❌ Error: {e}")

    print("\n" + "="*60)
    print("  ALL FILES PROCESSED")
    print("="*60 + "\n")


if __name__ == '__main__':
    print("\n╔═══════════════════════════════════════════════════════════╗")
    print("║                                                           ║")
    print("║              CSV ERROR FIXER UTILITY                      ║")
    print("║                                                           ║")
    print("╚═══════════════════════════════════════════════════════════╝\n")

    print("This will fix the CSV data corruption error.")
    print("\nOptions:")
    print("  1. Fix bot_automl_performance.csv only (RECOMMENDED)")
    print("  2. Fix all CSV files")
    print("  3. Exit")

    choice = input("\nEnter choice (1-3): ").strip()

    if choice == '1':
        success = fix_automl_csv()
        if success:
            print("\n✓ Done! Now restart the dashboard:")
            print("  python run_dashboard.py")
    elif choice == '2':
        fix_all_csv_files()
        print("\n✓ Done! Now restart the dashboard:")
        print("  python run_dashboard.py")
    elif choice == '3':
        print("\nGoodbye!")
    else:
        print("\n❌ Invalid choice")
