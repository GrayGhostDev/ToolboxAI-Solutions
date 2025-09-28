"""
Performance Optimization Integration Module
Coordinates all performance optimizations including caching, database pooling,
and Pusher optimization to achieve target P95 latency of <150ms.
"""

import asyncio
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from contextlib import asynccontextmanager

from apps.backend.core.cache import initialize_cache, cache, get_cache_health
from apps.backend.core.db_optimization import initialize_db_optimization, optimizer, get_db_health
from apps.backend.services.pusher_optimized import get_optimized_pusher_service, get_pusher_health
from apps.backend.core.config import settings

logger = logging.getLogger(__name__)


class PerformanceOptimizationManager:
    """Manages all performance optimization systems"""

    def __init__(self):
        self.initialized = False
        self.initialization_time: Optional[datetime] = None
        self.services_status = {
            "cache": {"status": "not_initialized", "error": None},
            "database": {"status": "not_initialized", "error": None},
            "pusher": {"status": "not_initialized", "error": None},
        }

    async def initialize_all_optimizations(self) -> Dict[str, Any]:
        """Initialize all performance optimization systems"""

        if self.initialized:
            logger.info("Performance optimizations already initialized")
            return {"status": "already_initialized", "services": self.services_status}

        logger.info("🚀 Initializing performance optimization systems...")
        start_time = datetime.now()

        initialization_results = {}

        # 1. Initialize Redis Cache System
        try:
            logger.info("Initializing Redis cache system...")
            await initialize_cache()
            self.services_status["cache"] = {"status": "initialized", "error": None}
            logger.info("✅ Redis cache system initialized")

        except Exception as e:
            error_msg = f"Failed to initialize cache system: {e}"
            logger.error(f"❌ {error_msg}")
            self.services_status["cache"] = {"status": "failed", "error": str(e)}
            initialization_results["cache"] = {"success": False, "error": str(e)}

        # 2. Initialize Database Optimization
        try:
            logger.info("Initializing database optimization...")
            await initialize_db_optimization()
            self.services_status["database"] = {"status": "initialized", "error": None}
            logger.info("✅ Database optimization initialized")

        except Exception as e:
            error_msg = f"Failed to initialize database optimization: {e}"
            logger.error(f"❌ {error_msg}")
            self.services_status["database"] = {"status": "failed", "error": str(e)}
            initialization_results["database"] = {"success": False, "error": str(e)}

        # 3. Initialize Optimized Pusher Service
        try:
            logger.info("Initializing optimized Pusher service...")
            await get_optimized_pusher_service()
            self.services_status["pusher"] = {"status": "initialized", "error": None}
            logger.info("✅ Optimized Pusher service initialized")

        except Exception as e:
            error_msg = f"Failed to initialize Pusher optimization: {e}"
            logger.error(f"❌ {error_msg}")
            self.services_status["pusher"] = {"status": "failed", "error": str(e)}
            initialization_results["pusher"] = {"success": False, "error": str(e)}

        # Mark as initialized if at least one service succeeded
        successful_services = [
            name
            for name, status in self.services_status.items()
            if status["status"] == "initialized"
        ]

        if successful_services:
            self.initialized = True
            self.initialization_time = start_time

        duration = (datetime.now() - start_time).total_seconds()

        summary = {
            "status": "completed" if self.initialized else "partial_failure",
            "duration_seconds": round(duration, 2),
            "successful_services": successful_services,
            "failed_services": [
                name
                for name, status in self.services_status.items()
                if status["status"] == "failed"
            ],
            "services_status": self.services_status,
            "initialization_time": (
                self.initialization_time.isoformat() if self.initialization_time else None
            ),
        }

        if self.initialized:
            logger.info(
                f"🎉 Performance optimization initialization completed in {duration:.2f}s - "
                f"Services: {', '.join(successful_services)}"
            )
        else:
            logger.error(
                f"⚠️ Performance optimization initialization partially failed after {duration:.2f}s"
            )

        return summary

    async def get_comprehensive_health_status(self) -> Dict[str, Any]:
        """Get comprehensive health status of all optimization systems"""

        health_checks = {}

        # Cache health
        try:
            health_checks["cache"] = await get_cache_health()
        except Exception as e:
            health_checks["cache"] = {"status": "unhealthy", "error": str(e)}

        # Database health
        try:
            health_checks["database"] = await get_db_health()
        except Exception as e:
            health_checks["database"] = {"status": "unhealthy", "error": str(e)}

        # Pusher health
        try:
            health_checks["pusher"] = await get_pusher_health()
        except Exception as e:
            health_checks["pusher"] = {"status": "unhealthy", "error": str(e)}

        # Overall status
        all_healthy = all(check.get("status") == "healthy" for check in health_checks.values())

        return {
            "overall_status": "healthy" if all_healthy else "degraded",
            "optimization_enabled": self.initialized,
            "initialization_time": (
                self.initialization_time.isoformat() if self.initialization_time else None
            ),
            "services": health_checks,
            "timestamp": datetime.now().isoformat(),
        }

    async def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics from all optimization systems"""

        metrics = {
            "timestamp": datetime.now().isoformat(),
            "optimization_enabled": self.initialized,
        }

        # Cache metrics
        try:
            cache_health = await get_cache_health()
            metrics["cache"] = cache_health.get("stats", {})
        except Exception as e:
            metrics["cache"] = {"error": str(e)}

        # Database metrics
        try:
            db_health = await get_db_health()
            metrics["database"] = {
                "connection_pool": db_health.get("connection_pool", {}),
                "query_performance": db_health.get("query_performance", {}),
                "prepared_statements": db_health.get("prepared_statements", {}),
            }
        except Exception as e:
            metrics["database"] = {"error": str(e)}

        # Pusher metrics
        try:
            pusher_health = await get_pusher_health()
            metrics["pusher"] = pusher_health.get("performance", {})
        except Exception as e:
            metrics["pusher"] = {"error": str(e)}

        return metrics

    async def warm_caches(self) -> Dict[str, Any]:
        """Warm all caches for better performance"""

        if not self.initialized:
            return {"status": "skipped", "reason": "Performance optimizations not initialized"}

        logger.info("🔥 Starting cache warming...")
        start_time = datetime.now()

        warming_results = {"dashboard_cache": False, "query_cache": False, "api_cache": False}

        # Warm dashboard cache for sample users
        try:
            from apps.backend.core.cache import warmer

            # Sample users to warm cache for
            sample_users = [(1, "admin"), (2, "teacher"), (3, "student"), (4, "parent")]

            for user_id, role in sample_users:
                try:
                    await warmer.warm_user_dashboard(user_id, role)
                except Exception as e:
                    logger.debug(f"Failed to warm cache for user {user_id}: {e}")

            warming_results["dashboard_cache"] = True
            logger.info("✅ Dashboard cache warmed")

        except Exception as e:
            logger.error(f"❌ Failed to warm dashboard cache: {e}")

        # Warm common queries
        try:
            from apps.backend.core.db_optimization import optimizer

            # Execute some common queries to warm cache
            common_queries = [
                ("SELECT 1 as health_check", {}),
                ("SELECT current_timestamp", {}),
            ]

            for query, params in common_queries:
                try:
                    await optimizer.execute_optimized_query(query, params, use_cache=True)
                except Exception as e:
                    logger.debug(f"Failed to execute query for warming: {e}")

            warming_results["query_cache"] = True
            logger.info("✅ Query cache warmed")

        except Exception as e:
            logger.error(f"❌ Failed to warm query cache: {e}")

        # Warm API response cache
        try:
            from apps.backend.core.cache import cache, CacheConfig

            # Pre-cache some common API responses
            common_responses = [
                ("api:health", {"status": "healthy", "timestamp": datetime.now().isoformat()}),
                ("api:config:app_name", settings.APP_NAME),
                ("api:config:version", settings.APP_VERSION),
            ]

            for key, data in common_responses:
                try:
                    await cache.set(key, data, CacheConfig.LONG_TTL)
                except Exception as e:
                    logger.debug(f"Failed to cache {key}: {e}")

            warming_results["api_cache"] = True
            logger.info("✅ API cache warmed")

        except Exception as e:
            logger.error(f"❌ Failed to warm API cache: {e}")

        duration = (datetime.now() - start_time).total_seconds()
        successful_warmups = sum(warming_results.values())

        return {
            "status": "completed",
            "duration_seconds": round(duration, 2),
            "successful_warmups": successful_warmups,
            "total_warmups": len(warming_results),
            "results": warming_results,
            "timestamp": datetime.now().isoformat(),
        }


# Global performance manager instance
_performance_manager: Optional[PerformanceOptimizationManager] = None


def get_performance_manager() -> PerformanceOptimizationManager:
    """Get or create the global performance manager"""
    global _performance_manager

    if _performance_manager is None:
        _performance_manager = PerformanceOptimizationManager()

    return _performance_manager


# Context manager for performance optimization lifecycle
@asynccontextmanager
async def performance_optimization_context():
    """Context manager for managing performance optimization lifecycle"""
    manager = get_performance_manager()

    try:
        # Initialize optimizations
        await manager.initialize_all_optimizations()

        # Warm caches
        await manager.warm_caches()

        yield manager

    finally:
        # Cleanup would go here if needed
        pass


# Convenience functions for common operations
async def initialize_performance_optimizations() -> Dict[str, Any]:
    """Initialize all performance optimizations"""
    manager = get_performance_manager()
    return await manager.initialize_all_optimizations()


async def get_optimization_health() -> Dict[str, Any]:
    """Get optimization system health status"""
    manager = get_performance_manager()
    return await manager.get_comprehensive_health_status()


async def get_optimization_metrics() -> Dict[str, Any]:
    """Get optimization performance metrics"""
    manager = get_performance_manager()
    return await manager.get_performance_metrics()


async def warm_all_caches() -> Dict[str, Any]:
    """Warm all caches for better performance"""
    manager = get_performance_manager()
    return await manager.warm_caches()


# Middleware integration helpers
def create_performance_middleware():
    """Create FastAPI middleware for performance optimization"""

    async def performance_middleware(request, call_next):
        """Middleware to apply performance optimizations"""

        # Add performance headers
        response = await call_next(request)

        # Add optimization status headers
        manager = get_performance_manager()
        if manager.initialized:
            response.headers["X-Performance-Optimization"] = "enabled"

        return response

    return performance_middleware


# Health check endpoint data
async def get_optimization_status_for_health_check() -> Dict[str, Any]:
    """Get optimization status for health check endpoints"""

    manager = get_performance_manager()

    return {
        "performance_optimization": {
            "enabled": manager.initialized,
            "initialization_time": (
                manager.initialization_time.isoformat() if manager.initialization_time else None
            ),
            "services": {
                name: status["status"] for name, status in manager.services_status.items()
            },
        }
    }


# Export main interfaces
__all__ = [
    "get_performance_manager",
    "performance_optimization_context",
    "initialize_performance_optimizations",
    "get_optimization_health",
    "get_optimization_metrics",
    "warm_all_caches",
    "create_performance_middleware",
    "get_optimization_status_for_health_check",
]
