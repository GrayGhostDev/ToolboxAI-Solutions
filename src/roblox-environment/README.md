# ToolboxAI Roblox Environment 🎮🤖

[![Version](https://img.shields.io/badge/version-0.9.0-blue.svg)](https://github.com/ToolBoxAI-Solutions/ToolboxAI-Roblox-Environment/releases)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://python.org)
[![Roblox](https://img.shields.io/badge/roblox-studio-00A2FF.svg)](https://developer.roblox.com)
[![AI Powered](https://img.shields.io/badge/AI-Powered-orange.svg)](https://openai.com)
[![Implementation](https://img.shields.io/badge/implementation-90%25-green.svg)](IMPLEMENTATION_STATUS.md)

> **An AI-powered educational platform that generates immersive Roblox educational environments using advanced multi-agent orchestration, featuring automated content generation, adaptive learning, and seamless LMS integration.**

## 🌟 Key Features

- **🤖 AI-Powered Content Generation**: Multi-agent system creates educational Roblox environments automatically
- **🧠 Advanced Agent Architecture**: LangChain/LangGraph orchestration with SPARC framework integration
- **🎓 LMS Integration**: Seamless connectivity with Schoology, Canvas, and other learning platforms
- **🔄 Real-time Collaboration**: Live editing via Roblox Studio plugin with WebSocket communication
- **📊 Adaptive Learning**: Dynamic difficulty adjustment based on student performance analytics
- **🏆 Gamification System**: Achievement tracking, rewards, and progress visualization
- **🌐 Model Context Protocol (MCP)**: Advanced context management with 128K token optimization
- **⚡ Swarm Intelligence**: Parallel agent execution with consensus-based quality assurance

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                    ToolboxAI Roblox Environment                     │
├─────────────────────────────────────────────────────────────────────┤
│                          Frontend Layer                             │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐     │
│  │   Roblox Studio │  │    Dashboard    │  │   Ghost CMS     │     │
│  │     Plugin      │  │   (React)       │  │   Backend       │     │
│  │   :64989        │  │   :3000         │  │   :2368         │     │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘     │
├─────────────────────────────────────────────────────────────────────┤
│                        API Gateway Layer                            │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐     │
│  │   FastAPI       │  │  Flask Bridge   │  │  MCP Server     │     │
│  │   Server        │  │     Server      │  │  (WebSocket)    │     │
│  │   :8008         │  │     :5001       │  │     :9876       │     │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘     │
├─────────────────────────────────────────────────────────────────────┤
│                     AI Agent Orchestration                          │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐     │
│  │   Supervisor    │  │  Content Agent  │  │  Quiz Agent     │     │
│  │     Agent       │  │                 │  │                 │     │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘     │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐     │
│  │  Terrain Agent  │  │  Script Agent   │  │  Review Agent   │     │
│  │                 │  │                 │  │                 │     │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘     │
├─────────────────────────────────────────────────────────────────────┤
│                      Intelligence Frameworks                        │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐     │
│  │ SPARC Framework │  │ Swarm Control   │  │  Coordinators   │     │
│  │ (State-Policy-  │  │ (Parallel       │  │ (Workflow       │     │
│  │  Action-Reward- │  │  Execution)     │  │  Management)    │     │
│  │  Context)       │  │                 │  │                 │     │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘     │
├─────────────────────────────────────────────────────────────────────┤
│                        External Integrations                        │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐     │
│  │      LMS        │  │     GitHub      │  │    Database     │     │
│  │  (Schoology/    │  │   Actions       │  │   PostgreSQL    │     │
│  │   Canvas)       │  │   CI/CD         │  │     Redis       │     │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘     │
└─────────────────────────────────────────────────────────────────────┘
```

## 🚀 Quick Start

### Prerequisites

- **Python 3.11+** with pip
- **Node.js 18+** with npm  
- **Roblox Studio** (latest version)
- **Docker & Docker Compose** (optional)
- **API Keys**: OpenAI, Schoology/Canvas, GitHub

### 1. Installation

```bash
# Clone the repository
git clone https://github.com/ToolBoxAI-Solutions/ToolboxAI-Roblox-Environment.git
cd ToolboxAI-Roblox-Environment

# Install Python dependencies
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Install Node.js dependencies
npm install
cd API/Dashboard && npm install && cd ../..
```

### 2. Environment Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your API keys and settings
# Required: OPENAI_API_KEY, SCHOOLOGY_KEY, SCHOOLOGY_SECRET
```

### 3. Start All Services

```bash
# Option 1: Start all services with Docker
docker-compose up -d

# Option 2: Start services individually
python mcp/server.py &           # MCP WebSocket server (:9876)
python server/main.py &          # FastAPI server (:8008) 
python server/roblox_server.py & # Flask bridge (:5001)

# Start existing API services
cd API/GhostBackend && npm start &    # Ghost CMS (:2368)
cd API/Dashboard && npm run dev &     # React dashboard (:3000)
```

### 4. Install Roblox Studio Plugin

1. Open Roblox Studio
2. Go to **Plugins** → **Manage Plugins** → **Install from File**
3. Select: `Roblox/Plugins/AIContentGenerator.lua`
4. Plugin will appear in toolbar as "AI Content Generator"

### 5. Verify Installation

```bash
# Test API endpoints
curl http://127.0.0.1:8008/health    # FastAPI health check
curl http://127.0.0.1:5001/health    # Flask bridge health check

# Access web interfaces
open http://127.0.0.1:8008/docs      # FastAPI Swagger UI
open http://127.0.0.1:3000           # Dashboard
open http://127.0.0.1:2368/admin     # Ghost CMS admin
```

## 📚 Component Overview (90% Complete)

### ✅ Completed Components

| Component | Files | Status | Description |
|-----------|-------|--------|-------------|
| **MCP System** | 5/5 | ✅ 100% | WebSocket context management with 128K optimization |
| **AI Agents** | 9/9 | ✅ 100% | Multi-agent orchestration with LangChain/LangGraph |
| **SPARC Framework** | 6/6 | ✅ 100% | State-Policy-Action-Reward-Context intelligence |
| **Swarm Intelligence** | 6/6 | ✅ 100% | Parallel execution with consensus mechanisms |
| **Coordinators** | 6/6 | ✅ 100% | High-level workflow and resource management |
| **Server Implementation** | 9/9 | ✅ 100% | FastAPI + Flask with WebSocket support |
| **GitHub Integration** | 15/15 | ✅ 100% | Complete CI/CD pipeline with automation |
| **Documentation** | 1/1 | ✅ 100% | Comprehensive CLAUDE.md guide |

### 🚧 Remaining Components (10%)

| Component | Files | Status | Description |
|-----------|-------|--------|-------------|
| **Roblox Scripts** | 0/6 | 🔄 0% | Studio plugin and game scripts |

**Total Progress: 57/63 files completed (90.5%)**

## 🛠️ API Documentation

### FastAPI Server (Port 8008)

#### Generate Educational Content
```http
POST /generate_content
Content-Type: application/json

{
  "subject": "Science",
  "grade_level": 7,
  "learning_objectives": ["Solar System", "Gravity", "Orbital Mechanics"],
  "environment_type": "space_station",
  "include_quiz": true,
  "difficulty_level": "intermediate"
}
```

#### Real-time WebSocket
```javascript
const ws = new WebSocket('ws://localhost:8008/ws');
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Content update:', data);
};
```

#### Health Monitoring
```http
GET /health          # System health status
GET /metrics         # Prometheus metrics
GET /agents/status   # AI agent pool status
```

### Flask Bridge Server (Port 5001)

#### Plugin Registration
```http
POST /register_plugin
Content-Type: application/json

{
  "port": 64989,
  "studio_id": "user-12345",
  "capabilities": ["terrain", "scripts", "ui"]
}
```

## 🎮 Roblox Integration

### Studio Plugin Usage

1. **Content Generation**
   - Click "AI Content Generator" in toolbar
   - Select subject and grade level
   - Choose environment type (classroom, laboratory, outdoor, space)
   - AI generates complete educational environment

2. **Script Generation**
   - Request specific game mechanics
   - AI creates optimized Lua scripts
   - Automatic integration with existing systems

3. **Quiz Integration**
   - AI generates interactive quizzes
   - Automatic UI creation
   - Progress tracking and analytics

### Lua API Examples

```lua
-- Educational content integration
local EducationAPI = require(game.ReplicatedStorage.EducationAPI)

-- Generate quiz
local quiz = EducationAPI:GenerateQuiz({
    subject = "Mathematics",
    topic = "Fractions",
    difficulty = "beginner",
    questionCount = 5
})

-- Track student progress
EducationAPI:TrackProgress(player, {
    subject = "Mathematics",
    score = 85,
    timeSpent = 300,
    completedObjectives = {"Understand fractions", "Compare fractions"}
})
```

## 🧠 AI Agent System

### Multi-Agent Architecture

- **Supervisor Agent**: Orchestrates all sub-agents using LangGraph
- **Content Agent**: Generates educational materials and environments
- **Quiz Agent**: Creates interactive assessments with multiple formats
- **Terrain Agent**: Builds 3D landscapes using Perlin noise algorithms
- **Script Agent**: Generates and optimizes Lua code
- **Review Agent**: Quality assurance and code optimization

### SPARC Framework Integration

```python
# State-Policy-Action-Reward-Context cycle
state = await sparc.observe_environment()
policy = sparc.policy_engine.decide(state, context)
action = await sparc.execute_action(policy)
reward = sparc.calculate_educational_reward(action, outcomes)
context = sparc.update_context(state, action, reward)
```

## 🔧 Development

### Project Structure

```
ToolboxAI-Roblox-Environment/
├── mcp/                    # Model Context Protocol
├── agents/                 # LangChain/LangGraph agents
├── sparc/                  # SPARC framework
├── swarm/                  # Swarm intelligence
├── coordinators/           # High-level coordination
├── server/                 # FastAPI + Flask servers
├── Roblox/                 # Roblox Studio components
├── API/                    # Existing Dashboard/Ghost backend
├── .github/workflows/      # CI/CD pipelines
└── tests/                  # Comprehensive test suite
```

### Running Tests

```bash
# Run all tests
pytest tests/ -v --cov=server --cov=agents --cov=mcp

# Run specific test categories
pytest tests/unit/          # Unit tests
pytest tests/integration/   # Integration tests
pytest tests/e2e/           # End-to-end tests

# Performance benchmarks
pytest tests/performance/ --benchmark-only
```

### Code Quality

```bash
# Format code
black server/ agents/ mcp/ sparc/ swarm/ coordinators/

# Check linting
flake8 server/ agents/ mcp/

# Type checking
mypy server/ agents/ mcp/
```

## 📊 Monitoring & Analytics

### Metrics Dashboard

- **Content Generation**: Success rate, generation time, quality scores
- **Student Engagement**: Time in environment, interaction patterns
- **Learning Outcomes**: Quiz scores, objective completion rates
- **System Performance**: API response times, agent utilization

### Available Endpoints

- Prometheus metrics: `http://127.0.0.1:8008/metrics`
- Health checks: `http://127.0.0.1:8008/health`
- Agent status: `http://127.0.0.1:8008/agents/status`

## 🔐 Security & Privacy

- **JWT Authentication**: Secure API access with role-based permissions
- **Input Validation**: Pydantic models prevent injection attacks
- **Rate Limiting**: 100 requests/minute per IP address
- **Data Encryption**: All sensitive data encrypted at rest
- **Privacy Compliant**: COPPA and FERPA compliant design
- **Audit Logging**: Comprehensive activity tracking

## 🌐 Deployment

### Docker Deployment

```bash
# Build and deploy
docker-compose up -d

# Scale services
docker-compose up -d --scale agents=3

# Monitor logs
docker-compose logs -f
```

### Production Configuration

```bash
# Set production environment
export ENVIRONMENT=production
export DEBUG=false
export LOG_LEVEL=INFO

# Configure SSL/TLS
export SSL_CERT_PATH=/path/to/cert.pem
export SSL_KEY_PATH=/path/to/key.pem
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## 📞 Support

- **Documentation**: [Comprehensive Guide](CLAUDE.md)
- **Issues**: [GitHub Issues](https://github.com/ToolBoxAI-Solutions/ToolboxAI-Roblox-Environment/issues)
- **Discussions**: [GitHub Discussions](https://github.com/ToolBoxAI-Solutions/ToolboxAI-Roblox-Environment/discussions)

## 🎯 Roadmap

### Version 0.9.0 (Current - 90% Complete)
- ✅ Multi-agent AI system
- ✅ SPARC framework integration
- ✅ Swarm intelligence coordination
- ✅ Complete server implementation
- 🚧 Roblox Studio plugin (final 10%)

### Version 1.0.0 (Coming Soon)
- 🔄 Complete Roblox integration
- 🔄 Advanced analytics dashboard
- 🔄 Mobile companion app
- 🔄 Multi-language support

---

<div align="center">
  <strong>Built with ❤️ by ToolBoxAI Solutions</strong><br/>
  <em>Revolutionizing education through AI-powered immersive learning experiences</em>
</div>