"""Game state detection using OCR and clipboard reading."""

import time
import pyautogui
import cv2
import numpy as np
from utils.clipboard_utils import clear_clipboard, read_clipboard, select_and_copy_text, parse_multiplier_from_text


class GameStateDetector:
    """Enhanced detector with OCR and clipboard reading capabilities."""
    
    def __init__(self, region):
        """
        Initialize game state detector.
        
        Args:
            region: Tuple (x, y, width, height) for multiplier region
        """
        self.region = region
        
        # Try to import pytesseract
        try:
            import pytesseract
            self.pytesseract = pytesseract
            self.tesseract_available = True
        except:
            self.pytesseract = None
            self.tesseract_available = False
            print("⚠️ Tesseract not available - OCR features disabled")
    
    def read_multiplier_from_clipboard(self):
        """
        Read multiplier from clipboard with proper cleanup.
        
        Returns:
            float or None: Multiplier value or None if failed
        """
        try:
            # Clear clipboard
            clear_clipboard()
            time.sleep(0.1)
            
            # Select text coordinates (adjust these based on your setup)
            x1, y1 = 19, 1101
            x2, y2 = 98, 1106
            
            # Select and copy text
            if not select_and_copy_text(x1, y1, x2, y2):
                return None
            
            # Read clipboard
            text = read_clipboard()
            if not text:
                return None
            
            # Parse multiplier
            multiplier = parse_multiplier_from_text(text)
            
            # Clear clipboard after read
            clear_clipboard()
            
            return multiplier
            
        except Exception as e:
            print(f"Error reading multiplier from clipboard: {e}")
            return None
    
    def read_text_in_region(self):
        """
        OCR text from multiplier region.
        
        Returns:
            str or None: Detected state ('AWAITING', 'ENDED', 'UNKNOWN') or None
        """
        if not self.tesseract_available:
            return None
        
        try:
            image = pyautogui.screenshot(region=self.region)
            img_array = np.array(image)
            gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
            
            # Apply threshold
            _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)
            
            # OCR
            text = self.pytesseract.image_to_string(thresh, config='--oem 3 --psm 6')
            
            if text:
                text = text.strip().upper()
                # Normalize common OCR errors
                text = text.replace('0', 'O').replace('1', 'I')
                
                # Check for keywords
                if any(kw in text for kw in ['AWAITING', 'AWAIT', 'NEXT', 'FLIGHT']):
                    return 'AWAITING'
                if any(kw in text for kw in ['FLEW', 'CRASH']):
                    return 'ENDED'
            
            return 'UNKNOWN'
        except Exception as e:
            print(f"Error reading text in region: {e}")
            return None
    
    def is_awaiting_next_flight(self):
        """
        Check if game is in 'awaiting next flight' state.
        
        Returns:
            bool: True if awaiting, False otherwise
        """
        state = self.read_text_in_region()
        return state == 'AWAITING'
    
    def is_game_already_running(self):
        """
        Check if game is currently running (more aggressive detection).
        
        Returns:
            bool: True if game is running, False otherwise
        """
        state = self.read_text_in_region()
        # Only return False if we're CERTAIN it's awaiting
        # If state is UNKNOWN or None, assume game might be running to be safe
        return state != 'AWAITING'
    
    def wait_for_clean_awaiting_state(self, timeout=10):
        """
        Wait for stable AWAITING state with multiple confirmations.
        
        Args:
            timeout: Maximum time to wait in seconds
        
        Returns:
            bool: True if stable AWAITING state reached, False if timeout
        """
        start = time.time()
        
        while time.time() - start < timeout:
            if self.is_awaiting_next_flight():
                time.sleep(0.3)
                # Triple check for stability
                if self.is_awaiting_next_flight():
                    time.sleep(0.2)
                    if self.is_awaiting_next_flight():
                        return True
            time.sleep(0.3)
        
        return False
    
    def has_game_crashed(self):
        """
        Check if game has crashed (transitioned to AWAITING or ENDED state).
        More reliable than just checking is_awaiting_next_flight.
        
        Returns:
            bool: True if game has crashed, False otherwise
        """
        state = self.read_text_in_region()
        # Game has crashed if we see AWAITING or ENDED
        return state in ['AWAITING', 'ENDED']
