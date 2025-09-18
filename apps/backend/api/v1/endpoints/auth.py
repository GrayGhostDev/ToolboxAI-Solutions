"""
Authentication endpoints for ToolboxAI
"""

import os
from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from passlib.context import CryptContext
from pydantic import BaseModel

from apps.backend.core.security.jwt_handler import (
    Token, TokenData, create_access_token, get_current_user
)

# Configuration from environment
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Router setup
auth_router = APIRouter(prefix="/auth", tags=["Authentication"])

# Pydantic models
class UserLogin(BaseModel):
    username: str
    password: str

# Mock user database
fake_users_db = {
    "test_teacher": {
        "username": "test_teacher",
        "hashed_password": pwd_context.hash("TestPass123!"),
        "role": "teacher"
    },
    "test_student": {
        "username": "test_student",
        "hashed_password": pwd_context.hash("StudentPass123!"),
        "role": "student"
    }
}

def verify_password(plain_password, hashed_password):
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)

def authenticate_user(username: str, password: str):
    """Authenticate a user"""
    user = fake_users_db.get(username)
    if not user:
        return False
    if not verify_password(password, user["hashed_password"]):
        return False
    return user

# Use the imported create_access_token from jwt_handler

@auth_router.post("/login", response_model=Token)
async def login(user_credentials: UserLogin):
    """
    Login endpoint for authentication
    """
    user = authenticate_user(user_credentials.username, user_credentials.password)
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

    return Token(
        access_token=access_token,
        token_type="bearer",
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        role=user["role"]
    )

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