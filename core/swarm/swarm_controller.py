"""
Swarm Controller - Main orchestration engine for the swarm intelligence system.

This module provides the central coordination point for all swarm operations,
managing parallel agent execution, task distribution, and result aggregation
with a focus on educational content generation.
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Optional

from .consensus_engine import ConsensusEngine
from .load_balancer import LoadBalancer
from .task_distributor import Task, TaskDistributor, TaskPriority
from .worker_pool import WorkerAgent, WorkerPool

logger = logging.getLogger(__name__)


class SwarmState(Enum):
    """Enumeration of possible swarm states."""

    INITIALIZING = "initializing"
    ACTIVE = "active"
    SCALING = "scaling"
    PAUSED = "paused"
    SHUTTING_DOWN = "shutting_down"
    ERROR = "error"


@dataclass
class SwarmConfig:
    """Configuration settings for the swarm controller."""

    max_workers: int = 10
    min_workers: int = 2
    task_timeout: int = 300  # seconds
    consensus_threshold: float = 0.7
    load_balancing_strategy: str = "round_robin"
    worker_specializations: list[str] = field(default_factory=list)
    educational_optimizations: dict[str, Any] = field(default_factory=dict)
    auto_scaling: bool = True
    health_check_interval: int = 30  # seconds
    metrics_retention_hours: int = 24

    # Educational-specific settings
    primary_subject: Optional[str] = None
    target_grade_level: Optional[int] = None
    curriculum_standards: list[str] = field(default_factory=list)

    def __post_init__(self):
        """Validate configuration after initialization."""
        if self.max_workers < self.min_workers:
            raise ValueError("max_workers must be >= min_workers")
        if not 0.0 <= self.consensus_threshold <= 1.0:
            raise ValueError("consensus_threshold must be between 0 and 1")


@dataclass
class SwarmMetrics:
    """Metrics and statistics for swarm performance monitoring."""

    start_time: datetime = field(default_factory=datetime.now)
    tasks_completed: int = 0
    tasks_failed: int = 0
    total_execution_time: float = 0.0
    active_workers: int = 0
    average_task_time: float = 0.0
    throughput_per_minute: float = 0.0
    consensus_accuracy: float = 0.0
    resource_utilization: float = 0.0
    error_rate: float = 0.0

    # Educational-specific metrics
    content_pieces_generated: int = 0
    quiz_questions_created: int = 0
    curriculum_alignment_score: float = 0.0
    learning_objective_coverage: float = 0.0

    def calculate_derived_metrics(self):
        """Calculate derived metrics from raw data."""
        total_tasks = self.tasks_completed + self.tasks_failed
        if total_tasks > 0:
            self.error_rate = self.tasks_failed / total_tasks
            if self.tasks_completed > 0:
                self.average_task_time = self.total_execution_time / self.tasks_completed

        # Calculate throughput
        uptime_minutes = (datetime.now() - self.start_time).total_seconds() / 60
        if uptime_minutes > 0:
            self.throughput_per_minute = self.tasks_completed / uptime_minutes


class SwarmController:
    """
    Main swarm orchestration engine that coordinates all swarm operations.

    Manages parallel agent execution, intelligent task distribution,
    consensus-based quality control, and educational content optimization.
    """

    def __init__(
        self,
        config: SwarmConfig,
        worker_pool: WorkerPool,
        task_distributor: TaskDistributor,
        consensus_engine: ConsensusEngine,
        load_balancer: LoadBalancer,
    ):
        self.config = config
        self.worker_pool = worker_pool
        self.task_distributor = task_distributor
        self.consensus_engine = consensus_engine
        self.load_balancer = load_balancer

        self.state = SwarmState.INITIALIZING
        self.metrics = SwarmMetrics()
        self.active_tasks: dict[str, Task] = {}
        self.completed_tasks: dict[str, Any] = {}
        self.event_callbacks: dict[str, list[Callable]] = {}

        # Educational content tracking
        self.subject_specialists: dict[str, list[WorkerAgent]] = {}
        self.grade_level_adapters: dict[int, list[WorkerAgent]] = {}

        # Background tasks
        self._health_check_task: Optional[asyncio.Task] = None
        self._metrics_task: Optional[asyncio.Task] = None
        self._auto_scaling_task: Optional[asyncio.Task] = None

        logger.info(f"SwarmController initialized with config: {self.config}")

    async def initialize(self):
        """Initialize the swarm controller and all components."""
        try:
            self.state = SwarmState.INITIALIZING

            # Initialize components
            await self.worker_pool.initialize()
            await self.task_distributor.initialize()
            await self.consensus_engine.initialize()
            await self.load_balancer.initialize()

            # Start background tasks
            await self._start_background_tasks()

            # Set up educational specializations
            if self.config.educational_optimizations.get("subject_specialization"):
                await self._setup_subject_specialists()

            self.state = SwarmState.ACTIVE
            await self._emit_event("swarm_initialized", {"config": self.config})

            logger.info("SwarmController initialized successfully")

        except (ValueError, TypeError, AttributeError, RuntimeError) as e:
            self.state = SwarmState.ERROR
            logger.error(f"Failed to initialize SwarmController: {e}")
            raise

    async def shutdown(self):
        """Gracefully shutdown the swarm controller."""
        try:
            self.state = SwarmState.SHUTTING_DOWN
            await self._emit_event("swarm_shutting_down", {})

            # Cancel background tasks
            tasks_to_cancel = [
                self._health_check_task,
                self._metrics_task,
                self._auto_scaling_task,
            ]

            for task in tasks_to_cancel:
                if task and not task.done():
                    task.cancel()
                    try:
                        await task
                    except asyncio.CancelledError:
                        pass

            # Wait for active tasks to complete or timeout
            if self.active_tasks:
                logger.info(f"Waiting for {len(self.active_tasks)} active tasks to complete...")
                try:
                    await asyncio.wait_for(self._wait_for_active_tasks(), timeout=30.0)
                except asyncio.TimeoutError:
                    logger.warning("Timeout waiting for active tasks to complete")

            # Shutdown components
            await self.worker_pool.shutdown()
            await self.task_distributor.shutdown()
            await self.consensus_engine.shutdown()
            await self.load_balancer.shutdown()

            await self._emit_event("swarm_shutdown", {"metrics": self.metrics})
            logger.info("SwarmController shutdown completed")

        except (ValueError, TypeError, RuntimeError, asyncio.TimeoutError) as e:
            logger.error(f"Error during SwarmController shutdown: {e}")
            raise

    async def submit_task(
        self,
        task_type: str,
        task_data: dict[str, Any],
        priority: TaskPriority = TaskPriority.NORMAL,
        requires_consensus: bool = True,
        educational_context: Optional[dict[str, Any]] = None,
    ) -> str:
        """
        Submit a task to the swarm for execution.

        Args:
            task_type: Type of task (content_generation, quiz_creation, etc.)
            task_data: Task-specific data and parameters
            priority: Task priority level
            requires_consensus: Whether task results require consensus validation
            educational_context: Educational metadata (subject, grade level, etc.)

        Returns:
            Task ID for tracking progress and results
        """
        if self.state != SwarmState.ACTIVE:
            raise RuntimeError(f"Swarm not active (current state: {self.state})")

        # Create task with educational enhancements
        task = Task(
            task_type=task_type,
            task_data=task_data,
            priority=priority,
            requires_consensus=requires_consensus,
            educational_context=educational_context or {},
            timeout=self.config.task_timeout,
        )

        # Add educational optimizations
        if educational_context:
            await self._apply_educational_optimizations(task)

        # Submit to task distributor
        task_id = await self.task_distributor.submit_task_object(task)
        self.active_tasks[task_id] = task

        # Distribute task to appropriate workers
        await self._distribute_task(task)

        await self._emit_event(
            "task_submitted",
            {"task_id": task_id, "task_type": task_type, "priority": priority.value},
        )

        logger.info(f"Task {task_id} submitted: {task_type}")
        return task_id

    async def get_task_result(self, task_id: str, timeout: Optional[float] = None) -> Any:
        """
        Get the result of a completed task.

        Args:
            task_id: ID of the task
            timeout: Maximum time to wait for completion

        Returns:
            Task result or raises TimeoutError
        """
        if task_id in self.completed_tasks:
            return self.completed_tasks[task_id]

        # Wait for task completion
        result = await self.task_distributor.wait_for_completion(task_id, timeout)

        # Apply consensus if required
        task = self.active_tasks.get(task_id)
        if task and task.requires_consensus:
            consensus_result = await self.consensus_engine.evaluate_result(task_id, result)
            result = consensus_result.final_result

            # Update metrics
            self.metrics.consensus_accuracy = consensus_result.confidence

        # Store result and clean up
        self.completed_tasks[task_id] = result
        self.active_tasks.pop(task_id, None)

        # Update metrics
        self.metrics.tasks_completed += 1
        self.metrics.calculate_derived_metrics()

        await self._emit_event(
            "task_completed",
            {
                "task_id": task_id,
                "execution_time": getattr(result, "execution_time", 0),
            },
        )

        return result

    async def get_swarm_status(self) -> dict[str, Any]:
        """Get comprehensive swarm status information."""
        worker_status = await self.worker_pool.get_status()
        task_status = await self.task_distributor.get_status()
        resource_metrics = await self.load_balancer.get_metrics()

        return {
            "state": self.state.value,
            "metrics": self.metrics,
            "workers": worker_status,
            "tasks": task_status,
            "resources": resource_metrics,
            "active_tasks": len(self.active_tasks),
            "completed_tasks": len(self.completed_tasks),
            "config": self.config,
        }

    async def scale_workers(self, target_count: int) -> bool:
        """
        Scale the number of workers up or down.

        Args:
            target_count: Desired number of workers

        Returns:
            True if scaling was successful
        """
        if not self.config.min_workers <= target_count <= self.config.max_workers:
            logger.warning(
                f"Target worker count {target_count} outside bounds "
                f"[{self.config.min_workers}, {self.config.max_workers}]"
            )
            return False

        try:
            self.state = SwarmState.SCALING
            success = await self.worker_pool.scale_to(target_count)

            if success:
                self.metrics.active_workers = await self.worker_pool.get_worker_count()
                await self._emit_event(
                    "swarm_scaled", {"new_worker_count": self.metrics.active_workers}
                )
                logger.info(f"Swarm scaled to {self.metrics.active_workers} workers")

            self.state = SwarmState.ACTIVE
            return success

        except (ValueError, TypeError, RuntimeError) as e:
            logger.error(f"Error scaling swarm: {e}")
            self.state = SwarmState.ACTIVE
            return False

    async def pause(self):
        """Pause swarm operations (complete active tasks but accept no new ones)."""
        self.state = SwarmState.PAUSED
        await self._emit_event("swarm_paused", {})
        logger.info("Swarm paused")

    async def resume(self):
        """Resume swarm operations."""
        if self.state == SwarmState.PAUSED:
            self.state = SwarmState.ACTIVE
            await self._emit_event("swarm_resumed", {})
            logger.info("Swarm resumed")

    def register_event_callback(self, event_type: str, callback: Callable):
        """Register a callback for swarm events."""
        if event_type not in self.event_callbacks:
            self.event_callbacks[event_type] = []
        self.event_callbacks[event_type].append(callback)

    # Private methods

    async def _start_background_tasks(self):
        """Start background monitoring and maintenance tasks."""
        self._health_check_task = asyncio.create_task(self._health_check_loop())
        self._metrics_task = asyncio.create_task(self._metrics_collection_loop())

        if self.config.auto_scaling:
            self._auto_scaling_task = asyncio.create_task(self._auto_scaling_loop())

    async def _health_check_loop(self):
        """Background task for monitoring swarm health."""
        while self.state in [SwarmState.ACTIVE, SwarmState.PAUSED]:
            try:
                # Check worker health
                unhealthy_workers = await self.worker_pool.check_worker_health()
                if unhealthy_workers:
                    logger.warning(f"Found {len(unhealthy_workers)} unhealthy workers")
                    await self._handle_unhealthy_workers(unhealthy_workers)

                # Check task distributor health
                stalled_tasks = await self.task_distributor.check_stalled_tasks()
                if stalled_tasks:
                    logger.warning(f"Found {len(stalled_tasks)} stalled tasks")
                    await self._handle_stalled_tasks(stalled_tasks)

                await asyncio.sleep(self.config.health_check_interval)

            except asyncio.CancelledError:
                break
            except (ValueError, TypeError, RuntimeError, AttributeError) as e:
                logger.error(f"Error in health check loop: {e}")
                await asyncio.sleep(self.config.health_check_interval)

    async def _metrics_collection_loop(self):
        """Background task for collecting and updating metrics."""
        while self.state in [SwarmState.ACTIVE, SwarmState.PAUSED]:
            try:
                # Update worker metrics
                self.metrics.active_workers = await self.worker_pool.get_worker_count()

                # Update resource utilization
                resource_metrics = await self.load_balancer.get_metrics()
                self.metrics.resource_utilization = resource_metrics.overall_utilization

                # Calculate derived metrics
                self.metrics.calculate_derived_metrics()

                await asyncio.sleep(60)  # Update every minute

            except asyncio.CancelledError:
                break
            except (ValueError, TypeError, RuntimeError, AttributeError) as e:
                logger.error(f"Error in metrics collection loop: {e}")
                await asyncio.sleep(60)

    async def _auto_scaling_loop(self):
        """Background task for automatic worker scaling."""
        while self.state in [SwarmState.ACTIVE, SwarmState.PAUSED]:
            try:
                if self.state == SwarmState.ACTIVE:
                    await self._evaluate_scaling_needs()

                await asyncio.sleep(120)  # Check every 2 minutes

            except asyncio.CancelledError:
                break
            except (ValueError, TypeError, RuntimeError) as e:
                logger.error(f"Error in auto-scaling loop: {e}")
                await asyncio.sleep(120)

    async def _evaluate_scaling_needs(self):
        """Evaluate whether the swarm needs to scale up or down."""
        current_workers = await self.worker_pool.get_worker_count()
        queue_size = await self.task_distributor.get_queue_size()

        # Scale up if queue is growing
        if queue_size > current_workers * 2 and current_workers < self.config.max_workers:
            target = min(current_workers + 2, self.config.max_workers)
            await self.scale_workers(target)
            logger.info(f"Auto-scaled up to {target} workers (queue size: {queue_size})")

        # Scale down if workers are idle
        elif queue_size == 0 and current_workers > self.config.min_workers:
            idle_time = await self.worker_pool.get_idle_time()
            if idle_time > 300:  # 5 minutes of idle time
                target = max(current_workers - 1, self.config.min_workers)
                await self.scale_workers(target)
                logger.info(f"Auto-scaled down to {target} workers (idle time: {idle_time}s)")

    async def _setup_subject_specialists(self):
        """Set up workers specialized for different subjects."""
        if not self.config.worker_specializations:
            return

        workers = await self.worker_pool.get_all_workers()

        for specialization in self.config.worker_specializations:
            specialist_workers = [w for w in workers if specialization in w.capabilities]
            if specialization not in self.subject_specialists:
                self.subject_specialists[specialization] = []
            self.subject_specialists[specialization].extend(specialist_workers)

        logger.info(f"Set up {len(self.subject_specialists)} subject specializations")

    async def _apply_educational_optimizations(self, task: Task):
        """Apply educational-specific optimizations to a task."""
        context = task.educational_context

        # Add curriculum alignment
        if self.config.curriculum_standards:
            context["curriculum_standards"] = self.config.curriculum_standards

        # Add grade level adaptation
        if self.config.target_grade_level:
            context["target_grade_level"] = self.config.target_grade_level

        # Add subject specialization
        if self.config.primary_subject:
            context["primary_subject"] = self.config.primary_subject

    async def _distribute_task(self, task: Task):
        """Distribute a task to appropriate workers based on specialization."""
        # Find specialized workers for this task
        suitable_workers = await self._find_suitable_workers(task)

        if suitable_workers:
            # Use load balancer to select best worker
            selected_worker = await self.load_balancer.select_worker(suitable_workers, task)
            await selected_worker.assign_task(task)
        else:
            # Fallback to general worker pool
            await self.worker_pool.assign_task(task)

    async def _find_suitable_workers(self, task: Task) -> list[WorkerAgent]:
        """Find workers suitable for a specific task."""
        suitable_workers = []

        # Check for subject specialists
        if task.educational_context.get("subject"):
            subject = task.educational_context["subject"]
            if subject in self.subject_specialists:
                suitable_workers.extend(self.subject_specialists[subject])

        # Check for task type specialists
        task_type = task.task_type
        if task_type in self.subject_specialists:
            suitable_workers.extend(self.subject_specialists[task_type])

        # Filter by availability
        available_workers = []
        for worker in suitable_workers:
            if await worker.is_available():
                available_workers.append(worker)

        return available_workers

    async def _handle_unhealthy_workers(self, unhealthy_workers: list[WorkerAgent]):
        """Handle workers that have become unhealthy."""
        for worker in unhealthy_workers:
            try:
                # Try to recover the worker
                if await worker.recover():
                    logger.info(f"Successfully recovered worker {worker.worker_id}")
                else:
                    # Replace the worker
                    await self.worker_pool.replace_worker(worker)
                    logger.info(f"Replaced unhealthy worker {worker.worker_id}")
            except (ValueError, TypeError, AttributeError, RuntimeError) as e:
                logger.error(f"Error handling unhealthy worker {worker.worker_id}: {e}")

    async def _handle_stalled_tasks(self, stalled_tasks: list[str]):
        """Handle tasks that have become stalled."""
        for task_id in stalled_tasks:
            try:
                # Retry the task
                await self.task_distributor.retry_task(task_id)
                logger.info(f"Retried stalled task {task_id}")
            except (ValueError, TypeError, AttributeError, RuntimeError) as e:
                logger.error(f"Error handling stalled task {task_id}: {e}")
                # Mark as failed
                self.metrics.tasks_failed += 1
                self.active_tasks.pop(task_id, None)

    async def _wait_for_active_tasks(self):
        """Wait for all active tasks to complete."""
        while self.active_tasks:
            await asyncio.sleep(0.1)

    async def _emit_event(self, event_type: str, event_data: dict[str, Any]):
        """Emit an event to registered callbacks."""
        if event_type in self.event_callbacks:
            for callback in self.event_callbacks[event_type]:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(event_type, event_data)
                    else:
                        callback(event_type, event_data)
                except (ValueError, TypeError, AttributeError, RuntimeError) as e:
                    logger.error(f"Error in event callback for {event_type}: {e}")

    @asynccontextmanager
    async def batch_context(self):
        """Context manager for batch operations with optimized resource usage."""
        original_state = self.state
        try:
            # Optimize for batch processing
            await self.load_balancer.enable_batch_mode()
            yield self
        finally:
            # Restore normal operation
            await self.load_balancer.disable_batch_mode()
            self.state = original_state
