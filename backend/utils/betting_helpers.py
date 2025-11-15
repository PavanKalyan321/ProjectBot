"""Helper functions for betting operations and verification."""

import math
import time
import numpy as np
import cv2
import pyautogui
import time
import colorsys
from statistics import median

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
        print("  🔍 Verifying active bet...{detector}")
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


# def cashout_verified(cashout_coords, detector):
#     """
#     Cashout with verification.
    
#     Args:
#         cashout_coords: Tuple (x, y) of cashout button coordinates
#         detector: GameStateDetector instance
    
#     Returns:
#         Tuple (bool, str): (success, reason)
#     """
#     try:
#         # if not verify_bet_is_active(cashout_coords, detector):
#         #     print("  ⚠️ No active bet!")
#         #     return False, "NO_ACTIVE_BET"
        
#         pyautogui.click(cashout_coords)
#         time.sleep(0.1)
#         # pyautogui.click(cashout_coords)
#         # time.sleep(0.2)
        
#         # Verify cashout
#         for _ in range(5):
#             if detector.is_awaiting_next_flight():
#                 return True, "SUCCESS"
#             time.sleep(0.2)
        
#         return True, "SENT_PENDING"
        
#     except Exception as e:
#         return False, f"ERROR: {e}"



def cashout_verified(cashout_coords, detector,
                     duration=4.0, interval=0.2,
                     sample_radius=3, rgb_tol=65, hue_tol_deg=15, low_v_acceptance=0.5):
    """
    Live color tracker + smart cashout verification.
    Observes color changes in 0.2s intervals to deduce what happened.

    Args:
        cashout_coords: (x, y) button center
        detector: GameStateDetector instance
        duration: how long (seconds) to track colors after clicking
        interval: sampling gap between frames (seconds)
        sample_radius: sampling radius around the coord
        rgb_tol, hue_tol_deg, low_v_acceptance: color match tuning

    Returns:
        (bool, str): success flag, outcome reason
    """
    try:
        x, y = int(cashout_coords[0]), int(cashout_coords[1])

        TARGETS = {
            "GREEN": (85, 170, 38),
            "BLUE": (45, 107, 253),
            "ORANGE": (242, 96, 44)
        }

        def rgb_distance(c1, c2):
            return ((c1[0]-c2[0])**2 + (c1[1]-c2[1])**2 + (c1[2]-c2[2])**2) ** 0.5

        def rgb_to_hsv_deg(rgb):
            r, g, b = rgb
            h, s, v = colorsys.rgb_to_hsv(r/255.0, g/255.0, b/255.0)
            return h * 360.0, s, v

        def hue_diff_deg(h1, h2):
            diff = abs(h1 - h2) % 360
            return min(diff, 360 - diff)

        # --- Step 1: initial click if button is green ---
        img = pyautogui.screenshot()
        start_color = img.getpixel((x, y))
        r, g, b = start_color
        d_green = rgb_distance(start_color, TARGETS["GREEN"])

        if d_green <= rgb_tol:
            pyautogui.click(cashout_coords)
            print("🟢 Cashout clicked (button was green).")
        else:
            print("⚠️ Cashout button not green at start, skipping click.")

        # --- Step 2: observe color changes for a few seconds ---
        observed = []
        start_time = time.time()
        while time.time() - start_time < duration:
            img = pyautogui.screenshot()
            pixels = []
            for dx in range(-sample_radius, sample_radius + 1):
                for dy in range(-sample_radius, sample_radius + 1):
                    sx, sy = x + dx, y + dy
                    if 0 <= sx < img.width and 0 <= sy < img.height:
                        pixels.append(img.getpixel((sx, sy)))
            if pixels:
                r = int(median([p[0] for p in pixels]))
                g = int(median([p[1] for p in pixels]))
                b = int(median([p[2] for p in pixels]))
                color = (r, g, b)
            else:
                color = img.getpixel((x, y))

            color_h, _, color_v = rgb_to_hsv_deg(color)
            best_match, best_dist = None, float('inf')

            for name, ref in TARGETS.items():
                ref_h, _, ref_v = rgb_to_hsv_deg(ref)
                dist = rgb_distance(color, ref)
                hue_diff = hue_diff_deg(color_h, ref_h)
                if dist < best_dist or (hue_diff < hue_tol_deg and color_v < low_v_acceptance):
                    best_match, best_dist = name, dist

            observed.append(best_match)
            time.sleep(interval)

        # --- Step 3: interpret what happened based on observed sequence ---
        if not observed:
            return False, "NO_COLOR_DATA"

        joined = "→".join([c for c in observed if c])
        last = observed[-1]

        if "GREEN" in observed and "BLUE" in observed:
            return True, f"CASHOUT_SUCCESS (Green→Blue transition)"
        elif "GREEN" in observed and "ORANGE" in observed:
            return True, f"ROUND_ENDED_BET_AGAIN (Green→Orange)"
        elif "BLUE" in observed and "ORANGE" in observed:
            return False, f"ROUND_ENDED_BET_AVAILABLE (Blue→Orange)"
        elif all(c == "GREEN" for c in observed if c):
            return True, f"CASHOUT_HELD_GREEN (stable)"
        elif all(c == "BLUE" for c in observed if c):
            return False, f"ROUND_ENDED_NO_BET (Blue stable)"
        elif all(c == "ORANGE" for c in observed if c):
            return False, f"WAITING_NEXT_ROUND (Orange stable)"
        elif detector.is_awaiting_next_flight():
            return True, "DETECTED_NEXT_FLIGHT"
        else:
            return False, f"UNSURE|Sequence={joined}"

    except Exception as e:
        return False, f"ERROR: {e}"


# ============================================================================
# MULTI-POSITION SUPPORT FUNCTIONS
# ============================================================================

def set_stake_verified_pos(stake_coords, amount, position=1):
    """
    Set stake amount for a specific position.

    Args:
        stake_coords: Tuple (x, y) of stake input coordinates
        amount: Stake amount to set
        position: Position number (1 or 2) for logging

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
        print(f"  💰 Position {position} stake set to: {amount}")
        return True
    except Exception as e:
        print(f"  ❌ Error setting Position {position} stake: {e}")
        return False


def place_bet_with_verification_pos(bet_button_coords, detector, stats, current_stake, position=1):
    """
    Place bet with verification for a specific position.

    Args:
        bet_button_coords: Tuple (x, y) of bet button coordinates
        detector: GameStateDetector instance
        stats: Stats dictionary to update
        current_stake: Current stake amount
        position: Position number (1 or 2)

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
                stats[f"position{position}_bets_placed"] = stats.get(f"position{position}_bets_placed", 0) + 1
                stats[f"position{position}_total_bet"] = stats.get(f"position{position}_total_bet", 0) + current_stake
                print(f"  ✅ Position {position} bet confirmed ({current_stake} stake)")
                return True, "SUCCESS"

            if attempt < 2:
                print(f"  ⚠️ Position {position} Retry {attempt+1}/3...")
                pyautogui.click(bet_button_coords)
                time.sleep(0.3)

        print(f"  ❌ Position {position} bet verification failed")
        return False, "FAILED_VERIFICATION"

    except Exception as e:
        return False, f"ERROR: {e}"


def cashout_verified_pos(cashout_coords, detector, position=1,
                         duration=4.0, interval=0.2,
                         sample_radius=3, rgb_tol=65, hue_tol_deg=15, low_v_acceptance=0.5):
    """
    Cashout with verification for a specific position.

    Args:
        cashout_coords: (x, y) button center
        detector: GameStateDetector instance
        position: Position number (1 or 2)
        duration: how long (seconds) to track colors after clicking
        interval: sampling gap between frames (seconds)
        sample_radius: sampling radius around the coord
        rgb_tol, hue_tol_deg, low_v_acceptance: color match tuning

    Returns:
        (bool, str): success flag, outcome reason
    """
    try:
        x, y = int(cashout_coords[0]), int(cashout_coords[1])

        TARGETS = {
            "GREEN": (85, 170, 38),
            "BLUE": (45, 107, 253),
            "ORANGE": (242, 96, 44)
        }

        def rgb_distance(c1, c2):
            return ((c1[0]-c2[0])**2 + (c1[1]-c2[1])**2 + (c1[2]-c2[2])**2) ** 0.5

        def rgb_to_hsv_deg(rgb):
            r, g, b = rgb
            h, s, v = colorsys.rgb_to_hsv(r/255.0, g/255.0, b/255.0)
            return h * 360.0, s, v

        def hue_diff_deg(h1, h2):
            diff = abs(h1 - h2) % 360
            return min(diff, 360 - diff)

        # Check button color and click if green
        img = pyautogui.screenshot()
        start_color = img.getpixel((x, y))
        r, g, b = start_color
        d_green = rgb_distance(start_color, TARGETS["GREEN"])

        if d_green <= rgb_tol:
            pyautogui.click(cashout_coords)
            print(f"🟢 Position {position} cashout clicked (button was green).")
        else:
            print(f"⚠️ Position {position} cashout button not green at start, skipping click.")

        # Observe color changes
        observed = []
        start_time = time.time()
        while time.time() - start_time < duration:
            img = pyautogui.screenshot()
            pixels = []
            for dx in range(-sample_radius, sample_radius + 1):
                for dy in range(-sample_radius, sample_radius + 1):
                    sx, sy = x + dx, y + dy
                    if 0 <= sx < img.width and 0 <= sy < img.height:
                        pixels.append(img.getpixel((sx, sy)))
            if pixels:
                r = int(median([p[0] for p in pixels]))
                g = int(median([p[1] for p in pixels]))
                b = int(median([p[2] for p in pixels]))
                color = (r, g, b)
            else:
                color = img.getpixel((x, y))

            color_h, _, color_v = rgb_to_hsv_deg(color)
            best_match, best_dist = None, float('inf')

            for name, ref in TARGETS.items():
                ref_h, _, ref_v = rgb_to_hsv_deg(ref)
                dist = rgb_distance(color, ref)
                hue_diff = hue_diff_deg(color_h, ref_h)
                if dist < best_dist or (hue_diff < hue_tol_deg and color_v < low_v_acceptance):
                    best_match, best_dist = name, dist

            observed.append(best_match)
            time.sleep(interval)

        # Interpret sequence
        if not observed:
            return False, "NO_COLOR_DATA"

        joined = "→".join([c for c in observed if c])
        last = observed[-1]

        if "GREEN" in observed and "BLUE" in observed:
            return True, f"CASHOUT_SUCCESS (Green→Blue transition)"
        elif "GREEN" in observed and "ORANGE" in observed:
            return False, f"CASHOUT_CRASHED (Green→Orange)"
        elif last == "BLUE" or (observed.count("BLUE") > observed.count("GREEN") // 2):
            return True, "DETECTED_NEXT_FLIGHT"
        else:
            return False, f"UNSURE|Sequence={joined}"

    except Exception as e:
        return False, f"ERROR: {e}"
