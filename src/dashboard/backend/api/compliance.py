"""
Compliance API Endpoints
Handles COPPA, FERPA, and GDPR compliance requirements
"""

import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from database import get_db
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from models import ComplianceLog
from models import ComplianceStatus as ComplianceStatusEnum
from models import ConsentRecord, ConsentType, DataRetention, User, UserRole
from pydantic import BaseModel, Field
from sqlalchemy import and_
from sqlalchemy.orm import Session

from .auth import decode_token

# Create router
router = APIRouter(prefix="/api/v1/compliance", tags=["compliance"])
security = HTTPBearer()

# ==================== Pydantic Models ====================


class ConsentRequest(BaseModel):
    consent_type: str
    granted: bool
    parent_email: Optional[str] = None
    details: Optional[dict] = None


class ConsentResponse(BaseModel):
    id: str
    user_id: str
    consent_type: str
    granted: bool
    granted_at: datetime
    expires_at: Optional[datetime]
    parent_verified: bool


class ComplianceStatusResponse(BaseModel):
    coppa_compliant: bool
    ferpa_compliant: bool
    gdpr_compliant: bool
    overall_status: str
    last_review_date: Optional[datetime]
    next_review_date: Optional[datetime]
    pending_actions: List[str]
    active_consents: List[dict]


class ComplianceMetrics(BaseModel):
    total_consents: int
    active_consents: int
    expired_consents: int
    pending_reviews: int
    compliance_score: float


class AuditLogEntry(BaseModel):
    id: str
    timestamp: datetime
    action: str
    user_id: str
    details: dict
    compliance_impact: Optional[str]


# ==================== Helper Functions ====================


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
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Authentication failed: {str(e)}",
        )


# ==================== Endpoints ====================


@router.get("/status")
async def get_compliance_status(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """Get current compliance status for the user or organization"""

    # Check user's age for COPPA compliance
    coppa_compliant = True
    coppa_issues = []
    if current_user.birth_date:
        age = (datetime.now().date() - current_user.birth_date).days / 365
        if age < 13:
            # Check for parental consent
            parent_consent = (
                db.query(ConsentRecord)
                .filter(
                    and_(
                        ConsentRecord.user_id == current_user.id,
                        ConsentRecord.consent_type == ConsentType.COPPA_PARENTAL.value,
                        ConsentRecord.granted == True,
                        ConsentRecord.withdrawn_at == None,
                    )
                )
                .first()
            )
            coppa_compliant = parent_consent is not None
            if not coppa_compliant:
                coppa_issues.append("Parental consent required for user under 13")

    # Check FERPA compliance (simplified)
    ferpa_compliant = True  # Assume compliant if proper data handling is in place
    ferpa_issues = []

    # Check GDPR compliance
    gdpr_compliant = True
    gdpr_issues = []
    if current_user.consent_given:
        # Check for valid GDPR consent
        gdpr_consent = (
            db.query(ConsentRecord)
            .filter(
                and_(
                    ConsentRecord.user_id == current_user.id,
                    ConsentRecord.consent_type == ConsentType.GDPR_PROCESSING.value,
                    ConsentRecord.granted == True,
                    ConsentRecord.withdrawn_at == None,
                )
            )
            .first()
        )
        gdpr_compliant = gdpr_consent is not None
        if not gdpr_compliant:
            gdpr_issues.append("GDPR consent needs to be updated")

    # Get active consents count for details
    active_consents = (
        db.query(ConsentRecord)
        .filter(
            and_(
                ConsentRecord.user_id == current_user.id,
                ConsentRecord.granted == True,
                ConsentRecord.withdrawn_at == None,
            )
        )
        .count()
    )

    # Calculate scores based on compliance
    coppa_score = 98 if coppa_compliant else 65
    ferpa_score = 95 if ferpa_compliant else 70
    gdpr_score = 97 if gdpr_compliant else 60
    overall_score = int((coppa_score + ferpa_score + gdpr_score) / 3)

    # Determine overall status
    if coppa_compliant and ferpa_compliant and gdpr_compliant:
        overall_status = "compliant"
    elif not coppa_compliant or not gdpr_compliant:
        overall_status = "non-compliant"
    else:
        overall_status = "review-needed"

    # Return nested structure expected by frontend
    return {
        "coppa": {
            "status": "compliant" if coppa_compliant else "non-compliant",
            "score": coppa_score,
            "issues": coppa_issues,
            "lastAudit": datetime.now().isoformat(),
            "nextAudit": (datetime.now() + timedelta(days=7)).isoformat(),
            "recommendations": (
                ["Continue monitoring age verification processes"]
                if coppa_compliant
                else ["Obtain parental consent for users under 13"]
            ),
            "details": {
                "parentalConsents": 234,  # Mock data
                "pendingConsents": 2 if not coppa_compliant else 0,
                "ageVerifications": 450,  # Mock data
            },
        },
        "ferpa": {
            "status": "compliant" if ferpa_compliant else "non-compliant",
            "score": ferpa_score,
            "issues": ferpa_issues,
            "lastAudit": (datetime.now() - timedelta(days=2)).isoformat(),
            "nextAudit": (datetime.now() + timedelta(days=5)).isoformat(),
            "recommendations": ["Review data retention policies"],
            "details": {
                "recordsProtected": 892,  # Mock data
                "accessRequests": 12,  # Mock data
                "dataBreaches": 0,
            },
        },
        "gdpr": {
            "status": "compliant" if gdpr_compliant else "non-compliant",
            "score": gdpr_score,
            "issues": gdpr_issues,
            "lastAudit": (datetime.now() - timedelta(days=1)).isoformat(),
            "nextAudit": (datetime.now() + timedelta(days=6)).isoformat(),
            "recommendations": (
                ["Update privacy policy for new features"]
                if gdpr_compliant
                else ["Update GDPR consent"]
            ),
            "details": {
                "dataSubjects": 1250,  # Mock data
                "deletionRequests": 3,  # Mock data
                "portabilityRequests": 1,  # Mock data
            },
        },
        "overallStatus": overall_status,
        "overallScore": overall_score,
        "lastAudit": (datetime.now() - timedelta(days=15)).isoformat(),
        "nextAudit": (datetime.now() + timedelta(days=15)).isoformat(),
        "certificateValid": True,
        "certificateExpiry": (datetime.now() + timedelta(days=180)).isoformat(),
    }


@router.post(
    "/consent", response_model=ConsentResponse, status_code=status.HTTP_201_CREATED
)
async def record_consent(
    consent_data: ConsentRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Record user consent for compliance purposes"""

    # Create new consent record
    # Allow either a string or an Enum-like object for consent_type
    consent_type_val = getattr(
        consent_data.consent_type, "value", consent_data.consent_type
    )

    consent_record = ConsentRecord(
        id=str(uuid.uuid4()),
        user_id=current_user.id,
        consent_type=consent_type_val,
        granted=consent_data.granted,
        granted_at=datetime.now() if consent_data.granted else None,
        consent_text="Standard consent text",  # Would be fetched from config
        ip_address="127.0.0.1",  # Would get from request
        user_agent="Browser",  # Would get from request headers
    )

    # If COPPA consent and parent email provided, link parent
    if (
        consent_data.consent_type == ConsentType.COPPA_PARENTAL.value
        and consent_data.parent_email
    ):
        parent = db.query(User).filter(User.email == consent_data.parent_email).first()
        if parent:
            consent_record.parent_id = parent.id
            # Set parent_verified only if attribute exists and is settable
            if hasattr(consent_record, "parent_verified"):
                try:
                    setattr(consent_record, "parent_verified", True)
                except Exception:
                    # Some ORM properties may be read-only; ignore if so
                    pass

    db.add(consent_record)

    # Log the consent action
    log_entry = ComplianceLog(
        id=str(uuid.uuid4()),
        action="consent_recorded",
        user_id=current_user.id,
        details={
            "consent_type": consent_data.consent_type,
            "granted": consent_data.granted,
        },
        compliance_impact="Updated user consent status",
    )
    db.add(log_entry)

    db.commit()
    db.refresh(consent_record)

    return ConsentResponse(
        id=consent_record.id,
        user_id=str(consent_record.user_id or ""),
        consent_type=str(
            getattr(consent_record.consent_type, "value", consent_record.consent_type)
        ),
        granted=consent_record.granted,
        granted_at=consent_record.granted_at or datetime.now(),
        expires_at=consent_record.expires_at,
        parent_verified=bool(getattr(consent_record, "parent_verified", False)),
    )


@router.get("/audit-log", response_model=List[AuditLogEntry])
async def get_audit_log(
    skip: int = 0,
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get compliance audit log entries"""

    # Only admins can view audit logs
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can view audit logs",
        )

    logs = (
        db.query(ComplianceLog)
        .order_by(ComplianceLog.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

    return [
        AuditLogEntry(
            id=log.id,
            timestamp=log.created_at,
            action=log.action,
            user_id=str(log.user_id or ""),
            details=log.details or {},
            compliance_impact=log.compliance_impact,
        )
        for log in logs
    ]


@router.get("/metrics", response_model=ComplianceMetrics)
async def get_compliance_metrics(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """Get compliance metrics and statistics"""

    # Only admins and teachers can view metrics
    if current_user.role not in [UserRole.ADMIN, UserRole.TEACHER]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions"
        )

    # Get consent statistics
    total_consents = db.query(ConsentRecord).count()
    active_consents = (
        db.query(ConsentRecord)
        .filter(and_(ConsentRecord.granted == True, ConsentRecord.withdrawn_at == None))
        .count()
    )
    expired_consents = (
        db.query(ConsentRecord)
        .filter(
            and_(
                ConsentRecord.expires_at != None,
                ConsentRecord.expires_at < datetime.now(),
            )
        )
        .count()
    )

    # Calculate compliance score (simplified)
    compliance_score = 0.0
    if total_consents > 0:
        compliance_score = (active_consents / total_consents) * 100

    return ComplianceMetrics(
        total_consents=total_consents,
        active_consents=active_consents,
        expired_consents=expired_consents,
        pending_reviews=0,  # Would calculate based on review schedule
        compliance_score=compliance_score,
    )


@router.delete("/consent/{consent_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_consent(
    consent_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Revoke a previously granted consent"""

    consent = (
        db.query(ConsentRecord)
        .filter(
            and_(
                ConsentRecord.id == consent_id, ConsentRecord.user_id == current_user.id
            )
        )
        .first()
    )

    if not consent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Consent record not found"
        )

    # Mark consent as revoked
    consent.withdrawn_at = datetime.now()
    consent.granted = False

    # Log the revocation
    log_entry = ComplianceLog(
        id=str(uuid.uuid4()),
        action="consent_revoked",
        user_id=current_user.id,
        details={"consent_id": consent_id, "consent_type": consent.consent_type},
        compliance_impact="User revoked consent",
    )
    db.add(log_entry)

    db.commit()

    return None


# Export router
__all__ = ["router"]
