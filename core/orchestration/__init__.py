"""
Core Orchestration Module

Unified orchestration system with domain-specific modules organized under
the MasterOrchestrator for optimal agent coordination and task management.

Architecture:
- MasterOrchestrator: Top-level orchestration and agent management
- Domain Modules: Specialized orchestration for specific domains
- Backward Compatibility: Maintains existing API contracts

Authors: ToolboxAI Team
Created: September 26, 2025
"""

from typing import Dict, Any, Optional
import logging

# Import the master orchestrator
from ..agents.master_orchestrator import (
    MasterOrchestrator,
    OrchestratorConfig,
    AgentSystemType,
    TaskPriority,
    TaskStatus,
    TaskInfo
)

# Import orchestration modules
try:
    from .roblox import RobloxOrchestrationModule
except ImportError as e:
    logger.warning(f"Could not import RobloxOrchestrationModule: {e}")
    RobloxOrchestrationModule = None

try:
    from .educational import EducationalOrchestrationModule
except ImportError as e:
    logger.warning(f"Could not import EducationalOrchestrationModule: {e}")
    EducationalOrchestrationModule = None

try:
    from .github import GitHubOrchestrationModule
except ImportError as e:
    logger.warning(f"Could not import GitHubOrchestrationModule: {e}")
    GitHubOrchestrationModule = None

try:
    from .error_handling import ErrorHandlingOrchestrationModule
except ImportError as e:
    logger.warning(f"Could not import ErrorHandlingOrchestrationModule: {e}")
    ErrorHandlingOrchestrationModule = None

try:
    from .sparc import SPARCOrchestrationModule
except ImportError as e:
    logger.warning(f"Could not import SPARCOrchestrationModule: {e}")
    SPARCOrchestrationModule = None

logger = logging.getLogger(__name__)

__all__ = [
    # Core orchestrator
    "MasterOrchestrator",
    "OrchestratorConfig",
    "AgentSystemType",
    "TaskPriority",
    "TaskStatus",
    "TaskInfo",

    # Orchestration modules
    "RobloxOrchestrationModule",
    "EducationalOrchestrationModule",
    "GitHubOrchestrationModule",
    "ErrorHandlingOrchestrationModule",
    "SPARCOrchestrationModule",

    # Factory functions
    "create_orchestrator",
    "get_orchestration_module"
]


class UnifiedOrchestrator:
    """
    Unified orchestrator that combines MasterOrchestrator with domain-specific modules.

    This class provides a single entry point for all orchestration needs while
    maintaining the modular architecture underneath.
    """

    def __init__(self, config: Optional[OrchestratorConfig] = None):
        """Initialize the unified orchestrator."""
        self.config = config or OrchestratorConfig()
        self.master = MasterOrchestrator(self.config)

        # Initialize domain modules
        self.modules = {}

        if RobloxOrchestrationModule:
            self.modules["roblox"] = RobloxOrchestrationModule(self.master)

        if EducationalOrchestrationModule:
            self.modules["educational"] = EducationalOrchestrationModule(self.master)

        if GitHubOrchestrationModule:
            self.modules["github"] = GitHubOrchestrationModule(self.master)

        if ErrorHandlingOrchestrationModule:
            self.modules["error_handling"] = ErrorHandlingOrchestrationModule(self.master)

        if SPARCOrchestrationModule:
            self.modules["sparc"] = SPARCOrchestrationModule(self.master)

        logger.info("Unified Orchestrator initialized with all modules")

    async def start(self):
        """Start the orchestrator and all modules."""
        await self.master.start()

        # Initialize modules
        for name, module in self.modules.items():
            try:
                await module.initialize()
                logger.info(f"Initialized {name} orchestration module")
            except Exception as e:
                logger.error(f"Failed to initialize {name} module: {e}")

    async def stop(self):
        """Stop the orchestrator and cleanup modules."""
        # Stop modules first
        for name, module in self.modules.items():
            try:
                await module.cleanup()
                logger.info(f"Cleaned up {name} orchestration module")
            except Exception as e:
                logger.error(f"Failed to cleanup {name} module: {e}")

        # Stop master orchestrator
        await self.master.stop()

    def get_module(self, domain: str):
        """Get a specific orchestration module."""
        return self.modules.get(domain)

    async def submit_task(self, domain: str, **kwargs):
        """Submit a task to a specific domain module."""
        module = self.modules.get(domain)
        if not module:
            raise ValueError(f"Unknown domain: {domain}")

        return await module.submit_task(**kwargs)

    async def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status."""
        master_stats = await self.master.get_statistics()

        module_status = {}
        for name, module in self.modules.items():
            try:
                module_status[name] = await module.get_status()
            except Exception as e:
                module_status[name] = {"error": str(e)}

        return {
            "master_orchestrator": master_stats,
            "modules": module_status,
            "overall_health": master_stats.get("system_health", "unknown")
        }


def create_orchestrator(config: Optional[OrchestratorConfig] = None) -> UnifiedOrchestrator:
    """
    Factory function to create a new unified orchestrator instance.

    Args:
        config: Optional orchestrator configuration

    Returns:
        Configured UnifiedOrchestrator instance
    """
    return UnifiedOrchestrator(config)


def get_orchestration_module(orchestrator: UnifiedOrchestrator, domain: str):
    """
    Get a specific orchestration module from the unified orchestrator.

    Args:
        orchestrator: The unified orchestrator instance
        domain: Domain name (roblox, educational, github, error_handling, sparc)

    Returns:
        The requested orchestration module
    """
    return orchestrator.get_module(domain)


# Backward compatibility exports
# These maintain compatibility with existing imports
Orchestrator = UnifiedOrchestrator  # Alias for backward compatibility
OrchestrationEngine = UnifiedOrchestrator  # Alternative alias