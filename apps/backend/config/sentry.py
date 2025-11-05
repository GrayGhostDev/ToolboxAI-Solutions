"""
============================================
SENTRY CONFIGURATION - BACKEND
============================================
Sentry monitoring and error tracking setup
Updated: 2025-11-02
============================================
"""

import os
import logging
from typing import Optional

import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.redis import RedisIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
from sentry_sdk.integrations.logging import LoggingIntegration

logger = logging.getLogger(__name__)


def init_sentry() -> None:
    """
    Initialize Sentry for error tracking and performance monitoring
    """
    sentry_dsn = os.getenv('SENTRY_DSN')
    environment = os.getenv('ENVIRONMENT', 'development')

    # Only initialize if DSN is provided and not in development
    if not sentry_dsn or environment == 'development':
        logger.info("Sentry disabled in development mode")
        return

    try:
        sentry_sdk.init(
            dsn=sentry_dsn,
            environment=environment,
            release=os.getenv('SENTRY_RELEASE', 'unknown'),

            # Integrations
            integrations=[
                FastApiIntegration(
                    transaction_style='url',
                    failed_request_status_codes=[500, 502, 503, 504],
                ),
                SqlalchemyIntegration(),
                RedisIntegration(),
                LoggingIntegration(
                    level=logging.INFO,
                    event_level=logging.ERROR,
                ),
            ],

            # Performance Monitoring
            traces_sample_rate=0.1,  # 10% of transactions
            profiles_sample_rate=0.1,  # 10% of profiling data

            # Error filtering
            before_send=before_send,

            # Additional options
            attach_stacktrace=True,
            send_default_pii=False,  # Don't send personally identifiable information
            max_breadcrumbs=50,

            # Request data (updated for Sentry SDK v2.0+)
            max_request_body_size='medium',  # 'never', 'small', 'medium', 'always'
        )

        logger.info("✅ Sentry initialized for production monitoring")

    except Exception as e:
        logger.error(f"Failed to initialize Sentry: {e}")


def before_send(event, hint):
    """
    Filter events before sending to Sentry
    """
    # Filter out sensitive data
    if 'request' in event:
        if 'headers' in event['request']:
            # Remove sensitive headers
            headers_to_remove = [
                'Authorization',
                'X-API-Key',
                'Cookie',
                'X-Auth-Token',
            ]
            for header in headers_to_remove:
                event['request']['headers'].pop(header, None)

        if 'data' in event['request']:
            # Remove sensitive fields from request data
            sensitive_fields = ['password', 'token', 'secret', 'api_key']
            if isinstance(event['request']['data'], dict):
                for field in sensitive_fields:
                    if field in event['request']['data']:
                        event['request']['data'][field] = '[Filtered]'

    # Filter out specific exceptions
    if 'exception' in event:
        for exception in event['exception'].get('values', []):
            exc_type = exception.get('type', '')
            exc_value = exception.get('value', '')

            # Ignore certain exceptions
            if exc_type in ['KeyboardInterrupt', 'SystemExit']:
                return None

            # Ignore connection errors
            if 'ConnectionError' in exc_type or 'TimeoutError' in exc_type:
                return None

            # Ignore 404 errors
            if '404' in exc_value or 'Not Found' in exc_value:
                return None

    return event


def set_user_context(user_id: str, email: Optional[str] = None, username: Optional[str] = None) -> None:
    """
    Set user context for Sentry
    """
    sentry_sdk.set_user({
        'id': user_id,
        'email': email,
        'username': username,
    })


def clear_user_context() -> None:
    """
    Clear user context
    """
    sentry_sdk.set_user(None)


def capture_exception(exception: Exception, context: Optional[dict] = None) -> None:
    """
    Capture an exception with optional context
    """
    if context:
        sentry_sdk.set_context('custom', context)
    sentry_sdk.capture_exception(exception)


def capture_message(message: str, level: str = 'info') -> None:
    """
    Capture a custom message
    """
    sentry_sdk.capture_message(message, level=level)


def add_breadcrumb(message: str, category: str = 'default', level: str = 'info', data: Optional[dict] = None) -> None:
    """
    Add a breadcrumb for debugging
    """
    sentry_sdk.add_breadcrumb(
        message=message,
        category=category,
        level=level,
        data=data or {},
    )

