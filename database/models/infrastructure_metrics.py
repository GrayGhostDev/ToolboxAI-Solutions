"""
Infrastructure Metrics Database Models

Stores historical infrastructure monitoring data for analysis,
trending, and alerting.

Created: October 1, 2025
"""

from datetime import datetime, timezone
from typing import Optional, Dict, Any
from sqlalchemy import (
    Column, Integer, String, Float, DateTime, JSON,
    Boolean, Index, ForeignKey, Text, Enum as SQLEnum
)
from sqlalchemy.orm import relationship
from database.connection import Base
import enum


class MetricType(str, enum.Enum):
    """Metric type classification"""
    SYSTEM = "system"
    PROCESS = "process"
    NETWORK = "network"
    DISK = "disk"
    CUSTOM = "custom"


class HealthStatus(str, enum.Enum):
    """Health status levels"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class SystemMetricsHistory(Base):
    """
    Historical system metrics data

    Stores time-series system-level metrics for trending and analysis
    """
    __tablename__ = "system_metrics_history"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Timestamp
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True,
                      default=lambda: datetime.now(timezone.utc))

    # CPU Metrics
    cpu_percent = Column(Float, nullable=False)
    cpu_count = Column(Integer, nullable=False)
    cpu_freq_mhz = Column(Float)

    # Memory Metrics (in GB)
    memory_total_gb = Column(Float, nullable=False)
    memory_used_gb = Column(Float, nullable=False)
    memory_available_gb = Column(Float, nullable=False)
    memory_percent = Column(Float, nullable=False)

    # Disk Metrics (in GB)
    disk_total_gb = Column(Float, nullable=False)
    disk_used_gb = Column(Float, nullable=False)
    disk_free_gb = Column(Float, nullable=False)
    disk_percent = Column(Float, nullable=False)

    # Network Metrics
    network_bytes_sent = Column(Integer, nullable=False)
    network_bytes_recv = Column(Integer, nullable=False)
    network_connections = Column(Integer, nullable=False)

    # System Info
    uptime_seconds = Column(Float, nullable=False)
    boot_time = Column(DateTime(timezone=True))

    # Additional metadata
    metadata = Column(JSON, default={})

    # Indexes for performance
    __table_args__ = (
        Index('idx_system_metrics_timestamp', 'timestamp'),
        Index('idx_system_metrics_cpu_percent', 'cpu_percent'),
        Index('idx_system_metrics_memory_percent', 'memory_percent'),
    )

    def __repr__(self):
        return f"<SystemMetricsHistory(timestamp={self.timestamp}, cpu={self.cpu_percent}%, mem={self.memory_percent}%)>"


class ProcessMetricsHistory(Base):
    """
    Historical process metrics data

    Stores time-series process-level metrics for the backend application
    """
    __tablename__ = "process_metrics_history"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Timestamp
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True,
                      default=lambda: datetime.now(timezone.utc))

    # Process Info
    pid = Column(Integer, nullable=False)
    name = Column(String(255), nullable=False)
    status = Column(String(50))

    # Resource Usage
    cpu_percent = Column(Float, nullable=False)
    memory_mb = Column(Float, nullable=False)
    memory_percent = Column(Float, nullable=False)

    # Thread and File Descriptor Info
    num_threads = Column(Integer, nullable=False)
    num_fds = Column(Integer, default=0)  # File descriptors

    # Process Lifecycle
    create_time = Column(DateTime(timezone=True))

    # Additional metadata
    metadata = Column(JSON, default={})

    # Indexes
    __table_args__ = (
        Index('idx_process_metrics_timestamp', 'timestamp'),
        Index('idx_process_metrics_pid', 'pid'),
        Index('idx_process_metrics_cpu_percent', 'cpu_percent'),
    )

    def __repr__(self):
        return f"<ProcessMetricsHistory(timestamp={self.timestamp}, pid={self.pid}, cpu={self.cpu_percent}%)>"


class InfrastructureHealth(Base):
    """
    Infrastructure health check results

    Stores health status snapshots with warnings and critical issues
    """
    __tablename__ = "infrastructure_health"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Timestamp
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True,
                      default=lambda: datetime.now(timezone.utc))

    # Overall Status
    status = Column(SQLEnum(HealthStatus), nullable=False, index=True)
    health_score = Column(Float, nullable=False)  # 0-100

    # Issues
    warnings = Column(JSON, default=[])  # List of warning messages
    critical = Column(JSON, default=[])  # List of critical issues

    # Thresholds Used
    thresholds = Column(JSON, default={})

    # System Snapshot
    cpu_percent = Column(Float)
    memory_percent = Column(Float)
    disk_percent = Column(Float)

    # Additional context
    metadata = Column(JSON, default={})

    # Indexes
    __table_args__ = (
        Index('idx_infra_health_timestamp', 'timestamp'),
        Index('idx_infra_health_status', 'status'),
        Index('idx_infra_health_score', 'health_score'),
    )

    def __repr__(self):
        return f"<InfrastructureHealth(timestamp={self.timestamp}, status={self.status}, score={self.health_score})>"


class InfrastructureAlert(Base):
    """
    Infrastructure alerts and notifications

    Stores alerts triggered by threshold violations or anomalies
    """
    __tablename__ = "infrastructure_alerts"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Timestamp
    created_at = Column(DateTime(timezone=True), nullable=False, index=True,
                       default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True),
                       default=lambda: datetime.now(timezone.utc),
                       onupdate=lambda: datetime.now(timezone.utc))

    # Alert Info
    alert_type = Column(String(50), nullable=False)  # cpu, memory, disk, etc.
    severity = Column(String(20), nullable=False, index=True)  # warning, critical
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)

    # Metric Details
    metric_name = Column(String(100))
    metric_value = Column(Float)
    threshold_value = Column(Float)

    # Status
    is_active = Column(Boolean, default=True, index=True)
    acknowledged = Column(Boolean, default=False)
    acknowledged_by = Column(String(255))
    acknowledged_at = Column(DateTime(timezone=True))

    # Resolution
    resolved = Column(Boolean, default=False)
    resolved_at = Column(DateTime(timezone=True))
    resolution_note = Column(Text)

    # Additional metadata
    metadata = Column(JSON, default={})

    # Indexes
    __table_args__ = (
        Index('idx_alerts_created_at', 'created_at'),
        Index('idx_alerts_severity', 'severity'),
        Index('idx_alerts_is_active', 'is_active'),
        Index('idx_alerts_acknowledged', 'acknowledged'),
    )

    def __repr__(self):
        return f"<InfrastructureAlert(type={self.alert_type}, severity={self.severity}, active={self.is_active})>"


class MetricAggregation(Base):
    """
    Aggregated metrics for faster queries

    Stores pre-computed hourly/daily aggregations
    """
    __tablename__ = "metric_aggregations"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Time Window
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    aggregation_period = Column(String(20), nullable=False)  # hourly, daily, weekly

    # Metric Type
    metric_type = Column(SQLEnum(MetricType), nullable=False)
    metric_name = Column(String(100), nullable=False)

    # Aggregated Values
    min_value = Column(Float, nullable=False)
    max_value = Column(Float, nullable=False)
    avg_value = Column(Float, nullable=False)
    median_value = Column(Float)
    stddev_value = Column(Float)

    # Sample Count
    sample_count = Column(Integer, nullable=False)

    # Additional metadata
    metadata = Column(JSON, default={})

    # Indexes
    __table_args__ = (
        Index('idx_agg_timestamp_period', 'timestamp', 'aggregation_period'),
        Index('idx_agg_metric_type_name', 'metric_type', 'metric_name'),
    )

    def __repr__(self):
        return f"<MetricAggregation(period={self.aggregation_period}, metric={self.metric_name}, avg={self.avg_value})>"


# Helper functions for data retention

async def cleanup_old_metrics(session, days_to_keep: int = 30):
    """
    Remove metrics older than specified days

    Args:
        session: Database session
        days_to_keep: Number of days to retain
    """
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_to_keep)

    # Delete old system metrics
    await session.execute(
        SystemMetricsHistory.__table__.delete().where(
            SystemMetricsHistory.timestamp < cutoff_date
        )
    )

    # Delete old process metrics
    await session.execute(
        ProcessMetricsHistory.__table__.delete().where(
            ProcessMetricsHistory.timestamp < cutoff_date
        )
    )

    # Delete old health records
    await session.execute(
        InfrastructureHealth.__table__.delete().where(
            InfrastructureHealth.timestamp < cutoff_date
        )
    )

    await session.commit()


async def create_hourly_aggregations(session, timestamp: datetime):
    """
    Create hourly aggregations for the specified hour

    Args:
        session: Database session
        timestamp: Hour to aggregate
    """
    from sqlalchemy import func
    from datetime import timedelta

    start_time = timestamp.replace(minute=0, second=0, microsecond=0)
    end_time = start_time + timedelta(hours=1)

    # Aggregate CPU metrics
    cpu_stats = await session.execute(
        session.query(
            func.min(SystemMetricsHistory.cpu_percent).label('min_val'),
            func.max(SystemMetricsHistory.cpu_percent).label('max_val'),
            func.avg(SystemMetricsHistory.cpu_percent).label('avg_val'),
            func.count(SystemMetricsHistory.id).label('count')
        ).filter(
            SystemMetricsHistory.timestamp >= start_time,
            SystemMetricsHistory.timestamp < end_time
        )
    )

    result = cpu_stats.first()
    if result and result.count > 0:
        aggregation = MetricAggregation(
            timestamp=start_time,
            aggregation_period='hourly',
            metric_type=MetricType.SYSTEM,
            metric_name='cpu_percent',
            min_value=result.min_val,
            max_value=result.max_val,
            avg_value=result.avg_val,
            sample_count=result.count
        )
        session.add(aggregation)

    await session.commit()
