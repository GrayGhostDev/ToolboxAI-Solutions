#!/usr/bin/env python3
"""Simple Agent Coordinator runner for development."""

import asyncio
import logging
import sys
import os
from typing import Dict, List, Any
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from fastapi import FastAPI, WebSocket
from fastapi.responses import JSONResponse
import uvicorn

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Agent Coordinator", version="1.0.0")

# Agent registry
agents: Dict[str, Dict[str, Any]] = {}
active_tasks: List[Dict[str, Any]] = []

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return JSONResponse({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "agents_registered": len(agents),
        "active_tasks": len(active_tasks)
    })

@app.post("/agents/register")
async def register_agent(agent_data: dict):
    """Register a new agent."""
    agent_id = agent_data.get("agent_id")
    if not agent_id:
        return JSONResponse({"error": "agent_id required"}, status_code=400)

    agents[agent_id] = {
        **agent_data,
        "registered_at": datetime.now().isoformat(),
        "status": "active"
    }
    logger.info(f"Agent registered: {agent_id}")
    return JSONResponse({"status": "registered", "agent_id": agent_id})

@app.post("/agents/{agent_id}/task")
async def assign_task(agent_id: str, task_data: dict):
    """Assign a task to an agent."""
    if agent_id not in agents:
        return JSONResponse({"error": "Agent not found"}, status_code=404)

    task = {
        "task_id": f"task_{len(active_tasks) + 1}",
        "agent_id": agent_id,
        "data": task_data,
        "created_at": datetime.now().isoformat(),
        "status": "assigned"
    }
    active_tasks.append(task)
    logger.info(f"Task assigned to agent {agent_id}: {task['task_id']}")
    return JSONResponse(task)

@app.get("/agents")
async def list_agents():
    """List all registered agents."""
    return JSONResponse({"agents": list(agents.values())})

@app.get("/tasks")
async def list_tasks():
    """List all active tasks."""
    return JSONResponse({"tasks": active_tasks})

@app.websocket("/ws/agent/{agent_id}")
async def agent_websocket(websocket: WebSocket, agent_id: str):
    """WebSocket endpoint for agent communication."""
    await websocket.accept()
    logger.info(f"WebSocket connected: {agent_id}")

    try:
        while True:
            data = await websocket.receive_json()
            logger.info(f"Received from {agent_id}: {data}")

            # Echo back for now
            await websocket.send_json({
                "type": "ack",
                "agent_id": agent_id,
                "timestamp": datetime.now().isoformat()
            })
    except Exception as e:
        logger.error(f"WebSocket error for {agent_id}: {e}")
    finally:
        logger.info(f"WebSocket disconnected: {agent_id}")

if __name__ == "__main__":
    port = int(os.getenv("COORDINATOR_PORT", "8888"))
    logger.info(f"Starting Agent Coordinator on port {port}...")
    uvicorn.run(app, host="0.0.0.0", port=port)