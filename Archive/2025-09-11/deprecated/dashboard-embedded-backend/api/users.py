"""
Users Management API Endpoints
"""

import uuid
from datetime import datetime
from typing import List, Optional

import bcrypt
from database import get_db
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from models import Class, School, User, UserRole
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session

from ._utils import now
from .auth import decode_token

# ==================== Router Setup ====================
router = APIRouter(prefix="/api/v1/users", tags=["users"])
security = HTTPBearer()

# ==================== Pydantic Schemas ====================


class UserCreate(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=100)
    password: str = Field(..., min_length=8, max_length=100)
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    display_name: Optional[str] = Field(None, max_length=200)
    role: str = Field(..., pattern="^(Admin|Teacher|Student|Parent)$")
    school_id: Optional[str] = None
    language: str = Field("en", max_length=5)
    timezone: str = Field("UTC", max_length=50)


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    username: Optional[str] = Field(None, min_length=3, max_length=100)
    password: Optional[str] = Field(None, min_length=8, max_length=100)
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    display_name: Optional[str] = Field(None, max_length=200)
    role: Optional[str] = Field(None, pattern="^(Admin|Teacher|Student|Parent)$")
    school_id: Optional[str] = None
    is_active: Optional[bool] = None
    language: Optional[str] = Field(None, max_length=5)
    timezone: Optional[str] = Field(None, max_length=50)


class UserResponse(BaseModel):
    id: str
    email: str
    username: str
    first_name: str
    last_name: str
    display_name: Optional[str]
    avatar_url: Optional[str]
    role: str
    school_id: Optional[str]
    school_name: Optional[str] = None
    class_ids: List[str] = []
    is_active: bool
    is_verified: bool
    total_xp: int
    level: int
    last_login: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    status: str  # "active", "suspended", or "pending"

    class Config:
        from_attributes = True


# ==================== Authentication ====================


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    """Verify JWT token and return current user"""
    try:
        payload = decode_token(credentials.credentials)
        user = db.query(User).filter(User.id == payload["sub"]).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found"
            )
        return user
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))


def require_admin(current_user: User = Depends(get_current_user)):
    """Require admin role for access"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required"
        )
    return current_user


def require_admin_or_teacher(current_user: User = Depends(get_current_user)):
    """Require admin or teacher role for access"""
    if current_user.role not in [UserRole.ADMIN, UserRole.TEACHER]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin or Teacher access required",
        )
    return current_user


# ==================== Helper Functions ====================


def hash_password(password: str) -> str:
    """Hash a password for storing"""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def get_user_status(user: User) -> str:
    """Determine user status based on flags"""
    if not user.is_active:
        return "suspended"
    elif not user.is_verified:
        return "pending"
    else:
        return "active"


def get_user_class_ids(user: User, db: Session) -> List[str]:
    """Get list of class IDs for a user"""
    if user.role == UserRole.TEACHER:
        # Get classes taught by teacher
        classes = db.query(Class).filter(Class.teacher_id == user.id).all()
        return [c.id for c in classes]
    elif user.role == UserRole.STUDENT:
        # Get enrolled classes
        from models.class_model import ClassEnrollment

        enrollments = (
            db.query(ClassEnrollment)
            .filter(
                ClassEnrollment.user_id == user.id, ClassEnrollment.is_active == True
            )
            .all()
        )
        return [e.class_id for e in enrollments]
    else:
        return []


# ==================== Endpoints ====================


@router.get("/", response_model=List[UserResponse])
async def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    role: Optional[str] = None,
    school_id: Optional[str] = None,
    is_active: Optional[bool] = None,
    search: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List all users with optional filtering"""
    query = db.query(User)

    # Apply filters
    if role:
        try:
            role_enum = UserRole[role.upper()]
            query = query.filter(User.role == role_enum)
        except KeyError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid role: {role}"
            )

    if school_id:
        query = query.filter(User.school_id == school_id)

    if is_active is not None:
        query = query.filter(User.is_active == is_active)

    if search:
        search_term = f"%{search}%"
        query = query.filter(
            (User.username.ilike(search_term))
            | (User.email.ilike(search_term))
            | (User.first_name.ilike(search_term))
            | (User.last_name.ilike(search_term))
            | (User.display_name.ilike(search_term))
        )

    # For non-admins, limit to their own school
    if current_user.role != UserRole.ADMIN and current_user.school_id:
        query = query.filter(User.school_id == current_user.school_id)

    users = query.offset(skip).limit(limit).all()

    # Convert to response model
    response = []
    for user in users:
        # Get school name if user has school_id
        school_name = None
        if user.school_id:
            school = db.query(School).filter(School.id == user.school_id).first()
            school_name = school.name if school else None

        user_dict = {
            "id": user.id,
            "email": user.email,
            "username": user.username,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "display_name": user.display_name or f"{user.first_name} {user.last_name}",
            "avatar_url": user.avatar_url,
            "role": user.role.value,
            "school_id": user.school_id,
            "school_name": school_name,
            "class_ids": get_user_class_ids(user, db),
            "is_active": user.is_active,
            "is_verified": user.is_verified,
            "total_xp": user.total_xp,
            "level": user.level,
            "last_login": user.last_login,
            "created_at": user.created_at,
            "updated_at": user.updated_at or user.created_at,
            "status": get_user_status(user),
        }
        response.append(UserResponse(**user_dict))

    return response


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get a specific user by ID"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    # Check permissions
    if current_user.role != UserRole.ADMIN:
        if current_user.id != user_id and current_user.school_id != user.school_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Access denied"
            )

    # Get school name if user has school_id
    school_name = None
    if user.school_id:
        school = db.query(School).filter(School.id == user.school_id).first()
        school_name = school.name if school else None

    return UserResponse(
        id=user.id,
        email=user.email,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name,
        display_name=user.display_name or f"{user.first_name} {user.last_name}",
        avatar_url=user.avatar_url,
        role=user.role.value,
        school_id=user.school_id,
        school_name=school_name,
        class_ids=get_user_class_ids(user, db),
        is_active=user.is_active,
        is_verified=user.is_verified,
        total_xp=user.total_xp,
        level=user.level,
        last_login=user.last_login,
        created_at=user.created_at,
        updated_at=user.updated_at or user.created_at,
        status=get_user_status(user),
    )


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate,
    current_user: User = Depends(require_admin_or_teacher),
    db: Session = Depends(get_db),
):
    """Create a new user (Admin or Teacher only)"""
    # Teachers can only create students in their school
    if current_user.role == UserRole.TEACHER:
        if user_data.role not in ["Student", "Parent"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Teachers can only create Student or Parent accounts",
            )
        if not current_user.school_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Teacher must be assigned to a school",
            )
        user_data.school_id = current_user.school_id

    # Check if username or email already exists
    existing_username = (
        db.query(User).filter(User.username == user_data.username).first()
    )
    if existing_username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Username already exists"
        )

    existing_email = db.query(User).filter(User.email == user_data.email).first()
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Email already exists"
        )

    # Create new user
    user_role = UserRole[user_data.role.upper()]
    new_user = User(
        id=str(uuid.uuid4()),
        email=user_data.email,
        username=user_data.username,
        password_hash=hash_password(user_data.password),
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        display_name=user_data.display_name,
        role=user_role,
        school_id=user_data.school_id,
        is_active=True,
        is_verified=False,
        total_xp=0,
        level=1,
        language=user_data.language,
        timezone=user_data.timezone,
        created_at=now(),
        updated_at=now(),
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Get school name if user has school_id
    school_name = None
    if new_user.school_id:
        school = db.query(School).filter(School.id == new_user.school_id).first()
        school_name = school.name if school else None

    return UserResponse(
        id=new_user.id,
        email=new_user.email,
        username=new_user.username,
        first_name=new_user.first_name,
        last_name=new_user.last_name,
        display_name=new_user.display_name
        or f"{new_user.first_name} {new_user.last_name}",
        avatar_url=new_user.avatar_url,
        role=new_user.role.value,
        school_id=new_user.school_id,
        school_name=school_name,
        class_ids=[],
        is_active=new_user.is_active,
        is_verified=new_user.is_verified,
        total_xp=new_user.total_xp,
        level=new_user.level,
        last_login=new_user.last_login,
        created_at=new_user.created_at,
        updated_at=new_user.updated_at or new_user.created_at,
        status=get_user_status(new_user),
    )


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str,
    user_data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update a user"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    # Check permissions
    if current_user.role != UserRole.ADMIN:
        if current_user.id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only update your own profile",
            )
        # Non-admins cannot change roles or active status
        if user_data.role is not None or user_data.is_active is not None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only admins can change role or active status",
            )

    # Update fields if provided
    update_dict = user_data.dict(exclude_unset=True)

    # Handle password hashing if password is being updated
    if "password" in update_dict:
        update_dict["password_hash"] = hash_password(update_dict["password"])
        del update_dict["password"]

    # Handle role conversion if role is being updated
    if "role" in update_dict:
        update_dict["role"] = UserRole[update_dict["role"].upper()]

    # Check for duplicate username/email if being changed
    if "username" in update_dict and update_dict["username"] != user.username:
        existing = (
            db.query(User).filter(User.username == update_dict["username"]).first()
        )
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already exists",
            )

    if "email" in update_dict and update_dict["email"] != user.email:
        existing = db.query(User).filter(User.email == update_dict["email"]).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Email already exists"
            )

    for field, value in update_dict.items():
        setattr(user, field, value)

    user.updated_at = now()
    db.commit()
    db.refresh(user)

    # Get school name if user has school_id
    school_name = None
    if user.school_id:
        school = db.query(School).filter(School.id == user.school_id).first()
        school_name = school.name if school else None

    return UserResponse(
        id=user.id,
        email=user.email,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name,
        display_name=user.display_name or f"{user.first_name} {user.last_name}",
        avatar_url=user.avatar_url,
        role=user.role.value,
        school_id=user.school_id,
        school_name=school_name,
        class_ids=get_user_class_ids(user, db),
        is_active=user.is_active,
        is_verified=user.is_verified,
        total_xp=user.total_xp,
        level=user.level,
        last_login=user.last_login,
        created_at=user.created_at,
        updated_at=user.updated_at or user.created_at,
        status=get_user_status(user),
    )


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: str,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Delete a user (Admin only)"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    # Prevent deleting yourself
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account",
        )

    # Soft delete by deactivating
    user.is_active = False
    user.updated_at = now()
    db.commit()

    return None


@router.put("/{user_id}/suspend", response_model=UserResponse)
async def suspend_user(
    user_id: str,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Suspend or unsuspend a user (Admin only)"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    # Prevent suspending yourself
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot suspend your own account",
        )

    # Toggle active status
    user.is_active = not user.is_active
    user.updated_at = now()
    db.commit()
    db.refresh(user)

    # Get school name if user has school_id
    school_name = None
    if user.school_id:
        school = db.query(School).filter(School.id == user.school_id).first()
        school_name = school.name if school else None

    return UserResponse(
        id=user.id,
        email=user.email,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name,
        display_name=user.display_name or f"{user.first_name} {user.last_name}",
        avatar_url=user.avatar_url,
        role=user.role.value,
        school_id=user.school_id,
        school_name=school_name,
        class_ids=get_user_class_ids(user, db),
        is_active=user.is_active,
        is_verified=user.is_verified,
        total_xp=user.total_xp,
        level=user.level,
        last_login=user.last_login,
        created_at=user.created_at,
        updated_at=user.updated_at,
        status=get_user_status(user),
    )


@router.get("/me/profile", response_model=UserResponse)
async def get_my_profile(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """Get current user's profile"""
    # Get school name if user has school_id
    school_name = None
    if current_user.school_id:
        school = db.query(School).filter(School.id == current_user.school_id).first()
        school_name = school.name if school else None

    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        username=current_user.username,
        first_name=current_user.first_name,
        last_name=current_user.last_name,
        display_name=current_user.display_name
        or f"{current_user.first_name} {current_user.last_name}",
        avatar_url=current_user.avatar_url,
        role=current_user.role.value,
        school_id=current_user.school_id,
        school_name=school_name,
        class_ids=get_user_class_ids(current_user, db),
        is_active=current_user.is_active,
        is_verified=current_user.is_verified,
        total_xp=current_user.total_xp,
        level=current_user.level,
        last_login=current_user.last_login,
        created_at=current_user.created_at,
        updated_at=current_user.updated_at or current_user.created_at,
        status=get_user_status(current_user),
    )
