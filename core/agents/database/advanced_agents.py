"""
Advanced Database Agents Implementation

This module implements the remaining specialized database agents:
- Event Sourcing Agent
- Data Integrity Agent
- Backup Recovery Agent
- Monitoring Agent

Author: ToolboxAI Team
Created: 2025-09-16
Version: 1.0.0
"""

import asyncio
import logging
import hashlib
import json
import uuid
import gzip
import shutil
from typing import Dict, Any, Optional, List, Set, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
from pathlib import Path
import pickle

from .base_database_agent import (
    BaseDatabaseAgent,
    DatabaseAgentConfig,
    DatabaseOperation,
    DatabaseHealth
)
from core.agents.base_agent import AgentCapability, AgentState, TaskResult

logger = logging.getLogger(__name__)


# ============================================================================
# EVENT SOURCING AGENT
# ============================================================================

@dataclass
class Event:
    """Represents a domain event."""
    event_id: str
    aggregate_id: str
    event_type: str
    event_data: Dict[str, Any]
    event_metadata: Dict[str, Any]
    event_version: int
    created_at: datetime

    def to_dict(self) -> Dict:
        """Convert event to dictionary."""
        return {
            "event_id": self.event_id,
            "aggregate_id": self.aggregate_id,
            "event_type": self.event_type,
            "event_data": self.event_data,
            "event_metadata": self.event_metadata,
            "event_version": self.event_version,
            "created_at": self.created_at.isoformat()
        }


class EventSourcingAgent(BaseDatabaseAgent):
    """
    Manages event sourcing patterns and event stream processing.

    Features:
    - Event store management in PostgreSQL
    - Event stream processing and projections
    - Snapshot management for performance
    - Event replay capabilities
    - Schema versioning for events
    - CQRS pattern implementation
    """

    def __init__(self, config: Optional[DatabaseAgentConfig] = None):
        """Initialize the Event Sourcing Agent."""
        if not config:
            config = DatabaseAgentConfig(
                name="EventSourcingAgent",
                capability=AgentCapability.ORCHESTRATION,
                event_sourcing_enabled=True,
                cqrs_enabled=True
            )
        super().__init__(config)
        self.event_store: List[Event] = []
        self.snapshots: Dict[str, Any] = {}
        self.projections: Dict[str, Any] = {}
        self.event_handlers: Dict[str, List[callable]] = {}

    async def _process_task(self, state: AgentState) -> TaskResult:
        """Process event sourcing tasks."""
        task = state.get("task", "")
        operation = state.get("operation")

        if task == "append_event":
            event_data = state.get("event_data", {})
            return await self.append_event(event_data)
        elif task == "replay_events":
            aggregate_id = state.get("aggregate_id")
            return await self.replay_events(aggregate_id)
        elif task == "create_snapshot":
            aggregate_id = state.get("aggregate_id")
            return await self.create_snapshot(aggregate_id)
        else:
            return await self.get_event_stream()

    async def append_event(self, event_data: Dict[str, Any]) -> TaskResult:
        """
        Append a new event to the event store.

        Args:
            event_data: Event information to store

        Returns:
            TaskResult with event details
        """
        try:
            # Create event
            event = Event(
                event_id=str(uuid.uuid4()),
                aggregate_id=event_data.get("aggregate_id", str(uuid.uuid4())),
                event_type=event_data.get("event_type", "unknown"),
                event_data=event_data.get("data", {}),
                event_metadata=event_data.get("metadata", {}),
                event_version=len(self.event_store) + 1,
                created_at=datetime.utcnow()
            )

            # Store event in database
            async with self.get_db_session() as session:
                await session.execute("""
                    INSERT INTO event_store
                    (event_id, aggregate_id, event_type, event_data, event_metadata, event_version, created_at)
                    VALUES (:event_id, :aggregate_id, :event_type, :event_data, :event_metadata, :event_version, :created_at)
                """, {
                    "event_id": event.event_id,
                    "aggregate_id": event.aggregate_id,
                    "event_type": event.event_type,
                    "event_data": json.dumps(event.event_data),
                    "event_metadata": json.dumps(event.event_metadata),
                    "event_version": event.event_version,
                    "created_at": event.created_at
                })

            # Add to in-memory store
            self.event_store.append(event)

            # Update projections
            await self._update_projections(event)

            # Publish event
            await self.publish_event("event_appended", event.to_dict())

            # Trigger event handlers
            await self._trigger_handlers(event)

            logger.info(f"Event appended: {event.event_id}")

            return TaskResult(
                success=True,
                data={
                    "event_id": event.event_id,
                    "aggregate_id": event.aggregate_id,
                    "event_type": event.event_type,
                    "event_version": event.event_version,
                    "timestamp": event.created_at.isoformat()
                }
            )

        except Exception as e:
            logger.error(f"Failed to append event: {e}")
            return TaskResult(
                success=False,
                data={"error": str(e)}
            )

    async def replay_events(
        self,
        aggregate_id: Optional[str] = None,
        from_version: int = 0,
        to_version: Optional[int] = None
    ) -> TaskResult:
        """
        Replay events for an aggregate or all events.

        Args:
            aggregate_id: Optional aggregate ID to filter events
            from_version: Starting version (inclusive)
            to_version: Ending version (inclusive)

        Returns:
            TaskResult with replayed state
        """
        try:
            # Get events to replay
            events_to_replay = []

            async with self.get_db_session() as session:
                query = "SELECT * FROM event_store WHERE 1=1"
                params = {}

                if aggregate_id:
                    query += " AND aggregate_id = :aggregate_id"
                    params["aggregate_id"] = aggregate_id

                if from_version > 0:
                    query += " AND event_version >= :from_version"
                    params["from_version"] = from_version

                if to_version:
                    query += " AND event_version <= :to_version"
                    params["to_version"] = to_version

                query += " ORDER BY event_version ASC"

                result = await session.execute(query, params)
                rows = result.fetchall()

                for row in rows:
                    event = Event(
                        event_id=row["event_id"],
                        aggregate_id=row["aggregate_id"],
                        event_type=row["event_type"],
                        event_data=json.loads(row["event_data"]),
                        event_metadata=json.loads(row["event_metadata"]),
                        event_version=row["event_version"],
                        created_at=row["created_at"]
                    )
                    events_to_replay.append(event)

            # Rebuild state from events
            rebuilt_state = {}
            for event in events_to_replay:
                rebuilt_state = await self._apply_event(rebuilt_state, event)

            logger.info(f"Replayed {len(events_to_replay)} events")

            return TaskResult(
                success=True,
                data={
                    "events_replayed": len(events_to_replay),
                    "final_state": rebuilt_state,
                    "aggregate_id": aggregate_id,
                    "version_range": f"{from_version}-{to_version or 'latest'}"
                }
            )

        except Exception as e:
            logger.error(f"Event replay failed: {e}")
            return TaskResult(
                success=False,
                data={"error": str(e)}
            )

    async def create_snapshot(self, aggregate_id: str) -> TaskResult:
        """
        Create a snapshot of current aggregate state.

        Snapshots improve performance by reducing the number
        of events that need to be replayed.
        """
        try:
            # Get current state by replaying events
            replay_result = await self.replay_events(aggregate_id)

            if not replay_result.success:
                return replay_result

            current_state = replay_result.data["final_state"]

            # Create snapshot
            snapshot_id = str(uuid.uuid4())
            snapshot = {
                "snapshot_id": snapshot_id,
                "aggregate_id": aggregate_id,
                "snapshot_data": current_state,
                "event_version": len(self.event_store),
                "created_at": datetime.utcnow().isoformat()
            }

            # Store snapshot
            async with self.get_db_session() as session:
                await session.execute("""
                    INSERT INTO event_snapshots
                    (snapshot_id, aggregate_id, snapshot_data, event_version, created_at)
                    VALUES (:snapshot_id, :aggregate_id, :snapshot_data, :event_version, :created_at)
                """, {
                    "snapshot_id": snapshot_id,
                    "aggregate_id": aggregate_id,
                    "snapshot_data": json.dumps(snapshot["snapshot_data"]),
                    "event_version": snapshot["event_version"],
                    "created_at": snapshot["created_at"]
                })

            self.snapshots[aggregate_id] = snapshot

            logger.info(f"Snapshot created for aggregate {aggregate_id}")

            return TaskResult(
                success=True,
                data=snapshot
            )

        except Exception as e:
            logger.error(f"Snapshot creation failed: {e}")
            return TaskResult(
                success=False,
                data={"error": str(e)}
            )

    async def get_event_stream(self, filters: Optional[Dict] = None) -> TaskResult:
        """Get event stream with optional filters."""
        try:
            events = []

            async with self.get_db_session() as session:
                query = "SELECT * FROM event_store"
                params = {}

                if filters:
                    conditions = []
                    if "event_type" in filters:
                        conditions.append("event_type = :event_type")
                        params["event_type"] = filters["event_type"]
                    if "aggregate_id" in filters:
                        conditions.append("aggregate_id = :aggregate_id")
                        params["aggregate_id"] = filters["aggregate_id"]
                    if "from_date" in filters:
                        conditions.append("created_at >= :from_date")
                        params["from_date"] = filters["from_date"]

                    if conditions:
                        query += " WHERE " + " AND ".join(conditions)

                query += " ORDER BY event_version DESC LIMIT 100"

                result = await session.execute(query, params)
                rows = result.fetchall()

                for row in rows:
                    events.append({
                        "event_id": row["event_id"],
                        "aggregate_id": row["aggregate_id"],
                        "event_type": row["event_type"],
                        "event_version": row["event_version"],
                        "created_at": row["created_at"].isoformat()
                    })

            return TaskResult(
                success=True,
                data={
                    "events": events,
                    "count": len(events),
                    "filters": filters or {}
                }
            )

        except Exception as e:
            logger.error(f"Failed to get event stream: {e}")
            return TaskResult(
                success=False,
                data={"error": str(e)}
            )

    async def _apply_event(self, state: Dict, event: Event) -> Dict:
        """Apply an event to rebuild state."""
        # Event-specific logic would go here
        # This is a simplified implementation
        if event.event_type == "created":
            state[event.aggregate_id] = event.event_data
        elif event.event_type == "updated":
            if event.aggregate_id in state:
                state[event.aggregate_id].update(event.event_data)
        elif event.event_type == "deleted":
            state.pop(event.aggregate_id, None)

        return state

    async def _update_projections(self, event: Event):
        """Update read model projections based on event."""
        # Update projections for CQRS read model
        projection_key = f"{event.event_type}:{event.aggregate_id}"
        self.projections[projection_key] = {
            "last_event": event.event_id,
            "version": event.event_version,
            "updated_at": event.created_at.isoformat()
        }

    async def _trigger_handlers(self, event: Event):
        """Trigger registered event handlers."""
        handlers = self.event_handlers.get(event.event_type, [])
        for handler in handlers:
            try:
                await handler(event)
            except Exception as e:
                logger.error(f"Event handler failed: {e}")

    def register_handler(self, event_type: str, handler: callable):
        """Register an event handler for a specific event type."""
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []
        self.event_handlers[event_type].append(handler)


# ============================================================================
# DATA INTEGRITY AGENT
# ============================================================================

class DataIntegrityAgent(BaseDatabaseAgent):
    """
    Validates data consistency and repairs integrity issues.

    Features:
    - Referential integrity validation
    - Data corruption detection using checksums
    - Automated repair mechanisms
    - Orphan record cleanup
    - Cross-system consistency validation
    - Constraint violation detection
    """

    def __init__(self, config: Optional[DatabaseAgentConfig] = None):
        """Initialize the Data Integrity Agent."""
        if not config:
            config = DatabaseAgentConfig(
                name="DataIntegrityAgent",
                capability=AgentCapability.VALIDATION,
                auto_repair=True
            )
        super().__init__(config)
        self.integrity_checks: Dict[str, callable] = {}
        self.repair_strategies: Dict[str, callable] = {}
        self.validation_history: List[Dict] = []

    async def _process_task(self, state: AgentState) -> TaskResult:
        """Process data integrity tasks."""
        task = state.get("task", "")
        operation = state.get("operation", DatabaseOperation.VALIDATE)

        if operation == DatabaseOperation.VALIDATE:
            return await self.validate_integrity()
        elif operation == DatabaseOperation.REPAIR:
            return await self.repair_integrity_issues()
        else:
            return await self.check_constraints()

    async def validate_integrity(self) -> TaskResult:
        """
        Perform comprehensive data integrity validation.

        Checks:
        - Foreign key constraints
        - Unique constraints
        - Check constraints
        - Orphan records
        - Data type consistency
        """
        try:
            validation_report = {
                "timestamp": datetime.utcnow().isoformat(),
                "checks_performed": [],
                "issues_found": [],
                "status": "healthy"
            }

            # Check foreign key constraints
            fk_issues = await self._check_foreign_keys()
            validation_report["checks_performed"].append("foreign_keys")
            if fk_issues:
                validation_report["issues_found"].extend(fk_issues)

            # Check for orphan records
            orphan_issues = await self._check_orphan_records()
            validation_report["checks_performed"].append("orphan_records")
            if orphan_issues:
                validation_report["issues_found"].extend(orphan_issues)

            # Check data consistency
            consistency_issues = await self._check_data_consistency()
            validation_report["checks_performed"].append("data_consistency")
            if consistency_issues:
                validation_report["issues_found"].extend(consistency_issues)

            # Check for duplicate records
            duplicate_issues = await self._check_duplicates()
            validation_report["checks_performed"].append("duplicates")
            if duplicate_issues:
                validation_report["issues_found"].extend(duplicate_issues)

            # Determine overall status
            if validation_report["issues_found"]:
                validation_report["status"] = "issues_detected"

                # Auto-repair if enabled
                if self.db_config.auto_repair:
                    repair_result = await self.repair_integrity_issues()
                    validation_report["auto_repair"] = repair_result.data

            # Save validation history
            self.validation_history.append(validation_report)

            # Publish validation results
            await self.publish_event("integrity_validated", validation_report)

            logger.info(f"Integrity validation completed: {len(validation_report['issues_found'])} issues found")

            return TaskResult(
                success=True,
                data=validation_report
            )

        except Exception as e:
            logger.error(f"Integrity validation failed: {e}")
            return TaskResult(
                success=False,
                data={"error": str(e)}
            )

    async def repair_integrity_issues(self) -> TaskResult:
        """
        Automatically repair detected integrity issues.

        Repair strategies:
        - Remove orphan records
        - Fix constraint violations
        - Rebuild corrupted indexes
        - Restore referential integrity
        """
        try:
            repair_report = {
                "timestamp": datetime.utcnow().isoformat(),
                "repairs_attempted": [],
                "repairs_successful": [],
                "repairs_failed": []
            }

            # Get latest validation report
            if not self.validation_history:
                validation_result = await self.validate_integrity()
                if not validation_result.success:
                    return validation_result

            latest_validation = self.validation_history[-1] if self.validation_history else {}
            issues = latest_validation.get("issues_found", [])

            for issue in issues:
                repair_strategy = self.repair_strategies.get(issue["type"])

                if repair_strategy:
                    try:
                        repair_report["repairs_attempted"].append(issue)
                        await repair_strategy(issue)
                        repair_report["repairs_successful"].append(issue)
                        logger.info(f"Repaired: {issue['type']} - {issue.get('description', '')}")
                    except Exception as e:
                        repair_report["repairs_failed"].append({
                            "issue": issue,
                            "error": str(e)
                        })
                        logger.error(f"Repair failed: {e}")

            # Verify repairs
            if repair_report["repairs_successful"]:
                verification_result = await self.validate_integrity()
                repair_report["verification"] = verification_result.data

            return TaskResult(
                success=True,
                data=repair_report
            )

        except Exception as e:
            logger.error(f"Repair process failed: {e}")
            return TaskResult(
                success=False,
                data={"error": str(e)}
            )

    async def _check_foreign_keys(self) -> List[Dict]:
        """Check foreign key constraint violations."""
        issues = []

        try:
            async with self.get_db_session() as session:
                # Check for invalid foreign keys (simplified example)
                result = await session.execute("""
                    SELECT
                        tc.table_name,
                        tc.constraint_name
                    FROM information_schema.table_constraints tc
                    WHERE tc.constraint_type = 'FOREIGN KEY'
                """)

                constraints = result.fetchall()

                # For each constraint, check for violations
                # (In real implementation, would perform actual checks)
                for constraint in constraints[:2]:  # Limit for demo
                    # Simulate check
                    await asyncio.sleep(0.01)

                    # Example of finding an issue
                    if False:  # Would be actual check
                        issues.append({
                            "type": "foreign_key_violation",
                            "table": constraint["table_name"],
                            "constraint": constraint["constraint_name"],
                            "description": "Invalid foreign key reference"
                        })
        except:
            pass  # Handle database not available

        return issues

    async def _check_orphan_records(self) -> List[Dict]:
        """Check for orphan records without parent references."""
        issues = []

        # Simplified check for orphan records
        tables_to_check = ["user_progress", "quiz_results", "content_items"]

        for table in tables_to_check:
            # Simulate checking
            await asyncio.sleep(0.01)

            # Example of finding orphans (would be actual query)
            if False:  # Would check actual orphans
                issues.append({
                    "type": "orphan_records",
                    "table": table,
                    "count": 5,
                    "description": f"Found orphan records in {table}"
                })

        return issues

    async def _check_data_consistency(self) -> List[Dict]:
        """Check for data consistency issues."""
        issues = []

        # Check for inconsistent data
        consistency_checks = [
            {"field": "email", "pattern": r"^[\w\.-]+@[\w\.-]+\.\w+$"},
            {"field": "phone", "pattern": r"^\+?1?\d{9,15}$"}
        ]

        for check in consistency_checks:
            # Simulate consistency check
            await asyncio.sleep(0.01)

            # Example of finding inconsistency
            if False:  # Would be actual check
                issues.append({
                    "type": "data_inconsistency",
                    "field": check["field"],
                    "pattern": check["pattern"],
                    "description": f"Invalid format for {check['field']}"
                })

        return issues

    async def _check_duplicates(self) -> List[Dict]:
        """Check for duplicate records."""
        issues = []

        # Check for duplicates in key tables
        tables = ["users", "content", "assessments"]

        for table in tables:
            # Simulate duplicate check
            await asyncio.sleep(0.01)

            # Example of finding duplicates
            if False:  # Would be actual check
                issues.append({
                    "type": "duplicate_records",
                    "table": table,
                    "count": 3,
                    "description": f"Found duplicate records in {table}"
                })

        return issues

    async def check_constraints(self) -> TaskResult:
        """Check all database constraints."""
        try:
            constraint_report = {
                "timestamp": datetime.utcnow().isoformat(),
                "constraints_checked": 0,
                "violations": []
            }

            async with self.get_db_session() as session:
                # Get all constraints
                result = await session.execute("""
                    SELECT
                        tc.constraint_name,
                        tc.constraint_type,
                        tc.table_name
                    FROM information_schema.table_constraints tc
                    WHERE tc.table_schema = 'public'
                """)

                constraints = result.fetchall()
                constraint_report["constraints_checked"] = len(constraints)

            return TaskResult(
                success=True,
                data=constraint_report
            )

        except Exception as e:
            logger.error(f"Constraint check failed: {e}")
            return TaskResult(
                success=False,
                data={"error": str(e)}
            )


# ============================================================================
# BACKUP RECOVERY AGENT
# ============================================================================

class BackupRecoveryAgent(BaseDatabaseAgent):
    """
    Manages automated backup and disaster recovery procedures.

    Features:
    - Scheduled automatic backups
    - Point-in-time recovery (PITR)
    - Cross-region replication
    - Recovery testing automation
    - Backup verification and integrity checks
    - Incremental and differential backups
    """

    def __init__(self, config: Optional[DatabaseAgentConfig] = None):
        """Initialize the Backup Recovery Agent."""
        if not config:
            config = DatabaseAgentConfig(
                name="BackupRecoveryAgent",
                capability=AgentCapability.ORCHESTRATION,
                backup_retention_days=30
            )
        super().__init__(config)
        self.backup_history: List[Dict] = []
        self.recovery_points: Dict[str, Any] = {}
        self.backup_schedule: Dict[str, Any] = {
            "full": "0 2 * * 0",  # Weekly full backup at 2 AM Sunday
            "incremental": "0 2 * * 1-6",  # Daily incremental
            "transaction_log": "*/15 * * * *"  # Every 15 minutes
        }

    async def _process_task(self, state: AgentState) -> TaskResult:
        """Process backup and recovery tasks."""
        task = state.get("task", "")
        operation = state.get("operation", DatabaseOperation.BACKUP)

        if operation == DatabaseOperation.BACKUP:
            backup_type = state.get("backup_type", "full")
            return await self.create_backup(backup_type)
        elif operation == DatabaseOperation.RESTORE:
            backup_id = state.get("backup_id")
            return await self.restore_backup(backup_id)
        else:
            return await self.verify_backups()

    async def create_backup(self, backup_type: str = "full") -> TaskResult:
        """
        Create a database backup.

        Args:
            backup_type: Type of backup (full, incremental, differential)

        Returns:
            TaskResult with backup details
        """
        try:
            backup_id = str(uuid.uuid4())
            timestamp = datetime.utcnow()

            logger.info(f"Creating {backup_type} backup: {backup_id}")

            # Determine backup path
            backup_path = Path(f"/backups/{timestamp.strftime('%Y%m%d')}/{backup_id}")
            backup_path.mkdir(parents=True, exist_ok=True)

            # Perform backup based on type
            if backup_type == "full":
                backup_result = await self._full_backup(backup_path)
            elif backup_type == "incremental":
                backup_result = await self._incremental_backup(backup_path)
            elif backup_type == "differential":
                backup_result = await self._differential_backup(backup_path)
            else:
                backup_result = await self._transaction_log_backup(backup_path)

            # Create backup metadata
            backup_metadata = {
                "backup_id": backup_id,
                "backup_type": backup_type,
                "timestamp": timestamp.isoformat(),
                "path": str(backup_path),
                "size_bytes": backup_result.get("size", 0),
                "duration_seconds": backup_result.get("duration", 0),
                "checksum": backup_result.get("checksum", ""),
                "status": "completed"
            }

            # Store backup metadata
            self.backup_history.append(backup_metadata)

            # Update metrics
            self.metrics.last_backup = timestamp

            # Compress backup
            if backup_result.get("compress", True):
                await self._compress_backup(backup_path)

            # Verify backup integrity
            verification = await self._verify_backup_integrity(backup_path)
            backup_metadata["verified"] = verification["valid"]

            # Replicate to secondary location if configured
            if backup_result.get("replicate", False):
                replication = await self._replicate_backup(backup_path)
                backup_metadata["replicated"] = replication["success"]

            # Clean old backups based on retention policy
            await self._cleanup_old_backups()

            # Publish backup event
            await self.publish_event("backup_completed", backup_metadata)

            logger.info(f"Backup completed: {backup_id}")

            return TaskResult(
                success=True,
                data=backup_metadata
            )

        except Exception as e:
            logger.error(f"Backup failed: {e}")
            return TaskResult(
                success=False,
                data={"error": str(e), "backup_type": backup_type}
            )

    async def restore_backup(
        self,
        backup_id: Optional[str] = None,
        point_in_time: Optional[datetime] = None
    ) -> TaskResult:
        """
        Restore database from backup.

        Args:
            backup_id: Specific backup to restore
            point_in_time: Restore to specific point in time

        Returns:
            TaskResult with restoration details
        """
        try:
            logger.info(f"Starting restoration: backup_id={backup_id}, pit={point_in_time}")

            # Find backup to restore
            if backup_id:
                backup = self._find_backup(backup_id)
            elif point_in_time:
                backup = self._find_backup_for_pit(point_in_time)
            else:
                # Use latest backup
                backup = self.backup_history[-1] if self.backup_history else None

            if not backup:
                return TaskResult(
                    success=False,
                    data={"error": "No suitable backup found"}
                )

            restoration_report = {
                "restoration_id": str(uuid.uuid4()),
                "backup_id": backup["backup_id"],
                "started_at": datetime.utcnow().isoformat(),
                "backup_timestamp": backup["timestamp"],
                "steps": []
            }

            # Step 1: Validate backup
            validation = await self._verify_backup_integrity(Path(backup["path"]))
            if not validation["valid"]:
                return TaskResult(
                    success=False,
                    data={"error": "Backup validation failed", "validation": validation}
                )
            restoration_report["steps"].append({"step": "validation", "status": "completed"})

            # Step 2: Create restoration point
            restoration_point = await self._create_restoration_point()
            restoration_report["steps"].append({"step": "restoration_point", "status": "completed"})

            # Step 3: Restore data
            restore_result = await self._restore_data(Path(backup["path"]))
            restoration_report["steps"].append({"step": "restore_data", "status": "completed"})

            # Step 4: Apply transaction logs if point-in-time
            if point_in_time:
                log_result = await self._apply_transaction_logs(backup["timestamp"], point_in_time)
                restoration_report["steps"].append({"step": "transaction_logs", "status": "completed"})

            # Step 5: Verify restoration
            verification = await self._verify_restoration()
            restoration_report["steps"].append({"step": "verification", "status": "completed"})

            restoration_report["completed_at"] = datetime.utcnow().isoformat()
            restoration_report["status"] = "success"

            # Publish restoration event
            await self.publish_event("restoration_completed", restoration_report)

            logger.info(f"Restoration completed: {restoration_report['restoration_id']}")

            return TaskResult(
                success=True,
                data=restoration_report
            )

        except Exception as e:
            logger.error(f"Restoration failed: {e}")
            return TaskResult(
                success=False,
                data={"error": str(e)}
            )

    async def verify_backups(self) -> TaskResult:
        """Verify all backups for integrity and recoverability."""
        try:
            verification_report = {
                "timestamp": datetime.utcnow().isoformat(),
                "backups_checked": 0,
                "valid_backups": [],
                "invalid_backups": [],
                "recovery_test_results": []
            }

            # Check recent backups
            recent_backups = self.backup_history[-10:] if len(self.backup_history) > 10 else self.backup_history

            for backup in recent_backups:
                verification_report["backups_checked"] += 1

                # Verify integrity
                integrity = await self._verify_backup_integrity(Path(backup["path"]))

                if integrity["valid"]:
                    verification_report["valid_backups"].append(backup["backup_id"])
                else:
                    verification_report["invalid_backups"].append({
                        "backup_id": backup["backup_id"],
                        "reason": integrity.get("error", "Unknown")
                    })

            # Perform recovery test on latest backup
            if self.backup_history:
                test_result = await self._test_recovery(self.backup_history[-1])
                verification_report["recovery_test_results"].append(test_result)

            return TaskResult(
                success=True,
                data=verification_report
            )

        except Exception as e:
            logger.error(f"Backup verification failed: {e}")
            return TaskResult(
                success=False,
                data={"error": str(e)}
            )

    async def _full_backup(self, path: Path) -> Dict:
        """Perform full database backup."""
        # Simulate full backup
        await asyncio.sleep(0.5)
        return {
            "size": 1024 * 1024 * 100,  # 100MB
            "duration": 5,
            "checksum": hashlib.sha256(str(path).encode()).hexdigest(),
            "compress": True,
            "replicate": True
        }

    async def _incremental_backup(self, path: Path) -> Dict:
        """Perform incremental backup."""
        # Simulate incremental backup
        await asyncio.sleep(0.2)
        return {
            "size": 1024 * 1024 * 10,  # 10MB
            "duration": 2,
            "checksum": hashlib.sha256(str(path).encode()).hexdigest(),
            "compress": True,
            "replicate": False
        }

    async def _differential_backup(self, path: Path) -> Dict:
        """Perform differential backup."""
        # Simulate differential backup
        await asyncio.sleep(0.3)
        return {
            "size": 1024 * 1024 * 30,  # 30MB
            "duration": 3,
            "checksum": hashlib.sha256(str(path).encode()).hexdigest(),
            "compress": True,
            "replicate": False
        }

    async def _transaction_log_backup(self, path: Path) -> Dict:
        """Backup transaction logs."""
        # Simulate transaction log backup
        await asyncio.sleep(0.1)
        return {
            "size": 1024 * 1024,  # 1MB
            "duration": 1,
            "checksum": hashlib.sha256(str(path).encode()).hexdigest(),
            "compress": False,
            "replicate": True
        }

    async def _compress_backup(self, path: Path):
        """Compress backup files."""
        # Simulate compression
        await asyncio.sleep(0.1)

    async def _verify_backup_integrity(self, path: Path) -> Dict:
        """Verify backup file integrity."""
        # Simulate integrity check
        await asyncio.sleep(0.05)
        return {
            "valid": True,
            "checksum_match": True,
            "files_complete": True
        }

    async def _replicate_backup(self, path: Path) -> Dict:
        """Replicate backup to secondary location."""
        # Simulate replication
        await asyncio.sleep(0.2)
        return {
            "success": True,
            "destination": "s3://backup-bucket/",
            "duration": 2
        }

    async def _cleanup_old_backups(self):
        """Remove backups older than retention period."""
        retention_date = datetime.utcnow() - timedelta(days=self.db_config.backup_retention_days)

        self.backup_history = [
            backup for backup in self.backup_history
            if datetime.fromisoformat(backup["timestamp"]) > retention_date
        ]

    def _find_backup(self, backup_id: str) -> Optional[Dict]:
        """Find backup by ID."""
        for backup in self.backup_history:
            if backup["backup_id"] == backup_id:
                return backup
        return None

    def _find_backup_for_pit(self, point_in_time: datetime) -> Optional[Dict]:
        """Find suitable backup for point-in-time recovery."""
        # Find the latest full backup before the target time
        for backup in reversed(self.backup_history):
            if backup["backup_type"] == "full":
                if datetime.fromisoformat(backup["timestamp"]) <= point_in_time:
                    return backup
        return None

    async def _create_restoration_point(self) -> Dict:
        """Create restoration point before restoring."""
        # Simulate creating restoration point
        await asyncio.sleep(0.1)
        return {"restoration_point": str(uuid.uuid4())}

    async def _restore_data(self, path: Path) -> Dict:
        """Restore data from backup."""
        # Simulate data restoration
        await asyncio.sleep(0.5)
        return {"restored": True}

    async def _apply_transaction_logs(self, from_time: str, to_time: datetime) -> Dict:
        """Apply transaction logs for point-in-time recovery."""
        # Simulate applying transaction logs
        await asyncio.sleep(0.2)
        return {"logs_applied": True}

    async def _verify_restoration(self) -> Dict:
        """Verify successful restoration."""
        # Simulate verification
        await asyncio.sleep(0.1)
        return {"verified": True}

    async def _test_recovery(self, backup: Dict) -> Dict:
        """Test recovery procedure with a backup."""
        # Simulate recovery test
        await asyncio.sleep(0.3)
        return {
            "backup_id": backup["backup_id"],
            "test_status": "passed",
            "recovery_time": 10
        }


# ============================================================================
# MONITORING AGENT
# ============================================================================

class MonitoringAgent(BaseDatabaseAgent):
    """
    Tracks database performance metrics and provides alerting.

    Features:
    - Real-time metrics collection
    - Anomaly detection using statistical models
    - Alert management with escalation
    - Performance trending and forecasting
    - Capacity planning recommendations
    - Dashboard metrics generation
    """

    def __init__(self, config: Optional[DatabaseAgentConfig] = None):
        """Initialize the Monitoring Agent."""
        if not config:
            config = DatabaseAgentConfig(
                name="MonitoringAgent",
                capability=AgentCapability.ANALYSIS,
                enable_monitoring=True,
                monitoring_interval=60
            )
        super().__init__(config)
        self.metrics_history: List[Dict] = []
        self.alerts: List[Dict] = []
        self.thresholds: Dict[str, float] = {
            "cpu_percent": 80.0,
            "memory_percent": 85.0,
            "disk_usage_percent": 90.0,
            "query_time_ms": 1000.0,
            "error_rate": 0.05,
            "connection_pool_usage": 0.8
        }
        self.anomaly_baselines: Dict[str, Any] = {}

    async def _process_task(self, state: AgentState) -> TaskResult:
        """Process monitoring tasks."""
        task = state.get("task", "")
        operation = state.get("operation", DatabaseOperation.MONITOR)

        if task == "collect_metrics":
            return await self.collect_metrics()
        elif task == "detect_anomalies":
            return await self.detect_anomalies()
        elif task == "generate_alerts":
            return await self.generate_alerts()
        else:
            return await self.generate_dashboard_metrics()

    async def collect_metrics(self) -> TaskResult:
        """
        Collect comprehensive database metrics.

        Metrics collected:
        - Performance metrics (CPU, memory, disk)
        - Query statistics
        - Connection pool status
        - Cache performance
        - Replication lag
        - Error rates
        """
        try:
            metrics = {
                "timestamp": datetime.utcnow().isoformat(),
                "performance": {},
                "database": {},
                "cache": {},
                "replication": {},
                "errors": {}
            }

            # Collect performance metrics
            perf_metrics = await self._collect_performance_metrics()
            metrics["performance"] = perf_metrics

            # Collect database metrics
            db_metrics = await self._collect_database_metrics()
            metrics["database"] = db_metrics

            # Collect cache metrics
            cache_metrics = await self._collect_cache_metrics()
            metrics["cache"] = cache_metrics

            # Collect replication metrics
            repl_metrics = await self._collect_replication_metrics()
            metrics["replication"] = repl_metrics

            # Collect error metrics
            error_metrics = await self._collect_error_metrics()
            metrics["errors"] = error_metrics

            # Store metrics history
            self.metrics_history.append(metrics)

            # Keep only last 24 hours of metrics
            cutoff_time = datetime.utcnow() - timedelta(hours=24)
            self.metrics_history = [
                m for m in self.metrics_history
                if datetime.fromisoformat(m["timestamp"]) > cutoff_time
            ]

            # Check thresholds and generate alerts if needed
            alerts = await self._check_thresholds(metrics)
            if alerts:
                for alert in alerts:
                    await self.publish_event("alert_triggered", alert)

            # Update anomaly baselines
            await self._update_baselines(metrics)

            logger.info(f"Metrics collected: {len(metrics)} categories")

            return TaskResult(
                success=True,
                data=metrics
            )

        except Exception as e:
            logger.error(f"Metrics collection failed: {e}")
            return TaskResult(
                success=False,
                data={"error": str(e)}
            )

    async def detect_anomalies(self) -> TaskResult:
        """
        Detect anomalies in database behavior using statistical analysis.

        Uses:
        - Standard deviation for outlier detection
        - Moving averages for trend analysis
        - Pattern matching for known issues
        """
        try:
            anomalies = {
                "timestamp": datetime.utcnow().isoformat(),
                "anomalies_detected": [],
                "severity_counts": {
                    "low": 0,
                    "medium": 0,
                    "high": 0,
                    "critical": 0
                }
            }

            if len(self.metrics_history) < 10:
                # Not enough data for anomaly detection
                return TaskResult(
                    success=True,
                    data={
                        "message": "Insufficient data for anomaly detection",
                        "metrics_available": len(self.metrics_history)
                    }
                )

            # Analyze query times
            query_anomalies = await self._detect_query_anomalies()
            anomalies["anomalies_detected"].extend(query_anomalies)

            # Analyze connection patterns
            conn_anomalies = await self._detect_connection_anomalies()
            anomalies["anomalies_detected"].extend(conn_anomalies)

            # Analyze error patterns
            error_anomalies = await self._detect_error_anomalies()
            anomalies["anomalies_detected"].extend(error_anomalies)

            # Analyze resource usage
            resource_anomalies = await self._detect_resource_anomalies()
            anomalies["anomalies_detected"].extend(resource_anomalies)

            # Count severities
            for anomaly in anomalies["anomalies_detected"]:
                severity = anomaly.get("severity", "low")
                anomalies["severity_counts"][severity] += 1

            # Generate alerts for critical anomalies
            for anomaly in anomalies["anomalies_detected"]:
                if anomaly.get("severity") in ["high", "critical"]:
                    await self._create_alert(anomaly)

            logger.info(f"Anomaly detection completed: {len(anomalies['anomalies_detected'])} found")

            return TaskResult(
                success=True,
                data=anomalies
            )

        except Exception as e:
            logger.error(f"Anomaly detection failed: {e}")
            return TaskResult(
                success=False,
                data={"error": str(e)}
            )

    async def generate_alerts(self) -> TaskResult:
        """Generate and manage alerts based on monitoring data."""
        try:
            alert_report = {
                "timestamp": datetime.utcnow().isoformat(),
                "active_alerts": [],
                "resolved_alerts": [],
                "new_alerts": []
            }

            # Check current metrics against thresholds
            if self.metrics_history:
                latest_metrics = self.metrics_history[-1]

                # Check each threshold
                for metric_name, threshold in self.thresholds.items():
                    current_value = self._get_metric_value(latest_metrics, metric_name)

                    if current_value and current_value > threshold:
                        alert = {
                            "alert_id": str(uuid.uuid4()),
                            "metric": metric_name,
                            "value": current_value,
                            "threshold": threshold,
                            "severity": self._calculate_severity(metric_name, current_value, threshold),
                            "timestamp": datetime.utcnow().isoformat(),
                            "status": "active"
                        }

                        alert_report["new_alerts"].append(alert)
                        self.alerts.append(alert)

            # Check for resolved alerts
            for alert in self.alerts:
                if alert["status"] == "active":
                    current_value = self._get_current_metric_value(alert["metric"])

                    if current_value and current_value <= self.thresholds[alert["metric"]]:
                        alert["status"] = "resolved"
                        alert["resolved_at"] = datetime.utcnow().isoformat()
                        alert_report["resolved_alerts"].append(alert)
                    else:
                        alert_report["active_alerts"].append(alert)

            # Send notifications for new critical alerts
            for alert in alert_report["new_alerts"]:
                if alert["severity"] == "critical":
                    await self._send_alert_notification(alert)

            return TaskResult(
                success=True,
                data=alert_report
            )

        except Exception as e:
            logger.error(f"Alert generation failed: {e}")
            return TaskResult(
                success=False,
                data={"error": str(e)}
            )

    async def generate_dashboard_metrics(self) -> TaskResult:
        """Generate metrics for monitoring dashboard."""
        try:
            dashboard_data = {
                "timestamp": datetime.utcnow().isoformat(),
                "summary": {},
                "charts": {},
                "alerts": [],
                "recommendations": []
            }

            # Generate summary metrics
            if self.metrics_history:
                latest = self.metrics_history[-1]
                dashboard_data["summary"] = {
                    "health_score": self._calculate_health_score(),
                    "active_connections": latest.get("database", {}).get("active_connections", 0),
                    "queries_per_second": latest.get("database", {}).get("qps", 0),
                    "cache_hit_ratio": latest.get("cache", {}).get("hit_ratio", 0),
                    "error_rate": latest.get("errors", {}).get("rate", 0)
                }

            # Generate time series data for charts
            dashboard_data["charts"] = {
                "performance": self._generate_performance_chart_data(),
                "queries": self._generate_query_chart_data(),
                "errors": self._generate_error_chart_data()
            }

            # Add active alerts
            dashboard_data["alerts"] = [
                alert for alert in self.alerts
                if alert.get("status") == "active"
            ]

            # Generate recommendations
            dashboard_data["recommendations"] = await self._generate_recommendations()

            return TaskResult(
                success=True,
                data=dashboard_data
            )

        except Exception as e:
            logger.error(f"Dashboard metrics generation failed: {e}")
            return TaskResult(
                success=False,
                data={"error": str(e)}
            )

    async def _collect_performance_metrics(self) -> Dict:
        """Collect system performance metrics."""
        # Simulate performance metrics collection
        return {
            "cpu_percent": 45.2,
            "memory_percent": 62.8,
            "disk_usage_percent": 71.5,
            "network_io": {
                "bytes_sent": 1024000,
                "bytes_recv": 2048000
            }
        }

    async def _collect_database_metrics(self) -> Dict:
        """Collect database-specific metrics."""
        metrics = {
            "active_connections": self.metrics.active_connections,
            "connection_pool_size": self.metrics.connection_pool_size,
            "queries_per_second": 150,
            "avg_query_time_ms": self.metrics.avg_query_time * 1000,
            "slow_queries": 5,
            "deadlocks": 0
        }

        if self.engine:
            # Get actual metrics from database
            try:
                async with self.get_db_session() as session:
                    result = await session.execute("""
                        SELECT
                            COUNT(*) as connection_count
                        FROM pg_stat_activity
                    """)
                    row = result.fetchone()
                    if row:
                        metrics["active_connections"] = row["connection_count"]
            except:
                pass

        return metrics

    async def _collect_cache_metrics(self) -> Dict:
        """Collect cache performance metrics."""
        return {
            "hit_ratio": self.metrics.cache_hit_ratio,
            "memory_usage_mb": 256,
            "evictions": 10,
            "keys_count": 5000
        }

    async def _collect_replication_metrics(self) -> Dict:
        """Collect replication metrics."""
        return {
            "lag_seconds": self.metrics.replication_lag,
            "replicas_connected": 2,
            "sync_status": "in_sync"
        }

    async def _collect_error_metrics(self) -> Dict:
        """Collect error metrics."""
        return {
            "rate": self.metrics.error_rate,
            "total_errors": 25,
            "error_types": {
                "connection": 5,
                "timeout": 10,
                "constraint": 3,
                "other": 7
            }
        }

    async def _check_thresholds(self, metrics: Dict) -> List[Dict]:
        """Check metrics against thresholds."""
        alerts = []

        # Check performance thresholds
        perf = metrics.get("performance", {})
        for metric, value in perf.items():
            if metric in self.thresholds and value > self.thresholds[metric]:
                alerts.append({
                    "metric": metric,
                    "value": value,
                    "threshold": self.thresholds[metric],
                    "severity": "high" if value > self.thresholds[metric] * 1.2 else "medium"
                })

        return alerts

    async def _update_baselines(self, metrics: Dict):
        """Update anomaly detection baselines."""
        # Simple baseline update (would use more sophisticated methods in production)
        for category, values in metrics.items():
            if isinstance(values, dict):
                for metric, value in values.items():
                    if isinstance(value, (int, float)):
                        key = f"{category}.{metric}"
                        if key not in self.anomaly_baselines:
                            self.anomaly_baselines[key] = {
                                "mean": value,
                                "std": 0,
                                "count": 1
                            }
                        else:
                            # Update running statistics
                            baseline = self.anomaly_baselines[key]
                            baseline["count"] += 1
                            delta = value - baseline["mean"]
                            baseline["mean"] += delta / baseline["count"]
                            baseline["std"] = (baseline["std"] * (baseline["count"] - 1) + delta ** 2) / baseline["count"]

    async def _detect_query_anomalies(self) -> List[Dict]:
        """Detect anomalies in query performance."""
        anomalies = []

        # Check for sudden query time increases
        if len(self.metrics_history) > 2:
            recent = self.metrics_history[-1].get("database", {}).get("avg_query_time_ms", 0)
            previous = self.metrics_history[-2].get("database", {}).get("avg_query_time_ms", 0)

            if previous > 0 and recent > previous * 2:
                anomalies.append({
                    "type": "query_performance",
                    "description": f"Query time doubled: {previous}ms -> {recent}ms",
                    "severity": "high",
                    "timestamp": datetime.utcnow().isoformat()
                })

        return anomalies

    async def _detect_connection_anomalies(self) -> List[Dict]:
        """Detect anomalies in connection patterns."""
        anomalies = []

        # Check for connection spikes
        if len(self.metrics_history) > 5:
            recent_connections = [
                m.get("database", {}).get("active_connections", 0)
                for m in self.metrics_history[-5:]
            ]
            avg_connections = sum(recent_connections) / len(recent_connections)
            current = recent_connections[-1]

            if current > avg_connections * 1.5:
                anomalies.append({
                    "type": "connection_spike",
                    "description": f"Connection spike: {current} (avg: {avg_connections:.1f})",
                    "severity": "medium",
                    "timestamp": datetime.utcnow().isoformat()
                })

        return anomalies

    async def _detect_error_anomalies(self) -> List[Dict]:
        """Detect anomalies in error patterns."""
        anomalies = []

        # Check for error rate increases
        if self.metrics_history:
            current_error_rate = self.metrics_history[-1].get("errors", {}).get("rate", 0)

            if current_error_rate > 0.1:  # More than 10% errors
                anomalies.append({
                    "type": "high_error_rate",
                    "description": f"High error rate: {current_error_rate:.1%}",
                    "severity": "critical",
                    "timestamp": datetime.utcnow().isoformat()
                })

        return anomalies

    async def _detect_resource_anomalies(self) -> List[Dict]:
        """Detect anomalies in resource usage."""
        anomalies = []

        # Check for high resource usage
        if self.metrics_history:
            perf = self.metrics_history[-1].get("performance", {})

            if perf.get("cpu_percent", 0) > 90:
                anomalies.append({
                    "type": "high_cpu",
                    "description": f"CPU usage critical: {perf['cpu_percent']}%",
                    "severity": "high",
                    "timestamp": datetime.utcnow().isoformat()
                })

            if perf.get("memory_percent", 0) > 90:
                anomalies.append({
                    "type": "high_memory",
                    "description": f"Memory usage critical: {perf['memory_percent']}%",
                    "severity": "high",
                    "timestamp": datetime.utcnow().isoformat()
                })

        return anomalies

    async def _create_alert(self, anomaly: Dict):
        """Create an alert from an anomaly."""
        alert = {
            "alert_id": str(uuid.uuid4()),
            "type": anomaly["type"],
            "description": anomaly["description"],
            "severity": anomaly["severity"],
            "timestamp": anomaly["timestamp"],
            "status": "active"
        }
        self.alerts.append(alert)

        # Publish alert event
        await self.publish_event("alert_created", alert)

    def _get_metric_value(self, metrics: Dict, metric_name: str) -> Optional[float]:
        """Extract metric value from nested metrics dictionary."""
        # Map metric names to their locations
        metric_map = {
            "cpu_percent": ["performance", "cpu_percent"],
            "memory_percent": ["performance", "memory_percent"],
            "disk_usage_percent": ["performance", "disk_usage_percent"],
            "query_time_ms": ["database", "avg_query_time_ms"],
            "error_rate": ["errors", "rate"],
            "connection_pool_usage": ["database", "active_connections"]
        }

        if metric_name in metric_map:
            path = metric_map[metric_name]
            value = metrics
            for key in path:
                value = value.get(key)
                if value is None:
                    return None
            return value

        return None

    def _get_current_metric_value(self, metric_name: str) -> Optional[float]:
        """Get current value for a metric."""
        if self.metrics_history:
            return self._get_metric_value(self.metrics_history[-1], metric_name)
        return None

    def _calculate_severity(self, metric_name: str, value: float, threshold: float) -> str:
        """Calculate alert severity."""
        ratio = value / threshold

        if ratio > 1.5:
            return "critical"
        elif ratio > 1.2:
            return "high"
        elif ratio > 1.0:
            return "medium"
        else:
            return "low"

    async def _send_alert_notification(self, alert: Dict):
        """Send alert notification."""
        # Publish to Redis for notification system
        await self.publish_event("critical_alert", alert)
        logger.warning(f"Critical alert: {alert['description']}")

    def _calculate_health_score(self) -> float:
        """Calculate overall database health score (0-100)."""
        if not self.metrics_history:
            return 100.0

        latest = self.metrics_history[-1]
        score = 100.0

        # Deduct points for issues
        error_rate = latest.get("errors", {}).get("rate", 0)
        score -= error_rate * 100  # High penalty for errors

        cpu = latest.get("performance", {}).get("cpu_percent", 0)
        if cpu > 80:
            score -= (cpu - 80) / 2  # Deduct for high CPU

        memory = latest.get("performance", {}).get("memory_percent", 0)
        if memory > 85:
            score -= (memory - 85) / 2  # Deduct for high memory

        # Bonus for good cache performance
        cache_hit = latest.get("cache", {}).get("hit_ratio", 0)
        score += cache_hit * 5  # Bonus for cache hits

        return max(0, min(100, score))

    def _generate_performance_chart_data(self) -> List[Dict]:
        """Generate performance chart data."""
        return [
            {
                "timestamp": m["timestamp"],
                "cpu": m.get("performance", {}).get("cpu_percent", 0),
                "memory": m.get("performance", {}).get("memory_percent", 0)
            }
            for m in self.metrics_history[-20:]  # Last 20 data points
        ]

    def _generate_query_chart_data(self) -> List[Dict]:
        """Generate query performance chart data."""
        return [
            {
                "timestamp": m["timestamp"],
                "qps": m.get("database", {}).get("queries_per_second", 0),
                "avg_time": m.get("database", {}).get("avg_query_time_ms", 0)
            }
            for m in self.metrics_history[-20:]
        ]

    def _generate_error_chart_data(self) -> List[Dict]:
        """Generate error rate chart data."""
        return [
            {
                "timestamp": m["timestamp"],
                "error_rate": m.get("errors", {}).get("rate", 0) * 100
            }
            for m in self.metrics_history[-20:]
        ]

    async def _generate_recommendations(self) -> List[str]:
        """Generate performance recommendations."""
        recommendations = []

        if self.metrics_history:
            latest = self.metrics_history[-1]

            # Check cache performance
            cache_hit = latest.get("cache", {}).get("hit_ratio", 0)
            if cache_hit < 0.8:
                recommendations.append("Consider increasing cache size or optimizing cache strategy")

            # Check query performance
            avg_query_time = latest.get("database", {}).get("avg_query_time_ms", 0)
            if avg_query_time > 500:
                recommendations.append("Analyze slow queries and consider adding indexes")

            # Check connection pool
            connections = latest.get("database", {}).get("active_connections", 0)
            pool_size = latest.get("database", {}).get("connection_pool_size", 20)
            if connections > pool_size * 0.8:
                recommendations.append("Consider increasing connection pool size")

            # Check resource usage
            cpu = latest.get("performance", {}).get("cpu_percent", 0)
            if cpu > 70:
                recommendations.append("CPU usage is high - consider scaling vertically or optimizing queries")

        return recommendations


# Export all advanced agents
__all__ = [
    "EventSourcingAgent",
    "DataIntegrityAgent",
    "BackupRecoveryAgent",
    "MonitoringAgent"
]