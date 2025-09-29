#!/usr/bin/env python3
"""
Smoke Tests for ToolboxAI Solutions
Verifies basic functionality of deployed services
"""

import argparse
import json
import sys
import time
from typing import Dict, List, Optional
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry


class SmokeTestRunner:
    """Runs smoke tests against deployed environments."""

    def __init__(self, environment: str):
        self.environment = environment
        self.base_urls = {
            'development': 'https://dev.toolboxai.solutions',
            'staging': 'https://staging.toolboxai.solutions',
            'production': 'https://app.toolboxai.solutions'
        }
        self.base_url = self.base_urls.get(environment, 'http://localhost:8009')
        self.session = self._create_session()
        self.results: List[Dict] = []

    def _create_session(self) -> requests.Session:
        """Create HTTP session with retries."""
        session = requests.Session()
        retry = Retry(
            total=3,
            read=3,
            connect=3,
            backoff_factor=0.3,
            status_forcelist=(500, 502, 504)
        )
        adapter = HTTPAdapter(max_retries=retry)
        session.mount('http://', adapter)
        session.mount('https://', adapter)
        return session

    def test_health_check(self) -> bool:
        """Test health check endpoint."""
        try:
            response = self.session.get(
                f"{self.base_url}/health",
                timeout=10
            )
            success = response.status_code == 200
            self.results.append({
                'test': 'health_check',
                'passed': success,
                'message': f'Health check returned {response.status_code}'
            })
            return success
        except Exception as e:
            self.results.append({
                'test': 'health_check',
                'passed': False,
                'message': f'Health check failed: {str(e)}'
            })
            return False

    def test_api_version(self) -> bool:
        """Test API version endpoint."""
        try:
            response = self.session.get(
                f"{self.base_url}/api/v1/version",
                timeout=10
            )
            success = response.status_code == 200
            if success:
                data = response.json()
                self.results.append({
                    'test': 'api_version',
                    'passed': True,
                    'message': f'API version: {data.get("version", "unknown")}'
                })
            else:
                self.results.append({
                    'test': 'api_version',
                    'passed': False,
                    'message': f'API version returned {response.status_code}'
                })
            return success
        except Exception as e:
            self.results.append({
                'test': 'api_version',
                'passed': False,
                'message': f'API version failed: {str(e)}'
            })
            return False

    def test_database_connection(self) -> bool:
        """Test database connectivity through status endpoint."""
        try:
            response = self.session.get(
                f"{self.base_url}/api/v1/status",
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                db_status = data.get('database', {}).get('status', 'unknown')
                success = db_status == 'connected'
                self.results.append({
                    'test': 'database_connection',
                    'passed': success,
                    'message': f'Database status: {db_status}'
                })
            else:
                self.results.append({
                    'test': 'database_connection',
                    'passed': False,
                    'message': f'Status endpoint returned {response.status_code}'
                })
                success = False
            return success
        except Exception as e:
            self.results.append({
                'test': 'database_connection',
                'passed': False,
                'message': f'Database check failed: {str(e)}'
            })
            return False

    def test_redis_connection(self) -> bool:
        """Test Redis connectivity through status endpoint."""
        try:
            response = self.session.get(
                f"{self.base_url}/api/v1/status",
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                redis_status = data.get('redis', {}).get('status', 'unknown')
                success = redis_status == 'connected'
                self.results.append({
                    'test': 'redis_connection',
                    'passed': success,
                    'message': f'Redis status: {redis_status}'
                })
            else:
                self.results.append({
                    'test': 'redis_connection',
                    'passed': False,
                    'message': f'Status endpoint returned {response.status_code}'
                })
                success = False
            return success
        except Exception as e:
            self.results.append({
                'test': 'redis_connection',
                'passed': False,
                'message': f'Redis check failed: {str(e)}'
            })
            return False

    def test_dashboard_availability(self) -> bool:
        """Test dashboard is accessible."""
        try:
            # For localhost, use port 5179
            if 'localhost' in self.base_url:
                dashboard_url = 'http://localhost:5179'
            else:
                dashboard_url = self.base_url

            response = self.session.get(dashboard_url, timeout=10)
            success = response.status_code == 200
            self.results.append({
                'test': 'dashboard_availability',
                'passed': success,
                'message': f'Dashboard returned {response.status_code}'
            })
            return success
        except Exception as e:
            self.results.append({
                'test': 'dashboard_availability',
                'passed': False,
                'message': f'Dashboard check failed: {str(e)}'
            })
            return False

    def test_api_authentication(self) -> bool:
        """Test API authentication endpoint."""
        try:
            response = self.session.post(
                f"{self.base_url}/api/v1/auth/test",
                json={'test': True},
                timeout=10
            )
            # We expect either 200 (if test endpoint exists) or 404/401
            success = response.status_code in [200, 401, 404]
            self.results.append({
                'test': 'api_authentication',
                'passed': success,
                'message': f'Auth endpoint returned {response.status_code}'
            })
            return success
        except Exception as e:
            self.results.append({
                'test': 'api_authentication',
                'passed': False,
                'message': f'Auth check failed: {str(e)}'
            })
            return False

    def run_all_tests(self) -> bool:
        """Run all smoke tests."""
        print(f"\n🔍 Running smoke tests for {self.environment} environment")
        print(f"   Base URL: {self.base_url}\n")

        tests = [
            self.test_health_check,
            self.test_api_version,
            self.test_database_connection,
            self.test_redis_connection,
            self.test_dashboard_availability,
            self.test_api_authentication
        ]

        all_passed = True
        for test in tests:
            passed = test()
            all_passed = all_passed and passed

        return all_passed

    def print_results(self):
        """Print test results."""
        print("\n" + "="*50)
        print("SMOKE TEST RESULTS")
        print("="*50)

        for result in self.results:
            status = "✅ PASS" if result['passed'] else "❌ FAIL"
            print(f"{status} | {result['test']}: {result['message']}")

        passed = sum(1 for r in self.results if r['passed'])
        total = len(self.results)

        print("="*50)
        print(f"SUMMARY: {passed}/{total} tests passed")

        if passed == total:
            print("✅ All smoke tests passed!")
        else:
            print(f"⚠️  {total - passed} test(s) failed")

        return passed == total


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Run smoke tests')
    parser.add_argument(
        '--env',
        required=True,
        choices=['development', 'staging', 'production'],
        help='Environment to test'
    )
    parser.add_argument(
        '--timeout',
        type=int,
        default=30,
        help='Overall timeout in seconds'
    )

    args = parser.parse_args()

    runner = SmokeTestRunner(args.env)

    try:
        all_passed = runner.run_all_tests()
        runner.print_results()

        if not all_passed:
            sys.exit(1)

    except KeyboardInterrupt:
        print("\n⚠️  Tests interrupted")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error running smoke tests: {e}")
        sys.exit(1)

    sys.exit(0)


if __name__ == '__main__':
    main()