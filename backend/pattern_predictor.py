"""
Pattern Predictor - Detects low-to-high sequences and predicts high multiplier rounds
"""

import time
from datetime import datetime, timedelta
from collections import deque

class PatternPredictor:
    """Predicts high multiplier sequences after low rounds."""
    
    def __init__(self, history_tracker):
        self.history_tracker = history_tracker
        self.pattern_buffer = deque(maxlen=100)  # Store recent patterns
        self.last_notification = 0
        self.notification_cooldown = 300  # 5 minutes between notifications
        
        # Validation tracking
        self.active_predictions = []  # Track sent predictions
        self.validation_results = []  # Store validation results
        
    def analyze_hourly_patterns(self):
        """Analyze multiplier patterns in different timeframes."""
        timeframes = {
            '15min': 90,   # ~90 rounds in 15 minutes
            '30min': 180,  # ~180 rounds in 30 minutes  
            '1hour': 360   # ~360 rounds in 1 hour
        }
        
        patterns = {}
        for name, rounds in timeframes.items():
            recent = self.history_tracker.get_recent_multipliers(rounds)
            if len(recent) >= rounds:
                patterns[name] = self._analyze_sequence(recent)
        
        return patterns
    
    def _analyze_sequence(self, multipliers):
        """Analyze a sequence for low-to-high patterns."""
        low_count = sum(1 for m in multipliers if m < 2.0)
        high_count = sum(1 for m in multipliers if m >= 5.0)
        very_high_count = sum(1 for m in multipliers if m >= 10.0)
        
        # Find consecutive low streaks
        low_streaks = []
        current_streak = 0
        for m in multipliers:
            if m < 2.0:
                current_streak += 1
            else:
                if current_streak >= 5:
                    low_streaks.append(current_streak)
                current_streak = 0
        
        return {
            'low_count': low_count,
            'high_count': high_count,
            'very_high_count': very_high_count,
            'low_streaks': low_streaks,
            'avg_multiplier': sum(multipliers) / len(multipliers),
            'max_multiplier': max(multipliers)
        }
    
    def predict_high_sequence(self):
        """Predict if high multiplier sequence is coming."""
        recent_50 = self.history_tracker.get_recent_multipliers(50)
        if len(recent_50) < 50:
            return {'prediction': False, 'confidence': 0, 'reason': 'Insufficient data'}
        
        # Pattern: 8+ low rounds in last 15 rounds
        last_15 = recent_50[-15:]
        low_in_last_15 = sum(1 for m in last_15 if m < 2.0)
        
        # Pattern: No high multiplier in last 30 rounds
        last_30 = recent_50[-30:]
        high_in_last_30 = sum(1 for m in last_30 if m >= 5.0)
        
        # Calculate prediction confidence
        confidence = 0
        reasons = []
        
        if low_in_last_15 >= 8:
            confidence += 40
            reasons.append(f"Extreme cold: {low_in_last_15}/15 low rounds")
        
        if high_in_last_30 == 0:
            confidence += 30
            reasons.append("No high multipliers in 30 rounds")
        
        if low_in_last_15 >= 10:
            confidence += 20
            reasons.append("Critical low streak detected")
        
        # Check historical patterns
        hourly_patterns = self.analyze_hourly_patterns()
        if '1hour' in hourly_patterns:
            hour_data = hourly_patterns['1hour']
            if hour_data['high_count'] <= 2:  # Very few high multipliers in hour
                confidence += 10
                reasons.append("Hourly high deficit")
        
        should_predict = confidence >= 60
        
        return {
            'prediction': should_predict,
            'confidence': min(confidence, 95),
            'reason': ' | '.join(reasons) if reasons else 'No strong pattern',
            'low_in_15': low_in_last_15,
            'high_in_30': high_in_last_30,
            'patterns': hourly_patterns
        }
    
    def start_prediction_tracking(self, prediction_data):
        """Start tracking a prediction for validation."""
        prediction_record = {
            'timestamp': time.time(),
            'confidence': prediction_data['confidence'],
            'reason': prediction_data['reason'],
            'high_sequence_started': None,
            'high_sequence_ended': None,
            'max_multiplier_achieved': 0,
            'validation_complete': False
        }
        self.active_predictions.append(prediction_record)
        return len(self.active_predictions) - 1  # Return index
    
    def validate_predictions(self, current_multiplier):
        """Validate active predictions and send results."""
        current_time = time.time()
        
        for i, prediction in enumerate(self.active_predictions):
            if prediction['validation_complete']:
                continue
                
            # Check if high sequence started (multiplier >= 5.0)
            if current_multiplier >= 5.0 and prediction['high_sequence_started'] is None:
                prediction['high_sequence_started'] = current_time
                prediction['max_multiplier_achieved'] = current_multiplier
            
            # Update max multiplier during sequence
            if prediction['high_sequence_started'] and current_multiplier > prediction['max_multiplier_achieved']:
                prediction['max_multiplier_achieved'] = current_multiplier
            
            # Check if sequence ended (back to low multipliers)
            if (prediction['high_sequence_started'] and 
                prediction['high_sequence_ended'] is None and 
                current_multiplier < 3.0):
                prediction['high_sequence_ended'] = current_time
            
            # Complete validation after 30 minutes or if sequence ended
            time_elapsed = current_time - prediction['timestamp']
            if (time_elapsed > 1800 or  # 30 minutes
                (prediction['high_sequence_started'] and prediction['high_sequence_ended'])):
                
                self._complete_validation(prediction)
                prediction['validation_complete'] = True
    
    def _complete_validation(self, prediction):
        """Complete validation and send results."""
        result = {
            'prediction_time': datetime.fromtimestamp(prediction['timestamp']).strftime('%H:%M:%S'),
            'confidence': prediction['confidence'],
            'success': prediction['high_sequence_started'] is not None,
            'max_multiplier': prediction['max_multiplier_achieved'],
            'start_delay': None,
            'duration': None
        }
        
        if prediction['high_sequence_started']:
            start_delay = (prediction['high_sequence_started'] - prediction['timestamp']) / 60  # minutes
            result['start_delay'] = round(start_delay, 1)
            
            if prediction['high_sequence_ended']:
                duration = (prediction['high_sequence_ended'] - prediction['high_sequence_started']) / 60
                result['duration'] = round(duration, 1)
        
        self.validation_results.append(result)
        return result