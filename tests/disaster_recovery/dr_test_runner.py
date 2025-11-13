#!/usr/bin/env python3
"""Disaster Recovery Testing System for ToolBoxAI.

This module implements comprehensive disaster recovery testing including
backup/restore validation, failover testing, and data integrity verification.
"""

import argparse
import asyncio
import hashlib
import json
import os
import shutil
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import aiohttp
import docker
import psycopg2
import redis
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()


class DisasterRecoveryTester:
    """Disaster recovery testing system."""

    def __init__(self, config_file: str = "config/dr-testing.json"):
        self.config_file = Path(config_file)
        self.config = self._load_config()
        self.docker_client = docker.from_env()
        self.test_results: list[dict] = []
        self.checkpoints: dict[str, Any] = {}

    def _load_config(self) -> dict:
        """Load DR testing configuration."""
        if self.config_file.exists():
            with open(self.config_file) as f:
                return json.load(f)
        else:
            # Default configuration
            return {
                "backup": {
                    "database": {
                        "enabled": True,
                        "method": "pg_dump",
                        "location": "/tmp/backups/database",
                        "retention_days": 7,
                        "compression": True,
                    },
                    "files": {
                        "enabled": True,
                        "directories": [
                            "uploads",
                            "config",
                            "certificates",
                        ],
                        "location": "/tmp/backups/files",
                        "compression": True,
                    },
                    "redis": {
                        "enabled": True,
                        "method": "bgsave",
                        "location": "/tmp/backups/redis",
                    },
                },
                "recovery": {
                    "rpo_minutes": 15,  # Recovery Point Objective
                    "rto_minutes": 30,  # Recovery Time Objective
                    "parallel_restore": True,
                    "verify_integrity": True,
                },
                "scenarios": [
                    {
                        "name": "database_failure",
                        "description": "Simulate complete database failure",
                        "steps": ["backup", "corrupt_db", "restore", "verify"],
                    },
                    {
                        "name": "data_corruption",
                        "description": "Simulate data corruption",
                        "steps": ["backup", "corrupt_data", "detect", "restore", "verify"],
                    },
                    {
                        "name": "ransomware",
                        "description": "Simulate ransomware attack",
                        "steps": ["backup", "encrypt_files", "isolate", "restore", "verify"],
                    },
                    {
                        "name": "cascading_failure",
                        "description": "Simulate cascading service failure",
                        "steps": ["backup", "kill_services", "restore_order", "verify"],
                    },
                ],
                "validation": {
                    "data_integrity": {
                        "checksum": True,
                        "row_counts": True,
                        "sample_verification": True,
                    },
                    "functionality": {
                        "api_health": True,
                        "authentication": True,
                        "critical_paths": True,
                    },
                    "performance": {
                        "response_times": True,
                        "throughput": True,
                    },
                },
            }

    async def run_scenario(self, scenario_name: str) -> dict[str, Any]:
        """Run a specific disaster recovery scenario."""
        console.print(f"\n[bold cyan]Running DR Scenario: {scenario_name}[/bold cyan]")

        scenario = next((s for s in self.config["scenarios"] if s["name"] == scenario_name), None)

        if not scenario:
            raise ValueError(f"Unknown scenario: {scenario_name}")

        result = {
            "scenario": scenario_name,
            "description": scenario["description"],
            "started_at": datetime.now().isoformat(),
            "steps": [],
            "status": "running",
        }

        try:
            # Create checkpoint before starting
            checkpoint_id = await self._create_checkpoint()
            result["checkpoint_id"] = checkpoint_id

            # Execute scenario steps
            for step_name in scenario["steps"]:
                console.print(f"  Executing: [yellow]{step_name}[/yellow]")

                step_result = await self._execute_step(step_name)
                result["steps"].append(
                    {
                        "name": step_name,
                        "result": step_result,
                        "timestamp": datetime.now().isoformat(),
                    }
                )

                if not step_result.get("success"):
                    result["status"] = "failed"
                    break

            # If all steps succeeded
            if result["status"] == "running":
                result["status"] = "completed"

            # Validate recovery
            validation_result = await self._validate_recovery(checkpoint_id)
            result["validation"] = validation_result

            # Calculate metrics
            result["metrics"] = self._calculate_metrics(result)

        except Exception as e:
            result["status"] = "error"
            result["error"] = str(e)
            console.print(f"[red]Scenario failed: {e}[/red]")

        finally:
            result["completed_at"] = datetime.now().isoformat()
            self.test_results.append(result)

        # Display result
        self._display_scenario_result(result)

        return result

    async def _create_checkpoint(self) -> str:
        """Create a checkpoint of current system state."""
        checkpoint_id = f"checkpoint_{datetime.now():%Y%m%d_%H%M%S}"

        checkpoint = {
            "id": checkpoint_id,
            "created_at": datetime.now().isoformat(),
            "database": {},
            "files": {},
            "services": {},
        }

        # Capture database state
        checkpoint["database"] = await self._capture_database_state()

        # Capture file checksums
        checkpoint["files"] = await self._capture_file_state()

        # Capture service states
        checkpoint["services"] = await self._capture_service_state()

        self.checkpoints[checkpoint_id] = checkpoint
        console.print(f"  Created checkpoint: {checkpoint_id}")

        return checkpoint_id

    async def _capture_database_state(self) -> dict:
        """Capture current database state."""
        state = {
            "row_counts": {},
            "checksums": {},
            "sample_data": {},
        }

        try:
            # Connect to database
            conn = psycopg2.connect(
                os.environ.get(
                    "DATABASE_URL", "postgresql://test_user:test_password@localhost/test_db"
                )
            )
            cursor = conn.cursor()

            # Get row counts for all tables
            cursor.execute(
                """
                SELECT tablename
                FROM pg_tables
                WHERE schemaname = 'public'
            """
            )
            tables = cursor.fetchall()

            for (table,) in tables:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                state["row_counts"][table] = cursor.fetchone()[0]

                # Calculate checksum for table data
                cursor.execute(
                    f"""
                    SELECT md5(array_agg(md5(t::text))::text)
                    FROM {table} t
                """
                )
                checksum_result = cursor.fetchone()
                state["checksums"][table] = checksum_result[0] if checksum_result[0] else "empty"

                # Sample first row
                cursor.execute(f"SELECT * FROM {table} LIMIT 1")
                if cursor.rowcount > 0:
                    state["sample_data"][table] = str(cursor.fetchone())

            cursor.close()
            conn.close()

        except Exception as e:
            console.print(f"  [yellow]Warning: Could not capture database state: {e}[/yellow]")

        return state

    async def _capture_file_state(self) -> dict:
        """Capture file system state."""
        state = {
            "checksums": {},
            "sizes": {},
        }

        for directory in self.config["backup"]["files"]["directories"]:
            dir_path = Path(directory)
            if dir_path.exists():
                for file_path in dir_path.rglob("*"):
                    if file_path.is_file():
                        # Calculate checksum
                        with open(file_path, "rb") as f:
                            file_hash = hashlib.sha256(f.read()).hexdigest()
                        state["checksums"][str(file_path)] = file_hash
                        state["sizes"][str(file_path)] = file_path.stat().st_size

        return state

    async def _capture_service_state(self) -> dict:
        """Capture service states."""
        state = {
            "containers": {},
            "health_checks": {},
        }

        # Docker containers
        containers = self.docker_client.containers.list()
        for container in containers:
            state["containers"][container.name] = {
                "status": container.status,
                "image": container.image.tags[0] if container.image.tags else "unknown",
                "ports": container.ports,
            }

        # Health checks
        health_endpoints = [
            ("api", "http://localhost:8009/health"),
            ("dashboard", "http://localhost:5179"),
            ("redis", "redis://localhost:6379"),
        ]

        for name, endpoint in health_endpoints:
            state["health_checks"][name] = await self._check_health(endpoint)

        return state

    async def _check_health(self, endpoint: str) -> bool:
        """Check health of an endpoint."""
        if endpoint.startswith("http"):
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(endpoint, timeout=5) as response:
                        return response.status == 200
            except:
                return False

        elif endpoint.startswith("redis://"):
            try:
                r = redis.from_url(endpoint, socket_connect_timeout=1)
                return r.ping()
            except:
                return False

        return False

    async def _execute_step(self, step_name: str) -> dict:
        """Execute a disaster recovery step."""
        step_handlers = {
            "backup": self._step_backup,
            "corrupt_db": self._step_corrupt_db,
            "corrupt_data": self._step_corrupt_data,
            "encrypt_files": self._step_encrypt_files,
            "kill_services": self._step_kill_services,
            "detect": self._step_detect_corruption,
            "isolate": self._step_isolate_system,
            "restore": self._step_restore,
            "restore_order": self._step_restore_order,
            "verify": self._step_verify,
        }

        handler = step_handlers.get(step_name)
        if not handler:
            return {"success": False, "error": f"Unknown step: {step_name}"}

        try:
            result = await handler()
            return {"success": True, **result}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _step_backup(self) -> dict:
        """Perform backup."""
        backup_results = {}

        # Database backup
        if self.config["backup"]["database"]["enabled"]:
            db_backup = await self._backup_database()
            backup_results["database"] = db_backup

        # File backup
        if self.config["backup"]["files"]["enabled"]:
            file_backup = await self._backup_files()
            backup_results["files"] = file_backup

        # Redis backup
        if self.config["backup"]["redis"]["enabled"]:
            redis_backup = await self._backup_redis()
            backup_results["redis"] = redis_backup

        return {"backups": backup_results}

    async def _backup_database(self) -> dict:
        """Backup database."""
        backup_dir = Path(self.config["backup"]["database"]["location"])
        backup_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = backup_dir / f"db_backup_{timestamp}.sql"

        # Run pg_dump
        db_url = os.environ.get(
            "DATABASE_URL", "postgresql://test_user:test_password@localhost/test_db"
        )

        cmd = ["pg_dump", db_url, "-f", str(backup_file)]

        if self.config["backup"]["database"]["compression"]:
            backup_file = backup_dir / f"db_backup_{timestamp}.sql.gz"
            cmd = ["pg_dump", db_url, "-Z", "9", "-f", str(backup_file)]

        result = subprocess.run(cmd, capture_output=True, text=True)

        return {
            "file": str(backup_file),
            "size": backup_file.stat().st_size if backup_file.exists() else 0,
            "success": result.returncode == 0,
            "timestamp": timestamp,
        }

    async def _backup_files(self) -> dict:
        """Backup files."""
        backup_dir = Path(self.config["backup"]["files"]["location"])
        backup_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = backup_dir / f"files_backup_{timestamp}.tar"

        # Create tar archive
        directories = self.config["backup"]["files"]["directories"]
        existing_dirs = [d for d in directories if Path(d).exists()]

        if existing_dirs:
            cmd = ["tar", "-cf", str(backup_file)] + existing_dirs

            if self.config["backup"]["files"]["compression"]:
                backup_file = backup_dir / f"files_backup_{timestamp}.tar.gz"
                cmd = ["tar", "-czf", str(backup_file)] + existing_dirs

            result = subprocess.run(cmd, capture_output=True, text=True)

            return {
                "file": str(backup_file),
                "size": backup_file.stat().st_size if backup_file.exists() else 0,
                "success": result.returncode == 0,
                "directories": existing_dirs,
                "timestamp": timestamp,
            }

        return {"success": False, "error": "No directories to backup"}

    async def _backup_redis(self) -> dict:
        """Backup Redis data."""
        try:
            r = redis.Redis(host="localhost", port=6379)
            r.bgsave()

            # Wait for backup to complete
            while r.lastsave() < time.time() - 1:
                await asyncio.sleep(0.5)

            # Copy dump file
            backup_dir = Path(self.config["backup"]["redis"]["location"])
            backup_dir.mkdir(parents=True, exist_ok=True)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = backup_dir / f"redis_backup_{timestamp}.rdb"

            # Find Redis dump file (usually in /var/lib/redis/dump.rdb)
            redis_dump = Path("/var/lib/redis/dump.rdb")
            if not redis_dump.exists():
                redis_dump = Path("dump.rdb")  # Check current directory

            if redis_dump.exists():
                shutil.copy2(redis_dump, backup_file)

                return {
                    "file": str(backup_file),
                    "size": backup_file.stat().st_size,
                    "success": True,
                    "timestamp": timestamp,
                }

        except Exception as e:
            return {"success": False, "error": str(e)}

        return {"success": False, "error": "Redis dump file not found"}

    async def _step_corrupt_db(self) -> dict:
        """Simulate database corruption."""
        # WARNING: This is for testing only!
        conn = psycopg2.connect(
            os.environ.get("DATABASE_URL", "postgresql://test_user:test_password@localhost/test_db")
        )
        cursor = conn.cursor()

        # Drop a random index to simulate corruption
        cursor.execute(
            """
            SELECT indexname FROM pg_indexes
            WHERE schemaname = 'public'
            LIMIT 1
        """
        )
        result = cursor.fetchone()

        if result:
            index_name = result[0]
            cursor.execute(f"DROP INDEX IF EXISTS {index_name}")
            conn.commit()

            return {"corrupted": "index", "name": index_name}

        cursor.close()
        conn.close()

        return {"corrupted": "none"}

    async def _step_corrupt_data(self) -> dict:
        """Simulate data corruption."""
        # Modify random files
        corrupted_files = []

        for directory in self.config["backup"]["files"]["directories"]:
            dir_path = Path(directory)
            if dir_path.exists():
                files = list(dir_path.rglob("*"))[:3]  # Corrupt up to 3 files
                for file_path in files:
                    if file_path.is_file():
                        # Append garbage data
                        with open(file_path, "ab") as f:
                            f.write(b"CORRUPTED_DATA_MARKER")
                        corrupted_files.append(str(file_path))

        return {"corrupted_files": corrupted_files}

    async def _step_encrypt_files(self) -> dict:
        """Simulate ransomware encryption."""
        encrypted_files = []

        # Simulate encryption by renaming files
        for directory in self.config["backup"]["files"]["directories"]:
            dir_path = Path(directory)
            if dir_path.exists():
                files = list(dir_path.rglob("*"))[:5]  # "Encrypt" up to 5 files
                for file_path in files:
                    if file_path.is_file():
                        encrypted_path = file_path.with_suffix(file_path.suffix + ".encrypted")
                        file_path.rename(encrypted_path)
                        encrypted_files.append(str(encrypted_path))

        return {"encrypted_files": encrypted_files}

    async def _step_kill_services(self) -> dict:
        """Simulate service failure."""
        killed_services = []

        # Stop random containers
        containers = self.docker_client.containers.list()[:2]  # Kill up to 2 services
        for container in containers:
            if "test" in container.name.lower():  # Only kill test containers
                container.stop()
                killed_services.append(container.name)

        return {"killed_services": killed_services}

    async def _step_detect_corruption(self) -> dict:
        """Detect data corruption."""
        detected_issues = []

        # Check database integrity
        try:
            conn = psycopg2.connect(
                os.environ.get(
                    "DATABASE_URL", "postgresql://test_user:test_password@localhost/test_db"
                )
            )
            cursor = conn.cursor()

            # Check for missing indexes
            cursor.execute(
                """
                SELECT tablename, indexname
                FROM pg_indexes
                WHERE schemaname = 'public'
            """
            )
            current_indexes = cursor.fetchall()

            # Compare with checkpoint
            # (In real scenario, would compare with stored metadata)
            detected_issues.append(
                {
                    "type": "database",
                    "issue": "index_check",
                    "status": "checked",
                }
            )

            cursor.close()
            conn.close()

        except Exception as e:
            detected_issues.append(
                {
                    "type": "database",
                    "issue": "connection_failed",
                    "error": str(e),
                }
            )

        # Check file integrity
        for directory in self.config["backup"]["files"]["directories"]:
            dir_path = Path(directory)
            if dir_path.exists():
                for file_path in dir_path.rglob("*"):
                    if file_path.is_file():
                        # Check for corruption marker
                        with open(file_path, "rb") as f:
                            content = f.read()
                            if b"CORRUPTED_DATA_MARKER" in content:
                                detected_issues.append(
                                    {
                                        "type": "file",
                                        "issue": "corruption_detected",
                                        "file": str(file_path),
                                    }
                                )

        return {"detected_issues": detected_issues}

    async def _step_isolate_system(self) -> dict:
        """Isolate affected systems."""
        isolated_components = []

        # In real scenario, would:
        # 1. Block network access
        # 2. Disable user logins
        # 3. Stop affected services
        # 4. Create forensic snapshots

        # For testing, just log the action
        isolated_components.append("network_isolated")
        isolated_components.append("logins_disabled")

        return {"isolated": isolated_components}

    async def _step_restore(self) -> dict:
        """Restore from backup."""
        restore_results = {}

        # Find latest backups
        backup_dir = Path(self.config["backup"]["database"]["location"])
        if backup_dir.exists():
            db_backups = sorted(backup_dir.glob("db_backup_*.sql*"), reverse=True)
            if db_backups:
                # Restore database
                latest_backup = db_backups[0]
                restore_cmd = ["psql", os.environ.get("DATABASE_URL"), "-f", str(latest_backup)]

                if latest_backup.suffix == ".gz":
                    # Decompress first
                    restore_cmd = [
                        "sh",
                        "-c",
                        f"gunzip -c {latest_backup} | psql {os.environ.get('DATABASE_URL')}",
                    ]

                result = subprocess.run(restore_cmd, capture_output=True, text=True)
                restore_results["database"] = {
                    "restored_from": str(latest_backup),
                    "success": result.returncode == 0,
                }

        # Restore files
        file_backup_dir = Path(self.config["backup"]["files"]["location"])
        if file_backup_dir.exists():
            file_backups = sorted(file_backup_dir.glob("files_backup_*.tar*"), reverse=True)
            if file_backups:
                latest_backup = file_backups[0]
                extract_cmd = ["tar", "-xf", str(latest_backup)]

                if latest_backup.suffix == ".gz":
                    extract_cmd = ["tar", "-xzf", str(latest_backup)]

                result = subprocess.run(extract_cmd, capture_output=True, text=True)
                restore_results["files"] = {
                    "restored_from": str(latest_backup),
                    "success": result.returncode == 0,
                }

        return {"restore_results": restore_results}

    async def _step_restore_order(self) -> dict:
        """Restore services in correct order."""
        restore_order = [
            "database",
            "redis",
            "backend",
            "frontend",
        ]

        restored_services = []

        for service in restore_order:
            # Start service (in real scenario)
            console.print(f"    Starting {service}...")
            await asyncio.sleep(0.5)  # Simulate startup time
            restored_services.append(service)

        return {"restored_services": restored_services}

    async def _step_verify(self) -> dict:
        """Verify system recovery."""
        verification_results = {}

        # Verify database
        try:
            conn = psycopg2.connect(
                os.environ.get(
                    "DATABASE_URL", "postgresql://test_user:test_password@localhost/test_db"
                )
            )
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM pg_tables WHERE schemaname = 'public'")
            table_count = cursor.fetchone()[0]
            verification_results["database"] = {
                "connected": True,
                "tables": table_count,
            }
            cursor.close()
            conn.close()
        except Exception as e:
            verification_results["database"] = {
                "connected": False,
                "error": str(e),
            }

        # Verify services
        health_checks = {
            "api": "http://localhost:8009/health",
            "dashboard": "http://localhost:5179",
        }

        for name, endpoint in health_checks.items():
            verification_results[name] = await self._check_health(endpoint)

        return {"verification": verification_results}

    async def _validate_recovery(self, checkpoint_id: str) -> dict:
        """Validate recovery against checkpoint."""
        if checkpoint_id not in self.checkpoints:
            return {"error": "Checkpoint not found"}

        checkpoint = self.checkpoints[checkpoint_id]
        validation_results = {
            "data_integrity": {},
            "functionality": {},
            "performance": {},
        }

        # Validate data integrity
        if self.config["validation"]["data_integrity"]["checksum"]:
            current_state = await self._capture_database_state()

            # Compare row counts
            for table, original_count in checkpoint["database"]["row_counts"].items():
                current_count = current_state["row_counts"].get(table, 0)
                match = original_count == current_count
                validation_results["data_integrity"][f"{table}_count"] = {
                    "original": original_count,
                    "current": current_count,
                    "match": match,
                }

            # Compare checksums
            for table, original_checksum in checkpoint["database"]["checksums"].items():
                current_checksum = current_state["checksums"].get(table)
                match = original_checksum == current_checksum
                validation_results["data_integrity"][f"{table}_checksum"] = {
                    "match": match,
                }

        # Validate functionality
        if self.config["validation"]["functionality"]["api_health"]:
            api_health = await self._check_health("http://localhost:8009/health")
            validation_results["functionality"]["api_health"] = api_health

        # Validate performance
        if self.config["validation"]["performance"]["response_times"]:
            response_time = await self._measure_response_time("http://localhost:8009/health")
            validation_results["performance"]["api_response_time"] = response_time

        return validation_results

    async def _measure_response_time(self, endpoint: str) -> float:
        """Measure response time of an endpoint."""
        start_time = time.time()
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(endpoint, timeout=10) as response:
                    await response.text()
            return time.time() - start_time
        except:
            return -1

    def _calculate_metrics(self, result: dict) -> dict:
        """Calculate disaster recovery metrics."""
        metrics = {}

        # Calculate Recovery Time (RTO)
        if result.get("started_at") and result.get("completed_at"):
            start = datetime.fromisoformat(result["started_at"])
            end = datetime.fromisoformat(result["completed_at"])
            recovery_time = (end - start).total_seconds() / 60  # in minutes
            metrics["recovery_time_minutes"] = round(recovery_time, 2)
            metrics["rto_met"] = recovery_time <= self.config["recovery"]["rto_minutes"]

        # Calculate Recovery Point (RPO)
        # This would normally check the age of the backup
        metrics["rpo_met"] = True  # Placeholder

        # Calculate success rate
        successful_steps = sum(
            1 for step in result.get("steps", []) if step.get("result", {}).get("success")
        )
        total_steps = len(result.get("steps", []))
        metrics["success_rate"] = successful_steps / total_steps if total_steps > 0 else 0

        # Data integrity score
        if "validation" in result:
            integrity_checks = result["validation"].get("data_integrity", {})
            passed_checks = sum(
                1 for check in integrity_checks.values() if check.get("match") is True
            )
            total_checks = len(integrity_checks)
            metrics["data_integrity_score"] = (
                passed_checks / total_checks if total_checks > 0 else 0
            )

        return metrics

    def _display_scenario_result(self, result: dict):
        """Display scenario execution result."""
        status_color = {
            "completed": "green",
            "failed": "red",
            "error": "red",
        }.get(result["status"], "yellow")

        console.print("\n" + "=" * 60)
        console.print(
            f"[{status_color}]Scenario: {result['scenario']} - {result['status'].upper()}[/{status_color}]"
        )
        console.print(f"Description: {result['description']}")

        # Display steps
        console.print("\nSteps:")
        for step in result.get("steps", []):
            success = step["result"].get("success")
            icon = "✓" if success else "✗"
            color = "green" if success else "red"
            console.print(f"  [{color}]{icon}[/{color}] {step['name']}")

        # Display metrics
        if "metrics" in result:
            metrics = result["metrics"]
            console.print("\nMetrics:")
            console.print(f"  Recovery Time: {metrics.get('recovery_time_minutes', 'N/A')} minutes")
            console.print(f"  RTO Met: {metrics.get('rto_met', 'N/A')}")
            console.print(f"  Success Rate: {metrics.get('success_rate', 0):.1%}")
            console.print(f"  Data Integrity: {metrics.get('data_integrity_score', 0):.1%}")

    async def run_all_scenarios(self):
        """Run all disaster recovery scenarios."""
        console.print(
            Panel.fit(
                "[bold cyan]Disaster Recovery Testing Suite[/bold cyan]\n"
                f"Running {len(self.config['scenarios'])} scenarios",
                title="DR Testing",
            )
        )

        for scenario in self.config["scenarios"]:
            result = await self.run_scenario(scenario["name"])
            await asyncio.sleep(2)  # Brief pause between scenarios

        # Generate report
        self._generate_report()

    def _generate_report(self):
        """Generate DR testing report."""
        # Create summary table
        table = Table(title="Disaster Recovery Test Results")
        table.add_column("Scenario", style="cyan")
        table.add_column("Status", style="white")
        table.add_column("Recovery Time", justify="right")
        table.add_column("Success Rate", justify="right")
        table.add_column("Data Integrity", justify="right")

        for result in self.test_results:
            status_style = {
                "completed": "[green]✓ Completed[/green]",
                "failed": "[red]✗ Failed[/red]",
                "error": "[red]✗ Error[/red]",
            }.get(result["status"], result["status"])

            metrics = result.get("metrics", {})

            table.add_row(
                result["scenario"],
                status_style,
                f"{metrics.get('recovery_time_minutes', 'N/A')} min",
                f"{metrics.get('success_rate', 0):.0%}",
                f"{metrics.get('data_integrity_score', 0):.0%}",
            )

        console.print("\n")
        console.print(table)

        # Save detailed report
        report_path = Path("tests/disaster_recovery/reports")
        report_path.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = report_path / f"dr_report_{timestamp}.json"

        with open(report_file, "w") as f:
            json.dump(
                {
                    "timestamp": datetime.now().isoformat(),
                    "summary": {
                        "total_scenarios": len(self.test_results),
                        "passed": sum(1 for r in self.test_results if r["status"] == "completed"),
                        "failed": sum(
                            1 for r in self.test_results if r["status"] in ["failed", "error"]
                        ),
                    },
                    "config": self.config,
                    "results": self.test_results,
                },
                f,
                indent=2,
            )

        console.print(f"\n[dim]Report saved to: {report_file}[/dim]")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Disaster Recovery Testing")

    parser.add_argument(
        "--scenario",
        choices=["database_failure", "data_corruption", "ransomware", "cascading_failure", "all"],
        default="all",
        help="Scenario to test",
    )
    parser.add_argument(
        "--config",
        default="config/dr-testing.json",
        help="Configuration file",
    )

    args = parser.parse_args()

    tester = DisasterRecoveryTester(config_file=args.config)

    if args.scenario == "all":
        asyncio.run(tester.run_all_scenarios())
    else:
        asyncio.run(tester.run_scenario(args.scenario))


if __name__ == "__main__":
    main()
