"""
AI Processing Tasks
==================
Background tasks for AI content generation and processing
"""

import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime
from celery import shared_task
from celery.utils.log import get_task_logger
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from apps.backend.core.database import get_db
from apps.backend.core.config import settings
from apps.backend.services.cached_ai_service import cached_ai

logger = get_task_logger(__name__)


@shared_task(
    bind=True,
    name="tasks.process_generation_queue",
    max_retries=3,
    default_retry_delay=120,
    queue="ai_generation",
    priority=7,
)
def process_generation_queue(self, batch_size: int = 10) -> Dict[str, Any]:
    """
    Process pending AI content generation requests

    Args:
        batch_size: Number of requests to process in this batch

    Returns:
        Dictionary with processing statistics
    """
    try:
        logger.info(f"Processing AI generation queue (batch size: {batch_size})")

        # Import database models
        from database.models import EnhancedContentGeneration

        # Get database session
        db = next(get_db())

        try:
            # Query pending generation requests
            pending_requests = db.query(EnhancedContentGeneration).filter(
                EnhancedContentGeneration.status == "pending"
            ).limit(batch_size).all()

            requests_processed = 0
            requests_completed = 0
            requests_failed = 0

            for request in pending_requests:
                try:
                    # Update status to processing
                    request.status = "processing"
                    db.commit()

                    # Build prompt from request data
                    original_request = request.original_request or {}
                    prompt = original_request.get("prompt", f"Generate {request.content_type} content")

                    # Generate content via AI service
                    result = asyncio.run(cached_ai.generate_completion(
                        prompt=prompt,
                        model=getattr(settings, 'OPENAI_MODEL', 'gpt-4'),
                        temperature=0.7,
                        max_tokens=2000,
                        use_cache=True
                    ))

                    # Save generated content to database
                    request.generated_content = {
                        "content": result.get("completion", ""),
                        "tokens_used": result.get("tokens_used", 0),
                        "cost": result.get("cost", 0.0),
                        "model": result.get("model", "gpt-4"),
                        "cached": result.get("cached", False),
                        "generated_at": datetime.utcnow().isoformat()
                    }

                    # Update request status
                    request.status = "completed"
                    db.commit()

                    requests_completed += 1
                    logger.info(f"Completed generation request {request.id}")

                except Exception as e:
                    logger.error(f"Failed to process generation request {request.id}: {e}")
                    request.status = "failed"
                    # Store error in original_request metadata
                    if not request.original_request:
                        request.original_request = {}
                    request.original_request["error"] = str(e)
                    db.commit()
                    requests_failed += 1

                requests_processed += 1

            return {
                "status": "success",
                "requests_processed": requests_processed,
                "requests_completed": requests_completed,
                "requests_failed": requests_failed,
                "timestamp": datetime.utcnow().isoformat()
            }

        finally:
            db.close()

    except Exception as e:
        logger.error(f"Failed to process generation queue: {e}")
        raise self.retry(exc=e, countdown=120)


@shared_task(
    bind=True,
    name="tasks.generate_content",
    max_retries=3,
    default_retry_delay=60,
    queue="ai_generation",
    priority=8,
)
def generate_content(
    self,
    content_type: str,
    prompt: str,
    user_id: Optional[int] = None,
    metadata: Optional[Dict] = None
) -> Dict[str, Any]:
    """
    Generate AI content from prompt

    Args:
        content_type: Type of content (lesson, quiz, explanation, etc.)
        prompt: Generation prompt
        user_id: Optional user ID requesting generation
        metadata: Optional additional metadata

    Returns:
        Dictionary with generated content and metadata
    """
    try:
        logger.info(f"Generating {content_type} content for user {user_id}")

        # Call AI service using asyncio bridge
        result = asyncio.run(cached_ai.generate_completion(
            prompt=prompt,
            model=getattr(settings, 'OPENAI_MODEL', 'gpt-4'),
            temperature=0.7,
            max_tokens=2000,
            use_cache=True
        ))

        # Extract token usage and cost from result
        tokens_used = result.get("tokens_used", 0)
        estimated_cost = result.get("cost", 0.0)
        generated_content = result.get("completion", "")

        return {
            "status": "success",
            "content_type": content_type,
            "generated_content": generated_content,
            "tokens_used": tokens_used,
            "estimated_cost": estimated_cost,
            "cached": result.get("cached", False),
            "model": result.get("model", "gpt-4"),
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"Failed to generate content: {e}")
        raise self.retry(exc=e, countdown=60)


@shared_task(
    bind=True,
    name="tasks.batch_content_generation",
    max_retries=2,
    default_retry_delay=180,
    queue="ai_generation",
    priority=5,
)
def batch_content_generation(
    self,
    requests: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Process multiple content generation requests as a batch

    Args:
        requests: List of generation request dictionaries
               Each request should have: content_type, prompt, metadata (optional)

    Returns:
        Dictionary with batch processing statistics
    """
    try:
        logger.info(f"Processing batch content generation: {len(requests)} requests")

        async def generate_single(request_data: Dict) -> Dict:
            """Generate content for single request"""
            try:
                result = await cached_ai.generate_completion(
                    prompt=request_data.get("prompt", ""),
                    model=getattr(settings, 'OPENAI_MODEL', 'gpt-4'),
                    temperature=request_data.get("temperature", 0.7),
                    max_tokens=request_data.get("max_tokens", 2000),
                    use_cache=True
                )
                return {
                    "status": "success",
                    "content_type": request_data.get("content_type"),
                    "result": result,
                    "generated_content": result.get("completion", ""),
                    "tokens_used": result.get("tokens_used", 0),
                    "cost": result.get("cost", 0.0)
                }
            except Exception as e:
                logger.error(f"Failed to generate content for request: {e}")
                return {
                    "status": "failed",
                    "content_type": request_data.get("content_type"),
                    "error": str(e)
                }

        async def process_batch():
            """Process all requests concurrently"""
            # Create tasks for all requests
            tasks = [generate_single(req) for req in requests]

            # Process with concurrency limit (max 5 concurrent requests)
            results = []
            batch_size = 5

            for i in range(0, len(tasks), batch_size):
                batch = tasks[i:i + batch_size]
                batch_results = await asyncio.gather(*batch, return_exceptions=True)
                results.extend(batch_results)

            return results

        # Run async batch processing
        results = asyncio.run(process_batch())

        # Count successes and failures
        completed = sum(1 for r in results if isinstance(r, dict) and r.get("status") == "success")
        failed = sum(1 for r in results if isinstance(r, dict) and r.get("status") == "failed")

        # Calculate total tokens and cost
        total_tokens = sum(r.get("tokens_used", 0) for r in results if isinstance(r, dict))
        total_cost = sum(r.get("cost", 0.0) for r in results if isinstance(r, dict))

        return {
            "status": "success",
            "total_requests": len(requests),
            "completed": completed,
            "failed": failed,
            "total_tokens_used": total_tokens,
            "total_cost": total_cost,
            "results": results,
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"Failed to process batch generation: {e}")
        raise self.retry(exc=e, countdown=180)
