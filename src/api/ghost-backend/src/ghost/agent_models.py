"""
AI Agent System Models for ToolboxAI Roblox Environment

This module provides models for managing the multi-agent AI system including
agent definitions, task orchestration, SPARC framework state management,
and performance tracking.
"""

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from sqlalchemy import (
    DECIMAL,
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from .database import Base
from .models import AuditMixin, SoftDeleteMixin, TimestampMixin


class AgentType(str, Enum):
    """Types of AI agents in the system"""

    SUPERVISOR = "supervisor"
    CONTENT = "content"
    QUIZ = "quiz"
    TERRAIN = "terrain"
    SCRIPT = "script"
    REVIEW = "review"
    ORCHESTRATOR = "orchestrator"


class AgentStatus(str, Enum):
    """Agent operational status"""

    ACTIVE = "active"
    INACTIVE = "inactive"
    MAINTENANCE = "maintenance"
    ERROR = "error"
    UPDATING = "updating"


class TaskStatus(str, Enum):
    """Task execution status"""

    PENDING = "pending"
    ASSIGNED = "assigned"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


class TaskType(str, Enum):
    """Types of tasks that can be assigned to agents"""

    CONTENT_GENERATION = "content_generation"
    QUIZ_CREATION = "quiz_creation"
    SCRIPT_GENERATION = "script_generation"
    TERRAIN_CREATION = "terrain_creation"
    CONTENT_REVIEW = "content_review"
    QUALITY_ASSURANCE = "quality_assurance"
    OPTIMIZATION = "optimization"
    ANALYSIS = "analysis"


class SPARCStateType(str, Enum):
    """SPARC framework state types"""

    SITUATION = "situation"
    PROBLEM = "problem"
    ACTION = "action"
    RESULT = "result"
    CONTEXT = "context"


class AgentPriority(int, Enum):
    """Agent task priority levels"""

    CRITICAL = 1
    HIGH = 2
    NORMAL = 3
    LOW = 4
    BACKGROUND = 5


class AIAgent(Base, TimestampMixin, AuditMixin, SoftDeleteMixin):
    """AI agent definitions and configurations"""

    __tablename__ = "ai_agents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), unique=True, nullable=False)
    agent_type = Column(String(50), nullable=False)
    description = Column(Text, nullable=True)
    version = Column(String(20), nullable=False)

    # Configuration
    model_config = Column(JSONB, nullable=False)  # LLM and framework config
    capabilities = Column(JSONB, default=list)  # Array of capabilities
    dependencies = Column(JSONB, default=list)  # Agent dependencies

    # Performance settings
    priority = Column(Integer, default=5)
    max_concurrent_tasks = Column(Integer, default=3)
    timeout_seconds = Column(Integer, default=300)
    retry_count = Column(Integer, default=3)

    # Status and health
    is_active = Column(Boolean, default=True)
    status = Column(String(20), default="active")
    health_check_url = Column(String(500), nullable=True)
    last_health_check = Column(DateTime(timezone=True), nullable=True)
    error_count = Column(Integer, default=0)
    last_error = Column(Text, nullable=True)

    # Performance metrics
    total_tasks_completed = Column(Integer, default=0)
    success_rate = Column(DECIMAL(5, 2), default=0.0)
    average_execution_time = Column(DECIMAL(8, 2), default=0.0)
    quality_score = Column(DECIMAL(5, 2), default=0.0)

    # Relationships
    tasks = relationship(
        "AgentTask", back_populates="agent", cascade="all, delete-orphan"
    )
    states = relationship(
        "AgentState", back_populates="agent", cascade="all, delete-orphan"
    )
    metrics = relationship(
        "AgentMetric", back_populates="agent", cascade="all, delete-orphan"
    )
    review_tasks = relationship(
        "AgentState",
        back_populates="reviewed_by_agent",
        foreign_keys="AgentState.reviewed_by_id",
    )

    # Constraints
    __table_args__ = (
        CheckConstraint("priority >= 1 AND priority <= 5", name="valid_priority"),
        CheckConstraint("max_concurrent_tasks > 0", name="positive_concurrent_tasks"),
        CheckConstraint("timeout_seconds > 0", name="positive_timeout"),
        CheckConstraint("retry_count >= 0", name="non_negative_retry"),
        CheckConstraint(
            "success_rate >= 0 AND success_rate <= 100", name="valid_success_rate"
        ),
        Index("ix_ai_agents_type", "agent_type"),
        Index("ix_ai_agents_status", "status"),
        Index("ix_ai_agents_active", "is_active"),
        Index("ix_ai_agents_priority", "priority"),
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        return {
            "id": str(self.id),
            "name": self.name,
            "agent_type": self.agent_type,
            "description": self.description,
            "version": self.version,
            "model_config": self.model_config,
            "capabilities": self.capabilities,
            "dependencies": self.dependencies,
            "priority": self.priority,
            "max_concurrent_tasks": self.max_concurrent_tasks,
            "timeout_seconds": self.timeout_seconds,
            "retry_count": self.retry_count,
            "is_active": self.is_active,
            "status": self.status,
            "health_check_url": self.health_check_url,
            "last_health_check": (
                self.last_health_check.isoformat() if self.last_health_check else None
            ),
            "error_count": self.error_count,
            "last_error": self.last_error,
            "total_tasks_completed": self.total_tasks_completed,
            "success_rate": float(self.success_rate) if self.success_rate else 0.0,
            "average_execution_time": (
                float(self.average_execution_time)
                if self.average_execution_time
                else 0.0
            ),
            "quality_score": float(self.quality_score) if self.quality_score else 0.0,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


class AgentTask(Base, TimestampMixin, AuditMixin):
    """Agent task management and workflow tracking"""

    __tablename__ = "agent_tasks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agent_id = Column(
        UUID(as_uuid=True),
        ForeignKey("ai_agents.id", ondelete="CASCADE"),
        nullable=False,
    )
    parent_task_id = Column(
        UUID(as_uuid=True),
        ForeignKey("agent_tasks.id", ondelete="CASCADE"),
        nullable=True,
    )
    workflow_id = Column(UUID(as_uuid=True), nullable=True)  # Groups related tasks

    # Task definition
    task_type = Column(String(50), nullable=False)
    task_name = Column(String(200), nullable=False)
    input_data = Column(JSONB, nullable=False)
    output_data = Column(JSONB, nullable=True)

    # Status tracking
    status = Column(String(20), default="pending")
    priority = Column(Integer, default=5)

    # User context
    created_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    # Execution tracking
    assigned_at = Column(DateTime(timezone=True), nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    duration_seconds = Column(Integer, nullable=True)

    # Error handling
    retry_count = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    error_details = Column(JSONB, nullable=True)

    # Progress tracking
    progress_percentage = Column(Integer, default=0)
    intermediate_results = Column(JSONB, nullable=True)  # For long-running tasks

    # SPARC framework context
    context_data = Column(JSONB, nullable=True)

    # Quality metrics
    quality_score = Column(DECIMAL(5, 2), nullable=True)
    reviewed = Column(Boolean, default=False)
    approved = Column(Boolean, default=False)

    # Relationships
    agent = relationship("AIAgent", back_populates="tasks")
    parent_task = relationship("AgentTask", remote_side=[id])
    sub_tasks = relationship("AgentTask", back_populates="parent_task")
    created_by = relationship("User", foreign_keys=[created_by_id])
    states = relationship(
        "AgentState", back_populates="task", cascade="all, delete-orphan"
    )
    metrics = relationship(
        "AgentMetric", back_populates="task", cascade="all, delete-orphan"
    )

    # Constraints
    __table_args__ = (
        CheckConstraint("priority >= 1 AND priority <= 5", name="valid_task_priority"),
        CheckConstraint(
            "progress_percentage >= 0 AND progress_percentage <= 100",
            name="valid_progress",
        ),
        CheckConstraint("retry_count >= 0", name="non_negative_task_retry"),
        Index("ix_agent_tasks_agent", "agent_id"),
        Index("ix_agent_tasks_workflow", "workflow_id"),
        Index("ix_agent_tasks_status", "status"),
        Index("ix_agent_tasks_priority", "priority"),
        Index("ix_agent_tasks_created_by", "created_by_id"),
        Index("ix_agent_tasks_parent", "parent_task_id"),
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        return {
            "id": str(self.id),
            "agent_id": str(self.agent_id),
            "parent_task_id": str(self.parent_task_id) if self.parent_task_id else None,
            "workflow_id": str(self.workflow_id) if self.workflow_id else None,
            "task_type": self.task_type,
            "task_name": self.task_name,
            "input_data": self.input_data,
            "output_data": self.output_data,
            "status": self.status,
            "priority": self.priority,
            "created_by_id": str(self.created_by_id) if self.created_by_id else None,
            "assigned_at": self.assigned_at.isoformat() if self.assigned_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": (
                self.completed_at.isoformat() if self.completed_at else None
            ),
            "duration_seconds": self.duration_seconds,
            "retry_count": self.retry_count,
            "error_message": self.error_message,
            "error_details": self.error_details,
            "progress_percentage": self.progress_percentage,
            "intermediate_results": self.intermediate_results,
            "context_data": self.context_data,
            "quality_score": float(self.quality_score) if self.quality_score else None,
            "reviewed": self.reviewed,
            "approved": self.approved,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


class AgentState(Base, TimestampMixin):
    """Agent state management for SPARC framework"""

    __tablename__ = "agent_states"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agent_id = Column(
        UUID(as_uuid=True),
        ForeignKey("ai_agents.id", ondelete="CASCADE"),
        nullable=False,
    )
    task_id = Column(
        UUID(as_uuid=True),
        ForeignKey("agent_tasks.id", ondelete="CASCADE"),
        nullable=True,
    )
    workflow_id = Column(UUID(as_uuid=True), nullable=False)

    # SPARC state information
    state_type = Column(
        String(50), nullable=False
    )  # situation, problem, action, result, context
    state_data = Column(JSONB, nullable=False)
    sequence_number = Column(Integer, nullable=False)

    # Quality assessment
    quality_score = Column(DECIMAL(3, 2), nullable=True)  # 0.00 to 1.00
    confidence_score = Column(DECIMAL(3, 2), nullable=True)  # 0.00 to 1.00

    # Review process
    reviewed_by_id = Column(
        UUID(as_uuid=True),
        ForeignKey("ai_agents.id", ondelete="SET NULL"),
        nullable=True,
    )
    approved = Column(Boolean, default=False)
    review_notes = Column(Text, nullable=True)

    # Relationships
    agent = relationship("AIAgent", back_populates="states", foreign_keys=[agent_id])
    task = relationship("AgentTask", back_populates="states")
    reviewed_by_agent = relationship(
        "AIAgent", back_populates="review_tasks", foreign_keys=[reviewed_by_id]
    )

    # Constraints
    __table_args__ = (
        CheckConstraint(
            "quality_score IS NULL OR (quality_score >= 0 AND quality_score <= 1)",
            name="valid_quality_score",
        ),
        CheckConstraint(
            "confidence_score IS NULL OR (confidence_score >= 0 AND confidence_score <= 1)",
            name="valid_confidence_score",
        ),
        Index(
            "ix_agent_states_unique",
            "workflow_id",
            "state_type",
            "sequence_number",
            unique=True,
        ),
        Index("ix_agent_states_agent", "agent_id"),
        Index("ix_agent_states_task", "task_id"),
        Index("ix_agent_states_workflow", "workflow_id"),
        Index("ix_agent_states_type", "state_type"),
        Index("ix_agent_states_reviewed", "reviewed_by_id"),
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        return {
            "id": str(self.id),
            "agent_id": str(self.agent_id),
            "task_id": str(self.task_id) if self.task_id else None,
            "workflow_id": str(self.workflow_id),
            "state_type": self.state_type,
            "state_data": self.state_data,
            "sequence_number": self.sequence_number,
            "quality_score": float(self.quality_score) if self.quality_score else None,
            "confidence_score": (
                float(self.confidence_score) if self.confidence_score else None
            ),
            "reviewed_by_id": str(self.reviewed_by_id) if self.reviewed_by_id else None,
            "approved": self.approved,
            "review_notes": self.review_notes,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


class AgentMetric(Base, TimestampMixin):
    """Agent performance metrics and learning data"""

    __tablename__ = "agent_metrics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)


if TYPE_CHECKING:
    # Help static analyzers understand class-level attributes created by SQLAlchemy
    from uuid import UUID as _UUID

    AIAgent.id: _UUID  # type: ignore[misc]
    AgentTask.id: _UUID  # type: ignore[misc]
    AgentState.id: _UUID  # type: ignore[misc]
    AgentMetric.id: _UUID  # type: ignore[misc]
    agent_id = Column(
        UUID(as_uuid=True),
        ForeignKey("ai_agents.id", ondelete="CASCADE"),
        nullable=False,
    )
    task_id = Column(
        UUID(as_uuid=True),
        ForeignKey("agent_tasks.id", ondelete="CASCADE"),
        nullable=True,
    )

    # Metric information
    metric_type = Column(
        String(50), nullable=False
    )  # execution_time, success_rate, quality_score
    metric_value = Column(DECIMAL(10, 4), nullable=False)
    metric_unit = Column(String(20), nullable=True)  # seconds, percentage, score

    # Benchmarking
    benchmark_value = Column(DECIMAL(10, 4), nullable=True)
    target_value = Column(DECIMAL(10, 4), nullable=True)

    # Context
    context = Column(JSONB, nullable=True)
    recorded_at = Column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    agent = relationship("AIAgent", back_populates="metrics")
    task = relationship("AgentTask", back_populates="metrics")

    # Constraints
    __table_args__ = (
        Index("ix_agent_metrics_agent", "agent_id"),
        Index("ix_agent_metrics_task", "task_id"),
        Index("ix_agent_metrics_type", "metric_type"),
        Index("ix_agent_metrics_recorded", "recorded_at"),
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        return {
            "id": str(self.id),
            "agent_id": str(self.agent_id),
            "task_id": str(self.task_id) if self.task_id else None,
            "metric_type": self.metric_type,
            "metric_value": float(self.metric_value),
            "metric_unit": self.metric_unit,
            "benchmark_value": (
                float(self.benchmark_value) if self.benchmark_value else None
            ),
            "target_value": float(self.target_value) if self.target_value else None,
            "context": self.context,
            "recorded_at": self.recorded_at.isoformat(),
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


# Export models
__all__ = [
    "AgentType",
    "AgentStatus",
    "TaskStatus",
    "TaskType",
    "SPARCStateType",
    "AgentPriority",
    "AIAgent",
    "AgentTask",
    "AgentState",
    "AgentMetric",
]
