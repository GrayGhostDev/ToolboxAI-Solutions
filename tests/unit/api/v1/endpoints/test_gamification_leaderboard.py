"""
Tests for GET /gamification/leaderboard endpoint - Leaderboard rankings.

Tests the analytics_production.py leaderboard endpoint which provides:
- Dynamic leaderboard based on timeframe (day, week, month, all)
- Real user data from database
- Current user ranking and percentile
- Total participants count
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from fastapi import HTTPException

from apps.backend.api.v1.endpoints.analytics_production import get_leaderboard
from database.models.models import User, UserRole, Analytics, Leaderboard


class TestGetLeaderboard:
    """Test suite for GET /gamification/leaderboard endpoint."""

    @pytest.fixture
    def mock_current_user(self):
        """Create a mock authenticated user."""
        user = MagicMock()
        user.id = uuid4()
        user.username = "test_user"
        user.role = UserRole.STUDENT
        user.is_active = True
        return user

    @pytest.fixture
    def mock_session(self):
        """Create a mock async database session."""
        session = AsyncMock()
        return session

    @pytest.fixture
    def mock_leaderboard_data(self):
        """Sample leaderboard data."""
        return [
            {"user_id": uuid4(), "username": "user1", "first_name": "Alice", "last_name": "Smith", "xp": 5420, "level": 24},
            {"user_id": uuid4(), "username": "user2", "first_name": "Bob", "last_name": "Johnson", "xp": 5180, "level": 23},
            {"user_id": uuid4(), "username": "user3", "first_name": "Carol", "last_name": "Williams", "xp": 4950, "level": 22},
            {"user_id": uuid4(), "username": "user4", "first_name": "Dave", "last_name": "Brown", "xp": 4720, "level": 21},
            {"user_id": uuid4(), "username": "user5", "first_name": "Eve", "last_name": "Davis", "xp": 4580, "level": 21},
        ]

    def create_mock_leaderboard_rows(self, leaderboard_data):
        """Create mock database result rows."""
        rows = []
        for entry in leaderboard_data:
            row = MagicMock()
            row.user_id = entry["user_id"]
            row.username = entry["username"]
            row.first_name = entry["first_name"]
            row.last_name = entry["last_name"]
            row.xp = entry["xp"]
            row.level = entry.get("level", 0)
            row.rank = entry.get("rank", 0)
            rows.append(row)
        return rows

    @pytest.mark.asyncio
    async def test_leaderboard_success_week_timeframe(
        self, mock_current_user, mock_session, mock_leaderboard_data
    ):
        """Test successful leaderboard retrieval for week timeframe."""
        # Mock leaderboard query result
        mock_leaderboard_result = AsyncMock()
        mock_leaderboard_result.all.return_value = self.create_mock_leaderboard_rows(
            mock_leaderboard_data
        )

        # Mock total participants count
        mock_total_result = AsyncMock()
        mock_total_result.scalar.return_value = 150

        mock_session.execute.side_effect = [
            mock_leaderboard_result,
            mock_total_result,
        ]

        with patch('apps.backend.api.v1.endpoints.analytics_production.database_service') as mock_db_service:
            mock_db_service.initialize = AsyncMock()

            response = await get_leaderboard(
                timeframe="week",
                limit=10,
                current_user=mock_current_user,
                session=mock_session
            )

        # Assertions
        assert response["timeframe"] == "week"
        assert response["total_participants"] == 150
        assert len(response["leaderboard"]) == 5
        assert response["leaderboard"][0]["rank"] == 1
        assert response["leaderboard"][0]["name"] == "Alice Smith"
        assert response["leaderboard"][0]["xp"] == 5420

    @pytest.mark.asyncio
    async def test_leaderboard_all_timeframe_uses_leaderboard_table(
        self, mock_current_user, mock_session, mock_leaderboard_data
    ):
        """Test that 'all' timeframe uses Leaderboard table instead of Analytics."""
        # Mock leaderboard query result
        mock_leaderboard_result = AsyncMock()
        mock_leaderboard_result.all.return_value = self.create_mock_leaderboard_rows(
            mock_leaderboard_data
        )

        # Mock total participants count
        mock_total_result = AsyncMock()
        mock_total_result.scalar.return_value = 200

        mock_session.execute.side_effect = [
            mock_leaderboard_result,
            mock_total_result,
        ]

        with patch('apps.backend.api.v1.endpoints.analytics_production.database_service') as mock_db_service:
            mock_db_service.initialize = AsyncMock()

            response = await get_leaderboard(
                timeframe="all",
                limit=10,
                current_user=mock_current_user,
                session=mock_session
            )

        assert response["timeframe"] == "all"
        assert response["total_participants"] == 200
        assert len(response["leaderboard"]) == 5

    @pytest.mark.asyncio
    async def test_leaderboard_current_user_highlighted(
        self, mock_current_user, mock_session
    ):
        """Test that current user is highlighted as 'You' in leaderboard."""
        # Include current user in leaderboard
        leaderboard_data = [
            {"user_id": uuid4(), "username": "user1", "first_name": "Alice", "last_name": "Smith", "xp": 5420, "level": 24},
            {"user_id": mock_current_user.id, "username": mock_current_user.username, "first_name": "Test", "last_name": "User", "xp": 5180, "level": 23},
            {"user_id": uuid4(), "username": "user3", "first_name": "Carol", "last_name": "Williams", "xp": 4950, "level": 22},
        ]

        mock_leaderboard_result = AsyncMock()
        mock_leaderboard_result.all.return_value = self.create_mock_leaderboard_rows(
            leaderboard_data
        )

        mock_total_result = AsyncMock()
        mock_total_result.scalar.return_value = 100

        mock_session.execute.side_effect = [
            mock_leaderboard_result,
            mock_total_result,
        ]

        with patch('apps.backend.api.v1.endpoints.analytics_production.database_service') as mock_db_service:
            mock_db_service.initialize = AsyncMock()

            response = await get_leaderboard(
                timeframe="week",
                limit=10,
                current_user=mock_current_user,
                session=mock_session
            )

        # Current user should be rank 2 and named "You"
        current_user_entry = response["leaderboard"][1]
        assert current_user_entry["name"] == "You"
        assert current_user_entry["is_current_user"] == True
        assert current_user_entry["rank"] == 2
        assert response["user_stats"]["current_rank"] == 2

    @pytest.mark.asyncio
    async def test_leaderboard_user_not_in_top_list(
        self, mock_current_user, mock_session, mock_leaderboard_data
    ):
        """Test leaderboard when current user is not in top rankings."""
        # Current user not in leaderboard
        mock_leaderboard_result = AsyncMock()
        mock_leaderboard_result.all.return_value = self.create_mock_leaderboard_rows(
            mock_leaderboard_data
        )

        mock_total_result = AsyncMock()
        mock_total_result.scalar.return_value = 150

        mock_session.execute.side_effect = [
            mock_leaderboard_result,
            mock_total_result,
        ]

        with patch('apps.backend.api.v1.endpoints.analytics_production.database_service') as mock_db_service:
            mock_db_service.initialize = AsyncMock()

            response = await get_leaderboard(
                timeframe="week",
                limit=10,
                current_user=mock_current_user,
                session=mock_session
            )

        # User not in top list, so current_rank should be 0
        assert response["user_stats"]["current_rank"] == 0
        assert all(not entry["is_current_user"] for entry in response["leaderboard"])

    @pytest.mark.asyncio
    async def test_leaderboard_calculates_percentile_correctly(
        self, mock_current_user, mock_session
    ):
        """Test that percentile is calculated correctly."""
        # Current user at rank 10 out of 100 total
        leaderboard_data = []
        for i in range(10):
            user_data = {
                "user_id": mock_current_user.id if i == 9 else uuid4(),
                "username": f"user{i}",
                "first_name": f"User{i}",
                "last_name": "Test",
                "xp": 5000 - (i * 100),
                "level": 20 - i
            }
            leaderboard_data.append(user_data)

        mock_leaderboard_result = AsyncMock()
        mock_leaderboard_result.all.return_value = self.create_mock_leaderboard_rows(
            leaderboard_data
        )

        mock_total_result = AsyncMock()
        mock_total_result.scalar.return_value = 100  # 100 total participants

        mock_session.execute.side_effect = [
            mock_leaderboard_result,
            mock_total_result,
        ]

        with patch('apps.backend.api.v1.endpoints.analytics_production.database_service') as mock_db_service:
            mock_db_service.initialize = AsyncMock()

            response = await get_leaderboard(
                timeframe="week",
                limit=10,
                current_user=mock_current_user,
                session=mock_session
            )

        # User at rank 10 out of 100: percentile = (1 - 10/100) * 100 = 90.0
        assert response["user_stats"]["current_rank"] == 10
        assert response["user_stats"]["percentile"] == 90.0

    @pytest.mark.asyncio
    async def test_leaderboard_limit_parameter(
        self, mock_current_user, mock_session
    ):
        """Test that limit parameter controls result count."""
        # Create 20 entries but limit to 5
        leaderboard_data = []
        for i in range(20):
            user_data = {
                "user_id": uuid4(),
                "username": f"user{i}",
                "first_name": f"User{i}",
                "last_name": "Test",
                "xp": 5000 - (i * 50),
                "level": 20
            }
            leaderboard_data.append(user_data)

        # But only return 5 due to limit
        mock_leaderboard_result = AsyncMock()
        mock_leaderboard_result.all.return_value = self.create_mock_leaderboard_rows(
            leaderboard_data[:5]  # Only first 5
        )

        mock_total_result = AsyncMock()
        mock_total_result.scalar.return_value = 200

        mock_session.execute.side_effect = [
            mock_leaderboard_result,
            mock_total_result,
        ]

        with patch('apps.backend.api.v1.endpoints.analytics_production.database_service') as mock_db_service:
            mock_db_service.initialize = AsyncMock()

            response = await get_leaderboard(
                timeframe="week",
                limit=5,
                current_user=mock_current_user,
                session=mock_session
            )

        assert len(response["leaderboard"]) == 5

    @pytest.mark.asyncio
    async def test_leaderboard_day_timeframe(
        self, mock_current_user, mock_session, mock_leaderboard_data
    ):
        """Test leaderboard with day timeframe."""
        mock_leaderboard_result = AsyncMock()
        mock_leaderboard_result.all.return_value = self.create_mock_leaderboard_rows(
            mock_leaderboard_data
        )

        mock_total_result = AsyncMock()
        mock_total_result.scalar.return_value = 75

        mock_session.execute.side_effect = [
            mock_leaderboard_result,
            mock_total_result,
        ]

        with patch('apps.backend.api.v1.endpoints.analytics_production.database_service') as mock_db_service:
            mock_db_service.initialize = AsyncMock()

            response = await get_leaderboard(
                timeframe="day",
                limit=10,
                current_user=mock_current_user,
                session=mock_session
            )

        assert response["timeframe"] == "day"
        assert response["total_participants"] == 75

    @pytest.mark.asyncio
    async def test_leaderboard_month_timeframe(
        self, mock_current_user, mock_session, mock_leaderboard_data
    ):
        """Test leaderboard with month timeframe."""
        mock_leaderboard_result = AsyncMock()
        mock_leaderboard_result.all.return_value = self.create_mock_leaderboard_rows(
            mock_leaderboard_data
        )

        mock_total_result = AsyncMock()
        mock_total_result.scalar.return_value = 250

        mock_session.execute.side_effect = [
            mock_leaderboard_result,
            mock_total_result,
        ]

        with patch('apps.backend.api.v1.endpoints.analytics_production.database_service') as mock_db_service:
            mock_db_service.initialize = AsyncMock()

            response = await get_leaderboard(
                timeframe="month",
                limit=10,
                current_user=mock_current_user,
                session=mock_session
            )

        assert response["timeframe"] == "month"
        assert response["total_participants"] == 250

    @pytest.mark.asyncio
    async def test_leaderboard_empty_results(
        self, mock_current_user, mock_session
    ):
        """Test leaderboard with no data."""
        mock_leaderboard_result = AsyncMock()
        mock_leaderboard_result.all.return_value = []  # No entries

        mock_total_result = AsyncMock()
        mock_total_result.scalar.return_value = 0

        mock_session.execute.side_effect = [
            mock_leaderboard_result,
            mock_total_result,
        ]

        with patch('apps.backend.api.v1.endpoints.analytics_production.database_service') as mock_db_service:
            mock_db_service.initialize = AsyncMock()

            response = await get_leaderboard(
                timeframe="week",
                limit=10,
                current_user=mock_current_user,
                session=mock_session
            )

        assert len(response["leaderboard"]) == 0
        assert response["total_participants"] == 0
        assert response["user_stats"]["current_rank"] == 0
        assert response["user_stats"]["percentile"] == 0

    @pytest.mark.asyncio
    async def test_leaderboard_user_without_names_shows_username(
        self, mock_current_user, mock_session
    ):
        """Test that users without first/last names show username."""
        leaderboard_data = [
            {"user_id": uuid4(), "username": "cooluser123", "first_name": None, "last_name": None, "xp": 5420, "level": 24},
            {"user_id": uuid4(), "username": "player456", "first_name": "", "last_name": "", "xp": 5180, "level": 23},
        ]

        mock_leaderboard_result = AsyncMock()
        mock_leaderboard_result.all.return_value = self.create_mock_leaderboard_rows(
            leaderboard_data
        )

        mock_total_result = AsyncMock()
        mock_total_result.scalar.return_value = 50

        mock_session.execute.side_effect = [
            mock_leaderboard_result,
            mock_total_result,
        ]

        with patch('apps.backend.api.v1.endpoints.analytics_production.database_service') as mock_db_service:
            mock_db_service.initialize = AsyncMock()

            response = await get_leaderboard(
                timeframe="week",
                limit=10,
                current_user=mock_current_user,
                session=mock_session
            )

        # Should show username when names are missing
        assert response["leaderboard"][0]["name"] == "cooluser123"
        assert response["leaderboard"][1]["name"] == "player456"

    @pytest.mark.asyncio
    async def test_leaderboard_database_error_handling(
        self, mock_current_user, mock_session
    ):
        """Test that database errors are handled gracefully."""
        mock_session.execute.side_effect = Exception("Database connection error")

        with patch('apps.backend.api.v1.endpoints.analytics_production.database_service') as mock_db_service:
            mock_db_service.initialize = AsyncMock()

            with pytest.raises(HTTPException) as exc_info:
                await get_leaderboard(
                    timeframe="week",
                    limit=10,
                    current_user=mock_current_user,
                    session=mock_session
                )

            assert exc_info.value.status_code == 500
            assert "Failed to fetch leaderboard" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_leaderboard_response_structure(
        self, mock_current_user, mock_session
    ):
        """Test that response has correct structure with all required fields."""
        mock_leaderboard_result = AsyncMock()
        mock_leaderboard_result.all.return_value = []

        mock_total_result = AsyncMock()
        mock_total_result.scalar.return_value = 0

        mock_session.execute.side_effect = [
            mock_leaderboard_result,
            mock_total_result,
        ]

        with patch('apps.backend.api.v1.endpoints.analytics_production.database_service') as mock_db_service:
            mock_db_service.initialize = AsyncMock()

            response = await get_leaderboard(
                timeframe="week",
                limit=10,
                current_user=mock_current_user,
                session=mock_session
            )

        # Verify top-level fields
        assert "timeframe" in response
        assert "last_updated" in response
        assert "total_participants" in response
        assert "leaderboard" in response
        assert "user_stats" in response

        # Verify user_stats fields
        assert "current_rank" in response["user_stats"]
        assert "percentile" in response["user_stats"]

        # Verify data types
        assert isinstance(response["timeframe"], str)
        assert isinstance(response["last_updated"], str)
        assert isinstance(response["total_participants"], int)
        assert isinstance(response["leaderboard"], list)
        assert isinstance(response["user_stats"], dict)

    @pytest.mark.asyncio
    async def test_leaderboard_entry_structure(
        self, mock_current_user, mock_session, mock_leaderboard_data
    ):
        """Test that each leaderboard entry has correct structure."""
        mock_leaderboard_result = AsyncMock()
        mock_leaderboard_result.all.return_value = self.create_mock_leaderboard_rows(
            mock_leaderboard_data
        )

        mock_total_result = AsyncMock()
        mock_total_result.scalar.return_value = 100

        mock_session.execute.side_effect = [
            mock_leaderboard_result,
            mock_total_result,
        ]

        with patch('apps.backend.api.v1.endpoints.analytics_production.database_service') as mock_db_service:
            mock_db_service.initialize = AsyncMock()

            response = await get_leaderboard(
                timeframe="week",
                limit=10,
                current_user=mock_current_user,
                session=mock_session
            )

        # Check first entry structure
        entry = response["leaderboard"][0]
        required_fields = ["rank", "user_id", "name", "xp", "level", "badges", "is_current_user", "movement"]

        for field in required_fields:
            assert field in entry, f"Missing field: {field}"

        # Verify data types
        assert isinstance(entry["rank"], int)
        assert isinstance(entry["user_id"], str)
        assert isinstance(entry["name"], str)
        assert isinstance(entry["xp"], int)
        assert isinstance(entry["level"], int)
        assert isinstance(entry["is_current_user"], bool)

    @pytest.mark.asyncio
    async def test_leaderboard_authorization_all_roles(self, mock_session):
        """Test that all authenticated users can access leaderboard."""
        roles = [UserRole.ADMIN, UserRole.TEACHER, UserRole.STUDENT]

        for role in roles:
            user = MagicMock()
            user.id = uuid4()
            user.role = role

            mock_leaderboard_result = AsyncMock()
            mock_leaderboard_result.all.return_value = []

            mock_total_result = AsyncMock()
            mock_total_result.scalar.return_value = 0

            mock_session.execute.side_effect = [
                mock_leaderboard_result,
                mock_total_result,
            ]

            with patch('apps.backend.api.v1.endpoints.analytics_production.database_service') as mock_db_service:
                mock_db_service.initialize = AsyncMock()

                # Should not raise authorization error
                response = await get_leaderboard(
                    timeframe="week",
                    limit=10,
                    current_user=user,
                    session=mock_session
                )

                assert response is not None
                assert "leaderboard" in response


@pytest.mark.integration
class TestLeaderboardIntegration:
    """Integration tests for leaderboard endpoint with real database."""

    @pytest.mark.asyncio
    async def test_leaderboard_with_test_database(self):
        """Test leaderboard endpoint with actual test database."""
        # TODO: Implement with test database fixture
        pass

    @pytest.mark.asyncio
    async def test_leaderboard_performance_with_large_dataset(self):
        """Test leaderboard performance with large user base."""
        # TODO: Implement performance test with 10,000+ users
        pass

    @pytest.mark.asyncio
    async def test_leaderboard_ranking_accuracy(self):
        """Test that rankings are calculated accurately."""
        # TODO: Verify ranking logic with real data
        pass
