"""
WebSocket Clustering with Session Management

Provides horizontal scaling for WebSocket connections with:
- Session affinity using consistent hashing
- Cross-server message routing
- Connection state synchronization
- Automatic failover and recovery
"""

import asyncio
import json
import hashlib
import time
import uuid
from enum import Enum
from typing import Dict, List, Optional, Set, Any, Callable
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
import logging

import redis.asyncio as aioredis
from fastapi import WebSocket, WebSocketDisconnect, HTTPException
import msgpack

logger = logging.getLogger(__name__)


class MessageType(Enum):
    """WebSocket message types"""
    BROADCAST = "broadcast"
    UNICAST = "unicast"
    MULTICAST = "multicast"
    CLUSTER_SYNC = "cluster_sync"
    HEARTBEAT = "heartbeat"
    SESSION_TRANSFER = "session_transfer"


class NodeState(Enum):
    """Cluster node states"""
    INITIALIZING = "initializing"
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    DRAINING = "draining"
    SHUTDOWN = "shutdown"


@dataclass
class ConnectionInfo:
    """WebSocket connection metadata"""
    connection_id: str
    session_id: str
    user_id: Optional[str]
    node_id: str
    connected_at: datetime
    last_heartbeat: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)
    rooms: Set[str] = field(default_factory=set)


@dataclass
class ClusterNode:
    """Represents a node in the WebSocket cluster"""
    node_id: str
    hostname: str
    port: int
    state: NodeState
    connections: int
    cpu_usage: float
    memory_usage: float
    last_heartbeat: datetime
    weight: float = 1.0  # For load balancing


class ConsistentHash:
    """Consistent hashing for session affinity"""

    def __init__(self, nodes: List[str] = None, virtual_nodes: int = 150):
        self.nodes = nodes or []
        self.virtual_nodes = virtual_nodes
        self.ring: Dict[int, str] = {}
        self._rebuild_ring()

    def _hash(self, key: str) -> int:
        """Generate hash for a key"""
        return int(hashlib.md5(key.encode()).hexdigest(), 16)

    def _rebuild_ring(self):
        """Rebuild the hash ring"""
        self.ring = {}
        for node in self.nodes:
            for i in range(self.virtual_nodes):
                virtual_key = f"{node}:{i}"
                hash_value = self._hash(virtual_key)
                self.ring[hash_value] = node

    def add_node(self, node: str):
        """Add a node to the ring"""
        if node not in self.nodes:
            self.nodes.append(node)
            self._rebuild_ring()

    def remove_node(self, node: str):
        """Remove a node from the ring"""
        if node in self.nodes:
            self.nodes.remove(node)
            self._rebuild_ring()

    def get_node(self, key: str) -> Optional[str]:
        """Get the node responsible for a key"""
        if not self.ring:
            return None

        hash_value = self._hash(key)
        sorted_keys = sorted(self.ring.keys())

        # Find the first node with hash >= key hash
        for ring_hash in sorted_keys:
            if ring_hash >= hash_value:
                return self.ring[ring_hash]

        # Wrap around to first node
        return self.ring[sorted_keys[0]]


class WebSocketCluster:
    """Manages WebSocket connections across multiple server nodes"""

    def __init__(
        self,
        node_id: str,
        redis_url: str,
        hostname: str = "localhost",
        port: int = 8000,
        heartbeat_interval: int = 30,
        cleanup_interval: int = 60,
        session_timeout: int = 300
    ):
        self.node_id = node_id
        self.hostname = hostname
        self.port = port
        self.heartbeat_interval = heartbeat_interval
        self.cleanup_interval = cleanup_interval
        self.session_timeout = session_timeout

        # Redis for coordination
        self.redis_url = redis_url
        self.redis_client: Optional[aioredis.Redis] = None
        self.pubsub: Optional[aioredis.client.PubSub] = None

        # Local connection tracking
        self.connections: Dict[str, WebSocket] = {}
        self.connection_info: Dict[str, ConnectionInfo] = {}

        # Cluster state
        self.nodes: Dict[str, ClusterNode] = {}
        self.consistent_hash = ConsistentHash()
        self.node_state = NodeState.INITIALIZING

        # Message handlers
        self.handlers: Dict[MessageType, List[Callable]] = {
            msg_type: [] for msg_type in MessageType
        }

        # Room memberships (local cache)
        self.room_members: Dict[str, Set[str]] = {}

        # Background tasks
        self.tasks: List[asyncio.Task] = []

    async def start(self):
        """Start the cluster node"""
        logger.info("Starting WebSocket cluster node: %s", self.node_id)

        # Connect to Redis
        self.redis_client = await aioredis.from_url(
            self.redis_url,
            encoding="utf-8",
            decode_responses=False  # We'll use msgpack for serialization
        )

        # Subscribe to cluster channels
        self.pubsub = self.redis_client.pubsub()
        await self.pubsub.subscribe(
            f"cluster:broadcast",
            f"cluster:node:{self.node_id}",
            f"cluster:heartbeat"
        )

        # Register node
        await self._register_node()

        # Start background tasks
        self.tasks = [
            asyncio.create_task(self._heartbeat_loop()),
            asyncio.create_task(self._cleanup_loop()),
            asyncio.create_task(self._message_loop()),
            asyncio.create_task(self._monitor_cluster())
        ]

        self.node_state = NodeState.HEALTHY
        logger.info("WebSocket cluster node started successfully")

    async def stop(self):
        """Stop the cluster node"""
        logger.info("Stopping WebSocket cluster node: %s", self.node_id)

        self.node_state = NodeState.DRAINING

        # Notify cluster of shutdown
        await self._unregister_node()

        # Cancel background tasks
        for task in self.tasks:
            task.cancel()
        await asyncio.gather(*self.tasks, return_exceptions=True)

        # Close all connections
        for conn_id in list(self.connections.keys()):
            await self.disconnect(conn_id, reason="Server shutdown")

        # Clean up Redis
        if self.pubsub:
            await self.pubsub.unsubscribe()
            await self.pubsub.close()

        if self.redis_client:
            await self.redis_client.close()

        self.node_state = NodeState.SHUTDOWN
        logger.info("WebSocket cluster node stopped")

    async def _register_node(self):
        """Register this node in the cluster"""
        node_data = {
            "node_id": self.node_id,
            "hostname": self.hostname,
            "port": self.port,
            "state": NodeState.HEALTHY.value,
            "connections": 0,
            "cpu_usage": 0.0,
            "memory_usage": 0.0,
            "last_heartbeat": datetime.utcnow().isoformat()
        }

        # Store in Redis with expiry
        await self.redis_client.setex(
            f"cluster:nodes:{self.node_id}",
            self.heartbeat_interval * 3,
            msgpack.packb(node_data)
        )

        # Add to consistent hash ring
        self.consistent_hash.add_node(self.node_id)

        logger.info("Node registered: %s", self.node_id)

    async def _unregister_node(self):
        """Remove this node from the cluster"""
        # Initiate session transfers for sticky sessions
        for conn_info in self.connection_info.values():
            await self._initiate_session_transfer(conn_info)

        # Remove from Redis
        await self.redis_client.delete(f"cluster:nodes:{self.node_id}")

        # Remove from consistent hash
        self.consistent_hash.remove_node(self.node_id)

        logger.info("Node unregistered: %s", self.node_id)

    async def _heartbeat_loop(self):
        """Send periodic heartbeats"""
        while self.node_state not in (NodeState.DRAINING, NodeState.SHUTDOWN):
            try:
                # Update node metrics
                import psutil
                cpu_usage = psutil.cpu_percent(interval=1)
                memory_usage = psutil.virtual_memory().percent

                node_data = {
                    "node_id": self.node_id,
                    "hostname": self.hostname,
                    "port": self.port,
                    "state": self.node_state.value,
                    "connections": len(self.connections),
                    "cpu_usage": cpu_usage,
                    "memory_usage": memory_usage,
                    "last_heartbeat": datetime.utcnow().isoformat()
                }

                # Update in Redis
                await self.redis_client.setex(
                    f"cluster:nodes:{self.node_id}",
                    self.heartbeat_interval * 3,
                    msgpack.packb(node_data)
                )

                # Publish heartbeat
                await self.redis_client.publish(
                    "cluster:heartbeat",
                    msgpack.packb({"node_id": self.node_id, "timestamp": time.time()})
                )

                await asyncio.sleep(self.heartbeat_interval)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Error in heartbeat loop: %s", e)
                await asyncio.sleep(5)

    async def _cleanup_loop(self):
        """Clean up stale connections and data"""
        while self.node_state not in (NodeState.DRAINING, NodeState.SHUTDOWN):
            try:
                now = datetime.utcnow()

                # Clean up stale connections
                stale_connections = []
                for conn_id, info in self.connection_info.items():
                    if now - info.last_heartbeat > timedelta(seconds=self.session_timeout):
                        stale_connections.append(conn_id)

                for conn_id in stale_connections:
                    logger.warning("Cleaning up stale connection: %s", conn_id)
                    await self.disconnect(conn_id, reason="Session timeout")

                # Clean up empty rooms
                empty_rooms = [
                    room for room, members in self.room_members.items()
                    if not members
                ]
                for room in empty_rooms:
                    del self.room_members[room]

                await asyncio.sleep(self.cleanup_interval)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Error in cleanup loop: %s", e)
                await asyncio.sleep(10)

    async def _message_loop(self):
        """Process messages from Redis pub/sub"""
        while self.node_state not in (NodeState.DRAINING, NodeState.SHUTDOWN):
            try:
                message = await self.pubsub.get_message(
                    ignore_subscribe_messages=True,
                    timeout=1.0
                )

                if message and message["type"] == "message":
                    await self._handle_cluster_message(message)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Error in message loop: %s", e)
                await asyncio.sleep(1)

    async def _monitor_cluster(self):
        """Monitor cluster health and update node list"""
        while self.node_state not in (NodeState.DRAINING, NodeState.SHUTDOWN):
            try:
                # Get all cluster nodes
                node_keys = await self.redis_client.keys("cluster:nodes:*")
                current_nodes = {}

                for key in node_keys:
                    node_data = await self.redis_client.get(key)
                    if node_data:
                        data = msgpack.unpackb(node_data)
                        node_id = data["node_id"]
                        current_nodes[node_id] = ClusterNode(
                            node_id=node_id,
                            hostname=data["hostname"],
                            port=data["port"],
                            state=NodeState(data["state"]),
                            connections=data["connections"],
                            cpu_usage=data["cpu_usage"],
                            memory_usage=data["memory_usage"],
                            last_heartbeat=datetime.fromisoformat(data["last_heartbeat"])
                        )

                        # Calculate weight for load balancing
                        if current_nodes[node_id].state == NodeState.HEALTHY:
                            # Weight based on available capacity
                            cpu_factor = 1.0 - (data["cpu_usage"] / 100)
                            mem_factor = 1.0 - (data["memory_usage"] / 100)
                            conn_factor = max(0.1, 1.0 - (data["connections"] / 1000))
                            current_nodes[node_id].weight = (
                                cpu_factor * 0.3 + mem_factor * 0.3 + conn_factor * 0.4
                            )

                # Update consistent hash ring
                for node_id in current_nodes:
                    if node_id not in self.nodes:
                        self.consistent_hash.add_node(node_id)

                for node_id in list(self.nodes.keys()):
                    if node_id not in current_nodes:
                        self.consistent_hash.remove_node(node_id)
                        logger.warning("Node %s removed from cluster", node_id)

                self.nodes = current_nodes

                await asyncio.sleep(10)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Error monitoring cluster: %s", e)
                await asyncio.sleep(5)

    async def _handle_cluster_message(self, message: dict):
        """Handle messages from other cluster nodes"""
        try:
            data = msgpack.unpackb(message["data"])
            msg_type = MessageType(data.get("type"))

            if msg_type == MessageType.BROADCAST:
                await self._handle_broadcast(data)
            elif msg_type == MessageType.UNICAST:
                await self._handle_unicast(data)
            elif msg_type == MessageType.MULTICAST:
                await self._handle_multicast(data)
            elif msg_type == MessageType.SESSION_TRANSFER:
                await self._handle_session_transfer(data)

        except Exception as e:
            logger.error("Error handling cluster message: %s", e)

    async def connect(
        self,
        websocket: WebSocket,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Register a new WebSocket connection"""
        connection_id = str(uuid.uuid4())

        # Use session_id for sticky sessions
        if not session_id:
            session_id = connection_id

        # Check if this session should be on this node
        target_node = self.consistent_hash.get_node(session_id)
        if target_node != self.node_id:
            # Session should be on different node
            logger.info("Redirecting session %s to node %s", session_id, target_node)
            if target_node in self.nodes:
                node = self.nodes[target_node]
                raise HTTPException(
                    status_code=307,
                    detail=f"Redirect to {node.hostname}:{node.port}"
                )

        # Accept connection
        await websocket.accept()

        # Store connection
        self.connections[connection_id] = websocket
        self.connection_info[connection_id] = ConnectionInfo(
            connection_id=connection_id,
            session_id=session_id,
            user_id=user_id,
            node_id=self.node_id,
            connected_at=datetime.utcnow(),
            last_heartbeat=datetime.utcnow(),
            metadata=metadata or {}
        )

        # Store session mapping in Redis
        await self.redis_client.setex(
            f"session:{session_id}",
            self.session_timeout,
            msgpack.packb({
                "node_id": self.node_id,
                "connection_id": connection_id
            })
        )

        logger.info("WebSocket connected: %s (session: %s)", connection_id, session_id)
        return connection_id

    async def disconnect(
        self,
        connection_id: str,
        reason: str = "Normal closure"
    ):
        """Disconnect a WebSocket connection"""
        if connection_id not in self.connections:
            return

        # Get connection info
        info = self.connection_info.get(connection_id)

        # Close WebSocket
        ws = self.connections[connection_id]
        try:
            await ws.close(reason=reason)
        except Exception:
            pass

        # Clean up local state
        del self.connections[connection_id]
        if info:
            del self.connection_info[connection_id]

            # Remove from rooms
            for room in info.rooms:
                if room in self.room_members:
                    self.room_members[room].discard(connection_id)

            # Remove session mapping
            await self.redis_client.delete(f"session:{info.session_id}")

        logger.info("WebSocket disconnected: %s (reason: %s)", connection_id, reason)

    async def send_message(
        self,
        connection_id: str,
        message: Dict[str, Any]
    ):
        """Send message to a specific connection"""
        if connection_id in self.connections:
            ws = self.connections[connection_id]
            try:
                await ws.send_json(message)
            except Exception as e:
                logger.error("Error sending message to %s: %s", connection_id, e)
                await self.disconnect(connection_id, reason="Send error")

    async def broadcast(
        self,
        message: Dict[str, Any],
        exclude: Optional[Set[str]] = None
    ):
        """Broadcast message to all connections on all nodes"""
        cluster_msg = {
            "type": MessageType.BROADCAST.value,
            "message": message,
            "exclude": list(exclude) if exclude else [],
            "source_node": self.node_id
        }

        # Send to other nodes
        await self.redis_client.publish(
            "cluster:broadcast",
            msgpack.packb(cluster_msg)
        )

        # Send to local connections
        await self._handle_broadcast(cluster_msg)

    async def _handle_broadcast(self, data: dict):
        """Handle broadcast from cluster"""
        message = data["message"]
        exclude = set(data.get("exclude", []))
        source_node = data.get("source_node")

        # Don't process our own broadcasts again
        if source_node == self.node_id and "cluster:broadcast" in data:
            return

        # Send to all local connections
        for conn_id in list(self.connections.keys()):
            if conn_id not in exclude:
                await self.send_message(conn_id, message)

    async def join_room(self, connection_id: str, room: str):
        """Add connection to a room"""
        if connection_id not in self.connection_info:
            return

        # Update local state
        if room not in self.room_members:
            self.room_members[room] = set()
        self.room_members[room].add(connection_id)
        self.connection_info[connection_id].rooms.add(room)

        # Update Redis
        await self.redis_client.sadd(f"room:{room}", connection_id)

        logger.debug("Connection %s joined room %s", connection_id, room)

    async def leave_room(self, connection_id: str, room: str):
        """Remove connection from a room"""
        if connection_id not in self.connection_info:
            return

        # Update local state
        if room in self.room_members:
            self.room_members[room].discard(connection_id)
        self.connection_info[connection_id].rooms.discard(room)

        # Update Redis
        await self.redis_client.srem(f"room:{room}", connection_id)

        logger.debug("Connection %s left room %s", connection_id, room)

    async def room_broadcast(
        self,
        room: str,
        message: Dict[str, Any],
        exclude: Optional[Set[str]] = None
    ):
        """Broadcast message to all connections in a room across cluster"""
        # Get all members from Redis
        members = await self.redis_client.smembers(f"room:{room}")

        cluster_msg = {
            "type": MessageType.MULTICAST.value,
            "targets": [m.decode() if isinstance(m, bytes) else m for m in members],
            "message": message,
            "exclude": list(exclude) if exclude else [],
            "source_node": self.node_id
        }

        # Send to cluster
        await self.redis_client.publish(
            "cluster:broadcast",
            msgpack.packb(cluster_msg)
        )

        # Handle locally
        await self._handle_multicast(cluster_msg)

    async def _handle_multicast(self, data: dict):
        """Handle multicast from cluster"""
        targets = set(data["targets"])
        message = data["message"]
        exclude = set(data.get("exclude", []))

        # Send to local targets
        for conn_id in targets.intersection(self.connections.keys()):
            if conn_id not in exclude:
                await self.send_message(conn_id, message)

    async def _initiate_session_transfer(self, conn_info: ConnectionInfo):
        """Initiate transfer of session to another node"""
        # Find best target node
        best_node = None
        best_weight = 0

        for node_id, node in self.nodes.items():
            if node_id != self.node_id and node.state == NodeState.HEALTHY:
                if node.weight > best_weight:
                    best_node = node_id
                    best_weight = node.weight

        if not best_node:
            logger.warning("No healthy nodes available for session transfer")
            return

        # Prepare transfer data
        transfer_data = {
            "type": MessageType.SESSION_TRANSFER.value,
            "session_id": conn_info.session_id,
            "user_id": conn_info.user_id,
            "metadata": conn_info.metadata,
            "rooms": list(conn_info.rooms),
            "target_node": best_node
        }

        # Notify target node
        await self.redis_client.publish(
            f"cluster:node:{best_node}",
            msgpack.packb(transfer_data)
        )

        logger.info("Initiated session transfer: %s -> %s",
                   conn_info.session_id, best_node)

    async def _handle_session_transfer(self, data: dict):
        """Handle incoming session transfer"""
        session_id = data["session_id"]

        # Update consistent hash to prefer this node for the session
        # This ensures the session will reconnect to this node
        await self.redis_client.setex(
            f"session:transfer:{session_id}",
            60,  # Transfer hint expires in 60 seconds
            self.node_id
        )

        logger.info("Ready to accept session transfer: %s", session_id)

    def get_metrics(self) -> dict:
        """Get cluster metrics"""
        return {
            "node_id": self.node_id,
            "state": self.node_state.value,
            "connections": len(self.connections),
            "rooms": len(self.room_members),
            "total_room_memberships": sum(
                len(members) for members in self.room_members.values()
            ),
            "cluster_nodes": len(self.nodes),
            "healthy_nodes": sum(
                1 for node in self.nodes.values()
                if node.state == NodeState.HEALTHY
            )
        }


# Global cluster instance
_cluster_instance: Optional[WebSocketCluster] = None


def init_websocket_cluster(
    node_id: str,
    redis_url: str,
    **kwargs
) -> WebSocketCluster:
    """Initialize the WebSocket cluster"""
    global _cluster_instance
    _cluster_instance = WebSocketCluster(node_id, redis_url, **kwargs)
    return _cluster_instance


def get_websocket_cluster() -> Optional[WebSocketCluster]:
    """Get the WebSocket cluster instance"""
    return _cluster_instance