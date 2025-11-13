
from unittest.mock import Mock, patch

import pytest


@pytest.fixture
def mock_db_connection():
    """Mock database connection for tests"""
    with patch('psycopg2.connect') as mock_connect:
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn
        yield mock_conn

#!/usr/bin/env python3
"""
Database Performance Testing Script
Validates query performance after optimization and measures execution times
Target: All queries < 50ms
"""

import os
import statistics
import sys
import time
from contextlib import contextmanager
from typing import Any, Dict, List, Tuple

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Direct database connection for testing
DATABASE_URL = "postgresql://grayghostdata@localhost/educational_platform"

class DatabasePerformanceTester:
    """Comprehensive database performance testing suite."""
    
    def __init__(self):
        """Initialize the performance tester."""
        self.engine = create_engine(DATABASE_URL)
        self.Session = sessionmaker(bind=self.engine)
        self.results = []
        self.target_time_ms = 50.0  # Target response time
        
    @contextmanager
    def measure_time(self, query_name: str):
        """Context manager to measure query execution time."""
        start_time = time.perf_counter()
        yield
        end_time = time.perf_counter()
        execution_time = (end_time - start_time) * 1000  # Convert to milliseconds
        
        self.results.append({
            'query': query_name,
            'time_ms': execution_time,
            'passed': execution_time < self.target_time_ms
        })
        
        status = "✅ PASS" if execution_time < self.target_time_ms else "❌ FAIL"
        print(f"{status} {query_name}: {execution_time:.2f}ms")

    def test_user_queries(self):
        """Test user-related queries."""
        print("\n🔍 Testing User Queries...")
        
        session = self.Session()
        try:
            # Test 1: User authentication by email
            with self.measure_time("User Authentication by Email"):
                session.execute(text("""
                    SELECT id, username, password_hash, role 
                    FROM users 
                    WHERE email = 'test@example.com' AND is_active = true
                    LIMIT 1
                """))
            
            # Test 2: Active users by school
            with self.measure_time("Active Users by School"):
                session.execute(text("""
                    SELECT COUNT(*) 
                    FROM users 
                    WHERE school_name = 'Lincoln Elementary' 
                    AND is_active = true
                """))
            
            # Test 3: Teachers by subject
            with self.measure_time("Teachers by Subject"):
                session.execute(text("""
                    SELECT id, username, email 
                    FROM users 
                    WHERE role = 'teacher' 
                    AND subjects_taught ? 'Mathematics'
                    AND is_active = true
                """))
            
            # Test 4: Recent user activity
            with self.measure_time("Recent User Activity"):
                session.execute(text("""
                    SELECT id, username, last_login 
                    FROM users 
                    WHERE last_login >= NOW() - INTERVAL '7 days'
                    AND is_active = true
                    ORDER BY last_login DESC
                    LIMIT 50
                """))
        finally:
            session.close()

    def test_content_queries(self):
        """Test educational content queries."""
        print("\n📚 Testing Content Queries...")
        
        session = self.Session()
        try:
            # Test 1: Content by subject and grade
            with self.measure_time("Content by Subject and Grade"):
                session.execute(text("""
                    SELECT id, title, description 
                    FROM educational_content 
                    WHERE subject = 'Science' 
                    AND grade_level = 7 
                    AND is_published = true
                    ORDER BY created_at DESC
                    LIMIT 20
                """))
            
            # Test 2: Full-text search
            with self.measure_time("Full-text Content Search"):
                session.execute(text("""
                    SELECT id, title, description 
                    FROM educational_content 
                    WHERE to_tsvector('english', 
                        COALESCE(title, '') || ' ' || 
                        COALESCE(description, '')
                    ) @@ plainto_tsquery('english', 'solar system planets')
                    AND is_published = true
                    LIMIT 10
                """))
            
            # Test 3: Content by difficulty and duration
            with self.measure_time("Content by Difficulty and Duration"):
                session.execute(text("""
                    SELECT id, title, difficulty_level, duration_minutes 
                    FROM educational_content 
                    WHERE difficulty_level IN ('beginner', 'intermediate')
                    AND duration_minutes BETWEEN 15 AND 45
                    AND is_published = true
                    ORDER BY duration_minutes ASC
                    LIMIT 25
                """))
        finally:
            session.close()

    def test_quiz_queries(self):
        """Test quiz and assessment queries."""
        print("\n🎯 Testing Quiz Queries...")
        
        session = self.Session()
        try:
            # Test 1: Quiz leaderboard
            with self.measure_time("Quiz Leaderboard"):
                session.execute(text("""
                    SELECT u.username, qa.score, qa.time_taken
                    FROM quiz_attempts qa
                    JOIN users u ON qa.user_id = u.id
                    WHERE qa.quiz_id = 1
                    AND qa.completed_at IS NOT NULL
                    ORDER BY qa.score DESC, qa.time_taken ASC
                    LIMIT 20
                """))
            
            # Test 2: User quiz history
            with self.measure_time("User Quiz History"):
                session.execute(text("""
                    SELECT qa.quiz_id, q.title, qa.score, qa.completed_at
                    FROM quiz_attempts qa
                    JOIN quizzes q ON qa.quiz_id = q.id
                    WHERE qa.user_id = 1
                    AND qa.completed_at IS NOT NULL
                    ORDER BY qa.completed_at DESC
                    LIMIT 15
                """))
            
            # Test 3: Quiz attempts by date range
            with self.measure_time("Quiz Attempts by Date Range"):
                session.execute(text("""
                    SELECT DATE(completed_at) as date, COUNT(*) as attempts
                    FROM quiz_attempts
                    WHERE completed_at >= NOW() - INTERVAL '30 days'
                    AND completed_at IS NOT NULL
                    GROUP BY DATE(completed_at)
                    ORDER BY date DESC
                """))

    def test_progress_queries(self):
        """Test learning progress queries."""
        print("\n📈 Testing Progress Queries...")
        
        session = self.Session()
        try:
            # Test 1: User progress by content
            with self.measure_time("User Progress by Content"):
                session.execute(text("""
                    SELECT up.content_id, ec.title, up.completion_percentage, up.mastery_level
                    FROM user_progress up
                    JOIN educational_content ec ON up.content_id = ec.id
                    WHERE up.user_id = 1
                    ORDER BY up.last_interaction DESC
                    LIMIT 20
                """))
            
            # Test 2: Progress analytics by grade level
            with self.measure_time("Progress Analytics by Grade Level"):
                session.execute(text("""
                    SELECT ec.grade_level, 
                           AVG(up.completion_percentage) as avg_completion,
                           COUNT(DISTINCT up.user_id) as unique_users
                    FROM user_progress up
                    JOIN educational_content ec ON up.content_id = ec.id
                    WHERE up.completion_percentage > 0
                    GROUP BY ec.grade_level
                    ORDER BY ec.grade_level
                """))
            
            # Test 3: High achievers with streaks
            with self.measure_time("High Achievers with Streaks"):
                session.execute(text("""
                    SELECT u.username, up.current_streak, up.max_streak, up.mastery_level
                    FROM user_progress up
                    JOIN users u ON up.user_id = u.id
                    WHERE up.current_streak >= 5
                    AND up.mastery_level IS NOT NULL
                    ORDER BY up.current_streak DESC, up.max_streak DESC
                    LIMIT 25
                """))

    def test_dashboard_queries(self):
        """Test dashboard-specific queries."""
        print("\n📊 Testing Dashboard Queries...")
        
        session = self.Session()
        try:
            # Test 1: Class enrollment stats
            with self.measure_time("Class Enrollment Stats"):
                session.execute(text("""
                    SELECT c.name, c.subject, c.student_count, c.max_students
                    FROM classes c
                    WHERE c.is_active = true
                    AND c.start_date <= CURRENT_DATE
                    AND c.end_date >= CURRENT_DATE
                    ORDER BY c.student_count DESC
                    LIMIT 20
                """))
            
            # Test 2: Student progress leaderboard
            with self.measure_time("Student Progress Leaderboard"):
                session.execute(text("""
                    SELECT sp.student_id, u.username, sp.xp_points, sp.level, sp.rank_position
                    FROM student_progress sp
                    JOIN users u ON sp.student_id = u.id
                    WHERE sp.class_id = 1
                    ORDER BY sp.rank_position ASC
                    LIMIT 30
                """))
            
            # Test 3: Recent assignments and submissions
            with self.measure_time("Recent Assignments and Submissions"):
                session.execute(text("""
                    SELECT a.title, a.due_date, COUNT(s.id) as submissions
                    FROM assignments a
                    LEFT JOIN submissions s ON a.id = s.assignment_id
                    WHERE a.created_at >= NOW() - INTERVAL '14 days'
                    AND a.is_published = true
                    GROUP BY a.id, a.title, a.due_date
                    ORDER BY a.due_date ASC
                    LIMIT 15
                """))

    def test_complex_analytical_queries(self):
        """Test complex analytical queries."""
        print("\n🔬 Testing Complex Analytical Queries...")
        
        session = self.Session()
        try:
            # Test 1: Student performance analysis
            with self.measure_time("Student Performance Analysis"):
                session.execute(text("""
                    SELECT 
                        u.grade_level,
                        COUNT(DISTINCT u.id) as total_students,
                        AVG(up.completion_percentage) as avg_completion,
                        AVG(qa.score) as avg_quiz_score,
                        COUNT(DISTINCT qa.id) as total_quiz_attempts
                    FROM users u
                    LEFT JOIN user_progress up ON u.id = up.user_id
                    LEFT JOIN quiz_attempts qa ON u.id = qa.user_id
                    WHERE u.role = 'student' AND u.is_active = true
                    GROUP BY u.grade_level
                    ORDER BY u.grade_level
                """))
            
            # Test 2: Content engagement metrics
            with self.measure_time("Content Engagement Metrics"):
                session.execute(text("""
                    SELECT 
                        ec.subject,
                        ec.grade_level,
                        COUNT(DISTINCT up.user_id) as unique_users,
                        AVG(up.completion_percentage) as avg_completion,
                        COUNT(DISTINCT qa.id) as quiz_attempts,
                        AVG(qa.score) as avg_quiz_score
                    FROM educational_content ec
                    LEFT JOIN user_progress up ON ec.id = up.content_id
                    LEFT JOIN quizzes q ON ec.id = q.content_id
                    LEFT JOIN quiz_attempts qa ON q.id = qa.quiz_id
                    WHERE ec.is_published = true
                    GROUP BY ec.subject, ec.grade_level
                    HAVING COUNT(DISTINCT up.user_id) > 0
                    ORDER BY COUNT(DISTINCT up.user_id) DESC
                    LIMIT 20
                """))

    def test_connection_pool_performance(self):
        """Test connection pool performance under load."""
        print("\n🔄 Testing Connection Pool Performance...")
        
        def execute_simple_query():
            """Execute a simple query to test connection pooling."""
            session = self.Session()
        try:
                session.execute(text("SELECT 1"))
        
        # Test rapid sequential connections
        start_time = time.perf_counter()
        for i in range(50):
            execute_simple_query()
        end_time = time.perf_counter()
        
        total_time = (end_time - start_time) * 1000
        avg_time = total_time / 50
        
        self.results.append({
            'query': 'Connection Pool (50 sequential)',
            'time_ms': avg_time,
            'passed': avg_time < self.target_time_ms
        })
        
        status = "✅ PASS" if avg_time < self.target_time_ms else "❌ FAIL"
        print(f"{status} Connection Pool (50 sequential): {avg_time:.2f}ms avg")

    def check_index_usage(self):
        """Check if indexes are being used effectively."""
        print("\n📋 Checking Index Usage...")
        
        session = self.Session()
        try:
            # Check most used indexes
            result = session.execute(text("""
                SELECT 
                    schemaname,
                    relname as table_name,
                    indexrelname as index_name,
                    idx_scan as scans,
                    idx_tup_read as tuples_read,
                    idx_tup_fetch as tuples_fetched
                FROM pg_stat_user_indexes
                WHERE idx_scan > 0
                ORDER BY idx_scan DESC
                LIMIT 10
            """))
            
            print("\nTop 10 Most Used Indexes:")
            for row in result:
                print(f"  {row.table_name}.{row.index_name}: {row.scans} scans")
            
            # Check for unused indexes
            unused = session.execute(text("""
                SELECT 
                    schemaname,
                    relname as table_name,
                    indexrelname as index_name,
                    pg_size_pretty(pg_relation_size(indexrelid)) as size
                FROM pg_stat_user_indexes
                WHERE idx_scan = 0
                AND indexrelname NOT LIKE '%_pkey'
                ORDER BY pg_relation_size(indexrelid) DESC
                LIMIT 5
            """))
            
            unused_count = 0
            print("\nUnused Indexes:")
            for row in unused:
                print(f"  {row.table_name}.{row.index_name}: {row.size}")
                unused_count += 1
            
            if unused_count == 0:
                print("  No unused indexes found - excellent!")

    def generate_report(self):
        """Generate a comprehensive performance report."""
        print("\n" + "="*60)
        print("📊 DATABASE PERFORMANCE REPORT")
        print("="*60)
        
        if not self.results:
            print("❌ No test results available")
            return
        
        # Calculate statistics
        times = [r['time_ms'] for r in self.results]
        passed_tests = [r for r in self.results if r['passed']]
        failed_tests = [r for r in self.results if not r['passed']]
        
        print(f"\n📈 Performance Statistics:")
        print(f"   Total Tests: {len(self.results)}")
        print(f"   Passed: {len(passed_tests)} ✅")
        print(f"   Failed: {len(failed_tests)} ❌")
        print(f"   Success Rate: {len(passed_tests)/len(self.results)*100:.1f}%")
        print(f"   Average Time: {statistics.mean(times):.2f}ms")
        print(f"   Median Time: {statistics.median(times):.2f}ms")
        print(f"   Max Time: {max(times):.2f}ms")
        print(f"   Min Time: {min(times):.2f}ms")
        print(f"   Target: < {self.target_time_ms}ms")
        
        if failed_tests:
            print(f"\n❌ Failed Tests (>{self.target_time_ms}ms):")
            for test in failed_tests:
                print(f"   • {test['query']}: {test['time_ms']:.2f}ms")
        
        # Overall assessment
        success_rate = len(passed_tests) / len(self.results) * 100
        avg_time = statistics.mean(times)
        
        print(f"\n🎯 Overall Assessment:")
        if success_rate >= 95 and avg_time < self.target_time_ms:
            print("   ✅ EXCELLENT - Database is highly optimized!")
        elif success_rate >= 85 and avg_time < self.target_time_ms * 1.5:
            print("   ✅ GOOD - Database performance is acceptable")
        elif success_rate >= 70:
            print("   ⚠️  FAIR - Some optimization needed")
        else:
            print("   ❌ POOR - Significant optimization required")
        
        # Recommendations
        print(f"\n💡 Recommendations:")
        if avg_time > self.target_time_ms:
            print("   • Consider adding more specific indexes")
            print("   • Review query patterns and optimize frequent queries")
        if len(failed_tests) > 0:
            print("   • Focus on optimizing the slowest queries first")
        if success_rate < 90:
            print("   • Run ANALYZE on tables to update query planner statistics")
            print("   • Consider increasing shared_buffers in PostgreSQL config")
        
        print("\n✅ Performance testing completed!")

    def run_all_tests(self):
        """Run the complete performance test suite."""
        print("🚀 Starting Database Performance Tests...")
        print(f"Target: All queries < {self.target_time_ms}ms")
        
        try:
            self.test_user_queries()
            self.test_content_queries()
            self.test_quiz_queries()
            self.test_progress_queries()
            self.test_dashboard_queries()
            self.test_complex_analytical_queries()
            self.test_connection_pool_performance()
            self.check_index_usage()
            self.generate_report()
            
        except Exception as e:
            print(f"❌ Test execution failed: {e}")
            return False
        
        return True

def main():
    """Main execution function."""
    tester = DatabasePerformanceTester()
    success = tester.run_all_tests()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()