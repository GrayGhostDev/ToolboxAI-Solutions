"""
Agent-Specific LCEL Chains

Specialized chains for different agent types using LCEL patterns.
"""

import logging
from typing import Any, Optional

from pydantic import BaseModel, Field

from core.langchain_compat import (
    LANGCHAIN_AVAILABLE,
    ChatPromptTemplate,
    HumanMessage,
    PydanticOutputParser,
    RunnableLambda,
    RunnableParallel,
    RunnablePassthrough,
    SystemMessage,
    get_chat_model,
)

from .base_chains import ChainConfig

logger = logging.getLogger(__name__)


# Output schemas for structured generation
class ContentOutput(BaseModel):
    """Schema for educational content output"""

    title: str = Field(description="Content title")
    objectives: list[str] = Field(description="Learning objectives")
    content: str = Field(description="Main content body")
    activities: list[dict[str, Any]] = Field(description="Interactive activities")
    assessment: Optional[dict[str, Any]] = Field(description="Assessment criteria")


class QuizOutput(BaseModel):
    """Schema for quiz generation output"""

    title: str = Field(description="Quiz title")
    instructions: str = Field(description="Quiz instructions")
    questions: list[dict[str, Any]] = Field(description="Quiz questions")
    answers: list[dict[str, Any]] = Field(description="Answer key")
    scoring_rubric: dict[str, Any] = Field(description="Scoring guidelines")


class TerrainOutput(BaseModel):
    """Schema for terrain generation output"""

    name: str = Field(description="Terrain name")
    description: str = Field(description="Terrain description")
    dimensions: dict[str, int] = Field(description="Terrain dimensions")
    features: list[dict[str, Any]] = Field(description="Terrain features")
    lua_code: str = Field(description="Lua code for terrain generation")


class ScriptOutput(BaseModel):
    """Schema for script generation output"""

    script_name: str = Field(description="Script name")
    description: str = Field(description="Script purpose")
    dependencies: list[str] = Field(description="Required dependencies")
    code: str = Field(description="Lua script code")
    usage_instructions: str = Field(description="How to use the script")


class ReviewOutput(BaseModel):
    """Schema for code review output"""

    summary: str = Field(description="Review summary")
    issues: list[dict[str, Any]] = Field(description="Identified issues")
    suggestions: list[str] = Field(description="Improvement suggestions")
    security_concerns: list[str] = Field(description="Security issues")
    performance_notes: list[str] = Field(description="Performance considerations")
    overall_score: float = Field(description="Overall code quality score")


def create_content_generation_chain(
    subject: str, grade_level: str, config: Optional[ChainConfig] = None
):
    """
    Create a chain for educational content generation.

    Args:
        subject: Subject area
        grade_level: Target grade level
        config: Chain configuration

    Returns:
        LCEL chain for content generation
    """
    if not LANGCHAIN_AVAILABLE:
        raise ImportError("LangChain not available")

    config = config or ChainConfig(temperature=0.7)

    system_prompt = f"""You are an expert educational content creator specializing in {subject} for {grade_level}.

Your task is to generate comprehensive educational content that is:
- Age-appropriate and engaging
- Aligned with curriculum standards
- Interactive and gamified for Roblox environments
- Includes clear learning objectives
- Provides assessment opportunities

Generate structured content following the specified output format."""

    prompt = ChatPromptTemplate.from_messages(
        [
            SystemMessage(content=system_prompt),
            HumanMessage(content="Topic: {topic}\n\nAdditional Requirements: {requirements}"),
        ]
    )

    model = get_chat_model(model_name=config.model_name, temperature=config.temperature)

    # Use structured output parser
    parser = PydanticOutputParser(pydantic_object=ContentOutput)

    # Add format instructions to prompt
    format_prompt = RunnableLambda(
        lambda x: {**x, "format_instructions": parser.get_format_instructions()}
    )

    # Build chain
    chain = format_prompt | prompt | model | parser

    logger.debug(f"Created content generation chain for {subject} - {grade_level}")
    return chain


def create_quiz_generation_chain(
    subject: str,
    difficulty: str = "medium",
    question_count: int = 10,
    config: Optional[ChainConfig] = None,
):
    """
    Create a chain for quiz generation.

    Args:
        subject: Subject for the quiz
        difficulty: Difficulty level
        question_count: Number of questions
        config: Chain configuration

    Returns:
        LCEL chain for quiz generation
    """
    if not LANGCHAIN_AVAILABLE:
        raise ImportError("LangChain not available")

    config = config or ChainConfig(temperature=0.5)

    system_prompt = f"""You are an expert quiz creator for educational assessments.

Create a {difficulty} difficulty quiz on {subject} with {question_count} questions.

Requirements:
- Mix of question types (multiple choice, true/false, short answer)
- Clear, unambiguous questions
- Appropriate difficulty progression
- Include answer explanations
- Provide scoring rubric

Generate structured quiz data following the specified format."""

    prompt = ChatPromptTemplate.from_messages(
        [
            SystemMessage(content=system_prompt),
            HumanMessage(
                content="Learning Objectives: {objectives}\n\nContent Coverage: {content}"
            ),
        ]
    )

    model = get_chat_model(model_name=config.model_name, temperature=config.temperature)

    parser = PydanticOutputParser(pydantic_object=QuizOutput)

    # Build chain with parallel processing for efficiency
    chain = (
        RunnableParallel(
            objectives=RunnablePassthrough(),
            content=RunnablePassthrough(),
            format_instructions=lambda x: parser.get_format_instructions(),
        )
        | prompt
        | model
        | parser
    )

    logger.debug(f"Created quiz generation chain for {subject}")
    return chain


def create_terrain_generation_chain(environment_theme: str, config: Optional[ChainConfig] = None):
    """
    Create a chain for Roblox terrain generation.

    Args:
        environment_theme: Theme for the terrain
        config: Chain configuration

    Returns:
        LCEL chain for terrain generation
    """
    if not LANGCHAIN_AVAILABLE:
        raise ImportError("LangChain not available")

    config = config or ChainConfig(temperature=0.6)

    system_prompt = f"""You are an expert Roblox terrain designer and Lua programmer.

Create a {environment_theme} themed terrain with:
- Realistic and immersive features
- Educational elements integrated naturally
- Interactive components
- Optimized Lua code for Roblox Studio
- Clear documentation

Generate complete terrain specification with Lua implementation."""

    prompt = ChatPromptTemplate.from_messages(
        [
            SystemMessage(content=system_prompt),
            HumanMessage(content="Educational Goals: {goals}\n\nSpecial Features: {features}"),
        ]
    )

    model = get_chat_model(model_name=config.model_name, temperature=config.temperature)

    parser = PydanticOutputParser(pydantic_object=TerrainOutput)

    chain = (
        RunnablePassthrough.assign(format_instructions=lambda x: parser.get_format_instructions())
        | prompt
        | model
        | parser
    )

    logger.debug(f"Created terrain generation chain for {environment_theme}")
    return chain


def create_script_generation_chain(script_type: str, config: Optional[ChainConfig] = None):
    """
    Create a chain for Roblox Lua script generation.

    Args:
        script_type: Type of script to generate
        config: Chain configuration

    Returns:
        LCEL chain for script generation
    """
    if not LANGCHAIN_AVAILABLE:
        raise ImportError("LangChain not available")

    config = config or ChainConfig(temperature=0.4)

    system_prompt = f"""You are an expert Roblox Lua developer.

Generate a {script_type} script that is:
- Clean, efficient, and well-commented
- Following Roblox best practices
- Secure and performant
- Modular and reusable
- Includes error handling

Provide complete, production-ready Lua code."""

    prompt = ChatPromptTemplate.from_messages(
        [
            SystemMessage(content=system_prompt),
            HumanMessage(content="Functionality: {functionality}\n\nConstraints: {constraints}"),
        ]
    )

    model = get_chat_model(model_name=config.model_name, temperature=config.temperature)

    parser = PydanticOutputParser(pydantic_object=ScriptOutput)

    chain = (
        RunnablePassthrough.assign(format_instructions=lambda x: parser.get_format_instructions())
        | prompt
        | model
        | parser
    )

    logger.debug(f"Created script generation chain for {script_type}")
    return chain


def create_code_review_chain(language: str = "lua", config: Optional[ChainConfig] = None):
    """
    Create a chain for code review.

    Args:
        language: Programming language
        config: Chain configuration

    Returns:
        LCEL chain for code review
    """
    if not LANGCHAIN_AVAILABLE:
        raise ImportError("LangChain not available")

    config = config or ChainConfig(temperature=0.3)

    system_prompt = f"""You are an expert {language} code reviewer.

Perform a comprehensive code review checking for:
- Code quality and readability
- Performance issues
- Security vulnerabilities
- Best practices adherence
- Potential bugs
- Improvement opportunities

Provide constructive feedback with specific suggestions."""

    prompt = ChatPromptTemplate.from_messages(
        [
            SystemMessage(content=system_prompt),
            HumanMessage(
                content="Code to Review:\n```{language}\n{code}\n```\n\nContext: {context}"
            ),
        ]
    )

    model = get_chat_model(model_name=config.model_name, temperature=config.temperature)

    parser = PydanticOutputParser(pydantic_object=ReviewOutput)

    # Build review chain with structured output
    chain = (
        RunnablePassthrough.assign(
            language=lambda x: language,
            format_instructions=lambda x: parser.get_format_instructions(),
        )
        | prompt
        | model
        | parser
    )

    logger.debug(f"Created code review chain for {language}")
    return chain


# Composite chains for complex workflows
def create_full_environment_chain(
    subject: str,
    grade_level: str,
    environment_theme: str,
    config: Optional[ChainConfig] = None,
):
    """
    Create a composite chain for generating a complete educational environment.

    Args:
        subject: Subject area
        grade_level: Grade level
        environment_theme: Environment theme
        config: Chain configuration

    Returns:
        Composite LCEL chain
    """
    if not LANGCHAIN_AVAILABLE:
        raise ImportError("LangChain not available")

    config = config or ChainConfig()

    # Create individual chains
    content_chain = create_content_generation_chain(subject, grade_level, config)
    quiz_chain = create_quiz_generation_chain(subject, config=config)
    terrain_chain = create_terrain_generation_chain(environment_theme, config)
    script_chain = create_script_generation_chain("educational_interaction", config)

    # Combine in parallel for efficiency
    composite_chain = RunnableParallel(
        {
            "content": content_chain,
            "quiz": quiz_chain,
            "terrain": terrain_chain,
            "scripts": script_chain,
        }
    )

    logger.debug("Created full environment generation chain")
    return composite_chain
