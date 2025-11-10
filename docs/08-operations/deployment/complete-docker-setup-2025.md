# Complete Docker Setup Guide - 2025 Implementation

## 🎯 **Overview**
Complete guide for setting up ToolboxAI with Docker Hub integration, Pusher real-time communication, Mantine v8 UI, and full service integration following 2025 best practices.

## 🚀 **Quick Start Implementation**

### **Step 1: Resolve Port Conflicts**
```bash
# Kill any processes using port 5179
pkill -f "vite" 2>/dev/null || true
pkill -f "npm run dev" 2>/dev/null || true
lsof -ti:5179 | xargs kill -9 2>/dev/null || true
echo "✅ Port conflicts resolved"
```

### **Step 2: Configure Environment**
```bash
# Navigate to project root
cd /Volumes/G-DRIVE\ ArmorATD/Development/Clients/ToolBoxAI-Solutions

# Copy environment template
cp infrastructure/docker/config/environment.env .env.docker

# Edit with your actual credentials
nano .env.docker
# Replace these values:
# - VITE_PUSHER_KEY=your_actual_pusher_key
# - VITE_PUSHER_CLUSTER=your_cluster
# - VITE_CLERK_PUBLISHABLE_KEY=your_clerk_key
```

### **Step 3: Build and Deploy**
```bash
# Make setup script executable
chmod +x infrastructure/docker/scripts/dockerhub-setup.sh

# Run the complete setup
./infrastructure/docker/scripts/dockerhub-setup.sh

# Or manual deployment
cd infrastructure/docker/compose
docker-compose --env-file ../config/environment.env up -d
```

### **Step 4: Verify Installation**
```bash
# Check all services
docker-compose ps

# Test dashboard (new port)
curl http://localhost:5179/health

# Test backend
curl http://localhost:8009/health

# Open dashboard
open http://localhost:5179
```

## 🏗️ **Architecture Overview**

### **Service Stack (Updated)**
```
┌─────────────────────────────────────────────────────────────┐
│                    ToolboxAI Platform 2025                  │
├─────────────────────────────────────────────────────────────┤
│ Frontend (Port 5179)                                        │
│ ├── React 18 + TypeScript                                   │
│ ├── Mantine v8.3.1 UI Components                           │
│ ├── Pusher Real-time Communication                          │
│ └── Nginx Production Server                                 │
├─────────────────────────────────────────────────────────────┤
│ Backend Services                                            │
│ ├── FastAPI Backend (8009) - Main API + Pusher Auth        │
│ ├── MCP Server (9877) - AI Model Context Protocol          │
│ ├── Agent Coordinator (8888) - AI Agent Orchestration      │
│ ├── Roblox Bridge (5001) - Educational Game Integration    │
│ └── Ghost CMS (8000) - Content Management                  │
├─────────────────────────────────────────────────────────────┤
│ Data Layer                                                  │
│ ├── PostgreSQL (5434) - Primary Database                   │
│ └── Redis (6381) - Cache + Session Storage                 │
└─────────────────────────────────────────────────────────────┘
```

### **Integration Flow**
```
Dashboard ──┬── Pusher Channels ──→ Real-time Updates
            ├── REST API ──────────→ Backend Services
            ├── /mcp/ ─────────────→ MCP Server
            ├── /agents/ ──────────→ Agent Coordinator
            ├── /roblox/ ──────────→ Roblox Bridge
            └── /ghost/ ───────────→ Ghost CMS
```

## 🔧 **Service Integration Details**

### **1. MCP Server Integration**
```typescript
// Dashboard integration
import { mcpService } from '../services/mcp';

// Get available AI models
const models = await mcpService.getModels();

// Create AI task
const task = await mcpService.createTask(modelId, contextId, prompt);

// Subscribe to real-time updates
mcpService.subscribeToEvents((event) => {
  console.log('MCP Event:', event);
});
```

**Backend Endpoints Required:**
```python
@app.get("/mcp/health")
async def mcp_health():
    return {"status": "healthy", "service": "mcp-server"}

@app.get("/mcp/models")
async def get_mcp_models():
    # Return available AI models
    pass

@app.post("/mcp/tasks")
async def create_mcp_task(task: MCPTaskRequest):
    # Create new AI task
    pass
```

### **2. Agent Coordinator Integration**
```typescript
// Dashboard integration
import { agentService } from '../services/agents';

// Get available agents
const agents = await agentService.getAgents();

// Create agent task
const task = await agentService.createTask(agentId, taskType, parameters);

// Monitor real-time status
agentService.subscribeToEvents((event) => {
  console.log('Agent Event:', event);
});
```

**Backend Endpoints Required:**
```python
@app.get("/agents/health")
async def agents_health():
    return {"status": "healthy", "service": "agent-coordinator"}

@app.get("/agents")
async def get_agents():
    # Return available agents
    pass

@app.post("/agents/tasks")
async def create_agent_task(task: AgentTaskRequest):
    # Create new agent task
    pass
```

### **3. Roblox Bridge Integration**
```typescript
// Dashboard integration
import { robloxService } from '../services/roblox';

// Get Roblox worlds
const worlds = await robloxService.getWorlds();

// Start student session
const session = await robloxService.startSession(studentId, worldId);

// Monitor game events
robloxService.subscribeToEvents((event) => {
  console.log('Roblox Event:', event);
});
```

**Backend Endpoints Required:**
```python
@app.get("/roblox/health")
async def roblox_health():
    return {"status": "healthy", "service": "roblox-bridge"}

@app.get("/roblox/worlds")
async def get_roblox_worlds():
    # Return available worlds
    pass

@app.post("/roblox/sessions")
async def create_roblox_session(session: RobloxSessionRequest):
    # Start new game session
    pass
```

### **4. Ghost CMS Integration**
```typescript
// Dashboard integration
import { ghostService } from '../services/ghost';

// Get content
const posts = await ghostService.getPosts();

// Create content
const post = await ghostService.createPost(postData);

// Subscribe to content updates
ghostService.subscribeToEvents((event) => {
  console.log('Ghost Event:', event);
});
```

## 📊 **Docker Hub Repository Setup**

### **Repository Structure**
```
Docker Hub Organization: toolboxai/
├── dashboard:2025.09.27     # Frontend with Pusher + Mantine v8
├── backend:2025.09.27       # FastAPI with all integrations
├── mcp-server:2025.09.27    # Model Context Protocol
├── agent-coordinator:2025.09.27  # AI Agent orchestration
├── roblox-bridge:2025.09.27 # Roblox educational integration
└── ghost-cms:2025.09.27     # Content management system
```

### **Image Tags Strategy**
```bash
# Version tags
toolboxai/dashboard:2025.09.27
toolboxai/dashboard:latest
toolboxai/dashboard:v2.0.0

# Environment tags
toolboxai/dashboard:production
toolboxai/dashboard:staging
toolboxai/dashboard:development

# Feature tags
toolboxai/dashboard:pusher-enabled
toolboxai/dashboard:mantine-v8
```

## 🔐 **Security Configuration**

### **Enhanced CSP Headers**
```nginx
# Updated Content Security Policy for all services
Content-Security-Policy:
  default-src 'self';
  script-src 'self' 'unsafe-inline' 'unsafe-eval'
    https://clerk.toolboxai.app
    https://*.clerk.accounts.dev
    https://js.pusher.com
    https://*.pusher.com;
  style-src 'self' 'unsafe-inline'
    https://fonts.googleapis.com
    https://fonts.gstatic.com;
  font-src 'self' data:
    https://fonts.gstatic.com
    https://fonts.googleapis.com;
  img-src 'self' data: https: blob:;
  connect-src 'self' https: wss: ws:
    https://*.pusher.com
    wss://*.pusher.com
    http://localhost:8009
    http://localhost:9877
    http://localhost:8888
    http://localhost:5001
    http://localhost:8000;
  media-src 'self' data: blob:;
  object-src 'none';
  base-uri 'self';
  form-action 'self';
  frame-ancestors 'self';
```

### **Network Security**
```yaml
# Docker network configuration
networks:
  frontend:
    driver: bridge
    internal: false
  backend:
    driver: bridge
    internal: true
  database:
    driver: bridge
    internal: true
  mcp:
    driver: bridge
    internal: true
```

## 📈 **Monitoring and Health Checks**

### **Service Health Endpoints**
```bash
# Dashboard health
curl http://localhost:5179/health

# Backend health
curl http://localhost:8009/health

# MCP server health
curl http://localhost:5179/mcp/health

# Agent coordinator health
curl http://localhost:5179/agents/health

# Roblox bridge health
curl http://localhost:5179/roblox/health

# Ghost CMS health
curl http://localhost:5179/ghost/health
```

### **Real-time Monitoring**
```bash
# Monitor all services
docker-compose logs -f

# Monitor specific service
docker-compose logs -f dashboard

# Check resource usage
docker stats

# Monitor Pusher connections
# (Check dashboard browser console)
```

## 🚨 **Troubleshooting Guide**

### **Common Issues**

#### **1. Port Conflicts**
```bash
# Check what's using ports
lsof -i :5179,:5179,:8009

# Kill conflicting processes
pkill -f "vite"
lsof -ti:5179 | xargs kill -9
```

#### **2. Build Failures**
```bash
# Clear Docker cache
docker system prune -a

# Rebuild without cache
docker-compose build --no-cache

# Check build logs
docker-compose build --progress=plain
```

#### **3. Pusher Connection Issues**
```bash
# Verify Pusher config
docker exec toolboxai-dashboard-v2 env | grep PUSHER

# Test Pusher connectivity
curl https://js.pusher.com/8.4/pusher.min.js

# Check CSP headers
curl -I http://localhost:5179/
```

#### **4. Service Integration Issues**
```bash
# Test service connectivity
docker exec toolboxai-dashboard-v2 curl http://backend:8009/health
docker exec toolboxai-dashboard-v2 curl http://mcp-server:9877/health

# Check network connectivity
docker network inspect compose_backend
```

## 📋 **Implementation Checklist**

### **Pre-deployment**
- [ ] ✅ Port conflicts resolved
- [ ] ✅ Environment variables configured
- [ ] ✅ Pusher credentials added
- [ ] ✅ Docker Hub access configured

### **Build Process**
- [ ] ✅ Dockerfile updated for Pusher + Mantine v8
- [ ] ✅ Docker Compose configuration updated
- [ ] ✅ Service proxy configurations added
- [ ] ✅ CSP headers updated for all services

### **Service Integration**
- [ ] ✅ MCP service integration implemented
- [ ] ✅ Agent coordinator integration implemented
- [ ] ✅ Roblox bridge integration implemented
- [ ] ✅ Ghost CMS integration implemented

### **Testing**
- [ ] All services start successfully
- [ ] Dashboard loads on port 5179
- [ ] Pusher real-time features work
- [ ] All service proxies functional
- [ ] Health checks pass

### **Documentation**
- [ ] ✅ Docker Hub setup guide created
- [ ] ✅ Service integration guide created
- [ ] ✅ Troubleshooting guide created
- [ ] ✅ Implementation checklist created

## 🎉 **Deployment Commands**

### **Complete Deployment**
```bash
# 1. Navigate to project
cd /Volumes/G-DRIVE\ ArmorATD/Development/Clients/ToolBoxAI-Solutions

# 2. Run complete setup
./infrastructure/docker/scripts/dockerhub-setup.sh

# 3. Configure Pusher credentials
nano infrastructure/docker/config/environment.env

# 4. Deploy all services
./infrastructure/docker/scripts/deploy.sh 2025.09.27 development

# 5. Verify deployment
curl http://localhost:5179/health
open http://localhost:5179
```

### **Quick Update Deployment**
```bash
# For code changes only
docker-compose --env-file infrastructure/docker/config/environment.env up -d --build dashboard

# For configuration changes
docker-compose --env-file infrastructure/docker/config/environment.env down
docker-compose --env-file infrastructure/docker/config/environment.env up -d
```

---

**Status**: ✅ Ready for Implementation
**Estimated Time**: 15-30 minutes
**Dependencies**: Docker, Docker Compose, Pusher account
**Result**: Complete integrated platform on port 5179
