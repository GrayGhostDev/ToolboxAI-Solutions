"""
Multi-Agent System for Roblox Educational Environment Generation

This module provides a comprehensive agent-based system for generating
AI-powered educational content in Roblox environments using LangChain/LangGraph.
"""

from typing import Optional, Dict, Any, List, TYPE_CHECKING

from .base_agent import BaseAgent, AgentConfig, AgentState, TaskResult, AgentStatus, AgentPriority

# Import only essential types at module level
from .supervisor import TaskType, SupervisorDecision
from .review_agent import ReviewSeverity, ReviewFinding
from .testing_agent import TestType, TestStatus, TestResult, TestSuiteResult
from .orchestrator import OrchestrationRequest, OrchestrationResult, WorkflowType

# Import agent classes lazily to avoid circular imports
if TYPE_CHECKING:
    from .supervisor import SupervisorAgent
    from .supervisor_complete import CompleteSupervisorAgent
    from .content_agent import ContentAgent
    from .quiz_agent import QuizAgent
    from .terrain_agent import TerrainAgent
    from .script_agent import ScriptAgent
    from .review_agent import ReviewAgent
    from .testing_agent import TestingAgent
    from .orchestrator import Orchestrator

# Direct imports for runtime access
try:
    from .supervisor import SupervisorAgent
    from .supervisor_complete import CompleteSupervisorAgent
    from .content_agent import ContentAgent
    from .quiz_agent import QuizAgent
    from .terrain_agent import TerrainAgent
    from .script_agent import ScriptAgent
    from .review_agent import ReviewAgent
    from .testing_agent import TestingAgent
    from .orchestrator import Orchestrator
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
    # Orchestration
    "Orchestrator",
    "OrchestrationRequest",
    "OrchestrationResult",
    "WorkflowType",
    # Factory functions
    "create_orchestrator",
    "create_agent",
    "get_available_agents",
]

# Agent registry - lazy loading
def _get_agent_registry():
    """Get agent registry with lazy loading to avoid circular imports"""
    from .supervisor import SupervisorAgent
    from .content_agent import ContentAgent
    from .quiz_agent import QuizAgent
    from .terrain_agent import TerrainAgent
    from .script_agent import ScriptAgent
    from .review_agent import ReviewAgent
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


def create_orchestrator(config: Optional[Dict[str, Any]] = None):
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


def get_available_agents() -> List[str]:
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
