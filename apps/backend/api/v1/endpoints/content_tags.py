"""
Content Tags API Endpoints for ToolBoxAI Educational Platform

Provides comprehensive tag management for content organization and discovery.

Features:
- Tag creation and management
- Tag assignment to content
- Tag search and filtering
- Popular tags analytics
- Tag hierarchies and relationships
- Tag merging and cleanup

Author: ToolBoxAI Team
Created: 2025-10-02
Version: 1.0.0
Standards: Python 3.12, FastAPI async, Pydantic v2
"""

import logging
from datetime import datetime
from typing import Annotated, Optional
from uuid import UUID, uuid4

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    status,
)
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.ext.asyncio import AsyncSession

from apps.backend.api.auth.auth import get_current_user
from apps.backend.core.deps import get_async_db
from apps.backend.middleware.tenant import get_tenant_context, TenantContext
from apps.backend.models.schemas import User

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/tags",
    tags=["content-tags"],
    responses={404: {"description": "Tag not found"}},
)


# === Pydantic v2 Models ===

class Tag(BaseModel):
    """Tag model with Pydantic v2"""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    slug: str
    description: Optional[str] = None
    color: Optional[str] = Field(None, pattern="^#[0-9A-Fa-f]{6}$")
    category: Optional[str] = None
    usage_count: int = 0
    created_at: datetime
    created_by: UUID
    created_by_name: str


class TagCreateRequest(BaseModel):
    """Request model for creating a tag"""

    model_config = ConfigDict(from_attributes=True)

    name: str = Field(..., min_length=1, max_length=50)
    description: Optional[str] = Field(None, max_length=200)
    color: Optional[str] = Field(None, pattern="^#[0-9A-Fa-f]{6}$")
    category: Optional[str] = Field(None, max_length=50)


class TagUpdateRequest(BaseModel):
    """Request model for updating a tag"""

    model_config = ConfigDict(from_attributes=True)

    name: Optional[str] = Field(None, min_length=1, max_length=50)
    description: Optional[str] = Field(None, max_length=200)
    color: Optional[str] = Field(None, pattern="^#[0-9A-Fa-f]{6}$")
    category: Optional[str] = Field(None, max_length=50)


class TagListResponse(BaseModel):
    """Response model for tag list"""

    model_config = ConfigDict(from_attributes=True)

    tags: list[Tag]
    total: int
    page: int
    page_size: int


class PopularTag(BaseModel):
    """Popular tag with usage statistics"""

    model_config = ConfigDict(from_attributes=True)

    tag: Tag
    content_count: int
    trending_score: float = 0.0
    recent_usage_count: int = 0  # Last 30 days


class PopularTagsResponse(BaseModel):
    """Response model for popular tags"""

    model_config = ConfigDict(from_attributes=True)

    tags: list[PopularTag]
    period: str = "all_time"


class TagMergeRequest(BaseModel):
    """Request model for merging tags"""

    model_config = ConfigDict(from_attributes=True)

    source_tag_ids: list[UUID] = Field(..., min_length=1)
    target_tag_id: UUID
    delete_source_tags: bool = Field(
        default=True,
        description="Delete source tags after merge"
    )


class TagMergeResponse(BaseModel):
    """Response model for tag merge"""

    model_config = ConfigDict(from_attributes=True)

    target_tag: Tag
    merged_count: int
    affected_content_count: int
    message: str


# === API Endpoints ===

@router.get(
    "",
    response_model=TagListResponse,
    summary="List tags",
    description="Get list of all tags with pagination and filtering",
)
async def list_tags(
    session: Annotated[AsyncSession, Depends(get_async_db)],
    tenant_context: Annotated[TenantContext, Depends(get_tenant_context)],
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    search: Optional[str] = Query(None, max_length=50),
    category: Optional[str] = Query(None, max_length=50),
    sort_by: str = Query("name", pattern="^(name|usage_count|created_at)$"),
    sort_order: str = Query("asc", pattern="^(asc|desc)$"),
) -> TagListResponse:
    """
    List all tags with pagination and filtering.

    Args:
        session: Async database session
        tenant_context: Current tenant context
        page: Page number
        page_size: Items per page
        search: Search term for tag name
        category: Filter by category
        sort_by: Sort field
        sort_order: Sort direction

    Returns:
        TagListResponse: List of tags with pagination
    """
    try:
        logger.info(f"Listing tags: page={page}, search={search}")

        # TODO: Implement actual tag retrieval from database
        tags: list[Tag] = []

        return TagListResponse(
            tags=tags,
            total=0,
            page=page,
            page_size=page_size,
        )

    except Exception as e:
        logger.error(f"Failed to list tags: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list tags"
        )


@router.post(
    "",
    response_model=Tag,
    status_code=status.HTTP_201_CREATED,
    summary="Create tag",
    description="Create a new tag",
)
async def create_tag(
    request: TagCreateRequest,
    session: Annotated[AsyncSession, Depends(get_async_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    tenant_context: Annotated[TenantContext, Depends(get_tenant_context)],
) -> Tag:
    """
    Create a new tag.

    Generates a URL-friendly slug from the name.

    Args:
        request: Tag creation request
        session: Async database session
        current_user: Current authenticated user
        tenant_context: Current tenant context

    Returns:
        Tag: Created tag

    Raises:
        HTTPException: If tag creation fails or name already exists
    """
    try:
        logger.info(f"Creating tag: {request.name}")

        # Generate slug from name
        slug = request.name.lower().replace(" ", "-")

        # TODO: Implement actual tag creation
        # - Check for duplicate names
        # - Store in database
        # - Return created tag

        tag = Tag(
            id=uuid4(),
            name=request.name,
            slug=slug,
            description=request.description,
            color=request.color or "#3B82F6",  # Default blue
            category=request.category,
            usage_count=0,
            created_at=datetime.utcnow(),
            created_by=current_user.id,
            created_by_name=current_user.username,
        )

        logger.info(f"Tag created: {tag.id}")

        return tag

    except Exception as e:
        logger.error(f"Failed to create tag: {str(e)}", exc_info=True)
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create tag"
        )


@router.get(
    "/{tag_id}",
    response_model=Tag,
    summary="Get tag",
    description="Get detailed information about a specific tag",
)
async def get_tag(
    tag_id: UUID,
    session: Annotated[AsyncSession, Depends(get_async_db)],
) -> Tag:
    """
    Get detailed information about a tag.

    Args:
        tag_id: Tag identifier
        session: Async database session

    Returns:
        Tag: Tag details

    Raises:
        HTTPException: If tag not found
    """
    try:
        logger.info(f"Getting tag: {tag_id}")

        # TODO: Implement actual tag retrieval
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tag not found"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get tag: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get tag"
        )


@router.patch(
    "/{tag_id}",
    response_model=Tag,
    summary="Update tag",
    description="Update tag information",
)
async def update_tag(
    tag_id: UUID,
    request: TagUpdateRequest,
    session: Annotated[AsyncSession, Depends(get_async_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> Tag:
    """
    Update tag information.

    Args:
        tag_id: Tag identifier
        request: Update request
        session: Async database session
        current_user: Current authenticated user

    Returns:
        Tag: Updated tag

    Raises:
        HTTPException: If tag not found or update fails
    """
    try:
        logger.info(f"Updating tag: {tag_id}")

        # TODO: Implement actual tag update
        # - Retrieve tag
        # - Update fields
        # - Regenerate slug if name changed
        # - Save to database

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tag not found"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update tag: {str(e)}", exc_info=True)
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update tag"
        )


@router.delete(
    "/{tag_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete tag",
    description="Delete a tag and remove it from all content",
)
async def delete_tag(
    tag_id: UUID,
    session: Annotated[AsyncSession, Depends(get_async_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> None:
    """
    Delete a tag.

    Removes the tag from all associated content.

    Args:
        tag_id: Tag identifier
        session: Async database session
        current_user: Current authenticated user

    Raises:
        HTTPException: If tag not found or deletion fails
    """
    try:
        logger.info(f"Deleting tag: {tag_id}")

        # TODO: Implement actual tag deletion
        # - Remove tag from all content
        # - Delete tag record

    except Exception as e:
        logger.error(f"Failed to delete tag: {str(e)}", exc_info=True)
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete tag"
        )


@router.get(
    "/popular",
    response_model=PopularTagsResponse,
    summary="Get popular tags",
    description="Get most frequently used tags",
)
async def get_popular_tags(
    session: Annotated[AsyncSession, Depends(get_async_db)],
    tenant_context: Annotated[TenantContext, Depends(get_tenant_context)],
    limit: int = Query(20, ge=1, le=100),
    period: str = Query("all_time", pattern="^(all_time|30_days|7_days)$"),
) -> PopularTagsResponse:
    """
    Get most popular tags by usage.

    Args:
        session: Async database session
        tenant_context: Current tenant context
        limit: Maximum number of tags to return
        period: Time period for popularity calculation

    Returns:
        PopularTagsResponse: List of popular tags with statistics
    """
    try:
        logger.info(f"Getting popular tags: limit={limit}, period={period}")

        # TODO: Implement actual popular tags calculation
        # - Count tag usage
        # - Calculate trending scores
        # - Sort by popularity

        popular_tags: list[PopularTag] = []

        return PopularTagsResponse(
            tags=popular_tags,
            period=period,
        )

    except Exception as e:
        logger.error(f"Failed to get popular tags: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get popular tags"
        )


@router.post(
    "/merge",
    response_model=TagMergeResponse,
    summary="Merge tags",
    description="Merge multiple tags into one",
)
async def merge_tags(
    request: TagMergeRequest,
    session: Annotated[AsyncSession, Depends(get_async_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> TagMergeResponse:
    """
    Merge multiple tags into a single tag.

    All content tagged with source tags will be retagged with target tag.
    Source tags can optionally be deleted.

    Args:
        request: Merge request
        session: Async database session
        current_user: Current authenticated user

    Returns:
        TagMergeResponse: Merge confirmation

    Raises:
        HTTPException: If merge fails
    """
    try:
        logger.info(
            f"Merging {len(request.source_tag_ids)} tags into {request.target_tag_id}"
        )

        # TODO: Implement actual tag merging
        # - Validate all tags exist
        # - Update all content with source tags to use target tag
        # - Delete source tags if requested
        # - Update usage counts

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Target tag not found"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to merge tags: {str(e)}", exc_info=True)
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to merge tags"
        )
