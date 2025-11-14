"""Test Generation Agent for AI-powered test creation.

This agent automatically generates comprehensive test cases from:
- User stories and requirements
- API specifications
- UI interactions
- Code analysis
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional

from core.agents.base_agent import BaseAgent
from core.coordinators.error_coordinator import ErrorCoordinator
from core.sparc.state_manager import StateManager

logger = logging.getLogger(__name__)


@dataclass
class TestCase:
    """Represents a generated test case."""

    id: str
    name: str
    description: str
    type: str  # unit, integration, e2e
    priority: str  # high, medium, low
    tags: list[str]
    preconditions: list[str]
    steps: list[dict[str, str]]
    expected_results: list[str]
    assertions: list[str]
    data_requirements: Optional[dict[str, Any]] = None
    dependencies: Optional[list[str]] = None
    generated_code: Optional[str] = None


class TestGenerationAgent(BaseAgent):
    """
    Agent responsible for generating comprehensive test cases.

    Capabilities:
    - Generate tests from user stories
    - Create API test scenarios
    - Build UI interaction tests
    - Generate data-driven tests
    - Create edge case tests
    - Generate negative test scenarios
    """

    def __init__(self, name: str = "TestGenerationAgent", **kwargs):
        """Initialize the Test Generation Agent."""
        super().__init__(name=name, **kwargs)
        self.state_manager = StateManager()
        self.error_coordinator = ErrorCoordinator()

        # Test generation configuration
        self.config = {
            "max_tests_per_story": 10,
            "include_edge_cases": True,
            "include_negative_tests": True,
            "test_frameworks": {
                "python": "pytest",
                "javascript": "playwright",
                "api": "httpx",
            },
            "coverage_targets": {"unit": 0.80, "integration": 0.70, "e2e": 0.60},
        }

        # Test patterns and templates
        self.test_templates = self._load_test_templates()
        self.assertion_patterns = self._load_assertion_patterns()

    async def execute_task(self, task: dict[str, Any]) -> dict[str, Any]:
        """Execute test generation task."""
        try:
            action = task.get("action")

            if action == "generate_from_story":
                return await self.generate_from_user_story(task.get("story"))
            elif action == "generate_api_tests":
                return await self.generate_api_tests(task.get("spec"))
            elif action == "generate_ui_tests":
                return await self.generate_ui_tests(task.get("flow"))
            elif action == "generate_regression_suite":
                return await self.generate_regression_suite(task.get("changes"))
            elif action == "generate_data_tests":
                return await self.generate_data_driven_tests(task.get("schema"))
            else:
                return await self.generate_comprehensive_suite(task.get("requirements"))

        except Exception as e:
            return await self.handle_error(e, task)

    async def generate_from_user_story(self, story: dict[str, Any]) -> dict[str, Any]:
        """
        Generate test cases from user story.

        Example story:
        {
            'title': 'User Login',
            'as_a': 'registered user',
            'i_want': 'to log into the system',
            'so_that': 'I can access my dashboard',
            'acceptance_criteria': [
                'Valid credentials allow access',
                'Invalid credentials show error',
                'Remember me option works'
            ]
        }
        """
        logger.info(f"Generating tests from user story: {story.get('title')}")

        test_cases = []

        # Generate happy path test
        happy_path = await self._generate_happy_path_test(story)
        test_cases.append(happy_path)

        # Generate tests for each acceptance criterion
        for criterion in story.get("acceptance_criteria", []):
            test_case = await self._generate_acceptance_test(story, criterion)
            test_cases.append(test_case)

        # Generate edge cases
        if self.config["include_edge_cases"]:
            edge_cases = await self._generate_edge_cases(story)
            test_cases.extend(edge_cases)

        # Generate negative tests
        if self.config["include_negative_tests"]:
            negative_tests = await self._generate_negative_tests(story)
            test_cases.extend(negative_tests)

        # Generate test code
        for test_case in test_cases:
            test_case.generated_code = await self._generate_test_code(test_case)

        return {
            "status": "success",
            "story": story["title"],
            "test_cases": [self._serialize_test_case(tc) for tc in test_cases],
            "coverage_estimate": await self._estimate_coverage(test_cases),
            "execution_time_estimate": await self._estimate_execution_time(test_cases),
        }

    async def generate_api_tests(self, spec: dict[str, Any]) -> dict[str, Any]:
        """Generate API test cases from OpenAPI/Swagger spec."""
        logger.info("Generating API tests from specification")

        test_cases = []

        # Parse endpoints
        endpoints = spec.get("paths", {})

        for path, methods in endpoints.items():
            for method, details in methods.items():
                if method.upper() in ["GET", "POST", "PUT", "DELETE", "PATCH"]:
                    # Generate standard tests
                    test_case = await self._generate_api_test(
                        path=path, method=method, details=details
                    )
                    test_cases.append(test_case)

                    # Generate status code tests
                    status_tests = await self._generate_status_code_tests(
                        path=path, method=method, details=details
                    )
                    test_cases.extend(status_tests)

                    # Generate validation tests
                    validation_tests = await self._generate_validation_tests(
                        path=path, method=method, details=details
                    )
                    test_cases.extend(validation_tests)

        # Generate authentication tests
        auth_tests = await self._generate_auth_tests(spec)
        test_cases.extend(auth_tests)

        # Generate rate limiting tests
        rate_limit_tests = await self._generate_rate_limit_tests(endpoints)
        test_cases.extend(rate_limit_tests)

        return {
            "status": "success",
            "api_spec": spec.get("info", {}).get("title", "Unknown"),
            "test_cases": [self._serialize_test_case(tc) for tc in test_cases],
            "endpoints_covered": len(endpoints),
            "total_tests": len(test_cases),
        }

    async def generate_ui_tests(self, flow: dict[str, Any]) -> dict[str, Any]:
        """Generate UI test cases from user flow."""
        logger.info("Generating UI tests from user flow")

        test_cases = []

        # Parse UI flow
        pages = flow.get("pages", [])
        interactions = flow.get("interactions", [])

        # Generate page load tests
        for page in pages:
            page_test = await self._generate_page_load_test(page)
            test_cases.append(page_test)

            # Generate element visibility tests
            element_tests = await self._generate_element_tests(page)
            test_cases.extend(element_tests)

        # Generate interaction tests
        for interaction in interactions:
            interaction_test = await self._generate_interaction_test(interaction)
            test_cases.append(interaction_test)

        # Generate form validation tests
        form_tests = await self._generate_form_tests(flow)
        test_cases.extend(form_tests)

        # Generate navigation tests
        nav_tests = await self._generate_navigation_tests(flow)
        test_cases.extend(nav_tests)

        # Generate responsive tests
        responsive_tests = await self._generate_responsive_tests(pages)
        test_cases.extend(responsive_tests)

        return {
            "status": "success",
            "flow": flow.get("name", "Unknown"),
            "test_cases": [self._serialize_test_case(tc) for tc in test_cases],
            "pages_covered": len(pages),
            "interactions_covered": len(interactions),
        }

    async def generate_regression_suite(self, changes: dict[str, Any]) -> dict[str, Any]:
        """Generate regression test suite based on code changes."""
        logger.info("Generating regression test suite")

        test_cases = []

        # Analyze changed files
        changed_files = changes.get("files", [])

        for file in changed_files:
            # Generate tests for modified functions
            if file.get("type") == "modified":
                func_tests = await self._generate_function_tests(file)
                test_cases.extend(func_tests)

            # Generate integration tests for dependencies
            dep_tests = await self._generate_dependency_tests(file)
            test_cases.extend(dep_tests)

        # Generate smoke tests
        smoke_tests = await self._generate_smoke_tests(changes)
        test_cases.extend(smoke_tests)

        # Generate critical path tests
        critical_tests = await self._generate_critical_path_tests(changes)
        test_cases.extend(critical_tests)

        return {
            "status": "success",
            "changed_files": len(changed_files),
            "test_cases": [self._serialize_test_case(tc) for tc in test_cases],
            "risk_assessment": await self._assess_regression_risk(changes),
            "recommended_execution_order": await self._prioritize_tests(test_cases),
        }

    async def generate_data_driven_tests(self, schema: dict[str, Any]) -> dict[str, Any]:
        """Generate data-driven test cases."""
        logger.info("Generating data-driven tests")

        test_cases = []

        # Generate boundary value tests
        boundary_tests = await self._generate_boundary_tests(schema)
        test_cases.extend(boundary_tests)

        # Generate equivalence partition tests
        partition_tests = await self._generate_partition_tests(schema)
        test_cases.extend(partition_tests)

        # Generate combinatorial tests
        combo_tests = await self._generate_combinatorial_tests(schema)
        test_cases.extend(combo_tests)

        # Generate null/empty tests
        null_tests = await self._generate_null_tests(schema)
        test_cases.extend(null_tests)

        # Generate format validation tests
        format_tests = await self._generate_format_tests(schema)
        test_cases.extend(format_tests)

        return {
            "status": "success",
            "schema": schema.get("name", "Unknown"),
            "test_cases": [self._serialize_test_case(tc) for tc in test_cases],
            "data_combinations": await self._count_combinations(schema),
            "coverage_matrix": await self._generate_coverage_matrix(test_cases),
        }

    async def generate_comprehensive_suite(self, requirements: dict[str, Any]) -> dict[str, Any]:
        """Generate comprehensive test suite from requirements."""
        logger.info("Generating comprehensive test suite")

        all_tests = {
            "unit": [],
            "integration": [],
            "e2e": [],
            "performance": [],
            "security": [],
        }

        # Generate unit tests
        unit_tests = await self._generate_unit_tests(requirements)
        all_tests["unit"] = unit_tests

        # Generate integration tests
        integration_tests = await self._generate_integration_tests(requirements)
        all_tests["integration"] = integration_tests

        # Generate E2E tests
        e2e_tests = await self._generate_e2e_tests(requirements)
        all_tests["e2e"] = e2e_tests

        # Generate performance tests
        perf_tests = await self._generate_performance_tests(requirements)
        all_tests["performance"] = perf_tests

        # Generate security tests
        security_tests = await self._generate_security_tests(requirements)
        all_tests["security"] = security_tests

        # Calculate metrics
        total_tests = sum(len(tests) for tests in all_tests.values())

        return {
            "status": "success",
            "test_suites": {
                category: [self._serialize_test_case(tc) for tc in tests]
                for category, tests in all_tests.items()
            },
            "total_tests": total_tests,
            "coverage_prediction": await self._predict_coverage(all_tests),
            "execution_plan": await self._generate_execution_plan(all_tests),
            "resource_requirements": await self._calculate_resources(all_tests),
        }

    async def _generate_test_code(self, test_case: TestCase) -> str:
        """Generate actual test code for a test case."""
        if test_case.type == "e2e":
            return await self._generate_playwright_test(test_case)
        elif test_case.type == "api":
            return await self._generate_api_test_code(test_case)
        else:
            return await self._generate_pytest_test(test_case)

    async def _generate_playwright_test(self, test_case: TestCase) -> str:
        """Generate Playwright test code."""
        code = f"""
import {{ test, expect }} from '@playwright/test';

test.describe('{test_case.name}', () => {{
    test('{test_case.description}', async ({{ page }}) => {{
        // Preconditions
"""

        for precondition in test_case.preconditions:
            code += f"        // {precondition}\n"

        code += "\n        // Test steps\n"
        for step in test_case.steps:
            action = step.get("action", "")
            target = step.get("target", "")
            value = step.get("value", "")

            if action == "navigate":
                code += f"        await page.goto('{value}');\n"
            elif action == "click":
                code += f"        await page.click('{target}');\n"
            elif action == "fill":
                code += f"        await page.fill('{target}', '{value}');\n"
            elif action == "select":
                code += f"        await page.selectOption('{target}', '{value}');\n"
            elif action == "wait":
                code += f"        await page.waitForSelector('{target}');\n"

        code += "\n        // Assertions\n"
        for assertion in test_case.assertions:
            code += f"        {assertion}\n"

        code += "    });\n});\n"

        return code

    async def _generate_api_test_code(self, test_case: TestCase) -> str:
        """Generate API test code."""
        code = f"""
import httpx
import pytest

@pytest.mark.asyncio
async def test_{test_case.name.lower().replace(' ', '_')}():
    \"\"\"
    {test_case.description}
    \"\"\"
    async with httpx.AsyncClient() as client:
"""

        for step in test_case.steps:
            method = step.get("method", "GET")
            url = step.get("url", "")
            payload = step.get("payload", {})

            if method == "GET":
                code += f"        response = await client.get('{url}')\n"
            elif method == "POST":
                code += f"        response = await client.post('{url}', json={payload})\n"
            elif method == "PUT":
                code += f"        response = await client.put('{url}', json={payload})\n"
            elif method == "DELETE":
                code += f"        response = await client.delete('{url}')\n"

        code += "\n        # Assertions\n"
        for assertion in test_case.assertions:
            code += f"        {assertion}\n"

        return code

    async def _generate_pytest_test(self, test_case: TestCase) -> str:
        """Generate pytest test code."""
        code = f"""
import pytest

def test_{test_case.name.lower().replace(' ', '_')}():
    \"\"\"
    {test_case.description}
    \"\"\"
    # Setup
"""

        for precondition in test_case.preconditions:
            code += f"    # {precondition}\n"

        code += "\n    # Execute\n"
        for step in test_case.steps:
            code += f"    # {step.get('description', '')}\n"

        code += "\n    # Assert\n"
        for assertion in test_case.assertions:
            code += f"    {assertion}\n"

        return code

    def _load_test_templates(self) -> dict[str, str]:
        """Load test templates."""
        return {
            "unit": "def test_{name}():\n    # Arrange\n    # Act\n    # Assert\n",
            "integration": "async def test_{name}():\n    # Setup\n    # Execute\n    # Verify\n",
            "e2e": 'test("{name}", async ({ page }) => {{\n    // Navigate\n    // Interact\n    // Assert\n}});\n',
        }

    def _load_assertion_patterns(self) -> dict[str, str]:
        """Load assertion patterns."""
        return {
            "equality": "assert {actual} == {expected}",
            "contains": "assert {needle} in {haystack}",
            "visibility": 'await expect(page.locator("{selector}")).toBeVisible()',
            "text_content": 'await expect(page.locator("{selector}")).toHaveText("{text}")',
            "status_code": "assert response.status_code == {code}",
            "json_field": 'assert response.json()["{field}"] == {value}',
        }

    def _serialize_test_case(self, test_case: TestCase) -> dict[str, Any]:
        """Serialize test case to dictionary."""
        return {
            "id": test_case.id,
            "name": test_case.name,
            "description": test_case.description,
            "type": test_case.type,
            "priority": test_case.priority,
            "tags": test_case.tags,
            "preconditions": test_case.preconditions,
            "steps": test_case.steps,
            "expected_results": test_case.expected_results,
            "assertions": test_case.assertions,
            "data_requirements": test_case.data_requirements,
            "dependencies": test_case.dependencies,
            "generated_code": test_case.generated_code,
        }

    # Helper methods would continue here...
    async def _generate_happy_path_test(self, story: dict[str, Any]) -> TestCase:
        """Generate happy path test case."""
        return TestCase(
            id=f"tc_{datetime.now().timestamp()}",
            name=f"Happy Path - {story['title']}",
            description=f"Verify {story['i_want']} works correctly",
            type="e2e",
            priority="high",
            tags=["happy_path", "smoke"],
            preconditions=[f"User is {story['as_a']}"],
            steps=[
                {"action": "navigate", "target": "", "value": "/login"},
                {"action": "fill", "target": "#username", "value": "test_user"},
                {"action": "fill", "target": "#password", "value": "test_pass"},
                {"action": "click", "target": "#submit", "value": ""},
            ],
            expected_results=[story["so_that"]],
            assertions=['await expect(page).toHaveURL("/dashboard")'],
        )

    async def _generate_acceptance_test(self, story: dict[str, Any], criterion: str) -> TestCase:
        """Generate acceptance test case."""
        return TestCase(
            id=f"tc_{datetime.now().timestamp()}",
            name=f"AC - {criterion[:30]}",
            description=f"Verify: {criterion}",
            type="integration",
            priority="high",
            tags=["acceptance", "functional"],
            preconditions=[],
            steps=[{"description": f"Test {criterion}"}],
            expected_results=[criterion],
            assertions=[f'assert {criterion.lower().replace(" ", "_")} is True'],
        )

    async def _generate_edge_cases(self, story: dict[str, Any]) -> list[TestCase]:
        """Generate edge case tests."""
        return []  # Simplified for brevity

    async def _generate_negative_tests(self, story: dict[str, Any]) -> list[TestCase]:
        """Generate negative test cases."""
        return []  # Simplified for brevity

    async def _estimate_coverage(self, test_cases: list[TestCase]) -> float:
        """Estimate test coverage."""
        return min(0.95, len(test_cases) * 0.1)

    async def _estimate_execution_time(self, test_cases: list[TestCase]) -> int:
        """Estimate execution time in seconds."""
        return len(test_cases) * 5
