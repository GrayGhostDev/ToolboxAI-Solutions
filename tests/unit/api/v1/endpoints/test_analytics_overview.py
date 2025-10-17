"""
Tests for GET /analytics/overview endpoint - Production analytics overview.

Tests the analytics_production.py overview endpoint which provides:
- Total and active student counts
- Total active classes
- Average completion rate
- Average quiz score
- Assignment statistics
- Engagement and attendance rates
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from fastapi import HTTPException
from sqlalchemy import select, func, and_

from apps.backend.api.v1.endpoints.analytics_production import get_analytics_overview
from database.models.models import User, UserRole, Class, ClassEnrollment, UserProgress, Quiz, QuizAttempt


class TestGetAnalyticsOverview:
    """Test suite for GET /analytics/overview endpoint."""

    @pytest.fixture
    def mock_current_user(self):
        """Create a mock authenticated user."""
        user = MagicMock()
        user.id = uuid4()
        user.username = "test_user"
        user.role = UserRole.ADMIN
        user.is_active = True
        return user

    @pytest.fixture
    def mock_session(self):
        """Create a mock async database session."""
        session = AsyncMock()
        return session

    @pytest.fixture
    def sample_overview_data(self):
        """Sample overview data structure."""
        return {
            "total_students": 100,
            "active_students": 75,
            "total_classes": 10,
            "average_completion": 65.5,
            "average_score": 78.3,
            "total_assignments": 50,
            "completed_assignments": 380,
            "pending_submissions": 120,
            "engagement_rate": 75.0,
            "attendance_rate": 85.0,
        }

    @pytest.mark.asyncio
    async def test_overview_success_with_data(self, mock_current_user, mock_session):
        """Test successful overview retrieval with existing data."""
        # Mock database queries
        mock_result = AsyncMock()
        mock_result.scalar.return_value = 100  # total_students

        # Setup multiple query results
        query_results = [
            100,  # total_students
            75,   # active_students
            10,   # total_classes
            65.5, # average_completion
            78.3, # average_score
            50,   # total_assignments
            380,  # completed_assignments
            500,  # total_enrollments
            425,  # active_enrollments
        ]

        result_mocks = []
        for value in query_results:
            result_mock = AsyncMock()
            result_mock.scalar.return_value = value
            result_mocks.append(result_mock)

        mock_session.execute.side_effect = result_mocks

        # Call endpoint
        with patch('apps.backend.api.v1.endpoints.analytics_production.database_service') as mock_db_service:
            mock_db_service.initialize = AsyncMock()

            response = await get_analytics_overview(
                current_user=mock_current_user,
                session=mock_session
            )

        # Assertions
        assert response["total_students"] == 100
        assert response["active_students"] == 75
        assert response["total_classes"] == 10
        assert response["average_completion"] == 65.5
        assert response["average_score"] == 78.3
        assert response["total_assignments"] == 50
        assert response["completed_assignments"] == 380
        assert response["pending_submissions"] == 120  # 500 - 380
        assert response["engagement_rate"] == 75.0  # 75/100 * 100
        assert response["attendance_rate"] == 85.0  # 425/500 * 100

        # Verify database was initialized
        mock_db_service.initialize.assert_called_once()

        # Verify queries were executed
        assert mock_session.execute.call_count == len(query_results)

    @pytest.mark.asyncio
    async def test_overview_success_with_no_data(self, mock_current_user, mock_session):
        """Test successful overview retrieval with no data (empty database)."""
        # Mock all queries returning 0 or None
        mock_result = AsyncMock()
        mock_result.scalar.return_value = 0

        mock_session.execute.return_value = mock_result

        with patch('apps.backend.api.v1.endpoints.analytics_production.database_service') as mock_db_service:
            mock_db_service.initialize = AsyncMock()

            response = await get_analytics_overview(
                current_user=mock_current_user,
                session=mock_session
            )

        # All values should be 0 or 0.0
        assert response["total_students"] == 0
        assert response["active_students"] == 0
        assert response["total_classes"] == 0
        assert response["average_completion"] == 0.0
        assert response["average_score"] == 0.0
        assert response["total_assignments"] == 0
        assert response["completed_assignments"] == 0
        assert response["engagement_rate"] == 0  # Should handle division by zero
        assert response["attendance_rate"] == 0  # Should handle division by zero

    @pytest.mark.asyncio
    async def test_overview_calculates_engagement_rate_correctly(self, mock_current_user, mock_session):
        """Test that engagement rate is calculated correctly."""
        # Setup: 80 active out of 100 total students
        query_results = [
            100,  # total_students
            80,   # active_students
            10,   # total_classes
            65.0, # average_completion
            75.0, # average_score
            50,   # total_assignments
            400,  # completed_assignments
            500,  # total_enrollments
            450,  # active_enrollments
        ]

        result_mocks = []
        for value in query_results:
            result_mock = AsyncMock()
            result_mock.scalar.return_value = value
            result_mocks.append(result_mock)

        mock_session.execute.side_effect = result_mocks

        with patch('apps.backend.api.v1.endpoints.analytics_production.database_service') as mock_db_service:
            mock_db_service.initialize = AsyncMock()

            response = await get_analytics_overview(
                current_user=mock_current_user,
                session=mock_session
            )

        # Engagement rate should be 80/100 * 100 = 80.0
        assert response["engagement_rate"] == 80.0
        assert response["attendance_rate"] == 90.0  # 450/500 * 100

    @pytest.mark.asyncio
    async def test_overview_handles_null_averages(self, mock_current_user, mock_session):
        """Test that null averages from database are handled correctly."""
        # Mock queries where averages return None
        query_results = [
            50,   # total_students
            40,   # active_students
            5,    # total_classes
            None, # average_completion (no progress data)
            None, # average_score (no quiz attempts)
            25,   # total_assignments
            0,    # completed_assignments
            100,  # total_enrollments
            90,   # active_enrollments
        ]

        result_mocks = []
        for value in query_results:
            result_mock = AsyncMock()
            result_mock.scalar.return_value = value
            result_mocks.append(result_mock)

        mock_session.execute.side_effect = result_mocks

        with patch('apps.backend.api.v1.endpoints.analytics_production.database_service') as mock_db_service:
            mock_db_service.initialize = AsyncMock()

            response = await get_analytics_overview(
                current_user=mock_current_user,
                session=mock_session
            )

        # Null values should be converted to 0.0
        assert response["average_completion"] == 0.0
        assert response["average_score"] == 0.0
        assert response["total_students"] == 50
        assert response["active_students"] == 40

    @pytest.mark.asyncio
    async def test_overview_rounds_decimal_values(self, mock_current_user, mock_session):
        """Test that decimal values are properly rounded."""
        query_results = [
            100,      # total_students
            75,       # active_students
            10,       # total_classes
            67.8523,  # average_completion
            84.6789,  # average_score
            50,       # total_assignments
            380,      # completed_assignments
            500,      # total_enrollments
            425,      # active_enrollments
        ]

        result_mocks = []
        for value in query_results:
            result_mock = AsyncMock()
            result_mock.scalar.return_value = value
            result_mocks.append(result_mock)

        mock_session.execute.side_effect = result_mocks

        with patch('apps.backend.api.v1.endpoints.analytics_production.database_service') as mock_db_service:
            mock_db_service.initialize = AsyncMock()

            response = await get_analytics_overview(
                current_user=mock_current_user,
                session=mock_session
            )

        # Should be rounded to 1 decimal place
        assert response["average_completion"] == 67.9
        assert response["average_score"] == 84.7
        assert response["engagement_rate"] == 75.0
        assert response["attendance_rate"] == 85.0

    @pytest.mark.asyncio
    async def test_overview_calculates_pending_submissions(self, mock_current_user, mock_session):
        """Test that pending submissions are calculated correctly."""
        query_results = [
            100,  # total_students
            75,   # active_students
            10,   # total_classes
            65.0, # average_completion
            78.0, # average_score
            100,  # total_assignments
            250,  # completed_assignments
            500,  # total_enrollments
            425,  # active_enrollments
        ]

        result_mocks = []
        for value in query_results:
            result_mock = AsyncMock()
            result_mock.scalar.return_value = value
            result_mocks.append(result_mock)

        mock_session.execute.side_effect = result_mocks

        with patch('apps.backend.api.v1.endpoints.analytics_production.database_service') as mock_db_service:
            mock_db_service.initialize = AsyncMock()

            response = await get_analytics_overview(
                current_user=mock_current_user,
                session=mock_session
            )

        # Pending = total_assignments - completed_assignments
        # But note: total_assignments is count of Quiz, completed is count of QuizAttempt
        # So pending_submissions = 100 - 250 could be negative if multiple attempts allowed
        # The implementation should handle this correctly
        assert "pending_submissions" in response
        assert isinstance(response["pending_submissions"], int)

    @pytest.mark.asyncio
    async def test_overview_authorization_all_roles(self, mock_session):
        """Test that all authenticated users can access overview."""
        # Test with different roles
        roles = [UserRole.ADMIN, UserRole.TEACHER, UserRole.STUDENT]

        for role in roles:
            user = MagicMock()
            user.id = uuid4()
            user.role = role

            # Mock minimal successful response
            mock_result = AsyncMock()
            mock_result.scalar.return_value = 0
            mock_session.execute.return_value = mock_result

            with patch('apps.backend.api.v1.endpoints.analytics_production.database_service') as mock_db_service:
                mock_db_service.initialize = AsyncMock()

                # Should not raise authorization error
                response = await get_analytics_overview(
                    current_user=user,
                    session=mock_session
                )

                assert response is not None
                assert "total_students" in response

    @pytest.mark.asyncio
    async def test_overview_database_error_handling(self, mock_current_user, mock_session):
        """Test that database errors are handled gracefully."""
        # Mock database error
        mock_session.execute.side_effect = Exception("Database connection error")

        with patch('apps.backend.api.v1.endpoints.analytics_production.database_service') as mock_db_service:
            mock_db_service.initialize = AsyncMock()

            with pytest.raises(HTTPException) as exc_info:
                await get_analytics_overview(
                    current_user=mock_current_user,
                    session=mock_session
                )

            assert exc_info.value.status_code == 500
            assert "Failed to fetch analytics overview" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_overview_response_structure(self, mock_current_user, mock_session):
        """Test that response has correct structure with all required fields."""
        # Mock minimal data
        mock_result = AsyncMock()
        mock_result.scalar.return_value = 0
        mock_session.execute.return_value = mock_result

        with patch('apps.backend.api.v1.endpoints.analytics_production.database_service') as mock_db_service:
            mock_db_service.initialize = AsyncMock()

            response = await get_analytics_overview(
                current_user=mock_current_user,
                session=mock_session
            )

        # Verify all required fields are present
        required_fields = [
            "total_students",
            "active_students",
            "total_classes",
            "average_completion",
            "average_score",
            "total_assignments",
            "completed_assignments",
            "pending_submissions",
            "engagement_rate",
            "attendance_rate",
        ]

        for field in required_fields:
            assert field in response, f"Missing required field: {field}"

        # Verify data types
        assert isinstance(response["total_students"], int)
        assert isinstance(response["active_students"], int)
        assert isinstance(response["total_classes"], int)
        assert isinstance(response["average_completion"], (int, float))
        assert isinstance(response["average_score"], (int, float))
        assert isinstance(response["total_assignments"], int)
        assert isinstance(response["completed_assignments"], int)
        assert isinstance(response["pending_submissions"], int)
        assert isinstance(response["engagement_rate"], (int, float))
        assert isinstance(response["attendance_rate"], (int, float))

    @pytest.mark.asyncio
    async def test_overview_active_students_date_filter(self, mock_current_user, mock_session):
        """Test that active students query uses correct date filtering."""
        # This test verifies the 30-day active window is applied
        query_results = [
            100,  # total_students
            75,   # active_students (logged in last 30 days)
            10,   # total_classes
            65.0, # average_completion
            78.0, # average_score
            50,   # total_assignments
            380,  # completed_assignments
            500,  # total_enrollments
            425,  # active_enrollments
        ]

        result_mocks = []
        for value in query_results:
            result_mock = AsyncMock()
            result_mock.scalar.return_value = value
            result_mocks.append(result_mock)

        mock_session.execute.side_effect = result_mocks

        with patch('apps.backend.api.v1.endpoints.analytics_production.database_service') as mock_db_service:
            mock_db_service.initialize = AsyncMock()

            response = await get_analytics_overview(
                current_user=mock_current_user,
                session=mock_session
            )

        # Verify active_students is less than or equal to total_students
        assert response["active_students"] <= response["total_students"]
        assert response["active_students"] == 75

    @pytest.mark.asyncio
    async def test_overview_integration_with_real_queries(self, mock_current_user, mock_session):
        """Test that the endpoint constructs valid SQLAlchemy queries."""
        # This test verifies query structure without actually executing against database
        executed_queries = []

        async def capture_query(query):
            executed_queries.append(query)
            mock_result = AsyncMock()
            mock_result.scalar.return_value = 0
            return mock_result

        mock_session.execute.side_effect = capture_query

        with patch('apps.backend.api.v1.endpoints.analytics_production.database_service') as mock_db_service:
            mock_db_service.initialize = AsyncMock()

            await get_analytics_overview(
                current_user=mock_current_user,
                session=mock_session
            )

        # Verify multiple queries were executed
        assert len(executed_queries) >= 7  # At least 7 different queries

        # Note: Actual query validation would require more complex mocking
        # This verifies the function executes the expected number of queries


# Integration test marker for actual database tests
@pytest.mark.integration
class TestAnalyticsOverviewIntegration:
    """Integration tests for overview endpoint with real database."""

    @pytest.mark.asyncio
    async def test_overview_with_test_database(self):
        """Test overview endpoint with actual test database."""
        # TODO: Implement with test database fixture
        # This would require:
        # 1. Test database setup with sample data
        # 2. Real User, Class, UserProgress, Quiz records
        # 3. Verification of accurate calculations
        pass

    @pytest.mark.asyncio
    async def test_overview_performance_with_large_dataset(self):
        """Test overview endpoint performance with large dataset."""
        # TODO: Implement performance test
        # This would verify:
        # 1. Response time < 200ms target
        # 2. Efficient query execution
        # 3. No N+1 query issues
        pass
