"""
Memory Store for MCP - Persistent storage with vector embeddings
"""

import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import numpy as np
from pathlib import Path
import sqlite3
import hashlib
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


@dataclass
class Memory:
    """Represents a memory entry with embedding"""

    id: str
    content: str
    embedding: Optional[np.ndarray]
    metadata: Dict[str, Any]
    timestamp: datetime
    access_count: int = 0
    last_accessed: Optional[datetime] = None


class MemoryStore:
    """
    Persistent memory storage with vector similarity search.

    Features:
    - SQLite backend for persistence
    - Vector embeddings for semantic search
    - Memory importance scoring
    - Automatic memory consolidation
    """

    def __init__(self, db_path: str = "memory_store.db", embedding_dim: int = 1536):
        self.db_path = db_path
        self.embedding_dim = embedding_dim
        self.conn = None
        self._init_database()

    def _init_database(self):
        """Initialize SQLite database"""
        self.conn = sqlite3.connect(self.db_path)
        cursor = self.conn.cursor()

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

        # Create index for faster queries
        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_timestamp 
            ON memories(timestamp)
        """
        )

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_importance 
            ON memories(importance)
        """
        )

        self.conn.commit()

    def store_memory(
        self,
        key_or_content: str,
        content_or_metadata: Optional[Dict] = None,
        embedding: Optional[np.ndarray] = None,
    ) -> str:
        """Store a new memory
        
        Can be called two ways:
        1. store_memory(content, metadata, embedding) - original signature
        2. store_memory(key, content_dict) - test signature where content_dict contains all data
        """
        # Handle both calling patterns
        if isinstance(content_or_metadata, dict) and embedding is None:
            # Test pattern: store_memory("key", {"content": ..., "metadata": ...})
            memory_id = self._generate_id(key_or_content)
            content = json.dumps(content_or_metadata) if not isinstance(content_or_metadata.get("content"), str) else content_or_metadata.get("content", json.dumps(content_or_metadata))
            metadata = content_or_metadata.get("metadata", content_or_metadata)
            embedding = None
        else:
            # Original pattern: store_memory(content, metadata, embedding)
            content = key_or_content
            metadata = content_or_metadata or {}
            memory_id = self._generate_id(content)

        # Prepare data
        metadata = metadata or {}
        timestamp = datetime.now()

        cursor = self.conn.cursor()

        # Check if memory already exists
        cursor.execute("SELECT id FROM memories WHERE id = ?", (memory_id,))
        if cursor.fetchone():
            # Update existing memory
            self._update_memory_access(memory_id)
            return memory_id

        # Store new memory
        cursor.execute(
            """
            INSERT INTO memories (id, content, embedding, metadata, timestamp, importance)
            VALUES (?, ?, ?, ?, ?, ?)
        """,
            (
                memory_id,
                content,
                json.dumps(embedding.tolist()) if embedding is not None else None,
                json.dumps(metadata),
                timestamp.isoformat(),
                self._calculate_importance(content, metadata),
            ),
        )

        self.conn.commit()
        logger.info(f"Stored memory: {memory_id}")

        # Consolidate if needed
        self._consolidate_memories()

        return memory_id

    def retrieve_memory(self, memory_id: str) -> Optional[Dict]:
        """Retrieve a specific memory by ID"""
        cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT content, embedding, metadata, timestamp, access_count, last_accessed
            FROM memories WHERE id = ?
        """,
            (memory_id,),
        )

        row = cursor.fetchone()
        if not row:
            return None

        # Update access count
        self._update_memory_access(memory_id)

        # Parse data
        (
            content,
            embedding_blob,
            metadata_json,
            timestamp_str,
            access_count,
            last_accessed_str,
        ) = row

        # Return as dictionary for JSON serialization
        return {
            "id": memory_id,
            "content": content,
            "embedding": json.loads(embedding_blob) if embedding_blob else None,
            "metadata": json.loads(metadata_json) if metadata_json else {},
            "timestamp": timestamp_str,
            "access_count": access_count + 1,
            "last_accessed": last_accessed_str
        }

    def search_similar(
        self, query_embedding: np.ndarray, limit: int = 10, threshold: float = 0.7
    ) -> List[Tuple[Memory, float]]:
        """Search for similar memories using vector similarity"""
        cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT id, content, embedding, metadata, timestamp, access_count, last_accessed
            FROM memories WHERE embedding IS NOT NULL
        """
        )

        results = []
        for row in cursor.fetchall():
            (
                memory_id,
                content,
                embedding_blob,
                metadata_json,
                timestamp_str,
                access_count,
                last_accessed_str,
            ) = row

            # Load embedding
            memory_embedding = np.array(json.loads(embedding_blob))

            # Calculate cosine similarity
            similarity = self._cosine_similarity(query_embedding, memory_embedding)

            if similarity >= threshold:
                memory = Memory(
                    id=memory_id,
                    content=content,
                    embedding=memory_embedding,
                    metadata=json.loads(metadata_json),
                    timestamp=datetime.fromisoformat(timestamp_str),
                    access_count=access_count,
                    last_accessed=(
                        datetime.fromisoformat(last_accessed_str)
                        if last_accessed_str
                        else None
                    ),
                )
                results.append((memory, similarity))

        # Sort by similarity
        results.sort(key=lambda x: x[1], reverse=True)

        # Update access for retrieved memories
        for memory, _ in results[:limit]:
            self._update_memory_access(memory.id)

        return results[:limit]

    def search_by_metadata(self, filters: Dict[str, Any]) -> List[Memory]:
        """Search memories by metadata filters"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT id, content, metadata, timestamp FROM memories")

        results = []
        for row in cursor.fetchall():
            memory_id, content, metadata_json, timestamp_str = row
            metadata = json.loads(metadata_json)

            # Check if all filters match
            match = True
            for key, value in filters.items():
                if key not in metadata or metadata[key] != value:
                    match = False
                    break

            if match:
                results.append(
                    Memory(
                        id=memory_id,
                        content=content,
                        embedding=None,  # Skip loading embedding for metadata search
                        metadata=metadata,
                        timestamp=datetime.fromisoformat(timestamp_str),
                        access_count=0,
                        last_accessed=None,
                    )
                )

        return results

    def get_recent_memories(self, limit: int = 20) -> List[Memory]:
        """Get most recent memories"""
        cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT id, content, metadata, timestamp, access_count, last_accessed
            FROM memories
            ORDER BY timestamp DESC
            LIMIT ?
        """,
            (limit,),
        )

        results = []
        for row in cursor.fetchall():
            (
                memory_id,
                content,
                metadata_json,
                timestamp_str,
                access_count,
                last_accessed_str,
            ) = row

            results.append(
                Memory(
                    id=memory_id,
                    content=content,
                    embedding=None,  # Skip loading embedding for listing
                    metadata=json.loads(metadata_json),
                    timestamp=datetime.fromisoformat(timestamp_str),
                    access_count=access_count,
                    last_accessed=(
                        datetime.fromisoformat(last_accessed_str)
                        if last_accessed_str
                        else None
                    ),
                )
            )

        return results

    def get_important_memories(self, limit: int = 20) -> List[Memory]:
        """Get most important memories based on importance score"""
        cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT id, content, metadata, timestamp, importance
            FROM memories
            ORDER BY importance DESC
            LIMIT ?
        """,
            (limit,),
        )

        results = []
        for row in cursor.fetchall():
            memory_id, content, metadata_json, timestamp_str, importance = row

            metadata = json.loads(metadata_json)
            metadata["importance"] = importance

            results.append(
                Memory(
                    id=memory_id,
                    content=content,
                    embedding=None,
                    metadata=metadata,
                    timestamp=datetime.fromisoformat(timestamp_str),
                    access_count=0,
                    last_accessed=None,
                )
            )

        return results

    def _generate_id(self, content: str) -> str:
        """Generate unique ID for memory"""
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    def _calculate_importance(self, content: str, metadata: Dict) -> float:
        """Calculate importance score for memory"""
        importance = 1.0

        # Increase importance for certain metadata flags
        if metadata.get("is_user_feedback"):
            importance += 0.5
        if metadata.get("is_error"):
            importance += 0.3
        if metadata.get("is_success"):
            importance += 0.2
        if metadata.get("source") == "user":
            importance += 0.4

        # Adjust based on content length (longer = potentially more important)
        content_length = len(content)
        if content_length > 500:
            importance += 0.2
        elif content_length > 1000:
            importance += 0.4

        return min(importance, 5.0)  # Cap at 5.0

    def _update_memory_access(self, memory_id: str):
        """Update access count and timestamp for memory"""
        cursor = self.conn.cursor()
        cursor.execute(
            """
            UPDATE memories 
            SET access_count = access_count + 1,
                last_accessed = ?,
                importance = importance * 1.1
            WHERE id = ?
        """,
            (datetime.now().isoformat(), memory_id),
        )
        self.conn.commit()

    def _cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """Calculate cosine similarity between two vectors"""
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return dot_product / (norm1 * norm2)

    def _consolidate_memories(self):
        """Consolidate memories to prevent database bloat"""
        cursor = self.conn.cursor()

        # Get memory count
        cursor.execute("SELECT COUNT(*) FROM memories")
        count = cursor.fetchone()[0]

        # If too many memories, remove least important/accessed
        max_memories = 10000
        if count > max_memories:
            # Delete memories with low importance and access count
            cursor.execute(
                """
                DELETE FROM memories
                WHERE id IN (
                    SELECT id FROM memories
                    ORDER BY importance * (access_count + 1) ASC
                    LIMIT ?
                )
            """,
                (count - max_memories,),
            )

            self.conn.commit()
            logger.info(
                f"Consolidated memories: removed {count - max_memories} entries"
            )

    def export_memories(self, filepath: str):
        """Export all memories to JSON file"""
        memories = self.get_recent_memories(limit=10000)

        export_data = {
            "exported_at": datetime.now().isoformat(),
            "memory_count": len(memories),
            "memories": [
                {
                    "id": m.id,
                    "content": m.content,
                    "metadata": m.metadata,
                    "timestamp": m.timestamp.isoformat(),
                    "access_count": m.access_count,
                }
                for m in memories
            ],
        }

        with open(filepath, "w") as f:
            json.dump(export_data, f, indent=2)

    def import_memories(self, filepath: str):
        """Import memories from JSON file"""
        with open(filepath, "r") as f:
            import_data = json.load(f)

        for memory_data in import_data["memories"]:
            self.store_memory(
                content=memory_data["content"], metadata=memory_data.get("metadata", {})
            )

        logger.info(f"Imported {len(import_data['memories'])} memories")

    def get_statistics(self) -> Dict[str, Any]:
        """Get memory store statistics"""
        cursor = self.conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM memories")
        total_count = cursor.fetchone()[0]

        cursor.execute("SELECT AVG(access_count) FROM memories")
        avg_access = cursor.fetchone()[0] or 0

        cursor.execute("SELECT AVG(importance) FROM memories")
        avg_importance = cursor.fetchone()[0] or 0

        cursor.execute(
            """
            SELECT COUNT(*) FROM memories 
            WHERE last_accessed > datetime('now', '-1 day')
        """
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

    def delete_memory(self, memory_id: str) -> bool:
        """Delete a memory by ID and return success status"""
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM memories WHERE id = ?", (memory_id,))
        deleted = cursor.rowcount > 0
        self.conn.commit()
        
        if deleted:
            logger.info(f"Deleted memory: {memory_id}")
        else:
            logger.warning(f"Memory not found for deletion: {memory_id}")
        
        return deleted
    
    def search_memories(self, query: str) -> List[Dict]:
        """Search memories by content using full-text search"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT id, content, metadata, timestamp, importance
            FROM memories 
            WHERE content LIKE ? 
            ORDER BY importance DESC, timestamp DESC
            LIMIT 20
        """, (f"%{query}%",))
        
        results = []
        for row in cursor.fetchall():
            memory_id, content, metadata_json, timestamp_str, importance = row
            results.append({
                "id": memory_id,
                "content": content,
                "metadata": json.loads(metadata_json) if metadata_json else {},
                "timestamp": timestamp_str,
                "importance": importance
            })
        
        logger.info(f"Found {len(results)} memories matching query: {query}")
        return results

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
