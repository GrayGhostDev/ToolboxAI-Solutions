"""
Redis AI Manager - Enhanced Redis Stack Integration

Implements Redis Stack features for AI agents and MCP systems:
- Vector similarity search for semantic queries
- JSON document storage for complex agent states
- Time series for monitoring and metrics
- Bloom filters for efficient existence checks
- Pub/Sub for real-time agent communication
- Session management with automatic expiration

References:
- Redis Stack AI: https://redis.io/docs/latest/develop/ai/
- Redis Vector Similarity: https://redis.io/docs/latest/develop/interact/search-and-query/vector-search/
- Redis JSON: https://redis.io/docs/latest/develop/data-types/json/
- Redis OM Python: https://github.com/redis/redis-om-python
"""

import json
import logging
import time
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, asdict, field
from enum import Enum
import numpy as np

import redis
from redis import Redis
from redis.commands.search.field import TextField, NumericField, TagField, VectorField
from redis.commands.search.indexDefinition import IndexDefinition, IndexType
from redis.commands.search.query import Query
from redis_om import JsonModel, Field, get_redis_connection
from redis_om import Migrator
import hiredis  # C-accelerated parser for better performance

logger = logging.getLogger(__name__)


class RedisAIConnectionPool:
    """
    Optimized Redis connection pool with AI features support.
    Uses hiredis for C-accelerated parsing.
    """
    
    def __init__(
        self,
        host: str = "localhost",
        port: int = 6379,
        db: int = 0,
        password: Optional[str] = None,
        max_connections: int = 50,
        socket_keepalive: bool = True,
        socket_keepalive_options: Optional[Dict] = None,
        health_check_interval: int = 30,
        retry_on_error: List[Exception] = None,
        decode_responses: bool = True
    ):
        """
        Initialize Redis connection pool with AI features.
        
        Args:
            host: Redis host
            port: Redis port
            db: Database number
            password: Redis password
            max_connections: Maximum connections in pool
            socket_keepalive: Enable TCP keepalive
            socket_keepalive_options: TCP keepalive options
            health_check_interval: Health check interval in seconds
            retry_on_error: Exceptions to retry on
            decode_responses: Decode responses to strings
        """
        self.host = host
        self.port = port
        self.db = db
        self.password = password
        
        # TCP keepalive options for production
        if socket_keepalive_options is None:
            socket_keepalive_options = {
                1: 1,  # TCP_KEEPIDLE
                2: 3,  # TCP_KEEPINTVL
                3: 5,  # TCP_KEEPCNT
            }
        
        # Retry on network errors
        if retry_on_error is None:
            retry_on_error = [
                redis.ConnectionError,
                redis.TimeoutError,
                redis.BusyLoadingError
            ]
        
        # Create connection pool with optimizations
        self.pool = redis.ConnectionPool(
            host=host,
            port=port,
            db=db,
            password=password,
            max_connections=max_connections,
            socket_keepalive=socket_keepalive,
            socket_keepalive_options=socket_keepalive_options,
            health_check_interval=health_check_interval,
            retry_on_error=retry_on_error,
            decode_responses=decode_responses,
            parser_class=hiredis.Parser  # Use C-accelerated parser
        )
        
        # Create Redis client
        self.client = redis.Redis(connection_pool=self.pool)
        
        # Test connection
        try:
            self.client.ping()
            logger.info(f"Redis AI connection established to {host}:{port}")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise
    
    def get_client(self) -> Redis:
        """Get Redis client from pool"""
        return self.client
    
    def close(self):
        """Close all connections in pool"""
        self.pool.disconnect()


class AgentState(JsonModel):
    """
    Redis OM model for agent state storage using RedisJSON.
    Provides automatic serialization and indexing.
    """
    agent_id: str = Field(index=True)
    agent_type: str = Field(index=True)
    status: str = Field(index=True, default="idle")
    created_at: float = Field(default_factory=time.time)
    updated_at: float = Field(default_factory=time.time)
    context: Dict = Field(default_factory=dict)
    memory: List[Dict] = Field(default_factory=list)
    metrics: Dict = Field(default_factory=dict)
    
    class Meta:
        database = get_redis_connection(decode_responses=True)


@dataclass
class VectorDocument:
    """Document with vector embedding for similarity search"""
    id: str
    content: str
    embedding: np.ndarray
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)


class RedisAIManager:
    """
    Comprehensive Redis AI manager for agents and MCP systems.
    Implements vector search, session management, and real-time communication.
    """
    
    # Prefixes for different data types
    PREFIX_SESSION = "session:"
    PREFIX_AGENT = "agent:"
    PREFIX_VECTOR = "vec:"
    PREFIX_METRIC = "metric:"
    PREFIX_CACHE = "cache:"
    PREFIX_LOCK = "lock:"
    PREFIX_PUBSUB = "pubsub:"
    
    def __init__(
        self,
        connection_pool: Optional[RedisAIConnectionPool] = None,
        vector_dim: int = 1536,  # OpenAI embedding dimension
        vector_index_name: str = "agent_vectors"
    ):
        """
        Initialize Redis AI Manager.
        
        Args:
            connection_pool: Redis connection pool
            vector_dim: Dimension of vector embeddings
            vector_index_name: Name for vector search index
        """
        if connection_pool:
            self.redis = connection_pool.get_client()
        else:
            # Create default connection
            self.redis = redis.Redis(
                host="localhost",
                port=6379,
                decode_responses=True,
                health_check_interval=30
            )
        
        self.vector_dim = vector_dim
        self.vector_index_name = vector_index_name
        
        # Initialize vector search index
        self._initialize_vector_index()
        
        # Initialize Redis OM models
        Migrator().run()
        
        logger.info("Redis AI Manager initialized with vector search and AI features")
    
    def _initialize_vector_index(self):
        """Initialize vector similarity search index"""
        try:
            # Check if index exists
            self.redis.ft(self.vector_index_name).info()
            logger.info(f"Vector index '{self.vector_index_name}' already exists")
        except:
            # Create new index
            schema = (
                TextField("content"),
                TagField("agent_id"),
                TagField("type"),
                NumericField("timestamp"),
                VectorField(
                    "embedding",
                    "FLAT",  # Use FLAT for small datasets, HNSW for large
                    {
                        "TYPE": "FLOAT32",
                        "DIM": self.vector_dim,
                        "DISTANCE_METRIC": "COSINE"
                    }
                )
            )
            
            definition = IndexDefinition(
                prefix=[self.PREFIX_VECTOR],
                index_type=IndexType.HASH
            )
            
            self.redis.ft(self.vector_index_name).create_index(
                fields=schema,
                definition=definition
            )
            
            logger.info(f"Created vector index '{self.vector_index_name}'")
    
    # ========== Session Management with Expiration ==========
    
    def create_session(
        self,
        session_id: str,
        user_id: str,
        data: Dict[str, Any],
        ttl: int = 3600
    ) -> bool:
        """
        Create a session with automatic expiration.
        
        Args:
            session_id: Unique session identifier
            user_id: User identifier
            data: Session data
            ttl: Time to live in seconds
            
        Returns:
            Success status
        """
        key = f"{self.PREFIX_SESSION}{session_id}"
        
        session_data = {
            "session_id": session_id,
            "user_id": user_id,
            "created_at": time.time(),
            "last_activity": time.time(),
            **data
        }
        
        # Store as JSON with expiration
        pipe = self.redis.pipeline()
        pipe.json().set(key, "$", session_data)
        pipe.expire(key, ttl)
        
        # Add to user's session set
        user_sessions_key = f"{self.PREFIX_SESSION}user:{user_id}"
        pipe.sadd(user_sessions_key, session_id)
        pipe.expire(user_sessions_key, ttl)
        
        results = pipe.execute()
        return all(results)
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session data"""
        key = f"{self.PREFIX_SESSION}{session_id}"
        data = self.redis.json().get(key)
        
        if data:
            # Update last activity
            self.redis.json().set(key, "$.last_activity", time.time())
        
        return data
    
    def invalidate_user_sessions(self, user_id: str) -> int:
        """
        Invalidate all sessions for a user (for password change).
        
        Args:
            user_id: User identifier
            
        Returns:
            Number of sessions invalidated
        """
        user_sessions_key = f"{self.PREFIX_SESSION}user:{user_id}"
        session_ids = self.redis.smembers(user_sessions_key)
        
        if not session_ids:
            return 0
        
        pipe = self.redis.pipeline()
        for session_id in session_ids:
            pipe.delete(f"{self.PREFIX_SESSION}{session_id}")
        pipe.delete(user_sessions_key)
        
        pipe.execute()
        return len(session_ids)
    
    # ========== Agent State Management ==========
    
    def save_agent_state(self, agent: AgentState) -> str:
        """Save agent state using Redis OM"""
        agent.updated_at = time.time()
        agent.save()
        
        # Also store in regular Redis for fast access
        key = f"{self.PREFIX_AGENT}{agent.agent_id}"
        self.redis.json().set(key, "$", agent.dict())
        
        return agent.pk
    
    def get_agent_state(self, agent_id: str) -> Optional[AgentState]:
        """Get agent state"""
        try:
            return AgentState.get(agent_id)
        except:
            # Fallback to regular Redis
            key = f"{self.PREFIX_AGENT}{agent_id}"
            data = self.redis.json().get(key)
            if data:
                return AgentState(**data)
            return None
    
    def update_agent_metrics(self, agent_id: str, metrics: Dict[str, Any]):
        """Update agent metrics"""
        key = f"{self.PREFIX_AGENT}{agent_id}"
        
        # Update metrics and timestamp
        pipe = self.redis.pipeline()
        pipe.json().set(key, "$.metrics", metrics)
        pipe.json().set(key, "$.updated_at", time.time())
        pipe.execute()
    
    # ========== Vector Similarity Search ==========
    
    def store_vector(
        self,
        doc_id: str,
        content: str,
        embedding: Union[List[float], np.ndarray],
        agent_id: str,
        doc_type: str = "memory",
        metadata: Optional[Dict] = None
    ) -> bool:
        """
        Store document with vector embedding for similarity search.
        
        Args:
            doc_id: Document identifier
            content: Text content
            embedding: Vector embedding
            agent_id: Associated agent ID
            doc_type: Document type
            metadata: Additional metadata
            
        Returns:
            Success status
        """
        if isinstance(embedding, list):
            embedding = np.array(embedding, dtype=np.float32)
        
        key = f"{self.PREFIX_VECTOR}{doc_id}"
        
        doc_data = {
            "content": content,
            "embedding": embedding.tobytes(),
            "agent_id": agent_id,
            "type": doc_type,
            "timestamp": time.time(),
            "metadata": json.dumps(metadata or {})
        }
        
        return self.redis.hset(key, mapping=doc_data) > 0
    
    def search_similar_vectors(
        self,
        query_embedding: Union[List[float], np.ndarray],
        k: int = 10,
        agent_id: Optional[str] = None,
        doc_type: Optional[str] = None
    ) -> List[Tuple[str, float, Dict]]:
        """
        Search for similar vectors using cosine similarity.
        
        Args:
            query_embedding: Query vector
            k: Number of results
            agent_id: Filter by agent ID
            doc_type: Filter by document type
            
        Returns:
            List of (doc_id, score, data) tuples
        """
        if isinstance(query_embedding, list):
            query_embedding = np.array(query_embedding, dtype=np.float32)
        
        # Build query
        query_str = f"*=>[KNN {k} @embedding $vec AS score]"
        
        # Add filters
        filters = []
        if agent_id:
            filters.append(f"@agent_id:{{{agent_id}}}")
        if doc_type:
            filters.append(f"@type:{{{doc_type}}}")
        
        if filters:
            query_str = f"({' '.join(filters)}) {query_str}"
        
        query = Query(query_str).sort_by("score").return_fields(
            "content", "agent_id", "type", "timestamp", "metadata", "score"
        ).dialect(2)
        
        # Execute search
        results = self.redis.ft(self.vector_index_name).search(
            query,
            query_params={"vec": query_embedding.tobytes()}
        )
        
        # Parse results
        output = []
        for doc in results.docs:
            output.append((
                doc.id,
                float(doc.score),
                {
                    "content": doc.content,
                    "agent_id": doc.agent_id,
                    "type": doc.type,
                    "timestamp": float(doc.timestamp),
                    "metadata": json.loads(doc.metadata) if doc.metadata else {}
                }
            ))
        
        return output
    
    # ========== Caching with TTL ==========
    
    def cache_set(
        self,
        key: str,
        value: Any,
        ttl: int = 300,
        namespace: str = "default"
    ) -> bool:
        """
        Set cache value with TTL.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds
            namespace: Cache namespace
            
        Returns:
            Success status
        """
        cache_key = f"{self.PREFIX_CACHE}{namespace}:{key}"
        
        # Serialize complex objects
        if isinstance(value, (dict, list)):
            value = json.dumps(value)
        
        return self.redis.setex(cache_key, ttl, value)
    
    def cache_get(self, key: str, namespace: str = "default") -> Optional[Any]:
        """Get cached value"""
        cache_key = f"{self.PREFIX_CACHE}{namespace}:{key}"
        value = self.redis.get(cache_key)
        
        # Try to deserialize JSON
        if value:
            try:
                return json.loads(value)
            except:
                return value
        
        return None
    
    def cache_invalidate(self, pattern: str, namespace: str = "default") -> int:
        """Invalidate cache entries matching pattern"""
        pattern_key = f"{self.PREFIX_CACHE}{namespace}:{pattern}"
        keys = self.redis.keys(pattern_key)
        
        if keys:
            return self.redis.delete(*keys)
        
        return 0
    
    # ========== Distributed Locking ==========
    
    def acquire_lock(
        self,
        resource: str,
        timeout: int = 10,
        blocking: bool = True,
        blocking_timeout: int = 5
    ) -> Optional[redis.lock.Lock]:
        """
        Acquire distributed lock for resource.
        
        Args:
            resource: Resource to lock
            timeout: Lock timeout in seconds
            blocking: Whether to block waiting for lock
            blocking_timeout: How long to wait for lock
            
        Returns:
            Lock object if acquired, None otherwise
        """
        lock_key = f"{self.PREFIX_LOCK}{resource}"
        lock = self.redis.lock(
            lock_key,
            timeout=timeout,
            blocking=blocking,
            blocking_timeout=blocking_timeout
        )
        
        if lock.acquire():
            return lock
        
        return None
    
    # ========== Pub/Sub for Agent Communication ==========
    
    def publish_agent_event(
        self,
        agent_id: str,
        event_type: str,
        data: Dict[str, Any]
    ) -> int:
        """
        Publish agent event to channel.
        
        Args:
            agent_id: Agent identifier
            event_type: Event type
            data: Event data
            
        Returns:
            Number of subscribers that received the message
        """
        channel = f"{self.PREFIX_PUBSUB}agent:{agent_id}"
        
        message = json.dumps({
            "agent_id": agent_id,
            "event_type": event_type,
            "timestamp": time.time(),
            "data": data
        })
        
        return self.redis.publish(channel, message)
    
    def subscribe_agent_events(
        self,
        agent_id: str,
        callback: callable,
        event_types: Optional[List[str]] = None
    ):
        """
        Subscribe to agent events.
        
        Args:
            agent_id: Agent identifier
            callback: Callback function for events
            event_types: Filter by event types
        """
        channel = f"{self.PREFIX_PUBSUB}agent:{agent_id}"
        pubsub = self.redis.pubsub()
        pubsub.subscribe(channel)
        
        for message in pubsub.listen():
            if message["type"] == "message":
                try:
                    data = json.loads(message["data"])
                    
                    # Filter by event type if specified
                    if event_types and data["event_type"] not in event_types:
                        continue
                    
                    callback(data)
                except Exception as e:
                    logger.error(f"Error processing pubsub message: {e}")
    
    # ========== Time Series for Metrics ==========
    
    def record_metric(
        self,
        metric_name: str,
        value: float,
        labels: Optional[Dict[str, str]] = None,
        timestamp: Optional[int] = None
    ):
        """
        Record time series metric.
        
        Args:
            metric_name: Metric name
            value: Metric value
            labels: Metric labels
            timestamp: Unix timestamp (auto if None)
        """
        key = f"{self.PREFIX_METRIC}{metric_name}"
        
        if labels:
            label_str = ":".join(f"{k}={v}" for k, v in labels.items())
            key = f"{key}:{label_str}"
        
        if timestamp is None:
            timestamp = int(time.time() * 1000)  # Milliseconds
        
        # Use Redis sorted set for time series
        self.redis.zadd(key, {f"{value}:{timestamp}": timestamp})
        
        # Expire old data (keep 7 days)
        cutoff = int((time.time() - 7 * 86400) * 1000)
        self.redis.zremrangebyscore(key, 0, cutoff)
    
    def get_metrics(
        self,
        metric_name: str,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None,
        labels: Optional[Dict[str, str]] = None
    ) -> List[Tuple[float, int]]:
        """
        Get time series metrics.
        
        Args:
            metric_name: Metric name
            start_time: Start timestamp
            end_time: End timestamp
            labels: Metric labels
            
        Returns:
            List of (value, timestamp) tuples
        """
        key = f"{self.PREFIX_METRIC}{metric_name}"
        
        if labels:
            label_str = ":".join(f"{k}={v}" for k, v in labels.items())
            key = f"{key}:{label_str}"
        
        if start_time is None:
            start_time = 0
        if end_time is None:
            end_time = int(time.time() * 1000)
        
        # Get data from sorted set
        data = self.redis.zrangebyscore(key, start_time, end_time, withscores=True)
        
        # Parse results
        results = []
        for item, score in data:
            value = float(item.split(":")[0])
            timestamp = int(score)
            results.append((value, timestamp))
        
        return results
    
    # ========== Health Check ==========
    
    def health_check(self) -> Dict[str, Any]:
        """
        Perform comprehensive health check.
        
        Returns:
            Health status and metrics
        """
        try:
            # Basic ping
            ping_start = time.time()
            self.redis.ping()
            ping_time = (time.time() - ping_start) * 1000
            
            # Get info
            info = self.redis.info()
            
            # Get memory info
            memory_info = self.redis.memory_stats()
            
            # Check vector index
            vector_index_ok = False
            try:
                self.redis.ft(self.vector_index_name).info()
                vector_index_ok = True
            except:
                pass
            
            return {
                "status": "healthy",
                "ping_ms": round(ping_time, 2),
                "version": info.get("redis_version", "unknown"),
                "connected_clients": info.get("connected_clients", 0),
                "used_memory_human": info.get("used_memory_human", "unknown"),
                "used_memory_peak_human": info.get("used_memory_peak_human", "unknown"),
                "total_connections_received": info.get("total_connections_received", 0),
                "total_commands_processed": info.get("total_commands_processed", 0),
                "vector_index_ready": vector_index_ok,
                "uptime_days": info.get("uptime_in_days", 0)
            }
            
        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e)
            }


# Global Redis AI manager instance
_redis_ai_manager: Optional[RedisAIManager] = None


def get_redis_ai_manager(
    host: str = "localhost",
    port: int = 6379,
    password: Optional[str] = None
) -> RedisAIManager:
    """
    Get or create global Redis AI manager instance.
    
    Args:
        host: Redis host
        port: Redis port
        password: Redis password
        
    Returns:
        RedisAIManager instance
    """
    global _redis_ai_manager
    
    if _redis_ai_manager is None:
        # Create connection pool
        pool = RedisAIConnectionPool(
            host=host,
            port=port,
            password=password,
            max_connections=50,
            socket_keepalive=True,
            health_check_interval=30
        )
        
        _redis_ai_manager = RedisAIManager(
            connection_pool=pool,
            vector_dim=1536  # OpenAI embedding dimension
        )
    
    return _redis_ai_manager