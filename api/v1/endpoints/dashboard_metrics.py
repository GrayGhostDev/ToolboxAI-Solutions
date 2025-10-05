"""
Dashboard Metrics API Endpoints

Provides comprehensive metrics and analytics for the dashboard,
with Redis caching and multi-tenant isolation.

Endpoints:
- GET /api/v1/dashboard/metrics - Overall metrics
- GET /api/v1/dashboard/activity - Recent activity
- GET /api/v1/dashboard/statistics - Detailed statistics
- POST /api/v1/dashboard/export - Export metrics data
"""

from datetime import datetime, timedelta, timezone
from typing import Optional, List, Dict, Any
from uuid import UUID

from fastapi import APIRouter, Depends, Query, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_

from apps.backend.core.dependencies.database import get_async_session
from apps.backend.core.dependencies.auth import get_current_user
from apps.backend.services.cache_service import cached, cache_service
from apps.backend.core.logging import logging_manager
from database.models.models import User, EducationalContent, Lesson, Assessment

logger = logging_manager.get_logger(__name__)

router = APIRouter(prefix="/dashboard", tags=["Dashboard Metrics"])


# ============================================================================
# Pydantic Models
# ============================================================================

class UserMetrics(BaseModel):
    """User-related metrics"""
    total: int = Field(..., description="Total number of users")
    active_today: int = Field(..., description="Users active in last 24 hours")
    active_week: int = Field(..., description="Users active in last 7 days")
    active_month: int = Field(..., description="Users active in last 30 days")
    growth_rate: float = Field(..., description="Month-over-month growth percentage")
    by_role: Dict[str, int] = Field(default_factory=dict, description="Users by role")


class ContentMetrics(BaseModel):
    """Content-related metrics"""
    total: int = Field(..., description="Total content items")
    published: int = Field(..., description="Published content")
    draft: int = Field(..., description="Draft content")
    pending_review: int = Field(..., description="Content pending review")
    avg_engagement: float = Field(..., description="Average engagement score")
    recent_uploads: int = Field(..., description="Uploads in last 24 hours")


class EngagementMetrics(BaseModel):
    """User engagement metrics"""
    daily_active_users: int = Field(..., description="Daily active users")
    avg_session_duration: float = Field(..., description="Average session duration (minutes)")
    total_sessions: int = Field(..., description="Total sessions today")
    lessons_completed: int = Field(..., description="Lessons completed today")
    assessments_taken: int = Field(..., description="Assessments taken today")


class SystemMetrics(BaseModel):
    """System health metrics"""
    uptime_seconds: float = Field(..., description="System uptime in seconds")
    cache_hit_rate: float = Field(..., description="Cache hit rate percentage")
    api_response_time_ms: float = Field(..., description="Average API response time")
    error_rate: float = Field(..., description="Error rate percentage")


class DashboardMetricsResponse(BaseModel):
    """Complete dashboard metrics response"""
    status: str = Field(default="success", description="Response status")
    data: Dict[str, Any] = Field(..., description="Metrics data")
    metadata: Dict[str, Any] = Field(..., description="Response metadata")

    class Config:
        schema_extra = {
            "example": {
                "status": "success",
                "data": {
                    "users": {"total": 1234, "active_today": 567},
                    "content": {"total": 890, "published": 456},
                    "engagement": {"daily_active_users": 234}
                },
                "metadata": {
                    "timestamp": "2025-10-01T20:00:00Z",
                    "cache_ttl": 300,
                    "cached": True
                }
            }
        }


class ActivityItem(BaseModel):
    """Recent activity item"""
    id: str
    type: str = Field(..., description="Activity type (content, lesson, assessment)")
    action: str = Field(..., description="Action performed (created, updated, completed)")
    user_id: str
    user_name: str
    timestamp: datetime
    details: Dict[str, Any] = Field(default_factory=dict)


class ActivityResponse(BaseModel):
    """Recent activity response"""
    status: str = "success"
    data: List[ActivityItem]
    metadata: Dict[str, Any]


# ============================================================================
# Helper Functions
# ============================================================================

async def calculate_user_metrics(
    session: AsyncSession,
    organization_id: UUID
) -> UserMetrics:
    """Calculate user-related metrics"""
    now = datetime.now(timezone.utc)
    day_ago = now - timedelta(days=1)
    week_ago = now - timedelta(days=7)
    month_ago = now - timedelta(days=30)

    # Total users
    total_query = select(func.count(User.id)).where(
        User.organization_id == organization_id,
        User.deleted_at.is_(None)
    )
    total = (await session.execute(total_query)).scalar() or 0

    # Active users by timeframe
    active_today_query = total_query.where(User.last_login >= day_ago)
    active_week_query = total_query.where(User.last_login >= week_ago)
    active_month_query = total_query.where(User.last_login >= month_ago)

    active_today = (await session.execute(active_today_query)).scalar() or 0
    active_week = (await session.execute(active_week_query)).scalar() or 0
    active_month = (await session.execute(active_month_query)).scalar() or 0

    # Users by role
    role_query = select(
        User.role,
        func.count(User.id)
    ).where(
        User.organization_id == organization_id,
        User.deleted_at.is_(None)
    ).group_by(User.role)

    role_results = (await session.execute(role_query)).all()
    by_role = {role: count for role, count in role_results}

    # Calculate growth rate (simplified)
    two_months_ago = now - timedelta(days=60)
    previous_month_query = total_query.where(User.created_at < month_ago)
    previous_month_total = (await session.execute(previous_month_query)).scalar() or 1

    current_month_new = total - previous_month_total
    growth_rate = (current_month_new / previous_month_total * 100) if previous_month_total > 0 else 0

    return UserMetrics(
        total=total,
        active_today=active_today,
        active_week=active_week,
        active_month=active_month,
        growth_rate=round(growth_rate, 2),
        by_role=by_role
    )


async def calculate_content_metrics(
    session: AsyncSession,
    organization_id: UUID
) -> ContentMetrics:
    """Calculate content-related metrics"""
    now = datetime.now(timezone.utc)
    day_ago = now - timedelta(days=1)

    # Total content
    total_query = select(func.count(EducationalContent.id)).where(
        EducationalContent.organization_id == organization_id,
        EducationalContent.deleted_at.is_(None)
    )
    total = (await session.execute(total_query)).scalar() or 0

    # Content by status
    published_query = total_query.where(EducationalContent.status == "published")
    draft_query = total_query.where(EducationalContent.status == "draft")
    pending_query = total_query.where(EducationalContent.status == "pending_review")

    published = (await session.execute(published_query)).scalar() or 0
    draft = (await session.execute(draft_query)).scalar() or 0
    pending = (await session.execute(pending_query)).scalar() or 0

    # Recent uploads
    recent_query = total_query.where(EducationalContent.created_at >= day_ago)
    recent_uploads = (await session.execute(recent_query)).scalar() or 0

    # Average engagement (mock for now)
    avg_engagement = 7.5  # TODO: Calculate from actual engagement data

    return ContentMetrics(
        total=total,
        published=published,
        draft=draft,
        pending_review=pending,
        avg_engagement=avg_engagement,
        recent_uploads=recent_uploads
    )


async def calculate_engagement_metrics(
    session: AsyncSession,
    organization_id: UUID
) -> EngagementMetrics:
    """Calculate engagement metrics"""
    # Mock data for now - would integrate with actual session tracking
    return EngagementMetrics(
        daily_active_users=234,
        avg_session_duration=25.5,
        total_sessions=456,
        lessons_completed=89,
        assessments_taken=45
    )


async def get_system_metrics() -> SystemMetrics:
    """Get system health metrics"""
    # Get cache statistics
    cache_stats = await cache_service.get_stats()

    return SystemMetrics(
        uptime_seconds=0.0,  # TODO: Calculate actual uptime
        cache_hit_rate=cache_stats.get("hit_rate_percent", 0.0),
        api_response_time_ms=150.0,  # TODO: Get from Prometheus
        error_rate=0.5  # TODO: Get from error tracking
    )


# ============================================================================
# API Endpoints
# ============================================================================

@router.get("/metrics", response_model=DashboardMetricsResponse)
@cached(namespace="dashboard", ttl=300)  # Cache for 5 minutes
async def get_dashboard_metrics(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """
    Get comprehensive dashboard metrics

    Returns overall metrics including:
    - User statistics
    - Content metrics
    - Engagement data
    - System health

    Cached for 5 minutes per organization.
    """
    logger.info(
        f"Fetching dashboard metrics for organization {current_user.organization_id}",
        extra={"user_id": str(current_user.id)}
    )

    try:
        # Calculate all metrics concurrently
        user_metrics = await calculate_user_metrics(session, current_user.organization_id)
        content_metrics = await calculate_content_metrics(session, current_user.organization_id)
        engagement_metrics = await calculate_engagement_metrics(session, current_user.organization_id)
        system_metrics = await get_system_metrics()

        return DashboardMetricsResponse(
            status="success",
            data={
                "users": user_metrics.dict(),
                "content": content_metrics.dict(),
                "engagement": engagement_metrics.dict(),
                "system": system_metrics.dict()
            },
            metadata={
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "organization_id": str(current_user.organization_id),
                "cache_ttl": 300,
                "cached": True
            }
        )

    except Exception as e:
        logger.error(
            f"Error fetching dashboard metrics: {e}",
            extra={"user_id": str(current_user.id)},
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch dashboard metrics"
        )


@router.get("/activity", response_model=ActivityResponse)
@cached(namespace="dashboard", ttl=60)  # Cache for 1 minute
async def get_recent_activity(
    limit: int = Query(default=20, ge=1, le=100),
    activity_type: Optional[str] = Query(default=None),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """
    Get recent activity for the organization

    Args:
        limit: Maximum number of activities to return (1-100)
        activity_type: Filter by activity type (content, lesson, assessment)

    Returns recent activities with user information.
    Cached for 1 minute per organization.
    """
    logger.info(
        f"Fetching recent activity for organization {current_user.organization_id}",
        extra={"user_id": str(current_user.id), "limit": limit}
    )

    # Mock activity data - would query from audit logs
    activities = [
        ActivityItem(
            id="act_001",
            type="content",
            action="created",
            user_id="user_123",
            user_name="John Doe",
            timestamp=datetime.now(timezone.utc) - timedelta(minutes=5),
            details={"content_title": "Introduction to Python"}
        ),
        ActivityItem(
            id="act_002",
            type="lesson",
            action="completed",
            user_id="user_456",
            user_name="Jane Smith",
            timestamp=datetime.now(timezone.utc) - timedelta(minutes=15),
            details={"lesson_title": "Variables and Data Types"}
        )
    ]

    return ActivityResponse(
        status="success",
        data=activities[:limit],
        metadata={
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "count": len(activities),
            "limit": limit,
            "organization_id": str(current_user.organization_id)
        }
    )


@router.get("/statistics")
async def get_detailed_statistics(
    start_date: Optional[datetime] = Query(default=None),
    end_date: Optional[datetime] = Query(default=None),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """
    Get detailed statistics for a specific date range

    Args:
        start_date: Start of date range (default: 30 days ago)
        end_date: End of date range (default: now)

    Returns comprehensive statistics including trends and comparisons.
    """
    now = datetime.now(timezone.utc)
    start = start_date or (now - timedelta(days=30))
    end = end_date or now

    logger.info(
        f"Fetching statistics for {start} to {end}",
        extra={"user_id": str(current_user.id)}
    )

    # Mock detailed statistics
    return {
        "status": "success",
        "data": {
            "date_range": {
                "start": start.isoformat(),
                "end": end.isoformat()
            },
            "user_growth": [
                {"date": "2025-10-01", "new_users": 12, "total_users": 1234}
            ],
            "content_creation": [
                {"date": "2025-10-01", "new_content": 5, "total_content": 890}
            ],
            "engagement_trends": {
                "sessions_per_day": [45, 52, 48, 61, 55],
                "avg_session_duration": [22, 25, 23, 28, 26]
            }
        },
        "metadata": {
            "timestamp": now.isoformat()
        }
    }


@router.post("/export")
async def export_metrics(
    format: str = Query(default="json", regex="^(json|csv|xlsx)$"),
    include_history: bool = Query(default=False),
    current_user: User = Depends(get_current_user)
):
    """
    Export metrics data in specified format

    Args:
        format: Export format (json, csv, xlsx)
        include_history: Include historical data (30 days)

    Returns download URL or inline data depending on format.
    """
    logger.info(
        f"Exporting metrics in {format} format",
        extra={"user_id": str(current_user.id)}
    )

    # Mock export response
    return {
        "status": "success",
        "data": {
            "export_format": format,
            "download_url": f"/exports/metrics_{datetime.now().strftime('%Y%m%d')}. {format}",
            "expires_at": (datetime.now(timezone.utc) + timedelta(hours=24)).isoformat()
        }
    }
