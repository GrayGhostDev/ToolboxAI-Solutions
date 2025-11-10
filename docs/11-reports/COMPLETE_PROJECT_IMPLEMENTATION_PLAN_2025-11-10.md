# ToolBoxAI Solutions - Complete Project Implementation Plan

**Date:** November 10, 2025  
**Version:** 1.0.0  
**Status:** Production Implementation Guide

---

## 📋 Table of Contents

1. [Executive Summary](#executive-summary)
2. [Project Architecture](#project-architecture)
3. [Technology Stack](#technology-stack)
4. [Implementation Phases](#implementation-phases)
5. [Database Schema](#database-schema)
6. [API Endpoints](#api-endpoints)
7. [Frontend Components](#frontend-components)
8. [AI Agent System](#ai-agent-system)
9. [Infrastructure Setup](#infrastructure-setup)
10. [Security Implementation](#security-implementation)
11. [Deployment Strategy](#deployment-strategy)
12. [Testing Strategy](#testing-strategy)
13. [Monitoring & Observability](#monitoring--observability)
14. [Next Steps](#next-steps)

---

## Executive Summary

**ToolBoxAI Solutions** is an AI-powered educational platform with Roblox integration, designed to provide interactive learning experiences for K-12 students. The platform combines modern web technologies, AI agents, and gamification to create engaging educational content.

### Key Features
- ✅ AI-powered content generation and tutoring
- ✅ Roblox game integration for immersive learning
- ✅ Real-time collaboration via Pusher Channels
- ✅ Multi-tenant architecture with role-based access
- ✅ Adaptive learning paths based on student performance
- ✅ Comprehensive analytics and progress tracking
- ✅ COPPA, FERPA, GDPR compliant

### Project Stats
- **Backend Lines of Code:** ~50,000+
- **Frontend Components:** 50+ React components
- **API Endpoints:** 100+ endpoints
- **AI Agents:** 15+ specialized agents
- **Database Models:** 25+ models
- **Test Coverage:** Target 80%+

---

## Project Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        FRONTEND LAYER                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │   React UI   │  │  Mantine UI  │  │   Clerk Auth │         │
│  │   Vite       │  │  TypeScript  │  │   Pusher     │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
└─────────────────────────────────────────────────────────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                         API GATEWAY                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │   FastAPI    │  │  REST API    │  │   GraphQL    │         │
│  │   Gunicorn   │  │  OpenAPI     │  │   (Future)   │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
└─────────────────────────────────────────────────────────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      BUSINESS LOGIC LAYER                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │  AI Agents   │  │   Services   │  │  Workflows   │         │
│  │  LangChain   │  │   Domain     │  │  Celery      │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
└─────────────────────────────────────────────────────────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                        DATA LAYER                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │  PostgreSQL  │  │    Redis     │  │   Supabase   │         │
│  │  (Supabase)  │  │    Cache     │  │   Storage    │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
└─────────────────────────────────────────────────────────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                   EXTERNAL INTEGRATIONS                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │   OpenAI     │  │    Roblox    │  │   Stripe     │         │
│  │   GPT-4.1    │  │  Game API    │  │   Payments   │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
└─────────────────────────────────────────────────────────────────┘
```

### Application Structure

```
ToolBoxAI-Solutions/
├── apps/
│   ├── backend/              # FastAPI Backend (Port 8009)
│   │   ├── api/             # API routes and endpoints
│   │   │   ├── v1/          # API version 1
│   │   │   │   ├── endpoints/
│   │   │   │   │   ├── auth.py          # Authentication
│   │   │   │   │   ├── users.py         # User management
│   │   │   │   │   ├── content.py       # Content operations
│   │   │   │   │   ├── roblox.py        # Roblox integration
│   │   │   │   │   ├── ai_tutor.py      # AI tutoring
│   │   │   │   │   ├── analytics.py     # Analytics
│   │   │   │   │   ├── payments.py      # Stripe payments
│   │   │   │   │   └── webhooks/        # Webhook handlers
│   │   │   └── routers/     # Route registration
│   │   ├── core/            # Core functionality
│   │   │   ├── app_factory.py          # App creation
│   │   │   ├── config.py               # Settings
│   │   │   ├── logging.py              # Logging
│   │   │   ├── security.py             # Security utils
│   │   │   └── monitoring.py           # Observability
│   │   ├── services/        # Business logic
│   │   │   ├── auth_service.py
│   │   │   ├── content_service.py
│   │   │   ├── roblox_service.py
│   │   │   ├── ai_service.py
│   │   │   └── stripe_service.py
│   │   ├── models/          # Pydantic models
│   │   ├── middleware/      # Custom middleware
│   │   ├── workers/         # Celery workers
│   │   └── main.py          # Application entry
│   │
│   └── dashboard/           # React Frontend (Port 5179)
│       ├── src/
│       │   ├── components/  # React components
│       │   │   ├── auth/    # Authentication
│       │   │   ├── dashboard/  # Dashboard views
│       │   │   ├── content/    # Content management
│       │   │   ├── analytics/  # Analytics views
│       │   │   └── shared/     # Shared components
│       │   ├── hooks/       # Custom React hooks
│       │   ├── contexts/    # Context providers
│       │   ├── pages/       # Page components
│       │   ├── config/      # Configuration
│       │   └── App.tsx      # Main app component
│       └── package.json
│
├── core/                    # Shared core modules
│   ├── agents/             # AI Agent System
│   │   ├── base_agent.py
│   │   ├── content_agent.py
│   │   ├── tutor_agent.py
│   │   ├── assessment_agent.py
│   │   ├── roblox_agent.py
│   │   ├── master_orchestrator.py
│   │   └── agent_registry.py
│   ├── mcp/                # Model Context Protocol
│   │   └── server.py
│   └── prompts/            # AI prompts
│
├── database/               # Database layer
│   ├── models/            # SQLAlchemy models
│   │   ├── base.py
│   │   ├── user_modern.py
│   │   ├── content_modern.py
│   │   ├── roblox_models.py
│   │   ├── agent_models.py
│   │   └── payment.py
│   ├── migrations/        # Alembic migrations
│   └── connection.py      # Database connection
│
├── infrastructure/         # Infrastructure as Code
│   ├── docker/
│   │   └── compose/       # Docker Compose files
│   ├── kubernetes/        # K8s manifests (future)
│   └── terraform/         # Terraform configs (future)
│
├── scripts/               # Utility scripts
│   ├── deployment/
│   ├── maintenance/
│   └── testing/
│
├── tests/                 # Test suites
│   ├── backend/
│   ├── api/
│   ├── agents/
│   └── e2e/
│
└── docs/                  # Documentation
    ├── 01-getting-started/
    ├── 02-architecture/
    ├── 03-api/
    └── 11-reports/
```

---

## Technology Stack

### Backend Stack

| Technology | Version | Purpose |
|------------|---------|---------|
| Python | 3.12+ | Core language |
| FastAPI | 0.121.1 | Web framework |
| Gunicorn | 23.0.0 | WSGI server |
| Uvicorn | 0.30.6 | ASGI server |
| Pydantic | 2.7.4+ | Data validation |
| SQLAlchemy | 2.0+ | ORM |
| Alembic | Latest | Database migrations |
| asyncpg | Latest | Async PostgreSQL driver |
| Redis | 7.x | Caching & sessions |
| Celery | Latest | Task queue |
| LangChain | 1.0+ | AI framework |
| OpenAI | Latest | GPT-4.1 integration |
| Clerk | Latest | Authentication |
| Pusher | Latest | Real-time channels |
| Stripe | Latest | Payment processing |
| Sentry | Latest | Error monitoring |
| Prometheus | Latest | Metrics |

### Frontend Stack

| Technology | Version | Purpose |
|------------|---------|---------|
| React | 19.1.0 | UI framework |
| TypeScript | 5.9.2 | Type safety |
| Vite | 6.x | Build tool |
| Mantine UI | 8.x | UI library |
| Redux Toolkit | Latest | State management |
| React Query | Latest | Server state |
| React Router | Latest | Routing |
| Clerk React | Latest | Auth UI |
| Pusher JS | Latest | Real-time client |
| Chart.js | Latest | Charts |
| Vitest | Latest | Testing |

### Database & Storage

| Service | Purpose |
|---------|---------|
| Supabase PostgreSQL | Primary database |
| Supabase Storage | File storage |
| Redis | Caching & sessions |
| Vault | Secrets management |

### DevOps & Infrastructure

| Tool | Purpose |
|------|---------|
| Docker | Containerization |
| Docker Compose | Local development |
| GitHub Actions | CI/CD |
| TeamCity | Enterprise CI/CD |
| Render | Backend hosting |
| Vercel | Frontend hosting |
| OpenTelemetry | Observability |

---

## Implementation Phases

### Phase 1: Foundation (Weeks 1-2) ✅ COMPLETED

**Objectives:**
- ✅ Project structure setup
- ✅ Development environment configuration
- ✅ Basic backend API framework
- ✅ Basic frontend shell
- ✅ Database schema design

**Deliverables:**
- ✅ Monorepo structure with pnpm workspaces
- ✅ Docker development environment
- ✅ FastAPI application with health endpoints
- ✅ React app with Mantine UI
- ✅ PostgreSQL database with initial schema
- ✅ CI/CD pipeline setup

### Phase 2: Authentication & User Management (Weeks 3-4)

**Objectives:**
- [ ] Implement Clerk authentication
- [ ] User role-based access control (RBAC)
- [ ] Multi-tenant architecture
- [ ] User profile management
- [ ] Parent/guardian accounts

**Tasks:**

#### Backend
```python
# apps/backend/api/v1/endpoints/auth.py

from fastapi import APIRouter, Depends, HTTPException
from apps.backend.core.security import get_current_user
from apps.backend.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["authentication"])

@router.post("/register")
async def register_user(user_data: UserCreate):
    """Register new user with Clerk"""
    pass

@router.get("/me")
async def get_current_user_info(current_user = Depends(get_current_user)):
    """Get current user information"""
    pass

@router.put("/profile")
async def update_profile(profile: UserProfile, current_user = Depends(get_current_user)):
    """Update user profile"""
    pass
```

#### Frontend
```typescript
// apps/dashboard/src/components/auth/Login.tsx

import { SignIn } from '@clerk/clerk-react';

export function Login() {
  return (
    <SignIn
      routing="path"
      path="/sign-in"
      signUpUrl="/sign-up"
      afterSignInUrl="/dashboard"
    />
  );
}
```

**Deliverables:**
- [ ] Clerk integration complete
- [ ] User registration flow
- [ ] Login/logout functionality
- [ ] Role-based access control
- [ ] User profile pages
- [ ] Multi-tenant support

### Phase 3: Content Management System (Weeks 5-7)

**Objectives:**
- [ ] Content creation and editing
- [ ] Content versioning
- [ ] Media upload and management
- [ ] Content organization (courses, lessons, modules)
- [ ] Content metadata and tagging

**Database Models:**

```python
# database/models/content_modern.py

from sqlalchemy import Column, String, Integer, ForeignKey, Text, ARRAY
from database.models.base_modern import BaseModel

class Course(BaseModel):
    __tablename__ = "courses"
    
    title = Column(String(255), nullable=False)
    description = Column(Text)
    grade_level = Column(String(50))
    subject = Column(String(100))
    difficulty = Column(String(20))  # beginner, intermediate, advanced
    thumbnail_url = Column(String(500))
    created_by_id = Column(Integer, ForeignKey("users.id"))
    tenant_id = Column(Integer, ForeignKey("tenants.id"))
    tags = Column(ARRAY(String))
    is_published = Column(Boolean, default=False)

class Lesson(BaseModel):
    __tablename__ = "lessons"
    
    course_id = Column(Integer, ForeignKey("courses.id"))
    title = Column(String(255), nullable=False)
    description = Column(Text)
    content = Column(Text)  # Rich text content
    order = Column(Integer)
    duration_minutes = Column(Integer)
    learning_objectives = Column(ARRAY(String))

class ContentAsset(BaseModel):
    __tablename__ = "content_assets"
    
    lesson_id = Column(Integer, ForeignKey("lessons.id"))
    asset_type = Column(String(50))  # video, image, pdf, interactive
    file_url = Column(String(500))
    file_size = Column(Integer)
    metadata = Column(JSON)
```

**API Endpoints:**

```python
# apps/backend/api/v1/endpoints/content.py

@router.post("/courses")
async def create_course(course: CourseCreate, current_user = Depends(require_educator)):
    """Create new course"""
    pass

@router.get("/courses/{course_id}")
async def get_course(course_id: int):
    """Get course details"""
    pass

@router.put("/courses/{course_id}")
async def update_course(course_id: int, course: CourseUpdate):
    """Update course"""
    pass

@router.post("/lessons")
async def create_lesson(lesson: LessonCreate):
    """Create new lesson"""
    pass

@router.post("/upload")
async def upload_content_asset(file: UploadFile):
    """Upload media file to Supabase Storage"""
    pass
```

**Deliverables:**
- [ ] Course management CRUD
- [ ] Lesson management CRUD
- [ ] Rich text editor integration
- [ ] Media upload system
- [ ] Content preview
- [ ] Content search and filtering

### Phase 4: AI Agent System (Weeks 8-10)

**Objectives:**
- [ ] Implement AI tutoring agent
- [ ] Content generation agent
- [ ] Assessment creation agent
- [ ] Personalized learning path agent
- [ ] Agent orchestration system

**Agent Architecture:**

```python
# core/agents/base_agent.py

from abc import ABC, abstractmethod
from langchain.agents import AgentExecutor
from langchain.tools import Tool
from langchain_openai import ChatOpenAI

class BaseAgent(ABC):
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.llm = ChatOpenAI(model="gpt-4-1106-preview", temperature=0.7)
        self.tools = self._initialize_tools()
        
    @abstractmethod
    def _initialize_tools(self) -> list[Tool]:
        """Initialize agent-specific tools"""
        pass
    
    @abstractmethod
    async def execute(self, task: dict) -> dict:
        """Execute agent task"""
        pass
```

```python
# core/agents/tutor_agent.py

from core.agents.base_agent import BaseAgent
from langchain.tools import Tool

class TutorAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="AI Tutor",
            description="Provides personalized tutoring and answers student questions"
        )
    
    def _initialize_tools(self):
        return [
            Tool(
                name="answer_question",
                func=self._answer_question,
                description="Answer student questions with context"
            ),
            Tool(
                name="explain_concept",
                func=self._explain_concept,
                description="Explain complex concepts in simple terms"
            ),
            Tool(
                name="provide_examples",
                func=self._provide_examples,
                description="Provide relevant examples"
            )
        ]
    
    async def execute(self, task: dict) -> dict:
        """Process tutoring request"""
        question = task.get("question")
        context = task.get("context", {})
        
        # Use LangChain to process the question
        response = await self.llm.ainvoke([
            {"role": "system", "content": self._get_system_prompt()},
            {"role": "user", "content": question}
        ])
        
        return {
            "answer": response.content,
            "confidence": 0.95,
            "sources": []
        }
```

**Agent Registry:**

```python
# core/agents/agent_registry.py

from typing import Dict
from core.agents.tutor_agent import TutorAgent
from core.agents.content_agent import ContentAgent
from core.agents.assessment_agent import AssessmentAgent

class AgentRegistry:
    _instance = None
    _agents: Dict[str, BaseAgent] = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize_agents()
        return cls._instance
    
    def _initialize_agents(self):
        """Register all available agents"""
        self._agents = {
            "tutor": TutorAgent(),
            "content": ContentAgent(),
            "assessment": AssessmentAgent(),
        }
    
    def get_agent(self, agent_type: str) -> BaseAgent:
        """Get agent by type"""
        return self._agents.get(agent_type)
    
    async def execute_task(self, agent_type: str, task: dict) -> dict:
        """Execute task with specified agent"""
        agent = self.get_agent(agent_type)
        if not agent:
            raise ValueError(f"Agent {agent_type} not found")
        return await agent.execute(task)
```

**Deliverables:**
- [ ] Base agent framework
- [ ] Tutor agent implementation
- [ ] Content generation agent
- [ ] Assessment agent
- [ ] Agent registry and orchestration
- [ ] LangChain integration
- [ ] Agent API endpoints

### Phase 5: Roblox Integration (Weeks 11-13)

**Objectives:**
- [ ] Roblox game connection API
- [ ] Player data synchronization
- [ ] In-game events tracking
- [ ] Rewards system
- [ ] Game progress tracking

**Roblox Service:**

```python
# apps/backend/services/roblox_service.py

from typing import Optional
import httpx
from apps.backend.core.config import settings

class RobloxService:
    def __init__(self):
        self.api_url = settings.ROBLOX_API_URL
        self.api_key = settings.ROBLOX_API_KEY
    
    async def authenticate_player(self, roblox_user_id: int) -> dict:
        """Authenticate Roblox player"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.api_url}/users/{roblox_user_id}",
                headers={"Authorization": f"Bearer {self.api_key}"}
            )
            return response.json()
    
    async def sync_player_data(self, user_id: int, roblox_data: dict):
        """Sync player data from Roblox to our system"""
        pass
    
    async def track_game_event(self, event_data: dict):
        """Track in-game events for analytics"""
        pass
    
    async def award_badges(self, user_id: int, badges: list):
        """Award badges to player"""
        pass
```

**Database Models:**

```python
# database/models/roblox_models.py

class RobloxPlayer(BaseModel):
    __tablename__ = "roblox_players"
    
    user_id = Column(Integer, ForeignKey("users.id"))
    roblox_user_id = Column(BigInteger, unique=True)
    username = Column(String(50))
    display_name = Column(String(100))
    avatar_url = Column(String(500))
    join_date = Column(DateTime)
    last_sync = Column(DateTime)

class GameSession(BaseModel):
    __tablename__ = "game_sessions"
    
    player_id = Column(Integer, ForeignKey("roblox_players.id"))
    game_id = Column(String(100))
    started_at = Column(DateTime)
    ended_at = Column(DateTime)
    duration_seconds = Column(Integer)
    events_count = Column(Integer)

class GameEvent(BaseModel):
    __tablename__ = "game_events"
    
    session_id = Column(Integer, ForeignKey("game_sessions.id"))
    event_type = Column(String(50))
    event_data = Column(JSON)
    occurred_at = Column(DateTime)
```

**Deliverables:**
- [ ] Roblox API integration
- [ ] Player authentication
- [ ] Data synchronization
- [ ] Event tracking system
- [ ] Rewards and badges
- [ ] Game session management

### Phase 6: Analytics & Reporting (Weeks 14-15)

**Objectives:**
- [ ] Student progress tracking
- [ ] Performance analytics
- [ ] Learning outcomes measurement
- [ ] Educator dashboards
- [ ] Parent reports
- [ ] Administrative analytics

**Analytics Models:**

```python
# database/models/analytics.py

class StudentProgress(BaseModel):
    __tablename__ = "student_progress"
    
    user_id = Column(Integer, ForeignKey("users.id"))
    course_id = Column(Integer, ForeignKey("courses.id"))
    completion_percentage = Column(Float)
    lessons_completed = Column(Integer)
    total_lessons = Column(Integer)
    average_score = Column(Float)
    time_spent_minutes = Column(Integer)
    last_activity = Column(DateTime)

class Assessment(BaseModel):
    __tablename__ = "assessments"
    
    lesson_id = Column(Integer, ForeignKey("lessons.id"))
    title = Column(String(255))
    assessment_type = Column(String(50))  # quiz, test, assignment
    total_points = Column(Integer)
    passing_score = Column(Integer)

class AssessmentResult(BaseModel):
    __tablename__ = "assessment_results"
    
    assessment_id = Column(Integer, ForeignKey("assessments.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    score = Column(Integer)
    percentage = Column(Float)
    time_taken_seconds = Column(Integer)
    answers = Column(JSON)
    submitted_at = Column(DateTime)
```

**Analytics API:**

```python
# apps/backend/api/v1/endpoints/analytics.py

@router.get("/student/{user_id}/progress")
async def get_student_progress(user_id: int):
    """Get student learning progress"""
    pass

@router.get("/course/{course_id}/analytics")
async def get_course_analytics(course_id: int):
    """Get course analytics"""
    pass

@router.get("/educator/dashboard")
async def get_educator_dashboard(current_user = Depends(require_educator)):
    """Get educator dashboard data"""
    pass

@router.post("/reports/generate")
async def generate_report(report_config: ReportConfig):
    """Generate custom report"""
    pass
```

**Deliverables:**
- [ ] Progress tracking system
- [ ] Analytics dashboards
- [ ] Report generation
- [ ] Performance metrics
- [ ] Data visualization

### Phase 7: Real-Time Features (Weeks 16-17)

**Objectives:**
- [ ] Real-time notifications
- [ ] Live collaboration
- [ ] Chat system
- [ ] Presence indicators
- [ ] Activity feed

**Pusher Integration:**

```typescript
// apps/dashboard/src/hooks/usePusher.ts

import { useEffect } from 'react';
import Pusher from 'pusher-js';

export function usePusher(userId: string) {
  useEffect(() => {
    const pusher = new Pusher(import.meta.env.VITE_PUSHER_KEY, {
      cluster: import.meta.env.VITE_PUSHER_CLUSTER,
      authEndpoint: '/api/v1/pusher/auth',
    });

    const channel = pusher.subscribe(`private-user-${userId}`);
    
    channel.bind('notification', (data: any) => {
      // Handle notification
    });

    channel.bind('message', (data: any) => {
      // Handle message
    });

    return () => {
      pusher.unsubscribe(`private-user-${userId}`);
    };
  }, [userId]);
}
```

```python
# apps/backend/api/v1/endpoints/pusher.py

from pusher import Pusher

pusher_client = Pusher(
    app_id=settings.PUSHER_APP_ID,
    key=settings.PUSHER_KEY,
    secret=settings.PUSHER_SECRET,
    cluster=settings.PUSHER_CLUSTER,
)

@router.post("/pusher/auth")
async def pusher_auth(auth_data: PusherAuthRequest, current_user = Depends(get_current_user)):
    """Authenticate Pusher channel subscription"""
    auth = pusher_client.authenticate(
        channel=auth_data.channel_name,
        socket_id=auth_data.socket_id,
        custom_data={
            "user_id": current_user.id,
            "user_info": {
                "name": current_user.name,
                "role": current_user.role
            }
        }
    )
    return auth

@router.post("/notifications/send")
async def send_notification(notification: NotificationCreate):
    """Send real-time notification"""
    pusher_client.trigger(
        f'private-user-{notification.user_id}',
        'notification',
        {
            'title': notification.title,
            'message': notification.message,
            'type': notification.type
        }
    )
```

**Deliverables:**
- [ ] Pusher integration
- [ ] Real-time notifications
- [ ] Chat system
- [ ] Presence tracking
- [ ] Live updates

### Phase 8: Payment Integration (Week 18)

**Objectives:**
- [ ] Stripe integration
- [ ] Subscription management
- [ ] Payment processing
- [ ] Invoice generation
- [ ] Webhook handling

**Stripe Service:**

```python
# apps/backend/services/stripe_service.py

import stripe
from apps.backend.core.config import settings

stripe.api_key = settings.STRIPE_SECRET_KEY

class StripeService:
    async def create_customer(self, user_id: int, email: str):
        """Create Stripe customer"""
        customer = stripe.Customer.create(
            email=email,
            metadata={"user_id": user_id}
        )
        return customer
    
    async def create_subscription(self, customer_id: str, price_id: str):
        """Create subscription"""
        subscription = stripe.Subscription.create(
            customer=customer_id,
            items=[{"price": price_id}],
            payment_behavior="default_incomplete",
            expand=["latest_invoice.payment_intent"]
        )
        return subscription
    
    async def handle_webhook(self, payload: bytes, sig_header: str):
        """Handle Stripe webhook events"""
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
        
        if event.type == "invoice.paid":
            await self._handle_invoice_paid(event.data.object)
        elif event.type == "customer.subscription.deleted":
            await self._handle_subscription_deleted(event.data.object)
```

**Deliverables:**
- [ ] Stripe integration
- [ ] Payment endpoints
- [ ] Subscription management
- [ ] Webhook handlers
- [ ] Billing dashboard

---

## Database Schema

### Core Tables

```sql
-- Users and Authentication
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    clerk_user_id VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(50) UNIQUE,
    full_name VARCHAR(255),
    role VARCHAR(50) NOT NULL, -- student, educator, parent, admin
    tenant_id INTEGER REFERENCES tenants(id),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Multi-tenancy
CREATE TABLE tenants (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(100) UNIQUE NOT NULL,
    subscription_tier VARCHAR(50),
    settings JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Content Management
CREATE TABLE courses (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    grade_level VARCHAR(50),
    subject VARCHAR(100),
    difficulty VARCHAR(20),
    thumbnail_url VARCHAR(500),
    created_by_id INTEGER REFERENCES users(id),
    tenant_id INTEGER REFERENCES tenants(id),
    tags TEXT[],
    is_published BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE lessons (
    id SERIAL PRIMARY KEY,
    course_id INTEGER REFERENCES courses(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    content TEXT,
    order_index INTEGER,
    duration_minutes INTEGER,
    learning_objectives TEXT[],
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Progress Tracking
CREATE TABLE student_progress (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    course_id INTEGER REFERENCES courses(id),
    lesson_id INTEGER REFERENCES lessons(id),
    completion_percentage FLOAT DEFAULT 0,
    time_spent_seconds INTEGER DEFAULT 0,
    last_accessed TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(user_id, course_id, lesson_id)
);

-- Assessments
CREATE TABLE assessments (
    id SERIAL PRIMARY KEY,
    lesson_id INTEGER REFERENCES lessons(id),
    title VARCHAR(255) NOT NULL,
    assessment_type VARCHAR(50),
    total_points INTEGER,
    passing_score INTEGER,
    questions JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE assessment_results (
    id SERIAL PRIMARY KEY,
    assessment_id INTEGER REFERENCES assessments(id),
    user_id INTEGER REFERENCES users(id),
    score INTEGER,
    percentage FLOAT,
    time_taken_seconds INTEGER,
    answers JSONB,
    submitted_at TIMESTAMP DEFAULT NOW()
);

-- Roblox Integration
CREATE TABLE roblox_players (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) UNIQUE,
    roblox_user_id BIGINT UNIQUE,
    username VARCHAR(50),
    display_name VARCHAR(100),
    avatar_url VARCHAR(500),
    join_date TIMESTAMP,
    last_sync TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE game_sessions (
    id SERIAL PRIMARY KEY,
    player_id INTEGER REFERENCES roblox_players(id),
    game_id VARCHAR(100),
    started_at TIMESTAMP,
    ended_at TIMESTAMP,
    duration_seconds INTEGER,
    events_count INTEGER DEFAULT 0,
    metadata JSONB
);

-- AI Agents
CREATE TABLE agent_tasks (
    id SERIAL PRIMARY KEY,
    agent_type VARCHAR(50) NOT NULL,
    task_type VARCHAR(50) NOT NULL,
    input_data JSONB,
    output_data JSONB,
    status VARCHAR(20), -- pending, running, completed, failed
    user_id INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP
);

-- Payments
CREATE TABLE subscriptions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    tenant_id INTEGER REFERENCES tenants(id),
    stripe_customer_id VARCHAR(255),
    stripe_subscription_id VARCHAR(255),
    plan_name VARCHAR(100),
    status VARCHAR(50),
    current_period_start TIMESTAMP,
    current_period_end TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

### Indexes

```sql
-- Performance indexes
CREATE INDEX idx_users_clerk_id ON users(clerk_user_id);
CREATE INDEX idx_users_tenant ON users(tenant_id);
CREATE INDEX idx_courses_tenant ON courses(tenant_id);
CREATE INDEX idx_lessons_course ON lessons(course_id);
CREATE INDEX idx_progress_user ON student_progress(user_id);
CREATE INDEX idx_progress_course ON student_progress(course_id);
CREATE INDEX idx_roblox_user ON roblox_players(user_id);
CREATE INDEX idx_game_sessions_player ON game_sessions(player_id);
CREATE INDEX idx_agent_tasks_user ON agent_tasks(user_id);
CREATE INDEX idx_agent_tasks_status ON agent_tasks(status);
```

---

## API Endpoints

### Authentication Endpoints

```
POST   /api/v1/auth/register          - Register new user
POST   /api/v1/auth/login             - Login user
POST   /api/v1/auth/logout            - Logout user
GET    /api/v1/auth/me                - Get current user
PUT    /api/v1/auth/profile           - Update profile
POST   /api/v1/auth/verify-email      - Verify email
POST   /api/v1/auth/reset-password    - Reset password
```

### User Management

```
GET    /api/v1/users                  - List users (admin)
GET    /api/v1/users/{id}             - Get user by ID
PUT    /api/v1/users/{id}             - Update user
DELETE /api/v1/users/{id}             - Delete user
POST   /api/v1/users/{id}/roles       - Assign roles
GET    /api/v1/users/{id}/progress    - Get user progress
```

### Content Management

```
GET    /api/v1/courses                - List courses
POST   /api/v1/courses                - Create course
GET    /api/v1/courses/{id}           - Get course
PUT    /api/v1/courses/{id}           - Update course
DELETE /api/v1/courses/{id}           - Delete course
POST   /api/v1/courses/{id}/publish   - Publish course

GET    /api/v1/lessons                - List lessons
POST   /api/v1/lessons                - Create lesson
GET    /api/v1/lessons/{id}           - Get lesson
PUT    /api/v1/lessons/{id}           - Update lesson
DELETE /api/v1/lessons/{id}           - Delete lesson

POST   /api/v1/upload                 - Upload media
GET    /api/v1/media/{id}             - Get media file
DELETE /api/v1/media/{id}             - Delete media
```

### AI Tutoring

```
POST   /api/v1/ai/ask                 - Ask AI tutor question
POST   /api/v1/ai/explain             - Explain concept
POST   /api/v1/ai/generate-content    - Generate content
POST   /api/v1/ai/create-assessment   - Create assessment
GET    /api/v1/ai/suggestions         - Get learning suggestions
```

### Roblox Integration

```
POST   /api/v1/roblox/authenticate    - Authenticate player
GET    /api/v1/roblox/player/{id}     - Get player data
POST   /api/v1/roblox/sync            - Sync player data
POST   /api/v1/roblox/events          - Track game event
GET    /api/v1/roblox/sessions        - Get game sessions
POST   /api/v1/roblox/rewards         - Award rewards
```

### Analytics

```
GET    /api/v1/analytics/dashboard    - Get dashboard data
GET    /api/v1/analytics/student/{id} - Student analytics
GET    /api/v1/analytics/course/{id}  - Course analytics
POST   /api/v1/analytics/reports      - Generate report
GET    /api/v1/analytics/export       - Export data
```

### Payments

```
POST   /api/v1/payments/checkout      - Create checkout session
POST   /api/v1/payments/subscribe     - Subscribe to plan
GET    /api/v1/payments/subscription  - Get subscription
PUT    /api/v1/payments/subscription  - Update subscription
POST   /api/v1/payments/cancel        - Cancel subscription
POST   /api/v1/payments/webhook       - Stripe webhook
GET    /api/v1/payments/invoices      - Get invoices
```

### Real-time (Pusher)

```
POST   /api/v1/pusher/auth            - Authenticate channel
POST   /api/v1/pusher/notify          - Send notification
POST   /api/v1/pusher/broadcast       - Broadcast message
GET    /api/v1/pusher/presence        - Get presence
```

### Health & Monitoring

```
GET    /health                        - Health check
GET    /metrics                       - Prometheus metrics
GET    /docs                          - API documentation
GET    /openapi.json                  - OpenAPI spec
```

---

## Frontend Components

### Component Structure

```typescript
// Core Components
components/
├── auth/
│   ├── Login.tsx
│   ├── Register.tsx
│   ├── Profile.tsx
│   └── ProtectedRoute.tsx
│
├── dashboard/
│   ├── DashboardLayout.tsx
│   ├── StudentDashboard.tsx
│   ├── EducatorDashboard.tsx
│   └── ParentDashboard.tsx
│
├── content/
│   ├── CourseList.tsx
│   ├── CourseCard.tsx
│   ├── LessonViewer.tsx
│   ├── ContentEditor.tsx
│   └── MediaUpload.tsx
│
├── ai/
│   ├── AIChatbot.tsx
│   ├── TutorInterface.tsx
│   ├── ContentGenerator.tsx
│   └── AssessmentCreator.tsx
│
├── analytics/
│   ├── ProgressChart.tsx
│   ├── PerformanceMetrics.tsx
│   ├── ReportViewer.tsx
│   └── DataExport.tsx
│
├── roblox/
│   ├── GameConnect.tsx
│   ├── PlayerStats.tsx
│   ├── RewardsDisplay.tsx
│   └── SessionHistory.tsx
│
└── shared/
    ├── Header.tsx
    ├── Sidebar.tsx
    ├── Notifications.tsx
    ├── LoadingSpinner.tsx
    └── ErrorBoundary.tsx
```

### Key Frontend Features

1. **Dashboard Views**
   - Student: Progress, courses, AI tutor
   - Educator: Class management, content creation, analytics
   - Parent: Child progress, reports
   - Admin: System overview, user management

2. **Content Creation**
   - Rich text editor (TipTap/Slate)
   - Media upload (Dropzone)
   - Course builder (Drag & drop)
   - Preview mode

3. **AI Integration**
   - Chat interface
   - Real-time responses
   - Context-aware suggestions
   - Voice input (future)

4. **Analytics Dashboards**
   - Charts (Chart.js/Recharts)
   - Data tables (TanStack Table)
   - Filters and exports
   - Real-time updates

---

## Infrastructure Setup

### Local Development

```yaml
# infrastructure/docker/compose/docker-compose.yml

version: '3.8'

services:
  postgres:
    image: postgres:16
    environment:
      POSTGRES_DB: educational_platform_dev
      POSTGRES_USER: eduplatform
      POSTGRES_PASSWORD: eduplatform2024
    ports:
      - "5434:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    ports:
      - "6381:6379"
    volumes:
      - redis_data:/data

  backend:
    build:
      context: ../../../
      dockerfile: apps/backend/Dockerfile
    ports:
      - "8009:8009"
    environment:
      DATABASE_URL: postgresql://eduplatform:eduplatform2024@postgres:5432/educational_platform_dev
      REDIS_URL: redis://redis:6379
    depends_on:
      - postgres
      - redis
    volumes:
      - ../../../apps/backend:/app/apps/backend

  celery-worker:
    build:
      context: ../../../
      dockerfile: apps/backend/Dockerfile
    command: celery -A celery_app worker --loglevel=info
    environment:
      DATABASE_URL: postgresql://eduplatform:eduplatform2024@postgres:5432/educational_platform_dev
      REDIS_URL: redis://redis:6379
    depends_on:
      - postgres
      - redis

volumes:
  postgres_data:
  redis_data:
```

### Production Deployment

See `render.yaml` and `vercel.json` for production configurations.

---

## Security Implementation

### Authentication & Authorization

1. **Clerk Integration**
   - JWT token validation
   - Role-based access control
   - Session management
   - Multi-factor authentication

2. **API Security**
   - Rate limiting
   - CORS configuration
   - Input validation
   - SQL injection prevention

3. **Data Protection**
   - Encryption at rest
   - Encryption in transit (SSL/TLS)
   - Secure password hashing
   - PII data handling

### Compliance

- **COPPA**: Children's Online Privacy Protection Act
- **FERPA**: Family Educational Rights and Privacy Act
- **GDPR**: General Data Protection Regulation
- **SOC 2 Type 2**: Security compliance

---

## Testing Strategy

### Backend Testing

```python
# tests/backend/test_content.py

import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_create_course(client: AsyncClient, auth_headers):
    course_data = {
        "title": "Math 101",
        "description": "Introduction to Mathematics",
        "grade_level": "6th",
        "subject": "Mathematics"
    }
    
    response = await client.post(
        "/api/v1/courses",
        json=course_data,
        headers=auth_headers
    )
    
    assert response.status_code == 201
    assert response.json()["title"] == "Math 101"

@pytest.mark.asyncio
async def test_get_course(client: AsyncClient, test_course):
    response = await client.get(f"/api/v1/courses/{test_course.id}")
    
    assert response.status_code == 200
    assert response.json()["id"] == test_course.id
```

### Frontend Testing

```typescript
// apps/dashboard/src/__tests__/components/CourseCard.test.tsx

import { render, screen } from '@testing-library/react';
import { CourseCard } from '@/components/content/CourseCard';

describe('CourseCard', () => {
  it('renders course information', () => {
    const course = {
      id: 1,
      title: 'Math 101',
      description: 'Introduction to Mathematics',
      thumbnailUrl: '/images/math.jpg'
    };

    render(<CourseCard course={course} />);
    
    expect(screen.getByText('Math 101')).toBeInTheDocument();
    expect(screen.getByText('Introduction to Mathematics')).toBeInTheDocument();
  });
});
```

### E2E Testing

```typescript
// tests/e2e/content.spec.ts

import { test, expect } from '@playwright/test';

test('educator can create course', async ({ page }) => {
  await page.goto('/login');
  await page.fill('[name="email"]', 'educator@test.com');
  await page.fill('[name="password"]', 'password123');
  await page.click('button[type="submit"]');
  
  await page.goto('/courses/new');
  await page.fill('[name="title"]', 'New Course');
  await page.fill('[name="description"]', 'Course description');
  await page.click('button[type="submit"]');
  
  await expect(page).toHaveURL(/\/courses\/\d+/);
  await expect(page.locator('h1')).toContainText('New Course');
});
```

---

## Monitoring & Observability

### Metrics Collection

```python
# apps/backend/core/monitoring.py

from prometheus_client import Counter, Histogram, Gauge

# Request metrics
http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

http_request_duration = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration',
    ['method', 'endpoint']
)

# Business metrics
active_users = Gauge('active_users_total', 'Number of active users')
courses_created = Counter('courses_created_total', 'Total courses created')
ai_requests = Counter('ai_requests_total', 'Total AI requests', ['agent_type'])
```

### Error Tracking (Sentry)

```python
# apps/backend/config/sentry.py

import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration

def init_sentry():
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        integrations=[FastApiIntegration()],
        traces_sample_rate=1.0,
        environment=settings.ENVIRONMENT
    )
```

### Logging

```python
# apps/backend/core/logging.py

import logging
from pythonjsonlogger import jsonlogger

class LoggingManager:
    def __init__(self):
        self.logger = logging.getLogger("toolboxai")
        handler = logging.StreamHandler()
        formatter = jsonlogger.JsonFormatter(
            '%(timestamp)s %(level)s %(name)s %(message)s'
        )
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)
```

---

## Next Steps

### Immediate Actions

1. **Complete Phase 2** (Authentication)
   - [ ] Finalize Clerk integration
   - [ ] Implement RBAC
   - [ ] Create user management UI

2. **Start Phase 3** (Content Management)
   - [ ] Design content models
   - [ ] Build API endpoints
   - [ ] Create editor UI

3. **Infrastructure**
   - [x] Deploy backend to Render ✅
   - [ ] Deploy frontend to Vercel
   - [ ] Setup production database (Supabase)
   - [ ] Configure monitoring

### Short-term Goals (1-2 weeks)

- [ ] Complete user authentication flow
- [ ] Build basic content creation
- [ ] Setup Supabase integration
- [ ] Deploy staging environment
- [ ] Write integration tests

### Medium-term Goals (1-2 months)

- [ ] Complete AI agent system
- [ ] Roblox integration MVP
- [ ] Analytics dashboard
- [ ] Payment processing
- [ ] Beta testing with users

### Long-term Goals (3-6 months)

- [ ] Full production launch
- [ ] Mobile app development
- [ ] Advanced AI features
- [ ] Multi-language support
- [ ] Enterprise features

---

## Resources & Documentation

### Development Resources
- **Backend Docs:** `/docs/03-api/`
- **Frontend Docs:** `/docs/04-frontend/`
- **Database Docs:** `/docs/05-database/`
- **Deployment Docs:** `/docs/08-operations/deployment/`

### External Documentation
- **FastAPI:** https://fastapi.tiangolo.com
- **React:** https://react.dev
- **Mantine UI:** https://mantine.dev
- **LangChain:** https://python.langchain.com
- **Supabase:** https://supabase.com/docs

### Team Communication
- **Project Board:** GitHub Projects
- **CI/CD:** GitHub Actions + TeamCity
- **Monitoring:** Sentry + Prometheus
- **Documentation:** Markdown in `/docs/`

---

**Document Version:** 1.0.0  
**Last Updated:** November 10, 2025  
**Next Review:** December 10, 2025  
**Maintainer:** Development Team

---

**This is a living document. Update as the project evolves.**
