"""
Test script to verify all modules are working correctly.
Run this to ensure the modularization was successful.
"""

import sys
import traceback

def test_imports():
    """Test all module imports."""
    print("="*60)
    print("Testing Module Imports")
    print("="*60)
    
    tests = [
        ("Config Module", "from config import ConfigManager"),
        ("Game Detector", "from core import GameStateDetector"),
        ("History Tracker", "from core import RoundHistoryTracker"),
        ("ML Signal Generator", "from core import MLSignalGenerator"),
        ("Dashboard", "from dashboard import AviatorDashboard"),
        ("Clipboard Utils", "from utils import clear_clipboard, read_clipboard"),
        ("OCR Utils", "from utils import preprocess_image_for_ocr"),
        ("Betting Helpers", "from utils import verify_bet_placed, estimate_multiplier"),
    ]
    
    passed = 0
    failed = 0
    
    for name, import_stmt in tests:
        try:
            exec(import_stmt)
            print(f"✅ {name:25} - OK")
            passed += 1
        except Exception as e:
            print(f"❌ {name:25} - FAILED: {str(e)}")
            failed += 1
    
    print("\n" + "="*60)
    print(f"Results: {passed} passed, {failed} failed")
    print("="*60)
    
    return failed == 0

def test_instantiation():
    """Test basic instantiation of classes."""
    print("\n" + "="*60)
    print("Testing Class Instantiation")
    print("="*60)
    
    try:
        from config import ConfigManager
        config = ConfigManager()
        print("✅ ConfigManager instantiated")
        
        from core import RoundHistoryTracker
        tracker = RoundHistoryTracker()
        print("✅ RoundHistoryTracker instantiated")
        
        from core import MLSignalGenerator
        ml_gen = MLSignalGenerator(tracker)
        print("✅ MLSignalGenerator instantiated")
        
        from core import GameStateDetector
        detector = GameStateDetector((100, 100, 200, 50))
        print("✅ GameStateDetector instantiated")
        
        print("\n✅ All classes instantiated successfully!")
        return True
        
    except Exception as e:
        print(f"\n❌ Instantiation failed: {str(e)}")
        traceback.print_exc()
        return False

def test_module_structure():
    """Test module structure and exports."""
    print("\n" + "="*60)
    print("Testing Module Structure")
    print("="*60)
    
    try:
        import config
        print(f"✅ config module exports: {config.__all__}")
        
        import core
        print(f"✅ core module exports: {core.__all__}")
        
        import dashboard
        print(f"✅ dashboard module exports: {dashboard.__all__}")
        
        import utils
        print(f"✅ utils module exports: {utils.__all__}")
        
        print("\n✅ All module structures valid!")
        return True
        
    except Exception as e:
        print(f"\n❌ Structure test failed: {str(e)}")
        traceback.print_exc()
        return False

def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("🧪 AVIATOR BOT - MODULE VERIFICATION")
    print("="*60 + "\n")
    
    results = []
    
    # Test imports
    results.append(("Imports", test_imports()))
    
    # Test instantiation
    results.append(("Instantiation", test_instantiation()))
    
    # Test structure
    results.append(("Structure", test_module_structure()))
    
    # Final summary
    print("\n" + "="*60)
    print("📊 FINAL SUMMARY")
    print("="*60)
    
    all_passed = True
    for test_name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name:20} {status}")
        if not passed:
            all_passed = False
    
    print("="*60)
    
    if all_passed:
        print("\n🎉 All tests passed! Modularization successful!")
        print("\nYou can now run the bot with:")
        print("  python bot_modular.py")
    else:
        print("\n⚠️ Some tests failed. Please check the errors above.")
    
    print()
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())
