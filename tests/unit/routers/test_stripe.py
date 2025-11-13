"""
Unit tests for Stripe payment router

Tests all Stripe payment endpoints including checkout sessions, subscriptions,
customer management, invoices, and webhook handling.
"""

from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastapi import status
from fastapi.testclient import TestClient

# Import the main FastAPI app
from apps.backend.main import app


@pytest.fixture
def test_client():
    """FastAPI test client"""
    return TestClient(app)


@pytest.fixture
def mock_current_user():
    """Mock authenticated user"""
    user = Mock()
    user.id = "user_123"
    user.email = "test@example.com"
    user.name = "Test User"
    user.role = "student"
    return user


@pytest.fixture
def mock_stripe_service():
    """Mock StripeService"""
    service = AsyncMock()

    # Mock customer creation
    service.create_customer.return_value = {
        "id": "cus_123456",
        "email": "test@example.com",
        "name": "Test User",
        "default_source": None,
    }

    # Mock checkout session creation
    service.create_checkout_session.return_value = {
        "id": "cs_123456",
        "url": "https://checkout.stripe.com/pay/cs_123456",
        "amount_total": 2999,
    }

    # Mock subscription creation
    service.create_subscription.return_value = {
        "id": "sub_123456",
        "status": "trialing",
        "current_period_end": 1735689600,
        "trial_end": 1734393600,
    }

    # Mock subscription update
    service.update_subscription.return_value = {
        "id": "sub_123456",
        "status": "active",
        "cancel_at_period_end": False,
    }

    # Mock subscription cancellation
    service.cancel_subscription.return_value = {
        "id": "sub_123456",
        "status": "canceled",
        "canceled_at": 1734393600,
    }

    # Mock invoice retrieval
    service.get_invoices.return_value = [
        {
            "id": "in_123456",
            "number": "INV-001",
            "amount_due": 2999,
            "amount_paid": 2999,
            "status": "paid",
            "created": 1734393600,
            "due_date": None,
            "invoice_pdf": "https://pay.stripe.com/invoice/123/pdf",
        }
    ]

    # Mock webhook handling
    service.handle_webhook.return_value = (
        True,
        {
            "event_type": "checkout.session.completed",
            "event_id": "evt_123456",
        },
    )

    return service


@pytest.fixture
def sample_checkout_request():
    """Sample checkout session request"""
    return {
        "price_id": "price_123456",
        "mode": "subscription",
        "success_url": "https://example.com/success",
        "cancel_url": "https://example.com/cancel",
        "metadata": {"plan": "premium"},
    }


@pytest.fixture
def sample_subscription_request():
    """Sample subscription request"""
    return {
        "price_id": "price_123456",
        "trial_days": 14,
        "payment_method_id": "pm_123456",
        "metadata": {"plan": "premium"},
    }


@pytest.mark.unit
class TestCheckoutSession:
    """Test checkout session creation endpoint"""

    def test_create_checkout_session_success(
        self, test_client, sample_checkout_request, mock_current_user, mock_stripe_service
    ):
        """Test successful checkout session creation"""
        with patch(
            "apps.backend.api.routers.stripe.get_current_user", return_value=mock_current_user
        ):
            with patch("apps.backend.api.routers.stripe.stripe_service", mock_stripe_service):
                with patch("apps.backend.api.routers.stripe.log_audit"):
                    response = test_client.post(
                        "/api/v1/stripe/checkout", json=sample_checkout_request
                    )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "success"
        assert "session_id" in data["data"]
        assert "url" in data["data"]
        assert data["data"]["session_id"] == "cs_123456"
        assert data["data"]["customer_id"] == "cus_123456"

        # Verify service calls
        mock_stripe_service.create_customer.assert_called_once()
        mock_stripe_service.create_checkout_session.assert_called_once()

    def test_create_checkout_session_with_line_items(
        self, test_client, mock_current_user, mock_stripe_service
    ):
        """Test checkout session with line items for one-time payment"""
        request_data = {
            "line_items": [{"price": "price_123", "quantity": 1}],
            "mode": "payment",
        }

        with patch(
            "apps.backend.api.routers.stripe.get_current_user", return_value=mock_current_user
        ):
            with patch("apps.backend.api.routers.stripe.stripe_service", mock_stripe_service):
                with patch("apps.backend.api.routers.stripe.log_audit"):
                    response = test_client.post("/api/v1/stripe/checkout", json=request_data)

        assert response.status_code == status.HTTP_200_OK

    def test_create_checkout_session_default_urls(
        self, test_client, mock_current_user, mock_stripe_service
    ):
        """Test checkout session creation with default success/cancel URLs"""
        request_data = {
            "price_id": "price_123456",
            "mode": "subscription",
        }

        with patch(
            "apps.backend.api.routers.stripe.get_current_user", return_value=mock_current_user
        ):
            with patch("apps.backend.api.routers.stripe.stripe_service", mock_stripe_service):
                with patch("apps.backend.api.routers.stripe.log_audit"):
                    with patch("apps.backend.api.routers.stripe.settings") as mock_settings:
                        mock_settings.FRONTEND_URL = "https://example.com"
                        response = test_client.post("/api/v1/stripe/checkout", json=request_data)

        assert response.status_code == status.HTTP_200_OK

        # Verify checkout session was called with default URLs
        call_args = mock_stripe_service.create_checkout_session.call_args
        assert "billing/success" in call_args.kwargs["success_url"]
        assert "billing/cancel" in call_args.kwargs["cancel_url"]

    def test_create_checkout_session_stripe_error(
        self, test_client, sample_checkout_request, mock_current_user, mock_stripe_service
    ):
        """Test checkout session creation with Stripe API error"""
        mock_stripe_service.create_checkout_session.side_effect = Exception("Stripe API error")

        with patch(
            "apps.backend.api.routers.stripe.get_current_user", return_value=mock_current_user
        ):
            with patch("apps.backend.api.routers.stripe.stripe_service", mock_stripe_service):
                response = test_client.post("/api/v1/stripe/checkout", json=sample_checkout_request)

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        data = response.json()
        assert "Failed to create checkout session" in data["detail"]


@pytest.mark.unit
class TestSubscriptionCreation:
    """Test subscription creation endpoint"""

    def test_create_subscription_success(
        self, test_client, sample_subscription_request, mock_current_user, mock_stripe_service
    ):
        """Test successful subscription creation"""
        with patch(
            "apps.backend.api.routers.stripe.get_current_user", return_value=mock_current_user
        ):
            with patch("apps.backend.api.routers.stripe.stripe_service", mock_stripe_service):
                with patch("apps.backend.api.routers.stripe.log_audit"):
                    response = test_client.post(
                        "/api/v1/stripe/subscriptions", json=sample_subscription_request
                    )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "success"
        assert data["data"]["subscription_id"] == "sub_123456"
        assert data["data"]["status"] == "trialing"
        assert "trial_end" in data["data"]

        # Verify service calls
        mock_stripe_service.create_customer.assert_called_once_with(
            user_id="user_123",
            email="test@example.com",
            name="Test User",
            payment_method_id="pm_123456",
        )
        mock_stripe_service.create_subscription.assert_called_once()

    def test_create_subscription_without_trial(
        self, test_client, mock_current_user, mock_stripe_service
    ):
        """Test subscription creation without trial period"""
        request_data = {
            "price_id": "price_123456",
            "trial_days": 0,
        }

        mock_stripe_service.create_subscription.return_value = {
            "id": "sub_123456",
            "status": "active",
            "current_period_end": 1735689600,
            "trial_end": None,
        }

        with patch(
            "apps.backend.api.routers.stripe.get_current_user", return_value=mock_current_user
        ):
            with patch("apps.backend.api.routers.stripe.stripe_service", mock_stripe_service):
                with patch("apps.backend.api.routers.stripe.log_audit"):
                    response = test_client.post("/api/v1/stripe/subscriptions", json=request_data)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["data"]["status"] == "active"
        assert data["data"]["trial_end"] is None

    def test_create_subscription_missing_price_id(self, test_client, mock_current_user):
        """Test subscription creation with missing price_id"""
        request_data = {
            "trial_days": 14,
        }

        with patch(
            "apps.backend.api.routers.stripe.get_current_user", return_value=mock_current_user
        ):
            response = test_client.post("/api/v1/stripe/subscriptions", json=request_data)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_create_subscription_stripe_error(
        self, test_client, sample_subscription_request, mock_current_user, mock_stripe_service
    ):
        """Test subscription creation with Stripe API error"""
        mock_stripe_service.create_subscription.side_effect = Exception("Payment method required")

        with patch(
            "apps.backend.api.routers.stripe.get_current_user", return_value=mock_current_user
        ):
            with patch("apps.backend.api.routers.stripe.stripe_service", mock_stripe_service):
                response = test_client.post(
                    "/api/v1/stripe/subscriptions", json=sample_subscription_request
                )

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        data = response.json()
        assert "Failed to create subscription" in data["detail"]


@pytest.mark.unit
class TestSubscriptionUpdate:
    """Test subscription update endpoint"""

    def test_update_subscription_change_price(
        self, test_client, mock_current_user, mock_stripe_service
    ):
        """Test subscription price change"""
        request_data = {
            "price_id": "price_new_789",
        }

        with patch(
            "apps.backend.api.routers.stripe.get_current_user", return_value=mock_current_user
        ):
            with patch("apps.backend.api.routers.stripe.stripe_service", mock_stripe_service):
                with patch("apps.backend.api.routers.stripe.log_audit"):
                    response = test_client.patch(
                        "/api/v1/stripe/subscriptions/sub_123456", json=request_data
                    )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "success"
        assert data["data"]["subscription_id"] == "sub_123456"

        # Verify update was called with correct arguments
        call_args = mock_stripe_service.update_subscription.call_args
        assert call_args.args[0] == "sub_123456"
        assert "items" in call_args.kwargs

    def test_update_subscription_cancel_at_period_end(
        self, test_client, mock_current_user, mock_stripe_service
    ):
        """Test setting subscription to cancel at period end"""
        request_data = {
            "cancel_at_period_end": True,
        }

        mock_stripe_service.update_subscription.return_value = {
            "id": "sub_123456",
            "status": "active",
            "cancel_at_period_end": True,
        }

        with patch(
            "apps.backend.api.routers.stripe.get_current_user", return_value=mock_current_user
        ):
            with patch("apps.backend.api.routers.stripe.stripe_service", mock_stripe_service):
                with patch("apps.backend.api.routers.stripe.log_audit"):
                    response = test_client.patch(
                        "/api/v1/stripe/subscriptions/sub_123456", json=request_data
                    )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["data"]["cancel_at_period_end"] is True

    def test_update_subscription_metadata(
        self, test_client, mock_current_user, mock_stripe_service
    ):
        """Test updating subscription metadata"""
        request_data = {
            "metadata": {"upgrade_reason": "annual_discount"},
        }

        with patch(
            "apps.backend.api.routers.stripe.get_current_user", return_value=mock_current_user
        ):
            with patch("apps.backend.api.routers.stripe.stripe_service", mock_stripe_service):
                with patch("apps.backend.api.routers.stripe.log_audit"):
                    response = test_client.patch(
                        "/api/v1/stripe/subscriptions/sub_123456", json=request_data
                    )

        assert response.status_code == status.HTTP_200_OK

    def test_update_subscription_stripe_error(
        self, test_client, mock_current_user, mock_stripe_service
    ):
        """Test subscription update with Stripe API error"""
        request_data = {"price_id": "price_invalid"}
        mock_stripe_service.update_subscription.side_effect = Exception("Invalid price")

        with patch(
            "apps.backend.api.routers.stripe.get_current_user", return_value=mock_current_user
        ):
            with patch("apps.backend.api.routers.stripe.stripe_service", mock_stripe_service):
                response = test_client.patch(
                    "/api/v1/stripe/subscriptions/sub_123456", json=request_data
                )

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        data = response.json()
        assert "Failed to update subscription" in data["detail"]


@pytest.mark.unit
class TestSubscriptionCancellation:
    """Test subscription cancellation endpoint"""

    def test_cancel_subscription_at_period_end(
        self, test_client, mock_current_user, mock_stripe_service
    ):
        """Test cancelling subscription at period end (default)"""
        mock_stripe_service.cancel_subscription.return_value = {
            "id": "sub_123456",
            "status": "active",
            "canceled_at": None,
        }

        with patch(
            "apps.backend.api.routers.stripe.get_current_user", return_value=mock_current_user
        ):
            with patch("apps.backend.api.routers.stripe.stripe_service", mock_stripe_service):
                with patch("apps.backend.api.routers.stripe.log_audit"):
                    response = test_client.delete(
                        "/api/v1/stripe/subscriptions/sub_123456?immediately=false"
                    )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "will cancel at period end" in data["message"]

        # Verify cancellation was called correctly
        mock_stripe_service.cancel_subscription.assert_called_once_with(
            subscription_id="sub_123456", immediately=False
        )

    def test_cancel_subscription_immediately(
        self, test_client, mock_current_user, mock_stripe_service
    ):
        """Test immediate subscription cancellation"""
        with patch(
            "apps.backend.api.routers.stripe.get_current_user", return_value=mock_current_user
        ):
            with patch("apps.backend.api.routers.stripe.stripe_service", mock_stripe_service):
                with patch("apps.backend.api.routers.stripe.log_audit"):
                    response = test_client.delete(
                        "/api/v1/stripe/subscriptions/sub_123456?immediately=true"
                    )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["data"]["status"] == "canceled"
        assert "cancelled immediately" in data["message"]

        # Verify immediate cancellation
        mock_stripe_service.cancel_subscription.assert_called_once_with(
            subscription_id="sub_123456", immediately=True
        )

    def test_cancel_subscription_stripe_error(
        self, test_client, mock_current_user, mock_stripe_service
    ):
        """Test subscription cancellation with Stripe API error"""
        mock_stripe_service.cancel_subscription.side_effect = Exception("Subscription not found")

        with patch(
            "apps.backend.api.routers.stripe.get_current_user", return_value=mock_current_user
        ):
            with patch("apps.backend.api.routers.stripe.stripe_service", mock_stripe_service):
                response = test_client.delete("/api/v1/stripe/subscriptions/sub_invalid")

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        data = response.json()
        assert "Failed to cancel subscription" in data["detail"]


@pytest.mark.unit
class TestCustomerInfo:
    """Test customer information endpoint"""

    def test_get_customer_info_success(self, test_client, mock_current_user, mock_stripe_service):
        """Test successful customer info retrieval"""
        with patch(
            "apps.backend.api.routers.stripe.get_current_user", return_value=mock_current_user
        ):
            with patch("apps.backend.api.routers.stripe.stripe_service", mock_stripe_service):
                response = test_client.get("/api/v1/stripe/customer")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "success"
        assert data["data"]["customer_id"] == "cus_123456"
        assert data["data"]["email"] == "test@example.com"
        assert data["data"]["name"] == "Test User"

    def test_get_customer_info_creates_if_not_exists(
        self, test_client, mock_current_user, mock_stripe_service
    ):
        """Test customer info endpoint creates customer if not exists"""
        with patch(
            "apps.backend.api.routers.stripe.get_current_user", return_value=mock_current_user
        ):
            with patch("apps.backend.api.routers.stripe.stripe_service", mock_stripe_service):
                response = test_client.get("/api/v1/stripe/customer")

        # Verify customer creation was called
        mock_stripe_service.create_customer.assert_called_once()
        assert response.status_code == status.HTTP_200_OK

    def test_get_customer_info_stripe_error(
        self, test_client, mock_current_user, mock_stripe_service
    ):
        """Test customer info retrieval with Stripe API error"""
        mock_stripe_service.create_customer.side_effect = Exception("API error")

        with patch(
            "apps.backend.api.routers.stripe.get_current_user", return_value=mock_current_user
        ):
            with patch("apps.backend.api.routers.stripe.stripe_service", mock_stripe_service):
                response = test_client.get("/api/v1/stripe/customer")

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        data = response.json()
        assert "Failed to get customer information" in data["detail"]


@pytest.mark.unit
class TestInvoices:
    """Test invoice listing endpoint"""

    def test_get_invoices_success(self, test_client, mock_current_user, mock_stripe_service):
        """Test successful invoice retrieval"""
        with patch(
            "apps.backend.api.routers.stripe.get_current_user", return_value=mock_current_user
        ):
            with patch("apps.backend.api.routers.stripe.stripe_service", mock_stripe_service):
                response = test_client.get("/api/v1/stripe/invoices")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "success"
        assert len(data["data"]["invoices"]) == 1
        assert data["data"]["invoices"][0]["id"] == "in_123456"
        assert data["data"]["invoices"][0]["status"] == "paid"

    def test_get_invoices_with_limit(self, test_client, mock_current_user, mock_stripe_service):
        """Test invoice retrieval with custom limit"""
        with patch(
            "apps.backend.api.routers.stripe.get_current_user", return_value=mock_current_user
        ):
            with patch("apps.backend.api.routers.stripe.stripe_service", mock_stripe_service):
                response = test_client.get("/api/v1/stripe/invoices?limit=20")

        assert response.status_code == status.HTTP_200_OK

        # Verify limit was passed to service
        call_args = mock_stripe_service.get_invoices.call_args
        assert call_args.kwargs["limit"] == 20

    def test_get_invoices_empty_list(self, test_client, mock_current_user, mock_stripe_service):
        """Test invoice retrieval with no invoices"""
        mock_stripe_service.get_invoices.return_value = []

        with patch(
            "apps.backend.api.routers.stripe.get_current_user", return_value=mock_current_user
        ):
            with patch("apps.backend.api.routers.stripe.stripe_service", mock_stripe_service):
                response = test_client.get("/api/v1/stripe/invoices")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["data"]["invoices"]) == 0

    def test_get_invoices_stripe_error(self, test_client, mock_current_user, mock_stripe_service):
        """Test invoice retrieval with Stripe API error"""
        mock_stripe_service.get_invoices.side_effect = Exception("API error")

        with patch(
            "apps.backend.api.routers.stripe.get_current_user", return_value=mock_current_user
        ):
            with patch("apps.backend.api.routers.stripe.stripe_service", mock_stripe_service):
                response = test_client.get("/api/v1/stripe/invoices")

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        data = response.json()
        assert "Failed to get invoices" in data["detail"]


@pytest.mark.unit
class TestWebhookHandler:
    """Test Stripe webhook handling endpoint"""

    @pytest.mark.asyncio
    async def test_handle_webhook_success(self, test_client, mock_stripe_service):
        """Test successful webhook processing"""
        payload = b'{"type": "checkout.session.completed"}'
        signature = "t=1234567890,v1=signature_here"

        with patch("apps.backend.api.routers.stripe.stripe_service", mock_stripe_service):
            response = test_client.post(
                "/api/v1/stripe/webhook", data=payload, headers={"Stripe-Signature": signature}
            )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "success"
        assert data["data"]["event_type"] == "checkout.session.completed"
        assert data["data"]["processed"] is True

        # Verify webhook handler was called
        mock_stripe_service.handle_webhook.assert_called_once_with(
            payload=payload, signature=signature
        )

    @pytest.mark.asyncio
    async def test_handle_webhook_invalid_signature(self, test_client, mock_stripe_service):
        """Test webhook with invalid signature"""
        payload = b'{"type": "checkout.session.completed"}'
        signature = "invalid_signature"

        mock_stripe_service.handle_webhook.return_value = (False, {"error": "Invalid signature"})

        with patch("apps.backend.api.routers.stripe.stripe_service", mock_stripe_service):
            response = test_client.post(
                "/api/v1/stripe/webhook", data=payload, headers={"Stripe-Signature": signature}
            )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert "signature" in data["detail"].lower() or "verification" in data["detail"].lower()

    @pytest.mark.asyncio
    async def test_handle_webhook_missing_signature(self, test_client, mock_stripe_service):
        """Test webhook with missing signature header"""
        payload = b'{"type": "checkout.session.completed"}'

        mock_stripe_service.handle_webhook.return_value = (False, {"error": "Signature required"})

        with patch("apps.backend.api.routers.stripe.stripe_service", mock_stripe_service):
            response = test_client.post("/api/v1/stripe/webhook", data=payload)

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @pytest.mark.asyncio
    async def test_handle_webhook_payment_succeeded(self, test_client, mock_stripe_service):
        """Test webhook for payment_intent.succeeded event"""
        payload = b'{"type": "payment_intent.succeeded"}'
        signature = "t=1234567890,v1=valid_signature"

        mock_stripe_service.handle_webhook.return_value = (
            True,
            {
                "event_type": "payment_intent.succeeded",
                "event_id": "evt_payment_123",
            },
        )

        with patch("apps.backend.api.routers.stripe.stripe_service", mock_stripe_service):
            response = test_client.post(
                "/api/v1/stripe/webhook", data=payload, headers={"Stripe-Signature": signature}
            )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["data"]["event_type"] == "payment_intent.succeeded"

    @pytest.mark.asyncio
    async def test_handle_webhook_subscription_updated(self, test_client, mock_stripe_service):
        """Test webhook for customer.subscription.updated event"""
        payload = b'{"type": "customer.subscription.updated"}'
        signature = "t=1234567890,v1=valid_signature"

        mock_stripe_service.handle_webhook.return_value = (
            True,
            {
                "event_type": "customer.subscription.updated",
                "event_id": "evt_sub_123",
            },
        )

        with patch("apps.backend.api.routers.stripe.stripe_service", mock_stripe_service):
            response = test_client.post(
                "/api/v1/stripe/webhook", data=payload, headers={"Stripe-Signature": signature}
            )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["data"]["event_type"] == "customer.subscription.updated"

    @pytest.mark.asyncio
    async def test_handle_webhook_processing_error(self, test_client, mock_stripe_service):
        """Test webhook processing with internal error"""
        payload = b'{"type": "checkout.session.completed"}'
        signature = "t=1234567890,v1=signature_here"

        mock_stripe_service.handle_webhook.side_effect = Exception("Database error")

        with patch("apps.backend.api.routers.stripe.stripe_service", mock_stripe_service):
            response = test_client.post(
                "/api/v1/stripe/webhook", data=payload, headers={"Stripe-Signature": signature}
            )

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        data = response.json()
        assert "Webhook processing failed" in data["detail"]


@pytest.mark.unit
class TestRequestModels:
    """Test Pydantic request model validation"""

    def test_checkout_session_request_validation(self):
        """Test CheckoutSessionRequest model validation"""
        from apps.backend.api.routers.stripe import CheckoutSessionRequest

        # Valid request
        request = CheckoutSessionRequest(
            price_id="price_123",
            mode="subscription",
            success_url="https://example.com/success",
            cancel_url="https://example.com/cancel",
        )
        assert request.price_id == "price_123"
        assert request.mode == "subscription"

        # Optional fields
        request2 = CheckoutSessionRequest(mode="payment")
        assert request2.price_id is None
        assert request2.line_items is None

    def test_subscription_request_validation(self):
        """Test SubscriptionRequest model validation"""
        from apps.backend.api.routers.stripe import SubscriptionRequest

        # Valid request
        request = SubscriptionRequest(
            price_id="price_123",
            trial_days=14,
        )
        assert request.price_id == "price_123"
        assert request.trial_days == 14

        # Default trial_days
        request2 = SubscriptionRequest(price_id="price_123")
        assert request2.trial_days == 14

    def test_subscription_update_request_validation(self):
        """Test SubscriptionUpdateRequest model validation"""
        from apps.backend.api.routers.stripe import SubscriptionUpdateRequest

        # All fields optional
        request = SubscriptionUpdateRequest()
        assert request.price_id is None
        assert request.cancel_at_period_end is None
        assert request.metadata is None

        # With values
        request2 = SubscriptionUpdateRequest(
            price_id="price_new", cancel_at_period_end=True, metadata={"reason": "upgrade"}
        )
        assert request2.price_id == "price_new"
        assert request2.cancel_at_period_end is True
