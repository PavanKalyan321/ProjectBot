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

    def generate_ensemble_signal(self):
        """
        Generate ensemble betting signal using trained ML models.

        Returns:
            dict: Signal dictionary with keys:
                - should_bet: bool
                - confidence: float
                - prediction: float
                - range: tuple (low, high)
                - reason: str
                - log: str
                - models: list of dicts with keys:
                    - model_id: str
                    - prediction: float
                    - confidence: float
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
                'models': []
            }

        # Get recent multipliers
        recent_multipliers = recent_rounds['multiplier'].values.tolist()

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
                'models': []
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
        # If models agree (low std), boost confidence
        if pred_std < 0.3:
            ensemble_conf *= 1.1  # 10% boost for high agreement
        elif pred_std > 1.0:
            ensemble_conf *= 0.9  # 10% penalty for disagreement

        # Cap confidence at 95%
        ensemble_conf = min(95.0, ensemble_conf)

        # Log summary
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
            'agreement': round(pred_std, 2)
        }

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
