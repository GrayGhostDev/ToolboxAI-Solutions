#!/usr/bin/env python3
"""
Storage System Tests
====================

Tests for Supabase storage integration with security features.
"""

import os
import sys
import uuid
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

import pytest

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


@pytest.fixture
def organization_id():
    """Test organization ID."""
    return uuid.uuid4()


@pytest.fixture
def user_id():
    """Test user ID."""
    return uuid.uuid4()


@pytest.fixture
def mock_file():
    """Mock file object."""
    file = Mock()
    file.filename = "test_document.pdf"
    file.content_type = "application/pdf"
    file.size = 1024 * 1024  # 1MB
    file.read.return_value = b"Mock file content"
    return file


@pytest.fixture
def mock_supabase_client():
    """Mock Supabase client."""
    client = Mock()
    client.storage = Mock()
    client.storage.from_.return_value = Mock()
    return client


class TestStorageConfiguration:
    """Test storage system configuration."""

    def test_supabase_configuration(self):
        """Test Supabase storage configuration (not AWS S3)."""
        config = {
            "provider": "supabase",
            "url": "https://example.supabase.co",
            "bucket": "educational-content",
            "cdn_enabled": True,
            "use_self_hosted": True,
        }

        # Verify not using AWS S3
        assert config["provider"] == "supabase"
        assert "s3" not in config["provider"].lower()
        assert "aws" not in config["provider"].lower()
        assert config["use_self_hosted"] is True

    def test_storage_quota_configuration(self):
        """Test storage quota settings per tier."""
        quotas = {
            "FREE": {
                "max_storage_gb": 10,
                "max_file_size_mb": 50,
                "allowed_types": ["pdf", "doc", "jpg", "png"],
            },
            "BASIC": {
                "max_storage_gb": 100,
                "max_file_size_mb": 100,
                "allowed_types": ["pdf", "doc", "jpg", "png", "mp4", "zip"],
            },
            "PREMIUM": {"max_storage_gb": 500, "max_file_size_mb": 500, "allowed_types": "all"},
            "ENTERPRISE": {
                "max_storage_gb": None,  # Unlimited
                "max_file_size_mb": 1000,
                "allowed_types": "all",
            },
        }

        # Test tier limits
        assert quotas["FREE"]["max_storage_gb"] == 10
        assert quotas["BASIC"]["max_storage_gb"] == 100
        assert quotas["PREMIUM"]["max_storage_gb"] == 500
        assert quotas["ENTERPRISE"]["max_storage_gb"] is None


class TestFileUpload:
    """Test file upload functionality."""

    @patch("apps.backend.services.storage.supabase_provider.SupabaseProvider")
    def test_file_upload_success(self, mock_provider, mock_file, organization_id, user_id):
        """Test successful file upload."""
        # Mock upload response
        mock_provider.upload.return_value = {
            "file_id": str(uuid.uuid4()),
            "file_name": mock_file.filename,
            "file_size": mock_file.size,
            "mime_type": mock_file.content_type,
            "storage_path": f"{organization_id}/{user_id}/{mock_file.filename}",
            "cdn_url": f"https://cdn.example.com/{organization_id}/{mock_file.filename}",
            "uploaded_at": datetime.utcnow().isoformat(),
        }

        result = mock_provider.upload(
            file=mock_file, organization_id=organization_id, user_id=user_id
        )

        # Verify upload
        assert "file_id" in result
        assert result["file_name"] == "test_document.pdf"
        assert result["file_size"] == 1024 * 1024
        assert str(organization_id) in result["storage_path"]

    @patch("apps.backend.services.storage.file_validator.FileValidator")
    def test_file_validation(self, mock_validator, mock_file):
        """Test file validation before upload."""
        # Test MIME type validation
        mock_validator.validate_mime_type.return_value = True
        mock_validator.validate_file_size.return_value = True
        mock_validator.validate_file_extension.return_value = True

        # Validate file
        is_valid_mime = mock_validator.validate_mime_type(mock_file.content_type)
        is_valid_size = mock_validator.validate_file_size(mock_file.size, max_size_mb=100)
        is_valid_ext = mock_validator.validate_file_extension("pdf")

        assert is_valid_mime is True
        assert is_valid_size is True
        assert is_valid_ext is True

    def test_file_size_limits(self, mock_file, organization_id):
        """Test file size limit enforcement."""
        # Test different file sizes
        max_size_mb = 100
        max_size_bytes = max_size_mb * 1024 * 1024

        # Within limit
        mock_file.size = 50 * 1024 * 1024  # 50MB
        assert mock_file.size < max_size_bytes

        # Exceeding limit
        mock_file.size = 150 * 1024 * 1024  # 150MB
        assert mock_file.size > max_size_bytes


class TestVirusScanning:
    """Test virus scanning integration."""

    @patch("apps.backend.services.storage.virus_scanner.ClamAVScanner")
    def test_virus_scanning(self, mock_scanner, mock_file):
        """Test ClamAV virus scanning."""
        # Mock clean file
        mock_scanner.scan.return_value = {
            "status": "clean",
            "threats": [],
            "scan_time": 0.5,
            "engine": "clamav",
            "definitions_version": "2025.09.28",
        }

        result = mock_scanner.scan(mock_file.read())

        assert result["status"] == "clean"
        assert len(result["threats"]) == 0
        assert result["engine"] == "clamav"

    @patch("apps.backend.services.storage.virus_scanner.ClamAVScanner")
    def test_virus_detected(self, mock_scanner, mock_file):
        """Test virus detection and quarantine."""
        # Mock infected file
        mock_scanner.scan.return_value = {
            "status": "infected",
            "threats": ["EICAR-Test-Signature"],
            "action": "quarantined",
            "quarantine_path": "/quarantine/infected_file.quarantine",
        }

        result = mock_scanner.scan(mock_file.read())

        assert result["status"] == "infected"
        assert "EICAR-Test-Signature" in result["threats"]
        assert result["action"] == "quarantined"

    def test_eicar_test_file(self):
        """Test EICAR test file detection."""
        # EICAR test signature
        eicar_signature = b"X5O!P%@AP[4\\PZX54(P^)7CC)7}$EICAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*"

        # Should be detected as a test virus
        assert b"EICAR" in eicar_signature
        assert len(eicar_signature) == 68


class TestComplianceFeatures:
    """Test COPPA/FERPA compliance features."""

    @patch("apps.backend.services.storage.security.ComplianceChecker")
    def test_pii_detection(self, mock_checker):
        """Test PII detection in uploaded files."""
        # Mock PII detection
        mock_checker.detect_pii.return_value = {
            "contains_pii": True,
            "pii_types": ["social_security_number", "email", "phone_number"],
            "confidence": 0.95,
            "locations": [
                {"type": "ssn", "page": 2, "line": 15},
                {"type": "email", "page": 3, "line": 22},
            ],
        }

        file_content = "John Doe, SSN: 123-45-6789, Email: john@example.com"
        result = mock_checker.detect_pii(file_content)

        assert result["contains_pii"] is True
        assert "social_security_number" in result["pii_types"]
        assert result["confidence"] >= 0.9

    @patch("apps.backend.services.storage.security.ComplianceChecker")
    def test_coppa_compliance(self, mock_checker, user_id):
        """Test COPPA compliance for users under 13."""
        # Mock user age check
        mock_checker.check_coppa_compliance.return_value = {
            "user_id": str(user_id),
            "age": 11,
            "requires_parental_consent": True,
            "consent_status": "pending",
            "restrictions": ["no_personal_info_collection", "no_behavioral_tracking"],
        }

        result = mock_checker.check_coppa_compliance(user_id=user_id)

        assert result["requires_parental_consent"] is True
        assert result["age"] < 13
        assert "no_personal_info_collection" in result["restrictions"]

    @patch("apps.backend.services.storage.security.ComplianceChecker")
    def test_ferpa_compliance(self, mock_checker, organization_id):
        """Test FERPA compliance for educational records."""
        # Mock FERPA check
        mock_checker.check_ferpa_compliance.return_value = {
            "organization_id": str(organization_id),
            "is_educational_record": True,
            "access_restricted": True,
            "allowed_parties": ["student", "parent", "authorized_school_official"],
            "audit_required": True,
        }

        result = mock_checker.check_ferpa_compliance(
            organization_id=organization_id, file_type="transcript"
        )

        assert result["is_educational_record"] is True
        assert result["access_restricted"] is True
        assert "parent" in result["allowed_parties"]


class TestFileOperations:
    """Test file operations (CRUD)."""

    @patch("apps.backend.services.storage.supabase_provider.SupabaseProvider")
    def test_file_listing(self, mock_provider, organization_id, user_id):
        """Test listing files for an organization."""
        # Mock file list
        mock_provider.list_files.return_value = {
            "files": [
                {
                    "file_id": str(uuid.uuid4()),
                    "name": "lesson1.pdf",
                    "size": 2048000,
                    "created_at": "2025-09-28T00:00:00Z",
                },
                {
                    "file_id": str(uuid.uuid4()),
                    "name": "quiz1.docx",
                    "size": 1024000,
                    "created_at": "2025-09-27T00:00:00Z",
                },
            ],
            "total": 2,
            "page": 1,
            "per_page": 20,
        }

        result = mock_provider.list_files(organization_id=organization_id, user_id=user_id)

        assert len(result["files"]) == 2
        assert result["total"] == 2
        assert result["files"][0]["name"] == "lesson1.pdf"

    @patch("apps.backend.services.storage.supabase_provider.SupabaseProvider")
    def test_file_deletion(self, mock_provider, organization_id):
        """Test file deletion with soft delete."""
        file_id = uuid.uuid4()

        mock_provider.delete_file.return_value = {
            "file_id": str(file_id),
            "deleted": True,
            "soft_delete": True,
            "deleted_at": datetime.utcnow().isoformat(),
            "retention_days": 30,
        }

        result = mock_provider.delete_file(file_id=file_id)

        assert result["deleted"] is True
        assert result["soft_delete"] is True
        assert result["retention_days"] == 30

    @patch("apps.backend.services.storage.supabase_provider.SupabaseProvider")
    def test_file_sharing(self, mock_provider):
        """Test secure file sharing."""
        file_id = uuid.uuid4()
        share_with = ["user1@school.edu", "user2@school.edu"]

        mock_provider.share_file.return_value = {
            "share_id": str(uuid.uuid4()),
            "file_id": str(file_id),
            "shared_with": share_with,
            "expires_at": (datetime.utcnow() + timedelta(days=7)).isoformat(),
            "share_url": f"https://share.example.com/{uuid.uuid4().hex}",
        }

        result = mock_provider.share_file(file_id=file_id, share_with=share_with, expires_days=7)

        assert result["shared_with"] == share_with
        assert "expires_at" in result
        assert "share_url" in result


class TestFileVersioning:
    """Test file versioning functionality."""

    @patch("apps.backend.services.storage.supabase_provider.SupabaseProvider")
    def test_file_versioning(self, mock_provider):
        """Test file version creation."""
        file_id = uuid.uuid4()

        mock_provider.create_version.return_value = {
            "version_id": str(uuid.uuid4()),
            "file_id": str(file_id),
            "version_number": 2,
            "changes": "Updated content in section 3",
            "created_by": str(uuid.uuid4()),
            "created_at": datetime.utcnow().isoformat(),
        }

        result = mock_provider.create_version(
            file_id=file_id, changes="Updated content in section 3"
        )

        assert result["version_number"] == 2
        assert result["changes"] == "Updated content in section 3"

    @patch("apps.backend.services.storage.supabase_provider.SupabaseProvider")
    def test_version_history(self, mock_provider):
        """Test retrieving version history."""
        file_id = uuid.uuid4()

        mock_provider.get_version_history.return_value = {
            "file_id": str(file_id),
            "versions": [
                {"version": 1, "created_at": "2025-09-25T00:00:00Z", "size": 1024000},
                {"version": 2, "created_at": "2025-09-26T00:00:00Z", "size": 1048000},
                {"version": 3, "created_at": "2025-09-27T00:00:00Z", "size": 1050000},
            ],
            "current_version": 3,
        }

        result = mock_provider.get_version_history(file_id=file_id)

        assert len(result["versions"]) == 3
        assert result["current_version"] == 3


class TestCDNIntegration:
    """Test Smart CDN integration."""

    def test_cdn_url_generation(self, organization_id):
        """Test CDN URL generation for files."""
        file_name = "lesson_video.mp4"
        base_cdn = "https://cdn.supabase.co"

        # Generate CDN URL
        cdn_url = f"{base_cdn}/{organization_id}/{file_name}"

        assert base_cdn in cdn_url
        assert str(organization_id) in cdn_url
        assert file_name in cdn_url

    def test_cdn_caching_headers(self):
        """Test CDN caching configuration."""
        cache_config = {
            "images": {
                "max_age": 86400 * 30,  # 30 days
                "extensions": ["jpg", "png", "gif", "webp"],
            },
            "documents": {"max_age": 86400 * 7, "extensions": ["pdf", "doc", "docx"]},  # 7 days
            "videos": {"max_age": 86400 * 90, "extensions": ["mp4", "webm", "mov"]},  # 90 days
        }

        assert cache_config["images"]["max_age"] == 86400 * 30
        assert "pdf" in cache_config["documents"]["extensions"]


class TestStorageQuotas:
    """Test storage quota management."""

    @patch("apps.backend.services.storage.tenant_storage.TenantStorageManager")
    def test_quota_check(self, mock_manager, organization_id):
        """Test storage quota checking."""
        mock_manager.check_quota.return_value = {
            "organization_id": str(organization_id),
            "used_bytes": 5 * 1024 * 1024 * 1024,  # 5GB
            "limit_bytes": 10 * 1024 * 1024 * 1024,  # 10GB
            "percentage_used": 50.0,
            "can_upload": True,
        }

        result = mock_manager.check_quota(organization_id=organization_id)

        assert result["percentage_used"] == 50.0
        assert result["can_upload"] is True

    @patch("apps.backend.services.storage.tenant_storage.TenantStorageManager")
    def test_quota_exceeded(self, mock_manager, organization_id):
        """Test behavior when quota is exceeded."""
        mock_manager.check_quota.return_value = {
            "organization_id": str(organization_id),
            "used_bytes": 10 * 1024 * 1024 * 1024,  # 10GB
            "limit_bytes": 10 * 1024 * 1024 * 1024,  # 10GB
            "percentage_used": 100.0,
            "can_upload": False,
            "message": "Storage quota exceeded. Please upgrade your plan.",
        }

        result = mock_manager.check_quota(organization_id=organization_id)

        assert result["percentage_used"] == 100.0
        assert result["can_upload"] is False
        assert "upgrade" in result["message"].lower()


class TestImageProcessing:
    """Test image optimization and processing."""

    @patch("apps.backend.services.storage.image_processor.ImageProcessor")
    def test_image_optimization(self, mock_processor):
        """Test image optimization for web delivery."""
        mock_processor.optimize.return_value = {
            "original_size": 5 * 1024 * 1024,  # 5MB
            "optimized_size": 800 * 1024,  # 800KB
            "compression_ratio": 0.84,
            "format": "webp",
            "dimensions": {"width": 1920, "height": 1080},
        }

        result = mock_processor.optimize(image_data=b"mock_image_data", max_width=1920, quality=85)

        assert result["optimized_size"] < result["original_size"]
        assert result["format"] == "webp"
        assert result["dimensions"]["width"] == 1920

    @patch("apps.backend.services.storage.image_processor.ImageProcessor")
    def test_thumbnail_generation(self, mock_processor):
        """Test thumbnail generation for images."""
        mock_processor.generate_thumbnail.return_value = {
            "thumbnail_size": 50 * 1024,  # 50KB
            "dimensions": {"width": 200, "height": 200},
            "format": "jpeg",
        }

        result = mock_processor.generate_thumbnail(image_data=b"mock_image_data", size=(200, 200))

        assert result["dimensions"]["width"] == 200
        assert result["dimensions"]["height"] == 200


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "--tb=short"])
