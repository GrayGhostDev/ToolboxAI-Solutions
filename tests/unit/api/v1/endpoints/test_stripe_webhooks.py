"""
Unit Tests for Stripe Webhook Handlers

Tests webhook event processing including:
- Signature verification
- Event parsing and validation
- Checkout session completion
- Subscription lifecycle events
- Payment success/failure handling
- Multi-tenant organization ID extraction
- Error handling and security
"""

import hashlib
import hmac
import json
from datetime import datetime
from unittest.mock import AsyncMock, Mock, patch
from uuid import uuid4

import pytest
from fastapi import HTTPException

# Import webhook functions and models
from apps.backend.api.v1.endpoints.stripe_webhooks import (
    StripeEvent,
    extract_organization_id,
    handle_checkout_completed,
    handle_payment_failed,
    handle_payment_succeeded,
    handle_stripe_webhook,
    handle_subscription_created,
    handle_subscription_deleted,
    handle_subscription_updated,
    verify_stripe_signature,
)


@pytest.fixture
def mock_request():
    """Mock FastAPI request with webhook payload"""
    request = Mock()
    request.body = AsyncMock()
    return request


@pytest.fixture
def mock_stripe_service():
    """Mock Stripe service"""
    with patch("apps.backend.api.v1.endpoints.stripe_webhooks.StripeService") as mock:
        service_instance = Mock()
        service_instance._handle_checkout_completed = AsyncMock(
            return_value={"status": "processed"}
        )
        service_instance._handle_subscription_created = AsyncMock(
            return_value={"status": "processed"}
        )
        service_instance._handle_subscription_updated = AsyncMock(
            return_value={"status": "processed"}
        )
        service_instance._handle_subscription_deleted = AsyncMock(
            return_value={"status": "processed"}
        )
        service_instance._handle_payment_succeeded = AsyncMock(return_value={"status": "processed"})
        service_instance._handle_payment_failed = AsyncMock(return_value={"status": "processed"})
        mock.return_value = service_instance
        yield service_instance


@pytest.fixture
def sample_org_id():
    """Sample organization ID"""
    return uuid4()


@pytest.fixture
def sample_webhook_event(sample_org_id):
    """Sample Stripe webhook event"""
    return {
        "id": "evt_test_123",
        "object": "event",
        "api_version": "2023-10-16",
        "created": int(datetime.now().timestamp()),
        "data": {
            "object": {
                "id": "sub_test_123",
                "object": "subscription",
                "metadata": {"organization_id": str(sample_org_id), "user_id": "user_123"},
            }
        },
        "livemode": False,
        "pending_webhooks": 1,
        "type": "customer.subscription.created",
    }


class TestSignatureVerification:
    """Test Stripe webhook signature verification."""

    def test_verify_signature_valid(self):
        """Test valid signature verification."""
        # Arrange
        secret = "whsec_test_secret"
        payload = b'{"test": "data"}'
        timestamp = str(int(datetime.now().timestamp()))

        # Create valid signature
        signed_payload = f"{timestamp}.".encode() + payload
        signature_hash = hmac.new(secret.encode(), signed_payload, hashlib.sha256).hexdigest()
        signature = f"t={timestamp},v1={signature_hash}"

        # Act
        result = verify_stripe_signature(payload, signature, secret)

        # Assert
        assert result is True

    def test_verify_signature_invalid(self):
        """Test invalid signature verification."""
        # Arrange
        secret = "whsec_test_secret"
        payload = b'{"test": "data"}'
        timestamp = str(int(datetime.now().timestamp()))
        signature = f"t={timestamp},v1=invalid_signature_hash"

        # Act
        result = verify_stripe_signature(payload, signature, secret)

        # Assert
        assert result is False

    def test_verify_signature_missing_timestamp(self):
        """Test signature verification with missing timestamp."""
        # Arrange
        secret = "whsec_test_secret"
        payload = b'{"test": "data"}'
        signature = "v1=some_hash"

        # Act
        result = verify_stripe_signature(payload, signature, secret)

        # Assert
        assert result is False

    def test_verify_signature_no_secret(self):
        """Test signature verification with no secret configured."""
        # Arrange
        payload = b'{"test": "data"}'
        signature = "t=123,v1=hash"

        # Act
        result = verify_stripe_signature(payload, signature, "")

        # Assert
        assert result is False


class TestOrganizationExtraction:
    """Test organization ID extraction from Stripe metadata."""

    def test_extract_organization_id_success(self, sample_org_id):
        """Test successful organization ID extraction."""
        # Arrange
        stripe_object = {"id": "obj_123", "metadata": {"organization_id": str(sample_org_id)}}

        # Act
        result = extract_organization_id(stripe_object)

        # Assert
        assert result == sample_org_id

    def test_extract_organization_id_missing(self):
        """Test extraction when organization_id is missing."""
        # Arrange
        stripe_object = {"id": "obj_123", "metadata": {}}

        # Act
        result = extract_organization_id(stripe_object)

        # Assert
        assert result is None

    def test_extract_organization_id_invalid_uuid(self):
        """Test extraction with invalid UUID format."""
        # Arrange
        stripe_object = {"id": "obj_123", "metadata": {"organization_id": "not-a-valid-uuid"}}

        # Act
        result = extract_organization_id(stripe_object)

        # Assert
        assert result is None

    def test_extract_organization_id_no_metadata(self):
        """Test extraction when metadata field is missing."""
        # Arrange
        stripe_object = {"id": "obj_123"}

        # Act
        result = extract_organization_id(stripe_object)

        # Assert
        assert result is None


class TestWebhookMainHandler:
    """Test main webhook handler endpoint."""

    @pytest.mark.asyncio
    @patch("apps.backend.api.v1.endpoints.stripe_webhooks.ENABLE_STRIPE_WEBHOOKS", True)
    @patch("apps.backend.api.v1.endpoints.stripe_webhooks.STRIPE_WEBHOOK_SECRET", "")
    async def test_webhook_handler_success_no_signature(
        self, mock_request, sample_webhook_event, mock_stripe_service
    ):
        """Test successful webhook processing without signature verification."""
        # Arrange
        payload = json.dumps(sample_webhook_event).encode()
        mock_request.body.return_value = payload

        # Act
        result = await handle_stripe_webhook(mock_request, stripe_signature=None)

        # Assert
        assert result.status == "success"
        assert result.event_id == "evt_test_123"
        assert "subscription.created" in result.message
        mock_stripe_service._handle_subscription_created.assert_called_once()

    @pytest.mark.asyncio
    @patch("apps.backend.api.v1.endpoints.stripe_webhooks.ENABLE_STRIPE_WEBHOOKS", False)
    async def test_webhook_handler_disabled(self, mock_request):
        """Test webhook handler when webhooks are disabled."""
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await handle_stripe_webhook(mock_request, stripe_signature=None)

        assert exc_info.value.status_code == 503
        assert "disabled" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    @patch("apps.backend.api.v1.endpoints.stripe_webhooks.ENABLE_STRIPE_WEBHOOKS", True)
    @patch("apps.backend.api.v1.endpoints.stripe_webhooks.STRIPE_WEBHOOK_SECRET", "whsec_test")
    async def test_webhook_handler_missing_signature(self, mock_request, sample_webhook_event):
        """Test webhook handler with missing signature header."""
        # Arrange
        payload = json.dumps(sample_webhook_event).encode()
        mock_request.body.return_value = payload

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await handle_stripe_webhook(mock_request, stripe_signature=None)

        assert exc_info.value.status_code == 400
        assert "Missing Stripe signature" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    @patch("apps.backend.api.v1.endpoints.stripe_webhooks.ENABLE_STRIPE_WEBHOOKS", True)
    @patch("apps.backend.api.v1.endpoints.stripe_webhooks.STRIPE_WEBHOOK_SECRET", "whsec_test")
    @patch(
        "apps.backend.api.v1.endpoints.stripe_webhooks.verify_stripe_signature", return_value=False
    )
    async def test_webhook_handler_invalid_signature(
        self, mock_verify, mock_request, sample_webhook_event
    ):
        """Test webhook handler with invalid signature."""
        # Arrange
        payload = json.dumps(sample_webhook_event).encode()
        mock_request.body.return_value = payload

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await handle_stripe_webhook(mock_request, stripe_signature="invalid")

        assert exc_info.value.status_code == 400
        assert "Invalid signature" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    @patch("apps.backend.api.v1.endpoints.stripe_webhooks.ENABLE_STRIPE_WEBHOOKS", True)
    @patch("apps.backend.api.v1.endpoints.stripe_webhooks.STRIPE_WEBHOOK_SECRET", "")
    async def test_webhook_handler_invalid_json(self, mock_request):
        """Test webhook handler with invalid JSON payload."""
        # Arrange
        mock_request.body.return_value = b"invalid json {"

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await handle_stripe_webhook(mock_request, stripe_signature=None)

        assert exc_info.value.status_code == 400
        assert "Invalid event payload" in str(exc_info.value.detail)


class TestEventHandlers:
    """Test individual Stripe event handlers."""

    @pytest.mark.asyncio
    async def test_handle_checkout_completed(
        self, sample_webhook_event, sample_org_id, mock_stripe_service
    ):
        """Test checkout completion event handler."""
        # Arrange
        sample_webhook_event["type"] = "checkout.session.completed"
        event = StripeEvent(**sample_webhook_event)

        # Act
        await handle_checkout_completed(event)

        # Assert
        mock_stripe_service._handle_checkout_completed.assert_called_once()
        call_args = mock_stripe_service._handle_checkout_completed.call_args
        assert call_args[1]["organization_id"] == sample_org_id

    @pytest.mark.asyncio
    async def test_handle_subscription_created(
        self, sample_webhook_event, sample_org_id, mock_stripe_service
    ):
        """Test subscription creation event handler."""
        # Arrange
        event = StripeEvent(**sample_webhook_event)

        # Act
        await handle_subscription_created(event)

        # Assert
        mock_stripe_service._handle_subscription_created.assert_called_once()
        call_args = mock_stripe_service._handle_subscription_created.call_args
        assert call_args[1]["organization_id"] == sample_org_id

    @pytest.mark.asyncio
    async def test_handle_subscription_updated(
        self, sample_webhook_event, sample_org_id, mock_stripe_service
    ):
        """Test subscription update event handler."""
        # Arrange
        sample_webhook_event["type"] = "customer.subscription.updated"
        event = StripeEvent(**sample_webhook_event)

        # Act
        await handle_subscription_updated(event)

        # Assert
        mock_stripe_service._handle_subscription_updated.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_subscription_deleted(
        self, sample_webhook_event, sample_org_id, mock_stripe_service
    ):
        """Test subscription deletion event handler."""
        # Arrange
        sample_webhook_event["type"] = "customer.subscription.deleted"
        event = StripeEvent(**sample_webhook_event)

        # Act
        await handle_subscription_deleted(event)

        # Assert
        mock_stripe_service._handle_subscription_deleted.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_payment_succeeded(
        self, sample_webhook_event, sample_org_id, mock_stripe_service
    ):
        """Test payment success event handler."""
        # Arrange
        sample_webhook_event["type"] = "invoice.payment_succeeded"
        sample_webhook_event["data"]["object"]["object"] = "invoice"
        event = StripeEvent(**sample_webhook_event)

        # Act
        await handle_payment_succeeded(event)

        # Assert
        mock_stripe_service._handle_payment_succeeded.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_payment_failed(
        self, sample_webhook_event, sample_org_id, mock_stripe_service
    ):
        """Test payment failure event handler."""
        # Arrange
        sample_webhook_event["type"] = "invoice.payment_failed"
        sample_webhook_event["data"]["object"]["object"] = "invoice"
        event = StripeEvent(**sample_webhook_event)

        # Act
        await handle_payment_failed(event)

        # Assert
        mock_stripe_service._handle_payment_failed.assert_called_once()


class TestMultiTenantSecurity:
    """Test multi-tenant security in webhook processing."""

    @pytest.mark.asyncio
    async def test_organization_id_passed_to_service(
        self, sample_webhook_event, sample_org_id, mock_stripe_service
    ):
        """Test that organization_id is extracted and passed to service layer."""
        # Arrange
        event = StripeEvent(**sample_webhook_event)

        # Act
        await handle_subscription_created(event)

        # Assert
        call_args = mock_stripe_service._handle_subscription_created.call_args
        assert call_args[1]["organization_id"] == sample_org_id

    @pytest.mark.asyncio
    async def test_missing_organization_id_handled(self, sample_webhook_event, mock_stripe_service):
        """Test webhook processing when organization_id is missing."""
        # Arrange
        sample_webhook_event["data"]["object"]["metadata"] = {}
        event = StripeEvent(**sample_webhook_event)

        # Act
        await handle_subscription_created(event)

        # Assert - should still process but with None org_id
        call_args = mock_stripe_service._handle_subscription_created.call_args
        assert call_args[1]["organization_id"] is None


class TestUnhandledEvents:
    """Test handling of unhandled event types."""

    @pytest.mark.asyncio
    @patch("apps.backend.api.v1.endpoints.stripe_webhooks.ENABLE_STRIPE_WEBHOOKS", True)
    @patch("apps.backend.api.v1.endpoints.stripe_webhooks.STRIPE_WEBHOOK_SECRET", "")
    async def test_unhandled_event_type(self, mock_request, sample_webhook_event):
        """Test handling of unsupported event type."""
        # Arrange
        sample_webhook_event["type"] = "customer.created"  # Unhandled event
        payload = json.dumps(sample_webhook_event).encode()
        mock_request.body.return_value = payload

        # Act
        result = await handle_stripe_webhook(mock_request, stripe_signature=None)

        # Assert - should succeed but log unhandled type
        assert result.status == "success"
        assert "customer.created" in result.message


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
