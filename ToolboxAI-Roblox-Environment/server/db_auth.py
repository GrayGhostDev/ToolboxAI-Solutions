"""
Real Database Authentication Module
Connects to PostgreSQL for actual user authentication.
"""

import os
import hashlib
import secrets
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import psycopg2
from psycopg2.extras import RealDictCursor
import jwt
from dotenv import load_dotenv
from passlib.context import CryptContext

# Load environment variables
load_dotenv()

# Database configuration
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': int(os.getenv('DB_PORT', 5432)),
    'user': os.getenv('DB_USER', 'eduplatform'),
    'password': os.getenv('DB_PASSWORD', 'eduplatform2024'),
    'database': os.getenv('DB_NAME', 'educational_platform_dev')
}

# JWT configuration
JWT_SECRET = os.getenv('JWT_SECRET_KEY', 'your-secret-key-change-in-production')
JWT_ALGORITHM = 'HS256'
JWT_EXPIRATION_HOURS = 24

class DatabaseAuth:
    """Handles real database authentication."""
    
    def __init__(self):
        """Initialize database authentication."""
        self.db_config = DB_CONFIG
        # Initialize password context for bcrypt
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        
    def get_connection(self):
        """Get database connection."""
        return psycopg2.connect(**self.db_config)
        
    def hash_password(self, password: str) -> str:
        """Hash a password for storage using bcrypt."""
        return self.pwd_context.hash(password)
        
    def verify_password(self, password: str, password_hash: str) -> bool:
        """Verify a password against its bcrypt hash."""
        try:
            return self.pwd_context.verify(password, password_hash)
        except Exception:
            # If bcrypt fails, try SHA256 as fallback for legacy passwords
            return hashlib.sha256(password.encode()).hexdigest() == password_hash
        
    def authenticate_user(self, username_or_email: str, password: str) -> Optional[Dict[str, Any]]:
        """
        Authenticate a user with username/email and password.
        Returns user data if successful, None otherwise.
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            # Check if input is email or username
            if '@' in username_or_email:
                query = """
                    SELECT id, username, email, password_hash, first_name, last_name, 
                           first_name as display_name, role, is_active, is_verified, profile_picture_url as avatar_url
                    FROM dashboard_users 
                    WHERE email = %s AND is_active = true
                """
            else:
                query = """
                    SELECT id, username, email, password_hash, first_name, last_name,
                           first_name as display_name, role, is_active, is_verified, profile_picture_url as avatar_url
                    FROM dashboard_users 
                    WHERE username = %s AND is_active = true
                """
                
            cursor.execute(query, (username_or_email,))
            user = cursor.fetchone()
            
            if user and self.verify_password(password, user['password_hash']):
                # Update last login
                cursor.execute(
                    "UPDATE dashboard_users SET last_login = %s WHERE id = %s",
                    (datetime.now(), user['id'])
                )
                conn.commit()
                
                # Remove password hash from response
                del user['password_hash']
                
                cursor.close()
                conn.close()
                
                return dict(user)
                
            cursor.close()
            conn.close()
            return None
            
        except Exception as e:
            print(f"Authentication error: {e}")
            return None
            
    def create_tokens(self, user: Dict[str, Any]) -> Dict[str, str]:
        """Create JWT access and refresh tokens."""
        # Access token payload
        access_payload = {
            'user_id': str(user['id']),
            'username': user['username'],
            'email': user['email'],
            'role': user['role'],
            'exp': datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS)
        }
        
        # Refresh token payload (longer expiration)
        refresh_payload = {
            'user_id': str(user['id']),
            'type': 'refresh',
            'exp': datetime.utcnow() + timedelta(days=30)
        }
        
        access_token = jwt.encode(access_payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
        refresh_token = jwt.encode(refresh_payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
        
        return {
            'access_token': access_token,
            'refresh_token': refresh_token
        }
        
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify and decode a JWT token."""
        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
            
    def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user by ID."""
        try:
            conn = self.get_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            cursor.execute("""
                SELECT id, username, email, first_name, last_name, first_name as display_name,
                       role, is_active, is_verified, profile_picture_url as avatar_url, address as bio
                FROM dashboard_users 
                WHERE id = %s AND is_active = true
            """, (user_id,))
            
            user = cursor.fetchone()
            
            cursor.close()
            conn.close()
            
            return dict(user) if user else None
            
        except Exception as e:
            print(f"Error getting user: {e}")
            return None
            
    def get_user_stats(self, user_id: str) -> Dict[str, Any]:
        """Get user statistics from the database."""
        try:
            conn = self.get_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            stats = {}
            
            # Get user's basic info
            cursor.execute("""
                SELECT role, created_at, last_login 
                FROM dashboard_users 
                WHERE id = %s
            """, (user_id,))
            user_info = cursor.fetchone()
            
            if user_info:
                stats['role'] = user_info['role']
                stats['member_since'] = user_info['created_at'].isoformat() if user_info['created_at'] else None
                stats['last_login'] = user_info['last_login'].isoformat() if user_info['last_login'] else None
                
                # Role-specific stats
                if user_info['role'] == 'student':
                    # Get student progress
                    cursor.execute("""
                        SELECT COUNT(DISTINCT course_id) as courses_enrolled,
                               AVG(progress_percentage) as avg_progress,
                               SUM(xp_earned) as total_xp
                        FROM student_progress
                        WHERE student_id = %s::uuid
                    """, (user_id,))
                    progress = cursor.fetchone()
                    if progress:
                        stats['courses_enrolled'] = progress['courses_enrolled'] or 0
                        stats['avg_progress'] = float(progress['avg_progress'] or 0)
                        stats['total_xp'] = progress['total_xp'] or 0
                        
                elif user_info['role'] == 'teacher':
                    # Get teacher stats
                    cursor.execute("""
                        SELECT COUNT(*) as total_courses
                        FROM courses
                        WHERE teacher_id = %s::uuid
                    """, (user_id,))
                    courses = cursor.fetchone()
                    if courses:
                        stats['total_courses'] = courses['total_courses'] or 0
                        
                    cursor.execute("""
                        SELECT COUNT(*) as total_classes
                        FROM classes
                        WHERE teacher_id = %s::uuid
                    """, (user_id,))
                    classes = cursor.fetchone()
                    if classes:
                        stats['total_classes'] = classes['total_classes'] or 0
                        
            cursor.close()
            conn.close()
            
            return stats
            
        except Exception as e:
            print(f"Error getting user stats: {e}")
            return {}
            
    def create_user(self, user_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create a new user in the database."""
        try:
            conn = self.get_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            # Hash the password
            password_hash = self.hash_password(user_data['password'])
            
            # Insert new user
            cursor.execute("""
                INSERT INTO dashboard_users (username, email, password_hash, first_name, last_name, 
                                 role, is_active, is_verified)
                VALUES (%s, %s, %s, %s, %s, %s, true, false)
                RETURNING id, username, email, first_name, last_name, first_name as display_name, role
            """, (
                user_data['username'],
                user_data['email'],
                password_hash,
                user_data.get('first_name', ''),
                user_data.get('last_name', ''),
                user_data.get('role', 'student')
            ))
            
            new_user = cursor.fetchone()
            conn.commit()
            
            cursor.close()
            conn.close()
            
            return dict(new_user) if new_user else None
            
        except Exception as e:
            print(f"Error creating user: {e}")
            return None


# Global instance
db_auth = DatabaseAuth()