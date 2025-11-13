"""
Twilio Service Implementation

Production-ready Twilio integration following 2025 best practices
Supports SMS, Voice, Video, and Verify services
Implements webhook security and rate limiting
"""

import asyncio
import logging
import os
import time
from dataclasses import dataclass
from functools import wraps
from typing import Any

from twilio.base import exceptions as twilio_exceptions
from twilio.jwt.access_token import AccessToken
from twilio.jwt.access_token.grants import VideoGrant
from twilio.request_validator import RequestValidator
from twilio.rest import Client

logger = logging.getLogger(__name__)


@dataclass
class SMSMessage:
    """SMS message data"""

    to_number: str
    body: str
    from_number: str | None = None
    media_urls: list[str] | None = None
    status_callback: str | None = None


@dataclass
class VerificationRequest:
    """Verification request data"""

    to_number: str
    channel: str = "sms"  # sms, call, email, whatsapp
    custom_message: str | None = None
    locale: str = "en"


class RateLimiter:
    """Simple rate limiter for API calls"""

    def __init__(self, max_calls: int = 600, period: int = 60):
        self.max_calls = max_calls
        self.period = period
        self.calls = []

    def is_allowed(self) -> bool:
        """Check if a call is allowed within rate limits"""
        now = time.time()
        # Remove old calls outside the period
        self.calls = [call_time for call_time in self.calls if now - call_time < self.period]

        if len(self.calls) < self.max_calls:
            self.calls.append(now)
            return True
        return False


def rate_limited(max_calls: int = 600, period: int = 60):
    """Decorator for rate-limited functions"""
    limiter = RateLimiter(max_calls, period)

    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            if not limiter.is_allowed():
                logger.warning(f"Rate limit exceeded for {func.__name__}")
                raise Exception("Rate limit exceeded. Please try again later.")
            return await func(*args, **kwargs)

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            if not limiter.is_allowed():
                logger.warning(f"Rate limit exceeded for {func.__name__}")
                raise Exception("Rate limit exceeded. Please try again later.")
            return func(*args, **kwargs)

        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper

    return decorator


class TwilioService:
    """
    Twilio service implementation following 2025 best practices

    Features:
    - SMS and MMS messaging
    - Voice calls
    - Video conferencing
    - Phone number verification
    - Webhook security validation
    - Rate limiting
    - Error handling and retries
    """

    def __init__(self):
        """Initialize Twilio client with API credentials"""
        # Use API SID and Secret for production (not Account SID/Auth Token)
        self.api_sid = os.getenv("TWILIO_API_SID")
        self.api_secret = os.getenv("TWILIO_API_SECRET")
        self.account_sid = os.getenv("TWILIO_ACCOUNT_SID")
        self.auth_token = os.getenv("TWILIO_AUTH_TOKEN")
        self.from_number = os.getenv("TWILIO_PHONE_NUMBER")
        self.messaging_service_sid = os.getenv("TWILIO_MESSAGING_SERVICE_SID")
        self.verify_service_sid = os.getenv("TWILIO_VERIFY_SERVICE_SID")

        if not self.account_sid or not self.auth_token:
            logger.error("Twilio credentials not configured")
            self.client = None
            self.webhook_validator = None
        else:
            try:
                # Initialize Twilio client
                self.client = Client(self.account_sid, self.auth_token)

                # Initialize webhook validator for security
                self.webhook_validator = RequestValidator(self.auth_token)

                logger.info("Twilio client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Twilio client: {e}")
                self.client = None
                self.webhook_validator = None

        # Initialize rate limiter (600 requests per minute as per Twilio limits)
        self.rate_limiter = RateLimiter(max_calls=600, period=60)

    # SMS/MMS Services
    @rate_limited(max_calls=100, period=60)  # More conservative for SMS
    async def send_sms(
        self,
        to_number: str,
        body: str,
        from_number: str | None = None,
        media_urls: list[str] | None = None,
        status_callback: str | None = None,
    ) -> str | None:
        """
        Send SMS or MMS message

        Args:
            to_number: Recipient phone number (E.164 format)
            body: Message body
            from_number: Sender phone number (uses default if not provided)
            media_urls: List of media URLs for MMS
            status_callback: URL for status callbacks

        Returns:
            Message SID if successful, None otherwise
        """
        if not self.client:
            logger.error("Twilio client not initialized")
            return None

        try:
            message_params = {
                "to": to_number,
                "body": body,
                "from_": from_number or self.from_number,
            }

            # Add messaging service if configured (better deliverability)
            if self.messaging_service_sid and not from_number:
                message_params["messaging_service_sid"] = self.messaging_service_sid
                del message_params["from_"]

            # Add media for MMS
            if media_urls:
                message_params["media_url"] = media_urls

            # Add status callback for tracking
            if status_callback:
                message_params["status_callback"] = status_callback

            message = self.client.messages.create(**message_params)

            logger.info(f"SMS sent successfully: {message.sid}")
            return message.sid

        except twilio_exceptions.TwilioRestException as e:
            logger.error(f"Twilio error sending SMS: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error sending SMS: {e}")
            return None

    @rate_limited(max_calls=50, period=60)
    async def send_bulk_sms(
        self, messages: list[SMSMessage], batch_size: int = 10
    ) -> dict[str, Any]:
        """
        Send bulk SMS messages with batching

        Args:
            messages: List of SMS messages to send
            batch_size: Number of messages to send concurrently

        Returns:
            Dictionary with success and failure counts
        """
        results = {"success": 0, "failed": 0, "message_sids": []}

        for i in range(0, len(messages), batch_size):
            batch = messages[i : i + batch_size]
            tasks = []

            for msg in batch:
                task = self.send_sms(
                    to_number=msg.to_number,
                    body=msg.body,
                    from_number=msg.from_number,
                    media_urls=msg.media_urls,
                    status_callback=msg.status_callback,
                )
                tasks.append(task)

            # Wait for batch to complete
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)

            for result in batch_results:
                if isinstance(result, str) and result:
                    results["success"] += 1
                    results["message_sids"].append(result)
                else:
                    results["failed"] += 1

            # Add delay between batches to respect rate limits
            if i + batch_size < len(messages):
                await asyncio.sleep(1)

        return results

    # Verification Services
    @rate_limited(max_calls=100, period=60)
    async def send_verification(
        self,
        to_number: str,
        channel: str = "sms",
        custom_message: str | None = None,
        locale: str = "en",
    ) -> str | None:
        """
        Send verification code via Twilio Verify

        Args:
            to_number: Phone number to verify (E.164 format)
            channel: Verification channel (sms, call, email, whatsapp)
            custom_message: Custom message template
            locale: Language locale

        Returns:
            Verification SID if successful
        """
        if not self.client or not self.verify_service_sid:
            logger.error("Twilio Verify not configured")
            return None

        try:
            verification_params = {"to": to_number, "channel": channel, "locale": locale}

            if custom_message:
                verification_params["custom_friendly_name"] = custom_message

            verification = self.client.verify.v2.services(
                self.verify_service_sid
            ).verifications.create(**verification_params)

            logger.info(f"Verification sent: {verification.sid}")
            return verification.sid

        except twilio_exceptions.TwilioRestException as e:
            logger.error(f"Twilio Verify error: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error in verification: {e}")
            return None

    @rate_limited(max_calls=100, period=60)
    async def check_verification(self, to_number: str, code: str) -> bool:
        """
        Check verification code

        Args:
            to_number: Phone number being verified
            code: Verification code entered by user

        Returns:
            True if verification successful, False otherwise
        """
        if not self.client or not self.verify_service_sid:
            logger.error("Twilio Verify not configured")
            return False

        try:
            verification_check = self.client.verify.v2.services(
                self.verify_service_sid
            ).verification_checks.create(to=to_number, code=code)

            success = verification_check.status == "approved"

            if success:
                logger.info(f"Verification successful for {to_number}")
            else:
                logger.warning(f"Verification failed for {to_number}")

            return success

        except twilio_exceptions.TwilioRestException as e:
            logger.error(f"Twilio Verify check error: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error checking verification: {e}")
            return False

    # Video Services
    def create_video_room(
        self,
        room_name: str,
        max_participants: int = 50,
        record_participants_on_connect: bool = False,
    ) -> dict[str, Any] | None:
        """
        Create a video room for conferencing

        Args:
            room_name: Unique room name
            max_participants: Maximum number of participants
            record_participants_on_connect: Whether to record

        Returns:
            Room details if successful
        """
        if not self.client:
            logger.error("Twilio client not initialized")
            return None

        try:
            room = self.client.video.v1.rooms.create(
                unique_name=room_name,
                type="group",
                max_participants=max_participants,
                record_participants_on_connect=record_participants_on_connect,
            )

            return {
                "sid": room.sid,
                "name": room.unique_name,
                "status": room.status,
                "max_participants": room.max_participants,
                "url": room.url,
            }

        except Exception as e:
            logger.error(f"Error creating video room: {e}")
            return None

    def generate_video_token(
        self, identity: str, room_name: str | None = None, ttl: int = 3600
    ) -> str | None:
        """
        Generate access token for video participant

        Args:
            identity: Unique user identity
            room_name: Room to grant access to
            ttl: Token time-to-live in seconds

        Returns:
            JWT access token
        """
        if not self.api_sid or not self.api_secret:
            logger.error("Twilio API credentials not configured")
            return None

        try:
            # Create access token
            token = AccessToken(
                self.account_sid, self.api_sid, self.api_secret, identity=identity, ttl=ttl
            )

            # Add video grant
            video_grant = VideoGrant(room=room_name) if room_name else VideoGrant()
            token.add_grant(video_grant)

            return token.to_jwt()

        except Exception as e:
            logger.error(f"Error generating video token: {e}")
            return None

    # Webhook Security
    def validate_webhook(self, url: str, params: dict[str, str], signature: str) -> bool:
        """
        Validate Twilio webhook request signature

        Args:
            url: Full webhook URL
            params: Request parameters
            signature: X-Twilio-Signature header value

        Returns:
            True if signature is valid
        """
        if not self.webhook_validator:
            logger.error("Webhook validator not initialized")
            return False

        try:
            return self.webhook_validator.validate(url, params, signature)
        except Exception as e:
            logger.error(f"Error validating webhook: {e}")
            return False

    # Utility Methods
    async def get_message_status(self, message_sid: str) -> str | None:
        """Get status of a sent message"""
        if not self.client:
            return None

        try:
            message = self.client.messages(message_sid).fetch()
            return message.status
        except Exception as e:
            logger.error(f"Error fetching message status: {e}")
            return None

    async def get_phone_number_info(self, phone_number: str) -> dict[str, Any] | None:
        """
        Look up phone number information

        Args:
            phone_number: Phone number to look up (E.164 format)

        Returns:
            Phone number details
        """
        if not self.client:
            return None

        try:
            phone_number = self.client.lookups.v2.phone_numbers(phone_number).fetch()

            return {
                "phone_number": phone_number.phone_number,
                "country_code": phone_number.country_code,
                "national_format": phone_number.national_format,
                "valid": phone_number.valid,
                "validation_errors": phone_number.validation_errors,
            }
        except Exception as e:
            logger.error(f"Error looking up phone number: {e}")
            return None

    def close(self):
        """Clean up Twilio client resources"""
        # Twilio client doesn't require explicit cleanup
        logger.info("Twilio service closed")


# Global service instance
twilio_service = TwilioService()
