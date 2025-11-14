"""
Health Check API Module

This package provides comprehensive health monitoring endpoints for the ToolBoxAI platform.

Available Modules:
- health_checks: Core health check endpoints (database, Redis, system)
- integrations: External service integration health checks (Supabase, Pusher, OpenAI)
- agent_health: AI agent system health monitoring
- enhanced_health: Advanced health metrics and diagnostics
- queue_health: Celery queue health monitoring
- supabase_health: Supabase-specific health checks
- load_balancing_health: Load balancer health endpoints
- mcp_health: MCP (Model Context Protocol) health checks
"""

__all__ = [
    "health_checks",
    "integrations",
    "agent_health",
    "enhanced_health",
    "queue_health",
    "supabase_health",
    "load_balancing_health",
    "mcp_health",
]
