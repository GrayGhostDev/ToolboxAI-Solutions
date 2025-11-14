"""
API Key Authentication System for Roblox Plugins
Provides secure, scoped API keys for automated plugin access
"""

import asyncio
import hashlib
import logging
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import List, Optional

import redis.asyncio as redis
from pydantic import BaseModel, Field
from sqlalchemy import (
    JSON,
    Column,
    DateTime,
    Integer,
    String,
    select,
)
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.declarative import declarative_base

logger = logging.getLogger(__name__)

Base = declarative_base()


class APIKeyScope(str, Enum):
    """API key permission scopes"""

    READ = "read"
    WRITE = "write"
    DEPLOY = "deploy"
    ADMIN = "admin"
    SCRIPT_GENERATE = "script.generate"
    SCRIPT_VALIDATE = "script.validate"
    CONTENT_ACCESS = "content.access"
    ANALYTICS_READ = "analytics.read"


class APIKeyStatus(str, Enum):
    """API key status"""

    ACTIVE = "active"
    REVOKED = "revoked"
    EXPIRED = "expired"
    SUSPENDED = "suspended"


class APIKeyModel(Base):
    """Database model for API keys"""

    __tablename__ = "api_keys"

    id = Column(Integer, primary_key=True, index=True)
    key_id = Column(String(36), unique=True, index=True, default=lambda: str(uuid.uuid4()))
    key_hash = Column(String(128), unique=True, index=True)  # SHA-512 hash
    name = Column(String(100), nullable=False)
    description = Column(String(500))
    user_id = Column(String(100), index=True, nullable=False)

    # Scopes and permissions
    scopes = Column(JSON, default=list)  # List of APIKeyScope values
    place_ids = Column(JSON, default=list)  # Restricted to specific Roblox places
    ip_whitelist = Column(JSON, default=list)  # IP restriction (optional)

    # Status and lifecycle
    status = Column(SQLEnum(APIKeyStatus), default=APIKeyStatus.ACTIVE)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    expires_at = Column(DateTime(timezone=True), nullable=True)
    last_used_at = Column(DateTime(timezone=True), nullable=True)
    revoked_at = Column(DateTime(timezone=True), nullable=True)

    # Usage tracking
    usage_count = Column(Integer, default=0)
    rate_limit = Column(Integer, default=1000)  # Requests per hour

    # Additional data
    additional_metadata = Column("metadata", JSON, default=dict)


class APIKeyCreate(BaseModel):
    """API key creation request"""

    name: str = Field(min_length=3, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    scopes: List[APIKeyScope] = Field(default=[APIKeyScope.READ])
    place_ids: Optional[List[str]] = Field(default=[])
    ip_whitelist: Optional[List[str]] = Field(default=[])
    expires_in_days: Optional[int] = Field(None, ge=1, le=365)
    rate_limit: int = Field(default=1000, ge=10, le=10000)


class APIKeyResponse(BaseModel):
    """API key response"""

    key_id: str
    api_key: Optional[str] = Field(None, description="Only provided on creation")
    name: str
    description: Optional[str]
    scopes: List[str]
    place_ids: List[str]
    status: str
    created_at: datetime
    expires_at: Optional[datetime]
    rate_limit: int
    usage_count: int


class APIKeyValidation(BaseModel):
    """API key validation result"""

    is_valid: bool
    key_id: Optional[str] = None
    user_id: Optional[str] = None
    scopes: List[str] = Field(default=[])
    place_ids: List[str] = Field(default=[])
    rate_limit_remaining: Optional[int] = None
    error: Optional[str] = None


class APIKeyManager:
    """Manages API key lifecycle and validation"""

    def __init__(
        self,
        redis_url: str = "redis://localhost:6379",
        key_prefix: str = "roblox:apikey:",
        rate_limit_window: int = 3600,  # 1 hour in seconds
    ):
        self.redis_url = redis_url
        self.redis_client: Optional[redis.Redis] = None
        self.key_prefix = key_prefix
        self.rate_limit_prefix = f"{key_prefix}rate:"
        self.rate_limit_window = rate_limit_window

    async def initialize(self):
        """Initialize Redis connection"""
        try:
            self.redis_client = await redis.from_url(
                self.redis_url, encoding="utf-8", decode_responses=True
            )
            logger.info("API Key Manager initialized")
        except Exception as e:
            logger.error(f"Failed to initialize API Key Manager: {e}")
            raise

    async def close(self):
        """Close Redis connection"""
        if self.redis_client:
            await self.redis_client.close()

    def _generate_api_key(self) -> str:
        """Generate a secure API key"""
        # Format: rbx_<random_32_chars>
        return f"rbx_{secrets.token_urlsafe(32)}"

    def _hash_api_key(self, api_key: str) -> str:
        """Hash API key for storage"""
        return hashlib.sha512(api_key.encode()).hexdigest()

    async def create_api_key(
        self, db: AsyncSession, user_id: str, request: APIKeyCreate
    ) -> APIKeyResponse:
        """Create a new API key"""
        try:
            # Generate API key
            api_key = self._generate_api_key()
            key_hash = self._hash_api_key(api_key)

            # Calculate expiration
            expires_at = None
            if request.expires_in_days:
                expires_at = datetime.now(timezone.utc) + timedelta(days=request.expires_in_days)

            # Create database record
            db_key = APIKeyModel(
                key_hash=key_hash,
                name=request.name,
                description=request.description,
                user_id=user_id,
                scopes=[scope.value for scope in request.scopes],
                place_ids=request.place_ids or [],
                ip_whitelist=request.ip_whitelist or [],
                expires_at=expires_at,
                rate_limit=request.rate_limit,
            )

            db.add(db_key)
            await db.commit()
            await db.refresh(db_key)

            # Cache key info in Redis for fast lookup
            cache_data = {
                "key_id": db_key.key_id,
                "user_id": user_id,
                "scopes": ",".join([scope for scope in db_key.scopes]),
                "place_ids": ",".join(db_key.place_ids) if db_key.place_ids else "",
                "rate_limit": str(db_key.rate_limit),
                "status": db_key.status.value,
            }

            # Store with TTL if key expires
            ttl = None
            if expires_at:
                ttl = int((expires_at - datetime.now(timezone.utc)).total_seconds())

            await self.redis_client.hset(f"{self.key_prefix}{key_hash}", mapping=cache_data)

            if ttl and ttl > 0:
                await self.redis_client.expire(f"{self.key_prefix}{key_hash}", ttl)

            logger.info(f"Created API key {db_key.key_id} for user {user_id}")

            return APIKeyResponse(
                key_id=db_key.key_id,
                api_key=api_key,  # Only returned on creation
                name=db_key.name,
                description=db_key.description,
                scopes=db_key.scopes,
                place_ids=db_key.place_ids,
                status=db_key.status.value,
                created_at=db_key.created_at,
                expires_at=db_key.expires_at,
                rate_limit=db_key.rate_limit,
                usage_count=db_key.usage_count,
            )

        except Exception as e:
            logger.error(f"Failed to create API key: {e}")
            await db.rollback()
            raise

    async def validate_api_key(
        self,
        api_key: str,
        required_scope: Optional[APIKeyScope] = None,
        place_id: Optional[str] = None,
        client_ip: Optional[str] = None,
    ) -> APIKeyValidation:
        """Validate an API key"""
        try:
            key_hash = self._hash_api_key(api_key)

            # Check Redis cache first
            cached_data = await self.redis_client.hgetall(f"{self.key_prefix}{key_hash}")

            if not cached_data:
                return APIKeyValidation(is_valid=False, error="Invalid API key")

            # Check status
            if cached_data.get("status") != APIKeyStatus.ACTIVE.value:
                return APIKeyValidation(
                    is_valid=False,
                    error=f"API key is {cached_data.get('status', 'invalid')}",
                )

            # Check scope
            scopes = cached_data.get("scopes", "").split(",") if cached_data.get("scopes") else []
            if (
                required_scope
                and required_scope.value not in scopes
                and APIKeyScope.ADMIN.value not in scopes
            ):
                return APIKeyValidation(
                    is_valid=False,
                    error=f"Insufficient permissions. Required scope: {required_scope.value}",
                )

            # Check place ID restriction
            place_ids = (
                cached_data.get("place_ids", "").split(",") if cached_data.get("place_ids") else []
            )
            if place_ids and place_id and place_id not in place_ids:
                return APIKeyValidation(
                    is_valid=False,
                    error=f"API key not authorized for place ID: {place_id}",
                )

            # Check rate limit
            rate_limit = int(cached_data.get("rate_limit", "1000"))
            rate_key = f"{self.rate_limit_prefix}{key_hash}"

            # Increment and check rate limit
            current_count = await self.redis_client.incr(rate_key)

            # Set expiration on first request
            if current_count == 1:
                await self.redis_client.expire(rate_key, self.rate_limit_window)

            if current_count > rate_limit:
                return APIKeyValidation(
                    is_valid=False,
                    error=f"Rate limit exceeded. Limit: {rate_limit}/hour",
                )

            # Update last used timestamp (async, don't wait)
            asyncio.create_task(self._update_last_used(key_hash))

            return APIKeyValidation(
                is_valid=True,
                key_id=cached_data.get("key_id"),
                user_id=cached_data.get("user_id"),
                scopes=scopes,
                place_ids=place_ids,
                rate_limit_remaining=max(0, rate_limit - current_count),
            )

        except Exception as e:
            logger.error(f"Error validating API key: {e}")
            return APIKeyValidation(is_valid=False, error="Internal validation error")

    async def _update_last_used(self, key_hash: str):
        """Update last used timestamp for API key"""
        try:
            # Update in cache
            await self.redis_client.hset(
                f"{self.key_prefix}{key_hash}",
                "last_used",
                datetime.now(timezone.utc).isoformat(),
            )

            # Increment usage counter
            await self.redis_client.hincrby(f"{self.key_prefix}{key_hash}", "usage_count", 1)
        except Exception as e:
            logger.warning(f"Failed to update last used timestamp: {e}")

    async def revoke_api_key(self, db: AsyncSession, key_id: str, user_id: str) -> bool:
        """Revoke an API key"""
        try:
            # Find the key
            result = await db.execute(
                select(APIKeyModel).where(
                    APIKeyModel.key_id == key_id, APIKeyModel.user_id == user_id
                )
            )
            db_key = result.scalar_one_or_none()

            if not db_key:
                return False

            # Update status
            db_key.status = APIKeyStatus.REVOKED
            db_key.revoked_at = datetime.now(timezone.utc)

            await db.commit()

            # Remove from cache
            await self.redis_client.delete(f"{self.key_prefix}{db_key.key_hash}")
            await self.redis_client.delete(f"{self.rate_limit_prefix}{db_key.key_hash}")

            logger.info(f"Revoked API key {key_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to revoke API key: {e}")
            await db.rollback()
            return False

    async def list_api_keys(
        self, db: AsyncSession, user_id: str, include_revoked: bool = False
    ) -> List[APIKeyResponse]:
        """List API keys for a user"""
        try:
            query = select(APIKeyModel).where(APIKeyModel.user_id == user_id)

            if not include_revoked:
                query = query.where(APIKeyModel.status == APIKeyStatus.ACTIVE)

            result = await db.execute(query)
            keys = result.scalars().all()

            return [
                APIKeyResponse(
                    key_id=key.key_id,
                    name=key.name,
                    description=key.description,
                    scopes=key.scopes,
                    place_ids=key.place_ids,
                    status=key.status.value,
                    created_at=key.created_at,
                    expires_at=key.expires_at,
                    rate_limit=key.rate_limit,
                    usage_count=key.usage_count,
                )
                for key in keys
            ]

        except Exception as e:
            logger.error(f"Failed to list API keys: {e}")
            return []

    async def cleanup_expired_keys(self, db: AsyncSession):
        """Clean up expired API keys"""
        try:
            now = datetime.now(timezone.utc)

            # Find expired keys
            result = await db.execute(
                select(APIKeyModel).where(
                    APIKeyModel.expires_at < now,
                    APIKeyModel.status == APIKeyStatus.ACTIVE,
                )
            )
            expired_keys = result.scalars().all()

            for key in expired_keys:
                key.status = APIKeyStatus.EXPIRED

                # Remove from cache
                await self.redis_client.delete(f"{self.key_prefix}{key.key_hash}")
                await self.redis_client.delete(f"{self.rate_limit_prefix}{key.key_hash}")

            await db.commit()

            if expired_keys:
                logger.info(f"Cleaned up {len(expired_keys)} expired API keys")

        except Exception as e:
            logger.error(f"Failed to cleanup expired keys: {e}")
            await db.rollback()


# Singleton instance
_api_key_manager: Optional[APIKeyManager] = None


async def get_api_key_manager() -> APIKeyManager:
    """Get or create API key manager instance"""
    global _api_key_manager

    if _api_key_manager is None:
        _api_key_manager = APIKeyManager()
        await _api_key_manager.initialize()

    return _api_key_manager
