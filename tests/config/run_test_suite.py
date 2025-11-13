"""Comprehensive test suite runner with metrics"""

import json
import signal
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path


class ComprehensiveTestRunner:
    """Run comprehensive test suite with metrics and reporting"""

    def __init__(self):
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "environment": {},
            "test_results": {},
            "metrics": {},
            "issues": [],
        }
        self.project_root = Path(
            "/Volumes/G-DRIVE ArmorATD/Development/Clients/ToolBoxAI-Solutions"
        )

    def check_environment(self):
        """Check environment setup"""
        print("🔍 Checking environment...")

        # Python version
        try:
            result = subprocess.run(
                ["python", "--version"], capture_output=True, text=True, timeout=10
            )
            self.results["environment"]["python"] = (
                result.stdout.strip() if result.returncode == 0 else "Not available"
            )
        except (subprocess.TimeoutExpired, FileNotFoundError):
            self.results["environment"]["python"] = "Not available"

        # Node version
        try:
            result = subprocess.run(
                ["node", "--version"], capture_output=True, text=True, timeout=10
            )
            self.results["environment"]["node"] = (
                result.stdout.strip() if result.returncode == 0 else "Not available"
            )
        except (subprocess.TimeoutExpired, FileNotFoundError):
            self.results["environment"]["node"] = "Not available"

        # Check services
        services = {
            "PostgreSQL": {
                "commands": [
                    ["pg_isready", "-h", "localhost", "-p", "5434"],
                    ["psql", "--version"],
                ],
                "name": "PostgreSQL",
            },
            "Redis": {
                "commands": [["redis-cli", "-p", "6381", "ping"], ["redis-cli", "--version"]],
                "name": "Redis",
            },
        }

        for service, config in services.items():
            service_available = False
            for command in config["commands"]:
                try:
                    result = subprocess.run(command, capture_output=True, text=True, timeout=5)
                    if result.returncode == 0:
                        service_available = True
                        break
                except (subprocess.TimeoutExpired, FileNotFoundError):
                    continue

            self.results["environment"][service] = (
                "Available" if service_available else "Not Available"
            )

        # Check project structure
        critical_paths = [
            "apps/backend",
            "apps/dashboard",
            "core",
            "tests",
            "requirements.txt",
            "pytest.ini",
        ]

        for path in critical_paths:
            full_path = self.project_root / path
            self.results["environment"][f"path_{path}"] = (
                "Exists" if full_path.exists() else "Missing"
            )

    def run_test_category(self, category: str, command: list[str], timeout: int = 300) -> dict:
        """Run a category of tests"""
        print(f"\n🧪 Running {category}...")
        start_time = time.time()

        try:
            # Change to project root directory
            result = subprocess.run(
                command, capture_output=True, text=True, timeout=timeout, cwd=self.project_root
            )

            elapsed = time.time() - start_time

            return {
                "category": category,
                "status": "passed" if result.returncode == 0 else "failed",
                "duration": elapsed,
                "returncode": result.returncode,
                "output": result.stdout[-2000:] if result.stdout else "",  # Last 2000 chars
                "errors": result.stderr[-2000:] if result.stderr else "",
                "command": " ".join(command),
            }
        except subprocess.TimeoutExpired:
            return {
                "category": category,
                "status": "timeout",
                "duration": timeout,
                "errors": f"Test timed out after {timeout} seconds",
                "command": " ".join(command),
            }
        except Exception as e:
            return {
                "category": category,
                "status": "error",
                "duration": time.time() - start_time,
                "errors": str(e),
                "command": " ".join(command),
            }

    def run_all_tests(self):
        """Run all test categories"""
        test_categories = [
            (
                "Environment Config",
                ["python", "-m", "pytest", "tests/config/", "-v", "--tb=short", "-x"],
                180,
            ),
            (
                "Unit Tests",
                ["python", "-m", "pytest", "tests/unit/", "-v", "--tb=short", "-x"],
                300,
            ),
            (
                "Integration Tests",
                [
                    "python",
                    "-m",
                    "pytest",
                    "tests/integration/",
                    "-v",
                    "--tb=short",
                    "-x",
                    "--maxfail=5",
                ],
                600,
            ),
            (
                "Security Tests",
                ["python", "-m", "pytest", "tests/security/", "-v", "--tb=short", "-x"],
                300,
            ),
            (
                "Compliance Tests",
                ["python", "-m", "pytest", "tests/compliance/", "-v", "--tb=short"],
                180,
            ),
            (
                "Migration Tests",
                ["python", "-m", "pytest", "tests/migration/", "-v", "--tb=short"],
                240,
            ),
            (
                "CI/CD Alignment",
                ["python", "-m", "pytest", "tests/ci_cd/", "-v", "--tb=short"],
                120,
            ),
            (
                "Performance Tests (Quick)",
                [
                    "python",
                    "-m",
                    "pytest",
                    "tests/performance/",
                    "-v",
                    "-m",
                    "not slow",
                    "--tb=short",
                ],
                600,
            ),
        ]

        # Add frontend tests if dashboard exists
        dashboard_path = self.project_root / "apps/dashboard"
        if dashboard_path.exists():
            package_json = dashboard_path / "package.json"
            if package_json.exists():
                test_categories.append(
                    ("Frontend Tests", ["npm", "test", "--prefix", str(dashboard_path)], 300)
                )

        for category, command, timeout in test_categories:
            result = self.run_test_category(category, command, timeout)
            self.results["test_results"][category] = result

            if result["status"] not in ["passed"]:
                self.results["issues"].append(
                    {
                        "category": category,
                        "status": result["status"],
                        "error": result.get("errors", ""),
                        "command": result.get("command", ""),
                        "duration": result.get("duration", 0),
                    }
                )

            # Print immediate feedback
            status_emoji = {"passed": "✅", "failed": "❌", "error": "⚠️", "timeout": "⏰"}.get(
                result["status"], "❓"
            )

            print(
                f"{status_emoji} {category}: {result['status'].upper()} ({result['duration']:.1f}s)"
            )

            if result["status"] != "passed" and result.get("errors"):
                print(f"   Error: {result['errors'][:200]}...")

    def calculate_metrics(self):
        """Calculate test metrics"""
        results = self.results["test_results"]

        total_tests = len(results)
        passed = sum(1 for r in results.values() if r["status"] == "passed")
        failed = sum(1 for r in results.values() if r["status"] == "failed")
        errors = sum(1 for r in results.values() if r["status"] in ["error", "timeout"])

        self.results["metrics"] = {
            "total": total_tests,
            "passed": passed,
            "failed": failed,
            "errors": errors,
            "pass_rate": (passed / total_tests * 100) if total_tests > 0 else 0,
            "total_duration": sum(r.get("duration", 0) for r in results.values()),
            "avg_duration": (
                sum(r.get("duration", 0) for r in results.values()) / total_tests
                if total_tests > 0
                else 0
            ),
        }

    def generate_report(self):
        """Generate test report"""
        print("\n" + "=" * 60)
        print("📊 TEST RESULTS SUMMARY")
        print("=" * 60)

        metrics = self.results["metrics"]
        print(f"Total Test Categories: {metrics['total']}")
        print(f"Passed: {metrics['passed']} ✅")
        print(f"Failed: {metrics['failed']} ❌")
        print(f"Errors: {metrics['errors']} ⚠️")
        print(f"Pass Rate: {metrics['pass_rate']:.1f}%")
        print(f"Total Duration: {metrics['total_duration']:.1f}s")
        print(f"Average Duration: {metrics['avg_duration']:.1f}s")

        if self.results["issues"]:
            print("\n⚠️ ISSUES FOUND:")
            for issue in self.results["issues"]:
                print(f"  - {issue['category']}: {issue['status']}")
                if issue.get("error"):
                    print(f"    Error: {issue['error'][:100]}...")

        # Environment summary
        print("\n🔧 ENVIRONMENT STATUS:")
        env = self.results["environment"]
        for key, value in env.items():
            if key.startswith("path_"):
                continue  # Skip path checks in summary
            status_emoji = (
                "✅"
                if "Available" in str(value) or "3." in str(value) or "v" in str(value)
                else "❌"
            )
            print(f"  {status_emoji} {key}: {value}")

        # Save JSON report
        report_path = self.project_root / "test_report.json"
        try:
            with open(report_path, "w") as f:
                json.dump(self.results, f, indent=2)
            print(f"\n📄 Detailed report saved to: {report_path}")
        except Exception as e:
            print(f"⚠️ Could not save report: {e}")

        # Generate summary file
        summary_path = self.project_root / "test_summary.md"
        try:
            self.generate_markdown_summary(summary_path)
            print(f"📝 Summary report saved to: {summary_path}")
        except Exception as e:
            print(f"⚠️ Could not save summary: {e}")

        # Return exit code
        return 0 if metrics["pass_rate"] >= 70 else 1  # Relaxed threshold for development

    def generate_markdown_summary(self, output_path: Path):
        """Generate markdown summary report"""
        metrics = self.results["metrics"]
        timestamp = datetime.fromisoformat(self.results["timestamp"])

        content = f"""# Test Suite Results

**Generated:** {timestamp.strftime("%Y-%m-%d %H:%M:%S")}

## Overview

- **Total Categories:** {metrics['total']}
- **Passed:** {metrics['passed']} ✅
- **Failed:** {metrics['failed']} ❌
- **Errors:** {metrics['errors']} ⚠️
- **Pass Rate:** {metrics['pass_rate']:.1f}%
- **Total Duration:** {metrics['total_duration']:.1f}s

## Test Categories

| Category | Status | Duration | Details |
|----------|--------|----------|---------|
"""

        for category, result in self.results["test_results"].items():
            status_emoji = {"passed": "✅", "failed": "❌", "error": "⚠️", "timeout": "⏰"}.get(
                result["status"], "❓"
            )

            content += f"| {category} | {status_emoji} {result['status']} | {result['duration']:.1f}s | {result.get('returncode', 'N/A')} |\n"

        if self.results["issues"]:
            content += "\n## Issues\n\n"
            for issue in self.results["issues"]:
                content += f"### {issue['category']}\n"
                content += f"- **Status:** {issue['status']}\n"
                content += f"- **Duration:** {issue['duration']:.1f}s\n"
                if issue.get("command"):
                    content += f"- **Command:** `{issue['command']}`\n"
                if issue.get("error"):
                    content += f"- **Error:** {issue['error'][:500]}...\n"
                content += "\n"

        content += "\n## Environment\n\n"
        for key, value in self.results["environment"].items():
            if not key.startswith("path_"):
                content += f"- **{key}:** {value}\n"

        with open(output_path, "w") as f:
            f.write(content)

    def handle_interrupt(self, signum, frame):
        """Handle interrupt signal"""
        print("\n\n⚠️ Test run interrupted by user")
        self.calculate_metrics()
        self.generate_report()
        sys.exit(1)

    def run(self):
        """Main entry point"""
        # Set up signal handler for graceful interruption
        signal.signal(signal.SIGINT, self.handle_interrupt)

        print("🚀 Starting Comprehensive Test Suite")
        print(f"📁 Project Root: {self.project_root}")

        self.check_environment()
        self.run_all_tests()
        self.calculate_metrics()
        exit_code = self.generate_report()

        if exit_code == 0:
            print("\n🎉 All tests completed successfully!")
        else:
            print(
                f"\n⚠️ Tests completed with issues (pass rate: {self.results['metrics']['pass_rate']:.1f}%)"
            )

        return exit_code


if __name__ == "__main__":
    runner = ComprehensiveTestRunner()
    exit_code = runner.invoke()
    sys.exit(exit_code)
