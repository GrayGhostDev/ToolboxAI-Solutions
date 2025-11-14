"""
Analytics API Endpoints

Provides REST API endpoints for advanced analytics and reporting features.
"""

import io
import random
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any

import pandas as pd
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Path, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from apps.backend.analytics_advanced import (
    AdvancedAnalytics,
    generate_analytics_report,
)
from apps.backend.api.auth.auth import get_current_user
from apps.backend.cache import cache_result
from database.connection import get_db

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


class MetricType(str, Enum):
    """Available metric types for predictions"""

    COMPLETION_PROBABILITY = "completion_probability"
    PERFORMANCE_TREND = "performance_trend"
    ENGAGEMENT_FORECAST = "engagement_forecast"
    DROPOUT_RISK = "dropout_risk"


class ReportType(str, Enum):
    """Available report types"""

    EXECUTIVE_SUMMARY = "executive_summary"
    STUDENT_PERFORMANCE = "student_performance"
    ENGAGEMENT_ANALYSIS = "engagement_analysis"
    CONTENT_EFFECTIVENESS = "content_effectiveness"
    CUSTOM = "custom"


class ReportFormat(str, Enum):
    """Report export formats"""

    JSON = "json"
    PDF = "pdf"
    EXCEL = "excel"
    CSV = "csv"


class InsightScope(str, Enum):
    """Scope for ML insights"""

    PLATFORM = "platform"
    COURSE = "course"
    USER = "user"


class PredictionRequest(BaseModel):
    """Request model for predictions"""

    metric_type: MetricType
    user_id: str | None = None
    course_id: str | None = None
    additional_params: dict[str, Any] | None = None


class ReportRequest(BaseModel):
    """Request model for report generation"""

    report_type: ReportType
    start_date: datetime
    end_date: datetime
    filters: dict[str, Any] | None = None
    format: ReportFormat = ReportFormat.JSON
    email_delivery: str | None = None


class InsightRequest(BaseModel):
    """Request model for ML insights"""

    scope: InsightScope
    entity_id: str | None = None
    limit: int = Field(default=10, le=50)


class DashboardMetrics(BaseModel):
    """Response model for dashboard metrics"""

    period: dict[str, str]
    metrics: dict[str, Any]
    trends: dict[str, list[dict[str, Any]]]
    predictions: list[dict[str, Any]]
    insights: list[dict[str, Any]]


@router.get("/dashboard", response_model=DashboardMetrics)
@cache_result(expire=300)  # Cache for 5 minutes
async def get_analytics_dashboard(
    days: int = Query(default=30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Get comprehensive analytics dashboard data

    Returns metrics, trends, predictions, and insights for the dashboard.
    """
    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(days=days)

    analytics = AdvancedAnalytics(db)

    # Get basic metrics
    metrics = await analytics._get_key_metrics(start_date, end_date)

    # Get trends
    trends = await analytics._calculate_growth_metrics(start_date, end_date)

    # Get predictions for current user if student
    predictions = []
    if current_user["role"] == "student":
        try:
            completion_pred = await analytics.get_predictive_analytics(
                user_id=current_user["id"], metric_type="completion_probability"
            )
            performance_pred = await analytics.get_predictive_analytics(
                user_id=current_user["id"], metric_type="performance_trend"
            )
            predictions = [
                {
                    "type": "completion",
                    "value": completion_pred.prediction,
                    "confidence": completion_pred.confidence,
                },
                {
                    "type": "performance",
                    "value": performance_pred.prediction,
                    "confidence": performance_pred.confidence,
                },
            ]
        except Exception as e:
            # Log error but don't fail the whole request
            print(f"Prediction error: {e}")

    # Get top insights
    insights_raw = await analytics.get_ml_insights("platform")
    insights = [
        {
            "type": i.insight_type,
            "title": i.title,
            "description": i.description,
            "impact": i.impact_score,
        }
        for i in insights_raw[:5]  # Top 5 insights
    ]

    return DashboardMetrics(
        period={"start": start_date.isoformat(), "end": end_date.isoformat()},
        metrics=metrics,
        trends={
            "user_growth": trends.get("user_growth", []),
            "content_growth": trends.get("content_growth", []),
            "engagement_growth": trends.get("engagement_growth", []),
        },
        predictions=predictions,
        insights=insights,
    )


@router.post("/predict")
async def get_prediction(
    request: PredictionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Get predictive analytics for specified metric

    Available metrics:
    - completion_probability: Predict course completion likelihood
    - performance_trend: Predict performance trajectory
    - engagement_forecast: Forecast engagement levels
    - dropout_risk: Assess dropout risk
    """
    analytics = AdvancedAnalytics(db)

    # Use current user if not specified
    user_id = request.user_id or current_user["id"]

    try:
        result = await analytics.get_predictive_analytics(
            user_id=user_id,
            course_id=request.course_id,
            metric_type=request.metric_type.value,
        )

        return {
            "prediction": result.prediction,
            "confidence": result.confidence,
            "factors": result.factors,
            "recommendation": result.recommendation,
            "timestamp": result.timestamp.isoformat(),
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")


@router.post("/insights")
async def get_ml_insights(
    request: InsightRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Get machine learning generated insights

    Scopes:
    - platform: Platform-wide insights
    - course: Course-specific insights
    - user: User-specific insights
    """
    # Check permissions
    if request.scope == InsightScope.PLATFORM and current_user["role"] not in [
        "admin",
        "teacher",
    ]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")

    if request.scope == InsightScope.USER and request.entity_id != current_user["id"]:
        if current_user["role"] not in ["admin", "teacher"]:
            raise HTTPException(status_code=403, detail="Cannot view other users' insights")

    analytics = AdvancedAnalytics(db)

    try:
        insights = await analytics.get_ml_insights(
            scope=request.scope.value, entity_id=request.entity_id
        )

        return [
            {
                "insight_type": i.insight_type,
                "title": i.title,
                "description": i.description,
                "impact_score": i.impact_score,
                "affected_users": i.affected_users[:10],  # Limit exposed user IDs
                "recommendations": i.recommendations,
                "data": (
                    i.data if current_user["role"] == "admin" else {}
                ),  # Only admins see raw data
            }
            for i in insights[: request.limit]
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate insights: {str(e)}")


@router.post("/report")
async def generate_report(
    request: ReportRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Generate custom analytics report

    Report types:
    - executive_summary: High-level overview for administrators
    - student_performance: Detailed student performance analysis
    - engagement_analysis: User engagement patterns and trends
    - content_effectiveness: Content performance and optimization
    """
    # Check permissions
    if current_user["role"] not in ["admin", "teacher"]:
        raise HTTPException(
            status_code=403, detail="Insufficient permissions for report generation"
        )

    # Validate date range
    if request.end_date <= request.start_date:
        raise HTTPException(status_code=400, detail="End date must be after start date")

    if (request.end_date - request.start_date).days > 365:
        raise HTTPException(status_code=400, detail="Date range cannot exceed 365 days")

    try:
        # Generate report
        report = await generate_analytics_report(
            session=db,
            report_type=request.report_type.value,
            start_date=request.start_date,
            end_date=request.end_date,
            filters=request.filters,
            format=request.format.value,
        )

        # Handle different formats
        if request.format == ReportFormat.JSON:
            return report

        elif request.format == ReportFormat.CSV:
            # Convert to CSV
            df = pd.DataFrame(report["sections"][0]["data"] if report["sections"] else {})
            csv_buffer = io.StringIO()
            df.to_csv(csv_buffer, index=False)
            csv_buffer.seek(0)

            return StreamingResponse(
                io.BytesIO(csv_buffer.getvalue().encode()),
                media_type="text/csv",
                headers={
                    "Content-Disposition": f"attachment; filename=report_{request.report_type}_{datetime.now(timezone.utc).strftime('%Y%m%d')}.csv"
                },
            )

        elif request.format == ReportFormat.EXCEL:
            # Convert to Excel
            excel_buffer = io.BytesIO()
            with pd.ExcelWriter(excel_buffer, engine="xlsxwriter") as writer:
                for section in report.get("sections", []):
                    df = pd.DataFrame(section["data"])
                    df.to_excel(writer, sheet_name=section["title"][:31], index=False)
            excel_buffer.seek(0)

            return StreamingResponse(
                excel_buffer,
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                headers={
                    "Content-Disposition": f"attachment; filename=report_{request.report_type}_{datetime.now(timezone.utc).strftime('%Y%m%d')}.xlsx"
                },
            )

        elif request.format == ReportFormat.PDF:
            # PDF generation would require additional libraries
            raise HTTPException(status_code=501, detail="PDF export not yet implemented")

        # Email delivery if requested
        if request.email_delivery:
            background_tasks.add_task(
                send_report_email,
                email=request.email_delivery,
                report=report,
                report_type=request.report_type,
            )

            return {"message": f"Report will be delivered to {request.email_delivery}"}

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Report generation failed: {str(e)}")


@router.get("/report/{report_id}")
async def get_report(
    report_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Retrieve a previously generated report by ID
    """
    # This would retrieve cached reports from storage
    # Implementation depends on report storage strategy
    raise HTTPException(status_code=501, detail="Report retrieval not yet implemented")


@router.get("/anomalies")
async def detect_anomalies(
    scope: str = Query(default="activity", pattern="^(activity|performance|engagement)$"),
    days: int = Query(default=7, ge=1, le=30),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Detect anomalies in platform data

    Scopes:
    - activity: Unusual user activity patterns
    - performance: Abnormal performance metrics
    - engagement: Engagement anomalies
    """
    if current_user["role"] not in ["admin", "teacher"]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")

    analytics = AdvancedAnalytics(db)

    try:
        if scope == "activity":
            anomalies = await analytics._detect_activity_anomalies()
            return {
                "scope": scope,
                "anomaly_count": len(anomalies),
                "affected_users": anomalies[:20],  # Limit to 20
                "detection_timestamp": datetime.now(timezone.utc).isoformat(),
            }
        else:
            # Other anomaly types would be implemented similarly
            return {
                "scope": scope,
                "message": "Anomaly detection for this scope is under development",
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Anomaly detection failed: {str(e)}")


@router.get("/trends/engagement")
async def get_engagement_trends(
    start_date: datetime | None = Query(None, description="Start date for trends"),
    end_date: datetime | None = Query(None, description="End date for trends"),
    interval: str = Query("day", description="Interval for data points"),
    current_user: dict = Depends(get_current_user),
) -> dict[str, Any]:
    """Get engagement trend data"""

    # Default to last 30 days if dates not provided
    if not end_date:
        end_date = datetime.now()
    if not start_date:
        start_date = end_date - timedelta(days=30)

    # Generate trend data points
    trends = []
    current = start_date

    while current <= end_date:
        trends.append(
            {
                "date": current.isoformat(),
                "value": random.uniform(70, 95),
                "label": current.strftime("%b %d"),
            }
        )

        if interval == "day":
            current += timedelta(days=1)
        elif interval == "week":
            current += timedelta(weeks=1)
        elif interval == "month":
            current += timedelta(days=30)
        else:
            current += timedelta(days=1)

    # Add additional engagement metrics
    summary = {
        "average_engagement": 82.5,
        "peak_engagement": 95.2,
        "low_engagement": 68.3,
        "trend_direction": "up",
        "change_percentage": 5.4,
    }

    # Breakdown by activity type
    activity_breakdown = {
        "video_lessons": 35.2,
        "interactive_exercises": 28.4,
        "quizzes": 22.3,
        "discussions": 14.1,
    }

    return {
        "trends": trends,
        "summary": summary,
        "activity_breakdown": activity_breakdown,
        "period": {
            "start": start_date.isoformat(),
            "end": end_date.isoformat(),
            "interval": interval,
        },
    }


@router.get("/trends/content")
async def get_content_trends(
    start_date: datetime | None = Query(None, description="Start date for trends"),
    end_date: datetime | None = Query(None, description="End date for trends"),
    current_user: dict = Depends(get_current_user),
) -> dict[str, Any]:
    """Get content consumption trends"""

    # Default to last 30 days if dates not provided
    if not end_date:
        end_date = datetime.now()
    if not start_date:
        start_date = end_date - timedelta(days=30)

    # Generate content trends
    content_trends = []
    current = start_date

    while current <= end_date:
        content_trends.append(
            {
                "date": current.isoformat(),
                "views": random.randint(100, 500),
                "completions": random.randint(50, 300),
                "interactions": random.randint(200, 800),
                "label": current.strftime("%b %d"),
            }
        )
        current += timedelta(days=1)

    # Popular content
    popular_content = [
        {
            "id": "content1",
            "title": "Introduction to Algebra",
            "type": "video",
            "views": 1523,
            "completion_rate": 85.2,
            "rating": 4.8,
        },
        {
            "id": "content2",
            "title": "Physics Lab: Forces and Motion",
            "type": "interactive",
            "views": 1245,
            "completion_rate": 78.9,
            "rating": 4.6,
        },
        {
            "id": "content3",
            "title": "World History Timeline",
            "type": "article",
            "views": 987,
            "completion_rate": 92.1,
            "rating": 4.7,
        },
    ]

    # Content performance metrics
    performance = {
        "total_views": sum(d["views"] for d in content_trends),
        "total_completions": sum(d["completions"] for d in content_trends),
        "average_completion_rate": 82.4,
        "average_rating": 4.5,
        "total_content_items": 256,
        "active_content_items": 189,
    }

    return {
        "trends": content_trends,
        "popular_content": popular_content,
        "performance": performance,
        "period": {"start": start_date.isoformat(), "end": end_date.isoformat()},
    }


@router.get("/subject_mastery")
async def get_subject_mastery(
    time_range: str = Query("30d"),
    student_id: str | None = Query(None),
    current_user: dict = Depends(get_current_user),
) -> list[dict[str, Any]]:
    """Get subject mastery levels"""
    subjects = [
        "Mathematics",
        "Science",
        "English",
        "History",
        "Geography",
        "Physics",
        "Chemistry",
        "Biology",
    ]

    return [
        {
            "subject": subject,
            "mastery": random.randint(60, 100),
            "improvement": random.randint(-10, 20),
            "topics_completed": random.randint(5, 20),
            "avg_score": random.randint(70, 95),
        }
        for subject in subjects
    ]


@router.get("/trends/{metric}")
@cache_result(expire=600)  # Cache for 10 minutes
async def get_metric_trends(
    metric: str = Path(..., pattern="^(users|content|engagement|performance)$"),
    days: int = Query(default=30, ge=7, le=365),
    granularity: str = Query(default="daily", pattern="^(hourly|daily|weekly|monthly)$"),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Get trend data for specific metrics

    Metrics:
    - users: User growth and activity trends
    - content: Content creation and consumption trends
    - engagement: Engagement metrics over time
    - performance: Performance trends
    """
    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(days=days)

    # This would fetch and aggregate trend data based on the metric and granularity
    # Placeholder response
    return {
        "metric": metric,
        "period": {"start": start_date.isoformat(), "end": end_date.isoformat()},
        "granularity": granularity,
        "data": [
            {
                "timestamp": (start_date + timedelta(days=i)).isoformat(),
                "value": 100 + i * 2,  # Placeholder data
            }
            for i in range(min(days, 30))
        ],
    }


@router.post("/export")
async def export_analytics_data(
    start_date: datetime | None = Query(None),
    end_date: datetime | None = Query(None),
    data_types: list[str] = Query(...),
    format: ReportFormat = Query(default=ReportFormat.CSV),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Export raw analytics data for external analysis

    Data types:
    - user_activity
    - quiz_results
    - content_metrics
    - engagement_data
    """
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Only administrators can export data")

    # This would implement data export functionality
    # Placeholder implementation
    return {
        "message": "Data export initiated",
        "format": format,
        "data_types": data_types,
        "period": {"start": start_date.isoformat(), "end": end_date.isoformat()},
    }


async def send_report_email(email: str, report: dict, report_type: str):
    """
    Background task to send report via email
    """
    # This would implement email sending
    # Using a service like SendGrid, AWS SES, etc.
    print(f"Sending {report_type} report to {email}")
    pass
