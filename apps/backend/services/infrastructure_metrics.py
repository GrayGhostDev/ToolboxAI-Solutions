"""
Infrastructure Metrics Service

Comprehensive infrastructure monitoring and metrics collection service
for the ToolboxAI platform. Provides detailed system metrics, container
health, service status, and resource utilization.

Created: October 1, 2025
"""

import asyncio
import psutil
import platform
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
import logging
import structlog
from dataclasses import dataclass, asdict
from enum import Enum

logger = structlog.get_logger(__name__)


class ServiceStatus(str, Enum):
    """Service health status"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class MetricType(str, Enum):
    """Metric type classification"""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"


@dataclass
class SystemMetrics:
    """System-level metrics"""
    cpu_percent: float
    cpu_count: int
    cpu_freq_current: float
    memory_total_gb: float
    memory_available_gb: float
    memory_used_gb: float
    memory_percent: float
    disk_total_gb: float
    disk_used_gb: float
    disk_free_gb: float
    disk_percent: float
    network_bytes_sent: int
    network_bytes_recv: int
    network_connections: int
    uptime_seconds: float
    boot_time: datetime
    timestamp: datetime


@dataclass
class ProcessMetrics:
    """Process-level metrics"""
    pid: int
    name: str
    cpu_percent: float
    memory_mb: float
    memory_percent: float
    num_threads: int
    num_fds: int  # File descriptors
    status: str
    create_time: datetime
    timestamp: datetime


@dataclass
class ServiceHealth:
    """Service health information"""
    name: str
    status: ServiceStatus
    uptime_seconds: float
    last_check: datetime
    response_time_ms: float
    error_count: int
    success_rate: float
    metadata: Dict[str, Any]


class InfrastructureMetricsCollector:
    """
    Comprehensive infrastructure metrics collector

    Collects and aggregates system, process, and service metrics
    for monitoring and observability.
    """

    def __init__(self):
        self.boot_time = datetime.fromtimestamp(psutil.boot_time(), tz=timezone.utc)
        self.process = psutil.Process()
        self._metrics_history: List[SystemMetrics] = []
        self._max_history_size = 1000  # Keep last 1000 samples

    async def collect_system_metrics(self) -> SystemMetrics:
        """
        Collect comprehensive system-level metrics

        Returns:
            SystemMetrics object with current system state
        """
        try:
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=0.1)
            cpu_count = psutil.cpu_count()
            cpu_freq = psutil.cpu_freq()
            cpu_freq_current = cpu_freq.current if cpu_freq else 0.0

            # Memory metrics
            memory = psutil.virtual_memory()
            memory_total_gb = memory.total / (1024 ** 3)
            memory_available_gb = memory.available / (1024 ** 3)
            memory_used_gb = memory.used / (1024 ** 3)
            memory_percent = memory.percent

            # Disk metrics
            disk = psutil.disk_usage('/')
            disk_total_gb = disk.total / (1024 ** 3)
            disk_used_gb = disk.used / (1024 ** 3)
            disk_free_gb = disk.free / (1024 ** 3)
            disk_percent = disk.percent

            # Network metrics
            net_io = psutil.net_io_counters()
            network_bytes_sent = net_io.bytes_sent
            network_bytes_recv = net_io.bytes_recv

            # Connection metrics
            try:
                network_connections = len(psutil.net_connections())
            except (psutil.AccessDenied, psutil.NoSuchProcess):
                network_connections = 0

            # Uptime
            uptime_seconds = (datetime.now(timezone.utc) - self.boot_time).total_seconds()

            metrics = SystemMetrics(
                cpu_percent=cpu_percent,
                cpu_count=cpu_count,
                cpu_freq_current=cpu_freq_current,
                memory_total_gb=round(memory_total_gb, 2),
                memory_available_gb=round(memory_available_gb, 2),
                memory_used_gb=round(memory_used_gb, 2),
                memory_percent=round(memory_percent, 2),
                disk_total_gb=round(disk_total_gb, 2),
                disk_used_gb=round(disk_used_gb, 2),
                disk_free_gb=round(disk_free_gb, 2),
                disk_percent=round(disk_percent, 2),
                network_bytes_sent=network_bytes_sent,
                network_bytes_recv=network_bytes_recv,
                network_connections=network_connections,
                uptime_seconds=round(uptime_seconds, 2),
                boot_time=self.boot_time,
                timestamp=datetime.now(timezone.utc)
            )

            # Store in history
            self._metrics_history.append(metrics)
            if len(self._metrics_history) > self._max_history_size:
                self._metrics_history.pop(0)

            return metrics

        except Exception as e:
            logger.error("Failed to collect system metrics", error=str(e))
            raise

    async def collect_process_metrics(self) -> ProcessMetrics:
        """
        Collect current process metrics

        Returns:
            ProcessMetrics object with current process state
        """
        try:
            with self.process.oneshot():
                cpu_percent = self.process.cpu_percent()
                memory_info = self.process.memory_info()
                memory_mb = memory_info.rss / (1024 * 1024)
                memory_percent = self.process.memory_percent()
                num_threads = self.process.num_threads()

                # File descriptors (Unix-like systems)
                try:
                    num_fds = self.process.num_fds()
                except (AttributeError, psutil.AccessDenied):
                    num_fds = 0

                metrics = ProcessMetrics(
                    pid=self.process.pid,
                    name=self.process.name(),
                    cpu_percent=round(cpu_percent, 2),
                    memory_mb=round(memory_mb, 2),
                    memory_percent=round(memory_percent, 2),
                    num_threads=num_threads,
                    num_fds=num_fds,
                    status=self.process.status(),
                    create_time=datetime.fromtimestamp(
                        self.process.create_time(),
                        tz=timezone.utc
                    ),
                    timestamp=datetime.now(timezone.utc)
                )

            return metrics

        except Exception as e:
            logger.error("Failed to collect process metrics", error=str(e))
            raise

    async def get_platform_info(self) -> Dict[str, Any]:
        """
        Get platform and environment information

        Returns:
            Dictionary with platform details
        """
        return {
            "system": platform.system(),
            "release": platform.release(),
            "version": platform.version(),
            "machine": platform.machine(),
            "processor": platform.processor(),
            "python_version": platform.python_version(),
            "hostname": platform.node(),
            "architecture": platform.architecture()[0],
        }

    async def get_metrics_summary(
        self,
        time_window_minutes: int = 5
    ) -> Dict[str, Any]:
        """
        Get summarized metrics over a time window

        Args:
            time_window_minutes: Time window for aggregation

        Returns:
            Dictionary with aggregated metrics
        """
        if not self._metrics_history:
            return {}

        cutoff_time = datetime.now(timezone.utc) - timedelta(minutes=time_window_minutes)
        recent_metrics = [
            m for m in self._metrics_history
            if m.timestamp >= cutoff_time
        ]

        if not recent_metrics:
            return {}

        cpu_values = [m.cpu_percent for m in recent_metrics]
        memory_values = [m.memory_percent for m in recent_metrics]
        disk_values = [m.disk_percent for m in recent_metrics]

        return {
            "time_window_minutes": time_window_minutes,
            "sample_count": len(recent_metrics),
            "cpu": {
                "avg": round(sum(cpu_values) / len(cpu_values), 2),
                "min": round(min(cpu_values), 2),
                "max": round(max(cpu_values), 2),
            },
            "memory": {
                "avg": round(sum(memory_values) / len(memory_values), 2),
                "min": round(min(memory_values), 2),
                "max": round(max(memory_values), 2),
            },
            "disk": {
                "avg": round(sum(disk_values) / len(disk_values), 2),
                "min": round(min(disk_values), 2),
                "max": round(max(disk_values), 2),
            },
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    async def check_resource_thresholds(self) -> Dict[str, Any]:
        """
        Check if resources are within acceptable thresholds

        Returns:
            Dictionary with threshold check results
        """
        metrics = await self.collect_system_metrics()

        # Define thresholds
        THRESHOLDS = {
            "cpu_warning": 70.0,
            "cpu_critical": 90.0,
            "memory_warning": 75.0,
            "memory_critical": 90.0,
            "disk_warning": 80.0,
            "disk_critical": 95.0,
        }

        warnings = []
        critical = []

        # Check CPU
        if metrics.cpu_percent >= THRESHOLDS["cpu_critical"]:
            critical.append(f"CPU usage critical: {metrics.cpu_percent}%")
        elif metrics.cpu_percent >= THRESHOLDS["cpu_warning"]:
            warnings.append(f"CPU usage high: {metrics.cpu_percent}%")

        # Check Memory
        if metrics.memory_percent >= THRESHOLDS["memory_critical"]:
            critical.append(f"Memory usage critical: {metrics.memory_percent}%")
        elif metrics.memory_percent >= THRESHOLDS["memory_warning"]:
            warnings.append(f"Memory usage high: {metrics.memory_percent}%")

        # Check Disk
        if metrics.disk_percent >= THRESHOLDS["disk_critical"]:
            critical.append(f"Disk usage critical: {metrics.disk_percent}%")
        elif metrics.disk_percent >= THRESHOLDS["disk_warning"]:
            warnings.append(f"Disk usage high: {metrics.disk_percent}%")

        # Determine overall status
        if critical:
            status = ServiceStatus.UNHEALTHY
        elif warnings:
            status = ServiceStatus.DEGRADED
        else:
            status = ServiceStatus.HEALTHY

        return {
            "status": status.value,
            "warnings": warnings,
            "critical": critical,
            "thresholds": THRESHOLDS,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    async def get_comprehensive_report(self) -> Dict[str, Any]:
        """
        Generate comprehensive infrastructure report

        Returns:
            Complete infrastructure status report
        """
        try:
            # Collect all metrics concurrently
            system_metrics, process_metrics, platform_info, threshold_check = await asyncio.gather(
                self.collect_system_metrics(),
                self.collect_process_metrics(),
                self.get_platform_info(),
                self.check_resource_thresholds(),
                return_exceptions=True
            )

            # Get 5-minute summary
            metrics_summary = await self.get_metrics_summary(time_window_minutes=5)

            return {
                "status": "success",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "platform": platform_info if not isinstance(platform_info, Exception) else {},
                "system": asdict(system_metrics) if not isinstance(system_metrics, Exception) else {},
                "process": asdict(process_metrics) if not isinstance(process_metrics, Exception) else {},
                "threshold_check": threshold_check if not isinstance(threshold_check, Exception) else {},
                "metrics_summary": metrics_summary,
                "health_score": self._calculate_health_score(system_metrics, threshold_check)
            }

        except Exception as e:
            logger.error("Failed to generate comprehensive report", error=str(e))
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

    def _calculate_health_score(
        self,
        system_metrics: SystemMetrics,
        threshold_check: Dict[str, Any]
    ) -> float:
        """
        Calculate overall infrastructure health score (0-100)

        Args:
            system_metrics: Current system metrics
            threshold_check: Threshold check results

        Returns:
            Health score between 0 and 100
        """
        try:
            # Base score
            score = 100.0

            # Deduct based on resource usage
            score -= (system_metrics.cpu_percent / 100) * 30  # CPU impact: 30%
            score -= (system_metrics.memory_percent / 100) * 30  # Memory impact: 30%
            score -= (system_metrics.disk_percent / 100) * 20  # Disk impact: 20%

            # Deduct for warnings and critical issues
            score -= len(threshold_check.get("warnings", [])) * 5
            score -= len(threshold_check.get("critical", [])) * 15

            # Ensure score is within bounds
            return max(0.0, min(100.0, round(score, 2)))

        except Exception:
            return 0.0


# Global singleton instance
_infrastructure_metrics = None


def get_infrastructure_metrics() -> InfrastructureMetricsCollector:
    """Get or create infrastructure metrics collector instance"""
    global _infrastructure_metrics
    if _infrastructure_metrics is None:
        _infrastructure_metrics = InfrastructureMetricsCollector()
    return _infrastructure_metrics


# Export the instance
infrastructure_metrics = get_infrastructure_metrics()
