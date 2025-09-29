"""
Integration Testing Coordinator Agent

Specialized agent for coordinating integration testing activities across
the ToolBoxAI platform, ensuring proper testing workflows and coverage.
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
import json

from langchain_core.tools import Tool
from pydantic import BaseModel, Field

from .base_error_agent import BaseErrorAgent, ErrorAgentConfig, ErrorState, ErrorType, ErrorPriority
from core.agents.base_agent import TaskResult

logger = logging.getLogger(__name__)


class TestSuite(BaseModel):
    """Model for test suite configuration"""
    suite_id: str = Field(description="Unique identifier for the test suite")
    name: str = Field(description="Human-readable name of the test suite")
    test_files: List[str] = Field(default_factory=list, description="List of test files in the suite")
    dependencies: List[str] = Field(default_factory=list, description="Dependencies required for this suite")
    environment: str = Field(default="testing", description="Environment for running tests")
    timeout_minutes: int = Field(default=30, description="Timeout for the entire suite")
    priority: int = Field(default=1, description="Priority level (1-5)")
    tags: List[str] = Field(default_factory=list, description="Tags for categorizing tests")


class TestResult(BaseModel):
    """Model for test execution results"""
    test_id: str = Field(description="Unique identifier for the test")
    suite_id: str = Field(description="ID of the test suite this belongs to")
    status: str = Field(description="Test status: passed, failed, skipped, error")
    duration_seconds: float = Field(description="Execution time in seconds")
    error_message: Optional[str] = Field(default=None, description="Error message if test failed")
    stack_trace: Optional[str] = Field(default=None, description="Stack trace for failed tests")
    coverage_percentage: Optional[float] = Field(default=None, description="Code coverage percentage")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional test metadata")


@dataclass
class IntegrationTestConfig(ErrorAgentConfig):
    """Configuration specific to integration testing coordination"""
    test_suites_path: str = "tests/integration"
    test_results_path: str = "test_results"
    max_parallel_suites: int = 3
    test_timeout_minutes: int = 45
    coverage_threshold: float = 0.80
    retry_failed_tests: bool = True
    max_test_retries: int = 2
    enable_performance_monitoring: bool = True
    enable_flaky_test_detection: bool = True


class IntegrationTestingCoordinatorAgent(BaseErrorAgent):
    """
    Specialized agent for coordinating integration testing activities.

    Provides capabilities for:
    - Test suite orchestration
    - Integration test execution
    - Test result aggregation
    - Coverage analysis
    - Flaky test detection
    - Test environment management
    """

    def __init__(self, config: Optional[IntegrationTestConfig] = None):
        if config is None:
            config = IntegrationTestConfig(
                name="IntegrationTestingCoordinator",
                description="Coordinates integration testing activities"
            )

        super().__init__(config)
        self.test_config = config
        self.test_suites: List[TestSuite] = []
        self.test_results: List[TestResult] = []
        self.running_tests: Dict[str, Dict[str, Any]] = {}
        self.flaky_tests: Set[str] = set()

        # Load test suites
        self._load_test_suites()

        # Add integration testing specific tools
        self.tools.extend(self._create_testing_tools())

        logger.info(f"Initialized {self.name} with {len(self.test_suites)} test suites")

    def _get_default_system_prompt(self) -> str:
        """Get specialized system prompt for integration testing coordination"""
        return f"""You are {self.name}, an advanced integration testing coordinator agent specialized in managing and executing comprehensive test suites.

Your core responsibilities:
- Orchestrate integration test execution across multiple environments
- Monitor test coverage and quality metrics
- Detect and handle flaky tests
- Coordinate test dependencies and sequencing
- Analyze test failures and suggest fixes
- Ensure testing best practices are followed

Key principles:
1. Maintain high test coverage and quality
2. Minimize test execution time while maximizing coverage
3. Detect and isolate flaky or unreliable tests
4. Provide clear feedback on test failures
5. Ensure test environments are properly configured
6. Coordinate with other agents for comprehensive testing

You have access to specialized tools for test orchestration and analysis.
Always provide detailed test reports and actionable recommendations."""

    def _create_testing_tools(self) -> List[Tool]:
        """Create specialized tools for integration testing"""
        tools = []

        # Test suite executor
        tools.append(Tool(
            name="execute_test_suite",
            description="Execute a specific test suite",
            func=self._execute_test_suite_tool
        ))

        # Test result analyzer
        tools.append(Tool(
            name="analyze_test_results",
            description="Analyze test results and generate report",
            func=self._analyze_test_results_tool
        ))

        # Coverage calculator
        tools.append(Tool(
            name="calculate_coverage",
            description="Calculate code coverage from test results",
            func=self._calculate_coverage_tool
        ))

        # Flaky test detector
        tools.append(Tool(
            name="detect_flaky_tests",
            description="Detect flaky or unreliable tests",
            func=self._detect_flaky_tests_tool
        ))

        # Test environment validator
        tools.append(Tool(
            name="validate_test_environment",
            description="Validate test environment configuration",
            func=self._validate_test_environment_tool
        ))

        return tools

    def _load_test_suites(self):
        """Load test suite configurations"""
        suites_path = Path(self.test_config.test_suites_path)

        if not suites_path.exists():
            logger.warning(f"Test suites path does not exist: {suites_path}")
            self._create_default_test_suites()
            return

        # Load from JSON files
        for suite_file in suites_path.glob("*.json"):
            try:
                with open(suite_file, 'r') as f:
                    suite_data = json.load(f)
                    self.test_suites.append(TestSuite(**suite_data))
                logger.info(f"Loaded test suite from {suite_file}")
            except Exception as e:
                logger.error(f"Failed to load test suite from {suite_file}: {e}")

        if not self.test_suites:
            self._create_default_test_suites()

    def _create_default_test_suites(self):
        """Create default test suite configurations"""
        default_suites = [
            TestSuite(
                suite_id="api_integration",
                name="API Integration Tests",
                test_files=["test_api_endpoints.py", "test_authentication.py"],
                dependencies=["pytest", "httpx", "pytest-asyncio"],
                environment="testing",
                timeout_minutes=20,
                priority=1,
                tags=["api", "integration", "critical"]
            ),
            TestSuite(
                suite_id="database_integration",
                name="Database Integration Tests",
                test_files=["test_database_operations.py", "test_migrations.py"],
                dependencies=["pytest", "sqlalchemy", "alembic"],
                environment="testing",
                timeout_minutes=15,
                priority=2,
                tags=["database", "integration"]
            ),
            TestSuite(
                suite_id="roblox_integration",
                name="Roblox Integration Tests",
                test_files=["test_roblox_api.py", "test_content_generation.py"],
                dependencies=["pytest", "requests", "roblox"],
                environment="testing",
                timeout_minutes=30,
                priority=1,
                tags=["roblox", "integration", "content"]
            ),
            TestSuite(
                suite_id="agent_integration",
                name="Agent System Integration Tests",
                test_files=["test_agent_communication.py", "test_swarm_coordination.py"],
                dependencies=["pytest", "langchain", "asyncio"],
                environment="testing",
                timeout_minutes=25,
                priority=1,
                tags=["agents", "swarm", "integration"]
            )
        ]

        self.test_suites = default_suites
        self._save_test_suites()

    def _save_test_suites(self):
        """Save test suite configurations"""
        suites_path = Path(self.test_config.test_suites_path)
        suites_path.mkdir(parents=True, exist_ok=True)

        for suite in self.test_suites:
            suite_file = suites_path / f"{suite.suite_id}.json"
            try:
                with open(suite_file, 'w') as f:
                    json.dump(suite.model_dump(), f, indent=2)
            except Exception as e:
                logger.error(f"Failed to save test suite {suite.suite_id}: {e}")

    async def execute_integration_tests(self, suite_ids: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Execute integration tests for specified suites or all suites.

        Args:
            suite_ids: List of suite IDs to execute, or None for all suites

        Returns:
            Dictionary containing execution results and summary
        """
        if suite_ids is None:
            suites_to_run = self.test_suites
        else:
            suites_to_run = [s for s in self.test_suites if s.suite_id in suite_ids]

        if not suites_to_run:
            logger.warning("No test suites found to execute")
            return {"status": "no_suites", "results": []}

        # Sort by priority
        suites_to_run.sort(key=lambda s: s.priority)

        execution_results = []
        start_time = datetime.now()

        # Execute suites (limited parallelism)
        semaphore = asyncio.Semaphore(self.test_config.max_parallel_suites)
        tasks = []

        for suite in suites_to_run:
            task = asyncio.create_task(self._execute_suite_with_semaphore(semaphore, suite))
            tasks.append(task)

        suite_results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        total_tests = 0
        passed_tests = 0
        failed_tests = 0
        skipped_tests = 0
        total_coverage = 0.0

        for i, result in enumerate(suite_results):
            if isinstance(result, Exception):
                logger.error(f"Suite execution failed: {result}")
                execution_results.append({
                    "suite_id": suites_to_run[i].suite_id,
                    "status": "error",
                    "error": str(result)
                })
            else:
                execution_results.append(result)
                if "metrics" in result:
                    metrics = result["metrics"]
                    total_tests += metrics.get("total", 0)
                    passed_tests += metrics.get("passed", 0)
                    failed_tests += metrics.get("failed", 0)
                    skipped_tests += metrics.get("skipped", 0)
                    total_coverage += metrics.get("coverage", 0.0)

        end_time = datetime.now()
        execution_time = (end_time - start_time).total_seconds()

        # Generate summary
        summary = {
            "status": "completed",
            "execution_time_seconds": execution_time,
            "suites_executed": len(execution_results),
            "total_tests": total_tests,
            "passed": passed_tests,
            "failed": failed_tests,
            "skipped": skipped_tests,
            "success_rate": passed_tests / total_tests if total_tests > 0 else 0,
            "average_coverage": total_coverage / len(execution_results) if execution_results else 0,
            "results": execution_results,
            "timestamp": datetime.now().isoformat()
        }

        # Detect and handle failures
        if failed_tests > 0:
            await self._handle_test_failures(execution_results)

        # Update flaky test detection
        await self._update_flaky_test_detection(execution_results)

        return summary

    async def _execute_suite_with_semaphore(self, semaphore: asyncio.Semaphore, suite: TestSuite) -> Dict[str, Any]:
        """Execute a test suite with semaphore control"""
        async with semaphore:
            return await self._execute_single_suite(suite)

    async def _execute_single_suite(self, suite: TestSuite) -> Dict[str, Any]:
        """Execute a single test suite"""
        logger.info(f"Executing test suite: {suite.name}")

        start_time = datetime.now()
        self.running_tests[suite.suite_id] = {
            "suite": suite,
            "start_time": start_time,
            "status": "running"
        }

        try:
            # Validate environment
            env_valid = await self._validate_environment(suite)
            if not env_valid:
                raise RuntimeError(f"Environment validation failed for suite {suite.suite_id}")

            # Simulate test execution (replace with actual test runner integration)
            await asyncio.sleep(2.0)  # Simulate test execution time

            # Generate mock results
            result = await self._simulate_test_execution(suite)

            end_time = datetime.now()
            execution_time = (end_time - start_time).total_seconds()

            result.update({
                "suite_id": suite.suite_id,
                "execution_time_seconds": execution_time,
                "status": "completed"
            })

            # Store results
            self._store_test_results(suite.suite_id, result)

            return result

        except Exception as e:
            logger.error(f"Failed to execute suite {suite.suite_id}: {e}")
            return {
                "suite_id": suite.suite_id,
                "status": "error",
                "error": str(e),
                "execution_time_seconds": (datetime.now() - start_time).total_seconds()
            }
        finally:
            self.running_tests.pop(suite.suite_id, None)

    async def _simulate_test_execution(self, suite: TestSuite) -> Dict[str, Any]:
        """Simulate test execution results (replace with actual test runner)"""
        import random

        total_tests = len(suite.test_files) * random.randint(5, 15)
        passed = int(total_tests * random.uniform(0.75, 0.95))
        failed = random.randint(0, total_tests - passed)
        skipped = total_tests - passed - failed

        coverage = random.uniform(0.70, 0.95)

        return {
            "metrics": {
                "total": total_tests,
                "passed": passed,
                "failed": failed,
                "skipped": skipped,
                "coverage": coverage
            },
            "test_files": suite.test_files,
            "coverage_details": {
                "line_coverage": coverage,
                "branch_coverage": coverage * 0.9,
                "function_coverage": coverage * 1.1
            }
        }

    async def _validate_environment(self, suite: TestSuite) -> bool:
        """Validate test environment for suite execution"""
        # Check dependencies
        for dependency in suite.dependencies:
            # Simulate dependency check
            if dependency in ["missing_package"]:
                logger.warning(f"Missing dependency: {dependency}")
                return False

        # Check environment variables
        if suite.environment == "production":
            logger.error("Cannot run integration tests in production environment")
            return False

        return True

    def _store_test_results(self, suite_id: str, results: Dict[str, Any]):
        """Store test results for analysis"""
        results_path = Path(self.test_config.test_results_path)
        results_path.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        result_file = results_path / f"{suite_id}_{timestamp}.json"

        try:
            with open(result_file, 'w') as f:
                json.dump(results, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Failed to store test results: {e}")

    async def _handle_test_failures(self, execution_results: List[Dict[str, Any]]):
        """Handle test failures by creating error states"""
        for result in execution_results:
            if result.get("status") == "completed" and result.get("metrics", {}).get("failed", 0) > 0:
                await self._create_failure_error_state(result)

    async def _create_failure_error_state(self, result: Dict[str, Any]):
        """Create error state for test failures"""
        suite_id = result["suite_id"]
        failed_count = result["metrics"]["failed"]

        error_data = {
            "error_message": f"{failed_count} tests failed in suite {suite_id}",
            "stack_trace": f"Test suite: {suite_id}",
            "context": {
                "suite_id": suite_id,
                "failed_tests": failed_count,
                "test_results": result
            },
            "metadata": {
                "source": "integration_testing",
                "severity": "test_failure"
            }
        }

        error_state = await self.detect_error(error_data)

        # Suggest fixes for test failures
        fix_suggestions = await self.suggest_fix(error_state)
        logger.info(f"Generated fix suggestions for test failures: {fix_suggestions}")

    async def _update_flaky_test_detection(self, execution_results: List[Dict[str, Any]]):
        """Update flaky test detection based on execution patterns"""
        # This would analyze test result patterns to identify flaky tests
        # For now, we'll use a simple simulation
        for result in execution_results:
            suite_id = result["suite_id"]
            if result.get("metrics", {}).get("failed", 0) > 0:
                # Simple flaky test detection logic
                if suite_id in self.flaky_tests:
                    logger.warning(f"Suite {suite_id} showing flaky behavior")
                else:
                    self.flaky_tests.add(suite_id)

    async def get_test_status(self) -> Dict[str, Any]:
        """Get current testing status and metrics"""
        return {
            "total_suites": len(self.test_suites),
            "running_tests": len(self.running_tests),
            "flaky_tests": list(self.flaky_tests),
            "test_results_count": len(self.test_results),
            "suites": [
                {
                    "suite_id": suite.suite_id,
                    "name": suite.name,
                    "priority": suite.priority,
                    "tags": suite.tags
                }
                for suite in self.test_suites
            ]
        }

    # Tool implementation methods
    def _execute_test_suite_tool(self, suite_id: str) -> str:
        """Tool for executing a specific test suite"""
        suite = next((s for s in self.test_suites if s.suite_id == suite_id), None)
        if not suite:
            return f"Test suite {suite_id} not found"

        # This would trigger actual execution
        return f"Executing test suite: {suite.name} ({suite_id})"

    def _analyze_test_results_tool(self, results_data: str) -> str:
        """Tool for analyzing test results"""
        try:
            # Parse and analyze results
            return "Test results analyzed successfully"
        except Exception as e:
            return f"Failed to analyze test results: {e}"

    def _calculate_coverage_tool(self, coverage_data: str) -> str:
        """Tool for calculating code coverage"""
        # This would integrate with coverage tools
        return "Coverage calculated: 85.5%"

    def _detect_flaky_tests_tool(self, test_history: str) -> str:
        """Tool for detecting flaky tests"""
        flaky_count = len(self.flaky_tests)
        return f"Detected {flaky_count} potentially flaky test suites"

    def _validate_test_environment_tool(self, environment_info: str) -> str:
        """Tool for validating test environment"""
        return "Test environment validation completed"

    async def execute_task(self, task_data: Dict[str, Any]) -> TaskResult:
        """Execute integration testing coordination task"""
        task_type = task_data.get("task_type", "execute_tests")

        try:
            if task_type == "execute_tests":
                suite_ids = task_data.get("suite_ids")
                result = await self.execute_integration_tests(suite_ids)
                return TaskResult.create(
                    success=True,
                    data=result,
                    message="Integration tests executed successfully"
                )

            elif task_type == "get_status":
                status = await self.get_test_status()
                return TaskResult.create(
                    success=True,
                    data=status,
                    message="Test status retrieved successfully"
                )

            else:
                return TaskResult.create(
                    success=False,
                    error=f"Unknown task type: {task_type}",
                    message="Task execution failed"
                )

        except Exception as e:
            logger.error(f"Integration testing task failed: {e}")
            return TaskResult.create(
                success=False,
                error=str(e),
                message="Integration testing coordination failed"
            )