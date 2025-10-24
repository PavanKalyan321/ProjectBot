import mss
import numpy as np
import cv2
import pytesseract
import re
import time

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

class MultiplierReader:
    """Real-time multiplier reader for Aviator game"""
    
    def __init__(self, region):
        """
        Initialize reader with screen region
        
        Args:
            region: dict with keys 'top', 'left', 'width', 'height'
        """
        self.region = region
        self.last_valid_multiplier = None
        self.flight_in_progress = False
        self.last_print_was_awaiting = False
        
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
            self.flight_in_progress = False
            self.last_valid_multiplier = None
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
                    self.flight_in_progress = False  # Reset for new flight
                
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


# Standalone testing
def main_loop_test():
    """Test loop for multiplier reader"""
    # Define multiplier region
    multiplier_region = {"top": 506, "left": 330, "width": 322, "height": 76}
    
    reader = MultiplierReader(multiplier_region)
    
    print("Starting multiplier tracker...")
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
        print("\nStopped.")


if __name__ == "__main__":
    main_loop_test()