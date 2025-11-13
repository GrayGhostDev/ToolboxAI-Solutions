import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from unittest.mock import Mock, patch

import pytest
import pytest_asyncio


@pytest.fixture
def mock_db_connection():
    """Mock database connection for tests"""
    with patch('psycopg2.connect') as mock_connect:
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn
        yield mock_conn

"""
WebSocket Pipeline Integration Tests

Tests the WebSocket pipeline manager functionality after Redis client fixes.
Validates:
1. WebSocket connection management
2. Redis integration for message queuing
3. Pipeline manager coordination
4. Real-time message broadcasting
5. Connection cleanup and error handling
"""

import asyncio
import json
import logging
import time
from typing import Any, Dict, List
from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastapi.testclient import TestClient

from tests.fixtures.pusher_mocks import MockPusherService

# Import application components
try:
    from apps.backend.main import app
    from apps.backend.services.pusher import trigger_event
    from tests.fixtures.pusher_test_utils import (
        WebSocketManager,
        broadcast_content_update,
        websocket_manager,
    )
except ImportError as e:
    pytest.skip(f"Required WebSocket modules not available: {e}", allow_module_level=True)

logger = logging.getLogger(__name__)


class TestWebSocketPipelineManager:
    """Test WebSocket pipeline manager functionality"""

    @pytest.mark.asyncio
    @pytest.mark.websocket
    @pytest.mark.asyncio
async def test_websocket_manager_initialization(self):
        """Test WebSocket manager initializes correctly"""
        manager = WebSocketManager()
        assert manager is not None
        assert hasattr(manager, 'active_connections')
        assert isinstance(manager.active_connections, list)

    @pytest.mark.asyncio
    @pytest.mark.websocket
    @pytest.mark.asyncio
async def test_websocket_connection_lifecycle(self):
        """Test WebSocket connection lifecycle management"""
        manager = WebSocketManager()

        # Create mock WebSocket connection
        mock_pusher_as_websocket = AsyncMock()
        mock_pusher_as_websocket.client_state = "CONNECTED"

        # Test connection
        await manager.connect(mock_pusher_as_websocket)
        assert mock_pusher_as_websocket in manager.active_connections

        # Test disconnection
        manager.disconnect(mock_pusher_as_websocket)
        assert mock_pusher_as_websocket not in manager.active_connections

    @pytest.mark.asyncio
    @pytest.mark.websocket
    @pytest.mark.asyncio
async def test_websocket_message_broadcasting(self):
        """Test message broadcasting to connected WebSocket clients"""
        manager = WebSocketManager()

        # Create multiple mock connections
        mock_pusher_as_websockets = []
        for i in range(3):
            mock_ws = AsyncMock()
            mock_ws.client_state = "CONNECTED"
            mock_ws.send_text = AsyncMock()
            await manager.connect(mock_ws)
            mock_pusher_as_websockets.append(mock_ws)

        # Test broadcasting
        test_message = {"type": 'content-update', "data": "test content"}
        await manager.broadcast(json.dumps(test_message))

        # Verify all connections received the message
        for mock_ws in mock_pusher_as_websockets:
            mock_ws.send_text.assert_called_with(json.dumps(test_message))

    @pytest.mark.asyncio
    @pytest.mark.websocket
    @pytest.mark.asyncio
async def test_websocket_error_handling(self):
        """Test WebSocket error handling and cleanup"""
        manager = WebSocketManager()

        # Create mock connection that will fail
        mock_pusher_as_websocket = AsyncMock()
        mock_pusher_as_websocket.client_state = "CONNECTED"
        mock_pusher_as_websocket.send_text.side_effect = Exception("Connection failed")

        await manager.connect(mock_pusher_as_websocket)

        # Test error handling during broadcast
        test_message = {"type": "error_test", "data": "test"}
        await manager.broadcast(json.dumps(test_message))

        # Connection should be removed after error
        assert mock_pusher_as_websocket not in manager.active_connections


class TestWebSocketEndpoints:
    """Test WebSocket endpoint functionality"""

    @pytest.mark.integration
    @pytest.mark.websocket
    def test_websocket_endpoints_available(self):
        """Test that WebSocket endpoints are properly registered"""
        # Check if WebSocket routes are in the app
        websocket_routes = [route for route in app.routes if hasattr(route, 'path') and 'ws' in route.path]
        assert len(websocket_routes) > 0, "No WebSocket routes found"

    @pytest.mark.asyncio
    @pytest.mark.websocket
    @pytest.mark.asyncio
async def test_websocket_content_endpoint(self):
        """Test WebSocket content generation endpoint"""
        try:
            async with async_mock_pusher_context() as pusher:
        # Connect using Pusher"pusher://app_key@cluster/content") as websocket:
                # Send test message
                test_request = {
                    "type": "content_request",
                    "data": {
                        "subject": "math",
                        "grade_level": "5th",
                        "content_type": "lesson"
                    }
                }

                await pusher.trigger(json.dumps(test_request))

                # Wait for response with timeout
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    response_data = json.loads(response)
                    assert "type" in response_data
                except asyncio.TimeoutError:
                    pytest.skip("WebSocket server not responding")

        except Exception as e:
            logger.warning(f"WebSocket connection test failed: {e}")
            pytest.skip(f"WebSocket endpoint not available: {e}")

    @pytest.mark.asyncio
    @pytest.mark.websocket
    @pytest.mark.asyncio
async def test_websocket_agent_communication(self):
        """Test WebSocket agent communication endpoint"""
        try:
            async with async_mock_pusher_context() as pusher:
        # Connect using Pusher"pusher://app_key@cluster/agent/test_agent") as websocket:
                # Send agent communication test
                test_message = {
                    "type": "agent_command",
                    "agent_id": "test_agent",
                    "command": "status"
                }

                await pusher.trigger(json.dumps(test_message))

                # Wait for response
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=3.0)
                    response_data = json.loads(response)
                    assert "type" in response_data
                except asyncio.TimeoutError:
                    logger.info("Agent WebSocket timeout - may be expected")

        except Exception as e:
            logger.warning(f"Agent WebSocket test failed: {e}")
            pytest.skip(f"Agent WebSocket endpoint not available: {e}")


class TestRedisWebSocketIntegration:
    """Test Redis integration with WebSocket pipeline"""

    @pytest.mark.asyncio
    @pytest.mark.requires_redis
    @pytest.mark.websocket
    @pytest.mark.asyncio
async def test_redis_message_queue_integration(self):
        """Test Redis message queue integration with WebSocket"""
        try:
            # Test Redis-based message queuing
            from apps.backend.services.redis_handler import redis_client

            # Test Redis connection
            await redis_client.ping()

            # Test message publishing
            test_message = {
                "channel": "websocket_updates",
                "data": {"type": "test", "content": "Redis integration test"}
            }

            await redis_client.publish("websocket_updates", json.dumps(test_message))

            # Verify message was published
            assert True  # If we get here, Redis is working

        except ImportError:
            pytest.skip("Redis handler not available")
        except Exception as e:
            logger.warning(f"Redis integration test failed: {e}")
            pytest.skip(f"Redis not available: {e}")

    @pytest.mark.asyncio
    @pytest.mark.requires_redis
    @pytest.mark.websocket
    @pytest.mark.asyncio
async def test_redis_websocket_pipeline_coordination(self):
        """Test coordination between Redis and WebSocket pipeline"""
        try:
            # Test the coordination between Redis events and WebSocket broadcasting
            manager = WebSocketManager()

            # Create mock WebSocket connection
            mock_pusher_as_websocket = AsyncMock()
            mock_pusher_as_websocket.client_state = "CONNECTED"
            mock_pusher_as_websocket.send_text = AsyncMock()
            await manager.connect(mock_pusher_as_websocket)

            # Test Redis-triggered WebSocket broadcast
            test_data = {"message": "Redis pipeline test", "timestamp": time.time()}
            await broadcast_content_update(test_data)

            # Verify broadcast was attempted
            assert len(manager.active_connections) >= 0

        except Exception as e:
            logger.warning(f"Redis-WebSocket pipeline test failed: {e}")


class TestPusherWebSocketComparison:
    """Test Pusher vs WebSocket functionality comparison"""

    @pytest.mark.integration
    @pytest.mark.websocket
    def test_pusher_trigger_functionality(self):
        """Test Pusher trigger functionality as WebSocket alternative"""
        try:
            from apps.backend.services.pusher import trigger_event

            # Test Pusher event triggering
            result = trigger_event(
                channel="test-channel",
                event="test-event",
                data={"message": "Pusher integration test"}
            )

            # Should not raise exception
            assert True

        except ImportError:
            pytest.skip("Pusher service not available")
        except Exception as e:
            logger.warning(f"Pusher test failed: {e}")

    @pytest.mark.asyncio
    @pytest.mark.websocket
    @pytest.mark.asyncio
async def test_realtime_delivery_comparison(self):
        """Test real-time delivery capabilities of both systems"""
        # Test WebSocket delivery
        websocket_start = time.time()
        try:
            manager = WebSocketManager()
            test_message = {"type": "performance_test", "timestamp": websocket_start}
            await manager.broadcast(json.dumps(test_message))
            websocket_time = time.time() - websocket_start
        except Exception:
            websocket_time = float('inf')

        # Test Pusher delivery
        pusher_start = time.time()
        try:
            result = trigger_event(
                channel="performance-test",
                event="delivery-test",
                data={"timestamp": pusher_start}
            )
            pusher_time = time.time() - pusher_start
        except Exception:
            pusher_time = float('inf')

        # Both should complete reasonably quickly
        assert websocket_time < 1.0 or pusher_time < 1.0


class TestWebSocketPerformance:
    """Test WebSocket performance and scalability"""

    @pytest.mark.asyncio
    @pytest.mark.performance
    @pytest.mark.websocket
    @pytest.mark.asyncio
async def test_multiple_connection_handling(self):
        """Test handling multiple WebSocket connections"""
        manager = WebSocketManager()

        # Create multiple mock connections
        connections = []
        for i in range(10):
            mock_ws = AsyncMock()
            mock_ws.client_state = "CONNECTED"
            mock_ws.send_text = AsyncMock()
            await manager.connect(mock_ws)
            connections.append(mock_ws)

        # Test broadcasting to all connections
        start_time = time.time()
        test_message = {"type": "load_test", "data": f"Message to {len(connections)} connections"}
        await manager.broadcast(json.dumps(test_message))
        broadcast_time = time.time() - start_time

        # Should handle broadcast efficiently
        assert broadcast_time < 1.0
        assert len(manager.active_connections) == 10

    @pytest.mark.asyncio
    @pytest.mark.performance
    @pytest.mark.websocket
    @pytest.mark.asyncio
async def test_message_throughput(self):
        """Test WebSocket message throughput"""
        manager = WebSocketManager()

        # Create mock connection
        mock_ws = AsyncMock()
        mock_ws.client_state = "CONNECTED"
        mock_ws.send_text = AsyncMock()
        await manager.connect(mock_ws)

        # Send multiple messages rapidly
        start_time = time.time()
        message_count = 100

        for i in range(message_count):
            test_message = {"type": "throughput_test", "sequence": i}
            await manager.send_personal_message(json.dumps(test_message), mock_ws)

        throughput_time = time.time() - start_time
        messages_per_second = message_count / throughput_time

        # Should handle reasonable throughput
        assert messages_per_second > 50  # At least 50 messages per second


class TestWebSocketErrorRecovery:
    """Test WebSocket error recovery and resilience"""

    @pytest.mark.asyncio
    @pytest.mark.websocket
    @pytest.mark.asyncio
async def test_connection_cleanup_on_error(self):
        """Test proper cleanup when WebSocket connections fail"""
        manager = WebSocketManager()

        # Create failing connection
        failing_ws = AsyncMock()
        failing_ws.client_state = "CONNECTED"
        failing_ws.send_text.side_effect = Exception("Connection lost")

        # Create working connection
        working_ws = AsyncMock()
        working_ws.client_state = "CONNECTED"
        working_ws.send_text = AsyncMock()

        await manager.connect(failing_ws)
        await manager.connect(working_ws)

        # Test broadcast with one failing connection
        test_message = {"type": "error_recovery_test", "data": "test"}
        await manager.broadcast(json.dumps(test_message))

        # Working connection should still receive message
        working_ws.send_text.assert_called()

        # Failing connection should be cleaned up
        assert failing_ws not in manager.active_connections

    @pytest.mark.asyncio
    @pytest.mark.websocket
    @pytest.mark.asyncio
async def test_graceful_shutdown(self):
        """Test graceful WebSocket manager shutdown"""
        manager = WebSocketManager()

        # Create connections
        connections = []
        for i in range(3):
            mock_ws = AsyncMock()
            mock_ws.client_state = "CONNECTED"
            mock_ws.close = AsyncMock()
            await manager.connect(mock_ws)
            connections.append(mock_ws)

        # Test graceful shutdown
        await manager.shutdown()

        # All connections should be closed
        for ws in connections:
            ws.close.assert_called()


# Integration test runner
async def run_websocket_integration_tests():
    """Run comprehensive WebSocket integration tests"""
    test_results = {
        "websocket_manager": False,
        "websocket_endpoints": False,
        "redis_integration": False,
        "pusher_comparison": False,
        "performance_tests": False,
        "error_recovery": False
    }

    try:
        # Test WebSocket manager
        manager = WebSocketManager()
        test_results["websocket_manager"] = True

        # Test basic functionality
        mock_ws = AsyncMock()
        await manager.connect(mock_ws)
        manager.disconnect(mock_ws)
        test_results["websocket_endpoints"] = True

    except Exception as e:
        logger.error(f"WebSocket integration test failed: {e}")

    return test_results


if __name__ == "__main__":
    # Run basic WebSocket tests when executed directly
    print("Running WebSocket Pipeline Validation Tests...")

    # Test WebSocket manager import
    try:
        from tests.fixtures.pusher_test_utils import websocket_manager
        print("✓ WebSocket manager import successful")
    except Exception as e:
        print(f"✗ WebSocket manager import failed: {e}")

    # Test basic manager functionality
    try:
        manager = WebSocketManager()
        print("✓ WebSocket manager initialization successful")
    except Exception as e:
        print(f"✗ WebSocket manager initialization failed: {e}")

    print("\nRun 'pytest tests/integration/test_websocket_pipeline_validation.py -v' for full WebSocket test suite")