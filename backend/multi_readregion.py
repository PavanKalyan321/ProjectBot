import mss
import numpy as np
import cv2
import pytesseract
import re
import time
import os
import csv
import threading
import json
from datetime import datetime
from collections import defaultdict
from queue import Queue
from typing import Dict, List, Tuple, Optional
import sys

from utils.betting_helpers import (
    set_stake_verified,
    place_bet_with_verification,
    cashout_verified,
    estimate_multiplier,
    increase_stake,
    reset_stake
)
from utils.data_logger import get_round_logger


class DataPoint:
    """Represents a single data point to be extracted from screen"""
    def __init__(self, name: str, region: Dict, pattern: str, data_type: str = 'float'):
        """
        Initialize a data point.

        Args:
            name: Display name (e.g., 'Balance', 'Multiplier')
            region: {'top', 'left', 'width', 'height'} coordinates
            pattern: Regex pattern to extract value
            data_type: 'float', 'int', 'string'
        """
        self.name = name
        self.region = region
        self.pattern = pattern
        self.data_type = data_type
        self.last_value = None
        self.last_raw = None
        self.confidence = 0.0
        self.errors = []

    def extract(self, frame) -> Tuple[Optional, float, str]:
        """
        Extract value from frame.

        Returns:
            tuple: (value, confidence: 0-1, raw_ocr_text)
        """
        if frame is None or len(frame.shape) < 2:
            return None, 0.0, ""

        try:
            # Preprocess
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)

            # OCR
            config = r'--psm 7 --oem 3'
            raw = pytesseract.image_to_string(thresh, config=config).strip().replace('\n', '').replace(' ', '')

            # Match pattern
            match = re.search(self.pattern, raw)
            if not match:
                return None, 0.0, raw

            value_str = match.group(1) if match.groups() else match.group(0)

            # Convert to appropriate type
            if self.data_type == 'float':
                value = float(value_str)
                confidence = 0.95
            elif self.data_type == 'int':
                value = int(value_str)
                confidence = 0.95
            else:
                value = value_str
                confidence = 0.9

            self.last_value = value
            self.last_raw = raw
            self.confidence = confidence

            return value, confidence, raw

        except Exception as e:
            self.errors.append(str(e))
            return None, 0.0, ""


class BrowserDataCollector:
    """
    Collects all game data points from a single browser instance.
    Tracks: balance, multiplier, place bet status, stake, number of players.
    """

    def __init__(self, browser_id: int):
        """
        Initialize collector for a browser.

        Args:
            browser_id: Browser ID (0-5)
        """
        self.browser_id = browser_id
        self.data_points = {}
        self.collected_data = defaultdict(list)
        self.validation_status = {}

    def register_data_point(self, name: str, region: Dict, pattern: str, data_type: str = 'float'):
        """
        Register a data point to be collected from this browser.

        Args:
            name: Display name ('balance', 'multiplier', 'place_bet', 'stake', 'players')
            region: Screen region coordinates
            pattern: Regex pattern for extraction
            data_type: 'float', 'int', 'string'
        """
        self.data_points[name] = DataPoint(name, region, pattern, data_type)
        self.validation_status[name] = False

    def capture_region(self, region: Dict) -> Optional[np.ndarray]:
        """Capture a screen region"""
        try:
            with mss.mss() as sct:
                img = np.array(sct.grab(region))
                return img[..., :3]
        except Exception as e:
            print(f"❌ Capture error for browser {self.browser_id}: {e}")
            return None

    def collect_all_data_points(self) -> Dict[str, Tuple]:
        """
        Collect all registered data points.

        Returns:
            dict: {point_name: (value, confidence, raw_text)}
        """
        results = {}
        for name, datapoint in self.data_points.items():
            frame = self.capture_region(datapoint.region)
            value, confidence, raw = datapoint.extract(frame)
            results[name] = (value, confidence, raw)
            self.collected_data[name].append({
                'timestamp': datetime.now().isoformat(),
                'value': value,
                'confidence': confidence,
                'raw': raw
            })
        return results

    def get_current_state(self) -> Dict:
        """Get current state of all data points"""
        return {
            name: {
                'value': dp.last_value,
                'confidence': dp.confidence,
                'raw': dp.last_raw,
                'validated': self.validation_status.get(name, False)
            }
            for name, dp in self.data_points.items()
        }

    def validate_data_point(self, name: str, is_valid: bool):
        """Mark a data point as validated by user"""
        self.validation_status[name] = is_valid
        if is_valid:
            print(f"✅ {name.upper()} validated for Browser {self.browser_id}")
        else:
            print(f"❌ {name.upper()} validation failed for Browser {self.browser_id}")

    def get_validation_report(self) -> Dict:
        """Get validation report for all data points"""
        return {
            name: {
                'validated': self.validation_status.get(name, False),
                'last_value': self.data_points[name].last_value if name in self.data_points else None,
                'confidence': self.data_points[name].confidence if name in self.data_points else 0.0,
                'samples': len(self.collected_data.get(name, []))
            }
            for name in self.data_points.keys()
        }


class MultiScreenMultiplierReader:
    """
    Multi-browser multiplier reader for parallel Aviator game tracking.
    Reads from up to 6 browser instances simultaneously with OCR validation.
    """

    def __init__(self, browser_regions: Dict[int, Dict], enable_logging=True):
        """
        Initialize multi-screen reader.

        Args:
            browser_regions: Dict mapping browser_id (0-5) to region dict
                            Each region: {'top': int, 'left': int, 'width': int, 'height': int}
            enable_logging: Whether to log rounds to CSV
        """
        self.browser_regions = browser_regions
        self.num_browsers = len(browser_regions)
        self.enable_logging = enable_logging

        # State tracking per browser
        self.states = {}
        self.ocr_validation_logs = {}
        self.data_queues = {}  # Queue for thread-safe data collection

        # Initialize per-browser state
        for browser_id in browser_regions.keys():
            self.states[browser_id] = {
                'last_valid_multiplier': None,
                'flight_in_progress': False,
                'round_start_multiplier': None,
                'round_peak_multiplier': None,
                'last_ocr_raw': '',
                'last_capture_time': None,
                'ocr_confidence': 0.0,
                'validation_errors': [],
                'consecutive_valid_reads': 0,
                'status': 'AWAITING'
            }
            self.ocr_validation_logs[browser_id] = []
            self.data_queues[browser_id] = Queue()

        # Centralized logger
        self.round_logger = get_round_logger() if enable_logging else None

        # OCR validation statistics
        self.ocr_stats = {
            'total_reads': 0,
            'valid_multipliers': 0,
            'invalid_reads': 0,
            'awaiting_status': 0,
            'ocr_errors': 0,
            'validation_errors': defaultdict(int)
        }

    def preprocess_for_ocr(self, img):
        """Convert image to grayscale and apply thresholding for better OCR"""
        if img is None or len(img.shape) < 2:
            return None

        try:
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            # More aggressive thresholding for better OCR
            _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)
            return thresh
        except Exception as e:
            print(f"❌ Preprocessing error: {e}")
            return None

    def capture_region(self, browser_id: int) -> Optional[np.ndarray]:
        """
        Capture screen region for a specific browser.

        Args:
            browser_id: Browser ID (0-5)

        Returns:
            numpy array or None if capture fails
        """
        try:
            region = self.browser_regions[browser_id]
            with mss.mss() as sct:
                img = np.array(sct.grab(region))
                return img[..., :3]  # Drop alpha channel
        except Exception as e:
            self.states[browser_id]['validation_errors'].append(f"Capture error: {e}")
            return None

    def extract_multiplier_with_validation(self, frame, browser_id: int) -> Tuple[str, float]:
        """
        Extract multiplier value with OCR confidence scoring.

        Args:
            frame: Captured frame
            browser_id: Browser ID for logging

        Returns:
            tuple: (raw_value: str, confidence: float)
        """
        if frame is None:
            return "", 0.0

        try:
            gray = self.preprocess_for_ocr(frame)
            if gray is None:
                return "", 0.0

            # Optimized OCR config
            config = r'--psm 7 --oem 3 -c tessedit_char_whitelist=0123456789.xABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'
            raw = pytesseract.image_to_string(gray, config=config).strip().replace('\n', '').replace(' ', '')

            # Calculate confidence based on pattern matching
            confidence = self._calculate_ocr_confidence(raw)

            # Log OCR extraction
            self.ocr_validation_logs[browser_id].append({
                'timestamp': datetime.now().isoformat(),
                'raw_value': raw,
                'confidence': confidence,
                'preprocessed': True
            })

            self.ocr_stats['total_reads'] += 1

            return raw, confidence

        except Exception as e:
            self.states[browser_id]['validation_errors'].append(f"OCR error: {e}")
            self.ocr_stats['ocr_errors'] += 1
            return "", 0.0

    def _calculate_ocr_confidence(self, raw_value: str) -> float:
        """
        Calculate confidence score for OCR result (0.0 to 1.0).

        Args:
            raw_value: Raw OCR output

        Returns:
            float: Confidence score
        """
        if not raw_value:
            return 0.0

        # Check for AWAITING status
        if "AWAITING" in raw_value.upper() and "FLIGHT" in raw_value.upper():
            return 0.95  # High confidence for awaiting status

        # Check for number pattern
        if re.search(r'\d{1,3}\.\d{1,2}', raw_value):
            return 0.9  # High confidence for proper format
        elif re.search(r'\d+(\.\d+)?', raw_value):
            return 0.7  # Medium confidence for number with variations
        else:
            return 0.3  # Low confidence for non-numeric

    def validate_multiplier(self, raw_value: str, browser_id: int, last_valid: Optional[float] = None, in_flight: bool = False) -> Tuple[Optional[float], str]:
        """
        Validate and clean multiplier value with strict rules.

        Args:
            raw_value: Raw OCR value
            browser_id: Browser ID
            last_valid: Last valid multiplier
            in_flight: Whether flight is in progress

        Returns:
            tuple: (validated_multiplier: float or None, validation_reason: str)
        """
        if not raw_value or raw_value == "AWAITING NEXT FLIGHT":
            return None, "AWAITING_NEXT_FLIGHT"

        # Remove 'x' or 'X' suffix
        cleaned = re.sub(r'[xX]$', '', raw_value)

        # Try to extract a valid number
        match = re.search(r'(\d{1,3}\.\d+)', cleaned)
        if not match:
            self.ocr_stats['validation_errors']['no_number_pattern'] += 1
            return None, "NO_NUMBER_PATTERN"

        try:
            mult = float(match.group(1))

            # Validation Rule 1: Must be >= 1.00
            if mult < 1.0:
                self.ocr_stats['validation_errors']['below_minimum'] += 1
                return None, "BELOW_MINIMUM_1.00"

            # Validation Rule 2: Reasonable upper limit
            if mult > 1000.0:
                self.ocr_stats['validation_errors']['exceeds_maximum'] += 1
                return None, "EXCEEDS_MAXIMUM_1000"

            # Validation Rule 3: During flight, must ALWAYS increase
            if in_flight and last_valid:
                # Must be strictly greater (with small tolerance for rounding)
                if mult <= last_valid * 0.99:  # Allow 1% tolerance
                    self.ocr_stats['validation_errors']['decreasing_value'] += 1
                    return None, "DECREASING_VALUE"

                # Also reject values that jump too much (likely OCR error)
                if mult > last_valid * 2.0:  # More than 2x jump
                    self.ocr_stats['validation_errors']['excessive_jump'] += 1
                    return None, "EXCESSIVE_JUMP"

            # Validation Rule 4: New flight detection
            if last_valid and last_valid > 1.5 and mult < 1.5:
                return mult, "NEW_FLIGHT_DETECTED"

            self.ocr_stats['valid_multipliers'] += 1
            return mult, "VALID"

        except (ValueError, AttributeError) as e:
            self.ocr_stats['validation_errors']['parse_error'] += 1
            return None, f"PARSE_ERROR: {str(e)}"

    def read_browser_multiplier(self, browser_id: int) -> Optional[float]:
        """
        Read current multiplier for a specific browser with full validation pipeline.

        Args:
            browser_id: Browser ID (0-5)

        Returns:
            float: Current multiplier, or None if not readable
        """
        # Capture frame
        frame = self.capture_region(browser_id)
        if frame is None:
            self.ocr_stats['invalid_reads'] += 1
            return None

        state = self.states[browser_id]

        # Extract with OCR
        raw_value, confidence = self.extract_multiplier_with_validation(frame, browser_id)
        state['last_ocr_raw'] = raw_value
        state['ocr_confidence'] = confidence
        state['last_capture_time'] = datetime.now()

        # Check for awaiting status
        if "AWAITING" in raw_value.upper() and "FLIGHT" in raw_value.upper():
            self.ocr_stats['awaiting_status'] += 1

            # Log round if exists
            if self.enable_logging and self.round_logger and state['round_peak_multiplier'] and state['round_peak_multiplier'] >= 1.0:
                self.round_logger.log_round(state['round_peak_multiplier'], source=f'browser_{browser_id}')

            # Reset state
            state['flight_in_progress'] = False
            state['last_valid_multiplier'] = None
            state['round_start_multiplier'] = None
            state['round_peak_multiplier'] = None
            state['consecutive_valid_reads'] = 0
            state['status'] = 'AWAITING'
            return None

        # Validate multiplier
        validated, reason = self.validate_multiplier(
            raw_value,
            browser_id,
            state['last_valid_multiplier'],
            state['flight_in_progress']
        )

        state['status'] = reason

        if validated:
            # Check if this is a new flight
            if state['last_valid_multiplier'] and state['last_valid_multiplier'] > 1.5 and validated < 1.5:
                # Log previous round
                if self.enable_logging and self.round_logger and state['round_peak_multiplier'] and state['round_peak_multiplier'] >= 1.0:
                    self.round_logger.log_round(state['round_peak_multiplier'], source=f'browser_{browser_id}')

                state['flight_in_progress'] = False
                state['round_start_multiplier'] = None
                state['round_peak_multiplier'] = None
                state['consecutive_valid_reads'] = 0

            # Track round stats
            if not state['flight_in_progress']:
                state['round_start_multiplier'] = validated

            # Update peak multiplier
            if state['round_peak_multiplier'] is None or validated > state['round_peak_multiplier']:
                state['round_peak_multiplier'] = validated

            state['last_valid_multiplier'] = validated
            state['flight_in_progress'] = True
            state['consecutive_valid_reads'] += 1
            state['status'] = f'FLYING: {validated:.2f}x'

            return validated
        else:
            state['consecutive_valid_reads'] = 0
            return None

    def read_all_browsers(self) -> Dict[int, Optional[float]]:
        """
        Read multipliers from all browsers simultaneously.

        Returns:
            dict: {browser_id: multiplier_value or None}
        """
        results = {}
        threads = []

        def read_browser(bid):
            result = self.read_browser_multiplier(bid)
            results[bid] = result

        # Start threads for all browsers
        for browser_id in self.browser_regions.keys():
            thread = threading.Thread(target=read_browser, args=(browser_id,))
            thread.daemon = True
            thread.start()
            threads.append(thread)

        # Wait for all threads to complete
        for thread in threads:
            thread.join(timeout=5)

        return results

    def get_browser_status(self, browser_id: int) -> Dict:
        """
        Get current status of a specific browser.

        Returns:
            dict: Status information
        """
        state = self.states[browser_id]
        return {
            'browser_id': browser_id,
            'status': state['status'],
            'current_multiplier': state['last_valid_multiplier'],
            'flight_in_progress': state['flight_in_progress'],
            'round_peak': state['round_peak_multiplier'],
            'ocr_confidence': state['ocr_confidence'],
            'last_ocr_raw': state['last_ocr_raw'],
            'consecutive_valid_reads': state['consecutive_valid_reads'],
            'last_capture_time': state['last_capture_time'].isoformat() if state['last_capture_time'] else None,
            'validation_errors': state['validation_errors'][-5:]  # Last 5 errors
        }

    def get_all_statuses(self) -> Dict:
        """
        Get status of all browsers.

        Returns:
            dict: Status for each browser
        """
        return {
            bid: self.get_browser_status(bid)
            for bid in self.browser_regions.keys()
        }

    def get_ocr_validation_report(self) -> Dict:
        """
        Get detailed OCR validation report.

        Returns:
            dict: Statistics and validation info
        """
        return {
            'total_reads': self.ocr_stats['total_reads'],
            'valid_multipliers': self.ocr_stats['valid_multipliers'],
            'invalid_reads': self.ocr_stats['invalid_reads'],
            'awaiting_status': self.ocr_stats['awaiting_status'],
            'ocr_errors': self.ocr_stats['ocr_errors'],
            'validation_errors_breakdown': dict(self.ocr_stats['validation_errors']),
            'success_rate': f"{(self.ocr_stats['valid_multipliers'] / max(1, self.ocr_stats['total_reads']) * 100):.2f}%",
            'browsers_summary': {
                bid: {
                    'ocr_logs_count': len(self.ocr_validation_logs[bid]),
                    'last_5_logs': self.ocr_validation_logs[bid][-5:]
                }
                for bid in self.browser_regions.keys()
            }
        }

    def export_ocr_logs(self, filepath: str = "ocr_validation_logs.json"):
        """
        Export detailed OCR validation logs to JSON.

        Args:
            filepath: Output file path
        """
        try:
            export_data = {
                'timestamp': datetime.now().isoformat(),
                'statistics': self.ocr_stats.copy(),
                'browser_states': {
                    bid: {
                        k: v for k, v in self.states[bid].items()
                        if k != 'validation_errors'
                    }
                    for bid in self.browser_regions.keys()
                },
                'ocr_logs': {
                    bid: self.ocr_validation_logs[bid]
                    for bid in self.browser_regions.keys()
                }
            }

            with open(filepath, 'w') as f:
                json.dump(export_data, f, indent=2, default=str)

            print(f"✅ OCR logs exported to {filepath}")

        except Exception as e:
            print(f"❌ Error exporting logs: {e}")

    def reset_all(self):
        """Reset all browser states"""
        for browser_id in self.browser_regions.keys():
            self.states[browser_id] = {
                'last_valid_multiplier': None,
                'flight_in_progress': False,
                'round_start_multiplier': None,
                'round_peak_multiplier': None,
                'last_ocr_raw': '',
                'last_capture_time': None,
                'ocr_confidence': 0.0,
                'validation_errors': [],
                'consecutive_valid_reads': 0,
                'status': 'AWAITING'
            }


# Example usage and testing
def main_multi_browser_test():
    """Test multi-browser multiplier reader"""

    # Define regions for 6 browsers (adjust coordinates as needed)
    browser_regions = {
        0: {"top": 506, "left": 330, "width": 322, "height": 76},      # Browser 1
        1: {"top": 506, "left": 680, "width": 322, "height": 76},      # Browser 2
        2: {"top": 506, "left": 1030, "width": 322, "height": 76},     # Browser 3
        3: {"top": 800, "left": 330, "width": 322, "height": 76},      # Browser 4
        4: {"top": 800, "left": 680, "width": 322, "height": 76},      # Browser 5
        5: {"top": 800, "left": 1030, "width": 322, "height": 76},     # Browser 6
    }

    # Initialize multi-browser reader
    reader = MultiScreenMultiplierReader(browser_regions, enable_logging=True)

    print("🚀 Starting Multi-Browser Multiplier Reader")
    print(f"📺 Tracking {len(browser_regions)} browsers")
    print("Press Ctrl+C to stop.\n")

    try:
        iteration = 0
        while True:
            iteration += 1

            # Read all browsers
            results = reader.read_all_browsers()

            # Print status every 10 iterations
            if iteration % 10 == 0:
                print("\n" + "="*80)
                print(f"Iteration {iteration} - {datetime.now().strftime('%H:%M:%S')}")
                print("="*80)

                all_statuses = reader.get_all_statuses()
                for bid, status in all_statuses.items():
                    print(f"\n🔍 Browser {bid}:")
                    print(f"   Status: {status['status']}")
                    print(f"   Current: {status['current_multiplier']}")
                    print(f"   Peak: {status['round_peak']}")
                    print(f"   OCR Confidence: {status['ocr_confidence']:.2%}")
                    print(f"   Valid Reads: {status['consecutive_valid_reads']}")

                # Print OCR validation report
                print("\n" + "-"*80)
                print("📊 OCR Validation Report:")
                print("-"*80)
                report = reader.get_ocr_validation_report()
                print(f"Total Reads: {report['total_reads']}")
                print(f"Valid Multipliers: {report['valid_multipliers']}")
                print(f"Success Rate: {report['success_rate']}")
                print(f"Validation Errors: {report['validation_errors_breakdown']}")

            time.sleep(0.03)  # 30ms between reads

    except KeyboardInterrupt:
        print("\n\n🛑 Stopped.")

        # Export logs
        print("\n📁 Exporting OCR validation logs...")
        reader.export_ocr_logs("ocr_validation_logs.json")

        # Print final summary
        print("\n" + "="*80)
        print("📈 FINAL SUMMARY")
        print("="*80)
        report = reader.get_ocr_validation_report()
        print(json.dumps(report, indent=2, default=str))


def setup_single_browser_validation():
    """
    Interactive setup for a single browser with coordinate validation.
    Goes through each data point one by one.
    """
    print("\n" + "="*80)
    print("🔧 BROWSER SETUP - ONE BY ONE VALIDATION")
    print("="*80)

    # Get browser ID
    while True:
        try:
            browser_id = int(input("\nEnter Browser ID (0-5): ").strip())
            if 0 <= browser_id <= 5:
                break
            print("❌ Please enter a number between 0 and 5")
        except ValueError:
            print("❌ Invalid input. Please enter a number.")

    # Create collector
    collector = BrowserDataCollector(browser_id)

    # Define all data points to collect
    data_points_config = [
        {
            'name': 'balance',
            'description': 'Player balance/account balance',
            'example_pattern': r'(\d+\.?\d*)',
            'data_type': 'float'
        },
        {
            'name': 'multiplier',
            'description': 'Current multiplier value',
            'example_pattern': r'(\d+\.\d+)',
            'data_type': 'float'
        },
        {
            'name': 'place_bet',
            'description': 'Place bet button/status',
            'example_pattern': r'(PLACE|BET|ACTIVE|INACTIVE)',
            'data_type': 'string'
        },
        {
            'name': 'stake',
            'description': 'Bet stake amount',
            'example_pattern': r'(\d+\.?\d*)',
            'data_type': 'float'
        },
        {
            'name': 'players',
            'description': 'Number of players',
            'example_pattern': r'(\d+)',
            'data_type': 'int'
        }
    ]

    # Setup each data point
    for idx, config in enumerate(data_points_config, 1):
        print(f"\n{'-'*80}")
        print(f"📍 DATA POINT {idx}/5: {config['name'].upper()}")
        print(f"Description: {config['description']}")
        print(f"Data type: {config['data_type']}")
        print(f"Example pattern: {config['example_pattern']}")
        print(f"{'-'*80}")

        # Get coordinates
        print(f"\nEnter coordinates for {config['name']}:")
        try:
            top = int(input("  Top (pixels from top): ").strip())
            left = int(input("  Left (pixels from left): ").strip())
            width = int(input("  Width (pixels): ").strip())
            height = int(input("  Height (pixels): ").strip())

            region = {'top': top, 'left': left, 'width': width, 'height': height}

            # Get pattern
            pattern = input(f"  Enter regex pattern [{config['example_pattern']}]: ").strip()
            if not pattern:
                pattern = config['example_pattern']

            # Register data point
            collector.register_data_point(
                config['name'],
                region,
                pattern,
                config['data_type']
            )

            print(f"✅ Registered {config['name']} data point")

        except ValueError as e:
            print(f"❌ Invalid input: {e}")
            continue

    # Validation loop
    print(f"\n" + "="*80)
    print("🧪 VALIDATION PHASE - Testing each data point")
    print("="*80)

    all_validated = False
    iteration = 0

    while not all_validated:
        iteration += 1
        print(f"\n[Iteration {iteration}]")

        # Collect data
        results = collector.collect_all_data_points()

        # Display results
        print("\n📊 CURRENT VALUES:")
        print("-" * 80)
        for name, (value, confidence, raw) in results.items():
            status = "✅" if collector.validation_status[name] else "⏳"
            confidence_pct = f"{confidence*100:.1f}%" if value is not None else "N/A"
            print(f"{status} {name:15} | Value: {str(value):15} | Confidence: {confidence_pct:8} | Raw: {raw[:50]}")

        print("-" * 80)

        # Get user input
        print("\nOptions:")
        print("  V<point> - Validate a data point (e.g., 'Vbalance', 'Vmultiplier')")
        print("  R<point> - Re-enter coordinates for a data point")
        print("  S       - Show summary")
        print("  Q       - Quit and save")

        user_input = input("\nEnter command: ").strip().upper()

        if user_input == 'S':
            # Show summary
            print("\n" + "="*80)
            print("📋 VALIDATION SUMMARY")
            print("="*80)
            report = collector.get_validation_report()
            for point_name, report_data in report.items():
                status = "✅ VALIDATED" if report_data['validated'] else "⏳ PENDING"
                print(f"\n{status}")
                print(f"  Data Point: {point_name}")
                print(f"  Last Value: {report_data['last_value']}")
                print(f"  Confidence: {report_data['confidence']*100:.1f}%")
                print(f"  Samples: {report_data['samples']}")

            # Check if all validated
            all_validated = all(report_data['validated'] for report_data in report.values())

            if all_validated:
                print("\n" + "="*80)
                print("🎉 ALL DATA POINTS VALIDATED!")
                print("="*80)
                break

        elif user_input.startswith('V'):
            point_name = user_input[1:].lower()
            if point_name in collector.data_points:
                collector.validate_data_point(point_name, True)
            else:
                print(f"❌ Unknown data point: {point_name}")

        elif user_input.startswith('R'):
            point_name = user_input[1:].lower()
            if point_name in collector.data_points:
                print(f"\nRe-entering coordinates for {point_name}:")
                try:
                    top = int(input("  Top (pixels from top): ").strip())
                    left = int(input("  Left (pixels from left): ").strip())
                    width = int(input("  Width (pixels): ").strip())
                    height = int(input("  Height (pixels): ").strip())

                    new_region = {'top': top, 'left': left, 'width': width, 'height': height}
                    collector.data_points[point_name].region = new_region
                    print(f"✅ Updated {point_name} coordinates")
                except ValueError:
                    print("❌ Invalid input")
            else:
                print(f"❌ Unknown data point: {point_name}")

        elif user_input == 'Q':
            print("\n⚠️  Exiting without validating all points")
            break

        time.sleep(0.5)

    # Save configuration
    config_to_save = {
        'browser_id': browser_id,
        'data_points': {
            name: {
                'region': dp.region,
                'pattern': dp.pattern,
                'data_type': dp.data_type,
                'validated': collector.validation_status[name]
            }
            for name, dp in collector.data_points.items()
        },
        'timestamp': datetime.now().isoformat()
    }

    filename = f"browser_{browser_id}_config.json"
    with open(filename, 'w') as f:
        json.dump(config_to_save, f, indent=2)

    print(f"\n✅ Configuration saved to {filename}")
    print("\nYou can now add coordinates for the next browser or proceed with testing.")

    return collector, config_to_save


if __name__ == "__main__":
    print("�� Multi-Browser Data Collector")
    print("Choose mode:")
    print("1. Setup single browser (interactive validation)")
    print("2. Run multi-browser test")

    choice = input("\nEnter choice (1-2): ").strip()

    if choice == '1':
        collector, config = setup_single_browser_validation()
    else:
        main_multi_browser_test()
