"""
Enhanced Content Pipeline Database Models
Provides comprehensive data models for the enhanced content generation system
"""

from sqlalchemy import Column, String, Float, Boolean, DateTime, ForeignKey, JSON, Text, Integer, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import uuid

Base = declarative_base()


class EnhancedContentGeneration(Base):
    """Model for tracking enhanced content generation requests and results"""
    __tablename__ = 'enhanced_content_generations'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)

    # Request details
    original_request = Column(JSON, nullable=False)
    content_type = Column(String(50), nullable=False)  # lesson, quiz, activity, scenario
    subject = Column(String(100))
    grade_level = Column(String(50))
    difficulty_level = Column(String(20))  # beginner, intermediate, advanced

    # Generated content
    enhanced_content = Column(JSON)
    generated_scripts = Column(JSON)  # Luau scripts for Roblox
    generated_assets = Column(JSON)   # 3D models, textures, etc.

    # Quality metrics
    quality_score = Column(Float)
    engagement_score = Column(Float)
    educational_value_score = Column(Float)
    accessibility_score = Column(Float)

    # Personalization
    personalization_applied = Column(Boolean, default=False)
    personalization_parameters = Column(JSON)

    # Metadata and status
    generation_metadata = Column(JSON)
    status = Column(String(50), default='processing')  # processing, completed, failed
    error_message = Column(Text)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)

    # Performance metrics
    generation_time_seconds = Column(Float)
    tokens_used = Column(Integer)

    # Relationships
    quality_metrics = relationship("ContentQualityMetrics", back_populates="content", cascade="all, delete-orphan")
    personalization_logs = relationship("ContentPersonalizationLog", back_populates="content")
    feedback_records = relationship("ContentFeedback", back_populates="content")

    # Indexes for performance
    __table_args__ = (
        Index('idx_ecg_user_status', 'user_id', 'status'),
        Index('idx_ecg_created_at', 'created_at'),
        Index('idx_ecg_quality_score', 'quality_score'),
    )


class ContentQualityMetrics(Base):
    """Detailed quality metrics for generated content"""
    __tablename__ = 'content_quality_metrics'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    content_id = Column(UUID(as_uuid=True), ForeignKey('enhanced_content_generations.id'), nullable=False)

    # Educational metrics
    curriculum_alignment_score = Column(Float)
    learning_objectives_coverage = Column(Float)
    cognitive_level_appropriateness = Column(Float)

    # Engagement metrics
    interactivity_score = Column(Float)
    visual_appeal_score = Column(Float)
    narrative_quality_score = Column(Float)

    # Technical metrics
    code_quality_score = Column(Float)
    performance_score = Column(Float)
    compatibility_score = Column(Float)

    # Accessibility metrics
    readability_score = Column(Float)
    wcag_compliance_score = Column(Float)
    language_simplicity_score = Column(Float)

    # Comprehensive scores
    overall_quality_score = Column(Float)
    recommendation_score = Column(Float)

    # Validation details
    validation_details = Column(JSON)
    validation_errors = Column(JSON)
    improvement_suggestions = Column(JSON)

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    content = relationship("EnhancedContentGeneration", back_populates="quality_metrics")

    # Indexes
    __table_args__ = (
        Index('idx_cqm_content_score', 'content_id', 'overall_quality_score'),
        Index('idx_cqm_created_at', 'created_at'),
    )


class LearningProfile(Base):
    """User learning profiles for content personalization"""
    __tablename__ = 'learning_profiles'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), unique=True, nullable=False)

    # Learning preferences
    learning_style = Column(JSON)  # visual, auditory, kinesthetic, reading/writing
    preferred_difficulty = Column(JSON)  # per subject preferences
    subject_preferences = Column(JSON)  # interest levels per subject

    # Engagement patterns
    engagement_patterns = Column(JSON)  # time of day, session duration, frequency
    interaction_preferences = Column(JSON)  # solo, collaborative, competitive

    # Performance history
    performance_history = Column(JSON)  # historical performance data
    strengths = Column(JSON)  # identified strong areas
    improvement_areas = Column(JSON)  # areas needing improvement

    # Accessibility needs
    accessibility_requirements = Column(JSON)  # specific accessibility needs
    language_preferences = Column(JSON)  # preferred languages and complexity

    # Roblox-specific preferences
    preferred_game_mechanics = Column(JSON)  # platformer, puzzle, adventure, etc.
    avatar_preferences = Column(JSON)  # customization preferences

    # Metadata
    profile_completeness = Column(Float)  # 0-1 scale of profile completeness
    confidence_score = Column(Float)  # confidence in profile accuracy

    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Indexes
    __table_args__ = (
        Index('idx_lp_user', 'user_id'),
        Index('idx_lp_updated', 'last_updated'),
    )


class ContentPersonalizationLog(Base):
    """Log of content personalizations applied"""
    __tablename__ = 'content_personalization_log'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    content_id = Column(UUID(as_uuid=True), ForeignKey('enhanced_content_generations.id'), nullable=False)

    # Personalization details
    personalization_type = Column(String(50))  # difficulty, style, pace, etc.
    personalization_applied = Column(JSON)  # specific changes made

    # Effectiveness tracking
    effectiveness_score = Column(Float)  # how well the personalization worked
    engagement_improvement = Column(Float)  # change in engagement
    learning_outcome_improvement = Column(Float)  # change in learning outcomes

    # User feedback
    user_feedback = Column(JSON)
    user_rating = Column(Float)  # 1-5 scale

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    content = relationship("EnhancedContentGeneration", back_populates="personalization_logs")

    # Indexes
    __table_args__ = (
        Index('idx_cpl_user_date', 'user_id', 'created_at'),
        Index('idx_cpl_content', 'content_id'),
        Index('idx_cpl_effectiveness', 'effectiveness_score'),
    )


class ContentFeedback(Base):
    """User feedback on generated content"""
    __tablename__ = 'content_feedback'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    content_id = Column(UUID(as_uuid=True), ForeignKey('enhanced_content_generations.id'), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)

    # Feedback data
    rating = Column(Float)  # 1-5 scale
    feedback_type = Column(String(50))  # quality, engagement, difficulty, etc.
    feedback_text = Column(Text)

    # Specific feedback categories
    educational_value_rating = Column(Float)
    engagement_rating = Column(Float)
    difficulty_rating = Column(Float)
    technical_quality_rating = Column(Float)

    # Improvement suggestions
    suggested_improvements = Column(JSON)
    reported_issues = Column(JSON)

    # Metadata
    session_duration = Column(Float)  # time spent with content
    completion_rate = Column(Float)  # percentage of content completed
    interaction_count = Column(Integer)  # number of interactions

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    content = relationship("EnhancedContentGeneration", back_populates="feedback_records")

    # Indexes
    __table_args__ = (
        Index('idx_cf_content_rating', 'content_id', 'rating'),
        Index('idx_cf_user', 'user_id'),
        Index('idx_cf_created_at', 'created_at'),
    )


class ContentGenerationBatch(Base):
    """Batch processing for multiple content generations"""
    __tablename__ = 'content_generation_batches'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    batch_name = Column(String(200))
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)

    # Batch configuration
    batch_config = Column(JSON)  # common parameters for all items
    total_items = Column(Integer)
    completed_items = Column(Integer, default=0)
    failed_items = Column(Integer, default=0)

    # Status tracking
    status = Column(String(50), default='pending')  # pending, processing, completed, failed

    # Performance
    estimated_completion_time = Column(DateTime)
    actual_completion_time = Column(DateTime)

    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)

    # Indexes
    __table_args__ = (
        Index('idx_cgb_user_status', 'user_id', 'status'),
        Index('idx_cgb_created_at', 'created_at'),
    )


class ContentCache(Base):
    """Cache for frequently accessed content and LLM responses"""
    __tablename__ = 'content_cache'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cache_key = Column(String(500), unique=True, nullable=False)
    cache_type = Column(String(50))  # content, llm_response, template, etc.

    # Cached data
    cached_data = Column(JSON)

    # Cache metadata
    access_count = Column(Integer, default=0)
    last_accessed = Column(DateTime)
    ttl_seconds = Column(Integer, default=3600)

    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime)

    # Indexes
    __table_args__ = (
        Index('idx_cc_key', 'cache_key'),
        Index('idx_cc_type', 'cache_type'),
        Index('idx_cc_expires', 'expires_at'),
    )