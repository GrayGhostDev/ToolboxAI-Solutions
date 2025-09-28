# Pusher Testing Guide

## WebSocket to Pusher Migration Guide for Tests

This guide explains how to write and migrate tests from WebSocket to Pusher Channels, providing patterns, examples, and best practices.

## Table of Contents

1. [Overview](#overview)
2. [Test Utilities](#test-utilities)
3. [Migration Patterns](#migration-patterns)
4. [Test Examples](#test-examples)
5. [Best Practices](#best-practices)
6. [Troubleshooting](#troubleshooting)

## Overview

The application has migrated from raw WebSocket connections to Pusher Channels for real-time communication. This provides:

- **Managed Infrastructure**: No need to maintain WebSocket servers
- **Built-in Features**: Presence channels, private channels, client events
- **Better Scalability**: Automatic scaling and load balancing
- **Enhanced Security**: Built-in authentication and encryption

## Test Utilities

### Core Test Files

```
tests/fixtures/
├── pusher_mocks.py         # Mock Pusher client and service
├── pusher_test_utils.py    # Test helpers and utilities
└── conftest.py              # Pytest fixtures
```

### Available Fixtures

#### Python Tests

```python
# Basic fixtures
@pytest.fixture
def mock_pusher_client():
    """Mock Pusher client for testing"""
    return MockPusherClient()

@pytest.fixture
def mock_pusher_service():
    """Mock Pusher service for testing"""
    return MockPusherService()

@pytest.fixture
def pusher_test_helper():
    """Helper for Pusher testing"""
    return PusherTestHelper()

@pytest.fixture
def pusher_event_recorder():
    """Record Pusher events for verification"""
    return PusherEventRecorder()
```

#### TypeScript/JavaScript Tests

```typescript
// Mock Pusher service
vi.mock('../../services/pusher', () => ({
  PusherService: {
    getInstance: vi.fn(() => ({
      connect: vi.fn(),
      disconnect: vi.fn(),
      subscribe: vi.fn(),
      trigger: vi.fn(),
      isConnected: vi.fn(() => true),
    }))
  }
}));
```

## Migration Patterns

### Pattern 1: Connection Testing

#### Before (WebSocket)
```python
import websockets

async def test_websocket_connection():
    ws = await websockets.connect("ws://localhost:8000/ws")
    await ws.send(json.dumps({"type": "ping"}))
    response = await ws.recv()
    assert json.loads(response)["type"] == "pong"
    await ws.close()
```

#### After (Pusher)
```python
from tests.fixtures.pusher_test_utils import async_mock_pusher_context

async def test_pusher_connection():
    async with async_mock_pusher_context() as pusher:
        pusher.connect()
        assert pusher.connected

        # Test event triggering
        response = pusher.trigger("test-channel", "ping", {"data": "test"})
        assert response["status"] == "success"
```

### Pattern 2: Channel Subscription

#### Before (WebSocket)
```python
async def test_channel_subscription():
    ws = await websockets.connect("ws://localhost:8000/ws")
    await ws.send(json.dumps({
        "type": "subscribe",
        "channel": "updates"
    }))
    response = await ws.recv()
    assert json.loads(response)["subscribed"] == True
```

#### After (Pusher)
```python
async def test_channel_subscription():
    async with async_mock_pusher_context() as pusher:
        # Subscribe to channel
        pusher.client.add_channel("dashboard-updates")

        # Verify subscription
        channels = pusher.channels_info()
        assert "dashboard-updates" in channels["channels"]
```

### Pattern 3: Message Broadcasting

#### Before (WebSocket)
```python
async def test_broadcasting():
    ws1 = await websockets.connect("ws://localhost:8000/ws")
    ws2 = await websockets.connect("ws://localhost:8000/ws")

    # Join same room
    await ws1.send(json.dumps({"type": "join", "room": "test"}))
    await ws2.send(json.dumps({"type": "join", "room": "test"}))

    # Send message
    await ws1.send(json.dumps({"type": "message", "data": "test"}))

    # Both should receive
    msg1 = await ws1.recv()
    msg2 = await ws2.recv()
```

#### After (Pusher)
```python
async def test_broadcasting():
    async with async_mock_pusher_context() as pusher:
        # Add channel with multiple users
        pusher.client.add_channel("presence-room-123", [
            {"id": "user1", "info": {"name": "Alice"}},
            {"id": "user2", "info": {"name": "Bob"}}
        ])

        # Broadcast message
        response = pusher.trigger("presence-room-123", "message", {
            "text": "Hello everyone",
            "sender": "user1"
        })

        # Verify broadcast
        assert response["status"] == "success"
        events = pusher.client.triggered_events
        assert len(events) > 0
```

### Pattern 4: Frontend Component Testing

#### Before (WebSocket)
```typescript
// Mock WebSocket
vi.mock('../../services/websocket', () => ({
  WebSocketService: {
    getInstance: vi.fn(() => ({
      connect: vi.fn(),
      send: vi.fn(),
      subscribe: vi.fn(() => vi.fn()),
    }))
  }
}));

test('should connect to websocket', () => {
  render(<Dashboard />);
  expect(WebSocketService.getInstance().connect).toHaveBeenCalled();
});
```

#### After (Pusher)
```typescript
// Mock Pusher
vi.mock('../../services/pusher', () => ({
  PusherService: {
    getInstance: vi.fn(() => ({
      connect: vi.fn(),
      subscribe: vi.fn(() => ({
        bind: vi.fn(),
        unbind: vi.fn(),
      })),
      trigger: vi.fn(),
    }))
  }
}));

test('should connect to pusher', () => {
  render(<Dashboard />);
  expect(PusherService.getInstance().connect).toHaveBeenCalled();
});
```

### Pattern 5: E2E Playwright Testing

#### Before (WebSocket)
```typescript
test('should track websocket frames', async ({ page }) => {
  const websockets = [];

  page.on('websocket', ws => {
    websockets.push(ws);
    ws.on('framereceived', frame => console.log('Received:', frame));
  });

  await page.goto('http://localhost:5179');
  expect(websockets.length).toBeGreaterThan(0);
});
```

#### After (Pusher)
```typescript
test('should connect to pusher', async ({ page }) => {
  await page.goto('http://localhost:5179');

  // Check Pusher connection state
  const pusherState = await page.evaluate(() => {
    if (window.pusher) {
      return {
        state: window.pusher.connection.state,
        socket_id: window.pusher.connection.socket_id
      };
    }
    return null;
  });

  expect(pusherState?.state).toBe('connected');
  expect(pusherState?.socket_id).toBeDefined();
});
```

## Test Examples

### Complete Python Test Example

```python
import pytest
from tests.fixtures.pusher_test_utils import (
    async_mock_pusher_context,
    PusherAsyncTestHelper,
    PusherEventRecorder
)

class TestPusherIntegration:

    @pytest.mark.asyncio
    async def test_full_workflow(self):
        """Test complete Pusher workflow"""
        async with async_mock_pusher_context() as pusher:
            helper = PusherAsyncTestHelper()
            recorder = PusherEventRecorder()

            # 1. Connect
            pusher.connect()
            assert pusher.connected

            # 2. Subscribe to channels
            channels = ["public-api", "private-user-123", "presence-room-456"]
            for channel in channels:
                pusher.client.add_channel(channel)

            # 3. Authenticate private/presence channels
            auth_response = pusher.authenticate(
                "private-user-123",
                "socket_123",
                {"user_id": "123", "user_info": {"name": "Test User"}}
            )
            assert auth_response.get("auth")

            # 4. Trigger events
            for channel in channels:
                event_data = {
                    "message": f"Test event for {channel}",
                    "timestamp": "2024-01-01T00:00:00Z"
                }
                response = pusher.trigger(channel, "test-event", event_data)
                assert response["status"] == "success"
                recorder.record(channel, "test-event", event_data)

            # 5. Verify events
            recorder.assert_event_count(3)
            recorder.assert_channel_used("public-api")

            # 6. Test presence channel features
            users = pusher.users_info("presence-room-456")
            assert len(users["users"]) > 0

            # 7. Disconnect
            pusher.disconnect()
            assert not pusher.connected
```

### Complete TypeScript Test Example

```typescript
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { Dashboard } from './Dashboard';

// Mock Pusher service
vi.mock('../../services/pusher', () => ({
  PusherService: {
    getInstance: vi.fn()
  },
  PusherChannels: {
    DASHBOARD_UPDATES: 'dashboard-updates',
    CONTENT_GENERATION: 'content-generation'
  },
  PusherEventType: {
    CONTENT_UPDATE: 'content-update',
    PROGRESS_UPDATE: 'progress-update'
  }
}));

describe('Dashboard with Pusher', () => {
  let mockPusherInstance;

  beforeEach(() => {
    // Create mock Pusher instance
    mockPusherInstance = {
      connect: vi.fn(),
      disconnect: vi.fn(),
      isConnected: vi.fn(() => true),
      getSocketId: vi.fn(() => 'mock-socket-123'),
      subscribe: vi.fn((channel) => ({
        bind: vi.fn(),
        unbind: vi.fn(),
        unsubscribe: vi.fn(),
        trigger: vi.fn()
      })),
      trigger: vi.fn()
    };

    // Return mock instance
    PusherService.getInstance.mockReturnValue(mockPusherInstance);
  });

  it('should connect to Pusher on mount', async () => {
    render(<Dashboard />);

    await waitFor(() => {
      expect(mockPusherInstance.connect).toHaveBeenCalled();
    });
  });

  it('should subscribe to dashboard channels', async () => {
    render(<Dashboard />);

    await waitFor(() => {
      expect(mockPusherInstance.subscribe).toHaveBeenCalledWith('dashboard-updates');
      expect(mockPusherInstance.subscribe).toHaveBeenCalledWith('content-generation');
    });
  });

  it('should handle Pusher events', async () => {
    render(<Dashboard />);

    // Get the channel mock
    const channelMock = mockPusherInstance.subscribe('dashboard-updates');

    // Simulate receiving an event
    const eventHandler = channelMock.bind.mock.calls[0][1];
    eventHandler({
      type: 'metric-update',
      data: { students: 150 }
    });

    // Verify UI updated
    await waitFor(() => {
      expect(screen.getByText(/150 students/)).toBeInTheDocument();
    });
  });

  it('should disconnect on unmount', () => {
    const { unmount } = render(<Dashboard />);

    unmount();

    expect(mockPusherInstance.disconnect).toHaveBeenCalled();
  });
});
```

## Best Practices

### 1. Use Context Managers

Always use context managers for Pusher connections in tests:

```python
# Good
async with async_mock_pusher_context() as pusher:
    # Test code here
    pass

# Bad
pusher = MockPusherService()
# Test code here
# Forgot to disconnect!
```

### 2. Test Event Recording

Use event recorders to verify complex event flows:

```python
recorder = PusherEventRecorder()

# Trigger multiple events
for i in range(10):
    pusher.trigger("channel", f"event-{i}", {"index": i})
    recorder.record("channel", f"event-{i}", {"index": i})

# Verify all events
recorder.assert_event_count(10)
events = recorder.get_events_for_channel("channel")
assert len(events) == 10
```

### 3. Mock Authentication Properly

For private/presence channels, always mock authentication:

```python
# Mock authentication
auth_response = pusher.authenticate(
    channel="private-user-123",
    socket_id="socket_456",
    custom_data={"user_id": "123", "role": "admin"}
)

# Verify auth token
assert "auth" in auth_response
assert auth_response["auth"].startswith("socket_456:")
```

### 4. Test Reconnection Logic

Always test connection resilience:

```python
async def test_reconnection():
    async with async_mock_pusher_context() as pusher:
        # Initial connection
        pusher.connect()
        assert pusher.connected

        # Simulate disconnection
        pusher.disconnect()
        assert not pusher.connected

        # Reconnect
        pusher.reconnect()
        assert pusher.connected

        # Verify can still trigger events
        response = pusher.trigger("test", "event", {})
        assert response["status"] == "success"
```

### 5. Clean Up After Tests

Always clean up subscriptions and connections:

```python
@pytest.fixture
def pusher_test_env():
    """Fixture that ensures cleanup"""
    pusher = MockPusherService()
    yield pusher
    # Cleanup
    pusher.disconnect()
    pusher.client.clear()
```

## Troubleshooting

### Common Issues and Solutions

#### Issue 1: Tests Still Using WebSocket Imports

**Problem**: Tests import `websockets` or `WebSocketService`

**Solution**: Run the migration script:
```bash
python scripts/migrate_websocket_tests_to_pusher.py --path tests/
```

#### Issue 2: Channel Not Found in Tests

**Problem**: Test fails with "channel not found"

**Solution**: Add the channel before testing:
```python
pusher.client.add_channel("my-channel")
```

#### Issue 3: Authentication Failures

**Problem**: Private/presence channel auth fails

**Solution**: Mock authentication properly:
```python
@patch('apps.backend.services.pusher_realtime.pusher_client.authenticate')
def test_private_channel(mock_auth):
    mock_auth.return_value = {"auth": "valid_auth_token"}
    # Test code here
```

#### Issue 4: Event Not Received

**Problem**: Test doesn't receive expected events

**Solution**: Use event recorder and verify triggering:
```python
recorder = PusherEventRecorder()
pusher.trigger("channel", "event", data)
# Verify in triggered_events, not received_events
assert len(pusher.client.triggered_events) > 0
```

#### Issue 5: Playwright Can't Find Pusher

**Problem**: `window.pusher` is undefined in Playwright tests

**Solution**: Wait for Pusher to initialize:
```typescript
await page.waitForFunction(() => window.pusher !== undefined);
```

## Migration Checklist

When migrating tests from WebSocket to Pusher:

- [ ] Replace `websockets` imports with Pusher utilities
- [ ] Update connection patterns (ws:// → Pusher client)
- [ ] Change `send()` calls to `trigger()`
- [ ] Update channel subscription patterns
- [ ] Replace WebSocket event listeners with Pusher bindings
- [ ] Update mocks in frontend tests
- [ ] Test authentication for private/presence channels
- [ ] Verify event recording and assertions
- [ ] Add proper cleanup in fixtures
- [ ] Run tests to ensure they pass

## Advanced Patterns

### Batch Event Testing

```python
async def test_batch_events():
    async with async_mock_pusher_context() as pusher:
        events = [
            {"channel": "ch1", "name": "evt1", "data": {"id": 1}},
            {"channel": "ch2", "name": "evt2", "data": {"id": 2}},
            {"channel": "ch3", "name": "evt3", "data": {"id": 3}},
        ]

        response = pusher.trigger_batch(events)
        assert response["status"] == "success"
        assert len(pusher.client.triggered_events) == 3
```

### Presence Channel Testing

```python
async def test_presence_channel():
    async with async_mock_pusher_context() as pusher:
        # Add presence channel with members
        pusher.client.add_channel("presence-classroom", [
            {"id": "teacher1", "info": {"name": "Ms. Smith", "role": "teacher"}},
            {"id": "student1", "info": {"name": "Alice", "role": "student"}},
            {"id": "student2", "info": {"name": "Bob", "role": "student"}},
        ])

        # Get channel info
        info = pusher.channel_info("presence-classroom", ["user_count"])
        assert info["user_count"] == 3

        # Get users
        users = pusher.users_info("presence-classroom")
        assert len(users["users"]) == 3

        # Simulate member events
        pusher.trigger("presence-classroom", "member_added", {
            "id": "student3",
            "info": {"name": "Charlie", "role": "student"}
        })
```

### Performance Testing

```python
async def test_pusher_performance():
    async with async_mock_pusher_context() as pusher:
        import time

        channel = "performance-test"
        pusher.client.add_channel(channel)

        # Measure event triggering performance
        start_time = time.time()
        num_events = 1000

        for i in range(num_events):
            pusher.trigger(channel, "perf-event", {"index": i})

        elapsed = time.time() - start_time
        events_per_second = num_events / elapsed

        assert events_per_second > 100  # Should handle >100 events/sec
        assert len(pusher.client.triggered_events) == num_events
```

## Resources

- [Pusher Documentation](https://pusher.com/docs)
- [Pusher Python Client](https://github.com/pusher/pusher-http-python)
- [Pusher JavaScript Client](https://github.com/pusher/pusher-js)
- [Migration Script](/scripts/migrate_websocket_tests_to_pusher.py)
- [Test Utilities](/tests/fixtures/pusher_test_utils.py)
- [Mock Implementations](/tests/fixtures/pusher_mocks.py)

## Summary

The migration from WebSocket to Pusher in tests provides:

1. **Simpler Testing**: No need to manage WebSocket connections
2. **Better Mocking**: Comprehensive mock implementations available
3. **Feature-Rich**: Test presence, private channels, and batch events
4. **Consistent Patterns**: Same patterns across Python and TypeScript
5. **Better Debugging**: Event recording and detailed assertions

Follow this guide when writing new tests or migrating existing WebSocket tests to Pusher.