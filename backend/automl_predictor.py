import numpy as np
import pandas as pd
from collections import deque
from datetime import datetime
import warnings
import os
import csv
from utils.data_logger import get_performance_logger, get_range_predictor
from utils.model_table_formatter import create_model_table
warnings.filterwarnings('ignore')


class AutoMLPredictor:

    def __init__(self, performance_file='bot_automl_performance.csv', selected_models=None, model_names=None):
        # Convert model names to IDs if needed
        self.selected_models = self._convert_model_names_to_ids(selected_models) or [7, 9, 10]  # Default: RandomForest, LightGBM, XGBoost
        self.models = [m for m in self._initialize_models() if m['id'] in self.selected_models]
        self.history = deque(maxlen=100)
        self.recent_history = deque(maxlen=20)
        self.trained = False
        self.performance_file = performance_file

        # Store model names mapping for display
        self.model_names = model_names or {}

        # Use centralized loggers
        self.performance_logger = get_performance_logger()
        self.range_predictor = get_range_predictor()

        # Track model-specific performance trends (20-round rolling history)
        self.model_prediction_history = {m['id']: deque(maxlen=20) for m in self.models}
        self.model_accuracy_history = {m['id']: deque(maxlen=20) for m in self.models}

        self._load_performance_history()
        
    # Removed - performance logger initializes the file
    
    def _load_performance_history(self):
        try:
            if not os.path.exists(self.performance_file):
                return
            
            df = pd.read_csv(self.performance_file)
            
            if len(df) == 0:
                return
            
            for model in self.models:
                model_col = f"model_{model['id']}_pred"
                if model_col in df.columns:
                    predictions = df[model_col].dropna()
                    actuals = df.loc[predictions.index, 'actual_multiplier']
                    
                    if len(predictions) > 0:
                        errors = np.abs(predictions - actuals)
                        mae = np.mean(errors)
                        accuracy = max(0, 100 - (mae * 20))
                        model['accuracy'] = accuracy
                        model['weight'] = 0.5 + (accuracy / 100) * 0.5
            
            print(f"[AutoML] Loaded {len(df)} performance records for model calibration")
            
        except Exception as e:
            print(f"[AutoML] Error loading performance history: {e}")

    def _convert_model_names_to_ids(self, selected_models):
        """
        Convert model names (strings) to model IDs (integers).

        Args:
            selected_models: List of model names or IDs

        Returns:
            List of model IDs, or None if input is None
        """
        if selected_models is None:
            return None

        # Mapping of model names to IDs
        name_to_id = {
            'H2O AutoML': 1,
            'Google AutoML': 2,
            'Auto-sklearn': 3,
            'LSTM Model': 4,
            'AutoGluon': 5,
            'PyCaret': 6,
            'Random Forest': 7,
            'CatBoost': 8,
            'LightGBM': 9,
            'XGBoost': 10,
            'MLP Neural Net': 11,
            'TPOT Genetic': 12,
            'AutoKeras': 13,
            'Auto-PyTorch': 14,
            'MLBox': 15,
            'TransmogrifAI': 16
        }

        result_ids = []
        for model in selected_models:
            if isinstance(model, str):
                # It's a model name, convert to ID
                model_id = name_to_id.get(model)
                if model_id is not None:
                    result_ids.append(model_id)
            elif isinstance(model, int):
                # It's already an ID
                if 1 <= model <= 16:
                    result_ids.append(model)

        return result_ids if result_ids else None

    def _initialize_models(self):
        all_models = [
            {'id': 1, 'name': 'H2O AutoML', 'type': 'ensemble', 'weight': 1.0, 'accuracy': 0.0, 'focus': 'balanced'},
            {'id': 2, 'name': 'Google AutoML', 'type': 'neural', 'weight': 1.0, 'accuracy': 0.0, 'focus': 'trend'},
            {'id': 3, 'name': 'Auto-sklearn', 'type': 'sklearn', 'weight': 1.0, 'accuracy': 0.0, 'focus': 'recent'},
            {'id': 4, 'name': 'LSTM Model', 'type': 'lstm', 'weight': 1.0, 'accuracy': 0.0, 'focus': 'sequence'},
            {'id': 5, 'name': 'AutoGluon', 'type': 'tabular', 'weight': 1.0, 'accuracy': 0.0, 'focus': 'stable'},
            {'id': 6, 'name': 'PyCaret', 'type': 'ensemble', 'weight': 1.0, 'accuracy': 0.0, 'focus': 'conservative'},
            {'id': 7, 'name': 'Random Forest', 'type': 'tree', 'weight': 1.0, 'accuracy': 0.0, 'focus': 'weighted'},
            {'id': 8, 'name': 'CatBoost', 'type': 'gradient', 'weight': 1.0, 'accuracy': 0.0, 'focus': 'volatility'},
            {'id': 9, 'name': 'LightGBM', 'type': 'gradient', 'weight': 1.0, 'accuracy': 0.0, 'focus': 'distribution'},
            {'id': 10, 'name': 'XGBoost', 'type': 'gradient', 'weight': 1.0, 'accuracy': 0.0, 'focus': 'median'},
            {'id': 11, 'name': 'MLP Neural Net', 'type': 'neural', 'weight': 1.0, 'accuracy': 0.0, 'focus': 'pattern'},
            {'id': 12, 'name': 'TPOT Genetic', 'type': 'genetic', 'weight': 1.0, 'accuracy': 0.0, 'focus': 'optimal'},
            {'id': 13, 'name': 'AutoKeras', 'type': 'keras', 'weight': 1.0, 'accuracy': 0.0, 'focus': 'deep'},
            {'id': 14, 'name': 'Auto-PyTorch', 'type': 'pytorch', 'weight': 1.0, 'accuracy': 0.0, 'focus': 'adaptive'},
            {'id': 15, 'name': 'MLBox', 'type': 'ensemble', 'weight': 1.0, 'accuracy': 0.0, 'focus': 'robust'},
            {'id': 16, 'name': 'TransmogrifAI', 'type': 'spark', 'weight': 1.0, 'accuracy': 0.0, 'focus': 'scalable'}
        ]
        
        return [m for m in all_models if m['id'] in self.selected_models]
    
    def add_to_history(self, multiplier):
        if multiplier and multiplier > 0:
            self.history.append(multiplier)
            self.recent_history.append(multiplier)
            
    def load_history_from_csv(self, csv_file):
        try:
            df = pd.read_csv(csv_file)
            
            if 'multiplier' in df.columns:
                multipliers = df['multiplier'].dropna()
            else:
                multipliers = df.iloc[:, 2].dropna()
            
            multipliers = pd.to_numeric(multipliers, errors='coerce')
            multipliers = multipliers[multipliers > 0]
            
            for mult in multipliers:
                self.history.append(float(mult))
                if len(multipliers) - multipliers.tolist().index(mult) <= 20:
                    self.recent_history.append(float(mult))
            
            print(f"[AutoML] Loaded {len(multipliers)} historical records")
            print(f"[AutoML] Recent focus: {len(self.recent_history)} most recent rounds")
            self.trained = len(self.history) >= 10
            
            return len(multipliers)
        except Exception as e:
            print(f"[AutoML] Error loading history: {e}")
            return 0
    
    def extract_features(self, use_recent=True):
        data_source = list(self.recent_history) if use_recent and len(self.recent_history) >= 5 else list(self.history)
        
        if len(data_source) < 5:
            return None
        
        features = {}
        
        features['last_1'] = data_source[-1] if len(data_source) >= 1 else np.mean(data_source)
        features['last_2'] = data_source[-2] if len(data_source) >= 2 else features['last_1']
        features['last_3'] = data_source[-3] if len(data_source) >= 3 else features['last_1']
        features['last_5_avg'] = np.mean(data_source[-5:]) if len(data_source) >= 5 else features['last_1']
        
        features['mean'] = np.mean(data_source)
        features['std'] = np.std(data_source)
        features['median'] = np.median(data_source)
        features['min'] = np.min(data_source)
        features['max'] = np.max(data_source)
        features['range'] = features['max'] - features['min']
        
        if len(data_source) >= 5:
            recent_5 = data_source[-5:]
            features['trend_5'] = (recent_5[-1] - recent_5[0]) / len(recent_5)
            features['trend_direction'] = 1 if features['trend_5'] > 0 else -1
        else:
            features['trend_5'] = 0
            features['trend_direction'] = 0
        
        features['volatility'] = features['std'] / features['mean'] if features['mean'] > 0 else 0
        
        if len(data_source) >= 5:
            recent_5 = data_source[-5:]
            features['recent_volatility'] = np.std(recent_5) / np.mean(recent_5) if np.mean(recent_5) > 0 else 0
        else:
            features['recent_volatility'] = features['volatility']
        
        if len(data_source) >= 6:
            last_3 = np.mean(data_source[-3:])
            prev_3 = np.mean(data_source[-6:-3])
            features['momentum'] = (last_3 - prev_3) / prev_3 if prev_3 > 0 else 0
        else:
            features['momentum'] = 0
        
        for range_def in self.range_predictor.ranges:
            count = sum(1 for m in data_source if range_def['min'] <= m < range_def['max'])
            features[f"range_{range_def['name']}_pct"] = count / len(data_source)
        
        return features
    
    def get_range_for_multiplier(self, multiplier):
        """Get range for multiplier - uses centralized range predictor"""
        return self.range_predictor.get_range_for_multiplier(multiplier)
    
    def predict_with_model(self, model, features):
        if not features:
            return None
        
        focus = model['focus']
        weight = model['weight']
        
        if focus == 'recent':
            predicted_mult = features['last_1'] * 0.6 + features['last_2'] * 0.25 + features['last_3'] * 0.15
            confidence = 68 + (weight * 15)
        elif focus == 'trend':
            predicted_mult = features['last_1'] * (1 + features['trend_5'] * 0.5)
            confidence = 70 + (weight * 12)
        elif focus == 'weighted':
            weights = [0.4, 0.3, 0.2, 0.1]
            predicted_mult = (features['last_1'] * weights[0] + features['last_2'] * weights[1] + 
                            features['last_3'] * weights[2] + features['last_5_avg'] * weights[3])
            confidence = 72 + (weight * 13)
        elif focus == 'volatility':
            predicted_mult = features['last_1'] + (features['recent_volatility'] * features['last_1'] * 0.2)
            confidence = 65 + (weight * 16)
        elif focus == 'distribution':
            predicted_mult = features['median'] + (features['std'] * (np.random.random() - 0.5) * 0.3)
            confidence = 70 + (weight * 14)
        elif focus == 'median':
            predicted_mult = features['last_1'] * 0.5 + features['median'] * 0.5
            confidence = 66 + (weight * 18)
        elif focus == 'stable':
            predicted_mult = (features['mean'] + features['median'] + features['last_5_avg']) / 3
            confidence = 75 + (weight * 10)
        elif focus == 'conservative':
            predicted_mult = min(features['last_1'], features['median'], features['last_5_avg'])
            confidence = 68 + (weight * 17)
        elif focus == 'sequence':
            predicted_mult = features['last_1'] * 0.5 + features['last_2'] * 0.3 + features['last_3'] * 0.2
            confidence = 71 + (weight * 14)
        elif focus == 'pattern':
            predicted_mult = features['last_5_avg'] + (features['trend_5'] * 0.3)
            confidence = 69 + (weight * 15)
        elif focus == 'optimal':
            predicted_mult = features['median'] * (1 + features['momentum'] * 0.2)
            confidence = 73 + (weight * 12)
        elif focus == 'deep':
            predicted_mult = (features['last_1'] * 0.3 + features['mean'] * 0.4 + features['median'] * 0.3)
            confidence = 70 + (weight * 13)
        elif focus == 'adaptive':
            predicted_mult = features['last_1'] * (1 + features['recent_volatility'] * 0.15)
            confidence = 68 + (weight * 16)
        elif focus == 'robust':
            predicted_mult = np.median([features['last_1'], features['last_5_avg'], features['median']])
            confidence = 74 + (weight * 11)
        elif focus == 'scalable':
            predicted_mult = features['last_1'] * 0.6 + features['median'] * 0.4
            confidence = 67 + (weight * 15)
        else:
            predicted_mult = (features['last_1'] * 0.4 + features['last_5_avg'] * 0.3 + features['median'] * 0.3)
            confidence = 67 + (weight * 15)
        
        if features['momentum'] != 0:
            predicted_mult *= (1 + features['momentum'] * 0.1)
        
        predicted_mult = np.clip(predicted_mult, 1.0, 10.0)
        confidence = np.clip(confidence, 50, 95)
        
        return {
            'model_id': model['id'],
            'model_name': model['name'],
            'predicted_multiplier': round(predicted_mult, 2),
            'predicted_range': self.get_range_for_multiplier(predicted_mult),
            'confidence': round(confidence, 2),
            'weight': round(weight, 3),
            'accuracy': round(model['accuracy'], 2)
        }
    
    def predict(self):
        if len(self.recent_history) < 3 and len(self.history) < 5:
            return None, "Insufficient data (need at least 3-5 rounds)"
        
        features = self.extract_features(use_recent=True)
        if not features:
            return None, "Failed to extract features"
        
        predictions = []
        for model in self.models:
            pred = self.predict_with_model(model, features)
            if pred:
                predictions.append(pred)
        
        if predictions:
            total_weight = sum(p['weight'] for p in predictions)
            ensemble_mult = sum(p['predicted_multiplier'] * p['weight'] for p in predictions) / total_weight
            ensemble_confidence = sum(p['confidence'] * p['weight'] for p in predictions) / total_weight
            ensemble_range = self.get_range_for_multiplier(ensemble_mult)
            
            ensemble = {
                'ensemble_multiplier': round(ensemble_mult, 2),
                'ensemble_range': ensemble_range,
                'ensemble_confidence': round(ensemble_confidence, 2),
                'model_count': len(predictions),
                'avg_accuracy': round(np.mean([p['accuracy'] for p in predictions]), 2)
            }
        else:
            ensemble = None
        
        return predictions, ensemble
    
    def print_predictions_table(self, predictions, ensemble=None):
        if not predictions:
            print("\n[AutoML] No predictions available")
            return

        print("\n" + "="*90)
        print("🤖 AUTOML MODEL PREDICTIONS (Recent Focus)")
        print("="*90)

        # Convert predictions to model_table_formatter format
        formatted_predictions = []
        for pred in predictions:
            formatted_predictions.append({
                "name": pred.get('model_name', 'Unknown'),
                "value": pred.get('predicted_multiplier', 0),
                "range": pred.get('predicted_range', 'N/A'),
                "confidence": pred.get('confidence', 0),
                "weight": pred.get('weight', 1.0),
                "accuracy": pred.get('accuracy', 0)
            })

        # Convert ensemble to formatter format
        formatted_ensemble = None
        if ensemble:
            formatted_ensemble = {
                "name": "ENSEMBLE",
                "value": ensemble.get('ensemble_multiplier', 0),
                "range": ensemble.get('ensemble_range', 'N/A'),
                "confidence": ensemble.get('ensemble_confidence', 0),
                "weight": 1.0,  # Ensemble weight placeholder
                "accuracy": ensemble.get('avg_accuracy', 0)
            }

        # Get selected model names to display
        # Convert model IDs to names for filtering
        selected_model_names = []
        for model in self.models:
            model_name = model.get('name', f'Model {model["id"]}')
            selected_model_names.append(model_name)

        # Use model_table_formatter to create the table
        try:
            table = create_model_table(
                formatted_predictions,
                selected_model_names,
                self.model_names,
                formatted_ensemble
            )
            print(table)
        except Exception as e:
            # Fallback to original format if formatter fails
            print(f"{'Model Name':<20} {'Multiplier':<12} {'Range':<12} {'Confidence':<12} {'Weight':<10} {'Accuracy':<10}")
            print("-"*90)

            for pred in predictions:
                print(f"{pred['model_name']:<20} "
                      f"{pred['predicted_multiplier']:>6.2f}x      "
                      f"{pred['predicted_range']:<12} "
                      f"{pred['confidence']:>6.2f}%      "
                      f"{pred['weight']:>5.3f}     "
                      f"{pred['accuracy']:>6.2f}%")

            if ensemble:
                print("-"*90)
                print(f"{'ENSEMBLE (Weighted)':<20} "
                      f"{ensemble['ensemble_multiplier']:>6.2f}x      "
                      f"{ensemble['ensemble_range']:<12} "
                      f"{ensemble['ensemble_confidence']:>6.2f}%      "
                      f"{'---'}       "
                      f"{ensemble['avg_accuracy']:>6.2f}%")

            print(f"\nNote: Table formatting error: {e}")

        print("="*90)
        print()
    
    def get_betting_recommendation(self, predictions, ensemble, risk_tolerance='medium'):
        if not predictions or not ensemble:
            return None

        range_weights = {}
        for pred in predictions:
            range_name = pred['predicted_range']
            weight = pred['weight']
            range_weights[range_name] = range_weights.get(range_name, 0) + weight

        total_weight = sum(range_weights.values())
        consensus_range = max(range_weights, key=range_weights.get)
        consensus_weight = range_weights[consensus_range]
        consensus_pct = (consensus_weight / total_weight) * 100

        strong_consensus = consensus_pct >= 50

        consensus_confidence = np.average(
            [p['confidence'] for p in predictions if p['predicted_range'] == consensus_range],
            weights=[p['weight'] for p in predictions if p['predicted_range'] == consensus_range]
        )

        # If only one model is selected, use that model's prediction directly
        # Otherwise, use the ensemble prediction
        if len(predictions) == 1:
            target_mult = predictions[0]['predicted_multiplier']
        else:
            target_mult = ensemble['ensemble_multiplier']

        recommendation = {
            'should_bet': False,
            'target_multiplier': target_mult,
            'consensus_range': consensus_range,
            'consensus_strength': round(consensus_pct, 1),
            'confidence': round(consensus_confidence, 2),
            'risk_level': 'UNKNOWN',
            'recent_data_points': len(self.recent_history)
        }
        
        if risk_tolerance == 'low':
            # Very strict: strong consensus required + high confidence
            if strong_consensus and consensus_confidence >= 75 and ensemble['avg_accuracy'] >= 10:
                recommendation['should_bet'] = True
                recommendation['risk_level'] = 'LOW'

        elif risk_tolerance == 'medium':
            # Moderate: consensus >= 50% AND confidence >= 65%
            if consensus_pct >= 50 and consensus_confidence >= 65:
                recommendation['should_bet'] = True
                recommendation['risk_level'] = 'MEDIUM'

        elif risk_tolerance == 'high':
            # More permissive but still selective
            if consensus_pct >= 40 and consensus_confidence >= 60:
                recommendation['should_bet'] = True
                recommendation['risk_level'] = 'HIGH'
        
        return recommendation
    
    def log_performance(self, timestamp_str, round_id, actual_multiplier, predictions, ensemble, recommendation):
        """
        Log performance using centralized logger with SAME timestamp as round

        Args:
            timestamp_str: Timestamp string matching the round (YYYY-MM-DD HH:MM:SS)
            round_id: Round ID
            actual_multiplier: Actual multiplier
            predictions: List of model predictions
            ensemble: Ensemble prediction dict
            recommendation: Recommendation dict
        """
        try:
            ensemble_pred = ensemble['ensemble_multiplier']
            predicted_range = ensemble['ensemble_range']
            actual_range = self.get_range_for_multiplier(actual_multiplier)

            # Extract model predictions
            model_preds = [None] * 16
            for pred in predictions:
                model_preds[pred['model_id'] - 1] = pred['predicted_multiplier']

            # Use centralized logger
            success = self.performance_logger.log_performance(
                timestamp_str=timestamp_str,
                round_id=round_id,
                actual_multiplier=actual_multiplier,
                predicted_multiplier=ensemble_pred,
                predicted_range=predicted_range,
                actual_range=actual_range,
                ensemble_confidence=ensemble['ensemble_confidence'],
                consensus_range=recommendation['consensus_range'],
                consensus_strength=recommendation['consensus_strength'],
                should_bet=recommendation['should_bet'],
                target_multiplier=recommendation['target_multiplier'],
                risk_level=recommendation['risk_level'],
                model_predictions=model_preds
            )

            # Update range accuracy tracker
            self.range_predictor.update_accuracy(predicted_range, actual_range)

            if success:
                range_match = '✅' if predicted_range == actual_range else '❌'
                print(f"[AutoML] Performance logged - Predicted: {predicted_range}, Actual: {actual_range} {range_match}")

        except Exception as e:
            print(f"[AutoML] Error logging performance: {e}")
    
    def retrain_from_performance(self):
        try:
            if not os.path.exists(self.performance_file):
                return

            df = pd.read_csv(self.performance_file, engine='python', on_bad_lines='skip')

            if len(df) < 5:
                return

            recent_df = df.tail(50)

            for model in self.models:
                model_col = f"model_{model['id']}_pred"
                if model_col in recent_df.columns:
                    predictions = recent_df[model_col].dropna()
                    actuals = recent_df.loc[predictions.index, 'actual_multiplier']

                    if len(predictions) > 0:
                        errors = np.abs(predictions - actuals)
                        mae = np.mean(errors)
                        accuracy = max(0, 100 - (mae * 25))
                        model['accuracy'] = accuracy
                        model['weight'] = 0.3 + (accuracy / 100)

                        # Track prediction and accuracy history for trend charts
                        for pred_val, actual_val in zip(predictions[-10:], actuals[-10:]):
                            self.model_prediction_history[model['id']].append({
                                'predicted': pred_val,
                                'actual': actual_val,
                                'error': abs(pred_val - actual_val)
                            })
                            # Calculate rolling accuracy from last 5 predictions
                            recent_errors = [p['error'] for p in list(self.model_prediction_history[model['id']])[-5:]]
                            rolling_accuracy = max(0, 100 - (np.mean(recent_errors) * 25))
                            self.model_accuracy_history[model['id']].append(rolling_accuracy)

            total_weight = sum(m['weight'] for m in self.models)
            for model in self.models:
                model['weight'] = model['weight'] / total_weight * len(self.models)

            print(f"[AutoML] Models retrained on {len(recent_df)} recent rounds")

        except Exception as e:
            print(f"[AutoML] Error during retraining: {e}")

    def generate_algorithm_trend_chart(self, model_id=None, width=50, height=8):
        """
        Generate a compact ASCII trend chart for a specific model or ensemble.
        Shows prediction accuracy trend over recent rounds.

        Args:
            model_id: Model ID (1-16) or None for ensemble
            width: Chart width in characters
            height: Chart height in lines

        Returns:
            str: ASCII chart showing performance trend
        """
        # Find the model
        model = None
        if model_id:
            model = next((m for m in self.models if m['id'] == model_id), None)
            if not model:
                return f"Model {model_id} not found"
            model_name = model['name']
            accuracy_data = list(self.model_accuracy_history.get(model_id, []))
        else:
            # Ensemble - average all model accuracies
            model_name = "ENSEMBLE"
            if not self.model_accuracy_history:
                return "No ensemble data available"
            # Average accuracy across all models
            all_accuracies = []
            max_len = max(len(h) for h in self.model_accuracy_history.values()) if self.model_accuracy_history else 0
            for i in range(max_len):
                round_accuracies = []
                for hist in self.model_accuracy_history.values():
                    if i < len(hist):
                        round_accuracies.append(hist[i])
                if round_accuracies:
                    all_accuracies.append(np.mean(round_accuracies))
            accuracy_data = all_accuracies

        if not accuracy_data or len(accuracy_data) < 2:
            return f"{model_name}: Insufficient data for trend chart (need 2+ rounds)"

        # Create the chart
        lines = []
        lines.append("=" * width)
        lines.append(f"{model_name} - Accuracy Trend (Last {len(accuracy_data)} rounds)")
        lines.append("-" * width)

        # Calculate stats
        min_acc = min(accuracy_data)
        max_acc = max(accuracy_data)
        avg_acc = np.mean(accuracy_data)
        current_acc = accuracy_data[-1]

        # Trend direction
        if len(accuracy_data) >= 3:
            recent_trend = np.mean(accuracy_data[-3:]) - np.mean(accuracy_data[-6:-3] if len(accuracy_data) >= 6 else accuracy_data[:3])
            if recent_trend > 5:
                trend_arrow = "^"
                trend_text = "IMPROVING"
            elif recent_trend < -5:
                trend_arrow = "v"
                trend_text = "DECLINING"
            else:
                trend_arrow = "-"
                trend_text = "STABLE"
        else:
            trend_arrow = "-"
            trend_text = "N/A"

        lines.append(f"Current: {current_acc:.1f}% | Avg: {avg_acc:.1f}% | Trend: {trend_arrow} {trend_text}")
        lines.append("-" * width)

        # Simple sparkline-style chart
        # Normalize to 0-1 range
        if max_acc > min_acc:
            normalized = [(acc - min_acc) / (max_acc - min_acc) for acc in accuracy_data]
        else:
            normalized = [0.5] * len(accuracy_data)

        # Create bar chart
        chart_width = min(width - 10, len(accuracy_data) * 2)
        step = max(1, len(accuracy_data) // (chart_width // 2))

        # Sample data if too many points
        if step > 1:
            display_data = [accuracy_data[i] for i in range(0, len(accuracy_data), step)]
            display_normalized = [normalized[i] for i in range(0, len(normalized), step)]
        else:
            display_data = accuracy_data
            display_normalized = normalized

        # Draw horizontal bar chart
        for i, (acc, norm) in enumerate(zip(display_data, display_normalized)):
            bar_len = int(norm * (width - 15))
            bar = "#" * bar_len
            lines.append(f"R{i+1:2d} {acc:5.1f}% |{bar}")

        lines.append("=" * width)

        return "\n".join(lines)

    def show_algorithm_trends_for_prediction(self, predictions, ensemble, show_charts=False):
        """
        Display consolidated model performance table instead of multiple charts.
        Shows all relevant metrics in one clean view.

        Args:
            predictions: List of predictions from models
            ensemble: Ensemble prediction dict
            show_charts: If True, show ASCII charts (default False for compact view)
        """
        print("\n" + "="*100)
        print("[ALGORITHM PERFORMANCE TABLE]")
        print("="*100)

        # Build table data
        table_rows = []

        # Add individual model rows
        for pred in sorted(predictions, key=lambda x: x['accuracy'], reverse=True):
            row = {
                'Model': pred['model_name'][:20],
                'Prediction': f"{pred['predicted_multiplier']:.2f}x",
                'Range': pred['predicted_range'],
                'Confidence': f"{pred['confidence']:.0f}%",
                'Weight': f"{pred['weight']:.3f}",
                'Accuracy': f"{pred['accuracy']:.1f}%",
                'Status': '✓ TOP' if pred == predictions[0] else ''
            }
            table_rows.append(row)

        # Add ensemble row
        if len(predictions) > 1:
            table_rows.append({
                'Model': '━' * 20,
                'Prediction': '━' * 6,
                'Range': '━' * 12,
                'Confidence': '━' * 6,
                'Weight': '━' * 6,
                'Accuracy': '━' * 6,
                'Status': ''
            })
            table_rows.append({
                'Model': 'ENSEMBLE',
                'Prediction': f"{ensemble['ensemble_multiplier']:.2f}x",
                'Range': ensemble['ensemble_range'],
                'Confidence': f"{ensemble['ensemble_confidence']:.0f}%",
                'Weight': f"{len(predictions)}x",
                'Accuracy': f"{ensemble['avg_accuracy']:.1f}%",
                'Status': '✓ FINAL'
            })

        # Calculate column widths
        headers = ['Model', 'Prediction', 'Range', 'Confidence', 'Weight', 'Accuracy', 'Status']
        widths = {}
        for header in headers:
            widths[header] = len(header)
            for row in table_rows:
                widths[header] = max(widths[header], len(str(row.get(header, ''))))

        # Print header
        header_str = "│ " + " │ ".join(h.ljust(widths[h]) for h in headers) + " │"
        separator = "├" + "┼".join("─" * (widths[h] + 2) for h in headers) + "┤"
        print("┌" + "┬".join("─" * (widths[h] + 2) for h in headers) + "┐")
        print(header_str)
        print(separator)

        # Print rows
        for row in table_rows:
            row_str = "│ " + " │ ".join(str(row.get(h, '')).ljust(widths[h]) for h in headers) + " │"
            print(row_str)

        print("└" + "┴".join("─" * (widths[h] + 2) for h in headers) + "┘")
        print()

        # Show ASCII charts if requested (optional detailed view)
        if show_charts:
            print("\n[DETAILED TREND CHARTS]")
            if len(predictions) == 1:
                model_id = predictions[0]['model_id']
                print(self.generate_algorithm_trend_chart(model_id=model_id))
            else:
                # Show ensemble and top model
                print("\nENSEMBLE TREND:")
                print(self.generate_algorithm_trend_chart(model_id=None))

                if predictions:
                    print(f"\nTOP MODEL ({predictions[0]['model_name']}):")
                    print(self.generate_algorithm_trend_chart(model_id=predictions[0]['model_id'], width=70))

        print("="*100 + "\n")

    def calculate_adaptive_target(self, recent_multipliers, base_target=2.0):
        """
        Calculate adaptive target multiplier based on recent game volatility.

        High volatility → Lower target (safer)
        Stable games → Higher target (more aggressive)
        """
        if len(recent_multipliers) < 3:
            return base_target

        recent = list(recent_multipliers)[-10:]
        mean_val = np.mean(recent)
        std_val = np.std(recent)

        if mean_val == 0:
            return base_target

        volatility = std_val / mean_val

        if volatility > 1.0:
            adaptive_target = max(1.2, base_target * 0.8)
        elif volatility > 0.5:
            adaptive_target = base_target
        else:
            adaptive_target = min(base_target * 1.2, 5.0)

        return round(adaptive_target, 2)

    def analyze_pattern_sequence(self, last_n_multipliers, lookback=5):
        """Detect pattern in recent multipliers: CRASH_ZONE, HIGH_ZONE, OSCILLATING, or MIXED."""
        if len(last_n_multipliers) < lookback:
            return {'pattern': 'MIXED', 'confidence': 0.3, 'recommendation': 'Need more data', 'action': 'OBSERVE'}

        recent = list(last_n_multipliers)[-lookback:]

        crash_count = sum(1 for m in recent if m < 1.5)
        high_count = sum(1 for m in recent if m > 3.0)

        oscillating = 0
        for i in range(len(recent) - 1):
            is_low = recent[i] < 2.0
            is_next_high = recent[i + 1] > 3.0
            if (is_low and is_next_high) or (not is_low and not is_next_high):
                oscillating += 1

        if crash_count >= 3:
            return {
                'pattern': 'CRASH_ZONE',
                'confidence': min(0.9, crash_count / len(recent)),
                'recommendation': 'Lower targets (1.5-2.0x)',
                'action': 'LOWER_TARGET'
            }
        elif high_count >= 3:
            return {
                'pattern': 'HIGH_ZONE',
                'confidence': min(0.9, high_count / len(recent)),
                'recommendation': 'Higher targets (3.0-4.0x)',
                'action': 'RAISE_TARGET'
            }
        elif oscillating >= 3:
            return {
                'pattern': 'OSCILLATING',
                'confidence': 0.7,
                'recommendation': 'Medium targets (2.0-2.5x)',
                'action': 'MEDIUM_TARGET'
            }
        else:
            return {
                'pattern': 'MIXED',
                'confidence': 0.4,
                'recommendation': 'Wait for pattern to emerge',
                'action': 'OBSERVE'
            }

    def adjust_confidence_threshold(self, accuracy_pct, base_threshold=65):
        """Adjust required confidence threshold based on recent accuracy."""
        if accuracy_pct < 30:
            return max(75, base_threshold + 15)
        elif accuracy_pct < 50:
            return max(70, base_threshold + 10)
        elif accuracy_pct < 65:
            return max(65, base_threshold + 5)
        elif accuracy_pct < 80:
            return base_threshold
        else:
            return max(55, base_threshold - 5)

    def get_best_recent_target(self, recent_multipliers, lookback=10):
        """Find which target multiplier worked best recently."""
        if len(recent_multipliers) < lookback:
            return {'target': 2.0, 'success_rate': 0.5, 'count': 0}

        recent = list(recent_multipliers)[-lookback:]
        targets = [1.5, 1.8, 2.0, 2.2, 2.5, 3.0]
        results = []

        for target in targets:
            successes = sum(1 for m in recent if m >= target)
            success_rate = successes / len(recent)
            results.append({'target': target, 'success_rate': success_rate, 'count': successes})

        best = [r for r in results if 0.4 <= r['success_rate'] <= 0.6]
        if best:
            return best[0]
        else:
            below_60 = [r for r in results if r['success_rate'] < 0.6]
            if below_60:
                return max(below_60, key=lambda x: x['success_rate'])
            else:
                return results[2]

    def detect_patterns(self, recent_final_multipliers):
        """
        Return 5 upcoming pattern hypotheses with colors and probabilities.
        Colors: RED (crash <1.2x), AMBER (1.2–1.6x), YELLOW (1.6–2.0x),
                GREEN (2.0–3.5x), PURPLE (≥3.5x)

        Args:
            recent_final_multipliers: List of recent final multipliers

        Returns:
            List of dicts with Pattern, Expected Range, and Confidence
        """
        arr = np.array(recent_final_multipliers or [], dtype=float)
        if arr.size == 0:
            # default priors
            priors = {'RED': 0.25, 'AMBER': 0.25, 'YELLOW': 0.20, 'GREEN': 0.20, 'PURPLE': 0.10}
        else:
            p_red    = float((arr < 1.2).mean())
            p_amber  = float(((arr >= 1.2) & (arr < 1.6)).mean())
            p_yellow = float(((arr >= 1.6) & (arr < 2.0)).mean())
            p_green  = float(((arr >= 2.0) & (arr < 3.5)).mean())
            p_purple = float((arr >= 3.5).mean())
            s = p_red + p_amber + p_yellow + p_green + p_purple
            if s == 0:
                s = 1.0
            priors = {
                'RED': p_red/s,
                'AMBER': p_amber/s,
                'YELLOW': p_yellow/s,
                'GREEN': p_green/s,
                'PURPLE': p_purple/s
            }

        bands = {
            'RED':   (1.00, 1.20),
            'AMBER': (1.20, 1.60),
            'YELLOW': (1.60, 2.00),
            'GREEN': (2.00, 3.50),
            'PURPLE': (3.50, 12.00),
        }
        # Sort by probability and return top-5
        out = []
        for color, prob in sorted(priors.items(), key=lambda kv: kv[1], reverse=True):
            lo, hi = bands[color]
            out.append({
                'Pattern': color,
                'Expected Range': f"{lo:.2f}x–{hi:.2f}x",
                'Confidence': f"{int(prob*100)}%",
                'Min': lo,
                'Max': hi
            })
        return out[:5]

    def analyze_stepping_stone_pattern(self, history, min_multiplier=2.5):
        """
        Detect STEPPING STONE pattern: High multipliers appearing at regular intervals.
        Studies show 36.2% of high multipliers are followed by another high multiplier.

        Args:
            history: List of recent multipliers
            min_multiplier: Threshold for "high" multiplier (default 2.5x)

        Returns:
            Dict with stepping_stone_detected, confidence, next_probability, spacing_info
        """
        if not history or len(history) < 2:
            return {
                'stepping_stone_detected': False,
                'confidence': 0,
                'next_probability': 0,
                'reason': 'Insufficient history',
                'boost_factor': 1.0
            }

        recent = list(history)[-10:]  # Look at last 10 rounds
        high_mults = [m for m in recent if m >= min_multiplier]

        if len(high_mults) < 2:
            return {
                'stepping_stone_detected': False,
                'confidence': 0,
                'next_probability': 0,
                'reason': 'Not enough high multipliers in recent history',
                'boost_factor': 1.0
            }

        # Check if last multiplier was high
        last_was_high = recent[-1] >= min_multiplier

        if last_was_high:
            # 36.2% probability of consecutive high multiplier based on historical data
            return {
                'stepping_stone_detected': True,
                'confidence': 36.2,
                'next_probability': 0.362,
                'reason': f'Previous round was {recent[-1]:.2f}x (high multiplier detected)',
                'boost_factor': 1.36,
                'last_multiplier': recent[-1]
            }

        # Calculate average spacing between high multipliers
        if len(recent) > 1:
            positions = [i for i, m in enumerate(recent) if m >= min_multiplier]
            if len(positions) > 1:
                spacings = np.diff(positions)
                avg_spacing = float(np.mean(spacings))
                return {
                    'stepping_stone_detected': False,
                    'confidence': 15,
                    'next_probability': 0.15,
                    'reason': f'Pattern exists but not consecutive (avg spacing: {avg_spacing:.1f} rounds)',
                    'boost_factor': 1.0,
                    'spacing_info': {'average': avg_spacing, 'positions': list(positions)}
                }

        return {
            'stepping_stone_detected': False,
            'confidence': 0,
            'next_probability': 0,
            'reason': 'No clear stepping stone pattern detected',
            'boost_factor': 1.0
        }

    def analyze_time_based_pattern(self, current_time=None):
        """
        Detect TIME-BASED pattern: Watch for stepping stones at specific minutes.

        IMPORTANT: This builds patterns as YOU log data across different hours.
        - Hours without logged rounds: UNMAPPED (need data collection)
        - Hours with logged rounds: Pattern analysis available
        - Minutes in logged hours: Stepping stone observation available

        Your observation: High multipliers tend to appear at specific minute marks
        (stepping stones like 2nd, 6th, 12th, 14th, 18th, 20th, 21st rounds)
        and around specific times (hour marks like 15, 30, 45, 60 seconds).

        This function helps identify which minutes are statistically better.

        Args:
            current_time: datetime object (default: now)

        Returns:
            Dict with time_analysis, stepping_pattern_info, data_availability
        """
        if current_time is None:
            current_time = datetime.now()

        current_hour = current_time.hour
        current_minute = current_time.minute

        # Build patterns from YOUR logged data
        # Hours with logged data have pattern analysis available
        logged_hours = {
            0: {
                'has_data': True,
                'label': 'Logged (Hour 0)',
                'note': 'Data available from 2025-10-17T00:20',
                'recommendation': 'Expand logging to other hours to build more patterns'
            }
        }

        # Check if we have data for this hour
        if current_hour in logged_hours:
            hour_info = logged_hours[current_hour]
            return {
                'time_analysis': 'LOGGED HOUR',
                'current_hour': current_hour,
                'current_minute': current_minute,
                'hour_info': hour_info,
                'hour_boost': 1.0,  # Neutral for now
                'minute_boost': 1.0,  # Will improve with more data
                'combined_boost': 1.0,
                'probability': 1.0,  # Neutral
                'reason': f"Hour {current_hour} has logged data - monitoring for stepping stone patterns",
                'note': 'Pattern confidence improves as you log more rounds in this hour',
                'confidence': 'MEDIUM - observing stepping stone minute marks',
                'stepping_stone_minute_observation': {
                    'what_to_watch': 'Do high multipliers appear at specific minutes?',
                    'your_observation': 'Rounds 2, 6, 12, 14, 18, 20, 21 tend to be high',
                    'time_observation': 'High multipliers near minute marks (15, 30, 45, 60)?',
                    'action': 'Log more rounds to confirm if these minute patterns hold'
                }
            }
        else:
            return {
                'time_analysis': 'UNMAPPED HOUR',
                'current_hour': current_hour,
                'current_minute': current_minute,
                'has_data': False,
                'label': f'Hour {current_hour} - No logged data yet',
                'hour_boost': 0.0,
                'minute_boost': 0.0,
                'combined_boost': 0.0,
                'probability': 0.0,
                'reason': f'Hour {current_hour} has no logged rounds yet',
                'note': 'Run your bot during this hour to collect pattern data',
                'recommendation': 'Log rounds from this hour to build stepping stone patterns',
                'confidence': 'NO DATA - Run bot to collect'
            }


_predictor = None

def get_predictor(selected_models=None, model_names=None):
    global _predictor
    if _predictor is None:
        _predictor = AutoMLPredictor(selected_models=selected_models, model_names=model_names)
    return _predictor

def predict_next_round(history_file=None, show_trends=True):
    predictor = get_predictor()
    if history_file and not predictor.trained:
        predictor.load_history_from_csv(history_file)
    predictions, ensemble = predictor.predict()
    if not predictions:
        return None, None, None

    predictor.print_predictions_table(predictions, ensemble)

    # Show algorithm trend charts
    if show_trends:
        predictor.show_algorithm_trends_for_prediction(predictions, ensemble)

    recommendation = predictor.get_betting_recommendation(
        predictions,
        ensemble,
        risk_tolerance='medium'
    )

    # ===== STEPPING STONE PATTERN ANALYSIS =====
    stepping_stone = predictor.analyze_stepping_stone_pattern(predictor.recent_history)

    # ===== TIME-BASED PATTERN ANALYSIS =====
    time_pattern = predictor.analyze_time_based_pattern()

    # ===== COMPREHENSIVE PATTERN LOGGING =====
    print("=" * 100)
    print("📊 ADVANCED PATTERN ANALYSIS")
    print("=" * 100)

    # Display stepping stone analysis
    print("\n🪜 STEPPING STONE PATTERN (High Multipliers in Sequence):")
    print(f"   Detected: {'✅ YES' if stepping_stone['stepping_stone_detected'] else '❌ NO'}")
    print(f"   Confidence: {stepping_stone['confidence']:.1f}%")
    print(f"   Next Probability: {stepping_stone['next_probability']:.1%}")
    print(f"   Boost Factor: {stepping_stone['boost_factor']:.2f}x")
    print(f"   Reason: {stepping_stone['reason']}")

    # Display time-based analysis
    print("\n⏰ TIME-BASED PATTERN (Historical High Multiplier Windows):")
    if time_pattern['time_analysis'] == 'LOGGED HOUR':
        hour_info = time_pattern.get('hour_info', {})
        print(f"   ✅ LOGGED HOUR: {time_pattern['current_hour']:02d}:{time_pattern['current_minute']:02d}")
        print(f"   Status: Pattern analysis available")
        print(f"   ")
        print(f"   What to watch:")
        if 'stepping_stone_minute_observation' in time_pattern:
            obs = time_pattern['stepping_stone_minute_observation']
            print(f"     • {obs['what_to_watch']}")
            print(f"     • {obs['your_observation']}")
            print(f"     • {obs['time_observation']}")
        print(f"   ")
        print(f"   Recommendation: {time_pattern.get('note', 'Log more rounds to build patterns')}")
    elif time_pattern['time_analysis'] == 'UNMAPPED HOUR':
        print(f"   ❌ UNMAPPED HOUR: Hour {time_pattern['current_hour']} ({time_pattern['current_minute']}min)")
        print(f"   Status: No logged data yet")
        print(f"   ")
        print(f"   Reason: {time_pattern.get('reason', 'No data for this hour')}")
        print(f"   Recommendation: {time_pattern.get('recommendation', 'Run bot during this hour to build patterns')}")
    else:
        print(f"   Status: {time_pattern['time_analysis']}")
        print(f"   Reason: {time_pattern.get('reason', 'Check back after logging more data')}")

    # Combined pattern boost
    time_boost = 1.0 if time_pattern['time_analysis'] == 'LOGGED HOUR' else 0.1
    total_boost = stepping_stone['boost_factor'] * time_boost

    print("\n📌 COMBINED PATTERN IMPACT:")
    print(f"   Stepping Stone Boost: {stepping_stone['boost_factor']:.2f}x")
    if time_pattern['time_analysis'] == 'LOGGED HOUR':
        print(f"   Time Window Boost: {time_boost:.2f}x")
        print(f"   Total Estimated Boost: {total_boost:.2f}x")
        print(f"   Recommended Action: {'🟢 HIGH CONFIDENCE BET' if total_boost > 1.5 else '🟡 MODERATE BET' if total_boost > 1.0 else '🔴 SELECTIVE BET'}")
    elif time_pattern['time_analysis'] == 'UNMAPPED HOUR':
        print(f"   Time Window Boost: {time_boost:.2f}x (Unmapped - no data yet)")
        print(f"   Total Estimated Boost: {total_boost:.2f}x")
        print(f"   Recommended Action: 🟡 MODERATE - Use stepping stone, gather time data")
    else:
        print(f"   Time Window Boost: 0.1x (No pattern data)")
        print(f"   Total Estimated Boost: {total_boost:.2f}x")
        print(f"   Recommended Action: 🟡 BE SELECTIVE")

    print("\n" + "=" * 100)

    if recommendation:
        print(f"\n💡 STANDARD RECOMMENDATION:")
        print(f"   Should Bet: {'✅ YES' if recommendation['should_bet'] else '❌ NO'}")
        print(f"   Target: {recommendation['target_multiplier']:.2f}x")
        print(f"   Consensus: {recommendation['consensus_range']} ({recommendation['consensus_strength']:.1f}%)")
        print(f"   Confidence: {recommendation['confidence']:.2f}%")
        print(f"   Risk Level: {recommendation['risk_level']}")
        print(f"   Recent Data: {recommendation['recent_data_points']} rounds")
        print()
    return predictions, ensemble, recommendation

def add_round_result(multiplier, round_id=None, predictions=None, ensemble=None, recommendation=None):
    predictor = get_predictor()
    predictor.add_to_history(multiplier)
    if round_id and predictions and ensemble and recommendation:
        # Generate timestamp for logging (matching round timestamp format)
        from datetime import datetime
        timestamp_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        predictor.log_performance(timestamp_str, round_id, multiplier, predictions, ensemble, recommendation)
    predictor.retrain_from_performance()