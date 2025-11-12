"""
API v1 Router

Main router for API v1 endpoints including the new Roblox AI agent endpoints.
"""

from fastapi import APIRouter

# Import endpoint modules directly to avoid circular imports
from .endpoints import auth
from .endpoints import users
from .endpoints import schools
from .endpoints import classes
from .endpoints import lessons
from .endpoints import assessments
from .endpoints import progress
from .endpoints import gamification
from .endpoints import messages
from .endpoints import analytics
from .endpoints import compliance
from .endpoints import reports
from .endpoints import roblox_ai

# Re-enabled for agent connectivity implementation
from .endpoints import roblox_agents
from .endpoints import direct_agents
from .endpoints import orchestrator
from .endpoints import admin
from .endpoints import observability

# Storage and Media endpoints (2025-10-02)
from .endpoints import uploads
from .endpoints import media

# Tenant Management endpoints (2025-10-02)
from .endpoints import tenant_admin
from .endpoints import tenant_settings
from .endpoints import tenant_billing

# Content Management endpoints (2025-10-02)
from .endpoints import content_versions
from .endpoints import content_workflow
from .endpoints import content_tags

# Analytics endpoints (2025-10-02)
from .endpoints import analytics_reports
from .endpoints import analytics_export
from .endpoints import analytics_dashboards

# User Management endpoints (2025-10-02)
from .endpoints import user_preferences
from .endpoints import user_notifications

# Monitoring endpoints (2025-10-02)
from .endpoints import api_metrics

# MCP Context API - Pusher + Redis Hybrid (2025-11-12)
from .endpoints import mcp_context

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
# Re-enabled for agent connectivity implementation
api_router.include_router(roblox_agents.router, tags=["roblox-agents"])
api_router.include_router(direct_agents.router, tags=["direct-agents"])
api_router.include_router(orchestrator.router, prefix="/orchestrator", tags=["orchestrator"])
api_router.include_router(admin.router, prefix="/admin", tags=["admin"])
api_router.include_router(observability.router, prefix="/observability", tags=["observability"])

# Storage and Media routers (2025-10-02) - High priority endpoints
api_router.include_router(uploads.router, tags=["uploads"])
api_router.include_router(media.router, tags=["media"])

# Tenant Management routers (2025-10-02) - Multi-tenancy support
api_router.include_router(tenant_admin.router, tags=["tenant-admin"])
api_router.include_router(tenant_settings.router, tags=["tenant-settings"])
api_router.include_router(tenant_billing.router, tags=["tenant-billing"])

# Content Management routers (2025-10-02) - Version control and workflow
api_router.include_router(content_versions.router, tags=["content-versions"])
api_router.include_router(content_workflow.router, tags=["content-workflow"])
api_router.include_router(content_tags.router, tags=["content-tags"])

# Analytics routers (2025-10-02) - Reporting and export
api_router.include_router(analytics_reports.router, tags=["analytics-reports"])
api_router.include_router(analytics_export.router, tags=["analytics-export"])
api_router.include_router(analytics_dashboards.router, tags=["analytics-dashboards"])

# User Management routers (2025-10-02) - Preferences and notifications
api_router.include_router(user_preferences.router, tags=["user-preferences"])
api_router.include_router(user_notifications.router, tags=["user-notifications"])

# Monitoring routers (2025-10-02) - Metrics and performance
api_router.include_router(api_metrics.router, tags=["api-metrics"])

# MCP Context router (2025-11-12) - Pusher + Redis hybrid implementation
api_router.include_router(mcp_context.router, tags=["mcp"])

# Health check endpoint
@api_router.get("/health")
async def health_check():
    """API v1 health check"""
    return {"status": "healthy", "version": "1.0.0", "service": "toolboxai-api-v1"}
