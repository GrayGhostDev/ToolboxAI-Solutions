"""
Database Integration Module for Agent System

Provides real data access to agents from the educational_platform database.
Replaces mock data with actual database queries.
"""

import logging
import json
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timezone
import os
import asyncio
import uuid
from contextlib import asynccontextmanager

# Import SQLAlchemy components
from sqlalchemy import text, select, insert, update, delete, and_, or_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError, NoResultFound
import websockets

# Import project components
try:
    from toolboxai_settings import settings, should_use_real_data
except ImportError:
    # Fallback for when running from different directory
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from toolboxai_settings import settings, should_use_real_data

# Import database components from correct paths
try:
    # Try to import from parent project directory first
    import sys
    from pathlib import Path
    parent_dir = Path(__file__).parent.parent.parent
    if str(parent_dir) not in sys.path:
        sys.path.insert(0, str(parent_dir))
    
    from core.database.connection_manager import get_async_session, get_session, get_redis_client
    from core.database.repositories import (
        UserRepository, CourseRepository, LessonRepository, 
        ContentRepository, QuizRepository, ProgressRepository,
        AnalyticsRepository
    )
except ImportError as e:
    logging.warning(f"Could not import core.database components: {e}")
    # Fallback for testing - will use mock data
    get_async_session = None
    get_session = None
    get_redis_client = None

logger = logging.getLogger(__name__)


class AgentDatabaseIntegration:
    """Provides database access for all agents with environment-aware real/mock data switching"""
    
    def __init__(self):
        self.env_config = settings
        self.mcp_url = self.env_config.get_service_url("mcp")
        self._use_real_data = should_use_real_data() and not self.env_config.use_mock_database
        self._connection_pool = None
        self._redis_client = None
        self._initialized = False
        self._session_factory = None
        
        # Skip initialization during testing/imports
        if os.getenv("TESTING", "false").lower() == "true" or os.getenv("SKIP_DB_INIT", "false").lower() == "true":
            logger.debug("Skipping database initialization (testing mode or SKIP_DB_INIT set)")
            self._use_real_data = False
            self._initialized = False
        # Initialize connections if using real data (but not during imports)
        elif self._use_real_data and os.getenv("SKIP_AGENTS", "false").lower() != "true":
            self._init_connections()
        
    def _init_connections(self):
        """Initialize database connections with retry logic"""
        if not self._use_real_data:
            logger.info("Using mock data - skipping real database connections")
            return
        
        max_retries = 3
        for attempt in range(max_retries):
            try:
                # Skip sync database test - we only support async now
                logger.info("Database integration using async mode only")
                
                # Initialize Redis if available
                if get_redis_client:
                    # Note: get_redis_client might be async too
                    try:
                        if asyncio.iscoroutinefunction(get_redis_client):
                            # Handle async redis client
                            loop = asyncio.new_event_loop()
                            self._redis_client = loop.run_until_complete(get_redis_client())
                            loop.close()
                        else:
                            self._redis_client = get_redis_client()
                        
                        if self._redis_client:
                            self._redis_client.ping()
                            logger.info("Redis connection established for agents")
                    except Exception as e:
                        logger.warning(f"Redis initialization failed: {e}")
                
                self._initialized = True
                return
                
            except Exception as e:
                logger.warning(f"Database connection attempt {attempt + 1} failed: {e}")
                if attempt == max_retries - 1:
                    logger.error(f"Failed to initialize database after {max_retries} attempts")
                    # Fall back to mock data
                    self._use_real_data = False
                    logger.info("Falling back to mock data mode")
                else:
                    import time
                    time.sleep(2 ** attempt)  # Exponential backoff
            
    async def get_learning_objectives(self, subject: str = None, grade_level: int = None) -> List[Dict]:
        """Get learning objectives from database or return mock data"""
        if not self._use_real_data or not self._initialized:
            return self._get_mock_learning_objectives(subject, grade_level)
        
        try:
            async for session in get_async_session("educational_platform"):
                query = """
                    SELECT id, title, description, subject, grade_level, 
                           bloom_level, curriculum_standard, measurable, created_at, updated_at
                    FROM learning_objectives
                    WHERE 1=1
                """
                params = {}
                
                if subject:
                    query += " AND subject = :subject"
                    params["subject"] = subject
                    
                if grade_level:
                    query += " AND grade_level = :grade_level"
                    params["grade_level"] = grade_level
                    
                query += " ORDER BY created_at DESC LIMIT 10"
                
                # Use text() with bound parameters properly
                if params:
                    result = await session.execute(text(query).bindparams(**params))
                else:
                    result = await session.execute(text(query))
                objectives = []
                for row in result:
                    objectives.append({
                        "id": str(row[0]),
                        "title": row[1],
                        "description": row[2],
                        "subject": row[3],
                        "grade_level": row[4],
                        "bloom_level": row[5],
                        "curriculum_standard": row[6],
                        "measurable": row[7],
                        "created_at": row[8].isoformat() if row[8] else None,
                        "updated_at": row[9].isoformat() if row[9] else None
                    })
                    
                logger.info(f"Retrieved {len(objectives)} learning objectives from database")
                return objectives
                
        except Exception as e:
            logger.error(f"Error retrieving learning objectives: {e}")
            # Fall back to mock data on error
            return self._get_mock_learning_objectives(subject, grade_level)
    
    def _get_mock_learning_objectives(self, subject: str = None, grade_level: int = None) -> List[Dict]:
        """Return mock learning objectives for testing/development"""
        mock_objectives = [
            {
                "id": "mock-obj-1",
                "title": "Basic Programming Concepts",
                "description": "Understand fundamental programming concepts",
                "subject": subject or "Computer Science",
                "grade_level": grade_level or 6,
                "bloom_level": "understand",
                "curriculum_standard": "CSTA-1A-AP-10",
                "measurable": True,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat()
            },
            {
                "id": "mock-obj-2",
                "title": "Problem Solving",
                "description": "Develop problem-solving skills through coding",
                "subject": subject or "Computer Science",
                "grade_level": grade_level or 6,
                "bloom_level": "apply",
                "curriculum_standard": "CSTA-1A-AP-11",
                "measurable": True,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
        ]
        
        # Filter by subject if provided
        if subject:
            mock_objectives = [obj for obj in mock_objectives if obj["subject"].lower() == subject.lower()]
        
        logger.info(f"Using mock learning objectives (count: {len(mock_objectives)})")
        return mock_objectives
            
    async def get_educational_content(self, objective_id: str = None, subject: str = None, grade_level: int = None) -> List[Dict]:
        """Get educational content from database or return mock data"""
        if not self._use_real_data or not self._initialized:
            return self._get_mock_educational_content(objective_id, subject, grade_level)
        
        try:
            async for session in get_async_session("educational_platform"):
                query = """
                    SELECT c.id, c.title, c.description, c.subject, c.grade_level,
                           c.environment_type, c.content_data, c.generated_scripts, c.terrain_config,
                           c.difficulty_level, c.duration_minutes, c.is_published,
                           c.created_at, c.updated_at
                    FROM educational_content c
                    WHERE c.is_published = true
                """
                params = {}
                
                if subject:
                    query += " AND c.subject = :subject"
                    params["subject"] = subject
                    
                if grade_level:
                    query += " AND c.grade_level = :grade_level"
                    params["grade_level"] = grade_level
                    
                query += " ORDER BY c.created_at DESC LIMIT 10"
                
                # Use text() with bound parameters properly
                if params:
                    result = await session.execute(text(query).bindparams(**params))
                else:
                    result = await session.execute(text(query))
                content_items = []
                for row in result:
                    content_items.append({
                        "id": str(row[0]),
                        "title": row[1],
                        "description": row[2],
                        "subject": row[3],
                        "grade_level": row[4],
                        "environment_type": row[5],
                        "content_data": row[6],
                        "generated_scripts": row[7],
                        "terrain_config": row[8],
                        "difficulty_level": row[9],
                        "duration_minutes": row[10],
                        "is_published": row[11],
                        "created_at": row[12].isoformat() if row[12] else None,
                        "updated_at": row[13].isoformat() if row[13] else None
                    })
                    
                logger.info(f"Retrieved {len(content_items)} content items from database")
                return content_items
                
        except Exception as e:
            logger.error(f"Error retrieving educational content: {e}")
            return self._get_mock_educational_content(objective_id, subject, grade_level)
    
    def _get_mock_educational_content(self, objective_id: str = None, subject: str = None, grade_level: int = None) -> List[Dict]:
        """Return mock educational content for testing/development"""
        mock_content = [
            {
                "id": "mock-content-1",
                "title": "Introduction to Programming",
                "description": "Learn basic programming concepts in a fun Roblox environment",
                "subject": subject or "Computer Science",
                "grade_level": grade_level or 6,
                "environment_type": "classroom",
                "content_data": {
                    "activities": ["coding_challenges", "interactive_tutorials"],
                    "resources": ["video_tutorials", "practice_exercises"]
                },
                "generated_scripts": [],
                "terrain_config": {"size": "medium", "theme": "modern_classroom"},
                "difficulty_level": "beginner",
                "duration_minutes": 45,
                "is_published": True,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
        ]
        
        logger.info(f"Using mock educational content (count: {len(mock_content)})")
        return mock_content
            
    async def get_quiz_questions(self, subject: str = None, difficulty: str = None, grade_level: int = None) -> List[Dict]:
        """Get quiz questions from database or return mock data"""
        if not self._use_real_data or not self._initialized:
            return self._get_mock_quiz_questions(subject, difficulty, grade_level)
        
        try:
            async for session in get_async_session("educational_platform"):
                # Get quizzes with questions
                query = """
                    SELECT q.id, q.title, q.subject, q.grade_level, q.difficulty_progression,
                           qq.id as question_id, qq.question_text, qq.question_type, 
                           qq.correct_answer, qq.difficulty, qq.points, qq.hint, qq.explanation,
                           qq.question_data
                    FROM quizzes q
                    LEFT JOIN quiz_questions qq ON q.id = qq.quiz_id
                    WHERE 1=1
                """
                params = {}
                
                if subject:
                    query += " AND q.subject = :subject"
                    params["subject"] = subject
                    
                if grade_level:
                    query += " AND q.grade_level = :grade_level"
                    params["grade_level"] = grade_level
                    
                if difficulty:
                    query += " AND qq.difficulty = :difficulty"
                    params["difficulty"] = difficulty
                    
                query += " ORDER BY q.created_at DESC, qq.order_index LIMIT 50"
                
                result = await session.execute(text(query), params)
                
                # Group questions by quiz
                quiz_data = {}
                for row in result:
                    quiz_id = str(row[0])
                    if quiz_id not in quiz_data:
                        quiz_data[quiz_id] = {
                            "id": quiz_id,
                            "title": row[1],
                            "subject": row[2],
                            "grade_level": row[3],
                            "difficulty_progression": row[4],
                            "questions": []
                        }
                    
                    if row[5]:  # question_id exists
                        quiz_data[quiz_id]["questions"].append({
                            "id": str(row[5]),
                            "question_text": row[6],
                            "question_type": row[7],
                            "correct_answer": row[8],
                            "difficulty": row[9],
                            "points": row[10],
                            "hint": row[11],
                            "explanation": row[12],
                            "question_data": row[13] or {}
                        })
                
                quiz_list = list(quiz_data.values())
                logger.info(f"Retrieved {len(quiz_list)} quizzes with questions from database")
                return quiz_list
                
        except Exception as e:
            logger.error(f"Error retrieving quiz questions: {e}")
            return self._get_mock_quiz_questions(subject, difficulty, grade_level)
    
    def _get_mock_quiz_questions(self, subject: str = None, difficulty: str = None, grade_level: int = None) -> List[Dict]:
        """Return mock quiz questions for testing/development"""
        mock_quizzes = [
            {
                "id": "mock-quiz-1",
                "title": f"{subject or 'Programming'} Quiz",
                "subject": subject or "Computer Science",
                "grade_level": grade_level or 6,
                "difficulty_progression": {"adaptive": True},
                "questions": [
                    {
                        "id": "mock-q-1",
                        "question_text": "What is a variable in programming?",
                        "question_type": "multiple_choice",
                        "correct_answer": "A container for storing data",
                        "difficulty": difficulty or "easy",
                        "points": 1,
                        "hint": "Think about storage containers",
                        "explanation": "Variables store data values that can be used later",
                        "question_data": {
                            "options": [
                                "A container for storing data",
                                "A type of loop",
                                "A function parameter",
                                "A programming language"
                            ]
                        }
                    }
                ]
            }
        ]
        
        logger.info(f"Using mock quiz questions (count: {len(mock_quizzes)})")
        return mock_quizzes
            
    async def get_student_progress(self, student_id: Union[int, str, uuid.UUID]) -> Dict:
        """Get student progress data from database or return mock data"""
        if not self._use_real_data or not self._initialized:
            return self._get_mock_student_progress(student_id)
        
        try:
            # Convert student_id to UUID if needed
            if isinstance(student_id, (int, str)):
                try:
                    student_uuid = uuid.UUID(str(student_id))
                except ValueError:
                    # If not a valid UUID, search by username or email
                    student_uuid = await self._find_student_by_identifier(student_id)
                    if not student_uuid:
                        logger.warning(f"Student not found: {student_id}")
                        return {}
            else:
                student_uuid = student_id
            
            async for session in get_async_session("educational_platform"):
                # Get student info
                student_query = """
                    SELECT u.id, u.username, u.email, u.role, u.display_name, u.grade_level
                    FROM users u
                    WHERE u.id = :student_id AND u.role = 'student'
                """
                
                result = await session.execute(text(student_query), {"student_id": student_uuid})
                student_row = result.fetchone()
                
                if not student_row:
                    logger.warning(f"Student not found: {student_uuid}")
                    return {}
                    
                # Get progress data
                progress_query = """
                    SELECT up.content_id, up.progress_type, up.completion_percentage,
                           up.time_spent_seconds, up.best_score, up.mastery_level,
                           up.last_interaction, ec.title, ec.subject
                    FROM user_progress up
                    LEFT JOIN educational_content ec ON up.content_id = ec.id
                    WHERE up.user_id = :student_id
                    ORDER BY up.updated_at DESC
                    LIMIT 20
                """
                
                progress_result = await session.execute(text(progress_query), {"student_id": student_uuid})
                progress_items = []
                for row in progress_result:
                    progress_items.append({
                        "content_id": str(row[0]),
                        "progress_type": row[1],
                        "completion_percentage": float(row[2]) if row[2] else 0.0,
                        "time_spent_seconds": row[3] or 0,
                        "best_score": float(row[4]) if row[4] else None,
                        "mastery_level": row[5],
                        "last_interaction": row[6].isoformat() if row[6] else None,
                        "content_title": row[7],
                        "subject": row[8]
                    })
                    
                return {
                    "student_id": str(student_row[0]),
                    "username": student_row[1],
                    "email": student_row[2],
                    "display_name": student_row[4],
                    "grade_level": student_row[5],
                    "progress": progress_items
                }
                
        except Exception as e:
            logger.error(f"Error retrieving student progress: {e}")
            return self._get_mock_student_progress(student_id)
    
    async def _find_student_by_identifier(self, identifier: Union[str, int]) -> Optional[uuid.UUID]:
        """Find student UUID by username or email"""
        try:
            async for session in get_async_session("educational_platform"):
                query = """
                    SELECT id FROM users 
                    WHERE (username = :identifier OR email = :identifier) 
                    AND role = 'student'
                    LIMIT 1
                """
                result = await session.execute(text(query), {"identifier": str(identifier)})
                row = result.fetchone()
                return row[0] if row else None
        except Exception as e:
            logger.error(f"Error finding student by identifier: {e}")
            return None
    
    def _get_mock_student_progress(self, student_id: Union[int, str, uuid.UUID]) -> Dict:
        """Return mock student progress for testing/development"""
        mock_progress = {
            "student_id": str(student_id),
            "username": "mock_student",
            "email": "mock.student@example.com",
            "display_name": "Mock Student",
            "grade_level": 6,
            "progress": [
                {
                    "content_id": "mock-content-1",
                    "progress_type": "lesson",
                    "completion_percentage": 75.0,
                    "time_spent_seconds": 1800,
                    "best_score": 85.5,
                    "mastery_level": "developing",
                    "last_interaction": datetime.now(timezone.utc).isoformat(),
                    "content_title": "Introduction to Programming",
                    "subject": "Computer Science"
                }
            ]
        }
        
        logger.info(f"Using mock student progress for: {student_id}")
        return mock_progress
            
    async def save_generated_content(self, content_type: str, content_data: Dict, 
                                   created_by: Optional[Union[str, uuid.UUID]] = None) -> bool:
        """Save agent-generated content to database or simulate save in mock mode"""
        if not self._use_real_data or not self._initialized:
            logger.info(f"Mock mode: Simulating save of {content_type} content")
            return True
        
        try:
            # Convert created_by to UUID if needed
            created_by_uuid = None
            if created_by:
                try:
                    created_by_uuid = uuid.UUID(str(created_by)) if not isinstance(created_by, uuid.UUID) else created_by
                except ValueError:
                    logger.warning(f"Invalid created_by UUID: {created_by}")
            
            async for session in get_async_session("educational_platform"):
                insert_query = """
                    INSERT INTO educational_content (title, description, subject, grade_level,
                                                   environment_type, content_data, difficulty_level,
                                                   duration_minutes, terrain_size, max_students,
                                                   created_by, is_template, created_at, updated_at)
                    VALUES (:title, :description, :subject, :grade_level,
                           :environment_type, :content_data, :difficulty_level,
                           :duration_minutes, :terrain_size, :max_students,
                           :created_by, :is_template, NOW(), NOW())
                    RETURNING id
                """
                
                params = {
                    "title": content_data.get("title", f"Generated {content_type}"),
                    "description": content_data.get("description", f"AI-generated {content_type} content"),
                    "subject": content_data.get("subject", "General"),
                    "grade_level": content_data.get("grade_level", 6),
                    "environment_type": content_data.get("environment_type", "classroom"),
                    "difficulty_level": content_data.get("difficulty_level", "medium"),
                    "duration_minutes": content_data.get("duration_minutes", 30),
                    "terrain_size": content_data.get("terrain_size", "medium"),
                    "max_students": content_data.get("max_students", 30),
                    "content_data": json.dumps(content_data),
                    "created_by": created_by_uuid,
                    "is_template": content_data.get("is_template", False)
                }
                
                result = await session.execute(text(insert_query), params)
                content_id = result.fetchone()[0]
                await session.commit()
                
                logger.info(f"Saved generated {content_type} with ID {content_id}")
                
                # Cache the content ID in Redis if available
                if self._redis_client:
                    try:
                        cache_key = f"agent:generated_content:{content_id}"
                        value = json.dumps({"type": content_type, "created_at": datetime.now(timezone.utc).isoformat()})
                        # Value is str; some clients may expect bytes; ignore typing mismatch if any
                        self._redis_client.setex(cache_key, 3600, value)  # type: ignore[arg-type]
                    except Exception as cache_error:
                        logger.warning(f"Failed to cache content: {cache_error}")
                
                return True
                
        except Exception as e:
            logger.error(f"Error saving generated content: {e}")
            return False
            
    async def get_curriculum_standards(self, subject: str = None, grade_level: int = None) -> List[Dict]:
        """Get curriculum standards from database or return comprehensive mock data"""
        try:
            # Get learning objectives with curriculum standards
            objectives = await self.get_learning_objectives(subject, grade_level)
            
            standards = []
            for obj in objectives:
                if obj.get("curriculum_standard"):
                    standards.append({
                        "objective_id": obj["id"],
                        "subject": obj["subject"],
                        "grade_level": obj["grade_level"],
                        "title": obj["title"],
                        "standards": obj["curriculum_standard"],
                        "description": obj["description"]
                    })
            
            # Add comprehensive real standards based on subject
            additional_standards = self._get_real_curriculum_standards(subject, grade_level)
            standards.extend(additional_standards)
                
            logger.info(f"Retrieved {len(standards)} curriculum standards")
            return standards
            
        except Exception as e:
            logger.error(f"Error retrieving curriculum standards: {e}")
            return self._get_real_curriculum_standards(subject, grade_level)
    
    def _get_real_curriculum_standards(self, subject: str = None, grade_level: int = None) -> List[Dict]:
        """Return real curriculum standards based on Common Core, NGSS, etc."""
        standards = []
        
        if not subject or subject.lower() in ["mathematics", "math"]:
            standards.extend([
                {
                    "standard_code": "CCSS.MATH.CONTENT.6.EE.A.1",
                    "description": "Write and evaluate numerical expressions involving whole-number exponents",
                    "grade_level": 6,
                    "subject": "Mathematics"
                },
                {
                    "standard_code": "CCSS.MATH.CONTENT.7.EE.A.1",
                    "description": "Apply properties of operations to add, subtract, factor, and expand linear expressions",
                    "grade_level": 7,
                    "subject": "Mathematics"
                },
                {
                    "standard_code": "CCSS.MATH.CONTENT.7.G.B.4",
                    "description": "Know formulas for area and circumference of a circle",
                    "grade_level": 7,
                    "subject": "Mathematics"
                },
                {
                    "standard_code": "CCSS.MATH.CONTENT.8.F.A.1",
                    "description": "Understand that a function assigns exactly one output to each input",
                    "grade_level": 8,
                    "subject": "Mathematics"
                }
            ])
        
        if not subject or subject.lower() in ["science", "physics", "chemistry", "biology", "earth science"]:
            standards.extend([
                {
                    "standard_code": "MS-ESS1-2",
                    "description": "Analyze and interpret data on scale properties to describe objects in the solar system",
                    "grade_level": 7,
                    "subject": "Science"
                },
                {
                    "standard_code": "MS-PS1-1",
                    "description": "Develop models to describe atomic composition of simple molecules",
                    "grade_level": 7,
                    "subject": "Science"
                },
                {
                    "standard_code": "MS-LS1-1",
                    "description": "Conduct investigation to provide evidence that living things are made of cells",
                    "grade_level": 6,
                    "subject": "Science"
                },
                {
                    "standard_code": "5-ESS1-1",
                    "description": "Use observations to support arguments about the sun's brightness compared to other stars",
                    "grade_level": 5,
                    "subject": "Science"
                }
            ])
        
        if not subject or subject.lower() in ["computer science", "programming", "coding", "technology"]:
            standards.extend([
                {
                    "standard_code": "CSTA-1A-AP-08",
                    "description": "Model daily processes by creating and following algorithms",
                    "grade_level": 2,
                    "subject": "Computer Science"
                },
                {
                    "standard_code": "CSTA-1A-AP-10",
                    "description": "Develop programs with sequences and simple loops",
                    "grade_level": 4,
                    "subject": "Computer Science"
                },
                {
                    "standard_code": "CSTA-1A-AP-11",
                    "description": "Decompose steps needed to solve a problem into a precise sequence of instructions",
                    "grade_level": 5,
                    "subject": "Computer Science"
                },
                {
                    "standard_code": "CSTA-1B-AP-13",
                    "description": "Use an iterative process to plan development of a program",
                    "grade_level": 6,
                    "subject": "Computer Science"
                }
            ])
        
        # Filter by grade level if specified
        if grade_level:
            standards = [s for s in standards if s["grade_level"] == grade_level]
        
        # Filter by subject if specified
        if subject:
            standards = [s for s in standards if s["subject"].lower() == subject.lower()]
        
        return standards
            
    async def update_mcp_context(self, context_data: Dict, source: str = "agent_system", priority: int = 3):
        """Update MCP context with agent data"""
        try:
            async with websockets.connect(self.mcp_url) as websocket:
                message = {
                    "type": "update_context",
                    "context": context_data,
                    "source": source,
                    "priority": priority
                }
                await websocket.send(json.dumps(message))
                response = await websocket.recv()
                logger.info(f"Updated MCP context from {source}")
                return True
        except Exception as e:
            logger.error(f"Failed to update MCP context: {e}")
            return False
            
    async def get_mcp_context(self, source_filter: str = None) -> Dict:
        """Get current context from MCP"""
        try:
            async with websockets.connect(self.mcp_url) as websocket:
                query = {"type": "query_context"}
                if source_filter:
                    query["query"] = {"source": source_filter}
                    
                await websocket.send(json.dumps(query))
                response = await websocket.recv()
                data = json.loads(response)
                
                if data.get("type") == "query_response":
                    return data.get("data", {})
                return {}
        except Exception as e:
            logger.error(f"Failed to get MCP context: {e}")
            return {}


    @property
    def is_using_real_data(self) -> bool:
        """Check if currently using real data"""
        return self._use_real_data and self._initialized
    
    def get_connection_status(self) -> Dict[str, Any]:
        """Get current connection status"""
        return {
            "environment": self.env_config.environment.value,
            "use_real_data": self._use_real_data,
            "initialized": self._initialized,
            "redis_available": self._redis_client is not None,
            "database_configured": get_async_session is not None
        }


# Singleton instance for agent use
_agent_db_instance: Optional[AgentDatabaseIntegration] = None


def get_agent_database() -> AgentDatabaseIntegration:
    """Get or create singleton instance of AgentDatabaseIntegration"""
    global _agent_db_instance
    if _agent_db_instance is None:
        _agent_db_instance = AgentDatabaseIntegration()
    return _agent_db_instance


# For backward compatibility - create a lazy property
class LazyAgentDB:
    """Lazy wrapper for agent database to avoid initialization at import time"""
    def __getattr__(self, name):
        return getattr(get_agent_database(), name)
    
    def __repr__(self):
        return "<LazyAgentDB (not yet initialized)>"


# Use lazy wrapper instead of direct instantiation
agent_db = LazyAgentDB()