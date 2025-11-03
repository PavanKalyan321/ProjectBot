"""
Compact Analytics Dashboard for Half-Screen Viewing
Real-time bot monitoring with all models and trends
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
import webbrowser
import time

class CompactAnalyticsDashboard:
    """Half-screen optimized real-time analytics dashboard."""

    def __init__(self, port=5001):
        self.port = port
        self.app = Flask(__name__, template_folder='templates')
        self.socketio = SocketIO(self.app, cors_allowed_origins="*", async_mode='threading')

        # Data paths
        self.rounds_csv = "backend/aviator_rounds_history.csv"
        self.bets_csv = "backend/bet_history.csv"
        self.automl_csv = "backend/bot_automl_performance.csv"

        # Real-time data
        self.current_round = {}
        self.recent_rounds = deque(maxlen=20)
        self.live_stats = {
            'total_rounds': 0,
            'win_rate': 0,
            'profit_loss': 0,
            'best_model': 'N/A',
            'trend': 'NEUTRAL',
            'signal': 'WAIT'
        }

        # Model performance tracking
        self.model_accuracy = {}
        self.trend_analyzer = TrendAnalyzer()

        # Cache
        self._cache = {}
        self._cache_time = None

        self._setup_routes()
        self._setup_socketio()

    def _setup_routes(self):
        """Setup Flask routes."""

        @self.app.route('/')
        def index():
            return render_template('compact_dashboard.html')

        @self.app.route('/api/current_round')
        def get_current_round():
            """Get current round information with all model predictions."""
            return jsonify(self._get_current_round_data())

        @self.app.route('/api/live_stats')
        def get_live_stats():
            """Get live statistics."""
            return jsonify(self._get_live_stats())

        @self.app.route('/api/model_comparison')
        def get_model_comparison():
            """Get all 16 models comparison."""
            return jsonify(self._get_model_comparison())

        @self.app.route('/api/trend_signal')
        def get_trend_signal():
            """Get trend analysis and signal."""
            return jsonify(self._get_trend_signal())

        @self.app.route('/api/recent_rounds')
        def get_recent_rounds():
            """Get last 20 rounds with predictions."""
            limit = int(request.args.get('limit', 20))
            return jsonify(self._get_recent_rounds_data(limit))

        @self.app.route('/api/top_models')
        def get_top_models():
            """Get top performing models."""
            return jsonify(self._get_top_models())

        @self.app.route('/api/rules_status')
        def get_rules_status():
            """Get game rules status."""
            return jsonify(self._get_rules_status())

        @self.app.route('/api/cleanup', methods=['POST'])
        def cleanup_data():
            """Clean up data files."""
            result = self._cleanup_data()
            return jsonify(result)

    def _setup_socketio(self):
        """Setup SocketIO for real-time updates."""

        @self.socketio.on('connect')
        def handle_connect():
            print(f"Client connected")
            emit('initial_data', self._get_live_stats())

        @self.socketio.on('disconnect')
        def handle_disconnect():
            print(f"Client disconnected")

        @self.socketio.on('request_update')
        def handle_update_request():
            emit('live_update', self._get_current_round_data())

    def _load_latest_data(self):
        """Load latest data from CSVs with error handling."""
        try:
            # Load AutoML data (most comprehensive) with error handling
            automl_df = pd.DataFrame()
            if os.path.exists(self.automl_csv):
                try:
                    # Try loading with on_bad_lines parameter (pandas >= 1.3.0)
                    automl_df = pd.read_csv(self.automl_csv, on_bad_lines='skip')
                except TypeError:
                    # Fallback for older pandas versions
                    try:
                        automl_df = pd.read_csv(self.automl_csv, error_bad_lines=False, warn_bad_lines=False)
                    except:
                        automl_df = pd.read_csv(self.automl_csv)

            if not automl_df.empty:
                # Convert types
                if 'actual_multiplier' in automl_df.columns:
                    automl_df['actual_multiplier'] = pd.to_numeric(automl_df['actual_multiplier'], errors='coerce')
                if 'ensemble_prediction' in automl_df.columns:
                    automl_df['ensemble_prediction'] = pd.to_numeric(automl_df['ensemble_prediction'], errors='coerce')

            # Load rounds data with error handling
            rounds_df = pd.DataFrame()
            if os.path.exists(self.rounds_csv):
                try:
                    rounds_df = pd.read_csv(self.rounds_csv, header=None, on_bad_lines='skip')
                except TypeError:
                    try:
                        rounds_df = pd.read_csv(self.rounds_csv, header=None, error_bad_lines=False, warn_bad_lines=False)
                    except:
                        rounds_df = pd.read_csv(self.rounds_csv, header=None)

            if not rounds_df.empty and len(rounds_df.columns) >= 3:
                rounds_df.columns = ['timestamp', 'round_id', 'multiplier'] + [f'col_{i}' for i in range(len(rounds_df.columns) - 3)]
                if 'multiplier' in rounds_df.columns:
                    rounds_df['multiplier'] = pd.to_numeric(rounds_df['multiplier'], errors='coerce')

            # Load bets data with error handling
            bets_df = pd.DataFrame()
            if os.path.exists(self.bets_csv):
                try:
                    bets_df = pd.read_csv(self.bets_csv, on_bad_lines='skip')
                except TypeError:
                    try:
                        bets_df = pd.read_csv(self.bets_csv, error_bad_lines=False, warn_bad_lines=False)
                    except:
                        bets_df = pd.read_csv(self.bets_csv)

            return {
                'automl': automl_df,
                'rounds': rounds_df,
                'bets': bets_df
            }

        except Exception as e:
            print(f"Error loading data: {e}")
            return {'automl': pd.DataFrame(), 'rounds': pd.DataFrame(), 'bets': pd.DataFrame()}

    def _get_current_round_data(self):
        """Get current round with all model predictions."""
        data = self._load_latest_data()
        automl_df = data['automl']

        if automl_df.empty:
            return {
                'round_id': 'N/A',
                'actual': 0,
                'ensemble_prediction': 0,
                'confidence': 0,
                'models': [],
                'best_model': 'N/A',
                'trend': 'NEUTRAL',
                'signal': 'WAIT'
            }

        # Get latest round
        latest = automl_df.iloc[-1]

        # Extract all 16 model predictions
        model_predictions = []
        model_cols = [col for col in automl_df.columns if 'model_' in col and col.endswith('_pred')]

        for i, col in enumerate(model_cols[:16], 1):
            pred_value = float(latest[col]) if pd.notna(latest[col]) else 0
            actual_value = float(latest['actual_multiplier']) if pd.notna(latest.get('actual_multiplier')) else 0

            error = abs(pred_value - actual_value) if actual_value > 0 else 0
            accuracy = max(0, 100 - (error / max(actual_value, 1) * 100))

            model_predictions.append({
                'name': f'Model {i}',
                'prediction': round(pred_value, 2),
                'error': round(error, 2),
                'accuracy': round(accuracy, 1)
            })

        # Find best model
        if model_predictions:
            best_model = min(model_predictions, key=lambda x: x['error'])
        else:
            best_model = {'name': 'N/A', 'prediction': 0, 'accuracy': 0}

        # Get trend
        trend_data = self._analyze_trend(automl_df)

        return {
            'round_id': str(latest.get('round_id', 'N/A')),
            'timestamp': str(latest.get('timestamp', '')),
            'actual': round(float(latest.get('actual_multiplier', 0)), 2) if pd.notna(latest.get('actual_multiplier')) else 0,
            'ensemble_prediction': round(float(latest.get('ensemble_prediction', 0)), 2) if pd.notna(latest.get('ensemble_prediction')) else 0,
            'ensemble_range': str(latest.get('ensemble_range', 'N/A')),
            'confidence': round(float(latest.get('ensemble_confidence', 0)), 1) if pd.notna(latest.get('ensemble_confidence')) else 0,
            'recommendation': bool(latest.get('recommendation_should_bet', False)),
            'target': round(float(latest.get('recommendation_target', 0)), 2) if pd.notna(latest.get('recommendation_target')) else 0,
            'models': model_predictions,
            'best_model': best_model['name'],
            'best_model_accuracy': best_model['accuracy'],
            'trend': trend_data['trend'],
            'signal': trend_data['signal'],
            'trend_strength': trend_data['strength']
        }

    def _get_live_stats(self):
        """Get live statistics summary."""
        data = self._load_latest_data()
        automl_df = data['automl']
        bets_df = data['bets']

        stats = {
            'total_rounds': len(automl_df),
            'total_bets': 0,
            'win_rate': 0,
            'profit_loss': 0,
            'avg_confidence': 0,
            'avg_accuracy': 0,
            'current_streak': 0,
            'streak_type': 'N/A'
        }

        if not automl_df.empty:
            # Calculate average confidence
            if 'ensemble_confidence' in automl_df.columns:
                stats['avg_confidence'] = round(float(automl_df['ensemble_confidence'].mean()), 1)

            # Calculate accuracy
            if 'range_correct' in automl_df.columns:
                correct = automl_df['range_correct'].sum()
                stats['avg_accuracy'] = round(float(correct / len(automl_df) * 100), 1)

        if not bets_df.empty and 'Profit/Loss' in bets_df.columns:
            actual_bets = bets_df[bets_df['Bet Placed'] == 'Yes'] if 'Bet Placed' in bets_df.columns else bets_df
            stats['total_bets'] = len(actual_bets)

            if len(actual_bets) > 0:
                profit_loss = actual_bets['Profit/Loss'].sum()
                stats['profit_loss'] = round(float(profit_loss), 2)

                wins = len(actual_bets[actual_bets['Profit/Loss'] > 0])
                stats['win_rate'] = round(float(wins / len(actual_bets) * 100), 1)

                # Calculate current streak
                recent = actual_bets.tail(10)['Profit/Loss']
                streak_count = 0
                streak_type = 'N/A'

                if len(recent) > 0:
                    is_win = recent.iloc[-1] > 0
                    streak_type = 'WIN' if is_win else 'LOSS'

                    for val in reversed(recent.values):
                        if (val > 0) == is_win:
                            streak_count += 1
                        else:
                            break

                stats['current_streak'] = streak_count
                stats['streak_type'] = streak_type

        return stats

    def _get_model_comparison(self):
        """Compare all 16 models."""
        data = self._load_latest_data()
        automl_df = data['automl']

        if automl_df.empty:
            return {'models': []}

        model_cols = [col for col in automl_df.columns if 'model_' in col and col.endswith('_pred')]

        comparison = []

        for i, col in enumerate(model_cols[:16], 1):
            predictions = automl_df[col].dropna()
            actuals = automl_df['actual_multiplier'].dropna() if 'actual_multiplier' in automl_df.columns else pd.Series()

            if len(predictions) > 0 and len(actuals) > 0:
                # Align predictions and actuals
                min_len = min(len(predictions), len(actuals))
                errors = abs(predictions.tail(min_len).values - actuals.tail(min_len).values)

                avg_error = float(np.mean(errors))
                median_error = float(np.median(errors))
                accuracy = max(0, 100 - (avg_error / actuals.tail(min_len).mean() * 100)) if actuals.tail(min_len).mean() > 0 else 0

                comparison.append({
                    'model': f'Model {i}',
                    'avg_error': round(avg_error, 2),
                    'median_error': round(median_error, 2),
                    'accuracy': round(accuracy, 1),
                    'predictions': len(predictions)
                })

        # Sort by accuracy
        comparison.sort(key=lambda x: x['accuracy'], reverse=True)

        return {'models': comparison}

    def _get_trend_signal(self):
        """Get trend analysis and trading signal."""
        data = self._load_latest_data()
        automl_df = data['automl']

        if automl_df.empty or len(automl_df) < 5:
            return {
                'trend': 'NEUTRAL',
                'signal': 'WAIT',
                'strength': 0,
                'analysis': 'Insufficient data'
            }

        return self._analyze_trend(automl_df)

    def _analyze_trend(self, df):
        """Analyze multiplier trend."""
        if df.empty or 'actual_multiplier' not in df.columns:
            return {'trend': 'NEUTRAL', 'signal': 'WAIT', 'strength': 0, 'analysis': 'No data'}

        # Get last 10 rounds
        recent = df['actual_multiplier'].tail(10).dropna()

        if len(recent) < 5:
            return {'trend': 'NEUTRAL', 'signal': 'WAIT', 'strength': 0, 'analysis': 'Insufficient data'}

        # Calculate trend indicators
        avg_recent = recent.tail(5).mean()
        avg_older = recent.head(5).mean()

        # Volatility
        volatility = recent.std()

        # Direction
        if avg_recent > avg_older * 1.1:
            trend = 'UPWARD'
            signal = 'CAUTIOUS'  # High multipliers mean next might be low
        elif avg_recent < avg_older * 0.9:
            trend = 'DOWNWARD'
            signal = 'OPPORTUNITY'  # Low multipliers mean recovery likely
        else:
            trend = 'NEUTRAL'
            signal = 'WAIT'

        # Calculate strength (0-100)
        strength = min(100, abs(avg_recent - avg_older) / avg_older * 100)

        # Check for low greens pattern (multiple rounds < 2x)
        low_greens = (recent < 2.0).sum()
        if low_greens >= 3:
            signal = 'STRONG_BET'
            analysis = f'Low green pattern detected ({low_greens}/10 rounds < 2x)'
        elif avg_recent > 5.0:
            signal = 'SKIP'
            analysis = f'High multiplier phase (avg: {avg_recent:.2f}x)'
        elif volatility > 2.0:
            analysis = f'High volatility detected (σ={volatility:.2f})'
        else:
            analysis = f'Trend: {trend}, Avg: {avg_recent:.2f}x'

        return {
            'trend': trend,
            'signal': signal,
            'strength': round(strength, 1),
            'analysis': analysis,
            'avg_recent': round(avg_recent, 2),
            'volatility': round(volatility, 2),
            'low_greens': int(low_greens)
        }

    def _get_recent_rounds_data(self, limit=20):
        """Get recent rounds with predictions."""
        data = self._load_latest_data()
        automl_df = data['automl']

        if automl_df.empty:
            return {'rounds': []}

        recent = automl_df.tail(limit)

        rounds = []
        for _, row in recent.iterrows():
            rounds.append({
                'round_id': str(row.get('round_id', 'N/A')),
                'actual': round(float(row.get('actual_multiplier', 0)), 2) if pd.notna(row.get('actual_multiplier')) else 0,
                'prediction': round(float(row.get('ensemble_prediction', 0)), 2) if pd.notna(row.get('ensemble_prediction')) else 0,
                'range': str(row.get('ensemble_range', 'N/A')),
                'confidence': round(float(row.get('ensemble_confidence', 0)), 1) if pd.notna(row.get('ensemble_confidence')) else 0,
                'recommended': bool(row.get('recommendation_should_bet', False)),
                'error': round(abs(float(row.get('actual_multiplier', 0)) - float(row.get('ensemble_prediction', 0))), 2)
            })

        return {'rounds': rounds}

    def _get_top_models(self):
        """Get top 3 performing models."""
        comparison = self._get_model_comparison()

        if not comparison['models']:
            return {'top_models': []}

        top_3 = comparison['models'][:3]

        return {'top_models': top_3}

    def _get_rules_status(self):
        """Get game rules status and patterns."""
        data = self._load_latest_data()
        automl_df = data['automl']

        if automl_df.empty or 'actual_multiplier' not in automl_df.columns:
            return {'rules': [], 'patterns': {}}

        recent = automl_df['actual_multiplier'].tail(20).dropna()

        rules_status = []

        # Rule 1: Low Green Series (3+ rounds < 2x)
        low_greens = (recent.tail(10) < 2.0).sum()
        rules_status.append({
            'name': 'Low Green Series',
            'active': bool(low_greens >= 3),
            'count': int(low_greens),
            'signal': 'BET' if low_greens >= 3 else 'WAIT'
        })

        # Rule 2: Post-High Echo (after 10x+ comes low)
        has_high = (recent.tail(5) >= 10.0).any()
        rules_status.append({
            'name': 'Post-High Echo',
            'active': bool(has_high),
            'signal': 'CAUTIOUS' if has_high else 'NEUTRAL'
        })

        # Rule 3: Mean Reversion (extended deviation)
        mean = recent.mean()
        current = recent.iloc[-1] if len(recent) > 0 else 0
        deviation = abs(current - mean) / mean if mean > 0 else 0

        rules_status.append({
            'name': 'Mean Reversion',
            'active': bool(deviation > 0.5),
            'signal': 'REVERSION_LIKELY' if current > mean else 'STABLE'
        })

        # Patterns
        patterns = {
            'avg_multiplier': round(float(recent.mean()), 2),
            'median_multiplier': round(float(recent.median()), 2),
            'max_recent': round(float(recent.max()), 2),
            'min_recent': round(float(recent.min()), 2),
            'volatility': round(float(recent.std()), 2)
        }

        return {
            'rules': rules_status,
            'patterns': patterns
        }

    def _cleanup_data(self):
        """Clean up data files."""
        try:
            cleaned_count = 0

            for csv_file in [self.automl_csv, self.rounds_csv, self.bets_csv]:
                if not os.path.exists(csv_file):
                    continue

                df = pd.read_csv(csv_file)
                original_len = len(df)

                # Remove duplicates
                if 'round_id' in df.columns:
                    df = df.drop_duplicates(subset=['round_id'], keep='last')

                # Remove all-null rows
                df = df.dropna(how='all')

                cleaned_count += original_len - len(df)

                # Save
                df.to_csv(csv_file, index=False)

            return {
                'success': True,
                'rows_removed': cleaned_count,
                'message': f'Cleaned {cleaned_count} duplicate/empty rows'
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def broadcast_update(self, round_data):
        """Broadcast round update to all connected clients."""
        self.socketio.emit('live_update', round_data)

    def run(self, open_browser=True):
        """Run the dashboard server."""
        print(f"\n{'='*60}")
        print(f"  Compact Analytics Dashboard - Half Screen Mode")
        print(f"{'='*60}")
        print(f"  URL: http://localhost:{self.port}")
        print(f"  Optimized for 50% screen width")
        print(f"  Real-time model predictions & trend analysis")
        print(f"  Press Ctrl+C to stop")
        print(f"{'='*60}\n")

        if open_browser:
            threading.Timer(1.5, lambda: webbrowser.open(f'http://localhost:{self.port}')).start()

        self.socketio.run(self.app, host='0.0.0.0', port=self.port, debug=False, allow_unsafe_werkzeug=True)


class TrendAnalyzer:
    """Analyze trends and patterns."""

    def __init__(self):
        self.history = deque(maxlen=50)

    def add_round(self, multiplier):
        """Add a round to history."""
        self.history.append(multiplier)

    def get_trend(self):
        """Get current trend."""
        if len(self.history) < 5:
            return 'NEUTRAL'

        recent = list(self.history)[-5:]
        older = list(self.history)[-10:-5] if len(self.history) >= 10 else recent

        avg_recent = np.mean(recent)
        avg_older = np.mean(older)

        if avg_recent > avg_older * 1.15:
            return 'STRONG_UP'
        elif avg_recent > avg_older * 1.05:
            return 'UP'
        elif avg_recent < avg_older * 0.85:
            return 'STRONG_DOWN'
        elif avg_recent < avg_older * 0.95:
            return 'DOWN'
        else:
            return 'NEUTRAL'


if __name__ == '__main__':
    dashboard = CompactAnalyticsDashboard(port=5001)
    dashboard.run()
