# ToolBoxAI Supabase Migration System - Integration Guide

## Table of Contents

1. [Integration Architecture](#integration-architecture)
2. [SPARC Framework Integration](#sparc-framework-integration)
3. [Database Integration](#database-integration)
4. [Environment Configuration](#environment-configuration)
5. [Docker Integration](#docker-integration)
6. [API Integration](#api-integration)
7. [CI/CD Integration](#cicd-integration)
8. [Monitoring Integration](#monitoring-integration)

## Integration Architecture

### System Overview

The ToolBoxAI Supabase Migration System integrates with multiple components of the platform to provide seamless database migration capabilities.

```mermaid
graph TB
    subgraph "ToolBoxAI Platform"
        A[FastAPI Backend] --> B[Migration Agent]
        C[React Dashboard] --> A
        D[SPARC Framework] --> B
        E[State Manager] --> D
        F[Task Coordinator] --> E
    end

    subgraph "Migration System"
        B --> G[Schema Analyzer]
        B --> H[RLS Generator]
        B --> I[Data Migrator]
        B --> J[Edge Function Converter]
    end

    subgraph "External Systems"
        K[Source PostgreSQL] --> G
        L[Supabase] --> H
        L --> I
        L --> J
        M[Monitoring] --> B
        N[Logging] --> B
    end

    subgraph "Storage & State"
        O[Redis Cache] --> E
        P[File Storage] --> I
        Q[Migration Logs] --> N
    end
```

### Integration Points

| Component | Integration Type | Purpose | Configuration |
|-----------|------------------|---------|---------------|
| **SPARC Framework** | Core Architecture | Structured reasoning and state management | `core/sparc/` |
| **FastAPI Backend** | API Integration | Migration endpoints and orchestration | `apps/backend/api/v1/endpoints/` |
| **Database Layer** | Data Access | PostgreSQL and Supabase connections | `database/` |
| **Redis Cache** | State Persistence | Migration state and progress tracking | Redis configuration |
| **Docker** | Containerization | Consistent deployment environment | `infrastructure/docker/` |
| **Monitoring** | Observability | Migration monitoring and alerting | Sentry, Prometheus |

## SPARC Framework Integration

### Overview

The Supabase Migration Agent integrates deeply with the SPARC (Structured Patterns and Reasoning for Coordination) framework to provide intelligent decision-making throughout the migration process.

### SPARC Components Integration

#### 1. State Manager Integration

```python
# core/agents/supabase/supabase_migration_agent.py

from core.sparc.state_manager import StateManager
from core.sparc.sparc_model import SPARCOutput

class SupabaseMigrationAgent(BaseAgent):
    def __init__(self, state_manager: Optional[StateManager] = None, **kwargs):
        super().__init__(
            name="SupabaseMigrationAgent",
            description="Orchestrates PostgreSQL to Supabase migration",
            state_manager=state_manager,
            **kwargs
        )

    async def _sparc_reasoning(
        self,
        observation: Dict[str, Any],
        context: Dict[str, Any]
    ) -> SPARCOutput:
        """Apply SPARC framework for migration planning."""
        return await self.apply_sparc_framework(
            observation=observation,
            action="generate_migration_plan",
            context=context
        )
```

#### 2. Task Coordination Integration

```python
# Integration with task coordinator
from core.coordinators.base_coordinator import TaskOutput

async def process_task(self, task: str, context: Dict[str, Any]) -> TaskOutput:
    """Process migration tasks through SPARC coordination."""

    # Update SPARC state
    self.state_manager.update_state({
        'current_task': task,
        'task_context': context,
        'status': 'processing'
    })

    # Apply SPARC reasoning
    sparc_output = await self._sparc_reasoning(
        observation={'task': task, 'context': context},
        context={'agent': self.name}
    )

    # Execute based on SPARC decision
    if sparc_output.reasoning.confidence > 0.8:
        result = await self._execute_task(task, context)
    else:
        result = await self._request_human_input(task, context)

    return TaskOutput(
        success=True,
        result=result,
        metadata={'sparc_confidence': sparc_output.reasoning.confidence}
    )
```

#### 3. State Persistence

```python
# core/sparc/enhanced_orchestrator.py integration

class MigrationStateManager:
    """Enhanced state management for migration operations."""

    def __init__(self, redis_client):
        self.redis = redis_client
        self.state_key_prefix = "migration:state:"

    async def save_migration_state(
        self,
        migration_id: str,
        state: Dict[str, Any]
    ):
        """Persist migration state to Redis."""
        key = f"{self.state_key_prefix}{migration_id}"
        await self.redis.hset(key, mapping={
            'state': json.dumps(state),
            'timestamp': datetime.utcnow().isoformat(),
            'phase': state.get('current_phase', 'unknown')
        })

    async def load_migration_state(self, migration_id: str) -> Dict[str, Any]:
        """Load migration state from Redis."""
        key = f"{self.state_key_prefix}{migration_id}"
        state_data = await self.redis.hgetall(key)

        if state_data:
            return {
                'state': json.loads(state_data['state']),
                'timestamp': state_data['timestamp'],
                'phase': state_data['phase']
            }
        return {}
```

### SPARC Configuration

```python
# Configuration for SPARC integration
SPARC_CONFIG = {
    "reasoning_engine": {
        "confidence_threshold": 0.8,
        "max_iterations": 10,
        "timeout_seconds": 300
    },
    "state_management": {
        "persistence_backend": "redis",
        "state_ttl_hours": 24,
        "checkpoint_interval": 300
    },
    "coordination": {
        "max_concurrent_tasks": 5,
        "task_timeout_seconds": 3600,
        "retry_attempts": 3
    }
}
```

## Database Integration

### Connection Management

#### 1. Multi-Database Connection Setup

```python
# database/connection.py integration

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
import asyncpg
from supabase import create_client, Client

class MigrationDatabaseManager:
    """Manages database connections for migration operations."""

    def __init__(self):
        self.source_engine = None
        self.target_engine = None
        self.supabase_client = None

    async def initialize_connections(self, config: Dict[str, Any]):
        """Initialize all database connections."""

        # Source PostgreSQL connection
        self.source_engine = create_async_engine(
            config['source_database_url'],
            pool_size=5,
            max_overflow=10,
            pool_pre_ping=True
        )

        # Target PostgreSQL connection (Supabase)
        self.target_engine = create_async_engine(
            config['target_database_url'],
            pool_size=5,
            max_overflow=10,
            pool_pre_ping=True
        )

        # Supabase API client
        self.supabase_client = create_client(
            config['supabase_url'],
            config['supabase_service_role_key']
        )

    async def get_source_session(self) -> AsyncSession:
        """Get async session for source database."""
        async_session = sessionmaker(
            self.source_engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
        return async_session()

    async def get_target_session(self) -> AsyncSession:
        """Get async session for target database."""
        async_session = sessionmaker(
            self.target_engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
        return async_session()

    def get_supabase_client(self) -> Client:
        """Get Supabase client."""
        return self.supabase_client
```

#### 2. Database Model Integration

```python
# database/models.py integration with migration

from database.models import (
    User, Class, Lesson, Quiz,
    EducationalContent, StudentProgress
)

class MigrationModelMapper:
    """Maps ToolBoxAI models to Supabase schema."""

    @staticmethod
    def get_model_mappings() -> Dict[str, Any]:
        """Get model to table mappings for migration."""
        return {
            'users': {
                'model': User,
                'supabase_table': 'users',
                'rls_policies': ['user_own_data', 'admin_all_data'],
                'realtime_enabled': True
            },
            'classes': {
                'model': Class,
                'supabase_table': 'classes',
                'rls_policies': ['teacher_own_classes', 'student_enrolled_classes'],
                'realtime_enabled': True
            },
            'lessons': {
                'model': Lesson,
                'supabase_table': 'lessons',
                'rls_policies': ['content_access_policy'],
                'realtime_enabled': False
            },
            'educational_content': {
                'model': EducationalContent,
                'supabase_table': 'educational_content',
                'rls_policies': ['content_visibility_policy'],
                'realtime_enabled': False,
                'vector_columns': ['content_embedding']
            }
        }

    @staticmethod
    def generate_supabase_schema(model_class) -> Dict[str, Any]:
        """Generate Supabase schema from SQLAlchemy model."""
        columns = []

        for column in model_class.__table__.columns:
            supabase_column = {
                'name': column.name,
                'type': str(column.type),
                'nullable': column.nullable,
                'primary_key': column.primary_key,
                'default': str(column.default) if column.default else None
            }
            columns.append(supabase_column)

        return {
            'table_name': model_class.__tablename__,
            'columns': columns,
            'indexes': [str(idx) for idx in model_class.__table__.indexes],
            'foreign_keys': [str(fk) for fk in model_class.__table__.foreign_keys]
        }
```

### Schema Synchronization

```python
# Schema synchronization between ToolBoxAI and Supabase

class SchemaSynchronizer:
    """Synchronizes schema changes between ToolBoxAI and Supabase."""

    def __init__(self, migration_agent: SupabaseMigrationAgent):
        self.migration_agent = migration_agent

    async def sync_schema_changes(self, models: List[Any]):
        """Sync schema changes to Supabase."""

        for model in models:
            # Detect schema changes
            current_schema = await self.get_current_schema(model)
            target_schema = MigrationModelMapper.generate_supabase_schema(model)

            changes = self.detect_changes(current_schema, target_schema)

            if changes:
                # Generate migration for changes
                migration_sql = self.generate_migration_sql(changes)

                # Apply migration through agent
                await self.migration_agent.apply_schema_migration(
                    table_name=model.__tablename__,
                    migration_sql=migration_sql
                )

    def detect_changes(self, current: Dict, target: Dict) -> List[Dict]:
        """Detect schema changes between current and target."""
        changes = []

        # Compare columns
        current_columns = {col['name']: col for col in current.get('columns', [])}
        target_columns = {col['name']: col for col in target.get('columns', [])}

        # New columns
        for col_name, col_def in target_columns.items():
            if col_name not in current_columns:
                changes.append({
                    'type': 'add_column',
                    'column': col_def
                })

        # Modified columns
        for col_name, col_def in target_columns.items():
            if col_name in current_columns:
                current_col = current_columns[col_name]
                if current_col['type'] != col_def['type']:
                    changes.append({
                        'type': 'modify_column',
                        'column': col_def,
                        'old_column': current_col
                    })

        return changes
```

## Environment Configuration

### 1. Environment Variables

```bash
# .env configuration for migration system integration

# ToolBoxAI Database (Source)
TOOLBOXAI_DATABASE_URL=postgresql://user:pass@localhost:5432/toolboxai_dev
TOOLBOXAI_DATABASE_NAME=toolboxai_production

# Supabase Configuration (Target)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=eyJ...
SUPABASE_SERVICE_ROLE_KEY=eyJ...
SUPABASE_DB_PASSWORD=your_db_password

# Redis Configuration (SPARC State)
REDIS_URL=redis://localhost:6379
REDIS_MIGRATION_DB=1
REDIS_TTL_HOURS=24

# Migration Configuration
MIGRATION_BATCH_SIZE=1000
MIGRATION_PARALLEL_WORKERS=4
MIGRATION_TIMEOUT_SECONDS=3600
ENABLE_MIGRATION_LOGGING=true
MIGRATION_LOG_LEVEL=INFO

# AI Configuration
OPENAI_API_KEY=sk-...
USE_MOCK_LLM=false
AI_REASONING_TIMEOUT=300

# Monitoring Configuration
SENTRY_DSN=https://...
ENABLE_METRICS=true
METRICS_PORT=9090

# Security Configuration
ENABLE_AUDIT_LOGGING=true
AUDIT_LOG_RETENTION_DAYS=90
ENCRYPT_MIGRATION_LOGS=true
```

### 2. Configuration Management

```python
# toolboxai_settings/settings.py integration

from pydantic import BaseSettings, Field
from typing import Optional, Dict, Any

class MigrationSettings(BaseSettings):
    """Settings for Supabase migration system."""

    # Database Configuration
    source_database_url: str = Field(..., env="TOOLBOXAI_DATABASE_URL")
    target_database_url: str = Field(..., env="SUPABASE_DATABASE_URL")
    supabase_url: str = Field(..., env="SUPABASE_URL")
    supabase_service_role_key: str = Field(..., env="SUPABASE_SERVICE_ROLE_KEY")

    # Migration Configuration
    batch_size: int = Field(1000, env="MIGRATION_BATCH_SIZE")
    parallel_workers: int = Field(4, env="MIGRATION_PARALLEL_WORKERS")
    timeout_seconds: int = Field(3600, env="MIGRATION_TIMEOUT_SECONDS")
    enable_dry_run: bool = Field(True, env="ENABLE_DRY_RUN")

    # SPARC Configuration
    redis_url: str = Field("redis://localhost:6379", env="REDIS_URL")
    redis_migration_db: int = Field(1, env="REDIS_MIGRATION_DB")
    state_ttl_hours: int = Field(24, env="REDIS_TTL_HOURS")

    # AI Configuration
    openai_api_key: Optional[str] = Field(None, env="OPENAI_API_KEY")
    use_mock_llm: bool = Field(False, env="USE_MOCK_LLM")
    ai_reasoning_timeout: int = Field(300, env="AI_REASONING_TIMEOUT")

    # Security Configuration
    enable_audit_logging: bool = Field(True, env="ENABLE_AUDIT_LOGGING")
    encrypt_migration_logs: bool = Field(True, env="ENCRYPT_MIGRATION_LOGS")

    class Config:
        env_file = ".env"
        case_sensitive = False

# Global settings instance
migration_settings = MigrationSettings()
```

### 3. Configuration Validation

```python
# Configuration validation and health checks

class ConfigurationValidator:
    """Validates migration configuration."""

    @staticmethod
    async def validate_configuration(settings: MigrationSettings) -> Dict[str, Any]:
        """Validate all configuration parameters."""

        validation_results = {
            'valid': True,
            'errors': [],
            'warnings': []
        }

        # Database connectivity
        try:
            await test_database_connection(settings.source_database_url)
        except Exception as e:
            validation_results['errors'].append(f"Source database connection failed: {e}")
            validation_results['valid'] = False

        try:
            await test_supabase_connection(settings.supabase_url, settings.supabase_service_role_key)
        except Exception as e:
            validation_results['errors'].append(f"Supabase connection failed: {e}")
            validation_results['valid'] = False

        # Redis connectivity
        try:
            await test_redis_connection(settings.redis_url)
        except Exception as e:
            validation_results['errors'].append(f"Redis connection failed: {e}")
            validation_results['valid'] = False

        # AI service availability
        if settings.openai_api_key and not settings.use_mock_llm:
            try:
                await test_openai_connection(settings.openai_api_key)
            except Exception as e:
                validation_results['warnings'].append(f"OpenAI connection issue: {e}")

        return validation_results

async def test_database_connection(database_url: str):
    """Test PostgreSQL database connection."""
    engine = create_async_engine(database_url)
    async with engine.begin() as conn:
        await conn.execute("SELECT 1")
    await engine.dispose()

async def test_supabase_connection(url: str, service_key: str):
    """Test Supabase connection."""
    client = create_client(url, service_key)
    response = await client.from('_test').select('*').limit(1).execute()
    if response.error and response.error.code != 'PGRST116':
        raise Exception(f"Supabase connection failed: {response.error}")

async def test_redis_connection(redis_url: str):
    """Test Redis connection."""
    import aioredis
    redis = aioredis.from_url(redis_url)
    await redis.ping()
    await redis.close()
```

## Docker Integration

### 1. Migration Service Container

```dockerfile
# infrastructure/docker/migration-service.Dockerfile

FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY core/ ./core/
COPY database/ ./database/
COPY toolboxai_settings/ ./toolboxai_settings/

# Copy migration scripts
COPY scripts/migration/ ./scripts/migration/

# Set environment variables
ENV PYTHONPATH=/app
ENV MIGRATION_SERVICE=true

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python scripts/migration/health_check.py

# Default command
CMD ["python", "-m", "core.agents.supabase.migration_service"]
```

### 2. Docker Compose Integration

```yaml
# infrastructure/docker/docker-compose.migration.yml

version: '3.8'

services:
  migration-service:
    build:
      context: ../../
      dockerfile: infrastructure/docker/migration-service.Dockerfile
    environment:
      - TOOLBOXAI_DATABASE_URL=${TOOLBOXAI_DATABASE_URL}
      - SUPABASE_URL=${SUPABASE_URL}
      - SUPABASE_SERVICE_ROLE_KEY=${SUPABASE_SERVICE_ROLE_KEY}
      - REDIS_URL=redis://redis:6379
      - MIGRATION_BATCH_SIZE=${MIGRATION_BATCH_SIZE:-1000}
      - LOG_LEVEL=${LOG_LEVEL:-INFO}
    depends_on:
      - redis
      - postgres
    volumes:
      - migration_logs:/app/logs
      - migration_backups:/app/backups
    networks:
      - toolboxai_network

  redis:
    image: redis:7-alpine
    command: redis-server --appendonly yes
    volumes:
      - redis_migration_data:/data
    networks:
      - toolboxai_network

  postgres:
    image: postgres:15-alpine
    environment:
      - POSTGRES_DB=${POSTGRES_DB:-toolboxai_dev}
      - POSTGRES_USER=${POSTGRES_USER:-toolboxai}
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./init-scripts:/docker-entrypoint-initdb.d
    networks:
      - toolboxai_network

volumes:
  migration_logs:
  migration_backups:
  redis_migration_data:
  postgres_data:

networks:
  toolboxai_network:
    driver: bridge
```

### 3. Migration Service Implementation

```python
# core/agents/supabase/migration_service.py

import asyncio
import logging
from fastapi import FastAPI, BackgroundTasks
from typing import Dict, Any
import uvicorn

from core.agents.supabase import SupabaseMigrationAgent
from toolboxai_settings.settings import migration_settings

# Initialize FastAPI app
app = FastAPI(
    title="ToolBoxAI Migration Service",
    description="Supabase migration service",
    version="1.0.0"
)

# Global migration agent instance
migration_agent = None

@app.on_event("startup")
async def startup_event():
    """Initialize migration service."""
    global migration_agent

    # Validate configuration
    config_validation = await ConfigurationValidator.validate_configuration(migration_settings)
    if not config_validation['valid']:
        logging.error(f"Configuration validation failed: {config_validation['errors']}")
        raise Exception("Invalid configuration")

    # Initialize migration agent
    migration_agent = SupabaseMigrationAgent()
    logging.info("Migration service initialized successfully")

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "migration-service",
        "agent_status": "ready" if migration_agent else "not_initialized"
    }

@app.post("/api/v1/migration/analyze")
async def analyze_database(request: Dict[str, Any]):
    """Analyze source database."""
    try:
        analysis = await migration_agent.analyze_database(
            connection_string=request['connection_string'],
            database_name=request['database_name']
        )
        return {"status": "success", "data": analysis}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/api/v1/migration/plan")
async def generate_migration_plan(request: Dict[str, Any]):
    """Generate migration plan."""
    try:
        plan = await migration_agent.generate_migration_plan(
            analysis_results=request['analysis_results'],
            migration_options=request.get('migration_options', {})
        )
        return {"status": "success", "data": plan}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/api/v1/migration/execute")
async def execute_migration(request: Dict[str, Any], background_tasks: BackgroundTasks):
    """Execute migration."""
    try:
        # Execute migration in background
        background_tasks.add_task(
            _execute_migration_background,
            request['plan'],
            request.get('dry_run', True)
        )
        return {"status": "started", "message": "Migration started in background"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

async def _execute_migration_background(plan: Dict[str, Any], dry_run: bool):
    """Execute migration in background."""
    try:
        results = await migration_agent.execute_migration(plan, dry_run)
        logging.info(f"Migration completed with status: {results['status']}")
    except Exception as e:
        logging.error(f"Migration failed: {e}")

if __name__ == "__main__":
    uvicorn.run(
        "migration_service:app",
        host="0.0.0.0",
        port=8010,
        log_level="info"
    )
```

## API Integration

### 1. FastAPI Backend Integration

```python
# apps/backend/api/v1/endpoints/migration.py

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from typing import Dict, Any, Optional
from pydantic import BaseModel

from core.agents.supabase import SupabaseMigrationAgent
from apps.backend.core.auth import get_current_admin_user
from apps.backend.core.monitoring.metrics import track_migration_metrics

router = APIRouter(prefix="/migration", tags=["Migration"])

class MigrationAnalysisRequest(BaseModel):
    connection_string: str
    database_name: str
    options: Optional[Dict[str, Any]] = {}

class MigrationPlanRequest(BaseModel):
    analysis_results: Dict[str, Any]
    migration_options: Optional[Dict[str, Any]] = {}

class MigrationExecutionRequest(BaseModel):
    plan: Dict[str, Any]
    dry_run: bool = True
    notification_webhook: Optional[str] = None

@router.post("/analyze")
async def analyze_database(
    request: MigrationAnalysisRequest,
    current_user = Depends(get_current_admin_user)
):
    """Analyze source database for migration."""

    try:
        # Initialize migration agent
        agent = SupabaseMigrationAgent()

        # Track metrics
        with track_migration_metrics("database_analysis"):
            analysis = await agent.analyze_database(
                connection_string=request.connection_string,
                database_name=request.database_name
            )

        return {
            "status": "success",
            "data": analysis,
            "metadata": {
                "analyzed_by": current_user.id,
                "timestamp": datetime.utcnow().isoformat()
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/plan")
async def generate_migration_plan(
    request: MigrationPlanRequest,
    current_user = Depends(get_current_admin_user)
):
    """Generate comprehensive migration plan."""

    try:
        agent = SupabaseMigrationAgent()

        with track_migration_metrics("migration_planning"):
            plan = await agent.generate_migration_plan(
                analysis_results=request.analysis_results,
                migration_options=request.migration_options
            )

        return {
            "status": "success",
            "data": plan,
            "metadata": {
                "planned_by": current_user.id,
                "timestamp": datetime.utcnow().isoformat()
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/execute")
async def execute_migration(
    request: MigrationExecutionRequest,
    background_tasks: BackgroundTasks,
    current_user = Depends(get_current_admin_user)
):
    """Execute migration plan."""

    # Generate migration ID
    migration_id = f"mig_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{current_user.id}"

    # Start migration in background
    background_tasks.add_task(
        _execute_migration_background,
        migration_id=migration_id,
        plan=request.plan,
        dry_run=request.dry_run,
        user_id=current_user.id,
        webhook_url=request.notification_webhook
    )

    return {
        "status": "started",
        "migration_id": migration_id,
        "message": "Migration started in background",
        "metadata": {
            "initiated_by": current_user.id,
            "dry_run": request.dry_run,
            "timestamp": datetime.utcnow().isoformat()
        }
    }

async def _execute_migration_background(
    migration_id: str,
    plan: Dict[str, Any],
    dry_run: bool,
    user_id: str,
    webhook_url: Optional[str] = None
):
    """Execute migration in background with notifications."""

    agent = SupabaseMigrationAgent()

    try:
        with track_migration_metrics("migration_execution"):
            results = await agent.execute_migration(plan, dry_run)

        # Send notification
        if webhook_url:
            await send_migration_notification(
                webhook_url=webhook_url,
                migration_id=migration_id,
                status=results['status'],
                results=results
            )

        # Log completion
        logging.info(f"Migration {migration_id} completed: {results['status']}")

    except Exception as e:
        logging.error(f"Migration {migration_id} failed: {e}")

        if webhook_url:
            await send_migration_notification(
                webhook_url=webhook_url,
                migration_id=migration_id,
                status="failed",
                error=str(e)
            )

@router.get("/status/{migration_id}")
async def get_migration_status(
    migration_id: str,
    current_user = Depends(get_current_admin_user)
):
    """Get migration status and progress."""

    # Retrieve status from Redis/state manager
    state_manager = StateManager()
    status = await state_manager.get_migration_status(migration_id)

    if not status:
        raise HTTPException(status_code=404, detail="Migration not found")

    return {
        "status": "success",
        "data": status
    }
```

### 2. WebSocket Integration for Real-time Updates

```python
# apps/backend/api/v1/endpoints/migration_websocket.py

from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, Set
import json
import asyncio

# Active WebSocket connections
migration_connections: Dict[str, Set[WebSocket]] = {}

@router.websocket("/ws/migration/{migration_id}")
async def migration_websocket(websocket: WebSocket, migration_id: str):
    """WebSocket endpoint for real-time migration updates."""

    await websocket.accept()

    # Add connection to tracking
    if migration_id not in migration_connections:
        migration_connections[migration_id] = set()
    migration_connections[migration_id].add(websocket)

    try:
        # Send initial status
        state_manager = StateManager()
        initial_status = await state_manager.get_migration_status(migration_id)

        if initial_status:
            await websocket.send_text(json.dumps({
                "type": "status_update",
                "data": initial_status
            }))

        # Keep connection alive and handle incoming messages
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)

            if message.get("type") == "ping":
                await websocket.send_text(json.dumps({"type": "pong"}))

    except WebSocketDisconnect:
        # Remove connection
        migration_connections[migration_id].discard(websocket)
        if not migration_connections[migration_id]:
            del migration_connections[migration_id]

async def broadcast_migration_update(migration_id: str, update: Dict[str, Any]):
    """Broadcast migration update to all connected clients."""

    if migration_id in migration_connections:
        message = json.dumps({
            "type": "progress_update",
            "data": update
        })

        # Send to all connected clients
        for websocket in migration_connections[migration_id].copy():
            try:
                await websocket.send_text(message)
            except:
                # Remove failed connections
                migration_connections[migration_id].discard(websocket)
```

## CI/CD Integration

### 1. GitHub Actions Integration

```yaml
# .github/workflows/migration-test.yml

name: Migration System Tests

on:
  push:
    branches: [ main, develop ]
    paths:
      - 'core/agents/supabase/**'
      - 'tests/migration/**'
  pull_request:
    branches: [ main ]
    paths:
      - 'core/agents/supabase/**'

jobs:
  migration-tests:
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: postgres
          POSTGRES_DB: test_migration
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432

      redis:
        image: redis:7
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 6379:6379

    steps:
    - uses: actions/checkout@v3

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'

    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install -r requirements-test.txt

    - name: Set up test database
      run: |
        psql -h localhost -U postgres -d test_migration -c "
          CREATE EXTENSION IF NOT EXISTS vector;
          CREATE EXTENSION IF NOT EXISTS pg_stat_statements;
        "
      env:
        PGPASSWORD: postgres

    - name: Run migration tests
      run: |
        pytest tests/migration/ -v --cov=core.agents.supabase
      env:
        DATABASE_URL: postgresql://postgres:postgres@localhost:5432/test_migration
        REDIS_URL: redis://localhost:6379
        USE_MOCK_LLM: true
        ENABLE_MIGRATION_TESTING: true

    - name: Upload coverage reports
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
        flags: migration
        name: migration-tests
```

### 2. Deployment Pipeline Integration

```yaml
# .github/workflows/deploy-migration.yml

name: Deploy Migration Service

on:
  push:
    branches: [ main ]
    paths:
      - 'core/agents/supabase/**'
      - 'infrastructure/docker/migration-service.Dockerfile'

jobs:
  deploy:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v3

    - name: Build migration service image
      run: |
        docker build -f infrastructure/docker/migration-service.Dockerfile \
          -t toolboxai/migration-service:${{ github.sha }} \
          -t toolboxai/migration-service:latest .

    - name: Push to registry
      run: |
        echo ${{ secrets.DOCKER_PASSWORD }} | docker login -u ${{ secrets.DOCKER_USERNAME }} --password-stdin
        docker push toolboxai/migration-service:${{ github.sha }}
        docker push toolboxai/migration-service:latest

    - name: Deploy to staging
      run: |
        # Deploy to staging environment
        kubectl set image deployment/migration-service \
          migration-service=toolboxai/migration-service:${{ github.sha }} \
          -n staging

    - name: Run integration tests
      run: |
        # Wait for deployment
        kubectl rollout status deployment/migration-service -n staging

        # Run integration tests
        python tests/integration/test_migration_service.py
      env:
        KUBE_CONFIG: ${{ secrets.KUBE_CONFIG }}
        STAGING_API_URL: ${{ secrets.STAGING_API_URL }}
```

## Monitoring Integration

### 1. Metrics and Observability

```python
# core/agents/supabase/monitoring.py

from prometheus_client import Counter, Histogram, Gauge
import time
from contextlib import contextmanager
from typing import Dict, Any

# Prometheus metrics
migration_counter = Counter(
    'toolboxai_migrations_total',
    'Total number of migrations executed',
    ['status', 'migration_type']
)

migration_duration = Histogram(
    'toolboxai_migration_duration_seconds',
    'Migration execution duration',
    ['phase', 'status']
)

migration_progress = Gauge(
    'toolboxai_migration_progress_percent',
    'Current migration progress percentage',
    ['migration_id', 'phase']
)

schema_analysis_duration = Histogram(
    'toolboxai_schema_analysis_duration_seconds',
    'Schema analysis duration'
)

class MigrationMonitoring:
    """Monitoring and metrics collection for migrations."""

    @staticmethod
    @contextmanager
    def track_migration_phase(phase: str, migration_id: str):
        """Track migration phase execution."""
        start_time = time.time()
        status = 'success'

        try:
            yield
        except Exception as e:
            status = 'error'
            raise
        finally:
            duration = time.time() - start_time
            migration_duration.labels(phase=phase, status=status).observe(duration)

    @staticmethod
    def update_migration_progress(migration_id: str, phase: str, progress: float):
        """Update migration progress metrics."""
        migration_progress.labels(migration_id=migration_id, phase=phase).set(progress)

    @staticmethod
    def record_migration_completion(status: str, migration_type: str):
        """Record migration completion."""
        migration_counter.labels(status=status, migration_type=migration_type).inc()

# Integration with migration agent
class MonitoredSupabaseMigrationAgent(SupabaseMigrationAgent):
    """Migration agent with monitoring integration."""

    async def execute_migration(self, plan, dry_run=True):
        """Execute migration with monitoring."""

        migration_id = f"mig_{int(time.time())}"

        try:
            with MigrationMonitoring.track_migration_phase("execution", migration_id):
                results = await super().execute_migration(plan, dry_run)

            MigrationMonitoring.record_migration_completion(
                status=results['status'],
                migration_type='full_migration'
            )

            return results

        except Exception as e:
            MigrationMonitoring.record_migration_completion(
                status='failed',
                migration_type='full_migration'
            )
            raise

    async def analyze_database(self, connection_string, database_name):
        """Analyze database with monitoring."""

        with schema_analysis_duration.time():
            return await super().analyze_database(connection_string, database_name)
```

### 2. Logging Integration

```python
# core/agents/supabase/logging_config.py

import logging
import structlog
from pythonjsonlogger import jsonlogger
import sys

def configure_migration_logging():
    """Configure structured logging for migration operations."""

    # Configure structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # Configure JSON formatter for structured logs
    formatter = jsonlogger.JsonFormatter(
        '%(asctime)s %(name)s %(levelname)s %(message)s'
    )

    # Create handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    # Configure migration logger
    migration_logger = logging.getLogger('migration')
    migration_logger.addHandler(handler)
    migration_logger.setLevel(logging.INFO)

# Migration-specific logger
migration_logger = structlog.get_logger('migration')

class MigrationLogger:
    """Enhanced logging for migration operations."""

    @staticmethod
    def log_migration_start(migration_id: str, plan_summary: Dict[str, Any]):
        """Log migration start."""
        migration_logger.info(
            "Migration started",
            migration_id=migration_id,
            tables_count=len(plan_summary.get('schema_mappings', {})),
            estimated_duration=plan_summary.get('estimated_duration'),
            risk_level=plan_summary.get('risk_assessment', {}).get('level')
        )

    @staticmethod
    def log_phase_completion(migration_id: str, phase: str, result: Dict[str, Any]):
        """Log phase completion."""
        migration_logger.info(
            "Migration phase completed",
            migration_id=migration_id,
            phase=phase,
            status=result.get('status'),
            duration_seconds=result.get('duration'),
            items_processed=result.get('items_processed')
        )

    @staticmethod
    def log_migration_error(migration_id: str, phase: str, error: Exception):
        """Log migration error."""
        migration_logger.error(
            "Migration error occurred",
            migration_id=migration_id,
            phase=phase,
            error_type=type(error).__name__,
            error_message=str(error),
            exc_info=True
        )
```

### 3. Health Checks and Alerting

```python
# core/agents/supabase/health_checks.py

from typing import Dict, Any, List
import asyncio
from dataclasses import dataclass
from enum import Enum

class HealthStatus(Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"

@dataclass
class HealthCheck:
    name: str
    status: HealthStatus
    message: str
    details: Dict[str, Any] = None

class MigrationHealthChecker:
    """Health checker for migration system components."""

    async def check_all_components(self) -> Dict[str, Any]:
        """Check health of all migration components."""

        checks = await asyncio.gather(
            self.check_database_connectivity(),
            self.check_supabase_connectivity(),
            self.check_redis_connectivity(),
            self.check_ai_service_connectivity(),
            return_exceptions=True
        )

        health_status = HealthStatus.HEALTHY
        failed_checks = []

        for check in checks:
            if isinstance(check, Exception):
                failed_checks.append(str(check))
                health_status = HealthStatus.UNHEALTHY
            elif check.status != HealthStatus.HEALTHY:
                failed_checks.append(f"{check.name}: {check.message}")
                if check.status == HealthStatus.UNHEALTHY:
                    health_status = HealthStatus.UNHEALTHY
                elif health_status == HealthStatus.HEALTHY:
                    health_status = HealthStatus.DEGRADED

        return {
            "status": health_status.value,
            "checks": [check for check in checks if not isinstance(check, Exception)],
            "failed_checks": failed_checks,
            "timestamp": datetime.utcnow().isoformat()
        }

    async def check_database_connectivity(self) -> HealthCheck:
        """Check source database connectivity."""
        try:
            # Test database connection
            await test_database_connection(migration_settings.source_database_url)
            return HealthCheck(
                name="source_database",
                status=HealthStatus.HEALTHY,
                message="Database connection healthy"
            )
        except Exception as e:
            return HealthCheck(
                name="source_database",
                status=HealthStatus.UNHEALTHY,
                message=f"Database connection failed: {e}"
            )

    async def check_supabase_connectivity(self) -> HealthCheck:
        """Check Supabase connectivity."""
        try:
            await test_supabase_connection(
                migration_settings.supabase_url,
                migration_settings.supabase_service_role_key
            )
            return HealthCheck(
                name="supabase",
                status=HealthStatus.HEALTHY,
                message="Supabase connection healthy"
            )
        except Exception as e:
            return HealthCheck(
                name="supabase",
                status=HealthStatus.UNHEALTHY,
                message=f"Supabase connection failed: {e}"
            )

    async def check_redis_connectivity(self) -> HealthCheck:
        """Check Redis connectivity."""
        try:
            await test_redis_connection(migration_settings.redis_url)
            return HealthCheck(
                name="redis",
                status=HealthStatus.HEALTHY,
                message="Redis connection healthy"
            )
        except Exception as e:
            return HealthCheck(
                name="redis",
                status=HealthStatus.UNHEALTHY,
                message=f"Redis connection failed: {e}"
            )

    async def check_ai_service_connectivity(self) -> HealthCheck:
        """Check AI service connectivity."""
        if migration_settings.use_mock_llm:
            return HealthCheck(
                name="ai_service",
                status=HealthStatus.HEALTHY,
                message="Using mock LLM (no external service required)"
            )

        try:
            if migration_settings.openai_api_key:
                await test_openai_connection(migration_settings.openai_api_key)
                return HealthCheck(
                    name="ai_service",
                    status=HealthStatus.HEALTHY,
                    message="AI service connection healthy"
                )
            else:
                return HealthCheck(
                    name="ai_service",
                    status=HealthStatus.DEGRADED,
                    message="No AI service configured"
                )
        except Exception as e:
            return HealthCheck(
                name="ai_service",
                status=HealthStatus.DEGRADED,
                message=f"AI service connection degraded: {e}"
            )
```

---

*Integration Guide Version: 1.0.0*
*Last Updated: 2025-09-21*
*Compatible with: ToolBoxAI Platform v1.1.0+, Supabase Latest*