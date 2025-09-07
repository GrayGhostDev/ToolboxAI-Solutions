"""
Multi-Agent System for Roblox Educational Environment Generation

This module provides a comprehensive agent-based system for generating
AI-powered educational content in Roblox environments using LangChain/LangGraph.
"""

from .base_agent import BaseAgent, AgentConfig, AgentState, TaskResult, AgentStatus, AgentPriority

from .supervisor import SupervisorAgent, TaskType, SupervisorDecision

from .content_agent import ContentAgent
from .quiz_agent import QuizAgent
from .terrain_agent import TerrainAgent
from .script_agent import ScriptAgent
from .review_agent import ReviewAgent, ReviewSeverity, ReviewFinding

from .orchestrator import Orchestrator, OrchestrationRequest, OrchestrationResult, WorkflowType

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

# Agent registry
AGENT_REGISTRY = {
    "supervisor": SupervisorAgent,
    "content": ContentAgent,
    "quiz": QuizAgent,
    "terrain": TerrainAgent,
    "script": ScriptAgent,
    "review": ReviewAgent,
}


def create_orchestrator(config: dict = None) -> Orchestrator:
    """
    Create and configure an orchestrator instance.

    Args:
        config: Optional configuration dictionary

    Returns:
        Configured Orchestrator instance
    """
    return Orchestrator(config)


def create_agent(agent_type: str, config: AgentConfig = None) -> BaseAgent:
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
    agent_class = AGENT_REGISTRY.get(agent_type.lower())

    if not agent_class:
        raise ValueError(f"Unknown agent type: {agent_type}. Available: {list(AGENT_REGISTRY.keys())}")

    return agent_class(config)


def get_available_agents() -> list:
    """
    Get list of available agent types.

    Returns:
        List of agent type names
    """
    return list(AGENT_REGISTRY.keys())


# Module initialization message
import logging

logger = logging.getLogger(__name__)
logger.info(f"Multi-Agent System v{__version__} initialized")
