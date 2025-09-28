"""
Roblox Orchestration Module

Combines Roblox environment generation and project management orchestration
into a unified module for educational Roblox content creation.

This module integrates:
- Environment orchestration (from core/agents/orchestrator.py)
- Project orchestration (from core/agents/roblox/roblox_orchestrator.py)
- Agent coordination for Roblox-specific workflows
"""

from typing import Dict, Any, Optional, List
import asyncio
import logging
from datetime import datetime
from enum import Enum
from dataclasses import dataclass

# Import base orchestration components
from ...agents.base_agent import BaseAgent, TaskResult, AgentState
from ...agents.master_orchestrator import MasterOrchestrator, AgentSystemType, TaskPriority

# Import existing Roblox orchestrator classes for compatibility
from ...agents.orchestrator import (
    WorkflowType,
    OrchestrationRequest,
    OrchestrationResult,
    Orchestrator as EnvironmentOrchestrator
)

logger = logging.getLogger(__name__)


class RobloxWorkflowType(Enum):
    """Extended workflow types for Roblox orchestration."""
    # Environment workflows (from original orchestrator)
    FULL_ENVIRONMENT = "full_environment"
    CONTENT_ONLY = "content_only"
    QUIZ_ONLY = "quiz_only"
    TERRAIN_ONLY = "terrain_only"
    SCRIPT_ONLY = "script_only"
    REVIEW_OPTIMIZE = "review_optimize"
    TESTING_VALIDATION = "testing_validation"

    # Project workflows (from roblox_orchestrator)
    PROJECT_CREATION = "project_creation"
    GAME_DESIGN = "game_design"
    UI_DEVELOPMENT = "ui_development"
    GAMEPLAY_MECHANICS = "gameplay_mechanics"
    SECURITY_VALIDATION = "security_validation"
    PERFORMANCE_OPTIMIZATION = "performance_optimization"
    DEPLOYMENT = "deployment"


@dataclass
class RobloxTaskRequest:
    """Unified request for Roblox orchestration tasks."""
    workflow_type: RobloxWorkflowType
    subject: str
    grade_level: str
    learning_objectives: List[str]

    # Environment-specific options
    environment_theme: Optional[str] = None
    include_quiz: bool = True
    include_gamification: bool = True

    # Project-specific options
    game_type: str = "adventure"
    multiplayer: bool = True
    include_fun: bool = True
    target_age: Optional[int] = None

    # General options
    custom_requirements: Optional[Dict[str, Any]] = None


class RobloxOrchestrationModule:
    """
    Unified Roblox orchestration module that combines environment and project orchestration.

    This module provides a single interface for all Roblox-related orchestration tasks,
    delegating to specialized orchestrators as needed.
    """

    def __init__(self, master_orchestrator: MasterOrchestrator):
        """Initialize the Roblox orchestration module."""
        self.master = master_orchestrator
        self.environment_orchestrator: Optional[EnvironmentOrchestrator] = None
        self.project_orchestrator = None  # Will be created from roblox_orchestrator

        # Metrics
        self.metrics = {
            "environments_created": 0,
            "projects_created": 0,
            "successful_workflows": 0,
            "failed_workflows": 0
        }

        logger.info("Roblox Orchestration Module initialized")

    async def initialize(self):
        """Initialize the module and its sub-orchestrators."""
        try:
            # Initialize environment orchestrator
            self.environment_orchestrator = EnvironmentOrchestrator()

            # TODO: Initialize project orchestrator when roblox_orchestrator is integrated

            logger.info("Roblox Orchestration Module fully initialized")

        except Exception as e:
            logger.error(f"Failed to initialize Roblox module: {e}")
            raise

    async def submit_task(self, request: RobloxTaskRequest) -> str:
        """
        Submit a Roblox orchestration task.

        Args:
            request: The Roblox task request

        Returns:
            Task ID for tracking
        """
        # Determine which orchestrator to use based on workflow type
        if request.workflow_type in [
            RobloxWorkflowType.FULL_ENVIRONMENT,
            RobloxWorkflowType.CONTENT_ONLY,
            RobloxWorkflowType.QUIZ_ONLY,
            RobloxWorkflowType.TERRAIN_ONLY,
            RobloxWorkflowType.SCRIPT_ONLY,
            RobloxWorkflowType.REVIEW_OPTIMIZE,
            RobloxWorkflowType.TESTING_VALIDATION
        ]:
            return await self._submit_environment_task(request)

        elif request.workflow_type in [
            RobloxWorkflowType.PROJECT_CREATION,
            RobloxWorkflowType.GAME_DESIGN,
            RobloxWorkflowType.UI_DEVELOPMENT,
            RobloxWorkflowType.GAMEPLAY_MECHANICS,
            RobloxWorkflowType.SECURITY_VALIDATION,
            RobloxWorkflowType.PERFORMANCE_OPTIMIZATION,
            RobloxWorkflowType.DEPLOYMENT
        ]:
            return await self._submit_project_task(request)

        else:
            raise ValueError(f"Unknown workflow type: {request.workflow_type}")

    async def _submit_environment_task(self, request: RobloxTaskRequest) -> str:
        """Submit an environment orchestration task."""
        # Convert to environment orchestrator format
        env_request = OrchestrationRequest(
            workflow_type=WorkflowType(request.workflow_type.value),
            subject=request.subject,
            grade_level=request.grade_level,
            learning_objectives=request.learning_objectives,
            environment_theme=request.environment_theme,
            include_quiz=request.include_quiz,
            include_gamification=request.include_gamification,
            custom_requirements=request.custom_requirements
        )

        # Submit to master orchestrator
        task_data = {
            "orchestration_request": env_request,
            "type": "environment_generation"
        }

        task_id = await self.master.submit_task(
            agent_type=AgentSystemType.EDUCATIONAL,
            task_data=task_data,
            priority=TaskPriority.MEDIUM
        )

        self.metrics["environments_created"] += 1
        return task_id

    async def _submit_project_task(self, request: RobloxTaskRequest) -> str:
        """Submit a project orchestration task."""
        # TODO: Implement project task submission
        # This will be implemented when roblox_orchestrator is integrated

        task_data = {
            "project_request": request,
            "type": "project_creation"
        }

        task_id = await self.master.submit_task(
            agent_type=AgentSystemType.EDUCATIONAL,
            task_data=task_data,
            priority=TaskPriority.MEDIUM
        )

        self.metrics["projects_created"] += 1
        return task_id

    async def generate_environment(self, **kwargs) -> OrchestrationResult:
        """
        Convenience method to generate a complete Roblox environment.

        This is a direct interface to the environment orchestrator.
        """
        if not self.environment_orchestrator:
            raise RuntimeError("Environment orchestrator not initialized")

        result = await self.environment_orchestrator.generate_environment(**kwargs)

        if result.success:
            self.metrics["successful_workflows"] += 1
        else:
            self.metrics["failed_workflows"] += 1

        return result

    async def review_code(self, code: str, language: str = "lua") -> OrchestrationResult:
        """
        Convenience method to review Roblox code.

        This is a direct interface to the environment orchestrator.
        """
        if not self.environment_orchestrator:
            raise RuntimeError("Environment orchestrator not initialized")

        result = await self.environment_orchestrator.review_code(code, language)

        if result.success:
            self.metrics["successful_workflows"] += 1
        else:
            self.metrics["failed_workflows"] += 1

        return result

    async def get_status(self) -> Dict[str, Any]:
        """Get the status of the Roblox orchestration module."""
        env_status = None
        if self.environment_orchestrator:
            try:
                env_status = await self.environment_orchestrator.health_check()
            except Exception as e:
                env_status = {"error": str(e)}

        return {
            "module": "roblox",
            "initialized": self.environment_orchestrator is not None,
            "environment_orchestrator": env_status,
            "project_orchestrator": "not_implemented",  # TODO
            "metrics": self.metrics
        }

    async def cleanup(self):
        """Cleanup the module and its resources."""
        try:
            # Cleanup environment orchestrator if needed
            if self.environment_orchestrator and hasattr(self.environment_orchestrator, 'cleanup'):
                # Environment orchestrator doesn't have cleanup, but we check anyway
                pass

            logger.info("Roblox Orchestration Module cleaned up")

        except Exception as e:
            logger.error(f"Error cleaning up Roblox module: {e}")


# Backward compatibility exports
__all__ = [
    "RobloxOrchestrationModule",
    "RobloxWorkflowType",
    "RobloxTaskRequest",
    # Re-export environment orchestrator components for compatibility
    "WorkflowType",
    "OrchestrationRequest",
    "OrchestrationResult",
    "EnvironmentOrchestrator"
]

# Convenience factory function
def create_roblox_orchestrator(master_orchestrator: MasterOrchestrator) -> RobloxOrchestrationModule:
    """Create and initialize a Roblox orchestration module."""
    return RobloxOrchestrationModule(master_orchestrator)