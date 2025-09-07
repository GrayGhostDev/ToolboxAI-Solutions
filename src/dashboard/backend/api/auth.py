"""
Authentication endpoints for the educational platform
"""

import os
import sys
import uuid
from datetime import datetime, timedelta
from typing import Optional

import bcrypt
import jwt

# Import database and models
from database import get_db
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from models import User, UserRole
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session

from ._utils import now
from .simple_ghost import APIResponse

# Create router
router = APIRouter(prefix="/api/v1/auth", tags=["authentication"])
security = HTTPBearer()

# JWT Configuration
JWT_SECRET = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXPIRATION_MINUTES = int(os.getenv("JWT_EXPIRATION_MINUTES", "1440"))  # 24 hours

# ==================== Pydantic Models ====================


class UserRegister(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8)
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    role: str = Field(..., pattern="^(Admin|Teacher|Student|Parent)$")
    birth_date: Optional[datetime] = None
    parent_email: Optional[EmailStr] = None  # For students under 13 (COPPA)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: dict


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class PasswordReset(BaseModel):
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str = Field(..., min_length=8)


# ==================== Helper Functions ====================


def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def verify_password(password: str, hashed: str) -> bool:
    """Verify a password against its hash"""
    try:
        return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))
    except Exception:
        return False


def create_access_token(user: User, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token"""
    if expires_delta:
        expire_dt = now() + expires_delta
    else:
        expire_dt = now() + timedelta(minutes=JWT_EXPIRATION_MINUTES)

    payload = {
        "sub": user.id,
        "email": user.email,
        "username": user.username,
        "role": user.role.value,
        "exp": int(expire_dt.timestamp()),
        "iat": int(now().timestamp()),
        "type": "access",
    }

    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def create_refresh_token(user: User) -> str:
    """Create a JWT refresh token (longer expiration)"""
    expire_dt = now() + timedelta(days=30)

    payload = {
        "sub": user.id,
        "exp": int(expire_dt.timestamp()),
        "iat": int(now().timestamp()),
        "type": "refresh",
    }

    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> dict:
    """Decode and verify a JWT token"""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired"
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        )


# ==================== Authentication Endpoints ====================


@router.post("/register", response_model=TokenResponse)
async def register(user_data: UserRegister, db: Session = Depends(get_db)):
    """Register a new user"""

    # Check if email already exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered"
        )

    # Check if username already exists
    existing_username = (
        db.query(User).filter(User.username == user_data.username).first()
    )
    if existing_username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Username already taken"
        )

    # COPPA compliance: Check age for students
    if user_data.role == "Student" and user_data.birth_date:
        age = (datetime.now() - user_data.birth_date).days // 365
        if age < 13 and not user_data.parent_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Parental consent required for users under 13",
            )

    # Create new user
    new_user = User(
        id=str(uuid.uuid4()),
        email=user_data.email,
        username=user_data.username,
        password_hash=hash_password(user_data.password),
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        display_name=f"{user_data.first_name} {user_data.last_name}",
        role=UserRole[user_data.role.upper()],
        birth_date=user_data.birth_date,
        created_at=now(),
        is_active=True,
        is_verified=False,  # Email verification required
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Create tokens
    access_token = create_access_token(new_user)
    refresh_token = create_refresh_token(new_user)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": JWT_EXPIRATION_MINUTES * 60,
        "user": {
            "id": new_user.id,
            "email": new_user.email,
            "username": new_user.username,
            "displayName": new_user.display_name,
            "role": new_user.role.value,
            "avatarUrl": new_user.avatar_url,
        },
    }


@router.post("/login", response_model=TokenResponse)
async def login(credentials: UserLogin, db: Session = Depends(get_db)):
    """Login with email and password"""

    # Find user by email
    user = db.query(User).filter(User.email == credentials.email).first()

    if not user or not verify_password(credentials.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password"
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Account is inactive"
        )

    # Update last login
    user.last_login = now()
    db.commit()

    # Create tokens
    access_token = create_access_token(user)
    refresh_token = create_refresh_token(user)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": JWT_EXPIRATION_MINUTES * 60,
        "user": {
            "id": user.id,
            "email": user.email,
            "username": user.username,
            "displayName": user.display_name,
            "role": user.role.value,
            "avatarUrl": user.avatar_url,
            "totalXp": user.total_xp,
            "level": user.level,
        },
    }


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    token_request: RefreshTokenRequest, db: Session = Depends(get_db)
):
    """Refresh access token using refresh token"""

    # Decode refresh token
    try:
        payload = decode_token(token_request.refresh_token)
    except HTTPException:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token"
        )

    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type"
        )

    # Get user
    user = db.query(User).filter(User.id == payload["sub"]).first()

    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )

    # Create new tokens
    access_token = create_access_token(user)
    refresh_token = create_refresh_token(user)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": JWT_EXPIRATION_MINUTES * 60,
        "user": {
            "id": user.id,
            "email": user.email,
            "username": user.username,
            "displayName": user.display_name,
            "role": user.role.value,
            "avatarUrl": user.avatar_url,
        },
    }


@router.post("/logout")
async def logout(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Logout user (client should remove tokens)"""

    # In a production environment, you might want to:
    # 1. Add the token to a blacklist
    # 2. Store revoked tokens in Redis with expiration
    # 3. Check blacklist in authentication middleware

    return APIResponse.ok(message="Logged out successfully")


@router.get("/me")
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    """Get current user information"""

    # Decode token
    try:
        payload = decode_token(credentials.credentials)
    except HTTPException:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        )

    # Get user
    user = db.query(User).filter(User.id == payload["sub"]).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    # FastAPI dependencies should return plain data, not APIResponse objects
    # The route handler will wrap this in an APIResponse if needed
    return {
        "id": user.id,
        "email": user.email,
        "username": user.username,
        "firstName": user.first_name,
        "lastName": user.last_name,
        "displayName": user.display_name,
        "role": user.role.value,
        "avatarUrl": user.avatar_url,
        "totalXp": user.total_xp,
        "level": user.level,
        "streakDays": user.streak_days,
        "isVerified": user.is_verified,
        "language": user.language,
        "timezone": user.timezone,
        "createdAt": user.created_at.isoformat(),
        "lastLogin": user.last_login.isoformat() if user.last_login else None,
    }


@router.post("/password-reset")
async def request_password_reset(
    reset_request: PasswordReset, db: Session = Depends(get_db)
):
    """Request password reset email"""

    # Check if user exists
    user = db.query(User).filter(User.email == reset_request.email).first()

    # Don't reveal if email exists or not (security)
    # In production, send email with reset link

    return APIResponse.ok(
        message="If the email exists, a password reset link has been sent"
    )


@router.post("/password-reset/confirm")
async def confirm_password_reset(
    reset_confirm: PasswordResetConfirm, db: Session = Depends(get_db)
):
    """Confirm password reset with token"""

    # Decode reset token
    try:
        payload = decode_token(reset_confirm.token)
    except HTTPException:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token",
        )

    # Get user
    user = db.query(User).filter(User.id == payload["sub"]).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    # Update password
    user.password_hash = hash_password(reset_confirm.new_password)
    db.commit()

    return APIResponse.ok(message="Password reset successfully")


# Export router for main app
__all__ = ["router"]
