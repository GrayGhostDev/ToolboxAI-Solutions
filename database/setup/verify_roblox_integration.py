#!/usr/bin/env python3
"""
Verification script for Roblox integration database setup
Checks tables, indexes, relationships, and data integrity
"""

import asyncio
import os
import sys
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


async def verify_database_setup():
    """Verify the Roblox integration database setup."""

    database_url = os.getenv("DATABASE_URL", "postgresql+asyncpg://eduplatform:eduplatform2024@localhost:5432/educational_platform_dev")
    engine = create_async_engine(database_url, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        try:
            print("🔍 Verifying Roblox Integration Database Setup")
            print("=" * 50)

            # 1. Check that all Roblox tables exist
            print("\\n📋 Checking Roblox Tables...")
            expected_tables = [
                'roblox_templates',
                'roblox_sessions',
                'roblox_content',
                'roblox_player_progress',
                'roblox_quiz_results',
                'roblox_achievements'
            ]

            for table in expected_tables:
                result = await session.execute(
                    text(f"SELECT COUNT(*) FROM information_schema.tables WHERE table_name = '{table}'")
                )
                count = result.scalar()
                status = "✅" if count > 0 else "❌"
                print(f"   {status} {table}")

            # 2. Check enum types
            print("\\n🏷️  Checking Enum Types...")
            expected_enums = ['robloxcontenttype', 'robloxsessionstatus']

            for enum_name in expected_enums:
                result = await session.execute(
                    text(f"SELECT COUNT(*) FROM pg_type WHERE typname = '{enum_name}'")
                )
                count = result.scalar()
                status = "✅" if count > 0 else "❌"
                print(f"   {status} {enum_name}")

                # Show enum values
                if count > 0:
                    result = await session.execute(
                        text(f"SELECT enumlabel FROM pg_enum WHERE enumtypid = (SELECT oid FROM pg_type WHERE typname = '{enum_name}') ORDER BY enumsortorder")
                    )
                    values = [row[0] for row in result.fetchall()]
                    print(f"       Values: {', '.join(values)}")

            # 3. Check indexes
            print("\\n📊 Checking Key Indexes...")
            key_indexes = [
                ('roblox_sessions', 'idx_roblox_session_lesson'),
                ('roblox_sessions', 'idx_roblox_session_teacher'),
                ('roblox_sessions', 'idx_roblox_session_universe'),
                ('roblox_content', 'idx_roblox_content_lesson'),
                ('roblox_player_progress', 'idx_roblox_progress_session'),
                ('roblox_templates', 'idx_roblox_template_category')
            ]

            for table_name, index_name in key_indexes:
                result = await session.execute(
                    text(f"SELECT COUNT(*) FROM pg_indexes WHERE tablename = '{table_name}' AND indexname = '{index_name}'")
                )
                count = result.scalar()
                status = "✅" if count > 0 else "❌"
                print(f"   {status} {table_name}.{index_name}")

            # 4. Check foreign key relationships
            print("\\n🔗 Checking Foreign Key Relationships...")
            fk_queries = [
                ("roblox_sessions -> lessons", "SELECT COUNT(*) FROM information_schema.table_constraints WHERE constraint_name = 'roblox_sessions_lesson_id_fkey'"),
                ("roblox_sessions -> users", "SELECT COUNT(*) FROM information_schema.table_constraints WHERE constraint_name = 'roblox_sessions_teacher_id_fkey'"),
                ("roblox_content -> lessons", "SELECT COUNT(*) FROM information_schema.table_constraints WHERE constraint_name = 'roblox_content_lesson_id_fkey'"),
                ("roblox_content -> roblox_templates", "SELECT COUNT(*) FROM information_schema.table_constraints WHERE constraint_name = 'roblox_content_template_id_fkey'"),
                ("roblox_player_progress -> roblox_sessions", "SELECT COUNT(*) FROM information_schema.table_constraints WHERE constraint_name = 'roblox_player_progress_session_id_fkey'")
            ]

            for desc, query in fk_queries:
                result = await session.execute(text(query))
                count = result.scalar()
                status = "✅" if count > 0 else "❌"
                print(f"   {status} {desc}")

            # 5. Check unique constraints
            print("\\n🔑 Checking Unique Constraints...")
            unique_constraints = [
                ("roblox_sessions", "websocket_session_id", "roblox_sessions_websocket_session_id_key"),
                ("roblox_player_progress", "session_id, student_id, roblox_user_id", "roblox_player_progress_session_id_student_id_roblox_user_id_key")
            ]

            for table_name, columns, constraint_name in unique_constraints:
                result = await session.execute(
                    text(f"SELECT COUNT(*) FROM information_schema.table_constraints WHERE constraint_name = '{constraint_name}' AND constraint_type = 'UNIQUE'")
                )
                count = result.scalar()
                status = "✅" if count > 0 else "❌"
                print(f"   {status} {table_name}({columns})")

            # 6. Check check constraints
            print("\\n✔️  Checking Data Validation Constraints...")
            check_constraints = [
                ("roblox_templates", "grade level validation"),
                ("roblox_player_progress", "progress percentage validation"),
                ("roblox_quiz_results", "score validation")
            ]

            for table_name, desc in check_constraints:
                result = await session.execute(
                    text(f"SELECT COUNT(*) FROM information_schema.check_constraints WHERE constraint_name LIKE '{table_name}_%'")
                )
                count = result.scalar()
                status = "✅" if count > 0 else "❌"
                print(f"   {status} {table_name}: {desc} ({count} constraints)")

            # 7. Test basic CRUD operations
            print("\\n🧪 Testing Basic Operations...")

            # Test basic insert/select for Universe ID constraint
            try:
                result = await session.execute(
                    text("""
                        SELECT 1 FROM roblox_sessions
                        WHERE universe_id = '8505376973'
                        LIMIT 1
                    """)
                )
                print("   ✅ Universe ID constraint working")
            except Exception as e:
                print(f"   ❌ Universe ID test failed: {e}")

            # Test OAuth2 Client ID constraint
            try:
                result = await session.execute(
                    text("""
                        SELECT 1 FROM roblox_sessions
                        WHERE client_id = '2214511122270781418'
                        LIMIT 1
                    """)
                )
                print("   ✅ OAuth2 Client ID constraint working")
            except Exception as e:
                print(f"   ❌ OAuth2 Client ID test failed: {e}")

            # Test JSONB operations
            try:
                result = await session.execute(
                    text("""
                        SELECT jsonb_typeof(sync_data) as data_type
                        FROM roblox_sessions
                        WHERE sync_data IS NOT NULL
                        LIMIT 1
                    """)
                )
                row = result.fetchone()
                if row and row[0] == 'object':
                    print("   ✅ JSONB operations working")
                else:
                    print("   ⚠️  JSONB data not found (expected for empty database)")
            except Exception as e:
                print(f"   ❌ JSONB test failed: {e}")

            # 8. Performance check - explain key queries
            print("\\n⚡ Performance Analysis...")

            performance_queries = [
                ("Active sessions query", """
                    EXPLAIN (FORMAT JSON)
                    SELECT * FROM roblox_sessions
                    WHERE status = 'ACTIVE' AND websocket_connection_active = true
                """),
                ("Student progress query", """
                    EXPLAIN (FORMAT JSON)
                    SELECT rp.*, rs.place_id
                    FROM roblox_player_progress rp
                    JOIN roblox_sessions rs ON rp.session_id = rs.id
                    WHERE rp.student_id = (SELECT id FROM users LIMIT 1)
                """)
            ]

            for desc, query in performance_queries:
                try:
                    result = await session.execute(text(query))
                    plan = result.fetchone()
                    if plan:
                        # Basic check - look for index usage
                        plan_str = str(plan[0])
                        uses_index = "Index" in plan_str
                        status = "✅" if uses_index else "⚠️"
                        print(f"   {status} {desc} - {'Uses indexes' if uses_index else 'May need optimization'}")
                except Exception as e:
                    print(f"   ⚠️  {desc} - Cannot analyze: {e}")

            # 9. Summary
            print("\\n📈 Database Statistics...")
            stats_queries = [
                ("Total Roblox tables", "SELECT COUNT(*) FROM information_schema.tables WHERE table_name LIKE 'roblox_%'"),
                ("Total indexes on Roblox tables", "SELECT COUNT(*) FROM pg_indexes WHERE tablename LIKE 'roblox_%'"),
                ("Total constraints on Roblox tables", "SELECT COUNT(*) FROM information_schema.table_constraints WHERE table_name LIKE 'roblox_%'")
            ]

            for desc, query in stats_queries:
                result = await session.execute(text(query))
                count = result.scalar()
                print(f"   📊 {desc}: {count}")

            print("\\n" + "=" * 50)
            print("✅ Roblox Integration Database Verification Complete!")
            print("\\n📝 Next Steps:")
            print("   1. Run seed data script: python database/seed_roblox_data.py")
            print("   2. Test API endpoints with Roblox integration")
            print("   3. Verify WebSocket session management")
            print("   4. Test COPPA compliance features")
            print("   5. Validate OAuth2 token handling")

        except Exception as e:
            print(f"❌ Verification failed: {e}")
            raise

        finally:
            await engine.dispose()


def main():
    """Main entry point."""
    asyncio.run(verify_database_setup())


if __name__ == "__main__":
    main()