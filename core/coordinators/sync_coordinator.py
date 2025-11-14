"""
Sync Coordinator - Distributed state synchronization and event management

Manages state synchronization across all components, implements event bus,
handles real-time updates, and resolves conflicts in the ToolboxAI Roblox Environment.
"""

import asyncio
import json
import logging
import uuid
from collections import defaultdict, deque

# WebSocket import for type hints (Pusher used for actual real-time communication)
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Optional

from fastapi import FastAPI, WebSocket

logger = logging.getLogger(__name__)


class EventPriority(Enum):
    """Event priority levels"""

    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


class SyncState(Enum):
    """Synchronization state"""

    SYNCED = "synced"
    SYNCING = "syncing"
    CONFLICT = "conflict"
    ERROR = "error"
    DISCONNECTED = "disconnected"


@dataclass
class Event:
    """System event for synchronization"""

    event_id: str
    event_type: str
    source: str
    target: Optional[str]
    data: dict[str, Any]
    priority: EventPriority = EventPriority.NORMAL
    timestamp: datetime = field(default_factory=datetime.now)
    ttl_seconds: int = 3600
    retry_count: int = 3

    @property
    def is_expired(self) -> bool:
        """Check if event has expired"""
        return datetime.now() > self.timestamp + timedelta(seconds=self.ttl_seconds)


@dataclass
class StateSnapshot:
    """Snapshot of component state"""

    component_id: str
    state_data: dict[str, Any]
    version: int
    timestamp: datetime = field(default_factory=datetime.now)
    checksum: str = ""

    def __post_init__(self):
        if not self.checksum:
            self.checksum = self._calculate_checksum()

    def _calculate_checksum(self) -> str:
        """Calculate checksum for state integrity"""
        import hashlib

        state_str = json.dumps(self.state_data, sort_keys=True)
        # Use SHA256 instead of MD5 for better security (SonarQube: S4790)
        return hashlib.sha256(state_str.encode()).hexdigest()


@dataclass
class ConflictResolution:
    """Conflict resolution strategy and result"""

    conflict_id: str
    component_a: str
    component_b: str
    conflict_type: str
    resolution_strategy: str
    resolved_state: dict[str, Any]
    resolution_time: datetime = field(default_factory=datetime.now)


class SyncCoordinator:
    """
    Distributed state synchronization and event management coordinator.

    Handles:
    - State synchronization across all components
    - Event bus for inter-component communication
    - Real-time updates via WebSocket
    - Conflict detection and resolution
    - State versioning and rollback
    """

    def __init__(self, config: dict[str, Any] = None):
        self.config = config or {}

        # Configuration
        self.event_buffer_size = self.config.get("event_buffer_size", 10000)
        self.state_history_size = self.config.get("state_history_size", 100)
        self.sync_interval = self.config.get("sync_interval", 5)  # seconds
        self.enable_conflict_resolution = self.config.get("enable_conflict_resolution", True)

        # Core state
        self.is_initialized = False
        self.component_states: dict[str, StateSnapshot] = {}
        self.state_history: dict[str, deque] = defaultdict(
            lambda: deque(maxlen=self.state_history_size)
        )

        # Event system
        self.event_queue = asyncio.Queue(maxsize=self.event_buffer_size)
        self.event_handlers: dict[str, list[Callable]] = defaultdict(list)
        self.event_history = deque(maxlen=1000)

        # WebSocket connections
        self.websocket_connections: set[WebSocket] = set()
        self.component_websockets: dict[str, WebSocket] = {}

        # Conflict management
        self.active_conflicts: dict[str, ConflictResolution] = {}
        self.conflict_resolution_strategies = {
            "timestamp_wins": self._resolve_by_timestamp,
            "version_wins": self._resolve_by_version,
            "merge_strategy": self._resolve_by_merge,
            "user_decides": self._resolve_by_user,
        }

        # Sync status tracking
        self.component_sync_status: dict[str, SyncState] = {}
        self.last_sync_times: dict[str, datetime] = {}

        # Background tasks
        self.event_processor_task = None
        self.sync_monitor_task = None
        self.cleanup_task = None

        # Thread pool for CPU-intensive operations
        self.thread_pool = ThreadPoolExecutor(max_workers=4)

        # FastAPI app
        self.app = FastAPI(title="Sync Coordinator API", version="1.0.0")
        self._setup_routes()

    async def initialize(self):
        """Initialize the sync coordinator"""
        try:
            logger.info("Initializing Sync Coordinator...")

            # Register built-in event handlers
            await self._setup_event_handlers()

            # Start background tasks
            self.event_processor_task = asyncio.create_task(self._event_processor())
            self.sync_monitor_task = asyncio.create_task(self._sync_monitor())
            self.cleanup_task = asyncio.create_task(self._cleanup_expired_data())

            self.is_initialized = True
            logger.info("Sync Coordinator initialized successfully")

        except Exception as e:
            logger.error(f"Sync Coordinator initialization failed: {e}")
            raise

    async def _setup_event_handlers(self):
        """Setup built-in event handlers for common scenarios"""

        # State change events
        self.register_event_handler("state_changed", self._handle_state_change)
        self.register_event_handler("component_connected", self._handle_component_connect)
        self.register_event_handler("component_disconnected", self._handle_component_disconnect)

        # Workflow events
        self.register_event_handler("workflow_started", self._handle_workflow_event)
        self.register_event_handler("workflow_completed", self._handle_workflow_event)
        self.register_event_handler("workflow_failed", self._handle_workflow_event)

        # Resource events
        self.register_event_handler("resource_allocated", self._handle_resource_event)
        self.register_event_handler("resource_released", self._handle_resource_event)

        # Educational events
        self.register_event_handler("content_generated", self._handle_content_event)
        self.register_event_handler("quiz_completed", self._handle_educational_event)
        self.register_event_handler("learning_objective_achieved", self._handle_educational_event)

        logger.info("Event handlers registered successfully")

    def register_event_handler(self, event_type: str, handler: Callable):
        """Register an event handler for specific event type"""
        self.event_handlers[event_type].append(handler)
        logger.debug(f"Registered handler for event type: {event_type}")

    def unregister_event_handler(self, event_type: str, handler: Callable):
        """Unregister an event handler"""
        if handler in self.event_handlers[event_type]:
            self.event_handlers[event_type].remove(handler)
            logger.debug(f"Unregistered handler for event type: {event_type}")

    async def publish_event(
        self,
        event_type: str,
        source: str,
        data: dict[str, Any],
        target: Optional[str] = None,
        priority: EventPriority = EventPriority.NORMAL,
    ) -> str:
        """
        Publish an event to the event bus

        Args:
            event_type: Type of event
            source: Component that generated the event
            data: Event data payload
            target: Optional specific target component
            priority: Event priority level

        Returns:
            Event ID for tracking
        """
        event_id = str(uuid.uuid4())

        event = Event(
            event_id=event_id,
            event_type=event_type,
            source=source,
            target=target,
            data=data,
            priority=priority,
        )

        try:
            # Add to queue (with priority handling)
            await self.event_queue.put(event)
            logger.debug(f"Published event {event_id}: {event_type} from {source}")

            # Send immediate WebSocket notification for high priority events
            if priority in [EventPriority.HIGH, EventPriority.CRITICAL]:
                await self._broadcast_event(event)

            return event_id

        except asyncio.QueueFull:
            logger.error(f"Event queue full, dropping event {event_id}")
            raise RuntimeError("Event queue is full")

    async def _event_processor(self):
        """Background task to process events from the queue"""
        while self.is_initialized:
            try:
                # Get event with timeout
                event = await asyncio.wait_for(self.event_queue.get(), timeout=1.0)

                # Skip expired events
                if event.is_expired:
                    logger.warning(f"Skipping expired event {event.event_id}")
                    continue

                # Process event
                await self._process_event(event)

                # Add to history
                self.event_history.append(event)

            except asyncio.TimeoutError:
                continue  # No events to process
            except Exception as e:
                logger.error(f"Event processor error: {e}")
                await asyncio.sleep(1)

    async def _process_event(self, event: Event):
        """Process a single event"""
        try:
            # Call registered handlers
            handlers = self.event_handlers.get(event.event_type, [])

            if handlers:
                # Execute handlers in parallel
                handler_tasks = [asyncio.create_task(handler(event)) for handler in handlers]

                results = await asyncio.gather(*handler_tasks, return_exceptions=True)

                # Log handler results
                for i, result in enumerate(results):
                    if isinstance(result, Exception):
                        logger.error(f"Event handler {i} failed for {event.event_id}: {result}")

            # Broadcast to WebSocket connections
            await self._broadcast_event(event)

            logger.debug(f"Processed event {event.event_id}")

        except Exception as e:
            logger.error(f"Failed to process event {event.event_id}: {e}")

            # Retry logic for critical events
            if event.priority == EventPriority.CRITICAL and event.retry_count > 0:
                event.retry_count -= 1
                await asyncio.sleep(1)
                await self.event_queue.put(event)

    async def _broadcast_event(self, event: Event):
        """Broadcast event to all WebSocket connections"""
        if not self.websocket_connections:
            return

        message = {
            "type": "event",
            "event_id": event.event_id,
            "event_type": event.event_type,
            "source": event.source,
            "target": event.target,
            "data": event.data,
            "priority": event.priority.value,
            "timestamp": event.timestamp.isoformat(),
        }

        # Send to all connections or specific target
        target_connections = self.websocket_connections
        if event.target and event.target in self.component_websockets:
            target_connections = {self.component_websockets[event.target]}

        # Broadcast with error handling
        disconnected_connections = set()
        for websocket in target_connections:
            try:
                await websocket.send_text(json.dumps(message))
            except Exception as e:
                logger.warning(f"Failed to send event to WebSocket: {e}")
                disconnected_connections.add(websocket)

        # Clean up disconnected connections
        self.websocket_connections -= disconnected_connections

    async def update_component_state(
        self,
        component_id: str,
        state_data: dict[str, Any],
        version: Optional[int] = None,
    ) -> StateSnapshot:
        """
        Update state for a component and trigger synchronization

        Args:
            component_id: Unique component identifier
            state_data: New state data
            version: Optional version number

        Returns:
            StateSnapshot of the updated state
        """
        try:
            # Determine version
            current_state = self.component_states.get(component_id)
            if version is None:
                version = (current_state.version + 1) if current_state else 1

            # Create new state snapshot.json
            new_snapshot = StateSnapshot(
                component_id=component_id, state_data=state_data, version=version
            )

            # Check for conflicts
            if current_state and self.enable_conflict_resolution:
                conflict = await self._detect_conflict(current_state, new_snapshot)
                if conflict:
                    return await self._handle_conflict(conflict, current_state, new_snapshot)

            # Update state
            self.component_states[component_id] = new_snapshot
            self.state_history[component_id].append(new_snapshot)
            self.last_sync_times[component_id] = datetime.now()
            self.component_sync_status[component_id] = SyncState.SYNCED

            # Publish state change event
            await self.publish_event(
                event_type="state_changed",
                source="sync_coordinator",
                data={
                    "component_id": component_id,
                    "version": version,
                    "checksum": new_snapshot.checksum,
                    "timestamp": new_snapshot.timestamp.isoformat(),
                },
                priority=EventPriority.NORMAL,
            )

            logger.debug(f"Updated state for component {component_id} to version {version}")

            return new_snapshot

        except Exception as e:
            logger.error(f"Failed to update component state {component_id}: {e}")
            self.component_sync_status[component_id] = SyncState.ERROR
            raise

    async def get_component_state(
        self, component_id: str, version: Optional[int] = None
    ) -> Optional[StateSnapshot]:
        """
        Get current or specific version of component state

        Args:
            component_id: Component identifier
            version: Optional specific version to retrieve

        Returns:
            StateSnapshot or None if not found
        """
        if version is None:
            return self.component_states.get(component_id)

        # Search history for specific version
        history = self.state_history.get(component_id, deque())
        for snapshot in reversed(history):
            if snapshot.version == version:
                return snapshot

        return None

    async def sync_component(self, component_id: str) -> bool:
        """
        Force synchronization for a specific component

        Args:
            component_id: Component to synchronize

        Returns:
            True if sync successful
        """
        try:
            self.component_sync_status[component_id] = SyncState.SYNCING

            # Get current state from component (if it has a sync interface)
            current_state = await self._fetch_component_state(component_id)

            if current_state:
                await self.update_component_state(component_id, current_state)
                return True

            return False

        except Exception as e:
            logger.error(f"Failed to sync component {component_id}: {e}")
            self.component_sync_status[component_id] = SyncState.ERROR
            return False

    async def _fetch_component_state(self, component_id: str) -> Optional[dict[str, Any]]:
        """Fetch current state from a component"""
        try:
            # Try different methods to get component state

            # Method 1: Direct API call
            if component_id == "agent_system":
                from ..agents.orchestrator import AgentOrchestrator

                orchestrator = AgentOrchestrator()
                if hasattr(orchestrator, "get_state"):
                    return await orchestrator.get_state()

            elif component_id == "swarm_controller":
                from ..swarm.swarm_controller import SwarmController

                controller = SwarmController()
                if hasattr(controller, "get_state"):
                    return await controller.get_state()

            elif component_id == "sparc_manager":
                from ..sparc.state_manager import StateManager

                manager = StateManager()
                if hasattr(manager, "get_current_state"):
                    return await manager.get_current_state()

            elif component_id == "mcp_client":
                from ..mcp.client import MCPClient

                client = MCPClient()
                if hasattr(client, "get_context"):
                    return await client.get_context()

            # Method 2: WebSocket query
            if component_id in self.component_websockets:
                websocket = self.component_websockets[component_id]
                await websocket.send_text(
                    json.dumps({"type": "get_state", "request_id": str(uuid.uuid4())})
                )

                # Wait for response (with timeout)
                response = await asyncio.wait_for(websocket.recv(), timeout=10)
                data = json.loads(response)
                return data.get("state")

        except Exception as e:
            logger.warning(f"Could not fetch state for component {component_id}: {e}")

        return None

    async def _detect_conflict(
        self, current_state: StateSnapshot, new_state: StateSnapshot
    ) -> Optional[str]:
        """Detect conflicts between current and new state"""

        # Version conflict
        if new_state.version <= current_state.version:
            return "version_conflict"

        # Timestamp conflict (concurrent updates)
        time_diff = abs((new_state.timestamp - current_state.timestamp).total_seconds())
        if time_diff < 1:  # Updates within 1 second
            return "concurrent_update"

        # Data conflict (incompatible changes)
        if await self._has_incompatible_changes(current_state.state_data, new_state.state_data):
            return "data_conflict"

        return None

    async def _has_incompatible_changes(
        self, current_data: dict[str, Any], new_data: dict[str, Any]
    ) -> bool:
        """Check if changes are incompatible and require conflict resolution"""

        # Run in thread pool for CPU-intensive comparison
        return await asyncio.get_event_loop().run_in_executor(
            self.thread_pool, self._compare_data_structures, current_data, new_data
        )

    def _compare_data_structures(
        self, current_data: dict[str, Any], new_data: dict[str, Any]
    ) -> bool:
        """Compare data structures for conflicts (runs in thread pool)"""
        # Simple conflict detection - check for key deletions or type changes

        for key, current_value in current_data.items():
            if key not in new_data:
                # Key was deleted
                return True

            new_value = new_data[key]

            # Type change
            if type(current_value) != type(new_value):
                return True

            # Nested dict conflicts
            if isinstance(current_value, dict) and isinstance(new_value, dict):
                if self._compare_data_structures(current_value, new_value):
                    return True

        return False

    async def _handle_conflict(
        self, conflict_type: str, current_state: StateSnapshot, new_state: StateSnapshot
    ) -> StateSnapshot:
        """Handle state conflict using resolution strategies"""
        conflict_id = str(uuid.uuid4())

        logger.warning(f"Conflict detected for {new_state.component_id}: {conflict_type}")

        # Select resolution strategy
        strategy = self.config.get("default_conflict_strategy", "timestamp_wins")
        if conflict_type in self.config.get("conflict_strategies", {}):
            strategy = self.config["conflict_strategies"][conflict_type]

        # Apply resolution strategy
        resolver = self.conflict_resolution_strategies.get(strategy, self._resolve_by_timestamp)
        resolved_state = await resolver(current_state, new_state)

        # Record conflict resolution
        resolution = ConflictResolution(
            conflict_id=conflict_id,
            component_a=current_state.component_id,
            component_b=new_state.component_id,
            conflict_type=conflict_type,
            resolution_strategy=strategy,
            resolved_state=resolved_state.state_data,
        )

        self.active_conflicts[conflict_id] = resolution

        # Publish conflict resolution event
        await self.publish_event(
            event_type="conflict_resolved",
            source="sync_coordinator",
            data={
                "conflict_id": conflict_id,
                "component_id": new_state.component_id,
                "resolution_strategy": strategy,
                "resolved_version": resolved_state.version,
            },
            priority=EventPriority.HIGH,
        )

        return resolved_state

    async def _resolve_by_timestamp(
        self, current_state: StateSnapshot, new_state: StateSnapshot
    ) -> StateSnapshot:
        """Resolve conflict by choosing newer timestamp"""
        if new_state.timestamp >= current_state.timestamp:
            return new_state
        return current_state

    async def _resolve_by_version(
        self, current_state: StateSnapshot, new_state: StateSnapshot
    ) -> StateSnapshot:
        """Resolve conflict by choosing higher version"""
        if new_state.version >= current_state.version:
            return new_state
        return current_state

    async def _resolve_by_merge(
        self, current_state: StateSnapshot, new_state: StateSnapshot
    ) -> StateSnapshot:
        """Resolve conflict by merging compatible changes"""

        # Run merge in thread pool
        merged_data = await asyncio.get_event_loop().run_in_executor(
            self.thread_pool,
            self._merge_state_data,
            current_state.state_data,
            new_state.state_data,
        )

        return StateSnapshot(
            component_id=new_state.component_id,
            state_data=merged_data,
            version=max(current_state.version, new_state.version) + 1,
        )

    def _merge_state_data(
        self, current_data: dict[str, Any], new_data: dict[str, Any]
    ) -> dict[str, Any]:
        """Merge state data (runs in thread pool)"""
        merged = current_data.copy()

        for key, new_value in new_data.items():
            if key not in merged:
                # New key
                merged[key] = new_value
            elif isinstance(merged[key], dict) and isinstance(new_value, dict):
                # Recursively merge nested dicts
                merged[key] = self._merge_state_data(merged[key], new_value)
            else:
                # Overwrite with new value
                merged[key] = new_value

        return merged

    async def _resolve_by_user(
        self, current_state: StateSnapshot, new_state: StateSnapshot
    ) -> StateSnapshot:
        """Resolve conflict by requesting user input"""
        # This would integrate with UI for manual conflict resolution
        # For now, default to timestamp resolution
        logger.info(f"User conflict resolution requested for {new_state.component_id}")
        return await self._resolve_by_timestamp(current_state, new_state)

    async def register_component(
        self,
        component_id: str,
        websocket: Optional[WebSocket] = None,
        initial_state: Optional[dict[str, Any]] = None,
    ) -> bool:
        """
        Register a component for state synchronization

        Args:
            component_id: Unique component identifier
            websocket: Optional WebSocket connection
            initial_state: Optional initial state data

        Returns:
            True if registration successful
        """
        try:
            # Register WebSocket connection
            if websocket:
                self.component_websockets[component_id] = websocket
                self.websocket_connections.add(websocket)

            # Initialize state if provided
            if initial_state:
                await self.update_component_state(component_id, initial_state)

            # Set sync status
            self.component_sync_status[component_id] = SyncState.SYNCED
            self.last_sync_times[component_id] = datetime.now()

            # Publish registration event
            await self.publish_event(
                event_type="component_connected",
                source="sync_coordinator",
                data={
                    "component_id": component_id,
                    "has_websocket": websocket is not None,
                    "has_initial_state": initial_state is not None,
                },
            )

            logger.info(f"Registered component: {component_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to register component {component_id}: {e}")
            return False

    async def unregister_component(self, component_id: str) -> bool:
        """Unregister a component from synchronization"""
        try:
            # Remove WebSocket connection
            if component_id in self.component_websockets:
                websocket = self.component_websockets[component_id]
                self.websocket_connections.discard(websocket)
                del self.component_websockets[component_id]

            # Update sync status
            self.component_sync_status[component_id] = SyncState.DISCONNECTED

            # Publish disconnection event
            await self.publish_event(
                event_type="component_disconnected",
                source="sync_coordinator",
                data={"component_id": component_id},
            )

            logger.info(f"Unregistered component: {component_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to unregister component {component_id}: {e}")
            return False

    async def get_sync_status(self) -> dict[str, Any]:
        """Get comprehensive synchronization status"""

        # Component status summary
        status_counts = defaultdict(int)
        for status in self.component_sync_status.values():
            status_counts[status.value] += 1

        # Sync health assessment
        total_components = len(self.component_sync_status)
        synced_components = status_counts.get("synced", 0)
        sync_health = (synced_components / total_components * 100) if total_components > 0 else 100

        # Recent sync activity
        recent_syncs = sum(
            1
            for sync_time in self.last_sync_times.values()
            if datetime.now() - sync_time < timedelta(minutes=5)
        )

        return {
            "sync_health": sync_health,
            "total_components": total_components,
            "status_summary": dict(status_counts),
            "recent_sync_activity": recent_syncs,
            "active_conflicts": len(self.active_conflicts),
            "websocket_connections": len(self.websocket_connections),
            "event_queue_size": self.event_queue.qsize(),
            "events_processed": len(self.event_history),
            "last_updated": datetime.now().isoformat(),
        }

    async def get_component_history(
        self, component_id: str, limit: int = 10
    ) -> list[StateSnapshot]:
        """Get state history for a component"""
        history = self.state_history.get(component_id, deque())
        return list(history)[-limit:]

    async def rollback_component_state(self, component_id: str, target_version: int) -> bool:
        """
        Rollback component state to a specific version

        Args:
            component_id: Component to rollback
            target_version: Target version to rollback to

        Returns:
            True if rollback successful
        """
        try:
            # Find target state in history
            target_state = await self.get_component_state(component_id, target_version)

            if not target_state:
                raise ValueError(f"Version {target_version} not found for component {component_id}")

            # Create new state with incremented version
            rollback_state = StateSnapshot(
                component_id=component_id,
                state_data=target_state.state_data.copy(),
                version=self.component_states[component_id].version + 1,
            )

            # Update state
            await self.update_component_state(
                component_id, rollback_state.state_data, rollback_state.version
            )

            # Publish rollback event
            await self.publish_event(
                event_type="state_rollback",
                source="sync_coordinator",
                data={
                    "component_id": component_id,
                    "target_version": target_version,
                    "new_version": rollback_state.version,
                },
                priority=EventPriority.HIGH,
            )

            logger.info(f"Rolled back {component_id} to version {target_version}")
            return True

        except Exception as e:
            logger.error(f"Failed to rollback {component_id} to version {target_version}: {e}")
            return False

    async def _sync_monitor(self):
        """Background task to monitor synchronization health"""
        while self.is_initialized:
            try:
                # Check for stale components
                stale_threshold = timedelta(minutes=10)
                now = datetime.now()

                for component_id, last_sync in self.last_sync_times.items():
                    if now - last_sync > stale_threshold:
                        logger.warning(
                            f"Component {component_id} has stale sync (last: {last_sync})"
                        )

                        # Attempt to resync
                        await self.sync_component(component_id)

                # Monitor event queue health
                queue_size = self.event_queue.qsize()
                if queue_size > self.event_buffer_size * 0.8:
                    logger.warning(f"Event queue is {queue_size}/{self.event_buffer_size} full")

                await asyncio.sleep(self.sync_interval)

            except Exception as e:
                logger.error(f"Sync monitor error: {e}")
                await asyncio.sleep(self.sync_interval)

    async def _cleanup_expired_data(self):
        """Background task to cleanup expired data"""
        while self.is_initialized:
            try:
                # Clean expired conflicts
                expired_conflicts = [
                    conflict_id
                    for conflict_id, resolution in self.active_conflicts.items()
                    if datetime.now() - resolution.resolution_time > timedelta(hours=24)
                ]

                for conflict_id in expired_conflicts:
                    del self.active_conflicts[conflict_id]

                if expired_conflicts:
                    logger.info(f"Cleaned up {len(expired_conflicts)} expired conflicts")

                await asyncio.sleep(3600)  # Cleanup every hour

            except Exception as e:
                logger.error(f"Cleanup task error: {e}")
                await asyncio.sleep(3600)

    # Event handlers
    async def _handle_state_change(self, event: Event):
        """Handle state change events"""
        component_id = event.data.get("component_id")
        if component_id:
            self.last_sync_times[component_id] = datetime.now()

    async def _handle_component_connect(self, event: Event):
        """Handle component connection events"""
        component_id = event.data.get("component_id")
        if component_id:
            self.component_sync_status[component_id] = SyncState.SYNCED

    async def _handle_component_disconnect(self, event: Event):
        """Handle component disconnection events"""
        component_id = event.data.get("component_id")
        if component_id:
            self.component_sync_status[component_id] = SyncState.DISCONNECTED

    async def _handle_workflow_event(self, event: Event):
        """Handle workflow-related events"""
        # Sync workflow state changes across all components
        workflow_data = {
            "workflow_id": event.data.get("workflow_id"),
            "status": event.data.get("status"),
            "timestamp": event.timestamp.isoformat(),
        }

        # Broadcast to all components
        await self.publish_event(
            event_type="workflow_sync",
            source="sync_coordinator",
            data=workflow_data,
            priority=EventPriority.HIGH,
        )

    async def _handle_resource_event(self, event: Event):
        """Handle resource allocation events"""
        # Parse resource allocation event
        resource_id = event.data.get("resource_id")
        resource_type = event.data.get("resource_type")
        action = event.data.get("action")  # allocated/released/updated
        component_id = event.data.get("component_id")
        resource_data = event.data.get("resource_data", {})

        # Update resource tracking
        if action == "allocated":
            # Track resource allocation
            await self.update_component_state(
                f"resource_{resource_id}",
                {
                    "id": resource_id,
                    "type": resource_type,
                    "allocated_to": component_id,
                    "allocated_at": datetime.now().isoformat(),
                    "data": resource_data,
                    "status": "allocated",
                },
            )

            # Update component resource list
            component_state = await self.get_component_state(component_id)
            if component_state:
                resources = component_state.state_data.get("resources", [])
                resources.append(resource_id)
                component_state.state_data["resources"] = resources
                await self.update_component_state(component_id, component_state.state_data)

        elif action == "released":
            # Track resource release
            await self.update_component_state(
                f"resource_{resource_id}",
                {
                    "id": resource_id,
                    "type": resource_type,
                    "released_from": component_id,
                    "released_at": datetime.now().isoformat(),
                    "status": "available",
                },
            )

            # Update component resource list
            component_state = await self.get_component_state(component_id)
            if component_state:
                resources = component_state.state_data.get("resources", [])
                if resource_id in resources:
                    resources.remove(resource_id)
                component_state.state_data["resources"] = resources
                await self.update_component_state(component_id, component_state.state_data)

        elif action == "updated":
            # Update resource state
            await self.update_component_state(
                f"resource_{resource_id}",
                {
                    "id": resource_id,
                    "type": resource_type,
                    "component_id": component_id,
                    "updated_at": datetime.now().isoformat(),
                    "data": resource_data,
                    "status": "updated",
                },
            )

        # Notify affected components
        affected_components = event.data.get("affected_components", [])
        for affected_component in affected_components:
            await self.publish_event(
                event_type="resource_state_change",
                source="sync_coordinator",
                target=affected_component,
                data={
                    "resource_id": resource_id,
                    "resource_type": resource_type,
                    "action": action,
                    "component_id": component_id,
                    "resource_data": resource_data,
                },
                priority=EventPriority.HIGH,
            )

        # Adjust resource limits if needed
        if resource_type == "memory" or resource_type == "cpu":
            # Check if resource limits need adjustment
            total_allocated = 0
            for comp_id in self.component_states:
                if comp_id.startswith("resource_"):
                    resource_state = self.component_states[comp_id]
                    if (
                        resource_state.state_data.get("type") == resource_type
                        and resource_state.state_data.get("status") == "allocated"
                    ):
                        total_allocated += resource_state.state_data.get("data", {}).get(
                            "amount", 0
                        )

            # Publish resource limit update if threshold exceeded
            max_limit = resource_data.get("max_limit", float("inf"))
            if total_allocated > max_limit * 0.8:  # 80% threshold
                await self.publish_event(
                    event_type="resource_limit_warning",
                    source="sync_coordinator",
                    data={
                        "resource_type": resource_type,
                        "total_allocated": total_allocated,
                        "max_limit": max_limit,
                        "percentage_used": (total_allocated / max_limit * 100) if max_limit else 0,
                    },
                    priority=EventPriority.HIGH,
                )

        # Log resource changes
        logger.info(
            f"Resource event: {action} {resource_type} {resource_id} "
            f"for component {component_id}"
        )

    async def _handle_content_event(self, event: Event):
        """Handle content generation events"""
        # Sync generated content across all interested components
        content_data = event.data

        # Notify Roblox Studio plugin
        await self.publish_event(
            event_type="roblox_content_update",
            source="sync_coordinator",
            target="roblox_plugin",
            data=content_data,
            priority=EventPriority.HIGH,
        )

    async def _handle_educational_event(self, event: Event):
        """Handle educational-specific events"""
        # Track educational progress and sync with LMS
        educational_data = event.data

        # Update learning analytics
        await self.publish_event(
            event_type="learning_analytics_update",
            source="sync_coordinator",
            data=educational_data,
            priority=EventPriority.NORMAL,
        )

    async def get_metrics(self) -> dict[str, Any]:
        """Get sync coordinator metrics"""
        sync_status = await self.get_sync_status()

        # Event processing metrics
        event_types = defaultdict(int)
        for event in self.event_history:
            event_types[event.event_type] += 1

        return {
            "sync_status": sync_status,
            "event_processing": {
                "total_events": len(self.event_history),
                "queue_size": self.event_queue.qsize(),
                "event_types": dict(event_types),
            },
            "state_management": {
                "tracked_components": len(self.component_states),
                "total_state_versions": sum(
                    len(history) for history in self.state_history.values()
                ),
                "average_history_length": (
                    sum(len(history) for history in self.state_history.values())
                    / len(self.state_history)
                    if self.state_history
                    else 0
                ),
            },
            "conflict_resolution": {
                "active_conflicts": len(self.active_conflicts),
                "resolved_conflicts": len(
                    [c for c in self.active_conflicts.values() if c.resolved_state]
                ),
            },
        }

    async def get_health(self) -> dict[str, Any]:
        """Get sync coordinator health status"""
        try:
            sync_status = await self.get_sync_status()

            # Determine health status
            if sync_status["sync_health"] >= 90:
                status = "healthy"
            elif sync_status["sync_health"] >= 70:
                status = "degraded"
            else:
                status = "unhealthy"

            # Check background tasks
            background_tasks_healthy = all(
                [
                    self.event_processor_task and not self.event_processor_task.done(),
                    self.sync_monitor_task and not self.sync_monitor_task.done(),
                    self.cleanup_task and not self.cleanup_task.done(),
                ]
            )

            if not background_tasks_healthy:
                status = "degraded"

            return {
                "status": status,
                "sync_health": sync_status["sync_health"],
                "components_synced": sync_status["status_summary"].get("synced", 0),
                "total_components": sync_status["total_components"],
                "event_queue_size": sync_status["event_queue_size"],
                "active_conflicts": sync_status["active_conflicts"],
                "background_tasks_healthy": background_tasks_healthy,
                "last_check": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"Sync health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "last_check": datetime.now().isoformat(),
            }

    def _setup_routes(self):
        """Setup FastAPI routes for sync management"""

        @self.app.post("/register")
        async def register_component_endpoint(request: dict):
            """Register component for synchronization"""
            success = await self.register_component(
                request["component_id"], initial_state=request.get("initial_state")
            )
            return {"success": success}

        @self.app.delete("/register/{component_id}")
        async def unregister_component_endpoint(component_id: str):
            """Unregister component"""
            success = await self.unregister_component(component_id)
            return {"success": success}

        @self.app.post("/state/{component_id}")
        async def update_state_endpoint(component_id: str, request: dict):
            """Update component state"""
            snapshot = await self.update_component_state(
                component_id, request["state_data"], request.get("version")
            )
            return asdict(snapshot)

        @self.app.get("/state/{component_id}")
        async def get_state_endpoint(component_id: str, version: Optional[int] = None):
            """Get component state"""
            snapshot = await self.get_component_state(component_id, version)
            return asdict(snapshot) if snapshot else None

        @self.app.post("/sync/{component_id}")
        async def sync_component_endpoint(component_id: str):
            """Force component synchronization"""
            success = await self.sync_component(component_id)
            return {"success": success}

        @self.app.post("/rollback/{component_id}")
        async def rollback_endpoint(component_id: str, request: dict):
            """Rollback component state"""
            success = await self.rollback_component_state(component_id, request["target_version"])
            return {"success": success}

        @self.app.post("/events")
        async def publish_event_endpoint(request: dict):
            """Publish event to event bus"""
            event_id = await self.publish_event(
                event_type=request["event_type"],
                source=request["source"],
                data=request["data"],
                target=request.get("target"),
                priority=EventPriority(request.get("priority", 2)),
            )
            return {"event_id": event_id}

        @self.app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            """WebSocket endpoint for real-time synchronization"""
            await websocket.accept()
            self.websocket_connections.add(websocket)

            try:
                while True:
                    message = await websocket.receive_text()
                    data = json.loads(message)

                    # Handle different message types
                    if data.get("type") == "register_component":
                        await self.register_component(
                            data["component_id"], websocket, data.get("initial_state")
                        )
                    elif data.get("type") == "update_state":
                        await self.update_component_state(
                            data["component_id"],
                            data["state_data"],
                            data.get("version"),
                        )
                    elif data.get("type") == "publish_event":
                        await self.publish_event(
                            event_type=data["event_type"],
                            source=data["source"],
                            data=data["data"],
                            target=data.get("target"),
                            priority=EventPriority(data.get("priority", 2)),
                        )

            except WebSocketDisconnect:
                pass
            except Exception as e:
                logger.error(f"WebSocket error: {e}")
            finally:
                self.websocket_connections.discard(websocket)

                # Find and unregister component
                for component_id, ws in list(self.component_websockets.items()):
                    if ws == websocket:
                        await self.unregister_component(component_id)
                        break

        @self.app.get("/status")
        async def status_endpoint():
            """Get synchronization status"""
            return await self.get_sync_status()

        @self.app.get("/metrics")
        async def metrics_endpoint():
            """Get sync metrics"""
            return await self.get_metrics()

        @self.app.get("/health")
        async def health_endpoint():
            """Health check"""
            return await self.get_health()

    async def shutdown(self):
        """Gracefully shutdown sync coordinator"""
        try:
            logger.info("Shutting down Sync Coordinator...")

            # Cancel background tasks
            if self.event_processor_task:
                self.event_processor_task.cancel()
            if self.sync_monitor_task:
                self.sync_monitor_task.cancel()
            if self.cleanup_task:
                self.cleanup_task.cancel()

            # Close all WebSocket connections
            for websocket in list(self.websocket_connections):
                try:
                    await websocket.close()
                except (ConnectionError, OSError, AttributeError) as e:
                    logger.debug(f"Error closing websocket: {e}")

            # Shutdown thread pool
            self.thread_pool.shutdown(wait=True)

            self.is_initialized = False
            logger.info("Sync Coordinator shutdown complete")

        except Exception as e:
            logger.error(f"Error during Sync Coordinator shutdown: {e}")


# Convenience functions
async def create_sync_coordinator(**kwargs) -> SyncCoordinator:
    """Create and initialize a sync coordinator instance"""
    coordinator = SyncCoordinator(**kwargs)
    await coordinator.initialize()
    return coordinator
