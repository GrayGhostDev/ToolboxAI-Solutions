"""
Multi-Agent System for Roblox Educational Environment Generation

This module provides a comprehensive agent-based system for generating
AI-powered educational content in Roblox environments using LangChain/LangGraph.
"""

from typing import TYPE_CHECKING, Any, Dict, List, Optional

from .base_agent import (
    AgentConfig,
    AgentPriority,
    AgentState,
    AgentStatus,
    BaseAgent,
    TaskResult,
)
from .orchestrator import OrchestrationRequest, OrchestrationResult, WorkflowType
from .review_agent import ReviewFinding, ReviewSeverity

# Import only essential types at module level
from .supervisor import SupervisorDecision, TaskType
from .testing_agent import TestResult, TestStatus, TestSuiteResult, TestType

# New orchestration system imports (preferred) - lazy import to avoid circular imports
UnifiedOrchestrator = None
create_orchestrator = None
OrchestrationCompat = None


def _get_new_orchestration():
    """Lazy import of new orchestration system."""
    global UnifiedOrchestrator, create_orchestrator, OrchestrationCompat
    if UnifiedOrchestrator is None:
        try:
            from ..orchestration import UnifiedOrchestrator, create_orchestrator
            from .orchestrator_compat import OrchestrationCompat
        except ImportError as e:
            import logging

            logging.warning(f"Could not import new orchestration system: {e}")
    return UnifiedOrchestrator, create_orchestrator, OrchestrationCompat


# Import agent classes lazily to avoid circular imports
if TYPE_CHECKING:
    from .content_agent import ContentAgent
    from .orchestrator import Orchestrator
    from .quiz_agent import QuizAgent
    from .review_agent import ReviewAgent
    from .script_agent import ScriptAgent
    from .supervisor import SupervisorAgent
    from .supervisor_complete import CompleteSupervisorAgent
    from .terrain_agent import TerrainAgent
    from .testing_agent import TestingAgent

# Direct imports for runtime access
try:
    from .content_agent import ContentAgent
    from .orchestrator import Orchestrator
    from .quiz_agent import QuizAgent
    from .review_agent import ReviewAgent
    from .script_agent import ScriptAgent
    from .supervisor import SupervisorAgent
    from .supervisor_complete import CompleteSupervisorAgent
    from .terrain_agent import TerrainAgent
    from .testing_agent import TestingAgent
except ImportError as e:
    import logging

    logging.warning(f"Failed to import agents: {e}")

# Version
__version__ = "1.0.0"

# Convenience imports
__all__ = [
    # Base classes
    "BaseAgent",
    "AgentConfig",
    "AgentState",
    "TaskResult",
    "AgentStatus",
    "AgentPriority",
    # Supervisor
    "SupervisorAgent",
    "TaskType",
    "SupervisorDecision",
    # Specialized agents
    "ContentAgent",
    "QuizAgent",
    "TerrainAgent",
    "ScriptAgent",
    "ReviewAgent",
    "ReviewSeverity",
    "ReviewFinding",
    "TestingAgent",
    "TestType",
    "TestStatus",
    "TestResult",
    "TestSuiteResult",
    # Orchestration (legacy)
    "Orchestrator",
    "OrchestrationRequest",
    "OrchestrationResult",
    "WorkflowType",
    # New orchestration system
    "UnifiedOrchestrator",
    "OrchestrationCompat",
    # Factory functions
    "create_orchestrator",
    "create_agent",
    "get_available_agents",
]


# Agent registry - lazy loading
def _get_agent_registry():
    """Get agent registry with lazy loading to avoid circular imports"""
    from .content_agent import ContentAgent
    from .quiz_agent import QuizAgent
    from .review_agent import ReviewAgent
    from .script_agent import ScriptAgent
    from .supervisor import SupervisorAgent
    from .terrain_agent import TerrainAgent
    from .testing_agent import TestingAgent

    return {
        "supervisor": SupervisorAgent,
        "content": ContentAgent,
        "quiz": QuizAgent,
        "terrain": TerrainAgent,
        "script": ScriptAgent,
        "review": ReviewAgent,
        "testing": TestingAgent,
    }


def create_orchestrator(config: Optional[dict[str, Any]] = None):
    """
    Create and configure an orchestrator instance.

    Args:
        config: Optional configuration dictionary

    Returns:
        Configured Orchestrator instance
    """
    from .orchestrator import Orchestrator

    return Orchestrator(config)


def create_agent(agent_type: str, config: Optional[AgentConfig] = None) -> BaseAgent:
    """
    Create a specific agent by type.

    Args:
        agent_type: Type of agent to create
        config: Optional agent configuration

    Returns:
        Agent instance

    Raises:
        ValueError: If agent type is not recognized
    """
    registry = _get_agent_registry()
    agent_class = registry.get(agent_type.lower())

    if not agent_class:
        raise ValueError(f"Unknown agent type: {agent_type}. Available: {list(registry.keys())}")

    return agent_class(config or AgentConfig())


def get_available_agents() -> list[str]:
    """
    Get list of available agent types.

    Returns:
        List of agent type names
    """
    registry = _get_agent_registry()
    return list(registry.keys())


# Module initialization message
import logging

logger = logging.getLogger(__name__)
logger.info(f"Multi-Agent System v{__version__} initialized")
