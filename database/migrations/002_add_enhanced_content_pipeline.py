"""Add enhanced content pipeline tables

Revision ID: 002_enhanced_content
Revises: 001_add_integration_agent_data
Create Date: 2025-09-19 10:00:00

"""

import uuid

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = "002_enhanced_content"
down_revision = "001_add_integration_agent_data"
branch_labels = None
depends_on = None


def upgrade():
    """Add enhanced content pipeline tables"""

    # Create enhanced_content_generations table
    op.create_table(
        "enhanced_content_generations",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False, default=uuid.uuid4),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("original_request", sa.JSON(), nullable=False),
        sa.Column("content_type", sa.String(50), nullable=False),
        sa.Column("subject", sa.String(100), nullable=True),
        sa.Column("grade_level", sa.String(50), nullable=True),
        sa.Column("difficulty_level", sa.String(20), nullable=True),
        sa.Column("enhanced_content", sa.JSON(), nullable=True),
        sa.Column("generated_scripts", sa.JSON(), nullable=True),
        sa.Column("generated_assets", sa.JSON(), nullable=True),
        sa.Column("quality_score", sa.Float(), nullable=True),
        sa.Column("engagement_score", sa.Float(), nullable=True),
        sa.Column("educational_value_score", sa.Float(), nullable=True),
        sa.Column("accessibility_score", sa.Float(), nullable=True),
        sa.Column("personalization_applied", sa.Boolean(), default=False),
        sa.Column("personalization_parameters", sa.JSON(), nullable=True),
        sa.Column("generation_metadata", sa.JSON(), nullable=True),
        sa.Column("status", sa.String(50), default="processing"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, default=sa.func.now()),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("generation_time_seconds", sa.Float(), nullable=True),
        sa.Column("tokens_used", sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )

    # Create indexes for enhanced_content_generations
    op.create_index("idx_ecg_user_status", "enhanced_content_generations", ["user_id", "status"])
    op.create_index("idx_ecg_created_at", "enhanced_content_generations", ["created_at"])
    op.create_index("idx_ecg_quality_score", "enhanced_content_generations", ["quality_score"])

    # Create content_quality_metrics table
    op.create_table(
        "content_quality_metrics",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False, default=uuid.uuid4),
        sa.Column("content_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("curriculum_alignment_score", sa.Float(), nullable=True),
        sa.Column("learning_objectives_coverage", sa.Float(), nullable=True),
        sa.Column("cognitive_level_appropriateness", sa.Float(), nullable=True),
        sa.Column("interactivity_score", sa.Float(), nullable=True),
        sa.Column("visual_appeal_score", sa.Float(), nullable=True),
        sa.Column("narrative_quality_score", sa.Float(), nullable=True),
        sa.Column("code_quality_score", sa.Float(), nullable=True),
        sa.Column("performance_score", sa.Float(), nullable=True),
        sa.Column("compatibility_score", sa.Float(), nullable=True),
        sa.Column("readability_score", sa.Float(), nullable=True),
        sa.Column("wcag_compliance_score", sa.Float(), nullable=True),
        sa.Column("language_simplicity_score", sa.Float(), nullable=True),
        sa.Column("overall_quality_score", sa.Float(), nullable=True),
        sa.Column("recommendation_score", sa.Float(), nullable=True),
        sa.Column("validation_details", sa.JSON(), nullable=True),
        sa.Column("validation_errors", sa.JSON(), nullable=True),
        sa.Column("improvement_suggestions", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["content_id"], ["enhanced_content_generations.id"], ondelete="CASCADE"
        ),
    )

    # Create indexes for content_quality_metrics
    op.create_index(
        "idx_cqm_content_score", "content_quality_metrics", ["content_id", "overall_quality_score"]
    )
    op.create_index("idx_cqm_created_at", "content_quality_metrics", ["created_at"])

    # Create learning_profiles table
    op.create_table(
        "learning_profiles",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False, default=uuid.uuid4),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("learning_style", sa.JSON(), nullable=True),
        sa.Column("preferred_difficulty", sa.JSON(), nullable=True),
        sa.Column("subject_preferences", sa.JSON(), nullable=True),
        sa.Column("engagement_patterns", sa.JSON(), nullable=True),
        sa.Column("interaction_preferences", sa.JSON(), nullable=True),
        sa.Column("performance_history", sa.JSON(), nullable=True),
        sa.Column("strengths", sa.JSON(), nullable=True),
        sa.Column("improvement_areas", sa.JSON(), nullable=True),
        sa.Column("accessibility_requirements", sa.JSON(), nullable=True),
        sa.Column("language_preferences", sa.JSON(), nullable=True),
        sa.Column("preferred_game_mechanics", sa.JSON(), nullable=True),
        sa.Column("avatar_preferences", sa.JSON(), nullable=True),
        sa.Column("profile_completeness", sa.Float(), nullable=True),
        sa.Column("confidence_score", sa.Float(), nullable=True),
        sa.Column(
            "last_updated",
            sa.DateTime(),
            nullable=False,
            default=sa.func.now(),
            onupdate=sa.func.now(),
        ),
        sa.Column("created_at", sa.DateTime(), nullable=False, default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("user_id"),
    )

    # Create indexes for learning_profiles
    op.create_index("idx_lp_user", "learning_profiles", ["user_id"])
    op.create_index("idx_lp_updated", "learning_profiles", ["last_updated"])

    # Create content_personalization_log table
    op.create_table(
        "content_personalization_log",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False, default=uuid.uuid4),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("content_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("personalization_type", sa.String(50), nullable=True),
        sa.Column("personalization_applied", sa.JSON(), nullable=True),
        sa.Column("effectiveness_score", sa.Float(), nullable=True),
        sa.Column("engagement_improvement", sa.Float(), nullable=True),
        sa.Column("learning_outcome_improvement", sa.Float(), nullable=True),
        sa.Column("user_feedback", sa.JSON(), nullable=True),
        sa.Column("user_rating", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["content_id"], ["enhanced_content_generations.id"], ondelete="CASCADE"
        ),
    )

    # Create indexes for content_personalization_log
    op.create_index("idx_cpl_user_date", "content_personalization_log", ["user_id", "created_at"])
    op.create_index("idx_cpl_content", "content_personalization_log", ["content_id"])
    op.create_index("idx_cpl_effectiveness", "content_personalization_log", ["effectiveness_score"])

    # Create content_feedback table
    op.create_table(
        "content_feedback",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False, default=uuid.uuid4),
        sa.Column("content_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("rating", sa.Float(), nullable=True),
        sa.Column("feedback_type", sa.String(50), nullable=True),
        sa.Column("feedback_text", sa.Text(), nullable=True),
        sa.Column("educational_value_rating", sa.Float(), nullable=True),
        sa.Column("engagement_rating", sa.Float(), nullable=True),
        sa.Column("difficulty_rating", sa.Float(), nullable=True),
        sa.Column("technical_quality_rating", sa.Float(), nullable=True),
        sa.Column("suggested_improvements", sa.JSON(), nullable=True),
        sa.Column("reported_issues", sa.JSON(), nullable=True),
        sa.Column("session_duration", sa.Float(), nullable=True),
        sa.Column("completion_rate", sa.Float(), nullable=True),
        sa.Column("interaction_count", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["content_id"], ["enhanced_content_generations.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )

    # Create indexes for content_feedback
    op.create_index("idx_cf_content_rating", "content_feedback", ["content_id", "rating"])
    op.create_index("idx_cf_user", "content_feedback", ["user_id"])
    op.create_index("idx_cf_created_at", "content_feedback", ["created_at"])

    # Create content_generation_batches table
    op.create_table(
        "content_generation_batches",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False, default=uuid.uuid4),
        sa.Column("batch_name", sa.String(200), nullable=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("batch_config", sa.JSON(), nullable=True),
        sa.Column("total_items", sa.Integer(), nullable=True),
        sa.Column("completed_items", sa.Integer(), default=0),
        sa.Column("failed_items", sa.Integer(), default=0),
        sa.Column("status", sa.String(50), default="pending"),
        sa.Column("estimated_completion_time", sa.DateTime(), nullable=True),
        sa.Column("actual_completion_time", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, default=sa.func.now()),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )

    # Create indexes for content_generation_batches
    op.create_index("idx_cgb_user_status", "content_generation_batches", ["user_id", "status"])
    op.create_index("idx_cgb_created_at", "content_generation_batches", ["created_at"])

    # Create content_cache table
    op.create_table(
        "content_cache",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False, default=uuid.uuid4),
        sa.Column("cache_key", sa.String(500), nullable=False),
        sa.Column("cache_type", sa.String(50), nullable=True),
        sa.Column("cached_data", sa.JSON(), nullable=True),
        sa.Column("access_count", sa.Integer(), default=0),
        sa.Column("last_accessed", sa.DateTime(), nullable=True),
        sa.Column("ttl_seconds", sa.Integer(), default=3600),
        sa.Column("created_at", sa.DateTime(), nullable=False, default=sa.func.now()),
        sa.Column("expires_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("cache_key"),
    )

    # Create indexes for content_cache
    op.create_index("idx_cc_key", "content_cache", ["cache_key"])
    op.create_index("idx_cc_type", "content_cache", ["cache_type"])
    op.create_index("idx_cc_expires", "content_cache", ["expires_at"])


def downgrade():
    """Remove enhanced content pipeline tables"""

    # Drop indexes
    op.drop_index("idx_cc_expires", "content_cache")
    op.drop_index("idx_cc_type", "content_cache")
    op.drop_index("idx_cc_key", "content_cache")
    op.drop_index("idx_cgb_created_at", "content_generation_batches")
    op.drop_index("idx_cgb_user_status", "content_generation_batches")
    op.drop_index("idx_cf_created_at", "content_feedback")
    op.drop_index("idx_cf_user", "content_feedback")
    op.drop_index("idx_cf_content_rating", "content_feedback")
    op.drop_index("idx_cpl_effectiveness", "content_personalization_log")
    op.drop_index("idx_cpl_content", "content_personalization_log")
    op.drop_index("idx_cpl_user_date", "content_personalization_log")
    op.drop_index("idx_lp_updated", "learning_profiles")
    op.drop_index("idx_lp_user", "learning_profiles")
    op.drop_index("idx_cqm_created_at", "content_quality_metrics")
    op.drop_index("idx_cqm_content_score", "content_quality_metrics")
    op.drop_index("idx_ecg_quality_score", "enhanced_content_generations")
    op.drop_index("idx_ecg_created_at", "enhanced_content_generations")
    op.drop_index("idx_ecg_user_status", "enhanced_content_generations")

    # Drop tables
    op.drop_table("content_cache")
    op.drop_table("content_generation_batches")
    op.drop_table("content_feedback")
    op.drop_table("content_personalization_log")
    op.drop_table("learning_profiles")
    op.drop_table("content_quality_metrics")
    op.drop_table("enhanced_content_generations")
