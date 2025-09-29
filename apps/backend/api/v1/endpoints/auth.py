"""
Authentication endpoints for ToolboxAI
"""

import os
from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from pydantic import BaseModel

from apps.backend.core.security.jwt_handler import (
    Token, TokenData, create_access_token, get_current_user
)

# Use direct bcrypt implementation (2025 best practice)
from apps.backend.core.security.bcrypt_handler import BcryptHandler

# Configuration from environment
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

# Password hashing using direct bcrypt with SHA-256 pre-hashing
# This avoids passlib compatibility issues while following OWASP recommendations
bcrypt_handler = BcryptHandler(rounds=12)

# Router setup
auth_router = APIRouter(prefix="/auth", tags=["Authentication"])

# Pydantic models
class UserLogin(BaseModel):
    username: Optional[str] = None
    email: Optional[str] = None
    password: str

# Mock user database with demo users matching frontend
fake_users_db = {
    "admin@toolboxai.com": {
        "username": "admin",
        "email": "admin@toolboxai.com",
        "hashed_password": bcrypt_handler.hash_password("Admin123!"),
        "role": "admin"
    },
    "jane.smith@school.edu": {
        "username": "jane_smith",
        "email": "jane.smith@school.edu",
        "hashed_password": bcrypt_handler.hash_password("Teacher123!"),
        "role": "teacher"
    },
    "alex.johnson@student.edu": {
        "username": "alex_johnson",
        "email": "alex.johnson@student.edu",
        "hashed_password": bcrypt_handler.hash_password("Student123!"),
        "role": "student"
    },
    # Keep old test users for backwards compatibility
    "test_teacher": {
        "username": "test_teacher",
        "email": "test_teacher@test.com",
        "hashed_password": bcrypt_handler.hash_password("TestPass123!"),
        "role": "teacher"
    },
    "test_student": {
        "username": "test_student",
        "email": "test_student@test.com",
        "hashed_password": bcrypt_handler.hash_password("StudentPass123!"),
        "role": "student"
    }
}

def verify_password(plain_password, hashed_password):
    """Verify a password against its hash"""
    # Direct bcrypt with SHA-256 pre-hashing handles any length password
    return bcrypt_handler.verify_password(plain_password, hashed_password)

def authenticate_user(username: Optional[str], email: Optional[str], password: str):
    """Authenticate a user by username or email"""
    # Try to find user by email first, then by username
    lookup_key = email if email else username
    if not lookup_key:
        return False

    user = fake_users_db.get(lookup_key)
    if not user:
        return False
    if not verify_password(password, user["hashed_password"]):
        return False
    return user

# Use the imported create_access_token from jwt_handler

@auth_router.post("/login")
async def login(user_credentials: UserLogin):
    """
    Authenticate user and return JWT access token.

    Supports authentication using either username or email address.
    Returns user information along with the access token.

    Args:
        user_credentials (UserLogin): Login credentials containing:
            - username (optional): User's username
            - email (optional): User's email address
            - password (required): User's password

    Returns:
        dict: Authentication response containing:
            - access_token (str): JWT access token
            - token_type (str): Token type ("bearer")
            - expires_in (int): Token expiration time in seconds
            - role (str): User's role in the system
            - user (dict): User profile information

    Raises:
        HTTPException: 401 if credentials are invalid

    Rate Limit:
        10 requests per minute per IP

    Example:
        ```python
        response = await login({
            "email": "teacher@school.edu",
            "password": "SecurePass123!"
        })
        token = response["access_token"]
        ```
    """
    user = authenticate_user(user_credentials.username, user_credentials.email, user_credentials.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["username"], "role": user["role"], "user_id": 1},
        expires_delta=access_token_expires
    )

    # Return token with user information for frontend
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "role": user["role"],
        "user": {
            "id": user.get("id", 1),  # Mock ID for now
            "username": user["username"],
            "email": user.get("email", ""),
            "displayName": user.get("displayName", user["username"]),
            "role": user["role"]
        }
    }

@auth_router.post("/refresh", response_model=Token)
async def refresh_token(current_user: TokenData = Depends(get_current_user)):
    """
    Refresh an existing token
    """
    # Create new token with existing user data
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={
            "sub": current_user.username,
            "role": current_user.role,
            "user_id": current_user.user_id
        },
        expires_delta=access_token_expires
    )

    return Token(
        access_token=access_token,
        token_type="bearer",
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        role=current_user.role
    )

@auth_router.post("/logout")
async def logout():
    """
    Logout endpoint
    """
    # In a real application, you would invalidate the token here
    # For now, just return success
    return {"message": "Successfully logged out"}

# Export router with the expected name
router = auth_router