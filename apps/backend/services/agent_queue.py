"""
Redis-based Agent Task Queue System

This service provides a scalable task queue system for agent task management
using Redis as the backend for high-performance task queuing and processing.

Features:
- Priority-based task queuing
- Distributed task processing
- Retry mechanisms
- Dead letter queues
- Task scheduling
- Real-time monitoring

Author: ToolboxAI Team
Created: 2025-09-21
Version: 1.0.0
"""

import asyncio
import logging
import uuid
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any

try:
    import redis.asyncio as redis
    from redis.asyncio import Redis

    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    Redis = None

from apps.backend.services.agent_service import get_agent_service
from apps.backend.services.pusher import trigger_task_event

logger = logging.getLogger(__name__)


class TaskPriority(str, Enum):
    """Task priority levels"""

    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"
    CRITICAL = "critical"


class TaskStatus(str, Enum):
    """Task status in queue"""

    PENDING = "pending"
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRY = "retry"
    DEAD = "dead"


class QueuedTask:
    """Represents a task in the queue"""

    def __init__(
        self,
        task_id: str,
        agent_type: str,
        task_type: str,
        task_data: dict[str, Any],
        priority: TaskPriority = TaskPriority.NORMAL,
        user_id: str | None = None,
        max_retries: int = 3,
    ):
        self.task_id = task_id
        self.agent_type = agent_type
        self.task_type = task_type
        self.task_data = task_data
        self.priority = priority
        self.user_id = user_id
        self.max_retries = max_retries
        self.retry_count = 0
        self.created_at = datetime.now(timezone.utc)
        self.scheduled_at: datetime | None = None
        self.started_at: datetime | None = None
        self.completed_at: datetime | None = None
        self.error_message: str | None = None
        self.result: dict[str, Any] | None = None
        self.status = TaskStatus.PENDING

    def to_dict(self) -> dict[str, Any]:
        """Convert task to dictionary for serialization"""
        return {
            "task_id": self.task_id,
            "agent_type": self.agent_type,
            "task_type": self.task_type,
            "task_data": self.task_data,
            "priority": self.priority.value,
            "user_id": self.user_id,
            "max_retries": self.max_retries,
            "retry_count": self.retry_count,
            "created_at": self.created_at.isoformat(),
            "scheduled_at": self.scheduled_at.isoformat() if self.scheduled_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "error_message": self.error_message,
            "result": self.result,
            "status": self.status.value,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "QueuedTask":
        """Create task from dictionary"""
        task = cls(
            task_id=data["task_id"],
            agent_type=data["agent_type"],
            task_type=data["task_type"],
            task_data=data["task_data"],
            priority=TaskPriority(data["priority"]),
            user_id=data.get("user_id"),
            max_retries=data.get("max_retries", 3),
        )

        task.retry_count = data.get("retry_count", 0)
        task.created_at = datetime.fromisoformat(data["created_at"])
        task.scheduled_at = (
            datetime.fromisoformat(data["scheduled_at"]) if data.get("scheduled_at") else None
        )
        task.started_at = (
            datetime.fromisoformat(data["started_at"]) if data.get("started_at") else None
        )
        task.completed_at = (
            datetime.fromisoformat(data["completed_at"]) if data.get("completed_at") else None
        )
        task.error_message = data.get("error_message")
        task.result = data.get("result")
        task.status = TaskStatus(data["status"])

        return task


class AgentTaskQueue:
    """
    Redis-based task queue for agent system.

    Provides high-performance, distributed task queuing with:
    - Priority-based scheduling
    - Retry mechanisms
    - Dead letter queues
    - Task monitoring
    - Load balancing
    """

    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis_url = redis_url
        self.redis: Redis | None = None
        self.workers: dict[str, asyncio.Task] = {}
        self.running = False
        self.agent_service = None

        # Queue names
        self.queue_prefix = "agent_queue"
        self.processing_prefix = "agent_processing"
        self.retry_prefix = "agent_retry"
        self.dead_letter_prefix = "agent_dead"
        self.task_data_prefix = "agent_task_data"

        # Priority scores for Redis sorted sets
        self.priority_scores = {
            TaskPriority.LOW: 1,
            TaskPriority.NORMAL: 2,
            TaskPriority.HIGH: 3,
            TaskPriority.URGENT: 4,
            TaskPriority.CRITICAL: 5,
        }

    async def initialize(self):
        """Initialize Redis connection and agent service"""
        if not REDIS_AVAILABLE:
            logger.warning("Redis not available for task queue")
            return False

        try:
            self.redis = redis.from_url(self.redis_url, decode_responses=True)
            await self.redis.ping()
            self.agent_service = get_agent_service()
            logger.info("Agent task queue initialized with Redis")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize agent task queue: {e}")
            return False

    async def enqueue_task(
        self,
        agent_type: str,
        task_type: str,
        task_data: dict[str, Any],
        priority: TaskPriority = TaskPriority.NORMAL,
        user_id: str | None = None,
        delay_seconds: int = 0,
    ) -> str:
        """
        Add a task to the queue.

        Args:
            agent_type: Type of agent to handle the task
            task_type: Type of task to execute
            task_data: Task input data
            priority: Task priority level
            user_id: User who requested the task
            delay_seconds: Delay before task becomes available

        Returns:
            Task ID
        """
        if not self.redis:
            raise RuntimeError("Queue not initialized")

        task_id = str(uuid.uuid4())
        task = QueuedTask(
            task_id=task_id,
            agent_type=agent_type,
            task_type=task_type,
            task_data=task_data,
            priority=priority,
            user_id=user_id,
        )

        # Set scheduled time if delayed
        if delay_seconds > 0:
            task.scheduled_at = datetime.now(timezone.utc) + timedelta(seconds=delay_seconds)

        # Store task data
        await self.redis.hset(f"{self.task_data_prefix}:{task_id}", mapping=task.to_dict())

        # Add to appropriate queue
        queue_key = f"{self.queue_prefix}:{agent_type}"
        score = self.priority_scores[priority]

        if delay_seconds > 0:
            # Add to delayed queue with timestamp score
            delayed_queue_key = f"{queue_key}:delayed"
            timestamp = task.scheduled_at.timestamp()
            await self.redis.zadd(delayed_queue_key, {task_id: timestamp})
        else:
            # Add to immediate queue with priority score
            await self.redis.zadd(queue_key, {task_id: score})

        # Trigger task created event
        await trigger_task_event(
            "task_created",
            task_id,
            "queue",
            {"agent_type": agent_type, "task_type": task_type},
            user_id,
        )

        logger.info(f"Enqueued task {task_id} for {agent_type} with priority {priority.value}")
        return task_id

    async def dequeue_task(self, agent_type: str) -> QueuedTask | None:
        """
        Get the next task from the queue for a specific agent type.

        Args:
            agent_type: Agent type to get task for

        Returns:
            Next task or None if queue is empty
        """
        if not self.redis:
            return None

        queue_key = f"{self.queue_prefix}:{agent_type}"

        # Get highest priority task (highest score)
        result = await self.redis.zpopmax(queue_key)

        if not result:
            return None

        task_id, score = result[0]

        # Get task data
        task_data = await self.redis.hgetall(f"{self.task_data_prefix}:{task_id}")

        if not task_data:
            logger.warning(f"Task data not found for {task_id}")
            return None

        # Convert to QueuedTask
        task = QueuedTask.from_dict(task_data)
        task.status = TaskStatus.PROCESSING
        task.started_at = datetime.now(timezone.utc)

        # Move to processing queue
        processing_key = f"{self.processing_prefix}:{agent_type}"
        await self.redis.zadd(processing_key, {task_id: datetime.now(timezone.utc).timestamp()})

        # Update task data
        await self.redis.hset(f"{self.task_data_prefix}:{task_id}", mapping=task.to_dict())

        return task

    async def complete_task(self, task_id: str, result: dict[str, Any]):
        """
        Mark a task as completed.

        Args:
            task_id: Task ID
            result: Task execution result
        """
        if not self.redis:
            return

        # Get task data
        task_data = await self.redis.hgetall(f"{self.task_data_prefix}:{task_id}")
        if not task_data:
            return

        task = QueuedTask.from_dict(task_data)
        task.status = TaskStatus.COMPLETED
        task.completed_at = datetime.now(timezone.utc)
        task.result = result

        # Update task data
        await self.redis.hset(f"{self.task_data_prefix}:{task_id}", mapping=task.to_dict())

        # Remove from processing queue
        processing_key = f"{self.processing_prefix}:{task.agent_type}"
        await self.redis.zrem(processing_key, task_id)

        # Trigger completion event
        await trigger_task_event(
            "task_completed",
            task_id,
            "queue",
            {
                "result": result,
                "execution_time": (task.completed_at - task.started_at).total_seconds(),
            },
            task.user_id,
        )

        logger.info(f"Completed task {task_id}")

    async def fail_task(self, task_id: str, error_message: str):
        """
        Mark a task as failed and handle retries.

        Args:
            task_id: Task ID
            error_message: Error description
        """
        if not self.redis:
            return

        # Get task data
        task_data = await self.redis.hgetall(f"{self.task_data_prefix}:{task_id}")
        if not task_data:
            return

        task = QueuedTask.from_dict(task_data)
        task.error_message = error_message
        task.retry_count += 1

        # Remove from processing queue
        processing_key = f"{self.processing_prefix}:{task.agent_type}"
        await self.redis.zrem(processing_key, task_id)

        # Check if should retry
        if task.retry_count <= task.max_retries:
            task.status = TaskStatus.RETRY

            # Add to retry queue with delay
            retry_delay = min(60 * (2**task.retry_count), 3600)  # Exponential backoff, max 1 hour
            retry_time = datetime.now(timezone.utc) + timedelta(seconds=retry_delay)

            retry_key = f"{self.retry_prefix}:{task.agent_type}"
            await self.redis.zadd(retry_key, {task_id: retry_time.timestamp()})

            logger.info(
                f"Retrying task {task_id} in {retry_delay} seconds (attempt {task.retry_count})"
            )
        else:
            task.status = TaskStatus.DEAD
            task.completed_at = datetime.now(timezone.utc)

            # Move to dead letter queue
            dead_key = f"{self.dead_letter_prefix}:{task.agent_type}"
            await self.redis.zadd(dead_key, {task_id: datetime.now(timezone.utc).timestamp()})

            logger.error(
                f"Task {task_id} moved to dead letter queue after {task.retry_count} failures"
            )

        # Update task data
        await self.redis.hset(f"{self.task_data_prefix}:{task_id}", mapping=task.to_dict())

        # Trigger failure event
        await trigger_task_event(
            "task_failed",
            task_id,
            "queue",
            {
                "error": error_message,
                "retry_count": task.retry_count,
                "max_retries": task.max_retries,
            },
            task.user_id,
        )

    async def process_delayed_tasks(self):
        """Process tasks that are ready to be moved from delayed to immediate queues"""
        if not self.redis:
            return

        current_time = datetime.now(timezone.utc).timestamp()

        # Get all agent types with delayed tasks
        delayed_queues = await self.redis.keys(f"{self.queue_prefix}:*:delayed")

        for delayed_queue in delayed_queues:
            # Get tasks ready to be processed
            ready_tasks = await self.redis.zrangebyscore(
                delayed_queue, 0, current_time, withscores=True
            )

            if ready_tasks:
                # Extract agent type from queue name
                agent_type = delayed_queue.split(":")[1]
                immediate_queue = f"{self.queue_prefix}:{agent_type}"

                for task_id, _ in ready_tasks:
                    # Get task data to determine priority
                    task_data = await self.redis.hgetall(f"{self.task_data_prefix}:{task_id}")
                    if task_data:
                        priority = TaskPriority(task_data.get("priority", "normal"))
                        score = self.priority_scores[priority]

                        # Move to immediate queue
                        await self.redis.zadd(immediate_queue, {task_id: score})
                        await self.redis.zrem(delayed_queue, task_id)

                        logger.debug(f"Moved delayed task {task_id} to immediate queue")

    async def process_retry_tasks(self):
        """Process tasks that are ready to be retried"""
        if not self.redis:
            return

        current_time = datetime.now(timezone.utc).timestamp()

        # Get all agent types with retry tasks
        retry_queues = await self.redis.keys(f"{self.retry_prefix}:*")

        for retry_queue in retry_queues:
            # Get tasks ready to be retried
            ready_tasks = await self.redis.zrangebyscore(
                retry_queue, 0, current_time, withscores=True
            )

            if ready_tasks:
                # Extract agent type from queue name
                agent_type = retry_queue.split(":")[1]
                immediate_queue = f"{self.queue_prefix}:{agent_type}"

                for task_id, _ in ready_tasks:
                    # Get task data to determine priority
                    task_data = await self.redis.hgetall(f"{self.task_data_prefix}:{task_id}")
                    if task_data:
                        priority = TaskPriority(task_data.get("priority", "normal"))
                        score = self.priority_scores[priority]

                        # Move to immediate queue
                        await self.redis.zadd(immediate_queue, {task_id: score})
                        await self.redis.zrem(retry_queue, task_id)

                        # Update task status
                        task = QueuedTask.from_dict(task_data)
                        task.status = TaskStatus.QUEUED
                        await self.redis.hset(
                            f"{self.task_data_prefix}:{task_id}", mapping=task.to_dict()
                        )

                        logger.info(f"Moved retry task {task_id} back to queue")

    async def start_workers(self, agent_types: list[str], workers_per_type: int = 2):
        """
        Start background workers to process tasks.

        Args:
            agent_types: List of agent types to process
            workers_per_type: Number of workers per agent type
        """
        if not self.redis or not self.agent_service:
            logger.error("Cannot start workers: Redis or agent service not available")
            return

        self.running = True

        # Start maintenance worker
        self.workers["maintenance"] = asyncio.create_task(self._maintenance_worker())

        # Start workers for each agent type
        for agent_type in agent_types:
            for i in range(workers_per_type):
                worker_id = f"{agent_type}_worker_{i}"
                self.workers[worker_id] = asyncio.create_task(
                    self._task_worker(agent_type, worker_id)
                )

        logger.info(f"Started {len(self.workers)} queue workers")

    async def stop_workers(self):
        """Stop all background workers"""
        self.running = False

        # Cancel all workers
        for worker_id, worker in self.workers.items():
            worker.cancel()
            try:
                await worker
            except asyncio.CancelledError:
                pass

        self.workers.clear()
        logger.info("Stopped all queue workers")

    async def _task_worker(self, agent_type: str, worker_id: str):
        """
        Background worker to process tasks for a specific agent type.

        Args:
            agent_type: Agent type to process
            worker_id: Unique worker identifier
        """
        logger.info(f"Started task worker {worker_id} for {agent_type}")

        while self.running:
            try:
                # Get next task
                task = await self.dequeue_task(agent_type)

                if task:
                    logger.info(f"Worker {worker_id} processing task {task.task_id}")

                    try:
                        # Execute task via agent service
                        result = await self.agent_service.execute_task(
                            task.agent_type, task.task_type, task.task_data, task.user_id
                        )

                        if result["success"]:
                            await self.complete_task(task.task_id, result)
                        else:
                            await self.fail_task(task.task_id, result.get("error", "Unknown error"))

                    except Exception as e:
                        await self.fail_task(task.task_id, str(e))
                        logger.error(f"Worker {worker_id} task execution failed: {e}")

                else:
                    # No tasks available, wait a bit
                    await asyncio.sleep(1)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Worker {worker_id} error: {e}")
                await asyncio.sleep(5)  # Wait before retrying

        logger.info(f"Stopped task worker {worker_id}")

    async def _maintenance_worker(self):
        """Background worker for queue maintenance tasks"""
        logger.info("Started queue maintenance worker")

        while self.running:
            try:
                # Process delayed tasks
                await self.process_delayed_tasks()

                # Process retry tasks
                await self.process_retry_tasks()

                # Clean up old completed tasks (older than 24 hours)
                await self._cleanup_old_tasks()

                # Wait 30 seconds before next maintenance cycle
                await asyncio.sleep(30)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Maintenance worker error: {e}")
                await asyncio.sleep(60)  # Wait before retrying

        logger.info("Stopped queue maintenance worker")

    async def _cleanup_old_tasks(self):
        """Clean up old completed and dead letter tasks"""
        if not self.redis:
            return

        # Clean up tasks older than 24 hours
        cutoff_time = (datetime.now(timezone.utc) - timedelta(hours=24)).timestamp()

        # Clean up dead letter queues
        dead_queues = await self.redis.keys(f"{self.dead_letter_prefix}:*")
        for queue in dead_queues:
            old_tasks = await self.redis.zrangebyscore(queue, 0, cutoff_time)
            if old_tasks:
                # Remove task data
                for task_id in old_tasks:
                    await self.redis.delete(f"{self.task_data_prefix}:{task_id}")

                # Remove from dead letter queue
                await self.redis.zremrangebyscore(queue, 0, cutoff_time)
                logger.debug(f"Cleaned up {len(old_tasks)} old dead letter tasks from {queue}")

    async def get_queue_stats(self) -> dict[str, Any]:
        """Get queue statistics"""
        if not self.redis:
            return {}

        stats = {
            "queues": {},
            "processing": {},
            "retry": {},
            "dead_letter": {},
            "total_pending": 0,
            "total_processing": 0,
            "total_retry": 0,
            "total_dead": 0,
        }

        # Get all queue types
        all_queues = await self.redis.keys(f"{self.queue_prefix}:*")
        all_processing = await self.redis.keys(f"{self.processing_prefix}:*")
        all_retry = await self.redis.keys(f"{self.retry_prefix}:*")
        all_dead = await self.redis.keys(f"{self.dead_letter_prefix}:*")

        # Count tasks in each queue
        for queue in all_queues:
            if ":delayed" not in queue:  # Skip delayed queues for now
                count = await self.redis.zcard(queue)
                agent_type = queue.split(":")[1]
                stats["queues"][agent_type] = count
                stats["total_pending"] += count

        for queue in all_processing:
            count = await self.redis.zcard(queue)
            agent_type = queue.split(":")[1]
            stats["processing"][agent_type] = count
            stats["total_processing"] += count

        for queue in all_retry:
            count = await self.redis.zcard(queue)
            agent_type = queue.split(":")[1]
            stats["retry"][agent_type] = count
            stats["total_retry"] += count

        for queue in all_dead:
            count = await self.redis.zcard(queue)
            agent_type = queue.split(":")[1]
            stats["dead_letter"][agent_type] = count
            stats["total_dead"] += count

        return stats

    async def health_check(self) -> dict[str, Any]:
        """Perform health check on the queue system"""
        if not self.redis:
            return {"healthy": False, "error": "Redis not available"}

        try:
            await self.redis.ping()
            stats = await self.get_queue_stats()

            return {
                "healthy": True,
                "redis_connected": True,
                "workers_running": len(self.workers),
                "queue_stats": stats,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        except Exception as e:
            return {
                "healthy": False,
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }


# Global queue instance
_agent_queue: AgentTaskQueue | None = None


async def get_agent_queue() -> AgentTaskQueue:
    """Get or create global agent queue instance"""
    global _agent_queue
    if _agent_queue is None:
        _agent_queue = AgentTaskQueue()
        await _agent_queue.initialize()
        logger.info("Global agent queue initialized")
    return _agent_queue


async def shutdown_agent_queue():
    """Shutdown global agent queue"""
    global _agent_queue
    if _agent_queue:
        await _agent_queue.stop_workers()
        _agent_queue = None
