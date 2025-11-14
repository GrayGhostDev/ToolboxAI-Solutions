"""
Tenant/Organization Models for Multi-Tenancy Support

Implements organization-based multi-tenancy with proper isolation
and subscription management for the ToolBoxAI Educational Platform.
"""

import uuid
from datetime import datetime
from enum import Enum as PyEnum
from typing import Any, Optional

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    Enum,
    Float,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.sql import func

from database.models.models import Base


class OrganizationStatus(PyEnum):
    """Organization status enumeration"""

    ACTIVE = "active"
    SUSPENDED = "suspended"
    TRIAL = "trial"
    PENDING = "pending"
    CANCELLED = "cancelled"


class SubscriptionTier(PyEnum):
    """Subscription tier enumeration"""

    FREE = "free"
    BASIC = "basic"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"
    EDUCATION = "education"


class Organization(Base):
    """
    Organization model for multi-tenant isolation.
    Each organization represents a separate tenant with isolated data.
    """

    __tablename__ = "organizations"

    # Primary identification
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(200), nullable=False)
    slug = Column(String(100), unique=True, nullable=False)  # URL-friendly identifier

    # Contact information
    display_name = Column(String(250))
    description = Column(Text)
    website = Column(String(500))
    email = Column(String(255))
    phone = Column(String(50))

    # Address information
    address = Column(JSONB, default={})  # Structured address data
    timezone = Column(String(100), default="UTC")
    locale = Column(String(10), default="en-US")

    # Organization type and classification
    organization_type = Column(String(50), default="education")  # education, corporate, nonprofit
    industry = Column(String(100))
    size_category = Column(String(50))  # small, medium, large, enterprise

    # Subscription and billing
    subscription_tier = Column(
        Enum(SubscriptionTier, values_callable=lambda x: [e.value for e in x]),
        default=SubscriptionTier.FREE,
        nullable=False,
    )
    status = Column(
        Enum(OrganizationStatus, values_callable=lambda x: [e.value for e in x]),
        default=OrganizationStatus.TRIAL,
        nullable=False,
    )

    # Billing information
    billing_email = Column(String(255))
    billing_address = Column(JSONB, default={})
    tax_id = Column(String(100))  # VAT, EIN, etc.

    # Subscription dates
    trial_started_at = Column(DateTime(timezone=True))
    trial_expires_at = Column(DateTime(timezone=True))
    subscription_started_at = Column(DateTime(timezone=True))
    subscription_expires_at = Column(DateTime(timezone=True))
    last_billing_date = Column(DateTime(timezone=True))
    next_billing_date = Column(DateTime(timezone=True))

    # Usage limits and quotas
    max_users = Column(Integer, default=10)
    max_classes = Column(Integer, default=5)
    max_storage_gb = Column(Float, default=1.0)
    max_api_calls_per_month = Column(Integer, default=1000)
    max_roblox_sessions = Column(Integer, default=5)

    # Current usage tracking
    current_users = Column(Integer, default=0)
    current_classes = Column(Integer, default=0)
    current_storage_gb = Column(Float, default=0.0)
    current_api_calls_this_month = Column(Integer, default=0)
    current_roblox_sessions = Column(Integer, default=0)

    # Organization settings and configuration
    settings = Column(JSONB, default={})  # Flexible settings storage
    features = Column(JSONB, default=[])  # Enabled features array
    integrations = Column(JSONB, default={})  # Integration configurations

    # Security and compliance
    sso_enabled = Column(Boolean, default=False)
    sso_configuration = Column(JSONB, default={})
    data_retention_days = Column(Integer, default=365)
    audit_logs_enabled = Column(Boolean, default=True)
    coppa_compliance_required = Column(Boolean, default=True)
    ferpa_compliance_required = Column(Boolean, default=False)

    # Branding and customization
    logo_url = Column(String(500))
    primary_color = Column(String(7))  # Hex color
    secondary_color = Column(String(7))  # Hex color
    custom_domain = Column(String(255))
    custom_css = Column(Text)

    # API and technical configuration
    api_key = Column(String(255), unique=True)  # Organization API key
    webhook_url = Column(String(500))
    webhook_secret = Column(String(255))
    rate_limit_per_minute = Column(Integer, default=100)

    # Status flags
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False)
    is_demo = Column(Boolean, default=False)
    maintenance_mode = Column(Boolean, default=False)

    # Admin and emergency access
    emergency_contact_email = Column(String(255))
    admin_notes = Column(Text)
    support_level = Column(String(50), default="standard")  # standard, priority, enterprise

    # Audit and timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by_id = Column(UUID(as_uuid=True))  # Who created this organization
    updated_by_id = Column(UUID(as_uuid=True))  # Who last updated

    # Soft delete support
    deleted_at = Column(DateTime(timezone=True))
    deleted_by_id = Column(UUID(as_uuid=True))

    # Relationships (to be added when other models are updated)
    # users = relationship("User", back_populates="organization")
    # classes = relationship("Class", back_populates="organization")
    # courses = relationship("Course", back_populates="organization")

    __table_args__ = (
        # Indexes for performance
        Index("idx_organization_slug", "slug"),
        Index("idx_organization_status", "status"),
        Index("idx_organization_subscription", "subscription_tier"),
        Index("idx_organization_active", "is_active"),
        Index("idx_organization_trial_expires", "trial_expires_at"),
        Index("idx_organization_subscription_expires", "subscription_expires_at"),
        Index("idx_organization_created", "created_at"),
        # Constraints
        CheckConstraint("max_users > 0", name="check_max_users_positive"),
        CheckConstraint("max_classes >= 0", name="check_max_classes_non_negative"),
        CheckConstraint("max_storage_gb >= 0", name="check_max_storage_non_negative"),
        CheckConstraint("current_users >= 0", name="check_current_users_non_negative"),
        CheckConstraint("current_classes >= 0", name="check_current_classes_non_negative"),
        CheckConstraint("current_storage_gb >= 0", name="check_current_storage_non_negative"),
        CheckConstraint("data_retention_days > 0", name="check_retention_days_positive"),
        CheckConstraint("rate_limit_per_minute > 0", name="check_rate_limit_positive"),
    )

    def __repr__(self) -> str:
        return f"<Organization(id='{self.id}', name='{self.name}', status='{self.status}')>"

    @property
    def is_trial(self) -> bool:
        """Check if organization is in trial period"""
        return self.status == OrganizationStatus.TRIAL

    @property
    def is_subscription_active(self) -> bool:
        """Check if organization has an active subscription"""
        if self.status != OrganizationStatus.ACTIVE:
            return False

        if self.subscription_expires_at:
            return datetime.utcnow() < self.subscription_expires_at.replace(tzinfo=None)

        return True

    @property
    def trial_days_remaining(self) -> Optional[int]:
        """Get remaining trial days"""
        if not self.trial_expires_at or self.status != OrganizationStatus.TRIAL:
            return None

        remaining = self.trial_expires_at.replace(tzinfo=None) - datetime.utcnow()
        return max(0, remaining.days)

    @property
    def usage_percentage(self) -> dict[str, float]:
        """Get usage percentages for various limits"""
        return {
            "users": (self.current_users / self.max_users * 100) if self.max_users > 0 else 0,
            "classes": (
                (self.current_classes / self.max_classes * 100) if self.max_classes > 0 else 0
            ),
            "storage": (
                (self.current_storage_gb / self.max_storage_gb * 100)
                if self.max_storage_gb > 0
                else 0
            ),
            "api_calls": (
                (self.current_api_calls_this_month / self.max_api_calls_per_month * 100)
                if self.max_api_calls_per_month > 0
                else 0
            ),
            "roblox_sessions": (
                (self.current_roblox_sessions / self.max_roblox_sessions * 100)
                if self.max_roblox_sessions > 0
                else 0
            ),
        }

    def is_feature_enabled(self, feature_name: str) -> bool:
        """Check if a feature is enabled for this organization"""
        return feature_name in (self.features or [])

    def get_setting(self, key: str, default: Any = None) -> Any:
        """Get a setting value with optional default"""
        return (self.settings or {}).get(key, default)

    def set_setting(self, key: str, value: Any) -> None:
        """Set a setting value"""
        if self.settings is None:
            self.settings = {}
        self.settings[key] = value

    def can_add_user(self) -> bool:
        """Check if organization can add another user"""
        return self.current_users < self.max_users

    def can_add_class(self) -> bool:
        """Check if organization can add another class"""
        return self.current_classes < self.max_classes

    def can_use_storage(self, additional_gb: float = 0) -> bool:
        """Check if organization can use additional storage"""
        return (self.current_storage_gb + additional_gb) <= self.max_storage_gb

    def increment_usage(self, metric: str, amount: int = 1) -> None:
        """Increment usage counter for a metric"""
        if metric == "users":
            self.current_users = min(self.current_users + amount, self.max_users)
        elif metric == "classes":
            self.current_classes = min(self.current_classes + amount, self.max_classes)
        elif metric == "api_calls":
            self.current_api_calls_this_month += amount
        elif metric == "roblox_sessions":
            self.current_roblox_sessions = min(
                self.current_roblox_sessions + amount, self.max_roblox_sessions
            )

    def decrement_usage(self, metric: str, amount: int = 1) -> None:
        """Decrement usage counter for a metric"""
        if metric == "users":
            self.current_users = max(0, self.current_users - amount)
        elif metric == "classes":
            self.current_classes = max(0, self.current_classes - amount)
        elif metric == "roblox_sessions":
            self.current_roblox_sessions = max(0, self.current_roblox_sessions - amount)


class OrganizationInvitation(Base):
    """
    Organization invitation model for inviting users to join an organization.
    """

    __tablename__ = "organization_invitations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), nullable=False)  # FK will be added in migration

    # Invitation details
    email = Column(String(255), nullable=False)
    role = Column(String(50), default="member")  # admin, manager, teacher, member
    invited_by_id = Column(UUID(as_uuid=True))  # Who sent the invitation

    # Invitation token and security
    invitation_token = Column(String(255), unique=True, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)

    # Status tracking
    accepted_at = Column(DateTime(timezone=True))
    accepted_by_id = Column(UUID(as_uuid=True))  # User who accepted
    declined_at = Column(DateTime(timezone=True))
    cancelled_at = Column(DateTime(timezone=True))
    cancelled_by_id = Column(UUID(as_uuid=True))

    # Metadata
    invitation_message = Column(Text)
    permissions = Column(JSONB, default={})

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    __table_args__ = (
        Index("idx_org_invitation_token", "invitation_token"),
        Index("idx_org_invitation_email", "email"),
        Index("idx_org_invitation_organization", "organization_id"),
        Index("idx_org_invitation_expires", "expires_at"),
        Index("idx_org_invitation_status", "accepted_at", "declined_at", "cancelled_at"),
    )

    @property
    def is_pending(self) -> bool:
        """Check if invitation is still pending"""
        return not any([self.accepted_at, self.declined_at, self.cancelled_at])

    @property
    def is_expired(self) -> bool:
        """Check if invitation has expired"""
        return datetime.utcnow() > self.expires_at.replace(tzinfo=None)

    @property
    def is_valid(self) -> bool:
        """Check if invitation is valid (pending and not expired)"""
        return self.is_pending and not self.is_expired


class OrganizationUsageLog(Base):
    """
    Track organization usage over time for analytics and billing.
    """

    __tablename__ = "organization_usage_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), nullable=False)  # FK will be added in migration

    # Usage metrics snapshot
    users_count = Column(Integer, default=0)
    classes_count = Column(Integer, default=0)
    storage_gb = Column(Float, default=0.0)
    api_calls_count = Column(Integer, default=0)
    roblox_sessions_count = Column(Integer, default=0)

    # Additional metrics
    active_users_count = Column(Integer, default=0)  # Users who logged in this period
    content_generated_count = Column(Integer, default=0)
    quizzes_completed_count = Column(Integer, default=0)

    # Time period
    log_date = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    log_type = Column(String(20), default="daily")  # daily, weekly, monthly

    # Billing period reference
    billing_period_start = Column(DateTime(timezone=True))
    billing_period_end = Column(DateTime(timezone=True))

    # Raw usage data for detailed analysis
    usage_data = Column(JSONB, default={})

    __table_args__ = (
        Index("idx_org_usage_organization_date", "organization_id", "log_date"),
        Index("idx_org_usage_type_date", "log_type", "log_date"),
        Index("idx_org_usage_billing_period", "billing_period_start", "billing_period_end"),
    )
