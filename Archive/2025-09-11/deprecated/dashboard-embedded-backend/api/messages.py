"""
Messages API endpoints
Handles messaging system for teachers, students, and parents
"""

import json
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from api.auth import get_current_user
from database import get_db
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from models.class_model import Class
from models.message import Message, MessagePriority, MessageRecipient, MessageType
from models.user import User
from pydantic import BaseModel, Field
from sqlalchemy import and_, case, func, or_
from sqlalchemy.orm import Session

from ._utils import now, safe_json_loads

router = APIRouter(prefix="/api/v1/messages", tags=["messages"])
security = HTTPBearer()

# ==================== Pydantic Models ====================


class MessageCreate(BaseModel):
    """Model for creating a message"""

    subject: str = Field(..., min_length=1, max_length=200)
    body: str = Field(..., min_length=1)
    recipient_ids: List[str] = []
    class_id: Optional[str] = None  # For class-wide messages
    parent_message_id: Optional[str] = None  # For replies
    priority: str = Field(default="normal", pattern="^(low|normal|high|urgent)$")
    attachments: Optional[List[str]] = []
    message_type: str = Field(
        default="direct", pattern="^(direct|announcement|notification|alert|system)$"
    )


class MessageUpdate(BaseModel):
    """Model for updating a message (draft editing)"""

    subject: Optional[str] = Field(None, min_length=1, max_length=200)
    body: Optional[str] = Field(None, min_length=1)
    recipient_ids: Optional[List[str]] = None
    priority: Optional[str] = Field(None, pattern="^(low|normal|high|urgent)$")
    attachments: Optional[List[str]] = None


class MessageResponse(BaseModel):
    """Response model for a message"""

    id: str
    subject: str
    body: str
    sender_id: str
    sender_name: str
    sender_role: str
    sender_avatar: Optional[str] = None
    recipient_count: int
    recipients: List[Dict[str, Any]]  # List of recipient info
    parent_message_id: Optional[str] = None
    thread_id: str
    priority: str
    attachments: List[str]
    is_read: bool
    is_starred: bool
    is_archived: bool
    is_deleted: bool
    message_type: str
    class_id: Optional[str] = None
    class_name: Optional[str] = None
    created_at: datetime
    read_at: Optional[datetime] = None
    reply_count: int = 0


class ThreadResponse(BaseModel):
    """Response model for a message thread"""

    thread_id: str
    subject: str
    messages: List[MessageResponse]
    participant_count: int
    last_message_at: datetime
    unread_count: int


class FolderStats(BaseModel):
    """Statistics for message folders"""

    inbox_count: int
    unread_count: int
    sent_count: int
    draft_count: int
    starred_count: int
    archived_count: int
    trash_count: int


# ==================== Helper Functions ====================


def get_message_recipients(message_id: str, db: Session) -> List[Dict[str, Any]]:
    """Get recipient information for a message"""
    recipients = (
        db.query(MessageRecipient, User)
        .join(User, MessageRecipient.recipient_id == User.id)
        .filter(MessageRecipient.message_id == message_id)
        .all()
    )

    return [
        {
            "id": r.User.id,
            "name": (
                (r.User.display_name or "")
                if r.User and getattr(r.User, "display_name", None) is not None
                else ""
            ),
            "email": r.User.email,
            "role": r.User.role.value,
            "is_read": r.MessageRecipient.is_read,
            "read_at": r.MessageRecipient.read_at,
        }
        for r in recipients
    ]


def get_thread_messages(thread_id: str, user_id: str, db: Session) -> List[Message]:
    """Get all messages in a thread that the user has access to"""
    # Get messages where user is sender or recipient
    messages = (
        db.query(Message)
        .filter(Message.thread_id == thread_id)
        .filter(
            or_(
                Message.sender_id == user_id,
                # Only include messages where the user is a recipient using a subquery
                # but guard against cases where the subquery could be empty or None.
                Message.id.in_(
                    db.query(MessageRecipient.message_id).filter(
                        MessageRecipient.recipient_id == user_id
                    )
                ),
            )
        )
        .order_by(Message.created_at)
        .all()
    )

    return messages


def mark_message_as_read(message_id: str, user_id: str, db: Session):
    """Mark a message as read for a specific user"""
    recipient = (
        db.query(MessageRecipient)
        .filter(
            and_(
                MessageRecipient.message_id == message_id,
                MessageRecipient.recipient_id == user_id,
            )
        )
        .first()
    )

    if recipient and not recipient.is_read:
        recipient.is_read = True
        recipient.read_at = now()
        db.commit()


# ==================== Endpoints ====================


@router.get("/", response_model=List[MessageResponse])
async def list_messages(
    folder: str = Query(
        "inbox", pattern="^(inbox|sent|drafts|starred|archived|trash|all)$"
    ),
    unread_only: bool = Query(False),
    class_id: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List messages with folder filtering"""
    user_id = current_user["id"]

    # Base query based on folder
    if folder == "sent":
        query = db.query(Message).filter(Message.sender_id == user_id)
    elif folder == "drafts":
        query = db.query(Message).filter(
            and_(Message.sender_id == user_id, Message.is_draft == True)
        )
    else:
        # Inbox, starred, archived, trash - messages received by user
        query = (
            db.query(Message)
            .join(MessageRecipient, Message.id == MessageRecipient.message_id)
            .filter(MessageRecipient.recipient_id == user_id)
        )

        if folder == "inbox":
            query = query.filter(
                and_(
                    MessageRecipient.is_deleted == False,
                    MessageRecipient.is_archived == False,
                )
            )
        elif folder == "starred":
            query = query.filter(MessageRecipient.is_starred == True)
        elif folder == "archived":
            query = query.filter(MessageRecipient.is_archived == True)
        elif folder == "trash":
            query = query.filter(MessageRecipient.is_deleted == True)

    # Apply additional filters
    if unread_only and folder != "sent":
        query = query.filter(MessageRecipient.is_read == False)

    if class_id:
        query = query.filter(Message.class_id == class_id)

    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            or_(
                Message.subject.ilike(search_pattern),
                Message.body.ilike(search_pattern),
            )
        )

    # Execute query with pagination
    messages = (
        query.order_by(Message.created_at.desc()).offset(offset).limit(limit).all()
    )

    # Transform to response model
    response = []
    for message in messages:
        # Get recipient info
        recipients = get_message_recipients(message.id, db)

        # Get sender info
        sender = db.query(User).filter(User.id == message.sender_id).first()

        # Get read status for current user
        is_read = True
        is_starred = False
        is_archived = False
        is_deleted = False
        read_at = None

        if folder != "sent":
            recipient_record = (
                db.query(MessageRecipient)
                .filter(
                    and_(
                        MessageRecipient.message_id == message.id,
                        MessageRecipient.recipient_id == user_id,
                    )
                )
                .first()
            )

            if recipient_record:
                is_read = recipient_record.is_read
                is_starred = recipient_record.is_starred
                is_archived = recipient_record.is_archived
                is_deleted = recipient_record.is_deleted
                read_at = recipient_record.read_at

        # Get reply count
        reply_count = (
            db.query(Message).filter(Message.reply_to_id == message.id).count()
        )

        # Get class info if applicable
        class_name = None
        if message.class_id:
            class_obj = db.query(Class).filter(Class.id == message.class_id).first()
            if class_obj:
                class_name = class_obj.name

        response.append(
            MessageResponse(
                id=message.id,
                subject=message.subject,
                body=message.body,
                sender_id=message.sender_id,
                sender_name=(sender.display_name or "Unknown") if sender else "Unknown",
                sender_role=(
                    str(getattr(sender.role, "value", sender.role))
                    if sender
                    else "Unknown"
                ),
                sender_avatar=None,  # TODO: Add avatar support
                recipient_count=len(recipients),
                recipients=recipients,
                parent_message_id=message.reply_to_id,
                thread_id=str(message.thread_id or ""),
                priority=str(getattr(message.priority, "value", message.priority)),
                attachments=(
                    safe_json_loads(message.attachments, [])
                    if message.attachments
                    else []
                ),
                is_read=is_read,
                is_starred=is_starred,
                is_archived=is_archived,
                is_deleted=is_deleted,
                message_type=str(
                    getattr(message.message_type, "value", message.message_type)
                ),
                class_id=message.class_id,
                class_name=class_name,
                created_at=message.created_at,
                read_at=read_at,
                reply_count=reply_count,
            )
        )

    return response


@router.post("/", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def send_message(
    message_data: MessageCreate,
    is_draft: bool = Query(False),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Send a new message or save as draft"""
    # Validate recipients exist
    # Validate recipients exist. If recipient_ids is empty, treat as invalid input.
    if not message_data.recipient_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="recipient_ids must include at least one user",
        )

    recipients = db.query(User).filter(User.id.in_(message_data.recipient_ids)).all()
    if len(recipients) != len(message_data.recipient_ids):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="One or more recipients not found",
        )

    # If class message, verify sender has access to class
    if message_data.class_id:
        class_obj = db.query(Class).filter(Class.id == message_data.class_id).first()
        if not class_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Class not found"
            )

        if (
            current_user["role"] == "Teacher"
            and class_obj.teacher_id != current_user["id"]
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only send messages to your own classes",
            )

    # Determine thread_id
    thread_id = str(uuid.uuid4())
    if message_data.parent_message_id:
        # Reply to existing message
        parent_message = (
            db.query(Message)
            .filter(Message.id == message_data.parent_message_id)
            .first()
        )

        if not parent_message:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Parent message not found"
            )

        # Check if user has access to parent message
        has_access = (
            parent_message.sender_id == current_user["id"]
            or db.query(MessageRecipient)
            .filter(
                and_(
                    MessageRecipient.message_id == parent_message.id,
                    MessageRecipient.recipient_id == current_user["id"],
                )
            )
            .first()
            is not None
        )

        if not has_access:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have access to reply to this message",
            )

        thread_id = parent_message.thread_id

    # Create message
    new_message = Message(
        id=str(uuid.uuid4()),
        subject=message_data.subject,
        body=message_data.body,
        sender_id=current_user["id"],
        reply_to_id=message_data.parent_message_id,
        thread_id=thread_id,
        priority=MessagePriority[message_data.priority.upper()],
        attachments=(
            json.dumps(message_data.attachments) if message_data.attachments else None
        ),
        message_type=MessageType[message_data.message_type.upper()],
        is_draft=is_draft,
        class_id=message_data.class_id,
        sent_at=now(),
    )

    db.add(new_message)

    # Create recipient records (even for drafts, to track intended recipients)
    for recipient_id in message_data.recipient_ids:
        recipient_record = MessageRecipient(
            id=str(uuid.uuid4()),
            message_id=new_message.id,
            recipient_id=recipient_id,
            is_delivered=not is_draft,
            delivered_at=now(),
        )
        db.add(recipient_record)

    db.commit()
    db.refresh(new_message)

    # Get full message info for response
    recipients = get_message_recipients(new_message.id, db)
    sender = db.query(User).filter(User.id == current_user["id"]).first()

    class_name = None
    if new_message.class_id:
        class_obj = db.query(Class).filter(Class.id == new_message.class_id).first()
        if class_obj:
            class_name = class_obj.name

    return MessageResponse(
        id=new_message.id,
        subject=new_message.subject,
        body=new_message.body,
        sender_id=new_message.sender_id,
        sender_name=(sender.display_name or "Unknown") if sender else "Unknown",
        sender_role=(
            str(getattr(sender.role, "value", sender.role)) if sender else "Unknown"
        ),
        sender_avatar=None,
        recipient_count=len(recipients),
        recipients=recipients,
        parent_message_id=new_message.reply_to_id,
        thread_id=new_message.thread_id or "",
        priority=str(getattr(new_message.priority, "value", new_message.priority)),
        attachments=(
            safe_json_loads(new_message.attachments, [])
            if new_message.attachments
            else []
        ),
        is_read=False,
        is_starred=False,
        is_archived=False,
        is_deleted=False,
        message_type=str(
            getattr(new_message.message_type, "value", new_message.message_type)
        ),
        class_id=new_message.class_id,
        class_name=class_name,
        created_at=new_message.created_at,
        read_at=None,
        reply_count=0,
    )


@router.get("/unread-count", response_model=dict)
async def get_unread_count(
    current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)
):
    """Get unread message count for the current user"""
    user_id = current_user["id"]

    # Unread messages
    unread_count = (
        db.query(MessageRecipient)
        .filter(
            and_(
                MessageRecipient.recipient_id == user_id,
                MessageRecipient.is_read == False,
                MessageRecipient.is_deleted == False,
            )
        )
        .count()
    )

    return {"count": unread_count}


@router.get("/stats", response_model=FolderStats)
async def get_message_stats(
    current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)
):
    """Get message statistics for the current user"""
    user_id = current_user["id"]

    # Inbox messages (received, not deleted, not archived)
    inbox_count = (
        db.query(MessageRecipient)
        .filter(
            and_(
                MessageRecipient.recipient_id == user_id,
                MessageRecipient.is_deleted == False,
                MessageRecipient.is_archived == False,
            )
        )
        .count()
    )

    # Unread messages
    unread_count = (
        db.query(MessageRecipient)
        .filter(
            and_(
                MessageRecipient.recipient_id == user_id,
                MessageRecipient.is_read == False,
                MessageRecipient.is_deleted == False,
            )
        )
        .count()
    )

    # Sent messages
    sent_count = (
        db.query(Message)
        .filter(and_(Message.sender_id == user_id, Message.is_draft == False))
        .count()
    )

    # Draft messages
    draft_count = (
        db.query(Message)
        .filter(and_(Message.sender_id == user_id, Message.is_draft == True))
        .count()
    )

    # Starred messages
    starred_count = (
        db.query(MessageRecipient)
        .filter(
            and_(
                MessageRecipient.recipient_id == user_id,
                MessageRecipient.is_starred == True,
                MessageRecipient.is_deleted == False,
            )
        )
        .count()
    )

    # Archived messages
    archived_count = (
        db.query(MessageRecipient)
        .filter(
            and_(
                MessageRecipient.recipient_id == user_id,
                MessageRecipient.is_archived == True,
                MessageRecipient.is_deleted == False,
            )
        )
        .count()
    )

    # Trash messages
    trash_count = (
        db.query(MessageRecipient)
        .filter(
            and_(
                MessageRecipient.recipient_id == user_id,
                MessageRecipient.is_deleted == True,
            )
        )
        .count()
    )

    return FolderStats(
        inbox_count=inbox_count,
        unread_count=unread_count,
        sent_count=sent_count,
        draft_count=draft_count,
        starred_count=starred_count,
        archived_count=archived_count,
        trash_count=trash_count,
    )


@router.get("/thread/{thread_id}", response_model=ThreadResponse)
async def get_message_thread(
    thread_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get all messages in a thread"""
    user_id = current_user["id"]

    # Get all messages in thread that user has access to
    messages = get_thread_messages(thread_id, user_id, db)

    if not messages:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Thread not found or you don't have access",
        )

    # Transform messages to response format
    response_messages = []
    for message in messages:
        recipients = get_message_recipients(message.id, db)
        sender = db.query(User).filter(User.id == message.sender_id).first()

        # Get read status for current user
        is_read = True
        is_starred = False
        is_archived = False
        is_deleted = False
        read_at = None

        if message.sender_id != user_id:
            recipient_record = (
                db.query(MessageRecipient)
                .filter(
                    and_(
                        MessageRecipient.message_id == message.id,
                        MessageRecipient.recipient_id == user_id,
                    )
                )
                .first()
            )

            if recipient_record:
                is_read = recipient_record.is_read
                is_starred = recipient_record.is_starred
                is_archived = recipient_record.is_archived
                is_deleted = recipient_record.is_deleted
                read_at = recipient_record.read_at

                # Mark as read when viewing thread
                if not is_read:
                    mark_message_as_read(message.id, user_id, db)

        response_messages.append(
            MessageResponse(
                id=message.id,
                subject=message.subject,
                body=message.body,
                sender_id=message.sender_id,
                sender_name=(sender.display_name or "Unknown") if sender else "Unknown",
                sender_role=(
                    str(getattr(sender.role, "value", sender.role))
                    if sender
                    else "Unknown"
                ),
                sender_avatar=None,
                recipient_count=len(recipients),
                recipients=recipients,
                parent_message_id=message.reply_to_id,
                thread_id=str(message.thread_id or ""),
                priority=str(getattr(message.priority, "value", message.priority)),
                attachments=(
                    safe_json_loads(message.attachments, [])
                    if message.attachments
                    else []
                ),
                is_read=is_read,
                is_starred=is_starred,
                is_archived=is_archived,
                is_deleted=is_deleted,
                message_type=str(
                    getattr(message.message_type, "value", message.message_type)
                ),
                class_id=message.class_id,
                class_name=None,  # TODO: Add class name
                created_at=message.created_at,
                read_at=read_at,
                reply_count=0,
            )
        )

    # Get participant count
    participant_ids = set()
    for msg in messages:
        participant_ids.add(msg.sender_id)
        for recipient in get_message_recipients(msg.id, db):
            participant_ids.add(recipient["id"])

    # Count unread messages in thread
    unread_count = (
        db.query(MessageRecipient)
        .join(Message, MessageRecipient.message_id == Message.id)
        .filter(
            and_(
                Message.thread_id == thread_id,
                MessageRecipient.recipient_id == user_id,
                MessageRecipient.is_read == False,
            )
        )
        .count()
    )

    return ThreadResponse(
        thread_id=thread_id,
        subject=messages[0].subject,
        messages=response_messages,
        participant_count=len(participant_ids),
        last_message_at=messages[-1].created_at,
        unread_count=unread_count,
    )


@router.get("/{message_id}", response_model=MessageResponse)
async def get_message(
    message_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get a specific message"""
    user_id = current_user["id"]

    # Get message
    message = db.query(Message).filter(Message.id == message_id).first()
    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Message not found"
        )

    # Check if user has access
    has_access = message.sender_id == user_id
    recipient_record = None

    if not has_access:
        recipient_record = (
            db.query(MessageRecipient)
            .filter(
                and_(
                    MessageRecipient.message_id == message_id,
                    MessageRecipient.recipient_id == user_id,
                )
            )
            .first()
        )

        has_access = recipient_record is not None

    if not has_access:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this message",
        )

    # Mark as read if recipient
    # If the recipient record exists and the message is not yet marked read,
    # mark it as read. Previously this compared against a missing MessageStatus
    # enum; use the boolean `is_read` field on the recipient record instead.
    if recipient_record and not recipient_record.is_read:
        mark_message_as_read(message_id, user_id, db)

    # Get full message info
    recipients = get_message_recipients(message.id, db)
    sender = db.query(User).filter(User.id == message.sender_id).first()

    # Get read status for current user
    is_read = True
    is_starred = False
    is_archived = False
    is_deleted = False
    read_at = None

    if recipient_record:
        is_read = recipient_record.is_read
        is_starred = recipient_record.is_starred
        is_archived = recipient_record.is_archived
        is_deleted = recipient_record.is_deleted
        read_at = recipient_record.read_at

    # Get reply count
    reply_count = db.query(Message).filter(Message.reply_to_id == message.id).count()

    class_name = None
    if message.class_id:
        class_obj = db.query(Class).filter(Class.id == message.class_id).first()
        if class_obj:
            class_name = class_obj.name

    return MessageResponse(
        id=message.id,
        subject=message.subject,
        body=message.body,
        sender_id=message.sender_id,
        sender_name=(sender.display_name or "Unknown") if sender else "Unknown",
        sender_role=sender.role.value if sender else "Unknown",
        sender_avatar=None,
        recipient_count=len(recipients),
        recipients=recipients,
        parent_message_id=message.parent_message_id,
        thread_id=str(message.thread_id or ""),
        priority=str(getattr(message.priority, "value", message.priority)),
        attachments=(
            safe_json_loads(message.attachments, []) if message.attachments else []
        ),
        is_read=is_read,
        is_starred=is_starred,
        is_archived=is_archived,
        is_deleted=is_deleted,
        message_type=str(getattr(message.message_type, "value", message.message_type)),
        class_id=message.class_id,
        class_name=class_name,
        created_at=message.created_at,
        read_at=read_at,
        reply_count=reply_count,
    )


@router.put("/{message_id}/read", response_model=Dict[str, str])
async def mark_as_read(
    message_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Mark a message as read"""
    mark_message_as_read(message_id, current_user["id"], db)
    return {"message": "Message marked as read"}


@router.put("/{message_id}/unread", response_model=Dict[str, str])
async def mark_as_unread(
    message_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Mark a message as unread"""
    recipient = (
        db.query(MessageRecipient)
        .filter(
            and_(
                MessageRecipient.message_id == message_id,
                MessageRecipient.recipient_id == current_user["id"],
            )
        )
        .first()
    )

    if not recipient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message not found in your inbox",
        )

    recipient.is_read = False
    recipient.read_at = None
    db.commit()

    return {"message": "Message marked as unread"}


@router.put("/{message_id}/star", response_model=Dict[str, str])
async def star_message(
    message_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Star/unstar a message"""
    # Check if user is sender or recipient
    message = db.query(Message).filter(Message.id == message_id).first()
    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Message not found"
        )

    if message.sender_id == current_user["id"]:
        # Sender starring their own message (sent folder)
        # This could be stored in a separate table or user preferences
        return {"message": "Feature not yet implemented for sent messages"}

    recipient = (
        db.query(MessageRecipient)
        .filter(
            and_(
                MessageRecipient.message_id == message_id,
                MessageRecipient.recipient_id == current_user["id"],
            )
        )
        .first()
    )

    if not recipient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message not found in your inbox",
        )

    recipient.is_starred = not recipient.is_starred
    db.commit()

    action = "starred" if recipient.is_starred else "unstarred"
    return {"message": f"Message {action}"}


@router.put("/{message_id}/archive", response_model=Dict[str, str])
async def archive_message(
    message_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Archive/unarchive a message"""
    recipient = (
        db.query(MessageRecipient)
        .filter(
            and_(
                MessageRecipient.message_id == message_id,
                MessageRecipient.recipient_id == current_user["id"],
            )
        )
        .first()
    )

    if not recipient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message not found in your inbox",
        )

    recipient.is_archived = not recipient.is_archived
    if recipient.is_archived:
        recipient.is_deleted = False  # Undelete if archiving
    db.commit()

    action = "archived" if recipient.is_archived else "unarchived"
    return {"message": f"Message {action}"}


@router.delete("/{message_id}", response_model=Dict[str, str])
async def delete_message(
    message_id: str,
    permanent: bool = Query(False),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Move message to trash or permanently delete"""
    user_id = current_user["id"]

    # Check if user is sender
    message = db.query(Message).filter(Message.id == message_id).first()
    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Message not found"
        )

    if message.sender_id == user_id:
        # Sender deleting their own message
        if message.is_draft or permanent:
            # Permanently delete draft or if requested
            db.delete(message)
            db.commit()
            return {"message": "Message permanently deleted"}
        else:
            # Soft delete for sent messages
            message.is_deleted_by_sender = True
            db.commit()
            return {"message": "Message moved to trash"}

    # Recipient deleting message
    recipient = (
        db.query(MessageRecipient)
        .filter(
            and_(
                MessageRecipient.message_id == message_id,
                MessageRecipient.recipient_id == user_id,
            )
        )
        .first()
    )

    if not recipient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Message not found"
        )

    if permanent and recipient.is_deleted:
        # Permanently delete for recipient
        db.delete(recipient)
    else:
        # Move to trash
        recipient.is_deleted = not recipient.is_deleted
        if recipient.is_deleted:
            recipient.is_archived = False  # Unarchive if deleting

    db.commit()

    if permanent:
        return {"message": "Message permanently deleted"}
    else:
        action = "moved to trash" if recipient.is_deleted else "restored from trash"
        return {"message": f"Message {action}"}


@router.post("/{message_id}/reply", response_model=MessageResponse)
async def reply_to_message(
    message_id: str,
    reply_data: MessageCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Reply to a message"""
    # Set parent message id
    reply_data.parent_message_id = message_id

    # Use the send_message endpoint logic
    return await send_message(reply_data, False, current_user, db)


@router.post("/{message_id}/forward", response_model=MessageResponse)
async def forward_message(
    message_id: str,
    forward_data: MessageCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Forward a message to new recipients"""
    # Get original message
    original_message = db.query(Message).filter(Message.id == message_id).first()
    if not original_message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Message not found"
        )

    # Check if user has access to original message
    has_access = (
        original_message.sender_id == current_user["id"]
        or db.query(MessageRecipient)
        .filter(
            and_(
                MessageRecipient.message_id == message_id,
                MessageRecipient.recipient_id == current_user["id"],
            )
        )
        .first()
        is not None
    )

    if not has_access:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to forward this message",
        )

    # Modify body to include forward information
    forward_data.subject = f"Fwd: {original_message.subject}"
    # Safely fetch the original sender's display name
    orig_sender = db.query(User).filter(User.id == original_message.sender_id).first()
    orig_sender_name = (orig_sender.display_name or "") if orig_sender else ""

    forward_data.body = f"""
---------- Forwarded message ----------
From: {orig_sender_name}
Date: {original_message.created_at}
Subject: {original_message.subject}

{original_message.body}
---------- End forwarded message ----------

{forward_data.body}
"""

    # Send as new message
    return await send_message(forward_data, False, current_user, db)
