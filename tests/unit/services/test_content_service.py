"""
Unit tests for Content Service

Tests educational content generation, retrieval, management, and streaming operations.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timezone
import asyncio
import uuid

from apps.backend.services.content_service import ContentService, get_content_service


@pytest.fixture
def content_service():
    """ContentService instance"""
    return ContentService()


@pytest.fixture
def sample_generation_result():
    """Sample content generation result"""
    return {
        "title": "Introduction to Mathematics",
        "description": "A comprehensive lesson on basic math concepts",
        "content": "Detailed educational content here...",
        "exercises": [
            {"question": "What is 2+2?", "answer": "4"}
        ]
    }


@pytest.mark.unit
class TestContentGeneration:
    """Test educational content generation"""

    @pytest.mark.asyncio
    async def test_generate_content_success(self, content_service, sample_generation_result):
        """Test successful content generation"""
        with patch('apps.backend.services.content_service.generate_educational_content', new_callable=AsyncMock) as mock_generate:
            mock_generate.return_value = sample_generation_result

            result = await content_service.generate_content(
                topic="Mathematics Basics",
                user_id="user_123",
                subject="Math",
                grade_level="5th Grade",
                content_type="lesson"
            )

        assert result["topic"] == "Mathematics Basics"
        assert result["subject"] == "Math"
        assert result["grade_level"] == "5th Grade"
        assert result["content_type"] == "lesson"
        assert result["status"] == "completed"
        assert "id" in result
        assert "generation_time" in result
        mock_generate.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_generate_content_with_additional_requirements(self, content_service, sample_generation_result):
        """Test content generation with additional requirements"""
        with patch('apps.backend.services.content_service.generate_educational_content', new_callable=AsyncMock) as mock_generate:
            mock_generate.return_value = sample_generation_result

            additional_reqs = {
                "difficulty": "advanced",
                "interactive": True,
                "include_visuals": True
            }

            result = await content_service.generate_content(
                topic="Advanced Algebra",
                user_id="user_456",
                additional_requirements=additional_reqs
            )

        assert result["status"] == "completed"
        call_args = mock_generate.call_args
        assert call_args[1]["requirements"] == additional_reqs

    @pytest.mark.asyncio
    async def test_generate_content_timeout(self, content_service):
        """Test content generation timeout"""
        with patch('apps.backend.services.content_service.generate_educational_content', new_callable=AsyncMock) as mock_generate:
            # Simulate timeout
            async def slow_generation(**kwargs):
                await asyncio.sleep(10)
                return {}

            mock_generate.side_effect = slow_generation
            content_service.generation_timeout = 0.1  # 100ms timeout

            with pytest.raises(Exception) as exc_info:
                await content_service.generate_content(
                    topic="Test Topic",
                    user_id="user_123"
                )

            assert "timed out" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_generate_content_agent_failure(self, content_service):
        """Test content generation with agent failure"""
        with patch('apps.backend.services.content_service.generate_educational_content', new_callable=AsyncMock) as mock_generate:
            mock_generate.side_effect = Exception("Agent generation failed")

            with pytest.raises(Exception) as exc_info:
                await content_service.generate_content(
                    topic="Test Topic",
                    user_id="user_123"
                )

            assert "Agent generation failed" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_generate_content_stores_content(self, content_service, sample_generation_result):
        """Test that generated content is stored"""
        with patch('apps.backend.services.content_service.generate_educational_content', new_callable=AsyncMock) as mock_generate:
            with patch.object(content_service, '_store_content', new_callable=AsyncMock) as mock_store:
                mock_generate.return_value = sample_generation_result

                result = await content_service.generate_content(
                    topic="Test Topic",
                    user_id="user_123"
                )

                mock_store.assert_awaited_once()
                call_args = mock_store.call_args[0][0]
                assert call_args["id"] == result["id"]

    @pytest.mark.asyncio
    async def test_generate_content_updates_user_activity(self, content_service, sample_generation_result):
        """Test that user activity is updated after generation"""
        with patch('apps.backend.services.content_service.generate_educational_content', new_callable=AsyncMock) as mock_generate:
            with patch.object(content_service, '_update_user_activity', new_callable=AsyncMock) as mock_activity:
                mock_generate.return_value = sample_generation_result

                result = await content_service.generate_content(
                    topic="Test Topic",
                    user_id="user_123",
                    content_type="quiz"
                )

                mock_activity.assert_awaited_once()
                call_args = mock_activity.call_args
                assert call_args[0][0] == "user_123"
                assert call_args[0][1] == "content_generated"


@pytest.mark.unit
class TestContentRetrieval:
    """Test content retrieval operations"""

    @pytest.mark.asyncio
    async def test_get_content_success(self, content_service):
        """Test successful content retrieval"""
        with patch.object(content_service, '_check_content_access', new_callable=AsyncMock, return_value=True):
            with patch.object(content_service, '_log_content_access', new_callable=AsyncMock):
                content = await content_service.get_content("content_123", "user_123")

        assert content is not None
        assert content["id"] == "content_123"
        assert "topic" in content
        assert "content" in content

    @pytest.mark.asyncio
    async def test_get_content_access_denied(self, content_service):
        """Test content retrieval with access denied"""
        with patch.object(content_service, '_check_content_access', new_callable=AsyncMock, return_value=False):
            content = await content_service.get_content("content_123", "user_456")

        assert content is None

    @pytest.mark.asyncio
    async def test_get_content_logs_access(self, content_service):
        """Test that content access is logged"""
        with patch.object(content_service, '_check_content_access', new_callable=AsyncMock, return_value=True):
            with patch.object(content_service, '_log_content_access', new_callable=AsyncMock) as mock_log:
                await content_service.get_content("content_789", "user_123")

                mock_log.assert_awaited_once_with("content_789", "user_123")

    @pytest.mark.asyncio
    async def test_get_content_exception_handling(self, content_service):
        """Test content retrieval exception handling"""
        with patch.object(content_service, '_check_content_access', new_callable=AsyncMock, side_effect=Exception("Database error")):
            content = await content_service.get_content("content_123", "user_123")

        assert content is None


@pytest.mark.unit
class TestContentListing:
    """Test content listing operations"""

    @pytest.mark.asyncio
    async def test_list_user_content_success(self, content_service):
        """Test successful user content listing"""
        result = await content_service.list_user_content(
            user_id="user_123",
            limit=10,
            offset=0
        )

        assert "items" in result
        assert "total" in result
        assert "limit" in result
        assert "offset" in result
        assert result["limit"] == 10
        assert result["offset"] == 0
        assert isinstance(result["items"], list)

    @pytest.mark.asyncio
    async def test_list_user_content_with_filters(self, content_service):
        """Test content listing with filters"""
        result = await content_service.list_user_content(
            user_id="user_123",
            limit=20,
            offset=5,
            content_type="quiz",
            subject="Science"
        )

        assert result["filters"]["content_type"] == "quiz"
        assert result["filters"]["subject"] == "Science"
        assert result["limit"] == 20
        assert result["offset"] == 5

    @pytest.mark.asyncio
    async def test_list_user_content_pagination(self, content_service):
        """Test content listing pagination"""
        # First page
        page1 = await content_service.list_user_content(
            user_id="user_123",
            limit=5,
            offset=0
        )

        # Second page
        page2 = await content_service.list_user_content(
            user_id="user_123",
            limit=5,
            offset=5
        )

        assert page1["offset"] == 0
        assert page2["offset"] == 5
        assert len(page1["items"]) == 5
        assert len(page2["items"]) == 5

    @pytest.mark.asyncio
    async def test_list_user_content_exception_handling(self, content_service):
        """Test content listing exception handling"""
        with patch('apps.backend.services.content_service.logger') as mock_logger:
            mock_logger.error = Mock(side_effect=Exception("Logging error"))

            # Should return empty result on error
            result = await content_service.list_user_content("user_123")

            # Should not raise, returns safe defaults
            assert result["items"] == []
            assert result["total"] == 0


@pytest.mark.unit
class TestContentUpdate:
    """Test content update operations"""

    @pytest.mark.asyncio
    async def test_update_content_success(self, content_service):
        """Test successful content update"""
        mock_content = {
            "id": "content_123",
            "topic": "Original Topic",
            "user_id": "user_123"
        }

        with patch.object(content_service, 'get_content', new_callable=AsyncMock, return_value=mock_content):
            with patch.object(content_service, '_check_content_modify_access', new_callable=AsyncMock, return_value=True):
                with patch.object(content_service, '_store_content', new_callable=AsyncMock):
                    updates = {"topic": "Updated Topic", "description": "New description"}

                    result = await content_service.update_content("content_123", "user_123", updates)

        assert result is not None
        assert result["topic"] == "Updated Topic"
        assert result["description"] == "New description"
        assert "updated_at" in result

    @pytest.mark.asyncio
    async def test_update_content_not_found(self, content_service):
        """Test update when content not found"""
        with patch.object(content_service, 'get_content', new_callable=AsyncMock, return_value=None):
            result = await content_service.update_content("content_999", "user_123", {})

        assert result is None

    @pytest.mark.asyncio
    async def test_update_content_access_denied(self, content_service):
        """Test update with insufficient permissions"""
        mock_content = {"id": "content_123", "user_id": "user_789"}

        with patch.object(content_service, 'get_content', new_callable=AsyncMock, return_value=mock_content):
            with patch.object(content_service, '_check_content_modify_access', new_callable=AsyncMock, return_value=False):
                result = await content_service.update_content("content_123", "user_123", {"topic": "Hacked"})

        assert result is None

    @pytest.mark.asyncio
    async def test_update_content_exception_handling(self, content_service):
        """Test update exception handling"""
        with patch.object(content_service, 'get_content', new_callable=AsyncMock, side_effect=Exception("Database error")):
            result = await content_service.update_content("content_123", "user_123", {})

        assert result is None


@pytest.mark.unit
class TestContentDeletion:
    """Test content deletion operations"""

    @pytest.mark.asyncio
    async def test_delete_content_success(self, content_service):
        """Test successful content deletion"""
        mock_content = {"id": "content_123", "user_id": "user_123"}

        with patch.object(content_service, 'get_content', new_callable=AsyncMock, return_value=mock_content):
            with patch.object(content_service, '_check_content_delete_access', new_callable=AsyncMock, return_value=True):
                with patch.object(content_service, '_delete_content_from_storage', new_callable=AsyncMock):
                    result = await content_service.delete_content("content_123", "user_123")

        assert result is True

    @pytest.mark.asyncio
    async def test_delete_content_not_found(self, content_service):
        """Test deletion when content not found"""
        with patch.object(content_service, 'get_content', new_callable=AsyncMock, return_value=None):
            result = await content_service.delete_content("content_999", "user_123")

        assert result is False

    @pytest.mark.asyncio
    async def test_delete_content_access_denied(self, content_service):
        """Test deletion with insufficient permissions"""
        mock_content = {"id": "content_123", "user_id": "user_789"}

        with patch.object(content_service, 'get_content', new_callable=AsyncMock, return_value=mock_content):
            with patch.object(content_service, '_check_content_delete_access', new_callable=AsyncMock, return_value=False):
                result = await content_service.delete_content("content_123", "user_123")

        assert result is False

    @pytest.mark.asyncio
    async def test_delete_content_exception_handling(self, content_service):
        """Test deletion exception handling"""
        with patch.object(content_service, 'get_content', new_callable=AsyncMock, side_effect=Exception("Database error")):
            result = await content_service.delete_content("content_123", "user_123")

        assert result is False


@pytest.mark.unit
class TestContentStreaming:
    """Test content streaming generation"""

    @pytest.mark.asyncio
    async def test_generate_content_stream_success(self, content_service):
        """Test successful streaming content generation"""
        stages_received = []

        async for stage in content_service.generate_content_stream(
            topic="Streaming Test",
            user_id="user_123"
        ):
            stages_received.append(stage)

        assert len(stages_received) == 6  # initializing, analyzing, structuring, generating, finalizing, completed
        assert stages_received[0]["stage"] == "initializing"
        assert stages_received[-1]["stage"] == "completed"
        assert stages_received[-1]["progress"] == 100

    @pytest.mark.asyncio
    async def test_generate_content_stream_with_parameters(self, content_service):
        """Test streaming with additional parameters"""
        stages = []

        async for stage in content_service.generate_content_stream(
            topic="Advanced Topic",
            user_id="user_456",
            subject="Science",
            grade_level="8th Grade"
        ):
            stages.append(stage)

        # Verify all stages have required fields
        for stage in stages:
            assert "content_id" in stage
            assert "topic" in stage
            assert "user_id" in stage
            assert "timestamp" in stage
            assert "stage" in stage
            assert "progress" in stage

    @pytest.mark.asyncio
    async def test_generate_content_stream_progress_increments(self, content_service):
        """Test that progress increments correctly during streaming"""
        progress_values = []

        async for stage in content_service.generate_content_stream(
            topic="Test",
            user_id="user_123"
        ):
            progress_values.append(stage["progress"])

        # Verify progress increases monotonically
        assert progress_values == sorted(progress_values)
        assert progress_values[0] == 10
        assert progress_values[-1] == 100


@pytest.mark.unit
class TestAccessControl:
    """Test content access control methods"""

    @pytest.mark.asyncio
    async def test_check_content_access_owner(self, content_service):
        """Test access check for content owner"""
        content_data = {"user_id": "user_123"}

        with patch.object(content_service, '_is_admin', new_callable=AsyncMock, return_value=False):
            has_access = await content_service._check_content_access("user_123", content_data)

        assert has_access is True

    @pytest.mark.asyncio
    async def test_check_content_access_admin(self, content_service):
        """Test access check for admin user"""
        content_data = {"user_id": "user_456"}

        with patch.object(content_service, '_is_admin', new_callable=AsyncMock, return_value=True):
            has_access = await content_service._check_content_access("admin_user", content_data)

        assert has_access is True

    @pytest.mark.asyncio
    async def test_check_content_access_denied(self, content_service):
        """Test access check denied for unauthorized user"""
        content_data = {"user_id": "user_456"}

        with patch.object(content_service, '_is_admin', new_callable=AsyncMock, return_value=False):
            has_access = await content_service._check_content_access("user_123", content_data)

        assert has_access is False

    @pytest.mark.asyncio
    async def test_check_content_modify_access(self, content_service):
        """Test modify access check"""
        content_data = {"user_id": "user_123"}

        with patch.object(content_service, '_is_admin', new_callable=AsyncMock, return_value=False):
            has_access = await content_service._check_content_modify_access("user_123", content_data)

        assert has_access is True

    @pytest.mark.asyncio
    async def test_check_content_delete_access(self, content_service):
        """Test delete access check"""
        content_data = {"user_id": "user_123"}

        with patch.object(content_service, '_is_admin', new_callable=AsyncMock, return_value=False):
            has_access = await content_service._check_content_delete_access("user_123", content_data)

        assert has_access is True


@pytest.mark.unit
class TestGlobalServiceInstance:
    """Test global service instance"""

    def test_get_content_service_returns_instance(self):
        """Test global service instance retrieval"""
        service = get_content_service()

        assert service is not None
        assert isinstance(service, ContentService)

    def test_get_content_service_singleton(self):
        """Test service instance is singleton"""
        service1 = get_content_service()
        service2 = get_content_service()

        assert service1 is service2


@pytest.mark.unit
class TestServiceConfiguration:
    """Test service configuration"""

    def test_default_generation_timeout(self):
        """Test default generation timeout is 5 minutes"""
        service = ContentService()

        assert service.generation_timeout == 300  # 5 minutes

    def test_custom_generation_timeout_from_settings(self):
        """Test custom timeout from settings"""
        with patch('apps.backend.services.content_service.settings') as mock_settings:
            mock_settings.CONTENT_GENERATION_TIMEOUT = 600  # 10 minutes
            service = ContentService()

            assert service.generation_timeout == 600
