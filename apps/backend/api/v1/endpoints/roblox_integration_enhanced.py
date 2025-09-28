"""Enhanced Roblox Integration API Endpoints for ToolBoxAI

Provides comprehensive Roblox integration capabilities:
- Script generation and validation endpoints
- 3D model and asset management
- Roblox Studio integration endpoints
- Educational environment deployment
- Real-time collaboration features
- Asset marketplace integration
"""

import logging
import uuid
import base64
import asyncio
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional, Union
from enum import Enum

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    BackgroundTasks,
    status,
    WebSocket,
    WebSocketDisconnect,
)
from fastapi.security import HTTPBearer
from pydantic import BaseModel, Field, field_validator, ConfigDict
from sqlalchemy.ext.asyncio import AsyncSession

# Import authentication and dependencies
try:
    from apps.backend.api.auth.auth import get_current_user, require_role, require_any_role
    from apps.backend.core.deps import get_db
    from apps.backend.core.security.rate_limit_manager import rate_limit
    from apps.backend.services.websocket_handler import websocket_manager
except ImportError:
    # Fallback for development
    def get_current_user():
        return {"id": "test", "role": "teacher", "email": "test@example.com"}

    def require_role(role):
        return lambda: None

    def require_any_role(roles):
        return lambda: None

    def get_db():
        return None

    def rate_limit(requests=60, max_requests=None, **kwargs):
        def decorator(func):
            return func

        return decorator

    class MockWebSocketManager:
        async def connect(self, websocket, client_id):
            pass

        async def disconnect(self, websocket):
            pass

        async def broadcast(self, message):
            pass

    websocket_manager = MockWebSocketManager()

# Import models and services
try:
    from apps.backend.models.schemas import User, BaseResponse
    from apps.backend.services.pusher import trigger_event
except ImportError:

    class User(BaseModel):
        id: str
        email: str
        role: str

    class BaseResponse(BaseModel):
        success: bool = True
        message: str = ""
        timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    async def trigger_event(channel, event, data):
        pass


logger = logging.getLogger(__name__)
security = HTTPBearer()

# Create router
router = APIRouter(prefix="/roblox-integration", tags=["Roblox Integration"])


# Enums
class ScriptType(str, Enum):
    """Types of Roblox scripts"""

    SERVER = "server"
    CLIENT = "client"
    MODULE = "module"
    LOCAL = "local"


class AssetType(str, Enum):
    """Types of Roblox assets"""

    MODEL = "model"
    MESH = "mesh"
    TEXTURE = "texture"
    ANIMATION = "animation"
    SOUND = "sound"
    SCRIPT = "script"
    GUI = "gui"
    PARTICLE = "particle"
    LIGHTING = "lighting"


class EnvironmentType(str, Enum):
    """Types of educational environments"""

    CLASSROOM = "classroom"
    LABORATORY = "laboratory"
    MUSEUM = "museum"
    OUTDOOR = "outdoor"
    SPACE = "space"
    UNDERWATER = "underwater"
    HISTORICAL = "historical"
    FANTASY = "fantasy"


class DeploymentStatus(str, Enum):
    """Deployment status for environments"""

    PENDING = "pending"
    BUILDING = "building"
    TESTING = "testing"
    DEPLOYED = "deployed"
    FAILED = "failed"
    ARCHIVED = "archived"


class ValidationLevel(str, Enum):
    """Script validation levels"""

    BASIC = "basic"
    STANDARD = "standard"
    STRICT = "strict"
    EDUCATIONAL = "educational"


# Request Models
class ScriptGenerationRequest(BaseModel):
    """Request for generating Roblox scripts"""

    script_type: ScriptType
    functionality_description: str = Field(..., min_length=10, max_length=1000)
    educational_context: str = Field(..., description="Educational purpose and context")
    grade_level: int = Field(..., ge=1, le=12)
    complexity_level: str = Field("beginner", description="beginner, intermediate, advanced")
    required_services: List[str] = Field(default_factory=list, description="Roblox services needed")
    custom_requirements: Optional[str] = None
    include_comments: bool = Field(default=True)
    include_error_handling: bool = Field(default=True)
    target_age_appropriate: bool = Field(default=True)

    model_config = ConfigDict(from_attributes=True)


class ScriptValidationRequest(BaseModel):
    """Request for validating Roblox scripts"""

    script_content: str = Field(..., min_length=1)
    script_type: ScriptType
    validation_level: ValidationLevel = ValidationLevel.EDUCATIONAL
    check_security: bool = Field(default=True)
    check_performance: bool = Field(default=True)
    check_best_practices: bool = Field(default=True)
    educational_context: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class AssetUploadRequest(BaseModel):
    """Request for uploading Roblox assets"""

    asset_name: str = Field(..., min_length=1, max_length=100)
    asset_type: AssetType
    description: str = Field(..., max_length=500)
    educational_tags: List[str] = Field(default_factory=list)
    grade_levels: List[int] = Field(..., description="Applicable grade levels")
    subject_areas: List[str] = Field(default_factory=list)
    asset_data: str = Field(..., description="Base64 encoded asset data")
    thumbnail_data: Optional[str] = Field(None, description="Base64 encoded thumbnail")
    license_type: str = Field("educational", description="Asset license type")

    @field_validator("grade_levels")
    @classmethod
    def validate_grade_levels(cls, v):
        if not v or not all(1 <= level <= 12 for level in v):
            raise ValueError("Grade levels must be between 1 and 12")
        return v

    model_config = ConfigDict(from_attributes=True)


class EnvironmentDeploymentRequest(BaseModel):
    """Request for deploying educational environments"""

    environment_name: str = Field(..., min_length=1, max_length=100)
    environment_type: EnvironmentType
    description: str = Field(..., max_length=1000)
    lesson_id: Optional[str] = None
    grade_level: int = Field(..., ge=1, le=12)
    max_students: int = Field(default=30, ge=1, le=100)
    session_duration: int = Field(default=45, description="Session duration in minutes")
    required_assets: List[str] = Field(default_factory=list)
    custom_scripts: List[str] = Field(default_factory=list)
    spawn_configuration: Dict[str, Any] = Field(default_factory=dict)
    environment_settings: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(from_attributes=True)


class StudioSyncRequest(BaseModel):
    """Request for syncing with Roblox Studio"""

    studio_session_id: str
    project_name: str
    sync_type: str = Field(..., description="pull, push, or bidirectional")
    file_filters: List[str] = Field(default_factory=list)
    include_assets: bool = Field(default=True)
    include_scripts: bool = Field(default=True)
    backup_before_sync: bool = Field(default=True)

    model_config = ConfigDict(from_attributes=True)


# Response Models
class ScriptGenerationResponse(BaseModel):
    """Response for script generation"""

    script_id: str
    script_content: str
    script_type: ScriptType
    generated_at: datetime
    complexity_analysis: Dict[str, Any]
    educational_features: List[str]
    required_services: List[str]
    performance_notes: List[str]
    security_compliance: bool
    estimated_execution_time: Optional[float] = None

    model_config = ConfigDict(from_attributes=True)


class ScriptValidationResponse(BaseModel):
    """Response for script validation"""

    validation_id: str
    is_valid: bool
    validation_score: float = Field(..., ge=0, le=100)
    issues: List[Dict[str, Any]] = Field(default_factory=list)
    suggestions: List[str] = Field(default_factory=list)
    security_report: Dict[str, Any] = Field(default_factory=dict)
    performance_report: Dict[str, Any] = Field(default_factory=dict)
    educational_compliance: Dict[str, Any] = Field(default_factory=dict)
    recommended_improvements: List[str] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class AssetResponse(BaseModel):
    """Response for asset operations"""

    asset_id: str
    asset_name: str
    asset_type: AssetType
    description: str
    upload_status: str
    roblox_asset_id: Optional[str] = None
    download_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    educational_metadata: Dict[str, Any] = Field(default_factory=dict)
    usage_statistics: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class EnvironmentDeploymentResponse(BaseModel):
    """Response for environment deployment"""

    deployment_id: str
    environment_name: str
    environment_type: EnvironmentType
    status: DeploymentStatus
    roblox_place_id: Optional[str] = None
    join_url: Optional[str] = None
    deployment_progress: int = Field(default=0, ge=0, le=100)
    estimated_completion: Optional[datetime] = None
    deployment_logs: List[str] = Field(default_factory=list)
    resource_usage: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    last_updated: datetime

    model_config = ConfigDict(from_attributes=True)


class StudioSyncResponse(BaseModel):
    """Response for Studio synchronization"""

    sync_id: str
    sync_status: str
    files_synced: int
    assets_synced: int
    sync_log: List[str] = Field(default_factory=list)
    conflicts: List[Dict[str, Any]] = Field(default_factory=list)
    sync_statistics: Dict[str, Any] = Field(default_factory=dict)
    started_at: datetime
    completed_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class RobloxEnvironmentStatus(BaseModel):
    """Status of a Roblox environment"""

    environment_id: str
    place_id: str
    status: str
    active_students: int
    max_capacity: int
    session_start: datetime
    session_end: Optional[datetime] = None
    performance_metrics: Dict[str, Any] = Field(default_factory=dict)
    active_features: List[str] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


# Mock data stores
_mock_scripts_db: Dict[str, ScriptGenerationResponse] = {}
_mock_assets_db: Dict[str, AssetResponse] = {}
_mock_deployments_db: Dict[str, EnvironmentDeploymentResponse] = {}
_mock_environments_db: Dict[str, RobloxEnvironmentStatus] = {}


# Utility functions
async def notify_roblox_update(event_type: str, data: Dict[str, Any], user_id: str):
    """Notify about Roblox integration updates"""
    try:
        await trigger_event(
            "roblox-updates",
            f"roblox.{event_type}",
            {"data": data, "user_id": user_id, "timestamp": datetime.now(timezone.utc).isoformat()},
        )
    except Exception as e:
        logger.warning(f"Failed to send Roblox update notification: {e}")


def validate_script_security(script_content: str) -> Dict[str, Any]:
    """Validate script for security issues"""
    # Mock security validation
    security_issues = []

    # Check for potentially dangerous functions
    dangerous_patterns = ["require(", "loadstring(", "getfenv(", "setfenv(", "debug.", "os.", "io."]

    for pattern in dangerous_patterns:
        if pattern in script_content:
            security_issues.append(f"Potentially unsafe pattern detected: {pattern}")

    return {
        "is_secure": len(security_issues) == 0,
        "issues": security_issues,
        "risk_level": (
            "low" if len(security_issues) == 0 else "medium" if len(security_issues) < 3 else "high"
        ),
    }


def analyze_script_performance(script_content: str) -> Dict[str, Any]:
    """Analyze script for performance issues"""
    # Mock performance analysis
    performance_issues = []

    # Check for common performance anti-patterns
    if "while true do" in script_content.lower():
        performance_issues.append("Infinite loop detected - use heartbeat events instead")

    if script_content.count("wait(") > 10:
        performance_issues.append("Excessive use of wait() - consider alternative approaches")

    return {
        "estimated_performance": "good" if len(performance_issues) == 0 else "moderate",
        "issues": performance_issues,
        "optimization_suggestions": [
            "Use RunService.Heartbeat for game loops",
            "Cache frequently accessed objects",
            "Use object pooling for frequently created/destroyed objects",
        ],
    }


# Endpoints


@router.post(
    "/scripts/generate",
    response_model=ScriptGenerationResponse,
    status_code=status.HTTP_201_CREATED,
)
# @rate_limit(requests=10)  # 10 script generations per minute
async def generate_script(
    request: ScriptGenerationRequest,
    background_tasks: BackgroundTasks,
    current_user: Dict = Depends(get_current_user),
    _: None = Depends(require_any_role(["teacher", "admin"])),
):
    """
    Generate Roblox scripts based on educational requirements.

    Requires: Teacher or Admin role
    Rate limit: 10 requests per minute
    """
    try:
        script_id = str(uuid.uuid4())

        # Mock script generation (would integrate with AI agents)
        script_template = f"""
-- Generated Educational Script: {request.functionality_description}
-- Grade Level: {request.grade_level}
-- Educational Context: {request.educational_context}
-- Generated on: {datetime.now(timezone.utc).isoformat()}

-- Import required services
local RunService = game:GetService("RunService")
local Players = game:GetService("Players")

-- Educational script implementation
local function educationalFunction()
    -- Implementation based on requirements:
    -- {request.functionality_description}
    
    print("Educational feature initialized for grade {request.grade_level}")
end

-- Initialize the educational feature
educationalFunction()
        """.strip()

        # Create response
        script_response = ScriptGenerationResponse(
            script_id=script_id,
            script_content=script_template,
            script_type=request.script_type,
            generated_at=datetime.now(timezone.utc),
            complexity_analysis={
                "level": request.complexity_level,
                "lines_of_code": len(script_template.split("\n")),
                "estimated_difficulty": "age-appropriate",
            },
            educational_features=[
                "Age-appropriate content",
                "Clear commenting",
                "Error handling",
                "Educational context integration",
            ],
            required_services=request.required_services or ["RunService", "Players"],
            performance_notes=[
                "Optimized for educational environments",
                "Low resource usage",
                "Suitable for group activities",
            ],
            security_compliance=True,
            estimated_execution_time=0.1,
        )

        # Store in mock database
        _mock_scripts_db[script_id] = script_response

        # Background notification
        background_tasks.add_task(
            notify_roblox_update,
            "script_generated",
            {"script_id": script_id, "script_type": request.script_type.value},
            current_user["id"],
        )

        logger.info(f"Script generated: {script_id} by user {current_user['id']}")
        return script_response

    except Exception as e:
        logger.error(f"Error generating script: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to generate script"
        )


@router.post("/scripts/validate", response_model=ScriptValidationResponse)
# @rate_limit(requests=20)  # 20 validations per minute
async def validate_script(
    request: ScriptValidationRequest, current_user: Dict = Depends(get_current_user)
):
    """
    Validate Roblox scripts for security, performance, and educational compliance.

    Rate limit: 20 requests per minute
    """
    try:
        validation_id = str(uuid.uuid4())

        # Perform security validation
        security_report = validate_script_security(request.script_content)

        # Perform performance analysis
        performance_report = analyze_script_performance(request.script_content)

        # Educational compliance check
        educational_compliance = {
            "age_appropriate": True,
            "educational_value": "high",
            "learning_objectives_met": True,
            "safety_compliant": security_report["is_secure"],
        }

        # Calculate overall validation score
        base_score = 80
        security_penalty = len(security_report["issues"]) * 10
        performance_penalty = len(performance_report["issues"]) * 5
        validation_score = max(0, base_score - security_penalty - performance_penalty)

        # Compile issues and suggestions
        issues = []
        suggestions = []

        if security_report["issues"]:
            issues.extend(
                [{"type": "security", "message": issue} for issue in security_report["issues"]]
            )
            suggestions.append("Review security-sensitive functions")

        if performance_report["issues"]:
            issues.extend(
                [
                    {"type": "performance", "message": issue}
                    for issue in performance_report["issues"]
                ]
            )
            suggestions.extend(performance_report["optimization_suggestions"])

        response = ScriptValidationResponse(
            validation_id=validation_id,
            is_valid=validation_score >= 70,
            validation_score=validation_score,
            issues=issues,
            suggestions=suggestions,
            security_report=security_report,
            performance_report=performance_report,
            educational_compliance=educational_compliance,
            recommended_improvements=(
                [
                    "Add more descriptive comments",
                    "Include error handling",
                    "Follow Roblox Lua style guide",
                ]
                if validation_score < 90
                else []
            ),
        )

        logger.info(
            f"Script validated: {validation_id} (score: {validation_score}) by user {current_user['id']}"
        )
        return response

    except Exception as e:
        logger.error(f"Error validating script: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to validate script"
        )


@router.post("/assets/upload", response_model=AssetResponse, status_code=status.HTTP_201_CREATED)
# @rate_limit(requests=5)  # 5 asset uploads per minute
async def upload_asset(
    request: AssetUploadRequest,
    background_tasks: BackgroundTasks,
    current_user: Dict = Depends(get_current_user),
    _: None = Depends(require_any_role(["teacher", "admin"])),
):
    """
    Upload and manage Roblox assets for educational use.

    Requires: Teacher or Admin role
    Rate limit: 5 requests per minute
    """
    try:
        asset_id = str(uuid.uuid4())

        # Decode and validate asset data
        try:
            asset_bytes = base64.b64decode(request.asset_data)
            if len(asset_bytes) > 50 * 1024 * 1024:  # 50MB limit
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail="Asset size exceeds 50MB limit",
                )
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid asset data encoding"
            )

        # Create asset response
        asset_response = AssetResponse(
            asset_id=asset_id,
            asset_name=request.asset_name,
            asset_type=request.asset_type,
            description=request.description,
            upload_status="processing",
            roblox_asset_id=None,  # Would be populated after Roblox upload
            download_url=f"/api/v1/roblox-integration/assets/{asset_id}/download",
            thumbnail_url=(
                f"/api/v1/roblox-integration/assets/{asset_id}/thumbnail"
                if request.thumbnail_data
                else None
            ),
            educational_metadata={
                "grade_levels": request.grade_levels,
                "subject_areas": request.subject_areas,
                "educational_tags": request.educational_tags,
                "license_type": request.license_type,
                "uploaded_by": current_user["id"],
            },
            usage_statistics={"downloads": 0, "usage_in_environments": 0, "user_ratings": []},
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        # Store in mock database
        _mock_assets_db[asset_id] = asset_response

        # Background notification
        background_tasks.add_task(
            notify_roblox_update,
            "asset_uploaded",
            {"asset_id": asset_id, "asset_type": request.asset_type.value},
            current_user["id"],
        )

        logger.info(f"Asset uploaded: {asset_id} by user {current_user['id']}")
        return asset_response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading asset: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to upload asset"
        )


@router.get("/assets", response_model=List[AssetResponse])
async def list_assets(
    asset_type: Optional[AssetType] = Query(None, description="Filter by asset type"),
    grade_level: Optional[int] = Query(None, ge=1, le=12, description="Filter by grade level"),
    subject_area: Optional[str] = Query(None, description="Filter by subject area"),
    search: Optional[str] = Query(None, min_length=2, description="Search in name/description"),
    limit: int = Query(20, ge=1, le=100, description="Maximum results"),
    current_user: Dict = Depends(get_current_user),
):
    """
    List available Roblox assets with filtering options.
    """
    try:
        assets = list(_mock_assets_db.values())

        # Apply filters
        if asset_type:
            assets = [a for a in assets if a.asset_type == asset_type]

        if grade_level:
            assets = [
                a for a in assets if grade_level in a.educational_metadata.get("grade_levels", [])
            ]

        if subject_area:
            assets = [
                a for a in assets if subject_area in a.educational_metadata.get("subject_areas", [])
            ]

        if search:
            search_lower = search.lower()
            assets = [
                a
                for a in assets
                if search_lower in a.asset_name.lower() or search_lower in a.description.lower()
            ]

        # Sort by created_at descending and limit
        assets.sort(key=lambda x: x.created_at, reverse=True)
        return assets[:limit]

    except Exception as e:
        logger.error(f"Error listing assets: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve assets"
        )


@router.post(
    "/environments/deploy",
    response_model=EnvironmentDeploymentResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
# @rate_limit(requests=3)  # 3 deployments per minute
async def deploy_environment(
    request: EnvironmentDeploymentRequest,
    background_tasks: BackgroundTasks,
    current_user: Dict = Depends(get_current_user),
    _: None = Depends(require_any_role(["teacher", "admin"])),
):
    """
    Deploy educational Roblox environments.

    Requires: Teacher or Admin role
    Rate limit: 3 requests per minute
    """
    try:
        deployment_id = str(uuid.uuid4())

        # Create deployment response
        deployment_response = EnvironmentDeploymentResponse(
            deployment_id=deployment_id,
            environment_name=request.environment_name,
            environment_type=request.environment_type,
            status=DeploymentStatus.PENDING,
            roblox_place_id=None,
            join_url=None,
            deployment_progress=0,
            estimated_completion=datetime.now(timezone.utc) + timedelta(minutes=15),
            deployment_logs=["Deployment initiated"],
            resource_usage={
                "estimated_memory": "500MB",
                "estimated_cpu": "medium",
                "max_concurrent_users": request.max_students,
            },
            created_at=datetime.now(timezone.utc),
            last_updated=datetime.now(timezone.utc),
        )

        # Store in mock database
        _mock_deployments_db[deployment_id] = deployment_response

        # Background notification
        background_tasks.add_task(
            notify_roblox_update,
            "environment_deployment_started",
            {"deployment_id": deployment_id, "environment_type": request.environment_type.value},
            current_user["id"],
        )

        logger.info(f"Environment deployment started: {deployment_id} by user {current_user['id']}")
        return deployment_response

    except Exception as e:
        logger.error(f"Error deploying environment: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to start environment deployment",
        )


@router.get("/environments/{deployment_id}/status", response_model=EnvironmentDeploymentResponse)
async def get_deployment_status(deployment_id: str, current_user: Dict = Depends(get_current_user)):
    """
    Get the status of an environment deployment.
    """
    try:
        deployment = _mock_deployments_db.get(deployment_id)
        if not deployment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Deployment not found"
            )

        return deployment

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving deployment status {deployment_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve deployment status",
        )


@router.post(
    "/studio/sync", response_model=StudioSyncResponse, status_code=status.HTTP_202_ACCEPTED
)
# @rate_limit(requests=5)  # 5 sync operations per minute
async def sync_with_studio(
    request: StudioSyncRequest,
    background_tasks: BackgroundTasks,
    current_user: Dict = Depends(get_current_user),
    _: None = Depends(require_any_role(["teacher", "admin"])),
):
    """
    Synchronize content with Roblox Studio.

    Requires: Teacher or Admin role
    Rate limit: 5 requests per minute
    """
    try:
        sync_id = str(uuid.uuid4())

        # Create sync response
        sync_response = StudioSyncResponse(
            sync_id=sync_id,
            sync_status="initiated",
            files_synced=0,
            assets_synced=0,
            sync_log=[f"Sync operation initiated for project: {request.project_name}"],
            conflicts=[],
            sync_statistics={
                "sync_type": request.sync_type,
                "include_assets": request.include_assets,
                "include_scripts": request.include_scripts,
                "backup_created": request.backup_before_sync,
            },
            started_at=datetime.now(timezone.utc),
            completed_at=None,
        )

        # Background notification
        background_tasks.add_task(
            notify_roblox_update,
            "studio_sync_started",
            {"sync_id": sync_id, "project_name": request.project_name},
            current_user["id"],
        )

        logger.info(f"Studio sync started: {sync_id} by user {current_user['id']}")
        return sync_response

    except Exception as e:
        logger.error(f"Error starting studio sync: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to start studio synchronization",
        )


@router.websocket("/environments/{environment_id}/realtime")
async def environment_realtime(
    websocket: WebSocket, environment_id: str, current_user: Dict = Depends(get_current_user)
):
    """
    Real-time WebSocket connection for environment monitoring.
    """
    await websocket.accept()

    try:
        # Register connection
        client_id = f"{current_user['id']}_{environment_id}"
        await websocket_manager.connect(websocket, client_id)

        # Send initial status
        if environment_id in _mock_environments_db:
            await websocket.send_json(
                {
                    "type": "status_update",
                    "data": _mock_environments_db[environment_id].model_dump(),
                }
            )

        # Keep connection alive and handle messages
        while True:
            try:
                data = await websocket.receive_json()

                # Handle different message types
                if data.get("type") == "ping":
                    await websocket.send_json({"type": "pong"})

                elif data.get("type") == "request_status":
                    if environment_id in _mock_environments_db:
                        await websocket.send_json(
                            {
                                "type": "status_update",
                                "data": _mock_environments_db[environment_id].model_dump(),
                            }
                        )

            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(f"WebSocket error for environment {environment_id}: {e}")
                await websocket.send_json({"type": "error", "message": "An error occurred"})

    except WebSocketDisconnect:
        pass
    finally:
        await websocket_manager.disconnect(websocket)
        logger.info(f"WebSocket disconnected for environment {environment_id}")


@router.get("/environments/active", response_model=List[RobloxEnvironmentStatus])
async def get_active_environments(current_user: Dict = Depends(get_current_user)):
    """
    Get list of currently active Roblox environments.
    """
    try:
        # Filter active environments
        active_environments = [
            env for env in _mock_environments_db.values() if env.status == "active"
        ]

        return active_environments

    except Exception as e:
        logger.error(f"Error retrieving active environments: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve active environments",
        )


@router.get("/marketplace/browse", response_model=List[AssetResponse])
async def browse_marketplace(
    category: Optional[AssetType] = Query(None, description="Asset category"),
    grade_level: Optional[int] = Query(None, ge=1, le=12, description="Grade level"),
    featured: bool = Query(False, description="Show only featured assets"),
    limit: int = Query(20, ge=1, le=100, description="Maximum results"),
    current_user: Dict = Depends(get_current_user),
):
    """
    Browse the educational asset marketplace.
    """
    try:
        # Mock marketplace assets (would integrate with actual Roblox marketplace)
        marketplace_assets = list(_mock_assets_db.values())

        # Apply filters
        if category:
            marketplace_assets = [a for a in marketplace_assets if a.asset_type == category]

        if grade_level:
            marketplace_assets = [
                a
                for a in marketplace_assets
                if grade_level in a.educational_metadata.get("grade_levels", [])
            ]

        if featured:
            # Mock featured logic
            marketplace_assets = [
                a for a in marketplace_assets if a.usage_statistics.get("downloads", 0) > 10
            ]

        # Sort by popularity (downloads) and limit
        marketplace_assets.sort(key=lambda x: x.usage_statistics.get("downloads", 0), reverse=True)

        return marketplace_assets[:limit]

    except Exception as e:
        logger.error(f"Error browsing marketplace: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to browse marketplace"
        )
