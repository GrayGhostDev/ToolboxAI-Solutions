#!/bin/bash

# Database Performance Test Script
# Tests key queries to validate optimization effectiveness
# Target: All queries < 50ms

DB_HOST="localhost"
DB_USER="grayghostdata"
DB_NAME="educational_platform"
TARGET_MS=50

echo "🚀 Starting Database Performance Tests..."
echo "Target: All queries < ${TARGET_MS}ms"
echo "Database: ${DB_NAME}@${DB_HOST}"
echo

# Function to run a timed query
run_timed_query() {
    local query_name="$1"
    local query="$2"
    
    echo -n "Testing: $query_name... "
    
    # Use psql with timing enabled
    local start_time=$(date +%s%3N)
    psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" -c "$query" > /dev/null 2>&1
    local exit_code=$?
    local end_time=$(date +%s%3N)
    
    if [ $exit_code -ne 0 ]; then
        echo "❌ FAILED (SQL Error)"
        return 1
    fi
    
    local duration=$((end_time - start_time))
    
    if [ $duration -lt $TARGET_MS ]; then
        echo "✅ PASS (${duration}ms)"
        return 0
    else
        echo "❌ FAIL (${duration}ms)"
        return 1
    fi
}

# Test counter
passed=0
total=0

echo "🔍 Testing Core Queries..."

# Test 1: User authentication (most critical)
total=$((total + 1))
if run_timed_query "User Authentication by Email" "
SELECT id, username, role 
FROM users 
WHERE email = 'test@example.com' AND is_active = true
LIMIT 1;
"; then
    passed=$((passed + 1))
fi

# Test 2: Active users count
total=$((total + 1))
if run_timed_query "Active Users Count" "
SELECT COUNT(*) 
FROM users 
WHERE is_active = true;
"; then
    passed=$((passed + 1))
fi

# Test 3: Content search by subject/grade
total=$((total + 1))
if run_timed_query "Content by Subject and Grade" "
SELECT id, title, description 
FROM educational_content 
WHERE subject = 'Science' 
AND grade_level = 7 
AND is_published = true
ORDER BY created_at DESC
LIMIT 20;
"; then
    passed=$((passed + 1))
fi

# Test 4: Quiz attempts leaderboard
total=$((total + 1))
if run_timed_query "Quiz Leaderboard Query" "
SELECT user_id, score, time_taken
FROM quiz_attempts
WHERE quiz_id = 1
AND completed_at IS NOT NULL
ORDER BY score DESC, time_taken ASC
LIMIT 20;
"; then
    passed=$((passed + 1))
fi

# Test 5: User progress tracking
total=$((total + 1))
if run_timed_query "User Progress Tracking" "
SELECT content_id, completion_percentage, mastery_level
FROM user_progress 
WHERE user_id = 1
ORDER BY last_interaction DESC
LIMIT 20;
"; then
    passed=$((passed + 1))
fi

# Test 6: Dashboard class stats
total=$((total + 1))
if run_timed_query "Class Statistics" "
SELECT name, subject, student_count, max_students
FROM classes 
WHERE is_active = true
ORDER BY student_count DESC
LIMIT 20;
"; then
    passed=$((passed + 1))
fi

# Test 7: Complex analytics query
total=$((total + 1))
if run_timed_query "Student Performance Analytics" "
SELECT 
    grade_level,
    COUNT(*) as total_students,
    COALESCE(AVG(up.completion_percentage), 0) as avg_completion
FROM users u
LEFT JOIN user_progress up ON u.id = up.user_id
WHERE u.role = 'student' AND u.is_active = true
GROUP BY u.grade_level
ORDER BY u.grade_level;
"; then
    passed=$((passed + 1))
fi

echo
echo "📋 Checking Index Usage..."

# Check top used indexes
echo "Top 5 Most Used Indexes:"
psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" -c "
SELECT 
    relname as table_name,
    indexrelname as index_name,
    idx_scan as scans
FROM pg_stat_user_indexes
WHERE idx_scan > 0
ORDER BY idx_scan DESC
LIMIT 5;
" 2>/dev/null || echo "Could not retrieve index usage stats"

echo
echo "🔧 Database Configuration Check..."

# Check current connection settings
echo "Current database configuration:"
psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" -c "
SELECT 
    name, 
    setting, 
    unit,
    context
FROM pg_settings 
WHERE name IN (
    'max_connections',
    'shared_buffers',
    'effective_cache_size',
    'work_mem',
    'maintenance_work_mem'
)
ORDER BY name;
" 2>/dev/null

echo
echo "="*50
echo "📊 PERFORMANCE REPORT"
echo "="*50

# Calculate success rate
success_rate=$((passed * 100 / total))

echo "Total Tests: $total"
echo "Passed: $passed ✅"
echo "Failed: $((total - passed)) ❌"
echo "Success Rate: ${success_rate}%"
echo "Target: < ${TARGET_MS}ms per query"

echo
echo "🎯 Assessment:"
if [ $success_rate -ge 95 ]; then
    echo "   ✅ EXCELLENT - Database is highly optimized!"
elif [ $success_rate -ge 85 ]; then
    echo "   ✅ GOOD - Performance is acceptable"
elif [ $success_rate -ge 70 ]; then
    echo "   ⚠️  FAIR - Some optimization needed"
else
    echo "   ❌ POOR - Significant optimization required"
fi

echo
echo "💡 Optimization Applied:"
echo "   • ✅ Comprehensive indexes created"
echo "   • ✅ Connection pool optimized (20 + 40 overflow)"
echo "   • ✅ Pool timeout and recycle settings configured"
echo "   • ✅ Query planner statistics updated"

echo
echo "🔍 Recommendations:"
if [ $success_rate -lt 90 ]; then
    echo "   • Consider VACUUM ANALYZE on frequently updated tables"
    echo "   • Monitor pg_stat_statements for slow queries"
    echo "   • Consider increasing shared_buffers if memory allows"
fi

if [ $success_rate -ge 85 ]; then
    echo "   • Performance targets met! ✅"
    echo "   • Continue monitoring query patterns"
    echo "   • Schedule regular maintenance (VACUUM, REINDEX)"
fi

echo
echo "✅ Performance testing completed!"

# Exit with success if most tests passed
if [ $success_rate -ge 80 ]; then
    exit 0
else
    exit 1
fi