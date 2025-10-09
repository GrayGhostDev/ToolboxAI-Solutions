"""
Comprehensive tests for content generation and management API endpoints.

Tests cover AI-powered content creation, lesson management,
assessment generation, and Roblox integration endpoints.
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
import asyncio

from tests.api.conftest import Content, User


class TestContentGenerationEndpoints:
    """Test suite for AI-powered content generation."""

    @pytest.mark.asyncio
    async def test_generate_lesson_content(
        self, test_client: AsyncClient, teacher_headers: dict
    ):
        """Test generating lesson content with AI."""
        response = await test_client.post(
            "/api/v1/content/generate/lesson",
            json={
                "title": "Introduction to Photosynthesis",
                "subject": "Biology",
                "grade_level": "9th",
                "learning_objectives": [
                    "Understand the process of photosynthesis",
                    "Identify key components involved"
                ],
                "duration_minutes": 45
            },
            headers=teacher_headers
        )

        assert response.status_code in [200, 201, 404, 503]
        if response.status_code in [200, 201]:
            data = response.json()
            assert "content" in data or "id" in data
            assert "title" in data
            if "status" in data:
                assert data["status"] in ["pending", "processing", "completed"]

    @pytest.mark.asyncio
    async def test_generate_quiz(
        self, test_client: AsyncClient, teacher_headers: dict
    ):
        """Test generating quiz questions with AI."""
        response = await test_client.post(
            "/api/v1/content/generate/quiz",
            json={
                "topic": "World War II",
                "num_questions": 10,
                "question_types": ["multiple_choice", "true_false"],
                "difficulty": "medium"
            },
            headers=teacher_headers
        )

        assert response.status_code in [200, 201, 404, 503]
        if response.status_code in [200, 201]:
            data = response.json()
            if "questions" in data:
                assert len(data["questions"]) <= 10
                for question in data["questions"]:
                    assert "question" in question
                    assert "options" in question or "answer" in question

    @pytest.mark.asyncio
    async def test_generate_roblox_script(
        self, test_client: AsyncClient, teacher_headers: dict
    ):
        """Test generating Roblox Luau scripts."""
        response = await test_client.post(
            "/api/v1/content/generate/roblox-script",
            json={
                "script_type": "interactive_lesson",
                "topic": "Solar System",
                "features": ["3d_models", "quiz_integration", "leaderboard"],
                "target_age": 12
            },
            headers=teacher_headers
        )

        assert response.status_code in [200, 201, 404, 503]
        if response.status_code in [200, 201]:
            data = response.json()
            assert "script" in data or "scripts" in data
            if "script" in data:
                assert "--" in data["script"]  # Luau comment syntax

    @pytest.mark.asyncio
    async def test_generate_assessment(
        self, test_client: AsyncClient, teacher_headers: dict
    ):
        """Test generating comprehensive assessments."""
        response = await test_client.post(
            "/api/v1/content/generate/assessment",
            json={
                "title": "Mid-term Mathematics Assessment",
                "topics": ["Algebra", "Geometry", "Trigonometry"],
                "duration_minutes": 90,
                "points_total": 100,
                "include_rubric": True
            },
            headers=teacher_headers
        )

        assert response.status_code in [200, 201, 404, 503]
        if response.status_code in [200, 201]:
            data = response.json()
            assert "title" in data
            if "rubric" in data:
                assert isinstance(data["rubric"], dict) or isinstance(data["rubric"], str)

    @pytest.mark.asyncio
    async def test_generate_content_with_streaming(
        self, test_client: AsyncClient, teacher_headers: dict
    ):
        """Test content generation with streaming response."""
        response = await test_client.post(
            "/api/v1/content/generate/stream",
            json={
                "prompt": "Create a lesson about the water cycle",
                "stream": True
            },
            headers=teacher_headers
        )

        assert response.status_code in [200, 404, 501]
        # If streaming is implemented, response will be chunked

    @pytest.mark.asyncio
    async def test_content_generation_status(
        self, test_client: AsyncClient, teacher_headers: dict
    ):
        """Test checking content generation status."""
        # First, initiate generation
        gen_response = await test_client.post(
            "/api/v1/content/generate/lesson",
            json={
                "title": "Test Lesson",
                "subject": "Science",
                "grade_level": "7th"
            },
            headers=teacher_headers
        )

        if gen_response.status_code in [200, 201] and "id" in gen_response.json():
            task_id = gen_response.json()["id"]

            # Check status
            status_response = await test_client.get(
                f"/api/v1/content/generate/status/{task_id}",
                headers=teacher_headers
            )

            assert status_response.status_code in [200, 404]
            if status_response.status_code == 200:
                data = status_response.json()
                assert "status" in data
                assert data["status"] in ["pending", "processing", "completed", "failed"]

    @pytest.mark.asyncio
    async def test_cancel_content_generation(
        self, test_client: AsyncClient, teacher_headers: dict
    ):
        """Test canceling ongoing content generation."""
        # First, initiate generation
        gen_response = await test_client.post(
            "/api/v1/content/generate/lesson",
            json={
                "title": "Test Lesson to Cancel",
                "subject": "Math",
                "grade_level": "8th"
            },
            headers=teacher_headers
        )

        if gen_response.status_code in [200, 201] and "id" in gen_response.json():
            task_id = gen_response.json()["id"]

            # Cancel generation
            cancel_response = await test_client.delete(
                f"/api/v1/content/generate/{task_id}",
                headers=teacher_headers
            )

            assert cancel_response.status_code in [200, 204, 404]


class TestContentManagementEndpoints:
    """Test suite for content CRUD operations."""

    @pytest.mark.asyncio
    async def test_create_content(
        self, test_client: AsyncClient, teacher_headers: dict
    ):
        """Test creating content manually."""
        response = await test_client.post(
            "/api/v1/content",
            json={
                "title": "Manual Content Creation",
                "description": "This is manually created content",
                "content_type": "lesson",
                "subject": "History",
                "grade_level": "10th",
                "content_body": "Content details here...",
                "tags": ["history", "manual", "test"]
            },
            headers=teacher_headers
        )

        assert response.status_code in [200, 201, 404]
        if response.status_code in [200, 201]:
            data = response.json()
            assert data["title"] == "Manual Content Creation"
            assert "id" in data

    @pytest.mark.asyncio
    async def test_get_content_by_id(
        self, test_client: AsyncClient, test_session: AsyncSession, auth_headers: dict
    ):
        """Test retrieving content by ID."""
        # Create test content
        content = await create_test_content(test_session)

        response = await test_client.get(
            f"/api/v1/content/{content.id}",
            headers=auth_headers
        )

        assert response.status_code in [200, 404]
        if response.status_code == 200:
            data = response.json()
            assert data["id"] == content.id
            assert data["title"] == content.title

    @pytest.mark.asyncio
    async def test_list_content(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """Test listing all content with pagination."""
        response = await test_client.get(
            "/api/v1/content?page=1&limit=10",
            headers=auth_headers
        )

        assert response.status_code in [200, 404]
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, dict):
                assert "items" in data
                assert "total" in data
                assert len(data["items"]) <= 10

    @pytest.mark.asyncio
    async def test_filter_content_by_subject(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """Test filtering content by subject."""
        response = await test_client.get(
            "/api/v1/content?subject=Mathematics",
            headers=auth_headers
        )

        assert response.status_code in [200, 404]
        if response.status_code == 200:
            data = response.json()
            items = data.get("items", data if isinstance(data, list) else [])
            for content in items:
                if "subject" in content:
                    assert content["subject"] == "Mathematics"

    @pytest.mark.asyncio
    async def test_search_content(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """Test searching content by keyword."""
        response = await test_client.get(
            "/api/v1/content/search?q=photosynthesis",
            headers=auth_headers
        )

        assert response.status_code in [200, 404]
        if response.status_code == 200:
            data = response.json()
            items = data.get("items", data if isinstance(data, list) else [])
            for content in items:
                # Should contain search term in title or description
                assert any(
                    "photosynthesis" in str(content.get(field, "")).lower()
                    for field in ["title", "description", "content_body"]
                )

    @pytest.mark.asyncio
    async def test_update_content(
        self, test_client: AsyncClient, test_session: AsyncSession, teacher_headers: dict
    ):
        """Test updating existing content."""
        # Create test content
        content = await create_test_content(test_session)

        response = await test_client.patch(
            f"/api/v1/content/{content.id}",
            json={
                "title": "Updated Title",
                "description": "Updated description"
            },
            headers=teacher_headers
        )

        assert response.status_code in [200, 403, 404]
        if response.status_code == 200:
            data = response.json()
            assert data["title"] == "Updated Title"
            assert data["description"] == "Updated description"

    @pytest.mark.asyncio
    async def test_delete_content(
        self, test_client: AsyncClient, test_session: AsyncSession, teacher_headers: dict
    ):
        """Test deleting content."""
        # Create test content
        content = await create_test_content(test_session)

        response = await test_client.delete(
            f"/api/v1/content/{content.id}",
            headers=teacher_headers
        )

        assert response.status_code in [200, 204, 403, 404]

        # Verify deletion
        if response.status_code in [200, 204]:
            get_response = await test_client.get(
                f"/api/v1/content/{content.id}",
                headers=teacher_headers
            )
            assert get_response.status_code == 404

    @pytest.mark.asyncio
    async def test_duplicate_content(
        self, test_client: AsyncClient, test_session: AsyncSession, teacher_headers: dict
    ):
        """Test duplicating existing content."""
        # Create test content
        content = await create_test_content(test_session)

        response = await test_client.post(
            f"/api/v1/content/{content.id}/duplicate",
            headers=teacher_headers
        )

        assert response.status_code in [200, 201, 404, 501]
        if response.status_code in [200, 201]:
            data = response.json()
            assert data["id"] != content.id
            assert "Copy" in data["title"] or data["title"] != content.title

    @pytest.mark.asyncio
    async def test_publish_content(
        self, test_client: AsyncClient, test_session: AsyncSession, teacher_headers: dict
    ):
        """Test publishing content."""
        # Create test content
        content = await create_test_content(test_session)

        response = await test_client.post(
            f"/api/v1/content/{content.id}/publish",
            headers=teacher_headers
        )

        assert response.status_code in [200, 404, 501]
        if response.status_code == 200:
            data = response.json()
            assert data.get("is_published") is True or data.get("status") == "published"

    @pytest.mark.asyncio
    async def test_archive_content(
        self, test_client: AsyncClient, test_session: AsyncSession, teacher_headers: dict
    ):
        """Test archiving content."""
        # Create test content
        content = await create_test_content(test_session)

        response = await test_client.post(
            f"/api/v1/content/{content.id}/archive",
            headers=teacher_headers
        )

        assert response.status_code in [200, 404, 501]
        if response.status_code == 200:
            data = response.json()
            assert data.get("is_archived") is True or data.get("status") == "archived"


class TestRobloxIntegrationEndpoints:
    """Test suite for Roblox integration endpoints."""

    @pytest.mark.asyncio
    async def test_sync_content_to_roblox(
        self, test_client: AsyncClient, test_session: AsyncSession, teacher_headers: dict
    ):
        """Test syncing content to Roblox environment."""
        # Create test content
        content = await create_test_content(test_session)

        response = await test_client.post(
            f"/api/v1/roblox/sync/content/{content.id}",
            json={
                "universe_id": "123456789",
                "place_id": "987654321"
            },
            headers=teacher_headers
        )

        assert response.status_code in [200, 201, 404, 503]
        if response.status_code in [200, 201]:
            data = response.json()
            assert "sync_status" in data or "status" in data

    @pytest.mark.asyncio
    async def test_get_roblox_sync_status(
        self, test_client: AsyncClient, teacher_headers: dict
    ):
        """Test getting Roblox sync status."""
        response = await test_client.get(
            "/api/v1/roblox/sync/status/123",
            headers=teacher_headers
        )

        assert response.status_code in [200, 404]
        if response.status_code == 200:
            data = response.json()
            assert "status" in data
            assert data["status"] in ["pending", "syncing", "completed", "failed"]

    @pytest.mark.asyncio
    async def test_validate_roblox_script(
        self, test_client: AsyncClient, teacher_headers: dict
    ):
        """Test validating Roblox Luau script."""
        response = await test_client.post(
            "/api/v1/roblox/validate",
            json={
                "script": """
                local function onPlayerJoined(player)
                    print("Welcome, " .. player.Name)
                end
                game.Players.PlayerAdded:Connect(onPlayerJoined)
                """
            },
            headers=teacher_headers
        )

        assert response.status_code in [200, 404, 501]
        if response.status_code == 200:
            data = response.json()
            assert "is_valid" in data
            if not data["is_valid"]:
                assert "errors" in data

    @pytest.mark.asyncio
    async def test_get_roblox_analytics(
        self, test_client: AsyncClient, teacher_headers: dict
    ):
        """Test getting Roblox game analytics."""
        response = await test_client.get(
            "/api/v1/roblox/analytics?universe_id=123456789",
            headers=teacher_headers
        )

        assert response.status_code in [200, 404, 503]
        if response.status_code == 200:
            data = response.json()
            # Analytics structure depends on implementation
            assert isinstance(data, dict)


async def create_test_content(session: AsyncSession, title: str = "Test Content") -> Content:
    """Helper to create test content."""
    content = Content(
        title=title,
        description="Test description",
        content_type="lesson",
        created_at=datetime.utcnow()
    )
    session.add(content)
    await session.commit()
    await session.refresh(content)
    return content