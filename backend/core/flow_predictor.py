"""
Flow Prediction System for Aviator
Predicts whether upcoming rounds will have HIGH or LOW flow (volatility)
"""

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
import pickle
import os
from datetime import datetime


class FlowPredictor:
    """
    Predicts flow patterns for upcoming rounds.

    Flow Types:
    - HIGH FLOW: High volatility, more extreme multipliers (>5x, <1.5x)
    - LOW FLOW: Low volatility, stable mid-range multipliers (1.5x-3x)
    """

    def __init__(self, models_dir='models/flow_predictor'):
        """Initialize flow prediction system."""
        self.models_dir = models_dir
        os.makedirs(models_dir, exist_ok=True)

        # Models
        self.flow_classifier = None  # Predicts HIGH/LOW flow
        self.volatility_predictor = None  # Predicts volatility score
        self.scaler = StandardScaler()

        # Configuration
        self.window_size = 20  # Analyze last N rounds
        self.forecast_horizon = 10  # Predict next N rounds

        # Metadata
        self.is_trained = False
        self.last_train_date = None
        self.performance_metrics = {}

    def _engineer_flow_features(self, multipliers):
        """
        Create features for flow prediction.

        Args:
            multipliers: List of recent multipliers

        Returns:
            Feature vector
        """
        if len(multipliers) < self.window_size:
            return None

        sequence = multipliers[-self.window_size:]
        features = []

        # Basic statistics
        features.extend([
            np.mean(sequence),
            np.std(sequence),
            np.median(sequence),
            np.min(sequence),
            np.max(sequence),
            np.max(sequence) - np.min(sequence)  # Range (volatility indicator)
        ])

        # Coefficient of variation (normalized volatility)
        cv = np.std(sequence) / np.mean(sequence) if np.mean(sequence) > 0 else 0
        features.append(cv)

        # IQR (robust volatility measure)
        q25, q75 = np.percentile(sequence, [25, 75])
        iqr = q75 - q25
        features.append(iqr)

        # Distribution shape
        from scipy.stats import skew, kurtosis
        features.extend([skew(sequence), kurtosis(sequence)])

        # Count features (high/mid/low distribution)
        low_count = np.sum(np.array(sequence) < 1.5)
        mid_count = np.sum((np.array(sequence) >= 1.5) & (np.array(sequence) < 3.0))
        high_count = np.sum(np.array(sequence) >= 5.0)
        extreme_high = np.sum(np.array(sequence) >= 10.0)

        features.extend([
            low_count / len(sequence),  # % of low multipliers
            mid_count / len(sequence),  # % of mid multipliers
            high_count / len(sequence),  # % of high multipliers
            extreme_high / len(sequence)  # % of extreme multipliers
        ])

        # Trend analysis
        first_half_avg = np.mean(sequence[:len(sequence)//2])
        second_half_avg = np.mean(sequence[len(sequence)//2:])
        trend = second_half_avg - first_half_avg
        features.append(trend)

        # Alternation pattern (switching between high and low)
        alternations = 0
        for i in range(1, len(sequence)):
            if (sequence[i] >= 2.5 and sequence[i-1] < 2.5) or \
               (sequence[i] < 2.5 and sequence[i-1] >= 2.5):
                alternations += 1
        features.append(alternations / (len(sequence) - 1))

        # Consecutive patterns
        max_consecutive_low = 0
        max_consecutive_high = 0
        current_low_streak = 0
        current_high_streak = 0

        for val in sequence:
            if val < 2.0:
                current_low_streak += 1
                max_consecutive_low = max(max_consecutive_low, current_low_streak)
                current_high_streak = 0
            elif val >= 3.0:
                current_high_streak += 1
                max_consecutive_high = max(max_consecutive_high, current_high_streak)
                current_low_streak = 0
            else:
                current_low_streak = 0
                current_high_streak = 0

        features.extend([max_consecutive_low, max_consecutive_high])

        # Recent volatility vs historical volatility
        recent_5_std = np.std(sequence[-5:]) if len(sequence) >= 5 else np.std(sequence)
        historical_std = np.std(sequence)
        volatility_trend = recent_5_std - historical_std
        features.append(volatility_trend)

        # Time since last extreme event
        time_since_extreme = self.window_size
        for i in range(len(sequence)-1, -1, -1):
            if sequence[i] >= 10.0 or sequence[i] < 1.2:
                time_since_extreme = len(sequence) - 1 - i
                break
        features.append(time_since_extreme)

        # Gap analysis (time between high multipliers)
        high_indices = [i for i, x in enumerate(sequence) if x >= 5.0]
        if len(high_indices) >= 2:
            gaps = [high_indices[i+1] - high_indices[i] for i in range(len(high_indices)-1)]
            avg_gap = np.mean(gaps)
            std_gap = np.std(gaps)
        else:
            avg_gap = self.window_size
            std_gap = 0
        features.extend([avg_gap, std_gap])

        # Entropy (measure of unpredictability)
        bins = [0, 1.5, 2.0, 3.0, 5.0, 10.0, 100.0]
        hist, _ = np.histogram(sequence, bins=bins)
        hist = hist / len(sequence)
        hist = hist[hist > 0]
        entropy = -np.sum(hist * np.log2(hist)) if len(hist) > 0 else 0
        features.append(entropy)

        return np.array(features)

    def _label_flow_type(self, future_multipliers):
        """
        Label flow type based on upcoming multipliers.

        HIGH FLOW: High volatility (CV > 0.8, or multiple extremes)
        LOW FLOW: Low volatility (CV < 0.5, stable mid-range)

        Args:
            future_multipliers: List of upcoming multipliers

        Returns:
            'HIGH' or 'LOW'
        """
        if len(future_multipliers) == 0:
            return 'LOW'

        # Calculate metrics
        cv = np.std(future_multipliers) / np.mean(future_multipliers) if np.mean(future_multipliers) > 0 else 0
        extreme_count = np.sum((np.array(future_multipliers) >= 10.0) | (np.array(future_multipliers) < 1.3))
        high_count = np.sum(np.array(future_multipliers) >= 5.0)
        volatility = np.max(future_multipliers) - np.min(future_multipliers)

        # Determine flow type
        is_high_flow = (
            cv > 0.8 or  # High coefficient of variation
            extreme_count >= 2 or  # Multiple extreme values
            volatility > 8.0 or  # Large range
            high_count >= 3  # Multiple high multipliers
        )

        return 'HIGH' if is_high_flow else 'LOW'

    def _calculate_volatility_score(self, multipliers):
        """
        Calculate volatility score (0-100).

        Args:
            multipliers: List of multipliers

        Returns:
            Volatility score (0=very stable, 100=very volatile)
        """
        if len(multipliers) == 0:
            return 50.0

        cv = np.std(multipliers) / np.mean(multipliers) if np.mean(multipliers) > 0 else 0
        volatility = np.max(multipliers) - np.min(multipliers)
        extreme_ratio = np.sum((np.array(multipliers) >= 10.0) | (np.array(multipliers) < 1.3)) / len(multipliers)

        # Normalize to 0-100
        cv_score = min(100, cv * 80)
        range_score = min(100, volatility * 5)
        extreme_score = extreme_ratio * 100

        # Weighted combination
        score = (cv_score * 0.4) + (range_score * 0.3) + (extreme_score * 0.3)

        return float(min(100, max(0, score)))

    def train(self, csv_file='aviator_rounds_history.csv', min_samples=200):
        """
        Train flow prediction models.

        Args:
            csv_file: Path to historical data
            min_samples: Minimum samples required

        Returns:
            bool: Success status
        """
        print(f"\n{'='*80}")
        print("TRAINING FLOW PREDICTION SYSTEM")
        print(f"{'='*80}")

        if not os.path.exists(csv_file):
            print(f"ERROR: CSV file not found: {csv_file}")
            return False

        try:
            df = pd.read_csv(csv_file)
            print(f"[OK] Loaded {len(df)} rounds from {csv_file}")
        except Exception as e:
            print(f"ERROR: Failed to read CSV: {e}")
            return False

        # Clean data
        df = df.dropna(subset=['multiplier'])
        df = df[df['multiplier'] > 0]
        print(f"[OK] After cleaning: {len(df)} valid rounds")

        multipliers = df['multiplier'].values

        if len(multipliers) < min_samples + self.window_size + self.forecast_horizon:
            print(f"ERROR: Insufficient data. Need {min_samples}, have {len(multipliers)}")
            return False

        # Prepare training data
        X = []
        y_flow = []  # Flow labels (HIGH/LOW)
        y_volatility = []  # Volatility scores

        for i in range(len(multipliers) - self.window_size - self.forecast_horizon):
            # Features from current window
            features = self._engineer_flow_features(multipliers[i:i + self.window_size + 1])
            if features is None:
                continue

            # Labels from future window
            future = multipliers[i + self.window_size + 1:i + self.window_size + 1 + self.forecast_horizon]
            flow_label = self._label_flow_type(future)
            volatility_score = self._calculate_volatility_score(future)

            X.append(features)
            y_flow.append(1 if flow_label == 'HIGH' else 0)
            y_volatility.append(volatility_score)

        X = np.array(X)
        y_flow = np.array(y_flow)
        y_volatility = np.array(y_volatility)

        print(f"[OK] Created {len(X)} training samples with {X.shape[1]} features")

        # Check class balance
        high_count = np.sum(y_flow == 1)
        low_count = np.sum(y_flow == 0)
        print(f"[OK] Flow distribution: HIGH={high_count} ({high_count/len(y_flow)*100:.1f}%), LOW={low_count} ({low_count/len(y_flow)*100:.1f}%)")

        # Split data
        X_train, X_test, y_flow_train, y_flow_test, y_vol_train, y_vol_test = train_test_split(
            X, y_flow, y_volatility, test_size=0.2, random_state=42, shuffle=False
        )

        # Normalize features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)

        # Train flow classifier
        print(f"\n1. Training Flow Classifier (HIGH/LOW)...")
        self.flow_classifier = RandomForestClassifier(
            n_estimators=150,
            max_depth=12,
            min_samples_split=5,
            class_weight='balanced',
            random_state=42,
            n_jobs=-1
        )
        self.flow_classifier.fit(X_train_scaled, y_flow_train)

        # Evaluate
        from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
        y_flow_pred = self.flow_classifier.predict(X_test_scaled)
        accuracy = accuracy_score(y_flow_test, y_flow_pred)
        precision = precision_score(y_flow_test, y_flow_pred, zero_division=0)
        recall = recall_score(y_flow_test, y_flow_pred, zero_division=0)
        f1 = f1_score(y_flow_test, y_flow_pred, zero_division=0)

        print(f"   [OK] Accuracy:  {accuracy*100:.1f}%")
        print(f"   [OK] Precision: {precision*100:.1f}%")
        print(f"   [OK] Recall:    {recall*100:.1f}%")
        print(f"   [OK] F1 Score:  {f1:.3f}")

        self.performance_metrics['flow_classifier'] = {
            'accuracy': float(accuracy),
            'precision': float(precision),
            'recall': float(recall),
            'f1': float(f1)
        }

        # Train volatility predictor
        print(f"\n2. Training Volatility Score Predictor...")
        self.volatility_predictor = GradientBoostingClassifier(
            n_estimators=100,
            learning_rate=0.1,
            max_depth=6,
            random_state=42
        )

        # Convert volatility scores to classes (0-25: LOW, 25-50: MED_LOW, 50-75: MED_HIGH, 75-100: HIGH)
        y_vol_classes_train = np.digitize(y_vol_train, [25, 50, 75])
        y_vol_classes_test = np.digitize(y_vol_test, [25, 50, 75])

        self.volatility_predictor.fit(X_train_scaled, y_vol_classes_train)
        y_vol_pred = self.volatility_predictor.predict(X_test_scaled)

        vol_accuracy = accuracy_score(y_vol_classes_test, y_vol_pred)
        print(f"   [OK] Accuracy: {vol_accuracy*100:.1f}%")

        self.performance_metrics['volatility_predictor'] = {
            'accuracy': float(vol_accuracy)
        }

        # Update metadata
        self.is_trained = True
        self.last_train_date = datetime.now()

        print(f"\n{'='*80}")
        print("FLOW PREDICTION SYSTEM TRAINING COMPLETE")
        print(f"{'='*80}\n")

        # Save models
        self.save_models()

        return True

    def predict_flow(self, recent_multipliers):
        """
        Predict flow type for upcoming rounds.

        Args:
            recent_multipliers: List of recent multipliers

        Returns:
            dict: {
                'flow_type': 'HIGH' or 'LOW',
                'flow_probability': 0-100,
                'volatility_score': 0-100,
                'volatility_class': 'LOW'/'MED_LOW'/'MED_HIGH'/'HIGH',
                'confidence': 0-100,
                'recommendation': str
            }
        """
        if not self.is_trained:
            return {
                'flow_type': 'UNKNOWN',
                'flow_probability': 50.0,
                'volatility_score': 50.0,
                'volatility_class': 'MEDIUM',
                'confidence': 0.0,
                'recommendation': 'Model not trained'
            }

        # Engineer features
        features = self._engineer_flow_features(recent_multipliers)
        if features is None:
            return {
                'flow_type': 'UNKNOWN',
                'flow_probability': 50.0,
                'volatility_score': 50.0,
                'volatility_class': 'MEDIUM',
                'confidence': 0.0,
                'recommendation': 'Insufficient data'
            }

        X = features.reshape(1, -1)
        X_scaled = self.scaler.transform(X)

        # Predict flow type
        flow_proba = self.flow_classifier.predict_proba(X_scaled)[0]
        flow_pred = self.flow_classifier.predict(X_scaled)[0]
        flow_type = 'HIGH' if flow_pred == 1 else 'LOW'
        high_flow_probability = float(flow_proba[1] * 100)

        # Predict volatility
        vol_class = self.volatility_predictor.predict(X_scaled)[0]
        vol_classes = ['LOW', 'MED_LOW', 'MED_HIGH', 'HIGH']
        volatility_class = vol_classes[min(vol_class, 3)]

        # Estimate volatility score from class
        vol_score_map = {'LOW': 12.5, 'MED_LOW': 37.5, 'MED_HIGH': 62.5, 'HIGH': 87.5}
        volatility_score = vol_score_map[volatility_class]

        # Calculate confidence
        max_proba = max(flow_proba)
        confidence = float(max_proba * 100)

        # Generate recommendation
        if flow_type == 'HIGH' and confidence > 70:
            recommendation = "Expect volatile rounds - consider wider cashout targets"
        elif flow_type == 'LOW' and confidence > 70:
            recommendation = "Expect stable rounds - use conservative targets (1.5x-2x)"
        else:
            recommendation = "Mixed signals - proceed with caution"

        return {
            'flow_type': flow_type,
            'flow_probability': round(high_flow_probability, 1),
            'volatility_score': round(volatility_score, 1),
            'volatility_class': volatility_class,
            'confidence': round(confidence, 1),
            'recommendation': recommendation
        }

    def save_models(self):
        """Save flow prediction models."""
        if not self.is_trained:
            return

        # Save models
        if self.flow_classifier is not None:
            with open(os.path.join(self.models_dir, 'flow_classifier.pkl'), 'wb') as f:
                pickle.dump(self.flow_classifier, f)

        if self.volatility_predictor is not None:
            with open(os.path.join(self.models_dir, 'volatility_predictor.pkl'), 'wb') as f:
                pickle.dump(self.volatility_predictor, f)

        # Save scaler
        with open(os.path.join(self.models_dir, 'scaler.pkl'), 'wb') as f:
            pickle.dump(self.scaler, f)

        # Save metadata
        metadata = {
            'is_trained': self.is_trained,
            'last_train_date': self.last_train_date.isoformat() if self.last_train_date else None,
            'performance_metrics': self.performance_metrics,
            'window_size': self.window_size,
            'forecast_horizon': self.forecast_horizon
        }
        with open(os.path.join(self.models_dir, 'metadata.pkl'), 'wb') as f:
            pickle.dump(metadata, f)

        print(f"[OK] Flow prediction models saved to {self.models_dir}/")

    def load_models(self):
        """Load flow prediction models."""
        metadata_path = os.path.join(self.models_dir, 'metadata.pkl')
        if not os.path.exists(metadata_path):
            print(f"WARNING: No trained flow models found in {self.models_dir}/")
            return False

        # Load metadata
        with open(metadata_path, 'rb') as f:
            metadata = pickle.load(f)

        self.is_trained = metadata.get('is_trained', False)
        self.performance_metrics = metadata.get('performance_metrics', {})
        self.window_size = metadata.get('window_size', 20)
        self.forecast_horizon = metadata.get('forecast_horizon', 10)

        if metadata.get('last_train_date'):
            self.last_train_date = datetime.fromisoformat(metadata['last_train_date'])

        # Load scaler
        scaler_path = os.path.join(self.models_dir, 'scaler.pkl')
        if os.path.exists(scaler_path):
            with open(scaler_path, 'rb') as f:
                self.scaler = pickle.load(f)

        # Load models
        flow_path = os.path.join(self.models_dir, 'flow_classifier.pkl')
        if os.path.exists(flow_path):
            with open(flow_path, 'rb') as f:
                self.flow_classifier = pickle.load(f)

        vol_path = os.path.join(self.models_dir, 'volatility_predictor.pkl')
        if os.path.exists(vol_path):
            with open(vol_path, 'rb') as f:
                self.volatility_predictor = pickle.load(f)

        print(f"[OK] Flow prediction models loaded from {self.models_dir}/")
        if self.last_train_date:
            print(f"  Last trained: {self.last_train_date.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"  Flow classifier accuracy: {self.performance_metrics.get('flow_classifier', {}).get('accuracy', 0)*100:.1f}%")

        return True
