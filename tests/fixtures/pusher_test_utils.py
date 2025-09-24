"""
Pusher Test Utilities for WebSocket to Pusher Migration

This module provides comprehensive utilities for migrating WebSocket tests to Pusher,
including helpers for connection management, event simulation, and assertion helpers.
"""

import asyncio
import json
from typing import Dict, List, Optional, Any, Callable, Union
from unittest.mock import MagicMock, Mock, AsyncMock, patch
from datetime import datetime
import pytest
import pusher
from contextlib import contextmanager, asynccontextmanager
import logging

from tests.fixtures.pusher_mocks import (
    MockPusherClient, MockPusherService, MockPusherConnection,
    MockPusherChannelSubscription
)

logger = logging.getLogger(__name__)


class PusherTestHelper:
    """Helper class for Pusher testing with WebSocket migration support"""

    def __init__(self):
        self.received_events = []
        self.connections = []
        self.subscriptions = {}
        self.event_callbacks = {}

    def clear(self):
        """Clear all test data"""
        self.received_events = []
        self.connections = []
        self.subscriptions = {}
        self.event_callbacks = {}

    def simulate_websocket_to_pusher_event(self, ws_message: Dict) -> Dict:
        """
        Convert a WebSocket message to a Pusher event format

        WebSocket format: {"type": "message", "data": {...}}
        Pusher format: {"event": "message", "data": {...}, "channel": "..."}
        """
        pusher_event = {
            "event": ws_message.get("type", "message"),
            "data": ws_message.get("data", {}),
            "channel": ws_message.get("channel", "public-general"),
            "timestamp": datetime.utcnow().isoformat()
        }

        # Handle specific WebSocket patterns
        if "action" in ws_message:
            pusher_event["event"] = ws_message["action"]

        if "room" in ws_message:
            pusher_event["channel"] = f"presence-room-{ws_message['room']}"

        return pusher_event

    def assert_pusher_event_received(
        self,
        channel: str,
        event: str,
        data: Optional[Dict] = None,
        timeout: float = 5.0
    ) -> bool:
        """
        Assert that a specific Pusher event was received
        Replaces WebSocket frame assertions
        """
        for received in self.received_events:
            if (received.get("channel") == channel and
                received.get("event") == event):
                if data is None or received.get("data") == data:
                    return True
        return False

    def create_pusher_connection_mock(self) -> MockPusherConnection:
        """Create a mock Pusher connection with tracking"""
        conn = MockPusherConnection()
        self.connections.append(conn)

        # Track all events
        original_subscribe = conn.subscribe
        def tracked_subscribe(channel: str):
            sub = original_subscribe(channel)
            self.subscriptions[channel] = sub
            return sub
        conn.subscribe = tracked_subscribe

        return conn

    def simulate_pusher_events(self, events: List[Dict]):
        """Simulate multiple Pusher events for testing"""
        for event in events:
            self.received_events.append(event)
            channel = event.get("channel")
            event_name = event.get("event")

            # Trigger callbacks if subscribed
            if channel in self.subscriptions:
                sub = self.subscriptions[channel]
                sub.trigger(event_name, event.get("data"))

            # Trigger global callbacks
            if event_name in self.event_callbacks:
                for callback in self.event_callbacks[event_name]:
                    callback(event)


class PusherAsyncTestHelper(PusherTestHelper):
    """Async version of PusherTestHelper for async tests"""

    async def wait_for_event(
        self,
        channel: str,
        event: str,
        timeout: float = 5.0
    ) -> Optional[Dict]:
        """Wait for a specific Pusher event asynchronously"""
        start_time = asyncio.get_event_loop().time()

        while asyncio.get_event_loop().time() - start_time < timeout:
            for received in self.received_events:
                if (received.get("channel") == channel and
                    received.get("event") == event):
                    return received
            await asyncio.sleep(0.1)

        return None

    async def simulate_async_pusher_event(self, event: Dict):
        """Simulate an async Pusher event"""
        self.received_events.append(event)

        # Simulate async processing delay
        await asyncio.sleep(0.01)

        channel = event.get("channel")
        event_name = event.get("event")

        if channel in self.subscriptions:
            sub = self.subscriptions[channel]
            sub.trigger(event_name, event.get("data"))


@contextmanager
def mock_pusher_context(config: Optional[Dict] = None):
    """
    Context manager for mocking Pusher in tests
    Replaces WebSocket connection context managers
    """
    config = config or {}
    service = MockPusherService(
        app_id=config.get('app_id', 'test'),
        key=config.get('key', 'test'),
        secret=config.get('secret', 'test'),
        cluster=config.get('cluster', 'us2')
    )

    with patch('pusher.Pusher', return_value=service.client):
        with patch('apps.backend.services.pusher_realtime.pusher_client', service.client):
            yield service


@asynccontextmanager
async def async_mock_pusher_context(config: Optional[Dict] = None):
    """Async context manager for mocking Pusher in async tests"""
    config = config or {}
    service = MockPusherService(
        app_id=config.get('app_id', 'test'),
        key=config.get('key', 'test'),
        secret=config.get('secret', 'test'),
        cluster=config.get('cluster', 'us2')
    )

    with patch('pusher.Pusher', return_value=service.client):
        with patch('apps.backend.services.pusher_realtime.pusher_client', service.client):
            yield service


def create_pusher_test_client(app=None):
    """
    Create a test client with Pusher mocking enabled
    Replaces WebSocket test client creation
    """
    from fastapi.testclient import TestClient

    if app is None:
        from apps.backend.main import app

    client = TestClient(app)

    # Add Pusher-specific helpers to the client
    client.pusher_helper = PusherTestHelper()

    # Mock Pusher authentication endpoint
    original_post = client.post
    def enhanced_post(url: str, **kwargs):
        if url == "/pusher/auth":
            # Return mock authentication
            socket_id = kwargs.get('json', {}).get('socket_id', 'test_socket')
            channel = kwargs.get('json', {}).get('channel_name', 'test_channel')
            return MagicMock(
                status_code=200,
                json=lambda: {"auth": f"{socket_id}:{channel}:mock_auth"}
            )
        return original_post(url, **kwargs)

    client.post = enhanced_post

    return client


class PusherEventRecorder:
    """Records Pusher events for verification in tests"""

    def __init__(self):
        self.events = []
        self.channels = set()

    def record(self, channel: str, event: str, data: Any):
        """Record an event"""
        self.events.append({
            'channel': channel,
            'event': event,
            'data': data,
            'timestamp': datetime.utcnow().isoformat()
        })
        self.channels.add(channel)

    def get_events_for_channel(self, channel: str) -> List[Dict]:
        """Get all events for a specific channel"""
        return [e for e in self.events if e['channel'] == channel]

    def get_events_by_type(self, event_type: str) -> List[Dict]:
        """Get all events of a specific type"""
        return [e for e in self.events if e['event'] == event_type]

    def clear(self):
        """Clear all recorded events"""
        self.events = []
        self.channels = set()

    def assert_event_count(self, expected: int):
        """Assert the number of recorded events"""
        assert len(self.events) == expected, f"Expected {expected} events, got {len(self.events)}"

    def assert_channel_used(self, channel: str):
        """Assert that a specific channel was used"""
        assert channel in self.channels, f"Channel {channel} was not used"


# WebSocket to Pusher migration helpers

def convert_websocket_test_to_pusher(ws_test_func: Callable) -> Callable:
    """
    Decorator to convert WebSocket test to use Pusher

    Usage:
        @convert_websocket_test_to_pusher
        async def test_websocket_connection():
            # Test will automatically use Pusher instead
    """
    import functools
    import inspect

    @functools.wraps(ws_test_func)
    async def wrapper(*args, **kwargs):
        # Replace WebSocket with Pusher context
        async with async_mock_pusher_context() as pusher_service:
            # Inject pusher_service into the test
            if inspect.iscoroutinefunction(ws_test_func):
                return await ws_test_func(*args, pusher_service=pusher_service, **kwargs)
            else:
                return ws_test_func(*args, pusher_service=pusher_service, **kwargs)

    return wrapper


class WebSocketToPusherAdapter:
    """
    Adapter class to help migrate WebSocket tests to Pusher
    Provides WebSocket-like interface that uses Pusher under the hood
    """

    def __init__(self, pusher_connection: MockPusherConnection):
        self.pusher = pusher_connection
        self.default_channel = "public-general"

    async def send_text(self, message: str):
        """WebSocket send_text compatibility"""
        data = json.loads(message) if isinstance(message, str) else message
        event = self.pusher_helper.simulate_websocket_to_pusher_event(data)

        channel = self.pusher.channel(event['channel']) or self.pusher.subscribe(event['channel'])
        channel.trigger(event['event'], event['data'])

    async def send_json(self, data: Dict):
        """WebSocket send_json compatibility"""
        await self.send_text(json.dumps(data))

    async def receive_text(self) -> str:
        """WebSocket receive_text compatibility"""
        # Wait for next event
        if self.pusher_helper.received_events:
            event = self.pusher_helper.received_events.pop(0)
            return json.dumps(event)
        return json.dumps({"event": "empty"})

    async def receive_json(self) -> Dict:
        """WebSocket receive_json compatibility"""
        text = await self.receive_text()
        return json.loads(text)

    async def close(self):
        """WebSocket close compatibility"""
        self.pusher.disconnect()


# Pytest fixtures

@pytest.fixture
def pusher_test_helper():
    """Fixture for Pusher test helper"""
    helper = PusherTestHelper()
    yield helper
    helper.clear()


@pytest.fixture
def async_pusher_test_helper():
    """Fixture for async Pusher test helper"""
    helper = PusherAsyncTestHelper()
    yield helper
    helper.clear()


@pytest.fixture
def pusher_event_recorder():
    """Fixture for Pusher event recorder"""
    recorder = PusherEventRecorder()
    yield recorder
    recorder.clear()


@pytest.fixture
def pusher_test_client():
    """Fixture for test client with Pusher support"""
    return create_pusher_test_client()


@pytest.fixture
async def websocket_to_pusher_adapter(mock_pusher_connection):
    """Fixture for WebSocket to Pusher adapter"""
    adapter = WebSocketToPusherAdapter(mock_pusher_connection)
    adapter.pusher_helper = PusherTestHelper()
    yield adapter
    if adapter.pusher.state == 'connected':
        adapter.pusher.disconnect()


# Assertion helpers

def assert_pusher_connected(connection: MockPusherConnection):
    """Assert that Pusher connection is established"""
    assert connection.state == 'connected', "Pusher connection is not connected"
    assert connection.socket_id is not None, "Socket ID is not set"


def assert_channel_subscribed(connection: MockPusherConnection, channel: str):
    """Assert that a channel is subscribed"""
    assert channel in connection.channels, f"Channel {channel} is not subscribed"
    assert connection.channels[channel].subscribed, f"Channel {channel} subscription is not active"


def assert_event_triggered(service: MockPusherService, channel: str, event: str):
    """Assert that an event was triggered"""
    for triggered in service.client.triggered_events:
        if triggered['channel'] == channel and triggered['event'] == event:
            return True
    raise AssertionError(f"Event {event} on channel {channel} was not triggered")


# Batch migration helpers

def create_pusher_batch_test_suite(test_functions: List[Callable]) -> List[Callable]:
    """
    Convert multiple WebSocket test functions to Pusher tests

    Usage:
        ws_tests = [test_ws_connect, test_ws_message, test_ws_disconnect]
        pusher_tests = create_pusher_batch_test_suite(ws_tests)
    """
    return [convert_websocket_test_to_pusher(func) for func in test_functions]


# E2E test helpers for Playwright

def create_playwright_pusher_listener():
    """
    Create a Playwright page listener for Pusher events
    Replaces WebSocket frame monitoring
    """
    def pusher_listener(page):
        events = []

        # Inject Pusher event tracking into the page
        page.evaluate("""
            window.pusherEvents = [];
            if (window.pusher) {
                const originalSubscribe = window.pusher.subscribe;
                window.pusher.subscribe = function(channel) {
                    const sub = originalSubscribe.call(this, channel);
                    const originalBind = sub.bind;
                    sub.bind = function(event, callback) {
                        const wrappedCallback = function(data) {
                            window.pusherEvents.push({
                                channel: channel,
                                event: event,
                                data: data,
                                timestamp: new Date().toISOString()
                            });
                            callback(data);
                        };
                        return originalBind.call(this, event, wrappedCallback);
                    };
                    return sub;
                };
            }
        """)

        def get_events():
            return page.evaluate("window.pusherEvents || []")

        return get_events

    return pusher_listener


# Configuration helpers

def get_pusher_test_config():
    """Get Pusher test configuration"""
    return {
        'app_id': 'test_app_id',
        'key': 'test_key',
        'secret': 'test_secret',
        'cluster': 'us2',
        'ssl': False,
        'host': 'localhost',
        'port': 6001  # For local Pusher server testing
    }


def setup_pusher_test_environment():
    """Setup environment variables for Pusher testing"""
    import os
    config = get_pusher_test_config()

    os.environ['PUSHER_APP_ID'] = config['app_id']
    os.environ['PUSHER_KEY'] = config['key']
    os.environ['PUSHER_SECRET'] = config['secret']
    os.environ['PUSHER_CLUSTER'] = config['cluster']
    os.environ['PUSHER_ENABLED'] = 'true'