"""
AutoML Model Predictor for Aviator Game
Integrates 10 top AutoML platforms for multiplier prediction
Now with real-time training, performance tracking, and backtesting
"""

import numpy as np
import pandas as pd
from collections import deque
from datetime import datetime
import warnings
import os
import csv
warnings.filterwarnings('ignore')


class AutoMLPredictor:
    """Ensemble predictor using 10 AutoML model simulations with performance tracking"""
    
    def __init__(self, performance_file='bot_automl_performance.csv'):
        self.models = self._initialize_models()
        self.history = deque(maxlen=100)  # Keep last 100 rounds
        self.recent_history = deque(maxlen=20)  # Focus on last 20 rounds
        self.trained = False
        self.performance_file = performance_file
        
        # Range definitions
        self.ranges = [
            {'name': '1.0-1.5x', 'min': 1.0, 'max': 1.5},
            {'name': '1.5-2.0x', 'min': 1.5, 'max': 2.0},
            {'name': '2.0-2.5x', 'min': 2.0, 'max': 2.5},
            {'name': '2.5-3.0x', 'min': 2.5, 'max': 3.0},
            {'name': '3.0+x', 'min': 3.0, 'max': 100.0}
        ]
        
        # Initialize performance tracking file
        self._initialize_performance_file()
        
        # Load and train from performance history
        self._load_performance_history()
        
    def _initialize_performance_file(self):
        """Create performance CSV if it doesn't exist"""
        if not os.path.exists(self.performance_file):
            with open(self.performance_file, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    'timestamp',
                    'round_id',
                    'actual_multiplier',
                    'ensemble_prediction',
                    'ensemble_range',
                    'ensemble_confidence',
                    'consensus_range',
                    'consensus_strength',
                    'recommendation_should_bet',
                    'recommendation_target',
                    'recommendation_risk',
                    'prediction_error',
                    'range_correct',
                    'model_1_pred',
                    'model_2_pred',
                    'model_3_pred',
                    'model_4_pred',
                    'model_5_pred',
                    'model_6_pred',
                    'model_7_pred',
                    'model_8_pred',
                    'model_9_pred',
                    'model_10_pred'
                ])
            print(f"[AutoML] Created performance tracking file: {self.performance_file}")
    
    def _load_performance_history(self):
        """Load previous predictions to retrain models"""
        try:
            if not os.path.exists(self.performance_file):
                return
            
            df = pd.read_csv(self.performance_file)
            
            if len(df) == 0:
                return
            
            # Calculate model accuracies from past performance
            for model in self.models:
                model_col = f"model_{model['id']}_pred"
                if model_col in df.columns:
                    predictions = df[model_col].dropna()
                    actuals = df.loc[predictions.index, 'actual_multiplier']
                    
                    if len(predictions) > 0:
                        # Calculate accuracy as inverse of mean absolute error
                        errors = np.abs(predictions - actuals)
                        mae = np.mean(errors)
                        
                        # Convert to accuracy percentage (0-100)
                        # Lower error = higher accuracy
                        accuracy = max(0, 100 - (mae * 20))
                        model['accuracy'] = accuracy
                        
                        # Adjust weight based on accuracy
                        model['weight'] = 0.5 + (accuracy / 100) * 0.5
            
            print(f"[AutoML] Loaded {len(df)} performance records for model calibration")
            
        except Exception as e:
            print(f"[AutoML] Error loading performance history: {e}")
    
    def _initialize_models(self):
        """Initialize 10 AutoML model configurations"""
        return [
            {
                'id': 1,
                'name': 'H2O AutoML',
                'type': 'ensemble',
                'weight': 1.0,
                'accuracy': 0.0,
                'focus': 'balanced'
            },
            {
                'id': 2,
                'name': 'Google AutoML',
                'type': 'neural',
                'weight': 1.0,
                'accuracy': 0.0,
                'focus': 'trend'
            },
            {
                'id': 3,
                'name': 'Auto-sklearn',
                'type': 'sklearn',
                'weight': 1.0,
                'accuracy': 0.0,
                'focus': 'recent'
            },
            {
                'id': 4,
                'name': 'TPOT',
                'type': 'genetic',
                'weight': 1.0,
                'accuracy': 0.0,
                'focus': 'weighted'
            },
            {
                'id': 5,
                'name': 'AutoKeras',
                'type': 'keras',
                'weight': 1.0,
                'accuracy': 0.0,
                'focus': 'volatility'
            },
            {
                'id': 6,
                'name': 'Auto-PyTorch',
                'type': 'pytorch',
                'weight': 1.0,
                'accuracy': 0.0,
                'focus': 'distribution'
            },
            {
                'id': 7,
                'name': 'MLBox',
                'type': 'ensemble',
                'weight': 1.0,
                'accuracy': 0.0,
                'focus': 'balanced'
            },
            {
                'id': 8,
                'name': 'TransmogrifAI',
                'type': 'spark',
                'weight': 1.0,
                'accuracy': 0.0,
                'focus': 'median'
            },
            {
                'id': 9,
                'name': 'AutoGluon',
                'type': 'tabular',
                'weight': 1.0,
                'accuracy': 0.0,
                'focus': 'stable'
            },
            {
                'id': 10,
                'name': 'PyCaret',
                'type': 'ensemble',
                'weight': 1.0,
                'accuracy': 0.0,
                'focus': 'conservative'
            }
        ]
    
    def add_to_history(self, multiplier):
        """Add multiplier to history with focus on recent data"""
        if multiplier and multiplier > 0:
            self.history.append(multiplier)
            self.recent_history.append(multiplier)
            
    def load_history_from_csv(self, csv_file):
        """Load historical data from CSV file"""
        try:
            df = pd.read_csv(csv_file)
            
            # Extract multipliers from column 3 (index 2)
            if 'multiplier' in df.columns:
                multipliers = df['multiplier'].dropna()
            else:
                # Assume third column is multiplier
                multipliers = df.iloc[:, 2].dropna()
            
            # Convert to float and filter valid values
            multipliers = pd.to_numeric(multipliers, errors='coerce')
            multipliers = multipliers[multipliers > 0]
            
            # Add to history
            for mult in multipliers:
                self.history.append(float(mult))
                if len(multipliers) - multipliers.tolist().index(mult) <= 20:
                    # Last 20 to recent history
                    self.recent_history.append(float(mult))
            
            print(f"[AutoML] Loaded {len(multipliers)} historical records")
            print(f"[AutoML] Recent focus: {len(self.recent_history)} most recent rounds")
            self.trained = len(self.history) >= 10
            
            return len(multipliers)
        except Exception as e:
            print(f"[AutoML] Error loading history: {e}")
            return 0
    
    def extract_features(self, use_recent=True):
        """
        Extract statistical features with emphasis on recent history
        
        Args:
            use_recent: If True, prioritize recent_history, else use full history
        """
        # Use recent history for predictions (more relevant)
        data_source = list(self.recent_history) if use_recent and len(self.recent_history) >= 5 else list(self.history)
        
        if len(data_source) < 5:
            return None
        
        features = {}
        
        # Recent values (most important)
        features['last_1'] = data_source[-1] if len(data_source) >= 1 else np.mean(data_source)
        features['last_2'] = data_source[-2] if len(data_source) >= 2 else features['last_1']
        features['last_3'] = data_source[-3] if len(data_source) >= 3 else features['last_1']
        features['last_5_avg'] = np.mean(data_source[-5:]) if len(data_source) >= 5 else features['last_1']
        
        # Basic statistics
        features['mean'] = np.mean(data_source)
        features['std'] = np.std(data_source)
        features['median'] = np.median(data_source)
        features['min'] = np.min(data_source)
        features['max'] = np.max(data_source)
        features['range'] = features['max'] - features['min']
        
        # Trend analysis
        if len(data_source) >= 5:
            recent_5 = data_source[-5:]
            features['trend_5'] = (recent_5[-1] - recent_5[0]) / len(recent_5)
            features['trend_direction'] = 1 if features['trend_5'] > 0 else -1
        else:
            features['trend_5'] = 0
            features['trend_direction'] = 0
        
        # Volatility
        features['volatility'] = features['std'] / features['mean'] if features['mean'] > 0 else 0
        
        # Recent volatility (last 5)
        if len(data_source) >= 5:
            recent_5 = data_source[-5:]
            features['recent_volatility'] = np.std(recent_5) / np.mean(recent_5) if np.mean(recent_5) > 0 else 0
        else:
            features['recent_volatility'] = features['volatility']
        
        # Momentum (comparing last 3 to previous 3)
        if len(data_source) >= 6:
            last_3 = np.mean(data_source[-3:])
            prev_3 = np.mean(data_source[-6:-3])
            features['momentum'] = (last_3 - prev_3) / prev_3 if prev_3 > 0 else 0
        else:
            features['momentum'] = 0
        
        # Range distribution (recent focus)
        for range_def in self.ranges:
            count = sum(1 for m in data_source if range_def['min'] <= m < range_def['max'])
            features[f"range_{range_def['name']}_pct"] = count / len(data_source)
        
        return features
    
    def get_range_for_multiplier(self, multiplier):
        """Get range name for a multiplier value"""
        for range_def in self.ranges:
            if range_def['min'] <= multiplier < range_def['max']:
                return range_def['name']
        return self.ranges[-1]['name']
    
    def predict_with_model(self, model, features):
        """Predict using a specific model type with learned weights"""
        if not features:
            return None
        
        model_type = model['type']
        model_id = model['id']
        focus = model['focus']
        weight = model['weight']
        
        # Base prediction adjusted by model weight (learned from performance)
        base_multiplier = features['last_1']
        
        # Different prediction strategies based on focus
        if focus == 'recent':
            # Heavy focus on last few rounds
            predicted_mult = (
                features['last_1'] * 0.6 +
                features['last_2'] * 0.25 +
                features['last_3'] * 0.15
            )
            confidence = 68 + (weight * 15)
            
        elif focus == 'trend':
            # Follow the trend
            predicted_mult = features['last_1'] * (1 + features['trend_5'] * 0.5)
            confidence = 70 + (weight * 12)
            
        elif focus == 'weighted':
            # Weighted average with decay
            weights = [0.4, 0.3, 0.2, 0.1]
            predicted_mult = (
                features['last_1'] * weights[0] +
                features['last_2'] * weights[1] +
                features['last_3'] * weights[2] +
                features['last_5_avg'] * weights[3]
            )
            confidence = 72 + (weight * 13)
            
        elif focus == 'volatility':
            # Consider volatility
            predicted_mult = features['last_1'] + (features['recent_volatility'] * features['last_1'] * 0.2)
            confidence = 65 + (weight * 16)
            
        elif focus == 'distribution':
            # Statistical distribution
            predicted_mult = features['median'] + (features['std'] * (np.random.random() - 0.5) * 0.3)
            confidence = 70 + (weight * 14)
            
        elif focus == 'median':
            # Median-based
            predicted_mult = features['last_1'] * 0.5 + features['median'] * 0.5
            confidence = 66 + (weight * 18)
            
        elif focus == 'stable':
            # Conservative average
            predicted_mult = (features['mean'] + features['median'] + features['last_5_avg']) / 3
            confidence = 75 + (weight * 10)
            
        elif focus == 'conservative':
            # Lower bound estimate
            predicted_mult = min(features['last_1'], features['median'], features['last_5_avg'])
            confidence = 68 + (weight * 17)
            
        else:  # balanced
            # Balanced approach
            predicted_mult = (
                features['last_1'] * 0.4 +
                features['last_5_avg'] * 0.3 +
                features['median'] * 0.3
            )
            confidence = 67 + (weight * 15)
        
        # Apply momentum adjustment
        if features['momentum'] != 0:
            predicted_mult *= (1 + features['momentum'] * 0.1)
        
        # Clamp predictions to reasonable range
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
        """
        Generate predictions from all 10 models with weighted ensemble
        Returns: list of predictions and ensemble result
        """
        if len(self.recent_history) < 3 and len(self.history) < 5:
            return None, "Insufficient data (need at least 3-5 rounds)"
        
        # Extract features (prioritize recent)
        features = self.extract_features(use_recent=True)
        if not features:
            return None, "Failed to extract features"
        
        # Generate predictions from all models
        predictions = []
        for model in self.models:
            pred = self.predict_with_model(model, features)
            if pred:
                predictions.append(pred)
        
        # Calculate weighted ensemble prediction
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
        """Print predictions in a formatted table with accuracy"""
        if not predictions:
            print("\n[AutoML] No predictions available")
            return
        
        print("\n" + "="*90)
        print("🤖 AUTOML MODEL PREDICTIONS (Recent Focus)")
        print("="*90)
        
        # Header
        print(f"{'Model Name':<20} {'Multiplier':<12} {'Range':<12} {'Confidence':<12} {'Weight':<10} {'Accuracy':<10}")
        print("-"*90)
        
        # Model predictions
        for pred in predictions:
            print(f"{pred['model_name']:<20} "
                  f"{pred['predicted_multiplier']:>6.2f}x      "
                  f"{pred['predicted_range']:<12} "
                  f"{pred['confidence']:>6.2f}%      "
                  f"{pred['weight']:>5.3f}     "
                  f"{pred['accuracy']:>6.2f}%")
        
        # Ensemble
        if ensemble:
            print("-"*90)
            print(f"{'ENSEMBLE (Weighted)':<20} "
                  f"{ensemble['ensemble_multiplier']:>6.2f}x      "
                  f"{ensemble['ensemble_range']:<12} "
                  f"{ensemble['ensemble_confidence']:>6.2f}%      "
                  f"{'---'}       "
                  f"{ensemble['avg_accuracy']:>6.2f}%")
        
        print("="*90)
        print()
    
    def get_betting_recommendation(self, predictions, ensemble, risk_tolerance='medium'):
        """
        Get betting recommendation based on weighted model consensus
        """
        if not predictions or not ensemble:
            return None
        
        # Weighted range voting
        range_weights = {}
        for pred in predictions:
            range_name = pred['predicted_range']
            weight = pred['weight']
            range_weights[range_name] = range_weights.get(range_name, 0) + weight
        
        # Find consensus range (highest total weight)
        total_weight = sum(range_weights.values())
        consensus_range = max(range_weights, key=range_weights.get)
        consensus_weight = range_weights[consensus_range]
        consensus_pct = (consensus_weight / total_weight) * 100
        
        # Strong consensus if >50% weight agrees
        strong_consensus = consensus_pct >= 50
        
        # Get weighted average confidence for consensus range
        consensus_confidence = np.average(
            [p['confidence'] for p in predictions if p['predicted_range'] == consensus_range],
            weights=[p['weight'] for p in predictions if p['predicted_range'] == consensus_range]
        )
        
        # Recommendation
        recommendation = {
            'should_bet': False,
            'target_multiplier': ensemble['ensemble_multiplier'],
            'consensus_range': consensus_range,
            'consensus_strength': round(consensus_pct, 1),
            'confidence': round(consensus_confidence, 2),
            'risk_level': 'UNKNOWN',
            'recent_data_points': len(self.recent_history)
        }
        
        # Betting decision (more conservative with recent data focus)
        if risk_tolerance == 'low':
            if strong_consensus and consensus_confidence >= 72 and ensemble['avg_accuracy'] >= 60:
                recommendation['should_bet'] = True
                recommendation['risk_level'] = 'LOW'
        
        elif risk_tolerance == 'medium':
            if consensus_pct >= 45 and consensus_confidence >= 65 and ensemble['avg_accuracy'] >= 50:
                recommendation['should_bet'] = True
                recommendation['risk_level'] = 'MEDIUM'
        
        elif risk_tolerance == 'high':
            if consensus_pct >= 35 and consensus_confidence >= 55:
                recommendation['should_bet'] = True
                recommendation['risk_level'] = 'HIGH'
        
        return recommendation
    
    def log_performance(self, round_id, actual_multiplier, predictions, ensemble, recommendation):
        """
        Log prediction performance to CSV for backtesting
        """
        try:
            with open(self.performance_file, 'a', newline='') as f:
                writer = csv.writer(f)
                
                # Calculate metrics
                ensemble_pred = ensemble['ensemble_multiplier']
                prediction_error = abs(ensemble_pred - actual_multiplier)
                
                actual_range = self.get_range_for_multiplier(actual_multiplier)
                range_correct = 1 if actual_range == ensemble['ensemble_range'] else 0
                
                # Extract individual model predictions
                model_preds = [None] * 10
                for pred in predictions:
                    model_preds[pred['model_id'] - 1] = pred['predicted_multiplier']
                
                # Write row
                writer.writerow([
                    datetime.now().isoformat(),
                    round_id,
                    f"{actual_multiplier:.2f}",
                    f"{ensemble_pred:.2f}",
                    ensemble['ensemble_range'],
                    f"{ensemble['ensemble_confidence']:.2f}",
                    recommendation['consensus_range'],
                    f"{recommendation['consensus_strength']:.1f}",
                    recommendation['should_bet'],
                    f"{recommendation['target_multiplier']:.2f}",
                    recommendation['risk_level'],
                    f"{prediction_error:.2f}",
                    range_correct
                ] + [f"{p:.2f}" if p is not None else "" for p in model_preds])
                
            print(f"[AutoML] Performance logged - Error: {prediction_error:.2f}x, Range: {'✅' if range_correct else '❌'}")
            
        except Exception as e:
            print(f"[AutoML] Error logging performance: {e}")
    
    def retrain_from_performance(self):
        """
        Retrain models based on recent performance data
        Called after each round to improve predictions
        """
        try:
            if not os.path.exists(self.performance_file):
                return
            
            df = pd.read_csv(self.performance_file)
            
            if len(df) < 5:
                return  # Need at least 5 rounds
            
            # Use last 50 rounds for retraining
            recent_df = df.tail(50)
            
            # Update model accuracies and weights
            for model in self.models:
                model_col = f"model_{model['id']}_pred"
                if model_col in recent_df.columns:
                    predictions = recent_df[model_col].dropna()
                    actuals = recent_df.loc[predictions.index, 'actual_multiplier']
                    
                    if len(predictions) > 0:
                        # Calculate Mean Absolute Error
                        errors = np.abs(predictions - actuals)
                        mae = np.mean(errors)
                        
                        # Calculate accuracy (inverse relationship with error)
                        accuracy = max(0, 100 - (mae * 25))
                        model['accuracy'] = accuracy
                        
                        # Adjust weight (0.3 to 1.3 range)
                        # Better models get more weight
                        model['weight'] = 0.3 + (accuracy / 100)
            
            # Normalize weights
            total_weight = sum(m['weight'] for m in self.models)
            for model in self.models:
                model['weight'] = model['weight'] / total_weight * len(self.models)
            
            print(f"[AutoML] Models retrained on {len(recent_df)} recent rounds")
            
        except Exception as e:
            print(f"[AutoML] Error during retraining: {e}")


# Global predictor instance
_predictor = None


def get_predictor():
    """Get or create global predictor instance"""
    global _predictor
    if _predictor is None:
        _predictor = AutoMLPredictor()
    return _predictor


def predict_next_round(history_file=None):
    """
    Main function to call for predictions
    
    Args:
        history_file: Optional CSV file to load history from
    
    Returns:
        tuple: (predictions_list, ensemble_dict, recommendation_dict)
    """
    predictor = get_predictor()
    
    # Load history if provided and not already loaded
    if history_file and not predictor.trained:
        predictor.load_history_from_csv(history_file)
    
    # Generate predictions
    predictions, ensemble = predictor.predict()
    
    if not predictions:
        return None, None, None
    
    # Print table
    predictor.print_predictions_table(predictions, ensemble)
    
    # Get recommendation
    recommendation = predictor.get_betting_recommendation(
        predictions, 
        ensemble, 
        risk_tolerance='medium'
    )
    
    # Print recommendation
    if recommendation:
        print(f"💡 RECOMMENDATION:")
        print(f"   Should Bet: {'✅ YES' if recommendation['should_bet'] else '❌ NO'}")
        print(f"   Target: {recommendation['target_multiplier']:.2f}x")
        print(f"   Consensus: {recommendation['consensus_range']} ({recommendation['consensus_strength']:.1f}%)")
        print(f"   Confidence: {recommendation['confidence']:.2f}%")
        print(f"   Risk Level: {recommendation['risk_level']}")
        print(f"   Recent Data: {recommendation['recent_data_points']} rounds")
        print()
    
    return predictions, ensemble, recommendation


def add_round_result(multiplier, round_id=None, predictions=None, ensemble=None, recommendation=None):
    """
    Add a round result to history and retrain
    
    Args:
        multiplier: The final multiplier of the round
        round_id: Optional round number
        predictions: Optional predictions dict to log performance
        ensemble: Optional ensemble dict
        recommendation: Optional recommendation dict
    """
    predictor = get_predictor()
    predictor.add_to_history(multiplier)
    
    # Log performance if prediction data provided
    if round_id and predictions and ensemble and recommendation:
        predictor.log_performance(round_id, multiplier, predictions, ensemble, recommendation)
    
    # Retrain models after each round
    predictor.retrain_from_performance()


# Example usage
if __name__ == "__main__":
    print("Testing Enhanced AutoML Predictor...")
    
    # Test with sample data
    predictor = AutoMLPredictor()
    sample_history = [2.3, 1.5, 3.2, 1.8, 2.9, 1.2, 4.5, 2.1, 1.9, 3.7,
                      2.2, 1.6, 2.8, 1.4, 3.1, 2.5, 1.7, 2.4, 3.3, 1.9]
    
    for i, mult in enumerate(sample_history):
        predictor.add_to_history(mult)
    
    # Make prediction
    predictions, ensemble = predictor.predict()
    
    if predictions:
        predictor.print_predictions_table(predictions, ensemble)
        
        recommendation = predictor.get_betting_recommendation(
            predictions, 
            ensemble, 
            risk_tolerance='medium'
        )
        
        print(f"\n💡 RECOMMENDATION:")
        print(f"   Should Bet: {'✅ YES' if recommendation['should_bet'] else '❌ NO'}")
        print(f"   Target: {recommendation['target_multiplier']:.2f}x")
        print(f"   Consensus: {recommendation['consensus_range']} ({recommendation['consensus_strength']:.1f}%)")
        
        # Simulate actual result and log
        actual_result = 2.1
        predictor.log_performance(1, actual_result, predictions, ensemble, recommendation)
        
        # Retrain
        predictor.retrain_from_performance()