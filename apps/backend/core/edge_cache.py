"""
Edge Caching with CDN Integration

Provides intelligent edge caching with:
- Multi-tier caching (edge, regional, origin)
- Smart cache invalidation
- Cache warming and preloading
- Geographic routing optimization
- CDN provider abstraction
"""

import asyncio
import hashlib
import json
import time
from enum import Enum
from typing import Dict, List, Optional, Set, Any, Callable, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import logging
from functools import wraps

import httpx
import redis.asyncio as aioredis
from fastapi import Request, Response, HTTPException
from fastapi.responses import StreamingResponse
import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


class CacheTier(Enum):
    """Cache tier levels"""

    EDGE = "edge"  # CDN edge locations
    REGIONAL = "regional"  # Regional cache clusters
    ORIGIN = "origin"  # Origin server cache


class CacheStrategy(Enum):
    """Caching strategies"""

    CACHE_FIRST = "cache_first"  # Try cache first, fallback to origin
    CACHE_ONLY = "cache_only"  # Only serve from cache, error if miss
    NETWORK_FIRST = "network_first"  # Try origin first, cache response
    NETWORK_ONLY = "network_only"  # Always fetch from origin
    STALE_WHILE_REVALIDATE = "stale_while_revalidate"  # Serve stale, update async


class InvalidationScope(Enum):
    """Cache invalidation scopes"""

    EXACT = "exact"  # Invalidate exact key
    PREFIX = "prefix"  # Invalidate all keys with prefix
    TAG = "tag"  # Invalidate all keys with tag
    PATTERN = "pattern"  # Invalidate keys matching pattern
    GLOBAL = "global"  # Invalidate everything


@dataclass
class CacheConfig:
    """Cache configuration"""

    ttl_seconds: int = 3600
    max_age: int = 3600
    s_maxage: int = 86400  # Shared cache max age
    stale_while_revalidate: int = 60
    stale_if_error: int = 86400
    vary_headers: List[str] = field(default_factory=lambda: ["Accept", "Accept-Encoding"])
    cache_control_directives: List[str] = field(default_factory=list)
    surrogate_keys: List[str] = field(default_factory=list)
    edge_ttl: Optional[int] = None
    browser_ttl: Optional[int] = None


@dataclass
class CacheEntry:
    """Represents a cached item"""

    key: str
    value: bytes
    content_type: str
    headers: Dict[str, str]
    created_at: datetime
    expires_at: datetime
    etag: str
    tags: Set[str] = field(default_factory=set)
    hit_count: int = 0
    last_accessed: datetime = field(default_factory=datetime.utcnow)
    compressed: bool = False
    size_bytes: int = 0


@dataclass
class CacheMetrics:
    """Cache performance metrics"""

    hits: int = 0
    misses: int = 0
    evictions: int = 0
    invalidations: int = 0
    bytes_served: int = 0
    bytes_stored: int = 0
    average_latency_ms: float = 0.0
    error_count: int = 0


class CDNProvider:
    """Base class for CDN providers"""

    async def purge(self, urls: List[str]):
        """Purge URLs from CDN cache"""
        raise NotImplementedError

    async def warm(self, urls: List[str]):
        """Pre-warm CDN cache with URLs"""
        raise NotImplementedError

    async def get_metrics(self) -> dict:
        """Get CDN metrics"""
        raise NotImplementedError


class CloudflareCDN(CDNProvider):
    """Cloudflare CDN integration"""

    def __init__(self, zone_id: str, api_token: str):
        self.zone_id = zone_id
        self.api_token = api_token
        self.base_url = f"https://api.cloudflare.com/client/v4/zones/{zone_id}"
        self.headers = {"Authorization": f"Bearer {api_token}", "Content-Type": "application/json"}

    async def purge(self, urls: List[str]):
        """Purge URLs from Cloudflare cache"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/purge_cache", headers=self.headers, json={"files": urls}
            )
            response.raise_for_status()
            return response.json()

    async def warm(self, urls: List[str]):
        """Pre-warm Cloudflare cache"""
        async with httpx.AsyncClient() as client:
            tasks = [client.get(url, headers={"CF-Cache-Warmup": "1"}) for url in urls]
            await asyncio.gather(*tasks, return_exceptions=True)

    async def get_metrics(self) -> dict:
        """Get Cloudflare analytics"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/analytics/dashboard", headers=self.headers
            )
            response.raise_for_status()
            return response.json()


class CloudFrontCDN(CDNProvider):
    """AWS CloudFront CDN integration"""

    def __init__(self, distribution_id: str, aws_access_key: str, aws_secret_key: str):
        self.distribution_id = distribution_id
        self.client = boto3.client(
            "cloudfront", aws_access_key_id=aws_access_key, aws_secret_access_key=aws_secret_key
        )

    async def purge(self, urls: List[str]):
        """Create CloudFront invalidation"""
        try:
            response = self.client.create_invalidation(
                DistributionId=self.distribution_id,
                InvalidationBatch={
                    "Paths": {"Quantity": len(urls), "Items": urls},
                    "CallerReference": str(time.time()),
                },
            )
            return response["Invalidation"]
        except ClientError as e:
            logger.error("CloudFront invalidation failed: %s", e)
            raise

    async def warm(self, urls: List[str]):
        """Pre-warm CloudFront cache"""
        async with httpx.AsyncClient() as client:
            tasks = [client.get(url, headers={"X-Cache-Warmup": "1"}) for url in urls]
            await asyncio.gather(*tasks, return_exceptions=True)

    async def get_metrics(self) -> dict:
        """Get CloudFront metrics from CloudWatch"""
        cloudwatch = boto3.client("cloudwatch")
        try:
            response = cloudwatch.get_metric_statistics(
                Namespace="AWS/CloudFront",
                MetricName="Requests",
                Dimensions=[{"Name": "DistributionId", "Value": self.distribution_id}],
                StartTime=datetime.utcnow() - timedelta(hours=1),
                EndTime=datetime.utcnow(),
                Period=300,
                Statistics=["Sum", "Average"],
            )
            return response
        except ClientError as e:
            logger.error("CloudFront metrics failed: %s", e)
            return {}


class EdgeCache:
    """Multi-tier edge caching system"""

    def __init__(
        self,
        redis_url: str,
        cdn_provider: Optional[CDNProvider] = None,
        default_ttl: int = 3600,
        max_cache_size_mb: int = 1024,
        enable_compression: bool = True,
    ):
        self.redis_url = redis_url
        self.cdn_provider = cdn_provider
        self.default_ttl = default_ttl
        self.max_cache_size = max_cache_size_mb * 1024 * 1024  # Convert to bytes
        self.enable_compression = enable_compression

        # Redis clients for different tiers
        self.redis_clients: Dict[CacheTier, aioredis.Redis] = {}

        # Cache metrics per tier
        self.metrics: Dict[CacheTier, CacheMetrics] = {tier: CacheMetrics() for tier in CacheTier}

        # Cache key patterns
        self.key_patterns: Dict[str, str] = {}

        # Background tasks
        self.tasks: List[asyncio.Task] = []

    async def initialize(self):
        """Initialize cache system"""
        # Create Redis clients for each tier (could be different instances)
        for tier in CacheTier:
            db_num = list(CacheTier).index(tier)
            self.redis_clients[tier] = await aioredis.from_url(
                self.redis_url, db=db_num, encoding="utf-8", decode_responses=False
            )

        # Start background tasks
        self.tasks = [
            asyncio.create_task(self._metrics_collector()),
            asyncio.create_task(self._cache_warmer()),
            asyncio.create_task(self._eviction_manager()),
        ]

        logger.info("Edge cache system initialized")

    async def close(self):
        """Close cache connections"""
        for task in self.tasks:
            task.cancel()
        await asyncio.gather(*self.tasks, return_exceptions=True)

        for client in self.redis_clients.values():
            await client.aclose()

    def _generate_cache_key(
        self, request: Request, vary_headers: Optional[List[str]] = None
    ) -> str:
        """Generate cache key from request"""
        # Base key from URL
        key_parts = [
            request.url.scheme,
            request.url.netloc,
            request.url.path,
            str(sorted(request.url.query or "")),
        ]

        # Add vary headers
        if vary_headers:
            for header in vary_headers:
                value = request.headers.get(header, "")
                key_parts.append(f"{header}:{value}")

        # Generate hash
        key_string = "|".join(key_parts)
        key_hash = hashlib.sha256(key_string.encode()).hexdigest()[:16]

        return f"cache:{request.url.path}:{key_hash}"

    def _generate_etag(self, content: bytes) -> str:
        """Generate ETag for content"""
        return f'"{hashlib.md5(content).hexdigest()}"'

    async def get(
        self,
        key: str,
        tier: CacheTier = CacheTier.EDGE,
        strategy: CacheStrategy = CacheStrategy.CACHE_FIRST,
    ) -> Optional[CacheEntry]:
        """Get item from cache"""
        start_time = time.time()

        try:
            # Try specified tier first
            data = await self.redis_clients[tier].get(key)

            if data:
                # Deserialize cache entry
                entry_dict = json.loads(data)
                entry = CacheEntry(
                    key=entry_dict["key"],
                    value=bytes.fromhex(entry_dict["value"]),
                    content_type=entry_dict["content_type"],
                    headers=entry_dict["headers"],
                    created_at=datetime.fromisoformat(entry_dict["created_at"]),
                    expires_at=datetime.fromisoformat(entry_dict["expires_at"]),
                    etag=entry_dict["etag"],
                    tags=set(entry_dict.get("tags", [])),
                    hit_count=entry_dict.get("hit_count", 0),
                    compressed=entry_dict.get("compressed", False),
                    size_bytes=entry_dict.get("size_bytes", 0),
                )

                # Check expiration
                if datetime.utcnow() > entry.expires_at:
                    if strategy == CacheStrategy.STALE_WHILE_REVALIDATE:
                        # Return stale content and trigger revalidation
                        asyncio.create_task(self._revalidate(key, tier))
                    else:
                        # Expired, remove from cache
                        await self.delete(key, tier)
                        self.metrics[tier].misses += 1
                        return None

                # Update metrics
                self.metrics[tier].hits += 1
                self.metrics[tier].bytes_served += entry.size_bytes

                # Update hit count and last accessed
                entry.hit_count += 1
                entry.last_accessed = datetime.utcnow()
                asyncio.create_task(self._update_stats(key, tier, entry))

                # Update latency metric
                latency = (time.time() - start_time) * 1000
                self._update_latency(tier, latency)

                return entry

            else:
                # Cache miss - try fallback tiers
                if tier == CacheTier.EDGE and strategy != CacheStrategy.CACHE_ONLY:
                    # Try regional cache
                    entry = await self.get(key, CacheTier.REGIONAL, strategy)
                    if entry:
                        # Promote to edge cache
                        await self.set(key, entry, CacheTier.EDGE)
                        return entry

                    # Try origin cache
                    entry = await self.get(key, CacheTier.ORIGIN, strategy)
                    if entry:
                        # Promote to edge and regional
                        await self.set(key, entry, CacheTier.EDGE)
                        await self.set(key, entry, CacheTier.REGIONAL)
                        return entry

                self.metrics[tier].misses += 1
                return None

        except Exception as e:
            logger.error("Cache get error for %s: %s", key, e)
            self.metrics[tier].error_count += 1
            return None

    async def set(
        self,
        key: str,
        entry: Union[CacheEntry, bytes],
        tier: CacheTier = CacheTier.EDGE,
        config: Optional[CacheConfig] = None,
    ) -> bool:
        """Set item in cache"""
        try:
            if isinstance(entry, bytes):
                # Create cache entry from bytes
                config = config or CacheConfig()
                entry = CacheEntry(
                    key=key,
                    value=entry,
                    content_type="application/octet-stream",
                    headers={},
                    created_at=datetime.utcnow(),
                    expires_at=datetime.utcnow() + timedelta(seconds=config.ttl_seconds),
                    etag=self._generate_etag(entry),
                    size_bytes=len(entry),
                )

            # Compress if enabled and beneficial
            if self.enable_compression and entry.size_bytes > 1024:
                import gzip

                compressed = gzip.compress(entry.value)
                if len(compressed) < entry.size_bytes * 0.9:  # At least 10% compression
                    entry.value = compressed
                    entry.compressed = True
                    entry.size_bytes = len(compressed)

            # Serialize entry
            entry_dict = {
                "key": entry.key,
                "value": entry.value.hex(),
                "content_type": entry.content_type,
                "headers": entry.headers,
                "created_at": entry.created_at.isoformat(),
                "expires_at": entry.expires_at.isoformat(),
                "etag": entry.etag,
                "tags": list(entry.tags),
                "hit_count": entry.hit_count,
                "compressed": entry.compressed,
                "size_bytes": entry.size_bytes,
            }

            # Calculate TTL
            ttl = int((entry.expires_at - datetime.utcnow()).total_seconds())
            if ttl <= 0:
                return False

            # Store in cache
            await self.redis_clients[tier].setex(key, ttl, json.dumps(entry_dict))

            # Update metrics
            self.metrics[tier].bytes_stored += entry.size_bytes

            # Store tags for invalidation
            if entry.tags:
                for tag in entry.tags:
                    await self.redis_clients[tier].sadd(f"tag:{tag}", key)
                    await self.redis_clients[tier].expire(f"tag:{tag}", ttl)

            return True

        except Exception as e:
            logger.error("Cache set error for %s: %s", key, e)
            self.metrics[tier].error_count += 1
            return False

    async def delete(self, key: str, tier: Optional[CacheTier] = None):
        """Delete item from cache"""
        tiers = [tier] if tier else list(CacheTier)

        for t in tiers:
            try:
                await self.redis_clients[t].delete(key)
                self.metrics[t].evictions += 1
            except Exception as e:
                logger.error("Cache delete error for %s in %s: %s", key, t, e)

    async def invalidate(
        self, scope: InvalidationScope, value: str, tier: Optional[CacheTier] = None
    ):
        """Invalidate cache entries"""
        tiers = [tier] if tier else list(CacheTier)

        for t in tiers:
            try:
                keys_to_delete = []

                if scope == InvalidationScope.EXACT:
                    keys_to_delete = [value]

                elif scope == InvalidationScope.PREFIX:
                    cursor = 0
                    while True:
                        cursor, keys = await self.redis_clients[t].scan(
                            cursor, match=f"{value}*", count=100
                        )
                        keys_to_delete.extend(keys)
                        if cursor == 0:
                            break

                elif scope == InvalidationScope.TAG:
                    tag_members = await self.redis_clients[t].smembers(f"tag:{value}")
                    keys_to_delete = list(tag_members)

                elif scope == InvalidationScope.PATTERN:
                    cursor = 0
                    while True:
                        cursor, keys = await self.redis_clients[t].scan(
                            cursor, match=value, count=100
                        )
                        keys_to_delete.extend(keys)
                        if cursor == 0:
                            break

                elif scope == InvalidationScope.GLOBAL:
                    await self.redis_clients[t].flushdb()
                    self.metrics[t].invalidations += 1
                    logger.info("Global cache invalidation for tier %s", t)
                    continue

                # Delete keys
                if keys_to_delete:
                    # Decode bytes keys if necessary
                    decoded_keys = [
                        k.decode() if isinstance(k, bytes) else k for k in keys_to_delete
                    ]
                    await self.redis_clients[t].delete(*decoded_keys)
                    self.metrics[t].invalidations += len(decoded_keys)
                    logger.info("Invalidated %d keys in tier %s", len(decoded_keys), t)

                # CDN invalidation
                if (
                    t == CacheTier.EDGE
                    and self.cdn_provider
                    and scope in [InvalidationScope.EXACT, InvalidationScope.PREFIX]
                ):
                    urls = [f"/{k.split(':')[1]}" for k in decoded_keys if ":" in k]
                    if urls:
                        await self.cdn_provider.purge(urls)

            except Exception as e:
                logger.error("Cache invalidation error: %s", e)
                self.metrics[t].error_count += 1

    async def warm_cache(self, urls: List[str], tier: CacheTier = CacheTier.EDGE):
        """Pre-warm cache with URLs"""
        if self.cdn_provider:
            await self.cdn_provider.warm(urls)

        # Also warm our Redis cache
        async with httpx.AsyncClient() as client:
            for url in urls:
                try:
                    response = await client.get(url)
                    if response.status_code == 200:
                        # Generate cache key
                        key = f"cache:{url}"
                        # Store in cache
                        entry = CacheEntry(
                            key=key,
                            value=response.content,
                            content_type=response.headers.get(
                                "content-type", "application/octet-stream"
                            ),
                            headers=dict(response.headers),
                            created_at=datetime.utcnow(),
                            expires_at=datetime.utcnow() + timedelta(seconds=self.default_ttl),
                            etag=self._generate_etag(response.content),
                            size_bytes=len(response.content),
                        )
                        await self.set(key, entry, tier)
                except Exception as e:
                    logger.error("Cache warming failed for %s: %s", url, e)

    async def _revalidate(self, key: str, tier: CacheTier):
        """Revalidate stale cache entry"""
        # This would fetch fresh content from origin
        # Implementation depends on your application
        pass

    async def _update_stats(self, key: str, tier: CacheTier, entry: CacheEntry):
        """Update cache entry statistics"""
        try:
            # Re-save entry with updated stats
            await self.set(key, entry, tier)
        except Exception as e:
            logger.error("Failed to update cache stats: %s", e)

    def _update_latency(self, tier: CacheTier, latency_ms: float):
        """Update average latency metric"""
        metrics = self.metrics[tier]
        total = metrics.hits + metrics.misses
        if total > 0:
            metrics.average_latency_ms = (
                metrics.average_latency_ms * (total - 1) + latency_ms
            ) / total

    async def _metrics_collector(self):
        """Collect cache metrics periodically"""
        while True:
            try:
                for tier in CacheTier:
                    # Get Redis info
                    info = await self.redis_clients[tier].info("stats")

                    # Log metrics
                    metrics = self.metrics[tier]
                    hit_rate = (
                        metrics.hits / (metrics.hits + metrics.misses) * 100
                        if metrics.hits + metrics.misses > 0
                        else 0
                    )

                    logger.info(
                        "Cache metrics [%s]: hit_rate=%.2f%%, hits=%d, misses=%d, "
                        "bytes_served=%d, latency=%.2fms",
                        tier.value,
                        hit_rate,
                        metrics.hits,
                        metrics.misses,
                        metrics.bytes_served,
                        metrics.average_latency_ms,
                    )

                await asyncio.sleep(60)  # Collect every minute

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Metrics collection error: %s", e)
                await asyncio.sleep(10)

    async def _cache_warmer(self):
        """Periodically warm cache with popular content"""
        # This would identify and pre-load popular content
        # Implementation depends on your application
        while True:
            try:
                await asyncio.sleep(300)  # Every 5 minutes
                # Implement cache warming logic here
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Cache warming error: %s", e)

    async def _eviction_manager(self):
        """Manage cache eviction when size limits are reached"""
        while True:
            try:
                for tier in CacheTier:
                    # Check cache size
                    info = await self.redis_clients[tier].info("memory")
                    used_memory = info.get("used_memory", 0)

                    if used_memory > self.max_cache_size:
                        # Implement LRU eviction
                        logger.warning("Cache size exceeded for %s, evicting...", tier)
                        # This would implement eviction logic
                        # Could use Redis MAXMEMORY policies instead

                await asyncio.sleep(60)  # Check every minute

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Eviction manager error: %s", e)
                await asyncio.sleep(10)

    def get_metrics(self) -> dict:
        """Get cache metrics for all tiers"""
        return {
            tier.value: {
                "hits": metrics.hits,
                "misses": metrics.misses,
                "hit_rate": (
                    metrics.hits / (metrics.hits + metrics.misses) * 100
                    if metrics.hits + metrics.misses > 0
                    else 0
                ),
                "evictions": metrics.evictions,
                "invalidations": metrics.invalidations,
                "bytes_served": metrics.bytes_served,
                "bytes_stored": metrics.bytes_stored,
                "average_latency_ms": metrics.average_latency_ms,
                "errors": metrics.error_count,
            }
            for tier, metrics in self.metrics.items()
        }


# Middleware for automatic caching
class EdgeCacheMiddleware:
    """FastAPI middleware for edge caching"""

    def __init__(self, cache: EdgeCache, config: CacheConfig = None):
        self.cache = cache
        self.config = config or CacheConfig()

    async def __call__(self, request: Request, call_next):
        # Skip non-cacheable methods
        if request.method not in ["GET", "HEAD"]:
            return await call_next(request)

        # Generate cache key
        cache_key = self.cache._generate_cache_key(request, self.config.vary_headers)

        # Check cache
        cache_entry = await self.cache.get(cache_key)

        if cache_entry:
            # Cache hit - return cached response
            headers = cache_entry.headers.copy()
            headers["X-Cache"] = "HIT"
            headers["Age"] = str(int((datetime.utcnow() - cache_entry.created_at).total_seconds()))

            # Check If-None-Match
            if request.headers.get("If-None-Match") == cache_entry.etag:
                return Response(status_code=304, headers=headers)

            # Decompress if needed
            content = cache_entry.value
            if cache_entry.compressed:
                import gzip

                content = gzip.decompress(content)

            return Response(content=content, media_type=cache_entry.content_type, headers=headers)

        # Cache miss - call origin
        response = await call_next(request)

        # Cache successful responses
        if 200 <= response.status_code < 300:
            # Read response body
            body = b""
            async for chunk in response.body_iterator:
                body += chunk

            # Create cache entry
            cache_entry = CacheEntry(
                key=cache_key,
                value=body,
                content_type=response.media_type,
                headers=dict(response.headers),
                created_at=datetime.utcnow(),
                expires_at=datetime.utcnow() + timedelta(seconds=self.config.ttl_seconds),
                etag=self.cache._generate_etag(body),
                tags=set(self.config.surrogate_keys),
                size_bytes=len(body),
            )

            # Store in cache
            await self.cache.set(cache_key, cache_entry)

            # Add cache headers
            response.headers["X-Cache"] = "MISS"
            response.headers["Cache-Control"] = self._build_cache_control()
            response.headers["ETag"] = cache_entry.etag

            # Return new response with body
            return Response(
                content=body,
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type=response.media_type,
            )

        return response

    def _build_cache_control(self) -> str:
        """Build Cache-Control header"""
        directives = []

        if self.config.max_age:
            directives.append(f"max-age={self.config.max_age}")

        if self.config.s_maxage:
            directives.append(f"s-maxage={self.config.s_maxage}")

        if self.config.stale_while_revalidate:
            directives.append(f"stale-while-revalidate={self.config.stale_while_revalidate}")

        if self.config.stale_if_error:
            directives.append(f"stale-if-error={self.config.stale_if_error}")

        directives.extend(self.config.cache_control_directives)

        return ", ".join(directives)


# Decorator for caching specific endpoints
def edge_cache(
    ttl: int = 3600, tags: List[str] = None, strategy: CacheStrategy = CacheStrategy.CACHE_FIRST
):
    """Decorator for caching endpoint responses"""

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Get cache instance (would be injected in real app)
            cache = kwargs.get("cache")
            if not cache:
                return await func(*args, **kwargs)

            # Generate cache key from function and args
            key_parts = [func.__name__]
            key_parts.extend(str(arg) for arg in args)
            key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()) if k != "cache")
            cache_key = f"endpoint:{':'.join(key_parts)}"

            # Try cache
            if strategy != CacheStrategy.NETWORK_ONLY:
                entry = await cache.get(cache_key, strategy=strategy)
                if entry:
                    return json.loads(entry.value)

            # Call function
            result = await func(*args, **kwargs)

            # Cache result
            if strategy != CacheStrategy.CACHE_ONLY:
                entry = CacheEntry(
                    key=cache_key,
                    value=json.dumps(result).encode(),
                    content_type="application/json",
                    headers={},
                    created_at=datetime.utcnow(),
                    expires_at=datetime.utcnow() + timedelta(seconds=ttl),
                    etag=cache._generate_etag(json.dumps(result).encode()),
                    tags=set(tags) if tags else set(),
                    size_bytes=len(json.dumps(result)),
                )
                await cache.set(cache_key, entry)

            return result

        return wrapper

    return decorator
