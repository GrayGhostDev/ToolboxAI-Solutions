"""
Worktree-Agent Coordinator

This module provides coordination between the worktree system and the main agent swarm,
enabling intelligent task distribution across parallel Claude Code sessions.

Author: ToolboxAI Team
Created: 2025-09-17
Version: 1.0.0
"""

import json
import logging
import uuid
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta

# Import only the enums to avoid circular dependency
from enum import Enum
from pathlib import Path
from typing import Any, Optional

# from core.agents.github_agents.worktree_orchestrator_agent import WorktreeOrchestratorAgent  # Archived - now in orchestration module
from core.agents.github_agents.session_manager_agent import SessionManagerAgent


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


class TaskPriority(Enum):
    """Priority levels for task execution."""

    CRITICAL = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4
    DEFERRED = 5


logger = logging.getLogger(__name__)


class TaskDistributionStrategy(Enum):
    """Strategies for distributing tasks across worktrees."""

    ROUND_ROBIN = "round_robin"
    LEAST_LOADED = "least_loaded"
    CAPABILITY_BASED = "capability_based"
    AFFINITY_BASED = "affinity_based"
    PRIORITY_BASED = "priority_based"


class WorktreeTaskType(Enum):
    """Types of tasks that can be assigned to worktrees."""

    FEATURE_DEVELOPMENT = "feature_development"
    BUG_FIX = "bug_fix"
    REFACTORING = "refactoring"
    TESTING = "testing"
    DOCUMENTATION = "documentation"
    CODE_REVIEW = "code_review"
    PERFORMANCE_OPTIMIZATION = "performance_optimization"
    SECURITY_AUDIT = "security_audit"
    DEPENDENCY_UPDATE = "dependency_update"
    EXPERIMENTATION = "experimentation"


@dataclass
class WorktreeTask:
    """Represents a task to be executed in a worktree."""

    task_id: str
    task_type: WorktreeTaskType
    branch_name: str
    description: str
    requirements: list[str] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)  # Other task IDs
    priority: TaskPriority = TaskPriority.MEDIUM
    estimated_hours: float = 2.0
    assigned_worktree: Optional[str] = None
    assigned_session: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    status: str = "pending"
    result: Optional[dict[str, Any]] = None
    context: dict[str, Any] = field(default_factory=dict)


@dataclass
class WorktreeCapabilities:
    """Capabilities of a worktree session."""

    worktree_id: str
    branch_name: str
    session_id: Optional[str]
    available_agents: list[str] = field(default_factory=list)
    specialization: Optional[WorktreeTaskType] = None
    current_load: int = 0
    max_load: int = 3
    performance_score: float = 1.0
    error_rate: float = 0.0
    last_activity: Optional[datetime] = None


class WorktreeAgentCoordinator:
    """
    Coordinates task distribution and agent collaboration across worktrees.

    Links the worktree orchestrator with the main agent swarm to enable
    intelligent parallel development with multiple Claude Code sessions.
    """

        # WorktreeOrchestratorAgent has been archived - functionality temporarily disabled
        self.worktree_orchestrator = None  # Previously: WorktreeOrchestratorAgent()
        """Initialize the worktree coordinator.

        Args:
            master_orchestrator: Master orchestrator instance
        """
        self.master_orchestrator = master_orchestrator
        self.worktree_orchestrator = WorktreeOrchestratorAgent()
        self.session_manager = SessionManagerAgent()

        # Task management
        self.task_queue: list[WorktreeTask] = []
        self.active_tasks: dict[str, WorktreeTask] = {}
        self.completed_tasks: list[WorktreeTask] = []
        self.task_dependencies: dict[str, set[str]] = defaultdict(set)

        # Worktree tracking
        self.worktree_capabilities: dict[str, WorktreeCapabilities] = {}
        self.worktree_affinity: dict[str, dict[WorktreeTaskType, float]] = defaultdict(dict)

        # Configuration
        self.distribution_strategy = TaskDistributionStrategy.CAPABILITY_BASED
        self.max_parallel_tasks = 10
        self.enable_auto_scaling = True
        self.enable_load_balancing = True

        # Metrics
        self.metrics = {
            "tasks_distributed": 0,
            "tasks_completed": 0,
            "average_completion_time": 0.0,
            "worktree_efficiency": {},
            "task_success_rate": 0.0,
        }

        logger.info("Worktree-Agent Coordinator initialized")

    async def distribute_task(
        self,
        task_type: WorktreeTaskType,
        description: str,
        requirements: list[str],
        priority: TaskPriority = TaskPriority.MEDIUM,
        dependencies: Optional[list[str]] = None,
        context: Optional[dict[str, Any]] = None,
    ) -> str:
        """Distribute a task to an appropriate worktree.

        Args:
            task_type: Type of task
            description: Task description
            requirements: Task requirements
            priority: Task priority
            dependencies: Task dependencies (other task IDs)
            context: Additional context

        Returns:
            Task ID for tracking
        """
        # Create task
        task = WorktreeTask(
            task_id=str(uuid.uuid4()),
            task_type=task_type,
            branch_name=self._generate_branch_name(task_type),
            description=description,
            requirements=requirements,
            dependencies=dependencies or [],
            priority=priority,
            context=context or {},
        )

        # Add to queue
        self.task_queue.append(task)

        # Track dependencies
        if task.dependencies:
            for dep_id in task.dependencies:
                self.task_dependencies[dep_id].add(task.task_id)

        # Process distribution
        await self._process_task_distribution(task)

        self.metrics["tasks_distributed"] += 1

        logger.info(f"Task {task.task_id} distributed for {task_type.value}")
        return task.task_id

    async def _process_task_distribution(self, task: WorktreeTask):
        """Process task distribution to worktrees.

        Args:
            task: Task to distribute
        """
        # Check dependencies
        if not await self._check_dependencies(task):
            logger.info(f"Task {task.task_id} waiting for dependencies")
            return

        # Find or create suitable worktree
        worktree = await self._find_suitable_worktree(task)

        if not worktree:
            # Create new worktree if auto-scaling enabled
            if self.enable_auto_scaling:
                worktree = await self._create_worktree_for_task(task)

        if worktree:
            # Assign task to worktree
            await self._assign_task_to_worktree(task, worktree)
        else:
            logger.warning(f"No suitable worktree found for task {task.task_id}")

    async def _check_dependencies(self, task: WorktreeTask) -> bool:
        """Check if task dependencies are satisfied.

        Args:
            task: Task to check

        Returns:
            True if dependencies are satisfied
        """
        if not task.dependencies:
            return True

        for dep_id in task.dependencies:
            # Check if dependency is completed
            completed = any(
                t.task_id == dep_id and t.status == "completed" for t in self.completed_tasks
            )
            if not completed:
                return False

        return True

    async def _find_suitable_worktree(self, task: WorktreeTask) -> Optional[str]:
        """Find a suitable worktree for the task.

        Args:
            task: Task to assign

        Returns:
            Worktree ID or None
        """
        # Update worktree capabilities
        await self._update_worktree_capabilities()

        suitable_worktrees = []

        for worktree_id, capabilities in self.worktree_capabilities.items():
            # Check load
            if capabilities.current_load >= capabilities.max_load:
                continue

            # Check specialization match
            if capabilities.specialization == task.task_type:
                suitable_worktrees.append((worktree_id, 2.0))  # Higher score
            elif capabilities.specialization is None:
                suitable_worktrees.append((worktree_id, 1.0))  # Normal score

        if not suitable_worktrees:
            return None

        # Apply distribution strategy
        if self.distribution_strategy == TaskDistributionStrategy.LEAST_LOADED:
            # Sort by load
            suitable_worktrees.sort(key=lambda x: self.worktree_capabilities[x[0]].current_load)
        elif self.distribution_strategy == TaskDistributionStrategy.CAPABILITY_BASED:
            # Sort by score and performance
            suitable_worktrees.sort(
                key=lambda x: (x[1] * self.worktree_capabilities[x[0]].performance_score),
                reverse=True,
            )
        elif self.distribution_strategy == TaskDistributionStrategy.AFFINITY_BASED:
            # Sort by affinity
            suitable_worktrees.sort(
                key=lambda x: self.worktree_affinity[x[0]].get(task.task_type, 0.5),
                reverse=True,
            )

        return suitable_worktrees[0][0] if suitable_worktrees else None

    async def _create_worktree_for_task(self, task: WorktreeTask) -> Optional[str]:
        """Create a new worktree for the task.

        Args:
            task: Task requiring a worktree
        # Worktree orchestrator has been archived - functionality temporarily disabled
        if self.worktree_orchestrator is None:
            logger.warning(
                f"Worktree creation disabled: WorktreeOrchestratorAgent archived. "
                f"Task {task.task_id} cannot be assigned to a worktree."
            )
            return None
            

        Returns:
            Worktree ID or None
        """
        try:
            # Create worktree via orchestrator
            result = await self.worktree_orchestrator.execute(
                {
                    "action": "create",
                    "branch_name": task.branch_name,
                    "launch_claude": True,
                }
            )

            if result.get("success"):
                result.get("worktree", {}).get("path")
                worktree_id = task.branch_name

                # Register capabilities
                capabilities = WorktreeCapabilities(
                    worktree_id=worktree_id,
                    branch_name=task.branch_name,
                    specialization=task.task_type,
                    last_activity=datetime.now(),
                )
                self.worktree_capabilities[worktree_id] = capabilities

                logger.info(f"Created worktree {worktree_id} for task {task.task_id}")
                return worktree_id

        except Exception as e:
            logger.error(f"Failed to create worktree for task {task.task_id}: {e}")

        return None

    async def _assign_task_to_worktree(self, task: WorktreeTask, worktree_id: str):
        """Assign a task to a worktree.

        Args:
            task: Task to assign
            worktree_id: ID of the worktree
        """
        task.assigned_worktree = worktree_id
        task.started_at = datetime.now()
        task.status = "assigned"

        # Update active tasks
        self.active_tasks[task.task_id] = task

        # Update worktree load
        if worktree_id in self.worktree_capabilities:
            self.worktree_capabilities[worktree_id].current_load += 1
            self.worktree_capabilities[worktree_id].last_activity = datetime.now()

        # Start Claude session if needed
        capabilities = self.worktree_capabilities.get(worktree_id)
        if capabilities and not capabilities.session_id:
            session_result = await self.session_manager.execute(
                {
                    "action": "start",
                    "worktree_branch": task.branch_name,
                    "worktree_path": f"/Volumes/G-DRIVE ArmorATD/Development/Clients/ToolBoxAI-Solutions-worktrees/{task.branch_name}",
                }
            )

            if session_result.get("success"):
                capabilities.session_id = session_result.get("session_id")

        # Create task file in worktree
        await self._create_task_file(worktree_id, task)

        # If master orchestrator available, create agent tasks
        if self.master_orchestrator:
            await self._create_agent_tasks_for_worktree_task(task)

        logger.info(f"Assigned task {task.task_id} to worktree {worktree_id}")

    async def _create_task_file(self, worktree_id: str, task: WorktreeTask):
        """Create a task file in the worktree for Claude.

        Args:
            worktree_id: ID of the worktree
            task: Task to document
        """
        task_content = f"""# Task: {task.task_type.value.replace('_', ' ').title()}

## Task ID
{task.task_id}

## Description
{task.description}

## Requirements
{json.dumps(task.requirements, indent=2)}

## Priority
{task.priority.value}

## Estimated Time
{task.estimated_hours} hours

## Context
{json.dumps(task.context, indent=2) if task.context else "No additional context"}

## Instructions
Please complete this task following the requirements above. Use the agent system
to coordinate with other components as needed. Commit your changes with descriptive
messages and update the task status when complete.

## Available Agents
The following agent types are available for this task:
- Educational agents for content creation
- Database agents for data operations
- Integration agents for system connections
- Quality agents for code review
- Documentation agents for generating docs

Use the agent system by calling the appropriate endpoints or using the Task tool.
"""

        # Save to worktree
        task_file_path = Path(
            f"/Volumes/G-DRIVE ArmorATD/Development/Clients/ToolBoxAI-Solutions-worktrees/{worktree_id}/.claude-task-{task.task_id}.md"
        )

        try:
            task_file_path.write_text(task_content)
            logger.debug(f"Created task file for {task.task_id} in {worktree_id}")
        except Exception as e:
            logger.error(f"Failed to create task file: {e}")

    async def _create_agent_tasks_for_worktree_task(self, task: WorktreeTask):
        """Create specific agent tasks based on worktree task type.

        Args:
            task: Worktree task
        """
        if not self.master_orchestrator:
            return

        # Map task types to agent systems
        task_mapping = {
            WorktreeTaskType.FEATURE_DEVELOPMENT: [
                (AgentSystemType.INTEGRATION, "backend"),
                (AgentSystemType.INTEGRATION, "frontend"),
                (AgentSystemType.QUALITY, "code_review"),
            ],
            WorktreeTaskType.BUG_FIX: [
                (AgentSystemType.QUALITY, "debugging"),
                (AgentSystemType.TESTING, "regression"),
            ],
            WorktreeTaskType.DOCUMENTATION: [
                (AgentSystemType.DOCUMENTATION, "generate"),
                (AgentSystemType.REVIEW, "content"),
            ],
            WorktreeTaskType.TESTING: [
                (AgentSystemType.TESTING, "unit"),
                (AgentSystemType.TESTING, "integration"),
            ],
        }

        agent_tasks = task_mapping.get(task.task_type, [])

        for agent_type, sub_task in agent_tasks:
            await self.master_orchestrator.submit_task(
                agent_type=agent_type,
                task_data={
                    "worktree_task_id": task.task_id,
        # Worktree orchestrator has been archived - functionality temporarily disabled
        if self.worktree_orchestrator is None:
            logger.debug("Worktree capability updates disabled: WorktreeOrchestratorAgent archived.")
            return
            
                    "worktree_id": task.assigned_worktree,
                    "sub_task": sub_task,
                    "context": task.context,
                },
                priority=task.priority,
                context={"worktree_task": task.task_id},
            )

    async def _update_worktree_capabilities(self):
        """Update capabilities of all worktrees."""
        try:
            # Get worktree status from orchestrator
            status_result = await self.worktree_orchestrator.execute({"action": "list"})

            if status_result.get("success"):
                worktrees = status_result.get("worktrees", [])

                for worktree in worktrees:
                    worktree_id = worktree.get("branch")

                    if worktree_id not in self.worktree_capabilities:
                        # Create new capabilities entry
                        self.worktree_capabilities[worktree_id] = WorktreeCapabilities(
                            worktree_id=worktree_id,
                            branch_name=worktree.get("branch"),
                            session_id=None,
                            last_activity=datetime.now(),
                        )

                    # Update activity status
                    capabilities = self.worktree_capabilities[worktree_id]
                    if worktree.get("claude_active"):
                        capabilities.last_activity = datetime.now()

        except Exception as e:
            logger.error(f"Failed to update worktree capabilities: {e}")

    def _generate_branch_name(self, task_type: WorktreeTaskType) -> str:
        """Generate a branch name for a task.

        Args:
            task_type: Type of task

        Returns:
            Branch name
        """
        prefix_map = {
            WorktreeTaskType.FEATURE_DEVELOPMENT: "feature",
            WorktreeTaskType.BUG_FIX: "bugfix",
            WorktreeTaskType.REFACTORING: "refactor",
            WorktreeTaskType.TESTING: "test",
            WorktreeTaskType.DOCUMENTATION: "docs",
            WorktreeTaskType.PERFORMANCE_OPTIMIZATION: "perf",
            WorktreeTaskType.SECURITY_AUDIT: "security",
            WorktreeTaskType.DEPENDENCY_UPDATE: "deps",
            WorktreeTaskType.EXPERIMENTATION: "experiment",
        }

        prefix = prefix_map.get(task_type, "task")
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        return f"{prefix}-{timestamp}"

    async def complete_task(self, task_id: str, result: Optional[dict[str, Any]] = None):
        """Mark a task as complete.

        Args:
            task_id: ID of the task
            result: Task result data
        """
        if task_id not in self.active_tasks:
            logger.warning(f"Task {task_id} not found in active tasks")
            return

        task = self.active_tasks[task_id]
        task.completed_at = datetime.now()
        task.status = "completed"
        task.result = result

        # Update metrics
        completion_time = (task.completed_at - task.started_at).total_seconds() / 3600
        self.metrics["tasks_completed"] += 1
        self.metrics["average_completion_time"] = (
            self.metrics["average_completion_time"] * (self.metrics["tasks_completed"] - 1)
            + completion_time
        ) / self.metrics["tasks_completed"]

        # Update worktree metrics
        if task.assigned_worktree:
            if task.assigned_worktree not in self.metrics["worktree_efficiency"]:
                self.metrics["worktree_efficiency"][task.assigned_worktree] = {
                    "tasks_completed": 0,
                    "average_time": 0.0,
                }

            efficiency = self.metrics["worktree_efficiency"][task.assigned_worktree]
            efficiency["tasks_completed"] += 1
            efficiency["average_time"] = (
                efficiency["average_time"] * (efficiency["tasks_completed"] - 1) + completion_time
            ) / efficiency["tasks_completed"]

            # Update worktree load
            if task.assigned_worktree in self.worktree_capabilities:
                self.worktree_capabilities[task.assigned_worktree].current_load -= 1

        # Move to completed
        self.completed_tasks.append(task)
        del self.active_tasks[task_id]

        # Check for dependent tasks
        if task_id in self.task_dependencies:
            dependent_tasks = self.task_dependencies[task_id]
            for dep_task_id in dependent_tasks:
                # Find dependent task in queue
                for queued_task in self.task_queue:
                    if queued_task.task_id == dep_task_id:
                        # Try to process it now
                        await self._process_task_distribution(queued_task)

        logger.info(f"Task {task_id} completed")

    async def get_task_status(self, task_id: str) -> Optional[dict[str, Any]]:
        """Get status of a specific task.

        Args:
            task_id: ID of the task

        Returns:
            Task status or None
        """
        # Check active tasks
        if task_id in self.active_tasks:
            task = self.active_tasks[task_id]
            return self._task_to_dict(task)

        # Check completed tasks
        for task in self.completed_tasks:
            if task.task_id == task_id:
                return self._task_to_dict(task)

        # Check queue
        for task in self.task_queue:
            if task.task_id == task_id:
                return self._task_to_dict(task)

        return None

    def _task_to_dict(self, task: WorktreeTask) -> dict[str, Any]:
        """Convert task to dictionary.

        Args:
            task: Task to convert

        Returns:
            Dictionary representation
        """
        return {
            "task_id": task.task_id,
            "task_type": task.task_type.value,
            "branch_name": task.branch_name,
            "description": task.description,
            "status": task.status,
            "priority": task.priority.value,
            "assigned_worktree": task.assigned_worktree,
            "assigned_session": task.assigned_session,
            "created_at": task.created_at.isoformat(),
            "started_at": task.started_at.isoformat() if task.started_at else None,
            "completed_at": task.completed_at.isoformat() if task.completed_at else None,
            "estimated_hours": task.estimated_hours,
            "result": task.result,
        }

    async def optimize_distribution(self):
        """Optimize task distribution across worktrees."""
        # Rebalance tasks if needed
        if self.enable_load_balancing:
            await self._rebalance_tasks()

        # Update affinity scores
        await self._update_affinity_scores()

        # Clean up idle worktrees
        await self._cleanup_idle_worktrees()

    async def _rebalance_tasks(self):
        """Rebalance tasks across worktrees."""
        # Find overloaded worktrees
        overloaded = []
        underloaded = []

        for worktree_id, capabilities in self.worktree_capabilities.items():
            if capabilities.current_load > capabilities.max_load:
                overloaded.append(worktree_id)
            elif capabilities.current_load < capabilities.max_load / 2:
                underloaded.append(worktree_id)

        # TODO: Implement task migration between worktrees

    async def _update_affinity_scores(self):
        """Update affinity scores based on performance."""
        for worktree_id in self.metrics.get("worktree_efficiency", {}):
            efficiency = self.metrics["worktree_efficiency"][worktree_id]

            # Calculate affinity based on completion rate and time
            if efficiency["tasks_completed"] > 0:
                performance_score = (
        # Worktree orchestrator has been archived - functionality temporarily disabled
        if self.worktree_orchestrator is None:
            logger.debug("Worktree cleanup disabled: WorktreeOrchestratorAgent archived.")
            return
            
                    1.0 / efficiency["average_time"] if efficiency["average_time"] > 0 else 1.0
                )

                # Update capabilities
                if worktree_id in self.worktree_capabilities:
                    self.worktree_capabilities[worktree_id].performance_score = performance_score

    async def _cleanup_idle_worktrees(self):
        """Clean up idle worktrees."""
        now = datetime.now()
        idle_threshold = timedelta(minutes=30)

        for worktree_id, capabilities in list(self.worktree_capabilities.items()):
            if capabilities.current_load == 0 and capabilities.last_activity:
                idle_time = now - capabilities.last_activity
                if idle_time > idle_threshold:
                    # Remove idle worktree
                    await self.worktree_orchestrator.execute(
                        {"action": "remove", "branch_name": capabilities.branch_name}
                    )

                    del self.worktree_capabilities[worktree_id]
                    logger.info(f"Cleaned up idle worktree: {worktree_id}")

    async def get_statistics(self) -> dict[str, Any]:
        """Get coordinator statistics.

        Returns:
            Statistics dictionary
        """
        return {
            "tasks": {
                "queued": len(self.task_queue),
                "active": len(self.active_tasks),
                "completed": len(self.completed_tasks),
            },
            "worktrees": {
                "total": len(self.worktree_capabilities),
                "active": sum(1 for c in self.worktree_capabilities.values() if c.current_load > 0),
            },
            "metrics": self.metrics,
            "distribution_strategy": self.distribution_strategy.value,
        }
