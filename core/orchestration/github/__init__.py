"""
GitHub Orchestration Module

Integrates GitHub-specific orchestration capabilities including workflow management,
worktree coordination, and Git operations through LangGraph workflows.

This module provides:
- GitHub workflow orchestration
- Git worktree management
- Large file detection and LFS migration
- Repository health monitoring
- Deployment preparation
"""

import asyncio
import logging
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

# Import GitHub orchestrator components
from ...agents.github_agents.orchestrator import (
    GitHubAgentOrchestrator,
    GitHubAgentState,
    OperationType,
)

# Import base orchestration components
from ...agents.master_orchestrator import (
    AgentSystemType,
    MasterOrchestrator,
    TaskPriority,
)

logger = logging.getLogger(__name__)


class GitHubWorkflowType(Enum):
    """GitHub workflow types."""

    PRE_COMMIT = "pre_commit"
    PRE_PUSH = "pre_push"
    HEALTH_CHECK = "health_check"
    OPTIMIZATION = "optimization"
    DEPLOYMENT = "deployment"
    FULL_SCAN = "full_scan"
    WORKTREE_MANAGEMENT = "worktree_management"


class GitHubOrchestrationModule:
    """
    GitHub orchestration module that provides Git and GitHub-specific workflows.

    This module integrates GitHub agent orchestration with worktree management
    and provides a unified interface for Git operations.
    """

    def __init__(self, master_orchestrator: MasterOrchestrator):
        """Initialize the GitHub orchestration module."""
        self.master = master_orchestrator
        self.github_orchestrator: Optional[GitHubAgentOrchestrator] = None

        # Metrics
        self.metrics = {
            "workflows_executed": 0,
            "successful_workflows": 0,
            "failed_workflows": 0,
            "files_processed": 0,
            "lfs_migrations": 0,
        }

        logger.info("GitHub Orchestration Module initialized")

    async def initialize(self):
        """Initialize the module and its GitHub orchestrator."""
        try:
            # Initialize GitHub agent orchestrator
            self.github_orchestrator = GitHubAgentOrchestrator()

            logger.info("GitHub Orchestration Module fully initialized")

        except Exception as e:
            logger.error(f"Failed to initialize GitHub module: {e}")
            raise

    async def submit_task(self, **kwargs) -> str:
        """
        Submit a GitHub orchestration task.

        Args:
            **kwargs: Task parameters including workflow_type, files, auto_fix

        Returns:
            Task ID for tracking
        """
        # Extract parameters
        workflow_type = kwargs.get("workflow_type", GitHubWorkflowType.HEALTH_CHECK)
        files_to_process = kwargs.get("files", [])
        auto_fix = kwargs.get("auto_fix", False)

        # Prepare task data for master orchestrator
        task_data = {
            "type": "github_workflow",
            "workflow_type": workflow_type.value,
            "files_to_process": files_to_process,
            "auto_fix": auto_fix,
            "module": "github",
        }

        # Submit to master orchestrator
        task_id = await self.master.submit_task(
            agent_type=AgentSystemType.GITHUB,
            task_data=task_data,
            priority=TaskPriority.MEDIUM,
        )

        self.metrics["workflows_executed"] += 1
        return task_id

    async def execute_workflow(
        self,
        operation_type: OperationType,
        files_to_process: list[str] = None,
        auto_fix: bool = False,
    ) -> dict[str, Any]:
        """
        Execute a GitHub workflow directly.

        Args:
            operation_type: Type of operation to perform
            files_to_process: List of files to process
            auto_fix: Whether to automatically fix issues

        Returns:
            Workflow execution result
        """
        if not self.github_orchestrator:
            raise RuntimeError("GitHub orchestrator not initialized")

        try:
            # Prepare initial state
            initial_state = GitHubAgentState(
                operation_type=operation_type.value,
                files_to_process=files_to_process or [],
                large_files_detected=[],
                lfs_migrations=[],
                optimizations_applied=[],
                health_status={},
                deployment_readiness={},
                errors=[],
                recommendations=[],
                current_agent="",
                timestamp=datetime.now().isoformat(),
                auto_fix=auto_fix,
            )

            # Execute workflow
            result = await self.github_orchestrator.execute_operation(initial_state)

            # Update metrics
            if result.get("errors"):
                self.metrics["failed_workflows"] += 1
            else:
                self.metrics["successful_workflows"] += 1

            self.metrics["files_processed"] += len(files_to_process or [])
            self.metrics["lfs_migrations"] += len(result.get("lfs_migrations", []))

            return result

        except Exception as e:
            logger.error(f"Error executing GitHub workflow: {e}")
            self.metrics["failed_workflows"] += 1
            raise

    async def pre_commit_check(self, files: list[str] = None) -> dict[str, Any]:
        """
        Perform pre-commit checks on specified files.

        Args:
            files: List of files to check (all if None)

        Returns:
            Pre-commit check results
        """
        return await self.execute_workflow(
            operation_type=OperationType.PRE_COMMIT,
            files_to_process=files or [],
            auto_fix=True,
        )

    async def pre_push_check(self, files: list[str] = None) -> dict[str, Any]:
        """
        Perform pre-push checks on specified files.

        Args:
            files: List of files to check (all if None)

        Returns:
            Pre-push check results
        """
        return await self.execute_workflow(
            operation_type=OperationType.PRE_PUSH,
            files_to_process=files or [],
            auto_fix=True,
        )

    async def health_check(self) -> dict[str, Any]:
        """
        Perform repository health check.

        Returns:
            Repository health status
        """
        return await self.execute_workflow(
            operation_type=OperationType.HEALTH_CHECK, auto_fix=False
        )

    async def optimize_repository(self) -> dict[str, Any]:
        """
        Optimize repository performance and structure.

        Returns:
            Optimization results
        """
        return await self.execute_workflow(operation_type=OperationType.OPTIMIZATION, auto_fix=True)

    async def prepare_deployment(self) -> dict[str, Any]:
        """
        Prepare repository for deployment.

        Returns:
            Deployment preparation results
        """
        return await self.execute_workflow(operation_type=OperationType.DEPLOYMENT, auto_fix=True)

    async def full_scan(self) -> dict[str, Any]:
        """
        Perform full repository scan.

        Returns:
            Full scan results
        """
        return await self.execute_workflow(operation_type=OperationType.FULL_SCAN, auto_fix=False)

    async def manage_worktrees(self, **kwargs) -> dict[str, Any]:
        """
        Manage Git worktrees.

        Args:
            **kwargs: Worktree management parameters

        Returns:
            Worktree management results
        """
        # This would integrate with the archived worktree orchestrator
        # For now, return a placeholder
        return {
            "success": True,
            "message": "Worktree management not yet implemented",
            "data": kwargs,
        }

    async def get_status(self) -> dict[str, Any]:
        """Get the status of the GitHub orchestration module."""
        github_status = None
        if self.github_orchestrator:
            try:
                # GitHub orchestrator doesn't have a direct status method
                # We'll use the workflow execution as a health check
                github_status = {
                    "initialized": True,
                    "workflow_engine": "langgraph",
                    "available_operations": [op.value for op in OperationType],
                }
            except Exception as e:
                github_status = {"error": str(e)}

        return {
            "module": "github",
            "initialized": self.github_orchestrator is not None,
            "github_orchestrator": github_status,
            "metrics": self.metrics,
        }

    async def cleanup(self):
        """Cleanup the module and its resources."""
        try:
            # Cleanup GitHub orchestrator if needed
            if self.github_orchestrator:
                # GitHub orchestrator doesn't have explicit cleanup
                pass

            logger.info("GitHub Orchestration Module cleaned up")

        except Exception as e:
            logger.error(f"Error cleaning up GitHub module: {e}")


# Export key classes for backward compatibility
__all__ = [
    "GitHubOrchestrationModule",
    "GitHubWorkflowType",
    "GitHubAgentOrchestrator",
    "OperationType",
    "GitHubAgentState",
]


# Convenience factory function
def create_github_orchestrator(
    master_orchestrator: MasterOrchestrator,
) -> GitHubOrchestrationModule:
    """Create and initialize a GitHub orchestration module."""
    return GitHubOrchestrationModule(master_orchestrator)
