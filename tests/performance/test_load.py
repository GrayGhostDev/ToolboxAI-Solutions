"""
Performance and Load Tests for ToolboxAI Platform

Tests API endpoint load handling, agent pool performance,
WebSocket connection limits, and overall system performance.
"""

import asyncio
import time
import pytest
import aiohttp
import websockets
from typing import List, Dict, Any
from concurrent.futures import ThreadPoolExecutor
import statistics
from datetime import datetime, timezone
import json

# Add project path
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent / "src" / "roblox-environment"))

# Skip all tests in this module as they require external services
pytestmark = pytest.mark.skip(reason="Performance tests require external services - run with --run-performance")


class PerformanceMetrics:
    """Track and calculate performance metrics"""
    
    def __init__(self):
        self.response_times: List[float] = []
        self.error_count = 0
        self.success_count = 0
        self.start_time = None
        self.end_time = None
    
    def start(self):
        """Start timing"""
        self.start_time = time.time()
    
    def stop(self):
        """Stop timing"""
        self.end_time = time.time()
    
    def add_response_time(self, duration: float):
        """Add response time measurement"""
        self.response_times.append(duration)
        self.success_count += 1
    
    def add_error(self):
        """Increment error count"""
        self.error_count += 1
    
    def get_statistics(self) -> Dict[str, Any]:
        """Calculate and return statistics"""
        if not self.response_times:
            return {"error": "No data collected"}
        
        total_time = (self.end_time or time.time()) - (self.start_time or 0)
        total_requests = self.success_count + self.error_count
        
        return {
            "total_requests": total_requests,
            "successful_requests": self.success_count,
            "failed_requests": self.error_count,
            "error_rate": (self.error_count / total_requests * 100) if total_requests > 0 else 0,
            "total_time_seconds": total_time,
            "requests_per_second": total_requests / total_time if total_time > 0 else 0,
            "response_times": {
                "min": min(self.response_times),
                "max": max(self.response_times),
                "mean": statistics.mean(self.response_times),
                "median": statistics.median(self.response_times),
                "p95": statistics.quantiles(self.response_times, n=20)[18] if len(self.response_times) > 20 else max(self.response_times),
                "p99": statistics.quantiles(self.response_times, n=100)[98] if len(self.response_times) > 100 else max(self.response_times),
                "stdev": statistics.stdev(self.response_times) if len(self.response_times) > 1 else 0
            }
        }


class TestAPILoadPerformance:
    """Test API endpoint load handling"""
    
    @pytest.mark.asyncio(loop_scope="function")
    async def test_content_generation_load(self):
        """Test content generation endpoint under load"""
        url = "http://localhost:8008/generate_content"
        concurrent_requests = 50
        total_requests = 200
        
        metrics = PerformanceMetrics()
        
        async def make_request(session: aiohttp.ClientSession):
            """Make single content generation request"""
            payload = {
                "subject": "Mathematics",
                "grade_level": 7,
                "topic": "Algebra",
                "learning_objectives": ["Understand variables"],
                "environment_type": "classroom",
                "include_quiz": True
            }
            
            start = time.time()
            try:
                async with session.post(url, json=payload) as response:
                    await response.json()
                    if response.status == 200:
                        metrics.add_response_time(time.time() - start)
                    else:
                        metrics.add_error()
            except Exception:
                metrics.add_error()
        
        # Run load test
        metrics.start()
        
        async with aiohttp.ClientSession() as session:
            # Create batches of concurrent requests
            for i in range(0, total_requests, concurrent_requests):
                batch = min(concurrent_requests, total_requests - i)
                tasks = [make_request(session) for _ in range(batch)]
                await asyncio.gather(*tasks)
        
        metrics.stop()
        
        # Analyze results
        stats = metrics.get_statistics()
        
        # Performance assertions
        assert stats["error_rate"] < 5, f"Error rate too high: {stats['error_rate']}%"
        assert stats["response_times"]["mean"] < 2.0, f"Mean response time too high: {stats['response_times']['mean']}s"
        assert stats["response_times"]["p95"] < 5.0, f"P95 response time too high: {stats['response_times']['p95']}s"
        assert stats["requests_per_second"] > 10, f"Throughput too low: {stats['requests_per_second']} RPS"
        
        print(f"\nContent Generation Load Test Results:")
        print(json.dumps(stats, indent=2))
    
    @pytest.mark.asyncio(loop_scope="function")
    async def test_authentication_load(self):
        """Test authentication endpoint under load"""
        url = "http://localhost:8008/auth/login"
        concurrent_users = 100
        
        metrics = PerformanceMetrics()
        
        async def authenticate_user(session: aiohttp.ClientSession, user_id: int):
            """Authenticate single user"""
            payload = {
                "username": f"user_{user_id}",
                "password": "testpass123"
            }
            
            start = time.time()
            try:
                async with session.post(url, json=payload) as response:
                    await response.json()
                    if response.status in [200, 401]:  # Success or auth failure
                        metrics.add_response_time(time.time() - start)
                    else:
                        metrics.add_error()
            except Exception:
                metrics.add_error()
        
        metrics.start()
        
        async with aiohttp.ClientSession() as session:
            tasks = [authenticate_user(session, i) for i in range(concurrent_users)]
            await asyncio.gather(*tasks)
        
        metrics.stop()
        
        stats = metrics.get_statistics()
        
        # Authentication should be fast
        assert stats["response_times"]["mean"] < 0.5, f"Auth too slow: {stats['response_times']['mean']}s"
        assert stats["response_times"]["p99"] < 1.0, f"P99 auth too slow: {stats['response_times']['p99']}s"
        
        print(f"\nAuthentication Load Test Results:")
        print(json.dumps(stats, indent=2))
    
    @pytest.mark.asyncio(loop_scope="function")
    async def test_database_query_load(self):
        """Test database query performance under load"""
        url = "http://localhost:8008/courses/search"
        concurrent_queries = 30
        total_queries = 100
        
        metrics = PerformanceMetrics()
        
        async def query_courses(session: aiohttp.ClientSession):
            """Query courses from database"""
            params = {
                "subject": "Mathematics",
                "grade_level": 7,
                "limit": 20
            }
            
            start = time.time()
            try:
                async with session.get(url, params=params) as response:
                    await response.json()
                    if response.status == 200:
                        metrics.add_response_time(time.time() - start)
                    else:
                        metrics.add_error()
            except Exception:
                metrics.add_error()
        
        metrics.start()
        
        async with aiohttp.ClientSession() as session:
            for i in range(0, total_queries, concurrent_queries):
                batch = min(concurrent_queries, total_queries - i)
                tasks = [query_courses(session) for _ in range(batch)]
                await asyncio.gather(*tasks)
        
        metrics.stop()
        
        stats = metrics.get_statistics()
        
        # Database queries should be optimized
        assert stats["response_times"]["mean"] < 0.2, f"DB queries too slow: {stats['response_times']['mean']}s"
        assert stats["error_rate"] < 1, f"DB error rate too high: {stats['error_rate']}%"
        
        print(f"\nDatabase Query Load Test Results:")
        print(json.dumps(stats, indent=2))


class TestAgentPoolPerformance:
    """Test agent pool performance and scaling"""
    
    @pytest.mark.asyncio(loop_scope="function")
    async def test_agent_pool_scaling(self):
        """Test agent pool scaling under increasing load"""
        from core.agents.orchestrator import Orchestrator
        
        orchestrator = Orchestrator()
        
        # Test with increasing number of concurrent tasks
        load_levels = [10, 20, 50, 100]
        results = {}
        
        for load in load_levels:
            metrics = PerformanceMetrics()
            metrics.start()
            
            # Create tasks
            tasks = []
            for i in range(load):
                task = {
                    "type": "content" if i % 3 == 0 else "quiz" if i % 3 == 1 else "terrain",
                    "data": {"id": i, "complexity": "simple"}
                }
                tasks.append(task)
            
            # Execute tasks
            start = time.time()
            try:
                results_batch = await orchestrator.process_tasks_batch(tasks)
                duration = time.time() - start
                
                if results_batch:
                    metrics.add_response_time(duration)
                else:
                    metrics.add_error()
            except Exception:
                metrics.add_error()
            
            metrics.stop()
            
            results[f"load_{load}"] = {
                "total_time": metrics.end_time - metrics.start_time,
                "tasks_per_second": load / (metrics.end_time - metrics.start_time),
                "success": metrics.success_count > 0
            }
        
        # Verify scaling behavior
        # Should handle increasing load with sub-linear time increase
        time_10 = results["load_10"]["total_time"]
        time_100 = results["load_100"]["total_time"]
        
        # Time for 100 tasks should be less than 10x time for 10 tasks (parallel processing)
        assert time_100 < time_10 * 5, f"Poor scaling: {time_100}s for 100 tasks vs {time_10}s for 10 tasks"
        
        print(f"\nAgent Pool Scaling Test Results:")
        print(json.dumps(results, indent=2))
    
    @pytest.mark.asyncio(loop_scope="function")
    async def test_agent_memory_usage(self):
        """Test agent memory usage under sustained load"""
        import psutil
        import os
        
        from core.agents.supervisor import SupervisorAgent
        
        supervisor = SupervisorAgent()
        process = psutil.Process(os.getpid())
        
        # Baseline memory
        baseline_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Run sustained load
        duration = 30  # seconds
        tasks_per_second = 5
        memory_samples = []
        
        start_time = time.time()
        while time.time() - start_time < duration:
            # Create and execute task
            task = {
                "type": "content",
                "data": {"timestamp": time.time()}
            }
            
            try:
                await supervisor.process_task(task)
            except Exception:
                pass
            
            # Sample memory usage
            current_memory = process.memory_info().rss / 1024 / 1024
            memory_samples.append(current_memory)
            
            await asyncio.sleep(1 / tasks_per_second)
        
        # Analyze memory usage
        max_memory = max(memory_samples)
        avg_memory = statistics.mean(memory_samples)
        memory_growth = max_memory - baseline_memory
        
        # Memory should not grow excessively
        assert memory_growth < 500, f"Excessive memory growth: {memory_growth}MB"
        
        print(f"\nAgent Memory Usage Test Results:")
        print(f"Baseline: {baseline_memory:.2f}MB")
        print(f"Average: {avg_memory:.2f}MB")
        print(f"Maximum: {max_memory:.2f}MB")
        print(f"Growth: {memory_growth:.2f}MB")


class TestWebSocketPerformance:
    """Test WebSocket connection limits and performance"""
    
    @pytest.mark.asyncio(loop_scope="function")
    async def test_websocket_connection_limit(self):
        """Test maximum concurrent WebSocket connections"""
        url = "ws://localhost:9876"
        target_connections = 500
        successful_connections = []
        failed_connections = 0
        
        async def create_connection(index: int):
            """Create single WebSocket connection"""
            try:
                ws = await websockets.connect(url)
                successful_connections.append(ws)
                
                # Send initial message
                await ws.send(json.dumps({
                    "type": "subscribe",
                    "channel": f"test_{index}"
                }))
                
                # Keep connection alive
                await asyncio.sleep(5)
                
                # Close connection
                await ws.close()
                return True
            except Exception:
                return False
        
        # Create connections in batches
        batch_size = 50
        for i in range(0, target_connections, batch_size):
            batch = min(batch_size, target_connections - i)
            tasks = [create_connection(i + j) for j in range(batch)]
            results = await asyncio.gather(*tasks)
            failed_connections += results.count(False)
        
        successful_count = target_connections - failed_connections
        
        # Should handle at least 400 concurrent connections
        assert successful_count >= 400, f"Only handled {successful_count} connections"
        
        print(f"\nWebSocket Connection Limit Test:")
        print(f"Target: {target_connections}")
        print(f"Successful: {successful_count}")
        print(f"Failed: {failed_connections}")
    
    @pytest.mark.asyncio(loop_scope="function")
    async def test_websocket_message_throughput(self):
        """Test WebSocket message throughput"""
        url = "ws://localhost:9876"
        num_clients = 10
        messages_per_client = 100
        
        metrics = PerformanceMetrics()
        
        async def client_sender(client_id: int):
            """Client that sends messages"""
            try:
                async with websockets.connect(url) as ws:
                    for i in range(messages_per_client):
                        start = time.time()
                        
                        # Send message
                        await ws.send(json.dumps({
                            "type": "message",
                            "client_id": client_id,
                            "message_id": i,
                            "timestamp": time.time()
                        }))
                        
                        # Wait for echo/response
                        response = await ws.recv()
                        
                        metrics.add_response_time(time.time() - start)
                        
                        # Small delay between messages
                        await asyncio.sleep(0.01)
            except Exception:
                metrics.add_error()
        
        metrics.start()
        
        # Run all clients concurrently
        tasks = [client_sender(i) for i in range(num_clients)]
        await asyncio.gather(*tasks)
        
        metrics.stop()
        
        stats = metrics.get_statistics()
        total_messages = num_clients * messages_per_client
        
        # Calculate throughput
        throughput = total_messages / (metrics.end_time - metrics.start_time)
        
        # Should handle at least 500 messages per second
        assert throughput > 500, f"Low throughput: {throughput} messages/second"
        assert stats["response_times"]["mean"] < 0.05, f"High latency: {stats['response_times']['mean']}s"
        
        print(f"\nWebSocket Throughput Test:")
        print(f"Total messages: {total_messages}")
        print(f"Throughput: {throughput:.2f} messages/second")
        print(f"Mean latency: {stats['response_times']['mean']*1000:.2f}ms")


class TestCachingPerformance:
    """Test caching layer performance"""
    
    @pytest.mark.asyncio(loop_scope="function")
    async def test_cache_hit_performance(self):
        """Test performance improvement with caching"""
        from apps.backend.performance import cache_manager
        
        await cache_manager.initialize()
        
        # Test data
        test_key = "test_content_123"
        test_data = {
            "content": "x" * 1000,  # 1KB of data
            "metadata": {"type": "lesson", "id": "123"}
        }
        
        # Measure cache miss (first access)
        start = time.time()
        result = await cache_manager.get(test_key)
        miss_time = time.time() - start
        assert result is None
        
        # Store in cache
        await cache_manager.set(test_key, test_data)
        
        # Measure cache hit
        start = time.time()
        result = await cache_manager.get(test_key)
        hit_time = time.time() - start
        assert result == test_data
        
        # Cache hit should be much faster
        assert hit_time < miss_time * 0.1, f"Cache not providing speedup: hit={hit_time}s, miss={miss_time}s"
        
        # Test cache performance under load
        metrics = PerformanceMetrics()
        
        # Perform many cache operations
        num_operations = 1000
        metrics.start()
        
        for i in range(num_operations):
            key = f"key_{i % 100}"  # Use 100 different keys
            
            start = time.time()
            if i % 3 == 0:  # 33% writes
                await cache_manager.set(key, {"data": i})
            else:  # 67% reads
                await cache_manager.get(key)
            metrics.add_response_time(time.time() - start)
        
        metrics.stop()
        
        stats = metrics.get_statistics()
        
        # Cache operations should be very fast
        assert stats["response_times"]["mean"] < 0.001, f"Cache too slow: {stats['response_times']['mean']}s"
        
        cache_stats = cache_manager.get_stats()
        hit_rate = float(cache_stats["hit_rate"].rstrip("%"))
        
        # Should have good hit rate after warmup
        assert hit_rate > 50, f"Low cache hit rate: {hit_rate}%"
        
        print(f"\nCache Performance Test:")
        print(f"Operations: {num_operations}")
        print(f"Mean time: {stats['response_times']['mean']*1000:.3f}ms")
        print(f"Hit rate: {hit_rate}%")
        
        await cache_manager.close()


class TestSystemPerformance:
    """Test overall system performance"""
    
    @pytest.mark.asyncio(loop_scope="function")
    async def test_end_to_end_latency(self):
        """Test end-to-end latency for complete workflow"""
        metrics = PerformanceMetrics()
        
        async with aiohttp.ClientSession() as session:
            for i in range(10):
                start = time.time()
                
                try:
                    # Step 1: Generate content
                    content_response = await session.post(
                        "http://localhost:8008/generate_content",
                        json={
                            "subject": "Science",
                            "grade_level": 8,
                            "topic": "Solar System",
                            "learning_objectives": ["Understand planets"],
                            "include_quiz": True
                        }
                    )
                    content = await content_response.json()
                    
                    # Step 2: Save to database
                    save_response = await session.post(
                        "http://localhost:8008/content/save",
                        json=content
                    )
                    saved = await save_response.json()
                    
                    # Step 3: Send to Roblox
                    roblox_response = await session.post(
                        "http://localhost:5001/publish",
                        json=saved
                    )
                    
                    if roblox_response.status == 200:
                        metrics.add_response_time(time.time() - start)
                    else:
                        metrics.add_error()
                    
                except Exception:
                    metrics.add_error()
        
        stats = metrics.get_statistics()
        
        # End-to-end should complete within reasonable time
        assert stats["response_times"]["mean"] < 10.0, f"E2E too slow: {stats['response_times']['mean']}s"
        assert stats["error_rate"] < 10, f"E2E error rate too high: {stats['error_rate']}%"
        
        print(f"\nEnd-to-End Latency Test:")
        print(json.dumps(stats, indent=2))
    
    @pytest.mark.asyncio(loop_scope="function")
    async def test_resource_usage(self):
        """Test system resource usage under normal load"""
        import psutil
        
        # Get initial system state
        initial_cpu = psutil.cpu_percent(interval=1)
        initial_memory = psutil.virtual_memory().percent
        
        # Run normal workload for 60 seconds
        duration = 60
        requests_per_second = 10
        
        cpu_samples = []
        memory_samples = []
        
        async with aiohttp.ClientSession() as session:
            start_time = time.time()
            
            while time.time() - start_time < duration:
                # Make request
                try:
                    await session.get("http://localhost:8008/health")
                except Exception:
                    pass
                
                # Sample resource usage
                cpu_samples.append(psutil.cpu_percent(interval=0))
                memory_samples.append(psutil.virtual_memory().percent)
                
                await asyncio.sleep(1 / requests_per_second)
        
        # Analyze resource usage
        avg_cpu = statistics.mean(cpu_samples)
        max_cpu = max(cpu_samples)
        avg_memory = statistics.mean(memory_samples)
        max_memory = max(memory_samples)
        
        # Resource usage should be reasonable
        assert avg_cpu < 80, f"High average CPU usage: {avg_cpu}%"
        assert max_cpu < 95, f"CPU maxed out: {max_cpu}%"
        assert avg_memory < 80, f"High memory usage: {avg_memory}%"
        
        print(f"\nResource Usage Test:")
        print(f"CPU - Initial: {initial_cpu}%, Average: {avg_cpu:.1f}%, Max: {max_cpu:.1f}%")
        print(f"Memory - Initial: {initial_memory}%, Average: {avg_memory:.1f}%, Max: {max_memory:.1f}%")


def create_performance_report(test_results: Dict[str, Any]):
    """Create comprehensive performance report"""
    report = f"""
    ToolboxAI Performance Test Report
    ==================================
    Generated: {datetime.now(timezone.utc).isoformat()}
    
    Summary
    -------
    Total Tests Run: {test_results.get('total_tests', 0)}
    Passed: {test_results.get('passed', 0)}
    Failed: {test_results.get('failed', 0)}
    
    Key Metrics
    -----------
    API Throughput: {test_results.get('api_throughput', 'N/A')} requests/second
    Average Latency: {test_results.get('avg_latency', 'N/A')}ms
    P95 Latency: {test_results.get('p95_latency', 'N/A')}ms
    Error Rate: {test_results.get('error_rate', 'N/A')}%
    
    WebSocket Performance
    ---------------------
    Max Connections: {test_results.get('ws_max_connections', 'N/A')}
    Message Throughput: {test_results.get('ws_throughput', 'N/A')} msg/second
    
    Resource Usage
    --------------
    CPU Usage: {test_results.get('cpu_usage', 'N/A')}%
    Memory Usage: {test_results.get('memory_usage', 'N/A')}%
    
    Recommendations
    ---------------
    {test_results.get('recommendations', 'No specific recommendations')}
    """
    
    return report


if __name__ == "__main__":
    # Run performance tests and generate report
    pytest.main([__file__, "-v", "--tb=short"])