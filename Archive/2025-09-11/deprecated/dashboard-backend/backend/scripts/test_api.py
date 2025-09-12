#!/usr/bin/env python3
"""
Test API endpoints with sample data
"""

import requests
import json

BASE_URL = "http://localhost:8001"

def test_health():
    """Test health endpoint"""
    print("🔍 Testing health endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_login():
    """Test login endpoint with admin credentials"""
    print("\n🔍 Testing login endpoint...")
    try:
        data = {
            "email": "admin@toolboxai.com",
            "password": "Admin123!"
        }
        response = requests.post(f"{BASE_URL}/api/v1/auth/login", json=data)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        
        if response.status_code == 200:
            return response.json().get("access_token")
        return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def test_dashboard(token):
    """Test dashboard endpoint with authentication"""
    print("\n🔍 Testing dashboard endpoint...")
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{BASE_URL}/api/v1/dashboard", headers=headers)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    print("🚀 Testing Educational Platform API...\n")
    
    # Test health
    if not test_health():
        print("❌ Health check failed!")
        return
    
    # Test login
    token = test_login()
    if not token:
        print("❌ Login failed!")
        return
    
    print(f"✅ Login successful! Token: {token[:50]}...")
    
    # Test dashboard
    if test_dashboard(token):
        print("\n✅ Dashboard endpoint working!")
    else:
        print("\n❌ Dashboard endpoint failed!")
    
    print("\n🎉 API testing complete!")

if __name__ == "__main__":
    main()