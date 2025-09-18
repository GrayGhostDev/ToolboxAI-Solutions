"""
Master Orchestrator for Unified Agent Management

This module provides a centralized orchestrator that manages all agent subsystems,
coordinates task distribution, monitors performance, and ensures system health.

Author: ToolboxAI Team
Created: 2025-09-17
Version: 1.0.0
"""

import asyncio
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Union
from uuid import uuid4

from core.agents.agent_registry import AgentRegistry, AgentFactory, AgentCategory
from core.agents.base_agent import BaseAgent, AgentConfig, TaskResult
from core.agents.worktree_coordinator import WorktreeAgentCoordinator
from core.swarm.message_bus import MessageBus, MessageBusConfig

logger = logging.getLogger(__name__)


class AgentSystemType(Enum):
    """Types of agent systems available."""
    EDUCATIONAL = "educational"
    CONTENT = "content"
    DATABASE = "database"
    GITHUB = "github"
    INTEGRATION = "integration"
    WORKTREE = "worktree"
    NLU = "nlu"
    MONITORING = "monitoring"
    TESTING = "testing"
    REVIEW = "review"


class TaskStatus(Enum):
    """Status of a task in the system."""
    PENDING = "pending"
    QUEUED = "queued"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    DISTRIBUTED = "distributed"
    UNKNOWN = "unknown"


class TaskPriority(Enum):
    """Priority levels for task execution."""
    CRITICAL = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4
    DEFERRED = 5


@dataclass
class OrchestratorConfig:
    """Configuration for the Master Orchestrator."""
    max_agents_per_type: int = 5
    task_queue_size: int = 1000
    enable_health_checks: bool = True
    health_check_interval: int = 30  # seconds
    enable_metrics: bool = True
    metrics_interval: int = 60  # seconds
    enable_auto_scaling: bool = False
    min_agents: int = 1
    max_agents: int = 10


@dataclass
class TaskInfo:
    """Information about a task in the system."""
    task_id: str
    agent_type: AgentSystemType
    priority: TaskPriority
    data: Dict[str, Any]
    status: TaskStatus = TaskStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    assigned_to: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    retries: int = 0


class MasterOrchestrator:
    """
    Master Orchestrator that unifies all agent management systems.

    Provides centralized control over:
    - Agent registration and discovery
    - Task distribution and load balancing
    - Performance monitoring and optimization
    - Health checks and failure recovery
    - Message bus communication
    - Worktree coordination
    """

    def __init__(self, config: Optional[OrchestratorConfig] = None):
        """Initialize the Master Orchestrator."""
        self.config = config or OrchestratorConfig()
        self.registry = AgentRegistry()
        self.factory = AgentFactory(self.registry)
        self.worktree_coordinator: Optional[WorktreeAgentCoordinator] = None
        self.message_bus: Optional[MessageBus] = None

        # Task management
        self.task_queue: asyncio.Queue = asyncio.Queue(maxsize=self.config.task_queue_size)
        self.active_tasks: Dict[str, TaskInfo] = {}
        self.completed_tasks: Dict[str, TaskInfo] = {}
        self.task_history: List[TaskInfo] = []

        # Agent pools by type
        self.agent_pools: Dict[AgentSystemType, List[BaseAgent]] = {
            agent_type: [] for agent_type in AgentSystemType
        }

        # Metrics
        self.metrics = {
            "total_tasks_processed": 0,
            "successful_tasks": 0,
            "failed_tasks": 0,
            "average_processing_time": 0.0,
            "agent_utilization": {},
            "system_health": "healthy"
        }

        # Background tasks
        self.background_tasks: List[asyncio.Task] = []
        self.is_running = False

        logger.info("Master Orchestrator initialized")

    async def initialize(self):
        """Initialize all subsystems."""
        try:
            # Registry auto-discovers agents on initialization
            logger.info(f"Discovered {len(self.registry.registered_agents)} agents")

            # Initialize agent pools
            await self._initialize_agent_pools()

            # Initialize worktree coordinator
            self.worktree_coordinator = WorktreeAgentCoordinator(self)

            # Initialize message bus
            self._initialize_message_bus()

            logger.info("Master Orchestrator fully initialized")

        except Exception as e:
            logger.error(f"Failed to initialize orchestrator: {e}")
            raise

    def _initialize_message_bus(self):
        """Initialize the message bus for inter-agent communication."""
        try:
            bus_config = MessageBusConfig(
                max_queue_size=1000,
                processing_timeout=60,
                retry_attempts=3,
                enable_logging=True
            )
            self.message_bus = MessageBus(bus_config)
            logger.info("Message bus initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize message bus: {e}")
            self.message_bus = None

    async def _initialize_agent_pools(self):
        """Initialize agent pools for each system type."""
        # Import CompleteSupervisorAgent for content category
        from core.agents.supervisor_complete import CompleteSupervisorAgent

        for agent_type in AgentSystemType:
            # Special handling for content type - use supervisor
            if agent_type == AgentSystemType.CONTENT:
                try:
                    # Create a CompleteSupervisorAgent for content tasks
                    supervisor = CompleteSupervisorAgent()
                    self.agent_pools[agent_type].append(supervisor)
                    logger.info(f"Added CompleteSupervisorAgent to {agent_type.value} pool")
                except Exception as e:
                    logger.error(f"Failed to create CompleteSupervisorAgent: {e}")
            else:
                # Find agents matching this type
                matching_agents = [
                    name for name, metadata in self.registry.registered_agents.items()
                    if metadata.category.value == agent_type.value
                ]

                # Create initial pool
                for agent_name in matching_agents[:self.config.max_agents_per_type]:
                    try:
                        agent = self.factory.create_agent(agent_name)
                        if agent:
                            self.agent_pools[agent_type].append(agent)
                            logger.debug(f"Added {agent_name} to {agent_type.value} pool")
                    except Exception as e:
                        logger.error(f"Failed to create agent {agent_name}: {e}")

            logger.info(f"Initialized {len(self.agent_pools[agent_type])} agents for {agent_type.value}")

    async def submit_task(
        self,
        agent_type: AgentSystemType,
        task_data: Dict[str, Any],
        priority: TaskPriority = TaskPriority.MEDIUM
    ) -> str:
        """
        Submit a task to the orchestrator for processing.

        Args:
            agent_type: Type of agent system to handle the task
            task_data: Task-specific data
            priority: Priority level for the task

        Returns:
            Task ID for tracking
        """
        task_id = str(uuid4())

        task_info = TaskInfo(
            task_id=task_id,
            agent_type=agent_type,
            priority=priority,
            data=task_data
        )

        # Add to queue based on priority
        await self.task_queue.put((priority.value, task_info))
        self.active_tasks[task_id] = task_info

        logger.info(f"Task {task_id} submitted for {agent_type.value} processing")

        return task_id

    async def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """Get the status of a submitted task."""
        if task_id in self.active_tasks:
            task = self.active_tasks[task_id]
        elif task_id in self.completed_tasks:
            task = self.completed_tasks[task_id]
        else:
            return {"status": TaskStatus.UNKNOWN, "error": "Task not found"}

        return {
            "status": task.status,
            "agent_type": task.agent_type.value,
            "created_at": task.created_at.isoformat(),
            "started_at": task.started_at.isoformat() if task.started_at else None,
            "completed_at": task.completed_at.isoformat() if task.completed_at else None,
            "result": task.result,
            "error": task.error
        }

    async def get_statistics(self) -> Dict[str, Any]:
        """Get orchestrator statistics."""
        active_count = len(self.active_tasks)
        completed_count = len(self.completed_tasks)
        queued_count = self.task_queue.qsize()

        # Calculate agent utilization
        agent_utilization = {}
        for agent_type, agents in self.agent_pools.items():
            if agents:
                busy_count = sum(1 for agent in agents if hasattr(agent, 'is_busy') and agent.is_busy)
                agent_utilization[agent_type.value] = busy_count / len(agents)

        return {
            "active_tasks": active_count,
            "completed_tasks": completed_count,
            "queued_tasks": queued_count,
            "total_tasks_processed": self.metrics["total_tasks_processed"],
            "successful_tasks": self.metrics["successful_tasks"],
            "failed_tasks": self.metrics["failed_tasks"],
            "average_processing_time": self.metrics["average_processing_time"],
            "agent_utilization": agent_utilization,
            "system_health": self.metrics["system_health"],
            "uptime": (datetime.now() - self.start_time).total_seconds() if hasattr(self, 'start_time') else 0
        }

    async def _assign_task_to_agent(self, task: TaskInfo) -> Optional[BaseAgent]:
        """Assign a task to an available agent."""
        agent_pool = self.agent_pools.get(task.agent_type, [])

        if not agent_pool:
            logger.warning(f"No agents available for {task.agent_type.value}")

            # Try to create a new agent if possible
            if self.config.enable_auto_scaling:
                agent = await self._create_agent_for_type(task.agent_type)
                if agent:
                    agent_pool.append(agent)
                    return agent
            return None

        # Find an available agent (simple round-robin for now)
        for agent in agent_pool:
            if not hasattr(agent, 'is_busy') or not agent.is_busy:
                return agent

        # All agents busy - wait or scale
        if self.config.enable_auto_scaling and len(agent_pool) < self.config.max_agents:
            agent = await self._create_agent_for_type(task.agent_type)
            if agent:
                agent_pool.append(agent)
                return agent

        # Return least loaded agent
        return agent_pool[0]

    async def _create_agent_for_type(self, agent_type: AgentSystemType) -> Optional[BaseAgent]:
        """Create a new agent for the specified type."""
        matching_agents = [
            name for name, metadata in self.registry.registered_agents.items()
            if metadata.category.value == agent_type.value
        ]

        if not matching_agents:
            return None

        # Create the first available agent type
        try:
            agent = self.factory.create_agent(matching_agents[0])
            logger.info(f"Auto-scaled: Created new {matching_agents[0]} agent")
            return agent
        except Exception as e:
            logger.error(f"Failed to auto-scale agent: {e}")
            return None

    async def start(self):
        """Start the orchestrator and all background tasks."""
        if self.is_running:
            logger.warning("Orchestrator is already running")
            return

        self.is_running = True
        logger.info("Starting Master Orchestrator")

        # Start background tasks
        if self.config.enable_health_checks:
            self.background_tasks.append(
                asyncio.create_task(self._health_check_loop())
            )

        self.background_tasks.append(
            asyncio.create_task(self._task_processor_loop())
        )

        if self.config.enable_metrics:
            self.background_tasks.append(
                asyncio.create_task(self._metrics_collector_loop())
            )

        # Message bus doesn't need explicit starting

        logger.info("Master Orchestrator started successfully")

    async def stop(self):
        """Stop the orchestrator and cleanup resources."""
        if not self.is_running:
            return

        logger.info("Stopping Master Orchestrator")
        self.is_running = False

        # Cancel background tasks
        for task in self.background_tasks:
            task.cancel()

        await asyncio.gather(*self.background_tasks, return_exceptions=True)

        # Message bus doesn't need explicit stopping

        # Cleanup agent pools
        for agent_type in self.agent_pools:
            for agent in self.agent_pools[agent_type]:
                try:
                    if hasattr(agent, 'cleanup'):
                        await agent.cleanup()
                except Exception as e:
                    logger.error(f"Error cleaning up agent: {e}")

        logger.info("Master Orchestrator stopped")

    async def _task_processor_loop(self):
        """Background loop for processing tasks from the queue."""
        while self.is_running:
            try:
                # Get task from queue (with timeout to allow checking is_running)
                priority, task = await asyncio.wait_for(
                    self.task_queue.get(),
                    timeout=1.0
                )

                # Update task status
                task.status = TaskStatus.ASSIGNED
                task.started_at = datetime.now()

                # Assign to agent
                agent = await self._assign_task_to_agent(task)
                if not agent:
                    task.status = TaskStatus.FAILED
                    task.error = "No agent available"
                    self.completed_tasks[task.task_id] = task
                    del self.active_tasks[task.task_id]
                    continue

                task.assigned_to = agent.config.name if hasattr(agent, 'config') else str(agent)
                task.status = TaskStatus.IN_PROGRESS

                # Execute task
                try:
                    # Convert task data to proper format for agent execution
                    # The agent expects a task string and optional context dictionary
                    task_description = task.data.get("description",
                                                    task.data.get("type",
                                                    f"Process {task.agent_type.value} task"))

                    # Pass the rest of task.data as context
                    context = {k: v for k, v in task.data.items() if k not in ["description", "type"]}
                    context["agent_type"] = task.agent_type.value
                    context["task_id"] = task.task_id
                    context["priority"] = task.priority.value

                    result = await agent.execute(task_description, context)

                    if result.success:
                        task.status = TaskStatus.COMPLETED
                        task.result = result.output
                        self.metrics["successful_tasks"] += 1
                    else:
                        task.status = TaskStatus.FAILED
                        task.error = result.error
                        self.metrics["failed_tasks"] += 1

                except Exception as e:
                    task.status = TaskStatus.FAILED
                    task.error = str(e)
                    self.metrics["failed_tasks"] += 1
                    logger.error(f"Task {task.task_id} failed: {e}")

                # Update metrics
                task.completed_at = datetime.now()
                processing_time = (task.completed_at - task.started_at).total_seconds()
                self._update_average_processing_time(processing_time)

                # Move to completed
                self.completed_tasks[task.task_id] = task
                del self.active_tasks[task.task_id]
                self.metrics["total_tasks_processed"] += 1

                # Keep history limited
                self.task_history.append(task)
                if len(self.task_history) > 1000:
                    self.task_history = self.task_history[-500:]

            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Error in task processor loop: {e}")
                await asyncio.sleep(1)

    def _update_average_processing_time(self, new_time: float):
        """Update the running average of processing time."""
        current_avg = self.metrics["average_processing_time"]
        total_tasks = self.metrics["total_tasks_processed"]

        if total_tasks == 0:
            self.metrics["average_processing_time"] = new_time
        else:
            # Calculate new average
            self.metrics["average_processing_time"] = (
                (current_avg * (total_tasks - 1) + new_time) / total_tasks
            )

    async def _health_check_loop(self):
        """Background loop for health checking."""
        while self.is_running:
            try:
                await self._perform_health_check()
                await asyncio.sleep(self.config.health_check_interval)
            except Exception as e:
                logger.error(f"Error in health check loop: {e}")
                await asyncio.sleep(5)

    async def _perform_health_check(self):
        """Perform health check on all subsystems."""
        health_status = "healthy"
        issues = []

        # Check agent pools
        for agent_type, agents in self.agent_pools.items():
            if not agents:
                issues.append(f"No agents in {agent_type.value} pool")
                health_status = "degraded"

        # Check task queue
        if self.task_queue.full():
            issues.append("Task queue is full")
            health_status = "degraded"

        # Check message bus
        if self.message_bus:
            bus_stats = self.message_bus.get_stats()
            if bus_stats.get("messages_failed", 0) > 100:
                issues.append("High message failure rate")
                health_status = "unhealthy"

        # Update metrics
        self.metrics["system_health"] = health_status

        if issues:
            logger.warning(f"Health check issues: {', '.join(issues)}")

    async def _metrics_collector_loop(self):
        """Background loop for collecting metrics."""
        self.start_time = datetime.now()

        while self.is_running:
            try:
                # Collect metrics from all subsystems
                metrics = await self.get_statistics()

                # Log metrics
                logger.debug(f"System metrics: {json.dumps(metrics)}")

                await asyncio.sleep(self.config.metrics_interval)

            except Exception as e:
                logger.error(f"Error in metrics collector loop: {e}")
                await asyncio.sleep(5)