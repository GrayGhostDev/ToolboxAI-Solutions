#!/usr/bin/env python3
import pytest
import requests
import json

# Skip all tests in this module as they require external services
pytestmark = pytest.mark.skip(reason="Integration tests require external services - run with --run-integration")

# Test credentials
users = [
    {"username": "admin", "password": "Admin123!", "role": "admin"},
    {"username": "john_teacher", "password": "Teacher123!", "role": "teacher"},
    {"username": "sarah_student", "password": "Student123!", "role": "student"},
]

url = "http://localhost:8008/auth/login"
headers = {
    "Content-Type": "application/json",
    "Origin": "http://localhost:5176"
}

print("Testing login functionality:")
print("=" * 50)

for user in users:
    print(f"\nTesting {user['role']} login:")
    print(f"Username: {user['username']}")
    
    data = {
        "username": user["username"],
        "password": user["password"]
    }
    
    try:
        response = requests.post(url, json=data, headers=headers, timeout=5)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Login successful!")
            print(f"Token: {result.get('access_token', 'N/A')[:20]}...")
            if 'user' in result:
                print(f"User role: {result['user'].get('role', 'N/A')}")
        else:
            print(f"❌ Login failed with status {response.status_code}")
            print(f"Response: {response.text}")
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")

print("\n" + "=" * 50)
print("Testing complete!")