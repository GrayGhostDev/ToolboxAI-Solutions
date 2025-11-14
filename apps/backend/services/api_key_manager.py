"""
API Key Manager Service

Manages API keys for external integrations with comprehensive security features.
Integrates with Supabase for persistence and Redis for caching.
"""

import hashlib
import hmac
import json
import logging
import secrets
import time
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Optional, Tuple

import redis.asyncio as redis
from pydantic import BaseModel, Field, validator

from apps.backend.core.config import settings
from apps.backend.core.security.rate_limit_manager import get_rate_limit_manager
from apps.backend.services.supabase_service import SupabaseService

logger = logging.getLogger(__name__)


class APIKeyScope(str, Enum):
    """API key permission scopes."""

    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    ADMIN = "admin"

    # Service-specific scopes
    ROBLOX = "roblox"
    AI = "ai"
    WEBHOOK = "webhook"
    ANALYTICS = "analytics"
    CONTENT = "content"


class APIKeyStatus(str, Enum):
    """API key lifecycle status."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    EXPIRED = "expired"
    REVOKED = "revoked"
    SUSPENDED = "suspended"


@dataclass
class APIKeyMetadata:
    """Metadata associated with an API key."""

    name: str
    description: Optional[str] = None
    organization: Optional[str] = None
    contact_email: Optional[str] = None
    ip_whitelist: Optional[list[str]] = None
    allowed_origins: Optional[list[str]] = None
    rate_limit_override: Optional[int] = None
    custom_data: Optional[dict[str, Any]] = None


class APIKeyModel(BaseModel):
    """API Key data model."""

    key_id: str
    key_hash: str  # Store hashed version
    prefix: str  # First 8 chars for identification
    name: str
    description: Optional[str] = None
    scopes: list[str] = Field(default_factory=list)
    status: APIKeyStatus = APIKeyStatus.ACTIVE

    # Metadata
    organization: Optional[str] = None
    contact_email: Optional[str] = None
    ip_whitelist: Optional[list[str]] = None
    allowed_origins: Optional[list[str]] = None

    # Rate limiting
    rate_limit_per_minute: int = 60
    rate_limit_per_hour: int = 1000
    rate_limit_per_day: int = 10000

    # Usage tracking
    total_requests: int = 0
    last_used_at: Optional[datetime] = None
    last_used_ip: Optional[str] = None

    # Lifecycle
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: Optional[datetime] = None
    rotated_at: Optional[datetime] = None
    revoked_at: Optional[datetime] = None
    revoked_reason: Optional[str] = None

    @validator("scopes", pre=True)
    def validate_scopes(cls, v):
        """Ensure scopes are valid."""
        if isinstance(v, str):
            v = [v]
        valid_scopes = set(s.value for s in APIKeyScope)
        for scope in v:
            if scope not in valid_scopes:
                raise ValueError(f"Invalid scope: {scope}")
        return v


class APIKeyManager:
    """
    Centralized API key management service.

    Features:
    - Secure key generation with cryptographic randomness
    - Key validation with Redis caching
    - Usage tracking and analytics
    - Rate limiting per key
    - Key rotation and revocation
    - Supabase persistence
    - Prometheus metrics
    """

    _instance = None

    def __init__(self):
        self.supabase = SupabaseService() if hasattr(SupabaseService, "__init__") else None
        self.rate_limiter = get_rate_limit_manager()
        self.redis_client: Optional[redis.Redis] = None

        # Configuration
        self.key_prefix = "tbai_"  # ToolBoxAI prefix
        self.key_length = 48  # Characters after prefix
        self.cache_ttl = 300  # 5 minutes cache TTL
        self.hash_algorithm = "sha256"

        # Cache prefixes
        self.cache_prefix_key = "api_key:"
        self.cache_prefix_usage = "api_key_usage:"

        # Metrics
        self.total_validations = 0
        self.cache_hits = 0
        self.cache_misses = 0
        self.failed_validations = 0

        # In-memory cache for frequently used keys
        self._memory_cache: dict[str, Tuple[APIKeyModel, float]] = {}
        self._memory_cache_max_size = 100

    @classmethod
    def get_instance(cls) -> "APIKeyManager":
        """Get singleton instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    async def connect_redis(self) -> bool:
        """Connect to Redis for caching."""
        try:
            redis_url = settings.REDIS_URL

            if redis_url and redis_url.startswith("rediss://"):
                # Redis Cloud with TLS
                cert_path = settings.REDIS_CLOUD_CA_CERT_PATH
                self.redis_client = await redis.from_url(
                    redis_url,
                    decode_responses=True,
                    socket_connect_timeout=5,
                    ssl_cert_reqs="required" if cert_path else None,
                    ssl_ca_certs=cert_path if cert_path else None,
                )
            else:
                # Local Redis
                self.redis_client = await redis.from_url(
                    redis_url or "redis://localhost:6379/2", decode_responses=True
                )

            await self.redis_client.ping()
            logger.info("Connected to Redis for API key caching")
            return True

        except Exception as e:
            logger.warning(f"Failed to connect to Redis for API keys: {e}")
            return False

    def generate_api_key(self) -> tuple[str, str]:
        """
        Generate a new API key.

        Returns:
            Tuple of (full_key, key_id)
        """
        # Generate cryptographically secure random key
        raw_key = secrets.token_urlsafe(self.key_length)

        # Create full key with prefix
        full_key = f"{self.key_prefix}{raw_key}"

        # Generate key ID (first 8 chars after prefix for identification)
        key_id = raw_key[:8]

        return full_key, key_id

    def hash_api_key(self, api_key: str) -> str:
        """
        Hash an API key for secure storage.

        Args:
            api_key: The plain API key

        Returns:
            Hashed key
        """
        # Use HMAC with a secret for additional security
        secret = (
            settings.JWT_SECRET_KEY.encode()
            if hasattr(settings, "JWT_SECRET_KEY")
            else b"default_secret"
        )

        return hmac.new(secret, api_key.encode(), hashlib.sha256).hexdigest()

    async def create_api_key(
        self,
        name: str,
        scopes: list[str],
        metadata: Optional[APIKeyMetadata] = None,
        expires_in_days: Optional[int] = None,
    ) -> dict[str, Any]:
        """
        Create a new API key.

        Args:
            name: Name for the API key
            scopes: List of permission scopes
            metadata: Optional metadata
            expires_in_days: Optional expiration in days

        Returns:
            Dictionary with key details
        """
        # Generate key
        full_key, key_id = self.generate_api_key()
        key_hash = self.hash_api_key(full_key)

        # Create key model
        api_key = APIKeyModel(
            key_id=key_id,
            key_hash=key_hash,
            prefix=full_key[: len(self.key_prefix) + 8],
            name=name,
            scopes=scopes,
            status=APIKeyStatus.ACTIVE,
        )

        # Add metadata if provided
        if metadata:
            api_key.description = metadata.description
            api_key.organization = metadata.organization
            api_key.contact_email = metadata.contact_email
            api_key.ip_whitelist = metadata.ip_whitelist
            api_key.allowed_origins = metadata.allowed_origins

            if metadata.rate_limit_override:
                api_key.rate_limit_per_minute = metadata.rate_limit_override

        # Set expiration if specified
        if expires_in_days:
            api_key.expires_at = datetime.now(timezone.utc) + timedelta(days=expires_in_days)

        # Store in Supabase
        if self.supabase:
            try:
                await self.supabase.table("api_keys").insert(api_key.dict()).execute()
                logger.info(f"Created API key: {api_key.key_id}")
            except Exception as e:
                logger.error(f"Failed to store API key in Supabase: {e}")
                # Continue with in-memory storage as fallback

        # Cache in Redis
        if self.redis_client:
            try:
                cache_key = f"{self.cache_prefix_key}{key_hash}"
                await self.redis_client.setex(
                    cache_key, self.cache_ttl, json.dumps(api_key.dict(), default=str)
                )
            except Exception as e:
                logger.debug(f"Failed to cache API key: {e}")

        return {
            "api_key": full_key,  # Only returned once
            "key_id": key_id,
            "prefix": api_key.prefix,
            "name": name,
            "scopes": scopes,
            "expires_at": api_key.expires_at.isoformat() if api_key.expires_at else None,
            "rate_limits": {
                "per_minute": api_key.rate_limit_per_minute,
                "per_hour": api_key.rate_limit_per_hour,
                "per_day": api_key.rate_limit_per_day,
            },
        }

    async def validate_api_key(
        self,
        api_key: str,
        required_scopes: Optional[list[str]] = None,
        request_ip: Optional[str] = None,
        origin: Optional[str] = None,
    ) -> tuple[bool, Optional[APIKeyModel]]:
        """
        Validate an API key.

        Args:
            api_key: The API key to validate
            required_scopes: Optional required scopes
            request_ip: Optional request IP for validation
            origin: Optional request origin for validation

        Returns:
            Tuple of (is_valid, api_key_model)
        """
        self.total_validations += 1

        # Hash the provided key
        key_hash = self.hash_api_key(api_key)

        # Check memory cache first
        if key_hash in self._memory_cache:
            cached_key, cached_time = self._memory_cache[key_hash]
            if time.time() - cached_time < 60:  # 1 minute memory cache
                self.cache_hits += 1
                return await self._validate_key_model(
                    cached_key, required_scopes, request_ip, origin
                )

        # Check Redis cache
        api_key_model = None
        if self.redis_client:
            try:
                cache_key = f"{self.cache_prefix_key}{key_hash}"
                cached_data = await self.redis_client.get(cache_key)

                if cached_data:
                    self.cache_hits += 1
                    api_key_model = APIKeyModel(**json.loads(cached_data))

                    # Update memory cache
                    self._update_memory_cache(key_hash, api_key_model)

            except Exception as e:
                logger.debug(f"Redis cache error: {e}")

        # If not in cache, fetch from Supabase
        if not api_key_model:
            self.cache_misses += 1

            if self.supabase:
                try:
                    result = (
                        await self.supabase.table("api_keys")
                        .select("*")
                        .eq("key_hash", key_hash)
                        .execute()
                    )

                    if result.data and len(result.data) > 0:
                        api_key_model = APIKeyModel(**result.data[0])

                        # Update caches
                        await self._cache_api_key(api_key_model)
                        self._update_memory_cache(key_hash, api_key_model)

                except Exception as e:
                    logger.error(f"Failed to fetch API key from Supabase: {e}")

            # Fallback: check in-memory if Supabase not available
            if not api_key_model and not self.supabase:
                # For development/testing, accept any key with the right prefix
                if api_key.startswith(self.key_prefix):
                    api_key_model = APIKeyModel(
                        key_id=api_key[len(self.key_prefix) : len(self.key_prefix) + 8],
                        key_hash=key_hash,
                        prefix=api_key[: len(self.key_prefix) + 8],
                        name="Development Key",
                        scopes=[s.value for s in APIKeyScope],
                        status=APIKeyStatus.ACTIVE,
                    )

        if not api_key_model:
            self.failed_validations += 1
            return False, None

        # Validate the key model
        return await self._validate_key_model(api_key_model, required_scopes, request_ip, origin)

    async def _validate_key_model(
        self,
        api_key: APIKeyModel,
        required_scopes: Optional[list[str]],
        request_ip: Optional[str],
        origin: Optional[str],
    ) -> tuple[bool, Optional[APIKeyModel]]:
        """
        Validate an API key model against requirements.

        Returns:
            Tuple of (is_valid, api_key_model)
        """
        # Check status
        if api_key.status != APIKeyStatus.ACTIVE:
            logger.warning(f"API key {api_key.key_id} is {api_key.status}")
            self.failed_validations += 1
            return False, None

        # Check expiration
        if api_key.expires_at and api_key.expires_at < datetime.now(timezone.utc):
            api_key.status = APIKeyStatus.EXPIRED
            await self._update_key_status(api_key)
            logger.warning(f"API key {api_key.key_id} has expired")
            self.failed_validations += 1
            return False, None

        # Check scopes
        if required_scopes:
            key_scopes = set(api_key.scopes)
            if not all(scope in key_scopes for scope in required_scopes):
                logger.warning(f"API key {api_key.key_id} lacks required scopes")
                self.failed_validations += 1
                return False, None

        # Check IP whitelist
        if api_key.ip_whitelist and request_ip:
            if request_ip not in api_key.ip_whitelist:
                logger.warning(f"API key {api_key.key_id} rejected for IP {request_ip}")
                self.failed_validations += 1
                return False, None

        # Check origin whitelist
        if api_key.allowed_origins and origin:
            if origin not in api_key.allowed_origins:
                logger.warning(f"API key {api_key.key_id} rejected for origin {origin}")
                self.failed_validations += 1
                return False, None

        # Update usage
        await self._track_usage(api_key, request_ip)

        return True, api_key

    async def _cache_api_key(self, api_key: APIKeyModel):
        """Cache an API key in Redis."""
        if self.redis_client:
            try:
                cache_key = f"{self.cache_prefix_key}{api_key.key_hash}"
                await self.redis_client.setex(
                    cache_key, self.cache_ttl, json.dumps(api_key.dict(), default=str)
                )
            except Exception as e:
                logger.debug(f"Failed to cache API key: {e}")

    def _update_memory_cache(self, key_hash: str, api_key: APIKeyModel):
        """Update in-memory cache with LRU eviction."""
        # Remove oldest entries if cache is full
        if len(self._memory_cache) >= self._memory_cache_max_size:
            # Remove oldest 10%
            to_remove = int(self._memory_cache_max_size * 0.1)
            for _ in range(to_remove):
                if self._memory_cache:
                    self._memory_cache.pop(next(iter(self._memory_cache)))

        self._memory_cache[key_hash] = (api_key, time.time())

    async def _track_usage(self, api_key: APIKeyModel, request_ip: Optional[str] = None):
        """Track API key usage."""
        api_key.total_requests += 1
        api_key.last_used_at = datetime.now(timezone.utc)

        if request_ip:
            api_key.last_used_ip = request_ip

        # Update in Redis for distributed tracking
        if self.redis_client:
            try:
                usage_key = f"{self.cache_prefix_usage}{api_key.key_id}"
                await self.redis_client.hincrby(usage_key, "total_requests", 1)
                await self.redis_client.hset(
                    usage_key, "last_used_at", api_key.last_used_at.isoformat()
                )

                if request_ip:
                    await self.redis_client.hset(usage_key, "last_used_ip", request_ip)

                await self.redis_client.expire(usage_key, 86400)  # 24 hour TTL

            except Exception as e:
                logger.debug(f"Failed to track usage in Redis: {e}")

        # Periodically sync to Supabase
        if api_key.total_requests % 100 == 0:
            await self._sync_usage_to_database(api_key)

    async def _sync_usage_to_database(self, api_key: APIKeyModel):
        """Sync usage statistics to database."""
        if self.supabase:
            try:
                await (
                    self.supabase.table("api_keys")
                    .update(
                        {
                            "total_requests": api_key.total_requests,
                            "last_used_at": api_key.last_used_at.isoformat(),
                            "last_used_ip": api_key.last_used_ip,
                        }
                    )
                    .eq("key_id", api_key.key_id)
                    .execute()
                )
            except Exception as e:
                logger.error(f"Failed to sync usage to database: {e}")

    async def _update_key_status(self, api_key: APIKeyModel):
        """Update key status in database."""
        if self.supabase:
            try:
                await (
                    self.supabase.table("api_keys")
                    .update({"status": api_key.status.value})
                    .eq("key_id", api_key.key_id)
                    .execute()
                )
            except Exception as e:
                logger.error(f"Failed to update key status: {e}")

    async def revoke_api_key(self, key_id: str, reason: str) -> bool:
        """
        Revoke an API key.

        Args:
            key_id: The key ID to revoke
            reason: Reason for revocation

        Returns:
            Success status
        """
        try:
            # Update in database
            if self.supabase:
                await (
                    self.supabase.table("api_keys")
                    .update(
                        {
                            "status": APIKeyStatus.REVOKED.value,
                            "revoked_at": datetime.now(timezone.utc).isoformat(),
                            "revoked_reason": reason,
                        }
                    )
                    .eq("key_id", key_id)
                    .execute()
                )

            # Clear from caches
            if self.redis_client:
                # Find and delete cache entries
                pattern = f"{self.cache_prefix_key}*"
                keys = await self.redis_client.keys(pattern)

                for cache_key in keys:
                    cached_data = await self.redis_client.get(cache_key)
                    if cached_data:
                        api_key = APIKeyModel(**json.loads(cached_data))
                        if api_key.key_id == key_id:
                            await self.redis_client.delete(cache_key)
                            break

            # Clear from memory cache
            keys_to_remove = []
            for key_hash, (api_key, _) in self._memory_cache.items():
                if api_key.key_id == key_id:
                    keys_to_remove.append(key_hash)

            for key_hash in keys_to_remove:
                del self._memory_cache[key_hash]

            logger.info(f"Revoked API key {key_id}: {reason}")
            return True

        except Exception as e:
            logger.error(f"Failed to revoke API key: {e}")
            return False

    async def rotate_api_key(self, key_id: str) -> Optional[Dict[str, Any]]:
        """
        Rotate an API key (generate new key with same permissions).

        Args:
            key_id: The key ID to rotate

        Returns:
            New key details or None
        """
        try:
            # Fetch existing key
            if self.supabase:
                result = (
                    await self.supabase.table("api_keys").select("*").eq("key_id", key_id).execute()
                )

                if result.data and len(result.data) > 0:
                    old_key = APIKeyModel(**result.data[0])

                    # Revoke old key
                    await self.revoke_api_key(key_id, "Rotated")

                    # Create new key with same settings
                    metadata = APIKeyMetadata(
                        name=f"{old_key.name} (Rotated)",
                        description=old_key.description,
                        organization=old_key.organization,
                        contact_email=old_key.contact_email,
                        ip_whitelist=old_key.ip_whitelist,
                        allowed_origins=old_key.allowed_origins,
                        rate_limit_override=old_key.rate_limit_per_minute,
                    )

                    # Calculate remaining days if key had expiration
                    expires_in_days = None
                    if old_key.expires_at:
                        remaining = (old_key.expires_at - datetime.now(timezone.utc)).days
                        if remaining > 0:
                            expires_in_days = remaining

                    return await self.create_api_key(
                        name=metadata.name,
                        scopes=old_key.scopes,
                        metadata=metadata,
                        expires_in_days=expires_in_days,
                    )

            return None

        except Exception as e:
            logger.error(f"Failed to rotate API key: {e}")
            return None

    async def check_rate_limit(
        self, api_key: APIKeyModel, source: str = "api"
    ) -> tuple[bool, Optional[int]]:
        """
        Check rate limit for an API key.

        Args:
            api_key: The API key model
            source: Request source

        Returns:
            Tuple of (allowed, retry_after_seconds)
        """
        # Use the key's custom rate limits
        identifier = f"api_key:{api_key.key_id}"

        # Check per-minute limit
        allowed, retry_after = await self.rate_limiter.check_rate_limit(
            identifier=identifier,
            max_requests=api_key.rate_limit_per_minute,
            window_seconds=60,
            source=source,
        )

        if not allowed:
            return False, retry_after

        # Check per-hour limit
        allowed, retry_after = await self.rate_limiter.check_rate_limit(
            identifier=f"{identifier}:hourly",
            max_requests=api_key.rate_limit_per_hour,
            window_seconds=3600,
            source=source,
        )

        if not allowed:
            return False, retry_after

        # Check per-day limit
        allowed, retry_after = await self.rate_limiter.check_rate_limit(
            identifier=f"{identifier}:daily",
            max_requests=api_key.rate_limit_per_day,
            window_seconds=86400,
            source=source,
        )

        return allowed, retry_after

    async def list_api_keys(
        self, organization: Optional[str] = None, status: Optional[APIKeyStatus] = None
    ) -> list[Dict[str, Any]]:
        """
        List API keys with optional filters.

        Args:
            organization: Optional organization filter
            status: Optional status filter

        Returns:
            List of API key summaries
        """
        try:
            if self.supabase:
                query = self.supabase.table("api_keys").select("*")

                if organization:
                    query = query.eq("organization", organization)

                if status:
                    query = query.eq("status", status.value)

                result = await query.execute()

                # Convert to summaries (don't expose hashes)
                summaries = []
                for data in result.data:
                    api_key = APIKeyModel(**data)
                    summaries.append(
                        {
                            "key_id": api_key.key_id,
                            "prefix": api_key.prefix,
                            "name": api_key.name,
                            "organization": api_key.organization,
                            "status": api_key.status,
                            "scopes": api_key.scopes,
                            "total_requests": api_key.total_requests,
                            "last_used_at": (
                                api_key.last_used_at.isoformat() if api_key.last_used_at else None
                            ),
                            "created_at": api_key.created_at.isoformat(),
                            "expires_at": (
                                api_key.expires_at.isoformat() if api_key.expires_at else None
                            ),
                        }
                    )

                return summaries

            return []

        except Exception as e:
            logger.error(f"Failed to list API keys: {e}")
            return []

    def get_metrics(self) -> dict[str, Any]:
        """Get API key manager metrics."""
        cache_hit_rate = self.cache_hits / max(self.total_validations, 1)
        validation_failure_rate = self.failed_validations / max(self.total_validations, 1)

        return {
            "total_validations": self.total_validations,
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "cache_hit_rate": cache_hit_rate,
            "failed_validations": self.failed_validations,
            "validation_failure_rate": validation_failure_rate,
            "memory_cache_size": len(self._memory_cache),
            "memory_cache_max_size": self._memory_cache_max_size,
        }

    def export_prometheus_metrics(self) -> str:
        """Export metrics in Prometheus format."""
        metrics = self.get_metrics()

        lines = [
            "# HELP api_key_validations_total Total API key validations",
            "# TYPE api_key_validations_total counter",
            f"api_key_validations_total {metrics['total_validations']}",
            "# HELP api_key_cache_hits_total Cache hits for API key validation",
            "# TYPE api_key_cache_hits_total counter",
            f"api_key_cache_hits_total {metrics['cache_hits']}",
            "# HELP api_key_cache_misses_total Cache misses for API key validation",
            "# TYPE api_key_cache_misses_total counter",
            f"api_key_cache_misses_total {metrics['cache_misses']}",
            "# HELP api_key_validation_failures_total Failed API key validations",
            "# TYPE api_key_validation_failures_total counter",
            f"api_key_validation_failures_total {metrics['failed_validations']}",
            "# HELP api_key_cache_hit_rate API key cache hit rate",
            "# TYPE api_key_cache_hit_rate gauge",
            f"api_key_cache_hit_rate {metrics['cache_hit_rate']}",
            "# HELP api_key_memory_cache_size Current memory cache size",
            "# TYPE api_key_memory_cache_size gauge",
            f"api_key_memory_cache_size {metrics['memory_cache_size']}",
        ]

        return "\n".join(lines)


# Singleton instance getter
def get_api_key_manager() -> APIKeyManager:
    """Get singleton instance of the API key manager."""
    return APIKeyManager.get_instance()


# Export for convenience
api_key_manager = get_api_key_manager()
