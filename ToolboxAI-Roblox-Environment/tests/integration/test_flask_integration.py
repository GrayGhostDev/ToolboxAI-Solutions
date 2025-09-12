#!/usr/bin/env python3
"""
Flask Bridge Integration Test Suite
Terminal 3 - Roblox Integration Testing
"""

import json
import time
import requests
from datetime import datetime
from typing import Dict, Any, List

# Configuration
FLASK_URL = "http://127.0.0.1:5001"
FASTAPI_URL = "http://127.0.0.1:8008"
DASHBOARD_URL = "http://127.0.0.1:5179"

# Test data
TEST_PLUGIN_ID = f"test_plugin_{int(time.time())}"
TEST_STUDIO_ID = f"studio_{int(time.time())}"
TEST_PORT = 64989

def print_result(test_name: str, result: bool, details: str = ""):
    """Print test result with formatting"""
    status = "✅ PASS" if result else "❌ FAIL"
    print(f"\n{status} - {test_name}")
    if details:
        print(f"  Details: {details}")

def test_health_endpoint():
    """Test the health endpoint"""
    try:
        response = requests.get(f"{FLASK_URL}/health")
        data = response.json()
        success = (
            response.status_code == 200 and
            data.get("status") == "healthy" and
            data.get("checks", {}).get("fastapi") == True
        )
        print_result("Health Check", success, f"Status: {data.get('status')}, FastAPI: {data.get('checks', {}).get('fastapi')}")
        return success
    except Exception as e:
        print_result("Health Check", False, str(e))
        return False

def test_plugin_registration():
    """Test plugin registration"""
    try:
        payload = {
            "plugin_id": TEST_PLUGIN_ID,
            "studio_id": TEST_STUDIO_ID,
            "port": TEST_PORT,
            "version": "1.0.0",
            "capabilities": ["content_generation", "quiz", "terrain", "script"]
        }
        response = requests.post(f"{FLASK_URL}/register_plugin", json=payload)
        data = response.json()
        success = response.status_code == 200 and data.get("success") == True
        print_result("Plugin Registration", success, f"Plugin ID: {TEST_PLUGIN_ID}")
        return success
    except Exception as e:
        print_result("Plugin Registration", False, str(e))
        return False

def test_content_generation():
    """Test content generation through Flask bridge"""
    try:
        payload = {
            "type": "quiz",
            "subject": "Math",
            "grade": 5,
            "topic": "Fractions",
            "num_questions": 5
        }
        response = requests.post(f"{FLASK_URL}/plugin/content/generate", json=payload)
        data = response.json()
        success = response.status_code == 200 and "content" in data
        print_result("Content Generation", success, f"Generated {data.get('type', 'unknown')} content")
        return success, data
    except Exception as e:
        print_result("Content Generation", False, str(e))
        return False, {}

def test_terrain_generation():
    """Test terrain generation"""
    try:
        payload = {
            "type": "terrain",
            "environment": "forest",
            "size": "medium",
            "features": ["trees", "rocks", "water"]
        }
        response = requests.post(f"{FLASK_URL}/generate_terrain", json=payload)
        data = response.json()
        success = response.status_code == 200 and "content" in data
        print_result("Terrain Generation", success, f"Environment: {payload['environment']}")
        return success, data
    except Exception as e:
        print_result("Terrain Generation", False, str(e))
        return False, {}

def test_script_generation():
    """Test Lua script generation"""
    try:
        # Use the script endpoint to get pre-made scripts
        response = requests.get(f"{FLASK_URL}/script/quiz_ui")
        data = response.json()
        success = response.status_code == 200 and ("content" in data or "script" in data)
        print_result("Script Generation", success, f"Script type: quiz_ui")
        return success, data
    except Exception as e:
        print_result("Script Generation", False, str(e))
        return False, {}

def test_plugin_polling():
    """Test plugin polling for updates"""
    try:
        # First register the plugin
        register_payload = {
            "plugin_id": f"poll_test_{int(time.time())}",
            "studio_id": f"studio_poll_{int(time.time())}",
            "port": 64990,
            "version": "1.0.0"
        }
        requests.post(f"{FLASK_URL}/register_plugin", json=register_payload)
        
        # Now poll for messages
        poll_payload = {
            "plugin_id": register_payload["plugin_id"],
            "studio_id": register_payload["studio_id"]
        }
        response = requests.post(f"{FLASK_URL}/plugin/poll-messages", json=poll_payload)
        data = response.json()
        success = response.status_code == 200
        print_result("Plugin Polling", success, f"Updates available: {data.get('has_updates', False)}")
        return success
    except Exception as e:
        print_result("Plugin Polling", False, str(e))
        return False

def test_error_handling():
    """Test error handling for invalid requests"""
    test_cases = [
        {
            "name": "Invalid content type",
            "endpoint": "/plugin/content/generate",
            "payload": {"type": "invalid_type"},
            "expected_error": True
        },
        {
            "name": "Missing required fields",
            "endpoint": "/register_plugin",
            "payload": {"plugin_id": "test"},
            "expected_error": True
        },
        {
            "name": "Invalid JSON",
            "endpoint": "/plugin/content/generate",
            "payload": "not_json",
            "expected_error": True
        }
    ]
    
    all_passed = True
    for test in test_cases:
        try:
            if test["payload"] == "not_json":
                response = requests.post(f"{FLASK_URL}{test['endpoint']}", data=test["payload"])
            else:
                response = requests.post(f"{FLASK_URL}{test['endpoint']}", json=test["payload"])
            
            success = response.status_code >= 400 if test["expected_error"] else response.status_code == 200
            print_result(f"Error Handling - {test['name']}", success, f"Status code: {response.status_code}")
            all_passed = all_passed and success
        except Exception as e:
            print_result(f"Error Handling - {test['name']}", False, str(e))
            all_passed = False
    
    return all_passed

def test_network_resilience():
    """Test network failure scenarios"""
    print("\n🔄 Testing Network Resilience...")
    
    # Test timeout handling
    try:
        response = requests.get(f"{FLASK_URL}/health", timeout=0.001)
        print_result("Timeout Handling", False, "Should have timed out")
        return False
    except requests.Timeout:
        print_result("Timeout Handling", True, "Properly handled timeout")
        return True
    except Exception as e:
        print_result("Timeout Handling", False, str(e))
        return False

def test_integration_with_fastapi():
    """Test Flask bridge integration with FastAPI backend"""
    try:
        # Check if FastAPI is accessible
        fastapi_response = requests.get(f"{FASTAPI_URL}/health")
        if fastapi_response.status_code != 200:
            print_result("FastAPI Integration", False, "FastAPI not accessible")
            return False
        
        # Test content generation through Flask that calls FastAPI
        payload = {
            "type": "quiz",
            "subject": "Science",
            "grade": 7,
            "topic": "Solar System"
        }
        response = requests.post(f"{FLASK_URL}/plugin/content/generate", json=payload)
        success = response.status_code == 200
        print_result("FastAPI Integration", success, "Content generation through Flask->FastAPI chain")
        return success
    except Exception as e:
        print_result("FastAPI Integration", False, str(e))
        return False

def generate_test_report(results: Dict[str, Any]):
    """Generate a test report"""
    report = {
        "timestamp": datetime.now().isoformat(),
        "terminal": "terminal3",
        "test_suite": "Flask Bridge Integration",
        "results": results,
        "summary": {
            "total": len(results),
            "passed": sum(1 for v in results.values() if v),
            "failed": sum(1 for v in results.values() if not v)
        }
    }
    
    # Save report
    with open("/Volumes/G-DRIVE ArmorATD/Development/Clients/ToolBoxAI-Solutions/flask_integration_test_report.json", "w") as f:
        json.dump(report, f, indent=2)
    
    return report

def main():
    """Run all integration tests"""
    print("=" * 60)
    print("Flask Bridge Integration Test Suite")
    print(f"Terminal 3 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    results = {}
    
    # Basic health check
    results["health"] = test_health_endpoint()
    
    # Plugin registration
    results["registration"] = test_plugin_registration()
    
    # Content generation tests
    quiz_success, quiz_data = test_content_generation()
    results["quiz_generation"] = quiz_success
    
    terrain_success, terrain_data = test_terrain_generation()
    results["terrain_generation"] = terrain_success
    
    script_success, script_data = test_script_generation()
    results["script_generation"] = script_success
    
    # Polling mechanism
    results["polling"] = test_plugin_polling()
    
    # Error handling
    results["error_handling"] = test_error_handling()
    
    # Network resilience
    results["network_resilience"] = test_network_resilience()
    
    # Integration with FastAPI
    results["fastapi_integration"] = test_integration_with_fastapi()
    
    # Generate report
    report = generate_test_report(results)
    
    print("\n" + "=" * 60)
    print("Test Summary:")
    print(f"Total Tests: {report['summary']['total']}")
    print(f"Passed: {report['summary']['passed']}")
    print(f"Failed: {report['summary']['failed']}")
    print(f"Success Rate: {(report['summary']['passed'] / report['summary']['total'] * 100):.1f}%")
    print("=" * 60)
    
    # Report any API mismatches found
    if quiz_data and not quiz_data.get("questions"):
        print("\n⚠️  API Mismatch: Quiz generation not returning 'questions' field")
    if terrain_data and not terrain_data.get("regions"):
        print("⚠️  API Mismatch: Terrain generation not returning 'regions' field")
    if script_data and not script_data.get("source"):
        print("⚠️  API Mismatch: Script generation not returning 'source' field")
    
    print(f"\n📄 Full report saved to: flask_integration_test_report.json")
    
    return report['summary']['passed'] == report['summary']['total']

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)