"""
Unit tests for the Pusher and Realtime Communication API Router.

Tests cover Pusher channel authentication, webhook handling, event triggering,
statistics retrieval, and permission validation with comprehensive mocking.
"""

import json
from unittest.mock import Mock, patch
from uuid import uuid4

import pytest
from fastapi import status


# Sample test data
@pytest.fixture
def sample_pusher_auth_request_form():
    """Sample Pusher auth request (form-urlencoded)"""
    return {"channel_name": "private-user-abc123", "socket_id": "123456.789012"}


@pytest.fixture
def sample_pusher_auth_request_json():
    """Sample Pusher auth request (JSON)"""
    return {"channel_name": "presence-classroom-101", "socket_id": "654321.210987"}


@pytest.fixture
def sample_webhook_payload():
    """Sample Pusher webhook payload"""
    return {
        "time_ms": 1234567890,
        "events": [
            {"name": "channel_occupied", "channel": "private-classroom-101", "data": {}},
            {
                "name": "member_added",
                "channel": "presence-classroom-101",
                "data": {"user_id": "user_123"},
            },
        ],
    }


@pytest.fixture
def sample_trigger_event_request():
    """Sample realtime event trigger request"""
    return {
        "channel": "private-teacher",
        "event": "content-updated",
        "data": {"content_id": "content_123", "status": "completed"},
    }


@pytest.fixture
def mock_current_user():
    """Mock authenticated user"""
    user = Mock()
    user.id = str(uuid4())
    user.name = "Test User"
    user.role = "teacher"
    return user


@pytest.fixture
def mock_admin_user():
    """Mock admin user"""
    user = Mock()
    user.id = str(uuid4())
    user.name = "Admin User"
    user.role = "admin"
    return user


@pytest.fixture
def mock_student_user():
    """Mock student user"""
    user = Mock()
    user.id = str(uuid4())
    user.name = "Student User"
    user.role = "student"
    return user


@pytest.mark.unit
class TestPusherAuthentication:
    """Tests for Pusher channel authentication endpoint"""

    @pytest.mark.asyncio
    async def test_authenticate_channel_json_success(
        self, test_client, sample_pusher_auth_request_json, mock_current_user
    ):
        """Test successful channel authentication with JSON request"""
        mock_auth_response = {
            "auth": "test_auth_signature:abc123",
            "channel_data": json.dumps(
                {
                    "user_id": mock_current_user.id,
                    "user_info": {
                        "id": mock_current_user.id,
                        "name": "Test User",
                        "role": "teacher",
                    },
                }
            ),
        }

        with patch(
            "apps.backend.api.routers.pusher.get_current_user", return_value=mock_current_user
        ):
            with patch("apps.backend.api.routers.pusher._can_access_channel", return_value=True):
                with patch(
                    "apps.backend.api.routers.pusher.pusher_authenticate",
                    return_value=mock_auth_response,
                ):
                    response = test_client.post(
                        "/pusher/auth",
                        json=sample_pusher_auth_request_json,
                        headers={"content-type": "application/json"},
                    )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "auth" in data
        assert data["auth"] == "test_auth_signature:abc123"

    def test_authenticate_channel_missing_channel_name(self, test_client, mock_current_user):
        """Test authentication with missing channel_name"""
        invalid_request = {
            "socket_id": "123456.789012"
            # Missing channel_name
        }

        with patch(
            "apps.backend.api.routers.pusher.get_current_user", return_value=mock_current_user
        ):
            response = test_client.post("/pusher/auth", json=invalid_request)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "channel_name" in response.json()["detail"].lower()

    def test_authenticate_channel_missing_socket_id(self, test_client, mock_current_user):
        """Test authentication with missing socket_id"""
        invalid_request = {
            "channel_name": "private-test"
            # Missing socket_id
        }

        with patch(
            "apps.backend.api.routers.pusher.get_current_user", return_value=mock_current_user
        ):
            response = test_client.post("/pusher/auth", json=invalid_request)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "socket_id" in response.json()["detail"].lower()

    def test_authenticate_channel_forbidden(
        self, test_client, sample_pusher_auth_request_json, mock_current_user
    ):
        """Test authentication when user lacks channel permissions"""
        with patch(
            "apps.backend.api.routers.pusher.get_current_user", return_value=mock_current_user
        ):
            with patch("apps.backend.api.routers.pusher._can_access_channel", return_value=False):
                response = test_client.post("/pusher/auth", json=sample_pusher_auth_request_json)

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "insufficient permissions" in response.json()["detail"].lower()

    def test_authenticate_channel_service_failure(
        self, test_client, sample_pusher_auth_request_json, mock_current_user
    ):
        """Test authentication when Pusher service fails"""
        with patch(
            "apps.backend.api.routers.pusher.get_current_user", return_value=mock_current_user
        ):
            with patch("apps.backend.api.routers.pusher._can_access_channel", return_value=True):
                with patch(
                    "apps.backend.api.routers.pusher.pusher_authenticate",
                    side_effect=Exception("Pusher unavailable"),
                ):
                    response = test_client.post(
                        "/pusher/auth", json=sample_pusher_auth_request_json
                    )

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR


@pytest.mark.unit
class TestPusherWebhook:
    """Tests for Pusher webhook handling endpoint"""

    @pytest.mark.asyncio
    async def test_handle_webhook_success(self, test_client, sample_webhook_payload):
        """Test successful webhook processing"""
        with patch("apps.backend.api.routers.pusher.pusher_verify_webhook", return_value=True):
            response = test_client.post(
                "/pusher/webhook",
                json=sample_webhook_payload,
                headers={"X-Pusher-Key": "test_key", "X-Pusher-Signature": "test_signature"},
            )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "success"
        assert data["data"]["events_processed"] == 2

    @pytest.mark.asyncio
    async def test_handle_webhook_invalid_signature(self, test_client, sample_webhook_payload):
        """Test webhook with invalid signature"""
        with patch("apps.backend.api.routers.pusher.pusher_verify_webhook", return_value=False):
            response = test_client.post(
                "/pusher/webhook",
                json=sample_webhook_payload,
                headers={"X-Pusher-Key": "test_key", "X-Pusher-Signature": "invalid_signature"},
            )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "invalid webhook signature" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_handle_webhook_empty_events(self, test_client):
        """Test webhook with no events"""
        empty_payload = {"time_ms": 1234567890, "events": []}

        with patch("apps.backend.api.routers.pusher.pusher_verify_webhook", return_value=True):
            response = test_client.post(
                "/pusher/webhook",
                json=empty_payload,
                headers={"X-Pusher-Key": "test_key", "X-Pusher-Signature": "test_signature"},
            )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["data"]["events_processed"] == 0

    @pytest.mark.asyncio
    async def test_handle_webhook_partial_failure(self, test_client):
        """Test webhook with some events failing"""
        payload = {
            "time_ms": 1234567890,
            "events": [
                {"name": "channel_occupied", "channel": "test-channel", "data": {}},
                {"name": "invalid_event", "channel": "test-channel", "data": {}},
            ],
        }

        with patch("apps.backend.api.routers.pusher.pusher_verify_webhook", return_value=True):
            with patch(
                "apps.backend.api.routers.pusher._process_webhook_event",
                side_effect=[{"action": "success"}, Exception("Processing error")],
            ):
                response = test_client.post(
                    "/pusher/webhook",
                    json=payload,
                    headers={"X-Pusher-Key": "test_key", "X-Pusher-Signature": "test_signature"},
                )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["data"]["events_processed"] == 2
        # Check results array has both success and failure
        results = data["data"]["results"]
        assert any(r["status"] == "processed" for r in results)
        assert any(r["status"] == "failed" for r in results)


@pytest.mark.unit
class TestRealtimeEventTriggering:
    """Tests for realtime event triggering endpoint"""

    def test_trigger_event_success(
        self, test_client, sample_trigger_event_request, mock_current_user
    ):
        """Test successful event triggering"""
        mock_result = {"channels": {"private-teacher": {}}}

        with patch(
            "apps.backend.api.routers.pusher.get_current_user", return_value=mock_current_user
        ):
            with patch("apps.backend.api.routers.pusher._can_trigger_event", return_value=True):
                with patch(
                    "apps.backend.api.routers.pusher.pusher_trigger_event", return_value=mock_result
                ):
                    response = test_client.post(
                        "/realtime/trigger", json=sample_trigger_event_request
                    )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "success"
        assert data["data"]["triggered"] is True
        assert data["data"]["channel"] == "private-teacher"
        assert data["data"]["event"] == "content-updated"

    def test_trigger_event_missing_channel(self, test_client, mock_current_user):
        """Test event triggering with missing channel"""
        invalid_request = {
            "event": "test-event",
            "data": {},
            # Missing channel
        }

        with patch(
            "apps.backend.api.routers.pusher.get_current_user", return_value=mock_current_user
        ):
            response = test_client.post("/realtime/trigger", json=invalid_request)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "channel" in response.json()["detail"].lower()

    def test_trigger_event_missing_event_name(self, test_client, mock_current_user):
        """Test event triggering with missing event name"""
        invalid_request = {
            "channel": "test-channel",
            "data": {},
            # Missing event
        }

        with patch(
            "apps.backend.api.routers.pusher.get_current_user", return_value=mock_current_user
        ):
            response = test_client.post("/realtime/trigger", json=invalid_request)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "event" in response.json()["detail"].lower()

    def test_trigger_event_forbidden(
        self, test_client, sample_trigger_event_request, mock_current_user
    ):
        """Test event triggering without permissions"""
        with patch(
            "apps.backend.api.routers.pusher.get_current_user", return_value=mock_current_user
        ):
            with patch("apps.backend.api.routers.pusher._can_trigger_event", return_value=False):
                response = test_client.post("/realtime/trigger", json=sample_trigger_event_request)

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_trigger_event_service_failure(
        self, test_client, sample_trigger_event_request, mock_current_user
    ):
        """Test event triggering when Pusher service fails"""
        with patch(
            "apps.backend.api.routers.pusher.get_current_user", return_value=mock_current_user
        ):
            with patch("apps.backend.api.routers.pusher._can_trigger_event", return_value=True):
                with patch(
                    "apps.backend.api.routers.pusher.pusher_trigger_event",
                    side_effect=Exception("Pusher API error"),
                ):
                    response = test_client.post(
                        "/realtime/trigger", json=sample_trigger_event_request
                    )

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR


@pytest.mark.unit
class TestPusherStatistics:
    """Tests for Pusher statistics endpoint"""

    def test_get_stats_success_admin(self, test_client, mock_admin_user):
        """Test successful stats retrieval by admin"""
        mock_stats = {
            "connected_clients": 42,
            "channels": 15,
            "uptime": 3600,
            "messages_sent": 1000,
        }

        with patch(
            "apps.backend.api.routers.pusher.get_current_user", return_value=mock_admin_user
        ):
            with patch("apps.backend.api.routers.pusher._user_has_role", return_value=True):
                with patch(
                    "apps.backend.api.routers.pusher.get_pusher_status", return_value=mock_stats
                ):
                    response = test_client.get("/pusher/stats")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "success"
        assert data["data"]["connected_clients"] == 42

    def test_get_stats_forbidden_non_admin(self, test_client, mock_current_user):
        """Test stats retrieval forbidden for non-admin"""
        with patch(
            "apps.backend.api.routers.pusher.get_current_user", return_value=mock_current_user
        ):
            with patch("apps.backend.api.routers.pusher._user_has_role", return_value=False):
                response = test_client.get("/pusher/stats")

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "admin" in response.json()["detail"].lower()

    def test_get_stats_service_failure(self, test_client, mock_admin_user):
        """Test stats retrieval when service fails"""
        with patch(
            "apps.backend.api.routers.pusher.get_current_user", return_value=mock_admin_user
        ):
            with patch("apps.backend.api.routers.pusher._user_has_role", return_value=True):
                with patch(
                    "apps.backend.api.routers.pusher.get_pusher_status",
                    side_effect=Exception("Stats unavailable"),
                ):
                    response = test_client.get("/pusher/stats")

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR


@pytest.mark.unit
class TestPermissionHelpers:
    """Tests for permission helper functions"""

    def test_can_access_public_channel(self, mock_current_user):
        """Test access to public channels"""
        from apps.backend.api.routers.pusher import _can_access_channel

        result = _can_access_channel(mock_current_user, "public-announcements")
        assert result is True

    def test_can_access_private_channel_admin(self, mock_admin_user):
        """Test admin access to any private channel"""
        from apps.backend.api.routers.pusher import _can_access_channel

        result = _can_access_channel(mock_admin_user, "private-admin-only")
        assert result is True

    def test_can_access_own_private_channel(self, mock_current_user):
        """Test access to user's own private channel"""
        from apps.backend.api.routers.pusher import _can_access_channel

        channel_name = f"private-user-{mock_current_user.id}"
        result = _can_access_channel(mock_current_user, channel_name)
        assert result is True

    def test_can_access_role_channel(self, mock_current_user):
        """Test access to role-based channel"""
        from apps.backend.api.routers.pusher import _can_access_channel

        result = _can_access_channel(mock_current_user, "private-teacher")
        assert result is True

    def test_can_access_student_channel_as_teacher(self, mock_current_user):
        """Test teacher access to student channels"""
        from apps.backend.api.routers.pusher import _can_access_channel

        result = _can_access_channel(mock_current_user, "private-student-abc123")
        assert result is True

    def test_cannot_access_unauthorized_private_channel(self, mock_student_user):
        """Test student cannot access unauthorized private channel"""
        from apps.backend.api.routers.pusher import _can_access_channel

        result = _can_access_channel(mock_student_user, "private-admin-only")
        assert result is False

    def test_can_trigger_event_admin(self, mock_admin_user):
        """Test admin can trigger any event"""
        from apps.backend.api.routers.pusher import _can_trigger_event

        result = _can_trigger_event(mock_admin_user, "any-channel", "any-event")
        assert result is True

    def test_can_trigger_educational_event_teacher(self, mock_current_user):
        """Test teacher can trigger educational events"""
        from apps.backend.api.routers.pusher import _can_trigger_event

        result = _can_trigger_event(mock_current_user, "private-classroom", "content-updated")
        assert result is True

    def test_can_trigger_event_own_channel(self, mock_student_user):
        """Test user can trigger events on own channel"""
        from apps.backend.api.routers.pusher import _can_trigger_event

        channel = f"private-user-{mock_student_user.id}"
        result = _can_trigger_event(mock_student_user, channel, "any-event")
        assert result is True

    def test_cannot_trigger_unauthorized_event(self, mock_student_user):
        """Test student cannot trigger unauthorized events"""
        from apps.backend.api.routers.pusher import _can_trigger_event

        result = _can_trigger_event(mock_student_user, "private-admin", "admin-event")
        assert result is False

    def test_user_has_role_match(self, mock_current_user):
        """Test user has matching role"""
        from apps.backend.api.routers.pusher import _user_has_role

        result = _user_has_role(mock_current_user, ["admin", "teacher"])
        assert result is True

    def test_user_has_role_no_match(self, mock_current_user):
        """Test user role does not match"""
        from apps.backend.api.routers.pusher import _user_has_role

        result = _user_has_role(mock_current_user, ["admin", "student"])
        assert result is False

    def test_user_has_role_no_role_attribute(self):
        """Test user without role attribute"""
        from apps.backend.api.routers.pusher import _user_has_role

        user_no_role = Mock(spec=[])
        result = _user_has_role(user_no_role, ["admin"])
        assert result is False


@pytest.mark.unit
class TestWebhookEventProcessing:
    """Tests for webhook event processing function"""

    @pytest.mark.asyncio
    async def test_process_channel_occupied_event(self):
        """Test processing channel_occupied event"""
        from apps.backend.api.routers.pusher import _process_webhook_event

        event = {"name": "channel_occupied", "channel": "test-channel", "data": {}}

        result = await _process_webhook_event(event)
        assert result["action"] == "channel_occupied"
        assert result["channel"] == "test-channel"

    @pytest.mark.asyncio
    async def test_process_channel_vacated_event(self):
        """Test processing channel_vacated event"""
        from apps.backend.api.routers.pusher import _process_webhook_event

        event = {"name": "channel_vacated", "channel": "test-channel", "data": {}}

        result = await _process_webhook_event(event)
        assert result["action"] == "channel_vacated"

    @pytest.mark.asyncio
    async def test_process_member_added_event(self):
        """Test processing member_added event"""
        from apps.backend.api.routers.pusher import _process_webhook_event

        event = {
            "name": "member_added",
            "channel": "presence-classroom",
            "data": {"user_id": "user_123"},
        }

        result = await _process_webhook_event(event)
        assert result["action"] == "member_added"
        assert result["data"] == {"user_id": "user_123"}

    @pytest.mark.asyncio
    async def test_process_member_removed_event(self):
        """Test processing member_removed event"""
        from apps.backend.api.routers.pusher import _process_webhook_event

        event = {
            "name": "member_removed",
            "channel": "presence-classroom",
            "data": {"user_id": "user_456"},
        }

        result = await _process_webhook_event(event)
        assert result["action"] == "member_removed"

    @pytest.mark.asyncio
    async def test_process_unknown_event(self):
        """Test processing unknown event type"""
        from apps.backend.api.routers.pusher import _process_webhook_event

        event = {"name": "custom_event", "channel": "test-channel", "data": {}}

        result = await _process_webhook_event(event)
        assert result["action"] == "unknown_event"
        assert result["event"] == "custom_event"
