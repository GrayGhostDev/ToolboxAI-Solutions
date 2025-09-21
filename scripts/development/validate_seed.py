#!/usr/bin/env python3
"""
Database Seed Validation Script

Verifies that all seeded data is properly created with correct relationships
and data integrity.
"""

import asyncio
import sys
import os
from pathlib import Path
from typing import Dict, List, Any, Tuple
from datetime import datetime
import json

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from core.database import db_manager
from sqlalchemy import text


class SeedValidator:
    """Validate seeded database data"""
    
    def __init__(self):
        self.errors = []
        self.warnings = []
        self.stats = {}
        
    async def validate_table_counts(self) -> Dict[str, int]:
        """Get row counts for all tables"""
        counts = {}
        
        async with db_manager.get_connection() as conn:
            # Get all tables
            tables = await conn.fetch("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                    AND table_type = 'BASE TABLE'
                    AND table_name NOT IN ('alembic_version')
                ORDER BY table_name;
            """)
            
            for table in tables:
                table_name = table['table_name']
                count = await conn.fetchval(f"SELECT COUNT(*) FROM {table_name}")
                counts[table_name] = count
                
        self.stats['table_counts'] = counts
        return counts
    
    async def validate_users(self) -> Tuple[bool, List[str]]:
        """Validate user data integrity"""
        issues = []
        
        async with db_manager.get_connection() as conn:
            # Check for required users
            required_users = ['admin', 'teacher1', 'teacher2', 'student1', 'student2', 'parent1']
            
            for username in required_users:
                exists = await conn.fetchval(
                    "SELECT EXISTS(SELECT 1 FROM users WHERE username = $1)",
                    username
                )
                if not exists:
                    issues.append(f"Missing required user: {username}")
            
            # Check for duplicate emails
            duplicates = await conn.fetch("""
                SELECT email, COUNT(*) as count
                FROM users
                GROUP BY email
                HAVING COUNT(*) > 1
            """)
            
            for dup in duplicates:
                issues.append(f"Duplicate email found: {dup['email']} ({dup['count']} times)")
            
            # Check for invalid roles (handle both uppercase and lowercase)
            invalid_roles = await conn.fetch("""
                SELECT username, role
                FROM users
                WHERE UPPER(role::text) NOT IN ('ADMIN', 'TEACHER', 'STUDENT', 'PARENT')
            """)
            
            for user in invalid_roles:
                issues.append(f"Invalid role for user {user['username']}: {user['role']}")
            
            # Get user statistics
            user_stats = await conn.fetchrow("""
                SELECT 
                    COUNT(*) as total_users,
                    COUNT(CASE WHEN role = 'admin' THEN 1 END) as admins,
                    COUNT(CASE WHEN role = 'teacher' THEN 1 END) as teachers,
                    COUNT(CASE WHEN role = 'student' THEN 1 END) as students,
                    COUNT(CASE WHEN role = 'parent' THEN 1 END) as parents,
                    COUNT(CASE WHEN is_verified = true THEN 1 END) as verified,
                    COUNT(CASE WHEN is_active = true THEN 1 END) as active
                FROM users
            """)
            
            self.stats['users'] = dict(user_stats)
            
        return len(issues) == 0, issues
    
    async def validate_courses(self) -> Tuple[bool, List[str]]:
        """Validate course data integrity"""
        issues = []
        
        async with db_manager.get_connection() as conn:
            # Check for courses without lessons
            courses_without_lessons = await conn.fetch("""
                SELECT c.title, c.code
                FROM courses c
                LEFT JOIN lessons l ON c.id = l.course_id
                WHERE l.id IS NULL
            """)
            
            for course in courses_without_lessons:
                self.warnings.append(f"Course '{course['title']}' ({course['code']}) has no lessons")
            
            # Check for duplicate course codes
            duplicate_codes = await conn.fetch("""
                SELECT code, COUNT(*) as count
                FROM courses
                GROUP BY code
                HAVING COUNT(*) > 1
            """)
            
            for dup in duplicate_codes:
                issues.append(f"Duplicate course code: {dup['code']} ({dup['count']} times)")
            
            # Check grade levels
            invalid_grades = await conn.fetch("""
                SELECT title, grade_level
                FROM courses
                WHERE grade_level < 1 OR grade_level > 12
            """)
            
            for course in invalid_grades:
                issues.append(f"Invalid grade level for course '{course['title']}': {course['grade_level']}")
            
            # Get course statistics
            course_stats = await conn.fetchrow("""
                SELECT 
                    COUNT(*) as total_courses,
                    COUNT(DISTINCT subject) as subjects,
                    MIN(grade_level) as min_grade,
                    MAX(grade_level) as max_grade,
                    AVG(COALESCE(max_students, 30)) as avg_max_students
                FROM courses
            """)
            
            self.stats['courses'] = dict(course_stats)
            
        return len(issues) == 0, issues
    
    async def validate_lessons(self) -> Tuple[bool, List[str]]:
        """Validate lesson data integrity"""
        issues = []
        
        async with db_manager.get_connection() as conn:
            # Check for orphaned lessons
            orphaned = await conn.fetch("""
                SELECT l.title, l.id
                FROM lessons l
                LEFT JOIN courses c ON l.course_id = c.id
                WHERE c.id IS NULL
            """)
            
            for lesson in orphaned:
                issues.append(f"Orphaned lesson '{lesson['title']}' with no course")
            
            # Check for duplicate order indexes within courses
            duplicate_orders = await conn.fetch("""
                SELECT course_id, order_index, COUNT(*) as count
                FROM lessons
                GROUP BY course_id, order_index
                HAVING COUNT(*) > 1
            """)
            
            for dup in duplicate_orders:
                issues.append(f"Duplicate order_index {dup['order_index']} in course {dup['course_id']}")
            
            # Get lesson statistics
            lesson_stats = await conn.fetchrow("""
                SELECT 
                    COUNT(*) as total_lessons,
                    COUNT(CASE WHEN is_published = true THEN 1 END) as published,
                    COUNT(CASE WHEN roblox_place_id IS NOT NULL THEN 1 END) as with_roblox,
                    AVG(estimated_duration) as avg_duration
                FROM lessons
            """)
            
            self.stats['lessons'] = dict(lesson_stats)
            
        return len(issues) == 0, issues
    
    async def validate_content(self) -> Tuple[bool, List[str]]:
        """Validate educational content integrity"""
        issues = []
        
        async with db_manager.get_connection() as conn:
            # Check for content without lessons
            orphaned = await conn.fetch("""
                SELECT c.title, c.id
                FROM content c
                LEFT JOIN lessons l ON c.lesson_id = l.id
                WHERE l.id IS NULL
            """)
            
            for content in orphaned:
                issues.append(f"Orphaned content '{content['title']}' with no lesson")
            
            # Check for invalid content status
            invalid_status = await conn.fetch("""
                SELECT title, status
                FROM content
                WHERE status NOT IN ('draft', 'pending', 'approved', 'rejected', 'archived')
            """)
            
            for content in invalid_status:
                issues.append(f"Invalid status for content '{content['title']}': {content['status']}")
            
            # Get content statistics
            content_stats = await conn.fetchrow("""
                SELECT 
                    COUNT(*) as total_content,
                    COUNT(DISTINCT content_type) as content_types,
                    COUNT(CASE WHEN ai_generated = true THEN 1 END) as ai_generated,
                    COUNT(CASE WHEN status = 'approved' THEN 1 END) as approved,
                    AVG(quality_score) as avg_quality_score
                FROM content
            """)
            
            self.stats['content'] = dict(content_stats)
            
        return len(issues) == 0, issues
    
    async def validate_quizzes(self) -> Tuple[bool, List[str]]:
        """Validate quiz data integrity"""
        issues = []
        
        async with db_manager.get_connection() as conn:
            # Check for quizzes without questions
            quizzes_without_questions = await conn.fetch("""
                SELECT q.title, q.id
                FROM quizzes q
                LEFT JOIN quiz_questions qq ON q.id = qq.quiz_id
                WHERE qq.id IS NULL
            """)
            
            for quiz in quizzes_without_questions:
                self.warnings.append(f"Quiz '{quiz['title']}' has no questions")
            
            # Check passing scores
            invalid_scores = await conn.fetch("""
                SELECT title, passing_score
                FROM quizzes
                WHERE passing_score < 0 OR passing_score > 100
            """)
            
            for quiz in invalid_scores:
                issues.append(f"Invalid passing score for quiz '{quiz['title']}': {quiz['passing_score']}")
            
            # Get quiz statistics
            quiz_stats = await conn.fetchrow("""
                SELECT 
                    COUNT(DISTINCT q.id) as total_quizzes,
                    COUNT(qq.id) as total_questions,
                    AVG(q.passing_score) as avg_passing_score,
                    AVG(qq.points) as avg_points_per_question
                FROM quizzes q
                LEFT JOIN quiz_questions qq ON q.id = qq.quiz_id
            """)
            
            self.stats['quizzes'] = dict(quiz_stats)
            
        return len(issues) == 0, issues
    
    async def validate_relationships(self) -> Tuple[bool, List[str]]:
        """Validate foreign key relationships"""
        issues = []
        
        async with db_manager.get_connection() as conn:
            # Check enrollments reference valid users and courses
            invalid_enrollments = await conn.fetch("""
                SELECT e.id
                FROM enrollments e
                LEFT JOIN users u ON e.user_id = u.id
                LEFT JOIN courses c ON e.course_id = c.id
                WHERE u.id IS NULL OR c.id IS NULL
            """)
            
            if invalid_enrollments:
                issues.append(f"Found {len(invalid_enrollments)} enrollments with invalid references")
            
            # Check user progress references
            invalid_progress = await conn.fetch("""
                SELECT up.id
                FROM user_progress up
                LEFT JOIN users u ON up.user_id = u.id
                WHERE u.id IS NULL
            """)
            
            if invalid_progress:
                issues.append(f"Found {len(invalid_progress)} progress records with invalid user references")
            
            # Check quiz attempts reference valid users and quizzes
            invalid_attempts = await conn.fetch("""
                SELECT qa.id
                FROM quiz_attempts qa
                LEFT JOIN users u ON qa.user_id = u.id
                LEFT JOIN quizzes q ON qa.quiz_id = q.id
                WHERE u.id IS NULL OR q.id IS NULL
            """)
            
            if invalid_attempts:
                issues.append(f"Found {len(invalid_attempts)} quiz attempts with invalid references")
            
        return len(issues) == 0, issues
    
    async def generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive validation report"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'status': 'valid' if not self.errors else 'invalid',
            'statistics': self.stats,
            'errors': self.errors,
            'warnings': self.warnings
        }
        
        # Add summary
        report['summary'] = {
            'total_tables': len(self.stats.get('table_counts', {})),
            'populated_tables': sum(1 for count in self.stats.get('table_counts', {}).values() if count > 0),
            'total_errors': len(self.errors),
            'total_warnings': len(self.warnings)
        }
        
        return report


async def main():
    """Main validation function"""
    print("\n🔍 Database Seed Validation\n")
    print("Checking data integrity and relationships...\n")
    
    validator = SeedValidator()
    
    try:
        # Initialize database connection
        await db_manager.initialize()
        
        # Get table counts
        print("📊 Checking table counts...")
        counts = await validator.validate_table_counts()
        
        empty_tables = [table for table, count in counts.items() if count == 0]
        if empty_tables:
            print(f"   ⚠️  Empty tables: {', '.join(empty_tables)}")
        else:
            print(f"   ✅ All {len(counts)} tables have data")
        
        # Validate users
        print("\n👥 Validating users...")
        valid, issues = await validator.validate_users()
        if valid:
            print(f"   ✅ Users valid ({validator.stats['users']['total_users']} total)")
        else:
            validator.errors.extend(issues)
            for issue in issues:
                print(f"   ❌ {issue}")
        
        # Validate courses
        print("\n📚 Validating courses...")
        valid, issues = await validator.validate_courses()
        if valid:
            print(f"   ✅ Courses valid ({validator.stats['courses']['total_courses']} total)")
        else:
            validator.errors.extend(issues)
            for issue in issues:
                print(f"   ❌ {issue}")
        
        # Validate lessons
        print("\n📖 Validating lessons...")
        valid, issues = await validator.validate_lessons()
        if valid:
            print(f"   ✅ Lessons valid ({validator.stats['lessons']['total_lessons']} total)")
        else:
            validator.errors.extend(issues)
            for issue in issues:
                print(f"   ❌ {issue}")
        
        # Validate content
        print("\n📝 Validating content...")
        valid, issues = await validator.validate_content()
        if valid:
            print(f"   ✅ Content valid ({validator.stats['content']['total_content']} items)")
        else:
            validator.errors.extend(issues)
            for issue in issues:
                print(f"   ❌ {issue}")
        
        # Validate quizzes
        print("\n❓ Validating quizzes...")
        valid, issues = await validator.validate_quizzes()
        if valid:
            print(f"   ✅ Quizzes valid ({validator.stats['quizzes']['total_quizzes']} total)")
        else:
            validator.errors.extend(issues)
            for issue in issues:
                print(f"   ❌ {issue}")
        
        # Validate relationships
        print("\n🔗 Validating relationships...")
        valid, issues = await validator.validate_relationships()
        if valid:
            print("   ✅ All foreign key relationships valid")
        else:
            validator.errors.extend(issues)
            for issue in issues:
                print(f"   ❌ {issue}")
        
        # Generate report
        report = await validator.generate_report()
        
        # Print summary
        print("\n" + "="*50)
        print("📋 VALIDATION SUMMARY")
        print("="*50)
        
        if not validator.errors:
            print("\n✅ Database seed validation PASSED!")
            print(f"   - {report['summary']['populated_tables']} tables populated")
            print(f"   - {validator.stats['users']['total_users']} users")
            print(f"   - {validator.stats['courses']['total_courses']} courses")
            print(f"   - {validator.stats['lessons']['total_lessons']} lessons")
            print(f"   - {validator.stats['content']['total_content']} content items")
            print(f"   - {validator.stats['quizzes']['total_quizzes']} quizzes")
        else:
            print(f"\n❌ Database seed validation FAILED!")
            print(f"   - {len(validator.errors)} errors found")
            print(f"   - {len(validator.warnings)} warnings")
        
        if validator.warnings:
            print(f"\n⚠️  Warnings ({len(validator.warnings)}):")
            for warning in validator.warnings[:5]:  # Show first 5 warnings
                print(f"   - {warning}")
            if len(validator.warnings) > 5:
                print(f"   ... and {len(validator.warnings) - 5} more")
        
        # Save report to file
        report_path = Path(__file__).parent / f"seed_validation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        print(f"\n📄 Full report saved to: {report_path}")
        
        # Exit with appropriate code
        sys.exit(0 if not validator.errors else 1)
        
    except Exception as e:
        print(f"\n❌ Validation failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    finally:
        await db_manager.close_all()


if __name__ == "__main__":
    asyncio.run(main())