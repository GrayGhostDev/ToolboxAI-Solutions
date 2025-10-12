"""
Database models for AI Agent System

This module defines SQLAlchemy models for tracking agent execution,
performance metrics, and system monitoring data.

Features:
- Agent execution history
- Performance metrics tracking
- Task queue management
- System health monitoring
- User interaction logging
- Multi-tenant isolation via organization_id

Author: ToolboxAI Team
Created: 2025-09-21
Updated: 2025-10-10 (Added multi-tenant support)
Version: 2.0.0
"""

import uuid
from datetime import datetime
from typing import Optional
from enum import Enum as PyEnum

from sqlalchemy import (
    Column, String, Integer, Float, Boolean, DateTime, Text, JSON,
    ForeignKey, UniqueConstraint, Index, CheckConstraint, Enum
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship, backref
from sqlalchemy.sql import func

# Import tenant-aware base models
from database.models.base import TenantBaseModel, GlobalBaseModel


class AgentType(PyEnum):
    """Types of AI agents"""
    CONTENT_GENERATOR = "content_generator"
    QUIZ_GENERATOR = "quiz_generator"
    TERRAIN_GENERATOR = "terrain_generator"
    SCRIPT_GENERATOR = "script_generator"
    CODE_REVIEWER = "code_reviewer"
    ROBLOX_ASSET = "roblox_asset"
    ROBLOX_TESTING = "roblox_testing"
    ROBLOX_ANALYTICS = "roblox_analytics"


class AgentStatus(PyEnum):
    """Agent operational status"""
    INITIALIZING = "initializing"
    IDLE = "idle"
    BUSY = "busy"
    PROCESSING = "processing"
    WAITING = "waiting"
    ERROR = "error"
    OFFLINE = "offline"
    MAINTENANCE = "maintenance"


class TaskStatus(PyEnum):
    """Task execution status"""
    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRYING = "retrying"


class TaskPriority(PyEnum):
    """Task priority levels"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"
    CRITICAL = "critical"


class AgentInstance(TenantBaseModel):
    """
    Agent instance registration and configuration.

    Tracks individual agent instances, their configuration,
    and current operational status.

    Multi-tenant: organization_id inherited from TenantBaseModel
    """
    __tablename__ = "agent_instances"

    # Note: id, organization_id, created_at, updated_at, created_by_id, updated_by_id, deleted_at
    # are inherited from TenantBaseModel

    agent_id = Column(String(100), unique=True, nullable=False, index=True)
    agent_type = Column(
        Enum(AgentType, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        index=True
    )
    status = Column(
        Enum(AgentStatus, values_callable=lambda x: [e.value for e in x]),
        default=AgentStatus.INITIALIZING,
        nullable=False,
        index=True
    )

    # Configuration and metadata
    configuration = Column(JSONB, default={})
    resource_limits = Column(JSONB, default={})
    performance_thresholds = Column(JSONB, default={})

    # Status tracking
    current_task_id = Column(String(100), index=True)
    last_activity = Column(DateTime(timezone=True), default=func.now(), index=True)
    last_heartbeat = Column(DateTime(timezone=True), default=func.now())

    # Performance counters
    total_tasks_completed = Column(Integer, default=0)
    total_tasks_failed = Column(Integer, default=0)
    total_execution_time = Column(Float, default=0.0)
    average_execution_time = Column(Float, default=0.0)

    # Relationships
    executions = relationship("AgentExecution", back_populates="agent_instance")
    metrics = relationship("AgentMetrics", back_populates="agent_instance")

    # Indexes (organization_id index auto-created by TenantMixin)
    __table_args__ = (
        Index('idx_agent_org_type_status', 'organization_id', 'agent_type', 'status'),
        Index('idx_agent_last_activity', 'last_activity'),
        Index('idx_agent_performance', 'total_tasks_completed', 'total_tasks_failed'),
    )


class AgentExecution(TenantBaseModel):
    """
    Individual agent task execution records.

    Tracks every task executed by agents including input data,
    output results, performance metrics, and error information.

    Multi-tenant: organization_id inherited from TenantBaseModel
    """
    __tablename__ = "agent_executions"

    # Note: id, organization_id, created_at, updated_at, created_by_id, updated_by_id, deleted_at
    # are inherited from TenantBaseModel

    task_id = Column(String(100), unique=True, nullable=False, index=True)

    # Agent information
    agent_instance_id = Column(UUID(as_uuid=True), ForeignKey("agent_instances.id"), nullable=False, index=True)
    agent_type = Column(
        Enum(AgentType, values_callable=lambda x: [e.value for e in x]), 
        nullable=False,
        index=True
    )
    
    # Task information
    task_type = Column(String(100), nullable=False, index=True)
    priority = Column(
        Enum(TaskPriority, values_callable=lambda x: [e.value for e in x]), 
        default=TaskPriority.NORMAL,
        index=True
    )
    
    # Execution data
    input_data = Column(JSONB, nullable=False)
    output_data = Column(JSONB)
    context_data = Column(JSONB, default={})
    
    # Status and results
    status = Column(
        Enum(TaskStatus, values_callable=lambda x: [e.value for e in x]), 
        default=TaskStatus.PENDING, 
        nullable=False,
        index=True
    )
    error_message = Column(Text)
    error_details = Column(JSONB)
    
    # Performance metrics
    execution_time_seconds = Column(Float)
    memory_usage_mb = Column(Float)
    cpu_usage_percent = Column(Float)
    
    # Quality metrics
    quality_score = Column(Float)
    confidence_score = Column(Float)
    user_rating = Column(Integer)  # 1-5 rating from user

    # Execution timestamps (created_at/updated_at inherited from TenantBaseModel)
    started_at = Column(DateTime(timezone=True), index=True)
    completed_at = Column(DateTime(timezone=True), index=True)

    # User context
    user_id = Column(UUID(as_uuid=True), index=True)
    session_id = Column(String(100), index=True)

    # Retry information
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)
    parent_task_id = Column(String(100), index=True)  # For retry chains

    # Relationships
    agent_instance = relationship("AgentInstance", back_populates="executions")

    # Constraints (organization_id index auto-created by TenantMixin)
    __table_args__ = (
        CheckConstraint('execution_time_seconds >= 0', name='check_positive_execution_time'),
        CheckConstraint('quality_score >= 0 AND quality_score <= 1', name='check_quality_score_range'),
        CheckConstraint('confidence_score >= 0 AND confidence_score <= 1', name='check_confidence_score_range'),
        CheckConstraint('user_rating >= 1 AND user_rating <= 5', name='check_user_rating_range'),
        CheckConstraint('retry_count >= 0', name='check_positive_retry_count'),
        Index('idx_execution_org_status_created', 'organization_id', 'status', 'created_at'),
        Index('idx_execution_agent_task_type', 'agent_type', 'task_type'),
        Index('idx_execution_user_session', 'user_id', 'session_id'),
        Index('idx_execution_performance', 'execution_time_seconds', 'quality_score'),
    )


class AgentMetrics(TenantBaseModel):
    """
    Aggregated agent performance metrics.

    Stores periodic performance snapshots for agents including
    throughput, success rates, and resource utilization.

    Multi-tenant: organization_id inherited from TenantBaseModel
    """
    __tablename__ = "agent_metrics"

    # Note: id, organization_id, created_at inherited from TenantBaseModel

    # Agent reference
    agent_instance_id = Column(UUID(as_uuid=True), ForeignKey("agent_instances.id"), nullable=False, index=True)
    agent_type = Column(
        Enum(AgentType, values_callable=lambda x: [e.value for e in x]), 
        nullable=False,
        index=True
    )
    
    # Time period
    period_start = Column(DateTime(timezone=True), nullable=False, index=True)
    period_end = Column(DateTime(timezone=True), nullable=False, index=True)
    period_duration_minutes = Column(Integer, nullable=False)
    
    # Task metrics
    tasks_completed = Column(Integer, default=0)
    tasks_failed = Column(Integer, default=0)
    tasks_cancelled = Column(Integer, default=0)
    total_tasks = Column(Integer, default=0)
    
    # Performance metrics
    success_rate = Column(Float, default=0.0)
    error_rate = Column(Float, default=0.0)
    average_execution_time = Column(Float, default=0.0)
    median_execution_time = Column(Float, default=0.0)
    p95_execution_time = Column(Float, default=0.0)
    
    # Throughput metrics
    tasks_per_minute = Column(Float, default=0.0)
    tasks_per_hour = Column(Float, default=0.0)
    
    # Quality metrics
    average_quality_score = Column(Float, default=0.0)
    average_confidence_score = Column(Float, default=0.0)
    average_user_rating = Column(Float, default=0.0)
    
    # Resource metrics
    average_memory_usage_mb = Column(Float, default=0.0)
    peak_memory_usage_mb = Column(Float, default=0.0)
    average_cpu_usage_percent = Column(Float, default=0.0)
    peak_cpu_usage_percent = Column(Float, default=0.0)
    
    # System metrics
    uptime_percentage = Column(Float, default=100.0)
    availability_percentage = Column(Float, default=100.0)
    
    # Additional metrics
    custom_metrics = Column(JSONB, default={})

    # Note: created_at timestamp inherited from TenantBaseModel

    # Relationships
    agent_instance = relationship("AgentInstance", back_populates="metrics")

    # Constraints (organization_id index auto-created by TenantMixin)
    __table_args__ = (
        CheckConstraint('success_rate >= 0 AND success_rate <= 100', name='check_success_rate_range'),
        CheckConstraint('error_rate >= 0 AND error_rate <= 100', name='check_error_rate_range'),
        CheckConstraint('uptime_percentage >= 0 AND uptime_percentage <= 100', name='check_uptime_range'),
        CheckConstraint('availability_percentage >= 0 AND availability_percentage <= 100', name='check_availability_range'),
        CheckConstraint('period_end > period_start', name='check_valid_period'),
        UniqueConstraint('agent_instance_id', 'period_start', name='uq_agent_period'),
        Index('idx_metrics_org_period', 'organization_id', 'period_start', 'period_end'),
        Index('idx_metrics_performance', 'success_rate', 'average_execution_time'),
    )


class AgentTaskQueue(TenantBaseModel):
    """
    Task queue management for agent system.

    Manages task queuing, prioritization, and scheduling
    for optimal agent utilization.

    Multi-tenant: organization_id inherited from TenantBaseModel
    """
    __tablename__ = "agent_task_queue"

    # Note: id, organization_id, created_at, updated_at inherited from TenantBaseModel

    task_id = Column(String(100), unique=True, nullable=False, index=True)
    
    # Task specification
    agent_type = Column(
        Enum(AgentType, values_callable=lambda x: [e.value for e in x]), 
        nullable=False,
        index=True
    )
    task_type = Column(String(100), nullable=False, index=True)
    priority = Column(
        Enum(TaskPriority, values_callable=lambda x: [e.value for e in x]), 
        default=TaskPriority.NORMAL,
        index=True
    )
    
    # Task data
    task_data = Column(JSONB, nullable=False)
    context_data = Column(JSONB, default={})
    
    # Scheduling information
    status = Column(
        Enum(TaskStatus, values_callable=lambda x: [e.value for e in x]), 
        default=TaskStatus.PENDING, 
        nullable=False,
        index=True
    )
    scheduled_at = Column(DateTime(timezone=True), index=True)
    deadline = Column(DateTime(timezone=True), index=True)
    max_execution_time_seconds = Column(Integer, default=300)
    
    # Assignment information
    assigned_agent_id = Column(String(100), index=True)
    assigned_at = Column(DateTime(timezone=True))
    
    # Dependencies
    depends_on = Column(JSONB, default=[])  # Array of task IDs
    blocks = Column(JSONB, default=[])      # Array of task IDs this blocks
    
    # Retry configuration
    max_retries = Column(Integer, default=3)
    retry_delay_seconds = Column(Integer, default=60)
    retry_count = Column(Integer, default=0)
    last_retry_at = Column(DateTime(timezone=True))
    
    # User context
    user_id = Column(UUID(as_uuid=True), index=True)
    session_id = Column(String(100), index=True)
    callback_url = Column(String(500))

    # Note: created_at, updated_at timestamps inherited from TenantBaseModel

    # Constraints (organization_id index auto-created by TenantMixin)
    __table_args__ = (
        CheckConstraint('max_retries >= 0', name='check_positive_max_retries'),
        CheckConstraint('retry_count >= 0', name='check_positive_retry_count'),
        CheckConstraint('max_execution_time_seconds > 0', name='check_positive_execution_time'),
        Index('idx_queue_org_priority_created', 'organization_id', 'priority', 'created_at'),
        Index('idx_queue_agent_status', 'agent_type', 'status'),
        Index('idx_queue_scheduled', 'scheduled_at', 'status'),
        Index('idx_queue_user_session', 'user_id', 'session_id'),
    )


class SystemHealth(GlobalBaseModel):
    """
    System-wide health and performance monitoring.

    Tracks overall system metrics, resource usage,
    and health indicators for the agent system.

    Global model: No organization_id - shared across all tenants
    """
    __tablename__ = "system_health"

    # Note: id, created_at, updated_at inherited from GlobalBaseModel
    # No organization_id - this is a system-wide model

    # Time period
    timestamp = Column(DateTime(timezone=True), default=func.now(), nullable=False, index=True)
    period_minutes = Column(Integer, default=5)  # 5-minute intervals
    
    # Agent system metrics
    total_agents = Column(Integer, default=0)
    active_agents = Column(Integer, default=0)
    idle_agents = Column(Integer, default=0)
    busy_agents = Column(Integer, default=0)
    error_agents = Column(Integer, default=0)
    
    # Task metrics
    total_tasks = Column(Integer, default=0)
    completed_tasks = Column(Integer, default=0)
    failed_tasks = Column(Integer, default=0)
    queued_tasks = Column(Integer, default=0)
    running_tasks = Column(Integer, default=0)
    
    # Performance metrics
    system_success_rate = Column(Float, default=0.0)
    system_error_rate = Column(Float, default=0.0)
    average_response_time = Column(Float, default=0.0)
    p95_response_time = Column(Float, default=0.0)
    
    # Throughput metrics
    tasks_per_minute = Column(Float, default=0.0)
    tasks_per_hour = Column(Float, default=0.0)
    
    # Resource metrics
    total_memory_usage_mb = Column(Float, default=0.0)
    total_cpu_usage_percent = Column(Float, default=0.0)
    disk_usage_percent = Column(Float, default=0.0)
    network_io_mbps = Column(Float, default=0.0)
    
    # Queue metrics
    queue_length = Column(Integer, default=0)
    average_queue_wait_time = Column(Float, default=0.0)
    queue_processing_rate = Column(Float, default=0.0)
    
    # Health indicators
    overall_health_score = Column(Float, default=100.0)  # 0-100
    availability_percentage = Column(Float, default=100.0)
    
    # Alerts and issues
    active_alerts = Column(Integer, default=0)
    critical_issues = Column(Integer, default=0)
    warnings = Column(Integer, default=0)
    
    # Custom metrics
    custom_metrics = Column(JSONB, default={})
    
    # Constraints
    __table_args__ = (
        CheckConstraint('overall_health_score >= 0 AND overall_health_score <= 100', name='check_health_score_range'),
        CheckConstraint('availability_percentage >= 0 AND availability_percentage <= 100', name='check_availability_range'),
        CheckConstraint('system_success_rate >= 0 AND system_success_rate <= 100', name='check_system_success_rate'),
        CheckConstraint('system_error_rate >= 0 AND system_error_rate <= 100', name='check_system_error_rate'),
        Index('idx_health_timestamp', 'timestamp'),
        Index('idx_health_score', 'overall_health_score', 'availability_percentage'),
    )


class AgentConfiguration(TenantBaseModel):
    """
    Agent configuration and settings management.

    Stores configuration templates and settings for different
    agent types and deployment environments.

    Multi-tenant: organization_id inherited from TenantBaseModel
    """
    __tablename__ = "agent_configurations"

    # Note: id, organization_id, created_at, updated_at, created_by_id inherited from TenantBaseModel

    # Configuration identification
    name = Column(String(100), nullable=False, index=True)
    version = Column(String(20), nullable=False)
    agent_type = Column(
        Enum(AgentType, values_callable=lambda x: [e.value for e in x]), 
        nullable=False,
        index=True
    )
    
    # Configuration data
    configuration = Column(JSONB, nullable=False)
    resource_limits = Column(JSONB, default={})
    performance_thresholds = Column(JSONB, default={})
    
    # Metadata
    description = Column(Text)
    environment = Column(String(50), default="production", index=True)  # dev, staging, production
    is_active = Column(Boolean, default=True, index=True)
    is_default = Column(Boolean, default=False, index=True)
    
    # Validation
    schema_version = Column(String(20), default="1.0")
    validation_rules = Column(JSONB, default={})

    # Note: created_at, updated_at, created_by_id timestamps inherited from TenantBaseModel

    # Constraints (organization_id index auto-created by TenantMixin)
    __table_args__ = (
        UniqueConstraint('organization_id', 'name', 'version', 'agent_type', name='uq_org_config_name_version_type'),
        Index('idx_config_org_active', 'organization_id', 'is_active', 'agent_type'),
        Index('idx_config_environment', 'environment', 'is_active'),
    )
