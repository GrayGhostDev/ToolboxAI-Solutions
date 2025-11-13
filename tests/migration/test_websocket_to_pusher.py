"""WebSocket to Pusher Migration Tests"""


import httpx
import pytest
from pusher import Pusher


class TestWebSocketToPusherMigration:
    """Test suite for WebSocket to Pusher migration validation"""

    @pytest.fixture
    def pusher_client(self):
        """Create test Pusher client"""
        return Pusher(
            app_id="test-app", key="test-key", secret="test-secret", cluster="us2", ssl=True
        )

    @pytest.mark.asyncio
    async def test_websocket_endpoints_return_deprecation_warning(self):
        """Test that all WebSocket endpoints return deprecation warnings"""
        websocket_endpoints = [
            "/ws/roblox",
            "/ws/content",
            "/ws/plugin/test-id",
            "/ws/agent/agent-123",
            "/ws/native",
        ]

        async with httpx.AsyncClient(base_url="http://localhost:8009") as client:
            for endpoint in websocket_endpoints:
                response = await client.get(
                    endpoint, headers={"Upgrade": "websocket", "Connection": "Upgrade"}
                )

                # Should include deprecation headers
                assert response.headers.get("X-Deprecated") == "true"
                assert "pusher" in response.headers.get("X-Alternative", "").lower()

    @pytest.mark.asyncio
    async def test_pusher_channels_equivalent_functionality(self, pusher_client):
        """Test Pusher channels provide equivalent functionality to WebSocket"""
        # Test channel equivalence
        channel_mappings = {
            "/ws/roblox": "roblox-sync",
            "/ws/content": "content-generation",
            "/ws/agent/123": "agent-status",
            "/ws/plugin/xyz": "private-plugin-xyz",
        }

        for ws_endpoint, pusher_channel in channel_mappings.items():
            # Verify channel can be triggered
            result = pusher_client.trigger(pusher_channel, "test-event", {"message": "test"})
            assert result is not None

    @pytest.mark.asyncio
    async def test_backwards_compatibility_adapter(self):
        """Test WebSocket to Pusher adapter for backwards compatibility"""
        from tests.fixtures.pusher_test_utils import WebSocketToPusherAdapter

        adapter = WebSocketToPusherAdapter()

        # Old WebSocket message
        ws_message = {"type": "message", "data": {"content": "test message"}}

        # Convert to Pusher format
        pusher_event = adapter.convert_ws_to_pusher(ws_message)

        assert pusher_event["event"] == "message"
        assert pusher_event["data"]["content"] == "test message"

    @pytest.mark.asyncio
    async def test_pusher_auth_endpoint(self):
        """Test Pusher authentication endpoint"""
        async with httpx.AsyncClient(base_url="http://localhost:8009") as client:
            response = await client.post(
                "/pusher/auth",
                data={"socket_id": "test.socket", "channel_name": "private-test-channel"},
                headers={
                    "Authorization": "Bearer test-token",
                    "Content-Type": "application/x-www-form-urlencoded",
                },
            )

            # Should return auth signature for private channels
            assert response.status_code in [200, 401]  # 401 if no valid token

    @pytest.mark.asyncio
    async def test_realtime_trigger_endpoint(self):
        """Test Pusher realtime event triggering endpoint"""
        async with httpx.AsyncClient(base_url="http://localhost:8009") as client:
            response = await client.post(
                "/api/v1/realtime/trigger",
                json={
                    "channel": "test-channel",
                    "event": "test-event",
                    "data": {"message": "test"},
                },
                headers={"Authorization": "Bearer test-token", "Content-Type": "application/json"},
            )

            # Should accept event triggering
            assert response.status_code in [200, 401]  # 401 if no valid token

    def test_channel_naming_conventions(self):
        """Test Pusher channel naming follows conventions"""
        from tests.fixtures.pusher_test_utils import WebSocketToPusherAdapter

        adapter = WebSocketToPusherAdapter()

        test_cases = [
            ("/ws/roblox", "roblox-sync"),
            ("/ws/content", "content-generation"),
            ("/ws/agent/123", "agent-status-123"),
            ("/ws/plugin/xyz", "plugin-xyz"),
        ]

        for ws_endpoint, expected_channel in test_cases:
            channel = adapter.get_pusher_channel(ws_endpoint)
            assert channel == expected_channel

    @pytest.mark.asyncio
    async def test_websocket_legacy_support_headers(self):
        """Test that WebSocket endpoints include proper legacy support headers"""
        async with httpx.AsyncClient(base_url="http://localhost:8009") as client:
            response = await client.get("/ws/native")

            # Check for migration guidance headers
            headers = response.headers
            assert headers.get("X-Deprecated") == "true"
            assert "X-Alternative" in headers
            assert "X-Migration-Guide" in headers or "X-Documentation" in headers
