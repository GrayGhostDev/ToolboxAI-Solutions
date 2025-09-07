"""
Report models for the educational platform
"""

import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin


class ReportType(str, enum.Enum):
    """Types of reports available"""

    PROGRESS = "progress"
    ATTENDANCE = "attendance"
    GRADES = "grades"
    BEHAVIOR = "behavior"
    ASSESSMENT = "assessment"
    COMPLIANCE = "compliance"
    GAMIFICATION = "gamification"
    CUSTOM = "custom"


class ReportFrequency(str, enum.Enum):
    """Report generation frequency"""

    ONCE = "once"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"


class ReportStatus(str, enum.Enum):
    """Report generation status"""

    PENDING = "pending"
    GENERATING = "generating"
    READY = "ready"
    FAILED = "failed"
    SCHEDULED = "scheduled"
    CANCELLED = "cancelled"


class ReportFormat(str, enum.Enum):
    """Output formats for reports"""

    PDF = "pdf"
    EXCEL = "excel"
    CSV = "csv"
    HTML = "html"
    JSON = "json"


class ReportTemplate(Base, TimestampMixin):
    """Predefined report templates"""

    __tablename__ = "report_templates"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    type: Mapped[ReportType] = mapped_column(Enum(ReportType), nullable=False)
    category: Mapped[str | None] = mapped_column(String(100))
    icon: Mapped[str | None] = mapped_column(String(50))  # Icon name for frontend
    fields: Mapped[list | dict | None] = mapped_column(
        JSON
    )  # List of fields included in the template
    filters: Mapped[dict | None] = mapped_column(
        JSON
    )  # Available filters for the template
    default_format: Mapped[ReportFormat] = mapped_column(
        Enum(ReportFormat), default=ReportFormat.PDF
    )
    is_popular: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Configuration for data sources and aggregations
    data_sources: Mapped[list | None] = mapped_column(
        JSON
    )  # Which models/tables to query
    aggregations: Mapped[dict | None] = mapped_column(JSON)  # How to aggregate data

    # Relationships
    reports: Mapped[list["Report"]] = relationship("Report", back_populates="template")


class Report(Base, TimestampMixin):
    """Generated reports"""

    __tablename__ = "reports"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    type: Mapped[ReportType] = mapped_column(Enum(ReportType), nullable=False)
    format: Mapped[ReportFormat] = mapped_column(
        Enum(ReportFormat), nullable=False, default=ReportFormat.PDF
    )
    status: Mapped[ReportStatus] = mapped_column(
        Enum(ReportStatus), nullable=False, default=ReportStatus.PENDING
    )

    # Template reference
    template_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("report_templates.id", ondelete="SET NULL")
    )
    template: Mapped["ReportTemplate"] = relationship(
        "ReportTemplate", back_populates="reports"
    )

    # User who generated the report
    generated_by: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"))

    # Report parameters
    filters: Mapped[dict | None] = mapped_column(
        JSON
    )  # Applied filters (date range, classes, etc.)
    parameters: Mapped[dict | None] = mapped_column(JSON)  # Additional parameters

    # School/Class scope
    school_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("schools.id", ondelete="CASCADE")
    )
    class_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("classes.id", ondelete="CASCADE")
    )

    # File information
    file_path: Mapped[str | None] = mapped_column(String(500))
    file_size: Mapped[int | None] = mapped_column(Integer)  # Size in bytes
    mime_type: Mapped[str | None] = mapped_column(String(100))

    # Generation details
    generated_at: Mapped[datetime | None] = mapped_column(DateTime)
    generation_time: Mapped[float | None] = mapped_column(
        Float
    )  # Time taken in seconds
    error_message: Mapped[str | None] = mapped_column(Text)

    # Email details
    recipients: Mapped[list | None] = mapped_column(JSON)  # List of email addresses
    emailed_at: Mapped[datetime | None] = mapped_column(DateTime)

    # Scheduling
    schedule_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("report_schedules.id", ondelete="SET NULL")
    )

    # Statistics
    row_count: Mapped[int | None] = mapped_column(
        Integer
    )  # Number of records in report
    page_count: Mapped[int | None] = mapped_column(Integer)  # For PDF reports


class ReportSchedule(Base, TimestampMixin):
    """Scheduled report generation"""

    __tablename__ = "report_schedules"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)

    # Template and configuration
    template_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("report_templates.id", ondelete="CASCADE")
    )
    template: Mapped["ReportTemplate"] = relationship("ReportTemplate")

    # Schedule configuration
    frequency: Mapped[ReportFrequency] = mapped_column(
        Enum(ReportFrequency), nullable=False
    )
    cron_expression: Mapped[str | None] = mapped_column(
        String(100)
    )  # For complex schedules

    # Timing
    start_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    end_date: Mapped[datetime | None] = mapped_column(DateTime)
    next_run: Mapped[datetime | None] = mapped_column(DateTime)
    last_run: Mapped[datetime | None] = mapped_column(DateTime)

    # Time of day for daily/weekly/monthly reports
    hour: Mapped[int] = mapped_column(Integer, default=9)  # 0-23
    minute: Mapped[int] = mapped_column(Integer, default=0)  # 0-59
    day_of_week: Mapped[int | None] = mapped_column(Integer)  # 0-6 for weekly reports
    day_of_month: Mapped[int | None] = mapped_column(
        Integer
    )  # 1-31 for monthly reports

    # Report configuration
    format: Mapped[ReportFormat] = mapped_column(
        Enum(ReportFormat), default=ReportFormat.PDF
    )
    filters: Mapped[dict | None] = mapped_column(JSON)
    parameters: Mapped[dict | None] = mapped_column(JSON)

    # Scope
    school_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("schools.id", ondelete="CASCADE")
    )
    class_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("classes.id", ondelete="CASCADE")
    )

    # Recipients
    recipients: Mapped[list | None] = mapped_column(JSON)  # Email addresses
    auto_email: Mapped[bool] = mapped_column(Boolean, default=False)

    # Owner
    created_by: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"))

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    failure_count: Mapped[int] = mapped_column(Integer, default=0)
    max_retries: Mapped[int] = mapped_column(Integer, default=3)

    # History
    reports: Mapped[list["Report"]] = relationship("Report", backref="schedule")


class ReportGeneration(Base, TimestampMixin):
    """Log of report generation attempts"""

    __tablename__ = "report_generations"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    report_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("reports.id", ondelete="CASCADE")
    )
    schedule_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("report_schedules.id", ondelete="CASCADE")
    )

    # Timing
    started_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime)
    duration_seconds: Mapped[float | None] = mapped_column(Float)

    # Status
    status: Mapped[ReportStatus] = mapped_column(Enum(ReportStatus), nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text)

    # Metrics
    records_processed: Mapped[int | None] = mapped_column(Integer)
    memory_usage_mb: Mapped[float | None] = mapped_column(Float)

    # User who triggered (if manual)
    triggered_by: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"))
    is_manual: Mapped[bool] = mapped_column(Boolean, default=False)
