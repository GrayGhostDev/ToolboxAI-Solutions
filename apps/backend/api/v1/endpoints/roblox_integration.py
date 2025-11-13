"""
Roblox Integration API Endpoints
Complete integration with OAuth2, Open Cloud, Rojo, and Conversation Flow
"""

import logging
import secrets
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, Field

from apps.backend.api.auth.auth import get_current_user
from apps.backend.core.prompts.enhanced_conversation_flow import (
    enhanced_conversation_flow,
)
from apps.backend.models.schemas import User
from apps.backend.services.pusher_realtime import pusher_service
from apps.backend.services.roblox.auth import roblox_auth_service
from apps.backend.services.roblox.open_cloud import (
    AssetDescription,
    AssetType,
    CreationContext,
    DataStoreEntry,
    MessagingServiceMessage,
    open_cloud_client,
)
from apps.backend.services.roblox.rojo_manager import rojo_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/roblox", tags=["roblox-integration"])

# ==================== Request/Response Models ====================


class ConversationStartRequest(BaseModel):
    """Request to start a new conversation"""

    initial_message: str | None = Field(None, description="Initial user message")
    metadata: dict[str, Any] | None = Field(default_factory=dict)


class ConversationInputRequest(BaseModel):
    """Request to process conversation input"""

    session_id: str
    user_input: str


class RobloxAuthRequest(BaseModel):
    """Request for Roblox OAuth2 authentication"""

    additional_scopes: list[str] | None = Field(default_factory=list)


class AssetUploadRequest(BaseModel):
    """Request to upload asset to Roblox"""

    asset_type: AssetType
    display_name: str
    description: str
    file_content_base64: str  # Base64 encoded file content


class DataStoreRequest(BaseModel):
    """Request for DataStore operations"""

    universe_id: str
    datastore_name: str
    key: str
    value: Any
    metadata: dict[str, Any] | None = None


class MessagePublishRequest(BaseModel):
    """Request to publish message to Universe Messaging Service"""

    universe_id: str
    topic: str
    message: dict[str, Any]


# ==================== OAuth2 Endpoints ====================


@router.post("/auth/initiate")
async def initiate_roblox_auth(
    request: RobloxAuthRequest, current_user: User = Depends(get_current_user)
):
    """
    Initiate Roblox OAuth2 authentication flow

    Returns authorization URL for user to authenticate with Roblox
    """
    try:
        auth_data = roblox_auth_service.generate_authorization_url(
            user_id=current_user.id, additional_scopes=request.additional_scopes
        )

        return {
            "success": True,
            "authorization_url": auth_data["authorization_url"],
            "state": auth_data["state"],
            "expires_at": auth_data["expires_at"],
        }

    except Exception as e:
        logger.error(f"Error initiating Roblox auth: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/oauth/callback")
async def roblox_oauth_callback(
    code: str = Query(..., description="Authorization code from Roblox"),
    state: str = Query(..., description="State parameter for CSRF protection"),
):
    """
    OAuth2 callback endpoint for Roblox authentication

    Exchanges authorization code for access token
    """
    try:
        async with roblox_auth_service as auth:
            # Exchange code for token
            token = await auth.exchange_code_for_token(code, state)

            # Get user info
            user_info = await auth.get_user_info(token.access_token)

            # Broadcast successful auth via Pusher
            await pusher_service.broadcast_event(
                "roblox-auth",
                "authentication_complete",
                {"roblox_user_id": user_info.sub, "username": user_info.preferred_username},
            )

            # Redirect to dashboard with success
            return RedirectResponse(
                url=f"/dashboard?auth=success&roblox_id={user_info.sub}", status_code=302
            )

    except ValueError as e:
        logger.error(f"OAuth callback error: {e}")
        return RedirectResponse(url=f"/dashboard?auth=error&message={str(e)}", status_code=302)


@router.post("/auth/refresh")
async def refresh_roblox_token(current_user: User = Depends(get_current_user)):
    """Refresh Roblox access token"""
    try:
        async with roblox_auth_service as auth:
            new_token = await auth.refresh_access_token(current_user.id)

            return {
                "success": True,
                "access_token": new_token.access_token,
                "expires_in": new_token.expires_in,
            }

    except Exception as e:
        logger.error(f"Error refreshing token: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/auth/revoke")
async def revoke_roblox_token(current_user: User = Depends(get_current_user)):
    """Revoke Roblox authentication tokens"""
    try:
        async with roblox_auth_service as auth:
            success = await auth.revoke_token(current_user.id)

            return {
                "success": success,
                "message": "Tokens revoked successfully" if success else "Failed to revoke tokens",
            }

    except Exception as e:
        logger.error(f"Error revoking token: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Conversation Flow Endpoints ====================


@router.post("/conversation/start")
async def start_conversation(
    request: ConversationStartRequest, current_user: User = Depends(get_current_user)
):
    """Start a new educational content conversation"""
    try:
        session_id = secrets.token_urlsafe(16)

        # Start conversation
        context = await enhanced_conversation_flow.start_conversation(
            user_id=current_user.id, session_id=session_id
        )

        # Process initial message if provided
        result = None
        if request.initial_message:
            result = await enhanced_conversation_flow.process_input(
                session_id=session_id, user_input=request.initial_message
            )

        return {
            "success": True,
            "session_id": session_id,
            "current_stage": context.current_stage.value,
            "pusher_channel": f"conversation-{session_id}",
            "initial_result": result,
        }

    except Exception as e:
        logger.error(f"Error starting conversation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/conversation/input")
async def process_conversation_input(
    request: ConversationInputRequest, current_user: User = Depends(get_current_user)
):
    """Process user input in conversation"""
    try:
        result = await enhanced_conversation_flow.process_input(
            session_id=request.session_id, user_input=request.user_input
        )

        return {"success": True, "result": result}

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error processing conversation input: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/conversation/advance")
async def advance_conversation_stage(
    session_id: str, current_user: User = Depends(get_current_user)
):
    """Advance to next conversation stage"""
    try:
        context = await enhanced_conversation_flow.advance_stage(session_id)

        return {
            "success": True,
            "current_stage": context.current_stage.value,
            "progress": (len(context.stage_data) / 8) * 100,
        }

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error advancing stage: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/conversation/generate")
async def generate_roblox_environment(
    session_id: str,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
):
    """Generate Roblox environment from conversation"""
    try:
        result = await enhanced_conversation_flow.generate_roblox_environment(session_id)

        # Background task to upload assets
        background_tasks.add_task(
            upload_generated_assets, session_id, result["project_id"], current_user.id
        )

        return {
            "success": True,
            "generation_result": result,
            "rojo_connect_url": f"http://localhost:{result['rojo_port']}/api/rojo",
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error generating environment: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Rojo Management Endpoints ====================


@router.get("/rojo/check")
async def check_rojo_installation(current_user: User = Depends(get_current_user)):
    """Check if Rojo is installed and accessible"""
    try:
        async with rojo_manager as manager:
            installed = await manager.check_rojo_installed()

            return {
                "success": True,
                "rojo_installed": installed,
                "base_port": manager.base_port,
                "max_projects": manager.max_projects,
            }

    except Exception as e:
        logger.error(f"Error checking Rojo: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/rojo/projects")
async def list_rojo_projects(current_user: User = Depends(get_current_user)):
    """List all Rojo projects for current user"""
    try:
        async with rojo_manager as manager:
            projects = await manager.list_projects(current_user.id)

            return {
                "success": True,
                "projects": [p.dict() for p in projects],
                "count": len(projects),
            }

    except Exception as e:
        logger.error(f"Error listing projects: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/rojo/project/{project_id}")
async def get_rojo_project(project_id: str, current_user: User = Depends(get_current_user)):
    """Get details of a specific Rojo project"""
    try:
        async with rojo_manager as manager:
            project = await manager.get_project(project_id)

            if not project:
                raise HTTPException(status_code=404, detail="Project not found")

            # Get sync status if running
            sync_status = None
            if project.status == "running":
                sync_status = await manager.get_sync_status(project_id)

            return {
                "success": True,
                "project": project.dict(),
                "sync_status": sync_status.dict() if sync_status else None,
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting project: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/rojo/project/{project_id}/start")
async def start_rojo_project(project_id: str, current_user: User = Depends(get_current_user)):
    """Start Rojo server for a project"""
    try:
        async with rojo_manager as manager:
            sync_status = await manager.start_project(project_id)

            return {
                "success": True,
                "sync_status": sync_status.dict(),
                "connect_url": f"http://localhost:{sync_status.port}/api/rojo",
            }

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error starting project: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/rojo/project/{project_id}/stop")
async def stop_rojo_project(project_id: str, current_user: User = Depends(get_current_user)):
    """Stop Rojo server for a project"""
    try:
        async with rojo_manager as manager:
            success = await manager.stop_project(project_id)

            return {
                "success": success,
                "message": "Project stopped" if success else "Failed to stop project",
            }

    except Exception as e:
        logger.error(f"Error stopping project: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/rojo/project/{project_id}/build")
async def build_rojo_project(project_id: str, current_user: User = Depends(get_current_user)):
    """Build Rojo project to .rbxl file"""
    try:
        async with rojo_manager as manager:
            output_path = await manager.build_project(project_id)

            return {
                "success": True,
                "output_path": str(output_path),
                "file_size": output_path.stat().st_size,
            }

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error building project: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/rojo/project/{project_id}")
async def delete_rojo_project(project_id: str, current_user: User = Depends(get_current_user)):
    """Delete a Rojo project"""
    try:
        async with rojo_manager as manager:
            success = await manager.delete_project(project_id)

            return {
                "success": success,
                "message": "Project deleted" if success else "Project not found",
            }

    except Exception as e:
        logger.error(f"Error deleting project: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Open Cloud API Endpoints ====================


@router.post("/assets/upload")
async def upload_asset(request: AssetUploadRequest, current_user: User = Depends(get_current_user)):
    """Upload asset to Roblox via Open Cloud API"""
    try:
        # Get Roblox user info
        token = roblox_auth_service.get_stored_token(current_user.id)
        if not token:
            raise HTTPException(status_code=401, detail="Roblox authentication required")

        # Decode base64 content
        import base64

        file_content = base64.b64decode(request.file_content_base64)

        # Create asset description
        asset_desc = AssetDescription(
            asset_type=request.asset_type,
            display_name=request.display_name,
            description=request.description,
            creation_context=CreationContext(
                creator_type="User", creator_id=current_user.id  # Should be Roblox user ID
            ),
        )

        async with open_cloud_client as client:
            result = await client.create_asset(asset_desc, file_content)

            return {
                "success": True,
                "asset_id": result.get("assetId"),
                "asset_url": result.get("assetUrl"),
            }

    except Exception as e:
        logger.error(f"Error uploading asset: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/assets/{asset_id}")
async def get_asset(asset_id: str, current_user: User = Depends(get_current_user)):
    """Get asset information from Roblox"""
    try:
        async with open_cloud_client as client:
            asset = await client.get_asset(asset_id)

            return {"success": True, "asset": asset}

    except Exception as e:
        logger.error(f"Error getting asset: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/datastore/set")
async def set_datastore_entry(
    request: DataStoreRequest, current_user: User = Depends(get_current_user)
):
    """Set entry in Roblox DataStore"""
    try:
        entry = DataStoreEntry(
            key=request.key,
            value=request.value,
            metadata=request.metadata,
            user_ids=[current_user.id],
        )

        async with open_cloud_client as client:
            result = await client.set_datastore_entry(
                request.universe_id, request.datastore_name, entry
            )

            return {"success": True, "result": result}

    except Exception as e:
        logger.error(f"Error setting datastore entry: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/datastore/get")
async def get_datastore_entry(
    universe_id: str, datastore_name: str, key: str, current_user: User = Depends(get_current_user)
):
    """Get entry from Roblox DataStore"""
    try:
        async with open_cloud_client as client:
            entry = await client.get_datastore_entry(universe_id, datastore_name, key)

            if not entry:
                raise HTTPException(status_code=404, detail="Entry not found")

            return {"success": True, "entry": entry.dict()}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting datastore entry: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/messaging/publish")
async def publish_message(
    request: MessagePublishRequest, current_user: User = Depends(get_current_user)
):
    """Publish message to Universe Messaging Service"""
    try:
        message = MessagingServiceMessage(topic=request.topic, message=request.message)

        async with open_cloud_client as client:
            result = await client.publish_message(request.universe_id, message)

            return {"success": True, "result": result}

    except Exception as e:
        logger.error(f"Error publishing message: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Helper Functions ====================


async def upload_generated_assets(session_id: str, project_id: str, user_id: str):
    """Background task to upload generated assets to Roblox"""
    try:
        logger.info(f"Starting asset upload for session {session_id}")

        # Get project files
        async with rojo_manager as manager:
            files = await manager.get_project_files(project_id)

        # Upload each script as an asset
        async with open_cloud_client as client:
            for file_path, content in files.items():
                if file_path.endswith(".lua"):
                    asset_desc = AssetDescription(
                        asset_type=AssetType.MODEL,
                        display_name=file_path.replace("/", "_"),
                        description=f"Generated script from session {session_id}",
                        creation_context=CreationContext(creator_type="User", creator_id=user_id),
                    )

                    await client.create_asset(asset_desc, content.encode("utf-8"))

        # Notify via Pusher
        await pusher_service.broadcast_event(
            f"conversation-{session_id}",
            "assets_uploaded",
            {"project_id": project_id, "file_count": len(files)},
        )

        logger.info(f"Asset upload complete for session {session_id}")

    except Exception as e:
        logger.error(f"Error uploading assets: {e}")
        await pusher_service.broadcast_event(
            f"conversation-{session_id}", "asset_upload_failed", {"error": str(e)}
        )
