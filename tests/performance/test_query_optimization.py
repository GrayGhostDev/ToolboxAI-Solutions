import pytest_asyncio
"""
Test Database Query Optimization

Verifies that N+1 queries are prevented and query optimization works correctly.
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))



import asyncio
import time
from typing import List
from unittest.mock import AsyncMock, MagicMock, Mock, patch
from uuid import uuid4

import pytest
from tests.fixtures.agents import mock_llm
from sqlalchemy import create_engine, event, select, Column, String, Integer, ForeignKey
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import selectinload, joinedload, relationship, declarative_base
from sqlalchemy.ext.declarative import declarative_base

from database.core.query_optimizer import (
    QueryOptimizer, DataLoader, QueryAnalyzer, optimize_query
)
from database.core.repositories import (
    UserRepository, CourseRepository, LessonRepository
)
# Import real models for repository tests
from database.models.models import User, Course, Lesson, Content, Enrollment, UserProgress, Quiz, QuizAttempt

# Create test models for SQLAlchemy testing
Base = declarative_base()

class TestModel(Base):
    __tablename__ = 'test_model'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    
    # Relationships for testing
    posts = relationship("TestPost", back_populates="model")
    comments = relationship("TestComment", back_populates="model")
    user_id = Column(Integer, ForeignKey("test_user.id"))
    user = relationship("TestUser", back_populates="models")

class TestPost(Base):
    __tablename__ = 'test_post'
    id = Column(Integer, primary_key=True)
    model_id = Column(Integer, ForeignKey("test_model.id"))
    model = relationship("TestModel", back_populates="posts")
    comments = relationship("TestComment", back_populates="post")

class TestComment(Base):
    __tablename__ = 'test_comment'
    id = Column(Integer, primary_key=True)
    model_id = Column(Integer, ForeignKey("test_model.id"))
    model = relationship("TestModel", back_populates="comments")
    post_id = Column(Integer, ForeignKey("test_post.id"))
    post = relationship("TestPost", back_populates="comments")
    author_id = Column(Integer, ForeignKey("test_user.id"))
    author = relationship("TestUser", back_populates="comments")

class TestUser(Base):
    __tablename__ = 'test_user'
    id = Column(Integer, primary_key=True)
    models = relationship("TestModel", back_populates="user")
    comments = relationship("TestComment", back_populates="author")


class TestQueryOptimizer:
    """Test the QueryOptimizer class"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.optimizer = QueryOptimizer()
        self.test_model = TestModel
    
    def test_optimize_relationships_selectinload(self):
        """Test optimization with selectinload strategy"""
        query = select(self.test_model)
        
        optimized = self.optimizer.optimize_relationships(
            query,
            self.test_model,
            ["posts", "comments"],
            strategy="selectinload"
        )
        
        # Verify options were added - check that the query has load options
        assert optimized is not None
        # Check that options were applied
        assert len(optimized._with_options) > 0
    
    def test_optimize_relationships_joinedload(self):
        """Test optimization with joinedload strategy"""
        query = select(self.test_model)
        
        optimized = self.optimizer.optimize_relationships(
            query,
            self.test_model,
            ["user"],
            strategy="joinedload"
        )
        
        assert optimized is not None
        assert len(optimized._with_options) > 0
    
    def test_optimize_relationships_nested(self):
        """Test optimization with nested relationships"""
        query = select(self.test_model)
        
        optimized = self.optimizer.optimize_relationships(
            query,
            self.test_model,
            ["posts.comments.author"],
            strategy="selectinload"
        )
        
        assert optimized is not None
        assert len(optimized._with_options) > 0
    
    def test_cache_and_retrieve(self):
        """Test query result caching"""
        test_data = {"id": 1, "name": "Test"}
        cache_key = "test_key"
        
        # Cache data
        self.optimizer.cache_query_result(cache_key, test_data, ttl=10)
        
        # Retrieve cached data
        cached = self.optimizer.get_cached_result(cache_key)
        assert cached == test_data
        
        # Test expired cache
        self.optimizer.cache_query_result("expired", test_data, ttl=-1)
        expired = self.optimizer.get_cached_result("expired")
        assert expired is None
    
    def test_clear_cache(self):
        """Test cache clearing"""
        # Add multiple cache entries
        self.optimizer.cache_query_result("key1", {"data": 1}, ttl=10)
        self.optimizer.cache_query_result("key2", {"data": 2}, ttl=10)
        self.optimizer.cache_query_result("other", {"data": 3}, ttl=10)
        
        # Clear with pattern
        self.optimizer.clear_cache(pattern="key")
        
        assert self.optimizer.get_cached_result("key1") is None
        assert self.optimizer.get_cached_result("key2") is None
        assert self.optimizer.get_cached_result("other") is not None
        
        # Clear all
        self.optimizer.clear_cache()
        assert self.optimizer.get_cached_result("other") is None
    
    def test_performance_metrics(self):
        """Test performance metric recording"""
        # Record metrics
        self.optimizer.record_query_performance("select_users", 50.5, 100)
        self.optimizer.record_query_performance("select_users", 45.3, 95)
        self.optimizer.record_query_performance("select_posts", 120.0, 500)
        
        # Get stats for specific query
        stats = self.optimizer.get_performance_stats("select_users")
        assert stats["count"] == 2
        assert stats["avg_duration_ms"] == pytest.approx(47.9, 0.1)
        assert stats["min_duration_ms"] == 45.3
        assert stats["max_duration_ms"] == 50.5
        assert stats["total_rows"] == 195
        
        # Get all stats
        all_stats = self.optimizer.get_performance_stats()
        assert "select_users" in all_stats
        assert "select_posts" in all_stats


class TestDataLoader:
    """Test the DataLoader class"""
    
    @pytest.fixture
    def mock_session(self):
        """Create mock async session"""
        session = AsyncMock(spec=AsyncSession)
        return session
    
    @pytest.fixture
    def test_model_class(self):
        """Return test model class"""
        return TestModel
    
    @pytest.mark.asyncio(loop_scope="function")
    @pytest.mark.asyncio(loop_scope="function")
    @pytest.mark.asyncio
async def test_load_single_entity(self, mock_session, test_model_class):
        """Test loading single entity"""
        loader = DataLoader(mock_session)
        
        # Setup mock entity
        mock_entity = Mock()
        mock_entity.id = 1
        
        # Mock query execution
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_entity
        mock_session.execute.return_value = mock_result
        
        # Load entity
        result = await loader.load(test_model_class, mock_entity.id)
        
        assert result == mock_entity
        assert loader.cache[f"{test_model_class.__name__}:{mock_entity.id}"] == mock_entity
        
        # Load again (should use cache)
        mock_session.execute.reset_mock()
        cached_result = await loader.load(test_model_class, mock_entity.id)
        
        assert cached_result == mock_entity
        mock_session.execute.assert_not_called()
    
    @pytest.mark.asyncio(loop_scope="function")
    @pytest.mark.asyncio
async def test_load_many_entities(self, mock_session, test_model_class):
        """Test loading multiple entities"""
        loader = DataLoader(mock_session)
        
        # Setup mock entities
        entities = [Mock(id=i) for i in range(1, 6)]
        
        # Mock query execution
        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = entities
        mock_session.execute.return_value = mock_result
        
        # Load entities
        ids = [e.id for e in entities]
        results = await loader.load_many(test_model_class, ids)
        
        assert len(results) == 5
        assert all(e in results for e in entities)
        
        # Verify caching
        for entity in entities:
            cache_key = f"{test_model_class.__name__}:{entity.id}"
            assert cache_key in loader.cache
    
    @pytest.mark.asyncio(loop_scope="function")
    @pytest.mark.asyncio
async def test_load_with_relationships(self, mock_session, test_model_class):
        """Test loading with eager relationships"""
        loader = DataLoader(mock_session)
        
        # Setup mock entity
        mock_entity = Mock()
        mock_entity.id = 1
        
        # Mock query execution
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_entity
        mock_session.execute.return_value = mock_result
        
        # Load with relationships
        result = await loader.load(
            test_model_class,
            mock_entity.id,
            relationships=["posts", "comments"]
        )
        
        assert result == mock_entity
        mock_session.execute.assert_called_once()


class TestQueryAnalyzer:
    """Test the QueryAnalyzer class"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.analyzer = QueryAnalyzer()
    
    def test_detect_n_plus_one_pattern(self):
        """Test N+1 query pattern detection"""
        # Simulate N+1 queries
        queries = [
            "SELECT * FROM users",
            "SELECT * FROM posts WHERE user_id = 1",
            "SELECT * FROM posts WHERE user_id = 2",
            "SELECT * FROM posts WHERE user_id = 3",
            "SELECT * FROM posts WHERE user_id = 4",
            "SELECT * FROM posts WHERE user_id = 5",
            "SELECT * FROM posts WHERE user_id = 6",
            "SELECT * FROM posts WHERE user_id = 7",
            "SELECT * FROM posts WHERE user_id = 8",
            "SELECT * FROM posts WHERE user_id = 9",
            "SELECT * FROM posts WHERE user_id = 10",
            "SELECT * FROM posts WHERE user_id = 11",
        ]
        
        patterns = self.analyzer.analyze_query_pattern(queries)
        
        assert len(patterns) > 0
        assert patterns[0]["type"] == "potential_n_plus_one"
        assert patterns[0]["count"] == 11
        assert "batch loading" in patterns[0]["recommendation"]
    
    def test_suggest_optimizations(self):
        """Test optimization suggestions"""
        mock_model = Mock()
        mock_model.__name__ = "User"
        
        # Simulate repeated relationship access
        access_patterns = [
            "posts", "posts", "posts", "posts", "posts", "posts",
            "comments", "comments", "comments",
            "profile"
        ]
        
        suggestions = self.analyzer.suggest_optimizations(
            mock_model,
            access_patterns
        )
        
        assert len(suggestions) == 1  # Only posts exceeds threshold
        assert suggestions[0]["relationship"] == "posts"
        assert suggestions[0]["access_count"] == 6
        assert "selectinload" in suggestions[0]["suggestion"]


class TestOptimizeDecorator:
    """Test the optimize_query decorator"""
    
    @pytest.mark.asyncio(loop_scope="function")
    @pytest.mark.asyncio
async def test_decorator_with_caching(self):
        """Test optimize_query decorator with caching"""
        call_count = 0
        
        @optimize_query(cache_ttl=5)
        async def get_users():
            nonlocal call_count
            call_count += 1
            return [{"id": 1}, {"id": 2}]
        
        # First call
        result1 = await get_users()
        assert call_count == 1
        assert len(result1) == 2
        
        # Second call (should use cache)
        result2 = await get_users()
        assert call_count == 1  # Not incremented
        assert result1 == result2
    
    @pytest.mark.asyncio(loop_scope="function")
    @pytest.mark.asyncio
async def test_decorator_performance_tracking(self):
        """Test performance tracking in decorator"""
        from apps.backend.core.database.query_optimizer import optimizer
        
        @optimize_query()
        async def slow_query():
            await asyncio.sleep(0.1)
            return [{"id": 1}]
        
        await slow_query()
        
        # Check performance was recorded
        stats = optimizer.get_performance_stats("slow_query")
        assert stats["count"] == 1
        assert stats["avg_duration_ms"] > 100  # At least 100ms


class TestRepositoryOptimization:
    """Test repository classes with optimization"""
    
    @pytest.fixture
    def mock_session(self):
        """Create mock async session"""
        session = AsyncMock(spec=AsyncSession)
        return session
    
    @pytest.mark.asyncio(loop_scope="function")
    @pytest.mark.asyncio
async def test_user_repository_optimized_queries(self, mock_session, mock_llm):
        """Test UserRepository prevents N+1 queries"""
        repo = UserRepository(mock_session)
        
        # Mock user with relationships
        mock_user = Mock(spec=User)
        mock_user.id = uuid4()
        mock_user.enrollments = [Mock() for _ in range(3)]
        mock_user.achievements = [Mock() for _ in range(2)]
        
        # Mock query execution
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_session.execute.return_value = mock_result
        
        # Get user with enrollments (should use eager loading)
        user = await repo.get_user_with_enrollments(mock_user.id)
        
        assert user == mock_user
        # Verify only one query was executed
        assert mock_session.execute.call_count == 1
    
    @pytest.mark.asyncio(loop_scope="function")
    @pytest.mark.asyncio
async def test_course_repository_enrollment_count(self, mock_session, mock_llm):
        """Test CourseRepository gets enrollment count efficiently"""
        repo = CourseRepository(mock_session)
        
        # Mock courses with counts
        mock_rows = [
            (Mock(id=uuid4(), title="Course 1"), 25),
            (Mock(id=uuid4(), title="Course 2"), 30),
        ]
        
        # Mock query execution
        mock_result = Mock()
        mock_result.__iter__ = Mock(return_value=iter(mock_rows))
        mock_session.execute.return_value = mock_result
        
        # Get courses with enrollment count
        courses = await repo.get_courses_with_enrollment_count()
        
        assert len(courses) == 2
        assert courses[0]["enrollment_count"] == 25
        assert courses[1]["enrollment_count"] == 30
        # Verify single query
        assert mock_session.execute.call_count == 1


class TestN1QueryPrevention:
    """Integration tests for N+1 query prevention"""
    
    @pytest.fixture
    def mock_session(self):
        """Create mock async session"""
        session = AsyncMock(spec=AsyncSession)
        return session
    
    @pytest.mark.asyncio(loop_scope="function")
    @pytest.mark.asyncio
async def test_prevents_n_plus_one_in_dashboard(self, mock_session, mock_llm):
        """Test that dashboard data loading prevents N+1"""
        repo = UserRepository(mock_session)
        
        # Mock complex user data
        mock_user = Mock(spec=User)
        mock_user.id = uuid4()
        mock_user.username = "testuser"
        mock_user.email = "test@example.com"
        mock_user.role = Mock(value="student")
        
        # Mock related data
        mock_user.enrollments = [
            Mock(course_id=uuid4(), course=Mock(title=f"Course {i}"), enrolled_at=Mock(isoformat=lambda: "2025-01-01"))
            for i in range(5)
        ]
        mock_user.progress_records = [
            Mock(lesson_id=uuid4(), lesson=Mock(title=f"Lesson {i}"), progress_percentage=80, completed=False)
            for i in range(10)
        ]
        from datetime import datetime, timedelta
        base_time = datetime(2025, 1, 1)
        mock_user.quiz_attempts = [
            Mock(quiz_id=uuid4(), quiz=Mock(title=f"Quiz {i}"), score=85, 
                 attempted_at=base_time - timedelta(days=i))
            for i in range(3)
        ]
        mock_user.achievements = [
            Mock(id=uuid4(), title=f"Achievement {i}", earned_at=Mock(isoformat=lambda: "2025-01-01"))
            for i in range(2)
        ]
        
        # Mock query execution
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_session.execute.return_value = mock_result
        
        # Get dashboard data (should load everything in one query)
        dashboard_data = await repo.get_user_dashboard_data(mock_user.id)
        
        # Verify data structure
        assert dashboard_data["user"]["username"] == "testuser"
        assert len(dashboard_data["enrollments"]) == 5
        assert len(dashboard_data["progress"]) == 10
        assert len(dashboard_data["recent_quizzes"]) == 3
        assert len(dashboard_data["achievements"]) == 2
        
        # Verify only ONE query was executed (no N+1)
        assert mock_session.execute.call_count == 1
    
    def test_query_count_tracking(self):
        """Test that we can track query counts for N+1 detection"""
        queries_executed = []
        
        # Mock query tracking
        def track_query(query_string):
            queries_executed.append(query_string)
        
        # Simulate queries
        track_query("SELECT * FROM users WHERE id = 1")
        for i in range(10):
            track_query(f"SELECT * FROM posts WHERE user_id = 1")
        
        # Analyze for N+1
        analyzer = QueryAnalyzer()
        patterns = analyzer.analyze_query_pattern(queries_executed)
        
        # Should detect N+1 pattern
        assert any(p["type"] == "potential_n_plus_one" for p in patterns)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])