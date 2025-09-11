"""
Roblox Studio Integration API for Dashboard
Handles communication between Roblox Studio plugin and the dashboard backend
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import asyncio
import json
import logging
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Depends, WebSocket, WebSocketDisconnect, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from pydantic import BaseModel, Field

from models import (
    User, Lesson, Quiz, StudentProgress, 
    RobloxContent, RobloxSession, AgentTask
)
from database import get_db
from auth import get_current_user, verify_token
from _utils import generate_response, log_activity

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/roblox", tags=["Roblox Integration"])
security = HTTPBearer()

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.studio_connections: Dict[str, Dict] = {}
    
    async def connect(self, websocket: WebSocket, client_id: str, client_type: str = "studio"):
        await websocket.accept()
        self.active_connections[client_id] = websocket
        self.studio_connections[client_id] = {
            "type": client_type,
            "connected_at": datetime.utcnow(),
            "websocket": websocket
        }
        logger.info(f"Client {client_id} ({client_type}) connected")
    
    def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            del self.active_connections[client_id]
        if client_id in self.studio_connections:
            del self.studio_connections[client_id]
        logger.info(f"Client {client_id} disconnected")
    
    async def send_personal_message(self, message: str, client_id: str):
        if client_id in self.active_connections:
            await self.active_connections[client_id].send_text(message)
    
    async def broadcast(self, message: str, exclude: Optional[str] = None):
        for client_id, connection in self.active_connections.items():
            if client_id != exclude:
                await connection.send_text(message)

manager = ConnectionManager()

# Pydantic models for requests/responses
class PluginAuthRequest(BaseModel):
    api_key: str
    studio_id: str
    place_id: int
    version: str = "1.0.0"

class PluginAuthResponse(BaseModel):
    access_token: str
    refresh_token: str
    expires_in: int
    user_id: str
    role: str
    organization_id: Optional[str]

class ContentGenerationRequest(BaseModel):
    lesson_id: Optional[str] = None
    subject: str
    grade_level: int
    objectives: List[str]
    environment_type: str = "classroom"
    include_quiz: bool = True
    include_terrain: bool = True
    metadata: Dict[str, Any] = Field(default_factory=dict)

class AgentTaskRequest(BaseModel):
    event_type: str
    config: Dict[str, Any]
    context: Dict[str, Any] = Field(default_factory=dict)
    priority: str = "medium"

class SessionRequest(BaseModel):
    lesson_id: str
    classroom_id: Optional[str]
    max_students: int = 30
    session_type: str = "interactive"

class ProgressUpdate(BaseModel):
    student_id: str
    lesson_id: str
    progress_percentage: float
    milestones_completed: List[str]
    time_spent: int
    interactions: Dict[str, Any]

class QuizSubmission(BaseModel):
    quiz_id: str
    student_id: str
    answers: List[Dict[str, Any]]
    score: float
    time_spent: int
    attempt_number: int = 1

# Authentication endpoints
@router.post("/auth/studio-login", response_model=PluginAuthResponse)
async def studio_login(
    request: PluginAuthRequest,
    db: AsyncSession = Depends(get_db)
):
    """Authenticate Roblox Studio plugin"""
    try:
        # Validate API key and studio ID
        # In production, check against database
        if not request.api_key:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API key"
            )
        
        # Generate tokens
        access_token = generate_token({
            "studio_id": request.studio_id,
            "place_id": request.place_id,
            "type": "studio_plugin"
        })
        
        refresh_token = generate_token({
            "studio_id": request.studio_id,
            "type": "refresh"
        }, expires_delta=timedelta(days=30))
        
        return PluginAuthResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=3600,
            user_id="studio_user",
            role="studio",
            organization_id=None
        )
    
    except Exception as e:
        logger.error(f"Studio login error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication failed"
        )

@router.post("/auth/refresh")
async def refresh_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
):
    """Refresh authentication token"""
    try:
        token = credentials.credentials
        payload = verify_token(token)
        
        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
        
        # Generate new access token
        access_token = generate_token({
            "studio_id": payload.get("studio_id"),
            "type": "studio_plugin"
        })
        
        return {
            "access_token": access_token,
            "expires_in": 3600
        }
    
    except Exception as e:
        logger.error(f"Token refresh error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token refresh failed"
        )

# Content generation endpoints
@router.post("/plugin/trigger-agents")
async def trigger_agent_pipeline(
    request: AgentTaskRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
):
    """Trigger agent pipeline for content generation"""
    try:
        # Verify token
        token_payload = verify_token(credentials.credentials)
        
        # Create agent task record
        task_id = str(uuid4())
        agent_task = AgentTask(
            id=task_id,
            event_type=request.event_type,
            config=request.config,
            context=request.context,
            priority=request.priority,
            status="pending",
            created_at=datetime.utcnow()
        )
        
        db.add(agent_task)
        await db.commit()
        
        # Trigger agent pipeline (integrate with ToolboxAI-Roblox-Environment)
        from agents.plugin_communication import trigger_agent_pipeline
        
        result = await trigger_agent_pipeline({
            "request_id": task_id,
            "event_type": request.event_type,
            "config": request.config,
            "context": request.context
        })
        
        # Update task status
        agent_task.status = "processing"
        agent_task.result = result
        await db.commit()
        
        # Broadcast to connected studios
        await manager.broadcast(json.dumps({
            "type": "agent_task_started",
            "task_id": task_id,
            "event_type": request.event_type
        }))
        
        return {
            "task_id": task_id,
            "status": "processing",
            "message": "Agent pipeline triggered successfully"
        }
    
    except Exception as e:
        logger.error(f"Agent pipeline error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to trigger agent pipeline: {str(e)}"
        )

@router.post("/content/generate")
async def generate_content(
    request: ContentGenerationRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
):
    """Generate educational content for Roblox"""
    try:
        # Verify token
        token_payload = verify_token(credentials.credentials)
        
        # Create or get lesson
        if request.lesson_id:
            lesson = await db.get(Lesson, request.lesson_id)
            if not lesson:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Lesson not found"
                )
        else:
            lesson = Lesson(
                id=str(uuid4()),
                title=f"{request.subject} Lesson",
                subject=request.subject,
                grade_level=request.grade_level,
                objectives=request.objectives,
                created_at=datetime.utcnow()
            )
            db.add(lesson)
            await db.commit()
        
        # Trigger content generation
        from agents.supervisor import SupervisorAgent
        supervisor = SupervisorAgent()
        
        result = await supervisor.handle_plugin_request({
            "request_id": str(uuid4()),
            "event_type": "content_generation",
            "config": {
                "lesson_id": lesson.id,
                "subject": request.subject,
                "grade_level": request.grade_level,
                "objectives": request.objectives,
                "environment_type": request.environment_type,
                "include_quiz": request.include_quiz,
                "include_terrain": request.include_terrain
            },
            "metadata": request.metadata
        })
        
        # Store generated content
        roblox_content = RobloxContent(
            id=str(uuid4()),
            lesson_id=lesson.id,
            content_type="generated",
            content_data=result,
            created_at=datetime.utcnow()
        )
        db.add(roblox_content)
        await db.commit()
        
        return {
            "lesson_id": lesson.id,
            "content_id": roblox_content.id,
            "status": "success",
            "content": result
        }
    
    except Exception as e:
        logger.error(f"Content generation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate content: {str(e)}"
        )

# Lesson management endpoints
@router.get("/lessons/{lesson_id}")
async def get_lesson(
    lesson_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
):
    """Get lesson details"""
    try:
        # Verify token
        token_payload = verify_token(credentials.credentials)
        
        # Get lesson with content
        lesson = await db.get(Lesson, lesson_id)
        if not lesson:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Lesson not found"
            )
        
        # Get associated Roblox content
        result = await db.execute(
            select(RobloxContent).where(RobloxContent.lesson_id == lesson_id)
        )
        roblox_content = result.scalars().all()
        
        return {
            "lesson": lesson.to_dict(),
            "roblox_content": [content.to_dict() for content in roblox_content]
        }
    
    except Exception as e:
        logger.error(f"Get lesson error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve lesson"
        )

@router.post("/lessons")
async def create_lesson(
    lesson_data: Dict[str, Any],
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
):
    """Create new lesson"""
    try:
        # Verify token
        token_payload = verify_token(credentials.credentials)
        
        lesson = Lesson(
            id=str(uuid4()),
            **lesson_data,
            created_at=datetime.utcnow()
        )
        db.add(lesson)
        await db.commit()
        
        return {
            "lesson_id": lesson.id,
            "status": "created"
        }
    
    except Exception as e:
        logger.error(f"Create lesson error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create lesson"
        )

# Session management endpoints
@router.post("/sessions")
async def start_session(
    request: SessionRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
):
    """Start a classroom session"""
    try:
        # Verify token
        token_payload = verify_token(credentials.credentials)
        
        session = RobloxSession(
            id=str(uuid4()),
            lesson_id=request.lesson_id,
            classroom_id=request.classroom_id,
            max_students=request.max_students,
            session_type=request.session_type,
            started_at=datetime.utcnow(),
            status="active"
        )
        db.add(session)
        await db.commit()
        
        # Broadcast session start
        await manager.broadcast(json.dumps({
            "type": "session_started",
            "session_id": session.id,
            "lesson_id": request.lesson_id
        }))
        
        return {
            "session_id": session.id,
            "status": "started"
        }
    
    except Exception as e:
        logger.error(f"Start session error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to start session"
        )

@router.put("/sessions/{session_id}/end")
async def end_session(
    session_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
):
    """End a classroom session"""
    try:
        # Verify token
        token_payload = verify_token(credentials.credentials)
        
        session = await db.get(RobloxSession, session_id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
        
        session.ended_at = datetime.utcnow()
        session.status = "completed"
        await db.commit()
        
        # Broadcast session end
        await manager.broadcast(json.dumps({
            "type": "session_ended",
            "session_id": session_id
        }))
        
        return {
            "session_id": session_id,
            "status": "ended"
        }
    
    except Exception as e:
        logger.error(f"End session error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to end session"
        )

# Progress tracking endpoints
@router.post("/progress/update")
async def update_progress(
    progress: ProgressUpdate,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
):
    """Update student progress"""
    try:
        # Verify token
        token_payload = verify_token(credentials.credentials)
        
        # Find or create progress record
        result = await db.execute(
            select(StudentProgress).where(
                StudentProgress.student_id == progress.student_id,
                StudentProgress.lesson_id == progress.lesson_id
            )
        )
        student_progress = result.scalar_one_or_none()
        
        if student_progress:
            student_progress.progress_percentage = progress.progress_percentage
            student_progress.milestones_completed = progress.milestones_completed
            student_progress.time_spent += progress.time_spent
            student_progress.last_updated = datetime.utcnow()
        else:
            student_progress = StudentProgress(
                id=str(uuid4()),
                student_id=progress.student_id,
                lesson_id=progress.lesson_id,
                progress_percentage=progress.progress_percentage,
                milestones_completed=progress.milestones_completed,
                time_spent=progress.time_spent,
                interactions=progress.interactions,
                created_at=datetime.utcnow(),
                last_updated=datetime.utcnow()
            )
            db.add(student_progress)
        
        await db.commit()
        
        return {
            "status": "updated",
            "progress_id": student_progress.id
        }
    
    except Exception as e:
        logger.error(f"Update progress error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update progress"
        )

@router.post("/quiz/submit")
async def submit_quiz(
    submission: QuizSubmission,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
):
    """Submit quiz results"""
    try:
        # Verify token
        token_payload = verify_token(credentials.credentials)
        
        # Store quiz submission
        # This would integrate with your quiz tracking system
        
        return {
            "status": "submitted",
            "score": submission.score,
            "feedback": "Quiz submitted successfully"
        }
    
    except Exception as e:
        logger.error(f"Submit quiz error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to submit quiz"
        )

# WebSocket endpoint for real-time communication
@router.websocket("/ws/{client_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    client_id: str,
    db: AsyncSession = Depends(get_db)
):
    """WebSocket endpoint for real-time Roblox Studio communication"""
    await manager.connect(websocket, client_id)
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Handle different message types
            if message["type"] == "ping":
                await manager.send_personal_message(
                    json.dumps({"type": "pong"}),
                    client_id
                )
            
            elif message["type"] == "content_request":
                # Handle content request
                await handle_content_request(message, client_id, db)
            
            elif message["type"] == "progress_update":
                # Handle progress update
                await handle_progress_update(message, client_id, db)
            
            elif message["type"] == "session_event":
                # Broadcast session event to all connected clients
                await manager.broadcast(data, exclude=client_id)
            
    except WebSocketDisconnect:
        manager.disconnect(client_id)
        await manager.broadcast(json.dumps({
            "type": "client_disconnected",
            "client_id": client_id
        }))
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(client_id)

# Helper functions
async def handle_content_request(message: Dict, client_id: str, db: AsyncSession):
    """Handle content request from Roblox Studio"""
    try:
        lesson_id = message.get("lesson_id")
        
        if lesson_id:
            # Get lesson content
            lesson = await db.get(Lesson, lesson_id)
            if lesson:
                await manager.send_personal_message(
                    json.dumps({
                        "type": "content_response",
                        "lesson": lesson.to_dict()
                    }),
                    client_id
                )
    except Exception as e:
        logger.error(f"Content request error: {e}")

async def handle_progress_update(message: Dict, client_id: str, db: AsyncSession):
    """Handle progress update from Roblox Studio"""
    try:
        # Update progress in database
        progress_data = message.get("progress")
        if progress_data:
            # Process progress update
            pass
    except Exception as e:
        logger.error(f"Progress update error: {e}")

def generate_token(payload: Dict, expires_delta: timedelta = timedelta(hours=1)) -> str:
    """Generate JWT token"""
    import jwt
    from datetime import datetime
    
    expire = datetime.utcnow() + expires_delta
    payload["exp"] = expire
    
    return jwt.encode(payload, "your-secret-key", algorithm="HS256")

# Export router
__all__ = ["router"]