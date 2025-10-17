"""
Manual History Loader - Load previous rounds at startup for better ML predictions
Enhanced clipboard parsing for jammed multipliers and special characters
"""

import csv
import os
from datetime import datetime
import re


def parse_multiplier_robust(text):
    """
    Robustly parse multiplier from text, handling multiple values and special characters.
    
    Args:
        text: Text that may contain multiplier(s), dashes, or multiple values
        
    Returns:
        float or None: The LAST valid multiplier found, or None
    """
    if not text:
        return None
    
    # Clean the text
    text = str(text).strip()
    
    # Replace common separators with spaces
    text = text.replace(',', ' ').replace('|', ' ').replace('/', ' ')
    
    # Split by whitespace and dashes
    parts = re.split(r'[\s\-]+', text)
    
    # Try to find all valid multipliers
    multipliers = []
    
    for part in parts:
        if not part or part == '-':
            continue
        
        # Remove 'x' suffix/prefix
        part = part.replace('x', '').replace('X', '').strip()
        
        if not part:
            continue
        
        try:
            # Try to parse as float
            value = float(part)
            
            # Validate range (0.01 to 10000)
            if 0.01 <= value <= 10000:
                multipliers.append(value)
        except ValueError:
            continue
    
    # Return the LAST multiplier found (most recent)
    if multipliers:
        return multipliers[-1]
    
    return None


def extract_all_multipliers(text):
    """
    Extract ALL multipliers from text (for jammed up values).
    
    Args:
        text: Text containing one or more multipliers
        
    Returns:
        list: All valid multipliers found
    """
    if not text:
        return []
    
    text = str(text).strip()
    
    # Replace separators with spaces
    text = text.replace(',', ' ').replace('|', ' ').replace('/', ' ')
    
    # Split by whitespace and dashes
    parts = re.split(r'[\s\-]+', text)
    
    multipliers = []
    
    for part in parts:
        if not part or part == '-':
            continue
        
        # Remove 'x' suffix/prefix
        part = part.replace('x', '').replace('X', '').strip()
        
        if not part:
            continue
        
        try:
            value = float(part)
            if 0.01 <= value <= 10000:
                multipliers.append(value)
        except ValueError:
            continue
    
    return multipliers


class ManualHistoryLoader:
    """Load and manage manual history input for better ML predictions."""

    def __init__(self, csv_file="aviator_rounds_history.csv"):
        self.csv_file = csv_file
        self.history = []
    
    def parse_multipliers_from_text(self, text):
        """
        Parse multipliers from a text string (one per line or space-separated).
        Enhanced to handle jammed values and special characters.
        
        Args:
            text: String containing multipliers
            
        Returns:
            List of float multipliers
        """
        multipliers = []
        
        # Split by newlines
        lines = text.strip().split('\n')
        
        for line in lines:
            # Extract all multipliers from this line
            line_mults = extract_all_multipliers(line)
            multipliers.extend(line_mults)
        
        return multipliers
    
    def parse_multipliers_from_file(self, filepath):
        """
        Parse multipliers from a text file.
        
        Args:
            filepath: Path to text file containing multipliers
            
        Returns:
            List of float multipliers
        """
        try:
            with open(filepath, 'r') as f:
                text = f.read()
            return self.parse_multipliers_from_text(text)
        except Exception as e:
            print(f"❌ Error reading file: {e}")
            return []
    
    def load_from_manual_input(self):
        """
        Interactive manual input of multipliers.
        
        Returns:
            List of float multipliers
        """
        print("\n" + "="*80)
        print("📝 MANUAL HISTORY INPUT")
        print("="*80)
        print("\nYou can input previous round multipliers in several ways:")
        print("  1. Paste all multipliers (press Enter twice when done)")
        print("  2. Load from file")
        print("  3. Skip manual input")
        print("="*80)
        
        choice = input("\nChoice (1/2/3): ").strip()
        
        if choice == '1':
            return self._input_paste_mode()
        elif choice == '2':
            return self._input_file_mode()
        else:
            print("\n⏭️  Skipping manual history input")
            return []
    
    def _input_paste_mode(self):
        """Get multipliers from paste input."""
        print("\n📋 PASTE MODE")
        print("="*80)
        print("Paste your multipliers (one per line or space-separated)")
        print("Handles: jammed values (2.5 3.4), dashes (2.5 - 3.4), mixed formats")
        print("Press Enter twice (empty line) when done:")
        print("-"*80)
        
        lines = []
        empty_count = 0
        
        while empty_count < 2:
            try:
                line = input()
                if not line.strip():
                    empty_count += 1
                else:
                    empty_count = 0
                    lines.append(line)
            except EOFError:
                break
        
        text = '\n'.join(lines)
        multipliers = self.parse_multipliers_from_text(text)
        
        print(f"\n✅ Parsed {len(multipliers)} multipliers")
        if multipliers:
            print(f"📊 Range: {min(multipliers):.2f}x - {max(multipliers):.2f}x")
            print(f"📈 Average: {sum(multipliers)/len(multipliers):.2f}x")
            
            # Show first few and last few
            if len(multipliers) > 10:
                preview = multipliers[:5] + ['...'] + multipliers[-5:]
                print(f"📋 Preview: {', '.join(str(m) if isinstance(m, str) else f'{m:.2f}x' for m in preview)}")
        
        return multipliers
    
    def _input_file_mode(self):
        """Get multipliers from file."""
        print("\n📁 FILE MODE")
        print("="*80)
        filepath = input("Enter file path: ").strip().strip('"').strip("'")
        
        if not os.path.exists(filepath):
            print(f"❌ File not found: {filepath}")
            return []
        
        multipliers = self.parse_multipliers_from_file(filepath)
        
        print(f"\n✅ Parsed {len(multipliers)} multipliers from file")
        if multipliers:
            print(f"📊 Range: {min(multipliers):.2f}x - {max(multipliers):.2f}x")
            print(f"📈 Average: {sum(multipliers)/len(multipliers):.2f}x")
        
        return multipliers
    
    def save_to_csv(self, multipliers, append=True):
        """
        Save multipliers to CSV file.
        
        Args:
            multipliers: List of multipliers to save
            append: If True, append to existing file; if False, overwrite
        """
        mode = 'a' if append and os.path.exists(self.csv_file) else 'w'
        file_exists = os.path.exists(self.csv_file) and append
        
        try:
            with open(self.csv_file, mode, newline='') as f:
                writer = csv.writer(f)
                
                # Write header if new file (must match history_tracker.py schema!)
                if not file_exists:
                    writer.writerow([
                        'timestamp', 'round_id', 'multiplier',
                        'bet_placed', 'stake_amount', 'cashout_time',
                        'profit_loss', 'model_prediction', 'model_confidence',
                        'model_predicted_range_low', 'model_predicted_range_high',
                        'pos2_confidence', 'pos2_target_multiplier', 'pos2_burst_probability',
                        'pos2_phase', 'pos2_rules_triggered'
                    ])
                
                # Write multipliers (must match 16-column schema!)
                for mult in multipliers:
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    round_id = datetime.now().strftime("%Y%m%d%H%M%S%f")

                    writer.writerow([
                        timestamp,
                        round_id,
                        mult,
                        False,  # bet_placed
                        0,      # stake_amount
                        0,      # cashout_time
                        0,      # profit_loss
                        0,      # model_prediction
                        0,      # model_confidence
                        0,      # model_predicted_range_low
                        0,      # model_predicted_range_high
                        0,      # pos2_confidence
                        0,      # pos2_target_multiplier
                        0,      # pos2_burst_probability
                        'manual',  # pos2_phase
                        ''      # pos2_rules_triggered
                    ])
            
            print(f"\n✅ Saved {len(multipliers)} multipliers to {self.csv_file}")
            return True
        except Exception as e:
            print(f"\n❌ Error saving to CSV: {e}")
            return False
    
    def load_history_for_tracker(self, history_tracker):
        """
        Load manual history into RoundHistoryTracker.
        
        Args:
            history_tracker: RoundHistoryTracker instance
            
        Returns:
            int: Number of rounds loaded
        """
        # Get manual input
        multipliers = self.load_from_manual_input()
        
        if not multipliers:
            return 0
        
        # Ask if user wants to save to CSV
        save_choice = input("\n💾 Save to CSV? (y/n, default: y): ").strip().lower()
        if save_choice != 'n':
            self.save_to_csv(multipliers, append=True)
        
        # Load into tracker
        print(f"\n📥 Loading {len(multipliers)} rounds into tracker...")
        
        count = 0
        for mult in multipliers:
            try:
                # Add to history tracker as observed (non-bet) rounds
                # Match your CSV header structure
                history_tracker.log_round(
                    multiplier=mult,
                    bet_placed=False,
                    stake=0,
                    cashout_time=0,
                    profit_loss=0,
                    prediction=0,
                    confidence=0,
                    pred_range=(0, 0)
                )
                count += 1
            except Exception as e:
                print(f"⚠️  Error logging round {mult}: {e}")
                continue
        
        print(f"✅ Successfully loaded {count} rounds")

        # Get recent rounds to show total history size
        recent_df = history_tracker.get_recent_rounds(10000)
        if not recent_df.empty:
            print(f"📊 Total history size: {len(recent_df)}")

        return count
    
    def show_statistics(self, multipliers):
        """Show statistics about loaded multipliers."""
        if not multipliers:
            return
        
        print("\n" + "="*80)
        print("📊 LOADED HISTORY STATISTICS")
        print("="*80)
        
        # Basic stats
        print(f"Total rounds:     {len(multipliers)}")
        print(f"Min multiplier:   {min(multipliers):.2f}x")
        print(f"Max multiplier:   {max(multipliers):.2f}x")
        print(f"Average:          {sum(multipliers)/len(multipliers):.2f}x")
        print(f"Median:           {sorted(multipliers)[len(multipliers)//2]:.2f}x")
        
        # Range distribution
        low = sum(1 for m in multipliers if m < 2.0)
        medium = sum(1 for m in multipliers if 2.0 <= m < 10.0)
        high = sum(1 for m in multipliers if m >= 10.0)
        
        print(f"\n📈 Range Distribution:")
        print(f"  Low (< 2x):      {low:4d} ({low/len(multipliers)*100:5.1f}%)")
        print(f"  Medium (2-10x):  {medium:4d} ({medium/len(multipliers)*100:5.1f}%)")
        print(f"  High (>= 10x):   {high:4d} ({high/len(multipliers)*100:5.1f}%)")
        
        # Notable multipliers
        very_high = [m for m in multipliers if m >= 100]
        if very_high:
            print(f"\n🚀 Very High Multipliers (>= 100x):")
            for m in sorted(very_high, reverse=True)[:5]:
                print(f"  {m:.2f}x")
        
        print("="*80)


def integrate_manual_history_with_bot(bot):
    """
    Integrate manual history loading with the bot.
    
    Args:
        bot: AviatorBotML instance
        
    Returns:
        int: Number of rounds loaded
    """
    if not bot.history_tracker:
        print("⚠️  No history tracker available")
        return 0
    
    loader = ManualHistoryLoader(csv_file="aviator_rounds_history.csv")
    
    # Check if CSV exists and has data
    if os.path.exists(loader.csv_file):
        print(f"\n📁 Found existing history file: {loader.csv_file}")
        
        # Count existing rounds
        try:
            with open(loader.csv_file, 'r') as f:
                existing_count = sum(1 for _ in f) - 1  # Subtract header
            print(f"📊 Existing rounds in file: {existing_count}")
        except:
            existing_count = 0
    
    # Ask if user wants to add manual history
    print("\n" + "="*80)
    add_manual = input("📝 Add manual history for better predictions? (y/n, default: y): ").strip().lower()
    
    if add_manual == 'n':
        print("⏭️  Skipping manual history")
        return 0
    
    # Load manual history
    count = loader.load_history_for_tracker(bot.history_tracker)
    
    if count > 0:
        # Show statistics
        loader.show_statistics(bot.history_tracker.get_recent_multipliers(count))
        
        # Update ML model if needed
        if bot.ml_generator:
            print("\n🤖 ML models will use this history for predictions")
    
    return count


# Example usage function
def test_robust_parsing():
    """Test the robust parsing with edge cases."""
    test_cases = [
        "2.54 3.45",           # Jammed up
        "2.54 - 3.45",         # With dash
        "2.54-3.45",           # Dash no spaces
        "2.54x 3.45x",         # With x
        "- 2.54",              # Leading dash
        "2.54 -",              # Trailing dash
        "2.54 - - 3.45",       # Multiple dashes
        "2.54,3.45",           # Comma separated
        "2.54 | 3.45",         # Pipe separated
        "  2.54   3.45  ",     # Extra spaces
        "2.54\n3.45",          # Newline
    ]
    
    print("="*80)
    print("🧪 ROBUST PARSING TESTS")
    print("="*80)
    
    for test in test_cases:
        result = extract_all_multipliers(test)
        last = parse_multiplier_robust(test)
        print(f"\nInput:  '{test}'")
        print(f"All:    {result}")
        print(f"Last:   {last}")
    
    print("\n" + "="*80)


def load_sample_data():
    """Load the sample data you provided."""
    sample_text = """
1.64 1 2.54 10.74 1.29 1.54 1.12 1.68 1.23 5.6 4.16 3.93 1.02 10.7 3.28 1.14 
1.42 32.79 1.8 2.1 1.7 4.52 1.06 1.46 1.59 38.98 1.75 4.36 1.24 1.13 1.3 1.76 
5.3 1 1.84 1.15 2.59 1 1.94 1.56 1.61 1.05 4.83 4.47 2.03 1.33 4.17 3.84 1.29 
2.71 1.98 1.34 2.97 6.03 1.37 1 1 1.3 1.34 3.47 13.85 1.32 4.67 1.37 1.57 2.06 
1.08 3.81 3.06 1.58 1.14 2.3 135.31 1.92 1.51 1.01 1.5 1.41 31.37 1.06 2.12 1.5 
4.33 1.46 1.2 1.14 6.84 1.55 1.03 1.13 116.7 1.83 1.87 1.01 1.98 1.1 1.48 1.17 
1.09 3.21 1.39 1.63 5.05 1.17 3.01 3.39 2.68 15.06 1.49 1.52 4.12 1.36 2.43 2.32 
2.35 1.85 1.1 2.06 1.27 1.78 2.02 2.98 1.64 3.53 2.38 2.24 1.03 1.15 2.21 17.58 
4.94 2.09 1.25 1.09 2.85 2.26 1.55 1.42 5.49 1.1 1.19 2.87 2.26 1.94 1 7.8 1.73 
2.18 3.65 32.93 1.22 6.69 1.14 1.02 1.81 7.13 1.02 1.45 3.56 1.15 3.51 445.52 1 
1.82 3.36 2.69 1.06 4.04 1.16 1.07 1.05 1 26.24 1.23 7.28 1.23 3.56 1.21 1.4 
3.96 5.1 1.2 1.09 18.68 4.07 3.46 2.61 7.22 1.67 22.53 12.81
"""
    
    loader = ManualHistoryLoader()
    multipliers = loader.parse_multipliers_from_text(sample_text)
    
    print(f"\n✅ Loaded {len(multipliers)} multipliers from sample data")
    loader.show_statistics(multipliers)
    
    return multipliers


if __name__ == "__main__":
    # Test the loader
    print("="*80)
    print("🧪 MANUAL HISTORY LOADER - TEST MODE")
    print("="*80)
    
    # Test robust parsing
    test_robust_parsing()
    
    print("\n")
    
    # Load sample data
    multipliers = load_sample_data()
    
    # Save to CSV
    if multipliers:
        loader = ManualHistoryLoader()
        loader.save_to_csv(multipliers, append=False)
        print(f"\n💾 Saved to {loader.csv_file}")

    """Load and manage manual history input for better ML predictions."""
    
    def __init__(self, csv_file="aviator_history.csv"):
        self.csv_file = csv_file
        self.history = []
    
    def parse_multipliers_from_text(self, text):
        """
        Parse multipliers from a text string (one per line or space-separated).
        
        Args:
            text: String containing multipliers
            
        Returns:
            List of float multipliers
        """
        multipliers = []
        
        # Split by newlines and spaces
        lines = text.strip().split('\n')
        
        for line in lines:
            # Split by spaces/commas
            parts = re.split(r'[,\s]+', line.strip())
            
            for part in parts:
                if not part:
                    continue
                
                try:
                    # Try to parse as float
                    mult = float(part.replace('x', '').strip())
                    
                    # Validate range (0.01 to 10000)
                    if 0.01 <= mult <= 10000:
                        multipliers.append(mult)
                except ValueError:
                    continue
        
        return multipliers
    
    def parse_multipliers_from_file(self, filepath):
        """
        Parse multipliers from a text file.
        
        Args:
            filepath: Path to text file containing multipliers
            
        Returns:
            List of float multipliers
        """
        try:
            with open(filepath, 'r') as f:
                text = f.read()
            return self.parse_multipliers_from_text(text)
        except Exception as e:
            print(f"❌ Error reading file: {e}")
            return []
    
    def load_from_manual_input(self):
        """
        Interactive manual input of multipliers.
        
        Returns:
            List of float multipliers
        """
        print("\n" + "="*80)
        print("📝 MANUAL HISTORY INPUT")
        print("="*80)
        print("\nYou can input previous round multipliers in several ways:")
        print("  1. Paste all multipliers (press Enter twice when done)")
        print("  2. Load from file")
        print("  3. Skip manual input")
        print("="*80)
        
        choice = input("\nChoice (1/2/3): ").strip()
        
        if choice == '1':
            return self._input_paste_mode()
        elif choice == '2':
            return self._input_file_mode()
        else:
            print("\n⏭️  Skipping manual history input")
            return []
    
    def _input_paste_mode(self):
        """Get multipliers from paste input."""
        print("\n📋 PASTE MODE")
        print("="*80)
        print("Paste your multipliers (one per line or space-separated)")
        print("Press Enter twice (empty line) when done:")
        print("-"*80)
        
        lines = []
        empty_count = 0
        
        while empty_count < 2:
            try:
                line = input()
                if not line.strip():
                    empty_count += 1
                else:
                    empty_count = 0
                    lines.append(line)
            except EOFError:
                break
        
        text = '\n'.join(lines)
        multipliers = self.parse_multipliers_from_text(text)
        
        print(f"\n✅ Parsed {len(multipliers)} multipliers")
        if multipliers:
            print(f"📊 Range: {min(multipliers):.2f}x - {max(multipliers):.2f}x")
            print(f"📈 Average: {sum(multipliers)/len(multipliers):.2f}x")
        
        return multipliers
    
    def _input_file_mode(self):
        """Get multipliers from file."""
        print("\n📁 FILE MODE")
        print("="*80)
        filepath = input("Enter file path: ").strip().strip('"').strip("'")
        
        if not os.path.exists(filepath):
            print(f"❌ File not found: {filepath}")
            return []
        
        multipliers = self.parse_multipliers_from_file(filepath)
        
        print(f"\n✅ Parsed {len(multipliers)} multipliers from file")
        if multipliers:
            print(f"📊 Range: {min(multipliers):.2f}x - {max(multipliers):.2f}x")
            print(f"📈 Average: {sum(multipliers)/len(multipliers):.2f}x")
        
        return multipliers
    
    def save_to_csv(self, multipliers, append=True):
        """
        Save multipliers to CSV file.
        
        Args:
            multipliers: List of multipliers to save
            append: If True, append to existing file; if False, overwrite
        """
        mode = 'a' if append and os.path.exists(self.csv_file) else 'w'
        file_exists = os.path.exists(self.csv_file) and append
        
        try:
            with open(self.csv_file, mode, newline='') as f:
                writer = csv.writer(f)
                
                # Write header if new file (must match history_tracker.py schema!)
                if not file_exists:
                    writer.writerow([
                        'timestamp', 'round_id', 'multiplier',
                        'bet_placed', 'stake_amount', 'cashout_time',
                        'profit_loss', 'model_prediction', 'model_confidence',
                        'model_predicted_range_low', 'model_predicted_range_high',
                        'pos2_confidence', 'pos2_target_multiplier', 'pos2_burst_probability',
                        'pos2_phase', 'pos2_rules_triggered'
                    ])
                
                # Write multipliers (must match 16-column schema!)
                for mult in multipliers:
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    round_id = datetime.now().strftime("%Y%m%d%H%M%S%f")

                    writer.writerow([
                        timestamp,
                        round_id,
                        mult,
                        False,  # bet_placed
                        0,      # stake_amount
                        0,      # cashout_time
                        0,      # profit_loss
                        0,      # model_prediction
                        0,      # model_confidence
                        0,      # model_predicted_range_low
                        0,      # model_predicted_range_high
                        0,      # pos2_confidence
                        0,      # pos2_target_multiplier
                        0,      # pos2_burst_probability
                        'manual',  # pos2_phase
                        ''      # pos2_rules_triggered
                    ])
            
            print(f"\n✅ Saved {len(multipliers)} multipliers to {self.csv_file}")
            return True
        except Exception as e:
            print(f"\n❌ Error saving to CSV: {e}")
            return False
    
    def load_history_for_tracker(self, history_tracker):
        """
        Load manual history into RoundHistoryTracker.
        
        Args:
            history_tracker: RoundHistoryTracker instance
            
        Returns:
            int: Number of rounds loaded
        """
        # Get manual input
        multipliers = self.load_from_manual_input()
        
        if not multipliers:
            return 0
        
        # Ask if user wants to save to CSV
        save_choice = input("\n💾 Save to CSV? (y/n, default: y): ").strip().lower()
        if save_choice != 'n':
            self.save_to_csv(multipliers, append=True)
        
        # Load into tracker
        print(f"\n📥 Loading {len(multipliers)} rounds into tracker...")
        
        count = 0
        for mult in multipliers:
            try:
                # Add to history tracker as observed (non-bet) rounds
                history_tracker.log_round(
                    multiplier=mult,
                    bet_placed=False,
                    stake=0,
                    cashout_time=0,
                    profit_loss=0,
                    prediction=0,
                    confidence=0,
                    pred_range=(0, 0)
                )
                count += 1
            except Exception as e:
                print(f"⚠️  Error logging round {mult}: {e}")
                continue
        
        print(f"✅ Successfully loaded {count} rounds")

        # Get recent rounds to show total history size
        recent_df = history_tracker.get_recent_rounds(10000)
        if not recent_df.empty:
            print(f"📊 Total history size: {len(recent_df)}")

        return count
    
    def show_statistics(self, multipliers):
        """Show statistics about loaded multipliers."""
        if not multipliers:
            return
        
        print("\n" + "="*80)
        print("📊 LOADED HISTORY STATISTICS")
        print("="*80)
        
        # Basic stats
        print(f"Total rounds:     {len(multipliers)}")
        print(f"Min multiplier:   {min(multipliers):.2f}x")
        print(f"Max multiplier:   {max(multipliers):.2f}x")
        print(f"Average:          {sum(multipliers)/len(multipliers):.2f}x")
        print(f"Median:           {sorted(multipliers)[len(multipliers)//2]:.2f}x")
        
        # Range distribution
        low = sum(1 for m in multipliers if m < 2.0)
        medium = sum(1 for m in multipliers if 2.0 <= m < 10.0)
        high = sum(1 for m in multipliers if m >= 10.0)
        
        print(f"\n📈 Range Distribution:")
        print(f"  Low (< 2x):      {low:4d} ({low/len(multipliers)*100:5.1f}%)")
        print(f"  Medium (2-10x):  {medium:4d} ({medium/len(multipliers)*100:5.1f}%)")
        print(f"  High (>= 10x):   {high:4d} ({high/len(multipliers)*100:5.1f}%)")
        
        # Notable multipliers
        very_high = [m for m in multipliers if m >= 100]
        if very_high:
            print(f"\n🚀 Very High Multipliers (>= 100x):")
            for m in sorted(very_high, reverse=True)[:5]:
                print(f"  {m:.2f}x")
        
        print("="*80)


def integrate_manual_history_with_bot(bot):
    """
    Integrate manual history loading with the bot.
    
    Args:
        bot: AviatorBotML instance
        
    Returns:
        int: Number of rounds loaded
    """
    if not bot.history_tracker:
        print("⚠️  No history tracker available")
        return 0
    
    loader = ManualHistoryLoader(csv_file="aviator_rounds_history.csv")
    
    # Check if CSV exists and has data
    if os.path.exists(loader.csv_file):
        print(f"\n📁 Found existing history file: {loader.csv_file}")
        
        # Count existing rounds
        try:
            with open(loader.csv_file, 'r') as f:
                existing_count = sum(1 for _ in f) - 1  # Subtract header
            print(f"📊 Existing rounds in file: {existing_count}")
        except:
            existing_count = 0
    
    # Ask if user wants to add manual history
    print("\n" + "="*80)
    add_manual = input("📝 Add manual history for better predictions? (y/n, default: y): ").strip().lower()
    
    if add_manual == 'n':
        print("⏭️  Skipping manual history")
        return 0
    
    # Load manual history
    count = loader.load_history_for_tracker(bot.history_tracker)
    
    if count > 0:
        # Show statistics
        loader.show_statistics(bot.history_tracker.get_recent_multipliers(count))
        
        # Update ML model if needed
        if bot.ml_generator:
            print("\n🤖 ML models will use this history for predictions")
    
    return count

if __name__ == "__main__":
    # Test the loader
    print("="*80)
    print("🧪 MANUAL HISTORY LOADER - TEST MODE")
    print("="*80)