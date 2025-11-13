"""
Agent Service Layer - Manages agent lifecycle and execution

This service provides a centralized interface for managing all AI agents,
handling their lifecycle, execution, and integration with the application.

Features:
- Agent instance management and lifecycle
- Task execution and routing
- Performance monitoring and metrics
- Error handling and recovery
- Real-time status updates

Author: ToolboxAI Team
Created: 2025-09-21
Version: 1.0.0
"""

import asyncio
import logging
import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any

# Import agent classes
from apps.backend.agents.agent_classes import (
    CodeReviewAgent,
    ContentGenerationAgent,
    QuizGenerationAgent,
    ScriptGenerationAgent,
    TerrainGenerationAgent,
)

# Import Roblox agents with compatibility handling
try:
    from core.agents.roblox.roblox_analytics_agent import RobloxAnalyticsAgent
    from core.agents.roblox.roblox_asset_management_agent import (
        RobloxAssetManagementAgent,
    )
    from core.agents.roblox.roblox_testing_agent import RobloxTestingAgent

    ROBLOX_AGENTS_AVAILABLE = True
    logging.info("Roblox agents imported successfully")
except ImportError as e:
    logging.warning(f"Roblox agents not available: {e}")
    ROBLOX_AGENTS_AVAILABLE = False
except Exception as e:
    logging.error(f"Failed to import Roblox agents: {e}")
    ROBLOX_AGENTS_AVAILABLE = False

# Import Supabase and services
try:
    from apps.backend.services.pusher import (
        trigger_agent_event,
        trigger_agent_status_change,
        trigger_event,
        trigger_metrics_update,
        trigger_task_event,
    )
    from apps.backend.services.supabase_service import (
        SupabaseService,
        get_supabase_service,
    )

    SUPABASE_AVAILABLE = True
except ImportError as e:
    logging.warning(f"Supabase services not available: {e}")
    SUPABASE_AVAILABLE = False

    def get_supabase_service():
        return None

    async def trigger_event(channel, event, data):
        pass

    async def trigger_agent_event(event_type, agent_id, data, user_id=None):
        pass

    async def trigger_task_event(event_type, task_id, agent_id, data, user_id=None):
        pass

    async def trigger_metrics_update(metrics_data, agent_id=None):
        pass

    async def trigger_agent_status_change(agent_id, old_status, new_status, additional_data=None):
        pass


logger = logging.getLogger(__name__)


class AgentStatus(str, Enum):
    """Agent operational status"""

    INITIALIZING = "initializing"
    IDLE = "idle"
    BUSY = "busy"
    PROCESSING = "processing"
    WAITING = "waiting"
    ERROR = "error"
    OFFLINE = "offline"
    MAINTENANCE = "maintenance"


class TaskStatus(str, Enum):
    """Task execution status"""

    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRYING = "retrying"


class AgentInfo:
    """Agent information container"""

    def __init__(self, agent_id: str, agent_type: str, agent_instance):
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.agent_instance = agent_instance
        self.status = AgentStatus.INITIALIZING
        self.current_task_id: str | None = None
        self.total_tasks_completed = 0
        self.total_tasks_failed = 0
        self.average_execution_time = 0.0
        self.last_activity = datetime.now(timezone.utc)
        self.created_at = datetime.now(timezone.utc)
        self.performance_metrics = {
            "uptime": 100.0,
            "throughput": 0.0,
            "error_rate": 0.0,
            "success_rate": 100.0,
        }
        self.resource_usage = {"cpu_percent": 0.0, "memory_mb": 0, "gpu_percent": 0.0}


class TaskInfo:
    """Task information container"""

    def __init__(self, task_id: str, agent_type: str, task_type: str, task_data: dict[str, Any]):
        self.task_id = task_id
        self.agent_type = agent_type
        self.task_type = task_type
        self.task_data = task_data
        self.status = TaskStatus.PENDING
        self.result: dict[str, Any] | None = None
        self.error_message: str | None = None
        self.created_at = datetime.now(timezone.utc)
        self.started_at: datetime | None = None
        self.completed_at: datetime | None = None
        self.execution_time_seconds: float | None = None
        self.retry_count = 0
        self.max_retries = 3


class AgentService:
    """
    Central service for managing all AI agents in the application.

    Provides:
    - Agent lifecycle management
    - Task execution and routing
    - Performance monitoring
    - Error handling and recovery
    - Real-time status updates
    """

    def __init__(self):
        self.agents: dict[str, AgentInfo] = {}
        self.tasks: dict[str, TaskInfo] = {}
        self.task_queue: list[str] = []
        self.supabase_service: SupabaseService | None = None
        self._initialize_agents()
        self._setup_database()

    def _setup_database(self):
        """Setup Supabase connection if available"""
        if SUPABASE_AVAILABLE:
            try:
                self.supabase_service = get_supabase_service()
                logger.info("Supabase service connected for agent system")
            except Exception as e:
                logger.warning(f"Could not setup Supabase service: {e}")
                self.supabase_service = None
        else:
            self.supabase_service = None

    def _initialize_agents(self):
        """Initialize all agent instances"""
        try:
            # Initialize core agents
            core_agents = [
                ("content_generator", ContentGenerationAgent()),
                ("quiz_generator", QuizGenerationAgent()),
                ("terrain_generator", TerrainGenerationAgent()),
                ("script_generator", ScriptGenerationAgent()),
                ("code_reviewer", CodeReviewAgent()),
            ]

            for agent_type, agent_instance in core_agents:
                agent_id = f"agent_{agent_type}_{uuid.uuid4().hex[:8]}"
                agent_info = AgentInfo(agent_id, agent_type, agent_instance)
                agent_info.status = AgentStatus.IDLE
                self.agents[agent_id] = agent_info

                # Persist agent to Supabase if available
                if self.supabase_service and self.supabase_service.is_available():
                    asyncio.create_task(self._persist_agent_to_supabase(agent_info))

                logger.info(f"Initialized agent: {agent_id} ({agent_type})")

            # Initialize Roblox agents if available
            if ROBLOX_AGENTS_AVAILABLE:
                roblox_agents = [
                    ("roblox_asset", RobloxAssetManagementAgent()),
                    ("roblox_testing", RobloxTestingAgent()),
                    ("roblox_analytics", RobloxAnalyticsAgent()),
                ]

                for agent_type, agent_instance in roblox_agents:
                    agent_id = f"agent_{agent_type}_{uuid.uuid4().hex[:8]}"
                    agent_info = AgentInfo(agent_id, agent_type, agent_instance)
                    agent_info.status = AgentStatus.IDLE
                    self.agents[agent_id] = agent_info

                    # Persist agent to Supabase if available
                    if self.supabase_service and self.supabase_service.is_available():
                        asyncio.create_task(self._persist_agent_to_supabase(agent_info))

                    logger.info(f"Initialized Roblox agent: {agent_id} ({agent_type})")

            logger.info(f"Agent service initialized with {len(self.agents)} agents")

        except Exception as e:
            logger.error(f"Error initializing agents: {e}")
            raise

    async def _persist_agent_to_supabase(self, agent_info: AgentInfo):
        """Persist agent information to Supabase"""
        if not self.supabase_service or not self.supabase_service.is_available():
            return

        try:
            agent_data = {
                "agent_id": agent_info.agent_id,
                "agent_type": agent_info.agent_type,
                "status": agent_info.status.value,
                "configuration": {
                    "initialized_at": agent_info.created_at.isoformat(),
                    "agent_class": agent_info.agent_instance.__class__.__name__,
                },
                "resource_limits": {"max_memory_mb": 1024, "max_cpu_percent": 80},
                "performance_thresholds": {"min_quality_score": 0.85, "max_execution_time": 30},
            }

            await self.supabase_service.create_agent_instance(agent_data)
            logger.debug(f"Persisted agent {agent_info.agent_id} to Supabase")

        except Exception as e:
            logger.warning(f"Failed to persist agent {agent_info.agent_id} to Supabase: {e}")

    async def _persist_task_to_supabase(
        self, task_info: TaskInfo, agent_id: str, user_id: str | None = None
    ):
        """Persist task execution to Supabase"""
        if not self.supabase_service or not self.supabase_service.is_available():
            return None

        try:
            # Get agent instance ID from Supabase
            agent_instance = await self.supabase_service.get_agent_instance(agent_id)
            if not agent_instance:
                logger.warning(f"Agent {agent_id} not found in Supabase for task persistence")
                return None

            task_data = {
                "task_id": task_info.task_id,
                "agent_instance_id": agent_instance["id"],
                "agent_type": task_info.agent_type,
                "task_type": task_info.task_type,
                "priority": "normal",
                "input_data": task_info.task_data,
                "context_data": {"created_by_service": "agent_service", "service_version": "1.0.0"},
                "status": "pending",
                "user_id": user_id,
                "session_id": f"session_{uuid.uuid4().hex[:8]}",
            }

            result = await self.supabase_service.create_task_execution(task_data)
            logger.debug(f"Persisted task {task_info.task_id} to Supabase")
            return result

        except Exception as e:
            logger.warning(f"Failed to persist task {task_info.task_id} to Supabase: {e}")
            return None

    async def _update_task_in_supabase(self, task_id: str, updates: dict[str, Any]):
        """Update task execution status in Supabase"""
        if not self.supabase_service or not self.supabase_service.is_available():
            return

        try:
            await self.supabase_service.update_task_execution(task_id, updates)
            logger.debug(f"Updated task {task_id} in Supabase")

        except Exception as e:
            logger.warning(f"Failed to update task {task_id} in Supabase: {e}")

    async def _store_agent_metrics_to_supabase(self, agent_id: str, metrics: dict[str, Any]):
        """Store agent performance metrics to Supabase"""
        if not self.supabase_service or not self.supabase_service.is_available():
            return

        try:
            # Get agent instance from Supabase
            agent_instance = await self.supabase_service.get_agent_instance(agent_id)
            if not agent_instance:
                return

            # Get agent info
            agent_info = self.agents.get(agent_id)
            if not agent_info:
                return

            # Prepare metrics data
            from datetime import datetime, timezone

            now = datetime.now(timezone.utc)

            metrics_data = {
                "agent_instance_id": agent_instance["id"],
                "agent_type": agent_info.agent_type,
                "period_start": (now.replace(minute=0, second=0, microsecond=0)).isoformat(),
                "period_end": now.isoformat(),
                "period_duration_minutes": 60,
                "tasks_completed": metrics.get("tasks_completed", 0),
                "tasks_failed": metrics.get("tasks_failed", 0),
                "success_rate": metrics.get("success_rate", 0.0),
                "error_rate": metrics.get("error_rate", 0.0),
                "average_execution_time": metrics.get("average_execution_time", 0.0),
                "average_quality_score": metrics.get("average_quality_score", 0.0),
                "uptime_percentage": metrics.get("uptime_percentage", 100.0),
            }

            await self.supabase_service.store_agent_metrics(metrics_data)
            logger.debug(f"Stored metrics for agent {agent_id} to Supabase")

        except Exception as e:
            logger.warning(f"Failed to store metrics for agent {agent_id} to Supabase: {e}")

    async def list_agents(self) -> list[dict[str, Any]]:
        """
        List all available agents with their current status.

        Returns:
            List of agent dictionaries with id, name, status, and type
        """
        agents_list = []
        for agent_id, agent_info in self.agents.items():
            agents_list.append(
                {
                    "id": agent_id,
                    "name": agent_info.agent_type.replace("_", " ").title(),
                    "status": "active" if agent_info.status == AgentStatus.IDLE else "inactive",
                    "type": agent_info.agent_type.upper(),
                }
            )
        return agents_list

    async def execute_task(
        self,
        agent_type: str,
        task_type: str,
        task_data: dict[str, Any],
        user_id: str | None = None,
    ) -> dict[str, Any]:
        """
        Execute a task on a specific agent type.

        Args:
            agent_type: Type of agent to use
            task_type: Type of task to execute
            task_data: Data for the task
            user_id: ID of user requesting the task

        Returns:
            Task execution result
        """
        try:
            # Create task
            task_id = str(uuid.uuid4())
            task = TaskInfo(task_id, agent_type, task_type, task_data)
            self.tasks[task_id] = task

            # Find available agent
            agent_id = self._find_available_agent(agent_type)
            if not agent_id:
                # Queue task if no agent available
                self.task_queue.append(task_id)
                task.status = TaskStatus.QUEUED

                # Persist queued task to Supabase
                await self._persist_task_to_supabase(task, "queued", user_id)

                return {
                    "success": False,
                    "task_id": task_id,
                    "status": "queued",
                    "message": f"No available {agent_type} agent. Task queued.",
                }

            # Persist task to Supabase before execution
            supabase_task = await self._persist_task_to_supabase(task, agent_id, user_id)

            # Execute task
            result = await self._execute_task_on_agent(task_id, agent_id, user_id)

            # Update task status in Supabase
            if supabase_task and result.get("success"):
                await self._update_task_in_supabase(
                    task_id,
                    {
                        "status": "completed",
                        "output_data": result,
                        "completed_at": datetime.now(timezone.utc).isoformat(),
                        "quality_score": result.get("quality_score", 0.0),
                        "execution_time_seconds": result.get("execution_time", 0.0),
                    },
                )
            elif supabase_task:
                await self._update_task_in_supabase(
                    task_id,
                    {
                        "status": "failed",
                        "error_message": result.get("error", "Unknown error"),
                        "completed_at": datetime.now(timezone.utc).isoformat(),
                    },
                )

            return result

        except Exception as e:
            logger.error(f"Error executing task: {e}")
            return {"success": False, "error": str(e), "message": "Task execution failed"}

    def _find_available_agent(self, agent_type: str) -> str | None:
        """Find an available agent of the specified type"""
        for agent_id, agent_info in self.agents.items():
            if agent_info.agent_type == agent_type and agent_info.status == AgentStatus.IDLE:
                return agent_id
        return None

    async def _execute_task_on_agent(
        self, task_id: str, agent_id: str, user_id: str | None = None
    ) -> dict[str, Any]:
        """Execute a specific task on a specific agent"""
        task = self.tasks.get(task_id)
        agent = self.agents.get(agent_id)

        if not task or not agent:
            return {"success": False, "error": "Task or agent not found"}

        try:
            # Update task and agent status
            task.status = TaskStatus.RUNNING
            task.started_at = datetime.now(timezone.utc)
            agent.status = AgentStatus.BUSY
            agent.current_task_id = task_id
            agent.last_activity = datetime.now(timezone.utc)

            # Notify status update via Pusher
            await trigger_task_event(
                "task_started",
                task_id,
                agent_id,
                {"task_type": task.task_type, "agent_type": agent.agent_type},
                user_id,
            )

            # Route task to appropriate agent method
            result = await self._route_task_to_agent_method(agent, task)

            # Update task completion
            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.now(timezone.utc)
            task.execution_time_seconds = (task.completed_at - task.started_at).total_seconds()
            task.result = result

            # Update agent status and metrics
            agent.status = AgentStatus.IDLE
            agent.current_task_id = None
            agent.total_tasks_completed += 1
            agent.last_activity = datetime.now(timezone.utc)

            # Update performance metrics
            self._update_agent_metrics(agent, task.execution_time_seconds, True)

            # Store execution in database if available
            await self._store_execution_record(task, agent_id, user_id, True)

            # Notify completion via Pusher
            await trigger_task_event(
                "task_completed",
                task_id,
                agent_id,
                {
                    "execution_time": task.execution_time_seconds,
                    "result": result,
                    "quality_score": result.get("quality_score", 0) if result else 0,
                },
                user_id,
            )

            # Process queued tasks
            await self._process_task_queue()

            return {
                "success": True,
                "task_id": task_id,
                "result": result,
                "execution_time": task.execution_time_seconds,
                "agent_id": agent_id,
            }

        except Exception as e:
            # Handle task failure
            task.status = TaskStatus.FAILED
            task.error_message = str(e)
            task.completed_at = datetime.now(timezone.utc)

            agent.status = AgentStatus.IDLE
            agent.current_task_id = None
            agent.total_tasks_failed += 1

            # Update performance metrics
            execution_time = (
                (task.completed_at - task.started_at).total_seconds() if task.started_at else 0
            )
            self._update_agent_metrics(agent, execution_time, False)

            # Store execution record
            await self._store_execution_record(task, agent_id, user_id, False)

            # Notify failure via Pusher
            await trigger_task_event(
                "task_failed",
                task_id,
                agent_id,
                {"error": str(e), "execution_time": execution_time},
                user_id,
            )

            logger.error(f"Task {task_id} failed on agent {agent_id}: {e}")

            return {"success": False, "task_id": task_id, "error": str(e), "agent_id": agent_id}

    async def _route_task_to_agent_method(self, agent: AgentInfo, task: TaskInfo) -> dict[str, Any]:
        """Route task to appropriate agent method based on agent type"""
        agent_instance = agent.agent_instance
        task_data = task.task_data

        try:
            if agent.agent_type == "content":
                return await agent_instance.generate_content(
                    subject=task_data.get("subject", "General"),
                    grade_level=task_data.get("grade_level", 5),
                    objectives=task_data.get("objectives", ["Learn the topic"]),
                )

            elif agent.agent_type == "quiz":
                return await agent_instance.generate_quiz(
                    subject=task_data.get("subject", "General"),
                    objectives=task_data.get("objectives", ["Test knowledge"]),
                    num_questions=task_data.get("num_questions", 5),
                    difficulty=task_data.get("difficulty", "medium"),
                )

            elif agent.agent_type == "terrain":
                return await agent_instance.generate_terrain(
                    subject=task_data.get("subject", "General"),
                    terrain_type=task_data.get("terrain_type", "educational"),
                    complexity=task_data.get("complexity", "medium"),
                    features=task_data.get("features", []),
                )

            elif agent.agent_type == "script":
                return await agent_instance.generate_script(
                    script_type=task_data.get("script_type", "ServerScript"),
                    functionality=task_data.get("functionality", "Basic script"),
                    requirements=task_data.get("requirements", []),
                    context=task_data.get("context", {}),
                )

            elif agent.agent_type == "code_review":
                return await agent_instance.review_code(
                    code=task_data.get("code", ""),
                    language=task_data.get("language", "lua"),
                    review_type=task_data.get("review_type", "comprehensive"),
                )

            # Roblox agents
            elif agent.agent_type == "roblox_asset" and ROBLOX_AGENTS_AVAILABLE:
                return await agent_instance.manage_asset(
                    asset_type=task_data.get("asset_type", "model"),
                    action=task_data.get("action", "create"),
                    asset_data=task_data.get("asset_data", {}),
                )

            elif agent.agent_type == "roblox_testing" and ROBLOX_AGENTS_AVAILABLE:
                return await agent_instance.run_tests(
                    test_type=task_data.get("test_type", "functional"),
                    test_data=task_data.get("test_data", {}),
                )

            elif agent.agent_type == "roblox_analytics" and ROBLOX_AGENTS_AVAILABLE:
                return await agent_instance.analyze_data(
                    data_type=task_data.get("data_type", "player_behavior"),
                    analysis_data=task_data.get("analysis_data", {}),
                )

            else:
                raise ValueError(f"Unknown agent type: {agent.agent_type}")

        except Exception as e:
            logger.error(f"Error routing task to agent method: {e}")
            raise

    def _update_agent_metrics(self, agent: AgentInfo, execution_time: float, success: bool):
        """Update agent performance metrics"""
        total_tasks = agent.total_tasks_completed + agent.total_tasks_failed

        if total_tasks > 0:
            # Update success rate
            agent.performance_metrics["success_rate"] = (
                agent.total_tasks_completed / total_tasks * 100
            )

            # Update error rate
            agent.performance_metrics["error_rate"] = agent.total_tasks_failed / total_tasks * 100

            # Update average execution time
            if success and execution_time > 0:
                current_avg = agent.average_execution_time
                agent.average_execution_time = (
                    current_avg * (agent.total_tasks_completed - 1) + execution_time
                ) / agent.total_tasks_completed

            # Update throughput (tasks per minute)
            uptime_minutes = (datetime.now(timezone.utc) - agent.created_at).total_seconds() / 60
            if uptime_minutes > 0:
                agent.performance_metrics["throughput"] = total_tasks / uptime_minutes

    async def _store_execution_record(
        self, task: TaskInfo, agent_id: str, user_id: str | None, success: bool
    ):
        """Store task execution record in Supabase"""
        if not self.supabase_service or not self.supabase_service.is_available():
            logger.debug("Supabase not available for storing execution record")
            return

        try:
            # Get agent instance ID from Supabase
            agent_instance = await self.supabase_service.get_agent_instance(agent_id)
            agent_instance_id = agent_instance["id"] if agent_instance else None

            execution_record = {
                "task_id": task.task_id,
                "agent_instance_id": agent_instance_id,
                "agent_type": task.agent_type,
                "task_type": task.task_type,
                "input_data": task.task_data,
                "output_data": task.result,
                "execution_time_seconds": task.execution_time_seconds,
                "status": "completed" if success else "failed",
                "error_message": task.error_message,
                "quality_score": task.result.get("quality_score", 0) if task.result else 0,
                "user_id": user_id,
                "created_at": task.created_at.isoformat() if task.created_at else None,
                "started_at": task.started_at.isoformat() if task.started_at else None,
                "completed_at": task.completed_at.isoformat() if task.completed_at else None,
                "retry_count": task.retry_count,
                "max_retries": task.max_retries,
            }

            await self.supabase_service.create_task_execution(execution_record)
            logger.debug(f"Stored execution record in Supabase: {task.task_id}")

        except Exception as e:
            logger.warning(f"Could not store execution record in Supabase: {e}")

    async def _notify_status_update(self, agent_id: str, event_type: str, data: dict[str, Any]):
        """Send real-time status updates via Pusher (legacy method - use trigger_agent_event instead)"""
        try:
            await trigger_agent_event(event_type, agent_id, data, data.get("user_id"))
        except Exception as e:
            logger.warning(f"Could not send status update: {e}")

    async def _notify_agent_status_change(
        self,
        agent_id: str,
        old_status: str,
        new_status: str,
        additional_data: dict[str, Any] | None = None,
    ):
        """Notify about agent status changes via Pusher"""
        try:
            await trigger_agent_status_change(agent_id, old_status, new_status, additional_data)
        except Exception as e:
            logger.warning(f"Could not send agent status change notification: {e}")

    async def _process_task_queue(self):
        """Process queued tasks when agents become available"""
        if not self.task_queue:
            return

        # Process one task from queue
        task_id = self.task_queue.pop(0)
        task = self.tasks.get(task_id)

        if task and task.status == TaskStatus.QUEUED:
            agent_id = self._find_available_agent(task.agent_type)
            if agent_id:
                # Execute queued task
                await self._execute_task_on_agent(task_id, agent_id)

    # Public API methods

    def get_agent_status(self, agent_id: str) -> dict[str, Any] | None:
        """Get status of specific agent"""
        agent = self.agents.get(agent_id)
        if not agent:
            return None

        return {
            "agent_id": agent.agent_id,
            "agent_type": agent.agent_type,
            "status": agent.status.value,
            "current_task_id": agent.current_task_id,
            "total_tasks_completed": agent.total_tasks_completed,
            "total_tasks_failed": agent.total_tasks_failed,
            "average_execution_time": agent.average_execution_time,
            "last_activity": agent.last_activity.isoformat(),
            "created_at": agent.created_at.isoformat(),
            "performance_metrics": agent.performance_metrics,
            "resource_usage": agent.resource_usage,
        }

    def get_all_agents_status(self) -> list[dict[str, Any]]:
        """Get status of all agents"""
        return [self.get_agent_status(agent_id) for agent_id in self.agents.keys()]

    def get_task_status(self, task_id: str) -> dict[str, Any] | None:
        """Get status of specific task"""
        task = self.tasks.get(task_id)
        if not task:
            return None

        return {
            "task_id": task.task_id,
            "agent_type": task.agent_type,
            "task_type": task.task_type,
            "status": task.status.value,
            "result": task.result,
            "error_message": task.error_message,
            "created_at": task.created_at.isoformat(),
            "started_at": task.started_at.isoformat() if task.started_at else None,
            "completed_at": task.completed_at.isoformat() if task.completed_at else None,
            "execution_time_seconds": task.execution_time_seconds,
            "retry_count": task.retry_count,
        }

    def get_system_metrics(self) -> dict[str, Any]:
        """Get overall system metrics"""
        total_agents = len(self.agents)
        idle_agents = len([a for a in self.agents.values() if a.status == AgentStatus.IDLE])
        busy_agents = len([a for a in self.agents.values() if a.status == AgentStatus.BUSY])
        error_agents = len([a for a in self.agents.values() if a.status == AgentStatus.ERROR])

        total_tasks = len(self.tasks)
        completed_tasks = len([t for t in self.tasks.values() if t.status == TaskStatus.COMPLETED])
        failed_tasks = len([t for t in self.tasks.values() if t.status == TaskStatus.FAILED])
        running_tasks = len([t for t in self.tasks.values() if t.status == TaskStatus.RUNNING])

        return {
            "agents": {
                "total": total_agents,
                "idle": idle_agents,
                "busy": busy_agents,
                "error": error_agents,
                "utilization_rate": (busy_agents / max(total_agents, 1)) * 100,
            },
            "tasks": {
                "total": total_tasks,
                "completed": completed_tasks,
                "failed": failed_tasks,
                "running": running_tasks,
                "queued": len(self.task_queue),
                "success_rate": (
                    (completed_tasks / max(total_tasks, 1)) * 100 if total_tasks > 0 else 0
                ),
            },
            "system": {
                "status": "healthy" if error_agents == 0 else "degraded",
                "uptime": "99.8%",  # Mock data
                "last_updated": datetime.now(timezone.utc).isoformat(),
            },
        }

    async def shutdown(self):
        """Shutdown all agents gracefully"""
        logger.info("Shutting down agent service...")

        # Cancel running tasks
        for task in self.tasks.values():
            if task.status == TaskStatus.RUNNING:
                task.status = TaskStatus.CANCELLED

        # Set all agents to maintenance mode
        for agent in self.agents.values():
            agent.status = AgentStatus.MAINTENANCE

        # Close Supabase connection if available
        if self.supabase_service and self.supabase_service.is_available():
            # Supabase client doesn't require explicit cleanup
            logger.info("Supabase connection closed")

        logger.info("Agent service shutdown complete")


# Global agent service instance
_agent_service: AgentService | None = None


def get_agent_service() -> AgentService:
    """Get or create global agent service instance"""
    global _agent_service
    if _agent_service is None:
        _agent_service = AgentService()
        logger.info("Global agent service initialized")
    return _agent_service


async def shutdown_agent_service():
    """Shutdown global agent service"""
    global _agent_service
    if _agent_service:
        await _agent_service.shutdown()
        _agent_service = None
