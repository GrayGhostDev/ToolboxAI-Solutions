"""
Unit Tests for User Notifications Endpoints

Tests notification list, creation, reading, archiving, and statistics endpoints.

Phase 1 Week 1: Authentication & user management endpoint tests
"""

import pytest
from datetime import datetime
from uuid import uuid4, UUID
from unittest.mock import AsyncMock, Mock, patch

from fastapi import HTTPException, status

# Import endpoint functions and models
from apps.backend.api.v1.endpoints.user_notifications import (
    list_notifications,
    get_notification,
    create_notification,
    create_bulk_notifications,
    mark_as_read,
    mark_multiple_as_read,
    mark_all_as_read,
    delete_notification,
    archive_notifications,
    get_notification_stats,
    clear_old_notifications,
    Notification,
    NotificationListResponse,
    CreateNotificationRequest,
    BulkNotificationRequest,
    MarkAsReadRequest,
    NotificationStats,
    NotificationType,
    NotificationPriority,
    NotificationChannel,
    NotificationStatus,
)

from apps.backend.models.schemas import User


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def mock_user():
    """Create mock authenticated user."""
    user = Mock(spec=User)
    user.id = uuid4()
    user.username = "testuser"
    user.email = "test@example.com"
    user.role = "teacher"
    return user


@pytest.fixture
def mock_session():
    """Create mock async database session."""
    session = AsyncMock()
    return session


@pytest.fixture
def sample_notification():
    """Create sample notification."""
    return Notification(
        id=uuid4(),
        user_id=uuid4(),
        type=NotificationType.INFO,
        priority=NotificationPriority.NORMAL,
        title="Test Notification",
        message="This is a test notification",
        data={},
        actions=[],
        channels=[NotificationChannel.IN_APP],
        status=NotificationStatus.UNREAD,
        created_at=datetime.utcnow(),
    )


@pytest.fixture
def create_notification_request():
    """Create notification request data."""
    return CreateNotificationRequest(
        user_id=uuid4(),
        type=NotificationType.SUCCESS,
        priority=NotificationPriority.HIGH,
        title="Assignment Completed",
        message="Your assignment has been graded",
        data={"assignment_id": "123", "grade": "A"},
        channels=[NotificationChannel.IN_APP, NotificationChannel.EMAIL],
    )


# ============================================================================
# Test List Notifications Endpoint
# ============================================================================


class TestListNotifications:
    """Test notification listing endpoint."""

    @pytest.mark.asyncio
    async def test_list_notifications_success(self, mock_session, mock_user):
        """Test successful notification retrieval."""
        result = await list_notifications(
            session=mock_session, current_user=mock_user, status_filter=None,
            type_filter=None, priority_filter=None, limit=50, offset=0
        )

        assert isinstance(result, NotificationListResponse)
        assert result.total == 0
        assert result.unread_count == 0
        assert isinstance(result.notifications, list)

    @pytest.mark.asyncio
    async def test_list_notifications_with_filters(self, mock_session, mock_user):
        """Test notification listing with filters."""
        result = await list_notifications(
            session=mock_session,
            current_user=mock_user,
            status_filter=NotificationStatus.UNREAD,
            type_filter=NotificationType.INFO,
            priority_filter=NotificationPriority.HIGH,
            limit=25,
            offset=0,
        )

        assert isinstance(result, NotificationListResponse)

    @pytest.mark.asyncio
    async def test_list_notifications_with_pagination(self, mock_session, mock_user):
        """Test notification listing with pagination."""
        result = await list_notifications(
            session=mock_session, current_user=mock_user, status_filter=None,
            type_filter=None, priority_filter=None, limit=10, offset=20
        )

        assert isinstance(result, NotificationListResponse)

    @pytest.mark.asyncio
    async def test_list_notifications_max_limit(self, mock_session, mock_user):
        """Test that limit parameter respects maximum."""
        # This would normally be validated by FastAPI Query
        result = await list_notifications(
            session=mock_session, current_user=mock_user, status_filter=None,
            type_filter=None, priority_filter=None, limit=100, offset=0
        )

        assert isinstance(result, NotificationListResponse)


# ============================================================================
# Test Get Notification Endpoint
# ============================================================================


class TestGetNotification:
    """Test get notification endpoint."""

    @pytest.mark.asyncio
    async def test_get_notification_not_found(self, mock_session, mock_user):
        """Test get notification when not found."""
        notification_id = uuid4()

        with pytest.raises(HTTPException) as exc_info:
            await get_notification(
                notification_id=notification_id,
                session=mock_session,
                current_user=mock_user,
            )

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND


# ============================================================================
# Test Create Notification Endpoint
# ============================================================================


class TestCreateNotification:
    """Test notification creation endpoint."""

    @pytest.mark.asyncio
    async def test_create_notification_success(
        self, mock_session, mock_user, create_notification_request
    ):
        """Test successful notification creation."""
        result = await create_notification(
            request=create_notification_request,
            session=mock_session,
            current_user=mock_user,
        )

        assert isinstance(result, Notification)
        assert result.title == "Assignment Completed"
        assert result.message == "Your assignment has been graded"
        assert result.type == NotificationType.SUCCESS
        assert result.priority == NotificationPriority.HIGH
        assert result.status == NotificationStatus.UNREAD
        assert NotificationChannel.IN_APP in result.channels
        assert NotificationChannel.EMAIL in result.channels

    @pytest.mark.asyncio
    async def test_create_notification_with_actions(self, mock_session, mock_user):
        """Test notification creation with actions."""
        from apps.backend.api.v1.endpoints.user_notifications import NotificationAction

        request = CreateNotificationRequest(
            user_id=uuid4(),
            type=NotificationType.REMINDER,
            priority=NotificationPriority.HIGH,
            title="Meeting Reminder",
            message="Your meeting starts in 10 minutes",
            actions=[
                NotificationAction(
                    label="Join Now",
                    action_type="navigate",
                    url="/meetings/123",
                    data={"meeting_id": "123"},
                )
            ],
            channels=[NotificationChannel.IN_APP, NotificationChannel.PUSH],
        )

        result = await create_notification(
            request=request, session=mock_session, current_user=mock_user
        )

        assert len(result.actions) == 1
        assert result.actions[0].label == "Join Now"

    @pytest.mark.asyncio
    async def test_create_notification_with_icon_and_image(self, mock_session, mock_user):
        """Test notification creation with icon and image."""
        request = CreateNotificationRequest(
            user_id=uuid4(),
            type=NotificationType.SUCCESS,
            priority=NotificationPriority.NORMAL,
            title="Achievement Unlocked",
            message="You've completed 10 lessons!",
            icon="trophy",
            image_url="https://example.com/achievement.png",
            channels=[NotificationChannel.IN_APP],
        )

        result = await create_notification(
            request=request, session=mock_session, current_user=mock_user
        )

        assert result.icon == "trophy"
        assert result.image_url == "https://example.com/achievement.png"


# ============================================================================
# Test Create Bulk Notifications Endpoint
# ============================================================================


class TestCreateBulkNotifications:
    """Test bulk notification creation endpoint."""

    @pytest.mark.asyncio
    async def test_create_bulk_notifications_success(self, mock_session, mock_user):
        """Test successful bulk notification creation."""
        user_ids = [uuid4() for _ in range(5)]
        request = BulkNotificationRequest(
            user_ids=user_ids,
            type=NotificationType.ALERT,
            priority=NotificationPriority.URGENT,
            title="System Maintenance",
            message="System will be down for maintenance",
            channels=[NotificationChannel.EMAIL, NotificationChannel.SMS],
        )

        result = await create_bulk_notifications(
            request=request, session=mock_session, current_user=mock_user
        )

        assert "queued" in result
        assert result["queued"] == 5

    @pytest.mark.asyncio
    async def test_create_bulk_notifications_large_batch(self, mock_session, mock_user):
        """Test bulk notification with maximum users."""
        user_ids = [uuid4() for _ in range(100)]
        request = BulkNotificationRequest(
            user_ids=user_ids,
            type=NotificationType.INFO,
            priority=NotificationPriority.NORMAL,
            title="Newsletter",
            message="Check out this month's newsletter",
            channels=[NotificationChannel.EMAIL],
        )

        result = await create_bulk_notifications(
            request=request, session=mock_session, current_user=mock_user
        )

        assert result["queued"] == 100


# ============================================================================
# Test Mark As Read Endpoints
# ============================================================================


class TestMarkAsRead:
    """Test mark notification as read endpoints."""

    @pytest.mark.asyncio
    async def test_mark_single_as_read_not_found(self, mock_session, mock_user):
        """Test marking non-existent notification as read."""
        notification_id = uuid4()

        with pytest.raises(HTTPException) as exc_info:
            await mark_as_read(
                notification_id=notification_id,
                session=mock_session,
                current_user=mock_user,
            )

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    async def test_mark_multiple_as_read_success(self, mock_session, mock_user):
        """Test marking multiple notifications as read."""
        notification_ids = [uuid4() for _ in range(3)]
        request = MarkAsReadRequest(notification_ids=notification_ids)

        result = await mark_multiple_as_read(
            request=request, session=mock_session, current_user=mock_user
        )

        assert result["count"] == 3
        assert "marked" in result["message"].lower()

    @pytest.mark.asyncio
    async def test_mark_all_as_read_success(self, mock_session, mock_user):
        """Test marking all notifications as read."""
        result = await mark_all_as_read(session=mock_session, current_user=mock_user)

        assert "message" in result
        assert "count" in result
        assert result["count"] == 0  # TODO implementation will change this


# ============================================================================
# Test Delete Notification Endpoint
# ============================================================================


class TestDeleteNotification:
    """Test notification deletion endpoint."""

    @pytest.mark.asyncio
    async def test_delete_notification_success(self, mock_session, mock_user):
        """Test successful notification deletion."""
        notification_id = uuid4()

        # Should not raise exception
        result = await delete_notification(
            notification_id=notification_id,
            session=mock_session,
            current_user=mock_user,
        )

        assert result is None


# ============================================================================
# Test Archive Notifications Endpoint
# ============================================================================


class TestArchiveNotifications:
    """Test notification archiving endpoint."""

    @pytest.mark.asyncio
    async def test_archive_notifications_success(self, mock_session, mock_user):
        """Test successful notification archiving."""
        notification_ids = [uuid4() for _ in range(5)]
        request = MarkAsReadRequest(notification_ids=notification_ids)

        result = await archive_notifications(
            request=request, session=mock_session, current_user=mock_user
        )

        assert result["count"] == 5
        assert "archived" in result["message"].lower()

    @pytest.mark.asyncio
    async def test_archive_single_notification(self, mock_session, mock_user):
        """Test archiving single notification."""
        notification_ids = [uuid4()]
        request = MarkAsReadRequest(notification_ids=notification_ids)

        result = await archive_notifications(
            request=request, session=mock_session, current_user=mock_user
        )

        assert result["count"] == 1


# ============================================================================
# Test Get Notification Stats Endpoint
# ============================================================================


class TestGetNotificationStats:
    """Test notification statistics endpoint."""

    @pytest.mark.asyncio
    async def test_get_notification_stats_success(self, mock_session, mock_user):
        """Test successful stats retrieval."""
        result = await get_notification_stats(
            session=mock_session, current_user=mock_user
        )

        assert isinstance(result, NotificationStats)
        assert result.total_count == 0
        assert result.unread_count == 0
        assert result.read_count == 0
        assert result.archived_count == 0
        assert isinstance(result.by_type, dict)
        assert isinstance(result.by_priority, dict)

    @pytest.mark.asyncio
    async def test_get_notification_stats_structure(self, mock_session, mock_user):
        """Test notification stats response structure."""
        result = await get_notification_stats(
            session=mock_session, current_user=mock_user
        )

        # Verify all required fields
        assert hasattr(result, "total_count")
        assert hasattr(result, "unread_count")
        assert hasattr(result, "read_count")
        assert hasattr(result, "archived_count")
        assert hasattr(result, "by_type")
        assert hasattr(result, "by_priority")


# ============================================================================
# Test Clear Old Notifications Endpoint
# ============================================================================


class TestClearOldNotifications:
    """Test clearing old notifications endpoint."""

    @pytest.mark.asyncio
    async def test_clear_old_notifications_default_days(self, mock_session, mock_user):
        """Test clearing notifications with default 30 days."""
        result = await clear_old_notifications(
            older_than_days=30, session=mock_session, current_user=mock_user
        )

        assert "message" in result
        assert "30 days" in result["message"]
        assert result["count"] == 0

    @pytest.mark.asyncio
    async def test_clear_old_notifications_custom_days(self, mock_session, mock_user):
        """Test clearing notifications with custom days."""
        result = await clear_old_notifications(
            older_than_days=90, session=mock_session, current_user=mock_user
        )

        assert "90 days" in result["message"]

    @pytest.mark.asyncio
    async def test_clear_old_notifications_minimum_days(self, mock_session, mock_user):
        """Test clearing notifications with minimum days (1)."""
        result = await clear_old_notifications(
            older_than_days=1, session=mock_session, current_user=mock_user
        )

        assert "1 days" in result["message"]

    @pytest.mark.asyncio
    async def test_clear_old_notifications_maximum_days(self, mock_session, mock_user):
        """Test clearing notifications with maximum days (365)."""
        result = await clear_old_notifications(
            older_than_days=365, session=mock_session, current_user=mock_user
        )

        assert "365 days" in result["message"]


# ============================================================================
# Test Notification Models
# ============================================================================


class TestNotificationModels:
    """Test notification model validations."""

    def test_notification_type_enum(self):
        """Test notification type enum values."""
        assert NotificationType.INFO == "info"
        assert NotificationType.SUCCESS == "success"
        assert NotificationType.WARNING == "warning"
        assert NotificationType.ERROR == "error"
        assert NotificationType.REMINDER == "reminder"
        assert NotificationType.ALERT == "alert"

    def test_notification_priority_enum(self):
        """Test notification priority enum values."""
        assert NotificationPriority.LOW == "low"
        assert NotificationPriority.NORMAL == "normal"
        assert NotificationPriority.HIGH == "high"
        assert NotificationPriority.URGENT == "urgent"

    def test_notification_channel_enum(self):
        """Test notification channel enum values."""
        assert NotificationChannel.IN_APP == "in_app"
        assert NotificationChannel.EMAIL == "email"
        assert NotificationChannel.PUSH == "push"
        assert NotificationChannel.SMS == "sms"

    def test_notification_status_enum(self):
        """Test notification status enum values."""
        assert NotificationStatus.UNREAD == "unread"
        assert NotificationStatus.READ == "read"
        assert NotificationStatus.ARCHIVED == "archived"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
