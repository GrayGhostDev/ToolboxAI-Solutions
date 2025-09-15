"""
Roblox Environment API Endpoints

Handles CRUD operations for Roblox environments and coordinates with
the AI agent service for generation and deployment.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from apps.backend.core.auth import get_current_user
from apps.backend.core.database import get_db
from apps.backend.models.schemas import User
from apps.backend.services.roblox_ai_agent import roblox_ai_agent
from apps.backend.services.pusher import trigger_event as pusher_trigger
from apps.backend.models.database import RobloxEnvironment
from sqlalchemy import select, and_

router = APIRouter()

class RobloxEnvironmentAPI:
    """API for managing Roblox environments"""

    @staticmethod
    async def create_environment(
        environment_data: Dict[str, Any],
        user: User,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Create a new Roblox environment"""
        try:
            # Generate IDs
            environment_id = str(uuid4())
            conversation_id = f"conv_{datetime.now(timezone.utc).timestamp()}_{environment_id[:8]}"

            # Create database record
            db_environment = RobloxEnvironment(
                id=environment_id,
                name=environment_data['spec']['environment_name'],
                theme=environment_data['spec']['theme'],
                map_type=environment_data['spec']['map_type'],
                spec=environment_data['spec'],
                status='draft',
                user_id=user.id,
                conversation_id=conversation_id,
                created_at=datetime.now(timezone.utc)
            )

            db.add(db_environment)
            await db.commit()
            await db.refresh(db_environment)

            return {
                "id": environment_id,
                "conversationId": conversation_id,
                "status": "created"
            }

        except Exception as e:
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create environment: {str(e)}"
            )

    @staticmethod
    async def get_user_environments(
        user: User,
        db: AsyncSession
    ) -> List[Dict[str, Any]]:
        """Get all environments for a user"""
        try:
            result = await db.execute(
                select(RobloxEnvironment).where(
                    RobloxEnvironment.user_id == user.id
                ).order_by(RobloxEnvironment.created_at.desc())
            )

            environments = result.scalars().all()

            return [
                {
                    "id": env.id,
                    "name": env.name,
                    "theme": env.theme,
                    "mapType": env.map_type,
                    "status": env.status,
                    "spec": env.spec,
                    "generatedAt": env.generated_at.isoformat() if env.generated_at else None,
                    "downloadUrl": env.download_url,
                    "previewUrl": env.preview_url,
                    "userId": env.user_id,
                    "conversationId": env.conversation_id
                }
                for env in environments
            ]

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to fetch environments: {str(e)}"
            )

    @staticmethod
    async def generate_environment(
        environment_id: str,
        user: User,
        db: AsyncSession
    ) -> Dict[str, str]:
        """Start environment generation"""
        try:
            # Get environment from database
            result = await db.execute(
                select(RobloxEnvironment).where(
                    and_(
                        RobloxEnvironment.id == environment_id,
                        RobloxEnvironment.user_id == user.id
                    )
                )
            )

            environment = result.scalar_one_or_none()
            if not environment:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Environment not found"
                )

            # Update status to generating
            environment.status = 'generating'
            environment.generation_started_at = datetime.now(timezone.utc)
            await db.commit()

            # Start AI generation
            request_id = await roblox_ai_agent.generate_environment(
                environment.conversation_id,
                environment.spec
            )

            return {
                "requestId": request_id,
                "status": "generation_started"
            }

        except HTTPException:
            raise
        except Exception as e:
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to start generation: {str(e)}"
            )

    @staticmethod
    async def deploy_environment(
        environment_id: str,
        user: User,
        db: AsyncSession
    ) -> Dict[str, str]:
        """Deploy environment to Roblox"""
        try:
            # Get environment
            result = await db.execute(
                select(RobloxEnvironment).where(
                    and_(
                        RobloxEnvironment.id == environment_id,
                        RobloxEnvironment.user_id == user.id,
                        RobloxEnvironment.status == 'ready'
                    )
                )
            )

            environment = result.scalar_one_or_none()
            if not environment:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Environment not found or not ready for deployment"
                )

            # Update status
            environment.status = 'deployed'
            environment.deployed_at = datetime.now(timezone.utc)
            await db.commit()

            # Notify via WebSocket
            await pusher_trigger(
                f"user-{user.id}",
                "roblox_environment_deployed",
                {
                    "environmentId": environment_id,
                    "status": "deployed"
                }
            )

            return {"status": "deployed"}

        except HTTPException:
            raise
        except Exception as e:
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to deploy environment: {str(e)}"
            )

    @staticmethod
    async def delete_environment(
        environment_id: str,
        user: User,
        db: AsyncSession
    ) -> Dict[str, str]:
        """Delete an environment"""
        try:
            # Get environment
            result = await db.execute(
                select(RobloxEnvironment).where(
                    and_(
                        RobloxEnvironment.id == environment_id,
                        RobloxEnvironment.user_id == user.id
                    )
                )
            )

            environment = result.scalar_one_or_none()
            if not environment:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Environment not found"
                )

            # Clear AI conversation
            if environment.conversation_id:
                roblox_ai_agent.clear_conversation(environment.conversation_id)

            # Delete from database
            await db.delete(environment)
            await db.commit()

            return {"status": "deleted"}

        except HTTPException:
            raise
        except Exception as e:
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to delete environment: {str(e)}"
            )

# Route definitions
api = RobloxEnvironmentAPI()

@router.get("/environments")
async def get_environments(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all environments for the current user"""
    return await api.get_user_environments(current_user, db)

@router.post("/environments")
async def create_environment(
    environment_data: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new Roblox environment"""
    return await api.create_environment(environment_data, current_user, db)

@router.post("/environments/{environment_id}/generate")
async def generate_environment(
    environment_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Start environment generation"""
    return await api.generate_environment(environment_id, current_user, db)

@router.post("/environments/{environment_id}/deploy")
async def deploy_environment(
    environment_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Deploy environment to Roblox"""
    return await api.deploy_environment(environment_id, current_user, db)

@router.delete("/environments/{environment_id}")
async def delete_environment(
    environment_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete an environment"""
    return await api.delete_environment(environment_id, current_user, db)
