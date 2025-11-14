"""
Task Distributor - Intelligent task distribution and scheduling system.

This module provides advanced task distribution capabilities including priority
scheduling, dependency management, load-aware distribution, and educational
content optimization with failure detection and retry mechanisms.
"""

import asyncio
import heapq
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Optional

logger = logging.getLogger(__name__)


class TaskPriority(Enum):
    """Enumeration of task priority levels."""

    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4
    URGENT = 5


class TaskStatus(Enum):
    """Enumeration of possible task states."""

    PENDING = "pending"
    QUEUED = "queued"
    ASSIGNED = "assigned"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRYING = "retrying"


class TaskType(Enum):
    """Enumeration of educational task types."""

    CONTENT_GENERATION = "content_generation"
    QUIZ_CREATION = "quiz_creation"
    TERRAIN_GENERATION = "terrain_generation"
    SCRIPT_OPTIMIZATION = "script_optimization"
    QUALITY_REVIEW = "quality_review"
    LMS_INTEGRATION = "lms_integration"
    CURRICULUM_ALIGNMENT = "curriculum_alignment"
    ASSESSMENT_ANALYSIS = "assessment_analysis"


@dataclass
class TaskDependency:
    """Represents a dependency relationship between tasks."""

    task_id: str
    dependency_type: str = "completion"  # completion, data, resource
    required_result: Optional[Any] = None


@dataclass
class Task:
    """Represents a task in the distributed system with educational enhancements."""

    task_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    task_type: str = "generic"
    task_data: dict[str, Any] = field(default_factory=dict)
    priority: TaskPriority = TaskPriority.NORMAL
    status: TaskStatus = TaskStatus.PENDING

    # Timing and lifecycle
    created_at: datetime = field(default_factory=datetime.now)
    scheduled_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    timeout: int = 300  # seconds

    # Dependencies and relationships
    dependencies: list[TaskDependency] = field(default_factory=list)
    dependent_tasks: set[str] = field(default_factory=set)
    parent_task_id: Optional[str] = None
    child_task_ids: set[str] = field(default_factory=set)

    # Execution context
    assigned_worker_id: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    retry_delay: float = 5.0  # seconds

    # Results and errors
    result: Optional[Any] = None
    error: Optional[Exception] = None
    execution_time: float = 0.0

    # Educational context
    educational_context: dict[str, Any] = field(default_factory=dict)
    requires_consensus: bool = False
    curriculum_standards: list[str] = field(default_factory=list)
    learning_objectives: list[str] = field(default_factory=list)
    target_grade_levels: list[int] = field(default_factory=list)

    # Callback functions
    on_completion: Optional[Callable] = None
    on_failure: Optional[Callable] = None
    on_retry: Optional[Callable] = None

    def __lt__(self, other):
        """Support for priority queue operations."""
        if not isinstance(other, Task):
            return NotImplemented

        # Higher priority values come first
        if self.priority.value != other.priority.value:
            return self.priority.value > other.priority.value

        # Earlier created tasks come first for same priority
        return self.created_at < other.created_at

    def get_age(self) -> float:
        """Get the age of the task in seconds."""
        return (datetime.now() - self.created_at).total_seconds()

    def is_expired(self) -> bool:
        """Check if the task has exceeded its timeout."""
        if not self.started_at:
            return False
        return (datetime.now() - self.started_at).total_seconds() > self.timeout

    def can_execute(self, completed_tasks: set[str]) -> bool:
        """Check if all dependencies are satisfied."""
        for dependency in self.dependencies:
            if dependency.task_id not in completed_tasks:
                return False
        return True

    def set_result(self, result: Any):
        """Set the task result and update status."""
        self.result = result
        self.status = TaskStatus.COMPLETED
        self.completed_at = datetime.now()
        if self.started_at:
            self.execution_time = (self.completed_at - self.started_at).total_seconds()

    def set_error(self, error: Exception):
        """Set task error and determine if retry is needed."""
        self.error = error

        if self.retry_count < self.max_retries:
            self.status = TaskStatus.RETRYING
            self.retry_count += 1
        else:
            self.status = TaskStatus.FAILED
            self.completed_at = datetime.now()

    def to_dict(self) -> dict[str, Any]:
        """Convert task to dictionary representation."""
        return {
            "task_id": self.task_id,
            "task_type": self.task_type,
            "priority": self.priority.value,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": (self.completed_at.isoformat() if self.completed_at else None),
            "execution_time": self.execution_time,
            "retry_count": self.retry_count,
            "assigned_worker_id": self.assigned_worker_id,
            "educational_context": self.educational_context,
            "curriculum_standards": self.curriculum_standards,
            "learning_objectives": self.learning_objectives,
            "target_grade_levels": self.target_grade_levels,
        }


@dataclass
class SchedulingPolicy:
    """Configuration for task scheduling behavior."""

    algorithm: str = "priority_fair"  # priority, fifo, fair, priority_fair
    enable_load_balancing: bool = True
    enable_dependency_resolution: bool = True
    enable_educational_optimization: bool = True
    max_queue_size: int = 1000
    starvation_prevention: bool = True
    age_factor_weight: float = 0.1
    load_factor_weight: float = 0.3
    capability_factor_weight: float = 0.6


@dataclass
class DistributorConfig:
    """Configuration for the TaskDistributor."""

    timeout: int = 300
    max_queue_size: int = 1000
    scheduling_policy: Optional[SchedulingPolicy] = None
    max_worker_load: float = 0.8
    task_retry_enabled: bool = True
    max_retries: int = 3
    retry_delay: float = 5.0

    # Educational optimization settings
    enable_subject_prioritization: bool = True
    enable_grade_level_optimization: bool = True
    curriculum_alignment_weight: float = 0.3

    # Performance settings
    background_monitoring_enabled: bool = True
    cleanup_interval: int = 300  # seconds
    health_check_interval: int = 30  # seconds
    metrics_retention_hours: int = 24

    # Task distribution settings
    load_balancing_algorithm: str = "weighted_round_robin"
    enable_task_affinity: bool = True
    worker_selection_strategy: str = "capability_load_balanced"

    def __post_init__(self):
        """Initialize scheduling policy if not provided."""
        if self.scheduling_policy is None:
            self.scheduling_policy = SchedulingPolicy()


class TaskDistributor:
    """
    Intelligent task distribution and scheduling system optimized for
    educational content generation with advanced dependency management,
    load-aware distribution, and failure recovery mechanisms.
    """

    def __init__(
        self,
        config: Optional[DistributorConfig] = None,
        timeout: int = 300,
        max_queue_size: int = 1000,
        scheduling_policy: Optional[SchedulingPolicy] = None,
    ):
        # Support both config object and individual parameters for backward compatibility
        if config is not None:
            self.config = config
            self.timeout = config.timeout
            self.max_queue_size = config.max_queue_size
            self.policy = config.scheduling_policy
        else:
            self.config = DistributorConfig(
                timeout=timeout,
                max_queue_size=max_queue_size,
                scheduling_policy=scheduling_policy,
            )
            self.timeout = timeout
            self.max_queue_size = max_queue_size
            self.policy = scheduling_policy or SchedulingPolicy()

        # Task storage and queuing
        self.tasks: dict[str, Task] = {}
        self.priority_queue: list[Task] = []  # Heap-based priority queue
        self.dependency_graph: dict[str, set[str]] = {}  # task_id -> dependent_task_ids
        self.completed_tasks: set[str] = set()
        self.failed_tasks: set[str] = set()

        # Execution tracking
        self.running_tasks: dict[str, Task] = {}
        self.task_completion_events: dict[str, asyncio.Event] = {}
        self.task_results: dict[str, Any] = {}

        # Educational optimization
        self.subject_task_queues: dict[str, list[Task]] = {}
        self.grade_level_task_queues: dict[int, list[Task]] = {}
        self.curriculum_task_mapping: dict[str, list[str]] = {}  # standard -> task_ids

        # Load balancing and monitoring
        self.worker_load_history: dict[str, list[float]] = {}
        self.task_execution_history: list[dict[str, Any]] = []

        # Background tasks
        self._scheduler_task: Optional[asyncio.Task] = None
        self._monitor_task: Optional[asyncio.Task] = None
        self._cleanup_task: Optional[asyncio.Task] = None

        # Metrics and statistics
        self.metrics = {
            "tasks_submitted": 0,
            "tasks_completed": 0,
            "tasks_failed": 0,
            "tasks_retried": 0,
            "average_queue_time": 0.0,
            "average_execution_time": 0.0,
            "throughput_per_minute": 0.0,
            "dependency_resolution_time": 0.0,
        }

        logger.info(f"TaskDistributor initialized with policy: {self.policy.algorithm}")

    async def initialize(self):
        """Initialize the task distributor and start background processes."""
        try:
            # Start background tasks
            self._scheduler_task = asyncio.create_task(self._scheduling_loop())
            self._monitor_task = asyncio.create_task(self._monitoring_loop())
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())

            logger.info("TaskDistributor initialized successfully")

        except (ValueError, TypeError, RuntimeError, AttributeError) as e:
            logger.error(f"Failed to initialize TaskDistributor: {e}")
            raise

    async def shutdown(self):
        """Gracefully shutdown the task distributor."""
        try:
            # Cancel background tasks
            background_tasks = [
                self._scheduler_task,
                self._monitor_task,
                self._cleanup_task,
            ]

            for task in background_tasks:
                if task and not task.done():
                    task.cancel()
                    try:
                        await task
                    except asyncio.CancelledError:
                        pass

            # Complete any remaining tasks
            if self.running_tasks:
                logger.info(f"Waiting for {len(self.running_tasks)} running tasks to complete...")
                try:
                    await asyncio.wait_for(self._wait_for_running_tasks(), timeout=30.0)
                except asyncio.TimeoutError:
                    logger.warning("Timeout waiting for running tasks to complete")

            # Clear all data structures
            self.tasks.clear()
            self.priority_queue.clear()
            self.dependency_graph.clear()
            self.running_tasks.clear()
            self.task_completion_events.clear()

            logger.info("TaskDistributor shutdown completed")

        except (ValueError, TypeError, RuntimeError, asyncio.CancelledError) as e:
            logger.error(f"Error during TaskDistributor shutdown: {e}")

    async def submit_task(
        self,
        task_type: str,
        task_data: dict[str, Any],
        priority: TaskPriority = TaskPriority.NORMAL,
        dependencies: Optional[list[str]] = None,
        educational_context: Optional[dict[str, Any]] = None,
        timeout: Optional[int] = None,
        on_completion: Optional[Callable] = None,
        on_failure: Optional[Callable] = None,
    ) -> str:
        """
        Submit a new task for execution.

        Args:
            task_type: Type of task to execute
            task_data: Task-specific data and parameters
            priority: Task priority level
            dependencies: List of task IDs this task depends on
            educational_context: Educational metadata and context
            timeout: Custom timeout for this task
            on_completion: Callback for task completion
            on_failure: Callback for task failure

        Returns:
            Task ID for tracking and retrieval
        """
        if len(self.priority_queue) >= self.max_queue_size:
            raise RuntimeError(f"Task queue is full (max: {self.max_queue_size})")

        # Create task
        task = Task(
            task_type=task_type,
            task_data=task_data,
            priority=priority,
            educational_context=educational_context or {},
            timeout=timeout or self.timeout,
            on_completion=on_completion,
            on_failure=on_failure,
        )

        # Set up dependencies
        if dependencies:
            for dep_task_id in dependencies:
                task.dependencies.append(TaskDependency(task_id=dep_task_id))

                # Update dependency graph
                if dep_task_id not in self.dependency_graph:
                    self.dependency_graph[dep_task_id] = set()
                self.dependency_graph[dep_task_id].add(task.task_id)

        # Apply educational optimizations
        if self.policy.enable_educational_optimization:
            await self._apply_educational_optimizations(task)

        # Store task
        self.tasks[task.task_id] = task
        self.task_completion_events[task.task_id] = asyncio.Event()

        # Add to appropriate queues
        await self._enqueue_task(task)

        # Update metrics
        self.metrics["tasks_submitted"] += 1

        logger.info(f"Task {task.task_id} submitted: {task_type} (priority: {priority.name})")
        return task.task_id

    async def submit_task_object(self, task: Task) -> str:
        """Submit an already constructed task object."""
        if len(self.priority_queue) >= self.max_queue_size:
            raise RuntimeError(f"Task queue is full (max: {self.max_queue_size})")

        # Apply educational optimizations
        if self.policy.enable_educational_optimization:
            await self._apply_educational_optimizations(task)

        # Store task
        self.tasks[task.task_id] = task
        self.task_completion_events[task.task_id] = asyncio.Event()

        # Set up dependency graph
        for dep in task.dependencies:
            if dep.task_id not in self.dependency_graph:
                self.dependency_graph[dep.task_id] = set()
            self.dependency_graph[dep.task_id].add(task.task_id)

        # Add to appropriate queues
        await self._enqueue_task(task)

        # Update metrics
        self.metrics["tasks_submitted"] += 1

        logger.info(f"Task object {task.task_id} submitted: {task.task_type}")
        return task.task_id

    async def get_next_task(
        self, worker_capabilities: Optional[list[str]] = None
    ) -> Optional[Task]:
        """
        Get the next task for execution based on scheduling policy.

        Args:
            worker_capabilities: List of worker capabilities for task matching

        Returns:
            Next task to execute or None if no suitable tasks available
        """
        if not self.priority_queue:
            return None

        # Find next executable task
        suitable_tasks = []

        for i, task in enumerate(self.priority_queue):
            # Check dependencies
            if not task.can_execute(self.completed_tasks):
                continue

            # Check worker capabilities
            if worker_capabilities and not self._worker_can_handle_task(worker_capabilities, task):
                continue

            suitable_tasks.append((i, task))

        if not suitable_tasks:
            return None

        # Select best task based on scheduling policy
        selected_index, selected_task = await self._select_task_by_policy(suitable_tasks)

        # Remove from queue and update status
        del self.priority_queue[selected_index]
        heapq.heapify(self.priority_queue)  # Re-heapify after deletion

        selected_task.status = TaskStatus.ASSIGNED
        selected_task.scheduled_at = datetime.now()

        # Remove from specialized queues
        await self._dequeue_task(selected_task)

        logger.info(f"Selected task {selected_task.task_id} for execution")
        return selected_task

    async def mark_task_started(self, task_id: str, worker_id: str):
        """Mark a task as started by a specific worker."""
        if task_id not in self.tasks:
            logger.warning(f"Attempted to start unknown task: {task_id}")
            return

        task = self.tasks[task_id]
        task.status = TaskStatus.RUNNING
        task.started_at = datetime.now()
        task.assigned_worker_id = worker_id

        self.running_tasks[task_id] = task

        logger.info(f"Task {task_id} started by worker {worker_id}")

    async def mark_task_completed(self, task_id: str, result: Any):
        """Mark a task as completed with result."""
        if task_id not in self.tasks:
            logger.warning(f"Attempted to complete unknown task: {task_id}")
            return

        task = self.tasks[task_id]
        task.set_result(result)

        # Move from running to completed
        self.running_tasks.pop(task_id, None)
        self.completed_tasks.add(task_id)
        self.task_results[task_id] = result

        # Signal completion
        if task_id in self.task_completion_events:
            self.task_completion_events[task_id].set()

        # Execute completion callback
        if task.on_completion:
            try:
                if asyncio.iscoroutinefunction(task.on_completion):
                    await task.on_completion(task_id, result)
                else:
                    task.on_completion(task_id, result)
            except (ValueError, TypeError, RuntimeError, AttributeError) as e:
                logger.error(f"Error in completion callback for task {task_id}: {e}")

        # Process dependent tasks
        await self._process_dependent_tasks(task_id)

        # Update metrics
        self.metrics["tasks_completed"] += 1
        if task.scheduled_at:
            queue_time = (task.started_at - task.scheduled_at).total_seconds()
            self._update_average_metric("average_queue_time", queue_time)
        self._update_average_metric("average_execution_time", task.execution_time)

        logger.info(f"Task {task_id} completed in {task.execution_time:.2f}s")

    async def mark_task_failed(self, task_id: str, error: Exception):
        """Mark a task as failed with error information."""
        if task_id not in self.tasks:
            logger.warning(f"Attempted to fail unknown task: {task_id}")
            return

        task = self.tasks[task_id]
        task.set_error(error)

        # Handle retry or final failure
        if task.status == TaskStatus.RETRYING:
            logger.info(f"Task {task_id} will be retried (attempt {task.retry_count})")

            # Re-queue for retry after delay
            asyncio.create_task(self._schedule_retry(task))
            self.metrics["tasks_retried"] += 1

        else:
            # Final failure
            self.running_tasks.pop(task_id, None)
            self.failed_tasks.add(task_id)

            # Signal completion (with failure)
            if task_id in self.task_completion_events:
                self.task_completion_events[task_id].set()

            # Execute failure callback
            if task.on_failure:
                try:
                    if asyncio.iscoroutinefunction(task.on_failure):
                        await task.on_failure(task_id, error)
                    else:
                        task.on_failure(task_id, error)
                except (ValueError, TypeError, RuntimeError, AttributeError) as e:
                    logger.error(f"Error in failure callback for task {task_id}: {e}")

            # Update metrics
            self.metrics["tasks_failed"] += 1

            logger.error(f"Task {task_id} failed permanently: {error}")

    async def wait_for_completion(self, task_id: str, timeout: Optional[float] = None) -> Any:
        """
        Wait for a task to complete and return its result.

        Args:
            task_id: ID of the task to wait for
            timeout: Maximum time to wait (uses task timeout if not specified)

        Returns:
            Task result

        Raises:
            asyncio.TimeoutError: If task doesn't complete within timeout
            RuntimeError: If task failed
        """
        if task_id not in self.tasks:
            raise ValueError(f"Unknown task ID: {task_id}")

        task = self.tasks[task_id]

        # Return immediately if already completed
        if task.status == TaskStatus.COMPLETED:
            return task.result
        elif task.status == TaskStatus.FAILED:
            raise RuntimeError(f"Task {task_id} failed: {task.error}")

        # Wait for completion
        completion_timeout = timeout or task.timeout

        try:
            await asyncio.wait_for(
                self.task_completion_events[task_id].wait(), timeout=completion_timeout
            )
        except asyncio.TimeoutError:
            logger.error(f"Task {task_id} timed out after {completion_timeout}s")
            raise

        # Check final status
        if task.status == TaskStatus.COMPLETED:
            return task.result
        elif task.status == TaskStatus.FAILED:
            raise RuntimeError(f"Task {task_id} failed: {task.error}")
        else:
            raise RuntimeError(f"Task {task_id} in unexpected state: {task.status}")

    async def cancel_task(self, task_id: str) -> bool:
        """Cancel a pending or running task."""
        if task_id not in self.tasks:
            return False

        task = self.tasks[task_id]

        if task.status in [
            TaskStatus.COMPLETED,
            TaskStatus.FAILED,
            TaskStatus.CANCELLED,
        ]:
            return False

        # Remove from queues
        if task.status in [TaskStatus.PENDING, TaskStatus.QUEUED]:
            await self._remove_from_queues(task)

        task.status = TaskStatus.CANCELLED
        task.completed_at = datetime.now()

        # Clean up
        self.running_tasks.pop(task_id, None)

        # Signal completion
        if task_id in self.task_completion_events:
            self.task_completion_events[task_id].set()

        logger.info(f"Task {task_id} cancelled")
        return True

    async def get_task_status(self, task_id: str) -> Optional[dict[str, Any]]:
        """Get comprehensive status information for a task."""
        if task_id not in self.tasks:
            return None

        task = self.tasks[task_id]
        return task.to_dict()

    async def get_queue_size(self) -> int:
        """Get the current number of queued tasks."""
        return len(self.priority_queue)

    async def get_status(self) -> dict[str, Any]:
        """Get comprehensive status of the task distributor."""
        return {
            "queue_size": len(self.priority_queue),
            "running_tasks": len(self.running_tasks),
            "completed_tasks": len(self.completed_tasks),
            "failed_tasks": len(self.failed_tasks),
            "total_tasks": len(self.tasks),
            "metrics": self.metrics.copy(),
            "scheduling_policy": {
                "algorithm": self.policy.algorithm,
                "load_balancing": self.policy.enable_load_balancing,
                "educational_optimization": self.policy.enable_educational_optimization,
            },
            "subject_queues": {
                subject: len(tasks) for subject, tasks in self.subject_task_queues.items()
            },
            "grade_level_queues": {
                level: len(tasks) for level, tasks in self.grade_level_task_queues.items()
            },
        }

    async def check_stalled_tasks(self) -> list[str]:
        """Check for tasks that have stalled and may need intervention."""
        stalled_tasks = []
        datetime.now()

        for task_id, task in self.running_tasks.items():
            if task.is_expired():
                stalled_tasks.append(task_id)
                logger.warning(
                    f"Task {task_id} has stalled (running for {task.execution_time:.2f}s)"
                )

        return stalled_tasks

    async def retry_task(self, task_id: str) -> bool:
        """Manually retry a failed or stalled task."""
        if task_id not in self.tasks:
            return False

        task = self.tasks[task_id]

        if task.retry_count >= task.max_retries:
            logger.warning(f"Task {task_id} has exceeded maximum retries")
            return False

        # Reset task for retry
        task.status = TaskStatus.PENDING
        task.started_at = None
        task.error = None
        task.retry_count += 1
        task.assigned_worker_id = None

        # Re-queue task
        await self._enqueue_task(task)

        # Remove from running tasks
        self.running_tasks.pop(task_id, None)

        logger.info(f"Task {task_id} queued for retry (attempt {task.retry_count})")
        return True

    # Private methods

    async def _scheduling_loop(self):
        """Background task scheduling loop."""
        while True:
            try:
                # Update throughput metrics
                self._update_throughput_metrics()

                # Process dependency graph updates
                await self._update_dependency_graph()

                # Rebalance queues if needed
                if self.policy.enable_load_balancing:
                    await self._rebalance_queues()

                await asyncio.sleep(5.0)  # Run every 5 seconds

            except asyncio.CancelledError:
                break
            except (ValueError, TypeError, RuntimeError, AttributeError) as e:
                logger.error(f"Error in scheduling loop: {e}")
                await asyncio.sleep(5.0)

    async def _monitoring_loop(self):
        """Background monitoring loop."""
        while True:
            try:
                # Check for stalled tasks
                stalled_tasks = await self.check_stalled_tasks()
                for task_id in stalled_tasks:
                    await self.retry_task(task_id)

                # Clean up old completed tasks
                await self._cleanup_old_tasks()

                await asyncio.sleep(30.0)  # Run every 30 seconds

            except asyncio.CancelledError:
                break
            except (ValueError, TypeError, RuntimeError, AttributeError) as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(30.0)

    async def _cleanup_loop(self):
        """Background cleanup loop."""
        while True:
            try:
                # Remove old task completion events
                self._cleanup_completion_events()

                # Cleanup old execution history
                self._cleanup_execution_history()

                await asyncio.sleep(300.0)  # Run every 5 minutes

            except asyncio.CancelledError:
                break
            except (ValueError, TypeError, RuntimeError, AttributeError) as e:
                logger.error(f"Error in cleanup loop: {e}")
                await asyncio.sleep(300.0)

    async def _apply_educational_optimizations(self, task: Task):
        """Apply educational-specific optimizations to task."""
        context = task.educational_context

        # Extract curriculum standards
        if "curriculum_standards" in context:
            task.curriculum_standards = context["curriculum_standards"]

            # Map task to curriculum standards
            for standard in task.curriculum_standards:
                if standard not in self.curriculum_task_mapping:
                    self.curriculum_task_mapping[standard] = []
                self.curriculum_task_mapping[standard].append(task.task_id)

        # Extract learning objectives
        if "learning_objectives" in context:
            task.learning_objectives = context["learning_objectives"]

        # Extract target grade levels
        if "grade_level" in context:
            grade_level = context["grade_level"]
            if isinstance(grade_level, int):
                task.target_grade_levels = [grade_level]
            elif isinstance(grade_level, list):
                task.target_grade_levels = grade_level

        # Set educational priority adjustments
        if task.task_type in [
            TaskType.CURRICULUM_ALIGNMENT.value,
            TaskType.ASSESSMENT_ANALYSIS.value,
        ]:
            # Boost priority for critical educational tasks
            if task.priority == TaskPriority.NORMAL:
                task.priority = TaskPriority.HIGH

    async def _enqueue_task(self, task: Task):
        """Add task to appropriate queues."""
        # Add to main priority queue
        heapq.heappush(self.priority_queue, task)
        task.status = TaskStatus.QUEUED

        # Add to educational specialized queues
        context = task.educational_context

        # Subject-based queuing
        if "subject" in context:
            subject = context["subject"]
            if subject not in self.subject_task_queues:
                self.subject_task_queues[subject] = []
            self.subject_task_queues[subject].append(task)

        # Grade level-based queuing
        for grade_level in task.target_grade_levels:
            if grade_level not in self.grade_level_task_queues:
                self.grade_level_task_queues[grade_level] = []
            self.grade_level_task_queues[grade_level].append(task)

    async def _dequeue_task(self, task: Task):
        """Remove task from specialized queues."""
        context = task.educational_context

        # Remove from subject queue
        if "subject" in context:
            subject = context["subject"]
            if subject in self.subject_task_queues:
                try:
                    self.subject_task_queues[subject].remove(task)
                except ValueError:
                    pass

        # Remove from grade level queues
        for grade_level in task.target_grade_levels:
            if grade_level in self.grade_level_task_queues:
                try:
                    self.grade_level_task_queues[grade_level].remove(task)
                except ValueError:
                    pass

    async def _remove_from_queues(self, task: Task):
        """Remove task from all queues."""
        # Remove from priority queue
        try:
            self.priority_queue.remove(task)
            heapq.heapify(self.priority_queue)
        except ValueError:
            pass

        # Remove from specialized queues
        await self._dequeue_task(task)

    async def _select_task_by_policy(
        self, suitable_tasks: list[tuple[int, Task]]
    ) -> tuple[int, Task]:
        """Select the best task based on scheduling policy."""
        if len(suitable_tasks) == 1:
            return suitable_tasks[0]

        if self.policy.algorithm == "priority":
            # Simple priority-based selection (already sorted by heap)
            return suitable_tasks[0]

        elif self.policy.algorithm == "fifo":
            # First In, First Out
            return min(suitable_tasks, key=lambda x: x[1].created_at)

        elif self.policy.algorithm == "fair":
            # Fair scheduling with age consideration
            return self._select_by_fairness(suitable_tasks)

        elif self.policy.algorithm == "priority_fair":
            # Priority with fairness and age considerations
            return self._select_by_priority_fairness(suitable_tasks)

        else:
            # Default to priority
            return suitable_tasks[0]

    def _select_by_fairness(self, suitable_tasks: list[tuple[int, Task]]) -> tuple[int, Task]:
        """Select task using fairness algorithm."""
        # Weight by age to prevent starvation
        best_index, best_task = suitable_tasks[0]
        best_score = best_task.get_age()

        for index, task in suitable_tasks[1:]:
            score = task.get_age()
            if score > best_score:
                best_score = score
                best_index, best_task = index, task

        return best_index, best_task

    def _select_by_priority_fairness(
        self, suitable_tasks: list[tuple[int, Task]]
    ) -> tuple[int, Task]:
        """Select task using priority-fairness algorithm."""
        best_index, best_task = suitable_tasks[0]
        best_score = best_task.priority.value + self.policy.age_factor_weight * (
            best_task.get_age() / 3600
        )  # Age in hours

        for index, task in suitable_tasks[1:]:
            score = task.priority.value + self.policy.age_factor_weight * (task.get_age() / 3600)

            if score > best_score:
                best_score = score
                best_index, best_task = index, task

        return best_index, best_task

    def _worker_can_handle_task(self, worker_capabilities: list[str], task: Task) -> bool:
        """Check if worker has required capabilities for task."""
        required_capability = self._get_required_capability(task.task_type)
        return required_capability in worker_capabilities

    def _get_required_capability(self, task_type: str) -> str:
        """Map task type to required worker capability."""
        capability_map = {
            TaskType.CONTENT_GENERATION.value: "content_generation",
            TaskType.QUIZ_CREATION.value: "quiz_creation",
            TaskType.TERRAIN_GENERATION.value: "terrain_generation",
            TaskType.SCRIPT_OPTIMIZATION.value: "script_optimization",
            TaskType.QUALITY_REVIEW.value: "quality_review",
            TaskType.LMS_INTEGRATION.value: "lms_integration",
            TaskType.CURRICULUM_ALIGNMENT.value: "curriculum_alignment",
            TaskType.ASSESSMENT_ANALYSIS.value: "assessment_analysis",
        }
        return capability_map.get(task_type, "content_generation")

    async def _process_dependent_tasks(self, completed_task_id: str):
        """Process tasks that were waiting for the completed task."""
        if completed_task_id not in self.dependency_graph:
            return

        dependent_task_ids = self.dependency_graph[completed_task_id]

        for dependent_id in dependent_task_ids:
            if dependent_id in self.tasks:
                dependent_task = self.tasks[dependent_id]
                if dependent_task.can_execute(self.completed_tasks):
                    # Task dependencies are now satisfied
                    logger.info(f"Task {dependent_id} dependencies satisfied")

    async def _schedule_retry(self, task: Task):
        """Schedule a task for retry after delay."""
        await asyncio.sleep(task.retry_delay)

        # Reset task for retry
        task.status = TaskStatus.PENDING
        task.started_at = None
        task.assigned_worker_id = None

        # Re-queue
        await self._enqueue_task(task)

        # Execute retry callback
        if task.on_retry:
            try:
                if asyncio.iscoroutinefunction(task.on_retry):
                    await task.on_retry(task.task_id, task.retry_count)
                else:
                    task.on_retry(task.task_id, task.retry_count)
            except (ValueError, TypeError, RuntimeError, AttributeError) as e:
                logger.error(f"Error in retry callback for task {task.task_id}: {e}")

    async def _update_dependency_graph(self):
        """Update dependency graph by removing completed tasks."""
        completed_to_remove = []

        for completed_id in self.completed_tasks:
            if completed_id in self.dependency_graph:
                completed_to_remove.append(completed_id)

        for completed_id in completed_to_remove:
            del self.dependency_graph[completed_id]

    async def _rebalance_queues(self):
        """Rebalance specialized queues based on current load."""
        # This is a placeholder for more sophisticated load balancing
        # Could implement queue priority adjustments, task migration, etc.
        pass

    async def _wait_for_running_tasks(self):
        """Wait for all running tasks to complete."""
        while self.running_tasks:
            await asyncio.sleep(0.1)

    async def _cleanup_old_tasks(self):
        """Remove old completed/failed tasks to free memory."""
        cutoff_time = datetime.now() - timedelta(hours=24)

        old_task_ids = []
        for task_id, task in self.tasks.items():
            if (
                task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]
                and task.completed_at
                and task.completed_at < cutoff_time
            ):
                old_task_ids.append(task_id)

        for task_id in old_task_ids:
            self.tasks.pop(task_id, None)
            self.task_results.pop(task_id, None)
            self.completed_tasks.discard(task_id)
            self.failed_tasks.discard(task_id)

    def _cleanup_completion_events(self):
        """Remove old task completion events."""
        cutoff_time = datetime.now() - timedelta(hours=1)

        old_event_ids = []
        for task_id in self.task_completion_events:
            if (
                task_id in self.tasks
                and self.tasks[task_id].completed_at
                and self.tasks[task_id].completed_at < cutoff_time
            ):
                old_event_ids.append(task_id)

        for task_id in old_event_ids:
            self.task_completion_events.pop(task_id, None)

    def _cleanup_execution_history(self):
        """Clean up old execution history data."""
        if len(self.task_execution_history) > 10000:  # Keep last 10k records
            self.task_execution_history = self.task_execution_history[-5000:]

    def _update_average_metric(self, metric_name: str, new_value: float):
        """Update running average for a metric."""
        current_value = self.metrics.get(metric_name, 0.0)
        completed_count = self.metrics["tasks_completed"]

        if completed_count <= 1:
            self.metrics[metric_name] = new_value
        else:
            # Running average
            self.metrics[metric_name] = (
                current_value * (completed_count - 1) + new_value
            ) / completed_count

    def _update_throughput_metrics(self):
        """Update throughput metrics."""
        # Calculate tasks completed in the last minute
        cutoff_time = datetime.now() - timedelta(minutes=1)
        recent_completions = 0

        for task in self.tasks.values():
            if (
                task.status == TaskStatus.COMPLETED
                and task.completed_at
                and task.completed_at >= cutoff_time
            ):
                recent_completions += 1

        self.metrics["throughput_per_minute"] = recent_completions
