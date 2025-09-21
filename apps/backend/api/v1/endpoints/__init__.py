"""
API v1 Endpoints Package

This module exports all endpoint routers for the API v1.
Includes both existing and new comprehensive endpoints for the ToolBoxAI platform.
"""

# Keep this file empty to avoid circular imports
# Modules should be imported directly where needed

__all__ = [
    # Authentication & User Management
    "auth",
    "users",
    "user_management_enhanced",

    # Educational Content
    "educational_content",
    "lessons",
    "assessments",
    "enhanced_content",

    # Roblox Integration
    "roblox",
    "roblox_ai",
    "roblox_integration",
    "roblox_integration_enhanced",
    "roblox_environment",
    "roblox_agents",

    # AI & Agent Systems
    "ai_agent_orchestration",
    "ai_chat",
    "agent_swarm",
    "orchestrator",
    "database_swarm",

    # Analytics & Reporting
    "analytics",
    "analytics_reporting",
    "reports",
    "progress",

    # Organization Management
    "schools",
    "classes",
    "admin",

    # Communication & Collaboration
    "messages",
    "pusher_auth",

    # System Features
    "gamification",
    "compliance",
    "privacy",
    "api_keys",
    "dashboard",

    # Mobile & Integration
    "mobile",
    "integration",
    "design_files",

    # Payment & Business
    "stripe_checkout",
    "stripe_webhook",
    "stripe_webhooks",

    # Security
    "password",

    # Template Management
    "prompt_templates"
]

# Comprehensive endpoint registration for main application
# This provides a reference for all available endpoints in the ToolBoxAI platform

ENDPOINT_DESCRIPTIONS = {
    # Enhanced New Endpoints
    "educational_content": "Comprehensive educational content management with AI generation",
    "roblox_integration_enhanced": "Advanced Roblox integration with script generation and asset management",
    "user_management_enhanced": "Enhanced user management with learning preferences and parent access",
    "ai_agent_orchestration": "AI agent coordination with SPARC framework and swarm intelligence",
    "analytics_reporting": "Advanced analytics with real-time dashboards and learning insights",

    # Existing Core Endpoints
    "auth": "Authentication and authorization",
    "users": "Basic user management",
    "lessons": "Lesson management and delivery",
    "assessments": "Assessment creation and grading",
    "roblox": "Core Roblox platform integration",
    "ai_chat": "AI-powered chat and assistance",
    "analytics": "Basic analytics and metrics",
    "schools": "School and district management",
    "classes": "Classroom and group management",
    "progress": "Student progress tracking",
    "gamification": "Achievement and reward systems",
    "messages": "Messaging and communication",
    "compliance": "Privacy and compliance features",
    "reports": "Report generation and management",
    "dashboard": "Dashboard configuration and data",
    "admin": "Administrative functions",
    "mobile": "Mobile app integration",
    "integration": "Third-party integrations",
    "privacy": "Privacy controls and data management",
    "api_keys": "API key management",
    "pusher_auth": "Real-time communication authentication",
    "orchestrator": "Basic agent orchestration",
    "agent_swarm": "Multi-agent coordination",
    "database_swarm": "Database agent operations",
    "stripe_checkout": "Payment processing",
    "stripe_webhook": "Payment webhook handling",
    "design_files": "Design asset management",
    "password": "Password management",
    "prompt_templates": "AI prompt template management"
}

# Router priority for registration (higher priority = registered first)
ROUTER_PRIORITY = {
    # Core authentication - highest priority
    "auth": 100,
    "user_management_enhanced": 95,
    "users": 90,

    # Educational content - high priority
    "educational_content": 85,
    "lessons": 80,
    "assessments": 80,

    # Roblox integration - high priority
    "roblox_integration_enhanced": 75,
    "roblox": 70,
    "roblox_ai": 70,

    # AI systems - medium-high priority
    "ai_agent_orchestration": 65,
    "ai_chat": 60,
    "orchestrator": 55,

    # Analytics - medium priority
    "analytics_reporting": 50,
    "analytics": 45,
    "reports": 45,

    # Organization - medium priority
    "schools": 40,
    "classes": 40,
    "progress": 40,

    # Communication - medium priority
    "messages": 35,
    "pusher_auth": 35,

    # System features - lower priority
    "gamification": 30,
    "dashboard": 30,
    "admin": 25,

    # Utilities - lowest priority
    "compliance": 20,
    "privacy": 20,
    "api_keys": 15,
    "mobile": 15,
    "integration": 15,
    "password": 10,
    "prompt_templates": 10
}

# Endpoint feature flags for conditional registration
FEATURE_FLAGS = {
    "enhanced_endpoints": True,  # Enable new comprehensive endpoints
    "roblox_advanced": True,     # Enable advanced Roblox features
    "ai_orchestration": True,    # Enable AI agent orchestration
    "analytics_advanced": True,  # Enable advanced analytics
    "user_management_v2": True,  # Enable enhanced user management
    "experimental": False,      # Enable experimental endpoints
    "legacy_support": True       # Maintain legacy endpoint compatibility
}