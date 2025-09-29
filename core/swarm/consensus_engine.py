"""
Consensus Engine - Quality consensus mechanisms for swarm intelligence.

This module provides comprehensive consensus-based quality control including
result validation, voting strategies, conflict resolution, confidence scoring,
and ensemble decision making optimized for educational content generation.
"""

import asyncio
import statistics
from typing import Dict, List, Any, Optional, Callable, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum
import logging
from datetime import datetime, timedelta
import json
import numpy as np
from collections import defaultdict, Counter
import hashlib

logger = logging.getLogger(__name__)


class VotingStrategy(Enum):
    """Enumeration of voting strategies for consensus."""

    SIMPLE_MAJORITY = "simple_majority"
    WEIGHTED_MAJORITY = "weighted_majority"
    UNANIMOUS = "unanimous"
    THRESHOLD_BASED = "threshold_based"
    CONFIDENCE_WEIGHTED = "confidence_weighted"
    EDUCATIONAL_WEIGHTED = "educational_weighted"


class ConsensusType(Enum):
    """Types of consensus decisions."""

    QUALITY_VALIDATION = "quality_validation"
    CONTENT_APPROVAL = "content_approval"
    CURRICULUM_ALIGNMENT = "curriculum_alignment"
    ACCESSIBILITY_COMPLIANCE = "accessibility_compliance"
    EDUCATIONAL_EFFECTIVENESS = "educational_effectiveness"
    TECHNICAL_CORRECTNESS = "technical_correctness"


@dataclass
class Vote:
    """Represents a single vote in the consensus process."""

    voter_id: str
    vote_value: Any  # Can be bool, float, str, or complex object
    confidence: float = 1.0  # 0.0 to 1.0
    weight: float = 1.0  # Voter weight
    timestamp: datetime = field(default_factory=datetime.now)
    reasoning: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    # Educational-specific vote attributes
    expertise_areas: List[str] = field(default_factory=list)
    subject_specialization: Optional[str] = None
    grade_level_experience: List[int] = field(default_factory=list)
    curriculum_knowledge: List[str] = field(default_factory=list)


@dataclass
class ConsensusResult:
    """Result of a consensus process."""

    consensus_id: str
    consensus_type: ConsensusType
    final_result: Any
    confidence: float
    agreement_level: float
    participating_voters: int
    total_votes: int

    # Detailed results
    votes: List[Vote] = field(default_factory=list)
    vote_distribution: Dict[Any, int] = field(default_factory=dict)
    weighted_scores: Dict[str, float] = field(default_factory=dict)

    # Timing information
    started_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    duration_seconds: float = 0.0

    # Educational-specific results
    curriculum_alignment_score: float = 0.0
    accessibility_score: float = 0.0
    educational_quality_score: float = 0.0
    subject_expert_agreement: float = 0.0

    # Conflict resolution
    conflicts_detected: List[str] = field(default_factory=list)
    resolution_strategy: str = ""
    minority_opinions: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary representation."""
        return {
            "consensus_id": self.consensus_id,
            "consensus_type": self.consensus_type.value,
            "final_result": self.final_result,
            "confidence": self.confidence,
            "agreement_level": self.agreement_level,
            "participating_voters": self.participating_voters,
            "total_votes": self.total_votes,
            "duration_seconds": self.duration_seconds,
            "curriculum_alignment_score": self.curriculum_alignment_score,
            "accessibility_score": self.accessibility_score,
            "educational_quality_score": self.educational_quality_score,
            "subject_expert_agreement": self.subject_expert_agreement,
            "conflicts_detected": self.conflicts_detected,
            "resolution_strategy": self.resolution_strategy,
            "completed_at": (
                self.completed_at.isoformat() if self.completed_at else None
            ),
        }


@dataclass
class ConsensusConfig:
    """Configuration for consensus processes."""

    voting_strategy: VotingStrategy = VotingStrategy.WEIGHTED_MAJORITY
    minimum_votes: int = 3
    maximum_votes: int = 10
    confidence_threshold: float = 0.7
    agreement_threshold: float = 0.6
    timeout_seconds: int = 300

    # Educational-specific settings
    require_subject_expert: bool = True
    require_grade_level_expert: bool = True
    curriculum_alignment_weight: float = 0.3
    accessibility_weight: float = 0.2
    educational_quality_weight: float = 0.5

    # Conflict resolution
    enable_conflict_detection: bool = True
    conflict_threshold: float = 0.4
    minority_protection: bool = True

    # Quality assurance
    enable_quality_checks: bool = True
    require_unanimous_for_critical: bool = True
    allow_abstention: bool = True


class ConsensusEngine:
    """
    Comprehensive consensus engine for quality control and decision making
    in educational content generation with advanced voting strategies,
    conflict resolution, and educational domain expertise integration.
    """

    def __init__(
        self, config: Optional[ConsensusConfig] = None, threshold: float = 0.7
    ):
        self.config = config or ConsensusConfig()
        self.config.confidence_threshold = threshold  # Override with parameter

        # Active consensus processes
        self.active_consensus: Dict[str, Dict[str, Any]] = {}
        self.completed_consensus: Dict[str, ConsensusResult] = {}

        # Voter management
        self.registered_voters: Dict[str, Dict[str, Any]] = {}
        self.voter_expertise: Dict[str, List[str]] = {}
        self.voter_performance: Dict[str, Dict[str, float]] = {}

        # Educational domain knowledge
        self.subject_experts: Dict[str, List[str]] = {}  # subject -> voter_ids
        self.grade_level_experts: Dict[int, List[str]] = {}  # grade -> voter_ids
        self.curriculum_experts: Dict[str, List[str]] = {}  # standard -> voter_ids

        # Quality metrics and learning
        self.consensus_history: List[ConsensusResult] = []
        self.quality_trends: Dict[str, List[float]] = defaultdict(list)
        self.expert_reliability: Dict[str, float] = defaultdict(lambda: 1.0)

        # Background tasks
        self._monitoring_task: Optional[asyncio.Task] = None
        self._learning_task: Optional[asyncio.Task] = None

        logger.info(
            f"ConsensusEngine initialized with strategy: {self.config.voting_strategy}"
        )

    async def initialize(self):
        """Initialize the consensus engine and start background processes."""
        try:
            # Start background monitoring
            self._monitoring_task = asyncio.create_task(self._monitoring_loop())
            self._learning_task = asyncio.create_task(self._learning_loop())

            logger.info("ConsensusEngine initialized successfully")

        except (ValueError, TypeError, RuntimeError, AttributeError) as e:
            logger.error(f"Failed to initialize ConsensusEngine: {e}")
            raise

    async def shutdown(self):
        """Gracefully shutdown the consensus engine."""
        try:
            # Cancel background tasks
            tasks = [self._monitoring_task, self._learning_task]
            for task in tasks:
                if task and not task.done():
                    task.cancel()
                    try:
                        await task
                    except asyncio.CancelledError:
                        pass

            # Complete any active consensus processes
            if self.active_consensus:
                logger.info(
                    f"Completing {len(self.active_consensus)} active consensus processes..."
                )
                await self._complete_active_consensus()

            logger.info("ConsensusEngine shutdown completed")

        except (ValueError, TypeError, RuntimeError, asyncio.CancelledError) as e:
            logger.error(f"Error during ConsensusEngine shutdown: {e}")

    async def register_voter(
        self,
        voter_id: str,
        expertise_areas: List[str],
        subject_specializations: Optional[List[str]] = None,
        grade_level_experience: Optional[List[int]] = None,
        curriculum_knowledge: Optional[List[str]] = None,
        base_weight: float = 1.0,
    ):
        """
        Register a voter with their expertise and qualifications.

        Args:
            voter_id: Unique identifier for the voter
            expertise_areas: List of expertise areas
            subject_specializations: Subject areas of specialization
            grade_level_experience: Grade levels the voter has experience with
            curriculum_knowledge: Curriculum standards the voter knows
            base_weight: Base voting weight
        """
        voter_info = {
            "voter_id": voter_id,
            "expertise_areas": expertise_areas,
            "subject_specializations": subject_specializations or [],
            "grade_level_experience": grade_level_experience or [],
            "curriculum_knowledge": curriculum_knowledge or [],
            "base_weight": base_weight,
            "registration_time": datetime.now(),
            "votes_cast": 0,
            "accuracy_score": 1.0,
        }

        self.registered_voters[voter_id] = voter_info
        self.voter_expertise[voter_id] = expertise_areas

        # Update expert mappings
        for subject in subject_specializations or []:
            if subject not in self.subject_experts:
                self.subject_experts[subject] = []
            self.subject_experts[subject].append(voter_id)

        for grade_level in grade_level_experience or []:
            if grade_level not in self.grade_level_experts:
                self.grade_level_experts[grade_level] = []
            self.grade_level_experts[grade_level].append(voter_id)

        for standard in curriculum_knowledge or []:
            if standard not in self.curriculum_experts:
                self.curriculum_experts[standard] = []
            self.curriculum_experts[standard].append(voter_id)

        logger.info(f"Registered voter {voter_id} with expertise: {expertise_areas}")

    async def start_consensus(
        self,
        consensus_type: ConsensusType,
        subject_matter: Any,
        context: Dict[str, Any],
        timeout: Optional[int] = None,
    ) -> str:
        """
        Start a new consensus process.

        Args:
            consensus_type: Type of consensus decision needed
            subject_matter: The content/decision to reach consensus on
            context: Additional context including educational metadata
            timeout: Custom timeout for this consensus

        Returns:
            Consensus ID for tracking the process
        """
        consensus_id = self._generate_consensus_id(consensus_type, subject_matter)

        # Select appropriate voters
        eligible_voters = await self._select_voters(consensus_type, context)

        if len(eligible_voters) < self.config.minimum_votes:
            raise ValueError(
                f"Insufficient eligible voters: {len(eligible_voters)} < {self.config.minimum_votes}"
            )

        # Initialize consensus process
        consensus_data = {
            "consensus_id": consensus_id,
            "consensus_type": consensus_type,
            "subject_matter": subject_matter,
            "context": context,
            "eligible_voters": eligible_voters,
            "votes": [],
            "started_at": datetime.now(),
            "timeout": timeout or self.config.timeout_seconds,
            "status": "active",
        }

        self.active_consensus[consensus_id] = consensus_data

        # Notify eligible voters (placeholder for actual notification system)
        await self._notify_voters(eligible_voters, consensus_id, subject_matter)

        logger.info(
            f"Started consensus {consensus_id} with {len(eligible_voters)} voters"
        )
        return consensus_id

    async def submit_vote(
        self,
        consensus_id: str,
        voter_id: str,
        vote_value: Any,
        confidence: float = 1.0,
        reasoning: str = "",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Submit a vote for an active consensus.

        Args:
            consensus_id: ID of the consensus process
            voter_id: ID of the voting entity
            vote_value: The vote (can be bool, float, str, or complex object)
            confidence: Voter's confidence in their vote (0.0 to 1.0)
            reasoning: Optional reasoning for the vote
            metadata: Additional vote metadata

        Returns:
            True if vote was accepted
        """
        if consensus_id not in self.active_consensus:
            logger.warning(f"Vote submitted for unknown consensus: {consensus_id}")
            return False

        consensus_data = self.active_consensus[consensus_id]

        # Verify voter eligibility
        if voter_id not in consensus_data["eligible_voters"]:
            logger.warning(
                f"Ineligible voter {voter_id} attempted to vote on {consensus_id}"
            )
            return False

        # Check for duplicate votes
        for existing_vote in consensus_data["votes"]:
            if existing_vote.voter_id == voter_id:
                logger.warning(f"Duplicate vote from {voter_id} for {consensus_id}")
                return False

        # Get voter information
        voter_info = self.registered_voters.get(voter_id, {})

        # Create vote object
        vote = Vote(
            voter_id=voter_id,
            vote_value=vote_value,
            confidence=min(1.0, max(0.0, confidence)),  # Clamp to [0, 1]
            weight=self._calculate_voter_weight(voter_id, consensus_data),
            reasoning=reasoning,
            metadata=metadata or {},
            expertise_areas=voter_info.get("expertise_areas", []),
            subject_specialization=voter_info.get("subject_specializations", [None])[0],
            grade_level_experience=voter_info.get("grade_level_experience", []),
            curriculum_knowledge=voter_info.get("curriculum_knowledge", []),
        )

        # Add vote to consensus
        consensus_data["votes"].append(vote)

        # Update voter statistics
        if voter_id in self.registered_voters:
            self.registered_voters[voter_id]["votes_cast"] += 1

        logger.info(f"Vote recorded from {voter_id} for consensus {consensus_id}")

        # Check if consensus can be reached
        if await self._can_reach_consensus(consensus_data):
            await self._finalize_consensus(consensus_id)

        return True

    async def get_consensus_result(
        self, consensus_id: str, wait: bool = False
    ) -> Optional[ConsensusResult]:
        """
        Get the result of a consensus process.

        Args:
            consensus_id: ID of the consensus process
            wait: Whether to wait for completion if still active

        Returns:
            ConsensusResult if completed, None if still active and wait=False
        """
        # Check completed consensus first
        if consensus_id in self.completed_consensus:
            return self.completed_consensus[consensus_id]

        # Check if still active
        if consensus_id not in self.active_consensus:
            logger.warning(f"Unknown consensus ID: {consensus_id}")
            return None

        if not wait:
            return None  # Still active, not waiting

        # Wait for completion
        try:
            while consensus_id in self.active_consensus:
                await asyncio.sleep(0.1)

            return self.completed_consensus.get(consensus_id)

        except asyncio.CancelledError:
            return None

    async def evaluate_result(self, task_id: str, result: Any) -> ConsensusResult:
        """
        Evaluate a task result using consensus mechanisms.

        Args:
            task_id: ID of the task being evaluated
            result: Task result to evaluate

        Returns:
            ConsensusResult with evaluation outcome
        """
        # Extract educational context from result
        context = {}
        if isinstance(result, dict):
            context = result.get("educational_context", {})
            context.update(result.get("metadata", {}))

        # Start consensus for quality validation
        consensus_id = await self.start_consensus(
            ConsensusType.QUALITY_VALIDATION, result, {"task_id": task_id, **context}
        )

        # Auto-vote based on result quality metrics
        await self._auto_vote_quality_metrics(consensus_id, result)

        # Wait for consensus completion
        consensus_result = await self.get_consensus_result(consensus_id, wait=True)

        if not consensus_result:
            # Fallback result if consensus fails
            consensus_result = ConsensusResult(
                consensus_id=consensus_id,
                consensus_type=ConsensusType.QUALITY_VALIDATION,
                final_result=result,
                confidence=0.5,
                agreement_level=0.5,
                participating_voters=0,
                total_votes=0,
            )

        return consensus_result

    async def get_consensus_status(self) -> Dict[str, Any]:
        """Get comprehensive status of all consensus processes."""
        active_count = len(self.active_consensus)
        completed_count = len(self.completed_consensus)

        # Calculate average consensus time
        if self.consensus_history:
            avg_duration = statistics.mean(
                [r.duration_seconds for r in self.consensus_history[-100:]]
            )
        else:
            avg_duration = 0.0

        # Calculate agreement trends
        agreement_trend = []
        if self.consensus_history:
            recent_results = self.consensus_history[-20:]  # Last 20 consensus results
            agreement_trend = [r.agreement_level for r in recent_results]

        return {
            "active_processes": active_count,
            "completed_processes": completed_count,
            "registered_voters": len(self.registered_voters),
            "average_duration_seconds": avg_duration,
            "agreement_trend": agreement_trend,
            "voting_strategy": self.config.voting_strategy.value,
            "confidence_threshold": self.config.confidence_threshold,
            "subject_experts": {k: len(v) for k, v in self.subject_experts.items()},
            "grade_level_experts": {
                k: len(v) for k, v in self.grade_level_experts.items()
            },
            "quality_trends": dict(self.quality_trends),
        }

    # Private methods

    async def _monitoring_loop(self):
        """Background loop for monitoring active consensus processes."""
        while True:
            try:
                current_time = datetime.now()
                expired_consensus = []

                for consensus_id, data in self.active_consensus.items():
                    start_time = data["started_at"]
                    timeout = data["timeout"]

                    if (current_time - start_time).total_seconds() > timeout:
                        expired_consensus.append(consensus_id)

                # Handle expired consensus
                for consensus_id in expired_consensus:
                    await self._handle_timeout(consensus_id)

                await asyncio.sleep(10.0)  # Check every 10 seconds

            except asyncio.CancelledError:
                break
            except (ValueError, TypeError, RuntimeError, AttributeError) as e:
                logger.error(f"Error in consensus monitoring loop: {e}")
                await asyncio.sleep(10.0)

    async def _learning_loop(self):
        """Background loop for learning from consensus outcomes."""
        while True:
            try:
                # Update voter performance metrics
                await self._update_voter_performance()

                # Update expert reliability scores
                await self._update_expert_reliability()

                # Analyze quality trends
                await self._analyze_quality_trends()

                await asyncio.sleep(300.0)  # Run every 5 minutes

            except asyncio.CancelledError:
                break
            except (ValueError, TypeError, RuntimeError, AttributeError) as e:
                logger.error(f"Error in consensus learning loop: {e}")
                await asyncio.sleep(300.0)

    async def _select_voters(
        self, consensus_type: ConsensusType, context: Dict[str, Any]
    ) -> List[str]:
        """Select appropriate voters for a consensus based on expertise and context."""
        eligible_voters = set()

        # Always include general voters
        for voter_id in self.registered_voters:
            eligible_voters.add(voter_id)

        # Add subject matter experts if required
        if self.config.require_subject_expert and "subject" in context:
            subject = context["subject"]
            if subject in self.subject_experts:
                eligible_voters.update(self.subject_experts[subject])

        # Add grade level experts if required
        if self.config.require_grade_level_expert and "grade_level" in context:
            grade_level = context["grade_level"]
            if grade_level in self.grade_level_experts:
                eligible_voters.update(self.grade_level_experts[grade_level])

        # Add curriculum experts for curriculum-related consensus
        if consensus_type == ConsensusType.CURRICULUM_ALIGNMENT:
            for standard in context.get("curriculum_standards", []):
                if standard in self.curriculum_experts:
                    eligible_voters.update(self.curriculum_experts[standard])

        # Limit to maximum voters (select most qualified)
        voters_list = list(eligible_voters)
        if len(voters_list) > self.config.maximum_votes:
            # Score voters by relevance and select top N
            voter_scores = []
            for voter_id in voters_list:
                score = self._calculate_voter_relevance(
                    voter_id, consensus_type, context
                )
                voter_scores.append((score, voter_id))

            voter_scores.sort(reverse=True)  # Highest scores first
            voters_list = [
                voter_id for _, voter_id in voter_scores[: self.config.maximum_votes]
            ]

        return voters_list

    def _calculate_voter_weight(
        self, voter_id: str, consensus_data: Dict[str, Any]
    ) -> float:
        """Calculate the voting weight for a voter in a specific consensus."""
        if voter_id not in self.registered_voters:
            return 1.0

        voter_info = self.registered_voters[voter_id]
        base_weight = voter_info.get("base_weight", 1.0)

        # Apply expertise weighting
        context = consensus_data.get("context", {})
        consensus_type = consensus_data.get("consensus_type")

        # Subject matter expertise bonus
        subject_bonus = 1.0
        if "subject" in context:
            subject = context["subject"]
            voter_subjects = voter_info.get("subject_specializations", [])
            if subject in voter_subjects:
                subject_bonus = 1.5

        # Grade level experience bonus
        grade_bonus = 1.0
        if "grade_level" in context:
            grade_level = context["grade_level"]
            voter_grades = voter_info.get("grade_level_experience", [])
            if grade_level in voter_grades:
                grade_bonus = 1.3

        # Curriculum knowledge bonus
        curriculum_bonus = 1.0
        if consensus_type == ConsensusType.CURRICULUM_ALIGNMENT:
            standards = context.get("curriculum_standards", [])
            voter_standards = voter_info.get("curriculum_knowledge", [])
            matching_standards = set(standards) & set(voter_standards)
            if matching_standards:
                curriculum_bonus = (
                    1.0 + (len(matching_standards) / len(standards)) * 0.5
                )

        # Reliability factor
        reliability = self.expert_reliability.get(voter_id, 1.0)

        final_weight = (
            base_weight * subject_bonus * grade_bonus * curriculum_bonus * reliability
        )
        return min(3.0, final_weight)  # Cap at 3x base weight

    def _calculate_voter_relevance(
        self, voter_id: str, consensus_type: ConsensusType, context: Dict[str, Any]
    ) -> float:
        """Calculate how relevant a voter is for a specific consensus."""
        if voter_id not in self.registered_voters:
            return 0.0

        voter_info = self.registered_voters[voter_id]
        score = voter_info.get("accuracy_score", 1.0)

        # Expertise relevance
        expertise_areas = voter_info.get("expertise_areas", [])
        if consensus_type.value in expertise_areas:
            score += 1.0

        # Subject relevance
        if "subject" in context:
            subject = context["subject"]
            voter_subjects = voter_info.get("subject_specializations", [])
            if subject in voter_subjects:
                score += 1.0

        # Grade level relevance
        if "grade_level" in context:
            grade_level = context["grade_level"]
            voter_grades = voter_info.get("grade_level_experience", [])
            if grade_level in voter_grades:
                score += 0.5

        return score

    async def _notify_voters(
        self, voter_ids: List[str], consensus_id: str, subject_matter: Any
    ):
        """Notify voters about a new consensus process (placeholder)."""
        # This would integrate with actual notification system
        logger.info(f"Notifying {len(voter_ids)} voters about consensus {consensus_id}")

    async def _can_reach_consensus(self, consensus_data: Dict[str, Any]) -> bool:
        """Check if consensus can be reached with current votes."""
        votes = consensus_data["votes"]

        if len(votes) < self.config.minimum_votes:
            return False

        # Check if we have enough votes from different voter types
        if self.config.require_subject_expert:
            subject_experts_voted = any(vote.subject_specialization for vote in votes)
            if not subject_experts_voted and len(votes) < self.config.maximum_votes:
                return False

        return True

    async def _finalize_consensus(self, consensus_id: str):
        """Finalize a consensus process and calculate the result."""
        if consensus_id not in self.active_consensus:
            return

        consensus_data = self.active_consensus[consensus_id]
        votes = consensus_data["votes"]

        if not votes:
            logger.warning(f"Finalizing consensus {consensus_id} with no votes")
            return

        # Calculate consensus result based on voting strategy
        result = await self._calculate_consensus_result(consensus_data)

        # Move from active to completed
        self.completed_consensus[consensus_id] = result
        del self.active_consensus[consensus_id]

        # Add to history
        self.consensus_history.append(result)

        # Update quality trends
        self._update_quality_trends(result)

        logger.info(
            f"Consensus {consensus_id} finalized: {result.final_result} (confidence: {result.confidence:.3f})"
        )

    async def _calculate_consensus_result(
        self, consensus_data: Dict[str, Any]
    ) -> ConsensusResult:
        """Calculate the final consensus result based on votes and strategy."""
        consensus_id = consensus_data["consensus_id"]
        consensus_type = consensus_data["consensus_type"]
        votes = consensus_data["votes"]
        started_at = consensus_data["started_at"]

        # Initialize result
        result = ConsensusResult(
            consensus_id=consensus_id,
            consensus_type=consensus_type,
            final_result=None,
            confidence=0.0,
            agreement_level=0.0,
            participating_voters=len(votes),
            total_votes=len(votes),
            votes=votes.copy(),
            started_at=started_at,
            completed_at=datetime.now(),
        )

        result.duration_seconds = (
            result.completed_at - result.started_at
        ).total_seconds()

        # Calculate result based on voting strategy
        if self.config.voting_strategy == VotingStrategy.SIMPLE_MAJORITY:
            result = await self._calculate_simple_majority(result)
        elif self.config.voting_strategy == VotingStrategy.WEIGHTED_MAJORITY:
            result = await self._calculate_weighted_majority(result)
        elif self.config.voting_strategy == VotingStrategy.UNANIMOUS:
            result = await self._calculate_unanimous(result)
        elif self.config.voting_strategy == VotingStrategy.THRESHOLD_BASED:
            result = await self._calculate_threshold_based(result)
        elif self.config.voting_strategy == VotingStrategy.CONFIDENCE_WEIGHTED:
            result = await self._calculate_confidence_weighted(result)
        elif self.config.voting_strategy == VotingStrategy.EDUCATIONAL_WEIGHTED:
            result = await self._calculate_educational_weighted(result)

        # Calculate educational-specific scores
        await self._calculate_educational_scores(result, consensus_data)

        # Detect conflicts and calculate agreement
        await self._analyze_consensus_quality(result)

        return result

    async def _calculate_simple_majority(
        self, result: ConsensusResult
    ) -> ConsensusResult:
        """Calculate result using simple majority voting."""
        vote_counts = Counter()

        for vote in result.votes:
            vote_counts[vote.vote_value] += 1

        if vote_counts:
            majority_vote, count = vote_counts.most_common(1)[0]
            result.final_result = majority_vote
            result.confidence = count / len(result.votes)
            result.vote_distribution = dict(vote_counts)

        return result

    async def _calculate_weighted_majority(
        self, result: ConsensusResult
    ) -> ConsensusResult:
        """Calculate result using weighted majority voting."""
        vote_weights = defaultdict(float)
        total_weight = 0.0

        for vote in result.votes:
            weight = vote.weight * vote.confidence
            vote_weights[vote.vote_value] += weight
            total_weight += weight

        if total_weight > 0:
            # Find weighted majority
            max_weight = max(vote_weights.values())
            majority_votes = [
                vote for vote, weight in vote_weights.items() if weight == max_weight
            ]

            result.final_result = majority_votes[0]  # Take first if tie
            result.confidence = max_weight / total_weight
            result.weighted_scores = dict(vote_weights)

        return result

    async def _calculate_unanimous(self, result: ConsensusResult) -> ConsensusResult:
        """Calculate result requiring unanimous agreement."""
        if not result.votes:
            return result

        first_vote = result.votes[0].vote_value
        unanimous = all(vote.vote_value == first_vote for vote in result.votes)

        if unanimous:
            result.final_result = first_vote
            result.confidence = 1.0
            result.agreement_level = 1.0
        else:
            # No consensus
            result.final_result = None
            result.confidence = 0.0
            result.agreement_level = 0.0

        return result

    async def _calculate_threshold_based(
        self, result: ConsensusResult
    ) -> ConsensusResult:
        """Calculate result using threshold-based voting."""
        vote_counts = Counter()

        for vote in result.votes:
            if vote.confidence >= self.config.confidence_threshold:
                vote_counts[vote.vote_value] += 1

        total_qualified_votes = sum(vote_counts.values())

        if total_qualified_votes >= self.config.minimum_votes:
            majority_vote, count = vote_counts.most_common(1)[0]
            if count / total_qualified_votes >= self.config.agreement_threshold:
                result.final_result = majority_vote
                result.confidence = count / total_qualified_votes
                result.vote_distribution = dict(vote_counts)

        return result

    async def _calculate_confidence_weighted(
        self, result: ConsensusResult
    ) -> ConsensusResult:
        """Calculate result using confidence-weighted voting."""
        vote_weights = defaultdict(float)
        total_confidence = 0.0

        for vote in result.votes:
            weight = vote.weight * (
                vote.confidence**2
            )  # Square confidence for emphasis
            vote_weights[vote.vote_value] += weight
            total_confidence += vote.confidence

        if total_confidence > 0:
            max_weight = max(vote_weights.values())
            majority_votes = [
                vote for vote, weight in vote_weights.items() if weight == max_weight
            ]

            result.final_result = majority_votes[0]
            result.confidence = max_weight / sum(vote_weights.values())
            result.weighted_scores = dict(vote_weights)

        return result

    async def _calculate_educational_weighted(
        self, result: ConsensusResult
    ) -> ConsensusResult:
        """Calculate result using educational domain-specific weighting."""
        educational_weights = defaultdict(float)
        total_weight = 0.0

        for vote in result.votes:
            # Base weight
            weight = vote.weight

            # Educational expertise multipliers
            if vote.expertise_areas:
                if "curriculum_alignment" in vote.expertise_areas:
                    weight *= 1.3
                if "educational_design" in vote.expertise_areas:
                    weight *= 1.2
                if "accessibility" in vote.expertise_areas:
                    weight *= 1.1

            # Confidence factor
            weight *= vote.confidence

            educational_weights[vote.vote_value] += weight
            total_weight += weight

        if total_weight > 0:
            max_weight = max(educational_weights.values())
            majority_votes = [
                vote
                for vote, weight in educational_weights.items()
                if weight == max_weight
            ]

            result.final_result = majority_votes[0]
            result.confidence = max_weight / total_weight
            result.weighted_scores = dict(educational_weights)

        return result

    async def _calculate_educational_scores(
        self, result: ConsensusResult, consensus_data: Dict[str, Any]
    ):
        """Calculate educational-specific quality scores."""
        votes = result.votes
        if not votes:
            return

        # Curriculum alignment score
        curriculum_votes = [
            vote for vote in votes if "curriculum_alignment" in vote.expertise_areas
        ]
        if curriculum_votes:
            curriculum_scores = []
            for vote in curriculum_votes:
                if (
                    isinstance(vote.vote_value, dict)
                    and "curriculum_alignment_score" in vote.vote_value
                ):
                    curriculum_scores.append(
                        vote.vote_value["curriculum_alignment_score"]
                    )
                elif isinstance(vote.vote_value, (int, float)):
                    curriculum_scores.append(float(vote.vote_value))

            if curriculum_scores:
                result.curriculum_alignment_score = statistics.mean(curriculum_scores)

        # Accessibility score
        accessibility_votes = [
            vote for vote in votes if "accessibility" in vote.expertise_areas
        ]
        if accessibility_votes:
            accessibility_scores = []
            for vote in accessibility_votes:
                if (
                    isinstance(vote.vote_value, dict)
                    and "accessibility_score" in vote.vote_value
                ):
                    accessibility_scores.append(vote.vote_value["accessibility_score"])
                elif isinstance(vote.vote_value, (int, float)):
                    accessibility_scores.append(float(vote.vote_value))

            if accessibility_scores:
                result.accessibility_score = statistics.mean(accessibility_scores)

        # Educational quality score
        quality_scores = []
        for vote in votes:
            if isinstance(vote.vote_value, dict) and "quality_score" in vote.vote_value:
                quality_scores.append(vote.vote_value["quality_score"])
            elif isinstance(vote.vote_value, (int, float)):
                quality_scores.append(float(vote.vote_value))

        if quality_scores:
            result.educational_quality_score = statistics.mean(quality_scores)

    async def _analyze_consensus_quality(self, result: ConsensusResult):
        """Analyze consensus quality and detect conflicts."""
        votes = result.votes
        if len(votes) < 2:
            result.agreement_level = 1.0
            return

        # Calculate agreement level
        vote_values = [vote.vote_value for vote in votes]

        if isinstance(vote_values[0], bool):
            # Boolean votes
            true_votes = sum(1 for v in vote_values if v)
            false_votes = len(vote_values) - true_votes
            result.agreement_level = max(true_votes, false_votes) / len(vote_values)

        elif isinstance(vote_values[0], (int, float)):
            # Numeric votes - use standard deviation as disagreement measure
            if len(vote_values) > 1:
                std_dev = statistics.stdev(vote_values)
                mean_val = statistics.mean(vote_values)
                if mean_val != 0:
                    coefficient_of_variation = std_dev / abs(mean_val)
                    result.agreement_level = max(0.0, 1.0 - coefficient_of_variation)
                else:
                    result.agreement_level = 1.0 if std_dev == 0 else 0.0

        else:
            # Categorical votes
            most_common_count = Counter(vote_values).most_common(1)[0][1]
            result.agreement_level = most_common_count / len(vote_values)

        # Detect conflicts
        if result.agreement_level < self.config.conflict_threshold:
            result.conflicts_detected.append("Low agreement among voters")

            # Identify minority opinions
            vote_counter = Counter(vote_values)
            minority_threshold = len(vote_values) * 0.3  # 30% or less is minority

            for vote_value, count in vote_counter.items():
                if count <= minority_threshold:
                    minority_votes = [
                        {
                            "voter_id": vote.voter_id,
                            "vote_value": vote.vote_value,
                            "reasoning": vote.reasoning,
                            "confidence": vote.confidence,
                        }
                        for vote in votes
                        if vote.vote_value == vote_value
                    ]
                    result.minority_opinions.extend(minority_votes)

        # Subject expert agreement
        subject_expert_votes = [vote for vote in votes if vote.subject_specialization]
        if len(subject_expert_votes) > 1:
            expert_values = [vote.vote_value for vote in subject_expert_votes]
            expert_agreement = Counter(expert_values).most_common(1)[0][1] / len(
                expert_values
            )
            result.subject_expert_agreement = expert_agreement

    async def _handle_timeout(self, consensus_id: str):
        """Handle consensus timeout."""
        if consensus_id not in self.active_consensus:
            return

        consensus_data = self.active_consensus[consensus_id]
        votes = consensus_data.get("votes", [])

        logger.warning(f"Consensus {consensus_id} timed out with {len(votes)} votes")

        if len(votes) >= self.config.minimum_votes:
            # Try to finalize with available votes
            await self._finalize_consensus(consensus_id)
        else:
            # Create failed consensus result
            result = ConsensusResult(
                consensus_id=consensus_id,
                consensus_type=consensus_data["consensus_type"],
                final_result=None,
                confidence=0.0,
                agreement_level=0.0,
                participating_voters=len(votes),
                total_votes=len(votes),
                votes=votes,
                started_at=consensus_data["started_at"],
                completed_at=datetime.now(),
            )
            result.duration_seconds = (
                result.completed_at - result.started_at
            ).total_seconds()
            result.conflicts_detected.append(
                "Consensus timed out with insufficient votes"
            )

            self.completed_consensus[consensus_id] = result
            del self.active_consensus[consensus_id]

    async def _auto_vote_quality_metrics(self, consensus_id: str, result: Any):
        """Automatically cast votes based on quality metrics in the result."""
        if not isinstance(result, dict):
            return

        # Create synthetic quality vote based on metrics
        quality_metrics = {}

        if "quality_score" in result:
            quality_metrics["quality_score"] = result["quality_score"]

        if "curriculum_alignment_score" in result:
            quality_metrics["curriculum_alignment_score"] = result[
                "curriculum_alignment_score"
            ]

        if "accessibility_score" in result:
            quality_metrics["accessibility_score"] = result["accessibility_score"]

        if quality_metrics:
            # Calculate overall quality
            avg_quality = statistics.mean(quality_metrics.values())

            await self.submit_vote(
                consensus_id=consensus_id,
                voter_id="system_quality_analyzer",
                vote_value=avg_quality > 0.7,  # Pass/fail based on 70% threshold
                confidence=min(avg_quality, 1.0),
                reasoning=f"Automated quality analysis: {quality_metrics}",
                metadata={"automated": True, "metrics": quality_metrics},
            )

    async def _complete_active_consensus(self):
        """Complete all active consensus processes."""
        for consensus_id in list(self.active_consensus.keys()):
            await self._handle_timeout(consensus_id)

    async def _update_voter_performance(self):
        """Update voter performance metrics based on historical accuracy."""
        try:
            if len(self.consensus_history) < 5:
                return  # Need minimum history for analysis
            
            # Track consensus accuracy over time
            for voter_id in self.registered_voters:
                if voter_id not in self.voter_performance:
                    self.voter_performance[voter_id] = {
                        "total_votes": 0,
                        "accurate_votes": 0,
                        "accuracy_rate": 0.0,
                        "agreement_rate": 0.0,
                        "avg_confidence": 0.0,
                        "avg_response_time": 0.0,
                        "efficiency_score": 0.0,
                        "performance_trend": [],
                        "last_updated": datetime.now()
                    }
                
                voter_stats = self.voter_performance[voter_id]
                
                # Analyze voter participation in recent consensus
                recent_results = self.consensus_history[-50:]  # Last 50 consensus results
                voter_votes = []
                voter_accuracies = []
                voter_response_times = []
                
                for result in recent_results:
                    for vote in result.votes:
                        if vote.voter_id == voter_id:
                            voter_votes.append(vote)
                            
                            # Check if vote aligned with final consensus
                            if vote.vote_value == result.final_result:
                                voter_accuracies.append(1.0)
                            else:
                                voter_accuracies.append(0.0)
                            
                            # Calculate response time (from consensus start to vote time)
                            response_time = (vote.timestamp - result.started_at).total_seconds()
                            voter_response_times.append(response_time)
                
                if not voter_votes:
                    continue
                
                # Update performance metrics
                voter_stats["total_votes"] = len(voter_votes)
                voter_stats["accurate_votes"] = sum(voter_accuracies)
                voter_stats["accuracy_rate"] = statistics.mean(voter_accuracies) if voter_accuracies else 0.0
                
                # Monitor agreement rates between validators
                agreement_scores = []
                for result in recent_results:
                    result_votes = [v for v in result.votes if v.voter_id == voter_id]
                    if result_votes and result.agreement_level > 0:
                        # Calculate how often this voter agrees with majority
                        vote = result_votes[0]
                        if vote.vote_value == result.final_result:
                            agreement_scores.append(result.agreement_level)
                        else:
                            agreement_scores.append(1.0 - result.agreement_level)
                
                voter_stats["agreement_rate"] = statistics.mean(agreement_scores) if agreement_scores else 0.0
                
                # Calculate average confidence
                confidences = [v.confidence for v in voter_votes]
                voter_stats["avg_confidence"] = statistics.mean(confidences) if confidences else 0.0
                
                # Calculate average response time
                voter_stats["avg_response_time"] = statistics.mean(voter_response_times) if voter_response_times else 0.0
                
                # Calculate efficiency metrics
                # Efficiency = (accuracy * agreement * confidence) / normalized_response_time
                normalized_response_time = min(voter_stats["avg_response_time"] / 60.0, 1.0)  # Normalize to 1 minute
                efficiency_components = [
                    voter_stats["accuracy_rate"],
                    voter_stats["agreement_rate"],
                    voter_stats["avg_confidence"]
                ]
                
                if normalized_response_time > 0:
                    voter_stats["efficiency_score"] = (
                        statistics.mean(efficiency_components) / (1.0 + normalized_response_time)
                    )
                else:
                    voter_stats["efficiency_score"] = statistics.mean(efficiency_components)
                
                # Identify performance patterns
                if len(voter_accuracies) >= 10:
                    # Calculate rolling average for trend analysis
                    window_size = min(10, len(voter_accuracies))
                    rolling_accuracies = []
                    
                    for i in range(len(voter_accuracies) - window_size + 1):
                        window = voter_accuracies[i:i + window_size]
                        rolling_accuracies.append(statistics.mean(window))
                    
                    voter_stats["performance_trend"] = rolling_accuracies[-5:]  # Keep last 5 trend points
                    
                    # Detect improvement or decline
                    if len(rolling_accuracies) >= 2:
                        trend_direction = rolling_accuracies[-1] - rolling_accuracies[0]
                        if trend_direction > 0.1:
                            logger.info(f"Voter {voter_id} showing performance improvement: +{trend_direction:.2%}")
                        elif trend_direction < -0.1:
                            logger.warning(f"Voter {voter_id} showing performance decline: {trend_direction:.2%}")
                
                voter_stats["last_updated"] = datetime.now()
                
                # Update voter's accuracy score in registered_voters
                if voter_id in self.registered_voters:
                    self.registered_voters[voter_id]["accuracy_score"] = voter_stats["accuracy_rate"]
            
            # Generate performance reports for top/bottom performers
            if self.voter_performance:
                # Sort by efficiency score
                sorted_performers = sorted(
                    self.voter_performance.items(),
                    key=lambda x: x[1]["efficiency_score"],
                    reverse=True
                )
                
                # Log top performers
                top_performers = sorted_performers[:3]
                if top_performers:
                    logger.info("Top performing voters:")
                    for voter_id, stats in top_performers:
                        logger.info(
                            f"  {voter_id}: Efficiency={stats['efficiency_score']:.3f}, "
                            f"Accuracy={stats['accuracy_rate']:.2%}, "
                            f"Agreement={stats['agreement_rate']:.2%}"
                        )
                
                # Log bottom performers (if more than 5 voters)
                if len(sorted_performers) > 5:
                    bottom_performers = sorted_performers[-3:]
                    logger.info("Voters needing improvement:")
                    for voter_id, stats in bottom_performers:
                        logger.info(
                            f"  {voter_id}: Efficiency={stats['efficiency_score']:.3f}, "
                            f"Accuracy={stats['accuracy_rate']:.2%}, "
                            f"Agreement={stats['agreement_rate']:.2%}"
                        )
        
        except (ValueError, TypeError, AttributeError, KeyError) as e:
            logger.error(f"Error updating voter performance: {e}")
        except Exception as e:
            logger.error(f"Unexpected error in voter performance update: {e}")

    async def _update_expert_reliability(self):
        """Update expert reliability scores based on consensus outcomes."""
        try:
            if len(self.consensus_history) < 10:
                return  # Need minimum history for reliable analysis
            
            # Initialize expert performance tracking
            expert_performance = {}
            
            # Analyze recent consensus for expert performance
            recent_results = self.consensus_history[-100:]  # Last 100 consensus results
            
            for voter_id in self.registered_voters:
                voter_info = self.registered_voters[voter_id]
                
                # Check if voter is an expert in any domain
                is_expert = (
                    voter_info.get("subject_specializations", []) or
                    voter_info.get("grade_level_experience", []) or
                    voter_info.get("curriculum_knowledge", [])
                )
                
                if not is_expert:
                    continue
                
                if voter_id not in expert_performance:
                    expert_performance[voter_id] = {
                        "total_consensus": 0,
                        "successful_consensus": 0,
                        "weighted_success_rate": 0.0,
                        "domain_expertise_scores": {},
                        "consensus_confidence_correlation": 0.0,
                        "historical_trend": [],
                        "trust_level": 1.0,
                        "expert_rank": 0
                    }
                
                stats = expert_performance[voter_id]
                
                # Calculate expert success rates
                expert_votes = []
                consensus_outcomes = []
                
                for result in recent_results:
                    for vote in result.votes:
                        if vote.voter_id == voter_id:
                            expert_votes.append(vote)
                            
                            # Determine if expert's vote led to successful consensus
                            success = (
                                vote.vote_value == result.final_result and
                                result.confidence >= self.config.confidence_threshold
                            )
                            consensus_outcomes.append({
                                "success": success,
                                "consensus_confidence": result.confidence,
                                "expert_confidence": vote.confidence,
                                "consensus_type": result.consensus_type,
                                "agreement_level": result.agreement_level,
                                "weight": vote.weight
                            })
                
                if not consensus_outcomes:
                    continue
                
                stats["total_consensus"] = len(consensus_outcomes)
                stats["successful_consensus"] = sum(1 for o in consensus_outcomes if o["success"])
                
                # Weight by consensus accuracy
                weighted_successes = 0.0
                total_weight = 0.0
                
                for outcome in consensus_outcomes:
                    # Weight factors: consensus confidence, agreement level, expert confidence
                    weight = (
                        outcome["consensus_confidence"] * 
                        outcome["agreement_level"] * 
                        outcome["expert_confidence"] *
                        outcome["weight"]
                    )
                    
                    if outcome["success"]:
                        weighted_successes += weight
                    total_weight += weight
                
                if total_weight > 0:
                    stats["weighted_success_rate"] = weighted_successes / total_weight
                else:
                    stats["weighted_success_rate"] = 0.0
                
                # Calculate domain-specific expertise scores
                domain_scores = {}
                
                # Subject expertise
                for subject in voter_info.get("subject_specializations", []):
                    subject_outcomes = [
                        o for o in consensus_outcomes 
                        if o["consensus_type"] in [
                            ConsensusType.CONTENT_APPROVAL,
                            ConsensusType.EDUCATIONAL_EFFECTIVENESS
                        ]
                    ]
                    if subject_outcomes:
                        domain_scores[f"subject_{subject}"] = sum(
                            1 for o in subject_outcomes if o["success"]
                        ) / len(subject_outcomes)
                
                # Grade level expertise
                for grade in voter_info.get("grade_level_experience", []):
                    grade_outcomes = [
                        o for o in consensus_outcomes
                        if o["consensus_type"] == ConsensusType.EDUCATIONAL_EFFECTIVENESS
                    ]
                    if grade_outcomes:
                        domain_scores[f"grade_{grade}"] = sum(
                            1 for o in grade_outcomes if o["success"]
                        ) / len(grade_outcomes)
                
                # Curriculum expertise
                curriculum_outcomes = [
                    o for o in consensus_outcomes
                    if o["consensus_type"] == ConsensusType.CURRICULUM_ALIGNMENT
                ]
                if curriculum_outcomes:
                    domain_scores["curriculum"] = sum(
                        1 for o in curriculum_outcomes if o["success"]
                    ) / len(curriculum_outcomes)
                
                stats["domain_expertise_scores"] = domain_scores
                
                # Calculate confidence correlation
                if len(consensus_outcomes) >= 5:
                    expert_confidences = [o["expert_confidence"] for o in consensus_outcomes]
                    consensus_confidences = [o["consensus_confidence"] for o in consensus_outcomes]
                    
                    # Calculate correlation between expert confidence and consensus confidence
                    if len(set(expert_confidences)) > 1 and len(set(consensus_confidences)) > 1:
                        # Simple correlation calculation
                        mean_expert = statistics.mean(expert_confidences)
                        mean_consensus = statistics.mean(consensus_confidences)
                        
                        numerator = sum(
                            (e - mean_expert) * (c - mean_consensus)
                            for e, c in zip(expert_confidences, consensus_confidences)
                        )
                        
                        denominator_expert = sum((e - mean_expert) ** 2 for e in expert_confidences)
                        denominator_consensus = sum((c - mean_consensus) ** 2 for c in consensus_confidences)
                        
                        if denominator_expert > 0 and denominator_consensus > 0:
                            correlation = numerator / (
                                (denominator_expert * denominator_consensus) ** 0.5
                            )
                            stats["consensus_confidence_correlation"] = max(-1, min(1, correlation))
                
                # Consider historical performance
                if voter_id in self.voter_performance:
                    perf = self.voter_performance[voter_id]
                    if "performance_trend" in perf and perf["performance_trend"]:
                        stats["historical_trend"] = perf["performance_trend"]
                
                # Adjust trust levels dynamically
                # Trust level based on: weighted success rate, correlation, and trend
                trust_components = []
                
                # Success rate component (0-1)
                trust_components.append(stats["weighted_success_rate"])
                
                # Correlation component (normalized to 0-1)
                correlation_score = (stats["consensus_confidence_correlation"] + 1) / 2
                trust_components.append(correlation_score)
                
                # Trend component (if improving, boost trust)
                if stats["historical_trend"] and len(stats["historical_trend"]) >= 2:
                    trend_improvement = stats["historical_trend"][-1] - stats["historical_trend"][0]
                    trend_score = max(0, min(1, 0.5 + trend_improvement))
                    trust_components.append(trend_score)
                
                # Calculate final trust level
                if trust_components:
                    base_trust = statistics.mean(trust_components)
                    
                    # Apply exponential smoothing with previous trust level
                    alpha = 0.3  # Smoothing factor
                    previous_trust = self.expert_reliability.get(voter_id, 1.0)
                    new_trust = alpha * base_trust + (1 - alpha) * previous_trust
                    
                    stats["trust_level"] = max(0.1, min(2.0, new_trust))  # Clamp between 0.1 and 2.0
                    self.expert_reliability[voter_id] = stats["trust_level"]
                
                expert_performance[voter_id] = stats
            
            # Update expert rankings
            if expert_performance:
                # Sort experts by weighted success rate and trust level
                sorted_experts = sorted(
                    expert_performance.items(),
                    key=lambda x: (
                        x[1]["weighted_success_rate"] * 0.6 +
                        x[1]["trust_level"] * 0.4
                    ),
                    reverse=True
                )
                
                # Assign ranks
                for rank, (expert_id, stats) in enumerate(sorted_experts, 1):
                    stats["expert_rank"] = rank
                
                # Log top experts
                top_experts = sorted_experts[:5]
                if top_experts:
                    logger.info("Top reliability experts:")
                    for expert_id, stats in top_experts:
                        logger.info(
                            f"  Rank {stats['expert_rank']}: {expert_id} - "
                            f"Success={stats['weighted_success_rate']:.2%}, "
                            f"Trust={stats['trust_level']:.3f}, "
                            f"Domains={len(stats['domain_expertise_scores'])}"
                        )
                
                # Identify experts needing calibration
                low_trust_experts = [
                    (expert_id, stats)
                    for expert_id, stats in expert_performance.items()
                    if stats["trust_level"] < 0.5
                ]
                
                if low_trust_experts:
                    logger.warning("Experts requiring calibration:")
                    for expert_id, stats in low_trust_experts:
                        logger.warning(
                            f"  {expert_id}: Trust={stats['trust_level']:.3f}, "
                            f"Success={stats['weighted_success_rate']:.2%}"
                        )
                
                # Update domain-specific expert lists based on performance
                # Remove underperforming experts from specialized lists
                for expert_id, stats in expert_performance.items():
                    if stats["trust_level"] < 0.3:  # Very low trust
                        # Remove from subject experts
                        for subject_list in self.subject_experts.values():
                            if expert_id in subject_list:
                                subject_list.remove(expert_id)
                                logger.info(f"Removed low-trust expert {expert_id} from subject experts")
                        
                        # Remove from grade level experts
                        for grade_list in self.grade_level_experts.values():
                            if expert_id in grade_list:
                                grade_list.remove(expert_id)
                                logger.info(f"Removed low-trust expert {expert_id} from grade experts")
                        
                        # Remove from curriculum experts
                        for curriculum_list in self.curriculum_experts.values():
                            if expert_id in curriculum_list:
                                curriculum_list.remove(expert_id)
                                logger.info(f"Removed low-trust expert {expert_id} from curriculum experts")
        
        except (ValueError, TypeError, AttributeError, KeyError, ZeroDivisionError) as e:
            logger.error(f"Error updating expert reliability: {e}")
        except Exception as e:
            logger.error(f"Unexpected error in expert reliability update: {e}")

    async def _analyze_quality_trends(self):
        """Analyze quality trends from consensus history."""
        if len(self.consensus_history) < 10:
            return

        recent_results = self.consensus_history[-20:]  # Last 20 results

        # Track confidence trends
        confidence_trend = [r.confidence for r in recent_results]
        self.quality_trends["confidence"].extend(confidence_trend[-5:])  # Keep last 5

        # Track agreement trends
        agreement_trend = [r.agreement_level for r in recent_results]
        self.quality_trends["agreement"].extend(agreement_trend[-5:])

        # Limit trend data
        for trend_name, trend_data in self.quality_trends.items():
            if len(trend_data) > 100:
                self.quality_trends[trend_name] = trend_data[-50:]  # Keep last 50

    def _update_quality_trends(self, result: ConsensusResult):
        """Update quality trends with new consensus result."""
        self.quality_trends["confidence"].append(result.confidence)
        self.quality_trends["agreement"].append(result.agreement_level)
        self.quality_trends["duration"].append(result.duration_seconds)

        if result.curriculum_alignment_score > 0:
            self.quality_trends["curriculum_alignment"].append(
                result.curriculum_alignment_score
            )

        if result.accessibility_score > 0:
            self.quality_trends["accessibility"].append(result.accessibility_score)

    def _generate_consensus_id(
        self, consensus_type: ConsensusType, subject_matter: Any
    ) -> str:
        """Generate a unique consensus ID."""
        content_hash = hashlib.md5(str(subject_matter).encode()).hexdigest()[:8]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"{consensus_type.value}_{timestamp}_{content_hash}"
