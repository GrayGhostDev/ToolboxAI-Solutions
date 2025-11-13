#!/usr/bin/env python3
"""
Performance Tests for ToolboxAI Solutions
Load testing and performance benchmarking for deployed services
"""

import argparse
import concurrent.futures
import json
import statistics
import sys
import time

import requests
from requests.adapters import HTTPAdapter


class PerformanceTestRunner:
    """Runs performance tests against deployed environments."""

    def __init__(self, environment: str):
        self.environment = environment
        self.base_urls = {
            "development": "https://dev.toolboxai.solutions",
            "staging": "https://staging.toolboxai.solutions",
            "production": "https://app.toolboxai.solutions",
        }
        self.base_url = self.base_urls.get(environment, "http://localhost:8009")
        self.results = {
            "environment": environment,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "tests": {},
            "summary": {},
        }

    def _create_session(self) -> requests.Session:
        """Create HTTP session without retries for accurate timing."""
        session = requests.Session()
        adapter = HTTPAdapter(pool_connections=100, pool_maxsize=100)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        return session

    def _make_request(
        self, url: str, method: str = "GET", **kwargs
    ) -> tuple[float, int, str | None]:
        """Make a single request and return timing info."""
        session = self._create_session()
        start_time = time.time()
        error = None
        status_code = 0

        try:
            if method == "GET":
                response = session.get(url, timeout=30, **kwargs)
            elif method == "POST":
                response = session.post(url, timeout=30, **kwargs)
            else:
                response = session.request(method, url, timeout=30, **kwargs)

            status_code = response.status_code
            response_time = (time.time() - start_time) * 1000  # Convert to ms

            return response_time, status_code, error

        except requests.exceptions.Timeout:
            response_time = (time.time() - start_time) * 1000
            return response_time, 0, "Timeout"
        except requests.exceptions.ConnectionError:
            response_time = (time.time() - start_time) * 1000
            return response_time, 0, "Connection Error"
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return response_time, 0, str(e)
        finally:
            session.close()

    def test_endpoint_performance(
        self, name: str, url: str, requests_count: int = 100, concurrent_users: int = 10
    ) -> dict:
        """Test performance of a single endpoint."""
        print(f"\n  Testing {name}...")
        print(f"    URL: {url}")
        print(f"    Requests: {requests_count}, Concurrent users: {concurrent_users}")

        response_times = []
        status_codes = {}
        errors = []

        with concurrent.futures.ThreadPoolExecutor(max_workers=concurrent_users) as executor:
            futures = []
            for _ in range(requests_count):
                future = executor.submit(self._make_request, url)
                futures.append(future)

            for future in concurrent.futures.as_completed(futures):
                try:
                    response_time, status_code, error = future.result(timeout=35)
                    response_times.append(response_time)

                    if status_code not in status_codes:
                        status_codes[status_code] = 0
                    status_codes[status_code] += 1

                    if error:
                        errors.append(error)
                except Exception as e:
                    errors.append(str(e))

        # Calculate statistics
        if response_times:
            stats = {
                "name": name,
                "url": url,
                "requests_total": requests_count,
                "requests_successful": len(response_times) - len(errors),
                "requests_failed": len(errors),
                "response_time_avg": statistics.mean(response_times),
                "response_time_median": statistics.median(response_times),
                "response_time_min": min(response_times),
                "response_time_max": max(response_times),
                "response_time_p95": self._percentile(response_times, 95),
                "response_time_p99": self._percentile(response_times, 99),
                "status_codes": status_codes,
                "errors": len(errors),
                "error_rate": (len(errors) / requests_count) * 100,
                "requests_per_second": (
                    requests_count / (max(response_times) / 1000) if response_times else 0
                ),
            }
        else:
            stats = {
                "name": name,
                "url": url,
                "requests_total": requests_count,
                "requests_successful": 0,
                "requests_failed": requests_count,
                "error_rate": 100,
                "errors": errors,
            }

        return stats

    def _percentile(self, data: list[float], percentile: int) -> float:
        """Calculate percentile value."""
        if not data:
            return 0
        size = len(data)
        sorted_data = sorted(data)
        index = int(size * percentile / 100)
        if index >= size:
            index = size - 1
        return sorted_data[index]

    def run_load_test(self, duration_seconds: int = 60, target_rps: int = 10) -> dict:
        """Run a sustained load test."""
        print(f"\n🔥 Running load test for {duration_seconds} seconds at {target_rps} req/s")

        url = f"{self.base_url}/api/v1/health"
        delay_between_requests = 1.0 / target_rps

        response_times = []
        errors = []
        start_time = time.time()
        requests_sent = 0

        with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
            futures = []

            while time.time() - start_time < duration_seconds:
                future = executor.submit(self._make_request, url)
                futures.append(future)
                requests_sent += 1
                time.sleep(delay_between_requests)

            # Collect results
            for future in concurrent.futures.as_completed(futures):
                try:
                    response_time, status_code, error = future.result(timeout=35)
                    response_times.append(response_time)
                    if error:
                        errors.append(error)
                except Exception as e:
                    errors.append(str(e))

        actual_duration = time.time() - start_time

        if response_times:
            stats = {
                "test_type": "load_test",
                "duration_seconds": actual_duration,
                "target_rps": target_rps,
                "actual_rps": requests_sent / actual_duration,
                "requests_total": requests_sent,
                "requests_successful": len(response_times) - len(errors),
                "requests_failed": len(errors),
                "response_time_avg": statistics.mean(response_times),
                "response_time_p95": self._percentile(response_times, 95),
                "response_time_p99": self._percentile(response_times, 99),
                "error_rate": (len(errors) / requests_sent) * 100 if requests_sent > 0 else 0,
            }
        else:
            stats = {
                "test_type": "load_test",
                "duration_seconds": actual_duration,
                "requests_total": requests_sent,
                "requests_failed": requests_sent,
                "error_rate": 100,
            }

        return stats

    def run_stress_test(self, max_concurrent_users: int = 100) -> dict:
        """Run stress test to find breaking point."""
        print(f"\n💥 Running stress test up to {max_concurrent_users} concurrent users")

        url = f"{self.base_url}/api/v1/health"
        concurrent_levels = [1, 5, 10, 25, 50, 75, 100]
        concurrent_levels = [c for c in concurrent_levels if c <= max_concurrent_users]

        stress_results = []

        for concurrent_users in concurrent_levels:
            print(f"  Testing with {concurrent_users} concurrent users...")

            response_times = []
            errors = []
            requests_per_user = 10

            with concurrent.futures.ThreadPoolExecutor(max_workers=concurrent_users) as executor:
                futures = []
                for _ in range(concurrent_users * requests_per_user):
                    future = executor.submit(self._make_request, url)
                    futures.append(future)

                for future in concurrent.futures.as_completed(futures):
                    try:
                        response_time, status_code, error = future.result(timeout=35)
                        response_times.append(response_time)
                        if error:
                            errors.append(error)
                    except Exception as e:
                        errors.append(str(e))

            error_rate = (len(errors) / (concurrent_users * requests_per_user)) * 100

            level_stats = {
                "concurrent_users": concurrent_users,
                "requests_total": concurrent_users * requests_per_user,
                "response_time_avg": statistics.mean(response_times) if response_times else 0,
                "response_time_p95": self._percentile(response_times, 95) if response_times else 0,
                "error_rate": error_rate,
            }

            stress_results.append(level_stats)

            # Stop if error rate is too high
            if error_rate > 50:
                print(
                    f"    ⚠️  Error rate exceeded 50% at {concurrent_users} users. Stopping stress test."
                )
                break

        return {
            "test_type": "stress_test",
            "max_concurrent_tested": concurrent_levels[-1] if concurrent_levels else 0,
            "results_by_level": stress_results,
        }

    def run_all_tests(self, quick: bool = False) -> bool:
        """Run all performance tests."""
        print(f"\n⚡ Running performance tests for {self.environment} environment")
        print(f"   Base URL: {self.base_url}")

        all_passed = True

        # Test individual endpoints
        endpoints = [
            ("Health Check", f"{self.base_url}/health"),
            ("API Status", f"{self.base_url}/api/v1/status"),
            ("API Version", f"{self.base_url}/api/v1/version"),
        ]

        endpoint_results = []
        for name, url in endpoints:
            requests_count = 50 if quick else 100
            concurrent = 5 if quick else 10
            result = self.test_endpoint_performance(name, url, requests_count, concurrent)
            endpoint_results.append(result)

            # Check if performance is acceptable
            if result.get("response_time_p95", float("inf")) > 1000:  # 1 second
                all_passed = False
            if result.get("error_rate", 100) > 5:  # 5% error rate
                all_passed = False

        self.results["tests"]["endpoints"] = endpoint_results

        if not quick:
            # Run load test
            load_result = self.run_load_test(duration_seconds=30, target_rps=10)
            self.results["tests"]["load_test"] = load_result

            if load_result.get("error_rate", 100) > 10:
                all_passed = False

            # Run stress test
            stress_result = self.run_stress_test(max_concurrent_users=50)
            self.results["tests"]["stress_test"] = stress_result

        # Calculate summary
        self.results["summary"] = self._calculate_summary()
        self.results["passed"] = all_passed

        return all_passed

    def _calculate_summary(self) -> dict:
        """Calculate performance test summary."""
        summary = {
            "total_requests": 0,
            "total_errors": 0,
            "avg_response_time": [],
            "performance_grade": "A",
        }

        # Aggregate endpoint results
        if "endpoints" in self.results["tests"]:
            for endpoint in self.results["tests"]["endpoints"]:
                summary["total_requests"] += endpoint.get("requests_total", 0)
                summary["total_errors"] += endpoint.get("requests_failed", 0)
                if "response_time_avg" in endpoint:
                    summary["avg_response_time"].append(endpoint["response_time_avg"])

        # Calculate overall metrics
        if summary["avg_response_time"]:
            summary["avg_response_time"] = statistics.mean(summary["avg_response_time"])
        else:
            summary["avg_response_time"] = 0

        if summary["total_requests"] > 0:
            summary["error_rate"] = (summary["total_errors"] / summary["total_requests"]) * 100
        else:
            summary["error_rate"] = 0

        # Grade performance
        if summary["avg_response_time"] > 1000 or summary["error_rate"] > 10:
            summary["performance_grade"] = "F"
        elif summary["avg_response_time"] > 500 or summary["error_rate"] > 5:
            summary["performance_grade"] = "C"
        elif summary["avg_response_time"] > 200 or summary["error_rate"] > 2:
            summary["performance_grade"] = "B"
        else:
            summary["performance_grade"] = "A"

        return summary

    def print_results(self):
        """Print formatted test results."""
        print("\n" + "=" * 70)
        print("PERFORMANCE TEST RESULTS")
        print("=" * 70)

        # Endpoint tests
        if "endpoints" in self.results["tests"]:
            print("\n📊 Endpoint Performance:")
            for endpoint in self.results["tests"]["endpoints"]:
                print(f"\n  {endpoint['name']}:")
                print(
                    f"    Requests: {endpoint.get('requests_successful', 0)}/{endpoint.get('requests_total', 0)}"
                )
                print(f"    Avg Response Time: {endpoint.get('response_time_avg', 0):.0f}ms")
                print(f"    P95 Response Time: {endpoint.get('response_time_p95', 0):.0f}ms")
                print(f"    P99 Response Time: {endpoint.get('response_time_p99', 0):.0f}ms")
                print(f"    Error Rate: {endpoint.get('error_rate', 0):.1f}%")

        # Load test
        if "load_test" in self.results["tests"]:
            load = self.results["tests"]["load_test"]
            print(f"\n🔥 Load Test Results:")
            print(f"    Duration: {load.get('duration_seconds', 0):.0f}s")
            print(f"    Target RPS: {load.get('target_rps', 0)}")
            print(f"    Actual RPS: {load.get('actual_rps', 0):.1f}")
            print(f"    Avg Response Time: {load.get('response_time_avg', 0):.0f}ms")
            print(f"    P95 Response Time: {load.get('response_time_p95', 0):.0f}ms")
            print(f"    Error Rate: {load.get('error_rate', 0):.1f}%")

        # Stress test
        if "stress_test" in self.results["tests"]:
            stress = self.results["tests"]["stress_test"]
            print(f"\n💥 Stress Test Results:")
            for level in stress.get("results_by_level", []):
                print(
                    f"    {level['concurrent_users']} users: "
                    f"{level.get('response_time_avg', 0):.0f}ms avg, "
                    f"{level.get('error_rate', 0):.1f}% errors"
                )

        # Summary
        summary = self.results.get("summary", {})
        print("\n" + "=" * 70)
        print(f"Performance Grade: {summary.get('performance_grade', 'N/A')}")
        print(f"Total Requests: {summary.get('total_requests', 0)}")
        print(f"Overall Error Rate: {summary.get('error_rate', 0):.1f}%")
        print(f"Average Response Time: {summary.get('avg_response_time', 0):.0f}ms")

        if self.results.get("passed"):
            print("\n✅ Performance tests PASSED")
        else:
            print("\n❌ Performance tests FAILED")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Run performance tests")
    parser.add_argument(
        "--env",
        required=True,
        choices=["development", "staging", "production"],
        help="Environment to test",
    )
    parser.add_argument("--quick", action="store_true", help="Run quick tests only")
    parser.add_argument(
        "--output", choices=["console", "json"], default="console", help="Output format"
    )

    args = parser.parse_args()

    runner = PerformanceTestRunner(args.env)

    try:
        all_passed = runner.run_all_tests(quick=args.quick)

        if args.output == "json":
            print(json.dumps(runner.results, indent=2))
        else:
            runner.print_results()

        if not all_passed:
            sys.exit(1)

    except KeyboardInterrupt:
        print("\n⚠️  Performance tests interrupted")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error running performance tests: {e}")
        sys.exit(1)

    sys.exit(0)


if __name__ == "__main__":
    main()
