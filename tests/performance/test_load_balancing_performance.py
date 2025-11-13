"""
Performance Testing Suite for Load Balancing

Comprehensive tests for validating load balancing performance:
- Circuit breaker effectiveness
- Rate limiting accuracy
- Database replica routing
- WebSocket clustering
- Edge caching hit rates
- Global routing latency
"""

import asyncio
import random
import statistics
import time

import aioredis
import numpy as np
import pytest
from apps.backend.core.websocket_cluster import WebSocketCluster
from database.replica_router import ConsistencyLevel, ReplicaRouter
from locust import HttpUser, between, task
from locust.env import Environment
from locust.log import setup_logging

from apps.backend.core.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerConfig,
)
from apps.backend.core.edge_cache import CacheTier, EdgeCache
from apps.backend.core.global_load_balancer import (
    GeographicLocation,
    GlobalLoadBalancer,
    HealthCheck,
    Region,
    RegionCode,
    RoutingPolicy,
    TrafficPolicy,
)
from apps.backend.core.rate_limiter import RateLimitConfig, RateLimiter


class LoadBalancingUser(HttpUser):
    """Simulated user for load testing"""

    wait_time = between(0.5, 2)

    def on_start(self):
        """Initialize user session"""
        self.session_id = f"user_{self.environment.runner.user_count}"
        self.region = random.choice(["us-east", "eu-west", "ap-south"])

    @task(10)
    def read_operation(self):
        """Simulate read operations"""
        response = self.client.get(
            "/api/v1/content/list", headers={"X-Session-ID": self.session_id}
        )

    @task(5)
    def write_operation(self):
        """Simulate write operations"""
        response = self.client.post(
            "/api/v1/content/create",
            json={"title": "Test", "content": "Content"},
            headers={"X-Session-ID": self.session_id},
        )

    @task(3)
    def cached_operation(self):
        """Simulate cached requests"""
        response = self.client.get(
            "/api/v1/static/resource", headers={"X-Session-ID": self.session_id}
        )

    @task(1)
    def websocket_operation(self):
        """Simulate WebSocket connections"""
        # In real test, would establish WebSocket connection
        response = self.client.get("/ws/connect", headers={"X-Session-ID": self.session_id})


class TestCircuitBreakerPerformance:
    """Performance tests for circuit breaker"""

    @pytest.mark.asyncio
    async def test_circuit_breaker_under_load(self):
        """Test circuit breaker behavior under high load"""
        config = CircuitBreakerConfig(
            failure_threshold=10, success_threshold=5, reset_timeout=5.0, timeout=1.0
        )
        breaker = CircuitBreaker("test_service", config)

        # Simulate mixed success/failure scenario
        results = {"success": 0, "failure": 0, "rejected": 0}
        latencies = []

        async def failing_operation():
            if random.random() < 0.3:  # 30% failure rate
                raise Exception("Service error")
            await asyncio.sleep(random.uniform(0.01, 0.1))
            return "success"

        # Run 1000 operations
        tasks = []
        for _ in range(1000):

            async def single_operation():
                start = time.time()
                try:
                    result = await breaker.call(failing_operation)
                    results["success"] += 1
                except Exception as e:
                    if "Circuit breaker" in str(e):
                        results["rejected"] += 1
                    else:
                        results["failure"] += 1
                latencies.append((time.time() - start) * 1000)

            tasks.append(single_operation())

        # Execute all operations
        await asyncio.gather(*tasks, return_exceptions=True)

        # Analyze results
        assert results["rejected"] > 0, "Circuit breaker should reject some requests"
        assert results["success"] > 500, "Should have reasonable success rate"

        # Check latency
        p50 = statistics.median(latencies)
        p95 = np.percentile(latencies, 95)
        p99 = np.percentile(latencies, 99)

        print(f"\nCircuit Breaker Performance:")
        print(f"  Success: {results['success']}")
        print(f"  Failures: {results['failure']}")
        print(f"  Rejected: {results['rejected']}")
        print(f"  P50 latency: {p50:.2f}ms")
        print(f"  P95 latency: {p95:.2f}ms")
        print(f"  P99 latency: {p99:.2f}ms")

        # Performance assertions
        assert p50 < 100, "P50 latency should be under 100ms"
        assert p99 < 500, "P99 latency should be under 500ms"


class TestRateLimiterPerformance:
    """Performance tests for rate limiting"""

    @pytest.mark.asyncio
    async def test_rate_limiter_accuracy(self):
        """Test rate limiter accuracy under concurrent load"""
        redis_client = await aioredis.from_url("redis://localhost:6379/15")

        config = RateLimitConfig(requests_per_second=100, burst_size=10)
        limiter = RateLimiter(redis_client, config)

        # Track results
        results = {"allowed": 0, "rejected": 0}
        request_times = []

        # Simulate 1000 requests over 5 seconds
        start_time = time.time()

        async def make_request(user_id: str):
            result = await limiter.check_rate_limit(user_id)
            if result.allowed:
                results["allowed"] += 1
                request_times.append(time.time() - start_time)
            else:
                results["rejected"] += 1

        # Generate requests with varying rates
        tasks = []
        for i in range(1000):
            # Use 10 different users
            user_id = f"user_{i % 10}"
            tasks.append(make_request(user_id))

            # Add some delay to spread over time
            if i % 50 == 0:
                await asyncio.sleep(0.1)

        await asyncio.gather(*tasks)

        duration = time.time() - start_time

        # Calculate actual rate
        actual_rate = results["allowed"] / duration
        expected_rate = config.requests_per_second * 10  # 10 users

        print(f"\nRate Limiter Performance:")
        print(f"  Duration: {duration:.2f}s")
        print(f"  Allowed: {results['allowed']}")
        print(f"  Rejected: {results['rejected']}")
        print(f"  Actual rate: {actual_rate:.2f} req/s")
        print(f"  Expected rate: {expected_rate:.2f} req/s")
        print(f"  Accuracy: {abs(1 - actual_rate/expected_rate) * 100:.2f}%")

        # Assert accuracy within 10%
        assert abs(actual_rate - expected_rate) / expected_rate < 0.1

        await redis_client.close()


class TestDatabaseReplicaPerformance:
    """Performance tests for database replica routing"""

    @pytest.mark.asyncio
    async def test_replica_routing_distribution(self):
        """Test load distribution across replicas"""
        primary_url = "postgresql://user:pass@primary:5432/db"
        replica_urls = [
            "postgresql://user:pass@replica1:5432/db",
            "postgresql://user:pass@replica2:5432/db",
            "postgresql://user:pass@replica3:5432/db",
        ]

        router = ReplicaRouter(primary_url, replica_urls)
        await router.start()

        # Track routing decisions
        routing_stats = {"primary": 0, "replicas": {}}

        # Simulate 1000 queries
        for _ in range(1000):
            consistency = random.choice(
                [
                    ConsistencyLevel.EVENTUAL,
                    ConsistencyLevel.EVENTUAL,  # Weight towards eventual
                    ConsistencyLevel.BOUNDED_STALENESS,
                    ConsistencyLevel.STRONG,
                ]
            )

            # Mock the routing decision tracking
            replica = router._select_replica(consistency)
            if replica is None:
                routing_stats["primary"] += 1
            else:
                if replica not in routing_stats["replicas"]:
                    routing_stats["replicas"][replica] = 0
                routing_stats["replicas"][replica] += 1

        # Analyze distribution
        total_queries = 1000
        primary_percentage = (routing_stats["primary"] / total_queries) * 100

        print(f"\nReplica Routing Distribution:")
        print(f"  Primary: {routing_stats['primary']} ({primary_percentage:.1f}%)")
        for replica, count in routing_stats["replicas"].items():
            percentage = (count / total_queries) * 100
            print(f"  {replica}: {count} ({percentage:.1f}%)")

        # Assert reasonable distribution
        assert (
            primary_percentage < 30
        ), "Primary should handle less than 30% with eventual consistency"

        # Check replica balance (should be relatively even)
        if routing_stats["replicas"]:
            counts = list(routing_stats["replicas"].values())
            avg = statistics.mean(counts)
            std_dev = statistics.stdev(counts) if len(counts) > 1 else 0
            cv = (std_dev / avg) * 100 if avg > 0 else 0
            print(f"  Replica balance CV: {cv:.1f}%")
            assert cv < 20, "Replicas should be balanced (CV < 20%)"

        await router.stop()


class TestEdgeCachePerformance:
    """Performance tests for edge caching"""

    @pytest.mark.asyncio
    async def test_cache_hit_rate(self):
        """Test cache hit rate and latency improvement"""
        cache = EdgeCache(redis_url="redis://localhost:6379", default_ttl=300)
        await cache.initialize()

        # Warm up cache with common requests
        warm_up_keys = [f"cache:resource:{i}" for i in range(100)]
        for key in warm_up_keys:
            await cache.set(key, f"data_{key}".encode(), CacheTier.EDGE)

        # Simulate mixed workload
        hit_latencies = []
        miss_latencies = []

        for _ in range(1000):
            key = f"cache:resource:{random.randint(0, 200)}"

            start = time.time()
            result = await cache.get(key, CacheTier.EDGE)
            latency = (time.time() - start) * 1000

            if result:
                hit_latencies.append(latency)
            else:
                miss_latencies.append(latency)
                # Simulate origin fetch and cache
                await asyncio.sleep(random.uniform(0.05, 0.1))
                await cache.set(key, f"data_{key}".encode(), CacheTier.EDGE)

        # Calculate metrics
        metrics = cache.get_metrics()
        edge_metrics = metrics[CacheTier.EDGE.value]

        print(f"\nEdge Cache Performance:")
        print(f"  Hit rate: {edge_metrics['hit_rate']:.1f}%")
        print(f"  Hits: {edge_metrics['hits']}")
        print(f"  Misses: {edge_metrics['misses']}")

        if hit_latencies:
            print(f"  Hit latency P50: {statistics.median(hit_latencies):.2f}ms")
            print(f"  Hit latency P95: {np.percentile(hit_latencies, 95):.2f}ms")

        if miss_latencies:
            print(f"  Miss latency P50: {statistics.median(miss_latencies):.2f}ms")
            print(f"  Miss latency P95: {np.percentile(miss_latencies, 95):.2f}ms")

        # Performance assertions
        assert edge_metrics["hit_rate"] > 40, "Hit rate should be > 40%"
        if hit_latencies:
            assert statistics.median(hit_latencies) < 10, "Cache hit latency should be < 10ms"

        await cache.close()


class TestWebSocketClusterPerformance:
    """Performance tests for WebSocket clustering"""

    @pytest.mark.asyncio
    async def test_websocket_session_affinity(self):
        """Test WebSocket session affinity across nodes"""
        # Create 3 cluster nodes
        nodes = []
        for i in range(3):
            node = WebSocketCluster(
                node_id=f"node_{i}",
                redis_url="redis://localhost:6379",
                hostname=f"server{i}",
                port=8000 + i,
            )
            await node.start()
            nodes.append(node)

        # Track session distributions
        session_distribution = {f"node_{i}": 0 for i in range(3)}

        # Simulate 100 sessions
        for session_num in range(100):
            session_id = f"session_{session_num}"

            # Determine target node using consistent hashing
            target_node = nodes[0].consistent_hash.get_node(session_id)
            if target_node:
                session_distribution[target_node] += 1

        print(f"\nWebSocket Session Distribution:")
        for node_id, count in session_distribution.items():
            percentage = (count / 100) * 100
            print(f"  {node_id}: {count} ({percentage:.1f}%)")

        # Check distribution is relatively even
        counts = list(session_distribution.values())
        std_dev = statistics.stdev(counts)
        mean = statistics.mean(counts)
        cv = (std_dev / mean) * 100 if mean > 0 else 0

        print(f"  Distribution CV: {cv:.1f}%")
        assert cv < 30, "Session distribution should be balanced (CV < 30%)"

        # Test session stickiness
        test_session = "test_session_123"
        target_node = nodes[0].consistent_hash.get_node(test_session)

        # Check same session always routes to same node
        for _ in range(10):
            assert nodes[0].consistent_hash.get_node(test_session) == target_node

        # Clean up
        for node in nodes:
            await node.stop()


class TestGlobalLoadBalancerPerformance:
    """Performance tests for global load balancing"""

    @pytest.mark.asyncio
    async def test_geographic_routing_latency(self):
        """Test geographic routing reduces latency"""
        # Define regions
        regions = [
            Region(
                code=RegionCode.US_EAST_1,
                name="US East",
                location=GeographicLocation(40.7128, -74.0060),  # New York
                endpoints=["us-east-1.example.com"],
                capacity=10000,
            ),
            Region(
                code=RegionCode.EU_WEST_1,
                name="EU West",
                location=GeographicLocation(53.3498, -6.2603),  # Dublin
                endpoints=["eu-west-1.example.com"],
                capacity=10000,
            ),
            Region(
                code=RegionCode.AP_SOUTH_1,
                name="AP South",
                location=GeographicLocation(19.0760, 72.8777),  # Mumbai
                endpoints=["ap-south-1.example.com"],
                capacity=10000,
            ),
        ]

        policy = TrafficPolicy(
            policy_type=RoutingPolicy.GEOPROXIMITY, endpoints=[r.endpoints[0] for r in regions]
        )

        health_check = HealthCheck(endpoint="health", type="http", interval=30)

        lb = GlobalLoadBalancer(regions=regions, policy=policy, health_check_config=health_check)

        await lb.start()

        # Simulate requests from different locations
        test_locations = [
            ("1.2.3.4", "US"),  # US IP
            ("185.2.3.4", "EU"),  # EU IP
            ("103.2.3.4", "AP"),  # Asia IP
        ]

        routing_results = []

        for ip, expected_region in test_locations:
            endpoints = await lb.route(ip)
            if endpoints:
                routing_results.append((expected_region, endpoints[0]))

        print(f"\nGeographic Routing Results:")
        for region, endpoint in routing_results:
            print(f"  {region}: {endpoint}")

        # Get metrics
        metrics = lb.get_metrics()
        print(f"\nGlobal LB Metrics:")
        print(f"  Total requests: {metrics['total_requests']}")
        print(f"  Average latency: {metrics['average_latency_ms']:.2f}ms")
        print(f"  Cache hit rate: {metrics['cache_hit_rate']:.1f}%")

        await lb.stop()


class TestEndToEndPerformance:
    """End-to-end performance test of entire load balancing stack"""

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_full_stack_performance(self):
        """Test complete load balancing stack under realistic load"""
        print("\n" + "=" * 60)
        print("FULL STACK LOAD BALANCING PERFORMANCE TEST")
        print("=" * 60)

        # Initialize all components
        components_initialized = []

        try:
            # 1. Circuit Breaker
            cb_config = CircuitBreakerConfig(failure_threshold=10, reset_timeout=5.0)
            circuit_breaker = CircuitBreaker("api", cb_config)
            components_initialized.append("Circuit Breaker")

            # 2. Rate Limiter
            redis_client = await aioredis.from_url("redis://localhost:6379/15")
            rl_config = RateLimitConfig(requests_per_second=1000)
            rate_limiter = RateLimiter(redis_client, rl_config)
            components_initialized.append("Rate Limiter")

            # 3. Database Replica Router
            replica_router = ReplicaRouter(
                "postgresql://primary:5432/db",
                ["postgresql://replica1:5432/db", "postgresql://replica2:5432/db"],
            )
            await replica_router.start()
            components_initialized.append("Replica Router")

            # 4. Edge Cache
            edge_cache = EdgeCache("redis://localhost:6379")
            await edge_cache.initialize()
            components_initialized.append("Edge Cache")

            # 5. WebSocket Cluster
            ws_cluster = WebSocketCluster("main", "redis://localhost:6379")
            await ws_cluster.start()
            components_initialized.append("WebSocket Cluster")

            print(f"\nInitialized components: {', '.join(components_initialized)}")

            # Run performance test
            start_time = time.time()
            total_requests = 10000
            successful_requests = 0
            failed_requests = 0
            latencies = []

            async def simulate_request():
                nonlocal successful_requests, failed_requests

                request_start = time.time()
                try:
                    # 1. Check rate limit
                    user_id = f"user_{random.randint(1, 100)}"
                    rl_result = await rate_limiter.check_rate_limit(user_id)
                    if not rl_result.allowed:
                        failed_requests += 1
                        return

                    # 2. Circuit breaker check
                    async def api_call():
                        # Simulate API processing
                        if random.random() < 0.95:  # 95% success rate
                            await asyncio.sleep(random.uniform(0.01, 0.05))
                            return {"status": "success"}
                        else:
                            raise Exception("API Error")

                    await circuit_breaker.call(api_call)

                    # 3. Cache check
                    cache_key = f"resource:{random.randint(1, 500)}"
                    cached = await edge_cache.get(cache_key)
                    if not cached:
                        # Simulate cache miss - fetch from origin
                        await asyncio.sleep(random.uniform(0.02, 0.1))
                        await edge_cache.set(cache_key, b"data")

                    successful_requests += 1

                except Exception:
                    failed_requests += 1
                finally:
                    latencies.append((time.time() - request_start) * 1000)

            # Run concurrent requests
            batch_size = 100
            for batch in range(total_requests // batch_size):
                tasks = [simulate_request() for _ in range(batch_size)]
                await asyncio.gather(*tasks, return_exceptions=True)

                # Show progress
                if (batch + 1) % 10 == 0:
                    progress = ((batch + 1) * batch_size / total_requests) * 100
                    print(f"  Progress: {progress:.0f}%")

            duration = time.time() - start_time

            # Calculate metrics
            throughput = successful_requests / duration
            success_rate = (successful_requests / total_requests) * 100
            p50_latency = statistics.median(latencies)
            p95_latency = np.percentile(latencies, 95)
            p99_latency = np.percentile(latencies, 99)

            print(f"\n{'='*60}")
            print("PERFORMANCE TEST RESULTS")
            print(f"{'='*60}")
            print(f"Duration: {duration:.2f} seconds")
            print(f"Total Requests: {total_requests}")
            print(f"Successful: {successful_requests} ({success_rate:.1f}%)")
            print(f"Failed: {failed_requests}")
            print(f"Throughput: {throughput:.0f} req/s")
            print(f"\nLatency Percentiles:")
            print(f"  P50: {p50_latency:.2f}ms")
            print(f"  P95: {p95_latency:.2f}ms")
            print(f"  P99: {p99_latency:.2f}ms")

            # Component metrics
            print(f"\nComponent Metrics:")

            cb_status = circuit_breaker.get_status()
            print(f"  Circuit Breaker:")
            print(f"    State: {cb_status['state']}")
            print(f"    Failure rate: {cb_status['metrics']['failure_rate']*100:.1f}%")

            cache_metrics = edge_cache.get_metrics()
            edge_metrics = cache_metrics.get(CacheTier.EDGE.value, {})
            print(f"  Edge Cache:")
            print(f"    Hit rate: {edge_metrics.get('hit_rate', 0):.1f}%")

            replica_metrics = replica_router.get_metrics()
            print(f"  Replica Router:")
            print(f"    Replica usage: {replica_metrics['replica_percentage']:.1f}%")

            ws_metrics = ws_cluster.get_metrics()
            print(f"  WebSocket Cluster:")
            print(f"    Active connections: {ws_metrics['connections']}")

            # Performance assertions
            assert throughput > 100, "Throughput should exceed 100 req/s"
            assert success_rate > 90, "Success rate should exceed 90%"
            assert p50_latency < 100, "P50 latency should be under 100ms"
            assert p99_latency < 1000, "P99 latency should be under 1000ms"

            print(f"\n{'='*60}")
            print("✅ ALL PERFORMANCE TESTS PASSED")
            print(f"{'='*60}")

        finally:
            # Clean up
            print("\nCleaning up...")
            if "replica_router" in locals():
                await replica_router.stop()
            if "edge_cache" in locals():
                await edge_cache.close()
            if "ws_cluster" in locals():
                await ws_cluster.stop()
            if "redis_client" in locals():
                await redis_client.close()


# Locust test configuration for load testing
def run_locust_test():
    """Run Locust load test"""
    setup_logging("INFO", None)

    # Create environment
    env = Environment(user_classes=[LoadBalancingUser])
    env.create_local_runner()

    # Start test
    env.runner.start(100, spawn_rate=10)  # 100 users, 10/s spawn rate

    # Run for 60 seconds
    time.sleep(60)

    # Stop test
    env.runner.quit()

    # Print statistics
    stats = env.stats
    print("\nLocust Test Results:")
    print(f"Total requests: {stats.total.num_requests}")
    print(f"Failure rate: {stats.total.fail_ratio*100:.2f}%")
    print(f"Average response time: {stats.total.avg_response_time:.2f}ms")
    print(f"RPS: {stats.total.current_rps:.2f}")


if __name__ == "__main__":
    # Run performance tests
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "locust":
        print("Running Locust load test...")
        run_locust_test()
    else:
        print("Running unit performance tests...")
        # Run individual test classes
        asyncio.run(TestCircuitBreakerPerformance().test_circuit_breaker_under_load())
        asyncio.run(TestRateLimiterPerformance().test_rate_limiter_accuracy())
        asyncio.run(TestDatabaseReplicaPerformance().test_replica_routing_distribution())
        asyncio.run(TestEdgeCachePerformance().test_cache_hit_rate())
        asyncio.run(TestWebSocketClusterPerformance().test_websocket_session_affinity())
        asyncio.run(TestGlobalLoadBalancerPerformance().test_geographic_routing_latency())
        asyncio.run(TestEndToEndPerformance().test_full_stack_performance())
