"""OCR utility functions for image preprocessing."""

import cv2
import numpy as np
from PIL import Image


def preprocess_image_for_ocr(pil_img):
    """
    Preprocess image for better OCR results.
    
    Converts to grayscale, applies adaptive threshold and morphological operations
    to make text more legible for Tesseract.
    
    Args:
        pil_img: PIL.Image object
    
    Returns:
        PIL.Image: Preprocessed image
    """
    try:
        # Convert to grayscale
        arr = np.array(pil_img.convert("L"))
        
        # Apply adaptive threshold to binarize
        arr = cv2.adaptiveThreshold(
            arr, 255, 
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY, 
            11, 2
        )
        
        # Morphological open to remove small noise
        kernel = np.ones((2, 2), np.uint8)
        arr = cv2.morphologyEx(arr, cv2.MORPH_OPEN, kernel)
        
        return Image.fromarray(arr)
    except Exception as e:
        print(f"Error preprocessing image: {e}")
        return pil_img


def enhance_image_for_text(image_array):
    """
    Enhance image for text detection.
    
    Args:
        image_array: numpy array of image
    
    Returns:
        numpy array: Enhanced image
    """
    try:
        # Convert to grayscale if needed
        if len(image_array.shape) == 3:
            gray = cv2.cvtColor(image_array, cv2.COLOR_RGB2GRAY)
        else:
            gray = image_array
        
        # Apply threshold
        _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)
        
        return thresh
    except Exception as e:
        print(f"Error enhancing image: {e}")
        return image_array
