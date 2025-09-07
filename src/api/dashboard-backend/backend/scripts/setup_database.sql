-- Educational Platform Database Setup Script
-- PostgreSQL 16
-- 
-- This script creates the necessary databases and users for the educational platform
-- Run as PostgreSQL superuser (postgres)

-- ==================== USER CREATION ====================
-- Drop user if exists (for clean setup)
DROP USER IF EXISTS eduplatform;

-- Create application user
CREATE USER eduplatform WITH PASSWORD 'eduplatform2024';

-- Grant necessary permissions
ALTER USER eduplatform CREATEDB;

-- ==================== DATABASE CREATION ====================
-- Drop databases if they exist (for clean setup)
DROP DATABASE IF EXISTS educational_platform_dev;
DROP DATABASE IF EXISTS educational_platform;
DROP DATABASE IF EXISTS educational_platform_test;

-- Create development database
CREATE DATABASE educational_platform_dev
    OWNER eduplatform
    ENCODING 'UTF8'
    LC_COLLATE 'en_US.UTF-8'
    LC_CTYPE 'en_US.UTF-8'
    TEMPLATE template0;

-- Create production database
CREATE DATABASE educational_platform
    OWNER eduplatform
    ENCODING 'UTF8'
    LC_COLLATE 'en_US.UTF-8'
    LC_CTYPE 'en_US.UTF-8'
    TEMPLATE template0;

-- Create test database
CREATE DATABASE educational_platform_test
    OWNER eduplatform
    ENCODING 'UTF8'
    LC_COLLATE 'en_US.UTF-8'
    LC_CTYPE 'en_US.UTF-8'
    TEMPLATE template0;

-- ==================== GRANT PRIVILEGES ====================
GRANT ALL PRIVILEGES ON DATABASE educational_platform_dev TO eduplatform;
GRANT ALL PRIVILEGES ON DATABASE educational_platform TO eduplatform;
GRANT ALL PRIVILEGES ON DATABASE educational_platform_test TO eduplatform;

-- ==================== EXTENSIONS FOR DEVELOPMENT DATABASE ====================
\c educational_platform_dev;

-- UUID generation support
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Cryptographic functions
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Full text search (optional, for future use)
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Grant schema permissions
GRANT ALL ON SCHEMA public TO eduplatform;

-- ==================== EXTENSIONS FOR PRODUCTION DATABASE ====================
\c educational_platform;

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

GRANT ALL ON SCHEMA public TO eduplatform;

-- ==================== EXTENSIONS FOR TEST DATABASE ====================
\c educational_platform_test;

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

GRANT ALL ON SCHEMA public TO eduplatform;

-- ==================== VERIFICATION ====================
\c educational_platform_dev;

-- Verify extensions are installed
SELECT extname, extversion FROM pg_extension WHERE extname IN ('uuid-ossp', 'pgcrypto', 'pg_trgm');

-- List databases
\l

-- List users
\du

-- ==================== SUCCESS MESSAGE ====================
\echo ''
\echo '================================================================'
\echo '✅ Database setup completed successfully!'
\echo '================================================================'
\echo ''
\echo 'Databases created:'
\echo '  - educational_platform_dev (development)'
\echo '  - educational_platform (production)'
\echo '  - educational_platform_test (testing)'
\echo ''
\echo 'User created:'
\echo '  - eduplatform (password: eduplatform2024)'
\echo ''
\echo 'Extensions installed:'
\echo '  - uuid-ossp (UUID generation)'
\echo '  - pgcrypto (Cryptographic functions)'
\echo '  - pg_trgm (Text search)'
\echo ''
\echo 'Next steps:'
\echo '  1. Update backend/.env with the correct DATABASE_URL'
\echo '  2. Run: cd backend && python database.py'
\echo '  3. Run: python scripts/seed_data.py'
\echo '================================================================'