"""
Enhanced Health Check System for ToolBoxAI Backend
===============================================

This module provides comprehensive health checks including:
- Detailed component health status
- Performance metrics integration
- Dependency health validation
- SLA compliance monitoring
- Metrics collection for monitoring systems
"""

import asyncio
import logging
import os
import time
from datetime import datetime, timezone
from enum import Enum
from typing import Any

import asyncpg
import httpx
import redis.asyncio as aioredis
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from apps.backend.core.config import settings
from apps.backend.core.metrics import metrics

logger = logging.getLogger(__name__)


class HealthStatus(str, Enum):
    """Health status enumeration"""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


class ComponentHealth(BaseModel):
    """Individual component health model"""

    name: str
    status: HealthStatus
    response_time_ms: float | None = None
    last_check: datetime
    error: str | None = None
    metrics: dict[str, Any] = Field(default_factory=dict)
    details: dict[str, Any] = Field(default_factory=dict)


class SystemHealth(BaseModel):
    """Overall system health model"""

    status: HealthStatus
    timestamp: datetime
    uptime_seconds: float
    version: str
    environment: str
    components: list[ComponentHealth]
    performance_summary: dict[str, Any] = Field(default_factory=dict)
    sla_compliance: dict[str, Any] = Field(default_factory=dict)


class EnhancedHealthChecker:
    """
    Comprehensive health checker for ToolBoxAI backend system.

    Monitors all critical dependencies and provides detailed health status
    with performance metrics and SLA compliance information.
    """

    def __init__(self):
        self.start_time = time.time()
        self.last_full_check = None
        self.cached_health = None
        self.cache_ttl = 30  # Cache health results for 30 seconds

        # Component timeout settings
        self.timeouts = {"database": 5.0, "redis": 2.0, "external_api": 10.0, "file_system": 1.0}

        # Performance thresholds
        self.performance_thresholds = {
            "response_time_ms": 150,  # SLA: P95 < 150ms
            "error_rate_percent": 1.0,  # SLA: < 1% error rate
            "uptime_percent": 99.9,  # SLA: > 99.9% uptime
        }

    async def get_health_status(
        self, quick_check: bool = False, include_metrics: bool = True
    ) -> SystemHealth:
        """
        Get comprehensive system health status.

        Args:
            quick_check: If True, performs basic checks only
            include_metrics: If True, includes performance metrics

        Returns:
            SystemHealth object with detailed status information
        """
        current_time = time.time()

        # Use cached result if still valid
        if (
            self.cached_health
            and self.last_full_check
            and current_time - self.last_full_check < self.cache_ttl
            and not include_metrics
        ):  # Skip cache for metrics requests
            return self.cached_health

        logger.info(f"Performing {'quick' if quick_check else 'comprehensive'} health check")

        start_check_time = time.time()
        components = []

        # Core dependency checks
        if quick_check:
            components = await self._quick_health_checks()
        else:
            components = await self._comprehensive_health_checks()

        # Calculate overall status
        overall_status = self._calculate_overall_status(components)

        # Collect performance summary if requested
        performance_summary = {}
        sla_compliance = {}

        if include_metrics:
            performance_summary = await self._collect_performance_summary()
            sla_compliance = await self._check_sla_compliance()

        # Update metrics
        metrics.set_health_status(overall_status.value)
        metrics.update_uptime(self.start_time)

        # Record health check duration
        check_duration = time.time() - start_check_time
        logger.info(f"Health check completed in {check_duration:.3f}s")

        health_status = SystemHealth(
            status=overall_status,
            timestamp=datetime.now(timezone.utc),
            uptime_seconds=current_time - self.start_time,
            version=settings.APP_VERSION,
            environment=settings.ENVIRONMENT,
            components=components,
            performance_summary=performance_summary,
            sla_compliance=sla_compliance,
        )

        # Cache result
        self.cached_health = health_status
        self.last_full_check = current_time

        return health_status

    async def _quick_health_checks(self) -> list[ComponentHealth]:
        """Perform quick health checks for critical components"""
        components = []

        # Basic API health
        components.append(
            ComponentHealth(
                name="api",
                status=HealthStatus.HEALTHY,
                response_time_ms=0.1,
                last_check=datetime.now(timezone.utc),
                details={"check_type": "basic"},
            )
        )

        # Quick database ping
        db_health = await self._check_database_health(quick=True)
        components.append(db_health)

        # Quick Redis ping
        redis_health = await self._check_redis_health(quick=True)
        components.append(redis_health)

        return components

    async def _comprehensive_health_checks(self) -> list[ComponentHealth]:
        """Perform comprehensive health checks for all components"""
        components = []

        # Run health checks concurrently for better performance
        health_checks = [
            self._check_database_health(),
            self._check_redis_health(),
            self._check_file_system_health(),
            self._check_external_dependencies_health(),
            self._check_metrics_system_health(),
            self._check_agent_system_health(),
        ]

        try:
            results = await asyncio.gather(*health_checks, return_exceptions=True)

            for result in results:
                if isinstance(result, Exception):
                    logger.error(f"Health check failed: {result}")
                    components.append(
                        ComponentHealth(
                            name="unknown",
                            status=HealthStatus.UNHEALTHY,
                            last_check=datetime.now(timezone.utc),
                            error=str(result),
                        )
                    )
                else:
                    components.append(result)

        except Exception as e:
            logger.error(f"Comprehensive health check failed: {e}")
            components.append(
                ComponentHealth(
                    name="health_system",
                    status=HealthStatus.UNHEALTHY,
                    last_check=datetime.now(timezone.utc),
                    error=f"Health check system error: {str(e)}",
                )
            )

        return components

    async def _check_database_health(self, quick: bool = False) -> ComponentHealth:
        """Check PostgreSQL database health"""
        start_time = time.time()

        try:
            # Basic connection test
            conn = await asyncpg.connect(settings.DATABASE_URL, timeout=self.timeouts["database"])

            if quick:
                # Just test connection
                await conn.close()
                response_time = (time.time() - start_time) * 1000

                return ComponentHealth(
                    name="database",
                    status=HealthStatus.HEALTHY,
                    response_time_ms=response_time,
                    last_check=datetime.now(timezone.utc),
                    details={"check_type": "quick_ping"},
                )

            # Comprehensive database checks
            details = {}

            # Test query execution
            result = await conn.fetchval("SELECT 1")
            if result != 1:
                raise Exception("Database query test failed")

            # Check connection pool status
            pool_info = await conn.fetchrow(
                """
                SELECT
                    count(*) as active_connections,
                    current_setting('max_connections')::int as max_connections
                FROM pg_stat_activity
                WHERE state = 'active'
            """
            )

            details.update(
                {
                    "active_connections": pool_info["active_connections"],
                    "max_connections": pool_info["max_connections"],
                    "connection_usage_percent": (
                        pool_info["active_connections"] / pool_info["max_connections"]
                    )
                    * 100,
                }
            )

            # Check database size and performance
            db_stats = await conn.fetchrow(
                """
                SELECT
                    pg_database_size(current_database()) as db_size_bytes,
                    (SELECT count(*) FROM pg_stat_activity) as total_connections
            """
            )

            details.update(
                {
                    "database_size_mb": db_stats["db_size_bytes"] / (1024 * 1024),
                    "total_connections": db_stats["total_connections"],
                }
            )

            await conn.close()
            response_time = (time.time() - start_time) * 1000

            # Determine status based on performance
            status = HealthStatus.HEALTHY
            if response_time > 1000:  # > 1 second is concerning
                status = HealthStatus.DEGRADED
            if details["connection_usage_percent"] > 90:
                status = HealthStatus.DEGRADED

            return ComponentHealth(
                name="database",
                status=status,
                response_time_ms=response_time,
                last_check=datetime.now(timezone.utc),
                details=details,
            )

        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            logger.error(f"Database health check failed: {e}")

            return ComponentHealth(
                name="database",
                status=HealthStatus.UNHEALTHY,
                response_time_ms=response_time,
                last_check=datetime.now(timezone.utc),
                error=str(e),
            )

    async def _check_redis_health(self, quick: bool = False) -> ComponentHealth:
        """Check Redis cache health"""
        start_time = time.time()

        try:
            redis_client = aioredis.from_url(
                settings.REDIS_URL, socket_timeout=self.timeouts["redis"]
            )

            if quick:
                # Just ping Redis
                await redis_client.ping()
                await redis_client.close()
                response_time = (time.time() - start_time) * 1000

                return ComponentHealth(
                    name="redis",
                    status=HealthStatus.HEALTHY,
                    response_time_ms=response_time,
                    last_check=datetime.now(timezone.utc),
                    details={"check_type": "ping"},
                )

            # Comprehensive Redis checks
            details = {}

            # Test basic operations
            test_key = "health_check_test"
            await redis_client.set(test_key, "test_value", ex=10)
            test_result = await redis_client.get(test_key)
            await redis_client.delete(test_key)

            if test_result != b"test_value":
                raise Exception("Redis read/write test failed")

            # Get Redis info
            redis_info = await redis_client.info()

            details.update(
                {
                    "redis_version": redis_info.get("redis_version", "unknown"),
                    "connected_clients": redis_info.get("connected_clients", 0),
                    "used_memory_mb": redis_info.get("used_memory", 0) / (1024 * 1024),
                    "used_memory_peak_mb": redis_info.get("used_memory_peak", 0) / (1024 * 1024),
                    "keyspace_hits": redis_info.get("keyspace_hits", 0),
                    "keyspace_misses": redis_info.get("keyspace_misses", 0),
                }
            )

            # Calculate hit rate
            hits = details["keyspace_hits"]
            misses = details["keyspace_misses"]
            if hits + misses > 0:
                details["hit_rate_percent"] = (hits / (hits + misses)) * 100
            else:
                details["hit_rate_percent"] = 100

            await redis_client.close()
            response_time = (time.time() - start_time) * 1000

            # Determine status
            status = HealthStatus.HEALTHY
            if response_time > 500:  # > 500ms is concerning for Redis
                status = HealthStatus.DEGRADED
            if details["hit_rate_percent"] < 80:  # Low hit rate
                status = HealthStatus.DEGRADED

            return ComponentHealth(
                name="redis",
                status=status,
                response_time_ms=response_time,
                last_check=datetime.now(timezone.utc),
                details=details,
            )

        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            logger.error(f"Redis health check failed: {e}")

            return ComponentHealth(
                name="redis",
                status=HealthStatus.UNHEALTHY,
                response_time_ms=response_time,
                last_check=datetime.now(timezone.utc),
                error=str(e),
            )

    async def _check_file_system_health(self) -> ComponentHealth:
        """Check file system health and disk space"""
        start_time = time.time()

        try:
            import shutil

            # Check disk space
            total, used, free = shutil.disk_usage("/")

            details = {
                "total_gb": total / (1024**3),
                "used_gb": used / (1024**3),
                "free_gb": free / (1024**3),
                "usage_percent": (used / total) * 100,
            }

            # Test file operations
            test_file = "/tmp/toolboxai_health_test"
            try:
                with open(test_file, "w") as f:
                    f.write("health check test")
                with open(test_file) as f:
                    content = f.read()
                os.remove(test_file)

                if content != "health check test":
                    raise Exception("File read/write test failed")
            except Exception as e:
                raise Exception(f"File system test failed: {e}")

            response_time = (time.time() - start_time) * 1000

            # Determine status based on disk usage
            status = HealthStatus.HEALTHY
            if details["usage_percent"] > 85:
                status = HealthStatus.DEGRADED
            if details["usage_percent"] > 95:
                status = HealthStatus.UNHEALTHY

            return ComponentHealth(
                name="file_system",
                status=status,
                response_time_ms=response_time,
                last_check=datetime.now(timezone.utc),
                details=details,
            )

        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            logger.error(f"File system health check failed: {e}")

            return ComponentHealth(
                name="file_system",
                status=HealthStatus.UNHEALTHY,
                response_time_ms=response_time,
                last_check=datetime.now(timezone.utc),
                error=str(e),
            )

    async def _check_external_dependencies_health(self) -> ComponentHealth:
        """Check external API dependencies"""
        start_time = time.time()

        details = {}
        errors = []

        try:
            async with httpx.AsyncClient(timeout=self.timeouts["external_api"]) as client:

                # Check OpenAI API if configured
                if settings.OPENAI_API_KEY:
                    try:
                        # Simple API check
                        response = await client.get(
                            "https://api.openai.com/v1/models",
                            headers={"Authorization": f"Bearer {settings.OPENAI_API_KEY}"},
                        )
                        details["openai_status"] = response.status_code
                        if response.status_code != 200:
                            errors.append(f"OpenAI API returned {response.status_code}")
                    except Exception as e:
                        details["openai_status"] = "error"
                        errors.append(f"OpenAI API error: {str(e)}")

                # Add other external dependency checks here

            response_time = (time.time() - start_time) * 1000

            status = HealthStatus.HEALTHY
            if errors:
                status = HealthStatus.DEGRADED if len(errors) < 2 else HealthStatus.UNHEALTHY

            return ComponentHealth(
                name="external_apis",
                status=status,
                response_time_ms=response_time,
                last_check=datetime.now(timezone.utc),
                details=details,
                error="; ".join(errors) if errors else None,
            )

        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            logger.error(f"External dependencies health check failed: {e}")

            return ComponentHealth(
                name="external_apis",
                status=HealthStatus.UNHEALTHY,
                response_time_ms=response_time,
                last_check=datetime.now(timezone.utc),
                error=str(e),
            )

    async def _check_metrics_system_health(self) -> ComponentHealth:
        """Check metrics collection system health"""
        start_time = time.time()

        try:
            # Check if metrics are being collected
            from apps.backend.core.metrics import check_metrics_health

            metrics_health = check_metrics_health()
            response_time = (time.time() - start_time) * 1000

            status = HealthStatus.HEALTHY
            if metrics_health["status"] != "healthy":
                status = HealthStatus.DEGRADED

            return ComponentHealth(
                name="metrics_system",
                status=status,
                response_time_ms=response_time,
                last_check=datetime.now(timezone.utc),
                details=metrics_health,
            )

        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            logger.error(f"Metrics system health check failed: {e}")

            return ComponentHealth(
                name="metrics_system",
                status=HealthStatus.UNHEALTHY,
                response_time_ms=response_time,
                last_check=datetime.now(timezone.utc),
                error=str(e),
            )

    async def _check_agent_system_health(self) -> ComponentHealth:
        """Check AI agent system health"""
        start_time = time.time()

        try:
            details = {
                "mock_check": True,  # Placeholder for actual agent health checks
                "agents_available": True,
            }

            response_time = (time.time() - start_time) * 1000

            return ComponentHealth(
                name="agent_system",
                status=HealthStatus.HEALTHY,
                response_time_ms=response_time,
                last_check=datetime.now(timezone.utc),
                details=details,
            )

        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            logger.error(f"Agent system health check failed: {e}")

            return ComponentHealth(
                name="agent_system",
                status=HealthStatus.UNHEALTHY,
                response_time_ms=response_time,
                last_check=datetime.now(timezone.utc),
                error=str(e),
            )

    async def _collect_performance_summary(self) -> dict[str, Any]:
        """Collect performance metrics summary"""
        try:
            # This would integrate with actual metrics collection
            # For now, return mock data structure
            return {
                "avg_response_time_ms": 85.2,
                "p95_response_time_ms": 142.1,
                "error_rate_percent": 0.3,
                "requests_per_minute": 156,
                "active_connections": 12,
                "cache_hit_rate_percent": 87.3,
            }
        except Exception as e:
            logger.error(f"Failed to collect performance summary: {e}")
            return {}

    async def _check_sla_compliance(self) -> dict[str, Any]:
        """Check SLA compliance metrics"""
        try:
            performance = await self._collect_performance_summary()

            sla_status = {
                "response_time_sla": {
                    "threshold_ms": self.performance_thresholds["response_time_ms"],
                    "current_p95_ms": performance.get("p95_response_time_ms", 0),
                    "compliant": performance.get("p95_response_time_ms", 0)
                    < self.performance_thresholds["response_time_ms"],
                },
                "error_rate_sla": {
                    "threshold_percent": self.performance_thresholds["error_rate_percent"],
                    "current_percent": performance.get("error_rate_percent", 0),
                    "compliant": performance.get("error_rate_percent", 0)
                    < self.performance_thresholds["error_rate_percent"],
                },
                "overall_sla_compliance": True,  # Would be calculated based on actual metrics
            }

            return sla_status

        except Exception as e:
            logger.error(f"Failed to check SLA compliance: {e}")
            return {"error": str(e)}

    def _calculate_overall_status(self, components: list[ComponentHealth]) -> HealthStatus:
        """Calculate overall system status based on component health"""
        if not components:
            return HealthStatus.UNHEALTHY

        unhealthy_count = sum(1 for c in components if c.status == HealthStatus.UNHEALTHY)
        degraded_count = sum(1 for c in components if c.status == HealthStatus.DEGRADED)

        # System is unhealthy if any critical component is unhealthy
        critical_components = ["database", "redis", "api"]
        for component in components:
            if component.name in critical_components and component.status == HealthStatus.UNHEALTHY:
                return HealthStatus.UNHEALTHY

        # System is unhealthy if too many components are unhealthy
        if unhealthy_count > len(components) * 0.3:  # >30% unhealthy
            return HealthStatus.UNHEALTHY

        # System is degraded if any component is unhealthy or many are degraded
        if unhealthy_count > 0 or degraded_count > len(components) * 0.5:
            return HealthStatus.DEGRADED

        return HealthStatus.HEALTHY


# Global health checker instance
health_checker = EnhancedHealthChecker()

# FastAPI router for health endpoints
router = APIRouter(prefix="/health", tags=["health"])


@router.get("/", response_model=SystemHealth)
async def get_health_status(quick: bool = False, metrics: bool = True):
    """
    Get comprehensive system health status.

    Query Parameters:
    - quick: Perform quick health checks only (faster response)
    - metrics: Include performance metrics in response
    """
    try:
        health_status = await health_checker.get_health_status(
            quick_check=quick, include_metrics=metrics
        )

        # Return appropriate HTTP status based on health
        if health_status.status == HealthStatus.HEALTHY:
            status_code = 200
        elif health_status.status == HealthStatus.DEGRADED:
            status_code = 200  # Still operational
        else:
            status_code = 503  # Service unavailable

        return JSONResponse(content=health_status.dict(), status_code=status_code)

    except Exception as e:
        logger.error(f"Health check endpoint failed: {e}")
        return JSONResponse(
            content={
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
            status_code=503,
        )


@router.get("/ready")
async def readiness_probe():
    """Kubernetes readiness probe endpoint"""
    try:
        health_status = await health_checker.get_health_status(
            quick_check=True, include_metrics=False
        )

        if health_status.status in [HealthStatus.HEALTHY, HealthStatus.DEGRADED]:
            return {"status": "ready"}
        else:
            return JSONResponse(content={"status": "not_ready"}, status_code=503)
    except Exception as e:
        logger.error(f"Readiness probe failed: {e}")
        return JSONResponse(content={"status": "not_ready", "error": str(e)}, status_code=503)


@router.get("/live")
async def liveness_probe():
    """Kubernetes liveness probe endpoint"""
    return {"status": "alive", "timestamp": datetime.now(timezone.utc)}


@router.get("/metrics-integration")
async def health_metrics_endpoint():
    """Endpoint specifically for metrics integration"""
    try:
        health_status = await health_checker.get_health_status(
            quick_check=False, include_metrics=True
        )

        # Return metrics-focused response
        return {
            "overall_status": health_status.status.value,
            "uptime_seconds": health_status.uptime_seconds,
            "component_count": len(health_status.components),
            "healthy_components": len(
                [c for c in health_status.components if c.status == HealthStatus.HEALTHY]
            ),
            "degraded_components": len(
                [c for c in health_status.components if c.status == HealthStatus.DEGRADED]
            ),
            "unhealthy_components": len(
                [c for c in health_status.components if c.status == HealthStatus.UNHEALTHY]
            ),
            "performance_summary": health_status.performance_summary,
            "sla_compliance": health_status.sla_compliance,
        }

    except Exception as e:
        logger.error(f"Health metrics endpoint failed: {e}")
        return JSONResponse(content={"error": str(e)}, status_code=500)


# Export main components
__all__ = [
    "EnhancedHealthChecker",
    "health_checker",
    "router",
    "HealthStatus",
    "ComponentHealth",
    "SystemHealth",
]
