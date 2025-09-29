"""
Rojo API Integration Service
Connects to Roblox Studio via Rojo API for environment creation
"""

import asyncio
import json
import logging
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Any
import aiohttp
import aiofiles

from apps.backend.core.config import settings

logger = logging.getLogger(__name__)


class RojoAPIError(Exception):
    """Custom exception for Rojo API errors"""

    pass


class RojoAPIService:
    """Service for interacting with Roblox Studio via Rojo API"""

    def __init__(self):
        self.rojo_port = getattr(settings, "ROJO_PORT", 34872)
        self.rojo_host = getattr(settings, "ROJO_HOST", "localhost")
        self.base_url = f"http://{self.rojo_host}:{self.rojo_port}"
        self.session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()

    async def check_rojo_connection(self) -> bool:
        """Check if Rojo is running and accessible"""
        try:
            if not self.session:
                self.session = aiohttp.ClientSession()

            async with self.session.get(f"{self.base_url}/api/rojo") as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"Rojo connection successful: {data}")
                    return True
                else:
                    logger.warning(f"Rojo connection failed: {response.status}")
                    return False
        except Exception as e:
            logger.error(f"Rojo connection error: {e}")
            return False

    async def get_rojo_info(self) -> Dict[str, Any]:
        """Get Rojo server information"""
        try:
            if not self.session:
                self.session = aiohttp.ClientSession()

            async with self.session.get(f"{self.base_url}/api/rojo") as response:
                if response.status == 200:
                    return await response.json()
                else:
                    raise RojoAPIError(f"Failed to get Rojo info: {response.status}")
        except Exception as e:
            logger.error(f"Error getting Rojo info: {e}")
            raise RojoAPIError(f"Rojo info request failed: {e}")

    async def create_environment_from_description(
        self, description: str, environment_name: str, user_id: str
    ) -> Dict[str, Any]:
        """
        Create a Roblox environment from natural language description

        Args:
            description: Natural language description of the environment
            environment_name: Name for the environment
            user_id: ID of the user creating the environment

        Returns:
            Dictionary with creation results and environment details
        """
        try:
            # Step 1: Parse natural language description
            parsed_components = await self._parse_environment_description(description)

            # Step 2: Generate Rojo project structure
            project_structure = await self._generate_rojo_structure(
                parsed_components, environment_name, user_id
            )

            # Step 3: Create temporary project directory
            project_path = await self._create_project_directory(
                project_structure, environment_name, user_id
            )

            # Step 4: Build and sync with Roblox Studio
            sync_result = await self._sync_to_roblox_studio(project_path)

            return {
                "success": True,
                "environment_name": environment_name,
                "project_path": str(project_path),
                "components": parsed_components,
                "sync_result": sync_result,
                "rojo_url": f"rojo://{self.rojo_host}:{self.rojo_port}/api/rojo",
            }

        except Exception as e:
            logger.error(f"Environment creation failed: {e}")
            return {"success": False, "error": str(e), "environment_name": environment_name}

    async def _parse_environment_description(self, description: str) -> Dict[str, Any]:
        """Parse natural language description into structured components"""
        # This would integrate with AI/ML service for natural language processing
        # For now, we'll create a basic parser

        components = {
            "terrain": [],
            "buildings": [],
            "objects": [],
            "lighting": {},
            "effects": [],
            "scripts": [],
        }

        # Basic keyword detection (in production, use proper NLP)
        description_lower = description.lower()

        # Terrain detection
        if any(
            word in description_lower for word in ["mountain", "hill", "valley", "forest", "desert"]
        ):
            components["terrain"].append(
                {"type": "natural", "description": "Natural terrain based on description"}
            )

        # Building detection
        if any(
            word in description_lower
            for word in ["house", "building", "school", "classroom", "lab"]
        ):
            components["buildings"].append(
                {"type": "educational", "description": "Educational building structure"}
            )

        # Object detection
        if any(
            word in description_lower
            for word in ["table", "chair", "computer", "board", "equipment"]
        ):
            components["objects"].append(
                {"type": "furniture", "description": "Educational furniture and equipment"}
            )

        # Lighting detection
        if any(word in description_lower for word in ["bright", "dark", "sunny", "moonlight"]):
            components["lighting"] = {"type": "ambient", "description": "Ambient lighting setup"}

        return components

    async def _generate_rojo_structure(
        self, components: Dict[str, Any], environment_name: str, user_id: str
    ) -> Dict[str, Any]:
        """Generate Rojo project structure from parsed components"""

        project_structure = {
            "name": environment_name,
            "tree": {
                "$className": "DataModel",
                "ReplicatedStorage": {
                    "$className": "ReplicatedStorage",
                    "SharedModules": {
                        "$className": "Folder",
                        "EnvironmentConfig": {"$path": "src/shared/EnvironmentConfig.lua"},
                    },
                },
                "ServerStorage": {
                    "$className": "ServerStorage",
                    "EnvironmentScripts": {"$className": "Folder"},
                },
                "Workspace": {
                    "$className": "Workspace",
                    "Environment": {
                        "$className": "Folder",
                        "Terrain": {"$className": "Terrain"},
                        "Buildings": {"$className": "Folder"},
                        "Objects": {"$className": "Folder"},
                        "Lighting": {"$className": "Lighting"},
                    },
                },
            },
        }

        # Add components based on parsed description
        if components["terrain"]:
            project_structure["tree"]["Workspace"]["Environment"]["Terrain"]["$properties"] = {
                "MaterialColors": "BrickColor"
            }

        if components["buildings"]:
            for i, building in enumerate(components["buildings"]):
                project_structure["tree"]["Workspace"]["Environment"]["Buildings"][
                    f"Building_{i+1}"
                ] = {"$className": "Model", "$properties": {"Name": building["type"]}}

        if components["objects"]:
            for i, obj in enumerate(components["objects"]):
                project_structure["tree"]["Workspace"]["Environment"]["Objects"][
                    f"Object_{i+1}"
                ] = {"$className": "Model", "$properties": {"Name": obj["type"]}}

        return project_structure

    async def _create_project_directory(
        self, project_structure: Dict[str, Any], environment_name: str, user_id: str
    ) -> Path:
        """Create temporary project directory with Rojo structure"""

        # Create temporary directory
        temp_dir = Path(tempfile.mkdtemp(prefix=f"rojo_{environment_name}_"))

        # Create project.json
        project_config = {
            "name": project_structure["name"],
            "tree": project_structure["tree"],
            "serve": {"port": self.rojo_port},
        }

        project_json_path = temp_dir / "default.project.json"
        async with aiofiles.open(project_json_path, "w") as f:
            await f.write(json.dumps(project_config, indent=2))

        # Create source directory structure
        src_dir = temp_dir / "src"
        src_dir.mkdir(exist_ok=True)

        shared_dir = src_dir / "shared"
        shared_dir.mkdir(exist_ok=True)

        # Create basic environment configuration script
        env_config_script = f"""-- Environment Configuration for {environment_name}
-- Generated for user: {user_id}

local EnvironmentConfig = {{}}

EnvironmentConfig.Name = "{environment_name}"
EnvironmentConfig.Description = "Educational environment created from natural language"
EnvironmentConfig.Creator = "{user_id}"
EnvironmentConfig.CreatedAt = os.time()

-- Environment settings
EnvironmentConfig.Settings = {{
    MaxPlayers = 20,
    AllowGuests = false,
    EducationalMode = true
}}

return EnvironmentConfig
"""

        config_script_path = shared_dir / "EnvironmentConfig.lua"
        async with aiofiles.open(config_script_path, "w") as f:
            await f.write(env_config_script)

        logger.info(f"Created project directory: {temp_dir}")
        return temp_dir

    async def _sync_to_roblox_studio(self, project_path: Path) -> Dict[str, Any]:
        """Sync the project to Roblox Studio via Rojo"""
        try:
            # Check if Rojo is running
            if not await self.check_rojo_connection():
                raise RojoAPIError("Rojo is not running or not accessible")

            # Build the project
            build_result = await self._build_rojo_project(project_path)

            if not build_result["success"]:
                raise RojoAPIError(f"Rojo build failed: {build_result['error']}")

            # Sync to Roblox Studio
            sync_result = await self._sync_project(project_path)

            return {
                "success": True,
                "build_result": build_result,
                "sync_result": sync_result,
                "project_path": str(project_path),
            }

        except Exception as e:
            logger.error(f"Sync to Roblox Studio failed: {e}")
            return {"success": False, "error": str(e)}

    async def _build_rojo_project(self, project_path: Path) -> Dict[str, Any]:
        """Build Rojo project"""
        try:
            # Run rojo build command
            process = await asyncio.create_subprocess_exec(
                "rojo",
                "build",
                str(project_path / "default.project.json"),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(project_path),
            )

            stdout, stderr = await process.communicate()

            if process.returncode == 0:
                return {
                    "success": True,
                    "output": stdout.decode(),
                    "project_path": str(project_path),
                }
            else:
                return {"success": False, "error": stderr.decode(), "output": stdout.decode()}

        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _sync_project(self, project_path: Path) -> Dict[str, Any]:
        """Sync project to Roblox Studio"""
        try:
            # Run rojo serve command in background
            process = await asyncio.create_subprocess_exec(
                "rojo",
                "serve",
                str(project_path / "default.project.json"),
                "--port",
                str(self.rojo_port),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(project_path),
            )

            # Give it a moment to start
            await asyncio.sleep(2)

            # Check if it's running
            if process.returncode is None:
                return {
                    "success": True,
                    "message": f"Rojo server started on port {self.rojo_port}",
                    "rojo_url": f"rojo://{self.rojo_host}:{self.rojo_port}/api/rojo",
                }
            else:
                stdout, stderr = await process.communicate()
                return {"success": False, "error": stderr.decode(), "output": stdout.decode()}

        except Exception as e:
            return {"success": False, "error": str(e)}

    async def get_environment_status(self, environment_name: str) -> Dict[str, Any]:
        """Get status of a created environment"""
        try:
            if not self.session:
                self.session = aiohttp.ClientSession()

            # This would check the status of the environment in Roblox Studio
            # For now, return a mock status
            return {
                "environment_name": environment_name,
                "status": "active",
                "players": 0,
                "last_updated": "2025-01-15T10:30:00Z",
                "rojo_connected": await self.check_rojo_connection(),
            }

        except Exception as e:
            logger.error(f"Error getting environment status: {e}")
            return {"environment_name": environment_name, "status": "error", "error": str(e)}


# Global instance
rojo_api_service = RojoAPIService()
