"""
Analytics Tasks
===============
Background tasks for aggregating metrics, generating reports, and exporting data
"""

import json
import csv
import io
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from celery import shared_task
from celery.utils.log import get_task_logger
from sqlalchemy import func, select
import pandas as pd

from apps.backend.core.config import settings
from apps.backend.core.database import get_session
from apps.backend.services.pusher_service import pusher_client
from database.models import (
    User,
    EducationalContent,
    Quiz,
    UserProgress,
    ClassSession,
    Assessment,
    Analytics,
)

logger = get_task_logger(__name__)


@shared_task(
    bind=True,
    name="tasks.aggregate_usage_metrics",
    max_retries=2,
    default_retry_delay=120,
    queue="analytics",
    priority=3,
)
def aggregate_usage_metrics(
    self, period: str = "daily", date: Optional[str] = None
) -> Dict[str, Any]:
    """
    Aggregate usage metrics for the specified period

    Args:
        period: Aggregation period (hourly, daily, weekly, monthly)
        date: Specific date to aggregate (defaults to yesterday for daily)

    Returns:
        Aggregated metrics
    """
    try:
        task_id = self.request.id

        # Determine date range based on period
        if date:
            target_date = datetime.fromisoformat(date)
        else:
            target_date = datetime.utcnow() - timedelta(days=1)

        if period == "hourly":
            start_time = target_date.replace(minute=0, second=0, microsecond=0)
            end_time = start_time + timedelta(hours=1)
        elif period == "daily":
            start_time = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
            end_time = start_time + timedelta(days=1)
        elif period == "weekly":
            # Start from Monday
            days_since_monday = target_date.weekday()
            start_time = (target_date - timedelta(days=days_since_monday)).replace(
                hour=0, minute=0, second=0, microsecond=0
            )
            end_time = start_time + timedelta(days=7)
        elif period == "monthly":
            start_time = target_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            # Get first day of next month
            if start_time.month == 12:
                end_time = start_time.replace(year=start_time.year + 1, month=1)
            else:
                end_time = start_time.replace(month=start_time.month + 1)
        else:
            raise ValueError(f"Invalid period: {period}")

        logger.info(f"Aggregating {period} metrics from {start_time} to {end_time}")

        metrics = {}

        with get_session() as session:
            # User metrics
            metrics["users"] = {
                "total": session.query(User).count(),
                "active": session.query(User)
                .filter(User.last_login >= start_time, User.last_login < end_time)
                .count(),
                "new": session.query(User)
                .filter(User.created_at >= start_time, User.created_at < end_time)
                .count(),
            }

            # Content metrics
            metrics["content"] = {
                "total": session.query(EducationalContent).count(),
                "created": session.query(EducationalContent)
                .filter(
                    EducationalContent.created_at >= start_time,
                    EducationalContent.created_at < end_time,
                )
                .count(),
                "views": session.query(func.sum(UserProgress.view_count))
                .filter(
                    UserProgress.last_accessed >= start_time, UserProgress.last_accessed < end_time
                )
                .scalar()
                or 0,
            }

            # Quiz metrics
            metrics["quizzes"] = {
                "total": session.query(Quiz).count(),
                "attempts": session.query(Assessment)
                .filter(Assessment.started_at >= start_time, Assessment.started_at < end_time)
                .count(),
                "completed": session.query(Assessment)
                .filter(
                    Assessment.completed_at >= start_time,
                    Assessment.completed_at < end_time,
                    Assessment.status == "completed",
                )
                .count(),
            }

            # Calculate average scores
            avg_score = (
                session.query(func.avg(Assessment.score))
                .filter(
                    Assessment.completed_at >= start_time,
                    Assessment.completed_at < end_time,
                    Assessment.status == "completed",
                )
                .scalar()
            )
            metrics["quizzes"]["average_score"] = float(avg_score) if avg_score else 0

            # Session metrics
            metrics["sessions"] = {
                "total": session.query(ClassSession)
                .filter(ClassSession.started_at >= start_time, ClassSession.started_at < end_time)
                .count(),
                "average_duration": 0,  # Calculate from session logs
            }

            # Calculate engagement rate
            total_users = metrics["users"]["total"]
            active_users = metrics["users"]["active"]
            metrics["engagement_rate"] = (
                (active_users / total_users * 100) if total_users > 0 else 0
            )

            # Store aggregated metrics in database
            analytics_entry = Analytics(
                period=period,
                period_start=start_time,
                period_end=end_time,
                metrics=json.dumps(metrics),
                created_at=datetime.utcnow(),
            )
            session.add(analytics_entry)
            session.commit()
            analytics_id = analytics_entry.id

        logger.info(f"Metrics aggregated for {period}: {metrics}")

        # Send real-time update
        if pusher_client:
            pusher_client.trigger(
                "analytics-updates",
                "metrics-aggregated",
                {"period": period, "date": start_time.isoformat(), "metrics": metrics},
            )

        return {
            "status": "success",
            "task_id": task_id,
            "analytics_id": analytics_id,
            "period": period,
            "period_start": start_time.isoformat(),
            "period_end": end_time.isoformat(),
            "metrics": metrics,
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Metrics aggregation failed: {e}")
        raise self.retry(exc=e)


@shared_task(
    bind=True,
    name="tasks.generate_reports",
    max_retries=2,
    default_retry_delay=180,
    queue="analytics",
    priority=4,
)
def generate_reports(
    self, report_type: str, start_date: str, end_date: str, filters: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Generate analytical reports

    Args:
        report_type: Type of report (usage, performance, progress, compliance)
        start_date: Report start date
        end_date: Report end date
        filters: Additional filters

    Returns:
        Generated report data
    """
    try:
        task_id = self.request.id
        filters = filters or {}

        start = datetime.fromisoformat(start_date)
        end = datetime.fromisoformat(end_date)

        logger.info(f"Generating {report_type} report from {start_date} to {end_date}")

        report_data = {}

        with get_session() as session:
            if report_type == "usage":
                # User activity report
                report_data["user_activity"] = []

                users = session.query(User)
                if filters.get("role"):
                    users = users.filter(User.role == filters["role"])

                for user in users.all():
                    progress = (
                        session.query(UserProgress)
                        .filter(
                            UserProgress.user_id == user.id,
                            UserProgress.last_accessed >= start,
                            UserProgress.last_accessed <= end,
                        )
                        .all()
                    )

                    user_data = {
                        "user_id": str(user.id),
                        "username": user.username,
                        "role": user.role,
                        "content_accessed": len(progress),
                        "total_time_spent": sum(p.time_spent or 0 for p in progress),
                        "last_active": user.last_login.isoformat() if user.last_login else None,
                    }
                    report_data["user_activity"].append(user_data)

                # Content usage statistics
                content_stats = (
                    session.query(
                        EducationalContent.topic,
                        func.count(UserProgress.id).label("views"),
                        func.avg(UserProgress.completion_percentage).label("avg_completion"),
                    )
                    .join(UserProgress, UserProgress.content_id == EducationalContent.id)
                    .filter(UserProgress.last_accessed >= start, UserProgress.last_accessed <= end)
                    .group_by(EducationalContent.topic)
                    .all()
                )

                report_data["content_stats"] = [
                    {
                        "topic": stat.topic,
                        "views": stat.views,
                        "avg_completion": float(stat.avg_completion) if stat.avg_completion else 0,
                    }
                    for stat in content_stats
                ]

            elif report_type == "performance":
                # Student performance report
                assessments = session.query(Assessment).filter(
                    Assessment.completed_at >= start, Assessment.completed_at <= end
                )

                if filters.get("class_id"):
                    assessments = assessments.filter(Assessment.class_id == filters["class_id"])

                assessment_data = []
                for assessment in assessments.all():
                    user = session.query(User).filter_by(id=assessment.user_id).first()
                    assessment_data.append(
                        {
                            "user_id": str(assessment.user_id),
                            "username": user.username if user else "Unknown",
                            "quiz_id": str(assessment.quiz_id),
                            "score": assessment.score,
                            "time_taken": assessment.time_taken,
                            "completed_at": assessment.completed_at.isoformat(),
                        }
                    )

                report_data["assessments"] = assessment_data

                # Calculate statistics
                if assessment_data:
                    scores = [a["score"] for a in assessment_data if a["score"] is not None]
                    report_data["statistics"] = {
                        "total_assessments": len(assessment_data),
                        "average_score": sum(scores) / len(scores) if scores else 0,
                        "highest_score": max(scores) if scores else 0,
                        "lowest_score": min(scores) if scores else 0,
                    }

            elif report_type == "progress":
                # Learning progress report
                progress_data = []

                users = session.query(User).filter(User.role == "student")
                if filters.get("class_id"):
                    # Filter by class membership
                    pass  # Implement based on your class membership model

                for user in users.all():
                    user_progress = (
                        session.query(UserProgress)
                        .filter(
                            UserProgress.user_id == user.id,
                            UserProgress.last_accessed >= start,
                            UserProgress.last_accessed <= end,
                        )
                        .all()
                    )

                    completed_content = [p for p in user_progress if p.completion_percentage >= 100]

                    progress_data.append(
                        {
                            "user_id": str(user.id),
                            "username": user.username,
                            "content_started": len(user_progress),
                            "content_completed": len(completed_content),
                            "avg_completion": (
                                sum(p.completion_percentage for p in user_progress)
                                / len(user_progress)
                                if user_progress
                                else 0
                            ),
                            "total_time_spent": sum(p.time_spent or 0 for p in user_progress),
                        }
                    )

                report_data["progress"] = progress_data

            elif report_type == "compliance":
                # Compliance and safety report
                report_data["compliance"] = {
                    "coppa_compliant": True,
                    "ferpa_compliant": True,
                    "gdpr_compliant": settings.GDPR_COMPLIANCE,
                    "data_retention_days": 365,
                    "last_audit": datetime.utcnow().isoformat(),
                }

                # Add any compliance violations or concerns
                report_data["violations"] = []

        # Generate report file
        report_id = f"{report_type}_{start_date}_{end_date}_{task_id}"
        report_path = f"/tmp/reports/{report_id}.json"

        # Save report
        import os

        os.makedirs(os.path.dirname(report_path), exist_ok=True)
        with open(report_path, "w") as f:
            json.dump(report_data, f, indent=2, default=str)

        logger.info(f"Report generated: {report_id}")

        # Notify completion
        if pusher_client:
            pusher_client.trigger(
                "report-generation",
                "report-complete",
                {
                    "task_id": task_id,
                    "report_id": report_id,
                    "report_type": report_type,
                    "path": report_path,
                },
            )

        return {
            "status": "success",
            "task_id": task_id,
            "report_id": report_id,
            "report_type": report_type,
            "report_path": report_path,
            "data_points": len(report_data.get("user_activity", []))
            + len(report_data.get("assessments", []))
            + len(report_data.get("progress", [])),
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Report generation failed: {e}")
        raise self.retry(exc=e)


@shared_task(
    bind=True,
    name="tasks.export_analytics_data",
    max_retries=2,
    default_retry_delay=60,
    queue="analytics",
    priority=2,
)
def export_analytics_data(
    self,
    export_format: str = "csv",
    data_type: str = "all",
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Export analytics data in various formats

    Args:
        export_format: Format for export (csv, json, excel)
        data_type: Type of data to export
        start_date: Start date for export
        end_date: End date for export

    Returns:
        Export file information
    """
    try:
        task_id = self.request.id

        # Set date range
        if start_date:
            start = datetime.fromisoformat(start_date)
        else:
            start = datetime.utcnow() - timedelta(days=30)

        if end_date:
            end = datetime.fromisoformat(end_date)
        else:
            end = datetime.utcnow()

        logger.info(f"Exporting {data_type} data as {export_format}")

        export_data = {}

        with get_session() as session:
            # Gather data based on type
            if data_type in ["all", "users"]:
                users = session.query(User).all()
                export_data["users"] = [
                    {
                        "id": str(u.id),
                        "username": u.username,
                        "email": u.email,
                        "role": u.role,
                        "created_at": u.created_at.isoformat() if u.created_at else None,
                        "last_login": u.last_login.isoformat() if u.last_login else None,
                    }
                    for u in users
                ]

            if data_type in ["all", "content"]:
                content = (
                    session.query(EducationalContent)
                    .filter(
                        EducationalContent.created_at >= start, EducationalContent.created_at <= end
                    )
                    .all()
                )
                export_data["content"] = [
                    {
                        "id": str(c.id),
                        "title": c.title,
                        "topic": c.topic,
                        "grade_level": c.grade_level,
                        "content_type": c.content_type,
                        "created_at": c.created_at.isoformat() if c.created_at else None,
                    }
                    for c in content
                ]

            if data_type in ["all", "analytics"]:
                analytics = (
                    session.query(Analytics)
                    .filter(Analytics.period_start >= start, Analytics.period_end <= end)
                    .all()
                )
                export_data["analytics"] = [
                    {
                        "id": str(a.id),
                        "period": a.period,
                        "period_start": a.period_start.isoformat(),
                        "period_end": a.period_end.isoformat(),
                        "metrics": json.loads(a.metrics),
                    }
                    for a in analytics
                ]

        # Create export file
        export_id = f"export_{data_type}_{task_id}"
        export_dir = "/tmp/exports"
        os.makedirs(export_dir, exist_ok=True)

        if export_format == "csv":
            # Export each data type to separate CSV files
            for key, data in export_data.items():
                if data:
                    filepath = f"{export_dir}/{export_id}_{key}.csv"
                    df = pd.DataFrame(data)
                    df.to_csv(filepath, index=False)
                    logger.info(f"Exported {len(data)} {key} records to {filepath}")

            export_path = f"{export_dir}/{export_id}.csv"

        elif export_format == "json":
            export_path = f"{export_dir}/{export_id}.json"
            with open(export_path, "w") as f:
                json.dump(export_data, f, indent=2, default=str)

        elif export_format == "excel":
            export_path = f"{export_dir}/{export_id}.xlsx"
            with pd.ExcelWriter(export_path) as writer:
                for key, data in export_data.items():
                    if data:
                        df = pd.DataFrame(data)
                        df.to_excel(writer, sheet_name=key, index=False)

        else:
            raise ValueError(f"Unsupported export format: {export_format}")

        # Calculate export size
        file_size = os.path.getsize(export_path) if os.path.exists(export_path) else 0

        logger.info(f"Data exported to {export_path} ({file_size} bytes)")

        return {
            "status": "success",
            "task_id": task_id,
            "export_id": export_id,
            "export_path": export_path,
            "export_format": export_format,
            "file_size": file_size,
            "data_types": list(export_data.keys()),
            "total_records": sum(len(v) for v in export_data.values()),
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Data export failed: {e}")
        raise self.retry(exc=e)
