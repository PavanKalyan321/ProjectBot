"""Round history tracking and CSV logging."""

import os
import csv
import time
import pandas as pd
from datetime import datetime
from collections import deque


class RoundHistoryTracker:
    """Track and log round history to CSV."""

    def __init__(self, history_region=None):
        """
        Initialize history tracker.
        
        Args:
            history_region: Tuple (x, y, width, height) for history region (optional)
        """
        self.history_region = history_region
        self.csv_file = "aviator_rounds_history.csv"
        self.last_logged_multiplier = None
        self.last_log_time = 0
        self.log_cooldown = 2.0
        self.local_history_buffer = deque(maxlen=10)

        # Create CSV file if it doesn't exist
        if not os.path.exists(self.csv_file):
            with open(self.csv_file, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    'timestamp', 'round_id', 'multiplier',
                    'bet_placed', 'stake_amount', 'cashout_time',
                    'profit_loss', 'model_prediction', 'model_confidence',
                    'model_predicted_range_low', 'model_predicted_range_high'
                ])

    def auto_log_from_clipboard(self, detector, force=False):
        """
        Automatically log round from clipboard reading.
        
        Args:
            detector: GameStateDetector instance
            force: Force logging even if cooldown not expired
        
        Returns:
            Tuple (bool, float or None): (success, multiplier)
        """
        try:
            current_time = time.time()
            
            # Check cooldown
            if not force and (current_time - self.last_log_time) < self.log_cooldown:
                return False, None

            # Read multiplier
            multiplier = detector.read_multiplier_from_clipboard()
            if multiplier is None:
                return False, None

            # Check if already logged
            if not force and multiplier == self.last_logged_multiplier:
                return False, multiplier

            # Log the round
            self.log_round(multiplier=multiplier, bet_placed=False, stake=0,
                          cashout_time=0, profit_loss=0)

            # Add to local buffer
            self.local_history_buffer.append({
                'multiplier': multiplier,
                'timestamp': datetime.now().isoformat(),
                'round_id': datetime.now().strftime("%Y%m%d%H%M%S%f")
            })

            # Update tracking
            self.last_logged_multiplier = multiplier
            self.last_log_time = current_time
            
            return True, multiplier

        except Exception as e:
            print(f"Error auto-logging from clipboard: {e}")
            return False, None

    def log_round(self, multiplier, bet_placed=False, stake=0, cashout_time=0,
                  profit_loss=0, prediction=None, confidence=0, pred_range=(0, 0)):
        """
        Log a round to CSV file.
        
        Args:
            multiplier: Round multiplier value
            bet_placed: Whether a bet was placed
            stake: Stake amount
            cashout_time: Time of cashout in seconds
            profit_loss: Profit or loss amount
            prediction: ML model prediction
            confidence: ML model confidence
            pred_range: Tuple (low, high) prediction range
        """
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            round_id = datetime.now().strftime("%Y%m%d%H%M%S%f")
            
            with open(self.csv_file, 'a', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    timestamp, round_id, multiplier, bet_placed, stake, cashout_time,
                    profit_loss, prediction, confidence,
                    pred_range[0] if pred_range else 0, 
                    pred_range[1] if pred_range else 0
                ])
        except Exception as e:
            print(f"Error logging round: {e}")

    def get_recent_rounds(self, n=100):
        """
        Get recent rounds from CSV.
        
        Args:
            n: Number of recent rounds to retrieve
        
        Returns:
            pandas.DataFrame: Recent rounds data
        """
        try:
            if not os.path.exists(self.csv_file):
                return pd.DataFrame()
            
            df = pd.read_csv(self.csv_file)
            
            if df.empty:
                return pd.DataFrame()
            
            # Clean column names
            df.columns = df.columns.str.strip()
            
            # Filter valid multipliers
            if 'multiplier' in df.columns:
                df = df[df['multiplier'].notna()]
            
            return df.tail(n)
        except Exception as e:
            print(f"Error getting recent rounds: {e}")
            return pd.DataFrame()
    
    def get_statistics(self):
        """
        Get statistics from history.
        
        Returns:
            dict: Statistics dictionary
        """
        try:
            df = self.get_recent_rounds(1000)
            
            if df.empty:
                return {}
            
            stats = {
                'total_rounds': len(df),
                'avg_multiplier': df['multiplier'].mean() if 'multiplier' in df.columns else 0,
                'max_multiplier': df['multiplier'].max() if 'multiplier' in df.columns else 0,
                'min_multiplier': df['multiplier'].min() if 'multiplier' in df.columns else 0,
            }
            
            if 'bet_placed' in df.columns:
                bets_df = df[df['bet_placed'] == True]
                stats['total_bets'] = len(bets_df)
                
                if 'profit_loss' in df.columns and len(bets_df) > 0:
                    stats['total_profit'] = bets_df['profit_loss'].sum()
                    stats['win_rate'] = len(bets_df[bets_df['profit_loss'] > 0]) / len(bets_df) * 100
            
            return stats
        except Exception as e:
            print(f"Error getting statistics: {e}")
            return {}
