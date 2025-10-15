import pyautogui
import keyboard
import time

def capture_history_region(label="History Bar"):
    """
    Capture top-left and bottom-right coordinates for the history bar region.
    Returns (x, y, width, height).
    """
    print("\n=== Capture region for:", label, "===")
    print("\n1) Move your mouse to the **TOP-LEFT** corner of the region")
    input("   -> Hover mouse, then press Enter here in the terminal...")
    x1, y1 = pyautogui.position()
    print(f"   Captured top-left: ({x1}, {y1})")

    time.sleep(0.5)
    print("\n2) Move your mouse to the **BOTTOM-RIGHT** corner of the region")
    input("   -> Hover mouse, then press Enter here in the terminal...")
    x2, y2 = pyautogui.position()
    print(f"   Captured bottom-right: ({x2}, {y2})")

    region = (x1, y1, x2 - x1, y2 - y1)
    print(f"\n✅ Region saved: {region}\n")
    return region


capture_history_region()