# Email Services Documentation

## 🚀 Overview

ToolBoxAI uses a dual email service architecture:
- **Development**: Mailhog for local email testing
- **Production**: SendGrid for transactional emails

## 📧 Email Service Architecture

### Service Factory Pattern
The system automatically selects the appropriate email service based on environment:

```python
# apps/backend/services/email_service_factory.py
- Checks for SENDGRID_API_KEY
- Validates API key format (must start with "SG.")
- Falls back to MockEmailService if unavailable
- Respects EMAIL_USE_MOCK flag for testing
```

## 🔧 SendGrid Configuration (Production)

### Prerequisites
1. **SendGrid Account**: Sign up at [sendgrid.com](https://sendgrid.com)
2. **API Key**: Generate with full access permissions
3. **Domain Authentication**: Verify sending domain
4. **Templates**: Create email templates in SendGrid dashboard

### Environment Variables
```bash
# Production (.env)
SENDGRID_API_KEY=SG.your-api-key-here
SENDGRID_FROM_EMAIL=noreply@toolboxai.com
SENDGRID_FROM_NAME=ToolBoxAI Platform
SENDGRID_REPLY_TO=support@toolboxai.com

# Template IDs (from SendGrid dashboard)
SENDGRID_TEMPLATE_WELCOME=d-abc123...
SENDGRID_TEMPLATE_PASSWORD_RESET=d-def456...
SENDGRID_TEMPLATE_CLASS_INVITATION=d-ghi789...
SENDGRID_TEMPLATE_CONTENT_READY=d-jkl012...
SENDGRID_TEMPLATE_ASSESSMENT_COMPLETE=d-mno345...
SENDGRID_TEMPLATE_WEEKLY_PROGRESS=d-pqr678...
```

### SendGrid Features Implemented

#### 1. **Transactional Emails**
```python
# Welcome email
await email_service.send_welcome_email(
    to_email=user.email,
    user_name=user.name,
    activation_link=activation_url
)

# Password reset
await email_service.send_password_reset(
    to_email=user.email,
    reset_token=token,
    reset_link=reset_url
)

# Class invitation
await email_service.send_class_invitation(
    to_email=student.email,
    class_name=class.name,
    teacher_name=teacher.name,
    join_link=invitation_url
)
```

#### 2. **Bulk Emails**
```python
# Send to multiple recipients
await email_service.send_bulk_notification(
    recipients=[student.email for student in class.students],
    subject="New Content Available",
    template_id="d-bulk123",
    personalizations={
        "student_name": lambda s: s.name,
        "class_name": class.name
    }
)
```

#### 3. **Email Tracking**
```python
# Track opens and clicks
email_config = {
    "tracking_settings": {
        "click_tracking": {"enable": True},
        "open_tracking": {"enable": True},
        "subscription_tracking": {"enable": False}
    }
}
```

#### 4. **Attachments**
```python
# Attach files
await email_service.send_with_attachment(
    to_email=user.email,
    subject="Your Progress Report",
    attachment_path="/path/to/report.pdf",
    attachment_name="progress_report.pdf"
)
```

#### 5. **Dynamic Templates**
```python
# Use SendGrid dynamic templates
await email_service.send_templated_email(
    to_email=user.email,
    template_id="d-template123",
    dynamic_data={
        "user_name": user.name,
        "course_progress": 85,
        "achievements": ["Master Coder", "Quiz Champion"],
        "next_lesson": "Advanced Algorithms"
    }
)
```

### SendGrid Webhooks

Configure webhook endpoint for event tracking:

```python
# apps/backend/api/webhooks/sendgrid.py
@router.post("/webhooks/sendgrid")
async def sendgrid_webhook(request: Request):
    events = await request.json()

    for event in events:
        event_type = event.get("event")
        email = event.get("email")

        if event_type == "delivered":
            await mark_email_delivered(email)
        elif event_type == "bounce":
            await handle_bounce(email, event.get("reason"))
        elif event_type == "spam_report":
            await handle_spam_report(email)
        elif event_type == "unsubscribe":
            await handle_unsubscribe(email)
```

Webhook Events:
- `processed` - Email received by SendGrid
- `delivered` - Email delivered to recipient
- `bounce` - Email bounced (soft/hard)
- `deferred` - Temporary delivery failure
- `open` - Email opened
- `click` - Link clicked
- `spam_report` - Marked as spam
- `unsubscribe` - User unsubscribed

## 🧪 Mailhog Configuration (Development)

### Docker Service
```yaml
# infrastructure/docker/compose/docker-compose.dev.yml
mailhog:
  image: mailhog/mailhog:latest
  container_name: toolboxai-mailhog
  ports:
    - "1025:1025"  # SMTP server
    - "8025:8025"  # Web UI
  networks:
    - toolboxai-network
  restart: unless-stopped
```

### Development Configuration
```bash
# Development (.env.local)
EMAIL_USE_MOCK=false  # Set to true to use mock service
SMTP_HOST=localhost
SMTP_PORT=1025
SMTP_USE_TLS=false
EMAIL_FROM=dev@toolboxai.local
```

### Accessing Mailhog
- **Web Interface**: http://localhost:8025
- **SMTP Server**: localhost:1025
- **API**: http://localhost:8025/api/v2/messages

### Mailhog Features
1. **Catch all emails** - No emails leave development
2. **Web UI** - View all sent emails
3. **API Access** - Programmatic email retrieval
4. **Search** - Find emails by subject, sender, etc.
5. **Release** - Forward emails to real addresses (testing)

## 📨 Email Templates

### Base Template Structure
```html
<!-- templates/email/base.html -->
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        /* Email-safe CSS */
        .container { max-width: 600px; margin: 0 auto; }
        .header { background: #228be6; color: white; padding: 20px; }
        .content { padding: 20px; }
        .footer { background: #f8f9fa; padding: 20px; text-align: center; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>ToolBoxAI</h1>
        </div>
        <div class="content">
            {{ content }}
        </div>
        <div class="footer">
            <p>&copy; 2025 ToolBoxAI. All rights reserved.</p>
            <p><a href="{{ unsubscribe_url }}">Unsubscribe</a></p>
        </div>
    </div>
</body>
</html>
```

### Template Types

#### 1. Welcome Email
```python
{
    "subject": "Welcome to ToolBoxAI!",
    "template_id": "d-welcome123",
    "dynamic_data": {
        "user_name": "John Doe",
        "activation_link": "https://...",
        "getting_started_url": "https://..."
    }
}
```

#### 2. Password Reset
```python
{
    "subject": "Reset Your Password",
    "template_id": "d-reset456",
    "dynamic_data": {
        "user_name": "John Doe",
        "reset_link": "https://...",
        "expires_in": "24 hours"
    }
}
```

#### 3. Content Generation Complete
```python
{
    "subject": "Your Content is Ready!",
    "template_id": "d-content789",
    "dynamic_data": {
        "user_name": "John Doe",
        "content_type": "Lesson Plan",
        "content_title": "Introduction to Python",
        "download_link": "https://..."
    }
}
```

#### 4. Weekly Progress Report
```python
{
    "subject": "Your Weekly Progress",
    "template_id": "d-progress012",
    "dynamic_data": {
        "student_name": "Jane Smith",
        "lessons_completed": 5,
        "quiz_score": 92,
        "time_spent": "12 hours",
        "achievements": ["Quick Learner", "Perfect Score"]
    }
}
```

## 🚀 Implementation Examples

### Basic Email Service Usage
```python
from apps.backend.services.email_service_factory import get_email_service

# Get appropriate service (SendGrid or Mock)
email_service = get_email_service()

# Send simple email
await email_service.send_email(
    to_email="user@example.com",
    subject="Test Email",
    html_content="<h1>Hello World</h1>",
    text_content="Hello World"
)
```

### Celery Task for Async Emails
```python
# apps/backend/workers/tasks/email_tasks.py
from celery import shared_task
from apps.backend.services.email_service_factory import get_email_service

@shared_task
def send_email_task(to_email: str, subject: str, content: str):
    """Background task for sending emails"""
    email_service = get_email_service()
    return email_service.send_email(
        to_email=to_email,
        subject=subject,
        html_content=content
    )

# Usage
send_email_task.delay(
    to_email="user@example.com",
    subject="Background Email",
    content="<p>Sent from Celery!</p>"
)
```

### Email Queue Management
```python
# apps/backend/services/email_queue.py
class EmailQueue:
    """Manage email queue with Redis"""

    def __init__(self):
        self.redis_client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            decode_responses=True
        )
        self.queue_key = "email:queue"

    async def enqueue(self, email_data: dict):
        """Add email to queue"""
        await self.redis_client.rpush(
            self.queue_key,
            json.dumps(email_data)
        )

    async def process_queue(self):
        """Process queued emails"""
        email_service = get_email_service()

        while True:
            email_json = await self.redis_client.lpop(self.queue_key)
            if not email_json:
                break

            email_data = json.loads(email_json)
            try:
                await email_service.send_email(**email_data)
            except Exception as e:
                logger.error(f"Failed to send email: {e}")
                # Re-queue or move to dead letter queue
```

## 📊 Email Analytics

### Tracking Metrics
```python
class EmailAnalytics:
    """Track email metrics"""

    async def record_sent(self, email: str, template: str):
        await db.email_metrics.insert({
            "email": email,
            "template": template,
            "event": "sent",
            "timestamp": datetime.utcnow()
        })

    async def get_metrics(self, days: int = 30):
        return {
            "total_sent": await self.count_events("sent", days),
            "delivered": await self.count_events("delivered", days),
            "opened": await self.count_events("open", days),
            "clicked": await self.count_events("click", days),
            "bounced": await self.count_events("bounce", days),
            "spam_reports": await self.count_events("spam_report", days)
        }
```

## 🔐 Security Best Practices

1. **API Key Security**
   - Store in environment variables
   - Never commit to repository
   - Rotate keys regularly
   - Use restricted API keys when possible

2. **Domain Authentication**
   - Verify sending domain with SPF
   - Set up DKIM signing
   - Configure DMARC policy

3. **Rate Limiting**
   ```python
   # Implement rate limiting
   @rate_limit("10/minute")
   async def send_email_endpoint():
       pass
   ```

4. **Input Validation**
   ```python
   # Validate email addresses
   from email_validator import validate_email

   try:
       validation = validate_email(email_address)
       email = validation.email
   except EmailNotValidError:
       raise ValueError("Invalid email address")
   ```

5. **Unsubscribe Management**
   - Honor unsubscribe requests immediately
   - Maintain suppression lists
   - Provide clear unsubscribe links

## 🧪 Testing

### Unit Tests
```python
# tests/unit/services/test_email_service.py
import pytest
from unittest.mock import Mock, patch

def test_sendgrid_email_service():
    with patch('sendgrid.SendGridAPIClient') as mock_sg:
        service = SendGridEmailService()
        service.send_email(
            to_email="test@example.com",
            subject="Test",
            content="Test content"
        )
        mock_sg.send.assert_called_once()
```

### Integration Tests
```python
# tests/integration/test_email_integration.py
@pytest.mark.integration
async def test_mailhog_integration():
    # Send email to Mailhog
    email_service = get_email_service()
    await email_service.send_email(
        to_email="test@example.com",
        subject="Integration Test",
        content="Test content"
    )

    # Verify via Mailhog API
    response = requests.get("http://localhost:8025/api/v2/messages")
    messages = response.json()["items"]
    assert len(messages) > 0
    assert messages[0]["Content"]["Headers"]["Subject"][0] == "Integration Test"
```

## 🚨 Troubleshooting

### Common Issues

1. **SendGrid API Key Invalid**
   - Verify key starts with "SG."
   - Check key has proper permissions
   - Ensure key is not expired

2. **Emails Not Sending**
   - Check EMAIL_USE_MOCK flag
   - Verify SENDGRID_API_KEY is set
   - Check network connectivity
   - Review SendGrid activity feed

3. **Mailhog Not Receiving**
   - Ensure Mailhog container is running
   - Check port 1025 is not blocked
   - Verify SMTP_HOST=localhost

4. **Template Errors**
   - Validate template IDs match SendGrid
   - Check dynamic data keys
   - Test templates in SendGrid editor

5. **Webhook Failures**
   - Verify webhook URL is publicly accessible
   - Check webhook signature validation
   - Review webhook event logs

## 📚 Resources

- [SendGrid Documentation](https://docs.sendgrid.com)
- [SendGrid Python SDK](https://github.com/sendgrid/sendgrid-python)
- [Mailhog Documentation](https://github.com/mailhog/MailHog)
- [Email Best Practices](https://sendgrid.com/resource/email-deliverability-guide/)
- [MJML Email Templates](https://mjml.io) - Responsive email framework

## 🔄 Migration Path

### From Mailhog to SendGrid
1. Create SendGrid account
2. Generate API key
3. Set SENDGRID_API_KEY in production environment
4. Create email templates in SendGrid
5. Update template IDs in environment
6. Test with sandbox mode
7. Verify domain authentication
8. Go live

### Monitoring Checklist
- [ ] Email delivery rate > 95%
- [ ] Bounce rate < 5%
- [ ] Spam report rate < 0.1%
- [ ] Open rate tracking enabled
- [ ] Click tracking configured
- [ ] Webhook endpoint secure
- [ ] Suppression list maintained

---

*Email services documentation completed: September 28, 2025*
*SendGrid v3 API / Mailhog v1.0*