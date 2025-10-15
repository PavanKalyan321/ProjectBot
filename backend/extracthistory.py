"""
capture_and_parse_history.py

Requirements:
    pip install pillow pytesseract opencv-python

Notes:
- On Windows, if Tesseract is not on PATH, set:
    pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
"""

from PIL import ImageGrab, Image
import pytesseract
import cv2
import numpy as np
import re
import os
import time
pytesseract.pytesseract.tesseract_cmd = "C:/Program Files/Tesseract-OCR/tesseract.exe"

# ---------------- CONFIG ----------------
# bbox chosen from your coordinates: top-left (5,1069), bottom-right (886,1132)
DEFAULT_BBOX = (5, 1069, 886, 1132)
DEFAULT_SAVE_PATH = "history_capture.png"
# OCR config - single-line tries (psm 7). We'll fall back if necessary.
DEFAULT_TESSERACT_CONFIG = "--psm 7"

# If needed (Windows), uncomment and set your tesseract exe path:
# pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# ---------------- UTIL: preprocess image for OCR ----------------
def _preprocess_image_for_ocr(pil_img: Image.Image) -> Image.Image:
    """
    Convert to grayscale, apply adaptive threshold and mild dilation/erosion
    to make numeric text more legible for Tesseract.
    """
    arr = np.array(pil_img.convert("L"))  # grayscale
    # adaptive threshold to binarize
    arr = cv2.adaptiveThreshold(arr, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                cv2.THRESH_BINARY, 11, 2)
    # morphological open to remove small noise
    kernel = np.ones((2, 2), np.uint8)
    arr = cv2.morphologyEx(arr, cv2.MORPH_OPEN, kernel)
    return Image.fromarray(arr)

# ---------------- Capture-only ----------------
def capture_region(bbox=DEFAULT_BBOX, save_path=None, show_timestamp=False):
    """
    Capture the screen region and return a PIL.Image.
    If save_path is provided, the image will be saved to disk.
    If show_timestamp True, timestamp appended to filename.
    """
    x1, y1, x2, y2 = bbox
    img = ImageGrab.grab(bbox=(x1, y1, x2, y2))
    if save_path:
        base, ext = os.path.splitext(save_path)
        if show_timestamp:
            save_path = f"{base}_{int(time.time())}{ext}"
        img.save(save_path)
        return save_path, img
    return None, img

# ---------------- Main: get multiplier array from captured image ----------------
def get_multiplier_array_from_image(img_or_path, *, do_preprocess=True, tess_config=DEFAULT_TESSERACT_CONFIG, newest_first=True, debug=False):
    """
    Convert an image (PIL.Image or file path) containing the history bar into a list of floats.

    Args:
        img_or_path: PIL.Image object or path to image file.
        do_preprocess: whether to run preprocessing to improve OCR.
        tess_config: tesseract config string, default "--psm 7".
        newest_first: if True, return newest->oldest (rightmost first). If False, leftmost first.
        debug: print OCR raw text and intermediate info.

    Returns:
        List[float] of detected multipliers (may be empty if nothing found).
    """
    # load image if path
    if isinstance(img_or_path, str):
        img = Image.open(img_or_path)
    else:
        img = img_or_path

    proc_img = _preprocess_image_for_ocr(img) if do_preprocess else img

    # Try primary OCR mode
    raw_text = pytesseract.image_to_string(proc_img, config=tess_config).strip()
    if debug:
        print("OCR (psm primary) raw_text:", repr(raw_text))

    # Fallback: if empty or clearly bad, try another psm
    if len(raw_text) < 2:
        raw_text = pytesseract.image_to_string(proc_img, config="--psm 6").strip()
        if debug:
            print("OCR (psm 6 fallback) raw_text:", repr(raw_text))

    # Extract numeric tokens: integers or decimals; accept optional trailing 'x' or 'X'
    # Examples matched: "3.78", "2.0x", "19.53x", "2"
    token_pattern = re.compile(r"\d+(?:\.\d+)?(?:[xX])?")
    tokens = token_pattern.findall(raw_text)

    # Clean tokens: remove trailing 'x'/'X', ignore short artifacts like single '-' or lone digits if unlikely
    cleaned = []
    for t in tokens:
        t2 = t.rstrip('xX')
        # skip tokens that are obviously not multipliers (e.g. single digit '1' might be valid though)
        # we keep both ints and floats; convert to float safely
        try:
            val = float(t2)
            cleaned.append(val)
        except:
            continue

    # If OCR merged numbers without clear spacing, try a different approach:
    if not cleaned:
        # try extracting using a more permissive regex that finds decimal-like substrings
        alt = re.findall(r"\d+\.\d+", raw_text)
        cleaned = [float(x) for x in alt]

    # At this point cleaned contains values in the textual order returned by tesseract (likely left->right)
    if debug:
        print("Tokens found by OCR:", tokens)
        print("Cleaned numeric list (left->right order assumed):", cleaned)

    # The UI commonly shows oldest->...->newest left->right. If newest_first requested, reverse.
    if newest_first:
        cleaned = cleaned[::-1]

    return cleaned

# ---------------- Convenience: capture region and return array directly ----------------
def get_multiplier_array_from_screen(bbox=DEFAULT_BBOX, save_capture_path=None, *, do_preprocess=True, newest_first=True, debug=False):
    """
    Capture the configured bbox and return the multiplier array (floats).
    If save_capture_path provided, the capture is saved for inspection.
    """
    saved_path, img = capture_region(bbox=bbox, save_path=save_capture_path, show_timestamp=False)
    if debug and saved_path:
        print("Saved capture to:", saved_path)
    arr = get_multiplier_array_from_image(img, do_preprocess=do_preprocess, newest_first=newest_first, debug=debug)
    if debug:
        print("Final multiplier array (newest_first={}): {}".format(newest_first, arr))
    return arr

# ---------------- Example usage ----------------
if __name__ == "__main__":
    # Quick demo: capture and parse, saving the capture for inspection
    arr = get_multiplier_array_from_screen(save_capture_path=DEFAULT_SAVE_PATH, do_preprocess=True, newest_first=True, debug=True)
    print("Returned multiplier array:", arr)
