import mss
import numpy as np
import cv2
import pytesseract
import re
import time

# Optional: Set path to tesseract executable if needed
# pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# Define only the multiplier region
multiplier_region = {"top": 506, "left": 330, "width": 322, "height": 76}

# Global variable to track last valid multiplier
last_valid_multiplier = None
flight_in_progress = False

def preprocess_for_ocr(img):
    """Convert image to grayscale and apply thresholding for better OCR"""
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)
    return thresh

def capture_region(region):
    """Capture a specific screen region"""
    with mss.mss() as sct:
        img = np.array(sct.grab(region))
        return img[..., :3]  # Drop alpha channel

def fast_extract_multiplier_or_status(frame):
    """Extract multiplier value or status message from frame"""
    gray = preprocess_for_ocr(frame)
    
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

def clean_and_validate_multiplier(raw_value, last_valid=None, in_flight=False):
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
            if mult > last_valid * 2.0:  # More than 2x jump (increased from 1.5)
                return None
        
        # 4. New flight detection: value < 1.5 after high value
        if last_valid and last_valid > 1.5 and mult < 1.5:
            return mult  # New flight starting
            
        return mult
    except (ValueError, AttributeError):
        return None

def interpolate_missing_values(last_val, current_val, step=0.02):
    """
    Generate intermediate values between last_val and current_val.
    Only interpolates if gap is significant (> 0.15).
    """
    gap = current_val - last_val
    
    # Only interpolate if gap is significant
    if gap > 0.15:
        # Generate intermediate values
        num_steps = int(gap / step)
        if num_steps > 0:
            intermediates = []
            for i in range(1, num_steps + 1):
                intermediate = last_val + (step * i)
                if intermediate < current_val:
                    intermediates.append(intermediate)
            return intermediates
    
    return []

def main_loop_fast():
    """Fast synchronous main loop with interpolation for missing values"""
    global last_valid_multiplier, flight_in_progress
    
    print("Starting fast multiplier tracker (with interpolation)...")
    print("Press Ctrl+C to stop.\n")
    
    with mss.mss() as sct:
        try:
            while True:
                # Capture
                frame = np.array(sct.grab(multiplier_region))[..., :3]
                
                # Process
                value = fast_extract_multiplier_or_status(frame)
                
                if value == "AWAITING NEXT FLIGHT":
                    if flight_in_progress:  # Only print once
                        print("AWAITING NEXT FLIGHT")
                    flight_in_progress = False
                    last_valid_multiplier = None
                elif value:
                    validated = clean_and_validate_multiplier(
                        value, 
                        last_valid_multiplier, 
                        flight_in_progress
                    )
                    
                    if validated:
                        # Check if this is a new flight
                        if last_valid_multiplier and last_valid_multiplier > 1.5 and validated < 1.5:
                            flight_in_progress = False  # Reset for new flight
                        
                        # Interpolate missing values if gap is large
                        if last_valid_multiplier and validated > last_valid_multiplier:
                            missing_values = interpolate_missing_values(
                                last_valid_multiplier, 
                                validated
                            )
                            
                            # Print interpolated values
                            for intermediate in missing_values:
                                print(f"{intermediate:.2f}")
                        
                        # Print actual captured value
                        last_valid_multiplier = validated
                        flight_in_progress = True
                        print(f"{validated:.2f}")
                
                time.sleep(0.03)  # Increased to ~33 FPS (faster than 0.05)
        except KeyboardInterrupt:
            print("\nStopped.")

if __name__ == "__main__":
    main_loop_fast()