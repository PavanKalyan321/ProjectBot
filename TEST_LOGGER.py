"""
Test Script for Standalone Round Logger
========================================

Verifies all dependencies and configurations before running the main script.

Usage:
    python TEST_LOGGER.py

This will:
    1. Check Tesseract installation
    2. Verify Python packages
    3. Test database connection
    4. Capture and test OCR on a screen region
    5. Verify AviatorRound table exists

Author: Aviator Bot
Date: 2025-11-23
"""

import os
import sys
from pathlib import Path

# Color codes for terminal output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


def print_header(text):
    """Print section header."""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'=' * 70}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text:^70}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'=' * 70}{Colors.RESET}\n")


def print_success(text):
    """Print success message."""
    print(f"{Colors.GREEN}✓ {text}{Colors.RESET}")


def print_error(text):
    """Print error message."""
    print(f"{Colors.RED}✗ {text}{Colors.RESET}")


def print_warning(text):
    """Print warning message."""
    print(f"{Colors.YELLOW}⚠ {text}{Colors.RESET}")


def check_tesseract():
    """Check if Tesseract is installed."""
    print_header("1. CHECKING TESSERACT OCR INSTALLATION")

    common_paths = [
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
        "/usr/bin/tesseract",
        "/usr/local/bin/tesseract",
    ]

    for path in common_paths:
        if os.path.exists(path):
            print_success(f"Tesseract found at: {path}")
            try:
                import pytesseract
                pytesseract.pytesseract.pytesseract_cmd = path
                version = pytesseract.get_tesseract_version()
                print_success(f"Tesseract version: {version}")
                return True
            except Exception as e:
                print_error(f"Error getting version: {e}")
                return False

    print_error("Tesseract not found in common locations")
    print(f"\n  Expected at: {common_paths[0]}")
    print(f"  Download from: https://github.com/UB-Mannheim/tesseract/wiki\n")
    return False


def check_python_packages():
    """Check if all required Python packages are installed."""
    print_header("2. CHECKING PYTHON PACKAGES")

    packages = {
        'pytesseract': 'OCR text extraction',
        'cv2': 'Image processing',
        'mss': 'Screen capture',
        'PIL': 'Image handling',
        'numpy': 'Numerical operations',
        'psycopg2': 'PostgreSQL database',
        'dotenv': 'Environment variables',
    }

    missing = []
    for package, description in packages.items():
        try:
            __import__(package)
            print_success(f"{package:20} - {description}")
        except ImportError:
            print_error(f"{package:20} - {description} (MISSING)")
            missing.append(package)

    if missing:
        print(f"\n{Colors.YELLOW}Install missing packages with:{Colors.RESET}")
        print(f"  pip install -r requirements.txt\n")
        return False

    return True


def check_environment_variables():
    """Check .env file and database credentials."""
    print_header("3. CHECKING ENVIRONMENT VARIABLES")

    env_file = Path("c:\\Project\\.env") if sys.platform == 'win32' else Path(".env")

    if not env_file.exists():
        print_error(f".env file not found at: {env_file}")
        print("\n  Create .env file with:")
        print("    DB_HOST=zofojiubrykbtmstfhzx.supabase.co")
        print("    DB_PORT=5432")
        print("    DB_NAME=postgres")
        print("    DB_USER=postgres")
        print("    DB_PASSWORD=your_password_here\n")
        return False

    print_success(f".env file found at: {env_file}")

    from dotenv import load_dotenv
    load_dotenv(env_file)

    required_vars = ['DB_HOST', 'DB_PORT', 'DB_NAME', 'DB_USER', 'DB_PASSWORD']
    missing_vars = []

    for var in required_vars:
        value = os.getenv(var)
        if value:
            # Mask password
            display_value = "***" if var == "DB_PASSWORD" else value
            print_success(f"{var:20} = {display_value}")
        else:
            print_error(f"{var:20} = (NOT SET)")
            missing_vars.append(var)

    if missing_vars:
        print(f"\n{Colors.RED}Missing variables: {', '.join(missing_vars)}{Colors.RESET}\n")
        return False

    return True


def test_database_connection():
    """Test connection to Supabase database."""
    print_header("4. TESTING DATABASE CONNECTION")

    try:
        import psycopg2
        from dotenv import load_dotenv

        load_dotenv()

        conn = psycopg2.connect(
            host=os.getenv("DB_HOST"),
            port=int(os.getenv("DB_PORT", "5432")),
            database=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            sslmode="require",
            connect_timeout=10
        )

        print_success("Connected to Supabase database!")

        # Check if AviatorRound table exists
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_name = 'AviatorRound'
            )
            """
        )
        table_exists = cursor.fetchone()[0]

        if table_exists:
            print_success("AviatorRound table exists")

            # Get table info
            cursor.execute(
                """
                SELECT column_name, data_type
                FROM information_schema.columns
                WHERE table_name = 'AviatorRound'
                """
            )
            columns = cursor.fetchall()
            print(f"\n  Table columns:")
            for col_name, col_type in columns:
                print(f"    - {col_name:20} : {col_type}")
            print()
        else:
            print_error("AviatorRound table NOT found")
            print("\n  Create table with:")
            print("""
    CREATE TABLE public."AviatorRound" (
        "roundId" bigint generated by default as identity not null,
        "multiplier" real not null,
        "timestamp" timestamp without time zone default current_timestamp,
        constraint "AviatorRound_pkey" primary key ("roundId")
    );
            """)

        # Get row count
        cursor.execute("SELECT COUNT(*) FROM \"AviatorRound\"")
        count = cursor.fetchone()[0]
        print_success(f"Table contains {count} rows")

        cursor.close()
        conn.close()

        return table_exists

    except Exception as e:
        print_error(f"Database connection failed: {e}")
        print("\n  Check:")
        print("    - .env file has correct DB_PASSWORD")
        print("    - Supabase project exists")
        print("    - Network can reach zofojiubrykbtmstfhzx.supabase.co\n")
        return False


def test_screen_capture():
    """Test screen capture capability."""
    print_header("5. TESTING SCREEN CAPTURE")

    try:
        import mss
        import numpy as np

        region = {"top": 506, "left": 330, "width": 322, "height": 76}

        with mss.mss() as sct:
            screenshot = sct.grab(region)
            frame = np.array(screenshot)[..., :3]

        print_success(f"Screen capture successful!")
        print(f"  Region captured: {region['width']}x{region['height']} pixels")
        print(f"  Position: ({region['left']}, {region['top']})")
        print(f"  Frame shape: {frame.shape}")

        return True

    except Exception as e:
        print_error(f"Screen capture failed: {e}")
        print("\n  Check:")
        print("    - Game is visible on screen")
        print("    - Screen region coordinates are correct")
        print("    - Game window is not minimized\n")
        return False


def test_ocr():
    """Test OCR on captured screen."""
    print_header("6. TESTING OCR EXTRACTION")

    try:
        import mss
        import cv2
        import numpy as np
        import pytesseract

        region = {"top": 506, "left": 330, "width": 322, "height": 76}

        with mss.mss() as sct:
            screenshot = sct.grab(region)
            frame = np.array(screenshot)[..., :3]

        # Preprocess
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)

        # OCR
        config = r'--psm 7 --oem 3 -c tessedit_char_whitelist=0123456789.xABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'
        text = pytesseract.image_to_string(thresh, config=config).strip()

        print_success(f"OCR extraction successful!")
        print(f"  Extracted text: '{text}'")

        # Try to parse multiplier
        import re
        match = re.search(r'(\d{1,3}\.\d+)', text)
        if match:
            multiplier = float(match.group(1))
            print_success(f"Parsed multiplier: {multiplier:.2f}x")
            return True
        else:
            print_warning(f"Could not parse multiplier from: '{text}'")
            print("  This is normal if game is not currently showing a multiplier")
            return True  # Not fatal - game may be between rounds

    except Exception as e:
        print_error(f"OCR test failed: {e}")
        print("\n  Check:")
        print("    - Tesseract is installed")
        print("    - Screen capture is working")
        print("    - Game is visible and showing multiplier\n")
        return False


def main():
    """Run all tests."""
    print(f"\n{Colors.BOLD}{Colors.BLUE}")
    print("=" * 70)
    print("  STANDALONE ROUND LOGGER - SYSTEM TEST".center(70))
    print("=" * 70)
    print(Colors.RESET)

    tests = [
        ("Tesseract OCR", check_tesseract),
        ("Python Packages", check_python_packages),
        ("Environment Variables", check_environment_variables),
        ("Database Connection", test_database_connection),
        ("Screen Capture", test_screen_capture),
        ("OCR Extraction", test_ocr),
    ]

    results = []

    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print_error(f"Test failed with exception: {e}")
            results.append((test_name, False))

    # Summary
    print_header("TEST SUMMARY")

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = f"{Colors.GREEN}✓ PASS{Colors.RESET}" if result else f"{Colors.RED}✗ FAIL{Colors.RESET}"
        print(f"  {test_name:30} {status}")

    print(f"\n  {Colors.BOLD}Result: {passed}/{total} tests passed{Colors.RESET}\n")

    if passed == total:
        print_success("All systems ready! You can now run standalone_round_logger.py")
        print(f"\n  Run: {Colors.BOLD}python standalone_round_logger.py{Colors.RESET}\n")
        return 0
    else:
        print_error("Some tests failed. Please fix the issues above before running the logger.")
        print(f"\n  See: {Colors.BOLD}STANDALONE_LOGGER_SETUP.md{Colors.RESET} for troubleshooting\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
