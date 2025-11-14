"""
Resource Monitor Agent for system resource tracking and optimization.

This agent monitors CPU, memory, disk, and network usage across worktrees
and agents, providing insights and recommendations for optimization.

Author: ToolboxAI Team
Created: 2025-09-17
Version: 1.0.0
"""

import asyncio
import logging
import subprocess
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Optional

import psutil

from core.agents.base_agent import AgentConfig, BaseAgent, TaskResult

logger = logging.getLogger(__name__)


@dataclass
class ResourceSnapshot:
    """Snapshot of system resources at a point in time."""

    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    memory_used_mb: float
    memory_available_mb: float
    disk_usage_percent: float
    disk_free_gb: float
    network_sent_mb: float
    network_recv_mb: float
    process_count: int
    thread_count: int
    open_files: int


@dataclass
class WorktreeResources:
    """Resource usage for a specific worktree."""

    worktree_path: Path
    branch_name: str
    cpu_percent: float
    memory_mb: float
    disk_usage_mb: float
    process_pids: list[int]
    port_usage: dict[int, str]  # port -> process name
    last_updated: datetime


@dataclass
class AgentResources:
    """Resource usage for a specific agent."""

    agent_id: str
    agent_type: str
    cpu_percent: float
    memory_mb: float
    execution_time: float
    task_count: int
    error_count: int
    last_activity: datetime


@dataclass
class ResourceAlert:
    """Alert for resource issues."""

    alert_id: str
    severity: str  # critical, warning, info
    resource_type: str  # cpu, memory, disk, network
    message: str
    value: float
    threshold: float
    timestamp: datetime
    resolved: bool = False


class ResourceMonitorAgent(BaseAgent):
    """Monitors and optimizes system resource usage."""

    def __init__(self, config: Optional[AgentConfig] = None):
        """Initialize the resource monitor agent.

        Args:
            config: Agent configuration
        """
        if config is None:
            config = AgentConfig(
                name="ResourceMonitorAgent",
                model="gpt-3.5-turbo",
                temperature=0.1,
                verbose=False,
            )
        super().__init__(config)

        # Monitoring configuration
        self.monitoring_interval = 10  # seconds
        self.history_size = 100  # number of snapshots to keep
        self.alert_thresholds = {
            "cpu_critical": 90.0,
            "cpu_warning": 75.0,
            "memory_critical": 90.0,
            "memory_warning": 80.0,
            "disk_critical": 95.0,
            "disk_warning": 85.0,
        }

        # Resource tracking
        self.resource_history: list[ResourceSnapshot] = []
        self.worktree_resources: dict[str, WorktreeResources] = {}
        self.agent_resources: dict[str, AgentResources] = {}
        self.active_alerts: list[ResourceAlert] = []

        # Port ranges for monitoring
        self.backend_port_range = (8008, 8028)
        self.frontend_port_range = (5179, 5199)

        # Metrics
        self.metrics = {
            "snapshots_collected": 0,
            "alerts_generated": 0,
            "optimizations_applied": 0,
            "monitoring_uptime": 0.0,
        }

        self.monitoring_task: Optional[asyncio.Task] = None
        self.start_time = datetime.now()

    async def _process_task(self, task: dict[str, Any]) -> TaskResult:
        """Process a task (required by BaseAgent).

        Args:
            task: Task to process

        Returns:
            Task result
        """
        return await self.execute(task)

    async def execute(self, task: dict[str, Any]) -> TaskResult:
        """Execute resource monitoring task.

        Args:
            task: Task configuration

        Returns:
            Task result
        """
        action = task.get("action", "monitor")

        try:
            if action == "monitor":
                return await self.monitor_resources()
            elif action == "analyze":
                return await self.analyze_usage()
            elif action == "optimize":
                return await self.optimize_resources()
            elif action == "get_status":
                return await self.get_resource_status()
            elif action == "get_alerts":
                return await self.get_alerts()
            elif action == "check_worktree":
                worktree_path = task.get("worktree_path")
                return await self.monitor_worktree(worktree_path)
            elif action == "check_agent":
                agent_id = task.get("agent_id")
                return await self.monitor_agent(agent_id)
            elif action == "start_monitoring":
                return await self.start_continuous_monitoring()
            elif action == "stop_monitoring":
                return await self.stop_continuous_monitoring()
            else:
                return TaskResult(success=False, output=None, error=f"Unknown action: {action}")
        except Exception as e:
            logger.error(f"Error executing resource monitor task: {e}")
            return TaskResult(success=False, output=None, error=str(e))

    async def monitor_resources(self) -> TaskResult:
        """Monitor current system resources.

        Returns:
            Current resource snapshot
        """
        try:
            snapshot = await self._collect_resource_snapshot()
            self.resource_history.append(snapshot)

            # Trim history if needed
            if len(self.resource_history) > self.history_size:
                self.resource_history = self.resource_history[-self.history_size :]

            # Check for alerts
            await self._check_alerts(snapshot)

            # Update metrics
            self.metrics["snapshots_collected"] += 1

            return TaskResult(
                success=True,
                output={
                    "snapshot": self._snapshot_to_dict(snapshot),
                    "active_alerts": len(self.active_alerts),
                },
            )

        except Exception as e:
            return TaskResult(success=False, output=None, error=str(e))

    async def _collect_resource_snapshot(self) -> ResourceSnapshot:
        """Collect current resource snapshot.

        Returns:
            Resource snapshot
        """
        # CPU usage
        cpu_percent = psutil.cpu_percent(interval=1)

        # Memory usage
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        memory_used_mb = memory.used / (1024 * 1024)
        memory_available_mb = memory.available / (1024 * 1024)

        # Disk usage
        disk = psutil.disk_usage("/")
        disk_usage_percent = disk.percent
        disk_free_gb = disk.free / (1024 * 1024 * 1024)

        # Network usage
        network = psutil.net_io_counters()
        network_sent_mb = network.bytes_sent / (1024 * 1024)
        network_recv_mb = network.bytes_recv / (1024 * 1024)

        # Process info
        process_count = len(psutil.pids())
        thread_count = psutil.cpu_count()
        open_files = len(psutil.Process().open_files())

        return ResourceSnapshot(
            timestamp=datetime.now(),
            cpu_percent=cpu_percent,
            memory_percent=memory_percent,
            memory_used_mb=memory_used_mb,
            memory_available_mb=memory_available_mb,
            disk_usage_percent=disk_usage_percent,
            disk_free_gb=disk_free_gb,
            network_sent_mb=network_sent_mb,
            network_recv_mb=network_recv_mb,
            process_count=process_count,
            thread_count=thread_count,
            open_files=open_files,
        )

    async def monitor_worktree(self, worktree_path: str) -> TaskResult:
        """Monitor resources for a specific worktree.

        Args:
            worktree_path: Path to the worktree

        Returns:
            Worktree resource usage
        """
        try:
            path = Path(worktree_path)
            if not path.exists():
                return TaskResult(
                    success=False,
                    output=None,
                    error=f"Worktree path does not exist: {worktree_path}",
                )

            # Get branch name
            branch_cmd = ["git", "rev-parse", "--abbrev-ref", "HEAD"]
            result = subprocess.run(branch_cmd, cwd=str(path), capture_output=True, text=True)
            branch_name = result.stdout.strip() if result.returncode == 0 else "unknown"

            # Collect process information
            pids = []
            cpu_total = 0.0
            memory_total = 0.0

            # Find processes using the worktree path
            for proc in psutil.process_iter(["pid", "name", "cpu_percent", "memory_info", "cwd"]):
                try:
                    if proc.info["cwd"] and str(path) in proc.info["cwd"]:
                        pids.append(proc.info["pid"])
                        cpu_total += proc.info["cpu_percent"]
                        memory_total += proc.info["memory_info"].rss / (1024 * 1024)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue

            # Check port usage
            port_usage = await self._check_port_usage(path)

            # Calculate disk usage
            disk_usage_mb = sum(f.stat().st_size for f in path.rglob("*") if f.is_file()) / (
                1024 * 1024
            )

            resources = WorktreeResources(
                worktree_path=path,
                branch_name=branch_name,
                cpu_percent=cpu_total,
                memory_mb=memory_total,
                disk_usage_mb=disk_usage_mb,
                process_pids=pids,
                port_usage=port_usage,
                last_updated=datetime.now(),
            )

            self.worktree_resources[str(path)] = resources

            return TaskResult(success=True, output=self._worktree_resources_to_dict(resources))

        except Exception as e:
            return TaskResult(success=False, output=None, error=str(e))

    async def _check_port_usage(self, worktree_path: Path) -> dict[int, str]:
        """Check port usage for a worktree.

        Args:
            worktree_path: Path to the worktree

        Returns:
            Dictionary of port -> process name
        """
        port_usage = {}

        # Check backend ports
        for port in range(*self.backend_port_range):
            try:
                for conn in psutil.net_connections():
                    if conn.laddr.port == port and conn.status == "LISTEN":
                        try:
                            proc = psutil.Process(conn.pid)
                            port_usage[port] = proc.name()
                        except (psutil.NoSuchProcess, psutil.AccessDenied):
                            port_usage[port] = "unknown"
            except Exception:
                continue

        # Check frontend ports
        for port in range(*self.frontend_port_range):
            try:
                for conn in psutil.net_connections():
                    if conn.laddr.port == port and conn.status == "LISTEN":
                        try:
                            proc = psutil.Process(conn.pid)
                            port_usage[port] = proc.name()
                        except (psutil.NoSuchProcess, psutil.AccessDenied):
                            port_usage[port] = "unknown"
            except Exception:
                continue

        return port_usage

    async def monitor_agent(self, agent_id: str) -> TaskResult:
        """Monitor resources for a specific agent.

        Args:
            agent_id: ID of the agent

        Returns:
            Agent resource usage
        """
        # This would need integration with the agent system
        # For now, return a placeholder
        return TaskResult(
            success=True,
            data={
                "agent_id": agent_id,
                "message": "Agent monitoring not yet implemented",
            },
        )

    async def analyze_usage(self) -> TaskResult:
        """Analyze resource usage patterns.

        Returns:
            Analysis results
        """
        if len(self.resource_history) < 2:
            return TaskResult(success=False, output=None, error="Insufficient history for analysis")

        # Calculate statistics
        cpu_values = [s.cpu_percent for s in self.resource_history]
        memory_values = [s.memory_percent for s in self.resource_history]
        disk_values = [s.disk_usage_percent for s in self.resource_history]

        analysis = {
            "cpu": {
                "average": sum(cpu_values) / len(cpu_values),
                "max": max(cpu_values),
                "min": min(cpu_values),
                "current": cpu_values[-1],
                "trend": "increasing" if cpu_values[-1] > cpu_values[0] else "decreasing",
            },
            "memory": {
                "average": sum(memory_values) / len(memory_values),
                "max": max(memory_values),
                "min": min(memory_values),
                "current": memory_values[-1],
                "trend": "increasing" if memory_values[-1] > memory_values[0] else "decreasing",
            },
            "disk": {
                "average": sum(disk_values) / len(disk_values),
                "max": max(disk_values),
                "min": min(disk_values),
                "current": disk_values[-1],
                "trend": "increasing" if disk_values[-1] > disk_values[0] else "decreasing",
            },
            "patterns": self._identify_patterns(),
            "recommendations": self._generate_recommendations(),
        }

        return TaskResult(success=True, output=analysis)

    def _identify_patterns(self) -> list[str]:
        """Identify resource usage patterns.

        Returns:
            List of identified patterns
        """
        patterns = []

        if len(self.resource_history) < 5:
            return patterns

        # Check for consistent high CPU usage
        recent_cpu = [s.cpu_percent for s in self.resource_history[-5:]]
        if all(cpu > self.alert_thresholds["cpu_warning"] for cpu in recent_cpu):
            patterns.append("Sustained high CPU usage")

        # Check for memory leaks
        memory_values = [s.memory_used_mb for s in self.resource_history]
        if len(memory_values) > 10:
            memory_increase = memory_values[-1] - memory_values[-10]
            if memory_increase > 1000:  # 1GB increase
                patterns.append("Potential memory leak detected")

        # Check for disk space consumption
        if self.resource_history[-1].disk_usage_percent > self.alert_thresholds["disk_warning"]:
            patterns.append("High disk usage")

        # Check for process proliferation
        if self.resource_history[-1].process_count > self.resource_history[0].process_count * 2:
            patterns.append("Significant increase in process count")

        return patterns

    def _generate_recommendations(self) -> list[str]:
        """Generate optimization recommendations.

        Returns:
            List of recommendations
        """
        recommendations = []

        if not self.resource_history:
            return recommendations

        latest = self.resource_history[-1]

        # CPU recommendations
        if latest.cpu_percent > self.alert_thresholds["cpu_warning"]:
            recommendations.append("Consider reducing concurrent tasks or scaling horizontally")

        # Memory recommendations
        if latest.memory_percent > self.alert_thresholds["memory_warning"]:
            recommendations.append("Free up memory by closing unused applications or worktrees")

        # Disk recommendations
        if latest.disk_usage_percent > self.alert_thresholds["disk_warning"]:
            recommendations.append("Clean up disk space: remove old worktrees, clear caches")

        # Worktree recommendations
        if len(self.worktree_resources) > 5:
            recommendations.append("Consider consolidating worktrees to reduce resource usage")

        # Port recommendations
        used_ports = sum(len(wr.port_usage) for wr in self.worktree_resources.values())
        if used_ports > 15:
            recommendations.append("Many ports in use; consider cleanup of unused services")

        return recommendations

    async def optimize_resources(self) -> TaskResult:
        """Apply resource optimizations.

        Returns:
            Optimization results
        """
        optimizations = []

        try:
            # Clean up old log files
            log_cleanup = await self._cleanup_logs()
            if log_cleanup["freed_mb"] > 0:
                optimizations.append(f"Cleaned up {log_cleanup['freed_mb']} MB of logs")

            # Clear caches
            cache_cleanup = await self._clear_caches()
            if cache_cleanup["freed_mb"] > 0:
                optimizations.append(f"Cleared {cache_cleanup['freed_mb']} MB of caches")

            # Kill zombie processes
            zombie_cleanup = await self._cleanup_zombie_processes()
            if zombie_cleanup["killed"] > 0:
                optimizations.append(f"Killed {zombie_cleanup['killed']} zombie processes")

            # Suggest idle worktree removal
            idle_worktrees = self._find_idle_worktrees()
            if idle_worktrees:
                optimizations.append(f"Found {len(idle_worktrees)} idle worktrees for cleanup")

            self.metrics["optimizations_applied"] += len(optimizations)

            return TaskResult(
                success=True,
                output={
                    "optimizations": optimizations,
                    "idle_worktrees": idle_worktrees,
                },
            )

        except Exception as e:
            return TaskResult(success=False, output=None, error=str(e))

    async def _cleanup_logs(self) -> dict[str, Any]:
        """Clean up old log files.

        Returns:
            Cleanup statistics
        """
        freed_mb = 0
        log_dirs = [
            Path("/Volumes/G-DRIVE ArmorATD/Development/Clients/ToolBoxAI-Solutions/logs"),
            Path("/Volumes/G-DRIVE ArmorATD/Development/Clients/ToolBoxAI-Solutions-worktrees"),
        ]

        for log_dir in log_dirs:
            if log_dir.exists():
                # Find old log files (>7 days)
                cutoff = datetime.now() - timedelta(days=7)
                for log_file in log_dir.rglob("*.log"):
                    try:
                        if datetime.fromtimestamp(log_file.stat().st_mtime) < cutoff:
                            size_mb = log_file.stat().st_size / (1024 * 1024)
                            log_file.unlink()
                            freed_mb += size_mb
                    except Exception as e:
                        logger.warning(f"Could not delete log file {log_file}: {e}")

        return {"freed_mb": freed_mb}

    async def _clear_caches(self) -> dict[str, Any]:
        """Clear cache directories.

        Returns:
            Cache cleanup statistics
        """
        freed_mb = 0
        cache_dirs = [
            Path.home() / ".cache" / "toolboxai",
            Path("/Volumes/G-DRIVE ArmorATD/Development/Clients/ToolBoxAI-Solutions/.cache"),
        ]

        for cache_dir in cache_dirs:
            if cache_dir.exists():
                try:
                    for cache_file in cache_dir.rglob("*"):
                        if cache_file.is_file():
                            size_mb = cache_file.stat().st_size / (1024 * 1024)
                            cache_file.unlink()
                            freed_mb += size_mb
                except Exception as e:
                    logger.warning(f"Could not clear cache {cache_dir}: {e}")

        return {"freed_mb": freed_mb}

    async def _cleanup_zombie_processes(self) -> dict[str, int]:
        """Clean up zombie processes.

        Returns:
            Number of processes killed
        """
        killed = 0

        for proc in psutil.process_iter(["pid", "status"]):
            try:
                if proc.info["status"] == psutil.STATUS_ZOMBIE:
                    proc.kill()
                    killed += 1
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        return {"killed": killed}

    def _find_idle_worktrees(self) -> list[str]:
        """Find idle worktrees.

        Returns:
            List of idle worktree paths
        """
        idle_worktrees = []
        idle_threshold = timedelta(minutes=30)
        now = datetime.now()

        for path, resources in self.worktree_resources.items():
            if resources.last_updated:
                idle_time = now - resources.last_updated
                if idle_time > idle_threshold and resources.cpu_percent < 1.0:
                    idle_worktrees.append(path)

        return idle_worktrees

    async def _check_alerts(self, snapshot: ResourceSnapshot):
        """Check for resource alerts.

        Args:
            snapshot: Current resource snapshot
        """
        # Check CPU alerts
        if snapshot.cpu_percent > self.alert_thresholds["cpu_critical"]:
            self._create_alert(
                "critical",
                "cpu",
                f"CPU usage critical: {snapshot.cpu_percent:.1f}%",
                snapshot.cpu_percent,
                self.alert_thresholds["cpu_critical"],
            )
        elif snapshot.cpu_percent > self.alert_thresholds["cpu_warning"]:
            self._create_alert(
                "warning",
                "cpu",
                f"CPU usage high: {snapshot.cpu_percent:.1f}%",
                snapshot.cpu_percent,
                self.alert_thresholds["cpu_warning"],
            )

        # Check memory alerts
        if snapshot.memory_percent > self.alert_thresholds["memory_critical"]:
            self._create_alert(
                "critical",
                "memory",
                f"Memory usage critical: {snapshot.memory_percent:.1f}%",
                snapshot.memory_percent,
                self.alert_thresholds["memory_critical"],
            )
        elif snapshot.memory_percent > self.alert_thresholds["memory_warning"]:
            self._create_alert(
                "warning",
                "memory",
                f"Memory usage high: {snapshot.memory_percent:.1f}%",
                snapshot.memory_percent,
                self.alert_thresholds["memory_warning"],
            )

        # Check disk alerts
        if snapshot.disk_usage_percent > self.alert_thresholds["disk_critical"]:
            self._create_alert(
                "critical",
                "disk",
                f"Disk usage critical: {snapshot.disk_usage_percent:.1f}%",
                snapshot.disk_usage_percent,
                self.alert_thresholds["disk_critical"],
            )
        elif snapshot.disk_usage_percent > self.alert_thresholds["disk_warning"]:
            self._create_alert(
                "warning",
                "disk",
                f"Disk usage high: {snapshot.disk_usage_percent:.1f}%",
                snapshot.disk_usage_percent,
                self.alert_thresholds["disk_warning"],
            )

    def _create_alert(
        self,
        severity: str,
        resource_type: str,
        message: str,
        value: float,
        threshold: float,
    ):
        """Create a resource alert.

        Args:
            severity: Alert severity
            resource_type: Type of resource
            message: Alert message
            value: Current value
            threshold: Threshold value
        """
        alert = ResourceAlert(
            alert_id=str(uuid.uuid4()),
            severity=severity,
            resource_type=resource_type,
            message=message,
            value=value,
            threshold=threshold,
            timestamp=datetime.now(),
        )

        self.active_alerts.append(alert)
        self.metrics["alerts_generated"] += 1

        logger.warning(f"Resource alert: {message}")

    async def get_alerts(self) -> TaskResult:
        """Get active alerts.

        Returns:
            List of active alerts
        """
        # Filter out resolved alerts
        active = [a for a in self.active_alerts if not a.resolved]

        return TaskResult(
            success=True,
            data={
                "alerts": [self._alert_to_dict(a) for a in active],
                "count": len(active),
            },
        )

    async def get_resource_status(self) -> TaskResult:
        """Get current resource status.

        Returns:
            Comprehensive resource status
        """
        latest_snapshot = self.resource_history[-1] if self.resource_history else None

        status = {
            "current": self._snapshot_to_dict(latest_snapshot) if latest_snapshot else None,
            "worktrees": {
                path: self._worktree_resources_to_dict(resources)
                for path, resources in self.worktree_resources.items()
            },
            "alerts": len([a for a in self.active_alerts if not a.resolved]),
            "metrics": self.metrics,
            "uptime": (datetime.now() - self.start_time).total_seconds(),
        }

        return TaskResult(success=True, output=status)

    async def start_continuous_monitoring(self) -> TaskResult:
        """Start continuous resource monitoring.

        Returns:
            Success status
        """
        if self.monitoring_task and not self.monitoring_task.done():
            return TaskResult(success=False, output=None, error="Monitoring already running")

        self.monitoring_task = asyncio.create_task(self._monitoring_loop())
        return TaskResult(success=True, output={"message": "Monitoring started"})

    async def stop_continuous_monitoring(self) -> TaskResult:
        """Stop continuous resource monitoring.

        Returns:
            Success status
        """
        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass
            self.monitoring_task = None

        return TaskResult(success=True, output={"message": "Monitoring stopped"})

    async def _monitoring_loop(self):
        """Continuous monitoring loop."""
        while True:
            try:
                await self.monitor_resources()
                await asyncio.sleep(self.monitoring_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(self.monitoring_interval)

    def _snapshot_to_dict(self, snapshot: ResourceSnapshot) -> dict[str, Any]:
        """Convert snapshot to dictionary.

        Args:
            snapshot: Resource snapshot

        Returns:
            Dictionary representation
        """
        if not snapshot:
            return {}

        return {
            "timestamp": snapshot.timestamp.isoformat(),
            "cpu_percent": snapshot.cpu_percent,
            "memory_percent": snapshot.memory_percent,
            "memory_used_mb": snapshot.memory_used_mb,
            "memory_available_mb": snapshot.memory_available_mb,
            "disk_usage_percent": snapshot.disk_usage_percent,
            "disk_free_gb": snapshot.disk_free_gb,
            "network_sent_mb": snapshot.network_sent_mb,
            "network_recv_mb": snapshot.network_recv_mb,
            "process_count": snapshot.process_count,
            "thread_count": snapshot.thread_count,
            "open_files": snapshot.open_files,
        }

    def _worktree_resources_to_dict(self, resources: WorktreeResources) -> dict[str, Any]:
        """Convert worktree resources to dictionary.

        Args:
            resources: Worktree resources

        Returns:
            Dictionary representation
        """
        return {
            "branch_name": resources.branch_name,
            "cpu_percent": resources.cpu_percent,
            "memory_mb": resources.memory_mb,
            "disk_usage_mb": resources.disk_usage_mb,
            "process_count": len(resources.process_pids),
            "port_usage": resources.port_usage,
            "last_updated": resources.last_updated.isoformat(),
        }

    def _alert_to_dict(self, alert: ResourceAlert) -> dict[str, Any]:
        """Convert alert to dictionary.

        Args:
            alert: Resource alert

        Returns:
            Dictionary representation
        """
        return {
            "alert_id": alert.alert_id,
            "severity": alert.severity,
            "resource_type": alert.resource_type,
            "message": alert.message,
            "value": alert.value,
            "threshold": alert.threshold,
            "timestamp": alert.timestamp.isoformat(),
            "resolved": alert.resolved,
        }

    def get_report(self) -> dict[str, Any]:
        """Generate a resource monitoring report.

        Returns:
            Report data
        """
        return {
            "agent": "ResourceMonitorAgent",
            "status": "operational",
            "monitoring": {
                "snapshots_collected": self.metrics["snapshots_collected"],
                "alerts_generated": self.metrics["alerts_generated"],
                "optimizations_applied": self.metrics["optimizations_applied"],
                "active_alerts": len([a for a in self.active_alerts if not a.resolved]),
            },
            "resources": {
                "worktrees_monitored": len(self.worktree_resources),
                "agents_monitored": len(self.agent_resources),
            },
            "uptime": (datetime.now() - self.start_time).total_seconds(),
        }


# Import uuid for alert IDs
import uuid
