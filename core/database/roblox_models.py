"""
Database models for Roblox content integration
Provides ORM models for storing and retrieving Roblox-specific data

This module imports models from database.models to avoid duplication.
The RobloxDatabaseHelper class provides async helper methods for database operations.
"""

from sqlalchemy import Column, String, Integer, Float, Boolean, JSON, DateTime, ForeignKey, Text, Index
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.sql import func
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
import uuid

# Import all Roblox models from the main database models
try:
    from database.models import (
        Base,
        Lesson,
        User,
        RobloxContent,
        RobloxSession,
        RobloxPlayerProgress as StudentProgress,  # Alias for backward compatibility
        RobloxDeployment,
        RobloxTemplate,
        RobloxQuizResult,
        RobloxAchievement
    )

    # Additional models that only exist in this file
    # (These don't conflict with database.models)

except ImportError:
    # Fallback for tests or when main models aren't available
    Base = declarative_base()
    Lesson = None
    User = None

    # Define minimal fallback models for testing
    RobloxContent = None
    RobloxSession = None
    StudentProgress = None
    RobloxDeployment = None
    RobloxTemplate = None
    RobloxQuizResult = None
    RobloxAchievement = None

# Models unique to this file (not in database.models)
class PluginRequest(Base):
    """Track requests from Roblox Studio plugin"""
    __tablename__ = 'plugin_requests'

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    request_id = Column(String(36), unique=True, nullable=False)

    # Request details
    event_type = Column(String(50), nullable=False)
    studio_id = Column(String(100))
    place_id = Column(Integer)
    user_id = Column(String(36), ForeignKey('users.id'))

    # Request data
    request_data = Column(JSON, nullable=False)
    context = Column(JSON)
    config = Column(JSON)

    # Response tracking
    status = Column(String(20), default='pending')  # pending, processing, completed, failed
    response_data = Column(JSON)
    error_message = Column(Text)

    # Content association
    content_id = Column(String(36), ForeignKey('roblox_content.id'))

    # Agent tracking
    assigned_agents = Column(JSON)  # List of agents assigned to this request
    agent_results = Column(JSON)  # Results from each agent

    # Performance metrics
    processing_time = Column(Float)  # Time in seconds
    token_usage = Column(JSON)  # Token usage by each agent

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))

    # Relationships
    user = relationship("User", back_populates="plugin_requests")
    content = relationship("RobloxContent", back_populates="plugin_requests")

    # Indexes
    __table_args__ = (
        Index('idx_plugin_request_status', 'status'),
        Index('idx_plugin_request_user', 'user_id'),
        Index('idx_plugin_request_created', 'created_at'),
        {'extend_existing': True}  # Allow coexistence
    )

# All the above models have been removed as they're now imported from database.models

class TerrainTemplate(Base):
    """Store reusable terrain templates - unique to this file"""
    __tablename__ = 'terrain_templates'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), unique=True, nullable=False)
    category = Column(String(50))  # educational, recreational, challenge
    
    # Terrain data
    terrain_type = Column(String(50))  # classroom, laboratory, outdoor, space
    terrain_config = Column(JSON, nullable=False)
    material_palette = Column(JSON)
    lighting_config = Column(JSON)
    
    # Educational metadata
    suitable_subjects = Column(JSON)  # List of subjects this terrain suits
    grade_levels = Column(JSON)  # Suitable grade levels
    learning_objectives = Column(JSON)
    
    # Usage tracking
    usage_count = Column(Integer, default=0)
    rating = Column(Float)
    reviews = Column(JSON)
    
    # Customization
    customizable_properties = Column(JSON)
    preset_variations = Column(JSON)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Creator
    created_by = Column(String(36), ForeignKey('users.id'))
    
    # Relationships
    creator = relationship("User", back_populates="terrain_templates")

    # Indexes
    __table_args__ = (
        Index('idx_terrain_template_category', 'category'),
        Index('idx_terrain_template_type', 'terrain_type'),
        {'extend_existing': True}  # Allow coexistence
    )

class QuizTemplate(Base):
    """Store reusable quiz templates - unique to this file"""
    __tablename__ = 'quiz_templates'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), nullable=False)
    
    # Quiz configuration
    quiz_type = Column(String(50))  # multiple_choice, true_false, fill_blank, matching
    question_format = Column(JSON)
    answer_format = Column(JSON)
    ui_template = Column(Text)  # Lua UI template
    
    # Educational metadata
    subject = Column(String(50))
    topic = Column(String(100))
    difficulty_level = Column(String(20))  # easy, medium, hard
    grade_level = Column(Integer)
    
    # Question pool
    question_pool = Column(JSON)  # Pool of questions to randomly select from
    randomization_config = Column(JSON)
    
    # Scoring
    scoring_rubric = Column(JSON)
    time_limits = Column(JSON)
    hint_system = Column(JSON)
    
    # Analytics
    average_score = Column(Float)
    completion_rate = Column(Float)
    common_mistakes = Column(JSON)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Creator
    created_by = Column(String(36), ForeignKey('users.id'))
    
    # Relationships
    creator = relationship("User", back_populates="quiz_templates")

    # Indexes
    __table_args__ = (
        Index('idx_quiz_template_subject', 'subject'),
        Index('idx_quiz_template_type', 'quiz_type'),
        Index('idx_quiz_template_grade', 'grade_level'),
        {'extend_existing': True}  # Allow coexistence
    )

class AgentTask(Base):
    """Track agent tasks and their results - unique to this file"""
    __tablename__ = 'agent_tasks'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    task_id = Column(String(36), unique=True, nullable=False)
    
    # Task details
    event_type = Column(String(50), nullable=False)
    agent_type = Column(String(50))  # supervisor, content, quiz, terrain, script, review
    parent_task_id = Column(String(36), ForeignKey('agent_tasks.id'))
    
    # Configuration
    config = Column(JSON, nullable=False)
    context = Column(JSON)
    priority = Column(String(20), default='medium')
    
    # Execution
    status = Column(String(20), default='pending')  # pending, queued, processing, completed, failed
    result = Column(JSON)
    error = Column(Text)
    retry_count = Column(Integer, default=0)
    
    # Performance
    execution_time = Column(Float)
    tokens_used = Column(Integer)
    cost_estimate = Column(Float)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    
    # Relationships
    subtasks = relationship("AgentTask", backref="parent_task", remote_side=[id])

    # Indexes
    __table_args__ = (
        Index('idx_agent_task_status', 'status'),
        Index('idx_agent_task_type', 'event_type'),
        Index('idx_agent_task_created', 'created_at'),
        {'extend_existing': True}  # Allow coexistence
    )

# Helper functions for database operations
class RobloxDatabaseHelper:
    """Helper class for Roblox database operations"""
    
    @staticmethod
    async def store_generated_content(
        session,
        lesson_id: str,
        content_type: str,
        content_data: Dict[str, Any],
        generated_by: str
    ) -> RobloxContent:
        """Store generated content in database"""
        content = RobloxContent(
            lesson_id=lesson_id,
            content_type=content_type,
            generated_by=generated_by,
            generation_config=content_data.get('config'),
            created_at=datetime.now(timezone.utc)
        )
        
        # Store specific content based on type
        if content_type == 'terrain':
            content.terrain_data = content_data.get('terrain')
            content.content_subtype = content_data.get('terrain_type')
        elif content_type == 'script':
            content.lua_script = content_data.get('script')
            content.content_subtype = content_data.get('script_type')
        elif content_type == 'quiz':
            content.quiz_data = content_data.get('quiz')
            content.ui_data = content_data.get('ui')
        elif content_type == 'model':
            content.model_data = content_data.get('model')
        
        session.add(content)
        await session.commit()
        return content
    
    @staticmethod
    async def get_content_for_lesson(
        session,
        lesson_id: str,
        content_type: Optional[str] = None
    ) -> List[RobloxContent]:
        """Get all content for a lesson"""
        from sqlalchemy import select
        
        query = select(RobloxContent).where(RobloxContent.lesson_id == lesson_id)
        
        if content_type:
            query = query.where(RobloxContent.content_type == content_type)
        
        result = await session.execute(query)
        return result.scalars().all()
    
    @staticmethod
    async def update_plugin_request(
        session,
        request_id: str,
        status: str,
        result: Optional[Dict] = None,
        error: Optional[str] = None
    ):
        """Update plugin request status"""
        from sqlalchemy import select
        
        query = select(PluginRequest).where(PluginRequest.request_id == request_id)
        result_obj = await session.execute(query)
        request = result_obj.scalar_one_or_none()
        
        if request:
            request.status = status
            if result:
                request.response_data = result
            if error:
                request.error_message = error
            if status == 'completed':
                request.completed_at = datetime.now(timezone.utc)
                if request.started_at:
                    request.processing_time = (
                        request.completed_at - request.started_at
                    ).total_seconds()
            
            await session.commit()
    
    @staticmethod
    async def create_session(
        session,
        lesson_id: str,
        teacher_id: str,
        place_id: int,
        **kwargs
    ) -> RobloxSession:
        """Create a new Roblox session"""
        roblox_session = RobloxSession(
            session_id=str(uuid.uuid4()),
            lesson_id=lesson_id,
            teacher_id=teacher_id,
            place_id=place_id,
            status='active',
            started_at=datetime.now(timezone.utc),
            **kwargs
        )
        
        session.add(roblox_session)
        await session.commit()
        return roblox_session
    
    @staticmethod
    async def track_student_progress(
        session,
        student_id: str,
        lesson_id: str,
        progress_data: Dict[str, Any]
    ):
        """Track or update student progress"""
        from sqlalchemy import select
        
        # Find existing progress record
        query = select(StudentProgress).where(
            StudentProgress.student_id == student_id,
            StudentProgress.lesson_id == lesson_id
        )
        result = await session.execute(query)
        progress = result.scalar_one_or_none()
        
        if progress:
            # Update existing progress
            progress.progress_percentage = progress_data.get(
                'percentage', progress.progress_percentage
            )
            progress.time_spent += progress_data.get('time_spent', 0)
            progress.last_updated = datetime.now(timezone.utc)
            
            # Update milestones
            if 'milestones' in progress_data:
                existing_milestones = progress.milestones_completed or []
                new_milestones = progress_data['milestones']
                progress.milestones_completed = list(
                    set(existing_milestones + new_milestones)
                )
        else:
            # Create new progress record
            progress = StudentProgress(
                student_id=student_id,
                lesson_id=lesson_id,
                progress_percentage=progress_data.get('percentage', 0.0),
                time_spent=progress_data.get('time_spent', 0),
                milestones_completed=progress_data.get('milestones', []),
                created_at=datetime.now(timezone.utc)
            )
            session.add(progress)
        
        await session.commit()
        return progress

# Export models and helper
# Note: Most models are now imported from database.models
__all__ = [
    'Base',
    'RobloxContent',  # From database.models
    'PluginRequest',  # Unique to this file
    'RobloxSession',  # From database.models
    'StudentProgress',  # Alias for RobloxPlayerProgress from database.models
    'RobloxDeployment',  # From database.models
    'TerrainTemplate',  # Unique to this file
    'QuizTemplate',  # Unique to this file
    'AgentTask',  # Unique to this file
    'RobloxDatabaseHelper',  # Unique to this file
    'RobloxTemplate',  # From database.models
    'RobloxQuizResult',  # From database.models
    'RobloxAchievement'  # From database.models
]