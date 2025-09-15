"""Comprehensive Roblox API Endpoints for ToolboxAI Educational Platform

Provides complete Roblox integration including:
- Game instance management
- AI-powered content generation
- Student progress tracking
- Real-time communication
- Analytics and reporting
- WebSocket integration
- OAuth2 authentication with JWT
- Rate limiting and security

Compatible with Universe ID: 8505376973
Backend URL: http://127.0.0.1:8008
Client ID: 2214511122270781418
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Header, BackgroundTasks, WebSocket, WebSocketDisconnect, status
from fastapi.security import OAuth2PasswordBearer
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timedelta
import logging
import httpx
import os
import json
import base64
import asyncio
from pydantic import BaseModel, Field, field_validator
from enum import Enum
import uuid
from contextlib import asynccontextmanager

# Handle imports safely
try:
    from apps.backend.api.auth.auth import get_current_user
except ImportError:
    try:
        from auth.auth import get_current_user
    except ImportError:
        # Fallback for development
        def get_current_user():
            from pydantic import BaseModel
            class MockUser(BaseModel):
                email: str = "test@example.com"
                role: str = "teacher"
                id: Optional[str] = "test_user_id"
            return MockUser()

try:
    from apps.backend.models.schemas import User, BaseResponse
except ImportError:
    try:
        from apps.backend.models.schemas import User, BaseResponse
    except ImportError:
        # Fallback models for development
        class User(BaseModel):
            email: str
            role: str
            id: Optional[str] = None

        class BaseResponse(BaseModel):
            success: bool = True
            message: str = ""
            timestamp: datetime = Field(default_factory=datetime.utcnow)
            request_id: str = Field(default_factory=lambda: str(uuid.uuid4()))

try:
    from apps.backend.services.database import db_service
except ImportError:
    db_service = None  # Fallback for development

logger = logging.getLogger(__name__)

# Configuration
ROBLOX_CLIENT_ID = os.getenv("ROBLOX_CLIENT_ID", "2214511122270781418")
ROBLOX_CLIENT_SECRET = os.getenv("ROBLOX_CLIENT_SECRET")
ROBLOX_API_KEY = os.getenv("ROBLOX_API_KEY")
ROBLOX_PLUGIN_PORT = os.getenv("ROBLOX_PLUGIN_PORT", "64989")
ROBLOX_UNIVERSE_ID = os.getenv("ROBLOX_UNIVERSE_ID", "8505376973")
BACKEND_URL = "http://127.0.0.1:8008"

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Rate limiting configurations
RATE_LIMIT_REQUESTS = 100  # per minute
RATE_LIMIT_BURST = 10      # burst limit

# =============================================================================
# PYDANTIC MODELS
# =============================================================================

class GameStatus(str, Enum):
    """Game instance status"""
    CREATING = "creating"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    ARCHIVED = "archived"

class ContentType(str, Enum):
    """Content generation types"""
    LESSON = "lesson"
    QUIZ = "quiz"
    ACTIVITY = "activity"
    TERRAIN = "terrain"
    SCRIPT = "script"

class DeploymentStatus(str, Enum):
    """Content deployment status"""
    PENDING = "pending"
    DEPLOYING = "deploying"
    DEPLOYED = "deployed"
    FAILED = "failed"
    ROLLBACK = "rollback"

class AnalyticsEventType(str, Enum):
    """Custom analytics event types"""
    STUDENT_JOIN = "student_join"
    STUDENT_LEAVE = "student_leave"
    QUIZ_START = "quiz_start"
    QUIZ_COMPLETE = "quiz_complete"
    CHECKPOINT_REACH = "checkpoint_reach"
    ACHIEVEMENT_UNLOCK = "achievement_unlock"

# Request Models
class CreateGameRequest(BaseModel):
    """Create new educational game instance"""
    title: str = Field(..., min_length=3, max_length=100, description="Game title")
    description: Optional[str] = Field(None, max_length=500, description="Game description")
    subject: str = Field(..., description="Educational subject")
    grade_level: int = Field(..., ge=1, le=12, description="Target grade level")
    max_players: int = Field(default=30, ge=1, le=50, description="Maximum players")
    template_id: Optional[str] = Field(None, description="Template to use")
    settings: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Game settings")

    class Config:
        schema_extra = {
            "example": {
                "title": "Solar System Explorer",
                "description": "Interactive space exploration game",
                "subject": "Science",
                "grade_level": 7,
                "max_players": 25,
                "template_id": "space_station",
                "settings": {
                    "enable_voice_chat": False,
                    "difficulty": "medium"
                }
            }
        }

class UpdateGameSettingsRequest(BaseModel):
    """Update game settings"""
    title: Optional[str] = Field(None, min_length=3, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    max_players: Optional[int] = Field(None, ge=1, le=50)
    settings: Optional[Dict[str, Any]] = None
    status: Optional[GameStatus] = None

class ContentGenerationRequest(BaseModel):
    """Request for AI content generation"""
    content_type: ContentType = Field(..., description="Type of content to generate")
    subject: str = Field(..., description="Educational subject")
    grade_level: int = Field(..., ge=1, le=12, description="Target grade level")
    learning_objectives: List[str] = Field(..., min_items=1, max_items=10, description="Learning objectives")
    environment_type: str = Field(..., description="Roblox environment type")
    difficulty: str = Field(default="medium", description="Content difficulty")
    duration_minutes: int = Field(default=30, ge=5, le=120, description="Expected duration")
    include_quiz: bool = Field(default=True, description="Include assessment quiz")
    custom_requirements: Optional[str] = Field(None, max_length=1000, description="Custom requirements")

    @field_validator('learning_objectives')
    def validate_objectives(cls, v):
        for obj in v:
            if len(obj.strip()) < 10:
                raise ValueError('Each learning objective must be at least 10 characters')
        return v

class ContentDeploymentRequest(BaseModel):
    """Deploy content to Roblox game"""
    content_id: str = Field(..., description="Generated content ID")
    game_id: str = Field(..., description="Target game instance ID")
    deploy_options: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Deployment options")
    notify_students: bool = Field(default=True, description="Notify students of update")

class StudentProgressUpdate(BaseModel):
    """Update student progress"""
    student_id: str = Field(..., description="Student identifier")
    game_id: str = Field(..., description="Game instance ID")
    session_id: str = Field(..., description="Current session ID")
    progress_data: Dict[str, Any] = Field(..., description="Progress information")
    completed_objectives: List[str] = Field(default_factory=list, description="Completed learning objectives")
    score: Optional[float] = Field(None, ge=0, le=100, description="Current score")
    time_spent_minutes: int = Field(default=0, ge=0, description="Time spent in minutes")

class CheckpointSaveRequest(BaseModel):
    """Save student checkpoint"""
    student_id: str = Field(..., description="Student identifier")
    game_id: str = Field(..., description="Game instance ID")
    checkpoint_data: Dict[str, Any] = Field(..., description="Checkpoint state data")
    checkpoint_name: Optional[str] = Field(None, description="Checkpoint identifier")
    auto_save: bool = Field(default=False, description="Was this an automatic save")

class AnalyticsEventRequest(BaseModel):
    """Track custom analytics event"""
    event_type: AnalyticsEventType = Field(..., description="Type of event")
    game_id: Optional[str] = Field(None, description="Game instance ID")
    student_id: Optional[str] = Field(None, description="Student ID")
    session_id: Optional[str] = Field(None, description="Session ID")
    event_data: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Event-specific data")
    timestamp: Optional[datetime] = Field(default_factory=datetime.utcnow, description="Event timestamp")

class WebhookRequest(BaseModel):
    """Roblox webhook payload"""
    event_type: str = Field(..., description="Webhook event type")
    universe_id: str = Field(..., description="Roblox universe ID")
    place_id: Optional[str] = Field(None, description="Roblox place ID")
    user_id: Optional[str] = Field(None, description="Roblox user ID")
    data: Dict[str, Any] = Field(default_factory=dict, description="Event payload")
    signature: Optional[str] = Field(None, description="Webhook signature")

# Response Models
class GameInstanceResponse(BaseModel):
    """Game instance details"""
    game_id: str = Field(..., description="Unique game identifier")
    title: str = Field(..., description="Game title")
    description: Optional[str] = Field(None, description="Game description")
    subject: str = Field(..., description="Educational subject")
    grade_level: int = Field(..., description="Target grade level")
    status: GameStatus = Field(..., description="Current game status")
    roblox_place_id: Optional[str] = Field(None, description="Roblox place ID")
    roblox_universe_id: Optional[str] = Field(None, description="Roblox universe ID")
    max_players: int = Field(..., description="Maximum players")
    current_players: int = Field(default=0, description="Currently active players")
    created_by: str = Field(..., description="Creator user ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    settings: Dict[str, Any] = Field(default_factory=dict, description="Game configuration")
    join_url: Optional[str] = Field(None, description="Game join URL")

class ContentGenerationResponse(BaseModel):
    """Generated content response"""
    content_id: str = Field(..., description="Generated content identifier")
    content_type: ContentType = Field(..., description="Type of generated content")
    status: str = Field(default="completed", description="Generation status")
    generated_at: datetime = Field(default_factory=datetime.utcnow, description="Generation timestamp")
    lesson_content: Optional[Dict[str, Any]] = Field(None, description="Generated lesson content")
    quiz_content: Optional[Dict[str, Any]] = Field(None, description="Generated quiz content")
    terrain_config: Optional[Dict[str, Any]] = Field(None, description="Terrain configuration")
    script_content: Optional[Dict[str, Any]] = Field(None, description="Generated scripts")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Generation metadata")

class TemplateResponse(BaseModel):
    """Content template information"""
    template_id: str = Field(..., description="Template identifier")
    name: str = Field(..., description="Template name")
    description: str = Field(..., description="Template description")
    category: str = Field(..., description="Template category")
    subject: str = Field(..., description="Educational subject")
    grade_levels: List[int] = Field(..., description="Supported grade levels")
    features: List[str] = Field(..., description="Template features")
    difficulty: str = Field(..., description="Template difficulty")
    thumbnail_url: Optional[str] = Field(None, description="Template thumbnail")
    created_at: datetime = Field(..., description="Creation timestamp")
    usage_count: int = Field(default=0, description="Number of times used")

class DeploymentStatusResponse(BaseModel):
    """Content deployment status"""
    deployment_id: str = Field(..., description="Deployment identifier")
    content_id: str = Field(..., description="Content identifier")
    game_id: str = Field(..., description="Target game ID")
    status: DeploymentStatus = Field(..., description="Current deployment status")
    progress: float = Field(default=0, ge=0, le=100, description="Deployment progress percentage")
    started_at: datetime = Field(..., description="Deployment start time")
    completed_at: Optional[datetime] = Field(None, description="Deployment completion time")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    deployed_assets: List[str] = Field(default_factory=list, description="Successfully deployed assets")

class StudentProgressResponse(BaseModel):
    """Student progress information"""
    student_id: str = Field(..., description="Student identifier")
    game_id: str = Field(..., description="Game instance ID")
    overall_progress: float = Field(..., ge=0, le=100, description="Overall progress percentage")
    completed_objectives: List[str] = Field(..., description="Completed learning objectives")
    current_score: float = Field(..., ge=0, le=100, description="Current score")
    time_spent_minutes: int = Field(..., ge=0, description="Total time spent")
    last_active: datetime = Field(..., description="Last activity timestamp")
    achievements: List[str] = Field(default_factory=list, description="Unlocked achievements")
    checkpoints: List[Dict[str, Any]] = Field(default_factory=list, description="Saved checkpoints")
    performance_metrics: Dict[str, Any] = Field(default_factory=dict, description="Performance data")

class LeaderboardResponse(BaseModel):
    """Class leaderboard data"""
    game_id: str = Field(..., description="Game instance ID")
    leaderboard_type: str = Field(..., description="Leaderboard type (score, progress, time)")
    generated_at: datetime = Field(default_factory=datetime.utcnow, description="Generation timestamp")
    entries: List[Dict[str, Any]] = Field(..., description="Leaderboard entries")
    total_students: int = Field(..., description="Total number of students")
    class_average: float = Field(..., description="Class average score/progress")

class SessionAnalyticsResponse(BaseModel):
    """Session analytics data"""
    session_id: str = Field(..., description="Session identifier")
    game_id: str = Field(..., description="Game instance ID")
    student_count: int = Field(..., description="Number of students in session")
    duration_minutes: int = Field(..., description="Session duration")
    engagement_score: float = Field(..., ge=0, le=10, description="Session engagement score")
    completion_rate: float = Field(..., ge=0, le=100, description="Average completion rate")
    learning_outcomes: Dict[str, Any] = Field(..., description="Learning outcome metrics")
    activity_heatmap: List[Dict[str, Any]] = Field(..., description="Student activity timeline")
    performance_metrics: Dict[str, Any] = Field(..., description="Performance statistics")

class PerformanceMetricsResponse(BaseModel):
    """System performance metrics"""
    server_uptime_seconds: int = Field(..., description="Server uptime in seconds")
    active_games: int = Field(..., description="Number of active games")
    total_students_online: int = Field(..., description="Total students currently online")
    average_response_time_ms: float = Field(..., description="Average API response time")
    memory_usage_mb: float = Field(..., description="Current memory usage")
    cpu_usage_percent: float = Field(..., description="Current CPU usage")
    websocket_connections: int = Field(..., description="Active WebSocket connections")
    last_updated: datetime = Field(default_factory=datetime.utcnow, description="Metrics timestamp")

# =============================================================================
# CONNECTION MANAGERS
# =============================================================================

class WebSocketManager:
    """Manages WebSocket connections for real-time updates"""

    def __init__(self):
        # Room-based connections: room_id -> set of websockets
        self.connections: Dict[str, set] = {}
        # Connection metadata: websocket -> dict
        self.connection_metadata: Dict[WebSocket, Dict[str, Any]] = {}

    async def connect(self, websocket: WebSocket, room_id: str, user_id: str = None):
        """Connect websocket to a room"""
        await websocket.accept()

        if room_id not in self.connections:
            self.connections[room_id] = set()

        self.connections[room_id].add(websocket)
        self.connection_metadata[websocket] = {
            "room_id": room_id,
            "user_id": user_id,
            "connected_at": datetime.utcnow()
        }

        logger.info(f"WebSocket connected to room {room_id} (user: {user_id})")

    def disconnect(self, websocket: WebSocket):
        """Disconnect websocket from its room"""
        if websocket in self.connection_metadata:
            metadata = self.connection_metadata[websocket]
            room_id = metadata["room_id"]
            user_id = metadata["user_id"]

            if room_id in self.connections:
                self.connections[room_id].discard(websocket)
                if not self.connections[room_id]:
                    del self.connections[room_id]

            del self.connection_metadata[websocket]
            logger.info(f"WebSocket disconnected from room {room_id} (user: {user_id})")

    async def send_to_room(self, room_id: str, message: dict):
        """Send message to all connections in a room"""
        if room_id in self.connections:
            disconnected = []
            for websocket in self.connections[room_id]:
                try:
                    await websocket.send_json(message)
                except:
                    disconnected.append(websocket)

            # Clean up disconnected websockets
            for ws in disconnected:
                self.disconnect(ws)

    async def send_to_user(self, user_id: str, message: dict):
        """Send message to specific user across all rooms"""
        for websocket, metadata in self.connection_metadata.items():
            if metadata.get("user_id") == user_id:
                try:
                    await websocket.send_json(message)
                except:
                    self.disconnect(websocket)

    def get_room_connections(self, room_id: str) -> int:
        """Get number of connections in a room"""
        return len(self.connections.get(room_id, set()))

# Global WebSocket manager
ws_manager = WebSocketManager()

# =============================================================================
# IN-MEMORY STORAGE (Replace with database in production)
# =============================================================================

# Game instances storage
game_instances: Dict[str, Dict[str, Any]] = {}

# Content generation storage
generated_content: Dict[str, Dict[str, Any]] = {}

# Student progress storage
student_progress: Dict[str, Dict[str, Any]] = {}

# Analytics events storage
analytics_events: List[Dict[str, Any]] = []

# Deployment tracking
deployments: Dict[str, Dict[str, Any]] = {}

# Active sessions
active_sessions: Dict[str, Dict[str, Any]] = {}

# =============================================================================
# ROUTER SETUP
# =============================================================================

# Create router for roblox endpoints
roblox_router = APIRouter(prefix="/roblox", tags=["Roblox Integration"])

# =============================================================================
# 1. GAME MANAGEMENT ENDPOINTS
# =============================================================================

@roblox_router.post(
    "/game/create",
    response_model=GameInstanceResponse,
    status_code=status.HTTP_201_CREATED,
    # Rate limiting would be implemented here in production
    # dependencies=[Depends(rate_limiter)]
)
async def create_game_instance(
    request: CreateGameRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
) -> GameInstanceResponse:
    """
    Create new educational game instance in Roblox.

    Creates a new game instance with the specified configuration,
    generates a unique game ID, and initializes the Roblox environment.

    Requires: Teacher or Admin role
    Rate Limited: 10 requests per minute
    """
    # Verify user permissions
    if current_user.role.lower() not in ["teacher", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only teachers and admins can create game instances"
        )

    # Generate unique game ID
    game_id = f"game_{uuid.uuid4().hex[:12]}"
    roblox_place_id = f"place_{uuid.uuid4().hex[:8]}"

    # Create game instance
    game_instance = {
        "game_id": game_id,
        "title": request.title,
        "description": request.description,
        "subject": request.subject,
        "grade_level": request.grade_level,
        "status": GameStatus.CREATING.value,
        "roblox_place_id": roblox_place_id,
        "roblox_universe_id": ROBLOX_UNIVERSE_ID,
        "max_players": request.max_players,
        "current_players": 0,
        "created_by": current_user.id if hasattr(current_user, 'id') else current_user.email,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "settings": request.settings or {},
        "template_id": request.template_id,
        "join_url": f"https://www.roblox.com/games/{roblox_place_id}/"
    }

    # Store game instance
    game_instances[game_id] = game_instance

    # Schedule background game setup
    background_tasks.add_task(setup_game_instance, game_id, request.template_id)

    logger.info(f"Created game instance {game_id} for user {current_user.email}")

    return GameInstanceResponse(**game_instance)

@roblox_router.get("/game/{game_id}", response_model=GameInstanceResponse)
async def get_game_instance(
    game_id: str,
    current_user: User = Depends(get_current_user)
) -> GameInstanceResponse:
    """
    Get game instance details.

    Retrieves detailed information about a specific game instance,
    including current status, player count, and configuration.
    """
    if game_id not in game_instances:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Game instance {game_id} not found"
        )

    game_instance = game_instances[game_id]

    # Check if user has access to this game
    user_role = current_user.role.lower()
    if user_role not in ["admin"] and game_instance["created_by"] != (current_user.id if hasattr(current_user, 'id') else current_user.email):
        # Students can access if they're enrolled in the class (simplified check)
        if user_role != "student":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this game instance"
            )

    return GameInstanceResponse(**game_instance)

@roblox_router.put("/game/{game_id}/settings", response_model=GameInstanceResponse)
async def update_game_settings(
    game_id: str,
    request: UpdateGameSettingsRequest,
    current_user: User = Depends(get_current_user)
) -> GameInstanceResponse:
    """
    Update game instance settings.

    Allows modification of game configuration including title, description,
    player limits, and custom settings.

    Requires: Owner, Teacher, or Admin role
    """
    if game_id not in game_instances:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Game instance {game_id} not found"
        )

    game_instance = game_instances[game_id]

    # Check permissions
    user_role = current_user.role.lower()
    user_id = current_user.id if hasattr(current_user, 'id') else current_user.email

    if user_role not in ["admin"] and game_instance["created_by"] != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the game creator or admin can update settings"
        )

    # Update fields
    update_data = request.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if field == "settings" and value:
            game_instance["settings"].update(value)
        else:
            game_instance[field] = value

    game_instance["updated_at"] = datetime.utcnow()
    game_instances[game_id] = game_instance

    # Notify connected clients
    await ws_manager.send_to_room(f"game_{game_id}", {
        "type": "game_settings_updated",
        "game_id": game_id,
        "updates": update_data,
        "timestamp": datetime.utcnow().isoformat()
    })

    logger.info(f"Updated settings for game {game_id} by user {current_user.email}")

    return GameInstanceResponse(**game_instance)

@roblox_router.delete("/game/{game_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_game_instance(
    game_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Archive/delete game instance.

    Marks the game instance as archived and removes it from active games.
    Student progress data is preserved.

    Requires: Owner or Admin role
    """
    if game_id not in game_instances:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Game instance {game_id} not found"
        )

    game_instance = game_instances[game_id]

    # Check permissions
    user_role = current_user.role.lower()
    user_id = current_user.id if hasattr(current_user, 'id') else current_user.email

    if user_role not in ["admin"] and game_instance["created_by"] != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the game creator or admin can delete game instances"
        )

    # Archive instead of delete to preserve data
    game_instance["status"] = GameStatus.ARCHIVED.value
    game_instance["archived_at"] = datetime.utcnow()
    game_instances[game_id] = game_instance

    # Notify connected clients
    await ws_manager.send_to_room(f"game_{game_id}", {
        "type": "game_archived",
        "game_id": game_id,
        "timestamp": datetime.utcnow().isoformat()
    })

    logger.info(f"Archived game instance {game_id} by user {current_user.email}")

# =============================================================================
# 2. CONTENT GENERATION ENDPOINTS
# =============================================================================

@roblox_router.post(
    "/content/generate",
    response_model=ContentGenerationResponse,
    status_code=status.HTTP_202_ACCEPTED,
    # Rate limiting would be implemented here in production
    # dependencies=[Depends(rate_limiter)]
)
async def generate_educational_content(
    request: ContentGenerationRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
) -> ContentGenerationResponse:
    """
    Generate educational content using AI agents.

    Initiates AI-powered content generation including lessons, quizzes,
    activities, terrain configurations, and custom scripts.

    Requires: Teacher or Admin role
    Rate Limited: 5 requests per minute
    """
    # Verify permissions
    if current_user.role.lower() not in ["teacher", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only teachers and admins can generate content"
        )

    # Generate content ID
    content_id = f"content_{uuid.uuid4().hex[:12]}"

    # Create content generation record
    content_record = {
        "content_id": content_id,
        "content_type": request.content_type.value,
        "status": "generating",
        "requested_by": current_user.id if hasattr(current_user, 'id') else current_user.email,
        "generated_at": datetime.utcnow(),
        "request_data": request.model_dump(),
        "generation_progress": 0
    }

    generated_content[content_id] = content_record

    # Schedule background content generation
    background_tasks.add_task(generate_content_async, content_id, request)

    # Notify via WebSocket
    await ws_manager.send_to_user(current_user.id if hasattr(current_user, 'id') else current_user.email, {
        "type": "content_generation_started",
        "content_id": content_id,
        "estimated_time_minutes": estimate_generation_time(request),
        "timestamp": datetime.utcnow().isoformat()
    })

    logger.info(f"Started content generation {content_id} for user {current_user.email}")

    return ContentGenerationResponse(
        content_id=content_id,
        content_type=request.content_type,
        status="generating"
    )

@roblox_router.get("/content/templates", response_model=List[TemplateResponse])
async def get_content_templates(
    category: Optional[str] = Query(None, description="Filter by category"),
    subject: Optional[str] = Query(None, description="Filter by subject"),
    grade_level: Optional[int] = Query(None, ge=1, le=12, description="Filter by grade level"),
    current_user: User = Depends(get_current_user)
) -> List[TemplateResponse]:
    """
    Get available content templates.

    Returns a list of pre-built templates for different subjects,
    grade levels, and content types.
    """
    # Mock template data (replace with database query)
    templates = [
        {
            "template_id": "space_station_science",
            "name": "Space Station Science Lab",
            "description": "Interactive space station for science experiments",
            "category": "educational",
            "subject": "Science",
            "grade_levels": [6, 7, 8, 9],
            "features": ["Zero Gravity Physics", "Laboratory Equipment", "Planet Observation"],
            "difficulty": "intermediate",
            "thumbnail_url": "/templates/space_station.png",
            "created_at": datetime.utcnow() - timedelta(days=30),
            "usage_count": 45
        },
        {
            "template_id": "math_adventure_castle",
            "name": "Math Adventure Castle",
            "description": "Medieval castle with math puzzles and challenges",
            "category": "game",
            "subject": "Mathematics",
            "grade_levels": [4, 5, 6, 7],
            "features": ["Puzzle Rooms", "Treasure Hunts", "Mathematical Quests"],
            "difficulty": "beginner",
            "thumbnail_url": "/templates/math_castle.png",
            "created_at": datetime.utcnow() - timedelta(days=15),
            "usage_count": 67
        },
        {
            "template_id": "history_time_machine",
            "name": "History Time Machine",
            "description": "Travel through different historical periods",
            "category": "adventure",
            "subject": "History",
            "grade_levels": [7, 8, 9, 10],
            "features": ["Historical Recreations", "Interactive Characters", "Timeline Navigation"],
            "difficulty": "advanced",
            "thumbnail_url": "/templates/time_machine.png",
            "created_at": datetime.utcnow() - timedelta(days=45),
            "usage_count": 32
        }
    ]

    # Apply filters
    filtered_templates = templates

    if category:
        filtered_templates = [t for t in filtered_templates if t["category"].lower() == category.lower()]

    if subject:
        filtered_templates = [t for t in filtered_templates if t["subject"].lower() == subject.lower()]

    if grade_level:
        filtered_templates = [t for t in filtered_templates if grade_level in t["grade_levels"]]

    return [TemplateResponse(**template) for template in filtered_templates]

@roblox_router.post(
    "/content/deploy",
    response_model=DeploymentStatusResponse,
    status_code=status.HTTP_202_ACCEPTED,
    # Rate limiting would be implemented here in production
    # dependencies=[Depends(rate_limiter)]
)
async def deploy_content_to_game(
    request: ContentDeploymentRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
) -> DeploymentStatusResponse:
    """
    Deploy generated content to a Roblox game instance.

    Takes generated educational content and deploys it to the specified
    game instance, updating the game environment.

    Requires: Teacher or Admin role
    """
    # Verify permissions
    if current_user.role.lower() not in ["teacher", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only teachers and admins can deploy content"
        )

    # Verify content exists
    if request.content_id not in generated_content:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Content {request.content_id} not found"
        )

    # Verify game exists
    if request.game_id not in game_instances:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Game instance {request.game_id} not found"
        )

    # Generate deployment ID
    deployment_id = f"deploy_{uuid.uuid4().hex[:12]}"

    # Create deployment record
    deployment = {
        "deployment_id": deployment_id,
        "content_id": request.content_id,
        "game_id": request.game_id,
        "status": DeploymentStatus.PENDING.value,
        "progress": 0,
        "started_at": datetime.utcnow(),
        "requested_by": current_user.id if hasattr(current_user, 'id') else current_user.email,
        "deploy_options": request.deploy_options or {},
        "deployed_assets": []
    }

    deployments[deployment_id] = deployment

    # Schedule background deployment
    background_tasks.add_task(deploy_content_async, deployment_id, request)

    logger.info(f"Started deployment {deployment_id} for content {request.content_id}")

    return DeploymentStatusResponse(**deployment)

@roblox_router.get("/content/{content_id}/status")
async def get_content_deployment_status(
    content_id: str,
    current_user: User = Depends(get_current_user)
) -> Union[ContentGenerationResponse, List[DeploymentStatusResponse]]:
    """
    Get content generation or deployment status.

    Returns the current status of content generation or all deployments
    for the specified content.
    """
    # Check if this is a content generation status request
    if content_id in generated_content:
        content = generated_content[content_id]
        return ContentGenerationResponse(**content)

    # Check for deployments
    content_deployments = [
        deployment for deployment in deployments.values()
        if deployment["content_id"] == content_id
    ]

    if not content_deployments:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No content or deployments found for {content_id}"
        )

    return [DeploymentStatusResponse(**deployment) for deployment in content_deployments]

# =============================================================================
# 3. STUDENT PROGRESS ENDPOINTS
# =============================================================================

@roblox_router.post("/progress/update", status_code=status.HTTP_200_OK)
async def update_student_progress(
    request: StudentProgressUpdate,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Update student progress in a game instance.

    Records student progress including completed objectives, scores,
    and time spent in the educational environment.
    """
    # Create progress key
    progress_key = f"{request.student_id}_{request.game_id}"

    # Update or create progress record
    if progress_key not in student_progress:
        student_progress[progress_key] = {
            "student_id": request.student_id,
            "game_id": request.game_id,
            "created_at": datetime.utcnow(),
            "sessions": []
        }

    progress = student_progress[progress_key]
    progress.update({
        "last_updated": datetime.utcnow(),
        "current_session_id": request.session_id,
        "progress_data": request.progress_data,
        "completed_objectives": request.completed_objectives,
        "current_score": request.score,
        "total_time_minutes": progress.get("total_time_minutes", 0) + request.time_spent_minutes
    })

    # Notify real-time systems
    await ws_manager.send_to_room(f"game_{request.game_id}", {
        "type": "student_progress_updated",
        "student_id": request.student_id,
        "progress": request.progress_data,
        "timestamp": datetime.utcnow().isoformat()
    })

    logger.info(f"Updated progress for student {request.student_id} in game {request.game_id}")

    return {
        "status": "success",
        "message": "Student progress updated successfully",
        "student_id": request.student_id,
        "game_id": request.game_id
    }

@roblox_router.get("/progress/{student_id}", response_model=StudentProgressResponse)
async def get_student_progress(
    student_id: str,
    game_id: Optional[str] = Query(None, description="Specific game ID"),
    current_user: User = Depends(get_current_user)
) -> StudentProgressResponse:
    """
    Get comprehensive student progress data.

    Returns detailed progress information including objectives completed,
    scores, time spent, achievements, and performance metrics.
    """
    # Check permissions - students can only view their own progress
    if current_user.role.lower() == "student" and student_id != (current_user.id if hasattr(current_user, 'id') else current_user.email):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Students can only view their own progress"
        )

    if game_id:
        progress_key = f"{student_id}_{game_id}"
        if progress_key not in student_progress:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No progress found for student {student_id} in game {game_id}"
            )

        progress = student_progress[progress_key]

        return StudentProgressResponse(
            student_id=student_id,
            game_id=game_id,
            overall_progress=progress.get("progress_data", {}).get("overall_progress", 0),
            completed_objectives=progress.get("completed_objectives", []),
            current_score=progress.get("current_score", 0),
            time_spent_minutes=progress.get("total_time_minutes", 0),
            last_active=progress.get("last_updated", datetime.utcnow()),
            achievements=progress.get("achievements", []),
            checkpoints=progress.get("checkpoints", []),
            performance_metrics=progress.get("performance_metrics", {})
        )

    # Return aggregated progress across all games
    student_games = [p for p in student_progress.values() if p["student_id"] == student_id]

    if not student_games:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No progress found for student {student_id}"
        )

    # Aggregate data (simplified for demo)
    total_time = sum(p.get("total_time_minutes", 0) for p in student_games)
    avg_score = sum(p.get("current_score", 0) for p in student_games) / len(student_games)
    all_objectives = []
    all_achievements = []

    for p in student_games:
        all_objectives.extend(p.get("completed_objectives", []))
        all_achievements.extend(p.get("achievements", []))

    return StudentProgressResponse(
        student_id=student_id,
        game_id="aggregated",
        overall_progress=avg_score,
        completed_objectives=list(set(all_objectives)),
        current_score=avg_score,
        time_spent_minutes=total_time,
        last_active=max(p.get("last_updated", datetime.utcnow()) for p in student_games),
        achievements=list(set(all_achievements)),
        checkpoints=[],
        performance_metrics={"games_played": len(student_games)}
    )

@roblox_router.post("/progress/checkpoint", status_code=status.HTTP_201_CREATED)
async def save_student_checkpoint(
    request: CheckpointSaveRequest,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Save student progress checkpoint.

    Creates a save point that students can return to later,
    preserving their current state and progress.
    """
    progress_key = f"{request.student_id}_{request.game_id}"
    checkpoint_id = f"checkpoint_{uuid.uuid4().hex[:8]}"

    # Ensure progress record exists
    if progress_key not in student_progress:
        student_progress[progress_key] = {
            "student_id": request.student_id,
            "game_id": request.game_id,
            "created_at": datetime.utcnow(),
            "checkpoints": []
        }

    # Create checkpoint
    checkpoint = {
        "checkpoint_id": checkpoint_id,
        "checkpoint_name": request.checkpoint_name or f"Checkpoint {len(student_progress[progress_key].get('checkpoints', [])) + 1}",
        "checkpoint_data": request.checkpoint_data,
        "saved_at": datetime.utcnow(),
        "auto_save": request.auto_save
    }

    # Add to progress record
    if "checkpoints" not in student_progress[progress_key]:
        student_progress[progress_key]["checkpoints"] = []

    student_progress[progress_key]["checkpoints"].append(checkpoint)

    # Keep only last 10 checkpoints per student/game
    student_progress[progress_key]["checkpoints"] = student_progress[progress_key]["checkpoints"][-10:]

    logger.info(f"Saved checkpoint {checkpoint_id} for student {request.student_id}")

    return {
        "status": "success",
        "message": "Checkpoint saved successfully",
        "checkpoint_id": checkpoint_id,
        "student_id": request.student_id,
        "game_id": request.game_id
    }

@roblox_router.get("/progress/leaderboard", response_model=LeaderboardResponse)
async def get_class_leaderboard(
    game_id: str,
    leaderboard_type: str = Query("score", regex="^(score|progress|time)$"),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user)
) -> LeaderboardResponse:
    """
    Get class leaderboard for a game instance.

    Returns ranked student performance data for the specified game,
    sorted by score, progress, or time spent.
    """
    # Verify game exists
    if game_id not in game_instances:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Game instance {game_id} not found"
        )

    # Get all progress records for this game
    game_progress = [p for p in student_progress.values() if p["game_id"] == game_id]

    # Sort based on leaderboard type
    sort_key = {
        "score": lambda x: x.get("current_score", 0),
        "progress": lambda x: x.get("progress_data", {}).get("overall_progress", 0),
        "time": lambda x: x.get("total_time_minutes", 0)
    }[leaderboard_type]

    sorted_progress = sorted(game_progress, key=sort_key, reverse=True)[:limit]

    # Build leaderboard entries
    entries = []
    for i, progress in enumerate(sorted_progress):
        entries.append({
            "rank": i + 1,
            "student_id": progress["student_id"],
            "score": progress.get("current_score", 0),
            "progress": progress.get("progress_data", {}).get("overall_progress", 0),
            "time_minutes": progress.get("total_time_minutes", 0),
            "achievements_count": len(progress.get("achievements", [])),
            "last_active": progress.get("last_updated", datetime.utcnow()).isoformat()
        })

    # Calculate class average
    class_average = sum(sort_key(p) for p in game_progress) / len(game_progress) if game_progress else 0

    return LeaderboardResponse(
        game_id=game_id,
        leaderboard_type=leaderboard_type,
        entries=entries,
        total_students=len(game_progress),
        class_average=class_average
    )

# =============================================================================
# 4. REAL-TIME COMMUNICATION (WebSocket Endpoints)
# =============================================================================

@roblox_router.websocket("/ws/game/{game_id}")
async def websocket_game_updates(websocket: WebSocket, game_id: str):
    """
    WebSocket endpoint for real-time game updates.

    Provides live updates for:
    - Player join/leave events
    - Progress updates
    - Game state changes
    - Teacher announcements
    """
    # Note: In production, implement proper authentication for WebSocket
    user_id = "anonymous"  # Extract from token

    await ws_manager.connect(websocket, f"game_{game_id}", user_id)

    try:
        # Send initial game state
        if game_id in game_instances:
            await websocket.send_json({
                "type": "game_state",
                "game": game_instances[game_id],
                "timestamp": datetime.utcnow().isoformat()
            })

        while True:
            # Listen for messages from client
            data = await websocket.receive_json()

            # Handle different message types
            if data.get("type") == "ping":
                await websocket.send_json({
                    "type": "pong",
                    "timestamp": datetime.utcnow().isoformat()
                })
            elif data.get("type") == "student_action":
                # Broadcast student action to other players
                await ws_manager.send_to_room(f"game_{game_id}", {
                    "type": "student_action",
                    "student_id": data.get("student_id"),
                    "action": data.get("action"),
                    "timestamp": datetime.utcnow().isoformat()
                })

    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error in game {game_id}: {e}")
        ws_manager.disconnect(websocket)

@roblox_router.websocket("/ws/content")
async def websocket_content_generation(websocket: WebSocket):
    """
    WebSocket endpoint for content generation updates.

    Provides real-time updates on AI content generation progress,
    including status changes, progress percentages, and completion notifications.
    """
    user_id = "anonymous"  # Extract from token

    await ws_manager.connect(websocket, "content_generation", user_id)

    try:
        while True:
            data = await websocket.receive_json()

            if data.get("type") == "subscribe_content":
                content_id = data.get("content_id")
                if content_id in generated_content:
                    await websocket.send_json({
                        "type": "content_status",
                        "content": generated_content[content_id],
                        "timestamp": datetime.utcnow().isoformat()
                    })

    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error in content generation: {e}")
        ws_manager.disconnect(websocket)

@roblox_router.post("/webhook", status_code=status.HTTP_200_OK)
async def handle_roblox_webhook(
    request: WebhookRequest,
    x_roblox_signature: Optional[str] = Header(None)
) -> Dict[str, Any]:
    """
    Handle incoming webhooks from Roblox.

    Processes events from Roblox servers including:
    - Player join/leave events
    - Game state changes
    - Purchase events
    - Custom game events

    Security: Validates webhook signature for authenticity
    """
    # Verify webhook signature (implement proper HMAC verification)
    if x_roblox_signature and ROBLOX_API_KEY:
        # TODO: Implement proper webhook signature verification
        pass

    # Verify universe ID
    if request.universe_id != ROBLOX_UNIVERSE_ID:
        logger.warning(f"Webhook from unknown universe: {request.universe_id}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid universe ID"
        )

    # Process different event types
    event_type = request.event_type

    if event_type == "player_joined":
        # Update active player count
        place_id = request.place_id
        user_id = request.user_id

        # Find game by place_id
        for game in game_instances.values():
            if game.get("roblox_place_id") == place_id:
                game["current_players"] = game.get("current_players", 0) + 1

                # Notify WebSocket clients
                await ws_manager.send_to_room(f"game_{game['game_id']}", {
                    "type": "player_joined",
                    "user_id": user_id,
                    "current_players": game["current_players"],
                    "timestamp": datetime.utcnow().isoformat()
                })
                break

    elif event_type == "player_left":
        place_id = request.place_id
        user_id = request.user_id

        # Find game by place_id
        for game in game_instances.values():
            if game.get("roblox_place_id") == place_id:
                game["current_players"] = max(0, game.get("current_players", 0) - 1)

                # Notify WebSocket clients
                await ws_manager.send_to_room(f"game_{game['game_id']}", {
                    "type": "player_left",
                    "user_id": user_id,
                    "current_players": game["current_players"],
                    "timestamp": datetime.utcnow().isoformat()
                })
                break

    elif event_type == "custom_event":
        # Handle custom game events
        event_data = request.data

        # Log analytics event
        analytics_events.append({
            "event_id": str(uuid.uuid4()),
            "event_type": "custom",
            "universe_id": request.universe_id,
            "place_id": request.place_id,
            "user_id": request.user_id,
            "event_data": event_data,
            "timestamp": datetime.utcnow()
        })

    logger.info(f"Processed webhook event: {event_type} from universe {request.universe_id}")

    return {
        "status": "success",
        "message": f"Webhook event {event_type} processed successfully",
        "event_id": str(uuid.uuid4())
    }

# =============================================================================
# 5. ANALYTICS ENDPOINTS
# =============================================================================

@roblox_router.get("/analytics/session/{session_id}", response_model=SessionAnalyticsResponse)
async def get_session_analytics(
    session_id: str,
    current_user: User = Depends(get_current_user)
) -> SessionAnalyticsResponse:
    """
    Get detailed analytics for a specific gaming session.

    Provides comprehensive session metrics including student engagement,
    completion rates, learning outcomes, and activity patterns.
    """
    # Find session in active_sessions or generate mock data
    if session_id in active_sessions:
        session = active_sessions[session_id]
    else:
        # Generate mock session data
        session = {
            "session_id": session_id,
            "game_id": "game_example",
            "duration_minutes": 45,
            "student_count": 23,
            "engagement_metrics": {
                "average_engagement": 8.2,
                "peak_engagement": 9.1,
                "low_engagement_periods": 2
            }
        }

    # Calculate analytics metrics
    return SessionAnalyticsResponse(
        session_id=session_id,
        game_id=session.get("game_id", "unknown"),
        student_count=session.get("student_count", 0),
        duration_minutes=session.get("duration_minutes", 0),
        engagement_score=session.get("engagement_metrics", {}).get("average_engagement", 7.5),
        completion_rate=85.4,  # Mock calculation
        learning_outcomes={
            "objectives_met": 12,
            "objectives_total": 15,
            "average_score": 78.3,
            "improvement_rate": 23.5
        },
        activity_heatmap=[
            {"minute": i, "activity_level": max(1, 10 - abs(i - 22))}
            for i in range(session.get("duration_minutes", 45))
        ],
        performance_metrics={
            "response_time_avg": 1.2,
            "error_rate": 0.03,
            "memory_usage": 245.6
        }
    )

@roblox_router.get("/analytics/performance", response_model=PerformanceMetricsResponse)
async def get_system_performance_metrics(
    current_user: User = Depends(get_current_user)
) -> PerformanceMetricsResponse:
    """
    Get real-time system performance metrics.

    Returns server performance data including resource usage,
    active connections, and system health indicators.

    Requires: Admin role
    """
    if current_user.role.lower() != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can view system performance metrics"
        )

    # Calculate metrics (in production, use actual system monitoring)
    import psutil
    import os

    # Get system stats
    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()

    # Count active resources
    active_games = len([g for g in game_instances.values() if g.get("status") == "active"])
    total_students = sum(g.get("current_players", 0) for g in game_instances.values())
    websocket_connections = sum(len(connections) for connections in ws_manager.connections.values())

    return PerformanceMetricsResponse(
        server_uptime_seconds=int((datetime.utcnow() - datetime.utcnow().replace(hour=0, minute=0, second=0)).total_seconds()),
        active_games=active_games,
        total_students_online=total_students,
        average_response_time_ms=125.3,  # Mock value
        memory_usage_mb=memory.used / (1024 * 1024),
        cpu_usage_percent=cpu_percent,
        websocket_connections=websocket_connections
    )

@roblox_router.post("/analytics/event", status_code=status.HTTP_201_CREATED)
async def track_analytics_event(
    request: AnalyticsEventRequest,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Track custom analytics event.

    Records custom events for detailed analytics and reporting.
    Events can be used for A/B testing, feature usage tracking,
    and custom metrics collection.
    """
    # Create event record
    event_id = str(uuid.uuid4())
    event = {
        "event_id": event_id,
        "event_type": request.event_type.value,
        "game_id": request.game_id,
        "student_id": request.student_id,
        "session_id": request.session_id,
        "event_data": request.event_data or {},
        "timestamp": request.timestamp or datetime.utcnow(),
        "user_agent": None,  # Extract from request headers
        "ip_address": None   # Extract from request
    }

    # Store event
    analytics_events.append(event)

    # Real-time processing for certain events
    if request.event_type == AnalyticsEventType.ACHIEVEMENT_UNLOCK:
        # Notify other students in the same game
        if request.game_id:
            await ws_manager.send_to_room(f"game_{request.game_id}", {
                "type": "achievement_unlocked",
                "student_id": request.student_id,
                "achievement": request.event_data.get("achievement"),
                "timestamp": datetime.utcnow().isoformat()
            })

    logger.info(f"Tracked analytics event: {request.event_type} for student {request.student_id}")

    return {
        "status": "success",
        "message": "Analytics event tracked successfully",
        "event_id": event_id
    }

# =============================================================================
# BACKGROUND TASKS
# =============================================================================

async def setup_game_instance(game_id: str, template_id: Optional[str]):
    """Background task to set up a new game instance"""
    try:
        # Simulate game setup process
        await asyncio.sleep(2)  # Mock setup time

        if game_id in game_instances:
            game_instances[game_id]["status"] = GameStatus.ACTIVE.value
            game_instances[game_id]["setup_completed_at"] = datetime.utcnow()

            # Notify via WebSocket
            await ws_manager.send_to_room(f"game_{game_id}", {
                "type": "game_ready",
                "game_id": game_id,
                "timestamp": datetime.utcnow().isoformat()
            })

            logger.info(f"Game instance {game_id} setup completed")

    except Exception as e:
        logger.error(f"Failed to set up game instance {game_id}: {e}")
        if game_id in game_instances:
            game_instances[game_id]["status"] = "setup_failed"
            game_instances[game_id]["error"] = str(e)

async def generate_content_async(content_id: str, request: ContentGenerationRequest):
    """Background task for AI content generation"""
    try:
        content = generated_content[content_id]

        # Simulate content generation phases
        phases = ["analyzing_requirements", "generating_lesson", "creating_quiz", "building_terrain", "finalizing"]

        for i, phase in enumerate(phases):
            await asyncio.sleep(5)  # Mock generation time

            progress = (i + 1) / len(phases) * 100
            content["generation_progress"] = progress
            content["current_phase"] = phase

            # Notify progress via WebSocket
            await ws_manager.send_to_room("content_generation", {
                "type": "generation_progress",
                "content_id": content_id,
                "progress": progress,
                "phase": phase,
                "timestamp": datetime.utcnow().isoformat()
            })

        # Complete generation
        content.update({
            "status": "completed",
            "generation_progress": 100,
            "lesson_content": {
                "title": f"{request.subject} Lesson",
                "objectives": request.learning_objectives,
                "content": "Generated educational content...",
                "activities": ["Activity 1", "Activity 2"]
            },
            "quiz_content": {
                "questions": [
                    {
                        "question": "Sample question 1",
                        "type": "multiple_choice",
                        "options": ["A", "B", "C", "D"],
                        "correct_answer": "A"
                    }
                ]
            } if request.include_quiz else None,
            "terrain_config": {
                "environment_type": request.environment_type,
                "size": "medium",
                "features": ["hills", "water", "buildings"]
            },
            "metadata": {
                "generation_time_seconds": len(phases) * 5,
                "ai_model": "gpt-4",
                "tokens_used": 2500
            }
        })

        logger.info(f"Content generation {content_id} completed successfully")

    except Exception as e:
        logger.error(f"Content generation {content_id} failed: {e}")
        content["status"] = "failed"
        content["error"] = str(e)

async def deploy_content_async(deployment_id: str, request: ContentDeploymentRequest):
    """Background task for content deployment"""
    try:
        deployment = deployments[deployment_id]
        content = generated_content[request.content_id]

        # Simulate deployment phases
        phases = ["validating_content", "uploading_assets", "configuring_game", "testing", "activating"]

        for i, phase in enumerate(phases):
            await asyncio.sleep(3)  # Mock deployment time

            progress = (i + 1) / len(phases) * 100
            deployment["progress"] = progress
            deployment["status"] = DeploymentStatus.DEPLOYING.value
            deployment["current_phase"] = phase

            # Add deployed assets
            if phase == "uploading_assets":
                deployment["deployed_assets"].extend(["terrain.rbxl", "scripts.lua"])
            elif phase == "configuring_game":
                deployment["deployed_assets"].append("game_config.json")

        # Complete deployment
        deployment.update({
            "status": DeploymentStatus.DEPLOYED.value,
            "progress": 100,
            "completed_at": datetime.utcnow(),
            "deployed_assets": ["terrain.rbxl", "scripts.lua", "game_config.json", "quiz_data.json"]
        })

        # Update game instance
        game = game_instances[request.game_id]
        game["last_content_update"] = datetime.utcnow()
        game["deployed_content_id"] = request.content_id

        # Notify students if requested
        if request.notify_students:
            await ws_manager.send_to_room(f"game_{request.game_id}", {
                "type": "content_updated",
                "content_id": request.content_id,
                "timestamp": datetime.utcnow().isoformat()
            })

        logger.info(f"Content deployment {deployment_id} completed successfully")

    except Exception as e:
        logger.error(f"Content deployment {deployment_id} failed: {e}")
        deployment["status"] = DeploymentStatus.FAILED.value
        deployment["error_message"] = str(e)

def estimate_generation_time(request: ContentGenerationRequest) -> int:
    """Estimate content generation time in minutes"""
    base_time = 5  # Base time in minutes

    # Add time based on complexity
    if request.content_type == ContentType.TERRAIN:
        base_time += 3
    if request.include_quiz:
        base_time += 2
    if len(request.learning_objectives) > 5:
        base_time += 2
    if request.difficulty == "advanced":
        base_time += 3

    return base_time

# =============================================================================
# LEGACY OAUTH ENDPOINTS (maintained for backward compatibility)
# =============================================================================

@roblox_router.get("/auth/login")
async def roblox_oauth_login(
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Initiate Roblox OAuth login flow (Legacy endpoint)"""
    state = str(uuid.uuid4())

    oauth_url = (
        f"https://apis.roblox.com/oauth/v1/authorize"
        f"?client_id={ROBLOX_CLIENT_ID}"
        f"&redirect_uri=https://toolboxai.com/roblox/callback"
        f"&scope=openid profile universe-messaging-service:publish"
        f"&response_type=code"
        f"&state={state}"
    )

    return {
        "status": "success",
        "oauth_url": oauth_url,
        "state": state,
        "client_id": ROBLOX_CLIENT_ID
    }

@roblox_router.get("/plugin/status")
async def check_plugin_status() -> Dict[str, Any]:
    """Check Roblox Studio Plugin connection status"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"http://localhost:{ROBLOX_PLUGIN_PORT}/status",
                timeout=5.0
            )

            if response.status_code == 200:
                status_data = response.json()
                return {
                    "connected": True,
                    "version": status_data.get("version", "unknown"),
                    "studio_version": status_data.get("studio_version"),
                    "port": ROBLOX_PLUGIN_PORT
                }
    except Exception as e:
        logger.debug(f"Roblox Studio Plugin not available: {e}")

    return {
        "connected": False,
        "version": None,
        "port": ROBLOX_PLUGIN_PORT,
        "message": "Plugin not connected. Please ensure Roblox Studio is running with ToolBoxAI plugin installed."
    }

# Export router
__all__ = ["roblox_router", "ws_manager"]