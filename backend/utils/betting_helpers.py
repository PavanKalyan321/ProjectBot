"""Helper functions for betting operations and verification."""

import math
import time
import numpy as np
import cv2
import pyautogui


def verify_bet_placed(bet_button_coords, detector=None):
    """
    Verify bet was actually placed by checking button state.
    
    Args:
        bet_button_coords: Tuple (x, y) of bet button coordinates
        detector: GameStateDetector instance (optional, for OCR)
    
    Returns:
        Tuple (bool, str): (is_placed, button_text/status)
    """
    try:
        x, y = bet_button_coords
        region = (x - 60, y - 25, 120, 50)
        
        screenshot = pyautogui.screenshot(region=region)
        img = np.array(screenshot)
        gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
        
        # Check button color
        avg_color = np.mean(img, axis=(0, 1))
        is_green = avg_color[1] > 100 and avg_color[0] < avg_color[1]
        
        # Try OCR if detector available
        if detector and hasattr(detector, 'pytesseract'):
            try:
                text = detector.pytesseract.image_to_string(gray).strip().upper()
                
                if 'PLACE' in text or 'BET' in text:
                    return False, text
                
                if 'CANCEL' in text or 'CASH' in text:
                    return True, text
            except:
                pass
        
        return not is_green, "COLOR_CHECK"
        
    except Exception as e:
        return False, f"ERROR: {e}"


def verify_bet_is_active(cashout_coords, detector):
    """
    Check if bet is currently active.
    
    Args:
        cashout_coords: Tuple (x, y) of cashout button coordinates
        detector: GameStateDetector instance
    
    Returns:
        bool: True if bet is active, False otherwise
    """
    try:
        # Check if in awaiting state
        if detector.is_awaiting_next_flight():
            return False
        
        x, y = cashout_coords
        region = (x - 50, y - 20, 100, 40)
        screenshot = pyautogui.screenshot(region=region)
        img = np.array(screenshot)
        gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
        
        # Try OCR
        if hasattr(detector, 'pytesseract'):
            text = detector.pytesseract.image_to_string(gray).strip().upper()
            return 'CASH' in text or 'CANCEL' in text
        
        return True
    except:
        return False


def estimate_multiplier(elapsed_time):
    """
    Estimate multiplier based on elapsed time.
    
    Args:
        elapsed_time: Time elapsed in seconds
    
    Returns:
        float: Estimated multiplier value
    """
    multiplier = math.exp(0.15 * elapsed_time)
    return round(multiplier, 2)


def increase_stake(current_stake, increase_percent, max_stake, stats):
    """
    Increase stake by percentage.
    
    Args:
        current_stake: Current stake amount
        increase_percent: Percentage to increase
        max_stake: Maximum allowed stake
        stats: Stats dictionary to update
    
    Returns:
        int: New stake amount
    """
    old_stake = current_stake
    new_stake = current_stake * (1 + increase_percent / 100)
    
    if new_stake > max_stake:
        new_stake = max_stake
    
    new_stake = int(new_stake)
    
    if new_stake > stats.get("max_stake_reached", 0):
        stats["max_stake_reached"] = new_stake
    
    if new_stake != old_stake:
        print(f"  📈 Stake: {old_stake} → {new_stake}")
    
    return new_stake


def reset_stake(initial_stake, stats):
    """
    Reset stake to initial value.
    
    Args:
        initial_stake: Initial stake amount
        stats: Stats dictionary to update
    
    Returns:
        int: Reset stake amount
    """
    stats["current_streak"] = 0
    print(f"  📉 Stake reset to: {initial_stake}")
    return initial_stake


def set_stake_verified(stake_coords, amount):
    """
    Set stake amount and verify it changed.
    
    Args:
        stake_coords: Tuple (x, y) of stake input coordinates
        amount: Stake amount to set
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        pyautogui.click(stake_coords)
        time.sleep(0.15)
        pyautogui.hotkey('ctrl', 'a')
        time.sleep(0.1)
        pyautogui.press('backspace')
        time.sleep(0.1)
        pyautogui.typewrite(str(amount), interval=0.05)
        time.sleep(0.2)
        return True
    except Exception as e:
        print(f"Error setting stake: {e}")
        return False


def place_bet_with_verification(bet_button_coords, detector, stats, current_stake):
    """
    Place bet with verification.
    
    Args:
        bet_button_coords: Tuple (x, y) of bet button coordinates
        detector: GameStateDetector instance
        stats: Stats dictionary to update
        current_stake: Current stake amount
    
    Returns:
        Tuple (bool, str): (success, reason)
    """
    try:
        pyautogui.click(bet_button_coords)
        time.sleep(0.4)
        
        # Verify it placed
        for attempt in range(3):
            is_placed, button_text = verify_bet_placed(bet_button_coords, detector)
            
            if is_placed:
                stats["rounds_played"] += 1
                stats["ml_bets_placed"] += 1
                stats["total_bet"] += current_stake
                print(f"  ✅ Bet confirmed")
                return True, "SUCCESS"
            
            if attempt < 2:
                print(f"  ⚠️ Retry {attempt+1}/3...")
                pyautogui.click(bet_button_coords)
                time.sleep(0.3)
        
        print(f"  ❌ Bet verification failed")
        return False, "FAILED_VERIFICATION"
        
    except Exception as e:
        return False, f"ERROR: {e}"


def cashout_verified(cashout_coords, detector):
    """
    Cashout with verification.
    
    Args:
        cashout_coords: Tuple (x, y) of cashout button coordinates
        detector: GameStateDetector instance
    
    Returns:
        Tuple (bool, str): (success, reason)
    """
    try:
        if not verify_bet_is_active(cashout_coords, detector):
            print("  ⚠️ No active bet!")
            return False, "NO_ACTIVE_BET"
        
        pyautogui.click(cashout_coords)
        time.sleep(0.1)
        pyautogui.click(cashout_coords)
        time.sleep(0.2)
        
        # Verify cashout
        for _ in range(5):
            if detector.is_awaiting_next_flight():
                return True, "SUCCESS"
            time.sleep(0.2)
        
        return True, "SENT_PENDING"
        
    except Exception as e:
        return False, f"ERROR: {e}"
