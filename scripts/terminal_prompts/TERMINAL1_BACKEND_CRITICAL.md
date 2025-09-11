# TERMINAL 1: BACKEND/DATABASE SPECIALIST - CRITICAL PATH
**Priority: CRITICAL | Status: 85% Complete | Target: 100% in 24 hours**

## YOUR MISSION
You are the Backend/Database Specialist responsible for the CRITICAL PATH of the project. The entire system depends on your services being operational. You must clean up duplicate processes, fix the FastAPI server, and ensure all database connections work with REAL DATA.

## CURRENT SYSTEM STATUS
```
✅ MCP Server: Running (PID 47275, port 9876)
✅ Flask Bridge: Running (PID 21538, port 5001)
❌ FastAPI: NOT RUNNING (port 8008 dead)
⚠️ Multiple duplicate processes consuming resources
⚠️ Database connections need verification
```

## PHASE 1: IMMEDIATE CLEANUP (First 30 minutes)

### Task 1.1: Kill Duplicate Processes
```bash
# Check all running Python/Node processes
ps aux | grep -E "(python|node|uvicorn)" | grep -v grep

# Kill unnecessary Node processes (keep only dashboard on 5179)
lsof -iTCP:5175 -sTCP:LISTEN | awk 'NR>1 {print $2}' | xargs kill -9
lsof -iTCP:5176 -sTCP:LISTEN | awk 'NR>1 {print $2}' | xargs kill -9
lsof -iTCP:5177 -sTCP:LISTEN | awk 'NR>1 {print $2}' | xargs kill -9
lsof -iTCP:5178 -sTCP:LISTEN | awk 'NR>1 {print $2}' | xargs kill -9

# Clean up any orphaned Python processes
pkill -f "uvicorn.*8008"
pkill -f "python.*server.main"

# Verify cleanup
lsof -iTCP -sTCP:LISTEN | grep -E "(5001|8008|9876|5179)"
```

### Task 1.2: Clear Python Cache and Temp Files
```bash
cd /Volumes/G-DRIVE\ ArmorATD/Development/Clients/ToolBoxAI-Solutions

# Clear Python cache
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
find . -type f -name "*.pyc" -delete
find . -type f -name "*.pyo" -delete

# Clear temp files
rm -rf /tmp/terminal_coordination.json
rm -rf logs/*.log
touch logs/fastapi.log logs/database.log logs/integration.log
```

## PHASE 2: FIX FASTAPI SERVER (Next 2 hours)

### Task 2.1: Fix Import Issues in server/main.py
```bash
cd /Volumes/G-DRIVE\ ArmorATD/Development/Clients/ToolBoxAI-Solutions/ToolboxAI-Roblox-Environment

# First, ensure virtual environment is activated
source venv_clean/bin/activate

# Verify all dependencies are installed
pip install -r requirements.txt --upgrade

# Fix the main.py imports
cat > server/main.py << 'EOF'
"""
FastAPI Main Application Server
FIXED VERSION with proper imports and real data integration
"""
import os
import sys
from pathlib import Path

# Critical: Add parent directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi import FastAPI, HTTPException, Depends, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import asyncio
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
import json

# Database imports - REAL DATA
from database.connection import get_db, DatabaseConnection
from database.repositories import (
    UserRepository,
    ContentRepository,
    LessonRepository,
    QuizRepository
)

# Authentication
from server.auth import get_current_user, User, create_access_token
from server.config import settings

# Agent system imports
try:
    from agents.supervisor import SupervisorAgent
    from agents.content_agent import ContentAgent
    from agents.quiz_agent import QuizAgent
    AGENTS_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Agent system not available: {e}")
    AGENTS_AVAILABLE = False

# MCP integration
try:
    from mcp.server import MCPServer
    from mcp.context_manager import ContextManager
    MCP_AVAILABLE = True
except ImportError as e:
    print(f"Warning: MCP system not available: {e}")
    MCP_AVAILABLE = False

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/fastapi.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Database connection manager
db_connection = DatabaseConnection()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle"""
    logger.info("Starting FastAPI server with REAL DATA integration...")
    
    # Initialize database connection pool
    await db_connection.connect()
    logger.info("✅ Database connection pool established")
    
    # Initialize agent system if available
    if AGENTS_AVAILABLE:
        app.state.supervisor = SupervisorAgent()
        logger.info("✅ Agent system initialized")
    
    # Initialize MCP if available
    if MCP_AVAILABLE:
        app.state.mcp_server = MCPServer()
        app.state.context_manager = ContextManager(max_tokens=128000)
        logger.info("✅ MCP system initialized")
    
    # Verify critical services
    try:
        # Test database connection
        async with db_connection.get_session() as session:
            result = await session.execute("SELECT COUNT(*) FROM users")
            user_count = result.scalar()
            logger.info(f"✅ Database operational - {user_count} users found")
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")
    
    yield
    
    # Cleanup
    logger.info("Shutting down FastAPI server...")
    await db_connection.disconnect()
    logger.info("✅ Cleanup complete")

# Create FastAPI app with lifespan
app = FastAPI(
    title="ToolBoxAI Educational Platform API",
    version="1.0.0",
    description="Production-ready API with real data integration",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5179", "http://127.0.0.1:5179"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        
    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections[client_id] = websocket
        logger.info(f"WebSocket connected: {client_id}")
        
    def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            del self.active_connections[client_id]
            logger.info(f"WebSocket disconnected: {client_id}")
            
    async def send_personal_message(self, message: str, client_id: str):
        if client_id in self.active_connections:
            await self.active_connections[client_id].send_text(message)
            
    async def broadcast(self, message: str):
        for connection in self.active_connections.values():
            await connection.send_text(message)

manager = ConnectionManager()

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check with real service status"""
    status = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "database": False,
            "agents": AGENTS_AVAILABLE,
            "mcp": MCP_AVAILABLE,
            "websocket": len(manager.active_connections) > 0
        },
        "metrics": {
            "active_connections": len(manager.active_connections)
        }
    }
    
    # Check database
    try:
        async with db_connection.get_session() as session:
            await session.execute("SELECT 1")
            status["services"]["database"] = True
    except:
        pass
    
    return status

# Authentication endpoint
@app.post("/auth/login")
async def login(username: str, password: str):
    """Login with real user authentication"""
    async with db_connection.get_session() as session:
        user_repo = UserRepository(session)
        user = await user_repo.authenticate(username, password)
        
        if not user:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        access_token = create_access_token(data={"sub": user.username, "role": user.role})
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "username": user.username,
                "role": user.role,
                "email": user.email
            }
        }

# Content generation endpoint with real data
@app.post("/generate_content")
async def generate_content(
    subject: str,
    grade_level: int,
    learning_objectives: List[str],
    environment_type: str,
    include_quiz: bool = True,
    current_user: User = Depends(get_current_user)
):
    """Generate educational content using real agent system"""
    
    if not AGENTS_AVAILABLE:
        return {
            "status": "error",
            "message": "Agent system not available",
            "fallback": True,
            "content": {
                "subject": subject,
                "grade_level": grade_level,
                "objectives": learning_objectives,
                "environment": environment_type,
                "generated_at": datetime.now().isoformat()
            }
        }
    
    try:
        supervisor = app.state.supervisor
        
        # Create content generation request
        request = {
            "type": "content_generation",
            "parameters": {
                "subject": subject,
                "grade_level": grade_level,
                "learning_objectives": learning_objectives,
                "environment_type": environment_type,
                "include_quiz": include_quiz,
                "user_id": current_user.id,
                "user_role": current_user.role
            }
        }
        
        # Process with supervisor agent
        result = await supervisor.process_request(request)
        
        # Store in database
        async with db_connection.get_session() as session:
            content_repo = ContentRepository(session)
            await content_repo.create_content(
                user_id=current_user.id,
                content_type="educational",
                content_data=result
            )
            await session.commit()
        
        return {
            "status": "success",
            "content": result,
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Content generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# WebSocket endpoint for real-time updates
@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    """WebSocket for real-time communication"""
    await manager.connect(websocket, client_id)
    
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Process message based on type
            if message["type"] == "ping":
                await manager.send_personal_message(
                    json.dumps({"type": "pong", "timestamp": datetime.now().isoformat()}),
                    client_id
                )
            elif message["type"] == "broadcast":
                await manager.broadcast(json.dumps({
                    "type": "broadcast",
                    "from": client_id,
                    "message": message.get("message", ""),
                    "timestamp": datetime.now().isoformat()
                }))
            
    except WebSocketDisconnect:
        manager.disconnect(client_id)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(client_id)

# Dashboard endpoints with real data
@app.get("/dashboard/stats")
async def dashboard_stats(current_user: User = Depends(get_current_user)):
    """Get real dashboard statistics"""
    async with db_connection.get_session() as session:
        stats = {
            "users": await session.execute("SELECT COUNT(*) FROM users"),
            "lessons": await session.execute("SELECT COUNT(*) FROM lessons"),
            "quizzes": await session.execute("SELECT COUNT(*) FROM quizzes"),
            "content": await session.execute("SELECT COUNT(*) FROM content")
        }
        
        return {
            "statistics": {
                "total_users": stats["users"].scalar(),
                "total_lessons": stats["lessons"].scalar(),
                "total_quizzes": stats["quizzes"].scalar(),
                "total_content": stats["content"].scalar()
            },
            "timestamp": datetime.now().isoformat()
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "server.main:app",
        host="127.0.0.1",
        port=8008,
        reload=True,
        log_level="info"
    )
EOF
```

### Task 2.2: Start FastAPI Server
```bash
# Start the server with proper error handling
cd ToolboxAI-Roblox-Environment
source venv_clean/bin/activate

# Start with uvicorn directly for better control
uvicorn server.main:app --host 127.0.0.1 --port 8008 --reload --log-level info &

# Save the PID
echo $! > ../scripts/pids/fastapi.pid

# Wait for server to start
sleep 5

# Verify it's running
curl -X GET "http://127.0.0.1:8008/health" | jq '.'

# If not running, check logs
tail -n 50 logs/fastapi.log
```

## PHASE 3: DATABASE VERIFICATION (Next 1 hour)

### Task 3.1: Verify All Database Connections
```bash
# Test PostgreSQL databases
cd /Volumes/G-DRIVE\ ArmorATD/Development/Clients/ToolBoxAI-Solutions

# Create database test script
cat > test_databases.py << 'EOF'
import asyncio
import asyncpg
from datetime import datetime

async def test_databases():
    """Test all database connections with real queries"""
    
    databases = {
        "ghost_backend": "postgresql://grayghostdata:securepass123@localhost/ghost_backend",
        "educational_platform": "postgresql://grayghostdata:securepass123@localhost/educational_platform",
        "roblox_data": "postgresql://grayghostdata:securepass123@localhost/roblox_data",
        "mcp_memory": "postgresql://grayghostdata:securepass123@localhost/mcp_memory"
    }
    
    results = {}
    
    for db_name, connection_string in databases.items():
        try:
            conn = await asyncpg.connect(connection_string)
            
            # Test basic connectivity
            version = await conn.fetchval('SELECT version()')
            
            # Get table count
            table_count = await conn.fetchval("""
                SELECT COUNT(*) 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
            """)
            
            # Get row counts for key tables
            row_counts = {}
            if db_name == "educational_platform":
                row_counts["users"] = await conn.fetchval("SELECT COUNT(*) FROM users")
                row_counts["lessons"] = await conn.fetchval("SELECT COUNT(*) FROM lessons")
                row_counts["classes"] = await conn.fetchval("SELECT COUNT(*) FROM classes")
            
            await conn.close()
            
            results[db_name] = {
                "status": "✅ Connected",
                "tables": table_count,
                "row_counts": row_counts,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            results[db_name] = {
                "status": f"❌ Failed",
                "error": str(e)
            }
    
    return results

# Run the test
results = asyncio.run(test_databases())
for db, info in results.items():
    print(f"\n{db}:")
    for key, value in info.items():
        print(f"  {key}: {value}")
EOF

python test_databases.py
```

### Task 3.2: Fix Any Database Issues
```bash
# If databases are not accessible, restart PostgreSQL
brew services restart postgresql@14

# Check PostgreSQL is running
pg_ctl status -D /usr/local/var/postgresql@14

# If needed, create missing databases
psql -U grayghostdata << EOF
CREATE DATABASE IF NOT EXISTS ghost_backend;
CREATE DATABASE IF NOT EXISTS educational_platform;
CREATE DATABASE IF NOT EXISTS roblox_data;
CREATE DATABASE IF NOT EXISTS mcp_memory;
EOF

# Run migrations if needed
cd ToolboxAI-Roblox-Environment
alembic upgrade head
```

## PHASE 4: INTEGRATION VERIFICATION (Next 30 minutes)

### Task 4.1: Test Service Communication
```bash
# Test FastAPI -> Database
curl -X POST "http://127.0.0.1:8008/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username": "john_teacher", "password": "Teacher123!"}'

# Test FastAPI -> Flask Bridge communication
curl -X GET "http://127.0.0.1:5001/health"

# Test WebSocket connection
cat > test_websocket.py << 'EOF'
import asyncio
import websockets
import json

async def test_websocket():
    uri = "ws://127.0.0.1:8008/ws/test_client"
    async with websockets.connect(uri) as websocket:
        # Send ping
        await websocket.send(json.dumps({"type": "ping"}))
        response = await websocket.recv()
        print(f"Received: {response}")
        
        # Send broadcast
        await websocket.send(json.dumps({
            "type": "broadcast",
            "message": "Test message from Terminal 1"
        }))
        response = await websocket.recv()
        print(f"Broadcast response: {response}")

asyncio.run(test_websocket())
EOF

python test_websocket.py
```

### Task 4.2: Create Service Monitor
```bash
# Create monitoring script
cat > monitor_services.sh << 'EOF'
#!/bin/bash

echo "=== Service Status Monitor ==="
echo "Time: $(date)"
echo ""

# Check FastAPI
if curl -s http://127.0.0.1:8008/health > /dev/null; then
    echo "✅ FastAPI: Running on port 8008"
else
    echo "❌ FastAPI: Not responding on port 8008"
fi

# Check Flask Bridge
if curl -s http://127.0.0.1:5001/health > /dev/null; then
    echo "✅ Flask Bridge: Running on port 5001"
else
    echo "❌ Flask Bridge: Not responding on port 5001"
fi

# Check MCP
if lsof -iTCP:9876 -sTCP:LISTEN > /dev/null; then
    echo "✅ MCP Server: Running on port 9876"
else
    echo "❌ MCP Server: Not running on port 9876"
fi

# Check Dashboard
if curl -s http://127.0.0.1:5179 > /dev/null; then
    echo "✅ Dashboard: Running on port 5179"
else
    echo "❌ Dashboard: Not responding on port 5179"
fi

# Check Database
if pg_isready -h localhost -p 5432 > /dev/null; then
    echo "✅ PostgreSQL: Accepting connections"
else
    echo "❌ PostgreSQL: Not accepting connections"
fi

echo ""
echo "=== Resource Usage ==="
echo "Memory: $(ps aux | grep -E "(python|node)" | awk '{sum+=$4} END {print sum "%"}')"
echo "CPU: $(ps aux | grep -E "(python|node)" | awk '{sum+=$3} END {print sum "%"}')"
EOF

chmod +x monitor_services.sh
./monitor_services.sh
```

## PHASE 5: PERFORMANCE OPTIMIZATION (Final 30 minutes)

### Task 5.1: Optimize Database Queries
```bash
# Add database indexes for performance
psql -U grayghostdata -d educational_platform << EOF
-- Add indexes for frequently queried columns
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_lessons_subject ON lessons(subject);
CREATE INDEX IF NOT EXISTS idx_content_user_id ON content(user_id);
CREATE INDEX IF NOT EXISTS idx_content_created_at ON content(created_at DESC);

-- Analyze tables for query optimization
ANALYZE users;
ANALYZE lessons;
ANALYZE content;
ANALYZE quizzes;
EOF
```

### Task 5.2: Configure Connection Pooling
```bash
# Update database connection configuration
cat > ToolboxAI-Roblox-Environment/database/connection.py << 'EOF'
"""
Optimized Database Connection with Connection Pooling
"""
import asyncpg
from asyncpg.pool import Pool
from typing import Optional
import logging

logger = logging.getLogger(__name__)

class DatabaseConnection:
    """Manages database connection pool for optimal performance"""
    
    def __init__(self):
        self.pool: Optional[Pool] = None
        self.config = {
            "host": "localhost",
            "port": 5432,
            "user": "grayghostdata",
            "password": "securepass123",
            "database": "educational_platform",
            "min_size": 10,  # Minimum connections in pool
            "max_size": 20,  # Maximum connections in pool
            "max_queries": 50000,  # Max queries per connection before recycling
            "max_inactive_connection_lifetime": 300.0,  # 5 minutes
            "command_timeout": 60.0
        }
    
    async def connect(self):
        """Create connection pool"""
        if not self.pool:
            self.pool = await asyncpg.create_pool(**self.config)
            logger.info(f"Database pool created with {self.config['min_size']}-{self.config['max_size']} connections")
    
    async def disconnect(self):
        """Close connection pool"""
        if self.pool:
            await self.pool.close()
            logger.info("Database pool closed")
    
    async def get_session(self):
        """Get a connection from the pool"""
        if not self.pool:
            await self.connect()
        return self.pool.acquire()
    
    async def execute_query(self, query: str, *args):
        """Execute a query with automatic connection management"""
        async with self.pool.acquire() as conn:
            return await conn.fetch(query, *args)
    
    async def execute_many(self, query: str, args_list):
        """Execute many queries efficiently"""
        async with self.pool.acquire() as conn:
            return await conn.executemany(query, args_list)
EOF
```

## SUCCESS CRITERIA CHECKLIST

Before marking Terminal 1 complete, verify:

- [ ] All duplicate processes killed
- [ ] FastAPI running on port 8008
- [ ] Health endpoint returns 200 OK
- [ ] All 4 databases accessible
- [ ] WebSocket connections working
- [ ] Authentication endpoint functional
- [ ] Connection pooling configured
- [ ] Database indexes created
- [ ] Monitor script shows all services green
- [ ] Logs show no critical errors

## HANDOFF TO OTHER TERMINALS

Once complete, notify other terminals:

1. **Terminal 2**: FastAPI is ready at http://127.0.0.1:8008
2. **Terminal 3**: API endpoints available for Roblox integration
3. **Terminal 4**: Services ready for security testing
4. **Terminal 5**: API documentation can be generated
5. **Terminal 6**: System ready for cleanup phase
6. **Terminal 7**: Services stable for CI/CD setup
7. **Terminal 8**: Backend ready for containerization

## TROUBLESHOOTING GUIDE

### If FastAPI won't start:
```bash
# Check for port conflicts
lsof -iTCP:8008
# Kill any process using the port
kill -9 <PID>

# Check Python path issues
python -c "import sys; print(sys.path)"

# Reinstall dependencies
pip install --force-reinstall -r requirements.txt
```

### If database connections fail:
```bash
# Check PostgreSQL status
pg_ctl status
brew services restart postgresql@14

# Verify user exists
psql -U postgres -c "\du"

# Reset password if needed
psql -U postgres -c "ALTER USER grayghostdata PASSWORD 'securepass123';"
```

### If WebSocket fails:
```bash
# Check if WebSocket upgrade is being blocked
curl -i -N -H "Connection: Upgrade" -H "Upgrade: websocket" \
  -H "Sec-WebSocket-Version: 13" -H "Sec-WebSocket-Key: SGVsbG8sIHdvcmxkIQ==" \
  http://127.0.0.1:8008/ws/test
```

## MONITORING COMMANDS

Keep these running in separate terminal tabs:

```bash
# Tab 1: Watch logs
tail -f ToolboxAI-Roblox-Environment/logs/fastapi.log

# Tab 2: Monitor connections
watch -n 2 'netstat -an | grep -E "(8008|5001|9876|5432)"'

# Tab 3: Monitor resources
watch -n 2 './monitor_services.sh'
```

Remember: YOU ARE CRITICAL PATH. Other terminals depend on your success. Be thorough, test everything, and communicate status frequently.