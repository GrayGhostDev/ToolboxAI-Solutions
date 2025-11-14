"""
AI-Driven Context MCP

Advanced Model Context Protocol with AI-powered context management,
intelligent pruning, relevance scoring, and predictive prefetching.

Author: ToolboxAI Team
Created: 2025-09-21
Version: 1.0.0
"""

import hashlib
import json
import logging
import math
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Optional

logger = logging.getLogger(__name__)


class RelevanceModel(Enum):
    """AI models for relevance scoring"""

    SIMILARITY_BASED = "similarity_based"
    TRANSFORMER_BASED = "transformer_based"
    HYBRID = "hybrid"
    EDUCATIONAL_OPTIMIZED = "educational_optimized"


class PruningStrategy(Enum):
    """Context pruning strategies"""

    TIME_BASED = "time_based"
    RELEVANCE_BASED = "relevance_based"
    USAGE_BASED = "usage_based"
    AI_OPTIMIZED = "ai_optimized"
    EDUCATIONAL_PRIORITY = "educational_priority"


@dataclass
class ContextEntry:
    """Enhanced context entry with AI metadata"""

    entry_id: str
    content: dict[str, Any]
    timestamp: datetime
    source: str
    relevance_score: float = 0.0
    usage_count: int = 0
    last_accessed: Optional[datetime] = None
    educational_value: float = 0.0
    semantic_embedding: Optional[list[float]] = None
    topic_tags: list[str] = None
    learning_level: Optional[str] = None

    def __post_init__(self):
        if self.topic_tags is None:
            self.topic_tags = []
        if self.last_accessed is None:
            self.last_accessed = self.timestamp


@dataclass
class PrefetchPrediction:
    """Predictive prefetch recommendation"""

    prediction_id: str
    predicted_context: dict[str, Any]
    confidence_score: float
    prediction_basis: str
    estimated_usage_time: datetime
    prefetch_priority: int  # 1-5, higher is more important

    def should_prefetch(self, threshold: float = 0.7) -> bool:
        return self.confidence_score >= threshold


class AIDrivenContextMCP:
    """
    AI-driven context management with intelligent optimization.

    Features:
    - AI-powered relevance scoring
    - Intelligent context pruning
    - Predictive prefetching
    - Semantic similarity analysis
    - Educational content optimization
    - Adaptive learning patterns
    """

    def __init__(self, config: dict[str, Any] = None):
        self.config = config or {}

        # AI model configuration
        self.ai_config = {
            "relevance_model": RelevanceModel(
                self.config.get("relevance_model", "educational_optimized")
            ),
            "pruning_strategy": PruningStrategy(
                self.config.get("pruning_strategy", "ai_optimized")
            ),
            "embedding_dimension": self.config.get("embedding_dimension", 384),
            "similarity_threshold": self.config.get("similarity_threshold", 0.7),
            "relevance_decay_factor": self.config.get("relevance_decay_factor", 0.95),
            "educational_weight": self.config.get("educational_weight", 1.5),
        }

        # Context storage
        self.context_store: dict[str, ContextEntry] = {}
        self.relevance_cache: dict[str, float] = {}
        self.semantic_index: dict[str, list[str]] = {}  # Topic -> [entry_ids]

        # Prefetching system
        self.prefetch_predictions: list[PrefetchPrediction] = []
        self.prefetch_cache: dict[str, Any] = {}
        self.user_patterns: dict[str, dict[str, Any]] = {}

        # Performance tracking
        self.performance_stats = {
            "relevance_calculations": 0,
            "pruning_operations": 0,
            "prefetch_hits": 0,
            "prefetch_misses": 0,
            "total_context_accesses": 0,
            "average_relevance_score": 0.0,
        }

        # Initialize AI components
        self._initialize_ai_components()

        logger.info("AIDrivenContextMCP initialized")

    def _initialize_ai_components(self):
        """Initialize AI components for context management"""
        # Initialize relevance scorer
        self.relevance_scorer = {
            "model_type": self.ai_config["relevance_model"],
            "weights": {
                "temporal_relevance": 0.2,
                "semantic_similarity": 0.3,
                "educational_value": 0.3,
                "usage_frequency": 0.2,
            },
            "learning_rate": 0.01,
            "adaptation_enabled": True,
        }

        # Initialize intelligent pruner
        self.intelligent_pruner = {
            "strategy": self.ai_config["pruning_strategy"],
            "preservation_rules": {
                "high_educational_value": 0.8,
                "recent_access": timedelta(minutes=30),
                "high_usage": 5,
                "semantic_importance": 0.7,
            },
            "pruning_aggressiveness": 0.3,
            "min_context_retention": 0.1,  # Always keep 10% of context
        }

        # Initialize predictive prefetcher
        self.predictive_prefetcher = {
            "enabled": True,
            "prediction_window_minutes": 60,
            "confidence_threshold": 0.6,
            "max_prefetch_items": 20,
            "pattern_learning_enabled": True,
            "educational_pattern_weight": 1.2,
        }

    async def score_context_relevance(
        self, context: dict[str, Any], query_context: dict[str, Any] = None
    ) -> float:
        """Score context relevance using AI"""
        try:
            context_id = context.get("id", str(uuid.uuid4()))

            # Check cache first
            cache_key = self._generate_relevance_cache_key(context, query_context)
            if cache_key in self.relevance_cache:
                self.performance_stats["relevance_calculations"] += 1
                return self.relevance_cache[cache_key]

            # Calculate relevance score
            relevance_score = await self._calculate_ai_relevance_score(context, query_context)

            # Cache the result
            self.relevance_cache[cache_key] = relevance_score

            # Update performance stats
            self.performance_stats["relevance_calculations"] += 1
            self._update_average_relevance_score(relevance_score)

            logger.debug(
                "Context relevance scored: %.3f for context %s",
                relevance_score,
                context_id,
            )

            return relevance_score

        except Exception as e:
            logger.error("Relevance scoring failed: %s", str(e))
            return 0.5  # Default moderate relevance

    async def _calculate_ai_relevance_score(
        self, context: dict[str, Any], query_context: dict[str, Any] = None
    ) -> float:
        """Calculate AI-based relevance score"""
        weights = self.relevance_scorer["weights"]

        # Temporal relevance (how recent is the context)
        temporal_score = await self._calculate_temporal_relevance(context)

        # Semantic similarity (how similar to current query/context)
        semantic_score = await self._calculate_semantic_similarity(context, query_context)

        # Educational value (how valuable for learning)
        educational_score = await self._calculate_educational_value(context)

        # Usage frequency (how often accessed)
        usage_score = await self._calculate_usage_frequency(context)

        # Weighted combination
        relevance_score = (
            temporal_score * weights["temporal_relevance"]
            + semantic_score * weights["semantic_similarity"]
            + educational_score * weights["educational_value"]
            + usage_score * weights["usage_frequency"]
        )

        # Apply educational weight boost
        if educational_score > 0.7:
            relevance_score *= self.ai_config["educational_weight"]

        return min(max(relevance_score, 0.0), 1.0)

    async def _calculate_temporal_relevance(self, context: dict[str, Any]) -> float:
        """Calculate temporal relevance score"""
        timestamp_str = context.get("timestamp", datetime.now(timezone.utc).isoformat())

        try:
            context_time = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
            age_hours = (datetime.now(timezone.utc) - context_time).total_seconds() / 3600

            # Exponential decay based on age
            decay_factor = self.ai_config["relevance_decay_factor"]
            temporal_relevance = decay_factor**age_hours

            return temporal_relevance

        except (ValueError, AttributeError):
            return 0.5  # Default if timestamp parsing fails

    async def _calculate_semantic_similarity(
        self, context: dict[str, Any], query_context: dict[str, Any] = None
    ) -> float:
        """Calculate semantic similarity score"""
        if not query_context:
            return 0.5  # Default if no query context

        # Extract text content for similarity analysis
        context_text = self._extract_text_content(context)
        query_text = self._extract_text_content(query_context)

        if not context_text or not query_text:
            return 0.3

        # Simple similarity calculation (in production, would use embeddings)
        similarity = await self._calculate_text_similarity(context_text, query_text)

        return similarity

    async def _calculate_educational_value(self, context: dict[str, Any]) -> float:
        """Calculate educational value score"""
        educational_indicators = {
            "learning_objectives": 0.3,
            "assessment_data": 0.2,
            "curriculum_alignment": 0.2,
            "interactive_elements": 0.15,
            "difficulty_level": 0.15,
        }

        educational_score = 0.0

        # Check for educational indicators
        content = context.get("content", {})

        if "learning_objectives" in content or "objectives" in content:
            educational_score += educational_indicators["learning_objectives"]

        if "quiz" in str(content).lower() or "assessment" in str(content).lower():
            educational_score += educational_indicators["assessment_data"]

        if "grade_level" in content or "curriculum" in str(content).lower():
            educational_score += educational_indicators["curriculum_alignment"]

        if "interactive" in str(content).lower() or "activity" in str(content).lower():
            educational_score += educational_indicators["interactive_elements"]

        if "difficulty" in content or "level" in str(content).lower():
            educational_score += educational_indicators["difficulty_level"]

        # Boost for educational content types
        content_type = context.get("type", "").lower()
        if content_type in ["lesson", "quiz", "assessment", "activity", "curriculum"]:
            educational_score += 0.2

        return min(educational_score, 1.0)

    async def _calculate_usage_frequency(self, context: dict[str, Any]) -> float:
        """Calculate usage frequency score"""
        context_id = context.get("id", "")

        # Find matching context entry
        matching_entry = None
        for entry in self.context_store.values():
            if entry.entry_id == context_id or self._contexts_match(entry.content, context):
                matching_entry = entry
                break

        if not matching_entry:
            return 0.1  # New context, low usage score

        # Calculate usage score based on access patterns
        usage_count = matching_entry.usage_count

        # Normalize usage count (log scale)
        if usage_count > 0:
            usage_score = min(
                1.0, math.log(usage_count + 1) / math.log(100)
            )  # Log scale up to 100 uses
        else:
            usage_score = 0.0

        # Recent access bonus
        if matching_entry.last_accessed:
            hours_since_access = (
                datetime.now(timezone.utc) - matching_entry.last_accessed
            ).total_seconds() / 3600
            if hours_since_access < 1:  # Accessed within last hour
                usage_score += 0.2

        return min(usage_score, 1.0)

    async def intelligent_prune(
        self, max_tokens: int, preserve_educational: bool = True
    ) -> dict[str, Any]:
        """Intelligently prune context based on AI relevance scoring"""
        try:
            if not self.context_store:
                return {
                    "pruned_entries": 0,
                    "tokens_freed": 0,
                    "message": "No context to prune",
                }

            # Calculate current token usage
            current_tokens = await self._calculate_total_tokens()

            if current_tokens <= max_tokens:
                return {
                    "pruned_entries": 0,
                    "tokens_freed": 0,
                    "message": "Within token limit",
                }

            tokens_to_free = current_tokens - max_tokens

            # Score all entries for pruning
            pruning_candidates = []

            for entry_id, entry in self.context_store.items():
                # Calculate pruning score (lower score = more likely to prune)
                pruning_score = await self._calculate_pruning_score(entry, preserve_educational)

                entry_tokens = await self._estimate_entry_tokens(entry)

                pruning_candidates.append(
                    {
                        "entry_id": entry_id,
                        "entry": entry,
                        "pruning_score": pruning_score,
                        "tokens": entry_tokens,
                    }
                )

            # Sort by pruning score (lowest first)
            pruning_candidates.sort(key=lambda x: x["pruning_score"])

            # Prune entries until we free enough tokens
            pruned_entries = []
            tokens_freed = 0

            for candidate in pruning_candidates:
                if tokens_freed >= tokens_to_free:
                    break

                # Check preservation rules
                if preserve_educational and candidate["entry"].educational_value > 0.8:
                    continue  # Skip high educational value entries

                # Prune entry
                del self.context_store[candidate["entry_id"]]
                pruned_entries.append(candidate["entry_id"])
                tokens_freed += candidate["tokens"]

            # Update performance stats
            self.performance_stats["pruning_operations"] += 1

            # Log pruning results
            logger.info(
                "Intelligent pruning completed: %d entries removed, %d tokens freed",
                len(pruned_entries),
                tokens_freed,
            )

            return {
                "pruned_entries": len(pruned_entries),
                "tokens_freed": tokens_freed,
                "tokens_remaining": current_tokens - tokens_freed,
                "pruning_strategy": self.ai_config["pruning_strategy"].value,
                "educational_preservation": preserve_educational,
                "pruned_entry_ids": pruned_entries,
            }

        except Exception as e:
            logger.error("Intelligent pruning failed: %s", str(e))
            return {"error": str(e), "pruned_entries": 0, "tokens_freed": 0}

    async def _calculate_pruning_score(
        self, entry: ContextEntry, preserve_educational: bool
    ) -> float:
        """Calculate pruning score for context entry"""
        # Base score from relevance (higher relevance = higher score = less likely to prune)
        base_score = entry.relevance_score

        # Temporal factor (newer content gets higher score)
        age_hours = (datetime.now(timezone.utc) - entry.timestamp).total_seconds() / 3600
        temporal_factor = math.exp(-age_hours / 24)  # Decay over 24 hours

        # Usage factor (more used content gets higher score)
        usage_factor = min(1.0, entry.usage_count / 10)  # Normalize to 10 uses

        # Educational value factor
        educational_factor = entry.educational_value
        if preserve_educational:
            educational_factor *= 2.0  # Double weight when preserving educational content

        # Recent access factor
        if entry.last_accessed:
            hours_since_access = (
                datetime.now(timezone.utc) - entry.last_accessed
            ).total_seconds() / 3600
            recency_factor = math.exp(-hours_since_access / 4)  # Decay over 4 hours
        else:
            recency_factor = 0.0

        # Weighted combination
        pruning_score = (
            base_score * 0.3
            + temporal_factor * 0.2
            + usage_factor * 0.2
            + educational_factor * 0.2
            + recency_factor * 0.1
        )

        return pruning_score

    async def predictive_prefetch(
        self, user_patterns: dict[str, Any], current_context: dict[str, Any] = None
    ) -> list[dict[str, Any]]:
        """Predictively prefetch relevant context based on user patterns"""
        try:
            user_id = user_patterns.get("user_id", "anonymous")

            # Update user patterns
            self.user_patterns[user_id] = user_patterns

            # Generate predictions
            predictions = await self._generate_prefetch_predictions(user_patterns, current_context)

            # Filter by confidence threshold
            confident_predictions = [
                p
                for p in predictions
                if p.confidence_score >= self.predictive_prefetcher["confidence_threshold"]
            ]

            # Sort by priority and confidence
            confident_predictions.sort(
                key=lambda p: (p.prefetch_priority, p.confidence_score), reverse=True
            )

            # Limit to max prefetch items
            max_items = self.predictive_prefetcher["max_prefetch_items"]
            top_predictions = confident_predictions[:max_items]

            # Execute prefetching
            prefetch_results = []

            for prediction in top_predictions:
                prefetch_result = await self._execute_prefetch(prediction)
                prefetch_results.append(prefetch_result)

            # Update performance stats
            successful_prefetches = sum(1 for r in prefetch_results if r.get("success", False))
            self.performance_stats["prefetch_hits"] += successful_prefetches
            self.performance_stats["prefetch_misses"] += (
                len(prefetch_results) - successful_prefetches
            )

            logger.info(
                "Predictive prefetch completed: %d predictions, %d successful",
                len(predictions),
                successful_prefetches,
            )

            return prefetch_results

        except Exception as e:
            logger.error("Predictive prefetching failed: %s", str(e))
            return []

    async def _generate_prefetch_predictions(
        self, user_patterns: dict[str, Any], current_context: dict[str, Any] = None
    ) -> list[PrefetchPrediction]:
        """Generate prefetch predictions based on user patterns"""
        predictions = []

        # Analyze user behavior patterns
        learning_style = user_patterns.get("learning_style", "visual")
        user_patterns.get("subject_preferences", [])
        difficulty_level = user_patterns.get("difficulty_level", "medium")
        recent_topics = user_patterns.get("recent_topics", [])

        # Pattern-based predictions

        # 1. Subject continuation prediction
        if recent_topics:
            latest_topic = recent_topics[-1]
            prediction = PrefetchPrediction(
                prediction_id=str(uuid.uuid4()),
                predicted_context={
                    "type": "subject_continuation",
                    "subject": latest_topic,
                    "difficulty": difficulty_level,
                    "learning_style": learning_style,
                },
                confidence_score=0.8,
                prediction_basis="subject_continuation_pattern",
                estimated_usage_time=datetime.now(timezone.utc) + timedelta(minutes=5),
                prefetch_priority=4,
            )
            predictions.append(prediction)

        # 2. Assessment prediction (users often take quizzes after content)
        if current_context and "content" in str(current_context).lower():
            prediction = PrefetchPrediction(
                prediction_id=str(uuid.uuid4()),
                predicted_context={
                    "type": "assessment",
                    "subject": current_context.get("subject", ""),
                    "assessment_type": "quiz",
                    "difficulty": difficulty_level,
                },
                confidence_score=0.75,
                prediction_basis="content_to_assessment_pattern",
                estimated_usage_time=datetime.now(timezone.utc) + timedelta(minutes=10),
                prefetch_priority=3,
            )
            predictions.append(prediction)

        # 3. Learning style-based prediction
        if learning_style == "visual":
            prediction = PrefetchPrediction(
                prediction_id=str(uuid.uuid4()),
                predicted_context={
                    "type": "visual_content",
                    "content_type": [
                        "diagrams",
                        "charts",
                        "interactive_visualizations",
                    ],
                    "learning_style": learning_style,
                },
                confidence_score=0.7,
                prediction_basis="learning_style_preference",
                estimated_usage_time=datetime.now(timezone.utc) + timedelta(minutes=15),
                prefetch_priority=2,
            )
            predictions.append(prediction)

        # 4. Difficulty progression prediction
        if difficulty_level == "easy":
            prediction = PrefetchPrediction(
                prediction_id=str(uuid.uuid4()),
                predicted_context={
                    "type": "difficulty_progression",
                    "next_difficulty": "medium",
                    "progression_type": "gradual",
                },
                confidence_score=0.65,
                prediction_basis="difficulty_progression_pattern",
                estimated_usage_time=datetime.now(timezone.utc) + timedelta(minutes=20),
                prefetch_priority=2,
            )
            predictions.append(prediction)

        # 5. Time-based prediction (students often review before tests)
        current_hour = datetime.now(timezone.utc).hour
        if 8 <= current_hour <= 16:  # School hours
            prediction = PrefetchPrediction(
                prediction_id=str(uuid.uuid4()),
                predicted_context={
                    "type": "review_content",
                    "content_type": "summary",
                    "time_context": "school_hours",
                },
                confidence_score=0.6,
                prediction_basis="temporal_usage_pattern",
                estimated_usage_time=datetime.now(timezone.utc) + timedelta(minutes=30),
                prefetch_priority=1,
            )
            predictions.append(prediction)

        return predictions

    async def _execute_prefetch(self, prediction: PrefetchPrediction) -> dict[str, Any]:
        """Execute a prefetch prediction"""
        try:
            # Generate or retrieve predicted content
            predicted_content = await self._generate_predicted_content(prediction.predicted_context)

            if predicted_content:
                # Store in prefetch cache
                cache_key = f"prefetch_{prediction.prediction_id}"
                self.prefetch_cache[cache_key] = {
                    "content": predicted_content,
                    "prediction": prediction,
                    "cached_at": datetime.now(timezone.utc),
                    "accessed": False,
                }

                return {
                    "success": True,
                    "prediction_id": prediction.prediction_id,
                    "cache_key": cache_key,
                    "content_size": len(json.dumps(predicted_content)),
                    "confidence": prediction.confidence_score,
                }
            else:
                return {
                    "success": False,
                    "prediction_id": prediction.prediction_id,
                    "error": "Failed to generate predicted content",
                }

        except Exception as e:
            logger.error(
                "Prefetch execution failed for prediction %s: %s",
                prediction.prediction_id,
                str(e),
            )
            return {
                "success": False,
                "prediction_id": prediction.prediction_id,
                "error": str(e),
            }

    async def _generate_predicted_content(
        self, predicted_context: dict[str, Any]
    ) -> Optional[dict[str, Any]]:
        """Generate content based on prediction"""
        content_type = predicted_context.get("type", "")

        if content_type == "subject_continuation":
            return {
                "type": "educational_content",
                "subject": predicted_context.get("subject", ""),
                "difficulty": predicted_context.get("difficulty", "medium"),
                "content": "Predicted educational content for subject continuation",
                "learning_objectives": [
                    "Continue learning",
                    "Build on previous knowledge",
                ],
                "estimated_duration": 30,
            }

        elif content_type == "assessment":
            return {
                "type": "quiz",
                "subject": predicted_context.get("subject", ""),
                "questions": [
                    {
                        "id": f"predicted_q_{i}",
                        "text": f"Predicted question {i+1}",
                        "type": "multiple_choice",
                        "options": ["A", "B", "C", "D"],
                    }
                    for i in range(5)
                ],
                "difficulty": predicted_context.get("difficulty", "medium"),
            }

        elif content_type == "visual_content":
            return {
                "type": "visual_learning",
                "content_types": predicted_context.get("content_type", []),
                "visual_elements": ["diagrams", "charts", "interactive_media"],
                "learning_style": predicted_context.get("learning_style", "visual"),
            }

        elif content_type == "review_content":
            return {
                "type": "review_summary",
                "content": "Review and summary content",
                "key_concepts": ["Concept 1", "Concept 2", "Concept 3"],
                "review_activities": [
                    "practice_problems",
                    "concept_review",
                    "self_assessment",
                ],
            }

        else:
            return {
                "type": "general_content",
                "content": "General predicted content",
                "prediction_context": predicted_context,
            }

    async def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """Calculate text similarity (simplified implementation)"""
        # Simple word overlap similarity
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())

        if not words1 or not words2:
            return 0.0

        intersection = words1.intersection(words2)
        union = words1.union(words2)

        jaccard_similarity = len(intersection) / len(union) if union else 0.0

        # Boost for educational terms
        educational_terms = {
            "learn",
            "study",
            "understand",
            "knowledge",
            "education",
            "quiz",
            "assessment",
            "lesson",
            "curriculum",
            "objective",
            "skill",
        }

        educational_overlap = intersection.intersection(educational_terms)
        if educational_overlap:
            jaccard_similarity += len(educational_overlap) * 0.1

        return min(jaccard_similarity, 1.0)

    def _extract_text_content(self, context: dict[str, Any]) -> str:
        """Extract text content from context for analysis"""
        text_parts = []

        # Extract from various fields
        for field in [
            "content",
            "text",
            "description",
            "objectives",
            "title",
            "subject",
        ]:
            value = context.get(field, "")
            if isinstance(value, str):
                text_parts.append(value)
            elif isinstance(value, list):
                text_parts.extend(str(item) for item in value)

        return " ".join(text_parts)

    def _contexts_match(self, context1: dict[str, Any], context2: dict[str, Any]) -> bool:
        """Check if two contexts are similar enough to be considered the same"""
        # Simple matching based on key fields
        key_fields = ["subject", "topic", "type", "learning_objectives"]

        matches = 0
        total_fields = 0

        for field in key_fields:
            if field in context1 and field in context2:
                total_fields += 1
                if context1[field] == context2[field]:
                    matches += 1

        if total_fields == 0:
            return False

        similarity = matches / total_fields
        return similarity >= 0.7  # 70% field similarity threshold

    async def _calculate_total_tokens(self) -> int:
        """Calculate total tokens in context store"""
        total_tokens = 0

        for entry in self.context_store.values():
            entry_tokens = await self._estimate_entry_tokens(entry)
            total_tokens += entry_tokens

        return total_tokens

    async def _estimate_entry_tokens(self, entry: ContextEntry) -> int:
        """Estimate token count for context entry"""
        # Simple token estimation (in production, would use tiktoken)
        content_str = json.dumps(entry.content)

        # Rough token estimation: ~4 characters per token
        estimated_tokens = len(content_str) // 4

        return max(1, estimated_tokens)

    def _generate_relevance_cache_key(
        self, context: dict[str, Any], query_context: dict[str, Any] = None
    ) -> str:
        """Generate cache key for relevance score"""
        context_hash = hashlib.md5(json.dumps(context, sort_keys=True).encode()).hexdigest()[:16]

        if query_context:
            query_hash = hashlib.md5(
                json.dumps(query_context, sort_keys=True).encode()
            ).hexdigest()[:16]
            return f"relevance_{context_hash}_{query_hash}"
        else:
            return f"relevance_{context_hash}"

    def _update_average_relevance_score(self, new_score: float):
        """Update running average relevance score"""
        current_avg = self.performance_stats["average_relevance_score"]
        total_calculations = self.performance_stats["relevance_calculations"]

        if total_calculations == 1:
            self.performance_stats["average_relevance_score"] = new_score
        else:
            self.performance_stats["average_relevance_score"] = (
                current_avg * (total_calculations - 1) + new_score
            ) / total_calculations

    async def add_context(self, context: dict[str, Any], source: str = "unknown") -> dict[str, Any]:
        """Add context with AI-enhanced metadata"""
        try:
            entry_id = context.get("id", str(uuid.uuid4()))

            # Calculate AI metadata
            relevance_score = await self.score_context_relevance(context)
            educational_value = await self._calculate_educational_value(context)
            topic_tags = await self._extract_topic_tags(context)
            learning_level = await self._detect_learning_level(context)

            # Create enhanced context entry
            entry = ContextEntry(
                entry_id=entry_id,
                content=context,
                timestamp=datetime.now(timezone.utc),
                source=source,
                relevance_score=relevance_score,
                educational_value=educational_value,
                topic_tags=topic_tags,
                learning_level=learning_level,
            )

            # Store entry
            self.context_store[entry_id] = entry

            # Update semantic index
            await self._update_semantic_index(entry)

            logger.debug(
                "Context added with AI metadata: %s (relevance=%.3f, educational=%.3f)",
                entry_id,
                relevance_score,
                educational_value,
            )

            return {
                "success": True,
                "entry_id": entry_id,
                "relevance_score": relevance_score,
                "educational_value": educational_value,
                "topic_tags": topic_tags,
                "learning_level": learning_level,
            }

        except Exception as e:
            logger.error("Failed to add context: %s", str(e))
            return {"success": False, "error": str(e)}

    async def _extract_topic_tags(self, context: dict[str, Any]) -> list[str]:
        """Extract topic tags from context using AI"""
        tags = []

        # Extract from subject
        subject = context.get("subject", "").lower()
        if subject:
            tags.append(subject)

        # Extract from content
        content_text = self._extract_text_content(context).lower()

        # Educational topic keywords
        topic_keywords = {
            "mathematics": ["math", "algebra", "geometry", "calculus", "arithmetic"],
            "science": ["biology", "chemistry", "physics", "experiment", "hypothesis"],
            "history": ["historical", "ancient", "civilization", "war", "culture"],
            "language": ["grammar", "vocabulary", "literature", "writing", "reading"],
            "geography": ["countries", "continents", "climate", "maps", "regions"],
            "art": ["drawing", "painting", "sculpture", "design", "creativity"],
        }

        for topic, keywords in topic_keywords.items():
            if any(keyword in content_text for keyword in keywords):
                tags.append(topic)

        # Learning activity tags
        activity_keywords = {
            "quiz": ["quiz", "test", "assessment", "question"],
            "interactive": ["interactive", "activity", "game", "simulation"],
            "visual": ["diagram", "chart", "image", "visual", "graphic"],
            "practical": ["experiment", "hands-on", "practice", "exercise"],
        }

        for activity, keywords in activity_keywords.items():
            if any(keyword in content_text for keyword in keywords):
                tags.append(activity)

        return list(set(tags))  # Remove duplicates

    async def _detect_learning_level(self, context: dict[str, Any]) -> Optional[str]:
        """Detect learning level from context"""
        # Check explicit grade level
        grade_level = context.get("grade_level")
        if isinstance(grade_level, int):
            if 1 <= grade_level <= 5:
                return "elementary"
            elif 6 <= grade_level <= 8:
                return "middle_school"
            elif 9 <= grade_level <= 12:
                return "high_school"

        # Check difficulty indicators
        difficulty = context.get("difficulty", "").lower()
        if difficulty in ["easy", "beginner", "basic"]:
            return "beginner"
        elif difficulty in ["medium", "intermediate"]:
            return "intermediate"
        elif difficulty in ["hard", "advanced", "expert"]:
            return "advanced"

        # Analyze content complexity
        content_text = self._extract_text_content(context)
        complexity_score = await self._analyze_content_complexity(content_text)

        if complexity_score < 0.3:
            return "beginner"
        elif complexity_score < 0.7:
            return "intermediate"
        else:
            return "advanced"

    async def _analyze_content_complexity(self, text: str) -> float:
        """Analyze content complexity score"""
        if not text:
            return 0.0

        # Simple complexity indicators
        complexity_score = 0.0

        # Word length complexity
        words = text.split()
        if words:
            avg_word_length = sum(len(word) for word in words) / len(words)
            complexity_score += min(0.3, avg_word_length / 10)  # Normalize to 0.3 max

        # Sentence length complexity
        sentences = text.split(".")
        if sentences:
            avg_sentence_length = sum(len(sentence.split()) for sentence in sentences) / len(
                sentences
            )
            complexity_score += min(0.3, avg_sentence_length / 20)  # Normalize to 0.3 max

        # Technical term complexity
        technical_terms = [
            "algorithm",
            "hypothesis",
            "analysis",
            "synthesis",
            "evaluation",
            "differentiation",
            "integration",
            "optimization",
            "methodology",
        ]

        technical_count = sum(1 for term in technical_terms if term in text.lower())
        complexity_score += min(0.4, technical_count / len(technical_terms))

        return min(complexity_score, 1.0)

    async def _update_semantic_index(self, entry: ContextEntry):
        """Update semantic index for fast topic-based retrieval"""
        for tag in entry.topic_tags:
            if tag not in self.semantic_index:
                self.semantic_index[tag] = []

            if entry.entry_id not in self.semantic_index[tag]:
                self.semantic_index[tag].append(entry.entry_id)

    async def query_by_semantic_similarity(
        self, query: str, max_results: int = 10
    ) -> list[dict[str, Any]]:
        """Query context by semantic similarity"""
        try:
            query_tags = await self._extract_topic_tags({"content": query})

            # Find relevant entries
            relevant_entries = []

            for tag in query_tags:
                if tag in self.semantic_index:
                    for entry_id in self.semantic_index[tag]:
                        if entry_id in self.context_store:
                            entry = self.context_store[entry_id]

                            # Calculate similarity score
                            similarity = await self._calculate_text_similarity(
                                query, self._extract_text_content(entry.content)
                            )

                            relevant_entries.append(
                                {
                                    "entry_id": entry_id,
                                    "entry": entry,
                                    "similarity_score": similarity,
                                    "relevance_score": entry.relevance_score,
                                    "educational_value": entry.educational_value,
                                }
                            )

            # Remove duplicates and sort by relevance
            unique_entries = {e["entry_id"]: e for e in relevant_entries}
            sorted_entries = sorted(
                unique_entries.values(),
                key=lambda x: (x["similarity_score"] + x["relevance_score"]) / 2,
                reverse=True,
            )

            # Return top results
            results = []
            for entry_data in sorted_entries[:max_results]:
                entry = entry_data["entry"]

                # Update usage statistics
                entry.usage_count += 1
                entry.last_accessed = datetime.now(timezone.utc)

                results.append(
                    {
                        "entry_id": entry.entry_id,
                        "content": entry.content,
                        "relevance_score": entry.relevance_score,
                        "similarity_score": entry_data["similarity_score"],
                        "educational_value": entry.educational_value,
                        "topic_tags": entry.topic_tags,
                        "learning_level": entry.learning_level,
                    }
                )

            self.performance_stats["total_context_accesses"] += len(results)

            return results

        except Exception as e:
            logger.error("Semantic query failed: %s", str(e))
            return []

    def get_ai_metrics(self) -> dict[str, Any]:
        """Get AI-driven context management metrics"""
        return {
            "context_entries": len(self.context_store),
            "relevance_calculations": self.performance_stats["relevance_calculations"],
            "average_relevance_score": self.performance_stats["average_relevance_score"],
            "pruning_operations": self.performance_stats["pruning_operations"],
            "prefetch_performance": {
                "hits": self.performance_stats["prefetch_hits"],
                "misses": self.performance_stats["prefetch_misses"],
                "hit_rate": (
                    self.performance_stats["prefetch_hits"]
                    / max(
                        1,
                        self.performance_stats["prefetch_hits"]
                        + self.performance_stats["prefetch_misses"],
                    )
                ),
            },
            "semantic_index_size": len(self.semantic_index),
            "total_context_accesses": self.performance_stats["total_context_accesses"],
            "cache_efficiency": {
                "relevance_cache_size": len(self.relevance_cache),
                "prefetch_cache_size": len(self.prefetch_cache),
            },
            "ai_configuration": {
                "relevance_model": self.ai_config["relevance_model"].value,
                "pruning_strategy": self.ai_config["pruning_strategy"].value,
                "educational_optimization": True,
            },
        }
