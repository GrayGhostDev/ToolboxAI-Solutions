"""
Enhanced Rojo Integration Manager
Manages Rojo 7.5.1 servers and project synchronization with Roblox Studio
"""

import asyncio
import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
import aiohttp
import aiofiles
from pydantic import BaseModel, Field
import logging

from apps.backend.core.config import settings

logger = logging.getLogger(__name__)


class RojoProject(BaseModel):
    """Rojo project configuration"""

    project_id: str
    name: str
    path: Path
    port: int
    status: str = Field(default="stopped")  # stopped, starting, running, error
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    user_id: str
    session_id: Optional[str] = None
    process_pid: Optional[int] = None


class RojoProjectConfig(BaseModel):
    """Rojo project.json configuration"""

    name: str
    tree: Dict[str, Any]
    serve_port: Optional[int] = None
    serve_address: Optional[str] = Field(default="127.0.0.1")
    glob_ignore_paths: Optional[List[str]] = Field(
        default_factory=lambda: ["**/node_modules", "**/.git", "**/*.lock"]
    )


class RojoSyncStatus(BaseModel):
    """Rojo synchronization status"""

    connected: bool
    session_id: Optional[str] = None
    project_name: Optional[str] = None
    client_count: int = Field(default=0)
    last_sync: Optional[datetime] = None
    errors: List[str] = Field(default_factory=list)


class EnhancedRojoManager:
    """
    Enhanced Rojo manager for version 7.5.1 with multi-project support
    and automatic port allocation
    """

    def __init__(self):
        # Rojo server configuration for ToolboxAI-Solutions at localhost:34872
        self.base_port = getattr(settings, "ROJO_BASE_PORT", 34872)
        self.rojo_host = "localhost"  # Default host for Rojo server
        self.max_projects = getattr(settings, "MAX_ROJO_PROJECTS", 10)
        self.projects_dir = Path(getattr(settings, "ROJO_PROJECTS_DIR", "/tmp/rojo_projects"))
        self.rojo_binary = "rojo"  # Assumes rojo is in PATH via aftman
        self.active_projects: Dict[str, RojoProject] = {}
        self.port_allocations: Dict[int, str] = {}  # port -> project_id
        self.session: Optional[aiohttp.ClientSession] = None

        # Create projects directory
        self.projects_dir.mkdir(parents=True, exist_ok=True)

        logger.info(
            f"Rojo Manager initialized - Server: {self.rojo_host}:{self.base_port} for ToolboxAI-Solutions"
        )

    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        # Stop all active projects
        for project_id in list(self.active_projects.keys()):
            await self.stop_project(project_id)

        if self.session:
            await self.session.close()

    def _allocate_port(self) -> Optional[int]:
        """
        Allocate an available port for a new Rojo server

        Returns:
            Available port number or None if all ports are in use
        """
        for i in range(self.max_projects):
            port = self.base_port + i
            if port not in self.port_allocations:
                return port
        return None

    def _release_port(self, port: int):
        """Release a port allocation"""
        if port in self.port_allocations:
            del self.port_allocations[port]

    async def check_rojo_installed(self) -> bool:
        """
        Check if Rojo is installed and accessible

        Returns:
            True if Rojo is installed
        """
        try:
            process = await asyncio.create_subprocess_exec(
                self.rojo_binary,
                "--version",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await process.communicate()

            if process.returncode == 0:
                version = stdout.decode().strip()
                logger.info(f"Rojo version: {version}")
                return "7.5" in version or "7.4" in version  # Accept 7.4+ for compatibility
            else:
                logger.error(f"Rojo not found or error: {stderr.decode()}")
                return False

        except Exception as e:
            logger.error(f"Error checking Rojo installation: {e}")
            return False

    async def create_project(
        self, project_name: str, user_id: str, project_config: RojoProjectConfig
    ) -> RojoProject:
        """
        Create a new Rojo project

        Args:
            project_name: Name of the project
            user_id: User ID creating the project
            project_config: Rojo project configuration

        Returns:
            Created RojoProject
        """
        # Generate project ID
        project_id = f"{user_id}_{project_name}_{datetime.utcnow().timestamp()}"

        # Allocate port
        port = self._allocate_port()
        if not port:
            raise ValueError("No available ports for new Rojo project")

        # Create project directory
        project_path = self.projects_dir / project_id
        project_path.mkdir(parents=True, exist_ok=True)

        # Set port in config
        project_config.serve_port = port

        # Create default.project.json
        project_json = {
            "name": project_config.name,
            "tree": project_config.tree,
            "servePort": port,
            "serveAddress": project_config.serve_address,
            "globIgnorePaths": project_config.glob_ignore_paths,
        }

        project_file = project_path / "default.project.json"
        async with aiofiles.open(project_file, "w") as f:
            await f.write(json.dumps(project_json, indent=2))

        # Create source directories based on tree structure
        await self._create_source_structure(project_path, project_config.tree)

        # Create project record
        project = RojoProject(
            project_id=project_id, name=project_name, path=project_path, port=port, user_id=user_id
        )

        # Store project
        self.active_projects[project_id] = project
        self.port_allocations[port] = project_id

        logger.info(f"Created Rojo project: {project_id} on port {port}")

        return project

    async def _create_source_structure(self, project_path: Path, tree: Dict[str, Any]):
        """
        Create source directory structure based on Rojo tree

        Args:
            project_path: Project root path
            tree: Rojo tree configuration
        """
        # Create src directory
        src_dir = project_path / "src"
        src_dir.mkdir(exist_ok=True)

        # Create subdirectories based on tree structure
        for service_name, service_config in tree.items():
            if service_name.startswith("$"):
                continue

            if isinstance(service_config, dict):
                # Check for path references
                if "$path" in service_config:
                    # Create the referenced file/directory
                    path_parts = service_config["$path"].split("/")
                    file_path = project_path
                    for part in path_parts[:-1]:
                        file_path = file_path / part
                        file_path.mkdir(parents=True, exist_ok=True)

                    # Create the file if it's a .lua file
                    if path_parts[-1].endswith(".lua"):
                        file_path = file_path / path_parts[-1]
                        if not file_path.exists():
                            async with aiofiles.open(file_path, "w") as f:
                                await f.write(
                                    f"-- {path_parts[-1]}\n-- Auto-generated by Rojo Manager\n\nreturn {{}}\n"
                                )

    async def start_project(self, project_id: str) -> RojoSyncStatus:
        """
        Start Rojo server for a project

        Args:
            project_id: Project ID to start

        Returns:
            Sync status
        """
        if project_id not in self.active_projects:
            raise ValueError(f"Project {project_id} not found")

        project = self.active_projects[project_id]

        if project.status == "running":
            return await self.get_sync_status(project_id)

        project.status = "starting"

        try:
            # Start Rojo serve process
            process = await asyncio.create_subprocess_exec(
                self.rojo_binary,
                "serve",
                str(project.path / "default.project.json"),
                "--port",
                str(project.port),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(project.path),
            )

            project.process_pid = process.pid
            project.status = "running"
            project.updated_at = datetime.utcnow()

            # Give it a moment to start
            await asyncio.sleep(2)

            # Check if it's running
            sync_status = await self.get_sync_status(project_id)

            if sync_status.connected:
                logger.info(f"Started Rojo server for project {project_id} on port {project.port}")
            else:
                logger.warning(f"Rojo server started but not responding for project {project_id}")

            return sync_status

        except Exception as e:
            project.status = "error"
            logger.error(f"Error starting Rojo server for project {project_id}: {e}")
            raise

    async def stop_project(self, project_id: str) -> bool:
        """
        Stop Rojo server for a project

        Args:
            project_id: Project ID to stop

        Returns:
            True if stopped successfully
        """
        if project_id not in self.active_projects:
            return False

        project = self.active_projects[project_id]

        if project.process_pid:
            try:
                # Terminate the process
                os.kill(project.process_pid, 15)  # SIGTERM
                await asyncio.sleep(1)

                # Check if still running and force kill if needed
                try:
                    os.kill(project.process_pid, 0)
                    os.kill(project.process_pid, 9)  # SIGKILL
                except ProcessLookupError:
                    pass

                project.process_pid = None

            except Exception as e:
                logger.error(f"Error stopping Rojo server for project {project_id}: {e}")

        project.status = "stopped"
        project.updated_at = datetime.utcnow()

        logger.info(f"Stopped Rojo server for project {project_id}")
        return True

    async def get_sync_status(self, project_id: str) -> RojoSyncStatus:
        """
        Get synchronization status for a project

        Args:
            project_id: Project ID

        Returns:
            Sync status
        """
        if project_id not in self.active_projects:
            return RojoSyncStatus(connected=False, errors=["Project not found"])

        project = self.active_projects[project_id]

        if project.status != "running":
            return RojoSyncStatus(connected=False, errors=["Project not running"])

        if not self.session:
            self.session = aiohttp.ClientSession()

        try:
            # Check Rojo API endpoint at localhost:34872 for ToolboxAI-Solutions
            async with self.session.get(
                f"http://{self.rojo_host}:{project.port}/api/rojo",
                timeout=aiohttp.ClientTimeout(total=2),
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return RojoSyncStatus(
                        connected=True,
                        session_id=data.get("sessionId"),
                        project_name=data.get("projectName"),
                        client_count=data.get("clientCount", 0),
                        last_sync=datetime.utcnow(),
                    )
                else:
                    return RojoSyncStatus(
                        connected=False, errors=[f"Rojo API returned status {response.status}"]
                    )

        except asyncio.TimeoutError:
            return RojoSyncStatus(connected=False, errors=["Connection timeout"])
        except Exception as e:
            return RojoSyncStatus(connected=False, errors=[str(e)])

    async def build_project(self, project_id: str, output_path: Optional[Path] = None) -> Path:
        """
        Build Rojo project to .rbxl or .rbxm file

        Args:
            project_id: Project ID to build
            output_path: Optional output path for built file

        Returns:
            Path to built file
        """
        if project_id not in self.active_projects:
            raise ValueError(f"Project {project_id} not found")

        project = self.active_projects[project_id]

        if not output_path:
            output_path = project.path / f"{project.name}.rbxl"

        try:
            process = await asyncio.create_subprocess_exec(
                self.rojo_binary,
                "build",
                str(project.path / "default.project.json"),
                "--output",
                str(output_path),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(project.path),
            )

            stdout, stderr = await process.communicate()

            if process.returncode == 0:
                logger.info(f"Built Rojo project {project_id} to {output_path}")
                return output_path
            else:
                error_msg = stderr.decode()
                logger.error(f"Failed to build project {project_id}: {error_msg}")
                raise ValueError(f"Build failed: {error_msg}")

        except Exception as e:
            logger.error(f"Error building project {project_id}: {e}")
            raise

    async def delete_project(self, project_id: str) -> bool:
        """
        Delete a project and clean up resources

        Args:
            project_id: Project ID to delete

        Returns:
            True if deleted successfully
        """
        if project_id not in self.active_projects:
            return False

        # Stop the project first
        await self.stop_project(project_id)

        project = self.active_projects[project_id]

        # Release port
        self._release_port(project.port)

        # Delete project directory
        if project.path.exists():
            shutil.rmtree(project.path)

        # Remove from active projects
        del self.active_projects[project_id]

        logger.info(f"Deleted project {project_id}")
        return True

    async def list_projects(self, user_id: Optional[str] = None) -> List[RojoProject]:
        """
        List all projects or projects for a specific user

        Args:
            user_id: Optional user ID to filter by

        Returns:
            List of projects
        """
        projects = list(self.active_projects.values())

        if user_id:
            projects = [p for p in projects if p.user_id == user_id]

        return projects

    async def get_project(self, project_id: str) -> Optional[RojoProject]:
        """
        Get a specific project

        Args:
            project_id: Project ID

        Returns:
            Project if found, None otherwise
        """
        return self.active_projects.get(project_id)

    async def update_project_files(self, project_id: str, files: Dict[str, str]) -> bool:
        """
        Update files in a project

        Args:
            project_id: Project ID
            files: Dictionary of file paths (relative to project) and contents

        Returns:
            True if updated successfully
        """
        if project_id not in self.active_projects:
            return False

        project = self.active_projects[project_id]

        try:
            for file_path, content in files.items():
                full_path = project.path / file_path
                full_path.parent.mkdir(parents=True, exist_ok=True)

                async with aiofiles.open(full_path, "w") as f:
                    await f.write(content)

            project.updated_at = datetime.utcnow()
            logger.info(f"Updated {len(files)} files in project {project_id}")
            return True

        except Exception as e:
            logger.error(f"Error updating project files: {e}")
            return False

    async def get_project_files(self, project_id: str) -> Dict[str, str]:
        """
        Get all Lua files from a project

        Args:
            project_id: Project ID

        Returns:
            Dictionary of file paths and contents
        """
        if project_id not in self.active_projects:
            return {}

        project = self.active_projects[project_id]
        files = {}

        try:
            for lua_file in project.path.rglob("*.lua"):
                relative_path = lua_file.relative_to(project.path)
                async with aiofiles.open(lua_file, "r") as f:
                    content = await f.read()
                files[str(relative_path)] = content

            return files

        except Exception as e:
            logger.error(f"Error getting project files: {e}")
            return {}


# Global instance
rojo_manager = EnhancedRojoManager()
