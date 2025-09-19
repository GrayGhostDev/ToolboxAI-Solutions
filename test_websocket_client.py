#!/usr/bin/env python3
"""
WebSocket Test Client for Roblox Integration
Tests the real-time connection to the FastAPI WebSocket endpoint
"""

import asyncio
import json
import logging
from datetime import datetime
import websockets
import uuid

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class RobloxWebSocketTestClient:
    def __init__(self, url="ws://localhost:8008/ws/roblox"):
        self.url = url
        self.client_id = str(uuid.uuid4())
        self.websocket = None

    async def connect(self):
        """Establish WebSocket connection"""
        try:
            self.websocket = await websockets.connect(self.url)
            logger.info(f"Connected to {self.url}")
            logger.info(f"Client ID: {self.client_id}")
            return True
        except Exception as e:
            logger.error(f"Connection failed: {e}")
            return False

    async def send_message(self, message_type, payload):
        """Send a message to the server"""
        message = {
            "id": str(uuid.uuid4()),
            "type": message_type,
            "payload": payload,
            "timestamp": datetime.utcnow().isoformat(),
            "client_id": self.client_id
        }

        try:
            await self.websocket.send(json.dumps(message))
            logger.info(f"Sent {message_type}: {payload}")
        except Exception as e:
            logger.error(f"Failed to send message: {e}")

    async def receive_messages(self):
        """Listen for messages from server"""
        try:
            async for message in self.websocket:
                data = json.loads(message)
                logger.info(f"Received: {json.dumps(data, indent=2)}")

                # Handle specific message types
                if data.get("type") == "CONNECTION_ACK":
                    logger.info("✓ Connection acknowledged by server")
                elif data.get("type") == "HEARTBEAT":
                    logger.info("♥ Heartbeat received")
                elif data.get("type") == "ERROR":
                    logger.error(f"Server error: {data.get('payload', {}).get('error')}")

        except websockets.exceptions.ConnectionClosed:
            logger.info("Connection closed by server")
        except Exception as e:
            logger.error(f"Error receiving messages: {e}")

    async def test_sequence(self):
        """Run a test sequence of operations"""

        # Test 1: Send heartbeat
        await asyncio.sleep(1)
        await self.send_message("heartbeat", {})

        # Test 2: Subscribe to channels
        await asyncio.sleep(1)
        await self.send_message("subscribe", {
            "channels": ["scripts", "deployments", "agents"]
        })

        # Test 3: Request script validation
        await asyncio.sleep(1)
        await self.send_message("validation_request", {
            "script": """
                local part = Instance.new("Part")
                part.Name = "TestPart"
                part.Parent = workspace
                print("Test script executed")
            """,
            "script_type": "ServerScript",
            "strict_mode": True
        })

        # Test 4: Simulate script update
        await asyncio.sleep(1)
        await self.send_message("script_update", {
            "script_id": "test-script-001",
            "script_type": "ModuleScript",
            "content": "return {version = '1.0.0'}"
        })

        # Test 5: Request deployment
        await asyncio.sleep(1)
        await self.send_message("deployment_request", {
            "content_type": "script",
            "content_data": "print('Deployed script')",
            "target_place_id": "test-place-123",
            "priority": 5
        })

        # Keep connection alive for more messages
        await asyncio.sleep(10)

    async def disconnect(self):
        """Close the WebSocket connection"""
        if self.websocket:
            await self.websocket.close()
            logger.info("Disconnected from server")

async def main():
    """Main test function"""

    logger.info("=" * 50)
    logger.info("Roblox WebSocket Test Client")
    logger.info("=" * 50)

    client = RobloxWebSocketTestClient()

    # Connect to server
    if not await client.connect():
        logger.error("Failed to establish connection. Is the server running?")
        return

    # Run test sequence and receive messages concurrently
    try:
        await asyncio.gather(
            client.test_sequence(),
            client.receive_messages()
        )
    except KeyboardInterrupt:
        logger.info("\nTest interrupted by user")
    finally:
        await client.disconnect()

    logger.info("=" * 50)
    logger.info("Test completed")
    logger.info("=" * 50)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\nTest client terminated")