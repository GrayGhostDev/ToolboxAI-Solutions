"""
Enhanced Content Generation API Client Example

Demonstrates how to use the enhanced content generation API endpoints
including authentication, content generation, validation, and real-time updates.

Features:
- JWT authentication
- Content generation pipeline
- Real-time progress tracking via WebSocket and Pusher
- Content validation
- Personalization
- Error handling and retry logic

Author: ToolboxAI Team
Created: 2025-09-19
Version: 2.0.0
"""

import asyncio
import json
import logging
import time
import websockets
from datetime import datetime
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

import aiohttp
import pusher


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class APIConfig:
    """Configuration for the API client"""
    base_url: str = "http://127.0.0.1:8008"
    api_version: str = "v1"
    jwt_token: Optional[str] = None
    pusher_key: Optional[str] = None
    pusher_cluster: Optional[str] = None
    timeout: int = 30


class EnhancedContentAPIClient:
    """
    Client for the Enhanced Content Generation API

    Provides high-level interface for content generation, validation,
    and real-time progress tracking.
    """

    def __init__(self, config: APIConfig):
        self.config = config
        self.session: Optional[aiohttp.ClientSession] = None
        self.pusher_client: Optional[pusher.Pusher] = None
        self.websocket_connections: Dict[str, websockets.WebSocketServerProtocol] = {}

        # Initialize Pusher client if credentials provided
        if config.pusher_key and config.pusher_cluster:
            self.pusher_client = pusher.Pusher(
                app_id='your-app-id',  # Replace with actual app ID
                key=config.pusher_key,
                secret='your-secret',  # Replace with actual secret
                cluster=config.pusher_cluster,
                ssl=True
            )

    async def __aenter__(self):
        """Async context manager entry"""
        await self._ensure_session()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()

    async def _ensure_session(self):
        """Ensure aiohttp session is available"""
        if self.session is None or self.session.closed:
            headers = {}
            if self.config.jwt_token:
                headers["Authorization"] = f"Bearer {self.config.jwt_token}"

            timeout = aiohttp.ClientTimeout(total=self.config.timeout)
            self.session = aiohttp.ClientSession(
                headers=headers,
                timeout=timeout
            )

    async def close(self):
        """Close all connections"""
        if self.session and not self.session.closed:
            await self.session.close()

        # Close WebSocket connections
        for ws in self.websocket_connections.values():
            if not ws.closed:
                await ws.close()
        self.websocket_connections.clear()

    def _get_api_url(self, endpoint: str) -> str:
        """Get full API URL for endpoint"""
        return f"{self.config.base_url}/api/{self.config.api_version}{endpoint}"

    async def authenticate(self, username: str, password: str) -> Dict[str, Any]:
        """
        Authenticate with the API and get JWT token

        Args:
            username: User's username
            password: User's password

        Returns:
            Authentication response with token
        """
        await self._ensure_session()

        auth_data = {
            "username": username,
            "password": password
        }

        async with self.session.post(
            self._get_api_url("/auth/login"),
            json=auth_data
        ) as response:
            if response.status == 200:
                data = await response.json()
                self.config.jwt_token = data.get("access_token")

                # Update session headers
                await self.close()
                await self._ensure_session()

                logger.info("Authentication successful")
                return data
            else:
                error_text = await response.text()
                raise Exception(f"Authentication failed: {error_text}")

    async def generate_content(
        self,
        subject: str,
        grade_level: str,
        content_type: str,
        learning_objectives: List[str],
        difficulty_level: str = "medium",
        duration_minutes: int = 30,
        personalization_enabled: bool = True,
        roblox_requirements: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Initiate enhanced content generation

        Args:
            subject: Subject area (e.g., "Mathematics", "Science")
            grade_level: Target grade level (e.g., "K-2", "6-8")
            content_type: Type of content ("lesson", "quiz", etc.)
            learning_objectives: List of learning objectives
            difficulty_level: Difficulty level ("easy", "medium", "hard")
            duration_minutes: Expected duration in minutes
            personalization_enabled: Whether to apply personalization
            roblox_requirements: Roblox-specific requirements

        Returns:
            Generation response with pipeline_id and status
        """
        await self._ensure_session()

        request_data = {
            "subject": subject,
            "grade_level": grade_level,
            "content_type": content_type,
            "learning_objectives": learning_objectives,
            "difficulty_level": difficulty_level,
            "duration_minutes": duration_minutes,
            "personalization_enabled": personalization_enabled,
            "roblox_requirements": roblox_requirements or {}
        }

        logger.info(f"Initiating content generation for {subject} - {content_type}")

        async with self.session.post(
            self._get_api_url("/content/generate"),
            json=request_data
        ) as response:
            if response.status == 200:
                data = await response.json()
                logger.info(f"Content generation started: {data['pipeline_id']}")
                return data
            elif response.status == 429:
                raise Exception("Rate limit exceeded. Please wait before retrying.")
            else:
                error_text = await response.text()
                raise Exception(f"Content generation failed: {error_text}")

    async def get_generation_status(self, pipeline_id: str) -> Dict[str, Any]:
        """
        Get the current status of a generation pipeline

        Args:
            pipeline_id: ID of the pipeline to check

        Returns:
            Status information including progress and current stage
        """
        await self._ensure_session()

        async with self.session.get(
            self._get_api_url(f"/content/status/{pipeline_id}")
        ) as response:
            if response.status == 200:
                return await response.json()
            elif response.status == 404:
                raise Exception(f"Pipeline {pipeline_id} not found")
            elif response.status == 403:
                raise Exception("Access denied to this pipeline")
            else:
                error_text = await response.text()
                raise Exception(f"Failed to get status: {error_text}")

    async def wait_for_completion(
        self,
        pipeline_id: str,
        check_interval: int = 5,
        max_wait_time: int = 600
    ) -> Dict[str, Any]:
        """
        Wait for a generation pipeline to complete

        Args:
            pipeline_id: ID of the pipeline to wait for
            check_interval: Seconds between status checks
            max_wait_time: Maximum time to wait in seconds

        Returns:
            Final status when completed
        """
        start_time = time.time()

        logger.info(f"Waiting for pipeline {pipeline_id} to complete...")

        while time.time() - start_time < max_wait_time:
            try:
                status = await self.get_generation_status(pipeline_id)

                logger.info(
                    f"Pipeline {pipeline_id}: {status['status']} - "
                    f"{status['current_stage']} ({status['progress_percentage']:.1f}%)"
                )

                if status["status"] in ["completed", "failed"]:
                    return status

                await asyncio.sleep(check_interval)

            except Exception as e:
                logger.error(f"Error checking status: {e}")
                await asyncio.sleep(check_interval)

        raise TimeoutError(f"Pipeline {pipeline_id} did not complete within {max_wait_time} seconds")

    async def get_generated_content(
        self,
        content_id: str,
        include_validation: bool = False
    ) -> Dict[str, Any]:
        """
        Retrieve generated content by ID

        Args:
            content_id: ID of the content to retrieve
            include_validation: Whether to include validation report

        Returns:
            Generated content with scripts, assets, and metadata
        """
        await self._ensure_session()

        params = {"include_validation": include_validation} if include_validation else {}

        async with self.session.get(
            self._get_api_url(f"/content/{content_id}"),
            params=params
        ) as response:
            if response.status == 200:
                return await response.json()
            elif response.status == 404:
                raise Exception(f"Content {content_id} not found")
            elif response.status == 403:
                raise Exception("Access denied to this content")
            else:
                error_text = await response.text()
                raise Exception(f"Failed to get content: {error_text}")

    async def validate_content(
        self,
        content: Dict[str, Any],
        content_type: str,
        target_age: int = 10,
        validation_categories: Optional[List[str]] = None,
        strict_mode: bool = False
    ) -> Dict[str, Any]:
        """
        Validate content for quality, safety, and compliance

        Args:
            content: Content to validate
            content_type: Type of content being validated
            target_age: Target age for validation
            validation_categories: Specific categories to validate
            strict_mode: Whether to use strict validation rules

        Returns:
            Validation results with scores and recommendations
        """
        await self._ensure_session()

        request_data = {
            "content": content,
            "content_type": content_type,
            "target_age": target_age,
            "strict_mode": strict_mode
        }

        if validation_categories:
            request_data["validation_categories"] = validation_categories

        logger.info(f"Validating {content_type} content for age {target_age}")

        async with self.session.post(
            self._get_api_url("/content/validate"),
            json=request_data
        ) as response:
            if response.status == 200:
                data = await response.json()
                logger.info(f"Validation completed. Score: {data['overall_score']:.2f}")
                return data
            elif response.status == 429:
                raise Exception("Validation rate limit exceeded")
            else:
                error_text = await response.text()
                raise Exception(f"Content validation failed: {error_text}")

    async def get_content_history(
        self,
        page: int = 1,
        page_size: int = 20,
        content_type: Optional[str] = None,
        subject: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get user's content generation history

        Args:
            page: Page number (1-based)
            page_size: Number of items per page
            content_type: Filter by content type
            subject: Filter by subject

        Returns:
            Paginated history with metadata
        """
        await self._ensure_session()

        params = {
            "page": page,
            "page_size": page_size
        }

        if content_type:
            params["content_type"] = content_type
        if subject:
            params["subject"] = subject

        async with self.session.get(
            self._get_api_url("/content/history"),
            params=params
        ) as response:
            if response.status == 200:
                return await response.json()
            else:
                error_text = await response.text()
                raise Exception(f"Failed to get history: {error_text}")

    async def apply_personalization(
        self,
        content_id: str,
        personalization_params: Dict[str, Any],
        learning_style: Optional[str] = None,
        difficulty_preference: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Apply personalization to existing content

        Args:
            content_id: ID of content to personalize
            personalization_params: Custom personalization parameters
            learning_style: Preferred learning style
            difficulty_preference: Preferred difficulty level

        Returns:
            Personalization result
        """
        await self._ensure_session()

        request_data = {
            "content_id": content_id,
            "personalization_params": personalization_params
        }

        if learning_style:
            request_data["learning_style"] = learning_style
        if difficulty_preference:
            request_data["difficulty_preference"] = difficulty_preference

        logger.info(f"Applying personalization to content {content_id}")

        async with self.session.post(
            self._get_api_url("/content/personalize"),
            json=request_data
        ) as response:
            if response.status == 200:
                data = await response.json()
                logger.info("Personalization applied successfully")
                return data
            elif response.status == 404:
                raise Exception(f"Content {content_id} not found")
            elif response.status == 429:
                raise Exception("Personalization rate limit exceeded")
            else:
                error_text = await response.text()
                raise Exception(f"Personalization failed: {error_text}")

    async def connect_websocket(
        self,
        pipeline_id: str,
        on_update_callback: Optional[callable] = None
    ) -> websockets.WebSocketServerProtocol:
        """
        Connect to WebSocket for real-time updates

        Args:
            pipeline_id: ID of the pipeline to monitor
            on_update_callback: Callback function for updates

        Returns:
            WebSocket connection
        """
        ws_url = f"ws://127.0.0.1:8008/api/v1/content/ws/{pipeline_id}"

        try:
            websocket = await websockets.connect(ws_url)
            self.websocket_connections[pipeline_id] = websocket

            logger.info(f"WebSocket connected for pipeline {pipeline_id}")

            # Start listening for messages
            if on_update_callback:
                asyncio.create_task(
                    self._listen_websocket(websocket, on_update_callback)
                )

            return websocket

        except Exception as e:
            logger.error(f"WebSocket connection failed: {e}")
            raise

    async def _listen_websocket(
        self,
        websocket: websockets.WebSocketServerProtocol,
        callback: callable
    ):
        """Listen for WebSocket messages and call callback"""
        try:
            async for message in websocket:
                try:
                    data = json.loads(message)
                    await callback(data)
                except json.JSONDecodeError:
                    logger.warning(f"Invalid JSON received: {message}")
                except Exception as e:
                    logger.error(f"Callback error: {e}")

        except websockets.exceptions.ConnectionClosed:
            logger.info("WebSocket connection closed")
        except Exception as e:
            logger.error(f"WebSocket error: {e}")

    def subscribe_to_pusher_channel(
        self,
        channel_name: str,
        event_callback: callable
    ):
        """
        Subscribe to Pusher channel for real-time updates

        Args:
            channel_name: Name of the Pusher channel
            event_callback: Callback for channel events
        """
        if not self.pusher_client:
            raise Exception("Pusher client not configured")

        channel = self.pusher_client.subscribe(channel_name)

        # Bind to all events
        channel.bind_all(event_callback)

        logger.info(f"Subscribed to Pusher channel: {channel_name}")


# Example usage and demonstration
async def main():
    """Example usage of the Enhanced Content API Client"""

    # Configuration
    config = APIConfig(
        base_url="http://127.0.0.1:8008",
        pusher_key="your-pusher-key",  # Replace with actual key
        pusher_cluster="us2"  # Replace with actual cluster
    )

    async with EnhancedContentAPIClient(config) as client:
        try:
            # Step 1: Authenticate (optional if you have a JWT token)
            # await client.authenticate("teacher@example.com", "password123")

            # Step 2: Generate content
            logger.info("=== Starting Content Generation ===")
            generation_result = await client.generate_content(
                subject="Mathematics",
                grade_level="6-8",
                content_type="lesson",
                learning_objectives=[
                    "Understand basic algebraic concepts",
                    "Solve simple linear equations",
                    "Apply algebra to real-world problems"
                ],
                difficulty_level="medium",
                duration_minutes=45,
                personalization_enabled=True,
                roblox_requirements={
                    "environment_type": "classroom",
                    "max_players": 25,
                    "required_assets": ["whiteboard", "calculator"]
                }
            )

            pipeline_id = generation_result["pipeline_id"]
            pusher_channel = generation_result.get("pusher_channel")

            # Step 3: Set up real-time monitoring
            logger.info("=== Setting up Real-time Monitoring ===")

            # WebSocket callback for updates
            async def on_websocket_update(data):
                logger.info(f"WebSocket Update: {data.get('type')} - {data.get('message', '')}")

            # Connect WebSocket
            await client.connect_websocket(pipeline_id, on_websocket_update)

            # Pusher callback (if available)
            def on_pusher_event(event_name, data):
                logger.info(f"Pusher Event [{event_name}]: {data}")

            if pusher_channel and client.pusher_client:
                client.subscribe_to_pusher_channel(pusher_channel, on_pusher_event)

            # Step 4: Wait for completion
            logger.info("=== Waiting for Completion ===")
            final_status = await client.wait_for_completion(
                pipeline_id,
                check_interval=3,
                max_wait_time=300
            )

            if final_status["status"] == "completed":
                logger.info("Content generation completed successfully!")

                # Step 5: Retrieve generated content
                logger.info("=== Retrieving Generated Content ===")
                content_id = final_status.get("content_id")
                if content_id:
                    content = await client.get_generated_content(
                        content_id,
                        include_validation=True
                    )

                    logger.info(f"Generated Content:")
                    logger.info(f"  Title: {content.get('enhanced_content', {}).get('title', 'N/A')}")
                    logger.info(f"  Scripts: {len(content.get('generated_scripts', []))}")
                    logger.info(f"  Assets: {len(content.get('generated_assets', []))}")
                    logger.info(f"  Quality Score: {content.get('quality_score', 0):.2f}")

                    # Step 6: Validate content (optional)
                    logger.info("=== Running Additional Validation ===")
                    validation_result = await client.validate_content(
                        content=content["enhanced_content"],
                        content_type=content["content_type"],
                        target_age=12
                    )

                    logger.info(f"Validation Results:")
                    logger.info(f"  Overall Score: {validation_result['overall_score']:.2f}")
                    logger.info(f"  Compliant: {validation_result['compliant']}")
                    logger.info(f"  Issues: {validation_result['issues_count']}")
                    logger.info(f"  Recommendations: {len(validation_result['recommendations'])}")

                    # Step 7: Apply personalization (optional)
                    if content.get("personalization_applied", False):
                        logger.info("=== Applying Additional Personalization ===")
                        personalization_result = await client.apply_personalization(
                            content_id=content_id,
                            personalization_params={
                                "visual_style": "colorful",
                                "interaction_frequency": "high",
                                "difficulty_adjustment": "adaptive"
                            },
                            learning_style="kinesthetic",
                            difficulty_preference="challenging"
                        )

                        logger.info("Additional personalization applied successfully")

                    # Step 8: Get content history
                    logger.info("=== Getting Content History ===")
                    history = await client.get_content_history(
                        page=1,
                        page_size=10,
                        content_type="lesson",
                        subject="Mathematics"
                    )

                    logger.info(f"Content History: {history['total_count']} items")
                    for item in history['items'][:3]:  # Show first 3
                        logger.info(f"  - {item.get('subject')} {item.get('content_type')}: {item.get('status')}")

            else:
                logger.error(f"Content generation failed: {final_status}")
                if final_status.get("errors"):
                    for error in final_status["errors"]:
                        logger.error(f"  Error: {error}")

        except Exception as e:
            logger.error(f"Example failed: {e}")
            raise

        finally:
            logger.info("=== Cleaning up ===")
            # Cleanup is handled by the context manager


if __name__ == "__main__":
    asyncio.run(main())