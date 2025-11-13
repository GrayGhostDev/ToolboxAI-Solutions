"""
Integration Package
==================
External system integration agents and coordination

Provides:
- IntegrationAgent: Base agent for external system integration
- IntegrationPlatform: Platform management and service orchestration
- IntegrationEvent: Event handling for integration workflows
"""

import logging
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class IntegrationStatus(Enum):
    """Status codes for integration operations"""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"


class IntegrationEvent:
    """
    Integration Event

    Represents an event in the integration workflow system.
    Used for tracking and coordinating asynchronous integration operations.
    """

    def __init__(
        self,
        event_type: str,
        platform: str,
        data: dict[str, Any],
        metadata: dict[str, Any] | None = None,
    ):
        """
        Initialize integration event

        Args:
            event_type: Type of integration event (e.g., 'webhook', 'sync', 'callback')
            platform: Source platform identifier
            data: Event payload data
            metadata: Optional event metadata
        """
        self.event_type = event_type
        self.platform = platform
        self.data = data
        self.metadata = metadata or {}
        self.timestamp = datetime.utcnow()
        self.status = IntegrationStatus.PENDING
        self.event_id = f"{platform}_{event_type}_{int(self.timestamp.timestamp())}"

        logger.info(f"Created integration event: {self.event_id}")

    def mark_completed(self):
        """Mark event as completed"""
        self.status = IntegrationStatus.COMPLETED
        logger.info(f"Event {self.event_id} completed")

    def mark_failed(self, error: str):
        """Mark event as failed"""
        self.status = IntegrationStatus.FAILED
        self.metadata["error"] = error
        logger.error(f"Event {self.event_id} failed: {error}")

    def to_dict(self) -> dict[str, Any]:
        """Convert event to dictionary"""
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "platform": self.platform,
            "data": self.data,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat(),
            "status": self.status.value,
        }


class IntegrationPlatform:
    """
    Integration Platform Manager

    Manages connections and operations for external platforms/services.
    Handles authentication, rate limiting, and service coordination.
    """

    def __init__(self, platform_name: str, config: dict[str, Any] | None = None):
        """
        Initialize integration platform

        Args:
            platform_name: Name of the external platform (e.g., 'roblox', 'stripe', 'sendgrid')
            config: Platform-specific configuration
        """
        self.platform_name = platform_name
        self.config = config or {}
        self.is_connected = False
        self.events: list[IntegrationEvent] = []

        logger.info(f"Initialized {platform_name} integration platform")

    async def connect(self) -> bool:
        """
        Establish connection to external platform

        Returns:
            Connection success status
        """
        try:
            logger.info(f"Connecting to {self.platform_name}...")

            # Platform-specific connection logic
            if self.platform_name.lower() == "roblox":
                from apps.backend.services.roblox_service import RobloxService

                api_key = self.config.get("api_key") or self.config.get("ROBLOX_API_KEY")
                self._service = RobloxService(api_key=api_key)
                logger.info("Roblox service initialized")

            elif self.platform_name.lower() == "stripe":
                from apps.backend.services.stripe_service import StripeService

                self._service = StripeService()
                logger.info("Stripe service initialized")

            elif self.platform_name.lower() in ["sendgrid", "email"]:
                from apps.backend.services.email import email_service

                self._service = email_service
                logger.info("SendGrid email service initialized")

            else:
                # Generic platform - no specific service
                logger.warning(f"No specific service for platform: {self.platform_name}")
                self._service = None

            self.is_connected = True
            logger.info(f"Successfully connected to {self.platform_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to connect to {self.platform_name}: {e}")
            self.is_connected = False
            self._service = None
            return False

    async def disconnect(self):
        """Disconnect from external platform"""
        logger.info(f"Disconnecting from {self.platform_name}")
        self.is_connected = False

    async def send_data(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        Send data to external platform

        Args:
            data: Data to send

        Returns:
            Response from platform
        """
        if not self.is_connected:
            raise ConnectionError(f"Not connected to {self.platform_name}")

        logger.info(f"Sending data to {self.platform_name}")

        try:
            # Route to platform-specific service
            if self.platform_name.lower() == "roblox":
                # Roblox operations: upload_script or upload_asset
                operation = data.get("operation", "upload_script")

                if operation == "upload_script":
                    result = self._service.upload_script(
                        universe_id=data.get("universe_id", ""),
                        script_name=data.get("script_name", ""),
                        script_content=data.get("script_content", ""),
                        script_type=data.get("script_type", "ModuleScript"),
                    )
                elif operation == "upload_asset":
                    result = self._service.upload_asset(
                        universe_id=data.get("universe_id", ""),
                        asset_name=data.get("asset_name", ""),
                        asset_data=data.get("asset_data", b""),
                        asset_type=data.get("asset_type", "Model"),
                    )
                else:
                    result = {"success": False, "error": f"Unknown Roblox operation: {operation}"}

            elif self.platform_name.lower() == "stripe":
                # Stripe operations - for now return success
                # In production, this would call specific Stripe methods
                logger.info(f"Stripe operation: {data.get('operation', 'payment')}")
                result = {
                    "success": True,
                    "message": "Stripe operation completed",
                    "operation": data.get("operation", "payment"),
                }

            elif self.platform_name.lower() in ["sendgrid", "email"]:
                # SendGrid email operations
                import asyncio

                email_result = await self._service.send_email(
                    to_emails=data.get("to_email", data.get("to_emails", "")),
                    subject=data.get("subject", ""),
                    text_content=data.get("body", data.get("text_content", "")),
                    html_content=data.get("html_body", data.get("html_content", None)),
                    attachments=data.get("attachments", None),
                )
                result = email_result

            else:
                # Generic platform - return mock success
                logger.warning(f"Generic send_data for platform: {self.platform_name}")
                result = {"success": True, "message": "Data sent to generic platform", "data": data}

            # Add platform metadata to result
            return {
                **result,
                "platform": self.platform_name,
                "timestamp": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"Failed to send data to {self.platform_name}: {e}")
            return {
                "status": "error",
                "platform": self.platform_name,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
            }

    async def receive_data(self) -> dict[str, Any] | None:
        """
        Receive data from external platform

        Returns:
            Received data or None
        """
        if not self.is_connected:
            raise ConnectionError(f"Not connected to {self.platform_name}")

        logger.info(f"Receiving data from {self.platform_name}")
        # Placeholder for actual API call
        return None

    def create_event(
        self, event_type: str, data: dict[str, Any], metadata: dict[str, Any] | None = None
    ) -> IntegrationEvent:
        """Create and track integration event"""
        event = IntegrationEvent(
            event_type=event_type, platform=self.platform_name, data=data, metadata=metadata
        )
        self.events.append(event)
        return event

    def get_events(self, status: IntegrationStatus | None = None) -> list[IntegrationEvent]:
        """
        Get integration events, optionally filtered by status

        Args:
            status: Filter by event status

        Returns:
            List of events
        """
        if status:
            return [e for e in self.events if e.status == status]
        return self.events


class IntegrationAgent:
    """
    Integration Agent

    Base agent for managing external system integrations.
    Coordinates with IntegrationPlatform for specific service connections.
    """

    def __init__(self, platforms: list[str] | None = None):
        """
        Initialize integration agent

        Args:
            platforms: List of platform names to manage
        """
        self.platforms: dict[str, IntegrationPlatform] = {}

        if platforms:
            for platform_name in platforms:
                self.register_platform(platform_name)

        logger.info(f"IntegrationAgent initialized with {len(self.platforms)} platforms")

    def register_platform(
        self, platform_name: str, config: dict[str, Any] | None = None
    ) -> IntegrationPlatform:
        """
        Register a new platform

        Args:
            platform_name: Name of the platform
            config: Platform configuration

        Returns:
            The registered platform instance
        """
        platform = IntegrationPlatform(platform_name, config)
        self.platforms[platform_name] = platform
        logger.info(f"Registered platform: {platform_name}")
        return platform

    def get_platform(self, platform_name: str) -> IntegrationPlatform | None:
        """Get platform by name"""
        return self.platforms.get(platform_name)

    async def integrate(self, system: str, data: dict[str, Any]) -> dict[str, Any]:
        """
        Integrate with external system

        Args:
            system: System/platform name
            data: Integration data

        Returns:
            Integration result
        """
        logger.info(f"Integrating with system: {system}")

        platform = self.get_platform(system)
        if not platform:
            platform = self.register_platform(system)

        # Connect if not already connected
        if not platform.is_connected:
            await platform.connect()

        # Send data
        result = await platform.send_data(data)

        return {
            "status": "integration_complete",
            "system": system,
            "result": result,
            "timestamp": datetime.utcnow().isoformat(),
        }

    async def sync_all(self) -> dict[str, Any]:
        """
        Sync data across all registered platforms

        Returns:
            Sync results for all platforms
        """
        results = {}

        for platform_name, platform in self.platforms.items():
            try:
                if not platform.is_connected:
                    await platform.connect()

                # Placeholder for sync logic
                results[platform_name] = {
                    "status": "synced",
                    "timestamp": datetime.utcnow().isoformat(),
                }
            except Exception as e:
                results[platform_name] = {"status": "error", "error": str(e)}
                logger.error(f"Sync failed for {platform_name}: {e}")

        return results


__all__ = [
    "IntegrationAgent",
    "IntegrationPlatform",
    "IntegrationEvent",
    "IntegrationStatus",
]
