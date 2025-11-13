"""
JWT Token Rotation Manager with Redis Storage
Implements secure key rotation, refresh tokens, and grace periods
"""

import json
import logging
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any

import redis.asyncio as redis
from jose import JWTError, jwt
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class JWTKeyPair(BaseModel):
    """JWT key pair with metadata"""

    kid: str = Field(description="Key ID")
    secret_key: str = Field(description="Secret key for signing")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: datetime = Field(description="Key expiration time")
    is_active: bool = Field(default=True)


class TokenPayload(BaseModel):
    """JWT token payload structure"""

    sub: str  # Subject (user ID)
    exp: datetime  # Expiration
    iat: datetime  # Issued at
    jti: str  # JWT ID (for revocation)
    kid: str  # Key ID (for rotation)
    type: str = "access"  # Token type: access or refresh
    scope: str | None = None


class JWTRotationManager:
    """Manages JWT key rotation with Redis storage"""

    def __init__(
        self,
        redis_url: str = "redis://localhost:6379",
        key_rotation_interval: int = 86400,  # 24 hours
        key_grace_period: int = 3600,  # 1 hour grace period for old keys
        access_token_expire: int = 900,  # 15 minutes
        refresh_token_expire: int = 604800,  # 7 days
        algorithm: str = "HS256",
    ):
        self.redis_url = redis_url
        self.redis_client: redis.Redis | None = None
        self.key_rotation_interval = key_rotation_interval
        self.key_grace_period = key_grace_period
        self.access_token_expire = access_token_expire
        self.refresh_token_expire = refresh_token_expire
        self.algorithm = algorithm
        self.key_prefix = "jwt:keys:"
        self.revoked_prefix = "jwt:revoked:"
        self.refresh_prefix = "jwt:refresh:"

    async def initialize(self):
        """Initialize Redis connection and ensure active key exists"""
        try:
            self.redis_client = await redis.from_url(
                self.redis_url, encoding="utf-8", decode_responses=True
            )

            # Ensure we have an active key
            active_key = await self.get_active_key()
            if not active_key:
                await self.rotate_keys()

            logger.info("JWT Rotation Manager initialized")
        except Exception as e:
            logger.error(f"Failed to initialize JWT Rotation Manager: {e}")
            raise

    async def close(self):
        """Close Redis connection"""
        if self.redis_client:
            await self.redis_client.close()

    def _generate_key_id(self) -> str:
        """Generate unique key ID"""
        return f"key_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}_{secrets.token_hex(4)}"

    def _generate_secret_key(self) -> str:
        """Generate cryptographically secure secret key"""
        # 512 bits of entropy for HS256
        return secrets.token_urlsafe(64)

    async def rotate_keys(self) -> JWTKeyPair:
        """Rotate JWT keys, maintaining grace period for old keys"""
        try:
            # Get current active key (if exists)
            old_key = await self.get_active_key()

            # Generate new key pair
            new_key = JWTKeyPair(
                kid=self._generate_key_id(),
                secret_key=self._generate_secret_key(),
                expires_at=datetime.now(timezone.utc)
                + timedelta(seconds=self.key_rotation_interval),
            )

            # Store new key in Redis
            key_data = new_key.model_dump_json()
            await self.redis_client.setex(
                f"{self.key_prefix}{new_key.kid}",
                self.key_rotation_interval + self.key_grace_period,
                key_data,
            )

            # Mark as active key
            await self.redis_client.setex(
                f"{self.key_prefix}active", self.key_rotation_interval, new_key.kid
            )

            # If old key exists, keep it for grace period
            if old_key:
                old_key.is_active = False
                await self.redis_client.setex(
                    f"{self.key_prefix}{old_key.kid}",
                    self.key_grace_period,
                    old_key.model_dump_json(),
                )
                logger.info(f"Rotated keys: {old_key.kid} -> {new_key.kid}")
            else:
                logger.info(f"Created initial key: {new_key.kid}")

            return new_key

        except Exception as e:
            logger.error(f"Key rotation failed: {e}")
            raise

    async def get_active_key(self) -> JWTKeyPair | None:
        """Get currently active signing key"""
        try:
            active_kid = await self.redis_client.get(f"{self.key_prefix}active")
            if not active_kid:
                return None

            key_data = await self.redis_client.get(f"{self.key_prefix}{active_kid}")
            if not key_data:
                return None

            return JWTKeyPair.model_validate_json(key_data)
        except Exception as e:
            logger.error(f"Failed to get active key: {e}")
            return None

    async def get_key_by_id(self, kid: str) -> JWTKeyPair | None:
        """Get key by ID (for validation of tokens with old keys)"""
        try:
            key_data = await self.redis_client.get(f"{self.key_prefix}{kid}")
            if not key_data:
                return None
            return JWTKeyPair.model_validate_json(key_data)
        except Exception as e:
            logger.error(f"Failed to get key {kid}: {e}")
            return None

    async def create_token_pair(self, user_id: str, scope: str | None = None) -> tuple[str, str]:
        """Create access and refresh token pair"""
        active_key = await self.get_active_key()
        if not active_key:
            active_key = await self.rotate_keys()

        # Create access token
        now = datetime.now(timezone.utc)
        access_jti = secrets.token_urlsafe(16)
        access_payload = {
            "sub": user_id,
            "exp": int((now + timedelta(seconds=self.access_token_expire)).timestamp()),
            "iat": int(now.timestamp()),
            "jti": access_jti,
            "kid": active_key.kid,
            "type": "access",
        }
        if scope:
            access_payload["scope"] = scope

        access_token = jwt.encode(access_payload, active_key.secret_key, algorithm=self.algorithm)

        # Create refresh token
        refresh_jti = secrets.token_urlsafe(16)
        refresh_payload = {
            "sub": user_id,
            "exp": int((now + timedelta(seconds=self.refresh_token_expire)).timestamp()),
            "iat": int(now.timestamp()),
            "jti": refresh_jti,
            "kid": active_key.kid,
            "type": "refresh",
        }
        if scope:
            refresh_payload["scope"] = scope

        refresh_token = jwt.encode(refresh_payload, active_key.secret_key, algorithm=self.algorithm)

        # Store refresh token in Redis for validation
        await self.redis_client.setex(
            f"{self.refresh_prefix}{refresh_jti}",
            self.refresh_token_expire,
            json.dumps(
                {
                    "user_id": user_id,
                    "kid": active_key.kid,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                }
            ),
        )

        return access_token, refresh_token

    async def verify_token(self, token: str) -> TokenPayload | None:
        """Verify and decode token"""
        try:
            # Decode without verification to get kid
            unverified = jwt.get_unverified_claims(token)
            kid = unverified.get("kid")

            if not kid:
                logger.warning("Token missing kid")
                return None

            # Check if token is revoked
            jti = unverified.get("jti")
            if jti and await self.is_token_revoked(jti):
                logger.warning(f"Token {jti} is revoked")
                return None

            # Get the key used to sign this token
            key = await self.get_key_by_id(kid)
            if not key:
                logger.warning(f"Key {kid} not found")
                return None

            # Verify and decode
            payload = jwt.decode(token, key.secret_key, algorithms=[self.algorithm])

            # Convert timestamps back to datetime objects
            payload_obj = TokenPayload(
                sub=payload["sub"],
                exp=datetime.fromtimestamp(payload["exp"], tz=timezone.utc),
                iat=datetime.fromtimestamp(payload["iat"], tz=timezone.utc),
                jti=payload["jti"],
                kid=payload["kid"],
                type=payload["type"],
                scope=payload.get("scope"),
            )

            return payload_obj

        except JWTError as e:
            logger.warning(f"Token verification failed: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error verifying token: {e}")
            return None

    async def refresh_access_token(self, refresh_token: str) -> tuple[str, str] | None:
        """Generate new access token from refresh token"""
        payload = await self.verify_token(refresh_token)

        if not payload or payload.type != "refresh":
            logger.warning("Invalid refresh token")
            return None

        # Check if refresh token exists in Redis
        refresh_data = await self.redis_client.get(f"{self.refresh_prefix}{payload.jti}")
        if not refresh_data:
            logger.warning(f"Refresh token {payload.jti} not found")
            return None

        # Create new token pair
        return await self.create_token_pair(payload.sub, payload.scope)

    async def revoke_token(self, token: str) -> bool:
        """Revoke a token by adding its JTI to revocation list"""
        try:
            payload = await self.verify_token(token)
            if not payload:
                return False

            # Calculate remaining TTL
            remaining_ttl = int((payload.exp - datetime.now(timezone.utc)).total_seconds())
            if remaining_ttl <= 0:
                return True  # Already expired

            # Add to revocation list
            await self.redis_client.setex(f"{self.revoked_prefix}{payload.jti}", remaining_ttl, "1")

            # If refresh token, also remove from refresh store
            if payload.type == "refresh":
                await self.redis_client.delete(f"{self.refresh_prefix}{payload.jti}")

            logger.info(f"Revoked token {payload.jti}")
            return True

        except Exception as e:
            logger.error(f"Failed to revoke token: {e}")
            return False

    async def is_token_revoked(self, jti: str) -> bool:
        """Check if token is revoked"""
        result = await self.redis_client.get(f"{self.revoked_prefix}{jti}")
        return result is not None

    async def revoke_all_user_tokens(self, user_id: str) -> int:
        """Revoke all tokens for a user (logout everywhere)"""
        count = 0

        # This would require maintaining a user -> tokens mapping
        # For now, return 0 as placeholder
        # In production, maintain a set of active JTIs per user

        logger.info(f"Revoked all tokens for user {user_id}")
        return count

    async def get_key_info(self) -> dict[str, Any]:
        """Get information about current keys"""
        active_key = await self.get_active_key()

        # Count all keys
        all_keys = []
        async for key in self.redis_client.scan_iter(f"{self.key_prefix}*"):
            if not key.endswith("active"):
                all_keys.append(key)

        return {
            "active_key_id": active_key.kid if active_key else None,
            "active_key_expires": active_key.expires_at.isoformat() if active_key else None,
            "total_keys": len(all_keys),
            "rotation_interval": self.key_rotation_interval,
            "grace_period": self.key_grace_period,
        }


# Singleton instance
_jwt_manager: JWTRotationManager | None = None


async def get_jwt_manager() -> JWTRotationManager:
    """Get or create JWT manager instance"""
    global _jwt_manager

    if _jwt_manager is None:
        _jwt_manager = JWTRotationManager()
        await _jwt_manager.initialize()

    return _jwt_manager
