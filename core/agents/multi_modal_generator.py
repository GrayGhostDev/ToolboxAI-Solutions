"""
Multi-Modal Content Generator

Advanced system for generating diverse content types including text, code, 3D assets,
audio, and visual elements for comprehensive educational experiences in Roblox.

Author: ToolboxAI Team
Created: 2025-09-19
Version: 2.0.0
"""

import asyncio
import logging
import json
import base64
from typing import Dict, Any, List, Optional, Union, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path

from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.output_parsers import JsonOutputParser
from langchain.chains import LLMChain
from langchain_core.prompts import PromptTemplate

from core.agents.base_agent import BaseAgent, AgentConfig, TaskResult
from core.agents.adaptive_learning_engine import LearningStyle

logger = logging.getLogger(__name__)


class ContentModality(Enum):
    """Types of content modalities"""
    TEXT = "text"
    CODE = "code"
    VISUAL = "visual"
    AUDIO = "audio"
    THREE_D = "3d"
    ANIMATION = "animation"
    INTERACTIVE = "interactive"


class AssetType(Enum):
    """Types of Roblox assets"""
    SCRIPT = "script"
    MODEL = "model"
    TEXTURE = "texture"
    SOUND = "sound"
    PARTICLE = "particle"
    TERRAIN = "terrain"
    UI = "ui"
    ANIMATION = "animation"


@dataclass
class GenerationRequest:
    """Request for multi-modal content generation"""
    content_type: str
    subject: str
    learning_objectives: List[str]
    grade_level: str
    modalities: List[ContentModality]

    # Optional parameters
    learning_style: Optional[LearningStyle] = None
    complexity: float = 0.5  # 0-1 scale
    duration_minutes: int = 30
    interactive_elements: bool = True
    accessibility_requirements: List[str] = field(default_factory=list)

    # Roblox-specific
    game_genre: str = "adventure"
    max_players: int = 20
    device_targets: List[str] = field(default_factory=lambda: ["computer", "mobile", "tablet"])

    # Context
    previous_content: Optional[Dict[str, Any]] = None
    user_preferences: Optional[Dict[str, Any]] = None


@dataclass
class GeneratedContent:
    """Container for generated multi-modal content"""
    content_id: str
    request: GenerationRequest

    # Generated content by modality
    text_content: Dict[str, Any] = field(default_factory=dict)
    code_content: Dict[str, Any] = field(default_factory=dict)
    visual_content: Dict[str, Any] = field(default_factory=dict)
    audio_content: Dict[str, Any] = field(default_factory=dict)
    asset_content: Dict[str, Any] = field(default_factory=dict)

    # Metadata
    generation_time: float = 0.0
    quality_scores: Dict[str, float] = field(default_factory=dict)
    tokens_used: Dict[str, int] = field(default_factory=dict)

    # Status
    status: str = "generating"
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


class MultiModalGenerator(BaseAgent):
    """
    Advanced multi-modal content generator that creates diverse educational
    content types for immersive Roblox experiences.

    Capabilities:
    - Text generation (narratives, instructions, dialogue)
    - Code generation (Luau scripts, game logic)
    - Visual content (UI layouts, color schemes)
    - Audio planning (sound effects, music cues)
    - 3D asset specifications (models, terrain)
    - Interactive element design
    """

    def __init__(self):
        """Initialize the multi-modal generator"""

        config = AgentConfig(
            name="MultiModalGenerator",
            model="gpt-4-turbo-preview",
            temperature=0.7,
            max_retries=3,
            timeout=600,
            verbose=True,
            system_prompt=self._get_generator_system_prompt()
        )

        super().__init__(config)

        # Specialized generators for each modality
        self.text_generator = self._initialize_text_generator()
        self.code_generator = self._initialize_code_generator()
        self.visual_generator = self._initialize_visual_generator()
        self.audio_generator = self._initialize_audio_generator()
        self.asset_generator = self._initialize_asset_generator()

        # Output parsers
        self.json_parser = JsonOutputParser()

        # Generation templates
        self.templates = self._load_generation_templates()

        logger.info("Multi-Modal Generator initialized")

    def _get_generator_system_prompt(self) -> str:
        """Get the system prompt for multi-modal generation"""
        return """You are an Advanced Multi-Modal Content Generator for educational Roblox experiences.

Your expertise spans:

1. **Text Generation**:
   - Educational narratives and storylines
   - Clear instructions and tutorials
   - Engaging dialogue for NPCs
   - Learning checkpoint descriptions
   - Achievement and feedback messages

2. **Code Generation**:
   - Luau scripts for game mechanics
   - Event handlers and interactions
   - Data persistence and progress tracking
   - Performance-optimized algorithms
   - Modular, reusable components

3. **Visual Design**:
   - UI/UX layouts for different devices
   - Color schemes for accessibility
   - Visual feedback systems
   - HUD and menu designs
   - Particle effects specifications

4. **Audio Planning**:
   - Sound effect requirements
   - Background music moods
   - Audio cues for actions
   - Narration scripts
   - Accessibility audio descriptions

5. **3D Asset Specifications**:
   - Model requirements and descriptions
   - Terrain generation parameters
   - Texture and material needs
   - Animation requirements
   - Environmental design

6. **Interactive Elements**:
   - Puzzle mechanics
   - Mini-games design
   - Collaboration features
   - Assessment integration
   - Adaptive difficulty systems

Always ensure content is:
- Age-appropriate and safe
- Educationally valuable
- Technically feasible in Roblox
- Optimized for performance
- Accessible and inclusive
"""

    def _initialize_text_generator(self) -> LLMChain:
        """Initialize text content generator"""
        template = """Generate educational text content for a Roblox experience.

Subject: {subject}
Grade Level: {grade_level}
Learning Objectives: {learning_objectives}
Content Type: {content_type}
Style: {style}

Generate the following text elements:
1. Main narrative or storyline
2. Learning instructions
3. NPC dialogue (at least 3 characters)
4. UI text (buttons, menus, tooltips)
5. Feedback messages (success, error, hints)
6. Achievement descriptions

Format as JSON with clear structure.
"""

        prompt = PromptTemplate(
            template=template,
            input_variables=["subject", "grade_level", "learning_objectives",
                           "content_type", "style"]
        )

        return LLMChain(llm=self.llm, prompt=prompt, verbose=False, output_key="output")

    def _initialize_code_generator(self) -> LLMChain:
        """Initialize Luau code generator"""
        template = """Generate Luau scripts for an educational Roblox experience.

Subject: {subject}
Learning Objectives: {learning_objectives}
Game Mechanics: {mechanics}
Interactions: {interactions}
Complexity Level: {complexity}

Generate the following Luau scripts:

1. **Main Game Controller** (ServerScriptService)
   - Game state management
   - Player progress tracking
   - Learning objective validation

2. **Player Controller** (StarterPlayer/StarterPlayerScripts)
   - Movement and interactions
   - Input handling
   - Client-side feedback

3. **Educational Module** (ServerScriptService)
   - Content delivery
   - Assessment logic
   - Adaptive difficulty

4. **UI Manager** (StarterGui)
   - HUD updates
   - Menu systems
   - Progress display

5. **Data Persistence** (ServerScriptService)
   - Save/load progress
   - Analytics tracking
   - Achievement system

Include:
- Proper error handling
- Performance optimization
- Security best practices
- Clear documentation comments

Format each script with proper Roblox service usage and event handling.
"""

        prompt = PromptTemplate(
            template=template,
            input_variables=["subject", "learning_objectives", "mechanics",
                           "interactions", "complexity"]
        )

        return LLMChain(llm=self.llm, prompt=prompt, verbose=False, output_key="output")

    def _initialize_visual_generator(self) -> LLMChain:
        """Initialize visual content generator"""
        template = """Design visual elements for an educational Roblox experience.

Subject: {subject}
Target Age: {target_age}
Learning Style: {learning_style}
Accessibility Requirements: {accessibility}
Device Targets: {devices}

Generate specifications for:

1. **User Interface Design**:
   - Main menu layout
   - HUD elements and positioning
   - Progress indicators
   - Modal dialogs and popups
   - Mobile-responsive layouts

2. **Color Scheme**:
   - Primary and secondary colors
   - Accessibility contrast ratios
   - Emotional associations
   - State indicators (success, error, warning)

3. **Visual Feedback Systems**:
   - Particle effects for achievements
   - Highlight colors for interactions
   - Animation transitions
   - Loading indicators

4. **Environmental Design**:
   - Lighting setup
   - Skybox specifications
   - Ambient effects
   - Weather systems (if applicable)

5. **Asset Style Guide**:
   - Model aesthetic (realistic, cartoon, minimal)
   - Texture resolution guidelines
   - Material properties
   - Consistent visual language

Format as detailed specifications with hex codes, dimensions, and Roblox property values.
"""

        prompt = PromptTemplate(
            template=template,
            input_variables=["subject", "target_age", "learning_style",
                           "accessibility", "devices"]
        )

        return LLMChain(llm=self.llm, prompt=prompt, verbose=False, output_key="output")

    def _initialize_audio_generator(self) -> LLMChain:
        """Initialize audio content generator"""
        template = """Design audio elements for an educational Roblox experience.

Subject: {subject}
Mood: {mood}
Duration: {duration} minutes
Accessibility: {accessibility}

Generate audio specifications for:

1. **Background Music**:
   - Main theme description
   - Intensity levels for different areas
   - Transition cues
   - Emotional targeting

2. **Sound Effects**:
   - Interaction sounds (click, hover, select)
   - Achievement sounds
   - Error/warning sounds
   - Ambient environmental sounds
   - Educational feedback sounds

3. **Voice/Narration**:
   - Character voice profiles
   - Narration style and tone
   - Key phrases and scripts
   - Language considerations

4. **Adaptive Audio**:
   - Volume ducking rules
   - Dynamic music based on progress
   - Stress/calm indicators
   - Focus enhancement sounds

5. **Accessibility Audio**:
   - Screen reader compatible descriptions
   - Audio cues for visual elements
   - Spatial audio for navigation
   - Clear speech parameters

Provide detailed descriptions, timing, and implementation notes for Roblox SoundService.
"""

        prompt = PromptTemplate(
            template=template,
            input_variables=["subject", "mood", "duration", "accessibility"]
        )

        return LLMChain(llm=self.llm, prompt=prompt, verbose=False, output_key="output")

    def _initialize_asset_generator(self) -> LLMChain:
        """Initialize 3D asset and environment generator"""
        template = """Design 3D assets and environment for an educational Roblox experience.

Subject: {subject}
Setting: {setting}
Scale: {scale}
Performance Target: {performance}
Players: {max_players}

Generate specifications for:

1. **Terrain Design**:
   - Terrain materials and distribution
   - Elevation maps
   - Water bodies
   - Vegetation placement
   - Path layouts

2. **3D Models Required**:
   - Educational props (books, tools, equipment)
   - Interactive objects
   - Character models/NPCs
   - Buildings and structures
   - Vehicles (if applicable)

3. **Optimization Requirements**:
   - LOD (Level of Detail) settings
   - Polygon counts per model
   - Texture atlas organization
   - Instance optimization
   - Streaming enabled regions

4. **Interactive Zones**:
   - Learning stations layout
   - Puzzle areas
   - Collaboration spaces
   - Safe zones
   - Challenge areas

5. **Environmental Systems**:
   - Day/night cycle parameters
   - Weather effects
   - Physics zones
   - Spawn points
   - Boundaries and invisible walls

Include Roblox Studio implementation details and performance considerations.
"""

        prompt = PromptTemplate(
            template=template,
            input_variables=["subject", "setting", "scale", "performance", "max_players"]
        )

        return LLMChain(llm=self.llm, prompt=prompt, verbose=False, output_key="output")

    def _load_generation_templates(self) -> Dict[str, Any]:
        """Load content generation templates"""
        return {
            "math": {
                "narrative": "Mathematical adventure through {topic}",
                "npcs": ["Professor Calculator", "Digit the Robot", "Fraction Fox"],
                "settings": ["Number Laboratory", "Geometry Garden", "Algebra Arena"]
            },
            "science": {
                "narrative": "Scientific exploration of {topic}",
                "npcs": ["Dr. Discovery", "Lab Assistant Luna", "Professor Proton"],
                "settings": ["Research Lab", "Nature Observatory", "Space Station"]
            },
            "history": {
                "narrative": "Time-traveling journey to {topic}",
                "npcs": ["Chronicler Chris", "Explorer Eva", "Historian Hal"],
                "settings": ["Time Machine Hub", "Historical Sites", "Museum of Ages"]
            },
            "language": {
                "narrative": "Linguistic quest through {topic}",
                "npcs": ["Grammar Guardian", "Vocabulary Victor", "Story Sage"],
                "settings": ["Library of Languages", "Word Workshop", "Story Studio"]
            }
        }

    async def generate(self, request: GenerationRequest) -> GeneratedContent:
        """
        Generate multi-modal educational content

        Args:
            request: Generation request with parameters

        Returns:
            Generated multi-modal content
        """
        logger.info(f"Starting multi-modal generation for {request.subject}")

        content = GeneratedContent(
            content_id=f"content_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            request=request
        )

        start_time = datetime.now()

        try:
            # Generate content for each requested modality in parallel
            generation_tasks = []

            if ContentModality.TEXT in request.modalities:
                generation_tasks.append(self._generate_text_content(request, content))

            if ContentModality.CODE in request.modalities:
                generation_tasks.append(self._generate_code_content(request, content))

            if ContentModality.VISUAL in request.modalities:
                generation_tasks.append(self._generate_visual_content(request, content))

            if ContentModality.AUDIO in request.modalities:
                generation_tasks.append(self._generate_audio_content(request, content))

            if ContentModality.THREE_D in request.modalities:
                generation_tasks.append(self._generate_3d_content(request, content))

            # Execute all generation tasks
            results = await asyncio.gather(*generation_tasks, return_exceptions=True)

            # Process results and handle any errors
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    content.errors.append(f"Generation error in task {i}: {str(result)}")
                    logger.error(f"Generation task {i} failed: {result}")

            # Calculate quality scores
            content.quality_scores = self._calculate_quality_scores(content)

            # Set final status
            if content.errors:
                content.status = "completed_with_errors"
            else:
                content.status = "completed"

        except Exception as e:
            logger.error(f"Multi-modal generation failed: {e}")
            content.status = "failed"
            content.errors.append(str(e))

        finally:
            content.generation_time = (datetime.now() - start_time).total_seconds()

        return content

    async def _generate_text_content(
        self,
        request: GenerationRequest,
        content: GeneratedContent
    ) -> None:
        """Generate text-based content"""
        try:
            # Get template for subject
            template = self.templates.get(
                request.subject.lower().split()[0],
                self.templates.get("math")
            )

            # Prepare style based on learning style
            style = "visual and descriptive" if request.learning_style == LearningStyle.VISUAL else "clear and structured"

            # Generate text content
            result = await self.text_generator.ainvoke({
                "subject": request.subject,
                "grade_level": request.grade_level,
                "learning_objectives": ", ".join(request.learning_objectives),
                "content_type": request.content_type,
                "style": style
            })

            # Parse and structure the result
            try:
                text_data = self.json_parser.parse(result["text"])
            except:
                # Fallback to structured extraction
                text_data = self._extract_text_structure(result["text"])

            content.text_content = {
                "narrative": text_data.get("narrative", template["narrative"]),
                "instructions": text_data.get("instructions", []),
                "dialogue": text_data.get("dialogue", {}),
                "ui_text": text_data.get("ui_text", {}),
                "feedback": text_data.get("feedback", {}),
                "achievements": text_data.get("achievements", [])
            }

            # Track tokens
            content.tokens_used["text"] = len(result["text"].split()) * 2  # Rough estimate

            logger.info("Text content generated successfully")

        except Exception as e:
            logger.error(f"Text generation failed: {e}")
            content.errors.append(f"Text generation error: {str(e)}")

    async def _generate_code_content(
        self,
        request: GenerationRequest,
        content: GeneratedContent
    ) -> None:
        """Generate Luau code content"""
        try:
            # Define game mechanics based on content type
            mechanics = self._determine_game_mechanics(request)
            interactions = self._determine_interactions(request)

            # Generate code
            result = await self.code_generator.ainvoke({
                "subject": request.subject,
                "learning_objectives": ", ".join(request.learning_objectives),
                "mechanics": ", ".join(mechanics),
                "interactions": ", ".join(interactions),
                "complexity": request.complexity
            })

            # Parse and structure scripts
            scripts = self._parse_lua_scripts(result["text"])

            content.code_content = {
                "scripts": scripts,
                "main_controller": scripts.get("MainGameController", ""),
                "player_controller": scripts.get("PlayerController", ""),
                "educational_module": scripts.get("EducationalModule", ""),
                "ui_manager": scripts.get("UIManager", ""),
                "data_persistence": scripts.get("DataPersistence", ""),
                "dependencies": self._extract_dependencies(scripts)
            }

            # Track tokens
            content.tokens_used["code"] = len(result["text"].split()) * 2

            logger.info("Code content generated successfully")

        except Exception as e:
            logger.error(f"Code generation failed: {e}")
            content.errors.append(f"Code generation error: {str(e)}")

    async def _generate_visual_content(
        self,
        request: GenerationRequest,
        content: GeneratedContent
    ) -> None:
        """Generate visual design specifications"""
        try:
            # Prepare accessibility requirements
            accessibility_str = ", ".join(request.accessibility_requirements) if request.accessibility_requirements else "standard WCAG 2.1"

            # Generate visual specifications
            result = await self.visual_generator.ainvoke({
                "subject": request.subject,
                "target_age": self._estimate_age_from_grade(request.grade_level),
                "learning_style": request.learning_style.value if request.learning_style else "mixed",
                "accessibility": accessibility_str,
                "devices": ", ".join(request.device_targets)
            })

            # Parse visual specifications
            visual_data = self._parse_visual_specs(result["text"])

            content.visual_content = {
                "ui_design": visual_data.get("ui_design", {}),
                "color_scheme": visual_data.get("color_scheme", {
                    "primary": "#4A90E2",
                    "secondary": "#50C878",
                    "background": "#F5F5F5",
                    "text": "#333333",
                    "error": "#E74C3C",
                    "success": "#27AE60"
                }),
                "visual_feedback": visual_data.get("visual_feedback", {}),
                "environmental_design": visual_data.get("environmental_design", {}),
                "asset_style": visual_data.get("asset_style", {})
            }

            # Track tokens
            content.tokens_used["visual"] = len(result["text"].split()) * 2

            logger.info("Visual content generated successfully")

        except Exception as e:
            logger.error(f"Visual generation failed: {e}")
            content.errors.append(f"Visual generation error: {str(e)}")

    async def _generate_audio_content(
        self,
        request: GenerationRequest,
        content: GeneratedContent
    ) -> None:
        """Generate audio specifications"""
        try:
            # Determine mood based on subject and content type
            mood = self._determine_audio_mood(request)

            # Generate audio specifications
            result = await self.audio_generator.ainvoke({
                "subject": request.subject,
                "mood": mood,
                "duration": request.duration_minutes,
                "accessibility": "full accessibility support" if request.accessibility_requirements else "standard"
            })

            # Parse audio specifications
            audio_data = self._parse_audio_specs(result["text"])

            content.audio_content = {
                "background_music": audio_data.get("background_music", {}),
                "sound_effects": audio_data.get("sound_effects", {}),
                "narration": audio_data.get("narration", {}),
                "adaptive_audio": audio_data.get("adaptive_audio", {}),
                "accessibility_audio": audio_data.get("accessibility_audio", {})
            }

            # Track tokens
            content.tokens_used["audio"] = len(result["text"].split()) * 2

            logger.info("Audio content generated successfully")

        except Exception as e:
            logger.error(f"Audio generation failed: {e}")
            content.errors.append(f"Audio generation error: {str(e)}")

    async def _generate_3d_content(
        self,
        request: GenerationRequest,
        content: GeneratedContent
    ) -> None:
        """Generate 3D asset and environment specifications"""
        try:
            # Determine setting based on subject
            setting = self._determine_setting(request)

            # Generate 3D specifications
            result = await self.asset_generator.ainvoke({
                "subject": request.subject,
                "setting": setting,
                "scale": "medium" if request.max_players <= 20 else "large",
                "performance": "optimized" if "mobile" in request.device_targets else "standard",
                "max_players": request.max_players
            })

            # Parse 3D specifications
            asset_data = self._parse_3d_specs(result["text"])

            content.asset_content = {
                "terrain": asset_data.get("terrain", {}),
                "models": asset_data.get("models", []),
                "optimization": asset_data.get("optimization", {}),
                "zones": asset_data.get("zones", {}),
                "environment": asset_data.get("environment", {})
            }

            # Track tokens
            content.tokens_used["3d"] = len(result["text"].split()) * 2

            logger.info("3D content generated successfully")

        except Exception as e:
            logger.error(f"3D generation failed: {e}")
            content.errors.append(f"3D generation error: {str(e)}")

    def _determine_game_mechanics(self, request: GenerationRequest) -> List[str]:
        """Determine appropriate game mechanics"""
        base_mechanics = ["exploration", "collection", "progression"]

        if request.interactive_elements:
            base_mechanics.extend(["puzzles", "mini-games", "challenges"])

        if request.content_type == "quiz":
            base_mechanics.extend(["questions", "timer", "scoring"])
        elif request.content_type == "simulation":
            base_mechanics.extend(["experimentation", "cause-effect", "sandbox"])
        elif request.content_type == "story":
            base_mechanics.extend(["dialogue", "choices", "branching"])

        return base_mechanics

    def _determine_interactions(self, request: GenerationRequest) -> List[str]:
        """Determine interaction types"""
        interactions = ["click", "touch", "proximity"]

        if request.learning_style == LearningStyle.KINESTHETIC:
            interactions.extend(["drag", "build", "manipulate"])

        if request.max_players > 1:
            interactions.extend(["collaborate", "compete", "trade"])

        return interactions

    def _determine_audio_mood(self, request: GenerationRequest) -> str:
        """Determine audio mood"""
        if "math" in request.subject.lower():
            return "focused and contemplative"
        elif "science" in request.subject.lower():
            return "curious and explorative"
        elif "history" in request.subject.lower():
            return "epic and adventurous"
        elif "language" in request.subject.lower():
            return "creative and expressive"
        else:
            return "upbeat and encouraging"

    def _determine_setting(self, request: GenerationRequest) -> str:
        """Determine 3D environment setting"""
        if "space" in request.subject.lower():
            return "futuristic space station"
        elif "nature" in request.subject.lower() or "biology" in request.subject.lower():
            return "natural outdoor environment"
        elif "history" in request.subject.lower():
            return "historical period setting"
        elif "chemistry" in request.subject.lower() or "physics" in request.subject.lower():
            return "modern laboratory"
        else:
            return "stylized educational campus"

    def _estimate_age_from_grade(self, grade_level: str) -> int:
        """Estimate age from grade level"""
        grade_age_map = {
            "K": 5, "1": 6, "2": 7, "3": 8, "4": 9, "5": 10,
            "6": 11, "7": 12, "8": 13, "9": 14, "10": 15,
            "11": 16, "12": 17
        }

        # Extract grade number
        for grade, age in grade_age_map.items():
            if grade in grade_level:
                return age

        return 10  # Default

    def _parse_lua_scripts(self, text: str) -> Dict[str, str]:
        """Parse Lua scripts from generated text"""
        scripts = {}
        current_script = None
        current_content = []

        lines = text.split('\n')
        for line in lines:
            # Check for script markers
            if "**" in line and "**" in line:
                if current_script and current_content:
                    scripts[current_script] = '\n'.join(current_content)
                    current_content = []

                # Extract script name
                current_script = line.strip('*').strip().replace(' ', '')

            elif current_script and (line.startswith('--') or line.strip().startswith('local') or
                                    line.strip().startswith('function') or line.strip()):
                current_content.append(line)

        # Add last script
        if current_script and current_content:
            scripts[current_script] = '\n'.join(current_content)

        return scripts

    def _extract_dependencies(self, scripts: Dict[str, str]) -> List[str]:
        """Extract Roblox service dependencies from scripts"""
        dependencies = set()

        for script_content in scripts.values():
            # Look for service usage
            if "game:GetService" in script_content:
                lines = script_content.split('\n')
                for line in lines:
                    if "GetService" in line:
                        # Extract service name
                        import_match = line.split('"')
                        if len(import_match) > 1:
                            dependencies.add(import_match[1])

        return list(dependencies)

    def _parse_visual_specs(self, text: str) -> Dict[str, Any]:
        """Parse visual specifications from text"""
        specs = {
            "ui_design": {},
            "color_scheme": {},
            "visual_feedback": {},
            "environmental_design": {},
            "asset_style": {}
        }

        current_section = None

        lines = text.split('\n')
        for line in lines:
            # Detect sections
            if "User Interface" in line or "UI Design" in line:
                current_section = "ui_design"
            elif "Color Scheme" in line:
                current_section = "color_scheme"
            elif "Visual Feedback" in line:
                current_section = "visual_feedback"
            elif "Environmental" in line:
                current_section = "environmental_design"
            elif "Asset Style" in line:
                current_section = "asset_style"

            # Extract hex colors
            if "#" in line and current_section == "color_scheme":
                parts = line.split(":")
                if len(parts) == 2:
                    key = parts[0].strip().lower().replace(" ", "_")
                    value = parts[1].strip()
                    if "#" in value:
                        specs["color_scheme"][key] = value.split()[0]

        return specs

    def _parse_audio_specs(self, text: str) -> Dict[str, Any]:
        """Parse audio specifications from text"""
        specs = {
            "background_music": {},
            "sound_effects": {},
            "narration": {},
            "adaptive_audio": {},
            "accessibility_audio": {}
        }

        # Simple extraction - would be more sophisticated in production
        if "Background Music" in text:
            specs["background_music"] = {
                "style": "educational",
                "intensity_levels": ["calm", "focused", "excited"],
                "loop": True
            }

        if "Sound Effects" in text:
            specs["sound_effects"] = {
                "ui_sounds": ["click", "hover", "success", "error"],
                "game_sounds": ["collect", "achieve", "level_up"],
                "ambient": ["nature", "technology"]
            }

        return specs

    def _parse_3d_specs(self, text: str) -> Dict[str, Any]:
        """Parse 3D specifications from text"""
        specs = {
            "terrain": {},
            "models": [],
            "optimization": {},
            "zones": {},
            "environment": {}
        }

        # Extract terrain materials
        if "Terrain" in text:
            specs["terrain"] = {
                "materials": ["Grass", "Sand", "Rock", "Water"],
                "elevation_range": [-10, 50],
                "water_level": 0
            }

        # Extract model requirements
        if "Models" in text or "3D Models" in text:
            specs["models"] = [
                {"name": "Learning Station", "poly_count": 500},
                {"name": "NPC Character", "poly_count": 1000},
                {"name": "Interactive Object", "poly_count": 300}
            ]

        return specs

    def _extract_text_structure(self, text: str) -> Dict[str, Any]:
        """Extract structured data from unformatted text"""
        return {
            "narrative": text[:500],
            "instructions": ["Follow the path", "Complete challenges", "Learn and explore"],
            "dialogue": {"NPC1": "Welcome!", "NPC2": "Let's learn together!"},
            "ui_text": {"start": "Begin Adventure", "menu": "Main Menu"},
            "feedback": {"success": "Great job!", "error": "Try again!"},
            "achievements": ["First Step", "Quick Learner", "Master"]
        }

    def _calculate_quality_scores(self, content: GeneratedContent) -> Dict[str, float]:
        """Calculate quality scores for generated content"""
        scores = {}

        # Text quality
        if content.text_content:
            text_score = 0.8  # Base score
            if "narrative" in content.text_content:
                text_score += 0.1
            if "dialogue" in content.text_content:
                text_score += 0.1
            scores["text"] = min(1.0, text_score)

        # Code quality
        if content.code_content:
            code_score = 0.7  # Base score
            if "scripts" in content.code_content:
                code_score += 0.15
            if "error_handling" in str(content.code_content):
                code_score += 0.15
            scores["code"] = min(1.0, code_score)

        # Visual quality
        if content.visual_content:
            visual_score = 0.75
            if "color_scheme" in content.visual_content:
                visual_score += 0.25
            scores["visual"] = min(1.0, visual_score)

        # Overall quality
        if scores:
            scores["overall"] = sum(scores.values()) / len(scores)
        else:
            scores["overall"] = 0.0

        return scores

    async def enhance_with_context(
        self,
        content: GeneratedContent,
        context: Dict[str, Any]
    ) -> GeneratedContent:
        """
        Enhance generated content with additional context

        Args:
            content: Previously generated content
            context: Additional context for enhancement

        Returns:
            Enhanced content
        """
        # Add contextual elements
        if "user_progress" in context:
            # Adjust difficulty based on progress
            progress = context["user_progress"]
            if progress < 0.3:
                content.text_content["feedback"]["encouragement"] = "You're doing great! Keep going!"
            elif progress > 0.7:
                content.text_content["feedback"]["challenge"] = "Ready for a bonus challenge?"

        if "previous_errors" in context:
            # Add targeted hints for common errors
            errors = context["previous_errors"]
            content.text_content["hints"] = self._generate_hints_for_errors(errors)

        return content

    def _generate_hints_for_errors(self, errors: List[str]) -> List[str]:
        """Generate hints based on common errors"""
        hints = []

        for error in errors:
            if "calculation" in error.lower():
                hints.append("Remember to check your math step by step")
            elif "concept" in error.lower():
                hints.append("Review the core concept before proceeding")
            elif "instruction" in error.lower():
                hints.append("Read the instructions carefully")

        return hints

    async def _process_task(self, state: Dict[str, Any]) -> Any:
        """Process a multi-modal generation task"""
        # Create generation request
        request = GenerationRequest(
            content_type=state.get("content_type", "lesson"),
            subject=state.get("subject", "general"),
            learning_objectives=state.get("learning_objectives", []),
            grade_level=state.get("grade_level", "5"),
            modalities=state.get("modalities", [ContentModality.TEXT, ContentModality.CODE])
        )

        # Generate content
        content = await self.generate(request)

        return {
            "content_id": content.content_id,
            "status": content.status,
            "text": content.text_content,
            "code": content.code_content,
            "visual": content.visual_content,
            "audio": content.audio_content,
            "assets": content.asset_content,
            "quality_scores": content.quality_scores,
            "generation_time": content.generation_time
        }