"""
Content Generation Tasks for Celery
====================================
Background tasks for generating educational content using AI agents.

Tasks:
- generate_lesson_content: Generate complete lesson plans and educational content
- generate_quiz_questions: Generate quiz questions and assessments

Features:
- Tenant-aware execution with organization context
- Integration with ContentAgent and QuizAgent
- Pusher notifications for real-time progress updates
- Database persistence for generated content
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
import asyncio

from apps.backend.workers.celery_app import app, TenantAwareTask
from core.agents.content_agent import ContentAgent
from core.agents.quiz_agent import QuizAgent
from core.agents.base_agent import AgentConfig, AgentState

logger = logging.getLogger(__name__)


@app.task(base=TenantAwareTask, bind=True, name="content.generate_lesson")
async def generate_lesson_content(
    self,
    lesson_id: str,
    organization_id: str,
    subject: str,
    topic: str,
    grade_level: str,
    learning_objectives: Optional[List[str]] = None,
    duration: int = 45,
    **kwargs
) -> Dict[str, Any]:
    """
    Generate educational lesson content using ContentAgent.

    Args:
        lesson_id: Unique identifier for the lesson
        organization_id: Organization/tenant ID for context isolation
        subject: Subject area (e.g., "Mathematics", "Science")
        topic: Specific topic for the lesson
        grade_level: Target grade level (e.g., "6-8", "K-2")
        learning_objectives: List of learning objectives
        duration: Lesson duration in minutes (default: 45)

    Returns:
        Dict containing generated content, metadata, and status

    Example:
        result = generate_lesson_content.delay(
            lesson_id="lesson_123",
            organization_id="org_456",
            subject="Mathematics",
            topic="Fractions",
            grade_level="3-5",
            learning_objectives=[
                "Students will understand numerator and denominator",
                "Students will add and subtract fractions with common denominators"
            ],
            duration=45
        )
    """
    # Set tenant context
    self.set_tenant_context(organization_id, {
        "lesson_id": lesson_id,
        "subject": subject,
        "topic": topic
    })

    try:
        logger.info(f"Starting lesson content generation for lesson {lesson_id} in org {organization_id}")

        # Initialize ContentAgent
        agent_config = AgentConfig(
            name="ContentAgent",
            model="gpt-4",
            temperature=0.7,
            system_prompt="You are an expert educational content creator for Roblox learning environments.",
            verbose=True
        )
        content_agent = ContentAgent(config=agent_config)

        # Prepare agent state
        agent_state: AgentState = {
            "task": f"Generate educational content for {topic} in {subject}",
            "context": {
                "subject": subject,
                "topic": topic,
                "grade_level": grade_level,
                "learning_objectives": learning_objectives or [],
                "duration": duration,
                "lesson_id": lesson_id,
                "organization_id": organization_id
            },
            "metadata": {
                "task_id": self.request.id,
                "tenant_id": organization_id,
                "initiated_at": datetime.utcnow().isoformat()
            }
        }

        # Trigger Pusher notification - content generation started
        try:
            from apps.backend.services.roblox.pusher import pusher_service
            await pusher_service.trigger_event(
                channel=f"org-{organization_id}",
                event="content-generation-started",
                data={
                    "lesson_id": lesson_id,
                    "task_id": self.request.id,
                    "topic": topic,
                    "progress": 0,
                    "status": "processing"
                }
            )
        except Exception as e:
            logger.warning(f"Failed to send Pusher start notification: {e}")

        # Generate content
        logger.info(f"Invoking ContentAgent for lesson {lesson_id}")
        result = await content_agent._process_task(agent_state)

        # Trigger Pusher notification - content generation progress
        try:
            await pusher_service.trigger_event(
                channel=f"org-{organization_id}",
                event="content-generation-progress",
                data={
                    "lesson_id": lesson_id,
                    "task_id": self.request.id,
                    "progress": 75,
                    "status": "finalizing",
                    "message": "Content generated, finalizing details"
                }
            )
        except Exception as e:
            logger.warning(f"Failed to send Pusher progress notification: {e}")

        # Package response
        response = {
            "success": True,
            "lesson_id": lesson_id,
            "organization_id": organization_id,
            "content": result.get("content", {}),
            "interactive_elements": result.get("interactive_elements", []),
            "assessments": result.get("assessments", {}),
            "metadata": {
                **result.get("metadata", {}),
                "task_id": self.request.id,
                "generated_at": datetime.utcnow().isoformat(),
                "tenant_context": self.tenant_context,
                "quality_metrics": result.get("quality_metrics", {})
            }
        }

        # Trigger Pusher notification - content generation completed
        try:
            await pusher_service.trigger_event(
                channel=f"org-{organization_id}",
                event="content-generation-completed",
                data={
                    "lesson_id": lesson_id,
                    "task_id": self.request.id,
                    "progress": 100,
                    "status": "completed",
                    "content_preview": {
                        "topic": topic,
                        "vocabulary_count": len(result.get("content", {}).get("vocabulary", [])),
                        "interactive_elements": len(result.get("interactive_elements", [])),
                        "has_assessments": bool(result.get("assessments"))
                    }
                }
            )
        except Exception as e:
            logger.warning(f"Failed to send Pusher completion notification: {e}")

        logger.info(f"Lesson content generation completed successfully for lesson {lesson_id}")
        return response

    except Exception as e:
        logger.error(f"Lesson content generation failed for lesson {lesson_id}: {e}", exc_info=True)

        # Trigger Pusher notification - content generation failed
        try:
            from apps.backend.services.roblox.pusher import pusher_service
            await pusher_service.trigger_event(
                channel=f"org-{organization_id}",
                event="content-generation-failed",
                data={
                    "lesson_id": lesson_id,
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


@app.task(base=TenantAwareTask, bind=True, name="content.generate_quiz")
async def generate_quiz_questions(
    self,
    assessment_id: str,
    organization_id: str,
    subject: str,
    topic: str,
    grade_level: str,
    num_questions: int = 10,
    difficulty: str = "medium",
    question_types: Optional[List[str]] = None,
    learning_objectives: Optional[List[str]] = None,
    lesson_id: Optional[str] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Generate quiz questions using QuizAgent.

    Args:
        assessment_id: Unique identifier for the assessment
        organization_id: Organization/tenant ID for context isolation
        subject: Subject area
        topic: Specific topic for questions
        grade_level: Target grade level
        num_questions: Number of questions to generate (default: 10)
        difficulty: Difficulty level ("easy", "medium", "hard", "expert")
        question_types: List of question types (e.g., ["multiple_choice", "true_false"])
        learning_objectives: List of learning objectives to assess
        lesson_id: Optional lesson ID if quiz is associated with a lesson

    Returns:
        Dict containing quiz data, Lua implementation, and metadata

    Example:
        result = generate_quiz_questions.delay(
            assessment_id="quiz_789",
            organization_id="org_456",
            subject="Science",
            topic="Photosynthesis",
            grade_level="6-8",
            num_questions=10,
            difficulty="medium",
            question_types=["multiple_choice", "true_false"]
        )
    """
    # Set tenant context
    self.set_tenant_context(organization_id, {
        "assessment_id": assessment_id,
        "subject": subject,
        "topic": topic,
        "lesson_id": lesson_id
    })

    try:
        logger.info(f"Starting quiz generation for assessment {assessment_id} in org {organization_id}")

        # Initialize QuizAgent
        agent_config = AgentConfig(
            name="QuizAgent",
            model="gpt-3.5-turbo",
            temperature=0.5,  # Lower temperature for more consistent questions
            system_prompt="You are an expert assessment designer creating educational quizzes for Roblox learning environments.",
            verbose=True
        )
        quiz_agent = QuizAgent(config=agent_config)

        # Prepare agent state
        agent_state: AgentState = {
            "task": f"Generate {num_questions} quiz questions about {topic} in {subject}",
            "context": {
                "subject": subject,
                "topic": topic,
                "grade_level": grade_level,
                "num_questions": num_questions,
                "difficulty": difficulty,
                "question_types": question_types or ["multiple_choice"],
                "learning_objectives": learning_objectives or [],
                "lesson_id": lesson_id,
                "assessment_id": assessment_id,
                "organization_id": organization_id
            },
            "metadata": {
                "task_id": self.request.id,
                "tenant_id": organization_id,
                "initiated_at": datetime.utcnow().isoformat()
            }
        }

        # Trigger Pusher notification - quiz generation started
        try:
            from apps.backend.services.roblox.pusher import pusher_service
            await pusher_service.trigger_event(
                channel=f"org-{organization_id}",
                event="quiz-generation-started",
                data={
                    "assessment_id": assessment_id,
                    "task_id": self.request.id,
                    "topic": topic,
                    "num_questions": num_questions,
                    "progress": 0,
                    "status": "processing"
                }
            )
        except Exception as e:
            logger.warning(f"Failed to send Pusher start notification: {e}")

        # Generate quiz
        logger.info(f"Invoking QuizAgent for assessment {assessment_id}")
        result = await quiz_agent._process_task(agent_state)

        # Package response
        response = {
            "success": True,
            "assessment_id": assessment_id,
            "organization_id": organization_id,
            "quiz": result.get("quiz", {}),
            "lua_script": result.get("lua_script", ""),
            "feedback_system": result.get("feedback_system", {}),
            "database_id": result.get("database_id"),
            "quality_score": result.get("quality_score", 0.0),
            "metadata": {
                **result.get("metadata", {}),
                "task_id": self.request.id,
                "generated_at": datetime.utcnow().isoformat(),
                "tenant_context": self.tenant_context,
                "metrics": result.get("metrics", {})
            }
        }

        # Trigger Pusher notification - quiz generation completed
        try:
            await pusher_service.trigger_event(
                channel=f"org-{organization_id}",
                event="quiz-generation-completed",
                data={
                    "assessment_id": assessment_id,
                    "task_id": self.request.id,
                    "progress": 100,
                    "status": "completed",
                    "quiz_preview": {
                        "title": result.get("quiz", {}).get("title", ""),
                        "num_questions": len(result.get("quiz", {}).get("questions", [])),
                        "time_limit": result.get("quiz", {}).get("time_limit"),
                        "passing_score": result.get("quiz", {}).get("passing_score")
                    },
                    "quality_score": result.get("quality_score", 0.0)
                }
            )
        except Exception as e:
            logger.warning(f"Failed to send Pusher completion notification: {e}")

        logger.info(f"Quiz generation completed successfully for assessment {assessment_id}")
        return response

    except Exception as e:
        logger.error(f"Quiz generation failed for assessment {assessment_id}: {e}", exc_info=True)

        # Trigger Pusher notification - quiz generation failed
        try:
            from apps.backend.services.roblox.pusher import pusher_service
            await pusher_service.trigger_event(
                channel=f"org-{organization_id}",
                event="quiz-generation-failed",
                data={
                    "assessment_id": assessment_id,
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


# Synchronous wrappers for Celery (Celery doesn't natively support async)
@app.task(base=TenantAwareTask, bind=True, name="content.generate_lesson_sync")
def generate_lesson_content_sync(self, *args, **kwargs):
    """Synchronous wrapper for generate_lesson_content."""
    return run_async_task(generate_lesson_content(self, *args, **kwargs))


@app.task(base=TenantAwareTask, bind=True, name="content.generate_quiz_sync")
def generate_quiz_questions_sync(self, *args, **kwargs):
    """Synchronous wrapper for generate_quiz_questions."""
    return run_async_task(generate_quiz_questions(self, *args, **kwargs))
