"""
API v1 Router

Main router for API v1 endpoints including the new Roblox AI agent endpoints.
"""

from fastapi import APIRouter
from .endpoints import (
    auth,
    users,
    schools,
    classes,
    lessons,
    assessments,
    progress,
    gamification,
    messages,
    analytics,
    compliance,
    reports,
    roblox_ai
)

# Create main API v1 router
api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(schools.router, prefix="/schools", tags=["schools"])
api_router.include_router(classes.router, prefix="/classes", tags=["classes"])
api_router.include_router(lessons.router, prefix="/lessons", tags=["lessons"])
api_router.include_router(assessments.router, prefix="/assessments", tags=["assessments"])
api_router.include_router(progress.router, prefix="/progress", tags=["progress"])
api_router.include_router(gamification.router, prefix="/gamification", tags=["gamification"])
api_router.include_router(messages.router, prefix="/messages", tags=["messages"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["analytics"])
api_router.include_router(compliance.router, prefix="/compliance", tags=["compliance"])
api_router.include_router(reports.router, prefix="/reports", tags=["reports"])
api_router.include_router(roblox_ai.router, tags=["roblox-ai"])

# Health check endpoint
@api_router.get("/health")
async def health_check():
    """API v1 health check"""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "service": "toolboxai-api-v1"
    }