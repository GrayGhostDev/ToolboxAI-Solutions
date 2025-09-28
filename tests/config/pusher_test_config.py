"""
Pusher Test Configuration

Central configuration for all Pusher-related tests including:
- Test environment setup
- Mock configurations
- Performance thresholds
- Test data generators
"""

import os
from typing import Dict, Any, List
from dataclasses import dataclass


@dataclass
class PusherTestConfig:
    """Configuration class for Pusher tests"""

    # Environment settings
    test_environment: str = "test"
    frontend_url: str = "http://localhost:5179"
    backend_url: str = "http://localhost:8009"

    # Pusher settings
    pusher_key: str = "test-pusher-key"
    pusher_cluster: str = "us2"
    pusher_auth_endpoint: str = "/api/v1/pusher/auth"

    # Performance thresholds
    max_connection_time_ms: int = 2000
    max_message_latency_ms: int = 100
    min_throughput_per_sec: int = 100
    max_memory_usage_mb: int = 500
    max_cpu_usage_percent: int = 80

    # Test limits
    max_concurrent_connections: int = 1000
    max_channels_per_connection: int = 100
    max_message_size_kb: int = 1024

    # Retry settings
    max_retry_attempts: int = 3
    retry_delay_ms: int = 1000

    # Timeout settings
    connection_timeout_ms: int = 10000
    message_timeout_ms: int = 5000
    test_timeout_ms: int = 30000


# Global test configuration
TEST_CONFIG = PusherTestConfig()

# Environment-specific overrides
if os.getenv("CI") == "true":
    # CI environment adjustments
    TEST_CONFIG.max_connection_time_ms = 5000
    TEST_CONFIG.max_message_latency_ms = 200
    TEST_CONFIG.min_throughput_per_sec = 50
    TEST_CONFIG.test_timeout_ms = 60000

if os.getenv("PERFORMANCE_TEST") == "true":
    # Performance test mode
    TEST_CONFIG.max_concurrent_connections = 5000
    TEST_CONFIG.max_channels_per_connection = 500
    TEST_CONFIG.min_throughput_per_sec = 500


# Test channel configurations
CHANNEL_CONFIGS = {
    "public": {
        "prefix": "",
        "auth_required": False,
        "presence": False
    },
    "private": {
        "prefix": "private-",
        "auth_required": True,
        "presence": False
    },
    "presence": {
        "prefix": "presence-",
        "auth_required": True,
        "presence": True
    }
}

# Test message templates
MESSAGE_TEMPLATES = {
    "content_progress": {
        "type": "content_progress",
        "payload": {
            "requestId": "test-request-{id}",
            "stage": "generating",
            "percentage": 50,
            "message": "Generating content...",
            "estimatedTimeRemaining": 30
        }
    },
    "content_complete": {
        "type": "content_complete",
        "payload": {
            "requestId": "test-request-{id}",
            "status": "completed",
            "content": {
                "scripts": ["script1.lua", "script2.lua"],
                "terrain": {"type": "hills"},
                "assets": ["tree", "rock"],
                "quiz": {"questions": []}
            }
        }
    },
    "system_notification": {
        "type": "system_notification",
        "payload": {
            "id": "notification-{id}",
            "type": "info",
            "title": "Test Notification",
            "message": "This is a test notification",
            "timestamp": None,  # Will be set dynamically
            "dismissible": True
        }
    },
    "user_message": {
        "type": "user_message",
        "payload": {
            "id": "msg-{id}",
            "userId": "user-{user_id}",
            "userName": "Test User {user_id}",
            "content": "Hello from user {user_id}!",
            "timestamp": None  # Will be set dynamically
        }
    },
    "analytics_update": {
        "type": "analytics_update",
        "payload": {
            "metric": "user_activity",
            "value": 100,
            "timestamp": None  # Will be set dynamically
        }
    }
}

# Performance test scenarios
PERFORMANCE_SCENARIOS = {
    "light_load": {
        "concurrent_connections": 10,
        "messages_per_second": 10,
        "duration_seconds": 60,
        "channels_per_connection": 5
    },
    "medium_load": {
        "concurrent_connections": 100,
        "messages_per_second": 100,
        "duration_seconds": 300,
        "channels_per_connection": 10
    },
    "heavy_load": {
        "concurrent_connections": 500,
        "messages_per_second": 500,
        "duration_seconds": 600,
        "channels_per_connection": 20
    },
    "stress_test": {
        "concurrent_connections": 1000,
        "messages_per_second": 1000,
        "duration_seconds": 300,
        "channels_per_connection": 50
    }
}

# Test user data generators
def generate_test_user(user_id: int) -> Dict[str, Any]:
    """Generate test user data"""
    return {
        "id": f"test-user-{user_id}",
        "name": f"Test User {user_id}",
        "email": f"user{user_id}@test.com",
        "role": "student" if user_id % 2 == 0 else "teacher",
        "avatar": f"avatar{user_id}.png",
        "status": "online"
    }

def generate_test_classroom(classroom_id: int, member_count: int = 10) -> Dict[str, Any]:
    """Generate test classroom data"""
    return {
        "id": f"classroom-{classroom_id}",
        "name": f"Test Classroom {classroom_id}",
        "members": [generate_test_user(i) for i in range(member_count)],
        "teacher": generate_test_user(0),  # First user is teacher
        "created_at": "2024-01-01T00:00:00Z"
    }

def generate_test_message(message_id: int, user_id: int = 1) -> Dict[str, Any]:
    """Generate test message"""
    import time
    template = MESSAGE_TEMPLATES["user_message"].copy()
    template["payload"]["id"] = template["payload"]["id"].format(id=message_id)
    template["payload"]["userId"] = template["payload"]["userId"].format(user_id=user_id)
    template["payload"]["userName"] = template["payload"]["userName"].format(user_id=user_id)
    template["payload"]["content"] = template["payload"]["content"].format(user_id=user_id)
    template["payload"]["timestamp"] = int(time.time() * 1000)
    return template

def generate_bulk_messages(count: int, template_name: str = "user_message") -> List[Dict[str, Any]]:
    """Generate bulk test messages"""
    import time
    messages = []

    for i in range(count):
        template = MESSAGE_TEMPLATES[template_name].copy()

        # Replace placeholders
        if "{id}" in str(template):
            template = str(template).replace("{id}", str(i))
            template = eval(template)  # Convert back to dict

        # Set timestamp
        if "timestamp" in template["payload"] and template["payload"]["timestamp"] is None:
            template["payload"]["timestamp"] = int(time.time() * 1000) + i

        messages.append(template)

    return messages

# Browser test configurations
BROWSER_CONFIG = {
    "headless": True,
    "viewport": {"width": 1280, "height": 720},
    "timeout": 30000,
    "slow_mo": 0,  # No slow motion for tests
    "args": [
        "--no-sandbox",
        "--disable-dev-shm-usage",
        "--disable-gpu",
        "--disable-background-timer-throttling",
        "--disable-backgrounding-occluded-windows",
        "--disable-renderer-backgrounding"
    ]
}

# E2E test selectors
SELECTORS = {
    # Authentication
    "login_email": "[data-testid=email-input]",
    "login_password": "[data-testid=password-input]",
    "login_button": "[data-testid=login-button]",

    # Dashboard
    "dashboard_container": "[data-testid=dashboard-container]",
    "connection_status": "[data-testid=connection-status]",
    "reconnection_indicator": "[data-testid=reconnection-indicator]",

    # Content Generation
    "generate_button": "[data-testid=generate-button]",
    "progress_container": "[data-testid=progress-container]",
    "progress_bar": "[data-testid=progress-bar]",
    "stage_message": "[data-testid=stage-message]",
    "generation_complete": "[data-testid=generation-complete]",
    "content_preview": "[data-testid=content-preview]",

    # Collaboration
    "collaboration_workspace": "[data-testid=collaboration-workspace]",
    "presence_members": "[data-testid=presence-members]",
    "member_item": "[data-testid=member-item]",
    "typing_indicator": "[data-testid=typing-indicator]",
    "collaboration_input": "[data-testid=collaboration-input]",
    "send_message_button": "[data-testid=send-message-button]",
    "message_item": "[data-testid=message-item]",

    # Notifications
    "system_notification": "[data-testid=system-notification]",
    "notification_title": "[data-testid=notification-title]",
    "dismiss_notification": "[data-testid=dismiss-notification]",

    # Analytics
    "analytics_dashboard": "[data-testid=analytics-dashboard]",
    "user_activity_chart": "[data-testid=user-activity-chart]",
    "content_generation_chart": "[data-testid=content-generation-chart]",
    "system_metrics_chart": "[data-testid=system-metrics-chart]"
}

# Test environment variables
TEST_ENV_VARS = {
    "NODE_ENV": "test",
    "VITE_API_BASE_URL": TEST_CONFIG.backend_url,
    "VITE_WS_URL": TEST_CONFIG.backend_url,
    "VITE_PUSHER_KEY": TEST_CONFIG.pusher_key,
    "VITE_PUSHER_CLUSTER": TEST_CONFIG.pusher_cluster,
    "VITE_PUSHER_AUTH_ENDPOINT": TEST_CONFIG.pusher_auth_endpoint,
    "VITE_ENABLE_WEBSOCKET": "true",
    "TEST_MODE": "true"
}

# Mock configurations
MOCK_CONFIGS = {
    "pusher_service": {
        "auto_connect": False,
        "simulate_latency": True,
        "default_latency_ms": 50,
        "error_rate": 0.0,
        "max_connections": 10000,
        "max_channels": 1000
    },
    "api_client": {
        "base_url": TEST_CONFIG.backend_url,
        "timeout_ms": 5000,
        "retry_attempts": 2,
        "mock_responses": True
    }
}

# Export configuration for external use
__all__ = [
    "TEST_CONFIG",
    "CHANNEL_CONFIGS",
    "MESSAGE_TEMPLATES",
    "PERFORMANCE_SCENARIOS",
    "BROWSER_CONFIG",
    "SELECTORS",
    "TEST_ENV_VARS",
    "MOCK_CONFIGS",
    "generate_test_user",
    "generate_test_classroom",
    "generate_test_message",
    "generate_bulk_messages"
]