"""
Integration Coordinator - Main orchestrator for multi-platform workflows

This agent coordinates:
- Cross-platform workflow orchestration
- Multi-agent task coordination
- Workflow state management
- Dependency resolution
- Parallel execution optimization
- End-to-end integration flows
"""

import asyncio
import logging
import uuid
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional

from core.agents.base_agent import AgentConfig

from ..base_integration_agent import (
    BaseIntegrationAgent,
    IntegrationEvent,
    IntegrationPlatform,
    TaskResult,
)

logger = logging.getLogger(__name__)


class WorkflowStatus(Enum):
    """Integration workflow status"""
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskPriority(Enum):
    """Task priority levels"""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class IntegrationTask:
    """Individual integration task"""
    task_id: str
    task_type: str
    agent_type: str  # Which agent should handle this
    platform: IntegrationPlatform
    parameters: dict[str, Any]
    dependencies: set[str] = field(default_factory=set)
    priority: TaskPriority = TaskPriority.MEDIUM
    status: str = "pending"
    result: Optional[Any] = None
    error: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    retry_count: int = 0
    max_retries: int = 3


@dataclass
class IntegrationWorkflow:
    """Complete integration workflow"""
    workflow_id: str
    name: str
    description: str
    tasks: dict[str, IntegrationTask]
    status: WorkflowStatus = WorkflowStatus.PENDING
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def get_ready_tasks(self) -> list[IntegrationTask]:
        """Get tasks that are ready to execute"""
        ready = []
        for task in self.tasks.values():
            if task.status == "pending":
                # Check if all dependencies are completed
                deps_completed = all(
                    self.tasks[dep_id].status == "completed"
                    for dep_id in task.dependencies
                    if dep_id in self.tasks
                )
                if deps_completed:
                    ready.append(task)
        return sorted(ready, key=lambda t: t.priority.value, reverse=True)


class IntegrationCoordinator(BaseIntegrationAgent):
    """
    Main coordinator for cross-platform integration workflows
    """

    def __init__(self, config: Optional[AgentConfig] = None):
        """Initialize Integration Coordinator"""
        if config is None:
            config = AgentConfig(
                name="IntegrationCoordinator",
                system_prompt="""You are the Integration Coordinator responsible for:
                - Orchestrating complex multi-platform workflows
                - Coordinating multiple agents across systems
                - Managing workflow dependencies and execution order
                - Optimizing parallel task execution
                - Handling workflow failures and recovery
                - Monitoring end-to-end integration flows
                """
            )
        super().__init__(config)

        # Workflow management
        self.workflows: dict[str, IntegrationWorkflow] = {}
        self.active_workflows: set[str] = set()

        # Agent registry
        self.agent_registry: dict[str, Any] = {}
        self.agent_availability: dict[str, bool] = defaultdict(lambda: True)

        # Task execution
        self.task_queue: asyncio.Queue = asyncio.Queue()
        self.executing_tasks: dict[str, asyncio.Task] = {}

        # Workflow templates
        self.workflow_templates: dict[str, dict[str, Any]] = self._init_workflow_templates()

        # Performance tracking
        self.workflow_metrics: dict[str, dict[str, Any]] = {}

    def _init_workflow_templates(self) -> dict[str, dict[str, Any]]:
        """Initialize predefined workflow templates"""
        return {
            "full_sync": {
                "name": "Full Platform Synchronization",
                "description": "Complete sync across all platforms",
                "tasks": [
                    {
                        "type": "database_sync",
                        "agent": "DatabaseSyncAgent",
                        "platform": IntegrationPlatform.DATABASE
                    },
                    {
                        "type": "api_update",
                        "agent": "APIGatewayAgent",
                        "platform": IntegrationPlatform.BACKEND
                    },
                    {
                        "type": "ui_refresh",
                        "agent": "UISyncAgent",
                        "platform": IntegrationPlatform.FRONTEND
                    },
                    {
                        "type": "roblox_deploy",
                        "agent": "AssetDeploymentAgent",
                        "platform": IntegrationPlatform.ROBLOX
                    }
                ]
            },
            "content_deployment": {
                "name": "Educational Content Deployment",
                "description": "Deploy educational content across platforms",
                "tasks": [
                    {
                        "type": "content_validation",
                        "agent": "SchemaValidatorAgent",
                        "platform": IntegrationPlatform.BACKEND
                    },
                    {
                        "type": "content_storage",
                        "agent": "DatabaseSyncAgent",
                        "platform": IntegrationPlatform.DATABASE
                    },
                    {
                        "type": "content_distribution",
                        "agent": "EventBusAgent",
                        "platform": IntegrationPlatform.MESSAGING
                    },
                    {
                        "type": "roblox_integration",
                        "agent": "EducationalContentAgent",
                        "platform": IntegrationPlatform.ROBLOX
                    },
                    {
                        "type": "ui_update",
                        "agent": "RealtimeUpdateAgent",
                        "platform": IntegrationPlatform.FRONTEND
                    }
                ]
            },
            "emergency_recovery": {
                "name": "Emergency Recovery Workflow",
                "description": "Recover from system failures",
                "tasks": [
                    {
                        "type": "health_check",
                        "agent": "PerformanceMonitorAgent",
                        "platform": IntegrationPlatform.BACKEND,
                        "priority": TaskPriority.CRITICAL
                    },
                    {
                        "type": "error_analysis",
                        "agent": "ErrorRecoveryAgent",
                        "platform": IntegrationPlatform.BACKEND,
                        "priority": TaskPriority.CRITICAL
                    },
                    {
                        "type": "cache_rebuild",
                        "agent": "CacheInvalidationAgent",
                        "platform": IntegrationPlatform.CACHE,
                        "priority": TaskPriority.HIGH
                    },
                    {
                        "type": "consistency_check",
                        "agent": "DatabaseSyncAgent",
                        "platform": IntegrationPlatform.DATABASE,
                        "priority": TaskPriority.HIGH
                    }
                ]
            }
        }

    async def create_workflow(
        self,
        name: str,
        description: str,
        template: Optional[str] = None,
        custom_tasks: Optional[list[dict[str, Any]]] = None
    ) -> IntegrationWorkflow:
        """Create a new integration workflow"""
        workflow_id = f"workflow_{uuid.uuid4().hex[:8]}"

        workflow = IntegrationWorkflow(
            workflow_id=workflow_id,
            name=name,
            description=description,
            tasks={}
        )

        # Use template if provided
        if template and template in self.workflow_templates:
            template_def = self.workflow_templates[template]
            for i, task_def in enumerate(template_def["tasks"]):
                task = IntegrationTask(
                    task_id=f"task_{workflow_id}_{i}",
                    task_type=task_def["type"],
                    agent_type=task_def["agent"],
                    platform=task_def["platform"],
                    parameters=task_def.get("parameters", {}),
                    priority=task_def.get("priority", TaskPriority.MEDIUM)
                )
                workflow.tasks[task.task_id] = task

        # Add custom tasks if provided
        if custom_tasks:
            for i, task_def in enumerate(custom_tasks):
                task = IntegrationTask(
                    task_id=f"custom_task_{workflow_id}_{i}",
                    task_type=task_def["type"],
                    agent_type=task_def["agent"],
                    platform=IntegrationPlatform[task_def["platform"]],
                    parameters=task_def.get("parameters", {}),
                    dependencies=set(task_def.get("dependencies", [])),
                    priority=TaskPriority[task_def.get("priority", "MEDIUM")]
                )
                workflow.tasks[task.task_id] = task

        self.workflows[workflow_id] = workflow

        # Initialize metrics
        self.workflow_metrics[workflow_id] = {
            "total_tasks": len(workflow.tasks),
            "completed_tasks": 0,
            "failed_tasks": 0,
            "average_task_duration": 0.0
        }

        logger.info(f"Created workflow: {workflow_id} with {len(workflow.tasks)} tasks")

        return workflow

    async def execute_workflow(
        self,
        workflow_id: str,
        parameters: Optional[dict[str, Any]] = None
    ) -> TaskResult:
        """Execute an integration workflow"""
        try:
            if workflow_id not in self.workflows:
                return TaskResult(
                    success=False,
                    output=None,
                    error=f"Workflow not found: {workflow_id}"
                )

            workflow = self.workflows[workflow_id]

            if workflow.status == WorkflowStatus.RUNNING:
                return TaskResult(
                    success=False,
                    output=None,
                    error="Workflow is already running"
                )

            # Update workflow status
            workflow.status = WorkflowStatus.RUNNING
            workflow.started_at = datetime.utcnow()
            self.active_workflows.add(workflow_id)

            # Apply parameters if provided
            if parameters:
                workflow.metadata.update(parameters)

            # Emit workflow start event
            await self.emit_event(IntegrationEvent(
                event_id=f"{workflow_id}_start",
                event_type="workflow_started",
                source_platform=IntegrationPlatform.BACKEND,
                payload={
                    "workflow_id": workflow_id,
                    "name": workflow.name,
                    "total_tasks": len(workflow.tasks)
                }
            ))

            # Execute workflow tasks
            while True:
                # Get ready tasks
                ready_tasks = workflow.get_ready_tasks()

                if not ready_tasks:
                    # Check if workflow is complete
                    all_completed = all(
                        task.status in ["completed", "failed", "skipped"]
                        for task in workflow.tasks.values()
                    )
                    if all_completed:
                        break

                    # Wait for running tasks to complete
                    await asyncio.sleep(0.1)
                    continue

                # Execute ready tasks in parallel
                execution_tasks = []
                for task in ready_tasks:
                    task.status = "running"
                    task.start_time = datetime.utcnow()
                    execution_tasks.append(
                        self._execute_task(workflow_id, task)
                    )

                # Wait for tasks to complete
                await asyncio.gather(*execution_tasks, return_exceptions=True)

            # Update workflow status
            failed_tasks = [t for t in workflow.tasks.values() if t.status == "failed"]
            if failed_tasks:
                workflow.status = WorkflowStatus.FAILED
                error_msg = f"Workflow failed with {len(failed_tasks)} failed tasks"
                logger.error(error_msg)

                return TaskResult(
                    success=False,
                    output={
                        "workflow_id": workflow_id,
                        "failed_tasks": [t.task_id for t in failed_tasks]
                    },
                    error=error_msg
                )
            else:
                workflow.status = WorkflowStatus.COMPLETED
                workflow.completed_at = datetime.utcnow()

                # Calculate execution time
                execution_time = (workflow.completed_at - workflow.started_at).total_seconds()

                logger.info(f"Workflow {workflow_id} completed in {execution_time:.2f} seconds")

                return TaskResult(
                    success=True,
                    output={
                        "workflow_id": workflow_id,
                        "execution_time": execution_time,
                        "completed_tasks": len(workflow.tasks)
                    },
                    execution_time=execution_time
                )

        except Exception as e:
            logger.error(f"Error executing workflow: {e}")
            if workflow_id in self.workflows:
                self.workflows[workflow_id].status = WorkflowStatus.FAILED
            return TaskResult(
                success=False,
                output=None,
                error=str(e)
            )
        finally:
            self.active_workflows.discard(workflow_id)

    async def _execute_task(
        self,
        workflow_id: str,
        task: IntegrationTask
    ) -> None:
        """Execute an individual task within a workflow"""
        try:
            logger.info(f"Executing task {task.task_id} with agent {task.agent_type}")

            # Get the appropriate agent
            agent = self.agent_registry.get(task.agent_type)
            if not agent:
                # Simulate agent execution for now
                await asyncio.sleep(0.5)  # Simulated execution time
                task.result = {"simulated": True, "task_id": task.task_id}
            else:
                # Execute with the actual agent
                result = await agent.execute_task(
                    task.task_type,
                    task.parameters
                )
                task.result = result.output

            task.status = "completed"
            task.end_time = datetime.utcnow()

            # Update metrics
            self.workflow_metrics[workflow_id]["completed_tasks"] += 1

            # Emit task completion event
            await self.emit_event(IntegrationEvent(
                event_id=f"{task.task_id}_complete",
                event_type="task_completed",
                source_platform=task.platform,
                payload={
                    "workflow_id": workflow_id,
                    "task_id": task.task_id,
                    "task_type": task.task_type,
                    "duration": (task.end_time - task.start_time).total_seconds()
                }
            ))

        except Exception as e:
            logger.error(f"Error executing task {task.task_id}: {e}")
            task.status = "failed"
            task.error = str(e)
            task.end_time = datetime.utcnow()

            # Update metrics
            self.workflow_metrics[workflow_id]["failed_tasks"] += 1

            # Retry logic
            if task.retry_count < task.max_retries:
                task.retry_count += 1
                task.status = "pending"  # Reset for retry
                logger.info(f"Retrying task {task.task_id} (attempt {task.retry_count})")

    async def pause_workflow(self, workflow_id: str) -> TaskResult:
        """Pause a running workflow"""
        if workflow_id not in self.workflows:
            return TaskResult(success=False, output=None, error="Workflow not found")

        workflow = self.workflows[workflow_id]
        if workflow.status != WorkflowStatus.RUNNING:
            return TaskResult(success=False, output=None, error="Workflow is not running")

        workflow.status = WorkflowStatus.PAUSED
        logger.info(f"Paused workflow: {workflow_id}")

        return TaskResult(success=True, output={"workflow_id": workflow_id, "status": "paused"})

    async def resume_workflow(self, workflow_id: str) -> TaskResult:
        """Resume a paused workflow"""
        if workflow_id not in self.workflows:
            return TaskResult(success=False, output=None, error="Workflow not found")

        workflow = self.workflows[workflow_id]
        if workflow.status != WorkflowStatus.PAUSED:
            return TaskResult(success=False, output=None, error="Workflow is not paused")

        workflow.status = WorkflowStatus.RUNNING
        logger.info(f"Resumed workflow: {workflow_id}")

        # Continue execution
        return await self.execute_workflow(workflow_id)

    async def cancel_workflow(self, workflow_id: str) -> TaskResult:
        """Cancel a workflow"""
        if workflow_id not in self.workflows:
            return TaskResult(success=False, output=None, error="Workflow not found")

        workflow = self.workflows[workflow_id]
        workflow.status = WorkflowStatus.CANCELLED

        # Cancel any running tasks
        for task in workflow.tasks.values():
            if task.status == "running":
                task.status = "cancelled"

        self.active_workflows.discard(workflow_id)
        logger.info(f"Cancelled workflow: {workflow_id}")

        return TaskResult(success=True, output={"workflow_id": workflow_id, "status": "cancelled"})

    async def get_workflow_status(self, workflow_id: str) -> dict[str, Any]:
        """Get detailed workflow status"""
        if workflow_id not in self.workflows:
            return {"error": "Workflow not found"}

        workflow = self.workflows[workflow_id]
        metrics = self.workflow_metrics.get(workflow_id, {})

        task_summary = {
            "total": len(workflow.tasks),
            "pending": sum(1 for t in workflow.tasks.values() if t.status == "pending"),
            "running": sum(1 for t in workflow.tasks.values() if t.status == "running"),
            "completed": sum(1 for t in workflow.tasks.values() if t.status == "completed"),
            "failed": sum(1 for t in workflow.tasks.values() if t.status == "failed")
        }

        return {
            "workflow_id": workflow_id,
            "name": workflow.name,
            "status": workflow.status.value,
            "created_at": workflow.created_at.isoformat(),
            "started_at": workflow.started_at.isoformat() if workflow.started_at else None,
            "completed_at": workflow.completed_at.isoformat() if workflow.completed_at else None,
            "task_summary": task_summary,
            "metrics": metrics,
            "current_tasks": [
                {
                    "task_id": t.task_id,
                    "type": t.task_type,
                    "status": t.status,
                    "platform": t.platform.value
                }
                for t in workflow.tasks.values()
                if t.status == "running"
            ]
        }

    async def register_agent(self, agent_type: str, agent_instance: Any):
        """Register an agent for task execution"""
        self.agent_registry[agent_type] = agent_instance
        logger.info(f"Registered agent: {agent_type}")

    async def _process_integration_event(self, event: IntegrationEvent):
        """Process integration events"""
        if event.event_type == "workflow_request":
            # Create and execute workflow based on event
            workflow = await self.create_workflow(
                name=event.payload.get("name", "Dynamic Workflow"),
                description=event.payload.get("description", ""),
                template=event.payload.get("template"),
                custom_tasks=event.payload.get("tasks")
            )
            await self.execute_workflow(workflow.workflow_id, event.payload.get("parameters"))

        elif event.event_type == "workflow_status_request":
            # Return workflow status
            workflow_id = event.payload.get("workflow_id")
            status = await self.get_workflow_status(workflow_id)

            await self.emit_event(IntegrationEvent(
                event_id=f"status_response_{event.event_id}",
                event_type="workflow_status_response",
                source_platform=IntegrationPlatform.BACKEND,
                payload=status,
                correlation_id=event.correlation_id
            ))

    async def execute_task(self, task: str, context: Optional[dict[str, Any]] = None) -> TaskResult:
        """Execute coordinator-specific tasks"""
        if task == "create_workflow":
            workflow = await self.create_workflow(
                name=context.get("name", "New Workflow"),
                description=context.get("description", ""),
                template=context.get("template"),
                custom_tasks=context.get("tasks")
            )
            return TaskResult(success=True, output={"workflow_id": workflow.workflow_id})

        elif task == "execute_workflow":
            return await self.execute_workflow(
                workflow_id=context["workflow_id"],
                parameters=context.get("parameters")
            )

        elif task == "workflow_status":
            status = await self.get_workflow_status(context["workflow_id"])
            return TaskResult(success=True, output=status)

        elif task == "pause_workflow":
            return await self.pause_workflow(context["workflow_id"])

        elif task == "resume_workflow":
            return await self.resume_workflow(context["workflow_id"])

        elif task == "cancel_workflow":
            return await self.cancel_workflow(context["workflow_id"])

        else:
            return await super().execute_task(task, context)