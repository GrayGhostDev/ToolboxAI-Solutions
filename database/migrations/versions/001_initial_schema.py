"""Initial database schema

Revision ID: 001
Revises:
Create Date: 2025-09-07 12:00:00

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create initial database schema."""

    # Enable extensions
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
    op.execute('CREATE EXTENSION IF NOT EXISTS "pgcrypto"')
    op.execute('CREATE EXTENSION IF NOT EXISTS "pg_trgm"')

    # Create schema
    op.execute("CREATE SCHEMA IF NOT EXISTS toolboxai")

    # Create users table
    op.create_table(
        "users",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("uuid_generate_v4()"),
            nullable=False,
        ),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("username", sa.String(50), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("first_name", sa.String(100)),
        sa.Column("last_name", sa.String(100)),
        sa.Column("role", sa.String(20), nullable=False),
        sa.Column("status", sa.String(20), server_default="active"),
        sa.Column("avatar_url", sa.Text()),
        sa.Column("bio", sa.Text()),
        sa.Column("grade_level", sa.Integer()),
        sa.Column("school_id", postgresql.UUID(as_uuid=True)),
        sa.Column("schoology_id", sa.String(100)),
        sa.Column("canvas_id", sa.String(100)),
        sa.Column("google_id", sa.String(100)),
        sa.Column("moodle_id", sa.String(100)),
        sa.Column("preferences", postgresql.JSONB(), server_default="{}"),
        sa.Column(
            "notification_settings",
            postgresql.JSONB(),
            server_default='{"email": true, "in_app": true}',
        ),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")
        ),
        sa.Column("last_login_at", sa.DateTime(timezone=True)),
        sa.Column("email_verified_at", sa.DateTime(timezone=True)),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
        sa.UniqueConstraint("username"),
        sa.CheckConstraint("role IN ('student', 'educator', 'admin', 'parent')"),
        sa.CheckConstraint("status IN ('active', 'inactive', 'suspended', 'pending')"),
        schema="toolboxai",
    )

    # Create indexes for users table
    op.create_index("idx_users_email", "users", ["email"], schema="toolboxai")
    op.create_index("idx_users_username", "users", ["username"], schema="toolboxai")
    op.create_index("idx_users_role", "users", ["role"], schema="toolboxai")
    op.create_index("idx_users_school_id", "users", ["school_id"], schema="toolboxai")

    # Create user_sessions table
    op.create_table(
        "user_sessions",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("uuid_generate_v4()"),
            nullable=False,
        ),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("token_hash", sa.String(255), nullable=False),
        sa.Column("refresh_token_hash", sa.String(255)),
        sa.Column("ip_address", postgresql.INET()),
        sa.Column("user_agent", sa.Text()),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")
        ),
        sa.ForeignKeyConstraint(["user_id"], ["toolboxai.users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token_hash"),
        schema="toolboxai",
    )

    # Create courses table
    op.create_table(
        "courses",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("uuid_generate_v4()"),
            nullable=False,
        ),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("subject", sa.String(100), nullable=False),
        sa.Column("grade_level", sa.Integer()),
        sa.Column("educator_id", postgresql.UUID(as_uuid=True)),
        sa.Column("lms_platform", sa.String(50)),
        sa.Column("lms_course_id", sa.String(100)),
        sa.Column("sync_enabled", sa.Boolean(), server_default="false"),
        sa.Column("last_synced_at", sa.DateTime(timezone=True)),
        sa.Column("settings", postgresql.JSONB(), server_default="{}"),
        sa.Column("is_active", sa.Boolean(), server_default="true"),
        sa.Column("enrollment_code", sa.String(20)),
        sa.Column("max_students", sa.Integer(), server_default="50"),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")
        ),
        sa.Column("start_date", sa.Date()),
        sa.Column("end_date", sa.Date()),
        sa.ForeignKeyConstraint(["educator_id"], ["toolboxai.users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("enrollment_code"),
        schema="toolboxai",
    )

    # Create enrollments table
    op.create_table(
        "enrollments",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("uuid_generate_v4()"),
            nullable=False,
        ),
        sa.Column("course_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("student_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "enrolled_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")
        ),
        sa.Column("status", sa.String(20), server_default="active"),
        sa.Column("grade", sa.Numeric(5, 2)),
        sa.ForeignKeyConstraint(["course_id"], ["toolboxai.courses.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["student_id"], ["toolboxai.users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("course_id", "student_id"),
        sa.CheckConstraint("status IN ('active', 'completed', 'dropped', 'pending')"),
        schema="toolboxai",
    )

    # Create lessons table
    op.create_table(
        "lessons",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("uuid_generate_v4()"),
            nullable=False,
        ),
        sa.Column("course_id", postgresql.UUID(as_uuid=True)),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("learning_objectives", postgresql.ARRAY(sa.Text())),
        sa.Column("content_type", sa.String(50), nullable=False),
        sa.Column("content_data", postgresql.JSONB(), nullable=False),
        sa.Column("roblox_place_id", sa.String(100)),
        sa.Column("roblox_scripts", postgresql.JSONB()),
        sa.Column("environment_type", sa.String(50)),
        sa.Column("terrain_config", postgresql.JSONB()),
        sa.Column("duration_minutes", sa.Integer()),
        sa.Column("difficulty_level", sa.String(20)),
        sa.Column("order_index", sa.Integer(), server_default="0"),
        sa.Column("is_published", sa.Boolean(), server_default="false"),
        sa.Column("ai_generated", sa.Boolean(), server_default="false"),
        sa.Column("ai_model", sa.String(50)),
        sa.Column("ai_prompt", sa.Text()),
        sa.Column("generation_params", postgresql.JSONB()),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")
        ),
        sa.Column("published_at", sa.DateTime(timezone=True)),
        sa.ForeignKeyConstraint(["course_id"], ["toolboxai.courses.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint("difficulty_level IN ('easy', 'medium', 'hard', 'expert')"),
        schema="toolboxai",
    )

    # Create quizzes table
    op.create_table(
        "quizzes",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("uuid_generate_v4()"),
            nullable=False,
        ),
        sa.Column("lesson_id", postgresql.UUID(as_uuid=True)),
        sa.Column("course_id", postgresql.UUID(as_uuid=True)),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("quiz_type", sa.String(50), server_default="standard"),
        sa.Column("time_limit_minutes", sa.Integer()),
        sa.Column("passing_score", sa.Numeric(5, 2), server_default="70.0"),
        sa.Column("max_attempts", sa.Integer(), server_default="3"),
        sa.Column("shuffle_questions", sa.Boolean(), server_default="true"),
        sa.Column("shuffle_answers", sa.Boolean(), server_default="true"),
        sa.Column("ai_generated", sa.Boolean(), server_default="false"),
        sa.Column("generation_prompt", sa.Text()),
        sa.Column("is_published", sa.Boolean(), server_default="false"),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")
        ),
        sa.Column("available_from", sa.DateTime(timezone=True)),
        sa.Column("available_until", sa.DateTime(timezone=True)),
        sa.ForeignKeyConstraint(["lesson_id"], ["toolboxai.lessons.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["course_id"], ["toolboxai.courses.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint("quiz_type IN ('standard', 'timed', 'practice', 'exam')"),
        schema="toolboxai",
    )

    # Create quiz_questions table
    op.create_table(
        "quiz_questions",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("uuid_generate_v4()"),
            nullable=False,
        ),
        sa.Column("quiz_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("question_text", sa.Text(), nullable=False),
        sa.Column("question_type", sa.String(50), nullable=False),
        sa.Column("options", postgresql.JSONB()),
        sa.Column("correct_answer", postgresql.JSONB()),
        sa.Column("explanation", sa.Text()),
        sa.Column("points", sa.Numeric(5, 2), server_default="1.0"),
        sa.Column("partial_credit_allowed", sa.Boolean(), server_default="false"),
        sa.Column("image_url", sa.Text()),
        sa.Column("audio_url", sa.Text()),
        sa.Column("video_url", sa.Text()),
        sa.Column("order_index", sa.Integer(), server_default="0"),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")
        ),
        sa.ForeignKeyConstraint(["quiz_id"], ["toolboxai.quizzes.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint(
            "question_type IN ('multiple_choice', 'true_false', 'short_answer', 'essay', 'matching', 'ordering')"
        ),
        schema="toolboxai",
    )

    # Create quiz_attempts table
    op.create_table(
        "quiz_attempts",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("uuid_generate_v4()"),
            nullable=False,
        ),
        sa.Column("quiz_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("student_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("attempt_number", sa.Integer(), nullable=False, server_default="1"),
        sa.Column(
            "started_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.Column("time_spent_seconds", sa.Integer()),
        sa.Column("score", sa.Numeric(5, 2)),
        sa.Column("points_earned", sa.Numeric(10, 2)),
        sa.Column("points_possible", sa.Numeric(10, 2)),
        sa.Column("passed", sa.Boolean()),
        sa.Column("answers", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("feedback", postgresql.JSONB()),
        sa.Column("status", sa.String(20), server_default="in_progress"),
        sa.ForeignKeyConstraint(["quiz_id"], ["toolboxai.quizzes.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["student_id"], ["toolboxai.users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("quiz_id", "student_id", "attempt_number"),
        sa.CheckConstraint("status IN ('in_progress', 'completed', 'abandoned', 'submitted')"),
        schema="toolboxai",
    )

    # Create student_progress table
    op.create_table(
        "student_progress",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("uuid_generate_v4()"),
            nullable=False,
        ),
        sa.Column("student_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("course_id", postgresql.UUID(as_uuid=True)),
        sa.Column("lesson_id", postgresql.UUID(as_uuid=True)),
        sa.Column("completion_percentage", sa.Numeric(5, 2), server_default="0"),
        sa.Column("time_spent_minutes", sa.Integer(), server_default="0"),
        sa.Column("last_accessed_at", sa.DateTime(timezone=True)),
        sa.Column("average_score", sa.Numeric(5, 2)),
        sa.Column("quizzes_completed", sa.Integer(), server_default="0"),
        sa.Column("quizzes_passed", sa.Integer(), server_default="0"),
        sa.Column("progress_data", postgresql.JSONB(), server_default="{}"),
        sa.Column("checkpoints_completed", postgresql.JSONB(), server_default="[]"),
        sa.Column(
            "started_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")
        ),
        sa.ForeignKeyConstraint(["student_id"], ["toolboxai.users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["course_id"], ["toolboxai.courses.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["lesson_id"], ["toolboxai.lessons.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("student_id", "course_id", "lesson_id"),
        schema="toolboxai",
    )

    # Create achievements table
    op.create_table(
        "achievements",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("uuid_generate_v4()"),
            nullable=False,
        ),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("category", sa.String(50)),
        sa.Column("criteria_type", sa.String(50), nullable=False),
        sa.Column("criteria_value", postgresql.JSONB(), nullable=False),
        sa.Column("points", sa.Integer(), server_default="10"),
        sa.Column("badge_image_url", sa.Text()),
        sa.Column("badge_color", sa.String(7)),
        sa.Column("is_active", sa.Boolean(), server_default="true"),
        sa.Column("is_hidden", sa.Boolean(), server_default="false"),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")
        ),
        sa.PrimaryKeyConstraint("id"),
        schema="toolboxai",
    )

    # Create user_achievements table
    op.create_table(
        "user_achievements",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("uuid_generate_v4()"),
            nullable=False,
        ),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("achievement_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("progress", sa.Numeric(5, 2), server_default="0"),
        sa.Column("unlocked", sa.Boolean(), server_default="false"),
        sa.Column("unlocked_at", sa.DateTime(timezone=True)),
        sa.Column("metadata", postgresql.JSONB(), server_default="{}"),
        sa.ForeignKeyConstraint(["user_id"], ["toolboxai.users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["achievement_id"], ["toolboxai.achievements.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "achievement_id"),
        schema="toolboxai",
    )

    # Create analytics_events table
    op.create_table(
        "analytics_events",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("uuid_generate_v4()"),
            nullable=False,
        ),
        sa.Column("user_id", postgresql.UUID(as_uuid=True)),
        sa.Column("session_id", postgresql.UUID(as_uuid=True)),
        sa.Column("event_type", sa.String(100), nullable=False),
        sa.Column("event_category", sa.String(50)),
        sa.Column("event_data", postgresql.JSONB(), server_default="{}"),
        sa.Column("course_id", postgresql.UUID(as_uuid=True)),
        sa.Column("lesson_id", postgresql.UUID(as_uuid=True)),
        sa.Column("quiz_id", postgresql.UUID(as_uuid=True)),
        sa.Column("ip_address", postgresql.INET()),
        sa.Column("user_agent", sa.Text()),
        sa.Column("platform", sa.String(50)),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")
        ),
        sa.ForeignKeyConstraint(["user_id"], ["toolboxai.users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["course_id"], ["toolboxai.courses.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["lesson_id"], ["toolboxai.lessons.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["quiz_id"], ["toolboxai.quizzes.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        schema="toolboxai",
    )

    # Create content_generation_history table
    op.create_table(
        "content_generation_history",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("uuid_generate_v4()"),
            nullable=False,
        ),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("request_type", sa.String(50), nullable=False),
        sa.Column("request_data", postgresql.JSONB(), nullable=False),
        sa.Column("prompt", sa.Text()),
        sa.Column("response_data", postgresql.JSONB()),
        sa.Column("generated_content", sa.Text()),
        sa.Column("ai_model", sa.String(50)),
        sa.Column("tokens_used", sa.Integer()),
        sa.Column("generation_time_ms", sa.Integer()),
        sa.Column("status", sa.String(20), server_default="pending"),
        sa.Column("error_message", sa.Text()),
        sa.Column("lesson_id", postgresql.UUID(as_uuid=True)),
        sa.Column("quiz_id", postgresql.UUID(as_uuid=True)),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.ForeignKeyConstraint(["user_id"], ["toolboxai.users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["lesson_id"], ["toolboxai.lessons.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["quiz_id"], ["toolboxai.quizzes.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint("status IN ('pending', 'processing', 'completed', 'failed')"),
        schema="toolboxai",
    )

    # Create system_config table
    op.create_table(
        "system_config",
        sa.Column("key", sa.String(100), nullable=False),
        sa.Column("value", postgresql.JSONB(), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")
        ),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True)),
        sa.ForeignKeyConstraint(["updated_by"], ["toolboxai.users.id"]),
        sa.PrimaryKeyConstraint("key"),
        schema="toolboxai",
    )

    # Create audit_log table
    op.create_table(
        "audit_log",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("uuid_generate_v4()"),
            nullable=False,
        ),
        sa.Column("user_id", postgresql.UUID(as_uuid=True)),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("entity_type", sa.String(50)),
        sa.Column("entity_id", postgresql.UUID(as_uuid=True)),
        sa.Column("old_values", postgresql.JSONB()),
        sa.Column("new_values", postgresql.JSONB()),
        sa.Column("ip_address", postgresql.INET()),
        sa.Column("user_agent", sa.Text()),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")
        ),
        sa.ForeignKeyConstraint(["user_id"], ["toolboxai.users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        schema="toolboxai",
    )

    # Create update_updated_at_column function
    op.execute(
        """
        CREATE OR REPLACE FUNCTION toolboxai.update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = CURRENT_TIMESTAMP;
            RETURN NEW;
        END;
        $$ language 'plpgsql';
    """
    )

    # Create triggers for updated_at columns
    tables_with_updated_at = [
        "users",
        "courses",
        "lessons",
        "quizzes",
        "quiz_questions",
        "student_progress",
    ]

    for table in tables_with_updated_at:
        op.execute(
            f"""
            CREATE TRIGGER update_{table}_updated_at 
            BEFORE UPDATE ON toolboxai.{table}
            FOR EACH ROW EXECUTE FUNCTION toolboxai.update_updated_at_column();
        """
        )

    # Insert default system configuration
    op.execute(
        """
        INSERT INTO toolboxai.system_config (key, value, description) VALUES
        ('max_file_size', '{"value": 10485760}', 'Maximum file upload size in bytes'),
        ('session_timeout', '{"value": 3600}', 'Session timeout in seconds'),
        ('maintenance_mode', '{"value": false}', 'System maintenance mode flag'),
        ('ai_models', '{"models": ["gpt-4", "gpt-3.5-turbo"]}', 'Available AI models'),
        ('supported_lms', '{"platforms": ["schoology", "canvas", "google_classroom", "moodle"]}', 'Supported LMS platforms')
        ON CONFLICT (key) DO NOTHING;
    """
    )

    # Insert default achievements
    op.execute(
        """
        INSERT INTO toolboxai.achievements (name, description, category, criteria_type, criteria_value, points) VALUES
        ('First Steps', 'Complete your first lesson', 'beginner', 'lessons_completed', '{"count": 1}', 10),
        ('Quiz Master', 'Score 100% on a quiz', 'performance', 'perfect_quiz', '{"score": 100}', 25),
        ('Dedicated Learner', 'Study for 7 days in a row', 'engagement', 'streak_days', '{"days": 7}', 50),
        ('Team Player', 'Join a study group', 'collaboration', 'group_joined', '{"count": 1}', 15),
        ('Knowledge Seeker', 'Complete 10 lessons', 'progress', 'lessons_completed', '{"count": 10}', 30);
    """
    )


def downgrade() -> None:
    """Drop all database objects."""

    # Drop schema cascade (removes all tables, functions, etc.)
    op.execute("DROP SCHEMA IF EXISTS toolboxai CASCADE")

    # Drop extensions if needed
    # op.execute('DROP EXTENSION IF EXISTS "uuid-ossp"')
    # op.execute('DROP EXTENSION IF EXISTS "pgcrypto"')
    # op.execute('DROP EXTENSION IF EXISTS "pg_trgm"')
