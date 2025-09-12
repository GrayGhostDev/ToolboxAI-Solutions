"""
Content Agent - Specializes in educational content generation

Creates curriculum-aligned educational content for Roblox environments.
"""

import logging
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
import json
import asyncio
import os
from contextlib import asynccontextmanager

from langchain_core.messages import HumanMessage, AIMessage
from langchain.tools import Tool

from .base_agent import BaseAgent, AgentConfig, AgentState, TaskResult

# Import SPARC framework components
try:
    from core.sparc import (
        create_state_manager, create_policy_engine, create_action_executor,
        create_reward_calculator, create_context_tracker,
        EnvironmentState, Action, ActionResult
    )
    SPARC_AVAILABLE = True
except ImportError as e:
    logger = logging.getLogger(__name__)
    logger.warning(f"SPARC framework not available: {e}")
    SPARC_AVAILABLE = False

# Import environment configuration
import sys
import os

# Add the project root to the path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

try:
    from config.environment import get_environment_config, should_use_real_data
except ImportError as e:
    # If still can't import, create a minimal fallback
    import logging
    logger = logging.getLogger(__name__)
    logger.warning(f"Could not import config.environment: {e}")
    
    class FallbackConfig:
        def __init__(self):
            self.use_mock_llm = os.getenv("USE_MOCK_LLM", "true").lower() == "true"
            self.use_mock_database = False
            self.use_mock_services = False
            self.bypass_rate_limit = True
            self.debug_mode = True
            self.log_level = "DEBUG"
            self.require_auth = False
            self.validate_ssl = False
            self.cache_enabled = True
    
    def get_environment_config():
        return FallbackConfig()
    
    def should_use_real_data():
        return not os.getenv("USE_MOCK_LLM", "true").lower() == "true"

# Import MCP context management
try:
    import websockets
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    websockets = None

logger = logging.getLogger(__name__)

try:
    from .database_integration import get_agent_database
    DATABASE_AVAILABLE = True
    logger.info("Database integration module loaded successfully")
except (ImportError, Exception) as e:
    logger.warning(f"Database integration not available: {e}")
    get_agent_database = None
    DATABASE_AVAILABLE = False

# Content Templates
LESSON_PLAN_TEMPLATE = """
# {title}

## Learning Objectives
{objectives}

## Grade Level: {grade_level}
## Subject: {subject}
## Duration: {duration}

## Pre-requisites
{prerequisites}

## Materials Needed
{materials}

## Introduction ({intro_time})
{introduction}

## Main Content ({main_time})
{main_content}

## Interactive Activities
{activities}

## Assessment
{assessment}

## Conclusion ({conclusion_time})
{conclusion}

## Extension Activities
{extensions}

## Standards Alignment
{standards}
"""

INTERACTIVE_SCENARIO_TEMPLATE = """
## Scenario: {title}

### Setting
{setting_description}

### Characters
{characters}

### Learning Goals
{learning_goals}

### Player Objectives
{player_objectives}

### Challenges
{challenges}

### Rewards
{rewards}

### Educational Checkpoints
{checkpoints}

### Dialogue Examples
{dialogue}

### Success Criteria
{success_criteria}
"""

VOCABULARY_MODULE_TEMPLATE = """
## Vocabulary Module: {topic}

### Core Terms
{core_terms}

### Definitions
{definitions}

### Context Sentences
{context_sentences}

### Visual Associations
{visual_associations}

### Interactive Exercises
{exercises}

### Memory Aids
{memory_aids}
"""


class ContentAgent(BaseAgent):
    """
    Agent specialized in generating educational content.

    Capabilities:
    - Curriculum alignment (Common Core, NGSS, etc.)
    - Age-appropriate content creation
    - Learning objective mapping
    - Educational narrative development
    - Interactive element design
    """

    def __init__(self, config: Optional[AgentConfig] = None):
        # Initialize environment configuration
        self.env_config = get_environment_config()
        self.use_real_data = should_use_real_data() and not self.env_config.use_mock_database
        
        # Initialize database integration
        self.database_available = DATABASE_AVAILABLE
        self.agent_db = get_agent_database() if DATABASE_AVAILABLE else None
        
        # Initialize SPARC framework components
        self.sparc_available = SPARC_AVAILABLE
        if SPARC_AVAILABLE:
            self._init_sparc_components()
        
        # Initialize MCP context management
        self.mcp_available = MCP_AVAILABLE
        get_svc = getattr(self.env_config, "get_service_url", None)
        self.mcp_url = get_svc("mcp") if callable(get_svc) else "ws://127.0.0.1:9876"
        
        if config is None:
            # Use appropriate model based on availability
            if not self.env_config.use_mock_llm and os.getenv("OPENAI_API_KEY"):
                # Try GPT-4 first, fallback to GPT-3.5-turbo if not available
                model = "gpt-4o" if os.getenv("USE_GPT4", "false").lower() == "true" else "gpt-3.5-turbo"
            else:
                model = "gpt-3.5-turbo"
            
            config = AgentConfig(
                name="ContentAgent",
                model=model,
                temperature=0.7,
                system_prompt=self._get_enhanced_content_prompt(),
                tools=self._initialize_tools(),
                max_retries=3,
                timeout=60
            )
        super().__init__(config)

        # Content templates
        self.templates = self._load_content_templates()
        
        # Initialize content quality metrics
        self.quality_metrics = {
            "generated_count": 0,
            "avg_quality_score": 0.0,
            "successful_generations": 0,
            "database_hits": 0,
            "openai_api_calls": 0
        }
        
        logger.info(f"ContentAgent initialized - Database: {self.database_available}, SPARC: {self.sparc_available}, Real Data: {self.use_real_data}")

        # Subject expertise areas
        self.subjects = [
            "Mathematics",
            "Science",
            "History",
            "Geography",
            "Language Arts",
            "Computer Science",
            "Art",
            "Music",
        ]

        # Grade level mappings
        self.grade_levels = {
            "K-2": {"age_range": "5-7", "complexity": "basic"},
            "3-5": {"age_range": "8-10", "complexity": "elementary"},
            "6-8": {"age_range": "11-13", "complexity": "intermediate"},
            "9-12": {"age_range": "14-18", "complexity": "advanced"},
        }

    def _get_enhanced_content_prompt(self) -> str:
        """Get enhanced specialized prompt for content generation"""
        return """You are an Advanced Educational Content Specialist and AI Agent for Roblox learning environments, integrated with real-time data systems and educational frameworks.

Your advanced capabilities include:
- Real-time curriculum alignment using live database standards (Common Core, NGSS, CSTA, state standards)
- Personalized content generation based on student progress analytics
- Multi-modal content creation (visual, auditory, kinesthetic learning styles)
- Adaptive difficulty scaling using machine learning insights
- Cross-platform educational content optimization
- Real-time assessment integration and feedback loops
- Cultural responsiveness and accessibility compliance
- Evidence-based pedagogical implementations

When creating content with real data integration:
1. Query existing curriculum standards and adapt content accordingly
2. Analyze student progress data to personalize difficulty and pacing
3. Use real educational outcomes to optimize content effectiveness
4. Integrate with existing educational content libraries when beneficial
5. Generate assessment items aligned with actual learning objectives
6. Create content that scales across multiple learning environments
7. Implement feedback mechanisms for continuous improvement
8. Ensure content meets current educational research best practices

Content Structure Requirements:
- Standards-aligned learning objectives (with specific standard codes)
- Evidence-based prerequisite analysis
- Scaffolded core content with multiple representations
- Interactive elements designed for Roblox implementation
- Formative and summative assessment opportunities
- Differentiation strategies for diverse learners
- Extension activities that promote deeper learning
- Real-world application connections
- Cultural relevance and inclusive design elements

Quality Metrics Integration:
- Track content effectiveness through student engagement data
- Monitor learning outcome improvements
- Analyze content usage patterns for optimization
- Provide detailed metadata for content management systems"""    

    def _initialize_tools(self) -> List[Tool]:
        """Initialize content generation tools"""
        tools = []

        # Research tools
        try:
            from langchain_community.tools import WikipediaQueryRun, DuckDuckGoSearchRun
            from langchain_community.utilities import WikipediaAPIWrapper, DuckDuckGoSearchAPIWrapper

            tools.append(
                Tool(
                    name="Wikipedia",
                    func=WikipediaQueryRun(api_wrapper=WikipediaAPIWrapper()).run,
                    description="Search Wikipedia for educational content and facts",
                )
            )

            tools.append(
                Tool(
                    name="WebSearch",
                    func=DuckDuckGoSearchRun(api_wrapper=DuckDuckGoSearchAPIWrapper()).run,
                    description="Search the web for current educational resources",
                )
            )
        except (ImportError, Exception) as e:
            logger.warning(f"Could not initialize search tools: {e}")

        # Custom educational tools
        # Create sync wrapper for async function
        def lookup_standards_sync(query: str) -> str:
            import asyncio
            try:
                loop = asyncio.get_event_loop()
                return loop.run_until_complete(self._lookup_standards(query))
            except RuntimeError:
                # If no loop is running, create a new one
                return asyncio.run(self._lookup_standards(query))
        
        tools.append(
            Tool(
                name="StandardsLookup",
                func=lookup_standards_sync,
                description="Look up educational standards by subject and grade",
            )
        )

        tools.append(
            Tool(
                name="VocabularyGenerator",
                func=self._generate_vocabulary,
                description="Generate grade-appropriate vocabulary lists",
            )
        )

        tools.append(
            Tool(
                name="LearningObjectiveBuilder",
                func=self._build_learning_objectives,
                description="Create SMART learning objectives",
            )
        )

        # Add database-specific tools if available
        if DATABASE_AVAILABLE and self.agent_db:
            tools.append(
                Tool(
                    name="DatabaseContentLookup",
                    func=self._lookup_database_content,
                    description="Look up existing educational content from database",
                )
            )
            
            tools.append(
                Tool(
                    name="StudentProgressAnalysis",
                    func=self._analyze_student_progress,
                    description="Analyze student progress data to customize content",
                )
            )

        # Add SPARC framework tools if available
        if SPARC_AVAILABLE:
            tools.extend([
                Tool(
                    name="SPARCStateAnalysis",
                    func=self._analyze_learning_state,
                    description="Analyze current learning state using SPARC framework",
                ),
                Tool(
                    name="SPARCPolicyDecision",
                    func=self._make_content_policy_decision,
                    description="Make content generation policy decisions using SPARC",
                ),
                Tool(
                    name="SPARCRewardCalculation",
                    func=self._calculate_content_rewards,
                    description="Calculate content quality and learning rewards",
                )
            ])
        
        # Add MCP context tools if available
        if MCP_AVAILABLE:
            tools.extend([
                Tool(
                    name="MCPContextUpdate",
                    func=self._update_mcp_context,
                    description="Update MCP context with content generation data",
                ),
                Tool(
                    name="MCPContextQuery",
                    func=self._query_mcp_context,
                    description="Query MCP for relevant educational context",
                )
            ])

        return tools

    def _load_content_templates(self) -> Dict[str, str]:
        """Load content generation templates"""
        return {
            "lesson_plan": LESSON_PLAN_TEMPLATE,
            "interactive_scenario": INTERACTIVE_SCENARIO_TEMPLATE,
            "vocabulary_module": VOCABULARY_MODULE_TEMPLATE,
        }

    def _init_sparc_components(self):
        """Initialize SPARC framework components"""
        try:
            self.state_manager = create_state_manager(
                history_size=100,
                compression_threshold=50
            )
            self.policy_engine = create_policy_engine(
                learning_rate=0.01,
                exploration_rate=0.1
            )
            self.action_executor = create_action_executor(
                max_parallel=3,
                timeout=30.0
            )
            self.reward_calculator = create_reward_calculator(
                dimensions=["learning_effectiveness", "engagement", "curriculum_alignment", "accessibility"]
            )
            self.context_tracker = create_context_tracker(
                window_size=20,
                session_timeout=1800.0
            )
            logger.info("SPARC framework components initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize SPARC components: {e}")
            self.sparc_available = False
    
    async def _process_task(self, state: AgentState) -> Any:
        """Process content generation task"""
        task = state["task"]
        context = state["context"]

        # Extract parameters
        subject = context.get("subject", "General")
        grade_level = context.get("grade_level", "6-8")
        topic = context.get("topic", task)
        learning_objectives = context.get("learning_objectives", [])

        # Generate content based on requirements
        content = await self._generate_educational_content(
            subject=subject,
            grade_level=grade_level,
            topic=topic,
            objectives=learning_objectives,
        )

        # Create interactive elements
        interactive_elements = await self._create_interactive_elements(
            content=content, grade_level=grade_level
        )

        # Generate assessment materials
        assessments = await self._generate_assessments(
            content=content, objectives=learning_objectives
        )

        # Execute SPARC framework cycle if available
        sparc_result = None
        if self.sparc_available:
            try:
                sparc_result = await self._execute_sparc_cycle({
                    "task": task,
                    "context": context,
                    "content": content,
                    "interactive_elements": interactive_elements,
                    "assessments": assessments
                })
            except Exception as e:
                logger.warning(f"SPARC cycle execution failed: {e}")
        
        # Update MCP context if available
        mcp_context_updated = False
        if self.mcp_available:
            try:
                await self._update_mcp_context({
                    "agent": "ContentAgent",
                    "task": task,
                    "content_generated": True,
                    "quality_metrics": self._calculate_content_quality_score(content),
                    "timestamp": datetime.now().isoformat()
                })
                mcp_context_updated = True
            except Exception as e:
                logger.warning(f"MCP context update failed: {e}")
        
        # Package comprehensive result
        result = {
            "content": content,
            "interactive_elements": interactive_elements,
            "assessments": assessments,
            "metadata": {
                "subject": subject,
                "grade_level": grade_level,
                "topic": topic,
                "generated_at": datetime.now().isoformat(),
                "database_enhanced": self.database_available,
                "sparc_integrated": sparc_result is not None,
                "mcp_context_updated": mcp_context_updated,
                "real_data_used": self.use_real_data,
                "model_used": self.config.model,
                "generation_source": "ai_with_real_data" if self.use_real_data else "ai_mock_data"
            },
            "quality_metrics": self.quality_metrics,
            "sparc_analysis": sparc_result,
        }
        
        # Update context with database data if available
        if self.database_available:
            try:
                enriched_context = await self.update_context_with_database_data(context)
                result["enriched_context"] = enriched_context
            except Exception as e:
                logger.warning(f"Failed to enrich context with database data: {e}")
        
        # Update quality metrics
        self.quality_metrics["generated_count"] += 1
        self.quality_metrics["successful_generations"] += 1
        if self.database_available:
            self.quality_metrics["database_hits"] += 1
        if not self.env_config.use_mock_llm:
            self.quality_metrics["openai_api_calls"] += 1

        return result

    async def _generate_educational_content(
        self, subject: str, grade_level: str, topic: str, objectives: List[str]
    ) -> Dict[str, Any]:
        """Generate main educational content"""
        
        existing_content = None
        if DATABASE_AVAILABLE and self.agent_db:
            try:
                # Try to get existing content from database
                content_items = await self.agent_db.get_educational_content() if self.agent_db else []
                
                # Look for content matching our topic/subject
                for item in content_items:
                    item_title = item.get('title', '').lower()
                    item_desc = item.get('description', '').lower()
                    item_subject = item.get('subject', '').lower()
                    if (topic.lower() in item_title or topic.lower() in item_desc or subject.lower() in item_subject):
                        if item.get('content_data'):
                            # Found existing content
                            try:
                                if isinstance(item['content_data'], str):
                                    existing_content = json.loads(item['content_data'])
                                else:
                                    existing_content = item['content_data']
                                logger.info(f"Using existing content from database: {item['title']}")
                                break
                            except json.JSONDecodeError:
                                logger.warning(f"Failed to parse content data for item {item['id']}")
                                
            except Exception as e:
                logger.warning(f"Failed to retrieve existing content from database: {e}")

        # Look up relevant standards
        standards = await self._lookup_standards(f"{subject} {grade_level}")

        # Create content prompt
        objectives_text = (
            "\n".join(f"- {obj}" for obj in objectives)
            if objectives
            else "- General understanding of the topic"
        )

        # If we have existing content, enhance it; otherwise generate new
        if existing_content:
            prompt = f"""Enhance and adapt this existing educational content for a Roblox learning environment:

Existing Content: {json.dumps(existing_content, indent=2)[:1000]}...

Subject: {subject}
Grade Level: {grade_level}
Topic: {topic}
Learning Objectives:
{objectives_text}

Standards to align with:
{standards}

Enhance the content to include:
1. Age-appropriate explanations for grade {grade_level}
2. Roblox-specific interactive elements
3. Clear learning progression
4. Engaging game narrative

Format the content for implementation in a Roblox game environment."""
        else:
            prompt = f"""Create educational content for a Roblox learning environment:

Subject: {subject}
Grade Level: {grade_level}
Topic: {topic}
Learning Objectives:
{objectives_text}

Standards to align with:
{standards}

Generate:
1. Core content explanation (age-appropriate)
2. Key concepts and vocabulary
3. Real-world connections
4. Common misconceptions to address
5. Engaging narrative framework
6. Interactive learning opportunities

Format the content for implementation in a Roblox game environment."""

        response = await self.llm.ainvoke(prompt)

        # Parse and structure response
        content = {
            "topic": topic,
            "explanation": response.content,
            "vocabulary": self._generate_vocabulary(f"{topic} {grade_level}"),
            "standards_alignment": standards,
            "learning_path": self._create_learning_path(topic, grade_level),
            "source": "database_enhanced" if existing_content else "ai_generated",
            "existing_content_used": existing_content is not None
        }
        
        # Save generated content to database if available
        if DATABASE_AVAILABLE and self.agent_db and not existing_content:
            try:
                # Enhanced content data with quality metrics
                content_data = {
                    "title": f"{subject} - {topic} (Grade {grade_level})",
                    "explanation": response.content,
                    "vocabulary": content["vocabulary"],
                    "standards_alignment": standards,
                    "subject": subject,
                    "grade_level": grade_level,
                    "topic": topic,
                    "generation_metadata": {
                        "model_used": self.config.model,
                        "real_data_enhanced": self.use_real_data,
                        "sparc_processed": self.sparc_available,
                        "quality_score": self._calculate_content_quality_score(content),
                        "generation_time": datetime.now().isoformat(),
                        "agent_version": "ContentAgent_v2.0_RealDataIntegrated"
                    }
                }
                
                # Add retry logic for database saves
                saved = await self._save_with_retry("lesson_content", content_data)
                if saved:
                    logger.info("Successfully saved enhanced content to database")
                else:
                    logger.warning("Failed to save content after retries")
            except Exception as e:
                logger.warning(f"Failed to save generated content: {e}")

        return content

    async def _create_interactive_elements(
        self, content: Dict[str, Any], grade_level: str
    ) -> List[Dict[str, Any]]:
        """Create interactive elements for the content"""

        prompt = f"""Design interactive elements for this educational content in Roblox:

Content: {content['explanation'][:500]}...
Grade Level: {grade_level}

Create 3-5 interactive elements that:
1. Reinforce key concepts
2. Provide hands-on learning
3. Are age-appropriate and engaging
4. Can be implemented in Roblox

For each element provide:
- Name and description
- Learning goal
- Interaction mechanics
- Success criteria
- Roblox implementation notes"""

        response = await self.llm.ainvoke(prompt)

        # Parse response into structured elements
        elements: List[Dict[str, Any]] = []

        # Simple parsing - in production, use more sophisticated parsing
        element_texts = str(response.content).split("\n\n")
        for text in element_texts[:5]:  # Limit to 5 elements
            if text.strip():
                elements.append(
                    {
                        "description": text,
                        "type": "interactive",
                        "grade_appropriate": True,
                    }
                )

        return elements

    async def _generate_assessments(
        self, content: Dict[str, Any], objectives: List[str]
    ) -> Dict[str, Any]:
        """Generate assessment materials"""
        
        if DATABASE_AVAILABLE and self.agent_db:
            try:
                # Try to get existing quiz questions from database
                topic = content.get('topic', '')
                subject = content.get('subject')
                
                quiz_items = await self.agent_db.get_quiz_questions(subject=subject) if self.agent_db else []
                
                if quiz_items:
                    # Use existing quiz data and format for response
                    for quiz in quiz_items:
                        if quiz.get('questions'):
                            # Found existing questions, format them
                            assessments = {
                                "questions": quiz['questions'],
                                "type": "database_quiz",
                                "objectives_assessed": objectives,
                                "difficulty": quiz.get('difficulty', 'medium'),
                                "source": "database",
                                "quiz_id": quiz.get('id')
                            }
                            return assessments
                    
            except Exception as e:
                logger.warning(f"Failed to retrieve quiz questions from database: {e}")

        # Generate new assessment using AI (fallback or when no database data)
        prompt = f"""Create assessment materials for this educational content:

Topic: {content['topic']}
Learning Objectives: {objectives}

Generate:
1. 5 multiple-choice questions
2. 2 short-answer questions
3. 1 practical application task
4. Rubric for evaluation
5. Success criteria

Format for Roblox quiz implementation."""

        response = await self.llm.ainvoke(prompt)

        assessments = {
            "questions": response.content,
            "type": "generated",
            "objectives_assessed": objectives,
            "difficulty": self._determine_difficulty(content["topic"]),
            "source": "ai_generated"
        }
        
        # Save generated assessment to database if available
        if DATABASE_AVAILABLE and self.agent_db:
            try:
                content_data = {
                    "title": f"Assessment for {content.get('topic', 'Unknown Topic')}",
                    "questions": response.content,
                    "objectives": objectives,
                    "difficulty": assessments["difficulty"]
                }
                await self.agent_db.save_generated_content("quiz", content_data) if self.agent_db else None
                logger.info("Saved generated assessment to database")
            except Exception as e:
                logger.warning(f"Failed to save generated assessment: {e}")

        return assessments

    async def _lookup_standards(self, query: str) -> str:
        """Look up educational standards"""
        if DATABASE_AVAILABLE and self.agent_db:
            try:
                # Parse subject and grade level from query
                subject = None
                grade_level = None
                
                query_lower = query.lower()
                subjects = ["mathematics", "science", "language arts", "history", "computer science"]
                for subj in subjects:
                    if subj in query_lower:
                        subject = subj.title()
                        break
                        
                # Extract grade level if present
                import re
                grade_match = re.search(r'(\d+)', query)
                if grade_match:
                    grade_level = int(grade_match.group(1))
                    
                # Get real standards from database
                if self.agent_db:
                    standards = await self.agent_db.get_curriculum_standards(subject, grade_level)
                else:
                    standards = []
                
                if standards:
                    standards_text = []
                    for std in standards[:5]:  # Limit to 5 standards
                        if 'standard_code' in std:
                            standards_text.append(f"{std['standard_code']}: {std['description']}")
                        elif 'standards' in std:
                            standards_text.append(f"{std['standards']} - {std['description'][:100]}...")
                    
                    if standards_text:
                        return "\n".join(standards_text)
                        
            except Exception as e:
                logger.warning(f"Failed to retrieve standards from database: {e}")

        # Fallback to mock data if database unavailable
        standards_map = {
            "Mathematics": "CCSS.MATH.CONTENT",
            "Science": "NGSS",
            "Language Arts": "CCSS.ELA-LITERACY",
            "History": "NCSS",
            "Computer Science": "CSTA",
        }

        for subject, standard in standards_map.items():
            if subject.lower() in query.lower():
                return f"{standard} - Relevant standards for {query}"

        return "General educational standards"

    def _generate_vocabulary(self, query: str) -> List[Dict[str, str]]:
        """Generate vocabulary list"""
        if DATABASE_AVAILABLE and self.agent_db:
            try:
                # Parse subject from query
                subject = None
                query_lower = query.lower()
                subjects = ["mathematics", "science", "language arts", "history", "computer science"]
                for subj in subjects:
                    if subj in query_lower:
                        subject = subj.title()
                        break
                        
                # Get learning objectives to extract vocabulary
                # Note: This is a synchronous method, so we'll use mock data for now
                objectives = []
                if self.agent_db:
                    # TODO: Need to refactor to make this async or use sync database methods
                    logger.info("Database vocabulary retrieval not yet implemented in sync context")
                    objectives = []
                
                vocab = []
                for obj in objectives[:3]:  # Limit to 3 objectives
                    title = obj.get('title', '')
                    description = obj.get('description', '')
                    
                    # Extract key terms from title and description
                    if title:
                        vocab.append({
                            "term": title,
                            "definition": description[:200] if description else f"Key concept related to {title}"
                        })
                    
                    # Add subject-specific vocabulary
                    if subject == "Science":
                        vocab.extend([
                            {"term": "hypothesis", "definition": "A testable explanation for a scientific observation"},
                            {"term": "variable", "definition": "A factor that can change in an experiment"},
                            {"term": "control", "definition": "The standard condition in an experiment"}
                        ])
                    elif subject == "Mathematics":
                        vocab.extend([
                            {"term": "equation", "definition": "A mathematical statement showing two expressions are equal"},
                            {"term": "variable", "definition": "A symbol representing an unknown value"},
                            {"term": "coefficient", "definition": "A number multiplied by a variable"}
                        ])
                    
                if vocab:
                    # Remove duplicates by term
                    seen_terms = set()
                    unique_vocab = []
                    for item in vocab:
                        if item['term'] not in seen_terms:
                            unique_vocab.append(item)
                            seen_terms.add(item['term'])
                    return unique_vocab[:10]  # Limit to 10 terms
                        
            except Exception as e:
                logger.warning(f"Failed to retrieve vocabulary from database: {e}")

        # Fallback to mock data if database unavailable
        vocab = [
            {"term": "concept", "definition": "A general idea or understanding"},
            {
                "term": "hypothesis",
                "definition": "A proposed explanation for a phenomenon",
            },
            {
                "term": "variable",
                "definition": "A factor that can change in an experiment",
            },
        ]

        return vocab

    def _build_learning_objectives(self, topic: str) -> List[str]:
        """Build SMART learning objectives"""
        if DATABASE_AVAILABLE and self.agent_db:
            try:
                # Get real learning objectives from database
                # Note: This is a synchronous method, so we'll use mock data for now
                # TODO: Need to refactor to make this async or use sync database methods
                logger.info("Database objectives retrieval not yet implemented in sync context")
                db_objectives = []
                
                # Filter by title/topic if available
                relevant_objectives = []
                for obj in db_objectives:
                    obj_title = obj.get('title', '').lower()
                    obj_desc = obj.get('description', '').lower()
                    if (topic.lower() in obj_title or topic.lower() in obj_desc):
                        relevant_objectives.append(obj['description'])
                        
                if relevant_objectives:
                    return relevant_objectives[:4]  # Return up to 4 objectives
                    
                # If no topic-specific objectives, use general ones from database
                if db_objectives:
                    return [obj['description'] for obj in db_objectives[:4]]
                    
            except Exception as e:
                logger.warning(f"Failed to retrieve learning objectives from database: {e}")

        # Fallback to generated objectives if database unavailable
        objectives = [
            f"Students will be able to identify key concepts related to {topic}",
            f"Students will demonstrate understanding of {topic} through practical application",
            f"Students will analyze and evaluate different aspects of {topic}",
            f"Students will create original solutions using knowledge of {topic}",
        ]

        return objectives

    def _create_learning_path(
        self, topic: str, grade_level: str
    ) -> List[Dict[str, Any]]:
        """Create a structured learning path"""

        complexity = self.grade_levels.get(grade_level, {}).get(
            "complexity", "intermediate"
        )

        path = [
            {
                "stage": "Introduction",
                "duration": "5 minutes",
                "activities": ["Watch intro video", "Explore environment"],
                "complexity": complexity,
            },
            {
                "stage": "Exploration",
                "duration": "10 minutes",
                "activities": ["Guided discovery", "Interactive examples"],
                "complexity": complexity,
            },
            {
                "stage": "Practice",
                "duration": "15 minutes",
                "activities": ["Hands-on exercises", "Collaborative tasks"],
                "complexity": complexity,
            },
            {
                "stage": "Assessment",
                "duration": "10 minutes",
                "activities": ["Quiz", "Practical challenge"],
                "complexity": complexity,
            },
            {
                "stage": "Extension",
                "duration": "Optional",
                "activities": ["Advanced challenges", "Creative projects"],
                "complexity": "advanced",
            },
        ]

        return path

    def _determine_difficulty(self, topic: str) -> str:
        """Determine content difficulty level"""
        # Simple heuristic - enhance with actual analysis

        advanced_topics = ["calculus", "physics", "chemistry", "programming"]
        basic_topics = ["counting", "colors", "shapes", "letters"]

        topic_lower = topic.lower()

        if any(t in topic_lower for t in advanced_topics):
            return "advanced"
        elif any(t in topic_lower for t in basic_topics):
            return "basic"
        else:
            return "intermediate"

    async def generate_lesson_plan(
        self, subject: str, topic: str, grade_level: str, duration: int = 45
    ) -> Dict[str, Any]:
        """Generate a complete lesson plan"""

        template = self.templates["lesson_plan"]

        # Generate components
        objectives = self._build_learning_objectives(topic)
        content = await self._generate_educational_content(
            subject, grade_level, topic, objectives
        )

        lesson_plan = {
            "title": f"{topic} - {subject} Lesson",
            "objectives": objectives,
            "grade_level": grade_level,
            "subject": subject,
            "duration": f"{duration} minutes",
            "content": content,
            "template": template,
        }

        return lesson_plan

    async def adapt_content_for_roblox(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """Adapt educational content specifically for Roblox implementation"""

        prompt = f"""Adapt this educational content for a Roblox game:

Content: {json.dumps(content, indent=2)[:1000]}...

Create:
1. Game narrative that incorporates the content
2. NPC dialogue for teaching concepts
3. Environmental design suggestions
4. Interactive object descriptions
5. Player progression system
6. Reward structure

Make it engaging and appropriate for Roblox platform."""

        response = await self.llm.ainvoke(prompt)

        adapted_content = {
            "original": content,
            "roblox_adaptation": response.content,
            "implementation_ready": True,
            "platform": "Roblox",
        }

        return adapted_content
        
    async def _lookup_database_content(self, query: str) -> str:
        """Look up existing content from database"""
        if not self.database_available:
            return "Database not available"
            
        try:
            content_items = await self.agent_db.get_educational_content() if self.agent_db else []
            
            # Search for relevant content
            relevant_items = []
            query_lower = query.lower()
            
            for item in content_items:
                if (query_lower in item.get('title', '').lower() or 
                    query_lower in item.get('topic', '').lower() or
                    query_lower in item.get('subject', '').lower()):
                    relevant_items.append({
                        'title': item.get('title', 'Untitled'),
                        'subject': item.get('subject', 'Unknown'),
                        'topic': item.get('topic', 'Unknown'),
                        'grade_level': item.get('grade_level', 'Unknown')
                    })
                    
            if relevant_items:
                return f"Found {len(relevant_items)} relevant content items: " + \
                       "; ".join([f"{item['title']} ({item['subject']})" for item in relevant_items])
            else:
                return "No relevant content found in database"
                
        except Exception as e:
            logger.error(f"Error looking up database content: {e}")
            return f"Error accessing database: {str(e)}"
            
    async def _analyze_student_progress(self, student_data: str) -> str:
        """Analyze student progress for content customization"""
        if not self.database_available:
            return "Database not available for progress analysis"
            
        try:
            # Parse student ID if provided
            import re
            student_match = re.search(r'student[_\s]?id[:\s]*(\d+)', student_data.lower())
            
            if student_match:
                student_id = int(student_match.group(1))
                progress_data = await self.agent_db.get_student_progress(student_id) if self.agent_db else {}
                
                if progress_data:
                    progress_summary = f"Student {progress_data.get('username', 'Unknown')}: "
                    progress_items = progress_data.get('progress', [])
                    
                    if progress_items:
                        completed = len([p for p in progress_items if p.get('status') == 'completed'])
                        in_progress = len([p for p in progress_items if p.get('status') == 'in_progress'])
                        avg_score = sum([p.get('score', 0) for p in progress_items if p.get('score')]) / len(progress_items)
                        
                        progress_summary += f"{completed} completed, {in_progress} in progress, avg score: {avg_score:.1f}"
                    else:
                        progress_summary += "No progress data available"
                        
                    return progress_summary
                else:
                    return f"No progress data found for student ID {student_id}"
            else:
                return "Please provide a valid student ID for progress analysis"
                
        except Exception as e:
            logger.error(f"Error analyzing student progress: {e}")
            return f"Error analyzing progress: {str(e)}"
            
    async def get_database_status(self) -> Dict[str, Any]:
        """Get current database integration status"""
        status = {
            "database_available": self.database_available,
            "agent_db_connected": self.agent_db is not None,
            "last_check": datetime.now().isoformat()
        }
        
        if self.database_available and self.agent_db:
            try:
                # Test database connectivity
                objectives = await self.agent_db.get_learning_objectives() if self.agent_db else []
                content_items = await self.agent_db.get_educational_content() if self.agent_db else []
                
                status["objectives_count"] = len(objectives)
                status["content_items_count"] = len(content_items)
                status["database_responsive"] = True
                
            except Exception as e:
                status["database_responsive"] = False
                status["error"] = str(e)
                
        return status
        
    async def _execute_sparc_cycle(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute SPARC framework cycle for content generation optimization"""
        if not self.sparc_available:
            return None
        
        try:
            # Create observation from task data
            observation = {
                "task_type": "content_generation",
                "subject": task_data.get("context", {}).get("subject", "unknown"),
                "grade_level": task_data.get("context", {}).get("grade_level", "unknown"),
                "content_quality": self._calculate_content_quality_score(task_data.get("content", {})),
                "database_enhanced": self.database_available,
                "timestamp": datetime.now().isoformat()
            }
            
            # Update state
            current_state = await self.state_manager.update_state(observation)
            
            # Get policy decision
            policy_input = {
                "state": current_state,
                "context": task_data.get("context", {}),
                "task": task_data.get("task", "")
            }
            policy_decision = await self.policy_engine.decide(policy_input)
            
            # Execute action if needed
            action = Action(
                type="content_quality_enhancement",
                parameters={
                    "enhancement_type": policy_decision.action_type,
                    "quality_threshold": 0.8
                },
                priority=1
            )
            action_result = await self.action_executor.execute(action)
            
            # Calculate rewards
            reward_input = {
                "state": current_state,
                "action": action,
                "result": action_result,
                "quality_metrics": self.quality_metrics
            }
            rewards = await self.reward_calculator.calculate_rewards(reward_input)
            
            # Update context tracker
            await self.context_tracker.update_context({
                "content_generated": True,
                "quality_score": observation["content_quality"],
                "rewards": rewards.total_reward
            })
            
            return {
                "sparc_cycle_completed": True,
                "state_summary": current_state.summary if hasattr(current_state, 'summary') else "state_updated",
                "policy_decision": policy_decision.action_type if hasattr(policy_decision, 'action_type') else "enhance_quality",
                "action_success": action_result.success if hasattr(action_result, 'success') else True,
                "total_reward": rewards.total_reward if hasattr(rewards, 'total_reward') else 0.0,
                "context_updated": True
            }
            
        except Exception as e:
            logger.error(f"SPARC cycle execution failed: {e}")
            return {
                "sparc_cycle_completed": False,
                "error": str(e)
            }
    
    async def _update_mcp_context(self, context_data: Dict[str, Any]) -> bool:
        """Update MCP context with content generation data"""
        if not self.mcp_available:
            return False
        
        try:
            assert websockets is not None
            async with websockets.connect(self.mcp_url) as websocket:
                message = {
                    "type": "context_update",
                    "source": "content_agent",
                    "data": context_data,
                    "timestamp": datetime.now().isoformat(),
                    "priority": 3
                }
                await websocket.send(json.dumps(message))
                response = await websocket.recv()
                
                response_data = json.loads(response)
                success = response_data.get("status") == "success"
                
                if success:
                    logger.info("Successfully updated MCP context")
                else:
                    logger.warning(f"MCP context update failed: {response_data.get('message')}")
                
                return success
                
        except Exception as e:
            logger.error(f"MCP context update failed: {e}")
            return False
    
    async def _query_mcp_context(self, query: str) -> Dict[str, Any]:
        """Query MCP for relevant educational context"""
        if not self.mcp_available:
            return {}
        
        try:
            assert websockets is not None
            async with websockets.connect(self.mcp_url) as websocket:
                message = {
                    "type": "context_query",
                    "query": query,
                    "source": "content_agent",
                    "timestamp": datetime.now().isoformat()
                }
                await websocket.send(json.dumps(message))
                response = await websocket.recv()
                
                response_data = json.loads(response)
                if response_data.get("status") == "success":
                    return response_data.get("data", {})
                else:
                    logger.warning(f"MCP context query failed: {response_data.get('message')}")
                    return {}
                    
        except Exception as e:
            logger.error(f"MCP context query failed: {e}")
            return {}
    
    def _calculate_content_quality_score(self, content: Dict[str, Any]) -> float:
        """Calculate content quality score based on multiple factors"""
        try:
            score = 0.0
            max_score = 100.0
            
            # Check for required components
            if content.get("explanation"):
                score += 25.0  # Core explanation exists
                
            if content.get("vocabulary") and len(content.get("vocabulary", [])) > 0:
                score += 20.0  # Vocabulary provided
                
            if content.get("standards_alignment"):
                score += 20.0  # Standards aligned
                
            if content.get("learning_path") and len(content.get("learning_path", [])) > 0:
                score += 15.0  # Learning path structured
                
            # Bonus points for enhanced features
            if content.get("source") == "database_enhanced":
                score += 10.0  # Real data enhancement
                
            if self.use_real_data:
                score += 5.0  # Real data integration
                
            if self.sparc_available:
                score += 5.0  # SPARC framework integration
                
            return min(score / max_score, 1.0)  # Normalize to 0-1 range
            
        except Exception as e:
            logger.warning(f"Failed to calculate content quality score: {e}")
            return 0.5  # Default average score
    
    async def _save_with_retry(self, content_type: str, content_data: Dict[str, Any], max_retries: int = 3) -> bool:
        """Save content to database with retry logic"""
        if not DATABASE_AVAILABLE or self.agent_db is None:
            logger.info("Database not available; skipping save")
            return False
        
        db = self.agent_db
        for attempt in range(max_retries):
            try:
                success = await db.save_generated_content(content_type, content_data)
                if success:
                    return True
                logger.warning(f"Save attempt {attempt + 1} failed, retrying...")
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
            except Exception as e:
                logger.warning(f"Save attempt {attempt + 1} error: {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
        
        return False
    
    async def _analyze_learning_state(self, context: str) -> str:
        """Analyze current learning state using SPARC framework"""
        if not self.sparc_available:
            return "SPARC framework not available for state analysis"
        
        try:
            # Parse context for learning indicators
            learning_indicators = {
                "engagement_level": "medium",  # Would be calculated from real data
                "comprehension_rate": 0.7,
                "learning_velocity": "normal",
                "subject_mastery": "developing"
            }
            
            # Create state observation
            observation = {
                "type": "learning_state_analysis",
                "indicators": learning_indicators,
                "context": context,
                "timestamp": datetime.now().isoformat()
            }
            
            # Update state manager
            current_state = await self.state_manager.update_state(observation)
            
            # Return analysis summary
            return f"Learning state analysis completed. Current state: {current_state.summary if hasattr(current_state, 'summary') else 'active'}. Recommendations: {'adapt_difficulty' if learning_indicators['comprehension_rate'] < 0.6 else 'maintain_pace'}."
            
        except Exception as e:
            logger.error(f"Learning state analysis failed: {e}")
            return f"Learning state analysis failed: {str(e)}"
    
    async def _make_content_policy_decision(self, situation: str) -> str:
        """Make content generation policy decisions using SPARC"""
        if not self.sparc_available:
            return "SPARC framework not available for policy decisions"
        
        try:
            # Create policy input
            policy_input = {
                "situation": situation,
                "current_metrics": self.quality_metrics,
                "database_available": self.database_available,
                "real_data_enabled": self.use_real_data
            }
            
            # Get policy decision
            decision = await self.policy_engine.decide(policy_input)
            
            return f"Policy decision: {decision.action_type if hasattr(decision, 'action_type') else 'generate_enhanced_content'}. Confidence: {decision.confidence if hasattr(decision, 'confidence') else 0.8}. Rationale: {'Use real data for enhanced quality' if self.use_real_data else 'Generate with available resources'}."
            
        except Exception as e:
            logger.error(f"Policy decision failed: {e}")
            return f"Policy decision failed: {str(e)}"
    
    async def _calculate_content_rewards(self, content_data: str) -> str:
        """Calculate content quality and learning rewards"""
        if not self.sparc_available:
            return "SPARC framework not available for reward calculation"
        
        try:
            # Parse content data
            try:
                content_dict = json.loads(content_data) if isinstance(content_data, str) else {}
            except json.JSONDecodeError:
                content_dict = {"raw_content": content_data}
            
            # Calculate reward dimensions
            reward_input = {
                "content_quality": self._calculate_content_quality_score(content_dict),
                "database_enhancement": 1.0 if self.database_available else 0.5,
                "real_data_usage": 1.0 if self.use_real_data else 0.3,
                "sparc_integration": 1.0 if self.sparc_available else 0.0
            }
            
            # Calculate rewards
            rewards = await self.reward_calculator.calculate_rewards(reward_input)
            
            return f"Reward calculation completed. Total reward: {rewards.total_reward if hasattr(rewards, 'total_reward') else 'unknown'}. Quality score: {reward_input['content_quality']:.2f}. Enhancement bonus: {'applied' if self.database_available else 'not_applied'}."
            
        except Exception as e:
            logger.error(f"Reward calculation failed: {e}")
            return f"Reward calculation failed: {str(e)}"
    
    async def update_context_with_database_data(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Update agent context with real database data"""
        if not self.database_available or not self.agent_db:
            logger.warning("Database not available for context update")
            return context
            
        try:
            # Extract subject and grade level from context
            subject = context.get('subject')
            grade_level = context.get('grade_level')
            
            # Convert grade level to integer if it's a string
            if grade_level and isinstance(grade_level, str):
                # Extract number from grade level (e.g., "7" from "6-8" or "Grade 7")
                import re
                grade_match = re.search(r'(\d+)', str(grade_level))
                if grade_match:
                    grade_level = int(grade_match.group(1))
                else:
                    grade_level = None
                    
            # Enrich context with database data
            enriched_context = context.copy()
            
            # Add real learning objectives
            objectives = await self.agent_db.get_learning_objectives(subject, grade_level) if self.agent_db else []
            if objectives:
                enriched_context['database_objectives'] = objectives
                enriched_context['objectives_count'] = len(objectives)
                
            # Add existing content
            content_items = await self.agent_db.get_educational_content(subject=subject, grade_level=grade_level) if self.agent_db else []
            if content_items:
                enriched_context['database_content'] = content_items
                enriched_context['content_count'] = len(content_items)
                
            # Add curriculum standards
            standards = await self.agent_db.get_curriculum_standards(subject, grade_level) if self.agent_db else []
            if standards:
                enriched_context['curriculum_standards'] = standards
                enriched_context['standards_count'] = len(standards)
                
            # Update MCP context if available
            if self.mcp_available:
                await self._update_mcp_context({
                    'agent': 'ContentAgent',
                    'context_update': enriched_context,
                    'timestamp': datetime.now().isoformat(),
                    'data_source': 'database'
                })
            
            logger.info("Successfully enriched context with database data")
            return enriched_context
            
        except Exception as e:
            logger.error(f"Error updating context with database data: {e}")
            return context
