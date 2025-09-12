"""
Analytics API Endpoints for ToolboxAI Educational Platform
Provides analytics and gamification data for the dashboard.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import random
import logging
from ....api.auth.auth import get_current_user
from ....models.schemas import User
from ....services.database import db_service

logger = logging.getLogger(__name__)

# Create router for analytics endpoints
analytics_router = APIRouter(prefix="/analytics", tags=["Analytics"])

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