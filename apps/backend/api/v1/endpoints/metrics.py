"""
Enhanced Dashboard Metrics API - 2025 Implementation
Provides comprehensive metrics with rate limiting, caching, and monitoring.

Features:
- Redis-based caching
- Rate limiting per user tier
- Async database queries
- Comprehensive error handling
- OpenAPI documentation
"""

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.responses import JSONResponse
from typing import Optional, Dict, Any
from datetime import datetime, timezone
import logging

from pydantic import BaseModel, Field, ConfigDict

from apps.backend.core.cache import RedisCache
from apps.backend.core.rate_limiter import RateLimiter, RateLimitConfig
from apps.backend.core.config import settings
from apps.backend.services.dashboard_metrics_service import (
    DashboardMetricsService,
    DashboardMetricsResponse,
    ActivityMetrics,
)
from apps.backend.api.auth.auth import get_current_user
from apps.backend.models.schemas import User
from apps.backend.core.dependencies import get_db_session
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

# Initialize router
metrics_router = APIRouter(prefix="/metrics", tags=["Metrics"])


# ============================================================================
# Pydantic v2 Models
# ============================================================================


class MetricsExportRequest(BaseModel):
    """Request model for metrics export"""

    model_config = ConfigDict()

    format: str = Field(default="json", description="Export format: json, csv, excel")
    date_range: str = Field(default="7d", description="Date range: 24h, 7d, 30d, 90d")
    metric_types: list[str] = Field(
        default_factory=lambda: ["users", "content", "engagement"],
        description="Metric types to include",
    )


class MetricsExportResponse(BaseModel):
    """Response model for metrics export"""

    model_config = ConfigDict()

    download_url: str = Field(..., description="URL to download export file")
    expires_at: datetime = Field(..., description="Expiration time for download URL")
    file_size: int = Field(..., description="File size in bytes")
    format: str = Field(..., description="Export format")


class StatisticsResponse(BaseModel):
    """Response model for statistics"""

    model_config = ConfigDict()

    period: str = Field(..., description="Time period: 24h, 7d, 30d")
    statistics: Dict[str, Any] = Field(..., description="Statistical data")
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# ============================================================================
# Dependency Injection
# ============================================================================


async def get_metrics_service(request: Request) -> DashboardMetricsService:
    """Get dashboard metrics service instance."""
    # Get Redis cache from app state (should be initialized at startup)
    if not hasattr(request.app.state, "redis_cache"):
        # Initialize cache if not exists
        from apps.backend.core.cache import RedisConnectionManager
        manager = RedisConnectionManager()
        await manager.initialize()
        cache = RedisCache(manager.client)
        request.app.state.redis_cache = cache
    else:
        cache = request.app.state.redis_cache

    return DashboardMetricsService(cache)


async def get_rate_limiter(request: Request) -> RateLimiter:
    """Get rate limiter instance."""
    # Get Redis client from app state
    if not hasattr(request.app.state, "redis_client"):
        from apps.backend.core.cache import RedisConnectionManager
        manager = RedisConnectionManager()
        await manager.initialize()
        request.app.state.redis_client = manager.client

    # Configure rate limits for metrics endpoints
    config = RateLimitConfig(
        requests_per_minute=30,  # 30 requests per minute
        requests_per_hour=500,  # 500 requests per hour
        endpoint_limits={
            "/api/v1/metrics/dashboard": {"requests_per_minute": 10},
            "/api/v1/metrics/activity": {"requests_per_minute": 20},
            "/api/v1/metrics/export": {"requests_per_hour": 10},
        },
    )

    return RateLimiter(request.app.state.redis_client, config)


# ============================================================================
# API Endpoints
# ============================================================================


@metrics_router.get(
    "/dashboard",
    response_model=DashboardMetricsResponse,
    summary="Get comprehensive dashboard metrics",
    description="""
    Returns comprehensive dashboard metrics including:
    - User metrics (total, active, growth)
    - Content metrics (published, draft, creation stats)
    - Engagement metrics (DAU, session duration, lessons)
    - System metrics (performance, cache, errors)
    - Time-series trends

    **Features:**
    - Cached for 15 minutes
    - Rate limited: 10 requests/minute
    - Multi-tenant aware
    - Force refresh with `?force_refresh=true`
    """,
    responses={
        200: {"description": "Metrics retrieved successfully"},
        429: {"description": "Rate limit exceeded"},
        500: {"description": "Internal server error"},
    },
)
async def get_dashboard_metrics(
    request: Request,
    response: Response,
    force_refresh: bool = False,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
    metrics_service: DashboardMetricsService = Depends(get_metrics_service),
    rate_limiter: RateLimiter = Depends(get_rate_limiter),
) -> DashboardMetricsResponse:
    """
    Get comprehensive dashboard metrics.

    Args:
        force_refresh: Force cache refresh
        current_user: Authenticated user
        session: Database session
        metrics_service: Dashboard metrics service

    Returns:
        DashboardMetricsResponse with all metrics
    """
    try:
        # Apply rate limiting
        identifier = f"user:{current_user.id}"
        rate_limit_result = await rate_limiter.check_rate_limit(
            identifier=identifier,
            endpoint="/api/v1/metrics/dashboard",
            user_tier=getattr(current_user, "tier", "free"),
        )

        if not rate_limit_result.allowed:
            # Add rate limit headers
            for header, value in rate_limit_result.headers.items():
                response.headers[header] = value

            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "error": "Rate limit exceeded",
                    "retry_after": rate_limit_result.retry_after,
                    "limit": rate_limit_result.limit,
                    "remaining": rate_limit_result.remaining,
                },
            )

        # Add rate limit headers to successful response
        for header, value in rate_limit_result.headers.items():
            response.headers[header] = value

        # Get organization ID from user (multi-tenancy)
        organization_id = getattr(current_user, "organization_id", None)

        # Fetch metrics
        metrics = await metrics_service.get_dashboard_metrics(
            session=session,
            user_id=current_user.id,
            organization_id=organization_id,
            force_refresh=force_refresh,
        )

        logger.info(
            f"Dashboard metrics retrieved for user {current_user.username}",
            extra={
                "user_id": current_user.id,
                "organization_id": organization_id,
                "cache_hit": not force_refresh,
            },
        )

        return metrics

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching dashboard metrics: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve dashboard metrics",
        )


@metrics_router.get(
    "/activity",
    response_model=ActivityMetrics,
    summary="Get recent activity metrics",
    description="""
    Returns recent activity metrics (last 24 hours):
    - Recent lessons count
    - Recent assessments count
    - Recent messages count
    - Top performing content
    - Hourly activity trend

    **Features:**
    - Cached for 1 minute (frequently changing data)
    - Rate limited: 20 requests/minute
    - Real-time activity tracking
    """,
)
async def get_activity_metrics(
    request: Request,
    response: Response,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
    metrics_service: DashboardMetricsService = Depends(get_metrics_service),
    rate_limiter: RateLimiter = Depends(get_rate_limiter),
) -> ActivityMetrics:
    """Get recent activity metrics."""
    try:
        # Apply rate limiting
        identifier = f"user:{current_user.id}"
        rate_limit_result = await rate_limiter.check_rate_limit(
            identifier=identifier,
            endpoint="/api/v1/metrics/activity",
            user_tier=getattr(current_user, "tier", "free"),
        )

        if not rate_limit_result.allowed:
            for header, value in rate_limit_result.headers.items():
                response.headers[header] = value

            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "error": "Rate limit exceeded",
                    "retry_after": rate_limit_result.retry_after,
                },
            )

        # Add rate limit headers
        for header, value in rate_limit_result.headers.items():
            response.headers[header] = value

        organization_id = getattr(current_user, "organization_id", None)

        activity = await metrics_service.get_activity_metrics(
            session=session,
            user_id=current_user.id,
            organization_id=organization_id,
        )

        return activity

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching activity metrics: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve activity metrics",
        )


@metrics_router.get(
    "/statistics",
    response_model=StatisticsResponse,
    summary="Get statistical data for a time period",
    description="""
    Returns statistical analysis for specified time period.

    **Supported periods:**
    - 24h: Last 24 hours
    - 7d: Last 7 days
    - 30d: Last 30 days
    - 90d: Last 90 days

    **Statistics include:**
    - Min, max, average values
    - Percentiles (P50, P95, P99)
    - Standard deviation
    - Growth trends
    """,
)
async def get_statistics(
    period: str = "7d",
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> StatisticsResponse:
    """Get statistical data for specified time period."""
    try:
        # Validate period
        valid_periods = ["24h", "7d", "30d", "90d"]
        if period not in valid_periods:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid period. Must be one of: {', '.join(valid_periods)}",
            )

        # Placeholder statistics - would calculate from actual data
        statistics = {
            "period": period,
            "user_growth": {
                "min": 100,
                "max": 250,
                "average": 175,
                "p50": 170,
                "p95": 240,
                "p99": 245,
                "std_dev": 35.2,
            },
            "content_creation": {
                "min": 10,
                "max": 45,
                "average": 28,
                "p50": 26,
                "p95": 42,
                "p99": 44,
                "std_dev": 8.5,
            },
            "api_performance": {
                "min": 85.0,
                "max": 210.0,
                "average": 145.3,
                "p50": 140.0,
                "p95": 180.0,
                "p99": 200.0,
                "std_dev": 25.8,
            },
        }

        return StatisticsResponse(period=period, statistics=statistics)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching statistics: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve statistics",
        )


@metrics_router.post(
    "/export",
    response_model=MetricsExportResponse,
    summary="Export metrics data",
    description="""
    Export metrics data in various formats.

    **Supported formats:**
    - json: JSON export
    - csv: CSV export
    - excel: Excel spreadsheet

    **Rate limited:** 10 requests/hour
    """,
)
async def export_metrics(
    request: Request,
    response: Response,
    export_request: MetricsExportRequest,
    current_user: User = Depends(get_current_user),
    rate_limiter: RateLimiter = Depends(get_rate_limiter),
) -> MetricsExportResponse:
    """Export metrics data."""
    try:
        # Apply strict rate limiting for exports
        identifier = f"user:{current_user.id}"
        rate_limit_result = await rate_limiter.check_rate_limit(
            identifier=identifier,
            endpoint="/api/v1/metrics/export",
            custom_limit=10,  # Only 10 exports per hour
        )

        if not rate_limit_result.allowed:
            for header, value in rate_limit_result.headers.items():
                response.headers[header] = value

            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "error": "Export rate limit exceeded",
                    "retry_after": rate_limit_result.retry_after,
                },
            )

        # Validate format
        valid_formats = ["json", "csv", "excel"]
        if export_request.format not in valid_formats:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid format. Must be one of: {', '.join(valid_formats)}",
            )

        # Generate export (placeholder - would actually generate file)
        from datetime import timedelta
        import uuid

        export_id = str(uuid.uuid4())
        download_url = f"/api/v1/metrics/download/{export_id}"
        expires_at = datetime.now(timezone.utc) + timedelta(hours=24)

        logger.info(
            f"Metrics export requested by {current_user.username}",
            extra={
                "user_id": current_user.id,
                "format": export_request.format,
                "date_range": export_request.date_range,
            },
        )

        return MetricsExportResponse(
            download_url=download_url,
            expires_at=expires_at,
            file_size=102400,  # Placeholder
            format=export_request.format,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting metrics: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to export metrics",
        )


@metrics_router.post(
    "/invalidate-cache",
    summary="Invalidate metrics cache",
    description="""
    Invalidate cached metrics data.

    **Admin only endpoint**
    Forces refresh of all cached metrics data.
    """,
)
async def invalidate_metrics_cache(
    request: Request,
    current_user: User = Depends(get_current_user),
    metrics_service: DashboardMetricsService = Depends(get_metrics_service),
) -> Dict[str, str]:
    """Invalidate metrics cache (admin only)."""
    try:
        # Check if user is admin
        if not getattr(current_user, "is_admin", False):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin access required",
            )

        organization_id = getattr(current_user, "organization_id", None)
        await metrics_service.invalidate_cache(organization_id)

        logger.info(
            f"Metrics cache invalidated by admin {current_user.username}",
            extra={"user_id": current_user.id, "organization_id": organization_id},
        )

        return {
            "status": "success",
            "message": "Metrics cache invalidated",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error invalidating cache: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to invalidate cache",
        )


# Export router
__all__ = ["metrics_router"]
