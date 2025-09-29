#!/usr/bin/env python3
"""
Database Reset Script

Safely clears all data from the database and resets sequences.
Use with caution - this will delete ALL data!
"""

import asyncio
import sys
import os
from pathlib import Path
from typing import List, Tuple
import logging

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from database import db_manager, Base
from sqlalchemy import text

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DatabaseReset:
    """Handle database reset operations safely"""
    
    def __init__(self):
        self.protected_tables = ['alembic_version']  # Never delete these
        self.table_order = []  # Will be populated with correct deletion order
        
    async def get_table_deletion_order(self) -> List[str]:
        """Get tables in order for safe deletion (respecting foreign keys)"""
        async with db_manager.get_connection() as conn:
            # Get all tables with their foreign key dependencies
            result = await conn.fetch("""
                SELECT DISTINCT
                    tc.table_name,
                    ccu.table_name AS referenced_table
                FROM information_schema.table_constraints tc
                LEFT JOIN information_schema.constraint_column_usage ccu
                    ON tc.constraint_name = ccu.constraint_name
                    AND tc.constraint_schema = ccu.constraint_schema
                WHERE tc.constraint_type = 'FOREIGN KEY'
                    AND tc.table_schema = 'public'
                ORDER BY tc.table_name;
            """)
            
            # Build dependency graph
            dependencies = {}
            all_tables = set()
            
            for row in result:
                table = row['table_name']
                ref_table = row['referenced_table']
                
                all_tables.add(table)
                if ref_table:
                    all_tables.add(ref_table)
                    
                if table not in dependencies:
                    dependencies[table] = set()
                if ref_table:
                    dependencies[table].add(ref_table)
            
            # Get all tables (including those without foreign keys)
            all_tables_result = await conn.fetch("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                    AND table_type = 'BASE TABLE'
                    AND table_name NOT IN ('alembic_version')
                ORDER BY table_name;
            """)
            
            for row in all_tables_result:
                all_tables.add(row['table_name'])
            
            # Topological sort to get deletion order
            deletion_order = []
            visited = set()
            
            def visit(table):
                if table in visited or table in self.protected_tables:
                    return
                visited.add(table)
                
                # Visit dependencies first
                if table in dependencies:
                    for dep in dependencies[table]:
                        if dep not in visited:
                            visit(dep)
                
                deletion_order.append(table)
            
            # Visit all tables
            for table in all_tables:
                visit(table)
            
            # Reverse for deletion (delete dependents before dependencies)
            return list(reversed(deletion_order))
    
    async def clear_all_tables(self, confirm: bool = False) -> Tuple[int, int]:
        """
        Clear all data from all tables
        
        Args:
            confirm: Must be True to actually delete data
            
        Returns:
            Tuple of (tables_cleared, total_rows_deleted)
        """
        if not confirm:
            logger.error("❌ Safety check failed: confirm=True required to clear tables")
            return 0, 0
        
        tables_cleared = 0
        total_rows_deleted = 0
        
        # Get table deletion order
        deletion_order = await self.get_table_deletion_order()
        
        async with db_manager.get_connection() as conn:
            # Start transaction
            async with conn.transaction():
                # Disable foreign key checks temporarily
                await conn.execute("SET CONSTRAINTS ALL DEFERRED;")
                
                for table in deletion_order:
                    if table in self.protected_tables:
                        logger.info(f"⏭️  Skipping protected table: {table}")
                        continue
                    
                    try:
                        # Get row count before deletion
                        count_result = await conn.fetchval(
                            f"SELECT COUNT(*) FROM {table}"
                        )
                        
                        # Truncate table (faster than DELETE and resets sequences)
                        await conn.execute(f"TRUNCATE TABLE {table} CASCADE;")
                        
                        tables_cleared += 1
                        total_rows_deleted += count_result or 0
                        
                        logger.info(f"✅ Cleared {table}: {count_result} rows deleted")
                        
                    except Exception as e:
                        logger.error(f"❌ Failed to clear {table}: {e}")
                        raise
        
        return tables_cleared, total_rows_deleted
    
    async def reset_sequences(self) -> int:
        """Reset all sequences to 1"""
        sequences_reset = 0
        
        async with db_manager.get_connection() as conn:
            # Get all sequences
            sequences = await conn.fetch("""
                SELECT sequence_name
                FROM information_schema.sequences
                WHERE sequence_schema = 'public';
            """)
            
            for seq in sequences:
                sequence_name = seq['sequence_name']
                try:
                    await conn.execute(
                        f"ALTER SEQUENCE {sequence_name} RESTART WITH 1;"
                    )
                    sequences_reset += 1
                    logger.info(f"✅ Reset sequence: {sequence_name}")
                except Exception as e:
                    logger.error(f"❌ Failed to reset sequence {sequence_name}: {e}")
        
        return sequences_reset
    
    async def vacuum_database(self):
        """Vacuum the database to reclaim space"""
        async with db_manager.get_connection() as conn:
            # Note: VACUUM cannot run inside a transaction block
            await conn.execute("COMMIT;")  # End any open transaction
            await conn.execute("VACUUM ANALYZE;")
            logger.info("✅ Database vacuumed and analyzed")
    
    async def get_database_stats(self) -> dict:
        """Get current database statistics"""
        async with db_manager.get_connection() as conn:
            # Get table statistics
            tables = await conn.fetch("""
                SELECT 
                    schemaname,
                    tablename,
                    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size,
                    n_live_tup AS row_count
                FROM pg_stat_user_tables
                WHERE schemaname = 'public'
                ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
            """)
            
            # Get database size
            db_size = await conn.fetchval("""
                SELECT pg_size_pretty(pg_database_size(current_database()));
            """)
            
            return {
                'database_size': db_size,
                'tables': [dict(t) for t in tables]
            }


async def main():
    """Main function to reset the database"""
    print("\n🔄 Database Reset Utility\n")
    print("⚠️  WARNING: This will DELETE ALL DATA from the database!")
    print("⚠️  This action cannot be undone!\n")
    
    # Get current stats
    reset = DatabaseReset()
    await db_manager.initialize()
    
    print("📊 Current Database Statistics:")
    stats = await reset.get_database_stats()
    print(f"   Database size: {stats['database_size']}")
    print(f"   Total tables: {len(stats['tables'])}")
    
    if stats['tables']:
        print("\n   Tables with data:")
        for table in stats['tables'][:10]:  # Show top 10 tables
            if table['row_count'] > 0:
                print(f"   - {table['tablename']}: {table['row_count']} rows ({table['size']})")
    
    # Confirmation
    print("\n" + "="*50)
    confirmation = input("Type 'RESET DATABASE' to confirm deletion: ")
    
    if confirmation != "RESET DATABASE":
        print("\n❌ Reset cancelled. Database unchanged.")
        return
    
    # Double confirmation for production
    if os.getenv("ENVIRONMENT") == "production":
        print("\n⚠️  PRODUCTION ENVIRONMENT DETECTED!")
        prod_confirm = input("Type 'I UNDERSTAND THIS IS PRODUCTION' to proceed: ")
        if prod_confirm != "I UNDERSTAND THIS IS PRODUCTION":
            print("\n❌ Reset cancelled. Database unchanged.")
            return
    
    print("\n🔄 Starting database reset...\n")
    
    try:
        # Clear all tables
        tables_cleared, rows_deleted = await reset.clear_all_tables(confirm=True)
        print(f"\n✅ Cleared {tables_cleared} tables ({rows_deleted} total rows)")
        
        # Reset sequences
        sequences_reset = await reset.reset_sequences()
        print(f"✅ Reset {sequences_reset} sequences")
        
        # Vacuum database
        await reset.vacuum_database()
        
        # Show new stats
        print("\n📊 Database Statistics After Reset:")
        new_stats = await reset.get_database_stats()
        print(f"   Database size: {new_stats['database_size']}")
        print(f"   Tables with data: 0")
        
        print("\n✅ Database reset completed successfully!")
        print("\n💡 Next steps:")
        print("   1. Run migrations: alembic upgrade head")
        print("   2. Seed database: python scripts/development/seed_database.py")
        
    except Exception as e:
        print(f"\n❌ Database reset failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    finally:
        await db_manager.close_all()


if __name__ == "__main__":
    asyncio.run(main())