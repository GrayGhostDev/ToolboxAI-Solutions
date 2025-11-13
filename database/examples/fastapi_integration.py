"""
FastAPI Integration Examples (2025 Standards)

Complete FastAPI endpoints using modern async database layer.

Run with:
    uvicorn database.examples.fastapi_integration:app --reload --port 8000
"""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from fastapi import Depends, FastAPI, HTTPException, Query, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.ext.asyncio import AsyncSession

from database.cache_modern import cache_result, invalidate_cache
from database.models.content_modern import (
    ContentStatus,
    ContentType,
    DifficultyLevel,
    EducationalContent,
)
from database.models.user_modern import User, UserRole, UserStatus
from database.repositories.base_repository import BaseRepository
from database.repositories.user_repository import UserRepository
from database.session_modern import db_manager, get_async_session

# Initialize FastAPI app
app = FastAPI(
    title="ToolboxAI Modern Database API",
    description="FastAPI integration with SQLAlchemy 2.0 async database",
    version="2.0.0",
)


# ============================================================================
# Pydantic Schemas (Request/Response Models)
# ============================================================================


class UserCreate(BaseModel):
    """Schema for creating a user."""

    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8)
    full_name: Optional[str] = None
    role: UserRole = UserRole.STUDENT
    bio: Optional[str] = None
    skills: List[str] = Field(default_factory=list)


class UserUpdate(BaseModel):
    """Schema for updating a user."""

    full_name: Optional[str] = None
    bio: Optional[str] = None
    skills: Optional[List[str]] = None
    status: Optional[UserStatus] = None


class UserResponse(BaseModel):
    """Schema for user response."""

    id: UUID
    email: str
    username: str
    full_name: Optional[str]
    role: UserRole
    status: UserStatus
    email_verified: bool
    created_at: datetime

    class Config:
        from_attributes = True


class UserProfileResponse(BaseModel):
    """Schema for user with profile."""

    id: UUID
    email: str
    username: str
    full_name: Optional[str]
    role: UserRole
    status: UserStatus
    bio: Optional[str] = None
    skills: List[str] = Field(default_factory=list)

    class Config:
        from_attributes = True


class ContentCreate(BaseModel):
    """Schema for creating content."""

    title: str = Field(..., min_length=1, max_length=255)
    slug: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    content: str
    content_type: ContentType
    difficulty_level: DifficultyLevel
    tags: List[str] = Field(default_factory=list)
    learning_objectives: List[str] = Field(default_factory=list)
    estimated_duration_minutes: Optional[int] = None


class ContentUpdate(BaseModel):
    """Schema for updating content."""

    title: Optional[str] = None
    description: Optional[str] = None
    content: Optional[str] = None
    status: Optional[ContentStatus] = None
    tags: Optional[List[str]] = None
    difficulty_level: Optional[DifficultyLevel] = None


class ContentResponse(BaseModel):
    """Schema for content response."""

    id: UUID
    title: str
    slug: str
    description: Optional[str]
    content_type: ContentType
    difficulty_level: DifficultyLevel
    status: ContentStatus
    author_id: UUID
    tags: List[str]
    view_count: int
    average_rating: Optional[float]
    created_at: datetime
    published_at: Optional[datetime]

    class Config:
        from_attributes = True


class PaginatedResponse(BaseModel):
    """Generic paginated response."""

    items: List[dict]
    total: int
    page: int
    page_size: int
    total_pages: int


# ============================================================================
# Dependency Functions
# ============================================================================


def hash_password(password: str) -> str:
    """Hash password (placeholder - use bcrypt in production)."""
    import hashlib

    return hashlib.sha256(password.encode()).hexdigest()


async def get_current_org_id() -> UUID:
    """
    Get current organization ID from auth context.

    In production, extract from JWT token or session.
    For demo, returns a fixed UUID.
    """
    # TODO: Extract from JWT token
    from uuid import uuid4

    return uuid4()


# ============================================================================
# Health Check Endpoints
# ============================================================================


@app.get("/health", tags=["Health"])
async def health_check():
    """Check API and database health."""
    db_healthy = await db_manager.health_check()

    return {
        "status": "healthy" if db_healthy else "unhealthy",
        "database": "connected" if db_healthy else "disconnected",
        "timestamp": datetime.utcnow().isoformat(),
    }


# ============================================================================
# User Endpoints
# ============================================================================


@app.post(
    "/users",
    response_model=UserProfileResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Users"],
)
async def create_user(
    user_data: UserCreate,
    session: AsyncSession = Depends(get_async_session),
    org_id: UUID = Depends(get_current_org_id),
):
    """
    Create a new user with profile.

    - **email**: Valid email address (must be unique)
    - **username**: Username (3-50 characters, must be unique)
    - **password**: Password (min 8 characters)
    - **role**: User role (student, teacher, admin, parent)
    """
    repo = UserRepository()

    # Check if user exists
    existing = await repo.get_by_email(session, user_data.email, org_id)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    # Create user with profile
    user = await repo.create_user_with_profile(
        session=session,
        organization_id=org_id,
        email=user_data.email,
        username=user_data.username,
        hashed_password=hash_password(user_data.password),
        full_name=user_data.full_name,
        role=user_data.role,
        bio=user_data.bio,
        skills=user_data.skills,
    )

    await session.commit()

    return UserProfileResponse(
        id=user.id,
        email=user.email,
        username=user.username,
        full_name=user.full_name,
        role=user.role,
        status=user.status,
        bio=user.profile.bio if user.profile else None,
        skills=user.profile.skills if user.profile else [],
    )


@app.get("/users", response_model=List[UserResponse], tags=["Users"])
async def list_users(
    role: Optional[UserRole] = None,
    status_filter: Optional[UserStatus] = Query(None, alias="status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    session: AsyncSession = Depends(get_async_session),
    org_id: UUID = Depends(get_current_org_id),
):
    """
    List users with optional filtering.

    - **role**: Filter by user role
    - **status**: Filter by user status
    - **skip**: Number of records to skip (pagination)
    - **limit**: Maximum records to return
    """
    repo = UserRepository()

    # Build filters
    filters = {"organization_id": org_id}
    if role:
        filters["role"] = role
    if status_filter:
        filters["status"] = status_filter

    users = await repo.find(
        session,
        filters=filters,
        skip=skip,
        limit=limit,
        order_by="created_at",
        descending=True,
    )

    return [UserResponse.model_validate(user) for user in users]


@app.get("/users/{user_id}", response_model=UserProfileResponse, tags=["Users"])
async def get_user(
    user_id: UUID,
    session: AsyncSession = Depends(get_async_session),
):
    """Get user by ID with profile information."""
    repo = UserRepository()

    user = await repo.get_by_id(session, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return UserProfileResponse(
        id=user.id,
        email=user.email,
        username=user.username,
        full_name=user.full_name,
        role=user.role,
        status=user.status,
        bio=user.profile.bio if user.profile else None,
        skills=user.profile.skills if user.profile else [],
    )


@app.patch("/users/{user_id}", response_model=UserResponse, tags=["Users"])
async def update_user(
    user_id: UUID,
    updates: UserUpdate,
    session: AsyncSession = Depends(get_async_session),
):
    """Update user information."""
    repo = UserRepository()

    # Get user
    user = await repo.get_by_id(session, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Update user fields
    update_data = updates.model_dump(exclude_unset=True)
    profile_fields = {"bio", "skills"}
    user_fields = {k: v for k, v in update_data.items() if k not in profile_fields}
    profile_updates = {k: v for k, v in update_data.items() if k in profile_fields}

    if user_fields:
        user = await repo.update(session, user_id, **user_fields)

    # Update profile if exists
    if profile_updates and user.profile:
        for key, value in profile_updates.items():
            setattr(user.profile, key, value)

    await session.commit()
    await session.refresh(user)

    return UserResponse.model_validate(user)


@app.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Users"])
async def delete_user(
    user_id: UUID,
    soft: bool = Query(True, description="Soft delete (keep data)"),
    session: AsyncSession = Depends(get_async_session),
):
    """
    Delete a user.

    - **soft**: If true, performs soft delete (keeps data). If false, permanently deletes.
    """
    repo = BaseRepository(User)

    deleted = await repo.delete(session, user_id, soft=soft)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    await session.commit()
    return None


@app.get("/users/statistics/overview", tags=["Users"])
@cache_result(prefix="user_stats", expire=300)
async def get_user_statistics(
    session: AsyncSession = Depends(get_async_session),
    org_id: UUID = Depends(get_current_org_id),
):
    """Get user statistics for organization (cached for 5 minutes)."""
    repo = UserRepository()

    stats = await repo.get_user_statistics(session, org_id)

    return stats


# ============================================================================
# Content Endpoints
# ============================================================================


@app.post(
    "/content",
    response_model=ContentResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Content"],
)
async def create_content(
    content_data: ContentCreate,
    session: AsyncSession = Depends(get_async_session),
    org_id: UUID = Depends(get_current_org_id),
):
    """Create new educational content."""
    repo = BaseRepository(EducationalContent)

    # Check for duplicate slug
    existing = await repo.find_one(
        session,
        filters={"organization_id": org_id, "slug": content_data.slug},
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Content with this slug already exists",
        )

    # Create content
    content = await repo.create(
        session=session,
        organization_id=org_id,
        author_id=org_id,  # TODO: Get from authenticated user
        status=ContentStatus.DRAFT,
        version=1,
        is_latest_version=True,
        **content_data.model_dump(),
    )

    await session.commit()

    return ContentResponse.model_validate(content)


@app.get("/content", response_model=List[ContentResponse], tags=["Content"])
async def list_content(
    content_type: Optional[ContentType] = None,
    difficulty: Optional[DifficultyLevel] = None,
    status_filter: Optional[ContentStatus] = Query(None, alias="status"),
    tag: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    session: AsyncSession = Depends(get_async_session),
    org_id: UUID = Depends(get_current_org_id),
):
    """
    List educational content with filtering.

    - **content_type**: Filter by content type
    - **difficulty**: Filter by difficulty level
    - **status**: Filter by status
    - **tag**: Filter by tag (partial match)
    """
    repo = BaseRepository(EducationalContent)

    # Build filters
    filters = {"organization_id": org_id, "is_latest_version": True}
    if content_type:
        filters["content_type"] = content_type
    if difficulty:
        filters["difficulty_level"] = difficulty
    if status_filter:
        filters["status"] = status_filter

    content_list = await repo.find(
        session,
        filters=filters,
        skip=skip,
        limit=limit,
        order_by="created_at",
        descending=True,
    )

    # Filter by tag if provided (PostgreSQL array contains)
    if tag:
        content_list = [c for c in content_list if tag.lower() in [t.lower() for t in c.tags]]

    return [ContentResponse.model_validate(c) for c in content_list]


@app.get("/content/{content_id}", response_model=ContentResponse, tags=["Content"])
async def get_content(
    content_id: UUID,
    session: AsyncSession = Depends(get_async_session),
):
    """Get content by ID and increment view count."""
    repo = BaseRepository(EducationalContent)

    content = await repo.get_by_id(session, content_id)
    if not content:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Content not found",
        )

    # Increment view count
    content.increment_views()
    await session.commit()

    return ContentResponse.model_validate(content)


@app.patch("/content/{content_id}", response_model=ContentResponse, tags=["Content"])
@invalidate_cache(prefix="content")
async def update_content(
    content_id: UUID,
    updates: ContentUpdate,
    session: AsyncSession = Depends(get_async_session),
):
    """Update content and invalidate cache."""
    repo = BaseRepository(EducationalContent)

    content = await repo.update(
        session,
        content_id,
        **updates.model_dump(exclude_unset=True),
    )

    if not content:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Content not found",
        )

    await session.commit()
    await session.refresh(content)

    return ContentResponse.model_validate(content)


@app.post("/content/{content_id}/publish", response_model=ContentResponse, tags=["Content"])
async def publish_content(
    content_id: UUID,
    session: AsyncSession = Depends(get_async_session),
    org_id: UUID = Depends(get_current_org_id),
):
    """Publish content (make publicly available)."""
    repo = BaseRepository(EducationalContent)

    content = await repo.get_by_id(session, content_id)
    if not content:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Content not found",
        )

    # Publish content
    content.publish(reviewer_id=org_id)  # TODO: Get from authenticated user
    await session.commit()
    await session.refresh(content)

    return ContentResponse.model_validate(content)


# ============================================================================
# Startup/Shutdown Events
# ============================================================================


@app.on_event("startup")
async def startup_event():
    """Initialize database connections on startup."""
    print("🚀 Starting FastAPI application...")
    print("📊 Database connection initialized")


@app.on_event("shutdown")
async def shutdown_event():
    """Close database connections on shutdown."""
    await db_manager.close()
    print("👋 FastAPI application shutdown complete")


# ============================================================================
# Example: Run the application
# ============================================================================

if __name__ == "__main__":
    import uvicorn

    uvicorn.invoke(
        "database.examples.fastapi_integration:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
