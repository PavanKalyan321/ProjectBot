"""
Prediction Validation and Tracking System
Tracks model performance and validates predictions against expected ranges
"""

import numpy as np
import pandas as pd
from collections import defaultdict, deque
from datetime import datetime
import json
import os


class PredictionValidator:
    """
    Validates and tracks predictions from all 30 models.
    Provides accuracy metrics, expected range validation, and model ranking.
    """

    def __init__(self, history_size=1000):
        """
        Initialize prediction validator.

        Args:
            history_size: Number of rounds to keep in history
        """
        self.history_size = history_size

        # Prediction history for each model
        # {model_id: deque([{prediction, actual, error, in_range, timestamp}, ...])}
        self.model_history = defaultdict(lambda: deque(maxlen=history_size))

        # Aggregate statistics for each model
        # {model_id: {mae, rmse, accuracy, in_range_pct, total_predictions, ...}}
        self.model_stats = defaultdict(dict)

        # Recent performance (last N rounds)
        self.recent_window = 50

        # Expected range configuration (tolerance %)
        self.range_tolerance = 0.15  # ±15% is considered "in range"

    def add_prediction(self, model_id, prediction, actual, timestamp=None):
        """
        Add a prediction and actual outcome for tracking.

        Args:
            model_id: Model identifier
            prediction: Predicted multiplier
            actual: Actual multiplier
            timestamp: Optional timestamp
        """
        if timestamp is None:
            timestamp = datetime.now()

        # Calculate metrics
        error = abs(prediction - actual)
        relative_error = error / actual if actual > 0 else 0

        # Check if in expected range
        lower_bound = actual * (1 - self.range_tolerance)
        upper_bound = actual * (1 + self.range_tolerance)
        in_range = lower_bound <= prediction <= upper_bound

        # Store in history
        self.model_history[model_id].append({
            'prediction': float(prediction),
            'actual': float(actual),
            'error': float(error),
            'relative_error': float(relative_error),
            'in_range': bool(in_range),
            'timestamp': timestamp.isoformat() if isinstance(timestamp, datetime) else timestamp
        })

        # Update stats
        self._update_model_stats(model_id)

    def _update_model_stats(self, model_id):
        """Recalculate statistics for a model."""
        history = list(self.model_history[model_id])

        if len(history) == 0:
            return

        # Extract data
        predictions = np.array([h['prediction'] for h in history])
        actuals = np.array([h['actual'] for h in history])
        errors = np.array([h['error'] for h in history])
        in_range_flags = np.array([h['in_range'] for h in history])

        # Calculate overall stats
        mae = float(np.mean(errors))
        rmse = float(np.sqrt(np.mean(errors ** 2)))
        mean_relative_error = float(np.mean([h['relative_error'] for h in history]))

        # In-range accuracy
        in_range_pct = float(np.mean(in_range_flags) * 100)

        # R-squared
        ss_res = np.sum((actuals - predictions) ** 2)
        ss_tot = np.sum((actuals - np.mean(actuals)) ** 2)
        r2 = float(1 - (ss_res / ss_tot)) if ss_tot > 0 else 0

        # Recent performance (last N rounds)
        recent_history = history[-self.recent_window:]
        if len(recent_history) > 0:
            recent_errors = np.array([h['error'] for h in recent_history])
            recent_in_range = np.array([h['in_range'] for h in recent_history])

            recent_mae = float(np.mean(recent_errors))
            recent_in_range_pct = float(np.mean(recent_in_range) * 100)
        else:
            recent_mae = mae
            recent_in_range_pct = in_range_pct

        # Trend analysis (is performance improving or degrading?)
        if len(history) >= 100:
            first_half = history[:len(history)//2]
            second_half = history[len(history)//2:]

            first_half_mae = np.mean([h['error'] for h in first_half])
            second_half_mae = np.mean([h['error'] for h in second_half])

            trend = 'IMPROVING' if second_half_mae < first_half_mae else 'DEGRADING'
            trend_delta = float(first_half_mae - second_half_mae)
        else:
            trend = 'STABLE'
            trend_delta = 0.0

        # Store stats
        self.model_stats[model_id] = {
            'total_predictions': len(history),
            'mae': mae,
            'rmse': rmse,
            'mean_relative_error': mean_relative_error,
            'r2': r2,
            'in_range_pct': in_range_pct,
            'recent_mae': recent_mae,
            'recent_in_range_pct': recent_in_range_pct,
            'trend': trend,
            'trend_delta': trend_delta,
            'last_updated': datetime.now().isoformat()
        }

    def get_model_stats(self, model_id):
        """
        Get statistics for a specific model.

        Args:
            model_id: Model identifier

        Returns:
            dict: Model statistics
        """
        return self.model_stats.get(model_id, {})

    def get_all_stats(self):
        """
        Get statistics for all models.

        Returns:
            dict: {model_id: stats}
        """
        return dict(self.model_stats)

    def get_ranked_models(self, metric='mae', ascending=True, top_n=None):
        """
        Get models ranked by performance.

        Args:
            metric: Metric to rank by ('mae', 'rmse', 'r2', 'in_range_pct')
            ascending: True for ascending order (best first for mae/rmse)
            top_n: Return only top N models (None for all)

        Returns:
            list: [(model_id, stats), ...] sorted by metric
        """
        if not self.model_stats:
            return []

        # Sort models
        models_with_stats = [(mid, stats) for mid, stats in self.model_stats.items() if stats]

        # For r2 and in_range_pct, higher is better (descending)
        if metric in ['r2', 'in_range_pct']:
            ascending = not ascending

        sorted_models = sorted(
            models_with_stats,
            key=lambda x: x[1].get(metric, float('inf') if ascending else float('-inf')),
            reverse=not ascending
        )

        if top_n:
            sorted_models = sorted_models[:top_n]

        return sorted_models

    def get_prediction_summary(self, model_ids=None):
        """
        Get summary of recent predictions with expected range indicators.

        Args:
            model_ids: List of model IDs to include (None for all)

        Returns:
            list: [{model_id, prediction, actual, in_range, accuracy, ...}, ...]
        """
        if model_ids is None:
            model_ids = list(self.model_history.keys())

        summary = []

        for model_id in model_ids:
            history = list(self.model_history[model_id])
            if not history:
                continue

            # Get last prediction
            last = history[-1]
            stats = self.model_stats.get(model_id, {})

            summary.append({
                'model_id': model_id,
                'prediction': last['prediction'],
                'actual': last['actual'],
                'error': last['error'],
                'in_range': last['in_range'],
                'in_range_pct': stats.get('in_range_pct', 0),
                'mae': stats.get('mae', 0),
                'recent_mae': stats.get('recent_mae', 0),
                'trend': stats.get('trend', 'STABLE')
            })

        return summary

    def calculate_ensemble_prediction(self, model_predictions, method='weighted_average'):
        """
        Calculate ensemble prediction from multiple models.

        Args:
            model_predictions: [{model_id, prediction, confidence}, ...]
            method: 'weighted_average', 'median', 'best_models', 'trimmed_mean'

        Returns:
            dict: {ensemble_prediction, confidence, method, contributing_models}
        """
        if not model_predictions:
            return {'ensemble_prediction': 2.0, 'confidence': 0.0, 'method': method, 'contributing_models': 0}

        if method == 'weighted_average':
            # Weight by inverse MAE (better models get higher weight)
            total_weight = 0
            weighted_sum = 0

            for pred in model_predictions:
                model_id = pred['model_id']
                prediction = pred['prediction']
                stats = self.model_stats.get(model_id, {})

                # Use inverse MAE as weight (lower error = higher weight)
                mae = stats.get('recent_mae', stats.get('mae', 1.0))
                weight = 1.0 / (mae + 0.1)  # Add small constant to avoid division by zero

                weighted_sum += prediction * weight
                total_weight += weight

            ensemble_pred = weighted_sum / total_weight if total_weight > 0 else np.mean([p['prediction'] for p in model_predictions])

            # Calculate confidence based on agreement
            predictions_array = np.array([p['prediction'] for p in model_predictions])
            std = np.std(predictions_array)
            confidence = max(50.0, min(95.0, 90.0 - (std * 10)))  # Lower std = higher confidence

        elif method == 'median':
            # Robust to outliers
            predictions_array = np.array([p['prediction'] for p in model_predictions])
            ensemble_pred = float(np.median(predictions_array))
            std = np.std(predictions_array)
            confidence = max(50.0, min(95.0, 85.0 - (std * 10)))

        elif method == 'best_models':
            # Use only top 10 models by recent MAE
            top_models = self.get_ranked_models(metric='recent_mae', ascending=True, top_n=10)
            top_model_ids = set([m[0] for m in top_models])

            filtered_preds = [p for p in model_predictions if p['model_id'] in top_model_ids]

            if filtered_preds:
                ensemble_pred = float(np.mean([p['prediction'] for p in filtered_preds]))
                std = np.std([p['prediction'] for p in filtered_preds])
                confidence = max(60.0, min(95.0, 92.0 - (std * 10)))
            else:
                # Fallback to all models
                ensemble_pred = float(np.mean([p['prediction'] for p in model_predictions]))
                confidence = 50.0

        elif method == 'trimmed_mean':
            # Remove top and bottom 10% to reduce outlier influence
            predictions_array = np.array([p['prediction'] for p in model_predictions])
            sorted_preds = np.sort(predictions_array)
            trim_count = max(1, len(sorted_preds) // 10)

            trimmed = sorted_preds[trim_count:-trim_count] if len(sorted_preds) > 2*trim_count else sorted_preds
            ensemble_pred = float(np.mean(trimmed))
            std = np.std(trimmed)
            confidence = max(55.0, min(95.0, 88.0 - (std * 10)))

        else:
            # Default to simple average
            ensemble_pred = float(np.mean([p['prediction'] for p in model_predictions]))
            confidence = 50.0

        return {
            'ensemble_prediction': round(ensemble_pred, 2),
            'confidence': round(confidence, 1),
            'method': method,
            'contributing_models': len(model_predictions),
            'prediction_std': round(float(np.std([p['prediction'] for p in model_predictions])), 2)
        }

    def get_expected_range(self, prediction, tolerance=None):
        """
        Get expected range for a prediction.

        Args:
            prediction: Predicted multiplier
            tolerance: Range tolerance (default: use self.range_tolerance)

        Returns:
            dict: {lower, upper, tolerance_pct}
        """
        if tolerance is None:
            tolerance = self.range_tolerance

        lower = round(prediction * (1 - tolerance), 2)
        upper = round(prediction * (1 + tolerance), 2)

        return {
            'lower': lower,
            'upper': upper,
            'tolerance_pct': round(tolerance * 100, 1)
        }

    def check_prediction_accuracy(self, prediction, actual, tolerance=None):
        """
        Check if prediction was within expected range.

        Args:
            prediction: Predicted multiplier
            actual: Actual multiplier
            tolerance: Range tolerance

        Returns:
            dict: {in_range, accuracy_score, distance}
        """
        expected_range = self.get_expected_range(prediction, tolerance)

        in_range = expected_range['lower'] <= actual <= expected_range['upper']

        # Calculate accuracy score (0-100)
        error = abs(prediction - actual)
        relative_error = error / actual if actual > 0 else 0
        accuracy_score = max(0, min(100, 100 * (1 - relative_error)))

        # Distance from range (0 if in range)
        if in_range:
            distance = 0
        elif actual < expected_range['lower']:
            distance = expected_range['lower'] - actual
        else:
            distance = actual - expected_range['upper']

        return {
            'in_range': in_range,
            'accuracy_score': round(accuracy_score, 1),
            'distance': round(distance, 2),
            'expected_lower': expected_range['lower'],
            'expected_upper': expected_range['upper']
        }

    def export_stats(self, filepath='model_performance_stats.json'):
        """Export model statistics to JSON file."""
        stats_export = {
            'export_timestamp': datetime.now().isoformat(),
            'total_models': len(self.model_stats),
            'model_stats': dict(self.model_stats),
            'top_10_by_mae': [
                {'model_id': mid, 'mae': stats['mae'], 'in_range_pct': stats['in_range_pct']}
                for mid, stats in self.get_ranked_models(metric='mae', top_n=10)
            ],
            'top_10_by_in_range': [
                {'model_id': mid, 'in_range_pct': stats['in_range_pct'], 'mae': stats['mae']}
                for mid, stats in self.get_ranked_models(metric='in_range_pct', top_n=10)
            ]
        }

        with open(filepath, 'w') as f:
            json.dump(stats_export, f, indent=2)

        print(f"[OK] Model statistics exported to {filepath}")

    def get_model_comparison_grid(self):
        """
        Get comparison data for all models in grid format.

        Returns:
            list: [{model_id, mae, in_range_pct, r2, trend, rank}, ...]
        """
        ranked = self.get_ranked_models(metric='mae', ascending=True)

        grid = []
        for rank, (model_id, stats) in enumerate(ranked, 1):
            grid.append({
                'rank': rank,
                'model_id': model_id,
                'mae': round(stats.get('mae', 0), 3),
                'recent_mae': round(stats.get('recent_mae', 0), 3),
                'in_range_pct': round(stats.get('in_range_pct', 0), 1),
                'recent_in_range_pct': round(stats.get('recent_in_range_pct', 0), 1),
                'r2': round(stats.get('r2', 0), 4),
                'trend': stats.get('trend', 'STABLE'),
                'total_predictions': stats.get('total_predictions', 0),
                'badge': '🥇' if rank == 1 else ('🥈' if rank == 2 else ('🥉' if rank == 3 else ''))
            })

        return grid
