"""
Context Manager for MCP - Handles context optimization and token management
"""

import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import tiktoken
import numpy as np
from collections import defaultdict

logger = logging.getLogger(__name__)


@dataclass
class ContextSegment:
    """Represents a segment of context with metadata"""

    content: str
    tokens: int
    importance: float
    category: str
    timestamp: datetime
    source: str
    embedding: Optional[np.ndarray] = None


class MCPContextManager:
    """
    Manages context for AI agents with intelligent pruning and optimization.

    Features:
    - Token counting with tiktoken
    - Importance-based pruning
    - Semantic chunking
    - Context categorization
    - Temporal decay
    """

    def __init__(self, max_tokens: int = 128000, model: str = "gpt-4"):
        self.max_tokens = max_tokens
        self.model = model
        self.encoder = tiktoken.encoding_for_model(model)
        self.segments: List[ContextSegment] = []
        self.category_limits = {
            "system": 0.2,  # 20% for system prompts
            "user": 0.3,  # 30% for user context
            "history": 0.2,  # 20% for conversation history
            "knowledge": 0.2,  # 20% for knowledge base
            "workspace": 0.1,  # 10% for current workspace
        }

    def add_context(self, content: str, category: str, source: str, importance: float = 1.0) -> bool:
        """Add new context segment"""
        tokens = self.count_tokens(content)

        if tokens > self.max_tokens * 0.5:
            # Content too large, need to chunk it
            chunks = self._chunk_content(content, int(self.max_tokens * 0.1))
            for chunk in chunks:
                self._add_segment(chunk, category, source, importance)
        else:
            self._add_segment(content, category, source, importance)

        # Prune if necessary
        self._optimize_context()
        return True

    def _add_segment(self, content: str, category: str, source: str, importance: float):
        """Add a single context segment"""
        segment = ContextSegment(
            content=content,
            tokens=self.count_tokens(content),
            importance=importance,
            category=category,
            timestamp=datetime.now(),
            source=source,
        )
        self.segments.append(segment)

    def count_tokens(self, text: str) -> int:
        """Count tokens in text using tiktoken"""
        try:
            return len(self.encoder.encode(text))
        except (ValueError, TypeError, AttributeError) as e:
            logger.warning(f"Token counting failed, using estimate: {e}")
            # Fallback to rough estimate
            TOKEN_ESTIMATE_DIVISOR = 4
            return len(text) // TOKEN_ESTIMATE_DIVISOR

    def _chunk_content(self, content: str, max_chunk_tokens: int) -> List[str]:
        """Split content into chunks respecting token limits"""
        chunks = []
        lines = content.split("\n")
        current_chunk = []
        current_tokens = 0

        for line in lines:
            line_tokens = self.count_tokens(line)

            if current_tokens + line_tokens > max_chunk_tokens:
                if current_chunk:
                    chunks.append("\n".join(current_chunk))
                current_chunk = [line]
                current_tokens = line_tokens
            else:
                current_chunk.append(line)
                current_tokens += line_tokens

        if current_chunk:
            chunks.append("\n".join(current_chunk))

        return chunks

    def _optimize_context(self):
        """
        Optimize context to fit within token limits.
        Uses importance scoring and category limits.
        """
        total_tokens = sum(s.tokens for s in self.segments)

        if total_tokens <= self.max_tokens:
            return

        # Apply temporal decay to importance scores
        self._apply_temporal_decay()

        # Group segments by category
        category_segments = defaultdict(list)
        for segment in self.segments:
            category_segments[segment.category].append(segment)

        # Optimize each category
        optimized_segments = []

        for category, limit_ratio in self.category_limits.items():
            category_limit = int(self.max_tokens * limit_ratio)
            segments = category_segments.get(category, [])

            if not segments:
                continue

            # Sort by importance (descending)
            segments.sort(key=lambda s: s.importance, reverse=True)

            # Keep most important segments within limit
            current_tokens = 0
            for segment in segments:
                if current_tokens + segment.tokens <= category_limit:
                    optimized_segments.append(segment)
                    current_tokens += segment.tokens

        self.segments = optimized_segments

    def _apply_temporal_decay(self):
        """Apply temporal decay to importance scores"""
        now = datetime.now()

        for segment in self.segments:
            age = now - segment.timestamp

            # Decay factor based on age
            if age < timedelta(minutes=5):
                decay = 1.0
            elif age < timedelta(minutes=30):
                decay = 0.9
            elif age < timedelta(hours=1):
                decay = 0.7
            elif age < timedelta(hours=6):
                decay = 0.5
            else:
                decay = 0.3

            segment.importance *= decay

    def get_context(self, categories: Optional[List[str]] = None) -> str:
        """Get formatted context for agent consumption"""
        if categories:
            segments = [s for s in self.segments if s.category in categories]
        else:
            segments = self.segments

        # Sort by category priority and importance
        category_priority = {"system": 1, "user": 2, "workspace": 3, "history": 4, "knowledge": 5}

        segments.sort(key=lambda s: (category_priority.get(s.category, 99), -s.importance))

        # Format context with category headers
        formatted_context = []
        current_category = None

        for segment in segments:
            if segment.category != current_category:
                formatted_context.append(f"\n## {segment.category.upper()} CONTEXT\n")
                current_category = segment.category
            formatted_context.append(segment.content)

        return "\n".join(formatted_context)

    def get_stats(self) -> Dict[str, Any]:
        """Get context statistics"""
        total_tokens = sum(s.tokens for s in self.segments)

        category_stats = defaultdict(lambda: {"segments": 0, "tokens": 0})
        for segment in self.segments:
            category_stats[segment.category]["segments"] += 1
            category_stats[segment.category]["tokens"] += segment.tokens

        return {
            "total_segments": len(self.segments),
            "total_tokens": total_tokens,
            "max_tokens": self.max_tokens,
            "utilization": f"{(total_tokens / self.max_tokens) * 100:.1f}%",
            "categories": dict(category_stats),
        }
    
    def add_segment(self, content: str, category: str, source: str, importance: float):
        """Public method to add a segment"""
        return self._add_segment(content, category, source, importance)
    
    def get_segment_by_id(self, segment_id: str):
        """Get segment by ID"""
        # Since segments don't have IDs in current implementation, 
        # we'll return the first matching segment or None
        for segment in self.segments:
            if hasattr(segment, 'id') and segment.id == segment_id:
                return segment
        return None

    def save_snapshot(self, filepath: str):
        """Save context snapshot.json to file"""
        snapshot = {
            "timestamp": datetime.now().isoformat(),
            "stats": self.get_stats(),
            "segments": [
                {
                    "content": s.content,
                    "tokens": s.tokens,
                    "importance": s.importance,
                    "category": s.category,
                    "timestamp": s.timestamp.isoformat(),
                    "source": s.source,
                }
                for s in self.segments
            ],
        }

        with open(filepath, "w") as f:
            json.dump(snapshot, f, indent=2)

    def load_snapshot(self, filepath: str):
        """Load context snapshot.json from file"""
        with open(filepath, "r") as f:
            snapshot = json.load(f)

        self.segments = []
        for seg_data in snapshot["segments"]:
            segment = ContextSegment(
                content=seg_data["content"],
                tokens=seg_data["tokens"],
                importance=seg_data["importance"],
                category=seg_data["category"],
                timestamp=datetime.fromisoformat(seg_data["timestamp"]),
                source=seg_data["source"],
            )
            self.segments.append(segment)

    def search(self, query: str, limit: int = 5) -> List[ContextSegment]:
        """Search for relevant context segments"""
        # Simple keyword search (can be enhanced with embeddings)
        query_lower = query.lower()
        scored_segments = []

        for segment in self.segments:
            content_lower = segment.content.lower()

            # Calculate relevance score
            score = 0
            for word in query_lower.split():
                if word in content_lower:
                    score += content_lower.count(word)

            if score > 0:
                scored_segments.append((score * segment.importance, segment))

        # Sort by score and return top results
        scored_segments.sort(key=lambda x: x[0], reverse=True)
        return [seg for _, seg in scored_segments[:limit]]

    def clear(self, category: Optional[str] = None):
        """Clear context, optionally by category"""
        if category:
            self.segments = [s for s in self.segments if s.category != category]
        else:
            self.segments = []


# Backward compatibility alias
ContextManager = MCPContextManager
