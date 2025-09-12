"""
RobloxPromptAnalyzer Agent - Natural language parsing for Roblox environment generation

Parses dashboard prompts to extract educational objectives, environment requirements,
and game specifications for Roblox world generation.
"""

import re
import logging
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
import json
from pathlib import Path

from ..base_agent import BaseAgent, AgentConfig, AgentState, TaskResult
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

# Import MCP for context management
try:
    from mcp.context_manager import ContextManager
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    ContextManager = None

logger = logging.getLogger(__name__)


class EducationalLevel:
    """Educational level classifications"""
    KINDERGARTEN = "kindergarten"
    ELEMENTARY = "elementary"      # Grades 1-5
    MIDDLE_SCHOOL = "middle_school" # Grades 6-8
    HIGH_SCHOOL = "high_school"    # Grades 9-12
    COLLEGE = "college"


class SubjectArea:
    """Subject area classifications"""
    MATH = "mathematics"
    SCIENCE = "science"
    ENGLISH = "english"
    HISTORY = "history"
    GEOGRAPHY = "geography"
    COMPUTER_SCIENCE = "computer_science"
    ART = "art"
    MUSIC = "music"
    PHYSICAL_EDUCATION = "physical_education"
    FOREIGN_LANGUAGE = "foreign_language"


class EnvironmentTheme:
    """Roblox environment themes"""
    SPACE = "space"
    UNDERWATER = "underwater"
    MEDIEVAL = "medieval"
    MODERN_CITY = "modern_city"
    FANTASY = "fantasy"
    JUNGLE = "jungle"
    DESERT = "desert"
    ARCTIC = "arctic"
    LABORATORY = "laboratory"
    CLASSROOM = "classroom"


class RobloxPromptAnalyzerAgent(BaseAgent):
    """
    Agent responsible for analyzing natural language prompts from the dashboard
    and extracting structured requirements for Roblox environment generation.
    
    Capabilities:
    - Natural language processing
    - Educational objective extraction
    - Grade level detection
    - Subject matter identification
    - Environment theme selection
    - Game mechanic suggestions
    - Accessibility requirement detection
    """
    
    def __init__(self, config: Optional[AgentConfig] = None):
        if not config:
            config = AgentConfig(
                name="RobloxPromptAnalyzer",
                model="gpt-3.5-turbo",
                temperature=0.3,  # Lower temperature for accurate parsing
                system_prompt=self._get_analyzer_prompt()
            )
        super().__init__(config)
        
        # MCP integration for context management
        self.context_manager = ContextManager() if MCP_AVAILABLE else None
        
        # Analysis patterns
        self.grade_patterns = {
            r'\b(kindergarten|k)\b': 0,
            r'\b(first|1st)\s+grade\b': 1,
            r'\b(second|2nd)\s+grade\b': 2,
            r'\b(third|3rd)\s+grade\b': 3,
            r'\b(fourth|4th)\s+grade\b': 4,
            r'\b(fifth|5th)\s+grade\b': 5,
            r'\b(sixth|6th)\s+grade\b': 6,
            r'\b(seventh|7th)\s+grade\b': 7,
            r'\b(eighth|8th)\s+grade\b': 8,
            r'\b(ninth|9th)\s+grade\b': 9,
            r'\b(tenth|10th)\s+grade\b': 10,
            r'\b(eleventh|11th)\s+grade\b': 11,
            r'\b(twelfth|12th)\s+grade\b': 12,
            r'\bgrade\s+(\d+)\b': 'extract'
        }
        
        # Subject keywords
        self.subject_keywords = {
            SubjectArea.MATH: ["math", "algebra", "geometry", "calculus", "arithmetic", "numbers"],
            SubjectArea.SCIENCE: ["science", "biology", "chemistry", "physics", "experiment", "lab"],
            SubjectArea.ENGLISH: ["english", "reading", "writing", "grammar", "literature", "vocabulary"],
            SubjectArea.HISTORY: ["history", "historical", "past", "civilization", "war", "timeline"],
            SubjectArea.GEOGRAPHY: ["geography", "maps", "countries", "continents", "earth", "location"],
            SubjectArea.COMPUTER_SCIENCE: ["programming", "coding", "computer", "algorithm", "software"],
            SubjectArea.ART: ["art", "drawing", "painting", "sculpture", "creative", "design"],
            SubjectArea.MUSIC: ["music", "rhythm", "melody", "instrument", "song", "composition"],
            SubjectArea.PHYSICAL_EDUCATION: ["physical", "sports", "exercise", "fitness", "health"],
            SubjectArea.FOREIGN_LANGUAGE: ["spanish", "french", "german", "chinese", "language", "foreign"]
        }
        
        # Theme keywords
        self.theme_keywords = {
            EnvironmentTheme.SPACE: ["space", "galaxy", "planet", "star", "astronaut", "rocket"],
            EnvironmentTheme.UNDERWATER: ["ocean", "underwater", "marine", "fish", "submarine", "coral"],
            EnvironmentTheme.MEDIEVAL: ["medieval", "castle", "knight", "dragon", "kingdom", "ancient"],
            EnvironmentTheme.MODERN_CITY: ["city", "urban", "building", "street", "modern", "skyscraper"],
            EnvironmentTheme.FANTASY: ["fantasy", "magic", "wizard", "fairy", "enchanted", "mystical"],
            EnvironmentTheme.JUNGLE: ["jungle", "forest", "rainforest", "tropical", "safari", "wildlife"],
            EnvironmentTheme.DESERT: ["desert", "sand", "pyramid", "oasis", "cactus", "arid"],
            EnvironmentTheme.ARCTIC: ["arctic", "ice", "snow", "polar", "frozen", "tundra"],
            EnvironmentTheme.LABORATORY: ["lab", "laboratory", "science", "experiment", "research", "test"],
            EnvironmentTheme.CLASSROOM: ["classroom", "school", "desk", "board", "teacher", "student"]
        }
    
    def _get_analyzer_prompt(self) -> str:
        """Get specialized analyzer prompt"""
        return """You are a Natural Language Processing expert for educational Roblox environment generation.
        
Your responsibilities:
- Parse natural language prompts from educators
- Extract clear educational objectives
- Identify grade levels and age groups
- Determine subject matter and topics
- Suggest appropriate Roblox environment themes
- Recommend game mechanics that support learning
- Identify accessibility and special requirements
- Structure information for downstream agents

Always provide structured, actionable output that other agents can use.
Prioritize educational value while maintaining engagement potential.
"""
    
    async def _process_task(self, state: AgentState) -> Any:
        """Process prompt analysis task"""
        task = state["task"]
        context = state["context"]
        
        # Get the prompt to analyze
        prompt = context.get("prompt", "")
        
        if not prompt:
            return {
                "error": "No prompt provided for analysis",
                "requirements": {}
            }
        
        # Store prompt in MCP context if available
        if self.context_manager:
            await self._store_in_context("original_prompt", prompt)
        
        # Extract components
        grade_level = self._extract_grade_level(prompt)
        subjects = self._extract_subjects(prompt)
        themes = self._extract_themes(prompt)
        objectives = await self._extract_learning_objectives(prompt, subjects)
        game_mechanics = await self._suggest_game_mechanics(prompt, subjects, grade_level)
        accessibility = self._extract_accessibility_requirements(prompt)
        
        # Structure the requirements
        structured_requirements = {
            "educational_requirements": {
                "grade_level": grade_level,
                "age_range": self._grade_to_age_range(grade_level),
                "subjects": subjects,
                "learning_objectives": objectives,
                "assessment_type": self._determine_assessment_type(prompt)
            },
            "environment_specifications": {
                "themes": themes,
                "preferred_theme": themes[0] if themes else EnvironmentTheme.CLASSROOM,
                "world_size": self._determine_world_size(prompt),
                "player_count": self._extract_player_count(prompt),
                "duration": self._extract_duration(prompt)
            },
            "game_specifications": {
                "suggested_mechanics": game_mechanics,
                "difficulty_level": self._determine_difficulty(grade_level),
                "progression_type": self._determine_progression_type(prompt),
                "reward_system": self._suggest_reward_system(grade_level)
            },
            "accessibility_requirements": accessibility,
            "special_features": self._extract_special_features(prompt),
            "metadata": {
                "analysis_timestamp": datetime.now().isoformat(),
                "prompt_length": len(prompt),
                "confidence_score": self._calculate_confidence_score(prompt)
            }
        }
        
        # Store in MCP context
        if self.context_manager:
            await self._store_in_context("structured_requirements", structured_requirements)
        
        return structured_requirements
    
    def _extract_grade_level(self, prompt: str) -> int:
        """Extract grade level from prompt"""
        prompt_lower = prompt.lower()
        
        for pattern, grade in self.grade_patterns.items():
            if grade == 'extract':
                match = re.search(pattern, prompt_lower)
                if match:
                    return int(match.group(1))
            else:
                if re.search(pattern, prompt_lower):
                    return grade
        
        # Default to grade 5 if not specified
        return 5
    
    def _extract_subjects(self, prompt: str) -> List[str]:
        """Extract subject areas from prompt"""
        prompt_lower = prompt.lower()
        detected_subjects = []
        
        for subject, keywords in self.subject_keywords.items():
            for keyword in keywords:
                if keyword in prompt_lower:
                    detected_subjects.append(subject)
                    break
        
        # Default to general education if no specific subject
        if not detected_subjects:
            detected_subjects.append(SubjectArea.MATH)  # Default subject
        
        return detected_subjects
    
    def _extract_themes(self, prompt: str) -> List[str]:
        """Extract environment themes from prompt"""
        prompt_lower = prompt.lower()
        detected_themes = []
        
        for theme, keywords in self.theme_keywords.items():
            for keyword in keywords:
                if keyword in prompt_lower:
                    detected_themes.append(theme)
                    break
        
        # Default to classroom if no theme specified
        if not detected_themes:
            detected_themes.append(EnvironmentTheme.CLASSROOM)
        
        return detected_themes
    
    async def _extract_learning_objectives(self, prompt: str, subjects: List[str]) -> List[Dict[str, Any]]:
        """Extract specific learning objectives using LLM"""
        
        objectives_prompt = f"""Extract specific learning objectives from this educational prompt:
        
        Prompt: {prompt}
        Detected Subjects: {subjects}
        
        List clear, measurable learning objectives. Format as:
        - Objective
        - Skill Level (beginner/intermediate/advanced)
        - Assessment Method
        """
        
        try:
            response = await self.llm.ainvoke(objectives_prompt)
            
            # Parse response into structured objectives
            objectives = []
            lines = response.content.split('\n')
            
            current_objective = {}
            for line in lines:
                line = line.strip()
                if line.startswith('- Objective'):
                    if current_objective:
                        objectives.append(current_objective)
                    current_objective = {"description": line.replace('- Objective:', '').strip()}
                elif line.startswith('- Skill Level'):
                    current_objective["skill_level"] = line.replace('- Skill Level:', '').strip()
                elif line.startswith('- Assessment'):
                    current_objective["assessment"] = line.replace('- Assessment Method:', '').strip()
            
            if current_objective:
                objectives.append(current_objective)
            
            return objectives if objectives else [{"description": "General learning", "skill_level": "beginner"}]
            
        except Exception as e:
            logger.error(f"Error extracting objectives: {e}")
            return [{"description": "General learning", "skill_level": "beginner"}]
    
    async def _suggest_game_mechanics(self, prompt: str, subjects: List[str], grade_level: int) -> List[str]:
        """Suggest appropriate game mechanics"""
        
        mechanics = []
        
        # Age-appropriate mechanics
        if grade_level <= 2:  # K-2
            mechanics.extend(["simple_clicking", "drag_and_drop", "color_matching", "basic_collection"])
        elif grade_level <= 5:  # 3-5
            mechanics.extend(["puzzle_solving", "platform_jumping", "quiz_challenges", "building"])
        elif grade_level <= 8:  # 6-8
            mechanics.extend(["strategy", "resource_management", "complex_puzzles", "multiplayer"])
        else:  # 9-12
            mechanics.extend(["simulation", "programming", "advanced_strategy", "creative_building"])
        
        # Subject-specific mechanics
        if SubjectArea.MATH in subjects:
            mechanics.extend(["calculation_races", "number_puzzles", "geometry_building"])
        if SubjectArea.SCIENCE in subjects:
            mechanics.extend(["experiment_simulation", "discovery_quests", "lab_management"])
        if SubjectArea.HISTORY in subjects:
            mechanics.extend(["time_travel", "civilization_building", "historical_roleplay"])
        
        return list(set(mechanics))  # Remove duplicates
    
    def _extract_accessibility_requirements(self, prompt: str) -> Dict[str, Any]:
        """Extract accessibility requirements"""
        prompt_lower = prompt.lower()
        
        requirements = {
            "visual_aids": "visual" in prompt_lower or "color blind" in prompt_lower,
            "audio_support": "audio" in prompt_lower or "hearing" in prompt_lower,
            "simple_controls": "simple" in prompt_lower or "easy" in prompt_lower,
            "text_to_speech": "speech" in prompt_lower or "read aloud" in prompt_lower,
            "adjustable_speed": "pace" in prompt_lower or "speed" in prompt_lower,
            "subtitles": "subtitle" in prompt_lower or "caption" in prompt_lower
        }
        
        return requirements
    
    def _grade_to_age_range(self, grade: int) -> Tuple[int, int]:
        """Convert grade level to age range"""
        if grade == 0:  # Kindergarten
            return (5, 6)
        else:
            min_age = grade + 5
            max_age = grade + 6
            return (min_age, max_age)
    
    def _determine_assessment_type(self, prompt: str) -> str:
        """Determine assessment type from prompt"""
        prompt_lower = prompt.lower()
        
        if "quiz" in prompt_lower:
            return "quiz_based"
        elif "project" in prompt_lower:
            return "project_based"
        elif "test" in prompt_lower or "exam" in prompt_lower:
            return "formal_testing"
        elif "portfolio" in prompt_lower:
            return "portfolio"
        else:
            return "continuous_assessment"
    
    def _determine_world_size(self, prompt: str) -> str:
        """Determine world size from prompt"""
        prompt_lower = prompt.lower()
        
        if "large" in prompt_lower or "huge" in prompt_lower:
            return "large"
        elif "small" in prompt_lower or "compact" in prompt_lower:
            return "small"
        else:
            return "medium"
    
    def _extract_player_count(self, prompt: str) -> str:
        """Extract player count from prompt"""
        prompt_lower = prompt.lower()
        
        # Look for specific numbers
        numbers = re.findall(r'\b(\d+)\s*players?\b', prompt_lower)
        if numbers:
            return f"up_to_{numbers[0]}"
        
        if "single" in prompt_lower or "solo" in prompt_lower:
            return "single_player"
        elif "multiplayer" in prompt_lower or "group" in prompt_lower:
            return "multiplayer"
        else:
            return "flexible"
    
    def _extract_duration(self, prompt: str) -> int:
        """Extract expected play duration in minutes"""
        prompt_lower = prompt.lower()
        
        # Look for specific time mentions
        minutes = re.findall(r'\b(\d+)\s*minutes?\b', prompt_lower)
        if minutes:
            return int(minutes[0])
        
        hours = re.findall(r'\b(\d+)\s*hours?\b', prompt_lower)
        if hours:
            return int(hours[0]) * 60
        
        # Default based on keywords
        if "quick" in prompt_lower or "short" in prompt_lower:
            return 15
        elif "long" in prompt_lower or "extended" in prompt_lower:
            return 60
        else:
            return 30  # Default 30 minutes
    
    def _determine_difficulty(self, grade_level: int) -> str:
        """Determine difficulty based on grade level"""
        if grade_level <= 2:
            return "easy"
        elif grade_level <= 5:
            return "medium"
        elif grade_level <= 8:
            return "challenging"
        else:
            return "advanced"
    
    def _determine_progression_type(self, prompt: str) -> str:
        """Determine progression type from prompt"""
        prompt_lower = prompt.lower()
        
        if "linear" in prompt_lower or "sequential" in prompt_lower:
            return "linear"
        elif "open" in prompt_lower or "sandbox" in prompt_lower:
            return "open_world"
        elif "branch" in prompt_lower or "choice" in prompt_lower:
            return "branching"
        else:
            return "adaptive"
    
    def _suggest_reward_system(self, grade_level: int) -> Dict[str, Any]:
        """Suggest appropriate reward system"""
        
        if grade_level <= 2:
            return {
                "type": "visual_rewards",
                "elements": ["stars", "stickers", "animations", "sounds"],
                "frequency": "frequent"
            }
        elif grade_level <= 5:
            return {
                "type": "points_and_badges",
                "elements": ["points", "badges", "trophies", "unlockables"],
                "frequency": "moderate"
            }
        elif grade_level <= 8:
            return {
                "type": "achievement_system",
                "elements": ["achievements", "leaderboards", "ranks", "collectibles"],
                "frequency": "balanced"
            }
        else:
            return {
                "type": "mastery_based",
                "elements": ["skill_trees", "certifications", "portfolios", "peer_recognition"],
                "frequency": "milestone_based"
            }
    
    def _extract_special_features(self, prompt: str) -> List[str]:
        """Extract any special feature requests"""
        features = []
        prompt_lower = prompt.lower()
        
        if "voice" in prompt_lower:
            features.append("voice_chat")
        if "creative" in prompt_lower or "build" in prompt_lower:
            features.append("creative_mode")
        if "compete" in prompt_lower or "competition" in prompt_lower:
            features.append("competitive_mode")
        if "collaborate" in prompt_lower or "team" in prompt_lower:
            features.append("collaboration_tools")
        if "parent" in prompt_lower:
            features.append("parent_dashboard")
        if "offline" in prompt_lower:
            features.append("offline_mode")
        
        return features
    
    def _calculate_confidence_score(self, prompt: str) -> float:
        """Calculate confidence in analysis"""
        score = 0.5  # Base score
        
        # Increase confidence for specific mentions
        if re.search(r'grade\s+\d+', prompt.lower()):
            score += 0.1
        if any(subj in prompt.lower() for subj in ["math", "science", "english"]):
            score += 0.1
        if len(prompt) > 100:
            score += 0.1
        if "objective" in prompt.lower() or "goal" in prompt.lower():
            score += 0.1
        if any(theme in prompt.lower() for theme in ["space", "ocean", "castle"]):
            score += 0.1
        
        return min(1.0, score)
    
    async def _store_in_context(self, key: str, value: Any):
        """Store data in MCP context if available"""
        if self.context_manager:
            try:
                # Store in context for other agents to access
                context_data = {
                    "agent": "RobloxPromptAnalyzer",
                    "timestamp": datetime.now().isoformat(),
                    "data": {key: value}
                }
                # Implementation would connect to actual MCP
                logger.debug(f"Stored {key} in MCP context")
            except Exception as e:
                logger.error(f"Failed to store in MCP context: {e}")
    
    async def analyze_prompt(self, prompt: str) -> Dict[str, Any]:
        """Main method to analyze a dashboard prompt"""
        context = {"prompt": prompt}
        result = await self.execute("Analyze educational prompt", context)
        return result.output