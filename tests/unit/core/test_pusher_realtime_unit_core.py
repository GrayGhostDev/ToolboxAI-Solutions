import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest_asyncio
"""
Test suite for Pusher Realtime Service
Replaces Socket.IO tests with Pusher equivalents
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from datetime import datetime, timezone

from apps.backend.services.pusher_realtime import (
    PusherRealtimeService,
    get_pusher_service,
    get_pusher_status,
    emit_dashboard_update,
    emit_content_generated,
    emit_quiz_submitted,
    emit_agent_status,
    _check_channel_access,
    _get_required_roles
)
from apps.backend.services.pusher import PusherUnavailable


class TestPusherRealtimeService:
    """Test Pusher Realtime Service functionality"""

    @pytest.fixture
    def mock_pusher_client(self):
        """Create a mock Pusher client"""
        with patch('apps.backend.services.pusher_realtime.get_pusher_client') as mock:
            client = MagicMock()
            client.trigger = MagicMock(return_value={"status": "ok"})
            client.authenticate = MagicMock(return_value={"auth": "test_auth"})
            mock.return_value = client
            yield client

    @pytest.fixture
    def pusher_service(self, mock_pusher_client):
        """Create a Pusher service instance"""
        with patch('apps.backend.services.pusher_realtime.get_pusher_client', return_value=mock_pusher_client):
            service = PusherRealtimeService()
            service.initialized = True
            return service

    @pytest.mark.asyncio
    @pytest.mark.asyncio
async def test_broadcast_event(self, pusher_service):
        """Test broadcasting an event to a channel"""
        with patch('apps.backend.services.pusher_realtime.trigger_event') as mock_trigger:
            mock_trigger.return_value = {"channel": "test-channel", "event": "test-event"}

            result = await pusher_service.broadcast_event(
                "test-channel",
                "test-event",
                {"message": "test"}
            )

            assert result["channel"] == "test-channel"
            assert result["event"] == "test-event"
            mock_trigger.assert_called_once()

    @pytest.mark.asyncio
    @pytest.mark.asyncio
async def test_authenticate_user_private_channel(self, pusher_service):
        """Test authenticating a user for a private channel"""
        with patch('apps.backend.services.pusher_realtime.authenticate_channel') as mock_auth:
            mock_auth.return_value = {"auth": "authenticated"}

            user_data = {
                "id": "user123",
                "role": "teacher",
                "name": "Test User"
            }

            result = await pusher_service.authenticate_user(
                "socket123",
                "private-teacher",
                user_data
            )

            assert result["auth"] == "authenticated"
            mock_auth.assert_called_once()

    @pytest.mark.asyncio
    @pytest.mark.asyncio
async def test_authenticate_user_presence_channel(self, pusher_service):
        """Test authenticating a user for a presence channel"""
        with patch('apps.backend.services.pusher_realtime.authenticate_channel') as mock_auth:
            mock_auth.return_value = {"auth": "authenticated", "channel_data": "user_info"}

            user_data = {
                "id": "user123",
                "role": "admin",
                "name": "Admin User",
                "avatar": "avatar.png"
            }

            result = await pusher_service.authenticate_user(
                "socket123",
                "presence-admin",
                user_data
            )

            assert "auth" in result
            mock_auth.assert_called_once_with(
                socket_id="socket123",
                channel_name="presence-admin",
                user_id="user123",
                user_info={
                    "name": "Admin User",
                    "role": "admin",
                    "avatar": "avatar.png"
                }
            )

    @pytest.mark.asyncio
    @pytest.mark.asyncio
async def test_authenticate_user_rbac_denied(self, pusher_service):
        """Test RBAC denies access to unauthorized channel"""
        user_data = {
            "id": "user123",
            "role": "student",
            "name": "Student User"
        }

        with pytest.raises(PermissionError):
            await pusher_service.authenticate_user(
                "socket123",
                "private-admin",
                user_data
            )

    @pytest.mark.asyncio
    @pytest.mark.asyncio
async def test_send_to_user(self, pusher_service):
        """Test sending event to specific user"""
        with patch.object(pusher_service, 'broadcast_event') as mock_broadcast:
            mock_broadcast.return_value = {"status": "sent"}

            result = await pusher_service.send_to_user(
                "user123",
                "notification",
                {"message": "Hello"}
            )

            assert result["status"] == "sent"
            mock_broadcast.assert_called_once_with(
                "private-user-user123",
                "notification",
                {"message": "Hello"}
            )

    @pytest.mark.asyncio
    @pytest.mark.asyncio
async def test_send_to_role(self, pusher_service):
        """Test sending event to all users with specific role"""
        with patch.object(pusher_service, 'broadcast_event') as mock_broadcast:
            mock_broadcast.return_value = {"status": "sent"}

            result = await pusher_service.send_to_role(
                "teacher",
                "announcement",
                {"message": "Meeting at 3pm"}
            )

            assert result["status"] == "sent"
            mock_broadcast.assert_called_once_with(
                "private-teacher",
                "announcement",
                {"message": "Meeting at 3pm"}
            )

    @pytest.mark.asyncio
    @pytest.mark.asyncio
async def test_handle_presence_member_added(self, pusher_service):
        """Test handling member_added presence event"""
        user_data = {
            "id": "user123",
            "name": "Test User",
            "role": "student"
        }

        await pusher_service.handle_presence_event(
            "presence-classroom",
            "member_added",
            user_data
        )

        assert "user123" in pusher_service.connected_users
        assert pusher_service.connected_users["user123"]["name"] == "Test User"

    @pytest.mark.asyncio
    @pytest.mark.asyncio
async def test_handle_presence_member_removed(self, pusher_service):
        """Test handling member_removed presence event"""
        # First add a user
        pusher_service.connected_users["user123"] = {
            "id": "user123",
            "name": "Test User"
        }

        user_data = {"id": "user123"}

        await pusher_service.handle_presence_event(
            "presence-classroom",
            "member_removed",
            user_data
        )

        assert "user123" not in pusher_service.connected_users

    def test_get_connected_users(self, pusher_service):
        """Test getting list of connected users"""
        pusher_service.connected_users = {
            "user1": {"id": "user1", "name": "User 1"},
            "user2": {"id": "user2", "name": "User 2"}
        }

        users = pusher_service.get_connected_users()
        assert len(users) == 2
        assert users[0]["name"] in ["User 1", "User 2"]

    def test_get_user_channels(self, pusher_service):
        """Test getting channels for a specific user"""
        pusher_service.channel_subscriptions["user123"] = {
            "private-user-user123",
            "presence-classroom",
            "public-dashboard"
        }

        channels = pusher_service.get_user_channels("user123")
        assert len(channels) == 3
        assert "presence-classroom" in channels

    @pytest.mark.asyncio
    @pytest.mark.asyncio
async def test_cleanup_user(self, pusher_service):
        """Test cleaning up user data on disconnect"""
        pusher_service.connected_users["user123"] = {"id": "user123"}
        pusher_service.channel_subscriptions["user123"] = {"channel1", "channel2"}

        await pusher_service.cleanup_user("user123")

        assert "user123" not in pusher_service.connected_users
        assert "user123" not in pusher_service.channel_subscriptions

    def test_get_pusher_status_healthy(self, pusher_service):
        """Test getting Pusher service status when healthy"""
        pusher_service.connected_users = {
            "user1": {"id": "user1", "role": "student"},
            "user2": {"id": "user2", "role": "teacher"}
        }
        pusher_service.channel_subscriptions = {
            "user1": {"channel1"},
            "user2": {"channel2", "channel3"}
        }

        status = get_pusher_status()
        assert status["status"] == "healthy"
        assert status["connected_users"] == 2
        assert status["total_channels"] == 3

    def test_get_pusher_status_unavailable(self):
        """Test getting Pusher service status when unavailable"""
        with patch('apps.backend.services.pusher_realtime._pusher_service', None):
            with patch('apps.backend.services.pusher_realtime.PusherRealtimeService') as mock_service:
                instance = mock_service.return_value
                instance.initialized = False

                status = get_pusher_status()
                assert status["status"] == "unavailable"

    @pytest.mark.asyncio
    @pytest.mark.asyncio
async def test_emit_dashboard_update(self, pusher_service):
        """Test emitting dashboard update event"""
        with patch('apps.backend.services.pusher_realtime.get_pusher_service') as mock_get:
            mock_get.return_value = pusher_service
            with patch.object(pusher_service, 'broadcast_event') as mock_broadcast:
                mock_broadcast.return_value = {"status": "sent"}

                result = await emit_dashboard_update({"update": "data"})

                assert result["status"] == "sent"
                mock_broadcast.assert_called_once_with(
                    "public-dashboard",
                    "dashboard-update",
                    {"update": "data"}
                )

    @pytest.mark.asyncio
    @pytest.mark.asyncio
async def test_emit_content_generated(self, pusher_service):
        """Test emitting content generation completion event"""
        with patch('apps.backend.services.pusher_realtime.get_pusher_service') as mock_get:
            mock_get.return_value = pusher_service
            with patch.object(pusher_service, 'broadcast_event') as mock_broadcast:
                mock_broadcast.return_value = {"status": "sent"}

                result = await emit_content_generated("content123", {"title": "Test"})

                assert result["status"] == "sent"
                mock_broadcast.assert_called_once()
                call_args = mock_broadcast.call_args[0]
                assert call_args[0] == "public-notifications"
                assert call_args[1] == "content-generated"

    @pytest.mark.asyncio
    @pytest.mark.asyncio
async def test_emit_quiz_submitted(self, pusher_service):
        """Test emitting quiz submission event"""
        with patch('apps.backend.services.pusher_realtime.get_pusher_service') as mock_get:
            mock_get.return_value = pusher_service
            with patch.object(pusher_service, 'send_to_role') as mock_role:
                with patch.object(pusher_service, 'send_to_user') as mock_user:
                    mock_role.return_value = {"status": "sent"}
                    mock_user.return_value = {"status": "sent"}

                    await emit_quiz_submitted("quiz123", "student456", 85.5)

                    mock_role.assert_called_once_with(
                        "teacher",
                        "quiz-submitted",
                        {
                            "quiz_id": "quiz123",
                            "student_id": "student456",
                            "score": 85.5
                        }
                    )
                    mock_user.assert_called_once()

    @pytest.mark.asyncio
    @pytest.mark.asyncio
async def test_emit_agent_status(self, pusher_service):
        """Test emitting agent status update"""
        with patch('apps.backend.services.pusher_realtime.get_pusher_service') as mock_get:
            mock_get.return_value = pusher_service
            with patch.object(pusher_service, 'broadcast_event') as mock_broadcast:
                mock_broadcast.return_value = {"status": "sent"}

                result = await emit_agent_status(
                    "ContentAgent",
                    "processing",
                    {"task": "generating content"}
                )

                assert result["status"] == "sent"
                mock_broadcast.assert_called_once()


class TestPusherRBAC:
    """Test RBAC functionality for Pusher channels"""

    def test_check_channel_access_student(self):
        """Test student channel access"""
        assert _check_channel_access("private-student", "student") is True
        assert _check_channel_access("private-teacher", "student") is False
        assert _check_channel_access("private-admin", "student") is False

    def test_check_channel_access_teacher(self):
        """Test teacher channel access"""
        assert _check_channel_access("private-student", "teacher") is True
        assert _check_channel_access("private-teacher", "teacher") is True
        assert _check_channel_access("private-admin", "teacher") is False

    def test_check_channel_access_admin(self):
        """Test admin channel access"""
        assert _check_channel_access("private-student", "admin") is True
        assert _check_channel_access("private-teacher", "admin") is True
        assert _check_channel_access("private-admin", "admin") is True

    def test_get_required_roles_default(self):
        """Test getting default required roles"""
        with patch('apps.backend.core.config.settings', {}):
            roles = _get_required_roles()
            assert roles["admin"] == "admin"
            assert roles["teacher"] == "teacher"
            assert roles["student"] == "student"

    def test_get_required_roles_from_settings(self):
        """Test getting required roles from settings"""
        mock_settings = MagicMock()
        mock_settings.PUSHER_RBAC_REQUIRED_ROLES = {
            "custom": "teacher"
        }
        with patch('apps.backend.services.pusher_realtime.settings', mock_settings):
            roles = _get_required_roles()
            assert roles["custom"] == "teacher"


class TestPusherRateLimit:
    """Test rate limiting for Pusher operations"""

    @pytest.mark.asyncio
    @pytest.mark.asyncio
async def test_authenticate_rate_limit(self):
        """Test rate limiting on authentication"""
        service = PusherRealtimeService()
        service.initialized = True

        # Mock rate limiter to reject
        mock_rate_limiter = AsyncMock()
        mock_rate_limiter.check_rate_limit = AsyncMock(return_value=False)
        service.rate_limiter = mock_rate_limiter

        user_data = {
            "id": "user123",
            "role": "student"
        }

        with pytest.raises(Exception, match="Rate limit exceeded"):
            await service.authenticate_user(
                "socket123",
                "private-student",
                user_data
            )


class TestPusherServiceInitialization:
    """Test Pusher service initialization"""

    def test_service_initialization_success(self):
        """Test successful service initialization"""
        with patch('apps.backend.services.pusher_realtime.get_pusher_client') as mock_client:
            mock_client.return_value = MagicMock()
            service = PusherRealtimeService()
            assert service.initialized is True

    def test_service_initialization_failure(self):
        """Test service initialization failure"""
        with patch('apps.backend.services.pusher_realtime.get_pusher_client') as mock_client:
            mock_client.side_effect = PusherUnavailable("No config")
            service = PusherRealtimeService()
            assert service.initialized is False

    def test_get_pusher_service_singleton(self):
        """Test that get_pusher_service returns singleton"""
        service1 = get_pusher_service()
        service2 = get_pusher_service()
        assert service1 is service2