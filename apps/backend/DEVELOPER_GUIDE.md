# Backend Developer Guide

## Table of Contents
- [Getting Started](#getting-started)
- [Project Structure](#project-structure)
- [Development Workflow](#development-workflow)
- [Adding New Features](#adding-new-features)
- [Creating Endpoints](#creating-endpoints)
- [Service Development](#service-development)
- [Middleware Development](#middleware-development)
- [Testing Guidelines](#testing-guidelines)
- [Code Standards](#code-standards)
- [Debugging Guide](#debugging-guide)
- [Performance Optimization](#performance-optimization)

## Getting Started

### Prerequisites
- Python 3.12+
- PostgreSQL 15+
- Redis 7+
- Node.js 18+ (for frontend development)

### Development Setup

#### 1. Environment Configuration
```bash
# Clone repository
git clone <repository-url>
cd ToolBoxAI-Solutions

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Setup environment variables
cp .env.example .env
# Edit .env with your configuration
```

#### 2. Database Setup
```bash
# Start PostgreSQL and Redis
docker-compose up -d postgres redis

# Run database migrations
cd apps/backend
alembic upgrade head

# Verify setup
python -c "from core.config import settings; print(f'Database: {settings.DATABASE_URL}')"
```

#### 3. Development Server
```bash
# Start backend server
cd apps/backend
uvicorn main:app --host 127.0.0.1 --port 8009 --reload

# Verify health check
curl http://localhost:8009/health
```

### IDE Configuration

#### VS Code Setup
```json
// .vscode/settings.json
{
  "python.defaultInterpreterPath": "./venv/bin/python",
  "python.linting.enabled": true,
  "python.linting.pylintEnabled": true,
  "python.formatting.provider": "black",
  "python.testing.pytestEnabled": true,
  "python.testing.pytestArgs": ["apps/backend/tests"],
  "files.associations": {
    "*.py": "python"
  }
}
```

#### PyCharm Setup
```python
# Configure Python interpreter
File > Settings > Project > Python Interpreter
Add > Virtualenv Environment > Existing environment
Point to: ./venv/bin/python

# Configure test runner
Run > Edit Configurations > Add > Python tests > pytest
Target: apps/backend/tests
```

## Project Structure

### Backend Directory Layout
```
apps/backend/
├── main.py                     # FastAPI application entry point
├── core/                       # Core functionality
│   ├── __init__.py
│   ├── config.py              # Configuration management
│   ├── logging.py             # Logging infrastructure
│   ├── monitoring.py          # Sentry and metrics
│   ├── circuit_breaker.py     # Circuit breaker implementation
│   ├── rate_limiter.py        # Rate limiting functionality
│   ├── security/              # Security components
│   │   ├── cors.py           # CORS configuration
│   │   ├── jwt_handler.py    # JWT authentication
│   │   ├── middleware.py     # Security middleware
│   │   └── secrets.py        # Secret management
│   ├── database/              # Database components
│   │   ├── repositories.py   # Data access layer
│   │   └── query_optimizer.py # Query optimization
│   └── errors/                # Error handling
│       ├── __init__.py
│       ├── error_handler.py  # Global error handler
│       └── middleware.py     # Error middleware
├── api/                       # API layer
│   ├── __init__.py
│   ├── v1/                   # API version 1
│   │   ├── __init__.py
│   │   ├── router.py         # Main API router
│   │   └── endpoints/        # Individual endpoint modules
│   │       ├── auth.py       # Authentication endpoints
│   │       ├── dashboard.py  # Dashboard endpoints
│   │       ├── content.py    # Content generation
│   │       ├── roblox.py     # Roblox integration
│   │       └── ...
│   ├── auth/                 # Authentication utilities
│   │   ├── db_auth.py       # Database authentication
│   │   └── auth_secure.py   # Secure auth helpers
│   ├── middleware/           # Custom middleware
│   │   └── resilience.py    # Resilience middleware
│   └── webhooks/             # Webhook handlers
│       └── clerk_webhooks.py # External webhook processing
├── services/                 # Business logic services
│   ├── __init__.py
│   ├── agent_service.py     # AI agent coordination
│   ├── pusher_realtime.py   # Real-time communication
│   ├── analytics.py         # Analytics processing
│   ├── roblox.py           # Roblox platform integration
│   └── websocket.py        # Legacy WebSocket support
├── agents/                  # AI agent system
│   ├── __init__.py
│   ├── agent.py            # Base agent implementation
│   ├── content_agent.py    # Content generation agent
│   └── tools.py            # Agent tools and utilities
├── models/                  # Data models
│   ├── __init__.py
│   └── database.py         # Database model definitions
├── utils/                   # Utility functions
│   ├── __init__.py
│   └── tools.py            # Helper functions
└── tests/                   # Test suite
    ├── __init__.py
    ├── unit/               # Unit tests
    ├── integration/        # Integration tests
    └── fixtures/           # Test fixtures
```

### Key Components Explained

#### 1. Core Layer (`core/`)
**Purpose**: Infrastructure and cross-cutting concerns
- **config.py**: Centralized configuration management
- **logging.py**: Structured logging with correlation IDs
- **monitoring.py**: Sentry integration and metrics collection
- **security/**: Authentication, authorization, and security middleware

#### 2. API Layer (`api/`)
**Purpose**: HTTP interface and routing
- **v1/endpoints/**: Modular endpoint organization
- **middleware/**: Custom middleware components
- **webhooks/**: External webhook processing

#### 3. Service Layer (`services/`)
**Purpose**: Business logic implementation
- Domain-specific services (AI agents, analytics, etc.)
- External service integrations
- Business rule enforcement

#### 4. Agent System (`agents/`)
**Purpose**: AI-powered task automation
- Multi-agent coordination
- Task queue management
- AI model integration

## Development Workflow

### Feature Development Process

#### 1. Planning Phase
```bash
# Create feature branch
git checkout -b feature/new-endpoint

# Create tracking issue (if using GitHub Issues)
# Define requirements and acceptance criteria
```

#### 2. Implementation Phase
```python
# Follow TDD approach
# 1. Write failing test
# 2. Implement minimum code to pass
# 3. Refactor and optimize
```

#### 3. Testing Phase
```bash
# Run unit tests
pytest apps/backend/tests/unit/

# Run integration tests
pytest apps/backend/tests/integration/

# Run specific test file
pytest apps/backend/tests/unit/test_new_feature.py -v
```

#### 4. Code Review Phase
```bash
# Create pull request
git push origin feature/new-endpoint

# Address review feedback
# Ensure all checks pass
```

### Development Commands

#### Common Tasks
```bash
# Start development server with auto-reload
cd apps/backend
uvicorn main:app --reload --host 127.0.0.1 --port 8009

# Run tests with coverage
pytest --cov=apps/backend apps/backend/tests/

# Format code
black apps/backend/
isort apps/backend/

# Lint code
pylint apps/backend/
mypy apps/backend/

# Generate migration
alembic revision --autogenerate -m "Add new feature"

# Apply migrations
alembic upgrade head
```

#### Docker Development
```bash
# Build and start all services
docker-compose -f infrastructure/docker/docker-compose.dev.yml up --build

# Restart specific service
docker-compose -f infrastructure/docker/docker-compose.dev.yml restart fastapi-main

# View logs
docker-compose -f infrastructure/docker/docker-compose.dev.yml logs -f fastapi-main
```

## Adding New Features

### Creating a New Router Module

#### 1. Create Router File
```python
# apps/backend/api/v1/endpoints/my_feature.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from apps.backend.core.database import get_async_session
from apps.backend.api.auth.db_auth import get_current_user
from apps.backend.models.database import User
from pydantic import BaseModel

router = APIRouter()

class MyFeatureRequest(BaseModel):
    name: str
    description: str

class MyFeatureResponse(BaseModel):
    id: int
    name: str
    description: str
    created_at: datetime

@router.post("/my-feature", response_model=MyFeatureResponse)
async def create_my_feature(
    request: MyFeatureRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    """Create a new feature instance."""
    # Implementation here
    pass

@router.get("/my-feature", response_model=List[MyFeatureResponse])
async def list_my_features(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    """List all feature instances."""
    # Implementation here
    pass
```

#### 2. Register Router
```python
# In apps/backend/main.py, add:
try:
    from apps.backend.api.v1.endpoints.my_feature import router as my_feature_router
    app.include_router(my_feature_router, prefix="/api/v1", tags=["my-feature"])
    logger.info("My Feature router registered successfully")
except ImportError as e:
    logger.warning(f"Could not import my feature router: {e}")
```

#### 3. Add Tests
```python
# apps/backend/tests/unit/api/v1/endpoints/test_my_feature.py
import pytest
from httpx import AsyncClient
from fastapi.testclient import TestClient

@pytest.mark.asyncio
async def test_create_my_feature(async_client: AsyncClient, auth_headers):
    """Test creating a new feature."""
    payload = {
        "name": "Test Feature",
        "description": "Test description"
    }

    response = await async_client.post(
        "/api/v1/my-feature",
        json=payload,
        headers=auth_headers
    )

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == payload["name"]
    assert data["description"] == payload["description"]

@pytest.mark.asyncio
async def test_list_my_features(async_client: AsyncClient, auth_headers):
    """Test listing features."""
    response = await async_client.get(
        "/api/v1/my-feature",
        headers=auth_headers
    )

    assert response.status_code == 200
    assert isinstance(response.json(), list)
```

### Adding a New Service

#### 1. Create Service Class
```python
# apps/backend/services/my_service.py
import asyncio
import logging
from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession

from apps.backend.core.config import settings
from apps.backend.core.logging import log_database_operation
from apps.backend.models.database import MyModel

logger = logging.getLogger(__name__)

class MyService:
    """Service for handling my feature business logic."""

    def __init__(self):
        self.config = settings

    async def create_item(
        self,
        db: AsyncSession,
        data: Dict[str, Any]
    ) -> MyModel:
        """Create a new item."""
        try:
            with log_database_operation("create_my_item"):
                item = MyModel(**data)
                db.add(item)
                await db.commit()
                await db.refresh(item)
                return item
        except Exception as e:
            logger.error(f"Failed to create item: {e}")
            await db.rollback()
            raise

    async def list_items(
        self,
        db: AsyncSession,
        user_id: int,
        limit: int = 100
    ) -> List[MyModel]:
        """List items for user."""
        try:
            with log_database_operation("list_my_items"):
                query = select(MyModel).where(
                    MyModel.user_id == user_id
                ).limit(limit)
                result = await db.execute(query)
                return result.scalars().all()
        except Exception as e:
            logger.error(f"Failed to list items: {e}")
            raise

    async def process_async_task(self, item_id: int) -> bool:
        """Process an asynchronous task."""
        try:
            # Simulate async processing
            await asyncio.sleep(1)
            logger.info(f"Processed item {item_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to process item {item_id}: {e}")
            return False

# Global service instance
my_service = MyService()

def get_my_service() -> MyService:
    """Get service instance."""
    return my_service
```

#### 2. Integrate with Router
```python
# In your router file, add:
from apps.backend.services.my_service import get_my_service, MyService

@router.post("/my-feature", response_model=MyFeatureResponse)
async def create_my_feature(
    request: MyFeatureRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
    service: MyService = Depends(get_my_service)
):
    """Create a new feature instance."""
    try:
        item = await service.create_item(
            db=db,
            data=request.dict()
        )
        return MyFeatureResponse.from_orm(item)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

## Creating Endpoints

### Endpoint Development Pattern

#### 1. Request/Response Models
```python
# Define clear Pydantic models
from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime

class CreateContentRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    content_type: str = Field(..., regex="^(lesson|quiz|activity)$")
    difficulty_level: int = Field(..., ge=1, le=10)

    @validator('title')
    def validate_title(cls, v):
        if not v.strip():
            raise ValueError('Title cannot be empty')
        return v.strip()

class ContentResponse(BaseModel):
    id: int
    title: str
    description: Optional[str]
    content_type: str
    difficulty_level: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True  # Pydantic v2
```

#### 2. Error Handling
```python
from apps.backend.core.errors import (
    ValidationError,
    NotFoundError,
    AuthenticationError
)

@router.post("/content", response_model=ContentResponse)
async def create_content(
    request: CreateContentRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    """Create educational content."""
    try:
        # Validation
        if not current_user.is_teacher():
            raise AuthenticationError("Only teachers can create content")

        # Business logic
        content = await content_service.create(
            db=db,
            user_id=current_user.id,
            data=request.dict()
        )

        return ContentResponse.from_orm(content)

    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except AuthenticationError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error creating content: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
```

#### 3. Async Operations
```python
from fastapi import BackgroundTasks

@router.post("/content/generate", response_model=TaskResponse)
async def generate_content(
    request: GenerateContentRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    """Generate content using AI agents."""
    # Create task
    task_id = str(uuid.uuid4())

    # Start background processing
    background_tasks.add_task(
        process_content_generation,
        task_id=task_id,
        user_id=current_user.id,
        request_data=request.dict()
    )

    return TaskResponse(
        task_id=task_id,
        status="started",
        message="Content generation started"
    )

async def process_content_generation(
    task_id: str,
    user_id: int,
    request_data: dict
):
    """Background task for content generation."""
    try:
        # Update task status
        await update_task_status(task_id, "processing")

        # Generate content
        result = await agent_service.generate_content(request_data)

        # Save result
        await save_generated_content(user_id, result)

        # Update task status
        await update_task_status(task_id, "completed", result)

        # Send real-time notification
        await pusher_service.trigger(
            f"user-{user_id}",
            "content_generated",
            {"task_id": task_id, "content": result}
        )

    except Exception as e:
        logger.error(f"Content generation failed: {e}")
        await update_task_status(task_id, "failed", {"error": str(e)})
```

#### 4. Pagination
```python
from fastapi import Query
from typing import Optional

class PaginationParams:
    def __init__(
        self,
        page: int = Query(1, ge=1, description="Page number"),
        size: int = Query(20, ge=1, le=100, description="Page size")
    ):
        self.page = page
        self.size = size
        self.offset = (page - 1) * size

@router.get("/content", response_model=PaginatedContentResponse)
async def list_content(
    pagination: PaginationParams = Depends(),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    """List content with pagination."""
    content_list, total = await content_service.list_paginated(
        db=db,
        user_id=current_user.id,
        offset=pagination.offset,
        limit=pagination.size
    )

    return PaginatedContentResponse(
        items=content_list,
        total=total,
        page=pagination.page,
        size=pagination.size,
        pages=(total + pagination.size - 1) // pagination.size
    )
```

## Service Development

### Service Architecture Pattern

#### 1. Base Service Class
```python
# apps/backend/services/base.py
from abc import ABC, abstractmethod
from typing import Generic, TypeVar, Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import declarative_base

ModelType = TypeVar("ModelType", bound=declarative_base())

class BaseService(Generic[ModelType], ABC):
    """Base service class with common CRUD operations."""

    def __init__(self, model_class: type[ModelType]):
        self.model_class = model_class

    async def create(
        self,
        db: AsyncSession,
        data: Dict[str, Any]
    ) -> ModelType:
        """Create a new instance."""
        instance = self.model_class(**data)
        db.add(instance)
        await db.commit()
        await db.refresh(instance)
        return instance

    async def get_by_id(
        self,
        db: AsyncSession,
        instance_id: int
    ) -> Optional[ModelType]:
        """Get instance by ID."""
        result = await db.get(self.model_class, instance_id)
        return result

    async def update(
        self,
        db: AsyncSession,
        instance_id: int,
        data: Dict[str, Any]
    ) -> Optional[ModelType]:
        """Update instance."""
        instance = await self.get_by_id(db, instance_id)
        if instance:
            for key, value in data.items():
                setattr(instance, key, value)
            await db.commit()
            await db.refresh(instance)
        return instance

    async def delete(
        self,
        db: AsyncSession,
        instance_id: int
    ) -> bool:
        """Delete instance."""
        instance = await self.get_by_id(db, instance_id)
        if instance:
            await db.delete(instance)
            await db.commit()
            return True
        return False
```

#### 2. Specialized Service Implementation
```python
# apps/backend/services/content_service.py
from typing import List, Optional, Dict, Any
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from apps.backend.services.base import BaseService
from apps.backend.models.database import EducationalContent, User
from apps.backend.core.logging import log_database_operation
from apps.backend.services.agent_service import get_agent_service

class ContentService(BaseService[EducationalContent]):
    """Service for managing educational content."""

    def __init__(self):
        super().__init__(EducationalContent)
        self.agent_service = get_agent_service()

    async def create_with_validation(
        self,
        db: AsyncSession,
        user_id: int,
        data: Dict[str, Any]
    ) -> EducationalContent:
        """Create content with validation."""
        with log_database_operation("create_content"):
            # Add user_id and validation
            data["user_id"] = user_id
            data["status"] = "draft"

            # Validate content type
            if data.get("content_type") not in ["lesson", "quiz", "activity"]:
                raise ValueError("Invalid content type")

            return await self.create(db, data)

    async def list_by_user(
        self,
        db: AsyncSession,
        user_id: int,
        content_type: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> tuple[List[EducationalContent], int]:
        """List content by user with filtering."""
        with log_database_operation("list_content_by_user"):
            query = select(EducationalContent).where(
                EducationalContent.user_id == user_id
            )

            if content_type:
                query = query.where(
                    EducationalContent.content_type == content_type
                )

            # Get total count
            count_query = select(func.count()).select_from(query.subquery())
            total_result = await db.execute(count_query)
            total = total_result.scalar()

            # Get paginated results
            query = query.offset(offset).limit(limit)
            result = await db.execute(query)
            content_list = result.scalars().all()

            return content_list, total

    async def generate_ai_content(
        self,
        db: AsyncSession,
        user_id: int,
        prompt: str,
        content_type: str
    ) -> EducationalContent:
        """Generate content using AI agents."""
        try:
            # Request AI generation
            generated_data = await self.agent_service.execute_task(
                task_type="content_generation",
                data={
                    "prompt": prompt,
                    "content_type": content_type,
                    "user_id": user_id
                }
            )

            # Save generated content
            content_data = {
                "title": generated_data["title"],
                "content": generated_data["content"],
                "content_type": content_type,
                "generated": True,
                "status": "generated"
            }

            return await self.create_with_validation(
                db, user_id, content_data
            )

        except Exception as e:
            logger.error(f"AI content generation failed: {e}")
            raise

# Global service instance
content_service = ContentService()

def get_content_service() -> ContentService:
    """Get content service instance."""
    return content_service
```

#### 3. Service Dependencies
```python
# apps/backend/services/dependencies.py
from typing import AsyncGenerator
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from apps.backend.core.database import get_async_session
from apps.backend.services.content_service import ContentService, get_content_service
from apps.backend.services.agent_service import AgentService, get_agent_service
from apps.backend.services.pusher_realtime import PusherService, get_pusher_service

class ServiceManager:
    """Centralized service management."""

    def __init__(
        self,
        db: AsyncSession,
        content_service: ContentService,
        agent_service: AgentService,
        pusher_service: PusherService
    ):
        self.db = db
        self.content = content_service
        self.agents = agent_service
        self.pusher = pusher_service

async def get_service_manager(
    db: AsyncSession = Depends(get_async_session),
    content_service: ContentService = Depends(get_content_service),
    agent_service: AgentService = Depends(get_agent_service),
    pusher_service: PusherService = Depends(get_pusher_service)
) -> ServiceManager:
    """Get service manager with all dependencies."""
    return ServiceManager(
        db=db,
        content_service=content_service,
        agent_service=agent_service,
        pusher_service=pusher_service
    )
```

## Middleware Development

### Custom Middleware Pattern

#### 1. Basic Middleware Structure
```python
# apps/backend/api/middleware/custom_middleware.py
import time
import uuid
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

class CustomMiddleware(BaseHTTPMiddleware):
    """Custom middleware for request processing."""

    def __init__(self, app, config: dict = None):
        super().__init__(app)
        self.config = config or {}

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and response."""
        # Pre-processing
        start_time = time.time()
        request_id = str(uuid.uuid4())

        # Add correlation ID to request
        request.state.correlation_id = request_id

        # Add custom headers
        response = await call_next(request)

        # Post-processing
        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = str(process_time)
        response.headers["X-Request-ID"] = request_id

        return response
```

#### 2. Authentication Middleware
```python
# apps/backend/api/middleware/auth_middleware.py
import jwt
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware

class AuthenticationMiddleware(BaseHTTPMiddleware):
    """JWT authentication middleware."""

    def __init__(self, app, secret_key: str, algorithm: str = "HS256"):
        super().__init__(app)
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.exempt_paths = {
            "/health",
            "/auth/login",
            "/auth/register",
            "/docs",
            "/openapi.json"
        }

    async def dispatch(self, request: Request, call_next):
        """Authenticate requests."""
        # Skip authentication for exempt paths
        if request.url.path in self.exempt_paths:
            return await call_next(request)

        # Extract token from header
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Missing or invalid token")

        token = auth_header[7:]  # Remove "Bearer " prefix

        try:
            # Decode and validate token
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm]
            )

            # Add user info to request state
            request.state.user_id = payload.get("user_id")
            request.state.user_role = payload.get("role")

        except jwt.InvalidTokenError:
            raise HTTPException(status_code=401, detail="Invalid token")

        return await call_next(request)
```

#### 3. Circuit Breaker Middleware
```python
# apps/backend/api/middleware/circuit_breaker_middleware.py
from typing import Dict, Callable, Optional
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware

from apps.backend.core.circuit_breaker import CircuitBreaker

class CircuitBreakerMiddleware(BaseHTTPMiddleware):
    """Circuit breaker middleware for route protection."""

    def __init__(self, app):
        super().__init__(app)
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self.route_configs = {
            "/api/v1/agents/": {
                "failure_threshold": 5,
                "timeout_seconds": 60,
                "expected_exception": HTTPException
            },
            "/api/v1/content/generate": {
                "failure_threshold": 3,
                "timeout_seconds": 120,
                "expected_exception": Exception
            }
        }

    def get_circuit_breaker(self, route: str) -> Optional[CircuitBreaker]:
        """Get or create circuit breaker for route."""
        config = self.route_configs.get(route)
        if not config:
            return None

        if route not in self.circuit_breakers:
            self.circuit_breakers[route] = CircuitBreaker(
                name=f"route_{route.replace('/', '_')}",
                failure_threshold=config["failure_threshold"],
                timeout_seconds=config["timeout_seconds"],
                expected_exception=config["expected_exception"]
            )

        return self.circuit_breakers[route]

    async def dispatch(self, request: Request, call_next):
        """Apply circuit breaker protection."""
        route_pattern = self.match_route_pattern(request.url.path)
        circuit_breaker = self.get_circuit_breaker(route_pattern)

        if not circuit_breaker:
            return await call_next(request)

        try:
            # Execute request through circuit breaker
            response = await circuit_breaker.call(call_next, request)
            return response

        except Exception as e:
            if circuit_breaker.is_open():
                raise HTTPException(
                    status_code=503,
                    detail="Service temporarily unavailable"
                )
            raise e

    def match_route_pattern(self, path: str) -> str:
        """Match path to route pattern."""
        for pattern in self.route_configs.keys():
            if path.startswith(pattern):
                return pattern
        return path
```

## Testing Guidelines

### Test Structure

#### 1. Test Organization
```
tests/
├── unit/                    # Unit tests
│   ├── api/
│   │   └── v1/
│   │       └── endpoints/
│   ├── services/
│   ├── core/
│   └── middleware/
├── integration/             # Integration tests
│   ├── api/
│   ├── database/
│   └── external/
├── fixtures/                # Test fixtures
│   ├── __init__.py
│   ├── database.py
│   ├── auth.py
│   └── agents.py
└── conftest.py             # Pytest configuration
```

#### 2. Test Configuration
```python
# tests/conftest.py
import asyncio
import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from apps.backend.main import app
from apps.backend.core.config import settings
from apps.backend.core.database import get_async_session
from apps.backend.models.database import Base

# Test database URL
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"

@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest_asyncio.fixture(scope="session")
async def test_engine():
    """Create test database engine."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()

@pytest_asyncio.fixture
async def test_db(test_engine):
    """Create test database session."""
    async_session = sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as session:
        yield session

@pytest_asyncio.fixture
async def async_client(test_db):
    """Create test client."""
    app.dependency_overrides[get_async_session] = lambda: test_db

    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client

    app.dependency_overrides.clear()

@pytest.fixture
def auth_headers():
    """Create authentication headers."""
    # Create test JWT token
    token = create_test_jwt_token(user_id=1, role="teacher")
    return {"Authorization": f"Bearer {token}"}
```

#### 3. Unit Test Examples
```python
# tests/unit/services/test_content_service.py
import pytest
from unittest.mock import AsyncMock, patch

from apps.backend.services.content_service import ContentService
from apps.backend.models.database import EducationalContent

@pytest.mark.asyncio
class TestContentService:
    """Test content service functionality."""

    @pytest.fixture
    def content_service(self):
        """Create content service instance."""
        return ContentService()

    async def test_create_content_success(self, content_service, test_db):
        """Test successful content creation."""
        data = {
            "title": "Test Content",
            "description": "Test description",
            "content_type": "lesson",
            "difficulty_level": 5
        }

        content = await content_service.create_with_validation(
            db=test_db,
            user_id=1,
            data=data
        )

        assert content.title == data["title"]
        assert content.content_type == data["content_type"]
        assert content.user_id == 1
        assert content.status == "draft"

    async def test_create_content_invalid_type(self, content_service, test_db):
        """Test content creation with invalid type."""
        data = {
            "title": "Test Content",
            "content_type": "invalid",
            "difficulty_level": 5
        }

        with pytest.raises(ValueError, match="Invalid content type"):
            await content_service.create_with_validation(
                db=test_db,
                user_id=1,
                data=data
            )

    @patch('apps.backend.services.content_service.agent_service')
    async def test_generate_ai_content(self, mock_agent_service, content_service, test_db):
        """Test AI content generation."""
        # Mock agent service response
        mock_agent_service.execute_task.return_value = {
            "title": "Generated Content",
            "content": "Generated content body"
        }

        content = await content_service.generate_ai_content(
            db=test_db,
            user_id=1,
            prompt="Create a lesson about Python",
            content_type="lesson"
        )

        assert content.title == "Generated Content"
        assert content.generated is True
        assert content.status == "generated"
        mock_agent_service.execute_task.assert_called_once()
```

#### 4. Integration Test Examples
```python
# tests/integration/api/test_content_endpoints.py
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
class TestContentEndpoints:
    """Test content API endpoints."""

    async def test_create_content_endpoint(self, async_client: AsyncClient, auth_headers):
        """Test content creation endpoint."""
        payload = {
            "title": "Integration Test Content",
            "description": "Test description",
            "content_type": "lesson",
            "difficulty_level": 5
        }

        response = await async_client.post(
            "/api/v1/content",
            json=payload,
            headers=auth_headers
        )

        assert response.status_code == 201
        data = response.json()
        assert data["data"]["title"] == payload["title"]
        assert data["status"] == "success"

    async def test_list_content_endpoint(self, async_client: AsyncClient, auth_headers):
        """Test content listing endpoint."""
        response = await async_client.get(
            "/api/v1/content?page=1&size=10",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert "items" in data["data"]
        assert "total" in data["data"]
        assert "page" in data["data"]

    async def test_unauthorized_access(self, async_client: AsyncClient):
        """Test unauthorized access to protected endpoint."""
        response = await async_client.get("/api/v1/content")

        assert response.status_code == 401
```

### Testing Best Practices

#### 1. Test Naming Convention
```python
# Format: test_[function]_[scenario]_[expected_result]
def test_create_content_with_valid_data_returns_success():
    pass

def test_create_content_with_invalid_type_raises_validation_error():
    pass

def test_list_content_with_pagination_returns_paginated_results():
    pass
```

#### 2. Test Data Management
```python
# tests/fixtures/content.py
import pytest
from apps.backend.models.database import EducationalContent, User

@pytest.fixture
def sample_user(test_db):
    """Create sample user for testing."""
    user = User(
        username="testuser",
        email="test@example.com",
        role="teacher"
    )
    test_db.add(user)
    test_db.commit()
    return user

@pytest.fixture
def sample_content(test_db, sample_user):
    """Create sample content for testing."""
    content = EducationalContent(
        title="Sample Content",
        description="Sample description",
        content_type="lesson",
        difficulty_level=5,
        user_id=sample_user.id
    )
    test_db.add(content)
    test_db.commit()
    return content
```

#### 3. Mock External Services
```python
# tests/unit/test_agent_integration.py
import pytest
from unittest.mock import AsyncMock, patch

@patch('apps.backend.services.agent_service.openai_client')
async def test_ai_content_generation(mock_openai):
    """Test AI content generation with mocked OpenAI."""
    mock_openai.chat.completions.create.return_value = AsyncMock(
        choices=[AsyncMock(message=AsyncMock(content="Generated content"))]
    )

    # Test implementation
    result = await generate_content_with_ai("Test prompt")
    assert "Generated content" in result
```

## Code Standards

### Python Code Style

#### 1. Code Formatting
```python
# Use Black for automatic formatting
# Configuration in pyproject.toml
[tool.black]
line-length = 100
target-version = ['py312']
include = '\.pyi?$'
exclude = '''
/(
    \.eggs
  | \.git
  | \.venv
  | build
  | dist
)/
'''
```

#### 2. Import Organization
```python
# Standard library imports
import asyncio
import logging
from datetime import datetime
from typing import List, Dict, Optional, Any

# Third-party imports
import httpx
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

# Local imports
from apps.backend.core.config import settings
from apps.backend.core.logging import logger
from apps.backend.models.database import User
from apps.backend.services.content_service import get_content_service
```

#### 3. Documentation Standards
```python
class ContentService:
    """Service for managing educational content.

    This service provides methods for creating, retrieving, updating,
    and deleting educational content. It integrates with AI agents
    for content generation and provides validation.

    Attributes:
        model_class: The SQLAlchemy model class for content
        agent_service: Service for AI agent integration
    """

    async def create_content(
        self,
        db: AsyncSession,
        user_id: int,
        data: Dict[str, Any]
    ) -> EducationalContent:
        """Create new educational content.

        Args:
            db: Database session
            user_id: ID of the user creating content
            data: Content data dictionary

        Returns:
            Created EducationalContent instance

        Raises:
            ValidationError: If content data is invalid
            DatabaseError: If database operation fails

        Example:
            >>> content = await service.create_content(
            ...     db=session,
            ...     user_id=1,
            ...     data={"title": "My Lesson", "content_type": "lesson"}
            ... )
        """
        pass
```

#### 4. Error Handling Standards
```python
from apps.backend.core.errors import (
    ValidationError,
    DatabaseError,
    ExternalServiceError
)

async def process_user_request(data: dict) -> dict:
    """Process user request with proper error handling."""
    try:
        # Validate input
        if not data.get('required_field'):
            raise ValidationError("Required field missing")

        # Database operation
        result = await database_operation(data)

        # External service call
        external_data = await external_service_call(result.id)

        return {"status": "success", "data": external_data}

    except ValidationError as e:
        logger.warning(f"Validation error: {e}")
        raise
    except DatabaseError as e:
        logger.error(f"Database error: {e}")
        raise
    except ExternalServiceError as e:
        logger.error(f"External service error: {e}")
        # Provide fallback or partial result
        return {"status": "partial", "error": str(e)}
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise DatabaseError("Internal processing error")
```

### API Design Standards

#### 1. Endpoint Naming
```python
# RESTful URL patterns
GET    /api/v1/content           # List content
POST   /api/v1/content           # Create content
GET    /api/v1/content/{id}      # Get specific content
PUT    /api/v1/content/{id}      # Update content
DELETE /api/v1/content/{id}      # Delete content

# Action-based endpoints
POST   /api/v1/content/{id}/publish    # Publish content
POST   /api/v1/content/{id}/duplicate  # Duplicate content
POST   /api/v1/content/generate        # Generate content
```

#### 2. Response Format Standards
```python
# Success response
{
    "status": "success",
    "data": { ... },
    "message": "Operation completed successfully",
    "metadata": {
        "timestamp": "2025-09-23T10:30:00Z",
        "request_id": "uuid-string",
        "execution_time": 0.123
    }
}

# Error response
{
    "status": "error",
    "data": null,
    "message": "Human readable error message",
    "metadata": {
        "timestamp": "2025-09-23T10:30:00Z",
        "request_id": "uuid-string",
        "error_code": "VALIDATION_ERROR",
        "details": { ... }
    }
}
```

## Debugging Guide

### Logging and Monitoring

#### 1. Structured Logging
```python
from apps.backend.core.logging import logger

# Context logging
logger.info(
    "User content created",
    extra={
        "user_id": user.id,
        "content_id": content.id,
        "content_type": content.type,
        "operation": "create_content"
    }
)

# Error logging with context
try:
    result = await risky_operation()
except Exception as e:
    logger.error(
        "Operation failed",
        extra={
            "error": str(e),
            "operation": "risky_operation",
            "user_id": user.id,
            "traceback": traceback.format_exc()
        }
    )
    raise
```

#### 2. Performance Monitoring
```python
from apps.backend.core.logging import log_execution_time

@log_execution_time
async def slow_operation():
    """Operation with execution time logging."""
    await asyncio.sleep(2)
    return "result"

# Manual timing
import time
start_time = time.time()
try:
    result = await operation()
    logger.info(
        "Operation completed",
        extra={
            "execution_time": time.time() - start_time,
            "operation": "manual_timing"
        }
    )
except Exception as e:
    logger.error(
        "Operation failed",
        extra={
            "execution_time": time.time() - start_time,
            "error": str(e)
        }
    )
    raise
```

### Debugging Tools

#### 1. Debug Endpoints
```python
@router.get("/debug/health", include_in_schema=False)
async def debug_health():
    """Debug endpoint for health checking."""
    return {
        "database": await check_database_connection(),
        "redis": await check_redis_connection(),
        "agents": await check_agent_status(),
        "external_services": await check_external_services()
    }

@router.get("/debug/config", include_in_schema=False)
async def debug_config():
    """Debug endpoint for configuration."""
    return {
        "environment": settings.ENVIRONMENT,
        "database_url": settings.DATABASE_URL.split('@')[1] if '@' in settings.DATABASE_URL else "hidden",
        "redis_connected": await redis_health_check(),
        "feature_flags": get_feature_flags()
    }
```

#### 2. Development Utilities
```python
# apps/backend/utils/debug.py
import inspect
from typing import Any

def debug_print(obj: Any, name: str = None):
    """Enhanced debug printing."""
    frame = inspect.currentframe().f_back
    if not name:
        name = f"{frame.f_code.co_filename}:{frame.f_lineno}"

    print(f"DEBUG [{name}]: {type(obj).__name__} = {obj}")

async def debug_request(request):
    """Debug request information."""
    return {
        "method": request.method,
        "url": str(request.url),
        "headers": dict(request.headers),
        "path_params": request.path_params,
        "query_params": dict(request.query_params),
        "client": request.client.host if request.client else None
    }
```

## Performance Optimization

### Database Optimization

#### 1. Query Optimization
```python
from sqlalchemy import select
from sqlalchemy.orm import selectinload, joinedload

# Eager loading relationships
async def get_content_with_user(db: AsyncSession, content_id: int):
    """Get content with user information efficiently."""
    query = select(EducationalContent).options(
        joinedload(EducationalContent.user)
    ).where(EducationalContent.id == content_id)

    result = await db.execute(query)
    return result.scalar_one_or_none()

# Batch loading
async def get_multiple_content_with_users(db: AsyncSession, content_ids: List[int]):
    """Get multiple content items with users efficiently."""
    query = select(EducationalContent).options(
        selectinload(EducationalContent.user)
    ).where(EducationalContent.id.in_(content_ids))

    result = await db.execute(query)
    return result.scalars().all()
```

#### 2. Connection Pooling
```python
# In core/database.py
from sqlalchemy.ext.asyncio import create_async_engine

engine = create_async_engine(
    DATABASE_URL,
    pool_size=20,                    # Number of connections to maintain
    max_overflow=30,                 # Additional connections when needed
    pool_timeout=30,                 # Seconds to wait for connection
    pool_recycle=3600,              # Recycle connections every hour
    pool_pre_ping=True,             # Validate connections before use
    echo=False                      # Set to True for SQL logging
)
```

#### 3. Caching Strategies
```python
from functools import wraps
import json
import hashlib

def cache_result(expiration: int = 300):
    """Cache function result in Redis."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Create cache key
            key_data = f"{func.__name__}:{args}:{kwargs}"
            cache_key = hashlib.md5(key_data.encode()).hexdigest()

            # Try to get from cache
            cached = await redis_client.get(cache_key)
            if cached:
                return json.loads(cached)

            # Execute function and cache result
            result = await func(*args, **kwargs)
            await redis_client.setex(
                cache_key,
                expiration,
                json.dumps(result, default=str)
            )

            return result
        return wrapper
    return decorator

@cache_result(expiration=600)
async def get_user_analytics(user_id: int):
    """Get user analytics with caching."""
    # Expensive computation here
    return analytics_data
```

This comprehensive developer guide provides the foundation for building robust, maintainable, and scalable features within the ToolboxAI backend architecture.