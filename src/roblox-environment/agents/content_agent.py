"""
Content Agent - Specializes in educational content generation

Creates curriculum-aligned educational content for Roblox environments.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import json

from langchain_core.messages import HumanMessage, AIMessage
from langchain.tools import Tool

from .base_agent import BaseAgent, AgentConfig, AgentState, TaskResult

logger = logging.getLogger(__name__)

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
        if config is None:
            config = AgentConfig(
                name="ContentAgent",
                model="gpt-4",
                temperature=0.7,
                system_prompt=self._get_content_prompt(),
                tools=self._initialize_tools(),
            )
        super().__init__(config)

        # Content templates
        self.templates = self._load_content_templates()

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

    def _get_content_prompt(self) -> str:
        """Get specialized prompt for content generation"""
        return """You are an Educational Content Specialist for Roblox learning environments.

Your expertise includes:
- Curriculum development and alignment (Common Core, NGSS, state standards)
- Age-appropriate content creation
- Interactive learning design
- Gamification of educational concepts
- Accessibility and inclusive design

When creating content:
1. Align with specific learning standards
2. Use age-appropriate language and concepts
3. Include clear learning objectives
4. Design for engagement and retention
5. Incorporate interactive elements
6. Provide assessment opportunities
7. Ensure cultural sensitivity and inclusion

Always structure content with:
- Learning objectives
- Pre-requisites
- Core content
- Interactive activities
- Assessment criteria
- Extension opportunities"""

    def _initialize_tools(self) -> List[Tool]:
        """Initialize content generation tools"""
        tools = []

        # Research tools
        try:
            from langchain_community.tools import WikipediaQueryRun, DuckDuckGoSearchRun

            tools.append(
                Tool(
                    name="Wikipedia",
                    func=WikipediaQueryRun().run,
                    description="Search Wikipedia for educational content and facts",
                )
            )

            tools.append(
                Tool(
                    name="WebSearch",
                    func=DuckDuckGoSearchRun().run,
                    description="Search the web for current educational resources",
                )
            )
        except ImportError as e:
            logger.warning(f"Could not initialize search tools: {e}")

        # Custom educational tools
        tools.append(
            Tool(
                name="StandardsLookup",
                func=self._lookup_standards,
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

        return tools

    def _load_content_templates(self) -> Dict[str, str]:
        """Load content generation templates"""
        return {
            "lesson_plan": LESSON_PLAN_TEMPLATE,
            "interactive_scenario": INTERACTIVE_SCENARIO_TEMPLATE,
            "vocabulary_module": VOCABULARY_MODULE_TEMPLATE,
        }

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

        # Package result
        result = {
            "content": content,
            "interactive_elements": interactive_elements,
            "assessments": assessments,
            "metadata": {
                "subject": subject,
                "grade_level": grade_level,
                "topic": topic,
                "generated_at": datetime.now().isoformat(),
            },
        }

        return result

    async def _generate_educational_content(
        self, subject: str, grade_level: str, topic: str, objectives: List[str]
    ) -> Dict[str, Any]:
        """Generate main educational content"""

        # Look up relevant standards
        standards = self._lookup_standards(f"{subject} {grade_level}")

        # Create content prompt
        objectives_text = (
            "\n".join(f"- {obj}" for obj in objectives)
            if objectives
            else "- General understanding of the topic"
        )

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
        }

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
        elements = []

        # Simple parsing - in production, use more sophisticated parsing
        element_texts = response.content.split("\n\n")
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
            "type": "formative",
            "objectives_assessed": objectives,
            "difficulty": self._determine_difficulty(content["topic"]),
        }

        return assessments

    def _lookup_standards(self, query: str) -> str:
        """Look up educational standards"""
        # In production, connect to standards database
        # For now, return sample standards

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
        # Simple vocabulary generation - enhance with actual vocabulary database

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
