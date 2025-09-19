#!/usr/bin/env python3
"""
Test authenticated WebSocket connection for Roblox integration
Validates JWT authentication and real-time communication
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


class AuthenticatedRobloxWebSocketTest:
    def __init__(self, base_url="localhost:8008"):
        self.base_url = base_url
        self.client_id = str(uuid.uuid4())
        self.websocket = None
        self.access_token = None
        self.refresh_token = None

    async def get_jwt_token(self):
        """Get JWT token from the authentication system"""
        try:
            # Import JWT manager
            from apps.backend.core.security.jwt_rotation import get_jwt_manager

            # Get manager and create token pair
            jwt_manager = await get_jwt_manager()
            self.access_token, self.refresh_token = await jwt_manager.create_token_pair(
                user_id="test-roblox-user",
                scope="roblox.studio"
            )

            logger.info("JWT tokens obtained successfully")
            logger.info(f"Access token (first 50 chars): {self.access_token[:50]}...")

            return True

        except Exception as e:
            logger.error(f"Failed to get JWT token: {e}")
            return False

    async def test_without_auth(self):
        """Test connection without authentication (should fail)"""
        logger.info("\n1. Testing connection WITHOUT authentication...")

        try:
            url = f"ws://{self.base_url}/ws/roblox"
            websocket = await websockets.connect(url)
            logger.error("  ✗ Connection succeeded without auth (security issue!)")
            await websocket.close()
            return False

        except websockets.exceptions.ConnectionClosedError as e:
            logger.info(f"  ✓ Connection properly rejected: {e}")
            return True
        except Exception as e:
            logger.error(f"  ✗ Unexpected error: {e}")
            return False

    async def test_with_invalid_token(self):
        """Test connection with invalid token (should fail)"""
        logger.info("\n2. Testing connection with INVALID token...")

        try:
            invalid_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.invalid.token"
            url = f"ws://{self.base_url}/ws/roblox?token={invalid_token}"
            websocket = await websockets.connect(url)
            logger.error("  ✗ Connection succeeded with invalid token (security issue!)")
            await websocket.close()
            return False

        except websockets.exceptions.ConnectionClosedError as e:
            logger.info(f"  ✓ Invalid token properly rejected: {e}")
            return True
        except Exception as e:
            logger.error(f"  ✗ Unexpected error: {e}")
            return False

    async def test_with_valid_token(self):
        """Test connection with valid token (should succeed)"""
        logger.info("\n3. Testing connection with VALID token...")

        try:
            if not self.access_token:
                await self.get_jwt_token()

            url = f"ws://{self.base_url}/ws/roblox?token={self.access_token}"
            self.websocket = await websockets.connect(url)
            logger.info("  ✓ Connected successfully with valid token")

            # Wait for connection acknowledgment
            message = await self.websocket.recv()
            data = json.loads(message)

            if data.get("type") == "connection_ack":
                logger.info(f"  ✓ Connection acknowledged")
                logger.info(f"    Client ID: {data.get('payload', {}).get('client_id')}")
                logger.info(f"    User ID: {data.get('payload', {}).get('user_id')}")
                logger.info(f"    Scope: {data.get('payload', {}).get('scope')}")
                return True
            else:
                logger.error(f"  ✗ Unexpected message type: {data.get('type')}")
                return False

        except Exception as e:
            logger.error(f"  ✗ Connection failed: {e}")
            return False

    async def test_authenticated_operations(self):
        """Test operations with authenticated connection"""
        logger.info("\n4. Testing authenticated operations...")

        if not self.websocket:
            logger.error("  ✗ No authenticated connection available")
            return False

        try:
            # Test heartbeat
            logger.info("  Testing heartbeat...")
            await self.websocket.send(json.dumps({
                "id": str(uuid.uuid4()),
                "type": "heartbeat",
                "payload": {},
                "client_id": self.client_id
            }))

            response = await asyncio.wait_for(self.websocket.recv(), timeout=5)
            data = json.loads(response)
            if data.get("type") == "heartbeat":
                logger.info("    ✓ Heartbeat successful")
            else:
                logger.error(f"    ✗ Unexpected response: {data.get('type')}")

            # Test subscription
            logger.info("  Testing subscription...")
            await self.websocket.send(json.dumps({
                "id": str(uuid.uuid4()),
                "type": "subscribe",
                "payload": {"channels": ["scripts", "deployments"]},
                "client_id": self.client_id
            }))

            response = await asyncio.wait_for(self.websocket.recv(), timeout=5)
            data = json.loads(response)
            if data.get("type") == "connection_ack":
                subscribed = data.get("payload", {}).get("subscribed", [])
                logger.info(f"    ✓ Subscribed to: {subscribed}")
            else:
                logger.error(f"    ✗ Subscription failed: {data}")

            return True

        except asyncio.TimeoutError:
            logger.error("  ✗ Operation timed out")
            return False
        except Exception as e:
            logger.error(f"  ✗ Operation failed: {e}")
            return False

    async def test_token_refresh(self):
        """Test token refresh flow"""
        logger.info("\n5. Testing token refresh...")

        try:
            # Use refresh token to get new access token
            from apps.backend.core.security.jwt_rotation import get_jwt_manager
            jwt_manager = await get_jwt_manager()

            new_tokens = await jwt_manager.refresh_access_token(self.refresh_token)
            if new_tokens:
                new_access, new_refresh = new_tokens
                logger.info("  ✓ Token refresh successful")
                logger.info(f"    New access token (first 50 chars): {new_access[:50]}...")

                # Test connection with new token
                url = f"ws://{self.base_url}/ws/roblox?token={new_access}"
                test_ws = await websockets.connect(url)
                logger.info("  ✓ Connected with refreshed token")
                await test_ws.close()

                return True
            else:
                logger.error("  ✗ Token refresh failed")
                return False

        except Exception as e:
            logger.error(f"  ✗ Refresh test failed: {e}")
            return False

    async def cleanup(self):
        """Clean up connections"""
        if self.websocket:
            await self.websocket.close()
            logger.info("\nConnection closed")


async def main():
    """Main test runner"""
    logger.info("=" * 60)
    logger.info("Authenticated Roblox WebSocket Test Suite")
    logger.info("=" * 60)

    tester = AuthenticatedRobloxWebSocketTest()

    # Run test suite
    results = {
        "no_auth": await tester.test_without_auth(),
        "invalid_token": await tester.test_with_invalid_token(),
        "valid_token": await tester.test_with_valid_token(),
        "operations": await tester.test_authenticated_operations(),
        "refresh": await tester.test_token_refresh()
    }

    # Cleanup
    await tester.cleanup()

    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("Test Results Summary:")
    logger.info("=" * 60)

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for test, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        logger.info(f"  {test:20} {status}")

    logger.info("-" * 60)
    logger.info(f"Total: {passed}/{total} tests passed")

    if passed == total:
        logger.info("\n🔒 WebSocket authentication is working correctly!")
    else:
        logger.error("\n⚠️ Some authentication tests failed!")

    logger.info("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())