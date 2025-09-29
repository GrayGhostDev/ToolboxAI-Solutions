"""
Example Usage of ToolBoxAI Storage Service

Demonstrates how to use the comprehensive storage service with all features
including uploads, virus scanning, image processing, and compliance checking.

Author: ToolBoxAI Team
Created: 2025-01-27
Version: 1.0.0
"""

import asyncio
import logging
from pathlib import Path
from typing import Dict, Any

from .supabase_provider import SupabaseStorageProvider
from .storage_service import UploadOptions, DownloadOptions, ListOptions, DownloadPermission
from .file_validator import ValidationResult
from .virus_scanner import ScanResult, ScanConfiguration
from .image_processor import ImageProcessor, ProcessingOptions
from .tenant_storage import TenantStorageManager
from .security import SecurityManager, ComplianceLevel
from .cdn import CDNManager, CDNConfiguration, ImageTransformation, CacheLevel

logger = logging.getLogger(__name__)


async def basic_file_upload_example():
    """Basic file upload example"""
    print("\n=== Basic File Upload Example ===")

    # Initialize storage provider
    storage = SupabaseStorageProvider(
        organization_id="org_123",
        user_id="user_456"
    )

    # Prepare file data
    file_data = b"Hello, this is a test file for ToolBoxAI!"
    filename = "test_document.txt"

    # Configure upload options
    options = UploadOptions(
        file_category="educational_content",
        title="Test Document",
        description="A simple test document for demonstration",
        tags=["test", "demo", "educational"],
        virus_scan=True,
        content_validation=True,
        generate_thumbnails=False,  # Not applicable for text files
        optimize_images=False
    )

    try:
        # Upload the file
        result = await storage.upload_file(file_data, filename, options)

        print(f"✅ Upload successful!")
        print(f"   File ID: {result.file_id}")
        print(f"   Storage Path: {result.storage_path}")
        print(f"   File Size: {result.file_size} bytes")
        print(f"   MIME Type: {result.mime_type}")
        print(f"   Checksum: {result.checksum}")
        print(f"   Status: {result.status}")

        if result.warnings:
            print(f"   Warnings: {result.warnings}")

        return result.file_id

    except Exception as e:
        print(f"❌ Upload failed: {e}")
        return None


async def image_upload_with_processing_example():
    """Image upload with processing example"""
    print("\n=== Image Upload with Processing Example ===")

    # Initialize storage provider
    storage = SupabaseStorageProvider(
        organization_id="org_123",
        user_id="user_456"
    )

    # Create a simple test image (1x1 pixel PNG)
    test_image_data = bytes([
        0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A,  # PNG signature
        0x00, 0x00, 0x00, 0x0D, 0x49, 0x48, 0x44, 0x52,  # IHDR chunk
        0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x01,  # 1x1 pixel
        0x08, 0x06, 0x00, 0x00, 0x00, 0x1F, 0x15, 0xC4,  # RGBA, etc.
        0x89, 0x00, 0x00, 0x00, 0x0A, 0x49, 0x44, 0x41,  # IDAT chunk
        0x54, 0x08, 0x1D, 0x01, 0x02, 0x00, 0x01, 0x00,  # Image data
        0x00, 0x00, 0x00, 0x00, 0x49, 0x45, 0x4E, 0x44,  # IEND chunk
        0xAE, 0x42, 0x60, 0x82
    ])

    filename = "test_avatar.png"

    # Configure upload options for image processing
    options = UploadOptions(
        file_category="avatar",
        title="User Avatar",
        description="Profile picture for user",
        tags=["avatar", "profile", "image"],
        virus_scan=True,
        content_validation=True,
        generate_thumbnails=True,
        optimize_images=True,
        download_permission=DownloadPermission.ORGANIZATION
    )

    try:
        # Upload the image
        result = await storage.upload_file(test_image_data, filename, options)

        print(f"✅ Image upload successful!")
        print(f"   File ID: {result.file_id}")
        print(f"   Storage Path: {result.storage_path}")
        print(f"   CDN URL: {result.cdn_url}")
        print(f"   Thumbnail URL: {result.thumbnail_url}")
        print(f"   Processing Metadata: {result.processing_metadata}")

        return result.file_id

    except Exception as e:
        print(f"❌ Image upload failed: {e}")
        return None


async def multipart_upload_example():
    """Multipart upload with progress tracking example"""
    print("\n=== Multipart Upload Example ===")

    # Initialize storage provider
    storage = SupabaseStorageProvider(
        organization_id="org_123",
        user_id="user_456"
    )

    # Create a larger test file (simulate chunks)
    async def generate_file_chunks():
        """Generate file chunks for streaming upload"""
        chunk_size = 1024  # 1KB chunks
        total_chunks = 100  # 100KB total file

        for i in range(total_chunks):
            chunk_data = f"Chunk {i:03d}: " + "x" * (chunk_size - 20) + "\n"
            yield chunk_data.encode()

    filename = "large_document.txt"
    total_size = 100 * 1024  # 100KB

    options = UploadOptions(
        file_category="educational_content",
        title="Large Educational Document",
        description="A larger document for multipart upload demonstration",
        virus_scan=True,
        content_validation=True
    )

    try:
        # Start multipart upload
        upload_generator = storage.upload_file_multipart(
            generate_file_chunks(),
            filename,
            total_size,
            options
        )

        print("📤 Starting multipart upload...")

        # Track progress
        async for progress in upload_generator:
            if hasattr(progress, 'progress_percentage'):
                print(f"   Progress: {progress.progress_percentage:.1f}% "
                      f"({progress.bytes_uploaded}/{progress.total_bytes} bytes)")
            else:
                # Final result
                result = progress
                print(f"✅ Multipart upload completed!")
                print(f"   File ID: {result.file_id}")
                print(f"   Final size: {result.file_size} bytes")
                return result.file_id

    except Exception as e:
        print(f"❌ Multipart upload failed: {e}")
        return None


async def compliance_and_security_example():
    """Compliance and security checking example"""
    print("\n=== Compliance and Security Example ===")

    # Initialize security manager
    security = SecurityManager(encryption_key="test_encryption_key_for_demo")

    # Test file with potential PII
    test_content = """
    Student Information:
    Name: John Doe
    Email: john.doe@example.com
    Phone: (555) 123-4567
    Student ID: STU123456
    DOB: 01/15/2010
    """

    filename = "student_record.txt"
    file_data = test_content.encode()

    # Configure upload for student submission
    options = UploadOptions(
        file_category="student_submission",
        title="Student Assignment",
        description="Student homework submission",
        require_consent=True,
        virus_scan=True,
        content_validation=True
    )

    # Organization context (simulate COPPA-applicable student)
    org_context = {
        "student_age": 12,  # Under 13, COPPA applies
        "parental_consent": True,
        "legitimate_educational_interest": True
    }

    try:
        # Check compliance
        compliance_result = await security.check_compliance(
            file_data, filename, options, org_context
        )

        print(f"📋 Compliance Check Results:")
        print(f"   Compliant: {'✅' if compliance_result.is_compliant else '❌'}")
        print(f"   Required Level: {compliance_result.required_level.value}")
        print(f"   Current Level: {compliance_result.current_level.value}")
        print(f"   Encryption Required: {compliance_result.encryption_required}")
        print(f"   Retention Required: {compliance_result.retention_required}")

        if compliance_result.issues:
            print(f"   Issues: {compliance_result.issues}")

        if compliance_result.recommendations:
            print(f"   Recommendations: {compliance_result.recommendations}")

        # Check PII detection
        if compliance_result.pii_detection:
            pii = compliance_result.pii_detection
            print(f"   PII Detected: {'✅' if pii.has_pii else '❌'}")
            if pii.has_pii:
                print(f"   PII Types: {[t.value for t in pii.pii_types]}")
                print(f"   Risk Level: {pii.risk_level.value}")

        # Demonstrate encryption if required
        if compliance_result.encryption_required:
            print("\n🔐 Encrypting sensitive content...")
            encrypted_data, metadata = await security.encrypt_sensitive_file(
                file_data, "org_123", "student_record_context"
            )
            print(f"   Encryption successful: {metadata['encrypted']}")
            print(f"   Algorithm: {metadata['algorithm']}")

            # Decrypt to verify
            decrypted_data = await security.decrypt_sensitive_file(
                encrypted_data, metadata, "org_123"
            )
            print(f"   Decryption successful: {decrypted_data == file_data}")

    except Exception as e:
        print(f"❌ Compliance check failed: {e}")


async def storage_analytics_example():
    """Storage analytics and quota management example"""
    print("\n=== Storage Analytics Example ===")

    # Initialize tenant storage manager (would use real Supabase client)
    from supabase import create_client
    from toolboxai_settings.settings import settings

    if settings.supabase.is_configured():
        supabase_client = create_client(
            settings.supabase.url,
            settings.supabase.service_role_key
        )
        tenant_manager = TenantStorageManager(supabase_client)
    else:
        print("⚠️  Supabase not configured, using mock data")
        tenant_manager = None

    organization_id = "org_123"

    try:
        if tenant_manager:
            # Get storage usage
            usage = await tenant_manager.get_storage_usage(organization_id)

            print(f"📊 Storage Usage for {organization_id}:")
            print(f"   Total Files: {usage.total_files}")
            print(f"   Total Size: {usage.total_size_mb:.2f} MB")
            print(f"   Quota Used: {usage.used_quota_percentage:.1f}%")
            print(f"   Files by Category: {usage.files_by_category}")

            # Check for quota alerts
            alerts = await tenant_manager.check_quota_alerts(organization_id)
            if alerts:
                print(f"   🚨 Quota Alerts:")
                for alert in alerts:
                    print(f"     {alert.alert_type}: {alert.message}")

            # Get analytics
            analytics = await tenant_manager.get_storage_analytics(organization_id, days=30)
            print(f"   📈 Analytics: {analytics.get('period_days', 'N/A')} days")

        else:
            print("📊 Mock Storage Analytics:")
            print("   Total Files: 150")
            print("   Total Size: 2.5 GB")
            print("   Quota Used: 25.0%")
            print("   Files by Category: {'educational_content': 80, 'student_submission': 50, 'media_resource': 20}")

    except Exception as e:
        print(f"❌ Analytics failed: {e}")


async def cdn_optimization_example():
    """CDN optimization and image transformation example"""
    print("\n=== CDN Optimization Example ===")

    # Initialize CDN manager
    cdn_config = CDNConfiguration(
        base_url="https://cdn.toolboxai.com",
        signing_key="demo_signing_key",
        enable_webp_conversion=True,
        enable_compression=True
    )

    cdn = CDNManager(cdn_config)

    storage_path = "org_123/avatars/2025/01/user_avatar_001.jpg"

    try:
        # Generate optimized URLs for different use cases
        print(f"🌐 CDN URL Examples for: {storage_path}")

        # Avatar preset
        avatar_url = await cdn.get_preset_url(
            storage_path, "avatar", CacheLevel.LONG, "org_123"
        )
        print(f"   Avatar (150x150): {avatar_url}")

        # Thumbnail preset
        thumbnail_url = await cdn.get_preset_url(
            storage_path, "thumbnail", CacheLevel.MEDIUM, "org_123"
        )
        print(f"   Thumbnail (300x200): {thumbnail_url}")

        # Custom transformation
        custom_transform = ImageTransformation(
            width=500,
            height=300,
            quality=85,
            resize_mode="crop",
            crop_gravity="face"
        )

        custom_url = await cdn.get_optimized_url(
            storage_path, custom_transform, CacheLevel.MEDIUM, organization_id="org_123"
        )
        print(f"   Custom (500x300 crop): {custom_url}")

        # Responsive URLs
        responsive_urls = await cdn.get_responsive_urls(
            storage_path, [480, 768, 1024], CacheLevel.LONG, "org_123"
        )
        print(f"   Responsive URLs:")
        for breakpoint, url in responsive_urls.items():
            print(f"     {breakpoint}: {url}")

        # Optimized delivery based on user context
        mobile_context = {
            "device_type": "mobile",
            "connection_speed": "slow",
            "country": "US"
        }

        optimized_url = await cdn.optimize_delivery(
            storage_path, mobile_context, "org_123"
        )
        print(f"   Mobile Optimized: {optimized_url}")

        # Get CDN statistics
        stats = await cdn.get_cdn_stats("org_123")
        print(f"\n📈 CDN Statistics:")
        print(f"   Total Requests: {stats.total_requests:,}")
        print(f"   Cache Hit Ratio: {stats.cache_hit_ratio:.1f}%")
        print(f"   Bandwidth: {stats.bandwidth_gb:.2f} GB")
        print(f"   Avg Response Time: {stats.avg_response_time_ms:.1f}ms")

    except Exception as e:
        print(f"❌ CDN optimization failed: {e}")


async def file_download_and_streaming_example(file_id):
    """File download and streaming example"""
    if not file_id:
        print("\n⚠️  Skipping download example - no file uploaded")
        return

    print(f"\n=== File Download Example ===")

    # Initialize storage provider
    storage = SupabaseStorageProvider(
        organization_id="org_123",
        user_id="user_456"
    )

    try:
        # Configure download options
        download_options = DownloadOptions(
            include_metadata=True,
            track_access=True,
            signed_url_expires_in=3600
        )

        # Download file information
        download_result = await storage.download_file(file_id, download_options)

        print(f"📥 Download Information:")
        print(f"   File URL: {download_result.file_url}")
        print(f"   Content Type: {download_result.content_type}")
        print(f"   Content Length: {download_result.content_length} bytes")
        print(f"   Expires At: {download_result.expires_at}")

        if download_result.metadata:
            print(f"   Metadata: {download_result.metadata}")

        # Stream file content
        print(f"\n📤 Streaming file content:")
        chunk_count = 0
        total_bytes = 0

        async for chunk in storage.get_file_stream(file_id):
            chunk_count += 1
            total_bytes += len(chunk)
            if chunk_count <= 3:  # Show first 3 chunks
                preview = chunk[:50].decode('utf-8', errors='ignore')
                print(f"   Chunk {chunk_count}: {len(chunk)} bytes - {preview}...")

        print(f"   Total: {chunk_count} chunks, {total_bytes} bytes")

    except Exception as e:
        print(f"❌ Download failed: {e}")


async def file_management_example():
    """File management operations example"""
    print("\n=== File Management Example ===")

    # Initialize storage provider
    storage = SupabaseStorageProvider(
        organization_id="org_123",
        user_id="user_456"
    )

    try:
        # List files with filtering
        list_options = ListOptions(
            limit=10,
            offset=0,
            file_types=["text/plain", "image/png"],
            categories=["educational_content", "avatar"],
            include_metadata=True,
            sort_by="created_at",
            sort_order="desc"
        )

        files = await storage.list_files(list_options)

        print(f"📁 File Listing ({len(files)} files):")
        for file_info in files[:5]:  # Show first 5 files
            print(f"   📄 {file_info.filename}")
            print(f"      ID: {file_info.file_id}")
            print(f"      Size: {file_info.file_size} bytes")
            print(f"      Type: {file_info.mime_type}")
            print(f"      Created: {file_info.created_at}")

        if files:
            # Get detailed info for first file
            file_info = await storage.get_file_info(files[0].file_id)
            if file_info:
                print(f"\n📋 Detailed File Info:")
                print(f"   Filename: {file_info.filename}")
                print(f"   Original: {file_info.original_filename}")
                print(f"   Storage Path: {file_info.storage_path}")
                print(f"   CDN URL: {file_info.cdn_url}")
                print(f"   Tags: {file_info.tags}")

    except Exception as e:
        print(f"❌ File management failed: {e}")


async def main():
    """Run all storage service examples"""
    print("🚀 ToolBoxAI Storage Service Examples")
    print("=" * 50)

    # Basic examples
    file_id_1 = await basic_file_upload_example()
    file_id_2 = await image_upload_with_processing_example()
    file_id_3 = await multipart_upload_example()

    # Advanced features
    await compliance_and_security_example()
    await storage_analytics_example()
    await cdn_optimization_example()

    # File operations
    await file_download_and_streaming_example(file_id_1)
    await file_management_example()

    print("\n✅ All examples completed!")
    print("\nNote: This demonstration uses mock data and test configurations.")
    print("In production, ensure proper Supabase configuration and security keys.")


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # Run examples
    asyncio.run(main())