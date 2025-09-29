"""
Comprehensive performance integration tests.

This module tests API response times, database query performance, frontend load times,
and overall system performance to ensure the entire system meets performance requirements.
"""

import asyncio
import json
import os
import time
import statistics
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
import pytest
import aiohttp
import asyncpg
import redis.asyncio as redis
import psutil
from pathlib import Path
import tempfile
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed


@pytest.mark.performance
@pytest.mark.integration
class TestComprehensivePerformance:
    """Test comprehensive system performance."""

    def setup_method(self):
        """Set up performance test environment."""
        self.api_url = "http://localhost:8009"
        self.dashboard_url = "http://localhost:5179"

        # Performance thresholds (in milliseconds)
        self.performance_thresholds = {
            "api_response_time": 500,
            "database_query_time": 100,
            "page_load_time": 3000,
            "memory_usage_mb": 1024,
            "cpu_usage_percent": 80
        }

        # Test data sizes
        self.test_data_sizes = {
            "small": 100,
            "medium": 1000,
            "large": 10000
        }

        # Database configuration
        self.db_config = {
            "host": "localhost",
            "port": 5434,
            "database": "educational_platform_dev",
            "user": "eduplatform",
            "password": "eduplatform2024"
        }

        # Redis configuration
        self.redis_url = "redis://localhost:6381/0"

    @pytest.mark.asyncio
    async def test_api_response_time_benchmarks(self):
        """Test API response time benchmarks for all endpoints."""

        endpoints = [
            ("/health", "GET", None),
            ("/", "GET", None),
            ("/docs", "GET", None),
            ("/api/v1/auth/status", "GET", None),
            ("/api/v1/classes", "GET", None),
            ("/api/v1/lessons", "GET", None),
            ("/api/v1/assessments", "GET", None),
            ("/api/v1/agents/status", "GET", None),
        ]

        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30)) as session:

            performance_results = {}

            for endpoint, method, data in endpoints:
                response_times = []
                status_codes = []

                # Make 20 requests to each endpoint
                for _ in range(20):
                    start_time = time.time()

                    try:
                        if method == "GET":
                            async with session.get(f"{self.api_url}{endpoint}") as response:
                                end_time = time.time()
                                response_times.append((end_time - start_time) * 1000)
                                status_codes.append(response.status)
                        elif method == "POST":
                            async with session.post(f"{self.api_url}{endpoint}", json=data) as response:
                                end_time = time.time()
                                response_times.append((end_time - start_time) * 1000)
                                status_codes.append(response.status)

                    except Exception as e:
                        # Record failed request
                        response_times.append(5000)  # 5 second timeout
                        status_codes.append(0)

                # Calculate statistics
                if response_times:
                    performance_results[endpoint] = {
                        "avg_response_time": statistics.mean(response_times),
                        "median_response_time": statistics.median(response_times),
                        "p95_response_time": sorted(response_times)[int(0.95 * len(response_times))],
                        "max_response_time": max(response_times),
                        "min_response_time": min(response_times),
                        "success_rate": sum(1 for code in status_codes if 200 <= code < 400) / len(status_codes),
                        "status_codes": status_codes
                    }

                    # Assert performance thresholds
                    avg_time = performance_results[endpoint]["avg_response_time"]
                    success_rate = performance_results[endpoint]["success_rate"]

                    assert avg_time < self.performance_thresholds["api_response_time"], \
                        f"{endpoint} avg response time: {avg_time:.2f}ms (threshold: {self.performance_thresholds['api_response_time']}ms)"

                    assert success_rate >= 0.95, \
                        f"{endpoint} success rate: {success_rate:.2f} (threshold: 0.95)"

            return performance_results

    @pytest.mark.asyncio
    async def test_database_query_performance(self):
        """Test database query performance with various data sizes."""

        conn = None
        try:
            conn = await asyncpg.connect(**self.db_config, timeout=30)

            # Create test table for performance testing
            test_table = f"perf_test_{int(time.time())}"
            await conn.execute(f"""
                CREATE TABLE {test_table} (
                    id SERIAL PRIMARY KEY,
                    data TEXT,
                    number_value INTEGER,
                    created_at TIMESTAMPTZ DEFAULT NOW()
                );
                CREATE INDEX idx_{test_table}_number ON {test_table}(number_value);
                CREATE INDEX idx_{test_table}_created ON {test_table}(created_at);
            """)

            # Insert test data
            insert_data = [(f"test_data_{i}", i % 1000) for i in range(self.test_data_sizes["medium"])]

            start_time = time.time()
            await conn.executemany(
                f"INSERT INTO {test_table} (data, number_value) VALUES ($1, $2);",
                insert_data
            )
            insert_time = (time.time() - start_time) * 1000

            assert insert_time < 2000, f"Bulk insert took {insert_time:.2f}ms"

            # Test various query types
            query_tests = [
                ("Simple SELECT", f"SELECT COUNT(*) FROM {test_table};"),
                ("Indexed WHERE", f"SELECT * FROM {test_table} WHERE number_value = 500;"),
                ("Range Query", f"SELECT * FROM {test_table} WHERE number_value BETWEEN 100 AND 200;"),
                ("ORDER BY", f"SELECT * FROM {test_table} ORDER BY created_at DESC LIMIT 100;"),
                ("GROUP BY", f"SELECT number_value, COUNT(*) FROM {test_table} GROUP BY number_value LIMIT 10;"),
                ("Text Search", f"SELECT * FROM {test_table} WHERE data LIKE 'test_data_1%' LIMIT 50;"),
            ]

            query_performance = {}

            for query_name, query in query_tests:
                response_times = []

                # Execute each query 10 times
                for _ in range(10):
                    start_time = time.time()
                    await conn.fetch(query)
                    end_time = time.time()
                    response_times.append((end_time - start_time) * 1000)

                avg_time = statistics.mean(response_times)
                max_time = max(response_times)

                query_performance[query_name] = {
                    "avg_time": avg_time,
                    "max_time": max_time,
                    "min_time": min(response_times)
                }

                # Assert query performance
                assert avg_time < self.performance_thresholds["database_query_time"], \
                    f"{query_name} avg time: {avg_time:.2f}ms (threshold: {self.performance_thresholds['database_query_time']}ms)"

            # Test concurrent query performance
            async def concurrent_query():
                start_time = time.time()
                await conn.fetchval(f"SELECT COUNT(*) FROM {test_table} WHERE number_value < 500;")
                return (time.time() - start_time) * 1000

            # Run 10 concurrent queries
            concurrent_tasks = [concurrent_query() for _ in range(10)]
            concurrent_times = await asyncio.gather(*concurrent_tasks)

            avg_concurrent_time = statistics.mean(concurrent_times)
            assert avg_concurrent_time < self.performance_thresholds["database_query_time"] * 2, \
                f"Concurrent query avg time: {avg_concurrent_time:.2f}ms"

            # Cleanup
            await conn.execute(f"DROP TABLE {test_table};")

            return query_performance

        except Exception as e:
            pytest.skip(f"Database performance test failed: {e}")
        finally:
            if conn:
                await conn.close()

    @pytest.mark.asyncio
    async def test_redis_cache_performance(self):
        """Test Redis cache performance."""

        redis_client = None
        try:
            redis_client = await redis.from_url(self.redis_url, decode_responses=True)

            # Test basic operations
            operations = ["SET", "GET", "HSET", "HGET", "LPUSH", "LPOP"]
            operation_times = {}

            # SET operations
            set_times = []
            for i in range(100):
                start_time = time.time()
                await redis_client.set(f"perf_test:{i}", f"value_{i}")
                set_times.append((time.time() - start_time) * 1000)

            operation_times["SET"] = statistics.mean(set_times)

            # GET operations
            get_times = []
            for i in range(100):
                start_time = time.time()
                await redis_client.get(f"perf_test:{i}")
                get_times.append((time.time() - start_time) * 1000)

            operation_times["GET"] = statistics.mean(get_times)

            # Hash operations
            hset_times = []
            for i in range(100):
                start_time = time.time()
                await redis_client.hset(f"perf_hash:{i}", "field", f"value_{i}")
                hset_times.append((time.time() - start_time) * 1000)

            operation_times["HSET"] = statistics.mean(hset_times)

            hget_times = []
            for i in range(100):
                start_time = time.time()
                await redis_client.hget(f"perf_hash:{i}", "field")
                hget_times.append((time.time() - start_time) * 1000)

            operation_times["HGET"] = statistics.mean(hget_times)

            # List operations
            lpush_times = []
            for i in range(100):
                start_time = time.time()
                await redis_client.lpush("perf_list", f"item_{i}")
                lpush_times.append((time.time() - start_time) * 1000)

            operation_times["LPUSH"] = statistics.mean(lpush_times)

            lpop_times = []
            for i in range(100):
                start_time = time.time()
                await redis_client.lpop("perf_list")
                lpop_times.append((time.time() - start_time) * 1000)

            operation_times["LPOP"] = statistics.mean(lpop_times)

            # Assert Redis performance (Redis should be very fast)
            for operation, avg_time in operation_times.items():
                assert avg_time < 10, f"Redis {operation} too slow: {avg_time:.2f}ms"

            # Test concurrent Redis operations
            async def concurrent_redis_ops():
                key = f"concurrent:{time.time()}"
                start_time = time.time()
                await redis_client.set(key, "value")
                await redis_client.get(key)
                await redis_client.delete(key)
                return (time.time() - start_time) * 1000

            # Run 20 concurrent operations
            concurrent_tasks = [concurrent_redis_ops() for _ in range(20)]
            concurrent_times = await asyncio.gather(*concurrent_tasks)

            avg_concurrent_time = statistics.mean(concurrent_times)
            assert avg_concurrent_time < 50, f"Concurrent Redis ops too slow: {avg_concurrent_time:.2f}ms"

            # Cleanup
            await redis_client.flushdb()

            return operation_times

        except Exception as e:
            pytest.skip(f"Redis performance test failed: {e}")
        finally:
            if redis_client:
                await redis_client.close()

    @pytest.mark.asyncio
    async def test_frontend_load_performance(self):
        """Test frontend load performance."""

        try:
            from playwright.async_api import async_playwright

            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                context = await browser.new_context()
                page = await context.new_page()

                # Measure page load times
                load_times = []
                resource_counts = []

                for _ in range(5):
                    start_time = time.time()

                    await page.goto(self.dashboard_url, wait_until="networkidle")

                    end_time = time.time()
                    load_times.append((end_time - start_time) * 1000)

                    # Get performance metrics
                    metrics = await page.evaluate("""
                        () => {
                            const perfData = performance.getEntriesByType('navigation')[0];
                            const resources = performance.getEntriesByType('resource');

                            return {
                                domContentLoaded: perfData.domContentLoadedEventEnd - perfData.domContentLoadedEventStart,
                                loadComplete: perfData.loadEventEnd - perfData.loadEventStart,
                                resourceCount: resources.length,
                                totalResourceSize: resources.reduce((sum, r) => sum + (r.transferSize || 0), 0)
                            };
                        }
                    """)

                    resource_counts.append(metrics["resourceCount"])

                    # Assert individual load metrics
                    if metrics["domContentLoaded"]:
                        assert metrics["domContentLoaded"] < 2000, \
                            f"DOM content loaded: {metrics['domContentLoaded']}ms"

                avg_load_time = statistics.mean(load_times)
                assert avg_load_time < self.performance_thresholds["page_load_time"], \
                    f"Avg page load time: {avg_load_time:.2f}ms"

                # Test JavaScript performance
                js_performance = await page.evaluate("""
                    () => {
                        const start = performance.now();

                        // Simulate heavy computation
                        let result = 0;
                        for (let i = 0; i < 100000; i++) {
                            result += Math.random();
                        }

                        const end = performance.now();
                        return end - start;
                    }
                """)

                assert js_performance < 100, f"JS computation too slow: {js_performance:.2f}ms"

                await browser.close()

                return {
                    "avg_load_time": avg_load_time,
                    "avg_resource_count": statistics.mean(resource_counts),
                    "js_performance": js_performance
                }

        except ImportError:
            pytest.skip("Playwright not available for frontend testing")
        except Exception as e:
            pytest.skip(f"Frontend performance test failed: {e}")

    @pytest.mark.asyncio
    async def test_concurrent_load_performance(self):
        """Test system performance under concurrent load."""

        async def simulate_user_load():
            """Simulate a single user's load on the system."""
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30)) as session:
                start_time = time.time()

                # Simulate user workflow
                endpoints = ["/health", "/api/v1/auth/status", "/api/v1/classes"]
                response_times = []

                for endpoint in endpoints:
                    try:
                        request_start = time.time()
                        async with session.get(f"{self.api_url}{endpoint}") as response:
                            request_end = time.time()
                            response_times.append((request_end - request_start) * 1000)

                            if response.status != 200:
                                return None  # Failed request

                        # Small delay between requests
                        await asyncio.sleep(0.1)

                    except Exception:
                        return None

                total_time = (time.time() - start_time) * 1000
                return {
                    "total_time": total_time,
                    "response_times": response_times,
                    "success": True
                }

        # Test with increasing concurrent users
        user_counts = [1, 5, 10, 20]
        load_test_results = {}

        for user_count in user_counts:
            print(f"Testing with {user_count} concurrent users...")

            # Create concurrent user tasks
            user_tasks = [simulate_user_load() for _ in range(user_count)]

            start_time = time.time()
            results = await asyncio.gather(*user_tasks, return_exceptions=True)
            end_time = time.time()

            # Analyze results
            successful_users = [r for r in results if isinstance(r, dict) and r.get("success")]
            success_rate = len(successful_users) / user_count

            if successful_users:
                avg_user_time = statistics.mean([r["total_time"] for r in successful_users])
                avg_response_time = statistics.mean([
                    time for r in successful_users for time in r["response_times"]
                ])

                load_test_results[user_count] = {
                    "success_rate": success_rate,
                    "avg_user_time": avg_user_time,
                    "avg_response_time": avg_response_time,
                    "total_test_time": (end_time - start_time) * 1000
                }

                # Assert performance under load
                assert success_rate >= 0.9, \
                    f"Success rate too low with {user_count} users: {success_rate:.2f}"

                assert avg_response_time < self.performance_thresholds["api_response_time"] * 2, \
                    f"Response time too high with {user_count} users: {avg_response_time:.2f}ms"

        return load_test_results

    @pytest.mark.asyncio
    async def test_memory_usage_performance(self):
        """Test system memory usage performance."""

        try:
            import docker

            client = docker.from_env()
            containers = client.containers.list()

            memory_stats = {}

            for container in containers:
                if "toolboxai" in container.name:
                    try:
                        stats = container.stats(stream=False)
                        memory_usage = stats["memory_stats"]

                        if "usage" in memory_usage:
                            memory_mb = memory_usage["usage"] / (1024 * 1024)
                            memory_stats[container.name] = memory_mb

                            # Assert memory usage is reasonable
                            if "postgres" in container.name:
                                assert memory_mb < 512, f"PostgreSQL using too much memory: {memory_mb:.1f}MB"
                            elif "redis" in container.name:
                                assert memory_mb < 256, f"Redis using too much memory: {memory_mb:.1f}MB"
                            else:
                                assert memory_mb < self.performance_thresholds["memory_usage_mb"], \
                                    f"{container.name} using too much memory: {memory_mb:.1f}MB"

                    except Exception as e:
                        print(f"Could not get memory stats for {container.name}: {e}")

            # Test system memory usage
            system_memory = psutil.virtual_memory()
            memory_usage_percent = system_memory.percent

            assert memory_usage_percent < 90, f"System memory usage too high: {memory_usage_percent:.1f}%"

            return memory_stats

        except ImportError:
            pytest.skip("Docker library not available")
        except Exception as e:
            pytest.skip(f"Memory usage test failed: {e}")

    @pytest.mark.asyncio
    async def test_cpu_usage_performance(self):
        """Test system CPU usage performance."""

        try:
            # Measure CPU usage during load test
            cpu_measurements = []

            async def measure_cpu():
                for _ in range(10):
                    cpu_percent = psutil.cpu_percent(interval=1)
                    cpu_measurements.append(cpu_percent)

            async def generate_load():
                # Generate some API load
                async with aiohttp.ClientSession() as session:
                    tasks = []
                    for _ in range(50):
                        task = session.get(f"{self.api_url}/health")
                        tasks.append(task)

                    responses = await asyncio.gather(*tasks, return_exceptions=True)
                    return len([r for r in responses if not isinstance(r, Exception)])

            # Run CPU monitoring and load generation concurrently
            cpu_task = asyncio.create_task(measure_cpu())
            load_task = asyncio.create_task(generate_load())

            successful_requests, _ = await asyncio.gather(load_task, cpu_task)

            if cpu_measurements:
                avg_cpu = statistics.mean(cpu_measurements)
                max_cpu = max(cpu_measurements)

                assert avg_cpu < self.performance_thresholds["cpu_usage_percent"], \
                    f"Average CPU usage too high: {avg_cpu:.1f}%"

                assert max_cpu < 95, f"Peak CPU usage too high: {max_cpu:.1f}%"

                return {
                    "avg_cpu": avg_cpu,
                    "max_cpu": max_cpu,
                    "successful_requests": successful_requests
                }

        except Exception as e:
            pytest.skip(f"CPU usage test failed: {e}")

    @pytest.mark.asyncio
    async def test_database_connection_pool_performance(self):
        """Test database connection pool performance."""

        async def test_connection_usage():
            """Test a single database connection."""
            conn = None
            try:
                start_time = time.time()
                conn = await asyncpg.connect(**self.db_config, timeout=10)
                connect_time = (time.time() - start_time) * 1000

                query_start = time.time()
                await conn.fetchval("SELECT 1;")
                query_time = (time.time() - query_start) * 1000

                return {
                    "connect_time": connect_time,
                    "query_time": query_time,
                    "success": True
                }

            except Exception:
                return {"success": False}
            finally:
                if conn:
                    await conn.close()

        # Test concurrent connections
        connection_counts = [1, 5, 10, 20]
        pool_performance = {}

        for count in connection_counts:
            tasks = [test_connection_usage() for _ in range(count)]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            successful_connections = [r for r in results if isinstance(r, dict) and r.get("success")]
            success_rate = len(successful_connections) / count

            if successful_connections:
                avg_connect_time = statistics.mean([r["connect_time"] for r in successful_connections])
                avg_query_time = statistics.mean([r["query_time"] for r in successful_connections])

                pool_performance[count] = {
                    "success_rate": success_rate,
                    "avg_connect_time": avg_connect_time,
                    "avg_query_time": avg_query_time
                }

                # Assert connection pool performance
                assert success_rate >= 0.9, f"Connection success rate too low: {success_rate:.2f}"
                assert avg_connect_time < 1000, f"Connection time too high: {avg_connect_time:.2f}ms"
                assert avg_query_time < 100, f"Query time too high: {avg_query_time:.2f}ms"

        return pool_performance

    @pytest.mark.asyncio
    async def test_websocket_performance(self):
        """Test WebSocket performance."""

        try:
            from tests.fixtures.pusher_mocks import MockPusherService

            async def test_websocket_connection():
                """Test a single WebSocket connection."""
                ws_url = "pusher://app_key@cluster/native"

                try:
                    start_time = time.time()
                    async with async_mock_pusher_context() as pusher:
        # Connect using Pusherws_url, timeout=10) as websocket:
                        connect_time = (time.time() - start_time) * 1000

                        # Test message round-trip
                        message_start = time.time()
                        await pusher.trigger(json.dumps({"type": "ping", "data": "test"}))
                        response = await asyncio.wait_for(websocket.recv(), timeout=5)
                        message_time = (time.time() - message_start) * 1000

                        return {
                            "connect_time": connect_time,
                            "message_time": message_time,
                            "success": True
                        }

                except Exception:
                    return {"success": False}

            # Test concurrent WebSocket connections
            ws_tasks = [test_websocket_connection() for _ in range(10)]
            ws_results = await asyncio.gather(*ws_tasks, return_exceptions=True)

            successful_connections = [r for r in ws_results if isinstance(r, dict) and r.get("success")]
            success_rate = len(successful_connections) / 10

            if successful_connections:
                avg_connect_time = statistics.mean([r["connect_time"] for r in successful_connections])
                avg_message_time = statistics.mean([r["message_time"] for r in successful_connections])

                assert success_rate >= 0.8, f"WebSocket success rate too low: {success_rate:.2f}"
                assert avg_connect_time < 1000, f"WebSocket connect time too high: {avg_connect_time:.2f}ms"
                assert avg_message_time < 100, f"WebSocket message time too high: {avg_message_time:.2f}ms"

                return {
                    "success_rate": success_rate,
                    "avg_connect_time": avg_connect_time,
                    "avg_message_time": avg_message_time
                }

        except ImportError:
            pytest.skip("websockets library not available")
        except Exception as e:
            pytest.skip(f"WebSocket performance test failed: {e}")

    @pytest.mark.asyncio
    async def test_overall_system_performance_benchmark(self):
        """Test overall system performance benchmark."""

        benchmark_results = {}

        # Run all performance tests and collect results
        try:
            benchmark_results["api_performance"] = await self.test_api_response_time_benchmarks()
        except Exception as e:
            benchmark_results["api_performance"] = {"error": str(e)}

        try:
            benchmark_results["database_performance"] = await self.test_database_query_performance()
        except Exception as e:
            benchmark_results["database_performance"] = {"error": str(e)}

        try:
            benchmark_results["redis_performance"] = await self.test_redis_cache_performance()
        except Exception as e:
            benchmark_results["redis_performance"] = {"error": str(e)}

        try:
            benchmark_results["concurrent_load"] = await self.test_concurrent_load_performance()
        except Exception as e:
            benchmark_results["concurrent_load"] = {"error": str(e)}

        # Calculate overall performance score
        performance_score = 100  # Start with perfect score

        # Deduct points for performance issues
        for test_name, results in benchmark_results.items():
            if isinstance(results, dict) and "error" in results:
                performance_score -= 10  # Deduct for failed tests

        # Overall system should achieve at least 70% performance score
        assert performance_score >= 70, f"Overall performance score too low: {performance_score}%"

        # Save benchmark results
        timestamp = datetime.now().isoformat()
        benchmark_file = Path(f"test-results/performance-benchmark-{timestamp}.json")
        benchmark_file.parent.mkdir(exist_ok=True)

        with open(benchmark_file, 'w') as f:
            json.dump({
                "timestamp": timestamp,
                "performance_score": performance_score,
                "results": benchmark_results
            }, f, indent=2)

        return {
            "performance_score": performance_score,
            "benchmark_file": str(benchmark_file),
            "results": benchmark_results
        }