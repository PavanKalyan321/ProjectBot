"""
Enhanced Clipboard utility functions with robust multiplier parsing.
Handles jammed values, dashes, and special characters.
Cross-platform compatible (Windows/Linux/macOS).
"""

import time
import re
import pyautogui
import platform

# Platform detection
IS_WINDOWS = platform.system() == 'Windows'
IS_LINUX = platform.system() == 'Linux'
IS_MAC = platform.system() == 'Darwin'

# Import platform-specific clipboard modules
if IS_WINDOWS:
    try:
        import win32clipboard
        import win32con
        CLIPBOARD_AVAILABLE = True
    except ImportError:
        print("Warning: pywin32 not installed. Falling back to pyperclip.")
        import pyperclip
        CLIPBOARD_AVAILABLE = False
else:
    # Linux/Mac - use pyperclip
    import pyperclip
    CLIPBOARD_AVAILABLE = False


def clear_clipboard():
    """Clear the system clipboard (cross-platform)."""
    try:
        if CLIPBOARD_AVAILABLE and IS_WINDOWS:
            # Windows with win32clipboard
            win32clipboard.OpenClipboard()
            win32clipboard.EmptyClipboard()
            win32clipboard.CloseClipboard()
        else:
            # Linux/Mac or Windows fallback - use pyperclip
            pyperclip.copy('')
        return True
    except Exception as e:
        print(f"Error clearing clipboard: {e}")
        return False


def read_clipboard():
    """
    Read text from clipboard (cross-platform).

    Returns:
        str or None: Clipboard text content or None if failed
    """
    try:
        if CLIPBOARD_AVAILABLE and IS_WINDOWS:
            # Windows with win32clipboard
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
        else:
            # Linux/Mac or Windows fallback - use pyperclip
            text = pyperclip.paste()
            return text.strip() if text else None

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

        pyautogui.mouseDown()
        pyautogui.mouseUp()
        
        return True
    except Exception as e:
        print(f"Error selecting and copying text: {e}")
        return False


def extract_all_multipliers(text):
    """
    Extract ALL multipliers from text (handles jammed values).
    
    Args:
        text: Text containing one or more multipliers
        
    Returns:
        list: All valid multipliers found, in order
        
    Examples:
        "2.54 3.45" -> [2.54, 3.45]
        "2.54 - 3.45" -> [2.54, 3.45]
        "2.54x 3.45x" -> [2.54, 3.45]
        "- 2.54" -> [2.54]
    """
    if not text:
        return []
    
    text = str(text).strip()
    
    # Replace common separators with spaces
    text = text.replace(',', ' ').replace('|', ' ').replace('/', ' ')
    
    # Split by whitespace and dashes
    parts = re.split(r'[\s\-]+', text)
    
    multipliers = []
    
    for part in parts:
        if not part or part == '-':
            continue
        
        # Remove 'x' suffix/prefix and any other non-numeric chars except decimal
        part = re.sub(r'[^\d.]', '', part).strip()
        
        if not part:
            continue
        
        try:
            value = float(part)
            
            # Validate range (0.01 to 10000)
            if 0.01 <= value <= 10000:
                multipliers.append(value)
        except ValueError:
            continue
    
    return multipliers


def parse_multiplier_from_text(text):
    """
    Parse multiplier value from text (enhanced to handle multiple values).
    Returns the LAST multiplier found (most recent).
    
    Args:
        text: Text containing multiplier (e.g., "2.5x", "x3.78", "2.0", "2.5 3.4", "2.5 - 3.4")
    
    Returns:
        float or None: Last parsed multiplier value or None if not found
        
    Examples:
        "2.5x" -> 2.5
        "2.5 3.4" -> 3.4 (last one)
        "2.5 - 3.4" -> 3.4 (ignores dash)
        "- 2.5" -> 2.5
    """
    if not text:
        return None
    
    # Extract all multipliers
    multipliers = extract_all_multipliers(text)
    
    # Return the last one (most recent/rightmost)
    if multipliers:
        return multipliers[-1]
    
    return None


def parse_multiplier_first(text):
    """
    Parse the FIRST multiplier from text (leftmost).
    Useful when you want the older value from jammed text.
    
    Args:
        text: Text containing multiplier(s)
    
    Returns:
        float or None: First parsed multiplier value or None if not found
    """
    if not text:
        return None
    
    multipliers = extract_all_multipliers(text)
    
    if multipliers:
        return multipliers[0]
    
    return None


# Additional optional imports for mutex (Windows only)
if IS_WINDOWS:
    try:
        import win32event
        import win32api
    except Exception:
        win32event = None
        win32api = None
else:
    win32event = None
    win32api = None


def acquire_mutex(mutex_name: str = "Global\\ClipboardUtilsMutex"):
    """
    Acquire a named Win32 mutex to avoid multiple script/process instances.
    Windows only - returns None on other platforms.
    Returns the mutex handle on success, None otherwise.
    """
    if not IS_WINDOWS or win32event is None or win32api is None:
        return None
    try:
        handle = win32event.CreateMutex(None, False, mutex_name)
        return handle
    except Exception:
        return None


def is_clipboard_busy(poll_seconds: float = 0.2) -> bool:
    """
    Quick non-blocking check if clipboard is accessible.
    Returns True if clipboard appears busy/unreadable, False if likely accessible.
    """
    try:
        if CLIPBOARD_AVAILABLE and IS_WINDOWS:
            win32clipboard.OpenClipboard()
            win32clipboard.CloseClipboard()
            return False
        else:
            # On Linux/Mac, try to read clipboard
            pyperclip.paste()
            return False
    except Exception:
        time.sleep(poll_seconds)
        return True


def copy_region_to_multiplier(x1, y1, x2, y2,
                              *,
                              fast: bool = True,
                              clear_before: bool = True,
                              select_delay: float = None,
                              after_copy_wait: float = None,
                              clipboard_timeout: float = 0.5,
                              return_all: bool = False,
                              debug: bool = False):
    """
    Convenience wrapper: select region, copy, read clipboard, parse multiplier.
    Enhanced to handle jammed values and special characters.

    Args:
        x1,y1,x2,y2: region coordinates (ints)
        fast: if True uses low delays for speedy operation
        clear_before: attempt to clear clipboard before copying
        select_delay: overrides select_and_copy_text's delay param if provided
        after_copy_wait: time to wait after pressing Ctrl+C
        clipboard_timeout: time (sec) to wait for clipboard to fill
        return_all: if True, returns list of all multipliers; if False, returns last one
        debug: print debug lines

    Returns:
        float (or list if return_all=True): multiplier(s) if parsed, otherwise None (or [])
        
    Examples:
        # Region contains "2.54 3.45"
        copy_region_to_multiplier(x1,y1,x2,y2) -> 3.45 (last)
        copy_region_to_multiplier(x1,y1,x2,y2, return_all=True) -> [2.54, 3.45]
    """
    # Choose small delay values for speed if fast=True
    if select_delay is None:
        select_delay = 0.05 if fast else 0.15
    if after_copy_wait is None:
        after_copy_wait = 0.06 if fast else 0.18

    if clear_before:
        try:
            clear_clipboard()
        except Exception:
            pass

    # Use existing selection function
    ok = select_and_copy_text(x1, y1, x2, y2, delay=select_delay)
    if not ok:
        if debug:
            print("[copy_region_to_multiplier] select_and_copy_text failed")
        return [] if return_all else None

    # Wait for clipboard
    t_deadline = time.time() + clipboard_timeout
    raw = None
    while time.time() < t_deadline:
        raw = read_clipboard()
        if raw:
            break
        time.sleep(0.02)

    if debug:
        print(f"[copy_region_to_multiplier] raw clipboard: {raw!r}")

    try:
        if return_all:
            # Return all multipliers found
            vals = extract_all_multipliers(raw)
            if debug:
                print(f"[copy_region_to_multiplier] parsed all: {vals}")
            return vals
        else:
            # Return last multiplier (default behavior)
            val = parse_multiplier_from_text(raw)
            if debug:
                print(f"[copy_region_to_multiplier] parsed last: {val}")
            return val
    except Exception as e:
        if debug:
            print(f"[copy_region_to_multiplier] parse error: {e}")
        return [] if return_all else None



# Simple self-test block
if __name__ == "__main__":
    print("="*60)
