# Storage User Guide

This guide shows you how to use the ToolBoxAI Storage System for managing files in your educational platform. Whether you're a teacher uploading course materials or a student submitting assignments, this guide covers everything you need to know.

## Table of Contents
- [Quick Start](#quick-start)
- [Uploading Files](#uploading-files)
- [Managing File Versions](#managing-file-versions)
- [Sharing Files](#sharing-files)
- [Understanding Storage Quotas](#understanding-storage-quotas)
- [File Categories and Retention](#file-categories-and-retention)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)

## Quick Start

### Basic File Upload

The simplest way to upload a file:

```python
from apps.backend.services.storage import SupabaseStorageProvider, UploadOptions

# Initialize storage with your organization context
storage = SupabaseStorageProvider(
    organization_id="your-org-id",
    user_id="your-user-id"
)

# Upload a file
file_data = open("my-document.pdf", "rb").read()
options = UploadOptions(
    file_category="educational_content",
    title="Course Introduction",
    description="Introduction materials for Biology 101"
)

result = await storage.upload_file(file_data, "intro-biology.pdf", options)
print(f"File uploaded! ID: {result.file_id}")
print(f"Access URL: {result.cdn_url}")
```

### Basic File Download

Download a file you have access to:

```python
# Download by file ID
download_result = await storage.download_file(file_id="your-file-id")

# Access the file
if download_result.success:
    print(f"Download URL: {download_result.file_url}")
    print(f"Expires at: {download_result.expires_at}")
else:
    print(f"Download failed: {download_result.error_message}")
```

## Uploading Files

### Upload Options

The storage system supports various upload configurations:

```python
from apps.backend.services.storage import UploadOptions, FileCategory

# Basic educational content
options = UploadOptions(
    file_category=FileCategory.EDUCATIONAL_CONTENT,
    title="Advanced Mathematics",
    description="Calculus textbook chapter 5",
    tags=["mathematics", "calculus", "textbook"],
    virus_scan=True,  # Always recommended
    content_validation=True,
    generate_thumbnails=True,  # For images/videos
    optimize_images=True
)

# Student assignment submission
assignment_options = UploadOptions(
    file_category=FileCategory.STUDENT_SUBMISSION,
    title="Lab Report - Photosynthesis",
    metadata={
        "assignment_id": "bio101_lab_03",
        "due_date": "2025-02-15",
        "submission_attempt": 1
    },
    requires_consent=True,  # FERPA compliance
    retention_days=2555  # 7 years for student records
)

# Profile picture
avatar_options = UploadOptions(
    file_category=FileCategory.AVATAR,
    title="Student Profile Picture",
    max_file_size_mb=10,
    requires_parental_consent=True  # COPPA compliance for minors
)
```

### File Categories

Choose the appropriate category for your files:

#### Educational Content
```python
# Course materials, textbooks, references
options = UploadOptions(
    file_category=FileCategory.EDUCATIONAL_CONTENT,
    title="Course Syllabus",
    allowed_mime_types=["application/pdf", "text/plain", "application/msword"],
    max_file_size_mb=100
)
```

#### Student Submissions
```python
# Assignments, projects, essays
options = UploadOptions(
    file_category=FileCategory.STUDENT_SUBMISSION,
    title="History Essay",
    metadata={"assignment_id": "hist_essay_01"},
    requires_consent=True,  # FERPA protected
    max_file_size_mb=50
)
```

#### Media Resources
```python
# Images, videos, audio files
options = UploadOptions(
    file_category=FileCategory.MEDIA_RESOURCE,
    title="Laboratory Procedure Video",
    generate_thumbnails=True,
    optimize_images=True,
    max_file_size_mb=500
)
```

### Large File Uploads

For files larger than 100MB, use the multipart upload:

```python
# Large video file upload with progress tracking
async def upload_large_file():
    file_path = "large-lecture-video.mp4"
    file_size = os.path.getsize(file_path)

    with open(file_path, "rb") as f:
        result = await storage.upload_file_multipart(
            file_stream=f,
            filename="lecture-01-introduction.mp4",
            total_size=file_size,
            options=UploadOptions(
                file_category=FileCategory.MEDIA_RESOURCE,
                title="Introduction to Biology",
                chunk_size=10 * 1024 * 1024  # 10MB chunks
            ),
            progress_callback=upload_progress_callback
        )

    return result

def upload_progress_callback(bytes_uploaded: int, total_bytes: int):
    percentage = (bytes_uploaded / total_bytes) * 100
    print(f"Upload progress: {percentage:.1f}%")
```

### Batch Uploads

Upload multiple files efficiently:

```python
files_to_upload = [
    {
        "file_data": open("chapter1.pdf", "rb").read(),
        "filename": "chapter1.pdf",
        "options": UploadOptions(
            file_category=FileCategory.EDUCATIONAL_CONTENT,
            title="Chapter 1: Introduction"
        )
    },
    {
        "file_data": open("chapter2.pdf", "rb").read(),
        "filename": "chapter2.pdf",
        "options": UploadOptions(
            file_category=FileCategory.EDUCATIONAL_CONTENT,
            title="Chapter 2: Fundamentals"
        )
    }
]

# Batch upload with progress tracking
results = await storage.upload_files_batch(
    files_to_upload,
    parallel_uploads=3,  # Upload 3 files simultaneously
    progress_callback=batch_progress_callback
)

for result in results:
    if result.success:
        print(f"✓ {result.filename} uploaded: {result.file_id}")
    else:
        print(f"✗ {result.filename} failed: {result.error_message}")
```

## Managing File Versions

### Creating New Versions

When you upload a file with the same name to replace an existing file:

```python
# Upload initial version
original_result = await storage.upload_file(
    file_data=open("syllabus_v1.pdf", "rb").read(),
    filename="course-syllabus.pdf",
    options=UploadOptions(
        file_category=FileCategory.EDUCATIONAL_CONTENT,
        title="Course Syllabus"
    )
)

# Upload updated version
updated_result = await storage.upload_file_version(
    file_id=original_result.file_id,
    file_data=open("syllabus_v2.pdf", "rb").read(),
    filename="course-syllabus.pdf",
    change_description="Added midterm exam date",
    options=UploadOptions(
        file_category=FileCategory.EDUCATIONAL_CONTENT,
        title="Course Syllabus (Updated)"
    )
)

print(f"New version created: {updated_result.version_number}")
```

### Viewing Version History

```python
# Get all versions of a file
versions = await storage.get_file_versions(file_id="your-file-id")

for version in versions:
    print(f"Version {version.version_number}:")
    print(f"  Created: {version.created_at}")
    print(f"  Changed by: {version.changed_by}")
    print(f"  Description: {version.change_description}")
    print(f"  Size: {version.file_size} bytes")
    print()
```

### Rolling Back to Previous Version

```python
# Rollback to a specific version
rollback_result = await storage.rollback_to_version(
    file_id="your-file-id",
    version_number=2,
    change_description="Rollback due to error in version 3"
)

if rollback_result.success:
    print(f"Rolled back to version {rollback_result.version_number}")
else:
    print(f"Rollback failed: {rollback_result.error_message}")
```

## Sharing Files

### Creating Share Links

Generate secure links to share files:

```python
from apps.backend.services.storage import ShareOptions, ShareType

# Public link with expiration
public_share = await storage.create_share_link(
    file_id="your-file-id",
    options=ShareOptions(
        share_type=ShareType.PUBLIC_LINK,
        expires_in_hours=48,
        password_protected=False,
        can_download=True,
        max_downloads=100
    )
)

print(f"Share URL: {public_share.share_url}")
print(f"Expires: {public_share.expires_at}")

# Password-protected link
protected_share = await storage.create_share_link(
    file_id="your-file-id",
    options=ShareOptions(
        share_type=ShareType.PUBLIC_LINK,
        password="secure-password-123",
        expires_in_hours=24,
        can_download=True,
        view_only=False
    )
)

print(f"Protected URL: {protected_share.share_url}")
print(f"Password: {protected_share.password}")
```

### Organization Sharing

Share with all members of your organization:

```python
# Share with organization
org_share = await storage.create_share_link(
    file_id="your-file-id",
    options=ShareOptions(
        share_type=ShareType.ORGANIZATION,
        can_download=True,
        expires_in_days=30
    )
)

# Share with specific class
class_share = await storage.create_share_link(
    file_id="your-file-id",
    options=ShareOptions(
        share_type=ShareType.CLASS,
        class_id="bio101_spring2025",
        can_download=True,
        notify_recipients=True
    )
)
```

### User-Specific Sharing

Share with specific users:

```python
# Share with specific users
user_share = await storage.create_share_link(
    file_id="your-file-id",
    options=ShareOptions(
        share_type=ShareType.SPECIFIC_USERS,
        user_ids=["user1", "user2", "user3"],
        can_download=True,
        notify_recipients=True,
        message="Please review this assignment rubric"
    )
)
```

### Managing Shared Links

```python
# List all shares for a file
shares = await storage.list_file_shares(file_id="your-file-id")

for share in shares:
    print(f"Share ID: {share.id}")
    print(f"Type: {share.share_type}")
    print(f"Created: {share.created_at}")
    print(f"Downloads: {share.download_count}")
    print(f"Last accessed: {share.last_accessed_at}")

# Revoke a share
await storage.revoke_share_link(share_id="share-id")

# Update share permissions
await storage.update_share_link(
    share_id="share-id",
    updates={
        "expires_at": datetime.now() + timedelta(days=7),
        "max_downloads": 50
    }
)
```

## Understanding Storage Quotas

### Checking Usage

Monitor your organization's storage usage:

```python
# Get current usage
usage = await storage.get_storage_usage()

print(f"Total quota: {usage.total_quota_gb} GB")
print(f"Used storage: {usage.used_storage_gb} GB")
print(f"Available: {usage.available_storage_gb} GB")
print(f"Usage percentage: {usage.used_percentage}%")
print(f"File count: {usage.file_count} / {usage.max_files}")

# Check if approaching limits
if usage.is_warning_threshold_reached():
    print("⚠️  Warning: Storage usage is above 80%")

if usage.is_critical_threshold_reached():
    print("🚨 Critical: Storage usage is above 95%")
```

### Usage by Category

See how storage is distributed across file categories:

```python
# Get usage breakdown
breakdown = await storage.get_usage_by_category()

for category, usage in breakdown.items():
    print(f"{category}:")
    print(f"  Files: {usage.file_count}")
    print(f"  Size: {usage.total_size_mb} MB")
    print(f"  Percentage: {usage.percentage_of_total}%")
```

### Quota Alerts

Set up automatic alerts for quota thresholds:

```python
# Configure quota alerts
await storage.configure_quota_alerts(
    warning_threshold=75,  # Alert at 75%
    critical_threshold=90,  # Critical alert at 90%
    alert_email="admin@school.edu",
    daily_reports=True
)
```

## File Categories and Retention

### Understanding Categories

Each file category has specific retention policies:

| Category | Retention Period | Auto-Delete | Compliance |
|----------|------------------|-------------|------------|
| Educational Content | 7 years | No | Standard |
| Student Submission | Student lifecycle | No | FERPA |
| Assessment | 7 years | No | FERPA |
| Media Resource | 5 years | Yes | Standard |
| Avatar | User lifecycle | Yes | COPPA |
| Administrative | Regulatory | No | FERPA |
| Temporary | 30 days | Yes | Standard |
| Report | 3 years | Yes | FERPA |

### Setting Custom Retention

Override default retention for specific files:

```python
# Set custom retention period
await storage.set_file_retention(
    file_id="your-file-id",
    retention_days=1825,  # 5 years
    auto_delete=False,
    retention_reason="Required by state law"
)

# Schedule deletion
deletion_date = datetime.now() + timedelta(days=365)
await storage.schedule_file_deletion(
    file_id="your-file-id",
    deletion_date=deletion_date,
    reason="End of academic year cleanup"
)
```

### Retention Reports

Generate reports on upcoming deletions:

```python
# Get files scheduled for deletion
upcoming_deletions = await storage.get_upcoming_deletions(
    days_ahead=30  # Next 30 days
)

for file_info in upcoming_deletions:
    print(f"File: {file_info.filename}")
    print(f"Deletion date: {file_info.deletion_date}")
    print(f"Reason: {file_info.deletion_reason}")
    print(f"Category: {file_info.category}")
    print()
```

## Best Practices

### File Organization

1. **Use Descriptive Filenames**
   ```python
   # Good
   "Bio101_Syllabus_Spring2025.pdf"
   "Lab03_Photosynthesis_Instructions.pdf"

   # Avoid
   "syllabus.pdf"
   "lab.pdf"
   ```

2. **Add Meaningful Metadata**
   ```python
   options = UploadOptions(
       title="Laboratory Safety Guidelines",
       description="Comprehensive safety procedures for chemistry lab",
       tags=["safety", "chemistry", "laboratory", "procedures"],
       metadata={
           "course_code": "CHEM101",
           "semester": "Spring2025",
           "version": "3.1",
           "approval_date": "2025-01-15"
       }
   )
   ```

3. **Choose Appropriate Categories**
   - Use `educational_content` for course materials
   - Use `student_submission` for assignments
   - Use `media_resource` for images and videos
   - Use `temporary` for files that can be deleted

### Security Best Practices

1. **Enable Virus Scanning**
   ```python
   options = UploadOptions(
       virus_scan=True,  # Always enable
       content_validation=True
   )
   ```

2. **Use Appropriate Sharing**
   ```python
   # Limit access appropriately
   ShareOptions(
       share_type=ShareType.CLASS,  # Not public
       expires_in_hours=48,  # Set expiration
       max_downloads=30,  # Limit downloads
       password_protected=True  # Add password for sensitive content
   )
   ```

3. **Regular Access Reviews**
   ```python
   # Review file access logs
   access_logs = await storage.get_file_access_logs(
       file_id="sensitive-file-id",
       days=30
   )

   for log in access_logs:
       print(f"User: {log.user_id} accessed at {log.accessed_at}")
   ```

### Performance Optimization

1. **Use Appropriate File Formats**
   - PDFs for documents
   - WebP for images (auto-converted)
   - MP4 for videos
   - Compressed formats when possible

2. **Enable Image Optimization**
   ```python
   options = UploadOptions(
       optimize_images=True,
       generate_thumbnails=True,
       responsive_variants=True
   )
   ```

3. **Use CDN URLs for Public Content**
   ```python
   # Use CDN URL for better performance
   cdn_url = result.cdn_url  # Instead of direct storage URL
   ```

## Troubleshooting

### Common Upload Issues

**File Too Large**
```python
# Check quota before upload
usage = await storage.get_storage_usage()
if not usage.has_storage_available(file_size):
    print("Insufficient storage space")
    # Request quota increase or clean up old files
```

**Unsupported File Type**
```python
# Check allowed MIME types for category
allowed_types = await storage.get_allowed_mime_types(
    category=FileCategory.EDUCATIONAL_CONTENT
)
print(f"Allowed types: {allowed_types}")
```

**Virus Detected**
```python
# Handle virus scan failures
try:
    result = await storage.upload_file(file_data, filename, options)
except VirusDetectedException as e:
    print(f"Virus detected: {e.threat_name}")
    print("File has been quarantined")
    # Notify user to scan their device
```

### Download Issues

**Access Denied**
```python
# Check file permissions
permissions = await storage.check_file_permissions(
    file_id="your-file-id",
    user_id="current-user-id"
)

if not permissions.can_read:
    print(f"Access denied: {permissions.denial_reason}")
```

**Expired Share Link**
```python
# Check share link status
share_info = await storage.get_share_info(share_token="token")

if share_info.is_expired:
    print("Share link has expired")
elif share_info.has_exceeded_downloads:
    print("Download limit exceeded")
```

### Storage Quota Issues

**Quota Exceeded**
```python
# Find large files that can be cleaned up
large_files = await storage.find_large_files(
    min_size_mb=50,
    categories=[FileCategory.TEMPORARY, FileCategory.MEDIA_RESOURCE]
)

for file_info in large_files:
    print(f"{file_info.filename}: {file_info.size_mb} MB")
    print(f"Last accessed: {file_info.last_accessed_at}")
```

**Clean Up Old Files**
```python
# Remove old temporary files
cleanup_result = await storage.cleanup_old_files(
    categories=[FileCategory.TEMPORARY],
    max_age_days=30,
    dry_run=True  # Preview what would be deleted
)

print(f"Would delete {cleanup_result.file_count} files")
print(f"Would free {cleanup_result.space_freed_mb} MB")

# Actually perform cleanup
if input("Proceed? (y/n): ").lower() == 'y':
    await storage.cleanup_old_files(
        categories=[FileCategory.TEMPORARY],
        max_age_days=30,
        dry_run=False
    )
```

### Getting Help

**Enable Debug Logging**
```python
import logging
logging.getLogger('apps.backend.services.storage').setLevel(logging.DEBUG)
```

**Contact Support**
- Check the API documentation for detailed error codes
- Review system logs for additional context
- Contact your system administrator for quota increases
- Report security issues immediately to the security team

For more technical details, see:
- [API Reference](../03-api/STORAGE_API_REFERENCE.md)
- [Implementation Guide](../04-implementation/SUPABASE_STORAGE.md)
- [Security Guide](../05-features/storage/SECURITY_COMPLIANCE.md)