"""
Multi-Tenant API Integration Examples

Example implementations showing how to integrate multi-tenancy
with FastAPI endpoints and middleware.
"""

import logging
from typing import Dict, List, Optional
from uuid import UUID

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.models import User, UserRole
from database.models.tenant import Organization, OrganizationStatus, SubscriptionTier
from database.repositories.tenant_repository import TenantContextManager
from database.services.tenant_service import TenantService

logger = logging.getLogger(__name__)
security = HTTPBearer()


# Pydantic models for API requests/responses
class OrganizationCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=200)
    admin_email: str = Field(..., regex=r"^[^@]+@[^@]+\.[^@]+$")
    admin_password: str = Field(..., min_length=8)
    admin_first_name: str = Field(default="", max_length=100)
    admin_last_name: str = Field(default="", max_length=100)
    organization_type: str = Field(default="education")
    subscription_tier: SubscriptionTier = Field(default=SubscriptionTier.FREE)


class OrganizationResponse(BaseModel):
    id: UUID
    name: str
    slug: str
    status: OrganizationStatus
    subscription_tier: SubscriptionTier
    current_users: int
    max_users: int
    trial_days_remaining: Optional[int]
    is_subscription_active: bool

    class Config:
        from_attributes = True


class UserInvite(BaseModel):
    email: str = Field(..., regex=r"^[^@]+@[^@]+\.[^@]+$")
    role: UserRole
    invitation_message: Optional[str] = Field(default=None, max_length=500)


class UsageStats(BaseModel):
    current_usage: Dict[str, int]
    limits: Dict[str, int]
    usage_percentage: Dict[str, float]
    subscription_tier: str
    status: str


# Dependency to get database session
async def get_db_session() -> AsyncSession:
    """Get database session (implement based on your database setup)"""
    # This should return your async database session
    # Example implementation would depend on your database configuration
    pass


# Dependency to get current user from JWT token
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    session: AsyncSession = Depends(get_db_session),
) -> User:
    """
    Extract current user from JWT token.
    This is a simplified example - implement proper JWT validation.
    """
    token = credentials.credentials

    # Implement JWT token validation here
    # This should extract user_id and organization_id from the token
    # and return the user object

    # Example placeholder:
    # user_id = decode_jwt_token(token)
    # user = await get_user_by_id(session, user_id)
    # return user

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED, detail="Not implemented - add JWT validation"
    )


# Dependency to get current organization from user context
async def get_current_organization(
    user: User = Depends(get_current_user), session: AsyncSession = Depends(get_db_session)
) -> Organization:
    """Get current organization from user context"""
    tenant_service = TenantService(session)
    org = await tenant_service.org_repo.get_by_id(user.organization_id)

    if not org:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")

    return org


# Middleware for setting tenant context
class TenantContextMiddleware:
    """Middleware to automatically set tenant context for requests"""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request = Request(scope, receive)

        # Extract organization ID from various sources
        org_id = None

        # Option 1: From subdomain (e.g., org1.yourapp.com)
        host = request.headers.get("host", "")
        if "." in host:
            subdomain = host.split(".")[0]
            # Look up organization by subdomain/slug
            # org_id = await get_org_id_by_subdomain(subdomain)

        # Option 2: From custom header
        org_header = request.headers.get("x-organization-id")
        if org_header:
            try:
                org_id = UUID(org_header)
            except ValueError:
                pass

        # Option 3: From JWT token (would be extracted in authentication)
        auth_header = request.headers.get("authorization")
        if auth_header and not org_id:
            # Extract org_id from JWT token
            # org_id = extract_org_from_jwt(auth_header)
            pass

        # Set tenant context in request state
        if org_id:
            request.state.organization_id = org_id

        await self.app(scope, receive, send)


# Permission checking dependencies
def require_admin(user: User = Depends(get_current_user)):
    """Require user to be admin"""
    if user.role != UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return user


def require_teacher_or_admin(user: User = Depends(get_current_user)):
    """Require user to be teacher or admin"""
    if user.role not in [UserRole.TEACHER, UserRole.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Teacher or admin access required"
        )
    return user


# Example API endpoints
class TenantAPI:
    """Example API endpoints for multi-tenant operations"""

    @staticmethod
    async def create_organization(
        org_data: OrganizationCreate, session: AsyncSession = Depends(get_db_session)
    ) -> OrganizationResponse:
        """Create a new organization with admin user"""
        tenant_service = TenantService(session)

        try:
            org, admin_user = await tenant_service.create_organization(
                name=org_data.name,
                admin_email=org_data.admin_email,
                admin_password=org_data.admin_password,
                admin_first_name=org_data.admin_first_name,
                admin_last_name=org_data.admin_last_name,
                organization_type=org_data.organization_type,
                subscription_tier=org_data.subscription_tier,
            )

            return OrganizationResponse(
                id=org.id,
                name=org.name,
                slug=org.slug,
                status=org.status,
                subscription_tier=org.subscription_tier,
                current_users=org.current_users,
                max_users=org.max_users,
                trial_days_remaining=org.trial_days_remaining,
                is_subscription_active=org.is_subscription_active,
            )

        except Exception as e:
            logger.error(f"Failed to create organization: {e}")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    @staticmethod
    async def get_organization_info(
        org: Organization = Depends(get_current_organization),
        user: User = Depends(get_current_user),
    ) -> OrganizationResponse:
        """Get current organization information"""
        return OrganizationResponse(
            id=org.id,
            name=org.name,
            slug=org.slug,
            status=org.status,
            subscription_tier=org.subscription_tier,
            current_users=org.current_users,
            max_users=org.max_users,
            trial_days_remaining=org.trial_days_remaining,
            is_subscription_active=org.is_subscription_active,
        )

    @staticmethod
    async def invite_user(
        invite_data: UserInvite,
        org: Organization = Depends(get_current_organization),
        user: User = Depends(require_admin),
        session: AsyncSession = Depends(get_db_session),
    ) -> Dict[str, str]:
        """Invite a user to the organization"""
        tenant_service = TenantService(session)

        try:
            invitation = await tenant_service.invite_user(
                organization_id=org.id,
                email=invite_data.email,
                role=invite_data.role,
                invited_by_id=user.id,
                invitation_message=invite_data.invitation_message,
            )

            return {
                "message": f"Invitation sent to {invite_data.email}",
                "invitation_token": invitation.invitation_token,
                "expires_at": invitation.expires_at.isoformat(),
            }

        except Exception as e:
            logger.error(f"Failed to send invitation: {e}")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    @staticmethod
    async def get_usage_stats(
        org: Organization = Depends(get_current_organization),
        user: User = Depends(require_admin),
        session: AsyncSession = Depends(get_db_session),
    ) -> UsageStats:
        """Get organization usage statistics"""
        tenant_service = TenantService(session)

        try:
            stats = await tenant_service.org_repo.get_usage_stats(org.id)
            return UsageStats(**stats)

        except Exception as e:
            logger.error(f"Failed to get usage stats: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve usage statistics",
            )

    @staticmethod
    async def upgrade_subscription(
        new_tier: SubscriptionTier,
        org: Organization = Depends(get_current_organization),
        user: User = Depends(require_admin),
        session: AsyncSession = Depends(get_db_session),
    ) -> OrganizationResponse:
        """Upgrade organization subscription"""
        tenant_service = TenantService(session)

        try:
            updated_org = await tenant_service.upgrade_subscription(
                organization_id=org.id, new_tier=new_tier, updated_by_id=user.id
            )

            await session.commit()

            return OrganizationResponse(
                id=updated_org.id,
                name=updated_org.name,
                slug=updated_org.slug,
                status=updated_org.status,
                subscription_tier=updated_org.subscription_tier,
                current_users=updated_org.current_users,
                max_users=updated_org.max_users,
                trial_days_remaining=updated_org.trial_days_remaining,
                is_subscription_active=updated_org.is_subscription_active,
            )

        except Exception as e:
            logger.error(f"Failed to upgrade subscription: {e}")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# Example of how to use tenant context in a repository operation
async def example_tenant_aware_operation(
    organization_id: UUID, session: AsyncSession
) -> List[User]:
    """Example of performing tenant-aware database operations"""

    # Method 1: Using context manager
    async with TenantContextManager(session, organization_id) as ctx:
        user_repo = ctx.get_repository(User)
        users = await user_repo.get_all()
        return users

    # Method 2: Using service layer
    # await TenantContextService.set_tenant_context(session, organization_id)
    # try:
    #     # Perform operations - RLS will automatically filter
    #     result = await session.execute(select(User))
    #     users = result.scalars().all()
    #     return users
    # finally:
    #     await TenantContextService.clear_tenant_context(session)


# FastAPI route registration example
def register_tenant_routes(app):
    """Register tenant-related routes with FastAPI app"""

    app.add_middleware(TenantContextMiddleware)

    @app.post("/organizations/", response_model=OrganizationResponse)
    async def create_organization_endpoint(
        org_data: OrganizationCreate, session: AsyncSession = Depends(get_db_session)
    ):
        return await TenantAPI.create_organization(org_data, session)

    @app.get("/organizations/me", response_model=OrganizationResponse)
    async def get_my_organization(
        org: Organization = Depends(get_current_organization),
        user: User = Depends(get_current_user),
    ):
        return await TenantAPI.get_organization_info(org, user)

    @app.post("/organizations/invitations/")
    async def invite_user_endpoint(
        invite_data: UserInvite,
        org: Organization = Depends(get_current_organization),
        user: User = Depends(require_admin),
        session: AsyncSession = Depends(get_db_session),
    ):
        return await TenantAPI.invite_user(invite_data, org, user, session)

    @app.get("/organizations/usage", response_model=UsageStats)
    async def get_usage_stats_endpoint(
        org: Organization = Depends(get_current_organization),
        user: User = Depends(require_admin),
        session: AsyncSession = Depends(get_db_session),
    ):
        return await TenantAPI.get_usage_stats(org, user, session)

    @app.post("/organizations/upgrade")
    async def upgrade_subscription_endpoint(
        new_tier: SubscriptionTier,
        org: Organization = Depends(get_current_organization),
        user: User = Depends(require_admin),
        session: AsyncSession = Depends(get_db_session),
    ):
        return await TenantAPI.upgrade_subscription(new_tier, org, user, session)


# Example usage in application startup
"""
from fastapi import FastAPI
from database.examples.tenant_api_integration import register_tenant_routes

app = FastAPI()
register_tenant_routes(app)
"""
