"""
Storage Service Module for ToolBoxAI Educational Platform

Comprehensive file storage system with multi-tenant isolation, security,
and compliance features for educational content management.

Features:
- Supabase Storage integration
- Multi-tenant file isolation
- Advanced security scanning
- Image processing and optimization
- COPPA/FERPA compliance
- CDN integration
- Quota management

Author: ToolBoxAI Team
Created: 2025-01-27
Version: 1.0.0
"""

from .storage_service import StorageService, UploadProgress, UploadResult
from .supabase_provider import SupabaseStorageProvider
from .file_validator import FileValidator, ValidationResult
from .virus_scanner import VirusScanner, ScanResult
from .image_processor import ImageProcessor, ImageVariant
from .tenant_storage import TenantStorageManager
from .security import SecurityManager, ComplianceCheck
from .cdn import CDNManager

__all__ = [
    "StorageService",
    "SupabaseStorageProvider",
    "FileValidator",
    "VirusScanner",
    "ImageProcessor",
    "TenantStorageManager",
    "SecurityManager",
    "CDNManager",
    "UploadProgress",
    "UploadResult",
    "ValidationResult",
    "ScanResult",
    "ImageVariant",
    "ComplianceCheck",
]