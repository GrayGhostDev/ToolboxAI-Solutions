"""Test database setup"""

import os

import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT


def setup_test_database():
    """Create test database if it doesn't exist"""
    try:
        # Connect to PostgreSQL
        conn = psycopg2.connect(
            host=os.getenv("DB_HOST", "localhost"),
            port=os.getenv("DB_PORT", 5432),
            user=os.getenv("DB_USER", "postgres"),
            password=os.getenv("DB_PASSWORD", "postgres"),
            database="postgres",
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()

        # Create test database
        cursor.execute("SELECT 1 FROM pg_database WHERE datname = 'test_db'")
        exists = cursor.fetchone()
        if not exists:
            cursor.execute("CREATE DATABASE test_db")
            print("Created test database")

        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"Warning: Could not create test database: {e}")
        return False


if __name__ == "__main__":
    setup_test_database()
