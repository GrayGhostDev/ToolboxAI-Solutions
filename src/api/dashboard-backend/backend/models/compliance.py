"""
Compliance models for COPPA, FERPA, and GDPR
"""

import enum
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import JSON, Boolean, DateTime
from sqlalchemy import Enum as SQLEnum
from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin

if TYPE_CHECKING:
    from .class_model import Class
    from .lesson import Lesson
    from .user import User


class ConsentType(enum.Enum):
    """Types of consent"""

    COPPA_PARENTAL = "coppa_parental"
    FERPA_RECORDS = "ferpa_records"
    GDPR_PROCESSING = "gdpr_processing"
    MARKETING = "marketing"
    ANALYTICS = "analytics"
    THIRD_PARTY = "third_party"


class ComplianceStatus(enum.Enum):
    """Compliance status levels"""

    COMPLIANT = "compliant"
    PENDING = "pending"
    NON_COMPLIANT = "non_compliant"
    REVIEW_NEEDED = "review_needed"


class DataRequestType(enum.Enum):
    """Types of data requests under GDPR"""

    ACCESS = "access"
    PORTABILITY = "portability"
    DELETION = "deletion"
    RECTIFICATION = "rectification"
    RESTRICTION = "restriction"


class ConsentRecord(Base, TimestampMixin):
    """Track consent records for compliance"""

    __tablename__ = "consent_records"

    # Primary key
    id: Mapped[str] = mapped_column(String(36), primary_key=True)

    # User information
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id"), nullable=False
    )
    parent_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("users.id"))

    # Consent details
    consent_type: Mapped[ConsentType] = mapped_column(
        SQLEnum(ConsentType), nullable=False
    )
    granted: Mapped[bool] = mapped_column(Boolean, nullable=False)
    granted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    # Consent scope
    scope: Mapped[list] = mapped_column(
        JSON, default=[], nullable=False
    )  # List of data types/purposes
    version: Mapped[str] = mapped_column(
        String(20), nullable=False
    )  # Version of terms/policy

    # Collection method
    method: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # "explicit", "implicit", "parental"
    ip_address: Mapped[Optional[str]] = mapped_column(String(45))
    user_agent: Mapped[Optional[str]] = mapped_column(Text)

    # Withdrawal
    withdrawn: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    withdrawn_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    withdrawal_reason: Mapped[Optional[str]] = mapped_column(Text)

    # Verification
    verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    verified_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    verification_method: Mapped[Optional[str]] = mapped_column(String(100))

    # Relationships
    user: Mapped["User"] = relationship("User", foreign_keys=[user_id])
    parent: Mapped[Optional["User"]] = relationship("User", foreign_keys=[parent_id])

    def __repr__(self):
        return f"<ConsentRecord {self.user_id} - {self.consent_type.value} ({'Granted' if self.granted else 'Denied'})>"


class DataRetention(Base, TimestampMixin):
    """Track data retention policies and schedules"""

    __tablename__ = "data_retention"

    # Primary key
    id: Mapped[str] = mapped_column(String(36), primary_key=True)

    # User data
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id"), nullable=False
    )

    # Retention details
    data_type: Mapped[str] = mapped_column(
        String(100), nullable=False
    )  # "personal", "academic", "behavioral"
    retention_days: Mapped[int] = mapped_column(String(10), nullable=False)
    deletion_scheduled: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    # Legal basis
    legal_basis: Mapped[str] = mapped_column(
        String(100), nullable=False
    )  # "consent", "contract", "legal_obligation"
    retention_reason: Mapped[str] = mapped_column(Text, nullable=False)

    # Audit
    last_reviewed: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    next_review: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )

    # Relationships
    user: Mapped["User"] = relationship("User")

    def __repr__(self):
        return f"<DataRetention {self.user_id} - {self.data_type}>"


class ComplianceLog(Base, TimestampMixin):
    """Audit log for compliance-related actions"""

    __tablename__ = "compliance_logs"

    # Primary key
    id: Mapped[str] = mapped_column(String(36), primary_key=True)

    # Action details
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    category: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # "COPPA", "FERPA", "GDPR"

    # User information
    user_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("users.id"))
    performed_by: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id"), nullable=False
    )

    # Details
    details: Mapped[dict] = mapped_column(JSON, nullable=False)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45))

    # Compliance status
    status: Mapped[ComplianceStatus] = mapped_column(
        SQLEnum(ComplianceStatus), nullable=False
    )
    issues: Mapped[Optional[list]] = mapped_column(JSON, default=[])
    recommendations: Mapped[Optional[list]] = mapped_column(JSON, default=[])

    # Relationships
    user: Mapped[Optional["User"]] = relationship("User", foreign_keys=[user_id])
    performer: Mapped["User"] = relationship("User", foreign_keys=[performed_by])

    def __repr__(self):
        return f"<ComplianceLog {self.action} - {self.category} ({self.status.value})>"


class DataRequest(Base, TimestampMixin):
    """GDPR data requests (access, portability, deletion)"""

    __tablename__ = "data_requests"

    # Primary key
    id: Mapped[str] = mapped_column(String(36), primary_key=True)

    # Request details
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id"), nullable=False
    )
    request_type: Mapped[DataRequestType] = mapped_column(
        SQLEnum(DataRequestType), nullable=False
    )

    # Status
    status: Mapped[str] = mapped_column(
        String(50), default="pending", nullable=False
    )  # "pending", "processing", "completed", "denied"
    requested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    # Processing
    processed_by: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("users.id")
    )
    processing_notes: Mapped[Optional[str]] = mapped_column(Text)

    # Response
    response_url: Mapped[Optional[str]] = mapped_column(
        String(500)
    )  # URL to download data
    response_expires: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True)
    )

    # Verification
    verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    verification_method: Mapped[Optional[str]] = mapped_column(String(100))

    # Relationships
    user: Mapped["User"] = relationship("User", foreign_keys=[user_id])
    processor: Mapped[Optional["User"]] = relationship(
        "User", foreign_keys=[processed_by]
    )

    def __repr__(self):
        return (
            f"<DataRequest {self.user_id} - {self.request_type.value} ({self.status})>"
        )
