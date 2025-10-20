"""
Test script for realistic timestamp generation and duplicate removal
"""

from manual_history_loader import (
    generate_realistic_timestamps,
    generate_realistic_round_ids,
    remove_duplicate_multipliers,
    ManualHistoryLoader
)

def test_timestamp_generation():
    """Test realistic timestamp generation."""
    print("="*80)
    print("TEST 1: Realistic Timestamp Generation")
    print("="*80)

    # Generate timestamps for 20 rounds
    num_rounds = 20
    timestamps = generate_realistic_timestamps(num_rounds, avg_round_duration=10)

    print(f"\nGenerated {len(timestamps)} timestamps:")
    print(f"Oldest: {timestamps[0]}")
    print(f"Newest: {timestamps[-1]}")

    # Show first 5 and last 5
    print("\nFirst 5:")
    for i, ts in enumerate(timestamps[:5]):
        print(f"  {i+1}. {ts}")

    print("\nLast 5:")
    for i, ts in enumerate(timestamps[-5:], len(timestamps)-4):
        print(f"  {i}. {ts}")

    # Calculate time differences
    from datetime import datetime
    diffs = []
    for i in range(1, len(timestamps)):
        t1 = datetime.strptime(timestamps[i-1], "%Y-%m-%d %H:%M:%S")
        t2 = datetime.strptime(timestamps[i], "%Y-%m-%d %H:%M:%S")
        diff = (t2 - t1).total_seconds()
        diffs.append(diff)

    avg_diff = sum(diffs) / len(diffs)
    print(f"\nAverage time between rounds: {avg_diff:.2f} seconds")
    print(f"Min: {min(diffs):.2f}s, Max: {max(diffs):.2f}s")


def test_duplicate_removal():
    """Test duplicate removal."""
    print("\n" + "="*80)
    print("TEST 2: Duplicate Removal")
    print("="*80)

    # Test data with duplicates
    test_cases = [
        {
            'name': 'Consecutive duplicates',
            'data': [1.5, 1.5, 2.0, 2.0, 2.0, 3.0, 3.0, 4.0]
        },
        {
            'name': 'Scattered duplicates',
            'data': [1.5, 2.0, 3.0, 1.5, 4.0, 2.0, 5.0]
        },
        {
            'name': 'No duplicates',
            'data': [1.5, 2.0, 3.0, 4.0, 5.0]
        },
        {
            'name': 'All duplicates',
            'data': [2.5, 2.5, 2.5, 2.5]
        }
    ]

    for test in test_cases:
        print(f"\n{test['name']}:")
        print(f"  Original: {test['data']} ({len(test['data'])} items)")
        cleaned, removed = remove_duplicate_multipliers(test['data'])
        print(f"  Cleaned:  {cleaned} ({len(cleaned)} items)")
        print(f"  Removed:  {removed} duplicates")


def test_full_workflow():
    """Test full workflow with realistic timestamps."""
    print("\n" + "="*80)
    print("TEST 3: Full Workflow")
    print("="*80)

    # Sample multipliers with some duplicates
    sample_mults = [
        2.54, 1.89, 3.21, 2.54,  # duplicate 2.54
        1.56, 4.44, 1.89,  # duplicate 1.89
        5.67, 8.90, 12.34,
        1.23, 4.56, 7.89,
        2.11, 3.33, 5.55
    ]

    print(f"\nSample data: {len(sample_mults)} multipliers")
    print(f"Contains duplicates: 2.54 (appears 2x), 1.89 (appears 2x)")

    # Test the save function
    loader = ManualHistoryLoader(csv_file="test_manual_history.csv")

    print("\nTesting save_to_csv with realistic timestamps...")
    success = loader.save_to_csv(
        sample_mults,
        append=False,
        use_realistic_timestamps=True,
        avg_round_duration=10
    )

    if success:
        print("\n[SUCCESS] Data saved successfully!")

        # Read back and verify
        import pandas as pd
        df = pd.read_csv("test_manual_history.csv")

        print(f"\nVerification:")
        print(f"  Rows in CSV: {len(df)}")
        print(f"  Unique multipliers: {df['multiplier'].nunique()}")
        print(f"  pos2_phase values: {df['pos2_phase'].unique()}")

        print(f"\nTimestamp distribution:")
        print(f"  Oldest: {df['timestamp'].iloc[0]}")
        print(f"  Newest: {df['timestamp'].iloc[-1]}")

        # Clean up test file
        import os
        os.remove("test_manual_history.csv")
        print("\n[OK] Test file cleaned up")
    else:
        print("\n[ERROR] Save failed!")


if __name__ == "__main__":
    print("\n" + "="*80)
    print("REALISTIC TIMESTAMP & DUPLICATE REMOVAL TESTS")
    print("="*80)

    test_timestamp_generation()
    test_duplicate_removal()
    test_full_workflow()

    print("\n" + "="*80)
    print("ALL TESTS COMPLETE!")
    print("="*80)
