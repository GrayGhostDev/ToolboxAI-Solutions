"""
Test configuration and fixtures for API endpoint testing.

This module provides reusable test fixtures and utilities for testing
FastAPI endpoints, including test client setup, database fixtures,
and authentication helpers.
"""

import asyncio
import os
from typing import AsyncGenerator, Generator, Dict, Any
from datetime import datetime, timedelta
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import sessionmaker
from fastapi import FastAPI
from jose import jwt

# Set testing environment
os.environ["TESTING"] = "true"
os.environ["SKIP_LIFESPAN"] = "true"

from apps.backend.core.app_factory import create_test_app
from apps.backend.core.auth import UnifiedAuthService

# Import models directly from SQLAlchemy since database.models has issues
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.sql import func

Base = declarative_base()

class User(Base):
    """Test user model."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(String, default="student")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Content(Base):
    """Test content model."""
    __tablename__ = "contents"

    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    description = Column(String)
    content_type = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

async def get_async_session():
    """Placeholder for session getter."""
    pass


# Test database URL - using SQLite for tests
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture
async def test_db_engine():
    """Create test database engine."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        future=True
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest_asyncio.fixture
async def test_session(test_db_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create test database session."""
    async_session_maker = async_sessionmaker(
        test_db_engine,
        class_=AsyncSession,
        expire_on_commit=False
    )

    async with async_session_maker() as session:
        yield session


@pytest.fixture
def test_app(test_session) -> FastAPI:
    """Create test FastAPI application."""
    app = create_test_app()

    # Override database dependency
    async def override_get_db():
        yield test_session

    app.dependency_overrides[get_async_session] = override_get_db

    return app


@pytest_asyncio.fixture
async def test_client(test_app) -> AsyncGenerator[AsyncClient, None]:
    """Create async test client."""
    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest_asyncio.fixture
async def auth_service() -> UnifiedAuthService:
    """Get auth service instance."""
    return UnifiedAuthService()


@pytest_asyncio.fixture
async def test_user(test_session: AsyncSession, auth_service: UnifiedAuthService) -> User:
    """Create a test user."""
    hashed_password = auth_service.hash_password("testpassword123")

    user = User(
        username="testuser",
        email="test@example.com",
        hashed_password=hashed_password,
        role="student",
        is_active=True,
        created_at=datetime.utcnow()
    )

    test_session.add(user)
    await test_session.commit()
    await test_session.refresh(user)

    return user


@pytest_asyncio.fixture
async def admin_user(test_session: AsyncSession, auth_service: UnifiedAuthService) -> User:
    """Create an admin test user."""
    hashed_password = auth_service.hash_password("adminpassword123")

    user = User(
        username="adminuser",
        email="admin@example.com",
        hashed_password=hashed_password,
        role="admin",
        is_active=True,
        created_at=datetime.utcnow()
    )

    test_session.add(user)
    await test_session.commit()
    await test_session.refresh(user)

    return user


@pytest_asyncio.fixture
async def teacher_user(test_session: AsyncSession, auth_service: UnifiedAuthService) -> User:
    """Create a teacher test user."""
    hashed_password = auth_service.hash_password("teacherpassword123")

    user = User(
        username="teacheruser",
        email="teacher@example.com",
        hashed_password=hashed_password,
        role="teacher",
        is_active=True,
        created_at=datetime.utcnow()
    )

    test_session.add(user)
    await test_session.commit()
    await test_session.refresh(user)

    return user


@pytest.fixture
def auth_headers(test_user: User, auth_service: UnifiedAuthService) -> Dict[str, str]:
    """Generate authentication headers for test user."""
    token = auth_service.create_access_token(
        user_id=str(test_user.id),
        username=test_user.username,
        role=test_user.role,
        email=test_user.email
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def admin_headers(admin_user: User, auth_service: UnifiedAuthService) -> Dict[str, str]:
    """Generate authentication headers for admin user."""
    token = auth_service.create_access_token(
        user_id=str(admin_user.id),
        username=admin_user.username,
        role=admin_user.role,
        email=admin_user.email
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def teacher_headers(teacher_user: User, auth_service: UnifiedAuthService) -> Dict[str, str]:
    """Generate authentication headers for teacher user."""
    token = auth_service.create_access_token(
        user_id=str(teacher_user.id),
        username=teacher_user.username,
        role=teacher_user.role,
        email=teacher_user.email
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def expired_token_headers(auth_service: UnifiedAuthService) -> Dict[str, str]:
    """Generate expired authentication headers."""
    # Create token that expired 1 hour ago
    expired_token = auth_service.create_access_token(
        user_id="123",
        username="expireduser",
        role="student",
        expires_delta=timedelta(hours=-1)
    )
    return {"Authorization": f"Bearer {expired_token}"}


@pytest.fixture
def invalid_token_headers() -> Dict[str, str]:
    """Generate invalid authentication headers."""
    return {"Authorization": "Bearer invalid_token_here"}


# Helper functions for tests
async def create_test_content(session: AsyncSession, title: str = "Test Content") -> Any:
    """Helper to create test content."""
    from database.models import Content

    content = Content(
        title=title,
        description="Test description",
        content_type="lesson",
        created_at=datetime.utcnow()
    )
    session.add(content)
    await session.commit()
    await session.refresh(content)
    return content


async def create_test_class(session: AsyncSession, teacher_id: int, name: str = "Test Class") -> Any:
    """Helper to create test class."""
    from database.models import Class

    test_class = Class(
        name=name,
        teacher_id=teacher_id,
        description="Test class description",
        created_at=datetime.utcnow()
    )
    session.add(test_class)
    await session.commit()
    await session.refresh(test_class)
    return test_class