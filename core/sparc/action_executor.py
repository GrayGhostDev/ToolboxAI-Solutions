"""
Action Executor - Action Execution Pipeline with Safety and Validation
=====================================================================

The ActionExecutor handles the safe and efficient execution of educational actions:
- Parallel action execution with resource management
- Comprehensive safety checks and validation
- Action rollback and error recovery capabilities
- Real-time monitoring and performance tracking
- Integration with Roblox, LMS, and other external systems

This component ensures that all educational actions are executed safely,
efficiently, and with proper error handling and recovery mechanisms.
"""

import asyncio
import json
import logging
import os
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable, Union, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import deque, defaultdict
import traceback
from pathlib import Path
import aiohttp
import aiofiles

logger = logging.getLogger(__name__)


class ActionStatus(Enum):
    """Status of action execution"""

    PENDING = "pending"
    QUEUED = "queued"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRYING = "retrying"
    ROLLED_BACK = "rolled_back"


class ActionType(Enum):
    """Types of actions that can be executed"""

    ROBLOX_COMMAND = "roblox_command"
    CONTENT_GENERATION = "content_generation"
    QUIZ_CREATION = "quiz_creation"
    LMS_INTERACTION = "lms_interaction"
    FEEDBACK_DELIVERY = "feedback_delivery"
    DIFFICULTY_ADJUSTMENT = "difficulty_adjustment"
    COLLABORATIVE_SETUP = "collaborative_setup"
    ASSESSMENT = "assessment"
    HINT_PROVISION = "hint_provision"
    EXPLORATION_GUIDANCE = "exploration_guidance"


class Priority(Enum):
    """Action priority levels"""

    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4
    EMERGENCY = 5


@dataclass
class Action:
    """Represents an action to be executed"""

    # Core identification
    action_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    type: str = ""
    parameters: Dict[str, Any] = field(default_factory=dict)

    # Execution control
    priority: float = 0.5  # 0-1 priority level
    timeout: float = 30.0  # seconds
    retry_attempts: int = 3

    # Scheduling
    scheduled_time: Optional[datetime] = None
    deadline: Optional[datetime] = None
    dependencies: List[str] = field(default_factory=list)

    # Safety and validation
    safety_checks_required: bool = True
    validation_rules: List[str] = field(default_factory=list)
    rollback_enabled: bool = True

    # Educational context
    student_id: Optional[str] = None
    subject_area: Optional[str] = None
    learning_objective: Optional[str] = None

    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)

    # Status tracking
    status: ActionStatus = ActionStatus.PENDING
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    error_message: Optional[str] = None

    @property
    def execution_time(self) -> Optional[float]:
        """Calculate execution time in seconds"""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return None

    @property
    def is_expired(self) -> bool:
        """Check if action has expired"""
        if self.deadline:
            return datetime.now() > self.deadline
        return False

    @property
    def priority_enum(self) -> Priority:
        """Convert priority float to enum"""
        if self.priority >= 0.9:
            return Priority.EMERGENCY
        elif self.priority >= 0.8:
            return Priority.CRITICAL
        elif self.priority >= 0.6:
            return Priority.HIGH
        elif self.priority >= 0.4:
            return Priority.NORMAL
        else:
            return Priority.LOW

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        result = asdict(self)
        result["status"] = self.status.value
        result["created_at"] = self.created_at.isoformat()
        result["start_time"] = self.start_time.isoformat() if self.start_time else None
        result["end_time"] = self.end_time.isoformat() if self.end_time else None
        result["scheduled_time"] = self.scheduled_time.isoformat() if self.scheduled_time else None
        result["deadline"] = self.deadline.isoformat() if self.deadline else None
        result["execution_time"] = self.execution_time
        result["is_expired"] = self.is_expired
        result["priority_enum"] = self.priority_enum.name
        return result


@dataclass
class ActionResult:
    """Result of action execution"""

    # Core result data
    action_id: str
    success: bool
    result_data: Dict[str, Any] = field(default_factory=dict)

    # Execution details
    execution_time: float = 0.0
    retry_count: int = 0
    final_status: ActionStatus = ActionStatus.COMPLETED

    # Error information
    error_message: Optional[str] = None
    error_type: Optional[str] = None
    stack_trace: Optional[str] = None

    # Educational outcomes
    learning_impact: Optional[Dict[str, Any]] = None
    student_response: Optional[Dict[str, Any]] = None

    # Rollback information
    rollback_data: Optional[Dict[str, Any]] = None
    rollback_possible: bool = True

    # Metadata
    timestamp: datetime = field(default_factory=datetime.now)
    executor_info: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        result = asdict(self)
        result["final_status"] = self.final_status.value
        result["timestamp"] = self.timestamp.isoformat()
        return result


class SafetyChecker:
    """Handles safety validation for actions"""

    def __init__(self):
        self.blocked_commands = {
            "roblox": [
                "game:Shutdown()",
                "workspace:ClearAllChildren()",
                "Players:ClearAllChildren()",
                "require(",  # Prevent arbitrary code execution
                "loadstring(",
                "getfenv(",
                "setfenv(",
            ],
            "system": ["os.execute", "io.popen", 'require("os")', "debug.getregistry"],
        }

        self.max_script_length = 10000
        self.max_content_size = 50000  # 50KB
        self.forbidden_patterns = [
            r"while\s+true\s+do",  # Infinite loops
            r"for\s+.*\s+do\s*end",  # Suspicious loops
            r"spawn\s*\(",  # Uncontrolled spawning
        ]

    async def check_action_safety(self, action: Action) -> Tuple[bool, List[str]]:
        """
        Perform comprehensive safety checks on an action.

        Returns:
            Tuple of (is_safe, list_of_issues)
        """
        issues = []

        # Check action type safety
        if not self._is_action_type_safe(action.type):
            issues.append(f"Action type '{action.type}' is not in allowed list")

        # Check parameter safety
        param_issues = await self._check_parameter_safety(action)
        issues.extend(param_issues)

        # Check resource limits
        resource_issues = self._check_resource_limits(action)
        issues.extend(resource_issues)

        # Check timing constraints
        timing_issues = self._check_timing_safety(action)
        issues.extend(timing_issues)

        # Educational appropriateness
        edu_issues = await self._check_educational_appropriateness(action)
        issues.extend(edu_issues)

        return len(issues) == 0, issues

    def _is_action_type_safe(self, action_type: str) -> bool:
        """Check if action type is in allowed list"""
        allowed_types = [at.value for at in ActionType]
        return action_type in allowed_types

    async def _check_parameter_safety(self, action: Action) -> List[str]:
        """Check safety of action parameters"""
        issues = []

        # Check for blocked commands in Roblox actions
        if "roblox" in action.type.lower():
            for param_name, param_value in action.parameters.items():
                if isinstance(param_value, str):
                    for blocked_cmd in self.blocked_commands["roblox"]:
                        if blocked_cmd.lower() in param_value.lower():
                            issues.append(f"Blocked Roblox command detected: {blocked_cmd}")

        # Check script content if present
        if "script" in action.parameters:
            script = action.parameters["script"]
            if len(script) > self.max_script_length:
                issues.append(f"Script too long: {len(script)} > {self.max_script_length}")

            # Check for dangerous patterns
            import re

            for pattern in self.forbidden_patterns:
                if re.search(pattern, script, re.IGNORECASE):
                    issues.append(f"Dangerous pattern detected: {pattern}")

        # Check content size limits
        total_content_size = len(str(action.parameters))
        if total_content_size > self.max_content_size:
            issues.append(f"Content too large: {total_content_size} > {self.max_content_size}")

        return issues

    def _check_resource_limits(self, action: Action) -> List[str]:
        """Check if action respects resource limits"""
        issues = []

        # Check timeout limits
        if action.timeout > 300:  # 5 minutes max
            issues.append(f"Timeout too long: {action.timeout} > 300 seconds")

        # Check retry limits
        if action.retry_attempts > 5:
            issues.append(f"Too many retry attempts: {action.retry_attempts} > 5")

        return issues

    def _check_timing_safety(self, action: Action) -> List[str]:
        """Check timing-related safety constraints"""
        issues = []

        # Check if deadline is reasonable
        if action.deadline:
            max_future = datetime.now() + timedelta(hours=24)
            if action.deadline > max_future:
                issues.append("Deadline too far in future (>24 hours)")

        # Check scheduled time
        if action.scheduled_time:
            if action.scheduled_time < datetime.now() - timedelta(minutes=5):
                issues.append("Scheduled time is in the past")

        return issues

    async def _check_educational_appropriateness(self, action: Action) -> List[str]:
        """Check if action is educationally appropriate"""
        issues = []

        # Check age-appropriate content
        if action.parameters.get("content"):
            content = str(action.parameters["content"]).lower()
            inappropriate_terms = ["violence", "weapon", "death", "kill", "hate"]
            for term in inappropriate_terms:
                if term in content:
                    issues.append(f"Potentially inappropriate content: contains '{term}'")

        # Check difficulty appropriateness
        if "difficulty" in action.parameters:
            difficulty = action.parameters["difficulty"]
            if isinstance(difficulty, (int, float)) and (difficulty < 0 or difficulty > 1):
                issues.append(f"Invalid difficulty level: {difficulty} (must be 0-1)")

        return issues


class ActionValidator:
    """Validates action parameters and dependencies"""

    def __init__(self):
        self.validation_rules = {
            ActionType.ROBLOX_COMMAND: self._validate_roblox_command,
            ActionType.CONTENT_GENERATION: self._validate_content_generation,
            ActionType.QUIZ_CREATION: self._validate_quiz_creation,
            ActionType.LMS_INTERACTION: self._validate_lms_interaction,
            ActionType.FEEDBACK_DELIVERY: self._validate_feedback_delivery,
        }

    async def validate_action(self, action: Action) -> Tuple[bool, List[str]]:
        """Validate action against type-specific rules"""

        issues = []

        # Basic validation
        if not action.type:
            issues.append("Action type is required")

        if not action.parameters:
            issues.append("Action parameters are required")

        # Type-specific validation
        action_enum = None
        try:
            action_enum = ActionType(action.type)
        except ValueError:
            issues.append(f"Unknown action type: {action.type}")

        if action_enum and action_enum in self.validation_rules:
            type_issues = await self.validation_rules[action_enum](action)
            issues.extend(type_issues)

        return len(issues) == 0, issues

    async def _validate_roblox_command(self, action: Action) -> List[str]:
        """Validate Roblox-specific action"""
        issues = []

        required_params = ["command"]
        for param in required_params:
            if param not in action.parameters:
                issues.append(f"Missing required parameter: {param}")

        if "command" in action.parameters:
            command = action.parameters["command"]
            if not isinstance(command, str):
                issues.append("Command must be a string")
            elif len(command.strip()) == 0:
                issues.append("Command cannot be empty")

        return issues

    async def _validate_content_generation(self, action: Action) -> List[str]:
        """Validate content generation action"""
        issues = []

        required_params = ["content_type", "subject_area"]
        for param in required_params:
            if param not in action.parameters:
                issues.append(f"Missing required parameter: {param}")

        # Validate content type
        if "content_type" in action.parameters:
            valid_types = ["lesson", "quiz", "activity", "tutorial", "challenge"]
            if action.parameters["content_type"] not in valid_types:
                issues.append(f"Invalid content_type: {action.parameters['content_type']}")

        return issues

    async def _validate_quiz_creation(self, action: Action) -> List[str]:
        """Validate quiz creation action"""
        issues = []

        required_params = ["subject_area", "num_questions"]
        for param in required_params:
            if param not in action.parameters:
                issues.append(f"Missing required parameter: {param}")

        # Validate number of questions
        if "num_questions" in action.parameters:
            num_q = action.parameters["num_questions"]
            if not isinstance(num_q, int) or num_q < 1 or num_q > 50:
                issues.append("num_questions must be an integer between 1 and 50")

        return issues

    async def _validate_lms_interaction(self, action: Action) -> List[str]:
        """Validate LMS interaction action"""
        issues = []

        required_params = ["lms_platform", "operation"]
        for param in required_params:
            if param not in action.parameters:
                issues.append(f"Missing required parameter: {param}")

        # Validate LMS platform
        if "lms_platform" in action.parameters:
            valid_platforms = ["schoology", "canvas", "moodle", "blackboard"]
            if action.parameters["lms_platform"].lower() not in valid_platforms:
                issues.append(f"Unsupported LMS platform: {action.parameters['lms_platform']}")

        return issues

    async def _validate_feedback_delivery(self, action: Action) -> List[str]:
        """Validate feedback delivery action"""
        issues = []

        required_params = ["feedback_content", "recipient"]
        for param in required_params:
            if param not in action.parameters:
                issues.append(f"Missing required parameter: {param}")

        # Validate feedback content
        if "feedback_content" in action.parameters:
            content = action.parameters["feedback_content"]
            if not isinstance(content, str) or len(content.strip()) == 0:
                issues.append("Feedback content must be a non-empty string")

        return issues


class ActionExecutor:
    """
    Advanced action execution system with safety, validation, and recovery.

    The ActionExecutor provides comprehensive action execution capabilities
    including parallel processing, safety checks, validation, error recovery,
    and rollback mechanisms for educational actions.
    """

    def __init__(
        self, max_parallel: int = 5, timeout: float = 30.0, retry_attempts: int = 3, safety_checks: bool = True
    ):
        """
        Initialize ActionExecutor.

        Args:
            max_parallel: Maximum number of parallel actions
            timeout: Default timeout for actions
            retry_attempts: Default number of retry attempts
            safety_checks: Whether to perform safety checks
        """
        self.max_parallel = max_parallel
        self.default_timeout = timeout
        self.default_retry_attempts = retry_attempts
        self.safety_checks_enabled = safety_checks

        # Execution infrastructure
        self.executor = ThreadPoolExecutor(max_workers=max_parallel)
        self.action_queue = asyncio.PriorityQueue()
        self.running_actions: Dict[str, asyncio.Task] = {}
        self.completed_actions: deque = deque(maxlen=1000)

        # Safety and validation
        self.safety_checker = SafetyChecker()
        self.validator = ActionValidator()

        # Performance tracking
        self.execution_stats = {
            "total_actions": 0,
            "successful_actions": 0,
            "failed_actions": 0,
            "retried_actions": 0,
            "rolled_back_actions": 0,
            "average_execution_time": 0.0,
            "total_execution_time": 0.0,
        }

        # Action handlers
        self.action_handlers: Dict[str, Callable] = {
            ActionType.ROBLOX_COMMAND.value: self._execute_roblox_command,
            ActionType.CONTENT_GENERATION.value: self._execute_content_generation,
            ActionType.QUIZ_CREATION.value: self._execute_quiz_creation,
            ActionType.LMS_INTERACTION.value: self._execute_lms_interaction,
            ActionType.FEEDBACK_DELIVERY.value: self._execute_feedback_delivery,
            ActionType.DIFFICULTY_ADJUSTMENT.value: self._execute_difficulty_adjustment,
            ActionType.HINT_PROVISION.value: self._execute_hint_provision,
            ActionType.ASSESSMENT.value: self._execute_assessment,
        }

        # Rollback handlers
        self.rollback_handlers: Dict[str, Callable] = {
            ActionType.ROBLOX_COMMAND.value: self._rollback_roblox_command,
            ActionType.CONTENT_GENERATION.value: self._rollback_content_generation,
            ActionType.DIFFICULTY_ADJUSTMENT.value: self._rollback_difficulty_adjustment,
        }

        # External service connections
        self.roblox_api_url = "http://localhost:5001"
        self.content_api_url = "http://localhost:8008"
        self.lms_apis = {"schoology": "https://api.schoology.com", "canvas": "https://canvas.instructure.com/api/v1"}

        # Processing control
        self.processing_active = False
        self.processor_task: Optional[asyncio.Task] = None

        # Persistence - use environment-aware path for Docker compatibility
        data_dir = os.environ.get('DATA_DIR', '/tmp' if os.path.exists('/tmp') else 'data')
        self.persistence_path = Path(data_dir) / "action_executor"
        try:
            self.persistence_path.mkdir(parents=True, exist_ok=True)
        except PermissionError:
            # Fallback to temp directory if permission denied
            self.persistence_path = Path("/tmp/action_executor")
            self.persistence_path.mkdir(parents=True, exist_ok=True)

        logger.info(f"ActionExecutor initialized with max_parallel={max_parallel}")

    async def start_processing(self):
        """Start the action processing loop"""
        if self.processing_active:
            logger.warning("Action processing is already active")
            return

        self.processing_active = True
        self.processor_task = asyncio.create_task(self._process_actions())
        logger.info("Action processing started")

    async def stop_processing(self):
        """Stop the action processing loop"""
        self.processing_active = False

        if self.processor_task:
            self.processor_task.cancel()
            try:
                await self.processor_task
            except asyncio.CancelledError:
                pass

        # Wait for running actions to complete
        if self.running_actions:
            logger.info(f"Waiting for {len(self.running_actions)} running actions to complete")
            await asyncio.gather(*self.running_actions.values(), return_exceptions=True)

        logger.info("Action processing stopped")

    async def execute(self, action: Action) -> ActionResult:
        """
        Execute a single action with full safety and validation.

        Args:
            action: Action to execute

        Returns:
            ActionResult with execution details
        """
        start_time = time.time()

        try:
            # Set default values if not specified
            if not hasattr(action, "timeout") or action.timeout <= 0:
                action.timeout = self.default_timeout
            if not hasattr(action, "retry_attempts"):
                action.retry_attempts = self.default_retry_attempts

            # Perform safety checks
            if self.safety_checks_enabled and action.safety_checks_required:
                safe, safety_issues = await self.safety_checker.check_action_safety(action)
                if not safe:
                    return ActionResult(
                        action_id=action.action_id,
                        success=False,
                        error_message=f"Safety checks failed: {'; '.join(safety_issues)}",
                        error_type="SafetyError",
                        final_status=ActionStatus.FAILED,
                    )

            # Validate action
            valid, validation_issues = await self.validator.validate_action(action)
            if not valid:
                return ActionResult(
                    action_id=action.action_id,
                    success=False,
                    error_message=f"Validation failed: {'; '.join(validation_issues)}",
                    error_type="ValidationError",
                    final_status=ActionStatus.FAILED,
                )

            # Execute with retries
            result = await self._execute_with_retries(action)

            # Update statistics
            execution_time = time.time() - start_time
            self._update_statistics(result, execution_time)

            # Add to completed actions
            self.completed_actions.append(result)

            return result

        except Exception as e:
            logger.error(f"Unexpected error executing action {action.action_id}: {e}")
            execution_time = time.time() - start_time

            error_result = ActionResult(
                action_id=action.action_id,
                success=False,
                execution_time=execution_time,
                error_message=str(e),
                error_type=type(e).__name__,
                stack_trace=traceback.format_exc(),
                final_status=ActionStatus.FAILED,
            )

            self._update_statistics(error_result, execution_time)
            return error_result

    async def queue_action(self, action: Action):
        """Queue an action for processing"""
        # Convert priority to negative for min-heap (higher priority = lower number)
        priority = -action.priority
        await self.action_queue.put((priority, time.time(), action))
        logger.debug(f"Queued action {action.action_id} with priority {action.priority}")

    async def cancel_action(self, action_id: str) -> bool:
        """Cancel a running or queued action"""

        # Check if action is currently running
        if action_id in self.running_actions:
            task = self.running_actions[action_id]
            task.cancel()
            del self.running_actions[action_id]
            logger.info(f"Cancelled running action {action_id}")
            return True

        # For queued actions, we'd need to implement queue scanning
        # This is a simplified version
        logger.warning(f"Action {action_id} not found in running actions")
        return False

    async def rollback_action(self, action_id: str) -> bool:
        """Rollback a completed action if possible"""

        # Find the action in completed actions
        target_action = None
        target_result = None

        for result in self.completed_actions:
            if result.action_id == action_id:
                target_result = result
                break

        if not target_result:
            logger.warning(f"Action {action_id} not found in completed actions")
            return False

        if not target_result.rollback_possible:
            logger.warning(f"Action {action_id} is not rollback-able")
            return False

        # Find rollback handler
        # We need to reconstruct the action type from the result
        action_type = target_result.executor_info.get("action_type")
        if not action_type or action_type not in self.rollback_handlers:
            logger.warning(f"No rollback handler for action type: {action_type}")
            return False

        try:
            rollback_handler = self.rollback_handlers[action_type]
            rollback_success = await rollback_handler(target_result)

            if rollback_success:
                self.execution_stats["rolled_back_actions"] += 1
                logger.info(f"Successfully rolled back action {action_id}")
                return True
            else:
                logger.error(f"Failed to rollback action {action_id}")
                return False

        except Exception as e:
            logger.error(f"Error during rollback of action {action_id}: {e}")
            return False

    async def _process_actions(self):
        """Main action processing loop"""
        logger.info("Starting action processing loop")

        while self.processing_active:
            try:
                # Check if we can process more actions
                if len(self.running_actions) >= self.max_parallel:
                    await asyncio.sleep(0.1)
                    continue

                # Get next action from queue (with timeout to allow checking processing_active)
                try:
                    priority, queued_time, action = await asyncio.wait_for(self.action_queue.get(), timeout=1.0)
                except asyncio.TimeoutError:
                    continue

                # Check if action has expired
                if action.is_expired:
                    logger.warning(f"Action {action.action_id} has expired, skipping")
                    continue

                # Create execution task
                task = asyncio.create_task(self.execute(action))
                self.running_actions[action.action_id] = task

                # Set up task completion callback
                task.add_done_callback(lambda t, aid=action.action_id: self.running_actions.pop(aid, None))

            except Exception as e:
                logger.error(f"Error in action processing loop: {e}")
                await asyncio.sleep(1.0)

        logger.info("Action processing loop ended")

    async def _execute_with_retries(self, action: Action) -> ActionResult:
        """Execute action with retry logic"""

        action.status = ActionStatus.EXECUTING
        action.start_time = datetime.now()

        last_error = None
        retry_count = 0

        for attempt in range(action.retry_attempts + 1):  # +1 for initial attempt
            try:
                # Get action handler
                if action.type not in self.action_handlers:
                    raise ValueError(f"No handler found for action type: {action.type}")

                handler = self.action_handlers[action.type]

                # Execute with timeout
                result_data = await asyncio.wait_for(handler(action), timeout=action.timeout)

                # Success
                action.status = ActionStatus.COMPLETED
                action.end_time = datetime.now()

                return ActionResult(
                    action_id=action.action_id,
                    success=True,
                    result_data=result_data,
                    execution_time=action.execution_time or 0,
                    retry_count=retry_count,
                    final_status=ActionStatus.COMPLETED,
                    executor_info={"action_type": action.type},
                )

            except asyncio.TimeoutError:
                last_error = f"Action timed out after {action.timeout} seconds"
                logger.warning(f"Action {action.action_id} timed out (attempt {attempt + 1})")

            except Exception as e:
                last_error = str(e)
                logger.warning(f"Action {action.action_id} failed (attempt {attempt + 1}): {e}")

            # Retry if not the last attempt
            if attempt < action.retry_attempts:
                action.status = ActionStatus.RETRYING
                retry_count += 1
                # Exponential backoff
                wait_time = min(30, 2**attempt)
                await asyncio.sleep(wait_time)

        # All retries exhausted
        action.status = ActionStatus.FAILED
        action.end_time = datetime.now()

        if retry_count > 0:
            self.execution_stats["retried_actions"] += 1

        return ActionResult(
            action_id=action.action_id,
            success=False,
            execution_time=action.execution_time or 0,
            retry_count=retry_count,
            final_status=ActionStatus.FAILED,
            error_message=last_error,
            error_type="ExecutionError",
            executor_info={"action_type": action.type},
        )

    # Action Handlers

    async def _execute_roblox_command(self, action: Action) -> Dict[str, Any]:
        """Execute Roblox command via API"""

        command = action.parameters.get("command", "")
        target_player = action.parameters.get("target_player")
        game_id = action.parameters.get("game_id")

        # Prepare API request
        payload = {"command": command, "target_player": target_player, "game_id": game_id, "metadata": action.metadata}

        async with aiohttp.ClientSession() as session:
            async with session.post(f"{self.roblox_api_url}/execute_command", json=payload) as response:
                if response.status == 200:
                    result = await response.json()
                    return {"roblox_response": result, "command_executed": command, "execution_successful": True}
                else:
                    error_text = await response.text()
                    raise Exception(f"Roblox API error ({response.status}): {error_text}")

    async def _execute_content_generation(self, action: Action) -> Dict[str, Any]:
        """Execute content generation via AI API"""

        content_type = action.parameters.get("content_type", "lesson")
        subject_area = action.parameters.get("subject_area", "general")
        grade_level = action.parameters.get("grade_level", 5)
        learning_objectives = action.parameters.get("learning_objectives", [])

        payload = {
            "content_type": content_type,
            "subject_area": subject_area,
            "grade_level": grade_level,
            "learning_objectives": learning_objectives,
            "additional_params": {
                k: v
                for k, v in action.parameters.items()
                if k not in ["content_type", "subject_area", "grade_level", "learning_objectives"]
            },
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(f"{self.content_api_url}/generate_content", json=payload) as response:
                if response.status == 200:
                    result = await response.json()
                    return {"generated_content": result, "content_type": content_type, "generation_successful": True}
                else:
                    error_text = await response.text()
                    raise Exception(f"Content API error ({response.status}): {error_text}")

    async def _execute_quiz_creation(self, action: Action) -> Dict[str, Any]:
        """Execute quiz creation"""

        subject_area = action.parameters.get("subject_area", "general")
        num_questions = action.parameters.get("num_questions", 5)
        difficulty = action.parameters.get("difficulty", 0.5)
        question_types = action.parameters.get("question_types", ["multiple_choice"])

        # Use content generation API for quiz creation
        payload = {
            "content_type": "quiz",
            "subject_area": subject_area,
            "num_questions": num_questions,
            "difficulty": difficulty,
            "question_types": question_types,
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(f"{self.content_api_url}/generate_content", json=payload) as response:
                if response.status == 200:
                    result = await response.json()
                    return {
                        "quiz_data": result,
                        "num_questions": num_questions,
                        "quiz_id": str(uuid.uuid4()),
                        "creation_successful": True,
                    }
                else:
                    error_text = await response.text()
                    raise Exception(f"Quiz creation error ({response.status}): {error_text}")

    async def _execute_lms_interaction(self, action: Action) -> Dict[str, Any]:
        """Execute LMS interaction"""

        platform = action.parameters.get("lms_platform", "").lower()
        operation = action.parameters.get("operation", "")
        data = action.parameters.get("data", {})

        if platform not in self.lms_apis:
            raise Exception(f"Unsupported LMS platform: {platform}")

        # This is a simplified implementation
        # In a real system, you'd need proper authentication and API handling

        api_url = self.lms_apis[platform]

        # Mock implementation for demonstration
        await asyncio.sleep(1)  # Simulate API call

        return {
            "lms_platform": platform,
            "operation": operation,
            "interaction_successful": True,
            "response_data": {"status": "completed", "platform": platform},
        }

    async def _execute_feedback_delivery(self, action: Action) -> Dict[str, Any]:
        """Execute feedback delivery"""

        feedback_content = action.parameters.get("feedback_content", "")
        recipient = action.parameters.get("recipient", "")
        delivery_method = action.parameters.get("delivery_method", "roblox_chat")

        if delivery_method == "roblox_chat":
            # Send via Roblox API
            payload = {
                "command": f'game.Players["{recipient}"]:SendSystemMessage("{feedback_content}")',
                "target_player": recipient,
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(f"{self.roblox_api_url}/execute_command", json=payload) as response:
                    if response.status != 200:
                        raise Exception(f"Failed to deliver feedback via Roblox: {response.status}")

        return {
            "feedback_delivered": True,
            "recipient": recipient,
            "delivery_method": delivery_method,
            "content_length": len(feedback_content),
        }

    async def _execute_difficulty_adjustment(self, action: Action) -> Dict[str, Any]:
        """Execute difficulty adjustment"""

        adjustment = action.parameters.get("difficulty_adjustment", 0)
        current_performance = action.parameters.get("current_performance", 0.5)
        target_success_rate = action.parameters.get("target_success_rate", 0.7)

        # Store previous state for potential rollback
        rollback_data = {
            "previous_adjustment": 0,  # This would be retrieved from current state
            "adjustment_timestamp": datetime.now().isoformat(),
        }

        # Apply difficulty adjustment (mock implementation)
        await asyncio.sleep(0.5)  # Simulate processing time

        new_difficulty = max(0.1, min(1.0, 0.5 + adjustment))  # Clamp to valid range

        return {
            "difficulty_adjusted": True,
            "new_difficulty": new_difficulty,
            "adjustment_amount": adjustment,
            "rollback_data": rollback_data,
        }

    async def _execute_hint_provision(self, action: Action) -> Dict[str, Any]:
        """Execute hint provision"""

        hint_level = action.parameters.get("hint_level", 1)
        context_specific = action.parameters.get("context_specific", True)
        student_id = action.student_id

        # Generate contextual hint (mock implementation)
        hints_by_level = {
            1: "Try looking at the problem from a different angle.",
            2: "Consider what you already know about this topic.",
            3: "Here's a specific clue: focus on the key variables.",
        }

        hint_text = hints_by_level.get(hint_level, "Think step by step.")

        # Deliver hint via appropriate method
        if student_id:
            delivery_result = await self._execute_feedback_delivery(
                Action(
                    type=ActionType.FEEDBACK_DELIVERY.value,
                    parameters={
                        "feedback_content": f"Hint: {hint_text}",
                        "recipient": student_id,
                        "delivery_method": "roblox_chat",
                    },
                )
            )

        return {
            "hint_provided": True,
            "hint_level": hint_level,
            "hint_text": hint_text,
            "delivery_successful": delivery_result.get("feedback_delivered", False) if student_id else True,
        }

    async def _execute_assessment(self, action: Action) -> Dict[str, Any]:
        """Execute assessment action"""

        assessment_type = action.parameters.get("assessment_type", "performance_check")
        student_id = action.student_id
        subject_area = action.subject_area

        # Mock assessment implementation
        await asyncio.sleep(1)  # Simulate assessment processing

        # Generate mock assessment results
        assessment_results = {
            "overall_score": 0.75,  # Mock score
            "subject_scores": {"knowledge": 0.8, "application": 0.7, "analysis": 0.6},
            "recommendations": ["Continue practicing problem-solving", "Focus on analytical thinking"],
            "next_steps": ["Advanced challenges", "Peer collaboration"],
        }

        return {
            "assessment_completed": True,
            "assessment_type": assessment_type,
            "results": assessment_results,
            "student_id": student_id,
        }

    # Rollback Handlers

    async def _rollback_roblox_command(self, result: ActionResult) -> bool:
        """Rollback a Roblox command"""

        # This would require storing the previous state and having reverse commands
        logger.warning("Roblox command rollback not implemented")
        return False

    async def _rollback_content_generation(self, result: ActionResult) -> bool:
        """Rollback content generation"""

        # For content generation, rollback might mean removing generated content
        logger.info("Content generation rollback: marking content as inactive")
        return True  # Simplified success

    async def _rollback_difficulty_adjustment(self, result: ActionResult) -> bool:
        """Rollback difficulty adjustment"""

        rollback_data = result.rollback_data
        if not rollback_data:
            return False

        # Restore previous difficulty setting
        previous_adjustment = rollback_data.get("previous_adjustment", 0)

        # Execute reverse adjustment
        reverse_action = Action(
            type=ActionType.DIFFICULTY_ADJUSTMENT.value,
            parameters={"difficulty_adjustment": -previous_adjustment, "rollback_operation": True},
        )

        reverse_result = await self._execute_difficulty_adjustment(reverse_action)
        return reverse_result.get("difficulty_adjusted", False)

    def _update_statistics(self, result: ActionResult, execution_time: float):
        """Update execution statistics"""

        self.execution_stats["total_actions"] += 1
        self.execution_stats["total_execution_time"] += execution_time

        if result.success:
            self.execution_stats["successful_actions"] += 1
        else:
            self.execution_stats["failed_actions"] += 1

        # Update average execution time
        total_actions = self.execution_stats["total_actions"]
        self.execution_stats["average_execution_time"] = self.execution_stats["total_execution_time"] / total_actions

    async def get_status(self) -> Dict[str, Any]:
        """Get comprehensive status of ActionExecutor"""

        return {
            "processing_active": self.processing_active,
            "queue_size": self.action_queue.qsize(),
            "running_actions": len(self.running_actions),
            "max_parallel": self.max_parallel,
            "completed_actions": len(self.completed_actions),
            "statistics": self.execution_stats.copy(),
            "safety_checks_enabled": self.safety_checks_enabled,
            "action_handlers": list(self.action_handlers.keys()),
            "rollback_handlers": list(self.rollback_handlers.keys()),
        }

    async def reset(self):
        """Reset ActionExecutor to initial state"""

        logger.info("Resetting ActionExecutor")

        # Stop processing
        await self.stop_processing()

        # Clear queues and caches
        while not self.action_queue.empty():
            self.action_queue.get_nowait()

        self.running_actions.clear()
        self.completed_actions.clear()

        # Reset statistics
        self.execution_stats = {
            "total_actions": 0,
            "successful_actions": 0,
            "failed_actions": 0,
            "retried_actions": 0,
            "rolled_back_actions": 0,
            "average_execution_time": 0.0,
            "total_execution_time": 0.0,
        }

        logger.info("ActionExecutor reset completed")

    async def __aenter__(self):
        """Async context manager entry"""
        await self.start_processing()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.stop_processing()
        self.executor.shutdown(wait=True)
