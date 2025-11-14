#!/usr/bin/env python3
"""
Create Initial Data Script for ToolboxAI

This script creates initial test data for all databases.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import text

from database import get_session


def create_initial_data():
    """Create initial data for all databases."""
    print("🌱 Creating Initial Data for ToolboxAI")
    print("=" * 50)

    try:
        # Create initial data for education database
        with get_session("education") as session:
            print("📊 Creating data for education database...")

            # Create test user
            user_sql = """
            INSERT INTO users (username, email, password_hash, first_name, last_name, role, is_active, is_verified)
            VALUES ('testuser', 'test@example.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4J/8KzKz2K', 'Test', 'User', 'teacher', true, true)
            ON CONFLICT (email) DO NOTHING;
            """

            # Create AI agents
            ai_agents_sql = """
            INSERT INTO ai_agents (name, agent_type, description, version, model_config, capabilities, is_active)
            VALUES
            ('supervisor', 'supervisor', 'Main orchestration agent', '1.0.0', '{"model": "gpt-4"}', ARRAY['["orchestration", "task_management", "workflow_coordination"]'::jsonb], true),
            ('content', 'content_generator', 'Educational content generation', '1.0.0', '{"model": "gpt-4"}', ARRAY['["content_creation", "curriculum_alignment"]'::jsonb], true),
            ('quiz', 'quiz_generator', 'Quiz and assessment creation', '1.0.0', '{"model": "gpt-4"}', ARRAY['["quiz_creation", "assessment_design"]'::jsonb], true),
            ('terrain', 'terrain_generator', 'Roblox terrain generation', '1.0.0', '{"model": "gpt-4"}', ARRAY['["terrain_creation", "environment_design"]'::jsonb], true),
            ('script', 'script_generator', 'Lua script generation', '1.0.0', '{"model": "gpt-4"}', ARRAY['["script_creation", "code_generation"]'::jsonb], true),
            ('review', 'review_agent', 'Content review and validation', '1.0.0', '{"model": "gpt-4"}', ARRAY['["content_review", "quality_assurance"]'::jsonb], true)
            ON CONFLICT (name) DO NOTHING;
            """

            # Create achievements
            achievements_sql = """
            INSERT INTO achievements (name, description, type, points, icon_url)
            VALUES
            ('First Steps', 'Complete your first lesson', 'milestone', 10, '/icons/first-steps.png'),
            ('Quiz Master', 'Score 100% on a quiz', 'performance', 25, '/icons/quiz-master.png'),
            ('Streak Keeper', 'Maintain a 7-day learning streak', 'consistency', 50, '/icons/streak.png'),
            ('Content Creator', 'Create your first educational content', 'creative', 30, '/icons/creator.png'),
            ('Team Player', 'Collaborate with other students', 'social', 20, '/icons/team.png')
            ON CONFLICT (name) DO NOTHING;
            """

            # Create leaderboards
            leaderboards_sql = """
            INSERT INTO leaderboards (name, description, type, scope, criteria)
            VALUES
            ('Weekly Top Performers', 'Top students by weekly progress', 'performance', 'global', '{"period": "weekly", "metric": "xp"}'),
            ('Quiz Champions', 'Students with highest quiz scores', 'academic', 'global', '{"metric": "quiz_average"}'),
            ('Most Helpful', 'Students who help others the most', 'social', 'global', '{"metric": "help_count"}'),
            ('Class Leaders', 'Top performers in each class', 'performance', 'class', '{"metric": "xp", "scope": "class"}')
            ON CONFLICT (name) DO NOTHING;
            """

            # Execute all SQL statements
            for sql_name, sql in [
                ("User", user_sql),
                ("AI Agents", ai_agents_sql),
                ("Achievements", achievements_sql),
                ("Leaderboards", leaderboards_sql),
            ]:
                try:
                    session.execute(text(sql))
                    print(f"✅ {sql_name} data created")
                except Exception as e:
                    print(f"ℹ️  {sql_name} data: {e}")

            session.commit()
            print("✅ Education database initial data created successfully")

        print("\n🎉 Initial data creation completed!")
        return True

    except Exception as e:
        print(f"❌ Failed to create initial data: {e}")
        return False


if __name__ == "__main__":
    success = create_initial_data()
    sys.exit(0 if success else 1)
