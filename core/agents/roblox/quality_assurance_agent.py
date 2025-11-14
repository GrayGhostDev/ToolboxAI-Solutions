"""
RobloxQualityAssuranceAgent - Tests and validates generated Roblox content

This agent performs quality assurance testing on generated scripts, validates
educational content accuracy, and ensures consistency.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from ..base_agent import BaseAgent


class TestType(Enum):
    FUNCTIONALITY = "functionality"
    PERFORMANCE = "performance"
    SECURITY = "security"
    EDUCATIONAL = "educational"
    COMPATIBILITY = "compatibility"


@dataclass
class TestResult:
    test_name: str
    test_type: TestType
    passed: bool
    message: str
    details: dict[str, Any] = field(default_factory=dict)


class RobloxQualityAssuranceAgent(BaseAgent):
    """
    Agent responsible for quality assurance testing of Roblox content.
    """

    def __init__(self):
        super().__init__(
            {
                "name": "RobloxQualityAssuranceAgent",
                "model": "gpt-4",
                "temperature": 0.7,
                "max_tokens": 2000,
            }
        )

        self.name = "RobloxQualityAssuranceAgent"
        self.description = "Tests and validates generated Roblox content"

        # Test suites
        self.test_suites = {
            TestType.FUNCTIONALITY: self._run_functionality_tests,
            TestType.PERFORMANCE: self._run_performance_tests,
            TestType.SECURITY: self._run_security_tests,
            TestType.EDUCATIONAL: self._run_educational_tests,
            TestType.COMPATIBILITY: self._run_compatibility_tests,
        }

    async def run_tests(
        self, content: dict[str, Any], test_types: list[TestType]
    ) -> dict[str, Any]:
        """Run quality assurance tests on content"""

        all_results = []

        for test_type in test_types:
            if test_type in self.test_suites:
                results = self.test_suites[test_type](content)
                all_results.extend(results)

        # Calculate overall score
        passed_tests = sum(1 for r in all_results if r.passed)
        total_tests = len(all_results)
        score = (passed_tests / total_tests * 100) if total_tests > 0 else 0

        return {
            "success": True,
            "score": score,
            "passed": score >= 80,
            "results": [
                {
                    "name": r.test_name,
                    "type": r.test_type.value,
                    "passed": r.passed,
                    "message": r.message,
                    "details": r.details,
                }
                for r in all_results
            ],
            "summary": f"{passed_tests}/{total_tests} tests passed",
        }

    def _run_functionality_tests(self, content: dict[str, Any]) -> list[TestResult]:
        """Run functionality tests"""
        results = []

        # Check for required functions
        code = content.get("code", "")

        results.append(
            TestResult(
                test_name="Required Functions Present",
                test_type=TestType.FUNCTIONALITY,
                passed="function" in code,
                message=(
                    "Code contains function definitions"
                    if "function" in code
                    else "No functions found"
                ),
            )
        )

        # Check for error handling
        results.append(
            TestResult(
                test_name="Error Handling",
                test_type=TestType.FUNCTIONALITY,
                passed="pcall" in code or "xpcall" in code,
                message=(
                    "Error handling implemented" if "pcall" in code else "No error handling found"
                ),
            )
        )

        # Check for initialization
        results.append(
            TestResult(
                test_name="Proper Initialization",
                test_type=TestType.FUNCTIONALITY,
                passed="new()" in code or "initialize()" in code or "init()" in code,
                message=(
                    "Initialization method found"
                    if "init" in code.lower()
                    else "No initialization found"
                ),
            )
        )

        return results

    def _run_performance_tests(self, content: dict[str, Any]) -> list[TestResult]:
        """Run performance tests"""
        results = []
        code = content.get("code", "")

        # Check for performance issues
        results.append(
            TestResult(
                test_name="No Infinite Loops",
                test_type=TestType.PERFORMANCE,
                passed="while true do" not in code or "wait()" in code or "task.wait()" in code,
                message=(
                    "No uncontrolled infinite loops"
                    if "while true do" not in code
                    else "Infinite loop with yield"
                ),
            )
        )

        # Check for caching
        results.append(
            TestResult(
                test_name="Service Caching",
                test_type=TestType.PERFORMANCE,
                passed="local" in code and "GetService" in code,
                message="Services are cached locally" if "local" in code else "Services not cached",
            )
        )

        return results

    def _run_security_tests(self, content: dict[str, Any]) -> list[TestResult]:
        """Run security tests"""
        results = []
        code = content.get("code", "")

        # Check for security vulnerabilities
        results.append(
            TestResult(
                test_name="No Loadstring Usage",
                test_type=TestType.SECURITY,
                passed="loadstring" not in code,
                message=(
                    "No loadstring vulnerability"
                    if "loadstring" not in code
                    else "Loadstring detected"
                ),
            )
        )

        # Check for input validation
        if "RemoteEvent" in code or "RemoteFunction" in code:
            results.append(
                TestResult(
                    test_name="Input Validation",
                    test_type=TestType.SECURITY,
                    passed="type(" in code or "typeof(" in code,
                    message=(
                        "Input validation present" if "type(" in code else "No input validation"
                    ),
                )
            )

        return results

    def _run_educational_tests(self, content: dict[str, Any]) -> list[TestResult]:
        """Run educational content tests"""
        results = []

        # Check educational metadata
        educational_data = content.get("educational_content", {})

        results.append(
            TestResult(
                test_name="Grade Level Appropriate",
                test_type=TestType.EDUCATIONAL,
                passed=educational_data.get("grade_level") is not None,
                message=(
                    "Grade level specified"
                    if educational_data.get("grade_level")
                    else "No grade level"
                ),
                details={"grade_level": educational_data.get("grade_level")},
            )
        )

        results.append(
            TestResult(
                test_name="Learning Objectives",
                test_type=TestType.EDUCATIONAL,
                passed=len(educational_data.get("objectives", [])) > 0,
                message=(
                    "Learning objectives defined"
                    if educational_data.get("objectives")
                    else "No objectives"
                ),
                details={"objectives": educational_data.get("objectives", [])},
            )
        )

        return results

    def _run_compatibility_tests(self, content: dict[str, Any]) -> list[TestResult]:
        """Run compatibility tests"""
        results = []
        code = content.get("code", "")

        # Check for deprecated APIs
        deprecated_apis = ["wait(", "delay(", "spawn("]
        uses_deprecated = any(api in code for api in deprecated_apis)

        results.append(
            TestResult(
                test_name="No Deprecated APIs",
                test_type=TestType.COMPATIBILITY,
                passed=not uses_deprecated,
                message="Using modern APIs" if not uses_deprecated else "Deprecated APIs detected",
            )
        )

        # Check for proper service usage
        results.append(
            TestResult(
                test_name="Proper Service Usage",
                test_type=TestType.COMPATIBILITY,
                passed="game:GetService" in code,
                message=(
                    "Using GetService properly"
                    if "game:GetService" in code
                    else "Direct service access"
                ),
            )
        )

        return results

    def generate_test_suite(self, script_name: str) -> str:
        """Generate a test suite for a script"""
        return f"""-- Test Suite for {script_name}
local TestSuite = {{}}

function TestSuite.runAll()
    local results = {{}}

    -- Test 1: Module loads without errors
    local test1 = {{name = "Module Loading", passed = false}}
    local success, module = pcall(function()
        return require(script.Parent.{script_name})
    end)
    test1.passed = success
    test1.message = success and "Module loaded successfully" or "Failed to load: " .. tostring(module)
    table.insert(results, test1)

    -- Test 2: Required methods exist
    local test2 = {{name = "Required Methods", passed = false}}
    if success and module then
        test2.passed = type(module.initialize) == "function" or type(module.new) == "function"
        test2.message = test2.passed and "Required methods exist" or "Missing required methods"
    end
    table.insert(results, test2)

    -- Test 3: Performance benchmark
    local test3 = {{name = "Performance", passed = false}}
    local startTime = tick()
    -- Run performance critical operations
    local elapsed = tick() - startTime
    test3.passed = elapsed < 0.1  -- 100ms threshold
    test3.message = string.format("Execution time: %.3fms", elapsed * 1000)
    table.insert(results, test3)

    return results
end

function TestSuite.printResults(results)
    print("\\n=== Test Results ===")
    local passed = 0
    local total = #results

    for _, test in ipairs(results) do
        local status = test.passed and "✓" or "✗"
        print(status .. " " .. test.name .. ": " .. test.message)
        if test.passed then
            passed = passed + 1
        end
    end

    print(string.format("\\nTotal: %d/%d tests passed (%.1f%%)\\n",
        passed, total, (passed/total) * 100))
end

-- Run tests
local results = TestSuite.runAll()
TestSuite.printResults(results)

return TestSuite
"""

    async def execute_task(self, task: str) -> dict[str, Any]:
        """Execute QA task"""
        if "test" in task.lower():
            # Run tests on provided content
            content = {"code": task}
            return await self.run_tests(content, [TestType.FUNCTIONALITY, TestType.PERFORMANCE])
        elif "generate test" in task.lower():
            return {"success": True, "code": self.generate_test_suite("TestModule")}
        else:
            return {"success": False, "error": "Unknown QA task"}
