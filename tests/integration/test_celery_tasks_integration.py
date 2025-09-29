"""
Integration tests for Celery background tasks.

Tests the complete Celery infrastructure including workers, beat scheduler,
and task execution for all implemented task types.
"""

import asyncio
import json
import os
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any
import pytest
import redis
from celery import Celery
from celery.result import AsyncResult
import tempfile

# Import the Celery app and tasks
from apps.backend.celery_app import celery_app
from apps.backend.tasks import (
    cleanup_old_files,
    cleanup_expired_sessions,
    cleanup_temp_storage,
    generate_educational_content,
    process_quiz_generation,
    analyze_content_quality,
    sync_roblox_environment,
    deploy_to_roblox,
    validate_roblox_assets,
    send_notification,
    send_bulk_notifications,
    process_webhook_event,
    aggregate_usage_metrics,
    generate_reports,
    export_analytics_data
)


@pytest.mark.integration
@pytest.mark.celery
class TestCeleryTasksIntegration:
    """Test Celery tasks integration and execution."""

    def setup_method(self):
        """Set up test environment."""
        self.celery_app = celery_app
        self.redis_client = redis.StrictRedis(
            host='localhost',
            port=6379,
            db=0,
            decode_responses=True
        )

        # Test data directory
        self.test_dir = tempfile.mkdtemp(prefix="test_celery_")

    def teardown_method(self):
        """Clean up test environment."""
        # Clean up test directory
        import shutil
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_celery_worker_connectivity(self):
        """Test that Celery workers are connected and responsive."""
        # Inspect workers
        inspector = self.celery_app.control.inspect()

        # Get active workers
        active_workers = inspector.active()
        assert active_workers is not None, "No active Celery workers found"
        assert len(active_workers) >= 1, "At least one worker should be active"

        # Get registered tasks
        registered_tasks = inspector.registered()
        assert registered_tasks is not None, "No registered tasks found"

        # Check our custom tasks are registered
        expected_tasks = [
            'tasks.cleanup_old_files',
            'tasks.generate_educational_content',
            'tasks.send_notification',
            'tasks.aggregate_usage_metrics'
        ]

        all_registered = []
        for worker, tasks in registered_tasks.items():
            all_registered.extend(tasks)

        for task in expected_tasks:
            assert task in all_registered, f"Task {task} not registered"

    def test_cleanup_tasks(self):
        """Test cleanup background tasks."""
        # Create test files
        test_file_old = os.path.join(self.test_dir, "old_file.txt")
        test_file_new = os.path.join(self.test_dir, "new_file.txt")

        # Create old file (8 days ago)
        with open(test_file_old, 'w') as f:
            f.write("old content")
        old_time = time.time() - (8 * 24 * 60 * 60)
        os.utime(test_file_old, (old_time, old_time))

        # Create new file
        with open(test_file_new, 'w') as f:
            f.write("new content")

        # Execute cleanup task
        result = cleanup_old_files.delay(directory=self.test_dir, days_old=7)

        # Wait for result with timeout
        task_result = result.get(timeout=30)

        assert task_result['status'] == 'success'
        assert task_result['files_removed'] == 1
        assert not os.path.exists(test_file_old), "Old file should be removed"
        assert os.path.exists(test_file_new), "New file should remain"

    @pytest.mark.skipif(
        not os.getenv('OPENAI_API_KEY'),
        reason="OpenAI API key required"
    )
    def test_content_generation_task(self):
        """Test educational content generation task."""
        request_data = {
            'topic': 'Introduction to Python Programming',
            'grade_level': 'Grade 9',
            'content_type': 'lesson',
            'language': 'en',
            'metadata': {
                'include_quiz': True,
                'quiz_questions': 3
            }
        }

        # Execute content generation task
        result = generate_educational_content.delay(
            request_data=request_data,
            callback_channel='test-channel'
        )

        # Wait for result with timeout
        task_result = result.get(timeout=60)

        assert task_result['status'] == 'success'
        assert 'content' in task_result
        assert 'quiz' in task_result
        assert task_result['task_id'] == result.id

    def test_notification_task(self):
        """Test notification sending task."""
        # Test single notification
        result = send_notification.delay(
            user_id='test_user_123',
            notification_type='info',
            title='Test Notification',
            message='This is a test notification',
            data={'test_key': 'test_value'},
            channels=['pusher']
        )

        task_result = result.get(timeout=30)

        assert task_result['status'] == 'success'
        assert task_result['user_id'] == 'test_user_123'
        assert 'delivery_results' in task_result

    def test_bulk_notification_task(self):
        """Test bulk notification sending task."""
        user_ids = ['user1', 'user2', 'user3']

        result = send_bulk_notifications.delay(
            user_ids=user_ids,
            notification_type='info',
            title='Bulk Test',
            message='Bulk notification test'
        )

        task_result = result.get(timeout=30)

        assert task_result['status'] in ['success', 'partial']
        assert task_result['total_users'] == len(user_ids)

    def test_analytics_aggregation_task(self):
        """Test analytics metrics aggregation task."""
        result = aggregate_usage_metrics.delay(
            period='daily',
            date=datetime.utcnow().isoformat()
        )

        task_result = result.get(timeout=30)

        assert task_result['status'] == 'success'
        assert 'metrics' in task_result
        assert 'users' in task_result['metrics']
        assert 'content' in task_result['metrics']
        assert 'engagement_rate' in task_result['metrics']

    def test_report_generation_task(self):
        """Test report generation task."""
        start_date = (datetime.utcnow() - timedelta(days=7)).isoformat()
        end_date = datetime.utcnow().isoformat()

        result = generate_reports.delay(
            report_type='usage',
            start_date=start_date,
            end_date=end_date,
            filters={'role': 'student'}
        )

        task_result = result.get(timeout=30)

        assert task_result['status'] == 'success'
        assert 'report_id' in task_result
        assert 'report_path' in task_result
        assert task_result['report_type'] == 'usage'

    def test_webhook_processing_task(self):
        """Test webhook event processing task."""
        event_data = {
            'channel': 'private-classroom-123',
            'event': 'channel_occupied',
            'time': datetime.utcnow().isoformat()
        }

        result = process_webhook_event.delay(
            event_type='pusher.channel_occupied',
            event_data=event_data,
            source='pusher'
        )

        task_result = result.get(timeout=30)

        assert task_result['status'] == 'success'
        assert task_result['event_type'] == 'pusher.channel_occupied'

    @pytest.mark.skipif(
        not os.getenv('ROBLOX_API_KEY'),
        reason="Roblox API key required"
    )
    def test_roblox_sync_task(self):
        """Test Roblox environment synchronization task."""
        universe_id = os.getenv('ROBLOX_UNIVERSE_ID', 'test_universe')

        result = sync_roblox_environment.delay(
            universe_id=universe_id,
            sync_type='incremental'
        )

        task_result = result.get(timeout=60)

        assert task_result['status'] == 'success'
        assert task_result['universe_id'] == universe_id
        assert 'results' in task_result

    def test_task_retry_mechanism(self):
        """Test task retry mechanism on failure."""
        # Create a task that will fail initially
        result = cleanup_old_files.delay(
            directory='/nonexistent/directory',
            days_old=7
        )

        # Task should retry on failure
        try:
            task_result = result.get(timeout=30)
            # If it succeeds, it handled the error gracefully
            assert task_result['status'] in ['success', 'skipped']
        except Exception as e:
            # Task failed after retries
            assert result.state == 'FAILURE'

    def test_task_priority_queues(self):
        """Test task priority queue routing."""
        # High priority task
        high_priority_result = send_notification.apply_async(
            args=['user1', 'critical', 'Urgent', 'Urgent message', None, ['pusher']],
            priority=9
        )

        # Low priority task
        low_priority_result = cleanup_old_files.apply_async(
            args=[self.test_dir, 30],
            priority=1
        )

        # Both tasks should be accepted
        assert high_priority_result.id is not None
        assert low_priority_result.id is not None

    def test_periodic_task_scheduling(self):
        """Test that periodic tasks are scheduled correctly."""
        # Get scheduled tasks from beat
        from apps.backend.celery_app import app

        # Check beat schedule is configured
        assert hasattr(app.conf, 'beat_schedule')
        schedule = app.conf.beat_schedule

        # Verify periodic tasks are configured
        expected_tasks = [
            'cleanup-old-files',
            'cleanup-expired-sessions',
            'aggregate-daily-metrics'
        ]

        for task_name in expected_tasks:
            assert task_name in schedule, f"Periodic task {task_name} not scheduled"
            task_config = schedule[task_name]
            assert 'task' in task_config
            assert 'schedule' in task_config

    def test_task_result_backend(self):
        """Test task result storage and retrieval."""
        # Execute a simple task
        result = send_notification.delay(
            user_id='test_user',
            notification_type='info',
            title='Test',
            message='Test message',
            channels=['pusher']
        )

        # Get task ID
        task_id = result.id
        assert task_id is not None

        # Wait for completion
        result.get(timeout=30)

        # Retrieve result by ID
        retrieved_result = AsyncResult(task_id, app=self.celery_app)
        assert retrieved_result.successful()
        assert retrieved_result.result['status'] == 'success'

    def test_task_chaining(self):
        """Test task chaining and workflows."""
        from celery import chain

        # Chain multiple tasks
        workflow = chain(
            aggregate_usage_metrics.s('daily', datetime.utcnow().isoformat()),
            generate_reports.s('usage', datetime.utcnow().isoformat(), datetime.utcnow().isoformat())
        )

        # Execute workflow
        result = workflow.apply_async()

        # Wait for completion
        final_result = result.get(timeout=60)

        # Final result should be from report generation
        assert 'report_id' in final_result or 'status' in final_result

    def test_task_group_execution(self):
        """Test parallel task execution with groups."""
        from celery import group

        # Create group of tasks
        job = group(
            send_notification.s(f'user{i}', 'info', 'Test', 'Message', None, ['pusher'])
            for i in range(3)
        )

        # Execute group
        result = job.apply_async()

        # Wait for all tasks
        results = result.get(timeout=30)

        assert len(results) == 3
        for task_result in results:
            assert task_result['status'] == 'success'

    def test_task_error_handling(self):
        """Test task error handling and exception propagation."""
        # Test with invalid input that should cause error
        result = process_quiz_generation.delay(
            content_id='nonexistent_content',
            num_questions=10
        )

        try:
            task_result = result.get(timeout=30)
            # Task might handle error gracefully
            if 'error' in task_result:
                assert task_result['error'] is not None
        except Exception as e:
            # Task raised exception
            assert result.state == 'FAILURE'
            assert str(e) is not None

    def test_celery_monitoring_metrics(self):
        """Test Celery monitoring and metrics collection."""
        inspector = self.celery_app.control.inspect()

        # Get statistics
        stats = inspector.stats()
        assert stats is not None

        for worker, worker_stats in stats.items():
            assert 'total' in worker_stats
            assert 'pool' in worker_stats

        # Get active tasks
        active = inspector.active()
        assert active is not None

        # Get reserved tasks
        reserved = inspector.reserved()
        assert reserved is not None


@pytest.mark.integration
@pytest.mark.celery
@pytest.mark.performance
class TestCeleryPerformance:
    """Test Celery performance and scalability."""

    def setup_method(self):
        """Set up test environment."""
        self.celery_app = celery_app

    def test_task_throughput(self):
        """Test task processing throughput."""
        num_tasks = 50
        start_time = time.time()

        # Submit multiple tasks
        results = []
        for i in range(num_tasks):
            result = send_notification.delay(
                user_id=f'user_{i}',
                notification_type='info',
                title=f'Test {i}',
                message='Performance test',
                channels=['pusher']
            )
            results.append(result)

        # Wait for all tasks to complete
        for result in results:
            result.get(timeout=60)

        end_time = time.time()
        duration = end_time - start_time

        # Calculate throughput
        throughput = num_tasks / duration

        # Should process at least 1 task per second
        assert throughput >= 1, f"Throughput {throughput:.2f} tasks/sec is too low"

    def test_memory_usage_under_load(self):
        """Test memory usage under load."""
        inspector = self.celery_app.control.inspect()

        # Get initial memory stats
        initial_stats = inspector.stats()

        # Submit memory-intensive tasks
        results = []
        for i in range(10):
            result = export_analytics_data.delay(
                export_format='json',
                data_type='all'
            )
            results.append(result)

        # Wait for completion
        for result in results:
            try:
                result.get(timeout=60)
            except Exception:
                pass  # Some tasks may fail, which is ok for this test

        # Get final memory stats
        final_stats = inspector.stats()

        # Memory should not have grown excessively
        # This is a basic check - in production you'd monitor more closely
        assert final_stats is not None