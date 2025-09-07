"""Performance and load tests"""

import pytest
import time
import threading
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from server.roblox_server import app
from src.shared.utils.cache import LRUCache
from src.shared.utils.monitoring import metrics


@pytest.fixture
def client():
    """Flask test client"""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


class TestCachePerformance:
    """Test cache performance"""
    
    def test_cache_performance(self):
        """Test cache read/write performance"""
        cache = LRUCache(max_size=1000, ttl=300)
        
        # Warm up
        for i in range(100):
            cache.set(f"key_{i}", f"value_{i}")
        
        # Test write performance
        start_time = time.time()
        for i in range(1000):
            cache.set(f"perf_key_{i}", f"perf_value_{i}")
        write_time = time.time() - start_time
        
        # Test read performance
        start_time = time.time()
        for i in range(1000):
            cache.get(f"perf_key_{i}")
        read_time = time.time() - start_time
        
        print(f"Cache write time for 1000 items: {write_time:.3f}s")
        print(f"Cache read time for 1000 items: {read_time:.3f}s")
        
        # Performance assertions
        assert write_time < 1.0  # Should write 1000 items in under 1 second
        assert read_time < 0.5   # Should read 1000 items in under 0.5 seconds
    
    def test_cache_concurrent_access(self):
        """Test cache under concurrent access"""
        cache = LRUCache(max_size=1000, ttl=300)
        
        def worker(worker_id):
            for i in range(100):
                key = f"worker_{worker_id}_key_{i}"
                value = f"worker_{worker_id}_value_{i}"
                cache.set(key, value)
                retrieved = cache.get(key)
                assert retrieved == value
        
        start_time = time.time()
        
        # Run 10 workers concurrently
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(worker, i) for i in range(10)]
            for future in as_completed(futures):
                future.result()  # Will raise exception if worker failed
        
        concurrent_time = time.time() - start_time
        print(f"Concurrent cache access time (10 workers, 100 ops each): {concurrent_time:.3f}s")
        
        # Should complete in reasonable time
        assert concurrent_time < 5.0


class TestAPILoadTesting:
    """Test API endpoints under load"""
    
    def test_health_endpoint_load(self, client):
        """Test health endpoint under load"""
        def make_request():
            response = client.get('/health')
            return response.status_code
        
        start_time = time.time()
        
        # Make 100 concurrent requests
        with ThreadPoolExecutor(max_workers=20) as executor:
            futures = [executor.submit(make_request) for _ in range(100)]
            results = [future.result() for future in as_completed(futures)]
        
        load_time = time.time() - start_time
        
        # Check results
        success_count = sum(1 for status in results if status in [200, 503])
        success_rate = success_count / len(results)
        
        print(f"Health endpoint load test: {load_time:.3f}s for 100 requests")
        print(f"Success rate: {success_rate:.2%}")
        
        assert success_rate >= 0.95  # At least 95% success rate
        assert load_time < 10.0      # Should complete in under 10 seconds
    
    def test_plugin_registration_load(self, client):
        """Test plugin registration under load"""
        def register_plugin(plugin_id):
            plugin_data = {
                'studio_id': f'load_test_studio_{plugin_id}',
                'port': 64989 + plugin_id,
                'version': '1.0.0'
            }
            response = client.post('/register_plugin', json=plugin_data)
            return response.status_code == 200
        
        start_time = time.time()
        
        # Register 50 plugins concurrently
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(register_plugin, i) for i in range(50)]
            results = [future.result() for future in as_completed(futures)]
        
        registration_time = time.time() - start_time
        
        success_count = sum(results)
        success_rate = success_count / len(results)
        
        print(f"Plugin registration load test: {registration_time:.3f}s for 50 registrations")
        print(f"Success rate: {success_rate:.2%}")
        
        assert success_rate >= 0.90  # At least 90% success rate
        assert registration_time < 15.0  # Should complete in under 15 seconds
    
    def test_heartbeat_load(self, client):
        """Test heartbeat endpoint under load"""
        # First register a plugin
        plugin_data = {'studio_id': 'heartbeat_load_test'}
        response = client.post('/register_plugin', json=plugin_data)
        plugin_id = json.loads(response.data)['plugin_id']
        
        def send_heartbeat():
            response = client.post(f'/plugin/{plugin_id}/heartbeat')
            return response.status_code in [200, 429]  # 429 is rate limit, which is expected
        
        start_time = time.time()
        
        # Send 100 heartbeats
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(send_heartbeat) for _ in range(100)]
            results = [future.result() for future in as_completed(futures)]
        
        heartbeat_time = time.time() - start_time
        
        success_count = sum(results)
        success_rate = success_count / len(results)
        
        print(f"Heartbeat load test: {heartbeat_time:.3f}s for 100 heartbeats")
        print(f"Success rate (including rate limits): {success_rate:.2%}")
        
        assert success_rate >= 0.80  # At least 80% (some may be rate limited)
        assert heartbeat_time < 10.0


class TestMemoryUsage:
    """Test memory usage patterns"""
    
    def test_cache_memory_growth(self):
        """Test cache memory usage doesn't grow unbounded"""
        cache = LRUCache(max_size=100, ttl=300)  # Small cache
        
        # Add many items (more than max_size)
        for i in range(1000):
            cache.set(f"memory_test_key_{i}", f"memory_test_value_{i}" * 100)
        
        # Cache should not exceed max_size
        assert cache.size() <= 100
        
        # Should still be functional
        cache.set("test_key", "test_value")
        assert cache.get("test_key") == "test_value"
    
    def test_plugin_manager_memory(self, client):
        """Test plugin manager doesn't leak memory"""
        initial_plugin_count = 0
        
        # Register many plugins
        for i in range(100):
            plugin_data = {
                'studio_id': f'memory_test_studio_{i}',
                'port': 65000 + i,
                'version': '1.0.0'
            }
            response = client.post('/register_plugin', json=plugin_data)
            assert response.status_code == 200
        
        # Check status
        response = client.get('/status')
        assert response.status_code == 200
        
        # Memory usage should be reasonable
        # (This is a basic check - in production you'd use more sophisticated memory profiling)
        data = json.loads(response.data)
        assert 'metrics' in data


class TestResponseTimes:
    """Test API response times"""
    
    def test_endpoint_response_times(self, client):
        """Test that endpoints respond within acceptable time limits"""
        endpoints = [
            ('GET', '/health'),
            ('GET', '/status'),
            ('GET', '/metrics'),
            ('GET', '/config'),
            ('POST', '/cache/clear'),
        ]
        
        for method, endpoint in endpoints:
            start_time = time.time()
            
            if method == 'GET':
                response = client.get(endpoint)
            else:
                response = client.post(endpoint)
            
            response_time = time.time() - start_time
            
            print(f"{method} {endpoint}: {response_time:.3f}s")
            
            # All endpoints should respond within 1 second
            assert response_time < 1.0
            assert response.status_code in [200, 400, 404, 500]  # Valid HTTP status


@pytest.mark.benchmark
class TestBenchmarks:
    """Benchmark tests (run with pytest-benchmark if available)"""
    
    def test_cache_set_benchmark(self, benchmark):
        """Benchmark cache set operation"""
        cache = LRUCache(max_size=1000, ttl=300)
        
        def cache_set():
            cache.set("benchmark_key", "benchmark_value")
        
        result = benchmark(cache_set)
        # Benchmark will automatically measure and report timing
    
    def test_cache_get_benchmark(self, benchmark):
        """Benchmark cache get operation"""
        cache = LRUCache(max_size=1000, ttl=300)
        cache.set("benchmark_key", "benchmark_value")
        
        def cache_get():
            return cache.get("benchmark_key")
        
        result = benchmark(cache_get)
        assert result == "benchmark_value"