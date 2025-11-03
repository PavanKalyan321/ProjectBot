import numpy as np
import pandas as pd
from collections import deque
from datetime import datetime
import warnings
import os
import csv
warnings.filterwarnings('ignore')


class AutoMLPredictor:
    
    def __init__(self, performance_file='bot_automl_performance.csv', selected_models=None):
        self.selected_models = selected_models or list(range(1, 17))
        self.models = self._initialize_models()
        self.history = deque(maxlen=100)
        self.recent_history = deque(maxlen=20)
        self.trained = False
        self.performance_file = performance_file
        
        self.ranges = [
            {'name': '1.0-1.5x', 'min': 1.0, 'max': 1.5},
            {'name': '1.5-2.0x', 'min': 1.5, 'max': 2.0},
            {'name': '2.0-2.5x', 'min': 2.0, 'max': 2.5},
            {'name': '2.5-3.0x', 'min': 2.5, 'max': 3.0},
            {'name': '3.0+x', 'min': 3.0, 'max': 100.0}
        ]
        
        self._initialize_performance_file()
        self._load_performance_history()
        
    def _initialize_performance_file(self):
        if not os.path.exists(self.performance_file):
            with open(self.performance_file, 'w', newline='') as f:
                writer = csv.writer(f)
                header = [
                    'timestamp', 'round_id', 'actual_multiplier',
                    'ensemble_prediction', 'ensemble_range', 'ensemble_confidence',
                    'consensus_range', 'consensus_strength',
                    'recommendation_should_bet', 'recommendation_target',
                    'recommendation_risk', 'prediction_error', 'range_correct'
                ]
                header.extend([f'model_{i}_pred' for i in range(1, 17)])
                writer.writerow(header)
            print(f"[AutoML] Created performance tracking file: {self.performance_file}")
    
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
        
        for range_def in self.ranges:
            count = sum(1 for m in data_source if range_def['min'] <= m < range_def['max'])
            features[f"range_{range_def['name']}_pct"] = count / len(data_source)
        
        return features
    
    def get_range_for_multiplier(self, multiplier):
        for range_def in self.ranges:
            if range_def['min'] <= multiplier < range_def['max']:
                return range_def['name']
        return self.ranges[-1]['name']
    
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
        
        recommendation = {
            'should_bet': False,
            'target_multiplier': ensemble['ensemble_multiplier'],
            'consensus_range': consensus_range,
            'consensus_strength': round(consensus_pct, 1),
            'confidence': round(consensus_confidence, 2),
            'risk_level': 'UNKNOWN',
            'recent_data_points': len(self.recent_history)
        }
        
        if risk_tolerance == 'low':
            if strong_consensus and consensus_confidence >= 70 and ensemble['avg_accuracy'] >= 5:
                recommendation['should_bet'] = True
                recommendation['risk_level'] = 'LOW'

        elif risk_tolerance == 'medium':
            if consensus_pct >= 35 and consensus_confidence >= 60:
                recommendation['should_bet'] = True
                recommendation['risk_level'] = 'MEDIUM'

        elif risk_tolerance == 'high':
            if consensus_pct >= 30 and consensus_confidence >= 55:
                recommendation['should_bet'] = True
                recommendation['risk_level'] = 'HIGH'
        
        return recommendation
    
    def log_performance(self, round_id, actual_multiplier, predictions, ensemble, recommendation):
        try:
            with open(self.performance_file, 'a', newline='') as f:
                writer = csv.writer(f)
                
                ensemble_pred = ensemble['ensemble_multiplier']
                prediction_error = abs(ensemble_pred - actual_multiplier)
                
                actual_range = self.get_range_for_multiplier(actual_multiplier)
                range_correct = 1 if actual_range == ensemble['ensemble_range'] else 0
                
                model_preds = [None] * 16
                for pred in predictions:
                    model_preds[pred['model_id'] - 1] = pred['predicted_multiplier']
                
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
        try:
            if not os.path.exists(self.performance_file):
                return
            
            df = pd.read_csv(self.performance_file)
            
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
            
            total_weight = sum(m['weight'] for m in self.models)
            for model in self.models:
                model['weight'] = model['weight'] / total_weight * len(self.models)
            
            print(f"[AutoML] Models retrained on {len(recent_df)} recent rounds")
            
        except Exception as e:
            print(f"[AutoML] Error during retraining: {e}")


_predictor = None

def get_predictor(selected_models=None):
    global _predictor
    if _predictor is None:
        _predictor = AutoMLPredictor(selected_models=selected_models)
    return _predictor

def predict_next_round(history_file=None):
    predictor = get_predictor()
    if history_file and not predictor.trained:
        predictor.load_history_from_csv(history_file)
    predictions, ensemble = predictor.predict()
    if not predictions:
        return None, None, None
    predictor.print_predictions_table(predictions, ensemble)
    recommendation = predictor.get_betting_recommendation(
        predictions,
        ensemble,
        risk_tolerance='medium'
    )
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
    predictor = get_predictor()
    predictor.add_to_history(multiplier)
    if round_id and predictions and ensemble and recommendation:
        predictor.log_performance(round_id, multiplier, predictions, ensemble, recommendation)
    predictor.retrain_from_performance()