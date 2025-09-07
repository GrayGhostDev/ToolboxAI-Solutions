#!/usr/bin/env python3
"""
Full End-to-End Integration Test for ToolboxAI Roblox Environment
Tests all components working together in a realistic scenario
"""

import asyncio
import json
import time
from typing import Dict, Any
import aiohttp
import websockets
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Service endpoints
FASTAPI_URL = "http://127.0.0.1:8008"
FLASK_URL = "http://127.0.0.1:5001"
DASHBOARD_BACKEND_URL = "http://127.0.0.1:8001"
DASHBOARD_FRONTEND_URL = "http://127.0.0.1:5176"
MCP_WEBSOCKET_URL = "ws://127.0.0.1:9876"

class IntegrationTester:
    """Comprehensive integration test suite"""
    
    def __init__(self):
        self.results = {
            "services": {},
            "tests": {},
            "errors": [],
            "performance": {}
        }
    
    async def test_service_health(self) -> Dict[str, bool]:
        """Test if all services are healthy"""
        services = {
            "FastAPI Backend": f"{FASTAPI_URL}/health",
            "Flask Bridge": f"{FLASK_URL}/health",
            "Dashboard Backend": f"{DASHBOARD_BACKEND_URL}/health",
            "Dashboard Frontend": DASHBOARD_FRONTEND_URL
        }
        
        async with aiohttp.ClientSession() as session:
            for name, url in services.items():
                try:
                    start = time.time()
                    async with session.get(url, timeout=5) as resp:
                        elapsed = (time.time() - start) * 1000
                        if resp.status == 200:
                            self.results["services"][name] = {
                                "status": "healthy",
                                "response_time_ms": elapsed
                            }
                            logger.info(f"✅ {name}: Healthy ({elapsed:.1f}ms)")
                        else:
                            self.results["services"][name] = {
                                "status": "error",
                                "code": resp.status
                            }
                            logger.error(f"❌ {name}: Error {resp.status}")
                except Exception as e:
                    self.results["services"][name] = {
                        "status": "offline",
                        "error": str(e)
                    }
                    logger.error(f"❌ {name}: Offline - {e}")
        
        return self.results["services"]
    
    async def test_content_generation_flow(self):
        """Test the complete content generation flow"""
        logger.info("\n📝 Testing Content Generation Flow...")
        
        # Step 1: Generate content via FastAPI
        async with aiohttp.ClientSession() as session:
            content_request = {
                "subject": "Mathematics",
                "grade_level": 5,
                "learning_objectives": ["Fractions", "Decimals"],
                "environment_type": "classroom",
                "include_quiz": True
            }
            
            try:
                async with session.post(
                    f"{FASTAPI_URL}/generate_content",
                    json=content_request,
                    timeout=30
                ) as resp:
                    if resp.status == 200:
                        result = await resp.json()
                        self.results["tests"]["content_generation"] = {
                            "status": "success",
                            "data": result
                        }
                        logger.info("✅ Content generation successful")
                        return result
                    else:
                        error = await resp.text()
                        self.results["tests"]["content_generation"] = {
                            "status": "failed",
                            "error": error
                        }
                        logger.error(f"❌ Content generation failed: {error}")
            except Exception as e:
                self.results["tests"]["content_generation"] = {
                    "status": "error",
                    "error": str(e)
                }
                logger.error(f"❌ Content generation error: {e}")
    
    async def test_roblox_bridge_flow(self):
        """Test Flask bridge for Roblox communication"""
        logger.info("\n🌉 Testing Roblox Bridge Flow...")
        
        async with aiohttp.ClientSession() as session:
            # Test plugin registration with required version field
            plugin_data = {
                "port": 64989,
                "studio_id": "test-studio-123",
                "version": "1.0.0"  # Added required version field
            }
            
            try:
                async with session.post(
                    f"{FLASK_URL}/register_plugin",
                    json=plugin_data,
                    timeout=5
                ) as resp:
                    if resp.status == 200:
                        result = await resp.json()
                        self.results["tests"]["roblox_bridge"] = {
                            "status": "success",
                            "plugin_registered": True,
                            "plugin_id": result.get("plugin_id")
                        }
                        logger.info(f"✅ Roblox bridge operational - Plugin ID: {result.get('plugin_id')}")
                    else:
                        self.results["tests"]["roblox_bridge"] = {
                            "status": "failed",
                            "code": resp.status
                        }
                        logger.error(f"❌ Roblox bridge failed: {resp.status}")
            except Exception as e:
                self.results["tests"]["roblox_bridge"] = {
                    "status": "error",
                    "error": str(e)
                }
                logger.error(f"❌ Roblox bridge error: {e}")
    
    async def test_websocket_connections(self):
        """Test WebSocket connections"""
        logger.info("\n🔌 Testing WebSocket Connections...")
        
        # Test FastAPI WebSocket
        try:
            async with websockets.connect(f"ws://127.0.0.1:8008/ws") as ws:
                # Send ping
                await ws.send(json.dumps({"type": "ping"}))
                # Wait for pong
                response = await asyncio.wait_for(ws.recv(), timeout=5)
                data = json.loads(response)
                
                if data.get("type") == "pong" or "echo" in data:
                    self.results["tests"]["websocket"] = {
                        "status": "success",
                        "fastapi_ws": True
                    }
                    logger.info("✅ FastAPI WebSocket connected")
                else:
                    self.results["tests"]["websocket"] = {
                        "status": "partial",
                        "message": "Unexpected response"
                    }
                    
        except Exception as e:
            self.results["tests"]["websocket"] = {
                "status": "failed",
                "error": str(e)
            }
            logger.warning(f"⚠️ WebSocket connection issue: {e}")
    
    async def test_dashboard_integration(self):
        """Test Dashboard backend integration"""
        logger.info("\n📊 Testing Dashboard Integration...")
        
        async with aiohttp.ClientSession() as session:
            # Test registration endpoint
            user_data = {
                "email": f"test_{int(time.time())}@test.com",
                "username": f"testuser_{int(time.time())}",
                "password": "TestPass123!",
                "first_name": "Test",
                "last_name": "User",
                "role": "Teacher"
            }
            
            try:
                # Attempt registration
                async with session.post(
                    f"{DASHBOARD_BACKEND_URL}/api/v1/auth/register",
                    json=user_data,
                    timeout=10
                ) as resp:
                    if resp.status in [200, 201]:
                        result = await resp.json()
                        self.results["tests"]["dashboard"] = {
                            "status": "success",
                            "auth_working": True,
                            "token": bool(result.get("access_token"))
                        }
                        logger.info("✅ Dashboard authentication working")
                    elif resp.status == 400:
                        # User might already exist, try login
                        self.results["tests"]["dashboard"] = {
                            "status": "partial",
                            "message": "Registration endpoint working"
                        }
                        logger.info("⚠️ Dashboard registration working (user exists)")
                    else:
                        self.results["tests"]["dashboard"] = {
                            "status": "error",
                            "code": resp.status
                        }
                        logger.error(f"❌ Dashboard auth failed: {resp.status}")
            except Exception as e:
                self.results["tests"]["dashboard"] = {
                    "status": "error",
                    "error": str(e)
                }
                logger.error(f"❌ Dashboard integration error: {e}")
    
    async def test_cross_service_communication(self):
        """Test communication between services"""
        logger.info("\n🔄 Testing Cross-Service Communication...")
        
        async with aiohttp.ClientSession() as session:
            # Test Flask calling FastAPI
            try:
                async with session.get(
                    f"{FLASK_URL}/health",
                    timeout=5
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        fastapi_check = data.get("checks", {}).get("fastapi", {})
                        
                        if fastapi_check.get("healthy"):
                            self.results["tests"]["cross_service"] = {
                                "status": "success",
                                "flask_to_fastapi": True
                            }
                            logger.info("✅ Cross-service communication working")
                        else:
                            self.results["tests"]["cross_service"] = {
                                "status": "partial",
                                "message": "Flask running but FastAPI check failed"
                            }
                            logger.warning("⚠️ Cross-service partially working")
            except Exception as e:
                self.results["tests"]["cross_service"] = {
                    "status": "error",
                    "error": str(e)
                }
                logger.error(f"❌ Cross-service error: {e}")
    
    async def run_all_tests(self):
        """Run all integration tests"""
        logger.info("=" * 60)
        logger.info("🚀 FULL END-TO-END INTEGRATION TEST")
        logger.info("=" * 60)
        
        # Test service health
        await self.test_service_health()
        
        # Test individual flows
        await self.test_content_generation_flow()
        await self.test_roblox_bridge_flow()
        await self.test_websocket_connections()
        await self.test_dashboard_integration()
        await self.test_cross_service_communication()
        
        # Calculate summary
        total_tests = len(self.results["tests"])
        successful = sum(1 for t in self.results["tests"].values() 
                        if t.get("status") == "success")
        partial = sum(1 for t in self.results["tests"].values() 
                     if t.get("status") == "partial")
        
        # Print summary
        logger.info("\n" + "=" * 60)
        logger.info("📈 INTEGRATION TEST SUMMARY")
        logger.info("=" * 60)
        
        # Service Status
        logger.info("\n🔧 Service Status:")
        for name, status in self.results["services"].items():
            if status.get("status") == "healthy":
                logger.info(f"  ✅ {name}: {status['status']} ({status.get('response_time_ms', 0):.1f}ms)")
            else:
                logger.info(f"  ❌ {name}: {status.get('status', 'unknown')}")
        
        # Test Results
        logger.info(f"\n📊 Test Results: {successful}/{total_tests} successful")
        for name, result in self.results["tests"].items():
            status = result.get("status", "unknown")
            icon = "✅" if status == "success" else "⚠️" if status == "partial" else "❌"
            logger.info(f"  {icon} {name}: {status}")
        
        # Overall Status
        success_rate = (successful / total_tests * 100) if total_tests > 0 else 0
        logger.info(f"\n🎯 Overall Success Rate: {success_rate:.1f}%")
        
        if success_rate >= 80:
            logger.info("✅ System integration is OPERATIONAL")
        elif success_rate >= 60:
            logger.info("⚠️ System integration is PARTIALLY OPERATIONAL")
        else:
            logger.info("❌ System integration has CRITICAL ISSUES")
        
        return self.results

async def main():
    """Main test runner"""
    tester = IntegrationTester()
    results = await tester.run_all_tests()
    
    # Save results to file
    with open("integration_test_results.json", "w") as f:
        json.dump(results, f, indent=2, default=str)
    
    logger.info("\n📁 Results saved to integration_test_results.json")

if __name__ == "__main__":
    asyncio.run(main())