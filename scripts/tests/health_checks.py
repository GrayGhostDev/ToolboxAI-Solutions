#!/usr/bin/env python3
"""
Health Checks for ToolboxAI Solutions
Comprehensive health monitoring for deployed services
"""

import argparse
import json
import sys
import time
import concurrent.futures
from typing import Dict, List, Optional, Tuple
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry


class HealthChecker:
    """Performs comprehensive health checks on deployed services."""

    def __init__(self, environment: str):
        self.environment = environment
        self.base_urls = {
            'development': 'https://dev.toolboxai.solutions',
            'staging': 'https://staging.toolboxai.solutions',
            'production': 'https://app.toolboxai.solutions'
        }
        self.base_url = self.base_urls.get(environment, 'http://localhost:8009')
        self.session = self._create_session()
        self.results: Dict[str, Dict] = {}

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

    def check_service_health(self, service_name: str, url: str, expected_status: int = 200) -> Dict:
        """Check health of a specific service."""
        start_time = time.time()
        try:
            response = self.session.get(url, timeout=10)
            response_time = (time.time() - start_time) * 1000  # ms

            is_healthy = response.status_code == expected_status

            result = {
                'service': service_name,
                'url': url,
                'healthy': is_healthy,
                'status_code': response.status_code,
                'response_time_ms': round(response_time, 2),
                'message': 'OK' if is_healthy else f'Expected {expected_status}, got {response.status_code}'
            }

            # Try to extract additional info from response
            if response.status_code == 200:
                try:
                    data = response.json()
                    if 'version' in data:
                        result['version'] = data['version']
                    if 'status' in data:
                        result['status'] = data['status']
                except:
                    pass

            return result

        except requests.exceptions.Timeout:
            return {
                'service': service_name,
                'url': url,
                'healthy': False,
                'status_code': None,
                'response_time_ms': (time.time() - start_time) * 1000,
                'message': 'Request timeout'
            }
        except requests.exceptions.ConnectionError:
            return {
                'service': service_name,
                'url': url,
                'healthy': False,
                'status_code': None,
                'response_time_ms': (time.time() - start_time) * 1000,
                'message': 'Connection failed'
            }
        except Exception as e:
            return {
                'service': service_name,
                'url': url,
                'healthy': False,
                'status_code': None,
                'response_time_ms': (time.time() - start_time) * 1000,
                'message': f'Error: {str(e)}'
            }

    def check_database_health(self) -> Dict:
        """Check database health through API."""
        url = f"{self.base_url}/api/v1/status/database"
        result = self.check_service_health('PostgreSQL Database', url)

        # If no specific database endpoint, try general status
        if result['status_code'] == 404:
            url = f"{self.base_url}/api/v1/status"
            result = self.check_service_health('PostgreSQL Database', url)
            if result['healthy'] and result.get('status'):
                db_status = result['status'].get('database', {})
                result['healthy'] = db_status.get('status') == 'connected'
                result['message'] = f"Database: {db_status.get('status', 'unknown')}"

        return result

    def check_redis_health(self) -> Dict:
        """Check Redis health through API."""
        url = f"{self.base_url}/api/v1/status/redis"
        result = self.check_service_health('Redis Cache', url)

        # If no specific Redis endpoint, try general status
        if result['status_code'] == 404:
            url = f"{self.base_url}/api/v1/status"
            result = self.check_service_health('Redis Cache', url)
            if result['healthy'] and result.get('status'):
                redis_status = result['status'].get('redis', {})
                result['healthy'] = redis_status.get('status') == 'connected'
                result['message'] = f"Redis: {redis_status.get('status', 'unknown')}"

        return result

    def check_api_endpoints(self) -> List[Dict]:
        """Check critical API endpoints."""
        endpoints = [
            ('API Health', f"{self.base_url}/health"),
            ('API Version', f"{self.base_url}/api/v1/version"),
            ('API Status', f"{self.base_url}/api/v1/status"),
            ('Auth Endpoint', f"{self.base_url}/api/v1/auth/login"),
            ('Users Endpoint', f"{self.base_url}/api/v1/users"),
            ('Content Endpoint', f"{self.base_url}/api/v1/content"),
            ('Agents Endpoint', f"{self.base_url}/api/v1/agents"),
            ('MCP Endpoint', f"{self.base_url}/api/v1/mcp"),
        ]

        results = []
        for name, url in endpoints:
            # Some endpoints might require auth, so 401 is also acceptable
            result = self.check_service_health(name, url)
            if result['status_code'] == 401:
                result['healthy'] = True
                result['message'] = 'Auth required (expected)'
            elif result['status_code'] == 404:
                # 404 might be acceptable for some endpoints
                result['message'] = 'Endpoint not found (may be expected)'
            results.append(result)

        return results

    def check_dashboard_health(self) -> Dict:
        """Check dashboard availability."""
        if 'localhost' in self.base_url:
            dashboard_url = 'http://localhost:5179'
        else:
            dashboard_url = self.base_url

        return self.check_service_health('Dashboard', dashboard_url)

    def check_websocket_health(self) -> Dict:
        """Check WebSocket/Pusher connectivity."""
        ws_url = f"{self.base_url}/ws"
        result = self.check_service_health('WebSocket', ws_url)

        # WebSocket might return 426 Upgrade Required or 101 Switching Protocols
        if result['status_code'] in [426, 101]:
            result['healthy'] = True
            result['message'] = 'WebSocket upgrade available'

        return result

    def run_all_checks(self) -> Tuple[bool, Dict]:
        """Run all health checks in parallel."""
        print(f"\n🏥 Running health checks for {self.environment} environment")
        print(f"   Base URL: {self.base_url}\n")

        all_results = {
            'environment': self.environment,
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'checks': {}
        }

        # Run checks in parallel for better performance
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = {
                'database': executor.submit(self.check_database_health),
                'redis': executor.submit(self.check_redis_health),
                'dashboard': executor.submit(self.check_dashboard_health),
                'websocket': executor.submit(self.check_websocket_health),
            }

            # API endpoints
            api_future = executor.submit(self.check_api_endpoints)

            # Collect results
            for key, future in futures.items():
                try:
                    all_results['checks'][key] = future.result(timeout=15)
                except Exception as e:
                    all_results['checks'][key] = {
                        'healthy': False,
                        'message': f'Check failed: {str(e)}'
                    }

            # API endpoints results
            try:
                all_results['checks']['api_endpoints'] = api_future.result(timeout=15)
            except Exception as e:
                all_results['checks']['api_endpoints'] = [{
                    'healthy': False,
                    'message': f'API checks failed: {str(e)}'
                }]

        # Calculate overall health
        all_healthy = True
        critical_services = ['database', 'redis']

        for service in critical_services:
            if service in all_results['checks']:
                if not all_results['checks'][service].get('healthy', False):
                    all_healthy = False

        all_results['overall_health'] = all_healthy

        return all_healthy, all_results

    def print_results(self, results: Dict):
        """Print formatted health check results."""
        print("\n" + "="*70)
        print("HEALTH CHECK RESULTS")
        print("="*70)

        # Individual service checks
        for key, check in results['checks'].items():
            if key == 'api_endpoints':
                print("\n📡 API Endpoints:")
                for endpoint in check:
                    status = "✅" if endpoint.get('healthy') else "❌"
                    time_str = f"{endpoint.get('response_time_ms', 0):.0f}ms"
                    print(f"  {status} {endpoint.get('service', 'Unknown'):20} [{time_str:>7}] - {endpoint.get('message', '')}")
            else:
                status = "✅" if check.get('healthy') else "❌"
                time_str = f"{check.get('response_time_ms', 0):.0f}ms"
                service_name = check.get('service', key.title())
                print(f"{status} {service_name:25} [{time_str:>7}] - {check.get('message', '')}")

        print("="*70)

        if results['overall_health']:
            print("✅ All critical services are healthy!")
        else:
            print("⚠️  Some services are experiencing issues")

        # Performance summary
        all_response_times = []
        for key, check in results['checks'].items():
            if key == 'api_endpoints':
                for endpoint in check:
                    if endpoint.get('response_time_ms'):
                        all_response_times.append(endpoint['response_time_ms'])
            else:
                if check.get('response_time_ms'):
                    all_response_times.append(check['response_time_ms'])

        if all_response_times:
            avg_time = sum(all_response_times) / len(all_response_times)
            max_time = max(all_response_times)
            print(f"\n📊 Performance: Avg response time: {avg_time:.0f}ms, Max: {max_time:.0f}ms")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Run health checks')
    parser.add_argument(
        '--env',
        required=True,
        choices=['development', 'staging', 'production'],
        help='Environment to check'
    )
    parser.add_argument(
        '--output',
        choices=['console', 'json'],
        default='console',
        help='Output format'
    )

    args = parser.parse_args()

    checker = HealthChecker(args.env)

    try:
        all_healthy, results = checker.run_all_checks()

        if args.output == 'json':
            print(json.dumps(results, indent=2))
        else:
            checker.print_results(results)

        if not all_healthy:
            sys.exit(1)

    except KeyboardInterrupt:
        print("\n⚠️  Health checks interrupted")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error running health checks: {e}")
        sys.exit(1)

    sys.exit(0)


if __name__ == '__main__':
    main()