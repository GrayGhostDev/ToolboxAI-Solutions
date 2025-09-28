"""
Unit Tests for Stripe Service
Tests all payment processing functionality
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from datetime import datetime, timedelta, timezone
import stripe
import stripe.error

from apps.backend.services.stripe_service import StripeService, stripe_service


@pytest.fixture
def mock_stripe():
    """Mock Stripe API"""
    with patch('apps.backend.services.stripe_service.stripe') as mock:
        yield mock


@pytest.fixture
def mock_settings():
    """Mock settings"""
    with patch('apps.backend.services.stripe_service.settings') as mock:
        mock.STRIPE_SECRET_KEY = 'sk_test_123'
        mock.STRIPE_WEBHOOK_SECRET = 'whsec_test_123'
        mock.STRIPE_PUBLISHABLE_KEY = 'pk_test_123'
        mock.STRIPE_STARTER_PRICE_ID = 'price_starter'
        mock.STRIPE_PRO_PRICE_ID = 'price_pro'
        mock.STRIPE_ENTERPRISE_PRICE_ID = 'price_enterprise'
        mock.FRONTEND_URL = 'https://test.com'
        yield mock


@pytest.fixture
def mock_cache():
    """Mock cache"""
    with patch('apps.backend.services.stripe_service.cache') as mock:
        mock.get = AsyncMock(return_value=None)
        mock.set = AsyncMock()
        mock.delete = AsyncMock()
        yield mock


@pytest.fixture
async def service(mock_settings, mock_cache):
    """Create service instance"""
    service = StripeService()
    return service


class TestStripeService:
    """Test Stripe service functionality"""

    @pytest.mark.asyncio
    async def test_init(self, mock_settings):
        """Test service initialization"""
        service = StripeService()

        assert service.api_key == 'sk_test_123'
        assert service.webhook_secret == 'whsec_test_123'
        assert service.publishable_key == 'pk_test_123'
        assert 'free' in service.subscription_tiers
        assert 'starter' in service.subscription_tiers
        assert 'professional' in service.subscription_tiers
        assert 'enterprise' in service.subscription_tiers

    @pytest.mark.asyncio
    async def test_create_customer(self, service, mock_stripe, mock_cache):
        """Test customer creation"""
        # Mock Stripe response
        mock_customer = MagicMock()
        mock_customer.id = 'cus_test123'
        mock_customer.to_dict.return_value = {
            'id': 'cus_test123',
            'email': 'test@example.com'
        }
        mock_stripe.Customer.create.return_value = mock_customer

        # Create customer
        result = await service.create_customer(
            user_id='user123',
            email='test@example.com',
            name='Test User',
            metadata={'source': 'test'}
        )

        # Verify
        assert result['id'] == 'cus_test123'
        assert result['email'] == 'test@example.com'
        mock_stripe.Customer.create.assert_called_once()

        # Verify caching
        mock_cache.set.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_customer_with_cached(self, service, mock_cache):
        """Test customer creation with cached data"""
        # Mock cached customer
        mock_cache.get.return_value = {
            'id': 'cus_cached',
            'email': 'cached@example.com'
        }

        result = await service.create_customer(
            user_id='user123',
            email='test@example.com'
        )

        # Should return cached customer
        assert result['id'] == 'cus_cached'

    @pytest.mark.asyncio
    async def test_create_subscription(self, service, mock_stripe):
        """Test subscription creation"""
        # Mock Stripe subscription
        mock_sub = MagicMock()
        mock_sub.id = 'sub_test123'
        mock_sub.status = 'active'
        mock_sub.current_period_start = 1234567890
        mock_sub.current_period_end = 1234567899
        mock_sub.trial_end = None
        mock_sub.latest_invoice = MagicMock()
        mock_sub.latest_invoice.payment_intent = MagicMock()
        mock_sub.latest_invoice.payment_intent.client_secret = 'pi_secret'
        mock_sub.latest_invoice.payment_intent.status = 'succeeded'
        mock_sub['items'] = {'data': [MagicMock()]}
        mock_sub.pending_setup_intent = None

        mock_stripe.Subscription.create.return_value = mock_sub

        # Create subscription
        result = await service.create_subscription(
            customer_id='cus_test123',
            price_id='price_starter',
            trial_days=14,
            metadata={'test': 'data'}
        )

        # Verify
        assert result['subscription_id'] == 'sub_test123'
        assert result['status'] == 'active'
        assert result['client_secret'] == 'pi_secret'
        assert result['payment_status'] == 'succeeded'
        mock_stripe.Subscription.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_cancel_subscription(self, service, mock_stripe):
        """Test subscription cancellation"""
        # Mock response
        mock_sub = MagicMock()
        mock_sub.to_dict.return_value = {'id': 'sub_test123', 'status': 'canceled'}
        mock_stripe.Subscription.delete.return_value = mock_sub

        # Cancel immediately
        result = await service.cancel_subscription(
            subscription_id='sub_test123',
            immediately=True,
            reason='User requested'
        )

        assert result['id'] == 'sub_test123'
        assert result['status'] == 'canceled'
        mock_stripe.Subscription.delete.assert_called_once_with('sub_test123')

    @pytest.mark.asyncio
    async def test_cancel_subscription_at_period_end(self, service, mock_stripe):
        """Test subscription cancellation at period end"""
        # Mock response
        mock_sub = MagicMock()
        mock_sub.to_dict.return_value = {
            'id': 'sub_test123',
            'cancel_at_period_end': True
        }
        mock_stripe.Subscription.modify.return_value = mock_sub

        # Cancel at period end
        result = await service.cancel_subscription(
            subscription_id='sub_test123',
            immediately=False,
            reason='User requested'
        )

        assert result['cancel_at_period_end'] == True
        mock_stripe.Subscription.modify.assert_called_once()

    @pytest.mark.asyncio
    async def test_attach_payment_method(self, service, mock_stripe):
        """Test attaching payment method"""
        # Mock response
        mock_pm = MagicMock()
        mock_pm.to_dict.return_value = {
            'id': 'pm_test123',
            'type': 'card'
        }
        mock_stripe.PaymentMethod.attach.return_value = mock_pm

        # Attach payment method
        result = await service.attach_payment_method(
            payment_method_id='pm_test123',
            customer_id='cus_test123',
            set_as_default=True
        )

        assert result['id'] == 'pm_test123'
        assert result['type'] == 'card'
        mock_stripe.PaymentMethod.attach.assert_called_once()
        mock_stripe.Customer.modify.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_payment_intent(self, service, mock_stripe):
        """Test payment intent creation"""
        # Mock response
        mock_intent = MagicMock()
        mock_intent.id = 'pi_test123'
        mock_intent.client_secret = 'pi_secret'
        mock_intent.amount = 5000
        mock_intent.currency = 'usd'
        mock_intent.status = 'requires_payment_method'

        mock_stripe.PaymentIntent.create.return_value = mock_intent

        # Create payment intent
        result = await service.create_payment_intent(
            amount=5000,
            currency='usd',
            customer_id='cus_test123',
            description='Test payment'
        )

        assert result['id'] == 'pi_test123'
        assert result['client_secret'] == 'pi_secret'
        assert result['amount'] == 5000
        assert result['status'] == 'requires_payment_method'
        mock_stripe.PaymentIntent.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_checkout_session(self, service, mock_stripe, mock_settings):
        """Test checkout session creation"""
        # Mock response
        mock_session = MagicMock()
        mock_session.id = 'cs_test123'
        mock_session.url = 'https://checkout.stripe.com/test'
        mock_session.expires_at = 1234567890

        mock_stripe.checkout.Session.create.return_value = mock_session

        # Create checkout session
        result = await service.create_checkout_session(
            customer_id='cus_test123',
            price_id='price_starter',
            mode='subscription',
            success_url='https://test.com/success',
            cancel_url='https://test.com/cancel'
        )

        assert result['id'] == 'cs_test123'
        assert result['url'] == 'https://checkout.stripe.com/test'
        assert result['expires_at'] == 1234567890
        mock_stripe.checkout.Session.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_webhook_valid(self, service, mock_stripe):
        """Test webhook handling with valid signature"""
        # Mock webhook event
        mock_event = {
            'id': 'evt_test123',
            'type': 'customer.created',
            'data': {
                'object': {
                    'id': 'cus_test123',
                    'metadata': {'user_id': 'user123'}
                }
            }
        }

        mock_stripe.Webhook.construct_event.return_value = mock_event

        # Handle webhook
        success, result = await service.handle_webhook(
            payload=b'test_payload',
            signature='test_signature'
        )

        assert success == True
        assert result['status'] == 'processed'
        assert result['customer_id'] == 'cus_test123'

    @pytest.mark.asyncio
    async def test_handle_webhook_invalid_signature(self, service, mock_stripe):
        """Test webhook handling with invalid signature"""
        # Import the actual Stripe error for proper testing
        from stripe.error import SignatureVerificationError

        # Mock signature verification error with correct parameters
        mock_stripe.Webhook.construct_event.side_effect = SignatureVerificationError(
            message='Invalid signature',
            sig_header='invalid_sig_header',
            http_body=b'test_payload'
        )

        # Handle webhook
        success, result = await service.handle_webhook(
            payload=b'test_payload',
            signature='invalid_signature'
        )

        assert success == False
        assert result['error'] == 'Invalid signature'

    @pytest.mark.asyncio
    async def test_create_refund(self, service, mock_stripe):
        """Test refund creation"""
        # Mock response
        mock_refund = MagicMock()
        mock_refund.to_dict.return_value = {
            'id': 'ref_test123',
            'amount': 5000,
            'status': 'succeeded'
        }
        mock_stripe.Refund.create.return_value = mock_refund

        # Create refund
        result = await service.create_refund(
            charge_id='ch_test123',
            amount=5000,
            reason='requested_by_customer'
        )

        assert result['id'] == 'ref_test123'
        assert result['amount'] == 5000
        assert result['status'] == 'succeeded'
        mock_stripe.Refund.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_revenue_metrics(self, service, mock_stripe):
        """Test revenue metrics calculation"""
        # Mock charges
        mock_charges = MagicMock()
        mock_charges.data = [
            MagicMock(amount=10000, paid=True, amount_refunded=0),
            MagicMock(amount=5000, paid=True, amount_refunded=1000),
            MagicMock(amount=2000, paid=False, amount_refunded=0)
        ]
        mock_stripe.Charge.list.return_value = mock_charges

        # Mock subscriptions
        mock_subs = MagicMock()
        mock_sub = MagicMock()
        mock_sub.status = 'active'
        mock_sub.items.data = [MagicMock()]
        mock_sub.items.data[0].price.unit_amount = 2999
        mock_sub.items.data[0].quantity = 1
        mock_subs.data = [mock_sub]
        mock_stripe.Subscription.list.return_value = mock_subs

        # Get metrics
        result = await service.get_revenue_metrics(
            start_date=datetime.now(timezone.utc) - timedelta(days=30),
            end_date=datetime.now(timezone.utc)
        )

        assert result['total_revenue'] == 150.00  # (10000 + 5000) / 100
        assert result['total_refunded'] == 10.00  # 1000 / 100
        assert result['net_revenue'] == 140.00
        assert result['transaction_count'] == 2
        assert result['active_subscriptions'] == 1
        assert result['monthly_recurring_revenue'] == 29.99  # 2999 / 100

    @pytest.mark.asyncio
    async def test_stripe_error_handling(self, service, mock_stripe):
        """Test Stripe error handling"""
        # Import actual Stripe errors for proper exception handling
        from stripe.error import APIError, StripeError

        # Mock Stripe error - APIError inherits from StripeError
        mock_stripe.Customer.create.side_effect = APIError('Test error')

        # Should raise error
        with pytest.raises(StripeError):
            await service.create_customer(
                user_id='user123',
                email='test@example.com'
            )


# Integration tests for webhook event handlers
class TestWebhookHandlers:
    """Test webhook event handlers"""

    @pytest.mark.asyncio
    async def test_handle_subscription_created(self, service):
        """Test subscription.created webhook handler"""
        event = {
            'data': {
                'object': {
                    'id': 'sub_test123',
                    'customer': 'cus_test123',
                    'status': 'active'
                }
            }
        }

        result = await service._handle_subscription_created(event)

        assert result['status'] == 'processed'
        assert result['subscription_id'] == 'sub_test123'

    @pytest.mark.asyncio
    async def test_handle_payment_succeeded(self, service):
        """Test payment_intent.succeeded webhook handler"""
        event = {
            'data': {
                'object': {
                    'id': 'pi_test123',
                    'amount': 5000,
                    'currency': 'usd'
                }
            }
        }

        result = await service._handle_payment_succeeded(event)

        assert result['status'] == 'processed'
        assert result['payment_intent_id'] == 'pi_test123'

    @pytest.mark.asyncio
    async def test_handle_invoice_paid(self, service):
        """Test invoice.paid webhook handler"""
        event = {
            'data': {
                'object': {
                    'id': 'inv_test123',
                    'amount_paid': 5000,
                    'subscription': 'sub_test123'
                }
            }
        }

        result = await service._handle_invoice_paid(event)

        assert result['status'] == 'processed'
        assert result['invoice_id'] == 'inv_test123'