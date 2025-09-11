# ToolboxAI Roblox Environment - Server Implementation

This directory contains the complete server implementation for the ToolboxAI Roblox Educational Platform, providing AI-powered content generation, multi-agent orchestration, and seamless integration with Roblox Studio.

## 🏗️ Architecture Overview

The server implementation consists of two main components:

### FastAPI Main Server (Port 8008)

- **Purpose**: Primary API server with advanced AI capabilities
- **Features**:
  - Educational content generation using LangChain agents
  - WebSocket support for real-time updates
  - Authentication and authorization
  - LMS integration (Schoology, Canvas)
  - Comprehensive monitoring and metrics

### Flask Bridge Server (Port 5001)

- **Purpose**: Lightweight bridge for Roblox Studio plugin communication
- **Features**:
  - Simple HTTP endpoints optimized for Roblox
  - Plugin registration and session management
  - Content caching for faster responses
  - Direct integration with FastAPI backend

## 📁 File Structure

```
server/
├── __init__.py              # Package initialization
├── main.py                  # FastAPI application (port 8008)
├── roblox_server.py         # Flask bridge server (port 5001)
├── config.py                # Configuration management
├── models.py                # Pydantic data models
├── auth.py                  # Authentication & authorization
├── tools.py                 # LangChain tools implementation
├── agent.py                 # Agent management system
├── websocket.py             # WebSocket connection management
├── start_servers.py         # Server startup script
└── README.md               # This documentation
```

## 🚀 Quick Start

### Prerequisites

1. **Python 3.11+** installed
2. **Required API Keys**:

   ```bash
   export OPENAI_API_KEY="your-openai-key"
   export LANGCHAIN_API_KEY="your-langchain-key"  # Optional
   export SCHOOLOGY_KEY="your-schoology-key"      # Optional
   export SCHOOLOGY_SECRET="your-schoology-secret" # Optional
   export CANVAS_TOKEN="your-canvas-token"        # Optional
   ```

3. **Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

### Starting the Servers

#### Option 1: Use the startup script (Recommended)

```bash
python server/start_servers.py
```

#### Option 2: Start servers manually

```bash
# Terminal 1 - Flask Bridge Server
python server/roblox_server.py

# Terminal 2 - FastAPI Main Server
python server/main.py
```

### Verification

Once started, verify the servers are running:

- **FastAPI Server**: http://127.0.0.1:8008/health
- **Flask Bridge Server**: http://127.0.0.1:5001/health
- **API Documentation**: http://127.0.0.1:8008/docs

## 🔧 Configuration

### Environment Variables

Create a `.env` file in the project root:

```env
# Core Configuration
DEBUG=true
ENVIRONMENT=development

# Server Configuration
FASTAPI_HOST=127.0.0.1
FASTAPI_PORT=8008
FLASK_HOST=127.0.0.1
FLASK_PORT=5001

# AI Configuration
OPENAI_API_KEY=your-openai-key
OPENAI_MODEL=gpt-4
OPENAI_TEMPERATURE=0.7

# Database & Cache
REDIS_URL=redis://localhost:6379

# Authentication
JWT_SECRET_KEY=your-secret-key-change-in-production

# LMS Integration (Optional)
SCHOOLOGY_KEY=your-schoology-key
SCHOOLOGY_SECRET=your-schoology-secret
CANVAS_TOKEN=your-canvas-token

# Rate Limiting
RATE_LIMIT_PER_MINUTE=100
```

### Key Configuration Options

| Setting                      | Default | Description                      |
| ---------------------------- | ------- | -------------------------------- |
| `FASTAPI_PORT`               | 8008    | Main API server port             |
| `FLASK_PORT`                 | 5001    | Roblox bridge server port        |
| `OPENAI_MODEL`               | gpt-4   | AI model for content generation  |
| `MAX_CONCURRENT_GENERATIONS` | 10      | Max parallel content generations |
| `RATE_LIMIT_PER_MINUTE`      | 100     | API rate limit per minute        |

## 📊 API Endpoints

### Core Endpoints

#### Health & Status

- `GET /health` - System health check
- `GET /metrics` - System metrics
- `GET /info` - Application information

#### Authentication

- `POST /auth/token` - Create JWT access token

#### Content Generation

- `POST /generate_content` - Generate educational content
- `POST /generate_quiz` - Generate interactive quiz
- `POST /generate_terrain` - Generate Roblox terrain

#### LMS Integration

- `GET /lms/courses` - List LMS courses
- `GET /lms/course/{course_id}` - Get course details

#### Plugin Management

- `POST /plugin/register` - Register Roblox plugin
- `POST /plugin/message` - Send message to plugin

#### WebSocket

- `WS /ws` - Real-time WebSocket connection
- `WS /ws/{client_id}` - WebSocket with client ID

### Bridge Server Endpoints (Port 5001)

#### Plugin Management

- `POST /register_plugin` - Register plugin instance
- `POST /plugin/{id}/heartbeat` - Update plugin heartbeat
- `GET /plugin/{id}` - Get plugin information
- `GET /plugins` - List active plugins

#### Simplified Content Generation

- `POST /generate_simple_content` - Simple content generation
- `POST /generate_terrain` - Terrain generation
- `POST /generate_quiz` - Quiz generation

#### Utilities

- `GET /status` - Bridge server status
- `POST /cache/clear` - Clear content cache

## 🤖 Agent System Integration

The server integrates with the multi-agent system in `/agents/`:

### Agent Types

- **Content Agent**: Generates educational content
- **Quiz Agent**: Creates interactive assessments
- **Terrain Agent**: Builds Roblox environments
- **Script Agent**: Generates Lua scripts
- **Review Agent**: Reviews and optimizes code

### Agent Coordination

- **Supervisor Agent**: Routes tasks intelligently
- **SPARC Framework**: State-Policy-Action-Reward-Context
- **Swarm Intelligence**: Parallel task execution
- **Main Coordinator**: Final result orchestration

## 🔗 Integration Points

### Roblox Studio Plugin

The server is designed to work with the Roblox Studio plugin at `/Roblox/Plugins/`:

```lua
-- Plugin connects to Flask bridge server
local BRIDGE_URL = "http://localhost:5001"

-- Register plugin
HttpService:RequestAsync({
    Url = BRIDGE_URL .. "/register_plugin",
    Method = "POST",
    Body = HttpService:JSONEncode({
        studio_id = plugin:GetStudioUserId(),
        port = 64989
    })
})
```

### Dashboard Integration

The server provides APIs for the React dashboard at `/API/Dashboard/`:

```typescript
// Dashboard connects to FastAPI server
const API_BASE = 'http://localhost:8008'

const generateContent = async (request: ContentRequest) => {
  const response = await fetch(`${API_BASE}/generate_content`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request),
  })
  return response.json()
}
```

### Ghost Backend Integration

Coordinates with the Ghost CMS backend at `/API/GhostBackend/`:

- User authentication flow
- Content persistence
- Progress tracking
- Analytics data

## 🔒 Security Features

### Authentication & Authorization

- JWT-based authentication
- Role-based access control (student, teacher, admin)
- API key validation for services
- Session management with Redis

### Rate Limiting

- Configurable per-endpoint rate limits
- IP-based and user-based limiting
- Burst protection
- Graceful degradation

### Input Validation

- Pydantic model validation
- SQL injection prevention
- XSS protection via CORS policies
- File upload restrictions

## 📈 Monitoring & Observability

### Health Checks

- Component-level health checks
- Dependency validation
- Performance metrics
- Error tracking

### Logging

- Structured logging with timestamps
- Request/response logging
- Error tracking with stack traces
- Performance monitoring

### Metrics

- Connection counts
- Response times
- Error rates
- Resource utilization

## 🚨 Troubleshooting

### Common Issues

#### Servers Won't Start

```bash
# Check if ports are in use
lsof -i :8008
lsof -i :5001

# Check Python environment
python --version
pip list | grep fastapi
```

#### API Keys Not Working

```bash
# Verify environment variables
echo $OPENAI_API_KEY
env | grep API_KEY

# Check API key validity
curl -H "Authorization: Bearer $OPENAI_API_KEY" \
     https://api.openai.com/v1/models
```

#### Redis Connection Issues

```bash
# Check Redis status
redis-cli ping

# Use alternative Redis URL
export REDIS_URL=redis://localhost:6379/0
```

#### Agent System Errors

```bash
# Enable debug logging
export DEBUG=true
export LOG_LEVEL=DEBUG

# Check agent dependencies
python -c "import langchain; print('LangChain OK')"
python -c "from agents import supervisor; print('Agents OK')"
```

### Error Codes

| Code | Description              | Solution                    |
| ---- | ------------------------ | --------------------------- |
| 401  | Authentication failed    | Check JWT token             |
| 403  | Insufficient permissions | Verify user role            |
| 429  | Rate limit exceeded      | Reduce request frequency    |
| 500  | Internal server error    | Check logs and dependencies |

## 🔄 Development Workflow

### Making Changes

1. Modify the appropriate module
2. Test changes with `python -m pytest tests/`
3. Restart servers to apply changes
4. Verify functionality with API tests

### Adding New Endpoints

1. Define Pydantic models in `models.py`
2. Implement endpoint in `main.py` or `roblox_server.py`
3. Add authentication/authorization if needed
4. Update documentation

### Adding New Agent Types

1. Create agent class in `/agents/`
2. Register in `agent.py`
3. Add routing logic in supervisor
4. Test integration

## 🌐 Deployment

### Development Deployment

```bash
# Use the startup script
python server/start_servers.py
```

### Production Deployment

```bash
# Use process managers
gunicorn server.main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker
gunicorn server.roblox_server:app --workers 2

# Or use Docker
docker-compose up -d
```

### Environment-Specific Settings

- **Development**: Debug enabled, verbose logging
- **Staging**: Rate limiting, basic auth
- **Production**: SSL, reverse proxy, monitoring

## 📚 Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [LangChain Documentation](https://docs.langchain.com/)
- [Roblox Developer Hub](https://developer.roblox.com/)
- [Project Wiki](../Docs/)

## 🤝 Contributing

1. Follow the existing code patterns
2. Add proper type hints and docstrings
3. Write tests for new functionality
4. Update documentation
5. Follow security best practices

---

**ToolboxAI Roblox Environment Server**
_AI-Powered Educational Content Generation Platform_
