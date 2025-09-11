#!/usr/bin/env python3

import asyncio
import asyncpg
from redis import asyncio as aioredis
import time
import os
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PerformanceOptimizer:
    async def optimize_database(self):
        """Optimize database performance"""
        try:
            # Get database URL from environment or use default
            db_url = os.getenv('DATABASE_URL', 'postgresql://eduplatform@localhost/educational_platform')
            
            conn = await asyncpg.connect(db_url)
            
            # Create missing indexes
            indexes = [
                "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_email ON users(email);",
                "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_assignments_class ON assignments(class_id);",
                "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_submissions_student ON submissions(student_id);",
                "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_messages_recipient ON messages(recipient_id);",
                "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_classes_school ON classes(school_id);",
                "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_classes_teacher ON classes(teacher_id);",
                "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_lessons_class ON lessons(class_id);",
                "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_assessments_class ON assessments(class_id);",
                "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_student_progress_student ON student_progress(student_id);",
                "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_student_progress_lesson ON student_progress(lesson_id);",
            ]
            
            for index in indexes:
                try:
                    await conn.execute(index)
                    index_name = index.split('idx_')[1].split(' ')[0]
                    logger.info(f"✅ Index created/verified: idx_{index_name}")
                except Exception as e:
                    if "already exists" in str(e):
                        index_name = index.split('idx_')[1].split(' ')[0]
                        logger.info(f"⚠️ Index already exists: idx_{index_name}")
                    else:
                        logger.error(f"Error creating index: {e}")
            
            # Vacuum and analyze
            logger.info("Running VACUUM ANALYZE...")
            await conn.execute("VACUUM ANALYZE;")
            logger.info("✅ Database vacuumed and analyzed")
            
            # Get table statistics
            stats = await conn.fetch("""
                SELECT 
                    schemaname,
                    tablename,
                    n_live_tup as live_rows,
                    n_dead_tup as dead_rows,
                    last_vacuum,
                    last_analyze
                FROM pg_stat_user_tables
                WHERE schemaname = 'public'
                ORDER BY n_live_tup DESC
                LIMIT 10;
            """)
            
            logger.info("\n📊 Top 10 Tables by Row Count:")
            for stat in stats:
                logger.info(f"  {stat['tablename']}: {stat['live_rows']} rows (dead: {stat['dead_rows']})")
            
            await conn.close()
            
        except Exception as e:
            logger.error(f"Database optimization failed: {e}")
    
    async def optimize_redis(self):
        """Optimize Redis performance"""
        try:
            redis = await aioredis.from_url('redis://localhost')
            
            # Set memory policies
            await redis.config_set('maxmemory-policy', 'allkeys-lru')
            await redis.config_set('timeout', '300')
            
            # Get Redis info
            info = await redis.info()
            logger.info(f"✅ Redis optimized - Memory used: {info.get('used_memory_human', 'N/A')}")
            
            await redis.close()
            
        except Exception as e:
            logger.error(f"Redis optimization failed: {e}")
    
    async def run_optimizations(self):
        """Run all optimizations"""
        logger.info("🚀 Starting Performance Optimization...")
        logger.info("=" * 50)
        
        # Run database optimization
        logger.info("\n📊 Optimizing Database...")
        await self.optimize_database()
        
        # Run Redis optimization
        logger.info("\n💾 Optimizing Redis...")
        await self.optimize_redis()
        
        logger.info("\n✅ Optimization complete!")

# Run optimizations
if __name__ == "__main__":
    optimizer = PerformanceOptimizer()
    asyncio.run(optimizer.run_optimizations())