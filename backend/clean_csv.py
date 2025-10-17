"""
CSV Data Cleaning Utility
Fixes corrupted CSV files with inconsistent column counts
"""

import pandas as pd
import os
from datetime import datetime


def clean_csv_file(input_file, output_file=None):
    """
    Clean CSV file by removing rows with incorrect column counts.

    Args:
        input_file: Path to input CSV file
        output_file: Path to output CSV file (optional, defaults to backup and overwrite)

    Returns:
        bool: True if successful
    """
    if not os.path.exists(input_file):
        print(f"ERROR: File not found: {input_file}")
        return False

    # Backup original file
    backup_file = f"{input_file}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    print(f"\n{'='*80}")
    print("CSV CLEANING UTILITY")
    print(f"{'='*80}")
    print(f"Input file: {input_file}")
    print(f"Backup file: {backup_file}")

    # Create backup
    import shutil
    shutil.copy2(input_file, backup_file)
    print(f"[OK] Backup created")

    # Read file line by line and check column counts
    expected_columns = None
    valid_lines = []
    invalid_lines = []

    with open(input_file, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue

            # Count columns
            col_count = len(line.split(','))

            # First non-empty line is the header
            if expected_columns is None:
                expected_columns = col_count
                valid_lines.append(line)
                continue

            # Check if line has correct column count
            if col_count == expected_columns:
                valid_lines.append(line)
            else:
                invalid_lines.append((line_num, col_count, line[:100]))

    print(f"\n[INFO] Analysis:")
    print(f"   Expected columns: {expected_columns}")
    print(f"   Valid lines: {len(valid_lines)}")
    print(f"   Invalid lines: {len(invalid_lines)}")

    if expected_columns != 16:
        print(f"\n[WARNING] Expected 16 columns but found {expected_columns}")
        print(f"   The aviator_rounds_history.csv should have 16 columns")
        print(f"   This file may need to be recreated or migrated")

    if invalid_lines:
        print(f"\n[WARNING] Found {len(invalid_lines)} invalid lines:")
        for line_num, col_count, preview in invalid_lines[:10]:
            print(f"   Line {line_num}: {col_count} columns - {preview}...")
        if len(invalid_lines) > 10:
            print(f"   ... and {len(invalid_lines) - 10} more")

    # Write cleaned data
    output_file = output_file or input_file

    with open(output_file, 'w', encoding='utf-8') as f:
        for line in valid_lines:
            f.write(line + '\n')

    print(f"\n[OK] Cleaned data written to: {output_file}")
    print(f"[OK] Removed {len(invalid_lines)} invalid rows")

    # Verify the cleaned file can be read by pandas
    try:
        df = pd.read_csv(output_file)
        print(f"[OK] Verification: Pandas can read {len(df)} rows successfully")
        print(f"\n{'='*80}")
        print("CLEANING COMPLETE")
        print(f"{'='*80}\n")
        return True
    except Exception as e:
        print(f"\n[ERROR] Verification failed: {e}")
        print(f"[INFO] Restoring from backup...")
        shutil.copy2(backup_file, output_file)
        return False


if __name__ == '__main__':
    # Clean the main history file
    csv_file = 'aviator_rounds_history.csv'

    if os.path.exists(csv_file):
        success = clean_csv_file(csv_file)
        if success:
            print("You can now run: python train_models.py")
        else:
            print("Cleaning failed. Please check the errors above.")
    else:
        print(f"ERROR: {csv_file} not found in current directory")
        print(f"Current directory: {os.getcwd()}")
