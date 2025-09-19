#!/usr/bin/env python3
"""
CI Database Setup Script
Ensures database tables exist before running tests
"""
import os
import sys
import time
import psycopg2
from psycopg2 import sql
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

def wait_for_db(max_retries=30):
    """Wait for database to be available"""
    db_url = os.getenv("DATABASE_URL", "postgresql://eduplatform:eduplatform2024@localhost/educational_platform_dev")

    for i in range(max_retries):
        try:
            conn = psycopg2.connect(db_url)
            conn.close()
            print("✅ Database is available")
            return True
        except Exception as e:
            if i < max_retries - 1:
                print(f"Waiting for database... ({i+1}/{max_retries})")
                time.sleep(1)
            else:
                print(f"❌ Database not available after {max_retries} seconds: {e}")
                return False
    return False

def create_tables():
    """Create essential tables if they don't exist"""
    db_url = os.getenv("DATABASE_URL", "postgresql://eduplatform:eduplatform2024@localhost/educational_platform_dev")

    try:
        conn = psycopg2.connect(db_url)
        cur = conn.cursor()

        # Create users table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username VARCHAR(100) UNIQUE NOT NULL,
                email VARCHAR(100) UNIQUE NOT NULL,
                password_hash VARCHAR(255),
                role VARCHAR(50) DEFAULT 'student',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Create dashboard_users table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS dashboard_users (
                id SERIAL PRIMARY KEY,
                username VARCHAR(100) UNIQUE NOT NULL,
                email VARCHAR(100) UNIQUE NOT NULL,
                password_hash VARCHAR(255),
                role VARCHAR(50) DEFAULT 'student',
                first_name VARCHAR(100),
                last_name VARCHAR(100),
                is_active BOOLEAN DEFAULT true,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Create classes table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS classes (
                id SERIAL PRIMARY KEY,
                name VARCHAR(200) NOT NULL,
                description TEXT,
                teacher_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Create lessons table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS lessons (
                id SERIAL PRIMARY KEY,
                title VARCHAR(200) NOT NULL,
                description TEXT,
                content TEXT,
                class_id INTEGER,
                order_index INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Create schools table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS schools (
                id SERIAL PRIMARY KEY,
                name VARCHAR(200) NOT NULL,
                address TEXT,
                admin_email VARCHAR(100),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Create api_keys table (fixed from previous issue)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS api_keys (
                id SERIAL PRIMARY KEY,
                key_id VARCHAR(36) UNIQUE NOT NULL,
                key_hash VARCHAR(128) UNIQUE NOT NULL,
                name VARCHAR(100) NOT NULL,
                description VARCHAR(500),
                user_id VARCHAR(100) NOT NULL,
                scopes JSON DEFAULT '[]',
                place_ids JSON DEFAULT '[]',
                ip_whitelist JSON DEFAULT '[]',
                status VARCHAR(50) DEFAULT 'active',
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP WITH TIME ZONE,
                last_used_at TIMESTAMP WITH TIME ZONE,
                revoked_at TIMESTAMP WITH TIME ZONE,
                usage_count INTEGER DEFAULT 0,
                rate_limit INTEGER DEFAULT 1000,
                metadata JSON DEFAULT '{}'
            )
        """)

        conn.commit()
        print("✅ All essential tables created/verified")

        # Check what tables exist
        cur.execute("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            ORDER BY table_name
        """)
        tables = cur.fetchall()
        print(f"📊 Found {len(tables)} tables:")
        for table in tables:
            print(f"  - {table[0]}")

        cur.close()
        conn.close()
        return True

    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        return False

def main():
    """Main entry point"""
    print("🚀 Starting CI database setup...")

    if not wait_for_db():
        sys.exit(1)

    if not create_tables():
        sys.exit(1)

    print("✅ CI database setup complete!")
    sys.exit(0)

if __name__ == "__main__":
    main()