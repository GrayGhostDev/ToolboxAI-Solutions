"""
Content Generation Tasks
=======================
Background tasks for AI-powered content generation and processing
"""

import json
import time
from datetime import datetime
from typing import Dict, List, Any, Optional
from celery import shared_task, chain, group
from celery.utils.log import get_task_logger
import httpx
import openai
from pydantic import BaseModel, Field

from apps.backend.core.config import settings
from apps.backend.core.database import get_async_session
from apps.backend.services.pusher_service import pusher_client
from database.models import EducationalContent, Quiz, User
from core.agents.content_agent import ContentAgent
from core.agents.orchestrator import Orchestrator

logger = get_task_logger(__name__)


class ContentRequest(BaseModel):
    """Content generation request model"""

    topic: str
    grade_level: str
    content_type: str = "lesson"
    language: str = "en"
    user_id: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


@shared_task(
    bind=True,
    name="tasks.generate_educational_content",
    max_retries=3,
    default_retry_delay=60,
    queue="ai_generation",
    priority=5,
)
def generate_educational_content(
    self, request_data: Dict[str, Any], callback_channel: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generate educational content using AI agents

    Args:
        request_data: Content generation request parameters
        callback_channel: Pusher channel for progress updates

    Returns:
        Generated content with metadata
    """
    try:
        request = ContentRequest(**request_data)
        task_id = self.request.id
        start_time = time.time()

        # Send initial progress update
        if callback_channel and pusher_client:
            pusher_client.trigger(
                callback_channel,
                "content-progress",
                {
                    "task_id": task_id,
                    "status": "started",
                    "progress": 0,
                    "message": f"Starting content generation for {request.topic}",
                },
            )

        # Initialize content agent
        agent = ContentAgent(name="content_generator", model_name=settings.OPENAI_MODEL or "gpt-4")

        # Prepare context for generation
        context = {
            "topic": request.topic,
            "grade_level": request.grade_level,
            "content_type": request.content_type,
            "language": request.language,
            "learning_objectives": request.metadata.get("objectives", []),
            "curriculum_standards": request.metadata.get("standards", []),
        }

        # Update progress: Context prepared
        if callback_channel and pusher_client:
            pusher_client.trigger(
                callback_channel,
                "content-progress",
                {
                    "task_id": task_id,
                    "status": "processing",
                    "progress": 25,
                    "message": "Context prepared, generating content...",
                },
            )

        # Generate main content
        content_result = agent.execute({"task": "generate_educational_content", "context": context})

        # Update progress: Content generated
        if callback_channel and pusher_client:
            pusher_client.trigger(
                callback_channel,
                "content-progress",
                {
                    "task_id": task_id,
                    "status": "processing",
                    "progress": 60,
                    "message": "Content generated, creating assessments...",
                },
            )

        # Generate related quiz questions
        quiz_data = None
        if request.metadata.get("include_quiz", True):
            quiz_result = agent.execute(
                {
                    "task": "generate_quiz",
                    "context": {
                        "content": content_result.get("content"),
                        "topic": request.topic,
                        "difficulty": request.grade_level,
                        "num_questions": request.metadata.get("quiz_questions", 5),
                    },
                }
            )
            quiz_data = quiz_result.get("quiz")

        # Update progress: Assessments created
        if callback_channel and pusher_client:
            pusher_client.trigger(
                callback_channel,
                "content-progress",
                {
                    "task_id": task_id,
                    "status": "processing",
                    "progress": 80,
                    "message": "Saving content to database...",
                },
            )

        # Save to database
        content_id = None
        try:
            # Note: In production, use async session properly
            # This is a simplified example
            from apps.backend.core.database import SessionLocal

            with SessionLocal() as session:
                content = EducationalContent(
                    title=content_result.get("title", request.topic),
                    topic=request.topic,
                    grade_level=request.grade_level,
                    content_type=request.content_type,
                    content_body=json.dumps(content_result.get("content")),
                    metadata=json.dumps(
                        {
                            "language": request.language,
                            "generated_at": datetime.utcnow().isoformat(),
                            "agent_id": agent.name,
                            "model": agent.model_name,
                            **request.metadata,
                        }
                    ),
                    created_by=request.user_id,
                )
                session.add(content)
                session.commit()
                content_id = content.id
                logger.info(f"Saved content with ID: {content_id}")

        except Exception as e:
            logger.error(f"Database save error: {e}")

        # Final progress update
        generation_time = round(time.time() - start_time, 2)

        if callback_channel and pusher_client:
            pusher_client.trigger(
                callback_channel,
                "content-complete",
                {
                    "task_id": task_id,
                    "status": "completed",
                    "progress": 100,
                    "content_id": content_id,
                    "generation_time": generation_time,
                    "message": "Content generation completed successfully!",
                },
            )

        result = {
            "status": "success",
            "task_id": task_id,
            "content_id": content_id,
            "content": content_result,
            "quiz": quiz_data,
            "generation_time": generation_time,
            "timestamp": datetime.utcnow().isoformat(),
        }

        logger.info(f"Content generation completed in {generation_time}s")
        return result

    except Exception as e:
        logger.error(f"Content generation failed: {e}")

        # Send error notification
        if callback_channel and pusher_client:
            pusher_client.trigger(
                callback_channel,
                "content-error",
                {
                    "task_id": self.request.id,
                    "status": "failed",
                    "error": str(e),
                    "message": "Content generation failed",
                },
            )

        raise self.retry(exc=e)


@shared_task(
    bind=True,
    name="tasks.process_quiz_generation",
    max_retries=3,
    default_retry_delay=30,
    queue="ai_generation",
    priority=4,
)
def process_quiz_generation(
    self, content_id: str, num_questions: int = 10, difficulty: str = "medium"
) -> Dict[str, Any]:
    """
    Generate quiz questions based on existing content

    Args:
        content_id: ID of the educational content
        num_questions: Number of questions to generate
        difficulty: Difficulty level (easy, medium, hard)

    Returns:
        Generated quiz data
    """
    try:
        from apps.backend.core.database import SessionLocal

        # Fetch content from database
        with SessionLocal() as session:
            content = session.query(EducationalContent).filter_by(id=content_id).first()

            if not content:
                raise ValueError(f"Content {content_id} not found")

            content_body = json.loads(content.content_body)

        # Use OpenAI to generate quiz questions
        openai.api_key = settings.OPENAI_API_KEY

        prompt = f"""
        Create {num_questions} quiz questions based on the following educational content.
        Difficulty level: {difficulty}
        Content: {content_body}

        Format the response as a JSON array with questions in this structure:
        {{
            "question": "Question text",
            "type": "multiple_choice",
            "options": ["A", "B", "C", "D"],
            "correct_answer": "A",
            "explanation": "Why this is correct"
        }}
        """

        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an educational assessment expert."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.7,
        )

        quiz_data = json.loads(response.choices[0].message.content)

        # Save quiz to database
        with SessionLocal() as session:
            quiz = Quiz(
                content_id=content_id,
                questions=json.dumps(quiz_data),
                difficulty=difficulty,
                created_at=datetime.utcnow(),
            )
            session.add(quiz)
            session.commit()
            quiz_id = quiz.id

        logger.info(f"Generated quiz {quiz_id} with {num_questions} questions")

        return {
            "status": "success",
            "quiz_id": quiz_id,
            "num_questions": len(quiz_data),
            "difficulty": difficulty,
            "questions": quiz_data,
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Quiz generation failed: {e}")
        raise self.retry(exc=e)


@shared_task(
    bind=True,
    name="tasks.analyze_content_quality",
    max_retries=2,
    default_retry_delay=60,
    queue="analysis",
    priority=3,
)
def analyze_content_quality(self, content_id: str) -> Dict[str, Any]:
    """
    Analyze the quality of generated educational content

    Args:
        content_id: ID of content to analyze

    Returns:
        Quality analysis report
    """
    try:
        from apps.backend.core.database import SessionLocal

        with SessionLocal() as session:
            content = session.query(EducationalContent).filter_by(id=content_id).first()

            if not content:
                raise ValueError(f"Content {content_id} not found")

            content_body = json.loads(content.content_body)

        # Perform quality checks
        analysis = {
            "readability_score": 0,
            "completeness_score": 0,
            "accuracy_confidence": 0,
            "engagement_score": 0,
            "issues": [],
            "suggestions": [],
        }

        # Check content length
        content_text = str(content_body)
        word_count = len(content_text.split())

        if word_count < 100:
            analysis["issues"].append("Content is too short")
            analysis["completeness_score"] = 30
        elif word_count > 2000:
            analysis["issues"].append("Content may be too long for grade level")
            analysis["completeness_score"] = 70
        else:
            analysis["completeness_score"] = 90

        # Simulate readability analysis
        # In production, use proper readability metrics
        analysis["readability_score"] = min(100, 50 + (word_count / 20))

        # Check for required elements based on content type
        required_elements = {
            "lesson": ["objectives", "introduction", "main_content", "summary"],
            "tutorial": ["steps", "examples", "exercises"],
            "assessment": ["questions", "answer_key", "rubric"],
        }

        content_type = content.content_type
        if content_type in required_elements:
            for element in required_elements[content_type]:
                if element not in str(content_body).lower():
                    analysis["issues"].append(f"Missing {element}")
                    analysis["suggestions"].append(f"Add {element} section")

        # Calculate overall quality score
        analysis["overall_score"] = (
            sum([analysis["readability_score"], analysis["completeness_score"]]) / 2
        )

        # Update content metadata with analysis
        with SessionLocal() as session:
            content = session.query(EducationalContent).filter_by(id=content_id).first()

            if content:
                metadata = json.loads(content.metadata or "{}")
                metadata["quality_analysis"] = analysis
                metadata["analyzed_at"] = datetime.utcnow().isoformat()
                content.metadata = json.dumps(metadata)
                session.commit()

        logger.info(
            f"Content analysis completed for {content_id}: score={analysis['overall_score']}"
        )

        return {
            "status": "success",
            "content_id": content_id,
            "analysis": analysis,
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Content analysis failed: {e}")
        raise self.retry(exc=e)
