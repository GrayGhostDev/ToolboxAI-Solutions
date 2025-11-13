"""
Performance Tests for Pusher Implementation

Tests various performance aspects of the Pusher real-time system:
- Message throughput under load
- Concurrent connection handling
- Channel subscription limits
- Message size limits
- Memory usage patterns
- Connection recovery performance
"""

import asyncio
import json
import statistics
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from typing import Any

import psutil
import pytest


@dataclass
class PerformanceMetrics:
    """Performance measurement data structure"""

    operation: str
    duration: float
    success: bool
    error: str = None
    memory_usage: float = 0
    cpu_usage: float = 0
    throughput: float = 0
    latency: float = 0


class PerformanceMonitor:
    """Monitor system performance during tests"""

    def __init__(self):
        self.process = psutil.Process()
        self.start_time = None
        self.start_memory = None
        self.start_cpu_times = None

    def start(self):
        """Start monitoring"""
        self.start_time = time.time()
        self.start_memory = self.process.memory_info().rss
        self.start_cpu_times = self.process.cpu_times()

    def stop(self) -> dict[str, float]:
        """Stop monitoring and return metrics"""
        end_time = time.time()
        end_memory = self.process.memory_info().rss
        end_cpu_times = self.process.cpu_times()

        duration = end_time - self.start_time
        memory_delta = end_memory - self.start_memory
        cpu_delta = (end_cpu_times.user - self.start_cpu_times.user) + (
            end_cpu_times.system - self.start_cpu_times.system
        )

        return {
            "duration": duration,
            "memory_delta_mb": memory_delta / (1024 * 1024),
            "cpu_usage_percent": (cpu_delta / duration) * 100 if duration > 0 else 0,
            "current_memory_mb": end_memory / (1024 * 1024),
        }


class MockPusherService:
    """High-performance mock Pusher service for testing"""

    def __init__(self):
        self.connections = {}
        self.channels = {}
        self.message_count = 0
        self.error_rate = 0.0
        self.latency_ms = 0

    async def connect(self, connection_id: str) -> bool:
        """Mock connection"""
        await asyncio.sleep(self.latency_ms / 1000)
        if self.error_rate > 0 and time.time() % 1 < self.error_rate:
            raise Exception("Connection failed")
        self.connections[connection_id] = time.time()
        return True

    async def disconnect(self, connection_id: str):
        """Mock disconnection"""
        self.connections.pop(connection_id, None)

    async def subscribe(self, connection_id: str, channel: str) -> bool:
        """Mock channel subscription"""
        await asyncio.sleep(self.latency_ms / 1000)
        if channel not in self.channels:
            self.channels[channel] = set()
        self.channels[channel].add(connection_id)
        return True

    async def send_message(self, channel: str, data: dict[str, Any]) -> bool:
        """Mock message sending"""
        await asyncio.sleep(self.latency_ms / 1000)
        if self.error_rate > 0 and time.time() % 1 < self.error_rate:
            raise Exception("Send failed")
        self.message_count += 1
        return True


class TestPusherPerformance:
    """Performance tests for Pusher functionality"""

    @pytest.fixture
    def pusher_service(self):
        """Mock Pusher service for performance testing"""
        return MockPusherService()

    @pytest.fixture
    def performance_monitor(self):
        """Performance monitoring fixture"""
        return PerformanceMonitor()

    @pytest.mark.asyncio
    async def test_message_throughput_single_channel(self, pusher_service, performance_monitor):
        """Test message throughput on a single channel"""
        message_count = 1000
        channel = "performance-test-channel"

        # Connect and subscribe
        await pusher_service.connect("test-connection")
        await pusher_service.subscribe("test-connection", channel)

        # Measure throughput
        performance_monitor.start()

        tasks = []
        for i in range(message_count):
            task = pusher_service.send_message(
                channel, {"id": f"msg-{i}", "data": f"test message {i}", "timestamp": time.time()}
            )
            tasks.append(task)

        # Execute all messages concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)

        metrics = performance_monitor.stop()

        # Analyze results
        successful_sends = sum(1 for r in results if not isinstance(r, Exception))
        throughput = successful_sends / metrics["duration"]

        assert successful_sends >= message_count * 0.95  # 95% success rate
        assert throughput >= 100  # At least 100 messages per second
        assert metrics["memory_delta_mb"] < 100  # Memory usage under 100MB

        print(f"Throughput: {throughput:.2f} messages/second")
        print(f"Memory usage: {metrics['memory_delta_mb']:.2f} MB")
        print(f"CPU usage: {metrics['cpu_usage_percent']:.2f}%")

    @pytest.mark.asyncio
    async def test_concurrent_connections_scaling(self, pusher_service, performance_monitor):
        """Test concurrent connection handling"""
        connection_counts = [10, 50, 100, 500, 1000]
        results = {}

        for conn_count in connection_counts:
            performance_monitor.start()

            # Create concurrent connections
            tasks = []
            for i in range(conn_count):
                task = pusher_service.connect(f"connection-{i}")
                tasks.append(task)

            connection_results = await asyncio.gather(*tasks, return_exceptions=True)
            metrics = performance_monitor.stop()

            successful_connections = sum(
                1 for r in connection_results if not isinstance(r, Exception)
            )
            connection_rate = successful_connections / metrics["duration"]

            results[conn_count] = {
                "success_rate": successful_connections / conn_count,
                "connection_rate": connection_rate,
                "memory_usage": metrics["memory_delta_mb"],
                "cpu_usage": metrics["cpu_usage_percent"],
            }

            # Cleanup connections
            for i in range(conn_count):
                await pusher_service.disconnect(f"connection-{i}")

            # Verify performance doesn't degrade significantly
            assert successful_connections >= conn_count * 0.9  # 90% success rate
            assert connection_rate >= min(conn_count / 10, 50)  # Reasonable connection rate

        # Print scaling results
        print("\nConnection Scaling Results:")
        for conn_count, result in results.items():
            print(
                f"{conn_count} connections: "
                f"{result['success_rate']:.2%} success, "
                f"{result['connection_rate']:.1f} conn/sec, "
                f"{result['memory_usage']:.1f} MB"
            )

    @pytest.mark.asyncio
    async def test_channel_subscription_limits(self, pusher_service, performance_monitor):
        """Test channel subscription performance limits"""
        connection_id = "test-connection"
        channel_count = 1000

        await pusher_service.connect(connection_id)

        performance_monitor.start()

        # Subscribe to many channels
        tasks = []
        for i in range(channel_count):
            task = pusher_service.subscribe(connection_id, f"channel-{i}")
            tasks.append(task)

        subscription_results = await asyncio.gather(*tasks, return_exceptions=True)
        metrics = performance_monitor.stop()

        successful_subscriptions = sum(
            1 for r in subscription_results if not isinstance(r, Exception)
        )
        subscription_rate = successful_subscriptions / metrics["duration"]

        assert successful_subscriptions >= channel_count * 0.95  # 95% success rate
        assert subscription_rate >= 50  # At least 50 subscriptions per second
        assert metrics["memory_delta_mb"] < 200  # Memory usage under 200MB

        print(f"Subscription rate: {subscription_rate:.2f} subscriptions/second")
        print(f"Memory usage: {metrics['memory_delta_mb']:.2f} MB")

    @pytest.mark.asyncio
    async def test_message_size_limits(self, pusher_service, performance_monitor):
        """Test performance with various message sizes"""
        channel = "size-test-channel"
        await pusher_service.connect("test-connection")
        await pusher_service.subscribe("test-connection", channel)

        # Test different message sizes (in KB)
        message_sizes = [1, 10, 50, 100, 500, 1000]
        size_results = {}

        for size_kb in message_sizes:
            # Create message of specified size
            message_data = {
                "id": f"size-test-{size_kb}kb",
                "data": "x" * (size_kb * 1024),  # Create payload of specified size
                "metadata": {"size_kb": size_kb},
            }

            performance_monitor.start()

            # Send 10 messages of this size
            tasks = []
            for i in range(10):
                task = pusher_service.send_message(channel, message_data)
                tasks.append(task)

            results = await asyncio.gather(*tasks, return_exceptions=True)
            metrics = performance_monitor.stop()

            successful_sends = sum(1 for r in results if not isinstance(r, Exception))
            avg_latency = metrics["duration"] / len(tasks)

            size_results[size_kb] = {
                "success_rate": successful_sends / len(tasks),
                "avg_latency_ms": avg_latency * 1000,
                "throughput_mb_per_sec": (size_kb * successful_sends / 1024) / metrics["duration"],
            }

            # Verify acceptable performance
            assert successful_sends >= 8  # At least 80% success
            assert avg_latency < 1.0  # Average latency under 1 second

        # Print size performance results
        print("\nMessage Size Performance:")
        for size_kb, result in size_results.items():
            print(
                f"{size_kb}KB messages: "
                f"{result['success_rate']:.2%} success, "
                f"{result['avg_latency_ms']:.1f}ms latency, "
                f"{result['throughput_mb_per_sec']:.2f} MB/sec"
            )

    @pytest.mark.asyncio
    async def test_burst_traffic_handling(self, pusher_service, performance_monitor):
        """Test handling of burst traffic patterns"""
        channel = "burst-test-channel"
        await pusher_service.connect("test-connection")
        await pusher_service.subscribe("test-connection", channel)

        # Simulate traffic bursts
        burst_sizes = [10, 50, 100, 200, 500]
        burst_results = {}

        for burst_size in burst_sizes:
            performance_monitor.start()

            # Send burst of messages
            tasks = []
            for i in range(burst_size):
                task = pusher_service.send_message(
                    channel,
                    {"id": f"burst-{i}", "burst_size": burst_size, "timestamp": time.time()},
                )
                tasks.append(task)

            # Execute all at once (burst)
            results = await asyncio.gather(*tasks, return_exceptions=True)
            metrics = performance_monitor.stop()

            successful_sends = sum(1 for r in results if not isinstance(r, Exception))
            burst_throughput = successful_sends / metrics["duration"]

            burst_results[burst_size] = {
                "success_rate": successful_sends / burst_size,
                "throughput": burst_throughput,
                "duration": metrics["duration"],
                "memory_usage": metrics["memory_delta_mb"],
            }

            # Verify burst handling
            assert successful_sends >= burst_size * 0.9  # 90% success rate
            assert metrics["duration"] < 5.0  # Complete within 5 seconds

        # Print burst results
        print("\nBurst Traffic Results:")
        for burst_size, result in burst_results.items():
            print(
                f"Burst {burst_size}: "
                f"{result['success_rate']:.2%} success, "
                f"{result['throughput']:.1f} msg/sec, "
                f"{result['duration']:.2f}s"
            )

    @pytest.mark.asyncio
    async def test_connection_recovery_performance(self, pusher_service, performance_monitor):
        """Test connection recovery speed and reliability"""
        connection_id = "recovery-test-connection"
        recovery_times = []

        for attempt in range(10):
            # Connect
            await pusher_service.connect(connection_id)

            # Simulate disconnection
            await pusher_service.disconnect(connection_id)

            # Measure reconnection time
            performance_monitor.start()
            await pusher_service.connect(connection_id)
            metrics = performance_monitor.stop()

            recovery_times.append(metrics["duration"])

        # Analyze recovery performance
        avg_recovery_time = statistics.mean(recovery_times)
        max_recovery_time = max(recovery_times)
        min_recovery_time = min(recovery_times)

        assert avg_recovery_time < 2.0  # Average recovery under 2 seconds
        assert max_recovery_time < 5.0  # Max recovery under 5 seconds
        assert min_recovery_time < 1.0  # Min recovery under 1 second

        print(f"\nConnection Recovery Performance:")
        print(f"Average: {avg_recovery_time:.2f}s")
        print(f"Min: {min_recovery_time:.2f}s")
        print(f"Max: {max_recovery_time:.2f}s")

    @pytest.mark.asyncio
    async def test_memory_leak_detection(self, pusher_service, performance_monitor):
        """Test for memory leaks during extended operation"""
        channel = "memory-test-channel"
        connection_id = "memory-test-connection"

        await pusher_service.connect(connection_id)
        await pusher_service.subscribe(connection_id, channel)

        initial_memory = psutil.Process().memory_info().rss
        memory_samples = [initial_memory]

        # Run extended operation cycles
        for cycle in range(10):
            performance_monitor.start()

            # Send batch of messages
            tasks = []
            for i in range(100):
                task = pusher_service.send_message(
                    channel, {"cycle": cycle, "message": i, "data": "x" * 1024}  # 1KB payload
                )
                tasks.append(task)

            await asyncio.gather(*tasks)

            # Sample memory usage
            current_memory = psutil.Process().memory_info().rss
            memory_samples.append(current_memory)

            # Small delay between cycles
            await asyncio.sleep(0.1)

        # Analyze memory trend
        memory_trend = []
        for i in range(1, len(memory_samples)):
            memory_delta = memory_samples[i] - memory_samples[i - 1]
            memory_trend.append(memory_delta)

        # Check for consistent memory growth (potential leak)
        positive_deltas = sum(1 for delta in memory_trend if delta > 0)
        avg_growth = statistics.mean(memory_trend)

        # Memory should not consistently grow
        assert positive_deltas < len(memory_trend) * 0.8  # Less than 80% positive growth
        assert avg_growth < 1024 * 1024  # Less than 1MB average growth per cycle

        print(f"\nMemory Leak Detection:")
        print(f"Initial memory: {initial_memory / (1024*1024):.2f} MB")
        print(f"Final memory: {memory_samples[-1] / (1024*1024):.2f} MB")
        print(f"Average growth per cycle: {avg_growth / 1024:.2f} KB")

    def test_cpu_usage_under_load(self, pusher_service):
        """Test CPU usage under sustained load"""

        def cpu_intensive_task():
            """Simulate CPU-intensive message processing"""
            start_time = time.time()
            message_count = 0

            while time.time() - start_time < 10:  # Run for 10 seconds
                # Simulate message processing
                data = json.dumps({"message": f"test-{message_count}", "timestamp": time.time()})
                json.loads(data)  # Parse back (CPU work)
                message_count += 1

            return message_count

        # Monitor CPU usage during load
        initial_cpu_percent = psutil.cpu_percent(interval=1)

        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = [executor.submit(cpu_intensive_task) for _ in range(4)]

            # Sample CPU usage during execution
            cpu_samples = []
            start_time = time.time()

            while any(not f.done() for f in futures):
                cpu_samples.append(psutil.cpu_percent(interval=0.5))
                if time.time() - start_time > 15:  # Safety timeout
                    break

            # Wait for completion
            total_messages = sum(f.result() for f in as_completed(futures, timeout=5))

        avg_cpu_usage = statistics.mean(cpu_samples) if cpu_samples else 0
        max_cpu_usage = max(cpu_samples) if cpu_samples else 0

        # Verify reasonable CPU usage
        assert avg_cpu_usage < 90  # Average CPU under 90%
        assert max_cpu_usage < 100  # Max CPU should not hit 100%
        assert total_messages > 0  # Some work was completed

        print(f"\nCPU Usage Under Load:")
        print(f"Initial CPU: {initial_cpu_percent:.1f}%")
        print(f"Average CPU: {avg_cpu_usage:.1f}%")
        print(f"Max CPU: {max_cpu_usage:.1f}%")
        print(f"Total messages processed: {total_messages}")

    @pytest.mark.asyncio
    async def test_latency_distribution(self, pusher_service, performance_monitor):
        """Test message latency distribution"""
        channel = "latency-test-channel"
        await pusher_service.connect("test-connection")
        await pusher_service.subscribe("test-connection", channel)

        latencies = []
        message_count = 100

        for i in range(message_count):
            start_time = time.time()

            await pusher_service.send_message(
                channel, {"id": f"latency-test-{i}", "timestamp": start_time}
            )

            end_time = time.time()
            latency = (end_time - start_time) * 1000  # Convert to milliseconds
            latencies.append(latency)

        # Calculate latency statistics
        avg_latency = statistics.mean(latencies)
        median_latency = statistics.median(latencies)
        p95_latency = sorted(latencies)[int(0.95 * len(latencies))]
        p99_latency = sorted(latencies)[int(0.99 * len(latencies))]

        # Verify acceptable latency
        assert avg_latency < 100  # Average under 100ms
        assert median_latency < 50  # Median under 50ms
        assert p95_latency < 200  # 95th percentile under 200ms
        assert p99_latency < 500  # 99th percentile under 500ms

        print(f"\nLatency Distribution:")
        print(f"Average: {avg_latency:.2f}ms")
        print(f"Median: {median_latency:.2f}ms")
        print(f"95th percentile: {p95_latency:.2f}ms")
        print(f"99th percentile: {p99_latency:.2f}ms")


class TestPusherStressTest:
    """Stress tests for extreme conditions"""

    @pytest.mark.asyncio
    async def test_extreme_concurrent_connections(self):
        """Test with very high connection count"""
        pusher_service = MockPusherService()
        connection_count = 5000

        # Set lower latency for stress test
        pusher_service.latency_ms = 1

        start_time = time.time()

        # Create connections in batches to avoid overwhelming
        batch_size = 100
        successful_connections = 0

        for batch_start in range(0, connection_count, batch_size):
            batch_end = min(batch_start + batch_size, connection_count)

            tasks = []
            for i in range(batch_start, batch_end):
                task = pusher_service.connect(f"stress-connection-{i}")
                tasks.append(task)

            results = await asyncio.gather(*tasks, return_exceptions=True)
            successful_connections += sum(1 for r in results if not isinstance(r, Exception))

            # Small delay between batches
            await asyncio.sleep(0.01)

        end_time = time.time()
        duration = end_time - start_time

        success_rate = successful_connections / connection_count
        connection_rate = successful_connections / duration

        # Should handle high load reasonably well
        assert success_rate >= 0.8  # 80% success rate under stress
        assert connection_rate >= 100  # At least 100 connections per second

        print(f"\nStress Test Results:")
        print(f"Connections: {successful_connections}/{connection_count}")
        print(f"Success rate: {success_rate:.2%}")
        print(f"Connection rate: {connection_rate:.1f} conn/sec")

    @pytest.mark.asyncio
    async def test_message_flood_resilience(self):
        """Test resilience against message flooding"""
        pusher_service = MockPusherService()
        channel = "flood-test-channel"

        await pusher_service.connect("flood-connection")
        await pusher_service.subscribe("flood-connection", channel)

        # Flood with messages
        message_count = 10000
        pusher_service.latency_ms = 0  # Remove artificial latency

        start_time = time.time()

        tasks = []
        for i in range(message_count):
            task = pusher_service.send_message(
                channel, {"flood_id": i, "data": f"flood message {i}"}
            )
            tasks.append(task)

        # Execute flood
        results = await asyncio.gather(*tasks, return_exceptions=True)

        end_time = time.time()
        duration = end_time - start_time

        successful_sends = sum(1 for r in results if not isinstance(r, Exception))
        throughput = successful_sends / duration

        # Should handle message flood
        assert successful_sends >= message_count * 0.7  # 70% success under flood
        assert throughput >= 500  # At least 500 messages per second

        print(f"\nMessage Flood Test:")
        print(f"Messages sent: {successful_sends}/{message_count}")
        print(f"Throughput: {throughput:.1f} msg/sec")
        print(f"Duration: {duration:.2f} seconds")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
