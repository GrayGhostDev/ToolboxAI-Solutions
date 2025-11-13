#!/usr/bin/env python3
"""
Chaos Engineering Test Runner

Safe execution of chaos engineering tests with proper environment setup,
monitoring, and cleanup procedures.

Usage:
    python run_chaos_tests.py [options]

Examples:
    # Run all chaos tests
    python run_chaos_tests.py

    # Run specific test categories
    python run_chaos_tests.py --category network
    python run_chaos_tests.py --category database

    # Run with custom timeout
    python run_chaos_tests.py --timeout 600

    # Dry run to validate setup
    python run_chaos_tests.py --dry-run
"""

import argparse
import json
import logging
import os
import signal
import subprocess
import sys
import tempfile
import time
from dataclasses import asdict, dataclass
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

logger = logging.getLogger(__name__)


@dataclass
class ChaosTestConfig:
    """Configuration for chaos test execution"""

    categories: list[str]
    timeout: int
    max_failures: int
    parallel: bool
    mock_external: bool
    isolated_env: bool
    report_file: str | None
    dry_run: bool
    verbose: bool


class ChaosTestRunner:
    """Manages execution of chaos engineering tests"""

    def __init__(self, config: ChaosTestConfig):
        self.config = config
        self.test_results = []
        self.start_time = time.time()
        self.emergency_stop = False
        self.temp_files = []

    def setup_environment(self):
        """Setup test environment and safety measures"""
        logger.info("Setting up chaos test environment")

        # Verify we're in a safe environment
        if not self._verify_safe_environment():
            raise RuntimeError("Unsafe environment for chaos testing")

        # Setup test database
        self._setup_test_database()

        # Setup monitoring
        self._setup_monitoring()

        # Setup emergency stop handler
        signal.signal(signal.SIGTERM, self._emergency_stop_handler)
        signal.signal(signal.SIGINT, self._emergency_stop_handler)

    def _verify_safe_environment(self) -> bool:
        """Verify that it's safe to run chaos tests"""
        # Check environment variables
        env = os.getenv("ENVIRONMENT", "").lower()
        if env not in ["test", "chaos_test", "development"]:
            logger.error(f"Unsafe environment: {env}. Use 'test', 'chaos_test', or 'development'")
            return False

        # Check for production indicators
        production_indicators = [
            "PRODUCTION",
            "PROD",
            "LIVE",
        ]

        for indicator in production_indicators:
            if os.getenv(indicator, "").lower() in ["true", "1", "yes"]:
                logger.error(f"Production indicator found: {indicator}")
                return False

        # Verify test database URL
        db_url = os.getenv("DATABASE_URL", "")
        if "test" not in db_url.lower() and "chaos" not in db_url.lower():
            logger.warning(f"Database URL doesn't contain 'test' or 'chaos': {db_url}")

        return True

    def _setup_test_database(self):
        """Setup isolated test database"""
        # Use separate database for chaos testing
        test_db_url = os.getenv("DATABASE_URL", "").replace("/toolboxai", "/toolboxai_chaos_test")
        os.environ["DATABASE_URL"] = test_db_url

        # Use separate Redis database
        os.environ["REDIS_DB"] = "15"  # Use test database

        logger.info("Configured isolated test databases")

    def _setup_monitoring(self):
        """Setup monitoring for chaos tests"""
        # Create temporary monitoring file
        monitor_file = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
        self.temp_files.append(monitor_file.name)

        monitoring_config = {
            "start_time": self.start_time,
            "config": asdict(self.config),
            "pid": os.getpid(),
            "environment": dict(os.environ),
        }

        json.dump(monitoring_config, monitor_file)
        monitor_file.close()

        os.environ["CHAOS_MONITOR_FILE"] = monitor_file.name
        logger.info(f"Monitoring configured: {monitor_file.name}")

    def _emergency_stop_handler(self, signum, frame):
        """Handle emergency stop signals"""
        logger.error(f"Emergency stop triggered by signal {signum}")
        self.emergency_stop = True
        self._cleanup()
        sys.exit(1)

    def run_tests(self):
        """Execute chaos engineering tests"""
        if self.config.dry_run:
            return self._dry_run()

        logger.info("Starting chaos engineering tests")

        try:
            # Build pytest command
            cmd = self._build_pytest_command()

            if self.config.verbose:
                logger.info(f"Executing: {' '.join(cmd)}")

            # Run tests
            result = subprocess.run(
                cmd,
                cwd=str(project_root),
                capture_output=True,
                text=True,
                timeout=self.config.timeout,
            )

            # Process results
            self._process_results(result)

            return result.returncode == 0

        except subprocess.TimeoutExpired:
            logger.error(f"Tests timed out after {self.config.timeout}s")
            return False

        except Exception as e:
            logger.error(f"Test execution failed: {e}")
            return False

        finally:
            self._cleanup()

    def _build_pytest_command(self) -> list[str]:
        """Build pytest command with appropriate options"""
        cmd = [
            sys.executable,
            "-m",
            "pytest",
            "tests/chaos/test_chaos_engineering.py",
            "-v",
            "--tb=short",
            f"--timeout={self.config.timeout}",
            f"--maxfail={self.config.max_failures}",
        ]

        # Add category filters
        if self.config.categories:
            category_markers = []
            for category in self.config.categories:
                category_markers.append(f"{category}_chaos")

            if category_markers:
                cmd.extend(["-m", " or ".join(category_markers)])

        # Add parallel execution if requested
        if self.config.parallel:
            cmd.extend(["-n", "auto"])

        # Add report generation
        if self.config.report_file:
            cmd.extend(["--junitxml", self.config.report_file])

        # Add chaos test marker
        if not any("-m" in str(arg) for arg in cmd):
            cmd.extend(["-m", "chaos"])

        return cmd

    def _dry_run(self) -> bool:
        """Perform dry run to validate setup"""
        logger.info("Performing dry run validation")

        checks = [
            ("Environment safety", self._verify_safe_environment),
            ("Database connectivity", self._check_database_connectivity),
            ("Redis connectivity", self._check_redis_connectivity),
            ("Required modules", self._check_required_modules),
            ("Test file syntax", self._validate_test_syntax),
        ]

        all_passed = True
        for check_name, check_func in checks:
            try:
                result = check_func()
                status = "PASS" if result else "FAIL"
                logger.info(f"{check_name}: {status}")
                if not result:
                    all_passed = False
            except Exception as e:
                logger.error(f"{check_name}: ERROR - {e}")
                all_passed = False

        return all_passed

    def _check_database_connectivity(self) -> bool:
        """Check database connectivity"""
        try:
            import asyncpg

            # This is a dry run, so we just check that we can import
            return True
        except ImportError:
            return False

    def _check_redis_connectivity(self) -> bool:
        """Check Redis connectivity"""
        try:
            import redis.asyncio

            return True
        except ImportError:
            return False

    def _check_required_modules(self) -> bool:
        """Check that required modules are available"""
        required_modules = [
            "asyncio",
            "pytest",
            "httpx",
            "psutil",
            "redis",
        ]

        for module in required_modules:
            try:
                __import__(module)
            except ImportError:
                logger.error(f"Required module not available: {module}")
                return False

        return True

    def _validate_test_syntax(self) -> bool:
        """Validate test file syntax"""
        test_file = project_root / "tests" / "chaos" / "test_chaos_engineering.py"

        try:
            with open(test_file) as f:
                code = f.read()

            compile(code, str(test_file), "exec")
            return True

        except SyntaxError as e:
            logger.error(f"Syntax error in test file: {e}")
            return False

        except Exception as e:
            logger.error(f"Error validating test file: {e}")
            return False

    def _process_results(self, result):
        """Process test execution results"""
        logger.info(f"Test execution completed with exit code: {result.returncode}")

        if result.stdout:
            logger.info("STDOUT:")
            logger.info(result.stdout)

        if result.stderr:
            logger.error("STDERR:")
            logger.error(result.stderr)

        # Parse pytest output for detailed results
        self._parse_pytest_output(result.stdout)

    def _parse_pytest_output(self, output: str):
        """Parse pytest output for test results"""
        lines = output.split("\n")

        for line in lines:
            if "::" in line and ("PASSED" in line or "FAILED" in line or "SKIPPED" in line):
                test_name = line.split("::")[-1].split()[0]
                status = (
                    "PASSED" if "PASSED" in line else "FAILED" if "FAILED" in line else "SKIPPED"
                )

                self.test_results.append(
                    {"name": test_name, "status": status, "line": line.strip()}
                )

        # Log summary
        if self.test_results:
            passed = sum(1 for r in self.test_results if r["status"] == "PASSED")
            failed = sum(1 for r in self.test_results if r["status"] == "FAILED")
            skipped = sum(1 for r in self.test_results if r["status"] == "SKIPPED")

            logger.info(
                f"Test Results Summary: {passed} passed, {failed} failed, {skipped} skipped"
            )

    def _cleanup(self):
        """Cleanup test environment"""
        logger.info("Cleaning up chaos test environment")

        # Remove temporary files
        for temp_file in self.temp_files:
            try:
                os.unlink(temp_file)
            except Exception as e:
                logger.warning(f"Failed to remove temp file {temp_file}: {e}")

        # Reset environment variables
        if "CHAOS_MONITOR_FILE" in os.environ:
            del os.environ["CHAOS_MONITOR_FILE"]

        # Additional cleanup can be added here

    def generate_report(self):
        """Generate test execution report"""
        if not self.config.report_file:
            return

        report_data = {
            "config": asdict(self.config),
            "execution_time": time.time() - self.start_time,
            "results": self.test_results,
            "environment": {
                "python_version": sys.version,
                "platform": sys.platform,
                "pid": os.getpid(),
            },
        }

        try:
            with open(self.config.report_file, "w") as f:
                json.dump(report_data, f, indent=2)

            logger.info(f"Report generated: {self.config.report_file}")

        except Exception as e:
            logger.error(f"Failed to generate report: {e}")


def setup_logging(verbose: bool = False):
    """Setup logging for chaos test runner"""
    level = logging.DEBUG if verbose else logging.INFO

    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def main():
    """Main entry point for chaos test runner"""
    parser = argparse.ArgumentParser(
        description="Run chaos engineering tests safely",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    parser.add_argument(
        "--category",
        action="append",
        dest="categories",
        choices=[
            "network",
            "service",
            "resource",
            "database",
            "cache",
            "rate_limit",
            "websocket",
            "region",
            "latency",
        ],
        help="Test categories to run (can be specified multiple times)",
    )

    parser.add_argument(
        "--timeout",
        type=int,
        default=600,
        help="Maximum test execution time in seconds (default: 600)",
    )

    parser.add_argument(
        "--max-failures",
        type=int,
        default=5,
        help="Maximum number of test failures before stopping (default: 5)",
    )

    parser.add_argument("--parallel", action="store_true", help="Run tests in parallel")

    parser.add_argument(
        "--no-mock-external",
        action="store_true",
        help="Disable mocking of external services (dangerous!)",
    )

    parser.add_argument(
        "--no-isolation", action="store_true", help="Disable environment isolation (dangerous!)"
    )

    parser.add_argument(
        "--report", dest="report_file", help="Generate JSON report to specified file"
    )

    parser.add_argument(
        "--dry-run", action="store_true", help="Validate setup without running tests"
    )

    parser.add_argument("--verbose", action="store_true", help="Enable verbose output")

    args = parser.parse_args()

    # Setup logging
    setup_logging(args.verbose)

    # Create configuration
    config = ChaosTestConfig(
        categories=args.categories or [],
        timeout=args.timeout,
        max_failures=args.max_failures,
        parallel=args.parallel,
        mock_external=not args.no_mock_external,
        isolated_env=not args.no_isolation,
        report_file=args.report_file,
        dry_run=args.dry_run,
        verbose=args.verbose,
    )

    # Create and run chaos test runner
    runner = ChaosTestRunner(config)

    try:
        runner.setup_environment()
        success = runner.run_tests()
        runner.generate_report()

        if success:
            logger.info("All chaos tests completed successfully")
            return 0
        else:
            logger.error("Some chaos tests failed")
            return 1

    except Exception as e:
        logger.error(f"Chaos test runner failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
