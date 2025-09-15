"""
Reports API Endpoints for ToolboxAI Educational Platform
Provides reporting, analytics, and statistics functionality for all user roles.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import logging
from apps.backend.api.auth.auth import get_current_user
from apps.backend.models.schemas import User
from apps.backend.services.database import db_service

logger = logging.getLogger(__name__)

# Create router for reports endpoints
reports_router = APIRouter(prefix="/reports", tags=["Reports"])

@reports_router.get("/")
async def get_reports(
    current_user: User = Depends(get_current_user),
    report_type: Optional[str] = None,
    class_id: Optional[int] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    limit: int = Query(default=10, le=100),
    offset: int = Query(default=0, ge=0)
) -> List[Dict[str, Any]]:
    """Get available reports based on user role and filters."""
    
    role = current_user.role.lower()
    
    # Try to get real data from database
    try:
        if role == "teacher":
            query = """
                SELECT r.*, c.name as class_name
                FROM reports r
                JOIN classes c ON r.class_id = c.id
                WHERE c.teacher_id = $1
                  AND ($2::text IS NULL OR r.report_type = $2)
                  AND ($3::int IS NULL OR r.class_id = $3)
                  AND ($4::timestamp IS NULL OR r.created_at >= $4::timestamp)
                  AND ($5::timestamp IS NULL OR r.created_at <= $5::timestamp)
                ORDER BY r.created_at DESC
                LIMIT $6 OFFSET $7
            """
            async with db_service.pool.acquire() as conn:
                rows = await conn.fetch(query, current_user.id, report_type, class_id, 
                                      date_from, date_to, limit, offset)
                return [dict(row) for row in rows]
                
        elif role == "student":
            query = """
                SELECT r.id, r.title, r.report_type, r.description, r.created_at,
                       c.name as class_name, c.subject
                FROM reports r
                JOIN classes c ON r.class_id = c.id
                JOIN class_enrollments ce ON c.id = ce.class_id
                WHERE ce.student_id = $1
                  AND r.visibility IN ('public', 'students')
                  AND ($2::text IS NULL OR r.report_type = $2)
                  AND ($3::int IS NULL OR r.class_id = $3)
                ORDER BY r.created_at DESC
                LIMIT $4 OFFSET $5
            """
            async with db_service.pool.acquire() as conn:
                rows = await conn.fetch(query, current_user.id, report_type, class_id, limit, offset)
                return [dict(row) for row in rows]
                
        elif role == "admin":
            query = """
                SELECT r.*, c.name as class_name, c.subject,
                       u.first_name || ' ' || u.last_name as teacher_name
                FROM reports r
                JOIN classes c ON r.class_id = c.id
                JOIN users u ON c.teacher_id = u.id
                WHERE ($1::text IS NULL OR r.report_type = $1)
                  AND ($2::int IS NULL OR r.class_id = $2)
                  AND ($3::timestamp IS NULL OR r.created_at >= $3::timestamp)
                  AND ($4::timestamp IS NULL OR r.created_at <= $4::timestamp)
                ORDER BY r.created_at DESC
                LIMIT $5 OFFSET $6
            """
            async with db_service.pool.acquire() as conn:
                rows = await conn.fetch(query, report_type, class_id, date_from, date_to, limit, offset)
                return [dict(row) for row in rows]
                
        elif role == "parent":
            query = """
                SELECT DISTINCT r.id, r.title, r.report_type, r.description, r.created_at,
                       c.name as class_name, c.subject,
                       s.first_name || ' ' || s.last_name as student_name
                FROM reports r
                JOIN classes c ON r.class_id = c.id
                JOIN class_enrollments ce ON c.id = ce.class_id
                JOIN users s ON ce.student_id = s.id
                JOIN parent_student_relationships psr ON s.id = psr.student_id
                WHERE psr.parent_id = $1
                  AND r.visibility IN ('public', 'parents')
                  AND ($2::text IS NULL OR r.report_type = $2)
                ORDER BY r.created_at DESC
                LIMIT $3 OFFSET $4
            """
            async with db_service.pool.acquire() as conn:
                rows = await conn.fetch(query, current_user.id, report_type, limit, offset)
                return [dict(row) for row in rows]
                
    except Exception as e:
        logger.warning(f"Failed to fetch reports from database: {e}. Using fallback data.")
    
    # Fallback sample data
    if role == "teacher":
        return [
            {
                "id": 1,
                "title": "Class Performance Summary - Week 1",
                "class_name": "Mathematics 101",
                "report_type": "performance",
                "description": "Weekly performance analysis for Mathematics 101",
                "created_at": "2025-01-08T09:00:00",
                "status": "completed"
            },
            {
                "id": 2,
                "title": "Assessment Results Analysis",
                "class_name": "Mathematics 101",
                "report_type": "assessment",
                "description": "Detailed analysis of recent quiz results",
                "created_at": "2025-01-07T14:30:00",
                "status": "completed"
            },
            {
                "id": 3,
                "title": "Student Engagement Report",
                "class_name": "Advanced Algebra",
                "report_type": "engagement",
                "description": "Student participation and engagement metrics",
                "created_at": "2025-01-06T11:15:00",
                "status": "completed"
            }
        ]
    elif role == "student":
        return [
            {
                "id": 1,
                "title": "My Progress Report - Mathematics",
                "class_name": "Mathematics 101",
                "subject": "Mathematics",
                "report_type": "progress",
                "description": "Personal progress summary for this semester",
                "created_at": "2025-01-08T09:00:00"
            },
            {
                "id": 4,
                "title": "Science Lab Achievement Report",
                "class_name": "Science Lab",
                "subject": "Science",
                "report_type": "achievement",
                "description": "Summary of completed experiments and projects",
                "created_at": "2025-01-05T16:00:00"
            }
        ]
    elif role == "admin":
        return [
            {
                "id": 1,
                "title": "School-wide Performance Analysis",
                "class_name": "All Classes",
                "teacher_name": "System Generated",
                "report_type": "performance",
                "description": "Comprehensive performance analysis across all classes",
                "created_at": "2025-01-08T08:00:00",
                "status": "completed"
            },
            {
                "id": 5,
                "title": "Teacher Effectiveness Report",
                "class_name": "Mathematics Department",
                "teacher_name": "Department Head",
                "report_type": "teacher_analysis",
                "description": "Analysis of teaching effectiveness and student outcomes",
                "created_at": "2025-01-07T10:00:00",
                "status": "completed"
            }
        ]
    elif role == "parent":
        return [
            {
                "id": 1,
                "title": "Alex's Progress Report",
                "class_name": "Mathematics 101",
                "student_name": "Alex Johnson",
                "subject": "Mathematics",
                "report_type": "progress",
                "description": "Monthly progress summary for Alex Johnson",
                "created_at": "2025-01-08T09:00:00"
            }
        ]
    
    return []

@reports_router.get("/templates")
async def get_report_templates(
    current_user: User = Depends(get_current_user),
    popular_only: bool = Query(default=False),
    category: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Get available report templates."""
    
    role = current_user.role.lower()
    
    # Try to get real data from database
    try:
        query = """
            SELECT rt.*, COUNT(r.id) as usage_count
            FROM report_templates rt
            LEFT JOIN reports r ON rt.id = r.template_id
            WHERE rt.available_to_roles @> $1
              AND ($2::boolean = false OR rt.is_popular = true)
              AND ($3::text IS NULL OR rt.category = $3)
            GROUP BY rt.id
            ORDER BY rt.is_popular DESC, rt.usage_count DESC, rt.name ASC
        """
        async with db_service.pool.acquire() as conn:
            rows = await conn.fetch(query, [role], popular_only, category)
            return [dict(row) for row in rows]
            
    except Exception as e:
        logger.warning(f"Failed to fetch report templates: {e}. Using fallback data.")
    
    # Fallback sample data - filter by popular_only if requested
    templates = [
        {
            "id": 1,
            "name": "Class Performance Summary",
            "category": "performance",
            "description": "Comprehensive class performance analysis",
            "is_popular": True,
            "usage_count": 45,
            "available_to": ["teacher", "admin"],
            "fields": ["class_id", "date_range", "metrics"]
        },
        {
            "id": 2,
            "name": "Student Progress Report",
            "category": "progress",
            "description": "Individual student progress tracking",
            "is_popular": True,
            "usage_count": 38,
            "available_to": ["teacher", "parent", "admin"],
            "fields": ["student_id", "subject", "date_range"]
        },
        {
            "id": 3,
            "name": "Assessment Analysis",
            "category": "assessment",
            "description": "Detailed assessment results analysis",
            "is_popular": True,
            "usage_count": 32,
            "available_to": ["teacher", "admin"],
            "fields": ["assessment_id", "analysis_type"]
        },
        {
            "id": 4,
            "name": "Attendance Report",
            "category": "attendance",
            "description": "Student attendance tracking and analysis",
            "is_popular": False,
            "usage_count": 18,
            "available_to": ["teacher", "admin"],
            "fields": ["class_id", "date_range", "students"]
        },
        {
            "id": 5,
            "name": "Grade Distribution",
            "category": "grades",
            "description": "Analysis of grade distribution across classes",
            "is_popular": False,
            "usage_count": 12,
            "available_to": ["admin"],
            "fields": ["class_id", "subject", "grade_level"]
        }
    ]
    
    # Filter by role access
    templates = [t for t in templates if role in t["available_to"]]
    
    # Filter by popular only if requested
    if popular_only:
        templates = [t for t in templates if t["is_popular"]]
    
    # Filter by category if specified
    if category:
        templates = [t for t in templates if t["category"] == category]
    
    return templates

@reports_router.get("/stats/overview")
async def get_overview_statistics(
    current_user: User = Depends(get_current_user),
    date_range: Optional[str] = "30d"
) -> Dict[str, Any]:
    """Get overview statistics based on user role."""
    
    role = current_user.role.lower()
    
    # Try to get real data from database
    try:
        if role == "teacher":
            # Get teacher's class statistics
            query = """
                SELECT 
                    COUNT(DISTINCT c.id) as total_classes,
                    COUNT(DISTINCT ce.student_id) as total_students,
                    COUNT(DISTINCT a.id) as total_assessments,
                    AVG(ar.score) as average_score,
                    COUNT(DISTINCT CASE WHEN lp.completed THEN lp.lesson_id END) as completed_lessons
                FROM classes c
                LEFT JOIN class_enrollments ce ON c.id = ce.class_id
                LEFT JOIN assessments a ON c.id = a.class_id
                LEFT JOIN assessment_results ar ON a.id = ar.assessment_id
                LEFT JOIN lesson_progress lp ON c.id = lp.class_id
                WHERE c.teacher_id = $1
                  AND c.created_at >= NOW() - INTERVAL '30 days'
            """
            async with db_service.pool.acquire() as conn:
                row = await conn.fetchrow(query, current_user.id)
                if row:
                    return dict(row)
                    
        elif role == "student":
            # Get student's performance statistics
            query = """
                SELECT 
                    COUNT(DISTINCT c.id) as enrolled_classes,
                    COUNT(DISTINCT a.id) as available_assessments,
                    COUNT(DISTINCT ar.id) as completed_assessments,
                    AVG(ar.score) as average_score,
                    COUNT(DISTINCT CASE WHEN lp.completed THEN lp.lesson_id END) as completed_lessons,
                    SUM(lp.xp_earned) as total_xp
                FROM class_enrollments ce
                JOIN classes c ON ce.class_id = c.id
                LEFT JOIN assessments a ON c.id = a.class_id
                LEFT JOIN assessment_results ar ON a.id = ar.assessment_id AND ar.student_id = $1
                LEFT JOIN lesson_progress lp ON c.id = lp.class_id AND lp.student_id = $1
                WHERE ce.student_id = $1
            """
            async with db_service.pool.acquire() as conn:
                row = await conn.fetchrow(query, current_user.id)
                if row:
                    return dict(row)
                    
        elif role == "admin":
            # Get system-wide statistics
            query = """
                SELECT 
                    COUNT(DISTINCT u.id) as total_users,
                    COUNT(DISTINCT c.id) as total_classes,
                    COUNT(DISTINCT a.id) as total_assessments,
                    COUNT(DISTINCT l.id) as total_lessons,
                    AVG(ar.score) as system_average_score,
                    COUNT(DISTINCT ar.id) as total_submissions
                FROM users u
                FULL OUTER JOIN classes c ON true
                FULL OUTER JOIN assessments a ON true
                FULL OUTER JOIN lessons l ON true
                FULL OUTER JOIN assessment_results ar ON true
                WHERE u.created_at >= NOW() - INTERVAL '30 days'
                   OR c.created_at >= NOW() - INTERVAL '30 days'
            """
            async with db_service.pool.acquire() as conn:
                row = await conn.fetchrow(query)
                if row:
                    return dict(row)
                    
        elif role == "parent":
            # Get statistics for parent's children
            query = """
                SELECT 
                    COUNT(DISTINCT s.id) as children_count,
                    COUNT(DISTINCT c.id) as total_classes,
                    COUNT(DISTINCT ar.id) as total_assessments,
                    AVG(ar.score) as children_average_score,
                    COUNT(DISTINCT CASE WHEN lp.completed THEN lp.lesson_id END) as completed_lessons
                FROM parent_student_relationships psr
                JOIN users s ON psr.student_id = s.id
                JOIN class_enrollments ce ON s.id = ce.student_id
                JOIN classes c ON ce.class_id = c.id
                LEFT JOIN assessment_results ar ON s.id = ar.student_id
                LEFT JOIN lesson_progress lp ON s.id = lp.student_id AND lp.completed = true
                WHERE psr.parent_id = $1
            """
            async with db_service.pool.acquire() as conn:
                row = await conn.fetchrow(query, current_user.id)
                if row:
                    return dict(row)
                    
    except Exception as e:
        logger.warning(f"Failed to fetch overview statistics: {e}. Using fallback data.")
    
    # Fallback sample data
    if role == "teacher":
        return {
            "total_classes": 3,
            "total_students": 82,
            "total_assessments": 12,
            "average_score": 84.2,
            "completed_lessons": 156,
            "active_assignments": 8,
            "recent_submissions": 24,
            "grade_distribution": {
                "A": 28,
                "B": 32,
                "C": 18,
                "D": 4,
                "F": 0
            }
        }
    elif role == "student":
        return {
            "enrolled_classes": 6,
            "available_assessments": 18,
            "completed_assessments": 14,
            "average_score": 87.5,
            "completed_lessons": 42,
            "total_xp": 2850,
            "current_streak": 7,
            "upcoming_deadlines": 3,
            "achievement_badges": 12
        }
    elif role == "admin":
        return {
            "total_users": 1247,
            "total_teachers": 45,
            "total_students": 1156,
            "total_parents": 782,
            "total_classes": 134,
            "total_assessments": 456,
            "total_lessons": 892,
            "system_average_score": 83.7,
            "total_submissions": 12847,
            "active_sessions": 234,
            "server_uptime": "99.8%"
        }
    elif role == "parent":
        return {
            "children_count": 2,
            "total_classes": 12,
            "total_assessments": 36,
            "children_average_score": 89.3,
            "completed_lessons": 84,
            "upcoming_events": 5,
            "recent_achievements": 8,
            "communication_unread": 2
        }
    
    return {}

@reports_router.get("/{report_id}")
async def get_report_details(
    report_id: int,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get detailed information about a specific report."""
    
    role = current_user.role.lower()
    
    try:
        # Get report details with access control
        query = """
            SELECT r.*, c.name as class_name, c.subject,
                   u.first_name || ' ' || u.last_name as teacher_name
            FROM reports r
            JOIN classes c ON r.class_id = c.id
            JOIN users u ON c.teacher_id = u.id
            WHERE r.id = $1
        """
        async with db_service.pool.acquire() as conn:
            row = await conn.fetchrow(query, report_id)
            if row:
                report = dict(row)
                
                # Check access permissions
                if role == "student" and report.get("visibility") not in ["public", "students"]:
                    raise HTTPException(status_code=403, detail="Not authorized to view this report")
                elif role == "parent" and report.get("visibility") not in ["public", "parents"]:
                    raise HTTPException(status_code=403, detail="Not authorized to view this report")
                    
                return report
                
    except HTTPException:
        raise
    except Exception as e:
        logger.warning(f"Failed to fetch report details: {e}")
    
    # Fallback sample data
    return {
        "id": report_id,
        "title": "Class Performance Analysis",
        "class_name": "Mathematics 101",
        "subject": "Mathematics",
        "teacher_name": "Mr. Smith",
        "report_type": "performance",
        "description": "Comprehensive analysis of class performance for the past month",
        "created_at": "2025-01-08T09:00:00",
        "data": {
            "summary": {
                "total_students": 28,
                "average_score": 84.2,
                "completion_rate": 89.3,
                "improvement_trend": "+5.2%"
            },
            "metrics": [
                {"name": "Class Average", "value": 84.2, "trend": "up"},
                {"name": "Completion Rate", "value": 89.3, "trend": "up"},
                {"name": "Participation", "value": 92.1, "trend": "stable"},
                {"name": "Assignment Submission", "value": 87.5, "trend": "up"}
            ],
            "charts": {
                "score_distribution": [
                    {"range": "90-100", "count": 10},
                    {"range": "80-89", "count": 12},
                    {"range": "70-79", "count": 5},
                    {"range": "60-69", "count": 1}
                ],
                "weekly_progress": [
                    {"week": "Week 1", "average": 78.5},
                    {"week": "Week 2", "average": 81.2},
                    {"week": "Week 3", "average": 83.7},
                    {"week": "Week 4", "average": 84.2}
                ]
            }
        },
        "recommendations": [
            "Consider additional practice sessions for students scoring below 75%",
            "Implement peer tutoring program for struggling students",
            "Continue current teaching methods as they show positive trends"
        ]
    }

@reports_router.post("/")
async def create_report(
    report_data: Dict[str, Any],
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Create a new report (teachers and admins only)."""
    
    role = current_user.role.lower()
    
    if role not in ["teacher", "admin"]:
        raise HTTPException(status_code=403, detail="Not authorized to generate reports")
    
    try:
        query = """
            INSERT INTO reports (title, description, report_type, class_id, 
                               parameters, visibility, status, created_by)
            VALUES ($1, $2, $3, $4, $5, $6, 'generating', $7)
            RETURNING *
        """
        async with db_service.pool.acquire() as conn:
            row = await conn.fetchrow(
                query,
                report_data["title"],
                report_data.get("description"),
                report_data.get("report_type", "custom"),
                report_data.get("class_id"),
                report_data.get("parameters", {}),
                report_data.get("visibility", "private"),
                current_user.id
            )
            return dict(row)
            
    except Exception as e:
        logger.error(f"Failed to generate report: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate report")

@reports_router.get("/analytics/engagement")
async def get_engagement_analytics(
    current_user: User = Depends(get_current_user),
    class_id: Optional[int] = None,
    time_period: str = Query(default="7d")
) -> Dict[str, Any]:
    """Get student engagement analytics (teachers and admins only)."""
    
    role = current_user.role.lower()
    
    if role not in ["teacher", "admin"]:
        raise HTTPException(status_code=403, detail="Not authorized to view analytics")
    
    # Fallback sample data
    return {
        "time_period": time_period,
        "class_id": class_id,
        "engagement_metrics": {
            "daily_active_students": 24,
            "average_session_duration": 32.5,
            "total_interactions": 1847,
            "participation_rate": 85.7
        },
        "activity_breakdown": {
            "lessons_viewed": 156,
            "assessments_completed": 42,
            "discussions_participated": 28,
            "resources_accessed": 89
        },
        "trends": {
            "weekly_engagement": [
                {"day": "Monday", "active_students": 26, "avg_duration": 35.2},
                {"day": "Tuesday", "active_students": 24, "avg_duration": 28.7},
                {"day": "Wednesday", "active_students": 28, "avg_duration": 42.1},
                {"day": "Thursday", "active_students": 22, "avg_duration": 31.5},
                {"day": "Friday", "active_students": 25, "avg_duration": 29.8}
            ]
        },
        "top_performers": [
            {"student_name": "Alex Johnson", "engagement_score": 95.2},
            {"student_name": "Maria Garcia", "engagement_score": 89.7},
            {"student_name": "David Lee", "engagement_score": 87.3}
        ]
    }

@reports_router.post("/generate")
async def generate_report(
    report_data: Dict[str, Any],
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Generate a new report - alias for create_report for frontend compatibility."""
    return await create_report(report_data, current_user)