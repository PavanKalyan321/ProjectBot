"""
Advanced Prediction Dashboard for 30-Model Ensemble
Real-time monitoring with flow prediction and model comparison
"""

import os
import sys
import pandas as pd
import numpy as np
from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO, emit
from datetime import datetime, timedelta
import json
from collections import deque, defaultdict
import threading
import time

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core.advanced_ml_ensemble import AdvancedMLEnsemble
from core.flow_predictor import FlowPredictor
from core.prediction_validator import PredictionValidator


class AdvancedPredictionDashboard:
    """
    Advanced dashboard for 30-model ensemble with flow prediction and comprehensive analytics.
    """

    def __init__(self, port=5002):
        self.port = port
        self.app = Flask(__name__, template_folder='templates')
        self.socketio = SocketIO(self.app, cors_allowed_origins="*", async_mode='threading')

        # Data paths
        self.rounds_csv = "backend/aviator_rounds_history.csv"
        self.predictions_csv = "backend/advanced_predictions_history.csv"

        # ML Components
        self.ensemble = AdvancedMLEnsemble()
        self.flow_predictor = FlowPredictor()
        self.validator = PredictionValidator()

        # Load models
        self._load_models()

        # Real-time data
        self.current_round = {}
        self.recent_rounds = deque(maxlen=50)
        self.live_stats = {}

        # Cache
        self._cache = {}
        self._cache_time = None
        self._cache_duration = 5  # Cache for 5 seconds

        self._setup_routes()
        self._setup_socketio()

    def _load_models(self):
        """Load all trained models."""
        print("[INFO] Loading models...")

        try:
            if self.ensemble.load_all_models():
                print("[OK] Ensemble models loaded successfully")
            else:
                print("[WARNING] Ensemble models not found - train first")
        except Exception as e:
            print(f"[WARNING] Failed to load ensemble: {e}")

        try:
            if self.flow_predictor.load_models():
                print("[OK] Flow predictor loaded successfully")
            else:
                print("[WARNING] Flow predictor not found - train first")
        except Exception as e:
            print(f"[WARNING] Failed to load flow predictor: {e}")

        # Load historical predictions for validator
        self._load_prediction_history()

    def _load_prediction_history(self):
        """Load historical predictions into validator."""
        if not os.path.exists(self.predictions_csv):
            print("[INFO] No prediction history found")
            return

        try:
            df = pd.read_csv(self.predictions_csv)
            print(f"[INFO] Loading {len(df)} historical predictions...")

            for _, row in df.tail(1000).iterrows():  # Load last 1000
                # Parse model predictions from row
                for col in df.columns:
                    if col.startswith('model_') and '_pred' in col:
                        model_id = col.replace('_pred', '')
                        prediction = row[col]
                        actual = row.get('actual_multiplier', 0)

                        if pd.notna(prediction) and pd.notna(actual) and actual > 0:
                            self.validator.add_prediction(
                                model_id,
                                prediction,
                                actual,
                                row.get('timestamp')
                            )

            print(f"[OK] Loaded prediction history for {len(self.validator.model_stats)} models")
        except Exception as e:
            print(f"[WARNING] Failed to load prediction history: {e}")

    def _setup_routes(self):
        """Setup Flask routes."""

        @self.app.route('/')
        def index():
            return render_template('predictions_dashboard.html')

        @self.app.route('/api/status')
        def get_status():
            """Get system status."""
            return jsonify({
                'ensemble_loaded': self.ensemble.is_trained,
                'flow_predictor_loaded': self.flow_predictor.is_trained,
                'total_models': len(self.ensemble.models),
                'validator_models': len(self.validator.model_stats),
                'last_train_date': self.ensemble.last_train_date.isoformat() if self.ensemble.last_train_date else None
            })

        @self.app.route('/api/predictions/current')
        def get_current_predictions():
            """Get current round predictions from all 30 models."""
            return jsonify(self._get_current_predictions())

        @self.app.route('/api/predictions/ensemble')
        def get_ensemble_prediction():
            """Get ensemble prediction with multiple methods."""
            return jsonify(self._get_ensemble_prediction())

        @self.app.route('/api/flow/current')
        def get_current_flow():
            """Get current flow prediction."""
            return jsonify(self._get_flow_prediction())

        @self.app.route('/api/flow/forecast')
        def get_flow_forecast():
            """Get flow forecast for upcoming rounds."""
            return jsonify(self._get_flow_forecast())

        @self.app.route('/api/models/ranking')
        def get_model_ranking():
            """Get all models ranked by performance."""
            metric = request.args.get('metric', 'mae')
            top_n = request.args.get('top_n', type=int)
            return jsonify(self._get_model_ranking(metric, top_n))

        @self.app.route('/api/models/comparison')
        def get_model_comparison():
            """Get detailed comparison grid for all 30 models."""
            return jsonify(self._get_model_comparison())

        @self.app.route('/api/models/stats/<model_id>')
        def get_model_stats(model_id):
            """Get detailed stats for specific model."""
            return jsonify(self._get_model_detailed_stats(model_id))

        @self.app.route('/api/models/history/<model_id>')
        def get_model_history(model_id):
            """Get prediction history for specific model."""
            limit = request.args.get('limit', 50, type=int)
            return jsonify(self._get_model_history(model_id, limit))

        @self.app.route('/api/validation/summary')
        def get_validation_summary():
            """Get prediction validation summary."""
            return jsonify(self._get_validation_summary())

        @self.app.route('/api/validation/expected_range')
        def get_expected_range():
            """Get expected range for ensemble prediction."""
            return jsonify(self._get_expected_range_info())

        @self.app.route('/api/analytics/performance')
        def get_performance_analytics():
            """Get performance analytics across all models."""
            return jsonify(self._get_performance_analytics())

        @self.app.route('/api/analytics/trends')
        def get_trend_analytics():
            """Get trend analysis."""
            return jsonify(self._get_trend_analytics())

        @self.app.route('/api/history/recent')
        def get_recent_history():
            """Get recent rounds with predictions."""
            limit = request.args.get('limit', 20, type=int)
            return jsonify(self._get_recent_history(limit))

        @self.app.route('/api/export/stats')
        def export_stats():
            """Export model statistics."""
            filepath = 'model_performance_export.json'
            self.validator.export_stats(filepath)
            return jsonify({'success': True, 'filepath': filepath})

    def _setup_socketio(self):
        """Setup SocketIO for real-time updates."""

        @self.socketio.on('connect')
        def handle_connect():
            print(f"Client connected")
            emit('initial_data', self._get_dashboard_snapshot())

        @self.socketio.on('disconnect')
        def handle_disconnect():
            print(f"Client disconnected")

        @self.socketio.on('request_update')
        def handle_update_request():
            emit('live_update', self._get_dashboard_snapshot())

    def _get_recent_multipliers(self, limit=50):
        """Load recent multipliers from CSV."""
        if not os.path.exists(self.rounds_csv):
            return []

        try:
            df = pd.read_csv(self.rounds_csv)
            df = df.dropna(subset=['multiplier'])
            df = df[df['multiplier'] > 0]
            multipliers = df['multiplier'].tail(limit).tolist()
            return multipliers
        except Exception as e:
            print(f"Error loading multipliers: {e}")
            return []

    def _get_current_predictions(self):
        """Get predictions from all 30 models."""
        recent_multipliers = self._get_recent_multipliers()

        if not recent_multipliers or not self.ensemble.is_trained:
            return {'predictions': [], 'status': 'not_ready'}

        predictions = self.ensemble.predict_all(recent_multipliers)

        # Enhance with validation data
        for pred in predictions:
            model_id = pred['model_id']
            stats = self.validator.get_model_stats(model_id)
            pred['in_range_pct'] = stats.get('in_range_pct', 0)
            pred['trend'] = stats.get('trend', 'STABLE')
            pred['recent_mae'] = stats.get('recent_mae', stats.get('mae', 0))

        return {
            'predictions': predictions,
            'total_models': len(predictions),
            'status': 'ready',
            'timestamp': datetime.now().isoformat()
        }

    def _get_ensemble_prediction(self):
        """Get ensemble predictions using multiple methods."""
        recent_multipliers = self._get_recent_multipliers()

        if not recent_multipliers or not self.ensemble.is_trained:
            return {'status': 'not_ready'}

        model_predictions = self.ensemble.predict_all(recent_multipliers)

        # Calculate ensemble using different methods
        methods = ['weighted_average', 'median', 'best_models', 'trimmed_mean']
        ensemble_results = {}

        for method in methods:
            result = self.validator.calculate_ensemble_prediction(model_predictions, method)
            ensemble_results[method] = result

        # Get expected ranges
        primary_method = 'weighted_average'
        primary_prediction = ensemble_results[primary_method]['ensemble_prediction']
        expected_range = self.validator.get_expected_range(primary_prediction)

        return {
            'ensemble_methods': ensemble_results,
            'recommended_method': primary_method,
            'recommended_prediction': primary_prediction,
            'expected_range': expected_range,
            'model_agreement': self._calculate_model_agreement(model_predictions),
            'timestamp': datetime.now().isoformat()
        }

    def _calculate_model_agreement(self, predictions):
        """Calculate how much models agree."""
        if len(predictions) < 2:
            return {'score': 0, 'level': 'NONE'}

        pred_values = [p['prediction'] for p in predictions]
        std = np.std(pred_values)
        mean = np.mean(pred_values)
        cv = std / mean if mean > 0 else 0

        # Agreement score (0-100, higher = more agreement)
        agreement_score = max(0, min(100, 100 * (1 - cv)))

        if agreement_score > 80:
            level = 'VERY_HIGH'
        elif agreement_score > 60:
            level = 'HIGH'
        elif agreement_score > 40:
            level = 'MEDIUM'
        else:
            level = 'LOW'

        return {
            'score': round(agreement_score, 1),
            'level': level,
            'std': round(std, 2),
            'cv': round(cv, 2)
        }

    def _get_flow_prediction(self):
        """Get current flow prediction."""
        recent_multipliers = self._get_recent_multipliers()

        if not recent_multipliers or not self.flow_predictor.is_trained:
            return {'status': 'not_ready'}

        flow_pred = self.flow_predictor.predict_flow(recent_multipliers)
        flow_pred['status'] = 'ready'
        flow_pred['timestamp'] = datetime.now().isoformat()

        return flow_pred

    def _get_flow_forecast(self):
        """Get flow forecast for upcoming rounds."""
        # For now, return current flow as forecast
        # In a real implementation, this could predict next N rounds
        current_flow = self._get_flow_prediction()

        return {
            'current_flow': current_flow,
            'forecast_horizon': 10,
            'forecast_rounds': [
                {
                    'round_offset': i,
                    'expected_flow': current_flow.get('flow_type', 'UNKNOWN'),
                    'confidence': max(0, current_flow.get('confidence', 0) - (i * 5))  # Decreasing confidence
                }
                for i in range(1, 11)
            ]
        }

    def _get_model_ranking(self, metric='mae', top_n=None):
        """Get models ranked by performance."""
        ranked = self.validator.get_ranked_models(metric, ascending=(metric in ['mae', 'rmse']), top_n=top_n)

        return {
            'ranked_models': [
                {
                    'rank': i,
                    'model_id': model_id,
                    'stats': stats
                }
                for i, (model_id, stats) in enumerate(ranked, 1)
            ],
            'metric': metric,
            'total_models': len(ranked)
        }

    def _get_model_comparison(self):
        """Get comparison grid for all models."""
        grid = self.validator.get_model_comparison_grid()

        return {
            'comparison_grid': grid,
            'total_models': len(grid),
            'metrics_included': ['mae', 'recent_mae', 'in_range_pct', 'r2', 'trend']
        }

    def _get_model_detailed_stats(self, model_id):
        """Get detailed statistics for a model."""
        stats = self.validator.get_model_stats(model_id)

        if not stats:
            return {'error': 'Model not found'}

        return {
            'model_id': model_id,
            'stats': stats,
            'expected_range_tolerance': self.validator.range_tolerance * 100
        }

    def _get_model_history(self, model_id, limit=50):
        """Get prediction history for a model."""
        history = list(self.validator.model_history.get(model_id, []))
        history = history[-limit:] if len(history) > limit else history

        return {
            'model_id': model_id,
            'history': history,
            'count': len(history)
        }

    def _get_validation_summary(self):
        """Get validation summary across all models."""
        all_stats = self.validator.get_all_stats()

        if not all_stats:
            return {'status': 'no_data'}

        # Aggregate metrics
        all_maes = [s['mae'] for s in all_stats.values() if 'mae' in s]
        all_in_range = [s['in_range_pct'] for s in all_stats.values() if 'in_range_pct' in s]

        return {
            'total_models': len(all_stats),
            'avg_mae': round(np.mean(all_maes), 3) if all_maes else 0,
            'median_mae': round(np.median(all_maes), 3) if all_maes else 0,
            'best_mae': round(min(all_maes), 3) if all_maes else 0,
            'worst_mae': round(max(all_maes), 3) if all_maes else 0,
            'avg_in_range_pct': round(np.mean(all_in_range), 1) if all_in_range else 0,
            'best_in_range_pct': round(max(all_in_range), 1) if all_in_range else 0,
            'top_3_models': self.validator.get_ranked_models(metric='mae', top_n=3)
        }

    def _get_expected_range_info(self):
        """Get expected range information for current ensemble prediction."""
        ensemble_data = self._get_ensemble_prediction()

        if ensemble_data.get('status') == 'not_ready':
            return {'status': 'not_ready'}

        prediction = ensemble_data['recommended_prediction']
        expected_range = ensemble_data['expected_range']

        return {
            'prediction': prediction,
            'expected_range': expected_range,
            'tolerance_pct': expected_range['tolerance_pct'],
            'interpretation': f"Actual multiplier is expected to fall between {expected_range['lower']}x and {expected_range['upper']}x"
        }

    def _get_performance_analytics(self):
        """Get performance analytics."""
        all_stats = self.validator.get_all_stats()

        if not all_stats:
            return {'status': 'no_data'}

        # Calculate distribution of performance
        maes = [s['mae'] for s in all_stats.values() if 'mae' in s]
        in_range_pcts = [s['in_range_pct'] for s in all_stats.values() if 'in_range_pct' in s]

        return {
            'mae_distribution': {
                'mean': round(np.mean(maes), 3),
                'median': round(np.median(maes), 3),
                'std': round(np.std(maes), 3),
                'min': round(min(maes), 3),
                'max': round(max(maes), 3),
                'percentile_25': round(np.percentile(maes, 25), 3),
                'percentile_75': round(np.percentile(maes, 75), 3)
            },
            'in_range_distribution': {
                'mean': round(np.mean(in_range_pcts), 1),
                'median': round(np.median(in_range_pcts), 1),
                'std': round(np.std(in_range_pcts), 1),
                'min': round(min(in_range_pcts), 1),
                'max': round(max(in_range_pcts), 1)
            },
            'trend_summary': {
                'improving': sum(1 for s in all_stats.values() if s.get('trend') == 'IMPROVING'),
                'stable': sum(1 for s in all_stats.values() if s.get('trend') == 'STABLE'),
                'degrading': sum(1 for s in all_stats.values() if s.get('trend') == 'DEGRADING')
            }
        }

    def _get_trend_analytics(self):
        """Get trend analysis."""
        recent_multipliers = self._get_recent_multipliers(100)

        if len(recent_multipliers) < 20:
            return {'status': 'insufficient_data'}

        # Analyze recent trends
        recent_20 = recent_multipliers[-20:]
        recent_50 = recent_multipliers[-50:] if len(recent_multipliers) >= 50 else recent_multipliers

        return {
            'last_20_rounds': {
                'mean': round(np.mean(recent_20), 2),
                'std': round(np.std(recent_20), 2),
                'min': round(min(recent_20), 2),
                'max': round(max(recent_20), 2),
                'volatility_score': round(np.std(recent_20) / np.mean(recent_20) * 100, 1) if np.mean(recent_20) > 0 else 0
            },
            'last_50_rounds': {
                'mean': round(np.mean(recent_50), 2),
                'std': round(np.std(recent_50), 2),
                'trend': 'INCREASING' if np.mean(recent_20) > np.mean(recent_50) else 'DECREASING'
            },
            'extreme_events': {
                'high_count_10x': sum(1 for x in recent_20 if x >= 10.0),
                'low_count_1.2x': sum(1 for x in recent_20 if x < 1.2),
                'mid_range_count': sum(1 for x in recent_20 if 1.5 <= x < 3.0)
            }
        }

    def _get_recent_history(self, limit=20):
        """Get recent rounds with all predictions."""
        # This would load from predictions_csv
        # For now, return placeholder
        return {
            'rounds': [],
            'limit': limit,
            'note': 'Historical data would be loaded from CSV'
        }

    def _get_dashboard_snapshot(self):
        """Get complete dashboard snapshot."""
        return {
            'predictions': self._get_current_predictions(),
            'ensemble': self._get_ensemble_prediction(),
            'flow': self._get_flow_prediction(),
            'validation': self._get_validation_summary(),
            'performance': self._get_performance_analytics(),
            'timestamp': datetime.now().isoformat()
        }

    def run(self, debug=False):
        """Run the dashboard server."""
        print(f"\n{'='*80}")
        print(f"ADVANCED PREDICTION DASHBOARD")
        print(f"{'='*80}")
        print(f"Dashboard URL: http://localhost:{self.port}")
        print(f"Models loaded: {len(self.ensemble.models)}")
        print(f"Flow predictor: {'Ready' if self.flow_predictor.is_trained else 'Not trained'}")
        print(f"{'='*80}\n")

        self.socketio.run(self.app, host='0.0.0.0', port=self.port, debug=debug, allow_unsafe_werkzeug=True)


if __name__ == '__main__':
    dashboard = AdvancedPredictionDashboard(port=5002)
    dashboard.run(debug=True)
