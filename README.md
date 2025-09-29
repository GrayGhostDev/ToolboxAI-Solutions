# ToolBoxAI Educational Platform - 2025 Edition

![Docker](https://img.shields.io/badge/Docker-25.x-2496ED?style=flat-square&logo=docker&logoColor=white)
![Security](https://img.shields.io/badge/Security-Hardened-28a745?style=flat-square&logo=security&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=flat-square&logo=python&logoColor=white)
![Node.js](https://img.shields.io/badge/Node.js-22-339933?style=flat-square&logo=node.js&logoColor=white)
![React](https://img.shields.io/badge/React-19.1.0-61DAFB?style=flat-square&logo=react&logoColor=white)
![TypeScript](https://img.shields.io/badge/TypeScript-5.9.2-3178C6?style=flat-square&logo=typescript&logoColor=white)
![Vite](https://img.shields.io/badge/Vite-6.0.1-646CFF?style=flat-square&logo=vite&logoColor=white)
![Pusher](https://img.shields.io/badge/Pusher-8.4.0-00D9FF?style=flat-square&logo=pusher&logoColor=white)
![Mantine](https://img.shields.io/badge/Mantine-v8.3.1-339AF0?style=flat-square&logo=mantine&logoColor=white)

> **🚀 Complete AI-Powered Educational Platform with Real-time Communication**
> **✨ 2025 Update**: React 19 + Pusher Channels + Mantine v8 + Docker Hub + Full Service Integration
> **🎯 Latest (2025-09-28)**: React 19.1.0 migration, Vite 6, TypeScript 5.9.2, ESLint 9 flat config

## 🚀 **Quick Start**

### **Prerequisites**
- Docker 25.x with Docker Compose v2
- Git
- 4GB+ RAM available for Docker
- Node.js 22+ and npm 10+ (for local development)

### **⚠️ External Drive Development Notice**
If developing on an external drive (e.g., `/Volumes/` on macOS):
- **Recommended**: Use Docker for all development (see Docker section below)
- **Issue**: Native binaries (esbuild, Rollup) fail with system error -88
- **NPM Workaround**: Use `npm install --no-bin-links --legacy-peer-deps`
- **Vite Config**: Use `vite.config.js` instead of `.ts` to avoid transpilation

### **🎯 2025 One-Command Deployment**
```bash
# Complete automated setup
git clone https://github.com/ToolBoxAI-Solutions/toolboxai.git
cd toolboxai
./infrastructure/docker/scripts/complete-setup-2025.sh

# Configure your credentials (replace with actual values)
nano infrastructure/docker/config/environment.env
# Update: VITE_PUSHER_KEY, VITE_CLERK_PUBLISHABLE_KEY, etc.

# Access the platform
open http://localhost:5180  # Dashboard
open http://localhost:8009/docs  # API Documentation
```

## ✨ **2025 Platform Updates**

### **🔐 Authentication System (Clerk - Complete)**
- **Clerk Auth**: Enterprise JWT-based authentication
- **Social Login**: Google, GitHub, Discord providers
- **MFA Support**: Two-factor authentication enabled
- **Session Management**: Secure cookie-based sessions
- **Role-Based Access**: Admin, Teacher, Student roles

### **🔄 Real-time Communication (Pusher - Primary Solution)**
- **Pusher Channels**: Primary real-time communication layer (no Socket.IO)
- **Private Channels**: User-specific and class-based channels
- **Presence Channels**: Real-time online user tracking
- **Auto-reconnection**: Exponential backoff with jitter
- **Event Streaming**: AI agent updates, content generation, notifications
- **Frontend Integration**: 46+ components using Pusher hooks
- **Backend Service**: Dedicated Pusher service in `services/roblox_pusher.py`

### **🎨 Modern UI Framework (Complete - Sept 28, 2025)**
- **Mantine v8.3.1**: Complete migration from Material-UI (0 MUI references remain)
- **Component Status**: 377 files successfully migrated
- **Icon Library**: Tabler Icons v3.x (140+ icon mappings)
- **Design System**: Roblox-themed consistent styling throughout
- **Performance**: Reduced bundle size by ~30% compared to Material-UI
- **Test Coverage**: All test mocks updated for Mantine

### **🐳 Docker Hub Integration (Complete)**
- **Registry**: docker.io/thegrayghost23/toolboxai-*
- **Automation**: Complete CI/CD pipeline
- **Security**: Vulnerability scanning enabled
- **Multi-arch**: Support for AMD64 and ARM64

### **🤖 AI Service Integration (Complete - Sept 28, 2025)**
- **LangChain/LangGraph**: Full observability with LangSmith tracing
- **Agent Coordinator**: 8 specialized agents with orchestration
- **MCP Server**: Model Context Protocol for AI coordination
- **Real-time AI**: Pusher-powered AI event streaming
- **Educational AI**: Integrated with Roblox and content systems
- **Monitoring**: Complete traces available in LangSmith dashboard

### **🎮 Educational Gaming (Complete)**
- **Roblox Bridge**: Complete Studio integration
- **Student Tracking**: Real-time progress monitoring
- **Game Events**: Live event streaming via Pusher
- **Content Sync**: Automated educational content delivery

### **2. Start Development Environment**
```bash
# Navigate to the modernized Docker setup
cd infrastructure/docker/compose

# Start all services (backend, dashboard, databases, and tools)
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d

# View logs
docker compose logs -f backend dashboard
```

### **3. Access the Platform**
- **Dashboard**: http://localhost:5179
- **Backend API**: http://localhost:8009
- **API Documentation**: http://localhost:8009/docs
- **Database Admin**: http://localhost:8080 (Adminer)
- **Redis Admin**: http://localhost:8081 (Redis Commander)

### **macOS Performance Optimization**
For optimal Docker performance on macOS, enable VirtioFS:
```bash
# In Docker Desktop: Settings → Experimental Features → Enable VirtioFS
# Improves file system performance by up to 10x
```

## 🎨 **Mantine UI Framework**

### **Setup and Configuration**
The dashboard now uses Mantine v8.3.1 for all UI components. Material-UI has been completely removed.

#### **Key Features**
- **React 19 Compatible**: Full support for React 18 and 19
- **TypeScript First**: Built with TypeScript from the ground up
- **Smaller Bundle**: ~30% smaller than Material-UI equivalent
- **Better Performance**: Optimized rendering and fewer re-renders
- **Rich Components**: 100+ components out of the box

#### **Theme Configuration**
The Mantine theme is configured in `apps/dashboard/src/theme/mantine-theme.ts` with:
- **Roblox Brand Colors**: Custom color palette matching Roblox design
- **Game-like Effects**: Neon glows, gradients, and animations
- **Responsive Design**: Mobile-first responsive breakpoints
- **Dark Mode Support**: Built-in light/dark theme switching

#### **Component Usage**
```tsx
// Import Mantine components
import { Button, Card, Text, Badge, Progress } from '@mantine/core';
import { notifications } from '@mantine/notifications';
import { IconPlayerPlay } from '@tabler/icons-react';

// Use in your components
<Button leftSection={<IconPlayerPlay size={16} />}>
  Start Game
</Button>
```

#### **Migration Guide**
For detailed migration information, see:
- `/docs/MANTINE_MIGRATION_GUIDE.md` - Complete migration reference
- Component mappings and patterns
- Icon migration tables
- Common troubleshooting tips

## 🔗 **LangChain/LangGraph Integration (Sept 28, 2025)**

### **Overview**
The platform now includes complete LangChain/LangGraph integration for advanced AI agent orchestration with full observability through LangSmith.

### **Key Features**
- **🔍 Full Observability**: Every agent operation traced in LangSmith dashboard
- **📊 Performance Monitoring**: Real-time metrics, token usage, and cost tracking
- **🤖 8 Specialized Agents**: Content, Quiz, Script, Terrain, Review, Testing, Supervisor, Orchestrator
- **🔄 Coordinator System**: Main, Workflow, Resource, Sync, and Error coordinators
- **⚡ Real-time Updates**: Pusher integration for live agent progress
- **💾 Redis Caching**: Efficient result caching on port 55007

### **Configuration**
```bash
# Add to your .env file (get your keys from LangSmith)
LANGCHAIN_API_KEY=your-langchain-api-key-here
LANGCHAIN_PROJECT_ID=your-project-id-here
LANGCHAIN_PROJECT=ToolboxAI-Solutions
LANGCHAIN_TRACING_V2=true
```

### **Quick Start**
```bash
# 1. Verify configuration
python test_langchain_simple.py

# 2. Start LangGraph services
./scripts/start_langgraph_services.sh

# 3. Test agent execution
curl -X POST http://localhost:8009/api/v1/coordinators/generate \
  -H "Content-Type: application/json" \
  -d '{"subject": "Math", "grade_level": 5}'

# 4. View traces in LangSmith dashboard
# https://smith.langchain.com/project/{your-project-id}
```

### **Documentation**
- **Setup Guide**: `/docs/LANGCHAIN_CONFIGURATION.md`
- **Integration Details**: `/docs/05-implementation/agents/coordinator-langchain-integration.md`
- **Agent System**: `/docs/05-implementation/agent-system/README.md`

## 🔒 **Security Notice**

**⚠️ NEVER commit real credentials to version control**

1. **Environment Configuration**: The `.env.example` file contains secure templates
2. **Generate Secure Keys**:
   ```bash
   # JWT Secret (32 bytes)
   openssl rand -hex 32

   # Database Password (32 chars base64)
   openssl rand -base64 32

   # Redis Password (24 chars base64)
   openssl rand -base64 24
   ```

3. **Production Security**: Use Docker Secrets for production deployments:
   ```bash
   echo "your-secure-password" | docker secret create db_password -
   ```

4. **API Keys**: Store API keys in secrets management:
   - Development: `.env` (never committed)
   - Production: Docker Secrets, AWS Secrets Manager, or HashiCorp Vault

## 📊 **Current Status (2025-09-28)**

✅ **Docker Infrastructure Modernized** - Enterprise security with non-root users
✅ **Backend Fully Operational** - Port 8009 with all services running
✅ **Dashboard Running** - Port 5179 with Mantine UI (100% migrated)
✅ **LangChain/LangGraph Integration** - Full observability with LangSmith
✅ **Agent Coordinator System** - 8 specialized agents with orchestration
✅ **Pusher Real-time** - Complete WebSocket replacement
✅ **Security Hardened** - No exposed API keys, proper .env configuration
✅ **All Import Path Errors Resolved**
✅ **91.8% Backend Code Reduction Complete**

## 🎯 **Overview**

ToolBoxAI is a comprehensive educational platform that combines AI-powered content generation, real-time collaboration, and immersive Roblox integration. The platform uses advanced agent systems powered by LangChain's Expression Language (LCEL) and provides robust data persistence through dual PostgreSQL + Supabase architecture.

### **Key Features**

- **🤖 AI Agent System**: 8 specialized agents using LangChain 0.3.26+ LCEL
- **📚 Educational Content**: Automated lesson, quiz, and assessment generation
- **🎮 Roblox Integration**: 3D environment generation and script optimization
- **⚡ Real-time Updates**: Supabase Realtime + Pusher Channels integration
- **⚛️ Modern Frontend**: React 19 with concurrent features and TypeScript
- **🐳 Docker Ready**: Complete containerized deployment with Supabase stack
- **🔒 Enterprise Security**: JWT authentication, RLS, and comprehensive monitoring

## 🏗️ **Architecture**

> **🎉 REFACTORING COMPLETE (Sept 2025)**: Backend transformed from 4,430-line monolith to modular architecture with 91.8% code reduction. See [REFACTORING_COMPLETE.md](REFACTORING_COMPLETE.md) for details.

**Backend (Python 3.12) - Refactored Modular Architecture**
- **Framework**: FastAPI 0.116.1 with Application Factory Pattern
- **Architecture**: Modular design with separation of concerns
- **AI/ML**: LangChain 0.3.26+ (LCEL), LangGraph 0.2.65+, LangSmith
- **Database**: PostgreSQL 16 (primary) + Supabase (optional storage/auth)
- **Cache**: Redis 7
- **Real-time**: Pusher Channels (primary) - NO WebSocket/Socket.IO
- **Auth**: JWT with enhanced security + optional Supabase Auth
- **Validation**: Pydantic v2 (2.9.0+)
- **Storage**: Supabase Storage providers for multi-tenant file management

**Frontend (Node.js 22) - Updated 2025-09-28**
- **Framework**: React 19.1.0 with concurrent features
- **TypeScript**: 5.9.2 with strict mode
- **Build**: Vite 6.0.1 (using vite.config.js for external drive support)
- **Testing**: Vitest 3.2.4 with React Testing Library
- **Linting**: ESLint 9.35.0 with flat config system
- **UI**: Mantine 8.3.1 (migrated from Material-UI)
- **Icons**: Tabler Icons React 3.35.0
- **State**: Redux Toolkit 2.2.7
- **Real-time**: Pusher-js 8.4.0 (primary, no WebSocket fallback)
- **3D Support**: @react-three/fiber 9.3.0 (React 19 compatible)
- **Package Management**: 692+ packages with external drive support

## 📚 **Documentation**

### Backend Architecture Documentation
- **[Architecture Overview](apps/backend/ARCHITECTURE.md)** - Complete system architecture, components, and technology stack
- **[Migration Guide](apps/backend/MIGRATION.md)** - Step-by-step migration instructions and rollback procedures
- **[Developer Guide](apps/backend/DEVELOPER_GUIDE.md)** - Development workflow, coding standards, and best practices
- **[Configuration Guide](apps/backend/CONFIGURATION.md)** - Environment variables, security settings, and performance tuning
- **[Troubleshooting Guide](apps/backend/TROUBLESHOOTING.md)** - Common issues, debugging techniques, and error resolution

### Quick Links
- **[API Endpoints](apps/backend/DEVELOPER_GUIDE.md#creating-endpoints)** - Creating and managing API endpoints
- **[Service Development](apps/backend/DEVELOPER_GUIDE.md#service-development)** - Building business logic services
- **[Testing Guidelines](apps/backend/DEVELOPER_GUIDE.md#testing-guidelines)** - Unit and integration testing
- **[Performance Optimization](apps/backend/DEVELOPER_GUIDE.md#performance-optimization)** - Database and application tuning

## 🛠️ **Development**

### **Local Development (Non-Docker)**

1. **Setup Python Environment**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

2. **IDE Setup**:
   - Point VS Code/Cursor Python interpreter to: `./venv/bin/python`
   - Reload window after changing interpreter for proper type checking

3. **Run Services**:
   ```bash
   # Backend
   cd apps/backend && uvicorn main:app --host 127.0.0.1 --port 8009 --reload

   # Dashboard
   cd apps/dashboard && npm install && npm run dev
   ```

4. **Run Tests**:
   ```bash
   # Python tests
   pytest -q

   # Frontend tests
   npm -w apps/dashboard test
   ```

### **Technical Architecture Decisions**

#### **Real-time Communication**
- **Primary**: Pusher Channels v8.4.0 - handles all real-time events
- **No WebSocket/Socket.IO**: Completely migrated to Pusher
- **Implementation**: 46+ React components using Pusher hooks
- **Backend**: Dedicated Pusher service for event broadcasting

#### **Database & Storage**
- **Primary Database**: PostgreSQL 16 for all application data
- **Cache Layer**: Redis 7 for sessions and caching
- **Supabase (Optional)**:
  - Storage buckets for file management
  - Auth provider (when enabled)
  - Database backup/sync (configurable)
  - Extensive configuration in `toolboxai_settings/settings.py`

#### **Configuration**
- **Settings**: Centralized in `toolboxai_settings/` using Pydantic v2
- **AI Agents**: LangChain 0.3.26+ LCEL (Expression Language) throughout
- **Backend**: Factory pattern with 91.8% code reduction from monolith

### **Compatibility**

- **Python**: 3.11+ required, 3.12 recommended
- **Node.js**: 22+ required for React 19 features
- **Docker**: 25.x with Compose v2
- **Pydantic**: v2-first with v1 compatibility adapter at `toolboxai_settings/compat.py`
# Test comment
