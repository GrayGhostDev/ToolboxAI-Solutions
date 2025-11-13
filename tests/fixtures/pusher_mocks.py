"""
Pusher mocking utilities for tests

Provides reusable mocks for Pusher functionality across all tests.
Replaces WebSocket mocks with Pusher-specific mocks.
"""

import json
from datetime import datetime
from typing import Any


class MockPusherClient:
    """Mock Pusher client for testing"""

    def __init__(self):
        self.triggered_events = []
        self.authenticated_channels = []
        self.channels = {}
        self._auth_responses = {}

    def trigger(self, channel: str, event: str, data: dict[str, Any]) -> dict:
        """Mock trigger method"""
        self.triggered_events.append(
            {
                "channel": channel,
                "event": event,
                "data": data,
                "timestamp": datetime.utcnow().isoformat(),
            }
        )
        return {"status": "success", "message_id": f"msg_{len(self.triggered_events)}"}

    def trigger_batch(self, events: list[dict]) -> dict:
        """Mock batch trigger method"""
        for event in events:
            self.trigger(event["channel"], event["name"], event["data"])
        return {"status": "success", "batch_id": f"batch_{len(self.triggered_events)}"}

    def authenticate(
        self, channel: str, socket_id: str, custom_data: dict | None = None
    ) -> dict:
        """Mock authentication method"""
        auth_key = f"{socket_id}:{channel}:mock_auth"

        response = {"auth": auth_key}

        if channel.startswith("presence-") and custom_data:
            response["channel_data"] = json.dumps(custom_data)

        self.authenticated_channels.append(
            {"channel": channel, "socket_id": socket_id, "timestamp": datetime.utcnow().isoformat()}
        )

        return response

    def channels_info(self, prefix_filter: str = "") -> dict:
        """Mock channels info method"""
        filtered_channels = {}
        for channel, info in self.channels.items():
            if not prefix_filter or channel.startswith(prefix_filter):
                filtered_channels[channel] = info
        return {"channels": filtered_channels}

    def channel_info(self, channel: str, attributes: list[str] = None) -> dict:
        """Mock channel info method"""
        if channel not in self.channels:
            return {"occupied": False}

        info = self.channels[channel]
        result = {"occupied": True}

        if attributes:
            if "user_count" in attributes and channel.startswith("presence-"):
                result["user_count"] = info.get("user_count", 0)
            if "subscription_count" in attributes:
                result["subscription_count"] = info.get("subscription_count", 0)

        return result

    def users_info(self, channel: str) -> dict:
        """Mock users info method for presence channels"""
        if not channel.startswith("presence-"):
            return {"users": []}

        if channel in self.channels:
            return {"users": self.channels[channel].get("users", [])}

        return {"users": []}

    def validate_webhook(self, key: str, signature: str, body: str) -> bool:
        """Mock webhook validation"""
        # In tests, we can simply return True or check a simple condition
        return signature == "valid_test_signature"

    def add_channel(self, channel: str, users: list[dict] = None):
        """Helper method to add a channel for testing"""
        self.channels[channel] = {
            "occupied": True,
            "subscription_count": len(users) if users else 1,
            "users": users or [],
        }
        if channel.startswith("presence-"):
            self.channels[channel]["user_count"] = len(users) if users else 0

    def clear(self):
        """Clear all mock data"""
        self.triggered_events = []
        self.authenticated_channels = []
        self.channels = {}


class MockPusherService:
    """Mock Pusher service for testing"""

    def __init__(self, app_id="test", key="test", secret="test", cluster="us2"):
        self.app_id = app_id
        self.key = key
        self.secret = secret
        self.cluster = cluster
        self.client = MockPusherClient()
        self.connected = True

    def trigger(self, channel: str, event: str, data: dict[str, Any]) -> dict:
        """Trigger an event"""
        if not self.connected:
            raise ConnectionError("Pusher service not connected")
        return self.client.trigger(channel, event, data)

    def trigger_batch(self, events: list[dict]) -> dict:
        """Trigger batch events"""
        if not self.connected:
            raise ConnectionError("Pusher service not connected")
        return self.client.trigger_batch(events)

    def authenticate(self, channel: str, socket_id: str, user_data: dict | None = None) -> dict:
        """Authenticate a channel"""
        return self.client.authenticate(channel, socket_id, user_data)

    def channels_info(self, prefix_filter: str = "") -> dict:
        """Get channels information"""
        return self.client.channels_info(prefix_filter)

    def channel_info(self, channel: str) -> dict:
        """Get single channel information"""
        return self.client.channel_info(channel)

    def users_info(self, channel: str) -> dict:
        """Get users in a presence channel"""
        return self.client.users_info(channel)

    def validate_webhook(self, key: str, signature: str, body: str) -> bool:
        """Validate webhook signature"""
        return self.client.validate_webhook(key, signature, body)

    def disconnect(self):
        """Simulate disconnection"""
        self.connected = False

    def reconnect(self):
        """Simulate reconnection"""
        self.connected = True


def create_mock_pusher_service():
    """Factory function to create a mock Pusher service"""
    return MockPusherService()


def create_mock_pusher_event(channel: str, event: str, data: dict[str, Any]) -> dict:
    """Create a mock Pusher event"""
    return {
        "id": f"evt_{datetime.utcnow().timestamp()}",
        "channel": channel,
        "event": event,
        "data": data,
        "timestamp": datetime.utcnow().isoformat(),
    }


def create_mock_webhook_payload(events: list[dict]) -> dict:
    """Create a mock Pusher webhook payload"""
    return {"time_ms": int(datetime.utcnow().timestamp() * 1000), "events": events}


class MockPusherChannelSubscription:
    """Mock a Pusher channel subscription for frontend testing"""

    def __init__(self, channel: str):
        self.channel = channel
        self.callbacks = {}
        self.subscribed = True

    def bind(self, event: str, callback):
        """Bind a callback to an event"""
        if event not in self.callbacks:
            self.callbacks[event] = []
        self.callbacks[event].append(callback)

    def unbind(self, event: str, callback=None):
        """Unbind a callback from an event"""
        if event in self.callbacks:
            if callback:
                self.callbacks[event].remove(callback)
            else:
                self.callbacks[event] = []

    def trigger(self, event: str, data: Any):
        """Trigger an event on this channel"""
        if event in self.callbacks:
            for callback in self.callbacks[event]:
                callback(data)

    def unsubscribe(self):
        """Unsubscribe from the channel"""
        self.subscribed = False
        self.callbacks = {}


class MockPusherConnection:
    """Mock Pusher connection for frontend testing"""

    def __init__(self):
        self.channels = {}
        self.state = "connected"
        self.socket_id = f"socket_{datetime.utcnow().timestamp()}"
        self.callbacks = {"state_change": [], "connected": [], "disconnected": [], "error": []}

    def subscribe(self, channel: str) -> MockPusherChannelSubscription:
        """Subscribe to a channel"""
        if channel not in self.channels:
            self.channels[channel] = MockPusherChannelSubscription(channel)
        return self.channels[channel]

    def unsubscribe(self, channel: str):
        """Unsubscribe from a channel"""
        if channel in self.channels:
            self.channels[channel].unsubscribe()
            del self.channels[channel]

    def bind(self, event: str, callback):
        """Bind a global event"""
        if event not in self.callbacks:
            self.callbacks[event] = []
        self.callbacks[event].append(callback)

    def unbind(self, event: str, callback=None):
        """Unbind a global event"""
        if event in self.callbacks:
            if callback:
                self.callbacks[event].remove(callback)
            else:
                self.callbacks[event] = []

    def disconnect(self):
        """Disconnect from Pusher"""
        self.state = "disconnected"
        self._trigger_callbacks("disconnected", {})
        self._trigger_callbacks(
            "state_change", {"current": "disconnected", "previous": "connected"}
        )

    def connect(self):
        """Connect to Pusher"""
        self.state = "connected"
        self.socket_id = f"socket_{datetime.utcnow().timestamp()}"
        self._trigger_callbacks("connected", {"socket_id": self.socket_id})
        self._trigger_callbacks(
            "state_change", {"current": "connected", "previous": "disconnected"}
        )

    def _trigger_callbacks(self, event: str, data: Any):
        """Trigger callbacks for an event"""
        if event in self.callbacks:
            for callback in self.callbacks[event]:
                callback(data)

    def channel(self, channel_name: str) -> MockPusherChannelSubscription | None:
        """Get a subscribed channel"""
        return self.channels.get(channel_name)


# Pytest fixtures
import pytest


@pytest.fixture
def mock_pusher_client():
    """Pytest fixture for mock Pusher client"""
    return MockPusherClient()


@pytest.fixture
def mock_pusher_service():
    """Pytest fixture for mock Pusher service"""
    return MockPusherService()


@pytest.fixture
def mock_pusher_connection():
    """Pytest fixture for mock Pusher connection (frontend)"""
    return MockPusherConnection()


@pytest.fixture
def mock_pusher_with_channels():
    """Pytest fixture with pre-configured channels"""
    service = MockPusherService()

    # Add some test channels
    service.client.add_channel("public-general", [])
    service.client.add_channel("private-user-123", [])
    service.client.add_channel(
        "presence-room-456",
        [{"id": "user1", "info": {"name": "User 1"}}, {"id": "user2", "info": {"name": "User 2"}}],
    )

    return service
