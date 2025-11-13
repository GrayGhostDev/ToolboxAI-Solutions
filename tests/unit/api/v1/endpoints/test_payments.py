"""
Unit Tests for Payment API Endpoints

Tests payment functionality including:
- Customer creation and management
- Subscription CRUD operations
- Payment methods
- Payment intents and checkout
- Webhooks
- Invoices and refunds
- Revenue analytics
- Multi-tenant isolation
"""

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, Mock, patch
from uuid import uuid4

import pytest
from fastapi import HTTPException

# Import request models
# Import endpoint functions
from apps.backend.api.v1.endpoints.payments import (
    AttachPaymentMethodRequest,
    CreateCheckoutSessionRequest,
    CreateCustomerRequest,
    CreatePaymentIntentRequest,
    CreateRefundRequest,
    CreateSubscriptionRequest,
    UpdateSubscriptionRequest,
    attach_payment_method,
    cancel_subscription,
    create_checkout_session,
    create_customer,
    create_payment_intent,
    create_refund,
    create_subscription,
    get_invoices,
    get_my_customer,
    get_my_subscriptions,
    get_payment_methods,
    get_revenue_analytics,
    stripe_webhook,
    update_subscription,
)


@pytest.fixture
def mock_org_id():
    """Mock organization ID for multi-tenant testing"""
    return uuid4()


@pytest.fixture
def mock_user():
    """Mock authenticated user"""
    user = Mock()
    user.id = uuid4()
    user.email = "test@example.com"
    user.username = "testuser"
    user.full_name = "Test User"
    user.role = "student"
    return user


@pytest.fixture
def mock_admin_user():
    """Mock admin user"""
    user = Mock()
    user.id = uuid4()
    user.email = "admin@example.com"
    user.username = "admin"
    user.full_name = "Admin User"
    user.role = "admin"
    return user


@pytest.fixture
def mock_db_session():
    """Mock database session"""
    session = AsyncMock()
    session.execute = AsyncMock()
    session.commit = AsyncMock()
    session.add = Mock()
    return session


@pytest.fixture
def mock_stripe_service():
    """Mock Stripe service"""
    with patch("apps.backend.api.v1.endpoints.payments.stripe_service") as mock:
        yield mock


class TestCustomerEndpoints:
    """Test customer creation and retrieval endpoints."""

    @pytest.mark.asyncio
    async def test_create_customer_success(
        self, mock_db_session, mock_user, mock_org_id, mock_stripe_service
    ):
        """Test successful customer creation."""
        # Arrange
        request = CreateCustomerRequest(email="test@example.com", name="Test User")

        # Mock no existing customer
        mock_result = Mock()
        mock_result.scalar_one_or_none = Mock(return_value=None)
        mock_db_session.execute.return_value = mock_result

        # Mock Stripe response
        mock_stripe_service.create_customer = AsyncMock(
            return_value={"id": "cus_123", "email": "test@example.com"}
        )

        # Act
        result = await create_customer(
            request=request, org_id=mock_org_id, current_user=mock_user, db=mock_db_session
        )

        # Assert
        assert result["message"] == "Customer created successfully"
        assert result["customer_id"] == "cus_123"
        mock_db_session.add.assert_called_once()
        mock_db_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_customer_already_exists(
        self, mock_db_session, mock_user, mock_org_id, mock_stripe_service
    ):
        """Test customer creation when customer already exists."""
        # Arrange
        request = CreateCustomerRequest(email="test@example.com")

        # Mock existing customer
        existing_customer = Mock()
        existing_customer.stripe_customer_id = "cus_existing"
        mock_result = Mock()
        mock_result.scalar_one_or_none = Mock(return_value=existing_customer)
        mock_db_session.execute.return_value = mock_result

        # Act
        result = await create_customer(
            request=request, org_id=mock_org_id, current_user=mock_user, db=mock_db_session
        )

        # Assert
        assert result["message"] == "Customer already exists"
        assert result["customer_id"] == "cus_existing"
        mock_stripe_service.create_customer.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_my_customer_success(
        self, mock_db_session, mock_user, mock_org_id, mock_stripe_service
    ):
        """Test successful customer retrieval."""
        # Arrange
        customer = Mock()
        customer.stripe_customer_id = "cus_123"
        customer.subscriptions = []

        mock_result = Mock()
        mock_result.scalar_one_or_none = Mock(return_value=customer)
        mock_db_session.execute.return_value = mock_result

        mock_stripe_service.get_customer = AsyncMock(return_value={"id": "cus_123"})

        # Act
        result = await get_my_customer(
            org_id=mock_org_id, current_user=mock_user, db=mock_db_session
        )

        # Assert
        assert "customer" in result
        assert result["customer"]["id"] == "cus_123"

    @pytest.mark.asyncio
    async def test_get_my_customer_not_found(self, mock_db_session, mock_user, mock_org_id):
        """Test customer retrieval when customer doesn't exist."""
        # Arrange
        mock_result = Mock()
        mock_result.scalar_one_or_none = Mock(return_value=None)
        mock_db_session.execute.return_value = mock_result

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await get_my_customer(org_id=mock_org_id, current_user=mock_user, db=mock_db_session)

        assert exc_info.value.status_code == 404


class TestSubscriptionEndpoints:
    """Test subscription CRUD operations."""

    @pytest.mark.asyncio
    async def test_create_subscription_success(
        self, mock_db_session, mock_user, mock_org_id, mock_stripe_service
    ):
        """Test successful subscription creation."""
        # Arrange
        request = CreateSubscriptionRequest(price_id="price_123", trial_days=14)

        # Mock customer exists
        customer = Mock()
        customer.id = uuid4()
        customer.stripe_customer_id = "cus_123"
        mock_result = Mock()
        mock_result.scalar_one_or_none = Mock(return_value=customer)
        mock_db_session.execute.return_value = mock_result

        # Mock Stripe subscription
        current_time = int(datetime.now().timestamp())
        mock_stripe_service.create_subscription = AsyncMock(
            return_value={
                "subscription_id": "sub_123",
                "status": "trialing",
                "current_period_start": current_time,
                "current_period_end": current_time + 2592000,  # 30 days
                "trial_end": current_time + 1209600,  # 14 days
            }
        )

        # Act
        result = await create_subscription(
            request=request, org_id=mock_org_id, current_user=mock_user, db=mock_db_session
        )

        # Assert
        assert result["message"] == "Subscription created successfully"
        assert result["subscription"]["subscription_id"] == "sub_123"
        mock_db_session.add.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_subscription_no_customer(self, mock_db_session, mock_user, mock_org_id):
        """Test subscription creation without customer."""
        # Arrange
        request = CreateSubscriptionRequest(price_id="price_123")

        mock_result = Mock()
        mock_result.scalar_one_or_none = Mock(return_value=None)
        mock_db_session.execute.return_value = mock_result

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await create_subscription(
                request=request, org_id=mock_org_id, current_user=mock_user, db=mock_db_session
            )

        assert exc_info.value.status_code == 400
        assert "create a customer account first" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_get_my_subscriptions(self, mock_db_session, mock_user, mock_org_id):
        """Test retrieving user subscriptions."""
        # Arrange
        customer = Mock()
        customer.id = uuid4()

        subscription = Mock()
        subscription.stripe_subscription_id = "sub_123"
        subscription.status = "active"
        subscription.tier = "professional"
        subscription.current_period_start = datetime.now()
        subscription.current_period_end = datetime.now() + timedelta(days=30)
        subscription.cancel_at_period_end = False
        subscription.trial_end = None

        # Mock database calls
        customer_result = Mock()
        customer_result.scalar_one_or_none = Mock(return_value=customer)

        subs_result = Mock()
        subs_result.scalars().all = Mock(return_value=[subscription])

        mock_db_session.execute.side_effect = [customer_result, subs_result]

        # Act
        result = await get_my_subscriptions(
            org_id=mock_org_id, current_user=mock_user, db=mock_db_session
        )

        # Assert
        assert len(result["subscriptions"]) == 1
        assert result["subscriptions"][0]["id"] == "sub_123"
        assert result["subscriptions"][0]["status"] == "active"

    @pytest.mark.asyncio
    async def test_update_subscription_cancel(
        self, mock_db_session, mock_user, mock_org_id, mock_stripe_service
    ):
        """Test subscription cancellation via update."""
        # Arrange
        request = UpdateSubscriptionRequest(cancel_at_period_end=True)

        subscription = Mock()
        subscription.cancel_at_period_end = False
        mock_result = Mock()
        mock_result.scalar_one_or_none = Mock(return_value=subscription)
        mock_db_session.execute.return_value = mock_result

        mock_stripe_service.cancel_subscription = AsyncMock(return_value={"status": "canceled"})

        # Act
        result = await update_subscription(
            subscription_id="sub_123",
            request=request,
            org_id=mock_org_id,
            current_user=mock_user,
            db=mock_db_session,
        )

        # Assert
        assert result["message"] == "Subscription updated successfully"
        assert subscription.cancel_at_period_end == True
        mock_stripe_service.cancel_subscription.assert_called_once()

    @pytest.mark.asyncio
    async def test_cancel_subscription_immediately(
        self, mock_db_session, mock_user, mock_org_id, mock_stripe_service
    ):
        """Test immediate subscription cancellation."""
        # Arrange
        subscription = Mock()
        subscription.status = "active"
        subscription.canceled_at = None

        mock_result = Mock()
        mock_result.scalar_one_or_none = Mock(return_value=subscription)
        mock_db_session.execute.return_value = mock_result

        mock_stripe_service.cancel_subscription = AsyncMock(return_value={"status": "canceled"})

        # Act
        result = await cancel_subscription(
            subscription_id="sub_123",
            immediately=True,
            org_id=mock_org_id,
            current_user=mock_user,
            db=mock_db_session,
        )

        # Assert
        assert result["message"] == "Subscription cancelled successfully"
        assert subscription.status == "canceled"
        assert subscription.canceled_at is not None


class TestPaymentMethodEndpoints:
    """Test payment method operations."""

    @pytest.mark.asyncio
    async def test_attach_payment_method_success(
        self, mock_db_session, mock_user, mock_org_id, mock_stripe_service
    ):
        """Test successful payment method attachment."""
        # Arrange
        request = AttachPaymentMethodRequest(payment_method_id="pm_123", set_as_default=True)

        customer = Mock()
        customer.stripe_customer_id = "cus_123"
        mock_result = Mock()
        mock_result.scalar_one_or_none = Mock(return_value=customer)
        mock_db_session.execute.return_value = mock_result

        mock_stripe_service.attach_payment_method = AsyncMock(return_value={"id": "pm_123"})

        # Act
        result = await attach_payment_method(
            request=request, org_id=mock_org_id, current_user=mock_user, db=mock_db_session
        )

        # Assert
        assert result["message"] == "Payment method attached successfully"
        mock_stripe_service.attach_payment_method.assert_called_once_with(
            payment_method_id="pm_123", customer_id="cus_123", set_as_default=True
        )

    @pytest.mark.asyncio
    async def test_get_payment_methods(
        self, mock_db_session, mock_user, mock_org_id, mock_stripe_service
    ):
        """Test retrieving payment methods."""
        # Arrange
        customer = Mock()
        customer.stripe_customer_id = "cus_123"
        mock_result = Mock()
        mock_result.scalar_one_or_none = Mock(return_value=customer)
        mock_db_session.execute.return_value = mock_result

        mock_stripe_service.list_payment_methods = AsyncMock(
            return_value=[{"id": "pm_1", "type": "card"}, {"id": "pm_2", "type": "card"}]
        )

        # Act
        result = await get_payment_methods(
            org_id=mock_org_id, current_user=mock_user, db=mock_db_session
        )

        # Assert
        assert len(result["payment_methods"]) == 2


class TestPaymentIntentEndpoints:
    """Test payment intent and checkout operations."""

    @pytest.mark.asyncio
    async def test_create_payment_intent_success(
        self, mock_db_session, mock_user, mock_org_id, mock_stripe_service
    ):
        """Test successful payment intent creation."""
        # Arrange
        request = CreatePaymentIntentRequest(
            amount=1000, currency="usd", description="Test payment"  # $10.00
        )

        customer = Mock()
        customer.stripe_customer_id = "cus_123"
        mock_result = Mock()
        mock_result.scalar_one_or_none = Mock(return_value=customer)
        mock_db_session.execute.return_value = mock_result

        mock_stripe_service.create_payment_intent = AsyncMock(
            return_value={"id": "pi_123", "client_secret": "pi_123_secret_abc"}
        )

        # Act
        result = await create_payment_intent(
            request=request, org_id=mock_org_id, current_user=mock_user, db=mock_db_session
        )

        # Assert
        assert result["message"] == "Payment intent created"
        assert result["payment_intent"]["id"] == "pi_123"

    @pytest.mark.asyncio
    async def test_create_payment_intent_minimum_amount(self):
        """Test payment intent validation for minimum amount."""
        # Assert minimum amount validation
        with pytest.raises(Exception):  # Pydantic validation error
            CreatePaymentIntentRequest(amount=25, currency="usd")  # Below minimum of 50

    @pytest.mark.asyncio
    async def test_create_checkout_session(
        self, mock_db_session, mock_user, mock_org_id, mock_stripe_service
    ):
        """Test checkout session creation."""
        # Arrange
        request = CreateCheckoutSessionRequest(
            price_id="price_123",
            mode="subscription",
            success_url="https://example.com/success",
            cancel_url="https://example.com/cancel",
            trial_days=14,
        )

        customer = Mock()
        customer.stripe_customer_id = "cus_123"
        mock_result = Mock()
        mock_result.scalar_one_or_none = Mock(return_value=customer)
        mock_db_session.execute.return_value = mock_result

        mock_stripe_service.create_checkout_session = AsyncMock(
            return_value={"id": "cs_123", "url": "https://checkout.stripe.com/c/pay/cs_123"}
        )

        # Act
        result = await create_checkout_session(
            request=request, org_id=mock_org_id, current_user=mock_user, db=mock_db_session
        )

        # Assert
        assert result["message"] == "Checkout session created"
        assert result["checkout_url"] == "https://checkout.stripe.com/c/pay/cs_123"
        assert result["session_id"] == "cs_123"


class TestWebhookEndpoints:
    """Test Stripe webhook handling."""

    @pytest.mark.asyncio
    async def test_stripe_webhook_success(self, mock_db_session, mock_stripe_service):
        """Test successful webhook processing."""
        # Arrange
        mock_request = Mock()
        mock_request.body = AsyncMock(return_value=b'{"type":"payment_intent.succeeded"}')

        mock_stripe_service.handle_webhook = AsyncMock(
            return_value=(True, {"event_type": "payment_intent.succeeded", "data": {}})
        )

        # Act
        result = await stripe_webhook(
            request=mock_request,
            stripe_signature="test_signature",
            background_tasks=Mock(),
            db=mock_db_session,
        )

        # Assert
        assert result.status_code == 200

    @pytest.mark.asyncio
    async def test_stripe_webhook_invalid_signature(self, mock_db_session, mock_stripe_service):
        """Test webhook with invalid signature."""
        # Arrange
        mock_request = Mock()
        mock_request.body = AsyncMock(return_value=b'{"type":"test"}')

        mock_stripe_service.handle_webhook = AsyncMock(
            return_value=(False, {"error": "Invalid signature"})
        )

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await stripe_webhook(
                request=mock_request,
                stripe_signature="invalid",
                background_tasks=Mock(),
                db=mock_db_session,
            )

        assert exc_info.value.status_code == 400


class TestInvoiceEndpoints:
    """Test invoice retrieval."""

    @pytest.mark.asyncio
    async def test_get_invoices_success(
        self, mock_db_session, mock_user, mock_org_id, mock_stripe_service
    ):
        """Test successful invoice retrieval."""
        # Arrange
        customer = Mock()
        customer.stripe_customer_id = "cus_123"
        mock_result = Mock()
        mock_result.scalar_one_or_none = Mock(return_value=customer)
        mock_db_session.execute.return_value = mock_result

        mock_stripe_service.get_invoices = AsyncMock(
            return_value=[{"id": "in_1", "amount_due": 1000}, {"id": "in_2", "amount_due": 2000}]
        )

        # Act
        result = await get_invoices(
            limit=10, org_id=mock_org_id, current_user=mock_user, db=mock_db_session
        )

        # Assert
        assert len(result["invoices"]) == 2

    @pytest.mark.asyncio
    async def test_get_invoices_no_customer(self, mock_db_session, mock_user, mock_org_id):
        """Test invoice retrieval without customer."""
        # Arrange
        mock_result = Mock()
        mock_result.scalar_one_or_none = Mock(return_value=None)
        mock_db_session.execute.return_value = mock_result

        # Act
        result = await get_invoices(
            limit=10, org_id=mock_org_id, current_user=mock_user, db=mock_db_session
        )

        # Assert
        assert result["invoices"] == []


class TestRefundEndpoints:
    """Test refund operations (admin only)."""

    @pytest.mark.asyncio
    async def test_create_refund_admin_success(
        self, mock_db_session, mock_admin_user, mock_org_id, mock_stripe_service
    ):
        """Test successful refund creation by admin."""
        # Arrange
        request = CreateRefundRequest(
            charge_id="ch_123", amount=1000, reason="requested_by_customer"
        )

        mock_stripe_service.create_refund = AsyncMock(
            return_value={"id": "re_123", "amount": 1000, "status": "succeeded"}
        )

        # Act
        result = await create_refund(
            request=request, org_id=mock_org_id, current_user=mock_admin_user, db=mock_db_session
        )

        # Assert
        assert result["message"] == "Refund created successfully"
        assert result["refund"]["id"] == "re_123"

    @pytest.mark.asyncio
    async def test_create_refund_non_admin_denied(self, mock_db_session, mock_user, mock_org_id):
        """Test refund creation denied for non-admin."""
        # Arrange
        request = CreateRefundRequest(charge_id="ch_123")

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await create_refund(
                request=request, org_id=mock_org_id, current_user=mock_user, db=mock_db_session
            )

        assert exc_info.value.status_code == 403
        assert "Admin access required" in str(exc_info.value.detail)


class TestRevenueAnalytics:
    """Test revenue analytics (admin only)."""

    @pytest.mark.asyncio
    async def test_get_revenue_analytics_admin(
        self, mock_admin_user, mock_org_id, mock_stripe_service
    ):
        """Test revenue analytics retrieval by admin."""
        # Arrange
        start_date = datetime(2025, 10, 1)
        end_date = datetime(2025, 10, 31)

        mock_stripe_service.get_revenue_metrics = AsyncMock(
            return_value={
                "total_revenue": 50000,
                "subscription_revenue": 40000,
                "one_time_revenue": 10000,
            }
        )

        # Act
        result = await get_revenue_analytics(
            start_date=start_date,
            end_date=end_date,
            org_id=mock_org_id,
            current_user=mock_admin_user,
        )

        # Assert
        assert result["metrics"]["total_revenue"] == 50000
        assert result["organization_id"] == str(mock_org_id)

    @pytest.mark.asyncio
    async def test_get_revenue_analytics_non_admin(self, mock_user, mock_org_id):
        """Test revenue analytics denied for non-admin."""
        # Arrange
        start_date = datetime(2025, 10, 1)
        end_date = datetime(2025, 10, 31)

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await get_revenue_analytics(
                start_date=start_date, end_date=end_date, org_id=mock_org_id, current_user=mock_user
            )

        assert exc_info.value.status_code == 403


class TestMultiTenantIsolation:
    """Test multi-tenant security and data isolation."""

    @pytest.mark.asyncio
    async def test_customer_scoped_to_organization(
        self, mock_db_session, mock_user, mock_org_id, mock_stripe_service
    ):
        """Test that customers are properly scoped to organization."""
        # Arrange
        request = CreateCustomerRequest(email="test@example.com")

        mock_result = Mock()
        mock_result.scalar_one_or_none = Mock(return_value=None)
        mock_db_session.execute.return_value = mock_result

        mock_stripe_service.create_customer = AsyncMock(return_value={"id": "cus_123"})

        # Act
        await create_customer(
            request=request, org_id=mock_org_id, current_user=mock_user, db=mock_db_session
        )

        # Assert - verify RLS context was set
        rls_call = mock_db_session.execute.call_args_list[0]
        assert "SET app.current_organization_id" in str(rls_call)

        # Verify organization_id in metadata
        create_call = mock_stripe_service.create_customer.call_args
        assert "organization_id" in create_call[1]["metadata"]
        assert create_call[1]["metadata"]["organization_id"] == str(mock_org_id)

    @pytest.mark.asyncio
    async def test_subscription_cross_org_access_denied(
        self, mock_db_session, mock_user, mock_org_id
    ):
        """Test that users cannot access subscriptions from other organizations."""
        # Arrange
        request = UpdateSubscriptionRequest(cancel_at_period_end=True)

        # Mock: subscription not found for this org (even if it exists in another org)
        mock_result = Mock()
        mock_result.scalar_one_or_none = Mock(return_value=None)
        mock_db_session.execute.return_value = mock_result

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await update_subscription(
                subscription_id="sub_123",
                request=request,
                org_id=mock_org_id,
                current_user=mock_user,
                db=mock_db_session,
            )

        assert exc_info.value.status_code == 404
        assert "not found or you don't have access" in str(exc_info.value.detail)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
