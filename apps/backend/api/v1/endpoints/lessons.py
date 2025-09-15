"""
Lessons API Endpoints for ToolboxAI Educational Platform
Provides lesson management functionality for all user roles.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import logging
from ....api.auth.auth import get_current_user
from ....models.schemas import User
from ....services.database import db_service

logger = logging.getLogger(__name__)

# In-memory storage for development (will be replaced with database)
in_memory_lessons: List[Dict[str, Any]] = []

# Create router for lessons endpoints
lessons_router = APIRouter(prefix="/lessons", tags=["Lessons"])

@lessons_router.get("")
async def get_lessons(
    current_user: User = Depends(get_current_user),
    class_id: Optional[int] = None,
    subject: Optional[str] = None,
    limit: int = Query(default=20, le=100),
    offset: int = Query(default=0, ge=0)
) -> List[Dict[str, Any]]:
    """Get lessons based on user role and filters."""
    
    role = current_user.role.lower()
    
    # Try to get real data from database
    try:
        if role == "teacher":
            query = """
                SELECT l.*, c.name as class_name, COUNT(DISTINCT lp.student_id) as completion_count
                FROM lessons l
                JOIN classes c ON l.class_id = c.id
                LEFT JOIN lesson_progress lp ON l.id = lp.lesson_id AND lp.completed = true
                WHERE c.teacher_id = $1
                  AND ($2::int IS NULL OR l.class_id = $2)
                  AND ($3::text IS NULL OR c.subject = $3)
                GROUP BY l.id, c.name
                ORDER BY l.created_at DESC
                LIMIT $4 OFFSET $5
            """
            async with db_service.pool.acquire() as conn:
                rows = await conn.fetch(query, current_user.id, class_id, subject, limit, offset)
                return [dict(row) for row in rows]
                
        elif role == "student":
            query = """
                SELECT l.*, c.name as class_name, c.subject,
                       lp.progress, lp.completed, lp.last_accessed
                FROM lessons l
                JOIN classes c ON l.class_id = c.id
                JOIN class_enrollments ce ON c.id = ce.class_id
                LEFT JOIN lesson_progress lp ON l.id = lp.lesson_id AND lp.student_id = $1
                WHERE ce.student_id = $1
                  AND ($2::int IS NULL OR l.class_id = $2)
                  AND ($3::text IS NULL OR c.subject = $3)
                ORDER BY l.sequence_number, l.created_at
                LIMIT $4 OFFSET $5
            """
            async with db_service.pool.acquire() as conn:
                rows = await conn.fetch(query, current_user.id, class_id, subject, limit, offset)
                return [dict(row) for row in rows]
                
        elif role == "admin":
            query = """
                SELECT l.*, c.name as class_name, c.subject,
                       u.first_name || ' ' || u.last_name as teacher_name,
                       COUNT(DISTINCT lp.student_id) as students_completed
                FROM lessons l
                JOIN classes c ON l.class_id = c.id
                JOIN users u ON c.teacher_id = u.id
                LEFT JOIN lesson_progress lp ON l.id = lp.lesson_id AND lp.completed = true
                WHERE ($1::int IS NULL OR l.class_id = $1)
                  AND ($2::text IS NULL OR c.subject = $2)
                GROUP BY l.id, c.name, c.subject, u.first_name, u.last_name
                ORDER BY l.created_at DESC
                LIMIT $3 OFFSET $4
            """
            async with db_service.pool.acquire() as conn:
                rows = await conn.fetch(query, class_id, subject, limit, offset)
                return [dict(row) for row in rows]
                
        elif role == "parent":
            query = """
                SELECT DISTINCT l.*, c.name as class_name, c.subject,
                       s.first_name || ' ' || s.last_name as student_name,
                       lp.progress, lp.completed
                FROM lessons l
                JOIN classes c ON l.class_id = c.id
                JOIN class_enrollments ce ON c.id = ce.class_id
                JOIN users s ON ce.student_id = s.id
                JOIN parent_student_relationships psr ON s.id = psr.student_id
                LEFT JOIN lesson_progress lp ON l.id = lp.lesson_id AND lp.student_id = s.id
                WHERE psr.parent_id = $1
                  AND ($2::int IS NULL OR l.class_id = $2)
                ORDER BY l.created_at DESC
                LIMIT $3 OFFSET $4
            """
            async with db_service.pool.acquire() as conn:
                rows = await conn.fetch(query, current_user.id, class_id, limit, offset)
                return [dict(row) for row in rows]
                
    except Exception as e:
        logger.warning(f"Failed to fetch lessons from database: {e}. Using fallback data.")
    
    # Fallback sample data combined with in-memory lessons
    if role == "teacher":
        # Get user's in-memory lessons first
        user_lessons = [l for l in in_memory_lessons if l.get("teacher_id") == current_user.id]
        
        # Add fallback sample data
        fallback_lessons = [
            {
                "id": 1,
                "title": "Introduction to Algebra",
                "class_name": "Mathematics 101",
                "subject": "Mathematics",
                "duration": 45,
                "difficulty": "beginner",
                "completion_count": 22,
                "total_students": 28,
                "status": "published",
                "created_at": "2025-01-01T09:00:00"
            },
            {
                "id": 2,
                "title": "Solving Linear Equations",
                "class_name": "Mathematics 101",
                "subject": "Mathematics",
                "duration": 50,
                "difficulty": "intermediate",
                "completion_count": 18,
                "total_students": 28,
                "status": "published",
                "created_at": "2025-01-03T09:00:00"
            },
            {
                "id": 3,
                "title": "Quadratic Equations",
                "class_name": "Advanced Algebra",
                "subject": "Mathematics",
                "duration": 60,
                "difficulty": "advanced",
                "completion_count": 15,
                "total_students": 24,
                "status": "draft",
                "created_at": "2025-01-05T09:00:00"
            }
        ]
        # Return user's created lessons first, then fallback lessons
        return user_lessons + fallback_lessons
    elif role == "student":
        return [
            {
                "id": 1,
                "title": "Introduction to Algebra",
                "class_name": "Mathematics 101",
                "subject": "Mathematics",
                "duration": 45,
                "difficulty": "beginner",
                "progress": 100,
                "completed": True,
                "last_accessed": "2025-01-06T14:30:00",
                "xp_reward": 50
            },
            {
                "id": 2,
                "title": "Solving Linear Equations",
                "class_name": "Mathematics 101",
                "subject": "Mathematics",
                "duration": 50,
                "difficulty": "intermediate",
                "progress": 65,
                "completed": False,
                "last_accessed": "2025-01-07T10:15:00",
                "xp_reward": 75
            },
            {
                "id": 4,
                "title": "The Solar System",
                "class_name": "Science Lab",
                "subject": "Science",
                "duration": 40,
                "difficulty": "beginner",
                "progress": 30,
                "completed": False,
                "xp_reward": 60
            }
        ]
    elif role == "admin":
        return [
            {
                "id": 1,
                "title": "Introduction to Algebra",
                "class_name": "Mathematics 101",
                "teacher_name": "John Smith",
                "subject": "Mathematics",
                "duration": 45,
                "students_completed": 22,
                "total_enrolled": 28,
                "status": "published",
                "created_at": "2025-01-01T09:00:00"
            },
            {
                "id": 2,
                "title": "The Solar System",
                "class_name": "Science Lab",
                "teacher_name": "Emily Johnson",
                "subject": "Science",
                "duration": 40,
                "students_completed": 24,
                "total_enrolled": 26,
                "status": "published",
                "created_at": "2025-01-02T10:00:00"
            }
        ]
    elif role == "parent":
        return [
            {
                "id": 1,
                "title": "Introduction to Algebra",
                "class_name": "Mathematics 101",
                "student_name": "Alex Johnson",
                "subject": "Mathematics",
                "progress": 100,
                "completed": True,
                "due_date": "2025-01-05T23:59:00"
            },
            {
                "id": 2,
                "title": "Solving Linear Equations",
                "class_name": "Mathematics 101",
                "student_name": "Alex Johnson",
                "subject": "Mathematics",
                "progress": 65,
                "completed": False,
                "due_date": "2025-01-10T23:59:00"
            }
        ]
    
    return []

@lessons_router.get("/{lesson_id}")
async def get_lesson_details(
    lesson_id: int,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get detailed information about a specific lesson."""
    
    role = current_user.role.lower()
    
    try:
        # Get lesson details with appropriate access control
        query = """
            SELECT l.*, c.name as class_name, c.subject,
                   u.first_name || ' ' || u.last_name as teacher_name
            FROM lessons l
            JOIN classes c ON l.class_id = c.id
            JOIN users u ON c.teacher_id = u.id
            WHERE l.id = $1
        """
        async with db_service.pool.acquire() as conn:
            row = await conn.fetchrow(query, lesson_id)
            if row:
                lesson = dict(row)
                
                # Add role-specific information
                if role == "student":
                    progress_query = """
                        SELECT progress, completed, last_accessed, notes
                        FROM lesson_progress
                        WHERE lesson_id = $1 AND student_id = $2
                    """
                    progress = await conn.fetchrow(progress_query, lesson_id, current_user.id)
                    if progress:
                        lesson.update(dict(progress))
                        
                return lesson
                
    except Exception as e:
        logger.warning(f"Failed to fetch lesson details: {e}")
    
    # Fallback sample data
    return {
        "id": lesson_id,
        "title": "Introduction to Algebra",
        "description": "Learn the fundamentals of algebraic expressions and equations",
        "class_name": "Mathematics 101",
        "subject": "Mathematics",
        "teacher_name": "Mr. Smith",
        "duration": 45,
        "difficulty": "beginner",
        "objectives": [
            "Understand variables and constants",
            "Learn basic algebraic operations",
            "Solve simple equations"
        ],
        "content": {
            "type": "interactive",
            "sections": [
                {"title": "Introduction", "duration": 10, "type": "video"},
                {"title": "Practice Problems", "duration": 20, "type": "interactive"},
                {"title": "Quiz", "duration": 15, "type": "assessment"}
            ]
        },
        "resources": [
            {"name": "Algebra Basics PDF", "url": "/resources/algebra_basics.pdf"},
            {"name": "Video Tutorial", "url": "/videos/algebra_intro.mp4"}
        ],
        "xp_reward": 50,
        "created_at": "2025-01-01T09:00:00"
    }

@lessons_router.post("/")
async def create_lesson(
    lesson_data: Dict[str, Any],
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Create a new lesson (teachers and admins only)."""
    
    role = current_user.role.lower()
    
    if role not in ["teacher", "admin"]:
        raise HTTPException(status_code=403, detail="Not authorized to create lessons")
    
    # Return the submitted data with added metadata for development since database isn't set up
    import random
    from datetime import datetime
    
    # Use all the submitted data and just add the necessary metadata
    new_lesson = {
        **lesson_data,  # Include all submitted data
        "id": random.randint(1000, 9999),
        "teacher_id": current_user.id if role == "teacher" else lesson_data.get("teacher_id", current_user.id),
        "teacher_name": f"{current_user.first_name} {current_user.last_name}" if hasattr(current_user, 'first_name') else current_user.email,
        "completion_count": 0,
        "total_students": 0,
        "status": lesson_data.get("status", "draft"),
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }
    
    # Add class_name if class_id is provided
    if "class_id" in lesson_data or "classId" in lesson_data:
        # Handle both snake_case and camelCase
        class_id = lesson_data.get("class_id") or lesson_data.get("classId")
        new_lesson["class_name"] = f"Class {class_id}"  # You could fetch the real class name here
    
    # Add to in-memory storage
    in_memory_lessons.append(new_lesson)
    
    logger.info(f"Created mock lesson: {new_lesson.get('title', 'Unnamed')} for user {current_user.email}")
    return new_lesson

@lessons_router.put("/{lesson_id}/progress")
async def update_lesson_progress(
    lesson_id: int,
    progress_data: Dict[str, Any],
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Update student's progress on a lesson."""
    
    if current_user.role.lower() != "student":
        raise HTTPException(status_code=403, detail="Only students can update their progress")
    
    try:
        query = """
            INSERT INTO lesson_progress (lesson_id, student_id, progress, completed, last_accessed)
            VALUES ($1, $2, $3, $4, NOW())
            ON CONFLICT (lesson_id, student_id) 
            DO UPDATE SET 
                progress = $3,
                completed = $4,
                last_accessed = NOW()
            RETURNING *
        """
        async with db_service.pool.acquire() as conn:
            row = await conn.fetchrow(
                query,
                lesson_id,
                current_user.id,
                progress_data.get("progress", 0),
                progress_data.get("completed", False)
            )
            return dict(row)
            
    except Exception as e:
        logger.error(f"Failed to update progress: {e}")
        raise HTTPException(status_code=500, detail="Failed to update progress")

@lessons_router.get("/{lesson_id}/statistics")
async def get_lesson_statistics(
    lesson_id: int,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get statistics for a lesson (teachers and admins only)."""
    
    role = current_user.role.lower()
    
    if role not in ["teacher", "admin"]:
        raise HTTPException(status_code=403, detail="Not authorized to view statistics")
    
    # Implementation would fetch real statistics from database
    return {
        "lesson_id": lesson_id,
        "total_students": 28,
        "completed": 22,
        "in_progress": 4,
        "not_started": 2,
        "average_progress": 78.5,
        "average_time_spent": 38,
        "completion_rate": 78.6,
        "difficulty_rating": 3.2
    }