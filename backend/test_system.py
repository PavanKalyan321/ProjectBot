"""
Comprehensive System Test Suite
Tests all components of the Aviator Bot system
"""

import os
import sys
import time
import pandas as pd
from datetime import datetime

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Color codes for terminal output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'
BOLD = '\033[1m'


class SystemTester:
    """Comprehensive system testing."""

    def __init__(self):
        self.tests_passed = 0
        self.tests_failed = 0
        self.tests_total = 0
        self.failures = []

    def print_header(self, title):
        """Print test section header."""
        print(f"\n{BLUE}{BOLD}{'='*80}")
        print(f"  {title}")
        print(f"{'='*80}{RESET}\n")

    def print_test(self, test_name):
        """Print test name."""
        print(f"  {YELLOW}>{RESET} {test_name}...", end=' ', flush=True)

    def print_success(self, message=""):
        """Print success message."""
        self.tests_passed += 1
        self.tests_total += 1
        msg = f" {message}" if message else ""
        print(f"{GREEN}[PASS]{RESET}{msg}")

    def print_failure(self, error):
        """Print failure message."""
        self.tests_failed += 1
        self.tests_total += 1
        print(f"{RED}[FAIL]{RESET}")
        print(f"    {RED}Error: {error}{RESET}")
        self.failures.append((self.tests_total, error))

    def test_imports(self):
        """Test that all required modules can be imported."""
        self.print_header("1. TESTING IMPORTS")

        # Core modules
        modules = [
            ('pandas', 'pandas'),
            ('numpy', 'numpy'),
            ('sklearn', 'scikit-learn'),
            ('flask', 'Flask'),
            ('flask_socketio', 'Flask-SocketIO'),
        ]

        for module_name, display_name in modules:
            self.print_test(f"Import {display_name}")
            try:
                __import__(module_name)
                self.print_success()
            except ImportError as e:
                self.print_failure(f"Cannot import {display_name}: {e}")

        # Optional modules
        optional_modules = [
            ('lightgbm', 'LightGBM'),
            ('tensorflow', 'TensorFlow')
        ]

        for module_name, display_name in optional_modules:
            self.print_test(f"Import {display_name} (optional)")
            try:
                __import__(module_name)
                self.print_success()
            except ImportError:
                print(f"{YELLOW}[SKIP] (optional){RESET}")

    def test_file_structure(self):
        """Test that all required files exist."""
        self.print_header("2. TESTING FILE STRUCTURE")

        required_files = [
            'bot_modular.py',
            'config.py',
            'core/history_tracker.py',
            'core/ml_models.py',
            'core/ml_signal_generator.py',
            'core/game_detector.py',
            'dashboard/dashboard_server.py',
            'dashboard/templates/advanced_dashboard.html',
            'train_models.py',
            'clean_csv.py',
            'add_manual_history.py',
        ]

        for file_path in required_files:
            self.print_test(f"Check {file_path}")
            full_path = os.path.join(os.path.dirname(__file__), file_path)
            if os.path.exists(full_path):
                self.print_success()
            else:
                self.print_failure(f"File not found: {file_path}")

    def test_csv_operations(self):
        """Test CSV file operations."""
        self.print_header("3. TESTING CSV OPERATIONS")

        csv_file = 'aviator_rounds_history.csv'
        full_path = os.path.join(os.path.dirname(__file__), csv_file)

        # Test 1: CSV file exists
        self.print_test(f"Check {csv_file} exists")
        if os.path.exists(full_path):
            self.print_success()
        else:
            self.print_failure(f"CSV file not found: {csv_file}")
            return

        # Test 2: CSV can be read
        self.print_test("Read CSV with pandas")
        try:
            df = pd.read_csv(full_path)
            self.print_success(f"({len(df)} rows)")
        except Exception as e:
            self.print_failure(f"Cannot read CSV: {e}")
            return

        # Test 3: Check required columns
        self.print_test("Verify CSV columns")
        required_columns = [
            'timestamp', 'round_id', 'multiplier', 'bet_placed',
            'stake_amount', 'cashout_time', 'profit_loss',
            'model_prediction', 'model_confidence'
        ]

        missing_cols = [col for col in required_columns if col not in df.columns]
        if not missing_cols:
            self.print_success(f"({len(df.columns)} columns)")
        else:
            self.print_failure(f"Missing columns: {missing_cols}")

        # Test 4: Check data integrity
        self.print_test("Check data integrity")
        try:
            # Check for valid multipliers
            if 'multiplier' in df.columns:
                valid_mults = df[df['multiplier'] > 0]
                invalid_count = len(df) - len(valid_mults)
                if invalid_count == 0:
                    self.print_success("(all multipliers valid)")
                else:
                    self.print_failure(f"{invalid_count} invalid multipliers")
            else:
                self.print_failure("No 'multiplier' column")
        except Exception as e:
            self.print_failure(f"Data integrity check failed: {e}")

    def test_history_tracker(self):
        """Test RoundHistoryTracker functionality."""
        self.print_header("4. TESTING HISTORY TRACKER")

        self.print_test("Import RoundHistoryTracker")
        try:
            from core.history_tracker import RoundHistoryTracker
            self.print_success()
        except ImportError as e:
            self.print_failure(f"Cannot import: {e}")
            return

        self.print_test("Initialize history tracker")
        try:
            tracker = RoundHistoryTracker()
            self.print_success()
        except Exception as e:
            self.print_failure(f"Initialization failed: {e}")
            return

        self.print_test("Get recent rounds")
        try:
            rounds = tracker.get_recent_rounds(10)
            self.print_success(f"(retrieved {len(rounds)} rounds)")
        except Exception as e:
            self.print_failure(f"Failed to get rounds: {e}")

        self.print_test("Get recent multipliers")
        try:
            multipliers = tracker.get_recent_multipliers(10)
            self.print_success(f"({len(multipliers)} multipliers)")
        except Exception as e:
            self.print_failure(f"Failed to get multipliers: {e}")

    def test_ml_models(self):
        """Test ML models functionality."""
        self.print_header("5. TESTING ML MODELS")

        self.print_test("Import AviatorMLModels")
        try:
            from core.ml_models import AviatorMLModels
            self.print_success()
        except ImportError as e:
            self.print_failure(f"Cannot import: {e}")
            return

        self.print_test("Initialize ML models")
        try:
            models = AviatorMLModels(models_dir='models')
            self.print_success()
        except Exception as e:
            self.print_failure(f"Initialization failed: {e}")
            return

        self.print_test("Check for trained models")
        try:
            loaded = models.load_models()
            if loaded:
                self.print_success("(models loaded)")
            else:
                print(f"{YELLOW}[SKIP] (no trained models){RESET}")
        except Exception as e:
            self.print_failure(f"Model loading failed: {e}")

        # Test feature engineering
        self.print_test("Test feature engineering")
        try:
            test_data = pd.DataFrame({
                'multiplier': [1.5, 2.3, 1.8, 3.2, 2.1, 1.9, 2.5, 1.7,
                              2.8, 1.6, 2.2, 1.9, 3.1, 2.4, 1.8, 2.6,
                              1.7, 2.9, 2.0, 1.8, 2.3, 1.9, 2.7, 2.1]
            })
            X, y = models.engineer_features(test_data)
            if X is not None and len(X) > 0:
                self.print_success(f"({X.shape[1]} features)")
            else:
                self.print_failure("Feature engineering returned None")
        except Exception as e:
            self.print_failure(f"Feature engineering failed: {e}")

    def test_ml_signal_generator(self):
        """Test ML signal generator."""
        self.print_header("6. TESTING ML SIGNAL GENERATOR")

        self.print_test("Import MLSignalGenerator")
        try:
            from core.ml_signal_generator import MLSignalGenerator
            from core.history_tracker import RoundHistoryTracker
            self.print_success()
        except ImportError as e:
            self.print_failure(f"Cannot import: {e}")
            return

        self.print_test("Initialize signal generator")
        try:
            tracker = RoundHistoryTracker()
            generator = MLSignalGenerator(tracker)
            self.print_success()
        except Exception as e:
            self.print_failure(f"Initialization failed: {e}")
            return

        self.print_test("Generate ensemble signal")
        try:
            signal = generator.generate_ensemble_signal()
            if signal and 'should_bet' in signal:
                self.print_success(f"(confidence: {signal.get('confidence', 0):.1f}%)")
            else:
                self.print_failure("Invalid signal format")
        except Exception as e:
            self.print_failure(f"Signal generation failed: {e}")

    def test_dashboard(self):
        """Test dashboard components."""
        self.print_header("7. TESTING DASHBOARD")

        self.print_test("Import Flask")
        try:
            from flask import Flask
            self.print_success()
        except ImportError as e:
            self.print_failure(f"Cannot import Flask: {e}")
            return

        self.print_test("Import SocketIO")
        try:
            from flask_socketio import SocketIO
            self.print_success()
        except ImportError as e:
            self.print_failure(f"Cannot import SocketIO: {e}")
            return

        self.print_test("Check dashboard template")
        template_path = os.path.join(
            os.path.dirname(__file__),
            'dashboard/templates/advanced_dashboard.html'
        )
        if os.path.exists(template_path):
            self.print_success()
        else:
            self.print_failure("Template not found")

        self.print_test("Verify template contains charts")
        try:
            with open(template_path, 'r', encoding='utf-8') as f:
                content = f.read()
                required_elements = [
                    'ensemble-vs-actual-chart',
                    'models-vs-actual-chart',
                    'spike-predictor-chart',
                    'multiplier-timeseries-chart'
                ]
                missing = [elem for elem in required_elements if elem not in content]
                if not missing:
                    self.print_success("(all 4 charts present)")
                else:
                    self.print_failure(f"Missing charts: {missing}")
        except Exception as e:
            self.print_failure(f"Template verification failed: {e}")

    def test_utilities(self):
        """Test utility scripts."""
        self.print_header("8. TESTING UTILITY SCRIPTS")

        utilities = [
            ('clean_csv.py', 'CSV cleaner'),
            ('add_manual_history.py', 'Manual history loader'),
            ('train_models.py', 'Model trainer'),
            ('migrate_csv_header.py', 'CSV migration tool'),
        ]

        for script, description in utilities:
            self.print_test(f"Check {description}")
            full_path = os.path.join(os.path.dirname(__file__), script)
            if os.path.exists(full_path):
                # Try to import/parse the file
                try:
                    with open(full_path, 'r', encoding='utf-8') as f:
                        code = f.read()
                        compile(code, script, 'exec')
                    self.print_success()
                except SyntaxError as e:
                    self.print_failure(f"Syntax error in {script}: {e}")
            else:
                self.print_failure(f"Script not found: {script}")

    def test_configuration(self):
        """Test configuration system."""
        self.print_header("9. TESTING CONFIGURATION")

        self.print_test("Import ConfigManager")
        try:
            from config import ConfigManager
            self.print_success()
        except ImportError as e:
            self.print_failure(f"Cannot import: {e}")
            return

        self.print_test("Initialize ConfigManager")
        try:
            config = ConfigManager()
            self.print_success()
        except Exception as e:
            self.print_failure(f"Initialization failed: {e}")
            return

        self.print_test("Check config attributes")
        try:
            required_attrs = [
                'initial_stake', 'max_stake', 'cashout_delay',
                'stake_increase_percent'
            ]
            missing = [attr for attr in required_attrs if not hasattr(config, attr)]
            if not missing:
                self.print_success()
            else:
                self.print_failure(f"Missing attributes: {missing}")
        except Exception as e:
            self.print_failure(f"Attribute check failed: {e}")

    def run_all_tests(self):
        """Run all tests and print summary."""
        print(f"\n{BOLD}{BLUE}{'='*80}")
        print(f"  AVIATOR BOT - SYSTEM TEST SUITE")
        print(f"{'='*80}{RESET}\n")

        start_time = time.time()

        # Run all test suites
        self.test_imports()
        self.test_file_structure()
        self.test_csv_operations()
        self.test_history_tracker()
        self.test_ml_models()
        self.test_ml_signal_generator()
        self.test_dashboard()
        self.test_utilities()
        self.test_configuration()

        elapsed = time.time() - start_time

        # Print summary
        self.print_summary(elapsed)

    def print_summary(self, elapsed):
        """Print test summary."""
        print(f"\n{BOLD}{BLUE}{'='*80}")
        print(f"  TEST SUMMARY")
        print(f"{'='*80}{RESET}\n")

        print(f"  Total tests:     {self.tests_total}")
        print(f"  {GREEN}Passed:{RESET}        {self.tests_passed}")
        print(f"  {RED}Failed:{RESET}        {self.tests_failed}")
        print(f"  Time elapsed:    {elapsed:.2f}s")

        if self.tests_failed > 0:
            print(f"\n{RED}{BOLD}  FAILURES:{RESET}")
            for test_num, error in self.failures:
                print(f"    {test_num}. {error}")

        print(f"\n{BOLD}{'='*80}{RESET}\n")

        if self.tests_failed == 0:
            print(f"{GREEN}{BOLD}[SUCCESS] ALL TESTS PASSED! System is ready.{RESET}\n")
            return 0
        else:
            pass_rate = (self.tests_passed / self.tests_total) * 100
            print(f"{YELLOW}[WARNING] {self.tests_failed} test(s) failed ({pass_rate:.1f}% passed){RESET}\n")
            return 1


def main():
    """Main entry point."""
    print("\nStarting system tests...\n")

    tester = SystemTester()
    exit_code = tester.run_all_tests()

    # Print recommendations
    if exit_code != 0:
        print(f"{YELLOW}RECOMMENDATIONS:{RESET}")
        print("  1. Install missing dependencies:")
        print("     pip install -r requirements.txt")
        print("  2. Run CSV migration if needed:")
        print("     python migrate_csv_header.py")
        print("  3. Train models if not yet trained:")
        print("     python train_models.py")
        print()

    sys.exit(exit_code)


if __name__ == '__main__':
    main()
