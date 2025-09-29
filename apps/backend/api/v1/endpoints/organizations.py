"""
Organizations API Endpoints

Provides RESTful API endpoints for managing organizations in the multi-tenant
ToolBoxAI Educational Platform. Handles organization CRUD operations,
member management, invitations, and subscription management.
"""

import logging
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field, validator
from sqlalchemy.orm import Session

from apps.backend.api.auth.auth import (
    get_current_user,
    get_current_organization,
    get_current_user_with_organization,
    require_organization_role,
    create_organization_token,
    AuthorizationError
)
from apps.backend.models.schemas import User
from apps.backend.middleware.tenant import (
    get_tenant_context,
    require_tenant_context,
    TenantContext
)
from database.models.tenant import (
    Organization,
    OrganizationStatus,
    SubscriptionTier,
    OrganizationInvitation
)

# Database session dependency would be imported here
# from apps.backend.database.session import get_db

logger = logging.getLogger(__name__)

router = APIRouter()


# === REQUEST/RESPONSE MODELS ===

class OrganizationCreateRequest(BaseModel):
    """Request model for creating a new organization"""
    name: str = Field(..., min_length=2, max_length=200, description="Organization name")
    slug: str = Field(..., min_length=2, max_length=100, description="URL-friendly identifier")
    display_name: Optional[str] = Field(None, max_length=250, description="Display name")
    description: Optional[str] = Field(None, description="Organization description")
    website: Optional[str] = Field(None, max_length=500, description="Organization website")
    email: Optional[str] = Field(None, max_length=255, description="Contact email")
    phone: Optional[str] = Field(None, max_length=50, description="Contact phone")
    organization_type: str = Field("education", description="Organization type")
    industry: Optional[str] = Field(None, max_length=100, description="Industry")
    size_category: Optional[str] = Field(None, max_length=50, description="Organization size")
    timezone: str = Field("UTC", max_length=100, description="Organization timezone")
    locale: str = Field("en-US", max_length=10, description="Organization locale")

    @validator('slug')
    def validate_slug(cls, v):
        """Validate slug format"""
        import re
        if not re.match(r'^[a-z0-9-]+$', v):
            raise ValueError('Slug must contain only lowercase letters, numbers, and hyphens')
        return v


class OrganizationUpdateRequest(BaseModel):
    """Request model for updating an organization"""
    name: Optional[str] = Field(None, min_length=2, max_length=200)
    display_name: Optional[str] = Field(None, max_length=250)
    description: Optional[str] = Field(None)
    website: Optional[str] = Field(None, max_length=500)
    email: Optional[str] = Field(None, max_length=255)
    phone: Optional[str] = Field(None, max_length=50)
    timezone: Optional[str] = Field(None, max_length=100)
    locale: Optional[str] = Field(None, max_length=10)


class OrganizationResponse(BaseModel):
    """Response model for organization data"""
    id: str
    name: str
    slug: str
    display_name: Optional[str]
    description: Optional[str]
    website: Optional[str]
    email: Optional[str]
    organization_type: str
    subscription_tier: str
    status: str
    is_active: bool
    is_trial: bool
    trial_days_remaining: Optional[int]
    usage_percentage: Dict[str, float]
    settings: Dict[str, Any]
    features: List[str]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class OrganizationMemberResponse(BaseModel):
    """Response model for organization member"""
    id: str
    username: str
    email: str
    role: str
    organization_role: str
    joined_at: datetime
    last_active: Optional[datetime]
    is_active: bool

    class Config:
        from_attributes = True


class InvitationCreateRequest(BaseModel):
    """Request model for creating organization invitations"""
    email: str = Field(..., max_length=255, description="Email address to invite")
    role: str = Field("member", description="Role to assign (admin, manager, teacher, member)")
    invitation_message: Optional[str] = Field(None, description="Custom invitation message")

    @validator('role')
    def validate_role(cls, v):
        """Validate role value"""
        allowed_roles = ["admin", "manager", "teacher", "member"]
        if v not in allowed_roles:
            raise ValueError(f'Role must be one of: {", ".join(allowed_roles)}')
        return v


class InvitationResponse(BaseModel):
    """Response model for organization invitation"""
    id: str
    email: str
    role: str
    invitation_token: str
    expires_at: datetime
    is_pending: bool
    is_expired: bool
    is_valid: bool
    invited_by_id: str
    created_at: datetime

    class Config:
        from_attributes = True


class SubscriptionUpdateRequest(BaseModel):
    """Request model for updating subscription"""
    subscription_tier: str = Field(..., description="New subscription tier")
    max_users: Optional[int] = Field(None, gt=0, description="Maximum users")
    max_classes: Optional[int] = Field(None, ge=0, description="Maximum classes")
    max_storage_gb: Optional[float] = Field(None, ge=0, description="Maximum storage in GB")
    max_api_calls_per_month: Optional[int] = Field(None, gt=0, description="Maximum API calls per month")

    @validator('subscription_tier')
    def validate_subscription_tier(cls, v):
        """Validate subscription tier"""
        allowed_tiers = ["free", "basic", "professional", "enterprise", "education"]
        if v not in allowed_tiers:
            raise ValueError(f'Subscription tier must be one of: {", ".join(allowed_tiers)}')
        return v


# === HELPER FUNCTIONS ===

def get_mock_db_session():
    """Mock database session for development. Replace with real DB session."""
    class MockSession:
        def query(self, model):
            return MockQuery()
        def add(self, obj):
            pass
        def commit(self):
            pass
        def refresh(self, obj):
            pass
        def close(self):
            pass

    class MockQuery:
        def filter(self, *args):
            return self
        def first(self):
            return None
        def all(self):
            return []

    return MockSession()


def create_mock_organization(request: OrganizationCreateRequest, user_id: str) -> OrganizationResponse:
    """Create a mock organization for development"""
    org_id = str(uuid.uuid4())

    return OrganizationResponse(
        id=org_id,
        name=request.name,
        slug=request.slug,
        display_name=request.display_name,
        description=request.description,
        website=request.website,
        email=request.email,
        organization_type=request.organization_type,
        subscription_tier="trial",
        status="trial",
        is_active=True,
        is_trial=True,
        trial_days_remaining=14,
        usage_percentage={
            "users": 0.0,
            "classes": 0.0,
            "storage": 0.0,
            "api_calls": 0.0,
            "roblox_sessions": 0.0
        },
        settings={},
        features=["basic_content_generation", "basic_analytics"],
        created_at=datetime.now(timezone.utc),
        updated_at=None
    )


# === API ENDPOINTS ===

@router.get("/current", response_model=OrganizationResponse)
async def get_current_organization_info(
    current_user: User = Depends(get_current_user),
    organization_id: Optional[str] = Depends(get_current_organization),
    # db: Session = Depends(get_db)  # Uncomment when DB is available
):
    """
    Get current organization information from JWT token context.

    Returns the organization information for the organization ID found in the
    current user's JWT token. If no organization context is available,
    returns an error.
    """
    if not organization_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No organization context found in token"
        )

    # Mock implementation - replace with real database query
    db = get_mock_db_session()

    # In production:
    # organization = db.query(Organization).filter(
    #     Organization.id == organization_id,
    #     Organization.is_active == True
    # ).first()

    organization = None  # Mock result

    if not organization:
        # Return mock data for development
        logger.info(f"Returning mock organization data for ID: {organization_id}")
        return OrganizationResponse(
            id=organization_id,
            name="Development Organization",
            slug="dev-org",
            display_name="Development Organization",
            description="Mock organization for development",
            website="https://dev.toolboxai.com",
            email="dev@toolboxai.com",
            organization_type="education",
            subscription_tier="professional",
            status="active",
            is_active=True,
            is_trial=False,
            trial_days_remaining=None,
            usage_percentage={
                "users": 25.0,
                "classes": 40.0,
                "storage": 15.0,
                "api_calls": 30.0,
                "roblox_sessions": 20.0
            },
            settings={
                "auto_backup": True,
                "email_notifications": True,
                "api_rate_limit": 1000
            },
            features=[
                "content_generation",
                "advanced_analytics",
                "custom_branding",
                "api_access",
                "priority_support"
            ],
            created_at=datetime.now(timezone.utc) - timedelta(days=30),
            updated_at=datetime.now(timezone.utc) - timedelta(days=1)
        )

    return OrganizationResponse.from_orm(organization)


@router.post("", response_model=OrganizationResponse, status_code=status.HTTP_201_CREATED)
async def create_organization(
    request: OrganizationCreateRequest,
    current_user: User = Depends(get_current_user),
    # db: Session = Depends(get_db)  # Uncomment when DB is available
):
    """
    Create a new organization.

    Creates a new organization with the requesting user as the admin.
    The user will receive a new JWT token with the organization context.
    """
    db = get_mock_db_session()

    # Check if slug is already taken (in production)
    # existing_org = db.query(Organization).filter(Organization.slug == request.slug).first()
    # if existing_org:
    #     raise HTTPException(
    #         status_code=status.HTTP_409_CONFLICT,
    #         detail=f"Organization with slug '{request.slug}' already exists"
    #     )

    # Create organization (mock implementation)
    organization = create_mock_organization(request, current_user.id)

    logger.info(
        f"Organization created: {organization.id} by user {current_user.id}",
        extra={
            "organization_id": organization.id,
            "user_id": current_user.id,
            "organization_name": organization.name
        }
    )

    return organization


@router.get("/{organization_id}", response_model=OrganizationResponse)
async def get_organization(
    organization_id: str,
    current_user: User = Depends(require_organization_role("member", organization_id)),
    # db: Session = Depends(get_db)  # Uncomment when DB is available
):
    """
    Get organization information by ID.

    Requires the user to be a member of the specified organization
    or be a super admin.
    """
    db = get_mock_db_session()

    # In production:
    # organization = db.query(Organization).filter(
    #     Organization.id == organization_id,
    #     Organization.is_active == True
    # ).first()

    organization = None  # Mock result

    if not organization:
        # Return mock data for development
        return OrganizationResponse(
            id=organization_id,
            name=f"Organization {organization_id[:8]}",
            slug=f"org-{organization_id[:8]}",
            display_name=f"Organization {organization_id[:8]}",
            description="Mock organization data",
            website=None,
            email=f"contact@org-{organization_id[:8]}.com",
            organization_type="education",
            subscription_tier="basic",
            status="active",
            is_active=True,
            is_trial=False,
            trial_days_remaining=None,
            usage_percentage={
                "users": 60.0,
                "classes": 30.0,
                "storage": 45.0,
                "api_calls": 75.0,
                "roblox_sessions": 25.0
            },
            settings={},
            features=["content_generation", "basic_analytics"],
            created_at=datetime.now(timezone.utc) - timedelta(days=60),
            updated_at=datetime.now(timezone.utc) - timedelta(days=5)
        )

    return OrganizationResponse.from_orm(organization)


@router.patch("/{organization_id}", response_model=OrganizationResponse)
async def update_organization(
    organization_id: str,
    request: OrganizationUpdateRequest,
    current_user: User = Depends(require_organization_role("admin", organization_id)),
    # db: Session = Depends(get_db)  # Uncomment when DB is available
):
    """
    Update organization information.

    Requires admin role in the organization.
    """
    db = get_mock_db_session()

    # In production:
    # organization = db.query(Organization).filter(
    #     Organization.id == organization_id,
    #     Organization.is_active == True
    # ).first()

    organization = None  # Mock result

    if not organization:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )

    # Update fields (mock implementation)
    logger.info(
        f"Organization updated: {organization_id} by user {current_user.id}",
        extra={
            "organization_id": organization_id,
            "user_id": current_user.id,
            "updated_fields": request.dict(exclude_unset=True)
        }
    )

    # Return updated organization (mock)
    return OrganizationResponse(
        id=organization_id,
        name=request.name or f"Updated Organization {organization_id[:8]}",
        slug=f"org-{organization_id[:8]}",
        display_name=request.display_name or f"Updated Organization {organization_id[:8]}",
        description=request.description or "Updated organization",
        website=request.website,
        email=request.email,
        organization_type="education",
        subscription_tier="professional",
        status="active",
        is_active=True,
        is_trial=False,
        trial_days_remaining=None,
        usage_percentage={
            "users": 60.0,
            "classes": 30.0,
            "storage": 45.0,
            "api_calls": 75.0,
            "roblox_sessions": 25.0
        },
        settings={},
        features=["content_generation", "advanced_analytics"],
        created_at=datetime.now(timezone.utc) - timedelta(days=60),
        updated_at=datetime.now(timezone.utc)
    )


@router.get("/{organization_id}/members", response_model=List[OrganizationMemberResponse])
async def get_organization_members(
    organization_id: str,
    current_user: User = Depends(require_organization_role("member", organization_id)),
    limit: int = Query(50, ge=1, le=100, description="Number of members to return"),
    offset: int = Query(0, ge=0, description="Number of members to skip"),
    # db: Session = Depends(get_db)  # Uncomment when DB is available
):
    """
    Get organization members.

    Requires member role or higher in the organization.
    """
    db = get_mock_db_session()

    # In production:
    # members = db.query(User).join(OrganizationMember).filter(
    #     OrganizationMember.organization_id == organization_id,
    #     User.is_active == True
    # ).offset(offset).limit(limit).all()

    # Return mock members
    mock_members = [
        OrganizationMemberResponse(
            id=str(uuid.uuid4()),
            username="admin_user",
            email="admin@organization.com",
            role="teacher",
            organization_role="admin",
            joined_at=datetime.now(timezone.utc) - timedelta(days=30),
            last_active=datetime.now(timezone.utc) - timedelta(hours=2),
            is_active=True
        ),
        OrganizationMemberResponse(
            id=str(uuid.uuid4()),
            username="teacher_1",
            email="teacher1@organization.com",
            role="teacher",
            organization_role="teacher",
            joined_at=datetime.now(timezone.utc) - timedelta(days=20),
            last_active=datetime.now(timezone.utc) - timedelta(hours=1),
            is_active=True
        ),
        OrganizationMemberResponse(
            id=str(uuid.uuid4()),
            username="teacher_2",
            email="teacher2@organization.com",
            role="teacher",
            organization_role="member",
            joined_at=datetime.now(timezone.utc) - timedelta(days=10),
            last_active=datetime.now(timezone.utc) - timedelta(minutes=30),
            is_active=True
        )
    ]

    return mock_members[offset:offset + limit]


@router.post("/{organization_id}/invite", response_model=InvitationResponse)
async def create_invitation(
    organization_id: str,
    request: InvitationCreateRequest,
    current_user: User = Depends(require_organization_role("admin", organization_id)),
    # db: Session = Depends(get_db)  # Uncomment when DB is available
):
    """
    Invite a user to join the organization.

    Requires admin role in the organization.
    Creates an invitation token that can be used to join the organization.
    """
    db = get_mock_db_session()

    # Check if user is already a member (in production)
    # existing_member = db.query(OrganizationMember).filter(
    #     OrganizationMember.organization_id == organization_id,
    #     OrganizationMember.user_email == request.email
    # ).first()

    # Generate invitation token
    invitation_token = secrets.token_urlsafe(32)
    expires_at = datetime.now(timezone.utc) + timedelta(days=7)  # 7 days to accept

    # Create invitation (mock implementation)
    invitation_id = str(uuid.uuid4())

    logger.info(
        f"Organization invitation created: {invitation_id} for {request.email}",
        extra={
            "organization_id": organization_id,
            "invitation_id": invitation_id,
            "invited_email": request.email,
            "invited_by": current_user.id,
            "role": request.role
        }
    )

    # In production, save to database and send email
    # send_invitation_email(request.email, organization_id, invitation_token)

    return InvitationResponse(
        id=invitation_id,
        email=request.email,
        role=request.role,
        invitation_token=invitation_token,
        expires_at=expires_at,
        is_pending=True,
        is_expired=False,
        is_valid=True,
        invited_by_id=current_user.id,
        created_at=datetime.now(timezone.utc)
    )


@router.patch("/{organization_id}/subscription", response_model=OrganizationResponse)
async def update_subscription(
    organization_id: str,
    request: SubscriptionUpdateRequest,
    current_user: User = Depends(require_organization_role("admin", organization_id)),
    # db: Session = Depends(get_db)  # Uncomment when DB is available
):
    """
    Update organization subscription.

    Requires admin role in the organization.
    Updates subscription tier and associated limits.
    """
    db = get_mock_db_session()

    # In production:
    # organization = db.query(Organization).filter(
    #     Organization.id == organization_id,
    #     Organization.is_active == True
    # ).first()

    organization = None  # Mock result

    if not organization:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )

    # Update subscription (mock implementation)
    logger.info(
        f"Organization subscription updated: {organization_id}",
        extra={
            "organization_id": organization_id,
            "user_id": current_user.id,
            "new_tier": request.subscription_tier,
            "updated_limits": request.dict(exclude_unset=True)
        }
    )

    # Return updated organization (mock)
    return OrganizationResponse(
        id=organization_id,
        name=f"Organization {organization_id[:8]}",
        slug=f"org-{organization_id[:8]}",
        display_name=f"Organization {organization_id[:8]}",
        description="Organization with updated subscription",
        website=None,
        email=f"contact@org-{organization_id[:8]}.com",
        organization_type="education",
        subscription_tier=request.subscription_tier,
        status="active",
        is_active=True,
        is_trial=False,
        trial_days_remaining=None,
        usage_percentage={
            "users": 40.0,
            "classes": 25.0,
            "storage": 30.0,
            "api_calls": 50.0,
            "roblox_sessions": 15.0
        },
        settings={},
        features=["content_generation", "advanced_analytics", "api_access"],
        created_at=datetime.now(timezone.utc) - timedelta(days=60),
        updated_at=datetime.now(timezone.utc)
    )


@router.delete("/{organization_id}/members/{user_id}")
async def remove_organization_member(
    organization_id: str,
    user_id: str,
    current_user: User = Depends(require_organization_role("admin", organization_id)),
    # db: Session = Depends(get_db)  # Uncomment when DB is available
):
    """
    Remove a member from the organization.

    Requires admin role in the organization.
    Cannot remove yourself as the last admin.
    """
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot remove yourself from the organization"
        )

    # In production, implement member removal logic
    logger.info(
        f"Member removed from organization: {user_id} from {organization_id}",
        extra={
            "organization_id": organization_id,
            "removed_user_id": user_id,
            "removed_by": current_user.id
        }
    )

    return {"message": "Member removed successfully"}


# === UTILITY ENDPOINTS ===

@router.get("/{organization_id}/usage")
async def get_organization_usage(
    organization_id: str,
    current_user: User = Depends(require_organization_role("member", organization_id)),
    period: str = Query("current", description="Usage period: current, last_month, last_year"),
    # db: Session = Depends(get_db)  # Uncomment when DB is available
):
    """
    Get organization usage statistics.

    Returns detailed usage information including limits and current usage.
    """
    # In production, fetch real usage data from database
    mock_usage = {
        "period": period,
        "organization_id": organization_id,
        "usage": {
            "users": {"current": 15, "limit": 50, "percentage": 30.0},
            "classes": {"current": 8, "limit": 20, "percentage": 40.0},
            "storage_gb": {"current": 2.5, "limit": 10.0, "percentage": 25.0},
            "api_calls": {"current": 7500, "limit": 10000, "percentage": 75.0},
            "roblox_sessions": {"current": 3, "limit": 15, "percentage": 20.0}
        },
        "trends": {
            "users_growth": "+20%",
            "api_calls_growth": "+15%",
            "storage_growth": "+5%"
        },
        "generated_at": datetime.now(timezone.utc)
    }

    return mock_usage


@router.get("/{organization_id}/features")
async def get_organization_features(
    organization_id: str,
    current_user: User = Depends(require_organization_role("member", organization_id)),
    # db: Session = Depends(get_db)  # Uncomment when DB is available
):
    """
    Get organization enabled features and available upgrades.
    """
    # Mock feature data
    mock_features = {
        "organization_id": organization_id,
        "subscription_tier": "professional",
        "enabled_features": [
            "content_generation",
            "advanced_analytics",
            "custom_branding",
            "api_access",
            "priority_support"
        ],
        "available_upgrades": [
            "white_label_solution",
            "dedicated_support",
            "custom_integrations",
            "advanced_security"
        ],
        "feature_limits": {
            "content_generation_per_month": 1000,
            "api_calls_per_minute": 100,
            "storage_gb": 50,
            "concurrent_sessions": 25
        }
    }

    return mock_features