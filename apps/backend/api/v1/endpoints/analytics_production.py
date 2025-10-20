"""
Analytics API Endpoints for ToolboxAI Educational Platform - PRODUCTION VERSION
Provides real analytics data from the database.

This file replaces the hardcoded sample data with actual database queries.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from uuid import UUID
import logging

from sqlalchemy import select, func, and_, or_, desc
from sqlalchemy.ext.asyncio import AsyncSession

from apps.backend.api.auth.auth import get_current_user
from database.models.models import (
    User, UserRole, Class, ClassEnrollment, UserProgress,
    Analytics, Leaderboard, Enrollment, Quiz, QuizAttempt,
    StudentProgress, Course, Lesson, Content
)
from database.database_service import DatabaseService

logger = logging.getLogger(__name__)

# Initialize database service
database_service = DatabaseService()

# Database session dependency
async def get_db_session():
    """Get database session"""
    async with database_service.async_session_scope() as session:
        yield session

# Create router for analytics endpoints
analytics_router = APIRouter(tags=["Analytics"])


@analytics_router.get("/overview")
async def get_analytics_overview(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> Dict[str, Any]:
    """Get analytics overview for dashboard with real database data."""

    try:
        await database_service.initialize()

        # Get total and active students
        total_students_query = select(func.count(User.id)).where(User.role == UserRole.STUDENT)
        total_students_result = await session.execute(total_students_query)
        total_students = total_students_result.scalar() or 0

        # Active students (logged in within last 30 days)
        thirty_days_ago = datetime.now() - timedelta(days=30)
        active_students_query = select(func.count(User.id)).where(
            and_(User.role == UserRole.STUDENT, User.last_login >= thirty_days_ago)
        )
        active_students_result = await session.execute(active_students_query)
        active_students = active_students_result.scalar() or 0

        # Get total classes
        total_classes_query = select(func.count(Class.id)).where(Class.is_active == True)
        total_classes_result = await session.execute(total_classes_query)
        total_classes = total_classes_result.scalar() or 0

        # Get average completion rate from UserProgress
        avg_completion_query = select(func.avg(UserProgress.progress_percentage))
        avg_completion_result = await session.execute(avg_completion_query)
        average_completion = avg_completion_result.scalar() or 0.0

        # Get average quiz score
        avg_score_query = select(func.avg(QuizAttempt.score)).where(
            QuizAttempt.completed_at.isnot(None)
        )
        avg_score_result = await session.execute(avg_score_query)
        average_score = avg_score_result.scalar() or 0.0

        # Get assignment counts (using Quiz as proxy for assignments)
        total_assignments_query = select(func.count(Quiz.id))
        total_assignments_result = await session.execute(total_assignments_query)
        total_assignments = total_assignments_result.scalar() or 0

        completed_assignments_query = select(func.count(QuizAttempt.id)).where(
            QuizAttempt.completed_at.isnot(None)
        )
        completed_assignments_result = await session.execute(completed_assignments_query)
        completed_assignments = completed_assignments_result.scalar() or 0

        pending_submissions = total_assignments - completed_assignments

        # Calculate engagement rate (active students / total students)
        engagement_rate = (active_students / total_students * 100) if total_students > 0 else 0

        # Calculate attendance rate (active enrollments / total enrollments)
        total_enrollments_query = select(func.count(ClassEnrollment.id))
        total_enrollments_result = await session.execute(total_enrollments_query)
        total_enrollments = total_enrollments_result.scalar() or 0

        active_enrollments_query = select(func.count(ClassEnrollment.id)).where(
            ClassEnrollment.status == "active"
        )
        active_enrollments_result = await session.execute(active_enrollments_query)
        active_enrollments = active_enrollments_result.scalar() or 0

        attendance_rate = (active_enrollments / total_enrollments * 100) if total_enrollments > 0 else 0

        return {
            "total_students": total_students,
            "active_students": active_students,
            "total_classes": total_classes,
            "average_completion": round(average_completion, 1),
            "average_score": round(average_score, 1),
            "total_assignments": total_assignments,
            "completed_assignments": completed_assignments,
            "pending_submissions": pending_submissions,
            "engagement_rate": round(engagement_rate, 1),
            "attendance_rate": round(attendance_rate, 1),
        }

    except Exception as e:
        logger.error(f"Error fetching analytics overview: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch analytics overview"
        )


@analytics_router.get("/student-progress")
async def get_student_progress(
    student_id: Optional[str] = Query(None),
    class_id: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> Dict[str, Any]:
    """Get student progress data from database."""

    try:
        await database_service.initialize()

        # Determine which student to get progress for
        target_student_id = student_id if student_id else str(current_user.id)

        # Authorization check
        if current_user.role != UserRole.ADMIN and current_user.role != UserRole.TEACHER:
            if str(current_user.id) != target_student_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not authorized to view this student's progress"
                )

        student_uuid = UUID(target_student_id)

        # Get overall progress
        progress_query = select(func.avg(UserProgress.progress_percentage)).where(
            UserProgress.user_id == student_uuid
        )
        progress_result = await session.execute(progress_query)
        overall_progress = progress_result.scalar() or 0.0

        # Get lesson counts
        completed_lessons_query = select(func.count(UserProgress.id)).where(
            and_(
                UserProgress.user_id == student_uuid,
                UserProgress.progress_percentage >= 100
            )
        )
        completed_result = await session.execute(completed_lessons_query)
        completed_lessons = completed_result.scalar() or 0

        total_lessons_query = select(func.count(Lesson.id))
        total_result = await session.execute(total_lessons_query)
        total_lessons = total_result.scalar() or 0

        # Get XP earned (from UserProgress or Analytics table)
        xp_query = select(func.sum(Analytics.xp_earned)).where(
            Analytics.user_id == student_uuid
        )
        xp_result = await session.execute(xp_query)
        xp_earned = xp_result.scalar() or 0

        # Get badges (placeholder - would need UserAchievement table)
        badges_earned = 0

        # Get rank from Leaderboard
        rank_query = select(Leaderboard.rank).where(
            Leaderboard.user_id == student_uuid
        ).order_by(Leaderboard.updated_at.desc()).limit(1)
        rank_result = await session.execute(rank_query)
        rank = rank_result.scalar() or 0

        # TODO: Implement subject breakdown from actual data
        # TODO: Implement recent activity from audit logs
        # TODO: Implement streak tracking

        return {
            "overall_progress": round(overall_progress, 1),
            "completed_lessons": completed_lessons,
            "total_lessons": total_lessons,
            "current_streak": 0,  # TODO: Implement streak tracking
            "best_streak": 0,  # TODO: Implement streak tracking
            "xp_earned": xp_earned,
            "badges_earned": badges_earned,
            "rank": rank,
            "subjects": [],  # TODO: Aggregate by subject
            "recent_activity": [],  # TODO: Query from activity logs
        }

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid student ID format"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching student progress: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch student progress"
        )


@analytics_router.get("/weekly_xp")
async def get_weekly_xp(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> Dict[str, Any]:
    """Get weekly XP progression from database."""

    try:
        await database_service.initialize()

        # Get XP data for the last 7 days
        end_date = datetime.now()
        start_date = end_date - timedelta(days=6)  # 7 days including today

        # Query daily XP from Analytics table
        daily_xp_query = select(
            func.date(Analytics.created_at).label('date'),
            func.sum(Analytics.xp_earned).label('xp')
        ).where(
            and_(
                Analytics.user_id == current_user.id,
                Analytics.created_at >= start_date,
                Analytics.created_at <= end_date
            )
        ).group_by(func.date(Analytics.created_at))

        result = await session.execute(daily_xp_query)
        daily_data = {row.date: row.xp for row in result}

        # Build response for all 7 days
        days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

        xp_data = []
        total_xp = 0
        days_with_data = 0

        for i in range(7):
            date = start_date + timedelta(days=i)
            date_key = date.date()
            xp = daily_data.get(date_key, 0)

            if xp > 0:
                total_xp += xp
                days_with_data += 1

            xp_data.append({
                "day": days[date.weekday()],
                "xp": int(xp) if xp else 0,
                "completed": date.date() <= datetime.now().date(),
                "date": date_key.isoformat()
            })

        return {
            "week_total": int(total_xp),
            "daily_average": int(total_xp / days_with_data) if days_with_data > 0 else 0,
            "streak": days_with_data,
            "data": xp_data,
        }

    except Exception as e:
        logger.error(f"Error fetching weekly XP: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch weekly XP data"
        )


@analytics_router.get("/subject_mastery")
async def get_subject_mastery(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> List[Dict[str, Any]]:
    """Get subject mastery levels from database."""

    try:
        await database_service.initialize()

        # Query progress by subject/course
        subject_query = select(
            Course.title.label('subject'),
            func.avg(UserProgress.progress_percentage).label('mastery'),
            func.count(UserProgress.id).label('topics_completed')
        ).select_from(
            UserProgress.__table__.join(
                Lesson.__table__, UserProgress.lesson_id == Lesson.id
            ).join(
                Course.__table__, Lesson.course_id == Course.id
            )
        ).where(
            UserProgress.user_id == current_user.id
        ).group_by(Course.title)

        result = await session.execute(subject_query)
        subjects = []

        for row in result:
            subjects.append({
                "subject": row.subject,
                "mastery": round(row.mastery, 0) if row.mastery else 0,
                "progress": 0,  # TODO: Calculate recent progress change
                "topics_completed": row.topics_completed,
            })

        subjects.sort(key=lambda x: x['mastery'], reverse=True)

        return subjects

    except Exception as e:
        logger.error(f"Error fetching subject mastery: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch subject mastery"
        )


# Gamification Router
gamification_router = APIRouter(prefix="/gamification", tags=["Gamification"])


@gamification_router.get("/leaderboard")
async def get_leaderboard(
    timeframe: str = Query(default="week", enum=["day", "week", "month", "all"]),
    limit: int = Query(default=10, le=100),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> Dict[str, Any]:
    """Get leaderboard data from database."""

    try:
        await database_service.initialize()

        end_date = datetime.now()
        if timeframe == "day":
            start_date = end_date - timedelta(days=1)
        elif timeframe == "week":
            start_date = end_date - timedelta(days=7)
        elif timeframe == "month":
            start_date = end_date - timedelta(days=30)
        else:
            start_date = None

        if start_date:
            leaderboard_query = select(
                Analytics.user_id,
                User.username,
                User.first_name,
                User.last_name,
                func.sum(Analytics.xp_earned).label('xp')
            ).select_from(
                Analytics.__table__.join(User.__table__, Analytics.user_id == User.id)
            ).where(
                Analytics.created_at >= start_date
            ).group_by(
                Analytics.user_id, User.username, User.first_name, User.last_name
            ).order_by(desc('xp')).limit(limit)
        else:
            leaderboard_query = select(
                Leaderboard.user_id,
                User.username,
                User.first_name,
                User.last_name,
                Leaderboard.xp,
                Leaderboard.level,
                Leaderboard.rank
            ).select_from(
                Leaderboard.__table__.join(User.__table__, Leaderboard.user_id == User.id)
            ).order_by(Leaderboard.rank).limit(limit)

        result = await session.execute(leaderboard_query)
        rows = result.all()

        leaderboard = []
        current_user_rank = None

        for i, row in enumerate(rows, 1):
            name = f"{row.first_name} {row.last_name}".strip() if row.first_name else row.username
            is_current = str(row.user_id) == str(current_user.id)

            if is_current:
                name = "You"
                current_user_rank = i

            leaderboard.append({
                "rank": i,
                "user_id": str(row.user_id),
                "name": name,
                "xp": int(row.xp) if row.xp else 0,
                "level": getattr(row, 'level', 0) or 0,
                "badges": 0,
                "is_current_user": is_current,
                "movement": "same",
            })

        total_query = select(func.count(func.distinct(Analytics.user_id)))
        if start_date:
            total_query = total_query.where(Analytics.created_at >= start_date)
        total_result = await session.execute(total_query)
        total_participants = total_result.scalar() or 0

        return {
            "timeframe": timeframe,
            "last_updated": datetime.now().isoformat(),
            "total_participants": total_participants,
            "leaderboard": leaderboard,
            "user_stats": {
                "current_rank": current_user_rank or 0,
                "previous_rank": 0,
                "xp_to_next_rank": 0,
                "percentile": round((1 - (current_user_rank / total_participants)) * 100, 1) if current_user_rank and total_participants > 0 else 0,
            },
        }

    except Exception as e:
        logger.error(f"Error fetching leaderboard: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch leaderboard"
        )


# Users Router
users_router = APIRouter(prefix="/users", tags=["Users"])


@users_router.get("/")
async def list_users(
    search: str = Query(default="", description="Search term"),
    role: Optional[str] = Query(default=None, description="Filter by role"),
    limit: int = Query(default=20, le=100),
    offset: int = Query(default=0, ge=0),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> List[Dict[str, Any]]:
    """List users from database (admin only)."""

    try:
        await database_service.initialize()

        if current_user.role != UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only admins can list users"
            )

        query = select(User)

        if role:
            try:
                role_enum = UserRole[role.upper()]
                query = query.where(User.role == role_enum)
            except KeyError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid role: {role}"
                )

        if search:
            search_term = f"%{search.lower()}%"
            query = query.where(
                or_(
                    func.lower(User.username).like(search_term),
                    func.lower(User.email).like(search_term),
                    func.lower(User.first_name).like(search_term),
                    func.lower(User.last_name).like(search_term)
                )
            )

        query = query.order_by(User.created_at.desc()).limit(limit).offset(offset)

        result = await session.execute(query)
        users = result.scalars().all()

        return [
            {
                "id": str(user.id),
                "username": user.username,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "role": user.role.value if hasattr(user.role, 'value') else str(user.role),
                "status": "active" if user.is_active else "inactive",
                "created_at": user.created_at.isoformat() if user.created_at else None,
                "last_login": user.last_login.isoformat() if user.last_login else None,
            }
            for user in users
        ]

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing users: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list users"
        )


@users_router.get("/{user_id}")
async def get_user(
    user_id: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> Dict[str, Any]:
    """Get user details from database."""

    try:
        await database_service.initialize()

        if current_user.role != UserRole.ADMIN and str(current_user.id) != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to view this user"
            )

        user_uuid = UUID(user_id)

        user_query = select(User).where(User.id == user_uuid)
        result = await session.execute(user_query)
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        profile_data = {}

        if user.role == UserRole.TEACHER:
            class_count_query = select(func.count(Class.id)).where(Class.teacher_id == user_uuid)
            class_count_result = await session.execute(class_count_query)
            total_classes = class_count_result.scalar() or 0

            student_count_query = select(func.count(func.distinct(ClassEnrollment.student_id))).select_from(
                Class.__table__.join(ClassEnrollment.__table__, Class.id == ClassEnrollment.class_id)
            ).where(Class.teacher_id == user_uuid)
            student_count_result = await session.execute(student_count_query)
            total_students = student_count_result.scalar() or 0

            profile_data = {
                "total_students": total_students,
                "total_classes": total_classes,
            }

        elif user.role == UserRole.STUDENT:
            enrollment_count_query = select(func.count(ClassEnrollment.id)).where(
                ClassEnrollment.student_id == user_uuid
            )
            enrollment_result = await session.execute(enrollment_count_query)
            total_enrollments = enrollment_result.scalar() or 0

            xp_query = select(func.sum(Analytics.xp_earned)).where(Analytics.user_id == user_uuid)
            xp_result = await session.execute(xp_query)
            total_xp = xp_result.scalar() or 0

            profile_data = {
                "total_enrollments": total_enrollments,
                "total_xp": int(total_xp),
            }

        return {
            "id": str(user.id),
            "username": user.username,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "role": user.role.value if hasattr(user.role, 'value') else str(user.role),
            "status": "active" if user.is_active else "inactive",
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "last_login": user.last_login.isoformat() if user.last_login else None,
            "profile": profile_data,
        }

    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID format"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user"
        )


@analytics_router.get("/realtime")
async def get_realtime_analytics(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> Dict[str, Any]:
    """Get real-time analytics data from database."""

    try:
        await database_service.initialize()

        five_min_ago = datetime.now() - timedelta(minutes=5)
        active_users_query = select(func.count(func.distinct(Analytics.user_id))).where(
            Analytics.created_at >= five_min_ago
        )
        active_result = await session.execute(active_users_query)
        active_users = active_result.scalar() or 0

        recent_query = select(Analytics).order_by(Analytics.created_at.desc()).limit(10)
        recent_result = await session.execute(recent_query)
        recent_activities_raw = recent_result.scalars().all()

        recent_activities = [
            {
                "type": "activity",
                "user": f"user_{activity.user_id}",
                "timestamp": activity.created_at.isoformat() if activity.created_at else None,
            }
            for activity in recent_activities_raw
        ]

        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        today_query = select(func.count(Analytics.id)).where(Analytics.created_at >= today_start)
        today_result = await session.execute(today_query)
        today_activities = today_result.scalar() or 0

        return {
            "timestamp": datetime.now().isoformat(),
            "active_users": active_users,
            "active_sessions": active_users,
            "recent_activities": recent_activities,
            "usage_stats": {
                "activities_today": today_activities,
                "active_users": active_users,
            },
        }

    except Exception as e:
        logger.error(f"Error fetching realtime analytics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch realtime analytics"
        )


@analytics_router.get("/trends/engagement")
async def get_engagement_trends(
    days: int = Query(default=30, le=365, description="Number of days to analyze"),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> Dict[str, Any]:
    """Get engagement trends over time from database."""

    try:
        await database_service.initialize()

        # Authorization: admin only
        if current_user.role != UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only admins can view engagement trends"
            )

        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        # Daily active users
        daily_users_query = select(
            func.date(Analytics.created_at).label('date'),
            func.count(func.distinct(Analytics.user_id)).label('users')
        ).where(
            Analytics.created_at >= start_date
        ).group_by(func.date(Analytics.created_at))

        daily_result = await session.execute(daily_users_query)
        daily_users = {row.date: row.users for row in daily_result}

        # Daily activities
        daily_activities_query = select(
            func.date(Analytics.created_at).label('date'),
            func.count(Analytics.id).label('activities')
        ).where(
            Analytics.created_at >= start_date
        ).group_by(func.date(Analytics.created_at))

        activities_result = await session.execute(daily_activities_query)
        daily_activities = {row.date: row.activities for row in activities_result}

        # Build time series data
        trend_data = []
        for i in range(days):
            date = (start_date + timedelta(days=i)).date()
            trend_data.append({
                "date": date.isoformat(),
                "active_users": daily_users.get(date, 0),
                "activities": daily_activities.get(date, 0),
                "avg_session_duration": 0,  # TODO: Implement session tracking
            })

        # Calculate summary statistics
        total_activities = sum(daily_activities.values())
        avg_daily_users = sum(daily_users.values()) / days if days > 0 else 0
        avg_daily_activities = total_activities / days if days > 0 else 0

        # Calculate growth rate (comparing first week to last week)
        if days >= 14:
            first_week_users = sum(daily_users.get((start_date + timedelta(days=i)).date(), 0) for i in range(7))
            last_week_users = sum(daily_users.get((end_date - timedelta(days=6 - i)).date(), 0) for i in range(7))
            growth_rate = ((last_week_users - first_week_users) / first_week_users * 100) if first_week_users > 0 else 0
        else:
            growth_rate = 0

        return {
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
                "days": days,
            },
            "summary": {
                "avg_daily_users": round(avg_daily_users, 1),
                "avg_daily_activities": round(avg_daily_activities, 1),
                "total_activities": total_activities,
                "growth_rate": round(growth_rate, 2),
            },
            "trends": trend_data,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching engagement trends: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch engagement trends"
        )


@analytics_router.get("/trends/content")
async def get_content_trends(
    days: int = Query(default=30, le=365, description="Number of days to analyze"),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> Dict[str, Any]:
    """Get content consumption trends from database."""

    try:
        await database_service.initialize()

        # Authorization: admin or teacher
        if current_user.role not in [UserRole.ADMIN, UserRole.TEACHER]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to view content trends"
            )

        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        # Most viewed content (using UserProgress as proxy for views)
        most_viewed_query = select(
            Lesson.title.label('title'),
            Course.title.label('course'),
            func.count(UserProgress.id).label('views')
        ).select_from(
            UserProgress.__table__.join(
                Lesson.__table__, UserProgress.lesson_id == Lesson.id
            ).join(
                Course.__table__, Lesson.course_id == Course.id
            )
        ).where(
            UserProgress.updated_at >= start_date
        ).group_by(Lesson.title, Course.title).order_by(desc('views')).limit(10)

        viewed_result = await session.execute(most_viewed_query)
        most_viewed = [
            {
                "title": row.title,
                "course": row.course,
                "views": row.views,
                "type": "lesson",
            }
            for row in viewed_result
        ]

        # Completion rates by course
        completion_query = select(
            Course.title.label('course'),
            func.avg(UserProgress.progress_percentage).label('avg_completion')
        ).select_from(
            UserProgress.__table__.join(
                Lesson.__table__, UserProgress.lesson_id == Lesson.id
            ).join(
                Course.__table__, Lesson.course_id == Course.id
            )
        ).where(
            UserProgress.updated_at >= start_date
        ).group_by(Course.title)

        completion_result = await session.execute(completion_query)
        completion_rates = [
            {
                "course": row.course,
                "completion_rate": round(row.avg_completion, 1) if row.avg_completion else 0,
            }
            for row in completion_result
        ]

        # Daily content consumption
        daily_consumption_query = select(
            func.date(UserProgress.updated_at).label('date'),
            func.count(UserProgress.id).label('interactions')
        ).where(
            UserProgress.updated_at >= start_date
        ).group_by(func.date(UserProgress.updated_at))

        consumption_result = await session.execute(daily_consumption_query)
        daily_consumption = [
            {
                "date": row.date.isoformat(),
                "interactions": row.interactions,
            }
            for row in consumption_result
        ]

        return {
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
                "days": days,
            },
            "most_viewed": most_viewed,
            "completion_rates": completion_rates,
            "daily_consumption": daily_consumption,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching content trends: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch content trends"
        )


@analytics_router.get("/dashboard")
async def get_dashboard_analytics(
    time_range: str = Query(default="week", enum=["day", "week", "month", "year"]),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> Dict[str, Any]:
    """Get comprehensive dashboard analytics from database."""

    try:
        await database_service.initialize()

        # Authorization: admin or teacher
        if current_user.role not in [UserRole.ADMIN, UserRole.TEACHER]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to view dashboard analytics"
            )

        # Determine time range
        end_date = datetime.now()
        if time_range == "day":
            start_date = end_date - timedelta(days=1)
        elif time_range == "week":
            start_date = end_date - timedelta(days=7)
        elif time_range == "month":
            start_date = end_date - timedelta(days=30)
        else:  # year
            start_date = end_date - timedelta(days=365)

        # Get key metrics
        # 1. User engagement
        active_users_query = select(func.count(func.distinct(Analytics.user_id))).where(
            Analytics.created_at >= start_date
        )
        active_result = await session.execute(active_users_query)
        active_users = active_result.scalar() or 0

        # 2. Total activities
        activities_query = select(func.count(Analytics.id)).where(
            Analytics.created_at >= start_date
        )
        activities_result = await session.execute(activities_query)
        total_activities = activities_result.scalar() or 0

        # 3. Completion rate
        completion_query = select(func.avg(UserProgress.progress_percentage)).where(
            UserProgress.updated_at >= start_date
        )
        completion_result = await session.execute(completion_query)
        avg_completion = completion_result.scalar() or 0

        # 4. Quiz performance
        quiz_query = select(func.avg(QuizAttempt.score)).where(
            and_(
                QuizAttempt.completed_at.isnot(None),
                QuizAttempt.completed_at >= start_date
            )
        )
        quiz_result = await session.execute(quiz_query)
        avg_quiz_score = quiz_result.scalar() or 0

        # 5. Top performers (leaderboard)
        top_performers_query = select(
            User.username,
            User.first_name,
            User.last_name,
            func.sum(Analytics.xp_earned).label('xp')
        ).select_from(
            Analytics.__table__.join(User.__table__, Analytics.user_id == User.id)
        ).where(
            Analytics.created_at >= start_date
        ).group_by(
            User.username, User.first_name, User.last_name
        ).order_by(desc('xp')).limit(5)

        performers_result = await session.execute(top_performers_query)
        top_performers = [
            {
                "name": f"{row.first_name} {row.last_name}".strip() if row.first_name else row.username,
                "xp": int(row.xp) if row.xp else 0,
            }
            for row in performers_result
        ]

        # 6. Recent completions
        recent_completions_query = select(
            UserProgress.user_id,
            Lesson.title,
            UserProgress.progress_percentage,
            UserProgress.updated_at
        ).select_from(
            UserProgress.__table__.join(Lesson.__table__, UserProgress.lesson_id == Lesson.id)
        ).where(
            and_(
                UserProgress.progress_percentage >= 100,
                UserProgress.updated_at >= start_date
            )
        ).order_by(UserProgress.updated_at.desc()).limit(10)

        completions_result = await session.execute(recent_completions_query)
        recent_completions = [
            {
                "user_id": str(row.user_id),
                "lesson": row.title,
                "completed_at": row.updated_at.isoformat() if row.updated_at else None,
            }
            for row in completions_result
        ]

        return {
            "time_range": time_range,
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
            },
            "metrics": {
                "active_users": active_users,
                "total_activities": total_activities,
                "avg_completion_rate": round(avg_completion, 1),
                "avg_quiz_score": round(avg_quiz_score, 1),
            },
            "top_performers": top_performers,
            "recent_completions": recent_completions,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching dashboard analytics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch dashboard analytics"
        )


@analytics_router.get("/summary")
async def get_analytics_summary(
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    class_id: Optional[str] = Query(None, description="Filter by class ID"),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> Dict[str, Any]:
    """Get comprehensive analytics summary with optional filters."""

    try:
        await database_service.initialize()

        # Authorization: admin or teacher
        if current_user.role not in [UserRole.ADMIN, UserRole.TEACHER]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to view analytics summary"
            )

        # Parse date filters
        if start_date:
            start_dt = datetime.fromisoformat(start_date)
        else:
            start_dt = datetime.now() - timedelta(days=30)

        if end_date:
            end_dt = datetime.fromisoformat(end_date)
        else:
            end_dt = datetime.now()

        # Build base queries with filters
        base_conditions = [Analytics.created_at >= start_dt, Analytics.created_at <= end_dt]

        # If class filter provided, join to get students in that class
        if class_id:
            class_uuid = UUID(class_id)
            # Get user IDs enrolled in class
            enrollment_query = select(ClassEnrollment.student_id).where(
                ClassEnrollment.class_id == class_uuid
            )
            enrollment_result = await session.execute(enrollment_query)
            student_ids = [row[0] for row in enrollment_result]

            if student_ids:
                base_conditions.append(Analytics.user_id.in_(student_ids))

        # 1. User statistics
        total_users_query = select(func.count(func.distinct(Analytics.user_id))).where(
            and_(*base_conditions)
        )
        users_result = await session.execute(total_users_query)
        total_users = users_result.scalar() or 0

        # 2. Activity statistics
        total_activities_query = select(func.count(Analytics.id)).where(
            and_(*base_conditions)
        )
        activities_result = await session.execute(total_activities_query)
        total_activities = activities_result.scalar() or 0

        # 3. XP statistics
        total_xp_query = select(func.sum(Analytics.xp_earned)).where(
            and_(*base_conditions)
        )
        xp_result = await session.execute(total_xp_query)
        total_xp = xp_result.scalar() or 0

        avg_xp_per_user = (total_xp / total_users) if total_users > 0 else 0

        # 4. Progress statistics
        progress_conditions = [UserProgress.updated_at >= start_dt, UserProgress.updated_at <= end_dt]
        if class_id and student_ids:
            progress_conditions.append(UserProgress.user_id.in_(student_ids))

        avg_progress_query = select(func.avg(UserProgress.progress_percentage)).where(
            and_(*progress_conditions)
        )
        progress_result = await session.execute(avg_progress_query)
        avg_progress = progress_result.scalar() or 0

        # 5. Completion count
        completed_query = select(func.count(UserProgress.id)).where(
            and_(
                UserProgress.progress_percentage >= 100,
                *progress_conditions
            )
        )
        completed_result = await session.execute(completed_query)
        total_completed = completed_result.scalar() or 0

        # 6. Quiz statistics
        quiz_conditions = [QuizAttempt.completed_at >= start_dt, QuizAttempt.completed_at <= end_dt]
        if class_id and student_ids:
            quiz_conditions.append(QuizAttempt.user_id.in_(student_ids))

        quiz_stats_query = select(
            func.count(QuizAttempt.id).label('total'),
            func.avg(QuizAttempt.score).label('avg_score')
        ).where(
            and_(QuizAttempt.completed_at.isnot(None), *quiz_conditions)
        )
        quiz_result = await session.execute(quiz_stats_query)
        quiz_row = quiz_result.first()

        return {
            "period": {
                "start": start_dt.isoformat(),
                "end": end_dt.isoformat(),
            },
            "filters": {
                "class_id": class_id,
            },
            "summary": {
                "total_users": total_users,
                "total_activities": total_activities,
                "total_xp_earned": int(total_xp),
                "avg_xp_per_user": round(avg_xp_per_user, 1),
                "avg_progress": round(avg_progress, 1),
                "total_completions": total_completed,
                "quiz_attempts": quiz_row.total if quiz_row else 0,
                "avg_quiz_score": round(quiz_row.avg_score, 1) if quiz_row and quiz_row.avg_score else 0,
            },
        }

    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid date format or class ID"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching analytics summary: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch analytics summary"
        )
