"""
Agent Registry and Factory System

This module provides a centralized registry for all agent types and a factory
for dynamic agent instantiation based on workload and requirements.

Author: ToolboxAI Team
Created: 2025-09-17
Version: 1.0.0
"""

import asyncio
import importlib
import inspect
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Type, Union

from core.agents.base_agent import BaseAgent, AgentConfig, AgentCapability

logger = logging.getLogger(__name__)


class AgentCategory(Enum):
    """Categories of agents in the system."""
    EDUCATIONAL = "educational"
    CONTENT = "content"
    ASSESSMENT = "assessment"
    DATABASE = "database"
    INTEGRATION = "integration"
    GITHUB = "github"
    WORKTREE = "worktree"
    NLU = "nlu"
    MONITORING = "monitoring"
    QUALITY = "quality"
    DOCUMENTATION = "documentation"
    TESTING = "testing"
    REVIEW = "review"
    ORCHESTRATION = "orchestration"


@dataclass
class AgentMetadata:
    """Metadata for registered agents."""
    name: str
    category: AgentCategory
    class_path: str
    capabilities: List[AgentCapability] = field(default_factory=list)
    description: str = ""
    version: str = "1.0.0"
    dependencies: List[str] = field(default_factory=list)
    config_schema: Dict[str, Any] = field(default_factory=dict)
    max_instances: int = 10
    min_instances: int = 0
    auto_scale: bool = True
    priority: int = 5  # 1-10, higher is more important
    tags: List[str] = field(default_factory=list)


@dataclass
class AgentInstance:
    """Represents an active agent instance."""
    instance_id: str
    agent_name: str
    agent: BaseAgent
    created_at: datetime
    last_used: datetime
    task_count: int = 0
    is_busy: bool = False
    metadata: Optional[AgentMetadata] = None


class AgentRegistry:
    """
    Central registry for all agent types in the system.

    Maintains a catalog of available agents, their metadata, and provides
    discovery services for agent capabilities.
    """

    def __init__(self):
        """Initialize the agent registry."""
        self.registered_agents: Dict[str, AgentMetadata] = {}
        self.agent_categories: Dict[AgentCategory, List[str]] = {
            category: [] for category in AgentCategory
        }
        self.capability_index: Dict[AgentCapability, List[str]] = {}
        self.tag_index: Dict[str, List[str]] = {}

        # Auto-discover and register agents
        self._auto_discover_agents()

    def _auto_discover_agents(self):
        """Automatically discover and register agents from known locations."""
        # Define agent discovery paths
        discovery_paths = [
            ("core.agents", AgentCategory.CONTENT),
            ("core.agents.educational", AgentCategory.EDUCATIONAL),
            ("core.agents.github_agents", AgentCategory.GITHUB),
            ("core.agents.database", AgentCategory.DATABASE),
            ("core.agents.integration", AgentCategory.INTEGRATION),
            ("core.agents.nlu", AgentCategory.NLU),
        ]

        for module_path, category in discovery_paths:
            self._discover_agents_in_module(module_path, category)

        logger.info(f"Auto-discovered {len(self.registered_agents)} agents")

    def _discover_agents_in_module(self, module_path: str, category: AgentCategory):
        """Discover agents in a specific module.

        Args:
            module_path: Python module path to search
            category: Category for agents in this module
        """
        try:
            module = importlib.import_module(module_path)

            for name, obj in inspect.getmembers(module):
                if (inspect.isclass(obj) and
                    issubclass(obj, BaseAgent) and
                    obj != BaseAgent and
                    not name.startswith('_')):

                    # Create metadata for the agent
                    metadata = AgentMetadata(
                        name=name,
                        category=category,
                        class_path=f"{module_path}.{name}",
                        description=obj.__doc__ or "",
                        capabilities=self._extract_capabilities(obj),
                        tags=self._extract_tags(obj)
                    )

                    self.register_agent(name, metadata)

        except ImportError as e:
            logger.warning(f"Could not import module {module_path}: {e}")
        except Exception as e:
            logger.error(f"Error discovering agents in {module_path}: {e}")

    def _extract_capabilities(self, agent_class: Type[BaseAgent]) -> List[AgentCapability]:
        """Extract capabilities from an agent class.

        Args:
            agent_class: Agent class to analyze

        Returns:
            List of capabilities
        """
        capabilities = []

        # Check for capability attributes or methods
        if hasattr(agent_class, 'capabilities'):
            caps = agent_class.capabilities
            if isinstance(caps, list):
                capabilities.extend(caps)

        # Analyze methods to infer capabilities
        for method_name in dir(agent_class):
            if method_name.startswith('can_'):
                capability_name = method_name[4:].upper()
                try:
                    capability = AgentCapability[capability_name]
                    capabilities.append(capability)
                except KeyError:
                    pass

        return capabilities

    def _extract_tags(self, agent_class: Type[BaseAgent]) -> List[str]:
        """Extract tags from an agent class.

        Args:
            agent_class: Agent class to analyze

        Returns:
            List of tags
        """
        tags = []

        # Check for tags attribute
        if hasattr(agent_class, 'tags'):
            agent_tags = agent_class.tags
            if isinstance(agent_tags, list):
                tags.extend(agent_tags)

        # Add class name as tag
        tags.append(agent_class.__name__.lower())

        return tags

    def register_agent(self, name: str, metadata: AgentMetadata):
        """Register an agent in the registry.

        Args:
            name: Unique name for the agent
            metadata: Agent metadata
        """
        self.registered_agents[name] = metadata

        # Update category index
        self.agent_categories[metadata.category].append(name)

        # Update capability index
        for capability in metadata.capabilities:
            if capability not in self.capability_index:
                self.capability_index[capability] = []
            self.capability_index[capability].append(name)

        # Update tag index
        for tag in metadata.tags:
            if tag not in self.tag_index:
                self.tag_index[tag] = []
            self.tag_index[tag].append(name)

        logger.debug(f"Registered agent: {name} ({metadata.category.value})")

    def unregister_agent(self, name: str):
        """Unregister an agent from the registry.

        Args:
            name: Name of the agent to unregister
        """
        if name not in self.registered_agents:
            logger.warning(f"Agent {name} not found in registry")
            return

        metadata = self.registered_agents[name]

        # Remove from category index
        self.agent_categories[metadata.category].remove(name)

        # Remove from capability index
        for capability in metadata.capabilities:
            self.capability_index[capability].remove(name)

        # Remove from tag index
        for tag in metadata.tags:
            self.tag_index[tag].remove(name)

        # Remove from registry
        del self.registered_agents[name]

        logger.info(f"Unregistered agent: {name}")

    def get_agent_metadata(self, name: str) -> Optional[AgentMetadata]:
        """Get metadata for a specific agent.

        Args:
            name: Name of the agent

        Returns:
            Agent metadata or None if not found
        """
        return self.registered_agents.get(name)

    def find_agents_by_category(self, category: AgentCategory) -> List[str]:
        """Find all agents in a specific category.

        Args:
            category: Agent category

        Returns:
            List of agent names
        """
        return self.agent_categories.get(category, [])

    def find_agents_by_capability(self, capability: AgentCapability) -> List[str]:
        """Find agents with a specific capability.

        Args:
            capability: Required capability

        Returns:
            List of agent names
        """
        return self.capability_index.get(capability, [])

    def find_agents_by_tag(self, tag: str) -> List[str]:
        """Find agents with a specific tag.

        Args:
            tag: Tag to search for

        Returns:
            List of agent names
        """
        return self.tag_index.get(tag, [])

    def search_agents(
        self,
        category: Optional[AgentCategory] = None,
        capabilities: Optional[List[AgentCapability]] = None,
        tags: Optional[List[str]] = None
    ) -> List[str]:
        """Search for agents matching criteria.

        Args:
            category: Optional category filter
            capabilities: Optional required capabilities
            tags: Optional required tags

        Returns:
            List of agent names matching all criteria
        """
        # Start with all agents
        results = set(self.registered_agents.keys())

        # Filter by category
        if category:
            category_agents = set(self.find_agents_by_category(category))
            results = results.intersection(category_agents)

        # Filter by capabilities
        if capabilities:
            for capability in capabilities:
                capability_agents = set(self.find_agents_by_capability(capability))
                results = results.intersection(capability_agents)

        # Filter by tags
        if tags:
            for tag in tags:
                tag_agents = set(self.find_agents_by_tag(tag))
                results = results.intersection(tag_agents)

        return list(results)

    def get_statistics(self) -> Dict[str, Any]:
        """Get registry statistics.

        Returns:
            Statistics about registered agents
        """
        stats = {
            "total_agents": len(self.registered_agents),
            "by_category": {},
            "by_capability": {},
            "tags": len(self.tag_index)
        }

        # Count by category
        for category in AgentCategory:
            count = len(self.agent_categories[category])
            if count > 0:
                stats["by_category"][category.value] = count

        # Count by capability
        for capability, agents in self.capability_index.items():
            if agents:
                stats["by_capability"][capability.value] = len(agents)

        return stats


class AgentFactory:
    """
    Factory for creating agent instances dynamically.

    Manages agent lifecycle, pooling, and auto-scaling based on workload.
    """

    def __init__(self, registry: Optional[AgentRegistry] = None):
        """Initialize the agent factory.

        Args:
            registry: Agent registry to use (creates new if None)
        """
        self.registry = registry or AgentRegistry()
        self.active_instances: Dict[str, AgentInstance] = {}
        self.instance_pools: Dict[str, List[AgentInstance]] = {}
        self.instance_counter = 0

        # Configuration
        self.max_total_instances = 100
        self.idle_timeout_seconds = 300  # 5 minutes
        self.enable_pooling = True
        self.enable_auto_scaling = True

        # Metrics
        self.metrics = {
            "total_created": 0,
            "total_destroyed": 0,
            "cache_hits": 0,
            "cache_misses": 0
        }

    def create_agent(
        self,
        agent_name: str,
        config: Optional[AgentConfig] = None,
        use_pool: bool = True
    ) -> Optional[BaseAgent]:
        """Create an agent instance.

        Args:
            agent_name: Name of the agent to create
            config: Optional agent configuration
            use_pool: Whether to use instance pooling

        Returns:
            Agent instance or None if creation failed
        """
        # Check registry
        metadata = self.registry.get_agent_metadata(agent_name)
        if not metadata:
            logger.error(f"Agent {agent_name} not found in registry")
            return None

        # Check pool for available instance
        if use_pool and self.enable_pooling:
            pooled_instance = self._get_from_pool(agent_name)
            if pooled_instance:
                self.metrics["cache_hits"] += 1
                return pooled_instance.agent

        # Create new instance
        self.metrics["cache_misses"] += 1
        agent = self._create_new_instance(metadata, config)

        if agent:
            self.metrics["total_created"] += 1

        return agent

    def _get_from_pool(self, agent_name: str) -> Optional[AgentInstance]:
        """Get an agent instance from the pool.

        Args:
            agent_name: Name of the agent

        Returns:
            Agent instance or None if pool is empty
        """
        pool = self.instance_pools.get(agent_name, [])

        for instance in pool:
            if not instance.is_busy:
                instance.is_busy = True
                instance.last_used = datetime.now()
                instance.task_count += 1
                return instance

        return None

    def _create_new_instance(
        self,
        metadata: AgentMetadata,
        config: Optional[AgentConfig] = None
    ) -> Optional[BaseAgent]:
        """Create a new agent instance.

        Args:
            metadata: Agent metadata
            config: Optional agent configuration

        Returns:
            Agent instance or None if creation failed
        """
        try:
            # Import the agent class
            module_path, class_name = metadata.class_path.rsplit('.', 1)
            module = importlib.import_module(module_path)
            agent_class = getattr(module, class_name)

            # Create configuration if not provided
            if config is None:
                config = AgentConfig(
                    name=f"{metadata.name}_{self.instance_counter}",
                    model="gpt-3.5-turbo",
                    temperature=0.7
                )

            # Create agent instance
            agent = agent_class(config)

            # Create instance wrapper
            instance = AgentInstance(
                instance_id=f"{metadata.name}_{self.instance_counter}",
                agent_name=metadata.name,
                agent=agent,
                created_at=datetime.now(),
                last_used=datetime.now(),
                is_busy=True,
                metadata=metadata
            )

            # Track instance
            self.active_instances[instance.instance_id] = instance

            # Add to pool
            if metadata.name not in self.instance_pools:
                self.instance_pools[metadata.name] = []
            self.instance_pools[metadata.name].append(instance)

            self.instance_counter += 1

            logger.info(f"Created agent instance: {instance.instance_id}")
            return agent

        except Exception as e:
            logger.error(f"Failed to create agent {metadata.name}: {e}")
            return None

    def release_agent(self, agent: BaseAgent):
        """Release an agent back to the pool.

        Args:
            agent: Agent to release
        """
        # Find instance
        for instance_id, instance in self.active_instances.items():
            if instance.agent == agent:
                instance.is_busy = False
                instance.last_used = datetime.now()
                logger.debug(f"Released agent instance: {instance_id}")
                return

    def destroy_agent(self, agent: BaseAgent):
        """Destroy an agent instance.

        Args:
            agent: Agent to destroy
        """
        # Find and remove instance
        for instance_id, instance in list(self.active_instances.items()):
            if instance.agent == agent:
                # Remove from pool
                pool = self.instance_pools.get(instance.agent_name, [])
                if instance in pool:
                    pool.remove(instance)

                # Remove from active instances
                del self.active_instances[instance_id]

                # Cleanup agent if needed
                if hasattr(agent, 'cleanup'):
                    try:
                        asyncio.create_task(agent.cleanup())
                    except Exception as e:
                        logger.error(f"Error cleaning up agent: {e}")

                self.metrics["total_destroyed"] += 1
                logger.info(f"Destroyed agent instance: {instance_id}")
                return

    def get_or_create_agent(
        self,
        agent_name: str,
        config: Optional[AgentConfig] = None
    ) -> Optional[BaseAgent]:
        """Get an existing agent or create a new one.

        Args:
            agent_name: Name of the agent
            config: Optional agent configuration

        Returns:
            Agent instance or None
        """
        return self.create_agent(agent_name, config, use_pool=True)

    def create_agent_by_capability(
        self,
        capability: AgentCapability,
        config: Optional[AgentConfig] = None
    ) -> Optional[BaseAgent]:
        """Create an agent with a specific capability.

        Args:
            capability: Required capability
            config: Optional agent configuration

        Returns:
            Agent instance or None
        """
        # Find agents with the capability
        agent_names = self.registry.find_agents_by_capability(capability)

        if not agent_names:
            logger.warning(f"No agents found with capability: {capability}")
            return None

        # Choose the first available agent
        # TODO: Implement better selection logic (e.g., based on load)
        agent_name = agent_names[0]
        return self.create_agent(agent_name, config)

    def scale_pool(self, agent_name: str, target_size: int):
        """Scale the pool for a specific agent type.

        Args:
            agent_name: Name of the agent
            target_size: Target pool size
        """
        metadata = self.registry.get_agent_metadata(agent_name)
        if not metadata:
            logger.error(f"Agent {agent_name} not found in registry")
            return

        current_pool = self.instance_pools.get(agent_name, [])
        current_size = len(current_pool)

        if current_size < target_size:
            # Create more instances
            for _ in range(target_size - current_size):
                self._create_new_instance(metadata)
        elif current_size > target_size:
            # Remove idle instances
            idle_instances = [i for i in current_pool if not i.is_busy]
            for instance in idle_instances[:current_size - target_size]:
                self.destroy_agent(instance.agent)

        logger.info(f"Scaled {agent_name} pool from {current_size} to {target_size}")

    async def cleanup_idle_instances(self):
        """Clean up idle instances that have exceeded timeout."""
        now = datetime.now()
        idle_timeout = timedelta(seconds=self.idle_timeout_seconds)

        for instance in list(self.active_instances.values()):
            if not instance.is_busy:
                idle_time = now - instance.last_used
                if idle_time > idle_timeout:
                    logger.info(f"Cleaning up idle instance: {instance.instance_id}")
                    self.destroy_agent(instance.agent)

    def get_statistics(self) -> Dict[str, Any]:
        """Get factory statistics.

        Returns:
            Statistics about agent instances
        """
        stats = {
            "total_instances": len(self.active_instances),
            "busy_instances": sum(1 for i in self.active_instances.values() if i.is_busy),
            "idle_instances": sum(1 for i in self.active_instances.values() if not i.is_busy),
            "pools": {},
            "metrics": self.metrics
        }

        # Pool statistics
        for agent_name, pool in self.instance_pools.items():
            stats["pools"][agent_name] = {
                "total": len(pool),
                "busy": sum(1 for i in pool if i.is_busy),
                "idle": sum(1 for i in pool if not i.is_busy)
            }

        return stats


# Global instances
_registry_instance: Optional[AgentRegistry] = None
_factory_instance: Optional[AgentFactory] = None


def get_registry() -> AgentRegistry:
    """Get the global agent registry instance.

    Returns:
        Agent registry
    """
    global _registry_instance
    if _registry_instance is None:
        _registry_instance = AgentRegistry()
    return _registry_instance


def get_factory() -> AgentFactory:
    """Get the global agent factory instance.

    Returns:
        Agent factory
    """
    global _factory_instance
    if _factory_instance is None:
        _factory_instance = AgentFactory(get_registry())
    return _factory_instance


def discover_and_register_agents():
    """Discover and register all available agents."""
    registry = get_registry()
    logger.info(f"Agent discovery complete. Registered {len(registry.registered_agents)} agents")
    return registry


def create_agent(name: str, config: Optional[AgentConfig] = None) -> Optional[BaseAgent]:
    """Convenience function to create an agent.

    Args:
        name: Name of the agent
        config: Optional agent configuration

    Returns:
        Agent instance or None
    """
    factory = get_factory()
    return factory.create_agent(name, config)