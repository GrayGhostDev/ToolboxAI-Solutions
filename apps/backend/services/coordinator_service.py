"""
Coordinator Service - Connects Agent Coordinators to FastAPI Backend

This service initializes and manages the coordinator system, providing
integration with LangChain tracing and Pusher for real-time updates.
"""

import os
import asyncio
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
import json
import redis.asyncio as redis

from langchain.callbacks.tracers import LangChainTracer
from langsmith import Client

# Import coordinators from core
from core.coordinators import (
    MainCoordinator,
    WorkflowCoordinator,
    ResourceCoordinator,
    SyncCoordinator,
    ErrorCoordinator
)

# Import Pusher service for real-time updates
from apps.backend.services.pusher import pusher_service

logger = logging.getLogger(__name__)


class CoordinatorService:
    """
    Service that manages all coordinator components and provides
    a unified interface for the FastAPI backend.
    """

    def __init__(self):
        """Initialize the coordinator service with LangChain configuration."""

        # Set LangChain environment variables
        self._configure_langchain()

        # Redis configuration (using running redis-toolboxai container)
        self.redis_url = os.getenv("REDIS_URL", "redis://localhost:55007/2")
        self.redis_client = None

        # Initialize coordinators
        self.workflow_coordinator = WorkflowCoordinator()
        self.resource_coordinator = ResourceCoordinator()
        self.sync_coordinator = SyncCoordinator(redis_url=self.redis_url)
        self.error_coordinator = ErrorCoordinator()

        # Initialize main coordinator with sub-coordinators
        self.main_coordinator = MainCoordinator(
            workflow_coordinator=self.workflow_coordinator,
            resource_coordinator=self.resource_coordinator,
            sync_coordinator=self.sync_coordinator,
            error_coordinator=self.error_coordinator,
            config={
                "max_concurrent_requests": 10,
                "health_check_interval": 30,
                "enable_caching": True,
                "langchain_tracing": True
            }
        )

        # LangChain tracer for monitoring
        self.tracer = LangChainTracer(
            project_name="ToolboxAI-Coordinators",
            client=Client(
                api_key=os.getenv("LANGCHAIN_API_KEY"),
                api_url="https://api.smith.langchain.com"
            )
        )

        # Track initialization status
        self.is_initialized = False

    def _configure_langchain(self):
        """Configure LangChain environment variables."""
        # Only set defaults for non-sensitive values
        # API keys must come from environment
        langchain_defaults = {
            "LANGCHAIN_PROJECT": "ToolboxAI-Solutions",
            "LANGCHAIN_TRACING_V2": "true",
            "LANGCHAIN_ENDPOINT": "https://api.smith.langchain.com"
        }

        for key, value in langchain_defaults.items():
            if not os.getenv(key):
                os.environ[key] = value

        # Ensure required API keys are present
        if not os.getenv("LANGCHAIN_API_KEY"):
            logger.warning("LANGCHAIN_API_KEY not found in environment")
        if not os.getenv("LANGCHAIN_PROJECT_ID"):
            logger.warning("LANGCHAIN_PROJECT_ID not found in environment")

        logger.info("LangChain configuration updated")

    async def initialize(self):
        """
        Initialize all coordinators and establish connections.
        """
        try:
            logger.info("Initializing Coordinator Service...")

            # Connect to Redis
            self.redis_client = await redis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True
            )

            # Test Redis connection
            await self.redis_client.ping()
            logger.info(f"Connected to Redis at {self.redis_url}")

            # Initialize main coordinator
            await self.main_coordinator.initialize()

            # Register service in Redis
            await self._register_service()

            # Send initialization event via Pusher
            await self._notify_initialization()

            self.is_initialized = True
            logger.info("Coordinator Service initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize Coordinator Service: {e}")
            raise

    async def _register_service(self):
        """Register the coordinator service in Redis for service discovery."""
        service_info = {
            "name": "coordinator-service",
            "type": "orchestration",
            "status": "active",
            "host": "localhost",
            "port": 8009,
            "capabilities": [
                "agent-orchestration",
                "workflow-management",
                "resource-allocation",
                "error-handling"
            ],
            "registered_at": datetime.now().isoformat(),
            "langchain_enabled": True,
            "pusher_enabled": True
        }

        await self.redis_client.hset(
            "services:registry",
            "coordinator-service",
            json.dumps(service_info)
        )

        # Set expiry for health checking
        await self.redis_client.expire("services:health:coordinator-service", 60)

        logger.info("Coordinator Service registered in Redis")

    async def _notify_initialization(self):
        """Send initialization event via Pusher."""
        try:
            await pusher_service.trigger(
                channel="private-system",
                event="coordinator.initialized",
                data={
                    "service": "coordinator-service",
                    "timestamp": datetime.now().isoformat(),
                    "status": "ready",
                    "coordinators": [
                        "main", "workflow", "resource", "sync", "error"
                    ]
                }
            )
            logger.info("Initialization event sent via Pusher")
        except Exception as e:
            logger.warning(f"Failed to send Pusher notification: {e}")

    async def generate_educational_content(
        self,
        subject: str,
        grade_level: int,
        learning_objectives: List[str],
        environment_type: str = "interactive_classroom",
        include_quiz: bool = True,
        custom_parameters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate educational content using the coordinator system.

        Args:
            subject: The subject matter
            grade_level: Grade level (1-12)
            learning_objectives: List of learning objectives
            environment_type: Type of Roblox environment
            include_quiz: Whether to include quiz generation
            custom_parameters: Additional custom parameters

        Returns:
            Generated content with scripts, quiz, and metadata
        """
        if not self.is_initialized:
            raise RuntimeError("Coordinator Service not initialized")

        try:
            # Create request
            from core.coordinators.main_coordinator import ContentGenerationRequest

            request = ContentGenerationRequest(
                request_id=f"req_{datetime.now().timestamp()}",
                subject=subject,
                grade_level=grade_level,
                learning_objectives=learning_objectives,
                environment_type=environment_type,
                include_quiz=include_quiz,
                custom_parameters=custom_parameters or {},
                priority=1
            )

            # Send start event via Pusher
            await pusher_service.trigger(
                channel="private-agent-orchestration",
                event="generation.started",
                data={
                    "request_id": request.request_id,
                    "subject": subject,
                    "grade_level": grade_level
                }
            )

            # Execute generation with tracing
            with self.tracer as callback:
                result = await self.main_coordinator.generate_educational_content(
                    subject=subject,
                    grade_level=grade_level,
                    learning_objectives=learning_objectives,
                    environment_type=environment_type,
                    include_quiz=include_quiz,
                    custom_parameters=custom_parameters
                )

            # Send completion event via Pusher
            await pusher_service.trigger(
                channel="private-agent-orchestration",
                event="generation.completed",
                data={
                    "request_id": request.request_id,
                    "success": result.success,
                    "generation_time": result.generation_time
                }
            )

            return {
                "success": result.success,
                "request_id": result.request_id,
                "content": result.content,
                "scripts": result.scripts,
                "quiz_data": result.quiz_data,
                "metrics": result.metrics,
                "generation_time": result.generation_time
            }

        except Exception as e:
            logger.error(f"Content generation failed: {e}")

            # Send error event
            await pusher_service.trigger(
                channel="private-agent-orchestration",
                event="generation.error",
                data={
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }
            )

            raise

    async def get_health_status(self) -> Dict[str, Any]:
        """
        Get health status of all coordinators.

        Returns:
            Health status dictionary
        """
        if not self.is_initialized:
            return {
                "status": "not_initialized",
                "healthy": False,
                "timestamp": datetime.now().isoformat()
            }

        try:
            health = await self.main_coordinator.get_health_status()

            return {
                "status": health.status,
                "healthy": health.status == "healthy",
                "timestamp": health.timestamp.isoformat(),
                "components": health.component_health,
                "active_workflows": health.active_workflows,
                "resource_utilization": health.resource_utilization,
                "error_count": health.error_count,
                "last_error": health.last_error
            }

        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                "status": "error",
                "healthy": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    async def shutdown(self):
        """
        Gracefully shutdown the coordinator service.
        """
        logger.info("Shutting down Coordinator Service...")

        try:
            # Shutdown main coordinator
            if hasattr(self.main_coordinator, 'shutdown'):
                await self.main_coordinator.shutdown()

            # Unregister from Redis
            if self.redis_client:
                await self.redis_client.hdel("services:registry", "coordinator-service")
                await self.redis_client.close()

            # Send shutdown event
            await pusher_service.trigger(
                channel="private-system",
                event="coordinator.shutdown",
                data={
                    "service": "coordinator-service",
                    "timestamp": datetime.now().isoformat()
                }
            )

            self.is_initialized = False
            logger.info("Coordinator Service shutdown complete")

        except Exception as e:
            logger.error(f"Error during shutdown: {e}")


# Singleton instance
coordinator_service = None


async def get_coordinator() -> CoordinatorService:
    """
    Get the singleton coordinator service instance.

    Returns:
        CoordinatorService instance
    """
    global coordinator_service

    if coordinator_service is None:
        coordinator_service = CoordinatorService()
        await coordinator_service.initialize()

    return coordinator_service