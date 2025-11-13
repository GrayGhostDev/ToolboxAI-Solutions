"""
Global Server Load Balancing

Provides intelligent global traffic distribution with:
- Geographic routing based on user location
- Multi-region health monitoring
- Automatic failover between regions
- Traffic shaping and distribution
- Cost optimization routing
"""

import asyncio
import json
import logging
import math
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum

import aiodns
import geoip2.database
import geoip2.errors
import httpx

logger = logging.getLogger(__name__)


class RoutingPolicy(Enum):
    """Traffic routing policies"""

    GEOPROXIMITY = "geoproximity"  # Route to nearest location
    WEIGHTED = "weighted"  # Distribute by weights
    LATENCY = "latency"  # Route to lowest latency
    COST = "cost"  # Optimize for cost
    FAILOVER = "failover"  # Primary/backup routing
    MULTIVALUE = "multivalue"  # Return multiple endpoints


class HealthCheckType(Enum):
    """Health check types"""

    HTTP = "http"
    HTTPS = "https"
    TCP = "tcp"
    CALCULATED = "calculated"  # Based on child checks


class RegionCode(Enum):
    """Cloud provider region codes"""

    # AWS Regions
    US_EAST_1 = "us-east-1"  # N. Virginia
    US_WEST_1 = "us-west-1"  # N. California
    US_WEST_2 = "us-west-2"  # Oregon
    EU_WEST_1 = "eu-west-1"  # Ireland
    EU_CENTRAL_1 = "eu-central-1"  # Frankfurt
    AP_SOUTHEAST_1 = "ap-southeast-1"  # Singapore
    AP_NORTHEAST_1 = "ap-northeast-1"  # Tokyo
    AP_SOUTH_1 = "ap-south-1"  # Mumbai


@dataclass
class HealthCheck:
    """Health check configuration"""

    endpoint: str
    type: HealthCheckType
    interval: int = 30
    timeout: int = 5
    failure_threshold: int = 3
    success_threshold: int = 2
    path: str = "/health"
    port: int = 443
    protocol: str = "https"


@dataclass
class EndpointHealth:
    """Health status of an endpoint"""

    endpoint: str
    region: RegionCode
    healthy: bool = True
    latency_ms: float = 0
    last_check: datetime = field(default_factory=datetime.utcnow)
    consecutive_failures: int = 0
    consecutive_successes: int = 0
    availability: float = 100.0  # Percentage
    response_times: list[float] = field(default_factory=list)


@dataclass
class TrafficPolicy:
    """Traffic distribution policy"""

    policy_type: RoutingPolicy
    endpoints: list[str]
    weights: dict[str, int] | None = None
    failover_order: list[str] | None = None
    cost_per_request: dict[str, float] | None = None
    max_endpoints: int = 4


@dataclass
class GeographicLocation:
    """Geographic coordinates"""

    latitude: float
    longitude: float
    city: str | None = None
    country: str | None = None
    continent: str | None = None


@dataclass
class Region:
    """Represents a deployment region"""

    code: RegionCode
    name: str
    location: GeographicLocation
    endpoints: list[str]
    capacity: int  # Max requests per second
    current_load: int = 0
    cost_per_million: float = 1.0  # Cost per million requests
    active: bool = True


@dataclass
class GlobalMetrics:
    """Global load balancer metrics"""

    total_requests: int = 0
    requests_by_region: dict[str, int] = field(default_factory=dict)
    average_latency_ms: float = 0
    failovers: int = 0
    errors: int = 0
    cache_hits: int = 0
    bandwidth_gb: float = 0
    estimated_cost: float = 0


class GeoIPResolver:
    """Resolves IP addresses to geographic locations"""

    def __init__(self, database_path: str = "/usr/share/GeoIP/GeoLite2-City.mmdb"):
        try:
            self.reader = geoip2.database.Reader(database_path)
        except Exception as e:
            logger.warning("GeoIP database not available: %s", e)
            self.reader = None

    def get_location(self, ip: str) -> GeographicLocation | None:
        """Get geographic location for IP address"""
        if not self.reader:
            return None

        try:
            response = self.reader.city(ip)
            return GeographicLocation(
                latitude=response.location.latitude,
                longitude=response.location.longitude,
                city=response.city.name,
                country=response.country.iso_code,
                continent=response.continent.code,
            )
        except geoip2.errors.AddressNotFoundError:
            return None
        except Exception as e:
            logger.error("GeoIP lookup error: %s", e)
            return None

    def close(self):
        """Close GeoIP database"""
        if self.reader:
            self.reader.close()


class LatencyProber:
    """Probes endpoint latency from different locations"""

    @staticmethod
    async def measure_latency(endpoint: str, timeout: int = 5) -> float:
        """Measure latency to endpoint in milliseconds"""
        try:
            start = time.time()
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.head(f"https://{endpoint}/health")
                if response.status_code < 500:
                    return (time.time() - start) * 1000
        except Exception:
            pass
        return float("inf")

    @staticmethod
    async def measure_all(endpoints: list[str]) -> dict[str, float]:
        """Measure latency to all endpoints"""
        tasks = [LatencyProber.measure_latency(endpoint) for endpoint in endpoints]
        results = await asyncio.gather(*tasks)
        return dict(zip(endpoints, results))


class GlobalLoadBalancer:
    """Global server load balancing system"""

    def __init__(
        self,
        regions: list[Region],
        policy: TrafficPolicy,
        health_check_config: HealthCheck,
        enable_geo_routing: bool = True,
        enable_health_checks: bool = True,
        dns_ttl: int = 60,
    ):
        self.regions = {r.code: r for r in regions}
        self.policy = policy
        self.health_check_config = health_check_config
        self.enable_geo_routing = enable_geo_routing
        self.enable_health_checks = enable_health_checks
        self.dns_ttl = dns_ttl

        # Health tracking
        self.endpoint_health: dict[str, EndpointHealth] = {}
        for region in regions:
            for endpoint in region.endpoints:
                self.endpoint_health[endpoint] = EndpointHealth(
                    endpoint=endpoint, region=region.code
                )

        # GeoIP resolver
        self.geoip = GeoIPResolver() if enable_geo_routing else None

        # Latency prober
        self.prober = LatencyProber()

        # Metrics
        self.metrics = GlobalMetrics()

        # DNS resolver for custom logic
        self.dns_resolver = aiodns.DNSResolver()

        # Background tasks
        self.tasks: list[asyncio.Task] = []

        # Routing cache
        self.routing_cache: dict[str, tuple[list[str], datetime]] = {}
        self.cache_ttl = 60  # seconds

    async def start(self):
        """Start the global load balancer"""
        logger.info("Starting global load balancer with %d regions", len(self.regions))

        if self.enable_health_checks:
            self.tasks.append(asyncio.create_task(self._health_check_loop()))

        self.tasks.append(asyncio.create_task(self._metrics_collector()))

        self.tasks.append(asyncio.create_task(self._capacity_manager()))

        logger.info("Global load balancer started")

    async def stop(self):
        """Stop the global load balancer"""
        for task in self.tasks:
            task.cancel()
        await asyncio.gather(*self.tasks, return_exceptions=True)

        if self.geoip:
            self.geoip.close()

        logger.info("Global load balancer stopped")

    async def route(self, client_ip: str, path: str = "/", method: str = "GET") -> list[str]:
        """Route request to optimal endpoints"""
        start_time = time.time()

        # Check routing cache
        cache_key = f"{client_ip}:{path}:{method}"
        if cache_key in self.routing_cache:
            cached_endpoints, cached_time = self.routing_cache[cache_key]
            if datetime.utcnow() - cached_time < timedelta(seconds=self.cache_ttl):
                self.metrics.cache_hits += 1
                return cached_endpoints

        # Get client location if geo-routing enabled
        client_location = None
        if self.enable_geo_routing and self.geoip:
            client_location = self.geoip.get_location(client_ip)

        # Get healthy endpoints
        healthy_endpoints = self._get_healthy_endpoints()
        if not healthy_endpoints:
            logger.error("No healthy endpoints available")
            self.metrics.errors += 1
            return []

        # Apply routing policy
        selected_endpoints = await self._apply_routing_policy(healthy_endpoints, client_location)

        # Cache routing decision
        self.routing_cache[cache_key] = (selected_endpoints, datetime.utcnow())

        # Clean old cache entries periodically
        if len(self.routing_cache) > 10000:
            self._clean_routing_cache()

        # Update metrics
        self.metrics.total_requests += 1
        routing_time = (time.time() - start_time) * 1000
        self._update_average_latency(routing_time)

        # Track requests by region
        for endpoint in selected_endpoints[:1]:  # Count primary endpoint
            region = self._get_endpoint_region(endpoint)
            if region:
                if region.value not in self.metrics.requests_by_region:
                    self.metrics.requests_by_region[region.value] = 0
                self.metrics.requests_by_region[region.value] += 1

        return selected_endpoints

    def _get_healthy_endpoints(self) -> list[str]:
        """Get list of healthy endpoints"""
        return [endpoint for endpoint, health in self.endpoint_health.items() if health.healthy]

    def _get_endpoint_region(self, endpoint: str) -> RegionCode | None:
        """Get region for an endpoint"""
        for health in self.endpoint_health.values():
            if health.endpoint == endpoint:
                return health.region
        return None

    async def _apply_routing_policy(
        self, endpoints: list[str], client_location: GeographicLocation | None
    ) -> list[str]:
        """Apply routing policy to select endpoints"""

        if self.policy.policy_type == RoutingPolicy.GEOPROXIMITY:
            return await self._route_geoproximity(endpoints, client_location)

        elif self.policy.policy_type == RoutingPolicy.LATENCY:
            return await self._route_latency(endpoints)

        elif self.policy.policy_type == RoutingPolicy.WEIGHTED:
            return self._route_weighted(endpoints)

        elif self.policy.policy_type == RoutingPolicy.COST:
            return self._route_cost_optimized(endpoints)

        elif self.policy.policy_type == RoutingPolicy.FAILOVER:
            return self._route_failover(endpoints)

        elif self.policy.policy_type == RoutingPolicy.MULTIVALUE:
            return endpoints[: self.policy.max_endpoints]

        return endpoints[:1]  # Default to first endpoint

    async def _route_geoproximity(
        self, endpoints: list[str], client_location: GeographicLocation | None
    ) -> list[str]:
        """Route based on geographic proximity"""
        if not client_location:
            # Fallback to latency-based routing
            return await self._route_latency(endpoints)

        # Calculate distances to all regions
        distances = {}
        for endpoint in endpoints:
            region_code = self._get_endpoint_region(endpoint)
            if region_code and region_code in self.regions:
                region = self.regions[region_code]
                distance = self._calculate_distance(
                    client_location.latitude,
                    client_location.longitude,
                    region.location.latitude,
                    region.location.longitude,
                )
                distances[endpoint] = distance

        # Sort by distance
        sorted_endpoints = sorted(endpoints, key=lambda e: distances.get(e, float("inf")))

        # Return closest endpoints
        return sorted_endpoints[: self.policy.max_endpoints]

    async def _route_latency(self, endpoints: list[str]) -> list[str]:
        """Route based on measured latency"""
        # Measure latency to all endpoints
        latencies = await self.prober.measure_all(endpoints)

        # Sort by latency
        sorted_endpoints = sorted(endpoints, key=lambda e: latencies.get(e, float("inf")))

        # Return lowest latency endpoints
        return sorted_endpoints[: self.policy.max_endpoints]

    def _route_weighted(self, endpoints: list[str]) -> list[str]:
        """Route based on configured weights"""
        if not self.policy.weights:
            return endpoints[: self.policy.max_endpoints]

        # Sort by weight
        sorted_endpoints = sorted(
            endpoints, key=lambda e: self.policy.weights.get(e, 1), reverse=True
        )

        # Apply weighted random selection
        import random

        weighted_endpoints = []
        remaining = list(sorted_endpoints)

        for _ in range(min(self.policy.max_endpoints, len(endpoints))):
            if not remaining:
                break

            weights = [self.policy.weights.get(e, 1) for e in remaining]
            selected = random.choices(remaining, weights=weights)[0]
            weighted_endpoints.append(selected)
            remaining.remove(selected)

        return weighted_endpoints

    def _route_cost_optimized(self, endpoints: list[str]) -> list[str]:
        """Route to minimize cost while maintaining performance"""
        if not self.policy.cost_per_request:
            return endpoints[: self.policy.max_endpoints]

        # Calculate cost-performance score
        scores = {}
        for endpoint in endpoints:
            cost = self.policy.cost_per_request.get(endpoint, 1.0)
            health = self.endpoint_health[endpoint]

            # Lower score is better (cost / availability)
            if health.availability > 0:
                scores[endpoint] = cost / (health.availability / 100)
            else:
                scores[endpoint] = float("inf")

        # Sort by cost-performance score
        sorted_endpoints = sorted(endpoints, key=lambda e: scores.get(e, float("inf")))

        return sorted_endpoints[: self.policy.max_endpoints]

    def _route_failover(self, endpoints: list[str]) -> list[str]:
        """Route with failover priority"""
        if not self.policy.failover_order:
            return endpoints[:1]

        # Return first healthy endpoint in failover order
        for primary in self.policy.failover_order:
            if primary in endpoints:
                return [primary]

        # All primaries failed, return any healthy endpoint
        return endpoints[:1] if endpoints else []

    def _calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance between two points using Haversine formula"""
        R = 6371  # Earth's radius in kilometers

        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = (
            math.sin(dlat / 2) ** 2
            + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
        )
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        return R * c

    async def _health_check_loop(self):
        """Continuously monitor endpoint health"""
        while True:
            try:
                tasks = [self._check_endpoint_health(endpoint) for endpoint in self.endpoint_health]
                await asyncio.gather(*tasks, return_exceptions=True)
                await asyncio.sleep(self.health_check_config.interval)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Health check loop error: %s", e)
                await asyncio.sleep(10)

    async def _check_endpoint_health(self, endpoint: str):
        """Check health of a specific endpoint"""
        health = self.endpoint_health[endpoint]

        try:
            # Perform health check
            url = f"{self.health_check_config.protocol}://{endpoint}{self.health_check_config.path}"
            timeout = httpx.Timeout(self.health_check_config.timeout)

            start_time = time.time()
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.get(url)
                latency = (time.time() - start_time) * 1000

            # Check response
            if response.status_code < 500:
                # Success
                health.consecutive_successes += 1
                health.consecutive_failures = 0
                health.latency_ms = latency
                health.response_times.append(latency)

                # Keep only last 100 response times
                if len(health.response_times) > 100:
                    health.response_times = health.response_times[-100:]

                # Mark healthy after threshold successes
                if health.consecutive_successes >= self.health_check_config.success_threshold:
                    if not health.healthy:
                        logger.info("Endpoint %s marked healthy", endpoint)
                    health.healthy = True

                # Update availability (rolling average)
                health.availability = min(100.0, health.availability * 0.99 + 1.0)

            else:
                # Failure
                raise Exception(f"HTTP {response.status_code}")

        except Exception as e:
            # Health check failed
            health.consecutive_failures += 1
            health.consecutive_successes = 0

            # Mark unhealthy after threshold failures
            if health.consecutive_failures >= self.health_check_config.failure_threshold:
                if health.healthy:
                    logger.warning("Endpoint %s marked unhealthy: %s", endpoint, e)
                    self.metrics.failovers += 1
                health.healthy = False

            # Update availability
            health.availability = max(0.0, health.availability * 0.99)

        health.last_check = datetime.utcnow()

    async def _capacity_manager(self):
        """Manage regional capacity and auto-scaling"""
        while True:
            try:
                for region_code, region in self.regions.items():
                    # Calculate current load percentage
                    load_percentage = (
                        region.current_load / region.capacity * 100 if region.capacity > 0 else 0
                    )

                    # Auto-scaling logic
                    if load_percentage > 80:
                        logger.warning(
                            "Region %s at %.1f%% capacity", region_code.value, load_percentage
                        )
                        # Trigger scale-up (would integrate with cloud provider APIs)

                    elif load_percentage < 20 and len(region.endpoints) > 1:
                        logger.info(
                            "Region %s underutilized at %.1f%%", region_code.value, load_percentage
                        )
                        # Consider scale-down

                    # Update regional metrics
                    region.current_load = 0  # Reset for next interval

                await asyncio.sleep(60)  # Check every minute

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Capacity manager error: %s", e)
                await asyncio.sleep(10)

    async def _metrics_collector(self):
        """Collect and log metrics"""
        while True:
            try:
                # Calculate overall health
                healthy_count = sum(1 for h in self.endpoint_health.values() if h.healthy)
                total_count = len(self.endpoint_health)
                health_percentage = healthy_count / total_count * 100 if total_count > 0 else 0

                # Calculate average availability
                avg_availability = (
                    sum(h.availability for h in self.endpoint_health.values()) / total_count
                    if total_count > 0
                    else 0
                )

                # Estimate cost
                total_requests = self.metrics.total_requests
                self.metrics.estimated_cost = sum(
                    (count / 1_000_000)
                    * self.regions.get(
                        RegionCode(region),
                        Region(
                            code=RegionCode.US_EAST_1,
                            name="Unknown",
                            location=GeographicLocation(0, 0),
                            endpoints=[],
                            capacity=0,
                            cost_per_million=1.0,
                        ),
                    ).cost_per_million
                    for region, count in self.metrics.requests_by_region.items()
                )

                logger.info(
                    "Global LB metrics: requests=%d, healthy=%.1f%%, "
                    "availability=%.1f%%, latency=%.1fms, cost=$%.2f",
                    total_requests,
                    health_percentage,
                    avg_availability,
                    self.metrics.average_latency_ms,
                    self.metrics.estimated_cost,
                )

                # Log regional distribution
                if self.metrics.requests_by_region:
                    logger.info(
                        "Regional distribution: %s", json.dumps(self.metrics.requests_by_region)
                    )

                await asyncio.sleep(60)  # Log every minute

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Metrics collector error: %s", e)
                await asyncio.sleep(10)

    def _update_average_latency(self, latency_ms: float):
        """Update average latency metric"""
        total = self.metrics.total_requests
        if total > 0:
            self.metrics.average_latency_ms = (
                self.metrics.average_latency_ms * (total - 1) + latency_ms
            ) / total

    def _clean_routing_cache(self):
        """Clean expired entries from routing cache"""
        now = datetime.utcnow()
        expired_keys = [
            key
            for key, (_, cached_time) in self.routing_cache.items()
            if now - cached_time > timedelta(seconds=self.cache_ttl * 2)
        ]
        for key in expired_keys:
            del self.routing_cache[key]

    async def trigger_failover(self, failed_region: RegionCode):
        """Manually trigger failover from a region"""
        logger.warning("Manual failover triggered for region %s", failed_region.value)

        # Mark all endpoints in region as unhealthy
        for endpoint, health in self.endpoint_health.items():
            if health.region == failed_region:
                health.healthy = False
                health.consecutive_failures = self.health_check_config.failure_threshold

        self.metrics.failovers += 1

        # Clear routing cache to force re-evaluation
        self.routing_cache.clear()

    def get_metrics(self) -> dict:
        """Get global load balancer metrics"""
        return {
            "total_requests": self.metrics.total_requests,
            "requests_by_region": self.metrics.requests_by_region,
            "average_latency_ms": self.metrics.average_latency_ms,
            "failovers": self.metrics.failovers,
            "errors": self.metrics.errors,
            "cache_hits": self.metrics.cache_hits,
            "cache_hit_rate": (
                self.metrics.cache_hits / self.metrics.total_requests * 100
                if self.metrics.total_requests > 0
                else 0
            ),
            "estimated_cost": self.metrics.estimated_cost,
            "endpoint_health": {
                endpoint: {
                    "healthy": health.healthy,
                    "latency_ms": health.latency_ms,
                    "availability": health.availability,
                    "region": health.region.value,
                }
                for endpoint, health in self.endpoint_health.items()
            },
            "healthy_endpoints": sum(1 for h in self.endpoint_health.values() if h.healthy),
            "total_endpoints": len(self.endpoint_health),
        }


# Example DNS integration for Route53-style routing
class DNSRouter:
    """DNS-based global routing (for Route53/Cloud DNS integration)"""

    def __init__(self, load_balancer: GlobalLoadBalancer):
        self.load_balancer = load_balancer

    async def resolve(self, hostname: str, client_ip: str) -> list[str]:
        """Resolve hostname to IP addresses based on routing policy"""
        # Get optimal endpoints for client
        endpoints = await self.load_balancer.route(client_ip)

        # Resolve endpoints to IP addresses
        ips = []
        for endpoint in endpoints:
            try:
                # Resolve endpoint hostname to IP
                result = await self.load_balancer.dns_resolver.query(endpoint, "A")
                for rdata in result:
                    ips.append(rdata.address)
            except Exception as e:
                logger.error("DNS resolution failed for %s: %s", endpoint, e)

        return ips

    def generate_dns_response(self, query: str, client_ip: str) -> dict:
        """Generate DNS response for query"""
        # This would integrate with actual DNS server
        # Example response format for Route53
        return {
            "Name": query,
            "Type": "A",
            "SetIdentifier": "Dynamic",
            "TTL": self.load_balancer.dns_ttl,
            "ResourceRecords": [
                {"Value": ip} for ip in asyncio.run(self.resolve(query, client_ip))
            ],
        }
