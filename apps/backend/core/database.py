"""
Database connection module for ToolboxAI Backend
Provides database session management for Supabase PostgreSQL
"""

import os
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

# Get database URL from environment (Supabase pooler by default)
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/postgres")

# Create SQLAlchemy engine with optimized settings for Supabase pooler (pgBouncer)
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,        # Test connections before using
    pool_size=10,               # Increased for pooler (was 5)
    max_overflow=20,            # Increased overflow (was 10)
    pool_recycle=3600,          # Recycle connections after 1 hour
    echo=False
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create base class for models
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """
    Dependency function to get database session
    Usage: db: Session = Depends(get_db)
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database - create all tables"""
    Base.metadata.create_all(bind=engine)

