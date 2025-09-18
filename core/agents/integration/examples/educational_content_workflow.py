"""
Educational Content Integration Workflow Example

This example demonstrates a complete educational content deployment workflow
using the AI Agent Swarm for Application Integration.

Workflow steps:
1. Validate educational content schema
2. Sync data to database and cache
3. Deploy content to Roblox
4. Update frontend UI in real-time
5. Monitor deployment status
"""

import asyncio
import logging
from typing import Dict, Any
from datetime import datetime

# Import integration agents
from core.agents.integration import (
    IntegrationPlatform,
    IntegrationEvent
)
from core.agents.integration.backend import (
    APIGatewayAgent,
    DatabaseSyncAgent,
    APIEndpoint,
    APIVersion
)
from core.agents.integration.frontend import (
    UISyncAgent,
    RealtimeUpdateAgent,
    ComponentType,
    UIUpdateStrategy,
    ChannelType
)
from core.agents.integration.roblox import (
    StudioBridgeAgent,
    StudioConnectionType
)
from core.agents.integration.orchestration import (
    IntegrationCoordinator,
    TaskPriority
)
from core.agents.integration.data_flow import (
    SchemaValidatorAgent,
    SchemaType,
    ValidationLevel
)

logger = logging.getLogger(__name__)


class EducationalContentWorkflow:
    """
    Complete educational content deployment workflow
    """

    def __init__(self):
        """Initialize all agents for the workflow"""
        # Backend agents
        self.api_gateway = APIGatewayAgent()
        self.database_sync = DatabaseSyncAgent()

        # Frontend agents
        self.ui_sync = UISyncAgent()
        self.realtime_update = RealtimeUpdateAgent()

        # Roblox agents
        self.studio_bridge = StudioBridgeAgent()

        # Data flow agents
        self.schema_validator = SchemaValidatorAgent()

        # Orchestration
        self.coordinator = IntegrationCoordinator()

        # Register agents with coordinator
        asyncio.create_task(self._register_agents())

    async def _register_agents(self):
        """Register all agents with the coordinator"""
        await self.coordinator.register_agent("APIGatewayAgent", self.api_gateway)
        await self.coordinator.register_agent("DatabaseSyncAgent", self.database_sync)
        await self.coordinator.register_agent("UISyncAgent", self.ui_sync)
        await self.coordinator.register_agent("RealtimeUpdateAgent", self.realtime_update)
        await self.coordinator.register_agent("StudioBridgeAgent", self.studio_bridge)
        await self.coordinator.register_agent("SchemaValidatorAgent", self.schema_validator)

    async def setup_environment(self):
        """Set up the integration environment"""
        logger.info("Setting up integration environment...")

        # 1. Register schemas for each platform
        await self._register_schemas()

        # 2. Set up API endpoints
        await self._setup_api_endpoints()

        # 3. Initialize Pusher for real-time updates
        await self._initialize_realtime()

        # 4. Register UI components
        await self._register_ui_components()

        # 5. Establish Roblox Studio connection
        await self._establish_studio_connection()

        logger.info("Environment setup complete")

    async def _register_schemas(self):
        """Register schemas for data validation"""
        # Educational content schema for backend
        backend_schema = {
            "type": "object",
            "properties": {
                "content_id": {"type": "string"},
                "title": {"type": "string"},
                "description": {"type": "string"},
                "grade_level": {"type": "integer"},
                "subject": {"type": "string"},
                "learning_objectives": {
                    "type": "array",
                    "items": {"type": "string"}
                },
                "interactive_elements": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "type": {"type": "string"},
                            "data": {"type": "object"}
                        }
                    }
                },
                "created_at": {"type": "string", "format": "date-time"},
                "updated_at": {"type": "string", "format": "date-time"}
            },
            "required": ["content_id", "title", "grade_level", "subject"]
        }

        await self.schema_validator.register_schema(
            schema_name="educational_content",
            schema_type=SchemaType.JSON_SCHEMA,
            definition=backend_schema,
            platform=IntegrationPlatform.BACKEND,
            version="1.0.0"
        )

        # Frontend schema (camelCase)
        frontend_schema = {
            "type": "object",
            "properties": {
                "contentId": {"type": "string"},
                "title": {"type": "string"},
                "description": {"type": "string"},
                "gradeLevel": {"type": "number"},
                "subject": {"type": "string"},
                "learningObjectives": {
                    "type": "array",
                    "items": {"type": "string"}
                },
                "interactiveElements": {"type": "array"},
                "createdAt": {"type": "string"},
                "updatedAt": {"type": "string"}
            },
            "required": ["contentId", "title", "gradeLevel", "subject"]
        }

        await self.schema_validator.register_schema(
            schema_name="educational_content",
            schema_type=SchemaType.JSON_SCHEMA,
            definition=frontend_schema,
            platform=IntegrationPlatform.FRONTEND,
            version="1.0.0"
        )

        logger.info("Schemas registered for all platforms")

    async def _setup_api_endpoints(self):
        """Set up API endpoints for content management"""
        # Register content endpoints
        endpoints = [
            APIEndpoint(
                path="/content",
                method="GET",
                version=APIVersion.V1,
                description="Get all educational content",
                tags=["content"],
                rate_limit=100
            ),
            APIEndpoint(
                path="/content/{content_id}",
                method="GET",
                version=APIVersion.V1,
                description="Get specific content by ID",
                tags=["content"],
                rate_limit=200
            ),
            APIEndpoint(
                path="/content",
                method="POST",
                version=APIVersion.V1,
                description="Create new educational content",
                tags=["content"],
                rate_limit=50,
                authentication_required=True,
                roles_allowed=["teacher", "admin"]
            ),
            APIEndpoint(
                path="/content/{content_id}/deploy",
                method="POST",
                version=APIVersion.V1,
                description="Deploy content to Roblox",
                tags=["content", "deployment"],
                rate_limit=10,
                authentication_required=True,
                roles_allowed=["admin"]
            )
        ]

        for endpoint in endpoints:
            await self.api_gateway.register_endpoint(endpoint)

        logger.info(f"Registered {len(endpoints)} API endpoints")

    async def _initialize_realtime(self):
        """Initialize real-time communication"""
        # Initialize Pusher (using test credentials)
        await self.realtime_update.initialize_pusher(
            app_id="test_app_id",
            key="test_key",
            secret="test_secret",
            cluster="us2"
        )

        # Create channels for different platforms
        channels = [
            ("content-updates", ChannelType.PUBLIC),
            ("deployment-status", ChannelType.PRIVATE),
            ("studio-sync", ChannelType.PRESENCE)
        ]

        for channel_name, channel_type in channels:
            await self.realtime_update.subscribe_channel(
                channel_name=channel_name,
                channel_type=channel_type
            )

        logger.info("Real-time channels initialized")

    async def _register_ui_components(self):
        """Register UI components for synchronization"""
        # Register dashboard components
        components = [
            {
                "id": "content_table",
                "type": ComponentType.TABLE,
                "path": "/dashboard/content",
                "subscriptions": ["content-updates"],
                "strategy": UIUpdateStrategy.BATCHED
            },
            {
                "id": "content_form",
                "type": ComponentType.FORM,
                "path": "/dashboard/content/new",
                "subscriptions": ["validation-errors"],
                "strategy": UIUpdateStrategy.IMMEDIATE
            },
            {
                "id": "deployment_status",
                "type": ComponentType.CARD,
                "path": "/dashboard/deployment",
                "subscriptions": ["deployment-status"],
                "strategy": UIUpdateStrategy.OPTIMISTIC
            },
            {
                "id": "analytics_chart",
                "type": ComponentType.CHART,
                "path": "/dashboard/analytics",
                "subscriptions": ["content-analytics"],
                "strategy": UIUpdateStrategy.THROTTLED
            }
        ]

        for comp in components:
            await self.ui_sync.register_component(
                component_id=comp["id"],
                component_type=comp["type"],
                path=comp["path"],
                subscriptions=comp["subscriptions"],
                update_strategy=comp["strategy"]
            )

        logger.info(f"Registered {len(components)} UI components")

    async def _establish_studio_connection(self):
        """Establish connection with Roblox Studio"""
        result = await self.studio_bridge.establish_studio_connection(
            session_id="session_001",
            user_id="teacher_123",
            place_id="1234567890",
            universe_id="8505376973",
            connection_type=StudioConnectionType.HTTP_PLUGIN,
            plugin_version="2.0.0"
        )

        if result.success:
            logger.info("Roblox Studio connection established")
        else:
            logger.error(f"Failed to connect to Studio: {result.error}")

    async def deploy_educational_content(
        self,
        content: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Deploy educational content across all platforms

        This is the main workflow that coordinates all agents.
        """
        logger.info(f"Starting deployment for content: {content.get('title')}")

        # Create workflow in coordinator
        workflow = await self.coordinator.create_workflow(
            name=f"Deploy Content: {content.get('title')}",
            description="Complete educational content deployment",
            custom_tasks=[
                # 1. Validate content schema
                {
                    "type": "validate_content",
                    "agent": "SchemaValidatorAgent",
                    "platform": "BACKEND",
                    "priority": "HIGH",
                    "parameters": {
                        "data": content,
                        "schema_id": "backend_educational_content_1.0.0",
                        "level": "NORMAL"
                    },
                    "dependencies": []
                },
                # 2. Store in database
                {
                    "type": "store_database",
                    "agent": "DatabaseSyncAgent",
                    "platform": "DATABASE",
                    "priority": "HIGH",
                    "parameters": {
                        "table": "educational_content",
                        "primary_key": content["content_id"],
                        "data": content
                    },
                    "dependencies": ["custom_task_workflow_test_0"]
                },
                # 3. Sync to cache
                {
                    "type": "sync_cache",
                    "agent": "DatabaseSyncAgent",
                    "platform": "CACHE",
                    "priority": "MEDIUM",
                    "parameters": {
                        "table": "educational_content",
                        "primary_key": content["content_id"],
                        "data": content,
                        "ttl": 3600
                    },
                    "dependencies": ["custom_task_workflow_test_1"]
                },
                # 4. Transform for frontend
                {
                    "type": "transform_frontend",
                    "agent": "SchemaValidatorAgent",
                    "platform": "FRONTEND",
                    "priority": "MEDIUM",
                    "parameters": {
                        "data": content,
                        "source_schema": "backend_educational_content_1.0.0",
                        "target_schema": "frontend_educational_content_1.0.0"
                    },
                    "dependencies": ["custom_task_workflow_test_2"]
                },
                # 5. Update UI components
                {
                    "type": "update_ui",
                    "agent": "UISyncAgent",
                    "platform": "FRONTEND",
                    "priority": "MEDIUM",
                    "parameters": {
                        "component_id": "content_table",
                        "changes": {"new_content": content}
                    },
                    "dependencies": ["custom_task_workflow_test_3"]
                },
                # 6. Broadcast real-time update
                {
                    "type": "broadcast_update",
                    "agent": "RealtimeUpdateAgent",
                    "platform": "MESSAGING",
                    "priority": "LOW",
                    "parameters": {
                        "channel": "content-updates",
                        "event": "content_deployed",
                        "data": {"content_id": content["content_id"]}
                    },
                    "dependencies": ["custom_task_workflow_test_4"]
                },
                # 7. Deploy to Roblox
                {
                    "type": "deploy_roblox",
                    "agent": "StudioBridgeAgent",
                    "platform": "ROBLOX",
                    "priority": "HIGH",
                    "parameters": {
                        "session_id": "session_001",
                        "script_name": f"Content_{content['content_id']}",
                        "script_type": "ModuleScript",
                        "content": self._generate_roblox_script(content)
                    },
                    "dependencies": ["custom_task_workflow_test_5"]
                }
            ]
        )

        # Execute workflow
        result = await self.coordinator.execute_workflow(workflow.workflow_id)

        if result.success:
            logger.info(f"Content deployed successfully in {result.execution_time:.2f} seconds")

            # Get final status
            status = await self.coordinator.get_workflow_status(workflow.workflow_id)

            return {
                "success": True,
                "workflow_id": workflow.workflow_id,
                "execution_time": result.execution_time,
                "tasks_completed": status["task_summary"]["completed"],
                "deployment_status": "completed"
            }
        else:
            logger.error(f"Deployment failed: {result.error}")
            return {
                "success": False,
                "error": result.error,
                "workflow_id": workflow.workflow_id
            }

    def _generate_roblox_script(self, content: Dict[str, Any]) -> str:
        """Generate Roblox Lua script from content"""
        script = f"""
-- Educational Content: {content['title']}
-- Generated by ToolboxAI Integration System

local Content = {{}}

Content.id = "{content['content_id']}"
Content.title = "{content['title']}"
Content.description = "{content.get('description', '')}"
Content.gradeLevel = {content['grade_level']}
Content.subject = "{content['subject']}"

Content.learningObjectives = {{
"""
        for objective in content.get('learning_objectives', []):
            script += f'    "{objective}",\n'
        script += "}\n\n"

        script += """
Content.interactiveElements = {}

function Content:Initialize()
    print("Initializing educational content: " .. self.title)
    -- Setup interactive elements
end

function Content:GetNextActivity()
    -- Return next learning activity
end

function Content:CheckProgress(player)
    -- Check player's progress
end

return Content
"""
        return script

    async def monitor_deployment(self, workflow_id: str):
        """Monitor ongoing deployment"""
        while True:
            status = await self.coordinator.get_workflow_status(workflow_id)

            # Broadcast status update
            await self.realtime_update.broadcast_event(
                channel_name="deployment-status",
                event_name="status_update",
                data=status
            )

            # Update UI
            await self.ui_sync.update_component_state(
                component_id="deployment_status",
                state_changes={
                    "status": status["status"],
                    "progress": status["task_summary"]
                }
            )

            if status["status"] in ["completed", "failed", "cancelled"]:
                break

            await asyncio.sleep(1)  # Check every second


async def main():
    """Main execution function"""
    logging.basicConfig(level=logging.INFO)

    # Initialize workflow
    workflow = EducationalContentWorkflow()

    # Set up environment
    await workflow.setup_environment()

    # Example educational content
    content = {
        "content_id": "edu_math_001",
        "title": "Introduction to Fractions",
        "description": "Learn the basics of fractions through interactive games",
        "grade_level": 5,
        "subject": "Mathematics",
        "learning_objectives": [
            "Understand what fractions represent",
            "Identify numerator and denominator",
            "Compare simple fractions",
            "Add and subtract fractions with same denominator"
        ],
        "interactive_elements": [
            {
                "type": "quiz",
                "data": {
                    "questions": 10,
                    "difficulty": "medium"
                }
            },
            {
                "type": "game",
                "data": {
                    "name": "Fraction Pizza",
                    "levels": 5
                }
            }
        ],
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat()
    }

    # Deploy content
    deployment_result = await workflow.deploy_educational_content(content)

    if deployment_result["success"]:
        print(f"✅ Content deployed successfully!")
        print(f"   Workflow ID: {deployment_result['workflow_id']}")
        print(f"   Execution time: {deployment_result['execution_time']:.2f} seconds")
        print(f"   Tasks completed: {deployment_result['tasks_completed']}")

        # Monitor deployment
        await workflow.monitor_deployment(deployment_result["workflow_id"])
    else:
        print(f"❌ Deployment failed: {deployment_result['error']}")


if __name__ == "__main__":
    asyncio.run(main())