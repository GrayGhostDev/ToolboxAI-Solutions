#!/usr/bin/env python3
"""
API Test Runner Script

Executes comprehensive API endpoint tests and generates coverage reports.
Provides summary of test results and identifies gaps in testing.
"""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path


class APITestRunner:
    """Manages API test execution and reporting."""

    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.project_root = Path(__file__).parent
        self.test_dir = self.project_root / "tests" / "api"

    def setup_environment(self) -> None:
        """Set up test environment variables."""
        os.environ["TESTING"] = "true"
        os.environ["SKIP_LIFESPAN"] = "true"
        print("✓ Test environment configured")

    def check_dependencies(self) -> bool:
        """Check if required test dependencies are installed."""
        required = ["pytest", "pytest-asyncio", "httpx", "aiosqlite"]
        missing = []

        for package in required:
            try:
                __import__(package.replace("-", "_"))
            except ImportError:
                missing.append(package)

        if missing:
            print(f"❌ Missing dependencies: {', '.join(missing)}")
            print(f"   Run: pip install {' '.join(missing)}")
            return False

        print("✓ All test dependencies installed")
        return True

    def run_tests(self, test_pattern: str = None) -> tuple[bool, dict]:
        """Run API tests and return results."""
        cmd = [
            "pytest",
            str(self.test_dir),
            "-v" if self.verbose else "-q",
            "--tb=short",
            "--json-report",
            "--json-report-file=test_report.json",
            "-W",
            "ignore::DeprecationWarning",
        ]

        if test_pattern:
            cmd.extend(["-k", test_pattern])

        print(f"\n🧪 Running API tests...")
        print(f"   Command: {' '.join(cmd)}\n")

        result = subprocess.run(cmd, capture_output=True, text=True)

        # Parse results
        success = result.returncode == 0
        report = self._parse_test_report()

        return success, report

    def _parse_test_report(self) -> dict:
        """Parse JSON test report if available."""
        report_file = self.project_root / "test_report.json"

        if not report_file.exists():
            return {}

        try:
            with open(report_file) as f:
                data = json.load(f)
                return {
                    "total": data.get("summary", {}).get("total", 0),
                    "passed": data.get("summary", {}).get("passed", 0),
                    "failed": data.get("summary", {}).get("failed", 0),
                    "skipped": data.get("summary", {}).get("skipped", 0),
                    "duration": data.get("duration", 0),
                }
        except Exception as e:
            print(f"Warning: Could not parse test report: {e}")
            return {}

    def run_coverage_analysis(self) -> None:
        """Run tests with coverage analysis."""
        print("\n📊 Running tests with coverage analysis...")

        cmd = [
            "pytest",
            str(self.test_dir),
            "--cov=apps.backend",
            "--cov-report=html",
            "--cov-report=term-missing",
            "-q",
        ]

        subprocess.run(cmd)
        print(f"\n✓ Coverage report generated in htmlcov/index.html")

    def analyze_endpoint_coverage(self) -> dict:
        """Analyze which endpoints have tests."""
        # Get all endpoints from the API
        endpoints_file = self.project_root / "API_REFERENCE.md"
        tested_endpoints = set()
        all_endpoints = set()

        # Parse API reference for endpoints
        if endpoints_file.exists():
            with open(endpoints_file) as f:
                for line in f:
                    if line.startswith("- `"):
                        # Extract endpoint pattern
                        parts = line.split("`")
                        if len(parts) >= 3:
                            endpoint = parts[1].split()[1] if " " in parts[1] else parts[1]
                            all_endpoints.add(endpoint)

        # Parse test files for tested endpoints
        for test_file in self.test_dir.glob("test_*.py"):
            with open(test_file) as f:
                content = f.read()
                # Look for API calls in tests
                import re

                patterns = re.findall(r'(get|post|put|patch|delete)\s*\(\s*["\']([^"\']+)', content)
                for _, endpoint in patterns:
                    tested_endpoints.add(endpoint)

        untested = all_endpoints - tested_endpoints
        coverage_pct = (len(tested_endpoints) / len(all_endpoints) * 100) if all_endpoints else 0

        return {
            "total_endpoints": len(all_endpoints),
            "tested_endpoints": len(tested_endpoints),
            "untested_endpoints": len(untested),
            "coverage_percentage": coverage_pct,
            "untested_list": sorted(list(untested))[:10],  # Show first 10
        }

    def generate_report(self, test_results: dict, coverage_data: dict) -> None:
        """Generate comprehensive test report."""
        print("\n" + "=" * 60)
        print("📋 API TEST REPORT")
        print("=" * 60)

        if test_results:
            print("\n🧪 Test Results:")
            print(f"   Total Tests:  {test_results.get('total', 'N/A')}")
            print(f"   Passed:       {test_results.get('passed', 'N/A')} ✅")
            print(f"   Failed:       {test_results.get('failed', 'N/A')} ❌")
            print(f"   Skipped:      {test_results.get('skipped', 'N/A')} ⏭️")
            if test_results.get("duration"):
                print(f"   Duration:     {test_results['duration']:.2f}s")

        print("\n📊 Endpoint Coverage:")
        print(f"   Total Endpoints:    {coverage_data['total_endpoints']}")
        print(f"   Tested Endpoints:   {coverage_data['tested_endpoints']}")
        print(f"   Untested Endpoints: {coverage_data['untested_endpoints']}")
        print(f"   Coverage:           {coverage_data['coverage_percentage']:.1f}%")

        if coverage_data["untested_list"]:
            print("\n⚠️  Sample Untested Endpoints:")
            for endpoint in coverage_data["untested_list"]:
                print(f"   - {endpoint}")

        print("\n" + "=" * 60)

    def run_specific_test_suites(self) -> None:
        """Run specific test suites individually."""
        suites = {
            "Authentication": "test_auth",
            "User Management": "test_user",
            "Content Generation": "test_content",
            "Classes": "test_class",
            "Real-time": "test_realtime",
        }

        print("\n🔄 Running individual test suites:")
        for name, pattern in suites.items():
            cmd = ["pytest", str(self.test_dir), "-k", pattern, "-q"]
            result = subprocess.run(cmd, capture_output=True, text=True)
            status = "✅" if result.returncode == 0 else "❌"
            print(f"   {status} {name}")

    def check_test_health(self) -> list[str]:
        """Check for common test issues."""
        issues = []

        # Check for async test setup
        if not (self.test_dir / "conftest.py").exists():
            issues.append("Missing conftest.py for test fixtures")

        # Check for test database configuration
        test_files = list(self.test_dir.glob("test_*.py"))
        if len(test_files) < 3:
            issues.append(f"Only {len(test_files)} test files found")

        # Check for proper markers
        has_markers = False
        for test_file in test_files:
            with open(test_file) as f:
                if "@pytest.mark" in f.read():
                    has_markers = True
                    break

        if not has_markers:
            issues.append("No pytest markers found (consider adding for test organization)")

        return issues


def main():
    """Main entry point for test runner."""
    parser = argparse.ArgumentParser(description="Run API endpoint tests")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    parser.add_argument("-c", "--coverage", action="store_true", help="Run with coverage")
    parser.add_argument("-s", "--suites", action="store_true", help="Run individual suites")
    parser.add_argument("-p", "--pattern", help="Test pattern to match")
    parser.add_argument("--check-only", action="store_true", help="Only check setup")

    args = parser.parse_args()

    runner = APITestRunner(verbose=args.verbose)

    print("🚀 API Test Runner")
    print("=" * 60)

    # Setup
    runner.setup_environment()

    if not runner.check_dependencies():
        sys.exit(1)

    # Check test health
    issues = runner.check_test_health()
    if issues:
        print("\n⚠️  Test Health Issues:")
        for issue in issues:
            print(f"   - {issue}")

    if args.check_only:
        print("\n✓ Check complete")
        sys.exit(0)

    # Run tests
    success, test_results = runner.run_tests(args.pattern)

    # Analyze coverage
    coverage_data = runner.analyze_endpoint_coverage()

    # Generate report
    runner.generate_report(test_results, coverage_data)

    # Optional: run individual suites
    if args.suites:
        runner.run_specific_test_suites()

    # Optional: run with coverage
    if args.coverage:
        runner.run_coverage_analysis()

    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
