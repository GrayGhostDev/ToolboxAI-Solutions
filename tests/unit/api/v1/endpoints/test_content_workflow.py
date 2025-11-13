"""
Unit Tests for Content Workflow API Endpoints

Tests workflow management including review, approval, and publishing processes.

Phase 1 Week 1: Authentication & user management endpoint tests
"""

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, Mock
from uuid import UUID, uuid4

import pytest
from fastapi import BackgroundTasks

# Import endpoint functions and models
from apps.backend.api.v1.endpoints.content_workflow import (
    ContentWorkflowInfo,
    PendingReviewsResponse,
    PublishContentRequest,
    PublishContentResponse,
    ReviewContentRequest,
    ReviewContentResponse,
    ReviewDecision,
    SubmitForReviewRequest,
    SubmitForReviewResponse,
    WorkflowStatus,
    approve_content,
    get_pending_reviews,
    get_workflow_status,
    publish_content,
    reject_content,
    submit_for_review,
)
from apps.backend.middleware.tenant import TenantContext
from apps.backend.models.schemas import User

# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def mock_teacher_user():
    """Create mock teacher user."""
    user = Mock(spec=User)
    user.id = uuid4()
    user.username = "teacher_user"
    user.email = "teacher@example.com"
    user.role = "teacher"
    return user


@pytest.fixture
def mock_admin_user():
    """Create mock admin user."""
    user = Mock(spec=User)
    user.id = uuid4()
    user.username = "admin_user"
    user.email = "admin@example.com"
    user.role = "admin"
    return user


@pytest.fixture
def mock_student_user():
    """Create mock student user."""
    user = Mock(spec=User)
    user.id = uuid4()
    user.username = "student_user"
    user.email = "student@example.com"
    user.role = "student"
    return user


@pytest.fixture
def mock_session():
    """Create mock async database session."""
    session = AsyncMock()
    session.rollback = AsyncMock()
    return session


@pytest.fixture
def mock_tenant_context():
    """Create mock tenant context."""
    context = Mock(spec=TenantContext)
    context.organization_id = uuid4()
    context.tenant_id = "test-tenant"
    return context


@pytest.fixture
def mock_background_tasks():
    """Create mock background tasks."""
    return Mock(spec=BackgroundTasks)


@pytest.fixture
def valid_submit_request():
    """Create valid submit for review request."""
    return SubmitForReviewRequest(
        submission_notes="Ready for review",
        notify_reviewers=True,
        priority="normal",
    )


@pytest.fixture
def valid_review_request_approve():
    """Create valid approval review request."""
    return ReviewContentRequest(
        decision=ReviewDecision.APPROVE,
        comments="Looks good, approved!",
        notify_author=True,
    )


@pytest.fixture
def valid_review_request_reject():
    """Create valid rejection review request."""
    return ReviewContentRequest(
        decision=ReviewDecision.REJECT,
        comments="Needs significant improvements",
        change_requests=["Fix grammar", "Add more examples"],
        notify_author=True,
    )


@pytest.fixture
def valid_publish_request():
    """Create valid publish content request."""
    return PublishContentRequest(
        publish_immediately=True,
        notify_subscribers=True,
        publish_notes="Initial release",
    )


# ============================================================================
# Test Submit For Review Endpoint
# ============================================================================


class TestSubmitForReview:
    """Test content submission for review endpoint."""

    @pytest.mark.asyncio
    async def test_submit_for_review_success(
        self,
        mock_session,
        mock_teacher_user,
        mock_background_tasks,
        valid_submit_request,
    ):
        """Test successful content submission for review."""
        content_id = uuid4()

        result = await submit_for_review(
            content_id=content_id,
            request=valid_submit_request,
            session=mock_session,
            current_user=mock_teacher_user,
            background_tasks=mock_background_tasks,
        )

        assert isinstance(result, SubmitForReviewResponse)
        assert result.content_id == content_id
        assert isinstance(result.workflow_id, UUID)
        assert result.status == WorkflowStatus.SUBMITTED
        assert "submitted for review successfully" in result.message.lower()

    @pytest.mark.asyncio
    async def test_submit_for_review_with_notifications(
        self,
        mock_session,
        mock_teacher_user,
        mock_background_tasks,
        valid_submit_request,
    ):
        """Test submission with reviewer notifications."""
        content_id = uuid4()
        valid_submit_request.notify_reviewers = True

        result = await submit_for_review(
            content_id=content_id,
            request=valid_submit_request,
            session=mock_session,
            current_user=mock_teacher_user,
            background_tasks=mock_background_tasks,
        )

        assert len(result.reviewers_notified) > 0
        # Background task should be scheduled
        assert mock_background_tasks.add_task.called

    @pytest.mark.asyncio
    async def test_submit_for_review_without_notifications(
        self,
        mock_session,
        mock_teacher_user,
        mock_background_tasks,
    ):
        """Test submission without reviewer notifications."""
        content_id = uuid4()
        request = SubmitForReviewRequest(notify_reviewers=False)

        result = await submit_for_review(
            content_id=content_id,
            request=request,
            session=mock_session,
            current_user=mock_teacher_user,
            background_tasks=mock_background_tasks,
        )

        assert len(result.reviewers_notified) == 0

    @pytest.mark.asyncio
    async def test_submit_for_review_high_priority(
        self, mock_session, mock_teacher_user, mock_background_tasks
    ):
        """Test submission with high priority."""
        content_id = uuid4()
        request = SubmitForReviewRequest(priority="high")

        result = await submit_for_review(
            content_id=content_id,
            request=request,
            session=mock_session,
            current_user=mock_teacher_user,
            background_tasks=mock_background_tasks,
        )

        assert result.status == WorkflowStatus.SUBMITTED

    @pytest.mark.asyncio
    async def test_submit_for_review_urgent_priority(
        self, mock_session, mock_teacher_user, mock_background_tasks
    ):
        """Test submission with urgent priority."""
        content_id = uuid4()
        request = SubmitForReviewRequest(priority="urgent")

        result = await submit_for_review(
            content_id=content_id,
            request=request,
            session=mock_session,
            current_user=mock_teacher_user,
            background_tasks=mock_background_tasks,
        )

        assert result.status == WorkflowStatus.SUBMITTED

    @pytest.mark.asyncio
    async def test_submit_for_review_recent_timestamp(
        self, mock_session, mock_teacher_user, mock_background_tasks, valid_submit_request
    ):
        """Test that submission timestamp is recent."""
        content_id = uuid4()
        before = datetime.utcnow()

        result = await submit_for_review(
            content_id=content_id,
            request=valid_submit_request,
            session=mock_session,
            current_user=mock_teacher_user,
            background_tasks=mock_background_tasks,
        )

        after = datetime.utcnow()
        assert before <= result.submitted_at <= after


# ============================================================================
# Test Approve Content Endpoint
# ============================================================================


class TestApproveContent:
    """Test content approval endpoint."""

    @pytest.mark.asyncio
    async def test_approve_content_success(
        self,
        mock_session,
        mock_teacher_user,
        mock_background_tasks,
        valid_review_request_approve,
    ):
        """Test successful content approval."""
        content_id = uuid4()

        result = await approve_content(
            content_id=content_id,
            request=valid_review_request_approve,
            session=mock_session,
            current_user=mock_teacher_user,
            background_tasks=mock_background_tasks,
        )

        assert isinstance(result, ReviewContentResponse)
        assert result.content_id == content_id
        assert result.decision == ReviewDecision.APPROVE
        assert result.new_status == WorkflowStatus.APPROVED

    @pytest.mark.asyncio
    async def test_approve_content_with_reject_decision(
        self, mock_session, mock_teacher_user, mock_background_tasks, valid_review_request_reject
    ):
        """Test content rejection."""
        content_id = uuid4()

        result = await approve_content(
            content_id=content_id,
            request=valid_review_request_reject,
            session=mock_session,
            current_user=mock_teacher_user,
            background_tasks=mock_background_tasks,
        )

        assert result.decision == ReviewDecision.REJECT
        assert result.new_status == WorkflowStatus.REJECTED

    @pytest.mark.asyncio
    async def test_approve_content_request_changes(
        self, mock_session, mock_teacher_user, mock_background_tasks
    ):
        """Test requesting changes to content."""
        content_id = uuid4()
        request = ReviewContentRequest(
            decision=ReviewDecision.REQUEST_CHANGES,
            comments="Please make these changes",
            change_requests=["Add more examples", "Fix typo on page 3"],
            notify_author=True,
        )

        result = await approve_content(
            content_id=content_id,
            request=request,
            session=mock_session,
            current_user=mock_teacher_user,
            background_tasks=mock_background_tasks,
        )

        assert result.decision == ReviewDecision.REQUEST_CHANGES
        assert result.new_status == WorkflowStatus.DRAFT

    @pytest.mark.asyncio
    async def test_approve_content_notifies_author(
        self, mock_session, mock_teacher_user, mock_background_tasks, valid_review_request_approve
    ):
        """Test that approval notifies author."""
        content_id = uuid4()
        valid_review_request_approve.notify_author = True

        await approve_content(
            content_id=content_id,
            request=valid_review_request_approve,
            session=mock_session,
            current_user=mock_teacher_user,
            background_tasks=mock_background_tasks,
        )

        # Background task should be scheduled
        assert mock_background_tasks.add_task.called

    @pytest.mark.asyncio
    async def test_approve_content_without_notification(
        self, mock_session, mock_teacher_user, mock_background_tasks
    ):
        """Test approval without author notification."""
        content_id = uuid4()
        request = ReviewContentRequest(
            decision=ReviewDecision.APPROVE,
            comments="Approved",
            notify_author=False,
        )

        result = await approve_content(
            content_id=content_id,
            request=request,
            session=mock_session,
            current_user=mock_teacher_user,
            background_tasks=mock_background_tasks,
        )

        assert result.decision == ReviewDecision.APPROVE


# ============================================================================
# Test Reject Content Endpoint
# ============================================================================


class TestRejectContent:
    """Test content rejection endpoint."""

    @pytest.mark.asyncio
    async def test_reject_content_success(
        self, mock_session, mock_teacher_user, mock_background_tasks, valid_review_request_reject
    ):
        """Test successful content rejection."""
        content_id = uuid4()

        result = await reject_content(
            content_id=content_id,
            request=valid_review_request_reject,
            session=mock_session,
            current_user=mock_teacher_user,
            background_tasks=mock_background_tasks,
        )

        assert isinstance(result, ReviewContentResponse)
        assert result.decision == ReviewDecision.REJECT
        assert result.new_status == WorkflowStatus.REJECTED

    @pytest.mark.asyncio
    async def test_reject_content_forces_reject_decision(
        self, mock_session, mock_teacher_user, mock_background_tasks
    ):
        """Test that reject endpoint forces REJECT decision."""
        content_id = uuid4()
        # Start with approve decision
        request = ReviewContentRequest(
            decision=ReviewDecision.APPROVE,
            comments="Will be overridden",
        )

        result = await reject_content(
            content_id=content_id,
            request=request,
            session=mock_session,
            current_user=mock_teacher_user,
            background_tasks=mock_background_tasks,
        )

        # Decision should be forced to REJECT
        assert result.decision == ReviewDecision.REJECT


# ============================================================================
# Test Publish Content Endpoint
# ============================================================================


class TestPublishContent:
    """Test content publishing endpoint."""

    @pytest.mark.asyncio
    async def test_publish_content_immediately(
        self, mock_session, mock_teacher_user, mock_background_tasks, valid_publish_request
    ):
        """Test immediate content publishing."""
        content_id = uuid4()
        valid_publish_request.publish_immediately = True

        result = await publish_content(
            content_id=content_id,
            request=valid_publish_request,
            session=mock_session,
            current_user=mock_teacher_user,
            background_tasks=mock_background_tasks,
        )

        assert isinstance(result, PublishContentResponse)
        assert result.content_id == content_id
        assert result.status == WorkflowStatus.PUBLISHED
        assert result.public_url is not None

    @pytest.mark.asyncio
    async def test_publish_content_scheduled(
        self, mock_session, mock_teacher_user, mock_background_tasks
    ):
        """Test scheduled content publishing."""
        content_id = uuid4()
        future_time = datetime.utcnow() + timedelta(days=7)
        request = PublishContentRequest(
            publish_immediately=False,
            scheduled_publish_at=future_time,
            notify_subscribers=True,
        )

        result = await publish_content(
            content_id=content_id,
            request=request,
            session=mock_session,
            current_user=mock_teacher_user,
            background_tasks=mock_background_tasks,
        )

        assert result.published_at == future_time

    @pytest.mark.asyncio
    async def test_publish_content_generates_public_url(
        self, mock_session, mock_teacher_user, mock_background_tasks, valid_publish_request
    ):
        """Test that publishing generates public URL."""
        content_id = uuid4()

        result = await publish_content(
            content_id=content_id,
            request=valid_publish_request,
            session=mock_session,
            current_user=mock_teacher_user,
            background_tasks=mock_background_tasks,
        )

        assert result.public_url is not None
        assert str(content_id) in result.public_url

    @pytest.mark.asyncio
    async def test_publish_content_with_subscriber_notifications(
        self, mock_session, mock_teacher_user, mock_background_tasks, valid_publish_request
    ):
        """Test publishing with subscriber notifications."""
        content_id = uuid4()
        valid_publish_request.notify_subscribers = True

        await publish_content(
            content_id=content_id,
            request=valid_publish_request,
            session=mock_session,
            current_user=mock_teacher_user,
            background_tasks=mock_background_tasks,
        )

        # Background task should be scheduled
        assert mock_background_tasks.add_task.called

    @pytest.mark.asyncio
    async def test_publish_content_without_notifications(
        self, mock_session, mock_teacher_user, mock_background_tasks
    ):
        """Test publishing without subscriber notifications."""
        content_id = uuid4()
        request = PublishContentRequest(
            publish_immediately=True,
            notify_subscribers=False,
        )

        result = await publish_content(
            content_id=content_id,
            request=request,
            session=mock_session,
            current_user=mock_teacher_user,
            background_tasks=mock_background_tasks,
        )

        assert result.status == WorkflowStatus.PUBLISHED


# ============================================================================
# Test Get Pending Reviews Endpoint
# ============================================================================


class TestGetPendingReviews:
    """Test pending reviews endpoint."""

    @pytest.mark.asyncio
    async def test_get_pending_reviews_success(
        self, mock_session, mock_teacher_user, mock_tenant_context
    ):
        """Test successful pending reviews retrieval."""
        result = await get_pending_reviews(
            session=mock_session,
            current_user=mock_teacher_user,
            tenant_context=mock_tenant_context,
        )

        assert isinstance(result, PendingReviewsResponse)
        assert isinstance(result.items, list)
        assert isinstance(result.by_priority, dict)

    @pytest.mark.asyncio
    async def test_get_pending_reviews_with_priority_filter(
        self, mock_session, mock_teacher_user, mock_tenant_context
    ):
        """Test filtering pending reviews by priority."""
        result = await get_pending_reviews(
            session=mock_session,
            current_user=mock_teacher_user,
            tenant_context=mock_tenant_context,
            priority_filter="high",
        )

        assert isinstance(result, PendingReviewsResponse)

    @pytest.mark.asyncio
    async def test_get_pending_reviews_has_priority_breakdown(
        self, mock_session, mock_teacher_user, mock_tenant_context
    ):
        """Test that response includes priority breakdown."""
        result = await get_pending_reviews(
            session=mock_session,
            current_user=mock_teacher_user,
            tenant_context=mock_tenant_context,
        )

        assert "urgent" in result.by_priority
        assert "high" in result.by_priority
        assert "normal" in result.by_priority
        assert "low" in result.by_priority

    @pytest.mark.asyncio
    async def test_get_pending_reviews_total_matches_items(
        self, mock_session, mock_teacher_user, mock_tenant_context
    ):
        """Test that total count matches items length."""
        result = await get_pending_reviews(
            session=mock_session,
            current_user=mock_teacher_user,
            tenant_context=mock_tenant_context,
        )

        assert result.total == len(result.items)


# ============================================================================
# Test Get Workflow Status Endpoint
# ============================================================================


class TestGetWorkflowStatus:
    """Test workflow status endpoint."""

    @pytest.mark.asyncio
    async def test_get_workflow_status_success(self, mock_session, mock_teacher_user):
        """Test successful workflow status retrieval."""
        content_id = uuid4()

        result = await get_workflow_status(
            content_id=content_id,
            session=mock_session,
            current_user=mock_teacher_user,
        )

        assert isinstance(result, ContentWorkflowInfo)
        assert result.content_id == content_id
        assert isinstance(result.status, WorkflowStatus)

    @pytest.mark.asyncio
    async def test_get_workflow_status_structure(self, mock_session, mock_teacher_user):
        """Test workflow status response structure."""
        content_id = uuid4()

        result = await get_workflow_status(
            content_id=content_id,
            session=mock_session,
            current_user=mock_teacher_user,
        )

        assert hasattr(result, "content_id")
        assert hasattr(result, "title")
        assert hasattr(result, "status")
        assert hasattr(result, "review_comments")
        assert isinstance(result.review_comments, list)


# ============================================================================
# Test Workflow Models
# ============================================================================


class TestWorkflowModels:
    """Test workflow model validations."""

    def test_submit_request_priority_pattern(self):
        """Test that priority must match pattern."""
        with pytest.raises(Exception):
            SubmitForReviewRequest(priority="invalid")

    def test_submit_request_valid_priorities(self):
        """Test all valid priority values."""
        for priority in ["low", "normal", "high", "urgent"]:
            request = SubmitForReviewRequest(priority=priority)
            assert request.priority == priority

    def test_review_request_requires_comments(self):
        """Test that review request requires comments."""
        with pytest.raises(Exception):
            ReviewContentRequest(
                decision=ReviewDecision.APPROVE,
                comments="",  # Empty comments
            )

    def test_review_request_comments_max_length(self):
        """Test that review comments have max length."""
        long_comments = "a" * 2001  # Exceeds max_length=2000

        with pytest.raises(Exception):
            ReviewContentRequest(
                decision=ReviewDecision.APPROVE,
                comments=long_comments,
            )

    def test_publish_request_default_immediate(self):
        """Test that publish defaults to immediate."""
        request = PublishContentRequest()
        assert request.publish_immediately is True

    def test_publish_request_default_notify_subscribers(self):
        """Test that publish defaults to notifying subscribers."""
        request = PublishContentRequest()
        assert request.notify_subscribers is True

    def test_workflow_status_enum_values(self):
        """Test workflow status enum values."""
        assert WorkflowStatus.DRAFT == "draft"
        assert WorkflowStatus.SUBMITTED == "submitted"
        assert WorkflowStatus.IN_REVIEW == "in_review"
        assert WorkflowStatus.APPROVED == "approved"
        assert WorkflowStatus.REJECTED == "rejected"
        assert WorkflowStatus.PUBLISHED == "published"
        assert WorkflowStatus.ARCHIVED == "archived"

    def test_review_decision_enum_values(self):
        """Test review decision enum values."""
        assert ReviewDecision.APPROVE == "approve"
        assert ReviewDecision.REJECT == "reject"
        assert ReviewDecision.REQUEST_CHANGES == "request_changes"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
