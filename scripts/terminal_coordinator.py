#!/usr/bin/env python3
"""
Terminal Coordination System for ToolBoxAI Solutions
Manages terminal dependencies and prevents duplicate work
"""

import json
import os
import time
import threading
import socket
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Set
from enum import Enum

class TaskStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    WAITING = "waiting"
    COMPLETED = "completed"
    FAILED = "failed"

class TerminalCoordinator:
    """Coordinates work between multiple terminals to prevent conflicts"""
    
    def __init__(self, coordination_file: str = "/tmp/terminal_coordination.json"):
        self.coordination_file = Path(coordination_file)
        self.terminal_id = self._generate_terminal_id()
        self.tasks: Dict[str, Dict] = {}
        self.dependencies: Dict[str, List[str]] = {}
        self.lock = threading.Lock()
        self._ensure_coordination_file()
        
    def _generate_terminal_id(self) -> str:
        """Generate unique terminal ID"""
        pid = os.getpid()
        hostname = socket.gethostname()
        timestamp = int(time.time())
        return f"{hostname}_{pid}_{timestamp}"
    
    def _ensure_coordination_file(self):
        """Ensure coordination file exists"""
        if not self.coordination_file.exists():
            self.coordination_file.write_text(json.dumps({
                "tasks": {},
                "terminals": {},
                "dependencies": {}
            }))
    
    def _load_state(self) -> Dict:
        """Load current coordination state"""
        try:
            return json.loads(self.coordination_file.read_text())
        except:
            return {"tasks": {}, "terminals": {}, "dependencies": {}}
    
    def _save_state(self, state: Dict):
        """Save coordination state"""
        self.coordination_file.write_text(json.dumps(state, indent=2))
    
    def register_terminal(self, name: str, capabilities: List[str]):
        """Register this terminal with its capabilities"""
        with self.lock:
            state = self._load_state()
            state["terminals"][self.terminal_id] = {
                "name": name,
                "capabilities": capabilities,
                "registered_at": datetime.now().isoformat(),
                "status": "active"
            }
            self._save_state(state)
            print(f"✓ Terminal '{name}' registered with ID: {self.terminal_id}")
    
    def claim_task(self, task_id: str, dependencies: Optional[List[str]] = None) -> bool:
        """Attempt to claim a task for this terminal"""
        with self.lock:
            state = self._load_state()
            
            # Check if task is already claimed
            if task_id in state["tasks"]:
                task = state["tasks"][task_id]
                if task["status"] in [TaskStatus.IN_PROGRESS.value, TaskStatus.COMPLETED.value]:
                    print(f"✗ Task '{task_id}' already {task['status']} by terminal {task.get('terminal_id', 'unknown')}")
                    return False
            
            # Check dependencies
            if dependencies:
                for dep in dependencies:
                    if dep not in state["tasks"] or state["tasks"][dep]["status"] != TaskStatus.COMPLETED.value:
                        print(f"⏳ Waiting for dependency '{dep}' to complete")
                        state["tasks"][task_id] = {
                            "status": TaskStatus.WAITING.value,
                            "terminal_id": self.terminal_id,
                            "dependencies": dependencies,
                            "started_at": datetime.now().isoformat()
                        }
                        self._save_state(state)
                        return False
            
            # Claim the task
            state["tasks"][task_id] = {
                "status": TaskStatus.IN_PROGRESS.value,
                "terminal_id": self.terminal_id,
                "dependencies": dependencies or [],
                "started_at": datetime.now().isoformat()
            }
            self._save_state(state)
            print(f"✓ Task '{task_id}' claimed by this terminal")
            return True
    
    def complete_task(self, task_id: str, result: Optional[Dict] = None):
        """Mark a task as completed"""
        with self.lock:
            state = self._load_state()
            if task_id in state["tasks"]:
                state["tasks"][task_id]["status"] = TaskStatus.COMPLETED.value
                state["tasks"][task_id]["completed_at"] = datetime.now().isoformat()
                if result:
                    state["tasks"][task_id]["result"] = result
                self._save_state(state)
                print(f"✓ Task '{task_id}' completed")
                
                # Check for waiting tasks that can now proceed
                self._check_waiting_tasks(state)
    
    def fail_task(self, task_id: str, error: str):
        """Mark a task as failed"""
        with self.lock:
            state = self._load_state()
            if task_id in state["tasks"]:
                state["tasks"][task_id]["status"] = TaskStatus.FAILED.value
                state["tasks"][task_id]["failed_at"] = datetime.now().isoformat()
                state["tasks"][task_id]["error"] = error
                self._save_state(state)
                print(f"✗ Task '{task_id}' failed: {error}")
    
    def wait_for_task(self, task_id: str, timeout: int = 300) -> bool:
        """Wait for a task to complete"""
        start_time = time.time()
        while time.time() - start_time < timeout:
            state = self._load_state()
            if task_id in state["tasks"]:
                if state["tasks"][task_id]["status"] == TaskStatus.COMPLETED.value:
                    print(f"✓ Task '{task_id}' is complete")
                    return True
                elif state["tasks"][task_id]["status"] == TaskStatus.FAILED.value:
                    print(f"✗ Task '{task_id}' failed")
                    return False
            time.sleep(2)
        print(f"⏰ Timeout waiting for task '{task_id}'")
        return False
    
    def _check_waiting_tasks(self, state: Dict):
        """Check if any waiting tasks can now proceed"""
        for task_id, task in state["tasks"].items():
            if task["status"] == TaskStatus.WAITING.value:
                deps_complete = all(
                    state["tasks"].get(dep, {}).get("status") == TaskStatus.COMPLETED.value
                    for dep in task.get("dependencies", [])
                )
                if deps_complete:
                    print(f"🔄 Task '{task_id}' dependencies met, can proceed")
    
    def get_status(self) -> Dict:
        """Get current coordination status"""
        state = self._load_state()
        return {
            "terminal_id": self.terminal_id,
            "active_terminals": len([t for t in state["terminals"].values() if t["status"] == "active"]),
            "tasks": {
                "total": len(state["tasks"]),
                "pending": len([t for t in state["tasks"].values() if t["status"] == TaskStatus.PENDING.value]),
                "in_progress": len([t for t in state["tasks"].values() if t["status"] == TaskStatus.IN_PROGRESS.value]),
                "waiting": len([t for t in state["tasks"].values() if t["status"] == TaskStatus.WAITING.value]),
                "completed": len([t for t in state["tasks"].values() if t["status"] == TaskStatus.COMPLETED.value]),
                "failed": len([t for t in state["tasks"].values() if t["status"] == TaskStatus.FAILED.value])
            }
        }
    
    def cleanup_stale_tasks(self, max_age_minutes: int = 30):
        """Clean up stale tasks that have been in progress too long"""
        with self.lock:
            state = self._load_state()
            cutoff_time = datetime.now() - timedelta(minutes=max_age_minutes)
            
            for task_id, task in list(state["tasks"].items()):
                if task["status"] == TaskStatus.IN_PROGRESS.value:
                    started_at = datetime.fromisoformat(task["started_at"])
                    if started_at < cutoff_time:
                        task["status"] = TaskStatus.FAILED.value
                        task["error"] = "Task timed out"
                        print(f"⏰ Cleaned up stale task '{task_id}'")
            
            self._save_state(state)

# Terminal-specific task configurations
TERMINAL_TASKS = {
    "backend": {
        "tasks": [
            "setup_database",
            "start_fastapi_server",
            "start_socketio_server",
            "start_roblox_bridge"
        ],
        "dependencies": {
            "start_fastapi_server": ["setup_database"],
            "start_socketio_server": ["start_fastapi_server"],
            "start_roblox_bridge": ["start_fastapi_server"]
        }
    },
    "frontend": {
        "tasks": [
            "install_npm_packages",
            "build_dashboard",
            "start_dashboard_dev"
        ],
        "dependencies": {
            "build_dashboard": ["install_npm_packages"],
            "start_dashboard_dev": ["install_npm_packages"]
        }
    },
    "testing": {
        "tasks": [
            "run_backend_tests",
            "run_frontend_tests",
            "run_integration_tests"
        ],
        "dependencies": {
            "run_integration_tests": ["run_backend_tests", "run_frontend_tests"]
        }
    }
}

def main():
    """Example usage of terminal coordinator"""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: terminal_coordinator.py <terminal_type> [task_name]")
        print("Terminal types: backend, frontend, testing")
        sys.exit(1)
    
    terminal_type = sys.argv[1]
    task_name = sys.argv[2] if len(sys.argv) > 2 else None
    
    coordinator = TerminalCoordinator()
    coordinator.register_terminal(f"{terminal_type}_terminal", [terminal_type])
    
    if terminal_type in TERMINAL_TASKS:
        config = TERMINAL_TASKS[terminal_type]
        
        if task_name:
            # Execute specific task
            deps = config["dependencies"].get(task_name, [])
            if coordinator.claim_task(task_name, deps):
                print(f"🚀 Executing task: {task_name}")
                # Simulate task execution
                time.sleep(2)
                coordinator.complete_task(task_name)
            else:
                print(f"⏳ Task '{task_name}' cannot be executed yet")
        else:
            # Execute all tasks for this terminal
            for task in config["tasks"]:
                deps = config["dependencies"].get(task, [])
                
                # Wait for dependencies
                for dep in deps:
                    if not coordinator.wait_for_task(dep):
                        print(f"✗ Dependency '{dep}' failed or timed out")
                        continue
                
                if coordinator.claim_task(task, deps):
                    print(f"🚀 Executing task: {task}")
                    # Simulate task execution
                    time.sleep(2)
                    coordinator.complete_task(task)
    
    # Print final status
    status = coordinator.get_status()
    print(f"\n📊 Final Status:")
    print(f"  Terminal ID: {status['terminal_id']}")
    print(f"  Active Terminals: {status['active_terminals']}")
    print(f"  Tasks:")
    for status_type, count in status['tasks'].items():
        if count > 0:
            print(f"    {status_type}: {count}")

if __name__ == "__main__":
    main()