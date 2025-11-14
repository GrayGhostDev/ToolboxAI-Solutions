"""
Clerk Authentication Module for ToolboxAI (2025)
Provides JWT verification for Clerk-authenticated requests
"""

import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict, Optional

import httpx
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from pydantic import BaseModel

logger = logging.getLogger(__name__)

# Clerk configuration from environment
CLERK_SECRET_KEY = os.getenv("CLERK_SECRET_KEY")
CLERK_JWKS_URL = os.getenv(
    "CLERK_JWKS_URL", "https://casual-firefly-39.clerk.accounts.dev/.well-known/jwks.json"
)
CLERK_ISSUER = os.getenv("CLERK_FRONTEND_API_URL", "https://casual-firefly-39.clerk.accounts.dev")

# Security scheme
bearer_scheme = HTTPBearer(auto_error=False)

# Cache for JWKS keys
_jwks_cache = None
_jwks_cache_time = None
JWKS_CACHE_DURATION = 3600  # 1 hour


class ClerkUser(BaseModel):
    """Clerk user model from JWT claims"""

    user_id: str
    email: str | None = None
    username: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    image_url: str | None = None
    role: str = "student"
    metadata: Dict[str, Any] = {}
    session_id: str | None = None
    organization_id: str | None = None
    organization_role: str | None = None


class ClerkAuthError(HTTPException):
    """Clerk authentication error"""

    def __init__(self, detail: str = "Authentication failed"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_jwks_keys():
    """Fetch JWKS keys from Clerk with caching"""
    global _jwks_cache, _jwks_cache_time

    # Check cache
    if _jwks_cache and _jwks_cache_time:
        cache_age = (datetime.now(timezone.utc) - _jwks_cache_time).total_seconds()
        if cache_age < JWKS_CACHE_DURATION:
            return _jwks_cache

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(CLERK_JWKS_URL)
            response.raise_for_status()
            jwks = response.json()

            # Update cache
            _jwks_cache = jwks
            _jwks_cache_time = datetime.now(timezone.utc)

            return jwks
    except Exception as e:
        logger.error(f"Failed to fetch JWKS keys: {e}")
        if _jwks_cache:
            # Return cached keys if available
            return _jwks_cache
        raise ClerkAuthError("Failed to fetch authentication keys")


async def verify_clerk_token(token: str) -> ClerkUser:
    """
    Verify a Clerk JWT token and extract user information

    Args:
        token: JWT token from Clerk

    Returns:
        ClerkUser object with user information

    Raises:
        ClerkAuthError: If token verification fails
    """
    try:
        # Get JWKS keys
        jwks = await get_jwks_keys()

        # Decode token header to get kid
        unverified_header = jwt.get_unverified_header(token)
        kid = unverified_header.get("kid")

        if not kid:
            raise ClerkAuthError("Invalid token format")

        # Find the correct key
        rsa_key = None
        for key in jwks.get("keys", []):
            if key["kid"] == kid:
                rsa_key = key
                break

        if not rsa_key:
            raise ClerkAuthError("Unable to find appropriate key")

        # Verify and decode token
        payload = jwt.decode(
            token,
            rsa_key,
            algorithms=["RS256"],
            issuer=CLERK_ISSUER,
            options={
                "verify_signature": True,
                "verify_exp": True,
                "verify_aud": False,  # Clerk doesn't always set audience
            },
        )

        # Extract user information from claims
        user = ClerkUser(
            user_id=payload.get("sub"),
            email=payload.get("email"),
            username=payload.get("username"),
            first_name=payload.get("first_name"),
            last_name=payload.get("last_name"),
            image_url=payload.get("image_url"),
            session_id=payload.get("sid"),
            organization_id=payload.get("org_id"),
            organization_role=payload.get("org_role"),
            metadata={
                "email_verified": payload.get("email_verified", False),
                "phone_number": payload.get("phone_number"),
                "public_metadata": payload.get("public_metadata", {}),
                "unsafe_metadata": payload.get("unsafe_metadata", {}),
            },
        )

        # Extract role from metadata
        if payload.get("public_metadata", {}).get("role"):
            user.role = payload["public_metadata"]["role"]

        return user

    except JWTError as e:
        logger.error(f"JWT verification failed: {e}")
        raise ClerkAuthError(f"Invalid token: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error during token verification: {e}")
        raise ClerkAuthError("Authentication failed")


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> ClerkUser:
    """
    Dependency to get the current authenticated user from Clerk token

    Args:
        credentials: Bearer token from request header

    Returns:
        ClerkUser object

    Raises:
        ClerkAuthError: If authentication fails
    """
    if not credentials:
        raise ClerkAuthError("No authentication credentials provided")

    return await verify_clerk_token(credentials.credentials)


async def require_role(required_role: str):
    """
    Dependency factory to require a specific role

    Args:
        required_role: The role required to access the endpoint

    Returns:
        Dependency function that validates the user's role
    """

    async def role_checker(user: ClerkUser = Depends(get_current_user)) -> ClerkUser:
        if user.role != required_role and user.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required role: {required_role}",
            )
        return user

    return role_checker


# Convenience dependencies for common roles
RequireAdmin = Depends(require_role("admin"))
RequireTeacher = Depends(require_role("teacher"))
RequireStudent = Depends(require_role("student"))


# Optional: Backward compatibility with existing auth
async def get_current_user_compatible(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> Dict[str, Any]:
    """
    Backward compatible version that returns user dict like the old system
    """
    if not credentials:
        # Try to fall back to old JWT auth if available
        from apps.backend.api.auth.auth import get_current_user as get_jwt_user

        return await get_jwt_user(credentials)

    try:
        # Try Clerk auth first
        clerk_user = await verify_clerk_token(credentials.credentials)

        # Convert to old format
        return {
            "id": clerk_user.user_id,
            "email": clerk_user.email,
            "username": clerk_user.username,
            "role": clerk_user.role,
            "first_name": clerk_user.first_name,
            "last_name": clerk_user.last_name,
            "avatar": clerk_user.image_url,
            "is_active": True,
            "email_verified": clerk_user.metadata.get("email_verified", False),
        }
    except Exception:
        # Fall back to old auth
        from apps.backend.api.auth.auth import get_current_user as get_jwt_user

        return await get_jwt_user(credentials)
