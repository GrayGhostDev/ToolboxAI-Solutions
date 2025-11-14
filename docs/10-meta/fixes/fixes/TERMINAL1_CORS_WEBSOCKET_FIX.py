#!/usr/bin/env python3
"""
TERMINAL 1 - CORS and WebSocket Fix Verification
================================================
This script verifies all fixes applied to resolve dashboard-backend integration issues.

Issues Fixed:
1. CORS policy blocking requests from dashboard (port 5179)
2. Socket.IO endpoint not properly mounted at /socket.io/
3. Token verification import error causing "server error"
4. OPTIONS preflight requests returning 400 errors

Date: 2025-09-11
"""

import json
import sys
from datetime import datetime

import requests

# Configuration
BACKEND_URL = "http://localhost:8008"
DASHBOARD_ORIGIN = "http://localhost:5179"


def test_health():
    """Test basic health endpoint."""
    try:
        response = requests.get(f"{BACKEND_URL}/health", headers={"Origin": DASHBOARD_ORIGIN})
        return response.status_code == 200
    except:
        return False


def test_cors_preflight():
    """Test CORS preflight for /auth/verify."""
    try:
        response = requests.options(
            f"{BACKEND_URL}/auth/verify",
            headers={
                "Origin": DASHBOARD_ORIGIN,
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Content-Type, Authorization",
            },
        )
        return response.status_code == 200
    except:
        return False


def test_socketio_endpoint():
    """Test Socket.IO endpoint availability."""
    try:
        response = requests.get(
            f"{BACKEND_URL}/socket.io/?EIO=4&transport=polling",
            headers={"Origin": DASHBOARD_ORIGIN},
        )
        return response.status_code == 200 and response.text.startswith("0")
    except:
        return False


def test_auth_verify():
    """Test auth verification endpoint."""
    try:
        response = requests.post(
            f"{BACKEND_URL}/auth/verify",
            headers={
                "Origin": DASHBOARD_ORIGIN,
                "Content-Type": "application/json",
                "Authorization": "Bearer test-token",
            },
        )
        # 401 is expected without valid token
        return response.status_code in [200, 401]
    except:
        return False


def test_api_status():
    """Test API status endpoint."""
    try:
        response = requests.get(
            f"{BACKEND_URL}/api/v1/status", headers={"Origin": DASHBOARD_ORIGIN}
        )
        return response.status_code == 200
    except:
        return False


def main():
    """Run all tests and report results."""
    print("=" * 60)
    print("TERMINAL 1 - Dashboard-Backend Integration Verification")
    print("=" * 60)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print(f"Backend URL: {BACKEND_URL}")
    print(f"Dashboard Origin: {DASHBOARD_ORIGIN}")
    print()

    tests = [
        ("Health Endpoint", test_health),
        ("CORS Preflight", test_cors_preflight),
        ("Socket.IO Endpoint", test_socketio_endpoint),
        ("Auth Verify", test_auth_verify),
        ("API Status", test_api_status),
    ]

    results = {}
    all_passed = True

    for test_name, test_func in tests:
        print(f"Testing {test_name}...", end=" ")
        try:
            result = test_func()
            results[test_name] = result
            if result:
                print("✅ PASSED")
            else:
                print("❌ FAILED")
                all_passed = False
        except Exception as e:
            print(f"❌ ERROR: {e}")
            results[test_name] = False
            all_passed = False

    print()
    print("=" * 60)
    print("SUMMARY OF FIXES APPLIED:")
    print("=" * 60)
    print(
        """
1. CORS Configuration (server/main.py):
   - Added port 5179 to allowed origins
   - Configured proper CORS headers

2. OPTIONS Handler (server/main.py):
   - Added explicit OPTIONS handler for /auth/verify
   - Returns proper CORS preflight response

3. Socket.IO Mounting (server/main.py):
   - Properly mounted Socket.IO at /socket.io/
   - Using socketio_app instead of app for uvicorn

4. Token Verification Fix (server/main.py line 2450):
   - Fixed import: from .auth import JWTManager
   - Using JWTManager.verify_token() instead of direct import

5. Socket.IO CORS (server/socketio_server.py):
   - Ensured port 5179 is in Socket.IO allowed origins
   - Configured proper Socket.IO path
"""
    )

    print("=" * 60)
    if all_passed:
        print("✅ ALL TESTS PASSED - Integration Fixed!")
    else:
        print("⚠️  Some tests failed - Review needed")
    print("=" * 60)

    # Save results to file
    results_file = "/Volumes/G-DRIVE ArmorATD/Development/Clients/ToolBoxAI-Solutions/fixes/terminal1_test_results.json"
    with open(results_file, "w") as f:
        json.dump(
            {
                "timestamp": datetime.now().isoformat(),
                "all_passed": all_passed,
                "results": results,
            },
            f,
            indent=2,
        )
    print(f"\nResults saved to: {results_file}")

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
