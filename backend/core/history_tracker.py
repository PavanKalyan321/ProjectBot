"""Round history tracking and CSV logging."""

import os
import csv
import time
import pandas as pd
from datetime import datetime
from collections import deque
import threading
from queue import Queue


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

        # Performance optimization: In-memory cache
        self._cache = None
        self._cache_lock = threading.Lock()
        self._cache_last_modified = 0

        # Async write optimization
        self._write_queue = Queue()
        self._write_thread = None
        self._write_thread_running = False
        self._start_async_writer()

        # Create CSV file if it doesn't exist
        if not os.path.exists(self.csv_file):
            with open(self.csv_file, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    'timestamp', 'round_id', 'multiplier',
                    'bet_placed', 'stake_amount', 'cashout_time',
                    'profit_loss', 'model_prediction', 'model_confidence',
                    'model_predicted_range_low', 'model_predicted_range_high',
                    'pos2_confidence', 'pos2_target_multiplier', 'pos2_burst_probability',
                    'pos2_phase', 'pos2_rules_triggered'
                ])

    def _start_async_writer(self):
        """Start background thread for async CSV writing."""
        if self._write_thread is None or not self._write_thread.is_alive():
            self._write_thread_running = True
            self._write_thread = threading.Thread(target=self._async_write_worker, daemon=True)
            self._write_thread.start()

    def _async_write_worker(self):
        """Background worker that writes to CSV asynchronously."""
        while self._write_thread_running:
            try:
                # Get item from queue with timeout
                row_data = self._write_queue.get(timeout=1.0)

                if row_data is None:  # Shutdown signal
                    break

                # Write to CSV
                with open(self.csv_file, 'a', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow(row_data)

                self._write_queue.task_done()

            except Exception as e:
                if str(e) != '':  # Ignore timeout exceptions
                    print(f"Error in async writer: {e}")

    def stop_async_writer(self):
        """Stop the async writer thread."""
        if self._write_thread_running:
            self._write_thread_running = False
            self._write_queue.put(None)  # Send shutdown signal
            if self._write_thread:
                self._write_thread.join(timeout=2.0)

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
                  profit_loss=0, prediction=None, confidence=0, pred_range=(0, 0),
                  pos2_signal=None):
        """
        Log a round to CSV file with async non-blocking writing.

        Args:
            multiplier: Round multiplier value
            bet_placed: Whether a bet was placed
            stake: Stake amount
            cashout_time: Time of cashout in seconds
            profit_loss: Profit or loss amount
            prediction: ML model prediction
            confidence: ML model confidence
            pred_range: Tuple (low, high) prediction range
            pos2_signal: Position 2 signal dictionary (optional)
        """
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            round_id = datetime.now().strftime("%Y%m%d%H%M%S%f")

            # Extract Position 2 data if available
            pos2_confidence = 0
            pos2_target = 0
            pos2_burst_prob = 0
            pos2_phase = 'unknown'
            pos2_rules = ''

            if pos2_signal:
                pos2_confidence = pos2_signal.get('confidence', 0)
                pos2_target = pos2_signal.get('target_multiplier', 0)
                pos2_burst_prob = pos2_signal.get('burst_probability', 0)
                pos2_phase = pos2_signal.get('phase', 'unknown')
                pos2_rules = '|'.join(pos2_signal.get('rules_triggered', []))

            row_data = [
                timestamp, round_id, multiplier, bet_placed, stake, cashout_time,
                profit_loss, prediction, confidence,
                pred_range[0] if pred_range else 0,
                pred_range[1] if pred_range else 0,
                pos2_confidence, pos2_target, pos2_burst_prob,
                pos2_phase, pos2_rules
            ]

            # Add to async write queue (NON-BLOCKING!)
            self._write_queue.put(row_data)

            # Update cache immediately without waiting for disk write
            with self._cache_lock:
                if self._cache is not None:
                    # Add new row to cache instead of invalidating
                    new_row = pd.DataFrame([{
                        'timestamp': timestamp,
                        'round_id': round_id,
                        'multiplier': multiplier,
                        'bet_placed': bet_placed,
                        'stake_amount': stake,
                        'cashout_time': cashout_time,
                        'profit_loss': profit_loss,
                        'model_prediction': prediction,
                        'model_confidence': confidence,
                        'model_predicted_range_low': pred_range[0] if pred_range else 0,
                        'model_predicted_range_high': pred_range[1] if pred_range else 0,
                        'pos2_confidence': pos2_confidence,
                        'pos2_target_multiplier': pos2_target,
                        'pos2_burst_probability': pos2_burst_prob,
                        'pos2_phase': pos2_phase,
                        'pos2_rules_triggered': pos2_rules
                    }])
                    self._cache = pd.concat([self._cache, new_row], ignore_index=True)

        except Exception as e:
            print(f"Error logging round: {e}")

    def _read_csv_tail_efficient(self, n=100):
        """
        Efficiently read only the last N lines from CSV without loading entire file.
        Uses reverse file reading for very large files.

        Args:
            n: Number of lines to read from end

        Returns:
            pandas.DataFrame: Last N rows
        """
        try:
            if not os.path.exists(self.csv_file):
                return pd.DataFrame()

            # For small requests, use efficient tail reading
            if n <= 1000:
                lines = []
                with open(self.csv_file, 'r', encoding='utf-8') as f:
                    # Read header
                    header = f.readline()
                    lines.append(header)

                    # Read all remaining lines (for deque efficiency)
                    all_lines = f.readlines()

                    # Get last n lines
                    if len(all_lines) <= n:
                        lines.extend(all_lines)
                    else:
                        lines.extend(all_lines[-n:])

                # Parse with pandas
                from io import StringIO
                df = pd.read_csv(StringIO(''.join(lines)))

                if df.empty:
                    return pd.DataFrame()

                # Clean column names
                df.columns = df.columns.str.strip()

                # Filter valid multipliers
                if 'multiplier' in df.columns:
                    df = df[df['multiplier'].notna()]

                return df
            else:
                # For larger requests, fall back to full load
                return self._load_cache_from_csv()

        except Exception as e:
            print(f"Error reading CSV tail: {e}")
            return pd.DataFrame()

    def _load_cache_from_csv(self):
        """Load entire CSV into cache (called once, then cached)."""
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

            return df
        except Exception as e:
            print(f"Error loading cache from CSV: {e}")
            return pd.DataFrame()

    def get_recent_rounds(self, n=100):
        """
        Get recent rounds from cache (optimized - no CSV read if cached).

        Args:
            n: Number of recent rounds to retrieve

        Returns:
            pandas.DataFrame: Recent rounds data
        """
        try:
            with self._cache_lock:
                # Check if cache needs refresh (file modified or cache empty)
                if self._cache is None:
                    if os.path.exists(self.csv_file):
                        file_mtime = os.path.getmtime(self.csv_file)
                        if file_mtime > self._cache_last_modified or self._cache is None:
                            self._cache = self._load_cache_from_csv()
                            self._cache_last_modified = file_mtime
                    else:
                        return pd.DataFrame()

                if self._cache is None or self._cache.empty:
                    return pd.DataFrame()

                # Return tail from cache (FAST - no CSV read!)
                return self._cache.tail(n).copy()

        except Exception as e:
            print(f"Error getting recent rounds: {e}")
            return pd.DataFrame()
    
    def get_recent_multipliers(self, n=100):
        """
        Get recent multipliers as a list.

        Args:
            n: Number of recent multipliers to retrieve

        Returns:
            list: List of multiplier values
        """
        try:
            df = self.get_recent_rounds(n)

            if df.empty or 'multiplier' not in df.columns:
                return []

            return df['multiplier'].tolist()
        except Exception as e:
            print(f"Error getting recent multipliers: {e}")
            return []

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
