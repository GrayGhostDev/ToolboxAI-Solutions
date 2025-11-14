"""Self-Healing Test Agent for automatic test maintenance.

This agent automatically detects and fixes broken tests by:
- Analyzing test failures
- Identifying root causes
- Applying intelligent fixes
- Updating selectors and assertions
- Adapting to UI changes
"""

import difflib
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional

from core.agents.base_agent import BaseAgent
from core.coordinators.error_coordinator import ErrorCoordinator
from core.sparc.state_manager import StateManager

logger = logging.getLogger(__name__)


@dataclass
class TestFailure:
    """Represents a test failure."""

    test_name: str
    test_file: str
    failure_type: str  # assertion, timeout, element_not_found, etc.
    error_message: str
    stack_trace: str
    timestamp: datetime
    line_number: Optional[int] = None
    expected_value: Optional[Any] = None
    actual_value: Optional[Any] = None
    selector: Optional[str] = None


@dataclass
class HealingAction:
    """Represents a healing action to fix a test."""

    action_type: str  # update_selector, fix_assertion, add_wait, etc.
    target: str  # What to fix
    original_value: Any
    new_value: Any
    confidence: float  # 0-1 confidence score
    reasoning: str
    applied: bool = False
    successful: bool = False


@dataclass
class HealingReport:
    """Report of healing actions taken."""

    timestamp: datetime
    total_failures: int
    healed_tests: int
    failed_healings: int
    actions_taken: list[HealingAction]
    success_rate: float
    recommendations: list[str] = field(default_factory=list)


class SelfHealingTestAgent(BaseAgent):
    """
    Agent responsible for automatically fixing broken tests.

    Capabilities:
    - Detect and analyze test failures
    - Identify root causes of failures
    - Apply intelligent fixes
    - Update broken selectors
    - Fix outdated assertions
    - Adapt to UI/API changes
    - Learn from successful fixes
    """

    def __init__(self, name: str = "SelfHealingTestAgent", **kwargs):
        """Initialize the Self-Healing Test Agent."""
        super().__init__(name=name, **kwargs)
        self.state_manager = StateManager()
        self.error_coordinator = ErrorCoordinator()

        # Healing configuration
        self.config = {
            "auto_heal": True,
            "confidence_threshold": 0.7,  # Minimum confidence to apply fix
            "max_retry_attempts": 3,
            "learning_enabled": True,
            "selector_strategies": [
                "id",
                "data-testid",
                "aria-label",
                "text",
                "xpath",
                "css",
            ],
            "common_fixes": {
                "element_not_found": self._fix_element_not_found,
                "assertion_failed": self._fix_assertion_failure,
                "timeout": self._fix_timeout_issue,
                "stale_element": self._fix_stale_element,
                "api_change": self._fix_api_change,
            },
        }

        # Learning database
        self.healing_history: list[HealingAction] = []
        self.successful_patterns: dict[str, list[HealingAction]] = {}

    async def execute_task(self, task: dict[str, Any]) -> dict[str, Any]:
        """Execute self-healing task."""
        try:
            action = task.get("action")

            if action == "heal_test":
                return await self.heal_test(task.get("failure"))
            elif action == "analyze_failures":
                return await self.analyze_test_failures(task.get("failures"))
            elif action == "batch_heal":
                return await self.batch_heal_tests(task.get("test_results"))
            elif action == "update_selectors":
                return await self.update_all_selectors(task.get("test_files"))
            elif action == "adapt_to_changes":
                return await self.adapt_tests_to_changes(task.get("changes"))
            elif action == "generate_report":
                return await self.generate_healing_report()
            else:
                return await self.auto_heal_suite(task.get("test_suite"))

        except Exception as e:
            return await self.handle_error(e, task)

    async def heal_test(self, failure: dict[str, Any]) -> dict[str, Any]:
        """Heal a single test failure."""
        logger.info(f"Attempting to heal test: {failure.get('test_name')}")

        # Parse failure
        test_failure = await self._parse_failure(failure)

        # Analyze root cause
        root_cause = await self._analyze_root_cause(test_failure)

        # Determine healing strategy
        healing_strategy = await self._determine_healing_strategy(test_failure, root_cause)

        # Apply healing actions
        healing_actions = []
        for strategy in healing_strategy:
            action = await self._apply_healing_action(strategy, test_failure)
            healing_actions.append(action)

            # Test if fix worked
            if await self._verify_healing(test_failure, action):
                action.successful = True
                await self._learn_from_success(test_failure, action)
                break

        # Generate fix code
        fix_code = await self._generate_fix_code(test_failure, healing_actions)

        return {
            "status": "success" if any(a.successful for a in healing_actions) else "failed",
            "test": test_failure.test_name,
            "root_cause": root_cause,
            "healing_actions": [self._serialize_action(a) for a in healing_actions],
            "fix_code": fix_code,
            "confidence": max(a.confidence for a in healing_actions) if healing_actions else 0,
            "recommendations": await self._generate_recommendations(test_failure, healing_actions),
        }

    async def analyze_test_failures(self, failures: list[dict[str, Any]]) -> dict[str, Any]:
        """Analyze multiple test failures to identify patterns."""
        logger.info(f"Analyzing {len(failures)} test failures")

        failure_patterns = {
            "selector_issues": [],
            "assertion_changes": [],
            "timing_problems": [],
            "api_changes": [],
            "data_issues": [],
            "environment_issues": [],
        }

        # Categorize failures
        for failure in failures:
            test_failure = await self._parse_failure(failure)
            category = await self._categorize_failure(test_failure)

            if "selector" in category:
                failure_patterns["selector_issues"].append(test_failure)
            elif "assertion" in category:
                failure_patterns["assertion_changes"].append(test_failure)
            elif "timeout" in category:
                failure_patterns["timing_problems"].append(test_failure)
            elif "api" in category:
                failure_patterns["api_changes"].append(test_failure)
            elif "data" in category:
                failure_patterns["data_issues"].append(test_failure)
            else:
                failure_patterns["environment_issues"].append(test_failure)

        # Find common patterns
        common_patterns = await self._identify_common_patterns(failure_patterns)

        # Generate bulk fixes
        bulk_fixes = await self._generate_bulk_fixes(common_patterns)

        return {
            "status": "success",
            "total_failures": len(failures),
            "failure_patterns": {k: len(v) for k, v in failure_patterns.items()},
            "common_patterns": common_patterns,
            "bulk_fixes": bulk_fixes,
            "priority_fixes": await self._prioritize_fixes(failure_patterns),
            "estimated_healing_time": await self._estimate_healing_time(failure_patterns),
        }

    async def batch_heal_tests(self, test_results: dict[str, Any]) -> dict[str, Any]:
        """Batch heal multiple test failures."""
        logger.info("Starting batch healing process")

        healing_report = HealingReport(
            timestamp=datetime.now(),
            total_failures=0,
            healed_tests=0,
            failed_healings=0,
            actions_taken=[],
            success_rate=0.0,
        )

        # Extract failures from test results
        failures = await self._extract_failures(test_results)
        healing_report.total_failures = len(failures)

        # Group similar failures
        failure_groups = await self._group_similar_failures(failures)

        # Heal each group
        for group_type, group_failures in failure_groups.items():
            logger.info(f"Healing {len(group_failures)} {group_type} failures")

            # Apply group healing strategy
            group_actions = await self._heal_failure_group(group_type, group_failures)
            healing_report.actions_taken.extend(group_actions)

            # Count successes
            successful = sum(1 for a in group_actions if a.successful)
            healing_report.healed_tests += successful
            healing_report.failed_healings += len(group_actions) - successful

        # Calculate success rate
        if healing_report.total_failures > 0:
            healing_report.success_rate = (
                healing_report.healed_tests / healing_report.total_failures
            )

        # Generate recommendations
        healing_report.recommendations = await self._generate_batch_recommendations(healing_report)

        return {
            "status": "success",
            "healing_report": self._serialize_report(healing_report),
            "healed_files": await self._get_healed_files(healing_report),
            "remaining_failures": healing_report.total_failures - healing_report.healed_tests,
            "next_steps": await self._suggest_next_steps(healing_report),
        }

    async def update_all_selectors(self, test_files: list[str]) -> dict[str, Any]:
        """Update all selectors in test files to be more robust."""
        logger.info(f"Updating selectors in {len(test_files)} test files")

        updates = {
            "total_selectors": 0,
            "updated_selectors": 0,
            "improved_selectors": [],
            "files_modified": [],
        }

        for test_file in test_files:
            # Parse test file
            selectors = await self._extract_selectors(test_file)
            updates["total_selectors"] += len(selectors)

            # Improve each selector
            for selector in selectors:
                improved = await self._improve_selector(selector)

                if improved != selector:
                    updates["updated_selectors"] += 1
                    updates["improved_selectors"].append(
                        {
                            "file": test_file,
                            "original": selector,
                            "improved": improved,
                            "strategy": await self._get_selector_strategy(improved),
                        }
                    )

                    # Apply update to file
                    await self._update_selector_in_file(test_file, selector, improved)
                    if test_file not in updates["files_modified"]:
                        updates["files_modified"].append(test_file)

        return {
            "status": "success",
            "updates": updates,
            "improvement_rate": (
                updates["updated_selectors"] / updates["total_selectors"]
                if updates["total_selectors"] > 0
                else 0
            ),
            "recommendations": await self._generate_selector_recommendations(updates),
        }

    async def adapt_tests_to_changes(self, changes: dict[str, Any]) -> dict[str, Any]:
        """Adapt tests to application changes."""
        logger.info("Adapting tests to application changes")

        adaptations = {
            "ui_changes": [],
            "api_changes": [],
            "data_changes": [],
            "workflow_changes": [],
        }

        # Analyze changes
        change_analysis = await self._analyze_changes(changes)

        # Adapt to UI changes
        if change_analysis.get("ui_changes"):
            ui_adaptations = await self._adapt_to_ui_changes(change_analysis["ui_changes"])
            adaptations["ui_changes"] = ui_adaptations

        # Adapt to API changes
        if change_analysis.get("api_changes"):
            api_adaptations = await self._adapt_to_api_changes(change_analysis["api_changes"])
            adaptations["api_changes"] = api_adaptations

        # Adapt to data changes
        if change_analysis.get("data_changes"):
            data_adaptations = await self._adapt_to_data_changes(change_analysis["data_changes"])
            adaptations["data_changes"] = data_adaptations

        # Adapt to workflow changes
        if change_analysis.get("workflow_changes"):
            workflow_adaptations = await self._adapt_to_workflow_changes(
                change_analysis["workflow_changes"]
            )
            adaptations["workflow_changes"] = workflow_adaptations

        # Apply adaptations
        applied_adaptations = await self._apply_adaptations(adaptations)

        return {
            "status": "success",
            "changes_detected": change_analysis,
            "adaptations": adaptations,
            "applied_adaptations": applied_adaptations,
            "tests_affected": await self._count_affected_tests(adaptations),
            "validation_results": await self._validate_adaptations(applied_adaptations),
        }

    async def auto_heal_suite(self, test_suite: str) -> dict[str, Any]:
        """Automatically heal an entire test suite."""
        logger.info(f"Auto-healing test suite: {test_suite}")

        # Run tests to identify failures
        test_results = await self._run_test_suite(test_suite)

        # Extract and categorize failures
        failures = await self._extract_failures(test_results)

        if not failures:
            return {
                "status": "success",
                "message": "No failures detected",
                "test_suite": test_suite,
            }

        # Create healing plan
        healing_plan = await self._create_healing_plan(failures)

        # Execute healing plan
        healing_results = []
        for step in healing_plan["steps"]:
            result = await self._execute_healing_step(step)
            healing_results.append(result)

            # Re-run affected tests
            if result["successful"]:
                verification = await self._verify_healing_step(step, result)
                result["verified"] = verification

        # Generate comprehensive report
        final_report = await self._generate_final_healing_report(
            test_suite, failures, healing_plan, healing_results
        )

        # Learn from healing process
        if self.config["learning_enabled"]:
            await self._learn_from_healing_process(healing_results)

        return {
            "status": "success",
            "test_suite": test_suite,
            "initial_failures": len(failures),
            "healed_tests": sum(1 for r in healing_results if r["successful"]),
            "healing_plan": healing_plan,
            "healing_results": healing_results,
            "final_report": final_report,
            "success_rate": (
                sum(1 for r in healing_results if r["successful"]) / len(failures)
                if failures
                else 0
            ),
        }

    async def _fix_element_not_found(self, failure: TestFailure) -> HealingAction:
        """Fix element not found errors."""
        # Try alternative selectors
        alternatives = await self._generate_alternative_selectors(failure.selector)

        for alt_selector in alternatives:
            if await self._validate_selector(alt_selector):
                return HealingAction(
                    action_type="update_selector",
                    target=failure.selector,
                    original_value=failure.selector,
                    new_value=alt_selector,
                    confidence=0.85,
                    reasoning=f"Found working alternative selector: {alt_selector}",
                )

        # Try adding wait
        return HealingAction(
            action_type="add_wait",
            target=failure.selector,
            original_value=failure.selector,
            new_value=f"await page.waitForSelector('{failure.selector}', {{timeout: 10000}})",
            confidence=0.6,
            reasoning="Element might need more time to appear",
        )

    async def _fix_assertion_failure(self, failure: TestFailure) -> HealingAction:
        """Fix assertion failures."""
        # Analyze expected vs actual
        if failure.expected_value and failure.actual_value:
            # Check if it's a minor difference
            if isinstance(failure.expected_value, str) and isinstance(failure.actual_value, str):
                similarity = difflib.SequenceMatcher(
                    None, failure.expected_value, failure.actual_value
                ).ratio()

                if similarity > 0.8:  # Minor difference
                    return HealingAction(
                        action_type="update_assertion",
                        target="assertion",
                        original_value=failure.expected_value,
                        new_value=failure.actual_value,
                        confidence=similarity,
                        reasoning=f"Minor text change detected (similarity: {similarity:.2f})",
                    )

        # Check for regex pattern
        return HealingAction(
            action_type="use_pattern_matching",
            target="assertion",
            original_value=failure.expected_value,
            new_value=f"expect({failure.actual_value}).toMatch(/{failure.expected_value}/i)",
            confidence=0.7,
            reasoning="Using pattern matching for flexible assertion",
        )

    async def _fix_timeout_issue(self, failure: TestFailure) -> HealingAction:
        """Fix timeout issues."""
        return HealingAction(
            action_type="increase_timeout",
            target="timeout",
            original_value="5000",
            new_value="15000",
            confidence=0.75,
            reasoning="Increasing timeout to handle slower responses",
        )

    async def _fix_stale_element(self, failure: TestFailure) -> HealingAction:
        """Fix stale element reference errors."""
        return HealingAction(
            action_type="refetch_element",
            target=failure.selector,
            original_value=failure.selector,
            new_value=f"await page.locator('{failure.selector}').first()",
            confidence=0.8,
            reasoning="Re-fetching element to avoid stale reference",
        )

    async def _fix_api_change(self, failure: TestFailure) -> HealingAction:
        """Fix API change related failures."""
        return HealingAction(
            action_type="update_api_schema",
            target="api_response",
            original_value=failure.expected_value,
            new_value=failure.actual_value,
            confidence=0.65,
            reasoning="API response structure has changed",
        )

    def _serialize_action(self, action: HealingAction) -> dict[str, Any]:
        """Serialize healing action."""
        return {
            "action_type": action.action_type,
            "target": action.target,
            "original_value": str(action.original_value),
            "new_value": str(action.new_value),
            "confidence": action.confidence,
            "reasoning": action.reasoning,
            "applied": action.applied,
            "successful": action.successful,
        }

    def _serialize_report(self, report: HealingReport) -> dict[str, Any]:
        """Serialize healing report."""
        return {
            "timestamp": report.timestamp.isoformat(),
            "total_failures": report.total_failures,
            "healed_tests": report.healed_tests,
            "failed_healings": report.failed_healings,
            "actions_taken": [self._serialize_action(a) for a in report.actions_taken],
            "success_rate": report.success_rate,
            "recommendations": report.recommendations,
        }

    # Additional helper methods would continue here...
