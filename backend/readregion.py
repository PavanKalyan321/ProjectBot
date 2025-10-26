import mss
import numpy as np
import cv2
import pytesseract
import re
import time
import os
import csv
from datetime import datetime

from utils.betting_helpers import (
    set_stake_verified,
    place_bet_with_verification,
    cashout_verified,
    estimate_multiplier,
    increase_stake,
    reset_stake
)

# Optional: Set path to tesseract executable if needed
# pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'


class AviatorHistoryLogger:
    """Logger for Aviator game round history"""
    
    def __init__(self, csv_filename="aviator_rounds_history.csv"):
        """
        Initialize logger with CSV file
        
        Args:
            csv_filename: Name of CSV file to store history
        """
        self.csv_filename = csv_filename
        self.fieldnames = ['timestamp', 'round_no', 'multiplier']
        self._ensure_csv_exists()
    
    def _ensure_csv_exists(self):
        """Create CSV file with headers if it doesn't exist"""
        if not os.path.exists(self.csv_filename):
            with open(self.csv_filename, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=self.fieldnames)
                writer.writeheader()
    
    def _generate_round_no(self, timestamp):
        """
        Generate round number from timestamp
        Format: YYYYMMDDHHMMSS
        
        Args:
            timestamp: datetime object
            
        Returns:
            str: Round number
        """
        return timestamp.strftime("%Y%m%d%H%M%S")
    
    def validate_multiplier(self, multiplier):
        """
        Validate multiplier value
        
        Args:
            multiplier: Multiplier value to validate
            
        Returns:
            tuple: (is_valid: bool, validated_value: float or None, error_msg: str)
        """
        try:
            # Convert to float
            mult_float = float(multiplier)
            
            # Check if >= 1.00
            if mult_float < 1.0:
                return False, None, f"Multiplier {mult_float} is less than 1.00"
            
            # Check for reasonable upper bound (to catch OCR errors)
            if mult_float > 10000.0:
                return False, None, f"Multiplier {mult_float} exceeds reasonable limit (10000x)"
            
            return True, mult_float, ""
            
        except (ValueError, TypeError) as e:
            return False, None, f"Invalid multiplier value: {multiplier} - {str(e)}"
    
    def log_round(self, multiplier, custom_timestamp=None):
        """
        Log a completed round to CSV file
        
        Args:
            multiplier: Final multiplier value of the round
            custom_timestamp: Optional datetime object (uses current time if None)
            
        Returns:
            tuple: (success: bool, round_no: str or None, error_msg: str)
        """
        # Validate multiplier
        is_valid, validated_mult, error_msg = self.validate_multiplier(multiplier)
        if not is_valid:
            print(f"❌ Validation failed: {error_msg}")
            return False, None, error_msg
        
        # Get timestamp
        timestamp = custom_timestamp if custom_timestamp else datetime.now()
        timestamp_str = timestamp.strftime("%Y-%m-%d %H:%M:%S")
        round_no = self._generate_round_no(timestamp)
        
        # Write to CSV
        try:
            with open(self.csv_filename, 'a', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=self.fieldnames)
                writer.writerow({
                    'timestamp': timestamp_str,
                    'round_no': round_no,
                    'multiplier': f"{validated_mult:.2f}"
                })
            
            print(f"✅ Logged: Round {round_no} | {timestamp_str} | {validated_mult:.2f}x")
            return True, round_no, ""
            
        except Exception as e:
            error_msg = f"Failed to write to CSV: {str(e)}"
            print(f"❌ {error_msg}")
            return False, None, error_msg
    
    def get_statistics(self):
        """
        Get statistics from round history
        
        Returns:
            dict: Statistics including count, min, max, average multiplier
        """
        if not os.path.exists(self.csv_filename):
            return {
                'total_rounds': 0,
                'min_multiplier': 0,
                'max_multiplier': 0,
                'avg_multiplier': 0
            }
        
        try:
            with open(self.csv_filename, 'r') as f:
                reader = csv.DictReader(f)
                rounds = list(reader)
                
                if not rounds:
                    return {
                        'total_rounds': 0,
                        'min_multiplier': 0,
                        'max_multiplier': 0,
                        'avg_multiplier': 0
                    }
                
                multipliers = [float(r['multiplier']) for r in rounds]
                
                return {
                    'total_rounds': len(multipliers),
                    'min_multiplier': min(multipliers),
                    'max_multiplier': max(multipliers),
                    'avg_multiplier': sum(multipliers) / len(multipliers)
                }
        except Exception as e:
            print(f"Error reading statistics: {e}")
            return {
                'total_rounds': 0,
                'min_multiplier': 0,
                'max_multiplier': 0,
                'avg_multiplier': 0
            }


class MultiplierReader:
    """Real-time multiplier reader for Aviator game"""
    
    def __init__(self, region, enable_logging=True, csv_filename="aviator_rounds_history.csv"):
        """
        Initialize reader with screen region
        
        Args:
            region: dict with keys 'top', 'left', 'width', 'height'
            enable_logging: Whether to automatically log rounds to CSV
            csv_filename: Name of CSV file for logging
        """
        self.region = region
        self.last_valid_multiplier = None
        self.flight_in_progress = False
        self.last_print_was_awaiting = False
        
        # Logging setup
        self.enable_logging = enable_logging
        self.logger = AviatorHistoryLogger(csv_filename) if enable_logging else None
        self.round_start_multiplier = None
        self.round_peak_multiplier = None
        
    def preprocess_for_ocr(self, img):
        """Convert image to grayscale and apply thresholding for better OCR"""
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)
        return thresh
    
    def capture_region(self):
        """Capture the multiplier screen region"""
        try:
            with mss.mss() as sct:
                img = np.array(sct.grab(self.region))
                return img[..., :3]  # Drop alpha channel
        except Exception as e:
            print(f"Error capturing screen region: {e}")
            return None
    
    def fast_extract_multiplier_or_status(self, frame):
        """Extract multiplier value or status message from frame"""
        gray = self.preprocess_for_ocr(frame)
        
        # Optimized config for speed
        config = r'--psm 7 --oem 3 -c tessedit_char_whitelist=0123456789.xABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'
        raw = pytesseract.image_to_string(gray, config=config).strip().replace('\n', '').replace(' ', '')
        
        # Check for "AWAITING NEXT FLIGHT" status
        if "AWAITING" in raw.upper() and "FLIGHT" in raw.upper():
            return "AWAITING NEXT FLIGHT"
        
        # Check if we have a number pattern
        if re.search(r'\d{1,3}(\.\d+)?', raw):
            return raw
        
        return ""
    
    def clean_and_validate_multiplier(self, raw_value, last_valid=None, in_flight=False):
        """
        Clean and validate multiplier value with STRICT increasing validation.
        Returns float if valid, None if invalid.
        """
        if not raw_value or raw_value == "AWAITING NEXT FLIGHT":
            return None
        
        # Remove 'x' or 'X' suffix
        cleaned = re.sub(r'[xX]$', '', raw_value)
        
        # Try to extract a valid number
        match = re.search(r'(\d{1,3}\.\d+)', cleaned)
        if not match:
            return None
        
        try:
            mult = float(match.group(1))
            
            # Validation rules:
            # 1. Must be >= 1.00
            if mult < 1.0:
                return None
            
            # 2. Reasonable upper limit
            if mult > 1000.0:
                return None
            
            # 3. STRICT: During flight, must ALWAYS increase
            if in_flight and last_valid:
                # Must be strictly greater (with small tolerance for rounding)
                if mult <= last_valid * 0.99:  # Allow 1% tolerance
                    return None  # Reject decreasing values
                
                # Also reject values that jump too much (likely OCR error)
                if mult > last_valid * 2.0:  # More than 2x jump
                    return None
            
            # 4. New flight detection: value < 1.5 after high value
            if last_valid and last_valid > 1.5 and mult < 1.5:
                return mult  # New flight starting
                
            return mult
        except (ValueError, AttributeError):
            return None
    
    def read_current_multiplier(self):
        """
        Read current multiplier value from screen.

        Returns:
            float or None: Current multiplier value, or None if not readable
        """
        frame = self.capture_region()
        if frame is None:
            return None
        value = self.fast_extract_multiplier_or_status(frame)
        
        if value == "AWAITING NEXT FLIGHT":
            # Round ended - log it before resetting
            if self.enable_logging and self.round_peak_multiplier and self.round_peak_multiplier >= 1.0:
                self.logger.log_round(self.round_peak_multiplier)
            
            # Reset state
            self.flight_in_progress = False
            self.last_valid_multiplier = None
            self.round_start_multiplier = None
            self.round_peak_multiplier = None
            return None
        elif value:
            validated = self.clean_and_validate_multiplier(
                value, 
                self.last_valid_multiplier, 
                self.flight_in_progress
            )
            
            if validated:
                # Check if this is a new flight
                if self.last_valid_multiplier and self.last_valid_multiplier > 1.5 and validated < 1.5:
                    # Log previous round before starting new one
                    if self.enable_logging and self.round_peak_multiplier and self.round_peak_multiplier >= 1.0:
                        self.logger.log_round(self.round_peak_multiplier)
                    
                    self.flight_in_progress = False  # Reset for new flight
                    self.round_start_multiplier = None
                    self.round_peak_multiplier = None
                
                # Track round stats
                if not self.flight_in_progress:
                    self.round_start_multiplier = validated
                
                # Update peak multiplier
                if self.round_peak_multiplier is None or validated > self.round_peak_multiplier:
                    self.round_peak_multiplier = validated
                
                self.last_valid_multiplier = validated
                self.flight_in_progress = True
                return validated
        
        return None
    
    def wait_for_multiplier(self, target_multiplier, timeout=60, check_interval=0.03):
        """
        Wait until multiplier reaches target value.
        
        Args:
            target_multiplier: Target multiplier to wait for
            timeout: Maximum seconds to wait
            check_interval: How often to check (seconds)
            
        Returns:
            tuple: (success: bool, actual_multiplier: float or None)
        """
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            current = self.read_current_multiplier()
            
            if current is None:
                # Flight ended (crashed or awaiting)
                return False, self.last_valid_multiplier
            
            if current >= target_multiplier:
                return True, current
            
            time.sleep(check_interval)
        
        # Timeout
        return False, self.last_valid_multiplier
    
    def has_crashed(self):
        """
        Check if flight has crashed (AWAITING state detected).

        Returns:
            bool: True if crashed/awaiting, False if still flying
        """
        frame = self.capture_region()
        if frame is None:
            return False
        value = self.fast_extract_multiplier_or_status(frame)

        if value == "AWAITING NEXT FLIGHT":
            return True

        return False
    
    def reset(self):
        """Reset internal state"""
        self.last_valid_multiplier = None
        self.flight_in_progress = False
        self.last_print_was_awaiting = False
        self.round_start_multiplier = None
        self.round_peak_multiplier = None


# Standalone testing
def main_loop_test():
    """Test loop for multiplier reader with automatic logging"""
    # Define multiplier region
    multiplier_region = {"top": 506, "left": 330, "width": 322, "height": 76}
    
    # Initialize with logging enabled
    reader = MultiplierReader(multiplier_region, enable_logging=True)
    
    print("Starting multiplier tracker with AUTO-LOGGING...")
    print("Rounds will be saved to aviator_rounds_history.csv")
    print("Press Ctrl+C to stop.\n")
    
    try:
        while True:
            mult = reader.read_current_multiplier()
            
            if mult:
                # Flight in progress - print on same line with carriage return
                print(f"{mult:.2f}x", end='\r', flush=True)
                reader.last_print_was_awaiting = False
            elif not reader.flight_in_progress:
                # Flight not in progress - print on new line only once
                if not reader.last_print_was_awaiting:
                    print("\nAWAITING NEXT FLIGHT", flush=True)
                    reader.last_print_was_awaiting = True
            
            time.sleep(0.03)
    except KeyboardInterrupt:
        print("\n\nStopped.")
        
        # Show session statistics
        if reader.logger:
            print("\n=== Session Statistics ===")
            stats = reader.logger.get_statistics()
            print(f"Total Rounds Logged: {stats['total_rounds']}")
            if stats['total_rounds'] > 0:
                print(f"Min Multiplier: {stats['min_multiplier']:.2f}x")
                print(f"Max Multiplier: {stats['max_multiplier']:.2f}x")
                print(f"Avg Multiplier: {stats['avg_multiplier']:.2f}x")


if __name__ == "__main__":
    main_loop_test()