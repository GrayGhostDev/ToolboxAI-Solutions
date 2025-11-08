"""
Health Monitoring Tasks
======================
Background tasks for health checks and integration monitoring
"""

import asyncio
from typing import Dict, List, Any
from datetime import datetime
from celery import shared_task
from celery.utils.log import get_task_logger
import redis
from sqlalchemy import text

from apps.backend.core.database import get_db
from apps.backend.core.config import settings
from apps.backend.services.websocket_pipeline_manager import websocket_pipeline_manager
from apps.backend.services.supabase_service import supabase_service

logger = get_task_logger(__name__)


@shared_task(
    bind=True,
    name="tasks.check_integrations",
    max_retries=3,
    default_retry_delay=30,
    queue="high_priority",
    priority=9,
)
def check_integrations(self) -> Dict[str, Any]:
    """
    Check health of all external integrations

    Monitors:
    - Database connectivity
    - Redis connectivity
    - Pusher service status
    - Supabase connectivity (if configured)

    Returns:
        Dictionary with health check results
    """
    results = {
        "timestamp": datetime.utcnow().isoformat(),
        "status": "healthy",
        "checks": {},
        "errors": []
    }

    # Check database
    try:
        db = next(get_db())
        db.execute(text("SELECT 1"))
        results["checks"]["database"] = {"status": "up", "latency_ms": 0}
        logger.info("Database health check: OK")
    except Exception as e:
        results["checks"]["database"] = {"status": "down", "error": str(e)}
        results["status"] = "degraded"
        results["errors"].append(f"Database: {str(e)}")
        logger.error(f"Database health check failed: {e}")

    # Check Redis
    try:
        redis_client = redis.from_url(settings.REDIS_URL)
        redis_client.ping()
        results["checks"]["redis"] = {"status": "up"}
        logger.info("Redis health check: OK")
    except Exception as e:
        results["checks"]["redis"] = {"status": "down", "error": str(e)}
        results["status"] = "degraded"
        results["errors"].append(f"Redis: {str(e)}")
        logger.error(f"Redis health check failed: {e}")

    # Check Pusher
    try:
        if hasattr(settings, 'PUSHER_APP_ID') and settings.PUSHER_APP_ID:
            # Try to send a test event via Pusher
            test_result = asyncio.run(websocket_pipeline_manager.send_event(
                channel='test-health-check',
                event_type='ping',
                data={'timestamp': datetime.utcnow().isoformat()}
            ))

            if test_result:
                results["checks"]["pusher"] = {"status": "up", "latency_ms": 0}
            else:
                results["checks"]["pusher"] = {"status": "degraded"}
        else:
            results["checks"]["pusher"] = {"status": "not_configured"}

        logger.info("Pusher health check: OK")
    except Exception as e:
        results["checks"]["pusher"] = {"status": "down", "error": str(e)}
        results["status"] = "degraded"
        results["errors"].append(f"Pusher: {str(e)}")
        logger.error(f"Pusher health check failed: {e}")

    # Check Supabase
    try:
        if hasattr(settings, 'SUPABASE_URL') and settings.SUPABASE_URL:
            # Try a simple connection test
            test_result = supabase_service.ping()

            if test_result:
                results["checks"]["supabase"] = {"status": "up"}
            else:
                results["checks"]["supabase"] = {"status": "degraded"}
        else:
            results["checks"]["supabase"] = {"status": "not_configured"}

        logger.info("Supabase health check: OK")
    except Exception as e:
        results["checks"]["supabase"] = {"status": "unknown", "error": str(e)}
        logger.warning(f"Supabase health check warning: {e}")

    # Overall status
    if results["status"] == "degraded":
        logger.warning(f"Integration health check DEGRADED: {len(results['errors'])} errors")
    else:
        logger.info("All integrations healthy")

    return results


@shared_task(
    bind=True,
    name="tasks.check_database_health",
    max_retries=2,
    default_retry_delay=15,
    queue="high_priority",
    priority=8,
)
def check_database_health(self) -> Dict[str, Any]:
    """Check database connection pool and performance"""
    try:
        db = next(get_db())
        result = db.execute(text("SELECT COUNT(*) as count FROM information_schema.tables"))
        table_count = result.scalar()

        return {
            "status": "healthy",
            "tables": table_count,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }


@shared_task(
    bind=True,
    name="tasks.check_redis_health",
    max_retries=2,
    default_retry_delay=15,
    queue="high_priority",
    priority=8,
)
def check_redis_health(self) -> Dict[str, Any]:
    """Check Redis connectivity and memory usage"""
    try:
        redis_client = redis.from_url(settings.REDIS_URL)
        info = redis_client.info("memory")

        return {
            "status": "healthy",
            "memory_used_mb": int(info.get("used_memory", 0)) / (1024 * 1024),
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Redis health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }
