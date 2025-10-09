"""
Agent Configuration Module - LangChain Integration and Tracing Setup

This module provides configuration for all agents including LangChain/LangSmith
tracing, monitoring, and observability features.
"""

import os
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from enum import Enum

from langchain.callbacks.tracers import LangChainTracer
from langsmith import Client


class AgentType(Enum):
    """Types of agents in the system."""
    BASE = "base"
    CONTENT = "content"
    QUIZ = "quiz"
    TERRAIN = "terrain"
    SCRIPT = "script"
    REVIEW = "review"
    TESTING = "testing"
    SUPERVISOR = "supervisor"
    ORCHESTRATOR = "orchestrator"


@dataclass
class AgentConfig:
    """Configuration for individual agents with LangChain integration."""

    # Basic Configuration
    name: str = "BaseAgent"
    agent_type: AgentType = AgentType.BASE
    model: str = "gpt-3.5-turbo"
    temperature: float = 0.7
    max_retries: int = 3
    timeout: int = 300
    verbose: bool = False

    # Memory Configuration
    memory_enabled: bool = True
    max_memory_items: int = 100
    memory_ttl: int = 3600  # seconds

    # Context Configuration
    max_context_length: int = 128000
    max_tokens: int = 4096

    # Tool Configuration
    tools: List[Any] = field(default_factory=list)
    tool_timeout: int = 60

    # System Prompt
    system_prompt: str = ""

    # Collaboration Settings
    can_collaborate: bool = True
    max_collaborators: int = 5

    # Performance Settings
    enable_caching: bool = True
    cache_ttl: int = 600
    parallel_execution: bool = False

    # Monitoring Settings
    enable_metrics: bool = True
    enable_logging: bool = True
    log_level: str = "INFO"


class LangChainConfiguration:
    """
    Centralized LangChain/LangSmith configuration for all agents.
    Handles API keys, project settings, and tracing setup.
    """

    def __init__(self):
        """Initialize LangChain configuration with environment variables."""

        # Load LangChain credentials from environment
        self.api_key = os.getenv("LANGCHAIN_API_KEY")
        self.project_id = os.getenv("LANGCHAIN_PROJECT_ID")
        self.project_name = os.getenv(
            "LANGCHAIN_PROJECT",
            "ToolboxAI-Solutions"
        )
        self.endpoint = os.getenv(
            "LANGCHAIN_ENDPOINT",
            "https://api.smith.langchain.com"
        )

        # Enable tracing
        self.tracing_enabled = os.getenv("LANGCHAIN_TRACING_V2", "true").lower() == "true"

        # Initialize LangSmith client
        self.langsmith_client = None
        if self.api_key and self.tracing_enabled:
            try:
                self.langsmith_client = Client(
                    api_key=self.api_key,
                    api_url=self.endpoint
                )
            except Exception as e:
                print(f"Warning: Failed to initialize LangSmith client: {e}")

        # Store tracers for different agent types
        self.tracers: Dict[str, LangChainTracer] = {}

    def get_tracer(self, agent_name: str = None) -> Optional[LangChainTracer]:
        """
        Get or create a LangChain tracer for a specific agent.

        Args:
            agent_name: Name of the agent (used as project suffix)

        Returns:
            LangChainTracer instance or None if tracing disabled
        """
        if not self.tracing_enabled or not self.api_key:
            return None

        if agent_name not in self.tracers:
            project_name = f"{self.project_name}-{agent_name}" if agent_name else self.project_name

            try:
                self.tracers[agent_name] = LangChainTracer(
                    project_name=project_name,
                    client=self.langsmith_client
                )
            except Exception as e:
                print(f"Warning: Failed to create tracer for {agent_name}: {e}")
                return None

        return self.tracers[agent_name]

    def get_callbacks(self, agent_name: str = None) -> List:
        """
        Get callback handlers for LangChain operations.

        Args:
            agent_name: Name of the agent

        Returns:
            List of callback handlers
        """
        callbacks = []

        tracer = self.get_tracer(agent_name)
        if tracer:
            callbacks.append(tracer)

        return callbacks

    def log_run_url(self, run_id: str) -> str:
        """
        Get the LangSmith URL for a specific run.

        Args:
            run_id: The run ID from LangChain

        Returns:
            URL to view the run in LangSmith
        """
        if self.project_id:
            return f"https://smith.langchain.com/project/{self.project_id}/run/{run_id}"
        return f"https://smith.langchain.com/run/{run_id}"

    def update_environment(self):
        """Update os.environ with LangChain settings."""
        env_vars = {
            "LANGCHAIN_API_KEY": self.api_key,
            "LANGCHAIN_PROJECT_ID": self.project_id,
            "LANGCHAIN_PROJECT": self.project_name,
            "LANGCHAIN_TRACING_V2": str(self.tracing_enabled).lower(),
            "LANGCHAIN_ENDPOINT": self.endpoint,
            "LANGSMITH_API_KEY": self.api_key  # Some versions use LANGSMITH_API_KEY
        }

        for key, value in env_vars.items():
            if value:
                os.environ[key] = value


# Global configuration instances
langchain_config = LangChainConfiguration()
langchain_config.update_environment()


def get_agent_config(
    agent_type: AgentType = AgentType.BASE,
    **overrides
) -> AgentConfig:
    """
    Get agent configuration with type-specific defaults.

    Args:
        agent_type: Type of agent
        **overrides: Configuration overrides

    Returns:
        AgentConfig instance
    """
    # Base configuration
    config = AgentConfig(agent_type=agent_type)

    # Type-specific defaults
    if agent_type == AgentType.CONTENT:
        config.name = "ContentAgent"
        config.model = "gpt-4"
        config.temperature = 0.7
        config.max_tokens = 8192
        config.system_prompt = "You are an educational content generation expert."

    elif agent_type == AgentType.QUIZ:
        config.name = "QuizAgent"
        config.model = "gpt-3.5-turbo"
        config.temperature = 0.5
        config.system_prompt = "You are a quiz and assessment generation expert."

    elif agent_type == AgentType.TERRAIN:
        config.name = "TerrainAgent"
        config.model = "gpt-3.5-turbo"
        config.temperature = 0.8
        config.system_prompt = "You are a Roblox terrain and environment design expert."

    elif agent_type == AgentType.SCRIPT:
        config.name = "ScriptAgent"
        config.model = "gpt-4"
        config.temperature = 0.3
        config.system_prompt = "You are a Roblox Lua scripting expert."

    elif agent_type == AgentType.REVIEW:
        config.name = "ReviewAgent"
        config.model = "gpt-4"
        config.temperature = 0.2
        config.system_prompt = "You are a code review and quality assurance expert."

    elif agent_type == AgentType.TESTING:
        config.name = "TestingAgent"
        config.model = "gpt-3.5-turbo"
        config.temperature = 0.1
        config.system_prompt = "You are a testing and validation expert."

    elif agent_type == AgentType.SUPERVISOR:
        config.name = "SupervisorAgent"
        config.model = "gpt-4"
        config.temperature = 0.4
        config.max_collaborators = 10
        config.system_prompt = "You are a supervisor coordinating multiple specialized agents."

    elif agent_type == AgentType.ORCHESTRATOR:
        config.name = "Orchestrator"
        config.model = "gpt-4"
        config.temperature = 0.5
        config.max_collaborators = 20
        config.parallel_execution = True
        config.system_prompt = "You are the main orchestrator managing the entire agent system."

    # Apply overrides
    for key, value in overrides.items():
        if hasattr(config, key):
            setattr(config, key, value)

    return config


def get_llm_config(agent_config: AgentConfig) -> Dict[str, Any]:
    """
    Get LLM configuration dictionary for LangChain.

    Args:
        agent_config: Agent configuration

    Returns:
        Dictionary of LLM parameters
    """
    return {
        "model": agent_config.model,
        "temperature": agent_config.temperature,
        "max_tokens": agent_config.max_tokens,
        "callbacks": langchain_config.get_callbacks(agent_config.name),
        "verbose": agent_config.verbose,
        "api_key": os.getenv("OPENAI_API_KEY"),  # or appropriate API key
        "timeout": agent_config.timeout,
        "max_retries": agent_config.max_retries
    }