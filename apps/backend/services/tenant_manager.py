"""Tenant management services for ToolboxAI multi-tenancy (2025).

This module centralises organization CRUD, membership management, quota tracking
and usage analytics.  It is intentionally implemented with synchronous
SQLAlchemy sessions because the rest of the service layer still uses the
traditional `SessionLocal` factory exposed by ``apps.backend.core.database``.

The service follows the 2025 ToolboxAI documentation which outlines:

* Organization lifecycle (create, update, deactivate, archive)
* Membership management via `User.organization_id` and `organization_role`
* Usage tracking recorded through ``OrganizationUsageLog``
* Invitation workflows backed by ``OrganizationInvitation``

The goal is to provide a single entry-point that API endpoints, background
tasks, and provisioning scripts can depend upon without duplicating SQL logic
or leaking implementation details.
"""

from __future__ import annotations

import logging
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple
from uuid import UUID, uuid4

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError, NoResultFound
from sqlalchemy.orm import Session

from apps.backend.core.database import SessionLocal
from database.models.models import User
from database.models.tenant import (
    Organization,
    OrganizationInvitation,
    OrganizationStatus,
    OrganizationUsageLog,
    SubscriptionTier,
)

logger = logging.getLogger(__name__)


class TenantManagerError(Exception):
    """Base exception for tenant management errors."""


class OrganizationNotFoundError(TenantManagerError):
    """Raised when an organization cannot be located."""


class DuplicateOrganizationError(TenantManagerError):
    """Raised when attempting to create an organization with a duplicate slug."""


class InvitationError(TenantManagerError):
    """Raised when invitation workflows fail."""


class TenantManager:
    """Service responsible for managing organizations and membership."""

    def __init__(self, session_factory=SessionLocal):
        self._session_factory = session_factory

    # ------------------------------------------------------------------
    # Session helpers
    # ------------------------------------------------------------------

    @contextmanager
    def _session(self) -> Iterable[Session]:
        session: Session = self._session_factory()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    # ------------------------------------------------------------------
    # Organization lifecycle
    # ------------------------------------------------------------------

    def create_organization(
        self,
        name: str,
        slug: str,
        *,
        created_by_id: Optional[UUID] = None,
        subscription_tier: SubscriptionTier = SubscriptionTier.FREE,
        description: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Organization:
        """Create a new organization/tenant."""

        normalized_slug = slug.lower().strip()

        with self._session() as session:
            existing = session.execute(
                select(Organization).where(Organization.slug == normalized_slug)
            ).scalar_one_or_none()
            if existing is not None:
                raise DuplicateOrganizationError(f"Organization slug '{slug}' already exists")

            organization = Organization(
                id=uuid4(),
                name=name,
                slug=normalized_slug,
                display_name=metadata.get("display_name") if metadata else name,
                description=description,
                created_by_id=created_by_id,
                subscription_tier=subscription_tier,
                status=OrganizationStatus.TRIAL,
                trial_started_at=datetime.now(timezone.utc),
                trial_expires_at=datetime.now(timezone.utc) + timedelta(days=30),
            )

            if metadata:
                organization.settings = metadata.get("settings", {})
                organization.features = metadata.get("features", [])
                organization.integrations = metadata.get("integrations", {})

            session.add(organization)
            session.flush()  # Assign ID
            session.refresh(organization)

            logger.info("Organization created", extra={"organization_id": str(organization.id)})
            return organization

    def get_organization(self, organization_id: UUID) -> Organization:
        with self._session() as session:
            organization = session.get(Organization, organization_id)
            if organization is None:
                raise OrganizationNotFoundError(str(organization_id))
            session.expunge(organization)
            return organization

    def get_organization_by_slug(self, slug: str) -> Organization:
        with self._session() as session:
            organization = session.execute(
                select(Organization).where(Organization.slug == slug.lower().strip())
            ).scalar_one_or_none()

            if organization is None:
                raise OrganizationNotFoundError(slug)
            session.expunge(organization)
            return organization

    def list_organizations(
        self,
        *,
        status: Optional[OrganizationStatus] = None,
        subscription_tier: Optional[SubscriptionTier] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Organization]:
        with self._session() as session:
            query = select(Organization)
            if status is not None:
                query = query.where(Organization.status == status)
            if subscription_tier is not None:
                query = query.where(Organization.subscription_tier == subscription_tier)

            results = session.execute(query.offset(offset).limit(limit)).scalars().all()
            for org in results:
                session.expunge(org)
            return results

    def update_organization(self, organization_id: UUID, **updates: Any) -> Organization:
        with self._session() as session:
            organization = session.get(Organization, organization_id)
            if organization is None:
                raise OrganizationNotFoundError(str(organization_id))

            for field, value in updates.items():
                if hasattr(organization, field) and value is not None:
                    setattr(organization, field, value)

            organization.updated_at = datetime.now(timezone.utc)
            session.flush()
            session.refresh(organization)
            session.expunge(organization)
            return organization

    def set_status(self, organization_id: UUID, status: OrganizationStatus) -> Organization:
        return self.update_organization(organization_id, status=status)

    # ------------------------------------------------------------------
    # Membership management
    # ------------------------------------------------------------------

    def assign_user(
        self,
        user_id: UUID,
        organization_id: UUID,
        *,
        role: str = "member",
        activate: bool = True,
    ) -> User:
        with self._session() as session:
            organization = session.get(Organization, organization_id)
            if organization is None:
                raise OrganizationNotFoundError(str(organization_id))

            user = session.get(User, user_id)
            if user is None:
                raise TenantManagerError(f"User {user_id} not found")

            if user.organization_id and user.organization_id != organization_id:
                logger.info(
                    "User moving between organizations",
                    extra={
                        "user_id": str(user_id),
                        "old_organization_id": str(user.organization_id),
                        "new_organization_id": str(organization_id),
                    },
                )

            user.organization_id = organization_id
            user.organization_role = role
            if activate and hasattr(user, "status"):
                try:
                    from database.models.user_modern import UserStatus as ModernUserStatus

                    user.status = ModernUserStatus.ACTIVE
                except Exception:
                    user.is_active = True  # fallback for legacy model

            organization.increment_usage("users", 1)
            session.add(user)
            session.add(organization)
            session.flush()
            session.refresh(user)
            session.expunge(user)
            return user

    def remove_user(self, user_id: UUID) -> None:
        with self._session() as session:
            user = session.get(User, user_id)
            if user is None:
                raise TenantManagerError(f"User {user_id} not found")

            previous_org = user.organization_id
            user.organization_id = None
            user.organization_role = "member"

            if previous_org:
                org = session.get(Organization, previous_org)
                if org:
                    org.decrement_usage("users", 1)
                    session.add(org)

            session.add(user)

    def list_members(self, organization_id: UUID, *, limit: int = 100, offset: int = 0) -> List[User]:
        with self._session() as session:
            query = (
                select(User)
                .where(User.organization_id == organization_id)
                .offset(offset)
                .limit(limit)
            )
            members = session.execute(query).scalars().all()
            for user in members:
                session.expunge(user)
            return members

    # ------------------------------------------------------------------
    # Invitation workflow
    # ------------------------------------------------------------------

    def create_invitation(
        self,
        organization_id: UUID,
        email: str,
        *,
        role: str = "member",
        invited_by_id: Optional[UUID] = None,
        expires_in_days: int = 7,
        message: Optional[str] = None,
    ) -> OrganizationInvitation:
        with self._session() as session:
            organization = session.get(Organization, organization_id)
            if organization is None:
                raise OrganizationNotFoundError(str(organization_id))

            invitation = OrganizationInvitation(
                id=uuid4(),
                organization_id=organization_id,
                email=email.lower().strip(),
                role=role,
                invited_by_id=invited_by_id,
                invitation_token=uuid4().hex,
                expires_at=datetime.now(timezone.utc) + timedelta(days=expires_in_days),
                invitation_message=message,
            )

            session.add(invitation)
            session.flush()
            session.refresh(invitation)
            session.expunge(invitation)
            logger.info(
                "Organization invitation created",
                extra={"organization_id": str(organization_id), "email": email},
            )
            return invitation

    def mark_invitation_accepted(self, invitation_token: str, accepted_by: UUID) -> OrganizationInvitation:
        with self._session() as session:
            invitation = session.execute(
                select(OrganizationInvitation).where(OrganizationInvitation.invitation_token == invitation_token)
            ).scalar_one_or_none()

            if invitation is None:
                raise InvitationError("Invitation token not found")

            if invitation.is_expired:
                raise InvitationError("Invitation has expired")

            invitation.accepted_at = datetime.now(timezone.utc)
            invitation.accepted_by_id = accepted_by
            session.flush()
            session.refresh(invitation)
            session.expunge(invitation)
            return invitation

    # ------------------------------------------------------------------
    # Usage tracking
    # ------------------------------------------------------------------

    def record_usage(
        self,
        organization_id: UUID,
        *,
        users_count: int,
        classes_count: int,
        storage_gb: float,
        api_calls_count: int,
        roblox_sessions_count: int,
        log_type: str = "daily",
        usage_data: Optional[Dict[str, Any]] = None,
    ) -> OrganizationUsageLog:
        with self._session() as session:
            organization = session.get(Organization, organization_id)
            if organization is None:
                raise OrganizationNotFoundError(str(organization_id))

            usage_log = OrganizationUsageLog(
                id=uuid4(),
                organization_id=organization_id,
                users_count=users_count,
                classes_count=classes_count,
                storage_gb=storage_gb,
                api_calls_count=api_calls_count,
                roblox_sessions_count=roblox_sessions_count,
                log_type=log_type,
                log_date=datetime.now(timezone.utc),
                usage_data=usage_data or {},
            )

            session.add(usage_log)
            session.flush()
            session.refresh(usage_log)
            session.expunge(usage_log)
            return usage_log

    def get_recent_usage(self, organization_id: UUID, *, days: int = 30) -> List[OrganizationUsageLog]:
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        with self._session() as session:
            logs = session.execute(
                select(OrganizationUsageLog)
                .where(
                    OrganizationUsageLog.organization_id == organization_id,
                    OrganizationUsageLog.log_date >= cutoff,
                )
                .order_by(OrganizationUsageLog.log_date.desc())
            ).scalars().all()

            for entry in logs:
                session.expunge(entry)
            return logs

    # ------------------------------------------------------------------
    # Utility helpers
    # ------------------------------------------------------------------

    def get_member_count(self, organization_id: UUID) -> int:
        with self._session() as session:
            count = session.execute(
                select(func.count(User.id)).where(User.organization_id == organization_id)
            ).scalar_one()
            return int(count or 0)


_tenant_manager_singleton: Optional[TenantManager] = None


def get_tenant_manager() -> TenantManager:
    """Return a singleton instance used across the application."""

    global _tenant_manager_singleton
    if _tenant_manager_singleton is None:
        _tenant_manager_singleton = TenantManager()
    return _tenant_manager_singleton


__all__ = [
    "TenantManager",
    "TenantManagerError",
    "OrganizationNotFoundError",
    "DuplicateOrganizationError",
    "InvitationError",
    "get_tenant_manager",
]
