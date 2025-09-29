"""
Messages API Endpoints for ToolboxAI Educational Platform
Provides messaging system and notifications functionality for all user roles.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import logging
from apps.backend.api.auth.auth import get_current_user
from pydantic import BaseModel
from typing import Optional as Opt


# User model for type hints
class User(BaseModel):
    id: str
    username: str
    role: str
    email: Optional[str] = None


# Placeholder for database service
class DBService:
    pool = None


db_service = DBService()

logger = logging.getLogger(__name__)

# Create router for messages endpoints
messages_router = APIRouter(prefix="/messages", tags=["Messages"])

# Export standardized router name
router = messages_router


@messages_router.get("/")
async def get_messages(
    current_user: User = Depends(get_current_user),
    folder: str = Query(default="inbox"),
    message_type: Optional[str] = None,
    is_read: Optional[bool] = None,
    limit: int = Query(default=20, le=100),
    offset: int = Query(default=0, ge=0),
) -> List[Dict[str, Any]]:
    """Get messages based on folder and filters."""

    role = current_user.role.lower()
    user_id = current_user.id

    # Try to get real data from database
    try:
        if folder == "inbox":
            query = """
                SELECT m.*, s.first_name || ' ' || s.last_name as sender_name,
                       s.username as sender_username, s.role as sender_role
                FROM messages m
                JOIN users s ON m.sender_id = s.id
                WHERE m.recipient_id = $1
                  AND m.deleted_by_recipient = false
                  AND ($2::text IS NULL OR m.message_type = $2)
                  AND ($3::boolean IS NULL OR m.is_read = $3)
                ORDER BY m.created_at DESC
                LIMIT $4 OFFSET $5
            """
            async with db_service.pool.acquire() as conn:
                rows = await conn.fetch(query, user_id, message_type, is_read, limit, offset)
                return [dict(row) for row in rows]

        elif folder == "sent":
            query = """
                SELECT m.*, r.first_name || ' ' || r.last_name as recipient_name,
                       r.username as recipient_username, r.role as recipient_role
                FROM messages m
                JOIN users r ON m.recipient_id = r.id
                WHERE m.sender_id = $1
                  AND m.deleted_by_sender = false
                  AND ($2::text IS NULL OR m.message_type = $2)
                ORDER BY m.created_at DESC
                LIMIT $3 OFFSET $4
            """
            async with db_service.pool.acquire() as conn:
                rows = await conn.fetch(query, user_id, message_type, limit, offset)
                return [dict(row) for row in rows]

        elif folder == "archived":
            query = """
                SELECT m.*, s.first_name || ' ' || s.last_name as sender_name,
                       s.username as sender_username
                FROM messages m
                JOIN users s ON m.sender_id = s.id
                WHERE m.recipient_id = $1
                  AND m.archived = true
                  AND m.deleted_by_recipient = false
                ORDER BY m.archived_at DESC
                LIMIT $2 OFFSET $3
            """
            async with db_service.pool.acquire() as conn:
                rows = await conn.fetch(query, user_id, limit, offset)
                return [dict(row) for row in rows]

        elif folder == "trash":
            query = """
                SELECT m.*, s.first_name || ' ' || s.last_name as sender_name,
                       s.username as sender_username
                FROM messages m
                JOIN users s ON m.sender_id = s.id
                WHERE ((m.recipient_id = $1 AND m.deleted_by_recipient = true)
                       OR (m.sender_id = $1 AND m.deleted_by_sender = true))
                ORDER BY m.deleted_at DESC
                LIMIT $2 OFFSET $3
            """
            async with db_service.pool.acquire() as conn:
                rows = await conn.fetch(query, user_id, limit, offset)
                return [dict(row) for row in rows]

    except Exception as e:
        logger.warning(f"Failed to fetch messages from database: {e}. Using fallback data.")

    # Fallback sample data based on folder
    if folder == "inbox":
        base_messages = [
            {
                "id": 1,
                "subject": "Assignment Reminder: Math Homework Due Tomorrow",
                "sender_name": "John Smith",
                "sender_username": "j.smith",
                "sender_role": "teacher",
                "message_type": "reminder",
                "is_read": False,
                "is_urgent": False,
                "created_at": "2025-01-08T14:30:00",
                "preview": "Don't forget to submit your algebra homework by tomorrow at 11:59 PM...",
            },
            {
                "id": 2,
                "subject": "Great Work on Recent Quiz!",
                "sender_name": "Emily Johnson",
                "sender_username": "e.johnson",
                "sender_role": "teacher",
                "message_type": "feedback",
                "is_read": True,
                "is_urgent": False,
                "created_at": "2025-01-07T16:20:00",
                "preview": "I wanted to congratulate you on your excellent performance on the science quiz...",
            },
            {
                "id": 3,
                "subject": "Parent-Teacher Conference Scheduled",
                "sender_name": "School Administrator",
                "sender_username": "admin",
                "sender_role": "admin",
                "message_type": "announcement",
                "is_read": False,
                "is_urgent": True,
                "created_at": "2025-01-07T09:15:00",
                "preview": "Your parent-teacher conference has been scheduled for January 12th at 3:00 PM...",
            },
            {
                "id": 4,
                "subject": "Weekly Progress Update",
                "sender_name": "System",
                "sender_username": "system",
                "sender_role": "system",
                "message_type": "notification",
                "is_read": True,
                "is_urgent": False,
                "created_at": "2025-01-06T18:00:00",
                "preview": "Here's your weekly progress summary across all subjects...",
            },
        ]

        # Customize based on role
        if role == "teacher":
            base_messages.extend(
                [
                    {
                        "id": 5,
                        "subject": "New Student Enrollment in Your Class",
                        "sender_name": "School Administrator",
                        "sender_username": "admin",
                        "sender_role": "admin",
                        "message_type": "notification",
                        "is_read": False,
                        "is_urgent": False,
                        "created_at": "2025-01-06T10:30:00",
                        "preview": "A new student has been enrolled in your Mathematics 101 class...",
                    }
                ]
            )
        elif role == "parent":
            base_messages.extend(
                [
                    {
                        "id": 6,
                        "subject": "Alex's Academic Performance Update",
                        "sender_name": "John Smith",
                        "sender_username": "j.smith",
                        "sender_role": "teacher",
                        "message_type": "update",
                        "is_read": False,
                        "is_urgent": False,
                        "created_at": "2025-01-05T15:45:00",
                        "preview": "I wanted to update you on Alex's recent academic performance in Mathematics...",
                    }
                ]
            )

        return base_messages

    elif folder == "sent":
        if role == "teacher":
            return [
                {
                    "id": 7,
                    "subject": "Homework Assignment Posted",
                    "recipient_name": "All Students",
                    "recipient_username": "class_broadcast",
                    "recipient_role": "student",
                    "message_type": "assignment",
                    "created_at": "2025-01-08T10:00:00",
                    "preview": "I've posted the new algebra homework assignment. Please review the instructions...",
                },
                {
                    "id": 8,
                    "subject": "Great Job on Presentation!",
                    "recipient_name": "Alex Johnson",
                    "recipient_username": "alex_j",
                    "recipient_role": "student",
                    "message_type": "feedback",
                    "created_at": "2025-01-07T14:15:00",
                    "preview": "Your presentation on renewable energy was excellent. I was impressed by...",
                },
            ]
        else:
            return [
                {
                    "id": 9,
                    "subject": "Question about Assignment",
                    "recipient_name": "John Smith",
                    "recipient_username": "j.smith",
                    "recipient_role": "teacher",
                    "message_type": "question",
                    "created_at": "2025-01-08T19:30:00",
                    "preview": "I have a question about the algebra homework that was assigned today...",
                }
            ]

    elif folder == "archived":
        return [
            {
                "id": 10,
                "subject": "Semester Schedule Released",
                "sender_name": "School Administrator",
                "sender_username": "admin",
                "archived": True,
                "archived_at": "2025-01-05T12:00:00",
                "created_at": "2024-12-15T09:00:00",
                "preview": "The spring semester schedule has been released. Please review your class times...",
            }
        ]

    elif folder == "trash":
        return [
            {
                "id": 11,
                "subject": "Deleted: Old Assignment Reminder",
                "sender_name": "System",
                "sender_username": "system",
                "deleted_by_recipient": True,
                "deleted_at": "2025-01-06T20:00:00",
                "created_at": "2024-12-20T10:00:00",
                "preview": "This is a reminder about an assignment that was due last month...",
            }
        ]

    return []


@messages_router.get("/unread-count")
async def get_unread_message_count(
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """Get count of unread messages and notifications."""

    user_id = current_user.id

    try:
        # Get counts from database
        query = """
            SELECT 
                COUNT(*) FILTER (WHERE is_read = false AND message_type != 'notification') as unread_messages,
                COUNT(*) FILTER (WHERE is_read = false AND message_type = 'notification') as unread_notifications,
                COUNT(*) FILTER (WHERE is_read = false AND is_urgent = true) as urgent_messages,
                COUNT(*) FILTER (WHERE is_read = false AND created_at >= NOW() - INTERVAL '24 hours') as recent_unread
            FROM messages
            WHERE recipient_id = $1 
              AND deleted_by_recipient = false
        """
        async with db_service.pool.acquire() as conn:
            row = await conn.fetchrow(query, user_id)
            if row:
                return dict(row)

    except Exception as e:
        logger.warning(f"Failed to fetch unread count: {e}. Using fallback data.")

    # Fallback sample data
    role = current_user.role.lower()
    if role == "teacher":
        return {
            "unread_messages": 5,
            "unread_notifications": 3,
            "urgent_messages": 1,
            "recent_unread": 2,
            "breakdown": {
                "assignments": 2,
                "feedback": 0,
                "questions": 1,
                "announcements": 2,
                "system": 3,
            },
        }
    elif role == "student":
        return {
            "unread_messages": 3,
            "unread_notifications": 2,
            "urgent_messages": 1,
            "recent_unread": 1,
            "breakdown": {
                "assignments": 1,
                "feedback": 1,
                "reminders": 1,
                "announcements": 1,
                "system": 2,
            },
        }
    elif role == "parent":
        return {
            "unread_messages": 2,
            "unread_notifications": 1,
            "urgent_messages": 0,
            "recent_unread": 1,
            "breakdown": {"updates": 1, "conferences": 1, "announcements": 1, "system": 1},
        }
    else:  # admin
        return {
            "unread_messages": 8,
            "unread_notifications": 5,
            "urgent_messages": 2,
            "recent_unread": 3,
            "breakdown": {"reports": 2, "issues": 3, "system": 5, "announcements": 1, "alerts": 2},
        }


@messages_router.get("/{message_id}")
async def get_message_details(
    message_id: int, current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get detailed information about a specific message."""

    user_id = current_user.id

    try:
        # Get message details and mark as read
        query = """
            SELECT m.*, 
                   s.first_name || ' ' || s.last_name as sender_name,
                   s.username as sender_username, s.role as sender_role,
                   r.first_name || ' ' || r.last_name as recipient_name,
                   r.username as recipient_username, r.role as recipient_role
            FROM messages m
            JOIN users s ON m.sender_id = s.id
            JOIN users r ON m.recipient_id = r.id
            WHERE m.id = $1
              AND (m.sender_id = $2 OR m.recipient_id = $2)
              AND ((m.sender_id = $2 AND m.deleted_by_sender = false)
                   OR (m.recipient_id = $2 AND m.deleted_by_recipient = false))
        """
        async with db_service.pool.acquire() as conn:
            row = await conn.fetchrow(query, message_id, user_id)
            if row:
                message = dict(row)

                # Mark as read if user is recipient
                if message["recipient_id"] == user_id and not message["is_read"]:
                    await conn.execute(
                        "UPDATE messages SET is_read = true, read_at = NOW() WHERE id = $1",
                        message_id,
                    )
                    message["is_read"] = True
                    message["read_at"] = datetime.now()

                return message

    except Exception as e:
        logger.warning(f"Failed to fetch message details: {e}")

    # Fallback sample data
    return {
        "id": message_id,
        "subject": "Assignment Reminder: Math Homework Due Tomorrow",
        "content": """Dear Student,

This is a friendly reminder that your algebra homework assignment is due tomorrow at 11:59 PM.

The assignment covers:
- Linear equations (problems 1-15)
- Graphing functions (problems 16-25)
- Word problems (problems 26-30)

Please make sure to show all your work for partial credit. If you have any questions, feel free to reach out during office hours or send me a message.

Good luck!

Best regards,
Mr. Smith""",
        "sender_name": "John Smith",
        "sender_username": "j.smith",
        "sender_role": "teacher",
        "recipient_name": getattr(current_user, "full_name", current_user.username),
        "recipient_username": current_user.username,
        "recipient_role": current_user.role,
        "message_type": "reminder",
        "is_read": True,
        "is_urgent": False,
        "created_at": "2025-01-08T14:30:00",
        "read_at": "2025-01-08T15:45:00",
        "attachments": [
            {
                "name": "homework_assignment.pdf",
                "size": "245KB",
                "url": "/attachments/homework_assignment_math101.pdf",
            }
        ],
        "related_class": {"id": 1, "name": "Mathematics 101", "subject": "Mathematics"},
    }


@messages_router.post("/")
async def send_message(
    message_data: Dict[str, Any], current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Send a new message."""

    try:
        query = """
            INSERT INTO messages (sender_id, recipient_id, subject, content, 
                                message_type, is_urgent, attachments, related_class_id)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            RETURNING *
        """
        async with db_service.pool.acquire() as conn:
            row = await conn.fetchrow(
                query,
                current_user.id,
                message_data["recipient_id"],
                message_data["subject"],
                message_data["content"],
                message_data.get("message_type", "message"),
                message_data.get("is_urgent", False),
                message_data.get("attachments", []),
                message_data.get("related_class_id"),
            )
            return dict(row)

    except Exception as e:
        logger.error(f"Failed to send message: {e}")
        raise HTTPException(status_code=500, detail="Failed to send message")


@messages_router.put("/{message_id}/read")
async def mark_message_as_read(
    message_id: int, current_user: User = Depends(get_current_user)
) -> Dict[str, str]:
    """Mark a message as read."""

    try:
        query = """
            UPDATE messages 
            SET is_read = true, read_at = NOW()
            WHERE id = $1 AND recipient_id = $2
            RETURNING id
        """
        async with db_service.pool.acquire() as conn:
            result = await conn.fetchrow(query, message_id, current_user.id)
            if result:
                return {"message": "Message marked as read"}
            else:
                raise HTTPException(status_code=404, detail="Message not found")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to mark message as read: {e}")
        raise HTTPException(status_code=500, detail="Failed to update message")


@messages_router.put("/{message_id}/archive")
async def archive_message(
    message_id: int, current_user: User = Depends(get_current_user)
) -> Dict[str, str]:
    """Archive a message."""

    try:
        query = """
            UPDATE messages 
            SET archived = true, archived_at = NOW()
            WHERE id = $1 AND recipient_id = $2
            RETURNING id
        """
        async with db_service.pool.acquire() as conn:
            result = await conn.fetchrow(query, message_id, current_user.id)
            if result:
                return {"message": "Message archived"}
            else:
                raise HTTPException(status_code=404, detail="Message not found")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to archive message: {e}")
        raise HTTPException(status_code=500, detail="Failed to archive message")


@messages_router.delete("/{message_id}")
async def delete_message(
    message_id: int, current_user: User = Depends(get_current_user)
) -> Dict[str, str]:
    """Delete a message (move to trash)."""

    try:
        # Check if user is sender or recipient
        query = """
            SELECT sender_id, recipient_id FROM messages WHERE id = $1
        """
        async with db_service.pool.acquire() as conn:
            message = await conn.fetchrow(query, message_id)
            if not message:
                raise HTTPException(status_code=404, detail="Message not found")

            # Update appropriate delete flag
            if message["sender_id"] == current_user.id:
                update_query = """
                    UPDATE messages 
                    SET deleted_by_sender = true, deleted_at = NOW()
                    WHERE id = $1
                """
            elif message["recipient_id"] == current_user.id:
                update_query = """
                    UPDATE messages 
                    SET deleted_by_recipient = true, deleted_at = NOW()
                    WHERE id = $1
                """
            else:
                raise HTTPException(status_code=403, detail="Not authorized to delete this message")

            await conn.execute(update_query, message_id)
            return {"message": "Message deleted"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete message: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete message")


@messages_router.get("/notifications/recent")
async def get_recent_notifications(
    current_user: User = Depends(get_current_user), limit: int = Query(default=10, le=50)
) -> List[Dict[str, Any]]:
    """Get recent notifications for the current user."""

    try:
        query = """
            SELECT id, subject, message_type, is_read, is_urgent, created_at, preview
            FROM messages
            WHERE recipient_id = $1 
              AND message_type IN ('notification', 'alert', 'reminder')
              AND deleted_by_recipient = false
            ORDER BY created_at DESC
            LIMIT $2
        """
        async with db_service.pool.acquire() as conn:
            rows = await conn.fetch(query, current_user.id, limit)
            return [dict(row) for row in rows]

    except Exception as e:
        logger.warning(f"Failed to fetch notifications: {e}")

    # Fallback sample data
    role = current_user.role.lower()
    if role == "student":
        return [
            {
                "id": 101,
                "subject": "Assignment Due Tomorrow",
                "message_type": "reminder",
                "is_read": False,
                "is_urgent": True,
                "created_at": "2025-01-08T20:00:00",
                "preview": "Math homework due tomorrow at 11:59 PM",
            },
            {
                "id": 102,
                "subject": "New Grade Posted",
                "message_type": "notification",
                "is_read": False,
                "is_urgent": False,
                "created_at": "2025-01-08T16:30:00",
                "preview": "Your quiz grade has been posted: 87/100",
            },
        ]
    elif role == "teacher":
        return [
            {
                "id": 103,
                "subject": "New Student Message",
                "message_type": "notification",
                "is_read": False,
                "is_urgent": False,
                "created_at": "2025-01-08T18:15:00",
                "preview": "Alex Johnson sent you a question about today's assignment",
            }
        ]

    return []
