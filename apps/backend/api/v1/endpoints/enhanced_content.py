"""
Enhanced Content Generation API Endpoints

Provides comprehensive RESTful API endpoints for the enhanced content generation pipeline
that leverages the 5-stage orchestration system with SPARC framework integration.

Features:
- Content generation with real-time progress tracking
- Quality validation and personalization
- Comprehensive error handling and rate limiting
- JWT authentication integration
- WebSocket support for real-time updates
- OpenAPI documentation

Author: ToolboxAI Team
Created: 2025-09-19
Version: 2.0.0
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional, Union
from uuid import uuid4

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    HTTPException,
    Query,
    Request,
    WebSocket,
    WebSocketDisconnect,
    status,
)
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.ext.asyncio import AsyncSession

from apps.backend.api.auth.auth import (
    get_current_user,
    rate_limit,
    require_role,
    RateLimitError,
    AuthenticationError,
    AuthorizationError,
)
from apps.backend.models.schemas import User, BaseResponse
from apps.backend.services.pusher import trigger_event as pusher_trigger
from apps.backend.services.websocket_pipeline_manager import websocket_pipeline_manager
from apps.backend.services.websocket_handler import websocket_manager
from core.agents.enhanced_content_pipeline import (
    EnhancedContentPipeline,
    PipelineState,
    PipelineStage,
    ContentType,
)
from core.agents.content_quality_validator import (
    ContentQualityValidator,
    ValidationReport,
    ValidationSeverity,
)
from database.content_pipeline_models import (
    EnhancedContentGeneration,
    ContentQualityMetrics,
    LearningProfile,
    ContentPersonalizationLog,
)

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/v1/content", tags=["Enhanced Content Generation"])

# Initialize pipeline components (these would be dependency injected in production)
pipeline_orchestrator = None
quality_validator = None
db_session = None

# In-memory storage for demo purposes
generation_sessions: Dict[str, Dict[str, Any]] = {}
websocket_connections: Dict[str, WebSocket] = {}

# Pydantic Models for Request/Response Validation


class ContentGenerationRequest(BaseModel):
    """Request model for enhanced content generation"""

    subject: str = Field(
        ..., min_length=1, max_length=100, description="Subject area for the content"
    )
    grade_level: str = Field(
        ..., description="Target grade level (e.g., 'K-2', '3-5', '6-8', '9-12')"
    )
    content_type: str = Field(..., description="Type of content to generate")

    learning_objectives: List[str] = Field(
        default_factory=list,
        min_items=1,
        max_items=10,
        description="Specific learning objectives for the content",
    )

    difficulty_level: Optional[str] = Field(
        "medium", description="Difficulty level: 'easy', 'medium', 'hard'"
    )

    duration_minutes: Optional[int] = Field(
        30, ge=5, le=120, description="Expected duration in minutes"
    )

    personalization_enabled: bool = Field(
        True, description="Whether to apply personalization based on user profile"
    )

    roblox_requirements: Optional[Dict[str, Any]] = Field(
        default_factory=dict, description="Specific Roblox environment requirements"
    )

    custom_parameters: Optional[Dict[str, Any]] = Field(
        default_factory=dict, description="Additional custom parameters"
    )

    @field_validator("content_type")
    @classmethod
    def validate_content_type(cls, v):
        valid_types = [
            "lesson",
            "quiz",
            "activity",
            "scenario",
            "assessment",
            "project",
            "simulation",
        ]
        if v.lower() not in valid_types:
            raise ValueError(f"Content type must be one of: {valid_types}")
        return v.lower()

    @field_validator("grade_level")
    @classmethod
    def validate_grade_level(cls, v):
        valid_levels = ["K-2", "3-5", "6-8", "9-12", "college", "adult"]
        if v not in valid_levels:
            raise ValueError(f"Grade level must be one of: {valid_levels}")
        return v


class ContentGenerationResponse(BaseModel):
    """Response model for content generation initiation"""

    pipeline_id: str = Field(..., description="Unique identifier for the generation pipeline")
    status: str = Field(..., description="Current status of the generation")
    message: str = Field(..., description="Human-readable status message")

    estimated_completion_time: Optional[datetime] = Field(
        None, description="Estimated completion time"
    )

    current_stage: str = Field(..., description="Current pipeline stage")
    progress_percentage: float = Field(0.0, ge=0, le=100, description="Completion percentage")

    websocket_url: Optional[str] = Field(None, description="WebSocket URL for real-time updates")

    pusher_channel: Optional[str] = Field(None, description="Pusher channel for real-time updates")


class ContentStatusResponse(BaseModel):
    """Response model for content generation status"""

    pipeline_id: str
    status: str
    current_stage: str
    progress_percentage: float

    started_at: datetime
    estimated_completion: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    stage_details: Dict[str, Any] = Field(default_factory=dict)
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)

    generated_artifacts: Dict[str, Any] = Field(default_factory=dict)
    quality_metrics: Optional[Dict[str, Any]] = None


class GeneratedContentResponse(BaseModel):
    """Response model for retrieved generated content"""

    content_id: str
    pipeline_id: str
    user_id: str

    content_type: str
    subject: str
    grade_level: str

    enhanced_content: Dict[str, Any]
    generated_scripts: List[Dict[str, Any]] = Field(default_factory=list)
    generated_assets: List[Dict[str, Any]] = Field(default_factory=list)

    quality_score: float = Field(ge=0, le=1)
    personalization_applied: bool

    validation_report: Optional[Dict[str, Any]] = None

    created_at: datetime
    generation_time_seconds: float


class ContentValidationRequest(BaseModel):
    """Request model for content validation"""

    content: Dict[str, Any] = Field(..., description="Content to validate")
    content_type: str = Field(..., description="Type of content being validated")
    target_age: int = Field(10, ge=5, le=18, description="Target age for validation")

    validation_categories: Optional[List[str]] = Field(
        None, description="Specific validation categories to run"
    )

    strict_mode: bool = Field(False, description="Whether to use strict validation rules")


class ContentValidationResponse(BaseModel):
    """Response model for content validation results"""

    validation_id: str
    overall_score: float = Field(ge=0, le=1)

    educational_score: float = Field(ge=0, le=1)
    technical_score: float = Field(ge=0, le=1)
    safety_score: float = Field(ge=0, le=1)
    engagement_score: float = Field(ge=0, le=1)
    accessibility_score: float = Field(ge=0, le=1)

    compliant: bool
    issues_count: int
    warnings_count: int

    detailed_report: Dict[str, Any]
    recommendations: List[str]

    validated_at: datetime
    validation_duration_seconds: float


class PersonalizationRequest(BaseModel):
    """Request model for content personalization"""

    content_id: str = Field(..., description="ID of content to personalize")
    personalization_params: Dict[str, Any] = Field(
        default_factory=dict, description="Specific personalization parameters"
    )

    learning_style: Optional[str] = Field(None, description="Preferred learning style")

    difficulty_preference: Optional[str] = Field(None, description="Preferred difficulty level")


class ContentHistoryResponse(BaseModel):
    """Response model for content generation history"""

    items: List[Dict[str, Any]]
    total_count: int
    page: int
    page_size: int
    has_more: bool


# Dependency functions


async def get_pipeline_orchestrator() -> EnhancedContentPipeline:
    """Get or create pipeline orchestrator instance"""
    global pipeline_orchestrator
    if pipeline_orchestrator is None:
        pipeline_orchestrator = EnhancedContentPipeline()
    return pipeline_orchestrator


async def get_quality_validator() -> ContentQualityValidator:
    """Get or create quality validator instance"""
    global quality_validator
    if quality_validator is None:
        quality_validator = ContentQualityValidator()
    return quality_validator


async def get_db_session() -> Optional[AsyncSession]:
    """Get database session (would be implemented with proper session management)"""
    # This would be implemented with proper database session management
    return None


# API Endpoints


@router.post("/generate", response_model=ContentGenerationResponse)
async def generate_enhanced_content(
    request: ContentGenerationRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    pipeline: EnhancedContentPipeline = Depends(get_pipeline_orchestrator),
    _: None = Depends(rate_limit(max_requests=10, window_seconds=60)),  # 10 calls per minute
) -> ContentGenerationResponse:
    """
    Initiate enhanced content generation using the 5-stage pipeline.

    This endpoint triggers the comprehensive content generation process that includes:
    - Ideation: Creative concept generation aligned with learning objectives
    - Generation: Content, script, and asset creation
    - Validation: Quality, safety, and educational value verification
    - Optimization: Performance and personalization enhancements
    - Deployment: Roblox environment packaging and deployment

    Rate Limited: 10 requests per minute per user
    """
    try:
        # Generate unique pipeline ID
        pipeline_id = str(uuid4())

        # Create pipeline state
        pipeline_state = PipelineState(
            pipeline_id=pipeline_id,
            user_id=current_user.id,
            content_type=ContentType(request.content_type),
            original_request=request.model_dump(),
            started_at=datetime.now(),
        )

        # Store session info
        generation_sessions[pipeline_id] = {
            "user_id": current_user.id,
            "request": request.model_dump(),
            "status": "initiated",
            "current_stage": PipelineStage.IDEATION.value,
            "progress": 0.0,
            "started_at": datetime.now(),
            "pipeline_state": pipeline_state,
        }

        # Create Pusher channel for real-time updates
        pusher_channel = f"content-generation-{pipeline_id}"

        # Trigger initial event
        await pusher_trigger(
            pusher_channel,
            "generation-started",
            {
                "pipeline_id": pipeline_id,
                "user_id": current_user.id,
                "status": "initiated",
                "stage": PipelineStage.IDEATION.value,
            },
        )

        # Start background generation process
        background_tasks.add_task(
            run_content_generation, pipeline_id, pipeline_state, pipeline, pusher_channel
        )

        logger.info(
            f"Content generation initiated for user {current_user.id}, pipeline {pipeline_id}"
        )

        return ContentGenerationResponse(
            pipeline_id=pipeline_id,
            status="initiated",
            message="Content generation pipeline started successfully",
            current_stage=PipelineStage.IDEATION.value,
            progress_percentage=0.0,
            pusher_channel=pusher_channel,
            websocket_url=f"/ws/content/{pipeline_id}",
        )

    except Exception as e:
        logger.error(f"Failed to initiate content generation: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to initiate content generation: {str(e)}"
        )


@router.get("/status/{pipeline_id}", response_model=ContentStatusResponse)
async def get_generation_status(
    pipeline_id: str, current_user: User = Depends(get_current_user)
) -> ContentStatusResponse:
    """
    Get the current status of a content generation pipeline.

    Returns detailed information about the pipeline progress, current stage,
    any errors or warnings, and generated artifacts.
    """
    try:
        if pipeline_id not in generation_sessions:
            raise HTTPException(status_code=404, detail=f"Pipeline {pipeline_id} not found")

        session = generation_sessions[pipeline_id]

        # Check if user has access to this pipeline
        if session["user_id"] != current_user.id and current_user.role != "admin":
            raise HTTPException(status_code=403, detail="Access denied to this pipeline")

        pipeline_state = session.get("pipeline_state")

        return ContentStatusResponse(
            pipeline_id=pipeline_id,
            status=session["status"],
            current_stage=session["current_stage"],
            progress_percentage=session.get("progress", 0.0),
            started_at=session["started_at"],
            completed_at=session.get("completed_at"),
            stage_details=session.get("stage_details", {}),
            errors=pipeline_state.errors if pipeline_state else [],
            warnings=session.get("warnings", []),
            generated_artifacts=session.get("artifacts", {}),
            quality_metrics=session.get("quality_metrics"),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get pipeline status: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve pipeline status")


@router.get("/{content_id}", response_model=GeneratedContentResponse)
async def get_generated_content(
    content_id: str,
    current_user: User = Depends(get_current_user),
    include_validation: bool = Query(False, description="Include validation report in response"),
) -> GeneratedContentResponse:
    """
    Retrieve generated content by ID.

    Returns the complete generated content including scripts, assets,
    quality metrics, and optionally the validation report.
    """
    try:
        # In a real implementation, this would query the database
        # For now, simulate with in-memory data

        # Find content in generation sessions
        content_data = None
        for session in generation_sessions.values():
            if session.get("content_id") == content_id:
                content_data = session
                break

        if not content_data:
            raise HTTPException(status_code=404, detail=f"Content {content_id} not found")

        # Check access permissions
        if content_data["user_id"] != current_user.id and current_user.role != "admin":
            raise HTTPException(status_code=403, detail="Access denied to this content")

        pipeline_state = content_data.get("pipeline_state")

        return GeneratedContentResponse(
            content_id=content_id,
            pipeline_id=content_data.get("pipeline_id", ""),
            user_id=content_data["user_id"],
            content_type=content_data["request"]["content_type"],
            subject=content_data["request"]["subject"],
            grade_level=content_data["request"]["grade_level"],
            enhanced_content=pipeline_state.final_content if pipeline_state else {},
            generated_scripts=pipeline_state.scripts if pipeline_state else [],
            generated_assets=pipeline_state.assets if pipeline_state else [],
            quality_score=content_data.get("quality_score", 0.0),
            personalization_applied=content_data.get("personalization_applied", False),
            validation_report=content_data.get("validation_report") if include_validation else None,
            created_at=content_data["started_at"],
            generation_time_seconds=content_data.get("generation_time", 0.0),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to retrieve content: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve content")


@router.post("/validate", response_model=ContentValidationResponse)
async def validate_content(
    request: ContentValidationRequest,
    current_user: User = Depends(get_current_user),
    validator: ContentQualityValidator = Depends(get_quality_validator),
    _: None = Depends(rate_limit(max_requests=20, window_seconds=60)),  # 20 validations per minute
) -> ContentValidationResponse:
    """
    Validate existing content for quality, safety, and compliance.

    Performs comprehensive validation across multiple dimensions:
    - Educational value and alignment
    - Technical quality and performance
    - Safety and age-appropriateness
    - Accessibility standards
    - Engagement design principles

    Rate Limited: 20 requests per minute per user
    """
    try:
        validation_id = str(uuid4())
        start_time = datetime.now()

        # Run content validation
        report = await validator.validate_content(
            content=request.content,
            content_type=request.content_type,
            target_age=request.target_age,
        )

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        logger.info(f"Content validation completed for user {current_user.id}")

        return ContentValidationResponse(
            validation_id=validation_id,
            overall_score=report.overall_score,
            educational_score=report.educational_score,
            technical_score=report.technical_score,
            safety_score=report.safety_score,
            engagement_score=report.engagement_score,
            accessibility_score=report.accessibility_score,
            compliant=report.compliant,
            issues_count=len(report.issues),
            warnings_count=len(report.warnings),
            detailed_report=report.__dict__,
            recommendations=report.recommendations,
            validated_at=end_time,
            validation_duration_seconds=duration,
        )

    except Exception as e:
        logger.error(f"Content validation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Content validation failed: {str(e)}")


@router.get("/history", response_model=ContentHistoryResponse)
async def get_content_history(
    current_user: User = Depends(get_current_user),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    content_type: Optional[str] = Query(None, description="Filter by content type"),
    subject: Optional[str] = Query(None, description="Filter by subject"),
) -> ContentHistoryResponse:
    """
    Get user's content generation history with filtering and pagination.

    Returns a paginated list of all content generated by the current user,
    with optional filtering by content type and subject.
    """
    try:
        # In a real implementation, this would query the database
        # For now, filter in-memory sessions

        user_sessions = [
            session
            for session in generation_sessions.values()
            if session["user_id"] == current_user.id
        ]

        # Apply filters
        if content_type:
            user_sessions = [
                s for s in user_sessions if s["request"]["content_type"] == content_type
            ]

        if subject:
            user_sessions = [
                s for s in user_sessions if s["request"]["subject"].lower() == subject.lower()
            ]

        # Sort by creation time (newest first)
        user_sessions.sort(key=lambda x: x["started_at"], reverse=True)

        # Pagination
        total_count = len(user_sessions)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        page_items = user_sessions[start_idx:end_idx]

        # Format response items
        items = []
        for session in page_items:
            items.append(
                {
                    "pipeline_id": session.get("pipeline_id", ""),
                    "content_id": session.get("content_id"),
                    "content_type": session["request"]["content_type"],
                    "subject": session["request"]["subject"],
                    "grade_level": session["request"]["grade_level"],
                    "status": session["status"],
                    "quality_score": session.get("quality_score"),
                    "created_at": session["started_at"],
                    "completed_at": session.get("completed_at"),
                    "generation_time": session.get("generation_time", 0.0),
                }
            )

        return ContentHistoryResponse(
            items=items,
            total_count=total_count,
            page=page,
            page_size=page_size,
            has_more=end_idx < total_count,
        )

    except Exception as e:
        logger.error(f"Failed to retrieve content history: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve content history")


@router.post("/personalize", response_model=Dict[str, Any])
async def apply_personalization(
    request: PersonalizationRequest,
    current_user: User = Depends(get_current_user),
    _: None = Depends(
        rate_limit(max_requests=15, window_seconds=60)
    ),  # 15 personalizations per minute
) -> Dict[str, Any]:
    """
    Apply personalization to existing content based on user profile.

    Customizes content based on learning style preferences, difficulty level,
    and other personalization parameters.

    Rate Limited: 15 requests per minute per user
    """
    try:
        # Find the content
        content_session = None
        for session in generation_sessions.values():
            if session.get("content_id") == request.content_id:
                content_session = session
                break

        if not content_session:
            raise HTTPException(status_code=404, detail=f"Content {request.content_id} not found")

        # Check permissions
        if content_session["user_id"] != current_user.id and current_user.role != "admin":
            raise HTTPException(status_code=403, detail="Access denied to this content")

        # Apply personalization (simplified implementation)
        personalization_log = {
            "user_id": current_user.id,
            "content_id": request.content_id,
            "personalization_type": "user_preferences",
            "parameters": request.personalization_params,
            "applied_at": datetime.now(),
            "success": True,
        }

        # Update session with personalization info
        content_session["personalization_applied"] = True
        content_session["personalization_log"] = personalization_log

        logger.info(
            f"Personalization applied to content {request.content_id} for user {current_user.id}"
        )

        return {
            "success": True,
            "message": "Personalization applied successfully",
            "content_id": request.content_id,
            "personalization_id": str(uuid4()),
            "applied_at": personalization_log["applied_at"],
            "parameters": request.personalization_params,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to apply personalization: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to apply personalization: {str(e)}")


@router.websocket("/ws/{pipeline_id}")
async def content_generation_websocket(websocket: WebSocket, pipeline_id: str):
    """
    Enhanced WebSocket endpoint for real-time content generation updates.

    Features:
    - Automatic state management and recovery
    - Redis-backed persistence for reliability
    - Integrated Pusher fallback for redundancy
    - Graceful error handling and reconnection support
    - Detailed progress tracking across all pipeline stages

    Connection Protocol:
    1. Client connects to /ws/{pipeline_id}
    2. Server sends current state if available
    3. Server sends real-time updates during generation
    4. Heartbeat keeps connection alive
    5. Completion/error triggers cleanup after delay
    """
    # Initialize manager if needed
    if not hasattr(websocket_pipeline_manager, "redis"):
        await websocket_pipeline_manager.initialize()

    # Connect to pipeline
    await websocket_pipeline_manager.connect(websocket, pipeline_id)

    try:
        # Keep connection alive and handle messages
        while True:
            try:
                # Wait for incoming messages with timeout
                data = await asyncio.wait_for(
                    websocket.receive_json(), timeout=60.0  # Longer timeout since we have heartbeat
                )

                # Handle message through manager
                await websocket_pipeline_manager.handle_message(websocket, pipeline_id, data)

            except asyncio.TimeoutError:
                # Timeout is normal - heartbeat handles keepalive
                continue

            except WebSocketDisconnect:
                logger.info(f"WebSocket client disconnected for pipeline {pipeline_id}")
                break

            except Exception as e:
                logger.error(f"Error handling WebSocket message: {e}")
                await websocket_pipeline_manager.send_error(
                    pipeline_id, f"Message handling error: {str(e)}"
                )

    except WebSocketDisconnect:
        # Normal disconnection
        pass

    except Exception as e:
        logger.error(f"WebSocket error for pipeline {pipeline_id}: {e}")

    finally:
        # Clean up connection
        await websocket_pipeline_manager.disconnect(websocket, pipeline_id)


# Background Tasks


async def run_content_generation(
    pipeline_id: str,
    pipeline_state: PipelineState,
    pipeline: EnhancedContentPipeline,
    pusher_channel: str,
):
    """
    Background task to run the content generation pipeline.

    Executes the 5-stage pipeline and sends real-time updates via Pusher and WebSocket.
    """
    session = generation_sessions[pipeline_id]

    try:
        logger.info(f"Starting content generation pipeline {pipeline_id}")

        # Update status to processing
        session["status"] = "processing"
        session["current_stage"] = PipelineStage.IDEATION.value

        await send_pipeline_update(
            pipeline_id,
            pusher_channel,
            "stage-started",
            {
                "stage": PipelineStage.IDEATION.value,
                "progress": 10.0,
                "message": "Starting creative ideation process",
            },
        )

        # Simulate pipeline stages (in real implementation, this would use the actual pipeline)
        stages = [
            (PipelineStage.IDEATION, 20, "Generating creative educational concepts"),
            (PipelineStage.GENERATION, 40, "Creating content, scripts, and assets"),
            (PipelineStage.VALIDATION, 60, "Validating quality and safety"),
            (PipelineStage.OPTIMIZATION, 80, "Optimizing for engagement and performance"),
            (PipelineStage.DEPLOYMENT, 95, "Packaging for Roblox deployment"),
        ]

        for stage, progress, message in stages:
            # Simulate processing time
            await asyncio.sleep(2)

            session["current_stage"] = stage.value
            session["progress"] = progress

            await send_pipeline_update(
                pipeline_id,
                pusher_channel,
                "stage-progress",
                {"stage": stage.value, "progress": progress, "message": message},
            )

        # Complete the generation
        session["status"] = "completed"
        session["current_stage"] = PipelineStage.COMPLETED.value
        session["progress"] = 100.0
        session["completed_at"] = datetime.now()
        session["content_id"] = str(uuid4())
        session["quality_score"] = 0.85
        session["generation_time"] = (datetime.now() - session["started_at"]).total_seconds()

        await send_pipeline_update(
            pipeline_id,
            pusher_channel,
            "generation-completed",
            {
                "content_id": session["content_id"],
                "quality_score": session["quality_score"],
                "generation_time": session["generation_time"],
                "message": "Content generation completed successfully",
            },
        )

        logger.info(f"Content generation pipeline {pipeline_id} completed successfully")

    except Exception as e:
        logger.error(f"Content generation pipeline {pipeline_id} failed: {e}")

        session["status"] = "failed"
        session["current_stage"] = PipelineStage.FAILED.value
        session["errors"] = [str(e)]
        session["completed_at"] = datetime.now()

        await send_pipeline_update(
            pipeline_id,
            pusher_channel,
            "generation-failed",
            {"error": str(e), "message": "Content generation failed"},
        )


async def send_pipeline_update(
    pipeline_id: str, pusher_channel: str, event_type: str, data: Dict[str, Any]
):
    """
    Enhanced pipeline update sender using WebSocketPipelineManager.

    Sends updates via:
    1. WebSocketPipelineManager for direct WebSocket connections
    2. Pusher for redundancy and broader reach
    3. Redis for persistence
    """
    # Extract stage and progress from data
    stage = data.get("stage", PipelineStage.PROCESSING.value)
    progress = data.get("progress", 0.0)
    message = data.get("message", "Processing...")

    # Send via WebSocketPipelineManager
    try:
        if not hasattr(websocket_pipeline_manager, "redis"):
            await websocket_pipeline_manager.initialize()

        # Map string stage to enum if needed
        if isinstance(stage, str):
            stage = PipelineStage(stage)

        await websocket_pipeline_manager.update_pipeline_state(
            pipeline_id=pipeline_id, stage=stage, progress=progress, message=message, metadata=data
        )
    except Exception as e:
        logger.warning(f"Failed to send WebSocket update: {e}")

    # Send via Pusher for redundancy
    try:
        await pusher_trigger(
            pusher_channel,
            event_type,
            {"pipeline_id": pipeline_id, "timestamp": datetime.now().isoformat(), **data},
        )
    except Exception as e:
        logger.warning(f"Failed to send Pusher update: {e}")


# Export the router
__all__ = ["router"]
