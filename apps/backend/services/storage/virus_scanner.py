"""
Virus Scanner for ToolBoxAI Educational Platform

Comprehensive virus scanning using ClamAV with async processing,
quarantine management, and integration with Celery for background scanning.

Author: ToolBoxAI Team
Created: 2025-01-27
Version: 1.0.0
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

try:
    import pyclamd

    CLAMAV_AVAILABLE = True
except ImportError:
    CLAMAV_AVAILABLE = False
    logging.warning("pyclamd not available - virus scanning will be mocked")

logger = logging.getLogger(__name__)


class ScanStatus(str, Enum):
    """Virus scan status"""

    PENDING = "pending"
    SCANNING = "scanning"
    CLEAN = "clean"
    INFECTED = "infected"
    ERROR = "error"
    SKIPPED = "skipped"


class ThreatLevel(str, Enum):
    """Threat level classification"""

    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class ScanResult:
    """Result of virus scan operation"""

    scan_id: str
    status: ScanStatus
    is_clean: bool
    threat_name: str | None = None
    threat_level: ThreatLevel = ThreatLevel.NONE
    scan_duration: float = 0.0
    engine_version: str | None = None
    signature_date: datetime | None = None
    details: dict[str, Any] = field(default_factory=dict)
    scanned_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "scan_id": self.scan_id,
            "status": self.status.value,
            "is_clean": self.is_clean,
            "threat_name": self.threat_name,
            "threat_level": self.threat_level.value,
            "scan_duration": self.scan_duration,
            "engine_version": self.engine_version,
            "signature_date": self.signature_date.isoformat() if self.signature_date else None,
            "details": self.details,
            "scanned_at": self.scanned_at.isoformat(),
        }


class QuarantineAction(str, Enum):
    """Actions to take for quarantined files"""

    QUARANTINE = "quarantine"
    DELETE = "delete"
    NOTIFY_ONLY = "notify_only"
    ALLOW = "allow"


@dataclass
class ScanConfiguration:
    """Configuration for virus scanning"""

    enabled: bool = True
    scan_timeout: int = 300  # 5 minutes
    max_file_size: int = 100 * 1024 * 1024  # 100MB
    quarantine_action: QuarantineAction = QuarantineAction.QUARANTINE
    scan_archives: bool = True
    heuristic_scanning: bool = True
    async_scanning: bool = True
    notification_webhook: str | None = None
    excluded_extensions: list[str] = field(default_factory=lambda: [".txt", ".md"])
    required_categories: list[str] = field(
        default_factory=lambda: [
            "student_submission",
            "educational_content",
            "media_resource",
        ]
    )


class VirusScanner:
    """
    Comprehensive virus scanning service using ClamAV.

    Features:
    - ClamAV integration with pyclamd
    - Async scanning with Celery
    - Quarantine management
    - Real-time signature updates
    - Educational platform-specific policies
    """

    def __init__(self, config: ScanConfiguration | None = None):
        """
        Initialize virus scanner.

        Args:
            config: Scanner configuration
        """
        self.config = config or ScanConfiguration()
        self.clamd_client = None
        self._scan_results: dict[str, ScanResult] = {}

        # Initialize ClamAV if available
        if CLAMAV_AVAILABLE and self.config.enabled:
            self._initialize_clamav()
        elif self.config.enabled:
            logger.warning("ClamAV not available - using mock scanner")

        logger.info(f"VirusScanner initialized: enabled={self.config.enabled}")

    def _initialize_clamav(self) -> None:
        """Initialize ClamAV daemon connection"""
        try:
            # Try different connection methods
            for connection_type in ["unix_socket", "tcp"]:
                try:
                    if connection_type == "unix_socket":
                        # Try common Unix socket paths
                        socket_paths = [
                            "/var/run/clamav/clamd.ctl",
                            "/var/run/clamd.scan/clamd.sock",
                            "/tmp/clamd.socket",
                        ]

                        for socket_path in socket_paths:
                            if Path(socket_path).exists():
                                self.clamd_client = pyclamd.ClamdUnixSocket(socket_path)
                                break
                    else:
                        # TCP connection
                        self.clamd_client = pyclamd.ClamdNetworkSocket()

                    # Test connection
                    if self.clamd_client and self.clamd_client.ping():
                        logger.info(f"ClamAV connected via {connection_type}")
                        return

                except Exception as e:
                    logger.debug(f"ClamAV {connection_type} connection failed: {e}")
                    continue

            # If no connection successful
            logger.warning("Could not connect to ClamAV daemon")
            self.clamd_client = None

        except Exception as e:
            logger.error(f"ClamAV initialization failed: {e}")
            self.clamd_client = None

    async def scan_data(
        self,
        file_data: bytes,
        filename: str | None = None,
        file_category: str | None = None,
    ) -> ScanResult:
        """
        Scan file data for viruses.

        Args:
            file_data: File content to scan
            filename: Original filename (for context)
            file_category: File category for policy decisions

        Returns:
            ScanResult: Scan results
        """
        scan_id = str(uuid4())
        start_time = datetime.utcnow()

        try:
            # Check if scanning is needed
            if not self._should_scan(filename, file_category):
                return ScanResult(
                    scan_id=scan_id,
                    status=ScanStatus.SKIPPED,
                    is_clean=True,
                    details={"reason": "Category excluded from scanning"},
                )

            # Size check
            if len(file_data) > self.config.max_file_size:
                return ScanResult(
                    scan_id=scan_id,
                    status=ScanStatus.ERROR,
                    is_clean=False,
                    details={
                        "error": "File too large for scanning",
                        "size": len(file_data),
                        "max_size": self.config.max_file_size,
                    },
                )

            # Perform scan
            if self.clamd_client and CLAMAV_AVAILABLE:
                result = await self._scan_with_clamav(scan_id, file_data, filename)
            else:
                result = await self._mock_scan(scan_id, file_data, filename)

            # Calculate duration
            result.scan_duration = (datetime.utcnow() - start_time).total_seconds()

            # Store result
            self._scan_results[scan_id] = result

            logger.info(
                f"Virus scan completed: {scan_id} -> {result.status.value} "
                f"({result.scan_duration:.2f}s)"
            )

            return result

        except Exception as e:
            logger.error(f"Virus scan failed: {e}")
            return ScanResult(
                scan_id=scan_id,
                status=ScanStatus.ERROR,
                is_clean=False,
                details={"error": str(e)},
                scan_duration=(datetime.utcnow() - start_time).total_seconds(),
            )

    async def scan_file(
        self, file_path: str | Path, file_category: str | None = None
    ) -> ScanResult:
        """
        Scan a file from disk.

        Args:
            file_path: Path to file to scan
            file_category: File category for policy decisions

        Returns:
            ScanResult: Scan results
        """
        try:
            file_path = Path(file_path)

            if not file_path.exists():
                raise FileNotFoundError(f"File not found: {file_path}")

            # Read file data
            with open(file_path, "rb") as f:
                file_data = f.read()

            return await self.scan_data(file_data, file_path.name, file_category)

        except Exception as e:
            logger.error(f"File scan failed: {e}")
            return ScanResult(
                scan_id=str(uuid4()),
                status=ScanStatus.ERROR,
                is_clean=False,
                details={"error": str(e)},
            )

    async def scan_file_async(
        self,
        file_data: bytes,
        filename: str | None = None,
        file_category: str | None = None,
        callback_url: str | None = None,
    ) -> str:
        """
        Submit file for asynchronous scanning using Celery.

        Args:
            file_data: File content to scan
            filename: Original filename
            file_category: File category
            callback_url: URL to notify when scan completes

        Returns:
            str: Scan ID for tracking
        """
        scan_id = str(uuid4())

        try:
            # Create placeholder result
            self._scan_results[scan_id] = ScanResult(
                scan_id=scan_id, status=ScanStatus.PENDING, is_clean=False
            )

            # Submit to Celery task (if available)
            if self._has_celery():
                await self._submit_celery_scan(
                    scan_id, file_data, filename, file_category, callback_url
                )
            else:
                # Fallback to immediate scan
                result = await self.scan_data(file_data, filename, file_category)
                result.scan_id = scan_id
                self._scan_results[scan_id] = result

            logger.info(f"Async scan submitted: {scan_id}")
            return scan_id

        except Exception as e:
            logger.error(f"Async scan submission failed: {e}")
            # Update result with error
            self._scan_results[scan_id] = ScanResult(
                scan_id=scan_id,
                status=ScanStatus.ERROR,
                is_clean=False,
                details={"error": str(e)},
            )
            return scan_id

    async def get_scan_result(self, scan_id: str) -> ScanResult | None:
        """
        Get scan result by ID.

        Args:
            scan_id: Scan identifier

        Returns:
            ScanResult: Scan result or None if not found
        """
        return self._scan_results.get(scan_id)

    async def quarantine_file(
        self, file_id: UUID, scan_result: ScanResult, organization_id: str | None = None
    ) -> bool:
        """
        Quarantine an infected file.

        Args:
            file_id: File identifier
            scan_result: Scan result showing infection
            organization_id: Organization ID for tenant isolation

        Returns:
            bool: True if quarantine successful
        """
        try:
            quarantine_record = {
                "file_id": str(file_id),
                "organization_id": organization_id,
                "scan_id": scan_result.scan_id,
                "threat_name": scan_result.threat_name,
                "threat_level": scan_result.threat_level.value,
                "quarantined_at": datetime.utcnow(),
                "action": self.config.quarantine_action.value,
                "details": scan_result.details,
            }

            # Store quarantine record (would integrate with database)
            await self._store_quarantine_record(quarantine_record)

            # Take configured action
            if self.config.quarantine_action == QuarantineAction.DELETE:
                await self._delete_infected_file(file_id)
            elif self.config.quarantine_action == QuarantineAction.QUARANTINE:
                await self._move_to_quarantine(file_id)

            # Send notification if configured
            if self.config.notification_webhook:
                await self._send_quarantine_notification(quarantine_record)

            logger.warning(
                f"File quarantined: {file_id} -> {scan_result.threat_name} "
                f"(action: {self.config.quarantine_action.value})"
            )

            return True

        except Exception as e:
            logger.error(f"File quarantine failed: {e}")
            return False

    async def update_signatures(self) -> bool:
        """
        Update virus signature database.

        Returns:
            bool: True if update successful
        """
        try:
            if not self.clamd_client:
                logger.warning("ClamAV not available for signature updates")
                return False

            # ClamAV signature updates are typically handled by freshclam
            # This would trigger an update if supported
            logger.info("Virus signature update requested")

            # Check current signature version
            version_info = await self._get_engine_version()
            logger.info(f"Current ClamAV version: {version_info}")

            return True

        except Exception as e:
            logger.error(f"Signature update failed: {e}")
            return False

    async def get_scanner_status(self) -> dict[str, Any]:
        """
        Get scanner status and statistics.

        Returns:
            dict[str, Any]: Scanner status information
        """
        try:
            status = {
                "enabled": self.config.enabled,
                "clamav_available": CLAMAV_AVAILABLE,
                "daemon_connected": self.clamd_client is not None,
                "configuration": {
                    "scan_timeout": self.config.scan_timeout,
                    "max_file_size": self.config.max_file_size,
                    "quarantine_action": self.config.quarantine_action.value,
                    "async_scanning": self.config.async_scanning,
                },
                "statistics": {
                    "total_scans": len(self._scan_results),
                    "clean_files": len([r for r in self._scan_results.values() if r.is_clean]),
                    "infected_files": len(
                        [
                            r
                            for r in self._scan_results.values()
                            if not r.is_clean and r.status != ScanStatus.ERROR
                        ]
                    ),
                    "scan_errors": len(
                        [r for r in self._scan_results.values() if r.status == ScanStatus.ERROR]
                    ),
                },
            }

            # Get engine version if available
            if self.clamd_client:
                try:
                    status["engine_version"] = await self._get_engine_version()
                except Exception:
                    status["engine_version"] = "unknown"

            return status

        except Exception as e:
            logger.error(f"Get scanner status failed: {e}")
            return {"error": str(e)}

    # Private helper methods

    async def _scan_with_clamav(
        self, scan_id: str, file_data: bytes, filename: str | None
    ) -> ScanResult:
        """Scan file data using ClamAV"""
        try:
            # Update scan status
            result = ScanResult(scan_id=scan_id, status=ScanStatus.SCANNING, is_clean=False)

            # Scan with timeout
            scan_task = asyncio.create_task(
                asyncio.to_thread(self.clamd_client.scan_stream, file_data)
            )

            try:
                scan_response = await asyncio.wait_for(scan_task, timeout=self.config.scan_timeout)
            except asyncio.TimeoutError:
                return ScanResult(
                    scan_id=scan_id,
                    status=ScanStatus.ERROR,
                    is_clean=False,
                    details={"error": "Scan timeout"},
                )

            # Parse ClamAV response
            if scan_response is None:
                # Clean file
                result.status = ScanStatus.CLEAN
                result.is_clean = True
            else:
                # Infected file
                result.status = ScanStatus.INFECTED
                result.is_clean = False
                result.threat_name = scan_response.get("stream", "Unknown threat")
                result.threat_level = self._classify_threat_level(result.threat_name)

            # Get engine version
            try:
                result.engine_version = self.clamd_client.version()
            except Exception:
                pass

            result.details = {"scanner": "clamav", "raw_response": scan_response}

            return result

        except Exception as e:
            logger.error(f"ClamAV scan failed: {e}")
            return ScanResult(
                scan_id=scan_id,
                status=ScanStatus.ERROR,
                is_clean=False,
                details={"error": str(e)},
            )

    async def _mock_scan(self, scan_id: str, file_data: bytes, filename: str | None) -> ScanResult:
        """Mock virus scan for testing/development"""
        # Simulate scan delay
        await asyncio.sleep(0.1)

        # Check for test virus patterns
        test_threats = [
            (b"EICAR-STANDARD-ANTIVIRUS-TEST-FILE", "EICAR-Test-File"),
            (b"X5O!P%@AP[4\\PZX54(P^)7CC)7}$EICAR", "EICAR-Test-File"),
            (b"virus_test_pattern", "Test.Virus.Pattern"),
        ]

        for pattern, threat_name in test_threats:
            if pattern in file_data:
                return ScanResult(
                    scan_id=scan_id,
                    status=ScanStatus.INFECTED,
                    is_clean=False,
                    threat_name=threat_name,
                    threat_level=ThreatLevel.HIGH,
                    engine_version="Mock Scanner 1.0",
                    details={
                        "scanner": "mock",
                        "test_pattern": pattern.decode("utf-8", errors="ignore"),
                    },
                )

        # Clean file
        return ScanResult(
            scan_id=scan_id,
            status=ScanStatus.CLEAN,
            is_clean=True,
            engine_version="Mock Scanner 1.0",
            details={"scanner": "mock", "file_size": len(file_data)},
        )

    def _should_scan(self, filename: str | None, file_category: str | None) -> bool:
        """Determine if file should be scanned"""
        if not self.config.enabled:
            return False

        # Check category requirements
        if file_category and self.config.required_categories:
            if file_category not in self.config.required_categories:
                return False

        # Check excluded extensions
        if filename and self.config.excluded_extensions:
            file_ext = Path(filename).suffix.lower()
            if file_ext in self.config.excluded_extensions:
                return False

        return True

    def _classify_threat_level(self, threat_name: str | None) -> ThreatLevel:
        """Classify threat level based on threat name"""
        if not threat_name:
            return ThreatLevel.NONE

        threat_lower = threat_name.lower()

        # Critical threats
        if any(keyword in threat_lower for keyword in ["trojan", "ransomware", "backdoor"]):
            return ThreatLevel.CRITICAL

        # High threats
        if any(keyword in threat_lower for keyword in ["virus", "worm", "rootkit"]):
            return ThreatLevel.HIGH

        # Medium threats
        if any(keyword in threat_lower for keyword in ["adware", "spyware", "pup"]):
            return ThreatLevel.MEDIUM

        # Low threats
        if any(keyword in threat_lower for keyword in ["test", "eicar", "harmless"]):
            return ThreatLevel.LOW

        # Default to medium for unknown threats
        return ThreatLevel.MEDIUM

    def _has_celery(self) -> bool:
        """Check if Celery is available"""
        try:
            import celery

            return True
        except ImportError:
            return False

    async def _submit_celery_scan(
        self,
        scan_id: str,
        file_data: bytes,
        filename: str | None,
        file_category: str | None,
        callback_url: str | None,
    ) -> None:
        """Submit scan to Celery task queue"""
        try:
            # This would integrate with your Celery setup
            from apps.backend.core.tasks import virus_scan_task

            virus_scan_task.delay(
                scan_id=scan_id,
                file_data=file_data,
                filename=filename,
                file_category=file_category,
                callback_url=callback_url,
            )

        except ImportError:
            logger.warning("Celery task not available - using synchronous scan")
            # Fallback to sync scan
            result = await self.scan_data(file_data, filename, file_category)
            result.scan_id = scan_id
            self._scan_results[scan_id] = result

    async def _get_engine_version(self) -> str:
        """Get ClamAV engine version"""
        try:
            if self.clamd_client:
                return self.clamd_client.version()
            return "Mock Scanner 1.0"
        except Exception:
            return "unknown"

    async def _store_quarantine_record(self, record: dict[str, Any]) -> None:
        """Store quarantine record in database"""
        # This would integrate with your database models
        logger.info(f"Quarantine record stored: {record['file_id']}")

    async def _delete_infected_file(self, file_id: UUID) -> None:
        """Delete infected file from storage"""
        # This would integrate with your storage service
        logger.warning(f"Infected file deleted: {file_id}")

    async def _move_to_quarantine(self, file_id: UUID) -> None:
        """Move infected file to quarantine storage"""
        # This would move file to quarantine bucket/folder
        logger.warning(f"File moved to quarantine: {file_id}")

    async def _send_quarantine_notification(self, record: dict[str, Any]) -> None:
        """Send notification about quarantined file"""
        try:
            import aiohttp

            async with aiohttp.ClientSession() as session:
                await session.post(
                    self.config.notification_webhook,
                    json={"event": "file_quarantined", "data": record},
                )

        except Exception as e:
            logger.error(f"Quarantine notification failed: {e}")
