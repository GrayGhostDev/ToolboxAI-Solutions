import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

"""
Comprehensive Test Suite for Enhanced Content Pipeline
Tests all components of the Week 2 implementation
"""

import asyncio
import json
import pytest
from datetime import datetime, timedelta
from typing import Dict, Any, List
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from uuid import uuid4

import pytest_asyncio
from fastapi.testclient import TestClient
from fastapi import WebSocket
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

# Import components to test
from core.agents.enhanced_content_pipeline import (
    EnhancedContentPipeline,
    PipelineState,
    PipelineStage,
    ContentGenerationRequest
)
from core.agents.content_quality_validator import (
    ContentQualityValidator,
    ValidationReport,
    QualityScore,
    ValidationIssue
)
from core.agents.adaptive_learning_engine import (
    AdaptiveLearningEngine,
    LearnerProfile,
    DifficultyLevel,
    LearnerMetrics
)
from core.agents.multi_modal_generator import (
    MultiModalGenerator,
    GenerationRequest,
    GeneratedContent,
    ContentModality
)
from tests.fixtures.pusher_test_utils import (
    WebSocketPipelineManager
)
from database.models import (
    EnhancedContentGeneration,
    ContentQualityMetrics,
    LearningProfile
)


# Fixtures
@pytest.fixture
async def async_db_session():
    """Create async database session for testing"""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False
    )

    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as session:
        yield session


@pytest.fixture
def mock_redis():
    """Mock Redis client"""
    redis = AsyncMock()
    redis.get = AsyncMock(return_value=None)
    redis.set = AsyncMock(return_value=True)
    redis.setex = AsyncMock(return_value=True)
    redis.delete = AsyncMock(return_value=True)
    return redis


@pytest.fixture
def mock_llm():
    """Mock LLM for testing"""
    llm = AsyncMock()
    llm.ainvoke = AsyncMock(return_value="Generated content")
    llm.agenerate = AsyncMock(return_value=MagicMock(generations=[[MagicMock(text="Generated")]]))
    return llm


@pytest.fixture
async def pipeline():
    """Create enhanced content pipeline instance"""
    with patch('core.agents.enhanced_content_pipeline.get_llm') as mock_get_llm:
        mock_get_llm.return_value = AsyncMock()
        pipeline = EnhancedContentPipeline(
            name="test-pipeline",
            description="Test pipeline"
        )
        await pipeline.initialize()
        yield pipeline


@pytest.fixture
async def quality_validator():
    """Create content quality validator instance"""
    validator = ContentQualityValidator(
        name="test-validator",
        description="Test validator"
    )
    await validator.initialize()
    return validator


@pytest.fixture
async def adaptive_engine():
    """Create adaptive learning engine instance"""
    engine = AdaptiveLearningEngine(
        name="test-engine",
        description="Test adaptive engine"
    )
    await engine.initialize()
    return engine


@pytest.fixture
async def multi_modal_generator(mock_llm):
    """Create multi-modal generator instance"""
    with patch('core.agents.multi_modal_generator.get_llm') as mock_get_llm:
        mock_get_llm.return_value = mock_llm
        generator = MultiModalGenerator(
            name="test-generator",
            description="Test generator"
        )
        await generator.initialize()
        yield generator


@pytest.fixture
async def websocket_manager(mock_redis):
    """Create WebSocket pipeline manager"""
    manager = WebSocketPipelineManager()
    manager.redis = mock_redis
    return manager


# Unit Tests - Enhanced Content Pipeline
class TestEnhancedContentPipeline:
    """Test suite for Enhanced Content Pipeline Orchestrator"""

    @pytest.mark.asyncio
    async def test_pipeline_initialization(self, pipeline):
        """Test pipeline initializes with correct stages"""
        assert pipeline.name == "test-pipeline"
        assert pipeline.workflow is not None
        assert len(pipeline.stages) == 5
        assert PipelineStage.IDEATION in pipeline.stages

    @pytest.mark.asyncio
    async def test_pipeline_state_creation(self, pipeline):
        """Test creation of pipeline state"""
        request = ContentGenerationRequest(
            topic="Roblox Coding",
            age_group="10-12",
            difficulty="intermediate",
            content_type="lesson",
            learning_objectives=["Learn loops", "Understand variables"]
        )

        state = pipeline.create_initial_state(request)

        assert state.pipeline_id is not None
        assert state.current_stage == PipelineStage.IDEATION
        assert state.request == request
        assert state.progress == 0.0

    @pytest.mark.asyncio
    async def test_ideation_stage(self, pipeline):
        """Test ideation stage execution"""
        state = PipelineState(
            pipeline_id=str(uuid4()),
            current_stage=PipelineStage.IDEATION,
            request=ContentGenerationRequest(
                topic="Game Development",
                age_group="8-10",
                difficulty="beginner"
            )
        )

        with patch.object(pipeline, 'ideation_agent') as mock_agent:
            mock_agent.execute = AsyncMock(return_value={
                "ideas": ["idea1", "idea2"],
                "selected_concept": "Game basics"
            })

            result = await pipeline._ideation_stage(state)

            assert "ideation_output" in result.outputs
            assert result.progress > 0
            mock_agent.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_generation_stage(self, pipeline):
        """Test content generation stage"""
        state = PipelineState(
            pipeline_id=str(uuid4()),
            current_stage=PipelineStage.GENERATION,
            outputs={"ideation_output": {"concept": "test"}}
        )

        with patch.object(pipeline, 'generation_agent') as mock_agent:
            mock_agent.execute = AsyncMock(return_value={
                "content": "Generated lesson",
                "scripts": ["script1.lua"],
                "assets": []
            })

            result = await pipeline._generation_stage(state)

            assert "generation_output" in result.outputs
            assert result.current_stage == PipelineStage.GENERATION

    @pytest.mark.asyncio
    async def test_validation_stage(self, pipeline):
        """Test validation stage with quality checks"""
        state = PipelineState(
            pipeline_id=str(uuid4()),
            current_stage=PipelineStage.VALIDATION,
            outputs={
                "generation_output": {
                    "content": "Test content",
                    "scripts": []
                }
            }
        )

        with patch.object(pipeline, 'validation_agent') as mock_agent:
            mock_agent.execute = AsyncMock(return_value={
                "quality_score": 0.85,
                "issues": [],
                "passed": True
            })

            result = await pipeline._validation_stage(state)

            assert "validation_output" in result.outputs
            assert result.outputs["validation_output"]["passed"] is True

    @pytest.mark.asyncio
    async def test_pipeline_error_handling(self, pipeline):
        """Test pipeline handles errors gracefully"""
        state = PipelineState(
            pipeline_id=str(uuid4()),
            current_stage=PipelineStage.IDEATION
        )

        with patch.object(pipeline, 'ideation_agent') as mock_agent:
            mock_agent.execute = AsyncMock(side_effect=Exception("Test error"))

            result = await pipeline._ideation_stage(state)

            assert "error" in result.metadata
            assert result.current_stage == PipelineStage.FAILED


# Unit Tests - Content Quality Validator
class TestContentQualityValidator:
    """Test suite for Content Quality Validator"""

    @pytest.mark.asyncio
    async def test_educational_value_validation(self, quality_validator):
        """Test educational value assessment"""
        content = {
            "text": "Learn about variables in programming",
            "learning_objectives": ["Understand variables"],
            "exercises": ["Create a variable"]
        }

        score = await quality_validator._validate_educational_value(
            content, target_age=10
        )

        assert isinstance(score, QualityScore)
        assert 0 <= score.score <= 1.0
        assert score.dimension == "educational_value"

    @pytest.mark.asyncio
    async def test_safety_compliance(self, quality_validator):
        """Test content safety validation"""
        content = {
            "text": "Safe educational content for kids",
            "scripts": ["print('Hello World')"]
        }

        issues = await quality_validator._check_safety_compliance(
            content, target_age=8
        )

        assert isinstance(issues, list)
        assert all(isinstance(i, ValidationIssue) for i in issues)

    @pytest.mark.asyncio
    async def test_auto_fix_capability(self, quality_validator):
        """Test auto-fix for common issues"""
        content = {
            "text": "learnprogramming",  # Missing spaces
            "code": "print('test')"
        }

        fixed = await quality_validator._auto_fix_issues(content, [
            ValidationIssue(
                severity="low",
                category="formatting",
                message="Missing spaces",
                suggestion="Add spaces between words"
            )
        ])

        assert fixed != content

    @pytest.mark.asyncio
    async def test_comprehensive_validation(self, quality_validator):
        """Test full validation pipeline"""
        content = {
            "title": "Introduction to Coding",
            "text": "Learn the basics of programming",
            "scripts": ["local x = 10"],
            "difficulty": "beginner"
        }

        report = await quality_validator.validate_content(
            content=content,
            content_type="lesson",
            target_age=10
        )

        assert isinstance(report, ValidationReport)
        assert report.overall_score >= 0
        assert isinstance(report.scores, dict)
        assert isinstance(report.issues, list)


# Unit Tests - Adaptive Learning Engine
class TestAdaptiveLearningEngine:
    """Test suite for Adaptive Learning Engine"""

    @pytest.mark.asyncio
    async def test_learner_profile_creation(self, adaptive_engine):
        """Test creation of learner profile"""
        profile = await adaptive_engine.create_learner_profile(
            user_id="test-user-123",
            age=10,
            skill_level="beginner",
            interests=["gaming", "art"]
        )

        assert isinstance(profile, LearnerProfile)
        assert profile.user_id == "test-user-123"
        assert profile.current_zpd is not None

    @pytest.mark.asyncio
    async def test_difficulty_adjustment(self, adaptive_engine):
        """Test dynamic difficulty adjustment"""
        # Test increasing difficulty for high performance
        level, adjustment = await adaptive_engine.optimize_difficulty(
            user_id="test-user",
            performance=0.9
        )

        assert level in [DifficultyLevel.INTERMEDIATE, DifficultyLevel.ADVANCED]
        assert adjustment > 0

        # Test decreasing difficulty for low performance
        level, adjustment = await adaptive_engine.optimize_difficulty(
            user_id="test-user",
            performance=0.3
        )

        assert level in [DifficultyLevel.BEGINNER, DifficultyLevel.INTERMEDIATE]
        assert adjustment < 0

    @pytest.mark.asyncio
    async def test_learning_metrics_tracking(self, adaptive_engine):
        """Test tracking of learning metrics"""
        metrics = LearnerMetrics(
            user_id="test-user",
            completion_rate=0.75,
            accuracy=0.85,
            engagement_score=0.9,
            time_on_task=1200,
            attempts_count=3
        )

        await adaptive_engine.update_metrics(metrics)

        retrieved = await adaptive_engine.get_metrics("test-user")
        assert retrieved.accuracy == 0.85
        assert retrieved.engagement_score == 0.9

    @pytest.mark.asyncio
    async def test_personalized_recommendations(self, adaptive_engine):
        """Test generation of personalized recommendations"""
        recommendations = await adaptive_engine.generate_recommendations(
            user_id="test-user",
            current_performance=0.7,
            interests=["coding", "games"]
        )

        assert isinstance(recommendations, list)
        assert len(recommendations) > 0
        assert all("topic" in rec for rec in recommendations)


# Unit Tests - Multi-Modal Generator
class TestMultiModalGenerator:
    """Test suite for Multi-Modal Content Generator"""

    @pytest.mark.asyncio
    async def test_text_generation(self, multi_modal_generator):
        """Test text content generation"""
        request = GenerationRequest(
            modality=ContentModality.TEXT,
            topic="Variables in Programming",
            parameters={"length": "medium", "style": "educational"}
        )

        content = await multi_modal_generator._generate_text(request)

        assert isinstance(content, GeneratedContent)
        assert content.modality == ContentModality.TEXT
        assert content.content is not None

    @pytest.mark.asyncio
    async def test_code_generation(self, multi_modal_generator):
        """Test Luau code generation"""
        request = GenerationRequest(
            modality=ContentModality.CODE,
            topic="Player movement script",
            parameters={"language": "luau", "complexity": "beginner"}
        )

        content = await multi_modal_generator._generate_code(request)

        assert isinstance(content, GeneratedContent)
        assert content.modality == ContentModality.CODE
        assert "script" in content.metadata

    @pytest.mark.asyncio
    async def test_multi_modal_coordination(self, multi_modal_generator):
        """Test generation across multiple modalities"""
        request = GenerationRequest(
            modality=ContentModality.MULTI,
            topic="Complete lesson on loops",
            parameters={
                "include_text": True,
                "include_code": True,
                "include_visual": True
            }
        )

        contents = await multi_modal_generator.generate(request)

        assert isinstance(contents, list)
        assert len(contents) >= 2
        modalities = [c.modality for c in contents]
        assert ContentModality.TEXT in modalities


# Unit Tests - WebSocket Pipeline Manager
class TestWebSocketPipelineManager:
    """Test suite for WebSocket Pipeline Manager"""

    @pytest.mark.asyncio
    async def test_websocket_connection(self, websocket_manager):
        """Test WebSocket connection handling"""
        websocket = AsyncMock(spec=WebSocket)
        pipeline_id = str(uuid4())

        await websocket_manager.connect(websocket, pipeline_id)

        assert pipeline_id in websocket_manager.connections
        assert websocket in websocket_manager.connections[pipeline_id]
        websocket.accept.assert_called_once()

    @pytest.mark.asyncio
    async def test_state_update_broadcast(self, websocket_manager):
        """Test broadcasting state updates"""
        websocket = AsyncMock(spec=WebSocket)
        pipeline_id = str(uuid4())

        websocket_manager.connections[pipeline_id] = {websocket}

        await websocket_manager.update_pipeline_state(
            pipeline_id=pipeline_id,
            stage=PipelineStage.GENERATION,
            progress=50.0,
            message="Generating content"
        )

        websocket.send_json.assert_called()
        assert pipeline_id in websocket_manager.pipeline_states

    @pytest.mark.asyncio
    async def test_error_notification(self, websocket_manager):
        """Test error notification to clients"""
        websocket = AsyncMock(spec=WebSocket)
        pipeline_id = str(uuid4())

        websocket_manager.connections[pipeline_id] = {websocket}

        await websocket_manager.send_error(
            pipeline_id=pipeline_id,
            error_message="Test error",
            error_details={"code": 500}
        )

        websocket.send_json.assert_called_with({
            "type": "error",
            "pipeline_id": pipeline_id,
            "message": "Test error",
            "details": {"code": 500},
            "timestamp": pytest.Any(str)
        })

    @pytest.mark.asyncio
    async def test_heartbeat_mechanism(self, websocket_manager):
        """Test heartbeat keeps connection alive"""
        websocket = AsyncMock(spec=WebSocket)
        pipeline_id = str(uuid4())

        # Start heartbeat task
        task = asyncio.create_task(
            websocket_manager._heartbeat(websocket, pipeline_id)
        )

        # Wait briefly
        await asyncio.sleep(0.1)

        # Cancel task
        task.cancel()

        try:
            await task
        except asyncio.CancelledError:
            pass


# Integration Tests
class TestPipelineIntegration:
    """Integration tests for complete pipeline flow"""

    @pytest.mark.asyncio
    async def test_full_pipeline_execution(self, pipeline, quality_validator):
        """Test complete pipeline from request to completion"""
        request = ContentGenerationRequest(
            topic="Introduction to Roblox Scripting",
            age_group="10-12",
            difficulty="beginner",
            content_type="interactive_lesson",
            learning_objectives=[
                "Understand basic scripting concepts",
                "Create first Roblox script",
                "Learn about game objects"
            ]
        )

        # Mock agent responses
        with patch.object(pipeline, 'ideation_agent') as mock_ideation, \
             patch.object(pipeline, 'generation_agent') as mock_generation, \
             patch.object(pipeline, 'validation_agent') as mock_validation:

            mock_ideation.execute = AsyncMock(return_value={
                "ideas": ["Interactive coding tutorial"],
                "selected_concept": "Learn by building"
            })

            mock_generation.execute = AsyncMock(return_value={
                "content": "Complete lesson content",
                "scripts": ["game.Workspace.Part.Touched"],
                "assets": ["tutorial_world.rbxl"]
            })

            mock_validation.execute = AsyncMock(return_value={
                "quality_score": 0.92,
                "issues": [],
                "passed": True
            })

            # Execute pipeline
            result = await pipeline.execute(request)

            assert result["status"] == "completed"
            assert result["quality_score"] >= 0.9
            assert "content" in result

    @pytest.mark.asyncio
    async def test_adaptive_content_generation(
        self, pipeline, adaptive_engine, multi_modal_generator
    ):
        """Test adaptive content generation based on learner profile"""
        # Create learner profile
        profile = await adaptive_engine.create_learner_profile(
            user_id="student-123",
            age=11,
            skill_level="intermediate",
            interests=["gaming", "puzzles"]
        )

        # Generate adapted content
        request = GenerationRequest(
            modality=ContentModality.MULTI,
            topic="Advanced loops and iterations",
            parameters={
                "learner_profile": profile,
                "adapt_to_zpd": True
            }
        )

        contents = await multi_modal_generator.generate(request)

        assert len(contents) > 0
        assert all(c.metadata.get("adapted") for c in contents)


# Performance Tests
class TestPerformance:
    """Performance and load tests"""

    @pytest.mark.asyncio
    async def test_concurrent_pipeline_execution(self, pipeline):
        """Test multiple concurrent pipeline executions"""
        requests = [
            ContentGenerationRequest(
                topic=f"Topic {i}",
                age_group="10-12",
                difficulty="beginner"
            )
            for i in range(5)
        ]

        # Execute pipelines concurrently
        tasks = [pipeline.execute(req) for req in requests]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Verify all completed
        assert len(results) == 5
        assert all(not isinstance(r, Exception) for r in results)

    @pytest.mark.asyncio
    async def test_websocket_multiple_connections(self, websocket_manager):
        """Test handling multiple WebSocket connections"""
        pipeline_id = str(uuid4())
        websockets = [AsyncMock(spec=WebSocket) for _ in range(10)]

        # Connect all websockets
        for ws in websockets:
            await websocket_manager.connect(ws, pipeline_id)

        # Send update to all
        await websocket_manager.update_pipeline_state(
            pipeline_id=pipeline_id,
            stage=PipelineStage.PROCESSING,
            progress=50.0,
            message="Processing"
        )

        # Verify all received update
        for ws in websockets:
            ws.send_json.assert_called()


# End-to-End Tests
class TestEndToEnd:
    """End-to-end tests with real components"""

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_complete_content_generation_flow(self):
        """Test complete flow from API to database"""
        # This would test the actual API endpoints
        # Requires running backend server
        pass

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_websocket_real_time_updates(self):
        """Test real-time updates via WebSocket"""
        # This would test actual WebSocket connections
        # Requires running backend server
        pass


# Run tests with coverage
if __name__ == "__main__":
    pytest.main([
        __file__,
        "-v",
        "--cov=core.agents",
        "--cov=apps.backend.services",
        "--cov-report=html",
        "--cov-report=term-missing"
    ])