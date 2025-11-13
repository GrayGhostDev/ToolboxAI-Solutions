"""Add Roblox integration tables - manual migration

Revision ID: 002
Revises: 001
Create Date: 2025-09-15 04:30:00.000000

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy import text
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Apply the migration."""
    connection = op.get_bind()

    # Create new enum types for Roblox integration
    connection.execute(
        text(
            """
        DO $$ BEGIN
            CREATE TYPE robloxcontenttype AS ENUM (
                'SCRIPT', 'MODEL', 'TERRAIN', 'GUI',
                'ANIMATION', 'SOUND', 'TEXTURE', 'MESH'
            );
        EXCEPTION
            WHEN duplicate_object THEN NULL;
        END $$;
    """
        )
    )

    connection.execute(
        text(
            """
        DO $$ BEGIN
            CREATE TYPE robloxsessionstatus AS ENUM (
                'ACTIVE', 'PAUSED', 'COMPLETED', 'DISCONNECTED', 'ERROR'
            );
        EXCEPTION
            WHEN duplicate_object THEN NULL;
        END $$;
    """
        )
    )

    # Create roblox_templates table
    op.create_table(
        "roblox_templates",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
            default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("creator_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("category", sa.String(100), nullable=False),
        sa.Column("subject_area", sa.String(100), nullable=False),
        sa.Column("grade_level_min", sa.Integer(), nullable=False),
        sa.Column("grade_level_max", sa.Integer(), nullable=False),
        sa.Column(
            "template_type",
            postgresql.ENUM(
                "SCRIPT",
                "MODEL",
                "TERRAIN",
                "GUI",
                "ANIMATION",
                "SOUND",
                "TEXTURE",
                "MESH",
                name="robloxcontenttype",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column("base_structure", postgresql.JSONB(), nullable=False),
        sa.Column("customization_points", postgresql.JSONB(), default=sa.text("'[]'::jsonb")),
        sa.Column("variable_definitions", postgresql.JSONB(), default=sa.text("'{}'::jsonb")),
        sa.Column(
            "learning_objectives_template", postgresql.JSONB(), default=sa.text("'[]'::jsonb")
        ),
        sa.Column("assessment_criteria", postgresql.JSONB(), default=sa.text("'{}'::jsonb")),
        sa.Column("difficulty_scales", postgresql.JSONB(), default=sa.text("'{}'::jsonb")),
        sa.Column("adaptation_rules", postgresql.JSONB(), default=sa.text("'{}'::jsonb")),
        sa.Column("required_assets", postgresql.JSONB(), default=sa.text("'[]'::jsonb")),
        sa.Column("script_templates", postgresql.JSONB(), default=sa.text("'{}'::jsonb")),
        sa.Column("ui_templates", postgresql.JSONB(), default=sa.text("'{}'::jsonb")),
        sa.Column("model_specifications", postgresql.JSONB(), default=sa.text("'{}'::jsonb")),
        sa.Column("ai_generation_prompts", postgresql.JSONB(), default=sa.text("'{}'::jsonb")),
        sa.Column("parameter_constraints", postgresql.JSONB(), default=sa.text("'{}'::jsonb")),
        sa.Column("quality_thresholds", postgresql.JSONB(), default=sa.text("'{}'::jsonb")),
        sa.Column("usage_count", sa.Integer(), default=0),
        sa.Column("success_rate", sa.Float(), default=0.0),
        sa.Column("average_rating", sa.Float(), default=0.0),
        sa.Column("performance_metrics", postgresql.JSONB(), default=sa.text("'{}'::jsonb")),
        sa.Column("version", sa.String(20), default="1.0.0"),
        sa.Column("is_active", sa.Boolean(), default=True),
        sa.Column("is_public", sa.Boolean(), default=False),
        sa.Column("coppa_compliant", sa.Boolean(), default=True),
        sa.Column("age_appropriate_content", sa.Boolean(), default=True),
        sa.Column("content_warnings", postgresql.JSONB(), default=sa.text("'[]'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True)),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["creator_id"], ["users.id"]),
        sa.CheckConstraint("grade_level_min >= 1 AND grade_level_min <= 12"),
        sa.CheckConstraint("grade_level_max >= 1 AND grade_level_max <= 12"),
        sa.CheckConstraint("grade_level_min <= grade_level_max"),
        sa.CheckConstraint("success_rate >= 0 AND success_rate <= 100"),
        sa.CheckConstraint("average_rating >= 0 AND average_rating <= 5"),
    )

    # Create indexes for roblox_templates
    op.create_index("idx_roblox_template_category", "roblox_templates", ["category"])
    op.create_index("idx_roblox_template_subject", "roblox_templates", ["subject_area"])
    op.create_index(
        "idx_roblox_template_grade", "roblox_templates", ["grade_level_min", "grade_level_max"]
    )
    op.create_index("idx_roblox_template_type", "roblox_templates", ["template_type"])
    op.create_index("idx_roblox_template_active", "roblox_templates", ["is_active", "is_public"])

    # Create roblox_sessions table
    op.create_table(
        "roblox_sessions",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
            default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("lesson_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("teacher_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("universe_id", sa.String(100), nullable=False, default="8505376973"),
        sa.Column("place_id", sa.String(100), nullable=False),
        sa.Column("server_id", sa.String(200)),
        sa.Column("job_id", sa.String(200)),
        sa.Column("client_id", sa.String(100), nullable=False, default="2214511122270781418"),
        sa.Column("access_token_hash", sa.String(255)),
        sa.Column("refresh_token_hash", sa.String(255)),
        sa.Column("token_expires_at", sa.DateTime(timezone=True)),
        sa.Column("websocket_session_id", sa.String(200), unique=True),
        sa.Column("websocket_connection_active", sa.Boolean(), default=False),
        sa.Column("last_heartbeat", sa.DateTime(timezone=True)),
        sa.Column(
            "status",
            postgresql.ENUM(
                "ACTIVE",
                "PAUSED",
                "COMPLETED",
                "DISCONNECTED",
                "ERROR",
                name="robloxsessionstatus",
                create_type=False,
            ),
            default="ACTIVE",
        ),
        sa.Column("max_players", sa.Integer(), default=30),
        sa.Column("current_players", sa.Integer(), default=0),
        sa.Column("sync_frequency_seconds", sa.Integer(), default=5),
        sa.Column("last_sync_at", sa.DateTime(timezone=True)),
        sa.Column("sync_errors", sa.Integer(), default=0),
        sa.Column("sync_data", postgresql.JSONB(), default=sa.text("'{}'::jsonb")),
        sa.Column("coppa_consent_verified", sa.Boolean(), default=False),
        sa.Column("audit_log", postgresql.JSONB(), default=sa.text("'[]'::jsonb")),
        sa.Column(
            "parental_consent_ids", postgresql.ARRAY(sa.String()), default=sa.text("'{}'::text[]")
        ),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("ended_at", sa.DateTime(timezone=True)),
        sa.Column("last_activity_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True)),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["lesson_id"], ["lessons.id"]),
        sa.ForeignKeyConstraint(["teacher_id"], ["users.id"]),
    )

    # Create indexes for roblox_sessions
    op.create_index("idx_roblox_session_lesson", "roblox_sessions", ["lesson_id"])
    op.create_index("idx_roblox_session_teacher", "roblox_sessions", ["teacher_id"])
    op.create_index("idx_roblox_session_universe", "roblox_sessions", ["universe_id", "place_id"])
    op.create_index("idx_roblox_session_status", "roblox_sessions", ["status"])
    op.create_index("idx_roblox_session_active", "roblox_sessions", ["websocket_connection_active"])
    op.create_index("idx_roblox_session_last_activity", "roblox_sessions", ["last_activity_at"])

    # Create roblox_content table
    op.create_table(
        "roblox_content",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
            default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("lesson_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("template_id", postgresql.UUID(as_uuid=True)),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column(
            "content_type",
            postgresql.ENUM(
                "SCRIPT",
                "MODEL",
                "TERRAIN",
                "GUI",
                "ANIMATION",
                "SOUND",
                "TEXTURE",
                "MESH",
                name="robloxcontenttype",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column("version", sa.String(20), default="1.0.0"),
        sa.Column("place_id", sa.String(100)),
        sa.Column("asset_id", sa.String(100)),
        sa.Column("model_id", sa.String(100)),
        sa.Column("script_content", sa.Text()),
        sa.Column("content_data", postgresql.JSONB(), nullable=False),
        sa.Column("roblox_properties", postgresql.JSONB(), default=sa.text("'{}'::jsonb")),
        sa.Column("educational_metadata", postgresql.JSONB(), default=sa.text("'{}'::jsonb")),
        sa.Column("ai_generated", sa.Boolean(), default=True),
        sa.Column("ai_model", sa.String(100), default="gpt-4"),
        sa.Column("generation_parameters", postgresql.JSONB(), default=sa.text("'{}'::jsonb")),
        sa.Column("generation_prompt", sa.Text()),
        sa.Column("is_deployed", sa.Boolean(), default=False),
        sa.Column("deployed_at", sa.DateTime(timezone=True)),
        sa.Column("deployment_hash", sa.String(64)),
        sa.Column("usage_count", sa.Integer(), default=0),
        sa.Column("performance_metrics", postgresql.JSONB(), default=sa.text("'{}'::jsonb")),
        sa.Column("user_feedback", postgresql.JSONB(), default=sa.text("'{}'::jsonb")),
        sa.Column("coppa_compliant", sa.Boolean(), default=True),
        sa.Column("content_rating", sa.String(10), default="E"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True)),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["lesson_id"], ["lessons.id"]),
        sa.ForeignKeyConstraint(["template_id"], ["roblox_templates.id"]),
    )

    # Create indexes for roblox_content
    op.create_index("idx_roblox_content_lesson", "roblox_content", ["lesson_id"])
    op.create_index("idx_roblox_content_type", "roblox_content", ["content_type"])
    op.create_index("idx_roblox_content_deployed", "roblox_content", ["is_deployed"])
    op.create_index("idx_roblox_content_place", "roblox_content", ["place_id"])
    op.create_index("idx_roblox_content_version", "roblox_content", ["version"])

    # Create roblox_player_progress table
    op.create_table(
        "roblox_player_progress",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
            default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("session_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("student_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("lesson_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("roblox_user_id", sa.String(100), nullable=False),
        sa.Column("roblox_username", sa.String(100), nullable=False),
        sa.Column("progress_percentage", sa.Float(), default=0.0),
        sa.Column("checkpoints_completed", postgresql.JSONB(), default=sa.text("'[]'::jsonb")),
        sa.Column("objectives_met", postgresql.JSONB(), default=sa.text("'[]'::jsonb")),
        sa.Column("score", sa.Integer(), default=0),
        sa.Column("time_spent_seconds", sa.Integer(), default=0),
        sa.Column("actions_completed", sa.Integer(), default=0),
        sa.Column("mistakes_made", sa.Integer(), default=0),
        sa.Column("hints_used", sa.Integer(), default=0),
        sa.Column("current_position", postgresql.JSONB()),
        sa.Column("current_activity", sa.String(200)),
        sa.Column("last_interaction", sa.DateTime(timezone=True)),
        sa.Column("team_id", sa.String(100)),
        sa.Column("collaborative_actions", sa.Integer(), default=0),
        sa.Column("peer_interactions", sa.Integer(), default=0),
        sa.Column("difficulty_adjustments", postgresql.JSONB(), default=sa.text("'[]'::jsonb")),
        sa.Column("learning_path", postgresql.JSONB(), default=sa.text("'[]'::jsonb")),
        sa.Column("performance_trends", postgresql.JSONB(), default=sa.text("'{}'::jsonb")),
        sa.Column("age_verified", sa.Boolean(), default=False),
        sa.Column("parental_consent_given", sa.Boolean(), default=False),
        sa.Column("data_collection_consent", sa.Boolean(), default=False),
        sa.Column("joined_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("left_at", sa.DateTime(timezone=True)),
        sa.Column("session_duration_seconds", sa.Integer(), default=0),
        sa.Column("disconnections", sa.Integer(), default=0),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True)),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["session_id"], ["roblox_sessions.id"]),
        sa.ForeignKeyConstraint(["student_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["lesson_id"], ["lessons.id"]),
        sa.UniqueConstraint("session_id", "student_id", "roblox_user_id"),
        sa.CheckConstraint("progress_percentage >= 0 AND progress_percentage <= 100"),
        sa.CheckConstraint("score >= 0"),
        sa.CheckConstraint("time_spent_seconds >= 0"),
    )

    # Create indexes for roblox_player_progress
    op.create_index("idx_roblox_progress_session", "roblox_player_progress", ["session_id"])
    op.create_index("idx_roblox_progress_student", "roblox_player_progress", ["student_id"])
    op.create_index("idx_roblox_progress_lesson", "roblox_player_progress", ["lesson_id"])
    op.create_index("idx_roblox_progress_roblox_user", "roblox_player_progress", ["roblox_user_id"])

    # Create roblox_quiz_results table
    op.create_table(
        "roblox_quiz_results",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
            default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("session_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("player_progress_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("quiz_id", postgresql.UUID(as_uuid=True)),
        sa.Column("quiz_name", sa.String(200), nullable=False),
        sa.Column("quiz_type", sa.String(100), default="interactive"),
        sa.Column(
            "difficulty_level",
            postgresql.ENUM(
                "BEGINNER",
                "INTERMEDIATE",
                "ADVANCED",
                "EXPERT",
                name="difficultylevel",
                create_type=False,
            ),
            default="INTERMEDIATE",
        ),
        sa.Column("total_questions", sa.Integer(), nullable=False),
        sa.Column("correct_answers", sa.Integer(), default=0),
        sa.Column("incorrect_answers", sa.Integer(), default=0),
        sa.Column("skipped_questions", sa.Integer(), default=0),
        sa.Column("raw_score", sa.Float(), default=0.0),
        sa.Column("percentage_score", sa.Float(), default=0.0),
        sa.Column("weighted_score", sa.Float(), default=0.0),
        sa.Column("bonus_points", sa.Integer(), default=0),
        sa.Column("time_allocated_seconds", sa.Integer()),
        sa.Column("time_taken_seconds", sa.Integer()),
        sa.Column("average_time_per_question", sa.Float()),
        sa.Column("question_responses", postgresql.JSONB(), default=sa.text("'[]'::jsonb")),
        sa.Column("response_patterns", postgresql.JSONB(), default=sa.text("'{}'::jsonb")),
        sa.Column("learning_gaps", postgresql.JSONB(), default=sa.text("'[]'::jsonb")),
        sa.Column("in_game_location", postgresql.JSONB()),
        sa.Column("game_context", postgresql.JSONB(), default=sa.text("'{}'::jsonb")),
        sa.Column("interactive_elements", postgresql.JSONB(), default=sa.text("'[]'::jsonb")),
        sa.Column("difficulty_adjustments", postgresql.JSONB(), default=sa.text("'[]'::jsonb")),
        sa.Column("hints_provided", sa.Integer(), default=0),
        sa.Column("help_requests", sa.Integer(), default=0),
        sa.Column("improvement_from_previous", sa.Float()),
        sa.Column("consistency_score", sa.Float()),
        sa.Column("confidence_indicators", postgresql.JSONB(), default=sa.text("'{}'::jsonb")),
        sa.Column("completed", sa.Boolean(), default=False),
        sa.Column("passed", sa.Boolean(), default=False),
        sa.Column("retry_count", sa.Integer(), default=0),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["session_id"], ["roblox_sessions.id"]),
        sa.ForeignKeyConstraint(["player_progress_id"], ["roblox_player_progress.id"]),
        sa.ForeignKeyConstraint(["quiz_id"], ["quizzes.id"]),
        sa.CheckConstraint("percentage_score >= 0 AND percentage_score <= 100"),
        sa.CheckConstraint("correct_answers >= 0"),
        sa.CheckConstraint("total_questions > 0"),
    )

    # Create indexes for roblox_quiz_results
    op.create_index("idx_roblox_quiz_session", "roblox_quiz_results", ["session_id"])
    op.create_index("idx_roblox_quiz_player", "roblox_quiz_results", ["player_progress_id"])
    op.create_index("idx_roblox_quiz_performance", "roblox_quiz_results", ["percentage_score"])
    op.create_index("idx_roblox_quiz_completion", "roblox_quiz_results", ["completed", "passed"])

    # Create roblox_achievements table
    op.create_table(
        "roblox_achievements",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
            default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("session_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("student_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("base_achievement_id", postgresql.UUID(as_uuid=True)),
        sa.Column("achievement_name", sa.String(200), nullable=False),
        sa.Column(
            "achievement_type",
            postgresql.ENUM(
                "MILESTONE",
                "STREAK",
                "COMPLETION",
                "MASTERY",
                "SPECIAL",
                name="achievementtype",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column("description", sa.Text()),
        sa.Column("in_game_badge_id", sa.String(100)),
        sa.Column("roblox_asset_id", sa.String(100)),
        sa.Column("game_location_earned", postgresql.JSONB()),
        sa.Column("points_awarded", sa.Integer(), default=10),
        sa.Column("difficulty_multiplier", sa.Float(), default=1.0),
        sa.Column("rarity_bonus", sa.Integer(), default=0),
        sa.Column("trigger_conditions", postgresql.JSONB(), nullable=False),
        sa.Column("performance_context", postgresql.JSONB(), default=sa.text("'{}'::jsonb")),
        sa.Column("peer_comparison", postgresql.JSONB(), default=sa.text("'{}'::jsonb")),
        sa.Column("icon_url", sa.String(500)),
        sa.Column("badge_color", sa.String(7)),
        sa.Column("animation_data", postgresql.JSONB()),
        sa.Column("is_shareable", sa.Boolean(), default=True),
        sa.Column("shared_count", sa.Integer(), default=0),
        sa.Column("likes_received", sa.Integer(), default=0),
        sa.Column("current_progress", sa.Float(), default=100.0),
        sa.Column("milestone_data", postgresql.JSONB(), default=sa.text("'{}'::jsonb")),
        sa.Column("earned_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["session_id"], ["roblox_sessions.id"]),
        sa.ForeignKeyConstraint(["student_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["base_achievement_id"], ["achievements.id"]),
    )

    # Create indexes for roblox_achievements
    op.create_index("idx_roblox_achievement_session", "roblox_achievements", ["session_id"])
    op.create_index("idx_roblox_achievement_student", "roblox_achievements", ["student_id"])
    op.create_index("idx_roblox_achievement_type", "roblox_achievements", ["achievement_type"])
    op.create_index("idx_roblox_achievement_earned", "roblox_achievements", ["earned_at"])


def downgrade() -> None:
    """Rollback the migration."""
    # Drop tables in reverse order of dependencies
    op.drop_table("roblox_achievements")
    op.drop_table("roblox_quiz_results")
    op.drop_table("roblox_player_progress")
    op.drop_table("roblox_content")
    op.drop_table("roblox_sessions")
    op.drop_table("roblox_templates")

    # Drop custom enum types
    connection = op.get_bind()
    connection.execute(text("DROP TYPE IF EXISTS robloxcontenttype"))
    connection.execute(text("DROP TYPE IF EXISTS robloxsessionstatus"))
