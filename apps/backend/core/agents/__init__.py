"""
Core Agent Module - Compatibility Shim Layer

This module provides backward-compatible imports for agent classes.
It re-exports agents from apps.backend.agents.agent_classes to maintain
compatibility with code that imports from core.agents.

The actual agent implementations are in apps.backend.agents.agent_classes.
"""

from apps.backend.agents.agent_classes import CodeReviewAgent as ReviewAgent
from apps.backend.agents.agent_classes import ContentGenerationAgent as ContentAgent
from apps.backend.agents.agent_classes import QuizGenerationAgent as QuizAgent
from apps.backend.agents.agent_classes import ScriptGenerationAgent as ScriptAgent
from apps.backend.agents.agent_classes import TerrainGenerationAgent as TerrainAgent

# Import SupervisorAgent from agent module
try:
    from apps.backend.agents.agent import SupervisorAgent
except ImportError:
    # Create placeholder if not available
    class SupervisorAgent:
        """Placeholder Supervisor Agent"""

        def __init__(self, *args, **kwargs):
            pass


# Re-export with both naming conventions
__all__ = [
    "ContentAgent",
    "QuizAgent",
    "ReviewAgent",
    "ScriptAgent",
    "TerrainAgent",
    "SupervisorAgent",
    "ContentGenerationAgent",
    "QuizGenerationAgent",
    "CodeReviewAgent",
    "ScriptGenerationAgent",
    "TerrainGenerationAgent",
]

# Provide convenient access to classes with both names
ContentGenerationAgent = ContentAgent
QuizGenerationAgent = QuizAgent
CodeReviewAgent = ReviewAgent
ScriptGenerationAgent = ScriptAgent
TerrainGenerationAgent = TerrainAgent
