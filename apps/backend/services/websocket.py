"""
Dashboard Backend Service for ToolboxAI Educational Platform

Provides dedicated API endpoints for the dashboard frontend on port 8001.
Integrates with the main FastAPI server and provides dashboard-specific functionality.
"""

import asyncio
import json
import logging
import time
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any

import uvicorn
from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from apps.backend.core.config import settings
from apps.backend.api.auth.auth import get_current_user, create_user_token, authenticate_user
from apps.backend.models.schemas import User, BaseResponse

logger = logging.getLogger(__name__)


# Dashboard-specific models
class DashboardStats(BaseModel):
    total_users: int
    total_classes: int
    total_lessons: int
    active_sessions: int
    content_generated_today: int


class DashboardUser(BaseModel):
    id: str
    username: str
    email: str
    role: str
    last_active: Optional[datetime] = None
    grade_level: Optional[int] = None


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user: DashboardUser


# Application lifespan management
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application startup and shutdown"""
    logger.info("Starting Dashboard Backend Service on port 8001")
    app.state.start_time = time.time()
    yield
    logger.info("Shutting down Dashboard Backend Service")


# Create FastAPI app
dashboard_app = FastAPI(
    title="ToolboxAI Dashboard Backend",
    version="1.0.0",
    description="Dashboard-specific API endpoints for ToolboxAI Educational Platform",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS configuration for dashboard
dashboard_app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001",
        "*",  # Allow all origins for development
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
)


# Health check endpoint
@dashboard_app.get("/health")
async def health_check():
    """Dashboard backend health check"""
    return {
        "status": "healthy",
        "service": "dashboard-backend",
        "version": "1.0.0",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "uptime": (
            time.time() - dashboard_app.state.start_time
            if hasattr(dashboard_app.state, "start_time")
            else 0
        ),
    }


# Authentication endpoints
@dashboard_app.post("/auth/login", response_model=TokenResponse)
async def dashboard_login(login_request: LoginRequest):
    """Dashboard-specific login endpoint"""
    try:
        # Authenticate user
        user = await authenticate_user(login_request.username, login_request.password)

        if not user:
            raise HTTPException(status_code=401, detail="Invalid credentials")

        # Create token
        token = create_user_token(user)

        # Convert to dashboard user model
        dashboard_user = DashboardUser(
            id=user.id,
            username=user.username,
            email=user.email,
            role=user.role,
            last_active=getattr(user, "last_active", datetime.now(timezone.utc)),
            grade_level=getattr(user, "grade_level", None),
        )

        return TokenResponse(access_token=token, token_type="bearer", user=dashboard_user)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Dashboard login error: {e}")
        raise HTTPException(status_code=500, detail="Authentication service error")


@dashboard_app.get("/auth/me")
async def get_current_dashboard_user(current_user: User = Depends(get_current_user)):
    """Get current authenticated dashboard user"""
    return DashboardUser(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        role=current_user.role,
        last_active=getattr(current_user, "last_active", datetime.now(timezone.utc)),
        grade_level=getattr(current_user, "grade_level", None),
    )


# Dashboard stats endpoints
@dashboard_app.get("/api/v1/dashboard/stats", response_model=DashboardStats)
async def get_dashboard_stats(current_user: User = Depends(get_current_user)):
    """Get dashboard statistics"""
    try:
        # In a real implementation, these would come from the database
        # For now, return mock data
        return DashboardStats(
            total_users=145,
            total_classes=23,
            total_lessons=387,
            active_sessions=12,
            content_generated_today=8,
        )
    except Exception as e:
        logger.error(f"Dashboard stats error: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch dashboard stats")


@dashboard_app.get("/api/v1/dashboard/overview")
async def get_dashboard_overview(current_user: User = Depends(get_current_user)):
    """Get dashboard overview data"""
    try:
        return {
            "user": {
                "id": current_user.id,
                "username": current_user.username,
                "role": current_user.role,
            },
            "recent_activities": [
                {
                    "id": "activity_1",
                    "type": "content_generated",
                    "description": "Generated Math lesson for Grade 7",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "user": current_user.username,
                },
                {
                    "id": "activity_2",
                    "type": "lesson_completed",
                    "description": "Student completed Science quiz",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "user": "sarah_student",
                },
            ],
            "quick_stats": {
                "active_students": 25,
                "lessons_today": 12,
                "quizzes_completed": 8,
                "avg_score": 87.5,
            },
            "notifications": [
                {
                    "id": "notif_1",
                    "type": "info",
                    "title": "System Update",
                    "message": "New features available in content generation",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            ],
        }
    except Exception as e:
        logger.error(f"Dashboard overview error: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch dashboard overview")


# Content management endpoints
@dashboard_app.get("/api/v1/dashboard/content")
async def get_dashboard_content(current_user: User = Depends(get_current_user)):
    """Get content management data for dashboard"""
    try:
        return {
            "recent_content": [
                {
                    "id": "content_1",
                    "title": "Solar System Exploration",
                    "subject": "Science",
                    "grade_level": 7,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "status": "published",
                    "engagement_score": 92,
                },
                {
                    "id": "content_2",
                    "title": "Fractions and Decimals",
                    "subject": "Mathematics",
                    "grade_level": 5,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "status": "draft",
                    "engagement_score": 0,
                },
            ],
            "content_stats": {
                "total_published": 45,
                "total_drafts": 12,
                "avg_engagement": 85.3,
                "most_popular_subject": "Science",
            },
        }
    except Exception as e:
        logger.error(f"Dashboard content error: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch content data")


# Student progress endpoints
@dashboard_app.get("/api/v1/dashboard/students")
async def get_dashboard_students(current_user: User = Depends(get_current_user)):
    """Get student progress data for dashboard"""
    try:
        return {
            "students": [
                {
                    "id": "student_1",
                    "name": "Alice Johnson",
                    "username": "alice_student",
                    "grade_level": 7,
                    "progress": {
                        "lessons_completed": 23,
                        "quizzes_passed": 18,
                        "avg_score": 89.5,
                        "time_spent_hours": 45.2,
                    },
                    "last_active": datetime.now(timezone.utc).isoformat(),
                    "status": "active",
                },
                {
                    "id": "student_2",
                    "name": "Bob Smith",
                    "username": "bob_student",
                    "grade_level": 7,
                    "progress": {
                        "lessons_completed": 19,
                        "quizzes_passed": 15,
                        "avg_score": 82.1,
                        "time_spent_hours": 38.7,
                    },
                    "last_active": datetime.now(timezone.utc).isoformat(),
                    "status": "active",
                },
            ],
            "class_stats": {
                "total_students": 25,
                "active_students": 23,
                "avg_progress": 78.5,
                "completion_rate": 85.2,
            },
        }
    except Exception as e:
        logger.error(f"Dashboard students error: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch student data")


# Analytics endpoints
@dashboard_app.get("/api/v1/dashboard/analytics")
async def get_dashboard_analytics(current_user: User = Depends(get_current_user)):
    """Get analytics data for dashboard"""
    try:
        return {
            "usage_metrics": {
                "daily_active_users": [
                    {"date": "2024-09-01", "count": 45},
                    {"date": "2024-09-02", "count": 52},
                    {"date": "2024-09-03", "count": 48},
                    {"date": "2024-09-04", "count": 59},
                    {"date": "2024-09-05", "count": 63},
                ],
                "content_generation": [
                    {"date": "2024-09-01", "count": 12},
                    {"date": "2024-09-02", "count": 8},
                    {"date": "2024-09-03", "count": 15},
                    {"date": "2024-09-04", "count": 11},
                    {"date": "2024-09-05", "count": 18},
                ],
                "quiz_completions": [
                    {"date": "2024-09-01", "count": 78},
                    {"date": "2024-09-02", "count": 85},
                    {"date": "2024-09-03", "count": 72},
                    {"date": "2024-09-04", "count": 91},
                    {"date": "2024-09-05", "count": 88},
                ],
            },
            "performance_metrics": {
                "avg_response_time_ms": 245,
                "error_rate_percent": 0.8,
                "uptime_percent": 99.9,
                "satisfaction_score": 4.7,
            },
        }
    except Exception as e:
        logger.error(f"Dashboard analytics error: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch analytics data")


# Settings endpoints
@dashboard_app.get("/api/v1/dashboard/settings")
async def get_dashboard_settings(current_user: User = Depends(get_current_user)):
    """Get dashboard settings"""
    try:
        return {
            "user_preferences": {
                "theme": "light",
                "notifications_enabled": True,
                "auto_save": True,
                "default_grade_level": getattr(current_user, "grade_level", 7),
            },
            "system_settings": {
                "content_auto_publish": False,
                "quiz_time_limit": 30,
                "max_attempts": 3,
                "show_detailed_analytics": True,
            },
        }
    except Exception as e:
        logger.error(f"Dashboard settings error: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch settings")


@dashboard_app.post("/api/v1/dashboard/settings")
async def update_dashboard_settings(
    settings_data: Dict[str, Any], current_user: User = Depends(get_current_user)
):
    """Update dashboard settings"""
    try:
        # In a real implementation, this would update the database
        logger.info(f"Updating settings for user {current_user.id}: {settings_data}")

        return {
            "success": True,
            "message": "Settings updated successfully",
            "updated_settings": settings_data,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as e:
        logger.error(f"Dashboard settings update error: {e}")
        raise HTTPException(status_code=500, detail="Failed to update settings")


# Error handlers
@dashboard_app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    """Handle 404 errors"""
    return JSONResponse(
        status_code=404,
        content={
            "error": "Not Found",
            "message": f"Dashboard endpoint not found: {request.url.path}",
            "service": "dashboard-backend",
        },
    )


@dashboard_app.exception_handler(500)
async def internal_error_handler(request: Request, exc):
    """Handle 500 errors"""
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "message": "Dashboard backend service error",
            "service": "dashboard-backend",
        },
    )


# Main entry point
if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Run the dashboard backend server
    uvicorn.run(
        "server.dashboard_backend:dashboard_app",
        host="127.0.0.1",
        port=8001,
        reload=settings.DEBUG,
        log_level="info",
        workers=1,
    )
