# ToolBoxAI Storage Service

A comprehensive file storage system for the ToolBoxAI Educational Platform with multi-tenant isolation, security, compliance, and performance optimization.

## Features

### 🏢 Multi-Tenant Architecture
- **Organization Isolation**: Complete tenant separation at bucket and database level
- **Context Management**: Automatic organization and user context handling
- **Quota Management**: Per-organization storage limits and monitoring
- **Usage Analytics**: Detailed storage analytics and recommendations

### 🔒 Security & Compliance
- **COPPA/FERPA Compliance**: Educational platform-specific compliance checking
- **PII Detection**: Advanced personally identifiable information scanning
- **File Encryption**: Sensitive file encryption with organization-specific keys
- **Access Control**: Role-based access control with audit logging
- **Virus Scanning**: ClamAV integration with quarantine management

### 🖼️ Image Processing
- **Thumbnail Generation**: Multiple size thumbnails automatically generated
- **Format Optimization**: WebP conversion and progressive JPEG support
- **Responsive Variants**: Multiple breakpoint images for responsive design
- **EXIF Stripping**: Privacy protection through metadata removal
- **Smart Compression**: Quality optimization based on content analysis

### 🌐 CDN Integration
- **Smart Caching**: Intelligent cache strategies for educational content
- **Image Transformations**: On-the-fly image resizing and optimization
- **Signed URLs**: Secure access with expiration and signature verification
- **Geographic Distribution**: Multi-region content delivery
- **Performance Monitoring**: Real-time CDN statistics and optimization

### 📁 File Management
- **Validation**: Comprehensive file type, size, and content validation
- **Versioning**: File version tracking and rollback capabilities
- **Sharing**: Secure file sharing with permissions and expiration
- **Cleanup**: Automated retention policies and old file cleanup
- **Search**: Advanced file search and filtering capabilities

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Storage API    │    │   Supabase      │
│   Dashboard     │───▶│   (FastAPI)      │───▶│   Storage       │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │
                                ▼
┌─────────────────┬──────────────────┬─────────────────┬─────────────────┐
│ File Validator  │ Virus Scanner    │ Image Processor │ Security Mgr    │
│ • MIME types    │ • ClamAV         │ • Thumbnails    │ • PII detection │
│ • Size limits   │ • Quarantine     │ • Optimization  │ • Encryption    │
│ • Content check │ • Background     │ • WebP convert  │ • Compliance    │
└─────────────────┴──────────────────┴─────────────────┴─────────────────┘
                                │
                                ▼
┌─────────────────┬──────────────────┬─────────────────┬─────────────────┐
│ Tenant Manager  │ CDN Manager      │ Database Models │ Background Jobs │
│ • Buckets       │ • Transformations│ • File metadata │ • Async scans   │
│ • Quotas        │ • Signed URLs    │ • Audit logs    │ • Cleanup       │
│ • Analytics     │ • Cache control  │ • Access logs   │ • Reports       │
└─────────────────┴──────────────────┴─────────────────┴─────────────────┘
```

## Quick Start

### 1. Installation

```bash
# Install required dependencies
pip install supabase pyclamd pillow cryptography aiohttp

# Optional: For document processing
pip install PyPDF2 python-docx pytesseract
```

### 2. Configuration

```python
# Environment variables (.env)
SUPABASE_URL=your_supabase_url
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key
SUPABASE_ANON_KEY=your_anon_key

# Optional: Virus scanning
CLAMAV_SOCKET_PATH=/var/run/clamav/clamd.ctl

# Optional: CDN
CDN_BASE_URL=https://cdn.yourapp.com
CDN_SIGNING_KEY=your_cdn_signing_key
```

### 3. Basic Usage

```python
from apps.backend.services.storage import (
    SupabaseStorageProvider,
    UploadOptions,
    DownloadPermission
)

# Initialize storage
storage = SupabaseStorageProvider(
    organization_id="org_123",
    user_id="user_456"
)

# Upload a file
file_data = b"Hello, World!"
options = UploadOptions(
    file_category="educational_content",
    title="Test Document",
    virus_scan=True,
    content_validation=True
)

result = await storage.upload_file(file_data, "test.txt", options)
print(f"Uploaded: {result.file_id}")

# Download a file
download_result = await storage.download_file(result.file_id)
print(f"Download URL: {download_result.file_url}")
```

## Service Components

### StorageService (Abstract Base)

The main interface defining all storage operations:

```python
class StorageService(ABC):
    async def upload_file(self, file_data, filename, options) -> UploadResult
    async def download_file(self, file_id, options) -> DownloadResult
    async def delete_file(self, file_id, permanent=False) -> bool
    async def list_files(self, options) -> List[FileInfo]
    # ... more methods
```

### SupabaseStorageProvider

Concrete implementation using Supabase Storage:

```python
provider = SupabaseStorageProvider(
    organization_id="org_123",
    user_id="user_456"
)

# Features:
# - Multi-tenant bucket management
# - Resumable uploads with progress tracking
# - Automatic virus scanning and quarantine
# - Image processing and optimization
# - CDN integration
```

### FileValidator

Comprehensive file validation:

```python
validator = FileValidator()

result = await validator.validate_file(
    file_data=file_bytes,
    filename="document.pdf",
    file_category="student_submission"
)

print(f"Valid: {result.is_valid}")
print(f"Errors: {result.errors}")
print(f"MIME Type: {result.detected_mime_type}")
```

### VirusScanner

ClamAV-based virus scanning:

```python
scanner = VirusScanner()

scan_result = await scanner.scan_data(file_data, filename)

if not scan_result.is_clean:
    print(f"Threat detected: {scan_result.threat_name}")
    # File would be quarantined automatically
```

### ImageProcessor

Advanced image processing:

```python
processor = ImageProcessor()

variants = await processor.process_image(
    image_data=image_bytes,
    generate_thumbnails=True,
    optimize=True
)

# Generated variants: original, thumbnails, responsive sizes, WebP
for name, variant in variants.items():
    print(f"{name}: {variant.width}x{variant.height}, {variant.file_size} bytes")
```

### SecurityManager

Security and compliance management:

```python
security = SecurityManager(encryption_key="your_key")

# Check compliance
compliance = await security.check_compliance(
    file_data=file_bytes,
    filename="student_record.pdf",
    options=upload_options,
    organization_context={"student_age": 12}
)

if compliance.encryption_required:
    encrypted_data, metadata = await security.encrypt_sensitive_file(
        file_data, organization_id
    )
```

### CDNManager

CDN optimization and management:

```python
cdn = CDNManager(CDNConfiguration(
    base_url="https://cdn.yourapp.com",
    enable_webp_conversion=True
))

# Get optimized URLs
avatar_url = await cdn.get_preset_url(
    storage_path="org_123/avatars/user.jpg",
    preset_name="avatar"
)

# Custom transformations
transform = ImageTransformation(width=500, height=300, quality=85)
custom_url = await cdn.get_optimized_url(storage_path, transform)

# Responsive URLs
responsive_urls = await cdn.get_responsive_urls(
    storage_path, breakpoints=[480, 768, 1024]
)
```

### TenantStorageManager

Multi-tenant management:

```python
tenant_manager = TenantStorageManager(supabase_client)

# Get storage usage
usage = await tenant_manager.get_storage_usage("org_123")
print(f"Used: {usage.total_size_mb} MB ({usage.used_quota_percentage}%)")

# Check quota alerts
alerts = await tenant_manager.check_quota_alerts("org_123")
for alert in alerts:
    print(f"Alert: {alert.alert_type} - {alert.message}")

# Update quota
await tenant_manager.update_quota("org_123", new_quota_gb=20)
```

## File Categories

The system supports different file categories with specific validation rules:

| Category | Description | MIME Types | Max Size | Compliance |
|----------|-------------|------------|----------|------------|
| `educational_content` | Educational materials | PDF, DOC, TXT, HTML | 100MB | Standard |
| `student_submission` | Student assignments | PDF, DOC, TXT, Images | 50MB | FERPA |
| `assessment` | Quizzes and tests | PDF, JSON, CSV | 25MB | FERPA |
| `media_resource` | Images, videos, audio | Images, Videos, Audio | 500MB | Standard |
| `avatar` | Profile pictures | Images only | 10MB | COPPA |
| `administrative` | Admin documents | Office docs, PDF | 100MB | FERPA |
| `temporary` | Temporary files | Any type | 1GB | Standard |
| `report` | Generated reports | PDF, Excel, CSV | 50MB | FERPA |

## Compliance Features

### COPPA Compliance
- Parental consent verification for users under 13
- Enhanced privacy controls for children's data
- Automatic encryption for child user files

### FERPA Compliance
- Educational record protection
- Legitimate educational interest verification
- Audit logging for all access
- Directory information opt-out support

### PII Detection
- Social Security Numbers
- Email addresses and phone numbers
- Student IDs and dates of birth
- Credit card numbers
- Custom pattern detection

## Security Features

### File Encryption
```python
# Automatic encryption for sensitive files
if compliance_check.encryption_required:
    encrypted_data, metadata = await security.encrypt_sensitive_file(
        file_data, organization_id
    )
```

### Access Control
```python
# Validate access before file operations
access_allowed, violations = await security.validate_access_control(
    file_id=file_id,
    user_id=current_user.id,
    organization_id=current_org.id,
    action="read"
)
```

### Audit Logging
```python
# All file operations are logged
await security.log_security_event(
    event_type="file_access",
    organization_id=org_id,
    user_id=user_id,
    resource_id=str(file_id),
    details={"action": "download", "ip_address": request.client.host}
)
```

## Performance Optimization

### Image Optimization
- Automatic WebP conversion for supported browsers
- Progressive JPEG for faster loading
- Multiple quality levels based on content analysis
- Responsive image variants for different screen sizes

### CDN Integration
- Intelligent caching strategies
- Geographic distribution
- On-the-fly image transformations
- Bandwidth optimization

### Database Optimization
- Indexed queries for fast file lookups
- Pagination support for large file lists
- Efficient storage usage calculations
- Background cleanup jobs

## Monitoring and Analytics

### Storage Analytics
```python
# Get comprehensive usage statistics
analytics = await tenant_manager.get_storage_analytics(
    organization_id="org_123",
    days=30
)

print(f"Growth trends: {analytics['trends']['daily_uploads']}")
print(f"Recommendations: {analytics['recommendations']}")
```

### CDN Statistics
```python
# Monitor CDN performance
stats = await cdn.get_cdn_stats("org_123")
print(f"Cache hit ratio: {stats.cache_hit_ratio}%")
print(f"Bandwidth usage: {stats.bandwidth_gb} GB")
```

### Quota Monitoring
```python
# Automated quota alerts
alerts = await tenant_manager.check_quota_alerts("org_123")
for alert in alerts:
    if alert.alert_type == "critical":
        # Send notification to administrators
        await send_quota_alert(alert)
```

## API Integration

### FastAPI Endpoints

Create API endpoints using the storage service:

```python
from fastapi import APIRouter, UploadFile, Depends
from apps.backend.services.storage import SupabaseStorageProvider

router = APIRouter()

@router.post("/files/upload")
async def upload_file(
    file: UploadFile,
    category: str = "media_resource",
    storage: SupabaseStorageProvider = Depends(get_storage_service)
):
    file_data = await file.read()

    options = UploadOptions(
        file_category=category,
        title=file.filename,
        virus_scan=True,
        content_validation=True
    )

    result = await storage.upload_file(file_data, file.filename, options)

    return {
        "file_id": result.file_id,
        "cdn_url": result.cdn_url,
        "status": result.status
    }

@router.get("/files/{file_id}/download")
async def download_file(
    file_id: UUID,
    storage: SupabaseStorageProvider = Depends(get_storage_service)
):
    result = await storage.download_file(file_id)
    return {"download_url": result.file_url}
```

## Background Jobs

### Celery Integration

```python
# Background virus scanning
@celery_app.task
async def virus_scan_task(scan_id: str, file_data: bytes, filename: str):
    scanner = VirusScanner()
    result = await scanner.scan_data(file_data, filename)

    if not result.is_clean:
        # Quarantine the file
        await quarantine_infected_file(scan_id, result)

    return result.to_dict()

# Automated cleanup
@celery_app.task
async def cleanup_old_files(organization_id: str):
    tenant_manager = TenantStorageManager(supabase_client)

    cleaned_count = await tenant_manager.cleanup_old_files(
        organization_id=organization_id,
        max_age_days=365,
        categories=["temporary"]
    )

    return f"Cleaned up {cleaned_count} files"
```

## Testing

### Unit Tests

```python
import pytest
from apps.backend.services.storage import FileValidator

@pytest.mark.asyncio
async def test_file_validation():
    validator = FileValidator()

    # Test valid file
    result = await validator.validate_file(
        file_data=b"Hello, World!",
        filename="test.txt",
        file_category="educational_content"
    )

    assert result.is_valid
    assert result.detected_mime_type == "text/plain"

@pytest.mark.asyncio
async def test_pii_detection():
    security = SecurityManager()

    # Test content with PII
    content = b"SSN: 123-45-6789"

    pii_result = await security.detect_pii(content, "test.txt")

    assert pii_result.has_pii
    assert PIIType.SSN in pii_result.pii_types
```

### Integration Tests

```python
@pytest.mark.asyncio
async def test_full_upload_workflow():
    storage = SupabaseStorageProvider(
        organization_id="test_org",
        user_id="test_user"
    )

    # Upload file
    result = await storage.upload_file(
        file_data=b"Test content",
        filename="test.txt",
        options=UploadOptions(file_category="educational_content")
    )

    assert result.status == UploadStatus.COMPLETED

    # Download file
    download_result = await storage.download_file(result.file_id)
    assert download_result.file_url

    # Clean up
    await storage.delete_file(result.file_id, permanent=True)
```

## Production Deployment

### Environment Setup

```bash
# Production environment variables
ENVIRONMENT=production
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your_production_service_role_key

# ClamAV configuration
CLAMAV_SOCKET_PATH=/var/run/clamav/clamd.ctl
CLAMAV_TCP_HOST=localhost
CLAMAV_TCP_PORT=3310

# CDN configuration
CDN_BASE_URL=https://cdn.yourapp.com
CDN_SIGNING_KEY=your_production_signing_key

# Security
ENCRYPTION_KEY=your_secure_encryption_key
STORAGE_SIGNING_SECRET=your_signing_secret
```

### Infrastructure Requirements

1. **Supabase Project**: With storage enabled and proper RLS policies
2. **ClamAV Daemon**: For virus scanning (or external service)
3. **CDN Service**: CloudFlare, AWS CloudFront, or similar
4. **Redis**: For caching and background jobs
5. **Celery Workers**: For background processing

### Monitoring Setup

```python
# Prometheus metrics
from prometheus_client import Counter, Histogram, Gauge

upload_counter = Counter('storage_uploads_total', 'Total file uploads')
scan_duration = Histogram('virus_scan_duration_seconds', 'Virus scan duration')
quota_usage = Gauge('storage_quota_usage_percent', 'Storage quota usage')

# Log structured events
import structlog

logger = structlog.get_logger()

logger.info(
    "file_uploaded",
    file_id=result.file_id,
    organization_id=org_id,
    file_size=result.file_size,
    category=options.file_category
)
```

## Troubleshooting

### Common Issues

1. **ClamAV Connection Failed**
   ```bash
   # Check ClamAV status
   sudo systemctl status clamav-daemon

   # Verify socket permissions
   ls -la /var/run/clamav/clamd.ctl
   ```

2. **Supabase Upload Errors**
   ```python
   # Check bucket policies and permissions
   buckets = supabase.storage.list_buckets()
   print(f"Available buckets: {[b['name'] for b in buckets]}")
   ```

3. **Image Processing Errors**
   ```bash
   # Install Pillow with all features
   pip install Pillow[all]

   # For AVIF support
   pip install pillow-avif-plugin
   ```

4. **Memory Issues with Large Files**
   ```python
   # Use streaming uploads for large files
   result = await storage.upload_file_multipart(
       file_stream=stream_large_file(),
       filename="large_file.zip",
       total_size=file_size
   )
   ```

### Performance Tuning

1. **Database Optimization**
   - Index frequently queried columns
   - Use pagination for large result sets
   - Implement database connection pooling

2. **Image Processing**
   - Use appropriate quality settings
   - Enable progressive JPEG
   - Implement lazy loading for thumbnails

3. **CDN Configuration**
   - Set appropriate cache headers
   - Use geographic distribution
   - Implement bandwidth throttling

## Contributing

1. Follow the existing code style and patterns
2. Add comprehensive tests for new features
3. Update documentation for API changes
4. Ensure security best practices are followed
5. Test with multiple file types and sizes

## License

This storage service is part of the ToolBoxAI Educational Platform and follows the project's licensing terms.

---

For more information, see the [example usage](./example_usage.py) file for comprehensive demonstrations of all features.