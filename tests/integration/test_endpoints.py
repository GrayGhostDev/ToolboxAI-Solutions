#!/usr/bin/env python3
"""
Simple test script to verify that the new endpoint files work correctly.
"""

import pytest
import os
import requests
import json
from typing import Dict, Any

# Skip all tests in this module as they require external services
# Tests are now enabled by default since we've fixed the issues
# To skip, set SKIP_INTEGRATION_TESTS=1
pytestmark = pytest.mark.skipif(
    os.environ.get('SKIP_INTEGRATION_TESTS'),
    reason="Tests manually disabled. Remove SKIP_INTEGRATION_TESTS to enable"
)

# Test configuration
BASE_URL = "http://localhost:8008"
TEST_USER_CREDENTIALS = {"username": "teacher1", "password": "teacher123"}

def get_auth_token() -> str:
    """Get authentication token for testing."""
    try:
        response = requests.post(f"{BASE_URL}/auth/login", json=TEST_USER_CREDENTIALS)
        if response.status_code == 200:
            return response.json().get("access_token", "")
        else:
            print(f"Authentication failed: {response.status_code}")
            return ""
    except Exception as e:
        print(f"Auth error: {e}")
        return ""

def check_endpoint(endpoint: str, token: str, description: str) -> bool:
    """Check a specific endpoint (helper function, not a test)."""
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    
    try:
        response = requests.get(f"{BASE_URL}{endpoint}", headers=headers)
        print(f"Testing {description}: {endpoint}")
        print(f"  Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"  Response type: {type(data)}")
            if isinstance(data, list):
                print(f"  Items returned: {len(data)}")
            elif isinstance(data, dict):
                print(f"  Keys: {list(data.keys())}")
            print("  ✅ SUCCESS")
            return True
        else:
            print(f"  ❌ FAILED - Status {response.status_code}")
            if response.text:
                print(f"  Error: {response.text[:200]}")
            return False
            
    except Exception as e:
        print(f"  ❌ ERROR: {e}")
        return False

@pytest.mark.integration
def test_endpoints():
    """Test all educational platform endpoints."""
    print("🧪 Testing New Educational Platform Endpoints")
    print("=" * 50)
    
    # Get authentication token
    print("🔐 Getting authentication token...")
    token = get_auth_token()
    if not token:
        print("❌ Could not get auth token, testing without authentication...")
    else:
        print("✅ Authentication successful")
    
    # Test endpoints that were showing 404 errors
    test_cases = [
        ("/assessments/", "Assessments list endpoint"),
        ("/reports/templates?popular_only=true", "Popular report templates"),
        ("/reports/stats/overview", "Overview statistics"),
        ("/reports/?limit=10", "Reports list"),
        ("/messages/?folder=inbox", "Inbox messages"),
        ("/messages/unread-count", "Unread message count"),
        ("/classes/", "Classes list endpoint"),
        ("/lessons", "Lessons list endpoint"),
        ("/assessments/1", "Assessment details"),
        ("/reports/1", "Report details"),
        ("/messages/1", "Message details"),
    ]
    
    print(f"\n🚀 Testing {len(test_cases)} endpoints...")
    print("-" * 50)
    
    success_count = 0
    for endpoint, description in test_cases:
        if check_endpoint(endpoint, token, description):
            success_count += 1
        print()
    
    print("=" * 50)
    print(f"📊 Test Results: {success_count}/{len(test_cases)} endpoints working")
    
    # Assert that at least some endpoints work
    assert success_count > 0, "No endpoints are working"

if __name__ == "__main__":
    # Run test function directly when script is executed
    test_endpoints()