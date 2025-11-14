"""
Educational Agent Pool
Manages a pool of educational content generation agents
"""

import asyncio
import json
import logging
import os
import signal
import sys
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional

import redis.asyncio as redis
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# WebSocket replaced with Pusher for real-time communication
# from apps.backend.services.pusher import trigger_event as pusher_trigger

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

from core.agents.base_agent import AgentConfig, BaseAgent
from core.agents.educational.adaptive_learning_agent import AdaptiveLearningAgent
from core.agents.educational.assessment_design_agent import AssessmentDesignAgent
from core.agents.educational.curriculum_alignment_agent import CurriculumAlignmentAgent

logger = logging.getLogger(__name__)

# Configuration from environment
AGENT_POOL_SIZE = int(os.getenv("AGENT_POOL_SIZE", "3"))
MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", "ws://mcp-server:9876")
COORDINATOR_URL = os.getenv("COORDINATOR_URL", "http://agent-coordinator:8888")
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379")
REGISTRATION_INTERVAL = int(os.getenv("REGISTRATION_INTERVAL", "60"))
AGENT_PORT = int(os.getenv("AGENT_PORT", "8080"))


class TaskRequest(BaseModel):
    task_id: str
    task_type: str
    payload: dict[str, Any]
    priority: str = "normal"
    timeout: int = 300


class AgentStatus(BaseModel):
    agent_id: str
    agent_type: str
    status: str
    current_task: Optional[str] = None
    tasks_completed: int = 0
    uptime: str
    last_heartbeat: str


@dataclass
class AgentInfo:
    agent_id: str
    agent_type: str
    capabilities: list[str]
    status: str
    created_at: datetime
    last_seen: datetime
    tasks_completed: int = 0


class EducationalAgentPool:
    """Pool manager for educational agents"""

    def __init__(self):
        self.pool_id = f"educational-pool-{os.getpid()}"
        self.agents: dict[str, BaseAgent] = {}
        self.agent_info: dict[str, AgentInfo] = {}
        self.redis_client: Optional[redis.Redis] = None
        self.mcp_connection: Optional[Any] = None
        self.running = False
        self.start_time = datetime.now()

        # Initialize FastAPI app
        self.app = FastAPI(
            title="Educational Agent Pool",
            description="Pool of educational content generation agents",
            version="1.0.0",
        )

        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        self.setup_routes()

    def setup_routes(self):
        """Setup FastAPI routes"""

        @self.app.get("/health")
        async def health():
            return {
                "status": "healthy",
                "pool_id": self.pool_id,
                "agents": len(self.agents),
                "uptime": str(datetime.now() - self.start_time),
            }

        @self.app.get("/status")
        async def status():
            agent_statuses = []
            for agent_id, agent in self.agents.items():
                info = self.agent_info.get(agent_id)
                if info:
                    agent_statuses.append(
                        AgentStatus(
                            agent_id=agent_id,
                            agent_type=info.agent_type,
                            status=info.status,
                            current_task=agent.current_task,
                            tasks_completed=info.tasks_completed,
                            uptime=str(datetime.now() - info.created_at),
                            last_heartbeat=info.last_seen.isoformat(),
                        )
                    )

            return {
                "pool_id": self.pool_id,
                "pool_status": "running" if self.running else "stopped",
                "total_agents": len(self.agents),
                "agents": agent_statuses,
            }

        @self.app.post("/execute")
        async def execute_task(request: TaskRequest):
            try:
                # Find available agent
                available_agent = await self._find_available_agent(request.task_type)
                if not available_agent:
                    raise HTTPException(status_code=503, detail="No available agents")

                # Execute task
                result = await available_agent.execute(
                    task=f"{request.task_type}: {request.payload}",
                    context=request.payload,
                )

                # Update agent info
                if available_agent.name in self.agent_info:
                    self.agent_info[available_agent.name].tasks_completed += 1
                    self.agent_info[available_agent.name].last_seen = datetime.now()

                return {
                    "task_id": request.task_id,
                    "success": result.success,
                    "output": result.output,
                    "metadata": result.metadata,
                    "execution_time": result.execution_time,
                    "agent_id": available_agent.name,
                }

            except Exception as e:
                logger.error(f"Task execution failed: {e}")
                raise HTTPException(status_code=500, detail=str(e))

    async def initialize(self):
        """Initialize the agent pool"""
        logger.info(f"Initializing Educational Agent Pool {self.pool_id}")

        # Connect to Redis
        try:
            self.redis_client = redis.from_url(REDIS_URL)
            await self.redis_client.ping()
            logger.info("Connected to Redis")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise

        # Create agent instances
        await self._create_agents()

        # Register with MCP server
        await self._register_with_mcp()

        # Start background tasks
        self.running = True
        asyncio.create_task(self._heartbeat_loop())
        asyncio.create_task(self._agent_health_monitor())

        logger.info(f"Educational Agent Pool initialized with {len(self.agents)} agents")

    async def _create_agents(self):
        """Create agent instances"""
        agent_types = [
            ("content-agent", CurriculumAlignmentAgent),
            ("adaptive-agent", AdaptiveLearningAgent),
            ("assessment-agent", AssessmentDesignAgent),
        ]

        for i in range(AGENT_POOL_SIZE):
            for agent_type, agent_class in agent_types:
                agent_id = f"{agent_type}-{i}"

                config = AgentConfig(
                    name=agent_id,
                    model="gpt-4-turbo-preview",
                    temperature=0.7,
                    max_retries=3,
                    timeout=300,
                    verbose=False,
                    memory_enabled=True,
                )

                try:
                    agent = agent_class(config)
                    self.agents[agent_id] = agent

                    self.agent_info[agent_id] = AgentInfo(
                        agent_id=agent_id,
                        agent_type=agent_type,
                        capabilities=self._get_agent_capabilities(agent_type),
                        status="idle",
                        created_at=datetime.now(),
                        last_seen=datetime.now(),
                    )

                    logger.info(f"Created agent: {agent_id}")

                except Exception as e:
                    logger.error(f"Failed to create agent {agent_id}: {e}")

    def _get_agent_capabilities(self, agent_type: str) -> list[str]:
        """Get capabilities for agent type"""
        capabilities_map = {
            "content-agent": ["content-generation", "curriculum-alignment"],
            "adaptive-agent": ["adaptive-learning", "personalization"],
            "assessment-agent": ["assessment-design", "quiz-creation"],
        }
        return capabilities_map.get(agent_type, [])

    async def _register_with_mcp(self):
        """Register agent pool with MCP server"""
        try:
            registration_data = {
                "pool_id": self.pool_id,
                "agent_type": "educational",
                "capabilities": [
                    "content-generation",
                    "assessment-design",
                    "adaptive-learning",
                ],
                "agents": [
                    {
                        "agent_id": info.agent_id,
                        "agent_type": info.agent_type,
                        "capabilities": info.capabilities,
                        "status": info.status,
                    }
                    for info in self.agent_info.values()
                ],
                "endpoint": f"http://educational-agents:{AGENT_PORT}",
                "health_endpoint": f"http://educational-agents:{AGENT_PORT}/health",
            }

            # Store in Redis for MCP discovery
            await self.redis_client.hset(
                "mcp:agent_pools",
                self.pool_id,
                json.dumps(registration_data, default=str),
            )

            # Set TTL for auto-cleanup
            await self.redis_client.expire(f"mcp:agent_pools:{self.pool_id}", 300)

            logger.info("Registered with MCP server")

        except Exception as e:
            logger.error(f"Failed to register with MCP: {e}")

    async def _find_available_agent(self, task_type: str) -> Optional[BaseAgent]:
        """Find an available agent for the task type"""
        # Simple round-robin selection for now
        for agent_id, agent in self.agents.items():
            info = self.agent_info.get(agent_id)
            if info and info.status == "idle" and agent.status.value == "idle":
                # Check if agent supports the task type
                if self._agent_supports_task(info.agent_type, task_type):
                    info.status = "busy"
                    return agent

        return None

    def _agent_supports_task(self, agent_type: str, task_type: str) -> bool:
        """Check if agent type supports the task"""
        support_map = {
            "content-agent": ["content-generation", "curriculum-alignment"],
            "adaptive-agent": ["adaptive-learning", "personalization"],
            "assessment-agent": ["assessment-design", "quiz-creation"],
        }

        supported_tasks = support_map.get(agent_type, [])
        return any(task in task_type.lower() for task in supported_tasks)

    async def _heartbeat_loop(self):
        """Send periodic heartbeats to MCP server"""
        while self.running:
            try:
                await self._register_with_mcp()
                await asyncio.sleep(REGISTRATION_INTERVAL)
            except Exception as e:
                logger.error(f"Heartbeat failed: {e}")
                await asyncio.sleep(5)

    async def _agent_health_monitor(self):
        """Monitor agent health and restart failed agents"""
        while self.running:
            try:
                for agent_id, agent in list(self.agents.items()):
                    info = self.agent_info.get(agent_id)
                    if info:
                        # Update agent status based on actual agent state
                        if agent.status.value == "idle" and info.status == "busy":
                            info.status = "idle"
                        elif agent.status.value == "error":
                            logger.warning(f"Agent {agent_id} in error state, resetting")
                            agent.reset()
                            info.status = "idle"

                        info.last_seen = datetime.now()

                await asyncio.sleep(30)  # Check every 30 seconds

            except Exception as e:
                logger.error(f"Health monitor error: {e}")
                await asyncio.sleep(5)

    async def shutdown(self):
        """Shutdown the agent pool"""
        logger.info("Shutting down Educational Agent Pool")
        self.running = False

        # Cleanup Redis registration
        if self.redis_client:
            try:
                await self.redis_client.hdel("mcp:agent_pools", self.pool_id)
                await self.redis_client.close()
            except Exception as e:
                logger.error(f"Redis cleanup error: {e}")

        # Reset all agents
        for agent in self.agents.values():
            try:
                agent.reset()
            except Exception as e:
                logger.error(f"Agent cleanup error: {e}")


# Global pool instance
pool = EducationalAgentPool()


def signal_handler(signum, frame):
    """Handle shutdown signals"""
    logger.info(f"Received signal {signum}")
    asyncio.create_task(pool.shutdown())


async def main():
    """Main entry point"""
    # Setup signal handlers
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    try:
        # Initialize pool
        await pool.initialize()

        # Start web server
        config = uvicorn.Config(app=pool.app, host="0.0.0.0", port=AGENT_PORT, log_level="info")
        server = uvicorn.Server(config)
        await server.serve()

    except Exception as e:
        logger.error(f"Agent pool startup failed: {e}")
        sys.exit(1)
    finally:
        await pool.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
