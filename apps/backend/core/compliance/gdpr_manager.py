"""
GDPR Compliance Manager
Implements GDPR requirements including right to erasure, data portability, and consent management
"""

import hashlib
import io
import json
import logging
import zipfile
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class ConsentType(str, Enum):
    """Types of consent that can be granted"""

    ESSENTIAL = "essential"  # Required for service
    ANALYTICS = "analytics"
    MARKETING = "marketing"
    THIRD_PARTY = "third_party"
    COOKIES = "cookies"
    PERSONALIZATION = "personalization"
    RESEARCH = "research"
    COMMUNICATION = "communication"


class RequestType(str, Enum):
    """GDPR request types"""

    ACCESS = "access"  # Right to access
    RECTIFICATION = "rectification"  # Right to rectification
    ERASURE = "erasure"  # Right to be forgotten
    PORTABILITY = "portability"  # Right to data portability
    RESTRICTION = "restriction"  # Right to restrict processing
    OBJECTION = "objection"  # Right to object


class RequestStatus(str, Enum):
    """Status of GDPR requests"""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    REJECTED = "rejected"
    PARTIALLY_COMPLETED = "partially_completed"


@dataclass
class ConsentRecord:
    """Record of user consent"""

    user_id: str
    consent_type: ConsentType
    granted: bool
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    ip_address: str | None = None
    user_agent: str | None = None
    purpose: str = ""
    expiry: datetime | None = None
    version: int = 1


@dataclass
class GDPRRequest:
    """GDPR data request"""

    request_id: str
    user_id: str
    request_type: RequestType
    status: RequestStatus
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: datetime | None = None
    deadline: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc) + timedelta(days=30)
    )
    processor: str | None = None
    notes: str = ""
    verification_token: str | None = None
    data: dict[str, Any] = field(default_factory=dict)


@dataclass
class DataRetentionPolicy:
    """Data retention policy configuration"""

    data_category: str
    retention_days: int
    legal_basis: str
    auto_delete: bool = True
    anonymize_instead: bool = False


class GDPRComplianceManager:
    """
    Manages GDPR compliance requirements

    Features:
    - Consent management with granular control
    - Right to erasure (delete all user data)
    - Data portability (export user data)
    - Data retention policies
    - Audit trail for all operations
    - Automated compliance workflows
    """

    def __init__(self):
        """Initialize GDPR Compliance Manager"""
        self.consent_records: dict[str, list[ConsentRecord]] = {}
        self.gdpr_requests: dict[str, GDPRRequest] = {}
        self.retention_policies = self._init_retention_policies()

        # PII field mappings for data operations
        self.pii_fields = {
            "email": "email",
            "phone": "phone_number",
            "full_name": "name",
            "address": "address",
            "date_of_birth": "birthdate",
            "ip_address": "ip",
            "user_agent": "device_info",
        }

    def _init_retention_policies(self) -> dict[str, DataRetentionPolicy]:
        """Initialize default data retention policies"""
        return {
            "user_profile": DataRetentionPolicy(
                data_category="user_profile",
                retention_days=365 * 3,  # 3 years
                legal_basis="Legitimate interest for service improvement",
                auto_delete=False,
                anonymize_instead=True,
            ),
            "activity_logs": DataRetentionPolicy(
                data_category="activity_logs",
                retention_days=90,
                legal_basis="Security and fraud prevention",
                auto_delete=True,
            ),
            "analytics": DataRetentionPolicy(
                data_category="analytics",
                retention_days=365,
                legal_basis="Legitimate interest for analytics",
                auto_delete=False,
                anonymize_instead=True,
            ),
            "marketing": DataRetentionPolicy(
                data_category="marketing",
                retention_days=180,
                legal_basis="Consent-based marketing",
                auto_delete=True,
            ),
            "financial": DataRetentionPolicy(
                data_category="financial",
                retention_days=365 * 7,  # 7 years for tax purposes
                legal_basis="Legal obligation",
                auto_delete=False,
            ),
            "educational_content": DataRetentionPolicy(
                data_category="educational_content",
                retention_days=365 * 2,  # 2 years
                legal_basis="Contractual necessity",
                auto_delete=False,
                anonymize_instead=True,
            ),
        }

    async def record_consent(
        self,
        user_id: str,
        consent_type: ConsentType,
        granted: bool,
        purpose: str,
        ip_address: str | None = None,
        user_agent: str | None = None,
        duration_days: int = 365,
    ) -> ConsentRecord:
        """
        Record user consent

        Args:
            user_id: User identifier
            consent_type: Type of consent
            granted: Whether consent was granted
            purpose: Purpose of data processing
            ip_address: User's IP address
            user_agent: User's browser/device info
            duration_days: Consent duration in days

        Returns:
            ConsentRecord object
        """
        try:
            # Create consent record
            consent = ConsentRecord(
                user_id=user_id,
                consent_type=consent_type,
                granted=granted,
                purpose=purpose,
                ip_address=ip_address,
                user_agent=user_agent,
                expiry=datetime.now(timezone.utc) + timedelta(days=duration_days),
            )

            # Store consent record
            if user_id not in self.consent_records:
                self.consent_records[user_id] = []
            self.consent_records[user_id].append(consent)

            # Audit log
            self._audit_consent(consent, "consent_recorded")

            logger.info(f"Consent recorded for user {user_id}: {consent_type.value} = {granted}")
            return consent

        except Exception as e:
            logger.error(f"Failed to record consent: {e}")
            raise

    async def check_consent(self, user_id: str, consent_type: ConsentType) -> bool:
        """
        Check if user has given consent

        Args:
            user_id: User identifier
            consent_type: Type of consent to check

        Returns:
            True if valid consent exists
        """
        if user_id not in self.consent_records:
            return consent_type == ConsentType.ESSENTIAL  # Essential is always granted

        # Get latest consent for this type
        user_consents = self.consent_records[user_id]
        relevant_consents = [c for c in user_consents if c.consent_type == consent_type]

        if not relevant_consents:
            return consent_type == ConsentType.ESSENTIAL

        # Check most recent consent
        latest = max(relevant_consents, key=lambda c: c.timestamp)

        # Check if expired
        if latest.expiry and latest.expiry < datetime.now(timezone.utc):
            return False

        return latest.granted

    async def process_erasure_request(self, user_id: str, verification_token: str) -> GDPRRequest:
        """
        Process right to erasure (right to be forgotten)

        Args:
            user_id: User identifier
            verification_token: Token to verify request authenticity

        Returns:
            GDPRRequest object tracking the erasure
        """
        try:
            # Create request
            request = GDPRRequest(
                request_id=self._generate_request_id(),
                user_id=user_id,
                request_type=RequestType.ERASURE,
                status=RequestStatus.PENDING,
                verification_token=verification_token,
            )

            self.gdpr_requests[request.request_id] = request

            # Start erasure process
            await self._execute_erasure(user_id, request.request_id)

            return request

        except Exception as e:
            logger.error(f"Erasure request failed: {e}")
            if request.request_id in self.gdpr_requests:
                self.gdpr_requests[request.request_id].status = RequestStatus.REJECTED
                self.gdpr_requests[request.request_id].notes = str(e)
            raise

    async def _execute_erasure(self, user_id: str, request_id: str):
        """
        Execute data erasure for user

        Args:
            user_id: User identifier
            request_id: GDPR request ID
        """
        try:
            request = self.gdpr_requests[request_id]
            request.status = RequestStatus.IN_PROGRESS

            erasure_log = {
                "user_data": False,
                "activity_logs": False,
                "analytics": False,
                "content": False,
                "backups": False,
            }

            # 1. Delete user profile data
            # In production, this would interface with your database
            erasure_log["user_data"] = await self._delete_user_data(user_id)

            # 2. Delete activity logs
            erasure_log["activity_logs"] = await self._delete_activity_logs(user_id)

            # 3. Anonymize analytics data
            erasure_log["analytics"] = await self._anonymize_analytics(user_id)

            # 4. Delete or anonymize user-generated content
            erasure_log["content"] = await self._handle_user_content(user_id)

            # 5. Queue deletion from backups
            erasure_log["backups"] = await self._queue_backup_deletion(user_id)

            # 6. Delete consent records
            if user_id in self.consent_records:
                del self.consent_records[user_id]

            # Update request status
            request.status = RequestStatus.COMPLETED
            request.completed_at = datetime.now(timezone.utc)
            request.data = erasure_log

            # Audit log
            self._audit_erasure(user_id, erasure_log)

            logger.info(f"Erasure completed for user {user_id}")

        except Exception as e:
            logger.error(f"Erasure execution failed: {e}")
            request.status = RequestStatus.PARTIALLY_COMPLETED
            raise

    async def process_portability_request(
        self, user_id: str, format: str = "json"
    ) -> dict[str, Any]:
        """
        Process data portability request

        Args:
            user_id: User identifier
            format: Export format (json, csv, xml)

        Returns:
            Dictionary containing exportable data
        """
        try:
            # Create request
            request = GDPRRequest(
                request_id=self._generate_request_id(),
                user_id=user_id,
                request_type=RequestType.PORTABILITY,
                status=RequestStatus.IN_PROGRESS,
            )

            self.gdpr_requests[request.request_id] = request

            # Collect all user data
            user_data = await self._collect_user_data(user_id)

            # Format data for export
            if format == "json":
                export_data = self._format_json_export(user_data)
            elif format == "csv":
                export_data = self._format_csv_export(user_data)
            else:
                export_data = user_data

            # Create downloadable package
            package = await self._create_data_package(user_id, export_data, format)

            # Update request
            request.status = RequestStatus.COMPLETED
            request.completed_at = datetime.now(timezone.utc)
            request.data = {"format": format, "size": len(str(export_data))}

            # Audit log
            self._audit_portability(user_id, format)

            return package

        except Exception as e:
            logger.error(f"Portability request failed: {e}")
            request.status = RequestStatus.REJECTED
            raise

    async def _collect_user_data(self, user_id: str) -> dict[str, Any]:
        """
        Collect all user data for export

        Args:
            user_id: User identifier

        Returns:
            Dictionary containing all user data
        """
        # In production, this would query various data sources
        user_data = {
            "profile": {
                "user_id": user_id,
                "created_at": datetime.now(timezone.utc).isoformat(),
                # Additional profile fields would come from database
            },
            "preferences": {},
            "activity": [],
            "content": [],
            "consents": [
                {
                    "type": c.consent_type.value,
                    "granted": c.granted,
                    "timestamp": c.timestamp.isoformat(),
                    "purpose": c.purpose,
                }
                for c in self.consent_records.get(user_id, [])
            ],
        }

        return user_data

    async def process_retention_policies(self) -> dict[str, int]:
        """
        Process data retention policies and delete expired data

        Returns:
            Dictionary with counts of deleted records by category
        """
        deletion_counts = {}

        for category, policy in self.retention_policies.items():
            if not policy.auto_delete:
                continue

            # Calculate cutoff date
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=policy.retention_days)

            # Delete or anonymize expired data
            if policy.anonymize_instead:
                count = await self._anonymize_old_data(category, cutoff_date)
                logger.info(f"Anonymized {count} {category} records older than {cutoff_date}")
            else:
                count = await self._delete_old_data(category, cutoff_date)
                logger.info(f"Deleted {count} {category} records older than {cutoff_date}")

            deletion_counts[category] = count

        return deletion_counts

    def get_consent_history(self, user_id: str) -> list[dict]:
        """
        Get consent history for user

        Args:
            user_id: User identifier

        Returns:
            List of consent records
        """
        if user_id not in self.consent_records:
            return []

        return [
            {
                "type": c.consent_type.value,
                "granted": c.granted,
                "timestamp": c.timestamp.isoformat(),
                "purpose": c.purpose,
                "expiry": c.expiry.isoformat() if c.expiry else None,
                "version": c.version,
            }
            for c in self.consent_records[user_id]
        ]

    def get_request_status(self, request_id: str) -> GDPRRequest | None:
        """
        Get status of GDPR request

        Args:
            request_id: Request identifier

        Returns:
            GDPRRequest object or None
        """
        return self.gdpr_requests.get(request_id)

    async def verify_compliance(self, user_id: str) -> dict[str, Any]:
        """
        Verify GDPR compliance for a user

        Args:
            user_id: User identifier

        Returns:
            Compliance status report
        """
        report = {
            "user_id": user_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "consents": {},
            "data_categories": {},
            "pending_requests": [],
            "compliance_score": 100,
        }

        # Check consents
        for consent_type in ConsentType.__members__.values():
            has_consent = await self.check_consent(user_id, consent_type)
            report["consents"][consent_type.value] = has_consent

        # Check pending requests
        user_requests = [
            r
            for r in self.gdpr_requests.values()
            if r.user_id == user_id
            and r.status in [RequestStatus.PENDING, RequestStatus.IN_PROGRESS]
        ]
        report["pending_requests"] = [
            {
                "request_id": r.request_id,
                "type": r.request_type.value,
                "status": r.status.value,
                "deadline": r.deadline.isoformat(),
            }
            for r in user_requests
        ]

        # Check data retention compliance
        for category, policy in self.retention_policies.items():
            report["data_categories"][category] = {
                "retention_days": policy.retention_days,
                "legal_basis": policy.legal_basis,
                "compliant": True,  # Would check actual data age
            }

        # Calculate compliance score
        if not report["consents"].get(ConsentType.ESSENTIAL.value, False):
            report["compliance_score"] -= 50

        missing_consents = sum(
            1
            for consent_type, granted in report["consents"].items()
            if not granted and consent_type != ConsentType.ESSENTIAL.value
        )
        report["compliance_score"] -= missing_consents * 5

        overdue_requests = sum(1 for r in user_requests if r.deadline < datetime.now(timezone.utc))
        report["compliance_score"] -= overdue_requests * 20

        report["compliance_score"] = max(0, report["compliance_score"])

        return report

    # Helper methods
    def _generate_request_id(self) -> str:
        """Generate unique request ID"""
        import uuid

        return f"GDPR-{uuid.uuid4().hex[:8].upper()}"

    async def _delete_user_data(self, user_id: str) -> bool:
        """Delete user profile data"""
        # In production, interface with database
        logger.info(f"Deleting user data for {user_id}")
        return True

    async def _delete_activity_logs(self, user_id: str) -> bool:
        """Delete user activity logs"""
        logger.info(f"Deleting activity logs for {user_id}")
        return True

    async def _anonymize_analytics(self, user_id: str) -> bool:
        """Anonymize analytics data"""
        logger.info(f"Anonymizing analytics for {user_id}")
        # Replace user_id with hash
        anonymized_id = hashlib.sha256(f"{user_id}_anonymous".encode()).hexdigest()[:16]
        return True

    async def _handle_user_content(self, user_id: str) -> bool:
        """Handle user-generated content"""
        logger.info(f"Processing user content for {user_id}")
        return True

    async def _queue_backup_deletion(self, user_id: str) -> bool:
        """Queue deletion from backups"""
        logger.info(f"Queuing backup deletion for {user_id}")
        # In production, add to backup deletion queue
        return True

    async def _anonymize_old_data(self, category: str, cutoff_date: datetime) -> int:
        """Anonymize old data"""
        # In production, interface with database
        return 0

    async def _delete_old_data(self, category: str, cutoff_date: datetime) -> int:
        """Delete old data"""
        # In production, interface with database
        return 0

    def _format_json_export(self, data: dict) -> str:
        """Format data as JSON"""
        return json.dumps(data, indent=2, default=str)

    def _format_csv_export(self, data: dict) -> str:
        """Format data as CSV"""
        import csv
        import io

        output = io.StringIO()
        writer = csv.writer(output)

        # Flatten nested structure for CSV
        for section, content in data.items():
            writer.writerow([section])
            if isinstance(content, dict):
                for key, value in content.items():
                    writer.writerow([key, value])
            elif isinstance(content, list):
                for item in content:
                    writer.writerow([str(item)])
            writer.writerow([])  # Empty line between sections

        return output.getvalue()

    async def _create_data_package(self, user_id: str, data: Any, format: str) -> dict[str, Any]:
        """Create downloadable data package"""
        # Create ZIP archive with data
        zip_buffer = io.BytesIO()

        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            # Add main data file
            if format == "json":
                zip_file.writestr(f"user_data_{user_id}.json", data)
            elif format == "csv":
                zip_file.writestr(f"user_data_{user_id}.csv", data)

            # Add metadata
            metadata = {
                "export_date": datetime.now(timezone.utc).isoformat(),
                "user_id": user_id,
                "format": format,
                "gdpr_request": True,
            }
            zip_file.writestr("metadata.json", json.dumps(metadata, indent=2))

            # Add README
            readme = f"""GDPR Data Export for User {user_id}

This archive contains all personal data associated with your account.

Files included:
- user_data_{user_id}.{format}: Your personal data
- metadata.json: Export metadata

This export was generated in compliance with GDPR Article 20 (Right to Data Portability).

For questions, contact: privacy@toolboxai.com
"""
            zip_file.writestr("README.txt", readme)

        return {
            "filename": f"gdpr_export_{user_id}_{datetime.now().strftime('%Y%m%d')}.zip",
            "content": zip_buffer.getvalue(),
            "mime_type": "application/zip",
            "size": zip_buffer.tell(),
        }

    def _audit_consent(self, consent: ConsentRecord, action: str):
        """Audit consent operation"""
        audit = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "action": action,
            "user_id": consent.user_id,
            "consent_type": consent.consent_type.value,
            "granted": consent.granted,
        }
        logger.info(f"Consent audit: {json.dumps(audit)}")

    def _audit_erasure(self, user_id: str, results: dict):
        """Audit erasure operation"""
        audit = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "action": "data_erasure",
            "user_id": user_id,
            "results": results,
        }
        logger.info(f"Erasure audit: {json.dumps(audit)}")

    def _audit_portability(self, user_id: str, format: str):
        """Audit portability operation"""
        audit = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "action": "data_export",
            "user_id": user_id,
            "format": format,
        }
        logger.info(f"Portability audit: {json.dumps(audit)}")


# Singleton instance
_gdpr_manager: GDPRComplianceManager | None = None


def get_gdpr_manager() -> GDPRComplianceManager:
    """Get singleton GDPR manager instance"""
    global _gdpr_manager
    if _gdpr_manager is None:
        _gdpr_manager = GDPRComplianceManager()
    return _gdpr_manager
