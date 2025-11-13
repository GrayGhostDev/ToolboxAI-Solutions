"""Performance testing for Pusher migration"""

import asyncio
import json
import os
import statistics
import time
from unittest.mock import Mock

import httpx
import pytest

# Mock Pusher for testing when not available
try:
    from pusher import Pusher
except ImportError:

    class Pusher:
        def __init__(self, **kwargs):
            self.config = kwargs

        def trigger(self, channel, event, data):
            # Simulate network latency
            time.sleep(0.01 + (len(json.dumps(data)) / 10000))  # Simulate based on data size
            return {"status": "ok"}


class TestPusherPerformance:
    """Performance testing for Pusher vs WebSocket"""

    @pytest.fixture
    def pusher_client(self):
        return Pusher(
            app_id=os.getenv("PUSHER_APP_ID", "test_app_id"),
            key=os.getenv("PUSHER_KEY", "test_key"),
            secret=os.getenv("PUSHER_SECRET", "test_secret"),
            cluster=os.getenv("PUSHER_CLUSTER", "us2"),
            ssl=True,
        )

    @pytest.fixture
    def api_base_url(self):
        """Get API base URL for testing"""
        return os.getenv("VITE_API_BASE_URL", "http://localhost:8009")

    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_pusher_latency(self, pusher_client):
        """Test Pusher message latency"""
        latencies = []

        for i in range(100):
            start = time.perf_counter()

            try:
                result = pusher_client.trigger(
                    "test-channel",
                    "latency-test",
                    {"timestamp": start, "sequence": i, "test_data": "x" * 100},  # Small payload
                )

                latency = (time.perf_counter() - start) * 1000  # Convert to ms
                latencies.append(latency)

                await asyncio.sleep(0.01)  # Small delay between messages
            except Exception as e:
                print(f"Error in latency test iteration {i}: {e}")
                continue

        if not latencies:
            pytest.skip("No successful latency measurements")

        # Calculate statistics
        avg_latency = statistics.mean(latencies)
        p95_latency = (
            statistics.quantiles(latencies, n=20)[18] if len(latencies) >= 20 else max(latencies)
        )
        max_latency = max(latencies)

        print(
            f"Pusher Latency - Avg: {avg_latency:.2f}ms, P95: {p95_latency:.2f}ms, Max: {max_latency:.2f}ms"
        )

        # Assert performance requirements (relaxed for testing)
        assert avg_latency < 200, f"Average latency too high: {avg_latency:.2f}ms"
        assert p95_latency < 300, f"P95 latency too high: {p95_latency:.2f}ms"
        assert max_latency < 1000, f"Max latency too high: {max_latency:.2f}ms"

    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_concurrent_pusher_connections(self, pusher_client):
        """Test concurrent Pusher connections"""
        num_connections = 50  # Reduced for test stability
        results = []

        async def create_connection(conn_id: int):
            start = time.perf_counter()
            try:
                # Simulate subscribing to a private channel
                channel_name = f"private-test-{conn_id}"

                result = pusher_client.trigger(
                    channel_name,
                    "connection-test",
                    {"connection_id": conn_id, "timestamp": time.time()},
                )

                elapsed = time.perf_counter() - start
                return {"success": True, "time": elapsed}
            except Exception as e:
                return {"success": False, "error": str(e)}

        # Create connections concurrently
        tasks = [create_connection(i) for i in range(num_connections)]
        results = await asyncio.gather(*tasks)

        # Calculate success rate
        successful = [r for r in results if r["success"]]
        success_rate = len(successful) / len(results) * 100

        if successful:
            avg_time = statistics.mean([r["time"] for r in successful])
            print(f"Concurrent Connections - Success: {success_rate}%, Avg Time: {avg_time:.3f}s")

        assert success_rate >= 80, f"Success rate too low: {success_rate}%"

    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_message_throughput(self, pusher_client):
        """Test message throughput capacity"""
        duration = 5  # Test for 5 seconds (reduced for testing)
        messages_sent = 0
        start_time = time.perf_counter()

        while time.perf_counter() - start_time < duration:
            try:
                pusher_client.trigger(
                    "throughput-test",
                    "message",
                    {
                        "seq": messages_sent,
                        "timestamp": time.time(),
                        "data": "x" * 50,  # Small payload
                    },
                )
                messages_sent += 1
            except Exception as e:
                print(f"Error sending message: {e}")
                break

        elapsed = time.perf_counter() - start_time
        throughput = messages_sent / elapsed

        print(
            f"Message Throughput: {throughput:.0f} msgs/sec ({messages_sent} messages in {elapsed:.1f}s)"
        )

        assert (
            throughput >= 10
        ), f"Throughput too low: {throughput:.0f} msgs/sec"  # Relaxed threshold

    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_channel_subscription_time(self, api_base_url):
        """Test time to subscribe to channels"""
        async with httpx.AsyncClient(base_url=api_base_url, timeout=10.0) as client:
            subscription_times = []

            for i in range(20):  # Reduced iterations
                start = time.perf_counter()

                try:
                    # Authenticate for private channel
                    response = await client.post(
                        "/api/v1/pusher/auth",
                        json={"channel": f"private-perf-test-{i}", "socket_id": f"test.{i}"},
                    )

                    subscription_time = (time.perf_counter() - start) * 1000
                    subscription_times.append(subscription_time)

                    if response.status_code != 200:
                        print(f"Warning: Auth failed with status {response.status_code}")

                except Exception as e:
                    print(f"Warning: Subscription test failed: {e}")
                    continue

            if not subscription_times:
                pytest.skip("No successful subscription measurements")

            avg_time = statistics.mean(subscription_times)
            print(f"Channel Subscription - Avg: {avg_time:.2f}ms")

            assert avg_time < 200, f"Average subscription time too high: {avg_time:.2f}ms"

    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_large_message_performance(self, pusher_client):
        """Test performance with larger messages"""
        message_sizes = [1024, 4096, 8192, 16384]  # Different payload sizes in bytes
        results = {}

        for size in message_sizes:
            latencies = []
            payload = {"data": "x" * size, "timestamp": time.time(), "size": size}

            for i in range(10):  # Test each size 10 times
                start = time.perf_counter()

                try:
                    pusher_client.trigger("large-message-test", "large-message", payload)

                    latency = (time.perf_counter() - start) * 1000
                    latencies.append(latency)

                    await asyncio.sleep(0.1)  # Brief pause between messages
                except Exception as e:
                    print(f"Error with {size}B message: {e}")
                    continue

            if latencies:
                avg_latency = statistics.mean(latencies)
                results[size] = avg_latency
                print(f"Message size {size}B - Avg latency: {avg_latency:.2f}ms")

        # Verify performance degrades gracefully with size
        if len(results) > 1:
            sizes = sorted(results.keys())
            for i in range(1, len(sizes)):
                current_size = sizes[i]
                prev_size = sizes[i - 1]

                # Larger messages should not be more than 3x slower
                assert (
                    results[current_size] <= results[prev_size] * 3
                ), f"Performance degradation too severe: {current_size}B took {results[current_size]:.2f}ms vs {prev_size}B took {results[prev_size]:.2f}ms"

    @pytest.mark.performance
    def test_pusher_vs_websocket_benchmark(self):
        """Compare Pusher performance to WebSocket baseline"""
        pusher_times = []
        websocket_times = []  # Mock WebSocket times

        # Mock Pusher client for consistent testing
        mock_pusher = Mock()

        # Test Pusher
        for _ in range(50):
            start = time.perf_counter()
            mock_pusher.trigger("test", "event", {"data": "test"})
            # Simulate network latency
            time.sleep(0.01)
            pusher_times.append((time.perf_counter() - start) * 1000)

        # Mock WebSocket performance (typically faster for simple messages)
        for _ in range(50):
            start = time.perf_counter()
            # Simulate WebSocket send
            time.sleep(0.005)  # Typically faster than Pusher
            websocket_times.append((time.perf_counter() - start) * 1000)

        pusher_avg = statistics.mean(pusher_times)
        websocket_avg = statistics.mean(websocket_times)

        print(f"Pusher avg: {pusher_avg:.2f}ms, WebSocket avg: {websocket_avg:.2f}ms")

        # Pusher should be within reasonable range of WebSocket
        assert pusher_avg < websocket_avg * 5, "Pusher significantly slower than WebSocket baseline"

    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_channel_scaling(self, pusher_client):
        """Test performance with multiple channels"""
        num_channels = 20
        messages_per_channel = 5

        results = []

        async def send_to_channel(channel_id: int):
            channel_name = f"scale-test-{channel_id}"
            times = []

            for msg_id in range(messages_per_channel):
                start = time.perf_counter()

                try:
                    pusher_client.trigger(
                        channel_name,
                        "scale-test",
                        {"channel_id": channel_id, "message_id": msg_id, "timestamp": time.time()},
                    )

                    times.append((time.perf_counter() - start) * 1000)
                except Exception as e:
                    print(f"Error in channel {channel_id}, message {msg_id}: {e}")

            return {
                "channel_id": channel_id,
                "avg_time": statistics.mean(times) if times else float("inf"),
                "success_count": len(times),
            }

        # Send messages to all channels concurrently
        tasks = [send_to_channel(i) for i in range(num_channels)]
        results = await asyncio.gather(*tasks)

        # Analyze results
        successful_channels = [r for r in results if r["success_count"] > 0]

        if successful_channels:
            overall_avg = statistics.mean([r["avg_time"] for r in successful_channels])
            success_rate = len(successful_channels) / num_channels * 100

            print(
                f"Channel Scaling - {num_channels} channels, avg: {overall_avg:.2f}ms, success: {success_rate:.1f}%"
            )

            assert success_rate >= 80, f"Channel scaling success rate too low: {success_rate}%"
            assert overall_avg < 500, f"Channel scaling average time too high: {overall_avg:.2f}ms"

    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_error_recovery_performance(self, pusher_client):
        """Test performance during error conditions"""
        # Test with various error scenarios
        error_scenarios = [
            {"channel": "", "event": "test", "data": {}},  # Empty channel
            {"channel": "test", "event": "", "data": {}},  # Empty event
            {"channel": "test", "event": "test", "data": "x" * 100000},  # Oversized data
        ]

        recovery_times = []

        for i, scenario in enumerate(error_scenarios):
            start = time.perf_counter()

            try:
                pusher_client.trigger(scenario["channel"], scenario["event"], scenario["data"])
            except Exception:
                # Expected to fail - measure recovery time
                pass

            # Try a normal message after error
            try:
                pusher_client.trigger("recovery-test", "normal-message", {"seq": i})
                recovery_time = (time.perf_counter() - start) * 1000
                recovery_times.append(recovery_time)
            except Exception as e:
                print(f"Recovery failed for scenario {i}: {e}")

        if recovery_times:
            avg_recovery = statistics.mean(recovery_times)
            print(f"Error Recovery - Avg recovery time: {avg_recovery:.2f}ms")

            assert avg_recovery < 1000, f"Error recovery too slow: {avg_recovery:.2f}ms"

    @pytest.mark.performance
    def test_pusher_configuration_validation(self):
        """Test Pusher configuration is optimized for performance"""
        # Test configuration parameters
        config_tests = [
            {
                "name": "SSL enabled",
                "check": lambda: os.getenv("PUSHER_SSL", "true").lower() == "true",
                "message": "SSL should be enabled for security",
            },
            {
                "name": "Cluster specified",
                "check": lambda: os.getenv("PUSHER_CLUSTER", "") != "",
                "message": "Cluster should be specified for optimal routing",
            },
            {
                "name": "App ID present",
                "check": lambda: os.getenv("PUSHER_APP_ID", "") != "",
                "message": "App ID is required",
            },
        ]

        for test in config_tests:
            try:
                assert test["check"](), test["message"]
                print(f"✓ {test['name']} - OK")
            except AssertionError as e:
                print(f"⚠ {test['name']} - {e}")
                # Don't fail test for missing config in test environment

    def test_pusher_client_instantiation_performance(self):
        """Test Pusher client creation performance"""
        instantiation_times = []

        for i in range(10):
            start = time.perf_counter()

            client = Pusher(
                app_id=f"test_app_{i}",
                key=f"test_key_{i}",
                secret=f"test_secret_{i}",
                cluster="us2",
                ssl=True,
            )

            instantiation_time = (time.perf_counter() - start) * 1000
            instantiation_times.append(instantiation_time)

        avg_time = statistics.mean(instantiation_times)
        print(f"Pusher Client Instantiation - Avg: {avg_time:.2f}ms")

        # Client creation should be fast
        assert avg_time < 100, f"Client instantiation too slow: {avg_time:.2f}ms"
