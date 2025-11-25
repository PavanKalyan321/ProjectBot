"""
Test script for multiplier logging API
Verifies that the API endpoints work correctly
"""

import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:5001"

def test_multiplier_logging():
    """Test the multiplier logging API."""
    print("\n" + "="*60)
    print("🧪 MULTIPLIER LOGGING API TEST")
    print("="*60)

    # Test 1: Create a round
    print("\n[1] Testing round creation...")
    round_data = {
        "bot_id": "test_bot_001",
        "round_number": 1,
        "stake_value": 25.0,
        "strategy_name": "custom",
        "game_name": "aviator",
        "platform_code": "demo",
        "session_id": "test_session_" + str(int(datetime.now().timestamp()))
    }

    try:
        response = requests.post(f"{BASE_URL}/api/multiplier/create_round", json=round_data)
        print(f"   Status: {response.status_code}")
        result = response.json()
        print(f"   Response: {json.dumps(result, indent=2)}")

        if result.get("status") == "success":
            round_id = result.get("round_id")
            print(f"   ✅ Round created with ID: {round_id}")
        else:
            print(f"   ❌ Failed to create round")
            return

    except Exception as e:
        print(f"   ❌ Error: {e}")
        return

    # Test 2: Log multiplier values
    print("\n[2] Testing multiplier logging...")
    multiplier_values = [1.05, 1.12, 1.23, 1.35, 1.47, 1.58, 1.72, 1.89, 2.01]

    for mult in multiplier_values:
        mult_data = {
            "bot_id": "test_bot_001",
            "multiplier": mult,
            "round_id": round_id,
            "is_crash": False,
            "game_name": "aviator",
            "platform_code": "demo",
            "timestamp": datetime.utcnow().isoformat()
        }

        try:
            response = requests.post(f"{BASE_URL}/api/multiplier/log", json=mult_data)
            print(f"   Multiplier {mult}x -> Status: {response.status_code}")
            result = response.json()

            if result.get("status") == "success":
                print(f"      ✅ Logged (record_id: {result.get('record_id')})")
            else:
                print(f"      ❌ Failed: {result.get('message')}")

        except Exception as e:
            print(f"   ❌ Error logging {mult}x: {e}")

    # Test 3: Log crash multiplier
    print("\n[3] Testing crash multiplier logging...")
    crash_data = {
        "bot_id": "test_bot_001",
        "multiplier": 2.15,
        "round_id": round_id,
        "is_crash": True,
        "game_name": "aviator",
        "platform_code": "demo",
        "timestamp": datetime.utcnow().isoformat()
    }

    try:
        response = requests.post(f"{BASE_URL}/api/multiplier/log", json=crash_data)
        print(f"   Status: {response.status_code}")
        result = response.json()

        if result.get("status") == "success":
            print(f"   ✅ Crash multiplier logged (record_id: {result.get('record_id')})")
        else:
            print(f"   ❌ Failed: {result.get('message')}")

    except Exception as e:
        print(f"   ❌ Error: {e}")

    # Test 4: Get latest round
    print("\n[4] Testing get latest round...")
    try:
        response = requests.get(f"{BASE_URL}/api/multiplier/latest_round/test_bot_001")
        print(f"   Status: {response.status_code}")
        result = response.json()

        if result.get("status") == "success" and result.get("round"):
            round_info = result.get("round")
            print(f"   ✅ Latest round found:")
            print(f"      Round ID: {round_info.get('id')}")
            print(f"      Round Number: {round_info.get('number')}")
        else:
            print(f"   ℹ️ No active round found")

    except Exception as e:
        print(f"   ❌ Error: {e}")

    print("\n" + "="*60)
    print("✅ API TESTS COMPLETED")
    print("="*60 + "\n")


if __name__ == "__main__":
    print("\n🔌 Connecting to API at", BASE_URL)
    print("Make sure the dashboard is running: python run_dashboard.py --port 5001\n")

    try:
        # Test connectivity
        response = requests.get(f"{BASE_URL}/api/current_round", timeout=2)
        print("✅ API is reachable!")
    except:
        print("❌ API is not reachable. Make sure the dashboard is running.")
        print("   Start with: python run_dashboard.py --port 5001")
        exit(1)

    test_multiplier_logging()
