#!/usr/bin/env python3
"""
Comprehensive integration test runner.

This script runs all comprehensive integration tests to achieve >90% coverage
for Docker services, Supabase integration, Mantine UI, end-to-end flows,
and performance benchmarks.
"""

import asyncio
import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any


class ComprehensiveTestRunner:
    """Runner for comprehensive integration tests."""

    def __init__(self, verbose: bool = False, coverage: bool = True):
        """Initialize test runner."""
        self.verbose = verbose
        self.coverage = coverage
        self.test_results = {}
        self.start_time = None
        self.end_time = None

        # Test categories and their test files
        self.test_categories = {
            "docker_integration": [
                "tests/integration/test_docker_services_integration.py"
            ],
            "supabase_integration": [
                "tests/integration/test_supabase_integration.py"
            ],
            "mantine_ui": [
                "tests/integration/test_mantine_ui_integration.py"
            ],
            "end_to_end": [
                "tests/e2e/test_comprehensive_end_to_end.py"
            ],
            "performance": [
                "tests/performance/test_comprehensive_performance.py"
            ],
            "existing_integration": [
                "tests/integration/test_agent_integration.py",
                "tests/integration/test_auth_system.py",
                "tests/integration/test_complete_integration.py",
                "tests/integration/test_websocket_integration.py"
            ]
        }

        # Coverage targets
        self.coverage_targets = {
            "docker_integration": 90,
            "supabase_integration": 85,
            "mantine_ui": 80,
            "end_to_end": 75,
            "performance": 70,
            "existing_integration": 85
        }

    def log(self, message: str, level: str = "INFO"):
        """Log message with timestamp."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")

    def run_pytest_command(self, test_files: List[str], markers: List[str] = None) -> Dict[str, Any]:
        """Run pytest command and return results."""
        cmd = ["python", "-m", "pytest"]

        # Add test files
        cmd.extend(test_files)

        # Add markers if specified
        if markers:
            for marker in markers:
                cmd.extend(["-m", marker])

        # Add coverage if enabled
        if self.coverage:
            cmd.extend([
                "--cov=apps/backend",
                "--cov=core",
                "--cov=database",
                "--cov-report=term-missing",
                "--cov-report=json:coverage-report.json"
            ])

        # Add verbose output if requested
        if self.verbose:
            cmd.extend(["-v", "-s"])

        # Add other useful options
        cmd.extend([
            "--tb=short",
            "--durations=10",
            "--maxfail=5",
            "--timeout=300"
        ])

        # Set environment variables
        env = os.environ.copy()
        env.update({
            "TESTING_MODE": "true",
            "BYPASS_RATE_LIMIT_IN_TESTS": "true",
            "USE_MOCK_LLM": "true",
            "PYTHONPATH": str(Path.cwd())
        })

        self.log(f"Running command: {' '.join(cmd)}")

        try:
            start_time = time.time()
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                env=env,
                timeout=1800  # 30 minutes timeout
            )
            end_time = time.time()

            # Parse output for test results
            output_lines = result.stdout.split('\n')
            error_lines = result.stderr.split('\n')

            # Extract test summary
            test_summary = self._parse_test_summary(output_lines)

            return {
                "success": result.returncode == 0,
                "return_code": result.returncode,
                "duration": end_time - start_time,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "test_summary": test_summary,
                "coverage_data": self._parse_coverage_data() if self.coverage else None
            }

        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "return_code": -1,
                "duration": 1800,
                "stdout": "",
                "stderr": "Test execution timed out after 30 minutes",
                "test_summary": {"passed": 0, "failed": 0, "skipped": 0, "error": "timeout"},
                "coverage_data": None
            }

        except Exception as e:
            return {
                "success": False,
                "return_code": -1,
                "duration": 0,
                "stdout": "",
                "stderr": str(e),
                "test_summary": {"passed": 0, "failed": 0, "skipped": 0, "error": str(e)},
                "coverage_data": None
            }

    def _parse_test_summary(self, output_lines: List[str]) -> Dict[str, Any]:
        """Parse pytest output for test summary."""
        summary = {"passed": 0, "failed": 0, "skipped": 0, "errors": 0}

        for line in output_lines:
            line = line.strip()

            # Look for pytest summary line
            if "passed" in line or "failed" in line or "skipped" in line:
                # Parse different summary formats
                if " passed" in line:
                    try:
                        passed = int(line.split(" passed")[0].split()[-1])
                        summary["passed"] = passed
                    except (ValueError, IndexError):
                        pass

                if " failed" in line:
                    try:
                        failed = int(line.split(" failed")[0].split()[-1])
                        summary["failed"] = failed
                    except (ValueError, IndexError):
                        pass

                if " skipped" in line:
                    try:
                        skipped = int(line.split(" skipped")[0].split()[-1])
                        summary["skipped"] = skipped
                    except (ValueError, IndexError):
                        pass

                if " error" in line:
                    try:
                        errors = int(line.split(" error")[0].split()[-1])
                        summary["errors"] = errors
                    except (ValueError, IndexError):
                        pass

        return summary

    def _parse_coverage_data(self) -> Optional[Dict[str, Any]]:
        """Parse coverage data from coverage report."""
        coverage_file = Path("coverage-report.json")

        if coverage_file.exists():
            try:
                with open(coverage_file, 'r') as f:
                    coverage_data = json.load(f)

                # Extract overall coverage percentage
                totals = coverage_data.get("totals", {})
                coverage_percent = totals.get("percent_covered", 0)

                return {
                    "overall_coverage": coverage_percent,
                    "totals": totals,
                    "files": coverage_data.get("files", {})
                }

            except Exception as e:
                self.log(f"Failed to parse coverage data: {e}", "ERROR")

        return None

    def run_category_tests(self, category: str) -> Dict[str, Any]:
        """Run tests for a specific category."""
        self.log(f"Running {category} tests...")

        test_files = self.test_categories.get(category, [])
        if not test_files:
            self.log(f"No test files found for category: {category}", "WARNING")
            return {"success": False, "error": "No test files"}

        # Check if test files exist
        existing_files = []
        for test_file in test_files:
            if Path(test_file).exists():
                existing_files.append(test_file)
            else:
                self.log(f"Test file not found: {test_file}", "WARNING")

        if not existing_files:
            self.log(f"No existing test files for category: {category}", "WARNING")
            return {"success": False, "error": "No existing test files"}

        # Determine markers based on category
        markers = []
        if category == "docker_integration":
            markers = ["integration", "docker"]
        elif category == "supabase_integration":
            markers = ["integration", "supabase"]
        elif category == "mantine_ui":
            markers = ["integration", "mantine"]
        elif category == "end_to_end":
            markers = ["e2e"]
        elif category == "performance":
            markers = ["performance"]
        elif category == "existing_integration":
            markers = ["integration"]

        # Run tests
        result = self.run_pytest_command(existing_files, markers)

        # Calculate coverage score
        coverage_score = 0
        if result.get("coverage_data"):
            coverage_score = result["coverage_data"]["overall_coverage"]

        # Determine if category passes coverage threshold
        target_coverage = self.coverage_targets.get(category, 70)
        coverage_passed = coverage_score >= target_coverage

        result["category"] = category
        result["coverage_score"] = coverage_score
        result["coverage_target"] = target_coverage
        result["coverage_passed"] = coverage_passed

        return result

    def run_all_tests(self) -> Dict[str, Any]:
        """Run all comprehensive tests."""
        self.start_time = time.time()
        self.log("Starting comprehensive integration test suite...")

        overall_results = {
            "start_time": datetime.now().isoformat(),
            "categories": {},
            "summary": {
                "total_passed": 0,
                "total_failed": 0,
                "total_skipped": 0,
                "total_errors": 0,
                "categories_passed": 0,
                "categories_failed": 0,
                "overall_coverage": 0,
                "coverage_targets_met": 0
            }
        }

        # Run tests for each category
        for category in self.test_categories.keys():
            try:
                result = self.run_category_tests(category)
                overall_results["categories"][category] = result

                # Update summary
                if result.get("success"):
                    overall_results["summary"]["categories_passed"] += 1
                else:
                    overall_results["summary"]["categories_failed"] += 1

                # Update test counts
                test_summary = result.get("test_summary", {})
                overall_results["summary"]["total_passed"] += test_summary.get("passed", 0)
                overall_results["summary"]["total_failed"] += test_summary.get("failed", 0)
                overall_results["summary"]["total_skipped"] += test_summary.get("skipped", 0)
                overall_results["summary"]["total_errors"] += test_summary.get("errors", 0)

                # Update coverage metrics
                if result.get("coverage_passed"):
                    overall_results["summary"]["coverage_targets_met"] += 1

            except Exception as e:
                self.log(f"Failed to run {category} tests: {e}", "ERROR")
                overall_results["categories"][category] = {
                    "success": False,
                    "error": str(e),
                    "category": category
                }
                overall_results["summary"]["categories_failed"] += 1

        self.end_time = time.time()

        # Calculate overall metrics
        total_categories = len(self.test_categories)
        overall_results["summary"]["total_duration"] = self.end_time - self.start_time
        overall_results["summary"]["success_rate"] = (
            overall_results["summary"]["categories_passed"] / total_categories * 100
            if total_categories > 0 else 0
        )

        # Calculate overall coverage
        coverage_scores = [
            result.get("coverage_score", 0)
            for result in overall_results["categories"].values()
            if result.get("coverage_score") is not None
        ]

        if coverage_scores:
            overall_results["summary"]["overall_coverage"] = sum(coverage_scores) / len(coverage_scores)

        overall_results["end_time"] = datetime.now().isoformat()

        return overall_results

    def generate_report(self, results: Dict[str, Any]) -> str:
        """Generate comprehensive test report."""
        report_lines = []

        # Header
        report_lines.append("=" * 80)
        report_lines.append("COMPREHENSIVE INTEGRATION TEST REPORT")
        report_lines.append("=" * 80)
        report_lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append(f"Duration: {results['summary']['total_duration']:.2f} seconds")
        report_lines.append("")

        # Overall Summary
        summary = results["summary"]
        report_lines.append("OVERALL SUMMARY")
        report_lines.append("-" * 40)
        report_lines.append(f"Categories Passed: {summary['categories_passed']}")
        report_lines.append(f"Categories Failed: {summary['categories_failed']}")
        report_lines.append(f"Success Rate: {summary['success_rate']:.1f}%")
        report_lines.append(f"Overall Coverage: {summary['overall_coverage']:.1f}%")
        report_lines.append(f"Coverage Targets Met: {summary['coverage_targets_met']}/{len(self.test_categories)}")
        report_lines.append("")

        # Test Counts
        report_lines.append("TEST EXECUTION SUMMARY")
        report_lines.append("-" * 40)
        report_lines.append(f"Total Passed: {summary['total_passed']}")
        report_lines.append(f"Total Failed: {summary['total_failed']}")
        report_lines.append(f"Total Skipped: {summary['total_skipped']}")
        report_lines.append(f"Total Errors: {summary['total_errors']}")
        report_lines.append("")

        # Category Details
        report_lines.append("CATEGORY DETAILS")
        report_lines.append("-" * 40)

        for category, result in results["categories"].items():
            status = "✓ PASSED" if result.get("success") else "✗ FAILED"
            coverage = result.get("coverage_score", 0)
            target = result.get("coverage_target", 0)
            coverage_status = "✓" if result.get("coverage_passed") else "✗"

            report_lines.append(f"{category.upper():<25} {status}")
            report_lines.append(f"  Coverage: {coverage:.1f}% (target: {target}%) {coverage_status}")

            if "test_summary" in result:
                ts = result["test_summary"]
                report_lines.append(f"  Tests: {ts.get('passed', 0)} passed, {ts.get('failed', 0)} failed, {ts.get('skipped', 0)} skipped")

            if not result.get("success") and "error" in result:
                report_lines.append(f"  Error: {result['error']}")

            report_lines.append("")

        # Coverage Analysis
        report_lines.append("COVERAGE ANALYSIS")
        report_lines.append("-" * 40)

        coverage_by_category = {}
        for category, result in results["categories"].items():
            coverage_score = result.get("coverage_score", 0)
            coverage_target = result.get("coverage_target", 0)
            coverage_by_category[category] = {
                "score": coverage_score,
                "target": coverage_target,
                "met": coverage_score >= coverage_target
            }

        for category, coverage_info in coverage_by_category.items():
            status = "✓" if coverage_info["met"] else "✗"
            report_lines.append(f"{category:<25} {coverage_info['score']:>6.1f}% / {coverage_info['target']:>3.0f}% {status}")

        report_lines.append("")

        # Recommendations
        report_lines.append("RECOMMENDATIONS")
        report_lines.append("-" * 40)

        failed_categories = [cat for cat, result in results["categories"].items() if not result.get("success")]
        low_coverage = [cat for cat, info in coverage_by_category.items() if not info["met"]]

        if failed_categories:
            report_lines.append("Failed test categories to investigate:")
            for category in failed_categories:
                report_lines.append(f"  - {category}")

        if low_coverage:
            report_lines.append("Categories below coverage targets:")
            for category in low_coverage:
                info = coverage_by_category[category]
                report_lines.append(f"  - {category}: {info['score']:.1f}% (need {info['target']:.1f}%)")

        if summary["overall_coverage"] >= 90:
            report_lines.append("🎉 Excellent! Overall coverage target of >90% achieved!")
        elif summary["overall_coverage"] >= 80:
            report_lines.append("✅ Good coverage achieved. Consider improving to reach >90%.")
        else:
            report_lines.append("⚠️  Coverage below target. Focus on improving test coverage.")

        report_lines.append("")
        report_lines.append("=" * 80)

        return "\n".join(report_lines)

    def save_results(self, results: Dict[str, Any], report: str):
        """Save test results and report to files."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Save JSON results
        results_file = Path(f"test-results/comprehensive_test_results_{timestamp}.json")
        results_file.parent.mkdir(exist_ok=True)

        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2)

        # Save text report
        report_file = Path(f"test-results/comprehensive_test_report_{timestamp}.txt")
        with open(report_file, 'w') as f:
            f.write(report)

        self.log(f"Results saved to: {results_file}")
        self.log(f"Report saved to: {report_file}")

        return results_file, report_file


def main():
    """Main entry point for comprehensive test runner."""
    parser = argparse.ArgumentParser(description="Run comprehensive integration tests")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose output")
    parser.add_argument("--no-coverage", action="store_true", help="Disable coverage reporting")
    parser.add_argument("--category", choices=["docker_integration", "supabase_integration", "mantine_ui", "end_to_end", "performance", "existing_integration"], help="Run specific category only")
    parser.add_argument("--save-results", action="store_true", default=True, help="Save results to files")

    args = parser.parse_args()

    # Initialize test runner
    runner = ComprehensiveTestRunner(
        verbose=args.verbose,
        coverage=not args.no_coverage
    )

    try:
        if args.category:
            # Run specific category
            runner.log(f"Running tests for category: {args.category}")
            result = runner.run_category_tests(args.category)

            if result.get("success"):
                runner.log(f"Category {args.category} tests PASSED", "SUCCESS")
                exit_code = 0
            else:
                runner.log(f"Category {args.category} tests FAILED", "ERROR")
                exit_code = 1

            if args.verbose:
                print(result.get("stdout", ""))
                if result.get("stderr"):
                    print("STDERR:", result.get("stderr"))

        else:
            # Run all categories
            results = runner.run_all_tests()
            report = runner.generate_report(results)

            # Print report
            print(report)

            # Save results if requested
            if args.save_results:
                runner.save_results(results, report)

            # Determine exit code
            success_rate = results["summary"]["success_rate"]
            overall_coverage = results["summary"]["overall_coverage"]

            if success_rate >= 80 and overall_coverage >= 90:
                runner.log("🎉 Comprehensive tests PASSED with excellent coverage!", "SUCCESS")
                exit_code = 0
            elif success_rate >= 60 and overall_coverage >= 70:
                runner.log("✅ Comprehensive tests mostly PASSED with good coverage.", "WARNING")
                exit_code = 0
            else:
                runner.log("❌ Comprehensive tests FAILED or coverage too low.", "ERROR")
                exit_code = 1

        sys.exit(exit_code)

    except KeyboardInterrupt:
        runner.log("Test execution interrupted by user", "WARNING")
        sys.exit(130)

    except Exception as e:
        runner.log(f"Test execution failed: {e}", "ERROR")
        sys.exit(1)


if __name__ == "__main__":
    main()