"""
Unit tests for Database Service

Tests PostgreSQL connection pooling, role-based dashboard data fetching,
and query execution for teacher, student, admin, and parent dashboards.
"""

from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import AsyncMock, patch

import pytest

from apps.backend.services.database import DatabaseService, db_service


@pytest.fixture
def database_service():
    """DatabaseService instance"""
    return DatabaseService()


@pytest.fixture
def mock_pool():
    """Mock asyncpg connection pool"""
    pool = AsyncMock()
    pool.acquire = AsyncMock()
    pool.close = AsyncMock()
    return pool


@pytest.fixture
def mock_connection():
    """Mock database connection"""
    conn = AsyncMock()
    conn.fetch = AsyncMock()
    conn.fetchrow = AsyncMock()
    conn.fetchval = AsyncMock()
    return conn


@pytest.mark.unit
class TestDatabaseConnection:
    """Test database connection pool management"""

    @pytest.mark.asyncio
    async def test_connect_success(self, database_service):
        """Test successful database connection"""
        with patch(
            "apps.backend.services.database.asyncpg.create_pool", new_callable=AsyncMock
        ) as mock_create_pool:
            mock_pool = AsyncMock()
            mock_create_pool.return_value = mock_pool

            await database_service.connect()

            assert database_service.pool == mock_pool
            mock_create_pool.assert_awaited_once()
            call_kwargs = mock_create_pool.call_args[1]
            assert call_kwargs["min_size"] == 5
            assert call_kwargs["max_size"] == 20
            assert call_kwargs["command_timeout"] == 60

    @pytest.mark.asyncio
    async def test_connect_already_connected(self, database_service):
        """Test connect when already connected"""
        existing_pool = AsyncMock()
        database_service.pool = existing_pool

        with patch(
            "apps.backend.services.database.asyncpg.create_pool", new_callable=AsyncMock
        ) as mock_create_pool:
            await database_service.connect()

            # Should not create new pool
            mock_create_pool.assert_not_called()
            assert database_service.pool == existing_pool

    @pytest.mark.asyncio
    async def test_connect_failure(self, database_service):
        """Test connection failure"""
        with patch(
            "apps.backend.services.database.asyncpg.create_pool", new_callable=AsyncMock
        ) as mock_create_pool:
            mock_create_pool.side_effect = Exception("Connection failed")

            with pytest.raises(Exception) as exc_info:
                await database_service.connect()

            assert "Connection failed" in str(exc_info.value)
            assert database_service.pool is None

    @pytest.mark.asyncio
    async def test_disconnect_success(self, database_service):
        """Test successful disconnection"""
        mock_pool = AsyncMock()
        database_service.pool = mock_pool

        await database_service.disconnect()

        mock_pool.close.assert_awaited_once()
        assert database_service.pool is None

    @pytest.mark.asyncio
    async def test_disconnect_no_pool(self, database_service):
        """Test disconnect when no pool exists"""
        database_service.pool = None

        # Should not raise exception
        await database_service.disconnect()

        assert database_service.pool is None


@pytest.mark.unit
class TestGetDashboardData:
    """Test role-based dashboard data retrieval"""

    @pytest.mark.asyncio
    async def test_get_dashboard_data_teacher(self, database_service):
        """Test dashboard data for teacher role"""
        mock_teacher_data = {"role": "teacher", "kpis": {"activeClasses": 3}, "classes": []}

        with patch.object(
            database_service,
            "_get_teacher_dashboard",
            new_callable=AsyncMock,
            return_value=mock_teacher_data,
        ):
            with patch.object(database_service, "connect", new_callable=AsyncMock):
                database_service.pool = AsyncMock()

                result = await database_service.get_dashboard_data("teacher", 123)

        assert result["role"] == "teacher"
        assert "kpis" in result

    @pytest.mark.asyncio
    async def test_get_dashboard_data_student(self, database_service):
        """Test dashboard data for student role"""
        mock_student_data = {"role": "student", "studentData": {"xp": 1000}}

        with patch.object(
            database_service,
            "_get_student_dashboard",
            new_callable=AsyncMock,
            return_value=mock_student_data,
        ):
            with patch.object(database_service, "connect", new_callable=AsyncMock):
                database_service.pool = AsyncMock()

                result = await database_service.get_dashboard_data("student", 456)

        assert result["role"] == "student"
        assert "studentData" in result

    @pytest.mark.asyncio
    async def test_get_dashboard_data_admin(self, database_service):
        """Test dashboard data for admin role"""
        mock_admin_data = {"role": "admin", "stats": {"totalUsers": 1000}}

        with patch.object(
            database_service,
            "_get_admin_dashboard",
            new_callable=AsyncMock,
            return_value=mock_admin_data,
        ):
            with patch.object(database_service, "connect", new_callable=AsyncMock):
                database_service.pool = AsyncMock()

                result = await database_service.get_dashboard_data("admin", 789)

        assert result["role"] == "admin"
        assert "stats" in result

    @pytest.mark.asyncio
    async def test_get_dashboard_data_parent(self, database_service):
        """Test dashboard data for parent role"""
        mock_parent_data = {"role": "parent", "children": []}

        with patch.object(
            database_service,
            "_get_parent_dashboard",
            new_callable=AsyncMock,
            return_value=mock_parent_data,
        ):
            with patch.object(database_service, "connect", new_callable=AsyncMock):
                database_service.pool = AsyncMock()

                result = await database_service.get_dashboard_data("parent", 999)

        assert result["role"] == "parent"
        assert "children" in result

    @pytest.mark.asyncio
    async def test_get_dashboard_data_invalid_role(self, database_service):
        """Test dashboard data with invalid role"""
        database_service.pool = AsyncMock()

        with pytest.raises(ValueError) as exc_info:
            await database_service.get_dashboard_data("invalid_role", 123)

        assert "Invalid role" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_dashboard_data_case_insensitive(self, database_service):
        """Test role matching is case insensitive"""
        mock_data = {"role": "teacher"}

        with patch.object(
            database_service,
            "_get_teacher_dashboard",
            new_callable=AsyncMock,
            return_value=mock_data,
        ):
            with patch.object(database_service, "connect", new_callable=AsyncMock):
                database_service.pool = AsyncMock()

                result = await database_service.get_dashboard_data("TEACHER", 123)

        assert result["role"] == "teacher"

    @pytest.mark.asyncio
    async def test_get_dashboard_data_auto_connect(self, database_service):
        """Test auto-connect when pool not initialized"""
        database_service.pool = None
        mock_data = {"role": "teacher"}

        with patch.object(
            database_service,
            "_get_teacher_dashboard",
            new_callable=AsyncMock,
            return_value=mock_data,
        ):
            with patch.object(database_service, "connect", new_callable=AsyncMock) as mock_connect:
                database_service.pool = AsyncMock()  # Set after connect

                await database_service.get_dashboard_data("teacher", 123)

                mock_connect.assert_awaited_once()


@pytest.mark.unit
class TestTeacherDashboard:
    """Test teacher dashboard data fetching"""

    @pytest.mark.asyncio
    async def test_get_teacher_dashboard_success(self, database_service, mock_connection):
        """Test successful teacher dashboard retrieval"""
        # Mock database responses
        mock_connection.fetch.side_effect = [
            [
                {
                    "id": 1,
                    "name": "Math 101",
                    "subject": "Math",
                    "grade_level": 5,
                    "student_count": 20,
                }
            ],  # classes
            [
                {
                    "id": 1,
                    "title": "Homework",
                    "type": "assignment",
                    "due_date": datetime.now(),
                    "class_id": 1,
                    "submissions": 15,
                    "graded": 10,
                }
            ],  # assignments
            [],  # recent_activity
            [],  # lessons
        ]
        mock_connection.fetchrow.return_value = {
            "average_grade": Decimal("85.5"),
            "active_students": 20,
            "total_submissions": 50,
            "pending_grading": 5,
        }

        mock_pool = AsyncMock()
        mock_pool.acquire.return_value.__aenter__.return_value = mock_connection
        database_service.pool = mock_pool

        result = await database_service._get_teacher_dashboard(123)

        assert result["role"] == "teacher"
        assert "kpis" in result
        assert "classes" in result
        assert "assignments" in result
        assert result["kpis"]["activeClasses"] == 1
        assert result["kpis"]["pendingAssessments"] == 5

    @pytest.mark.asyncio
    async def test_get_teacher_dashboard_no_pool(self, database_service):
        """Test teacher dashboard without connection pool"""
        database_service.pool = None

        with pytest.raises(RuntimeError) as exc_info:
            await database_service._get_teacher_dashboard(123)

        assert "not initialized" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_teacher_dashboard_empty_data(self, database_service, mock_connection):
        """Test teacher dashboard with no classes or assignments"""
        mock_connection.fetch.side_effect = [[], [], [], []]  # All empty
        mock_connection.fetchrow.return_value = {
            "average_grade": None,
            "active_students": 0,
            "total_submissions": 0,
            "pending_grading": 0,
        }

        mock_pool = AsyncMock()
        mock_pool.acquire.return_value.__aenter__.return_value = mock_connection
        database_service.pool = mock_pool

        result = await database_service._get_teacher_dashboard(123)

        assert result["kpis"]["activeClasses"] == 0
        assert result["kpis"]["totalStudents"] == 0
        assert len(result["classes"]) == 0


@pytest.mark.unit
class TestStudentDashboard:
    """Test student dashboard data fetching"""

    @pytest.mark.asyncio
    async def test_get_student_dashboard_success(self, database_service, mock_connection):
        """Test successful student dashboard retrieval"""
        # Mock student data
        mock_connection.fetchrow.return_value = {
            "id": 456,
            "username": "student1",
            "email": "student@example.com",
            "xp_points": 1500,
            "level": 5,
            "streak_days": 7,
            "total_badges": 12,
            "rank_position": 3,
        }

        # Mock other queries
        mock_connection.fetch.side_effect = [
            [],  # classes
            [],  # assignments
            [],  # achievements
            [],  # leaderboard
            [],  # activity
        ]

        with patch.object(
            database_service,
            "_get_student_upcoming_events",
            new_callable=AsyncMock,
            return_value=[],
        ):
            mock_pool = AsyncMock()
            mock_pool.acquire.return_value.__aenter__.return_value = mock_connection
            database_service.pool = mock_pool

            result = await database_service._get_student_dashboard(456)

        assert result["role"] == "student"
        assert result["studentData"]["xp"] == 1500
        assert result["studentData"]["level"] == 5
        assert result["studentData"]["streakDays"] == 7

    @pytest.mark.asyncio
    async def test_get_student_dashboard_with_assignments(self, database_service, mock_connection):
        """Test student dashboard with assignments"""
        mock_connection.fetchrow.return_value = {
            "id": 456,
            "username": "student1",
            "email": "student@example.com",
            "xp_points": 1000,
            "level": 3,
            "streak_days": 5,
            "total_badges": 8,
            "rank_position": 5,
        }

        mock_assignments = [
            {
                "id": 1,
                "title": "Math Homework",
                "subject": "Math",
                "due_date": datetime.now() + timedelta(days=2),
                "status": "in_progress",
                "grade": None,
                "progress": 50,
            }
        ]

        mock_connection.fetch.side_effect = [
            [],  # classes
            mock_assignments,
            [],  # achievements
            [],  # leaderboard
            [],  # activity
        ]

        with patch.object(
            database_service,
            "_get_student_upcoming_events",
            new_callable=AsyncMock,
            return_value=[],
        ):
            mock_pool = AsyncMock()
            mock_pool.acquire.return_value.__aenter__.return_value = mock_connection
            database_service.pool = mock_pool

            result = await database_service._get_student_dashboard(456)

        assert len(result["assignments"]) == 1
        assert result["assignments"][0]["title"] == "Math Homework"
        assert result["assignments"][0]["progress"] == 50


@pytest.mark.unit
class TestAdminDashboard:
    """Test admin dashboard data fetching"""

    @pytest.mark.asyncio
    async def test_get_admin_dashboard_success(self, database_service, mock_connection):
        """Test successful admin dashboard retrieval"""
        mock_connection.fetchrow.side_effect = [
            {  # stats
                "total_users": 1000,
                "active_users": 750,
                "total_schools": 50,
                "total_classes": 200,
                "total_assignments": 500,
                "total_lessons": 300,
            },
            {"coppa_compliant": 45, "ferpa_compliant": 48, "pending_reviews": 2},  # compliance
            {  # api_metrics
                "total_calls": 50000,
                "avg_response_time": Decimal("125.5"),
                "errors": 10,
            },
        ]

        mock_connection.fetch.side_effect = [[], []]  # user_growth  # events

        mock_connection.fetchval.side_effect = [
            500,
            100,
            5,
        ]  # students, lessons, pending assessments

        mock_pool = AsyncMock()
        mock_pool.acquire.return_value.__aenter__.return_value = mock_connection
        database_service.pool = mock_pool

        result = await database_service._get_admin_dashboard(999)

        assert result["role"] == "admin"
        assert result["stats"]["totalUsers"] == 1000
        assert result["stats"]["activeUsers"] == 750
        assert result["systemMetrics"]["errors"] == 10
        assert result["compliance"]["pendingAlerts"] == 2


@pytest.mark.unit
class TestParentDashboard:
    """Test parent dashboard data fetching"""

    @pytest.mark.asyncio
    async def test_get_parent_dashboard_with_children(self, database_service, mock_connection):
        """Test parent dashboard with children"""
        # Mock children
        mock_children = [
            {
                "student_id": 101,
                "username": "child1",
                "email": "child1@example.com",
                "grade_level": 5,
                "gpa": Decimal("3.8"),
                "attendance_rate": Decimal("95.5"),
                "xp_points": 1200,
                "level": 4,
            }
        ]

        mock_connection.fetch.side_effect = [
            mock_children,  # children
            [],  # grades
            [],  # recent_assignments
            [],  # upcoming
            [],  # messages
        ]

        mock_connection.fetchrow.return_value = {
            "present": 85,
            "absent": 3,
            "tardy": 2,
            "total": 90,
        }

        mock_pool = AsyncMock()
        mock_pool.acquire.return_value.__aenter__.return_value = mock_connection
        database_service.pool = mock_pool

        result = await database_service._get_parent_dashboard(888)

        assert result["role"] == "parent"
        assert len(result["children"]) == 1
        assert result["children"][0]["name"] == "child1"
        assert result["children"][0]["gpa"] == 3.8


@pytest.mark.unit
class TestUtilityMethods:
    """Test utility and helper methods"""

    def test_format_time_ago_just_now(self, database_service):
        """Test time formatting for recent timestamps"""
        now = datetime.now()
        result = database_service._format_time_ago(now)

        assert result == "Just now"

    def test_format_time_ago_minutes(self, database_service):
        """Test time formatting for minutes ago"""
        timestamp = datetime.now() - timedelta(minutes=15)
        result = database_service._format_time_ago(timestamp)

        assert "15 minute" in result
        assert "ago" in result

    def test_format_time_ago_hours(self, database_service):
        """Test time formatting for hours ago"""
        timestamp = datetime.now() - timedelta(hours=3)
        result = database_service._format_time_ago(timestamp)

        assert "3 hour" in result
        assert "ago" in result

    def test_format_time_ago_days(self, database_service):
        """Test time formatting for days ago"""
        timestamp = datetime.now() - timedelta(days=2)
        result = database_service._format_time_ago(timestamp)

        assert "2 day" in result
        assert "ago" in result

    def test_format_time_ago_weeks(self, database_service):
        """Test time formatting for weeks ago"""
        timestamp = datetime.now() - timedelta(days=10)
        result = database_service._format_time_ago(timestamp)

        # Should return month/day format
        assert "ago" not in result

    def test_format_time_ago_none(self, database_service):
        """Test time formatting with None timestamp"""
        result = database_service._format_time_ago(None)

        assert result == "Recently"

    def test_format_user_growth(self, database_service):
        """Test user growth data formatting"""
        now = datetime.now()
        mock_growth_data = [
            {"month": now.replace(day=1), "role": "student", "count": 50},
            {"month": now.replace(day=1), "role": "teacher", "count": 10},
            {"month": now.replace(day=1), "role": "parent", "count": 20},
        ]

        result = database_service._format_user_growth(mock_growth_data)

        assert "labels" in result
        assert "datasets" in result
        assert len(result["datasets"]) == 3
        assert result["datasets"][0]["label"] == "Students"
        assert result["datasets"][1]["label"] == "Teachers"
        assert result["datasets"][2]["label"] == "Parents"


@pytest.mark.unit
class TestStudentUpcomingEvents:
    """Test student upcoming events helper"""

    @pytest.mark.asyncio
    async def test_get_student_upcoming_events_with_assignments(
        self, database_service, mock_connection
    ):
        """Test upcoming events with assignments"""
        mock_assignments = [
            {"title": "Math Test", "due_date": datetime.now() + timedelta(days=2), "type": "quiz"}
        ]
        mock_connection.fetch.side_effect = [mock_assignments, []]

        result = await database_service._get_student_upcoming_events(123, mock_connection)

        assert len(result) > 0
        assert result[0]["type"] == "assessment"

    @pytest.mark.asyncio
    async def test_get_student_upcoming_events_with_lessons(
        self, database_service, mock_connection
    ):
        """Test upcoming events with lessons"""
        mock_lessons = [
            {"title": "Science Experiment", "scheduled_at": datetime.now() + timedelta(days=1)}
        ]
        mock_connection.fetch.side_effect = [[], mock_lessons]

        result = await database_service._get_student_upcoming_events(123, mock_connection)

        assert len(result) > 0
        assert result[0]["type"] == "lesson"
        assert "Roblox" in result[0]["event"]

    @pytest.mark.asyncio
    async def test_get_student_upcoming_events_sorted_by_date(
        self, database_service, mock_connection
    ):
        """Test events are sorted by date"""
        future_assignment = {
            "title": "Future Test",
            "due_date": datetime.now() + timedelta(days=5),
            "type": "quiz",
        }
        near_assignment = {
            "title": "Near Test",
            "due_date": datetime.now() + timedelta(days=1),
            "type": "assignment",
        }

        mock_connection.fetch.side_effect = [[future_assignment, near_assignment], []]

        result = await database_service._get_student_upcoming_events(123, mock_connection)

        # First event should be the nearest one
        assert "Near Test" in result[0]["event"]

    @pytest.mark.asyncio
    async def test_get_student_upcoming_events_limited_to_four(
        self, database_service, mock_connection
    ):
        """Test events limited to 4 items"""
        many_assignments = [
            {
                "title": f"Assignment {i}",
                "due_date": datetime.now() + timedelta(days=i),
                "type": "assignment",
            }
            for i in range(1, 10)
        ]

        mock_connection.fetch.side_effect = [many_assignments, []]

        result = await database_service._get_student_upcoming_events(123, mock_connection)

        assert len(result) <= 4


@pytest.mark.unit
class TestGlobalServiceInstance:
    """Test global database service instance"""

    def test_db_service_exists(self):
        """Test global db_service instance exists"""
        assert db_service is not None
        assert isinstance(db_service, DatabaseService)

    def test_db_service_config(self):
        """Test db_service has correct config"""
        assert "host" in db_service.db_config
        assert "port" in db_service.db_config
        assert "database" in db_service.db_config


@pytest.mark.unit
class TestDatabaseConfiguration:
    """Test database configuration"""

    def test_default_configuration(self):
        """Test default database configuration"""
        with patch.dict("os.environ", {}, clear=True):
            service = DatabaseService()

            assert service.db_config["host"] == "localhost"
            assert service.db_config["port"] == 5432
            assert service.db_config["user"] == "eduplatform"
            assert service.db_config["database"] == "educational_platform_dev"

    def test_environment_variable_configuration(self):
        """Test configuration from environment variables"""
        env_vars = {
            "DB_HOST": "custom-host",
            "DB_PORT": "5433",
            "DB_USER": "custom_user",
            "DB_PASSWORD": "custom_pass",
            "DB_NAME": "custom_db",
        }

        with patch.dict("os.environ", env_vars):
            service = DatabaseService()

            assert service.db_config["host"] == "custom-host"
            assert service.db_config["port"] == 5433
            assert service.db_config["user"] == "custom_user"
            assert service.db_config["password"] == "custom_pass"
            assert service.db_config["database"] == "custom_db"
