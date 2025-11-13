"""
Authentication Service

Business logic for authentication and authorization operations.
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from apps.backend.core.config import settings
from apps.backend.core.logging import logging_manager
from apps.backend.models.schemas import User

logger = logging_manager.get_logger(__name__)


class AuthService:
    """Authentication service for handling user authentication and authorization"""

    def __init__(self):
        self.token_expire_minutes = getattr(settings, "TOKEN_EXPIRE_MINUTES", 30)

    async def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """
        Authenticate user with username/password

        Args:
            username: User's username or email
            password: User's password

        Returns:
            User object if authentication successful, None otherwise
        """
        try:
            # For now, return a mock user
            # In a full implementation, this would verify against database
            if username and password:
                return User(
                    id="user_123",
                    username=username,
                    email=f"{username}@example.com",
                    role="student",
                    is_active=True,
                )
            return None

        except Exception as e:
            logger.error(f"Authentication failed for user {username}: {e}")
            return None

    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        """
        Get user by ID

        Args:
            user_id: User identifier

        Returns:
            User object if found, None otherwise
        """
        try:
            # For now, return a mock user
            # In a full implementation, this would query the database
            return User(
                id=user_id,
                username=f"user_{user_id}",
                email=f"user_{user_id}@example.com",
                role="student",
                is_active=True,
            )

        except Exception as e:
            logger.error(f"Failed to get user {user_id}: {e}")
            return None

    async def get_user_by_token(self, token: str) -> Optional[User]:
        """
        Get user from JWT token

        Args:
            token: JWT token

        Returns:
            User object if token valid, None otherwise
        """
        try:
            from apps.backend.api.auth.auth import decode_jwt_token

            # Decode token to get user ID
            payload = decode_jwt_token(token)
            if not payload:
                return None

            user_id = payload.get("sub")
            if not user_id:
                return None

            # Get user by ID
            return await self.get_user_by_id(user_id)

        except Exception as e:
            logger.error(f"Failed to get user from token: {e}")
            return None

    async def create_access_token(self, user: User) -> Dict[str, Any]:
        """
        Create JWT access token for user

        Args:
            user: User object

        Returns:
            Dict containing token information
        """
        try:
            from apps.backend.api.auth.auth import create_jwt_token

            # Create token payload
            token_data = {
                "sub": user.id,
                "username": user.username,
                "role": user.role,
                "exp": datetime.now(timezone.utc) + timedelta(minutes=self.token_expire_minutes),
            }

            # Generate token
            access_token = create_jwt_token(token_data)

            return {
                "access_token": access_token,
                "token_type": "bearer",
                "expires_in": self.token_expire_minutes * 60,
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "role": user.role,
                },
            }

        except Exception as e:
            logger.error(f"Failed to create access token for user {user.id}: {e}")
            raise

    async def refresh_token(self, refresh_token: str) -> Optional[Dict[str, Any]]:
        """
        Refresh access token

        Args:
            refresh_token: Refresh token

        Returns:
            New token information if successful, None otherwise
        """
        try:
            # Get user from refresh token
            user = await self.get_user_by_token(refresh_token)
            if not user:
                return None

            # Create new access token
            return await self.create_access_token(user)

        except Exception as e:
            logger.error(f"Failed to refresh token: {e}")
            return None

    async def revoke_token(self, token: str) -> bool:
        """
        Revoke access token

        Args:
            token: Token to revoke

        Returns:
            True if successful, False otherwise
        """
        try:
            # For now, just log the revocation
            # In a full implementation, this would add token to blacklist
            logger.info(f"Token revoked: {token[:20]}...")
            return True

        except Exception as e:
            logger.error(f"Failed to revoke token: {e}")
            return False

    async def check_user_permissions(self, user: User, required_roles: List[str]) -> bool:
        """
        Check if user has required permissions

        Args:
            user: User object
            required_roles: List of required roles

        Returns:
            True if user has permission, False otherwise
        """
        try:
            if not user or not user.is_active:
                return False

            # Admin users have all permissions
            if user.role == "admin":
                return True

            # Check if user role is in required roles
            return user.role in required_roles

        except Exception as e:
            logger.error(f"Failed to check permissions for user {user.id}: {e}")
            return False

    async def check_resource_access(
        self, user: User, resource_type: str, resource_id: str, action: str = "read"
    ) -> bool:
        """
        Check if user can access a specific resource

        Args:
            user: User object
            resource_type: Type of resource (e.g., 'content', 'class', 'lesson')
            resource_id: Resource identifier
            action: Action to perform (read, write, delete)

        Returns:
            True if user has access, False otherwise
        """
        try:
            if not user or not user.is_active:
                return False

            # Admin users have access to all resources
            if user.role == "admin":
                return True

            # Teachers have access to their classes and content
            if user.role == "teacher":
                if resource_type in ["content", "class", "lesson", "assessment"]:
                    # In a full implementation, check if teacher owns/manages this resource
                    return True

            # Students have read access to their assigned content
            if user.role == "student" and action == "read":
                if resource_type in ["content", "lesson", "assessment"]:
                    # In a full implementation, check if student is enrolled in related class
                    return True

            # User can access their own resources
            if resource_type == "user" and resource_id == user.id:
                return True

            return False

        except Exception as e:
            logger.error(f"Failed to check resource access for user {user.id}: {e}")
            return False

    async def get_user_stats(self, user_id: str) -> Dict[str, Any]:
        """
        Get user activity statistics

        Args:
            user_id: User identifier

        Returns:
            Dict containing user statistics
        """
        try:
            # For now, return mock statistics
            # In a full implementation, this would query database
            return {
                "user_id": user_id,
                "login_count": 50,
                "last_login": datetime.now(timezone.utc).isoformat(),
                "content_generated": 25,
                "lessons_completed": 10,
                "assessments_taken": 8,
                "total_time_spent": 3600,  # seconds
            }

        except Exception as e:
            logger.error(f"Failed to get user stats for {user_id}: {e}")
            return {}

    async def update_user_activity(
        self, user_id: str, activity_type: str, metadata: Dict[str, Any]
    ) -> bool:
        """
        Update user activity log

        Args:
            user_id: User identifier
            activity_type: Type of activity
            metadata: Additional activity data

        Returns:
            True if successful, False otherwise
        """
        try:
            # For now, just log the activity
            # In a full implementation, this would store in database
            logger.info(
                f"User activity logged",
                extra_fields={
                    "user_id": user_id,
                    "activity_type": activity_type,
                    "metadata": metadata,
                },
            )
            return True

        except Exception as e:
            logger.error(f"Failed to update user activity for {user_id}: {e}")
            return False


# Global service instance
auth_service = AuthService()


def get_auth_service() -> AuthService:
    """Get the global auth service instance"""
    return auth_service
