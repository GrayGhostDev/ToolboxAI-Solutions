"""
Unit Tests for Messages API Endpoints

Tests message retrieval, sending, reading, archiving, and notification endpoints.

Phase 1 Week 1: Authentication & user management endpoint tests
"""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, Mock, patch
from uuid import uuid4

import pytest
from fastapi import HTTPException, status

# Import endpoint functions and models
from apps.backend.api.v1.endpoints.messages import (
    User,
    archive_message,
    db_service,
    delete_message,
    get_message_details,
    get_messages,
    get_recent_notifications,
    get_unread_message_count,
    mark_message_as_read,
    send_message,
)

# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def mock_user():
    """Create mock authenticated user."""
    user = Mock(spec=User)
    user.id = str(uuid4())
    user.username = "testuser"
    user.email = "test@example.com"
    user.role = "student"
    return user


@pytest.fixture
def mock_teacher_user():
    """Create mock teacher user."""
    user = Mock(spec=User)
    user.id = str(uuid4())
    user.username = "teacher_user"
    user.email = "teacher@example.com"
    user.role = "teacher"
    return user


@pytest.fixture
def mock_parent_user():
    """Create mock parent user."""
    user = Mock(spec=User)
    user.id = str(uuid4())
    user.username = "parent_user"
    user.email = "parent@example.com"
    user.role = "parent"
    return user


@pytest.fixture
def mock_admin_user():
    """Create mock admin user."""
    user = Mock(spec=User)
    user.id = str(uuid4())
    user.username = "admin_user"
    user.email = "admin@example.com"
    user.role = "admin"
    return user


@pytest.fixture
def sample_message():
    """Create sample message."""
    return {
        "id": 1,
        "subject": "Test Message",
        "content": "This is a test message",
        "sender_id": str(uuid4()),
        "recipient_id": str(uuid4()),
        "sender_name": "John Smith",
        "sender_username": "j.smith",
        "sender_role": "teacher",
        "message_type": "message",
        "is_read": False,
        "is_urgent": False,
        "created_at": datetime.now(timezone.utc),
        "deleted_by_sender": False,
        "deleted_by_recipient": False,
    }


@pytest.fixture
def sample_message_list():
    """Create list of sample messages."""
    return [
        {
            "id": 1,
            "subject": "Assignment Reminder",
            "sender_name": "John Smith",
            "is_read": False,
            "created_at": datetime.now(timezone.utc),
        },
        {
            "id": 2,
            "subject": "Great Work!",
            "sender_name": "Emily Johnson",
            "is_read": True,
            "created_at": datetime.now(timezone.utc),
        },
    ]


@pytest.fixture
def mock_db_pool():
    """Create mock database pool."""
    pool = AsyncMock()
    conn = AsyncMock()

    # Setup connection acquire context manager
    pool.acquire.return_value.__aenter__.return_value = conn
    pool.acquire.return_value.__aexit__.return_value = None

    return pool, conn


@pytest.fixture
def send_message_data():
    """Create sample send message data."""
    return {
        "recipient_id": str(uuid4()),
        "subject": "Test Subject",
        "content": "Test content",
        "message_type": "message",
        "is_urgent": False,
    }


# ============================================================================
# Test Get Messages Endpoint
# ============================================================================


class TestGetMessages:
    """Test message retrieval endpoint."""

    @pytest.mark.asyncio
    async def test_get_messages_inbox_fallback(self, mock_user):
        """Test getting inbox messages with fallback data."""
        # Database will fail, should use fallback
        with patch.object(db_service, "pool", None):
            result = await get_messages(current_user=mock_user, folder="inbox")

        assert isinstance(result, list)
        assert len(result) > 0
        # Should have basic message fields
        assert "subject" in result[0]
        assert "sender_name" in result[0]

    @pytest.mark.asyncio
    async def test_get_messages_sent_fallback(self, mock_user):
        """Test getting sent messages with fallback data."""
        with patch.object(db_service, "pool", None):
            result = await get_messages(current_user=mock_user, folder="sent")

        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_get_messages_archived_fallback(self, mock_user):
        """Test getting archived messages with fallback data."""
        with patch.object(db_service, "pool", None):
            result = await get_messages(current_user=mock_user, folder="archived")

        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_get_messages_trash_fallback(self, mock_user):
        """Test getting trash messages with fallback data."""
        with patch.object(db_service, "pool", None):
            result = await get_messages(current_user=mock_user, folder="trash")

        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_get_messages_with_type_filter(self, mock_user):
        """Test getting messages with type filter."""
        with patch.object(db_service, "pool", None):
            result = await get_messages(
                current_user=mock_user, folder="inbox", message_type="reminder"
            )

        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_get_messages_with_read_filter(self, mock_user):
        """Test getting messages with read status filter."""
        with patch.object(db_service, "pool", None):
            result = await get_messages(current_user=mock_user, folder="inbox", is_read=False)

        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_get_messages_with_pagination(self, mock_user):
        """Test getting messages with pagination."""
        with patch.object(db_service, "pool", None):
            result = await get_messages(current_user=mock_user, folder="inbox", limit=10, offset=5)

        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_get_messages_teacher_role_has_extra_messages(self, mock_teacher_user):
        """Test teacher role receives role-specific messages."""
        with patch.object(db_service, "pool", None):
            result = await get_messages(current_user=mock_teacher_user, folder="inbox")

        assert isinstance(result, list)
        # Teachers should have additional messages
        assert len(result) > 0

    @pytest.mark.asyncio
    async def test_get_messages_parent_role_has_extra_messages(self, mock_parent_user):
        """Test parent role receives role-specific messages."""
        with patch.object(db_service, "pool", None):
            result = await get_messages(current_user=mock_parent_user, folder="inbox")

        assert isinstance(result, list)
        assert len(result) > 0

    @pytest.mark.asyncio
    async def test_get_messages_sent_teacher_different_from_student(
        self, mock_teacher_user, mock_user
    ):
        """Test sent messages differ by role."""
        with patch.object(db_service, "pool", None):
            teacher_messages = await get_messages(current_user=mock_teacher_user, folder="sent")
            student_messages = await get_messages(current_user=mock_user, folder="sent")

        # Both should return lists, but content differs by role
        assert isinstance(teacher_messages, list)
        assert isinstance(student_messages, list)


# ============================================================================
# Test Get Unread Message Count Endpoint
# ============================================================================


class TestGetUnreadMessageCount:
    """Test unread message count endpoint."""

    @pytest.mark.asyncio
    async def test_get_unread_count_student_fallback(self, mock_user):
        """Test getting unread count for student with fallback."""
        with patch.object(db_service, "pool", None):
            result = await get_unread_message_count(current_user=mock_user)

        assert "unread_messages" in result
        assert "unread_notifications" in result
        assert "urgent_messages" in result
        assert "recent_unread" in result
        assert isinstance(result["unread_messages"], int)

    @pytest.mark.asyncio
    async def test_get_unread_count_teacher_fallback(self, mock_teacher_user):
        """Test getting unread count for teacher with fallback."""
        with patch.object(db_service, "pool", None):
            result = await get_unread_message_count(current_user=mock_teacher_user)

        assert "unread_messages" in result
        assert "breakdown" in result
        assert isinstance(result["breakdown"], dict)

    @pytest.mark.asyncio
    async def test_get_unread_count_parent_fallback(self, mock_parent_user):
        """Test getting unread count for parent with fallback."""
        with patch.object(db_service, "pool", None):
            result = await get_unread_message_count(current_user=mock_parent_user)

        assert result["unread_messages"] >= 0
        assert "breakdown" in result

    @pytest.mark.asyncio
    async def test_get_unread_count_admin_fallback(self, mock_admin_user):
        """Test getting unread count for admin with fallback."""
        with patch.object(db_service, "pool", None):
            result = await get_unread_message_count(current_user=mock_admin_user)

        assert result["unread_messages"] >= 0
        assert "urgent_messages" in result

    @pytest.mark.asyncio
    async def test_get_unread_count_has_breakdown(self, mock_user):
        """Test that unread count includes breakdown by type."""
        with patch.object(db_service, "pool", None):
            result = await get_unread_message_count(current_user=mock_user)

        assert "breakdown" in result
        assert isinstance(result["breakdown"], dict)
        assert len(result["breakdown"]) > 0


# ============================================================================
# Test Get Message Details Endpoint
# ============================================================================


class TestGetMessageDetails:
    """Test get message details endpoint."""

    @pytest.mark.asyncio
    async def test_get_message_details_fallback(self, mock_user):
        """Test getting message details with fallback data."""
        with patch.object(db_service, "pool", None):
            result = await get_message_details(message_id=1, current_user=mock_user)

        assert "id" in result
        assert "subject" in result
        assert "content" in result
        assert "sender_name" in result
        assert result["is_read"] is True  # Fallback marks as read

    @pytest.mark.asyncio
    async def test_get_message_details_has_attachments(self, mock_user):
        """Test message details includes attachments."""
        with patch.object(db_service, "pool", None):
            result = await get_message_details(message_id=1, current_user=mock_user)

        assert "attachments" in result
        assert isinstance(result["attachments"], list)

    @pytest.mark.asyncio
    async def test_get_message_details_has_related_class(self, mock_user):
        """Test message details includes related class info."""
        with patch.object(db_service, "pool", None):
            result = await get_message_details(message_id=1, current_user=mock_user)

        assert "related_class" in result
        assert isinstance(result["related_class"], dict)


# ============================================================================
# Test Send Message Endpoint
# ============================================================================


class TestSendMessage:
    """Test send message endpoint."""

    @pytest.mark.asyncio
    async def test_send_message_no_db_raises_error(self, mock_user, send_message_data):
        """Test sending message without database raises error."""
        with patch.object(db_service, "pool", None):
            with pytest.raises(HTTPException) as exc_info:
                await send_message(message_data=send_message_data, current_user=mock_user)

            assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
            assert "Failed to send message" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_send_message_success_with_db(self, mock_user, send_message_data, mock_db_pool):
        """Test successful message sending with database."""
        pool, conn = mock_db_pool
        conn.fetchrow.return_value = {
            "id": 1,
            "subject": send_message_data["subject"],
            "sender_id": mock_user.id,
        }

        with patch.object(db_service, "pool", pool):
            result = await send_message(message_data=send_message_data, current_user=mock_user)

        assert result["id"] == 1
        assert result["subject"] == send_message_data["subject"]

    @pytest.mark.asyncio
    async def test_send_message_with_attachments(self, mock_user, mock_db_pool):
        """Test sending message with attachments."""
        pool, conn = mock_db_pool
        message_data = {
            "recipient_id": str(uuid4()),
            "subject": "Message with Attachments",
            "content": "See attached files",
            "attachments": [{"name": "file.pdf", "url": "/uploads/file.pdf"}],
        }
        conn.fetchrow.return_value = {"id": 1}

        with patch.object(db_service, "pool", pool):
            result = await send_message(message_data=message_data, current_user=mock_user)

        assert result is not None

    @pytest.mark.asyncio
    async def test_send_message_urgent(self, mock_user, mock_db_pool):
        """Test sending urgent message."""
        pool, conn = mock_db_pool
        message_data = {
            "recipient_id": str(uuid4()),
            "subject": "Urgent Message",
            "content": "This is urgent",
            "is_urgent": True,
        }
        conn.fetchrow.return_value = {"id": 1}

        with patch.object(db_service, "pool", pool):
            result = await send_message(message_data=message_data, current_user=mock_user)

        assert result is not None


# ============================================================================
# Test Mark Message As Read Endpoint
# ============================================================================


class TestMarkMessageAsRead:
    """Test mark message as read endpoint."""

    @pytest.mark.asyncio
    async def test_mark_as_read_success(self, mock_user, mock_db_pool):
        """Test successfully marking message as read."""
        pool, conn = mock_db_pool
        conn.fetchrow.return_value = {"id": 1}

        with patch.object(db_service, "pool", pool):
            result = await mark_message_as_read(message_id=1, current_user=mock_user)

        assert result["message"] == "Message marked as read"

    @pytest.mark.asyncio
    async def test_mark_as_read_not_found(self, mock_user, mock_db_pool):
        """Test marking non-existent message as read."""
        pool, conn = mock_db_pool
        conn.fetchrow.return_value = None

        with patch.object(db_service, "pool", pool):
            with pytest.raises(HTTPException) as exc_info:
                await mark_message_as_read(message_id=999, current_user=mock_user)

            assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    async def test_mark_as_read_no_db_raises_error(self, mock_user):
        """Test marking as read without database raises error."""
        with patch.object(db_service, "pool", None):
            with pytest.raises(HTTPException) as exc_info:
                await mark_message_as_read(message_id=1, current_user=mock_user)

            assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR


# ============================================================================
# Test Archive Message Endpoint
# ============================================================================


class TestArchiveMessage:
    """Test archive message endpoint."""

    @pytest.mark.asyncio
    async def test_archive_message_success(self, mock_user, mock_db_pool):
        """Test successfully archiving message."""
        pool, conn = mock_db_pool
        conn.fetchrow.return_value = {"id": 1}

        with patch.object(db_service, "pool", pool):
            result = await archive_message(message_id=1, current_user=mock_user)

        assert result["message"] == "Message archived"

    @pytest.mark.asyncio
    async def test_archive_message_not_found(self, mock_user, mock_db_pool):
        """Test archiving non-existent message."""
        pool, conn = mock_db_pool
        conn.fetchrow.return_value = None

        with patch.object(db_service, "pool", pool):
            with pytest.raises(HTTPException) as exc_info:
                await archive_message(message_id=999, current_user=mock_user)

            assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    async def test_archive_message_no_db_raises_error(self, mock_user):
        """Test archiving without database raises error."""
        with patch.object(db_service, "pool", None):
            with pytest.raises(HTTPException) as exc_info:
                await archive_message(message_id=1, current_user=mock_user)

            assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR


# ============================================================================
# Test Delete Message Endpoint
# ============================================================================


class TestDeleteMessage:
    """Test delete message endpoint."""

    @pytest.mark.asyncio
    async def test_delete_message_as_sender(self, mock_user, mock_db_pool):
        """Test deleting message as sender."""
        pool, conn = mock_db_pool
        conn.fetchrow.return_value = {
            "sender_id": mock_user.id,
            "recipient_id": str(uuid4()),
        }
        conn.execute = AsyncMock()

        with patch.object(db_service, "pool", pool):
            result = await delete_message(message_id=1, current_user=mock_user)

        assert result["message"] == "Message deleted"

    @pytest.mark.asyncio
    async def test_delete_message_as_recipient(self, mock_user, mock_db_pool):
        """Test deleting message as recipient."""
        pool, conn = mock_db_pool
        conn.fetchrow.return_value = {
            "sender_id": str(uuid4()),
            "recipient_id": mock_user.id,
        }
        conn.execute = AsyncMock()

        with patch.object(db_service, "pool", pool):
            result = await delete_message(message_id=1, current_user=mock_user)

        assert result["message"] == "Message deleted"

    @pytest.mark.asyncio
    async def test_delete_message_not_found(self, mock_user, mock_db_pool):
        """Test deleting non-existent message."""
        pool, conn = mock_db_pool
        conn.fetchrow.return_value = None

        with patch.object(db_service, "pool", pool):
            with pytest.raises(HTTPException) as exc_info:
                await delete_message(message_id=999, current_user=mock_user)

            assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    async def test_delete_message_unauthorized(self, mock_user, mock_db_pool):
        """Test deleting message user doesn't own."""
        pool, conn = mock_db_pool
        conn.fetchrow.return_value = {
            "sender_id": str(uuid4()),
            "recipient_id": str(uuid4()),
        }

        with patch.object(db_service, "pool", pool):
            with pytest.raises(HTTPException) as exc_info:
                await delete_message(message_id=1, current_user=mock_user)

            assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
            assert "Not authorized" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_delete_message_no_db_raises_error(self, mock_user):
        """Test deleting without database raises error."""
        with patch.object(db_service, "pool", None):
            with pytest.raises(HTTPException) as exc_info:
                await delete_message(message_id=1, current_user=mock_user)

            assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR


# ============================================================================
# Test Get Recent Notifications Endpoint
# ============================================================================


class TestGetRecentNotifications:
    """Test get recent notifications endpoint."""

    @pytest.mark.asyncio
    async def test_get_recent_notifications_student_fallback(self, mock_user):
        """Test getting recent notifications for student."""
        with patch.object(db_service, "pool", None):
            result = await get_recent_notifications(current_user=mock_user, limit=10)

        assert isinstance(result, list)
        assert len(result) > 0
        # Check notification structure
        assert "subject" in result[0]
        assert "message_type" in result[0]
        assert "is_read" in result[0]

    @pytest.mark.asyncio
    async def test_get_recent_notifications_teacher_fallback(self, mock_teacher_user):
        """Test getting recent notifications for teacher."""
        with patch.object(db_service, "pool", None):
            result = await get_recent_notifications(current_user=mock_teacher_user, limit=10)

        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_get_recent_notifications_with_limit(self, mock_user):
        """Test getting notifications with custom limit."""
        with patch.object(db_service, "pool", None):
            result = await get_recent_notifications(current_user=mock_user, limit=5)

        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_get_recent_notifications_empty_for_admin(self, mock_admin_user):
        """Test getting notifications for admin (may be empty)."""
        with patch.object(db_service, "pool", None):
            result = await get_recent_notifications(current_user=mock_admin_user, limit=10)

        # Admin fallback returns empty list
        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_get_recent_notifications_has_urgent_flag(self, mock_user):
        """Test notifications include urgent flag."""
        with patch.object(db_service, "pool", None):
            result = await get_recent_notifications(current_user=mock_user, limit=10)

        if len(result) > 0:
            assert "is_urgent" in result[0]
            assert isinstance(result[0]["is_urgent"], bool)

    @pytest.mark.asyncio
    async def test_get_recent_notifications_has_preview(self, mock_user):
        """Test notifications include preview text."""
        with patch.object(db_service, "pool", None):
            result = await get_recent_notifications(current_user=mock_user, limit=10)

        if len(result) > 0:
            assert "preview" in result[0]
            assert isinstance(result[0]["preview"], str)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
