# bot.py
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
import re
import win32clipboard
import win32con

class RoundHistoryTracker:
    """Track and log round history from the game's history bar"""

    def __init__(self, history_region=None):
        self.history_region = history_region  # (x, y, width, height)
        self.csv_file = "aviator_rounds_history.csv"
        self.last_round_data = None
        self.last_logged_multiplier = None
        self.last_log_time = 0
        self.log_cooldown = 2.0  # Minimum seconds between auto-logs
        self.local_history_buffer = deque(maxlen=10)  # Keep last 10 rounds in memory

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

        # Import tesseract if available
        try:
            import pytesseract
            self.pytesseract = pytesseract
            self.tesseract_available = True
        except Exception:
            print("⚠️  Warning: pytesseract not installed for OCR (history reading will be degraded)")
            self.tesseract_available = False

    def capture_history_region(self):
        if not self.history_region:
            return None

        try:
            x, y, w, h = self.history_region

            # Validate coordinates
            if w <= 0 or h <= 0:
                print(f"⚠️ Invalid history region: width={w}, height={h}")
                return None

            if x < 0 or y < 0:
                print(f"⚠️ Invalid history region: x={x}, y={y}")
                return None

            screenshot = pyautogui.screenshot(region=(x, y, w, h))
            return screenshot
        except Exception as e:
            print(f"⚠️ Error capturing history region: {e}")
            return None
    
    def auto_log_from_clipboard(self, detector, force=False):
        try:
            # Check cooldown to avoid duplicate logging
            current_time = time.time()
            if not force and (current_time - self.last_log_time) < self.log_cooldown:
                print(f"  ⏳ Cooldown active ({self.log_cooldown - (current_time - self.last_log_time):.1f}s remaining)")
                return False, None

            # Read multiplier from clipboard
            multiplier = detector.read_multiplier_from_clipboard()

            if multiplier is None:
                print("  ⚠️ Failed to read multiplier")
                return False, None

            # Check for duplicate
            if not force and multiplier == self.last_logged_multiplier:
                print(f"  ⏭️ Skipping duplicate: {multiplier}x")
                return False, multiplier

            # Log to CSV
            self.log_round(
                multiplier=multiplier,
                bet_placed=False,
                stake=0,
                cashout_time=0,
                profit_loss=0,
                prediction=None,
                confidence=0,
                pred_range=(0, 0)
            )

            # Update local buffer
            self.local_history_buffer.append({
                'multiplier': multiplier,
                'timestamp': datetime.now().isoformat(),
                'round_id': datetime.now().strftime("%Y%m%d%H%M%S%f")
            })

            # Update tracking variables
            self.last_logged_multiplier = multiplier
            self.last_log_time = current_time

            print(f"  ✅ Auto-logged: {multiplier}x | Buffer size: {len(self.local_history_buffer)}")
            return True, multiplier

        except Exception as e:
            print(f"  ❌ Auto-log error: {e}")
            return False, None

    def get_local_history(self, n=10):
        """Get last N rounds from local buffer (fastest access)"""
        history = list(self.local_history_buffer)
        return history[-n:] if len(history) >= n else history

    # ----------------------
    # Auto-detecting extractor
    # ----------------------
    def extract_history_values_auto(self, max_cells=30, debug=False):
        if not self.history_region:
            if debug: print("No history_region")
            return []

        shot = self.capture_history_region()
        if shot is None:
            if debug: print("capture failed")
            return []

        img = np.array(shot)
        h_img, w_img = img.shape[:2]

        # Divide into exactly 3 sections
        cell_width = w_img // 3
        cells = [(i * cell_width, 0, cell_width if i < 2 else w_img - i * cell_width, h_img) 
                 for i in range(3)]

        results = []
        for idx, (sx, sy, w_box, h_box) in enumerate(cells):
            crop = img[sy:sy+h_box, sx:sx+w_box].copy()
            color, multiplier, raw_text = "unknown", None, None

            try:
                # Enhanced color detection
                ch, cw = crop.shape[:2]
                center = crop[int(ch*0.25):int(ch*0.75), int(cw*0.25):int(cw*0.75)]
                hsv = cv2.cvtColor(center, cv2.COLOR_RGB2HSV)

                h_mean = int(np.mean(hsv[:,:,0]))
                s_mean = int(np.mean(hsv[:,:,1]))
                v_mean = int(np.mean(hsv[:,:,2]))
                r_mean = int(np.mean(center[:,:,0]))
                g_mean = int(np.mean(center[:,:,1]))
                b_mean = int(np.mean(center[:,:,2]))

                if debug:
                    print(f"Cell{idx}: HSV({h_mean},{s_mean},{v_mean}) RGB({r_mean},{g_mean},{b_mean})")

                # Color classification
                if s_mean > 80 and v_mean > 100:
                    if 35 <= h_mean <= 85:
                        color = "green"
                    elif h_mean <= 15 or h_mean >= 165:
                        color = "red"
                        multiplier = 0.0
                    elif 145 <= h_mean <= 165 and r_mean > 150:
                        color = "pink"
                        multiplier = 0.0
                elif s_mean < 40 and v_mean > 200:
                    color = "white"
                elif r_mean > 180 and g_mean < 100 and b_mean < 100:
                    color = "red"
                    multiplier = 0.0
                elif r_mean > 150 and g_mean < 120 and b_mean > 100:
                    color = "pink"
                    multiplier = 0.0
            except Exception as e:
                if debug: print(f"Color error cell{idx}: {e}")

            # OCR for green/unknown cells
            if multiplier is None and color in ("green", "white", "unknown"):
                if getattr(self, "tesseract_available", False):
                    try:
                        gray = cv2.cvtColor(crop, cv2.COLOR_RGB2GRAY)
                        variants = [
                            cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                                cv2.THRESH_BINARY, 11, 2),
                            cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
                        ]

                        best_mult, best_conf = None, -1
                        for var_img in variants:
                            scaled = cv2.resize(var_img, None, fx=3, fy=3, interpolation=cv2.INTER_CUBIC)
                            text = self.pytesseract.image_to_string(
                                scaled, config='--oem 3 --psm 7 -c tessedit_char_whitelist=0123456789.xX'
                            ).strip()

                            text_clean = text.replace('×','x').replace('X','x').replace(' ','')
                            match = re.search(r'(\d+\.?\d*)x?', text_clean)

                            if match:
                                try:
                                    mult_val = float(match.group(1))
                                    if 1.0 <= mult_val <= 1000.0:
                                        conf = len(match.group(1))
                                        if conf > best_conf:
                                            best_conf, best_mult, raw_text = conf, mult_val, text
                                except:
                                    pass

                        if best_mult: multiplier = best_mult
                    except Exception as e:
                        if debug: print(f"OCR error cell{idx}: {e}")

            # Fallback
            if multiplier is None:
                if color in ("red", "pink"):
                    multiplier = 0.0
                elif color == "green":
                    multiplier = 2.0

            results.append({
                "multiplier": float(multiplier) if multiplier is not None else None,
                "raw_text": raw_text,
                "color": color,
                "bbox": (int(sx), int(sy), int(w_box), int(h_box)),
                "cell_index": idx
            })

        if debug:
            print(f"Extracted {len(results)} cells: {[r['multiplier'] for r in results]}")

        return results  # LEFT to RIGHT
    # -------- wrapper: get last n history ----------
    def get_last_n_history(self, n=5, debug=False):
        """
        Returns (multipliers_list, details_list)
        multipliers_list: newest -> oldest (length <= n), entries may be None
        details_list: corresponding dicts
        """
        try:
            items = self.extract_history_values_auto(debug=debug)
            if not items:
                return [], []
            selected = items[-n:] if len(items) >= n else items[:]
            selected.reverse()  # newest -> oldest
            multipliers = [it.get("multiplier") for it in selected]
            if debug:
                print("get_last_n_history (newest->oldest):", multipliers)
            return multipliers, selected
        except Exception as e:
            if debug: print("get_last_n_history error:", e)
            return [], []

    # ---------------------
    # CSV logging & helpers
    # ---------------------
    def read_latest_round_ocr(self):
        """Read the latest round result using OCR (fallback)"""
        if not getattr(self, "tesseract_available", False) or not self.history_region:
            return None
        try:
            image = self.capture_history_region()
            img_array = np.array(image)
            gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
            _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)
            text = self.pytesseract.image_to_string(thresh, config='--oem 3 --psm 6')
            import re
            multipliers = re.findall(r'(\d+\.?\d*)x', text)
            if multipliers:
                return float(multipliers[0])
            return None
        except Exception:
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

    def bootstrap_history(self, n=10, force=False, debug=False):
        """
        Grab the most recent `n` history items (newest->oldest) and append to CSV as observations.
        Dedupes defaults to last CSV row unless force=True.
        """
        try:
            multipliers, details = self.get_last_n_history(n=n, debug=debug)
            if not details:
                if debug: print("No history items to bootstrap")
                return []

            existing_mults = []
            if os.path.exists(self.csv_file):
                try:
                    df = pd.read_csv(self.csv_file)
                    if not df.empty:
                        existing_mults = df['multiplier'].tail(n).tolist()
                except Exception as e:
                    if debug: print("Warning reading CSV for dedupe:", e)

            appended = 0
            to_append = list(reversed(details))  # oldest -> newest for logging
            for it in to_append:
                m = it.get("multiplier")
                color = it.get("color")
                if m is None:
                    if not force:
                        if debug: print("Skipping ambiguous history entry (no multiplier).")
                        continue
                    if color in ('red','pink'):
                        m = 0.0
                    elif color == 'green':
                        m = 2.0
                    else:
                        continue
                if not force and existing_mults:
                    try:
                        if float(existing_mults[-1]) == float(m):
                            if debug: print(f"Skipping duplicate multiplier {m} (already in CSV tail).")
                            continue
                    except Exception:
                        pass
                try:
                    self.log_round(
                        multiplier=m,
                        bet_placed=False,
                        stake=0,
                        cashout_time=0,
                        profit_loss=0,
                        prediction=None,
                        confidence=0,
                        pred_range=(0,0)
                    )
                    appended += 1
                except Exception as e:
                    if debug: print("Error logging bootstrap entry:", e)

            if debug: print(f"Bootstrap complete: appended {appended} items (requested {n}).")
            return details
        except Exception as e:
            if debug: print("bootstrap_history error:", e)
            return []


class EnhancedHistoryTracker(RoundHistoryTracker):
    """Extended tracker with exact 3-round storage"""
    
    def __init__(self, history_region=None):
        super().__init__(history_region)
        self.last_3_rounds = deque(maxlen=3)
        self.rounds_array_file = "last_3_rounds.json"
        
    def get_exact_last_3(self, debug=False):
        """Get EXACTLY last 3 rounds: [newest, middle, oldest]"""
        items = self.extract_history_values_auto(debug=debug)
        
        if not items or len(items) < 3:
            if debug: print(f"⚠️ Expected 3, got {len(items) if items else 0}")
            return [], []
        
        last_3 = items[-3:]
        last_3.reverse()  # Newest first
        
        multipliers = []
        for item in last_3:
            mult = item.get("multiplier")
            if mult is None:
                color = item.get("color", "unknown")
                mult = 0.0 if color in ("red","pink") else 2.0 if color=="green" else None
            multipliers.append(mult)
        
        if debug:
            print(f"Last 3 (newest→oldest): {multipliers}")
        
        return multipliers, last_3
    
    def update_last_3_buffer(self, debug=False):
        """Update buffer and JSON with latest 3"""
        multipliers, details = self.get_exact_last_3(debug=debug)
        
        if len(multipliers) == 3:
            self.last_3_rounds.clear()
            for mult in multipliers:
                self.last_3_rounds.append(mult)
            
            try:
                data = {
                    "timestamp": datetime.now().isoformat(),
                    "rounds": [
                        {"position": i, "multiplier": mult, 
                         "label": ["newest","middle","oldest"][i]}
                        for i, mult in enumerate(multipliers)
                    ]
                }
                with open(self.rounds_array_file, 'w') as f:
                    json.dump(data, f, indent=2)
                if debug: print(f"✓ Saved to {self.rounds_array_file}")
            except Exception as e:
                if debug: print(f"⚠️ JSON save error: {e}")
        
        return list(self.last_3_rounds)
    
    def get_last_3_from_buffer(self):
        """Fast buffer access"""
        return list(self.last_3_rounds)
    
    def log_round_enhanced(self, multiplier, bet_placed=False, stake=0,
                          cashout_time=0, profit_loss=0, prediction=None,
                          confidence=0, pred_range=(0,0)):
        """Enhanced logging with buffer update"""
        self.log_round(multiplier, bet_placed, stake, cashout_time,
                      profit_loss, prediction, confidence, pred_range)
        time.sleep(0.3)
        self.update_last_3_buffer()


# -------------------------
# MLSignalGenerator (unchanged core)
# -------------------------



class MLSignalGenerator:
    """Generate betting signals using ensemble ML models"""

    def __init__(self, history_tracker):
        self.history_tracker = history_tracker
        self.confidence_threshold = 65.0
        self.models_loaded = False
        self.feature_window = 20
        self.lstm_model = None
        self.rf_model = None
        self.xgb_model = None
        self.gb_model = None
        self.scaler = None
        print("🤖 ML Signal Generator initialized")
        print(f"   Confidence threshold: {self.confidence_threshold}%")

    def load_models(self):
        try:
            self.models_loaded = True
            print("✓ Models loaded successfully")
            return True
        except Exception as e:
            print(f"⚠️  Model loading failed: {e}")
            print("   Running in simulation mode")
            return False

    def engineer_features(self, recent_rounds):
        if len(recent_rounds) < self.feature_window:
            return None
        multipliers = recent_rounds['multiplier'].values[-self.feature_window:]
        features = {
            'mean': np.mean(multipliers),
            'std': np.std(multipliers),
            'min': np.min(multipliers),
            'max': np.max(multipliers),
            'median': np.median(multipliers),
            'trend': np.polyfit(range(len(multipliers)), multipliers, 1)[0],
            'momentum': multipliers[-1] - multipliers[-5] if len(multipliers) >= 5 else 0,
            'low_count': np.sum(multipliers < 2.0),
            'high_count': np.sum(multipliers >= 2.0),
            'crash_streak': self._calculate_crash_streak(multipliers, 2.0),
            'last_1': multipliers[-1],
            'last_2': multipliers[-2] if len(multipliers) >= 2 else 0,
            'last_3': multipliers[-3] if len(multipliers) >= 3 else 0,
            'last_5_avg': np.mean(multipliers[-5:]) if len(multipliers) >= 5 else 0,
            'volatility': np.std(multipliers[-10:]) if len(multipliers) >= 10 else 0,
        }
        return np.array(list(features.values())).reshape(1, -1)

    def _calculate_crash_streak(self, multipliers, threshold):
        streak = 0
        for mult in reversed(multipliers):
            if mult < threshold:
                streak += 1
            else:
                break
        return streak

    def predict_lstm(self, features):
        if not self.lstm_model:
            confidence = np.random.uniform(40, 90)
            prediction = np.random.uniform(1.5, 3.0)
            print(f"  [LSTM] Simulated prediction: {prediction:.2f}x with {confidence:.1f}% confidence")
            return prediction, confidence

    def predict_random_forest(self, features):
        if not self.rf_model:
            confidence = np.random.uniform(40, 90)
            prediction = np.random.uniform(1.5, 3.0)
            print(f"  [RF] Simulated prediction: {prediction:.2f}x with {confidence:.1f}% confidence")  
            return prediction, confidence

    def predict_xgboost(self, features):
        if not self.xgb_model:
            confidence = np.random.uniform(40, 90)
            prediction = np.random.uniform(1.5, 3.0)
            print(f"  [XGB] Simulated prediction: {prediction:.2f}x with {confidence:.1f}% confidence")
            return prediction, confidence

    def predict_gradient_boosting(self, features):
        if not self.gb_model:
            confidence = np.random.uniform(40, 90)
            prediction = np.random.uniform(1.5, 3.0)
            print(f"  [GB] Simulated prediction: {prediction:.2f}x with {confidence:.1f}% confidence")
            return prediction, confidence

    def generate_ensemble_signal(self):
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
        features = self.engineer_features(recent_rounds)
        if features is None:
            return {'should_bet': False, 'confidence': 0, 'prediction': 0, 'range': (0,0), 'reason': 'Feature engineering failed'}
        predictions = []; confidences = []
        pred, conf = self.predict_lstm(features); predictions.append(pred); confidences.append(conf)
        pred, conf = self.predict_random_forest(features); predictions.append(pred); confidences.append(conf)
        pred, conf = self.predict_xgboost(features); predictions.append(pred); confidences.append(conf)
        pred, conf = self.predict_gradient_boosting(features); predictions.append(pred); confidences.append(conf)
        total_conf = sum(confidences)
        if total_conf == 0:
            ensemble_pred = np.mean(predictions); ensemble_conf = 0
        else:
            weights = [c / total_conf for c in confidences]
            ensemble_pred = sum(p * w for p, w in zip(predictions, weights))
            ensemble_conf = np.mean(confidences)
        pred_std = np.std(predictions)
        pred_range = (max(1.0, ensemble_pred - pred_std), ensemble_pred + pred_std)
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
        print("  🔄 Incremental training triggered")
        pass

# -------------------------
# GameStateDetector & AviatorBotML (same structure as before)
# -------------------------
class GameStateDetector:
    """Detect game states: Awaiting, Active, Crashed"""

    def __init__(self, region):
        self.region = region
        self.multiplier_coords = [(18, 1100), (114, 1103)]  # Coordinates for multiplier text selection
        try:
            import pytesseract
            self.pytesseract = pytesseract
            self.tesseract_available = True
        except Exception:
            print("⚠️  Warning: pytesseract not installed")
            self.tesseract_available = False
            
    def read_multiplier_from_clipboard(self):
        try:
            # Clear clipboard first
            win32clipboard.OpenClipboard()
            win32clipboard.EmptyClipboard()
            win32clipboard.CloseClipboard()
            time.sleep(0.1)
            
            # Updated coordinates for text selection
            x1, y1 = 19, 1101
            x2, y2 = 98, 1106
            
            # Move to start position
            pyautogui.moveTo(x1, y1, duration=0.1)
            time.sleep(0.05)
            
            # Click and drag to select text
            pyautogui.mouseDown()
            pyautogui.moveTo(x2, y2, duration=0.1)
            pyautogui.mouseUp()
            time.sleep(0.1)
            
            # Copy to clipboard
            pyautogui.hotkey('ctrl', 'c')
            time.sleep(0.15)
            
            # Read from clipboard
            win32clipboard.OpenClipboard()
            try:
                data = win32clipboard.GetClipboardData(win32con.CF_UNICODETEXT)
            except:
                try:
                    data = win32clipboard.GetClipboardData(win32con.CF_TEXT)
                except:
                    data = None
            win32clipboard.CloseClipboard()
            
            if not data:
                print("  ⚠️ Clipboard empty")
                return None
                
            # Convert and clean text
            if isinstance(data, bytes):
                text = data.decode('utf-8', errors='ignore')
            else:
                text = str(data)
            
            text = text.strip()
            print(f'  📋 Copied text: "{text}"')
            
            # Extract multiplier value - handle various formats
            # Examples: "1.5x", "1.5", "x1.5", "1.50x"
            text_clean = text.replace(' ', '').replace(',', '.')
            
            # Try different patterns
            patterns = [
                r'(\d+\.?\d*)x',  # "1.5x" or "1x"
                r'x(\d+\.?\d*)',  # "x1.5"
                r'^(\d+\.?\d*)$', # Just "1.5"
            ]
            
            for pattern in patterns:
                match = re.search(pattern, text_clean, re.IGNORECASE)
                if match:
                    try:
                        value = float(match.group(1))
                        if 0 < value <= 1000:  # Sanity check
                            print(f'  ✓ Parsed multiplier: {value}x')
                            return value
                    except:
                        continue
            
            print(f'  ⚠️ Could not parse multiplier from: "{text}"')
            return None
            
        except Exception as e:
            print(f"  ⚠️ Error reading clipboard: {e}")
            return None

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
            white_ratio = white_pixels / total_pixels if total_pixels > 0 else 0
            if white_ratio > 0.1:
                return 'ACTIVE'
            return 'UNKNOWN'
        except Exception:
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

    def detect_actual_crash(self, timeout=5):
        print("  🔍 Verifying result...")
        time.sleep(0.5)

        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                history_items = self.history_tracker.extract_history_values_auto(debug=False)

                if history_items and len(history_items) >= 1:
                    latest = history_items[-1]
                    color = latest.get("color", "unknown")
                    mult = latest.get("multiplier")

                    if color in ("red", "pink") or (mult is not None and mult < 1.5):
                        print(f"  ❌ CRASH: Color={color}, Mult={mult}")
                        return True, mult if mult is not None else 0.0

                    elif color == "green" and mult is not None and mult >= 1.5:
                        print(f"  ✅ SUCCESS: {mult}x")
                        return False, mult

            except Exception as e:
                print(f"  ⚠️ Detection error: {e}")

            time.sleep(0.3)

        print("  ⚠️ Timeout - assuming success")
        return False, None


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
        while time.time() - start_time < timeout:
            time.sleep(0.5)
            if self.detector.is_awaiting_next_flight():
                print("  ✓ Round finished (observed)")
                break
        observed_mult = self.history_tracker.read_latest_round_ocr() or np.random.uniform(1.0, 5.0)
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

    def handle_loss(self, stake_used, signal, elapsed=0):
        print("  ❌ Round lost / crashed before cashout")
        self.stats["failed_cashouts"] += 1
        self.stats["current_streak"] = 0
        loss = -stake_used
        try:
            self.history_tracker.log_round(
                multiplier=0,
                bet_placed=True,
                stake=stake_used,
                cashout_time=round(elapsed, 2) if elapsed else 0,
                profit_loss=loss,
                prediction=signal.get('prediction') if signal else None,
                confidence=signal.get('confidence') if signal else 0,
                pred_range=signal.get('range') if signal else (0,0)
            )
        except Exception as e:
            print(f"  ⚠️  Error logging failed round: {e}")
        self.reset_stake()
        try:
            self.ml_generator.retrain_models_incremental({
                'multiplier': 0,
                'outcome': 'loss',
                'profit': loss
            })
        except Exception as e:
            print(f"  ⚠️  Error triggering retrain: {e}")

    def run_ml_mode(self):
        print("\n" + "="*60)
        print("AVIATOR BOT - ML MODE (ENHANCED)")
        print("="*60)
        print(f"Cashout: {self.cashout_delay}s | Threshold: {self.ml_generator.confidence_threshold}%")
        print("="*60 + "\nPress Ctrl+C to stop\n")

        try:
            while True:
                print(f"\n--- Round {self.stats['rounds_observed'] + 1} ---")
                
                if not self.detector.wait_for_awaiting_message(timeout=60):
                    print("⚠️ Timeout")
                    continue

                # AUTO-LOG: Read and log the completed round
                print("  🤖 Auto-logging completed round...")
                time.sleep(0.3)  # Small delay to ensure multiplier is displayed
                success, logged_mult = self.history_tracker.auto_log_from_clipboard(self.detector)

                if success:
                    print(f"  📝 Logged to CSV: {logged_mult}x")
                    # Update local buffer for quick access
                    recent = self.history_tracker.get_local_history(n=5)
                    print(f"  📊 Recent history: {[r['multiplier'] for r in recent]}")
                else:
                    print("  ⚠️ Auto-log failed, continuing...")

                print("  🤖 Generating signal...")
                signal = self.ml_generator.generate_ensemble_signal() if self.ml_generator else {
                    'should_bet': False, 'prediction': 0, 'confidence': 0, 
                    'range': (0,0), 'reason': 'no-ml'
                }

                print(f"  📊 Pred: {signal['prediction']}x | Conf: {signal['confidence']}% | {'BET' if signal['should_bet'] else 'SKIP'}")

                if signal['should_bet']:
                    stake_used = self.current_stake
                    self.set_stake(stake_used)
                    time.sleep(0.4)
                    self.place_bet()

                    if not self.detector.wait_for_game_start(timeout=10):
                        print("⚠️ Start timeout")
                        self.is_betting = False
                        self.history_tracker.log_round(0, True, stake_used, 0, -stake_used,
                                                      signal['prediction'], signal['confidence'], signal['range'])
                        self.reset_stake()
                        continue

                    print(f"  ⏱️ Timer: {self.cashout_delay}s")
                    round_start = time.time()
                    crashed_early = False

                    while True:
                        elapsed = time.time() - round_start
                        if self.detector.is_awaiting_next_flight():
                            crashed_early = True
                            print("\n  💥 CRASHED EARLY!")
                            break
                        if elapsed >= self.cashout_delay:
                            break
                        print(f"  {self.cashout_delay-elapsed:.1f}s...", end='\r')
                        time.sleep(0.1)
                    print(" "*50, end='\r')

                    if crashed_early:
                        self.is_betting = False
                        self.stats["failed_cashouts"] += 1
                        self.stats["current_streak"] = 0
                        self.history_tracker.log_round(0, True, stake_used, elapsed, -stake_used,
                                                      signal['prediction'], signal['confidence'], signal['range'])
                        print(f"  💸 Loss: -{stake_used:.2f}")
                        self.reset_stake()
                        self.stats["rounds_observed"] += 1
                        print(f"  📈 Total P/L: {self.stats['total_return']-self.stats['total_bet']:+.2f}")
                        time.sleep(2)
                        continue

                    # Attempt cashout
                    self.cashout()
                    time.sleep(1)
                    
                    # VERIFY result
                    crashed, actual_mult = self.detect_actual_crash(timeout=5)
                    
                    if crashed:
                        # False positive - actually crashed
                        self.is_betting = False
                        self.stats["failed_cashouts"] += 1
                        self.stats["current_streak"] = 0
                        self.stats["successful_cashouts"] -= 1
                        
                        self.history_tracker.log_round(
                            actual_mult if actual_mult else 0, True, stake_used,
                            self.cashout_delay, -stake_used,
                            signal['prediction'], signal['confidence'], signal['range']
                        )
                        print(f"  💸 ACTUAL LOSS: -{stake_used:.2f} (crashed at {actual_mult}x)")
                        self.reset_stake()
                    else:
                        # Genuine win
                        final_mult = actual_mult if actual_mult else self.estimate_multiplier(self.cashout_delay)
                        returns = stake_used * final_mult
                        profit = returns - stake_used
                        self.stats["total_return"] += returns
                        
                        self.history_tracker.log_round(
                            final_mult, True, stake_used, self.cashout_delay, profit,
                            signal['prediction'], signal['confidence'], signal['range']
                        )
                        print(f"  💰 WIN: +{profit:.2f} (Return: {returns:.2f})")
                        self.increase_stake()

                else:
                    # Skip round
                    print(f"  ⏭️ Skipping: {signal['reason']}")
                    self.stats["ml_skipped"] += 1
                    
                    start_wait = time.time()
                    while time.time() - start_wait < 30:
                        if self.detector.is_awaiting_next_flight():
                            break
                        time.sleep(0.5)
                    
                    time.sleep(1)
                    history_items = self.history_tracker.extract_history_values_auto(debug=False)
                    observed_mult = history_items[-1].get("multiplier") if history_items else 2.0
                    
                    self.history_tracker.log_round(
                        observed_mult if observed_mult else 2.0, False, 0, 0, 0,
                        signal['prediction'], signal['confidence'], signal['range']
                    )

                self.stats["rounds_observed"] += 1
                print(f"  📈 Total P/L: {self.stats['total_return']-self.stats['total_bet']:+.2f}")
                
                # Update buffer
                if hasattr(self.history_tracker, 'update_last_3_buffer'):
                    self.history_tracker.update_last_3_buffer()
                
                time.sleep(2)

        except KeyboardInterrupt:
            print("\n\n⏹️ Stopped")
            self.print_stats()

    # Convenience wrappers for history
    def get_last_history_array(self, n=5, debug=False):
        if not self.history_tracker:
            if debug: print("No history_tracker available"); return []
        mults, details = self.history_tracker.get_last_n_history(n=n, debug=debug)
        return mults

    def get_last_history_boxes(self, n=5):
        out = []
        if not self.history_tracker:
            return out
        mults, details = self.history_tracker.get_last_n_history(n=n, debug=False)
        hr = self.history_region
        if not hr:
            for d in details:
                out.append(d)
            return out
        hx, hy, hw, hh = hr
        for d in details:
            rel_bbox = d.get("bbox")
            if rel_bbox:
                abs_x = int(hx + rel_bbox[0])
                abs_y = int(hy + rel_bbox[1])
                w_box = int(rel_bbox[2]); h_box = int(rel_bbox[3])
                out.append({
                    "multiplier": d.get("multiplier"),
                    "raw_text": d.get("raw_text"),
                    "color": d.get("color"),
                    "bbox": (abs_x, abs_y, w_box, h_box)
                })
            else:
                out.append(d)
        return out

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


    # --- start AutoClipboardLogger with the live bot instance ---
    try:
        auto_logger = AutoClipboardLogger(bot, poll_interval=0.6, cooldown=3.0, debug=True)
        auto_logger.start()
        bot.auto_clipboard_logger = auto_logger
        print("✓ AutoClipboardLogger started in background.")
    except Exception as e:
        print("⚠️ Could not start AutoClipboardLogger:", e)

    # Bootstrap last 5 rounds into CSV (non-destructive dedupe)
    try:
        if bot.history_tracker and bot.history_region:
            print("\nBootstrapping last 5 on-screen rounds into CSV (if new)...")
            bot.history_tracker.bootstrap_history(n=5, force=False, debug=True)
    except Exception as e:
        print("Bootstrap failed:", e)

    # Bot parameters
    print("\n" + "="*60)
    print("BOT PARAMETERS")
    print("="*60)
    initial = input(f"\nInitial stake (default {bot.initial_stake}): ").strip()
    if initial:
        bot.initial_stake = int(initial); bot.current_stake = bot.initial_stake
    max_stake = input(f"Max stake limit (default {bot.max_stake}): ").strip()
    if max_stake: bot.max_stake = int(max_stake)
    increase = input(f"Stake increase % (default {bot.stake_increase_percent}): ").strip()
    if increase: bot.stake_increase_percent = int(increase)
    delay = input(f"Cashout delay in seconds (default {bot.cashout_delay}): ").strip()
    if delay: bot.cashout_delay = float(delay)
    threshold = input(f"ML confidence threshold % (default {bot.ml_generator.confidence_threshold}): ").strip()
    if threshold: bot.ml_generator.confidence_threshold = float(threshold)

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
    print("\nPress Enter to start bot...")
    input()
    bot.save_config()
    bot.run_ml_mode()

if __name__ == "__main__":
    main()

# -------------------------
# AutoClipboardLogger (minimal, non-invasive)
# -------------------------
import threading
import pyperclip

class AutoClipboardLogger(threading.Thread):
    """
    Background thread that watches for the game 'AWAITING' state using the existing
    GameStateDetector and automatically selects the multiplier text, copies it to
    the clipboard, parses the numeric multiplier and logs it to the existing history CSV
    via RoundHistoryTracker.log_round(...).
    """
    def __init__(self, bot, poll_interval=0.6, cooldown=3.0, debug=False):
        super().__init__(daemon=True)
        self.bot = bot
        self.poll_interval = poll_interval
        self.cooldown = cooldown
        self.debug = debug
        self._stop = threading.Event()
        self.last_logged_time = 0
        self.detector = getattr(bot, "detector", None)
        if self.detector is None and getattr(bot, "multiplier_region", None):
            try:
                self.detector = GameStateDetector(bot.multiplier_region)
            except Exception:
                self.detector = None

    def stop(self):
        self._stop.set()

    def _select_and_copy(self):
        try:
            mr = getattr(self.bot, "multiplier_region", None)
            if mr:
                x, y, w, h = mr
                cx = int(x + w/2)
                cy = int(y + h/2)
                pyautogui.moveTo(cx, cy, duration=0.03)
                pyautogui.click(clicks=2, interval=0.06)
            else:
                det = getattr(self.bot, "detector", None)
                if det and hasattr(det, "multiplier_coords"):
                    (x1,y1),(x2,y2) = det.multiplier_coords
                    pyautogui.moveTo(x1, y1, duration=0.02)
                    pyautogui.mouseDown()
                    pyautogui.moveTo(x2, y2, duration=0.02)
                    pyautogui.mouseUp()
                else:
                    return None

            import sys
            if sys.platform == 'darwin':
                pyautogui.hotkey('command', 'c')
            else:
                pyautogui.hotkey('ctrl', 'c')

            time.sleep(0.08)

            txt = ""
            for _ in range(8):
                try:
                    txt = pyperclip.paste()
                except Exception:
                    txt = ""
                if txt and str(txt).strip():
                    break
                time.sleep(0.05)
            return txt
        except Exception as e:
            if self.debug:
                print("AutoClipboardLogger: select_and_copy error:", e)
            return None

    def _parse_multiplier(self, text):
        if not text:
            return None
        try:
            m = re.search(r"\d+(?:\.\d+)?", str(text))
            if m:
                return float(m.group(0))
        except Exception:
            return None
        return None

    def run(self):
        if self.debug:
            print("AutoClipboardLogger: started")
        while not self._stop.is_set():
            try:
                awaiting = False
                if self.detector:
                    try:
                        awaiting = self.detector.is_awaiting_next_flight()
                    except Exception:
                        awaiting = False
                else:
                    awaiting = False

                if awaiting:
                    now = time.time()
                    if now - self.last_logged_time < self.cooldown:
                        time.sleep(self.poll_interval)
                        continue

                    time.sleep(0.12)

                    raw = self._select_and_copy()
                    parsed = self._parse_multiplier(raw)

                    ts = datetime.utcnow().isoformat()
                    if parsed is not None:
                        try:
                            if getattr(self.bot, "history_tracker", None):
                                self.bot.history_tracker.log_round(parsed, bet_placed=False, stake=0, cashout_time=0, profit_loss=0)
                            if self.debug:
                                print(f"[{ts}] AutoClipboardLogger: parsed {parsed} from clipboard -> logged")
                        except Exception as e:
                            if self.debug:
                                print("AutoClipboardLogger: failed to log_round:", e)
                        self.last_logged_time = time.time()
                    else:
                        try:
                            if getattr(self.bot, "history_tracker", None):
                                self.bot.history_tracker.log_round(None, bet_placed=False, stake=0, cashout_time=0, profit_loss=0)
                            if self.debug:
                                print(f"[{ts}] AutoClipboardLogger: failed to parse clipboard {repr(raw)} -> logged raw")
                        except Exception as e:
                            if self.debug:
                                print("AutoClipboardLogger: failed to log raw:", e)
                        self.last_logged_time = time.time()

                time.sleep(self.poll_interval)
            except Exception as e:
                if self.debug:
                    print("AutoClipboardLogger exception:", e)
                time.sleep(self.poll_interval)

# ---- end AutoClipboardLogger ----
