"""
ML Signal Generator - Uses trained models for predictions
Replaces random predictions with actual ML inference
"""

import numpy as np
from .ml_models import AviatorMLModels


class MLSignalGenerator:
    """Generate betting signals based on trained ML models."""

    def __init__(self, history_tracker):
        """
        Initialize ML signal generator with trained models.

        Args:
            history_tracker: RoundHistoryTracker instance
        """
        self.history_tracker = history_tracker
        self.confidence_threshold = 65.0
        self.feature_window = 20

        # Initialize ML models
        self.ml_models = AviatorMLModels(models_dir='models')

        # Try to load existing trained models
        loaded = self.ml_models.load_models()
        if not loaded:
            print("\nWARNING: No trained models found!")
            print("   Run 'python train_models.py' to train models on historical data")
            print("   Using placeholder predictions until models are trained\n")

    def generate_ensemble_signal(self, strategy='hybrid'):
        """
        Generate betting signal using hybrid or regression strategy.

        Args:
            strategy: 'hybrid' (green classifier + Position2) or 'regression' (old method)

        Returns:
            dict: Signal dictionary with keys:
                - should_bet: bool
                - confidence: float
                - prediction: float
                - range: tuple (low, high)
                - reason: str
                - log: str
                - models: list of dicts
                - strategy: str (which position/strategy was used)
                - target_multiplier: float (for hybrid mode)
        """
        recent_rounds = self.history_tracker.get_recent_rounds(self.feature_window + 10)

        if len(recent_rounds) < self.feature_window:
            return {
                'should_bet': False,
                'confidence': 0,
                'prediction': 0,
                'range': (0, 0),
                'reason': f'Need {self.feature_window} rounds, have {len(recent_rounds)}',
                'log': 'Insufficient data for signal generation.',
                'models': [],
                'strategy': 'none',
                'target_multiplier': 0
            }

        # Get recent multipliers
        recent_multipliers = recent_rounds['multiplier'].values.tolist()

        if strategy == 'hybrid':
            return self._generate_hybrid_signal(recent_multipliers)
        else:
            return self._generate_regression_signal(recent_multipliers)

    def _generate_hybrid_signal(self, recent_multipliers):
        """
        HYBRID STRATEGY:
        - Position 1 (conservative): Use ML green classifier for 1.5x-2x targets
        - Position 2 (aggressive): Use rule-based logic for 3x+ targets

        Args:
            recent_multipliers: List of recent multipliers

        Returns:
            dict: Signal with position-specific recommendations
        """
        # Try Position 1 first (ML Green Classifier for 1.5x or 2x)
        pos1_signal_15 = self.ml_models.predict_green_probability(recent_multipliers, target_multiplier=1.5)
        pos1_signal_20 = self.ml_models.predict_green_probability(recent_multipliers, target_multiplier=2.0)

        # Try Position 2 (Rule-based for 3x+)
        pos2_signal = self._generate_position2_signal(recent_multipliers)

        # Decision priority:
        # 1. If Position 1 (1.5x) has high confidence -> use it (safest)
        # 2. Else if Position 2 has signal -> use it (aggressive)
        # 3. Else skip

        # Position 1 evaluation (prefer 1.5x for safety, fallback to 2x)
        use_pos1 = False
        pos1_target = 1.5
        pos1_confidence = pos1_signal_15['confidence']

        if pos1_signal_15['recommendation'] == 'BET' and pos1_confidence >= 55:
            use_pos1 = True
            pos1_target = 1.5
            pos1_green_prob = pos1_signal_15['green_probability']
        elif pos1_signal_20['recommendation'] == 'BET' and pos1_signal_20['confidence'] >= 50:
            use_pos1 = True
            pos1_target = 2.0
            pos1_confidence = pos1_signal_20['confidence']
            pos1_green_prob = pos1_signal_20['green_probability']

        # Decision logic
        if use_pos1:
            # USE POSITION 1 (ML Green Classifier)
            return {
                'should_bet': True,
                'confidence': pos1_confidence,
                'prediction': pos1_target,
                'range': (pos1_target - 0.2, pos1_target + 0.2),
                'reason': f"Position 1: {pos1_green_prob:.1f}% chance of hitting {pos1_target}x",
                'log': f"Strategy: Position 1 (ML Green Classifier)\n"
                       f"Target: {pos1_target}x\n"
                       f"Green Probability: {pos1_green_prob:.1f}%\n"
                       f"Model Confidence: {pos1_confidence:.1f}%\n"
                       f"Model Accuracy: {pos1_signal_15['accuracy']:.1f}% (historical)",
                'models': [],  # Not using regression models
                'strategy': 'position1_green_classifier',
                'target_multiplier': pos1_target,
                'green_probability': pos1_green_prob,
                'classifier_accuracy': pos1_signal_15.get('accuracy', 0)
            }

        elif pos2_signal['should_bet']:
            # USE POSITION 2 (Rule-based for high multipliers)
            return pos2_signal

        else:
            # SKIP - No position recommends betting
            # Build detailed skip reasoning
            skip_details = []

            # Position 1 analysis
            pos1_15_prob = pos1_signal_15['green_probability']
            pos1_20_prob = pos1_signal_20['green_probability']

            skip_details.append("🎯 POSITION 1 (ML Green Classifier):")
            skip_details.append(f"   • 1.5x Target: {pos1_15_prob:.1f}% green probability, {pos1_signal_15['confidence']:.1f}% confidence")
            skip_details.append(f"     ↳ Threshold: Need 55% confidence (currently {pos1_signal_15['confidence']:.1f}%)")

            if pos1_signal_15['confidence'] < 55:
                gap = 55 - pos1_signal_15['confidence']
                skip_details.append(f"     ↳ Gap: {gap:.1f}% below threshold - pattern not strong enough")

            skip_details.append(f"   • 2.0x Target: {pos1_20_prob:.1f}% green probability, {pos1_signal_20['confidence']:.1f}% confidence")
            skip_details.append(f"     ↳ Threshold: Need 50% confidence (currently {pos1_signal_20['confidence']:.1f}%)")

            if pos1_signal_20['confidence'] < 50:
                gap = 50 - pos1_signal_20['confidence']
                skip_details.append(f"     ↳ Gap: {gap:.1f}% below threshold - pattern not strong enough")

            # Position 2 analysis
            skip_details.append("")
            skip_details.append("🎲 POSITION 2 (Rule-Based Pattern Detection):")

            # Get last 10 rounds for pattern info
            last_10 = recent_multipliers[-10:]
            low_count = sum(1 for m in last_10 if m < 2.0)
            high_count = sum(1 for m in last_10 if m >= 3.0)
            has_recent_high = any(m >= 5.0 for m in last_10)

            if has_recent_high:
                highest = max(m for m in last_10 if m >= 5.0)
                skip_details.append(f"   • Burst pattern detected: {highest:.2f}x in last 10 rounds")
                skip_details.append(f"     ↳ Waiting for pattern to cool down before betting")
            else:
                skip_details.append(f"   • Cold streak: {low_count}/10 rounds below 2x")
                skip_details.append(f"     ↳ Threshold: Need 7+ low rounds (currently {low_count})")
                if low_count < 7:
                    skip_details.append(f"     ↳ Gap: Need {7 - low_count} more low rounds to trigger bet")

            skip_details.append(f"   • Pattern strength: {pos2_signal['confidence']:.1f}% (too weak)")

            skip_reason_detailed = "\n".join(skip_details)

            return {
                'should_bet': False,
                'confidence': max(pos1_confidence, pos2_signal['confidence']),
                'prediction': 0,
                'range': (0, 0),
                'reason': f"Position 1: {pos1_confidence:.1f}% (need 55%), Position 2: {pos2_signal['reason']}",
                'log': f"Position 1 (1.5x): {pos1_signal_15['green_probability']:.1f}% green prob, {pos1_signal_15['confidence']:.1f}% confidence\n"
                       f"Position 1 (2.0x): {pos1_signal_20['green_probability']:.1f}% green prob, {pos1_signal_20['confidence']:.1f}% confidence\n"
                       f"Position 2 (3x+): {pos2_signal['reason']}",
                'models': [],
                'strategy': 'skip',
                'target_multiplier': 0,
                'skip_reason_detailed': skip_reason_detailed,
                'pos1_signal_15': pos1_signal_15,
                'pos1_signal_20': pos1_signal_20,
                'pos2_analysis': {
                    'low_count': low_count,
                    'high_count': high_count,
                    'has_recent_high': has_recent_high,
                    'last_10_mults': last_10
                }
            }

    def _generate_position2_signal(self, recent_multipliers):
        """
        Position 2 Rule-Based Strategy for high multipliers (3x+).
        Based on burst patterns and cold streaks.

        Args:
            recent_multipliers: List of recent multipliers

        Returns:
            dict: Position 2 signal
        """
        # Simple rule-based logic for Position 2
        # Look for "cold streak" (many low rounds) suggesting high round is due
        last_10 = recent_multipliers[-10:]
        low_count = sum(1 for m in last_10 if m < 2.0)
        high_count = sum(1 for m in last_10 if m >= 3.0)

        # Check if there's been a burst pattern
        has_recent_high = any(m >= 5.0 for m in last_10)

        # Position 2 rules:
        # 1. If 7+ low rounds in last 10 -> bet on 3x (due for high)
        # 2. If recent high exists -> skip (burst already happened)

        if has_recent_high:
            return {
                'should_bet': False,
                'confidence': 30,
                'prediction': 0,
                'range': (0, 0),
                'reason': f"Position 2: Recent burst detected, waiting",
                'log': f"Position 2: Burst pattern detected in last 10 rounds",
                'models': [],
                'strategy': 'position2_skip',
                'target_multiplier': 0
            }

        if low_count >= 7:
            # Cold streak - bet on 3x
            confidence = min(70, 40 + (low_count * 5))  # Higher confidence for longer streak
            return {
                'should_bet': True,
                'confidence': confidence,
                'prediction': 3.0,
                'range': (2.5, 5.0),
                'reason': f"Position 2: Cold streak ({low_count}/10 low rounds)",
                'log': f"Strategy: Position 2 (Rule-based)\n"
                       f"Target: 3.0x\n"
                       f"Cold Streak: {low_count}/10 rounds below 2x\n"
                       f"Pattern: Expecting higher multiplier",
                'models': [],
                'strategy': 'position2_cold_streak',
                'target_multiplier': 3.0,
                'cold_streak_length': low_count
            }

        # Not enough signal for Position 2
        return {
            'should_bet': False,
            'confidence': 35,
            'prediction': 0,
            'range': (0, 0),
            'reason': f"Position 2: Pattern not strong enough ({low_count}/10 low)",
            'log': f"Position 2: Cold streak {low_count}/10 (need 7+)",
            'models': [],
            'strategy': 'position2_skip',
            'target_multiplier': 0
        }

    def _generate_regression_signal(self, recent_multipliers):
        """
        Original regression-based signal generation (old method).

        Args:
            recent_multipliers: List of recent multipliers

        Returns:
            dict: Regression signal
        """
        # Get predictions from trained models
        model_outputs = self.ml_models.predict(recent_multipliers)

        if not model_outputs:
            return {
                'should_bet': False,
                'confidence': 0,
                'prediction': 0,
                'range': (0, 0),
                'reason': 'Model prediction failed',
                'log': 'Unable to generate predictions.',
                'models': [],
                'strategy': 'regression_failed',
                'target_multiplier': 0
            }

        # Ensemble metrics
        predictions = [m['prediction'] for m in model_outputs]
        confidences = [m['confidence'] for m in model_outputs]

        ensemble_pred = np.mean(predictions)
        ensemble_conf = np.mean(confidences)
        pred_std = np.std(predictions)

        # Calculate prediction range (std-based)
        pred_range = (
            max(1.0, ensemble_pred - pred_std),
            ensemble_pred + pred_std
        )

        # Expected value calculation
        expected_value = round(ensemble_pred * (ensemble_conf / 100), 2)

        # Decision logic
        should_bet = ensemble_conf >= self.confidence_threshold

        # Adjust confidence based on prediction agreement
        if pred_std < 0.3:
            ensemble_conf *= 1.1
        elif pred_std > 1.0:
            ensemble_conf *= 0.9

        ensemble_conf = min(95.0, ensemble_conf)

        log_lines = [
            f"{m['model_id']}: pred={m['prediction']:.2f}x, conf={m['confidence']:.1f}%"
            for m in model_outputs
        ]
        log_summary = (
            f"Expected Value: {expected_value} | "
            f"Ensemble Prediction: {ensemble_pred:.2f}x | "
            f"Ensemble Confidence: {ensemble_conf:.1f}% | "
            f"Agreement: {pred_std:.2f} | "
            f"Decision: {'Bet' if should_bet else 'Skip'}"
        )

        return {
            'should_bet': should_bet,
            'confidence': round(ensemble_conf, 2),
            'prediction': round(ensemble_pred, 2),
            'range': (round(pred_range[0], 2), round(pred_range[1], 2)),
            'reason': f"Ensemble confidence: {ensemble_conf:.1f}%",
            'log': "\n".join(log_lines + [log_summary]),
            'models': model_outputs,
            'expected_value': expected_value,
            'agreement': round(pred_std, 2),
            'strategy': 'regression',
            'target_multiplier': round(ensemble_pred, 2)
        }

    def get_highest_multipliers_by_time(self):
        """
        Get highest multipliers for different time windows (5, 10, 20, 30 minutes).
        Assumes average round duration is ~10 seconds (6 rounds per minute).

        Returns:
            dict: Highest multipliers for each time window
        """
        try:
            # Time windows in minutes
            time_windows = {
                '5min': 5,
                '10min': 10,
                '20min': 20,
                '30min': 30
            }

            results = {}

            for window_name, minutes in time_windows.items():
                # Approximate rounds per time window (6 rounds/min * minutes)
                rounds_count = minutes * 6

                # Get recent rounds for this window
                recent_rounds = self.history_tracker.get_recent_rounds(rounds_count)

                if recent_rounds.empty or 'multiplier' not in recent_rounds.columns:
                    results[window_name] = {
                        'max_multiplier': 0,
                        'rounds_analyzed': 0,
                        'timestamp': None
                    }
                    continue

                # Find max multiplier in this window
                max_mult = recent_rounds['multiplier'].max()
                max_idx = recent_rounds['multiplier'].idxmax()

                # Get timestamp if available
                timestamp = None
                if 'timestamp' in recent_rounds.columns:
                    timestamp = recent_rounds.loc[max_idx, 'timestamp']

                results[window_name] = {
                    'max_multiplier': round(max_mult, 2),
                    'rounds_analyzed': len(recent_rounds),
                    'timestamp': timestamp
                }

            return results

        except Exception as e:
            print(f"Error getting highest multipliers: {e}")
            return {}

    def get_top_multipliers_last_hour(self, top_n=10):
        """
        Get top N highest multipliers from the last hour.
        Assumes average round duration is ~10 seconds (6 rounds per minute, 360 rounds per hour).

        Args:
            top_n: Number of top multipliers to return (default: 10)

        Returns:
            list: List of tuples (multiplier, index_from_end, timestamp)
        """
        try:
            # Get last hour of rounds (360 rounds = 60 min * 6 rounds/min)
            rounds_in_hour = 60 * 6
            recent_rounds = self.history_tracker.get_recent_rounds(rounds_in_hour)

            if recent_rounds.empty or 'multiplier' not in recent_rounds.columns:
                return []

            # Get multipliers with their indices
            multipliers_data = []
            for idx, row in recent_rounds.iterrows():
                mult = row['multiplier']
                timestamp = row.get('timestamp', 'N/A')
                # Calculate position from end (how many rounds ago)
                position = len(recent_rounds) - list(recent_rounds.index).index(idx) - 1
                multipliers_data.append((mult, position, timestamp))

            # Sort by multiplier descending and get top N
            top_multipliers = sorted(multipliers_data, key=lambda x: x[0], reverse=True)[:top_n]

            return top_multipliers

        except Exception as e:
            print(f"Error getting top multipliers: {e}")
            return []

    def log_highest_multipliers(self):
        """
        Log the highest multipliers for 5, 10, 20, and 30 minute windows.
        Also shows top 10 multipliers from the last hour.
        """
        try:
            highest_mults = self.get_highest_multipliers_by_time()

            if not highest_mults:
                print("Unable to retrieve highest multipliers")
                return

            print("\n" + "="*60)
            print("HIGHEST MULTIPLIERS BY TIME WINDOW")
            print("="*60)

            for window_name in ['5min', '10min', '20min', '30min']:
                data = highest_mults.get(window_name, {})
                max_mult = data.get('max_multiplier', 0)
                rounds = data.get('rounds_analyzed', 0)
                timestamp = data.get('timestamp', 'N/A')

                print(f"{window_name:>8} | Max: {max_mult:6.2f}x | Rounds: {rounds:3d} | Time: {timestamp}")

            print("="*60)

            # Get and display top 10 multipliers from last hour
            top_mults = self.get_top_multipliers_last_hour(top_n=10)

            if top_mults:
                print("\n" + "="*60)
                print("TOP 10 MULTIPLIERS IN LAST HOUR")
                print("="*60)
                print(f"{'RANK':<6} | {'MULTIPLIER':<12} | {'ROUNDS AGO':<12} | {'TIME'}")
                print("-"*60)

                for rank, (mult, rounds_ago, timestamp) in enumerate(top_mults, 1):
                    print(f"{rank:<6} | {mult:>10.2f}x | {rounds_ago:>10d} | {timestamp}")

                print("="*60 + "\n")
            else:
                print("\n(No data available for top multipliers)\n")

        except Exception as e:
            print(f"Error logging highest multipliers: {e}")

    def analyze_recent_patterns(self, n_rounds=10):
        """
        Analyze recent round patterns.

        Args:
            n_rounds: Number of recent rounds to analyze

        Returns:
            dict: Pattern analysis
        """
        try:
            recent_rounds = self.history_tracker.get_recent_rounds(n_rounds)

            if recent_rounds.empty or 'multiplier' not in recent_rounds.columns:
                return {
                    'avg_multiplier': 0,
                    'volatility': 0,
                    'trend': 'unknown'
                }

            multipliers = recent_rounds['multiplier'].values

            avg_mult = np.mean(multipliers)
            volatility = np.std(multipliers)

            # Simple trend detection
            if len(multipliers) >= 3:
                recent_avg = np.mean(multipliers[-3:])
                older_avg = np.mean(multipliers[:-3]) if len(multipliers) > 3 else avg_mult
                trend = 'increasing' if recent_avg > older_avg else 'decreasing'
            else:
                trend = 'stable'

            return {
                'avg_multiplier': round(avg_mult, 2),
                'volatility': round(volatility, 2),
                'trend': trend,
                'recent_values': multipliers.tolist()
            }
        except Exception as e:
            print(f"Error analyzing patterns: {e}")
            return {
                'avg_multiplier': 0,
                'volatility': 0,
                'trend': 'unknown'
            }

    def set_confidence_threshold(self, threshold):
        """
        Set confidence threshold for betting.

        Args:
            threshold: Confidence threshold percentage (0-100)
        """
        self.confidence_threshold = max(0, min(100, threshold))

    def set_feature_window(self, window):
        """
        Set feature window size.

        Args:
            window: Number of rounds to use for features
        """
        self.feature_window = max(5, window)

    def retrain_models(self, csv_file='aviator_rounds_history.csv'):
        """
        Retrain ML models on latest data.

        Args:
            csv_file: Path to historical data CSV

        Returns:
            bool: True if retraining successful
        """
        print("\nRetraining ML models on latest data...")
        success = self.ml_models.train_models(csv_file=csv_file)
        if success:
            print("[OK] Models retrained successfully!")
        return success

    def get_model_info(self):
        """
        Get information about loaded models.

        Returns:
            dict: Model metadata
        """
        return {
            'is_trained': self.ml_models.is_trained,
            'last_train_date': self.ml_models.last_train_date,
            'train_samples': self.ml_models.train_samples,
            'model_scores': self.ml_models.model_scores,
            'models_available': [
                name for name, model in [
                    ('RandomForest', self.ml_models.random_forest),
                    ('GradientBoosting', self.ml_models.gradient_boosting),
                    ('LightGBM', self.ml_models.lightgbm),
                    ('LSTM', self.ml_models.lstm)
                ] if model is not None
            ]
        }
