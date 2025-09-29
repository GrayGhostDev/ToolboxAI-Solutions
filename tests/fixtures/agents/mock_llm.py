"""
Mock LLM Implementation for Testing
Provides mock responses for testing without requiring OpenAI API keys
"""

import random
import asyncio
from typing import List, Dict, Any, Optional, Union
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_core.language_models import BaseLLM
from langchain_core.outputs import LLMResult, Generation
from langchain_core.callbacks import CallbackManagerForLLMRun, AsyncCallbackManagerForLLMRun
from pydantic import Field


class MockLLM(BaseLLM):
    """Mock LLM for testing purposes"""
    
    model_name: str = Field(default="mock-llm", alias="model")
    temperature: float = Field(default=0.7)
    streaming: bool = Field(default=False)
    
    @property
    def _llm_type(self) -> str:
        """Return identifier of LLM type."""
        return "mock_llm"
    
    def _generate(
        self,
        prompts: List[str],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> LLMResult:
        """Generate mock responses for prompts."""
        generations = []
        
        for prompt in prompts:
            # Generate contextual mock response based on prompt content
            response = self._generate_mock_response(prompt)
            generations.append([Generation(text=response)])
        
        return LLMResult(generations=generations)  # type: ignore[reportCallIssue]
    
    async def _agenerate(
        self,
        prompts: List[str],
        stop: Optional[List[str]] = None,
        run_manager: Optional[AsyncCallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> LLMResult:
        """Async generate mock responses."""
        await asyncio.sleep(0.1)  # Simulate network delay
        return self._generate(prompts, stop)
    
    def _generate_mock_response(self, prompt: str) -> str:
        """Generate contextual mock response based on prompt content."""
        
        # Educational content generation
        if "educational" in prompt.lower() or "lesson" in prompt.lower():
            return """
            {
                "title": "Introduction to Solar System",
                "content": "The Solar System consists of the Sun and all objects that orbit it.",
                "learning_objectives": ["Understand planetary orbits", "Identify planets"],
                "grade_level": 7,
                "subject": "Science",
                "duration": 45,
                "materials": ["Interactive 3D models", "Quiz system"],
                "assessment": {
                    "type": "quiz",
                    "questions": 5,
                    "passing_score": 70
                }
            }
            """
        
        # Quiz generation
        elif "quiz" in prompt.lower() or "question" in prompt.lower():
            return """
            {
                "quiz": {
                    "title": "Solar System Quiz",
                    "questions": [
                        {
                            "question": "What is the largest planet?",
                            "options": ["Earth", "Jupiter", "Mars", "Venus"],
                            "correct": 1,
                            "explanation": "Jupiter is the largest planet in our solar system."
                        },
                        {
                            "question": "How many planets orbit the Sun?",
                            "options": ["7", "8", "9", "10"],
                            "correct": 1,
                            "explanation": "There are 8 planets in our solar system."
                        }
                    ],
                    "passing_score": 60,
                    "time_limit": 600
                }
            }
            """
        
        # Terrain generation
        elif "terrain" in prompt.lower() or "environment" in prompt.lower():
            return """
            {
                "terrain": {
                    "type": "space_station",
                    "features": ["Central hub", "Observation deck", "Science lab"],
                    "size": {"x": 100, "y": 50, "z": 100},
                    "materials": ["Metal", "Glass", "Neon"],
                    "lighting": "ambient_space",
                    "spawn_points": [{"x": 0, "y": 10, "z": 0}],
                    "interactive_elements": ["Telescope", "Computer terminals", "Holographic displays"]
                }
            }
            """
        
        # Script generation
        elif "script" in prompt.lower() or "lua" in prompt.lower() or "code" in prompt.lower():
            return """
            -- Generated Lua Script for Roblox
            local module = {}
            
            function module:Initialize()
                print("Initializing educational module")
                -- Setup code here
            end
            
            function module:StartLesson()
                print("Starting interactive lesson")
                -- Lesson logic here
            end
            
            return module
            """
        
        # Review/validation
        elif "review" in prompt.lower() or "validate" in prompt.lower():
            return """
            {
                "review": {
                    "status": "approved",
                    "score": 85,
                    "feedback": "Content is well-structured and age-appropriate",
                    "suggestions": ["Add more interactive elements", "Include visual aids"],
                    "quality_metrics": {
                        "accuracy": 90,
                        "engagement": 80,
                        "clarity": 85
                    }
                }
            }
            """
        
        # Task routing (for supervisor)
        elif "route" in prompt.lower() or "assign" in prompt.lower():
            return """
            {
                "agent": "content",
                "task": "generate_educational_content",
                "priority": "high",
                "parameters": {
                    "subject": "Science",
                    "grade_level": 7
                }
            }
            """
        
        # Orchestration response
        elif "orchestrate" in prompt.lower() or "workflow" in prompt.lower():
            return """
            {
                "workflow": "content_generation",
                "steps": [
                    {"agent": "content", "action": "generate", "status": "completed"},
                    {"agent": "quiz", "action": "create", "status": "completed"},
                    {"agent": "review", "action": "validate", "status": "completed"}
                ],
                "result": "success",
                "execution_time": 2.5
            }
            """
        
        # Default response
        else:
            return """
            {
                "response": "Mock response generated successfully",
                "status": "success",
                "data": {
                    "message": "This is a mock response for testing",
                    "timestamp": "2025-09-07T21:00:00Z",
                    "confidence": 0.95
                }
            }
            """


class MockChatModel:
    """Mock chat model for testing chat-based interactions"""
    
    def __init__(self, model_name: str = "mock-chat", **kwargs):
        self.model_name = model_name
        self.kwargs = kwargs
    
    def invoke(self, messages: List[BaseMessage], **kwargs) -> AIMessage:
        """Generate mock response for chat messages."""
        if messages:
            last_message = messages[-1].content if messages else ""
            # Use MockLLM to generate response
            mock_llm = MockLLM()
            response = mock_llm._generate_mock_response(last_message)
            return AIMessage(content=response)
        return AIMessage(content="Mock response")
    
    async def ainvoke(self, messages_or_prompt: Union[str, List[BaseMessage]], **kwargs) -> AIMessage:
        """Async generate mock response."""
        await asyncio.sleep(0.1)
        
        # Handle both string prompts and message lists
        if isinstance(messages_or_prompt, str):
            # Direct string prompt
            mock_llm = MockLLM()
            response = mock_llm._generate_mock_response(messages_or_prompt)
            return AIMessage(content=response)
        else:
            # List of messages
            return self.invoke(messages_or_prompt, **kwargs)
    
    def bind(self, **kwargs):
        """Bind additional parameters."""
        return self
    
    def with_structured_output(self, schema=None, **kwargs):
        """Return self for structured output compatibility."""
        return self


def get_mock_llm(model_name: str = "gpt-3.5-turbo", **kwargs) -> MockLLM:
    """
    Factory function to get mock LLM instance.
    Replaces real LLM when OPENAI_API_KEY is not available.
    """
    return MockLLM(model_name=model_name, **kwargs)


def get_mock_chat_model(model_name: str = "gpt-3.5-turbo", **kwargs) -> MockChatModel:
    """
    Factory function to get mock chat model instance.
    Replaces from langchain_openai import ChatOpenAI when OPENAI_API_KEY is not available.
    """
    return MockChatModel(model_name=model_name, **kwargs)


# Monkey-patch for testing without API keys
def patch_langchain_for_testing():
    """
    Patch LangChain to use mock models when API keys are not available.
    Call this in test setup or when OPENAI_API_KEY is not configured.
    """
    import os
    import sys
    
    # Check if OpenAI API key is available
    if not os.getenv("OPENAI_API_KEY") or os.getenv("USE_MOCK_LLM") == "true":
        # Patch from langchain_openai import ChatOpenAI import
        from unittest.mock import MagicMock
        
        # Create mock module
        mock_openai = MagicMock()
        mock_openai.ChatOpenAI = MockChatModel
        
        # Inject into sys.modules
        sys.modules["langchain_openai"] = mock_openai
        sys.modules["langchain.chat_models"] = mock_openai
        
        print("🤖 Using Mock LLM for testing (no OpenAI API key required)")
        return True
    
    return False