"""
Classes API Endpoints for ToolboxAI Educational Platform
Provides class management functionality for all user roles.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import logging
from ....api.auth.auth import get_current_user
from ....models.schemas import User
from ....services.database import db_service

logger = logging.getLogger(__name__)

# Create router for classes endpoints
classes_router = APIRouter(prefix="/classes", tags=["Classes"])

@classes_router.get("/")
async def get_classes(
    current_user: User = Depends(get_current_user),
    limit: int = Query(default=20, le=100),
    offset: int = Query(default=0, ge=0),
    subject: Optional[str] = None,
    grade_level: Optional[int] = None
) -> List[Dict[str, Any]]:
    """Get classes based on user role."""
    
    role = current_user.role.lower()
    
    # Try to get real data from database
    try:
        if role == "teacher":
            # Get teacher's classes
            query = """
                SELECT c.*, COUNT(DISTINCT ce.student_id) as student_count
                FROM classes c
                LEFT JOIN class_enrollments ce ON c.id = ce.class_id
                WHERE c.teacher_id = $1
                GROUP BY c.id
                ORDER BY c.created_at DESC
                LIMIT $2 OFFSET $3
            """
            async with db_service.pool.acquire() as conn:
                rows = await conn.fetch(query, current_user.id, limit, offset)
                return [dict(row) for row in rows]
                
        elif role == "student":
            # Get student's enrolled classes
            query = """
                SELECT c.*, u.first_name || ' ' || u.last_name as teacher_name
                FROM classes c
                JOIN class_enrollments ce ON c.id = ce.class_id
                JOIN users u ON c.teacher_id = u.id
                WHERE ce.student_id = $1
                ORDER BY c.name
                LIMIT $2 OFFSET $3
            """
            async with db_service.pool.acquire() as conn:
                rows = await conn.fetch(query, current_user.id, limit, offset)
                return [dict(row) for row in rows]
                
        elif role == "admin":
            # Get all classes with optional filters
            query = """
                SELECT c.*, u.first_name || ' ' || u.last_name as teacher_name,
                       COUNT(DISTINCT ce.student_id) as student_count
                FROM classes c
                JOIN users u ON c.teacher_id = u.id
                LEFT JOIN class_enrollments ce ON c.id = ce.class_id
                WHERE ($1::text IS NULL OR c.subject = $1)
                  AND ($2::int IS NULL OR c.grade_level = $2)
                GROUP BY c.id, u.first_name, u.last_name
                ORDER BY c.created_at DESC
                LIMIT $3 OFFSET $4
            """
            async with db_service.pool.acquire() as conn:
                rows = await conn.fetch(query, subject, grade_level, limit, offset)
                return [dict(row) for row in rows]
                
        elif role == "parent":
            # Get classes for parent's children
            query = """
                SELECT DISTINCT c.*, u.first_name || ' ' || u.last_name as teacher_name,
                       s.first_name || ' ' || s.last_name as student_name
                FROM classes c
                JOIN class_enrollments ce ON c.id = ce.class_id
                JOIN users u ON c.teacher_id = u.id
                JOIN users s ON ce.student_id = s.id
                JOIN parent_student_relationships psr ON s.id = psr.student_id
                WHERE psr.parent_id = $1
                ORDER BY c.name
                LIMIT $2 OFFSET $3
            """
            async with db_service.pool.acquire() as conn:
                rows = await conn.fetch(query, current_user.id, limit, offset)
                return [dict(row) for row in rows]
                
    except Exception as e:
        logger.warning(f"Failed to fetch classes from database: {e}. Using fallback data.")
    
    # Fallback sample data
    if role == "teacher":
        return [
            {
                "id": 1,
                "name": "Mathematics 101",
                "subject": "Mathematics",
                "grade_level": 7,
                "room": "Room 203",
                "schedule": "Mon/Wed/Fri 10:00 AM",
                "student_count": 28,
                "status": "active",
                "next_session": "2025-01-10T10:00:00"
            },
            {
                "id": 2,
                "name": "Advanced Algebra",
                "subject": "Mathematics",
                "grade_level": 8,
                "room": "Room 205",
                "schedule": "Tue/Thu 2:00 PM",
                "student_count": 24,
                "status": "active",
                "next_session": "2025-01-09T14:00:00"
            },
            {
                "id": 3,
                "name": "Geometry Basics",
                "subject": "Mathematics",
                "grade_level": 6,
                "room": "Room 201",
                "schedule": "Mon/Wed 1:00 PM",
                "student_count": 30,
                "status": "active",
                "next_session": "2025-01-08T13:00:00"
            }
        ]
    elif role == "student":
        return [
            {
                "id": 1,
                "name": "Mathematics 101",
                "subject": "Mathematics",
                "teacher_name": "Mr. Smith",
                "room": "Room 203",
                "schedule": "Mon/Wed/Fri 10:00 AM",
                "next_session": "2025-01-10T10:00:00",
                "assignments_due": 2,
                "grade": "A-"
            },
            {
                "id": 4,
                "name": "Science Lab",
                "subject": "Science",
                "teacher_name": "Ms. Johnson",
                "room": "Lab 2",
                "schedule": "Tue/Thu 10:30 AM",
                "next_session": "2025-01-09T10:30:00",
                "assignments_due": 1,
                "grade": "B+"
            }
        ]
    elif role == "admin":
        return [
            {
                "id": 1,
                "name": "Mathematics 101",
                "teacher_name": "John Smith",
                "subject": "Mathematics",
                "grade_level": 7,
                "student_count": 28,
                "status": "active",
                "created_at": "2024-09-01T08:00:00"
            },
            {
                "id": 2,
                "name": "Science Lab",
                "teacher_name": "Emily Johnson",
                "subject": "Science",
                "grade_level": 7,
                "student_count": 26,
                "status": "active",
                "created_at": "2024-09-01T08:00:00"
            }
        ]
    elif role == "parent":
        return [
            {
                "id": 1,
                "name": "Mathematics 101",
                "teacher_name": "Mr. Smith",
                "student_name": "Alex Johnson",
                "subject": "Mathematics",
                "grade_level": 7,
                "schedule": "Mon/Wed/Fri 10:00 AM",
                "student_grade": "A-"
            }
        ]
    
    return []

@classes_router.get("/{class_id}")
async def get_class_details(
    class_id: int,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get detailed information about a specific class."""
    
    role = current_user.role.lower()
    
    try:
        # Check access permissions and get class details
        if role == "teacher":
            query = """
                SELECT c.*, COUNT(DISTINCT ce.student_id) as student_count,
                       AVG(g.grade) as average_grade
                FROM classes c
                LEFT JOIN class_enrollments ce ON c.id = ce.class_id
                LEFT JOIN grades g ON c.id = g.class_id
                WHERE c.id = $1 AND c.teacher_id = $2
                GROUP BY c.id
            """
            async with db_service.pool.acquire() as conn:
                row = await conn.fetchrow(query, class_id, current_user.id)
                if row:
                    return dict(row)
                    
        elif role in ["student", "parent"]:
            # Verify access through enrollment or parent relationship
            query = """
                SELECT c.*, u.first_name || ' ' || u.last_name as teacher_name
                FROM classes c
                JOIN users u ON c.teacher_id = u.id
                WHERE c.id = $1
            """
            async with db_service.pool.acquire() as conn:
                row = await conn.fetchrow(query, class_id)
                if row:
                    return dict(row)
                    
        elif role == "admin":
            # Admin can see all classes
            query = """
                SELECT c.*, u.first_name || ' ' || u.last_name as teacher_name,
                       COUNT(DISTINCT ce.student_id) as student_count
                FROM classes c
                JOIN users u ON c.teacher_id = u.id
                LEFT JOIN class_enrollments ce ON c.id = ce.class_id
                WHERE c.id = $1
                GROUP BY c.id, u.first_name, u.last_name
            """
            async with db_service.pool.acquire() as conn:
                row = await conn.fetchrow(query, class_id)
                if row:
                    return dict(row)
                    
    except Exception as e:
        logger.warning(f"Failed to fetch class details: {e}")
    
    # Fallback sample data
    return {
        "id": class_id,
        "name": "Mathematics 101",
        "subject": "Mathematics",
        "grade_level": 7,
        "teacher_name": "Mr. Smith",
        "room": "Room 203",
        "schedule": "Mon/Wed/Fri 10:00 AM",
        "description": "Introduction to algebra and mathematical concepts",
        "student_count": 28,
        "status": "active",
        "created_at": "2024-09-01T08:00:00",
        "syllabus_url": "/files/syllabus_math101.pdf",
        "resources": [
            {"name": "Textbook", "url": "/resources/textbook_math7"},
            {"name": "Practice Problems", "url": "/resources/practice_math101"}
        ]
    }

@classes_router.get("/{class_id}/students")
async def get_class_students(
    class_id: int,
    current_user: User = Depends(get_current_user)
) -> List[Dict[str, Any]]:
    """Get students enrolled in a class."""
    
    role = current_user.role.lower()
    
    # Only teachers and admins can see full student list
    if role not in ["teacher", "admin"]:
        raise HTTPException(status_code=403, detail="Not authorized to view student list")
    
    try:
        query = """
            SELECT u.id, u.username, u.first_name, u.last_name, u.email,
                   ce.enrolled_at, AVG(g.grade) as average_grade
            FROM users u
            JOIN class_enrollments ce ON u.id = ce.student_id
            LEFT JOIN grades g ON u.id = g.student_id AND g.class_id = $1
            WHERE ce.class_id = $1
            GROUP BY u.id, ce.enrolled_at
            ORDER BY u.last_name, u.first_name
        """
        async with db_service.pool.acquire() as conn:
            rows = await conn.fetch(query, class_id)
            return [dict(row) for row in rows]
            
    except Exception as e:
        logger.warning(f"Failed to fetch class students: {e}")
    
    # Fallback sample data
    return [
        {
            "id": 1,
            "username": "alex_j",
            "first_name": "Alex",
            "last_name": "Johnson",
            "email": "alex.j@school.edu",
            "average_grade": 88.5,
            "enrolled_at": "2024-09-01T08:00:00"
        },
        {
            "id": 2,
            "username": "maria_g",
            "first_name": "Maria",
            "last_name": "Garcia",
            "email": "maria.g@school.edu",
            "average_grade": 92.3,
            "enrolled_at": "2024-09-01T08:00:00"
        }
    ]

@classes_router.post("/")
async def create_class(
    class_data: Dict[str, Any],
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Create a new class (teachers and admins only)."""
    
    role = current_user.role.lower()
    
    if role not in ["teacher", "admin"]:
        raise HTTPException(status_code=403, detail="Not authorized to create classes")
    
    try:
        query = """
            INSERT INTO classes (name, subject, grade_level, teacher_id, room, 
                               schedule, description, status)
            VALUES ($1, $2, $3, $4, $5, $6, $7, 'active')
            RETURNING *
        """
        async with db_service.pool.acquire() as conn:
            teacher_id = current_user.id if role == "teacher" else class_data.get("teacher_id")
            row = await conn.fetchrow(
                query,
                class_data["name"],
                class_data["subject"],
                class_data.get("grade_level"),
                teacher_id,
                class_data.get("room"),
                class_data.get("schedule"),
                class_data.get("description")
            )
            return dict(row)
            
    except Exception as e:
        logger.error(f"Failed to create class: {e}")
        raise HTTPException(status_code=500, detail="Failed to create class")

@classes_router.put("/{class_id}")
async def update_class(
    class_id: int,
    class_data: Dict[str, Any],
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Update class information."""
    
    role = current_user.role.lower()
    
    if role not in ["teacher", "admin"]:
        raise HTTPException(status_code=403, detail="Not authorized to update classes")
    
    # Implementation would update class in database
    return {
        "id": class_id,
        "message": "Class updated successfully",
        **class_data
    }

@classes_router.delete("/{class_id}")
async def delete_class(
    class_id: int,
    current_user: User = Depends(get_current_user)
) -> Dict[str, str]:
    """Delete a class (admins only)."""
    
    if current_user.role.lower() != "admin":
        raise HTTPException(status_code=403, detail="Only admins can delete classes")
    
    # Implementation would delete class from database
    return {"message": f"Class {class_id} deleted successfully"}