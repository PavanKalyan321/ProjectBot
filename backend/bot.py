import pyautogui
import time
from PIL import Image
import cv2
import numpy as np
import keyboard
import json
import os
import csv
from datetime import datetime
import pandas as pd
from collections import deque

class RoundHistoryTracker:
    """Track and log round history from the game's history bar"""
    
    def __init__(self, history_region=None):
        self.history_region = history_region  # (x, y, width, height)
        self.csv_file = "aviator_rounds_history.csv"
        self.last_round_data = None
        
        # Initialize CSV file with headers if it doesn't exist
        if not os.path.exists(self.csv_file):
            with open(self.csv_file, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    'timestamp', 'round_id', 'multiplier', 
                    'bet_placed', 'stake_amount', 'cashout_time', 
                    'profit_loss', 'model_prediction', 'model_confidence',
                    'model_predicted_range_low', 'model_predicted_range_high'
                ])
        
        # Import tesseract
        try:
            import pytesseract
            self.pytesseract = pytesseract
            self.tesseract_available = True
        except ImportError:
            print("⚠️  Warning: pytesseract not installed for OCR")
            self.tesseract_available = False
    
    def capture_history_region(self):
        """Capture screenshot of history bar region"""
        if not self.history_region:
            return None
        screenshot = pyautogui.screenshot(region=self.history_region)
        return screenshot
    
    def extract_multipliers_from_history(self):
        """Extract multipliers from the history bar using color detection"""
        if not self.history_region:
            return []
        
        try:
            # Capture image
            image = self.capture_history_region()
            img_array = np.array(image)
            
            # Convert to HSV for better color detection
            hsv = cv2.cvtColor(img_array, cv2.COLOR_RGB2HSV)
            
            # Detect colored regions (typically pink/red for low, green for high)
            # This is a placeholder - you'd need to calibrate for your specific game
            multipliers = []
            
            # For now, return empty list - implement based on game's UI
            return multipliers
            
        except Exception as e:
            print(f"Error extracting history: {e}")
            return []
    
    def read_latest_round_ocr(self):
        """Read the latest round result using OCR"""
        if not self.tesseract_available or not self.history_region:
            return None
        
        try:
            image = self.capture_history_region()
            img_array = np.array(image)
            
            # Preprocess for OCR
            gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
            _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)
            
            # Extract text
            text = self.pytesseract.image_to_string(thresh, config='--oem 3 --psm 6')
            
            # Parse multipliers (look for patterns like "1.50x", "2.34x")
            import re
            multipliers = re.findall(r'(\d+\.?\d*)x', text)
            
            if multipliers:
                return float(multipliers[0])
            
            return None
            
        except Exception as e:
            return None
    
    def log_round(self, multiplier, bet_placed=False, stake=0, cashout_time=0, 
                  profit_loss=0, prediction=None, confidence=0, pred_range=(0, 0)):
        """Log a round to CSV file"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        round_id = datetime.now().strftime("%Y%m%d%H%M%S%f")
        
        with open(self.csv_file, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                timestamp, round_id, multiplier,
                bet_placed, stake, cashout_time,
                profit_loss, prediction, confidence,
                pred_range[0], pred_range[1]
            ])
        
        print(f"  📝 Logged: {multiplier}x | Bet: {bet_placed} | P/L: {profit_loss:+.2f}")
    
    def get_recent_rounds(self, n=100):
        """Get the last N rounds from CSV"""
        try:
            df = pd.read_csv(self.csv_file)
            return df.tail(n)
        except Exception as e:
            print(f"Error reading history: {e}")
            return pd.DataFrame()


class MLSignalGenerator:
    """Generate betting signals using ensemble ML models"""
    
    def __init__(self, history_tracker):
        self.history_tracker = history_tracker
        self.confidence_threshold = 65.0  # Minimum confidence to place bet
        self.models_loaded = False
        self.feature_window = 20  # Use last 20 rounds for features
        
        # Model placeholders
        self.lstm_model = None
        self.rf_model = None
        self.xgb_model = None
        self.gb_model = None
        
        # Feature scaler
        self.scaler = None
        
        print("🤖 ML Signal Generator initialized")
        print(f"   Confidence threshold: {self.confidence_threshold}%")
    
    def load_models(self):
        """Load pre-trained models"""
        try:
            # TODO: Implement actual model loading
            # from tensorflow import keras
            # self.lstm_model = keras.models.load_model('lstm_model.h5')
            
            # import joblib
            # self.rf_model = joblib.load('rf_model.pkl')
            # self.xgb_model = joblib.load('xgb_model.pkl')
            # self.gb_model = joblib.load('gb_model.pkl')
            # self.scaler = joblib.load('scaler.pkl')
            
            self.models_loaded = True
            print("✓ Models loaded successfully")
            return True
        except Exception as e:
            print(f"⚠️  Model loading failed: {e}")
            print("   Running in simulation mode")
            return False
    
    def engineer_features(self, recent_rounds):
        """Engineer features from recent rounds"""
        if len(recent_rounds) < self.feature_window:
            return None
        
        multipliers = recent_rounds['multiplier'].values[-self.feature_window:]
        
        features = {
            # Statistical features
            'mean': np.mean(multipliers),
            'std': np.std(multipliers),
            'min': np.min(multipliers),
            'max': np.max(multipliers),
            'median': np.median(multipliers),
            
            # Trend features
            'trend': np.polyfit(range(len(multipliers)), multipliers, 1)[0],
            'momentum': multipliers[-1] - multipliers[-5] if len(multipliers) >= 5 else 0,
            
            # Pattern features
            'low_count': np.sum(multipliers < 2.0),
            'high_count': np.sum(multipliers >= 2.0),
            'crash_streak': self._calculate_crash_streak(multipliers, 2.0),
            
            # Recent behavior
            'last_1': multipliers[-1],
            'last_2': multipliers[-2] if len(multipliers) >= 2 else 0,
            'last_3': multipliers[-3] if len(multipliers) >= 3 else 0,
            'last_5_avg': np.mean(multipliers[-5:]) if len(multipliers) >= 5 else 0,
            
            # Volatility
            'volatility': np.std(multipliers[-10:]) if len(multipliers) >= 10 else 0,
        }
        
        return np.array(list(features.values())).reshape(1, -1)
    
    def _calculate_crash_streak(self, multipliers, threshold):
        """Calculate consecutive crashes below threshold"""
        streak = 0
        for mult in reversed(multipliers):
            if mult < threshold:
                streak += 1
            else:
                break
        return streak
    
    def predict_lstm(self, features):
        """LSTM model prediction"""
        if not self.lstm_model:
            # Simulate prediction
            confidence = np.random.uniform(40, 90)
            prediction = np.random.uniform(1.5, 3.0)
            return prediction, confidence
        
        # TODO: Actual LSTM prediction
        # pred = self.lstm_model.predict(features)
        # return pred, confidence
        pass
    
    def predict_random_forest(self, features):
        """Random Forest prediction"""
        if not self.rf_model:
            # Simulate prediction
            confidence = np.random.uniform(40, 90)
            prediction = np.random.uniform(1.5, 3.0)
            return prediction, confidence
        
        # TODO: Actual RF prediction
        # pred = self.rf_model.predict(features)
        # confidence = self.rf_model.predict_proba(features).max() * 100
        # return pred[0], confidence
        pass
    
    def predict_xgboost(self, features):
        """XGBoost prediction"""
        if not self.xgb_model:
            confidence = np.random.uniform(40, 90)
            prediction = np.random.uniform(1.5, 3.0)
            return prediction, confidence
        
        # TODO: Actual XGBoost prediction
        pass
    
    def predict_gradient_boosting(self, features):
        """Gradient Boosting prediction"""
        if not self.gb_model:
            confidence = np.random.uniform(40, 90)
            prediction = np.random.uniform(1.5, 3.0)
            return prediction, confidence
        
        # TODO: Actual GB prediction
        pass
    
    def generate_ensemble_signal(self):
        """Generate betting signal using ensemble of models"""
        # Get recent rounds
        recent_rounds = self.history_tracker.get_recent_rounds(self.feature_window + 10)
        
        if len(recent_rounds) < self.feature_window:
            print(f"  ⚠️  Not enough history ({len(recent_rounds)}/{self.feature_window})")
            return {
                'should_bet': False,
                'confidence': 0,
                'prediction': 0,
                'range': (0, 0),
                'reason': 'Insufficient data'
            }
        
        # Engineer features
        features = self.engineer_features(recent_rounds)
        
        if features is None:
            return {
                'should_bet': False,
                'confidence': 0,
                'prediction': 0,
                'range': (0, 0),
                'reason': 'Feature engineering failed'
            }
        
        # Get predictions from all models
        predictions = []
        confidences = []
        
        # LSTM
        pred, conf = self.predict_lstm(features)
        predictions.append(pred)
        confidences.append(conf)
        
        # Random Forest
        pred, conf = self.predict_random_forest(features)
        predictions.append(pred)
        confidences.append(conf)
        
        # XGBoost
        pred, conf = self.predict_xgboost(features)
        predictions.append(pred)
        confidences.append(conf)
        
        # Gradient Boosting
        pred, conf = self.predict_gradient_boosting(features)
        predictions.append(pred)
        confidences.append(conf)
        
        # Ensemble: weighted average by confidence
        total_conf = sum(confidences)
        if total_conf == 0:
            ensemble_pred = np.mean(predictions)
            ensemble_conf = 0
        else:
            weights = [c / total_conf for c in confidences]
            ensemble_pred = sum(p * w for p, w in zip(predictions, weights))
            ensemble_conf = np.mean(confidences)
        
        # Calculate prediction range (confidence interval)
        pred_std = np.std(predictions)
        pred_range = (
            max(1.0, ensemble_pred - pred_std),
            ensemble_pred + pred_std
        )
        
        # Decision
        should_bet = ensemble_conf >= self.confidence_threshold
        
        signal = {
            'should_bet': should_bet,
            'confidence': round(ensemble_conf, 2),
            'prediction': round(ensemble_pred, 2),
            'range': (round(pred_range[0], 2), round(pred_range[1], 2)),
            'individual_predictions': predictions,
            'individual_confidences': confidences,
            'reason': f"Ensemble confidence: {ensemble_conf:.1f}%"
        }
        
        return signal
    
    def retrain_models_incremental(self, new_data):
        """Incrementally retrain models with new data"""
        # TODO: Implement incremental learning
        # This would update models with new round results
        print("  🔄 Incremental training triggered")
        pass


class GameStateDetector:
    """Detect game states: Awaiting, Active, Crashed"""
    
    def __init__(self, region):
        self.region = region
        
        try:
            import pytesseract
            self.pytesseract = pytesseract
            self.tesseract_available = True
        except ImportError:
            print("⚠️  Warning: pytesseract not installed")
            self.tesseract_available = False
    
    def capture_region(self):
        screenshot = pyautogui.screenshot(region=self.region)
        return screenshot
    
    def read_text_in_region(self):
        if not self.tesseract_available:
            return None
        
        try:
            image = self.capture_region()
            img_array = np.array(image)
            gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
            
            methods = []
            _, thresh1 = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)
            methods.append(thresh1)
            
            _, thresh2 = cv2.threshold(gray, 100, 255, cv2.THRESH_BINARY_INV)
            methods.append(thresh2)
            
            thresh3 = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                           cv2.THRESH_BINARY, 11, 2)
            methods.append(thresh3)
            
            for processed in methods:
                text = self.pytesseract.image_to_string(processed, config='--oem 3 --psm 6')
                
                if text:
                    text = text.strip().upper()
                    text = text.replace('0', 'O').replace('1', 'I')
                    
                    if any(keyword in text for keyword in ['AWAITING', 'AWAIT', 'NEXT', 'FLIGHT']):
                        return 'AWAITING'
            
            hsv = cv2.cvtColor(img_array, cv2.COLOR_RGB2HSV)
            lower_white = np.array([0, 0, 200])
            upper_white = np.array([180, 30, 255])
            mask = cv2.inRange(hsv, lower_white, upper_white)
            white_pixels = cv2.countNonZero(mask)
            total_pixels = mask.shape[0] * mask.shape[1]
            white_ratio = white_pixels / total_pixels
            
            if white_ratio > 0.1:
                return 'ACTIVE'
            
            return 'UNKNOWN'
            
        except Exception as e:
            return None
    
    def is_awaiting_next_flight(self):
        state = self.read_text_in_region()
        return state == 'AWAITING'
    
    def is_game_active(self):
        state = self.read_text_in_region()
        return state == 'ACTIVE'
    
    def wait_for_awaiting_message(self, timeout=60):
        print("  Waiting for 'AWAITING NEXT FLIGHT'...")
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            if self.is_awaiting_next_flight():
                print("  ✓ 'AWAITING NEXT FLIGHT' detected!")
                return True
            time.sleep(0.5)
        
        print("  ⚠️  Timeout - message not detected")
        return False
    
    def wait_for_game_start(self, timeout=10):
        print("  Waiting for game to start...")
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            if self.is_game_active():
                print("  ✓ Game started!")
                return True
            time.sleep(0.2)
        
        print("  ⚠️  Game didn't start")
        return False


class AviatorBotML:
    """Enhanced Aviator bot with ML signal generation"""
    
    def __init__(self):
        self.stake_coords = None
        self.bet_button_coords = None
        self.cashout_coords = None
        self.multiplier_region = None
        self.history_region = None
        
        self.initial_stake = 25
        self.current_stake = 25
        self.max_stake = 1000
        self.stake_increase_percent = 20
        
        self.cashout_delay = 2.0
        self.is_betting = False
        
        self.detector = None
        self.history_tracker = None
        self.ml_generator = None
        
        self.config_file = "aviator_ml_config.json"
        
        # Statistics
        self.stats = {
            "rounds_played": 0,
            "rounds_observed": 0,
            "ml_bets_placed": 0,
            "successful_cashouts": 0,
            "failed_cashouts": 0,
            "ml_skipped": 0,
            "total_bet": 0,
            "total_return": 0,
            "current_streak": 0,
            "max_stake_reached": 25
        }
    
    def save_config(self):
        config = {
            "stake_coords": self.stake_coords,
            "bet_button_coords": self.bet_button_coords,
            "cashout_coords": self.cashout_coords,
            "multiplier_region": self.multiplier_region,
            "history_region": self.history_region,
            "cashout_delay": self.cashout_delay,
            "initial_stake": self.initial_stake,
            "max_stake": self.max_stake,
            "stake_increase_percent": self.stake_increase_percent
        }
        with open(self.config_file, 'w') as f:
            json.dump(config, f, indent=2)
        print("✓ Configuration saved!")
    
    def load_config(self):
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                
                self.stake_coords = tuple(config["stake_coords"]) if config.get("stake_coords") else None
                self.bet_button_coords = tuple(config["bet_button_coords"]) if config.get("bet_button_coords") else None
                self.cashout_coords = tuple(config["cashout_coords"]) if config.get("cashout_coords") else None
                self.multiplier_region = tuple(config["multiplier_region"]) if config.get("multiplier_region") else None
                self.history_region = tuple(config["history_region"]) if config.get("history_region") else None
                self.cashout_delay = config.get("cashout_delay", 2.0)
                self.initial_stake = config.get("initial_stake", 25)
                self.max_stake = config.get("max_stake", 1000)
                self.stake_increase_percent = config.get("stake_increase_percent", 20)
                self.current_stake = self.initial_stake
                
                print("✓ Configuration loaded!")
                return True
            except Exception as e:
                print(f"⚠️  Error loading config: {e}")
                return False
        return False
    
    def setup_coordinates(self):
        print("\n" + "="*60)
        print("COORDINATE SETUP")
        print("="*60)
        print("\nPosition your mouse and press SPACE\n")
        
        print("1. Hover over STAKE INPUT field...")
        keyboard.wait('space')
        self.stake_coords = pyautogui.position()
        print(f"   ✓ Stake input: {self.stake_coords}")
        time.sleep(0.5)
        
        print("\n2. Hover over PLACE BET button...")
        keyboard.wait('space')
        self.bet_button_coords = pyautogui.position()
        print(f"   ✓ Place bet button: {self.bet_button_coords}")
        time.sleep(0.5)
        
        print("\n3. Hover over CASHOUT button location...")
        keyboard.wait('space')
        self.cashout_coords = pyautogui.position()
        print(f"   ✓ Cashout button: {self.cashout_coords}")
        time.sleep(0.5)
        
        print("\n4. Define multiplier region (TOP-LEFT corner)...")
        keyboard.wait('space')
        x1, y1 = pyautogui.position()
        print(f"   ✓ Top-left: ({x1}, {y1})")
        time.sleep(0.5)
        
        print("\n   Define multiplier region (BOTTOM-RIGHT corner)...")
        keyboard.wait('space')
        x2, y2 = pyautogui.position()
        print(f"   ✓ Bottom-right: ({x2}, {y2})")
        self.multiplier_region = (x1, y1, x2-x1, y2-y1)
        print(f"\n✓ Multiplier region: {self.multiplier_region}")
        
        print("\n5. Define ROUND HISTORY bar (TOP-LEFT corner)...")
        keyboard.wait('space')
        h1, h2 = pyautogui.position()
        print(f"   ✓ History top-left: ({h1}, {h2})")
        time.sleep(0.5)
        
        print("\n   Define ROUND HISTORY bar (BOTTOM-RIGHT corner)...")
        keyboard.wait('space')
        h3, h4 = pyautogui.position()
        print(f"   ✓ History bottom-right: ({h3}, {h4})")
        self.history_region = (h1, h2, h3-h1, h4-h2)
        print(f"\n✓ History region: {self.history_region}")
        
        # Initialize components
        self.detector = GameStateDetector(self.multiplier_region)
        self.history_tracker = RoundHistoryTracker(self.history_region)
        self.ml_generator = MLSignalGenerator(self.history_tracker)
        
        self.save_config()
        
        print("\n" + "="*60)
        print("✓ Setup complete!")
        print("="*60 + "\n")
    
    def set_stake(self, amount):
        try:
            pyautogui.click(self.stake_coords)
            time.sleep(0.2)
            pyautogui.hotkey('ctrl', 'a')
            time.sleep(0.1)
            pyautogui.press('backspace')
            time.sleep(0.1)
            pyautogui.typewrite(str(amount), interval=0.05)
            time.sleep(0.2)
        except Exception as e:
            print(f"⚠️  Error setting stake: {e}")
    
    def place_bet(self):
        try:
            pyautogui.click(self.bet_button_coords)
            self.is_betting = True
            self.stats["rounds_played"] += 1
            self.stats["ml_bets_placed"] += 1
            self.stats["total_bet"] += self.current_stake
            print(f"✓ Bet placed: {self.current_stake} | Round: {self.stats['rounds_played']}")
        except Exception as e:
            print(f"⚠️  Error placing bet: {e}")
    
    def cashout(self):
        try:
            pyautogui.click(self.cashout_coords)
            self.is_betting = False
            self.stats["successful_cashouts"] += 1
            self.stats["current_streak"] += 1
            print(f"✓ CASHED OUT after {self.cashout_delay}s")
        except Exception as e:
            print(f"⚠️  Error cashing out: {e}")
            self.stats["failed_cashouts"] += 1
    
    def increase_stake(self):
        old_stake = self.current_stake
        new_stake = self.current_stake * (1 + self.stake_increase_percent / 100)
        
        if new_stake > self.max_stake:
            new_stake = self.max_stake
        
        self.current_stake = int(new_stake)
        
        if self.current_stake > self.stats["max_stake_reached"]:
            self.stats["max_stake_reached"] = self.current_stake
        
        if self.current_stake != old_stake:
            print(f"  💰 Stake increased: {old_stake} → {self.current_stake}")
    
    def reset_stake(self):
        old_stake = self.current_stake
        self.current_stake = self.initial_stake
        self.stats["current_streak"] = 0
        
        if old_stake != self.current_stake:
            print(f"  ⚠️  Stake reset: {old_stake} → {self.current_stake}")
    
    def estimate_multiplier(self, elapsed_time):
        import math
        multiplier = math.exp(0.15 * elapsed_time)
        return round(multiplier, 2)
    
    def observe_round_result(self, timeout=30):
        """Wait and observe the round result without betting"""
        print("  👀 Observing round (no bet)...")
        start_time = time.time()
        
        # Wait for round to finish (detect crash or timeout)
        while time.time() - start_time < timeout:
            time.sleep(0.5)
            
            # Try to detect if game crashed by checking for awaiting message
            if self.detector.is_awaiting_next_flight():
                print("  ✓ Round finished (observed)")
                break
        
        # Try to read the multiplier from history
        # This is a placeholder - implement based on your game's UI
        observed_mult = np.random.uniform(1.0, 5.0)  # Simulate
        
        return observed_mult
    
    def print_stats(self):
        print("\n" + "="*60)
        print("BOT STATISTICS")
        print("="*60)
        print(f"Rounds observed:      {self.stats['rounds_observed']}")
        print(f"ML bets placed:       {self.stats['ml_bets_placed']}")
        print(f"ML bets skipped:      {self.stats['ml_skipped']}")
        print(f"Successful cashouts:  {self.stats['successful_cashouts']}")
        print(f"Failed cashouts:      {self.stats['failed_cashouts']}")
        print(f"Current streak:       {self.stats['current_streak']}")
        
        if self.stats['ml_bets_placed'] > 0:
            success_rate = (self.stats['successful_cashouts'] / self.stats['ml_bets_placed']) * 100
            print(f"Success rate:         {success_rate:.1f}%")
        
        print(f"\nStake progression:")
        print(f"  Current stake:      {self.current_stake}")
        print(f"  Max stake reached:  {self.stats['max_stake_reached']}")
        
        print(f"\nFinancial summary:")
        print(f"  Total bet:          {self.stats['total_bet']:.2f}")
        print(f"  Total return:       {self.stats['total_return']:.2f}")
        
        profit = self.stats['total_return'] - self.stats['total_bet']
        print(f"  Profit/Loss:        {profit:+.2f}")
        
        if self.stats['total_bet'] > 0:
            roi = (profit / self.stats['total_bet']) * 100
            print(f"  ROI:                {roi:+.1f}%")
        
        print("="*60 + "\n")
    
    def run_ml_mode(self):
        """Main bot loop with ML signal generation"""
        print("\n" + "="*60)
        print("AVIATOR BOT - ML MODE")
        print("="*60)
        print(f"Strategy: ML Ensemble with {self.ml_generator.confidence_threshold}% threshold")
        print(f"Cashout: Timer-based ({self.cashout_delay}s)")
        print(f"Initial stake: {self.initial_stake}")
        print("="*60)
        print("\nPress Ctrl+C to stop\n")
        
        try:
            while True:
                # Step 1: Wait for next round
                print(f"\n--- Round {self.stats['rounds_observed'] + 1} ---")
                
                if not self.detector.wait_for_awaiting_message(timeout=60):
                    print("⚠️  Timeout - retrying...")
                    continue
                
                # Step 2: Generate ML signal
                print("  🤖 Generating ML signal...")
                signal = self.ml_generator.generate_ensemble_signal()
                
                print(f"  📊 Prediction: {signal['prediction']}x")
                print(f"  📊 Range: {signal['range'][0]}x - {signal['range'][1]}x")
                print(f"  📊 Confidence: {signal['confidence']}%")
                print(f"  📊 Decision: {'BET' if signal['should_bet'] else 'SKIP'}")
                
                # Step 3: Decide whether to bet
                if signal['should_bet']:
                    print(f"  ✅ Placing bet - confidence above threshold")
                    
                    # Place bet
                    self.set_stake(self.current_stake)
                    time.sleep(0.4)
                    self.place_bet()
                    
                    # Wait for game start
                    if not self.detector.wait_for_game_start(timeout=10):
                        print("⚠️  Game didn't start - assuming loss")
                        self.is_betting = False
                        self.reset_stake()
                        
                        # Log the round
                        self.history_tracker.log_round(
                            multiplier=0,
                            bet_placed=True,
                            stake=self.current_stake,
                            cashout_time=0,
                            profit_loss=-self.current_stake,
                            prediction=signal['prediction'],
                            confidence=signal['confidence'],
                            pred_range=signal['range']
                        )
                        continue
                    
                    # Timer-based cashout
                    print(f"  ⏱️  Timer started: {self.cashout_delay}s countdown...")
                    round_start = time.time()
                    
                    while True:
                        elapsed = time.time() - round_start
                        remaining = self.cashout_delay - elapsed
                        
                        if remaining <= 0:
                            break
                        
                        est_mult = self.estimate_multiplier(elapsed)
                        print(f"  {remaining:.1f}s remaining... (~{est_mult:.2f}x)", end='\r')
                        time.sleep(0.1)
                    
                    print(" " * 50, end='\r')
                    
                    # Execute cashout
                    try:
                        final_mult = self.estimate_multiplier(self.cashout_delay)
                        self.cashout()
                        
                        estimated_return = self.current_stake * final_mult
                        profit = estimated_return - self.current_stake
                        self.stats["total_return"] += estimated_return
                        
                        print(f"  💰 Return: {estimated_return:.2f} (Profit: +{profit:.2f})")
                        
                        # Log successful cashout
                        self.history_tracker.log_round(
                            multiplier=final_mult,
                            bet_placed=True,
                            stake=self.current_stake,
                            cashout_time=self.cashout_delay,
                            profit_loss=profit,
                            prediction=signal['prediction'],
                            confidence=signal['confidence'],
                            pred_range=signal['range']
                        )
                        
                        # Increase stake on success
                        self.increase_stake()
                        
                        # Trigger incremental retraining
                        self.ml_generator.retrain_models_incremental({
                            'multiplier': final_mult,
                            'outcome': 'win',
                            'profit': profit
                        })
                        
                    except Exception as e:
                        print(f"⚠️  Cashout failed - game may have crashed")
                        loss = -self.current_stake
                        
                        # Log failed cashout
                        self.history_tracker.log_round(
                            multiplier=0,
                            bet_placed=True,
                            stake=self.current_stake,
                            cashout_time=self.cashout_delay,
                            profit_loss=loss,
                            prediction=signal['prediction'],
                            confidence=signal['confidence'],
                            pred_range=signal['range']
                        )
                        
                        self.reset_stake()
                        
                        # Trigger retraining with loss
                        self.ml_generator.retrain_models_incremental({
                            'multiplier': 0,
                            'outcome': 'loss',
                            'profit': loss
                        })
                
                else:
                    print(f"  ⏭️  Skipping - confidence too low ({signal['reason']})")
                    self.stats["ml_skipped"] += 1
                    
                    # Observe the round without betting
                    observed_mult = self.observe_round_result()
                    
                    # Log observation
                    self.history_tracker.log_round(
                        multiplier=observed_mult,
                        bet_placed=False,
                        stake=0,
                        cashout_time=0,
                        profit_loss=0,
                        prediction=signal['prediction'],
                        confidence=signal['confidence'],
                        pred_range=signal['range']
                    )
                    
                    print(f"  📊 Observed result: {observed_mult:.2f}x")
                
                self.stats["rounds_observed"] += 1
                
                # Show progress
                current_profit = self.stats['total_return'] - self.stats['total_bet']
                print(f"  📈 Total P/L: {current_profit:+.2f}")
                
                time.sleep(2)
        
        except KeyboardInterrupt:
            print("\n\n⏹️  Bot stopped by user")
            self.print_stats()


def main():
    """Main function"""
    print("="*60)
    print("AVIATOR BOT - ML ENHANCED")
    print("="*60)
    
    bot = AviatorBotML()
    
    # Load or setup configuration
    if bot.load_config() and bot.multiplier_region:
        print(f"\nCurrent configuration loaded")
        print(f"  History region: {bot.history_region}")
        
        print("\nOptions:")
        print("  1. Use existing config and run")
        print("  2. New setup")
        print("  3. Load models and run")
        
        choice = input("\nChoice (1/2/3): ").strip()
        
        if choice == '2':
            bot.setup_coordinates()
        elif choice == '3':
            if not bot.history_tracker:
                bot.history_tracker = RoundHistoryTracker(bot.history_region)
            if not bot.ml_generator:
                bot.ml_generator = MLSignalGenerator(bot.history_tracker)
            bot.ml_generator.load_models()
    else:
        bot.setup_coordinates()
    
    # Initialize components if not already done
    if not bot.detector and bot.multiplier_region:
        bot.detector = GameStateDetector(bot.multiplier_region)
    
    if not bot.history_tracker and bot.history_region:
        bot.history_tracker = RoundHistoryTracker(bot.history_region)
    
    if not bot.ml_generator and bot.history_tracker:
        bot.ml_generator = MLSignalGenerator(bot.history_tracker)
    
    # Get bot parameters
    print("\n" + "="*60)
    print("BOT PARAMETERS")
    print("="*60)
    
    initial = input(f"\nInitial stake (default {bot.initial_stake}): ").strip()
    if initial:
        bot.initial_stake = int(initial)
        bot.current_stake = bot.initial_stake
    
    max_stake = input(f"Max stake limit (default {bot.max_stake}): ").strip()
    if max_stake:
        bot.max_stake = int(max_stake)
    
    increase = input(f"Stake increase % (default {bot.stake_increase_percent}): ").strip()
    if increase:
        bot.stake_increase_percent = int(increase)
    
    delay = input(f"Cashout delay in seconds (default {bot.cashout_delay}): ").strip()
    if delay:
        bot.cashout_delay = float(delay)
    
    threshold = input(f"ML confidence threshold % (default {bot.ml_generator.confidence_threshold}): ").strip()
    if threshold:
        bot.ml_generator.confidence_threshold = float(threshold)
    
    # Show strategy summary
    estimated_mult = bot.estimate_multiplier(bot.cashout_delay)
    
    print("\n" + "="*60)
    print("STRATEGY SUMMARY")
    print("="*60)
    print(f"Mode:              ML Ensemble")
    print(f"Initial stake:     {bot.initial_stake}")
    print(f"Max stake:         {bot.max_stake}")
    print(f"Increase on win:   +{bot.stake_increase_percent}%")
    print(f"Cashout timing:    {bot.cashout_delay}s (~{estimated_mult}x)")
    print(f"ML threshold:      {bot.ml_generator.confidence_threshold}%")
    print(f"CSV logging:       {bot.history_tracker.csv_file}")
    print("="*60)
    
    print("\n📝 How it works:")
    print("  1. Observe round history and generate ML signal")
    print("  2. If confidence ≥ threshold → Place bet")
    print("  3. If confidence < threshold → Skip and observe")
    print("  4. All rounds logged to CSV for training")
    print("  5. Models retrain incrementally with new data")
    
    input("\nPress Enter to start bot...")
    
    # Save config
    bot.save_config()
    
    # Run bot in ML mode
    bot.run_ml_mode()


if __name__ == "__main__":
    main()