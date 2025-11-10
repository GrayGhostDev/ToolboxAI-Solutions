#!/usr/bin/env python3
"""
SendGrid Email Test Script
Tests the SendGrid integration by sending a simple test email
"""

import os
import sys
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add project to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_sendgrid_basic():
    """Test basic SendGrid email sending with minimal code"""
    print("=" * 60)
    print("SendGrid Basic Email Test")
    print("=" * 60)

    # Import SendGrid
    from sendgrid import SendGridAPIClient
    from sendgrid.helpers.mail import Mail

    # Get API key from environment
    api_key = os.getenv('SENDGRID_API_KEY')

    if not api_key:
        print("❌ ERROR: SENDGRID_API_KEY not found in environment")
        return False

    if not api_key.startswith('SG.'):
        print("⚠️  WARNING: API key format may be invalid (should start with 'SG.')")

    print(f"✓ API Key loaded: {api_key[:20]}...")

    # Create message
    message = Mail(
        from_email='noreply@toolboxai.com',
        to_emails='test@example.com',  # This can be any email for testing
        subject=f'SendGrid Test Email - {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}',
        html_content='<strong>Hello from SendGrid!</strong><br><br>This is a test email sent via the SendGrid Python SDK.<br><br>If you received this, the integration is working correctly!'
    )

    try:
        # Initialize SendGrid client
        sg = SendGridAPIClient(api_key)

        # Send the email
        print("\n📧 Sending test email...")
        response = sg.send(message)

        # Check response
        print(f"✓ Response Status Code: {response.status_code}")
        print(f"✓ Response Headers: {dict(response.headers)}")

        if response.status_code in [200, 202]:
            print("\n✅ SUCCESS: Email sent successfully through SendGrid!")
            return True
        else:
            print(f"\n⚠️  WARNING: Unexpected status code: {response.status_code}")
            return False

    except Exception as e:
        print(f"\n❌ ERROR: Failed to send email: {str(e)}")
        if hasattr(e, 'body'):
            print(f"   Error details: {e.body}")
        return False


def test_sendgrid_with_service():
    """Test SendGrid using our service implementation"""
    print("\n" + "=" * 60)
    print("SendGrid Service Integration Test")
    print("=" * 60)

    try:
        # Import our service
        from apps.backend.services.email.sendgrid import SendGridEmailService
        import asyncio

        # Create service instance
        service = SendGridEmailService()

        print(f"✓ Service initialized")
        print(f"  - From email: {service.from_email}")
        print(f"  - From name: {service.from_name}")
        print(f"  - Sandbox mode: {service.sandbox_mode}")
        print(f"  - Tracking enabled: {service.enable_tracking}")

        # Test sending an email
        async def send_test():
            result = await service.send_email(
                to_emails='test@example.com',
                subject=f'Service Test - {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}',
                html_content='<h2>Service Test Email</h2><p>This email was sent using the SendGridEmailService implementation.</p>',
                text_content='Service Test Email\n\nThis email was sent using the SendGridEmailService implementation.'
            )
            return result

        print("\n📧 Sending email through service...")
        result = asyncio.run(send_test())

        if result['success']:
            print(f"✅ SUCCESS: Email sent via service!")
            print(f"  - Message ID: {result.get('message_id')}")
            print(f"  - Status Code: {result.get('status_code')}")
            print(f"  - Provider: {result.get('provider')}")
            return True
        else:
            print(f"❌ FAILED: {result.get('error')}")
            return False

    except Exception as e:
        print(f"❌ ERROR in service test: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def check_eu_residency():
    """Check if EU data residency is configured"""
    print("\n" + "=" * 60)
    print("EU Data Residency Check")
    print("=" * 60)

    # Check for EU-specific configuration
    eu_api_key = os.getenv('SENDGRID_EU_API_KEY')
    eu_enabled = os.getenv('SENDGRID_EU_RESIDENCY', 'false').lower() == 'true'

    if eu_api_key or eu_enabled:
        print("✓ EU Data Residency configuration detected")

        # If EU is configured, we would use:
        # from sendgrid import SendGridAPIClient, set_sendgrid_data_residency
        # set_sendgrid_data_residency("eu")

        return True
    else:
        print("ℹ️  EU Data Residency not configured (using global region)")
        return False


def main():
    """Run all SendGrid tests"""
    print("\n🚀 Starting SendGrid Configuration Tests\n")

    # Check packages
    print("=" * 60)
    print("Package Installation Check")
    print("=" * 60)

    try:
        import sendgrid
        print(f"✓ sendgrid package installed (version {sendgrid.__version__})")
    except ImportError:
        print("❌ sendgrid package not installed")
        print("   Run: pip install sendgrid")
        return

    try:
        import python_http_client
        print(f"✓ python_http_client package installed")
    except ImportError:
        print("❌ python_http_client package not installed")

    # Run tests
    basic_success = test_sendgrid_basic()

    # Check EU residency
    check_eu_residency()

    # Test with our service
    service_success = test_sendgrid_with_service()

    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)

    if basic_success and service_success:
        print("✅ All tests passed! SendGrid is properly configured.")
        print("\n📝 Next steps:")
        print("   1. Check your SendGrid dashboard for the test emails")
        print("   2. Verify the emails show in the Activity Feed")
        print("   3. Configure your domain authentication in SendGrid")
        print("   4. Set up email templates as needed")
    elif basic_success:
        print("⚠️  Basic test passed but service test failed")
        print("   Check the service implementation for issues")
    else:
        print("❌ Tests failed. Please check:")
        print("   1. Your SENDGRID_API_KEY is valid")
        print("   2. Your SendGrid account is active")
        print("   3. You have sending permissions configured")
        print("   4. Your API key has full access permissions")


if __name__ == "__main__":
    main()