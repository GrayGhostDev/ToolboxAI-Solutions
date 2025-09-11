"""
Reports Management API Endpoints
"""

import io
import json
import os
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from database import get_db
from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    HTTPException,
    Query,
    Response,
    status,
)
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from models import (
    Assessment,
    AssessmentSubmission,
    Badge,
    Class,
    LessonProgress,
    Report,
    ReportFormat,
    ReportFrequency,
    ReportGeneration,
    ReportSchedule,
    ReportStatus,
    ReportTemplate,
    ReportType,
    School,
    User,
    UserBadge,
    UserRole,
    XPTransaction,
)
from pydantic import BaseModel, Field
from sqlalchemy import and_, func, or_
from sqlalchemy.orm import Session

from ._utils import now
from .auth import decode_token

# ==================== Router Setup ====================
router = APIRouter(prefix="/api/v1/reports", tags=["reports"])
security = HTTPBearer()

# ==================== Pydantic Schemas ====================


class ReportTemplateResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    type: str
    category: Optional[str]
    icon: Optional[str]
    fields: Optional[List[str]]
    filters: Optional[Dict[str, Any]]
    default_format: str
    is_popular: bool
    is_active: bool

    class Config:
        from_attributes = True


class ReportGenerateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    type: str = Field(
        ...,
        pattern="^(progress|attendance|grades|behavior|assessment|compliance|gamification|custom)$",
    )
    format: str = Field(default="pdf", pattern="^(pdf|excel|csv|html|json)$")
    template_id: Optional[str] = None
    filters: Optional[Dict[str, Any]] = Field(default={})
    parameters: Optional[Dict[str, Any]] = Field(default={})
    school_id: Optional[str] = None
    class_id: Optional[str] = None
    recipients: Optional[List[str]] = None
    auto_email: bool = False


class ReportScheduleRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    template_id: str
    frequency: str = Field(
        ..., pattern="^(once|daily|weekly|monthly|quarterly|yearly)$"
    )
    start_date: datetime
    end_date: Optional[datetime] = None
    hour: int = Field(default=9, ge=0, le=23)
    minute: int = Field(default=0, ge=0, le=59)
    day_of_week: Optional[int] = Field(None, ge=0, le=6)  # For weekly
    day_of_month: Optional[int] = Field(None, ge=1, le=31)  # For monthly
    format: str = Field(default="pdf", pattern="^(pdf|excel|csv|html|json)$")
    filters: Optional[Dict[str, Any]] = Field(default={})
    parameters: Optional[Dict[str, Any]] = Field(default={})
    school_id: Optional[str] = None
    class_id: Optional[str] = None
    recipients: Optional[List[str]] = None
    auto_email: bool = False


class ReportEmailRequest(BaseModel):
    report_id: str
    recipients: List[str] = []
    subject: Optional[str] = None
    message: Optional[str] = None


class ReportResponse(BaseModel):
    id: str
    name: str
    type: str
    format: str
    status: str
    template_id: Optional[str]
    generated_by: Optional[str]
    filters: Optional[Dict[str, Any]]
    parameters: Optional[Dict[str, Any]]
    school_id: Optional[str]
    class_id: Optional[str]
    file_path: Optional[str]
    file_size: Optional[int]
    generated_at: Optional[datetime]
    generation_time: Optional[float]
    error_message: Optional[str]
    recipients: Optional[List[str]]
    emailed_at: Optional[datetime]
    row_count: Optional[int]
    page_count: Optional[int]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class ReportScheduleResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    template_id: str
    frequency: str
    start_date: datetime
    end_date: Optional[datetime]
    next_run: Optional[datetime]
    last_run: Optional[datetime]
    hour: int
    minute: int
    day_of_week: Optional[int]
    day_of_month: Optional[int]
    format: str
    filters: Optional[Dict[str, Any]]
    parameters: Optional[Dict[str, Any]]
    school_id: Optional[str]
    class_id: Optional[str]
    recipients: Optional[List[str]]
    auto_email: bool
    created_by: Optional[str]
    is_active: bool
    failure_count: int
    created_at: datetime
    updated_at: Optional[datetime]

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


def require_admin_or_teacher(current_user: User = Depends(get_current_user)):
    """Require admin or teacher role for access"""
    if current_user.role not in [UserRole.ADMIN, UserRole.TEACHER]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin or teacher access required",
        )
    return current_user


# ==================== Helper Functions ====================


def calculate_next_run(schedule: ReportSchedule) -> Optional[datetime]:
    """Calculate the next run time for a scheduled report (may return None)"""
    current_time = now()

    if schedule.frequency == ReportFrequency.ONCE:
        return schedule.start_date if schedule.start_date > current_time else None

    # Calculate based on frequency
    next_run = schedule.start_date

    if schedule.frequency == ReportFrequency.DAILY:
        while next_run <= current_time:
            next_run += timedelta(days=1)
    elif schedule.frequency == ReportFrequency.WEEKLY:
        while next_run <= current_time:
            next_run += timedelta(weeks=1)
    elif schedule.frequency == ReportFrequency.MONTHLY:
        while next_run <= current_time:
            # Add month (approximately)
            next_run += timedelta(days=30)
    elif schedule.frequency == ReportFrequency.QUARTERLY:
        while next_run <= current_time:
            next_run += timedelta(days=90)
    elif schedule.frequency == ReportFrequency.YEARLY:
        while next_run <= current_time:
            next_run += timedelta(days=365)

    # Apply end date constraint
    if schedule.end_date and next_run > schedule.end_date:
        return None

    return next_run


# ==================== Endpoints ====================


@router.get("/templates", response_model=List[ReportTemplateResponse])
async def list_report_templates(
    popular_only: bool = Query(False),
    category: Optional[str] = None,
    type: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List available report templates"""
    query = db.query(ReportTemplate).filter(ReportTemplate.is_active == True)

    if popular_only:
        query = query.filter(ReportTemplate.is_popular == True)

    if category:
        query = query.filter(ReportTemplate.category == category)

    if type:
        # Convert type to lowercase to match enum values in database
        query = query.filter(ReportTemplate.type == type.lower())

    templates = query.all()
    return templates


@router.get("/", response_model=List[ReportResponse])
async def list_reports(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    status: Optional[str] = None,
    type: Optional[str] = None,
    school_id: Optional[str] = None,
    class_id: Optional[str] = None,
    generated_by_me: bool = False,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List reports with optional filtering"""
    query = db.query(Report)

    # Filter by user's access
    if current_user.role == UserRole.TEACHER:
        # Teachers see reports for their classes
        # Build subquery for teacher's class ids and guard against empty result
        teacher_class_ids_q = db.query(Class.id).filter(
            Class.teacher_id == current_user.id
        )
        teacher_class_ids = [c.id for c in teacher_class_ids_q.all()]
        if teacher_class_ids:
            query = query.filter(
                or_(
                    Report.generated_by == current_user.id,
                    Report.class_id.in_(teacher_class_ids),
                )
            )
        else:
            query = query.filter(Report.generated_by == current_user.id)
    elif current_user.role == UserRole.STUDENT:
        # Students only see reports generated for them
        query = query.filter(Report.generated_by == current_user.id)

    if status:
        query = query.filter(Report.status == status)

    if type:
        query = query.filter(Report.type == type)

    if school_id:
        query = query.filter(Report.school_id == school_id)

    if class_id:
        query = query.filter(Report.class_id == class_id)

    if generated_by_me:
        query = query.filter(Report.generated_by == current_user.id)

    # Order by creation date descending
    query = query.order_by(Report.created_at.desc())

    reports = query.offset(skip).limit(limit).all()
    return reports


@router.get("/{report_id}", response_model=ReportResponse)
async def get_report(
    report_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get a specific report by ID"""
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Report not found"
        )

    # Check access permissions
    if current_user.role == UserRole.STUDENT:
        if report.generated_by != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Access denied"
            )
    elif current_user.role == UserRole.TEACHER:
        if report.generated_by != current_user.id:
            # Check if teacher has access to the class
            if report.class_id:
                class_obj = (
                    db.query(Class)
                    .filter(
                        Class.id == report.class_id, Class.teacher_id == current_user.id
                    )
                    .first()
                )
                if not class_obj:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN, detail="Access denied"
                    )

    return report


@router.post(
    "/generate", response_model=ReportResponse, status_code=status.HTTP_201_CREATED
)
async def generate_report(
    request: ReportGenerateRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_admin_or_teacher),
    db: Session = Depends(get_db),
):
    """Generate a new report"""
    # Create report record
    report = Report(
        id=str(uuid.uuid4()),
        name=request.name,
        type=request.type,
        format=request.format,
        status=ReportStatus.PENDING,
        template_id=request.template_id,
        generated_by=current_user.id,
        filters=request.filters,
        parameters=request.parameters,
        school_id=request.school_id,
        class_id=request.class_id,
        recipients=request.recipients,
        created_at=now(),
        updated_at=now(),
    )

    db.add(report)
    db.commit()
    db.refresh(report)

    # TODO: Add background task for actual report generation
    # For now, we'll simulate by updating status to generating
    report.status = ReportStatus.GENERATING
    db.commit()

    return report


@router.post(
    "/schedule",
    response_model=ReportScheduleResponse,
    status_code=status.HTTP_201_CREATED,
)
async def schedule_report(
    request: ReportScheduleRequest,
    current_user: User = Depends(require_admin_or_teacher),
    db: Session = Depends(get_db),
):
    """Schedule a report for automatic generation"""
    # Verify template exists
    template = (
        db.query(ReportTemplate)
        .filter(
            ReportTemplate.id == request.template_id, ReportTemplate.is_active == True
        )
        .first()
    )
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Template not found"
        )

    # Create schedule
    schedule = ReportSchedule(
        id=str(uuid.uuid4()),
        name=request.name,
        description=request.description,
        template_id=request.template_id,
        frequency=request.frequency,
        start_date=request.start_date,
        end_date=request.end_date,
        hour=request.hour,
        minute=request.minute,
        day_of_week=request.day_of_week,
        day_of_month=request.day_of_month,
        format=request.format,
        filters=request.filters,
        parameters=request.parameters,
        school_id=request.school_id,
        class_id=request.class_id,
        recipients=request.recipients,
        auto_email=request.auto_email,
        created_by=current_user.id,
        is_active=True,
        created_at=now(),
        updated_at=now(),
    )

    # Calculate next run
    schedule.next_run = calculate_next_run(schedule)

    db.add(schedule)
    db.commit()
    db.refresh(schedule)

    return schedule


@router.post("/email", status_code=status.HTTP_200_OK)
async def email_report(
    request: ReportEmailRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_admin_or_teacher),
    db: Session = Depends(get_db),
):
    """Email a generated report to recipients"""
    # Get report
    report = db.query(Report).filter(Report.id == request.report_id).first()
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Report not found"
        )

    # Check if report is ready
    if report.status != ReportStatus.READY:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Report is not ready for emailing",
        )

    # Update recipients
    report.recipients = request.recipients
    report.emailed_at = now()
    db.commit()

    # TODO: Add background task for actual email sending

    return {"message": "Report emailed successfully", "recipients": request.recipients}


@router.get("/{report_id}/download")
async def download_report(
    report_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Download a generated report file"""
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Report not found"
        )

    # Check access (same as get_report)
    if current_user.role == UserRole.STUDENT:
        if report.generated_by != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Access denied"
            )

    # Check if report is ready
    if report.status != ReportStatus.READY:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Report is not ready for download",
        )

    # For now, return a placeholder response
    # TODO: Implement actual file serving
    if report.format == ReportFormat.JSON:
        # Return JSON data directly
        sample_data = {
            "report_id": report.id,
            "name": report.name,
            "type": report.type,
            "generated_at": (
                report.generated_at.isoformat() if report.generated_at else None
            ),
            "data": [],  # Placeholder
        }
        return sample_data
    else:
        # Return a message for other formats (will implement file serving later)
        return {
            "message": f"Report download for {report.format} format will be implemented",
            "report_id": report.id,
            "format": report.format,
        }


@router.delete("/{report_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_report(
    report_id: str,
    current_user: User = Depends(require_admin_or_teacher),
    db: Session = Depends(get_db),
):
    """Delete a report"""
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Report not found"
        )

    # Check ownership
    if current_user.role == UserRole.TEACHER and report.generated_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete your own reports",
        )

    # Delete report file if it exists
    if report.file_path and os.path.exists(report.file_path):
        try:
            os.remove(report.file_path)
        except:
            pass  # Ignore file deletion errors

    db.delete(report)
    db.commit()

    return None


@router.get("/schedules/", response_model=List[ReportScheduleResponse])
async def list_scheduled_reports(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    active_only: bool = Query(True),
    current_user: User = Depends(require_admin_or_teacher),
    db: Session = Depends(get_db),
):
    """List scheduled reports"""
    query = db.query(ReportSchedule)

    if current_user.role == UserRole.TEACHER:
        query = query.filter(ReportSchedule.created_by == current_user.id)

    if active_only:
        query = query.filter(ReportSchedule.is_active == True)

    schedules = query.offset(skip).limit(limit).all()
    return schedules


@router.put("/schedules/{schedule_id}/cancel", response_model=ReportScheduleResponse)
async def cancel_scheduled_report(
    schedule_id: str,
    current_user: User = Depends(require_admin_or_teacher),
    db: Session = Depends(get_db),
):
    """Cancel a scheduled report"""
    schedule = db.query(ReportSchedule).filter(ReportSchedule.id == schedule_id).first()
    if not schedule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Schedule not found"
        )

    # Check ownership
    if current_user.role == UserRole.TEACHER and schedule.created_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only cancel your own schedules",
        )

    schedule.is_active = False
    schedule.updated_at = now()
    db.commit()
    db.refresh(schedule)

    return schedule


@router.get("/stats/overview")
async def get_report_statistics(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """Get report statistics overview"""
    # Base query based on user role
    base_query = db.query(Report)
    if current_user.role == UserRole.TEACHER:
        base_query = base_query.filter(Report.generated_by == current_user.id)
    elif current_user.role == UserRole.STUDENT:
        return {"message": "Statistics not available for students"}

    # Calculate statistics
    total_reports = base_query.count()
    reports_this_month = base_query.filter(
        Report.created_at >= now() - timedelta(days=30)
    ).count()

    scheduled_reports = (
        db.query(ReportSchedule).filter(ReportSchedule.is_active == True).count()
    )

    # Get next scheduled report
    next_scheduled = (
        db.query(ReportSchedule)
        .filter(ReportSchedule.is_active == True, ReportSchedule.next_run != None)
        .order_by(ReportSchedule.next_run)
        .first()
    )

    # Calculate storage (placeholder)
    total_storage = (
        base_query.filter(Report.file_size != None)
        .with_entities(func.sum(Report.file_size))
        .scalar()
        or 0
    )

    # Count recipients
    total_recipients = 0
    for report in base_query.filter(Report.recipients != None).all():
        if report.recipients:
            total_recipients += len(report.recipients)

    return {
        "reports_generated": total_reports,
        "reports_this_month": reports_this_month,
        "scheduled_reports": scheduled_reports,
        "next_scheduled_time": next_scheduled.next_run if next_scheduled else None,
        "total_recipients": total_recipients,
        "storage_used_bytes": total_storage,
        "storage_used_gb": round(total_storage / (1024**3), 2),
    }
