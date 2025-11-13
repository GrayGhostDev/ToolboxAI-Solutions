"""
Unit tests for Pusher Service

Tests Pusher Channels integration for real-time messaging, event triggering,
channel authentication, webhook validation, and agent-specific events.
"""

from datetime import datetime
from unittest.mock import AsyncMock, Mock, patch

import pytest

from apps.backend.services.pusher import (
    AGENT_CHANNELS,
    AGENT_EVENTS,
    PusherService,
    PusherUnavailable,
    authenticate_channel,
    get_agent_channels,
    get_agent_events,
    get_pusher_client,
    get_pusher_service,
    trigger_agent_event,
    trigger_agent_status_change,
    trigger_event,
    trigger_health_update,
    trigger_metrics_update,
    trigger_task_event,
    verify_webhook,
)


@pytest.fixture
def mock_pusher_client():
    """Mock Pusher client"""
    client = Mock()
    client.trigger = Mock()
    client.trigger_batch = Mock()
    client.authenticate = Mock()
    client.channels_info = Mock()
    client.channel_info = Mock()
    client.users_info = Mock()
    client.validate_webhook = Mock(return_value=True)
    return client


@pytest.fixture
def mock_settings():
    """Mock settings with Pusher configuration"""
    with patch("apps.backend.services.pusher.settings") as mock:
        mock.PUSHER_ENABLED = True
        mock.PUSHER_APP_ID = "test_app_id"
        mock.PUSHER_KEY = "test_key"
        mock.PUSHER_SECRET = "test_secret"
        mock.PUSHER_CLUSTER = "us2"
        mock.PUSHER_SSL = True
        yield mock


@pytest.mark.unit
class TestPusherServiceInitialization:
    """Test Pusher service initialization"""

    def test_pusher_service_construction(self, mock_settings):
        """Test Pusher service construction with configuration"""
        with patch("apps.backend.services.pusher.pusher") as mock_pusher_module:
            mock_pusher_module.Pusher = Mock()

            service = PusherService(
                app_id="app_123", key="key_456", secret="secret_789", cluster="us3", ssl=True
            )

        assert service.app_id == "app_123"
        assert service.key == "key_456"
        assert service.secret == "secret_789"
        assert service.cluster == "us3"
        assert service.ssl is True

    def test_pusher_service_without_pusher_package(self):
        """Test service when pusher package not installed"""
        with patch("apps.backend.services.pusher.pusher", None):
            service = PusherService("app", "key", "secret")

        assert service.client is None

    def test_pusher_service_initialization_failure(self):
        """Test service when client initialization fails"""
        with patch("apps.backend.services.pusher.pusher") as mock_pusher_module:
            mock_pusher_module.Pusher = Mock(side_effect=ValueError("Invalid credentials"))

            service = PusherService("app", "key", "secret")

        assert service.client is None


@pytest.mark.unit
class TestEventTriggering:
    """Test event triggering functionality"""

    def test_trigger_event_success(self, mock_pusher_client):
        """Test successful event triggering"""
        service = PusherService("app", "key", "secret")
        service.client = mock_pusher_client

        result = service.trigger("test-channel", "test-event", {"message": "Hello"})

        assert result["channel"] == "test-channel"
        assert result["event"] == "test-event"
        mock_pusher_client.trigger.assert_called_once()

    def test_trigger_event_with_datetime(self, mock_pusher_client):
        """Test event triggering with datetime objects"""
        service = PusherService("app", "key", "secret")
        service.client = mock_pusher_client

        data = {"message": "Test", "timestamp": datetime(2025, 1, 1, 12, 0, 0)}

        service.trigger("test-channel", "test-event", data)

        mock_pusher_client.trigger.assert_called_once()
        # Verify datetime was serialized
        call_args = mock_pusher_client.trigger.call_args[0]
        assert "timestamp" in call_args[2]

    def test_trigger_event_without_client(self):
        """Test event triggering without initialized client"""
        service = PusherService("app", "key", "secret")
        service.client = None

        with pytest.raises(PusherUnavailable):
            service.trigger("channel", "event", {})

    def test_trigger_event_encoding_error(self, mock_pusher_client):
        """Test event triggering with encoding errors"""
        service = PusherService("app", "key", "secret")
        service.client = mock_pusher_client

        # Create data that can't be serialized normally
        class UnserializableObject:
            pass

        with patch(
            "apps.backend.services.pusher.json.dumps", side_effect=TypeError("Not serializable")
        ):
            service.trigger("channel", "event", {"obj": UnserializableObject()})

        # Should still trigger with fallback data
        mock_pusher_client.trigger.assert_called_once()

    def test_trigger_batch_success(self, mock_pusher_client):
        """Test batch event triggering"""
        service = PusherService("app", "key", "secret")
        service.client = mock_pusher_client

        events = [
            {"channel": "ch1", "event": "ev1", "data": {}},
            {"channel": "ch2", "event": "ev2", "data": {}},
        ]

        result = service.trigger_batch(events)

        assert result["status"] == "success"
        assert result["events_count"] == 2
        mock_pusher_client.trigger_batch.assert_called_once_with(events)

    @pytest.mark.asyncio
    async def test_async_trigger(self, mock_pusher_client):
        """Test async trigger compatibility"""
        service = PusherService("app", "key", "secret")
        service.client = mock_pusher_client

        result = await service.async_trigger("channel", "event", {"data": "test"})

        assert result["channel"] == "channel"
        mock_pusher_client.trigger.assert_called_once()


@pytest.mark.unit
class TestChannelAuthentication:
    """Test channel authentication"""

    def test_authenticate_private_channel(self, mock_pusher_client):
        """Test private channel authentication"""
        service = PusherService("app", "key", "secret")
        service.client = mock_pusher_client
        mock_pusher_client.authenticate.return_value = {"auth": "test_auth_token"}

        result = service.authenticate("private-channel", "socket_123")

        assert "auth" in result
        mock_pusher_client.authenticate.assert_called_once_with(
            channel="private-channel", socket_id="socket_123"
        )

    def test_authenticate_presence_channel(self, mock_pusher_client):
        """Test presence channel authentication with user data"""
        service = PusherService("app", "key", "secret")
        service.client = mock_pusher_client
        mock_pusher_client.authenticate.return_value = {"auth": "test_auth", "channel_data": "{}"}

        user_data = {"user_id": "user_123", "user_info": {"name": "Test User"}}
        result = service.authenticate("presence-chat", "socket_456", user_data)

        assert "auth" in result
        mock_pusher_client.authenticate.assert_called_once_with(
            channel="presence-chat", socket_id="socket_456", custom_data=user_data
        )

    def test_authenticate_without_client(self):
        """Test authentication without initialized client"""
        service = PusherService("app", "key", "secret")
        service.client = None

        with pytest.raises(PusherUnavailable):
            service.authenticate("channel", "socket_id")


@pytest.mark.unit
class TestChannelInfo:
    """Test channel information retrieval"""

    def test_channels_info_all(self, mock_pusher_client):
        """Test retrieving all channels info"""
        service = PusherService("app", "key", "secret")
        service.client = mock_pusher_client
        mock_pusher_client.channels_info.return_value = {"channels": {"ch1": {}, "ch2": {}}}

        result = service.channels_info()

        assert "channels" in result
        mock_pusher_client.channels_info.assert_called_once()

    def test_channels_info_with_prefix(self, mock_pusher_client):
        """Test retrieving channels with prefix filter"""
        service = PusherService("app", "key", "secret")
        service.client = mock_pusher_client

        service.channels_info(prefix_filter="private-")

        call_args = mock_pusher_client.channels_info.call_args[1]
        assert call_args["prefix_filter"] == "private-"

    def test_channels_info_with_attributes(self, mock_pusher_client):
        """Test retrieving channels with attributes"""
        service = PusherService("app", "key", "secret")
        service.client = mock_pusher_client

        service.channels_info(attributes=["user_count", "subscription_count"])

        call_args = mock_pusher_client.channels_info.call_args[1]
        assert "user_count,subscription_count" in call_args["info"]

    def test_channel_info_success(self, mock_pusher_client):
        """Test retrieving specific channel info"""
        service = PusherService("app", "key", "secret")
        service.client = mock_pusher_client
        mock_pusher_client.channel_info.return_value = {"occupied": True}

        result = service.channel_info("test-channel")

        assert "occupied" in result
        mock_pusher_client.channel_info.assert_called_once_with("test-channel")

    def test_users_info_presence_channel(self, mock_pusher_client):
        """Test retrieving users from presence channel"""
        service = PusherService("app", "key", "secret")
        service.client = mock_pusher_client
        mock_pusher_client.users_info.return_value = {"users": [{"id": "1"}, {"id": "2"}]}

        result = service.users_info("presence-chat")

        assert len(result["users"]) == 2
        mock_pusher_client.users_info.assert_called_once_with("presence-chat")


@pytest.mark.unit
class TestWebhookValidation:
    """Test webhook signature validation"""

    def test_validate_webhook_success(self, mock_pusher_client):
        """Test successful webhook validation"""
        service = PusherService("app", "key", "secret")
        service.client = mock_pusher_client

        result = service.validate_webhook("key_123", "signature_456", '{"event": "test"}')

        assert result is True
        mock_pusher_client.validate_webhook.assert_called_once()

    def test_validate_webhook_invalid(self, mock_pusher_client):
        """Test invalid webhook signature"""
        service = PusherService("app", "key", "secret")
        service.client = mock_pusher_client
        mock_pusher_client.validate_webhook.return_value = False

        result = service.validate_webhook("key", "bad_sig", "{}")

        assert result is False


@pytest.mark.unit
class TestGlobalFunctions:
    """Test global helper functions"""

    def test_get_pusher_service(self, mock_settings):
        """Test getting Pusher service instance"""
        with patch("apps.backend.services.pusher.pusher") as mock_pusher:
            mock_pusher.Pusher = Mock()

            service = get_pusher_service()

        assert isinstance(service, PusherService)
        assert service.app_id == "test_app_id"

    def test_get_pusher_service_unavailable(self):
        """Test getting service when Pusher unavailable"""
        with patch("apps.backend.services.pusher.settings") as mock_settings:
            mock_settings.PUSHER_ENABLED = False

            with pytest.raises(PusherUnavailable):
                get_pusher_service()

    def test_get_pusher_client(self, mock_settings):
        """Test getting raw Pusher client"""
        with patch("apps.backend.services.pusher.pusher") as mock_pusher:
            mock_client = Mock()
            mock_pusher.Pusher = Mock(return_value=mock_client)

            client = get_pusher_client()

        assert client == mock_client

    def test_trigger_event_function(self, mock_settings):
        """Test trigger_event helper function"""
        with patch("apps.backend.services.pusher.pusher") as mock_pusher:
            mock_client = Mock()
            mock_pusher.Pusher = Mock(return_value=mock_client)

            result = trigger_event("channel", "event", {"test": "data"})

        assert result["channel"] == "channel"
        assert result["event"] == "event"
        mock_client.trigger.assert_called_once()

    def test_authenticate_channel_private(self, mock_settings):
        """Test authenticate_channel for private channel"""
        with patch("apps.backend.services.pusher.pusher") as mock_pusher:
            mock_client = Mock()
            mock_client.authenticate = Mock(return_value={"auth": "token"})
            mock_pusher.Pusher = Mock(return_value=mock_client)

            result = authenticate_channel("socket_123", "private-test")

        assert "auth" in result

    def test_authenticate_channel_presence(self, mock_settings):
        """Test authenticate_channel for presence channel"""
        with patch("apps.backend.services.pusher.pusher") as mock_pusher:
            mock_client = Mock()
            mock_client.authenticate = Mock(return_value={"auth": "token", "channel_data": "{}"})
            mock_pusher.Pusher = Mock(return_value=mock_client)

            result = authenticate_channel(
                "socket_456", "presence-chat", user_id="user_123", user_info={"name": "Test"}
            )

        assert "auth" in result

    def test_verify_webhook_valid(self, mock_settings):
        """Test webhook verification with valid signature"""
        with patch("apps.backend.services.pusher.pusher") as mock_pusher:
            mock_webhook = Mock()
            mock_webhook.validate = Mock(return_value={"events": []})
            mock_pusher.Webhook = Mock(return_value=mock_webhook)

            result = verify_webhook({"key": "test"}, b'{"event": "test"}')

        assert result is not None

    def test_verify_webhook_invalid(self, mock_settings):
        """Test webhook verification with invalid signature"""
        with patch("apps.backend.services.pusher.pusher") as mock_pusher:
            mock_webhook = Mock()
            mock_webhook.validate = Mock(side_effect=Exception("Invalid signature"))
            mock_pusher.Webhook = Mock(return_value=mock_webhook)

            result = verify_webhook({}, b"{}")

        assert result is None


@pytest.mark.unit
class TestAgentEvents:
    """Test agent-specific event functions"""

    @pytest.mark.asyncio
    async def test_trigger_agent_event(self, mock_settings):
        """Test triggering agent event"""
        with patch("apps.backend.services.pusher.trigger_event") as mock_trigger:
            await trigger_agent_event("agent_started", "agent_123", {"status": "idle"}, "user_456")

            # Should trigger on two channels
            assert mock_trigger.call_count == 2

    @pytest.mark.asyncio
    async def test_trigger_agent_event_error_handling(self, mock_settings):
        """Test agent event error handling"""
        with patch(
            "apps.backend.services.pusher.trigger_event", side_effect=Exception("Pusher error")
        ):
            # Should not raise exception
            await trigger_agent_event("agent_error", "agent_123", {})

    @pytest.mark.asyncio
    async def test_trigger_task_event(self, mock_settings):
        """Test triggering task event"""
        with patch("apps.backend.services.pusher.trigger_event") as mock_trigger:
            await trigger_task_event(
                "task_created", "task_789", "agent_123", {"description": "Test task"}, "user_456"
            )

            # Should trigger on agent-tasks, agent-specific, and user-specific channels
            assert mock_trigger.call_count == 3

    @pytest.mark.asyncio
    async def test_trigger_task_event_without_user(self, mock_settings):
        """Test triggering task event without user"""
        with patch("apps.backend.services.pusher.trigger_event") as mock_trigger:
            await trigger_task_event("task_started", "task_999", "agent_456", {})

            # Should trigger on 2 channels (no user channel)
            assert mock_trigger.call_count == 2

    @pytest.mark.asyncio
    async def test_trigger_metrics_update(self, mock_settings):
        """Test triggering metrics update"""
        with patch("apps.backend.services.pusher.trigger_event") as mock_trigger:
            metrics = {"success_rate": 95.5, "error_rate": 4.5, "throughput": 100}

            await trigger_metrics_update(metrics, "agent_123")

            # Should trigger on metrics channel and agent channel
            assert mock_trigger.call_count == 2

    @pytest.mark.asyncio
    async def test_trigger_metrics_update_system_wide(self, mock_settings):
        """Test triggering system-wide metrics update"""
        with patch("apps.backend.services.pusher.trigger_event") as mock_trigger:
            await trigger_metrics_update({"system_metric": 100})

            # Should trigger only on metrics channel
            assert mock_trigger.call_count == 1

    @pytest.mark.asyncio
    async def test_trigger_health_update(self, mock_settings):
        """Test triggering health update"""
        with patch("apps.backend.services.pusher.trigger_event") as mock_trigger:
            health_data = {"status": "healthy", "uptime": 99.9, "active_agents": 5}

            await trigger_health_update(health_data)

            mock_trigger.assert_called_once()
            call_args = mock_trigger.call_args
            assert call_args[0][0] == AGENT_CHANNELS["system_health"]

    @pytest.mark.asyncio
    async def test_trigger_agent_status_change(self, mock_settings):
        """Test triggering agent status change"""
        with patch(
            "apps.backend.services.pusher.trigger_agent_event", new_callable=AsyncMock
        ) as mock_trigger:
            await trigger_agent_status_change("agent_123", "idle", "busy", {"task_id": "task_999"})

            mock_trigger.assert_awaited_once()
            call_args = mock_trigger.call_args
            assert call_args[0][0] == "agent_busy"

    @pytest.mark.asyncio
    async def test_trigger_agent_status_change_to_offline(self, mock_settings):
        """Test agent status change to offline"""
        with patch(
            "apps.backend.services.pusher.trigger_agent_event", new_callable=AsyncMock
        ) as mock_trigger:
            await trigger_agent_status_change("agent_456", "busy", "offline")

            call_args = mock_trigger.call_args
            assert call_args[0][0] == "agent_stopped"


@pytest.mark.unit
class TestAgentChannelsAndEvents:
    """Test agent channel and event constants"""

    def test_get_agent_channels(self):
        """Test getting agent channels"""
        channels = get_agent_channels()

        assert "agent_status" in channels
        assert "agent_tasks" in channels
        assert "agent_metrics" in channels
        assert "system_health" in channels
        assert isinstance(channels, dict)

    def test_get_agent_events(self):
        """Test getting agent events"""
        events = get_agent_events()

        assert "agent_started" in events
        assert "agent_stopped" in events
        assert "task_created" in events
        assert "task_completed" in events
        assert "metrics_updated" in events
        assert isinstance(events, dict)

    def test_agent_channels_immutability(self):
        """Test that returned channels dict is a copy"""
        channels1 = get_agent_channels()
        channels2 = get_agent_channels()

        assert channels1 == channels2
        assert channels1 is not channels2  # Different objects

    def test_agent_events_immutability(self):
        """Test that returned events dict is a copy"""
        events1 = get_agent_events()
        events2 = get_agent_events()

        assert events1 == events2
        assert events1 is not events2  # Different objects


@pytest.mark.unit
class TestPusherUnavailableException:
    """Test PusherUnavailable exception"""

    def test_pusher_unavailable_exception(self):
        """Test PusherUnavailable exception creation"""
        exc = PusherUnavailable("Test message")

        assert str(exc) == "Test message"
        assert isinstance(exc, Exception)


@pytest.mark.unit
class TestAgentChannelConstants:
    """Test agent channel and event constant values"""

    def test_agent_channels_values(self):
        """Test agent channel constant values"""
        assert AGENT_CHANNELS["agent_status"] == "agent-status"
        assert AGENT_CHANNELS["agent_tasks"] == "agent-tasks"
        assert AGENT_CHANNELS["agent_metrics"] == "agent-metrics"
        assert AGENT_CHANNELS["system_health"] == "system-health"
        assert AGENT_CHANNELS["agent_updates"] == "agent-updates"

    def test_agent_events_values(self):
        """Test agent event constant values"""
        assert AGENT_EVENTS["agent_started"] == "agent.started"
        assert AGENT_EVENTS["agent_stopped"] == "agent.stopped"
        assert AGENT_EVENTS["task_created"] == "task.created"
        assert AGENT_EVENTS["task_completed"] == "task.completed"
        assert AGENT_EVENTS["task_failed"] == "task.failed"
        assert AGENT_EVENTS["metrics_updated"] == "metrics.updated"
        assert AGENT_EVENTS["health_updated"] == "health.updated"
