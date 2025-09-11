#!/usr/bin/env python3
"""
Simple Database Performance Test
Tests key queries to validate optimization effectiveness
Target: All queries < 50ms
"""

import time
import statistics
from sqlalchemy import create_engine, text

# Database connection
DATABASE_URL = "postgresql://grayghostdata@localhost/educational_platform"

class SimplePerformanceTester:
    """Simple database performance tester."""
    
    def __init__(self):
        """Initialize the tester."""
        self.engine = create_engine(DATABASE_URL)
        self.results = []
        self.target_time_ms = 50.0
    
    def measure_query(self, query_name: str, query: str):
        """Measure query execution time."""
        start_time = time.perf_counter()
        
        with self.engine.connect() as conn:
            conn.execute(text(query))
        
        end_time = time.perf_counter()
        execution_time = (end_time - start_time) * 1000  # Convert to milliseconds
        
        self.results.append({
            'query': query_name,
            'time_ms': execution_time,
            'passed': execution_time < self.target_time_ms
        })
        
        status = "✅ PASS" if execution_time < self.target_time_ms else "❌ FAIL"
        print(f"{status} {query_name}: {execution_time:.2f}ms")
        
        return execution_time < self.target_time_ms
    
    def run_tests(self):
        """Run all performance tests."""
        print("🚀 Starting Database Performance Tests...")
        print(f"Target: All queries < {self.target_time_ms}ms\n")
        
        # Test 1: User authentication (most critical)
        self.measure_query(
            "User Authentication by Email",
            """
            SELECT id, username, password_hash, role 
            FROM users 
            WHERE email = 'test@example.com' AND is_active = true
            LIMIT 1
            """
        )
        
        # Test 2: Active users count
        self.measure_query(
            "Active Users Count",
            """
            SELECT COUNT(*) 
            FROM users 
            WHERE is_active = true
            """
        )
        
        # Test 3: Content search by subject/grade
        self.measure_query(
            "Content by Subject and Grade",
            """
            SELECT id, title, description 
            FROM educational_content 
            WHERE subject = 'Science' 
            AND grade_level = 7 
            AND is_published = true
            ORDER BY created_at DESC
            LIMIT 20
            """
        )
        
        # Test 4: Quiz leaderboard query
        self.measure_query(
            "Quiz Leaderboard",
            """
            SELECT qa.user_id, qa.score, qa.time_taken
            FROM quiz_attempts qa
            WHERE qa.quiz_id = 1
            AND qa.completed_at IS NOT NULL
            ORDER BY qa.score DESC, qa.time_taken ASC
            LIMIT 20
            """
        )
        
        # Test 5: User progress tracking
        self.measure_query(
            "User Progress Tracking",
            """
            SELECT content_id, completion_percentage, mastery_level
            FROM user_progress 
            WHERE user_id = 1
            ORDER BY last_interaction DESC
            LIMIT 20
            """
        )
        
        # Test 6: Dashboard class enrollment
        self.measure_query(
            "Class Enrollment Stats",
            """
            SELECT name, subject, student_count, max_students
            FROM classes 
            WHERE is_active = true
            ORDER BY student_count DESC
            LIMIT 20
            """
        )
        
        # Test 7: Complex analytical query
        self.measure_query(
            "Student Performance Analytics",
            """
            SELECT 
                grade_level,
                COUNT(*) as total_students,
                AVG(CASE WHEN up.completion_percentage IS NOT NULL 
                    THEN up.completion_percentage ELSE 0 END) as avg_completion
            FROM users u
            LEFT JOIN user_progress up ON u.id = up.user_id
            WHERE u.role = 'student' AND u.is_active = true
            GROUP BY u.grade_level
            ORDER BY u.grade_level
            """
        )
        
        # Test 8: Connection pool stress test
        print("\n🔄 Testing Connection Pool Performance...")
        connection_times = []
        
        for i in range(20):
            start_time = time.perf_counter()
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            end_time = time.perf_counter()
            connection_times.append((end_time - start_time) * 1000)
        
        avg_connection_time = statistics.mean(connection_times)
        max_connection_time = max(connection_times)
        
        self.results.append({
            'query': 'Connection Pool (20 connections)',
            'time_ms': avg_connection_time,
            'passed': avg_connection_time < self.target_time_ms
        })
        
        status = "✅ PASS" if avg_connection_time < self.target_time_ms else "❌ FAIL"
        print(f"{status} Connection Pool (avg): {avg_connection_time:.2f}ms")
        print(f"   Max connection time: {max_connection_time:.2f}ms")
        
        # Test 9: Index usage check
        print("\n📋 Checking Index Usage...")
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text("""
                    SELECT 
                        relname as table_name,
                        indexrelname as index_name,
                        idx_scan as scans
                    FROM pg_stat_user_indexes
                    WHERE idx_scan > 0
                    ORDER BY idx_scan DESC
                    LIMIT 5
                """))
                
                print("Top 5 Most Used Indexes:")
                for row in result:
                    print(f"  {row.table_name}.{row.index_name}: {row.scans} scans")
        except Exception as e:
            print(f"⚠️  Could not check index usage: {e}")
        
        self.generate_report()
    
    def generate_report(self):
        """Generate performance report."""
        print("\n" + "="*50)
        print("📊 PERFORMANCE REPORT")
        print("="*50)
        
        if not self.results:
            print("❌ No test results available")
            return
        
        # Calculate statistics
        times = [r['time_ms'] for r in self.results]
        passed_tests = [r for r in self.results if r['passed']]
        failed_tests = [r for r in self.results if not r['passed']]
        
        print(f"\n📈 Results:")
        print(f"   Total Tests: {len(self.results)}")
        print(f"   Passed: {len(passed_tests)} ✅")
        print(f"   Failed: {len(failed_tests)} ❌")
        print(f"   Success Rate: {len(passed_tests)/len(self.results)*100:.1f}%")
        print(f"   Average Time: {statistics.mean(times):.2f}ms")
        print(f"   Maximum Time: {max(times):.2f}ms")
        print(f"   Target: < {self.target_time_ms}ms")
        
        if failed_tests:
            print(f"\n❌ Tests Exceeding {self.target_time_ms}ms:")
            for test in failed_tests:
                print(f"   • {test['query']}: {test['time_ms']:.2f}ms")
        
        # Overall assessment
        success_rate = len(passed_tests) / len(self.results) * 100
        avg_time = statistics.mean(times)
        
        print(f"\n🎯 Assessment:")
        if success_rate >= 95 and avg_time < self.target_time_ms:
            print("   ✅ EXCELLENT - Database is highly optimized!")
        elif success_rate >= 85:
            print("   ✅ GOOD - Performance is acceptable")
        elif success_rate >= 70:
            print("   ⚠️  FAIR - Some optimization needed")
        else:
            print("   ❌ POOR - Significant optimization required")
        
        print("\n💡 Optimization Status:")
        print("   • Indexes: Applied comprehensive index optimization")
        print("   • Connection Pool: Increased to 20 + 40 overflow")
        print("   • Pool Timeout: Set to 30 seconds")
        print("   • Pool Recycle: Set to 1 hour")
        
        print("\n✅ Performance testing completed!")

def main():
    """Main execution function."""
    try:
        tester = SimplePerformanceTester()
        tester.run_tests()
    except Exception as e:
        print(f"❌ Test execution failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    main()