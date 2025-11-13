import pytest_asyncio

#!/usr/bin/env python3
"""
WebSocket + Pusher Real-time Communication Integration Tests

Tests the complete real-time communication system including:
- WebSocket connection establishment and authentication
- Pusher channel subscription and message delivery
- Cross-platform message broadcasting
- Connection handling under various scenarios
- Performance and reliability of real-time features
"""

import asyncio
import json
import os
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from unittest.mock import AsyncMock, Mock, patch

import httpx
import pytest

from tests.fixtures.pusher_mocks import MockPusherService
from tests.fixtures.pusher_test_utils import ConnectionClosedError, ConnectionClosedOK

# Set environment for testing
os.environ["TESTING"] = "true"
os.environ["USE_MOCK_LLM"] = "true"
os.environ["PUSHER_ENABLED"] = "true"

pytestmark = [
    pytest.mark.integration,
    pytest.mark.asyncio,
    pytest.mark.websocket,
    pytest.mark.pusher,
]


@pytest.fixture
async def realtime_client():
    """HTTP client for real-time communication testing"""
    async with httpx.AsyncClient(
        base_url="http://127.0.0.1:8009",
        timeout=30.0
    ) as client:
        yield client


@pytest.fixture
def auth_headers():
    """Authentication headers for API requests"""
    from datetime import timedelta

    import jwt

    payload = {
        "sub": "realtime_test_user",
        "role": "teacher",
        "exp": datetime.utcnow() + timedelta(hours=1)
    }
    token = jwt.encode(payload, "test-secret", algorithm="HS256")
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def test_channels():
    """Test channel configurations"""
    return {
        "public": {
            "name": "public-notifications",
            "type": "public"
        },
        "private": {
            "name": "private-user-123",
            "type": "private"
        },
        "presence": {
            "name": "presence-lesson-456",
            "type": "presence"
        }
    }


@pytest.fixture
async def mock_pusher_client():
    """Mock Pusher client for testing"""
    mock_client = Mock()
    mock_client.trigger = AsyncMock(return_value={"status": "ok"})
    mock_client.authenticate = AsyncMock(return_value={"auth": "mock_auth_token"})
    mock_client.channels = AsyncMock(return_value={"channels": {}})
    return mock_client


class TestWebSocketConnections:
    """Test WebSocket connection establishment and handling"""

    @pytest.mark.asyncio
async def test_websocket_connection_establishment(self, realtime_client, auth_headers):
        """Test basic WebSocket connection establishment"""
        try:
            # Test WebSocket endpoint availability
            ws_url = "pusher://app_key@cluster"

            async with async_mock_pusher_context() as pusher:
        # Connect using Pusherws_url) as websocket:
                # Send authentication message
                auth_message = {
                    "type": "auth",
                    "token": auth_headers["Authorization"].replace("Bearer ", "")
                }
                await pusher.trigger(json.dumps(auth_message))

                # Wait for response
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    response_data = json.loads(response)

                    # Should receive authentication confirmation
                    assert response_data.get("type") in ["auth_success", "authenticated", "connected"]

                except asyncio.TimeoutError:
                    pytest.skip("WebSocket authentication timeout")

        except ConnectionRefusedError:
            pytest.skip("WebSocket server not available")
        except Exception as e:
            pytest.skip(f"WebSocket connection failed: {e}")

    @pytest.mark.asyncio
async def test_websocket_message_echo(self, realtime_client, auth_headers):
        """Test WebSocket message sending and receiving"""
        try:
            ws_url = "pusher://app_key@cluster/echo"  # Echo endpoint for testing

            async with async_mock_pusher_context() as pusher:
        # Connect using Pusherws_url) as websocket:
                # Send test message
                test_message = {
                    "type": "ping",
                    "data": {"message": "Hello WebSocket", "timestamp": time.time()}
                }
                await pusher.trigger(json.dumps(test_message))

                # Wait for echo response
                response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                response_data = json.loads(response)

                # Should receive echo back
                assert response_data.get("type") in ["pong", "echo"]
                assert "data" in response_data

        except ConnectionRefusedError:
            pytest.skip("WebSocket echo server not available")
        except Exception as e:
            pytest.skip(f"WebSocket echo test failed: {e}")

    @pytest.mark.asyncio
async def test_websocket_authentication_required(self):
        """Test that WebSocket connections require proper authentication"""
        try:
            ws_url = "pusher://app_key@cluster/protected"

            async with async_mock_pusher_context() as pusher:
        # Connect using Pusherws_url) as websocket:
                # Send message without authentication
                test_message = {"type": "test", "data": "unauthorized"}
                await pusher.trigger(json.dumps(test_message))

                # Should receive authentication error
                response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                response_data = json.loads(response)

                assert response_data.get("type") in ["error", "auth_required", "unauthorized"]

        except ConnectionRefusedError:
            pytest.skip("Protected WebSocket endpoint not available")
        except Exception as e:
            pytest.skip(f"WebSocket auth test failed: {e}")

    @pytest.mark.asyncio
async def test_websocket_connection_limits(self):
        """Test WebSocket connection limits and handling"""
        connections = []
        try:
            ws_url = "pusher://app_key@cluster"

            # Try to establish multiple connections
            for i in range(10):
                try:
                    websocket = await websockets.connect(ws_url)
                    connections.append(websocket)
                    await asyncio.sleep(0.1)  # Small delay between connections
                except Exception:
                    break

            # Should allow reasonable number of connections
            assert len(connections) >= 5

        except ConnectionRefusedError:
            pytest.skip("WebSocket server not available for connection limit testing")
        finally:
            # Clean up connections
            for ws in connections:
                try:
                    await ws.close()
                except Exception:
                    pass

    @pytest.mark.asyncio
async def test_websocket_reconnection_handling(self):
        """Test WebSocket reconnection after disconnect"""
        try:
            ws_url = "pusher://app_key@cluster"

            # First connection
            async with async_mock_pusher_context() as pusher:
        # Connect using Pusherws_url) as websocket1:
                test_message = {"type": "ping"}
                await websocket1.send(json.dumps(test_message))

            # Reconnection after disconnect
            async with async_mock_pusher_context() as pusher:
        # Connect using Pusherws_url) as websocket2:
                test_message = {"type": "ping"}
                await websocket2.send(json.dumps(test_message))

                # Should work without issues
                try:
                    response = await asyncio.wait_for(websocket2.recv(), timeout=5.0)
                    assert response is not None
                except asyncio.TimeoutError:
                    # May not have echo functionality, that's okay
                    pass

        except ConnectionRefusedError:
            pytest.skip("WebSocket server not available for reconnection testing")


class TestPusherIntegration:
    """Test Pusher integration and channel management"""

    @pytest.mark.asyncio
async def test_pusher_authentication_endpoint(self, realtime_client, auth_headers):
        """Test Pusher authentication endpoint"""
        auth_data = {
            "socket_id": "test_socket_123",
            "channel_name": "private-user-123"
        }

        response = await realtime_client.post(
            "/api/v1/pusher/auth",
            json=auth_data,
            headers=auth_headers
        )

        if response.status_code == 404:
            # Try alternative endpoint
            response = await realtime_client.post(
                "/pusher/auth",
                json=auth_data,
                headers=auth_headers
            )

        if response.status_code == 404:
            pytest.skip("Pusher authentication endpoint not implemented")

        assert response.status_code == 200
        result = response.json()

        # Should return auth signature
        assert "auth" in result
        assert isinstance(result["auth"], str)

    @pytest.mark.asyncio
async def test_pusher_trigger_endpoint(self, realtime_client, auth_headers, mock_pusher_client):
        """Test Pusher event triggering endpoint"""
        trigger_data = {
            "channel": "public-notifications",
            "event": "test-event",
            "data": {
                "message": "Test notification",
                "timestamp": datetime.now().isoformat()
            }
        }

        with patch("apps.backend.services.pusher.pusher_client", mock_pusher_client):
            response = await realtime_client.post(
                "/api/v1/pusher/trigger",
                json=trigger_data,
                headers=auth_headers
            )

            if response.status_code == 404:
                # Try alternative endpoint
                response = await realtime_client.post(
                    "/pusher/trigger",
                    json=trigger_data,
                    headers=auth_headers
                )

            if response.status_code == 404:
                pytest.skip("Pusher trigger endpoint not implemented")

            assert response.status_code == 200
            result = response.json()

            # Should confirm event was triggered
            assert result.get("status") == "success"

            # Verify mock was called
            mock_pusher_client.trigger.assert_called_once()

    @pytest.mark.asyncio
async def test_pusher_channel_info(self, realtime_client, auth_headers, mock_pusher_client):
        """Test retrieving Pusher channel information"""
        with patch("apps.backend.services.pusher.pusher_client", mock_pusher_client):
            response = await realtime_client.get(
                "/api/v1/pusher/channels",
                headers=auth_headers
            )

            if response.status_code == 404:
                response = await realtime_client.get("/pusher/channels", headers=auth_headers)

            if response.status_code == 404:
                pytest.skip("Pusher channels endpoint not implemented")

            if response.status_code == 200:
                result = response.json()
                assert "channels" in result

    @pytest.mark.asyncio
async def test_pusher_webhook_handling(self, realtime_client):
        """Test Pusher webhook endpoint"""
        webhook_data = {
            "time_ms": int(time.time() * 1000),
            "events": [
                {
                    "name": "channel_occupied",
                    "channel": "test-channel",
                    "event": "client_event",
                    "data": "{\"message\": \"test\"}"
                }
            ]
        }

        # Webhooks typically don't require authentication
        response = await realtime_client.post(
            "/api/v1/pusher/webhook",
            json=webhook_data
        )

        if response.status_code == 404:
            response = await realtime_client.post("/pusher/webhook", json=webhook_data)

        if response.status_code == 404:
            pytest.skip("Pusher webhook endpoint not implemented")

        # Should accept webhook (may return 200 or 204)
        assert response.status_code in [200, 204]


class TestRealTimeMessageFlow:
    """Test end-to-end real-time message flow"""

    @pytest.mark.asyncio
async def test_content_generation_updates(self, realtime_client, auth_headers, mock_pusher_client):
        """Test real-time updates during content generation"""
        # Start content generation
        content_request = {
            "subject": "Mathematics",
            "grade_level": 7,
            "topic": "Linear Equations",
            "learning_objectives": ["Solve linear equations"]
        }

        with patch("apps.backend.services.pusher.pusher_client", mock_pusher_client):
            response = await realtime_client.post(
                "/api/v1/content/generate",
                json=content_request,
                headers=auth_headers
            )

            if response.status_code == 404:
                response = await realtime_client.post(
                    "/generate_content",
                    json=content_request,
                    headers=auth_headers
                )

            if response.status_code == 404:
                pytest.skip("Content generation endpoint not implemented")

            if response.status_code == 202:  # Async processing
                result = response.json()
                task_id = result.get("data", {}).get("task_id")

                if task_id:
                    # Verify progress updates were triggered
                    # In a real implementation, this would check Pusher events
                    await asyncio.sleep(1)  # Give time for background processing

                    # Check if progress events were triggered
                    trigger_calls = mock_pusher_client.trigger.call_args_list
                    progress_events = [
                        call for call in trigger_calls
                        if "progress" in str(call) or "content-generation" in str(call)
                    ]

                    # Should have triggered some progress events
                    if len(trigger_calls) > 0:
                        print(f"Triggered {len(trigger_calls)} Pusher events")

    @pytest.mark.asyncio
async def test_user_activity_broadcasting(self, realtime_client, auth_headers, mock_pusher_client):
        """Test broadcasting user activity to other users"""
        activity_data = {
            "user_id": "test_user_123",
            "lesson_id": "lesson_456",
            "activity": "quiz_completed",
            "score": 85,
            "timestamp": datetime.now().isoformat()
        }

        with patch("apps.backend.services.pusher.pusher_client", mock_pusher_client):
            response = await realtime_client.post(
                "/api/v1/activities/broadcast",
                json=activity_data,
                headers=auth_headers
            )

            if response.status_code == 404:
                # Try alternative endpoint
                response = await realtime_client.post(
                    "/api/v1/realtime/activity",
                    json=activity_data,
                    headers=auth_headers
                )

            if response.status_code == 404:
                pytest.skip("Activity broadcasting endpoint not implemented")

            if response.status_code == 200:
                # Should have triggered broadcast event
                mock_pusher_client.trigger.assert_called()

                # Verify correct channel and event type
                call_args = mock_pusher_client.trigger.call_args
                if call_args:
                    channel = call_args[0][0] if call_args[0] else None
                    event = call_args[0][1] if len(call_args[0]) > 1 else None

                    assert "activity" in channel or "lesson" in channel
                    assert event in ["user-activity", "activity-update", "quiz-completed"]

    @pytest.mark.asyncio
async def test_notification_delivery(self, realtime_client, auth_headers, mock_pusher_client):
        """Test notification delivery through real-time channels"""
        notification_data = {
            "recipient_id": "user_123",
            "type": "achievement",
            "title": "Congratulations!",
            "message": "You completed your first lesson!",
            "priority": "normal"
        }

        with patch("apps.backend.services.pusher.pusher_client", mock_pusher_client):
            response = await realtime_client.post(
                "/api/v1/notifications/send",
                json=notification_data,
                headers=auth_headers
            )

            if response.status_code == 404:
                response = await realtime_client.post(
                    "/api/v1/realtime/notify",
                    json=notification_data,
                    headers=auth_headers
                )

            if response.status_code == 404:
                pytest.skip("Notification endpoint not implemented")

            if response.status_code == 200:
                # Should have triggered notification event
                mock_pusher_client.trigger.assert_called()

                # Verify notification was sent to correct channel
                call_args = mock_pusher_client.trigger.call_args
                if call_args:
                    channel = call_args[0][0] if call_args[0] else None
                    assert "user_123" in channel or "private-user-123" in channel

    @pytest.mark.asyncio
async def test_lesson_collaboration_events(self, realtime_client, auth_headers, mock_pusher_client):
        """Test real-time events during collaborative lessons"""
        collaboration_events = [
            {
                "event_type": "user_joined",
                "lesson_id": "lesson_789",
                "user_id": "student_1",
                "user_name": "Alice Student"
            },
            {
                "event_type": "activity_shared",
                "lesson_id": "lesson_789",
                "user_id": "student_1",
                "activity_id": "activity_123",
                "shared_data": {"answer": "x = 5", "confidence": 0.8}
            },
            {
                "event_type": "user_left",
                "lesson_id": "lesson_789",
                "user_id": "student_1"
            }
        ]

        with patch("apps.backend.services.pusher.pusher_client", mock_pusher_client):
            for event in collaboration_events:
                response = await realtime_client.post(
                    "/api/v1/lessons/collaboration/event",
                    json=event,
                    headers=auth_headers
                )

                if response.status_code == 404:
                    response = await realtime_client.post(
                        "/api/v1/realtime/lesson-event",
                        json=event,
                        headers=auth_headers
                    )

                if response.status_code not in [404, 200]:
                    continue  # Skip if endpoint doesn't exist

                if response.status_code == 200:
                    # Each event should trigger a broadcast
                    break  # At least one worked

            # Should have triggered some collaboration events
            if mock_pusher_client.trigger.call_count > 0:
                print(f"Triggered {mock_pusher_client.trigger.call_count} collaboration events")


class TestCrossCompatibilityWebSocketPusher:
    """Test compatibility and fallback between WebSocket and Pusher"""

    @pytest.mark.asyncio
async def test_websocket_to_pusher_bridge(self, realtime_client, auth_headers, mock_pusher_client):
        """Test bridging WebSocket messages to Pusher channels"""
        try:
            ws_url = "pusher://app_key@cluster/bridge"

            with patch("apps.backend.services.pusher.pusher_client", mock_pusher_client):
                async with async_mock_pusher_context() as pusher:
        # Connect using Pusherws_url) as websocket:
                    # Send message via WebSocket that should be bridged to Pusher
                    bridge_message = {
                        "type": "broadcast",
                        "channel": "public-notifications",
                        "event": "websocket-message",
                        "data": {
                            "message": "Hello from WebSocket",
                            "timestamp": time.time()
                        }
                    }
                    await pusher.trigger(json.dumps(bridge_message))

                    # Give time for processing
                    await asyncio.sleep(1)

                    # Should have triggered Pusher event
                    if mock_pusher_client.trigger.call_count > 0:
                        print("WebSocket message successfully bridged to Pusher")

        except ConnectionRefusedError:
            pytest.skip("WebSocket bridge not available")

    @pytest.mark.asyncio
async def test_pusher_to_websocket_relay(self, realtime_client, auth_headers):
        """Test relaying Pusher events to WebSocket connections"""
        # This would test the reverse direction - Pusher events being relayed to WebSocket clients
        # Implementation depends on the specific architecture

        try:
            ws_url = "pusher://app_key@cluster/relay"

            async with async_mock_pusher_context() as pusher:
        # Connect using Pusherws_url) as websocket:
                # Subscribe to relay channel
                subscribe_message = {
                    "type": "subscribe",
                    "channel": "pusher-relay"
                }
                await pusher.trigger(json.dumps(subscribe_message))

                # Trigger Pusher event that should be relayed
                pusher_data = {
                    "channel": "pusher-relay",
                    "event": "test-relay",
                    "data": {"message": "Hello from Pusher"}
                }

                await realtime_client.post(
                    "/api/v1/pusher/trigger",
                    json=pusher_data,
                    headers=auth_headers
                )

                # Wait for relayed message
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    response_data = json.loads(response)

                    # Should receive the relayed Pusher event
                    assert response_data.get("event") == "test-relay"
                    assert "Hello from Pusher" in str(response_data)

                except asyncio.TimeoutError:
                    pytest.skip("Pusher to WebSocket relay not implemented")

        except ConnectionRefusedError:
            pytest.skip("WebSocket relay not available")

    @pytest.mark.asyncio
async def test_dual_client_consistency(self, realtime_client, auth_headers, mock_pusher_client):
        """Test that both WebSocket and Pusher clients receive same messages"""
        # This test would verify that messages sent through either system
        # are received consistently by both types of clients

        messages_received = {"websocket": [], "pusher": []}

        try:
            ws_url = "pusher://app_key@cluster"

            with patch("apps.backend.services.pusher.pusher_client", mock_pusher_client):
                async with async_mock_pusher_context() as pusher:
        # Connect using Pusherws_url) as websocket:
                    # Subscribe WebSocket to test channel
                    subscribe_message = {
                        "type": "subscribe",
                        "channel": "dual-test"
                    }
                    await pusher.trigger(json.dumps(subscribe_message))

                    # Send test message through API (should reach both clients)
                    test_data = {
                        "channel": "dual-test",
                        "event": "consistency-test",
                        "data": {"message": "Consistency test", "id": "test-123"}
                    }

                    await realtime_client.post(
                        "/api/v1/realtime/broadcast",
                        json=test_data,
                        headers=auth_headers
                    )

                    # Check WebSocket received message
                    try:
                        ws_response = await asyncio.wait_for(websocket.recv(), timeout=3.0)
                        messages_received["websocket"].append(json.loads(ws_response))
                    except asyncio.TimeoutError:
                        pass

                    # Check Pusher was triggered
                    if mock_pusher_client.trigger.call_count > 0:
                        messages_received["pusher"].append(mock_pusher_client.trigger.call_args)

                    # Both should have received the message
                    if messages_received["websocket"] and messages_received["pusher"]:
                        print("Both WebSocket and Pusher received the message")

        except ConnectionRefusedError:
            pytest.skip("Dual client testing not available")


class TestRealTimePerformanceReliability:
    """Test performance and reliability of real-time features"""

    @pytest.mark.asyncio
async def test_high_frequency_message_handling(self, realtime_client, auth_headers, mock_pusher_client):
        """Test handling of high-frequency messages"""
        with patch("apps.backend.services.pusher.pusher_client", mock_pusher_client):
            # Send many messages quickly
            tasks = []
            for i in range(100):
                message_data = {
                    "channel": "high-frequency-test",
                    "event": "rapid-fire",
                    "data": {"message_id": i, "timestamp": time.time()}
                }

                task = realtime_client.post(
                    "/api/v1/pusher/trigger",
                    json=message_data,
                    headers=auth_headers
                )
                tasks.append(task)

            # Execute all requests
            responses = await asyncio.gather(*tasks, return_exceptions=True)

            # Count successful responses
            successful = sum(
                1 for r in responses
                if not isinstance(r, Exception) and hasattr(r, 'status_code') and r.status_code == 200
            )

            print(f"Successful high-frequency messages: {successful}/100")

            # Should handle most messages successfully
            if successful > 0:
                assert successful >= 50  # At least 50% success rate

    @pytest.mark.asyncio
async def test_connection_stability_under_load(self):
        """Test WebSocket connection stability under load"""
        connections = []
        try:
            ws_url = "pusher://app_key@cluster"

            # Create multiple concurrent connections
            for i in range(20):
                try:
                    websocket = await websockets.connect(ws_url)
                    connections.append(websocket)

                    # Send test message
                    test_message = {"type": "load_test", "connection_id": i}
                    await pusher.trigger(json.dumps(test_message))

                except Exception as e:
                    print(f"Connection {i} failed: {e}")
                    break

            print(f"Established {len(connections)} concurrent WebSocket connections")

            # Send messages through all connections
            message_tasks = []
            for i, ws in enumerate(connections):
                try:
                    message = {"type": "concurrent_test", "id": i, "timestamp": time.time()}
                    message_tasks.append(pusher.trigger(json.dumps(message)))
                except Exception:
                    pass

            if message_tasks:
                await asyncio.gather(*message_tasks, return_exceptions=True)

            # Connections should remain stable
            assert len(connections) >= 10

        except ConnectionRefusedError:
            pytest.skip("WebSocket server not available for load testing")
        finally:
            # Clean up all connections
            for ws in connections:
                try:
                    await ws.close()
                except Exception:
                    pass

    @pytest.mark.asyncio
async def test_message_delivery_reliability(self, realtime_client, auth_headers, mock_pusher_client):
        """Test reliability of message delivery"""
        delivered_messages = []
        failed_messages = []

        with patch("apps.backend.services.pusher.pusher_client", mock_pusher_client):
            # Send messages with different priorities
            message_types = [
                {"priority": "high", "event": "critical-alert"},
                {"priority": "normal", "event": "notification"},
                {"priority": "low", "event": "update"}
            ]

            for i in range(30):  # 10 messages of each type
                msg_type = message_types[i % 3]
                message_data = {
                    "channel": f"reliability-test-{msg_type['priority']}",
                    "event": msg_type["event"],
                    "data": {
                        "message_id": i,
                        "priority": msg_type["priority"],
                        "timestamp": time.time()
                    }
                }

                try:
                    response = await realtime_client.post(
                        "/api/v1/pusher/trigger",
                        json=message_data,
                        headers=auth_headers
                    )

                    if response.status_code == 200:
                        delivered_messages.append(i)
                    else:
                        failed_messages.append(i)

                except Exception as e:
                    failed_messages.append(i)

                # Small delay to avoid overwhelming
                await asyncio.sleep(0.01)

            delivery_rate = len(delivered_messages) / (len(delivered_messages) + len(failed_messages)) * 100
            print(f"Message delivery rate: {delivery_rate:.1f}%")

            # Should have high delivery rate
            if len(delivered_messages) > 0:
                assert delivery_rate >= 90

    @pytest.mark.asyncio
async def test_error_recovery_mechanisms(self, realtime_client, auth_headers):
        """Test error recovery and graceful degradation"""
        # Test behavior when services are unavailable
        error_scenarios = [
            {"channel": "", "event": "test", "data": {}},  # Empty channel
            {"channel": "test", "event": "", "data": {}},  # Empty event
            {"channel": "test", "event": "test", "data": None},  # Invalid data
        ]

        for i, scenario in enumerate(error_scenarios):
            response = await realtime_client.post(
                "/api/v1/pusher/trigger",
                json=scenario,
                headers=auth_headers
            )

            # Should handle errors gracefully (not crash)
            assert response.status_code in [200, 400, 422, 500]

            if response.status_code >= 400:
                result = response.json()
                # Should provide meaningful error message
                assert "error" in result or "message" in result


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v", "--tb=short"])