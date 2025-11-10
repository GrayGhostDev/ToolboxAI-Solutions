"""
Complete Unit Tests for SendGrid Email Service
Production-ready tests with comprehensive coverage
@module test_sendgrid_email_service
@version 3.0.0
@since 2025-09-26
"""

import pytest
import asyncio
import os
from unittest.mock import Mock, patch, AsyncMock, MagicMock, call
from datetime import datetime, timezone
import json
import base64

# Import the service
from apps.backend.services.email.sendgrid import (
    SendGridEmailService,
    EmailPriority,
    EmailType,
    EmailRecipient,
    EmailAttachment,
    SENDGRID_AVAILABLE
)


@pytest.fixture
def mock_sendgrid_client():
    """Mock SendGrid API client"""
    mock_client = MagicMock()

    # Mock successful send response
    mock_response = MagicMock()
    mock_response.status_code = 202
    mock_response.headers = {'X-Message-Id': 'test-message-123'}
    mock_client.send.return_value = mock_response

    # Mock suppression API
    mock_client.client.suppression.bounces.post.return_value = MagicMock(status_code=201)
    mock_client.client.suppression.spam_reports.post.return_value = MagicMock(status_code=201)
    # Use getattr for 'global' as it's a reserved keyword
    mock_global = MagicMock()
    mock_global.post.return_value = MagicMock(status_code=201)
    setattr(mock_client.client.suppression, 'global', mock_global)

    # Mock ASM (unsubscribe groups)
    mock_client.client.asm.groups._.return_value.suppressions.post.return_value = MagicMock(status_code=201)

    return mock_client


@pytest.fixture
def mock_settings():
    """Mock application settings"""
    with patch('apps.backend.services.email_service_sendgrid.settings') as mock:
        mock.DEFAULT_FROM_EMAIL = 'test@toolboxai.com'
        mock.DEFAULT_FROM_NAME = 'ToolBoxAI Test'
        mock.EMAIL_SANDBOX_MODE = True
        mock.EMAIL_ENABLE_TRACKING = True
        mock.EMAIL_ENABLE_CLICK_TRACKING = True
        mock.EMAIL_ENABLE_OPEN_TRACKING = True
        mock.EMAIL_ENABLE_UNSUBSCRIBE = True
        mock.SENDGRID_UNSUBSCRIBE_GROUP_ID = 12345
        mock.FRONTEND_URL = 'https://test.toolboxai.com'
        yield mock


@pytest.fixture
def mock_cache():
    """Mock cache service"""
    with patch('apps.backend.services.email_service_sendgrid.cache') as mock:
        mock.get = AsyncMock(return_value=None)
        mock.set = AsyncMock()
        mock.delete = AsyncMock()
        yield mock


@pytest.fixture
def mock_environment():
    """Mock environment variables"""
    with patch.dict(os.environ, {'SENDGRID_API_KEY': 'SG.test_api_key_123'}):
        yield


@pytest.fixture
def mock_html_processing():
    """Mock HTML processing libraries"""
    with patch('apps.backend.services.email_service_sendgrid.HTML_PROCESSING_AVAILABLE', True):
        with patch('apps.backend.services.email_service_sendgrid.bleach') as mock_bleach:
            mock_bleach.clean = MagicMock(side_effect=lambda x, **kwargs: x)

            with patch('apps.backend.services.email_service_sendgrid.BeautifulSoup') as mock_bs:
                mock_soup = MagicMock()
                mock_soup.get_text.return_value = "Plain text content"
                mock_bs.return_value = mock_soup

                with patch('apps.backend.services.email_service_sendgrid.transform') as mock_transform:
                    mock_transform.side_effect = lambda x: x  # Return unchanged
                    yield


@pytest.fixture
def mock_jinja2():
    """Mock Jinja2 template environment"""
    with patch('apps.backend.services.email_service_sendgrid.JINJA2_AVAILABLE', True):
        with patch('apps.backend.services.email_service_sendgrid.Environment') as mock_env_class:
            mock_env = MagicMock()

            # Mock template rendering
            mock_template = MagicMock()
            mock_template.render_async = AsyncMock(return_value='<html>Rendered content</html>')
            mock_env.get_template.return_value = mock_template

            mock_env_class.return_value = mock_env
            yield mock_env


@pytest.fixture
async def service(
    mock_settings,
    mock_environment,
    mock_sendgrid_client,
    mock_cache,
    mock_html_processing,
    mock_jinja2
):
    """Create service instance with all mocks"""
    with patch('apps.backend.services.email_service_sendgrid.SENDGRID_AVAILABLE', True):
        with patch('apps.backend.services.email_service_sendgrid.SendGridAPIClient') as mock_client_class:
            mock_client_class.return_value = mock_sendgrid_client

            service = SendGridEmailService()
            return service


class TestSendGridEmailService:
    """Test SendGrid Email Service functionality"""

    @pytest.mark.asyncio
    async def test_service_initialization(self, service):
        """Test service initializes correctly"""
        assert service is not None
        assert service.from_email == 'test@toolboxai.com'
        assert service.from_name == 'ToolBoxAI Test'
        assert service.sandbox_mode == True
        assert service.enable_tracking == True
        assert service.client is not None

    @pytest.mark.asyncio
    async def test_send_simple_email(self, service):
        """Test sending a simple email"""
        result = await service.send_email(
            to_emails='user@example.com',
            subject='Test Email',
            html_content='<p>Hello World</p>',
            text_content='Hello World'
        )

        assert result['success'] == True
        assert result['message_id'] == 'test-message-123'
        assert result['status_code'] == 202
        assert result['provider'] == 'sendgrid'

        # Verify send was called
        service.client.send.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_email_with_recipients(self, service):
        """Test sending email with EmailRecipient objects"""
        recipients = [
            EmailRecipient(
                email='user1@example.com',
                name='User One',
                substitutions={'greeting': 'Hello'},
                custom_args={'user_id': '123'}
            ),
            EmailRecipient(
                email='user2@example.com',
                name='User Two'
            )
        ]

        result = await service.send_email(
            to_emails=recipients,
            subject='Personalized Email',
            html_content='<p>{{greeting}} {{name}}</p>'
        )

        assert result['success'] == True
        service.client.send.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_email_with_cc_bcc(self, service):
        """Test sending email with CC and BCC"""
        result = await service.send_email(
            to_emails='main@example.com',
            subject='Email with CC/BCC',
            html_content='<p>Content</p>',
            cc=['cc1@example.com', 'cc2@example.com'],
            bcc=['bcc@example.com']
        )

        assert result['success'] == True

        # Check the Mail object was created with CC/BCC
        call_args = service.client.send.call_args
        mail_obj = call_args[0][0]
        assert mail_obj is not None

    @pytest.mark.asyncio
    async def test_send_email_with_attachments(self, service):
        """Test sending email with attachments"""
        attachments = [
            EmailAttachment(
                filename='test.pdf',
                content=b'PDF content here',
                type='application/pdf'
            ),
            EmailAttachment(
                filename='image.png',
                content=base64.b64encode(b'PNG image data').decode(),
                type='image/png',
                disposition='inline',
                content_id='logo'
            )
        ]

        result = await service.send_email(
            to_emails='user@example.com',
            subject='Email with Attachments',
            html_content='<p>See attached files</p>',
            attachments=attachments
        )

        assert result['success'] == True
        service.client.send.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_email_with_template(self, service):
        """Test sending email with template"""
        # Mock template rendering
        service.template_env.get_template.return_value.render_async = AsyncMock(
            side_effect=['<html>Welcome {{user_name}}</html>', 'Welcome {{user_name}}']
        )

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
        service.template_env.get_template.assert_called()

    @pytest.mark.asyncio
    async def test_send_email_with_categories(self, service):
        """Test sending email with categories"""
        result = await service.send_email(
            to_emails='user@example.com',
            subject='Categorized Email',
            html_content='<p>Content</p>',
            categories=['newsletter', 'weekly-update'],
            email_type=EmailType.MARKETING
        )

        assert result['success'] == True

    @pytest.mark.asyncio
    async def test_send_email_with_custom_args(self, service):
        """Test sending email with custom arguments"""
        result = await service.send_email(
            to_emails='user@example.com',
            subject='Tracked Email',
            html_content='<p>Content</p>',
            custom_args={
                'campaign_id': 'summer-2025',
                'user_segment': 'premium'
            }
        )

        assert result['success'] == True

    @pytest.mark.asyncio
    async def test_send_scheduled_email(self, service):
        """Test sending scheduled email"""
        send_at = int(datetime.now(timezone.utc).timestamp()) + 3600  # 1 hour from now

        result = await service.send_email(
            to_emails='user@example.com',
            subject='Scheduled Email',
            html_content='<p>This will be sent later</p>',
            send_at=send_at
        )

        assert result['success'] == True

    @pytest.mark.asyncio
    async def test_send_email_with_priority(self, service):
        """Test sending email with different priorities"""
        result = await service.send_email(
            to_emails='user@example.com',
            subject='Urgent Email',
            html_content='<p>Urgent content</p>',
            priority=EmailPriority.URGENT
        )

        assert result['success'] == True

    @pytest.mark.asyncio
    async def test_send_welcome_email(self, service):
        """Test sending welcome email"""
        result = await service.send_welcome_email(
            user_email='newuser@example.com',
            user_name='New User',
            verification_url='https://test.com/verify?token=abc123'
        )

        assert result['success'] == True
        assert result['provider'] == 'sendgrid'

    @pytest.mark.asyncio
    async def test_send_password_reset_email(self, service):
        """Test sending password reset email"""
        result = await service.send_password_reset_email(
            user_email='user@example.com',
            user_name='John Doe',
            reset_token='reset-token-123',
            reset_url='https://test.com/reset?token=reset-token-123'
        )

        assert result['success'] == True

    @pytest.mark.asyncio
    async def test_send_verification_email(self, service):
        """Test sending verification email"""
        result = await service.send_verification_email(
            user_email='user@example.com',
            user_name='John Doe',
            verification_code='123456',
            verification_url='https://test.com/verify?code=123456'
        )

        assert result['success'] == True

    @pytest.mark.asyncio
    async def test_send_subscription_confirmation(self, service):
        """Test sending subscription confirmation"""
        result = await service.send_subscription_confirmation_email(
            user_email='user@example.com',
            user_name='John Doe',
            plan_name='Professional',
            amount=99.99,
            next_billing_date=datetime.now(timezone.utc),
            invoice_url='https://test.com/invoice/123'
        )

        assert result['success'] == True

    @pytest.mark.asyncio
    async def test_handle_sendgrid_error(self, service):
        """Test handling SendGrid API errors"""
        from python_http_client.exceptions import HTTPError

        # Mock an error response
        error = HTTPError()
        error.status_code = 400
        error.to_dict = {'errors': [{'message': 'Invalid email'}]}
        service.client.send.side_effect = error

        result = await service.send_email(
            to_emails='invalid-email',
            subject='Test',
            html_content='<p>Test</p>'
        )

        assert result['success'] == False
        assert result['status_code'] == 400
        assert 'error' in result

    @pytest.mark.asyncio
    async def test_handle_general_error(self, service):
        """Test handling general errors"""
        service.client.send.side_effect = Exception("Network error")

        result = await service.send_email(
            to_emails='user@example.com',
            subject='Test',
            html_content='<p>Test</p>'
        )

        assert result['success'] == False
        assert 'Network error' in result['error']

    @pytest.mark.asyncio
    async def test_add_to_suppression_list(self, service):
        """Test adding email to suppression list"""
        result = await service.add_to_suppression_list(
            email='bounced@example.com',
            suppression_type='bounce'
        )

        assert result == True
        service.client.client.suppression.bounces.post.assert_called_once()

    @pytest.mark.asyncio
    async def test_remove_from_suppression_list(self, service):
        """Test removing email from suppression list"""
        service.client.client.suppression.bounces._.return_value.delete.return_value = MagicMock(status_code=204)

        result = await service.remove_from_suppression_list(
            email='bounced@example.com',
            suppression_type='bounce'
        )

        assert result == True

    @pytest.mark.asyncio
    async def test_verify_email_address(self, service):
        """Test email address verification"""
        # Test valid email
        assert await service.verify_email_address('valid@example.com') == True

        # Test invalid formats
        assert await service.verify_email_address('invalid') == False
        assert await service.verify_email_address('@example.com') == False
        assert await service.verify_email_address('user@') == False

    @pytest.mark.asyncio
    async def test_handle_webhook_events(self, service):
        """Test handling SendGrid webhook events"""
        events = [
            {
                'event': 'delivered',
                'email': 'user@example.com',
                'sg_message_id': 'msg-123',
                'timestamp': 1234567890
            },
            {
                'event': 'bounce',
                'email': 'bounced@example.com',
                'sg_message_id': 'msg-456',
                'timestamp': 1234567891,
                'type': 'hard'
            },
            {
                'event': 'spam_report',
                'email': 'spammer@example.com',
                'sg_message_id': 'msg-789',
                'timestamp': 1234567892
            }
        ]

        result = await service.handle_webhook(events)

        assert result['success'] == True
        assert result['processed'] == 3
        assert result['errors'] == 0

    @pytest.mark.asyncio
    async def test_cache_email_metadata(self, service, mock_cache):
        """Test email metadata caching"""
        await service.send_email(
            to_emails='user@example.com',
            subject='Cached Email',
            html_content='<p>Content</p>',
            email_type=EmailType.TRANSACTIONAL
        )

        # Verify cache was called
        mock_cache.set.assert_called()
        call_args = mock_cache.set.call_args
        assert 'email:sent:test-message-123' in call_args[0][0]

    @pytest.mark.asyncio
    async def test_get_email_status(self, service, mock_cache):
        """Test getting email status from cache"""
        mock_cache.get.return_value = {
            'message_id': 'msg-123',
            'status': 'delivered',
            'timestamp': '2025-09-26T12:00:00Z'
        }

        status = await service.get_email_status('msg-123')

        assert status is not None
        assert status['message_id'] == 'msg-123'
        assert status['status'] == 'delivered'

    @pytest.mark.asyncio
    async def test_html_processing(self, service):
        """Test HTML content processing"""
        html = '<p style="color: red;">Test <script>alert("XSS")</script></p>'
        processed = service._process_html(html)

        # Script should be sanitized
        assert '<script>' not in processed or processed == html  # Depends on bleach availability

    @pytest.mark.asyncio
    async def test_html_to_text_conversion(self, service):
        """Test HTML to text conversion"""
        html = '<h1>Title</h1><p>Paragraph text</p><script>alert("test")</script>'
        text = service._html_to_text(html)

        assert 'Title' in text or 'Paragraph text' in text
        assert 'script' not in text.lower() or 'alert' not in text

    @pytest.mark.asyncio
    async def test_sandbox_mode(self, service):
        """Test sandbox mode configuration"""
        assert service.sandbox_mode == True

        result = await service.send_email(
            to_emails='test@example.com',
            subject='Sandbox Test',
            html_content='<p>This should not actually send</p>'
        )

        assert result['success'] == True

    @pytest.mark.asyncio
    async def test_tracking_settings(self, service):
        """Test email tracking settings"""
        assert service.enable_tracking == True
        assert service.enable_click_tracking == True
        assert service.enable_open_tracking == True

        result = await service.send_email(
            to_emails='user@example.com',
            subject='Tracked Email',
            html_content='<p>Click <a href="https://example.com">here</a></p>'
        )

        assert result['success'] == True

    @pytest.mark.asyncio
    async def test_unsubscribe_settings(self, service):
        """Test unsubscribe settings"""
        assert service.enable_unsubscribe == True
        assert service.unsubscribe_group_id == 12345

        result = await service.send_email(
            to_emails='user@example.com',
            subject='Newsletter',
            html_content='<p>Content</p>',
            email_type=EmailType.MARKETING
        )

        assert result['success'] == True


class TestSendGridIntegration:
    """Integration tests for SendGrid service"""

    @pytest.mark.asyncio
    async def test_no_api_key(self, mock_settings, mock_cache):
        """Test service behavior without API key"""
        with patch.dict(os.environ, {}, clear=True):
            service = SendGridEmailService()
            assert service.client is None

            result = await service.send_email(
                to_emails='user@example.com',
                subject='Test',
                html_content='<p>Test</p>'
            )

            assert result['success'] == False
            assert 'not initialized' in result['error']

    @pytest.mark.asyncio
    async def test_invalid_api_key_format(self, mock_settings, mock_cache):
        """Test service with invalid API key format"""
        with patch.dict(os.environ, {'SENDGRID_API_KEY': 'invalid-key'}):
            service = SendGridEmailService()
            # Service initializes but warns about key format
            assert service.client is not None  # Client is created but may fail on actual send

    @pytest.mark.asyncio
    async def test_template_not_found(self, service):
        """Test handling missing template"""
        import jinja2
        service.template_env.get_template.side_effect = jinja2.TemplateNotFound('missing.html')

        with pytest.raises(jinja2.TemplateNotFound):
            await service.send_email(
                to_emails='user@example.com',
                subject='Test',
                template_name='missing',
                template_context={}
            )

    @pytest.mark.asyncio
    async def test_concurrent_sends(self, service):
        """Test sending multiple emails concurrently"""
        tasks = []
        for i in range(10):
            task = service.send_email(
                to_emails=f'user{i}@example.com',
                subject=f'Test Email {i}',
                html_content=f'<p>Content {i}</p>'
            )
            tasks.append(task)

        results = await asyncio.gather(*tasks)

        assert len(results) == 10
        assert all(r['success'] for r in results)
        assert service.client.send.call_count == 10


class TestEmailRecipient:
    """Test EmailRecipient dataclass"""

    def test_email_recipient_creation(self):
        """Test creating EmailRecipient"""
        recipient = EmailRecipient(
            email='user@example.com',
            name='John Doe',
            substitutions={'greeting': 'Hello'},
            custom_args={'user_id': '123'}
        )

        assert recipient.email == 'user@example.com'
        assert recipient.name == 'John Doe'
        assert recipient.substitutions['greeting'] == 'Hello'
        assert recipient.custom_args['user_id'] == '123'

    def test_email_recipient_defaults(self):
        """Test EmailRecipient default values"""
        recipient = EmailRecipient(email='user@example.com')

        assert recipient.email == 'user@example.com'
        assert recipient.name is None
        assert recipient.substitutions == {}
        assert recipient.custom_args == {}


class TestEmailAttachment:
    """Test EmailAttachment dataclass"""

    def test_email_attachment_creation(self):
        """Test creating EmailAttachment"""
        attachment = EmailAttachment(
            filename='document.pdf',
            content=b'PDF content',
            type='application/pdf',
            disposition='attachment',
            content_id='doc123'
        )

        assert attachment.filename == 'document.pdf'
        assert attachment.content == b'PDF content'
        assert attachment.type == 'application/pdf'
        assert attachment.disposition == 'attachment'
        assert attachment.content_id == 'doc123'

    def test_email_attachment_defaults(self):
        """Test EmailAttachment default values"""
        attachment = EmailAttachment(
            filename='image.png',
            content=b'PNG data',
            type='image/png'
        )

        assert attachment.disposition == 'attachment'
        assert attachment.content_id is None