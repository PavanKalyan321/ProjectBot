"""
Advanced ML Ensemble with 30 Diverse Models for Aviator Prediction
Combines multiple algorithms, hyperparameters, and architectures
"""

import os
import pickle
import numpy as np
import pandas as pd
from datetime import datetime
from sklearn.ensemble import (
    RandomForestRegressor, GradientBoostingRegressor,
    AdaBoostRegressor, ExtraTreesRegressor, BaggingRegressor
)
from sklearn.linear_model import Ridge, Lasso, ElasticNet, BayesianRidge
from sklearn.svm import SVR
from sklearn.neighbors import KNeighborsRegressor
from sklearn.tree import DecisionTreeRegressor
from sklearn.neural_network import MLPRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
import warnings
warnings.filterwarnings('ignore')

# Try importing advanced ML libraries
try:
    import lightgbm as lgb
    LIGHTGBM_AVAILABLE = True
except ImportError:
    LIGHTGBM_AVAILABLE = False

try:
    import xgboost as xgb
    XGBOOST_AVAILABLE = True
except ImportError:
    XGBOOST_AVAILABLE = False

try:
    from catboost import CatBoostRegressor
    CATBOOST_AVAILABLE = True
except ImportError:
    CATBOOST_AVAILABLE = False

try:
    from tensorflow import keras
    from tensorflow.keras.models import Sequential, load_model
    from tensorflow.keras.layers import LSTM, Dense, Dropout, GRU, Bidirectional
    KERAS_AVAILABLE = True
except ImportError:
    KERAS_AVAILABLE = False


class AdvancedMLEnsemble:
    """
    Ensemble of 30 diverse ML models for robust predictions.
    Each model has unique characteristics and hyperparameters.
    """

    def __init__(self, models_dir='models/advanced_ensemble'):
        """Initialize 30-model ensemble."""
        self.models_dir = models_dir
        os.makedirs(models_dir, exist_ok=True)

        # Model storage
        self.models = {}  # {model_id: model_instance}
        self.model_configs = self._define_model_configs()

        # Scaler for feature normalization
        self.scaler = StandardScaler()

        # Feature configuration
        self.sequence_length = 20
        self.feature_names = []

        # Metadata
        self.is_trained = False
        self.last_train_date = None
        self.train_samples = 0
        self.model_scores = {}  # {model_id: {'mae': x, 'rmse': y, 'r2': z}}

    def _define_model_configs(self):
        """Define configurations for all 30 models."""
        configs = []

        # 1-5: Random Forest Variations (different depths and estimators)
        configs.append({'id': 'RF_Deep', 'type': 'rf', 'params': {'n_estimators': 150, 'max_depth': 20, 'min_samples_split': 3}})
        configs.append({'id': 'RF_Wide', 'type': 'rf', 'params': {'n_estimators': 200, 'max_depth': 10, 'min_samples_split': 5}})
        configs.append({'id': 'RF_Balanced', 'type': 'rf', 'params': {'n_estimators': 100, 'max_depth': 15, 'min_samples_split': 4}})
        configs.append({'id': 'RF_Conservative', 'type': 'rf', 'params': {'n_estimators': 80, 'max_depth': 8, 'min_samples_split': 10}})
        configs.append({'id': 'RF_Aggressive', 'type': 'rf', 'params': {'n_estimators': 120, 'max_depth': 25, 'min_samples_split': 2}})

        # 6-10: Gradient Boosting Variations
        configs.append({'id': 'GB_Fast', 'type': 'gb', 'params': {'n_estimators': 80, 'learning_rate': 0.15, 'max_depth': 5}})
        configs.append({'id': 'GB_Accurate', 'type': 'gb', 'params': {'n_estimators': 150, 'learning_rate': 0.05, 'max_depth': 7}})
        configs.append({'id': 'GB_Balanced', 'type': 'gb', 'params': {'n_estimators': 100, 'learning_rate': 0.1, 'max_depth': 6}})
        configs.append({'id': 'GB_Deep', 'type': 'gb', 'params': {'n_estimators': 120, 'learning_rate': 0.08, 'max_depth': 10}})
        configs.append({'id': 'GB_Robust', 'type': 'gb', 'params': {'n_estimators': 90, 'learning_rate': 0.12, 'max_depth': 4}})

        # 11-13: XGBoost Variations (if available)
        configs.append({'id': 'XGB_Standard', 'type': 'xgb', 'params': {'n_estimators': 100, 'learning_rate': 0.1, 'max_depth': 6}})
        configs.append({'id': 'XGB_Deep', 'type': 'xgb', 'params': {'n_estimators': 150, 'learning_rate': 0.05, 'max_depth': 9}})
        configs.append({'id': 'XGB_Fast', 'type': 'xgb', 'params': {'n_estimators': 80, 'learning_rate': 0.15, 'max_depth': 4}})

        # 14-16: LightGBM Variations (if available)
        configs.append({'id': 'LGBM_Standard', 'type': 'lgbm', 'params': {'n_estimators': 100, 'learning_rate': 0.1, 'max_depth': 7, 'num_leaves': 31}})
        configs.append({'id': 'LGBM_Aggressive', 'type': 'lgbm', 'params': {'n_estimators': 150, 'learning_rate': 0.08, 'max_depth': 10, 'num_leaves': 50}})
        configs.append({'id': 'LGBM_Conservative', 'type': 'lgbm', 'params': {'n_estimators': 80, 'learning_rate': 0.12, 'max_depth': 5, 'num_leaves': 20}})

        # 17-18: CatBoost Variations (if available)
        configs.append({'id': 'CAT_Standard', 'type': 'catboost', 'params': {'iterations': 100, 'learning_rate': 0.1, 'depth': 6}})
        configs.append({'id': 'CAT_Deep', 'type': 'catboost', 'params': {'iterations': 150, 'learning_rate': 0.05, 'depth': 8}})

        # 19-21: Extra Trees Variations
        configs.append({'id': 'ET_Standard', 'type': 'et', 'params': {'n_estimators': 100, 'max_depth': 15}})
        configs.append({'id': 'ET_Deep', 'type': 'et', 'params': {'n_estimators': 120, 'max_depth': 20}})
        configs.append({'id': 'ET_Wide', 'type': 'et', 'params': {'n_estimators': 150, 'max_depth': 12}})

        # 22-24: Neural Networks (MLP Variations)
        configs.append({'id': 'NN_Small', 'type': 'nn', 'params': {'hidden_layer_sizes': (50, 25), 'learning_rate_init': 0.001}})
        configs.append({'id': 'NN_Medium', 'type': 'nn', 'params': {'hidden_layer_sizes': (100, 50, 25), 'learning_rate_init': 0.001}})
        configs.append({'id': 'NN_Large', 'type': 'nn', 'params': {'hidden_layer_sizes': (150, 100, 50), 'learning_rate_init': 0.0005}})

        # 25-26: LSTM Variations (if available)
        configs.append({'id': 'LSTM_Standard', 'type': 'lstm', 'params': {'units': [64, 32], 'dropout': 0.2}})
        configs.append({'id': 'LSTM_Deep', 'type': 'lstm', 'params': {'units': [128, 64, 32], 'dropout': 0.3}})

        # 27-28: GRU Variations (if available)
        configs.append({'id': 'GRU_Standard', 'type': 'gru', 'params': {'units': [64, 32], 'dropout': 0.2}})
        configs.append({'id': 'GRU_Bidirectional', 'type': 'gru_bi', 'params': {'units': [64], 'dropout': 0.2}})

        # 29-30: Ensemble Methods
        configs.append({'id': 'AdaBoost_Standard', 'type': 'adaboost', 'params': {'n_estimators': 100, 'learning_rate': 0.8}})
        configs.append({'id': 'Bagging_Standard', 'type': 'bagging', 'params': {'n_estimators': 50, 'max_samples': 0.8}})

        return configs

    def engineer_features(self, df, target_column='multiplier'):
        """
        Create advanced features from historical multiplier data.
        Same feature engineering as base models for consistency.
        """
        if df.empty or target_column not in df.columns:
            return None, None, None

        multipliers = df[target_column].values
        has_weights = 'sample_weight' in df.columns
        weights = df['sample_weight'].values if has_weights else None

        if len(multipliers) < self.sequence_length + 1:
            return None, None, None

        features = []
        targets = []
        sample_weights = [] if has_weights else None

        for i in range(len(multipliers) - self.sequence_length):
            sequence = multipliers[i:i + self.sequence_length]
            feature_vector = list(sequence)

            # Statistical features
            feature_vector.extend([
                np.mean(sequence),
                np.std(sequence),
                np.max(sequence),
                np.min(sequence),
                np.median(sequence)
            ])

            # Trend features
            recent_avg = np.mean(sequence[-3:])
            older_avg = np.mean(sequence[:3])
            feature_vector.extend([recent_avg, older_avg, recent_avg - older_avg])

            # Count features
            feature_vector.extend([
                np.sum(sequence < 2.0),  # Low count
                np.sum(sequence >= 10.0),  # High count
                np.max(sequence) - np.min(sequence)  # Volatility
            ])

            # Streak features
            increasing_streak = 0
            for j in range(1, len(sequence)):
                if sequence[j] > sequence[j-1]:
                    increasing_streak += 1
                else:
                    break
            feature_vector.append(increasing_streak)

            # Time since events
            time_since_high = self.sequence_length
            for j in range(len(sequence)-1, -1, -1):
                if sequence[j] >= 10.0:
                    time_since_high = len(sequence) - 1 - j
                    break
            feature_vector.append(time_since_high)

            # Percentiles
            feature_vector.extend([
                np.percentile(sequence, 25),
                np.percentile(sequence, 50),
                np.percentile(sequence, 75)
            ])

            # Entropy
            bins = [0, 1.5, 2.0, 3.0, 5.0, 10.0, 100.0]
            hist, _ = np.histogram(sequence, bins=bins)
            hist = hist / len(sequence)
            hist = hist[hist > 0]
            entropy = -np.sum(hist * np.log2(hist)) if len(hist) > 0 else 0
            feature_vector.append(entropy)

            # Advanced features
            from scipy.stats import skew, kurtosis
            feature_vector.extend([skew(sequence), kurtosis(sequence)])

            # Moving averages
            ma_5 = np.mean(sequence[-5:]) if len(sequence) >= 5 else np.mean(sequence)
            ma_10 = np.mean(sequence[-10:]) if len(sequence) >= 10 else np.mean(sequence)
            feature_vector.extend([ma_5, ma_10, ma_5 - ma_10])

            # IQR and CV
            q25, q75 = np.percentile(sequence, [25, 75])
            iqr = q75 - q25
            cv = np.std(sequence) / np.mean(sequence) if np.mean(sequence) > 0 else 0
            feature_vector.extend([iqr, cv])

            # More time-based features
            rounds_since_5x = self.sequence_length
            rounds_since_3x = self.sequence_length
            for j in range(len(sequence)-1, -1, -1):
                if sequence[j] >= 5.0 and rounds_since_5x == self.sequence_length:
                    rounds_since_5x = len(sequence) - 1 - j
                if sequence[j] >= 3.0 and rounds_since_3x == self.sequence_length:
                    rounds_since_3x = len(sequence) - 1 - j
            feature_vector.extend([rounds_since_5x, rounds_since_3x])

            # Streak features
            current_low_streak = 0
            for j in range(len(sequence)-1, -1, -1):
                if sequence[j] < 2.0:
                    current_low_streak += 1
                else:
                    break

            max_low_streak = 0
            temp_streak = 0
            for val in sequence:
                if val < 2.0:
                    temp_streak += 1
                    max_low_streak = max(max_low_streak, temp_streak)
                else:
                    temp_streak = 0

            feature_vector.extend([current_low_streak, max_low_streak])

            # Pattern features
            alternations = 0
            for j in range(1, len(sequence)):
                if (sequence[j] >= 2.0 and sequence[j-1] < 2.0) or \
                   (sequence[j] < 2.0 and sequence[j-1] >= 2.0):
                    alternations += 1
            feature_vector.append(alternations)

            # Ratio features
            high_count_3x = np.sum(sequence >= 3.0)
            low_count_15x = np.sum(sequence < 1.5)
            ratio = high_count_3x / (low_count_15x + 1)
            feature_vector.append(ratio)

            features.append(feature_vector)
            targets.append(multipliers[i + self.sequence_length])

            if has_weights:
                sample_weights.append(weights[i + self.sequence_length])

        X = np.array(features)
        y = np.array(targets)
        if sample_weights is not None:
            sample_weights = np.array(sample_weights)

        # Handle NaN values
        nan_mask = np.isnan(X)
        if np.any(nan_mask):
            col_mean = np.nanmean(X, axis=0)
            inds = np.where(nan_mask)
            X[inds] = np.take(col_mean, inds[1])

        # Store feature names
        if not self.feature_names:
            self.feature_names = (
                [f'mult_{i+1}' for i in range(self.sequence_length)] +
                ['mean', 'std', 'max', 'min', 'median',
                 'recent_avg', 'older_avg', 'trend',
                 'low_count', 'high_count', 'volatility', 'increasing_streak',
                 'time_since_high', 'p25', 'p50', 'p75', 'entropy',
                 'skewness', 'kurtosis', 'ma_5', 'ma_10', 'ma_crossover',
                 'iqr', 'coef_variation', 'rounds_since_5x', 'rounds_since_3x',
                 'current_low_streak', 'max_low_streak', 'alternations', 'high_low_ratio']
            )

        return X, y, sample_weights

    def _create_model(self, config):
        """Create a model instance based on configuration."""
        model_type = config['type']
        params = config['params']

        try:
            if model_type == 'rf':
                return RandomForestRegressor(
                    n_estimators=params['n_estimators'],
                    max_depth=params['max_depth'],
                    min_samples_split=params['min_samples_split'],
                    random_state=42,
                    n_jobs=-1
                )

            elif model_type == 'gb':
                return GradientBoostingRegressor(
                    n_estimators=params['n_estimators'],
                    learning_rate=params['learning_rate'],
                    max_depth=params['max_depth'],
                    random_state=42
                )

            elif model_type == 'xgb' and XGBOOST_AVAILABLE:
                return xgb.XGBRegressor(
                    n_estimators=params['n_estimators'],
                    learning_rate=params['learning_rate'],
                    max_depth=params['max_depth'],
                    random_state=42,
                    n_jobs=-1
                )

            elif model_type == 'lgbm' and LIGHTGBM_AVAILABLE:
                return lgb.LGBMRegressor(
                    n_estimators=params['n_estimators'],
                    learning_rate=params['learning_rate'],
                    max_depth=params['max_depth'],
                    num_leaves=params['num_leaves'],
                    random_state=42,
                    verbose=-1
                )

            elif model_type == 'catboost' and CATBOOST_AVAILABLE:
                return CatBoostRegressor(
                    iterations=params['iterations'],
                    learning_rate=params['learning_rate'],
                    depth=params['depth'],
                    random_state=42,
                    verbose=0
                )

            elif model_type == 'et':
                return ExtraTreesRegressor(
                    n_estimators=params['n_estimators'],
                    max_depth=params['max_depth'],
                    random_state=42,
                    n_jobs=-1
                )

            elif model_type == 'nn':
                return MLPRegressor(
                    hidden_layer_sizes=params['hidden_layer_sizes'],
                    learning_rate_init=params['learning_rate_init'],
                    max_iter=500,
                    random_state=42,
                    early_stopping=True
                )

            elif model_type == 'adaboost':
                return AdaBoostRegressor(
                    n_estimators=params['n_estimators'],
                    learning_rate=params['learning_rate'],
                    random_state=42
                )

            elif model_type == 'bagging':
                base_estimator = DecisionTreeRegressor(max_depth=10, random_state=42)
                return BaggingRegressor(
                    base_estimator=base_estimator,
                    n_estimators=params['n_estimators'],
                    max_samples=params['max_samples'],
                    random_state=42,
                    n_jobs=-1
                )

            elif model_type in ['lstm', 'gru', 'gru_bi'] and KERAS_AVAILABLE:
                # Return config for later neural network construction
                return {'type': model_type, 'params': params, 'needs_reshape': True}

            else:
                return None

        except Exception as e:
            print(f"Error creating model {config['id']}: {e}")
            return None

    def _create_keras_model(self, model_type, params, input_shape):
        """Create Keras models (LSTM, GRU, etc.)."""
        if model_type == 'lstm':
            model = Sequential()
            units = params['units']
            dropout = params['dropout']

            for i, unit_count in enumerate(units):
                if i == 0:
                    model.add(LSTM(unit_count, activation='relu', return_sequences=(i < len(units)-1), input_shape=input_shape))
                else:
                    model.add(LSTM(unit_count, activation='relu', return_sequences=(i < len(units)-1)))
                model.add(Dropout(dropout))

            model.add(Dense(16, activation='relu'))
            model.add(Dense(1))
            model.compile(optimizer='adam', loss='mse', metrics=['mae'])
            return model

        elif model_type == 'gru':
            model = Sequential()
            units = params['units']
            dropout = params['dropout']

            for i, unit_count in enumerate(units):
                if i == 0:
                    model.add(GRU(unit_count, activation='relu', return_sequences=(i < len(units)-1), input_shape=input_shape))
                else:
                    model.add(GRU(unit_count, activation='relu', return_sequences=(i < len(units)-1)))
                model.add(Dropout(dropout))

            model.add(Dense(16, activation='relu'))
            model.add(Dense(1))
            model.compile(optimizer='adam', loss='mse', metrics=['mae'])
            return model

        elif model_type == 'gru_bi':
            model = Sequential()
            units = params['units']
            dropout = params['dropout']

            for i, unit_count in enumerate(units):
                if i == 0:
                    model.add(Bidirectional(GRU(unit_count, activation='relu', return_sequences=(i < len(units)-1)), input_shape=input_shape))
                else:
                    model.add(Bidirectional(GRU(unit_count, activation='relu', return_sequences=(i < len(units)-1))))
                model.add(Dropout(dropout))

            model.add(Dense(16, activation='relu'))
            model.add(Dense(1))
            model.compile(optimizer='adam', loss='mse', metrics=['mae'])
            return model

        return None

    def train_all_models(self, csv_file='aviator_rounds_history.csv', min_samples=100):
        """Train all 30 models on historical data."""
        print(f"\n{'='*80}")
        print("TRAINING 30-MODEL ADVANCED ENSEMBLE")
        print(f"{'='*80}")

        # Load and prepare data
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

        # Cap outliers
        cap_value = df['multiplier'].quantile(0.99)
        df.loc[df['multiplier'] > cap_value, 'multiplier'] = cap_value
        print(f"[OK] Capped outliers at {cap_value:.2f}x")

        # Time-based weighting
        if 'timestamp' in df.columns:
            try:
                df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
                df = df.dropna(subset=['timestamp'])
                now = datetime.now()
                df['age_hours'] = (now - df['timestamp']).dt.total_seconds() / 3600
                df['sample_weight'] = np.exp(-df['age_hours'] / 24.0)
                print(f"[OK] Applied time-based weighting")
            except:
                df['sample_weight'] = 1.0
        else:
            df['sample_weight'] = 1.0

        # Engineer features
        X, y, sample_weights = self.engineer_features(df)

        if X is None or len(X) < min_samples:
            print(f"ERROR: Insufficient data. Need {min_samples}, have {len(X) if X is not None else 0}")
            return False

        print(f"[OK] Engineered {X.shape[1]} features from {len(X)} samples")

        # Split data
        if sample_weights is not None:
            X_train, X_test, y_train, y_test, w_train, w_test = train_test_split(
                X, y, sample_weights, test_size=0.2, random_state=42, shuffle=False
            )
        else:
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42, shuffle=False
            )
            w_train, w_test = None, None

        # Normalize features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)

        print(f"\nTraining Set: {len(X_train)} | Test Set: {len(X_test)}")
        print(f"Target Range: {y.min():.2f}x - {y.max():.2f}x (Mean: {y.mean():.2f}x)")

        # Train each model
        print(f"\n{'='*80}")
        print(f"Training 30 Models...")
        print(f"{'='*80}\n")

        trained_count = 0
        for i, config in enumerate(self.model_configs, 1):
            model_id = config['id']
            print(f"{i:2d}. Training {model_id:25s}...", end=" ")

            try:
                model = self._create_model(config)

                if model is None:
                    print(f"[SKIP] Library not available")
                    continue

                # Handle Keras models separately
                if isinstance(model, dict) and model.get('needs_reshape'):
                    if not KERAS_AVAILABLE:
                        print(f"[SKIP] Keras not available")
                        continue

                    X_train_reshaped = X_train_scaled.reshape((X_train_scaled.shape[0], 1, X_train_scaled.shape[1]))
                    X_test_reshaped = X_test_scaled.reshape((X_test_scaled.shape[0], 1, X_test_scaled.shape[1]))

                    keras_model = self._create_keras_model(
                        model['type'],
                        model['params'],
                        (1, X_train_scaled.shape[1])
                    )

                    keras_model.fit(
                        X_train_reshaped, y_train,
                        sample_weight=w_train,
                        epochs=50,
                        batch_size=32,
                        validation_split=0.1,
                        verbose=0
                    )

                    y_pred = keras_model.predict(X_test_reshaped, verbose=0).flatten()
                    self.models[model_id] = keras_model

                else:
                    # Standard sklearn models
                    model.fit(X_train_scaled, y_train, sample_weight=w_train)
                    y_pred = model.predict(X_test_scaled)
                    self.models[model_id] = model

                # Calculate metrics
                mae = np.mean(np.abs(y_test - y_pred))
                rmse = np.sqrt(np.mean((y_test - y_pred) ** 2))
                r2 = 1 - (np.sum((y_test - y_pred) ** 2) / np.sum((y_test - y.mean()) ** 2))

                self.model_scores[model_id] = {
                    'mae': float(mae),
                    'rmse': float(rmse),
                    'r2': float(r2)
                }

                print(f"[OK] MAE: {mae:.3f} | R²: {r2:.4f}")
                trained_count += 1

            except Exception as e:
                print(f"[ERROR] {str(e)[:50]}")

        # Update metadata
        self.is_trained = True
        self.last_train_date = datetime.now()
        self.train_samples = len(X)

        print(f"\n{'='*80}")
        print(f"TRAINING COMPLETE: {trained_count}/30 models trained successfully")
        print(f"{'='*80}\n")

        # Show top 5 models
        sorted_models = sorted(self.model_scores.items(), key=lambda x: x[1]['mae'])
        print("Top 5 Best Performing Models:")
        for i, (model_id, scores) in enumerate(sorted_models[:5], 1):
            print(f"  {i}. {model_id:25s} - MAE: {scores['mae']:.3f}, R²: {scores['r2']:.4f}")

        print(f"\n{'='*80}\n")

        # Save models
        self.save_all_models()

        return True

    def predict_all(self, recent_multipliers):
        """Generate predictions from all 30 models."""
        if not self.is_trained or len(recent_multipliers) < self.sequence_length:
            return self._generate_placeholder_predictions()

        # Prepare features
        sequence = recent_multipliers[-self.sequence_length:]
        features, _, _ = self.engineer_features(
            pd.DataFrame({'multiplier': sequence + [0]})
        )

        if features is None:
            return self._generate_placeholder_predictions()

        X = features[-1].reshape(1, -1)
        X_scaled = self.scaler.transform(X)

        predictions = []

        for model_id, model in self.models.items():
            try:
                # Check if it's a Keras model
                if hasattr(model, 'predict') and 'Sequential' in str(type(model)):
                    X_reshaped = X_scaled.reshape((1, 1, X_scaled.shape[1]))
                    pred = model.predict(X_reshaped, verbose=0)[0][0]
                else:
                    pred = model.predict(X_scaled)[0]

                scores = self.model_scores.get(model_id, {})
                confidence = self._calculate_confidence(pred, scores)

                predictions.append({
                    'model_id': model_id,
                    'prediction': max(1.0, float(pred)),
                    'confidence': float(confidence),
                    'mae': float(scores.get('mae', 0)),
                    'r2': float(scores.get('r2', 0))
                })
            except Exception as e:
                print(f"Error predicting with {model_id}: {e}")

        return predictions

    def _calculate_confidence(self, prediction, scores):
        """Calculate confidence based on model performance and prediction."""
        base_confidence = max(0, min(100, scores.get('r2', 0.5) * 100))

        # Adjust based on prediction range
        if 1.5 <= prediction <= 3.0:
            adjustment = 10
        elif 3.0 < prediction <= 5.0:
            adjustment = 5
        elif prediction > 10.0:
            adjustment = -10
        else:
            adjustment = -5

        confidence = base_confidence + adjustment
        return max(40.0, min(95.0, confidence))

    def _generate_placeholder_predictions(self):
        """Generate placeholder predictions when not trained."""
        return [{'model_id': f'Model_{i}', 'prediction': 2.0, 'confidence': 50.0, 'mae': 0, 'r2': 0} for i in range(1, 31)]

    def save_all_models(self):
        """Save all trained models to disk."""
        if not self.is_trained:
            return

        # Save sklearn models
        sklearn_models = {}
        keras_models_info = {}

        for model_id, model in self.models.items():
            if hasattr(model, 'predict') and 'Sequential' in str(type(model)):
                # Keras model - save separately
                model.save(os.path.join(self.models_dir, f'{model_id}.h5'))
                keras_models_info[model_id] = 'keras'
            else:
                # sklearn model
                sklearn_models[model_id] = model

        # Save sklearn models
        if sklearn_models:
            with open(os.path.join(self.models_dir, 'sklearn_models.pkl'), 'wb') as f:
                pickle.dump(sklearn_models, f)

        # Save scaler
        with open(os.path.join(self.models_dir, 'scaler.pkl'), 'wb') as f:
            pickle.dump(self.scaler, f)

        # Save metadata
        metadata = {
            'is_trained': self.is_trained,
            'last_train_date': self.last_train_date.isoformat() if self.last_train_date else None,
            'train_samples': self.train_samples,
            'model_scores': self.model_scores,
            'model_configs': self.model_configs,
            'keras_models': keras_models_info,
            'sequence_length': self.sequence_length,
            'feature_names': self.feature_names
        }
        with open(os.path.join(self.models_dir, 'metadata.pkl'), 'wb') as f:
            pickle.dump(metadata, f)

        print(f"[OK] All models saved to {self.models_dir}/")

    def load_all_models(self):
        """Load all trained models from disk."""
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
        self.model_configs = metadata.get('model_configs', self.model_configs)
        self.sequence_length = metadata.get('sequence_length', 20)
        self.feature_names = metadata.get('feature_names', [])
        keras_models_info = metadata.get('keras_models', {})

        if metadata.get('last_train_date'):
            self.last_train_date = datetime.fromisoformat(metadata['last_train_date'])

        # Load scaler
        scaler_path = os.path.join(self.models_dir, 'scaler.pkl')
        if os.path.exists(scaler_path):
            with open(scaler_path, 'rb') as f:
                self.scaler = pickle.load(f)

        # Load sklearn models
        sklearn_path = os.path.join(self.models_dir, 'sklearn_models.pkl')
        if os.path.exists(sklearn_path):
            with open(sklearn_path, 'rb') as f:
                sklearn_models = pickle.load(f)
                self.models.update(sklearn_models)

        # Load Keras models
        if KERAS_AVAILABLE:
            for model_id in keras_models_info.keys():
                model_path = os.path.join(self.models_dir, f'{model_id}.h5')
                if os.path.exists(model_path):
                    self.models[model_id] = load_model(model_path)

        print(f"[OK] Loaded {len(self.models)} models from {self.models_dir}/")
        print(f"  Trained on {self.train_samples} samples")
        if self.last_train_date:
            print(f"  Last trained: {self.last_train_date.strftime('%Y-%m-%d %H:%M:%S')}")

        return True
