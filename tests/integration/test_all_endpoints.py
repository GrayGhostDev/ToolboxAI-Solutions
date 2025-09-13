#!/usr/bin/env python3
"""
Comprehensive test script to verify all endpoints are working correctly.
"""

import pytest
import requests
import json
from typing import Dict, Any

# Skip all tests in this module as they require external services
pytestmark = pytest.mark.skip(reason="Integration tests require external services - run with --run-integration")

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

def test_endpoint(endpoint: str, token: str, description: str, method: str = "GET") -> bool:
    """Test a specific endpoint."""
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    
    try:
        if method == "GET":
            response = requests.get(f"{BASE_URL}{endpoint}", headers=headers)
        else:
            response = requests.request(method, f"{BASE_URL}{endpoint}", headers=headers)
            
        print(f"Testing {description}: {endpoint}")
        print(f"  Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"  Response type: {type(data)}")
            if isinstance(data, list):
                print(f"  Items returned: {len(data)}")
            elif isinstance(data, dict):
                keys = list(data.keys())[:5]  # Show first 5 keys
                print(f"  Keys: {keys}{'...' if len(data.keys()) > 5 else ''}")
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

def main():
    print("🧪 Testing All Educational Platform Endpoints")
    print("=" * 50)
    
    # Get authentication token
    print("🔐 Getting authentication token...")
    token = get_auth_token()
    if not token:
        print("❌ Could not get auth token, testing without authentication...")
    else:
        print("✅ Authentication successful")
    
    # All endpoints to test
    test_cases = [
        # Dashboard endpoints
        ("/dashboard/overview/teacher", "Teacher dashboard overview"),
        
        # Classes endpoints
        ("/classes/", "Classes list"),
        ("/classes/1", "Class details"),
        ("/classes/1/students", "Class students list"),
        
        # Lessons endpoints
        ("/lessons", "Lessons list"),
        ("/lessons/1", "Lesson details"),
        ("/lessons/1/progress", "Lesson progress"),
        
        # Assessments endpoints
        ("/assessments/", "Assessments list"),
        ("/assessments/1", "Assessment details"),
        ("/assessments/1/results", "Assessment results"),
        
        # Reports endpoints
        ("/reports/", "Reports list"),
        ("/reports/templates", "Report templates"),
        ("/reports/stats/overview", "Overview statistics"),
        ("/reports/analytics/engagement", "Engagement analytics"),
        
        # Messages endpoints
        ("/messages/", "Messages list"),
        ("/messages/unread-count", "Unread message count"),
        ("/messages/1", "Message details"),
        
        # Analytics endpoints
        ("/analytics/weekly_xp", "Weekly XP progression"),
        ("/analytics/subject_mastery", "Subject mastery levels"),
        
        # Gamification endpoints
        ("/gamification/leaderboard", "Leaderboard data"),
        
        # Compliance endpoints (admin only - might fail for teacher)
        ("/compliance/status", "Compliance status"),
        
        # Users endpoints (admin only - might fail for teacher)
        ("/users/", "Users list"),
        ("/users/user_1", "User details"),
        
        # Schools endpoints (admin only - might fail for teacher)
        ("/schools/", "Schools list"),
        ("/schools/school_1", "School details"),
    ]
    
    print(f"\n🚀 Testing {len(test_cases)} endpoints...")
    print("-" * 50)
    
    success_count = 0
    failed_endpoints = []
    
    for endpoint, description in test_cases:
        if test_endpoint(endpoint, token, description):
            success_count += 1
        else:
            failed_endpoints.append((endpoint, description))
        print()
    
    print("=" * 50)
    print(f"📊 Test Results: {success_count}/{len(test_cases)} endpoints working")
    
    if failed_endpoints:
        print("\n❌ Failed endpoints:")
        for endpoint, description in failed_endpoints:
            print(f"  - {description}: {endpoint}")
    
    if success_count == len(test_cases):
        print("🎉 All endpoints are working correctly!")
    elif success_count > len(test_cases) * 0.8:
        print("✅ Most endpoints are working correctly")
    elif success_count > len(test_cases) // 2:
        print("⚠️  Some endpoints are working, but issues remain")
    else:
        print("❌ Multiple endpoints have issues")

if __name__ == "__main__":
    main()