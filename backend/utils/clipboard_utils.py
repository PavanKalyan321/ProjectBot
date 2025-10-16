"""Clipboard utility functions for reading game data."""

import time
import re
import win32clipboard
import win32con
import pyautogui


def clear_clipboard():
    """Clear the system clipboard."""
    try:
        win32clipboard.OpenClipboard()
        win32clipboard.EmptyClipboard()
        win32clipboard.CloseClipboard()
        return True
    except Exception as e:
        print(f"Error clearing clipboard: {e}")
        return False


def read_clipboard():
    """
    Read text from clipboard.
    
    Returns:
        str or None: Clipboard text content or None if failed
    """
    try:
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
            return None
        
        # Convert to string
        if isinstance(data, bytes):
            text = data.decode('utf-8', errors='ignore')
        else:
            text = str(data)
        
        return text.strip()
    except Exception as e:
        print(f"Error reading clipboard: {e}")
        return None


def select_and_copy_text(x1, y1, x2, y2, delay=0.1):
    """
    Select text region and copy to clipboard.
    
    Args:
        x1, y1: Top-left coordinates
        x2, y2: Bottom-right coordinates
        delay: Delay between actions in seconds
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Move to start position
        pyautogui.moveTo(x1, y1, duration=0.05)
        time.sleep(delay)
        
        # Click and drag to select
        pyautogui.mouseDown()
        pyautogui.moveTo(x2, y2, duration=0.05)
        pyautogui.mouseUp()
        time.sleep(delay)
        
        # Copy to clipboard
        pyautogui.hotkey('ctrl', 'c')
        time.sleep(0.2)
        
        return True
    except Exception as e:
        print(f"Error selecting and copying text: {e}")
        return False


def parse_multiplier_from_text(text):
    """
    Parse multiplier value from text.
    
    Args:
        text: Text containing multiplier (e.g., "2.5x", "x3.78", "2.0")
    
    Returns:
        float or None: Parsed multiplier value or None if not found
    """
    if not text:
        return None
    
    # Clean text
    text = text.strip().replace(' ', '').replace(',', '.')
    
    # Try different patterns
    patterns = [
        r'(\d+\.?\d*)x',  # "2.5x"
        r'x(\d+\.?\d*)',  # "x2.5"
        r'^(\d+\.?\d*)$'  # "2.5"
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            try:
                value = float(match.group(1))
                # Validate range
                if 0 < value <= 1000:
                    return value
            except:
                continue
    
    return None
