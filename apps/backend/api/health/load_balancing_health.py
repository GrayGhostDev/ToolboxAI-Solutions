"""
Load Balancing Integration Health Checks

Comprehensive health checks for all load balancing components:
- Circuit breakers state and metrics
- Rate limiting functionality
- Database replica routing and lag
- Edge cache performance
- WebSocket cluster status
- Global load balancer health
"""

import asyncio
import logging
import time
from datetime import datetime
from enum import Enum

import httpx
import redis.asyncio as aioredis
from apps.backend.core.websocket_cluster import get_websocket_cluster
from database.replica_router import get_replica_router
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from apps.backend.core.circuit_breaker import CircuitBreakerState, get_circuit_breaker
from apps.backend.core.edge_cache import CacheTier, EdgeCache
from apps.backend.core.rate_limiter import RateLimiter

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/health/load-balancing", tags=["health"])


class HealthStatus(Enum):
    """Health check status levels"""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    CRITICAL = "critical"


class ComponentHealth:
    """Health check result for a component"""

    def __init__(self, name: str):
        self.name = name
        self.status = HealthStatus.HEALTHY
        self.message = "OK"
        self.details = {}
        self.latency_ms = 0
        self.checked_at = datetime.utcnow()

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "status": self.status.value,
            "message": self.message,
            "details": self.details,
            "latency_ms": self.latency_ms,
            "checked_at": self.checked_at.isoformat(),
        }


class LoadBalancingHealthChecker:
    """Comprehensive health checker for load balancing infrastructure"""

    def __init__(self, redis_url: str | None = None, enable_detailed_checks: bool = True):
        self.redis_url = redis_url or "redis://localhost:6379"
        self.enable_detailed = enable_detailed_checks
        self.redis_client: aioredis.Redis | None = None
        self.last_check_time = {}
        self.cached_results = {}
        self.cache_ttl = 30  # seconds

    async def initialize(self):
        """Initialize health checker"""
        self.redis_client = await aioredis.from_url(self.redis_url)

    async def cleanup(self):
        """Cleanup resources"""
        if self.redis_client:
            await self.redis_client.close()

    async def check_circuit_breakers(self) -> ComponentHealth:
        """Check circuit breaker health"""
        health = ComponentHealth("circuit_breakers")
        start_time = time.time()

        try:
            # Get all circuit breakers
            breakers = {
                "database": get_circuit_breaker("database"),
                "api": get_circuit_breaker("api"),
                "external_service": get_circuit_breaker("external_service"),
                "redis": get_circuit_breaker("redis"),
            }

            open_circuits = []
            half_open_circuits = []
            metrics_summary = {"total_calls": 0, "failed_calls": 0, "success_rate": 0}

            for name, breaker in breakers.items():
                if breaker:
                    status = breaker.get_status()

                    # Check state
                    if status["state"] == CircuitBreakerState.OPEN.value:
                        open_circuits.append(name)
                    elif status["state"] == CircuitBreakerState.HALF_OPEN.value:
                        half_open_circuits.append(name)

                    # Aggregate metrics
                    if "metrics" in status:
                        metrics_summary["total_calls"] += status["metrics"]["total_calls"]
                        metrics_summary["failed_calls"] += status["metrics"]["failed_calls"]

            # Calculate overall success rate
            if metrics_summary["total_calls"] > 0:
                metrics_summary["success_rate"] = (
                    1 - (metrics_summary["failed_calls"] / metrics_summary["total_calls"])
                ) * 100

            # Determine health status
            if open_circuits:
                health.status = HealthStatus.DEGRADED
                health.message = f"Circuit breakers open: {', '.join(open_circuits)}"
            elif half_open_circuits:
                health.status = HealthStatus.DEGRADED
                health.message = f"Circuit breakers recovering: {', '.join(half_open_circuits)}"
            else:
                health.status = HealthStatus.HEALTHY
                health.message = "All circuits closed"

            health.details = {
                "open_circuits": open_circuits,
                "half_open_circuits": half_open_circuits,
                "metrics": metrics_summary,
            }

        except Exception as e:
            logger.error(f"Circuit breaker health check failed: {e}")
            health.status = HealthStatus.UNHEALTHY
            health.message = f"Check failed: {str(e)}"

        health.latency_ms = (time.time() - start_time) * 1000
        return health

    async def check_rate_limiting(self) -> ComponentHealth:
        """Check rate limiting functionality"""
        health = ComponentHealth("rate_limiting")
        start_time = time.time()

        try:
            if not self.redis_client:
                await self.initialize()

            # Create test rate limiter
            from apps.backend.core.rate_limiter import RateLimitConfig

            config = RateLimitConfig(requests_per_second=10, burst_size=5)
            limiter = RateLimiter(self.redis_client, config)

            # Test rate limiting
            test_user = f"health_check_{int(time.time())}"
            results = []

            # Make 15 rapid requests (should exceed limit)
            for i in range(15):
                result = await limiter.check_rate_limit(test_user)
                results.append(result.allowed)

            allowed_count = sum(results)
            rejected_count = len(results) - allowed_count

            # Verify rate limiting is working
            if rejected_count > 0:
                health.status = HealthStatus.HEALTHY
                health.message = "Rate limiting functioning correctly"
            else:
                health.status = HealthStatus.DEGRADED
                health.message = "Rate limiting may not be enforcing limits"

            # Check Redis connectivity for distributed rate limiting
            redis_info = await self.redis_client.info("stats")
            connected_clients = redis_info.get("connected_clients", 0)

            health.details = {
                "test_results": {
                    "requests_made": len(results),
                    "requests_allowed": allowed_count,
                    "requests_rejected": rejected_count,
                },
                "redis_status": {"connected": True, "connected_clients": connected_clients},
            }

        except Exception as e:
            logger.error(f"Rate limiting health check failed: {e}")
            health.status = HealthStatus.UNHEALTHY
            health.message = f"Check failed: {str(e)}"
            health.details = {"error": str(e)}

        health.latency_ms = (time.time() - start_time) * 1000
        return health

    async def check_database_replicas(self) -> ComponentHealth:
        """Check database replica health and routing"""
        health = ComponentHealth("database_replicas")
        start_time = time.time()

        try:
            router = get_replica_router()

            if not router:
                health.status = HealthStatus.UNHEALTHY
                health.message = "Replica router not initialized"
                return health

            # Get replica health
            unhealthy_replicas = []
            high_lag_replicas = []
            replica_details = []

            for url, replica_health in router.replica_health.items():
                replica_info = {
                    "hostname": replica_health.hostname,
                    "healthy": replica_health.is_healthy,
                    "lag_seconds": replica_health.lag_seconds,
                    "connections": replica_health.active_connections,
                    "weight": replica_health.weight,
                }
                replica_details.append(replica_info)

                if not replica_health.is_healthy:
                    unhealthy_replicas.append(replica_health.hostname)
                elif replica_health.lag_seconds > 5.0:
                    high_lag_replicas.append(replica_health.hostname)

            # Get routing metrics
            routing_metrics = router.get_metrics()

            # Determine health status
            if unhealthy_replicas:
                if len(unhealthy_replicas) == len(router.replica_urls):
                    health.status = HealthStatus.CRITICAL
                    health.message = "All replicas unhealthy"
                else:
                    health.status = HealthStatus.DEGRADED
                    health.message = f"Unhealthy replicas: {', '.join(unhealthy_replicas)}"
            elif high_lag_replicas:
                health.status = HealthStatus.DEGRADED
                health.message = f"High lag replicas: {', '.join(high_lag_replicas)}"
            else:
                health.status = HealthStatus.HEALTHY
                health.message = f"{len(replica_details)} replicas healthy"

            health.details = {
                "replicas": replica_details,
                "routing_metrics": routing_metrics,
                "unhealthy_count": len(unhealthy_replicas),
                "high_lag_count": len(high_lag_replicas),
            }

        except Exception as e:
            logger.error(f"Database replica health check failed: {e}")
            health.status = HealthStatus.UNHEALTHY
            health.message = f"Check failed: {str(e)}"

        health.latency_ms = (time.time() - start_time) * 1000
        return health

    async def check_edge_cache(self) -> ComponentHealth:
        """Check edge cache performance"""
        health = ComponentHealth("edge_cache")
        start_time = time.time()

        try:
            # Get cache instance (would be injected in real app)
            cache = EdgeCache(self.redis_url)
            await cache.initialize()

            # Test cache operations
            test_key = f"health_check_{int(time.time())}"
            test_value = b"test_data"

            # Test set
            set_success = await cache.set(test_key, test_value, CacheTier.EDGE)

            # Test get
            retrieved = await cache.get(test_key, CacheTier.EDGE)

            # Get metrics
            cache_metrics = cache.get_metrics()
            edge_metrics = cache_metrics.get(CacheTier.EDGE.value, {})

            # Verify cache working
            if set_success and retrieved and retrieved.value == test_value:
                health.status = HealthStatus.HEALTHY
                health.message = (
                    f"Cache operational, hit rate: {edge_metrics.get('hit_rate', 0):.1f}%"
                )
            else:
                health.status = HealthStatus.DEGRADED
                health.message = "Cache operations partially failing"

            # Check cache hit rate
            hit_rate = edge_metrics.get("hit_rate", 0)
            if hit_rate < 30 and edge_metrics.get("hits", 0) > 100:
                health.status = HealthStatus.DEGRADED
                health.message = f"Low cache hit rate: {hit_rate:.1f}%"

            health.details = {
                "cache_tiers": list(cache_metrics.keys()),
                "edge_metrics": edge_metrics,
                "test_result": {"set": set_success, "get": retrieved is not None},
            }

            await cache.close()

        except Exception as e:
            logger.error(f"Edge cache health check failed: {e}")
            health.status = HealthStatus.UNHEALTHY
            health.message = f"Check failed: {str(e)}"

        health.latency_ms = (time.time() - start_time) * 1000
        return health

    async def check_websocket_cluster(self) -> ComponentHealth:
        """Check WebSocket cluster status"""
        health = ComponentHealth("websocket_cluster")
        start_time = time.time()

        try:
            cluster = get_websocket_cluster()

            if not cluster:
                health.status = HealthStatus.UNHEALTHY
                health.message = "WebSocket cluster not initialized"
                return health

            # Get cluster metrics
            metrics = cluster.get_metrics()

            # Check node state
            from apps.backend.core.websocket_cluster import NodeState

            if cluster.node_state == NodeState.HEALTHY:
                health.status = HealthStatus.HEALTHY
                health.message = f"Node healthy with {metrics['connections']} connections"
            elif cluster.node_state == NodeState.DRAINING:
                health.status = HealthStatus.DEGRADED
                health.message = "Node is draining connections"
            else:
                health.status = HealthStatus.UNHEALTHY
                health.message = f"Node state: {cluster.node_state.value}"

            # Check cluster health
            if metrics["healthy_nodes"] == 0:
                health.status = HealthStatus.CRITICAL
                health.message = "No healthy nodes in cluster"
            elif metrics["healthy_nodes"] < metrics["cluster_nodes"] / 2:
                health.status = HealthStatus.DEGRADED
                health.message = (
                    f"Only {metrics['healthy_nodes']}/{metrics['cluster_nodes']} nodes healthy"
                )

            health.details = metrics

        except Exception as e:
            logger.error(f"WebSocket cluster health check failed: {e}")
            health.status = HealthStatus.UNHEALTHY
            health.message = f"Check failed: {str(e)}"

        health.latency_ms = (time.time() - start_time) * 1000
        return health

    async def check_global_load_balancer(self) -> ComponentHealth:
        """Check global load balancer health"""
        health = ComponentHealth("global_load_balancer")
        start_time = time.time()

        try:
            # This would check actual global LB instance
            # For now, simulate health check

            # Check if we can reach different regions
            regions_checked = []
            healthy_regions = []

            test_endpoints = [
                ("us-east-1.example.com", "US East"),
                ("eu-west-1.example.com", "EU West"),
                ("ap-south-1.example.com", "AP South"),
            ]

            async with httpx.AsyncClient(timeout=5.0) as client:
                for endpoint, region in test_endpoints:
                    try:
                        # Try to reach health endpoint
                        response = await client.head(f"https://{endpoint}/health")
                        if response.status_code < 500:
                            healthy_regions.append(region)
                        regions_checked.append(region)
                    except Exception:
                        regions_checked.append(region)

            # Determine health
            if len(healthy_regions) == len(regions_checked):
                health.status = HealthStatus.HEALTHY
                health.message = "All regions reachable"
            elif len(healthy_regions) > 0:
                health.status = HealthStatus.DEGRADED
                health.message = f"{len(healthy_regions)}/{len(regions_checked)} regions healthy"
            else:
                health.status = HealthStatus.CRITICAL
                health.message = "No regions reachable"

            health.details = {
                "regions_checked": regions_checked,
                "healthy_regions": healthy_regions,
                "unhealthy_count": len(regions_checked) - len(healthy_regions),
            }

        except Exception as e:
            logger.error(f"Global load balancer health check failed: {e}")
            health.status = HealthStatus.UNHEALTHY
            health.message = f"Check failed: {str(e)}"

        health.latency_ms = (time.time() - start_time) * 1000
        return health

    async def check_all_components(self) -> dict[str, ComponentHealth]:
        """Run all health checks"""
        checks = [
            self.check_circuit_breakers(),
            self.check_rate_limiting(),
            self.check_database_replicas(),
            self.check_edge_cache(),
            self.check_websocket_cluster(),
            self.check_global_load_balancer(),
        ]

        results = await asyncio.gather(*checks, return_exceptions=True)

        health_results = {}
        for result in results:
            if isinstance(result, ComponentHealth):
                health_results[result.name] = result
            elif isinstance(result, Exception):
                # Create error health result
                error_health = ComponentHealth("unknown")
                error_health.status = HealthStatus.UNHEALTHY
                error_health.message = f"Health check error: {str(result)}"
                health_results["error"] = error_health

        return health_results

    def calculate_overall_health(
        self, component_health: dict[str, ComponentHealth]
    ) -> tuple[HealthStatus, str]:
        """Calculate overall system health from component health"""

        statuses = [h.status for h in component_health.values()]

        if any(s == HealthStatus.CRITICAL for s in statuses):
            return HealthStatus.CRITICAL, "Critical components failing"
        elif any(s == HealthStatus.UNHEALTHY for s in statuses):
            return HealthStatus.UNHEALTHY, "Some components unhealthy"
        elif any(s == HealthStatus.DEGRADED for s in statuses):
            return HealthStatus.DEGRADED, "Some components degraded"
        else:
            return HealthStatus.HEALTHY, "All components healthy"


# Global health checker instance
_health_checker: LoadBalancingHealthChecker | None = None


async def get_health_checker() -> LoadBalancingHealthChecker:
    """Get or create health checker instance"""
    global _health_checker
    if not _health_checker:
        _health_checker = LoadBalancingHealthChecker()
        await _health_checker.initialize()
    return _health_checker


# API Endpoints


@router.get("/status")
async def get_overall_status(
    detailed: bool = False, health_checker: LoadBalancingHealthChecker = Depends(get_health_checker)
):
    """Get overall load balancing health status"""

    # Run all health checks
    component_health = await health_checker.check_all_components()

    # Calculate overall health
    overall_status, overall_message = health_checker.calculate_overall_health(component_health)

    response = {
        "status": overall_status.value,
        "message": overall_message,
        "timestamp": datetime.utcnow().isoformat(),
        "components": {
            name: {"status": health.status.value, "message": health.message}
            for name, health in component_health.items()
        },
    }

    if detailed:
        response["details"] = {name: health.to_dict() for name, health in component_health.items()}

    # Set appropriate HTTP status code
    if overall_status == HealthStatus.CRITICAL:
        return JSONResponse(response, status_code=503)
    elif overall_status == HealthStatus.UNHEALTHY:
        return JSONResponse(response, status_code=500)
    elif overall_status == HealthStatus.DEGRADED:
        return JSONResponse(response, status_code=200)
    else:
        return response


@router.get("/circuit-breakers")
async def get_circuit_breaker_health(
    health_checker: LoadBalancingHealthChecker = Depends(get_health_checker),
):
    """Get circuit breaker health status"""
    health = await health_checker.check_circuit_breakers()
    return health.to_dict()


@router.get("/rate-limiting")
async def get_rate_limiting_health(
    health_checker: LoadBalancingHealthChecker = Depends(get_health_checker),
):
    """Get rate limiting health status"""
    health = await health_checker.check_rate_limiting()
    return health.to_dict()


@router.get("/database-replicas")
async def get_database_replica_health(
    health_checker: LoadBalancingHealthChecker = Depends(get_health_checker),
):
    """Get database replica health status"""
    health = await health_checker.check_database_replicas()
    return health.to_dict()


@router.get("/edge-cache")
async def get_edge_cache_health(
    health_checker: LoadBalancingHealthChecker = Depends(get_health_checker),
):
    """Get edge cache health status"""
    health = await health_checker.check_edge_cache()
    return health.to_dict()


@router.get("/websocket-cluster")
async def get_websocket_cluster_health(
    health_checker: LoadBalancingHealthChecker = Depends(get_health_checker),
):
    """Get WebSocket cluster health status"""
    health = await health_checker.check_websocket_cluster()
    return health.to_dict()


@router.get("/global-lb")
async def get_global_lb_health(
    health_checker: LoadBalancingHealthChecker = Depends(get_health_checker),
):
    """Get global load balancer health status"""
    health = await health_checker.check_global_load_balancer()
    return health.to_dict()


@router.post("/test-failover")
async def test_failover_scenario(
    component: str, health_checker: LoadBalancingHealthChecker = Depends(get_health_checker)
):
    """Test failover scenario for a component"""

    # This would trigger actual failover testing
    # For safety, this requires additional authentication

    return {
        "message": f"Failover test for {component} would be triggered",
        "note": "This endpoint requires additional authentication in production",
    }


@router.get("/metrics")
async def get_load_balancing_metrics():
    """Get detailed metrics for all load balancing components"""

    metrics = {}

    # Circuit breaker metrics
    for name in ["database", "api", "external_service", "redis"]:
        breaker = get_circuit_breaker(name)
        if breaker:
            metrics[f"circuit_breaker_{name}"] = breaker.get_status()

    # Replica router metrics
    router = get_replica_router()
    if router:
        metrics["replica_routing"] = router.get_metrics()

    # WebSocket cluster metrics
    cluster = get_websocket_cluster()
    if cluster:
        metrics["websocket_cluster"] = cluster.get_metrics()

    # Add timestamp
    metrics["timestamp"] = datetime.utcnow().isoformat()

    return metrics


# Liveness probe for Kubernetes
@router.get("/live")
async def liveness_probe():
    """Simple liveness probe"""
    return {"status": "alive"}


# Readiness probe for Kubernetes
@router.get("/ready")
async def readiness_probe(health_checker: LoadBalancingHealthChecker = Depends(get_health_checker)):
    """Readiness probe that checks critical components"""

    # Check only critical components for readiness
    critical_checks = await asyncio.gather(
        health_checker.check_database_replicas(),
        health_checker.check_circuit_breakers(),
        return_exceptions=True,
    )

    for check in critical_checks:
        if isinstance(check, Exception):
            return JSONResponse({"status": "not_ready", "error": str(check)}, status_code=503)
        elif isinstance(check, ComponentHealth):
            if check.status in [HealthStatus.CRITICAL, HealthStatus.UNHEALTHY]:
                return JSONResponse(
                    {"status": "not_ready", "component": check.name}, status_code=503
                )

    return {"status": "ready"}
