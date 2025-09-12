"""
Roblox-Specific Database Models

Provides models for Roblox game data, avatars, worlds, gameplay sessions, and achievements.
Integrates with the educational platform for progress tracking and gamification.
"""

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Optional, Any
from decimal import Decimal

from sqlalchemy import (
    JSON, Boolean, Column, DateTime, ForeignKey, Index, Integer, 
    String, Text, Float, Numeric, LargeBinary, Enum as SQLEnum
)
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship, declared_attr, Mapped, mapped_column
from sqlalchemy.ext.hybrid import hybrid_property

from .database import Base
from .models import TimestampMixin, SoftDeleteMixin, AuditMixin

# Constants for foreign key references
USERS_ID_FK = "users.id"
ROBLOX_WORLDS_ID_FK = "roblox_worlds.id"
ROBLOX_ASSETS_ID_FK = "roblox_assets.id"
ROBLOX_ACHIEVEMENTS_ID_FK = "roblox_achievements.id"
GAMEPLAY_SESSIONS_ID_FK = "gameplay_sessions.id"
PLAYER_AVATARS_ID_FK = "player_avatars.id"
VIRTUAL_ITEMS_ID_FK = "virtual_items.id"
ROBLOX_SCRIPTS_ID_FK = "roblox_scripts.id"


# Enums
class WorldType(Enum):
    """Types of Roblox worlds/games."""
    CLASSROOM = "classroom"
    PLAYGROUND = "playground"
    LABORATORY = "laboratory"
    LIBRARY = "library"
    MUSEUM = "museum"
    ARCADE = "arcade"
    ADVENTURE = "adventure"
    SIMULATION = "simulation"
    PUZZLE = "puzzle"
    CREATIVE = "creative"


class TerrainType(Enum):
    """Terrain types for Roblox worlds."""
    FLAT = "flat"
    HILLS = "hills"
    MOUNTAINS = "mountains"
    ISLAND = "island"
    DESERT = "desert"
    FOREST = "forest"
    UNDERWATER = "underwater"
    SPACE = "space"
    CUSTOM = "custom"


class AssetType(Enum):
    """Types of Roblox assets."""
    SCRIPT = "script"
    MODEL = "model"
    TERRAIN = "terrain"
    GUI = "gui"
    SOUND = "sound"
    IMAGE = "image"
    ANIMATION = "animation"
    TOOL = "tool"
    CLOTHING = "clothing"
    ACCESSORY = "accessory"


class GameplayAction(Enum):
    """Types of gameplay actions."""
    JOIN = "join"
    LEAVE = "leave"
    INTERACT = "interact"
    COMPLETE_TASK = "complete_task"
    ANSWER_QUESTION = "answer_question"
    COLLECT_ITEM = "collect_item"
    USE_TOOL = "use_tool"
    MOVE = "move"
    CHAT = "chat"
    ACHIEVEMENT = "achievement"


class AchievementType(Enum):
    """Types of achievements."""
    COMPLETION = "completion"
    MASTERY = "mastery"
    EXPLORATION = "exploration"
    COLLABORATION = "collaboration"
    CREATIVITY = "creativity"
    CONSISTENCY = "consistency"
    MILESTONE = "milestone"
    SPECIAL = "special"


class ItemRarity(Enum):
    """Rarity levels for virtual items."""
    COMMON = "common"
    UNCOMMON = "uncommon"
    RARE = "rare"
    EPIC = "epic"
    LEGENDARY = "legendary"
    MYTHIC = "mythic"


# Models
class RobloxWorld(Base, TimestampMixin, SoftDeleteMixin, AuditMixin):
    """Roblox world/game definition."""
    
    __tablename__ = "roblox_worlds"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    place_id = Column(String(50), unique=True, nullable=True, index=True)  # Roblox place ID
    name = Column(String(200), nullable=False, index=True)
    description = Column(Text, nullable=True)
    
    # Classification
    world_type = Column(SQLEnum(WorldType), nullable=False, index=True)
    subject = Column(String(100), nullable=True, index=True)  # Educational subject
    grade_level = Column(Integer, nullable=True, index=True)  # K-12 grade level
    difficulty_level = Column(String(20), nullable=True, index=True)  # easy, medium, hard
    
    # World Configuration
    terrain_type = Column(SQLEnum(TerrainType), default=TerrainType.FLAT)
    terrain_size = Column(String(20), default="medium")  # small, medium, large, massive
    max_players = Column(Integer, default=30)
    estimated_duration_minutes = Column(Integer, default=45)
    
    # Publishing
    is_published = Column(Boolean, default=False, nullable=False)
    is_featured = Column(Boolean, default=False, nullable=False)
    is_private = Column(Boolean, default=False, nullable=False)
    
    # Metrics
    total_visits = Column(Integer, default=0, nullable=False)
    active_players = Column(Integer, default=0, nullable=False)
    average_session_duration = Column(Float, default=0.0, nullable=False)
    completion_rate = Column(Float, default=0.0, nullable=False)
    
    # Content
    learning_objectives = Column(JSON, default=list, nullable=False)
    game_mechanics = Column(JSON, default=dict, nullable=False)
    spawn_location = Column(JSON, default=dict, nullable=False)  # x, y, z coordinates
    
    # Thumbnail and media
    thumbnail_url = Column(String(500), nullable=True)
    screenshot_urls = Column(JSON, default=list, nullable=False)
    
    # Creator information
    created_by_user_id = Column(UUID(as_uuid=True), ForeignKey(USERS_ID_FK), nullable=False)
    team_members = Column(JSON, default=list, nullable=False)  # User IDs with permissions
    
    # Relationships
    creator = relationship("User", foreign_keys=[created_by_user_id])
    assets = relationship("RobloxAsset", back_populates="world", cascade="all, delete-orphan")
    sessions = relationship("GameplaySession", back_populates="world")
    achievements = relationship("RobloxAchievement", back_populates="world")
    world_progress = relationship("WorldProgress", back_populates="world")
    
    # Indexes
    __table_args__ = (
        Index("ix_worlds_subject_grade", "subject", "grade_level"),
        Index("ix_worlds_type_difficulty", "world_type", "difficulty_level"),
        Index("ix_worlds_published_featured", "is_published", "is_featured"),
    )
    
    @hybrid_property
    def average_rating(self) -> float:
        """Calculate average rating from sessions."""
        # This would be calculated from session ratings
        return 4.5  # Placeholder
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": str(self.id),
            "place_id": self.place_id,
            "name": self.name,
            "description": self.description,
            "world_type": self.world_type.value,
            "subject": self.subject,
            "grade_level": self.grade_level,
            "difficulty_level": self.difficulty_level,
            "terrain_type": self.terrain_type.value,
            "max_players": self.max_players,
            "estimated_duration_minutes": self.estimated_duration_minutes,
            "is_published": self.is_published,
            "is_featured": self.is_featured,
            "total_visits": self.total_visits,
            "active_players": self.active_players,
            "completion_rate": self.completion_rate,
            "average_rating": self.average_rating,
            "learning_objectives": self.learning_objectives,
            "thumbnail_url": self.thumbnail_url,
            "created_at": self.created_at.isoformat(),
        }


class RobloxAsset(Base, TimestampMixin, SoftDeleteMixin):
    """Roblox game assets (scripts, models, terrain, etc.)."""
    
    __tablename__ = "roblox_assets"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    asset_id = Column(String(50), unique=True, nullable=True)  # Roblox asset ID
    name = Column(String(200), nullable=False, index=True)
    asset_type = Column(SQLEnum(AssetType), nullable=False, index=True)
    
    # World association
    world_id = Column(UUID(as_uuid=True), ForeignKey(ROBLOX_WORLDS_ID_FK), nullable=False)
    
    # Asset content
    content = Column(Text, nullable=True)  # Script code, JSON data, etc.
    binary_data = Column(LargeBinary, nullable=True)  # For images, sounds, etc.
    asset_metadata = Column(JSON, default=dict, nullable=False)
    
    # Properties
    position = Column(JSON, default=dict, nullable=False)  # x, y, z coordinates
    rotation = Column(JSON, default=dict, nullable=False)  # rotation angles
    scale = Column(JSON, default=dict, nullable=False)  # scale factors
    properties = Column(JSON, default=dict, nullable=False)  # Roblox properties
    
    # Organization
    parent_asset_id = Column(UUID(as_uuid=True), ForeignKey(ROBLOX_ASSETS_ID_FK), nullable=True)
    sort_order = Column(Integer, default=0, nullable=False)
    
    # Publishing
    is_active = Column(Boolean, default=True, nullable=False)
    is_template = Column(Boolean, default=False, nullable=False)
    
    # Version control
    version = Column(String(20), default="1.0.0", nullable=False)
    previous_version_id = Column(UUID(as_uuid=True), ForeignKey(ROBLOX_ASSETS_ID_FK), nullable=True)
    
    # Relationships
    world = relationship("RobloxWorld", back_populates="assets")
    parent_asset = relationship("RobloxAsset", remote_side=[id], foreign_keys=[parent_asset_id])
    child_assets = relationship("RobloxAsset", foreign_keys=[parent_asset_id])
    previous_version = relationship("RobloxAsset", remote_side=[id], foreign_keys=[previous_version_id])
    
    # Indexes
    __table_args__ = (
        Index("ix_assets_world_type", "world_id", "asset_type"),
        Index("ix_assets_parent_sort", "parent_asset_id", "sort_order"),
    )


class PlayerAvatar(Base, TimestampMixin):
    """Player avatar customization and appearance."""
    
    __tablename__ = "player_avatars"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey(USERS_ID_FK), nullable=False, unique=True)
    
    # Basic appearance
    body_colors = Column(JSON, default=dict, nullable=False)  # Head, torso, arms, legs
    avatar_type = Column(String(20), default="R15", nullable=False)  # R6, R15, custom
    
    # Clothing and accessories
    clothing_items = Column(JSON, default=list, nullable=False)  # Asset IDs for clothing
    accessory_items = Column(JSON, default=list, nullable=False)  # Asset IDs for accessories
    
    # Customization
    face_id = Column(String(50), nullable=True)  # Roblox face asset ID
    hair_id = Column(String(50), nullable=True)  # Hair asset ID
    emotes = Column(JSON, default=list, nullable=False)  # Available emotes
    
    # Settings
    is_public = Column(Boolean, default=True, nullable=False)
    display_name = Column(String(100), nullable=True)
    
    # Last known state
    last_position = Column(JSON, default=dict, nullable=False)  # x, y, z coordinates
    last_world_id = Column(UUID(as_uuid=True), ForeignKey(ROBLOX_WORLDS_ID_FK), nullable=True)
    
    # Relationships
    user = relationship("User")
    last_world = relationship("RobloxWorld")
    inventory_items = relationship("PlayerInventory", back_populates="avatar")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "body_colors": self.body_colors,
            "avatar_type": self.avatar_type,
            "clothing_items": self.clothing_items,
            "accessory_items": self.accessory_items,
            "face_id": self.face_id,
            "hair_id": self.hair_id,
            "emotes": self.emotes,
            "is_public": self.is_public,
            "display_name": self.display_name,
        }


class GameplaySession(Base, TimestampMixin):
    """Individual gameplay sessions with detailed tracking."""
    
    __tablename__ = "gameplay_sessions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey(USERS_ID_FK), nullable=False)
    world_id = Column(UUID(as_uuid=True), ForeignKey(ROBLOX_WORLDS_ID_FK), nullable=False)
    
    # Session timing
    started_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    ended_at = Column(DateTime(timezone=True), nullable=True)
    duration_seconds = Column(Integer, nullable=True)
    
    # Session state
    is_active = Column(Boolean, default=True, nullable=False)
    completion_status = Column(String(20), default="in_progress", nullable=False)  # in_progress, completed, abandoned
    completion_percentage = Column(Float, default=0.0, nullable=False)
    
    # Performance metrics
    score = Column(Integer, default=0, nullable=False)
    xp_earned = Column(Integer, default=0, nullable=False)
    achievements_earned = Column(JSON, default=list, nullable=False)
    
    # Learning metrics
    questions_answered = Column(Integer, default=0, nullable=False)
    questions_correct = Column(Integer, default=0, nullable=False)
    tasks_completed = Column(JSON, default=list, nullable=False)
    learning_objectives_met = Column(JSON, default=list, nullable=False)
    
    # Session data
    spawn_location = Column(JSON, default=dict, nullable=False)
    final_location = Column(JSON, default=dict, nullable=False)
    actions_taken = Column(JSON, default=list, nullable=False)  # Detailed action log
    chat_messages = Column(JSON, default=list, nullable=False)
    
    # Technical data
    device_type = Column(String(50), nullable=True)  # PC, Mobile, Tablet, Console
    platform = Column(String(50), nullable=True)  # Windows, Mac, iOS, Android
    roblox_version = Column(String(50), nullable=True)
    
    # Ratings and feedback
    fun_rating = Column(Integer, nullable=True)  # 1-5 stars
    difficulty_rating = Column(Integer, nullable=True)  # 1-5 stars
    educational_value_rating = Column(Integer, nullable=True)  # 1-5 stars
    feedback_text = Column(Text, nullable=True)
    
    # Relationships
    user = relationship("User")
    world = relationship("RobloxWorld", back_populates="sessions")
    actions = relationship("GameplayAction", back_populates="session")
    
    # Indexes
    __table_args__ = (
        Index("ix_sessions_user_world", "user_id", "world_id"),
        Index("ix_sessions_started", "started_at"),
        Index("ix_sessions_completion", "completion_status", "completion_percentage"),
    )
    
    @property
    def session_duration(self) -> Optional[int]:
        """Calculate session duration."""
        ended = getattr(self, 'ended_at', None)
        started = getattr(self, 'started_at', None)
        if ended and started:
            return int((ended - started).total_seconds())
        return getattr(self, 'duration_seconds', None)
    
    @property
    def accuracy_percentage(self) -> float:
        """Calculate question accuracy percentage."""
        answered = getattr(self, '_questions_answered', 0)
        correct = getattr(self, '_questions_correct', 0)
        if answered > 0:
            return (correct / answered) * 100
        return 0.0
    
    def end_session(self) -> None:
        """Mark session as ended and calculate final metrics."""
        self.ended_at = datetime.now(timezone.utc)
        if hasattr(self, 'ended_at') and hasattr(self, 'started_at'):
            self.duration_seconds = int((self.ended_at - self.started_at).total_seconds())
        self.is_active = False
        completion = getattr(self, 'completion_percentage', 0)
        if completion >= 100.0:
            self.completion_status = "completed"
        elif completion > 0:
            self.completion_status = "abandoned"


class GameplayActionLog(Base, TimestampMixin):
    """Detailed log of individual gameplay actions."""
    
    __tablename__ = "gameplay_actions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("gameplay_sessions.id"), nullable=False)
    
    # Action details
    action_type = Column(SQLEnum(GameplayAction), nullable=False, index=True)
    action_name = Column(String(200), nullable=False)
    action_data = Column(JSON, default=dict, nullable=False)
    
    # Context
    location = Column(JSON, default=dict, nullable=False)  # x, y, z coordinates
    target_object = Column(String(200), nullable=True)  # What was interacted with
    result = Column(String(100), nullable=True)  # success, failure, partial
    
    # Timing
    timestamp = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    duration_milliseconds = Column(Integer, nullable=True)
    
    # Learning context
    learning_objective_id = Column(String(100), nullable=True)
    subject_area = Column(String(100), nullable=True)
    skill_practiced = Column(String(200), nullable=True)
    
    # Relationships
    session = relationship("GameplaySession", back_populates="actions")
    
    # Indexes
    __table_args__ = (
        Index("ix_actions_session_type", "session_id", "action_type"),
        Index("ix_actions_timestamp", "timestamp"),
    )


class RobloxAchievement(Base, TimestampMixin, SoftDeleteMixin):
    """Achievement definitions for Roblox worlds."""
    
    __tablename__ = "roblox_achievements"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    world_id = Column(UUID(as_uuid=True), ForeignKey("roblox_worlds.id"), nullable=True)  # Null for global achievements
    
    # Basic info
    name = Column(String(200), nullable=False, index=True)
    description = Column(Text, nullable=False)
    category = Column(SQLEnum(AchievementType), nullable=False, index=True)
    
    # Requirements
    requirements = Column(JSON, default=dict, nullable=False)  # Criteria for earning
    prerequisite_achievements = Column(JSON, default=list, nullable=False)  # Required achievements
    
    # Rewards
    xp_reward = Column(Integer, default=0, nullable=False)
    badge_image_url = Column(String(500), nullable=True)
    virtual_item_rewards = Column(JSON, default=list, nullable=False)
    
    # Properties
    rarity = Column(SQLEnum(ItemRarity), default=ItemRarity.COMMON, nullable=False)
    is_secret = Column(Boolean, default=False, nullable=False)  # Hidden until earned
    is_active = Column(Boolean, default=True, nullable=False)
    sort_order = Column(Integer, default=0, nullable=False)
    
    # Statistics
    total_earned = Column(Integer, default=0, nullable=False)
    completion_rate = Column(Float, default=0.0, nullable=False)
    
    # Relationships
    world = relationship("RobloxWorld", back_populates="achievements")
    player_achievements = relationship("PlayerAchievement", back_populates="achievement")
    
    # Indexes
    __table_args__ = (
        Index("ix_achievements_world_category", "world_id", "category"),
        Index("ix_achievements_rarity_active", "rarity", "is_active"),
    )


class PlayerAchievement(Base, TimestampMixin):
    """Track player achievement progress and completion."""
    
    __tablename__ = "player_achievements"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    achievement_id = Column(UUID(as_uuid=True), ForeignKey("roblox_achievements.id"), nullable=False)
    
    # Progress tracking
    progress_percentage = Column(Float, default=0.0, nullable=False)
    current_values = Column(JSON, default=dict, nullable=False)  # Current progress values
    
    # Completion
    is_completed = Column(Boolean, default=False, nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Context
    earned_in_session_id = Column(UUID(as_uuid=True), ForeignKey("gameplay_sessions.id"), nullable=True)
    earning_world_id = Column(UUID(as_uuid=True), ForeignKey("roblox_worlds.id"), nullable=True)
    
    # Display
    is_featured = Column(Boolean, default=False, nullable=False)
    display_order = Column(Integer, default=0, nullable=False)
    
    # Relationships
    user = relationship("User")
    achievement = relationship("RobloxAchievement", back_populates="player_achievements")
    session = relationship("GameplaySession")
    world = relationship("RobloxWorld")
    
    # Unique constraint
    __table_args__ = (
        Index("ix_player_achievements_unique", "user_id", "achievement_id", unique=True),
        Index("ix_player_achievements_completed", "user_id", "is_completed"),
    )


class VirtualItem(Base, TimestampMixin, SoftDeleteMixin):
    """Virtual items that can be earned or purchased."""
    
    __tablename__ = "virtual_items"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    roblox_asset_id = Column(String(50), nullable=True)  # Roblox marketplace asset ID
    
    # Basic info
    name = Column(String(200), nullable=False, index=True)
    description = Column(Text, nullable=True)
    item_type = Column(String(50), nullable=False, index=True)  # clothing, accessory, tool, etc.
    
    # Properties
    rarity = Column(SQLEnum(ItemRarity), default=ItemRarity.COMMON, nullable=False)
    category = Column(String(100), nullable=False, index=True)
    subcategory = Column(String(100), nullable=True)
    
    # Media
    image_url = Column(String(500), nullable=True)
    thumbnail_url = Column(String(500), nullable=True)
    model_data = Column(JSON, default=dict, nullable=False)  # 3D model information
    
    # Acquisition
    cost_robux = Column(Integer, nullable=True)  # Cost in Robux
    cost_xp = Column(Integer, nullable=True)  # Cost in XP
    is_tradeable = Column(Boolean, default=False, nullable=False)
    is_limited = Column(Boolean, default=False, nullable=False)
    max_quantity = Column(Integer, nullable=True)  # Max items in circulation
    
    # Requirements
    required_level = Column(Integer, default=1, nullable=False)
    required_achievements = Column(JSON, default=list, nullable=False)
    
    # Status
    is_available = Column(Boolean, default=True, nullable=False)
    is_featured = Column(Boolean, default=False, nullable=False)
    
    # Statistics
    total_owned = Column(Integer, default=0, nullable=False)
    total_traded = Column(Integer, default=0, nullable=False)
    
    # Relationships
    inventory_items = relationship("PlayerInventory", back_populates="item")
    
    # Indexes
    __table_args__ = (
        Index("ix_virtual_items_type_rarity", "item_type", "rarity"),
        Index("ix_virtual_items_category_available", "category", "is_available"),
    )


class PlayerInventory(Base, TimestampMixin):
    """Player's virtual item inventory."""
    
    __tablename__ = "player_inventory"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    avatar_id = Column(UUID(as_uuid=True), ForeignKey("player_avatars.id"), nullable=False)
    item_id = Column(UUID(as_uuid=True), ForeignKey("virtual_items.id"), nullable=False)
    
    # Ownership
    quantity = Column(Integer, default=1, nullable=False)
    acquired_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    acquired_method = Column(String(50), nullable=False)  # purchase, reward, trade, gift
    
    # Item state
    is_equipped = Column(Boolean, default=False, nullable=False)
    is_favorite = Column(Boolean, default=False, nullable=False)
    condition = Column(String(20), default="new", nullable=False)  # new, used, worn
    
    # Transaction info
    purchase_price = Column(Numeric(10, 2), nullable=True)
    currency_type = Column(String(20), nullable=True)  # robux, xp, gift
    
    # Context
    earned_in_world_id = Column(UUID(as_uuid=True), ForeignKey("roblox_worlds.id"), nullable=True)
    earned_from_achievement_id = Column(UUID(as_uuid=True), ForeignKey("roblox_achievements.id"), nullable=True)
    
    # Relationships
    user = relationship("User")
    avatar = relationship("PlayerAvatar", back_populates="inventory_items")
    item = relationship("VirtualItem", back_populates="inventory_items")
    world = relationship("RobloxWorld")
    achievement = relationship("RobloxAchievement")
    
    # Unique constraint for non-stackable items
    __table_args__ = (
        Index("ix_inventory_user_item", "user_id", "item_id"),
        Index("ix_inventory_equipped", "user_id", "is_equipped"),
    )


class WorldProgress(Base, TimestampMixin):
    """Track player progress in specific worlds."""
    
    __tablename__ = "world_progress"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    world_id = Column(UUID(as_uuid=True), ForeignKey("roblox_worlds.id"), nullable=False)
    
    # Progress metrics
    completion_percentage = Column(Float, default=0.0, nullable=False)
    objectives_completed = Column(JSON, default=list, nullable=False)
    total_time_spent = Column(Integer, default=0, nullable=False)  # Total seconds
    visit_count = Column(Integer, default=0, nullable=False)
    
    # Performance
    best_score = Column(Integer, default=0, nullable=False)
    best_completion_time = Column(Integer, nullable=True)  # Seconds for speedrun
    total_xp_earned = Column(Integer, default=0, nullable=False)
    
    # Learning progress
    mastery_level = Column(String(20), default="beginner", nullable=False)  # beginner, intermediate, advanced, expert
    learning_objectives_mastered = Column(JSON, default=list, nullable=False)
    skills_practiced = Column(JSON, default=dict, nullable=False)  # Skill -> practice count
    
    # Status
    is_completed = Column(Boolean, default=False, nullable=False)
    first_completed_at = Column(DateTime(timezone=True), nullable=True)
    last_played_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    user = relationship("User")
    world = relationship("RobloxWorld", back_populates="world_progress")
    
    # Unique constraint
    __table_args__ = (
        Index("ix_world_progress_unique", "user_id", "world_id", unique=True),
        Index("ix_world_progress_completion", "completion_percentage", "is_completed"),
    )
    
    def update_progress(self, session: 'GameplaySession') -> None:
        """Update progress based on gameplay session."""
        self.visit_count += 1
        # Use getattr to safely access attributes
        duration = getattr(session, 'duration_seconds', 0) or 0
        self.total_time_spent += duration
        self.last_played_at = datetime.now(timezone.utc)
        
        # Safe attribute comparison
        session_score = getattr(session, 'score', 0)
        if session_score > getattr(self, 'best_score', 0):
            self.best_score = session_score
            
        session_completion = getattr(session, 'completion_percentage', 0.0)
        current_completion = getattr(self, 'completion_percentage', 0.0)
        if session_completion > current_completion:
            self.completion_percentage = session_completion
            
        # Check completion
        is_completed = getattr(self, 'is_completed', False)
        if current_completion >= 100.0 and not is_completed:
            self.is_completed = True
            self.first_completed_at = datetime.now(timezone.utc)
            
        # Update learning objectives
        session_objectives = getattr(session, 'learning_objectives_met', [])
        current_objectives = getattr(self, 'learning_objectives_mastered', [])
        for objective in session_objectives:
            if objective not in current_objectives:
                current_objectives.append(objective)
                
        session_xp = getattr(session, 'xp_earned', 0)
        self.total_xp_earned += session_xp


# Add any additional models for specific Roblox features
class RobloxScript(Base, TimestampMixin):
    """Store and manage Roblox Lua scripts."""
    
    __tablename__ = "roblox_scripts"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    world_id = Column(UUID(as_uuid=True), ForeignKey(ROBLOX_WORLDS_ID_FK), nullable=False)
    
    # Script identification
    name = Column(String(200), nullable=False)
    script_type = Column(String(50), nullable=False)  # ServerScript, LocalScript, ModuleScript
    
    # Content
    source_code = Column(Text, nullable=False)
    compiled_bytecode = Column(LargeBinary, nullable=True)
    
    # Metadata
    dependencies = Column(JSON, default=list, nullable=False)  # Required modules/scripts
    api_usage = Column(JSON, default=list, nullable=False)  # Roblox APIs used
    security_level = Column(String(20), default="safe", nullable=False)  # safe, restricted, unsafe
    
    # Version control
    version = Column(String(20), default="1.0.0", nullable=False)
    parent_script_id = Column(UUID(as_uuid=True), ForeignKey(ROBLOX_SCRIPTS_ID_FK), nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    is_template = Column(Boolean, default=False, nullable=False)
    
    # Relationships
    world = relationship("RobloxWorld")
    parent_script = relationship("RobloxScript", remote_side=[id])
    
    # Indexes
    __table_args__ = (
        Index("ix_scripts_world_type", "world_id", "script_type"),
        Index("ix_scripts_active_template", "is_active", "is_template"),
    )
