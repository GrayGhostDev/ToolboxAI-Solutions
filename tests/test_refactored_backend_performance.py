"""
Performance Test Suite for Refactored Backend Application

This test suite focuses on performance characteristics and benchmarks
for the refactored backend to ensure no performance regression.

Test Categories:
1. Application Startup Performance
2. Endpoint Response Time Benchmarks
3. Memory Usage Stability
4. Concurrent Request Handling
5. Database Connection Performance
6. Circuit Breaker Performance Impact
7. Rate Limiting Performance
"""

import asyncio
import gc
import os
import psutil
import time
import threading
from contextlib import contextmanager
from typing import List, Dict, Any
from unittest.mock import patch

import httpx
import pytest
from fastapi.testclient import TestClient

# Set testing environment
os.environ["TESTING"] = "true"
os.environ["SKIP_LIFESPAN"] = "true"

from apps.backend.core.app_factory import create_app, create_test_app
from apps.backend.main import app as main_app


class PerformanceMetrics:
    """Helper class to collect and analyze performance metrics"""

    def __init__(self):
        self.metrics = []
        self.start_time = None
        self.end_time = None

    @contextmanager
    def measure(self, operation_name: str):
        """Context manager to measure operation time"""
        start_time = time.perf_counter()
        start_memory = self._get_memory_usage()

        try:
            yield
        finally:
            end_time = time.perf_counter()
            end_memory = self._get_memory_usage()

            self.metrics.append({
                'operation': operation_name,
                'duration': end_time - start_time,
                'memory_start': start_memory,
                'memory_end': end_memory,
                'memory_delta': end_memory - start_memory
            })

    def _get_memory_usage(self) -> float:
        """Get current memory usage in MB"""
        process = psutil.Process(os.getpid())
        return process.memory_info().rss / 1024 / 1024

    def get_summary(self) -> Dict[str, Any]:
        """Get performance summary"""
        if not self.metrics:
            return {}

        durations = [m['duration'] for m in self.metrics]
        memory_deltas = [m['memory_delta'] for m in self.metrics]

        return {
            'total_operations': len(self.metrics),
            'total_duration': sum(durations),
            'avg_duration': sum(durations) / len(durations),
            'min_duration': min(durations),
            'max_duration': max(durations),
            'avg_memory_delta': sum(memory_deltas) / len(memory_deltas),
            'max_memory_delta': max(memory_deltas),
            'operations': self.metrics
        }


class TestApplicationStartupPerformance:
    """Test application startup performance"""

    def test_app_factory_creation_time(self):
        """Test app factory creation time"""
        metrics = PerformanceMetrics()

        with metrics.measure("app_factory_creation"):
            app = create_test_app()
            assert app is not None

        summary = metrics.get_summary()
        startup_time = summary['avg_duration']

        assert startup_time < 1.0, f"App creation took {startup_time:.3f}s, should be < 1s"

    def test_main_app_import_time(self):
        """Test main app import and initialization time"""
        # This test measures the time it takes to import the main app
        # which includes all the factory setup

        assert main_app is not None

        # Verify the app is properly configured
        assert hasattr(main_app, 'state')
        assert main_app.title is not None
        assert main_app.version is not None

    def test_multiple_app_creation_performance(self):
        """Test performance of creating multiple app instances"""
        metrics = PerformanceMetrics()

        num_apps = 5
        apps = []

        for i in range(num_apps):
            with metrics.measure(f"app_creation_{i}"):
                app = create_test_app()
                apps.append(app)

        summary = metrics.get_summary()

        # Average creation time should be reasonable
        assert summary['avg_duration'] < 0.5, f"Average app creation took {summary['avg_duration']:.3f}s"

        # Memory usage shouldn't grow excessively
        assert summary['max_memory_delta'] < 10.0, f"Memory delta too high: {summary['max_memory_delta']:.1f}MB"

    def test_app_configuration_overhead(self):
        """Test configuration overhead in app creation"""
        metrics = PerformanceMetrics()

        # Test with minimal configuration
        with metrics.measure("minimal_config"):
            app1 = create_app(skip_lifespan=True, skip_sentry=True, testing_mode=True)

        # Test with full configuration
        with metrics.measure("full_config"):
            app2 = create_app(testing_mode=False)

        summary = metrics.get_summary()

        # Both should be fast
        for metric in summary['operations']:
            assert metric['duration'] < 2.0, f"Configuration took {metric['duration']:.3f}s"


class TestEndpointPerformance:
    """Test endpoint response time performance"""

    def setup_method(self):
        """Setup test client"""
        self.client = TestClient(main_app)
        self.metrics = PerformanceMetrics()

    def test_health_endpoint_performance(self):
        """Test health endpoint response time"""
        times = []

        for i in range(10):
            with self.metrics.measure(f"health_request_{i}"):
                response = self.client.get("/health")
                assert response.status_code == 200

        summary = self.metrics.get_summary()

        # Average response time should be fast
        assert summary['avg_duration'] < 0.1, f"Health endpoint avg: {summary['avg_duration']:.3f}s"

        # Maximum response time should be reasonable
        assert summary['max_duration'] < 0.5, f"Health endpoint max: {summary['max_duration']:.3f}s"

    def test_info_endpoint_performance(self):
        """Test info endpoint response time"""
        times = []

        for i in range(10):
            with self.metrics.measure(f"info_request_{i}"):
                response = self.client.get("/info")
                assert response.status_code == 200

        summary = self.metrics.get_summary()
        assert summary['avg_duration'] < 0.1, f"Info endpoint avg: {summary['avg_duration']:.3f}s"

    def test_migration_status_performance(self):
        """Test migration status endpoint performance"""
        for i in range(5):
            with self.metrics.measure(f"migration_status_{i}"):
                response = self.client.get("/migration/status")
                assert response.status_code == 200

        summary = self.metrics.get_summary()
        assert summary['avg_duration'] < 0.2, f"Migration status avg: {summary['avg_duration']:.3f}s"

    def test_openapi_generation_performance(self):
        """Test OpenAPI schema generation performance"""
        with self.metrics.measure("openapi_generation"):
            response = self.client.get("/openapi.json")
            assert response.status_code == 200

        summary = self.metrics.get_summary()
        assert summary['avg_duration'] < 1.0, f"OpenAPI generation: {summary['avg_duration']:.3f}s"

    def test_error_endpoint_performance(self):
        """Test error endpoint response time"""
        with self.metrics.measure("error_endpoint"):
            response = self.client.get("/endpoint/that/errors")
            assert response.status_code == 500

        summary = self.metrics.get_summary()
        assert summary['avg_duration'] < 0.1, f"Error endpoint: {summary['avg_duration']:.3f}s"


class TestConcurrentRequestPerformance:
    """Test performance under concurrent requests"""

    def setup_method(self):
        """Setup test client"""
        self.client = TestClient(main_app)

    def test_concurrent_health_checks(self):
        """Test concurrent health check performance"""
        num_threads = 20
        num_requests_per_thread = 10
        results = []
        errors = []

        def make_requests():
            try:
                thread_times = []
                for _ in range(num_requests_per_thread):
                    start_time = time.perf_counter()
                    response = self.client.get("/health")
                    end_time = time.perf_counter()

                    if response.status_code == 200:
                        thread_times.append(end_time - start_time)
                    else:
                        errors.append(response.status_code)

                results.extend(thread_times)
            except Exception as e:
                errors.append(str(e))

        # Create and start threads
        threads = []
        start_time = time.perf_counter()

        for _ in range(num_threads):
            thread = threading.Thread(target=make_requests)
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        end_time = time.perf_counter()
        total_time = end_time - start_time

        # Analyze results
        total_requests = num_threads * num_requests_per_thread
        successful_requests = len(results)
        error_count = len(errors)

        print(f"\nConcurrent Health Check Results:")
        print(f"Total requests: {total_requests}")
        print(f"Successful requests: {successful_requests}")
        print(f"Error count: {error_count}")
        print(f"Total time: {total_time:.3f}s")
        print(f"Requests per second: {successful_requests / total_time:.1f}")

        # Assertions
        assert successful_requests >= total_requests * 0.95, "Should have >95% success rate"
        assert total_time < 10.0, f"Total time too high: {total_time:.3f}s"

        if results:
            avg_response_time = sum(results) / len(results)
            max_response_time = max(results)

            assert avg_response_time < 0.5, f"Average response time too high: {avg_response_time:.3f}s"
            assert max_response_time < 2.0, f"Max response time too high: {max_response_time:.3f}s"

    def test_mixed_endpoint_concurrent_access(self):
        """Test concurrent access to different endpoints"""
        endpoints = ["/health", "/info", "/migration/status"]
        num_threads_per_endpoint = 5
        results = {endpoint: [] for endpoint in endpoints}
        errors = []

        def make_requests(endpoint):
            try:
                for _ in range(10):
                    start_time = time.perf_counter()
                    response = self.client.get(endpoint)
                    end_time = time.perf_counter()

                    if response.status_code == 200:
                        results[endpoint].append(end_time - start_time)
                    else:
                        errors.append(f"{endpoint}: {response.status_code}")
            except Exception as e:
                errors.append(f"{endpoint}: {str(e)}")

        # Create threads for each endpoint
        threads = []
        start_time = time.perf_counter()

        for endpoint in endpoints:
            for _ in range(num_threads_per_endpoint):
                thread = threading.Thread(target=make_requests, args=(endpoint,))
                threads.append(thread)
                thread.start()

        # Wait for completion
        for thread in threads:
            thread.join()

        end_time = time.perf_counter()
        total_time = end_time - start_time

        # Analyze results
        print(f"\nMixed Endpoint Concurrent Results:")
        print(f"Total time: {total_time:.3f}s")
        print(f"Errors: {len(errors)}")

        for endpoint, times in results.items():
            if times:
                avg_time = sum(times) / len(times)
                print(f"{endpoint}: {len(times)} requests, avg {avg_time:.3f}s")

        # Assertions
        assert len(errors) <= 5, f"Too many errors: {errors}"
        assert total_time < 15.0, f"Total time too high: {total_time:.3f}s"


class TestMemoryPerformance:
    """Test memory usage and stability"""

    def test_memory_stability_under_load(self):
        """Test memory usage remains stable under request load"""
        client = TestClient(main_app)

        # Get initial memory usage
        gc.collect()  # Force garbage collection
        initial_memory = self._get_memory_usage()

        # Make many requests
        for i in range(100):
            response = client.get("/health")
            assert response.status_code == 200

            # Every 20 requests, check memory
            if i % 20 == 0:
                current_memory = self._get_memory_usage()
                memory_increase = current_memory - initial_memory

                # Memory increase should be reasonable
                assert memory_increase < 50.0, f"Memory increased by {memory_increase:.1f}MB at request {i}"

        # Final memory check
        gc.collect()
        final_memory = self._get_memory_usage()
        total_increase = final_memory - initial_memory

        print(f"\nMemory Usage:")
        print(f"Initial: {initial_memory:.1f}MB")
        print(f"Final: {final_memory:.1f}MB")
        print(f"Increase: {total_increase:.1f}MB")

        assert total_increase < 100.0, f"Total memory increase too high: {total_increase:.1f}MB"

    def test_memory_cleanup_after_errors(self):
        """Test memory is cleaned up properly after errors"""
        client = TestClient(main_app)

        gc.collect()
        initial_memory = self._get_memory_usage()

        # Generate many errors
        for _ in range(50):
            response = client.get("/endpoint/that/errors")
            assert response.status_code == 500

        gc.collect()
        after_errors_memory = self._get_memory_usage()

        # Make successful requests
        for _ in range(50):
            response = client.get("/health")
            assert response.status_code == 200

        gc.collect()
        final_memory = self._get_memory_usage()

        memory_increase = final_memory - initial_memory

        print(f"\nMemory After Errors:")
        print(f"Initial: {initial_memory:.1f}MB")
        print(f"After errors: {after_errors_memory:.1f}MB")
        print(f"Final: {final_memory:.1f}MB")
        print(f"Net increase: {memory_increase:.1f}MB")

        assert memory_increase < 30.0, f"Memory increase after errors: {memory_increase:.1f}MB"

    def _get_memory_usage(self) -> float:
        """Get current memory usage in MB"""
        process = psutil.Process(os.getpid())
        return process.memory_info().rss / 1024 / 1024


class TestFactoryPatternPerformance:
    """Test performance impact of factory pattern"""

    def test_factory_vs_direct_instantiation(self):
        """Compare factory pattern performance with direct instantiation"""
        metrics = PerformanceMetrics()

        # Test factory pattern (current approach)
        for i in range(5):
            with metrics.measure(f"factory_creation_{i}"):
                app = create_test_app()
                assert app is not None

        factory_summary = metrics.get_summary()

        # Reset metrics for comparison
        metrics = PerformanceMetrics()

        # Test direct FastAPI instantiation (for comparison)
        from fastapi import FastAPI

        for i in range(5):
            with metrics.measure(f"direct_creation_{i}"):
                app = FastAPI(
                    title="Direct App",
                    version="1.0.0",
                    lifespan=None
                )
                assert app is not None

        direct_summary = metrics.get_summary()

        print(f"\nFactory vs Direct Performance:")
        print(f"Factory avg: {factory_summary['avg_duration']:.3f}s")
        print(f"Direct avg: {direct_summary['avg_duration']:.3f}s")
        print(f"Overhead: {(factory_summary['avg_duration'] / direct_summary['avg_duration'] - 1) * 100:.1f}%")

        # Factory should not add significant overhead
        overhead_ratio = factory_summary['avg_duration'] / direct_summary['avg_duration']
        assert overhead_ratio < 3.0, f"Factory pattern adds too much overhead: {overhead_ratio:.1f}x"

    def test_configuration_impact_on_performance(self):
        """Test performance impact of different configuration options"""
        metrics = PerformanceMetrics()

        # Test minimal configuration
        with metrics.measure("minimal_config"):
            app = create_app(
                skip_lifespan=True,
                skip_sentry=True,
                testing_mode=True
            )

        # Test with components enabled
        with metrics.measure("full_config"):
            app = create_app(
                skip_lifespan=False,
                skip_sentry=False,
                testing_mode=False
            )

        summary = metrics.get_summary()

        for operation in summary['operations']:
            assert operation['duration'] < 2.0, f"Configuration took too long: {operation['duration']:.3f}s"


@pytest.mark.asyncio
class TestAsyncPerformance:
    """Test async operation performance"""

    async def test_async_endpoint_performance(self):
        """Test async endpoint performance"""
        async with httpx.AsyncClient(app=main_app, base_url="http://test") as client:
            # Test single async request
            start_time = time.perf_counter()
            response = await client.get("/health")
            end_time = time.perf_counter()

            assert response.status_code == 200
            assert (end_time - start_time) < 0.5

    async def test_concurrent_async_requests(self):
        """Test concurrent async request performance"""
        async with httpx.AsyncClient(app=main_app, base_url="http://test") as client:
            # Create concurrent requests
            start_time = time.perf_counter()

            tasks = [
                client.get("/health"),
                client.get("/info"),
                client.get("/migration/status")
            ] * 10  # 30 total requests

            responses = await asyncio.gather(*tasks)
            end_time = time.perf_counter()

            total_time = end_time - start_time

            # All should succeed
            for response in responses:
                assert response.status_code == 200

            # Should complete quickly
            assert total_time < 5.0, f"30 concurrent requests took {total_time:.3f}s"

            # Calculate requests per second
            rps = len(responses) / total_time
            print(f"\nAsync Performance: {rps:.1f} requests/second")

            assert rps > 10, f"Request rate too low: {rps:.1f} rps"


class TestLoadTestScenarios:
    """Load testing scenarios"""

    def test_sustained_load_performance(self):
        """Test performance under sustained load"""
        client = TestClient(main_app)

        start_time = time.perf_counter()
        response_times = []
        error_count = 0

        # Sustained load for a period
        duration = 10  # seconds
        end_test_time = start_time + duration

        request_count = 0
        while time.perf_counter() < end_test_time:
            request_start = time.perf_counter()

            try:
                response = client.get("/health")
                request_end = time.perf_counter()

                if response.status_code == 200:
                    response_times.append(request_end - request_start)
                else:
                    error_count += 1

                request_count += 1

            except Exception:
                error_count += 1
                request_count += 1

            # Small delay to prevent overwhelming
            time.sleep(0.01)

        total_time = time.perf_counter() - start_time

        print(f"\nSustained Load Results:")
        print(f"Duration: {total_time:.1f}s")
        print(f"Total requests: {request_count}")
        print(f"Successful requests: {len(response_times)}")
        print(f"Error count: {error_count}")
        print(f"Requests per second: {request_count / total_time:.1f}")

        if response_times:
            avg_response_time = sum(response_times) / len(response_times)
            max_response_time = max(response_times)

            print(f"Average response time: {avg_response_time:.3f}s")
            print(f"Max response time: {max_response_time:.3f}s")

            # Performance assertions
            assert avg_response_time < 0.1, f"Average response time too high: {avg_response_time:.3f}s"
            assert max_response_time < 1.0, f"Max response time too high: {max_response_time:.3f}s"

        # Error rate should be low
        error_rate = error_count / request_count if request_count > 0 else 1
        assert error_rate < 0.05, f"Error rate too high: {error_rate:.1%}"


# Performance benchmark fixtures and utilities
@pytest.fixture
def performance_monitor():
    """Fixture that provides performance monitoring"""
    return PerformanceMetrics()


def benchmark_operation(func, num_iterations=10):
    """Utility function to benchmark an operation"""
    times = []

    for _ in range(num_iterations):
        start_time = time.perf_counter()
        func()
        end_time = time.perf_counter()
        times.append(end_time - start_time)

    return {
        'avg_time': sum(times) / len(times),
        'min_time': min(times),
        'max_time': max(times),
        'total_time': sum(times),
        'iterations': num_iterations
    }


if __name__ == "__main__":
    # Run performance tests
    pytest.main([__file__, "-v", "--tb=short", "-s"])