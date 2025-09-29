"""
Security Manager for ToolBoxAI Educational Platform Storage

Comprehensive security management including COPPA/FERPA compliance,
PII detection, encryption, access control, and audit logging.

Author: ToolBoxAI Team
Created: 2025-01-27
Version: 1.0.0
"""

import asyncio
import hashlib
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple, Union
from uuid import UUID, uuid4

try:
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    import base64
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False
    logging.warning("Cryptography library not available - encryption will be mocked")

from .storage_service import UploadOptions

logger = logging.getLogger(__name__)


class ComplianceLevel(str, Enum):
    """Compliance requirement levels"""
    NONE = "none"
    STANDARD = "standard"
    COPPA = "coppa"          # Children's Online Privacy Protection Act
    FERPA = "ferpa"          # Family Educational Rights and Privacy Act
    HIPAA = "hipaa"          # Health Insurance Portability and Accountability Act
    GDPR = "gdpr"            # General Data Protection Regulation


class PIIType(str, Enum):
    """Types of Personally Identifiable Information"""
    NONE = "none"
    SSN = "ssn"              # Social Security Number
    EMAIL = "email"
    PHONE = "phone"
    ADDRESS = "address"
    DOB = "date_of_birth"    # Date of Birth
    STUDENT_ID = "student_id"
    CREDIT_CARD = "credit_card"
    BIOMETRIC = "biometric"
    MEDICAL = "medical"
    EDUCATIONAL_RECORD = "educational_record"


class SecurityRisk(str, Enum):
    """Security risk levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class PIIDetectionResult:
    """Result of PII detection analysis"""
    has_pii: bool = False
    pii_types: List[PIIType] = field(default_factory=list)
    confidence_scores: Dict[PIIType, float] = field(default_factory=dict)
    locations: Dict[PIIType, List[str]] = field(default_factory=dict)
    risk_level: SecurityRisk = SecurityRisk.LOW
    recommendations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "has_pii": self.has_pii,
            "pii_types": [pii_type.value for pii_type in self.pii_types],
            "confidence_scores": {k.value: v for k, v in self.confidence_scores.items()},
            "locations": {k.value: v for k, v in self.locations.items()},
            "risk_level": self.risk_level.value,
            "recommendations": self.recommendations
        }


@dataclass
class ComplianceCheck:
    """Result of compliance verification"""
    is_compliant: bool = True
    required_level: ComplianceLevel = ComplianceLevel.STANDARD
    current_level: ComplianceLevel = ComplianceLevel.STANDARD
    issues: List[str] = field(default_factory=list)
    requirements: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    pii_detection: Optional[PIIDetectionResult] = None
    encryption_required: bool = False
    retention_required: bool = False
    audit_required: bool = True

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "is_compliant": self.is_compliant,
            "required_level": self.required_level.value,
            "current_level": self.current_level.value,
            "issues": self.issues,
            "requirements": self.requirements,
            "recommendations": self.recommendations,
            "pii_detection": self.pii_detection.to_dict() if self.pii_detection else None,
            "encryption_required": self.encryption_required,
            "retention_required": self.retention_required,
            "audit_required": self.audit_required
        }


@dataclass
class AccessControlRule:
    """Access control rule definition"""
    rule_id: str
    organization_id: str
    resource_pattern: str
    allowed_roles: List[str]
    allowed_users: List[str] = field(default_factory=list)
    conditions: Dict[str, Any] = field(default_factory=dict)
    expires_at: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.utcnow)


class SecurityManager:
    """
    Comprehensive security management for educational file storage.

    Features:
    - COPPA/FERPA compliance checking
    - PII detection and classification
    - File encryption for sensitive data
    - Access control validation
    - Audit logging
    - Privacy protection measures
    """

    def __init__(self, encryption_key: Optional[str] = None):
        """
        Initialize security manager.

        Args:
            encryption_key: Base encryption key for sensitive files
        """
        self.encryption_key = encryption_key

        # Initialize encryption if available
        if CRYPTO_AVAILABLE and encryption_key:
            self._setup_encryption(encryption_key)
        else:
            self.fernet = None
            if not CRYPTO_AVAILABLE:
                logger.warning("Cryptography not available - encryption will be mocked")

        # PII detection patterns
        self._compile_pii_patterns()

        # Compliance requirements by file category
        self.compliance_requirements = {
            "student_submission": ComplianceLevel.FERPA,
            "educational_content": ComplianceLevel.STANDARD,
            "assessment": ComplianceLevel.FERPA,
            "administrative": ComplianceLevel.FERPA,
            "media_resource": ComplianceLevel.STANDARD,
            "avatar": ComplianceLevel.COPPA,
            "temporary": ComplianceLevel.STANDARD,
            "report": ComplianceLevel.FERPA
        }

        logger.info("SecurityManager initialized")

    async def check_compliance(
        self,
        file_data: bytes,
        filename: str,
        options: UploadOptions,
        organization_context: Optional[Dict[str, Any]] = None
    ) -> ComplianceCheck:
        """
        Perform comprehensive compliance check.

        Args:
            file_data: File content
            filename: Original filename
            options: Upload options
            organization_context: Organization-specific context

        Returns:
            ComplianceCheck: Compliance verification result
        """
        try:
            # Determine required compliance level
            required_level = self.compliance_requirements.get(
                options.file_category,
                ComplianceLevel.STANDARD
            )

            # Initialize compliance check
            compliance = ComplianceCheck(
                required_level=required_level,
                current_level=ComplianceLevel.STANDARD
            )

            # Detect PII in content
            pii_result = await self.detect_pii(file_data, filename)
            compliance.pii_detection = pii_result

            # Check compliance requirements
            await self._check_coppa_compliance(compliance, options, organization_context)
            await self._check_ferpa_compliance(compliance, options, organization_context)
            await self._check_general_privacy_compliance(compliance, pii_result)

            # Determine if encryption is required
            compliance.encryption_required = (
                pii_result.has_pii or
                required_level in [ComplianceLevel.FERPA, ComplianceLevel.COPPA, ComplianceLevel.HIPAA]
            )

            # Set retention requirements
            compliance.retention_required = required_level in [
                ComplianceLevel.FERPA, ComplianceLevel.COPPA
            ]

            # Generate recommendations
            await self._generate_security_recommendations(compliance, pii_result)

            # Final compliance determination
            compliance.is_compliant = len(compliance.issues) == 0

            if not compliance.is_compliant:
                logger.warning(f"Compliance issues detected for {filename}: {compliance.issues}")

            return compliance

        except Exception as e:
            logger.error(f"Compliance check failed: {e}")
            return ComplianceCheck(
                is_compliant=False,
                issues=[f"Compliance check error: {str(e)}"]
            )

    async def detect_pii(
        self,
        file_data: bytes,
        filename: str
    ) -> PIIDetectionResult:
        """
        Detect personally identifiable information in file content.

        Args:
            file_data: File content
            filename: Original filename

        Returns:
            PIIDetectionResult: PII detection results
        """
        result = PIIDetectionResult()

        try:
            # Convert binary data to text for analysis
            text_content = await self._extract_text_content(file_data, filename)

            if not text_content:
                return result

            # Run PII detection patterns
            for pii_type, patterns in self.pii_patterns.items():
                matches = []
                total_confidence = 0.0

                for pattern, confidence in patterns:
                    found_matches = re.finditer(pattern, text_content, re.IGNORECASE)
                    for match in found_matches:
                        matches.append(match.group())
                        total_confidence += confidence

                if matches:
                    result.pii_types.append(pii_type)
                    result.locations[pii_type] = matches[:5]  # Limit to first 5 matches
                    result.confidence_scores[pii_type] = min(1.0, total_confidence / len(matches))

            # Set overall PII detection result
            result.has_pii = len(result.pii_types) > 0

            # Determine risk level
            if result.has_pii:
                result.risk_level = await self._calculate_pii_risk_level(result)

            # Generate recommendations
            if result.has_pii:
                result.recommendations = await self._generate_pii_recommendations(result)

            logger.debug(f"PII detection completed for {filename}: {len(result.pii_types)} types found")
            return result

        except Exception as e:
            logger.error(f"PII detection failed: {e}")
            result.recommendations.append(f"PII detection error: {str(e)}")
            return result

    async def encrypt_sensitive_file(
        self,
        file_data: bytes,
        organization_id: str,
        additional_context: Optional[str] = None
    ) -> Tuple[bytes, Dict[str, Any]]:
        """
        Encrypt sensitive file data.

        Args:
            file_data: File content to encrypt
            organization_id: Organization identifier
            additional_context: Additional encryption context

        Returns:
            Tuple[bytes, Dict[str, Any]]: Encrypted data and metadata
        """
        try:
            if not CRYPTO_AVAILABLE or not self.fernet:
                # Mock encryption for testing
                logger.warning("Using mock encryption - data not actually encrypted")
                return file_data, {
                    "encrypted": False,
                    "algorithm": "mock",
                    "key_id": "mock_key",
                    "context": additional_context
                }

            # Generate organization-specific salt
            salt = self._generate_salt(organization_id)

            # Encrypt the data
            encrypted_data = self.fernet.encrypt(file_data)

            # Create encryption metadata
            metadata = {
                "encrypted": True,
                "algorithm": "Fernet",
                "key_id": self._get_key_id(),
                "salt": base64.b64encode(salt).decode('utf-8'),
                "context": additional_context,
                "encrypted_at": datetime.utcnow().isoformat()
            }

            logger.info(f"File encrypted for organization {organization_id}")
            return encrypted_data, metadata

        except Exception as e:
            logger.error(f"File encryption failed: {e}")
            raise ValueError(f"Encryption failed: {str(e)}")

    async def decrypt_sensitive_file(
        self,
        encrypted_data: bytes,
        metadata: Dict[str, Any],
        organization_id: str
    ) -> bytes:
        """
        Decrypt sensitive file data.

        Args:
            encrypted_data: Encrypted file content
            metadata: Encryption metadata
            organization_id: Organization identifier

        Returns:
            bytes: Decrypted file content
        """
        try:
            if not metadata.get("encrypted", False):
                return encrypted_data

            if not CRYPTO_AVAILABLE or not self.fernet:
                logger.warning("Mock decryption - returning data as-is")
                return encrypted_data

            # Decrypt the data
            decrypted_data = self.fernet.decrypt(encrypted_data)

            logger.info(f"File decrypted for organization {organization_id}")
            return decrypted_data

        except Exception as e:
            logger.error(f"File decryption failed: {e}")
            raise ValueError(f"Decryption failed: {str(e)}")

    async def validate_access_control(
        self,
        file_id: UUID,
        user_id: str,
        organization_id: str,
        action: str = "read",
        context: Optional[Dict[str, Any]] = None
    ) -> Tuple[bool, List[str]]:
        """
        Validate access control for file operations.

        Args:
            file_id: File identifier
            user_id: User requesting access
            organization_id: Organization context
            action: Action being performed (read, write, delete)
            context: Additional context

        Returns:
            Tuple[bool, List[str]]: Access allowed and reasons/violations
        """
        try:
            violations = []

            # Get file metadata (would query database)
            file_metadata = await self._get_file_metadata(file_id)

            if not file_metadata:
                violations.append("File not found")
                return False, violations

            # Check organization isolation
            if file_metadata.get("organization_id") != organization_id:
                violations.append("Organization isolation violation")
                return False, violations

            # Check user permissions
            if not await self._check_user_permissions(user_id, file_metadata, action):
                violations.append(f"Insufficient permissions for {action}")

            # Check file-specific access rules
            if not await self._check_file_access_rules(file_id, user_id, action, context):
                violations.append("File access rule violation")

            # Check compliance-based restrictions
            compliance_violations = await self._check_compliance_access(
                file_metadata, user_id, action, context
            )
            violations.extend(compliance_violations)

            access_allowed = len(violations) == 0

            if not access_allowed:
                logger.warning(f"Access denied for user {user_id} to file {file_id}: {violations}")

            return access_allowed, violations

        except Exception as e:
            logger.error(f"Access control validation failed: {e}")
            return False, [f"Access control error: {str(e)}"]

    async def log_security_event(
        self,
        event_type: str,
        organization_id: str,
        user_id: Optional[str] = None,
        resource_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        severity: str = "info"
    ) -> None:
        """
        Log security-related events for audit trails.

        Args:
            event_type: Type of security event
            organization_id: Organization identifier
            user_id: User associated with event
            resource_id: Resource involved in event
            details: Additional event details
            severity: Event severity level
        """
        try:
            event_record = {
                "event_id": str(uuid4()),
                "event_type": event_type,
                "organization_id": organization_id,
                "user_id": user_id,
                "resource_id": resource_id,
                "severity": severity,
                "timestamp": datetime.utcnow().isoformat(),
                "details": details or {},
                "ip_address": details.get("ip_address") if details else None,
                "user_agent": details.get("user_agent") if details else None
            }

            # Store in audit log (would integrate with logging system)
            await self._store_audit_event(event_record)

            logger.info(f"Security event logged: {event_type} for org {organization_id}")

        except Exception as e:
            logger.error(f"Security event logging failed: {e}")

    # Private helper methods

    def _setup_encryption(self, encryption_key: str) -> None:
        """Setup encryption with the provided key"""
        try:
            # Derive a key from the provided string
            key_bytes = encryption_key.encode()
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=b'stable_salt_for_toolbox_ai',  # In production, use random salt per org
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(key_bytes))
            self.fernet = Fernet(key)

        except Exception as e:
            logger.error(f"Encryption setup failed: {e}")
            self.fernet = None

    def _compile_pii_patterns(self) -> None:
        """Compile regular expressions for PII detection"""
        self.pii_patterns = {
            PIIType.SSN: [
                (r'\b\d{3}-\d{2}-\d{4}\b', 0.9),  # XXX-XX-XXXX
                (r'\b\d{3}\s\d{2}\s\d{4}\b', 0.8),  # XXX XX XXXX
                (r'\b\d{9}\b', 0.6),  # XXXXXXXXX
            ],
            PIIType.EMAIL: [
                (r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', 0.95),
            ],
            PIIType.PHONE: [
                (r'\b\(\d{3}\)\s?\d{3}-\d{4}\b', 0.9),  # (XXX) XXX-XXXX
                (r'\b\d{3}-\d{3}-\d{4}\b', 0.85),  # XXX-XXX-XXXX
                (r'\b\d{10}\b', 0.6),  # XXXXXXXXXX
            ],
            PIIType.CREDIT_CARD: [
                (r'\b4[0-9]{12}(?:[0-9]{3})?\b', 0.9),  # Visa
                (r'\b5[1-5][0-9]{14}\b', 0.9),  # MasterCard
                (r'\b3[47][0-9]{13}\b', 0.9),  # American Express
            ],
            PIIType.STUDENT_ID: [
                (r'\bstudent\s?id[\s:]*([A-Z0-9]{6,12})\b', 0.8),
                (r'\bstudent\s?number[\s:]*([A-Z0-9]{6,12})\b', 0.8),
            ],
            PIIType.DOB: [
                (r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b', 0.7),
                (r'\b\d{4}[/-]\d{1,2}[/-]\d{1,2}\b', 0.7),
            ]
        }

    async def _extract_text_content(self, file_data: bytes, filename: str) -> str:
        """Extract text content from file for analysis"""
        try:
            # Try to decode as text first
            for encoding in ['utf-8', 'latin1', 'cp1252']:
                try:
                    return file_data.decode(encoding)
                except UnicodeDecodeError:
                    continue

            # For binary files, try to extract text based on type
            file_ext = filename.lower().split('.')[-1] if '.' in filename else ''

            if file_ext == 'pdf':
                return await self._extract_pdf_text(file_data)
            elif file_ext in ['doc', 'docx']:
                return await self._extract_doc_text(file_data)
            elif file_ext in ['jpg', 'jpeg', 'png']:
                return await self._extract_image_text(file_data)

            return ""

        except Exception as e:
            logger.debug(f"Text extraction failed: {e}")
            return ""

    async def _extract_pdf_text(self, file_data: bytes) -> str:
        """Extract text from PDF file"""
        # Would use PyPDF2 or similar library
        return ""

    async def _extract_doc_text(self, file_data: bytes) -> str:
        """Extract text from Word document"""
        # Would use python-docx or similar library
        return ""

    async def _extract_image_text(self, file_data: bytes) -> str:
        """Extract text from image using OCR"""
        # Would use pytesseract or similar OCR library
        return ""

    async def _calculate_pii_risk_level(self, pii_result: PIIDetectionResult) -> SecurityRisk:
        """Calculate overall risk level based on PII types found"""
        high_risk_types = {PIIType.SSN, PIIType.CREDIT_CARD, PIIType.MEDICAL}
        medium_risk_types = {PIIType.DOB, PIIType.PHONE, PIIType.ADDRESS, PIIType.STUDENT_ID}

        if any(pii_type in high_risk_types for pii_type in pii_result.pii_types):
            return SecurityRisk.HIGH

        if any(pii_type in medium_risk_types for pii_type in pii_result.pii_types):
            return SecurityRisk.MEDIUM

        if pii_result.pii_types:
            return SecurityRisk.LOW

        return SecurityRisk.LOW

    async def _generate_pii_recommendations(self, pii_result: PIIDetectionResult) -> List[str]:
        """Generate recommendations based on PII detection"""
        recommendations = []

        if PIIType.SSN in pii_result.pii_types:
            recommendations.append("Consider removing or redacting Social Security Numbers")

        if PIIType.CREDIT_CARD in pii_result.pii_types:
            recommendations.append("Credit card numbers detected - ensure PCI compliance")

        if PIIType.EMAIL in pii_result.pii_types:
            recommendations.append("Email addresses found - verify consent for data collection")

        if pii_result.risk_level in [SecurityRisk.HIGH, SecurityRisk.CRITICAL]:
            recommendations.append("High-risk PII detected - encryption strongly recommended")

        return recommendations

    async def _check_coppa_compliance(
        self,
        compliance: ComplianceCheck,
        options: UploadOptions,
        context: Optional[Dict[str, Any]]
    ) -> None:
        """Check COPPA compliance requirements"""
        if compliance.required_level == ComplianceLevel.COPPA:
            # Check for parental consent
            if options.require_consent and not context.get("parental_consent"):
                compliance.issues.append("COPPA: Parental consent required for children under 13")

            # Check for age verification
            student_age = context.get("student_age") if context else None
            if student_age and student_age < 13:
                compliance.requirements.append("COPPA compliance required for students under 13")
                compliance.encryption_required = True

    async def _check_ferpa_compliance(
        self,
        compliance: ComplianceCheck,
        options: UploadOptions,
        context: Optional[Dict[str, Any]]
    ) -> None:
        """Check FERPA compliance requirements"""
        if compliance.required_level == ComplianceLevel.FERPA:
            compliance.requirements.append("FERPA compliance required for educational records")
            compliance.encryption_required = True
            compliance.retention_required = True

            # Check for directory information opt-out
            if context.get("directory_opt_out"):
                compliance.issues.append("FERPA: Student opted out of directory information")

    async def _check_general_privacy_compliance(
        self,
        compliance: ComplianceCheck,
        pii_result: PIIDetectionResult
    ) -> None:
        """Check general privacy compliance requirements"""
        if pii_result.has_pii:
            if pii_result.risk_level in [SecurityRisk.HIGH, SecurityRisk.CRITICAL]:
                compliance.encryption_required = True
                compliance.requirements.append("Encryption required for high-risk PII")

    async def _generate_security_recommendations(
        self,
        compliance: ComplianceCheck,
        pii_result: PIIDetectionResult
    ) -> None:
        """Generate security recommendations"""
        if compliance.encryption_required:
            compliance.recommendations.append("Enable encryption for this file")

        if compliance.retention_required:
            compliance.recommendations.append("Set appropriate retention policy")

        if pii_result.has_pii:
            compliance.recommendations.append("Consider data minimization practices")

    def _generate_salt(self, organization_id: str) -> bytes:
        """Generate organization-specific salt"""
        return hashlib.sha256(f"toolbox_ai_{organization_id}".encode()).digest()[:16]

    def _get_key_id(self) -> str:
        """Get encryption key identifier"""
        return "toolbox_ai_main_key_v1"

    async def _get_file_metadata(self, file_id: UUID) -> Optional[Dict[str, Any]]:
        """Get file metadata from database"""
        # Would query your File model
        return {
            "id": str(file_id),
            "organization_id": "test_org",
            "category": "student_submission",
            "requires_consent": False
        }

    async def _check_user_permissions(
        self,
        user_id: str,
        file_metadata: Dict[str, Any],
        action: str
    ) -> bool:
        """Check user permissions for file action"""
        # Would check user roles and permissions
        return True

    async def _check_file_access_rules(
        self,
        file_id: UUID,
        user_id: str,
        action: str,
        context: Optional[Dict[str, Any]]
    ) -> bool:
        """Check file-specific access rules"""
        # Would check custom access rules
        return True

    async def _check_compliance_access(
        self,
        file_metadata: Dict[str, Any],
        user_id: str,
        action: str,
        context: Optional[Dict[str, Any]]
    ) -> List[str]:
        """Check compliance-based access restrictions"""
        violations = []

        # Check FERPA educational interest
        if file_metadata.get("category") == "educational_record":
            if not context.get("legitimate_educational_interest"):
                violations.append("FERPA: No legitimate educational interest demonstrated")

        return violations

    async def _store_audit_event(self, event_record: Dict[str, Any]) -> None:
        """Store audit event in logging system"""
        # Would store in audit log database or external SIEM
        logger.info(f"Audit event: {event_record['event_type']}")