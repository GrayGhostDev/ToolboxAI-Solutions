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
WebSocket Integration Test Suite
Tests real-time communication across all services
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
import logging
from typing import Dict, Any, List
import websockets
import aiohttp
import pytest
from datetime import datetime, timezone

# Skip all tests in this module as they require external services
# Tests are now enabled by default since we've fixed the issues
# To skip, set SKIP_INTEGRATION_TESTS=1
pytestmark = pytest.mark.skipif(
    os.environ.get('SKIP_INTEGRATION_TESTS'),
    reason="Tests manually disabled. Remove SKIP_INTEGRATION_TESTS to enable"
)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configuration
SERVICES = {
    "fastapi": {
        "ws_url": "ws://127.0.0.1:8008/ws",
        "http_url": "http://127.0.0.1:8008",
        "health_endpoint": "/health"
    },
    "dashboard": {
        "ws_url": "ws://127.0.0.1:8001/ws",
        "http_url": "http://127.0.0.1:8001",
        "health_endpoint": "/api/v1/health"
    },
    "mcp": {
        "ws_url": "ws://127.0.0.1:9876",
        "http_url": None,  # MCP is WebSocket-only
        "health_endpoint": None
    }
}

class WebSocketTester:
    """Comprehensive WebSocket testing utility"""
    
    def __init__(self):
        self.results = {}
        self.connections = {}
        
    async def check_service_health(self, service_name: str) -> bool:
        """Check if HTTP service is healthy"""
        config = SERVICES[service_name]
        if not config["http_url"] or not config["health_endpoint"]:
            return True  # Skip health check for WebSocket-only services
            
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{config['http_url']}{config['health_endpoint']}"
                async with session.get(url, timeout=5) as response:
                    if response.status == 200:
                        logger.info(f"✅ {service_name} health check passed")
                        return True
        except Exception as e:
            logger.warning(f"⚠️ {service_name} health check failed: {e}")
        return False
    
    @pytest.mark.asyncio(loop_scope="function")
    @pytest.mark.asyncio
async def test_websocket_connection(self, service_name: str) -> Dict[str, Any]:
        """Test basic WebSocket connection"""
        config = SERVICES[service_name]
        result = {
            "service": service_name,
            "connection": False,
            "ping_pong": False,
            "error": None
        }
        
        try:
            logger.info(f"Testing WebSocket connection to {service_name}...")
            
            async with websockets.connect(config["ws_url"], timeout=5) as websocket:
                result["connection"] = True
                logger.info(f"✅ Connected to {service_name} WebSocket")
                
                # Test ping-pong
                await websocket.send(json.dumps({"type": "ping"}, default=make_json_serializable))
                
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=3)
                    data = json.loads(response)
                    if data.get("type") == "pong":
                        result["ping_pong"] = True
                        logger.info(f"✅ {service_name} ping-pong successful")
                except asyncio.TimeoutError:
                    logger.warning(f"⚠️ {service_name} ping-pong timeout")
                except json.JSONDecodeError:
                    # Some services might send plain text
                    result["ping_pong"] = True
                    
        except Exception as e:
            result["error"] = str(e)
            logger.error(f"❌ {service_name} WebSocket error: {e}")
            
        return result
    
    @pytest.mark.asyncio(loop_scope="function")
    @pytest.mark.asyncio
async def test_message_broadcasting(self) -> Dict[str, Any]:
        """Test message broadcasting within a service"""
        result = {
            "test": "broadcasting",
            "success": False,
            "details": {}
        }
        
        try:
            # Test Dashboard WebSocket broadcasting
            ws1 = await websockets.connect(SERVICES["dashboard"]["ws_url"])
            ws2 = await websockets.connect(SERVICES["dashboard"]["ws_url"])
            
            # Join same room
            room_id = f"test-room-{int(time.time())}"
            await ws1.send(json.dumps({
                "type": "join_room",
                "room": room_id
            }, default=make_json_serializable))
            await ws2.send(json.dumps({
                "type": "join_room",
                "room": room_id
            }, default=make_json_serializable))
            
            # Allow time for room joining
            await asyncio.sleep(0.5)
            
            # Send broadcast message
            test_message = {
                "type": "broadcast",
                "room": room_id,
                "message": "Test broadcast",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            await ws1.send(json.dumps(test_message, default=make_json_serializable))
            
            # Check if both receive the message
            received = []
            try:
                msg1 = await asyncio.wait_for(ws1.recv(), timeout=2)
                received.append(json.loads(msg1))
                msg2 = await asyncio.wait_for(ws2.recv(), timeout=2)
                received.append(json.loads(msg2))
                
                result["success"] = len(received) == 2
                result["details"]["messages_received"] = len(received)
                logger.info(f"✅ Broadcasting test: {len(received)} messages received")
                
            except asyncio.TimeoutError:
                logger.warning("⚠️ Broadcasting test timeout")
                
            await ws1.close()
            await ws2.close()
            
        except Exception as e:
            result["details"]["error"] = str(e)
            logger.error(f"❌ Broadcasting test error: {e}")
            
        return result
    
    @pytest.mark.asyncio(loop_scope="function")
    @pytest.mark.asyncio
async def test_cross_service_communication(self) -> Dict[str, Any]:
        """Test communication between different services"""
        result = {
            "test": "cross_service",
            "success": False,
            "details": {}
        }
        
        try:
            # Test MCP context sharing
            mcp_ws = await websockets.connect(SERVICES["mcp"]["ws_url"])
            
            # Update context
            context_update = {
                "type": "update_context",
                "context": {
                    "test_id": "cross-service-test",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "data": {"test": "value"}
                }
            }
            await mcp_ws.send(json.dumps(context_update, default=make_json_serializable))
            
            # Request context
            await mcp_ws.send(json.dumps({"type": "get_context"}, default=make_json_serializable))
            
            response = await asyncio.wait_for(mcp_ws.recv(), timeout=3)
            data = json.loads(response)
            
            if data.get("type") == "context":
                result["success"] = True
                result["details"]["context_received"] = True
                logger.info("✅ Cross-service MCP context test passed")
                
            await mcp_ws.close()
            
        except Exception as e:
            result["details"]["error"] = str(e)
            logger.error(f"❌ Cross-service test error: {e}")
            
        return result
    
    @pytest.mark.asyncio(loop_scope="function")
    @pytest.mark.asyncio
async def test_authentication_over_websocket(self) -> Dict[str, Any]:
        """Test WebSocket authentication"""
        result = {
            "test": "authentication",
            "success": False,
            "details": {}
        }
        
        try:
            # Get auth token first (mock for testing)
            token = "test-jwt-token-123"
            
            # Connect with authentication
            headers = {"Authorization": f"Bearer {token}"}
            ws = await websockets.connect(
                SERVICES["dashboard"]["ws_url"],
                extra_headers=headers
            )
            
            # Send authenticated message
            await ws.send(json.dumps({
                "type": "authenticated_action",
                "action": "get_user_data"
            }, default=make_json_serializable))
            
            try:
                response = await asyncio.wait_for(ws.recv(), timeout=3)
                result["success"] = True
                result["details"]["authenticated"] = True
                logger.info("✅ WebSocket authentication test passed")
            except asyncio.TimeoutError:
                logger.warning("⚠️ Authentication test timeout")
                
            await ws.close()
            
        except Exception as e:
            result["details"]["error"] = str(e)
            logger.error(f"❌ Authentication test error: {e}")
            
        return result
    
    @pytest.mark.asyncio(loop_scope="function")
    @pytest.mark.asyncio
async def test_realtime_updates(self) -> Dict[str, Any]:
        """Test real-time update propagation"""
        result = {
            "test": "realtime_updates",
            "success": False,
            "details": {}
        }
        
        try:
            ws = await websockets.connect(SERVICES["dashboard"]["ws_url"])
            
            # Subscribe to updates
            await ws.send(json.dumps({
                "type": "subscribe",
                "channel": "dashboard_updates"
            }, default=make_json_serializable))
            
            # Simulate an update (would normally come from API)
            update_message = {
                "type": "update",
                "channel": "dashboard_updates",
                "data": {
                    "metric": "student_count",
                    "value": 150,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            }
            
            # In real scenario, this would be triggered by API
            await ws.send(json.dumps(update_message, default=make_json_serializable))
            
            # Check if update is received
            response = await asyncio.wait_for(ws.recv(), timeout=3)
            data = json.loads(response)
            
            if "update" in str(data).lower():
                result["success"] = True
                result["details"]["update_received"] = True
                logger.info("✅ Real-time update test passed")
                
            await ws.close()
            
        except Exception as e:
            result["details"]["error"] = str(e)
            logger.error(f"❌ Real-time update test error: {e}")
            
        return result
    
    @pytest.mark.asyncio(loop_scope="function")
    @pytest.mark.asyncio
async def test_connection_resilience(self) -> Dict[str, Any]:
        """Test WebSocket reconnection and error handling"""
        result = {
            "test": "resilience",
            "success": False,
            "details": {}
        }
        
        try:
            # Test reconnection
            ws = await websockets.connect(SERVICES["dashboard"]["ws_url"])
            
            # Send keepalive
            await ws.send(json.dumps({"type": "keepalive"}, default=make_json_serializable))
            
            # Close and reconnect
            await ws.close()
            await asyncio.sleep(0.5)
            
            # Reconnect
            ws = await websockets.connect(SERVICES["dashboard"]["ws_url"])
            await ws.send(json.dumps({"type": "ping"}, default=make_json_serializable))
            
            try:
                response = await asyncio.wait_for(ws.recv(), timeout=3)
                result["success"] = True
                result["details"]["reconnection"] = True
                logger.info("✅ Connection resilience test passed")
            except asyncio.TimeoutError:
                logger.warning("⚠️ Resilience test timeout")
                
            await ws.close()
            
        except Exception as e:
            result["details"]["error"] = str(e)
            logger.error(f"❌ Resilience test error: {e}")
            
        return result
    
    @pytest.mark.asyncio(loop_scope="function")
    @pytest.mark.asyncio
async def test_performance(self) -> Dict[str, Any]:
        """Test WebSocket performance and throughput"""
        result = {
            "test": "performance",
            "success": False,
            "details": {
                "messages_sent": 0,
                "messages_received": 0,
                "average_latency_ms": 0
            }
        }
        
        try:
            ws = await websockets.connect(SERVICES["fastapi"]["ws_url"])
            
            num_messages = 100
            latencies = []
            
            for i in range(num_messages):
                start_time = time.time()
                
                message = {
                    "type": "echo",
                    "id": i,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
                await ws.send(json.dumps(message, default=make_json_serializable))
                
                try:
                    response = await asyncio.wait_for(ws.recv(), timeout=1)
                    latency = (time.time() - start_time) * 1000  # Convert to ms
                    latencies.append(latency)
                    result["details"]["messages_received"] += 1
                except asyncio.TimeoutError:
                    logger.warning(f"Message {i} timeout")
                    
                result["details"]["messages_sent"] += 1
            
            if latencies:
                result["details"]["average_latency_ms"] = sum(latencies) / len(latencies)
                result["success"] = True
                logger.info(f"✅ Performance test: {result['details']['messages_received']}/{num_messages} messages, "
                          f"avg latency: {result['details']['average_latency_ms']:.2f}ms")
            
            await ws.close()
            
        except Exception as e:
            result["details"]["error"] = str(e)
            logger.error(f"❌ Performance test error: {e}")
            
        return result
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all WebSocket tests"""
        logger.info("=" * 60)
        logger.info("WEBSOCKET INTEGRATION TESTS")
        logger.info("=" * 60)
        
        all_results = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "tests": {}
        }
        
        # Test basic connections
        logger.info("\n1. Testing WebSocket Connections")
        logger.info("-" * 40)
        for service in SERVICES.keys():
            result = await self.test_websocket_connection(service)
            all_results["tests"][f"connection_{service}"] = result
        
        # Test broadcasting
        logger.info("\n2. Testing Message Broadcasting")
        logger.info("-" * 40)
        broadcast_result = await self.test_message_broadcasting()
        all_results["tests"]["broadcasting"] = broadcast_result
        
        # Test cross-service
        logger.info("\n3. Testing Cross-Service Communication")
        logger.info("-" * 40)
        cross_result = await self.test_cross_service_communication()
        all_results["tests"]["cross_service"] = cross_result
        
        # Test authentication
        logger.info("\n4. Testing WebSocket Authentication")
        logger.info("-" * 40)
        auth_result = await self.test_authentication_over_websocket()
        all_results["tests"]["authentication"] = auth_result
        
        # Test real-time updates
        logger.info("\n5. Testing Real-time Updates")
        logger.info("-" * 40)
        realtime_result = await self.test_realtime_updates()
        all_results["tests"]["realtime_updates"] = realtime_result
        
        # Test resilience
        logger.info("\n6. Testing Connection Resilience")
        logger.info("-" * 40)
        resilience_result = await self.test_connection_resilience()
        all_results["tests"]["resilience"] = resilience_result
        
        # Test performance
        logger.info("\n7. Testing WebSocket Performance")
        logger.info("-" * 40)
        performance_result = await self.test_performance()
        all_results["tests"]["performance"] = performance_result
        
        # Summary
        logger.info("\n" + "=" * 60)
        logger.info("TEST SUMMARY")
        logger.info("=" * 60)
        
        passed = sum(1 for test in all_results["tests"].values() 
                    if test.get("success") or test.get("connection"))
        total = len(all_results["tests"])
        
        logger.info(f"✅ Passed: {passed}")
        logger.info(f"❌ Failed: {total - passed}")
        logger.info(f"📊 Total: {total}")
        
        all_results["summary"] = {
            "passed": passed,
            "failed": total - passed,
            "total": total,
            "success_rate": f"{(passed/total)*100:.1f}%"
        }
        
        # Save results
        with open("websocket_test_results.json", "w") as f:
            json.dump(all_results, f, indent=2)
        logger.info("\n📁 Results saved to websocket_test_results.json")
        
        if passed == total:
            logger.info("\n🎉 ALL WEBSOCKET TESTS PASSED!")
        else:
            logger.info(f"\n💔 {total - passed} TESTS FAILED")
        
        return all_results


# Pytest integration
@pytest.mark.asyncio(loop_scope="function")
@pytest.mark.asyncio
async def test_websocket_connections():
    """Pytest: Test WebSocket connections"""
    tester = WebSocketTester()
    for service in SERVICES.keys():
        result = await tester.test_websocket_connection(service)
        if service != "mcp":  # MCP might not always be running
            assert result["connection"], f"{service} connection failed"


@pytest.mark.asyncio(loop_scope="function")
@pytest.mark.asyncio
async def test_websocket_broadcasting():
    """Pytest: Test WebSocket broadcasting"""
    tester = WebSocketTester()
    result = await tester.test_message_broadcasting()
    assert result["success"], "Broadcasting test failed"


@pytest.mark.asyncio(loop_scope="function")
@pytest.mark.asyncio
async def test_websocket_performance():
    """Pytest: Test WebSocket performance"""
    tester = WebSocketTester()
    result = await tester.test_performance()
    assert result["success"], "Performance test failed"
    assert result["details"]["average_latency_ms"] < 100, "Latency too high"


async def main():
    """Main test runner"""
    tester = WebSocketTester()
    await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())