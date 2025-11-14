"""
Authentication endpoints for ToolboxAI
"""

import os
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel

# Use direct bcrypt implementation (2025 best practice)
from apps.backend.core.security.bcrypt_handler import BcryptHandler
from apps.backend.core.security.jwt_handler import (
    Token,
    TokenData,
    create_access_token,
    get_current_user,
)

# Configuration from environment
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

# Password hashing using direct bcrypt with SHA-256 pre-hashing
# This avoids passlib compatibility issues while following OWASP recommendations
bcrypt_handler = BcryptHandler(rounds=12)

# Router setup
auth_router = APIRouter(prefix="/auth", tags=["Authentication"])


# Pydantic models
class UserLogin(BaseModel):
    username: str | None = None
    email: str | None = None
    password: str


# Mock user database with demo users matching frontend
fake_users_db = {
    "admin@toolboxai.com": {
        "username": "admin",
        "email": "admin@toolboxai.com",
        "hashed_password": bcrypt_handler.hash_password("Admin123!"),
        "role": "admin",
    },
    "jane.smith@school.edu": {
        "username": "jane_smith",
        "email": "jane.smith@school.edu",
        "hashed_password": bcrypt_handler.hash_password("Teacher123!"),
        "role": "teacher",
    },
    "alex.johnson@student.edu": {
        "username": "alex_johnson",
        "email": "alex.johnson@student.edu",
        "hashed_password": bcrypt_handler.hash_password("Student123!"),
        "role": "student",
    },
    # Keep old test users for backwards compatibility
    "test_teacher": {
        "username": "test_teacher",
        "email": "test_teacher@test.com",
        "hashed_password": bcrypt_handler.hash_password("TestPass123!"),
        "role": "teacher",
    },
    "test_student": {
        "username": "test_student",
        "email": "test_student@test.com",
        "hashed_password": bcrypt_handler.hash_password("StudentPass123!"),
        "role": "student",
    },
}


def verify_password(plain_password, hashed_password):
    """Verify a password against its hash"""
    # Direct bcrypt with SHA-256 pre-hashing handles any length password
    return bcrypt_handler.verify_password(plain_password, hashed_password)


def authenticate_user(username: str | None, email: str | None, password: str):
    """
    Authenticate a user by username or email.

    Args:
        username: Optional username to authenticate with
        email: Optional email to authenticate with
        password: User's password

    Returns:
        User dict if authentication successful, False otherwise
    """
    if not username and not email:
        return False

    # Try direct lookup by email or username (for keys in dict)
    lookup_key = email if email else username
    user = fake_users_db.get(lookup_key)

    # If not found, search through all users for matching username or email
    if not user:
        for user_data in fake_users_db.values():
            # Check if username or email matches
            if (username and user_data.get("username") == username) or (
                email and user_data.get("email") == email
            ):
                user = user_data
                break

    # User not found
    if not user:
        return False

    # Verify password
    if not verify_password(password, user["hashed_password"]):
        return False

    return user


# Use the imported create_access_token from jwt_handler


class UserRegister(BaseModel):
    email: str
    password: str
    username: str
    first_name: str
    last_name: str
    role: str = "student"  # Default role


@auth_router.post("/register")
async def register(user_data: UserRegister):
    """
    Register a new user account.

    Args:
        user_data (UserRegister): Registration data containing:
            - email (required): User's email address
            - password (required): User's password
            - username (required): Desired username
            - first_name (required): User's first name
            - last_name (required): User's last name
            - role (optional): User role (default: student)

    Returns:
        dict: Authentication response containing:
            - access_token (str): JWT access token
            - token_type (str): Token type ("bearer")
            - expires_in (int): Token expiration time in seconds
            - role (str): User's role
            - user (dict): User profile information

    Raises:
        HTTPException: 400 if user already exists
    """
    # Check if user already exists
    if user_data.email in fake_users_db:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists",
        )

    # Check if username already exists
    for existing_user in fake_users_db.values():
        if existing_user.get("username") == user_data.username:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already taken",
            )

    # Hash password
    hashed_password = bcrypt_handler.hash_password(user_data.password)

    # Create new user
    new_user = {
        "username": user_data.username,
        "email": user_data.email,
        "hashed_password": hashed_password,
        "role": user_data.role,
        "first_name": user_data.first_name,
        "last_name": user_data.last_name,
        "displayName": f"{user_data.first_name} {user_data.last_name}",
    }

    # Store user in fake database
    fake_users_db[user_data.email] = new_user

    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": new_user["username"], "role": new_user["role"], "user_id": len(fake_users_db)},
        expires_delta=access_token_expires,
    )

    # Return same format as login
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "role": new_user["role"],
        "user": {
            "id": len(fake_users_db),  # Simple ID based on count
            "username": new_user["username"],
            "email": new_user["email"],
            "displayName": new_user["displayName"],
            "firstName": new_user["first_name"],
            "lastName": new_user["last_name"],
            "role": new_user["role"],
        },
    }


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
    user = authenticate_user(
        user_credentials.username, user_credentials.email, user_credentials.password
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["username"], "role": user["role"], "user_id": 1},
        expires_delta=access_token_expires,
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
            "role": user["role"],
        },
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
            "user_id": current_user.user_id,
        },
        expires_delta=access_token_expires,
    )

    return Token(
        access_token=access_token,
        token_type="bearer",
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        role=current_user.role,
    )


@auth_router.post("/logout")
async def logout():
    """
    Logout endpoint
    """
    # In a real application, you would invalidate the token here
    # For now, just return success
    return {"message": "Successfully logged out"}


@auth_router.post("/demo-login")
async def demo_login(role: str = "teacher"):
    """
    Demo login endpoint for development - bypasses authentication.

    Args:
        role (str): The role to use for the demo user (admin, teacher, student, parent)

    Returns:
        dict: Authentication response with demo token

    Example:
        POST /api/v1/auth/demo-login?role=teacher
    """
    # Map role to demo user
    role_to_user = {
        "admin": {
            "username": "admin_demo",
            "email": "admin@demo.com",
            "displayName": "Demo Admin",
            "role": "admin",
            "id": 1,
        },
        "teacher": {
            "username": "teacher_demo",
            "email": "teacher@demo.com",
            "displayName": "Demo Teacher",
            "role": "teacher",
            "id": 2,
        },
        "student": {
            "username": "student_demo",
            "email": "student@demo.com",
            "displayName": "Demo Student",
            "role": "student",
            "id": 3,
        },
        "parent": {
            "username": "parent_demo",
            "email": "parent@demo.com",
            "displayName": "Demo Parent",
            "role": "parent",
            "id": 4,
        },
    }

    # Get the demo user based on role
    demo_user = role_to_user.get(role, role_to_user["teacher"])

    # Create access token for demo user
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": demo_user["username"], "role": demo_user["role"], "user_id": demo_user["id"]},
        expires_delta=access_token_expires,
    )

    # Return token with user information
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "role": demo_user["role"],
        "user": demo_user,
    }


# Export router with the expected name
router = auth_router
