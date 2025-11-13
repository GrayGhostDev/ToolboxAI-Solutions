"""
User schema definitions
"""

from ..models.schemas import Session, User

# User-related schemas
UserCreate = User
UserResponse = User
UserUpdate = User
SessionCreate = Session
SessionResponse = Session

__all__ = [
    "User",
    "Session",
    "UserCreate",
    "UserResponse",
    "UserUpdate",
    "SessionCreate",
    "SessionResponse",
]
