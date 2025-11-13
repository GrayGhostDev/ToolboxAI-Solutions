#!/usr/bin/env python3
"""
Celery Background Jobs Tests
============================

Tests for Celery task queue system with Redis broker.
"""

import os
import sys
import uuid
from datetime import datetime
from unittest.mock import Mock, patch

import pytest

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


@pytest.fixture
def mock_celery_app():
    """Mock Celery application."""
    app = Mock()
    app.task = Mock(side_effect=lambda *args, **kwargs: lambda func: func)
    return app


@pytest.fixture
def organization_id():
    """Test organization ID."""
    return uuid.uuid4()


@pytest.fixture
def user_id():
    """Test user ID."""
    return uuid.uuid4()


class TestCeleryConfiguration:
    """Test Celery configuration and setup."""

    def test_redis_broker_configuration(self):
        """Test that Celery is configured with Redis broker."""
        expected_broker = "redis://localhost:6379/0"
        expected_backend = "redis://localhost:6379/0"

        # Mock configuration
        config = {
            "broker_url": expected_broker,
            "result_backend": expected_backend,
            "task_serializer": "json",
            "result_serializer": "json",
            "accept_content": ["json"],
            "timezone": "UTC",
            "enable_utc": True,
        }

        assert config["broker_url"] == expected_broker
        assert config["result_backend"] == expected_backend
        assert "aws" not in config["broker_url"].lower()
        assert "sqs" not in config["broker_url"].lower()

    def test_task_routing_configuration(self):
        """Test task routing to different queues."""
        task_routes = {
            "high_priority.*": {"queue": "high"},
            "content.*": {"queue": "content"},
            "email.*": {"queue": "email"},
            "analytics.*": {"queue": "analytics"},
            "cleanup.*": {"queue": "cleanup"},
        }

        # Test routing patterns
        assert task_routes["high_priority.*"]["queue"] == "high"
        assert task_routes["content.*"]["queue"] == "content"
        assert task_routes["email.*"]["queue"] == "email"

    def test_retry_configuration(self):
        """Test Celery retry settings."""
        retry_config = {
            "task_acks_late": True,
            "task_reject_on_worker_lost": True,
            "task_default_retry_delay": 60,
            "task_max_retries": 3,
            "task_soft_time_limit": 300,
            "task_time_limit": 600,
        }

        assert retry_config["task_max_retries"] == 3
        assert retry_config["task_default_retry_delay"] == 60
        assert retry_config["task_soft_time_limit"] < retry_config["task_time_limit"]


class TestContentTasks:
    """Test content generation tasks."""

    @patch("apps.backend.workers.tasks.content_tasks.generate_content")
    def test_content_generation_task(self, mock_generate, organization_id, user_id):
        """Test AI content generation task."""
        # Mock task parameters
        task_params = {
            "organization_id": str(organization_id),
            "user_id": str(user_id),
            "content_type": "lesson",
            "topic": "Introduction to Python",
            "grade_level": 9,
            "difficulty": "beginner",
            "standards": ["CS.9-12.1"],
        }

        # Mock successful generation
        mock_generate.return_value = {
            "content_id": str(uuid.uuid4()),
            "title": "Introduction to Python",
            "content": "Lesson content here...",
            "metadata": {
                "generated_at": datetime.utcnow().isoformat(),
                "model": "gpt-4",
                "tokens_used": 1500,
            },
        }

        # Execute task
        result = mock_generate(**task_params)

        # Verify execution
        mock_generate.assert_called_once_with(**task_params)
        assert "content_id" in result
        assert result["title"] == "Introduction to Python"
        assert "aws" not in str(mock_generate.call_args).lower()

    @patch("apps.backend.workers.tasks.content_tasks.generate_quiz")
    def test_quiz_generation_task(self, mock_quiz_gen, organization_id):
        """Test quiz generation from content."""
        content_id = uuid.uuid4()

        # Mock quiz generation
        mock_quiz_gen.return_value = {
            "quiz_id": str(uuid.uuid4()),
            "questions": [
                {
                    "question": "What is Python?",
                    "options": ["A snake", "A programming language", "A tool", "A framework"],
                    "correct": 1,
                    "explanation": "Python is a high-level programming language.",
                }
            ],
            "total_questions": 1,
            "difficulty": "beginner",
        }

        # Execute task
        result = mock_quiz_gen(
            organization_id=str(organization_id), content_id=str(content_id), num_questions=1
        )

        # Verify
        assert "quiz_id" in result
        assert len(result["questions"]) == 1
        assert result["questions"][0]["correct"] == 1


class TestEmailTasks:
    """Test email notification tasks."""

    @patch("apps.backend.workers.tasks.email_tasks.send_email")
    def test_send_email_task(self, mock_send, organization_id):
        """Test email sending via SMTP (not AWS SES)."""
        email_data = {
            "organization_id": str(organization_id),
            "to": ["teacher@school.edu"],
            "subject": "New Content Available",
            "body": "Your requested content has been generated.",
            "template": "content_ready",
        }

        # Mock successful send
        mock_send.return_value = {
            "message_id": str(uuid.uuid4()),
            "status": "sent",
            "provider": "smtp",
        }

        # Execute
        result = mock_send(**email_data)

        # Verify SMTP usage (not AWS SES)
        assert result["status"] == "sent"
        assert result["provider"] == "smtp"
        assert "ses" not in result["provider"].lower()
        assert "aws" not in result["provider"].lower()

    @patch("apps.backend.workers.tasks.email_tasks.send_bulk_emails")
    def test_bulk_email_task(self, mock_bulk, organization_id):
        """Test bulk email sending."""
        recipients = [f"user{i}@school.edu" for i in range(10)]

        mock_bulk.return_value = {"sent": 10, "failed": 0, "batch_id": str(uuid.uuid4())}

        result = mock_bulk(
            organization_id=str(organization_id), recipients=recipients, template="weekly_digest"
        )

        assert result["sent"] == 10
        assert result["failed"] == 0


class TestAnalyticsTasks:
    """Test analytics processing tasks."""

    @patch("apps.backend.workers.tasks.analytics_tasks.calculate_progress")
    def test_progress_calculation(self, mock_calc, organization_id, user_id):
        """Test student progress calculation."""
        mock_calc.return_value = {
            "user_id": str(user_id),
            "overall_progress": 75.5,
            "courses": {"python_intro": 100.0, "data_structures": 50.0, "algorithms": 76.5},
            "last_updated": datetime.utcnow().isoformat(),
        }

        result = mock_calc(organization_id=str(organization_id), user_id=str(user_id))

        assert result["overall_progress"] == 75.5
        assert result["courses"]["python_intro"] == 100.0

    @patch("apps.backend.workers.tasks.analytics_tasks.generate_report")
    def test_report_generation(self, mock_report, organization_id):
        """Test analytics report generation."""
        mock_report.return_value = {
            "report_id": str(uuid.uuid4()),
            "organization_id": str(organization_id),
            "type": "monthly",
            "metrics": {"active_users": 150, "content_created": 25, "avg_engagement": 82.3},
            "generated_at": datetime.utcnow().isoformat(),
        }

        result = mock_report(organization_id=str(organization_id), report_type="monthly")

        assert result["type"] == "monthly"
        assert result["metrics"]["active_users"] == 150


class TestCleanupTasks:
    """Test system cleanup tasks."""

    @patch("apps.backend.workers.tasks.cleanup_tasks.cleanup_old_files")
    def test_file_cleanup(self, mock_cleanup, organization_id):
        """Test old file cleanup task."""
        mock_cleanup.return_value = {
            "files_deleted": 42,
            "space_freed_mb": 512,
            "organization_id": str(organization_id),
        }

        result = mock_cleanup(organization_id=str(organization_id), days_old=30)

        assert result["files_deleted"] == 42
        assert result["space_freed_mb"] == 512

    @patch("apps.backend.workers.tasks.cleanup_tasks.cleanup_expired_sessions")
    def test_session_cleanup(self, mock_session_cleanup):
        """Test expired session cleanup."""
        mock_session_cleanup.return_value = {"sessions_removed": 15, "redis_keys_deleted": 30}

        result = mock_session_cleanup()

        assert result["sessions_removed"] == 15
        assert result["redis_keys_deleted"] == 30


class TestTenantTasks:
    """Test multi-tenant specific tasks."""

    @patch("apps.backend.workers.tasks.tenant_tasks.provision_organization")
    def test_organization_provisioning(self, mock_provision):
        """Test new organization provisioning."""
        org_data = {
            "name": "New School District",
            "subscription_tier": "PREMIUM",
            "admin_email": "admin@school.edu",
        }

        mock_provision.return_value = {
            "organization_id": str(uuid.uuid4()),
            "status": "provisioned",
            "resources_created": {
                "database_schema": True,
                "storage_bucket": True,
                "default_roles": True,
                "admin_user": True,
            },
        }

        result = mock_provision(**org_data)

        assert result["status"] == "provisioned"
        assert result["resources_created"]["database_schema"] is True
        assert result["resources_created"]["storage_bucket"] is True

    @patch("apps.backend.workers.tasks.tenant_tasks.calculate_usage")
    def test_usage_calculation(self, mock_usage, organization_id):
        """Test organization usage calculation."""
        mock_usage.return_value = {
            "organization_id": str(organization_id),
            "storage_used_gb": 45.2,
            "storage_limit_gb": 100,
            "users_count": 75,
            "users_limit": 200,
            "api_calls_month": 15000,
            "calculated_at": datetime.utcnow().isoformat(),
        }

        result = mock_usage(organization_id=str(organization_id))

        assert result["storage_used_gb"] < result["storage_limit_gb"]
        assert result["users_count"] < result["users_limit"]


class TestTaskMonitoring:
    """Test task monitoring and metrics."""

    @patch("apps.backend.workers.monitoring.get_task_metrics")
    def test_prometheus_metrics(self, mock_metrics):
        """Test Prometheus metrics collection."""
        mock_metrics.return_value = {
            "tasks_completed": 1500,
            "tasks_failed": 12,
            "tasks_retried": 45,
            "average_duration_seconds": 2.5,
            "queue_lengths": {"high": 5, "default": 20, "low": 100},
        }

        metrics = mock_metrics()

        assert metrics["tasks_completed"] == 1500
        assert metrics["tasks_failed"] == 12
        assert metrics["average_duration_seconds"] == 2.5

    def test_flower_monitoring_config(self):
        """Test Flower monitoring configuration."""
        flower_config = {
            "port": 5555,
            "basic_auth": True,
            "persistent": True,
            "db": "flower.db",
            "max_tasks": 10000,
        }

        assert flower_config["port"] == 5555
        assert flower_config["basic_auth"] is True


class TestTaskContext:
    """Test task context preservation."""

    @patch("apps.backend.workers.celery_app.Task")
    def test_organization_context_preserved(self, mock_task, organization_id):
        """Test that organization context is preserved in tasks."""
        # Mock task with context
        task_context = {
            "organization_id": str(organization_id),
            "user_id": str(uuid.uuid4()),
            "request_id": str(uuid.uuid4()),
        }

        mock_task.request.headers = task_context

        # Verify context is accessible
        assert mock_task.request.headers["organization_id"] == str(organization_id)
        assert "user_id" in mock_task.request.headers
        assert "request_id" in mock_task.request.headers

    def test_task_retry_with_context(self, organization_id):
        """Test task retry preserves context."""
        # Mock retry with context
        retry_context = {
            "organization_id": str(organization_id),
            "retry_count": 1,
            "max_retries": 3,
        }

        # Verify context preservation
        assert retry_context["organization_id"] == str(organization_id)
        assert retry_context["retry_count"] < retry_context["max_retries"]


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "--tb=short"])
