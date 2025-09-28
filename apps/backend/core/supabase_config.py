"""
Supabase Configuration and Initialization

This module provides configuration and initialization for Supabase integration
with the ToolBoxAI agent system.

Features:
- Supabase client configuration
- Environment-based settings
- Connection health monitoring
- Table initialization
- Real-time subscription setup

Author: ToolboxAI Team
Created: 2025-09-21
Version: 1.0.0
"""

import os
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timezone

try:
    from supabase import create_client, Client
    from gotrue.errors import AuthApiError

    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False
    Client = None

logger = logging.getLogger(__name__)


class SupabaseConfig:
    """Supabase configuration management"""

    def __init__(self):
        # Environment variables
        self.url = os.getenv("SUPABASE_URL")
        self.anon_key = os.getenv("SUPABASE_ANON_KEY")
        self.service_role_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        self.jwt_secret = os.getenv("SUPABASE_JWT_SECRET")

        # Database configuration
        self.db_host = os.getenv("SUPABASE_DB_HOST", "localhost")
        self.db_port = int(os.getenv("SUPABASE_DB_PORT", "54322"))
        self.db_name = os.getenv("SUPABASE_DB_NAME", "postgres")
        self.db_user = os.getenv("SUPABASE_DB_USER", "postgres")
        self.db_password = os.getenv("SUPABASE_DB_PASS", "postgres")

        # Agent system specific settings
        self.agent_schema = os.getenv("SUPABASE_AGENT_SCHEMA", "public")
        self.enable_realtime = os.getenv("SUPABASE_ENABLE_REALTIME", "true").lower() == "true"
        self.enable_rls = os.getenv("SUPABASE_ENABLE_RLS", "true").lower() == "true"

        # Performance settings
        self.connection_timeout = int(os.getenv("SUPABASE_CONNECTION_TIMEOUT", "30"))
        self.max_retries = int(os.getenv("SUPABASE_MAX_RETRIES", "3"))
        self.retry_delay = int(os.getenv("SUPABASE_RETRY_DELAY", "5"))

    def is_configured(self) -> bool:
        """Check if Supabase is properly configured"""
        return bool(self.url and self.anon_key and SUPABASE_AVAILABLE)

    def get_database_url(self) -> str:
        """Get PostgreSQL connection URL for direct database access"""
        return f"postgresql://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"

    def get_client_config(self) -> Dict[str, Any]:
        """Get Supabase client configuration"""
        return {
            "url": self.url,
            "key": self.service_role_key or self.anon_key,
            "options": {
                "schema": self.agent_schema,
                "auto_refresh_token": True,
                "persist_session": False,  # Backend doesn't need session persistence
                "detect_session_in_url": False,
                "headers": {
                    "x-application-name": "toolboxai-agent-system",
                    "x-client-info": "toolboxai-backend/1.0.0",
                },
            },
        }


class SupabaseInitializer:
    """Handles Supabase initialization for the agent system"""

    def __init__(self, config: SupabaseConfig):
        self.config = config
        self.client: Optional[Client] = None

    async def initialize(self) -> bool:
        """Initialize Supabase client and verify connection"""
        if not self.config.is_configured():
            logger.warning("Supabase not configured - skipping initialization")
            return False

        try:
            # Create client
            client_config = self.config.get_client_config()
            self.client = create_client(
                client_config["url"], client_config["key"], **client_config["options"]
            )

            # Verify connection with a simple query
            result = self.client.table("agent_instances").select("count").execute()

            logger.info("Supabase client initialized successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize Supabase client: {e}")
            return False

    async def verify_tables(self) -> Dict[str, bool]:
        """Verify that required tables exist"""
        if not self.client:
            return {}

        required_tables = [
            "agent_instances",
            "agent_executions",
            "agent_metrics",
            "agent_task_queue",
            "system_health",
            "agent_configurations",
        ]

        table_status = {}

        for table in required_tables:
            try:
                # Try to query the table
                result = self.client.table(table).select("count").execute()
                table_status[table] = True
                logger.debug(f"Table {table} exists and is accessible")
            except Exception as e:
                table_status[table] = False
                logger.warning(f"Table {table} not accessible: {e}")

        return table_status

    async def setup_realtime_subscriptions(self, callback_handlers: Dict[str, callable]):
        """Setup real-time subscriptions for agent system tables"""
        if not self.client or not self.config.enable_realtime:
            logger.info("Real-time subscriptions not enabled")
            return

        try:
            # Subscribe to agent instances changes
            if "agent_instances" in callback_handlers:
                self.client.table("agent_instances").on(
                    "*", callback_handlers["agent_instances"]
                ).subscribe()
                logger.info("Subscribed to agent_instances real-time updates")

            # Subscribe to agent executions changes
            if "agent_executions" in callback_handlers:
                self.client.table("agent_executions").on(
                    "*", callback_handlers["agent_executions"]
                ).subscribe()
                logger.info("Subscribed to agent_executions real-time updates")

            # Subscribe to system health changes
            if "system_health" in callback_handlers:
                self.client.table("system_health").on(
                    "*", callback_handlers["system_health"]
                ).subscribe()
                logger.info("Subscribed to system_health real-time updates")

        except Exception as e:
            logger.error(f"Failed to setup real-time subscriptions: {e}")

    async def initialize_default_data(self):
        """Initialize default data for the agent system"""
        if not self.client:
            return

        try:
            # Check if we need to insert default configurations
            result = self.client.table("agent_configurations").select("count").execute()

            if not result.data or len(result.data) == 0:
                # Insert default agent configurations
                default_configs = [
                    {
                        "name": "default_content_generator",
                        "version": "1.0.0",
                        "agent_type": "content_generator",
                        "configuration": {
                            "model": "gpt-4",
                            "temperature": 0.7,
                            "max_tokens": 2000,
                            "timeout_seconds": 30,
                        },
                        "resource_limits": {"max_memory_mb": 1024, "max_cpu_percent": 80},
                        "performance_thresholds": {
                            "min_quality_score": 0.85,
                            "max_execution_time": 30,
                        },
                        "environment": "production",
                        "is_active": True,
                        "is_default": True,
                        "created_at": datetime.now(timezone.utc).isoformat(),
                    }
                    # Add more default configurations as needed
                ]

                for config in default_configs:
                    self.client.table("agent_configurations").insert(config).execute()

                logger.info("Initialized default agent configurations")

        except Exception as e:
            logger.error(f"Failed to initialize default data: {e}")

    def get_client(self) -> Optional[Client]:
        """Get the initialized Supabase client"""
        return self.client


# Global instances
_supabase_config: Optional[SupabaseConfig] = None
_supabase_initializer: Optional[SupabaseInitializer] = None


def get_supabase_config() -> SupabaseConfig:
    """Get or create global Supabase configuration"""
    global _supabase_config
    if _supabase_config is None:
        _supabase_config = SupabaseConfig()
    return _supabase_config


async def get_supabase_initializer() -> SupabaseInitializer:
    """Get or create global Supabase initializer"""
    global _supabase_initializer
    if _supabase_initializer is None:
        config = get_supabase_config()
        _supabase_initializer = SupabaseInitializer(config)
        await _supabase_initializer.initialize()
    return _supabase_initializer


async def initialize_supabase_for_agents() -> Dict[str, Any]:
    """
    Initialize Supabase for the agent system.

    Returns:
        Initialization status and results
    """
    try:
        config = get_supabase_config()

        if not config.is_configured():
            return {"success": False, "error": "Supabase not configured", "configured": False}

        initializer = await get_supabase_initializer()

        # Verify tables
        table_status = await initializer.verify_tables()
        missing_tables = [table for table, exists in table_status.items() if not exists]

        if missing_tables:
            logger.warning(f"Missing Supabase tables: {missing_tables}")

        # Initialize default data
        await initializer.initialize_default_data()

        return {
            "success": True,
            "configured": True,
            "client_initialized": initializer.client is not None,
            "tables_verified": table_status,
            "missing_tables": missing_tables,
            "realtime_enabled": config.enable_realtime,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    except Exception as e:
        logger.error(f"Supabase initialization failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }


async def health_check_supabase() -> Dict[str, Any]:
    """Perform health check on Supabase connection"""
    try:
        config = get_supabase_config()

        if not config.is_configured():
            return {"healthy": False, "error": "Not configured"}

        initializer = await get_supabase_initializer()
        client = initializer.get_client()

        if not client:
            return {"healthy": False, "error": "Client not initialized"}

        # Test connection with simple query
        start_time = datetime.now()
        result = client.table("agent_instances").select("count").execute()
        end_time = datetime.now()

        response_time = (end_time - start_time).total_seconds() * 1000  # ms

        return {
            "healthy": True,
            "url": config.url,
            "response_time_ms": response_time,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    except Exception as e:
        return {
            "healthy": False,
            "error": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
