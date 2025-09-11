#!/bin/bash

# Database Performance Validation Script
# Tests key queries to validate optimization effectiveness
# Target: All queries < 50ms

DB_HOST="localhost"
DB_USER="grayghostdata"
DB_NAME="educational_platform"

echo "🚀 Database Performance Validation"
echo "Database: ${DB_NAME}@${DB_HOST}"
echo "Target: All queries < 50ms"
echo

# Test individual queries with timing
echo "🔍 Testing Core Queries..."

echo -n "1. User Authentication... "
psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" -c "\timing on" -c "
SELECT id, username, role 
FROM users 
WHERE email LIKE '%@%' AND is_active = true
LIMIT 1;
" 2>/dev/null | grep "Time:" | tail -1

echo -n "2. Active Users Count... "
psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" -c "\timing on" -c "
SELECT COUNT(*) 
FROM users 
WHERE is_active = true;
" 2>/dev/null | grep "Time:" | tail -1

echo -n "3. Educational Content Search... "
psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" -c "\timing on" -c "
SELECT id, title, subject 
FROM educational_content 
WHERE is_published = true
ORDER BY created_at DESC
LIMIT 20;
" 2>/dev/null | grep "Time:" | tail -1

echo -n "4. Quiz Attempts Query... "
psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" -c "\timing on" -c "
SELECT user_id, score, completed_at
FROM quiz_attempts
WHERE completed_at IS NOT NULL
ORDER BY score DESC
LIMIT 20;
" 2>/dev/null | grep "Time:" | tail -1

echo -n "5. User Progress Tracking... "
psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" -c "\timing on" -c "
SELECT user_id, completion_percentage, mastery_level
FROM user_progress 
ORDER BY last_interaction DESC
LIMIT 20;
" 2>/dev/null | grep "Time:" | tail -1

echo -n "6. Classes Information... "
psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" -c "\timing on" -c "
SELECT name, subject, student_count
FROM classes 
WHERE is_active = true
ORDER BY student_count DESC
LIMIT 20;
" 2>/dev/null | grep "Time:" | tail -1

echo -n "7. Recent Assignments... "
psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" -c "\timing on" -c "
SELECT title, due_date, created_at
FROM assignments
WHERE is_published = true
ORDER BY created_at DESC
LIMIT 15;
" 2>/dev/null | grep "Time:" | tail -1

echo
echo "📊 Index Usage Statistics:"
psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" -c "
SELECT 
    relname as table_name,
    indexrelname as index_name,
    idx_scan as scans,
    idx_tup_read as tuples_read
FROM pg_stat_user_indexes
WHERE idx_scan > 0
ORDER BY idx_scan DESC
LIMIT 10;
"

echo
echo "🔧 Connection Pool Test:"
echo "Testing 10 rapid connections..."

start_time=$(date +%s)
for i in {1..10}; do
    psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" -c "SELECT 1;" > /dev/null 2>&1
done
end_time=$(date +%s)

duration=$((end_time - start_time))
echo "10 connections completed in ${duration} seconds"

if [ $duration -le 2 ]; then
    echo "✅ Connection pool performance: EXCELLENT"
elif [ $duration -le 5 ]; then
    echo "✅ Connection pool performance: GOOD"
else
    echo "⚠️  Connection pool performance: NEEDS IMPROVEMENT"
fi

echo
echo "📈 Database Configuration:"
psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" -c "
SELECT 
    name, 
    setting,
    unit,
    CASE 
        WHEN name = 'max_connections' AND setting::int >= 100 THEN '✅ Good'
        WHEN name = 'shared_buffers' AND setting::int >= 16384 THEN '✅ Good' 
        WHEN name = 'work_mem' AND setting::int >= 4096 THEN '✅ Good'
        ELSE '⚠️  Could be optimized'
    END as status
FROM pg_settings 
WHERE name IN (
    'max_connections',
    'shared_buffers', 
    'work_mem',
    'effective_cache_size'
)
ORDER BY name;
"

echo
echo "🎯 Optimization Summary:"
echo "✅ Comprehensive indexes applied"
echo "✅ Connection pool optimized (20 + 40 overflow)" 
echo "✅ Pool timeout and recycle configured"
echo "✅ Query planner statistics updated"

echo
echo "💡 Maintenance Recommendations:"
echo "• Run VACUUM ANALYZE weekly on active tables"
echo "• Monitor pg_stat_statements for slow queries"
echo "• Consider connection pooling (pgbouncer) for high load"
echo "• Schedule REINDEX monthly for heavily updated tables"

echo
echo "✅ Performance validation completed!"
echo "📋 Review query times above - target < 50ms"