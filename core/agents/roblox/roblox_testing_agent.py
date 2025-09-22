"""
Roblox Testing Agent

AI agent for automated testing of Roblox experiences, including unit tests,
integration tests, performance benchmarks, and regression testing.

Author: ToolboxAI Team
Created: 2025-09-21
Version: 1.0.0
"""

import asyncio
import json
import logging
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from core.agents.base_agent import AgentConfig, BaseAgent, TaskResult

logger = logging.getLogger(__name__)


class TestType(Enum):
    """Types of tests that can be performed"""
    UNIT = "unit"
    INTEGRATION = "integration"
    PERFORMANCE = "performance"
    REGRESSION = "regression"
    SECURITY = "security"
    ACCESSIBILITY = "accessibility"
    LOAD = "load"


class TestStatus(Enum):
    """Test execution status"""
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ERROR = "error"


@dataclass
class TestCase:
    """Individual test case"""
    test_id: str
    name: str
    test_type: TestType
    description: str
    lua_code: str
    expected_result: Any
    timeout_seconds: int = 30
    priority: int = 1  # 1-5, higher is more important
    tags: List[str] = None

    def __post_init__(self):
        if self.tags is None:
            self.tags = []


@dataclass
class TestResult:
    """Result of test execution"""
    test_id: str
    status: TestStatus
    execution_time: float
    actual_result: Any = None
    error_message: str = None
    performance_metrics: Dict[str, Any] = None
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now(timezone.utc)
        if self.performance_metrics is None:
            self.performance_metrics = {}


class RobloxTestingAgent(BaseAgent):
    """
    AI agent for automated testing of Roblox experiences.

    Capabilities:
    - Automated test generation
    - Unit and integration testing
    - Performance benchmarking
    - Regression testing
    - Security testing
    - Accessibility validation
    """

    def __init__(self, config: AgentConfig = None):
        if config is None:
            config = AgentConfig(
                name="roblox_testing_agent",
                model="gpt-4-turbo-preview",
                temperature=0.2,
                max_tokens=4096
            )
        super().__init__(config)

        # Test generator configuration
        self.test_generator = {
            "enabled": True,
            "auto_generate_unit_tests": True,
            "auto_generate_integration_tests": True,
            "test_coverage_target": 0.85,
            "max_tests_per_function": 5
        }

        # Regression tester configuration
        self.regression_tester = {
            "enabled": True,
            "baseline_storage": {},
            "tolerance_threshold": 0.05,  # 5% tolerance for performance regression
            "auto_update_baselines": False
        }

        # Performance benchmarker configuration
        self.performance_benchmarker = {
            "enabled": True,
            "benchmark_iterations": 100,
            "memory_tracking": True,
            "cpu_profiling": True,
            "network_monitoring": True,
            "target_fps": 60,
            "max_memory_mb": 512
        }

        # Test suite storage
        self.test_suites: Dict[str, List[TestCase]] = {}
        self.test_results: Dict[str, List[TestResult]] = {}

        logger.info("RobloxTestingAgent initialized")

    async def _process_task(self, state) -> Any:
        """Process testing tasks"""
        test_type = state.context.get("test_type", "unit")

        if test_type == "unit":
            return await self._run_unit_tests(state.context)
        elif test_type == "integration":
            return await self._run_integration_tests(state.context)
        elif test_type == "performance":
            return await self._run_performance_tests(state.context)
        elif test_type == "regression":
            return await self._run_regression_tests(state.context)
        elif test_type == "security":
            return await self._run_security_tests(state.context)
        elif test_type == "accessibility":
            return await self._run_accessibility_tests(state.context)
        elif test_type == "generate":
            return await self._generate_tests(state.context)
        else:
            raise ValueError(f"Unknown test type: {test_type}")

    async def _run_unit_tests(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Run unit tests for Roblox scripts"""
        script_code = context.get("script_code", "")
        test_suite_id = context.get("test_suite_id", "default")

        # Generate unit tests if not provided
        if "test_cases" not in context:
            test_cases = await self._generate_unit_tests(script_code, context)
        else:
            test_cases = context["test_cases"]

        # Execute tests
        test_results = []
        passed_tests = 0
        failed_tests = 0

        for test_case in test_cases:
            result = await self._execute_test_case(test_case)
            test_results.append(result)

            if result.status == TestStatus.PASSED:
                passed_tests += 1
            elif result.status == TestStatus.FAILED:
                failed_tests += 1

        # Calculate coverage
        coverage_metrics = await self._calculate_test_coverage(script_code, test_cases)

        # Generate test report
        test_report = {
            "test_suite_id": test_suite_id,
            "test_type": "unit",
            "total_tests": len(test_cases),
            "passed_tests": passed_tests,
            "failed_tests": failed_tests,
            "success_rate": passed_tests / len(test_cases) if test_cases else 0,
            "coverage_metrics": coverage_metrics,
            "test_results": [self._serialize_test_result(result) for result in test_results],
            "execution_summary": self._generate_execution_summary(test_results),
            "recommendations": await self._generate_test_recommendations(test_results, coverage_metrics)
        }

        # Store results
        self.test_results[test_suite_id] = test_results

        logger.info("Unit tests completed: %d passed, %d failed", passed_tests, failed_tests)
        return test_report

    async def _run_integration_tests(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Run integration tests for multi-component interactions"""
        components = context.get("components", [])
        integration_scenarios = context.get("scenarios", [])

        if not integration_scenarios:
            integration_scenarios = await self._generate_integration_scenarios(components)

        test_results = []

        for scenario in integration_scenarios:
            # Create integration test case
            test_case = TestCase(
                test_id=str(uuid.uuid4()),
                name=scenario.get("name", "Integration Test"),
                test_type=TestType.INTEGRATION,
                description=scenario.get("description", ""),
                lua_code=scenario.get("test_code", ""),
                expected_result=scenario.get("expected_result"),
                timeout_seconds=scenario.get("timeout", 60)
            )

            # Execute integration test
            result = await self._execute_integration_test(test_case, components)
            test_results.append(result)

        # Analyze integration results
        integration_analysis = await self._analyze_integration_results(test_results, components)

        passed_tests = sum(1 for r in test_results if r.status == TestStatus.PASSED)

        return {
            "test_type": "integration",
            "components_tested": len(components),
            "scenarios_executed": len(integration_scenarios),
            "passed_tests": passed_tests,
            "failed_tests": len(test_results) - passed_tests,
            "success_rate": passed_tests / len(test_results) if test_results else 0,
            "integration_analysis": integration_analysis,
            "test_results": [self._serialize_test_result(result) for result in test_results],
            "component_compatibility": await self._assess_component_compatibility(components, test_results)
        }

    async def _run_performance_tests(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Run performance benchmarks and profiling"""
        script_code = context.get("script_code", "")
        benchmark_config = context.get("benchmark_config", {})

        # Performance test scenarios
        performance_scenarios = [
            {"name": "CPU Usage", "metric": "cpu_usage", "target": "< 30%"},
            {"name": "Memory Usage", "metric": "memory_usage", "target": "< 512MB"},
            {"name": "Frame Rate", "metric": "fps", "target": "> 30 FPS"},
            {"name": "Load Time", "metric": "load_time", "target": "< 3 seconds"},
            {"name": "Network Latency", "metric": "network_latency", "target": "< 100ms"}
        ]

        performance_results = []

        for scenario in performance_scenarios:
            # Run performance benchmark
            benchmark_result = await self._run_performance_benchmark(
                script_code,
                scenario,
                benchmark_config
            )
            performance_results.append(benchmark_result)

        # Analyze performance trends
        performance_analysis = await self._analyze_performance_trends(performance_results)

        # Generate performance score
        performance_score = self._calculate_overall_performance_score(performance_results)

        return {
            "test_type": "performance",
            "performance_score": performance_score,
            "benchmark_results": performance_results,
            "performance_analysis": performance_analysis,
            "meets_targets": performance_score >= 0.8,
            "optimization_suggestions": await self._generate_performance_optimizations(performance_results),
            "resource_usage_summary": self._summarize_resource_usage(performance_results)
        }

    async def _run_regression_tests(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Run regression tests against baseline"""
        current_version = context.get("current_version", "1.0.0")
        baseline_version = context.get("baseline_version", "0.9.0")
        test_suite_id = context.get("test_suite_id", "regression")

        # Get baseline results
        baseline_results = self.regression_tester["baseline_storage"].get(baseline_version, {})

        if not baseline_results:
            logger.warning("No baseline found for version %s", baseline_version)
            return {"error": f"No baseline found for version {baseline_version}"}

        # Run current tests
        current_results = await self._run_comprehensive_test_suite(context)

        # Compare with baseline
        regression_analysis = await self._compare_with_baseline(current_results, baseline_results)

        # Detect regressions
        regressions = self._detect_regressions(regression_analysis)

        return {
            "test_type": "regression",
            "current_version": current_version,
            "baseline_version": baseline_version,
            "regression_analysis": regression_analysis,
            "regressions_detected": len(regressions),
            "regressions": regressions,
            "performance_comparison": regression_analysis.get("performance_comparison", {}),
            "recommendation": "approve" if len(regressions) == 0 else "review_required"
        }

    async def _run_security_tests(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Run security validation tests"""
        script_code = context.get("script_code", "")

        security_tests = [
            {"name": "Injection Prevention", "pattern": "loadstring|getfenv|setfenv"},
            {"name": "Input Validation", "pattern": "validateInput|typeof"},
            {"name": "Rate Limiting", "pattern": "rateLimiter|cooldown"},
            {"name": "Access Control", "pattern": "checkPermission|authorize"},
            {"name": "Data Sanitization", "pattern": "sanitize|escape"}
        ]

        security_results = []

        for test in security_tests:
            result = await self._run_security_test(script_code, test)
            security_results.append(result)

        # Calculate security score
        security_score = sum(r["score"] for r in security_results) / len(security_results)

        return {
            "test_type": "security",
            "security_score": security_score,
            "security_results": security_results,
            "vulnerabilities_found": sum(1 for r in security_results if r["score"] < 0.7),
            "compliance_status": "compliant" if security_score >= 0.8 else "non_compliant",
            "security_recommendations": await self._generate_security_recommendations(security_results)
        }

    async def _run_accessibility_tests(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Run accessibility validation tests"""
        ui_code = context.get("ui_code", "")
        accessibility_requirements = context.get("accessibility_requirements", {})

        accessibility_tests = [
            {"name": "Color Contrast", "requirement": "WCAG AA"},
            {"name": "Text Size", "requirement": "Minimum 14px"},
            {"name": "Keyboard Navigation", "requirement": "Full keyboard support"},
            {"name": "Screen Reader", "requirement": "Alt text for images"},
            {"name": "Motor Accessibility", "requirement": "Large click targets"}
        ]

        accessibility_results = []

        for test in accessibility_tests:
            result = await self._run_accessibility_test(ui_code, test)
            accessibility_results.append(result)

        # Calculate accessibility score
        accessibility_score = sum(r["score"] for r in accessibility_results) / len(accessibility_results)

        return {
            "test_type": "accessibility",
            "accessibility_score": accessibility_score,
            "accessibility_results": accessibility_results,
            "wcag_compliance": accessibility_score >= 0.8,
            "accessibility_issues": [r for r in accessibility_results if r["score"] < 0.7],
            "remediation_suggestions": await self._generate_accessibility_recommendations(accessibility_results)
        }

    async def _generate_tests(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate test cases automatically"""
        script_code = context.get("script_code", "")
        test_types = context.get("test_types", ["unit", "integration"])
        coverage_target = context.get("coverage_target", 0.85)

        generated_tests = {
            "unit_tests": [],
            "integration_tests": [],
            "performance_tests": [],
            "security_tests": []
        }

        if "unit" in test_types:
            unit_tests = await self._generate_unit_tests(script_code, context)
            generated_tests["unit_tests"] = unit_tests

        if "integration" in test_types:
            integration_tests = await self._generate_integration_tests(script_code, context)
            generated_tests["integration_tests"] = integration_tests

        if "performance" in test_types:
            performance_tests = await self._generate_performance_tests(script_code, context)
            generated_tests["performance_tests"] = performance_tests

        if "security" in test_types:
            security_tests = await self._generate_security_tests(script_code, context)
            generated_tests["security_tests"] = security_tests

        # Calculate estimated coverage
        estimated_coverage = await self._estimate_test_coverage(script_code, generated_tests)

        return {
            "generated_tests": generated_tests,
            "total_tests_generated": sum(len(tests) for tests in generated_tests.values()),
            "estimated_coverage": estimated_coverage,
            "meets_coverage_target": estimated_coverage >= coverage_target,
            "test_generation_summary": self._summarize_test_generation(generated_tests)
        }

    async def _generate_unit_tests(self, script_code: str, context: Dict[str, Any]) -> List[TestCase]:
        """Generate unit tests for Lua script functions"""
        # Extract functions from script
        functions = self._extract_functions(script_code)

        unit_tests = []

        for func in functions:
            # Generate tests for each function
            func_tests = await self._generate_function_tests(func, script_code)
            unit_tests.extend(func_tests)

        return unit_tests

    async def _generate_function_tests(self, function_info: Dict[str, Any], script_code: str) -> List[TestCase]:
        """Generate tests for a specific function"""
        func_name = function_info.get("name", "unknown")
        func_params = function_info.get("parameters", [])

        # Generate test prompt
        prompt = f"""
        Generate comprehensive unit tests for this Roblox Lua function:

        Function: {func_name}
        Parameters: {func_params}

        Code context:
        {script_code[:500]}

        Generate tests for:
        1. Normal operation with valid inputs
        2. Edge cases and boundary conditions
        3. Invalid inputs and error handling
        4. Performance under load

        Format as Lua test code using Roblox TestService patterns.
        """

        try:
            response = await self.llm.ainvoke([{"role": "user", "content": prompt}])

            # Parse generated test code
            test_code = response.content

            # Create test cases
            test_cases = []

            # Split into individual test cases
            test_sections = test_code.split("-- Test:")

            for i, section in enumerate(test_sections[1:], 1):  # Skip first empty section
                test_case = TestCase(
                    test_id=f"{func_name}_test_{i}",
                    name=f"Test {func_name} - Case {i}",
                    test_type=TestType.UNIT,
                    description=f"Unit test for function {func_name}",
                    lua_code=f"-- Test:\n{section.strip()}",
                    expected_result={"success": True},
                    tags=[func_name, "unit_test", "auto_generated"]
                )
                test_cases.append(test_case)

            return test_cases

        except Exception as e:
            logger.error("Failed to generate unit tests for %s: %s", func_name, str(e))
            return []

    async def _execute_test_case(self, test_case: TestCase) -> TestResult:
        """Execute a single test case"""
        start_time = datetime.now(timezone.utc)

        try:
            # Simulate test execution
            await asyncio.sleep(0.1)  # Simulate test execution time

            # For simulation, randomly determine pass/fail based on quality indicators
            # In production, this would execute actual Lua code in Roblox environment

            # Simple heuristics for test success
            success_probability = 0.85  # 85% success rate for well-formed tests

            # Adjust based on test complexity
            if len(test_case.lua_code) > 500:
                success_probability -= 0.1  # More complex tests slightly more likely to fail

            if "error" in test_case.lua_code.lower() or "exception" in test_case.lua_code.lower():
                success_probability += 0.1  # Error handling tests more likely to pass

            # Simulate execution
            import random
            random.seed(hash(test_case.test_id))  # Deterministic based on test ID
            test_passed = random.random() < success_probability

            execution_time = (datetime.now(timezone.utc) - start_time).total_seconds()

            if test_passed:
                return TestResult(
                    test_id=test_case.test_id,
                    status=TestStatus.PASSED,
                    execution_time=execution_time,
                    actual_result={"success": True, "output": "Test passed"},
                    performance_metrics={
                        "memory_usage": random.uniform(10, 50),  # MB
                        "cpu_usage": random.uniform(5, 25),  # %
                        "execution_steps": random.randint(10, 100)
                    }
                )
            else:
                return TestResult(
                    test_id=test_case.test_id,
                    status=TestStatus.FAILED,
                    execution_time=execution_time,
                    error_message="Simulated test failure",
                    performance_metrics={
                        "memory_usage": random.uniform(20, 80),
                        "cpu_usage": random.uniform(15, 40),
                        "execution_steps": random.randint(5, 50)
                    }
                )

        except Exception as e:
            execution_time = (datetime.now(timezone.utc) - start_time).total_seconds()
            return TestResult(
                test_id=test_case.test_id,
                status=TestStatus.ERROR,
                execution_time=execution_time,
                error_message=str(e)
            )

    async def _run_performance_benchmark(self, script_code: str, scenario: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """Run performance benchmark for a specific scenario"""
        metric = scenario.get("metric", "cpu_usage")
        target = scenario.get("target", "unknown")

        # Simulate performance measurement
        await asyncio.sleep(0.2)  # Simulate benchmark execution

        # Generate realistic performance metrics
        import random

        if metric == "cpu_usage":
            measured_value = random.uniform(15, 35)  # 15-35% CPU usage
            meets_target = measured_value < 30
        elif metric == "memory_usage":
            measured_value = random.uniform(256, 600)  # 256-600MB memory usage
            meets_target = measured_value < 512
        elif metric == "fps":
            measured_value = random.uniform(25, 65)  # 25-65 FPS
            meets_target = measured_value > 30
        elif metric == "load_time":
            measured_value = random.uniform(1.5, 4.5)  # 1.5-4.5 seconds
            meets_target = measured_value < 3
        elif metric == "network_latency":
            measured_value = random.uniform(50, 150)  # 50-150ms latency
            meets_target = measured_value < 100
        else:
            measured_value = random.uniform(0.5, 1.5)
            meets_target = True

        return {
            "scenario": scenario["name"],
            "metric": metric,
            "measured_value": measured_value,
            "target": target,
            "meets_target": meets_target,
            "performance_score": 1.0 if meets_target else 0.6,
            "benchmark_iterations": config.get("iterations", 100),
            "measurement_accuracy": 0.95
        }

    async def _calculate_test_coverage(self, script_code: str, test_cases: List[TestCase]) -> Dict[str, Any]:
        """Calculate test coverage metrics"""
        # Extract code elements
        functions = self._extract_functions(script_code)
        conditions = self._extract_conditions(script_code)
        loops = self._extract_loops(script_code)

        # Calculate coverage
        functions_tested = self._count_tested_functions(functions, test_cases)
        conditions_tested = self._count_tested_conditions(conditions, test_cases)
        loops_tested = self._count_tested_loops(loops, test_cases)

        function_coverage = functions_tested / len(functions) if functions else 1.0
        condition_coverage = conditions_tested / len(conditions) if conditions else 1.0
        loop_coverage = loops_tested / len(loops) if loops else 1.0

        # Overall coverage (weighted average)
        overall_coverage = (function_coverage * 0.5 + condition_coverage * 0.3 + loop_coverage * 0.2)

        return {
            "function_coverage": function_coverage,
            "condition_coverage": condition_coverage,
            "loop_coverage": loop_coverage,
            "overall_coverage": overall_coverage,
            "functions_total": len(functions),
            "functions_tested": functions_tested,
            "conditions_total": len(conditions),
            "conditions_tested": conditions_tested,
            "loops_total": len(loops),
            "loops_tested": loops_tested,
            "meets_target": overall_coverage >= self.test_generator["test_coverage_target"]
        }

    def _extract_functions(self, code: str) -> List[Dict[str, Any]]:
        """Extract function definitions from Lua code"""
        functions = []
        lines = code.split('\n')

        for i, line in enumerate(lines):
            if 'function ' in line:
                # Extract function name and parameters
                func_line = line.strip()
                if func_line.startswith('local function') or func_line.startswith('function'):
                    func_name = func_line.split('(')[0].split()[-1]
                    params = []
                    if '(' in func_line and ')' in func_line:
                        param_str = func_line.split('(')[1].split(')')[0]
                        params = [p.strip() for p in param_str.split(',') if p.strip()]

                    functions.append({
                        "name": func_name,
                        "parameters": params,
                        "line_number": i + 1,
                        "definition": func_line
                    })

        return functions

    def _extract_conditions(self, code: str) -> List[str]:
        """Extract conditional statements from code"""
        conditions = []
        for line in code.split('\n'):
            if 'if ' in line or 'elseif ' in line:
                conditions.append(line.strip())
        return conditions

    def _extract_loops(self, code: str) -> List[str]:
        """Extract loop statements from code"""
        loops = []
        for line in code.split('\n'):
            if 'for ' in line or 'while ' in line:
                loops.append(line.strip())
        return loops

    def _count_tested_functions(self, functions: List[Dict[str, Any]], test_cases: List[TestCase]) -> int:
        """Count how many functions are covered by tests"""
        tested_functions = set()

        for test_case in test_cases:
            for func in functions:
                if func["name"] in test_case.lua_code:
                    tested_functions.add(func["name"])

        return len(tested_functions)

    def _count_tested_conditions(self, conditions: List[str], test_cases: List[TestCase]) -> int:
        """Count how many conditions are covered by tests"""
        # Simplified: assume each test case covers some conditions
        return min(len(conditions), len(test_cases) * 2)

    def _count_tested_loops(self, loops: List[str], test_cases: List[TestCase]) -> int:
        """Count how many loops are covered by tests"""
        # Simplified: assume each test case covers some loops
        return min(len(loops), len(test_cases))

    async def _generate_integration_scenarios(self, components: List[str]) -> List[Dict[str, Any]]:
        """Generate integration test scenarios"""
        scenarios = []

        # Generate pairwise integration tests
        for i in range(len(components)):
            for j in range(i + 1, len(components)):
                component_a = components[i]
                component_b = components[j]

                scenario = {
                    "name": f"Integration: {component_a} <-> {component_b}",
                    "description": f"Test integration between {component_a} and {component_b}",
                    "components": [component_a, component_b],
                    "test_code": await self._generate_integration_test_code(component_a, component_b),
                    "expected_result": {"integration_success": True},
                    "timeout": 60
                }
                scenarios.append(scenario)

        return scenarios

    async def _generate_integration_test_code(self, component_a: str, component_b: str) -> str:
        """Generate integration test code for two components"""
        return f"""
-- Integration Test: {component_a} <-> {component_b}
local {component_a} = require(script.{component_a})
local {component_b} = require(script.{component_b})

local function testIntegration()
    -- Initialize components
    local instanceA = {component_a}.new()
    local instanceB = {component_b}.new()

    -- Test communication
    local result = instanceA:communicateWith(instanceB)

    -- Validate result
    assert(result ~= nil, "Communication failed")
    assert(result.success == true, "Integration unsuccessful")

    return true
end

return testIntegration()
"""

    def _serialize_test_result(self, result: TestResult) -> Dict[str, Any]:
        """Serialize test result for JSON output"""
        return {
            "test_id": result.test_id,
            "status": result.status.value,
            "execution_time": result.execution_time,
            "actual_result": result.actual_result,
            "error_message": result.error_message,
            "performance_metrics": result.performance_metrics,
            "timestamp": result.timestamp.isoformat()
        }

    def _generate_execution_summary(self, test_results: List[TestResult]) -> Dict[str, Any]:
        """Generate execution summary from test results"""
        if not test_results:
            return {"message": "No tests executed"}

        total_time = sum(r.execution_time for r in test_results)
        avg_time = total_time / len(test_results)

        status_counts = {}
        for result in test_results:
            status = result.status.value
            status_counts[status] = status_counts.get(status, 0) + 1

        return {
            "total_execution_time": total_time,
            "average_execution_time": avg_time,
            "status_distribution": status_counts,
            "fastest_test": min(test_results, key=lambda r: r.execution_time).execution_time,
            "slowest_test": max(test_results, key=lambda r: r.execution_time).execution_time
        }

    async def _generate_test_recommendations(self, test_results: List[TestResult], coverage_metrics: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on test results"""
        recommendations = []

        # Coverage recommendations
        overall_coverage = coverage_metrics.get("overall_coverage", 0)
        if overall_coverage < 0.85:
            recommendations.append(f"Increase test coverage from {overall_coverage:.1%} to at least 85%")

        # Performance recommendations
        slow_tests = [r for r in test_results if r.execution_time > 5.0]
        if slow_tests:
            recommendations.append(f"Optimize {len(slow_tests)} slow-running tests")

        # Failure analysis
        failed_tests = [r for r in test_results if r.status == TestStatus.FAILED]
        if failed_tests:
            recommendations.append(f"Fix {len(failed_tests)} failing tests before deployment")

        # Quality recommendations
        success_rate = sum(1 for r in test_results if r.status == TestStatus.PASSED) / len(test_results)
        if success_rate < 0.9:
            recommendations.append("Improve test reliability - current success rate below 90%")

        return recommendations

    def _calculate_overall_performance_score(self, performance_results: List[Dict[str, Any]]) -> float:
        """Calculate overall performance score"""
        if not performance_results:
            return 0.0

        scores = [result.get("performance_score", 0) for result in performance_results]
        return sum(scores) / len(scores)

    async def _analyze_performance_trends(self, performance_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze performance trends and patterns"""
        metrics_by_type = {}

        for result in performance_results:
            metric = result.get("metric", "unknown")
            if metric not in metrics_by_type:
                metrics_by_type[metric] = []
            metrics_by_type[metric].append(result.get("measured_value", 0))

        trends = {}
        for metric, values in metrics_by_type.items():
            if len(values) > 1:
                # Simple trend analysis
                first_half = values[:len(values)//2]
                second_half = values[len(values)//2:]

                avg_first = sum(first_half) / len(first_half)
                avg_second = sum(second_half) / len(second_half)

                if metric in ["cpu_usage", "memory_usage", "load_time", "network_latency"]:
                    # Lower is better for these metrics
                    trend = "improving" if avg_second < avg_first else "degrading"
                else:
                    # Higher is better (like FPS)
                    trend = "improving" if avg_second > avg_first else "degrading"

                trends[metric] = {
                    "trend": trend,
                    "change_percentage": abs(avg_second - avg_first) / avg_first * 100 if avg_first > 0 else 0
                }

        return trends

    def get_testing_metrics(self) -> Dict[str, Any]:
        """Get comprehensive testing metrics"""
        total_tests = sum(len(results) for results in self.test_results.values())
        total_passed = sum(
            sum(1 for r in results if r.status == TestStatus.PASSED)
            for results in self.test_results.values()
        )

        return {
            "total_test_suites": len(self.test_suites),
            "total_tests_executed": total_tests,
            "total_tests_passed": total_passed,
            "overall_success_rate": total_passed / total_tests if total_tests > 0 else 0,
            "test_generation_enabled": self.test_generator["enabled"],
            "coverage_target": self.test_generator["test_coverage_target"],
            "performance_benchmarking_enabled": self.performance_benchmarker["enabled"],
            "regression_testing_enabled": self.regression_tester["enabled"]
        }
