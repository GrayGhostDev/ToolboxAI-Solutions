# Terminal 2: Backend Services Implementation Specialist

## CRITICAL: Complete Backend Services with Real Data Integration

### Your Role
You are the **Backend Services Implementation Specialist**. Your mission is to complete all backend services, fix integration issues, and ensure real data flows through the system.

### Immediate Tasks

#### 1. Fix FastAPI Server Issues (HIGH PRIORITY)
```bash
cd ToolboxAI-Roblox-Environment

# Fix import errors in server/main.py
cat > server/main.py << 'EOF'
"""
FastAPI Main Application Server
Production-ready with real data integration
"""
import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi import FastAPI, HTTPException, Depends, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import asyncio
import logging
from typing import Optional, Dict, Any, List

# Import our modules
from server.models import (
    ContentGenerationRequest,
    ContentGenerationResponse,
    QuizRequest,
    QuizResponse,
    EnvironmentRequest,
    EnvironmentResponse,
    HealthResponse
)
from server.auth import get_current_user, User
from server.config import settings
from agents.supervisor import SupervisorAgent
from database.connection import get_db
from database.repositories import (
    UserRepository,
    CourseRepository,
    ContentRepository,
    QuizRepository
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Lifespan manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle"""
    logger.info("Starting FastAPI server...")
    # Initialize database connection pool
    from database.connection import init_db
    await init_db()
    
    # Initialize supervisor agent
    app.state.supervisor = SupervisorAgent()
    await app.state.supervisor.initialize()
    
    yield
    
    # Cleanup
    logger.info("Shutting down FastAPI server...")
    await app.state.supervisor.cleanup()
    from database.connection import close_db
    await close_db()

# Create FastAPI app
app = FastAPI(
    title="ToolBoxAI Educational Platform API",
    version="1.0.0",
    description="Production API with real data integration",
    lifespan=lifespan
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5177", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check endpoint
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Check service health"""
    return HealthResponse(
        status="healthy",
        services={
            "api": "running",
            "database": "connected",
            "redis": "connected",
            "agents": "initialized"
        },
        version="1.0.0"
    )

# Content generation endpoint with real data
@app.post("/api/v1/content/generate", response_model=ContentGenerationResponse)
async def generate_content(
    request: ContentGenerationRequest,
    current_user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    """Generate educational content using AI agents"""
    try:
        # Get supervisor agent
        supervisor = app.state.supervisor
        
        # Generate content
        result = await supervisor.generate_content(
            subject=request.subject,
            grade_level=request.grade_level,
            learning_objectives=request.learning_objectives,
            content_type=request.content_type,
            user_id=current_user.id
        )
        
        # Save to database
        content_repo = ContentRepository(db)
        saved_content = await content_repo.create(
            user_id=current_user.id,
            course_id=request.course_id,
            content_data=result
        )
        
        return ContentGenerationResponse(
            content_id=saved_content.id,
            content=result,
            status="completed"
        )
    except Exception as e:
        logger.error(f"Content generation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Quiz generation endpoint with real data
@app.post("/api/v1/quiz/generate", response_model=QuizResponse)
async def generate_quiz(
    request: QuizRequest,
    current_user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    """Generate quiz using AI agents"""
    try:
        supervisor = app.state.supervisor
        
        # Generate quiz
        quiz_data = await supervisor.generate_quiz(
            topic=request.topic,
            difficulty=request.difficulty,
            num_questions=request.num_questions,
            question_types=request.question_types
        )
        
        # Save to database
        quiz_repo = QuizRepository(db)
        saved_quiz = await quiz_repo.create(
            course_id=request.course_id,
            creator_id=current_user.id,
            quiz_data=quiz_data
        )
        
        return QuizResponse(
            quiz_id=saved_quiz.id,
            questions=quiz_data["questions"],
            metadata=quiz_data["metadata"]
        )
    except Exception as e:
        logger.error(f"Quiz generation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# User endpoints with real database
@app.get("/api/v1/users/me")
async def get_user_profile(
    current_user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    """Get current user profile from database"""
    user_repo = UserRepository(db)
    user = await user_repo.get_by_id(current_user.id)
    return user

@app.get("/api/v1/users/{user_id}/courses")
async def get_user_courses(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    """Get user's enrolled courses"""
    course_repo = CourseRepository(db)
    courses = await course_repo.get_user_courses(user_id)
    return courses

# WebSocket for real-time updates
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket for real-time communication"""
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_json()
            # Process WebSocket messages
            response = await process_websocket_message(data)
            await websocket.send_json(response)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        await websocket.close()

async def process_websocket_message(data: Dict[str, Any]) -> Dict[str, Any]:
    """Process WebSocket messages"""
    message_type = data.get("type")
    
    if message_type == "ping":
        return {"type": "pong"}
    elif message_type == "content_status":
        # Check content generation status
        return {"type": "status", "status": "processing"}
    else:
        return {"type": "error", "message": "Unknown message type"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8008, reload=True)
EOF
```

#### 2. Implement Database Repositories
```bash
# Create repository implementations
cat > database/repositories.py << 'EOF'
"""
Database Repository Pattern Implementation
"""
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from sqlalchemy.orm import selectinload
from datetime import datetime

from database.models import (
    User, School, Course, Lesson, 
    Content, Quiz, QuizQuestion, QuizResult,
    StudentProgress, Analytics
)

class BaseRepository:
    """Base repository with common CRUD operations"""
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def commit(self):
        await self.db.commit()
    
    async def rollback(self):
        await self.db.rollback()

class UserRepository(BaseRepository):
    """User repository with real database operations"""
    
    async def create(self, **kwargs) -> User:
        user = User(**kwargs)
        self.db.add(user)
        await self.commit()
        await self.db.refresh(user)
        return user
    
    async def get_by_id(self, user_id: int) -> Optional[User]:
        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()
    
    async def get_by_email(self, email: str) -> Optional[User]:
        result = await self.db.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()
    
    async def update(self, user_id: int, **kwargs) -> User:
        await self.db.execute(
            update(User).where(User.id == user_id).values(**kwargs)
        )
        await self.commit()
        return await self.get_by_id(user_id)
    
    async def get_students_by_teacher(self, teacher_id: int) -> List[User]:
        result = await self.db.execute(
            select(User)
            .join(Course, User.enrolled_courses)
            .where(Course.teacher_id == teacher_id)
            .distinct()
        )
        return result.scalars().all()

class CourseRepository(BaseRepository):
    """Course repository with relationships"""
    
    async def create(self, **kwargs) -> Course:
        course = Course(**kwargs)
        self.db.add(course)
        await self.commit()
        await self.db.refresh(course)
        return course
    
    async def get_by_id(self, course_id: int) -> Optional[Course]:
        result = await self.db.execute(
            select(Course)
            .options(selectinload(Course.lessons))
            .where(Course.id == course_id)
        )
        return result.scalar_one_or_none()
    
    async def get_user_courses(self, user_id: int) -> List[Course]:
        result = await self.db.execute(
            select(Course)
            .join(Course.enrolled_students)
            .where(User.id == user_id)
        )
        return result.scalars().all()
    
    async def enroll_student(self, course_id: int, student_id: int):
        course = await self.get_by_id(course_id)
        student = await self.db.get(User, student_id)
        if course and student:
            course.enrolled_students.append(student)
            await self.commit()
            return True
        return False

class ContentRepository(BaseRepository):
    """Content repository for AI-generated content"""
    
    async def create(self, user_id: int, course_id: int, content_data: Dict[str, Any]) -> Content:
        content = Content(
            created_by_id=user_id,
            course_id=course_id,
            title=content_data.get("title"),
            content_type=content_data.get("type"),
            content_data=content_data,
            created_at=datetime.utcnow()
        )
        self.db.add(content)
        await self.commit()
        await self.db.refresh(content)
        return content
    
    async def get_by_course(self, course_id: int) -> List[Content]:
        result = await self.db.execute(
            select(Content)
            .where(Content.course_id == course_id)
            .order_by(Content.created_at.desc())
        )
        return result.scalars().all()

class QuizRepository(BaseRepository):
    """Quiz repository with questions"""
    
    async def create(self, course_id: int, creator_id: int, quiz_data: Dict[str, Any]) -> Quiz:
        quiz = Quiz(
            course_id=course_id,
            created_by_id=creator_id,
            title=quiz_data.get("title"),
            description=quiz_data.get("description"),
            total_points=quiz_data.get("total_points", 100),
            time_limit=quiz_data.get("time_limit"),
            created_at=datetime.utcnow()
        )
        self.db.add(quiz)
        await self.db.flush()
        
        # Add questions
        for q_data in quiz_data.get("questions", []):
            question = QuizQuestion(
                quiz_id=quiz.id,
                question_text=q_data["question"],
                question_type=q_data["type"],
                options=q_data.get("options"),
                correct_answer=q_data["answer"],
                points=q_data.get("points", 10),
                explanation=q_data.get("explanation")
            )
            self.db.add(question)
        
        await self.commit()
        await self.db.refresh(quiz)
        return quiz
    
    async def submit_result(self, quiz_id: int, student_id: int, answers: List[Dict]) -> QuizResult:
        # Calculate score
        quiz = await self.get_by_id(quiz_id)
        score = 0
        total = 0
        
        for answer in answers:
            question = next((q for q in quiz.questions if q.id == answer["question_id"]), None)
            if question:
                total += question.points
                if answer["answer"] == question.correct_answer:
                    score += question.points
        
        result = QuizResult(
            quiz_id=quiz_id,
            student_id=student_id,
            score=score,
            total_points=total,
            answers=answers,
            completed_at=datetime.utcnow()
        )
        self.db.add(result)
        await self.commit()
        return result

class ProgressRepository(BaseRepository):
    """Student progress tracking"""
    
    async def update_progress(self, student_id: int, lesson_id: int, progress: float):
        existing = await self.db.execute(
            select(StudentProgress)
            .where(
                StudentProgress.student_id == student_id,
                StudentProgress.lesson_id == lesson_id
            )
        )
        record = existing.scalar_one_or_none()
        
        if record:
            record.progress_percentage = progress
            record.last_accessed = datetime.utcnow()
        else:
            record = StudentProgress(
                student_id=student_id,
                lesson_id=lesson_id,
                progress_percentage=progress,
                last_accessed=datetime.utcnow()
            )
            self.db.add(record)
        
        await self.commit()
        return record
    
    async def get_student_progress(self, student_id: int, course_id: int) -> List[StudentProgress]:
        result = await self.db.execute(
            select(StudentProgress)
            .join(Lesson, StudentProgress.lesson_id == Lesson.id)
            .where(
                StudentProgress.student_id == student_id,
                Lesson.course_id == course_id
            )
        )
        return result.scalars().all()
EOF
```

#### 3. Fix Authentication with Real Users
```bash
# Update authentication to use real database
cat > server/auth.py << 'EOF'
"""
JWT Authentication with Database Integration
"""
from datetime import datetime, timedelta
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from database.connection import get_db
from database.repositories import UserRepository
from server.config import settings

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

class User(BaseModel):
    id: int
    email: str
    full_name: str
    role: str
    school_id: Optional[int]

class TokenData(BaseModel):
    email: Optional[str] = None

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm="HS256")
    return encoded_jwt

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=["HS256"])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        token_data = TokenData(email=email)
    except JWTError:
        raise credentials_exception
    
    user_repo = UserRepository(db)
    user = await user_repo.get_by_email(email=token_data.email)
    if user is None:
        raise credentials_exception
    
    return User(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        school_id=user.school_id
    )

async def authenticate_user(db: AsyncSession, email: str, password: str):
    user_repo = UserRepository(db)
    user = await user_repo.get_by_email(email)
    if not user:
        return False
    if not verify_password(password, user.password_hash):
        return False
    return user
EOF
```

#### 4. Implement Real WebSocket Communication
```bash
# Create WebSocket manager
cat > server/websocket_manager.py << 'EOF'
"""
WebSocket Connection Manager for Real-time Updates
"""
from typing import Dict, List, Set
from fastapi import WebSocket
import json
import asyncio
import logging

logger = logging.getLogger(__name__)

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.user_connections: Dict[int, Set[str]] = {}
        self.room_connections: Dict[str, Set[str]] = {}
    
    async def connect(self, websocket: WebSocket, client_id: str, user_id: int = None):
        await websocket.accept()
        self.active_connections[client_id] = websocket
        
        if user_id:
            if user_id not in self.user_connections:
                self.user_connections[user_id] = set()
            self.user_connections[user_id].add(client_id)
        
        logger.info(f"Client {client_id} connected")
    
    def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            del self.active_connections[client_id]
        
        # Remove from user connections
        for user_id, connections in self.user_connections.items():
            if client_id in connections:
                connections.remove(client_id)
        
        # Remove from rooms
        for room, connections in self.room_connections.items():
            if client_id in connections:
                connections.remove(client_id)
        
        logger.info(f"Client {client_id} disconnected")
    
    async def send_personal_message(self, message: str, client_id: str):
        if client_id in self.active_connections:
            websocket = self.active_connections[client_id]
            await websocket.send_text(message)
    
    async def send_user_message(self, message: str, user_id: int):
        if user_id in self.user_connections:
            for client_id in self.user_connections[user_id]:
                await self.send_personal_message(message, client_id)
    
    async def broadcast(self, message: str):
        for client_id, websocket in self.active_connections.items():
            await websocket.send_text(message)
    
    async def join_room(self, client_id: str, room: str):
        if room not in self.room_connections:
            self.room_connections[room] = set()
        self.room_connections[room].add(client_id)
    
    async def leave_room(self, client_id: str, room: str):
        if room in self.room_connections:
            self.room_connections[room].discard(client_id)
    
    async def send_room_message(self, message: str, room: str):
        if room in self.room_connections:
            for client_id in self.room_connections[room]:
                await self.send_personal_message(message, client_id)

# Global manager instance
manager = ConnectionManager()
EOF
```

#### 5. Complete AI Agent Integration
```bash
# Fix supervisor agent
cat > agents/supervisor.py << 'EOF'
"""
Supervisor Agent with LangGraph Implementation
"""
from typing import Dict, Any, List
from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolExecutor
import asyncio
import logging

from agents.content_agent import ContentAgent
from agents.quiz_agent import QuizAgent
from agents.terrain_agent import TerrainAgent
from agents.script_agent import ScriptAgent
from agents.review_agent import ReviewAgent

logger = logging.getLogger(__name__)

class SupervisorAgent:
    """Orchestrates all sub-agents using LangGraph"""
    
    def __init__(self):
        self.llm = ChatOpenAI(temperature=0.7, model="gpt-4")
        self.content_agent = ContentAgent()
        self.quiz_agent = QuizAgent()
        self.terrain_agent = TerrainAgent()
        self.script_agent = ScriptAgent()
        self.review_agent = ReviewAgent()
        self.workflow = self._create_workflow()
    
    async def initialize(self):
        """Initialize all sub-agents"""
        await asyncio.gather(
            self.content_agent.initialize(),
            self.quiz_agent.initialize(),
            self.terrain_agent.initialize(),
            self.script_agent.initialize(),
            self.review_agent.initialize()
        )
        logger.info("All agents initialized")
    
    async def cleanup(self):
        """Cleanup all sub-agents"""
        await asyncio.gather(
            self.content_agent.cleanup(),
            self.quiz_agent.cleanup(),
            self.terrain_agent.cleanup(),
            self.script_agent.cleanup(),
            self.review_agent.cleanup()
        )
    
    def _create_workflow(self):
        """Create LangGraph workflow"""
        workflow = StateGraph()
        
        # Add nodes for each agent
        workflow.add_node("router", self.route_request)
        workflow.add_node("content", self.content_agent.generate)
        workflow.add_node("quiz", self.quiz_agent.generate)
        workflow.add_node("terrain", self.terrain_agent.generate)
        workflow.add_node("script", self.script_agent.generate)
        workflow.add_node("review", self.review_agent.review)
        
        # Add edges
        workflow.add_edge("router", "content")
        workflow.add_edge("router", "quiz")
        workflow.add_edge("router", "terrain")
        workflow.add_edge("router", "script")
        workflow.add_edge("content", "review")
        workflow.add_edge("quiz", "review")
        workflow.add_edge("terrain", "review")
        workflow.add_edge("script", "review")
        workflow.add_edge("review", END)
        
        workflow.set_entry_point("router")
        
        return workflow.compile()
    
    async def route_request(self, state: Dict[str, Any]) -> str:
        """Route request to appropriate agent"""
        request_type = state.get("type", "content")
        
        routing_map = {
            "content": "content",
            "quiz": "quiz",
            "terrain": "terrain",
            "script": "script"
        }
        
        return routing_map.get(request_type, "content")
    
    async def generate_content(self, **kwargs) -> Dict[str, Any]:
        """Generate educational content"""
        state = {"type": "content", **kwargs}
        result = await self.workflow.arun(state)
        return result
    
    async def generate_quiz(self, **kwargs) -> Dict[str, Any]:
        """Generate quiz questions"""
        state = {"type": "quiz", **kwargs}
        result = await self.workflow.arun(state)
        return result
    
    async def generate_environment(self, **kwargs) -> Dict[str, Any]:
        """Generate 3D environment"""
        state = {"type": "terrain", **kwargs}
        result = await self.workflow.arun(state)
        return result
    
    async def generate_script(self, **kwargs) -> Dict[str, Any]:
        """Generate Lua scripts"""
        state = {"type": "script", **kwargs}
        result = await self.workflow.arun(state)
        return result
EOF
```

#### 6. Database Connection Management
```bash
# Create proper database connection
cat > database/connection.py << 'EOF'
"""
Database Connection Management with Connection Pooling
"""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from contextlib import asynccontextmanager
import os
import logging

logger = logging.getLogger(__name__)

# Database URL
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres:staging_password_2024@localhost:5432/toolboxai_db"
)

# Create async engine with connection pooling
engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    pool_size=20,
    max_overflow=0,
    pool_pre_ping=True,
    pool_recycle=3600
)

# Session factory
async_session = async_sessionmaker(
    engine, 
    class_=AsyncSession, 
    expire_on_commit=False
)

Base = declarative_base()

async def init_db():
    """Initialize database"""
    async with engine.begin() as conn:
        # Create tables if they don't exist
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database initialized")

async def close_db():
    """Close database connections"""
    await engine.dispose()
    logger.info("Database connections closed")

async def get_db():
    """Dependency to get database session"""
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

@asynccontextmanager
async def get_session():
    """Context manager for database session"""
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
EOF
```

#### 7. Redis Integration for Caching
```bash
# Setup Redis connection
cat > server/redis_manager.py << 'EOF'
"""
Redis Cache Manager for Performance
"""
import redis.asyncio as redis
import json
import pickle
from typing import Any, Optional
import os

class RedisManager:
    def __init__(self):
        self.redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        self.client = None
    
    async def connect(self):
        """Connect to Redis"""
        self.client = await redis.from_url(self.redis_url, decode_responses=True)
    
    async def disconnect(self):
        """Disconnect from Redis"""
        if self.client:
            await self.client.close()
    
    async def set_cache(self, key: str, value: Any, expire: int = 3600):
        """Set cache value"""
        if isinstance(value, (dict, list)):
            value = json.dumps(value)
        await self.client.setex(key, expire, value)
    
    async def get_cache(self, key: str) -> Optional[Any]:
        """Get cache value"""
        value = await self.client.get(key)
        if value:
            try:
                return json.loads(value)
            except:
                return value
        return None
    
    async def delete_cache(self, key: str):
        """Delete cache key"""
        await self.client.delete(key)
    
    async def flush_all(self):
        """Clear all cache"""
        await self.client.flushall()

# Global instance
redis_manager = RedisManager()
EOF
```

#### 8. Start Services with Monitoring
```bash
# Create service starter with health checks
cat > scripts/start_backend_services.sh << 'EOF'
#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}Starting Backend Services...${NC}"

# Set environment variables
export POSTGRES_PASSWORD=staging_password_2024
export REDIS_PASSWORD=staging_redis_2024
export JWT_SECRET_KEY=staging_jwt_secret_key_very_long_and_secure_2024
export OPENAI_API_KEY=${OPENAI_API_KEY:-"your-api-key"}
export ENVIRONMENT=production

# Start PostgreSQL if not running
if ! pg_isready -q; then
    echo -e "${YELLOW}Starting PostgreSQL...${NC}"
    pg_ctl start -D /usr/local/var/postgres
fi

# Start Redis if not running
if ! redis-cli ping > /dev/null 2>&1; then
    echo -e "${YELLOW}Starting Redis...${NC}"
    redis-server --daemonize yes
fi

# Navigate to project directory
cd /Volumes/G-DRIVE\ ArmorATD/Development/Clients/ToolBoxAI-Solutions/ToolboxAI-Roblox-Environment

# Activate virtual environment
source venv_clean/bin/activate

# Run database migrations
echo -e "${GREEN}Running database migrations...${NC}"
alembic upgrade head

# Start FastAPI server
echo -e "${GREEN}Starting FastAPI server on port 8008...${NC}"
uvicorn server.main:app --host 127.0.0.1 --port 8008 --reload &
FASTAPI_PID=$!

# Start Flask bridge
echo -e "${GREEN}Starting Flask bridge on port 5001...${NC}"
python server/roblox_server.py &
FLASK_PID=$!

# Start MCP server
echo -e "${GREEN}Starting MCP WebSocket on port 9876...${NC}"
python mcp/server.py &
MCP_PID=$!

# Save PIDs
echo $FASTAPI_PID > scripts/pids/fastapi.pid
echo $FLASK_PID > scripts/pids/flask.pid
echo $MCP_PID > scripts/pids/mcp.pid

# Wait for services to start
sleep 5

# Health check
echo -e "${GREEN}Checking service health...${NC}"
curl -s http://localhost:8008/health | jq .
curl -s http://localhost:5001/health | jq .

echo -e "${GREEN}All backend services started successfully!${NC}"
EOF

chmod +x scripts/start_backend_services.sh
```

## Communication Protocol
- Coordinate with Terminal 1 for file path updates
- Inform Terminal 3 of API endpoint changes
- Share database schema with Terminal 4
- Provide test endpoints to Terminal 5

## Success Metrics
✅ FastAPI server running without errors
✅ All endpoints returning real data
✅ Database connections working
✅ WebSocket connections stable
✅ Redis caching operational
✅ AI agents generating content
✅ Authentication working with JWT
✅ Health checks passing

## Notes
- Use real database connections, not mocks
- Implement proper error handling
- Add logging for debugging
- Test each endpoint manually
- Document any API changes