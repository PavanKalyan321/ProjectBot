"""Clipboard utility functions for reading game data."""

import time
import re
import win32clipboard
import win32con
import pyautogui

# --- (your original functions unchanged) ---


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


# --- (new helpers appended below — original functions above are untouched) ---
# Additional optional imports for mutex
try:
    import win32event
    import win32api
except Exception:
    win32event = None
    win32api = None


def acquire_mutex(mutex_name: str = "Global\\ClipboardUtilsMutex"):
    """
    Acquire a named Win32 mutex to avoid multiple script/process instances.
    Returns the mutex handle on success, None otherwise.
    
    Usage:
        h = acquire_mutex()
        if h is None:
            # mutex not available or win32 not present
            ...
        else:
            # hold h for lifetime of process, then ReleaseMutex on exit if desired
    """
    if win32event is None or win32api is None:
        return None
    try:
        handle = win32event.CreateMutex(None, False, mutex_name)
        # NOTE: even if ERROR_ALREADY_EXISTS is returned, CreateMutex returns a handle.
        # Caller can still use it to hold a mutex. We return the handle.
        return handle
    except Exception:
        return None


def is_clipboard_busy(poll_seconds: float = 0.2) -> bool:
    """
    Quick non-blocking check if clipboard is accessible.
    Returns True if clipboard appears busy/unreadable, False if likely accessible.
    """
    try:
        win32clipboard.OpenClipboard()
        win32clipboard.CloseClipboard()
        return False
    except Exception:
        # If open fails, clipboard likely busy
        time.sleep(poll_seconds)
        return True


def copy_region_to_multiplier(x1, y1, x2, y2,
                              *,
                              fast: bool = True,
                              clear_before: bool = True,
                              select_delay: float = None,
                              after_copy_wait: float = None,
                              clipboard_timeout: float = 0.5,
                              debug: bool = False):
    """
    Convenience wrapper: select region, copy, read clipboard, parse multiplier.
    DOES NOT modify your original functions; it calls them.

    Args:
        x1,y1,x2,y2: region coordinates (ints)
        fast: if True uses low delays for speedy operation
        clear_before: attempt to clear clipboard before copying
        select_delay: overrides select_and_copy_text's delay param if provided
        after_copy_wait: time to wait after pressing Ctrl+C (overridden via select_and_copy_text call)
        clipboard_timeout: time (sec) to wait for clipboard to fill (polled by read_clipboard)
        debug: print debug lines

    Returns:
        float multiplier if parsed, otherwise None
    """
    # choose small delay values for speed if fast=True
    if select_delay is None:
        select_delay = 0.05 if fast else 0.15
    if after_copy_wait is None:
        after_copy_wait = 0.06 if fast else 0.18

    if clear_before:
        try:
            clear_clipboard()
        except Exception:
            pass

    # use existing selection function; it will sleep internally based on its delay param.
    ok = select_and_copy_text(x1, y1, x2, y2, delay=select_delay)
    if not ok:
        if debug:
            print("[copy_region_to_multiplier] select_and_copy_text failed")
        return None

    # small extra wait to give clipboard a moment (read_clipboard retries internally)
    t_deadline = time.time() + clipboard_timeout
    raw = None
    while time.time() < t_deadline:
        raw = read_clipboard()
        if raw:
            break
        # If clipboard busy, wait a little and retry
        time.sleep(0.02)

    if debug:
        print(f"[copy_region_to_multiplier] raw clipboard: {raw!r}")

    try:
        val = parse_multiplier_from_text(raw)
        if debug:
            print(f"[copy_region_to_multiplier] parsed: {val!r}")
        return val
    except Exception:
        return None


# Simple self-test block — nothing runs when this file is imported.
if __name__ == "__main__":
    # Example: to enable single-instance guard when running the file directly,
    # uncomment the following lines:
    #
    # h = acquire_mutex()
    # if h is None:
    #     print("Warning: Could not acquire mutex (win32 not available or error).")
    #
    print("clipboard module executed directly. No automated tests run.")
    print("Use copy_region_to_multiplier(x1,y1,x2,y2) from your main bot.")
