"""
Educational Orchestration Module

Integrates the educational swarm orchestration controller for managing
intelligent, context-aware educational agent interactions.

This module provides:
- Natural language understanding and conversation management
- Educational agent coordination
- Adaptive learning workflows
- Assessment and curriculum alignment
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

# Import base orchestration components
from ...agents.master_orchestrator import (
    AgentSystemType,
    MasterOrchestrator,
    TaskPriority,
)

# Import the swarm orchestration controller
from ...swarm.orchestration_controller import (
    OrchestrationController,
    OrchestrationMode,
    OrchestrationPlan,
    SessionContext,
)

logger = logging.getLogger(__name__)


class EducationalOrchestrationModule:
    """
    Educational orchestration module that wraps the swarm orchestration controller.

    This module provides educational-specific orchestration capabilities including
    natural language processing, conversation management, and adaptive learning.
    """

    def __init__(self, master_orchestrator: MasterOrchestrator):
        """Initialize the educational orchestration module."""
        self.master = master_orchestrator
        self.swarm_controller: Optional[OrchestrationController] = None

        # Metrics
        self.metrics = {
            "interactions_processed": 0,
            "successful_interactions": 0,
            "failed_interactions": 0,
            "active_sessions": 0,
        }

        logger.info("Educational Orchestration Module initialized")

    async def initialize(self):
        """Initialize the module and its swarm controller."""
        try:
            # Initialize swarm orchestration controller
            self.swarm_controller = OrchestrationController()

            logger.info("Educational Orchestration Module fully initialized")

        except Exception as e:
            logger.error(f"Failed to initialize Educational module: {e}")
            raise

    async def submit_task(self, **kwargs) -> str:
        """
        Submit an educational orchestration task.

        Args:
            **kwargs: Task parameters including user_input, session_id, user_context

        Returns:
            Task ID for tracking
        """
        # Extract parameters
        user_input = kwargs.get("user_input", "")
        session_id = kwargs.get("session_id")
        user_context = kwargs.get("user_context", {})

        # Prepare task data for master orchestrator
        task_data = {
            "type": "educational_interaction",
            "user_input": user_input,
            "session_id": session_id,
            "user_context": user_context,
            "module": "educational",
        }

        # Submit to master orchestrator
        task_id = await self.master.submit_task(
            agent_type=AgentSystemType.EDUCATIONAL,
            task_data=task_data,
            priority=TaskPriority.MEDIUM,
        )

        self.metrics["interactions_processed"] += 1
        return task_id

    async def process_interaction(
        self,
        user_input: str,
        session_id: Optional[str] = None,
        user_context: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """
        Process user interaction through the swarm controller.

        This is a direct interface to the swarm orchestration controller.
        """
        if not self.swarm_controller:
            raise RuntimeError("Swarm controller not initialized")

        try:
            result = await self.swarm_controller.process_interaction(
                user_input=user_input, session_id=session_id, user_context=user_context
            )

            if result.get("success", False):
                self.metrics["successful_interactions"] += 1
            else:
                self.metrics["failed_interactions"] += 1

            return result

        except Exception as e:
            logger.error(f"Error processing interaction: {e}")
            self.metrics["failed_interactions"] += 1
            raise

    async def create_lesson(self, **kwargs) -> dict[str, Any]:
        """
        Create an educational lesson through the swarm controller.

        Args:
            **kwargs: Lesson parameters (subject, grade_level, objectives, etc.)

        Returns:
            Lesson creation result
        """
        # Format as user input for the swarm controller
        subject = kwargs.get("subject", "General")
        grade_level = kwargs.get("grade_level", "K-12")
        objectives = kwargs.get("learning_objectives", [])

        user_input = f"Create a lesson for {subject}, grade {grade_level}"
        if objectives:
            user_input += f" with objectives: {', '.join(objectives)}"

        return await self.process_interaction(user_input=user_input, user_context=kwargs)

    async def create_assessment(self, **kwargs) -> dict[str, Any]:
        """
        Create an educational assessment through the swarm controller.

        Args:
            **kwargs: Assessment parameters

        Returns:
            Assessment creation result
        """
        subject = kwargs.get("subject", "General")
        assessment_type = kwargs.get("type", "quiz")

        user_input = f"Create a {assessment_type} for {subject}"

        return await self.process_interaction(user_input=user_input, user_context=kwargs)

    async def analyze_performance(self, **kwargs) -> dict[str, Any]:
        """
        Analyze student performance through the swarm controller.

        Args:
            **kwargs: Performance data and parameters

        Returns:
            Performance analysis result
        """
        user_input = "Analyze student performance and provide recommendations"

        return await self.process_interaction(user_input=user_input, user_context=kwargs)

    async def get_session_context(self, session_id: str) -> Optional[dict[str, Any]]:
        """
        Get session context from the swarm controller.

        Args:
            session_id: Session identifier

        Returns:
            Session context or None if not found
        """
        if not self.swarm_controller:
            return None

        session = self.swarm_controller.sessions.get(session_id)
        if not session:
            return None

        return {
            "session_id": session.session_id,
            "user_id": session.user_id,
            "started_at": session.started_at.isoformat(),
            "current_state": session.current_state.value,
            "grade_level": session.grade_level,
            "subject": session.subject,
            "topics": session.topics,
            "learning_objectives": session.learning_objectives,
            "completed_tasks": session.completed_tasks,
        }

    async def get_status(self) -> dict[str, Any]:
        """Get the status of the educational orchestration module."""
        swarm_status = None
        if self.swarm_controller:
            try:
                # Count active sessions
                active_sessions = len(self.swarm_controller.sessions)
                self.metrics["active_sessions"] = active_sessions

                swarm_status = {
                    "active_sessions": active_sessions,
                    "total_agents": len(self.swarm_controller.agents),
                    "metrics": getattr(self.swarm_controller, "metrics", {}),
                }
            except Exception as e:
                swarm_status = {"error": str(e)}

        return {
            "module": "educational",
            "initialized": self.swarm_controller is not None,
            "swarm_controller": swarm_status,
            "metrics": self.metrics,
        }

    async def cleanup(self):
        """Cleanup the module and its resources."""
        try:
            # Cleanup swarm controller if needed
            if self.swarm_controller:
                # Clear sessions to free memory
                self.swarm_controller.sessions.clear()

            logger.info("Educational Orchestration Module cleaned up")

        except Exception as e:
            logger.error(f"Error cleaning up Educational module: {e}")


# Export key classes for backward compatibility
__all__ = [
    "EducationalOrchestrationModule",
    "OrchestrationController",
    "OrchestrationMode",
    "SessionContext",
    "OrchestrationPlan",
]


# Convenience factory function
def create_educational_orchestrator(
    master_orchestrator: MasterOrchestrator,
) -> EducationalOrchestrationModule:
    """Create and initialize an educational orchestration module."""
    return EducationalOrchestrationModule(master_orchestrator)
