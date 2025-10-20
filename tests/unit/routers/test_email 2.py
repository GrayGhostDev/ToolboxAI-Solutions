"""
Unit tests for Email service router

Tests all email endpoints including sending emails, welcome emails,
password resets, verification, templates, and webhook handling.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timezone
from fastapi import status
from fastapi.testclient import TestClient

# Import the main FastAPI app
from apps.backend.main import app


@pytest.fixture
def test_client():
    """FastAPI test client"""
    return TestClient(app)


@pytest.fixture
def mock_admin_user():
    """Mock admin user"""
    user = Mock()
    user.id = "admin_123"
    user.email = "admin@example.com"
    user.name = "Admin User"
    user.role = "admin"
    return user


@pytest.fixture
def mock_teacher_user():
    """Mock teacher user"""
    user = Mock()
    user.id = "teacher_123"
    user.email = "teacher@example.com"
    user.name = "Teacher User"
    user.role = "teacher"
    return user


@pytest.fixture
def mock_student_user():
    """Mock student user"""
    user = Mock()
    user.id = "student_123"
    user.email = "student@example.com"
    user.name = "Student User"
    user.role = "student"
    return user


@pytest.fixture
def mock_email_service():
    """Mock EmailService"""
    service = AsyncMock()

    # Mock send_email
    service.send_email.return_value = {
        "message_id": "msg_123456",
        "sent": True,
    }

    # Mock send_welcome_email
    service.send_welcome_email.return_value = {
        "message_id": "msg_welcome_123",
        "sent": True,
    }

    # Mock send_password_reset_email
    service.send_password_reset_email.return_value = {
        "message_id": "msg_reset_123",
        "sent": True,
    }

    # Mock send_verification_email
    service.send_verification_email.return_value = {
        "message_id": "msg_verify_123",
        "sent": True,
    }

    # Mock create_template
    service.create_template.return_value = "d-template_123"

    # Mock create_template_version
    service.create_template_version.return_value = "version_abc123"

    # Mock handle_webhook
    service.handle_webhook.return_value = {
        "processed_count": 3,
        "events": ["delivered", "opened", "clicked"],
    }

    # Mock get_email_status
    service.get_email_status.return_value = {
        "message_id": "msg_123456",
        "status": "delivered",
        "events": [
            {"event": "delivered", "timestamp": 1734393600},
            {"event": "opened", "timestamp": 1734393700},
        ],
    }

    return service


@pytest.fixture
def sample_send_email_request():
    """Sample send email request"""
    return {
        "to_email": "recipient@example.com",
        "to_name": "Recipient Name",
        "subject": "Test Email",
        "html_content": "<p>Hello World</p>",
        "text_content": "Hello World",
        "email_type": "transactional",
        "priority": "normal",
    }


@pytest.mark.unit
class TestSendEmail:
    """Test general email sending endpoint"""

    def test_send_email_as_admin_success(
        self, test_client, sample_send_email_request, mock_admin_user, mock_email_service
    ):
        """Test successful email sending as admin"""
        with patch('apps.backend.api.routers.email.get_current_user', return_value=mock_admin_user):
            with patch('apps.backend.api.routers.email.email_service', mock_email_service):
                with patch('apps.backend.api.routers.email.log_audit'):
                    response = test_client.post(
                        "/api/v1/email/send",
                        json=sample_send_email_request
                    )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "success"
        assert data["data"]["message_id"] == "msg_123456"
        assert data["data"]["sent"] is True
        assert data["data"]["to"] == "recipient@example.com"

        # Verify service was called
        mock_email_service.send_email.assert_called_once()

    def test_send_email_as_teacher_success(
        self, test_client, sample_send_email_request, mock_teacher_user, mock_email_service
    ):
        """Test successful email sending as teacher"""
        with patch('apps.backend.api.routers.email.get_current_user', return_value=mock_teacher_user):
            with patch('apps.backend.api.routers.email.email_service', mock_email_service):
                with patch('apps.backend.api.routers.email.log_audit'):
                    response = test_client.post(
                        "/api/v1/email/send",
                        json=sample_send_email_request
                    )

        assert response.status_code == status.HTTP_200_OK

    def test_send_email_as_student_forbidden(
        self, test_client, sample_send_email_request, mock_student_user
    ):
        """Test email sending forbidden for students"""
        with patch('apps.backend.api.routers.email.get_current_user', return_value=mock_student_user):
            response = test_client.post(
                "/api/v1/email/send",
                json=sample_send_email_request
            )

        assert response.status_code == status.HTTP_403_FORBIDDEN
        data = response.json()
        assert "Only admins and teachers" in data["detail"]

    def test_send_email_with_template(
        self, test_client, mock_admin_user, mock_email_service
    ):
        """Test email sending with template ID"""
        request_data = {
            "to_email": "recipient@example.com",
            "subject": "Test Template",
            "template_id": "d-template_123",
            "template_data": {"name": "John", "code": "ABC123"},
        }

        with patch('apps.backend.api.routers.email.get_current_user', return_value=mock_admin_user):
            with patch('apps.backend.api.routers.email.email_service', mock_email_service):
                with patch('apps.backend.api.routers.email.log_audit'):
                    response = test_client.post(
                        "/api/v1/email/send",
                        json=request_data
                    )

        assert response.status_code == status.HTTP_200_OK

    def test_send_email_with_attachments(
        self, test_client, mock_admin_user, mock_email_service
    ):
        """Test email sending with attachments"""
        request_data = {
            "to_email": "recipient@example.com",
            "subject": "Test with Attachment",
            "html_content": "<p>Please see attached</p>",
            "attachments": [
                {
                    "content": "base64encodedcontent",
                    "filename": "document.pdf",
                    "content_type": "application/pdf",
                }
            ],
        }

        with patch('apps.backend.api.routers.email.get_current_user', return_value=mock_admin_user):
            with patch('apps.backend.api.routers.email.email_service', mock_email_service):
                with patch('apps.backend.api.routers.email.log_audit'):
                    response = test_client.post(
                        "/api/v1/email/send",
                        json=request_data
                    )

        assert response.status_code == status.HTTP_200_OK

    def test_send_email_with_cc_bcc(
        self, test_client, mock_admin_user, mock_email_service
    ):
        """Test email sending with CC and BCC recipients"""
        request_data = {
            "to_email": "recipient@example.com",
            "subject": "Test CC/BCC",
            "html_content": "<p>Test</p>",
            "cc": ["cc1@example.com", "cc2@example.com"],
            "bcc": ["bcc@example.com"],
            "reply_to": "replyto@example.com",
        }

        with patch('apps.backend.api.routers.email.get_current_user', return_value=mock_admin_user):
            with patch('apps.backend.api.routers.email.email_service', mock_email_service):
                with patch('apps.backend.api.routers.email.log_audit'):
                    response = test_client.post(
                        "/api/v1/email/send",
                        json=request_data
                    )

        assert response.status_code == status.HTTP_200_OK

    def test_send_email_service_error(
        self, test_client, sample_send_email_request, mock_admin_user, mock_email_service
    ):
        """Test email sending with service error"""
        mock_email_service.send_email.side_effect = Exception("SendGrid API error")

        with patch('apps.backend.api.routers.email.get_current_user', return_value=mock_admin_user):
            with patch('apps.backend.api.routers.email.email_service', mock_email_service):
                response = test_client.post(
                    "/api/v1/email/send",
                    json=sample_send_email_request
                )

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        data = response.json()
        assert "Failed to send email" in data["detail"]


@pytest.mark.unit
class TestWelcomeEmail:
    """Test welcome email endpoint"""

    def test_send_welcome_email_as_admin_success(
        self, test_client, mock_admin_user, mock_email_service
    ):
        """Test successful welcome email sending as admin"""
        request_data = {
            "user_email": "newuser@example.com",
            "user_name": "New User",
            "additional_data": {"trial_days": 14},
        }

        with patch('apps.backend.api.routers.email.get_current_user', return_value=mock_admin_user):
            with patch('apps.backend.api.routers.email.email_service', mock_email_service):
                with patch('apps.backend.api.routers.email.log_audit'):
                    response = test_client.post(
                        "/api/v1/email/welcome",
                        json=request_data
                    )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "success"
        assert data["data"]["message_id"] == "msg_welcome_123"
        assert data["data"]["sent"] is True

        # Verify service was called correctly
        mock_email_service.send_welcome_email.assert_called_once_with(
            user_email="newuser@example.com",
            user_name="New User",
            additional_data={"trial_days": 14}
        )

    def test_send_welcome_email_as_teacher_forbidden(
        self, test_client, mock_teacher_user
    ):
        """Test welcome email forbidden for teachers"""
        request_data = {
            "user_email": "newuser@example.com",
            "user_name": "New User",
        }

        with patch('apps.backend.api.routers.email.get_current_user', return_value=mock_teacher_user):
            response = test_client.post(
                "/api/v1/email/welcome",
                json=request_data
            )

        assert response.status_code == status.HTTP_403_FORBIDDEN
        data = response.json()
        assert "Admin access required" in data["detail"]

    def test_send_welcome_email_without_additional_data(
        self, test_client, mock_admin_user, mock_email_service
    ):
        """Test welcome email without additional data"""
        request_data = {
            "user_email": "newuser@example.com",
            "user_name": "New User",
        }

        with patch('apps.backend.api.routers.email.get_current_user', return_value=mock_admin_user):
            with patch('apps.backend.api.routers.email.email_service', mock_email_service):
                with patch('apps.backend.api.routers.email.log_audit'):
                    response = test_client.post(
                        "/api/v1/email/welcome",
                        json=request_data
                    )

        assert response.status_code == status.HTTP_200_OK

        # Verify additional_data defaults to empty dict
        call_args = mock_email_service.send_welcome_email.call_args
        assert call_args.kwargs["additional_data"] == {}

    def test_send_welcome_email_service_error(
        self, test_client, mock_admin_user, mock_email_service
    ):
        """Test welcome email with service error"""
        request_data = {
            "user_email": "newuser@example.com",
            "user_name": "New User",
        }

        mock_email_service.send_welcome_email.side_effect = Exception("Email service down")

        with patch('apps.backend.api.routers.email.get_current_user', return_value=mock_admin_user):
            with patch('apps.backend.api.routers.email.email_service', mock_email_service):
                response = test_client.post(
                    "/api/v1/email/welcome",
                    json=request_data
                )

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        data = response.json()
        assert "Failed to send welcome email" in data["detail"]


@pytest.mark.unit
class TestPasswordResetEmail:
    """Test password reset email endpoint"""

    def test_send_password_reset_email_success(
        self, test_client, mock_email_service
    ):
        """Test successful password reset email (public endpoint)"""
        request_data = {
            "user_email": "user@example.com",
            "user_name": "User Name",
            "reset_token": "reset_token_abc123",
        }

        with patch('apps.backend.api.routers.email.email_service', mock_email_service):
            with patch('apps.backend.api.routers.email.settings') as mock_settings:
                mock_settings.FRONTEND_URL = "https://example.com"
                response = test_client.post(
                    "/api/v1/email/password-reset",
                    json=request_data
                )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "success"
        assert data["data"]["message_id"] == "msg_reset_123"
        assert data["data"]["sent"] is True

        # Verify reset URL was built correctly
        call_args = mock_email_service.send_password_reset_email.call_args
        assert "reset-password" in call_args.kwargs["reset_url"]
        assert "reset_token_abc123" in call_args.kwargs["reset_url"]

    def test_send_password_reset_email_custom_url(
        self, test_client, mock_email_service
    ):
        """Test password reset email with custom URL"""
        request_data = {
            "user_email": "user@example.com",
            "user_name": "User Name",
            "reset_token": "reset_token_abc123",
            "reset_url": "https://custom.com/reset?token=reset_token_abc123",
        }

        with patch('apps.backend.api.routers.email.email_service', mock_email_service):
            response = test_client.post(
                "/api/v1/email/password-reset",
                json=request_data
            )

        assert response.status_code == status.HTTP_200_OK

        # Verify custom URL was used
        call_args = mock_email_service.send_password_reset_email.call_args
        assert call_args.kwargs["reset_url"] == "https://custom.com/reset?token=reset_token_abc123"

    def test_send_password_reset_email_service_error(
        self, test_client, mock_email_service
    ):
        """Test password reset email with service error"""
        request_data = {
            "user_email": "user@example.com",
            "user_name": "User Name",
            "reset_token": "reset_token_abc123",
        }

        mock_email_service.send_password_reset_email.side_effect = Exception("Email service error")

        with patch('apps.backend.api.routers.email.email_service', mock_email_service):
            with patch('apps.backend.api.routers.email.settings') as mock_settings:
                mock_settings.FRONTEND_URL = "https://example.com"
                response = test_client.post(
                    "/api/v1/email/password-reset",
                    json=request_data
                )

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        data = response.json()
        assert "Failed to send password reset email" in data["detail"]


@pytest.mark.unit
class TestVerificationEmail:
    """Test email verification endpoint"""

    def test_send_verification_email_success(
        self, test_client, mock_email_service
    ):
        """Test successful verification email (public endpoint)"""
        request_data = {
            "user_email": "user@example.com",
            "user_name": "User Name",
            "verification_token": "verify_token_xyz789",
        }

        with patch('apps.backend.api.routers.email.email_service', mock_email_service):
            with patch('apps.backend.api.routers.email.settings') as mock_settings:
                mock_settings.FRONTEND_URL = "https://example.com"
                response = test_client.post(
                    "/api/v1/email/verification",
                    json=request_data
                )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "success"
        assert data["data"]["message_id"] == "msg_verify_123"
        assert data["data"]["sent"] is True

        # Verify verification URL was built correctly
        call_args = mock_email_service.send_verification_email.call_args
        assert "verify-email" in call_args.kwargs["verification_url"]
        assert "verify_token_xyz789" in call_args.kwargs["verification_url"]

    def test_send_verification_email_custom_url(
        self, test_client, mock_email_service
    ):
        """Test verification email with custom URL"""
        request_data = {
            "user_email": "user@example.com",
            "user_name": "User Name",
            "verification_token": "verify_token_xyz789",
            "verification_url": "https://custom.com/verify?token=verify_token_xyz789",
        }

        with patch('apps.backend.api.routers.email.email_service', mock_email_service):
            response = test_client.post(
                "/api/v1/email/verification",
                json=request_data
            )

        assert response.status_code == status.HTTP_200_OK

        # Verify custom URL was used
        call_args = mock_email_service.send_verification_email.call_args
        assert call_args.kwargs["verification_url"] == "https://custom.com/verify?token=verify_token_xyz789"

    def test_send_verification_email_service_error(
        self, test_client, mock_email_service
    ):
        """Test verification email with service error"""
        request_data = {
            "user_email": "user@example.com",
            "user_name": "User Name",
            "verification_token": "verify_token_xyz789",
        }

        mock_email_service.send_verification_email.side_effect = Exception("Email service error")

        with patch('apps.backend.api.routers.email.email_service', mock_email_service):
            with patch('apps.backend.api.routers.email.settings') as mock_settings:
                mock_settings.FRONTEND_URL = "https://example.com"
                response = test_client.post(
                    "/api/v1/email/verification",
                    json=request_data
                )

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        data = response.json()
        assert "Failed to send verification email" in data["detail"]


@pytest.mark.unit
class TestEmailTemplates:
    """Test email template creation endpoint"""

    def test_create_template_as_admin_success(
        self, test_client, mock_admin_user, mock_email_service
    ):
        """Test successful template creation as admin"""
        request_data = {
            "name": "Welcome Email Template",
            "subject": "Welcome to our platform!",
            "html_content": "<h1>Welcome {{name}}</h1>",
            "text_content": "Welcome {{name}}",
            "generation": "dynamic",
        }

        with patch('apps.backend.api.routers.email.get_current_user', return_value=mock_admin_user):
            with patch('apps.backend.api.routers.email.email_service', mock_email_service):
                with patch('apps.backend.api.routers.email.log_audit'):
                    response = test_client.post(
                        "/api/v1/email/templates",
                        json=request_data
                    )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "success"
        assert data["data"]["template_id"] == "d-template_123"
        assert data["data"]["version_id"] == "version_abc123"
        assert data["data"]["name"] == "Welcome Email Template"

        # Verify service calls
        mock_email_service.create_template.assert_called_once_with(
            name="Welcome Email Template",
            generation="dynamic"
        )
        mock_email_service.create_template_version.assert_called_once()

    def test_create_template_as_teacher_forbidden(
        self, test_client, mock_teacher_user
    ):
        """Test template creation forbidden for teachers"""
        request_data = {
            "name": "Test Template",
            "subject": "Test",
            "html_content": "<p>Test</p>",
        }

        with patch('apps.backend.api.routers.email.get_current_user', return_value=mock_teacher_user):
            response = test_client.post(
                "/api/v1/email/templates",
                json=request_data
            )

        assert response.status_code == status.HTTP_403_FORBIDDEN
        data = response.json()
        assert "Admin access required" in data["detail"]

    def test_create_template_default_generation(
        self, test_client, mock_admin_user, mock_email_service
    ):
        """Test template creation with default generation"""
        request_data = {
            "name": "Test Template",
            "subject": "Test Subject",
            "html_content": "<p>Test</p>",
        }

        with patch('apps.backend.api.routers.email.get_current_user', return_value=mock_admin_user):
            with patch('apps.backend.api.routers.email.email_service', mock_email_service):
                with patch('apps.backend.api.routers.email.log_audit'):
                    response = test_client.post(
                        "/api/v1/email/templates",
                        json=request_data
                    )

        assert response.status_code == status.HTTP_200_OK

        # Verify default generation is "legacy"
        call_args = mock_email_service.create_template.call_args
        assert call_args.kwargs["generation"] == "legacy"

    def test_create_template_service_error(
        self, test_client, mock_admin_user, mock_email_service
    ):
        """Test template creation with service error"""
        request_data = {
            "name": "Test Template",
            "subject": "Test",
            "html_content": "<p>Test</p>",
        }

        mock_email_service.create_template.return_value = None

        with patch('apps.backend.api.routers.email.get_current_user', return_value=mock_admin_user):
            with patch('apps.backend.api.routers.email.email_service', mock_email_service):
                response = test_client.post(
                    "/api/v1/email/templates",
                    json=request_data
                )

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        data = response.json()
        assert "Failed to create template" in data["detail"]


@pytest.mark.unit
class TestSendGridWebhook:
    """Test SendGrid webhook handling endpoint"""

    @pytest.mark.asyncio
    async def test_handle_webhook_success(
        self, test_client, mock_email_service
    ):
        """Test successful webhook processing"""
        webhook_events = [
            {
                "email": "user@example.com",
                "event": "delivered",
                "timestamp": 1734393600,
            },
            {
                "email": "user@example.com",
                "event": "opened",
                "timestamp": 1734393700,
            },
        ]

        with patch('apps.backend.api.routers.email.email_service', mock_email_service):
            response = test_client.post(
                "/api/v1/email/webhook",
                json=webhook_events
            )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "success"
        assert data["data"]["processed_count"] == 3

        # Verify webhook handler was called
        mock_email_service.handle_webhook.assert_called_once_with(events=webhook_events)

    @pytest.mark.asyncio
    async def test_handle_webhook_empty_events(
        self, test_client, mock_email_service
    ):
        """Test webhook with empty events array"""
        mock_email_service.handle_webhook.return_value = {
            "processed_count": 0,
            "events": [],
        }

        with patch('apps.backend.api.routers.email.email_service', mock_email_service):
            response = test_client.post(
                "/api/v1/email/webhook",
                json=[]
            )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["data"]["processed_count"] == 0

    @pytest.mark.asyncio
    async def test_handle_webhook_processing_error(
        self, test_client, mock_email_service
    ):
        """Test webhook processing with error"""
        webhook_events = [{"event": "delivered"}]

        mock_email_service.handle_webhook.side_effect = Exception("Processing error")

        with patch('apps.backend.api.routers.email.email_service', mock_email_service):
            response = test_client.post(
                "/api/v1/email/webhook",
                json=webhook_events
            )

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        data = response.json()
        assert "Webhook processing failed" in data["detail"]


@pytest.mark.unit
class TestEmailStatus:
    """Test email status retrieval endpoint"""

    def test_get_email_status_success(
        self, test_client, mock_admin_user, mock_email_service
    ):
        """Test successful email status retrieval"""
        with patch('apps.backend.api.routers.email.get_current_user', return_value=mock_admin_user):
            with patch('apps.backend.api.routers.email.email_service', mock_email_service):
                response = test_client.get("/api/v1/email/status/msg_123456")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "success"
        assert data["data"]["message_id"] == "msg_123456"
        assert data["data"]["status"] == "delivered"
        assert len(data["data"]["events"]) == 2

        # Verify service was called
        mock_email_service.get_email_status.assert_called_once_with(message_id="msg_123456")

    def test_get_email_status_not_found(
        self, test_client, mock_admin_user, mock_email_service
    ):
        """Test email status not found"""
        mock_email_service.get_email_status.return_value = None

        with patch('apps.backend.api.routers.email.get_current_user', return_value=mock_admin_user):
            with patch('apps.backend.api.routers.email.email_service', mock_email_service):
                response = test_client.get("/api/v1/email/status/msg_nonexistent")

        assert response.status_code == status.HTTP_404_NOT_FOUND
        data = response.json()
        assert "Email status not found" in data["detail"]

    def test_get_email_status_service_error(
        self, test_client, mock_admin_user, mock_email_service
    ):
        """Test email status retrieval with service error"""
        mock_email_service.get_email_status.side_effect = Exception("API error")

        with patch('apps.backend.api.routers.email.get_current_user', return_value=mock_admin_user):
            with patch('apps.backend.api.routers.email.email_service', mock_email_service):
                response = test_client.get("/api/v1/email/status/msg_123456")

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        data = response.json()
        assert "Failed to get email status" in data["detail"]


@pytest.mark.unit
class TestRequestModels:
    """Test Pydantic request model validation"""

    def test_send_email_request_validation(self):
        """Test SendEmailRequest model validation"""
        from apps.backend.api.routers.email import SendEmailRequest

        # Valid request
        request = SendEmailRequest(
            to_email="test@example.com",
            subject="Test",
            html_content="<p>Test</p>",
        )
        assert request.to_email == "test@example.com"
        assert request.subject == "Test"

        # Invalid email
        with pytest.raises(Exception):
            SendEmailRequest(
                to_email="invalid_email",
                subject="Test",
            )

    def test_welcome_email_request_validation(self):
        """Test WelcomeEmailRequest model validation"""
        from apps.backend.api.routers.email import WelcomeEmailRequest

        request = WelcomeEmailRequest(
            user_email="user@example.com",
            user_name="Test User",
        )
        assert request.user_email == "user@example.com"
        assert request.user_name == "Test User"

    def test_password_reset_email_request_validation(self):
        """Test PasswordResetEmailRequest model validation"""
        from apps.backend.api.routers.email import PasswordResetEmailRequest

        request = PasswordResetEmailRequest(
            user_email="user@example.com",
            user_name="Test User",
            reset_token="token_123",
        )
        assert request.user_email == "user@example.com"
        assert request.reset_token == "token_123"

    def test_verification_email_request_validation(self):
        """Test VerificationEmailRequest model validation"""
        from apps.backend.api.routers.email import VerificationEmailRequest

        request = VerificationEmailRequest(
            user_email="user@example.com",
            user_name="Test User",
            verification_token="token_456",
        )
        assert request.verification_token == "token_456"

    def test_create_template_request_validation(self):
        """Test CreateTemplateRequest model validation"""
        from apps.backend.api.routers.email import CreateTemplateRequest

        request = CreateTemplateRequest(
            name="Test Template",
            subject="Test Subject",
            html_content="<p>Test</p>",
        )
        assert request.name == "Test Template"
        assert request.generation == "legacy"  # Default value
