"""
Unit Tests for Content Tags API Endpoints

Tests tag management, listing, creation, updates, and merging functionality.

Phase 1 Week 1: Authentication & user management endpoint tests
Phase B: Converted to TestClient pattern
"""

import pytest
from datetime import datetime
from uuid import uuid4, UUID
from unittest.mock import AsyncMock, Mock, patch

from fastapi import FastAPI, HTTPException, status
from fastapi.testclient import TestClient

# Import router and models
from apps.backend.api.v1.endpoints.content_tags import (
    router,
    Tag,
    TagCreateRequest,
    TagUpdateRequest,
    TagListResponse,
    TagMergeRequest,
    TagMergeResponse,
    PopularTagsResponse,
)
from apps.backend.core.security.jwt_handler import create_access_token
from tests.utils import APITestHelper


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def app():
    """Create FastAPI app with content tags router."""
    app = FastAPI()
    app.include_router(router, prefix="/tags")
    return app


@pytest.fixture
def client(app):
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def teacher_token():
    """Create teacher JWT token."""
    return create_access_token(
        data={"sub": "teacher", "role": "teacher", "user_id": 1, "id": str(uuid4())}
    )


@pytest.fixture
def teacher_headers(teacher_token):
    """Create authorization headers for teacher."""
    return {"Authorization": f"Bearer {teacher_token}"}


@pytest.fixture
def valid_tag_create_request():
    """Create valid tag creation request."""
    return {
        "name": "Mathematics",
        "description": "Math-related content",
        "color": "#FF5733",
        "category": "subject",
    }


@pytest.fixture
def valid_tag_update_request():
    """Create valid tag update request."""
    return {
        "name": "Updated Math",
        "description": "Updated description",
        "color": "#33FF57",
    }


@pytest.fixture
def valid_tag_merge_request():
    """Create valid tag merge request."""
    return {
        "source_tag_ids": [str(uuid4()), str(uuid4())],
        "target_tag_id": str(uuid4()),
        "delete_source_tags": True,
    }


# ============================================================================
# Test List Tags Endpoint
# ============================================================================


class TestListTags:
    """Test tag listing endpoint."""

    def test_list_tags_success(self, client):
        """Test successful tag listing."""
        response = client.get("/tags/")

        data = APITestHelper.assert_success_response(response)

        assert "tags" in data
        assert isinstance(data["tags"], list)
        assert "total" in data
        assert data["total"] == 0
        assert data["page"] == 1
        assert data["page_size"] == 50

    def test_list_tags_with_pagination(self, client):
        """Test tag listing with custom pagination."""
        response = client.get("/tags/?page=2&page_size=25")

        data = APITestHelper.assert_success_response(response)

        assert data["page"] == 2
        assert data["page_size"] == 25

    def test_list_tags_with_search(self, client):
        """Test tag listing with search term."""
        response = client.get("/tags/?search=math")

        data = APITestHelper.assert_success_response(response)

        assert "tags" in data

    def test_list_tags_with_category_filter(self, client):
        """Test tag listing with category filter."""
        response = client.get("/tags/?category=subject")

        data = APITestHelper.assert_success_response(response)

        assert "tags" in data

    def test_list_tags_sort_by_name(self, client):
        """Test tag listing sorted by name."""
        response = client.get("/tags/?sort_by=name&sort_order=asc")

        data = APITestHelper.assert_success_response(response)

        assert "tags" in data

    def test_list_tags_sort_by_usage_count(self, client):
        """Test tag listing sorted by usage count."""
        response = client.get("/tags/?sort_by=usage_count&sort_order=desc")

        data = APITestHelper.assert_success_response(response)

        assert "tags" in data

    def test_list_tags_sort_by_created_at(self, client):
        """Test tag listing sorted by creation date."""
        response = client.get("/tags/?sort_by=created_at&sort_order=desc")

        data = APITestHelper.assert_success_response(response)

        assert "tags" in data


# ============================================================================
# Test Create Tag Endpoint
# ============================================================================


class TestCreateTag:
    """Test tag creation endpoint."""

    def test_create_tag_success(self, client, teacher_headers, valid_tag_create_request):
        """Test successful tag creation."""
        response = client.post(
            "/tags/",
            json=valid_tag_create_request,
            headers=teacher_headers
        )

        data = APITestHelper.assert_success_response(
            response,
            expected_status=status.HTTP_201_CREATED
        )

        assert data["name"] == valid_tag_create_request["name"]
        assert data["description"] == valid_tag_create_request["description"]
        assert data["color"] == valid_tag_create_request["color"]
        assert data["category"] == valid_tag_create_request["category"]

    def test_create_tag_generates_slug(self, client, teacher_headers):
        """Test that tag creation generates slug from name."""
        request_data = {"name": "Test Tag Name"}

        response = client.post(
            "/tags/",
            json=request_data,
            headers=teacher_headers
        )

        data = APITestHelper.assert_success_response(
            response,
            expected_status=status.HTTP_201_CREATED
        )

        assert data["slug"] == "test-tag-name"

    def test_create_tag_default_color(self, client, teacher_headers):
        """Test that tag creation assigns default color when not provided."""
        request_data = {"name": "No Color Tag"}

        response = client.post(
            "/tags/",
            json=request_data,
            headers=teacher_headers
        )

        data = APITestHelper.assert_success_response(
            response,
            expected_status=status.HTTP_201_CREATED
        )

        assert data["color"] == "#3B82F6"  # Default blue

    def test_create_tag_sets_created_by(self, client, teacher_headers, valid_tag_create_request):
        """Test that tag creation sets creator information."""
        response = client.post(
            "/tags/",
            json=valid_tag_create_request,
            headers=teacher_headers
        )

        data = APITestHelper.assert_success_response(
            response,
            expected_status=status.HTTP_201_CREATED
        )

        assert "created_by" in data
        assert "created_by_name" in data

    def test_create_tag_initial_usage_count_zero(self, client, teacher_headers, valid_tag_create_request):
        """Test that new tags have zero usage count."""
        response = client.post(
            "/tags/",
            json=valid_tag_create_request,
            headers=teacher_headers
        )

        data = APITestHelper.assert_success_response(
            response,
            expected_status=status.HTTP_201_CREATED
        )

        assert data["usage_count"] == 0

    def test_create_tag_has_timestamp(self, client, teacher_headers, valid_tag_create_request):
        """Test that created tag has timestamp."""
        before = datetime.utcnow()

        response = client.post(
            "/tags/",
            json=valid_tag_create_request,
            headers=teacher_headers
        )

        after = datetime.utcnow()

        data = APITestHelper.assert_success_response(
            response,
            expected_status=status.HTTP_201_CREATED
        )

        created_at = datetime.fromisoformat(data["created_at"].replace('Z', '+00:00'))
        assert before <= created_at <= after

    def test_create_tag_has_unique_id(self, client, teacher_headers, valid_tag_create_request):
        """Test that created tag has unique UUID."""
        response = client.post(
            "/tags/",
            json=valid_tag_create_request,
            headers=teacher_headers
        )

        data = APITestHelper.assert_success_response(
            response,
            expected_status=status.HTTP_201_CREATED
        )

        # Verify it's a valid UUID string
        tag_id = UUID(data["id"])
        assert isinstance(tag_id, UUID)


# ============================================================================
# Test Get Tag Endpoint
# ============================================================================


class TestGetTag:
    """Test get tag details endpoint."""

    def test_get_tag_not_found(self, client):
        """Test getting non-existent tag returns 404."""
        tag_id = uuid4()

        response = client.get(f"/tags/{tag_id}")

        APITestHelper.assert_error_response(
            response,
            expected_status=status.HTTP_404_NOT_FOUND,
            expected_detail="not found"
        )


# ============================================================================
# Test Update Tag Endpoint
# ============================================================================


class TestUpdateTag:
    """Test tag update endpoint."""

    def test_update_tag_not_found(self, client, teacher_headers, valid_tag_update_request):
        """Test updating non-existent tag returns 404."""
        tag_id = uuid4()

        response = client.put(
            f"/tags/{tag_id}",
            json=valid_tag_update_request,
            headers=teacher_headers
        )

        APITestHelper.assert_error_response(
            response,
            expected_status=status.HTTP_404_NOT_FOUND
        )


# ============================================================================
# Test Delete Tag Endpoint
# ============================================================================


class TestDeleteTag:
    """Test tag deletion endpoint."""

    def test_delete_tag_success(self, client, teacher_headers):
        """Test successful tag deletion."""
        tag_id = uuid4()

        response = client.delete(f"/tags/{tag_id}", headers=teacher_headers)

        # Should return 204 No Content or 200 OK with message
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_204_NO_CONTENT
        ]


# ============================================================================
# Test Get Popular Tags Endpoint
# ============================================================================


class TestGetPopularTags:
    """Test popular tags endpoint."""

    def test_get_popular_tags_default(self, client):
        """Test getting popular tags with default parameters."""
        response = client.get("/tags/popular")

        data = APITestHelper.assert_success_response(response)

        assert "tags" in data
        assert isinstance(data["tags"], list)
        assert data["period"] == "all_time"

    def test_get_popular_tags_with_limit(self, client):
        """Test getting popular tags with custom limit."""
        response = client.get("/tags/popular?limit=10")

        data = APITestHelper.assert_success_response(response)

        assert "tags" in data

    def test_get_popular_tags_30_days(self, client):
        """Test getting popular tags for 30 days period."""
        response = client.get("/tags/popular?period=30_days")

        data = APITestHelper.assert_success_response(response)

        assert data["period"] == "30_days"

    def test_get_popular_tags_7_days(self, client):
        """Test getting popular tags for 7 days period."""
        response = client.get("/tags/popular?period=7_days")

        data = APITestHelper.assert_success_response(response)

        assert data["period"] == "7_days"

    def test_get_popular_tags_all_time(self, client):
        """Test getting popular tags for all time."""
        response = client.get("/tags/popular?period=all_time")

        data = APITestHelper.assert_success_response(response)

        assert data["period"] == "all_time"


# ============================================================================
# Test Merge Tags Endpoint
# ============================================================================


class TestMergeTags:
    """Test tag merging endpoint."""

    def test_merge_tags_not_found(self, client, teacher_headers, valid_tag_merge_request):
        """Test merging with non-existent target tag returns 404."""
        response = client.post(
            "/tags/merge",
            json=valid_tag_merge_request,
            headers=teacher_headers
        )

        APITestHelper.assert_error_response(
            response,
            expected_status=status.HTTP_404_NOT_FOUND,
            expected_detail="not found"
        )


# ============================================================================
# Test Tag Models
# ============================================================================


class TestTagModels:
    """Test tag model validations."""

    def test_tag_create_request_name_min_length(self):
        """Test that tag name must be at least 1 character."""
        with pytest.raises(Exception):
            TagCreateRequest(name="")

    def test_tag_create_request_name_max_length(self):
        """Test that tag name has maximum length."""
        long_name = "a" * 51  # Exceeds max_length=50

        with pytest.raises(Exception):
            TagCreateRequest(name=long_name)

    def test_tag_create_request_valid_color_pattern(self):
        """Test that color must match hex pattern."""
        with pytest.raises(Exception):
            TagCreateRequest(name="Test", color="invalid")

    def test_tag_create_request_valid_hex_color(self):
        """Test that valid hex colors are accepted."""
        request = TagCreateRequest(name="Test", color="#FF5733")
        assert request.color == "#FF5733"

    def test_tag_create_request_optional_fields(self):
        """Test that description, color, and category are optional."""
        request = TagCreateRequest(name="Minimal Tag")
        assert request.name == "Minimal Tag"
        assert request.description is None
        assert request.color is None
        assert request.category is None

    def test_tag_update_request_all_fields_optional(self):
        """Test that all update fields are optional."""
        request = TagUpdateRequest()
        assert request.name is None
        assert request.description is None
        assert request.color is None
        assert request.category is None

    def test_tag_merge_request_requires_source_tags(self):
        """Test that merge request requires at least one source tag."""
        with pytest.raises(Exception):
            TagMergeRequest(source_tag_ids=[], target_tag_id=uuid4())

    def test_tag_merge_request_default_delete_source(self):
        """Test that merge request defaults to deleting source tags."""
        request = TagMergeRequest(
            source_tag_ids=[uuid4()],
            target_tag_id=uuid4(),
        )
        assert request.delete_source_tags is True

    def test_tag_merge_request_optional_keep_source(self):
        """Test that merge request can optionally keep source tags."""
        request = TagMergeRequest(
            source_tag_ids=[uuid4()],
            target_tag_id=uuid4(),
            delete_source_tags=False,
        )
        assert request.delete_source_tags is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
