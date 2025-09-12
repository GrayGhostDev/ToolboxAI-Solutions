"""
API Performance Tests
Specific tests for API endpoint response times and throughput
"""

import asyncio
import time
import pytest
import aiohttp
import statistics
from typing import List, Dict, Any
import json


@pytest.mark.performance
class TestAPIPerformanceSpecific:
    """Specific API performance tests"""
    
    @pytest.mark.asyncio
    async def test_health_endpoint_performance(self):
        """Test health endpoint response time under load"""
        url = "http://localhost:8008/health"
        num_requests = 1000
        concurrent_requests = 50
        
        response_times = []
        
        async def make_request(session):
            start = time.time()
            async with session.get(url) as response:
                await response.text()
                response_times.append(time.time() - start)
                return response.status == 200
        
        async with aiohttp.ClientSession() as session:
            # Warmup
            await make_request(session)
            response_times.clear()
            
            # Actual test
            tasks = []
            for i in range(num_requests):
                if len(tasks) >= concurrent_requests:
                    await asyncio.gather(*tasks)
                    tasks.clear()
                tasks.append(make_request(session))
            
            if tasks:
                await asyncio.gather(*tasks)
        
        # Performance assertions
        avg_time = statistics.mean(response_times)
        p95_time = statistics.quantiles(response_times, n=20)[18] if len(response_times) > 20 else max(response_times)
        
        assert avg_time < 0.05, f"Health endpoint too slow: {avg_time:.3f}s average"
        assert p95_time < 0.1, f"Health endpoint P95 too slow: {p95_time:.3f}s"
        assert len(response_times) == num_requests, "Not all requests completed"
        
        print(f"Health Endpoint Performance:")
        print(f"  Requests: {num_requests}")
        print(f"  Average: {avg_time*1000:.2f}ms")
        print(f"  P95: {p95_time*1000:.2f}ms")
        print(f"  Min: {min(response_times)*1000:.2f}ms")
        print(f"  Max: {max(response_times)*1000:.2f}ms")
    
    @pytest.mark.asyncio
    async def test_content_generation_performance(self):
        """Test content generation endpoint performance"""
        url = "http://localhost:8008/generate_content"
        
        payload = {
            "subject": "Mathematics",
            "grade_level": 7,
            "topic": "Basic Algebra",
            "learning_objectives": ["Understand variables", "Solve simple equations"],
            "environment_type": "classroom",
            "include_quiz": True
        }
        
        response_times = []
        errors = 0
        
        async with aiohttp.ClientSession() as session:
            # Test with sequential requests for accurate timing
            for i in range(10):
                start = time.time()
                try:
                    async with session.post(url, json=payload) as response:
                        result = await response.json()
                        if response.status == 200:
                            response_times.append(time.time() - start)
                        else:
                            errors += 1
                except Exception:
                    errors += 1
        
        if response_times:
            avg_time = statistics.mean(response_times)
            max_time = max(response_times)
            min_time = min(response_times)
            
            # Content generation targets
            assert avg_time < 5.0, f"Content generation too slow: {avg_time:.2f}s average"
            assert max_time < 10.0, f"Content generation max too slow: {max_time:.2f}s"
            assert errors < 2, f"Too many errors: {errors}"
            
            print(f"Content Generation Performance:")
            print(f"  Requests: {len(response_times)}")
            print(f"  Average: {avg_time:.2f}s")
            print(f"  Min: {min_time:.2f}s")
            print(f"  Max: {max_time:.2f}s")
            print(f"  Errors: {errors}")
        else:
            pytest.fail("No successful content generation requests")
    
    @pytest.mark.asyncio
    async def test_database_query_performance(self):
        """Test database query performance"""
        endpoints = [
            ("http://localhost:8008/courses", "GET"),
            ("http://localhost:8008/users", "GET"),
            ("http://localhost:8008/content/search", "GET")
        ]
        
        results = {}
        
        async with aiohttp.ClientSession() as session:
            for url, method in endpoints:
                endpoint_name = url.split('/')[-1]
                response_times = []
                
                for i in range(20):
                    start = time.time()
                    try:
                        if method == "GET":
                            async with session.get(url) as response:
                                await response.json()
                                if response.status == 200:
                                    response_times.append(time.time() - start)
                    except Exception:
                        pass
                
                if response_times:
                    results[endpoint_name] = {
                        "avg": statistics.mean(response_times),
                        "min": min(response_times),
                        "max": max(response_times),
                        "count": len(response_times)
                    }
        
        # Database queries should be fast
        for endpoint, stats in results.items():
            assert stats["avg"] < 0.2, f"{endpoint} queries too slow: {stats['avg']:.3f}s average"
            assert stats["max"] < 0.5, f"{endpoint} max query too slow: {stats['max']:.3f}s"
            
            print(f"{endpoint.capitalize()} Query Performance:")
            print(f"  Average: {stats['avg']*1000:.2f}ms")
            print(f"  Min: {stats['min']*1000:.2f}ms")
            print(f"  Max: {stats['max']*1000:.2f}ms")
    
    @pytest.mark.asyncio
    async def test_rate_limiting_performance(self):
        """Test API rate limiting behavior"""
        url = "http://localhost:8008/health"
        
        # Send requests rapidly to test rate limiting
        response_codes = []
        response_times = []
        
        async with aiohttp.ClientSession() as session:
            start_time = time.time()
            
            # Send 200 requests as fast as possible
            tasks = []
            for i in range(200):
                tasks.append(self._make_timed_request(session, url))
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            total_time = time.time() - start_time
            
            for result in results:
                if isinstance(result, tuple):
                    status, duration = result
                    response_codes.append(status)
                    response_times.append(duration)
        
        # Analyze rate limiting
        success_rate = (response_codes.count(200) / len(response_codes)) * 100
        rate_limited = response_codes.count(429)  # Too Many Requests
        throughput = len(response_codes) / total_time
        
        print(f"Rate Limiting Performance:")
        print(f"  Total requests: {len(response_codes)}")
        print(f"  Success rate: {success_rate:.1f}%")
        print(f"  Rate limited: {rate_limited}")
        print(f"  Throughput: {throughput:.1f} req/s")
        print(f"  Total time: {total_time:.2f}s")
        
        # Should handle reasonable load without too much rate limiting
        assert success_rate > 80, f"Too much rate limiting: {success_rate:.1f}% success"
    
    async def _make_timed_request(self, session, url):
        """Helper to make timed request"""
        start = time.time()
        try:
            async with session.get(url) as response:
                await response.text()
                return response.status, time.time() - start
        except Exception:
            return 500, time.time() - start