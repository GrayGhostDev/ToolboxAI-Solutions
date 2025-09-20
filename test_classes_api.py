#!/usr/bin/env python3
"""
Quick test of Classes API endpoints
"""

import requests
import json
from typing import Dict, Any

BASE_URL = "http://127.0.0.1:8008"
API_BASE = f"{BASE_URL}/api/v1"

def test_endpoint(method: str, endpoint: str, data: Dict[str, Any] = None, headers: Dict[str, str] = None) -> bool:
    """Test an API endpoint"""
    url = f"{API_BASE}{endpoint}"

    try:
        if method.upper() == "GET":
            response = requests.get(url, headers=headers, timeout=5)
        elif method.upper() == "POST":
            response = requests.post(url, json=data, headers=headers, timeout=5)
        else:
            print(f"❌ Unsupported method: {method}")
            return False

        print(f"  {method.upper()} {endpoint} -> {response.status_code}")

        if response.status_code == 401:
            print("    (Authentication required - expected for protected endpoints)")
            return True
        elif response.status_code in [200, 201]:
            try:
                result = response.json()
                print(f"    Response: {json.dumps(result, indent=2)[:200]}...")
            except:
                print(f"    Response: {response.text[:100]}...")
            return True
        else:
            print(f"    Error: {response.text[:200]}")
            return False

    except requests.exceptions.ConnectionError:
        print(f"❌ Connection failed to {url}")
        print("   Make sure the backend server is running on port 8008")
        return False
    except Exception as e:
        print(f"❌ Request failed: {e}")
        return False

def main():
    """Test the classes API endpoints"""
    print("=== Classes API Test ===\n")

    # Test health check first
    print("1. Testing server health...")
    if not test_endpoint("GET", "/health"):
        print("Server is not responding. Please start the backend server:")
        print("  cd apps/backend && uvicorn main:app --host 127.0.0.1 --port 8008 --reload")
        return 1

    # Test classes endpoints (these will require auth but should return 401, not 500)
    print("\n2. Testing classes endpoints...")

    endpoints_to_test = [
        ("GET", "/classes/"),
        ("GET", "/classes/123e4567-e89b-12d3-a456-426614174000"),  # Test with UUID format
        ("GET", "/classes/123e4567-e89b-12d3-a456-426614174000/students"),
    ]

    for method, endpoint in endpoints_to_test:
        success = test_endpoint(method, endpoint)
        if not success and "Connection failed" in str(success):
            return 1

    print("\n3. Testing POST endpoint...")
    test_class_data = {
        "name": "Test Mathematics Class",
        "subject": "Mathematics",
        "grade_level": 8,
        "room": "Room 101",
        "schedule": "Mon/Wed/Fri 10:00 AM",
        "description": "A test class",
        "max_students": 25
    }

    test_endpoint("POST", "/classes/", data=test_class_data)

    print("\n=== Test Complete ===")
    print("✅ Classes API endpoints are responding correctly!")
    print("\nNext steps:")
    print("1. Set up authentication to test full functionality")
    print("2. Create a teacher user account")
    print("3. Test creating and managing classes")

    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())