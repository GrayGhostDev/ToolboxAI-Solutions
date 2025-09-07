"""
Internal messaging system models
"""

import enum
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import JSON, Boolean, DateTime
from sqlalchemy import Enum as SQLEnum
from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin

if TYPE_CHECKING:
    from .assessment import Assessment
    from .class_model import Class
    from .lesson import Lesson
    from .user import User


class MessagePriority(enum.Enum):
    """Message priority levels"""

    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class MessageType(enum.Enum):
    """Types of messages"""

    DIRECT = "direct"
    ANNOUNCEMENT = "announcement"
    NOTIFICATION = "notification"
    ALERT = "alert"
    SYSTEM = "system"


class Message(Base, TimestampMixin):
    """Internal messaging between users"""

    __tablename__ = "messages"

    # Primary key
    id: Mapped[str] = mapped_column(String(36), primary_key=True)

    # Sender
    sender_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id"), nullable=False
    )

    # Message content
    subject: Mapped[str] = mapped_column(String(200), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)

    # Type and priority
    message_type: Mapped[MessageType] = mapped_column(
        SQLEnum(MessageType), default=MessageType.DIRECT, nullable=False
    )
    priority: Mapped[MessagePriority] = mapped_column(
        SQLEnum(MessagePriority), default=MessagePriority.NORMAL, nullable=False
    )

    # Context (optional associations)
    class_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("classes.id")
    )
    lesson_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("lessons.id")
    )
    assessment_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("assessments.id")
    )

    # Thread management
    thread_id: Mapped[Optional[str]] = mapped_column(String(36))  # For message threads
    reply_to_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("messages.id")
    )

    # Attachments
    attachments: Mapped[Optional[list]] = mapped_column(
        JSON, default=[]
    )  # List of attachment URLs/metadata

    # Scheduling
    scheduled_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    sent_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    # Expiration
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    is_expired: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Status
    is_draft: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_deleted_by_sender: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )

    # Relationships
    sender: Mapped["User"] = relationship("User", back_populates="sent_messages")
    recipients: Mapped[List["MessageRecipient"]] = relationship(
        "MessageRecipient", back_populates="message", cascade="all, delete-orphan"
    )
    reply_to: Mapped[Optional["Message"]] = relationship("Message", remote_side=[id])
    class_: Mapped[Optional["Class"]] = relationship("Class")
    lesson: Mapped[Optional["Lesson"]] = relationship("Lesson")
    assessment: Mapped[Optional["Assessment"]] = relationship("Assessment")

    def __repr__(self):
        return f"<Message {self.subject} from {self.sender_id}>"


class MessageRecipient(Base, TimestampMixin):
    """Track message recipients and read status"""

    __tablename__ = "message_recipients"

    # Primary key
    id: Mapped[str] = mapped_column(String(36), primary_key=True)

    # Foreign keys
    message_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("messages.id"), nullable=False
    )
    recipient_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id"), nullable=False
    )

    # Read status
    is_read: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False, index=True
    )
    read_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    # Delivery status
    is_delivered: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    delivered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )

    # User actions
    is_starred: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Folder organization
    folder: Mapped[str] = mapped_column(
        String(50), default="inbox", nullable=False
    )  # "inbox", "sent", "archived", "trash"
    labels: Mapped[Optional[list]] = mapped_column(
        JSON, default=[]
    )  # User-defined labels

    # Notifications
    notification_sent: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    notification_sent_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True)
    )

    # Relationships
    message: Mapped["Message"] = relationship("Message", back_populates="recipients")
    recipient: Mapped["User"] = relationship("User", back_populates="received_messages")

    def __repr__(self):
        return f"<MessageRecipient {self.recipient_id} - {'Read' if self.is_read else 'Unread'}>"
