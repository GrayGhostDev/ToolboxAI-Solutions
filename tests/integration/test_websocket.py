import asyncio
import websockets
import json
import pytest

# Skip all tests in this module as they require external services
pytestmark = pytest.mark.skip(reason="Integration tests require external services - run with --run-integration")

async def test_websocket():
    uri = "ws://127.0.0.1:8008/ws/test_client"
    try:
        async with websockets.connect(uri) as websocket:
            # Send ping
            await websocket.send(json.dumps({"type": "ping"}))
            response = await websocket.recv()
            print(f"Ping response: {response}")
            
            # Send broadcast
            await websocket.send(json.dumps({
                "type": "broadcast",
                "message": "Test message from Terminal 1"
            }))
            response = await websocket.recv()
            print(f"Broadcast response: {response}")
            print("✅ WebSocket test successful!")
    except Exception as e:
        print(f"❌ WebSocket test failed: {e}")

asyncio.run(test_websocket())