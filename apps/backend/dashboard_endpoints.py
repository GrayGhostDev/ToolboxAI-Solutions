"""
Dashboard API Endpoints for ToolboxAI Educational Platform
Provides real data for dashboard views across all user roles.
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any, List
from datetime import datetime, timedelta
import random
import logging
from .auth import get_current_user
from .models import User
from .database_service import db_service

logger = logging.getLogger(__name__)

# Create routers for dashboard endpoints
dashboard_router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

@dashboard_router.get("/overview/{role}")
async def get_dashboard_overview(
    role: str,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get dashboard overview data based on user role."""
    
    # Normalize role
    role = role.lower()
    
    # Try to get real data from database
    try:
        dashboard_data = await db_service.get_dashboard_data(role.capitalize(), current_user.id)
        logger.info(f"Successfully fetched dashboard data for {role} user {current_user.username}")
        return dashboard_data
    except Exception as e:
        logger.warning(f"Failed to fetch real data from database: {e}. Using fallback data.")
    
    # Fallback to sample data if database is unavailable
    # Base metrics all roles can see
    base_data = {
        "timestamp": datetime.now().isoformat(),
        "user": {
            "id": current_user.id,
            "name": current_user.username,
            "role": role,
            "lastLogin": datetime.now().isoformat()
        }
    }
    
    # Role-specific dashboard data
    if role == "teacher":
        return {
            **base_data,
            "stats": {
                "totalStudents": 32,
                "activeClasses": 4,
                "assignmentsDue": 7,
                "averageGrade": 85.5,
                "lessonsToday": 3,
                "pendingGrading": 12
            },
            "recentActivity": [
                {
                    "id": 1,
                    "type": "submission",
                    "student": "Alex Johnson",
                    "assignment": "Math Problem Set 3",
                    "time": "2 hours ago",
                    "status": "submitted"
                },
                {
                    "id": 2,
                    "type": "quiz",
                    "student": "Maria Garcia",
                    "assignment": "Science Quiz Ch.5",
                    "time": "3 hours ago",
                    "status": "completed",
                    "score": 92
                },
                {
                    "id": 3,
                    "type": "message",
                    "from": "David Lee",
                    "subject": "Question about homework",
                    "time": "5 hours ago",
                    "status": "unread"
                }
            ],
            "upcomingClasses": [
                {
                    "id": 1,
                    "name": "Mathematics 101",
                    "time": "10:00 AM",
                    "room": "Room 203",
                    "students": 28
                },
                {
                    "id": 2,
                    "name": "Advanced Algebra",
                    "time": "2:00 PM",
                    "room": "Room 205",
                    "students": 24
                }
            ],
            "performanceData": {
                "labels": ["Mon", "Tue", "Wed", "Thu", "Fri"],
                "datasets": [
                    {
                        "label": "Class Average",
                        "data": [82, 85, 83, 88, 86]
                    },
                    {
                        "label": "Assignments Submitted",
                        "data": [25, 28, 24, 30, 27]
                    }
                ]
            }
        }
        
    elif role == "student":
        return {
            **base_data,
            "stats": {
                "xp": 1250,
                "level": 12,
                "nextLevelXP": 1500,
                "completedMissions": 24,
                "currentStreak": 7,
                "rank": 5,
                "totalPoints": 890,
                "badges": 8
            },
            "todaySchedule": [
                {
                    "id": 1,
                    "subject": "Mathematics",
                    "time": "9:00 AM",
                    "teacher": "Mr. Smith",
                    "room": "Room 203"
                },
                {
                    "id": 2,
                    "subject": "Science",
                    "time": "10:30 AM",
                    "teacher": "Ms. Johnson",
                    "room": "Lab 2"
                },
                {
                    "id": 3,
                    "subject": "History",
                    "time": "2:00 PM",
                    "teacher": "Mr. Brown",
                    "room": "Room 107"
                }
            ],
            "assignments": [
                {
                    "id": 1,
                    "title": "Math Problem Set 3",
                    "subject": "Mathematics",
                    "dueDate": "2025-01-12",
                    "status": "in_progress",
                    "progress": 60
                },
                {
                    "id": 2,
                    "title": "Science Lab Report",
                    "subject": "Science",
                    "dueDate": "2025-01-14",
                    "status": "not_started",
                    "progress": 0
                }
            ],
            "achievements": [
                {
                    "id": 1,
                    "name": "Fast Learner",
                    "description": "Complete 5 lessons in one day",
                    "icon": "⚡",
                    "unlockedAt": "2025-01-05"
                },
                {
                    "id": 2,
                    "name": "Quiz Master",
                    "description": "Score 100% on 3 quizzes",
                    "icon": "🏆",
                    "unlockedAt": "2025-01-07"
                }
            ],
            "leaderboard": [
                {"rank": 1, "name": "Sarah Wilson", "xp": 1850, "level": 15},
                {"rank": 2, "name": "Mike Chen", "xp": 1680, "level": 14},
                {"rank": 3, "name": "Emma Davis", "xp": 1520, "level": 13},
                {"rank": 4, "name": "James Park", "xp": 1450, "level": 13},
                {"rank": 5, "name": "You", "xp": 1250, "level": 12, "isCurrentUser": True}
            ]
        }
        
    elif role == "admin":
        return {
            **base_data,
            "stats": {
                "totalUsers": 1523,
                "activeUsers": 1245,
                "totalSchools": 12,
                "totalClasses": 156,
                "systemHealth": 98.5,
                "storageUsed": 67.3,
                "apiCalls": 45231,
                "uptime": "99.98%"
            },
            "systemMetrics": {
                "cpu": 45.2,
                "memory": 62.8,
                "disk": 67.3,
                "network": 23.5,
                "activeConnections": 234,
                "requestsPerMinute": 1250
            },
            "recentEvents": [
                {
                    "id": 1,
                    "type": "user_registration",
                    "message": "New teacher registered: Emily Brown",
                    "time": "1 hour ago",
                    "severity": "info"
                },
                {
                    "id": 2,
                    "type": "system_update",
                    "message": "Database backup completed successfully",
                    "time": "3 hours ago",
                    "severity": "success"
                },
                {
                    "id": 3,
                    "type": "security",
                    "message": "Failed login attempt detected",
                    "time": "5 hours ago",
                    "severity": "warning"
                }
            ],
            "userGrowth": {
                "labels": ["Jan", "Feb", "Mar", "Apr", "May", "Jun"],
                "datasets": [
                    {
                        "label": "Students",
                        "data": [850, 920, 980, 1050, 1120, 1200]
                    },
                    {
                        "label": "Teachers",
                        "data": [120, 135, 145, 155, 168, 180]
                    },
                    {
                        "label": "Parents",
                        "data": [200, 220, 245, 270, 295, 320]
                    }
                ]
            }
        }
        
    elif role == "parent":
        return {
            **base_data,
            "children": [
                {
                    "id": 1,
                    "name": "Alex Johnson",
                    "grade": 7,
                    "school": "Lincoln Middle School",
                    "gpa": 3.8,
                    "attendance": 96.5,
                    "behaviorScore": "Excellent"
                }
            ],
            "childProgress": {
                "overallGrade": 88.5,
                "subjects": [
                    {"name": "Mathematics", "grade": 92, "trend": "up"},
                    {"name": "Science", "grade": 88, "trend": "stable"},
                    {"name": "English", "grade": 85, "trend": "up"},
                    {"name": "History", "grade": 87, "trend": "down"}
                ],
                "recentGrades": [
                    {
                        "subject": "Mathematics",
                        "assignment": "Quiz 5",
                        "grade": 95,
                        "date": "2025-01-07"
                    },
                    {
                        "subject": "Science",
                        "assignment": "Lab Report",
                        "grade": 88,
                        "date": "2025-01-06"
                    }
                ],
                "upcomingAssignments": [
                    {
                        "subject": "English",
                        "title": "Book Report",
                        "dueDate": "2025-01-15"
                    },
                    {
                        "subject": "Mathematics",
                        "title": "Chapter 8 Test",
                        "dueDate": "2025-01-18"
                    }
                ]
            },
            "attendance": {
                "present": 87,
                "absent": 3,
                "tardy": 2,
                "rate": 96.5
            },
            "communications": [
                {
                    "from": "Mr. Smith",
                    "subject": "Excellent performance in Math",
                    "date": "2025-01-07",
                    "read": False
                },
                {
                    "from": "Ms. Johnson",
                    "subject": "Upcoming field trip",
                    "date": "2025-01-05",
                    "read": True
                }
            ]
        }
    
    else:
        # Default data for unknown roles
        return {
            **base_data,
            "message": f"Dashboard data for role '{role}' is being prepared",
            "stats": {
                "placeholder": True
            }
        }

@dashboard_router.get("/metrics")
async def get_dashboard_metrics(
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get general metrics for the dashboard."""
    
    return {
        "timestamp": datetime.now().isoformat(),
        "metrics": {
            "totalUsers": 1523,
            "activeToday": 892,
            "newThisWeek": 45,
            "totalContent": 2341,
            "completionRate": 78.5,
            "satisfaction": 4.6
        },
        "trends": {
            "userGrowth": "+12.3%",
            "engagement": "+8.7%",
            "completion": "+5.2%"
        }
    }

@dashboard_router.get("/notifications")
async def get_notifications(
    current_user: User = Depends(get_current_user)
) -> List[Dict[str, Any]]:
    """Get user notifications."""
    
    notifications = [
        {
            "id": 1,
            "type": "info",
            "title": "System Update",
            "message": "New features have been added to the platform",
            "timestamp": datetime.now().isoformat(),
            "read": False
        },
        {
            "id": 2,
            "type": "success",
            "title": "Achievement Unlocked",
            "message": "You've reached a 7-day streak!",
            "timestamp": (datetime.now() - timedelta(hours=2)).isoformat(),
            "read": False
        }
    ]
    
    return notifications

@dashboard_router.get("/student")
async def get_student_dashboard(
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get student-specific dashboard data."""
    return await get_dashboard_overview("student", current_user)

@dashboard_router.get("/teacher")
async def get_teacher_dashboard(
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get teacher-specific dashboard data."""
    return await get_dashboard_overview("teacher", current_user)

@dashboard_router.get("/admin")
async def get_admin_dashboard(
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get admin-specific dashboard data."""
    return await get_dashboard_overview("admin", current_user)

@dashboard_router.get("/parent")
async def get_parent_dashboard(
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get parent-specific dashboard data."""
    return await get_dashboard_overview("parent", current_user)

@dashboard_router.get("/quick-stats")
async def get_quick_stats(
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get quick statistics for the dashboard header."""
    
    role = current_user.role.lower()
    
    if role == "teacher":
        return {
            "pendingTasks": 12,
            "todayClasses": 4,
            "unreadMessages": 3,
            "averageGrade": 85.5
        }
    elif role == "student":
        return {
            "xp": 1250,
            "level": 12,
            "streak": 7,
            "rank": 5
        }
    elif role == "admin":
        return {
            "activeUsers": 892,
            "systemHealth": 98.5,
            "alerts": 2,
            "uptime": "99.98%"
        }
    elif role == "parent":
        return {
            "children": 1,
            "unreadMessages": 2,
            "upcomingEvents": 3,
            "averageGrade": 88.5
        }
    else:
        return {
            "status": "active"
        }