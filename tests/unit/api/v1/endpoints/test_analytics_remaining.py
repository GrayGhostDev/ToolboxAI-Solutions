"""
Tests for remaining analytics endpoints - Consolidated test suite.

Covers:
- GET /analytics/weekly_xp - Weekly XP progression
- GET /analytics/subject_mastery - Subject mastery levels
- GET /analytics/realtime - Real-time analytics
- GET /analytics/trends/engagement - Engagement trends
- GET /analytics/trends/content - Content trends
- GET /analytics/dashboard - Dashboard analytics
- GET /analytics/summary - Summary analytics
- GET /users/ - List users
- GET /users/{user_id} - User details
"""

import pytest
from datetime import datetime, timedelta, date
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4, UUID

from fastapi import HTTPException

from apps.backend.api.v1.endpoints.analytics_production import (
    get_weekly_xp,
    get_subject_mastery,
    get_realtime_analytics,
    get_engagement_trends,
    get_content_trends,
    get_dashboard_analytics,
    get_analytics_summary,
    list_users,
    get_user,
)
from database.models.models import User, UserRole


class TestWeeklyXP:
    """Tests for GET /analytics/weekly_xp endpoint."""

    @pytest.fixture
    def mock_student_user(self):
        user = MagicMock()
        user.id = uuid4()
        user.role = UserRole.STUDENT
        return user

    @pytest.mark.asyncio
    async def test_weekly_xp_success(self, mock_student_user):
        """Test successful weekly XP retrieval."""
        mock_session = AsyncMock()

        # Mock daily XP query result
        mock_row = MagicMock()
        mock_row.date = date.today()
        mock_row.xp = 250

        mock_result = AsyncMock()
        mock_result.__iter__.return_value = [mock_row]
        mock_session.execute.return_value = mock_result

        with patch('apps.backend.api.v1.endpoints.analytics_production.database_service') as mock_db_service:
            mock_db_service.initialize = AsyncMock()

            response = await get_weekly_xp(
                current_user=mock_student_user,
                session=mock_session
            )

        assert "week_total" in response
        assert "daily_average" in response
        assert "streak" in response
        assert "data" in response
        assert len(response["data"]) == 7  # 7 days

    @pytest.mark.asyncio
    async def test_weekly_xp_empty_data(self, mock_student_user):
        """Test weekly XP with no activity."""
        mock_session = AsyncMock()
        mock_result = AsyncMock()
        mock_result.__iter__.return_value = []
        mock_session.execute.return_value = mock_result

        with patch('apps.backend.api.v1.endpoints.analytics_production.database_service') as mock_db_service:
            mock_db_service.initialize = AsyncMock()

            response = await get_weekly_xp(
                current_user=mock_student_user,
                session=mock_session
            )

        assert response["week_total"] == 0
        assert response["daily_average"] == 0
        assert response["streak"] == 0


class TestSubjectMastery:
    """Tests for GET /analytics/subject_mastery endpoint."""

    @pytest.fixture
    def mock_student_user(self):
        user = MagicMock()
        user.id = uuid4()
        user.role = UserRole.STUDENT
        return user

    @pytest.mark.asyncio
    async def test_subject_mastery_success(self, mock_student_user):
        """Test successful subject mastery retrieval."""
        mock_session = AsyncMock()

        # Mock subject query result
        mock_row = MagicMock()
        mock_row.subject = "Mathematics"
        mock_row.mastery = 75.5
        mock_row.topics_completed = 12

        mock_result = AsyncMock()
        mock_result.__iter__.return_value = [mock_row]
        mock_session.execute.return_value = mock_result

        with patch('apps.backend.api.v1.endpoints.analytics_production.database_service') as mock_db_service:
            mock_db_service.initialize = AsyncMock()

            response = await get_subject_mastery(
                current_user=mock_student_user,
                session=mock_session
            )

        assert isinstance(response, list)
        assert len(response) == 1
        assert response[0]["subject"] == "Mathematics"
        assert response[0]["mastery"] == 76  # Rounded
        assert response[0]["topics_completed"] == 12

    @pytest.mark.asyncio
    async def test_subject_mastery_sorted_by_mastery(self, mock_student_user):
        """Test that subjects are sorted by mastery level."""
        mock_session = AsyncMock()

        subjects = [
            MagicMock(subject="Math", mastery=85.0, topics_completed=10),
            MagicMock(subject="Science", mastery=92.0, topics_completed=12),
            MagicMock(subject="History", mastery=70.0, topics_completed=8),
        ]

        mock_result = AsyncMock()
        mock_result.__iter__.return_value = subjects
        mock_session.execute.return_value = mock_result

        with patch('apps.backend.api.v1.endpoints.analytics_production.database_service') as mock_db_service:
            mock_db_service.initialize = AsyncMock()

            response = await get_subject_mastery(
                current_user=mock_student_user,
                session=mock_session
            )

        # Should be sorted descending by mastery
        assert response[0]["subject"] == "Science"  # 92
        assert response[1]["subject"] == "Math"     # 85
        assert response[2]["subject"] == "History"  # 70


class TestRealtimeAnalytics:
    """Tests for GET /analytics/realtime endpoint."""

    @pytest.fixture
    def mock_user(self):
        user = MagicMock()
        user.id = uuid4()
        user.role = UserRole.ADMIN
        return user

    @pytest.mark.asyncio
    async def test_realtime_analytics_success(self, mock_user):
        """Test successful realtime analytics retrieval."""
        mock_session = AsyncMock()

        # Mock active users count
        active_result = AsyncMock()
        active_result.scalar.return_value = 15

        # Mock recent activities
        mock_activity = MagicMock()
        mock_activity.user_id = uuid4()
        mock_activity.created_at = datetime.now()

        recent_result = AsyncMock()
        recent_result.scalars.return_value.all.return_value = [mock_activity]

        # Mock today's activities count
        today_result = AsyncMock()
        today_result.scalar.return_value = 250

        mock_session.execute.side_effect = [active_result, recent_result, today_result]

        with patch('apps.backend.api.v1.endpoints.analytics_production.database_service') as mock_db_service:
            mock_db_service.initialize = AsyncMock()

            response = await get_realtime_analytics(
                current_user=mock_user,
                session=mock_session
            )

        assert response["active_users"] == 15
        assert response["active_sessions"] == 15
        assert len(response["recent_activities"]) == 1
        assert response["usage_stats"]["activities_today"] == 250


class TestEngagementTrends:
    """Tests for GET /analytics/trends/engagement endpoint."""

    @pytest.fixture
    def mock_admin_user(self):
        user = MagicMock()
        user.id = uuid4()
        user.role = UserRole.ADMIN
        return user

    @pytest.mark.asyncio
    async def test_engagement_trends_admin_only(self):
        """Test that only admins can access engagement trends."""
        mock_session = AsyncMock()
        student = MagicMock()
        student.id = uuid4()
        student.role = UserRole.STUDENT

        with patch('apps.backend.api.v1.endpoints.analytics_production.database_service') as mock_db_service:
            mock_db_service.initialize = AsyncMock()

            with pytest.raises(HTTPException) as exc_info:
                await get_engagement_trends(
                    days=30,
                    current_user=student,
                    session=mock_session
                )

            assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_engagement_trends_success(self, mock_admin_user):
        """Test successful engagement trends retrieval."""
        mock_session = AsyncMock()

        # Mock daily users query
        daily_users_result = AsyncMock()
        daily_users_result.__iter__.return_value = []

        # Mock daily activities query
        daily_activities_result = AsyncMock()
        daily_activities_result.__iter__.return_value = []

        mock_session.execute.side_effect = [daily_users_result, daily_activities_result]

        with patch('apps.backend.api.v1.endpoints.analytics_production.database_service') as mock_db_service:
            mock_db_service.initialize = AsyncMock()

            response = await get_engagement_trends(
                days=30,
                current_user=mock_admin_user,
                session=mock_session
            )

        assert "period" in response
        assert "summary" in response
        assert "trends" in response
        assert len(response["trends"]) == 30


class TestContentTrends:
    """Tests for GET /analytics/trends/content endpoint."""

    @pytest.fixture
    def mock_teacher_user(self):
        user = MagicMock()
        user.id = uuid4()
        user.role = UserRole.TEACHER
        return user

    @pytest.mark.asyncio
    async def test_content_trends_admin_or_teacher(self, mock_teacher_user):
        """Test that admin or teacher can access content trends."""
        mock_session = AsyncMock()

        # Mock all three queries
        mock_session.execute.return_value = AsyncMock(__iter__=lambda self: iter([]))

        with patch('apps.backend.api.v1.endpoints.analytics_production.database_service') as mock_db_service:
            mock_db_service.initialize = AsyncMock()

            response = await get_content_trends(
                days=30,
                current_user=mock_teacher_user,
                session=mock_session
            )

        assert "period" in response
        assert "most_viewed" in response
        assert "completion_rates" in response
        assert "daily_consumption" in response

    @pytest.mark.asyncio
    async def test_content_trends_student_denied(self):
        """Test that students cannot access content trends."""
        mock_session = AsyncMock()
        student = MagicMock()
        student.id = uuid4()
        student.role = UserRole.STUDENT

        with patch('apps.backend.api.v1.endpoints.analytics_production.database_service') as mock_db_service:
            mock_db_service.initialize = AsyncMock()

            with pytest.raises(HTTPException) as exc_info:
                await get_content_trends(
                    days=30,
                    current_user=student,
                    session=mock_session
                )

            assert exc_info.value.status_code == 403


class TestDashboardAnalytics:
    """Tests for GET /analytics/dashboard endpoint."""

    @pytest.fixture
    def mock_admin_user(self):
        user = MagicMock()
        user.id = uuid4()
        user.role = UserRole.ADMIN
        return user

    @pytest.mark.asyncio
    async def test_dashboard_analytics_success(self, mock_admin_user):
        """Test successful dashboard analytics retrieval."""
        mock_session = AsyncMock()

        # Mock all scalar queries
        mock_result = AsyncMock()
        mock_result.scalar.return_value = 100
        mock_result.__iter__.return_value = []

        mock_session.execute.return_value = mock_result

        with patch('apps.backend.api.v1.endpoints.analytics_production.database_service') as mock_db_service:
            mock_db_service.initialize = AsyncMock()

            response = await get_dashboard_analytics(
                time_range="week",
                current_user=mock_admin_user,
                session=mock_session
            )

        assert response["time_range"] == "week"
        assert "period" in response
        assert "metrics" in response
        assert "top_performers" in response
        assert "recent_completions" in response

    @pytest.mark.asyncio
    async def test_dashboard_all_time_ranges(self, mock_admin_user):
        """Test dashboard with all time range options."""
        time_ranges = ["day", "week", "month", "year"]

        for time_range in time_ranges:
            mock_session = AsyncMock()
            mock_result = AsyncMock()
            mock_result.scalar.return_value = 0
            mock_result.__iter__.return_value = []
            mock_session.execute.return_value = mock_result

            with patch('apps.backend.api.v1.endpoints.analytics_production.database_service') as mock_db_service:
                mock_db_service.initialize = AsyncMock()

                response = await get_dashboard_analytics(
                    time_range=time_range,
                    current_user=mock_admin_user,
                    session=mock_session
                )

            assert response["time_range"] == time_range


class TestAnalyticsSummary:
    """Tests for GET /analytics/summary endpoint."""

    @pytest.fixture
    def mock_admin_user(self):
        user = MagicMock()
        user.id = uuid4()
        user.role = UserRole.ADMIN
        return user

    @pytest.mark.asyncio
    async def test_summary_with_date_filters(self, mock_admin_user):
        """Test summary with custom date filters."""
        mock_session = AsyncMock()

        # Mock all queries
        mock_result = AsyncMock()
        mock_result.scalar.return_value = 50
        mock_result.first.return_value = MagicMock(total=10, avg_score=85.0)
        mock_session.execute.return_value = mock_result

        with patch('apps.backend.api.v1.endpoints.analytics_production.database_service') as mock_db_service:
            mock_db_service.initialize = AsyncMock()

            response = await get_analytics_summary(
                start_date="2025-01-01",
                end_date="2025-01-31",
                class_id=None,
                current_user=mock_admin_user,
                session=mock_session
            )

        assert "period" in response
        assert "filters" in response
        assert "summary" in response

    @pytest.mark.asyncio
    async def test_summary_with_class_filter(self, mock_admin_user):
        """Test summary with class filter."""
        mock_session = AsyncMock()
        class_id = str(uuid4())

        # Mock enrollment query
        enrollment_result = AsyncMock()
        enrollment_result.__iter__.return_value = [(uuid4(),), (uuid4(),)]

        # Mock other queries
        mock_result = AsyncMock()
        mock_result.scalar.return_value = 25
        mock_result.first.return_value = MagicMock(total=5, avg_score=80.0)

        mock_session.execute.side_effect = [enrollment_result, mock_result, mock_result, mock_result, mock_result, mock_result, mock_result]

        with patch('apps.backend.api.v1.endpoints.analytics_production.database_service') as mock_db_service:
            mock_db_service.initialize = AsyncMock()

            response = await get_analytics_summary(
                start_date=None,
                end_date=None,
                class_id=class_id,
                current_user=mock_admin_user,
                session=mock_session
            )

        assert response["filters"]["class_id"] == class_id


class TestListUsers:
    """Tests for GET /users/ endpoint."""

    @pytest.fixture
    def mock_admin_user(self):
        user = MagicMock()
        user.id = uuid4()
        user.role = UserRole.ADMIN
        return user

    @pytest.mark.asyncio
    async def test_list_users_admin_only(self):
        """Test that only admins can list users."""
        mock_session = AsyncMock()
        student = MagicMock()
        student.id = uuid4()
        student.role = UserRole.STUDENT

        with patch('apps.backend.api.v1.endpoints.analytics_production.database_service') as mock_db_service:
            mock_db_service.initialize = AsyncMock()

            with pytest.raises(HTTPException) as exc_info:
                await list_users(
                    search="",
                    role=None,
                    limit=20,
                    offset=0,
                    current_user=student,
                    session=mock_session
                )

            assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_list_users_success(self, mock_admin_user):
        """Test successful user listing."""
        mock_session = AsyncMock()

        mock_user = MagicMock()
        mock_user.id = uuid4()
        mock_user.username = "testuser"
        mock_user.email = "test@example.com"
        mock_user.first_name = "Test"
        mock_user.last_name = "User"
        mock_user.role = UserRole.STUDENT
        mock_user.is_active = True
        mock_user.created_at = datetime.now()
        mock_user.last_login = datetime.now()

        mock_result = AsyncMock()
        mock_result.scalars.return_value.all.return_value = [mock_user]
        mock_session.execute.return_value = mock_result

        with patch('apps.backend.api.v1.endpoints.analytics_production.database_service') as mock_db_service:
            mock_db_service.initialize = AsyncMock()

            response = await list_users(
                search="",
                role=None,
                limit=20,
                offset=0,
                current_user=mock_admin_user,
                session=mock_session
            )

        assert len(response) == 1
        assert response[0]["username"] == "testuser"
        assert response[0]["email"] == "test@example.com"


class TestGetUser:
    """Tests for GET /users/{user_id} endpoint."""

    @pytest.fixture
    def mock_admin_user(self):
        user = MagicMock()
        user.id = uuid4()
        user.role = UserRole.ADMIN
        return user

    @pytest.mark.asyncio
    async def test_get_user_admin_access(self, mock_admin_user):
        """Test that admin can view any user."""
        mock_session = AsyncMock()
        target_user_id = str(uuid4())

        mock_user = MagicMock()
        mock_user.id = UUID(target_user_id)
        mock_user.username = "targetuser"
        mock_user.email = "target@example.com"
        mock_user.first_name = "Target"
        mock_user.last_name = "User"
        mock_user.role = UserRole.STUDENT
        mock_user.is_active = True
        mock_user.created_at = datetime.now()
        mock_user.last_login = datetime.now()

        user_result = AsyncMock()
        user_result.scalar_one_or_none.return_value = mock_user

        # Mock additional queries
        mock_result = AsyncMock()
        mock_result.scalar.return_value = 5

        mock_session.execute.side_effect = [user_result, mock_result, mock_result]

        with patch('apps.backend.api.v1.endpoints.analytics_production.database_service') as mock_db_service:
            mock_db_service.initialize = AsyncMock()

            response = await get_user(
                user_id=target_user_id,
                current_user=mock_admin_user,
                session=mock_session
            )

        assert response["username"] == "targetuser"
        assert "profile" in response

    @pytest.mark.asyncio
    async def test_get_user_self_access(self):
        """Test that users can view their own profile."""
        mock_session = AsyncMock()
        user_id = uuid4()

        user = MagicMock()
        user.id = user_id
        user.role = UserRole.STUDENT

        mock_user = MagicMock()
        mock_user.id = user_id
        mock_user.username = "selfuser"
        mock_user.email = "self@example.com"
        mock_user.first_name = "Self"
        mock_user.last_name = "User"
        mock_user.role = UserRole.STUDENT
        mock_user.is_active = True
        mock_user.created_at = datetime.now()
        mock_user.last_login = datetime.now()

        user_result = AsyncMock()
        user_result.scalar_one_or_none.return_value = mock_user

        mock_result = AsyncMock()
        mock_result.scalar.return_value = 3

        mock_session.execute.side_effect = [user_result, mock_result, mock_result]

        with patch('apps.backend.api.v1.endpoints.analytics_production.database_service') as mock_db_service:
            mock_db_service.initialize = AsyncMock()

            response = await get_user(
                user_id=str(user_id),
                current_user=user,
                session=mock_session
            )

        assert response["username"] == "selfuser"

    @pytest.mark.asyncio
    async def test_get_user_authorization_denied(self):
        """Test that users cannot view other users."""
        mock_session = AsyncMock()

        user = MagicMock()
        user.id = uuid4()
        user.role = UserRole.STUDENT

        other_user_id = str(uuid4())

        with patch('apps.backend.api.v1.endpoints.analytics_production.database_service') as mock_db_service:
            mock_db_service.initialize = AsyncMock()

            with pytest.raises(HTTPException) as exc_info:
                await get_user(
                    user_id=other_user_id,
                    current_user=user,
                    session=mock_session
                )

            assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_get_user_not_found(self, mock_admin_user):
        """Test handling when user is not found."""
        mock_session = AsyncMock()
        target_user_id = str(uuid4())

        user_result = AsyncMock()
        user_result.scalar_one_or_none.return_value = None

        mock_session.execute.return_value = user_result

        with patch('apps.backend.api.v1.endpoints.analytics_production.database_service') as mock_db_service:
            mock_db_service.initialize = AsyncMock()

            with pytest.raises(HTTPException) as exc_info:
                await get_user(
                    user_id=target_user_id,
                    current_user=mock_admin_user,
                    session=mock_session
                )

            assert exc_info.value.status_code == 404
            assert "User not found" in str(exc_info.value.detail)
