"""
Router Registration for ToolboxAI Backend
Centralized router management for all API endpoints

Priority-based registration system:
- Tier 1 (90-100): Authentication & User Management
- Tier 2 (80-85): Core Educational Features
- Tier 3 (70-75): Roblox Integration
- Tier 4 (55-65): AI & Communication
- Tier 5 (40-50): Analytics & Management
"""

import logging

from fastapi import FastAPI

logger = logging.getLogger(__name__)


def register_routers(app: FastAPI) -> None:
    """
    Register all API routers with the FastAPI application

    Routers are registered in priority order to ensure critical
    endpoints are available first.
    """
    logger.info("=" * 60)
    logger.info("ROUTER REGISTRATION - Priority-Based System")
    logger.info("=" * 60)

    registration_stats = {"total": 0, "successful": 0, "failed": 0, "tiers": {}}

    # =========================================================================
    # TIER 1: AUTHENTICATION & USER MANAGEMENT (Priority 90-100)
    # =========================================================================
    tier_name = "Tier 1: Authentication & Users"
    logger.info(f"\n📋 {tier_name} (Priority 90-100)")
    logger.info("-" * 60)

    tier1_routers = [
        ("auth", "/api/v1/auth", "apps.backend.api.v1.endpoints.auth", ["authentication"]),
        ("users", "/api/v1/users", "apps.backend.api.v1.endpoints.users", ["users"]),
        (
            "user_management_enhanced",
            "/api/v1/user-management",
            "apps.backend.api.v1.endpoints.user_management_enhanced",
            ["user-management"],
        ),
    ]

    tier1_stats = _register_tier_routers(app, tier1_routers, tier_name)
    registration_stats["tiers"][tier_name] = tier1_stats

    # =========================================================================
    # TIER 2: CORE EDUCATIONAL FEATURES (Priority 80-85)
    # =========================================================================
    tier_name = "Tier 2: Educational Content"
    logger.info(f"\n📚 {tier_name} (Priority 80-85)")
    logger.info("-" * 60)

    tier2_routers = [
        (
            "educational_content",
            "/api/v1/educational-content",
            "apps.backend.api.v1.endpoints.educational_content",
            ["educational-content"],
        ),
        ("lessons", "/api/v1/lessons", "apps.backend.api.v1.endpoints.lessons", ["lessons"]),
        (
            "assessments",
            "/api/v1/assessments",
            "apps.backend.api.v1.endpoints.assessments",
            ["assessments"],
        ),
    ]

    tier2_stats = _register_tier_routers(app, tier2_routers, tier_name)
    registration_stats["tiers"][tier_name] = tier2_stats

    # =========================================================================
    # TIER 3: ROBLOX INTEGRATION (Priority 70-75)
    # =========================================================================
    tier_name = "Tier 3: Roblox Integration"
    logger.info(f"\n🎮 {tier_name} (Priority 70-75)")
    logger.info("-" * 60)

    tier3_routers = [
        (
            "roblox_integration_enhanced",
            "/api/v1/roblox/enhanced",
            "apps.backend.api.v1.endpoints.roblox_integration_enhanced",
            ["roblox"],
        ),
        ("roblox_ai", "/api/v1/roblox/ai", "apps.backend.api.v1.endpoints.roblox_ai", ["roblox"]),
        ("roblox", "/api/v1/roblox", "apps.backend.api.v1.endpoints.roblox", ["roblox"]),
        (
            "roblox_agents",
            "/api/v1/roblox/agents",
            "apps.backend.api.v1.endpoints.roblox_agents",
            ["roblox"],
        ),
        (
            "roblox_environment",
            "/api/v1/roblox/environment",
            "apps.backend.api.v1.endpoints.roblox_environment",
            ["roblox"],
        ),
    ]

    tier3_stats = _register_tier_routers(app, tier3_routers, tier_name)
    registration_stats["tiers"][tier_name] = tier3_stats

    # =========================================================================
    # TIER 4: AI AGENTS & COMMUNICATION (Priority 55-65)
    # =========================================================================
    tier_name = "Tier 4: AI & Communication"
    logger.info(f"\n🤖 {tier_name} (Priority 55-65)")
    logger.info("-" * 60)

    tier4_routers = [
        (
            "ai_agent_orchestration",
            "/api/v1/ai/orchestration",
            "apps.backend.api.v1.endpoints.ai_agent_orchestration",
            ["ai"],
        ),
        ("ai_chat", "/api/v1/ai/chat", "apps.backend.api.v1.endpoints.ai_chat", ["ai"]),
        ("agents", "/api/v1/agents", "apps.backend.api.v1.endpoints.agents", ["agents"]),
        (
            "pusher_auth",
            "/api/v1/pusher/auth",
            "apps.backend.api.v1.endpoints.pusher_auth",
            ["pusher"],
        ),
        ("messages", "/api/v1/messages", "apps.backend.api.v1.endpoints.messages", ["messages"]),
    ]

    tier4_stats = _register_tier_routers(app, tier4_routers, tier_name)
    registration_stats["tiers"][tier_name] = tier4_stats

    # =========================================================================
    # TIER 5: ANALYTICS & MANAGEMENT (Priority 40-50)
    # =========================================================================
    tier_name = "Tier 5: Analytics & Management"
    logger.info(f"\n📊 {tier_name} (Priority 40-50)")
    logger.info("-" * 60)

    tier5_routers = [
        (
            "analytics_reporting",
            "/api/v1/analytics/reporting",
            "apps.backend.api.v1.endpoints.analytics_reporting",
            ["analytics"],
        ),
        (
            "analytics",
            "/api/v1/analytics",
            "apps.backend.api.v1.endpoints.analytics",
            ["analytics"],
        ),
        ("classes", "/api/v1/classes", "apps.backend.api.v1.endpoints.classes", ["classes"]),
        ("schools", "/api/v1/schools", "apps.backend.api.v1.endpoints.schools", ["schools"]),
        ("progress", "/api/v1/progress", "apps.backend.api.v1.endpoints.progress", ["progress"]),
        ("reports", "/api/v1/reports", "apps.backend.api.v1.endpoints.reports", ["reports"]),
    ]

    tier5_stats = _register_tier_routers(app, tier5_routers, tier_name)
    registration_stats["tiers"][tier_name] = tier5_stats

    # =========================================================================
    # LEGACY ROUTERS (Backward Compatibility)
    # =========================================================================
    logger.info(f"\n🔄 Legacy Routes (Backward Compatibility)")
    logger.info("-" * 60)

    try:
        from apps.backend.api.routers.courses import router as courses_router

        app.include_router(courses_router, tags=["courses"])
        logger.info("✓ Registered courses router at /api/v1/courses")
        registration_stats["successful"] += 1
    except ImportError as e:
        logger.warning(f"⚠ Could not import courses router: {e}")
        registration_stats["failed"] += 1
    except Exception as e:
        logger.error(f"✗ Error registering courses router: {e}")
        registration_stats["failed"] += 1

    # =========================================================================
    # REGISTRATION SUMMARY
    # =========================================================================
    logger.info("\n" + "=" * 60)
    logger.info("ROUTER REGISTRATION SUMMARY")
    logger.info("=" * 60)

    total_successful = (
        sum(tier["successful"] for tier in registration_stats["tiers"].values())
        + registration_stats["successful"]
    )
    total_failed = (
        sum(tier["failed"] for tier in registration_stats["tiers"].values())
        + registration_stats["failed"]
    )
    total_attempted = total_successful + total_failed

    for tier_name, tier_stats in registration_stats["tiers"].items():
        logger.info(f"{tier_name}: {tier_stats['successful']}/{tier_stats['total']} routers")

    logger.info(
        f"\nLegacy Routes: {registration_stats['successful']}/{registration_stats['successful'] + registration_stats['failed']} routers"
    )
    logger.info(
        f"\n{'✅' if total_failed == 0 else '⚠️'} Total: {total_successful}/{total_attempted} routers registered"
    )

    if total_failed > 0:
        logger.warning(f"⚠️  {total_failed} router(s) failed to register - check logs above")
    else:
        logger.info("✨ All routers registered successfully!")

    logger.info("=" * 60 + "\n")


def _register_tier_routers(app: FastAPI, routers: list, tier_name: str) -> dict:
    """
    Register a tier of routers with error handling

    Args:
        app: FastAPI application instance
        routers: List of tuples (name, prefix, module_path, tags)
        tier_name: Name of the tier for logging

    Returns:
        Statistics dictionary with success/failure counts
    """
    import traceback
    
    stats = {"total": len(routers), "successful": 0, "failed": 0}

    for router_name, prefix, module_path, tags in routers:
        try:
            # Dynamic import
            module = __import__(module_path, fromlist=["router"])
            router = getattr(module, "router")

            # Register with FastAPI
            app.include_router(router, prefix=prefix, tags=tags)

            logger.info(f"✓ {router_name:<30} → {prefix}")
            stats["successful"] += 1

        except ImportError as e:
            logger.warning(f"⚠ {router_name:<30} → Import failed: {str(e)}")
            logger.debug(f"Full traceback for {router_name}:\n{traceback.format_exc()}")
            stats["failed"] += 1
        except AttributeError as e:
            logger.warning(f"⚠ {router_name:<30} → No 'router' object found: {str(e)}")
            logger.debug(f"Full traceback for {router_name}:\n{traceback.format_exc()}")
            stats["failed"] += 1
        except Exception as e:
            logger.error(f"✗ {router_name:<30} → Error: {str(e)}")
            logger.error(f"Full traceback for {router_name}:\n{traceback.format_exc()}")
            stats["failed"] += 1

    return stats
