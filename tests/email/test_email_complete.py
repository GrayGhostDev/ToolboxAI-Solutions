#!/usr/bin/env python3
"""
Complete Email Service Test
Tests email functionality with automatic fallback to mock service
"""

import os
import sys
import asyncio
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add project to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


async def test_email_service():
    """Test the email service with automatic selection"""
    print("\n" + "=" * 70)
    print("🚀 COMPLETE EMAIL SERVICE TEST")
    print("=" * 70)

    # Get the appropriate email service
    from apps.backend.services.email.factory import get_email_service

    service = get_email_service()

    print(f"\n📧 Service Type: {service.__class__.__name__}")
    print(f"   From: {service.from_email}")
    print(f"   Name: {service.from_name}")

    # Test 1: Simple email
    print("\n" + "-" * 60)
    print("TEST 1: Simple Email")
    print("-" * 60)

    result = await service.send_email(
        to_emails="test@example.com",
        subject=f"Test Email - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        html_content="<h2>Test Email</h2><p>This is a test email.</p>",
        text_content="Test Email\n\nThis is a test email."
    )

    if result['success']:
        print(f"✅ SUCCESS")
        print(f"   Message ID: {result.get('message_id')}")
        print(f"   Provider: {result.get('provider')}")
        if result.get('note'):
            print(f"   Note: {result.get('note')}")
    else:
        print(f"❌ FAILED: {result.get('error')}")

    # Test 2: Welcome email
    print("\n" + "-" * 60)
    print("TEST 2: Welcome Email")
    print("-" * 60)

    result = await service.send_welcome_email(
        user_email="newuser@example.com",
        user_name="John Doe",
        verification_url="https://example.com/verify?token=abc123"
    )

    if result['success']:
        print(f"✅ SUCCESS")
        print(f"   Message ID: {result.get('message_id')}")
    else:
        print(f"❌ FAILED: {result.get('error')}")

    # Test 3: Multiple recipients
    print("\n" + "-" * 60)
    print("TEST 3: Multiple Recipients")
    print("-" * 60)

    from apps.backend.services.email.sendgrid import EmailRecipient

    recipients = [
        EmailRecipient(email="user1@example.com", name="User One"),
        EmailRecipient(email="user2@example.com", name="User Two")
    ]

    result = await service.send_email(
        to_emails=recipients,
        subject="Multi-recipient Test",
        html_content="<p>Email to multiple recipients</p>"
    )

    if result['success']:
        print(f"✅ SUCCESS")
        print(f"   Message ID: {result.get('message_id')}")
    else:
        print(f"❌ FAILED: {result.get('error')}")

    # If using mock service, show sent emails
    if hasattr(service, 'get_sent_emails'):
        print("\n" + "=" * 70)
        print("📋 MOCK SERVICE EMAIL LOG")
        print("=" * 70)
        emails = service.get_sent_emails()
        for i, email in enumerate(emails, 1):
            print(f"\n{i}. Email to: {', '.join(email['to'])}")
            print(f"   Subject: {email['subject']}")
            print(f"   ID: {email['message_id']}")
            print(f"   Time: {email['timestamp']}")


async def test_with_mock():
    """Force test with mock service"""
    print("\n" + "=" * 70)
    print("🎭 TESTING WITH MOCK SERVICE")
    print("=" * 70)

    from apps.backend.services.email.factory import get_email_service

    # Force mock service
    service = get_email_service(force_mock=True)

    result = await service.send_email(
        to_emails="mock@test.com",
        subject="Mock Test",
        html_content="<p>This is a mock test</p>"
    )

    print(f"Result: {result}")


def check_configuration():
    """Check email configuration"""
    print("\n" + "=" * 70)
    print("⚙️  CONFIGURATION CHECK")
    print("=" * 70)

    # Check SendGrid configuration
    api_key = os.getenv('SENDGRID_API_KEY')
    if api_key:
        print(f"✓ SENDGRID_API_KEY: {api_key[:20]}...")
        if not api_key.startswith('SG.'):
            print("  ⚠️  Warning: Key doesn't start with 'SG.'")
    else:
        print("✗ SENDGRID_API_KEY: Not configured")

    # Check environment
    env = os.getenv('ENVIRONMENT', 'development')
    print(f"✓ ENVIRONMENT: {env}")

    # Check mock setting
    use_mock = os.getenv('EMAIL_USE_MOCK', 'false')
    print(f"✓ EMAIL_USE_MOCK: {use_mock}")

    # Check other email settings
    print(f"✓ DEFAULT_FROM_EMAIL: {os.getenv('DEFAULT_FROM_EMAIL', 'noreply@toolboxai.com')}")
    print(f"✓ EMAIL_SANDBOX_MODE: {os.getenv('EMAIL_SANDBOX_MODE', 'false')}")


def main():
    """Run all tests"""
    print("\n" + "🔧" * 35)
    print("\n        EMAIL SERVICE COMPLETE TEST SUITE")
    print("\n" + "🔧" * 35)

    # Check configuration
    check_configuration()

    # Run async tests
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        # Test with automatic service selection
        loop.run_until_complete(test_email_service())

        # Test with forced mock
        loop.run_until_complete(test_with_mock())

    finally:
        loop.close()

    # Summary
    print("\n" + "=" * 70)
    print("📊 TEST SUMMARY")
    print("=" * 70)

    api_key = os.getenv('SENDGRID_API_KEY')
    if api_key and api_key.startswith('SG.'):
        print("""
✅ SendGrid is configured

   To use SendGrid for real emails:
   1. Ensure your API key is valid
   2. Check your SendGrid dashboard for the emails

   If the API key is invalid, the system will automatically
   fall back to MockEmailService for development.
""")
    else:
        print("""
ℹ️  Using MockEmailService (no SendGrid API key)

   To enable real email sending:
   1. Get a SendGrid API key from: https://app.sendgrid.com
   2. Add to your .env file:
      SENDGRID_API_KEY=SG.your_key_here

   For now, emails are being logged but not sent.
   This is perfect for development and testing!
""")

    print("✨ All tests completed!")


if __name__ == "__main__":
    main()