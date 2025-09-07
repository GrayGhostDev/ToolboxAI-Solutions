# CLAUDE.md - ToolboxAI Roblox AI-Powered Educational Environment

> **Expert System**: You are an expert in Roblox game development using Lua, educational technology integration, AI-powered content generation, and multi-agent orchestration systems. This document provides comprehensive guidance for developing, maintaining, and extending the ToolboxAI Roblox Educational Platform.

## 🎮 Project Overview

**ToolboxAI Roblox Environment** - An AI-powered educational platform that generates immersive Roblox educational environments using LangChain/LangGraph multi-agent orchestration, integrated with Learning Management Systems (LMS), featuring automated content generation, quiz creation, and adaptive learning experiences.

### 🎯 Core Capabilities

- **AI-Powered Content Generation**: Automatically generates educational Roblox environments based on curriculum standards
- **Multi-Agent Orchestration**: Uses LangChain/LangGraph for coordinated content creation
- **LMS Integration**: Seamless integration with Schoology, Canvas, and other platforms
- **Real-time Collaboration**: Live editing and content updates via Roblox Studio plugin
- **Adaptive Learning**: Dynamic difficulty adjustment based on student performance
- **Gamification**: Achievement systems, rewards, and progress tracking

## 📁 Complete Repository Structure

```
ToolboxAI-Roblox-Environment/
├── CLAUDE.md                     # This comprehensive documentation
├── mcp/                          # Model Context Protocol Implementation
│   ├── __init__.py
│   ├── server.py                 # MCP WebSocket server (port 9876)
│   ├── context_manager.py        # Context window optimization (128K tokens)
│   ├── memory_store.py           # Vector embedding persistence
│   └── protocols/
│       ├── roblox.py             # Roblox-specific MCP protocols
│       └── education.py          # Educational context protocols
├── agents/                       # LangChain/LangGraph Multi-Agent System
│   ├── __init__.py
│   ├── base_agent.py             # Base agent with SPARC integration
│   ├── supervisor.py             # Hierarchical supervision agent
│   ├── content_agent.py          # Educational content generation
│   ├── quiz_agent.py             # Interactive quiz creation
│   ├── terrain_agent.py          # 3D terrain and environment
│   ├── script_agent.py           # Lua script generation
│   ├── review_agent.py           # Code review and optimization
│   └── orchestrator.py           # LangGraph workflow orchestration
├── sparc/                        # State-Policy-Action-Reward-Context Framework
│   ├── __init__.py
│   ├── state_manager.py          # Environment state tracking
│   ├── policy_engine.py          # Educational policy decisions
│   ├── action_executor.py        # Action execution pipeline
│   ├── reward_calculator.py      # Learning outcome rewards
│   └── context_tracker.py        # User context management
├── swarm/                        # Swarm Intelligence Coordination
│   ├── __init__.py
│   ├── swarm_controller.py       # Swarm orchestration engine
│   ├── worker_pool.py            # Parallel worker management
│   ├── task_distributor.py       # Intelligent task distribution
│   ├── consensus_engine.py       # Quality consensus mechanism
│   └── load_balancer.py          # Resource optimization
├── coordinators/                 # High-Level Coordination Layer
│   ├── __init__.py
│   ├── main_coordinator.py       # Master coordination hub
│   ├── workflow_coordinator.py   # End-to-end workflows
│   ├── resource_coordinator.py   # Resource allocation
│   ├── sync_coordinator.py       # State synchronization
│   └── error_coordinator.py      # Error recovery
├── github/                       # GitHub CI/CD Integration
│   ├── __init__.py
│   ├── .github/
│   │   └── workflows/
│   │       ├── deploy.yml        # Automated deployment
│   │       ├── test.yml          # Test automation
│   │       ├── roblox-sync.yml   # Roblox Studio sync
│   │       └── docs.yml          # Documentation generation
│   ├── hooks/
│   │   ├── pre_commit.py         # Code quality checks
│   │   ├── post_merge.py         # Post-merge actions
│   │   └── pre_push.py           # Security scanning
│   └── integrations/
│       ├── issues.py             # Issue tracking automation
│       ├── releases.py           # Release management
│       └── projects.py           # Project board sync
├── server/                       # Backend Services
│   ├── __init__.py
│   ├── main.py                   # FastAPI main app (port 8008)
│   ├── roblox_server.py          # Flask bridge server (port 5001)
│   ├── tools.py                  # LangChain tool implementations
│   ├── agent.py                  # Agent initialization
│   ├── models.py                 # Pydantic data models
│   ├── config.py                 # Configuration management
│   ├── auth.py                   # Authentication handlers
│   └── websocket.py              # WebSocket connections
├── Roblox/                       # Roblox Game Components
│   ├── Plugins/
│   │   └── AIContentGenerator.lua # Roblox Studio plugin (port 64989)
│   ├── Scripts/
│   │   ├── ServerScripts/
│   │   │   ├── Main.server.lua
│   │   │   ├── GameManager.lua
│   │   │   └── DataStore.lua
│   │   ├── ClientScripts/
│   │   │   ├── UI.client.lua
│   │   │   └── Input.client.lua
│   │   └── ModuleScripts/
│   │       ├── QuizSystem.lua
│   │       ├── GamificationHub.lua
│   │       └── NavigationMenu.lua
│   └── Templates/
│       ├── Terrain/
│       ├── UI/
│       └── GameMechanics/
├── API/                          # Existing Integration Points
│   ├── Dashboard/                # React dashboard (port 3000)
│   └── GhostBackend/             # Ghost CMS backend (port 2368)
├── tests/                        # Comprehensive Testing
│   ├── unit/
│   ├── integration/
│   ├── e2e/
│   └── performance/
└── docker/                       # Containerization
    ├── docker-compose.yml
    ├── Dockerfile.api
    ├── Dockerfile.mcp
    └── Dockerfile.agents
```

## 🤖 Roblox Development Expertise

### Core Roblox Concepts You Must Know

#### 1. **Instance Hierarchy**
```lua
-- Roblox service access pattern
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local TweenService = game:GetService("TweenService")
local DataStoreService = game:GetService("DataStoreService")
local HttpService = game:GetService("HttpService")
```

#### 2. **Client-Server Architecture**
```lua
-- RemoteEvent for client-server communication
local remoteEvent = ReplicatedStorage:WaitForChild("RemoteEvent")

-- Server side
remoteEvent.OnServerEvent:Connect(function(player, data)
    -- Validate and process client data
    if typeof(data) == "table" and data.action then
        processAction(player, data)
    end
end)

-- Client side
remoteEvent:FireServer({action = "quiz_answer", answer = selectedOption})
```

#### 3. **Best Practices**
- **Never trust the client**: All validation on server
- **Use ModuleScripts**: For reusable code
- **Optimize for performance**: Use object pooling, limit part count
- **Handle network latency**: Predictive movement, interpolation
- **Secure RemoteEvents**: Rate limiting, sanity checks

## 🧠 AI Agent Architecture

### LangChain/LangGraph Multi-Agent System

#### Agent Hierarchy
```python
# agents/supervisor.py
class SupervisorAgent:
    """Orchestrates all sub-agents using LangGraph state management"""
    
    def __init__(self):
        self.graph = StateGraph(AgentState)
        self.setup_nodes()
        self.setup_edges()
    
    def route_task(self, state: AgentState) -> str:
        """Intelligent task routing based on content type"""
        if "quiz" in state.task_description:
            return "quiz_agent"
        elif "terrain" in state.task_description:
            return "terrain_agent"
        elif "script" in state.task_description:
            return "script_agent"
        return "content_agent"
```

#### SPARC Framework Integration
```python
# sparc/state_manager.py
class SPARCStateManager:
    """Manages agent state using SPARC framework"""
    
    def __init__(self):
        self.state = {}  # Current environment state
        self.policy = EducationalPolicy()  # Decision policy
        self.actions = ActionQueue()  # Pending actions
        self.rewards = RewardTracker()  # Learning outcomes
        self.context = ContextWindow()  # User context
    
    async def execute_cycle(self):
        """Execute one SPARC cycle"""
        state = await self.observe_state()
        action = self.policy.decide(state, self.context)
        result = await self.execute_action(action)
        reward = self.calculate_reward(result)
        self.update_policy(state, action, reward)
```

### Swarm Intelligence
```python
# swarm/swarm_controller.py
class SwarmController:
    """Manages parallel agent execution"""
    
    def __init__(self, num_workers=5):
        self.workers = WorkerPool(num_workers)
        self.task_queue = asyncio.Queue()
        self.consensus = ConsensusEngine()
    
    async def distribute_tasks(self, tasks: List[Task]):
        """Distribute tasks across worker agents"""
        for task in tasks:
            worker = await self.workers.get_available()
            asyncio.create_task(worker.execute(task))
        
        # Wait for consensus on results
        results = await self.workers.gather_results()
        return await self.consensus.evaluate(results)
```

## Development Commands

### Root Level
```bash
# Install dependencies
npm install

# Build TypeScript
npm run build

# Start Ghost backend
npm start
```

### Dashboard (API/Dashboard)
```bash
cd API/Dashboard

# Development server
npm run dev

# Build for production
npm run build

# Run tests
npm test
npm run test:coverage

# Code quality
npm run lint
npm run typecheck
```

### Ghost Backend (API/GhostBackend)
```bash
cd API/GhostBackend

# Setup development environment
./bin/setup.sh
./bin/dev_setup.sh

# Start backend services
./bin/start_backend.sh    # Full stack (API + DB + Redis)
./bin/run_api.sh          # API only

# Stop services
./bin/stop_backend.sh
./bin/stop_api.sh

# Database management
make db/start
make db/stop
make db/status
alembic upgrade head      # Apply migrations

# Run tests
pytest
pytest --cov=src/ghost --cov-report=html

# Code quality
black src/ && isort src/ && flake8 src/ && mypy src/
```

### Roblox Development
```bash
# Roblox Studio workflow:
# 1. Open Roblox Studio
# 2. Load Roblox/src/Main.server.lua as entry point
# 3. Import modules from Roblox/src/Modules/
# 4. Configure API endpoints in Roblox/Config/settings.lua
```

## Architecture Overview

### Technology Stack

**Frontend (Dashboard)**
- React 18 with TypeScript
- Material-UI (MUI) for components
- Redux Toolkit for state management
- Vite for build tooling
- Vitest for testing
- Socket.io for real-time updates

**Backend (Ghost)**
- FastAPI for API framework
- SQLAlchemy (async) for ORM
- PostgreSQL for database
- Redis for caching/sessions
- JWT for authentication
- Alembic for migrations
- pytest for testing

**Roblox Integration**
- Lua scripting
- HTTP service for API calls
- ReplicatedStorage for data management

### Key Integration Points

1. **Authentication Flow**
   - Ghost backend manages JWT tokens
   - Dashboard authenticates users via Ghost API
   - Roblox validates tokens through Ghost backend

2. **API Communication**
   - Ghost backend serves as central API (port 8000/8080)
   - Dashboard connects via Axios HTTP client
   - Roblox uses HttpService for API calls

3. **Real-time Features**
   - WebSocket support in Ghost backend
   - Socket.io client in Dashboard
   - Event-driven updates across platforms

## Core Ghost Backend Modules

- `src/ghost/config.py` - Configuration management (env, YAML, JSON)
- `src/ghost/database.py` - Async SQLAlchemy with connection pooling
- `src/ghost/auth.py` - JWT authentication with RBAC
- `src/ghost/api.py` - FastAPI integration with middleware
- `src/ghost/models.py` - Base models and repository pattern
- `src/ghost/email.py` - Email sending capabilities
- `src/ghost/tasks.py` - Background task processing
- `src/ghost/storage.py` - File upload management
- `src/ghost/websocket.py` - Real-time communication

## Development Workflow

### Adding New Features

1. **Backend Endpoint**
   - Create route in Ghost backend
   - Use dependency injection for DB/auth
   - Return standardized APIResponse
   - Add tests in tests/

2. **Dashboard Integration**
   - Add API client method
   - Create Redux slice if needed
   - Build React components
   - Add routing if new page

3. **Roblox Integration**
   - Update API module in Roblox/API/
   - Implement game logic in Lua
   - Handle responses appropriately

### Testing Strategy

```bash
# Backend tests
cd API/GhostBackend
pytest -m "unit"          # Unit tests
pytest -m "integration"   # Integration tests

# Dashboard tests
cd API/Dashboard
npm test                  # Run all tests
npm run test:ui          # Interactive UI

# Roblox testing
# Use Roblox Studio test mode
```

## Security Configuration

- **All services bound to 127.0.0.1** (not 0.0.0.0)
- **JWT secrets in environment variables**
- **Database credentials secured** (macOS Keychain on dev)
- **CORS configured per frontend**
- **Input validation with Pydantic**
- **SQL injection protection via ORM**

## Environment Variables

Create `.env` files in respective directories:

**Ghost Backend (.env)**
```
DATABASE_URL=postgresql://user:pass@localhost/db
REDIS_URL=redis://localhost:6379
JWT_SECRET_KEY=your-secret-key
API_HOST=127.0.0.1
API_PORT=8000
LOG_LEVEL=INFO
```

**Dashboard (.env)**
```
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000
```

## API Documentation

When Ghost backend is running:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- Health check: http://localhost:8000/health

## Database Schema

Use Alembic for migrations:
```bash
cd API/GhostBackend
alembic revision --autogenerate -m "description"
alembic upgrade head
```

## Deployment Notes

- Use reverse proxy (nginx) for production
- Configure SSL/TLS certificates
- Set production environment variables
- Run database migrations before deployment
- Use process manager (systemd/supervisor) for backend

## Common Issues and Solutions

### Port Conflicts
- Check if ports 8000, 5432 (PostgreSQL), 6379 (Redis) are free
- Modify port configurations in respective config files

### Database Connection
```bash
cd API/GhostBackend
make db/status           # Check database status
psql $DATABASE_URL      # Test connection directly
```

### Module Import Errors
- Ensure virtual environment is activated
- Install Ghost backend: `pip install -e .`
- Verify all dependencies: `pip install -r requirements.txt`

## Development Best Practices

- Follow existing code patterns and conventions
- Use type hints in Python code
- Use TypeScript strict mode in Dashboard
- Write tests for new functionality
- Use standardized API responses
- Handle errors gracefully
- Log important operations
- Document complex logic

## 🔧 Complete Implementation Components

### 1. LangChain Tools Implementation (server/tools.py)

```python
import os
from typing import Optional, List, Dict, Tuple
from langchain.tools import BaseTool, tool
from langchain_community.tools import WikipediaQueryRun, DuckDuckGoSearchRun
from pydantic import BaseModel, Field
import requests
from requests_oauthlib import OAuth1
import json

# LMS Authentication
class LMSAuthentication:
    @staticmethod
    def get_schoology_auth() -> OAuth1:
        return OAuth1(
            client_key=os.getenv('SCHOOLOGY_KEY'),
            client_secret=os.getenv('SCHOOLOGY_SECRET')
        )
    
    @staticmethod
    def get_canvas_headers() -> Dict:
        return {
            'Authorization': f"Bearer {os.getenv('CANVAS_TOKEN')}"
        }

# Tool Definitions
class LMSSubjectLookup(BaseTool):
    name = "lms_subject_lookup"
    description = "Fetches course content from LMS platforms"
    
    def _run(self, course_id: str, platform: str = "schoology") -> str:
        if platform == "schoology":
            auth = LMSAuthentication.get_schoology_auth()
            response = requests.get(
                f"https://api.schoology.com/v1/courses/{course_id}",
                auth=auth
            )
        elif platform == "canvas":
            headers = LMSAuthentication.get_canvas_headers()
            response = requests.get(
                f"https://canvas.instructure.com/api/v1/courses/{course_id}",
                headers=headers
            )
        return response.json()

class GenerateRobloxTerrain(BaseTool):
    name = "generate_roblox_terrain"
    description = "Generates Roblox terrain based on educational theme"
    
    def _run(self, theme: str, size: str = "medium") -> str:
        terrain_script = f"""
        local Terrain = workspace.Terrain
        local Region = Region3.new(Vector3.new(-100, -50, -100), Vector3.new(100, 50, 100))
        Region = Region:ExpandToGrid(4)
        
        -- Generate themed terrain for {theme}
        if "{theme}" == "ocean" then
            Terrain:FillWater(Region, Vector3.new(0, 25, 0))
        elseif "{theme}" == "forest" then
            Terrain:FillBlock(Region.CFrame, Region.Size, Enum.Material.Grass)
        end
        """
        return terrain_script

class GenerateQuizTool(BaseTool):
    name = "generate_quiz"
    description = "Creates interactive quiz for Roblox"
    
    def _run(self, subject: str, difficulty: str, num_questions: int = 5) -> Dict:
        # Generate quiz based on subject and difficulty
        quiz_data = {
            "questions": [],
            "subject": subject,
            "difficulty": difficulty
        }
        # AI generates questions here
        return quiz_data

# Export all tools
ALL_TOOLS = [
    LMSSubjectLookup(),
    DuckDuckGoSearchRun(),
    WikipediaQueryRun(),
    GenerateRobloxTerrain(),
    GenerateQuizTool()
]
```

### 2. FastAPI Main Application (server/main.py)

```python
import asyncio
import subprocess
import time
from fastapi import FastAPI, WebSocket, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, List, Optional
import uvicorn
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from tools import ALL_TOOLS
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI app initialization
app = FastAPI(
    title="ToolboxAI Roblox Education API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Data models
class ContentRequest(BaseModel):
    subject: str
    grade_level: int
    learning_objectives: List[str]
    environment_type: str = "classroom"
    include_quiz: bool = True

class ContentResponse(BaseModel):
    success: bool
    content: Dict
    scripts: List[str]
    message: str

# Global agent instance
llm = ChatOpenAI(model="gpt-4", temperature=0.7)
agent = create_react_agent(llm, ALL_TOOLS)

# Ensure Flask server is running
def ensure_flask_server_running():
    try:
        response = requests.get("http://localhost:5001/health")
        if response.status_code == 200:
            logger.info("Flask server is running")
            return True
    except:
        logger.info("Starting Flask server...")
        subprocess.Popen(["python", "server/roblox_server.py"])
        time.sleep(3)
    return True

@app.on_event("startup")
async def startup_event():
    ensure_flask_server_running()
    logger.info("FastAPI server started on port 8008")

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "ToolboxAI-Roblox-API"}

@app.post("/generate_content", response_model=ContentResponse)
async def generate_content(request: ContentRequest):
    """Generate educational Roblox content based on requirements"""
    try:
        # Prepare agent prompt
        prompt = f"""
        Create an educational Roblox environment for:
        Subject: {request.subject}
        Grade Level: {request.grade_level}
        Learning Objectives: {', '.join(request.learning_objectives)}
        Environment Type: {request.environment_type}
        Include Quiz: {request.include_quiz}
        
        Generate complete Lua scripts for implementation.
        """
        
        # Execute agent
        result = await agent.ainvoke({"messages": [prompt]})
        
        return ContentResponse(
            success=True,
            content=result,
            scripts=result.get("scripts", []),
            message="Content generated successfully"
        )
    except Exception as e:
        logger.error(f"Content generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket for real-time updates"""
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            # Process and respond
            await websocket.send_text(f"Processed: {data}")
    except:
        await websocket.close()

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8008)
```

### 3. Roblox Studio Plugin (Roblox/Plugins/AIContentGenerator.lua)

```lua
-- AI Content Generator Plugin for Roblox Studio
local PLUGIN_PORT = 64989
local FLASK_SERVER_URL = "http://localhost:5001"
local API_SERVER_URL = "http://localhost:8008"

local toolbar = plugin:CreateToolbar("AI Content Generator")
local button = toolbar:CreateButton(
    "Generate Content",
    "Generate AI-powered educational content",
    "rbxasset://textures/ui/GuiImagePlaceholder.png"
)

local HttpService = game:GetService("HttpService")
local Selection = game:GetService("Selection")
local ChangeHistoryService = game:GetService("ChangeHistoryService")

-- Plugin state
local pluginGui = nil
local isConnected = false

-- Create plugin GUI
local function createGUI()
    local screenGui = plugin:CreateDockWidgetPluginGui(
        "AIContentGenerator",
        DockWidgetPluginGuiInfo.new(
            Enum.InitialDockState.Float,
            true,
            false,
            400,
            300,
            400,
            300
        )
    )
    screenGui.Title = "AI Content Generator"
    
    local frame = Instance.new("Frame")
    frame.Size = UDim2.new(1, 0, 1, 0)
    frame.Parent = screenGui
    
    -- Add UI elements
    local generateButton = Instance.new("TextButton")
    generateButton.Text = "Generate Educational Content"
    generateButton.Size = UDim2.new(0.9, 0, 0.1, 0)
    generateButton.Position = UDim2.new(0.05, 0, 0.1, 0)
    generateButton.Parent = frame
    
    generateButton.MouseButton1Click:Connect(function()
        generateContent()
    end)
    
    return screenGui
end

-- Register with Flask server
local function registerPlugin()
    local success, result = pcall(function()
        return HttpService:RequestAsync({
            Url = FLASK_SERVER_URL .. "/register_plugin",
            Method = "POST",
            Headers = {["Content-Type"] = "application/json"},
            Body = HttpService:JSONEncode({
                port = PLUGIN_PORT,
                studio_id = plugin:GetStudioUserId()
            })
        })
    end)
    
    if success and result.StatusCode == 200 then
        isConnected = true
        print("Plugin registered with server")
    else
        warn("Failed to register plugin")
    end
end

-- Generate content
local function generateContent()
    if not isConnected then
        registerPlugin()
    end
    
    local response = HttpService:RequestAsync({
        Url = API_SERVER_URL .. "/generate_content",
        Method = "POST",
        Headers = {["Content-Type"] = "application/json"},
        Body = HttpService:JSONEncode({
            subject = "Mathematics",
            grade_level = 5,
            learning_objectives = {"Fractions", "Decimals"},
            environment_type = "interactive_classroom"
        })
    })
    
    if response.StatusCode == 200 then
        local data = HttpService:JSONDecode(response.Body)
        implementContent(data)
    end
end

-- Implement generated content
local function implementContent(data)
    ChangeHistoryService:SetWaypoint("Before AI Content")
    
    for _, scriptContent in ipairs(data.scripts) do
        local func, err = loadstring(scriptContent)
        if func then
            func()
        else
            warn("Script error: " .. err)
        end
    end
    
    ChangeHistoryService:SetWaypoint("After AI Content")
    print("Content implemented successfully")
end

-- Plugin activation
button.Click:Connect(function()
    if not pluginGui then
        pluginGui = createGUI()
    end
    pluginGui.Enabled = not pluginGui.Enabled
end)

-- Initialize
registerPlugin()
```

### 4. MCP Server Implementation (mcp/server.py)

```python
import asyncio
import websockets
import json
from typing import Dict, Set
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class MCPServer:
    """Model Context Protocol server for managing agent context"""
    
    def __init__(self, port=9876):
        self.port = port
        self.clients: Set[websockets.WebSocketServerProtocol] = set()
        self.context_store = {}
        self.memory_limit = 128000  # 128K token limit
    
    async def register(self, websocket):
        self.clients.add(websocket)
        await self.send_context(websocket)
    
    async def unregister(self, websocket):
        self.clients.discard(websocket)
    
    async def handle_message(self, websocket, message):
        data = json.loads(message)
        
        if data["type"] == "update_context":
            self.update_context(data["context"])
            await self.broadcast_context()
        elif data["type"] == "get_context":
            await self.send_context(websocket)
        elif data["type"] == "clear_context":
            self.context_store.clear()
            await self.broadcast_context()
    
    def update_context(self, new_context: Dict):
        """Update context with token limit management"""
        timestamp = datetime.now().isoformat()
        self.context_store[timestamp] = new_context
        
        # Prune old context if exceeding limit
        self.prune_context()
    
    def prune_context(self):
        """Remove old context to stay within token limit"""
        total_tokens = sum(len(str(c)) for c in self.context_store.values())
        
        if total_tokens > self.memory_limit:
            # Remove oldest entries
            sorted_keys = sorted(self.context_store.keys())
            while total_tokens > self.memory_limit and sorted_keys:
                del self.context_store[sorted_keys.pop(0)]
                total_tokens = sum(len(str(c)) for c in self.context_store.values())
    
    async def send_context(self, websocket):
        await websocket.send(json.dumps({
            "type": "context",
            "data": self.context_store
        }))
    
    async def broadcast_context(self):
        if self.clients:
            await asyncio.gather(
                *[self.send_context(client) for client in self.clients]
            )
    
    async def handler(self, websocket, path):
        await self.register(websocket)
        try:
            async for message in websocket:
                await self.handle_message(websocket, message)
        finally:
            await self.unregister(websocket)
    
    async def start(self):
        logger.info(f"Starting MCP server on port {self.port}")
        async with websockets.serve(self.handler, "localhost", self.port):
            await asyncio.Future()  # Run forever

if __name__ == "__main__":
    server = MCPServer()
    asyncio.run(server.start())
```

### 5. GitHub Actions Workflow (.github/workflows/deploy.yml)

```yaml
name: Deploy ToolboxAI Roblox Environment

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-cov
      
      - name: Run tests
        run: |
          pytest tests/ --cov=server --cov-report=xml
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3

  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Run linters
        run: |
          pip install black flake8 mypy
          black --check server/
          flake8 server/
          mypy server/

  deploy:
    needs: [test, lint]
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Build Docker images
        run: |
          docker build -t toolboxai-api:latest -f docker/Dockerfile.api .
          docker build -t toolboxai-mcp:latest -f docker/Dockerfile.mcp .
          docker build -t toolboxai-agents:latest -f docker/Dockerfile.agents .
      
      - name: Deploy to production
        env:
          DEPLOY_KEY: ${{ secrets.DEPLOY_KEY }}
        run: |
          # Deploy to your infrastructure
          echo "Deploying to production..."

  sync-roblox:
    needs: deploy
    runs-on: windows-latest
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Install Rojo
        run: |
          cargo install rojo
      
      - name: Build Roblox project
        run: |
          rojo build -o game.rbxl
      
      - name: Upload to Roblox
        env:
          ROBLOX_API_KEY: ${{ secrets.ROBLOX_API_KEY }}
        run: |
          # Upload using Roblox API
          echo "Uploading to Roblox..."
```

## 🚀 Quick Start Guide

### Prerequisites

1. **Python 3.11+** with pip
2. **Node.js 18+** with npm
3. **Roblox Studio** installed
4. **Docker** and **Docker Compose**
5. **PostgreSQL 15+** and **Redis 7+**
6. **API Keys**:
   - OpenAI API key
   - Schoology/Canvas API credentials
   - GitHub personal access token

### Installation

```bash
# Clone repository
git clone https://github.com/your-org/ToolboxAI-Roblox-Environment.git
cd ToolboxAI-Roblox-Environment

# Install Python dependencies
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Install Node dependencies
npm install
cd API/Dashboard && npm install
cd ../GhostBackend && pip install -e .

# Set up environment variables
cp .env.example .env
# Edit .env with your API keys and configuration

# Start all services
docker-compose up -d

# Start MCP server
python mcp/server.py &

# Start FastAPI server
python server/main.py &

# Start Flask bridge server
python server/roblox_server.py &

# Open Roblox Studio and install plugin
# File -> Plugins -> Manage Plugins -> Install from File
# Select: Roblox/Plugins/AIContentGenerator.lua
```

## 📚 API Documentation

### Core Endpoints

#### Generate Educational Content
```http
POST /generate_content
Host: localhost:8008
Content-Type: application/json

{
  "subject": "Science",
  "grade_level": 7,
  "learning_objectives": ["Solar System", "Planets"],
  "environment_type": "space_station",
  "include_quiz": true
}
```

#### WebSocket Connection
```javascript
const ws = new WebSocket('ws://localhost:8008/ws');
ws.onmessage = (event) => {
  console.log('Received:', event.data);
};
```

#### Plugin Registration
```http
POST /register_plugin
Host: localhost:5001
Content-Type: application/json

{
  "port": 64989,
  "studio_id": "user-123"
}
```

## 🧪 Testing

### Run All Tests
```bash
# Unit tests
pytest tests/unit/

# Integration tests
pytest tests/integration/

# E2E tests
pytest tests/e2e/

# Performance tests
pytest tests/performance/ --benchmark-only

# Coverage report
pytest --cov=server --cov=agents --cov=mcp --cov-report=html
```

### Roblox Studio Testing
1. Open Roblox Studio
2. Load test place from `Roblox/TestPlace.rbxl`
3. Run plugin tests via command bar:
```lua
require(game.ServerScriptService.Tests.RunAll)()
```

## 🔒 Security Considerations

1. **API Security**
   - JWT authentication for all endpoints
   - Rate limiting: 100 requests/minute per IP
   - Input validation with Pydantic
   - SQL injection prevention via ORM

2. **Roblox Security**
   - Server-side validation for all RemoteEvents
   - Sanity checks on client data
   - Anti-exploit measures
   - DataStore encryption for sensitive data

3. **LMS Integration Security**
   - OAuth 2.0 for authentication
   - Encrypted token storage
   - Regular token rotation
   - Audit logging for all LMS operations

## 🎯 Performance Optimization

### Agent Optimization
- **Caching**: Redis cache for frequent queries
- **Parallelization**: Swarm execution for independent tasks
- **Token Management**: Efficient context window usage
- **Model Selection**: Use appropriate model sizes

### Roblox Optimization
- **StreamingEnabled**: For large worlds
- **Level of Detail (LOD)**: Reduce complexity at distance
- **Object Pooling**: Reuse instances
- **Network Optimization**: Batch RemoteEvent calls

## 📈 Monitoring & Analytics

### Metrics Collection
```python
# Prometheus metrics
from prometheus_client import Counter, Histogram

content_generated = Counter('content_generated_total', 'Total content generated')
generation_time = Histogram('generation_duration_seconds', 'Time to generate content')
```

### Dashboard Access
- **Grafana**: http://localhost:3001
- **Prometheus**: http://localhost:9090
- **LangSmith**: https://smith.langchain.com

## 🤝 Contributing

### Development Workflow
1. Create feature branch: `git checkout -b feature/your-feature`
2. Make changes and test thoroughly
3. Run linters: `make lint`
4. Commit with conventional commits: `feat: add new feature`
5. Push and create pull request
6. Wait for CI/CD checks
7. Request review from team

### Code Style
- **Python**: Black formatter, PEP 8
- **TypeScript**: Prettier, ESLint
- **Lua**: Roblox style guide

## 🐛 Troubleshooting

### Common Issues

#### Plugin Not Connecting
```bash
# Check if servers are running
curl http://localhost:5001/health
curl http://localhost:8008/health

# Check firewall settings
sudo ufw allow 5001
sudo ufw allow 8008
sudo ufw allow 64989
```

#### Agent Errors
```python
# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Check LangSmith traces
# Visit: https://smith.langchain.com
```

#### Memory Issues
```bash
# Increase Docker memory
docker-compose down
export DOCKER_MEMORY=8g
docker-compose up -d
```

## 📖 Additional Resources

- [Roblox Developer Hub](https://developer.roblox.com)
- [LangChain Documentation](https://docs.langchain.com)
- [LangGraph Guide](https://langchain-ai.github.io/langgraph/)
- [FastAPI Documentation](https://fastapi.tiangolo.com)
- [Project Wiki](https://github.com/your-org/ToolboxAI-Roblox/wiki)

---

*ToolboxAI Roblox Environment - AI-Powered Educational Platform*
*Version 2.0.0 | Licensed under MIT*