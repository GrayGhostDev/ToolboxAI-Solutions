"""
Integration test configuration

Provides sync database fixtures for integration tests.
"""

import os
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

# Database URL for testing
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://dbuser_4qnrmosa:13y70agAhh2LSyjLw3LYtF1kRPra0qnNhdQcng6YNb0lMz5h@localhost:5434/toolboxai_6rmgje4u"
)


@pytest.fixture(scope="session")
def engine():
    """Create database engine for integration tests"""
    return create_engine(DATABASE_URL)


@pytest.fixture(scope="function")
def db_session(engine) -> Session:
    """
    Create synchronous database session for each integration test.

    Provides a clean session with automatic rollback after test.
    """
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session: Session = SessionLocal()

    yield session

    # Cleanup
    session.rollback()
    session.close()
