#!/usr/bin/env python3

import asyncio
import aiohttp
import time
import statistics
import json
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LoadTester:
    def __init__(self, base_url="http://localhost:8008"):
        self.base_url = base_url
        self.results = []
        self.start_time = None
        self.end_time = None
    
    async def test_endpoint(self, session, endpoint, method="GET", data=None, headers=None):
        """Test a single endpoint"""
        start = time.time()
        try:
            if headers is None:
                headers = {"Content-Type": "application/json"}
                
            async with session.request(
                method, 
                f"{self.base_url}{endpoint}",
                json=data,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                duration = time.time() - start
                response_text = await response.text()
                return {
                    "endpoint": endpoint,
                    "method": method,
                    "status": response.status,
                    "duration": duration,
                    "success": 200 <= response.status < 300,
                    "timestamp": datetime.utcnow().isoformat(),
                    "size": len(response_text)
                }
        except asyncio.TimeoutError:
            return {
                "endpoint": endpoint,
                "method": method,
                "status": 0,
                "duration": time.time() - start,
                "success": False,
                "error": "Timeout",
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            return {
                "endpoint": endpoint,
                "method": method,
                "status": 0,
                "duration": time.time() - start,
                "success": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def run_concurrent_batch(self, session, endpoints, concurrent_users):
        """Run a batch of concurrent requests"""
        tasks = []
        for endpoint, method, data in endpoints:
            for _ in range(concurrent_users // len(endpoints)):
                task = asyncio.create_task(
                    self.test_endpoint(session, endpoint, method, data)
                )
                tasks.append(task)
        
        return await asyncio.gather(*tasks)
    
    async def run_load_test(self, concurrent_users=50, duration_seconds=30):
        """Run the load test"""
        logger.info(f"🚀 Starting load test: {concurrent_users} concurrent users for {duration_seconds}s")
        logger.info(f"Target: {self.base_url}")
        logger.info("=" * 60)
        
        # Define test endpoints
        endpoints = [
            ("/health", "GET", None),
            ("/generate_content", "POST", {"subject": "Math", "grade_level": 5}),
            ("/auth/login", "POST", {"username": "test_user", "password": "test_pass"}),
        ]
        
        # Add Flask Bridge endpoint if available
        flask_endpoints = [
            ("http://localhost:5001/health", "GET", None),
            ("http://localhost:5001/plugin/register", "POST", {"plugin_id": "load_test", "version": "1.0.0"}),
        ]
        
        self.start_time = time.time()
        
        # Create session with connection pooling
        connector = aiohttp.TCPConnector(limit=100, limit_per_host=30)
        async with aiohttp.ClientSession(connector=connector) as session:
            batch_count = 0
            
            while time.time() - self.start_time < duration_seconds:
                batch_count += 1
                logger.info(f"Running batch {batch_count}...")
                
                # Run batch of requests
                batch_results = await self.run_concurrent_batch(
                    session, endpoints, concurrent_users
                )
                self.results.extend(batch_results)
                
                # Brief pause between batches to avoid overwhelming the server
                await asyncio.sleep(0.5)
        
        self.end_time = time.time()
        self.print_results()
        self.save_results()
    
    def calculate_percentile(self, data, percentile):
        """Calculate percentile from data"""
        if not data:
            return 0
        size = len(data)
        if size == 0:
            return 0
        sorted_data = sorted(data)
        index = int(size * percentile / 100)
        if index >= size:
            index = size - 1
        return sorted_data[index]
    
    def print_results(self):
        """Print load test results"""
        total_duration = self.end_time - self.start_time
        
        logger.info("\n" + "=" * 60)
        logger.info("📊 LOAD TEST RESULTS")
        logger.info("=" * 60)
        logger.info(f"Test Duration: {total_duration:.2f} seconds")
        logger.info(f"Total Requests: {len(self.results)}")
        logger.info(f"Requests/Second: {len(self.results) / total_duration:.2f}")
        
        # Group by endpoint
        endpoints = {}
        for result in self.results:
            endpoint_key = f"{result['method']} {result['endpoint']}"
            if endpoint_key not in endpoints:
                endpoints[endpoint_key] = []
            endpoints[endpoint_key].append(result)
        
        # Print statistics for each endpoint
        for endpoint, results in endpoints.items():
            logger.info(f"\n📍 {endpoint}")
            logger.info("-" * 40)
            
            successful = [r for r in results if r['success']]
            failed = [r for r in results if not r['success']]
            
            logger.info(f"  Total Requests: {len(results)}")
            logger.info(f"  Successful: {len(successful)} ({len(successful)/len(results)*100:.1f}%)")
            logger.info(f"  Failed: {len(failed)} ({len(failed)/len(results)*100:.1f}%)")
            
            if successful:
                durations = [r['duration'] * 1000 for r in successful]  # Convert to ms
                logger.info(f"  Response Times (ms):")
                logger.info(f"    Min: {min(durations):.1f}")
                logger.info(f"    Max: {max(durations):.1f}")
                logger.info(f"    Mean: {statistics.mean(durations):.1f}")
                logger.info(f"    Median: {statistics.median(durations):.1f}")
                logger.info(f"    P95: {self.calculate_percentile(durations, 95):.1f}")
                logger.info(f"    P99: {self.calculate_percentile(durations, 99):.1f}")
                
                # Check if P95 is under 200ms (success criteria)
                p95 = self.calculate_percentile(durations, 95)
                if p95 < 200:
                    logger.info(f"    ✅ P95 < 200ms - Performance target MET")
                else:
                    logger.warning(f"    ⚠️ P95 > 200ms - Performance target NOT met")
            
            if failed:
                # Show error breakdown
                errors = {}
                for r in failed:
                    error = r.get('error', f"HTTP {r.get('status', 'Unknown')}")
                    errors[error] = errors.get(error, 0) + 1
                
                logger.info(f"  Error Breakdown:")
                for error, count in errors.items():
                    logger.info(f"    {error}: {count}")
        
        # Overall statistics
        logger.info("\n" + "=" * 60)
        logger.info("📈 OVERALL STATISTICS")
        logger.info("=" * 60)
        
        all_successful = [r for r in self.results if r['success']]
        success_rate = len(all_successful) / len(self.results) * 100 if self.results else 0
        
        logger.info(f"Overall Success Rate: {success_rate:.1f}%")
        logger.info(f"Total Throughput: {len(self.results) / total_duration:.1f} req/s")
        
        if all_successful:
            all_durations = [r['duration'] * 1000 for r in all_successful]
            overall_p95 = self.calculate_percentile(all_durations, 95)
            logger.info(f"Overall P95 Response Time: {overall_p95:.1f}ms")
            
            if overall_p95 < 200:
                logger.info("\n🎉 LOAD TEST PASSED - All performance criteria met!")
            else:
                logger.warning("\n⚠️ LOAD TEST WARNING - P95 response time exceeds 200ms target")
        else:
            logger.error("\n❌ LOAD TEST FAILED - No successful requests")
    
    def save_results(self):
        """Save detailed results to file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"load_test_results_{timestamp}.json"
        
        report = {
            "timestamp": datetime.utcnow().isoformat(),
            "configuration": {
                "base_url": self.base_url,
                "duration": self.end_time - self.start_time if self.end_time else 0,
                "total_requests": len(self.results)
            },
            "summary": {
                "success_rate": sum(1 for r in self.results if r['success']) / len(self.results) * 100 if self.results else 0,
                "total_requests": len(self.results),
                "requests_per_second": len(self.results) / (self.end_time - self.start_time) if self.end_time else 0
            },
            "results": self.results[:1000]  # Save first 1000 results to avoid huge files
        }
        
        with open(filename, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"\n📄 Detailed results saved to: {filename}")


async def main():
    """Main function to run load test"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Load test for Terminal 1 services')
    parser.add_argument('--users', type=int, default=50, help='Number of concurrent users')
    parser.add_argument('--duration', type=int, default=30, help='Test duration in seconds')
    parser.add_argument('--url', type=str, default='http://localhost:8008', help='Base URL to test')
    
    args = parser.parse_args()
    
    tester = LoadTester(base_url=args.url)
    await tester.run_load_test(
        concurrent_users=args.users,
        duration_seconds=args.duration
    )

if __name__ == "__main__":
    asyncio.run(main())