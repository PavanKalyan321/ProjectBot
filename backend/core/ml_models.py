"""
Real Machine Learning Models for Aviator Prediction
Trained on historical CSV data with proper feature engineering
"""

import os
import pickle
import numpy as np
import pandas as pd
from datetime import datetime
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split, cross_val_score
import warnings
warnings.filterwarnings('ignore')

# Try importing advanced ML libraries (optional dependencies)
try:
    import lightgbm as lgb
    LIGHTGBM_AVAILABLE = True
except ImportError:
    LIGHTGBM_AVAILABLE = False

try:
    from tensorflow import keras
    from tensorflow.keras.models import Sequential, load_model
    from tensorflow.keras.layers import LSTM, Dense, Dropout
    KERAS_AVAILABLE = True
except ImportError:
    KERAS_AVAILABLE = False


class AviatorMLModels:
    """
    Ensemble of trained ML models for multiplier prediction.
    Models: RandomForest, GradientBoosting, LightGBM (optional), LSTM (optional)
    """

    def __init__(self, models_dir='models'):
        """
        Initialize ML models.

        Args:
            models_dir: Directory to save/load trained models
        """
        self.models_dir = models_dir
        os.makedirs(models_dir, exist_ok=True)

        # Model instances
        self.random_forest = None
        self.gradient_boosting = None
        self.lightgbm = None
        self.lstm = None

        # Scaler for feature normalization
        self.scaler = StandardScaler()

        # Feature configuration
        self.sequence_length = 20
        self.feature_names = []

        # Model metadata
        self.is_trained = False
        self.last_train_date = None
        self.train_samples = 0
        self.model_scores = {}

    def engineer_features(self, df, target_column='multiplier'):
        """
        Create features from historical multiplier data.

        Args:
            df: DataFrame with 'multiplier' column
            target_column: Column to predict

        Returns:
            X (features), y (targets)
        """
        if df.empty or target_column not in df.columns:
            return None, None

        multipliers = df[target_column].values

        if len(multipliers) < self.sequence_length + 1:
            return None, None

        features = []
        targets = []

        for i in range(len(multipliers) - self.sequence_length):
            # Get sequence of past multipliers
            sequence = multipliers[i:i + self.sequence_length]

            # Feature 1-20: Past N multipliers
            feature_vector = list(sequence)

            # Feature 21: Mean of sequence
            feature_vector.append(np.mean(sequence))

            # Feature 22: Std deviation
            feature_vector.append(np.std(sequence))

            # Feature 23: Max in sequence
            feature_vector.append(np.max(sequence))

            # Feature 24: Min in sequence
            feature_vector.append(np.min(sequence))

            # Feature 25: Median
            feature_vector.append(np.median(sequence))

            # Feature 26-28: Recent trend (last 3 avg vs first 3 avg)
            recent_avg = np.mean(sequence[-3:])
            older_avg = np.mean(sequence[:3])
            feature_vector.append(recent_avg)
            feature_vector.append(older_avg)
            feature_vector.append(recent_avg - older_avg)

            # Feature 29: Count of low multipliers (<2.0)
            low_count = np.sum(sequence < 2.0)
            feature_vector.append(low_count)

            # Feature 30: Count of high multipliers (>=10.0)
            high_count = np.sum(sequence >= 10.0)
            feature_vector.append(high_count)

            # Feature 31: Volatility (range)
            feature_vector.append(np.max(sequence) - np.min(sequence))

            # Feature 32: Streak of increasing values
            increasing_streak = 0
            for j in range(1, len(sequence)):
                if sequence[j] > sequence[j-1]:
                    increasing_streak += 1
                else:
                    break
            feature_vector.append(increasing_streak)

            # Feature 33: Time since last high (>10x)
            time_since_high = 0
            for j in range(len(sequence)-1, -1, -1):
                if sequence[j] >= 10.0:
                    time_since_high = len(sequence) - 1 - j
                    break
            if time_since_high == 0:
                time_since_high = self.sequence_length
            feature_vector.append(time_since_high)

            # Feature 34-36: Percentiles (25th, 50th, 75th)
            feature_vector.append(np.percentile(sequence, 25))
            feature_vector.append(np.percentile(sequence, 50))
            feature_vector.append(np.percentile(sequence, 75))

            # Feature 37: Entropy (measure of randomness)
            # Binning multipliers to calculate entropy
            bins = [0, 1.5, 2.0, 3.0, 5.0, 10.0, 100.0]
            hist, _ = np.histogram(sequence, bins=bins)
            hist = hist / len(sequence)
            hist = hist[hist > 0]
            entropy = -np.sum(hist * np.log2(hist))
            feature_vector.append(entropy)

            features.append(feature_vector)
            targets.append(multipliers[i + self.sequence_length])

        X = np.array(features)
        y = np.array(targets)

        # Store feature names for reference
        if not self.feature_names:
            self.feature_names = (
                [f'mult_{i+1}' for i in range(self.sequence_length)] +
                ['mean', 'std', 'max', 'min', 'median',
                 'recent_avg', 'older_avg', 'trend',
                 'low_count', 'high_count', 'volatility', 'increasing_streak',
                 'time_since_high', 'p25', 'p50', 'p75', 'entropy']
            )

        return X, y

    def train_models(self, csv_file='aviator_rounds_history.csv', min_samples=100):
        """
        Train all available ML models on historical data.

        Args:
            csv_file: Path to CSV file with historical data
            min_samples: Minimum number of samples required for training

        Returns:
            bool: True if training successful
        """
        print(f"\n{'='*80}")
        print("TRAINING ML MODELS")
        print(f"{'='*80}")

        # Load data
        if not os.path.exists(csv_file):
            print(f"ERROR: CSV file not found: {csv_file}")
            return False

        # Try to load CSV with error handling
        try:
            df = pd.read_csv(csv_file)
            print(f"[OK] Loaded {len(df)} rounds from {csv_file}")
        except pd.errors.ParserError as e:
            print(f"\nERROR: CSV file is corrupted or has inconsistent columns")
            print(f"Details: {e}")
            print(f"\nTo fix this, run:")
            print(f"  python clean_csv.py")
            print(f"\nThis will clean the CSV file and create a backup.")
            return False
        except Exception as e:
            print(f"ERROR: Failed to read CSV file: {e}")
            return False

        # Clean data - remove NaN values
        df = df.dropna(subset=['multiplier'])
        df = df[df['multiplier'] > 0]  # Remove invalid multipliers
        print(f"[OK] After cleaning: {len(df)} valid rounds")

        # Engineer features
        X, y = self.engineer_features(df)

        if X is None or len(X) < min_samples:
            print(f"ERROR: Insufficient data. Need {min_samples} samples, have {len(X) if X is not None else 0}")
            return False

        print(f"[OK] Engineered {X.shape[1]} features from {len(X)} samples")

        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, shuffle=False
        )

        # Normalize features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)

        print(f"\nTraining Set: {len(X_train)} samples")
        print(f"Test Set: {len(X_test)} samples")
        print(f"\nTarget Range: {y.min():.2f}x - {y.max():.2f}x")
        print(f"Target Mean: {y.mean():.2f}x | Std: {y.std():.2f}x")

        # Train RandomForest
        print(f"\n{'-'*80}")
        print("1. Training Random Forest...")
        self.random_forest = RandomForestRegressor(
            n_estimators=100,
            max_depth=15,
            min_samples_split=5,
            min_samples_leaf=2,
            random_state=42,
            n_jobs=-1
        )
        self.random_forest.fit(X_train_scaled, y_train)
        rf_score = self.random_forest.score(X_test_scaled, y_test)
        self.model_scores['RandomForest'] = rf_score
        print(f"   [OK] R2 Score: {rf_score:.4f}")

        # Train GradientBoosting
        print(f"\n2. Training Gradient Boosting...")
        self.gradient_boosting = GradientBoostingRegressor(
            n_estimators=100,
            learning_rate=0.1,
            max_depth=7,
            min_samples_split=5,
            random_state=42
        )
        self.gradient_boosting.fit(X_train_scaled, y_train)
        gb_score = self.gradient_boosting.score(X_test_scaled, y_test)
        self.model_scores['GradientBoosting'] = gb_score
        print(f"   [OK] R2 Score: {gb_score:.4f}")

        # Train LightGBM if available
        if LIGHTGBM_AVAILABLE:
            print(f"\n3. Training LightGBM...")
            self.lightgbm = lgb.LGBMRegressor(
                n_estimators=100,
                learning_rate=0.1,
                max_depth=7,
                num_leaves=31,
                random_state=42,
                verbose=-1
            )
            self.lightgbm.fit(X_train_scaled, y_train)
            lgb_score = self.lightgbm.score(X_test_scaled, y_test)
            self.model_scores['LightGBM'] = lgb_score
            print(f"   [OK] R2 Score: {lgb_score:.4f}")
        else:
            print(f"\n3. LightGBM not available (install: pip install lightgbm)")

        # Train LSTM if available
        if KERAS_AVAILABLE:
            print(f"\n4. Training LSTM...")
            # Reshape for LSTM (samples, timesteps, features)
            X_train_lstm = X_train_scaled.reshape((X_train_scaled.shape[0], 1, X_train_scaled.shape[1]))
            X_test_lstm = X_test_scaled.reshape((X_test_scaled.shape[0], 1, X_test_scaled.shape[1]))

            self.lstm = Sequential([
                LSTM(64, activation='relu', input_shape=(1, X_train_scaled.shape[1]), return_sequences=True),
                Dropout(0.2),
                LSTM(32, activation='relu'),
                Dropout(0.2),
                Dense(16, activation='relu'),
                Dense(1)
            ])

            self.lstm.compile(optimizer='adam', loss='mse', metrics=['mae'])
            self.lstm.fit(
                X_train_lstm, y_train,
                epochs=50,
                batch_size=32,
                validation_split=0.1,
                verbose=0
            )

            lstm_score = self.lstm.evaluate(X_test_lstm, y_test, verbose=0)[0]
            self.model_scores['LSTM'] = 1 - (lstm_score / np.var(y_test))  # Approximate R²
            print(f"   [OK] R2 Score: {self.model_scores['LSTM']:.4f}")
        else:
            print(f"\n4. LSTM not available (install: pip install tensorflow)")

        # Update metadata
        self.is_trained = True
        self.last_train_date = datetime.now()
        self.train_samples = len(X)

        # Save models
        self.save_models()

        print(f"\n{'='*80}")
        print("MODEL TRAINING COMPLETE")
        print(f"{'='*80}")
        print(f"Model Performance Summary:")
        for name, score in self.model_scores.items():
            print(f"   {name:20s}: R2 = {score:.4f}")
        print(f"{'='*80}\n")

        return True

    def predict(self, recent_multipliers):
        """
        Generate ensemble predictions from all trained models.

        Args:
            recent_multipliers: List of recent multipliers (length = sequence_length)

        Returns:
            dict: Predictions from each model with metadata
        """
        if not self.is_trained:
            # Return placeholder if not trained
            return self._generate_placeholder_predictions()

        if len(recent_multipliers) < self.sequence_length:
            return self._generate_placeholder_predictions()

        # Prepare features
        sequence = recent_multipliers[-self.sequence_length:]
        features, _ = self.engineer_features(
            pd.DataFrame({'multiplier': sequence + [0]})
        )

        if features is None:
            return self._generate_placeholder_predictions()

        # Get last feature vector
        X = features[-1].reshape(1, -1)
        X_scaled = self.scaler.transform(X)

        predictions = []

        # RandomForest prediction
        if self.random_forest is not None:
            rf_pred = self.random_forest.predict(X_scaled)[0]
            rf_conf = self._calculate_confidence(rf_pred, 'RandomForest')
            predictions.append({
                'model_id': 'RandomForest',
                'prediction': max(1.0, float(rf_pred)),
                'confidence': float(rf_conf)
            })

        # GradientBoosting prediction
        if self.gradient_boosting is not None:
            gb_pred = self.gradient_boosting.predict(X_scaled)[0]
            gb_conf = self._calculate_confidence(gb_pred, 'GradientBoosting')
            predictions.append({
                'model_id': 'GradientBoosting',
                'prediction': max(1.0, float(gb_pred)),
                'confidence': float(gb_conf)
            })

        # LightGBM prediction
        if self.lightgbm is not None:
            lgb_pred = self.lightgbm.predict(X_scaled)[0]
            lgb_conf = self._calculate_confidence(lgb_pred, 'LightGBM')
            predictions.append({
                'model_id': 'LightGBM',
                'prediction': max(1.0, float(lgb_pred)),
                'confidence': float(lgb_conf)
            })

        # LSTM prediction
        if self.lstm is not None:
            X_lstm = X_scaled.reshape((1, 1, X_scaled.shape[1]))
            lstm_pred = self.lstm.predict(X_lstm, verbose=0)[0][0]
            lstm_conf = self._calculate_confidence(lstm_pred, 'LSTM')
            predictions.append({
                'model_id': 'LSTM',
                'prediction': max(1.0, float(lstm_pred)),
                'confidence': float(lstm_conf)
            })

        return predictions

    def _calculate_confidence(self, prediction, model_name):
        """
        Calculate confidence score based on model performance and prediction.

        Args:
            prediction: Predicted value
            model_name: Name of the model

        Returns:
            float: Confidence score (0-100)
        """
        # Base confidence from model R² score
        base_confidence = self.model_scores.get(model_name, 0.5) * 100

        # Adjust based on prediction range
        if 1.5 <= prediction <= 3.0:
            # High confidence for common range
            adjustment = 10
        elif 3.0 < prediction <= 5.0:
            # Medium confidence
            adjustment = 5
        elif prediction > 10.0:
            # Lower confidence for high predictions
            adjustment = -10
        else:
            # Very low predictions
            adjustment = -5

        confidence = base_confidence + adjustment
        return max(40.0, min(95.0, confidence))

    def _generate_placeholder_predictions(self):
        """Generate placeholder predictions when models not trained."""
        # Return cautious predictions
        return [
            {'model_id': 'RandomForest', 'prediction': 2.0, 'confidence': 50.0},
            {'model_id': 'GradientBoosting', 'prediction': 2.2, 'confidence': 50.0},
            {'model_id': 'LightGBM', 'prediction': 2.1, 'confidence': 50.0},
            {'model_id': 'LSTM', 'prediction': 2.0, 'confidence': 50.0}
        ]

    def save_models(self):
        """Save all trained models to disk."""
        if not self.is_trained:
            return

        # Save sklearn models
        if self.random_forest is not None:
            with open(os.path.join(self.models_dir, 'random_forest.pkl'), 'wb') as f:
                pickle.dump(self.random_forest, f)

        if self.gradient_boosting is not None:
            with open(os.path.join(self.models_dir, 'gradient_boosting.pkl'), 'wb') as f:
                pickle.dump(self.gradient_boosting, f)

        if self.lightgbm is not None:
            with open(os.path.join(self.models_dir, 'lightgbm.pkl'), 'wb') as f:
                pickle.dump(self.lightgbm, f)

        # Save scaler
        with open(os.path.join(self.models_dir, 'scaler.pkl'), 'wb') as f:
            pickle.dump(self.scaler, f)

        # Save LSTM separately
        if self.lstm is not None:
            self.lstm.save(os.path.join(self.models_dir, 'lstm_model.h5'))

        # Save metadata
        metadata = {
            'is_trained': self.is_trained,
            'last_train_date': self.last_train_date.isoformat() if self.last_train_date else None,
            'train_samples': self.train_samples,
            'model_scores': self.model_scores,
            'sequence_length': self.sequence_length,
            'feature_names': self.feature_names
        }
        with open(os.path.join(self.models_dir, 'metadata.pkl'), 'wb') as f:
            pickle.dump(metadata, f)

        print(f"[OK] Models saved to {self.models_dir}/")

    def load_models(self):
        """Load trained models from disk."""
        metadata_path = os.path.join(self.models_dir, 'metadata.pkl')
        if not os.path.exists(metadata_path):
            print(f"WARNING: No trained models found in {self.models_dir}/")
            return False

        # Load metadata
        with open(metadata_path, 'rb') as f:
            metadata = pickle.load(f)

        self.is_trained = metadata.get('is_trained', False)
        self.train_samples = metadata.get('train_samples', 0)
        self.model_scores = metadata.get('model_scores', {})
        self.sequence_length = metadata.get('sequence_length', 20)
        self.feature_names = metadata.get('feature_names', [])

        if metadata.get('last_train_date'):
            self.last_train_date = datetime.fromisoformat(metadata['last_train_date'])

        # Load scaler
        scaler_path = os.path.join(self.models_dir, 'scaler.pkl')
        if os.path.exists(scaler_path):
            with open(scaler_path, 'rb') as f:
                self.scaler = pickle.load(f)

        # Load sklearn models
        rf_path = os.path.join(self.models_dir, 'random_forest.pkl')
        if os.path.exists(rf_path):
            with open(rf_path, 'rb') as f:
                self.random_forest = pickle.load(f)

        gb_path = os.path.join(self.models_dir, 'gradient_boosting.pkl')
        if os.path.exists(gb_path):
            with open(gb_path, 'rb') as f:
                self.gradient_boosting = pickle.load(f)

        lgb_path = os.path.join(self.models_dir, 'lightgbm.pkl')
        if os.path.exists(lgb_path):
            with open(lgb_path, 'rb') as f:
                self.lightgbm = pickle.load(f)

        # Load LSTM
        lstm_path = os.path.join(self.models_dir, 'lstm_model.h5')
        if os.path.exists(lstm_path) and KERAS_AVAILABLE:
            self.lstm = load_model(lstm_path)

        print(f"[OK] Models loaded from {self.models_dir}/")
        print(f"  Trained on {self.train_samples} samples")
        if self.last_train_date:
            print(f"  Last trained: {self.last_train_date.strftime('%Y-%m-%d %H:%M:%S')}")

        return True
