-- Redis 7 ACL Configuration Script
-- ToolBoxAI Solutions - Phase 2 Database Modernization
-- Created: 2025-09-20
--
-- This script contains Redis CLI commands for configuring ACL v2
-- with enhanced security features for Redis 7.
--
-- Execute these commands via Redis CLI or through redis-py client
-- Usage: redis-cli < redis7_acl_configuration.sql

-- =====================================
-- 1. Clear existing ACL configuration
-- =====================================

-- Reset ACL to default state (use with caution in production)
-- ACL DELUSER testuser 2>/dev/null || true

-- =====================================
-- 2. Create Application Service Users
-- =====================================

-- Backend API service user with restricted permissions
ACL SETUSER backend_api on
ACL SETUSER backend_api >backend_api_secure_password_2025
ACL SETUSER backend_api ~app:cache:*
ACL SETUSER backend_api ~app:session:*
ACL SETUSER backend_api ~app:user:*
ACL SETUSER backend_api ~app:temp:*
ACL SETUSER backend_api +@read +@write +@list +@set +@hash +@string
ACL SETUSER backend_api -@dangerous
ACL SETUSER backend_api -flushdb -flushall -shutdown -debug
ACL SETUSER backend_api &app:notifications:*

-- Caching service user for temporary data
ACL SETUSER cache_service on
ACL SETUSER cache_service >cache_service_password_2025
ACL SETUSER cache_service ~cache:*
ACL SETUSER cache_service ~temp:*
ACL SETUSER cache_service +@read +@write +@string +@hash +@list
ACL SETUSER cache_service +expire +ttl +exists +del
ACL SETUSER cache_service -@dangerous -@admin -@scripting

-- Session management service user
ACL SETUSER session_manager on
ACL SETUSER session_manager >session_mgr_password_2025
ACL SETUSER session_manager ~session:*
ACL SETUSER session_manager ~user:session:*
ACL SETUSER session_manager +@read +@write +@hash +@string
ACL SETUSER session_manager +expire +ttl +exists +del
ACL SETUSER session_manager -@dangerous -@admin

-- Analytics service user (read-only for most operations)
ACL SETUSER analytics_service on
ACL SETUSER analytics_service >analytics_readonly_password_2025
ACL SETUSER analytics_service ~analytics:*
ACL SETUSER analytics_service ~metrics:*
ACL SETUSER analytics_service ~stats:*
ACL SETUSER analytics_service +@read +@list +@string +@hash
ACL SETUSER analytics_service +info +ping +exists
ACL SETUSER analytics_service -@write -@dangerous -@admin

-- Monitoring service user
ACL SETUSER monitoring_service on
ACL SETUSER monitoring_service >monitoring_readonly_password_2025
ACL SETUSER monitoring_service ~*
ACL SETUSER monitoring_service +@read +info +ping +client +config
ACL SETUSER monitoring_service +memory +latency +slowlog
ACL SETUSER monitoring_service -@write -@dangerous -flushdb -flushall

-- =====================================
-- 3. Create Administrative Users
-- =====================================

-- Database administrator with full access
ACL SETUSER db_admin on
ACL SETUSER db_admin >db_admin_secure_password_2025
ACL SETUSER db_admin ~*
ACL SETUSER db_admin &*
ACL SETUSER db_admin +@all

-- Application administrator with limited dangerous commands
ACL SETUSER app_admin on
ACL SETUSER app_admin >app_admin_password_2025
ACL SETUSER app_admin ~app:*
ACL SETUSER app_admin ~cache:*
ACL SETUSER app_admin ~session:*
ACL SETUSER app_admin ~temp:*
ACL SETUSER app_admin +@all
ACL SETUSER app_admin -flushall -shutdown -debug
ACL SETUSER app_admin &app:*

-- =====================================
-- 4. Create Environment-Specific Users
-- =====================================

-- Development environment user
ACL SETUSER dev_user on
ACL SETUSER dev_user >dev_password_2025
ACL SETUSER dev_user ~dev:*
ACL SETUSER dev_user ~test:*
ACL SETUSER dev_user +@all
ACL SETUSER dev_user -flushall -shutdown

-- Staging environment user
ACL SETUSER staging_user on
ACL SETUSER staging_user >staging_password_2025
ACL SETUSER staging_user ~staging:*
ACL SETUSER staging_user ~app:*
ACL SETUSER staging_user +@read +@write +@list +@set +@hash +@string
ACL SETUSER staging_user -@dangerous

-- Production read-only user for debugging
ACL SETUSER prod_readonly on
ACL SETUSER prod_readonly >prod_readonly_password_2025
ACL SETUSER prod_readonly ~*
ACL SETUSER prod_readonly +@read +info +ping +client +memory
ACL SETUSER prod_readonly -@write -@dangerous

-- =====================================
-- 5. Configure Pub/Sub Channel ACLs
-- =====================================

-- Configure pub/sub channels for different services
ACL SETUSER backend_api &notifications:*
ACL SETUSER backend_api &events:user:*
ACL SETUSER backend_api &cache:invalidation:*

ACL SETUSER analytics_service &analytics:*
ACL SETUSER analytics_service &metrics:*

ACL SETUSER monitoring_service &monitoring:*
ACL SETUSER monitoring_service &alerts:*

-- =====================================
-- 6. Create Redis Functions (Redis 7 Feature)
-- =====================================

-- Function to safely increment counters with expiration
FUNCTION LOAD "#!lua name=counter_utils
local function safe_increment(keys, args)
    local key = keys[1]
    local increment = tonumber(args[1]) or 1
    local ttl = tonumber(args[2]) or 3600

    local current = redis.call('INCR', key)
    if current == 1 then
        redis.call('EXPIRE', key, ttl)
    end

    return current
end

redis.register_function('safe_increment', safe_increment)
"

-- Function for session validation
FUNCTION LOAD "#!lua name=session_utils
local function validate_session(keys, args)
    local session_key = keys[1]
    local user_id = args[1]
    local max_age = tonumber(args[2]) or 3600

    local session_data = redis.call('HGETALL', session_key)
    if next(session_data) == nil then
        return {0, 'session_not_found'}
    end

    local session_user = nil
    local created_at = nil

    for i = 1, #session_data, 2 do
        if session_data[i] == 'user_id' then
            session_user = session_data[i + 1]
        elseif session_data[i] == 'created_at' then
            created_at = tonumber(session_data[i + 1])
        end
    end

    if session_user ~= user_id then
        return {0, 'invalid_user'}
    end

    if created_at and (redis.call('TIME')[1] - created_at) > max_age then
        redis.call('DEL', session_key)
        return {0, 'session_expired'}
    end

    return {1, 'valid'}
end

redis.register_function('validate_session', validate_session)
"

-- Function for rate limiting
FUNCTION LOAD "#!lua name=rate_limit_utils
local function rate_limit(keys, args)
    local key = keys[1]
    local limit = tonumber(args[1])
    local window = tonumber(args[2])

    local current = redis.call('INCR', key)
    if current == 1 then
        redis.call('EXPIRE', key, window)
    end

    if current > limit then
        local ttl = redis.call('TTL', key)
        return {0, ttl}
    end

    return {1, limit - current}
end

redis.register_function('rate_limit', rate_limit)
"

-- =====================================
-- 7. Configure Redis 7 Settings
-- =====================================

-- Enable ACL logging
CONFIG SET acllog-max-len 128

-- Configure memory optimization
CONFIG SET maxmemory-policy allkeys-lru
CONFIG SET maxmemory 512mb

-- Enable lazy freeing for better performance
CONFIG SET lazyfree-lazy-eviction yes
CONFIG SET lazyfree-lazy-expire yes
CONFIG SET lazyfree-lazy-server-del yes

-- Configure persistence
CONFIG SET save "900 1 300 10 60 10000"
CONFIG SET rdbcompression yes
CONFIG SET rdbchecksum yes

-- Enable command logging for security
CONFIG SET slowlog-log-slower-than 10000
CONFIG SET slowlog-max-len 128

-- =====================================
-- 8. Set up monitoring and alerts
-- =====================================

-- Configure keyspace notifications for monitoring
CONFIG SET notify-keyspace-events Ex

-- Set client output buffer limits
CONFIG SET client-output-buffer-limit "normal 0 0 0 slave 268435456 67108864 60 pubsub 33554432 8388608 60"

-- =====================================
-- 9. Backup ACL Configuration
-- =====================================

-- Save ACL configuration
ACL SAVE

-- Save Redis configuration
CONFIG REWRITE

-- =====================================
-- 10. Display Current ACL Status
-- =====================================

-- Show all configured users
ACL LIST

-- Show ACL categories
ACL CAT

-- Show current user
ACL WHOAMI

-- =====================================
-- 11. Security Validation Commands
-- =====================================

-- Test backend_api user permissions
-- AUTH backend_api backend_api_secure_password_2025
-- SET app:cache:test "test_value"
-- GET app:cache:test
-- DEL app:cache:test

-- Test that dangerous commands are blocked
-- FLUSHALL  -- This should fail

-- Test pub/sub permissions
-- PUBLISH notifications:user:123 "test message"

-- Reset to default user for admin tasks
-- AUTH default

-- =====================================
-- Configuration Summary
-- =====================================

-- Users created:
-- - backend_api: Application backend with restricted key patterns
-- - cache_service: Caching operations only
-- - session_manager: Session management operations
-- - analytics_service: Read-only analytics access
-- - monitoring_service: Read-only monitoring access
-- - db_admin: Full administrative access
-- - app_admin: Application administration
-- - dev_user: Development environment access
-- - staging_user: Staging environment access
-- - prod_readonly: Production read-only access

-- Functions registered:
-- - safe_increment: Counter with automatic expiration
-- - validate_session: Session validation logic
-- - rate_limit: Rate limiting implementation

-- Security features enabled:
-- - ACL v2 with key patterns and command categories
-- - Pub/sub channel restrictions
-- - Redis Functions for secure operations
-- - Command logging and monitoring
-- - Memory and persistence optimization