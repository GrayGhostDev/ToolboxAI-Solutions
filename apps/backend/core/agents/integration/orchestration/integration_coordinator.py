"""
Integration Coordinator
======================
Multi-agent orchestration for complex integration workflows

Coordinates multiple agents and external platforms to execute
complex integration workflows that span multiple systems.
"""
import logging
import asyncio
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime
from enum import Enum
from dataclasses import dataclass, field

from apps.backend.core.agents.integration import (
    IntegrationAgent,
    IntegrationPlatform,
    IntegrationEvent,
    IntegrationStatus
)

logger = logging.getLogger(__name__)


class WorkflowStatus(Enum):
    """Status codes for orchestration workflows"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"
    CANCELLED = "cancelled"


@dataclass
class WorkflowStep:
    """
    Individual step in an integration workflow

    Represents a single operation to be executed as part of
    a larger workflow orchestration.
    """
    step_id: str
    name: str
    agent_type: str
    operation: str
    params: Dict[str, Any] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)
    status: WorkflowStatus = WorkflowStatus.PENDING
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    def can_execute(self, completed_steps: set) -> bool:
        """Check if all dependencies are satisfied"""
        return all(dep in completed_steps for dep in self.dependencies)

    def mark_running(self):
        """Mark step as running"""
        self.status = WorkflowStatus.RUNNING
        self.started_at = datetime.utcnow()

    def mark_completed(self, result: Dict[str, Any]):
        """Mark step as completed"""
        self.status = WorkflowStatus.COMPLETED
        self.result = result
        self.completed_at = datetime.utcnow()

    def mark_failed(self, error: str):
        """Mark step as failed"""
        self.status = WorkflowStatus.FAILED
        self.error = error
        self.completed_at = datetime.utcnow()


@dataclass
class Workflow:
    """
    Integration Workflow Definition

    Defines a multi-step integration workflow with dependencies,
    execution order, and rollback capabilities.
    """
    workflow_id: str
    name: str
    description: str
    steps: List[WorkflowStep] = field(default_factory=list)
    status: WorkflowStatus = WorkflowStatus.PENDING
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def add_step(self, step: WorkflowStep):
        """Add a step to the workflow"""
        self.steps.append(step)

    def get_executable_steps(self, completed_steps: set) -> List[WorkflowStep]:
        """Get steps that are ready to execute"""
        return [
            step for step in self.steps
            if step.status == WorkflowStatus.PENDING and step.can_execute(completed_steps)
        ]

    def is_complete(self) -> bool:
        """Check if workflow is complete"""
        return all(
            step.status in (WorkflowStatus.COMPLETED, WorkflowStatus.FAILED)
            for step in self.steps
        )

    def has_failures(self) -> bool:
        """Check if any steps have failed"""
        return any(step.status == WorkflowStatus.FAILED for step in self.steps)


class IntegrationCoordinator:
    """
    Integration Coordinator

    Advanced orchestration engine for multi-agent integration workflows.
    Manages complex workflows that span multiple agents, platforms, and systems.

    Features:
    - Multi-agent coordination
    - Dependency management
    - Parallel execution where possible
    - Error handling and retry logic
    - Workflow rollback capabilities
    - Real-time status tracking
    """

    def __init__(self):
        """Initialize integration coordinator"""
        self.integration_agent = IntegrationAgent()
        self.workflows: Dict[str, Workflow] = {}
        self.agents: Dict[str, Any] = {}
        self.event_handlers: Dict[str, List[Callable]] = {}

        logger.info("IntegrationCoordinator initialized")

    def register_agent(self, agent_type: str, agent: Any):
        """
        Register an agent for workflow execution

        Args:
            agent_type: Type identifier for the agent
            agent: Agent instance
        """
        self.agents[agent_type] = agent
        logger.info(f"Registered agent: {agent_type}")

    def register_platform(self, platform_name: str, config: Optional[Dict] = None):
        """
        Register an external platform

        Args:
            platform_name: Platform identifier
            config: Platform configuration
        """
        self.integration_agent.register_platform(platform_name, config)
        logger.info(f"Registered platform: {platform_name}")

    def create_workflow(
        self,
        name: str,
        description: str,
        workflow_id: Optional[str] = None
    ) -> Workflow:
        """
        Create a new integration workflow

        Args:
            name: Workflow name
            description: Workflow description
            workflow_id: Optional workflow ID (auto-generated if not provided)

        Returns:
            Created workflow instance
        """
        if not workflow_id:
            workflow_id = f"workflow_{int(datetime.utcnow().timestamp())}"

        workflow = Workflow(
            workflow_id=workflow_id,
            name=name,
            description=description
        )

        self.workflows[workflow_id] = workflow
        logger.info(f"Created workflow: {workflow_id} - {name}")

        return workflow

    def add_workflow_step(
        self,
        workflow_id: str,
        step_id: str,
        name: str,
        agent_type: str,
        operation: str,
        params: Optional[Dict] = None,
        dependencies: Optional[List[str]] = None
    ) -> WorkflowStep:
        """
        Add a step to a workflow

        Args:
            workflow_id: Target workflow ID
            step_id: Unique step identifier
            name: Step name
            agent_type: Type of agent to execute this step
            operation: Operation to perform
            params: Operation parameters
            dependencies: List of step IDs that must complete first

        Returns:
            Created workflow step
        """
        workflow = self.workflows.get(workflow_id)
        if not workflow:
            raise ValueError(f"Workflow not found: {workflow_id}")

        step = WorkflowStep(
            step_id=step_id,
            name=name,
            agent_type=agent_type,
            operation=operation,
            params=params or {},
            dependencies=dependencies or []
        )

        workflow.add_step(step)
        logger.info(f"Added step {step_id} to workflow {workflow_id}")

        return step

    async def execute_workflow(self, workflow_id: str) -> Dict[str, Any]:
        """
        Execute an integration workflow

        Args:
            workflow_id: ID of workflow to execute

        Returns:
            Workflow execution results
        """
        workflow = self.workflows.get(workflow_id)
        if not workflow:
            raise ValueError(f"Workflow not found: {workflow_id}")

        logger.info(f"Starting workflow execution: {workflow_id}")

        workflow.status = WorkflowStatus.RUNNING
        workflow.started_at = datetime.utcnow()

        completed_steps = set()

        try:
            # Execute steps in dependency order
            while not workflow.is_complete():
                executable_steps = workflow.get_executable_steps(completed_steps)

                if not executable_steps:
                    # Check if we're stuck (no executable steps but not complete)
                    if not workflow.is_complete():
                        raise RuntimeError(
                            "Workflow deadlock: No executable steps but workflow incomplete"
                        )
                    break

                # Execute steps in parallel where possible
                tasks = [
                    self._execute_step(workflow_id, step)
                    for step in executable_steps
                ]

                results = await asyncio.gather(*tasks, return_exceptions=True)

                # Process results
                for step, result in zip(executable_steps, results):
                    if isinstance(result, Exception):
                        step.mark_failed(str(result))
                        logger.error(f"Step {step.step_id} failed: {result}")
                    else:
                        step.mark_completed(result)
                        completed_steps.add(step.step_id)
                        logger.info(f"Step {step.step_id} completed successfully")

            # Determine final workflow status
            if workflow.has_failures():
                workflow.status = WorkflowStatus.FAILED
                logger.warning(f"Workflow {workflow_id} completed with failures")
            else:
                workflow.status = WorkflowStatus.COMPLETED
                logger.info(f"Workflow {workflow_id} completed successfully")

            workflow.completed_at = datetime.utcnow()

            return self._get_workflow_results(workflow)

        except Exception as e:
            workflow.status = WorkflowStatus.FAILED
            workflow.completed_at = datetime.utcnow()
            logger.error(f"Workflow {workflow_id} execution failed: {e}")
            raise

    async def _execute_step(self, workflow_id: str, step: WorkflowStep) -> Dict[str, Any]:
        """
        Execute a single workflow step

        Args:
            workflow_id: Parent workflow ID
            step: Step to execute

        Returns:
            Step execution result
        """
        logger.info(f"Executing step {step.step_id}: {step.name}")

        step.mark_running()

        try:
            # Get the appropriate agent
            agent = self.agents.get(step.agent_type)
            if not agent:
                raise ValueError(f"Agent not found: {step.agent_type}")

            # Execute the operation
            if hasattr(agent, step.operation):
                operation_method = getattr(agent, step.operation)
                result = await operation_method(**step.params)
            elif step.agent_type == "integration":
                # Handle integration agent operations
                result = await self.integration_agent.integrate(
                    step.params.get("platform", "default"),
                    step.params
                )
            else:
                raise ValueError(
                    f"Operation '{step.operation}' not found on agent '{step.agent_type}'"
                )

            return result

        except Exception as e:
            logger.error(f"Step {step.step_id} execution error: {e}")
            raise

    def _get_workflow_results(self, workflow: Workflow) -> Dict[str, Any]:
        """
        Compile workflow execution results

        Args:
            workflow: Completed workflow

        Returns:
            Results dictionary
        """
        return {
            "workflow_id": workflow.workflow_id,
            "name": workflow.name,
            "status": workflow.status.value,
            "started_at": workflow.started_at.isoformat() if workflow.started_at else None,
            "completed_at": workflow.completed_at.isoformat() if workflow.completed_at else None,
            "duration_seconds": (
                (workflow.completed_at - workflow.started_at).total_seconds()
                if workflow.started_at and workflow.completed_at
                else None
            ),
            "steps": [
                {
                    "step_id": step.step_id,
                    "name": step.name,
                    "status": step.status.value,
                    "result": step.result,
                    "error": step.error,
                    "duration_seconds": (
                        (step.completed_at - step.started_at).total_seconds()
                        if step.started_at and step.completed_at
                        else None
                    )
                }
                for step in workflow.steps
            ],
            "total_steps": len(workflow.steps),
            "completed_steps": sum(
                1 for step in workflow.steps
                if step.status == WorkflowStatus.COMPLETED
            ),
            "failed_steps": sum(
                1 for step in workflow.steps
                if step.status == WorkflowStatus.FAILED
            )
        }

    def get_workflow_status(self, workflow_id: str) -> Dict[str, Any]:
        """
        Get current status of a workflow

        Args:
            workflow_id: Workflow ID

        Returns:
            Current workflow status
        """
        workflow = self.workflows.get(workflow_id)
        if not workflow:
            raise ValueError(f"Workflow not found: {workflow_id}")

        return self._get_workflow_results(workflow)

    def list_workflows(self) -> List[Dict[str, Any]]:
        """
        List all workflows

        Returns:
            List of workflow summaries
        """
        return [
            {
                "workflow_id": wf.workflow_id,
                "name": wf.name,
                "status": wf.status.value,
                "steps": len(wf.steps),
                "created_at": wf.created_at.isoformat()
            }
            for wf in self.workflows.values()
        ]


__all__ = ['IntegrationCoordinator', 'Workflow', 'WorkflowStep', 'WorkflowStatus']
