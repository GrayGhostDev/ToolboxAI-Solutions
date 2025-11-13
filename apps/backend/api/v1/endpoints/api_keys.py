"""
API Key Management Endpoints for Roblox Plugin Authentication
"""

import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from apps.backend.core.deps import get_async_db
from apps.backend.core.security.api_keys import (
    APIKeyCreate,
    APIKeyManager,
    APIKeyResponse,
    APIKeyScope,
    APIKeyValidation,
    get_api_key_manager,
)
from apps.backend.core.security.jwt_rotation import TokenPayload, get_jwt_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api-keys", tags=["API Keys"])

# Security dependencies
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> TokenPayload:
    """Verify JWT token and return current user"""
    jwt_manager = await get_jwt_manager()
    token_payload = await jwt_manager.verify_token(credentials.credentials)

    if not token_payload:
        raise HTTPException(status_code=401, detail="Invalid authentication token")

    return token_payload


async def verify_api_key(
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
    required_scope: Optional[APIKeyScope] = None,
    x_place_id: Optional[str] = Header(None, alias="X-Place-ID"),
) -> APIKeyValidation:
    """Verify API key from header"""
    if not x_api_key:
        raise HTTPException(status_code=401, detail="API key required")

    api_key_manager = await get_api_key_manager()
    validation = await api_key_manager.validate_api_key(
        api_key=x_api_key, required_scope=required_scope, place_id=x_place_id
    )

    if not validation.is_valid:
        raise HTTPException(status_code=403, detail=validation.error or "Invalid API key")

    return validation


# API Key Management Endpoints (require JWT auth)


@router.post("/create", response_model=APIKeyResponse)
async def create_api_key(
    request: APIKeyCreate,
    current_user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """
    Create a new API key for Roblox plugin authentication.

    Requires JWT authentication.
    The API key will be returned only once - store it securely!
    """
    try:
        api_key_manager = await get_api_key_manager()
        api_key = await api_key_manager.create_api_key(
            db=db, user_id=current_user.sub, request=request
        )

        logger.info(f"User {current_user.sub} created API key: {api_key.key_id}")

        return api_key

    except Exception as e:
        logger.error(f"Failed to create API key: {e}")
        raise HTTPException(status_code=500, detail="Failed to create API key")


@router.get("/list", response_model=List[APIKeyResponse])
async def list_api_keys(
    include_revoked: bool = Query(False, description="Include revoked keys"),
    current_user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """
    List all API keys for the current user.

    Note: The actual API key values are never returned after creation.
    """
    try:
        api_key_manager = await get_api_key_manager()
        keys = await api_key_manager.list_api_keys(
            db=db, user_id=current_user.sub, include_revoked=include_revoked
        )

        return keys

    except Exception as e:
        logger.error(f"Failed to list API keys: {e}")
        raise HTTPException(status_code=500, detail="Failed to list API keys")


@router.delete("/{key_id}")
async def revoke_api_key(
    key_id: str,
    current_user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """
    Revoke an API key.

    The key will be immediately invalidated and cannot be reactivated.
    """
    try:
        api_key_manager = await get_api_key_manager()
        success = await api_key_manager.revoke_api_key(
            db=db, key_id=key_id, user_id=current_user.sub
        )

        if not success:
            raise HTTPException(status_code=404, detail="API key not found")

        logger.info(f"User {current_user.sub} revoked API key: {key_id}")

        return {"message": "API key revoked successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to revoke API key: {e}")
        raise HTTPException(status_code=500, detail="Failed to revoke API key")


@router.post("/validate")
async def validate_api_key_endpoint(
    x_api_key: str = Header(..., alias="X-API-Key"),
    required_scope: Optional[str] = Query(None, description="Required permission scope"),
    x_place_id: Optional[str] = Header(None, alias="X-Place-ID"),
):
    """
    Validate an API key and check its permissions.

    This endpoint is useful for testing API keys.
    """
    try:
        api_key_manager = await get_api_key_manager()

        scope = APIKeyScope(required_scope) if required_scope else None
        validation = await api_key_manager.validate_api_key(
            api_key=x_api_key, required_scope=scope, place_id=x_place_id
        )

        if not validation.is_valid:
            return {"valid": False, "error": validation.error}

        return {
            "valid": True,
            "key_id": validation.key_id,
            "scopes": validation.scopes,
            "place_ids": validation.place_ids,
            "rate_limit_remaining": validation.rate_limit_remaining,
        }

    except Exception as e:
        logger.error(f"Failed to validate API key: {e}")
        return {"valid": False, "error": "Validation error"}


# Roblox Plugin Endpoints (can use API key auth)


@router.post("/roblox/generate-script")
async def generate_script_with_api_key(
    request: dict,
    api_key_validation: APIKeyValidation = Depends(
        lambda x_api_key: verify_api_key(x_api_key, required_scope=APIKeyScope.SCRIPT_GENERATE)
    ),
):
    """
    Generate a Roblox script using API key authentication.

    This endpoint is designed for Roblox Studio plugins.
    Requires 'script.generate' scope.
    """
    try:
        # Log API key usage
        logger.info(f"API key {api_key_validation.key_id} generating script")

        # Import Roblox content generation agent
        from core.agents.roblox.roblox_content_generation_agent import RobloxContentGenerationAgent

        agent = RobloxContentGenerationAgent(llm=None)
        script = agent.generate_educational_script(
            topic=request.get("topic", "Basic script"),
            script_type=request.get("script_type", "ServerScript"),
            difficulty_level=request.get("difficulty", "intermediate"),
        )

        return {
            "success": True,
            "script": script.code if hasattr(script, "code") else str(script),
            "metadata": script.metadata if hasattr(script, "metadata") else {},
            "api_key_id": api_key_validation.key_id,
            "rate_limit_remaining": api_key_validation.rate_limit_remaining,
        }

    except Exception as e:
        logger.error(f"Script generation failed: {e}")
        raise HTTPException(status_code=500, detail="Script generation failed")


@router.post("/roblox/validate-script")
async def validate_script_with_api_key(
    request: dict,
    api_key_validation: APIKeyValidation = Depends(
        lambda x_api_key: verify_api_key(x_api_key, required_scope=APIKeyScope.SCRIPT_VALIDATE)
    ),
):
    """
    Validate a Roblox script for security issues using API key authentication.

    This endpoint is designed for Roblox Studio plugins.
    Requires 'script.validate' scope.
    """
    try:
        logger.info(f"API key {api_key_validation.key_id} validating script")

        # Import security validation agent
        from core.agents.roblox.roblox_security_validation_agent import (
            RobloxSecurityValidationAgent,
        )

        agent = RobloxSecurityValidationAgent(
            llm=None, strict_mode=request.get("strict_mode", True)
        )
        report = agent.validate_script(
            script_code=request.get("script", ""),
            script_type=request.get("script_type", "ServerScript"),
        )

        return {
            "success": True,
            "risk_score": report.risk_score,
            "vulnerabilities": [v.dict() for v in report.vulnerabilities],
            "compliance_status": report.compliance_status.dict(),
            "recommendations": report.recommendations,
            "api_key_id": api_key_validation.key_id,
            "rate_limit_remaining": api_key_validation.rate_limit_remaining,
        }

    except Exception as e:
        logger.error(f"Script validation failed: {e}")
        raise HTTPException(status_code=500, detail="Script validation failed")


@router.get("/roblox/content")
async def get_educational_content_with_api_key(
    subject: str = Query("general", description="Educational subject"),
    grade_level: str = Query("middle", description="Grade level"),
    api_key_validation: APIKeyValidation = Depends(
        lambda x_api_key: verify_api_key(x_api_key, required_scope=APIKeyScope.CONTENT_ACCESS)
    ),
):
    """
    Get educational content for Roblox using API key authentication.

    This endpoint is designed for Roblox Studio plugins.
    Requires 'content.access' scope.
    """
    try:
        logger.info(f"API key {api_key_validation.key_id} accessing content")

        # Import content generation agent
        from core.agents.roblox.roblox_content_generation_agent import RobloxContentGenerationAgent

        agent = RobloxContentGenerationAgent(llm=None)
        content = agent.generate_educational_content(
            subject=subject, grade_level=grade_level, format_type="interactive"
        )

        return {
            "success": True,
            "content": content.dict() if hasattr(content, "dict") else content,
            "api_key_id": api_key_validation.key_id,
            "rate_limit_remaining": api_key_validation.rate_limit_remaining,
        }

    except Exception as e:
        logger.error(f"Content retrieval failed: {e}")
        raise HTTPException(status_code=500, detail="Content retrieval failed")


@router.get("/usage-stats")
async def get_api_key_usage_stats(
    key_id: str,
    current_user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """
    Get usage statistics for a specific API key.

    Requires JWT authentication and ownership of the key.
    """
    try:
        # Verify ownership
        api_key_manager = await get_api_key_manager()
        keys = await api_key_manager.list_api_keys(db, current_user.sub)

        key_found = any(k.key_id == key_id for k in keys)
        if not key_found:
            raise HTTPException(status_code=404, detail="API key not found")

        # Get usage stats from Redis
        # This would be expanded with more detailed analytics
        return {
            "key_id": key_id,
            "total_requests": next((k.usage_count for k in keys if k.key_id == key_id), 0),
            "rate_limit": next((k.rate_limit for k in keys if k.key_id == key_id), 0),
            "message": "Detailed analytics coming soon",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get usage stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to get usage statistics")
