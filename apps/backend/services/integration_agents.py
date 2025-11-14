"""
Integration Agents Service - Manages AI Agent Swarm for Application Integration

This service initializes and manages all integration agents for seamless
communication between Backend, Frontend/Dashboard, and Roblox/Studio.
"""

import asyncio
import logging
import os

# Import integration agents
import sys
from datetime import datetime
from typing import Any

# Add project root to path if not already there
project_root = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

try:
    from core.agents.integration import IntegrationEvent, IntegrationPlatform
    from core.agents.integration.backend import APIGatewayAgent, DatabaseSyncAgent
    from core.agents.integration.data_flow import SchemaValidatorAgent
    from core.agents.integration.frontend import RealtimeUpdateAgent, UISyncAgent
    from core.agents.integration.orchestration import IntegrationCoordinator
    from core.agents.integration.roblox import StudioBridgeAgent

    INTEGRATION_AVAILABLE = True
except ImportError as e:
    logger = logging.getLogger(__name__)
    logger.warning(f"Integration agents not available: {e}")
    INTEGRATION_AVAILABLE = False

    # Mock classes for compatibility
    class IntegrationPlatform:
        BACKEND = "backend"
        FRONTEND = "frontend"
        ROBLOX = "roblox"
        DATABASE = "database"
        CACHE = "cache"

    class IntegrationEvent:
        pass

    class MockAgent:
        """Base mock agent with health check"""

        def __init__(self, agent_name="MockAgent"):
            self.agent_name = agent_name
            self.healthy = True

        async def health_check(self):
            return {
                "status": "healthy" if self.healthy else "unhealthy",
                "healthy": self.healthy,
                "message": f"{self.agent_name} - mock implementation",
                "agent_type": self.agent_name,
            }

        async def cleanup(self):
            """Mock cleanup method"""
            pass

    class APIGatewayAgent(MockAgent):
        def __init__(self):
            super().__init__("APIGatewayAgent")

    class DatabaseSyncAgent(MockAgent):
        def __init__(self):
            super().__init__("DatabaseSyncAgent")

        async def connect_platform(self, platform, connection):
            """Mock connect platform method"""
            pass

        async def sync_data(self, source_platform, target_platform, data):
            """Mock sync data method"""
            return type("Result", (), {"success": True, "output": {}, "error": None})()

    class UISyncAgent(MockAgent):
        def __init__(self):
            super().__init__("UISyncAgent")

    class RealtimeUpdateAgent(MockAgent):
        def __init__(self):
            super().__init__("RealtimeUpdateAgent")

        async def initialize_pusher(self, app_id, key, secret, cluster):
            """Mock initialize pusher method"""
            pass

        async def subscribe_channel(self, channel):
            """Mock subscribe channel method"""
            pass

        async def broadcast_event(self, channel_name, event_name, data):
            """Mock broadcast event method"""
            return type("Result", (), {"success": True, "output": {}, "error": None})()

    class StudioBridgeAgent(MockAgent):
        def __init__(self):
            super().__init__("StudioBridgeAgent")

    class IntegrationCoordinator:
        def __init__(self):
            self.healthy = True
            self.agent_name = "IntegrationCoordinator"

        async def health_check(self):
            return {
                "status": "healthy" if self.healthy else "unhealthy",
                "healthy": self.healthy,
                "message": f"{self.agent_name} - mock implementation",
                "agent_type": self.agent_name,
            }

        async def register_agent(self, agent_type, agent):
            """Mock register agent method"""
            pass

        async def create_workflow(self, name, description, template=None, custom_tasks=None):
            """Mock create workflow method"""
            return type("Workflow", (), {"workflow_id": "mock-workflow-id"})()

        async def execute_workflow(self, workflow_id, parameters=None):
            """Mock execute workflow method"""
            return type("Result", (), {"success": True, "output": {}, "error": None})()

        async def cleanup(self):
            """Mock cleanup method"""
            pass

    class SchemaValidatorAgent(MockAgent):
        def __init__(self):
            super().__init__("SchemaValidatorAgent")

        async def register_schema(self, schema_name, schema_type, definition, platform, version):
            """Mock register schema method"""
            pass


# Import existing services for connection
from apps.backend.core.config import settings

logger = logging.getLogger(__name__)


class IntegrationAgentsManager:
    """
    Manages all integration agents for the ToolboxAI platform
    """

    def __init__(self):
        """Initialize the integration agents manager"""
        self.agents: dict[str, Any] = {}
        self.coordinator: IntegrationCoordinator | None = None
        self.initialized = False
        self._shutdown_event = asyncio.Event()

    async def initialize(self):
        """Initialize all integration agents and connect them to services"""
        if self.initialized:
            logger.info("Integration agents already initialized")
            return

        try:
            logger.info("Starting Integration Agents initialization...")

            if INTEGRATION_AVAILABLE:
                # Initialize backend agents
                self.agents["api_gateway"] = APIGatewayAgent()
                self.agents["database_sync"] = DatabaseSyncAgent()
                logger.info("Backend integration agents initialized")

                # Initialize frontend agents
                self.agents["ui_sync"] = UISyncAgent()
                self.agents["realtime_update"] = RealtimeUpdateAgent()
                logger.info("Frontend integration agents initialized")

                # Initialize Roblox agents
                self.agents["studio_bridge"] = StudioBridgeAgent()
                logger.info("Roblox integration agents initialized")

                # Initialize data flow agents
                self.agents["schema_validator"] = SchemaValidatorAgent()
                logger.info("Data flow agents initialized")

                # Initialize orchestration coordinator
                self.coordinator = IntegrationCoordinator()
                logger.info("Integration coordinator initialized")
            else:
                logger.warning("Integration agents not available, using mock agents")
                # Create mock agents for compatibility
                self.agents["api_gateway"] = APIGatewayAgent()
                self.agents["database_sync"] = DatabaseSyncAgent()
                self.agents["ui_sync"] = UISyncAgent()
                self.agents["realtime_update"] = RealtimeUpdateAgent()
                self.agents["studio_bridge"] = StudioBridgeAgent()
                self.agents["schema_validator"] = SchemaValidatorAgent()
                self.coordinator = IntegrationCoordinator()

            # Register all agents with the coordinator
            await self._register_agents()

            # Connect agents to platform services
            await self._connect_services()

            # Register default schemas
            await self._register_default_schemas()

            # Start background tasks
            asyncio.create_task(self._monitor_health())

            self.initialized = True
            logger.info(
                f"Integration Agents initialized successfully with {len(self.agents)} agents"
            )

        except Exception as e:
            logger.error(f"Failed to initialize integration agents: {e}")
            raise

    async def _register_agents(self):
        """Register all agents with the coordinator"""
        if not self.coordinator:
            logger.debug("No coordinator available, skipping agent registration")
            return

        try:
            for name, agent in self.agents.items():
                if agent is None:
                    continue
                agent_type = type(agent).__name__
                if hasattr(self.coordinator, "register_agent"):
                    await self.coordinator.register_agent(agent_type, agent)
                logger.debug(f"Registered agent: {agent_type}")

        except Exception as e:
            logger.error(f"Error registering agents: {e}")
            # Don't raise, allow partial initialization

    async def _connect_services(self):
        """Connect agents to existing platform services"""
        if not INTEGRATION_AVAILABLE:
            logger.debug("Integration agents not available, skipping service connections")
            return

        try:
            # Connect Database Sync Agent to PostgreSQL
            if (
                hasattr(settings, "DATABASE_URL")
                and settings.DATABASE_URL
                and self.agents.get("database_sync")
            ):
                # Import database manager
                from database.connection import DatabaseManager

                db_manager = DatabaseManager()
                await db_manager.initialize()

                if hasattr(self.agents["database_sync"], "connect_platform"):
                    await self.agents["database_sync"].connect_platform(
                        IntegrationPlatform.DATABASE, db_manager
                    )
                logger.info("Connected DatabaseSyncAgent to PostgreSQL")

            # Connect Database Sync Agent to Redis
            if hasattr(settings, "REDIS_URL") and settings.REDIS_URL:
                import redis.asyncio as redis

                redis_client = await redis.from_url(
                    settings.REDIS_URL, encoding="utf-8", decode_responses=True
                )

                await self.agents["database_sync"].connect_platform(
                    IntegrationPlatform.CACHE, redis_client
                )
                logger.info("Connected DatabaseSyncAgent to Redis")

            # Initialize Pusher for Realtime Update Agent
            if all(
                [
                    hasattr(settings, "PUSHER_APP_ID"),
                    hasattr(settings, "PUSHER_KEY"),
                    hasattr(settings, "PUSHER_SECRET"),
                    hasattr(settings, "PUSHER_CLUSTER"),
                ]
            ):
                await self.agents["realtime_update"].initialize_pusher(
                    app_id=settings.PUSHER_APP_ID,
                    key=settings.PUSHER_KEY,
                    secret=settings.PUSHER_SECRET,
                    cluster=settings.PUSHER_CLUSTER,
                )
                logger.info("Connected RealtimeUpdateAgent to Pusher")

                # Create default channels
                default_channels = [
                    "integration-status",
                    "workflow-updates",
                    "sync-notifications",
                    "agent-health",
                ]
                for channel in default_channels:
                    await self.agents["realtime_update"].subscribe_channel(channel)
                    logger.debug(f"Subscribed to channel: {channel}")

        except Exception as e:
            logger.error(f"Error connecting services: {e}")
            # Continue initialization even if some services fail to connect
            logger.warning("Some services failed to connect, continuing with reduced functionality")

    async def _register_default_schemas(self):
        """Register default schemas for cross-platform validation"""
        if not self.agents.get("schema_validator"):
            logger.debug("No schema validator available, skipping schema registration")
            return

        try:
            # Educational content schema
            educational_content_schema = {
                "type": "object",
                "properties": {
                    "content_id": {"type": "string"},
                    "title": {"type": "string"},
                    "description": {"type": "string"},
                    "grade_level": {"type": "integer", "minimum": 1, "maximum": 12},
                    "subject": {"type": "string"},
                    "learning_objectives": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                    "created_at": {"type": "string", "format": "date-time"},
                    "updated_at": {"type": "string", "format": "date-time"},
                },
                "required": ["content_id", "title", "grade_level", "subject"],
            }

            # Register for backend
            if INTEGRATION_AVAILABLE:
                from core.agents.integration.data_flow import SchemaType
            else:
                # Mock SchemaType enum
                class SchemaType:
                    JSON_SCHEMA = "json_schema"

            if hasattr(self.agents["schema_validator"], "register_schema"):
                await self.agents["schema_validator"].register_schema(
                    schema_name="educational_content",
                    schema_type=SchemaType.JSON_SCHEMA,
                    definition=educational_content_schema,
                    platform=IntegrationPlatform.BACKEND,
                    version="1.0.0",
                )

            # User schema
            user_schema = {
                "type": "object",
                "properties": {
                    "user_id": {"type": "string"},
                    "email": {"type": "string", "format": "email"},
                    "role": {"type": "string", "enum": ["student", "teacher", "admin"]},
                    "created_at": {"type": "string", "format": "date-time"},
                },
                "required": ["user_id", "email", "role"],
            }

            if hasattr(self.agents["schema_validator"], "register_schema"):
                await self.agents["schema_validator"].register_schema(
                    schema_name="user",
                    schema_type=SchemaType.JSON_SCHEMA,
                    definition=user_schema,
                    platform=IntegrationPlatform.BACKEND,
                    version="1.0.0",
                )

            logger.info("Default schemas registered")

        except Exception as e:
            logger.error(f"Error registering default schemas: {e}")

    async def execute_workflow(
        self,
        workflow_name: str,
        workflow_description: str,
        template: str | None = None,
        custom_tasks: list | None = None,
        parameters: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Execute an integration workflow"""
        if not self.coordinator:
            raise RuntimeError("Integration coordinator not initialized")

        try:
            # Create workflow
            workflow = await self.coordinator.create_workflow(
                name=workflow_name,
                description=workflow_description,
                template=template,
                custom_tasks=custom_tasks,
            )

            # Execute workflow
            result = await self.coordinator.execute_workflow(
                workflow_id=workflow.workflow_id, parameters=parameters
            )

            return {
                "workflow_id": workflow.workflow_id,
                "success": result.success,
                "output": result.output,
                "error": result.error if not result.success else None,
            }

        except Exception as e:
            logger.error(f"Error executing workflow: {e}")
            return {"success": False, "error": str(e)}

    async def get_agent_status(self, agent_name: str | None = None) -> dict[str, Any]:
        """Get status of integration agents"""
        status = {
            "initialized": self.initialized,
            "timestamp": datetime.utcnow().isoformat(),
            "agents": {},
        }

        if agent_name:
            # Get specific agent status
            if agent_name in self.agents:
                agent = self.agents[agent_name]
                if agent is not None and hasattr(agent, "health_check"):
                    try:
                        health = await agent.health_check()
                        status["agents"][agent_name] = health
                    except Exception as e:
                        status["agents"][agent_name] = {
                            "status": "error",
                            "healthy": False,
                            "error": str(e),
                        }
                else:
                    status["agents"][agent_name] = {
                        "status": "not_available",
                        "healthy": False,
                        "error": "Agent is None or missing health_check method",
                    }
        else:
            # Get all agents status
            for name, agent in self.agents.items():
                if agent is not None and hasattr(agent, "health_check"):
                    try:
                        health = await agent.health_check()
                        status["agents"][name] = health
                    except Exception as e:
                        status["agents"][name] = {
                            "status": "error",
                            "healthy": False,
                            "error": str(e),
                        }
                else:
                    status["agents"][name] = {
                        "status": "not_available",
                        "healthy": False,
                        "error": "Agent is None or missing health_check method",
                    }

        return status

    async def sync_data(
        self, source_platform: str, target_platform: str, data: dict[str, Any]
    ) -> dict[str, Any]:
        """Synchronize data between platforms"""
        try:
            source = IntegrationPlatform[source_platform.upper()]
            target = IntegrationPlatform[target_platform.upper()]

            result = await self.agents["database_sync"].sync_data(
                source_platform=source, target_platform=target, data=data
            )

            return {
                "success": result.success,
                "output": result.output,
                "error": result.error if not result.success else None,
            }

        except Exception as e:
            logger.error(f"Error syncing data: {e}")
            return {"success": False, "error": str(e)}

    async def broadcast_event(self, channel: str, event: str, data: Any) -> dict[str, Any]:
        """Broadcast an event through the realtime update agent"""
        try:
            result = await self.agents["realtime_update"].broadcast_event(
                channel_name=channel, event_name=event, data=data
            )

            return {
                "success": result.success,
                "output": result.output,
                "error": result.error if not result.success else None,
            }

        except Exception as e:
            logger.error(f"Error broadcasting event: {e}")
            return {"success": False, "error": str(e)}

    async def _monitor_health(self):
        """Background task to monitor agent health"""
        while not self._shutdown_event.is_set():
            try:
                # Check health every 30 seconds
                await asyncio.sleep(30)

                # Get health status
                status = await self.get_agent_status()

                # Broadcast health status
                if self.agents.get("realtime_update"):
                    await self.broadcast_event(
                        channel="agent-health", event="health_update", data=status
                    )

                # Log any unhealthy agents
                for agent_name, health in status.get("agents", {}).items():
                    if health.get("status") != "healthy":
                        logger.warning(
                            f"Agent {agent_name} is {health.get('status')}: {health.get('error')}"
                        )

            except Exception as e:
                logger.error(f"Error in health monitoring: {e}")

    async def shutdown(self):
        """Shutdown all agents gracefully"""
        logger.info("Shutting down integration agents...")

        # Signal shutdown to background tasks
        self._shutdown_event.set()

        # Cleanup each agent
        for name, agent in self.agents.items():
            if agent is not None and hasattr(agent, "cleanup"):
                try:
                    await agent.cleanup()
                    logger.debug(f"Cleaned up agent: {name}")
                except Exception as e:
                    logger.error(f"Error cleaning up agent {name}: {e}")
            else:
                logger.debug(f"Skipping cleanup for agent {name} (None or no cleanup method)")

        self.agents.clear()
        self.coordinator = None
        self.initialized = False

        logger.info("Integration agents shutdown complete")


# Singleton instance
integration_manager = IntegrationAgentsManager()


# Convenience functions for direct access
async def get_integration_manager() -> IntegrationAgentsManager:
    """Get the integration manager instance"""
    if not integration_manager.initialized:
        await integration_manager.initialize()
    return integration_manager


async def execute_integration_workflow(
    workflow_name: str,
    workflow_description: str,
    template: str | None = None,
    custom_tasks: list | None = None,
    parameters: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Execute an integration workflow"""
    manager = await get_integration_manager()
    return await manager.execute_workflow(
        workflow_name, workflow_description, template, custom_tasks, parameters
    )
