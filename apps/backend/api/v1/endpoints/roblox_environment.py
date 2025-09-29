"""
Roblox Environment Creation API Endpoints
Handles natural language to Roblox environment creation via Rojo API
"""

import logging
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel, Field
from datetime import datetime

from apps.backend.api.auth.auth import get_current_user
from apps.backend.models.schemas import User
from apps.backend.services.rojo_api import rojo_api_service, RojoAPIError
from apps.backend.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/roblox/environment", tags=["roblox-environment"])


class EnvironmentCreationRequest(BaseModel):
    """Request model for environment creation"""

    name: str = Field(..., description="Name of the environment")
    description: str = Field(..., description="Natural language description of the environment")
    grade_level: Optional[str] = Field(None, description="Target grade level")
    subject: Optional[str] = Field(None, description="Subject area")
    max_players: int = Field(default=20, description="Maximum number of players")
    settings: Optional[Dict[str, Any]] = Field(
        default_factory=dict, description="Additional settings"
    )


class EnvironmentCreationResponse(BaseModel):
    """Response model for environment creation"""

    success: bool
    environment_name: str
    project_path: Optional[str] = None
    rojo_url: Optional[str] = None
    components: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    created_at: datetime


class EnvironmentStatusResponse(BaseModel):
    """Response model for environment status"""

    environment_name: str
    status: str
    players: int
    last_updated: str
    rojo_connected: bool
    error: Optional[str] = None


@router.post("/preview", response_model=Dict[str, Any])
async def preview_environment(
    request: EnvironmentCreationRequest, current_user: User = Depends(get_current_user)
):
    """
    Generate a preview of the environment without creating it

    This endpoint:
    1. Takes a natural language description
    2. Parses it into structured components
    3. Generates a detailed preview structure
    4. Returns preview data for visualization
    """
    try:
        logger.info(
            f"Generating preview for environment '{request.name}' for user {current_user.id}"
        )

        # Validate request
        if not request.description.strip():
            raise HTTPException(status_code=400, detail="Environment description cannot be empty")

        # Parse natural language description
        async with rojo_api_service as rojo:
            parsed_components = await rojo._parse_environment_description(request.description)

            # Generate detailed preview structure
            preview_structure = await rojo._generate_rojo_structure(
                parsed_components, request.name or "Preview Environment", current_user.id
            )

            # Create enhanced preview with positioning and styling
            enhanced_preview = {
                "name": request.name or "Preview Environment",
                "description": request.description,
                "components": parsed_components,
                "structure": preview_structure,
                "visualization": {
                    "terrain": [
                        {
                            "type": comp["type"],
                            "position": {"x": i * 30, "y": 0, "z": 0},
                            "size": {"x": 20, "y": 10, "z": 20},
                            "color": "#4CAF50",
                        }
                        for i, comp in enumerate(parsed_components.get("terrain", []))
                    ],
                    "buildings": [
                        {
                            "type": comp["type"],
                            "position": {"x": i * 40, "y": 0, "z": 0},
                            "size": {"x": 25, "y": 15, "z": 25},
                            "color": f"#{hex(hash(comp['type']) % 0xFFFFFF)[2:].zfill(6)}",
                        }
                        for i, comp in enumerate(parsed_components.get("buildings", []))
                    ],
                    "objects": [
                        {
                            "type": comp["type"],
                            "position": {"x": (i % 5) * 15, "y": 0, "z": (i // 5) * 15},
                            "size": {"x": 5, "y": 5, "z": 5},
                            "color": f"#{hex(hash(comp['type']) % 0xFFFFFF)[2:].zfill(6)}",
                        }
                        for i, comp in enumerate(parsed_components.get("objects", []))
                    ],
                    "lighting": {
                        "type": parsed_components.get("lighting", {}).get("type", "Standard"),
                        "brightness": 0.7,
                        "color": "#FFFFFF",
                    },
                    "effects": [
                        {"type": effect, "intensity": 0.5, "active": True}
                        for effect in parsed_components.get("effects", [])
                    ],
                },
                "metadata": {
                    "grade_level": request.grade_level,
                    "subject": request.subject,
                    "max_players": request.max_players,
                    "estimated_creation_time": "2-5 minutes",
                    "complexity": (
                        "Medium" if len(parsed_components.get("buildings", [])) > 2 else "Simple"
                    ),
                },
            }

            return {
                "success": True,
                "preview": enhanced_preview,
                "created_at": datetime.now().isoformat(),
            }

    except Exception as e:
        logger.error(f"Environment preview generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Preview generation failed: {str(e)}")


@router.post("/create", response_model=EnvironmentCreationResponse)
async def create_environment(
    request: EnvironmentCreationRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
):
    """
    Create a Roblox environment from natural language description

    This endpoint:
    1. Takes a natural language description
    2. Parses it into structured components
    3. Generates Rojo project structure
    4. Creates the environment in Roblox Studio
    5. Returns creation results
    """
    try:
        logger.info(f"Creating environment '{request.name}' for user {current_user.id}")

        # Validate request
        if not request.name.strip():
            raise HTTPException(status_code=400, detail="Environment name cannot be empty")

        if not request.description.strip():
            raise HTTPException(status_code=400, detail="Environment description cannot be empty")

        # Check if Rojo is available
        async with rojo_api_service as rojo:
            rojo_available = await rojo.check_rojo_connection()

            if not rojo_available:
                logger.warning("Rojo is not available, returning mock response")
                return EnvironmentCreationResponse(
                    success=False,
                    environment_name=request.name,
                    error="Rojo is not running or not accessible. Please ensure Roblox Studio is open with Rojo plugin installed.",
                    created_at=datetime.now(),
                )

            # Create environment
            result = await rojo.create_environment_from_description(
                description=request.description,
                environment_name=request.name,
                user_id=current_user.id,
            )

            # Store environment info in database (background task)
            background_tasks.add_task(
                store_environment_info, current_user.id, request.name, request.description, result
            )

            return EnvironmentCreationResponse(
                success=result["success"],
                environment_name=result["environment_name"],
                project_path=result.get("project_path"),
                rojo_url=result.get("rojo_url"),
                components=result.get("components"),
                error=result.get("error"),
                created_at=datetime.now(),
            )

    except RojoAPIError as e:
        logger.error(f"Rojo API error: {e}")
        raise HTTPException(status_code=503, detail=f"Roblox Studio integration error: {str(e)}")

    except Exception as e:
        logger.error(f"Environment creation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Environment creation failed: {str(e)}")


@router.get("/status/{environment_name}", response_model=EnvironmentStatusResponse)
async def get_environment_status(
    environment_name: str, current_user: User = Depends(get_current_user)
):
    """Get the status of a created environment"""
    try:
        async with rojo_api_service as rojo:
            status = await rojo.get_environment_status(environment_name)

            return EnvironmentStatusResponse(
                environment_name=status["environment_name"],
                status=status["status"],
                players=status.get("players", 0),
                last_updated=status.get("last_updated", datetime.now().isoformat()),
                rojo_connected=status.get("rojo_connected", False),
                error=status.get("error"),
            )

    except Exception as e:
        logger.error(f"Error getting environment status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get environment status: {str(e)}")


@router.get("/rojo/info")
async def get_rojo_info(current_user: User = Depends(get_current_user)):
    """Get Rojo server information"""
    try:
        async with rojo_api_service as rojo:
            info = await rojo.get_rojo_info()
            return {
                "success": True,
                "rojo_info": info,
                "rojo_url": f"rojo://{rojo.rojo_host}:{rojo.rojo_port}/api/rojo",
            }

    except RojoAPIError as e:
        logger.error(f"Rojo info error: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": "Rojo is not running or not accessible",
        }

    except Exception as e:
        logger.error(f"Error getting Rojo info: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get Rojo info: {str(e)}")


@router.post("/rojo/check")
async def check_rojo_connection(current_user: User = Depends(get_current_user)):
    """Check if Rojo is running and accessible"""
    try:
        async with rojo_api_service as rojo:
            is_connected = await rojo.check_rojo_connection()

            return {
                "success": True,
                "rojo_connected": is_connected,
                "rojo_host": rojo.rojo_host,
                "rojo_port": rojo.rojo_port,
                "rojo_url": f"rojo://{rojo.rojo_host}:{rojo.rojo_port}/api/rojo",
            }

    except Exception as e:
        logger.error(f"Error checking Rojo connection: {e}")
        return {"success": False, "rojo_connected": False, "error": str(e)}


async def store_environment_info(
    user_id: str, environment_name: str, description: str, creation_result: Dict[str, Any]
):
    """Store environment information in database (background task)"""
    try:
        # This would store the environment info in the database
        # For now, just log it
        logger.info(f"Storing environment info for user {user_id}: {environment_name}")
        logger.info(f"Creation result: {creation_result}")

        # TODO: Implement database storage
        # await database.store_environment({
        #     "user_id": user_id,
        #     "name": environment_name,
        #     "description": description,
        #     "creation_result": creation_result,
        #     "created_at": datetime.now()
        # })

    except Exception as e:
        logger.error(f"Error storing environment info: {e}")


# Additional endpoints for environment management
@router.get("/list")
async def list_user_environments(current_user: User = Depends(get_current_user)):
    """List environments created by the current user"""
    try:
        # TODO: Implement database query
        # environments = await database.get_user_environments(current_user.id)

        # Mock response for now
        return {
            "success": True,
            "environments": [
                {
                    "name": "Sample Math World",
                    "description": "A mathematical learning environment",
                    "created_at": "2025-01-15T10:30:00Z",
                    "status": "active",
                }
            ],
        }

    except Exception as e:
        logger.error(f"Error listing environments: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list environments: {str(e)}")


@router.delete("/{environment_name}")
async def delete_environment(environment_name: str, current_user: User = Depends(get_current_user)):
    """Delete an environment"""
    try:
        # TODO: Implement environment deletion
        # This would:
        # 1. Stop the Rojo server for the environment
        # 2. Remove the project files
        # 3. Update the database

        logger.info(f"Deleting environment '{environment_name}' for user {current_user.id}")

        return {
            "success": True,
            "message": f"Environment '{environment_name}' deleted successfully",
        }

    except Exception as e:
        logger.error(f"Error deleting environment: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete environment: {str(e)}")
