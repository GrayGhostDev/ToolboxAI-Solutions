"""
Data Flow Agents for ToolboxAI Platform

This module provides agents for managing data flow, schema validation,
event bus operations, cache invalidation, and conflict resolution.
"""

from typing import Dict, Any, Optional, List, Set
from datetime import datetime
import asyncio
import logging
from enum import Enum
import json

from .base_integration_agent import BaseIntegrationAgent, IntegrationPlatform, IntegrationEvent

logger = logging.getLogger(__name__)


class SchemaType(Enum):
    """Schema validation types"""
    JSON_SCHEMA = "json_schema"
    PROTOBUF = "protobuf"
    GRAPHQL = "graphql"
    OPENAPI = "openapi"


class SchemaValidatorAgent(BaseIntegrationAgent):
    """
    Agent responsible for validating data schemas across platforms.
    """

    def __init__(self, name: str = "SchemaValidatorAgent"):
        super().__init__(name, IntegrationPlatform.BACKEND)
        self.schemas: Dict[str, Any] = {}
        self.validation_history: List[Dict[str, Any]] = []

    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on schema validator"""
        return {
            "status": "healthy",
            "agent": self.name,
            "platform": self.platform.value,
            "registered_schemas": len(self.schemas),
            "validations_performed": len(self.validation_history),
            "timestamp": datetime.utcnow().isoformat()
        }

    async def register_schema(self, schema_name: str, schema_type: SchemaType,
                            definition: Dict[str, Any], platform: IntegrationPlatform,
                            version: str = "1.0.0"):
        """Register a schema for validation"""
        schema_key = f"{platform.value}:{schema_name}:{version}"

        self.schemas[schema_key] = {
            "name": schema_name,
            "type": schema_type.value if isinstance(schema_type, SchemaType) else schema_type,
            "definition": definition,
            "platform": platform.value if isinstance(platform, IntegrationPlatform) else platform,
            "version": version,
            "registered_at": datetime.utcnow()
        }

        await self.publish_event(IntegrationEvent(
            event_type="schema_registered",
            source=self.platform,
            target=platform if isinstance(platform, IntegrationPlatform) else IntegrationPlatform.BACKEND,
            data={"schema": schema_name, "version": version}
        ))

        logger.info(f"Schema registered: {schema_key}")

    async def validate(self, data: Any, schema_name: str, platform: IntegrationPlatform,
                      version: str = "1.0.0") -> Dict[str, Any]:
        """Validate data against a schema"""
        schema_key = f"{platform.value}:{schema_name}:{version}"

        if schema_key not in self.schemas:
            return {
                "valid": False,
                "errors": [f"Schema {schema_key} not found"]
            }

        # Mock validation
        validation_result = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "schema": schema_key,
            "timestamp": datetime.utcnow().isoformat()
        }

        # Simple type checking (mock implementation)
        schema = self.schemas[schema_key]
        if "properties" in schema["definition"]:
            for prop, prop_schema in schema["definition"]["properties"].items():
                if prop_schema.get("required", False) and prop not in data:
                    validation_result["valid"] = False
                    validation_result["errors"].append(f"Required property '{prop}' missing")

        self.validation_history.append(validation_result)

        await self.publish_event(IntegrationEvent(
            event_type="schema_validated",
            source=self.platform,
            target=platform,
            data=validation_result
        ))

        return validation_result

    async def cleanup(self):
        """Clean up schema validator resources"""
        self.schemas.clear()
        self.validation_history.clear()
        await super().cleanup()


class EventBusAgent(BaseIntegrationAgent):
    """
    Agent responsible for managing the event bus for inter-platform communication.
    """

    def __init__(self, name: str = "EventBusAgent"):
        super().__init__(name, IntegrationPlatform.BACKEND)
        self.event_topics: Dict[str, List[Any]] = {}
        self.subscribers: Dict[str, List[Any]] = {}
        self.event_history: List[Dict[str, Any]] = []

    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on event bus"""
        return {
            "status": "healthy",
            "agent": self.name,
            "platform": self.platform.value,
            "topics": len(self.event_topics),
            "total_subscribers": sum(len(subs) for subs in self.subscribers.values()),
            "events_processed": len(self.event_history),
            "timestamp": datetime.utcnow().isoformat()
        }

    async def create_topic(self, topic_name: str):
        """Create an event topic"""
        if topic_name not in self.event_topics:
            self.event_topics[topic_name] = []
            self.subscribers[topic_name] = []

            await self.publish_event(IntegrationEvent(
                event_type="topic_created",
                source=self.platform,
                target=IntegrationPlatform.BACKEND,
                data={"topic": topic_name}
            ))

            logger.info(f"Event topic created: {topic_name}")

    async def subscribe(self, topic_name: str, subscriber: Any):
        """Subscribe to an event topic"""
        if topic_name not in self.event_topics:
            await self.create_topic(topic_name)

        self.subscribers[topic_name].append(subscriber)
        logger.info(f"Subscriber added to topic: {topic_name}")

    async def publish_to_topic(self, topic_name: str, event_data: Dict[str, Any]):
        """Publish an event to a topic"""
        if topic_name not in self.event_topics:
            await self.create_topic(topic_name)

        event = {
            "topic": topic_name,
            "data": event_data,
            "timestamp": datetime.utcnow().isoformat()
        }

        self.event_topics[topic_name].append(event)
        self.event_history.append(event)

        # Notify subscribers (mock implementation)
        for subscriber in self.subscribers.get(topic_name, []):
            try:
                # Mock notification
                logger.debug(f"Notifying subscriber of event on topic: {topic_name}")
            except Exception as e:
                logger.error(f"Error notifying subscriber: {e}")

        await self.publish_event(IntegrationEvent(
            event_type="event_published",
            source=self.platform,
            target=IntegrationPlatform.BACKEND,
            data=event
        ))

    async def cleanup(self):
        """Clean up event bus resources"""
        self.event_topics.clear()
        self.subscribers.clear()
        self.event_history.clear()
        await super().cleanup()


class CacheInvalidationAgent(BaseIntegrationAgent):
    """
    Agent responsible for managing cache invalidation across platforms.
    """

    def __init__(self, name: str = "CacheInvalidationAgent"):
        super().__init__(name, IntegrationPlatform.BACKEND)
        self.cache_keys: Set[str] = set()
        self.invalidation_rules: Dict[str, Any] = {}
        self.invalidation_history: List[Dict[str, Any]] = []

    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on cache invalidation"""
        return {
            "status": "healthy",
            "agent": self.name,
            "platform": self.platform.value,
            "cached_keys": len(self.cache_keys),
            "invalidation_rules": len(self.invalidation_rules),
            "invalidations_performed": len(self.invalidation_history),
            "timestamp": datetime.utcnow().isoformat()
        }

    async def register_key(self, cache_key: str, ttl: Optional[int] = None):
        """Register a cache key"""
        self.cache_keys.add(cache_key)

        if ttl:
            # Schedule automatic invalidation
            asyncio.create_task(self._schedule_invalidation(cache_key, ttl))

        logger.info(f"Cache key registered: {cache_key}")

    async def _schedule_invalidation(self, cache_key: str, ttl: int):
        """Schedule automatic cache invalidation"""
        await asyncio.sleep(ttl)
        await self.invalidate(cache_key)

    async def add_rule(self, rule_name: str, pattern: str, platforms: List[IntegrationPlatform]):
        """Add an invalidation rule"""
        self.invalidation_rules[rule_name] = {
            "pattern": pattern,
            "platforms": [p.value if isinstance(p, IntegrationPlatform) else p for p in platforms],
            "created_at": datetime.utcnow()
        }

        logger.info(f"Invalidation rule added: {rule_name}")

    async def invalidate(self, cache_key: str, cascade: bool = False) -> Dict[str, Any]:
        """Invalidate a cache key"""
        invalidation = {
            "key": cache_key,
            "cascade": cascade,
            "timestamp": datetime.utcnow().isoformat(),
            "affected_keys": [cache_key]
        }

        if cache_key in self.cache_keys:
            self.cache_keys.remove(cache_key)

        if cascade:
            # Find and invalidate related keys (mock implementation)
            related_keys = [k for k in self.cache_keys if cache_key in k]
            for key in related_keys:
                self.cache_keys.discard(key)
                invalidation["affected_keys"].append(key)

        self.invalidation_history.append(invalidation)

        await self.publish_event(IntegrationEvent(
            event_type="cache_invalidated",
            source=self.platform,
            target=IntegrationPlatform.BACKEND,
            data=invalidation
        ))

        logger.info(f"Cache invalidated: {cache_key} (cascade={cascade})")

        return invalidation

    async def cleanup(self):
        """Clean up cache invalidation resources"""
        self.cache_keys.clear()
        self.invalidation_rules.clear()
        self.invalidation_history.clear()
        await super().cleanup()


class ConflictResolutionAgent(BaseIntegrationAgent):
    """
    Agent responsible for resolving data conflicts during synchronization.
    """

    def __init__(self, name: str = "ConflictResolutionAgent"):
        super().__init__(name, IntegrationPlatform.BACKEND)
        self.resolution_strategies: Dict[str, Any] = {}
        self.conflict_history: List[Dict[str, Any]] = []

    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on conflict resolution"""
        return {
            "status": "healthy",
            "agent": self.name,
            "platform": self.platform.value,
            "strategies": len(self.resolution_strategies),
            "conflicts_resolved": len(self.conflict_history),
            "timestamp": datetime.utcnow().isoformat()
        }

    async def register_strategy(self, conflict_type: str, strategy: str,
                               priority_platform: Optional[IntegrationPlatform] = None):
        """Register a conflict resolution strategy"""
        self.resolution_strategies[conflict_type] = {
            "strategy": strategy,
            "priority_platform": priority_platform.value if priority_platform else None,
            "registered_at": datetime.utcnow()
        }

        logger.info(f"Resolution strategy registered for: {conflict_type}")

    async def resolve_conflict(self, conflict_type: str,
                              source_data: Dict[str, Any],
                              target_data: Dict[str, Any]) -> Dict[str, Any]:
        """Resolve a data conflict"""
        resolution = {
            "conflict_type": conflict_type,
            "resolved_at": datetime.utcnow().isoformat(),
            "strategy_used": "default"
        }

        if conflict_type in self.resolution_strategies:
            strategy = self.resolution_strategies[conflict_type]
            resolution["strategy_used"] = strategy["strategy"]

            # Apply resolution strategy (mock implementation)
            if strategy["strategy"] == "latest_wins":
                # Choose data with latest timestamp
                source_time = source_data.get("updated_at", "")
                target_time = target_data.get("updated_at", "")
                resolution["resolved_data"] = source_data if source_time > target_time else target_data
            elif strategy["strategy"] == "priority_platform":
                # Choose data from priority platform
                priority = strategy.get("priority_platform")
                resolution["resolved_data"] = source_data if priority == "source" else target_data
            else:
                # Merge strategy (default)
                resolution["resolved_data"] = {**target_data, **source_data}
        else:
            # Default: merge with source taking precedence
            resolution["resolved_data"] = {**target_data, **source_data}

        self.conflict_history.append(resolution)

        await self.publish_event(IntegrationEvent(
            event_type="conflict_resolved",
            source=self.platform,
            target=IntegrationPlatform.BACKEND,
            data=resolution
        ))

        logger.info(f"Conflict resolved: {conflict_type} using {resolution['strategy_used']}")

        return resolution

    async def cleanup(self):
        """Clean up conflict resolution resources"""
        self.resolution_strategies.clear()
        self.conflict_history.clear()
        await super().cleanup()


__all__ = [
    "SchemaType",
    "SchemaValidatorAgent",
    "EventBusAgent",
    "CacheInvalidationAgent",
    "ConflictResolutionAgent"
]