"""
Analytics API Endpoints for ToolboxAI Educational Platform
Provides analytics and gamification data for the dashboard.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import random
import logging
from apps.backend.api.auth.auth import get_current_user
from apps.backend.models.schemas import User
from apps.backend.services.database import db_service

logger = logging.getLogger(__name__)

# Create router for analytics endpoints
analytics_router = APIRouter(prefix="/api/v1/analytics", tags=["Analytics"])

@analytics_router.get("/overview")
async def get_analytics_overview(
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get analytics overview for dashboard."""

    return {
        "total_students": 487,
        "active_students": 423,
        "total_classes": 28,
        "average_completion": 78.5,
        "average_score": 85.3,
        "total_assignments": 156,
        "completed_assignments": 134,
        "pending_submissions": 22,
        "engagement_rate": 87.3,
        "attendance_rate": 95.2
    }

@analytics_router.get("/student-progress")
async def get_student_progress(
    student_id: Optional[str] = Query(None),
    class_id: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get student progress data."""

    # Generate sample progress data
    progress_data = {
        "overall_progress": 75.5,
        "completed_lessons": 45,
        "total_lessons": 60,
        "current_streak": 7,
        "best_streak": 15,
        "xp_earned": 1250,
        "badges_earned": 8,
        "rank": 5,
        "subjects": [
            {"name": "Mathematics", "progress": 82, "grade": "A-"},
            {"name": "Science", "progress": 78, "grade": "B+"},
            {"name": "English", "progress": 90, "grade": "A"},
            {"name": "History", "progress": 65, "grade": "B"}
        ],
        "recent_activity": [
            {"type": "lesson_completed", "title": "Algebra Basics", "time": "2 hours ago", "xp": 50},
            {"type": "quiz_completed", "title": "Chapter 5 Quiz", "time": "1 day ago", "score": 88},
            {"type": "badge_earned", "title": "Math Master", "time": "3 days ago"}
        ]
    }

    return progress_data

@analytics_router.get("/weekly_xp")
async def get_weekly_xp(
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get weekly XP progression for the current user."""
    
    # Generate sample weekly XP data
    days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    current_day = datetime.now().weekday()
    
    xp_data = []
    base_xp = 50
    for i, day in enumerate(days):
        if i <= current_day:
            xp = base_xp + random.randint(-10, 30)
        else:
            xp = 0
        xp_data.append({
            "day": day,
            "xp": xp,
            "completed": i <= current_day
        })
    
    return {
        "week_total": sum(d["xp"] for d in xp_data),
        "daily_average": sum(d["xp"] for d in xp_data) // max(1, current_day + 1),
        "streak": current_day + 1,
        "data": xp_data
    }

@analytics_router.get("/subject_mastery")
async def get_subject_mastery(
    current_user: User = Depends(get_current_user)
) -> List[Dict[str, Any]]:
    """Get subject mastery levels for the current user."""
    
    subjects = [
        {"subject": "Mathematics", "mastery": 85, "progress": 12, "topics_completed": 24},
        {"subject": "Science", "mastery": 78, "progress": 8, "topics_completed": 18},
        {"subject": "English", "mastery": 92, "progress": 5, "topics_completed": 30},
        {"subject": "History", "mastery": 70, "progress": 15, "topics_completed": 14},
        {"subject": "Computer Science", "mastery": 88, "progress": 10, "topics_completed": 22}
    ]
    
    return subjects

# Create router for gamification endpoints
gamification_router = APIRouter(prefix="/gamification", tags=["Gamification"])

@gamification_router.get("/leaderboard")
async def get_leaderboard(
    timeframe: str = Query(default="week", enum=["day", "week", "month", "all"]),
    limit: int = Query(default=10, le=100),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get leaderboard data for the specified timeframe."""
    
    # Generate sample leaderboard data
    names = ["Sarah Wilson", "Mike Chen", "Emma Davis", "James Park", "Lily Zhang", 
             "Alex Johnson", "Sofia Rodriguez", "Daniel Kim", "Maya Patel", "Oliver Smith"]
    
    leaderboard = []
    for i, name in enumerate(names[:limit], 1):
        is_current = i == 5 and name == "You"
        leaderboard.append({
            "rank": i,
            "user_id": f"user_{i}",
            "name": "You" if is_current else name,
            "xp": 2000 - (i * 100) + random.randint(-50, 50),
            "level": 15 - (i // 3),
            "badges": 10 - (i // 2),
            "is_current_user": is_current,
            "movement": random.choice(["up", "down", "same"])
        })
    
    # Ensure current user is in the list
    current_user_in_list = any(l["is_current_user"] for l in leaderboard)
    if not current_user_in_list and len(leaderboard) > 4:
        leaderboard[4] = {
            "rank": 5,
            "user_id": current_user.id,
            "name": "You",
            "xp": 1250,
            "level": 12,
            "badges": 8,
            "is_current_user": True,
            "movement": "up"
        }
    
    return {
        "timeframe": timeframe,
        "last_updated": datetime.now().isoformat(),
        "total_participants": 156,
        "leaderboard": leaderboard,
        "user_stats": {
            "current_rank": 5,
            "previous_rank": 7,
            "xp_to_next_rank": 150,
            "percentile": 96.8
        }
    }

# Create router for compliance endpoints
compliance_router = APIRouter(prefix="/compliance", tags=["Compliance"])

@compliance_router.get("/status")
async def get_compliance_status(
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get compliance status for the current user/organization."""
    
    if current_user.role.lower() != "admin":
        raise HTTPException(status_code=403, detail="Only admins can view compliance status")
    
    return {
        "overall_status": "compliant",
        "compliance_score": 94.5,
        "last_audit": "2025-01-05T10:00:00",
        "next_audit": "2025-02-05T10:00:00",
        "categories": [
            {
                "name": "COPPA",
                "status": "compliant",
                "score": 100,
                "last_checked": "2025-01-07T09:00:00",
                "issues": []
            },
            {
                "name": "FERPA",
                "status": "compliant",
                "score": 96,
                "last_checked": "2025-01-06T14:30:00",
                "issues": []
            },
            {
                "name": "GDPR",
                "status": "warning",
                "score": 88,
                "last_checked": "2025-01-07T11:00:00",
                "issues": [
                    {
                        "severity": "medium",
                        "description": "Data retention policy needs update",
                        "resolution": "Update policy document by Feb 1"
                    }
                ]
            },
            {
                "name": "Accessibility",
                "status": "compliant",
                "score": 92,
                "last_checked": "2025-01-08T08:00:00",
                "issues": []
            }
        ],
        "recent_changes": [
            {
                "date": "2025-01-05T10:00:00",
                "type": "policy_update",
                "description": "Updated privacy policy for COPPA compliance"
            },
            {
                "date": "2025-01-03T14:00:00",
                "type": "training",
                "description": "Staff completed FERPA training"
            }
        ]
    }

# Create router for users management endpoints
users_router = APIRouter(prefix="/users", tags=["Users"])

@users_router.get("/")
async def list_users(
    search: str = Query(default="", description="Search term"),
    role: Optional[str] = Query(default=None, description="Filter by role"),
    limit: int = Query(default=20, le=100),
    offset: int = Query(default=0, ge=0),
    current_user: User = Depends(get_current_user)
) -> List[Dict[str, Any]]:
    """List users (admin only)."""
    
    if current_user.role.lower() != "admin":
        raise HTTPException(status_code=403, detail="Only admins can list users")
    
    # Sample user data
    users = [
        {
            "id": "user_1",
            "username": "john_teacher",
            "email": "john@school.edu",
            "first_name": "John",
            "last_name": "Smith",
            "role": "teacher",
            "status": "active",
            "created_at": "2024-09-01T08:00:00",
            "last_login": "2025-01-08T09:00:00"
        },
        {
            "id": "user_2",
            "username": "sarah_student",
            "email": "sarah@school.edu",
            "first_name": "Sarah",
            "last_name": "Wilson",
            "role": "student",
            "status": "active",
            "created_at": "2024-09-15T10:00:00",
            "last_login": "2025-01-08T14:00:00"
        },
        {
            "id": "user_3",
            "username": "mike_parent",
            "email": "mike@parent.com",
            "first_name": "Mike",
            "last_name": "Johnson",
            "role": "parent",
            "status": "active",
            "created_at": "2024-09-20T11:00:00",
            "last_login": "2025-01-07T18:00:00"
        }
    ]
    
    # Filter by search term
    if search:
        users = [u for u in users if search.lower() in u["username"].lower() or 
                 search.lower() in u["email"].lower() or
                 search.lower() in f"{u['first_name']} {u['last_name']}".lower()]
    
    # Filter by role
    if role:
        users = [u for u in users if u["role"] == role.lower()]
    
    return users[offset:offset + limit]

@users_router.get("/{user_id}")
async def get_user(
    user_id: str,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get user details."""
    
    # Users can view their own profile, admins can view any
    if current_user.role.lower() != "admin" and current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized to view this user")
    
    return {
        "id": user_id,
        "username": "john_teacher",
        "email": "john@school.edu",
        "first_name": "John",
        "last_name": "Smith",
        "role": "teacher",
        "status": "active",
        "created_at": "2024-09-01T08:00:00",
        "last_login": "2025-01-08T09:00:00",
        "profile": {
            "bio": "Math teacher with 10 years of experience",
            "subjects": ["Mathematics", "Physics"],
            "grade_levels": [6, 7, 8],
            "achievements": 15,
            "total_students": 120
        }
    }

# Create router for schools endpoints
schools_router = APIRouter(prefix="/schools", tags=["Schools"])

@schools_router.get("/")
async def list_schools(
    search: str = Query(default="", description="Search term"),
    limit: int = Query(default=20, le=100),
    offset: int = Query(default=0, ge=0),
    current_user: User = Depends(get_current_user)
) -> List[Dict[str, Any]]:
    """List schools (admin only)."""
    
    if current_user.role.lower() != "admin":
        raise HTTPException(status_code=403, detail="Only admins can list schools")
    
    schools = [
        {
            "id": "school_1",
            "name": "Lincoln Middle School",
            "type": "public",
            "address": "123 Main St, Springfield, IL",
            "student_count": 450,
            "teacher_count": 35,
            "admin_count": 5,
            "status": "active",
            "created_at": "2023-08-01T08:00:00"
        },
        {
            "id": "school_2",
            "name": "Washington High School",
            "type": "public",
            "address": "456 Oak Ave, Springfield, IL",
            "student_count": 800,
            "teacher_count": 60,
            "admin_count": 8,
            "status": "active",
            "created_at": "2023-08-01T08:00:00"
        },
        {
            "id": "school_3",
            "name": "Jefferson Elementary",
            "type": "public",
            "address": "789 Elm St, Springfield, IL",
            "student_count": 320,
            "teacher_count": 25,
            "admin_count": 3,
            "status": "active",
            "created_at": "2023-08-15T09:00:00"
        }
    ]
    
    # Filter by search
    if search:
        schools = [s for s in schools if search.lower() in s["name"].lower() or
                   search.lower() in s["address"].lower()]
    
    return schools[offset:offset + limit]

@schools_router.get("/{school_id}")
async def get_school(
    school_id: str,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get school details."""
    
    if current_user.role.lower() not in ["admin", "teacher"]:
        raise HTTPException(status_code=403, detail="Not authorized to view school details")
    
    return {
        "id": school_id,
        "name": "Lincoln Middle School",
        "type": "public",
        "address": "123 Main St, Springfield, IL",
        "phone": "(555) 123-4567",
        "email": "admin@lincolnms.edu",
        "website": "https://lincolnms.edu",
        "principal": "Dr. Jane Wilson",
        "student_count": 450,
        "teacher_count": 35,
        "admin_count": 5,
        "grade_levels": [6, 7, 8],
        "subjects": ["Mathematics", "Science", "English", "History", "PE", "Art", "Music"],
        "status": "active",
        "created_at": "2023-08-01T08:00:00",
        "statistics": {
            "average_gpa": 3.4,
            "attendance_rate": 95.2,
            "graduation_rate": 98.5,
            "college_readiness": 87.3
        }
    }

@schools_router.post("/")
async def create_school(
    school_data: Dict[str, Any],
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Create a new school (admin only)."""
    
    if current_user.role.lower() != "admin":
        raise HTTPException(status_code=403, detail="Only admins can create schools")
    
    # Generate a new school ID
    import uuid
    school_id = f"school_{uuid.uuid4().hex[:8]}"
    
    # Create the new school with provided data
    new_school = {
        "id": school_id,
        "name": school_data.get("name", "New School"),
        "type": school_data.get("type", "public"),
        "address": school_data.get("address", ""),
        "phone": school_data.get("phone", ""),
        "email": school_data.get("email", ""),
        "website": school_data.get("website", ""),
        "student_count": 0,
        "teacher_count": 0,
        "admin_count": 1,
        "status": "active",
        "created_at": datetime.now().isoformat(),
        "created_by": current_user.id
    }
    
    logger.info(f"School created: {school_id} by user {current_user.id}")
    
    return {
        "success": True,
        "message": "School created successfully",
        "school": new_school
    }


# Missing analytics endpoints for Reports page
@analytics_router.get("/trends/engagement")
async def get_engagement_trends(
    start_date: datetime = Query(..., description="Start date for trends"),
    end_date: datetime = Query(..., description="End date for trends"),
    interval: str = Query("day", description="Interval for data points"),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get engagement trend data"""
    
    # Generate trend data points
    trends = []
    current = start_date
    
    while current <= end_date:
        trends.append({
            "date": current.isoformat(),
            "value": random.uniform(70, 95),
            "label": current.strftime("%b %d")
        })
        
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
        "change_percentage": 5.4
    }
    
    # Breakdown by activity type
    activity_breakdown = {
        "video_lessons": 35.2,
        "interactive_exercises": 28.4,
        "quizzes": 22.3,
        "discussions": 14.1
    }
    
    return {
        "trends": trends,
        "summary": summary,
        "activity_breakdown": activity_breakdown,
        "period": {
            "start": start_date.isoformat(),
            "end": end_date.isoformat(),
            "interval": interval
        }
    }

@analytics_router.get("/trends/content")
async def get_content_trends(
    start_date: datetime = Query(..., description="Start date for trends"),
    end_date: datetime = Query(..., description="End date for trends"),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get content consumption trends"""
    
    # Generate content trends
    content_trends = []
    current = start_date
    
    while current <= end_date:
        content_trends.append({
            "date": current.isoformat(),
            "views": random.randint(100, 500),
            "completions": random.randint(50, 300),
            "interactions": random.randint(200, 800),
            "label": current.strftime("%b %d")
        })
        current += timedelta(days=1)
    
    # Popular content
    popular_content = [
        {
            "id": "content1",
            "title": "Introduction to Algebra",
            "type": "video",
            "views": 1523,
            "completion_rate": 85.2,
            "rating": 4.8
        },
        {
            "id": "content2",
            "title": "Physics Lab: Forces and Motion",
            "type": "interactive",
            "views": 1245,
            "completion_rate": 78.9,
            "rating": 4.6
        },
        {
            "id": "content3",
            "title": "World History Timeline",
            "type": "article",
            "views": 987,
            "completion_rate": 92.1,
            "rating": 4.7
        }
    ]
    
    # Content performance metrics
    performance = {
        "total_views": sum(d["views"] for d in content_trends),
        "total_completions": sum(d["completions"] for d in content_trends),
        "average_completion_rate": 82.4,
        "average_rating": 4.5,
        "total_content_items": 256,
        "active_content_items": 189
    }
    
    return {
        "trends": content_trends,
        "popular_content": popular_content,
        "performance": performance,
        "period": {
            "start": start_date.isoformat(),
            "end": end_date.isoformat()
        }
    }

@analytics_router.get("/dashboard")
async def get_dashboard_analytics(
    start_date: datetime = Query(..., description="Start date for analytics"),
    end_date: datetime = Query(..., description="End date for analytics"),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get dashboard analytics for the specified date range"""
    
    # Generate mock analytics data
    overview = {
        "total_students": 487,
        "active_students": 423,
        "total_classes": 28,
        "average_completion": 78.5,
        "average_score": 85.3,
        "total_assignments": 156,
        "completed_assignments": 134,
        "pending_submissions": 22
    }
    
    metrics = [
        {
            "name": "Student Engagement",
            "value": 87.3,
            "change": 5.2,
            "trend": "up"
        },
        {
            "name": "Assignment Completion",
            "value": 78.5,
            "change": -2.1,
            "trend": "down"
        },
        {
            "name": "Average Score",
            "value": 85.3,
            "change": 1.8,
            "trend": "up"
        },
        {
            "name": "Active Time",
            "value": 4.5,
            "change": 0.3,
            "trend": "up"
        }
    ]
    
    # Generate engagement trends
    engagement_trends = []
    current = start_date
    while current <= end_date:
        engagement_trends.append({
            "date": current.isoformat(),
            "value": random.uniform(70, 95),
            "label": current.strftime("%b %d")
        })
        current += timedelta(days=1)
    
    # Top performers
    top_performers = [
        {
            "id": "student1",
            "name": "Emma Wilson",
            "class": "Mathematics 101",
            "score": 98.5,
            "completion": 100,
            "trend": "up"
        },
        {
            "id": "student2",
            "name": "Michael Chen",
            "class": "Science 201",
            "score": 96.2,
            "completion": 98,
            "trend": "up"
        },
        {
            "id": "student3",
            "name": "Sarah Johnson",
            "class": "History 301",
            "score": 94.8,
            "completion": 95,
            "trend": "stable"
        }
    ]
    
    # Recent activity
    recent_activity = [
        {
            "type": "submission",
            "student": "Alex Brown",
            "assignment": "Chapter 5 Quiz",
            "class": "Physics 202",
            "time": (datetime.now() - timedelta(minutes=15)).isoformat(),
            "score": 88
        },
        {
            "type": "completion",
            "student": "Lisa Martinez",
            "assignment": "Essay on Climate Change",
            "class": "Environmental Science",
            "time": (datetime.now() - timedelta(minutes=30)).isoformat(),
            "score": 92
        },
        {
            "type": "started",
            "student": "James Wilson",
            "assignment": "Math Problem Set 4",
            "class": "Algebra II",
            "time": (datetime.now() - timedelta(hours=1)).isoformat()
        }
    ]
    
    return {
        "overview": overview,
        "metrics": metrics,
        "trends": {
            "engagement": engagement_trends,
            "completion": [],
            "scores": []
        },
        "top_performers": top_performers,
        "recent_activity": recent_activity
    }