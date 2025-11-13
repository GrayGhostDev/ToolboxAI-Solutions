"""
Real-time Integration Service - Supabase + Pusher Integration

This service integrates Supabase real-time subscriptions with the existing
Pusher Channels system to provide comprehensive real-time updates.

Features:
- Supabase real-time event forwarding to Pusher
- Event transformation and filtering
- Dual real-time system support
- Error handling and reconnection
- Performance monitoring

Author: ToolboxAI Team
Created: 2025-09-21
Version: 1.0.0
"""

import asyncio
import logging
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

# Pusher integration
from apps.backend.services.pusher import AGENT_CHANNELS, AGENT_EVENTS, trigger_event

# Supabase integration
from apps.backend.services.supabase_service import get_supabase_service

logger = logging.getLogger(__name__)


@dataclass
class RealtimeEvent:
    """Real-time event data structure"""

    table: str
    event_type: str  # INSERT, UPDATE, DELETE
    old_record: dict[str, Any] | None
    new_record: dict[str, Any] | None
    timestamp: datetime
    schema: str = "public"


class RealtimeIntegrationService:
    """
    Service for integrating Supabase real-time with Pusher Channels.

    Listens to Supabase real-time events and forwards them to appropriate
    Pusher channels for frontend consumption.
    """

    def __init__(self):
        self.supabase_service = get_supabase_service()
        self.active_subscriptions: dict[str, Any] = {}
        self.event_handlers: dict[str, list[Callable]] = {}
        self.is_running = False
        self._setup_event_handlers()

    def _setup_event_handlers(self):
        """Setup event handlers for different table types"""
        self.event_handlers = {
            "agent_instances": [self._handle_agent_instance_event],
            "agent_executions": [self._handle_agent_execution_event],
            "agent_metrics": [self._handle_agent_metrics_event],
            "system_health": [self._handle_system_health_event],
            "agent_task_queue": [self._handle_task_queue_event],
        }

    async def start(self):
        """Start real-time integration service"""
        if not self.supabase_service or not self.supabase_service.is_available():
            logger.warning("Supabase not available, real-time integration disabled")
            return

        try:
            self.is_running = True

            # Setup subscriptions for each table
            for table_name in self.event_handlers.keys():
                await self._subscribe_to_table(table_name)

            logger.info("Real-time integration service started")

        except Exception as e:
            logger.error(f"Failed to start real-time integration: {e}")
            self.is_running = False

    async def stop(self):
        """Stop real-time integration service"""
        self.is_running = False

        # Unsubscribe from all tables
        for subscription in self.active_subscriptions.values():
            try:
                if hasattr(subscription, "unsubscribe"):
                    subscription.unsubscribe()
            except Exception as e:
                logger.warning(f"Error unsubscribing: {e}")

        self.active_subscriptions.clear()
        logger.info("Real-time integration service stopped")

    async def _subscribe_to_table(self, table_name: str):
        """Subscribe to real-time updates for a specific table"""
        if not self.supabase_service or not self.supabase_service.client:
            return

        try:
            # Create subscription callback
            def handle_event(payload):
                asyncio.create_task(self._process_realtime_event(table_name, payload))

            # Subscribe to table changes
            if table_name == "agent_instances":
                subscription = self.supabase_service.subscribe_to_agent_updates(handle_event)
            elif table_name == "agent_executions":
                subscription = self.supabase_service.subscribe_to_task_updates(handle_event)
            else:
                # Generic table subscription
                subscription = (
                    self.supabase_service.client.table(table_name).on("*", handle_event).subscribe()
                )

            self.active_subscriptions[table_name] = subscription
            logger.debug(f"Subscribed to {table_name} real-time updates")

        except Exception as e:
            logger.error(f"Failed to subscribe to {table_name}: {e}")

    async def _process_realtime_event(self, table_name: str, payload: dict[str, Any]):
        """Process a real-time event from Supabase"""
        try:
            # Extract event data
            event_type = payload.get("eventType", "UNKNOWN")
            old_record = payload.get("old")
            new_record = payload.get("new")

            # Create event object
            event = RealtimeEvent(
                table=table_name,
                event_type=event_type,
                old_record=old_record,
                new_record=new_record,
                timestamp=datetime.now(timezone.utc),
            )

            # Process event with registered handlers
            handlers = self.event_handlers.get(table_name, [])
            for handler in handlers:
                try:
                    await handler(event)
                except Exception as e:
                    logger.error(f"Error in event handler for {table_name}: {e}")

        except Exception as e:
            logger.error(f"Error processing real-time event for {table_name}: {e}")

    async def _handle_agent_instance_event(self, event: RealtimeEvent):
        """Handle agent instance table events"""
        try:
            if event.event_type == "INSERT" and event.new_record:
                # New agent registered
                await trigger_event(
                    channel=AGENT_CHANNELS["status"],
                    event=AGENT_EVENTS["agent_registered"],
                    data={
                        "agent_id": event.new_record.get("agent_id"),
                        "agent_type": event.new_record.get("agent_type"),
                        "status": event.new_record.get("status"),
                        "timestamp": event.timestamp.isoformat(),
                    },
                )

            elif event.event_type == "UPDATE" and event.new_record and event.old_record:
                # Agent status changed
                old_status = event.old_record.get("status")
                new_status = event.new_record.get("status")

                if old_status != new_status:
                    await trigger_event(
                        channel=AGENT_CHANNELS["status"],
                        event=AGENT_EVENTS["status_changed"],
                        data={
                            "agent_id": event.new_record.get("agent_id"),
                            "agent_type": event.new_record.get("agent_type"),
                            "old_status": old_status,
                            "new_status": new_status,
                            "timestamp": event.timestamp.isoformat(),
                        },
                    )

                # Task assignment changed
                old_task = event.old_record.get("current_task_id")
                new_task = event.new_record.get("current_task_id")

                if old_task != new_task:
                    if new_task:
                        await trigger_event(
                            channel=AGENT_CHANNELS["tasks"],
                            event=AGENT_EVENTS["task_assigned"],
                            data={
                                "agent_id": event.new_record.get("agent_id"),
                                "task_id": new_task,
                                "timestamp": event.timestamp.isoformat(),
                            },
                        )
                    elif old_task:
                        await trigger_event(
                            channel=AGENT_CHANNELS["tasks"],
                            event=AGENT_EVENTS["task_completed"],
                            data={
                                "agent_id": event.new_record.get("agent_id"),
                                "task_id": old_task,
                                "timestamp": event.timestamp.isoformat(),
                            },
                        )

        except Exception as e:
            logger.error(f"Error handling agent instance event: {e}")

    async def _handle_agent_execution_event(self, event: RealtimeEvent):
        """Handle agent execution table events"""
        try:
            if event.event_type == "INSERT" and event.new_record:
                # New task created
                await trigger_event(
                    channel=AGENT_CHANNELS["tasks"],
                    event=AGENT_EVENTS["task_created"],
                    data={
                        "task_id": event.new_record.get("task_id"),
                        "agent_type": event.new_record.get("agent_type"),
                        "task_type": event.new_record.get("task_type"),
                        "priority": event.new_record.get("priority"),
                        "status": event.new_record.get("status"),
                        "timestamp": event.timestamp.isoformat(),
                    },
                )

            elif event.event_type == "UPDATE" and event.new_record and event.old_record:
                # Task status changed
                old_status = event.old_record.get("status")
                new_status = event.new_record.get("status")

                if old_status != new_status:
                    # Determine event type based on status change
                    if new_status == "running":
                        pusher_event = AGENT_EVENTS["task_started"]
                    elif new_status == "completed":
                        pusher_event = AGENT_EVENTS["task_completed"]
                    elif new_status == "failed":
                        pusher_event = AGENT_EVENTS["task_failed"]
                    else:
                        pusher_event = AGENT_EVENTS["task_updated"]

                    await trigger_event(
                        channel=AGENT_CHANNELS["tasks"],
                        event=pusher_event,
                        data={
                            "task_id": event.new_record.get("task_id"),
                            "agent_type": event.new_record.get("agent_type"),
                            "old_status": old_status,
                            "new_status": new_status,
                            "execution_time": event.new_record.get("execution_time_seconds"),
                            "quality_score": event.new_record.get("quality_score"),
                            "error_message": event.new_record.get("error_message"),
                            "timestamp": event.timestamp.isoformat(),
                        },
                    )

        except Exception as e:
            logger.error(f"Error handling agent execution event: {e}")

    async def _handle_agent_metrics_event(self, event: RealtimeEvent):
        """Handle agent metrics table events"""
        try:
            if event.event_type == "INSERT" and event.new_record:
                # New metrics recorded
                await trigger_event(
                    channel=AGENT_CHANNELS["metrics"],
                    event=AGENT_EVENTS["metrics_updated"],
                    data={
                        "agent_type": event.new_record.get("agent_type"),
                        "period_start": event.new_record.get("period_start"),
                        "period_end": event.new_record.get("period_end"),
                        "success_rate": event.new_record.get("success_rate"),
                        "average_execution_time": event.new_record.get("average_execution_time"),
                        "tasks_completed": event.new_record.get("tasks_completed"),
                        "tasks_failed": event.new_record.get("tasks_failed"),
                        "average_quality_score": event.new_record.get("average_quality_score"),
                        "timestamp": event.timestamp.isoformat(),
                    },
                )

        except Exception as e:
            logger.error(f"Error handling agent metrics event: {e}")

    async def _handle_system_health_event(self, event: RealtimeEvent):
        """Handle system health table events"""
        try:
            if event.event_type == "INSERT" and event.new_record:
                # New health snapshot
                await trigger_event(
                    channel=AGENT_CHANNELS["health"],
                    event=AGENT_EVENTS["health_updated"],
                    data={
                        "total_agents": event.new_record.get("total_agents"),
                        "active_agents": event.new_record.get("active_agents"),
                        "busy_agents": event.new_record.get("busy_agents"),
                        "error_agents": event.new_record.get("error_agents"),
                        "system_success_rate": event.new_record.get("system_success_rate"),
                        "overall_health_score": event.new_record.get("overall_health_score"),
                        "availability_percentage": event.new_record.get("availability_percentage"),
                        "queued_tasks": event.new_record.get("queued_tasks"),
                        "running_tasks": event.new_record.get("running_tasks"),
                        "timestamp": event.timestamp.isoformat(),
                    },
                )

        except Exception as e:
            logger.error(f"Error handling system health event: {e}")

    async def _handle_task_queue_event(self, event: RealtimeEvent):
        """Handle task queue table events"""
        try:
            if event.event_type == "INSERT" and event.new_record:
                # New task queued
                await trigger_event(
                    channel=AGENT_CHANNELS["queue"],
                    event=AGENT_EVENTS["task_queued"],
                    data={
                        "task_id": event.new_record.get("task_id"),
                        "agent_type": event.new_record.get("agent_type"),
                        "task_type": event.new_record.get("task_type"),
                        "priority": event.new_record.get("priority"),
                        "scheduled_at": event.new_record.get("scheduled_at"),
                        "timestamp": event.timestamp.isoformat(),
                    },
                )

            elif event.event_type == "UPDATE" and event.new_record and event.old_record:
                # Task queue status changed
                old_status = event.old_record.get("status")
                new_status = event.new_record.get("status")

                if old_status != new_status:
                    await trigger_event(
                        channel=AGENT_CHANNELS["queue"],
                        event=AGENT_EVENTS["queue_updated"],
                        data={
                            "task_id": event.new_record.get("task_id"),
                            "agent_type": event.new_record.get("agent_type"),
                            "old_status": old_status,
                            "new_status": new_status,
                            "assigned_agent_id": event.new_record.get("assigned_agent_id"),
                            "timestamp": event.timestamp.isoformat(),
                        },
                    )

        except Exception as e:
            logger.error(f"Error handling task queue event: {e}")

    def add_event_handler(self, table_name: str, handler: Callable):
        """Add custom event handler for a table"""
        if table_name not in self.event_handlers:
            self.event_handlers[table_name] = []
        self.event_handlers[table_name].append(handler)
        logger.debug(f"Added event handler for {table_name}")

    def remove_event_handler(self, table_name: str, handler: Callable):
        """Remove event handler for a table"""
        if table_name in self.event_handlers:
            try:
                self.event_handlers[table_name].remove(handler)
                logger.debug(f"Removed event handler for {table_name}")
            except ValueError:
                logger.warning(f"Handler not found for {table_name}")

    async def get_status(self) -> dict[str, Any]:
        """Get real-time integration service status"""
        return {
            "running": self.is_running,
            "supabase_available": self.supabase_service and self.supabase_service.is_available(),
            "active_subscriptions": list(self.active_subscriptions.keys()),
            "event_handlers": {
                table: len(handlers) for table, handlers in self.event_handlers.items()
            },
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }


# Global service instance
_realtime_integration_service: RealtimeIntegrationService | None = None


def get_realtime_integration_service() -> RealtimeIntegrationService:
    """Get or create global real-time integration service instance"""
    global _realtime_integration_service
    if _realtime_integration_service is None:
        _realtime_integration_service = RealtimeIntegrationService()
        logger.info("Real-time integration service initialized")
    return _realtime_integration_service


async def start_realtime_integration():
    """Start the real-time integration service"""
    service = get_realtime_integration_service()
    await service.start()


async def stop_realtime_integration():
    """Stop the real-time integration service"""
    service = get_realtime_integration_service()
    await service.stop()


class RealtimeHealthMonitor:
    """
    Monitor real-time system health and performance.

    Tracks real-time event processing, subscription health,
    and integration performance metrics.
    """

    def __init__(self):
        self.event_counts: dict[str, int] = {}
        self.error_counts: dict[str, int] = {}
        self.last_event_times: dict[str, datetime] = {}
        self.start_time = datetime.now(timezone.utc)

    def record_event(self, table_name: str, event_type: str):
        """Record a processed event"""
        key = f"{table_name}:{event_type}"
        self.event_counts[key] = self.event_counts.get(key, 0) + 1
        self.last_event_times[key] = datetime.now(timezone.utc)

    def record_error(self, table_name: str, error: str):
        """Record an error in event processing"""
        key = f"{table_name}:error"
        self.error_counts[key] = self.error_counts.get(key, 0) + 1
        logger.error(f"Real-time error for {table_name}: {error}")

    def get_health_report(self) -> dict[str, Any]:
        """Get health report for real-time integration"""
        now = datetime.now(timezone.utc)
        uptime = (now - self.start_time).total_seconds()

        total_events = sum(self.event_counts.values())
        total_errors = sum(self.error_counts.values())

        return {
            "uptime_seconds": uptime,
            "total_events_processed": total_events,
            "total_errors": total_errors,
            "error_rate": (total_errors / max(total_events, 1)) * 100,
            "events_per_minute": (total_events / max(uptime / 60, 1)),
            "event_counts": self.event_counts.copy(),
            "error_counts": self.error_counts.copy(),
            "last_event_times": {k: v.isoformat() for k, v in self.last_event_times.items()},
            "timestamp": now.isoformat(),
        }


# Global health monitor
_realtime_health_monitor: RealtimeHealthMonitor | None = None


def get_realtime_health_monitor() -> RealtimeHealthMonitor:
    """Get or create global real-time health monitor"""
    global _realtime_health_monitor
    if _realtime_health_monitor is None:
        _realtime_health_monitor = RealtimeHealthMonitor()
    return _realtime_health_monitor


# Export commonly used functions
__all__ = [
    "RealtimeIntegrationService",
    "RealtimeEvent",
    "RealtimeHealthMonitor",
    "get_realtime_integration_service",
    "start_realtime_integration",
    "stop_realtime_integration",
    "get_realtime_health_monitor",
]
