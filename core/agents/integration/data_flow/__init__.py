"""
Data Flow Integration Agents

This module provides agents for data flow and synchronization including:
- Schema validation across platforms
- Event bus management
- Cache invalidation coordination
- Conflict resolution
"""

from .schema_validator_agent import (
    SchemaValidatorAgent,
    Schema,
    SchemaType,
    ValidationLevel,
    ValidationResult,
    SchemaMapping,
    SchemaEvolution
)

# Import other agents when available
try:
    from .event_bus_agent import EventBusAgent
except ImportError:
    pass

try:
    from .cache_invalidation_agent import CacheInvalidationAgent
except ImportError:
    pass

try:
    from .conflict_resolution_agent import ConflictResolutionAgent
except ImportError:
    pass

__all__ = [
    # Schema Validation
    "SchemaValidatorAgent",
    "Schema",
    "SchemaType",
    "ValidationLevel",
    "ValidationResult",
    "SchemaMapping",
    "SchemaEvolution",

    # Event Bus (future)
    "EventBusAgent",

    # Cache Invalidation (future)
    "CacheInvalidationAgent",

    # Conflict Resolution (future)
    "ConflictResolutionAgent"
]