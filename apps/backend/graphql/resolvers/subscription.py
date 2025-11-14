"""
GraphQL Subscription resolvers for real-time updates
"""

import asyncio
import uuid
from collections.abc import AsyncGenerator
from datetime import datetime
from typing import Any

from ariadne import SubscriptionType
from sqlalchemy import select

from database.models import Course

# Create Subscription type
subscription = SubscriptionType()

# In-memory event store (in production, use Redis pub/sub)
event_channels: dict[str, asyncio.Queue] = {}


async def publish_event(channel: str, event: dict[str, Any]):
    """Publish event to a channel"""
    if channel not in event_channels:
        event_channels[channel] = asyncio.Queue()

    await event_channels[channel].put(event)


@subscription.source("contentGeneration")
async def generate_content_updates(
    obj, info, generationId: str
) -> AsyncGenerator[dict[str, Any], None]:
    """Subscribe to content generation updates"""

    generation_id = uuid.UUID(generationId)
    channel_key = f"content_generation_{generation_id}"

    # Create queue for this subscription
    if channel_key not in event_channels:
        event_channels[channel_key] = asyncio.Queue()

    event_channels[channel_key]

    try:
        # Send initial status
        yield {
            "generationId": generation_id,
            "status": "PROCESSING",
            "progress": 0.0,
            "currentStep": "Initializing...",
        }

        # Simulate content generation progress
        steps = [
            ("Analyzing requirements", 20),
            ("Generating content structure", 40),
            ("Creating educational material", 60),
            ("Adding interactive elements", 80),
            ("Finalizing content", 100),
        ]

        for step, progress in steps:
            await asyncio.sleep(2)  # Simulate processing time

            yield {
                "generationId": generation_id,
                "status": "GENERATING",
                "progress": float(progress),
                "currentStep": step,
                "estimatedCompletion": datetime.utcnow().isoformat(),
            }

        # Send completion
        yield {
            "generationId": generation_id,
            "status": "COMPLETED",
            "progress": 100.0,
            "currentStep": "Complete",
            "partialResult": {"content": "Generated educational content here"},
        }

    finally:
        # Clean up queue when subscription ends
        if channel_key in event_channels:
            del event_channels[channel_key]


@subscription.field("contentGeneration")
def resolve_content_generation(update, info):
    """Resolve content generation update"""
    return update


@subscription.source("courseUpdates")
async def generate_course_updates(obj, info, courseId: str) -> AsyncGenerator[dict[str, Any], None]:
    """Subscribe to course updates"""

    course_id = uuid.UUID(courseId)
    db = info.context["db"]

    # Verify course exists
    stmt = select(Course).where(Course.id == course_id)
    result = await db.execute(stmt)
    course = result.scalar_one_or_none()

    if not course:
        raise Exception("Course not found")

    channel_key = f"course_updates_{course_id}"

    # Create queue for this subscription
    if channel_key not in event_channels:
        event_channels[channel_key] = asyncio.Queue()

    queue = event_channels[channel_key]

    try:
        while True:
            # Wait for events
            event = await queue.get()
            yield event

    except asyncio.CancelledError:
        # Subscription cancelled
        pass
    finally:
        # Clean up
        if channel_key in event_channels and event_channels[channel_key].empty():
            del event_channels[channel_key]


@subscription.field("courseUpdates")
def resolve_course_updates(update, info):
    """Resolve course update"""
    return update


@subscription.source("lessonProgress")
async def generate_lesson_progress(
    obj, info, courseId: str, studentId: str = None
) -> AsyncGenerator[dict[str, Any], None]:
    """Subscribe to lesson progress updates"""

    course_id = uuid.UUID(courseId)
    student_id = uuid.UUID(studentId) if studentId else info.context["user"].id

    channel_key = f"lesson_progress_{course_id}_{student_id}"

    # Create queue for this subscription
    if channel_key not in event_channels:
        event_channels[channel_key] = asyncio.Queue()

    event_channels[channel_key]

    try:
        # Simulate progress updates
        for i in range(0, 101, 10):
            await asyncio.sleep(1)

            yield {
                "lessonId": str(uuid.uuid4()),
                "studentId": str(student_id),
                "progress": float(i),
                "currentSection": f"Section {i // 20 + 1}",
                "timeSpent": i * 60,
                "isCompleted": i == 100,
            }

    except asyncio.CancelledError:
        pass
    finally:
        if channel_key in event_channels:
            del event_channels[channel_key]


@subscription.field("lessonProgress")
def resolve_lesson_progress(update, info):
    """Resolve lesson progress update"""
    return update


# Placeholder for required subscription fields
@subscription.field("_empty")
def resolve_empty(obj, info):
    """Placeholder resolver"""
    return None
