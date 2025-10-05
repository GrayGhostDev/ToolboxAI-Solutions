"""
MCP Server for Agent Coordination
Orchestrates multiple AI agents and manages task distribution
"""

import sys
import json
import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum

# Add parent directory to path for imports
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../..'))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TaskStatus(Enum):
    """Task status enumeration"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class AgentStatus(Enum):
    """Agent status enumeration"""
    IDLE = "idle"
    BUSY = "busy"
    OFFLINE = "offline"
    ERROR = "error"


class AgentCoordinatorMCPServer:
    """MCP Server for Agent Coordination"""

    def __init__(self):
        self.methods = {
            "register_agent": self.handle_register_agent,
            "unregister_agent": self.handle_unregister_agent,
            "list_agents": self.handle_list_agents,
            "get_agent_status": self.handle_get_agent_status,
            "submit_task": self.handle_submit_task,
            "get_task_status": self.handle_get_task_status,
            "cancel_task": self.handle_cancel_task,
            "list_tasks": self.handle_list_tasks,
            "orchestrate_workflow": self.handle_orchestrate_workflow,
            "get_workflow_status": self.handle_get_workflow_status,
            "health": self.handle_health,
            "capabilities": self.handle_capabilities,
        }

        # Agent registry
        self.agents = {}

        # Task queue
        self.tasks = {}
        self.task_counter = 0

        # Workflow management
        self.workflows = {}
        self.workflow_counter = 0

    async def handle_register_agent(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Register a new agent"""
        try:
            agent_id = params.get("agent_id")
            agent_type = params.get("agent_type")
            capabilities = params.get("capabilities", [])
            endpoint = params.get("endpoint")

            if not agent_id:
                return {
                    "status": "error",
                    "error": "agent_id is required"
                }

            self.agents[agent_id] = {
                "id": agent_id,
                "type": agent_type,
                "capabilities": capabilities,
                "endpoint": endpoint,
                "status": AgentStatus.IDLE.value,
                "registered_at": datetime.now().isoformat(),
                "tasks_completed": 0,
                "tasks_failed": 0
            }

            logger.info(f"Agent registered: {agent_id} ({agent_type})")

            return {
                "status": "success",
                "agent_id": agent_id,
                "message": f"Agent {agent_id} registered successfully"
            }
        except Exception as e:
            logger.error(f"Error registering agent: {e}")
            return {
                "status": "error",
                "error": str(e)
            }

    async def handle_unregister_agent(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Unregister an agent"""
        try:
            agent_id = params.get("agent_id")

            if agent_id in self.agents:
                del self.agents[agent_id]
                logger.info(f"Agent unregistered: {agent_id}")
                return {
                    "status": "success",
                    "message": f"Agent {agent_id} unregistered"
                }
            else:
                return {
                    "status": "error",
                    "error": f"Agent {agent_id} not found"
                }
        except Exception as e:
            logger.error(f"Error unregistering agent: {e}")
            return {
                "status": "error",
                "error": str(e)
            }

    async def handle_list_agents(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """List all registered agents"""
        try:
            filter_type = params.get("type")
            filter_status = params.get("status")

            agents_list = list(self.agents.values())

            # Apply filters
            if filter_type:
                agents_list = [a for a in agents_list if a["type"] == filter_type]
            if filter_status:
                agents_list = [a for a in agents_list if a["status"] == filter_status]

            return {
                "status": "success",
                "agents": agents_list,
                "total": len(agents_list)
            }
        except Exception as e:
            logger.error(f"Error listing agents: {e}")
            return {
                "status": "error",
                "error": str(e)
            }

    async def handle_get_agent_status(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get status of a specific agent"""
        try:
            agent_id = params.get("agent_id")

            if agent_id in self.agents:
                return {
                    "status": "success",
                    "agent": self.agents[agent_id]
                }
            else:
                return {
                    "status": "error",
                    "error": f"Agent {agent_id} not found"
                }
        except Exception as e:
            logger.error(f"Error getting agent status: {e}")
            return {
                "status": "error",
                "error": str(e)
            }

    async def handle_submit_task(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Submit a new task for execution"""
        try:
            task_type = params.get("task_type")
            task_data = params.get("task_data", {})
            priority = params.get("priority", "normal")
            assigned_agent = params.get("assigned_agent")

            # Generate task ID
            self.task_counter += 1
            task_id = f"task_{self.task_counter:06d}"

            # Find suitable agent if not specified
            if not assigned_agent:
                assigned_agent = self._find_suitable_agent(task_type)

            # Create task
            self.tasks[task_id] = {
                "id": task_id,
                "type": task_type,
                "data": task_data,
                "priority": priority,
                "status": TaskStatus.PENDING.value,
                "assigned_agent": assigned_agent,
                "created_at": datetime.now().isoformat(),
                "started_at": None,
                "completed_at": None,
                "result": None,
                "error": None
            }

            # Simulate task execution (in real implementation, would dispatch to agent)
            if assigned_agent:
                self.tasks[task_id]["status"] = TaskStatus.RUNNING.value
                self.tasks[task_id]["started_at"] = datetime.now().isoformat()

                # Update agent status
                if assigned_agent in self.agents:
                    self.agents[assigned_agent]["status"] = AgentStatus.BUSY.value

            logger.info(f"Task submitted: {task_id} ({task_type})")

            return {
                "status": "success",
                "task_id": task_id,
                "assigned_agent": assigned_agent,
                "message": f"Task {task_id} submitted successfully"
            }
        except Exception as e:
            logger.error(f"Error submitting task: {e}")
            return {
                "status": "error",
                "error": str(e)
            }

    async def handle_get_task_status(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get status of a specific task"""
        try:
            task_id = params.get("task_id")

            if task_id in self.tasks:
                return {
                    "status": "success",
                    "task": self.tasks[task_id]
                }
            else:
                return {
                    "status": "error",
                    "error": f"Task {task_id} not found"
                }
        except Exception as e:
            logger.error(f"Error getting task status: {e}")
            return {
                "status": "error",
                "error": str(e)
            }

    async def handle_cancel_task(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Cancel a running task"""
        try:
            task_id = params.get("task_id")

            if task_id in self.tasks:
                task = self.tasks[task_id]
                if task["status"] in [TaskStatus.PENDING.value, TaskStatus.RUNNING.value]:
                    task["status"] = TaskStatus.CANCELLED.value
                    task["completed_at"] = datetime.now().isoformat()

                    # Free up agent
                    if task["assigned_agent"] in self.agents:
                        self.agents[task["assigned_agent"]]["status"] = AgentStatus.IDLE.value

                    logger.info(f"Task cancelled: {task_id}")
                    return {
                        "status": "success",
                        "message": f"Task {task_id} cancelled"
                    }
                else:
                    return {
                        "status": "error",
                        "error": f"Task {task_id} cannot be cancelled (status: {task['status']})"
                    }
            else:
                return {
                    "status": "error",
                    "error": f"Task {task_id} not found"
                }
        except Exception as e:
            logger.error(f"Error cancelling task: {e}")
            return {
                "status": "error",
                "error": str(e)
            }

    async def handle_list_tasks(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """List all tasks"""
        try:
            filter_status = params.get("status")
            filter_agent = params.get("agent_id")
            limit = params.get("limit", 100)

            tasks_list = list(self.tasks.values())

            # Apply filters
            if filter_status:
                tasks_list = [t for t in tasks_list if t["status"] == filter_status]
            if filter_agent:
                tasks_list = [t for t in tasks_list if t["assigned_agent"] == filter_agent]

            # Sort by creation time (newest first)
            tasks_list.sort(key=lambda x: x["created_at"], reverse=True)

            # Apply limit
            tasks_list = tasks_list[:limit]

            return {
                "status": "success",
                "tasks": tasks_list,
                "total": len(tasks_list)
            }
        except Exception as e:
            logger.error(f"Error listing tasks: {e}")
            return {
                "status": "error",
                "error": str(e)
            }

    async def handle_orchestrate_workflow(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Orchestrate a complex workflow involving multiple agents"""
        try:
            workflow_type = params.get("workflow_type")
            workflow_data = params.get("workflow_data", {})
            steps = params.get("steps", [])

            # Generate workflow ID
            self.workflow_counter += 1
            workflow_id = f"workflow_{self.workflow_counter:06d}"

            # Create workflow
            self.workflows[workflow_id] = {
                "id": workflow_id,
                "type": workflow_type,
                "data": workflow_data,
                "steps": steps,
                "current_step": 0,
                "status": "running",
                "created_at": datetime.now().isoformat(),
                "completed_at": None,
                "tasks": [],
                "results": {}
            }

            # Start executing workflow steps
            # (In real implementation, this would be async)
            for i, step in enumerate(steps):
                task_result = await self.handle_submit_task({
                    "task_type": step.get("type"),
                    "task_data": step.get("data", {}),
                    "priority": "high"
                })

                if task_result["status"] == "success":
                    self.workflows[workflow_id]["tasks"].append(task_result["task_id"])
                    self.workflows[workflow_id]["current_step"] = i + 1

            logger.info(f"Workflow orchestrated: {workflow_id} ({workflow_type})")

            return {
                "status": "success",
                "workflow_id": workflow_id,
                "message": f"Workflow {workflow_id} started with {len(steps)} steps"
            }
        except Exception as e:
            logger.error(f"Error orchestrating workflow: {e}")
            return {
                "status": "error",
                "error": str(e)
            }

    async def handle_get_workflow_status(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get status of a workflow"""
        try:
            workflow_id = params.get("workflow_id")

            if workflow_id in self.workflows:
                workflow = self.workflows[workflow_id]

                # Check task statuses
                all_completed = all(
                    self.tasks.get(tid, {}).get("status") == TaskStatus.COMPLETED.value
                    for tid in workflow["tasks"]
                )

                if all_completed and workflow["status"] == "running":
                    workflow["status"] = "completed"
                    workflow["completed_at"] = datetime.now().isoformat()

                return {
                    "status": "success",
                    "workflow": workflow
                }
            else:
                return {
                    "status": "error",
                    "error": f"Workflow {workflow_id} not found"
                }
        except Exception as e:
            logger.error(f"Error getting workflow status: {e}")
            return {
                "status": "error",
                "error": str(e)
            }

    async def handle_health(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Health check endpoint"""
        active_agents = sum(1 for a in self.agents.values() if a["status"] != AgentStatus.OFFLINE.value)
        running_tasks = sum(1 for t in self.tasks.values() if t["status"] == TaskStatus.RUNNING.value)

        return {
            "status": "healthy",
            "service": "agent_coordinator",
            "agents": {
                "total": len(self.agents),
                "active": active_agents
            },
            "tasks": {
                "total": len(self.tasks),
                "running": running_tasks
            },
            "workflows": {
                "total": len(self.workflows)
            }
        }

    async def handle_capabilities(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Return server capabilities"""
        return {
            "capabilities": [
                "register_agent",
                "unregister_agent",
                "list_agents",
                "get_agent_status",
                "submit_task",
                "get_task_status",
                "cancel_task",
                "list_tasks",
                "orchestrate_workflow",
                "get_workflow_status"
            ],
            "supported_agent_types": [
                "content_generation",
                "quiz_generation",
                "terrain_generation",
                "script_generation",
                "analytics",
                "review"
            ],
            "task_priorities": ["low", "normal", "high", "critical"],
            "workflow_types": [
                "content_creation",
                "assessment_generation",
                "full_lesson_creation",
                "roblox_game_deployment"
            ]
        }

    def _find_suitable_agent(self, task_type: str) -> Optional[str]:
        """Find a suitable agent for the task type"""
        # Look for idle agents with matching capabilities
        for agent_id, agent in self.agents.items():
            if (agent["status"] == AgentStatus.IDLE.value and
                task_type in agent.get("capabilities", [])):
                return agent_id

        # If no specific match, find any idle agent
        for agent_id, agent in self.agents.items():
            if agent["status"] == AgentStatus.IDLE.value:
                return agent_id

        return None

    async def process_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Process incoming MCP request"""
        method = request.get("method")
        params = request.get("params", {})
        request_id = request.get("id")

        if method in self.methods:
            try:
                result = await self.methods[method](params)
                return {
                    "jsonrpc": "2.0",
                    "result": result,
                    "id": request_id
                }
            except Exception as e:
                logger.error(f"Error processing request: {e}")
                return {
                    "jsonrpc": "2.0",
                    "error": {
                        "code": -32603,
                        "message": str(e)
                    },
                    "id": request_id
                }
        else:
            return {
                "jsonrpc": "2.0",
                "error": {
                    "code": -32601,
                    "message": f"Method not found: {method}"
                },
                "id": request_id
            }

    async def run_stdio(self):
        """Run the server using stdio for MCP communication"""
        logger.info("Agent Coordinator MCP Server started (stdio mode)")

        while True:
            try:
                # Read from stdin
                line = sys.stdin.readline()
                if not line:
                    break

                # Parse JSON request
                request = json.loads(line.strip())

                # Process request
                response = await self.process_request(request)

                # Write response to stdout
                sys.stdout.write(json.dumps(response) + "\n")
                sys.stdout.flush()

            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON: {e}")
                error_response = {
                    "jsonrpc": "2.0",
                    "error": {
                        "code": -32700,
                        "message": "Parse error"
                    },
                    "id": None
                }
                sys.stdout.write(json.dumps(error_response) + "\n")
                sys.stdout.flush()
            except Exception as e:
                logger.error(f"Server error: {e}")
                break


def main():
    """Main entry point"""
    server = AgentCoordinatorMCPServer()

    # Run in stdio mode (standard for MCP)
    try:
        asyncio.run(server.run_stdio())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()