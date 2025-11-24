"""
Screen Coordinate Capture Tool
================================

Helps you find the exact screen coordinates of the Aviator game multiplier display.

Usage:
    python capture_coordinates.py

This tool will:
1. Take screenshots of your game
2. Let you click on the multiplier area
3. Show you the exact coordinates
4. Save coordinates to coordinates.txt
5. Display captured region for verification

Requirements:
    - mss (for screen capture)
    - opencv-python (for image display)
    - pillow (for image handling)

Author: Aviator Bot
Date: 2025-11-23
"""

import os
import sys
from pathlib import Path
from datetime import datetime

# Try to import required packages
try:
    import mss
    import numpy as np
    import cv2
    from PIL import Image
    print("✓ All required packages available")
except ImportError as e:
    print(f"✗ Missing package: {e}")
    print("Install with: pip install mss opencv-python pillow")
    sys.exit(1)


def capture_full_screen():
    """Capture the full screen."""
    try:
        with mss.mss() as sct:
            # Get primary monitor
            monitor = sct.monitors[1]
            screenshot = sct.grab(monitor)
            frame = np.array(screenshot)
            return cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
    except Exception as e:
        print(f"Error capturing screen: {e}")
        return None


def interactive_coordinate_selection():
    """
    Interactive tool to select region on screen and get coordinates.

    Instructions:
    - Move mouse to top-left corner of multiplier display
    - Click and drag to bottom-right corner
    - Screenshot saved with marked region
    - Coordinates printed
    """

    print("\n" + "=" * 70)
    print("INTERACTIVE COORDINATE SELECTION")
    print("=" * 70)

    frame = capture_full_screen()
    if frame is None:
        print("Failed to capture screen")
        return None

    # Store selection coordinates
    coordinates = {'top': 0, 'left': 0, 'bottom': 0, 'right': 0}
    drawing = False
    start_point = None

    def mouse_callback(event, x, y, flags, param):
        nonlocal drawing, start_point, frame

        if event == cv2.EVENT_LBUTTONDOWN:
            drawing = True
            start_point = (x, y)
            print(f"Start point: ({x}, {y})")

        elif event == cv2.EVENT_MOUSEMOVE:
            if drawing:
                # Show preview of selection
                temp_frame = frame.copy()
                cv2.rectangle(temp_frame, start_point, (x, y), (0, 255, 0), 2)
                cv2.imshow("Select Region - Current Selection", temp_frame)

        elif event == cv2.EVENT_LBUTTONUP:
            drawing = False
            coordinates['left'] = min(start_point[0], x)
            coordinates['top'] = min(start_point[1], y)
            coordinates['right'] = max(start_point[0], x)
            coordinates['bottom'] = max(start_point[1], y)

            print(f"End point: ({x}, {y})")
            print(f"Selection: top={coordinates['top']}, left={coordinates['left']}, "
                  f"bottom={coordinates['bottom']}, right={coordinates['right']}")

    # Display frame and wait for selection
    cv2.namedWindow("Select Region - Click and drag over multiplier area")
    cv2.setMouseCallback("Select Region - Click and drag over multiplier area", mouse_callback)

    print("\nInstructions:")
    print("1. Click and drag to select the multiplier display area")
    print("2. Start at TOP-LEFT corner of multiplier")
    print("3. Drag to BOTTOM-RIGHT corner")
    print("4. Release mouse to confirm selection")
    print("5. Press 'q' or close window when done")
    print("\n")

    cv2.imshow("Select Region - Click and drag over multiplier area", frame)

    # Wait for key press
    key = -1
    while True:
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q') or key == 27:  # 'q' or ESC
            break

    cv2.destroyAllWindows()

    if coordinates['right'] > coordinates['left'] and coordinates['bottom'] > coordinates['top']:
        return coordinates
    else:
        print("No selection made")
        return None


def manual_coordinate_input():
    """
    Manually enter coordinates via terminal.
    """
    print("\n" + "=" * 70)
    print("MANUAL COORDINATE INPUT")
    print("=" * 70)
    print("\nEnter coordinates manually:")
    print("(Top-left corner X, Y and bottom-right corner X, Y)")
    print("\nExample for default region:")
    print("  Top (Y): 506")
    print("  Left (X): 330")
    print("  Width: 322")
    print("  Height: 76")
    print("\n")

    try:
        top = int(input("Enter TOP position (Y coordinate): "))
        left = int(input("Enter LEFT position (X coordinate): "))
        width = int(input("Enter WIDTH (in pixels): "))
        height = int(input("Enter HEIGHT (in pixels): "))

        return {
            'top': top,
            'left': left,
            'bottom': top + height,
            'right': left + width,
            'width': width,
            'height': height
        }
    except ValueError:
        print("Invalid input. Please enter numbers only.")
        return None


def verify_coordinates(coords):
    """
    Verify captured coordinates by showing the region.
    """
    print("\n" + "=" * 70)
    print("VERIFYING COORDINATES")
    print("=" * 70)

    print(f"\nCoordinates found:")
    print(f"  Top (Y):    {coords['top']}")
    print(f"  Left (X):   {coords['left']}")
    print(f"  Width:      {coords['right'] - coords['left']}")
    print(f"  Height:     {coords['bottom'] - coords['top']}")

    # Capture the region
    try:
        with mss.mss() as sct:
            region = {
                "top": coords['top'],
                "left": coords['left'],
                "width": coords['right'] - coords['left'],
                "height": coords['bottom'] - coords['top']
            }

            screenshot = sct.grab(region)
            frame = np.array(screenshot)

            # Save the captured region
            filename = f"captured_region_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            cv2.imwrite(filename, cv2.cvtColor(frame, cv2.COLOR_RGB2BGR))
            print(f"\n✓ Region saved to: {filename}")

            # Display the captured region
            print("\nDisplaying captured region...")
            print("Press any key to close the preview")

            cv2.imshow("Captured Multiplier Region", cv2.cvtColor(frame, cv2.COLOR_RGB2BGR))
            cv2.waitKey(0)
            cv2.destroyAllWindows()

            return True
    except Exception as e:
        print(f"Error verifying coordinates: {e}")
        return False


def format_for_script(coords):
    """
    Format coordinates for use in standalone_round_logger.py
    """
    width = coords['right'] - coords['left']
    height = coords['bottom'] - coords['top']

    code = f"""
# Update in standalone_round_logger.py main() function:

logger = AviatorRoundLogger(
    region={{
        "top": {coords['top']},
        "left": {coords['left']},
        "width": {width},
        "height": {height}
    }},
    poll_interval_ms=30
)
"""
    return code


def save_coordinates_to_file(coords):
    """
    Save coordinates to coordinates.txt for reference.
    """
    filename = "coordinates.txt"

    with open(filename, 'w') as f:
        f.write("=" * 70 + "\n")
        f.write("CAPTURED SCREEN COORDINATES\n")
        f.write("=" * 70 + "\n\n")
        f.write(f"Capture Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write("COORDINATES:\n")
        f.write(f"  Top (Y position):    {coords['top']}\n")
        f.write(f"  Left (X position):   {coords['left']}\n")
        f.write(f"  Right (X position):  {coords['right']}\n")
        f.write(f"  Bottom (Y position): {coords['bottom']}\n\n")
        f.write("DIMENSIONS:\n")
        f.write(f"  Width:  {coords['right'] - coords['left']} pixels\n")
        f.write(f"  Height: {coords['bottom'] - coords['top']} pixels\n\n")
        f.write("USE IN CODE:\n")
        f.write(format_for_script(coords))
        f.write("\n" + "=" * 70 + "\n")

    print(f"\n✓ Coordinates saved to: {filename}")


def main():
    """
    Main execution flow.
    """
    print("\n" + "=" * 70)
    print("AVIATOR GAME - SCREEN COORDINATE CAPTURE")
    print("=" * 70)
    print("\nThis tool helps you find the exact screen coordinates")
    print("of your Aviator game multiplier display.")
    print("\nThese coordinates are CRITICAL for the OCR logger to work!")

    print("\n" + "=" * 70)
    print("CHOOSE METHOD")
    print("=" * 70)
    print("\n1. Interactive Selection (Recommended)")
    print("   Click and drag on the game screen to select multiplier area")
    print("   Easy and visual")
    print("\n2. Manual Input")
    print("   Type coordinates manually")
    print("   Use if interactive selection doesn't work")
    print("\n3. Default Coordinates")
    print("   Use default coordinates (may not work for your setup)")
    print("\nEnter your choice (1, 2, or 3): ", end="")

    choice = input().strip()

    coordinates = None

    if choice == "1":
        coordinates = interactive_coordinate_selection()
    elif choice == "2":
        coordinates = manual_coordinate_input()
    elif choice == "3":
        print("\nUsing default coordinates (may not match your screen):")
        coordinates = {
            'top': 506,
            'left': 330,
            'bottom': 506 + 76,
            'right': 330 + 322
        }
        print(f"  Top: 506, Left: 330, Width: 322, Height: 76")
    else:
        print("Invalid choice")
        return

    if coordinates is None:
        print("\nNo coordinates selected. Exiting.")
        return

    # Verify coordinates
    if verify_coordinates(coordinates):
        # Save to file
        save_coordinates_to_file(coordinates)

        # Show code snippet
        print("\n" + "=" * 70)
        print("USE THESE COORDINATES IN YOUR SCRIPT")
        print("=" * 70)
        print(format_for_script(coordinates))

        # Final instructions
        print("\n" + "=" * 70)
        print("NEXT STEPS")
        print("=" * 70)
        print("\n1. Open standalone_round_logger.py")
        print("2. Find the main() function")
        print("3. Update the region parameter with above coordinates")
        print("4. Save the file")
        print("5. Run: python TEST_LOGGER.py")
        print("6. Run: python standalone_round_logger.py")
        print("\n✓ Coordinates captured successfully!")
    else:
        print("\nFailed to verify coordinates")


if __name__ == "__main__":
    main()
