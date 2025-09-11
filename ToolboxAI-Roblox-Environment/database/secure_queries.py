"""
Secure Database Queries Module
All queries use parameterized statements to prevent SQL injection
"""
from typing import Any, Dict, List, Optional, Tuple
import asyncpg
import psycopg2
from psycopg2.extras import RealDictCursor

class SecureDatabase:
    """Database wrapper with SQL injection prevention"""
    
    @staticmethod
    def get_user(conn, user_id: int) -> Optional[Dict]:
        """Get user with parameterized query"""
        query = "SELECT * FROM users WHERE id = %s"
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, (user_id,))
            return cur.fetchone()
    
    @staticmethod
    def search_content(conn, search_term: str) -> List[Dict]:
        """Search with SQL injection prevention"""
        query = """
            SELECT * FROM content 
            WHERE title ILIKE %s OR description ILIKE %s
            LIMIT 100
        """
        search_pattern = f"%{search_term}%"
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, (search_pattern, search_pattern))
            return cur.fetchall()
    
    @staticmethod
    def create_lesson(conn, course_id: int, title: str, content: str) -> int:
        """Insert with parameterized query"""
        query = """
            INSERT INTO lessons (course_id, title, content)
            VALUES (%s, %s, %s)
            RETURNING id
        """
        with conn.cursor() as cur:
            cur.execute(query, (course_id, title, content))
            return cur.fetchone()[0]
    
    @staticmethod
    def update_user_role(conn, user_id: int, role: str) -> bool:
        """Update with validation and parameters"""
        allowed_roles = ['student', 'teacher', 'admin', 'parent']
        if role not in allowed_roles:
            raise ValueError(f"Invalid role: {role}")
        
        query = "UPDATE users SET role = %s WHERE id = %s"
        with conn.cursor() as cur:
            cur.execute(query, (role, user_id))
            return cur.rowcount > 0

# Async version for modern applications
class SecureDatabaseAsync:
    """Async database wrapper with SQL injection prevention"""
    
    @staticmethod
    async def get_user(pool: asyncpg.Pool, user_id: int) -> Optional[Dict]:
        """Get user with parameterized query (async)"""
        query = "SELECT * FROM users WHERE id = $1"
        async with pool.acquire() as conn:
            row = await conn.fetchrow(query, user_id)
            return dict(row) if row else None
    
    @staticmethod
    async def search_content(pool: asyncpg.Pool, search_term: str) -> List[Dict]:
        """Search with SQL injection prevention (async)"""
        query = """
            SELECT * FROM content 
            WHERE title ILIKE $1 OR description ILIKE $1
            LIMIT 100
        """
        search_pattern = f"%{search_term}%"
        async with pool.acquire() as conn:
            rows = await conn.fetch(query, search_pattern)
            return [dict(row) for row in rows]
