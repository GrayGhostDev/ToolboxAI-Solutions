"""
Database configuration and session management
"""

import os
from contextlib import contextmanager
from typing import Generator
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from dotenv import load_dotenv

from models.base import Base

# Load environment variables
load_dotenv()

# Database configuration
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://user:password@localhost:5432/educational_platform"
)

# Engine configuration
engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,  # Verify connections before using
    echo=os.getenv("DEBUG", "false").lower() == "true",  # SQL logging in debug mode
)

# Session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


def init_db():
    """Initialize database, create tables if they don't exist"""
    # Import all models to ensure they're registered with Base
    from models import (
        User, UserRole,
        Class, ClassEnrollment,
        Lesson, LessonProgress,
        Assessment, AssessmentSubmission, AssessmentQuestion,
        XPTransaction, Badge, UserBadge, LeaderboardEntry,
        ConsentRecord, DataRetention, ComplianceLog,
        Message, MessageRecipient
    )
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created successfully")


def get_db() -> Generator[Session, None, None]:
    """
    Dependency to get database session.
    Use in FastAPI endpoints with Depends(get_db)
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    """
    Context manager for database session.
    Use in non-FastAPI contexts.
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def drop_all_tables():
    """Drop all tables - USE WITH CAUTION"""
    Base.metadata.drop_all(bind=engine)
    print("⚠️  All database tables dropped")


def recreate_database():
    """Drop and recreate all tables - USE WITH CAUTION"""
    drop_all_tables()
    init_db()
    print("🔄 Database recreated successfully")


# Event listeners for debugging
if os.getenv("DEBUG", "false").lower() == "true":
    @event.listens_for(engine, "connect")
    def receive_connect(dbapi_conn, connection_record):
        print(f"📊 Database connection established: {connection_record.info}")
    
    @event.listens_for(engine, "close")
    def receive_close(dbapi_conn, connection_record):
        print(f"📊 Database connection closed: {connection_record.info}")


# Health check function
def check_database_health() -> bool:
    """Check if database is accessible"""
    try:
        from sqlalchemy import text
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception as e:
        print(f"❌ Database health check failed: {e}")
        return False


if __name__ == "__main__":
    # Initialize database when run directly
    print("🚀 Initializing database...")
    if check_database_health():
        init_db()
        print("✅ Database initialization complete")
    else:
        print("❌ Database is not accessible")