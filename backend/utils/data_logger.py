"""
Centralized Data Logger - Unified logging for all bot data
Ensures consistent format and avoids duplicate logging
"""

import os
import csv
from datetime import datetime
from collections import deque
import threading
from queue import Queue


class RoundLogger:
    """Simple logger for rounds with only 3 fields: timestamp, multiplier, source"""

    def __init__(self, csv_file="aviator_rounds_history.csv"):
        self.csv_file = csv_file
        self.last_logged_multiplier = None
        self.last_log_time = 0
        self.log_cooldown = 2.0

        # Async write queue
        self._write_queue = Queue()
        self._write_thread = None
        self._write_thread_running = False
        self._start_async_writer()

        # Create CSV if it doesn't exist
        if not os.path.exists(self.csv_file):
            with open(self.csv_file, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['timestamp', 'multiplier', 'source'])

    def _start_async_writer(self):
        """Start background thread for async CSV writing"""
        if self._write_thread is None or not self._write_thread.is_alive():
            self._write_thread_running = True
            self._write_thread = threading.Thread(target=self._async_write_worker, daemon=True)
            self._write_thread.start()

    def _async_write_worker(self):
        """Background worker that writes to CSV asynchronously"""
        while self._write_thread_running:
            try:
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
                    print(f"[RoundLogger] Error in async writer: {e}")

    def stop_async_writer(self):
        """Stop the async writer thread"""
        if self._write_thread_running:
            self._write_thread_running = False
            self._write_queue.put(None)
            if self._write_thread:
                self._write_thread.join(timeout=2.0)

    def log_round(self, multiplier, source='screen', custom_timestamp=None):
        """
        Log a round with timestamp, multiplier, and source

        Args:
            multiplier: Round multiplier value
            source: Source of the data ('screen', 'manual', 'clipboard')
            custom_timestamp: Optional custom timestamp (datetime object)

        Returns:
            tuple: (success: bool, timestamp_str: str)
        """
        try:
            timestamp = custom_timestamp if custom_timestamp else datetime.now()
            timestamp_str = timestamp.strftime("%Y-%m-%d %H:%M:%S")

            row_data = [timestamp_str, round(multiplier, 2), source]

            # Add to async write queue (NON-BLOCKING)
            self._write_queue.put(row_data)

            # Update tracking
            self.last_logged_multiplier = multiplier
            self.last_log_time = timestamp.timestamp()

            return True, timestamp_str

        except Exception as e:
            print(f"[RoundLogger] Error logging round: {e}")
            return False, None

    def log_batch(self, multipliers, source='manual', start_timestamp=None):
        """
        Log multiple rounds at once with backdated timestamps

        Args:
            multipliers: List of multiplier values
            source: Source of the data
            start_timestamp: Starting timestamp (datetime object) - will backdate from this

        Returns:
            int: Number of rounds logged
        """
        from datetime import timedelta
        import random

        if not multipliers:
            return 0

        count = 0
        base_time = start_timestamp if start_timestamp else datetime.now()

        # Calculate time span (10 seconds per round on average)
        total_seconds = len(multipliers) * 10
        oldest_time = base_time - timedelta(seconds=total_seconds)

        for i, mult in enumerate(multipliers):
            # Calculate realistic timestamp
            variation = random.uniform(-3, 3)
            round_time = oldest_time + timedelta(seconds=i * 10 + variation)

            success, _ = self.log_round(mult, source=source, custom_timestamp=round_time)
            if success:
                count += 1

        return count


class PerformanceLogger:
    """Logger for bot performance with unified timestamp"""

    def __init__(self, csv_file="bot_automl_performance.csv"):
        self.csv_file = csv_file

        # Async write queue
        self._write_queue = Queue()
        self._write_thread = None
        self._write_thread_running = False
        self._start_async_writer()

        # Create CSV if it doesn't exist
        if not os.path.exists(self.csv_file):
            self._initialize_csv()

    def _initialize_csv(self):
        """Initialize CSV with proper headers"""
        with open(self.csv_file, 'w', newline='') as f:
            writer = csv.writer(f)
            header = [
                'timestamp', 'round_id', 'actual_multiplier',
                'predicted_multiplier', 'predicted_range', 'actual_range',
                'ensemble_confidence', 'consensus_range', 'consensus_strength',
                'recommendation_should_bet', 'recommendation_target', 'recommendation_risk',
                'prediction_error', 'range_correct'
            ]
            # Add model predictions
            header.extend([f'model_{i}_pred' for i in range(1, 17)])
            writer.writerow(header)

    def _start_async_writer(self):
        """Start background thread for async CSV writing"""
        if self._write_thread is None or not self._write_thread.is_alive():
            self._write_thread_running = True
            self._write_thread = threading.Thread(target=self._async_write_worker, daemon=True)
            self._write_thread.start()

    def _async_write_worker(self):
        """Background worker that writes to CSV asynchronously"""
        while self._write_thread_running:
            try:
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
                    print(f"[PerformanceLogger] Error in async writer: {e}")

    def stop_async_writer(self):
        """Stop the async writer thread"""
        if self._write_thread_running:
            self._write_thread_running = False
            self._write_queue.put(None)
            if self._write_thread:
                self._write_thread.join(timeout=2.0)

    def log_performance(self, timestamp_str, round_id, actual_multiplier,
                       predicted_multiplier, predicted_range, actual_range,
                       ensemble_confidence, consensus_range, consensus_strength,
                       should_bet, target_multiplier, risk_level,
                       model_predictions=None):
        """
        Log bot performance with SAME timestamp as round

        Args:
            timestamp_str: Timestamp string matching the round (YYYY-MM-DD HH:MM:SS)
            round_id: Round ID
            actual_multiplier: Actual multiplier that occurred
            predicted_multiplier: Predicted multiplier
            predicted_range: Predicted range
            actual_range: Actual range
            ensemble_confidence: Ensemble confidence
            consensus_range: Consensus range
            consensus_strength: Consensus strength
            should_bet: Whether bot recommended betting
            target_multiplier: Target multiplier
            risk_level: Risk level
            model_predictions: List of 16 model predictions (optional)

        Returns:
            bool: Success
        """
        try:
            # Calculate metrics
            prediction_error = abs(predicted_multiplier - actual_multiplier)
            range_correct = 1 if actual_range == predicted_range else 0

            # Prepare model predictions (fill with empty if not provided)
            if model_predictions is None:
                model_predictions = [''] * 16
            else:
                # Ensure exactly 16 values
                model_predictions = list(model_predictions)[:16]
                while len(model_predictions) < 16:
                    model_predictions.append('')

            row_data = [
                timestamp_str,
                round_id,
                round(actual_multiplier, 2),
                round(predicted_multiplier, 2),
                predicted_range,
                actual_range,
                round(ensemble_confidence, 2),
                consensus_range,
                round(consensus_strength, 1),
                should_bet,
                round(target_multiplier, 2),
                risk_level,
                round(prediction_error, 2),
                range_correct
            ]

            # Add model predictions
            row_data.extend([f"{p:.2f}" if isinstance(p, (int, float)) else p for p in model_predictions])

            # Add to async write queue
            self._write_queue.put(row_data)

            return True

        except Exception as e:
            print(f"[PerformanceLogger] Error logging performance: {e}")
            return False


class RangePredictor:
    """Range-based prediction and accuracy tracker"""

    def __init__(self):
        self.ranges = [
            {'name': 'LOW', 'label': '1.0-1.5x', 'min': 1.0, 'max': 1.5},
            {'name': 'MEDIUM-LOW', 'label': '1.5-2.5x', 'min': 1.5, 'max': 2.5},
            {'name': 'MEDIUM', 'label': '2.5-3.5x', 'min': 2.5, 'max': 3.5},
            {'name': 'MEDIUM-HIGH', 'label': '3.5-5.0x', 'min': 3.5, 'max': 5.0},
            {'name': 'HIGH', 'label': '5.0+x', 'min': 5.0, 'max': 1000.0}
        ]

        # Track accuracy per range
        self.range_accuracy = {r['name']: {'correct': 0, 'total': 0} for r in self.ranges}

    def get_range_for_multiplier(self, multiplier):
        """Get range name for a multiplier value"""
        for r in self.ranges:
            if r['min'] <= multiplier < r['max']:
                return r['name']
        return 'HIGH'  # Default for very high values

    def get_range_label(self, range_name):
        """Get human-readable label for a range"""
        for r in self.ranges:
            if r['name'] == range_name:
                return r['label']
        return range_name

    def update_accuracy(self, predicted_range, actual_range):
        """Update accuracy tracking"""
        if predicted_range in self.range_accuracy:
            self.range_accuracy[predicted_range]['total'] += 1
            if predicted_range == actual_range:
                self.range_accuracy[predicted_range]['correct'] += 1

    def get_accuracy_stats(self):
        """Get accuracy statistics by range"""
        stats = {}
        for range_name, data in self.range_accuracy.items():
            if data['total'] > 0:
                accuracy = (data['correct'] / data['total']) * 100
                stats[range_name] = {
                    'accuracy': round(accuracy, 2),
                    'correct': data['correct'],
                    'total': data['total']
                }
            else:
                stats[range_name] = {'accuracy': 0, 'correct': 0, 'total': 0}
        return stats

    def print_accuracy_table(self):
        """Print accuracy table"""
        stats = self.get_accuracy_stats()

        print("\n" + "="*70)
        print("📊 RANGE PREDICTION ACCURACY")
        print("="*70)
        print(f"{'Range':<20} {'Label':<15} {'Correct':<10} {'Total':<10} {'Accuracy':<10}")
        print("-"*70)

        for r in self.ranges:
            name = r['name']
            label = r['label']
            s = stats.get(name, {'correct': 0, 'total': 0, 'accuracy': 0})
            print(f"{name:<20} {label:<15} {s['correct']:<10} {s['total']:<10} {s['accuracy']:>6.2f}%")

        # Overall accuracy
        total_correct = sum(s['correct'] for s in stats.values())
        total_predictions = sum(s['total'] for s in stats.values())
        overall_accuracy = (total_correct / total_predictions * 100) if total_predictions > 0 else 0

        print("-"*70)
        print(f"{'OVERALL':<20} {'All Ranges':<15} {total_correct:<10} {total_predictions:<10} {overall_accuracy:>6.2f}%")
        print("="*70 + "\n")


# Singleton instances
_round_logger = None
_performance_logger = None
_range_predictor = None


def get_round_logger():
    """Get singleton instance of RoundLogger"""
    global _round_logger
    if _round_logger is None:
        _round_logger = RoundLogger()
    return _round_logger


def get_performance_logger():
    """Get singleton instance of PerformanceLogger"""
    global _performance_logger
    if _performance_logger is None:
        _performance_logger = PerformanceLogger()
    return _performance_logger


def get_range_predictor():
    """Get singleton instance of RangePredictor"""
    global _range_predictor
    if _range_predictor is None:
        _range_predictor = RangePredictor()
    return _range_predictor


def cleanup_loggers():
    """Cleanup all logger threads"""
    global _round_logger, _performance_logger

    if _round_logger:
        _round_logger.stop_async_writer()

    if _performance_logger:
        _performance_logger.stop_async_writer()
