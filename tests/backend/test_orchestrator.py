"""Master test orchestrator for comprehensive testing"""
import asyncio
import subprocess
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import sys
import os
import re
from collections import defaultdict


class TestOrchestrator:
    """Orchestrate comprehensive test execution"""

    def __init__(self, verbose: bool = False, fast: bool = False, coverage: bool = True):
        self.verbose = verbose
        self.fast = fast  # Skip slow tests if True
        self.coverage = coverage
        self.start_time = time.time()
        self.test_results = {}
        self.metrics = {
            "total": 0,
            "passed": 0,
            "failed": 0,
            "skipped": 0,
            "errors": 0,
            "warnings": 0
        }

        # Set up test environment
        os.environ["TESTING"] = "true"
        os.environ["USE_MOCK_LLM"] = "true"
        os.environ["PUSHER_ENABLED"] = "true"
        os.environ["PYTEST_CURRENT_TEST"] = "test_orchestrator"

        # Ensure we're in the project root
        self.project_root = Path.cwd()
        if not (self.project_root / "tests").exists():
            raise RuntimeError("Must be run from project root directory")

    def print_header(self):
        """Print test execution header"""
        print("\n" + "=" * 80)
        print("🚀 TOOLBOXAI COMPREHENSIVE TEST SUITE")
        print("=" * 80)
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Python: {sys.version.split()[0]}")
        print(f"Platform: {sys.platform}")
        print(f"Project: {self.project_root.name}")
        print(f"Mode: {'Fast' if self.fast else 'Comprehensive'}")
        print(f"Coverage: {'Enabled' if self.coverage else 'Disabled'}")
        print("=" * 80 + "\n")

    async def check_services(self) -> Dict[str, bool]:
        """Check if required services are running"""
        services = {}

        # Check PostgreSQL
        try:
            pg_check = subprocess.run(
                ["pg_isready", "-h", "localhost", "-p", "5434"],
                capture_output=True,
                timeout=5
            )
            services["PostgreSQL"] = pg_check.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            services["PostgreSQL"] = False

        # Check Redis
        try:
            redis_check = subprocess.run(
                ["redis-cli", "-p", "6381", "ping"],
                capture_output=True,
                timeout=5
            )
            services["Redis"] = redis_check.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            services["Redis"] = False

        # Check FastAPI
        try:
            import httpx
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get("http://localhost:8009/health")
                services["FastAPI"] = response.status_code == 200
        except Exception:
            services["FastAPI"] = False

        # Check Node.js/Dashboard
        try:
            import httpx
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get("http://localhost:5179", follow_redirects=True)
                services["Dashboard"] = response.status_code == 200
        except Exception:
            services["Dashboard"] = False

        return services

    def parse_pytest_output(self, output: str) -> Dict[str, Any]:
        """Parse pytest output to extract metrics"""
        metrics = {
            "passed": 0,
            "failed": 0,
            "errors": 0,
            "skipped": 0,
            "warnings": 0,
            "duration": 0.0,
            "coverage": None
        }

        lines = output.split('\n')

        # Look for test results summary
        for line in lines:
            # Pattern: "=== 5 passed, 2 failed, 1 skipped in 10.5s ==="
            if "passed" in line and "in " in line and "s" in line:
                # Extract numbers using regex
                passed_match = re.search(r'(\d+)\s+passed', line)
                failed_match = re.search(r'(\d+)\s+failed', line)
                error_match = re.search(r'(\d+)\s+error', line)
                skipped_match = re.search(r'(\d+)\s+skipped', line)
                duration_match = re.search(r'in\s+([\d.]+)s', line)

                if passed_match:
                    metrics["passed"] = int(passed_match.group(1))
                if failed_match:
                    metrics["failed"] = int(failed_match.group(1))
                if error_match:
                    metrics["errors"] = int(error_match.group(1))
                if skipped_match:
                    metrics["skipped"] = int(skipped_match.group(1))
                if duration_match:
                    metrics["duration"] = float(duration_match.group(1))

            # Look for warnings
            if "warning" in line.lower():
                metrics["warnings"] += 1

            # Look for coverage
            if "TOTAL" in line and "%" in line:
                coverage_match = re.search(r'(\d+)%', line)
                if coverage_match:
                    metrics["coverage"] = int(coverage_match.group(1))

        return metrics

    def run_test_suite(self, suite: str, command: List[str], timeout: int = 300) -> Dict[str, Any]:
        """Run a test suite and capture results"""
        print(f"\n🧪 Running {suite}...")
        print("-" * 60)

        start = time.time()

        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=self.project_root
            )

            duration = time.time() - start

            # Parse output for detailed metrics
            parsed_metrics = self.parse_pytest_output(result.stdout)
            parsed_metrics["duration"] = duration

            # Determine status
            if result.returncode == 0:
                status = "passed"
                status_icon = "✅"
            elif parsed_metrics["failed"] > 0 or parsed_metrics["errors"] > 0:
                status = "failed"
                status_icon = "❌"
            else:
                status = "partial"  # Some skipped but none failed
                status_icon = "⚠️"

            print(f"{status_icon} {status.upper()} ({duration:.2f}s)")

            if parsed_metrics["passed"] > 0:
                print(f"   ✓ {parsed_metrics['passed']} passed")
            if parsed_metrics["failed"] > 0:
                print(f"   ✗ {parsed_metrics['failed']} failed")
            if parsed_metrics["errors"] > 0:
                print(f"   💥 {parsed_metrics['errors']} errors")
            if parsed_metrics["skipped"] > 0:
                print(f"   ⏭️  {parsed_metrics['skipped']} skipped")
            if parsed_metrics["warnings"] > 0:
                print(f"   ⚠️  {parsed_metrics['warnings']} warnings")
            if parsed_metrics["coverage"]:
                print(f"   📊 {parsed_metrics['coverage']}% coverage")

            if self.verbose and result.returncode != 0:
                print("\nErrors:")
                error_lines = result.stderr.split('\n')[:10]  # First 10 lines
                for line in error_lines:
                    if line.strip():
                        print(f"   {line}")

            return {
                "suite": suite,
                "status": status,
                "duration": duration,
                "return_code": result.returncode,
                "command": " ".join(command),
                "metrics": parsed_metrics,
                "stdout": result.stdout[-2000:] if result.stdout else "",  # Last 2000 chars
                "stderr": result.stderr[-1000:] if result.stderr else ""   # Last 1000 chars
            }

        except subprocess.TimeoutExpired:
            duration = time.time() - start
            print(f"⚠️  TIMEOUT after {duration:.1f}s")
            return {
                "suite": suite,
                "status": "timeout",
                "duration": duration,
                "return_code": -1,
                "command": " ".join(command),
                "error": f"Test timed out after {timeout}s"
            }
        except Exception as e:
            duration = time.time() - start
            print(f"❌ ERROR: {e}")
            return {
                "suite": suite,
                "status": "error",
                "duration": duration,
                "return_code": -2,
                "command": " ".join(command),
                "error": str(e)
            }

    def get_test_suites(self) -> List[Tuple[str, List[str], int]]:
        """Get list of test suites to run with timeouts"""
        base_cmd = ["python", "-m", "pytest", "-v", "--tb=short"]
        if self.coverage:
            base_cmd.extend(["--cov=.", "--cov-report=term-missing"])

        # Define test suites with priorities (higher = run first)
        suites = [
            # Critical Infrastructure (Priority 1)
            ("Environment Validation", base_cmd + ["tests/config/", "-k", "not slow"], 60),
            ("Security Scanning", base_cmd + ["tests/security/test_comprehensive_security.py"], 180),

            # Core Functionality (Priority 2)
            ("Unit Tests - Core", base_cmd + ["tests/unit/core/", "-k", "not slow"], 120),
            ("Authentication Tests", base_cmd + ["tests/security/", "-k", "auth"], 90),

            # Integration Tests (Priority 3)
            ("Database Integration", base_cmd + ["tests/integration/database/"], 120),
            ("API Integration", base_cmd + ["tests/integration/", "-k", "api"], 180),

            # Migration & Documentation (Priority 4)
            ("Migration Validation", base_cmd + ["tests/migration/"] if (self.project_root / "tests/migration").exists() else ["echo", "No migration tests"], 60),
            ("Documentation Validation", base_cmd + ["tests/documentation/"] if (self.project_root / "tests/documentation").exists() else ["echo", "No docs tests"], 30),

            # Compliance (Priority 5)
            ("Security Compliance", base_cmd + ["tests/security/", "-k", "compliance"], 90),
            ("Educational Compliance", base_cmd + ["tests/compliance/"] if (self.project_root / "tests/compliance").exists() else ["echo", "No compliance tests"], 60),

            # User Experience (Priority 6)
            ("User Journey Tests", base_cmd + ["tests/flows/"] if (self.project_root / "tests/flows").exists() else ["echo", "No flow tests"], 180),
            ("UI Component Tests", base_cmd + ["tests/", "-k", "ui or component"], 120),

            # Performance & Advanced (Priority 7 - Skip if fast mode)
            ("Performance Tests", base_cmd + ["tests/performance/", "-m", "not slow"] if not self.fast else ["echo", "Skipped performance tests in fast mode"], 300),
            ("End-to-End Tests", base_cmd + ["tests/e2e/", "-m", "not slow"] if not self.fast else ["echo", "Skipped E2E tests in fast mode"], 600),

            # CI/CD Alignment (Priority 8)
            ("CI/CD Pipeline Tests", base_cmd + ["tests/ci_cd/"] if (self.project_root / "tests/ci_cd").exists() else ["echo", "No CI/CD tests"], 60),
        ]

        # Filter out non-existent test paths
        filtered_suites = []
        for name, cmd, timeout in suites:
            # Check if the command references actual test files
            if "echo" in cmd[0]:
                filtered_suites.append((name, cmd, timeout))
            else:
                # Find pytest command and check if test paths exist
                test_paths = [arg for arg in cmd if arg.startswith("tests/")]
                if test_paths:
                    valid_paths = [p for p in test_paths if (self.project_root / p).exists()]
                    if valid_paths:
                        # Replace with valid paths
                        new_cmd = [arg if not arg.startswith("tests/") or arg in valid_paths else "" for arg in cmd]
                        new_cmd = [arg for arg in new_cmd if arg]  # Remove empty strings
                        filtered_suites.append((name, new_cmd, timeout))
                    else:
                        filtered_suites.append((name, ["echo", f"No tests found for {name}"], 10))
                else:
                    filtered_suites.append((name, cmd, timeout))

        return filtered_suites

    async def run_all_tests(self):
        """Run all test suites in order"""
        self.print_header()

        # Check services first
        print("🔍 Checking services...")
        services = await self.check_services()

        for service, available in services.items():
            status = "✅" if available else "❌"
            print(f"  {status} {service}")

        if not all(services.values()):
            print("\n⚠️  Warning: Some services are not available")
            print("   Run: docker-compose -f infrastructure/docker/docker-compose.dev.yml up -d")
            print("   Or: make dev")

        print("\n🧪 Starting test execution...")

        # Get test suites
        test_suites = self.get_test_suites()

        # Run each suite
        for suite_name, command, timeout in test_suites:
            result = self.run_test_suite(suite_name, command, timeout)
            self.test_results[suite_name] = result

            # Update global metrics
            self.metrics["total"] += 1
            if result["status"] == "passed":
                self.metrics["passed"] += 1
            elif result["status"] == "failed":
                self.metrics["failed"] += 1
            elif result["status"] == "error":
                self.metrics["errors"] += 1
            elif result["status"] == "timeout":
                self.metrics["errors"] += 1
            else:
                self.metrics["skipped"] += 1

            # Add detailed metrics if available
            if "metrics" in result:
                metrics = result["metrics"]
                self.metrics["warnings"] += metrics.get("warnings", 0)

    def calculate_health_score(self) -> float:
        """Calculate overall health score (0-100)"""
        total = self.metrics["total"]
        if total == 0:
            return 0.0

        passed = self.metrics["passed"]
        failed = self.metrics["failed"]
        errors = self.metrics["errors"]

        # Base score from pass rate
        pass_rate = (passed / total) * 100

        # Penalties for failures and errors
        failure_penalty = (failed / total) * 20
        error_penalty = (errors / total) * 30

        # Bonus for no warnings
        warning_bonus = 5 if self.metrics["warnings"] == 0 else 0

        score = max(0, pass_rate - failure_penalty - error_penalty + warning_bonus)
        return min(100, score)

    def generate_report(self) -> int:
        """Generate comprehensive test report"""
        elapsed = time.time() - self.start_time

        print("\n" + "=" * 80)
        print("📊 TEST EXECUTION SUMMARY")
        print("=" * 80)

        # Overall metrics
        total = self.metrics["total"]
        passed = self.metrics["passed"]
        pass_rate = (passed / total * 100) if total > 0 else 0
        health_score = self.calculate_health_score()

        print(f"🎯 Health Score: {health_score:.1f}/100")
        print(f"📈 Pass Rate: {pass_rate:.1f}% ({passed}/{total})")
        print(f"⏱️  Duration: {elapsed:.1f}s")
        print(f"📊 Results:")
        print(f"   ✅ Passed: {self.metrics['passed']}")
        print(f"   ❌ Failed: {self.metrics['failed']}")
        print(f"   💥 Errors: {self.metrics['errors']}")
        print(f"   ⏭️  Skipped: {self.metrics['skipped']}")
        if self.metrics['warnings'] > 0:
            print(f"   ⚠️  Warnings: {self.metrics['warnings']}")

        # Suite details
        print(f"\n📋 SUITE RESULTS:")
        print("-" * 60)

        suite_categories = defaultdict(list)
        for suite_name, result in self.test_results.items():
            # Categorize suites
            if "Security" in suite_name:
                category = "Security"
            elif "Integration" in suite_name or "API" in suite_name:
                category = "Integration"
            elif "Unit" in suite_name:
                category = "Unit Tests"
            elif "Performance" in suite_name or "E2E" in suite_name:
                category = "Performance"
            else:
                category = "Other"

            suite_categories[category].append((suite_name, result))

        for category, suites in suite_categories.items():
            print(f"\n{category}:")
            for suite_name, result in suites:
                status_icon = {
                    "passed": "✅",
                    "failed": "❌",
                    "error": "💥",
                    "timeout": "⏰",
                    "partial": "⚠️"
                }.get(result["status"], "❓")

                duration = result.get("duration", 0)
                print(f"  {status_icon} {suite_name:<40} {duration:.2f}s")

                # Show metrics if available
                if "metrics" in result:
                    metrics = result["metrics"]
                    if metrics["passed"] > 0 or metrics["failed"] > 0:
                        print(f"     📊 {metrics['passed']}✓ {metrics['failed']}✗ {metrics['skipped']}⏭️")

        # Critical issues
        failed_suites = [s for s, r in self.test_results.items() if r["status"] in ["failed", "error", "timeout"]]
        if failed_suites:
            print(f"\n⚠️  FAILED SUITES:")
            for suite in failed_suites:
                result = self.test_results[suite]
                print(f"   ❌ {suite} ({result['status']})")

        # Recommendations
        print(f"\n💡 RECOMMENDATIONS:")
        if health_score < 70:
            print("   🔴 Critical: System health is below acceptable threshold")
            print("   🔧 Focus on fixing failed tests before proceeding")
        elif health_score < 85:
            print("   🟡 Warning: Some issues detected")
            print("   🔧 Address failed tests when possible")
        else:
            print("   🟢 Good: System health is acceptable")
            print("   ✨ Consider improving test coverage")

        # Save detailed JSON report
        report_data = {
            "timestamp": datetime.now().isoformat(),
            "duration": elapsed,
            "health_score": health_score,
            "metrics": self.metrics,
            "pass_rate": pass_rate,
            "test_results": self.test_results,
            "failed_suites": failed_suites,
            "environment": {
                "python_version": sys.version.split()[0],
                "platform": sys.platform,
                "project_root": str(self.project_root),
                "fast_mode": self.fast,
                "coverage_enabled": self.coverage
            }
        }

        report_path = self.project_root / "test_execution_report.json"
        with open(report_path, 'w') as f:
            json.dump(report_data, f, indent=2, default=str)

        print(f"\n📄 Detailed report saved to: {report_path}")

        # Determine exit code based on health score
        if health_score >= 75:
            print("\n✅ TEST SUITE PASSED")
            return 0
        else:
            print(f"\n❌ TEST SUITE FAILED (Health Score: {health_score:.1f}% < 75%)")
            return 1


async def main():
    """Main execution entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="ToolboxAI Test Orchestrator")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--fast", "-f", action="store_true", help="Fast mode (skip slow tests)")
    parser.add_argument("--no-coverage", action="store_true", help="Disable coverage reporting")
    parser.add_argument("--suite", "-s", help="Run specific suite only")
    args = parser.parse_args()

    orchestrator = TestOrchestrator(
        verbose=args.verbose,
        fast=args.fast,
        coverage=not args.no_coverage
    )

    try:
        await orchestrator.run_all_tests()
        exit_code = orchestrator.generate_report()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n⚠️  Test execution interrupted by user")
        orchestrator.generate_report()
        sys.exit(130)  # Standard exit code for Ctrl+C
    except Exception as e:
        print(f"\n\n💥 Fatal error: {e}")
        if orchestrator.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    # Import re for parsing (needed for the parsing functions)
    import re
    asyncio.run(main())