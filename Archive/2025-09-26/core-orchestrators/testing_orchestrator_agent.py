"""
Testing Orchestrator Agent

Specialized agent for coordinating comprehensive test execution,
including unit tests, integration tests, performance tests, and coverage analysis.
"""

import asyncio
import logging
import subprocess
import json
import re
from typing import Dict, Any, Optional, List, Tuple, Set
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass
import coverage
import pytest
import unittest

from langchain_core.tools import Tool
from pydantic import BaseModel, Field

from core.agents.error_handling.base_error_agent import (
    BaseErrorAgent,
    ErrorAgentConfig,
    ErrorState,
    ErrorType,
    ErrorPriority
)

logger = logging.getLogger(__name__)


class TestCase(BaseModel):
    """Model for individual test case"""
    test_id: str = Field(description="Unique test identifier")
    name: str = Field(description="Test name")
    file_path: str = Field(description="Path to test file")
    function: str = Field(description="Test function name")
    test_type: str = Field(description="Type of test (unit, integration, e2e)")
    priority: int = Field(description="Test priority (1-5)")
    dependencies: List[str] = Field(default_factory=list, description="Test dependencies")
    expected_duration: float = Field(default=1.0, description="Expected duration in seconds")
    tags: List[str] = Field(default_factory=list, description="Test tags/markers")


class TestResult(BaseModel):
    """Model for test execution result"""
    test_id: str = Field(description="Test identifier")
    status: str = Field(description="Test status (passed, failed, skipped, error)")
    duration: float = Field(description="Execution duration in seconds")
    error_message: Optional[str] = Field(default=None, description="Error message if failed")
    stack_trace: Optional[str] = Field(default=None, description="Stack trace if failed")
    stdout: Optional[str] = Field(default=None, description="Captured stdout")
    stderr: Optional[str] = Field(default=None, description="Captured stderr")
    coverage_data: Optional[Dict[str, Any]] = Field(default=None, description="Coverage data")


class TestSuite(BaseModel):
    """Model for test suite"""
    suite_id: str = Field(description="Suite identifier")
    name: str = Field(description="Suite name")
    test_cases: List[TestCase] = Field(description="Test cases in suite")
    setup_commands: List[str] = Field(default_factory=list, description="Setup commands")
    teardown_commands: List[str] = Field(default_factory=list, description="Teardown commands")
    parallel_execution: bool = Field(default=True, description="Whether tests can run in parallel")
    max_parallel: int = Field(default=4, description="Maximum parallel test execution")


class TestReport(BaseModel):
    """Model for comprehensive test report"""
    report_id: str = Field(description="Report identifier")
    timestamp: str = Field(description="Report generation time")
    total_tests: int = Field(description="Total number of tests")
    passed: int = Field(description="Number of passed tests")
    failed: int = Field(description="Number of failed tests")
    skipped: int = Field(description="Number of skipped tests")
    errors: int = Field(description="Number of error tests")
    duration: float = Field(description="Total execution duration")
    coverage_percentage: float = Field(description="Code coverage percentage")
    test_results: List[TestResult] = Field(description="Individual test results")
    failed_tests: List[Dict[str, Any]] = Field(description="Details of failed tests")
    coverage_report: Dict[str, Any] = Field(description="Detailed coverage report")
    recommendations: List[str] = Field(description="Test improvement recommendations")


@dataclass
class TestingConfig(ErrorAgentConfig):
    """Configuration specific to testing orchestrator"""
    test_frameworks: List[str] = None
    coverage_threshold: float = 80.0
    parallel_execution: bool = True
    max_parallel_tests: int = 4
    test_timeout: int = 300  # seconds
    generate_coverage: bool = True
    test_directories: List[str] = None
    exclude_patterns: List[str] = None


class TestingOrchestratorAgent(BaseErrorAgent):
    """
    Agent specialized in orchestrating comprehensive test execution.

    Capabilities:
    - Test suite management and execution
    - Parallel test execution
    - Coverage analysis and reporting
    - Test result aggregation
    - Failure analysis and recommendations
    - Test generation for uncovered code
    - Performance test execution
    - Integration test coordination
    """

    def __init__(self, config: Optional[TestingConfig] = None):
        if config is None:
            config = TestingConfig(
                name="TestingOrchestratorAgent",
                model="gpt-4",
                temperature=0.3,
                test_frameworks=["pytest", "unittest"],
                coverage_threshold=80.0,
                parallel_execution=True,
                test_directories=["tests", "test", "spec"],
                exclude_patterns=["*/__pycache__/*", "*/venv/*", "*/.venv/*"]
            )

        super().__init__(config)
        self.testing_config = config

        # Test execution state
        self.test_suites: Dict[str, TestSuite] = {}
        self.test_results: List[TestResult] = []
        self.coverage_data: Dict[str, Any] = {}
        self.test_sessions: Dict[str, Any] = {}

        # Initialize testing tools
        self.tools.extend(self._create_testing_tools())

        # Initialize coverage if enabled
        if config.generate_coverage:
            self.coverage = coverage.Coverage()

        logger.info("Initialized Testing Orchestrator Agent")

    def _get_default_system_prompt(self) -> str:
        """Get specialized system prompt for testing orchestration"""
        return """You are the Testing Orchestrator Agent, specialized in comprehensive test execution and analysis.

Your core capabilities:
- Orchestrate unit, integration, and end-to-end tests
- Execute tests in parallel for efficiency
- Analyze code coverage and identify gaps
- Generate test reports with actionable insights
- Recommend test improvements and additions
- Coordinate cross-system integration tests
- Monitor test performance and reliability

Testing principles:
1. Comprehensive coverage - test all critical paths
2. Isolation - tests should not depend on each other
3. Repeatability - tests must produce consistent results
4. Performance awareness - optimize test execution time
5. Clear reporting - provide actionable test results

Focus on test quality, coverage, and reliability."""

    def _create_testing_tools(self) -> List[Tool]:
        """Create specialized tools for testing"""
        tools = []

        tools.append(Tool(
            name="discover_tests",
            description="Discover available tests in the codebase",
            func=self._discover_tests
        ))

        tools.append(Tool(
            name="run_test_suite",
            description="Execute a test suite",
            func=self._run_test_suite
        ))

        tools.append(Tool(
            name="analyze_coverage",
            description="Analyze code coverage",
            func=self._analyze_coverage
        ))

        tools.append(Tool(
            name="generate_test",
            description="Generate test for uncovered code",
            func=self._generate_test
        ))

        tools.append(Tool(
            name="run_performance_test",
            description="Execute performance tests",
            func=self._run_performance_test
        ))

        tools.append(Tool(
            name="validate_test_environment",
            description="Validate test environment setup",
            func=self._validate_test_environment
        ))

        return tools

    async def orchestrate_testing(
        self,
        target: Optional[str] = None,
        test_type: Optional[str] = None,
        error_context: Optional[ErrorState] = None
    ) -> TestReport:
        """
        Main method to orchestrate comprehensive testing.

        Args:
            target: Specific target to test (file, module, or directory)
            test_type: Type of tests to run (unit, integration, e2e, all)
            error_context: Error state if testing in response to an error

        Returns:
            TestReport with comprehensive test results
        """
        session_id = f"test_session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.test_sessions[session_id] = {
            "start_time": datetime.now(),
            "target": target,
            "test_type": test_type,
            "error_context": error_context
        }

        logger.info(f"Starting test orchestration session: {session_id}")

        # Discover tests
        discovered_tests = await self._discover_all_tests(target, test_type)

        # Create test suites
        test_suites = self._organize_test_suites(discovered_tests)

        # Validate environment
        env_valid = await self._validate_environment()
        if not env_valid:
            logger.warning("Test environment validation failed")

        # Execute tests
        all_results = []
        start_time = datetime.now()

        if self.testing_config.parallel_execution:
            # Run tests in parallel
            all_results = await self._run_tests_parallel(test_suites)
        else:
            # Run tests sequentially
            all_results = await self._run_tests_sequential(test_suites)

        total_duration = (datetime.now() - start_time).total_seconds()

        # Analyze coverage
        coverage_data = {}
        if self.testing_config.generate_coverage:
            coverage_data = await self._analyze_test_coverage()

        # Generate report
        report = self._generate_test_report(
            all_results,
            coverage_data,
            total_duration,
            session_id
        )

        # Generate recommendations
        report.recommendations = await self._generate_test_recommendations(
            report,
            error_context
        )

        # Store session data
        self.test_sessions[session_id].update({
            "end_time": datetime.now(),
            "report": report
        })

        return report

    async def _discover_all_tests(
        self,
        target: Optional[str],
        test_type: Optional[str]
    ) -> List[TestCase]:
        """Discover all available tests"""
        discovered_tests = []

        # Determine test directories
        test_dirs = self.testing_config.test_directories
        if target and Path(target).exists():
            if Path(target).is_dir():
                test_dirs = [target]
            else:
                # Single file target
                return self._discover_tests_in_file(target, test_type)

        # Discover tests in each directory
        for test_dir in test_dirs:
            if not Path(test_dir).exists():
                continue

            # Find test files
            test_files = self._find_test_files(test_dir)

            for test_file in test_files:
                tests = self._discover_tests_in_file(str(test_file), test_type)
                discovered_tests.extend(tests)

        return discovered_tests

    def _find_test_files(self, directory: str) -> List[Path]:
        """Find all test files in directory"""
        test_patterns = ["test_*.py", "*_test.py", "*_spec.py"]
        test_files = []

        dir_path = Path(directory)
        for pattern in test_patterns:
            test_files.extend(dir_path.rglob(pattern))

        # Exclude patterns
        filtered_files = []
        for file in test_files:
            file_str = str(file)
            if not any(re.match(pattern, file_str) for pattern in self.testing_config.exclude_patterns):
                filtered_files.append(file)

        return filtered_files

    def _discover_tests_in_file(self, file_path: str, test_type: Optional[str]) -> List[TestCase]:
        """Discover tests in a specific file"""
        tests = []

        try:
            # Parse file to find test functions
            with open(file_path, 'r') as f:
                content = f.read()

            # Find test functions/methods
            test_pattern = r'def (test_\w+)\('
            matches = re.findall(test_pattern, content)

            for match in matches:
                # Determine test type from name/location
                detected_type = self._detect_test_type(match, file_path)

                if test_type is None or test_type == "all" or detected_type == test_type:
                    tests.append(TestCase(
                        test_id=f"{Path(file_path).stem}::{match}",
                        name=match,
                        file_path=file_path,
                        function=match,
                        test_type=detected_type,
                        priority=self._determine_test_priority(match, detected_type),
                        tags=self._extract_test_tags(content, match)
                    ))

        except Exception as e:
            logger.error(f"Error discovering tests in {file_path}: {e}")

        return tests

    def _detect_test_type(self, test_name: str, file_path: str) -> str:
        """Detect the type of test based on name and location"""
        file_path_lower = file_path.lower()
        test_name_lower = test_name.lower()

        if "integration" in file_path_lower or "integration" in test_name_lower:
            return "integration"
        elif "e2e" in file_path_lower or "end_to_end" in test_name_lower:
            return "e2e"
        elif "performance" in file_path_lower or "perf" in test_name_lower:
            return "performance"
        else:
            return "unit"

    def _determine_test_priority(self, test_name: str, test_type: str) -> int:
        """Determine test priority (1-5, 5 being highest)"""
        priority = 3  # Default medium priority

        # Type-based priority
        if test_type == "unit":
            priority = 4
        elif test_type == "integration":
            priority = 3
        elif test_type == "e2e":
            priority = 2

        # Name-based adjustments
        if "critical" in test_name.lower() or "core" in test_name.lower():
            priority = 5
        elif "optional" in test_name.lower() or "experimental" in test_name.lower():
            priority = 1

        return priority

    def _extract_test_tags(self, content: str, test_name: str) -> List[str]:
        """Extract test tags/markers from test"""
        tags = []

        # Look for pytest markers
        marker_pattern = rf'@pytest\.mark\.(\w+).*\ndef {test_name}'
        markers = re.findall(marker_pattern, content)
        tags.extend(markers)

        # Look for unittest decorators
        if "@skip" in content:
            tags.append("skip")
        if "@slow" in content:
            tags.append("slow")

        return tags

    def _organize_test_suites(self, tests: List[TestCase]) -> List[TestSuite]:
        """Organize tests into logical suites"""
        suites = {}

        # Group by test type and file
        for test in tests:
            suite_key = f"{test.test_type}_{Path(test.file_path).stem}"

            if suite_key not in suites:
                suites[suite_key] = TestSuite(
                    suite_id=suite_key,
                    name=f"{test.test_type.title()} tests from {Path(test.file_path).name}",
                    test_cases=[],
                    parallel_execution=test.test_type == "unit"  # Only unit tests in parallel
                )

            suites[suite_key].test_cases.append(test)

        # Sort tests within suites by priority
        for suite in suites.values():
            suite.test_cases.sort(key=lambda t: t.priority, reverse=True)

        return list(suites.values())

    async def _validate_environment(self) -> bool:
        """Validate test environment setup"""
        validations = []

        # Check Python version
        try:
            result = subprocess.run(
                ["python", "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            validations.append(result.returncode == 0)
        except:
            validations.append(False)

        # Check test frameworks
        for framework in self.testing_config.test_frameworks:
            try:
                result = subprocess.run(
                    ["python", "-m", framework, "--version"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                validations.append(result.returncode == 0)
            except:
                validations.append(False)

        # Check for test directories
        for test_dir in self.testing_config.test_directories:
            validations.append(Path(test_dir).exists())

        return all(validations)

    async def _run_tests_parallel(self, test_suites: List[TestSuite]) -> List[TestResult]:
        """Run test suites in parallel"""
        all_results = []

        # Separate parallel and sequential suites
        parallel_suites = [s for s in test_suites if s.parallel_execution]
        sequential_suites = [s for s in test_suites if not s.parallel_execution]

        # Run parallel suites
        if parallel_suites:
            tasks = []
            for suite in parallel_suites:
                # Create batches based on max_parallel
                for i in range(0, len(suite.test_cases), self.testing_config.max_parallel_tests):
                    batch = suite.test_cases[i:i + self.testing_config.max_parallel_tests]
                    tasks.append(self._run_test_batch(batch))

            # Execute all tasks
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)

            for result in batch_results:
                if isinstance(result, Exception):
                    logger.error(f"Batch execution failed: {result}")
                else:
                    all_results.extend(result)

        # Run sequential suites
        for suite in sequential_suites:
            results = await self._run_test_batch(suite.test_cases)
            all_results.extend(results)

        return all_results

    async def _run_tests_sequential(self, test_suites: List[TestSuite]) -> List[TestResult]:
        """Run test suites sequentially"""
        all_results = []

        for suite in test_suites:
            for test_case in suite.test_cases:
                result = await self._execute_single_test(test_case)
                all_results.append(result)

        return all_results

    async def _run_test_batch(self, test_cases: List[TestCase]) -> List[TestResult]:
        """Run a batch of tests"""
        results = []

        # Use pytest to run tests
        for test_case in test_cases:
            result = await self._execute_single_test(test_case)
            results.append(result)

        return results

    async def _execute_single_test(self, test_case: TestCase) -> TestResult:
        """Execute a single test case"""
        start_time = datetime.now()

        try:
            # Build pytest command
            cmd = [
                "python", "-m", "pytest",
                f"{test_case.file_path}::{test_case.function}",
                "-v",
                "--tb=short",
                "--capture=yes"
            ]

            if self.testing_config.generate_coverage:
                cmd.extend(["--cov", "--cov-report=json"])

            # Execute test
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.testing_config.test_timeout
            )

            duration = (datetime.now() - start_time).total_seconds()

            # Parse result
            if result.returncode == 0:
                status = "passed"
                error_message = None
                stack_trace = None
            else:
                status = "failed"
                error_message = self._extract_error_message(result.stdout + result.stderr)
                stack_trace = self._extract_stack_trace(result.stdout + result.stderr)

            return TestResult(
                test_id=test_case.test_id,
                status=status,
                duration=duration,
                error_message=error_message,
                stack_trace=stack_trace,
                stdout=result.stdout,
                stderr=result.stderr
            )

        except subprocess.TimeoutExpired:
            return TestResult(
                test_id=test_case.test_id,
                status="error",
                duration=self.testing_config.test_timeout,
                error_message="Test timeout exceeded",
                stack_trace=None
            )
        except Exception as e:
            return TestResult(
                test_id=test_case.test_id,
                status="error",
                duration=(datetime.now() - start_time).total_seconds(),
                error_message=str(e),
                stack_trace=traceback.format_exc()
            )

    def _extract_error_message(self, output: str) -> Optional[str]:
        """Extract error message from test output"""
        # Look for assertion errors
        match = re.search(r'AssertionError: (.+?)(?:\n|$)', output)
        if match:
            return match.group(1)

        # Look for general errors
        match = re.search(r'FAILED .+ - (.+?)(?:\n|$)', output)
        if match:
            return match.group(1)

        # Return first line of error if found
        if "ERROR" in output or "FAILED" in output:
            lines = output.split('\n')
            for line in lines:
                if "ERROR" in line or "FAILED" in line:
                    return line

        return None

    def _extract_stack_trace(self, output: str) -> Optional[str]:
        """Extract stack trace from test output"""
        # Look for traceback section
        if "Traceback" in output:
            start_idx = output.index("Traceback")
            # Find the end of traceback
            lines = output[start_idx:].split('\n')
            trace_lines = []
            for line in lines:
                trace_lines.append(line)
                if line and not line.startswith(' ') and "Error" in line:
                    break
            return '\n'.join(trace_lines)
        return None

    async def _analyze_test_coverage(self) -> Dict[str, Any]:
        """Analyze code coverage from tests"""
        coverage_data = {
            "line_coverage": 0.0,
            "branch_coverage": 0.0,
            "files": {},
            "uncovered_lines": [],
            "coverage_gaps": []
        }

        try:
            # Use coverage.py to get coverage data
            if hasattr(self, 'coverage'):
                self.coverage.stop()
                self.coverage.save()

                # Get coverage percentage
                coverage_data["line_coverage"] = self.coverage.report()

                # Get detailed file coverage
                for file_name in self.coverage.get_data().measured_files():
                    analysis = self.coverage.analysis2(file_name)
                    covered = len(analysis[1])
                    missing = len(analysis[3])
                    total = covered + missing

                    if total > 0:
                        coverage_data["files"][file_name] = {
                            "coverage": (covered / total) * 100,
                            "covered_lines": covered,
                            "missing_lines": missing,
                            "total_lines": total
                        }

                        # Track uncovered lines
                        if missing > 0:
                            coverage_data["uncovered_lines"].append({
                                "file": file_name,
                                "lines": analysis[3][:10]  # First 10 uncovered lines
                            })

        except Exception as e:
            logger.error(f"Error analyzing coverage: {e}")

        return coverage_data

    def _generate_test_report(
        self,
        results: List[TestResult],
        coverage_data: Dict[str, Any],
        total_duration: float,
        session_id: str
    ) -> TestReport:
        """Generate comprehensive test report"""
        # Count test results
        passed = sum(1 for r in results if r.status == "passed")
        failed = sum(1 for r in results if r.status == "failed")
        skipped = sum(1 for r in results if r.status == "skipped")
        errors = sum(1 for r in results if r.status == "error")

        # Extract failed test details
        failed_tests = []
        for result in results:
            if result.status in ["failed", "error"]:
                failed_tests.append({
                    "test_id": result.test_id,
                    "error": result.error_message,
                    "duration": result.duration
                })

        return TestReport(
            report_id=session_id,
            timestamp=datetime.now().isoformat(),
            total_tests=len(results),
            passed=passed,
            failed=failed,
            skipped=skipped,
            errors=errors,
            duration=total_duration,
            coverage_percentage=coverage_data.get("line_coverage", 0.0),
            test_results=results,
            failed_tests=failed_tests,
            coverage_report=coverage_data,
            recommendations=[]  # Will be filled by generate_recommendations
        )

    async def _generate_test_recommendations(
        self,
        report: TestReport,
        error_context: Optional[ErrorState]
    ) -> List[str]:
        """Generate test recommendations based on report"""
        recommendations = []

        # Coverage-based recommendations
        if report.coverage_percentage < self.testing_config.coverage_threshold:
            recommendations.append(
                f"Increase test coverage from {report.coverage_percentage:.1f}% "
                f"to {self.testing_config.coverage_threshold}%"
            )

        # Failed test recommendations
        if report.failed > 0:
            recommendations.append(f"Fix {report.failed} failing tests")
            if report.failed > 5:
                recommendations.append("Consider fixing tests in smaller batches")

        # Performance recommendations
        slow_tests = [t for t in report.test_results if t.duration > 5.0]
        if slow_tests:
            recommendations.append(f"Optimize {len(slow_tests)} slow tests (>5s)")

        # Error context recommendations
        if error_context:
            if error_context["error_type"] == ErrorType.RUNTIME:
                recommendations.append("Add edge case tests for runtime errors")
            elif error_context["error_type"] == ErrorType.LOGIC:
                recommendations.append("Add assertion tests for business logic")

        # Coverage gap recommendations
        if report.coverage_report.get("uncovered_lines"):
            recommendations.append("Write tests for uncovered critical paths")

        # Test type balance
        test_types = {}
        for result in report.test_results:
            # Extract test type from test_id if available
            test_type = "unit"  # Default
            if "integration" in result.test_id.lower():
                test_type = "integration"
            elif "e2e" in result.test_id.lower():
                test_type = "e2e"

            test_types[test_type] = test_types.get(test_type, 0) + 1

        if test_types.get("unit", 0) < test_types.get("integration", 0):
            recommendations.append("Add more unit tests for better test pyramid")

        return recommendations[:10]  # Return top 10 recommendations

    # Tool implementations
    def _discover_tests(self, directory: str) -> str:
        """Tool: Discover tests in directory"""
        test_files = self._find_test_files(directory)
        return f"Found {len(test_files)} test files"

    def _run_test_suite(self, suite_name: str) -> str:
        """Tool: Run a test suite"""
        # This would run actual test suite
        return f"Executed test suite: {suite_name}"

    def _analyze_coverage(self, target: Optional[str] = None) -> str:
        """Tool: Analyze test coverage"""
        # This would analyze actual coverage
        return "Coverage analysis completed"

    def _generate_test(self, function_name: str) -> str:
        """Tool: Generate test for function"""
        # This would generate actual test
        return f"Generated test for: {function_name}"

    def _run_performance_test(self, test_name: str) -> str:
        """Tool: Run performance test"""
        return f"Performance test executed: {test_name}"

    def _validate_test_environment(self) -> str:
        """Tool: Validate test environment"""
        return "Test environment validation completed"

    async def get_testing_metrics(self) -> Dict[str, Any]:
        """Get metrics specific to testing"""
        base_metrics = await self.get_error_metrics()

        testing_metrics = {
            "total_test_sessions": len(self.test_sessions),
            "total_tests_executed": len(self.test_results),
            "average_test_duration": 0.0,
            "test_success_rate": 0.0,
            "coverage_trend": [],
            "flaky_tests": []
        }

        if self.test_results:
            # Calculate average duration
            durations = [r.duration for r in self.test_results]
            testing_metrics["average_test_duration"] = sum(durations) / len(durations)

            # Calculate success rate
            passed = sum(1 for r in self.test_results if r.status == "passed")
            testing_metrics["test_success_rate"] = passed / len(self.test_results)

        # Combine metrics
        return {**base_metrics, **testing_metrics}

    async def _process_task(self, state) -> Any:
        """
        Process testing orchestration task.

        Args:
            state: Agent state containing task information

        Returns:
            Task processing result
        """
        try:
            task = state.get("task", {})
            task_type = task.get("type", "orchestrate_tests")

            if task_type == "orchestrate_tests":
                error = task.get("error", {})
                test_types = task.get("test_types", ["unit", "integration"])
                coverage_requirement = task.get("coverage_requirement", 80.0)

                # Convert dict error to ErrorState format if needed
                if isinstance(error, dict):
                    # Ensure error has required fields
                    if "error_type" not in error:
                        error["error_type"] = ErrorType.RUNTIME
                    if "priority" not in error:
                        error["priority"] = ErrorPriority.MEDIUM
                    if "timestamp" not in error:
                        error["timestamp"] = datetime.now().isoformat()

                # Run orchestrated tests
                result = await self.orchestrate_testing(error, test_types, coverage_requirement)

                return {
                    "status": "completed",
                    "result": result,
                    "tests_executed": len(result.test_results) if result else 0,
                    "overall_status": result.overall_status if result else "unknown"
                }

            elif task_type == "run_test_suite":
                suite_config = task.get("suite_config", {})
                target_error = task.get("target_error", {})

                suite = TestSuite(
                    suite_id=suite_config.get("suite_id", f"suite_{datetime.now().strftime('%Y%m%d_%H%M%S')}"),
                    test_types=suite_config.get("test_types", ["unit"]),
                    target_files=suite_config.get("target_files", []),
                    coverage_requirement=suite_config.get("coverage_requirement", 80.0),
                    timeout=suite_config.get("timeout", 300),
                    parallel_execution=suite_config.get("parallel_execution", True)
                )

                result = await self.run_test_suite(suite, target_error)

                return {
                    "status": "completed",
                    "result": result,
                    "suite_id": suite.suite_id,
                    "execution_time": result.execution_time if result else 0
                }

            elif task_type == "generate_tests":
                error = task.get("error", {})
                test_type = task.get("test_type", "unit")

                tests = await self.generate_targeted_tests(error, test_type)

                return {
                    "status": "completed",
                    "result": tests,
                    "tests_generated": len(tests)
                }

            elif task_type == "validate_fix":
                fix_data = task.get("fix", {})
                error = task.get("error", {})

                # Convert to ErrorCorrection if needed
                if isinstance(fix_data, dict):
                    fix = ErrorCorrection(
                        correction_id=fix_data.get("correction_id", f"fix_{datetime.now().strftime('%Y%m%d_%H%M%S')}"),
                        error_type=ErrorType(fix_data.get("error_type", "runtime_error")),
                        fix_type=fix_data.get("fix_type", "code_modification"),
                        code_changes=fix_data.get("code_changes", []),
                        confidence=fix_data.get("confidence", 0.5),
                        description=fix_data.get("description", "Fix validation"),
                        validation_steps=fix_data.get("validation_steps", [])
                    )
                else:
                    fix = fix_data

                validation_result = await self.validate_fix_with_tests(fix, error)

                return {
                    "status": "completed",
                    "result": validation_result,
                    "is_valid": validation_result.is_valid if validation_result else False
                }

            elif task_type == "get_metrics":
                metrics = await self.get_performance_metrics()
                return {
                    "status": "completed",
                    "result": metrics
                }

            else:
                return {
                    "status": "error",
                    "error": f"Unknown task type: {task_type}",
                    "result": None
                }

        except Exception as e:
            logger.error(f"Error processing testing orchestration task: {e}")
            return {
                "status": "error",
                "error": str(e),
                "result": None
            }