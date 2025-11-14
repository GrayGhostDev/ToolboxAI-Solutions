"""
Coordinators Package - High-Level System Orchestration

This package provides high-level coordination for the ToolboxAI Roblox Environment,
orchestrating agents, swarm, SPARC, and MCP subsystems for educational content generation.
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Any, Dict, Optional

from .error_coordinator import ErrorCoordinator
from .main_coordinator import MainCoordinator
from .resource_coordinator import ResourceCoordinator
from .sync_coordinator import SyncCoordinator
from .workflow_coordinator import WorkflowCoordinator

logger = logging.getLogger(__name__)

# Global coordinator instances
_main_coordinator: Optional[MainCoordinator] = None
_workflow_coordinator: Optional[WorkflowCoordinator] = None
_resource_coordinator: Optional[ResourceCoordinator] = None
_sync_coordinator: Optional[SyncCoordinator] = None
_error_coordinator: Optional[ErrorCoordinator] = None


class CoordinatorSystem:
    """Central coordinator system management"""

    def __init__(self):
        self.main_coordinator = None
        self.workflow_coordinator = None
        self.resource_coordinator = None
        self.sync_coordinator = None
        self.error_coordinator = None
        self.is_initialized = False

    async def initialize(self, config: Optional[dict[str, Any]] = None):
        """Initialize all coordinator subsystems"""
        try:
            if config is None:
                config = {}

            # Initialize error coordinator first for system-wide error handling
            self.error_coordinator = ErrorCoordinator(config.get("error", {}))
            await self.error_coordinator.initialize()

            # Initialize resource coordinator for system resource management
            self.resource_coordinator = ResourceCoordinator(config.get("resource", {}))
            await self.resource_coordinator.initialize()

            # Initialize sync coordinator for state management
            self.sync_coordinator = SyncCoordinator(config.get("sync", {}))
            await self.sync_coordinator.initialize()

            # Initialize workflow coordinator for process orchestration
            self.workflow_coordinator = WorkflowCoordinator(config.get("workflow", {}))
            await self.workflow_coordinator.initialize()

            # Initialize main coordinator last to orchestrate all others
            self.main_coordinator = MainCoordinator(
                workflow_coordinator=self.workflow_coordinator,
                resource_coordinator=self.resource_coordinator,
                sync_coordinator=self.sync_coordinator,
                error_coordinator=self.error_coordinator,
                config=config.get("main", {}),
            )
            await self.main_coordinator.initialize()

            self.is_initialized = True
            logger.info("Coordinator system initialized successfully")

        except Exception as e:
            logger.error("Failed to initialize coordinator system: %s", e)
            if self.error_coordinator:
                await self.error_coordinator.handle_error(
                    "system_initialization", e, {"component": "coordinator_system"}
                )
            raise

    async def shutdown(self):
        """Gracefully shutdown all coordinators"""
        try:
            if self.main_coordinator:
                await self.main_coordinator.shutdown()
            if self.workflow_coordinator:
                await self.workflow_coordinator.shutdown()
            if self.sync_coordinator:
                await self.sync_coordinator.shutdown()
            if self.resource_coordinator:
                await self.resource_coordinator.shutdown()
            if self.error_coordinator:
                await self.error_coordinator.shutdown()

            self.is_initialized = False
            logger.info("Coordinator system shutdown complete")

        except Exception as e:
            logger.error("Error during coordinator system shutdown: %s", e)

    def get_main_coordinator(self) -> MainCoordinator:
        """Get main coordinator instance"""
        if not self.is_initialized or not self.main_coordinator:
            raise RuntimeError()
        return self.main_coordinator

    def get_workflow_coordinator(self) -> WorkflowCoordinator:
        """Get workflow coordinator instance"""
        if not self.is_initialized or not self.workflow_coordinator:
            raise RuntimeError()
        return self.workflow_coordinator

    def get_resource_coordinator(self) -> ResourceCoordinator:
        """Get resource coordinator instance"""
        if not self.is_initialized or not self.resource_coordinator:
            raise RuntimeError()
        return self.resource_coordinator

    def get_sync_coordinator(self) -> SyncCoordinator:
        """Get sync coordinator instance"""
        if not self.is_initialized or not self.sync_coordinator:
            raise RuntimeError("Coordinator system not initialized")
        return self.sync_coordinator

    def get_error_coordinator(self) -> ErrorCoordinator:
        """Get error coordinator instance"""
        if not self.is_initialized or not self.error_coordinator:
            raise RuntimeError("Coordinator system not initialized")
        return self.error_coordinator


# Global coordinator system
_coordinator_system: Optional[CoordinatorSystem] = None


async def initialize_coordinators(
    config: Optional[dict[str, Any]] = None,
) -> CoordinatorSystem:
    """Initialize the global coordinator system"""
    global _coordinator_system

    if _coordinator_system is None:
        _coordinator_system = CoordinatorSystem()

    await _coordinator_system.initialize(config)
    return _coordinator_system


def get_coordinator_system() -> CoordinatorSystem:
    """Get the global coordinator system"""
    global _coordinator_system

    if _coordinator_system is None or not _coordinator_system.is_initialized:
        raise RuntimeError(
            "Coordinator system not initialized. Call initialize_coordinators() first."
        )

    return _coordinator_system


@asynccontextmanager
async def coordinator_context(config: Optional[dict[str, Any]] = None):
    """Async context manager for coordinator system lifecycle"""
    system = await initialize_coordinators(config)
    try:
        yield system
    finally:
        await system.shutdown()


# Convenience factory functions
def create_main_coordinator(**kwargs) -> MainCoordinator:
    """Create standalone main coordinator"""
    return MainCoordinator(**kwargs)


def create_workflow_coordinator(**kwargs) -> WorkflowCoordinator:
    """Create standalone workflow coordinator"""
    return WorkflowCoordinator(**kwargs)


def create_resource_coordinator(**kwargs) -> ResourceCoordinator:
    """Create standalone resource coordinator"""
    return ResourceCoordinator(**kwargs)


def create_sync_coordinator(**kwargs) -> SyncCoordinator:
    """Create standalone sync coordinator"""
    return SyncCoordinator(**kwargs)


def create_error_coordinator(**kwargs) -> ErrorCoordinator:
    """Create standalone error coordinator"""
    return ErrorCoordinator(**kwargs)


# Quick access functions for common operations
async def generate_educational_content(
    subject: str,
    grade_level: int,
    learning_objectives: list,
    environment_type: str = "classroom",
    include_quiz: bool = True,
    **kwargs,
) -> Any:
    """Quick function to generate educational content using coordinator system"""
    system = get_coordinator_system()
    main_coordinator = system.get_main_coordinator()

    return await main_coordinator.generate_educational_content(
        subject=subject,
        grade_level=grade_level,
        learning_objectives=learning_objectives,
        environment_type=environment_type,
        include_quiz=include_quiz,
        **kwargs,
    )


async def create_learning_workflow(workflow_type: str, parameters: dict[str, Any]) -> str:
    """Create a new learning workflow"""
    system = get_coordinator_system()
    workflow_coordinator = system.get_workflow_coordinator()

    return await workflow_coordinator.create_workflow(workflow_type, parameters)


async def monitor_system_health() -> Any:
    """Get system health status"""
    system = get_coordinator_system()
    main_coordinator = system.get_main_coordinator()

    return await main_coordinator.get_health_status()


# Export all classes and functions
__all__ = [
    "CoordinatorSystem",
    "MainCoordinator",
    "WorkflowCoordinator",
    "ResourceCoordinator",
    "SyncCoordinator",
    "ErrorCoordinator",
    "initialize_coordinators",
    "get_coordinator_system",
    "coordinator_context",
    "create_main_coordinator",
    "create_workflow_coordinator",
    "create_resource_coordinator",
    "create_sync_coordinator",
    "create_error_coordinator",
    "generate_educational_content",
    "create_learning_workflow",
    "monitor_system_health",
]

# Package metadata
__version__ = "1.0.0"
__author__ = "ToolboxAI"
__description__ = "High-level coordination system for ToolboxAI Roblox Environment"
