"""
MCP Server for Educational Content Generation
Exposes ContentGenerationAgent via MCP protocol
"""

import sys
import json
import asyncio
import logging
from typing import Dict, Any, Optional

# Add parent directory to path for imports
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../..'))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EducationalContentMCPServer:
    """MCP Server wrapper for Educational Content Generation"""

    def __init__(self):
        # Lazy import to avoid initialization issues
        self.agent = None
        self._agent_initialized = False
        self.methods = {
            "generate_content": self.handle_generate_content,
            "generate_quiz": self.handle_generate_quiz,
            "generate_lesson": self.handle_generate_lesson,
            "generate_activity": self.handle_generate_activity,
            "health": self.handle_health,
            "capabilities": self.handle_capabilities,
        }

    def _ensure_agent_initialized(self):
        """Initialize the agent on first use to avoid import issues"""
        if not self._agent_initialized:
            try:
                # Import only when needed
                from apps.backend.agents.agent_classes import ContentGenerationAgent
                self.agent = ContentGenerationAgent()
                self._agent_initialized = True
                logger.info("ContentGenerationAgent initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize ContentGenerationAgent: {e}")
                # Create a mock agent for fallback
                self.agent = None
                raise RuntimeError(f"Agent initialization failed: {e}")

    async def handle_generate_content(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Generate educational content"""
        try:
            self._ensure_agent_initialized()

            subject = params.get("subject", "General")
            grade_level = params.get("grade_level", 5)
            objectives = params.get("objectives", [])
            include_assessment = params.get("include_assessment", True)

            result = await self.agent.generate_content(
                subject=subject,
                grade_level=grade_level,
                objectives=objectives,
                include_assessment=include_assessment
            )

            return {
                "status": "success",
                "content": result
            }
        except Exception as e:
            logger.error(f"Error generating content: {e}")
            return {
                "status": "error",
                "error": str(e)
            }

    async def handle_generate_quiz(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a quiz for educational content"""
        try:
            self._ensure_agent_initialized()

            topic = params.get("topic", "General Knowledge")
            num_questions = params.get("num_questions", 5)
            difficulty = params.get("difficulty", "medium")

            # Use the agent's quiz generation capability
            if hasattr(self.agent, 'generate_quiz'):
                result = await self.agent.generate_quiz(
                    topic=topic,
                    num_questions=num_questions,
                    difficulty=difficulty
                )
            else:
                # Fallback to content generation with quiz focus
                result = await self.agent.generate_content(
                    subject=topic,
                    grade_level=5,
                    objectives=[f"Create {num_questions} quiz questions"],
                    include_assessment=True
                )

            return {
                "status": "success",
                "quiz": result
            }
        except Exception as e:
            logger.error(f"Error generating quiz: {e}")
            return {
                "status": "error",
                "error": str(e)
            }

    async def handle_generate_lesson(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a complete lesson plan"""
        try:
            self._ensure_agent_initialized()

            topic = params.get("topic", "Science")
            grade = params.get("grade", 5)
            duration = params.get("duration", 45)  # minutes

            # Use the content generation with lesson template
            objectives = [
                f"Create a {duration}-minute lesson plan",
                f"Include introduction, main content, and conclusion",
                f"Add interactive elements"
            ]

            result = await self.agent.generate_content(
                subject=topic,
                grade_level=grade,
                objectives=objectives,
                include_assessment=True
            )

            return {
                "status": "success",
                "lesson": result
            }
        except Exception as e:
            logger.error(f"Error generating lesson: {e}")
            return {
                "status": "error",
                "error": str(e)
            }

    async def handle_generate_activity(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Generate an educational activity"""
        try:
            self._ensure_agent_initialized()

            topic = params.get("topic", "Math")
            age = params.get("age", 10)
            activity_type = params.get("type", "interactive")

            # Use the content generation with activity focus
            result = await self.agent.generate_content(
                subject=topic,
                grade_level=age - 5,  # Approximate grade from age
                objectives=[f"Create {activity_type} activity for {age} year olds"],
                include_assessment=False
            )

            return {
                "status": "success",
                "activity": result
            }
        except Exception as e:
            logger.error(f"Error generating activity: {e}")
            return {
                "status": "error",
                "error": str(e)
            }

    async def handle_health(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Health check endpoint"""
        # Check if agent can be initialized without actually doing it
        agent_available = self._agent_initialized or self._check_agent_availability()
        return {
            "status": "healthy",
            "service": "educational_content",
            "agent_status": "available" if agent_available else "not_initialized"
        }

    def _check_agent_availability(self) -> bool:
        """Check if agent can be initialized without actually doing it"""
        try:
            import apps.backend.agents.agent_classes
            return True
        except Exception:
            return False

    async def handle_capabilities(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Return server capabilities"""
        return {
            "capabilities": [
                "generate_content",
                "generate_quiz",
                "generate_lesson",
                "generate_activity"
            ],
            "supported_subjects": [
                "Math", "Science", "History", "English",
                "Geography", "Art", "Music", "Physical Education"
            ],
            "grade_levels": list(range(1, 13)),
            "content_types": ["lesson", "quiz", "activity", "assessment"]
        }

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
        logger.info("Educational Content MCP Server started (stdio mode)")

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
    server = EducationalContentMCPServer()

    # Check if running in stdio mode (default for MCP)
    if len(sys.argv) > 1 and sys.argv[1] == "--websocket":
        # WebSocket mode not implemented yet
        logger.error("WebSocket mode not yet implemented")
        sys.exit(1)
    else:
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