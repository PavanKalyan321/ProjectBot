"""
Data Management Utilities
Clean, archive, and optimize data files
"""

import os
import pandas as pd
import shutil
from datetime import datetime, timedelta
import json


class DataManager:
    """Manage data files - cleanup, archive, consolidate."""

    def __init__(self):
        self.base_path = "backend"
        self.archive_path = os.path.join(self.base_path, "data", "archive")

        self.rounds_csv = os.path.join(self.base_path, "aviator_rounds_history.csv")
        self.bets_csv = os.path.join(self.base_path, "bet_history.csv")
        self.automl_csv = os.path.join(self.base_path, "bot_automl_performance.csv")

        # Ensure archive directory exists
        os.makedirs(self.archive_path, exist_ok=True)

    def cleanup_all(self):
        """Clean up all data files."""
        print("\n" + "="*60)
        print("  DATA CLEANUP UTILITY")
        print("="*60 + "\n")

        results = {
            'rounds': self._cleanup_rounds(),
            'bets': self._cleanup_bets(),
            'automl': self._cleanup_automl()
        }

        total_removed = sum(r['removed'] for r in results.values())

        print(f"\n{'='*60}")
        print(f"  CLEANUP COMPLETE")
        print(f"  Total rows removed: {total_removed}")
        print(f"{'='*60}\n")

        return results

    def _cleanup_rounds(self):
        """Clean up rounds history file."""
        print("Cleaning aviator_rounds_history.csv...")

        if not os.path.exists(self.rounds_csv):
            print("  ⚠ File not found")
            return {'removed': 0, 'kept': 0}

        try:
            # Read without header
            df = pd.read_csv(self.rounds_csv, header=None)
            original_len = len(df)

            # Add proper column names
            if len(df.columns) >= 3:
                df.columns = ['timestamp', 'round_id', 'multiplier'] + \
                             [f'col_{i}' for i in range(len(df.columns) - 3)]

                # Convert types
                df['multiplier'] = pd.to_numeric(df['multiplier'], errors='coerce')
                df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')

                # Remove duplicates by round_id
                df = df.drop_duplicates(subset=['round_id'], keep='last')

                # Remove rows with invalid multipliers
                df = df[df['multiplier'].notna()]
                df = df[df['multiplier'] > 0]

                # Remove rows with all zeros in optional columns
                optional_cols = [col for col in df.columns if col.startswith('col_')]
                if optional_cols:
                    df = df[~(df[optional_cols] == 0).all(axis=1)]

                # Sort by timestamp
                df = df.sort_values('timestamp')

                # Save with proper header
                df.to_csv(self.rounds_csv, index=False)

                removed = original_len - len(df)
                print(f"  ✓ Removed: {removed} rows")
                print(f"  ✓ Kept: {len(df)} rows")

                return {'removed': removed, 'kept': len(df)}

        except Exception as e:
            print(f"  ✗ Error: {e}")
            return {'removed': 0, 'kept': 0}

    def _cleanup_bets(self):
        """Clean up bet history file."""
        print("\nCleaning bet_history.csv...")

        if not os.path.exists(self.bets_csv):
            print("  ⚠ File not found")
            return {'removed': 0, 'kept': 0}

        try:
            df = pd.read_csv(self.bets_csv)
            original_len = len(df)

            # Remove duplicates
            if 'Round ID' in df.columns:
                df = df.drop_duplicates(subset=['Round ID'], keep='last')

            # Remove rows with no bet placed and zero values
            if 'Bet Placed' in df.columns and 'Profit/Loss' in df.columns:
                # Keep rows where bet was placed OR there's actual data
                df = df[
                    (df['Bet Placed'] == 'Yes') |
                    (df['Profit/Loss'] != 0) |
                    (df['Stake'] != 0)
                ]

            # Sort by timestamp
            if 'Timestamp' in df.columns:
                df['Timestamp'] = pd.to_datetime(df['Timestamp'], errors='coerce')
                df = df.sort_values('Timestamp')

            df.to_csv(self.bets_csv, index=False)

            removed = original_len - len(df)
            print(f"  ✓ Removed: {removed} rows")
            print(f"  ✓ Kept: {len(df)} rows")

            return {'removed': removed, 'kept': len(df)}

        except Exception as e:
            print(f"  ✗ Error: {e}")
            return {'removed': 0, 'kept': 0}

    def _cleanup_automl(self):
        """Clean up AutoML performance file."""
        print("\nCleaning bot_automl_performance.csv...")

        if not os.path.exists(self.automl_csv):
            print("  ⚠ File not found")
            return {'removed': 0, 'kept': 0}

        try:
            df = pd.read_csv(self.automl_csv)
            original_len = len(df)

            # Remove duplicates
            if 'round_id' in df.columns:
                df = df.drop_duplicates(subset=['round_id'], keep='last')

            # Remove rows with invalid data
            if 'actual_multiplier' in df.columns:
                df = df[df['actual_multiplier'].notna()]
                df = df[df['actual_multiplier'] > 0]

            # Sort by timestamp
            if 'timestamp' in df.columns:
                df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
                df = df.sort_values('timestamp')

            df.to_csv(self.automl_csv, index=False)

            removed = original_len - len(df)
            print(f"  ✓ Removed: {removed} rows")
            print(f"  ✓ Kept: {len(df)} rows")

            return {'removed': removed, 'kept': len(df)}

        except Exception as e:
            print(f"  ✗ Error: {e}")
            return {'removed': 0, 'kept': 0}

    def archive_old_data(self, days_to_keep=30):
        """Archive data older than specified days."""
        print(f"\n{'='*60}")
        print(f"  ARCHIVING DATA OLDER THAN {days_to_keep} DAYS")
        print(f"{'='*60}\n")

        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        archive_date = datetime.now().strftime("%Y%m%d_%H%M%S")

        results = {}

        # Archive rounds
        if os.path.exists(self.rounds_csv):
            results['rounds'] = self._archive_file(
                self.rounds_csv,
                'timestamp',
                cutoff_date,
                f"rounds_archive_{archive_date}.csv"
            )

        # Archive bets
        if os.path.exists(self.bets_csv):
            results['bets'] = self._archive_file(
                self.bets_csv,
                'Timestamp',
                cutoff_date,
                f"bets_archive_{archive_date}.csv"
            )

        # Archive AutoML
        if os.path.exists(self.automl_csv):
            results['automl'] = self._archive_file(
                self.automl_csv,
                'timestamp',
                cutoff_date,
                f"automl_archive_{archive_date}.csv"
            )

        print(f"\n{'='*60}")
        print(f"  ARCHIVING COMPLETE")
        print(f"{'='*60}\n")

        return results

    def _archive_file(self, file_path, timestamp_col, cutoff_date, archive_name):
        """Archive old data from a file."""
        try:
            df = pd.read_csv(file_path)

            if timestamp_col not in df.columns:
                print(f"  ⚠ No {timestamp_col} column in {os.path.basename(file_path)}")
                return {'archived': 0, 'kept': len(df)}

            # Convert timestamp
            df[timestamp_col] = pd.to_datetime(df[timestamp_col], errors='coerce')

            # Split old and new data
            old_data = df[df[timestamp_col] < cutoff_date]
            new_data = df[df[timestamp_col] >= cutoff_date]

            if len(old_data) > 0:
                # Save old data to archive
                archive_path = os.path.join(self.archive_path, archive_name)
                old_data.to_csv(archive_path, index=False)

                # Save only new data to original file
                new_data.to_csv(file_path, index=False)

                print(f"  ✓ {os.path.basename(file_path)}:")
                print(f"    - Archived: {len(old_data)} rows → {archive_name}")
                print(f"    - Kept: {len(new_data)} rows")

                return {'archived': len(old_data), 'kept': len(new_data)}
            else:
                print(f"  ℹ {os.path.basename(file_path)}: No old data to archive")
                return {'archived': 0, 'kept': len(df)}

        except Exception as e:
            print(f"  ✗ Error archiving {os.path.basename(file_path)}: {e}")
            return {'archived': 0, 'kept': 0}

    def consolidate_data(self):
        """Consolidate all data into a single file."""
        print(f"\n{'='*60}")
        print(f"  CONSOLIDATING DATA")
        print(f"{'='*60}\n")

        try:
            # Load all files
            rounds_df = pd.read_csv(self.rounds_csv) if os.path.exists(self.rounds_csv) else pd.DataFrame()
            automl_df = pd.read_csv(self.automl_csv) if os.path.exists(self.automl_csv) else pd.DataFrame()
            bets_df = pd.read_csv(self.bets_csv) if os.path.exists(self.bets_csv) else pd.DataFrame()

            # Start with AutoML as base (most comprehensive)
            if not automl_df.empty:
                consolidated = automl_df.copy()
            elif not rounds_df.empty:
                consolidated = rounds_df.copy()
            else:
                print("  ⚠ No data to consolidate")
                return None

            # Merge with bets data
            if not bets_df.empty and 'Round ID' in bets_df.columns and 'round_id' in consolidated.columns:
                bets_df = bets_df.rename(columns={'Round ID': 'round_id'})
                consolidated = consolidated.merge(
                    bets_df[['round_id', 'Bet Placed', 'Stake', 'Profit/Loss', 'Cumulative P/L']],
                    on='round_id',
                    how='left',
                    suffixes=('', '_bet')
                )

            # Save consolidated file
            output_path = os.path.join(
                self.base_path,
                f"consolidated_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            )
            consolidated.to_csv(output_path, index=False)

            print(f"  ✓ Consolidated {len(consolidated)} rows")
            print(f"  ✓ Saved to: {output_path}")

            return output_path

        except Exception as e:
            print(f"  ✗ Error: {e}")
            return None

    def get_data_summary(self):
        """Get summary of all data files."""
        print(f"\n{'='*60}")
        print(f"  DATA SUMMARY")
        print(f"{'='*60}\n")

        summary = {}

        for name, path in [
            ('Rounds History', self.rounds_csv),
            ('Bet History', self.bets_csv),
            ('AutoML Performance', self.automl_csv)
        ]:
            if os.path.exists(path):
                size_mb = os.path.getsize(path) / (1024 * 1024)
                df = pd.read_csv(path)

                print(f"{name}:")
                print(f"  - Rows: {len(df):,}")
                print(f"  - Size: {size_mb:.2f} MB")
                print(f"  - Columns: {len(df.columns)}")

                summary[name] = {
                    'rows': len(df),
                    'size_mb': round(size_mb, 2),
                    'columns': len(df.columns)
                }
            else:
                print(f"{name}: Not found")
                summary[name] = None

        print(f"\n{'='*60}\n")

        return summary


if __name__ == '__main__':
    import sys

    manager = DataManager()

    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == 'cleanup':
            manager.cleanup_all()
        elif command == 'archive':
            days = int(sys.argv[2]) if len(sys.argv) > 2 else 30
            manager.archive_old_data(days)
        elif command == 'consolidate':
            manager.consolidate_data()
        elif command == 'summary':
            manager.get_data_summary()
        else:
            print(f"Unknown command: {command}")
            print("Usage: python data_manager.py [cleanup|archive|consolidate|summary]")
    else:
        # Interactive mode
        print("\nData Manager - Interactive Mode")
        print("1. Cleanup data (remove duplicates, fix headers)")
        print("2. Archive old data (move to archive folder)")
        print("3. Consolidate data (merge into single file)")
        print("4. Data summary")
        print("5. Exit")

        choice = input("\nEnter choice (1-5): ")

        if choice == '1':
            manager.cleanup_all()
        elif choice == '2':
            days = input("Keep how many days of data? (default: 30): ")
            days = int(days) if days else 30
            manager.archive_old_data(days)
        elif choice == '3':
            manager.consolidate_data()
        elif choice == '4':
            manager.get_data_summary()
        elif choice == '5':
            print("Goodbye!")
        else:
            print("Invalid choice")
