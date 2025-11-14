"""
Supabase Service for ToolBoxAI Agent System

This service provides a centralized interface for interacting with Supabase
for agent-related data storage and retrieval.

Features:
- Agent execution tracking
- Performance metrics storage
- Task queue management
- Real-time subscriptions
- Authentication integration

Author: ToolboxAI Team
Created: 2025-09-21
Version: 1.0.0
"""

import logging
import os
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

try:
    from gotrue.errors import AuthApiError

    from supabase import Client, create_client

    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False
    Client = None

logger = logging.getLogger(__name__)


class SupabaseUnavailable(Exception):
    """Raised when Supabase is not available or configured"""

    pass


class SupabaseService:
    """
    Service for managing Supabase operations for the agent system.

    Provides methods for:
    - Agent instance management
    - Task execution tracking
    - Performance metrics storage
    - System health monitoring
    - Real-time subscriptions
    """

    def __init__(self):
        self.client: Client | None = None
        self.url = os.getenv("SUPABASE_URL")
        self.anon_key = os.getenv("SUPABASE_ANON_KEY")
        self.service_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        self._initialize_client()

    def _initialize_client(self):
        """Initialize Supabase client"""
        if not SUPABASE_AVAILABLE:
            logger.warning("Supabase client library not available")
            return

        if not self.url or not self.anon_key:
            logger.warning("Supabase configuration missing (URL or ANON_KEY)")
            return

        try:
            # Use service key if available for backend operations
            key = self.service_key if self.service_key else self.anon_key
            self.client = create_client(self.url, key)
            logger.info("Supabase client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Supabase client: {e}")

    def is_available(self) -> bool:
        """Check if Supabase is available and configured"""
        return self.client is not None

    def _ensure_available(self):
        """Ensure Supabase is available, raise exception if not"""
        if not self.is_available():
            raise SupabaseUnavailable("Supabase is not available or configured")

    # Agent Instance Management

    async def create_agent_instance(self, agent_data: dict[str, Any]) -> dict[str, Any]:
        """
        Create a new agent instance record in Supabase.

        Args:
            agent_data: Agent instance data

        Returns:
            Created agent instance data
        """
        self._ensure_available()

        try:
            # Prepare data for Supabase
            supabase_data = {
                "id": str(uuid4()),
                "agent_id": agent_data.get("agent_id"),
                "agent_type": agent_data.get("agent_type"),
                "status": agent_data.get("status", "initializing"),
                "configuration": agent_data.get("configuration", {}),
                "resource_limits": agent_data.get("resource_limits", {}),
                "performance_thresholds": agent_data.get("performance_thresholds", {}),
                "total_tasks_completed": 0,
                "total_tasks_failed": 0,
                "total_execution_time": 0.0,
                "average_execution_time": 0.0,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }

            result = self.client.table("agent_instances").insert(supabase_data).execute()

            if result.data:
                logger.info(f"Created agent instance: {agent_data.get('agent_id')}")
                return result.data[0]
            else:
                raise Exception("No data returned from insert")

        except Exception as e:
            logger.error(f"Error creating agent instance: {e}")
            raise

    async def update_agent_instance(self, agent_id: str, updates: dict[str, Any]) -> dict[str, Any]:
        """
        Update an agent instance record.

        Args:
            agent_id: Agent ID to update
            updates: Fields to update

        Returns:
            Updated agent instance data
        """
        self._ensure_available()

        try:
            # Add updated timestamp
            updates["updated_at"] = datetime.now(timezone.utc).isoformat()

            result = (
                self.client.table("agent_instances")
                .update(updates)
                .eq("agent_id", agent_id)
                .execute()
            )

            if result.data:
                logger.debug(f"Updated agent instance: {agent_id}")
                return result.data[0]
            else:
                logger.warning(f"No agent instance found to update: {agent_id}")
                return {}

        except Exception as e:
            logger.error(f"Error updating agent instance {agent_id}: {e}")
            raise

    async def get_agent_instance(self, agent_id: str) -> dict[str, Any] | None:
        """
        Get agent instance by ID.

        Args:
            agent_id: Agent ID to retrieve

        Returns:
            Agent instance data or None if not found
        """
        self._ensure_available()

        try:
            result = (
                self.client.table("agent_instances").select("*").eq("agent_id", agent_id).execute()
            )

            if result.data:
                return result.data[0]
            return None

        except Exception as e:
            logger.error(f"Error getting agent instance {agent_id}: {e}")
            raise

    async def get_all_agent_instances(self) -> list[dict[str, Any]]:
        """
        Get all agent instances.

        Returns:
            List of agent instance data
        """
        self._ensure_available()

        try:
            result = (
                self.client.table("agent_instances")
                .select("*")
                .order("created_at", desc=True)
                .execute()
            )
            return result.data or []

        except Exception as e:
            logger.error(f"Error getting all agent instances: {e}")
            raise

    # Task Execution Tracking

    async def create_task_execution(self, task_data: dict[str, Any]) -> dict[str, Any]:
        """
        Create a task execution record.

        Args:
            task_data: Task execution data

        Returns:
            Created task execution data
        """
        self._ensure_available()

        try:
            # Prepare data for Supabase
            supabase_data = {
                "id": str(uuid4()),
                "task_id": task_data.get("task_id"),
                "agent_instance_id": task_data.get("agent_instance_id"),
                "agent_type": task_data.get("agent_type"),
                "task_type": task_data.get("task_type"),
                "priority": task_data.get("priority", "normal"),
                "input_data": task_data.get("input_data", {}),
                "context_data": task_data.get("context_data", {}),
                "status": task_data.get("status", "pending"),
                "user_id": task_data.get("user_id"),
                "session_id": task_data.get("session_id"),
                "retry_count": task_data.get("retry_count", 0),
                "max_retries": task_data.get("max_retries", 3),
                "created_at": datetime.now(timezone.utc).isoformat(),
            }

            result = self.client.table("agent_executions").insert(supabase_data).execute()

            if result.data:
                logger.info(f"Created task execution: {task_data.get('task_id')}")
                return result.data[0]
            else:
                raise Exception("No data returned from insert")

        except Exception as e:
            logger.error(f"Error creating task execution: {e}")
            raise

    async def update_task_execution(self, task_id: str, updates: dict[str, Any]) -> dict[str, Any]:
        """
        Update a task execution record.

        Args:
            task_id: Task ID to update
            updates: Fields to update

        Returns:
            Updated task execution data
        """
        self._ensure_available()

        try:
            result = (
                self.client.table("agent_executions")
                .update(updates)
                .eq("task_id", task_id)
                .execute()
            )

            if result.data:
                logger.debug(f"Updated task execution: {task_id}")
                return result.data[0]
            else:
                logger.warning(f"No task execution found to update: {task_id}")
                return {}

        except Exception as e:
            logger.error(f"Error updating task execution {task_id}: {e}")
            raise

    async def get_task_execution(self, task_id: str) -> dict[str, Any] | None:
        """
        Get task execution by ID.

        Args:
            task_id: Task ID to retrieve

        Returns:
            Task execution data or None if not found
        """
        self._ensure_available()

        try:
            result = (
                self.client.table("agent_executions").select("*").eq("task_id", task_id).execute()
            )

            if result.data:
                return result.data[0]
            return None

        except Exception as e:
            logger.error(f"Error getting task execution {task_id}: {e}")
            raise

    async def get_agent_task_history(self, agent_id: str, limit: int = 100) -> list[dict[str, Any]]:
        """
        Get task execution history for an agent.

        Args:
            agent_id: Agent ID
            limit: Maximum number of records to return

        Returns:
            List of task execution data
        """
        self._ensure_available()

        try:
            # First get the agent instance ID
            agent_instance = await self.get_agent_instance(agent_id)
            if not agent_instance:
                return []

            result = (
                self.client.table("agent_executions")
                .select("*")
                .eq("agent_instance_id", agent_instance["id"])
                .order("created_at", desc=True)
                .limit(limit)
                .execute()
            )

            return result.data or []

        except Exception as e:
            logger.error(f"Error getting agent task history {agent_id}: {e}")
            raise

    # Performance Metrics

    async def store_agent_metrics(self, metrics_data: dict[str, Any]) -> dict[str, Any]:
        """
        Store agent performance metrics.

        Args:
            metrics_data: Metrics data

        Returns:
            Stored metrics data
        """
        self._ensure_available()

        try:
            # Prepare data for Supabase
            supabase_data = {
                "id": str(uuid4()),
                "agent_instance_id": metrics_data.get("agent_instance_id"),
                "agent_type": metrics_data.get("agent_type"),
                "period_start": metrics_data.get("period_start"),
                "period_end": metrics_data.get("period_end"),
                "period_duration_minutes": metrics_data.get("period_duration_minutes"),
                "tasks_completed": metrics_data.get("tasks_completed", 0),
                "tasks_failed": metrics_data.get("tasks_failed", 0),
                "tasks_cancelled": metrics_data.get("tasks_cancelled", 0),
                "total_tasks": metrics_data.get("total_tasks", 0),
                "success_rate": metrics_data.get("success_rate", 0.0),
                "error_rate": metrics_data.get("error_rate", 0.0),
                "average_execution_time": metrics_data.get("average_execution_time", 0.0),
                "tasks_per_minute": metrics_data.get("tasks_per_minute", 0.0),
                "tasks_per_hour": metrics_data.get("tasks_per_hour", 0.0),
                "average_quality_score": metrics_data.get("average_quality_score", 0.0),
                "uptime_percentage": metrics_data.get("uptime_percentage", 100.0),
                "custom_metrics": metrics_data.get("custom_metrics", {}),
                "created_at": datetime.now(timezone.utc).isoformat(),
            }

            result = self.client.table("agent_metrics").insert(supabase_data).execute()

            if result.data:
                logger.debug(f"Stored agent metrics for: {metrics_data.get('agent_type')}")
                return result.data[0]
            else:
                raise Exception("No data returned from insert")

        except Exception as e:
            logger.error(f"Error storing agent metrics: {e}")
            raise

    async def get_agent_metrics(self, agent_id: str, hours: int = 24) -> list[dict[str, Any]]:
        """
        Get agent performance metrics for a time period.

        Args:
            agent_id: Agent ID
            hours: Number of hours to look back

        Returns:
            List of metrics data
        """
        self._ensure_available()

        try:
            # First get the agent instance ID
            agent_instance = await self.get_agent_instance(agent_id)
            if not agent_instance:
                return []

            # Calculate time range
            end_time = datetime.now(timezone.utc)
            start_time = end_time.replace(hour=end_time.hour - hours)

            result = (
                self.client.table("agent_metrics")
                .select("*")
                .eq("agent_instance_id", agent_instance["id"])
                .gte("period_start", start_time.isoformat())
                .lte("period_end", end_time.isoformat())
                .order("period_start", desc=True)
                .execute()
            )

            return result.data or []

        except Exception as e:
            logger.error(f"Error getting agent metrics {agent_id}: {e}")
            raise

    # System Health

    async def store_system_health(self, health_data: dict[str, Any]) -> dict[str, Any]:
        """
        Store system health snapshot.

        Args:
            health_data: System health data

        Returns:
            Stored health data
        """
        self._ensure_available()

        try:
            # Prepare data for Supabase
            supabase_data = {
                "id": str(uuid4()),
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "period_minutes": health_data.get("period_minutes", 5),
                "total_agents": health_data.get("total_agents", 0),
                "active_agents": health_data.get("active_agents", 0),
                "idle_agents": health_data.get("idle_agents", 0),
                "busy_agents": health_data.get("busy_agents", 0),
                "error_agents": health_data.get("error_agents", 0),
                "total_tasks": health_data.get("total_tasks", 0),
                "completed_tasks": health_data.get("completed_tasks", 0),
                "failed_tasks": health_data.get("failed_tasks", 0),
                "queued_tasks": health_data.get("queued_tasks", 0),
                "running_tasks": health_data.get("running_tasks", 0),
                "system_success_rate": health_data.get("system_success_rate", 0.0),
                "system_error_rate": health_data.get("system_error_rate", 0.0),
                "overall_health_score": health_data.get("overall_health_score", 100.0),
                "availability_percentage": health_data.get("availability_percentage", 100.0),
                "custom_metrics": health_data.get("custom_metrics", {}),
            }

            result = self.client.table("system_health").insert(supabase_data).execute()

            if result.data:
                logger.debug("Stored system health snapshot")
                return result.data[0]
            else:
                raise Exception("No data returned from insert")

        except Exception as e:
            logger.error(f"Error storing system health: {e}")
            raise

    async def get_recent_system_health(self, hours: int = 24) -> list[dict[str, Any]]:
        """
        Get recent system health snapshots.

        Args:
            hours: Number of hours to look back

        Returns:
            List of system health data
        """
        self._ensure_available()

        try:
            # Calculate time range
            end_time = datetime.now(timezone.utc)
            start_time = end_time.replace(hour=end_time.hour - hours)

            result = (
                self.client.table("system_health")
                .select("*")
                .gte("timestamp", start_time.isoformat())
                .lte("timestamp", end_time.isoformat())
                .order("timestamp", desc=True)
                .execute()
            )

            return result.data or []

        except Exception as e:
            logger.error(f"Error getting system health: {e}")
            raise

    # Real-time Subscriptions

    def subscribe_to_agent_updates(self, callback):
        """
        Subscribe to real-time agent updates.

        Args:
            callback: Function to call when updates are received
        """
        self._ensure_available()

        try:
            # Subscribe to agent_instances table changes
            self.client.table("agent_instances").on("*", callback).subscribe()
            logger.info("Subscribed to agent instance updates")
        except Exception as e:
            logger.error(f"Error subscribing to agent updates: {e}")

    def subscribe_to_task_updates(self, callback):
        """
        Subscribe to real-time task execution updates.

        Args:
            callback: Function to call when updates are received
        """
        self._ensure_available()

        try:
            # Subscribe to agent_executions table changes
            self.client.table("agent_executions").on("*", callback).subscribe()
            logger.info("Subscribed to task execution updates")
        except Exception as e:
            logger.error(f"Error subscribing to task updates: {e}")

    # Utility Methods

    async def health_check(self) -> dict[str, Any]:
        """
        Perform a health check on the Supabase connection.

        Returns:
            Health check results
        """
        if not self.is_available():
            return {"healthy": False, "error": "Supabase not configured or available"}

        try:
            # Simple query to test connection
            self.client.table("agent_instances").select("count").execute()

            return {
                "healthy": True,
                "url": self.url,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "response_time_ms": 0,  # Would need to measure actual response time
            }
        except Exception as e:
            return {
                "healthy": False,
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

    async def cleanup_old_data(self, days: int = 30):
        """
        Clean up old data from Supabase tables.

        Args:
            days: Number of days to keep data
        """
        self._ensure_available()

        try:
            cutoff_date = datetime.now(timezone.utc).replace(day=datetime.now().day - days)
            cutoff_iso = cutoff_date.isoformat()

            # Clean up old executions
            result = (
                self.client.table("agent_executions")
                .delete()
                .lt("created_at", cutoff_iso)
                .execute()
            )

            logger.info(f"Cleaned up old agent executions: {len(result.data or [])} records")

            # Clean up old metrics
            result = (
                self.client.table("agent_metrics").delete().lt("created_at", cutoff_iso).execute()
            )

            logger.info(f"Cleaned up old agent metrics: {len(result.data or [])} records")

            # Clean up old health data
            result = (
                self.client.table("system_health").delete().lt("timestamp", cutoff_iso).execute()
            )

            logger.info(f"Cleaned up old system health data: {len(result.data or [])} records")

        except Exception as e:
            logger.error(f"Error cleaning up old data: {e}")
            raise


# Global Supabase service instance
_supabase_service: SupabaseService | None = None


def get_supabase_service() -> SupabaseService:
    """Get or create global Supabase service instance"""
    global _supabase_service
    if _supabase_service is None:
        _supabase_service = SupabaseService()
        logger.info("Global Supabase service initialized")
    return _supabase_service


async def initialize_supabase_tables():
    """
    Initialize Supabase tables if they don't exist.
    This would typically be done via Supabase migrations,
    but included here for completeness.
    """
    service = get_supabase_service()
    if not service.is_available():
        logger.warning("Supabase not available for table initialization")
        return

    # Note: In a real implementation, you would use Supabase migrations
    # This is just for reference of the expected table structure
    logger.info("Supabase tables should be created via migrations")


# Export commonly used functions
__all__ = [
    "SupabaseService",
    "SupabaseUnavailable",
    "get_supabase_service",
    "initialize_supabase_tables",
]
