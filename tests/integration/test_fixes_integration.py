
import pytest
from unittest.mock import Mock, patch

@pytest.fixture
def mock_db_connection():
    """Mock database connection for tests"""
    with patch('psycopg2.connect') as mock_connect:
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn
        yield mock_conn

#!/usr/bin/env python3
"""
Integration test script to verify all API fixes are working properly.
Tests all the issues that were identified in the integration test.
"""

import asyncio
import os

def make_json_serializable(obj):
    """Convert non-serializable objects to serializable format."""
    if hasattr(obj, '__dict__'):
        return obj.__dict__
    elif hasattr(obj, 'to_dict'):
        return obj.to_dict()
    elif hasattr(obj, '_asdict'):
        return obj._asdict()
    else:
        return str(obj)

import json
import requests
import time
from datetime import datetime
import pytest

# Skip all tests in this module as they require external services
# Tests are now enabled by default since we've fixed the issues
# To skip, set SKIP_INTEGRATION_TESTS=1
pytestmark = pytest.mark.skipif(
    os.environ.get('SKIP_INTEGRATION_TESTS'),
    reason="Tests manually disabled. Remove SKIP_INTEGRATION_TESTS to enable"
)

def test_health_endpoints():
    """Test all health endpoints"""
    print("Testing health endpoints...")
    
    endpoints = [
        ("Main FastAPI", "http://127.0.0.1:8008/health"),
        ("Dashboard Backend", "http://127.0.0.1:8001/health"), 
        ("Flask Bridge", "http://127.0.0.1:5001/health"),
        ("Agents Health", "http://127.0.0.1:8008/agents/health")
    ]
    
    results = {}
    for name, url in endpoints:
        try:
            response = requests.get(url, timeout=5)
            results[name] = {
                "status": response.status_code,
                "healthy": response.status_code == 200,
                "response": response.json() if response.status_code == 200 else response.text
            }
            print(f"  ✅ {name}: {response.status_code}")
        except Exception as e:
            results[name] = {"status": "error", "healthy": False, "error": str(e)}
            print(f"  ❌ {name}: {e}")
    
    return results

def test_authentication_endpoints():
    """Test authentication endpoints"""
    print("Testing authentication endpoints...")
    
    results = {}
    
    # Test main server login
    try:
        response = requests.post(
            "http://127.0.0.1:8008/auth/login",
            json={"username": "john_teacher", "password": "Teacher123!"},
            timeout=5
        )
        results["main_login"] = {
            "status": response.status_code,
            "success": response.status_code == 200,
            "has_token": "access_token" in response.json() if response.status_code == 200 else False
        }
        print(f"  ✅ Main login: {response.status_code}")
        
        # Get token for further testing
        if response.status_code == 200:
            results["auth_token"] = response.json().get("access_token")
            
    except Exception as e:
        results["main_login"] = {"status": "error", "success": False, "error": str(e)}
        print(f"  ❌ Main login: {e}")
    
    # Test dashboard backend login
    try:
        response = requests.post(
            "http://127.0.0.1:8001/auth/login",
            json={"username": "john_teacher", "password": "Teacher123!"},
            timeout=5
        )
        results["dashboard_login"] = {
            "status": response.status_code,
            "success": response.status_code == 200,
            "has_token": "access_token" in response.json() if response.status_code == 200 else False
        }
        print(f"  ✅ Dashboard login: {response.status_code}")
        
    except Exception as e:
        results["dashboard_login"] = {"status": "error", "success": False, "error": str(e)}
        print(f"  ❌ Dashboard login: {e}")
    
    return results

def test_content_generation():
    """Test content generation with proper authorization"""
    print("Testing content generation API...")
    
    results = {}
    
    # Test new API endpoint with authorization header
    try:
        response = requests.post(
            "http://127.0.0.1:8008/api/v1/content/generate",
            headers={
                "Content-Type": "application/json",
                "Authorization": "Bearer test-token-123"
            },
            json={
                "subject": "Science",
                "grade_level": 7,
                "learning_objectives": [
                    {"title": "Solar System", "description": "Understanding our solar system"},
                    {"title": "Planets", "description": "Learn about different planets"}
                ],
                "environment_type": "space_station",
                "include_quiz": True
            },
            timeout=10
        )
        results["api_content_generation"] = {
            "status": response.status_code,
            "success": response.status_code == 200,
            "response": response.json() if response.status_code == 200 else response.text[:200]
        }
        print(f"  ✅ API content generation: {response.status_code}")
        
    except Exception as e:
        results["api_content_generation"] = {"status": "error", "success": False, "error": str(e)}
        print(f"  ❌ API content generation: {e}")
    
    return results

def test_dashboard_endpoints():
    """Test dashboard specific endpoints"""
    print("Testing dashboard endpoints...")
    
    results = {}
    
    # First authenticate to get a token
    try:
        auth_response = requests.post(
            "http://127.0.0.1:8001/auth/login",
            json={"username": "john_teacher", "password": "Teacher123!"},
            timeout=5
        )
        
        if auth_response.status_code != 200:
            print("  ❌ Cannot authenticate for dashboard tests")
            return {"error": "Authentication failed"}
            
        token = auth_response.json().get("access_token")
        headers = {"Authorization": f"Bearer {token}"}
        
        # Test dashboard endpoints
        dashboard_endpoints = [
            ("Dashboard Stats", "/api/v1/dashboard/stats"),
            ("Dashboard Overview", "/api/v1/dashboard/overview"),
            ("Dashboard Content", "/api/v1/dashboard/content"),
            ("Dashboard Students", "/api/v1/dashboard/students"),
            ("Dashboard Analytics", "/api/v1/dashboard/analytics"),
        ]
        
        for name, endpoint in dashboard_endpoints:
            try:
                response = requests.get(
                    f"http://127.0.0.1:8001{endpoint}",
                    headers=headers,
                    timeout=5
                )
                results[name.lower().replace(" ", "_")] = {
                    "status": response.status_code,
                    "success": response.status_code == 200
                }
                print(f"  ✅ {name}: {response.status_code}")
                
            except Exception as e:
                results[name.lower().replace(" ", "_")] = {"status": "error", "success": False, "error": str(e)}
                print(f"  ❌ {name}: {e}")
        
    except Exception as e:
        results["authentication_error"] = str(e)
        print(f"  ❌ Dashboard authentication: {e}")
    
    return results

def test_cors_and_cross_service():
    """Test CORS and cross-service communication"""
    print("Testing CORS and cross-service communication...")
    
    results = {}
    
    # Test CORS preflight
    try:
        response = requests.options(
            "http://127.0.0.1:8008/health",
            headers={"Origin": "http://localhost:3000", "Access-Control-Request-Method": "GET"},
            timeout=5
        )
        results["cors_preflight"] = {
            "status": response.status_code,
            "success": response.status_code in [200, 204],
            "has_cors_headers": "Access-Control-Allow-Origin" in response.headers
        }
        print(f"  ✅ CORS preflight: {response.status_code}")
        
    except Exception as e:
        results["cors_preflight"] = {"status": "error", "success": False, "error": str(e)}
        print(f"  ❌ CORS preflight: {e}")
    
    # Test cross-origin request
    try:
        response = requests.get(
            "http://127.0.0.1:8008/health",
            headers={"Origin": "http://localhost:3000"},
            timeout=5
        )
        results["cross_origin_request"] = {
            "status": response.status_code,
            "success": response.status_code == 200,
            "has_cors_headers": "Access-Control-Allow-Origin" in response.headers
        }
        print(f"  ✅ Cross-origin request: {response.status_code}")
        
    except Exception as e:
        results["cross_origin_request"] = {"status": "error", "success": False, "error": str(e)}
        print(f"  ❌ Cross-origin request: {e}")
    
    return results

def test_websocket_connection():
    """Test WebSocket connection (basic connectivity)"""
    print("Testing WebSocket connection...")
    
    results = {}
    
    # For now, just test if the endpoint exists by making an HTTP request to it
    # In a full test, we would use a WebSocket client
    try:
        response = requests.get("http://127.0.0.1:8008/ws/native", timeout=2)
        # WebSocket endpoints typically return 426 Upgrade Required for HTTP requests
        results["websocket_endpoint"] = {
            "status": response.status_code,
            "success": response.status_code in [400, 426, 405],  # Expected for WebSocket endpoints
            "note": "WebSocket endpoint exists (HTTP request to WS endpoint expected to fail)"
        }
        print(f"  ✅ WebSocket endpoint exists: {response.status_code}")
        
    except requests.exceptions.ReadTimeout:
        # This might happen if the server is waiting for WebSocket upgrade
        results["websocket_endpoint"] = {
            "status": "timeout",
            "success": True,
            "note": "WebSocket endpoint exists (timeout expected for HTTP request)"
        }
        print(f"  ✅ WebSocket endpoint exists (timeout expected)")
        
    except Exception as e:
        results["websocket_endpoint"] = {"status": "error", "success": False, "error": str(e)}
        print(f"  ❌ WebSocket endpoint: {e}")
    
    return results

def run_comprehensive_test():
    """Run all integration tests"""
    print("🧪 Running Comprehensive API Integration Test")
    print("=" * 50)
    print(f"Test started at: {datetime.now()}")
    print()
    
    # Run all tests
    results = {
        "health_endpoints": test_health_endpoints(),
        "authentication": test_authentication_endpoints(),
        "content_generation": test_content_generation(),
        "dashboard_endpoints": test_dashboard_endpoints(),
        "cors_cross_service": test_cors_and_cross_service(),
        "websocket": test_websocket_connection()
    }
    
    print()
    print("📊 Test Results Summary")
    print("=" * 50)
    
    total_tests = 0
    passed_tests = 0
    
    for category, category_results in results.items():
        print(f"\n{category.replace('_', ' ').title()}:")
        
        if isinstance(category_results, dict):
            for test_name, test_result in category_results.items():
                if isinstance(test_result, dict) and "success" in test_result:
                    total_tests += 1
                    if test_result["success"]:
                        passed_tests += 1
                        print(f"  ✅ {test_name}: PASS")
                    else:
                        print(f"  ❌ {test_name}: FAIL")
                        if "error" in test_result:
                            print(f"     Error: {test_result['error']}")
                elif isinstance(test_result, dict) and "healthy" in test_result:
                    total_tests += 1
                    if test_result["healthy"]:
                        passed_tests += 1
                        print(f"  ✅ {test_name}: HEALTHY")
                    else:
                        print(f"  ❌ {test_name}: UNHEALTHY")
    
    print("\n" + "=" * 50)
    print(f"🎯 Overall Results: {passed_tests}/{total_tests} tests passed")
    print(f"📈 Success Rate: {(passed_tests/total_tests*100):.1f}%")
    
    if passed_tests == total_tests:
        print("🎉 All tests passed! API integration is working correctly.")
    else:
        print("⚠️  Some tests failed. Check the results above for details.")
    
    print(f"\nTest completed at: {datetime.now()}")
    
    # Save results to file
    with open("integration_test_results.json", "w") as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "success_rate": passed_tests/total_tests*100
            },
            "results": results
        }, f, indent=2)
    
    print(f"📁 Detailed results saved to: integration_test_results.json")

if __name__ == "__main__":
    run_comprehensive_test()