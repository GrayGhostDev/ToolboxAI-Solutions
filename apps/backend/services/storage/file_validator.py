"""
File Validator for ToolBoxAI Educational Platform

Comprehensive file validation including MIME type checking, file size limits,
content validation, filename sanitization, and security checks.

Author: ToolBoxAI Team
Created: 2025-01-27
Version: 1.0.0
"""

import logging
import mimetypes
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import magic

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Result of file validation"""

    is_valid: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    detected_mime_type: str | None = None
    file_category: str | None = None
    sanitized_filename: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "is_valid": self.is_valid,
            "errors": self.errors,
            "warnings": self.warnings,
            "detected_mime_type": self.detected_mime_type,
            "file_category": self.file_category,
            "sanitized_filename": self.sanitized_filename,
            "metadata": self.metadata,
        }


class FileValidator:
    """
    Comprehensive file validation with educational platform-specific rules.

    Features:
    - MIME type detection using python-magic
    - File size validation per category
    - Content validation using magic bytes
    - Filename sanitization and security
    - Extension validation
    - Educational content-specific rules
    """

    def __init__(self):
        """Initialize file validator with configuration"""

        # MIME type categories for educational content
        self.mime_type_categories = {
            "educational_content": {
                "application/pdf",
                "application/msword",
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                "application/vnd.ms-powerpoint",
                "application/vnd.openxmlformats-officedocument.presentationml.presentation",
                "text/plain",
                "text/html",
                "text/markdown",
                "application/json",
                "text/csv",
            },
            "student_submission": {
                "application/pdf",
                "application/msword",
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                "text/plain",
                "image/jpeg",
                "image/png",
                "image/gif",
                "application/zip",
                "text/csv",
            },
            "assessment": {
                "application/pdf",
                "application/json",
                "text/csv",
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                "text/plain",
            },
            "media_resource": {
                "image/jpeg",
                "image/png",
                "image/gif",
                "image/webp",
                "image/svg+xml",
                "video/mp4",
                "video/webm",
                "video/quicktime",
                "audio/mpeg",
                "audio/wav",
                "audio/ogg",
                "application/pdf",
            },
            "avatar": {"image/jpeg", "image/png", "image/gif", "image/webp"},
            "administrative": {
                "application/pdf",
                "application/msword",
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                "application/vnd.ms-excel",
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                "text/csv",
                "text/plain",
            },
            "temporary": {"*"},  # Allow all types for temporary files
            "report": {
                "application/pdf",
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                "text/csv",
                "application/json",
            },
        }

        # File size limits by category (in MB)
        self.size_limits = {
            "educational_content": 100,
            "student_submission": 50,
            "assessment": 25,
            "media_resource": 500,
            "avatar": 10,
            "administrative": 100,
            "temporary": 1000,
            "report": 50,
        }

        # Dangerous file extensions
        self.dangerous_extensions = {
            ".exe",
            ".bat",
            ".cmd",
            ".com",
            ".pif",
            ".scr",
            ".vbs",
            ".js",
            ".jar",
            ".app",
            ".deb",
            ".pkg",
            ".dmg",
            ".sh",
            ".bash",
            ".ps1",
            ".msi",
            ".dll",
            ".so",
            ".dylib",
            ".php",
            ".asp",
            ".jsp",
        }

        # Safe filename pattern
        self.safe_filename_pattern = re.compile(r"^[a-zA-Z0-9._\-\s()]+$")

        # Maximum filename length
        self.max_filename_length = 255

        logger.info("FileValidator initialized with educational platform rules")

    async def validate_file(
        self,
        file_data: bytes | str,
        filename: str,
        file_category: str = "media_resource",
        additional_checks: dict[str, Any] | None = None,
    ) -> ValidationResult:
        """
        Validate a file comprehensively.

        Args:
            file_data: File content as bytes or file path
            filename: Original filename
            file_category: File category for validation rules
            additional_checks: Additional validation parameters

        Returns:
            ValidationResult: Comprehensive validation result
        """
        result = ValidationResult(is_valid=True, file_category=file_category)
        additional_checks = additional_checks or {}

        try:
            # Get file data if path provided
            if isinstance(file_data, str):
                with open(file_data, "rb") as f:
                    file_data = f.read()

            # Basic checks
            await self._validate_filename(filename, result)
            await self._validate_file_size(file_data, file_category, result)

            # MIME type validation
            await self._validate_mime_type(file_data, filename, file_category, result)

            # Content validation
            await self._validate_content(file_data, filename, result)

            # Security checks
            await self._validate_security(file_data, filename, result)

            # Educational platform-specific checks
            await self._validate_educational_rules(
                file_data, filename, file_category, result, additional_checks
            )

            # Generate sanitized filename
            result.sanitized_filename = self._sanitize_filename(filename)

            # Final validation status
            result.is_valid = len(result.errors) == 0

            logger.debug(
                f"File validation completed: {filename} -> "
                f"{'VALID' if result.is_valid else 'INVALID'}"
            )

            return result

        except Exception as e:
            logger.error(f"File validation failed: {e}")
            result.is_valid = False
            result.errors.append(f"Validation error: {str(e)}")
            return result

    async def _validate_filename(self, filename: str, result: ValidationResult) -> None:
        """Validate filename safety and format"""
        if not filename:
            result.errors.append("Filename cannot be empty")
            return

        # Length check
        if len(filename) > self.max_filename_length:
            result.errors.append(
                f"Filename too long: {len(filename)} characters "
                f"(maximum: {self.max_filename_length})"
            )

        # Extension check
        file_ext = Path(filename).suffix.lower()
        if file_ext in self.dangerous_extensions:
            result.errors.append(f"Dangerous file extension: {file_ext}")

        # Character safety check
        if not self.safe_filename_pattern.match(filename):
            result.warnings.append("Filename contains unsafe characters and will be sanitized")

        # Hidden file check
        if filename.startswith("."):
            result.warnings.append("Hidden file detected")

        # Multiple extensions check
        if filename.count(".") > 2:
            result.warnings.append("Multiple file extensions detected")

    async def _validate_file_size(
        self, file_data: bytes, file_category: str, result: ValidationResult
    ) -> None:
        """Validate file size against category limits"""
        file_size_mb = len(file_data) / (1024 * 1024)
        max_size_mb = self.size_limits.get(file_category, 100)

        if file_size_mb > max_size_mb:
            result.errors.append(
                f"File too large: {file_size_mb:.2f}MB "
                f"(maximum for {file_category}: {max_size_mb}MB)"
            )

        # Empty file check
        if len(file_data) == 0:
            result.errors.append("File is empty")

        result.metadata["file_size_bytes"] = len(file_data)
        result.metadata["file_size_mb"] = file_size_mb

    async def _validate_mime_type(
        self, file_data: bytes, filename: str, file_category: str, result: ValidationResult
    ) -> None:
        """Validate MIME type using magic bytes and filename"""
        try:
            # Detect MIME type using magic
            detected_mime = magic.from_buffer(file_data, mime=True)
            result.detected_mime_type = detected_mime

            # Get MIME type from filename
            filename_mime, _ = mimetypes.guess_type(filename)

            # Check against allowed types for category
            allowed_types = self.mime_type_categories.get(file_category, set())

            if "*" not in allowed_types and detected_mime not in allowed_types:
                result.errors.append(f"MIME type not allowed for {file_category}: {detected_mime}")

            # Check for MIME type mismatch
            if filename_mime and filename_mime != detected_mime:
                result.warnings.append(
                    f"MIME type mismatch: extension suggests {filename_mime}, "
                    f"content is {detected_mime}"
                )

            result.metadata["detected_mime_type"] = detected_mime
            result.metadata["filename_mime_type"] = filename_mime

        except Exception as e:
            logger.warning(f"MIME type detection failed: {e}")
            result.warnings.append("Could not detect MIME type")

    async def _validate_content(
        self, file_data: bytes, filename: str, result: ValidationResult
    ) -> None:
        """Validate file content and structure"""
        try:
            # Magic number validation
            if not self._validate_magic_numbers(file_data, result):
                result.errors.append("Invalid file header/magic numbers")

            # Text encoding validation for text files
            if self._is_text_file(filename):
                if not self._validate_text_encoding(file_data, result):
                    result.warnings.append("Text encoding issues detected")

            # Image validation
            if self._is_image_file(filename):
                await self._validate_image_content(file_data, result)

            # Document validation
            if self._is_document_file(filename):
                await self._validate_document_content(file_data, result)

        except Exception as e:
            logger.warning(f"Content validation failed: {e}")
            result.warnings.append(f"Content validation error: {str(e)}")

    async def _validate_security(
        self, file_data: bytes, filename: str, result: ValidationResult
    ) -> None:
        """Security-focused validation"""
        # Check for embedded executables
        if self._contains_executable_content(file_data):
            result.errors.append("File contains executable content")

        # Check for suspicious patterns
        suspicious_patterns = [
            b"<script",
            b"javascript:",
            b"vbscript:",
            b"onload=",
            b"onerror=",
            b"eval(",
            b"exec(",
        ]

        for pattern in suspicious_patterns:
            if pattern in file_data.lower():
                result.warnings.append(
                    f"Suspicious pattern detected: {pattern.decode('utf-8', errors='ignore')}"
                )

        # Check file size vs content ratio for zip bombs
        if self._is_archive_file(filename):
            await self._check_compression_ratio(file_data, result)

    async def _validate_educational_rules(
        self,
        file_data: bytes,
        filename: str,
        file_category: str,
        result: ValidationResult,
        additional_checks: dict[str, Any],
    ) -> None:
        """Educational platform-specific validation rules"""

        # COPPA compliance for student submissions
        if file_category == "student_submission":
            if additional_checks.get("student_age") and additional_checks["student_age"] < 13:
                result.warnings.append("COPPA compliance required for students under 13")

        # Assessment file validation
        if file_category == "assessment":
            if self._is_document_file(filename) and len(file_data) < 100:
                result.warnings.append("Assessment file appears to be very small")

        # Avatar image validation
        if file_category == "avatar":
            if not self._is_image_file(filename):
                result.errors.append("Avatar must be an image file")
            else:
                await self._validate_avatar_image(file_data, result)

        # Administrative document checks
        if file_category == "administrative":
            if additional_checks.get("require_signature") and not self._has_digital_signature(
                file_data
            ):
                result.warnings.append("Administrative document may require digital signature")

    def _validate_magic_numbers(self, file_data: bytes, result: ValidationResult) -> bool:
        """Validate file magic numbers/headers"""
        if len(file_data) < 4:
            return False

        # Common file signatures
        signatures = {
            b"\x89PNG": "image/png",
            b"\xff\xd8\xff": "image/jpeg",
            b"GIF8": "image/gif",
            b"%PDF": "application/pdf",
            b"PK\x03\x04": "application/zip",
            b"\xd0\xcf\x11\xe0": "application/msword",
            b"RIFF": "video/avi",
        }

        header = file_data[:8]
        for sig, mime_type in signatures.items():
            if header.startswith(sig):
                result.metadata["detected_signature"] = mime_type
                return True

        # If no known signature found, might still be valid
        return True

    def _validate_text_encoding(self, file_data: bytes, result: ValidationResult) -> bool:
        """Validate text file encoding"""
        try:
            # Try common encodings
            for encoding in ["utf-8", "latin1", "cp1252"]:
                try:
                    file_data.decode(encoding)
                    result.metadata["text_encoding"] = encoding
                    return True
                except UnicodeDecodeError:
                    continue

            return False

        except Exception:
            return False

    async def _validate_image_content(self, file_data: bytes, result: ValidationResult) -> None:
        """Validate image file content"""
        try:
            import io

            from PIL import Image

            # Try to open and validate image
            with Image.open(io.BytesIO(file_data)) as img:
                result.metadata["image_format"] = img.format
                result.metadata["image_size"] = img.size
                result.metadata["image_mode"] = img.mode

                # Check for reasonable dimensions
                width, height = img.size
                if width > 10000 or height > 10000:
                    result.warnings.append("Image dimensions are very large")

                if width < 10 or height < 10:
                    result.warnings.append("Image dimensions are very small")

        except Exception as e:
            result.errors.append(f"Invalid image file: {str(e)}")

    async def _validate_document_content(self, file_data: bytes, result: ValidationResult) -> None:
        """Validate document file content"""
        # Basic document validation
        if file_data.startswith(b"%PDF"):
            await self._validate_pdf_content(file_data, result)
        elif b"Microsoft Office" in file_data or b"word/" in file_data:
            await self._validate_office_content(file_data, result)

    async def _validate_pdf_content(self, file_data: bytes, result: ValidationResult) -> None:
        """Validate PDF file content"""
        try:
            # Check for PDF structure
            if b"%%EOF" not in file_data:
                result.warnings.append("PDF file may be corrupted")

            # Check for JavaScript (security concern)
            if b"/JavaScript" in file_data or b"/JS" in file_data:
                result.warnings.append("PDF contains JavaScript")

            # Check for forms
            if b"/AcroForm" in file_data:
                result.metadata["has_forms"] = True

        except Exception as e:
            result.warnings.append(f"PDF validation warning: {str(e)}")

    async def _validate_office_content(self, file_data: bytes, result: ValidationResult) -> None:
        """Validate Microsoft Office document content"""
        try:
            # Check for macros (security concern)
            if b"vba" in file_data.lower() or b"macro" in file_data.lower():
                result.warnings.append("Document may contain macros")

            # Check for external links
            if b"http://" in file_data or b"https://" in file_data:
                result.warnings.append("Document contains external links")

        except Exception as e:
            result.warnings.append(f"Office document validation warning: {str(e)}")

    async def _validate_avatar_image(self, file_data: bytes, result: ValidationResult) -> None:
        """Validate avatar image requirements"""
        try:
            import io

            from PIL import Image

            with Image.open(io.BytesIO(file_data)) as img:
                width, height = img.size

                # Avatar size requirements
                if width < 32 or height < 32:
                    result.errors.append("Avatar image too small (minimum 32x32)")

                if width > 1024 or height > 1024:
                    result.warnings.append("Avatar image very large (consider resizing)")

                # Aspect ratio check
                ratio = width / height
                if ratio < 0.5 or ratio > 2.0:
                    result.warnings.append("Avatar has unusual aspect ratio")

        except Exception as e:
            result.errors.append(f"Avatar validation failed: {str(e)}")

    def _contains_executable_content(self, file_data: bytes) -> bool:
        """Check for embedded executable content"""
        # Check for PE headers (Windows executables)
        if b"MZ" in file_data[:100] and b"PE\x00\x00" in file_data:
            return True

        # Check for ELF headers (Linux executables)
        if file_data.startswith(b"\x7fELF"):
            return True

        # Check for Mach-O headers (macOS executables)
        if file_data.startswith(b"\xfe\xed\xfa\xce") or file_data.startswith(b"\xce\xfa\xed\xfe"):
            return True

        return False

    async def _check_compression_ratio(self, file_data: bytes, result: ValidationResult) -> None:
        """Check compression ratio to detect zip bombs"""
        try:
            import io
            import zipfile

            if file_data.startswith(b"PK"):  # ZIP file
                with zipfile.ZipFile(io.BytesIO(file_data), "r") as zf:
                    compressed_size = len(file_data)
                    uncompressed_size = sum(info.file_size for info in zf.infolist())

                    if uncompressed_size > 0:
                        ratio = uncompressed_size / compressed_size
                        if ratio > 100:  # 100:1 ratio threshold
                            result.warnings.append(
                                f"High compression ratio detected: {ratio:.1f}:1"
                            )

        except Exception:
            # If we can't check, it's not necessarily an error
            pass

    def _is_text_file(self, filename: str) -> bool:
        """Check if file is a text file"""
        text_extensions = {".txt", ".md", ".csv", ".json", ".xml", ".html", ".css", ".js"}
        return Path(filename).suffix.lower() in text_extensions

    def _is_image_file(self, filename: str) -> bool:
        """Check if file is an image"""
        image_extensions = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg", ".bmp", ".tiff"}
        return Path(filename).suffix.lower() in image_extensions

    def _is_document_file(self, filename: str) -> bool:
        """Check if file is a document"""
        doc_extensions = {".pdf", ".doc", ".docx", ".ppt", ".pptx", ".xls", ".xlsx"}
        return Path(filename).suffix.lower() in doc_extensions

    def _is_archive_file(self, filename: str) -> bool:
        """Check if file is an archive"""
        archive_extensions = {".zip", ".rar", ".7z", ".tar", ".gz", ".bz2"}
        return Path(filename).suffix.lower() in archive_extensions

    def _has_digital_signature(self, file_data: bytes) -> bool:
        """Check if document has digital signature"""
        # Simple check for signature indicators in PDF
        if b"/Sig" in file_data or b"/signature" in file_data.lower():
            return True

        # Check for Office document signatures
        if b"signature" in file_data.lower() or b"cert" in file_data.lower():
            return True

        return False

    def _sanitize_filename(self, filename: str) -> str:
        """Sanitize filename for safe storage"""
        # Get base name and extension
        path = Path(filename)
        stem = path.stem
        suffix = path.suffix.lower()

        # Remove or replace unsafe characters
        safe_stem = re.sub(r"[^\w\-_\.]", "_", stem)

        # Remove multiple underscores
        safe_stem = re.sub(r"_+", "_", safe_stem)

        # Remove leading/trailing underscores
        safe_stem = safe_stem.strip("_")

        # Ensure not empty
        if not safe_stem:
            safe_stem = "file"

        # Truncate if too long
        max_stem_length = 200 - len(suffix)
        if len(safe_stem) > max_stem_length:
            safe_stem = safe_stem[:max_stem_length]

        return safe_stem + suffix

    def get_mime_type(self, filename: str) -> str:
        """Get MIME type from filename"""
        mime_type, _ = mimetypes.guess_type(filename)
        return mime_type or "application/octet-stream"

    def get_allowed_extensions(self, file_category: str) -> set[str]:
        """Get allowed file extensions for a category"""
        allowed_types = self.mime_type_categories.get(file_category, set())
        extensions = set()

        for mime_type in allowed_types:
            if mime_type == "*":
                return {"*"}

            # Get common extensions for this MIME type
            common_exts = mimetypes.guess_all_extensions(mime_type)
            extensions.update(common_exts)

        return extensions

    def is_extension_allowed(self, filename: str, file_category: str) -> bool:
        """Check if file extension is allowed for category"""
        allowed_extensions = self.get_allowed_extensions(file_category)

        if "*" in allowed_extensions:
            return True

        file_ext = Path(filename).suffix.lower()
        return file_ext in allowed_extensions
