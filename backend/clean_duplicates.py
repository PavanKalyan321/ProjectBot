"""
Clean duplicate entries from aviator_rounds_history.csv
Keeps only unique entries based on timestamp and multiplier combination.
"""

import pandas as pd
import shutil
from datetime import datetime

def clean_duplicates():
    """Remove duplicate entries from the CSV file."""

    csv_file = 'aviator_rounds_history.csv'
    backup_file = f'aviator_rounds_history_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'

    print("="*80)
    print("CLEANING DUPLICATE ENTRIES FROM CSV")
    print("="*80)

    # Create backup
    print(f"\n1. Creating backup: {backup_file}")
    shutil.copy(csv_file, backup_file)
    print(f"   [OK] Backup created successfully")

    # Read CSV
    print(f"\n2. Reading CSV file...")
    df = pd.read_csv(csv_file)
    original_count = len(df)
    print(f"   Total rows: {original_count}")

    # Check for duplicates
    duplicates = df[df.duplicated(subset=['timestamp', 'multiplier'], keep=False)]
    print(f"\n3. Duplicate analysis:")
    print(f"   Duplicate entries found: {len(duplicates)}")

    # Show sample duplicates
    if len(duplicates) > 0:
        print(f"\n   Sample duplicates:")
        sample = duplicates[['timestamp', 'multiplier', 'bet_placed', 'stake_amount']].head(10)
        print(sample.to_string(index=False))

    # Remove duplicates - keep first occurrence
    print(f"\n4. Removing duplicates (keeping first occurrence)...")
    df_cleaned = df.drop_duplicates(subset=['timestamp', 'multiplier'], keep='first')
    cleaned_count = len(df_cleaned)
    removed_count = original_count - cleaned_count

    print(f"   [OK] Removed {removed_count} duplicate entries")
    print(f"   Remaining rows: {cleaned_count}")

    # Save cleaned data
    print(f"\n5. Saving cleaned data to {csv_file}...")
    df_cleaned.to_csv(csv_file, index=False)
    print(f"   [OK] Cleaned data saved successfully")

    # Verify
    print(f"\n6. Verification:")
    df_verify = pd.read_csv(csv_file)
    duplicates_after = df_verify[df_verify.duplicated(subset=['timestamp', 'multiplier'], keep=False)]

    if len(duplicates_after) == 0:
        print(f"   [OK] No duplicates found in cleaned file")
    else:
        print(f"   [WARNING] Still {len(duplicates_after)} duplicates remain!")

    print(f"\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print(f"Original entries:      {original_count}")
    print(f"Duplicates removed:    {removed_count}")
    print(f"Final entries:         {cleaned_count}")
    print(f"Reduction:             {(removed_count/original_count)*100:.1f}%")
    print(f"\nBackup saved to:       {backup_file}")
    print("="*80)

    return removed_count, cleaned_count

if __name__ == "__main__":
    try:
        removed, final = clean_duplicates()
        print("\n[OK] Cleaning completed successfully!")
        print(f"\nThe CSV file is now clean and ready for model training.")
        print(f"You can delete the backup file if everything looks good.")
    except Exception as e:
        print(f"\n[ERROR] Error during cleaning: {e}")
        import traceback
        traceback.print_exc()
