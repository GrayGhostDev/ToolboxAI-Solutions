#!/usr/bin/env python3
"""
Flask Bridge Integration Test Suite
Tests Flask bridge server (port 5001) communication with FastAPI (port 8008)
"""

import asyncio
import json
import time
from datetime import datetime
import requests
import httpx
import pytest

# Skip all tests in this module as they require external services
pytestmark = pytest.mark.skip(reason="Integration tests require external services - run with --run-integration")


class FlaskBridgeIntegrationTest:
    """Test Flask bridge integration with FastAPI"""
    
    def __init__(self):
        self.flask_url = "http://127.0.0.1:5001"
        self.fastapi_url = "http://127.0.0.1:8008"
        self.test_results = []
        
    def test_health_endpoints(self):
        """Test both servers are healthy"""
        print("\n🔍 Testing Health Endpoints...")
        
        # Test Flask health
        try:
            response = requests.get(f"{self.flask_url}/health", timeout=5)
            flask_healthy = response.status_code == 200
            if flask_healthy:
                data = response.json()
                print(f"  ✅ Flask bridge healthy - Status: {data['status']}")
                print(f"     FastAPI connection: {'✅' if data['checks']['fastapi'] else '❌'}")
            else:
                print(f"  ❌ Flask bridge unhealthy - Status: {response.status_code}")
        except Exception as e:
            print(f"  ❌ Flask bridge error: {e}")
            flask_healthy = False
            
        # Test FastAPI health
        try:
            response = requests.get(f"{self.fastapi_url}/health", timeout=5)
            fastapi_healthy = response.status_code == 200
            if fastapi_healthy:
                data = response.json()
                print(f"  ✅ FastAPI healthy - Status: {data['status']}")
            else:
                print(f"  ❌ FastAPI unhealthy - Status: {response.status_code}")
        except Exception as e:
            print(f"  ❌ FastAPI error: {e}")
            fastapi_healthy = False
            
        self.test_results.append({
            "test": "health_endpoints",
            "flask": flask_healthy,
            "fastapi": fastapi_healthy,
            "success": flask_healthy and fastapi_healthy
        })
        
        return flask_healthy and fastapi_healthy
    
    def test_plugin_registration(self):
        """Test plugin registration through Flask bridge"""
        print("\n🔍 Testing Plugin Registration...")
        
        plugin_data = {
            "studio_id": "test-studio-123",
            "port": 64989,
            "version": "1.0.0"
        }
        
        try:
            response = requests.post(
                f"{self.flask_url}/register_plugin",
                json=plugin_data,
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                plugin_id = data.get("plugin_id")
                print(f"  ✅ Plugin registered successfully")
                print(f"     Plugin ID: {plugin_id}")
                
                # Test heartbeat
                heartbeat_response = requests.post(
                    f"{self.flask_url}/plugin/{plugin_id}/heartbeat",
                    timeout=5
                )
                
                if heartbeat_response.status_code == 200:
                    print(f"  ✅ Plugin heartbeat successful")
                else:
                    print(f"  ❌ Plugin heartbeat failed: {heartbeat_response.status_code}")
                
                self.test_results.append({
                    "test": "plugin_registration",
                    "success": True,
                    "plugin_id": plugin_id
                })
                return True
            else:
                print(f"  ❌ Plugin registration failed: {response.status_code}")
                self.test_results.append({
                    "test": "plugin_registration",
                    "success": False,
                    "error": response.text
                })
                return False
                
        except Exception as e:
            print(f"  ❌ Plugin registration error: {e}")
            self.test_results.append({
                "test": "plugin_registration",
                "success": False,
                "error": str(e)
            })
            return False
    
    def test_content_generation_bridge(self):
        """Test content generation through Flask bridge to FastAPI"""
        print("\n🔍 Testing Content Generation Bridge...")
        
        content_request = {
            "subject": "Science",
            "grade_level": 7,
            "learning_objectives": ["Solar System", "Planets"],
            "environment_type": "space_station",
            "include_quiz": True,
            "difficulty_level": "medium"
        }
        
        try:
            # Test through Flask bridge
            response = requests.post(
                f"{self.flask_url}/generate_simple_content",
                json=content_request,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    print(f"  ✅ Content generation through Flask bridge successful")
                    print(f"     Content ID: {data.get('content_id', 'N/A')}")
                    
                    # Check if agent integration is working
                    if "SPARC" in data.get("message", "") or "agent" in data.get("message", "").lower():
                        print(f"  ✅ Agent integration detected in response")
                    
                    self.test_results.append({
                        "test": "content_generation_bridge",
                        "success": True,
                        "content_id": data.get("content_id")
                    })
                    return True
                else:
                    print(f"  ⚠️  Content generation returned error: {data.get('message')}")
                    self.test_results.append({
                        "test": "content_generation_bridge",
                        "success": False,
                        "error": data.get("message")
                    })
                    return False
            else:
                print(f"  ❌ Content generation failed: {response.status_code}")
                self.test_results.append({
                    "test": "content_generation_bridge",
                    "success": False,
                    "status_code": response.status_code
                })
                return False
                
        except Exception as e:
            print(f"  ❌ Content generation error: {e}")
            self.test_results.append({
                "test": "content_generation_bridge",
                "success": False,
                "error": str(e)
            })
            return False
    
    def test_script_templates(self):
        """Test Lua script template delivery"""
        print("\n🔍 Testing Script Template Delivery...")
        
        script_types = ["quiz", "terrain", "ui"]
        success_count = 0
        
        for script_type in script_types:
            try:
                response = requests.get(
                    f"{self.flask_url}/script/{script_type}",
                    timeout=5
                )
                
                if response.status_code == 200:
                    print(f"  ✅ Script template '{script_type}' retrieved")
                    success_count += 1
                else:
                    print(f"  ❌ Script template '{script_type}' failed: {response.status_code}")
                    
            except Exception as e:
                print(f"  ❌ Script template '{script_type}' error: {e}")
        
        all_success = success_count == len(script_types)
        self.test_results.append({
            "test": "script_templates",
            "success": all_success,
            "retrieved": success_count,
            "total": len(script_types)
        })
        
        return all_success
    
    def test_cache_functionality(self):
        """Test Flask bridge cache functionality"""
        print("\n🔍 Testing Cache Functionality...")
        
        try:
            # Clear cache first
            response = requests.post(f"{self.flask_url}/cache/clear", timeout=5)
            if response.status_code == 200:
                print(f"  ✅ Cache cleared successfully")
            
            # Get status to check cache stats
            response = requests.get(f"{self.flask_url}/status", timeout=5)
            if response.status_code == 200:
                data = response.json()
                cache_stats = data.get("cache_stats", {})
                print(f"  ✅ Cache stats retrieved")
                print(f"     Cache size: {cache_stats.get('size', 0)}")
                print(f"     Hit rate: {cache_stats.get('hit_rate', 0):.2%}")
                
                self.test_results.append({
                    "test": "cache_functionality",
                    "success": True,
                    "cache_stats": cache_stats
                })
                return True
            else:
                print(f"  ❌ Failed to get cache stats: {response.status_code}")
                self.test_results.append({
                    "test": "cache_functionality",
                    "success": False
                })
                return False
                
        except Exception as e:
            print(f"  ❌ Cache functionality error: {e}")
            self.test_results.append({
                "test": "cache_functionality",
                "success": False,
                "error": str(e)
            })
            return False
    
    def test_agent_integration(self):
        """Test if agent systems are integrated in Flask bridge"""
        print("\n🔍 Testing Agent Integration...")
        
        try:
            # Check Flask status for agent integration
            response = requests.get(f"{self.flask_url}/status", timeout=5)
            if response.status_code == 200:
                data = response.json()
                
                # Check if SPARC, Swarm, or MCP are mentioned
                status_str = json.dumps(data)
                has_sparc = "sparc" in status_str.lower()
                has_swarm = "swarm" in status_str.lower()
                has_mcp = "mcp" in status_str.lower()
                
                if has_sparc or has_swarm or has_mcp:
                    print(f"  ✅ Agent systems detected in Flask bridge")
                    if has_sparc:
                        print(f"     ✅ SPARC framework integrated")
                    if has_swarm:
                        print(f"     ✅ Swarm controller integrated")
                    if has_mcp:
                        print(f"     ✅ MCP context manager integrated")
                else:
                    print(f"  ⚠️  Agent systems not detected (may be optional)")
                
                self.test_results.append({
                    "test": "agent_integration",
                    "success": True,
                    "sparc": has_sparc,
                    "swarm": has_swarm,
                    "mcp": has_mcp
                })
                return True
            else:
                print(f"  ❌ Failed to check agent integration: {response.status_code}")
                self.test_results.append({
                    "test": "agent_integration",
                    "success": False
                })
                return False
                
        except Exception as e:
            print(f"  ❌ Agent integration check error: {e}")
            self.test_results.append({
                "test": "agent_integration",
                "success": False,
                "error": str(e)
            })
            return False
    
    def run_all_tests(self):
        """Run all integration tests"""
        print("=" * 60)
        print("🚀 Flask Bridge Integration Test Suite")
        print("=" * 60)
        print(f"Flask Bridge: {self.flask_url}")
        print(f"FastAPI Backend: {self.fastapi_url}")
        print(f"Time: {datetime.now().isoformat()}")
        
        # Run tests
        self.test_health_endpoints()
        self.test_plugin_registration()
        self.test_content_generation_bridge()
        self.test_script_templates()
        self.test_cache_functionality()
        self.test_agent_integration()
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 Test Summary")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for r in self.test_results if r.get("success", False))
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {total_tests - passed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        print("\nDetailed Results:")
        for result in self.test_results:
            status = "✅" if result.get("success", False) else "❌"
            test_name = result.get("test", "unknown")
            print(f"  {status} {test_name}")
        
        return passed_tests == total_tests


def main():
    """Main test runner"""
    tester = FlaskBridgeIntegrationTest()
    success = tester.run_all_tests()
    return 0 if success else 1


if __name__ == "__main__":
    exit_code = main()
    exit(exit_code)