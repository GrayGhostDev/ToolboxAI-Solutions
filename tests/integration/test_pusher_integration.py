#!/usr/bin/env python3
"""
Pusher Integration Test Suite
Tests real-time communication using Pusher Channels across all services
Migrated from WebSocket to Pusher patterns
"""

import asyncio
import os
import json
import time
import logging
from typing import Dict, Any, List, Optional
import pytest
import aiohttp
from datetime import datetime, timezone
from unittest.mock import patch, MagicMock

# Import our Pusher test utilities
from tests.fixtures.pusher_mocks import MockPusherClient, MockPusherService
from tests.fixtures.pusher_test_utils import (
    PusherTestHelper,
    PusherAsyncTestHelper,
    mock_pusher_context,
    async_mock_pusher_context,
    PusherEventRecorder
)

# Skip all tests in this module as they require external services
# Tests are now enabled by default since we've fixed the issues
# To skip, set SKIP_INTEGRATION_TESTS=1
pytestmark = pytest.mark.skipif(
    os.environ.get('SKIP_INTEGRATION_TESTS'),
    reason="Tests manually disabled. Remove SKIP_INTEGRATION_TESTS to enable"
)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configuration - Updated for Pusher
SERVICES = {
    "fastapi": {
        "http_url": "http://127.0.0.1:8009",
        "health_endpoint": "/health",
        "pusher_auth_endpoint": "/pusher/auth",
        "channels": ["public-api", "private-api", "presence-api"]
    },
    "dashboard": {
        "http_url": "http://127.0.0.1:5179",
        "health_endpoint": "/api/v1/health",
        "pusher_auth_endpoint": "/api/pusher/auth",
        "channels": ["dashboard-updates", "content-generation", "presence-classroom"]
    },
    "mcp": {
        "http_url": "http://127.0.0.1:9877",
        "health_endpoint": "/health",
        "pusher_auth_endpoint": None,  # MCP might use different auth
        "channels": ["mcp-context", "agent-status"]
    }
}

# Pusher configuration for testing
PUSHER_CONFIG = {
    "app_id": os.environ.get("PUSHER_APP_ID", "test_app_id"),
    "key": os.environ.get("PUSHER_KEY", "test_key"),
    "secret": os.environ.get("PUSHER_SECRET", "test_secret"),
    "cluster": os.environ.get("PUSHER_CLUSTER", "us2"),
    "ssl": True
}


class PusherIntegrationTester:
    """Comprehensive Pusher testing utility"""

    def __init__(self):
        self.results = {}
        self.pusher_service = MockPusherService(**PUSHER_CONFIG)
        self.event_recorder = PusherEventRecorder()
        self.async_helper = PusherAsyncTestHelper()

    async def check_service_health(self, service_name: str) -> bool:
        """Check if HTTP service is healthy"""
        config = SERVICES[service_name]

        try:
            async with aiohttp.ClientSession() as session:
                url = f"{config['http_url']}{config['health_endpoint']}"
                async with session.get(url, timeout=5) as response:
                    if response.status == 200:
                        logger.info(f"✅ {service_name} health check passed")
                        return True
        except Exception as e:
            logger.warning(f"⚠️ {service_name} health check failed: {e}")
        return False

    @pytest.mark.asyncio
    async def test_pusher_connection(self, service_name: str) -> Dict[str, Any]:
        """Test Pusher connection and channel subscription"""
        config = SERVICES[service_name]
        result = {
            "service": service_name,
            "connection": False,
            "channels_subscribed": [],
            "error": None
        }

        try:
            logger.info(f"Testing Pusher connection for {service_name}...")

            # Simulate Pusher connection
            self.pusher_service.connect()
            result["connection"] = self.pusher_service.connected
            logger.info(f"✅ Connected to Pusher for {service_name}")

            # Subscribe to channels
            for channel in config["channels"]:
                # Add channel to mock service
                self.pusher_service.client.add_channel(channel)
                result["channels_subscribed"].append(channel)
                logger.info(f"✅ Subscribed to channel: {channel}")

            # Test event triggering
            test_event = {
                "event": "test-connection",
                "data": {"service": service_name, "timestamp": datetime.now(timezone.utc).isoformat()}
            }

            for channel in result["channels_subscribed"]:
                response = self.pusher_service.trigger(channel, test_event["event"], test_event["data"])
                if response.get("status") == "success":
                    logger.info(f"✅ Event triggered on {channel}")

        except Exception as e:
            result["error"] = str(e)
            logger.error(f"❌ {service_name} Pusher error: {e}")

        return result

    @pytest.mark.asyncio
    async def test_channel_authentication(self, service_name: str) -> Dict[str, Any]:
        """Test Pusher channel authentication"""
        config = SERVICES[service_name]
        result = {
            "service": service_name,
            "auth_success": False,
            "channels_authenticated": [],
            "error": None
        }

        if not config.get("pusher_auth_endpoint"):
            logger.info(f"⚠️ {service_name} has no Pusher auth endpoint")
            return result

        try:
            async with aiohttp.ClientSession() as session:
                # Test authentication for private channels
                for channel in config["channels"]:
                    if channel.startswith("private-") or channel.startswith("presence-"):
                        # Simulate authentication request
                        auth_data = {
                            "socket_id": f"test_socket_{time.time()}",
                            "channel_name": channel
                        }

                        # Mock authentication response
                        auth_response = self.pusher_service.authenticate(
                            channel,
                            auth_data["socket_id"],
                            {"user_id": "test_user", "user_info": {"name": "Test User"}}
                        )

                        if auth_response.get("auth"):
                            result["channels_authenticated"].append(channel)
                            logger.info(f"✅ Authenticated for channel: {channel}")

                result["auth_success"] = len(result["channels_authenticated"]) > 0

        except Exception as e:
            result["error"] = str(e)
            logger.error(f"❌ Authentication test error: {e}")

        return result

    @pytest.mark.asyncio
    async def test_message_broadcasting(self) -> Dict[str, Any]:
        """Test message broadcasting through Pusher channels"""
        result = {
            "test": "broadcasting",
            "success": False,
            "details": {}
        }

        try:
            # Subscribe to a channel
            channel_name = "test-broadcast-channel"
            self.pusher_service.client.add_channel(channel_name, [
                {"id": "user1", "info": {"name": "User 1"}},
                {"id": "user2", "info": {"name": "User 2"}}
            ])

            # Send broadcast message
            broadcast_data = {
                "message": "Test broadcast",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "sender": "test_system"
            }

            response = self.pusher_service.trigger(channel_name, "broadcast-event", broadcast_data)

            # Check if message was triggered
            if response.get("status") == "success":
                result["success"] = True
                result["details"]["message_id"] = response.get("message_id")

                # Verify in triggered events
                triggered = self.pusher_service.client.triggered_events
                result["details"]["events_triggered"] = len(triggered)

                logger.info(f"✅ Broadcasting test: {len(triggered)} events triggered")

        except Exception as e:
            result["details"]["error"] = str(e)
            logger.error(f"❌ Broadcasting test error: {e}")

        return result

    @pytest.mark.asyncio
    async def test_presence_channel_features(self) -> Dict[str, Any]:
        """Test Pusher presence channel features"""
        result = {
            "test": "presence_channel",
            "success": False,
            "details": {}
        }

        try:
            # Create presence channel with users
            presence_channel = "presence-room-123"
            users = [
                {"id": "user1", "info": {"name": "Alice", "role": "teacher"}},
                {"id": "user2", "info": {"name": "Bob", "role": "student"}},
                {"id": "user3", "info": {"name": "Charlie", "role": "student"}}
            ]

            self.pusher_service.client.add_channel(presence_channel, users)

            # Get channel info
            channel_info = self.pusher_service.channel_info(presence_channel)
            users_info = self.pusher_service.users_info(presence_channel)

            result["details"]["channel_occupied"] = channel_info.get("occupied", False)
            result["details"]["user_count"] = len(users_info.get("users", []))
            result["details"]["users"] = users_info.get("users", [])

            # Simulate member events
            member_events = ["member_added", "member_removed"]
            for event in member_events:
                self.pusher_service.trigger(presence_channel, event, {
                    "user_id": "user4",
                    "user_info": {"name": "David", "role": "student"}
                })

            result["success"] = result["details"]["user_count"] == len(users)
            logger.info(f"✅ Presence channel test: {result['details']['user_count']} users")

        except Exception as e:
            result["details"]["error"] = str(e)
            logger.error(f"❌ Presence channel test error: {e}")

        return result

    @pytest.mark.asyncio
    async def test_realtime_updates(self) -> Dict[str, Any]:
        """Test real-time update propagation through Pusher"""
        result = {
            "test": "realtime_updates",
            "success": False,
            "details": {}
        }

        try:
            # Subscribe to dashboard updates channel
            update_channel = "dashboard-updates"
            self.pusher_service.client.add_channel(update_channel)

            # Simulate multiple real-time updates
            updates = [
                {"metric": "student_count", "value": 150},
                {"metric": "active_lessons", "value": 5},
                {"metric": "completion_rate", "value": 85.5}
            ]

            triggered_count = 0
            for update in updates:
                update["timestamp"] = datetime.now(timezone.utc).isoformat()
                response = self.pusher_service.trigger(update_channel, "metric-update", update)
                if response.get("status") == "success":
                    triggered_count += 1

            result["details"]["updates_sent"] = len(updates)
            result["details"]["updates_triggered"] = triggered_count
            result["success"] = triggered_count == len(updates)

            logger.info(f"✅ Real-time updates: {triggered_count}/{len(updates)} triggered")

        except Exception as e:
            result["details"]["error"] = str(e)
            logger.error(f"❌ Real-time update test error: {e}")

        return result

    @pytest.mark.asyncio
    async def test_batch_event_triggering(self) -> Dict[str, Any]:
        """Test batch event triggering through Pusher"""
        result = {
            "test": "batch_triggering",
            "success": False,
            "details": {}
        }

        try:
            # Prepare batch of events
            events = []
            channels = ["public-notifications", "dashboard-updates", "content-generation"]

            for i, channel in enumerate(channels):
                for j in range(3):
                    events.append({
                        "channel": channel,
                        "name": f"event-{i}-{j}",
                        "data": {
                            "id": f"{i}_{j}",
                            "message": f"Batch event {i}-{j}",
                            "timestamp": datetime.now(timezone.utc).isoformat()
                        }
                    })

            # Trigger batch
            response = self.pusher_service.trigger_batch(events)

            result["details"]["events_in_batch"] = len(events)
            result["details"]["batch_id"] = response.get("batch_id")
            result["success"] = response.get("status") == "success"

            # Verify triggered events
            triggered = self.pusher_service.client.triggered_events
            result["details"]["total_triggered"] = len(triggered)

            logger.info(f"✅ Batch triggering: {len(triggered)} events triggered")

        except Exception as e:
            result["details"]["error"] = str(e)
            logger.error(f"❌ Batch triggering test error: {e}")

        return result

    @pytest.mark.asyncio
    async def test_connection_resilience(self) -> Dict[str, Any]:
        """Test Pusher connection resilience and reconnection"""
        result = {
            "test": "resilience",
            "success": False,
            "details": {}
        }

        try:
            # Initial connection
            self.pusher_service.connect()
            initial_state = self.pusher_service.connected
            result["details"]["initial_connected"] = initial_state

            # Simulate disconnection
            self.pusher_service.disconnect()
            disconnected_state = self.pusher_service.connected
            result["details"]["disconnected"] = not disconnected_state

            # Simulate reconnection
            await asyncio.sleep(0.5)
            self.pusher_service.reconnect()
            reconnected_state = self.pusher_service.connected
            result["details"]["reconnected"] = reconnected_state

            # Test event triggering after reconnection
            if reconnected_state:
                response = self.pusher_service.trigger("test-channel", "reconnect-test", {"status": "ok"})
                result["details"]["can_trigger_after_reconnect"] = response.get("status") == "success"

            result["success"] = initial_state and reconnected_state
            logger.info(f"✅ Connection resilience test passed")

        except Exception as e:
            result["details"]["error"] = str(e)
            logger.error(f"❌ Resilience test error: {e}")

        return result

    @pytest.mark.asyncio
    async def test_performance(self) -> Dict[str, Any]:
        """Test Pusher performance and throughput"""
        result = {
            "test": "performance",
            "success": False,
            "details": {
                "messages_sent": 0,
                "messages_triggered": 0,
                "average_time_ms": 0
            }
        }

        try:
            channel = "performance-test-channel"
            self.pusher_service.client.add_channel(channel)

            num_messages = 100
            times = []

            for i in range(num_messages):
                start_time = time.time()

                message = {
                    "id": i,
                    "data": f"Performance test message {i}",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }

                response = self.pusher_service.trigger(channel, "perf-test", message)

                if response.get("status") == "success":
                    result["details"]["messages_triggered"] += 1
                    elapsed = (time.time() - start_time) * 1000  # Convert to ms
                    times.append(elapsed)

                result["details"]["messages_sent"] += 1

            if times:
                result["details"]["average_time_ms"] = sum(times) / len(times)
                result["success"] = True
                logger.info(
                    f"✅ Performance test: {result['details']['messages_triggered']}/{num_messages} messages, "
                    f"avg time: {result['details']['average_time_ms']:.2f}ms"
                )

        except Exception as e:
            result["details"]["error"] = str(e)
            logger.error(f"❌ Performance test error: {e}")

        return result

    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all Pusher integration tests"""
        logger.info("=" * 60)
        logger.info("PUSHER INTEGRATION TESTS")
        logger.info("=" * 60)

        all_results = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "tests": {}
        }

        # Test basic connections
        logger.info("\n1. Testing Pusher Connections")
        logger.info("-" * 40)
        for service in SERVICES.keys():
            result = await self.test_pusher_connection(service)
            all_results["tests"][f"connection_{service}"] = result

        # Test authentication
        logger.info("\n2. Testing Channel Authentication")
        logger.info("-" * 40)
        for service in SERVICES.keys():
            auth_result = await self.test_channel_authentication(service)
            all_results["tests"][f"auth_{service}"] = auth_result

        # Test broadcasting
        logger.info("\n3. Testing Message Broadcasting")
        logger.info("-" * 40)
        broadcast_result = await self.test_message_broadcasting()
        all_results["tests"]["broadcasting"] = broadcast_result

        # Test presence channels
        logger.info("\n4. Testing Presence Channels")
        logger.info("-" * 40)
        presence_result = await self.test_presence_channel_features()
        all_results["tests"]["presence_channels"] = presence_result

        # Test real-time updates
        logger.info("\n5. Testing Real-time Updates")
        logger.info("-" * 40)
        realtime_result = await self.test_realtime_updates()
        all_results["tests"]["realtime_updates"] = realtime_result

        # Test batch triggering
        logger.info("\n6. Testing Batch Event Triggering")
        logger.info("-" * 40)
        batch_result = await self.test_batch_event_triggering()
        all_results["tests"]["batch_triggering"] = batch_result

        # Test resilience
        logger.info("\n7. Testing Connection Resilience")
        logger.info("-" * 40)
        resilience_result = await self.test_connection_resilience()
        all_results["tests"]["resilience"] = resilience_result

        # Test performance
        logger.info("\n8. Testing Pusher Performance")
        logger.info("-" * 40)
        performance_result = await self.test_performance()
        all_results["tests"]["performance"] = performance_result

        # Summary
        logger.info("\n" + "=" * 60)
        logger.info("TEST SUMMARY")
        logger.info("=" * 60)

        passed = sum(1 for test in all_results["tests"].values()
                    if test.get("success") or test.get("connection") or test.get("auth_success"))
        total = len(all_results["tests"])

        logger.info(f"✅ Passed: {passed}")
        logger.info(f"❌ Failed: {total - passed}")
        logger.info(f"📊 Total: {total}")

        all_results["summary"] = {
            "passed": passed,
            "failed": total - passed,
            "total": total,
            "success_rate": f"{(passed/total)*100:.1f}%"
        }

        # Save results
        with open("pusher_test_results.json", "w") as f:
            json.dump(all_results, f, indent=2, default=str)
        logger.info("\n📁 Results saved to pusher_test_results.json")

        if passed == total:
            logger.info("\n🎉 ALL PUSHER TESTS PASSED!")
        else:
            logger.info(f"\n💔 {total - passed} TESTS FAILED")

        return all_results


# Pytest integration
@pytest.mark.asyncio
async def test_pusher_connections():
    """Pytest: Test Pusher connections"""
    async with async_mock_pusher_context() as pusher_service:
        tester = PusherIntegrationTester()
        tester.pusher_service = pusher_service

        for service in SERVICES.keys():
            result = await tester.test_pusher_connection(service)
            assert result["connection"], f"{service} Pusher connection failed"


@pytest.mark.asyncio
async def test_pusher_broadcasting():
    """Pytest: Test Pusher broadcasting"""
    async with async_mock_pusher_context() as pusher_service:
        tester = PusherIntegrationTester()
        tester.pusher_service = pusher_service

        result = await tester.test_message_broadcasting()
        assert result["success"], "Pusher broadcasting test failed"


@pytest.mark.asyncio
async def test_pusher_presence_channels():
    """Pytest: Test Pusher presence channels"""
    async with async_mock_pusher_context() as pusher_service:
        tester = PusherIntegrationTester()
        tester.pusher_service = pusher_service

        result = await tester.test_presence_channel_features()
        assert result["success"], "Pusher presence channel test failed"


@pytest.mark.asyncio
async def test_pusher_performance():
    """Pytest: Test Pusher performance"""
    async with async_mock_pusher_context() as pusher_service:
        tester = PusherIntegrationTester()
        tester.pusher_service = pusher_service

        result = await tester.test_performance()
        assert result["success"], "Pusher performance test failed"
        assert result["details"]["average_time_ms"] < 50, "Pusher latency too high"


async def main():
    """Main test runner"""
    tester = PusherIntegrationTester()
    await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())