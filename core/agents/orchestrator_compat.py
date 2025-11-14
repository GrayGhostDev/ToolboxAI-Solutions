"""
Backward Compatibility Module for Orchestrator

This module provides backward compatibility for existing code that imports
from the original orchestrator.py file. It maintains the same API while
redirecting to the new unified orchestration system.

Deprecated imports will eventually be removed. Please update your code to use:
- core.orchestration.UnifiedOrchestrator instead of core.agents.orchestrator.Orchestrator
- core.orchestration.roblox.* for Roblox-specific functionality
"""

import warnings
from typing import Any, Optional

# Import the new orchestration system
from ..orchestration import OrchestratorConfig, UnifiedOrchestrator

# Import original classes for compatibility
from .orchestrator import OrchestrationRequest, OrchestrationResult, WorkflowType
from .orchestrator import Orchestrator as OriginalOrchestrator

# Issue deprecation warning
warnings.warn(
    "Importing from core.agents.orchestrator is deprecated. "
    "Please use core.orchestration instead.",
    DeprecationWarning,
    stacklevel=2,
)


class OrchestrationCompat:
    """
    Compatibility wrapper that provides the old Orchestrator interface
    while using the new unified orchestration system underneath.
    """

    def __init__(self, config: Optional[dict[str, Any]] = None):
        """Initialize with backward compatibility."""
        # Create a unified orchestrator
        orch_config = OrchestratorConfig() if not config else OrchestratorConfig(**config)
        self.unified = UnifiedOrchestrator(orch_config)

        # Keep a reference to the original orchestrator for direct calls
        self.original = OriginalOrchestrator(config)

    async def orchestrate(self, request: OrchestrationRequest) -> OrchestrationResult:
        """Orchestrate using the original orchestrator for now."""
        return await self.original.orchestrate(request)

    async def generate_environment(self, **kwargs) -> OrchestrationResult:
        """Generate environment using original orchestrator."""
        return await self.original.generate_environment(**kwargs)

    async def review_code(self, code: str, language: str = "lua") -> OrchestrationResult:
        """Review code using original orchestrator."""
        return await self.original.review_code(code, language)

    def get_metrics(self) -> dict[str, Any]:
        """Get metrics from original orchestrator."""
        return self.original.get_metrics()

    async def health_check(self) -> dict[str, Any]:
        """Perform health check using original orchestrator."""
        return await self.original.health_check()


# Backward compatibility aliases
Orchestrator = OrchestrationCompat
AgentOrchestrator = OrchestrationCompat
OrchestrationEngine = OrchestrationCompat

# Re-export all the original types for compatibility
__all__ = [
    "Orchestrator",
    "AgentOrchestrator",
    "OrchestrationEngine",
    "OrchestrationCompat",
    "WorkflowType",
    "OrchestrationRequest",
    "OrchestrationResult",
]
