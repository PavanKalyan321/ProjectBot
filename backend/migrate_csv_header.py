"""
Migrate CSV header from 11 columns to 16 columns
Fixes header mismatch in aviator_rounds_history.csv
"""

import os
import shutil
from datetime import datetime


def migrate_csv_header(csv_file="aviator_rounds_history.csv"):
    """
    Fix CSV header to match the 16-column schema used by history_tracker.py

    Args:
        csv_file: Path to CSV file to migrate

    Returns:
        bool: True if successful
    """
    if not os.path.exists(csv_file):
        print(f"ERROR: File not found: {csv_file}")
        return False

    print(f"\n{'='*80}")
    print("CSV HEADER MIGRATION")
    print(f"{'='*80}")
    print(f"File: {csv_file}")

    # Backup original file
    backup_file = f"{csv_file}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    shutil.copy2(csv_file, backup_file)
    print(f"[OK] Backup created: {backup_file}")

    # Read all lines
    with open(csv_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    if not lines:
        print("ERROR: File is empty")
        return False

    # Check current header
    current_header = lines[0].strip()
    current_col_count = len(current_header.split(','))

    print(f"\n[INFO] Current header has {current_col_count} columns")

    # Define correct 16-column header
    correct_header = (
        'timestamp,round_id,multiplier,'
        'bet_placed,stake_amount,cashout_time,'
        'profit_loss,model_prediction,model_confidence,'
        'model_predicted_range_low,model_predicted_range_high,'
        'pos2_confidence,pos2_target_multiplier,pos2_burst_probability,'
        'pos2_phase,pos2_rules_triggered'
    )

    if current_col_count == 16:
        print("[INFO] Header already has 16 columns, checking if it matches...")
        if current_header == correct_header:
            print("[OK] Header is already correct!")
            return True
        else:
            print("[INFO] Updating header to correct format...")
    elif current_col_count == 11:
        print("[INFO] Migrating from 11-column to 16-column header...")
    else:
        print(f"[WARNING] Unexpected column count: {current_col_count}")
        print("[INFO] Replacing with correct 16-column header...")

    # Write updated file
    with open(csv_file, 'w', encoding='utf-8') as f:
        # Write correct header
        f.write(correct_header + '\n')
        # Write all data rows (skip old header)
        f.writelines(lines[1:])

    print(f"[OK] Header updated to 16 columns")

    # Verify
    with open(csv_file, 'r', encoding='utf-8') as f:
        new_header = f.readline().strip()
        new_col_count = len(new_header.split(','))

    print(f"[OK] Verification: New header has {new_col_count} columns")

    # Try loading with pandas
    try:
        import pandas as pd
        df = pd.read_csv(csv_file)
        print(f"[OK] Pandas can read {len(df)} rows successfully")
        print(f"\nColumns in CSV:")
        for i, col in enumerate(df.columns, 1):
            print(f"  {i:2d}. {col}")
    except Exception as e:
        print(f"\n[ERROR] Verification failed: {e}")
        print(f"[INFO] Restoring from backup...")
        shutil.copy2(backup_file, csv_file)
        return False

    print(f"\n{'='*80}")
    print("MIGRATION COMPLETE")
    print(f"{'='*80}\n")
    return True


if __name__ == '__main__':
    csv_file = 'aviator_rounds_history.csv'

    if os.path.exists(csv_file):
        success = migrate_csv_header(csv_file)
        if success:
            print("✓ CSV header migration successful!")
            print("\nYou can now:")
            print("  1. Add manual history: python manual_history_loader.py")
            print("  2. Train models: python train_models.py")
            print("  3. Run the bot: python bot_modular.py")
        else:
            print("✗ Migration failed. Check errors above.")
    else:
        print(f"ERROR: {csv_file} not found")
        print(f"Current directory: {os.getcwd()}")
