"""
Unit Tests for Email Service
Tests all email functionality with SendGrid for Render/Supabase deployment
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock, MagicMock, call
from datetime import datetime, timezone
import json

from apps.backend.services import email_service
from apps.backend.services.email_service import (
    EmailService, EmailProvider,
    EmailType, EmailPriority
)


@pytest.fixture
def mock_bleach():
    """Mock bleach module"""
    # Mock at the module level where bleach is used
    mock_bleach_module = MagicMock()
    mock_bleach_module.clean = MagicMock(side_effect=lambda x, **kwargs: x)  # Return input unchanged

    # Mock BeautifulSoup too
    mock_bs = MagicMock()
    mock_soup_instance = MagicMock()
    mock_soup_instance.get_text.return_value = "Mocked text content"
    mock_bs.return_value = mock_soup_instance

    with patch.object(email_service, 'HTML_PROCESSING_AVAILABLE', True):
        with patch.object(email_service, 'bleach', mock_bleach_module):
            with patch.object(email_service, 'BeautifulSoup', mock_bs):
                yield mock_bleach_module


@pytest.fixture
def mock_sendgrid():
    """Mock SendGrid client"""
    mock_client = MagicMock()

    # Mock the send method to return a successful response
    mock_response = MagicMock()
    mock_response.status_code = 202
    mock_response.headers = {'X-Message-Id': 'msg_123'}
    mock_client.send.return_value = mock_response

    # Mock client methods for suppression list
    mock_client.client = MagicMock()
    mock_client.client.suppression = MagicMock()
    mock_client.client.suppression.group_suppressions = MagicMock()
    mock_client.client.suppression.group_suppressions.post = MagicMock()

    # Patch SENDGRID_AVAILABLE and the client creation
    with patch.object(email_service, 'SENDGRID_AVAILABLE', True):
        with patch.object(email_service, 'Mail', MagicMock):
            with patch.object(email_service, 'Email', MagicMock):
                with patch.object(email_service, 'To', MagicMock):
                    with patch.object(email_service, 'Content', MagicMock):
                        with patch.object(email_service, 'Attachment', MagicMock):
                            with patch.object(email_service, 'FileContent', MagicMock):
                                with patch.object(email_service, 'FileName', MagicMock):
                                    with patch.object(email_service, 'FileType', MagicMock):
                                        with patch.object(email_service, 'Disposition', MagicMock):
                                            with patch('apps.backend.services.email_service.EmailService._create_sendgrid_client', return_value=mock_client):
                                                yield mock_client


# AWS SES mock removed - using SendGrid only for Render/Supabase deployment


@pytest.fixture
def mock_settings():
    """Mock settings"""
    with patch('apps.backend.services.email_service.settings') as mock:
        mock.EMAIL_PROVIDER = EmailProvider.SENDGRID
        mock.SENDGRID_API_KEY = 'SG.test_key'
        mock.DEFAULT_FROM_EMAIL = 'noreply@test.com'
        mock.DEFAULT_FROM_NAME = 'Test App'
        mock.EMAIL_ENABLE_TRACKING = True
        mock.EMAIL_ENABLE_UNSUBSCRIBE = True
        mock.FRONTEND_URL = 'https://test.com'
        yield mock


@pytest.fixture
def mock_cache():
    """Mock cache"""
    with patch('apps.backend.services.email_service.cache') as mock:
        mock.get = AsyncMock(return_value=None)
        mock.set = AsyncMock()
        mock.delete = AsyncMock()
        yield mock


@pytest.fixture
def mock_template_env():
    """Mock Jinja2 template environment"""
    with patch('apps.backend.services.email_service.Environment') as mock:
        mock_env = MagicMock()
        mock_template = MagicMock()
        mock_template.render_async = AsyncMock(
            return_value='<html>Test HTML</html>'
        )
        mock_env.get_template.return_value = mock_template
        mock.return_value = mock_env
        yield mock_env


@pytest.fixture
async def service(mock_settings, mock_sendgrid, mock_cache, mock_bleach, mock_template_env):
    """Create service instance"""
    service = EmailService()
    # Ensure sg_client is set from the mock
    service.sg_client = mock_sendgrid
    # Set template environment
    service.template_env = mock_template_env
    return service


class TestEmailService:
    """Test Email service functionality"""

    @pytest.mark.asyncio
    async def test_init(self, mock_settings):
        """Test service initialization"""
        service = EmailService()

        assert service.provider == EmailProvider.SENDGRID
        assert service.from_email == 'noreply@test.com'
        assert service.from_name == 'Test App'
        assert service.enable_tracking == True
        assert service.enable_unsubscribe == True

    @pytest.mark.asyncio
    async def test_send_email_with_sendgrid(self, service, mock_sendgrid):
        """Test sending email with SendGrid"""
        # Mock SendGrid response
        mock_response = MagicMock()
        mock_response.status_code = 202
        mock_response.headers = {'X-Message-Id': 'msg_123'}
        service.sg_client.send.return_value = mock_response

        # Send email
        result = await service.send_email(
            to_emails=['user@example.com'],
            subject='Test Email',
            html_content='<p>Test content</p>',
            text_content='Test content',
            categories=['test'],
            priority=EmailPriority.HIGH
        )

        # Verify
        assert result['success'] == True
        assert result['message_id'] == 'msg_123'
        assert result['provider'] == EmailProvider.SENDGRID
        service.sg_client.send.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_email_with_multiple_recipients(self, service, mock_sendgrid):
        """Test sending email to multiple recipients"""
        # Mock SendGrid response
        mock_response = MagicMock()
        mock_response.status_code = 202
        mock_response.headers = {'X-Message-Id': 'msg_456'}
        service.sg_client.send.return_value = mock_response

        # Send email
        result = await service.send_email(
            to_emails=['user1@example.com', 'user2@example.com'],
            subject='Test Email',
            html_content='<p>Test content</p>',
            cc=['cc@example.com'],
            bcc=['bcc@example.com']
        )

        assert result['success'] == True
        assert result['message_id'] == 'msg_456'

    # AWS SES test removed - using SendGrid only for Render/Supabase deployment

    @pytest.mark.asyncio
    async def test_send_email_with_template(self, service, mock_sendgrid, mock_template_env):
        """Test sending email with template"""
        # Mock template rendering
        mock_template = MagicMock()
        mock_template.render_async = AsyncMock(
            side_effect=['<html>Rendered HTML</html>', 'Rendered Text']
        )
        mock_template_env.get_template.return_value = mock_template

        # Mock SendGrid response
        mock_response = MagicMock()
        mock_response.status_code = 202
        mock_response.headers = {'X-Message-Id': 'msg_789'}
        service.sg_client.send.return_value = mock_response

        # Send email with template
        result = await service.send_email(
            to_emails='user@example.com',
            subject='Welcome',
            template_name='welcome',
            template_context={
                'user_name': 'John Doe',
                'verification_url': 'https://test.com/verify'
            }
        )

        assert result['success'] == True
        mock_template_env.get_template.assert_called()

    @pytest.mark.asyncio
    async def test_send_email_with_attachments(self, service, mock_sendgrid):
        """Test sending email with attachments"""
        # Mock SendGrid response
        mock_response = MagicMock()
        mock_response.status_code = 202
        mock_response.headers = {'X-Message-Id': 'msg_attach'}
        service.sg_client.send.return_value = mock_response

        # Send email with attachment
        result = await service.send_email(
            to_emails='user@example.com',
            subject='Test with Attachment',
            html_content='<p>See attachment</p>',
            attachments=[{
                'filename': 'test.pdf',
                'content': 'base64encodedcontent',
                'type': 'application/pdf'
            }]
        )

        assert result['success'] == True
        assert result['message_id'] == 'msg_attach'

    @pytest.mark.asyncio
    async def test_send_welcome_email(self, service, mock_sendgrid, mock_template_env):
        """Test sending welcome email"""
        # Mock SendGrid response
        mock_response = MagicMock()
        mock_response.status_code = 202
        mock_response.headers = {'X-Message-Id': 'msg_welcome'}
        service.sg_client.send.return_value = mock_response

        # Send welcome email
        result = await service.send_welcome_email(
            user_email='newuser@example.com',
            user_name='New User',
            verification_url='https://test.com/verify?token=xyz'
        )

        assert result['success'] == True
        assert result['message_id'] == 'msg_welcome'

    @pytest.mark.asyncio
    async def test_send_password_reset_email(self, service, mock_sendgrid, mock_template_env):
        """Test sending password reset email"""
        # Mock SendGrid response
        mock_response = MagicMock()
        mock_response.status_code = 202
        mock_response.headers = {'X-Message-Id': 'msg_reset'}
        service.sg_client.send.return_value = mock_response

        # Send password reset email
        result = await service.send_password_reset_email(
            user_email='user@example.com',
            user_name='User',
            reset_token='reset_token_123',
            reset_url='https://test.com/reset?token=reset_token_123'
        )

        assert result['success'] == True
        assert result['message_id'] == 'msg_reset'
        assert result['provider'] == EmailProvider.SENDGRID

    @pytest.mark.asyncio
    async def test_send_subscription_confirmation_email(self, service, mock_sendgrid, mock_template_env):
        """Test sending subscription confirmation email"""
        # Mock SendGrid response
        mock_response = MagicMock()
        mock_response.status_code = 202
        mock_response.headers = {'X-Message-Id': 'msg_sub'}
        service.sg_client.send.return_value = mock_response

        # Send subscription confirmation
        result = await service.send_subscription_confirmation_email(
            user_email='user@example.com',
            user_name='User',
            plan_name='Professional',
            amount=99.00,
            next_billing_date=datetime.now(timezone.utc),
            invoice_url='https://test.com/invoice/123'
        )

        assert result['success'] == True
        assert result['message_id'] == 'msg_sub'

    @pytest.mark.asyncio
    async def test_send_payment_failed_email(self, service, mock_sendgrid, mock_template_env):
        """Test sending payment failed email"""
        # Mock SendGrid response
        mock_response = MagicMock()
        mock_response.status_code = 202
        mock_response.headers = {'X-Message-Id': 'msg_failed'}
        service.sg_client.send.return_value = mock_response

        # Send payment failed email
        result = await service.send_payment_failed_email(
            user_email='user@example.com',
            user_name='User',
            amount=99.00,
            retry_date=datetime.now(timezone.utc),
            update_payment_url='https://test.com/payment/update'
        )

        assert result['success'] == True
        assert result['message_id'] == 'msg_failed'
        assert result['provider'] == EmailProvider.SENDGRID

    @pytest.mark.asyncio
    async def test_send_trial_ending_email(self, service, mock_sendgrid, mock_template_env):
        """Test sending trial ending email"""
        # Mock SendGrid response
        mock_response = MagicMock()
        mock_response.status_code = 202
        mock_response.headers = {'X-Message-Id': 'msg_trial'}
        service.sg_client.send.return_value = mock_response

        # Send trial ending email
        result = await service.send_trial_ending_email(
            user_email='user@example.com',
            user_name='User',
            trial_end_date=datetime.now(timezone.utc),
            plan_name='Professional',
            upgrade_url='https://test.com/upgrade'
        )

        assert result['success'] == True
        assert result['message_id'] == 'msg_trial'

    @pytest.mark.asyncio
    async def test_html_to_text_conversion(self, service):
        """Test HTML to text conversion"""
        html = """
        <html>
            <body>
                <h1>Title</h1>
                <p>This is a paragraph.</p>
                <script>alert('test');</script>
                <style>body { color: red; }</style>
            </body>
        </html>
        """

        text = service._html_to_text(html)

        assert 'Title' in text
        assert 'This is a paragraph.' in text
        assert 'alert' not in text  # Script removed
        assert 'color' not in text  # Style removed

    @pytest.mark.asyncio
    async def test_verify_email_address(self, service):
        """Test email address verification"""
        # Valid email
        assert await service.verify_email_address('valid@example.com') == True

        # Invalid emails
        assert await service.verify_email_address('invalid') == False
        assert await service.verify_email_address('@example.com') == False
        assert await service.verify_email_address('user@') == False
        assert await service.verify_email_address('user@.com') == False

    @pytest.mark.asyncio
    async def test_add_to_suppression_list(self, service, mock_sendgrid):
        """Test adding email to suppression list"""
        await service.add_to_suppression_list('unsubscribe@example.com', 'unsubscribe')

        # Verify SendGrid API was called
        service.sg_client.client.suppression.group_suppressions.post.assert_called_once()

    @pytest.mark.asyncio
    async def test_email_caching(self, service, mock_sendgrid, mock_cache):
        """Test email metadata caching"""
        # Mock SendGrid response
        mock_response = MagicMock()
        mock_response.status_code = 202
        mock_response.headers = {'X-Message-Id': 'msg_cache'}
        service.sg_client.send.return_value = mock_response

        # Send email
        await service.send_email(
            to_emails='user@example.com',
            subject='Test Caching',
            html_content='<p>Test</p>',
            email_type=EmailType.TRANSACTIONAL
        )

        # Verify cache was called
        mock_cache.set.assert_called()
        cache_call = mock_cache.set.call_args
        assert 'email:sent:msg_cache' in cache_call[0][0]

    @pytest.mark.asyncio
    async def test_send_email_error_handling(self, service, mock_sendgrid):
        """Test error handling in email sending"""
        # Mock SendGrid error
        service.sg_client.send.side_effect = Exception('SendGrid API error')

        # Should raise exception
        with pytest.raises(Exception) as exc:
            await service.send_email(
                to_emails='user@example.com',
                subject='Test Error',
                html_content='<p>Test</p>'
            )

        assert 'SendGrid API error' in str(exc.value)

    @pytest.mark.asyncio
    async def test_provider_not_configured(self, mock_settings):
        """Test handling when provider is not configured"""
        # No API keys configured
        mock_settings.SENDGRID_API_KEY = None
        # Settings cleared for security test

        service = EmailService()

        # Should raise error when trying to send
        with pytest.raises(ValueError) as exc:
            await service.send_email(
                to_emails='user@example.com',
                subject='Test',
                html_content='<p>Test</p>'
            )

        assert 'not available or not configured' in str(exc.value)


class TestEmailTemplates:
    """Test email template rendering"""

    @pytest.mark.asyncio
    async def test_render_template(self, service, mock_template_env):
        """Test template rendering"""
        # Mock template
        mock_html_template = MagicMock()
        mock_html_template.render_async = AsyncMock(
            return_value='<html>Hello John</html>'
        )
        mock_text_template = MagicMock()
        mock_text_template.render_async = AsyncMock(
            return_value='Hello John'
        )

        mock_template_env.get_template.side_effect = [
            mock_html_template,
            mock_text_template
        ]

        # Render template
        html, text = await service._render_template(
            'welcome',
            {'user_name': 'John'}
        )

        assert 'Hello John' in html
        assert 'Hello John' in text

    @pytest.mark.asyncio
    async def test_render_template_without_text(self, service, mock_template_env):
        """Test template rendering when text template doesn't exist"""
        # Mock HTML template only
        mock_html_template = MagicMock()
        mock_html_template.render_async = AsyncMock(
            return_value='<html><body><h1>Title</h1><p>Content</p></body></html>'
        )

        import jinja2
        mock_template_env.get_template.side_effect = [
            mock_html_template,
            jinja2.TemplateNotFound('welcome.txt')
        ]

        # Render template
        html, text = await service._render_template(
            'welcome',
            {'user_name': 'John'}
        )

        assert '<h1>Title</h1>' in html
        assert 'Title' in text  # Converted from HTML
        assert 'Content' in text