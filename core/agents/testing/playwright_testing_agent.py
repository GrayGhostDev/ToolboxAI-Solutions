"""
Playwright Testing Agent for automated test orchestration and execution.

This agent manages Playwright test execution, Page Object Model creation,
and integration with the SPARC framework for intelligent test planning.
"""

import asyncio
import logging
import os
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from playwright.async_api import Browser, BrowserContext, Page, async_playwright

from core.agents.base_agent import BaseAgent
from core.coordinators.base_coordinator import TaskOutput
from core.sparc.state_manager import StateManager

logger = logging.getLogger(__name__)


@dataclass
class TestResult:
    """Represents a test execution result."""

    test_name: str
    status: str  # passed, failed, skipped
    duration_ms: int
    error_message: Optional[str] = None
    screenshot: Optional[str] = None
    video: Optional[str] = None
    trace: Optional[str] = None


@dataclass
class TestSuite:
    """Represents a collection of tests."""

    name: str
    tests: list[dict[str, Any]] = field(default_factory=list)
    page_objects: list[str] = field(default_factory=list)
    fixtures: list[str] = field(default_factory=list)
    coverage_target: float = 90.0


class PlaywrightTestingAgent(BaseAgent):
    """
    Agent for managing Playwright test execution and orchestration.

    Capabilities:
    - Automatic test generation from user stories
    - Page Object Model creation and management
    - Test orchestration and parallel execution
    - Coverage analysis and reporting
    - Integration with SPARC framework for intelligent test planning
    """

    def __init__(
        self,
        llm: Optional[Any] = None,
        state_manager: Optional[StateManager] = None,
        **kwargs,
    ):
        """Initialize the Playwright Testing Agent."""
        super().__init__(
            name="PlaywrightTestingAgent",
            description="Orchestrates Playwright test execution and management",
            llm=llm,
            state_manager=state_manager,
            **kwargs,
        )

        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.test_results: list[TestResult] = []
        self.test_suites: dict[str, TestSuite] = {}

        # Configuration
        self.config = {
            "browser": "chromium",
            "headless": os.getenv("CI", "false").lower() == "true",
            "timeout": 30000,
            "base_url": os.getenv("PLAYWRIGHT_BASE_URL", "http://localhost:5179"),
            "trace": True,
            "video": "retain-on-failure",
            "screenshot": "only-on-failure",
        }

    async def initialize_browser(self) -> None:
        """Initialize Playwright browser instance."""
        logger.info(f"Initializing {self.config['browser']} browser")

        playwright = await async_playwright().start()

        # Launch browser with configuration
        self.browser = await playwright[self.config["browser"]].launch(
            headless=self.config["headless"],
            args=["--no-sandbox", "--disable-setuid-sandbox"] if os.getenv("CI") else [],
        )

        # Create context with recording options
        self.context = await self.browser.new_context(
            base_url=self.config["base_url"],
            viewport={"width": 1280, "height": 720},
            record_video_dir="test-results/videos" if self.config["video"] else None,
        )

        # Start tracing if enabled
        if self.config["trace"]:
            await self.context.tracing.start(screenshots=True, snapshots=True, sources=True)

        # Create page
        self.page = await self.context.new_page()
        self.page.set_default_timeout(self.config["timeout"])

    async def cleanup_browser(self) -> None:
        """Cleanup browser resources."""
        if self.context and self.config["trace"]:
            await self.context.tracing.stop(path="test-results/trace.zip")

        if self.page:
            await self.page.close()

        if self.context:
            await self.context.close()

        if self.browser:
            await self.browser.close()

    async def create_page_object(self, page_name: str, selectors: dict[str, str]) -> str:
        """
        Generate a Page Object Model class.

        Args:
            page_name: Name of the page (e.g., 'LoginPage')
            selectors: Dictionary of element selectors

        Returns:
            Generated TypeScript code for the page object
        """
        logger.info(f"Creating Page Object Model for {page_name}")

        # Generate TypeScript Page Object Model
        code = f"""
import {{ Page, Locator }} from '@playwright/test';

export class {page_name} {{
    readonly page: Page;
"""

        # Add locator properties
        for name, selector in selectors.items():
            code += f"    readonly {name}: Locator;\n"

        # Add constructor
        code += f"""
    constructor(page: Page) {{
        this.page = page;
"""

        for name, selector in selectors.items():
            code += f"        this.{name} = page.locator('{selector}');\n"

        code += "    }\n\n"

        # Add common methods
        code += """    async goto() {
        await this.page.goto('/');
    }

    async waitForLoad() {
        await this.page.waitForLoadState('networkidle');
    }
}
"""

        # Store in test suite
        if "default" not in self.test_suites:
            self.test_suites["default"] = TestSuite(name="default")

        self.test_suites["default"].page_objects.append(page_name)

        return code

    async def execute_test(self, test_code: str, test_name: str = "test") -> TestResult:
        """
        Execute a single Playwright test.

        Args:
            test_code: JavaScript/TypeScript test code
            test_name: Name of the test

        Returns:
            Test execution result
        """
        logger.info(f"Executing test: {test_name}")

        if not self.page:
            await self.initialize_browser()

        start_time = datetime.now()
        result = TestResult(test_name=test_name, status="running", duration_ms=0)

        try:
            # Execute test code
            await self.page.evaluate(test_code)

            # Take screenshot on success
            if self.config["screenshot"] == "always":
                screenshot_path = f"test-results/screenshots/{test_name}_success.png"
                await self.page.screenshot(path=screenshot_path)
                result.screenshot = screenshot_path

            result.status = "passed"
            logger.info(f"Test {test_name} passed")

        except Exception as e:
            result.status = "failed"
            result.error_message = str(e)

            # Take screenshot on failure
            screenshot_path = f"test-results/screenshots/{test_name}_failure.png"
            await self.page.screenshot(path=screenshot_path)
            result.screenshot = screenshot_path

            logger.error(f"Test {test_name} failed: {str(e)}")

        # Calculate duration
        result.duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)

        # Store result
        self.test_results.append(result)

        return result

    async def run_test_suite(
        self, suite_name: str, parallel: bool = True, workers: int = 4
    ) -> dict[str, Any]:
        """
        Run a complete test suite.

        Args:
            suite_name: Name of the test suite
            parallel: Whether to run tests in parallel
            workers: Number of parallel workers

        Returns:
            Test suite execution summary
        """
        logger.info(f"Running test suite: {suite_name}")

        if suite_name not in self.test_suites:
            return {
                "error": f"Test suite '{suite_name}' not found",
                "available_suites": list(self.test_suites.keys()),
            }

        suite = self.test_suites[suite_name]
        results = []

        if parallel and len(suite.tests) > 1:
            # Run tests in parallel
            tasks = []
            for test in suite.tests[:workers]:
                task = asyncio.create_task(self.execute_test(test["code"], test["name"]))
                tasks.append(task)

            results = await asyncio.gather(*tasks)
        else:
            # Run tests sequentially
            for test in suite.tests:
                result = await self.execute_test(test["code"], test["name"])
                results.append(result)

        # Calculate summary
        total = len(results)
        passed = sum(1 for r in results if r.status == "passed")
        failed = sum(1 for r in results if r.status == "failed")
        skipped = sum(1 for r in results if r.status == "skipped")

        summary = {
            "suite": suite_name,
            "total": total,
            "passed": passed,
            "failed": failed,
            "skipped": skipped,
            "pass_rate": (passed / total * 100) if total > 0 else 0,
            "duration_ms": sum(r.duration_ms for r in results),
            "results": [
                {
                    "name": r.test_name,
                    "status": r.status,
                    "duration_ms": r.duration_ms,
                    "error": r.error_message,
                }
                for r in results
            ],
        }

        # Update state
        self.state_manager.update_state(
            {
                "task": "test_suite_execution",
                "suite": suite_name,
                "summary": summary,
                "timestamp": datetime.now().isoformat(),
            }
        )

        return summary

    async def generate_test_from_user_story(
        self, user_story: str, test_type: str = "e2e"
    ) -> dict[str, Any]:
        """
        Generate Playwright tests from a user story.

        Args:
            user_story: User story description
            test_type: Type of test (e2e, integration, unit)

        Returns:
            Generated test code and metadata
        """
        logger.info(f"Generating {test_type} test from user story")

        # Use SPARC framework for test planning
        sparc_output = await self.apply_sparc_framework(
            observation={"user_story": user_story, "test_type": test_type},
            action="generate_test",
            context={"platform": "educational", "framework": "playwright"},
        )

        # Generate test based on user story

        # This would normally call the LLM
        # For now, generate a template
        test_code = f"""
import {{ test, expect }} from '@playwright/test';

test.describe('{user_story[:50]}...', () => {{
    test.beforeEach(async ({{ page }}) => {{
        await page.goto('/');
    }});

    test('should {user_story.lower()}', async ({{ page }}) => {{
        // Test implementation
        await expect(page).toHaveTitle(/ToolBoxAI/);

        // User action simulation
        // TODO: Implement based on user story

        // Assertions
        // TODO: Add specific assertions

        // Accessibility check
        await expect(page).toHaveNoViolations();
    }});
}});
"""

        return {
            "test_code": test_code,
            "test_type": test_type,
            "user_story": user_story,
            "sparc_analysis": sparc_output,
        }

    async def analyze_coverage(
        self, coverage_data: Optional[dict[str, Any]] = None
    ) -> dict[str, Any]:
        """
        Analyze test coverage and identify gaps.

        Args:
            coverage_data: Optional coverage data to analyze

        Returns:
            Coverage analysis report
        """
        logger.info("Analyzing test coverage")

        if not coverage_data:
            # Get coverage from test results
            total_tests = len(self.test_results)
            passed_tests = sum(1 for r in self.test_results if r.status == "passed")

            coverage_data = {
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "coverage_percentage": (passed_tests / total_tests * 100) if total_tests > 0 else 0,
            }

        # Analyze coverage gaps
        gaps = []

        # Check authentication coverage
        auth_tests = [r for r in self.test_results if "auth" in r.test_name.lower()]
        if len(auth_tests) < 3:
            gaps.append("Insufficient authentication test coverage")

        # Check API coverage
        api_tests = [r for r in self.test_results if "api" in r.test_name.lower()]
        if len(api_tests) < 5:
            gaps.append("Insufficient API test coverage")

        # Check UI coverage
        ui_tests = [
            r
            for r in self.test_results
            if "ui" in r.test_name.lower() or "page" in r.test_name.lower()
        ]
        if len(ui_tests) < 10:
            gaps.append("Insufficient UI test coverage")

        return {
            "coverage": coverage_data,
            "gaps": gaps,
            "recommendations": self._generate_coverage_recommendations(gaps),
            "meets_target": coverage_data.get("coverage_percentage", 0) >= 90,
        }

    def _generate_coverage_recommendations(self, gaps: list[str]) -> list[str]:
        """Generate recommendations for improving coverage."""
        recommendations = []

        for gap in gaps:
            if "authentication" in gap.lower():
                recommendations.append("Add tests for login, logout, and role-based access")
            elif "api" in gap.lower():
                recommendations.append("Add tests for all critical API endpoints")
            elif "ui" in gap.lower():
                recommendations.append("Add tests for all user journeys and interactions")

        if not gaps:
            recommendations.append("Coverage target met - consider adding edge case tests")

        return recommendations

    async def parallel_test_execution(
        self, test_files: list[str], workers: int = 4
    ) -> dict[str, Any]:
        """
        Execute multiple test files in parallel.

        Args:
            test_files: List of test file paths
            workers: Number of parallel workers

        Returns:
            Execution summary
        """
        logger.info(f"Executing {len(test_files)} test files with {workers} workers")

        # Create worker tasks
        semaphore = asyncio.Semaphore(workers)

        async def run_test_file(test_file: str):
            async with semaphore:
                # Read test file
                with open(test_file) as f:
                    test_code = f.read()

                # Extract test name from file
                test_name = Path(test_file).stem

                # Execute test
                return await self.execute_test(test_code, test_name)

        # Run all tests in parallel
        tasks = [run_test_file(test_file) for test_file in test_files]
        results = await asyncio.gather(*tasks)

        # Generate summary
        return {
            "total_files": len(test_files),
            "results": [
                {
                    "file": test_files[i],
                    "status": results[i].status,
                    "duration_ms": results[i].duration_ms,
                }
                for i in range(len(results))
            ],
            "total_duration_ms": sum(r.duration_ms for r in results),
            "pass_rate": sum(1 for r in results if r.status == "passed") / len(results) * 100,
        }

    async def integration_test_verification(self) -> dict[str, Any]:
        """
        Verify all service integrations are working.

        Returns:
            Integration test results
        """
        logger.info("Running integration verification tests")

        integrations = {
            "database": False,
            "api": False,
            "realtime": False,
            "authentication": False,
            "storage": False,
        }

        if not self.page:
            await self.initialize_browser()

        # Test database connection through API
        try:
            response = await self.page.request.get("/api/v1/health/database")
            integrations["database"] = response.ok
        except Exception as e:
            logger.error(f"Database integration test failed: {e}")

        # Test API endpoints
        try:
            response = await self.page.request.get("/api/v1/health")
            integrations["api"] = response.ok
        except Exception as e:
            logger.error(f"API integration test failed: {e}")

        # Test real-time features (Pusher)
        try:
            response = await self.page.request.get("/api/v1/health/realtime")
            integrations["realtime"] = response.ok
        except Exception as e:
            logger.error(f"Realtime integration test failed: {e}")

        # Test authentication
        try:
            response = await self.page.request.get("/api/v1/auth/session")
            integrations["authentication"] = response.status in [200, 401]
        except Exception as e:
            logger.error(f"Authentication integration test failed: {e}")

        # Test storage
        try:
            response = await self.page.request.get("/api/v1/health/integrations")
            data = await response.json()
            integrations["storage"] = data.get("storage", {}).get("healthy", False)
        except Exception as e:
            logger.error(f"Storage integration test failed: {e}")

        # Calculate overall health
        healthy_count = sum(1 for v in integrations.values() if v)
        total_count = len(integrations)

        return {
            "integrations": integrations,
            "healthy": healthy_count,
            "total": total_count,
            "health_percentage": (healthy_count / total_count * 100),
            "all_healthy": all(integrations.values()),
        }

    async def process_task(self, task: str, context: dict[str, Any]) -> TaskOutput:
        """
        Process a testing task.

        Args:
            task: Task description
            context: Task context

        Returns:
            Task output with results
        """
        try:
            if "execute" in task.lower():
                # Execute tests
                result = await self.run_test_suite(
                    context.get("suite", "default"),
                    context.get("parallel", True),
                    context.get("workers", 4),
                )
            elif "generate" in task.lower():
                # Generate tests
                result = await self.generate_test_from_user_story(
                    context.get("user_story", ""), context.get("test_type", "e2e")
                )
            elif "coverage" in task.lower():
                # Analyze coverage
                result = await self.analyze_coverage(context.get("coverage_data"))
            elif "integration" in task.lower():
                # Verify integrations
                result = await self.integration_test_verification()
            elif "create" in task.lower() and "page" in task.lower():
                # Create page object
                result = await self.create_page_object(
                    context.get("page_name", "Page"), context.get("selectors", {})
                )
            else:
                result = {"error": f"Unknown task type: {task}"}

            return TaskOutput(
                success=True, result=result, metadata={"agent": self.name, "task": task}
            )

        except Exception as e:
            logger.error(f"Task processing failed: {str(e)}")
            return TaskOutput(
                success=False, error=str(e), metadata={"agent": self.name, "task": task}
            )
        finally:
            # Cleanup browser resources
            await self.cleanup_browser()
