"""
Pydantic Schemas for Roblox API Integration
Defines request/response models with validation
"""

from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field, field_validator, ConfigDict
import re


# ============================================
# Enums
# ============================================

class OAuth2ResponseType(str, Enum):
    """OAuth2 response types"""
    CODE = "code"
    TOKEN = "token"


class OAuth2GrantType(str, Enum):
    """OAuth2 grant types"""
    AUTHORIZATION_CODE = "authorization_code"
    REFRESH_TOKEN = "refresh_token"
    CLIENT_CREDENTIALS = "client_credentials"


class RojoProjectStatus(str, Enum):
    """Rojo project status"""
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    ERROR = "error"
    STOPPING = "stopping"


class ConversationStage(str, Enum):
    """8-stage conversation flow stages"""
    GREETING = "greeting"
    DISCOVERY = "discovery"
    REQUIREMENTS = "requirements"
    PERSONALIZATION = "personalization"
    DESIGN = "design"
    UNIQUENESS = "uniqueness"
    VALIDATION = "validation"
    GENERATION = "generation"
    COMPLETE = "complete"


class AssetType(str, Enum):
    """Roblox asset types"""
    MODEL = "Model"
    SCRIPT = "Script"
    LOCAL_SCRIPT = "LocalScript"
    MODULE_SCRIPT = "ModuleScript"
    SOUND = "Sound"
    IMAGE = "Image"
    MESH = "Mesh"
    ANIMATION = "Animation"


# ============================================
# OAuth2 Schemas
# ============================================

class OAuth2InitiateRequest(BaseModel):
    """Request to initiate OAuth2 flow"""
    redirect_uri: Optional[str] = Field(
        default="http://127.0.0.1:8009/api/v1/roblox/auth/callback",
        description="OAuth2 redirect URI"
    )
    scopes: Optional[List[str]] = Field(
        default=["openid", "profile", "asset:read", "asset:write"],
        description="OAuth2 scopes to request"
    )
    state: Optional[str] = Field(
        default=None,
        description="OAuth2 state parameter for CSRF protection"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "redirect_uri": "http://127.0.0.1:8009/api/v1/roblox/auth/callback",
                "scopes": ["openid", "profile", "asset:read", "asset:write"]
            }
        }
    )


class OAuth2InitiateResponse(BaseModel):
    """Response with OAuth2 authorization URL"""
    authorization_url: str = Field(description="URL to redirect user for authorization")
    state: str = Field(description="State parameter for CSRF validation")
    code_verifier: Optional[str] = Field(
        default=None,
        description="PKCE code verifier (store securely)"
    )
    expires_at: datetime = Field(description="When the authorization request expires")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "authorization_url": "https://authorize.roblox.com/v1/authorize?...",
                "state": "random_state_string",
                "code_verifier": "pkce_verifier_string",
                "expires_at": "2024-01-01T00:05:00Z"
            }
        }
    )


class OAuth2CallbackRequest(BaseModel):
    """OAuth2 callback request"""
    code: str = Field(description="Authorization code from Roblox")
    state: str = Field(description="State parameter for CSRF validation")
    code_verifier: Optional[str] = Field(
        default=None,
        description="PKCE code verifier"
    )


class OAuth2TokenResponse(BaseModel):
    """OAuth2 token response"""
    access_token: str = Field(description="Access token for API calls")
    token_type: str = Field(default="Bearer", description="Token type")
    expires_in: int = Field(description="Token expiry in seconds")
    refresh_token: Optional[str] = Field(
        default=None,
        description="Refresh token for getting new access tokens"
    )
    scope: Optional[str] = Field(default=None, description="Granted scopes")
    id_token: Optional[str] = Field(
        default=None,
        description="OpenID Connect ID token"
    )


class OAuth2RefreshRequest(BaseModel):
    """Request to refresh OAuth2 token"""
    refresh_token: str = Field(description="Refresh token")


class OAuth2RevokeRequest(BaseModel):
    """Request to revoke OAuth2 token"""
    token: str = Field(description="Token to revoke")
    token_type_hint: Optional[str] = Field(
        default="access_token",
        description="Type of token (access_token or refresh_token)"
    )


# ============================================
# Conversation Flow Schemas
# ============================================

class ConversationStartRequest(BaseModel):
    """Request to start 8-stage conversation"""
    user_id: str = Field(description="User ID")
    initial_message: Optional[str] = Field(
        default=None,
        description="Optional initial message from user"
    )
    context: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional context for conversation"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "user_id": "user_123",
                "initial_message": "I want to create a math learning environment",
                "context": {"grade_level": 5, "subject": "math"}
            }
        }
    )


class ConversationStartResponse(BaseModel):
    """Response for conversation start"""
    session_id: str = Field(description="Unique session identifier")
    current_stage: ConversationStage = Field(description="Current conversation stage")
    message: str = Field(description="AI response message")
    pusher_channel: str = Field(description="Pusher channel for real-time updates")
    created_at: datetime = Field(description="Session creation time")


class ConversationInputRequest(BaseModel):
    """User input for conversation"""
    session_id: str = Field(description="Session ID")
    user_input: str = Field(description="User's response")
    metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional metadata"
    )


class ConversationAdvanceRequest(BaseModel):
    """Request to advance conversation stage"""
    session_id: str = Field(description="Session ID")
    skip_validation: bool = Field(
        default=False,
        description="Skip validation for current stage"
    )


class ConversationGenerateRequest(BaseModel):
    """Request to generate content"""
    session_id: str = Field(description="Session ID")
    output_format: Optional[str] = Field(
        default="roblox",
        description="Output format (roblox, unity, minecraft)"
    )
    include_scripts: bool = Field(
        default=True,
        description="Include generated scripts"
    )
    include_models: bool = Field(
        default=True,
        description="Include 3D models"
    )


class ConversationResponse(BaseModel):
    """Generic conversation response"""
    session_id: str = Field(description="Session ID")
    current_stage: ConversationStage = Field(description="Current stage")
    message: str = Field(description="AI response")
    progress: float = Field(
        ge=0, le=100,
        description="Overall progress percentage"
    )
    data: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Stage-specific data"
    )


# ============================================
# Rojo Management Schemas
# ============================================

class RojoCheckResponse(BaseModel):
    """Rojo installation check response"""
    installed: bool = Field(description="Is Rojo installed")
    version: Optional[str] = Field(default=None, description="Rojo version")
    path: Optional[str] = Field(default=None, description="Rojo binary path")


class RojoProjectCreate(BaseModel):
    """Request to create Rojo project"""
    name: str = Field(description="Project name")
    template: Optional[str] = Field(
        default="default",
        description="Project template"
    )
    port: Optional[int] = Field(
        default=None,
        description="Rojo server port (auto-assigned if not provided)"
    )

    @field_validator('name')
    def validate_name(cls, v):
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError('Project name must contain only alphanumeric characters, underscore, and hyphen')
        return v


class RojoProject(BaseModel):
    """Rojo project information"""
    project_id: str = Field(description="Project ID")
    name: str = Field(description="Project name")
    path: str = Field(description="Project path")
    port: int = Field(description="Rojo server port")
    status: RojoProjectStatus = Field(description="Project status")
    created_at: datetime = Field(description="Creation time")
    updated_at: datetime = Field(description="Last update time")
    user_id: str = Field(description="Owner user ID")
    session_id: Optional[str] = Field(
        default=None,
        description="Roblox Studio session ID"
    )
    process_pid: Optional[int] = Field(
        default=None,
        description="Rojo process PID"
    )


class RojoProjectList(BaseModel):
    """List of Rojo projects"""
    projects: List[RojoProject] = Field(description="List of projects")
    total: int = Field(description="Total number of projects")


class RojoBuildRequest(BaseModel):
    """Request to build Rojo project"""
    output_path: Optional[str] = Field(
        default=None,
        description="Output path for built file"
    )
    output_format: Optional[str] = Field(
        default="rbxm",
        description="Output format (rbxm, rbxmx)"
    )


class RojoSyncStatus(BaseModel):
    """Rojo sync status"""
    connected: bool = Field(description="Is connected to Studio")
    session_id: Optional[str] = Field(default=None, description="Session ID")
    project_name: Optional[str] = Field(default=None, description="Project name")
    client_count: int = Field(default=0, description="Number of connected clients")
    last_sync: Optional[datetime] = Field(default=None, description="Last sync time")
    errors: List[str] = Field(default_factory=list, description="Any errors")


# ============================================
# Open Cloud API Schemas
# ============================================

class AssetUploadRequest(BaseModel):
    """Request to upload asset to Roblox"""
    name: str = Field(description="Asset name")
    description: str = Field(description="Asset description")
    asset_type: AssetType = Field(description="Type of asset")
    content: str = Field(description="Asset content (base64 for binary)")
    metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional metadata"
    )

    @field_validator('name')
    def validate_name(cls, v):
        if len(v) > 50:
            raise ValueError('Asset name must be 50 characters or less')
        return v


class AssetUploadResponse(BaseModel):
    """Response for asset upload"""
    asset_id: str = Field(description="Roblox asset ID")
    asset_url: str = Field(description="Asset URL")
    version_id: str = Field(description="Asset version ID")
    created_at: datetime = Field(description="Upload time")


class DataStoreEntry(BaseModel):
    """DataStore entry"""
    key: str = Field(description="Entry key")
    value: Any = Field(description="Entry value")
    metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Entry metadata"
    )
    version: Optional[str] = Field(
        default=None,
        description="Entry version"
    )


class DataStoreSetRequest(BaseModel):
    """Request to set DataStore entry"""
    datastore_name: str = Field(description="DataStore name")
    key: str = Field(description="Entry key")
    value: Any = Field(description="Entry value")
    metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Entry metadata"
    )
    exclusive_create: bool = Field(
        default=False,
        description="Only create if doesn't exist"
    )

    @field_validator('key')
    def validate_key(cls, v):
        if len(v) > 50:
            raise ValueError('DataStore key must be 50 characters or less')
        return v


class DataStoreGetRequest(BaseModel):
    """Request to get DataStore entry"""
    datastore_name: str = Field(description="DataStore name")
    key: str = Field(description="Entry key")
    version: Optional[str] = Field(
        default=None,
        description="Specific version to retrieve"
    )


class MessagingPublishRequest(BaseModel):
    """Request to publish message"""
    topic: str = Field(description="Message topic")
    message: Dict[str, Any] = Field(description="Message data")
    universe_id: Optional[str] = Field(
        default=None,
        description="Target universe ID"
    )


# ============================================
# Pusher/WebSocket Schemas
# ============================================

class PusherAuthRequest(BaseModel):
    """Pusher channel authentication request"""
    socket_id: str = Field(description="Pusher socket ID")
    channel_name: str = Field(description="Channel to authenticate")
    user_id: Optional[str] = Field(
        default=None,
        description="User ID for presence channels"
    )


class PusherAuthResponse(BaseModel):
    """Pusher authentication response"""
    auth: str = Field(description="Authentication signature")
    channel_data: Optional[str] = Field(
        default=None,
        description="Channel data for presence channels"
    )


# ============================================
# Error Response
# ============================================

class ErrorResponse(BaseModel):
    """Standard error response"""
    error: str = Field(description="Error type")
    message: str = Field(description="Error message")
    details: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional error details"
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Error timestamp"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "error": "AUTHENTICATION_FAILED",
                "message": "Invalid OAuth2 state parameter",
                "details": {"provided_state": "abc123", "expected_state": "xyz789"},
                "timestamp": "2024-01-01T00:00:00Z"
            }
        }
    )