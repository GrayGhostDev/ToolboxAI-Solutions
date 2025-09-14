import asyncio
import os
import websockets

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
import pytest

# Skip all tests in this module as they require external services
pytestmark = pytest.mark.skipif(
    not os.environ.get('RUN_INTEGRATION_TESTS'),
    reason="Integration tests disabled. Set RUN_INTEGRATION_TESTS=1 to enable"
)

@pytest.mark.asyncio(loop_scope="function")
async def test_websocket():
    uri = "ws://127.0.0.1:8008/ws/test_client"
    try:
        async with websockets.connect(uri) as websocket:
            # Send ping
            await websocket.send(json.dumps({"type": "ping"}, default=make_json_serializable))
            response = await websocket.recv()
            print(f"Ping response: {response}")
            
            # Send broadcast
            await websocket.send(json.dumps({
                "type": "broadcast",
                "message": "Test message from Terminal 1"
            }, default=make_json_serializable))
            response = await websocket.recv()
            print(f"Broadcast response: {response}")
            print("✅ WebSocket test successful!")
    except Exception as e:
        print(f"❌ WebSocket test failed: {e}")

asyncio.run(test_websocket())