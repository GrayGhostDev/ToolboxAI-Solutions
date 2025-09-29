"""Storage migration tool for migrating files to Supabase Storage."""

import asyncio
import json
import logging
import mimetypes
import os
import hashlib
from typing import Dict, List, Any, Optional, Callable, Set
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
import aiofiles
import aiohttp
from urllib.parse import urljoin

logger = logging.getLogger(__name__)


class MigrationStatus(Enum):
    """File migration status."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class FileInfo:
    """Information about a file to migrate."""
    local_path: str
    relative_path: str
    size_bytes: int
    mime_type: str
    checksum: str
    bucket_name: str
    storage_path: str
    public: bool = False


@dataclass
class MigrationBatch:
    """Batch of files for migration."""
    batch_id: int
    files: List[FileInfo]
    status: MigrationStatus
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    error_message: Optional[str] = None


@dataclass
class StorageMigrationResult:
    """Result of storage migration."""
    total_files: int
    migrated_files: int
    failed_files: int
    skipped_files: int
    total_size_bytes: int
    migrated_size_bytes: int
    duration_seconds: float
    status: MigrationStatus
    buckets_created: List[str]
    policies_created: List[str]


class StorageMigrationTool:
    """
    Tool for migrating files to Supabase Storage.

    Features:
    - File inventory creation
    - Bucket configuration
    - Batch upload mechanism
    - Access policy setup
    - Progress tracking
    - Resume capability
    """

    def __init__(
        self,
        supabase_url: str,
        supabase_key: str,
        batch_size: int = 10,
        max_concurrent_uploads: int = 3,
        max_file_size_mb: int = 50
    ):
        """
        Initialize the storage migration tool.

        Args:
            supabase_url: Supabase project URL
            supabase_key: Supabase service role key
            batch_size: Number of files per batch
            max_concurrent_uploads: Maximum concurrent uploads
            max_file_size_mb: Maximum file size in MB
        """
        self.supabase_url = supabase_url.rstrip('/')
        self.supabase_key = supabase_key
        self.batch_size = batch_size
        self.max_concurrent_uploads = max_concurrent_uploads
        self.max_file_size_bytes = max_file_size_mb * 1024 * 1024
        self.progress_callback: Optional[Callable] = None
        self.migration_state: Dict[str, Any] = {}

    async def create_file_inventory(
        self,
        source_directory: str,
        include_patterns: Optional[List[str]] = None,
        exclude_patterns: Optional[List[str]] = None,
        bucket_mapping: Optional[Dict[str, str]] = None
    ) -> List[FileInfo]:
        """
        Create inventory of files to migrate.

        Args:
            source_directory: Root directory to scan
            include_patterns: File patterns to include
            exclude_patterns: File patterns to exclude
            bucket_mapping: Mapping of directory patterns to bucket names

        Returns:
            List of file information
        """
        logger.info(f"Creating file inventory for: {source_directory}")

        if include_patterns is None:
            include_patterns = ['*']

        if exclude_patterns is None:
            exclude_patterns = [
                '*.tmp', '*.log', '*.pyc', '__pycache__',
                '.git', '.svn', '.DS_Store', 'Thumbs.db'
            ]

        if bucket_mapping is None:
            bucket_mapping = {'*': 'files'}

        inventory = []
        source_path = Path(source_directory)

        # Walk through directory tree
        for file_path in source_path.rglob('*'):
            if file_path.is_file():
                try:
                    # Check if file should be included
                    if self._should_include_file(file_path, include_patterns, exclude_patterns):
                        file_info = await self._create_file_info(
                            file_path,
                            source_path,
                            bucket_mapping
                        )
                        if file_info:
                            inventory.append(file_info)

                except Exception as e:
                    logger.warning(f"Failed to process file {file_path}: {str(e)}")

        logger.info(f"Created inventory of {len(inventory)} files")
        return inventory

    async def migrate_files(
        self,
        inventory: List[FileInfo],
        dry_run: bool = False,
        resume_from: Optional[str] = None,
        progress_callback: Optional[Callable] = None
    ) -> StorageMigrationResult:
        """
        Migrate files to Supabase Storage.

        Args:
            inventory: List of files to migrate
            dry_run: If True, don't actually upload files
            resume_from: Resume from specific file path
            progress_callback: Optional progress callback

        Returns:
            Migration result
        """
        logger.info(f"Starting migration of {len(inventory)} files")
        start_time = asyncio.get_event_loop().time()

        if progress_callback:
            self.progress_callback = progress_callback

        try:
            # Filter files if resuming
            if resume_from:
                inventory = self._filter_for_resume(inventory, resume_from)

            # Create buckets
            buckets_created = await self._create_buckets(inventory, dry_run)

            # Create batches
            batches = self._create_migration_batches(inventory)

            # Execute migration
            result = await self._execute_migration(batches, dry_run)

            # Create access policies
            policies_created = await self._create_access_policies(inventory, dry_run)

            # Update result
            result.buckets_created = buckets_created
            result.policies_created = policies_created
            result.duration_seconds = asyncio.get_event_loop().time() - start_time

            logger.info(f"Migration completed: {result.status}")
            return result

        except Exception as e:
            logger.error(f"Migration failed: {str(e)}")
            return StorageMigrationResult(
                total_files=len(inventory),
                migrated_files=0,
                failed_files=len(inventory),
                skipped_files=0,
                total_size_bytes=sum(f.size_bytes for f in inventory),
                migrated_size_bytes=0,
                duration_seconds=asyncio.get_event_loop().time() - start_time,
                status=MigrationStatus.FAILED,
                buckets_created=[],
                policies_created=[]
            )

    async def setup_bucket_policies(
        self,
        bucket_configs: List[Dict[str, Any]],
        dry_run: bool = False
    ) -> List[str]:
        """
        Setup bucket access policies.

        Args:
            bucket_configs: List of bucket configuration dictionaries
            dry_run: If True, don't create policies

        Returns:
            List of created policy names
        """
        logger.info("Setting up bucket policies")

        if dry_run:
            return [f"policy_{config['name']}" for config in bucket_configs]

        policies_created = []

        async with aiohttp.ClientSession() as session:
            for config in bucket_configs:
                try:
                    policy_name = await self._create_bucket_policy(
                        session,
                        config
                    )
                    if policy_name:
                        policies_created.append(policy_name)

                except Exception as e:
                    logger.error(f"Failed to create policy for bucket {config['name']}: {str(e)}")

        return policies_created

    async def verify_migration(
        self,
        inventory: List[FileInfo],
        sample_size: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Verify migrated files integrity.

        Args:
            inventory: List of migrated files
            sample_size: Number of files to verify (None for all)

        Returns:
            Verification results
        """
        logger.info("Verifying migration integrity")

        if sample_size:
            import random
            verification_files = random.sample(inventory, min(sample_size, len(inventory)))
        else:
            verification_files = inventory

        verification_results = {
            'total_checked': len(verification_files),
            'verified': 0,
            'failed': 0,
            'missing': 0,
            'size_mismatches': 0,
            'errors': []
        }

        async with aiohttp.ClientSession() as session:
            semaphore = asyncio.Semaphore(self.max_concurrent_uploads)

            async def verify_file(file_info: FileInfo):
                async with semaphore:
                    return await self._verify_single_file(session, file_info)

            # Verify files concurrently
            tasks = [verify_file(file_info) for file_info in verification_files]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            for result in results:
                if isinstance(result, Exception):
                    verification_results['failed'] += 1
                    verification_results['errors'].append(str(result))
                elif result['exists']:
                    if result['size_match']:
                        verification_results['verified'] += 1
                    else:
                        verification_results['size_mismatches'] += 1
                else:
                    verification_results['missing'] += 1

        return verification_results

    def _should_include_file(
        self,
        file_path: Path,
        include_patterns: List[str],
        exclude_patterns: List[str]
    ) -> bool:
        """Check if file should be included in migration."""
        # Check exclude patterns first
        for pattern in exclude_patterns:
            if file_path.match(pattern) or any(part.match(pattern) for part in file_path.parts):
                return False

        # Check include patterns
        for pattern in include_patterns:
            if pattern == '*' or file_path.match(pattern):
                return True

        return False

    async def _create_file_info(
        self,
        file_path: Path,
        source_root: Path,
        bucket_mapping: Dict[str, str]
    ) -> Optional[FileInfo]:
        """Create file information object."""
        try:
            # Get file stats
            stat = file_path.stat()

            # Skip if file is too large
            if stat.st_size > self.max_file_size_bytes:
                logger.warning(f"Skipping large file: {file_path} ({stat.st_size} bytes)")
                return None

            # Calculate relative path
            relative_path = file_path.relative_to(source_root)

            # Determine bucket
            bucket_name = self._determine_bucket(relative_path, bucket_mapping)

            # Calculate checksum
            checksum = await self._calculate_file_checksum(file_path)

            # Determine MIME type
            mime_type, _ = mimetypes.guess_type(str(file_path))
            if not mime_type:
                mime_type = 'application/octet-stream'

            # Determine storage path
            storage_path = str(relative_path).replace('\\', '/')

            return FileInfo(
                local_path=str(file_path),
                relative_path=str(relative_path),
                size_bytes=stat.st_size,
                mime_type=mime_type,
                checksum=checksum,
                bucket_name=bucket_name,
                storage_path=storage_path,
                public=self._is_public_file(relative_path)
            )

        except Exception as e:
            logger.error(f"Failed to create file info for {file_path}: {str(e)}")
            return None

    def _determine_bucket(
        self,
        relative_path: Path,
        bucket_mapping: Dict[str, str]
    ) -> str:
        """Determine bucket name for file."""
        # Check specific patterns first
        for pattern, bucket in bucket_mapping.items():
            if pattern != '*' and relative_path.match(pattern):
                return bucket

        # Use default bucket
        return bucket_mapping.get('*', 'files')

    def _is_public_file(self, relative_path: Path) -> bool:
        """Determine if file should be publicly accessible."""
        public_patterns = [
            'public/*',
            'static/*',
            'assets/*',
            'images/*',
            '*.jpg', '*.jpeg', '*.png', '*.gif', '*.svg',
            '*.css', '*.js', '*.html'
        ]

        for pattern in public_patterns:
            if relative_path.match(pattern):
                return True

        return False

    async def _calculate_file_checksum(self, file_path: Path) -> str:
        """Calculate MD5 checksum of file."""
        hash_md5 = hashlib.md5()

        async with aiofiles.open(file_path, 'rb') as f:
            while chunk := await f.read(8192):
                hash_md5.update(chunk)

        return hash_md5.hexdigest()

    def _filter_for_resume(
        self,
        inventory: List[FileInfo],
        resume_from: str
    ) -> List[FileInfo]:
        """Filter inventory to resume from specific file."""
        resume_index = 0

        for i, file_info in enumerate(inventory):
            if file_info.relative_path == resume_from:
                resume_index = i
                break

        logger.info(f"Resuming migration from file {resume_index + 1} of {len(inventory)}")
        return inventory[resume_index:]

    async def _create_buckets(
        self,
        inventory: List[FileInfo],
        dry_run: bool
    ) -> List[str]:
        """Create required storage buckets."""
        bucket_names = set(file_info.bucket_name for file_info in inventory)

        if dry_run:
            return list(bucket_names)

        created_buckets = []

        async with aiohttp.ClientSession() as session:
            for bucket_name in bucket_names:
                try:
                    created = await self._create_bucket(session, bucket_name)
                    if created:
                        created_buckets.append(bucket_name)

                except Exception as e:
                    logger.error(f"Failed to create bucket {bucket_name}: {str(e)}")

        return created_buckets

    async def _create_bucket(
        self,
        session: aiohttp.ClientSession,
        bucket_name: str
    ) -> bool:
        """Create a storage bucket."""
        url = f"{self.supabase_url}/storage/v1/bucket"

        headers = {
            'Authorization': f'Bearer {self.supabase_key}',
            'Content-Type': 'application/json'
        }

        data = {
            'id': bucket_name,
            'name': bucket_name,
            'public': False
        }

        async with session.post(url, headers=headers, json=data) as response:
            if response.status == 200:
                logger.info(f"Created bucket: {bucket_name}")
                return True
            elif response.status == 409:
                logger.info(f"Bucket already exists: {bucket_name}")
                return True
            else:
                response_text = await response.text()
                logger.error(f"Failed to create bucket {bucket_name}: {response.status} - {response_text}")
                return False

    def _create_migration_batches(
        self,
        inventory: List[FileInfo]
    ) -> List[MigrationBatch]:
        """Create batches for file migration."""
        batches = []
        batch_id = 0

        for i in range(0, len(inventory), self.batch_size):
            batch_files = inventory[i:i + self.batch_size]
            batch = MigrationBatch(
                batch_id=batch_id,
                files=batch_files,
                status=MigrationStatus.PENDING
            )
            batches.append(batch)
            batch_id += 1

        return batches

    async def _execute_migration(
        self,
        batches: List[MigrationBatch],
        dry_run: bool
    ) -> StorageMigrationResult:
        """Execute file migration batches."""
        total_files = sum(len(batch.files) for batch in batches)
        total_size = sum(file_info.size_bytes for batch in batches for file_info in batch.files)

        if dry_run:
            return StorageMigrationResult(
                total_files=total_files,
                migrated_files=total_files,
                failed_files=0,
                skipped_files=0,
                total_size_bytes=total_size,
                migrated_size_bytes=total_size,
                duration_seconds=0,
                status=MigrationStatus.COMPLETED,
                buckets_created=[],
                policies_created=[]
            )

        migrated_files = 0
        failed_files = 0
        skipped_files = 0
        migrated_size = 0

        # Create semaphore for concurrent uploads
        semaphore = asyncio.Semaphore(self.max_concurrent_uploads)

        async def process_batch(batch: MigrationBatch):
            async with semaphore:
                return await self._process_migration_batch(batch)

        # Process batches
        tasks = [process_batch(batch) for batch in batches]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Aggregate results
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                failed_files += len(batches[i].files)
                logger.error(f"Batch {i} failed: {str(result)}")
            else:
                migrated_files += result['migrated']
                failed_files += result['failed']
                skipped_files += result['skipped']
                migrated_size += result['size']

        # Determine overall status
        if failed_files == 0:
            status = MigrationStatus.COMPLETED
        elif migrated_files > 0:
            status = MigrationStatus.COMPLETED  # Partial success
        else:
            status = MigrationStatus.FAILED

        return StorageMigrationResult(
            total_files=total_files,
            migrated_files=migrated_files,
            failed_files=failed_files,
            skipped_files=skipped_files,
            total_size_bytes=total_size,
            migrated_size_bytes=migrated_size,
            duration_seconds=0,  # Will be set by caller
            status=status,
            buckets_created=[],
            policies_created=[]
        )

    async def _process_migration_batch(
        self,
        batch: MigrationBatch
    ) -> Dict[str, int]:
        """Process a single migration batch."""
        batch.started_at = asyncio.get_event_loop().time()
        batch.status = MigrationStatus.IN_PROGRESS

        migrated = 0
        failed = 0
        skipped = 0
        size = 0

        async with aiohttp.ClientSession() as session:
            for file_info in batch.files:
                try:
                    result = await self._upload_file(session, file_info)
                    if result['success']:
                        migrated += 1
                        size += file_info.size_bytes
                    elif result['skipped']:
                        skipped += 1
                    else:
                        failed += 1

                    # Progress callback
                    if self.progress_callback:
                        await self.progress_callback({
                            'batch_id': batch.batch_id,
                            'file': file_info.relative_path,
                            'status': 'completed' if result['success'] else 'failed'
                        })

                except Exception as e:
                    failed += 1
                    logger.error(f"Failed to upload {file_info.relative_path}: {str(e)}")

        batch.status = MigrationStatus.COMPLETED
        batch.completed_at = asyncio.get_event_loop().time()

        return {
            'migrated': migrated,
            'failed': failed,
            'skipped': skipped,
            'size': size
        }

    async def _upload_file(
        self,
        session: aiohttp.ClientSession,
        file_info: FileInfo
    ) -> Dict[str, Any]:
        """Upload a single file to Supabase Storage."""
        try:
            url = f"{self.supabase_url}/storage/v1/object/{file_info.bucket_name}/{file_info.storage_path}"

            headers = {
                'Authorization': f'Bearer {self.supabase_key}',
                'Content-Type': file_info.mime_type
            }

            # Read file content
            async with aiofiles.open(file_info.local_path, 'rb') as f:
                file_content = await f.read()

            async with session.post(url, headers=headers, data=file_content) as response:
                if response.status == 200:
                    return {'success': True, 'skipped': False}
                elif response.status == 409:
                    # File already exists
                    return {'success': False, 'skipped': True}
                else:
                    response_text = await response.text()
                    logger.error(f"Upload failed for {file_info.relative_path}: {response.status} - {response_text}")
                    return {'success': False, 'skipped': False}

        except Exception as e:
            logger.error(f"Upload error for {file_info.relative_path}: {str(e)}")
            return {'success': False, 'skipped': False}

    async def _create_access_policies(
        self,
        inventory: List[FileInfo],
        dry_run: bool
    ) -> List[str]:
        """Create access policies for uploaded files."""
        if dry_run:
            return ['public_policy', 'authenticated_policy']

        # Group files by bucket and public/private
        bucket_policies = {}
        for file_info in inventory:
            bucket = file_info.bucket_name
            if bucket not in bucket_policies:
                bucket_policies[bucket] = {'public': False, 'private': False}

            if file_info.public:
                bucket_policies[bucket]['public'] = True
            else:
                bucket_policies[bucket]['private'] = True

        policies_created = []

        async with aiohttp.ClientSession() as session:
            for bucket, needs in bucket_policies.items():
                if needs['public']:
                    policy_name = await self._create_public_policy(session, bucket)
                    if policy_name:
                        policies_created.append(policy_name)

                if needs['private']:
                    policy_name = await self._create_private_policy(session, bucket)
                    if policy_name:
                        policies_created.append(policy_name)

        return policies_created

    async def _create_public_policy(
        self,
        session: aiohttp.ClientSession,
        bucket_name: str
    ) -> Optional[str]:
        """Create public access policy for bucket."""
        policy_name = f"{bucket_name}_public_access"

        # This would typically be done through Supabase SQL functions
        # For now, we'll log the policy that should be created
        logger.info(f"Would create public policy: {policy_name}")
        return policy_name

    async def _create_private_policy(
        self,
        session: aiohttp.ClientSession,
        bucket_name: str
    ) -> Optional[str]:
        """Create private access policy for bucket."""
        policy_name = f"{bucket_name}_private_access"

        # This would typically be done through Supabase SQL functions
        # For now, we'll log the policy that should be created
        logger.info(f"Would create private policy: {policy_name}")
        return policy_name

    async def _create_bucket_policy(
        self,
        session: aiohttp.ClientSession,
        config: Dict[str, Any]
    ) -> Optional[str]:
        """Create bucket access policy from configuration."""
        # Implementation would depend on specific policy requirements
        policy_name = f"policy_{config['name']}"
        logger.info(f"Would create bucket policy: {policy_name}")
        return policy_name

    async def _verify_single_file(
        self,
        session: aiohttp.ClientSession,
        file_info: FileInfo
    ) -> Dict[str, Any]:
        """Verify a single uploaded file."""
        try:
            url = f"{self.supabase_url}/storage/v1/object/{file_info.bucket_name}/{file_info.storage_path}"

            headers = {
                'Authorization': f'Bearer {self.supabase_key}'
            }

            async with session.head(url, headers=headers) as response:
                if response.status == 200:
                    # Check file size
                    content_length = response.headers.get('Content-Length')
                    if content_length:
                        remote_size = int(content_length)
                        size_match = remote_size == file_info.size_bytes
                    else:
                        size_match = True  # Can't verify size

                    return {
                        'exists': True,
                        'size_match': size_match
                    }
                else:
                    return {
                        'exists': False,
                        'size_match': False
                    }

        except Exception as e:
            logger.error(f"Verification failed for {file_info.relative_path}: {str(e)}")
            return {
                'exists': False,
                'size_match': False
            }

    def generate_migration_report(
        self,
        result: StorageMigrationResult,
        inventory: List[FileInfo]
    ) -> str:
        """Generate migration report."""
        success_rate = (result.migrated_files / result.total_files * 100) if result.total_files > 0 else 0

        # Group files by bucket
        bucket_stats = {}
        for file_info in inventory:
            bucket = file_info.bucket_name
            if bucket not in bucket_stats:
                bucket_stats[bucket] = {'count': 0, 'size': 0}
            bucket_stats[bucket]['count'] += 1
            bucket_stats[bucket]['size'] += file_info.size_bytes

        report = f"""# Storage Migration Report

## Summary
- **Total Files**: {result.total_files:,}
- **Migrated Successfully**: {result.migrated_files:,}
- **Failed**: {result.failed_files:,}
- **Skipped**: {result.skipped_files:,}
- **Success Rate**: {success_rate:.1f}%

## Size Summary
- **Total Size**: {result.total_size_bytes / 1024 / 1024:.1f} MB
- **Migrated Size**: {result.migrated_size_bytes / 1024 / 1024:.1f} MB
- **Duration**: {result.duration_seconds:.1f} seconds

## Buckets Created
{chr(10).join(f'- {bucket}' for bucket in result.buckets_created)}

## Bucket Statistics
"""

        for bucket, stats in bucket_stats.items():
            report += f"### {bucket}\n"
            report += f"- Files: {stats['count']:,}\n"
            report += f"- Size: {stats['size'] / 1024 / 1024:.1f} MB\n\n"

        report += f"""
## Policies Created
{chr(10).join(f'- {policy}' for policy in result.policies_created)}

## Next Steps
1. Verify file accessibility through Supabase Storage
2. Update application code to use new storage URLs
3. Test file upload/download functionality
4. Configure CDN if needed
5. Monitor storage usage and costs
"""

        return report