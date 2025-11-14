"""Event Types and Categories for Agent Communication

Defines the types of events that can flow through the message bus,
their priorities, and categorization for routing.
"""

from dataclasses import dataclass
from enum import Enum, IntEnum
from typing import Any, Optional


class EventCategory(Enum):
    """High-level categorization of events."""

    # Core system events
    SYSTEM = "system"
    LIFECYCLE = "lifecycle"
    ERROR = "error"

    # Agent communication
    AGENT_REQUEST = "agent_request"
    AGENT_RESPONSE = "agent_response"
    AGENT_BROADCAST = "agent_broadcast"

    # Task management
    TASK_CREATED = "task_created"
    TASK_ASSIGNED = "task_assigned"
    TASK_COMPLETED = "task_completed"
    TASK_FAILED = "task_failed"

    # Educational workflow
    CONTENT_GENERATION = "content_generation"
    ASSESSMENT_CREATION = "assessment_creation"
    CURRICULUM_ALIGNMENT = "curriculum_alignment"
    STUDENT_PROGRESS = "student_progress"

    # Roblox integration
    ROBLOX_BUILD = "roblox_build"
    ROBLOX_SCRIPT = "roblox_script"
    ROBLOX_PUBLISH = "roblox_publish"
    ROBLOX_TEST = "roblox_test"

    # Collaboration
    COLLABORATION_REQUEST = "collaboration_request"
    COLLABORATION_UPDATE = "collaboration_update"
    COLLABORATION_COMPLETE = "collaboration_complete"

    # Monitoring
    METRICS = "metrics"
    HEALTH_CHECK = "health_check"
    PERFORMANCE = "performance"


class EventPriority(IntEnum):
    """Priority levels for event processing."""

    CRITICAL = 1  # System failures, security issues
    HIGH = 2  # User-facing operations, real-time requirements
    NORMAL = 3  # Standard operations
    LOW = 4  # Background tasks, analytics
    DEFERRED = 5  # Can be processed when resources available


class EventType(Enum):
    """Specific event types that can occur in the system."""

    # System Events
    SYSTEM_STARTUP = "system.startup"
    SYSTEM_SHUTDOWN = "system.shutdown"
    SYSTEM_ERROR = "system.error"
    SYSTEM_WARNING = "system.warning"
    SYSTEM_INFO = "system.info"

    # Agent Lifecycle
    AGENT_STARTED = "agent.started"
    AGENT_STOPPED = "agent.stopped"
    AGENT_READY = "agent.ready"
    AGENT_BUSY = "agent.busy"
    AGENT_IDLE = "agent.idle"
    AGENT_ERROR = "agent.error"
    AGENT_HEARTBEAT = "agent.heartbeat"

    # Agent Communication
    AGENT_MESSAGE = "agent.message"
    AGENT_REQUEST = "agent.request"
    AGENT_RESPONSE = "agent.response"
    AGENT_BROADCAST = "agent.broadcast"
    AGENT_WHISPER = "agent.whisper"  # Direct agent-to-agent

    # Task Management
    TASK_CREATE = "task.create"
    TASK_ASSIGN = "task.assign"
    TASK_START = "task.start"
    TASK_PROGRESS = "task.progress"
    TASK_COMPLETE = "task.complete"
    TASK_FAIL = "task.fail"
    TASK_RETRY = "task.retry"
    TASK_CANCEL = "task.cancel"

    # Educational Workflow Events
    EDU_CONTENT_REQUEST = "edu.content.request"
    EDU_CONTENT_GENERATED = "edu.content.generated"
    EDU_CONTENT_REVIEWED = "edu.content.reviewed"
    EDU_CONTENT_APPROVED = "edu.content.approved"
    EDU_QUIZ_CREATED = "edu.quiz.created"
    EDU_LESSON_DESIGNED = "edu.lesson.designed"
    EDU_CURRICULUM_ALIGNED = "edu.curriculum.aligned"
    EDU_ASSESSMENT_COMPLETE = "edu.assessment.complete"

    # NLU Events
    NLU_INTENT_DETECTED = "nlu.intent.detected"
    NLU_ENTITY_EXTRACTED = "nlu.entity.extracted"
    NLU_CONTEXT_UPDATED = "nlu.context.updated"
    NLU_CLARIFICATION_NEEDED = "nlu.clarification.needed"
    NLU_UNDERSTANDING_COMPLETE = "nlu.understanding.complete"

    # Conversation Events
    CONV_STARTED = "conv.started"
    CONV_TURN_PROCESSED = "conv.turn.processed"
    CONV_STATE_CHANGED = "conv.state.changed"
    CONV_CONTEXT_UPDATED = "conv.context.updated"
    CONV_COMPLETED = "conv.completed"

    # Roblox Events
    ROBLOX_SCRIPT_GENERATE = "roblox.script.generate"
    ROBLOX_SCRIPT_VALIDATE = "roblox.script.validate"
    ROBLOX_TERRAIN_BUILD = "roblox.terrain.build"
    ROBLOX_UI_CREATE = "roblox.ui.create"
    ROBLOX_GAME_MECHANICS = "roblox.mechanics.add"
    ROBLOX_ASSET_LOAD = "roblox.asset.load"
    ROBLOX_TEST_RUN = "roblox.test.run"
    ROBLOX_PUBLISH_REQUEST = "roblox.publish.request"
    ROBLOX_PUBLISH_SUCCESS = "roblox.publish.success"

    # Content Generation Events
    CONTENT_MULTIMODAL_REQUEST = "content.multimodal.request"
    CONTENT_IMAGE_GENERATE = "content.image.generate"
    CONTENT_AUDIO_CREATE = "content.audio.create"
    CONTENT_VIDEO_PRODUCE = "content.video.produce"
    CONTENT_TEXT_WRITE = "content.text.write"
    CONTENT_ASSET_OPTIMIZE = "content.asset.optimize"

    # Collaboration Events
    COLLAB_SESSION_START = "collab.session.start"
    COLLAB_USER_JOIN = "collab.user.join"
    COLLAB_USER_LEAVE = "collab.user.leave"
    COLLAB_EDIT_CONFLICT = "collab.edit.conflict"
    COLLAB_EDIT_MERGE = "collab.edit.merge"
    COLLAB_PERMISSION_REQUEST = "collab.permission.request"
    COLLAB_PERMISSION_GRANT = "collab.permission.grant"

    # Safety & Moderation Events
    SAFETY_CHECK_REQUEST = "safety.check.request"
    SAFETY_CHECK_PASS = "safety.check.pass"
    SAFETY_CHECK_FAIL = "safety.check.fail"
    SAFETY_CONTENT_FLAG = "safety.content.flag"
    SAFETY_USER_REPORT = "safety.user.report"
    SAFETY_INTERVENTION = "safety.intervention"

    # Performance & Monitoring
    PERF_METRIC_UPDATE = "perf.metric.update"
    PERF_THRESHOLD_EXCEED = "perf.threshold.exceed"
    PERF_OPTIMIZATION_SUGGEST = "perf.optimization.suggest"
    HEALTH_CHECK_REQUEST = "health.check.request"
    HEALTH_CHECK_RESPONSE = "health.check.response"
    HEALTH_DEGRADED = "health.degraded"
    HEALTH_RECOVERED = "health.recovered"

    # Swarm Management
    SWARM_SCALE_UP = "swarm.scale.up"
    SWARM_SCALE_DOWN = "swarm.scale.down"
    SWARM_REBALANCE = "swarm.rebalance"
    SWARM_CONSENSUS_REQUEST = "swarm.consensus.request"
    SWARM_CONSENSUS_REACHED = "swarm.consensus.reached"
    SWARM_ELECTION_START = "swarm.election.start"
    SWARM_LEADER_ELECTED = "swarm.leader.elected"

    # Database Events
    DB_SAVE_REQUEST = "db.save.request"
    DB_SAVE_SUCCESS = "db.save.success"
    DB_SAVE_FAILURE = "db.save.failure"
    DB_LOAD_REQUEST = "db.load.request"
    DB_LOAD_SUCCESS = "db.load.success"
    DB_SYNC_REQUEST = "db.sync.request"

    # User Interaction Events
    USER_MESSAGE_RECEIVED = "user.message.received"
    USER_ACTION_PERFORMED = "user.action.performed"
    USER_FEEDBACK_PROVIDED = "user.feedback.provided"
    USER_SESSION_START = "user.session.start"
    USER_SESSION_END = "user.session.end"


@dataclass
class EventMetadata:
    """Metadata associated with events."""

    event_type: EventType
    category: EventCategory
    priority: EventPriority
    source_agent: Optional[str] = None
    target_agent: Optional[str] = None
    correlation_id: Optional[str] = None
    causation_id: Optional[str] = None
    session_id: Optional[str] = None
    user_id: Optional[str] = None
    timestamp: Optional[str] = None
    ttl: Optional[int] = None  # Time to live in seconds
    retry_count: int = 0
    max_retries: int = 3
    custom_data: dict[str, Any] = None

    def __post_init__(self):
        """Initialize custom data if not provided."""
        if self.custom_data is None:
            self.custom_data = {}

    def is_expired(self, current_time: float) -> bool:
        """Check if event has expired based on TTL."""
        if not self.ttl or not self.timestamp:
            return False

        # Parse timestamp and check expiration
        # Implementation would depend on timestamp format
        return False  # Placeholder

    def should_retry(self) -> bool:
        """Check if event should be retried on failure."""
        return self.retry_count < self.max_retries

    def increment_retry(self):
        """Increment retry count."""
        self.retry_count += 1


def get_event_category(event_type: EventType) -> EventCategory:
    """Map event type to its category."""
    event_name = event_type.value.lower()

    if event_name.startswith("system"):
        return EventCategory.SYSTEM
    elif event_name.startswith("agent"):
        if "request" in event_name:
            return EventCategory.AGENT_REQUEST
        elif "response" in event_name:
            return EventCategory.AGENT_RESPONSE
        else:
            return EventCategory.LIFECYCLE
    elif event_name.startswith("task"):
        if "created" in event_name or "create" in event_name:
            return EventCategory.TASK_CREATED
        elif "assigned" in event_name or "assign" in event_name:
            return EventCategory.TASK_ASSIGNED
        elif "completed" in event_name or "complete" in event_name:
            return EventCategory.TASK_COMPLETED
        elif "failed" in event_name or "fail" in event_name:
            return EventCategory.TASK_FAILED
    elif event_name.startswith("edu"):
        if "content" in event_name:
            return EventCategory.CONTENT_GENERATION
        elif "assessment" in event_name or "quiz" in event_name:
            return EventCategory.ASSESSMENT_CREATION
        elif "curriculum" in event_name:
            return EventCategory.CURRICULUM_ALIGNMENT
    elif event_name.startswith("roblox"):
        if "build" in event_name or "terrain" in event_name:
            return EventCategory.ROBLOX_BUILD
        elif "script" in event_name:
            return EventCategory.ROBLOX_SCRIPT
        elif "publish" in event_name:
            return EventCategory.ROBLOX_PUBLISH
        elif "test" in event_name:
            return EventCategory.ROBLOX_TEST
    elif event_name.startswith("collab"):
        return EventCategory.COLLABORATION_UPDATE
    elif "health" in event_name:
        return EventCategory.HEALTH_CHECK
    elif "perf" in event_name or "metric" in event_name:
        return EventCategory.METRICS
    elif "error" in event_name or "fail" in event_name:
        return EventCategory.ERROR

    return EventCategory.SYSTEM  # Default category


def get_default_priority(event_type: EventType) -> EventPriority:
    """Get default priority for an event type."""
    event_name = event_type.value.lower()

    # Critical events
    if "error" in event_name or "fail" in event_name or "critical" in event_name:
        return EventPriority.CRITICAL

    # High priority events
    if any(keyword in event_name for keyword in ["user", "safety", "intervention", "request"]):
        return EventPriority.HIGH

    # Low priority events
    if any(keyword in event_name for keyword in ["metric", "heartbeat", "info", "progress"]):
        return EventPriority.LOW

    # Deferred events
    if any(keyword in event_name for keyword in ["optimize", "suggest", "analytics"]):
        return EventPriority.DEFERRED

    # Default to normal
    return EventPriority.NORMAL
