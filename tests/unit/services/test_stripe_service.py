"""
Unit Tests for Stripe Payment Service

Tests service layer functionality including:
- Customer management (create, get, update)
- Subscription lifecycle (create, update, cancel)
- Payment methods (attach, list)
- Payment intents and checkout sessions
- Invoices and refunds
- Webhook event handling
- Revenue analytics
- Caching and idempotency
- Multi-tenant organization filtering
"""

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, Mock, patch
from uuid import uuid4

import pytest
import stripe

# Import service under test
from apps.backend.services.stripe_service import StripeService


@pytest.fixture
def stripe_service():
    """Create Stripe service instance with mocked Stripe API"""
    with patch("apps.backend.services.stripe_service.stripe.api_key", "test_key"):
        service = StripeService()
        return service


@pytest.fixture
def mock_cache():
    """Mock cache for testing"""
    with patch("apps.backend.services.stripe_service.cache") as mock:
        mock.get = AsyncMock(return_value=None)
        mock.set = AsyncMock()
        mock.delete = AsyncMock()
        yield mock


class TestCustomerManagement:
    """Test customer creation and management."""

    @pytest.mark.asyncio
    @patch("stripe.Customer.create")
    async def test_create_customer_success(self, mock_create, stripe_service, mock_cache):
        """Test successful customer creation."""
        # Arrange
        mock_customer = Mock()
        mock_customer.id = "cus_test_123"
        mock_customer.email = "test@example.com"
        mock_customer.to_dict = Mock(
            return_value={"id": "cus_test_123", "email": "test@example.com"}
        )
        mock_create.return_value = mock_customer

        # Act
        result = await stripe_service.create_customer(
            user_id="user_123", email="test@example.com", name="Test User"
        )

        # Assert
        assert result["id"] == "cus_test_123"
        assert result["email"] == "test@example.com"
        mock_create.assert_called_once()
        mock_cache.set.assert_called_once()  # Customer cached

    @pytest.mark.asyncio
    @patch("stripe.Customer.create")
    async def test_create_customer_with_payment_method(
        self, mock_create, stripe_service, mock_cache
    ):
        """Test customer creation with payment method."""
        # Arrange
        mock_customer = Mock()
        mock_customer.to_dict = Mock(return_value={"id": "cus_123"})
        mock_create.return_value = mock_customer

        # Act
        await stripe_service.create_customer(
            user_id="user_123", email="test@example.com", payment_method_id="pm_123"
        )

        # Assert
        call_args = mock_create.call_args[1]
        assert call_args["payment_method"] == "pm_123"
        assert "invoice_settings" in call_args

    @pytest.mark.asyncio
    @patch("stripe.Customer.retrieve")
    async def test_get_customer_from_cache(self, mock_retrieve, stripe_service, mock_cache):
        """Test getting customer from cache."""
        # Arrange
        cached_customer = {"id": "cus_123", "email": "cached@example.com"}
        mock_cache.get.return_value = cached_customer

        # Act
        result = await stripe_service.get_customer("cus_123")

        # Assert
        assert result == cached_customer
        mock_retrieve.assert_not_called()  # Should not hit Stripe API

    @pytest.mark.asyncio
    @patch("stripe.Customer.retrieve")
    async def test_get_customer_from_stripe(self, mock_retrieve, stripe_service, mock_cache):
        """Test getting customer from Stripe API."""
        # Arrange
        mock_cache.get.return_value = None
        mock_customer = Mock()
        mock_customer.to_dict = Mock(return_value={"id": "cus_123"})
        mock_retrieve.return_value = mock_customer

        # Act
        result = await stripe_service.get_customer("cus_123")

        # Assert
        assert result["id"] == "cus_123"
        mock_cache.set.assert_called_once()  # Customer cached

    @pytest.mark.asyncio
    @patch("stripe.Customer.modify")
    async def test_update_customer(self, mock_modify, stripe_service, mock_cache):
        """Test customer update."""
        # Arrange
        mock_customer = Mock()
        mock_customer.to_dict = Mock(return_value={"id": "cus_123", "name": "Updated Name"})
        mock_modify.return_value = mock_customer

        # Act
        result = await stripe_service.update_customer("cus_123", name="Updated Name")

        # Assert
        assert result["name"] == "Updated Name"
        mock_cache.delete.assert_called_once()  # Cache invalidated


class TestSubscriptionManagement:
    """Test subscription lifecycle operations."""

    @pytest.mark.asyncio
    @patch("stripe.Subscription.create")
    async def test_create_subscription(self, mock_create, stripe_service):
        """Test subscription creation."""
        # Arrange
        mock_subscription = Mock()
        mock_subscription.id = "sub_123"
        mock_subscription.status = "trialing"
        mock_subscription.current_period_start = int(datetime.now().timestamp())
        mock_subscription.current_period_end = int(
            (datetime.now() + timedelta(days=30)).timestamp()
        )
        mock_subscription.trial_end = int((datetime.now() + timedelta(days=14)).timestamp())
        mock_subscription.__getitem__ = Mock(side_effect=lambda k: {"items": {"data": []}}[k])
        mock_subscription.latest_invoice = None
        mock_subscription.pending_setup_intent = None
        mock_create.return_value = mock_subscription

        # Act
        result = await stripe_service.create_subscription(
            customer_id="cus_123", price_id="price_123", trial_days=14
        )

        # Assert
        assert result["subscription_id"] == "sub_123"
        assert result["status"] == "trialing"
        mock_create.assert_called_once()

    @pytest.mark.asyncio
    @patch("stripe.Subscription.delete")
    async def test_cancel_subscription_immediately(self, mock_delete, stripe_service):
        """Test immediate subscription cancellation."""
        # Arrange
        mock_subscription = Mock()
        mock_subscription.to_dict = Mock(return_value={"id": "sub_123", "status": "canceled"})
        mock_delete.return_value = mock_subscription

        # Act
        result = await stripe_service.cancel_subscription("sub_123", immediately=True)

        # Assert
        assert result["status"] == "canceled"
        mock_delete.assert_called_once_with("sub_123")

    @pytest.mark.asyncio
    @patch("stripe.Subscription.modify")
    async def test_cancel_subscription_at_period_end(self, mock_modify, stripe_service):
        """Test cancellation at period end."""
        # Arrange
        mock_subscription = Mock()
        mock_subscription.to_dict = Mock(
            return_value={"id": "sub_123", "cancel_at_period_end": True}
        )
        mock_modify.return_value = mock_subscription

        # Act
        result = await stripe_service.cancel_subscription(
            "sub_123", immediately=False, reason="User request"
        )

        # Assert
        assert result["cancel_at_period_end"] == True
        call_args = mock_modify.call_args[1]
        assert call_args["cancel_at_period_end"] == True

    @pytest.mark.asyncio
    @patch("stripe.Subscription.retrieve")
    @patch("stripe.Subscription.modify")
    async def test_update_subscription(self, mock_modify, mock_retrieve, stripe_service):
        """Test subscription update/upgrade."""
        # Arrange
        mock_old_subscription = Mock()
        mock_old_subscription.__getitem__ = Mock(
            side_effect=lambda k: {"items": {"data": [Mock(id="si_123")]}}[k]
        )
        mock_retrieve.return_value = mock_old_subscription

        mock_new_subscription = Mock()
        mock_new_subscription.to_dict = Mock(return_value={"id": "sub_123", "plan": "new_plan"})
        mock_modify.return_value = mock_new_subscription

        # Act
        await stripe_service.update_subscription("sub_123", price_id="price_new")

        # Assert
        mock_modify.assert_called_once()
        call_args = mock_modify.call_args[1]
        assert "items" in call_args


class TestPaymentMethods:
    """Test payment method operations."""

    @pytest.mark.asyncio
    @patch("stripe.PaymentMethod.attach")
    @patch("stripe.Customer.modify")
    async def test_attach_payment_method(self, mock_customer_modify, mock_attach, stripe_service):
        """Test attaching payment method to customer."""
        # Arrange
        mock_pm = Mock()
        mock_pm.to_dict = Mock(return_value={"id": "pm_123", "type": "card"})
        mock_attach.return_value = mock_pm

        # Act
        result = await stripe_service.attach_payment_method(
            payment_method_id="pm_123", customer_id="cus_123", set_as_default=True
        )

        # Assert
        assert result["id"] == "pm_123"
        mock_attach.assert_called_once_with("pm_123", customer="cus_123")
        mock_customer_modify.assert_called_once()  # Set as default

    @pytest.mark.asyncio
    @patch("stripe.PaymentMethod.list")
    async def test_list_payment_methods(self, mock_list, stripe_service):
        """Test listing payment methods."""
        # Arrange
        mock_pm1 = Mock()
        mock_pm1.to_dict = Mock(return_value={"id": "pm_1", "type": "card"})
        mock_pm2 = Mock()
        mock_pm2.to_dict = Mock(return_value={"id": "pm_2", "type": "card"})

        mock_list.return_value = Mock(data=[mock_pm1, mock_pm2])

        # Act
        result = await stripe_service.list_payment_methods("cus_123")

        # Assert
        assert len(result) == 2
        assert result[0]["id"] == "pm_1"


class TestPaymentIntents:
    """Test payment intent operations."""

    @pytest.mark.asyncio
    @patch("stripe.PaymentIntent.create")
    async def test_create_payment_intent(self, mock_create, stripe_service):
        """Test payment intent creation."""
        # Arrange
        mock_intent = Mock()
        mock_intent.id = "pi_123"
        mock_intent.client_secret = "pi_123_secret_abc"
        mock_intent.amount = 1000
        mock_intent.currency = "usd"
        mock_intent.status = "requires_payment_method"
        mock_create.return_value = mock_intent

        # Act
        result = await stripe_service.create_payment_intent(
            amount=1000, currency="usd", customer_id="cus_123"
        )

        # Assert
        assert result["id"] == "pi_123"
        assert result["client_secret"] == "pi_123_secret_abc"
        assert result["amount"] == 1000

    @pytest.mark.asyncio
    @patch("stripe.PaymentIntent.retrieve")
    @patch("stripe.PaymentIntent.confirm")
    async def test_retry_payment_intent_success(self, mock_confirm, mock_retrieve, stripe_service):
        """Test retrying a failed payment intent."""
        # Arrange
        mock_intent = Mock()
        mock_intent.status = "requires_confirmation"
        mock_intent.to_dict = Mock(return_value={"id": "pi_123", "status": "requires_confirmation"})
        mock_retrieve.return_value = mock_intent

        mock_confirmed = Mock()
        mock_confirmed.status = "succeeded"
        mock_confirmed.to_dict = Mock(return_value={"id": "pi_123", "status": "succeeded"})
        mock_confirm.return_value = mock_confirmed

        # Act
        result = await stripe_service.retry_payment_intent("pi_123")

        # Assert
        assert result["success"] == True
        assert result["status"] == "succeeded"
        mock_confirm.assert_called_once()


class TestCheckoutSessions:
    """Test checkout session operations."""

    @pytest.mark.asyncio
    @patch("stripe.checkout.Session.create")
    async def test_create_checkout_session(self, mock_create, stripe_service):
        """Test checkout session creation."""
        # Arrange
        mock_session = Mock()
        mock_session.id = "cs_123"
        mock_session.url = "https://checkout.stripe.com/c/pay/cs_123"
        mock_session.expires_at = int((datetime.now() + timedelta(hours=1)).timestamp())
        mock_create.return_value = mock_session

        # Act
        result = await stripe_service.create_checkout_session(
            customer_id="cus_123",
            price_id="price_123",
            mode="subscription",
            trial_period_days=14,
        )

        # Assert
        assert result["id"] == "cs_123"
        assert result["url"].startswith("https://checkout.stripe.com")


class TestInvoices:
    """Test invoice operations."""

    @pytest.mark.asyncio
    @patch("stripe.Invoice.list")
    async def test_get_invoices(self, mock_list, stripe_service):
        """Test getting customer invoices."""
        # Arrange
        mock_invoice1 = Mock()
        mock_invoice1.id = "in_1"
        mock_invoice1.number = "INV-001"
        mock_invoice1.amount_paid = 1000
        mock_invoice1.amount_due = 0
        mock_invoice1.currency = "usd"
        mock_invoice1.status = "paid"
        mock_invoice1.created = int(datetime.now().timestamp())
        mock_invoice1.period_start = int(datetime.now().timestamp())
        mock_invoice1.period_end = int((datetime.now() + timedelta(days=30)).timestamp())
        mock_invoice1.invoice_pdf = "https://invoice.pdf"
        mock_invoice1.hosted_invoice_url = "https://invoice.url"

        mock_list.return_value = Mock(data=[mock_invoice1])

        # Act
        result = await stripe_service.get_invoices("cus_123", limit=10)

        # Assert
        assert len(result) == 1
        assert result[0]["id"] == "in_1"
        assert result[0]["status"] == "paid"


class TestRefunds:
    """Test refund operations."""

    @pytest.mark.asyncio
    @patch("stripe.Refund.create")
    async def test_create_refund(self, mock_create, stripe_service):
        """Test refund creation."""
        # Arrange
        mock_refund = Mock()
        mock_refund.id = "re_123"
        mock_refund.to_dict = Mock(
            return_value={"id": "re_123", "amount": 1000, "status": "succeeded"}
        )
        mock_create.return_value = mock_refund

        # Act
        result = await stripe_service.create_refund(
            charge_id="ch_123", amount=1000, reason="requested_by_customer"
        )

        # Assert
        assert result["id"] == "re_123"
        assert result["status"] == "succeeded"
        mock_create.assert_called_once()


class TestWebhookHandling:
    """Test webhook event processing."""

    @pytest.mark.asyncio
    @patch("stripe.Webhook.construct_event")
    async def test_handle_webhook_valid_signature(self, mock_construct, stripe_service, mock_cache):
        """Test webhook handling with valid signature."""
        # Arrange
        mock_event = {
            "id": "evt_123",
            "type": "customer.created",
            "data": {"object": {"id": "cus_123", "metadata": {}}},
        }
        mock_construct.return_value = mock_event

        # Act
        success, result = await stripe_service.handle_webhook(b'{"test": "data"}', "signature")

        # Assert
        assert success == True
        mock_construct.assert_called_once()

    @pytest.mark.asyncio
    @patch("stripe.Webhook.construct_event")
    async def test_handle_webhook_duplicate_event(self, mock_construct, stripe_service, mock_cache):
        """Test duplicate webhook event detection."""
        # Arrange
        mock_event = {
            "id": "evt_123",
            "type": "customer.created",
            "data": {"object": {"id": "cus_123", "metadata": {}}},
        }
        mock_construct.return_value = mock_event
        mock_cache.get.return_value = True  # Event already processed

        # Act
        success, result = await stripe_service.handle_webhook(b'{"test": "data"}', "signature")

        # Assert
        assert success == True
        assert result["status"] == "duplicate"


class TestRevenueAnalytics:
    """Test revenue metrics and analytics."""

    @pytest.mark.asyncio
    @patch("stripe.Charge.list")
    @patch("stripe.Subscription.list")
    async def test_get_revenue_metrics(self, mock_sub_list, mock_charge_list, stripe_service):
        """Test revenue metrics calculation."""
        # Arrange
        org_id = uuid4()

        # Mock charges
        mock_charge1 = Mock()
        mock_charge1.amount = 1000
        mock_charge1.amount_refunded = 0
        mock_charge1.paid = True
        mock_charge1.metadata = {"organization_id": str(org_id)}

        mock_charge_list.return_value = Mock(data=[mock_charge1])

        # Mock subscriptions
        mock_sub = Mock()
        mock_sub.status = "active"
        mock_sub.metadata = {"organization_id": str(org_id)}
        mock_item = Mock()
        mock_item.price = Mock(unit_amount=1000)
        mock_item.quantity = 1
        mock_sub.items = Mock(data=[mock_item])

        mock_sub_list.return_value = Mock(data=[mock_sub])

        # Act
        result = await stripe_service.get_revenue_metrics(
            start_date=datetime.now() - timedelta(days=30),
            end_date=datetime.now(),
            organization_id=org_id,
        )

        # Assert
        assert result["total_revenue"] == 10.0  # $10.00
        assert result["active_subscriptions"] == 1
        assert result["monthly_recurring_revenue"] == 10.0
        assert result["organization_id"] == str(org_id)


class TestErrorHandling:
    """Test error handling and edge cases."""

    @pytest.mark.asyncio
    @patch(
        "stripe.Customer.create",
        side_effect=stripe.error.CardError("Card declined", None, None),
    )
    async def test_create_customer_stripe_error(self, mock_create, stripe_service, mock_cache):
        """Test customer creation with Stripe error."""
        # Act & Assert
        with pytest.raises(stripe.error.CardError):
            await stripe_service.create_customer(user_id="user_123", email="test@example.com")

    @pytest.mark.asyncio
    @patch(
        "stripe.Customer.retrieve",
        side_effect=stripe.error.InvalidRequestError("Customer not found", None),
    )
    async def test_get_customer_not_found(self, mock_retrieve, stripe_service, mock_cache):
        """Test getting non-existent customer."""
        # Arrange
        mock_cache.get.return_value = None

        # Act
        result = await stripe_service.get_customer("cus_nonexistent")

        # Assert
        assert result is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
