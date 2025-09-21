
import pytest
from unittest.mock import Mock, patch

@pytest.fixture
def mock_db_connection():
    """Mock database connection for tests"""
    with patch('psycopg2.connect') as mock_connect:
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn
        yield mock_conn

#!/usr/bin/env python3
"""
Integration Test Runner

Orchestrates and runs comprehensive integration tests with proper setup,
teardown, and reporting. Provides different test suites for various scenarios.
"""

import asyncio
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pytest

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Test configuration
INTEGRATION_TEST_CONFIG = {
    "database": {
        "host": "localhost",
        "port": 5434,
        "name": "educational_platform_dev",
        "user": "eduplatform",
        "password": "eduplatform2024"
    },
    "redis": {
        "host": "localhost",
        "port": 6381,
        "db": 0
    },
    "api": {
        "base_url": "http://127.0.0.1:8009",
        "timeout": 30
    },
    "agent_coordinator": {
        "base_url": "http://127.0.0.1:8888",
        "timeout": 30
    },
    "websocket": {
        "base_url": "ws://127.0.0.1:8009",
        "timeout": 30
    }
}

# Test suites
TEST_SUITES = {
    "basic": {
        "description": "Basic integration tests - quick smoke tests",
        "files": [
            "test_comprehensive_auth_flow.py::TestLoginFlow::test_successful_login_flow",
            "test_content_generation_pipeline.py::TestBasicContentGeneration::test_simple_content_generation",
            "test_database_redis_api_integration.py::TestDatabaseTransactionIntegrity::test_successful_transaction_commit"
        ],
        "timeout": 300,  # 5 minutes
        "parallel": True
    },
    "auth": {
        "description": "Authentication and authorization tests",
        "files": [
            "test_comprehensive_auth_flow.py"
        ],
        "timeout": 600,  # 10 minutes
        "parallel": True
    },
    "content": {
        "description": "Content generation pipeline tests",
        "files": [
            "test_content_generation_pipeline.py"
        ],
        "timeout": 1800,  # 30 minutes
        "parallel": False
    },
    "database": {
        "description": "Database and Redis integration tests",
        "files": [
            "test_database_redis_api_integration.py"
        ],
        "timeout": 900,  # 15 minutes
        "parallel": True,
        "requires": ["postgres", "redis"]
    },
    "realtime": {
        "description": "Real-time communication tests",
        "files": [
            "test_realtime_communication.py"
        ],
        "timeout": 600,  # 10 minutes
        "parallel": True,
        "requires": ["websocket", "pusher"]
    },
    "agents": {
        "description": "Multi-agent coordination tests",
        "files": [
            "test_multi_agent_coordination.py"
        ],
        "timeout": 1200,  # 20 minutes
        "parallel": False
    },
    "e2e": {
        "description": "End-to-end workflow tests",
        "files": [
            "test_e2e_content_workflow.py"
        ],
        "timeout": 3600,  # 60 minutes
        "parallel": False,
        "requires": ["postgres", "redis", "websocket"]
    },
    "full": {
        "description": "Complete integration test suite",
        "files": [
            "test_comprehensive_auth_flow.py",
            "test_content_generation_pipeline.py",
            "test_database_redis_api_integration.py",
            "test_realtime_communication.py",
            "test_multi_agent_coordination.py",
            "test_e2e_content_workflow.py"
        ],
        "timeout": 7200,  # 2 hours
        "parallel": False
    }
}


class IntegrationTestRunner:
    """Integration test runner with service management and reporting"""

    def __init__(self, config: Dict = None):
        self.config = config or INTEGRATION_TEST_CONFIG
        self.test_dir = Path(__file__).parent
        self.results = {}
        self.start_time = None
        self.end_time = None

    async def check_services(self) -> Dict[str, bool]:
        """Check availability of required services"""
        import httpx
        import redis
        import psycopg2

        services = {}

        # Check API server
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.config['api']['base_url']}/health", timeout=5)
                services["api"] = response.status_code == 200
        except Exception:
            services["api"] = False

        # Check Agent Coordinator
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.config['agent_coordinator']['base_url']}/health", timeout=5)
                services["agent_coordinator"] = response.status_code == 200
        except Exception:
            services["agent_coordinator"] = False

        # Check PostgreSQL
        try:
            conn = psycopg2.connect(
                host=self.config["database"]["host"],
                port=self.config["database"]["port"],
                database=self.config["database"]["name"],
                user=self.config["database"]["user"],
                password=self.config["database"]["password"]
            )
            conn.close()
            services["postgres"] = True
        except Exception:
            services["postgres"] = False

        # Check Redis
        try:
            r = redis.Redis(
                host=self.config["redis"]["host"],
                port=self.config["redis"]["port"],
                db=self.config["redis"]["db"]
            )
            r.ping()
            services["redis"] = True
        except Exception:
            services["redis"] = False

        # Check WebSocket
        try:
            import websockets
            uri = f"{self.config['websocket']['base_url']}/ws"
            async with websockets.connect(uri, timeout=5) as ws:
                await ws.close()
            services["websocket"] = True
        except Exception:
            services["websocket"] = False

        return services

    def setup_environment(self):
        """Setup test environment variables"""
        os.environ.update({
            "TESTING": "true",
            "USE_MOCK_LLM": "true",
            "USE_MOCK_DATABASE": "false",
            "USE_MOCK_REDIS": "false",
            "INTEGRATION_TESTING": "true",
            "LOG_LEVEL": "WARNING",
            "BYPASS_RATE_LIMIT_IN_TESTS": "true"
        })

    def generate_pytest_args(self, suite_config: Dict, test_files: List[str]) -> List[str]:
        """Generate pytest arguments for test execution"""
        args = [
            "-v",
            "--tb=short",
            "--strict-markers",
            f"--timeout={suite_config['timeout']}",
            "--timeout-method=thread"
        ]

        # Add markers
        args.extend([
            "-m", "integration"
        ])

        # Add parallel execution if enabled
        if suite_config.get("parallel", False):
            args.extend(["-n", "auto", "--dist", "loadfile"])

        # Add JUnit XML output
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        junit_file = self.test_dir / f"../logs/integration/junit_{timestamp}.xml"
        junit_file.parent.mkdir(parents=True, exist_ok=True)
        args.extend(["--junitxml", str(junit_file)])

        # Add coverage if requested
        if os.getenv("INTEGRATION_COVERAGE", "false").lower() == "true":
            args.extend([
                "--cov=apps/backend",
                "--cov=core",
                "--cov-report=html:tests/logs/integration/coverage",
                "--cov-report=term-missing"
            ])

        # Add test files
        for test_file in test_files:
            if "::" in test_file:
                args.append(str(self.test_dir / test_file))
            else:
                args.append(str(self.test_dir / test_file))

        return args

    async def run_test_suite(self, suite_name: str) -> Dict:
        """Run a specific test suite"""
        if suite_name not in TEST_SUITES:
            raise ValueError(f"Unknown test suite: {suite_name}")

        suite_config = TEST_SUITES[suite_name]
        print(f"\n{'='*60}")
        print(f"Running Integration Test Suite: {suite_name}")
        print(f"Description: {suite_config['description']}")
        print(f"{'='*60}")

        # Check required services
        if suite_config.get("requires"):
            print("Checking required services...")
            services = await self.check_services()

            missing_services = []
            for service in suite_config["requires"]:
                if not services.get(service, False):
                    missing_services.append(service)

            if missing_services:
                error_msg = f"Missing required services: {', '.join(missing_services)}"
                print(f"❌ {error_msg}")
                return {
                    "suite": suite_name,
                    "status": "skipped",
                    "error": error_msg,
                    "tests_run": 0,
                    "passed": 0,
                    "failed": 0,
                    "duration": 0
                }

            print("✅ All required services available")

        # Setup environment
        self.setup_environment()

        # Generate pytest arguments
        pytest_args = self.generate_pytest_args(suite_config, suite_config["files"])

        print(f"Executing: pytest {' '.join(pytest_args)}")
        print(f"Timeout: {suite_config['timeout']} seconds")

        # Run tests
        start_time = time.time()

        try:
            # Change to test directory
            original_cwd = os.getcwd()
            os.chdir(self.test_dir)

            result = pytest.main(pytest_args)
            duration = time.time() - start_time

            # Parse results (simplified)
            status = "passed" if result == 0 else "failed"

            return {
                "suite": suite_name,
                "status": status,
                "exit_code": result,
                "duration": duration,
                "pytest_args": pytest_args
            }

        except Exception as e:
            duration = time.time() - start_time
            return {
                "suite": suite_name,
                "status": "error",
                "error": str(e),
                "duration": duration
            }
        finally:
            os.chdir(original_cwd)

    async def run_multiple_suites(self, suite_names: List[str]) -> Dict:
        """Run multiple test suites"""
        self.start_time = datetime.now()
        results = {}

        print(f"\n🚀 Starting Integration Test Run")
        print(f"Timestamp: {self.start_time}")
        print(f"Suites: {', '.join(suite_names)}")

        # Check overall service availability
        print("\n📊 Service Availability Check:")
        services = await self.check_services()
        for service, available in services.items():
            status = "✅" if available else "❌"
            print(f"  {status} {service}")

        # Run each suite
        for suite_name in suite_names:
            print(f"\n📋 Starting suite: {suite_name}")
            suite_result = await self.run_test_suite(suite_name)
            results[suite_name] = suite_result

            # Print immediate results
            status_emoji = {
                "passed": "✅",
                "failed": "❌",
                "error": "💥",
                "skipped": "⏭️"
            }

            emoji = status_emoji.get(suite_result["status"], "❓")
            duration = suite_result["duration"]
            print(f"{emoji} Suite '{suite_name}' {suite_result['status']} in {duration:.2f}s")

        self.end_time = datetime.now()
        self.results = results

        return self.generate_summary()

    def generate_summary(self) -> Dict:
        """Generate test run summary"""
        total_duration = (self.end_time - self.start_time).total_seconds()

        summary = {
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat(),
            "total_duration": total_duration,
            "suites": self.results,
            "summary": {
                "total_suites": len(self.results),
                "passed": sum(1 for r in self.results.values() if r["status"] == "passed"),
                "failed": sum(1 for r in self.results.values() if r["status"] == "failed"),
                "errors": sum(1 for r in self.results.values() if r["status"] == "error"),
                "skipped": sum(1 for r in self.results.values() if r["status"] == "skipped")
            }
        }

        return summary

    def print_summary(self, summary: Dict):
        """Print formatted test summary"""
        print(f"\n{'='*80}")
        print("🎯 INTEGRATION TEST SUMMARY")
        print(f"{'='*80}")

        print(f"📅 Start Time: {summary['start_time']}")
        print(f"⏱️  Total Duration: {summary['total_duration']:.2f} seconds")
        print(f"📊 Suite Results:")

        for suite_name, result in summary["suites"].items():
            status_emoji = {
                "passed": "✅",
                "failed": "❌",
                "error": "💥",
                "skipped": "⏭️"
            }
            emoji = status_emoji.get(result["status"], "❓")
            duration = result["duration"]
            print(f"   {emoji} {suite_name:<20} {result['status']:<10} ({duration:.2f}s)")

        print(f"\n📈 Overall Statistics:")
        stats = summary["summary"]
        print(f"   Total Suites: {stats['total_suites']}")
        print(f"   ✅ Passed: {stats['passed']}")
        print(f"   ❌ Failed: {stats['failed']}")
        print(f"   💥 Errors: {stats['errors']}")
        print(f"   ⏭️  Skipped: {stats['skipped']}")

        success_rate = (stats['passed'] / stats['total_suites']) * 100 if stats['total_suites'] > 0 else 0
        print(f"   🎯 Success Rate: {success_rate:.1f}%")

        print(f"\n{'='*80}")

    def save_results(self, summary: Dict, output_file: Optional[str] = None):
        """Save results to JSON file"""
        if not output_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"integration_test_results_{timestamp}.json"

        output_path = Path("tests/logs/integration") / output_file
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w') as f:
            json.dump(summary, f, indent=2, default=str)

        print(f"📄 Results saved to: {output_path}")


async def main():
    """Main entry point for integration test runner"""
    import argparse

    parser = argparse.ArgumentParser(description="Integration Test Runner")
    parser.add_argument(
        "suites",
        nargs="*",
        default=["basic"],
        help=f"Test suites to run. Available: {', '.join(TEST_SUITES.keys())}"
    )
    parser.add_argument("--list", action="store_true", help="List available test suites")
    parser.add_argument("--check-services", action="store_true", help="Check service availability only")
    parser.add_argument("--output", help="Output file for results")
    parser.add_argument("--coverage", action="store_true", help="Enable coverage reporting")

    args = parser.parse_args()

    if args.list:
        print("Available Integration Test Suites:")
        print("="*50)
        for name, config in TEST_SUITES.items():
            print(f"{name:<12} - {config['description']}")
            print(f"             Files: {len(config['files'])}")
            print(f"             Timeout: {config['timeout']}s")
            if config.get("requires"):
                print(f"             Requires: {', '.join(config['requires'])}")
            print()
        return

    runner = IntegrationTestRunner()

    if args.check_services:
        print("Checking service availability...")
        services = await runner.check_services()
        for service, available in services.items():
            status = "✅ Available" if available else "❌ Not Available"
            print(f"{service:<20} {status}")
        return

    # Validate suite names
    invalid_suites = [s for s in args.suites if s not in TEST_SUITES]
    if invalid_suites:
        print(f"Error: Unknown test suites: {', '.join(invalid_suites)}")
        print(f"Available suites: {', '.join(TEST_SUITES.keys())}")
        return 1

    # Set coverage flag
    if args.coverage:
        os.environ["INTEGRATION_COVERAGE"] = "true"

    # Run tests
    try:
        summary = await runner.run_multiple_suites(args.suites)
        runner.print_summary(summary)
        runner.save_results(summary, args.output)

        # Exit with appropriate code
        failed_count = summary["summary"]["failed"] + summary["summary"]["errors"]
        return 1 if failed_count > 0 else 0

    except KeyboardInterrupt:
        print("\n⚠️ Test run interrupted by user")
        return 130
    except Exception as e:
        print(f"\n💥 Test run failed with error: {e}")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)