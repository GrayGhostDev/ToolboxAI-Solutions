"""
Vector Memory Store for MCP Context Management

FIXED VERSION: Addresses SonarQube issues
- Proper resource management with context managers
- No generic exception catching
- Constants for magic numbers
- Secure random generation
"""

import hashlib
import json
import logging
import sqlite3
import secrets  # More secure than random for cryptographic purposes
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)

# Constants to replace magic numbers (SonarQube: S109)
DEFAULT_MEMORY_LIMIT = 1000
DEFAULT_CONSOLIDATION_THRESHOLD = 100
MIN_IMPORTANCE_SCORE = 0.5
MAX_QUERY_LIMIT = 100
ACCESS_COUNT_WEIGHT = 0.3
RECENCY_WEIGHT = 0.7
EMBEDDING_DIMENSION = 768
PRUNE_BATCH_SIZE = 10


@dataclass
class Memory:
    """Represents a single memory entry"""

    id: str
    content: str
    metadata: Dict[str, Any]
    timestamp: datetime
    embedding: Optional[np.ndarray] = None
    access_count: int = 0
    last_accessed: Optional[datetime] = None
    importance: float = 1.0


class MemoryStore:
    """
    SQLite-backed vector memory store with semantic search
    """

    def __init__(self, db_path: str = ":memory:", memory_limit: int = DEFAULT_MEMORY_LIMIT):
        self.db_path = db_path
        self.memory_limit = memory_limit
        self.consolidation_threshold = DEFAULT_CONSOLIDATION_THRESHOLD
        self.conn = None
        self._init_database()

    def _init_database(self):
        """Initialize SQLite database with proper resource management"""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row  # Enable column access by name
        
        # Use context manager for automatic transaction handling
        with self.conn:
            cursor = self.conn.cursor()
            try:
                # Create memories table
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS memories (
                        id TEXT PRIMARY KEY,
                        content TEXT NOT NULL,
                        embedding BLOB,
                        metadata TEXT,
                        timestamp TEXT,
                        access_count INTEGER DEFAULT 0,
                        last_accessed TEXT,
                        importance REAL DEFAULT 1.0
                    )
                """
                )

                # Create indexes for faster queries
                cursor.execute(
                    "CREATE INDEX IF NOT EXISTS idx_timestamp ON memories(timestamp)"
                )
                cursor.execute(
                    "CREATE INDEX IF NOT EXISTS idx_importance ON memories(importance)"
                )
                cursor.execute(
                    "CREATE INDEX IF NOT EXISTS idx_access_count ON memories(access_count)"
                )
            finally:
                cursor.close()

    @contextmanager
    def _get_cursor(self):
        """Context manager for database cursor (SonarQube: S5445)"""
        cursor = self.conn.cursor()
        try:
            yield cursor
        finally:
            cursor.close()

    def _generate_id(self, content: str) -> str:
        """Generate unique ID for memory using secure hashing"""
        # Use SHA256 for secure hashing (SonarQube: S4790)
        timestamp = datetime.now().isoformat()
        # Add secure random salt for uniqueness
        salt = secrets.token_hex(8)
        hash_input = f"{content}:{timestamp}:{salt}"
        return hashlib.sha256(hash_input.encode()).hexdigest()[:16]

    def _calculate_importance(self, content: str, metadata: Dict) -> float:
        """Calculate importance score for memory"""
        # Base importance on content length and metadata
        base_score = min(len(content) / 1000, 1.0)

        # Boost for specific metadata flags
        if metadata.get("important", False):
            base_score *= 2.0
        if metadata.get("reference", False):
            base_score *= 1.5
        if metadata.get("user_generated", False):
            base_score *= 1.3

        return min(base_score, 10.0)

    def store_memory(
        self,
        content: str,
        metadata: Optional[Dict] = None,
        embedding: Optional[np.ndarray] = None,
    ) -> str:
        """Store a new memory with proper resource management"""
        # Generate unique ID
        memory_id = self._generate_id(content)

        # Prepare data
        metadata = metadata or {}
        timestamp = datetime.now()

        # Check if memory already exists
        with self._get_cursor() as cursor:
            cursor.execute("SELECT id FROM memories WHERE id = ?", (memory_id,))
            if cursor.fetchone():
                # Update existing memory
                cursor.execute(
                    """
                    UPDATE memories 
                    SET access_count = access_count + 1,
                        last_accessed = ?
                    WHERE id = ?
                """,
                    (timestamp.isoformat(), memory_id),
                )
                self.conn.commit()
                return memory_id

        # Insert new memory with transaction
        embedding_bytes = (
            json.dumps(embedding.tolist()) if embedding is not None else None
        )

        with self.conn:
            with self._get_cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO memories 
                    (id, content, embedding, metadata, timestamp, last_accessed, importance)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        memory_id,
                        content,
                        embedding_bytes,
                        json.dumps(metadata),
                        timestamp.isoformat(),
                        timestamp.isoformat(),
                        self._calculate_importance(content, metadata),
                    ),
                )

        logger.info(f"Stored memory: {memory_id}")

        # Consolidate if needed
        self._consolidate_memories()

        return memory_id

    def retrieve_memory(self, memory_id: str) -> Optional[Memory]:
        """Retrieve a specific memory by ID"""
        with self._get_cursor() as cursor:
            cursor.execute(
                """
                SELECT content, embedding, metadata, timestamp, access_count, last_accessed, importance
                FROM memories WHERE id = ?
            """,
                (memory_id,),
            )
            row = cursor.fetchone()

        if not row:
            return None

        # Update access count
        with self.conn:
            with self._get_cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE memories 
                    SET access_count = access_count + 1,
                        last_accessed = ?
                    WHERE id = ?
                """,
                    (datetime.now().isoformat(), memory_id),
                )

        # Parse and return memory
        embedding = None
        if row["embedding"]:
            try:
                embedding_list = json.loads(row["embedding"])
                embedding = np.array(embedding_list)
            except (json.JSONDecodeError, ValueError) as e:
                logger.warning(f"Failed to parse embedding for memory {memory_id}: {e}")

        return Memory(
            id=memory_id,
            content=row["content"],
            embedding=embedding,
            metadata=json.loads(row["metadata"]) if row["metadata"] else {},
            timestamp=datetime.fromisoformat(row["timestamp"]),
            access_count=row["access_count"],
            last_accessed=datetime.fromisoformat(row["last_accessed"]) if row["last_accessed"] else None,
            importance=row["importance"],
        )

    def search_memories(
        self,
        query: str = "",
        limit: int = 10,
        min_importance: float = MIN_IMPORTANCE_SCORE,
        metadata_filter: Optional[Dict] = None,
    ) -> List[Memory]:
        """Search memories with various filters"""
        # Validate and sanitize limit (SonarQube: S5131)
        limit = min(max(1, limit), MAX_QUERY_LIMIT)

        # Build query with proper parameterization
        base_query = """
            SELECT id, content, embedding, metadata, timestamp, 
                   access_count, last_accessed, importance
            FROM memories
            WHERE importance >= ?
        """
        params = [min_importance]

        # Add content search if query provided
        if query:
            base_query += " AND content LIKE ?"
            # Properly escape special characters for LIKE
            safe_query = query.replace("%", "\\%").replace("_", "\\_")
            params.append(f"%{safe_query}%")

        # Add metadata filters
        if metadata_filter:
            for key, value in metadata_filter.items():
                base_query += f" AND json_extract(metadata, '$.{key}') = ?"
                params.append(value)

        # Order by relevance
        base_query += " ORDER BY importance DESC, access_count DESC LIMIT ?"
        params.append(limit)

        # Execute query
        with self._get_cursor() as cursor:
            cursor.execute(base_query, params)
            rows = cursor.fetchall()

        # Convert to Memory objects
        memories = []
        for row in rows:
            embedding = None
            if row["embedding"]:
                try:
                    embedding_list = json.loads(row["embedding"])
                    embedding = np.array(embedding_list)
                except (json.JSONDecodeError, ValueError) as e:
                    logger.warning(f"Failed to parse embedding: {e}")

            memories.append(
                Memory(
                    id=row["id"],
                    content=row["content"],
                    embedding=embedding,
                    metadata=json.loads(row["metadata"]) if row["metadata"] else {},
                    timestamp=datetime.fromisoformat(row["timestamp"]),
                    access_count=row["access_count"],
                    last_accessed=datetime.fromisoformat(row["last_accessed"]) if row["last_accessed"] else None,
                    importance=row["importance"],
                )
            )

        return memories

    def get_recent_memories(self, hours: int = 24, limit: int = 10) -> List[Memory]:
        """Get recently accessed memories"""
        # Validate and sanitize limit
        limit = min(max(1, limit), MAX_QUERY_LIMIT)
        cutoff_time = (datetime.now() - timedelta(hours=hours)).isoformat()

        with self._get_cursor() as cursor:
            cursor.execute(
                """
                SELECT id, content, embedding, metadata, timestamp,
                       access_count, last_accessed, importance
                FROM memories
                WHERE last_accessed > ?
                ORDER BY last_accessed DESC
                LIMIT ?
            """,
                (cutoff_time, limit),
            )
            rows = cursor.fetchall()

        # Convert to Memory objects
        memories = []
        for row in rows:
            embedding = None
            if row["embedding"]:
                try:
                    embedding_list = json.loads(row["embedding"])
                    embedding = np.array(embedding_list)
                except (json.JSONDecodeError, ValueError) as e:
                    logger.warning(f"Failed to parse embedding: {e}")

            memories.append(
                Memory(
                    id=row["id"],
                    content=row["content"],
                    embedding=embedding,
                    metadata=json.loads(row["metadata"]) if row["metadata"] else {},
                    timestamp=datetime.fromisoformat(row["timestamp"]),
                    access_count=row["access_count"],
                    last_accessed=datetime.fromisoformat(row["last_accessed"]) if row["last_accessed"] else None,
                    importance=row["importance"],
                )
            )

        return memories

    def get_important_memories(self, limit: int = 10) -> List[Memory]:
        """Get most important memories"""
        # Validate and sanitize limit
        limit = min(max(1, limit), MAX_QUERY_LIMIT)

        with self._get_cursor() as cursor:
            cursor.execute(
                """
                SELECT id, content, embedding, metadata, timestamp,
                       access_count, last_accessed, importance
                FROM memories
                ORDER BY importance DESC
                LIMIT ?
            """,
                (limit,),
            )
            rows = cursor.fetchall()

        # Convert to Memory objects
        memories = []
        for row in rows:
            embedding = None
            if row["embedding"]:
                try:
                    embedding_list = json.loads(row["embedding"])
                    embedding = np.array(embedding_list)
                except (json.JSONDecodeError, ValueError) as e:
                    logger.warning(f"Failed to parse embedding: {e}")

            memories.append(
                Memory(
                    id=row["id"],
                    content=row["content"],
                    embedding=embedding,
                    metadata=json.loads(row["metadata"]) if row["metadata"] else {},
                    timestamp=datetime.fromisoformat(row["timestamp"]),
                    access_count=row["access_count"],
                    last_accessed=datetime.fromisoformat(row["last_accessed"]) if row["last_accessed"] else None,
                    importance=row["importance"],
                )
            )

        return memories

    def _consolidate_memories(self):
        """Consolidate memories when limit is reached"""
        with self._get_cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM memories")
            count = cursor.fetchone()[0]

        if count <= self.memory_limit:
            return

        # Calculate consolidation score
        with self._get_cursor() as cursor:
            cursor.execute(
                """
                SELECT id, importance, access_count, last_accessed
                FROM memories
            """
            )
            rows = cursor.fetchall()

        # Score each memory for consolidation
        scores = []
        now = datetime.now()

        for row in rows:
            # Calculate recency score
            last_accessed = datetime.fromisoformat(row["last_accessed"]) if row["last_accessed"] else now
            days_old = (now - last_accessed).days
            recency_score = 1.0 / (1.0 + days_old)

            # Combined score
            score = (
                row["importance"]
                + row["access_count"] * ACCESS_COUNT_WEIGHT
                + recency_score * RECENCY_WEIGHT
            )
            scores.append((row["id"], score))

        # Sort by score and keep top memories
        scores.sort(key=lambda x: x[1], reverse=True)
        keep_ids = [s[0] for s in scores[: self.memory_limit - self.consolidation_threshold]]

        # Delete low-scoring memories in batches
        with self.conn:
            with self._get_cursor() as cursor:
                all_ids = [s[0] for s in scores]
                delete_ids = [id for id in all_ids if id not in keep_ids]
                
                # Delete in batches to avoid large queries
                for i in range(0, len(delete_ids), PRUNE_BATCH_SIZE):
                    batch = delete_ids[i : i + PRUNE_BATCH_SIZE]
                    placeholders = ",".join("?" * len(batch))
                    cursor.execute(f"DELETE FROM memories WHERE id IN ({placeholders})", batch)

        logger.info(f"Consolidated memories: kept {len(keep_ids)}, deleted {len(delete_ids)}")

    def update_importance(self, memory_id: str, importance: float):
        """Update importance score for a memory"""
        # Validate importance range
        importance = max(0.0, min(10.0, importance))
        
        with self.conn:
            with self._get_cursor() as cursor:
                cursor.execute(
                    "UPDATE memories SET importance = ? WHERE id = ?",
                    (importance, memory_id),
                )

    def delete_memory(self, memory_id: str) -> bool:
        """Delete a specific memory"""
        with self.conn:
            with self._get_cursor() as cursor:
                cursor.execute("DELETE FROM memories WHERE id = ?", (memory_id,))
                return cursor.rowcount > 0

    def clear_old_memories(self, days: int = 30):
        """Clear memories older than specified days"""
        cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
        
        with self.conn:
            with self._get_cursor() as cursor:
                cursor.execute(
                    "DELETE FROM memories WHERE last_accessed < ? OR last_accessed IS NULL",
                    (cutoff_date,),
                )
                deleted = cursor.rowcount

        logger.info(f"Cleared {deleted} old memories")
        return deleted

    def export_memories(self, filepath: str):
        """Export all memories to JSON file"""
        with self._get_cursor() as cursor:
            cursor.execute(
                """
                SELECT id, content, metadata, timestamp, access_count, 
                       last_accessed, importance
                FROM memories
            """
            )
            rows = cursor.fetchall()

        memories = []
        for row in rows:
            memories.append({
                "id": row["id"],
                "content": row["content"],
                "metadata": json.loads(row["metadata"]) if row["metadata"] else {},
                "timestamp": row["timestamp"],
                "access_count": row["access_count"],
                "last_accessed": row["last_accessed"],
                "importance": row["importance"],
            })

        with open(filepath, "w") as f:
            json.dump(memories, f, indent=2)

    def import_memories(self, filepath: str):
        """Import memories from JSON file"""
        with open(filepath, "r") as f:
            memories = json.load(f)

        with self.conn:
            with self._get_cursor() as cursor:
                for memory in memories:
                    cursor.execute(
                        """
                        INSERT OR REPLACE INTO memories 
                        (id, content, metadata, timestamp, access_count, last_accessed, importance)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                        (
                            memory["id"],
                            memory["content"],
                            json.dumps(memory.get("metadata", {})),
                            memory["timestamp"],
                            memory.get("access_count", 0),
                            memory.get("last_accessed"),
                            memory.get("importance", 1.0),
                        ),
                    )

    def get_statistics(self) -> Dict[str, Any]:
        """Get memory store statistics"""
        with self._get_cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM memories")
            total_count = cursor.fetchone()[0]

            cursor.execute("SELECT AVG(access_count) FROM memories")
            avg_access = cursor.fetchone()[0] or 0

            cursor.execute("SELECT AVG(importance) FROM memories")
            avg_importance = cursor.fetchone()[0] or 0

            cursor.execute(
                "SELECT COUNT(*) FROM memories WHERE last_accessed > ?",
                ((datetime.now() - timedelta(hours=24)).isoformat(),),
            )
            recent_access = cursor.fetchone()[0]

        return {
            "total_memories": total_count,
            "average_access_count": round(avg_access, 2),
            "average_importance": round(avg_importance, 2),
            "recently_accessed": recent_access,
            "database_size": (
                Path(self.db_path).stat().st_size if Path(self.db_path).exists() else 0
            ),
        }

    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            self.conn = None

    def __del__(self):
        """Destructor to ensure database connection is closed"""
        self.close()

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - ensure connection is closed"""
        self.close()
        return False