#!/usr/bin/env python3
"""
Database Integration Test for ToolboxAI Roblox Environment

This script tests all database connections, schemas, and integrations
to ensure everything is working correctly.
"""

import os
import sys
import asyncio
from pathlib import Path
from typing import Dict, Any, List
from sqlalchemy import text

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from database.connection_manager import db_manager, health_check, get_session, get_async_session


class DatabaseIntegrationTest:
    """Comprehensive database integration testing."""

    def __init__(self):
        """Initialize the test suite."""
        self.results = {}
        self.errors = []

    def run_all_tests(self) -> bool:
        """Run all integration tests."""
        print("🧪 ToolboxAI Database Integration Tests")
        print("=" * 50)

        tests = [
            ("Connection Health", self.test_connection_health),
            ("Database Schemas", self.test_database_schemas),
            ("User Management", self.test_user_management),
            ("Educational Content", self.test_educational_content),
            ("AI Agents", self.test_ai_agents),
            ("LMS Integration", self.test_lms_integration),
            ("Analytics", self.test_analytics),
            ("Redis Integration", self.test_redis_integration),
            ("Migration System", self.test_migration_system),
            ("Performance", self.test_performance),
        ]

        all_passed = True

        for test_name, test_func in tests:
            print(f"\n🔍 Running {test_name} test...")
            try:
                result = test_func()
                self.results[test_name] = result
                if result:
                    print(f"✅ {test_name} test passed")
                else:
                    print(f"❌ {test_name} test failed")
                    all_passed = False
            except Exception as e:
                print(f"❌ {test_name} test error: {e}")
                self.errors.append(f"{test_name}: {e}")
                all_passed = False

        self.print_summary()
        return all_passed

    def test_connection_health(self) -> bool:
        """Test database connection health."""
        try:
            db_manager.initialize()
            results = health_check()

            # Check if all required services are healthy
            required_services = ["postgresql_education", "redis"]
            for service in required_services:
                if not results.get(service, False):
                    print(f"❌ {service} is not healthy")
                    return False

            return True
        except Exception as e:
            print(f"❌ Connection health test failed: {e}")
            return False

    def test_database_schemas(self) -> bool:
        """Test database schema integrity."""
        try:
            with get_session("education") as session:
                # Test core tables exist
                core_tables = [
                    "users",
                    "roles",
                    "user_roles",
                    "user_sessions",
                    "learning_objectives",
                    "educational_content",
                    "quizzes",
                    "quiz_questions",
                    "quiz_options",
                    "quiz_attempts",
                    "user_progress",
                ]

                for table in core_tables:
                    result = session.execute(text(f"SELECT 1 FROM {table} LIMIT 1"))
                    if not result:
                        print(f"❌ Table {table} not accessible")
                        return False

                # Test AI agent tables
                ai_tables = [
                    "ai_agents",
                    "agent_tasks",
                    "agent_states",
                    "agent_metrics",
                    "roblox_plugins",
                    "roblox_scripts",
                ]

                for table in ai_tables:
                    result = session.execute(text(f"SELECT 1 FROM {table} LIMIT 1"))
                    if not result:
                        print(f"❌ AI table {table} not accessible")
                        return False

                # Test LMS integration tables
                lms_tables = [
                    "lms_integrations",
                    "lms_courses",
                    "lms_assignments",
                    "websocket_connections",
                    "collaboration_sessions",
                ]

                for table in lms_tables:
                    result = session.execute(text(f"SELECT 1 FROM {table} LIMIT 1"))
                    if not result:
                        print(f"❌ LMS table {table} not accessible")
                        return False

                # Test analytics tables
                analytics_tables = [
                    "usage_analytics",
                    "educational_analytics",
                    "error_logs",
                    "system_health_checks",
                    "notifications",
                    "achievements",
                ]

                for table in analytics_tables:
                    result = session.execute(text(f"SELECT 1 FROM {table} LIMIT 1"))
                    if not result:
                        print(f"❌ Analytics table {table} not accessible")
                        return False

                return True

        except Exception as e:
            print(f"❌ Schema test failed: {e}")
            return False

    def test_user_management(self) -> bool:
        """Test user management functionality."""
        try:
            with get_session("education") as session:
                # Test user creation using direct SQL queries
                # Check if test user exists
                result = session.execute(
                    text("SELECT COUNT(*) FROM users WHERE email = 'test@example.com'")
                )
                user_count = result.scalar()

                if user_count == 0:
                    print("❌ Test user not found")
                    return False

                # Test user data integrity
                result = session.execute(
                    text(
                        """
                    SELECT username, email, role, is_active, is_verified 
                    FROM users 
                    WHERE email = 'test@example.com'
                """
                    )
                )
                user_data = result.fetchone()

                if not user_data:
                    print("❌ User data not accessible")
                    return False

                username, email, role, is_active, is_verified = user_data

                # Validate user data
                if username != "testuser":
                    print("❌ Username not set correctly")
                    return False

                if role != "teacher":
                    print("❌ User role not set correctly")
                    return False

                if not is_active:
                    print("❌ User not active")
                    return False

                if not is_verified:
                    print("❌ User not verified")
                    return False

                print(f"✅ User management test passed - User: {username}, Role: {role}")
                return True

        except Exception as e:
            print(f"❌ User management test failed: {e}")
            return False

    def test_educational_content(self) -> bool:
        """Test educational content functionality."""
        try:
            with get_session("education") as session:
                # Test learning objectives
                result = session.execute(text("SELECT COUNT(*) FROM learning_objectives"))
                objective_count = result.scalar()
                if objective_count == 0:
                    print("❌ No learning objectives found")
                    return False

                # Test educational content
                result = session.execute(text("SELECT COUNT(*) FROM educational_content"))
                content_count = result.scalar()

                # Test quizzes
                result = session.execute(text("SELECT COUNT(*) FROM quizzes"))
                quiz_count = result.scalar()

                return True

        except Exception as e:
            print(f"❌ Educational content test failed: {e}")
            return False

    def test_ai_agents(self) -> bool:
        """Test AI agent system."""
        try:
            with get_session("education") as session:
                # Test AI agents
                result = session.execute(text("SELECT COUNT(*) FROM ai_agents"))
                agent_count = result.scalar()
                if agent_count == 0:
                    print("❌ No AI agents found")
                    return False

                # Test agent tasks
                result = session.execute(text("SELECT COUNT(*) FROM agent_tasks"))
                task_count = result.scalar()

                # Test Roblox integration
                result = session.execute(text("SELECT COUNT(*) FROM roblox_plugins"))
                plugin_count = result.scalar()

                return True

        except Exception as e:
            print(f"❌ AI agents test failed: {e}")
            return False

    def test_lms_integration(self) -> bool:
        """Test LMS integration functionality."""
        try:
            with get_session("education") as session:
                # Test LMS integrations
                result = session.execute(text("SELECT COUNT(*) FROM lms_integrations"))
                lms_count = result.scalar()
                if lms_count == 0:
                    print("❌ No LMS integrations found")
                    return False

                # Test WebSocket connections
                result = session.execute(text("SELECT COUNT(*) FROM websocket_connections"))
                ws_count = result.scalar()

                # Test collaboration sessions
                result = session.execute(text("SELECT COUNT(*) FROM collaboration_sessions"))
                collab_count = result.scalar()

                return True

        except Exception as e:
            print(f"❌ LMS integration test failed: {e}")
            return False

    def test_analytics(self) -> bool:
        """Test analytics and monitoring."""
        try:
            with get_session("education") as session:
                # Test usage analytics
                result = session.execute(text("SELECT COUNT(*) FROM usage_analytics"))
                usage_count = result.scalar()

                # Test educational analytics
                result = session.execute(text("SELECT COUNT(*) FROM educational_analytics"))
                edu_count = result.scalar()

                # Test achievements
                result = session.execute(text("SELECT COUNT(*) FROM achievements"))
                achievement_count = result.scalar()
                if achievement_count == 0:
                    print("❌ No achievements found")
                    return False

                # Test leaderboards
                result = session.execute(text("SELECT COUNT(*) FROM leaderboards"))
                leaderboard_count = result.scalar()
                if leaderboard_count == 0:
                    print("❌ No leaderboards found")
                    return False

                return True

        except Exception as e:
            print(f"❌ Analytics test failed: {e}")
            return False

    def test_redis_integration(self) -> bool:
        """Test Redis integration."""
        try:
            redis_client = db_manager.get_redis_client()
            if not redis_client:
                print("❌ Redis client not available")
                return False

            # Test basic operations
            redis_client.set("test_key", "test_value", ex=60)
            value = redis_client.get("test_key")
            if value != "test_value":
                print("❌ Redis set/get failed")
                return False

            redis_client.delete("test_key")
            return True

        except Exception as e:
            print(f"❌ Redis integration test failed: {e}")
            return False

    def test_migration_system(self) -> bool:
        """Test migration system."""
        try:
            # Check if Alembic is configured
            alembic_dir = project_root / "database" / "migrations"
            if not alembic_dir.exists():
                print("❌ Alembic migrations directory not found")
                return False

            # Check if versions directory exists
            versions_dir = alembic_dir / "versions"
            if not versions_dir.exists():
                print("❌ Alembic versions directory not found")
                return False

            # Check if there are migration files
            migration_files = list(versions_dir.glob("*.py"))
            if len(migration_files) == 0:
                print("❌ No migration files found")
                return False

            return True

        except Exception as e:
            print(f"❌ Migration system test failed: {e}")
            return False

    def test_performance(self) -> bool:
        """Test database performance."""
        try:
            import time

            with get_session("education") as session:
                # Test query performance
                start_time = time.time()

                # Simple query
                result = session.execute(text("SELECT COUNT(*) FROM users"))
                user_count = result.scalar()

                # Complex query with joins
                result = session.execute(
                    text(
                        """
                    SELECT u.email, COUNT(qa.id) as quiz_count
                    FROM users u
                    LEFT JOIN quiz_attempts qa ON u.id = qa.user_id
                    GROUP BY u.id, u.email
                    LIMIT 10
                """
                    )
                )
                results = result.fetchall()

                end_time = time.time()
                query_time = end_time - start_time

                if query_time > 5.0:  # 5 seconds threshold
                    print(f"❌ Query performance too slow: {query_time:.2f}s")
                    return False

                print(f"✅ Query performance: {query_time:.2f}s")
                return True

        except Exception as e:
            print(f"❌ Performance test failed: {e}")
            return False

    def print_summary(self):
        """Print test summary."""
        print("\n" + "=" * 50)
        print("📊 Test Summary")
        print("=" * 50)

        total_tests = len(self.results)
        passed_tests = sum(1 for result in self.results.values() if result)
        failed_tests = total_tests - passed_tests

        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")

        if failed_tests > 0:
            print(f"\n❌ Failed Tests:")
            for test_name, result in self.results.items():
                if not result:
                    print(f"  - {test_name}")

        if self.errors:
            print(f"\n🚨 Errors:")
            for error in self.errors:
                print(f"  - {error}")

        if passed_tests == total_tests:
            print(f"\n🎉 All tests passed! Database integration is working correctly.")
        else:
            print(f"\n⚠️  Some tests failed. Please check the errors above.")


def main():
    """Main function."""
    test_suite = DatabaseIntegrationTest()
    success = test_suite.run_all_tests()

    if success:
        print("\n✅ Database integration test completed successfully!")
        sys.exit(0)
    else:
        print("\n❌ Database integration test failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
