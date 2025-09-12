#!/usr/bin/env python3
"""
Database Performance Validation Script
Validates that all database queries execute in < 50ms as required
"""

import asyncio
import time
import asyncpg
import os
import statistics
from typing import List, Dict, Any, Tuple
from datetime import datetime
import json

class PerformanceValidator:
    """Validates database performance after optimization"""
    
    def __init__(self):
        self.db_config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': int(os.getenv('DB_PORT', 5432)),
            'user': os.getenv('DB_USER', 'eduplatform'),
            'password': os.getenv('DB_PASSWORD', 'eduplatform2024'),
            'database': os.getenv('DB_NAME', 'educational_platform_dev')
        }
        self.results: List[Dict[str, Any]] = []
        
    async def connect(self) -> asyncpg.Connection:
        """Create database connection"""
        return await asyncpg.connect(**self.db_config)
    
    async def measure_query_performance(self, conn: asyncpg.Connection, 
                                      query_name: str, query: str, 
                                      params: tuple = (), iterations: int = 10) -> Dict[str, Any]:
        """Measure query performance over multiple iterations"""
        times = []
        
        print(f"Testing {query_name}...")
        
        for i in range(iterations):
            start_time = time.time()
            try:
                if params:
                    result = await conn.fetch(query, *params)
                else:
                    result = await conn.fetch(query)
                
                execution_time = (time.time() - start_time) * 1000  # Convert to ms
                times.append(execution_time)
                
            except Exception as e:
                print(f"  ❌ Error in iteration {i+1}: {e}")
                continue
        
        if not times:
            return {
                'query_name': query_name,
                'status': 'FAILED',
                'error': 'All iterations failed'
            }
        
        avg_time = statistics.mean(times)
        max_time = max(times)
        min_time = min(times)
        
        status = 'PASS' if avg_time < 50 else 'FAIL'
        status_icon = '✅' if status == 'PASS' else '❌'
        
        result = {
            'query_name': query_name,
            'status': status,
            'avg_time_ms': round(avg_time, 3),
            'max_time_ms': round(max_time, 3),
            'min_time_ms': round(min_time, 3),
            'iterations': len(times),
            'target_ms': 50
        }
        
        print(f"  {status_icon} {query_name}: {avg_time:.3f}ms avg (target: <50ms)")
        return result
    
    async def run_dashboard_queries(self, conn: asyncpg.Connection):
        """Test dashboard-related queries"""
        
        # Get sample IDs for testing
        teacher_id = await conn.fetchval(
            "SELECT id FROM dashboard_users WHERE role = 'teacher' LIMIT 1"
        )
        student_id = await conn.fetchval(
            "SELECT id FROM dashboard_users WHERE role = 'student' LIMIT 1"
        )
        
        test_queries = [
            # Teacher Dashboard Queries
            {
                'name': 'Teacher Classes Query',
                'query': '''
                    SELECT c.id, c.name, c.subject, c.grade_level,
                           COUNT(DISTINCT cs.student_id) as student_count
                    FROM classes c
                    LEFT JOIN class_students cs ON c.id = cs.class_id
                    WHERE c.teacher_id = $1 AND c.is_active = true
                    GROUP BY c.id
                ''',
                'params': (teacher_id,) if teacher_id else ()
            },
            
            {
                'name': 'Teacher Assignments Query',
                'query': '''
                    SELECT a.id, a.title, a.type, a.due_date, a.class_id,
                           COUNT(s.id) as submissions,
                           COUNT(CASE WHEN s.status = 'graded' THEN 1 END) as graded
                    FROM assignments a
                    LEFT JOIN submissions s ON a.id = s.assignment_id
                    WHERE a.teacher_id = $1 
                        AND a.due_date >= CURRENT_DATE - INTERVAL '7 days'
                    GROUP BY a.id
                    ORDER BY a.due_date
                    LIMIT 10
                ''',
                'params': (teacher_id,) if teacher_id else ()
            },
            
            # Student Dashboard Queries
            {
                'name': 'Student Assignments Query',
                'query': '''
                    SELECT a.id, a.title, a.subject, a.due_date,
                           s.status, s.grade, s.progress
                    FROM assignments a
                    LEFT JOIN submissions s ON a.id = s.assignment_id AND s.student_id = $1
                    JOIN classes c ON a.class_id = c.id
                    JOIN class_students cs ON c.id = cs.class_id
                    WHERE cs.student_id = $1
                        AND a.due_date >= CURRENT_DATE
                    ORDER BY a.due_date
                    LIMIT 10
                ''',
                'params': (student_id,) if student_id else ()
            },
            
            {
                'name': 'Student Progress Query',
                'query': '''
                    SELECT u.id, u.username, u.email,
                           sp.xp_points, sp.level, sp.streak_days,
                           sp.total_badges, sp.rank_position
                    FROM dashboard_users u
                    LEFT JOIN student_progress sp ON u.id = sp.student_id
                    WHERE u.id = $1
                ''',
                'params': (student_id,) if student_id else ()
            },
            
            # Leaderboard Query
            {
                'name': 'Leaderboard Query',
                'query': '''
                    SELECT u.username, sp.xp_points, sp.level, sp.rank_position
                    FROM student_progress sp
                    JOIN dashboard_users u ON sp.student_id = u.id
                    WHERE sp.rank_position <= 10
                    ORDER BY sp.rank_position
                '''
            },
            
            # User Authentication Query
            {
                'name': 'User Authentication Query',
                'query': '''
                    SELECT id, username, email, role, is_active
                    FROM dashboard_users
                    WHERE username = $1 AND is_active = true
                ''',
                'params': ('test_user',)
            },
            
            # Class Enrollment Query
            {
                'name': 'Class Enrollment Query',
                'query': '''
                    SELECT c.id, c.name, c.subject, c.grade_level,
                           t.username as teacher_name
                    FROM classes c
                    JOIN class_students cs ON c.id = cs.class_id
                    JOIN dashboard_users t ON c.teacher_id = t.id
                    WHERE cs.student_id = $1 AND c.is_active = true
                ''',
                'params': (student_id,) if student_id else ()
            },
            
            # Recent Activity Query
            {
                'name': 'Recent Activity Query',
                'query': '''
                    SELECT type, description, created_at, xp_earned
                    FROM student_activity
                    WHERE student_id = $1
                    ORDER BY created_at DESC
                    LIMIT 10
                ''',
                'params': (student_id,) if student_id else ()
            }
        ]
        
        # Run each test query
        for query_test in test_queries:
            if not query_test.get('params') and '$1' in query_test['query']:
                # Skip queries that need parameters but don't have valid IDs
                print(f"  ⚠️ Skipping {query_test['name']} - no test data available")
                continue
                
            result = await self.measure_query_performance(
                conn, 
                query_test['name'],
                query_test['query'],
                query_test.get('params', ())
            )
            self.results.append(result)
    
    async def run_system_queries(self, conn: asyncpg.Connection):
        """Test system and admin queries"""
        
        system_queries = [
            {
                'name': 'System Statistics Query',
                'query': '''
                    SELECT 
                        (SELECT COUNT(*) FROM dashboard_users WHERE is_active = true) as total_users,
                        (SELECT COUNT(*) FROM classes WHERE is_active = true) as total_classes,
                        (SELECT COUNT(*) FROM assignments) as total_assignments
                '''
            },
            
            {
                'name': 'API Logs Query',
                'query': '''
                    SELECT COUNT(*) as total_calls,
                           AVG(response_time) as avg_response_time
                    FROM api_logs
                    WHERE timestamp >= CURRENT_TIMESTAMP - INTERVAL '24 hours'
                '''
            },
            
            {
                'name': 'System Events Query',
                'query': '''
                    SELECT id, event_type, message, severity, created_at
                    FROM system_events
                    ORDER BY created_at DESC
                    LIMIT 10
                '''
            }
        ]
        
        for query_test in system_queries:
            result = await self.measure_query_performance(
                conn,
                query_test['name'],
                query_test['query']
            )
            self.results.append(result)
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all performance validation tests"""
        print("🚀 Starting Database Performance Validation")
        print("=" * 60)
        
        start_time = time.time()
        
        try:
            conn = await self.connect()
            print("✅ Database connection established")
            
            # Test dashboard queries
            print("\n📊 Testing Dashboard Queries...")
            await self.run_dashboard_queries(conn)
            
            # Test system queries
            print("\n🔧 Testing System Queries...")
            await self.run_system_queries(conn)
            
            await conn.close()
            print("✅ Database connection closed")
            
        except Exception as e:
            print(f"❌ Database connection failed: {e}")
            return {
                'status': 'FAILED',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
        
        total_time = time.time() - start_time
        
        # Analyze results
        passed_tests = [r for r in self.results if r.get('status') == 'PASS']
        failed_tests = [r for r in self.results if r.get('status') == 'FAIL']
        
        # Calculate statistics
        all_times = [r['avg_time_ms'] for r in self.results if 'avg_time_ms' in r]
        overall_avg = statistics.mean(all_times) if all_times else 0
        
        summary = {
            'status': 'PASSED' if len(failed_tests) == 0 else 'FAILED',
            'total_tests': len(self.results),
            'passed_tests': len(passed_tests),
            'failed_tests': len(failed_tests),
            'overall_avg_time_ms': round(overall_avg, 3),
            'target_time_ms': 50,
            'total_duration_s': round(total_time, 2),
            'timestamp': datetime.now().isoformat(),
            'detailed_results': self.results
        }
        
        print("\n" + "=" * 60)
        print("📈 PERFORMANCE VALIDATION RESULTS")
        print("=" * 60)
        print(f"Total Tests: {summary['total_tests']}")
        print(f"Passed: {summary['passed_tests']} ✅")
        print(f"Failed: {summary['failed_tests']} {'❌' if summary['failed_tests'] > 0 else '✅'}")
        print(f"Overall Average: {summary['overall_avg_time_ms']}ms (target: <{summary['target_time_ms']}ms)")
        print(f"Test Duration: {summary['total_duration_s']}s")
        
        if summary['status'] == 'PASSED':
            print("\n🎉 ALL TESTS PASSED! Database is optimized for < 50ms queries.")
        else:
            print(f"\n⚠️ {summary['failed_tests']} tests failed. Review failed queries for further optimization.")
            
        return summary

    def save_results(self, results: Dict[str, Any], filename: str = None):
        """Save results to JSON file"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"performance_validation_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"📄 Results saved to: {filename}")

async def main():
    """Main function to run performance validation"""
    validator = PerformanceValidator()
    results = await validator.run_all_tests()
    
    # Save results
    validator.save_results(results)
    
    # Return exit code based on results
    return 0 if results['status'] == 'PASSED' else 1

if __name__ == "__main__":
    import sys
    exit_code = asyncio.run(main())
    sys.exit(exit_code)