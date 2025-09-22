import pytest_asyncio

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
Full End-to-End Integration Test for ToolboxAI Roblox Environment
Tests all components working together in a realistic scenario
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
import time
from typing import Dict, Any, List
import aiohttp
from tests.fixtures.pusher_mocks import MockPusherService
import logging
import psycopg2
import redis
import socketio
import concurrent.futures
from datetime import datetime, timezone
import pytest

# Skip all tests in this module as they require external services
pytestmark = pytest.mark.skipif(
    not os.environ.get('RUN_INTEGRATION_TESTS'),
    reason="Integration tests disabled. Set RUN_INTEGRATION_TESTS=1 to enable"
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Service endpoints
FASTAPI_URL = "http://127.0.0.1:8008"
FLASK_URL = "http://127.0.0.1:5001"
DASHBOARD_BACKEND_URL = "http://127.0.0.1:8001"
DASHBOARD_FRONTEND_URL = "http://127.0.0.1:5176"
MCP_WEBSOCKET_URL = "ws://127.0.0.1:9876"
SOCKETIO_URL = "http://127.0.0.1:8008"

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'user': 'eduplatform',
    'password': 'eduplatform2024',
    'database': 'educational_platform_dev'
}

# Test credentials
TEST_USER = {
    'username': 'john_teacher',
    'password': 'Teacher123!'
}

class IntegrationTester:
    """Comprehensive integration test suite"""
    
    def __init__(self):
        self.results = {
            "services": {},
            "tests": {},
            "errors": [],
            "performance": {}
        }
        self.auth_token = None
    
    @pytest.mark.asyncio(loop_scope="function")
    @pytest.mark.asyncio
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
    
    @pytest.mark.asyncio(loop_scope="function")
    @pytest.mark.asyncio
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
    
    @pytest.mark.asyncio(loop_scope="function")
    @pytest.mark.asyncio
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
    
    @pytest.mark.asyncio(loop_scope="function")
    @pytest.mark.asyncio
async def test_websocket_connections(self):
        """Test WebSocket connections"""
        logger.info("\n🔌 Testing WebSocket Connections...")
        
        # Test FastAPI WebSocket
        try:
            async with async_mock_pusher_context() as pusher:
        # Connect using Pusherf"pusher://app_key@cluster") as ws:
                # Send ping
                await pusher.trigger(json.dumps({"type": "ping"}, default=make_json_serializable))
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
    
    @pytest.mark.asyncio(loop_scope="function")
    @pytest.mark.asyncio
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
    
    @pytest.mark.asyncio(loop_scope="function")
    @pytest.mark.asyncio
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
    
    @pytest.mark.asyncio(loop_scope="function")
    @pytest.mark.asyncio
async def test_database_connections(self):
        """Test database connectivity"""
        logger.info("\n🗄️ Testing Database Connections...")
        
        # Test PostgreSQL
        try:
            conn = psycopg2.connect(**DB_CONFIG)
            cursor = conn.cursor()
            cursor.execute("SELECT version();")
            version = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM users;")
            user_count = cursor.fetchone()[0]
            cursor.close()
            conn.close()
            
            self.results["tests"]["postgresql"] = {
                "status": "success",
                "user_count": user_count
            }
            logger.info(f"✅ PostgreSQL connected ({user_count} users)")
        except Exception as e:
            self.results["tests"]["postgresql"] = {
                "status": "error",
                "error": str(e)
            }
            logger.error(f"❌ PostgreSQL error: {e}")
        
        # Test Redis
        try:
            r = redis.Redis(host='localhost', port=6379, db=0)
            r.ping()
            self.results["tests"]["redis"] = {"status": "success"}
            logger.info("✅ Redis connected")
        except Exception as e:
            self.results["tests"]["redis"] = {
                "status": "error",
                "error": str(e)
            }
            logger.error(f"❌ Redis error: {e}")
    
    @pytest.mark.asyncio(loop_scope="function")
    @pytest.mark.asyncio
async def test_authentication_flow(self):
        """Test authentication with real credentials"""
        logger.info("\n🔐 Testing Authentication Flow...")
        
        async with aiohttp.ClientSession() as session:
            try:
                # Login with test credentials
                async with session.post(
                    f"{FASTAPI_URL}/auth/login",
                    json={
                        "username": TEST_USER['username'],
                        "password": TEST_USER['password']
                    },
                    timeout=10
                ) as resp:
                    if resp.status == 200:
                        auth_data = await resp.json()
                        self.auth_token = auth_data.get('access_token')
                        
                        self.results["tests"]["authentication"] = {
                            "status": "success",
                            "token_received": bool(self.auth_token)
                        }
                        logger.info("✅ Authentication successful")
                        
                        # Test token verification
                        headers = {"Authorization": f"Bearer {self.auth_token}"}
                        async with session.get(
                            f"{FASTAPI_URL}/auth/me",
                            headers=headers,
                            timeout=5
                        ) as verify_resp:
                            if verify_resp.status == 200:
                                user_data = await verify_resp.json()
                                logger.info(f"✅ Token verified for user: {user_data.get('username')}")
                    else:
                        self.results["tests"]["authentication"] = {
                            "status": "failed",
                            "code": resp.status
                        }
                        logger.error(f"❌ Authentication failed: {resp.status}")
            except Exception as e:
                self.results["tests"]["authentication"] = {
                    "status": "error",
                    "error": str(e)
                }
                logger.error(f"❌ Authentication error: {e}")
    
    @pytest.mark.asyncio(loop_scope="function")
    @pytest.mark.asyncio
async def test_socketio_connection(self):
        """Test Socket.io connection"""
        logger.info("\n🔌 Testing Socket.io Connection...")
        
        try:
            # Create Socket.io client
            sio_client = socketio.AsyncClient()
            
            connected = False
            @sio_client.event
            async def connect():
                nonlocal connected
                connected = True
            
            # Connect to server
            await sio_client.connect(SOCKETIO_URL, wait_timeout=5)
            await asyncio.sleep(1)
            
            if connected:
                # Test ping/pong
                await sio_client.emit('ping', {'timestamp': datetime.now(timezone.utc).isoformat()})
                await asyncio.sleep(1)
                
                self.results["tests"]["socketio"] = {
                    "status": "success",
                    "connected": True
                }
                logger.info("✅ Socket.io connected and responsive")
            else:
                self.results["tests"]["socketio"] = {
                    "status": "failed",
                    "connected": False
                }
                logger.error("❌ Socket.io connection failed")
            
            await sio_client.disconnect()
            
        except Exception as e:
            self.results["tests"]["socketio"] = {
                "status": "error",
                "error": str(e)
            }
            logger.error(f"❌ Socket.io error: {e}")
    
    @pytest.mark.asyncio(loop_scope="function")
    @pytest.mark.asyncio
async def test_agent_systems(self):
        """Test agent system health"""
        logger.info("\n🤖 Testing Agent Systems...")
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(
                    f"{FASTAPI_URL}/agents/health",
                    timeout=5
                ) as resp:
                    if resp.status == 200:
                        health = await resp.json()
                        agents = health.get('agents', {})
                        
                        healthy_count = sum(1 for a in agents.values() if a.get('healthy'))
                        total_count = len(agents)
                        
                        self.results["tests"]["agents"] = {
                            "status": "success" if healthy_count == total_count else "partial",
                            "healthy": f"{healthy_count}/{total_count}"
                        }
                        logger.info(f"✅ Agent systems: {healthy_count}/{total_count} healthy")
                    else:
                        self.results["tests"]["agents"] = {
                            "status": "failed",
                            "code": resp.status
                        }
                        logger.error(f"❌ Agent health check failed: {resp.status}")
            except Exception as e:
                self.results["tests"]["agents"] = {
                    "status": "error",
                    "error": str(e)
                }
                logger.error(f"❌ Agent systems error: {e}")
    
    @pytest.mark.asyncio(loop_scope="function")
    @pytest.mark.asyncio
async def test_api_endpoints(self):
        """Test various API endpoints with authentication"""
        logger.info("\n📡 Testing API Endpoints...")
        
        if not self.auth_token:
            logger.warning("⚠️ Skipping API tests - no auth token")
            return
        
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        endpoints = [
            ("/dashboard/overview/Teacher", "Dashboard"),
            ("/classes/", "Classes"),
            ("/lessons/", "Lessons"),
            ("/assessments/", "Assessments"),
            ("/analytics/progress", "Analytics"),
            ("/users/profile", "User Profile"),
        ]
        
        async with aiohttp.ClientSession() as session:
            successful = 0
            for endpoint, name in endpoints:
                try:
                    async with session.get(
                        f"{FASTAPI_URL}{endpoint}",
                        headers=headers,
                        timeout=5
                    ) as resp:
                        if resp.status in [200, 201]:
                            successful += 1
                            logger.info(f"  ✅ {name}: OK")
                        else:
                            logger.warning(f"  ⚠️ {name}: {resp.status}")
                except Exception as e:
                    logger.error(f"  ❌ {name}: {str(e)[:50]}")
            
            self.results["tests"]["api_endpoints"] = {
                "status": "success" if successful == len(endpoints) else "partial",
                "passed": f"{successful}/{len(endpoints)}"
            }
    
    @pytest.mark.asyncio(loop_scope="function")
    @pytest.mark.asyncio
async def test_concurrent_load(self):
        """Test system under concurrent load"""
        logger.info("\n⚡ Testing Concurrent Load...")
        
        async def make_request(session, index):
            try:
                async with session.get(f"{FASTAPI_URL}/health", timeout=5) as resp:
                    return resp.status == 200
            except:
                return False
        
        async with aiohttp.ClientSession() as session:
            tasks = [make_request(session, i) for i in range(20)]
            results = await asyncio.gather(*tasks)
            
            success_rate = sum(results) / len(results)
            self.results["tests"]["concurrent_load"] = {
                "status": "success" if success_rate > 0.9 else "failed",
                "success_rate": f"{success_rate:.0%}"
            }
            logger.info(f"✅ Concurrent load: {success_rate:.0%} success rate")
    
    async def run_all_tests(self):
        """Run all integration tests"""
        logger.info("=" * 60)
        logger.info("🚀 FULL END-TO-END INTEGRATION TEST")
        logger.info("=" * 60)
        
        # Test service health
        await self.test_service_health()
        
        # Test database connections
        await self.test_database_connections()
        
        # Test authentication
        await self.test_authentication_flow()
        
        # Test individual flows
        await self.test_content_generation_flow()
        await self.test_roblox_bridge_flow()
        await self.test_websocket_connections()
        await self.test_socketio_connection()
        await self.test_dashboard_integration()
        await self.test_cross_service_communication()
        
        # Test additional components
        await self.test_agent_systems()
        await self.test_api_endpoints()
        await self.test_concurrent_load()
        
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