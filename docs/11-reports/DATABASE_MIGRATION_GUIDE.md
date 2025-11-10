# Database Migration Scripts

## Alembic Migration Setup

### Initial Database Schema Migration

```bash
# Generate migration
cd apps/backend
alembic revision -m "Initial schema - users, courses, lessons, analytics"
```

### Migration File

```python
# database/migrations/versions/001_initial_schema.py

"""Initial schema - users, courses, lessons, analytics

Revision ID: 001_initial
Revises: 
Create Date: 2025-11-10

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '001_initial'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Tenants table
    op.create_table(
        'tenants',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('slug', sa.String(100), nullable=False),
        sa.Column('subscription_tier', sa.String(50)),
        sa.Column('settings', postgresql.JSONB()),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('slug')
    )
    
    # Users table
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('clerk_user_id', sa.String(255), nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('username', sa.String(50)),
        sa.Column('full_name', sa.String(255)),
        sa.Column('role', sa.String(50), nullable=False),
        sa.Column('tenant_id', sa.Integer()),
        sa.Column('avatar_url', sa.String(500)),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('metadata', postgresql.JSONB()),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('clerk_user_id'),
        sa.UniqueConstraint('email'),
        sa.UniqueConstraint('username')
    )
    
    # Courses table
    op.create_table(
        'courses',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('description', sa.Text()),
        sa.Column('grade_level', sa.String(50)),
        sa.Column('subject', sa.String(100)),
        sa.Column('difficulty', sa.String(20)),
        sa.Column('thumbnail_url', sa.String(500)),
        sa.Column('created_by_id', sa.Integer()),
        sa.Column('tenant_id', sa.Integer()),
        sa.Column('tags', postgresql.ARRAY(sa.String())),
        sa.Column('is_published', sa.Boolean(), default=False),
        sa.Column('metadata', postgresql.JSONB()),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['created_by_id'], ['users.id']),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id']),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Lessons table
    op.create_table(
        'lessons',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('course_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('description', sa.Text()),
        sa.Column('content', sa.Text()),
        sa.Column('order_index', sa.Integer()),
        sa.Column('duration_minutes', sa.Integer()),
        sa.Column('learning_objectives', postgresql.ARRAY(sa.String())),
        sa.Column('metadata', postgresql.JSONB()),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['course_id'], ['courses.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Student Progress table
    op.create_table(
        'student_progress',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('course_id', sa.Integer(), nullable=False),
        sa.Column('lesson_id', sa.Integer()),
        sa.Column('completion_percentage', sa.Float(), default=0.0),
        sa.Column('time_spent_seconds', sa.Integer(), default=0),
        sa.Column('last_accessed', sa.DateTime()),
        sa.Column('metadata', postgresql.JSONB()),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['course_id'], ['courses.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['lesson_id'], ['lessons.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'course_id', 'lesson_id', name='unique_progress')
    )
    
    # Assessments table
    op.create_table(
        'assessments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('lesson_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('assessment_type', sa.String(50)),
        sa.Column('total_points', sa.Integer()),
        sa.Column('passing_score', sa.Integer()),
        sa.Column('questions', postgresql.JSONB()),
        sa.Column('metadata', postgresql.JSONB()),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['lesson_id'], ['lessons.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Assessment Results table
    op.create_table(
        'assessment_results',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('assessment_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('score', sa.Integer()),
        sa.Column('percentage', sa.Float()),
        sa.Column('time_taken_seconds', sa.Integer()),
        sa.Column('answers', postgresql.JSONB()),
        sa.Column('feedback', postgresql.JSONB()),
        sa.Column('submitted_at', sa.DateTime(), server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['assessment_id'], ['assessments.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Roblox Players table
    op.create_table(
        'roblox_players',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('roblox_user_id', sa.BigInteger(), nullable=False),
        sa.Column('username', sa.String(50)),
        sa.Column('display_name', sa.String(100)),
        sa.Column('avatar_url', sa.String(500)),
        sa.Column('join_date', sa.DateTime()),
        sa.Column('last_sync', sa.DateTime()),
        sa.Column('metadata', postgresql.JSONB()),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id'),
        sa.UniqueConstraint('roblox_user_id')
    )
    
    # Game Sessions table
    op.create_table(
        'game_sessions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('player_id', sa.Integer(), nullable=False),
        sa.Column('game_id', sa.String(100)),
        sa.Column('started_at', sa.DateTime()),
        sa.Column('ended_at', sa.DateTime()),
        sa.Column('duration_seconds', sa.Integer()),
        sa.Column('events_count', sa.Integer(), default=0),
        sa.Column('metadata', postgresql.JSONB()),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['player_id'], ['roblox_players.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Agent Tasks table
    op.create_table(
        'agent_tasks',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('agent_type', sa.String(50), nullable=False),
        sa.Column('task_type', sa.String(50), nullable=False),
        sa.Column('input_data', postgresql.JSONB()),
        sa.Column('output_data', postgresql.JSONB()),
        sa.Column('status', sa.String(20), default='pending'),
        sa.Column('error_message', sa.Text()),
        sa.Column('user_id', sa.Integer()),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()')),
        sa.Column('started_at', sa.DateTime()),
        sa.Column('completed_at', sa.DateTime()),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Subscriptions table
    op.create_table(
        'subscriptions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer()),
        sa.Column('tenant_id', sa.Integer()),
        sa.Column('stripe_customer_id', sa.String(255)),
        sa.Column('stripe_subscription_id', sa.String(255)),
        sa.Column('plan_name', sa.String(100)),
        sa.Column('status', sa.String(50)),
        sa.Column('current_period_start', sa.DateTime()),
        sa.Column('current_period_end', sa.DateTime()),
        sa.Column('metadata', postgresql.JSONB()),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes
    op.create_index('idx_users_clerk_id', 'users', ['clerk_user_id'])
    op.create_index('idx_users_tenant', 'users', ['tenant_id'])
    op.create_index('idx_users_role', 'users', ['role'])
    op.create_index('idx_courses_tenant', 'courses', ['tenant_id'])
    op.create_index('idx_courses_published', 'courses', ['is_published'])
    op.create_index('idx_lessons_course', 'lessons', ['course_id'])
    op.create_index('idx_progress_user', 'student_progress', ['user_id'])
    op.create_index('idx_progress_course', 'student_progress', ['course_id'])
    op.create_index('idx_progress_lesson', 'student_progress', ['lesson_id'])
    op.create_index('idx_assessments_lesson', 'assessments', ['lesson_id'])
    op.create_index('idx_assessment_results_user', 'assessment_results', ['user_id'])
    op.create_index('idx_assessment_results_assessment', 'assessment_results', ['assessment_id'])
    op.create_index('idx_roblox_user', 'roblox_players', ['user_id'])
    op.create_index('idx_roblox_roblox_id', 'roblox_players', ['roblox_user_id'])
    op.create_index('idx_game_sessions_player', 'game_sessions', ['player_id'])
    op.create_index('idx_agent_tasks_user', 'agent_tasks', ['user_id'])
    op.create_index('idx_agent_tasks_status', 'agent_tasks', ['status'])
    op.create_index('idx_agent_tasks_type', 'agent_tasks', ['agent_type', 'task_type'])
    op.create_index('idx_subscriptions_user', 'subscriptions', ['user_id'])
    op.create_index('idx_subscriptions_tenant', 'subscriptions', ['tenant_id'])
    op.create_index('idx_subscriptions_stripe_customer', 'subscriptions', ['stripe_customer_id'])


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_table('subscriptions')
    op.drop_table('agent_tasks')
    op.drop_table('game_sessions')
    op.drop_table('roblox_players')
    op.drop_table('assessment_results')
    op.drop_table('assessments')
    op.drop_table('student_progress')
    op.drop_table('lessons')
    op.drop_table('courses')
    op.drop_table('users')
    op.drop_table('tenants')
```

## Running Migrations

```bash
# Apply migrations
cd apps/backend
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# View migration history
alembic history

# Create new migration
alembic revision -m "description of changes"
```

## Seed Data Script

```python
# scripts/database/seed_data.py

"""
Seed database with initial data for development/testing
"""

import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from database.models import *
from apps.backend.core.config import settings
import bcrypt

async def seed_database():
    engine = create_async_engine(settings.DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        # Create default tenant
        tenant = Tenant(
            name="Demo School",
            slug="demo-school",
            subscription_tier="pro",
            settings={"features": ["ai_tutor", "roblox", "analytics"]}
        )
        session.add(tenant)
        await session.flush()
        
        # Create sample users
        admin = User(
            clerk_user_id="admin_clerk_id",
            email="admin@demo.com",
            username="admin",
            full_name="Admin User",
            role="admin",
            tenant_id=tenant.id,
            is_active=True
        )
        
        educator = User(
            clerk_user_id="educator_clerk_id",
            email="educator@demo.com",
            username="educator",
            full_name="John Educator",
            role="educator",
            tenant_id=tenant.id,
            is_active=True
        )
        
        student = User(
            clerk_user_id="student_clerk_id",
            email="student@demo.com",
            username="student",
            full_name="Jane Student",
            role="student",
            tenant_id=tenant.id,
            is_active=True
        )
        
        session.add_all([admin, educator, student])
        await session.flush()
        
        # Create sample course
        course = Course(
            title="Introduction to Mathematics",
            description="Learn fundamental math concepts",
            grade_level="6th",
            subject="Mathematics",
            difficulty="beginner",
            created_by_id=educator.id,
            tenant_id=tenant.id,
            tags=["math", "fundamentals", "6th grade"],
            is_published=True
        )
        session.add(course)
        await session.flush()
        
        # Create sample lessons
        lessons = [
            Lesson(
                course_id=course.id,
                title="Addition and Subtraction",
                description="Learn basic arithmetic operations",
                content="<p>Introduction to addition and subtraction...</p>",
                order_index=1,
                duration_minutes=30,
                learning_objectives=["Understand addition", "Practice subtraction"]
            ),
            Lesson(
                course_id=course.id,
                title="Multiplication Basics",
                description="Introduction to multiplication",
                content="<p>Learn multiplication tables...</p>",
                order_index=2,
                duration_minutes=45,
                learning_objectives=["Learn times tables", "Understand multiplication"]
            )
        ]
        session.add_all(lessons)
        
        await session.commit()
        print("✅ Database seeded successfully!")

if __name__ == "__main__":
    asyncio.run(seed_database())
```

## Usage

```bash
# Run seed script
python scripts/database/seed_data.py
```
