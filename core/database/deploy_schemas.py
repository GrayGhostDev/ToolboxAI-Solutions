#!/usr/bin/env python3
"""
Database Schema Deployment Script for ToolboxAI

This script deploys all database schemas to the appropriate databases.
"""

import os
import sys
from pathlib import Path
from typing import List, Dict, Any

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.database.connection_manager import db_manager, get_session
from sqlalchemy import text


class SchemaDeployer:
    """Deploys database schemas to all databases."""

    def __init__(self):
        """Initialize schema deployer."""
        self.project_root = project_root
        self.database_dir = self.project_root / "database"
        self.schemas_dir = self.database_dir / "schemas"

        # Database to schema mapping
        self.database_schemas = {
            "education": [
                "01_core_schema.sql",
                "02_ai_agents_schema.sql",
                "03_lms_integration_schema.sql",
                "04_analytics_schema.sql",
            ],
            "ghost": ["01_core_schema.sql"],  # Ghost backend uses core schema
            "roblox": ["02_ai_agents_schema.sql"],  # Roblox uses AI agents schema
            "mcp": ["02_ai_agents_schema.sql"],  # MCP uses AI agents schema
            "development": [
                "01_core_schema.sql",
                "02_ai_agents_schema.sql",
                "03_lms_integration_schema.sql",
                "04_analytics_schema.sql",
            ],
        }

    def deploy_all_schemas(self) -> bool:
        """Deploy schemas to all databases."""
        print("🚀 Deploying Database Schemas")
        print("=" * 50)

        try:
            # Initialize database connections
            db_manager.initialize()

            success = True

            for database_name, schema_files in self.database_schemas.items():
                print(f"\n📊 Deploying schemas to {database_name} database...")

                if not self._deploy_schemas_to_database(database_name, schema_files):
                    success = False
                    print(f"❌ Failed to deploy schemas to {database_name}")
                else:
                    print(f"✅ Successfully deployed schemas to {database_name}")

            if success:
                print("\n🎉 All schemas deployed successfully!")
            else:
                print("\n⚠️  Some schemas failed to deploy. Check the errors above.")

            return success

        except Exception as e:
            print(f"\n❌ Schema deployment failed: {e}")
            return False

    def _deploy_schemas_to_database(self, database_name: str, schema_files: List[str]) -> bool:
        """Deploy schemas to a specific database."""
        try:
            with get_session(database_name) as session:
                for schema_file in schema_files:
                    schema_path = self.schemas_dir / schema_file

                    if not schema_path.exists():
                        print(f"⚠️  Schema file {schema_file} not found, skipping...")
                        continue

                    print(f"📝 Deploying {schema_file}...")

                    with open(schema_path, "r") as f:
                        schema_sql = f.read()

                    # Split by semicolon and execute each statement
                    statements = [stmt.strip() for stmt in schema_sql.split(";") if stmt.strip()]

                    for statement in statements:
                        if statement:
                            try:
                                session.execute(text(statement))
                            except Exception as e:
                                # Skip errors for existing objects
                                if (
                                    "already exists" in str(e).lower()
                                    or "duplicate" in str(e).lower()
                                ):
                                    print(f"ℹ️  Skipping existing object: {e}")
                                    continue
                                else:
                                    print(f"❌ Error executing statement: {e}")
                                    print(f"Statement: {statement[:100]}...")
                                    return False

                    session.commit()
                    print(f"✅ {schema_file} deployed successfully")

            return True

        except Exception as e:
            print(f"❌ Failed to deploy schemas to {database_name}: {e}")
            return False

    def create_initial_data(self) -> bool:
        """Create initial data for all databases."""
        print("\n🌱 Creating initial data...")

        try:
            # Create initial data for education database
            with get_session("education") as session:
                self._create_initial_education_data(session)

            print("✅ Initial data created successfully")
            return True

        except Exception as e:
            print(f"❌ Failed to create initial data: {e}")
            return False

    def _create_initial_education_data(self, session):
        """Create initial data for education database."""
        # Create default roles
        roles_sql = """
        INSERT INTO roles (name, description, permissions) VALUES
        ('admin', 'System Administrator', '{"all": true}'),
        ('teacher', 'Teacher', '{"content": true, "students": true, "reports": true}'),
        ('student', 'Student', '{"content": true, "progress": true}'),
        ('parent', 'Parent', '{"children": true, "progress": true}')
        ON CONFLICT (name) DO NOTHING;
        """

        # Create default learning objectives
        objectives_sql = """
        INSERT INTO learning_objectives (title, description, subject, grade_level, standards) VALUES
        ('Basic Math Operations', 'Learn addition, subtraction, multiplication, and division', 'Mathematics', 'Elementary', '{"CCSS": "2.OA.A.1"}'),
        ('Reading Comprehension', 'Understand and analyze written text', 'English Language Arts', 'Elementary', '{"CCSS": "RL.3.1"}'),
        ('Scientific Method', 'Learn the process of scientific inquiry', 'Science', 'Middle School', '{"NGSS": "MS-PS1-1"}'),
        ('World History', 'Understand major historical events and their impact', 'Social Studies', 'High School', '{"NCSS": "D2.His.1.9-12"}')
        ON CONFLICT (title) DO NOTHING;
        """

        # Create default achievements
        achievements_sql = """
        INSERT INTO achievements (name, description, type, points, icon_url) VALUES
        ('First Steps', 'Complete your first lesson', 'milestone', 10, '/icons/first-steps.png'),
        ('Quiz Master', 'Score 100% on a quiz', 'performance', 25, '/icons/quiz-master.png'),
        ('Streak Keeper', 'Maintain a 7-day learning streak', 'consistency', 50, '/icons/streak.png'),
        ('Content Creator', 'Create your first educational content', 'creative', 30, '/icons/creator.png'),
        ('Team Player', 'Collaborate with other students', 'social', 20, '/icons/team.png')
        ON CONFLICT (name) DO NOTHING;
        """

        # Create default leaderboards
        leaderboards_sql = """
        INSERT INTO leaderboards (name, description, type, scope, criteria) VALUES
        ('Weekly Top Performers', 'Top students by weekly progress', 'performance', 'global', '{"period": "weekly", "metric": "xp"}'),
        ('Quiz Champions', 'Students with highest quiz scores', 'academic', 'global', '{"metric": "quiz_average"}'),
        ('Most Helpful', 'Students who help others the most', 'social', 'global', '{"metric": "help_count"}'),
        ('Class Leaders', 'Top performers in each class', 'performance', 'class', '{"metric": "xp", "scope": "class"}')
        ON CONFLICT (name) DO NOTHING;
        """

        # Execute all SQL statements
        for sql in [roles_sql, objectives_sql, achievements_sql, leaderboards_sql]:
            try:
                session.execute(text(sql))
            except Exception as e:
                print(f"ℹ️  Skipping existing data: {e}")

        session.commit()


def main():
    """Main function."""
    deployer = SchemaDeployer()

    # Deploy schemas
    if deployer.deploy_all_schemas():
        # Create initial data
        deployer.create_initial_data()
        print("\n🎉 Database setup completed successfully!")
        return True
    else:
        print("\n❌ Database setup failed!")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
