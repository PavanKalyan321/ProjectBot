"""
Standalone Aviator Round Logger
================================

Reads multipliers from Aviator game via OCR and logs them to Supabase database.

Usage:
    python standalone_round_logger.py

Requirements:
    - pytesseract, opencv-python, mss, pillow, psycopg2-binary, python-dotenv
    - Tesseract OCR installed on system
    - .env file with database credentials
    - Aviator game running on screen at region: top=506, left=330, width=322, height=76

Author: Aviator Bot
Date: 2025-11-23
"""

import os
import re
import time
import sys
from decimal import Decimal
from datetime import datetime
from typing import Optional, Tuple
import logging

# Third-party imports
import cv2
import numpy as np
import mss
import pytesseract
import psycopg2
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()


class AviatorRoundLogger:
    """
    Captures Aviator game multipliers via OCR and logs rounds to Supabase.
    """

    def __init__(
        self,
        region: dict = None,
        poll_interval_ms: int = 30,
        tesseract_path: Optional[str] = None
    ):
        """
        Initialize the round logger.

        Args:
            region: Screen region to capture (dict with top, left, width, height)
            poll_interval_ms: Time between captures (ms)
            tesseract_path: Path to tesseract executable
        """
        # Default region from readregion.py
        self.region = region or {
            "top": 506,
            "left": 330,
            "width": 322,
            "height": 76
        }

        self.poll_interval = poll_interval_ms / 1000.0  # Convert to seconds
        self.tesseract_path = tesseract_path or self._find_tesseract()

        # Set tesseract path if found
        if self.tesseract_path:
            pytesseract.pytesseract.pytesseract_cmd = self.tesseract_path
            logger.info(f"Using Tesseract at: {self.tesseract_path}")
        else:
            logger.warning("Tesseract not found. Make sure it's installed on system.")

        # Database connection
        self.db_connection = None
        self.connect_database()

        # Round tracking
        self.round_number = 0
        self.peak_multiplier: Optional[float] = None
        self.in_flight = False
        self.last_valid_multiplier: Optional[float] = None
        self.previous_raw_text = ""

    def _find_tesseract(self) -> Optional[str]:
        """Find tesseract executable path."""
        common_paths = [
            r"C:\Program Files\Tesseract-OCR\tesseract.exe",  # Windows default
            r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
            "/usr/bin/tesseract",  # Linux
            "/usr/local/bin/tesseract",  # macOS
        ]

        for path in common_paths:
            if os.path.exists(path):
                return path

        return None

    def connect_database(self) -> bool:
        """Connect to Supabase database."""
        try:
            db_host = os.getenv("DB_HOST", "zofojiubrykbtmstfhzx.supabase.co")
            db_port = os.getenv("DB_PORT", "5432")
            db_name = os.getenv("DB_NAME", "postgres")
            db_user = os.getenv("DB_USER", "postgres")
            db_password = os.getenv("DB_PASSWORD")

            if not db_password:
                logger.error("DB_PASSWORD not found in .env file")
                return False

            self.db_connection = psycopg2.connect(
                host=db_host,
                port=int(db_port),
                database=db_name,
                user=db_user,
                password=db_password,
                sslmode="require"
            )

            logger.info("✓ Connected to Supabase database")
            return True

        except psycopg2.Error as e:
            logger.error(f"✗ Database connection failed: {e}")
            return False
        except Exception as e:
            logger.error(f"✗ Unexpected error: {e}")
            return False

    def reconnect_database(self) -> bool:
        """Attempt to reconnect to database."""
        if self.db_connection:
            try:
                self.db_connection.close()
            except:
                pass

        logger.info("Attempting to reconnect to database...")
        return self.connect_database()

    def capture_region(self) -> Optional[np.ndarray]:
        """Capture the specified screen region."""
        try:
            with mss.mss() as sct:
                screenshot = sct.grab(self.region)
                # Convert to numpy array and drop alpha channel
                frame = np.array(screenshot)[..., :3]
                return frame
        except Exception as e:
            logger.error(f"Failed to capture screen: {e}")
            return None

    def preprocess_for_ocr(self, img: np.ndarray) -> np.ndarray:
        """
        Preprocess image for OCR.
        Converts to grayscale and applies threshold.
        """
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)
        return thresh

    def extract_text_ocr(self, img: np.ndarray) -> str:
        """
        Extract text from image using Tesseract OCR.

        Args:
            img: Preprocessed image

        Returns:
            Extracted text
        """
        try:
            config = r'--psm 7 --oem 3 -c tessedit_char_whitelist=0123456789.xABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'
            text = pytesseract.image_to_string(img, config=config).strip()
            return text
        except Exception as e:
            logger.error(f"OCR extraction failed: {e}")
            return ""

    def parse_multiplier(self, text: str) -> Optional[float]:
        """
        Parse multiplier value from OCR text.

        Args:
            text: OCR extracted text

        Returns:
            Multiplier value or None if invalid
        """
        # Look for pattern like "1.23" or "15.45"
        match = re.search(r'(\d{1,3}\.\d+)', text)
        if match:
            try:
                value = float(match.group(1))
                return value if 1.0 <= value <= 1000.0 else None
            except ValueError:
                return None
        return None

    def validate_multiplier(
        self,
        multiplier: float,
        last_valid: Optional[float] = None,
        in_flight: bool = False
    ) -> bool:
        """
        Validate multiplier based on game logic.

        Args:
            multiplier: The multiplier to validate
            last_valid: Last valid multiplier seen
            in_flight: Whether a flight is in progress

        Returns:
            True if valid, False otherwise
        """
        # Basic range check
        if multiplier < 1.0 or multiplier > 1000.0:
            return False

        # If in flight, multiplier must increase (with 1% tolerance)
        if in_flight and last_valid is not None:
            if multiplier < last_valid * 0.99:
                return False
            # Prevent jumps > 2x (catches OCR errors)
            if multiplier > last_valid * 2.0:
                return False

        return True

    def check_round_complete(self, text: str) -> bool:
        """
        Check if round is complete.
        Detects "AWAITING NEXT FLIGHT" or similar status text.

        Args:
            text: OCR extracted text

        Returns:
            True if round is complete
        """
        text_upper = text.upper()
        return "AWAITING" in text_upper and "FLIGHT" in text_upper

    def log_round_to_db(self, multiplier: float) -> bool:
        """
        Log a completed round to the database.

        Args:
            multiplier: The peak multiplier for the round

        Returns:
            True if successful
        """
        if not self.db_connection:
            logger.error("No database connection")
            return False

        try:
            cursor = self.db_connection.cursor()
            cursor.execute(
                'INSERT INTO "AviatorRound" ("multiplier", "timestamp") VALUES (%s, %s)',
                (float(multiplier), datetime.utcnow())
            )
            self.db_connection.commit()
            cursor.close()

            self.round_number += 1
            logger.info(
                f"✓ Round {self.round_number} logged: {multiplier:.2f}x"
            )
            return True

        except psycopg2.Error as e:
            logger.error(f"Database insert failed: {e}")
            # Try to reconnect
            if self.reconnect_database():
                return self.log_round_to_db(multiplier)
            return False
        except Exception as e:
            logger.error(f"Unexpected error logging round: {e}")
            return False

    def read_current_multiplier(self) -> None:
        """
        Main loop: Read current multiplier from screen and manage round state.
        """
        # Capture screen region
        frame = self.capture_region()
        if frame is None:
            return

        # Preprocess for OCR
        processed = self.preprocess_for_ocr(frame)

        # Extract text
        text = self.extract_text_ocr(processed)

        # Check for round completion
        if self.check_round_complete(text):
            if self.peak_multiplier and self.peak_multiplier >= 1.0:
                self.log_round_to_db(self.peak_multiplier)

            # Reset state
            self.peak_multiplier = None
            self.in_flight = False
            self.last_valid_multiplier = None
            return

        # Try to parse multiplier from text
        multiplier = self.parse_multiplier(text)

        if multiplier is not None:
            # Validate the multiplier
            if self.validate_multiplier(
                multiplier,
                self.last_valid_multiplier,
                self.in_flight
            ):
                self.in_flight = True
                self.last_valid_multiplier = multiplier

                # Track peak multiplier
                if self.peak_multiplier is None or multiplier > self.peak_multiplier:
                    self.peak_multiplier = multiplier

                # Console output (with carriage return to update in place)
                print(
                    f"Current: {multiplier:.2f}x (peak: {self.peak_multiplier:.2f}x) | "
                    f"Rounds logged: {self.round_number}",
                    end='\r'
                )

    def run(self) -> None:
        """
        Main loop for continuous monitoring.
        """
        logger.info("=" * 60)
        logger.info("Aviator Round Logger Started")
        logger.info("=" * 60)
        logger.info(f"Screen region: top={self.region['top']}, "
                    f"left={self.region['left']}, "
                    f"width={self.region['width']}, "
                    f"height={self.region['height']}")
        logger.info(f"Poll interval: {self.poll_interval * 1000:.0f}ms")
        logger.info("=" * 60)

        if not self.db_connection:
            logger.error("Cannot start without database connection")
            return

        logger.info("Monitoring game... Press Ctrl+C to stop\n")

        try:
            while True:
                self.read_current_multiplier()
                time.sleep(self.poll_interval)

        except KeyboardInterrupt:
            logger.info("\n\nShutdown requested by user")
            self.shutdown()
        except Exception as e:
            logger.error(f"\nUnexpected error: {e}")
            self.shutdown()

    def shutdown(self) -> None:
        """Clean shutdown."""
        if self.db_connection:
            try:
                self.db_connection.close()
                logger.info("✓ Database connection closed")
            except:
                pass

        logger.info(f"✓ Logger stopped. Total rounds logged: {self.round_number}")
        logger.info("=" * 60)


def main():
    """Entry point."""
    # Optional: Configure custom region or tesseract path
    logger = AviatorRoundLogger(
        region={
            "top": 506,
            "left": 330,
            "width": 322,
            "height": 76
        },
        poll_interval_ms=30  # 33 FPS
    )

    logger.run()


if __name__ == "__main__":
    main()
