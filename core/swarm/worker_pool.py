"""
Worker Pool Management - Manages the lifecycle and coordination of worker agents.

This module provides comprehensive worker pool management including dynamic scaling,
health monitoring, specialization management, and educational content optimization.
"""

import asyncio
import time
import uuid
from typing import Dict, List, Optional, Set, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
import logging
from datetime import datetime, timedelta
import json
import resource
import psutil
import threading

logger = logging.getLogger(__name__)


class WorkerStatus(Enum):
    """Enumeration of possible worker states."""

    INITIALIZING = "initializing"
    IDLE = "idle"
    WORKING = "working"
    OVERLOADED = "overloaded"
    ERROR = "error"
    SHUTTING_DOWN = "shutting_down"
    OFFLINE = "offline"


class WorkerCapability(Enum):
    """Enumeration of worker capabilities for task specialization."""

    CONTENT_GENERATION = "content_generation"
    QUIZ_CREATION = "quiz_creation"
    TERRAIN_GENERATION = "terrain_generation"
    SCRIPT_OPTIMIZATION = "script_optimization"
    QUALITY_REVIEW = "quality_review"
    LMS_INTEGRATION = "lms_integration"
    CURRICULUM_ALIGNMENT = "curriculum_alignment"
    ACCESSIBILITY_REVIEW = "accessibility_review"

    # Subject specializations
    MATHEMATICS = "mathematics"
    SCIENCE = "science"
    ENGLISH = "english"
    HISTORY = "history"
    ART = "art"
    PHYSICAL_EDUCATION = "physical_education"


@dataclass
class WorkerConfig:
    """Configuration for a worker agent in the pool."""

    worker_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    capabilities: List[WorkerCapability] = field(default_factory=list)
    max_concurrent_tasks: int = 5
    timeout_seconds: int = 300
    retry_attempts: int = 3
    priority: int = 1
    resource_limits: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class WorkerMetrics:
    """Metrics tracking for individual worker performance."""

    tasks_completed: int = 0
    tasks_failed: int = 0
    total_execution_time: float = 0.0
    average_task_time: float = 0.0
    cpu_usage: float = 0.0
    memory_usage: float = 0.0
    last_activity: datetime = field(default_factory=datetime.now)
    uptime: float = 0.0
    error_rate: float = 0.0

    # Educational-specific metrics
    content_quality_score: float = 0.0
    curriculum_alignment_score: float = 0.0
    student_engagement_score: float = 0.0

    def update_performance_metrics(self):
        """Calculate derived performance metrics."""
        total_tasks = self.tasks_completed + self.tasks_failed
        if total_tasks > 0:
            self.error_rate = self.tasks_failed / total_tasks
            if self.tasks_completed > 0:
                self.average_task_time = (
                    self.total_execution_time / self.tasks_completed
                )


class WorkerAgent:
    """
    Individual worker agent that executes tasks within the swarm.

    Each worker has specialized capabilities and maintains its own state,
    metrics, and task execution context optimized for educational content.
    """

    def __init__(
        self,
        worker_id: str,
        capabilities: List[WorkerCapability],
        max_concurrent_tasks: int = 3,
        educational_specializations: Optional[List[str]] = None,
    ):
        self.worker_id = worker_id
        self.capabilities = capabilities
        self.max_concurrent_tasks = max_concurrent_tasks
        self.educational_specializations = educational_specializations or []

        self.status = WorkerStatus.INITIALIZING
        self.metrics = WorkerMetrics()
        self.current_tasks: Dict[str, Any] = {}
        self.task_queue: asyncio.Queue = asyncio.Queue()

        # Resource monitoring
        self.process = psutil.Process()
        self.start_time = time.time()

        # Educational context
        self.subject_expertise: Dict[str, float] = {}  # subject -> expertise level
        self.grade_level_adaptations: Set[int] = set()
        self.curriculum_knowledge: List[str] = []

        # Task execution
        self._execution_lock = asyncio.Lock()
        self._shutdown_event = asyncio.Event()
        self._worker_task: Optional[asyncio.Task] = None

        logger.info(
            f"WorkerAgent {worker_id} initialized with capabilities: {capabilities}"
        )

    async def initialize(self):
        """Initialize the worker agent and start task processing."""
        try:
            self.status = WorkerStatus.INITIALIZING

            # Initialize educational specializations
            await self._initialize_educational_context()

            # Start task processing loop
            self._worker_task = asyncio.create_task(self._task_processing_loop())

            self.status = WorkerStatus.IDLE
            self.metrics.last_activity = datetime.now()

            logger.info(f"Worker {self.worker_id} initialized successfully")

        except (ValueError, TypeError, RuntimeError, AttributeError) as e:
            self.status = WorkerStatus.ERROR
            logger.error(f"Failed to initialize worker {self.worker_id}: {e}")
            raise

    async def shutdown(self):
        """Gracefully shutdown the worker agent."""
        try:
            self.status = WorkerStatus.SHUTTING_DOWN

            # Signal shutdown to processing loop
            self._shutdown_event.set()

            # Wait for current tasks to complete (with timeout)
            if self._worker_task and not self._worker_task.done():
                try:
                    await asyncio.wait_for(self._worker_task, timeout=30.0)
                except asyncio.TimeoutError:
                    logger.warning(f"Worker {self.worker_id} shutdown timed out")
                    self._worker_task.cancel()

            self.status = WorkerStatus.OFFLINE
            logger.info(f"Worker {self.worker_id} shutdown completed")

        except (ValueError, TypeError, RuntimeError, asyncio.CancelledError) as e:
            logger.error(f"Error during worker {self.worker_id} shutdown: {e}")

    async def assign_task(self, task: Any) -> bool:
        """
        Assign a task to this worker.

        Args:
            task: Task object to execute

        Returns:
            True if task was successfully assigned
        """
        if self.status not in [WorkerStatus.IDLE, WorkerStatus.WORKING]:
            logger.warning(
                f"Cannot assign task to worker {self.worker_id} in state {self.status}"
            )
            return False

        if len(self.current_tasks) >= self.max_concurrent_tasks:
            logger.warning(f"Worker {self.worker_id} is at capacity")
            return False

        # Check if worker has required capabilities
        if not await self._can_handle_task(task):
            logger.debug(
                f"Worker {self.worker_id} cannot handle task type {getattr(task, 'task_type', 'unknown')}"
            )
            return False

        try:
            await self.task_queue.put(task)
            logger.info(f"Task assigned to worker {self.worker_id}")
            return True

        except (ValueError, TypeError, RuntimeError, AttributeError) as e:
            logger.error(f"Error assigning task to worker {self.worker_id}: {e}")
            return False

    async def is_available(self) -> bool:
        """Check if the worker is available to accept new tasks."""
        return (
            self.status in [WorkerStatus.IDLE, WorkerStatus.WORKING]
            and len(self.current_tasks) < self.max_concurrent_tasks
            and not self._shutdown_event.is_set()
        )

    async def get_load_factor(self) -> float:
        """Get current load factor (0.0 = idle, 1.0 = fully loaded)."""
        if self.max_concurrent_tasks == 0:
            return 1.0
        return len(self.current_tasks) / self.max_concurrent_tasks

    async def check_health(self) -> bool:
        """Perform health check on the worker."""
        try:
            # Check process health
            if not self.process.is_running():
                logger.warning(f"Worker {self.worker_id} process not running")
                return False

            # Check memory usage
            memory_percent = self.process.memory_percent()
            if memory_percent > 90:
                logger.warning(
                    f"Worker {self.worker_id} memory usage high: {memory_percent}%"
                )
                self.status = WorkerStatus.OVERLOADED
                return False

            # Check if worker is responsive
            last_activity_ago = (
                datetime.now() - self.metrics.last_activity
            ).total_seconds()
            if last_activity_ago > 600:  # 10 minutes
                logger.warning(
                    f"Worker {self.worker_id} inactive for {last_activity_ago}s"
                )
                return False

            # Update metrics
            self.metrics.cpu_usage = self.process.cpu_percent()
            self.metrics.memory_usage = memory_percent
            self.metrics.uptime = time.time() - self.start_time

            return True

        except (ValueError, TypeError, RuntimeError, AttributeError, OSError) as e:
            logger.error(f"Health check failed for worker {self.worker_id}: {e}")
            self.status = WorkerStatus.ERROR
            return False

    async def recover(self) -> bool:
        """Attempt to recover the worker from an error state."""
        try:
            if self.status not in [WorkerStatus.ERROR, WorkerStatus.OVERLOADED]:
                return True

            # Clear current tasks if in error state
            if self.status == WorkerStatus.ERROR:
                self.current_tasks.clear()
                while not self.task_queue.empty():
                    try:
                        self.task_queue.get_nowait()
                    except asyncio.QueueEmpty:
                        break

            # Reset status
            self.status = WorkerStatus.IDLE
            self.metrics.last_activity = datetime.now()

            logger.info(f"Worker {self.worker_id} recovered successfully")
            return True

        except (ValueError, TypeError, RuntimeError, AttributeError) as e:
            logger.error(f"Failed to recover worker {self.worker_id}: {e}")
            return False

    async def get_capabilities_score(self, task: Any) -> float:
        """Calculate how well this worker matches the task requirements."""
        if not hasattr(task, "task_type") or not hasattr(task, "educational_context"):
            return 0.5  # Default score

        score = 0.0
        factors = 0

        # Check task type capability
        task_capability = self._get_task_capability(task.task_type)
        if task_capability in self.capabilities:
            score += 1.0
            factors += 1

        # Check subject expertise
        educational_context = task.educational_context
        if "subject" in educational_context:
            subject = educational_context["subject"]
            if subject in self.subject_expertise:
                score += self.subject_expertise[subject]
                factors += 1

        # Check grade level adaptation
        if "grade_level" in educational_context:
            grade_level = educational_context["grade_level"]
            if grade_level in self.grade_level_adaptations:
                score += 1.0
                factors += 1

        # Check curriculum knowledge
        if "curriculum_standards" in educational_context:
            standards = educational_context["curriculum_standards"]
            matching_standards = set(standards) & set(self.curriculum_knowledge)
            if matching_standards:
                score += len(matching_standards) / len(standards)
                factors += 1

        return score / factors if factors > 0 else 0.5

    def get_status_info(self) -> Dict[str, Any]:
        """Get comprehensive status information for this worker."""
        return {
            "worker_id": self.worker_id,
            "status": self.status.value,
            "capabilities": [cap.value for cap in self.capabilities],
            "educational_specializations": self.educational_specializations,
            "metrics": {
                "tasks_completed": self.metrics.tasks_completed,
                "tasks_failed": self.metrics.tasks_failed,
                "average_task_time": self.metrics.average_task_time,
                "cpu_usage": self.metrics.cpu_usage,
                "memory_usage": self.metrics.memory_usage,
                "uptime": self.metrics.uptime,
                "error_rate": self.metrics.error_rate,
                "content_quality_score": self.metrics.content_quality_score,
                "curriculum_alignment_score": self.metrics.curriculum_alignment_score,
            },
            "current_tasks": len(self.current_tasks),
            "max_concurrent_tasks": self.max_concurrent_tasks,
            "load_factor": len(self.current_tasks) / self.max_concurrent_tasks,
            "queue_size": self.task_queue.qsize(),
        }

    # Private methods

    async def _task_processing_loop(self):
        """Main task processing loop for the worker."""
        while not self._shutdown_event.is_set():
            try:
                # Get next task from queue (with timeout)
                try:
                    task = await asyncio.wait_for(self.task_queue.get(), timeout=1.0)
                except asyncio.TimeoutError:
                    continue

                # Execute the task
                await self._execute_task(task)

            except asyncio.CancelledError:
                break
            except (ValueError, TypeError, RuntimeError, AttributeError) as e:
                logger.error(
                    f"Error in task processing loop for worker {self.worker_id}: {e}"
                )
                await asyncio.sleep(1.0)

        logger.info(f"Task processing loop ended for worker {self.worker_id}")

    async def _execute_task(self, task: Any):
        """Execute a single task."""
        task_id = getattr(task, "task_id", str(uuid.uuid4()))
        start_time = time.time()

        try:
            async with self._execution_lock:
                self.current_tasks[task_id] = task
                self.status = WorkerStatus.WORKING
                self.metrics.last_activity = datetime.now()

            logger.info(f"Worker {self.worker_id} starting task {task_id}")

            # Execute task based on type
            result = await self._dispatch_task_execution(task)

            # Apply educational enhancements
            if hasattr(task, "educational_context"):
                result = await self._apply_educational_enhancements(
                    result, task.educational_context
                )

            # Update metrics with lock to prevent race conditions
            execution_time = time.time() - start_time
            async with self._execution_lock:
                self.metrics.tasks_completed += 1
                self.metrics.total_execution_time += execution_time
                self.metrics.update_performance_metrics()

            # Set task result
            if hasattr(task, "set_result"):
                task.set_result(result)

            logger.info(
                f"Worker {self.worker_id} completed task {task_id} in {execution_time:.2f}s"
            )

        except (ValueError, TypeError, RuntimeError, AttributeError) as e:
            logger.error(f"Worker {self.worker_id} failed task {task_id}: {e}")

            # Update failure metrics with lock
            async with self._execution_lock:
                self.metrics.tasks_failed += 1
                self.metrics.update_performance_metrics()

            if hasattr(task, "set_error"):
                task.set_error(e)

        finally:
            # Cleanup with lock to prevent race conditions
            async with self._execution_lock:
                self.current_tasks.pop(task_id, None)

                # Update status
                if len(self.current_tasks) == 0:
                    self.status = WorkerStatus.IDLE

                self.metrics.last_activity = datetime.now()

    async def _dispatch_task_execution(self, task: Any) -> Any:
        """Dispatch task execution based on task type."""
        task_type = getattr(task, "task_type", "unknown")
        task_data = getattr(task, "task_data", {})

        if task_type == "content_generation":
            return await self._execute_content_generation(task_data)
        elif task_type == "quiz_creation":
            return await self._execute_quiz_creation(task_data)
        elif task_type == "terrain_generation":
            return await self._execute_terrain_generation(task_data)
        elif task_type == "script_optimization":
            return await self._execute_script_optimization(task_data)
        elif task_type == "quality_review":
            return await self._execute_quality_review(task_data)
        else:
            return await self._execute_generic_task(task_data)

    async def _execute_content_generation(
        self, task_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute educational content generation task."""
        # Simulate content generation (replace with actual implementation)
        await asyncio.sleep(2.0)  # Simulate processing time

        return {
            "content_type": "educational_scenario",
            "title": task_data.get("title", "Generated Educational Content"),
            "description": f"Generated educational content for {task_data.get('subject', 'general')} subject",
            "roblox_scripts": ["-- Generated Lua script content"],
            "learning_objectives": task_data.get("learning_objectives", []),
            "assessment_items": [],
            "quality_score": 0.85,
        }

    async def _execute_quiz_creation(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute quiz creation task."""
        await asyncio.sleep(1.5)

        num_questions = task_data.get("num_questions", 5)
        questions = []

        for i in range(num_questions):
            questions.append(
                {
                    "question": f"Generated question {i+1} for {task_data.get('subject', 'general')}",
                    "options": ["Option A", "Option B", "Option C", "Option D"],
                    "correct_answer": 0,
                    "explanation": f"Explanation for question {i+1}",
                    "difficulty": task_data.get("difficulty", "medium"),
                }
            )

        return {
            "quiz_type": "multiple_choice",
            "questions": questions,
            "total_questions": num_questions,
            "estimated_duration": num_questions * 2,  # 2 minutes per question
            "quality_score": 0.88,
        }

    async def _execute_terrain_generation(
        self, task_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute terrain generation task."""
        await asyncio.sleep(3.0)

        return {
            "terrain_type": task_data.get("terrain_type", "educational_environment"),
            "size": task_data.get("size", "medium"),
            "lua_script": "-- Generated terrain Lua script",
            "features": task_data.get("features", []),
            "complexity_score": 0.7,
            "quality_score": 0.82,
        }

    async def _execute_script_optimization(
        self, task_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute script optimization task."""
        await asyncio.sleep(1.0)

        return {
            "original_script": task_data.get("script", ""),
            "optimized_script": "-- Optimized Lua script",
            "improvements": ["Performance optimization", "Code simplification"],
            "performance_gain": 0.25,
            "quality_score": 0.90,
        }

    async def _execute_quality_review(
        self, task_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute quality review task."""
        await asyncio.sleep(1.2)

        return {
            "review_type": "educational_content_review",
            "content_quality": 0.87,
            "curriculum_alignment": 0.92,
            "accessibility_score": 0.85,
            "recommendations": ["Minor improvements suggested"],
            "approved": True,
            "quality_score": 0.88,
        }

    async def _execute_generic_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute generic task."""
        await asyncio.sleep(1.0)

        return {
            "result": "Task completed successfully",
            "data": task_data,
            "processing_time": 1.0,
            "quality_score": 0.75,
        }

    async def _apply_educational_enhancements(
        self, result: Dict[str, Any], educational_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Apply educational enhancements to task results."""
        enhanced_result = result.copy()

        # Add curriculum alignment
        if "curriculum_standards" in educational_context:
            enhanced_result["curriculum_alignment"] = {
                "standards": educational_context["curriculum_standards"],
                "alignment_score": result.get("quality_score", 0.8),
            }

        # Add grade level appropriateness
        if "grade_level" in educational_context:
            enhanced_result["grade_level_appropriate"] = True
            enhanced_result["target_grade_level"] = educational_context["grade_level"]

        # Add accessibility features
        enhanced_result["accessibility_features"] = {
            "screen_reader_compatible": True,
            "keyboard_navigation": True,
            "high_contrast_support": True,
            "multilingual_support": educational_context.get("languages", ["en"]),
        }

        return enhanced_result

    async def _initialize_educational_context(self):
        """Initialize educational specializations and context."""
        # Set up subject expertise based on capabilities
        for capability in self.capabilities:
            if capability in [
                WorkerCapability.MATHEMATICS,
                WorkerCapability.SCIENCE,
                WorkerCapability.ENGLISH,
                WorkerCapability.HISTORY,
            ]:
                subject_name = capability.value
                self.subject_expertise[subject_name] = 0.9  # High expertise

        # Set up grade level adaptations (default to all levels)
        self.grade_level_adaptations = set(range(1, 13))  # K-12

        # Set up curriculum knowledge
        self.curriculum_knowledge = [
            "common_core",
            "next_generation_science",
            "state_standards",
        ]

    async def _can_handle_task(self, task: Any) -> bool:
        """Check if this worker can handle the given task."""
        if not hasattr(task, "task_type"):
            return True  # Can handle generic tasks

        required_capability = self._get_task_capability(task.task_type)
        return required_capability in self.capabilities

    def _get_task_capability(self, task_type: str) -> WorkerCapability:
        """Map task type to required worker capability."""
        capability_map = {
            "content_generation": WorkerCapability.CONTENT_GENERATION,
            "quiz_creation": WorkerCapability.QUIZ_CREATION,
            "terrain_generation": WorkerCapability.TERRAIN_GENERATION,
            "script_optimization": WorkerCapability.SCRIPT_OPTIMIZATION,
            "quality_review": WorkerCapability.QUALITY_REVIEW,
            "lms_integration": WorkerCapability.LMS_INTEGRATION,
            "curriculum_alignment": WorkerCapability.CURRICULUM_ALIGNMENT,
        }
        return capability_map.get(task_type, WorkerCapability.CONTENT_GENERATION)


class WorkerPool:
    """
    Manages a pool of worker agents with dynamic scaling, health monitoring,
    and educational specialization optimization.
    """

    def __init__(
        self,
        max_workers: int = 10,
        min_workers: int = 2,
        specializations: Optional[List[str]] = None,
    ):
        self.max_workers = max_workers
        self.min_workers = min_workers
        self.specializations = specializations or []

        self.workers: Dict[str, WorkerAgent] = {}
        self.worker_assignments: Dict[str, List[str]] = {}  # task_type -> worker_ids

        # Health monitoring
        self._health_check_task: Optional[asyncio.Task] = None
        self._health_check_interval = 30  # seconds

        # Worker creation settings
        self._next_worker_id = 1
        self._worker_capabilities_distribution = self._setup_capability_distribution()

        logger.info(f"WorkerPool initialized with {min_workers}-{max_workers} workers")

    async def initialize(self):
        """Initialize the worker pool with minimum number of workers."""
        try:
            # Create initial workers
            for _ in range(self.min_workers):
                await self._create_worker()

            # Start health monitoring
            self._health_check_task = asyncio.create_task(
                self._health_monitoring_loop()
            )

            logger.info(f"WorkerPool initialized with {len(self.workers)} workers")

        except (ValueError, TypeError, RuntimeError, AttributeError) as e:
            logger.error(f"Failed to initialize WorkerPool: {e}")
            raise

    async def shutdown(self):
        """Gracefully shutdown all workers in the pool."""
        try:
            # Stop health monitoring
            if self._health_check_task and not self._health_check_task.done():
                self._health_check_task.cancel()
                try:
                    await self._health_check_task
                except asyncio.CancelledError:
                    pass

            # Shutdown all workers
            shutdown_tasks = []
            for worker in self.workers.values():
                shutdown_tasks.append(worker.shutdown())

            if shutdown_tasks:
                await asyncio.gather(*shutdown_tasks, return_exceptions=True)

            self.workers.clear()
            self.worker_assignments.clear()

            logger.info("WorkerPool shutdown completed")

        except (ValueError, TypeError, RuntimeError, asyncio.CancelledError) as e:
            logger.error(f"Error during WorkerPool shutdown: {e}")

    async def assign_task(self, task: Any) -> bool:
        """Assign a task to the most suitable available worker."""
        # Find suitable workers
        suitable_workers = await self._find_suitable_workers(task)

        if not suitable_workers:
            logger.warning(
                f"No suitable workers found for task type {getattr(task, 'task_type', 'unknown')}"
            )
            return False

        # Select best worker based on load and capability score
        best_worker = await self._select_best_worker(suitable_workers, task)

        if best_worker:
            success = await best_worker.assign_task(task)
            if success:
                logger.info(f"Task assigned to worker {best_worker.worker_id}")
                return True

        logger.warning("Failed to assign task to any worker")
        return False

    async def scale_to(self, target_count: int) -> bool:
        """Scale the worker pool to the target number of workers."""
        if not self.min_workers <= target_count <= self.max_workers:
            logger.error(
                f"Target count {target_count} outside valid range "
                f"[{self.min_workers}, {self.max_workers}]"
            )
            return False

        current_count = len(self.workers)

        try:
            if target_count > current_count:
                # Scale up
                for _ in range(target_count - current_count):
                    await self._create_worker()
                logger.info(f"Scaled up to {target_count} workers")

            elif target_count < current_count:
                # Scale down
                workers_to_remove = current_count - target_count
                removed = await self._remove_idle_workers(workers_to_remove)
                logger.info(
                    f"Scaled down by {removed} workers to {len(self.workers)} total"
                )

            return True

        except (ValueError, TypeError, RuntimeError, AttributeError) as e:
            logger.error(f"Error scaling worker pool: {e}")
            return False

    async def get_worker_count(self) -> int:
        """Get the current number of workers."""
        return len(self.workers)

    async def get_all_workers(self) -> List[WorkerAgent]:
        """Get all workers in the pool."""
        return list(self.workers.values())

    async def get_status(self) -> Dict[str, Any]:
        """Get comprehensive status of the worker pool."""
        worker_statuses = {}
        total_tasks_completed = 0
        total_tasks_failed = 0

        for worker_id, worker in self.workers.items():
            status = worker.get_status_info()
            worker_statuses[worker_id] = status
            total_tasks_completed += status["metrics"]["tasks_completed"]
            total_tasks_failed += status["metrics"]["tasks_failed"]

        return {
            "total_workers": len(self.workers),
            "worker_statuses": worker_statuses,
            "total_tasks_completed": total_tasks_completed,
            "total_tasks_failed": total_tasks_failed,
            "specializations": self.specializations,
            "worker_assignments": self.worker_assignments,
        }

    async def check_worker_health(self) -> List[WorkerAgent]:
        """Check health of all workers and return unhealthy ones."""
        unhealthy_workers = []

        for worker in self.workers.values():
            if not await worker.check_health():
                unhealthy_workers.append(worker)

        return unhealthy_workers

    async def replace_worker(self, worker: WorkerAgent) -> bool:
        """Replace an unhealthy worker with a new one."""
        try:
            worker_id = worker.worker_id
            capabilities = worker.capabilities

            # Remove old worker
            await worker.shutdown()
            self.workers.pop(worker_id, None)

            # Create new worker with same capabilities
            new_worker = await self._create_worker_with_capabilities(capabilities)

            logger.info(f"Replaced worker {worker_id} with {new_worker.worker_id}")
            return True

        except (ValueError, TypeError, RuntimeError, AttributeError) as e:
            logger.error(f"Error replacing worker: {e}")
            return False

    async def get_idle_time(self) -> float:
        """Get average idle time across all workers."""
        if not self.workers:
            return 0.0

        total_idle_time = 0.0
        idle_workers = 0

        for worker in self.workers.values():
            if worker.status == WorkerStatus.IDLE:
                idle_time = (
                    datetime.now() - worker.metrics.last_activity
                ).total_seconds()
                total_idle_time += idle_time
                idle_workers += 1

        return total_idle_time / idle_workers if idle_workers > 0 else 0.0

    # Private methods

    async def _create_worker(self) -> WorkerAgent:
        """Create a new worker with appropriate capabilities."""
        worker_id = f"worker_{self._next_worker_id:03d}"
        self._next_worker_id += 1

        # Assign capabilities based on distribution
        capabilities = self._assign_worker_capabilities()

        # Create and initialize worker
        worker = WorkerAgent(
            worker_id=worker_id,
            capabilities=capabilities,
            educational_specializations=self.specializations,
        )

        await worker.initialize()
        self.workers[worker_id] = worker

        # Update assignments
        self._update_worker_assignments(worker_id, capabilities)

        logger.info(f"Created worker {worker_id} with capabilities: {capabilities}")
        return worker

    async def _create_worker_with_capabilities(
        self, capabilities: List[WorkerCapability]
    ) -> WorkerAgent:
        """Create a worker with specific capabilities."""
        worker_id = f"worker_{self._next_worker_id:03d}"
        self._next_worker_id += 1

        worker = WorkerAgent(
            worker_id=worker_id,
            capabilities=capabilities,
            educational_specializations=self.specializations,
        )

        await worker.initialize()
        self.workers[worker_id] = worker

        self._update_worker_assignments(worker_id, capabilities)

        return worker

    async def _remove_idle_workers(self, count: int) -> int:
        """Remove idle workers up to the specified count."""
        idle_workers = [
            worker
            for worker in self.workers.values()
            if worker.status == WorkerStatus.IDLE
        ]

        # Sort by last activity (remove least recently active first)
        idle_workers.sort(key=lambda w: w.metrics.last_activity)

        removed = 0
        for worker in idle_workers[:count]:
            await worker.shutdown()
            self.workers.pop(worker.worker_id, None)
            self._remove_worker_assignments(worker.worker_id)
            removed += 1

        return removed

    def _setup_capability_distribution(self) -> Dict[WorkerCapability, float]:
        """Set up the distribution of capabilities across workers."""
        return {
            WorkerCapability.CONTENT_GENERATION: 0.8,
            WorkerCapability.QUIZ_CREATION: 0.6,
            WorkerCapability.TERRAIN_GENERATION: 0.4,
            WorkerCapability.SCRIPT_OPTIMIZATION: 0.3,
            WorkerCapability.QUALITY_REVIEW: 0.5,
            WorkerCapability.LMS_INTEGRATION: 0.2,
            WorkerCapability.CURRICULUM_ALIGNMENT: 0.7,
            WorkerCapability.ACCESSIBILITY_REVIEW: 0.3,
            # Subject specializations
            WorkerCapability.MATHEMATICS: 0.3,
            WorkerCapability.SCIENCE: 0.3,
            WorkerCapability.ENGLISH: 0.2,
            WorkerCapability.HISTORY: 0.2,
        }

    def _assign_worker_capabilities(self) -> List[WorkerCapability]:
        """Assign capabilities to a new worker based on distribution."""
        capabilities = [
            WorkerCapability.CONTENT_GENERATION
        ]  # All workers can generate content

        for capability, probability in self._worker_capabilities_distribution.items():
            if capability != WorkerCapability.CONTENT_GENERATION:
                if (
                    hash(str(capability) + str(self._next_worker_id)) % 100
                    < probability * 100
                ):
                    capabilities.append(capability)

        return capabilities

    def _update_worker_assignments(
        self, worker_id: str, capabilities: List[WorkerCapability]
    ):
        """Update worker assignments based on capabilities."""
        for capability in capabilities:
            task_type = capability.value
            if task_type not in self.worker_assignments:
                self.worker_assignments[task_type] = []
            self.worker_assignments[task_type].append(worker_id)

    def _remove_worker_assignments(self, worker_id: str):
        """Remove worker from all assignments."""
        for task_type, worker_ids in self.worker_assignments.items():
            if worker_id in worker_ids:
                worker_ids.remove(worker_id)

    async def _find_suitable_workers(self, task: Any) -> List[WorkerAgent]:
        """Find workers suitable for the given task."""
        if not hasattr(task, "task_type"):
            # Return all available workers for generic tasks
            return [w for w in self.workers.values() if await w.is_available()]

        task_type = task.task_type
        suitable_workers = []

        # Get workers assigned to this task type
        if task_type in self.worker_assignments:
            for worker_id in self.worker_assignments[task_type]:
                if worker_id in self.workers:
                    worker = self.workers[worker_id]
                    if await worker.is_available():
                        suitable_workers.append(worker)

        return suitable_workers

    async def _select_best_worker(
        self, workers: List[WorkerAgent], task: Any
    ) -> Optional[WorkerAgent]:
        """Select the best worker for the task based on load and capabilities."""
        if not workers:
            return None

        best_worker = None
        best_score = -1.0

        for worker in workers:
            # Calculate selection score
            load_factor = await worker.get_load_factor()
            capability_score = await worker.get_capabilities_score(task)

            # Prefer workers with lower load and higher capability
            selection_score = capability_score * (1.0 - load_factor)

            if selection_score > best_score:
                best_score = selection_score
                best_worker = worker

        return best_worker

    async def _health_monitoring_loop(self):
        """Background loop for monitoring worker health."""
        while True:
            try:
                unhealthy_workers = await self.check_worker_health()

                for worker in unhealthy_workers:
                    logger.warning(f"Worker {worker.worker_id} is unhealthy")

                    # Try to recover first
                    if not await worker.recover():
                        # Replace if recovery fails
                        await self.replace_worker(worker)

                await asyncio.sleep(self._health_check_interval)

            except asyncio.CancelledError:
                break
            except (ValueError, TypeError, RuntimeError, AttributeError) as e:
                logger.error(f"Error in health monitoring loop: {e}")
                await asyncio.sleep(self._health_check_interval)
