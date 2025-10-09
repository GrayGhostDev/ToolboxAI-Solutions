"""
Roblox Optimization Tasks for Celery
=====================================
Background tasks for optimizing Roblox Luau scripts using AI agents.

Tasks:
- optimize_roblox_script: Optimize Luau scripts for performance, memory, and best practices

Features:
- Tenant-aware execution with organization context
- Integration with RobloxScriptOptimizationAgent
- Pusher notifications for real-time progress updates
- Performance metrics and optimization reports
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
import asyncio

from apps.backend.workers.celery_app import app, TenantAwareTask
from core.agents.roblox.roblox_script_optimization_agent import (
    RobloxScriptOptimizationAgent,
    OptimizationLevel,
)
from core.agents.base_agent import AgentConfig, AgentState

logger = logging.getLogger(__name__)


@app.task(base=TenantAwareTask, bind=True, name="roblox.optimize_script")
async def optimize_roblox_script(
    self,
    script_id: str,
    organization_id: str,
    script_code: str,
    script_name: str,
    optimization_level: str = "balanced",
    preserve_comments: bool = True,
    generate_report: bool = True,
    **kwargs
) -> Dict[str, Any]:
    """
    Optimize Roblox Luau script using RobloxScriptOptimizationAgent.

    Args:
        script_id: Unique identifier for the script
        organization_id: Organization/tenant ID for context isolation
        script_code: The Luau script code to optimize
        script_name: Name/description of the script
        optimization_level: Optimization level ("conservative", "balanced", "aggressive")
        preserve_comments: Whether to preserve comments in optimized code
        generate_report: Whether to generate detailed optimization report

    Returns:
        Dict containing optimized code, issues found, metrics, and optional report

    Example:
        result = optimize_roblox_script.delay(
            script_id="script_789",
            organization_id="org_456",
            script_code="local player = game.Players.LocalPlayer...",
            script_name="Player Inventory System",
            optimization_level="aggressive",
            preserve_comments=True,
            generate_report=True
        )
    """
    # Set tenant context
    self.set_tenant_context(organization_id, {
        "script_id": script_id,
        "script_name": script_name,
        "optimization_level": optimization_level
    })

    try:
        logger.info(f"Starting Roblox script optimization for script {script_id} in org {organization_id}")

        # Initialize RobloxScriptOptimizationAgent
        level_map = {
            "conservative": OptimizationLevel.CONSERVATIVE,
            "balanced": OptimizationLevel.BALANCED,
            "aggressive": OptimizationLevel.AGGRESSIVE
        }
        opt_level = level_map.get(optimization_level.lower(), OptimizationLevel.BALANCED)

        agent_config = AgentConfig(
            name="RobloxScriptOptimizer",
            model="gpt-4",
            temperature=0.1,  # Low temperature for consistent optimizations
            system_prompt="You are an expert Roblox Luau script optimizer specializing in performance and memory optimization.",
            verbose=True
        )
        optimizer_agent = RobloxScriptOptimizationAgent(
            config=agent_config,
            optimization_level=opt_level
        )

        # Prepare agent state
        agent_state: AgentState = {
            "task": f"Optimize Roblox Luau script: {script_name}",
            "context": {
                "script_code": script_code,
                "script_name": script_name,
                "optimization_level": optimization_level,
                "preserve_comments": preserve_comments,
                "script_id": script_id,
                "organization_id": organization_id
            },
            "metadata": {
                "task_id": self.request.id,
                "tenant_id": organization_id,
                "initiated_at": datetime.utcnow().isoformat()
            }
        }

        # Trigger Pusher notification - optimization started
        try:
            from apps.backend.services.roblox_pusher import pusher_service
            await pusher_service.trigger_event(
                channel=f"org-{organization_id}",
                event="script-optimization-started",
                data={
                    "script_id": script_id,
                    "task_id": self.request.id,
                    "script_name": script_name,
                    "optimization_level": optimization_level,
                    "progress": 0,
                    "status": "processing"
                }
            )
        except Exception as e:
            logger.warning(f"Failed to send Pusher start notification: {e}")

        # Trigger Pusher notification - analyzing script
        try:
            await pusher_service.trigger_event(
                channel=f"org-{organization_id}",
                event="script-optimization-progress",
                data={
                    "script_id": script_id,
                    "task_id": self.request.id,
                    "progress": 25,
                    "status": "analyzing",
                    "message": "Analyzing script for performance issues"
                }
            )
        except Exception as e:
            logger.warning(f"Failed to send Pusher progress notification: {e}")

        # Optimize script
        logger.info(f"Invoking RobloxScriptOptimizationAgent for script {script_id}")
        result = await optimizer_agent._process_task(agent_state)

        # Extract result data
        result_data = result.result if hasattr(result, 'result') else result

        # Trigger Pusher notification - optimization progress
        try:
            await pusher_service.trigger_event(
                channel=f"org-{organization_id}",
                event="script-optimization-progress",
                data={
                    "script_id": script_id,
                    "task_id": self.request.id,
                    "progress": 75,
                    "status": "finalizing",
                    "message": "Generating optimization report"
                }
            )
        except Exception as e:
            logger.warning(f"Failed to send Pusher progress notification: {e}")

        # Generate detailed report if requested
        optimization_report = None
        if generate_report:
            try:
                # Use agent's report generation method
                optimization_report = optimizer_agent.generate_optimization_report(
                    script_code,
                    optimizer_agent.optimize_script(script_code, opt_level, preserve_comments)
                )
            except Exception as e:
                logger.warning(f"Failed to generate optimization report: {e}")
                optimization_report = None

        # Package response
        response = {
            "success": True,
            "script_id": script_id,
            "organization_id": organization_id,
            "script_name": script_name,
            "original_code": result_data.get("original_code", script_code),
            "optimized_code": result_data.get("optimized_code", ""),
            "issues_found": result_data.get("issues_found", []),
            "metrics": result_data.get("metrics", {}),
            "optimization_level": optimization_level,
            "performance_gain": result_data.get("performance_gain", "Unknown"),
            "optimization_report": optimization_report,
            "metadata": {
                "task_id": self.request.id,
                "optimized_at": datetime.utcnow().isoformat(),
                "tenant_context": self.tenant_context,
                "issues_count": len(result_data.get("issues_found", [])),
                "critical_issues": len([
                    i for i in result_data.get("issues_found", [])
                    if i.get("severity") == "critical"
                ])
            }
        }

        # Trigger Pusher notification - optimization completed
        try:
            await pusher_service.trigger_event(
                channel=f"org-{organization_id}",
                event="script-optimization-completed",
                data={
                    "script_id": script_id,
                    "task_id": self.request.id,
                    "progress": 100,
                    "status": "completed",
                    "optimization_preview": {
                        "script_name": script_name,
                        "issues_found": len(result_data.get("issues_found", [])),
                        "critical_issues": response["metadata"]["critical_issues"],
                        "performance_gain": result_data.get("performance_gain", "Unknown"),
                        "optimization_level": optimization_level
                    }
                }
            )
        except Exception as e:
            logger.warning(f"Failed to send Pusher completion notification: {e}")

        logger.info(f"Roblox script optimization completed successfully for script {script_id}")
        return response

    except Exception as e:
        logger.error(f"Roblox script optimization failed for script {script_id}: {e}", exc_info=True)

        # Trigger Pusher notification - optimization failed
        try:
            from apps.backend.services.roblox_pusher import pusher_service
            await pusher_service.trigger_event(
                channel=f"org-{organization_id}",
                event="script-optimization-failed",
                data={
                    "script_id": script_id,
                    "task_id": self.request.id,
                    "progress": 0,
                    "status": "failed",
                    "error": str(e)
                }
            )
        except Exception as pusher_error:
            logger.warning(f"Failed to send Pusher error notification: {pusher_error}")

        # Re-raise exception for Celery retry mechanism
        raise


# Helper function to run async tasks in Celery
def run_async_task(coro):
    """Helper to run async coroutines in Celery tasks."""
    loop = asyncio.get_event_loop()
    if loop.is_running():
        # If loop is already running, create a new one
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as pool:
            return pool.submit(asyncio.run, coro).result()
    else:
        return loop.run_until_complete(coro)


# Synchronous wrapper for Celery (Celery doesn't natively support async)
@app.task(base=TenantAwareTask, bind=True, name="roblox.optimize_script_sync")
def optimize_roblox_script_sync(self, *args, **kwargs):
    """Synchronous wrapper for optimize_roblox_script."""
    return run_async_task(optimize_roblox_script(self, *args, **kwargs))
