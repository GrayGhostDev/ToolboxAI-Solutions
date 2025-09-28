# ToolBoxAI Educational Platform - 2025 Edition

![Docker](https://img.shields.io/badge/Docker-25.x-2496ED?style=flat-square&logo=docker&logoColor=white)
![Security](https://img.shields.io/badge/Security-Hardened-28a745?style=flat-square&logo=security&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=flat-square&logo=python&logoColor=white)
![Node.js](https://img.shields.io/badge/Node.js-22-339933?style=flat-square&logo=node.js&logoColor=white)
![Pusher](https://img.shields.io/badge/Pusher-8.4.0-00D9FF?style=flat-square&logo=pusher&logoColor=white)
![Mantine](https://img.shields.io/badge/Mantine-v8.3.1-339AF0?style=flat-square&logo=mantine&logoColor=white)

> **🚀 Complete AI-Powered Educational Platform with Real-time Communication**
> **✨ 2025 Update**: Pusher Channels + Mantine v8 + Docker Hub + Full Service Integration

## 🚀 **Quick Start**

### **Prerequisites**
- Docker 25.x with Docker Compose v2
- Git
- 4GB+ RAM available for Docker

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

### **🔄 Real-time Communication (Complete)**
- **Pusher Channels**: Modern WebSocket-only transport
- **Auto-reconnection**: Exponential backoff with jitter
- **Token Management**: Automatic JWT refresh
- **Multi-channel**: Support for all service integrations

### **🎨 Modern UI Framework (Complete)**
- **Mantine v8.3.1**: Latest component library - Migration Complete!
- **Component Status**: 100+ components successfully migrated from Material-UI
- **Design System**: Roblox-themed consistent styling throughout
- **Accessibility**: Enhanced ARIA compliance and keyboard navigation
- **Performance**: Reduced bundle size by ~30% compared to Material-UI

### **🐳 Docker Hub Integration (Complete)**
- **Registry**: docker.io/thegrayghost23/toolboxai-*
- **Automation**: Complete CI/CD pipeline
- **Security**: Vulnerability scanning enabled
- **Multi-arch**: Support for AMD64 and ARM64

### **🤖 AI Service Integration (Complete)**
- **MCP Server**: Model Context Protocol for AI coordination
- **Agent Coordinator**: AI task orchestration and management
- **Real-time AI**: Pusher-powered AI event streaming
- **Educational AI**: Integrated with Roblox and content systems

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

## 📊 **Current Status (2025-09-24)**

✅ **Docker Infrastructure Modernized**
✅ **Backend Fully Operational** - Port 8009
✅ **Dashboard Running** - Port 5179
✅ **All Import Path Errors Resolved**
✅ **Security Vulnerabilities Fixed**
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
- **Database**: PostgreSQL 16 + Supabase (dual strategy)
- **Cache**: Redis 7
- **Real-time**: Supabase Realtime + Pusher Channels
- **Auth**: JWT with enhanced security
- **Validation**: Pydantic v2 (2.9.0+)

**Frontend (Node.js 22)**
- **Framework**: React 19 with concurrent features
- **TypeScript**: 5.5.4 with strict mode
- **Build**: Vite 5.4.10
- **UI**: Material-UI 6.1.8 + Mantine 7.14.3
- **State**: Redux Toolkit 2.5.0
- **Real-time**: Supabase client + Pusher-js
- **Database**: Supabase client with type-safe operations

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

### **Technical Notes**

- **Configuration**: Uses Pydantic v2 and `pydantic-settings` in `toolboxai_settings/`
- **AI Agents**: LangChain 0.3.26+ LCEL (Expression Language) throughout
- **Backend**: Factory pattern with 91.8% code reduction from monolith
- **Database**: PostgreSQL + Redis with optional Supabase integration
- **Real-time**: Pusher Channels (migrated from Socket.IO)

### **Compatibility**

- **Python**: 3.11+ required, 3.12 recommended
- **Node.js**: 22+ required for React 19 features
- **Docker**: 25.x with Compose v2
- **Pydantic**: v2-first with v1 compatibility adapter at `toolboxai_settings/compat.py`
