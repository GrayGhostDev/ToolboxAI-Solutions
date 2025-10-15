"""
Example: Content API with RBAC Enforcement

This file demonstrates how to apply RBAC decorators to API endpoints
for comprehensive permission management.

BEFORE (Basic role checking):
    @router.post("/content")
    async def create_content(user: User = Depends(require_teacher)):
        # Simple role check only
        pass

AFTER (Fine-grained RBAC):
    @router.post("/content")
    @require_permission("content:create:organization")
    async def create_content(user: User = Depends(get_current_user)):
        # Permission-based with organization scope
        pass
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID

from database.models import User, EducationalContent
from database.connection import get_session
from apps.backend.core.deps import get_current_user, get_current_organization_id
from apps.backend.core.security.rbac_decorators import (
    require_permission,
    require_permissions,
    require_resource_access,
    require_organization_access,
    require_admin,
    require_teacher
)
from pydantic import BaseModel


router = APIRouter(prefix="/content", tags=["content-rbac-example"])


# ============================================================================
# Pydantic Models
# ============================================================================

class ContentCreate(BaseModel):
    title: str
    description: str
    content_type: str
    difficulty_level: str


class ContentUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None


class ContentResponse(BaseModel):
    id: int
    title: str
    description: str
    created_by: int
    organization_id: UUID
    status: str


# ============================================================================
# RBAC-Protected Endpoints
# ============================================================================

@router.get("/", response_model=List[ContentResponse])
@require_permission("content:read:organization")
async def list_content(
    skip: int = 0,
    limit: int = 100,
    user: User = Depends(get_current_user),
    org_id: UUID = Depends(get_current_organization_id),
    db: Session = Depends(get_session)
):
    """
    List all content in user's organization.

    Permissions: content:read:organization
    - Students: Can read content in their organization
    - Teachers: Can read all content in organization
    - Admins: Can read all content (any organization)
    """
    # Query automatically scoped by organization (via middleware or decorator)
    contents = db.query(EducationalContent).filter(
        EducationalContent.organization_id == org_id
    ).offset(skip).limit(limit).all()

    return contents


@router.post("/", response_model=ContentResponse, status_code=status.HTTP_201_CREATED)
@require_permission("content:create:organization")
async def create_content(
    content_data: ContentCreate,
    user: User = Depends(get_current_user),
    org_id: UUID = Depends(get_current_organization_id),
    db: Session = Depends(get_session)
):
    """
    Create new educational content.

    Permissions: content:create:organization
    - Students: Cannot create content
    - Teachers: Can create content in their organization
    - Admins: Can create content in any organization
    """
    content = EducationalContent(
        **content_data.dict(),
        created_by=user.id,
        organization_id=org_id,
        status="draft"
    )

    db.add(content)
    db.commit()
    db.refresh(content)

    return content


@router.get("/{content_id}", response_model=ContentResponse)
@require_resource_access("content", "read")
async def get_content(
    content_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_session)
):
    """
    Get specific content by ID.

    Permissions: Automatically checked based on scope
    - Students: Can read content in their organization
    - Teachers: Can read content in their organization
    - Admins: Can read any content

    The @require_resource_access decorator automatically:
    1. Checks user's permission scope (own/organization/all)
    2. Validates organization membership
    3. Returns 404 if not found, 403 if no access
    """
    content = db.query(EducationalContent).filter_by(id=content_id).first()

    if not content:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Content not found"
        )

    return content


@router.put("/{content_id}", response_model=ContentResponse)
@require_resource_access("content", "update")
async def update_content(
    content_id: int,
    content_data: ContentUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_session)
):
    """
    Update existing content.

    Permissions: content:update:own or content:update:organization
    - Students: Cannot update content
    - Teachers: Can update their own content
    - Admins: Can update any content

    Ownership is automatically validated by @require_resource_access
    """
    content = db.query(EducationalContent).filter_by(id=content_id).first()

    if not content:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Content not found"
        )

    # Update fields
    for key, value in content_data.dict(exclude_unset=True).items():
        setattr(content, key, value)

    db.commit()
    db.refresh(content)

    return content


@router.delete("/{content_id}", status_code=status.HTTP_204_NO_CONTENT)
@require_resource_access("content", "delete")
async def delete_content(
    content_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_session)
):
    """
    Delete content.

    Permissions: content:delete:own
    - Students: Cannot delete content
    - Teachers: Can delete their own content
    - Admins: Can delete any content
    """
    content = db.query(EducationalContent).filter_by(id=content_id).first()

    if not content:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Content not found"
        )

    db.delete(content)
    db.commit()

    return None


@router.post("/{content_id}/publish")
@require_permissions(
    ["content:publish:organization", "content:publish:all"],
    require_all=False
)
async def publish_content(
    content_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_session)
):
    """
    Publish content (make it available to students).

    Permissions: content:publish:organization
    - Students: Cannot publish content
    - Teachers: Can publish content in their organization
    - Admins: Can publish any content

    Uses @require_permissions to allow either organization or all scope.
    """
    content = db.query(EducationalContent).filter_by(id=content_id).first()

    if not content:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Content not found"
        )

    content.status = "published"
    db.commit()
    db.refresh(content)

    return {"message": "Content published successfully", "content": content}


@router.get("/admin/all", response_model=List[ContentResponse])
@require_admin
async def list_all_content_admin(
    skip: int = 0,
    limit: int = 100,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_session)
):
    """
    List ALL content across all organizations (admin only).

    Permissions: Admin role required
    - Students: Access denied
    - Teachers: Access denied
    - Admins: Full access

    Uses @require_admin convenience decorator for admin-only endpoints.
    """
    contents = db.query(EducationalContent).offset(skip).limit(limit).all()
    return contents


# ============================================================================
# Multiple Permission Example
# ============================================================================

@router.post("/{content_id}/clone")
@require_permissions([
    "content:read:organization",
    "content:create:organization"
], require_all=True)
async def clone_content(
    content_id: int,
    user: User = Depends(get_current_user),
    org_id: UUID = Depends(get_current_organization_id),
    db: Session = Depends(get_session)
):
    """
    Clone existing content to create new instance.

    Permissions: Requires BOTH
    - content:read:organization (to read source)
    - content:create:organization (to create clone)

    Uses @require_permissions with require_all=True to enforce multiple permissions.
    """
    source_content = db.query(EducationalContent).filter_by(id=content_id).first()

    if not source_content:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Source content not found"
        )

    # Create clone
    cloned_content = EducationalContent(
        title=f"{source_content.title} (Copy)",
        description=source_content.description,
        content_type=source_content.content_type,
        difficulty_level=source_content.difficulty_level,
        created_by=user.id,
        organization_id=org_id,
        status="draft"
    )

    db.add(cloned_content)
    db.commit()
    db.refresh(cloned_content)

    return {
        "message": "Content cloned successfully",
        "original_id": content_id,
        "clone_id": cloned_content.id,
        "content": cloned_content
    }


# ============================================================================
# Organization Context Example
# ============================================================================

@router.get("/stats/organization")
@require_organization_access()
@require_permission("analytics:read:organization")
async def get_organization_content_stats(
    user: User = Depends(get_current_user),
    org_id: UUID = Depends(get_current_organization_id),
    db: Session = Depends(get_session)
):
    """
    Get content statistics for user's organization.

    Permissions:
    - Requires organization membership (@require_organization_access)
    - Requires analytics:read:organization permission

    Demonstrates combining multiple decorators for layered security.
    """
    total_content = db.query(EducationalContent).filter(
        EducationalContent.organization_id == org_id
    ).count()

    published_content = db.query(EducationalContent).filter(
        EducationalContent.organization_id == org_id,
        EducationalContent.status == "published"
    ).count()

    draft_content = db.query(EducationalContent).filter(
        EducationalContent.organization_id == org_id,
        EducationalContent.status == "draft"
    ).count()

    return {
        "organization_id": str(org_id),
        "total_content": total_content,
        "published": published_content,
        "drafts": draft_content,
        "publish_rate": published_content / total_content if total_content > 0 else 0
    }
