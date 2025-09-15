"""
RobloxContentAgent - Educational Content Generation for Roblox Platform

Specialized agent for generating Lua scripts, educational content, and Roblox-specific
components using LangChain and SPARC framework integration.
"""

import asyncio
import json
import logging
from typing import Dict, Any, Optional, List, Union
from datetime import datetime
from dataclasses import dataclass

from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain.tools import Tool
from pydantic import BaseModel, Field

from .base_agent import BaseAgent, AgentConfig, TaskResult, AgentState
from ..sparc.state_manager import StateManager
from ..sparc.context_tracker import ContextTracker
from ..sparc.policy_engine import PolicyEngine
from ..sparc.action_executor import ActionExecutor
from ..sparc.reward_calculator import RewardCalculator

logger = logging.getLogger(__name__)


@dataclass
class RobloxContentSpec:
    """Specification for Roblox content generation"""
    subject: str
    grade_level: int
    learning_objectives: List[str]
    content_type: str  # "script", "terrain", "ui", "game_mechanics"
    difficulty: str = "medium"
    interaction_types: List[str] = None
    duration_minutes: int = 15
    
    def __post_init__(self):
        if self.interaction_types is None:
            self.interaction_types = ["click", "movement", "visual"]


class RobloxScriptResult(BaseModel):
    """Result from Roblox script generation"""
    lua_code: str = Field(description="Generated Lua script code")
    description: str = Field(description="Description of what the script does")
    components: List[str] = Field(description="List of Roblox components/services used")
    installation_steps: List[str] = Field(description="Steps to install the script")
    learning_integration: Dict[str, Any] = Field(description="How this integrates with learning objectives")
    estimated_complexity: str = Field(description="Complexity level: beginner, intermediate, advanced")
    dependencies: List[str] = Field(default_factory=list, description="Required dependencies or assets")
    validation_tests: List[str] = Field(default_factory=list, description="Suggested tests to validate the script")


class RobloxContentAgent(BaseAgent):
    """
    Specialized agent for generating educational Roblox content.
    
    Features:
    - Lua script generation for educational gameplay
    - Integration with SPARC framework for structured reasoning
    - Real-time WebSocket communication
    - Educational content alignment
    - Roblox Studio integration
    """
    
    def __init__(self, config: Optional[AgentConfig] = None):
        if config is None:
            config = AgentConfig(
                name="RobloxContentAgent",
                model="gpt-4",
                temperature=0.3,  # Lower temperature for more consistent code generation
                max_tokens=8192,
                system_prompt=self._create_roblox_system_prompt()
            )
        
        super().__init__(config)
        
        # Initialize SPARC components
        self.state_manager = StateManager("roblox_content")
        self.context_tracker = ContextTracker()
        self.policy_engine = PolicyEngine()
        self.action_executor = ActionExecutor()
        self.reward_calculator = RewardCalculator()
        
        # Initialize tools
        self.tools = self._initialize_roblox_tools()
        
        # Roblox-specific configurations
        self.supported_services = [
            "Workspace", "Players", "RunService", "UserInputService",
            "TweenService", "Lighting", "SoundService", "GuiService",
            "CollectionService", "PathfindingService", "ReplicatedStorage"
        ]
        
        logger.info(f"Initialized {self.name} with SPARC framework")
    
    def _create_roblox_system_prompt(self) -> str:
        """Create specialized system prompt for Roblox content generation"""
        return """You are RobloxContentAgent, an expert in creating educational Roblox experiences.

Your expertise includes:
- Lua scripting for Roblox Studio
- Educational game design principles
- Age-appropriate content creation
- Interactive learning mechanics
- Roblox platform best practices
- Performance optimization for educational games

Core responsibilities:
1. Generate clean, well-commented Lua code
2. Ensure educational alignment with learning objectives
3. Create engaging, interactive experiences
4. Follow Roblox Terms of Service and safety guidelines
5. Optimize for various device types (PC, mobile, tablet)
6. Implement accessibility features where possible

Code generation guidelines:
- Always include comprehensive comments
- Use descriptive variable and function names
- Implement error handling and edge cases
- Structure code for maintainability
- Include logging for debugging
- Follow Lua and Roblox coding standards

Educational integration:
- Align content with specified grade level
- Incorporate multiple learning styles
- Provide clear learning objectives
- Include assessment opportunities
- Design for collaborative learning

Always provide complete, working code with explanations."""
    
    def _initialize_roblox_tools(self) -> List[Tool]:
        """Initialize Roblox-specific tools"""
        return [
            Tool(
                name="validate_lua_syntax",
                func=self._validate_lua_syntax,
                description="Validate Lua code syntax and common errors"
            ),
            Tool(
                name="check_roblox_services",
                func=self._check_roblox_services,
                description="Validate Roblox services and APIs used in code"
            ),
            Tool(
                name="generate_comments",
                func=self._generate_comments,
                description="Generate comprehensive comments for Lua code"
            ),
            Tool(
                name="optimize_performance",
                func=self._optimize_performance,
                description="Analyze and suggest performance optimizations"
            )
        ]
    
    async def _process_task(self, state: AgentState) -> Any:
        """Process Roblox content generation task using SPARC framework"""
        try:
            # Parse task parameters
            task_context = state.get("context", {})
            content_spec = self._parse_content_specification(task_context)
            
            # Update SPARC state
            await self.state_manager.update_state({
                "current_task": state["task"],
                "content_spec": content_spec.__dict__,
                "timestamp": datetime.now().isoformat(),
                "status": "processing"
            })
            
            # Determine action using policy engine
            policy_decision = await self.policy_engine.decide_action(
                current_state=await self.state_manager.get_current_state(),
                context=task_context
            )
            
            # Execute content generation
            result = await self._generate_roblox_content(content_spec, policy_decision)
            
            # Calculate reward for learning outcomes
            reward = await self.reward_calculator.calculate_educational_reward(
                content_spec=content_spec,
                generated_content=result,
                learning_objectives=content_spec.learning_objectives
            )
            
            # Update context tracker
            await self.context_tracker.update_context({
                "generation_successful": True,
                "content_type": content_spec.content_type,
                "reward_score": reward,
                "complexity": result.estimated_complexity
            })
            
            return result
            
        except Exception as e:
            logger.error(f"Error in Roblox content generation: {e}")
            await self.state_manager.update_state({"status": "error", "error": str(e)})
            raise
    
    def _parse_content_specification(self, context: Dict[str, Any]) -> RobloxContentSpec:
        """Parse content specification from task context"""
        return RobloxContentSpec(
            subject=context.get("subject", "General"),
            grade_level=context.get("grade_level", 5),
            learning_objectives=context.get("learning_objectives", ["Engage with content"]),
            content_type=context.get("content_type", "script"),
            difficulty=context.get("difficulty", "medium"),
            interaction_types=context.get("interaction_types", ["click", "movement", "visual"]),
            duration_minutes=context.get("duration_minutes", 15)
        )
    
    async def _generate_roblox_content(self, spec: RobloxContentSpec, policy_decision: Dict[str, Any]) -> RobloxScriptResult:
        """Generate Roblox content based on specification"""
        # Create context-aware prompt
        prompt = self._create_generation_prompt(spec, policy_decision)
        
        # Generate content using LLM
        messages = [
            SystemMessage(content=self.config.system_prompt),
            HumanMessage(content=prompt)
        ]
        
        response = await self.llm.ainvoke(messages)
        
        # Parse and structure the response
        result = await self._parse_generation_response(response.content, spec)
        
        # Validate and enhance the result
        enhanced_result = await self._enhance_and_validate_result(result, spec)
        
        return enhanced_result
    
    def _create_generation_prompt(self, spec: RobloxContentSpec, policy_decision: Dict[str, Any]) -> str:
        """Create a detailed prompt for content generation"""
        return f"""Generate educational Roblox {spec.content_type} for:

Subject: {spec.subject}
Grade Level: {spec.grade_level}
Learning Objectives: {', '.join(spec.learning_objectives)}
Difficulty: {spec.difficulty}
Duration: {spec.duration_minutes} minutes
Interaction Types: {', '.join(spec.interaction_types)}

Policy Decision Context:
{json.dumps(policy_decision, indent=2)}

Requirements:
1. Create complete, working Lua code for Roblox Studio
2. Include comprehensive comments explaining each section
3. Align with educational objectives for grade level {spec.grade_level}
4. Implement {', '.join(spec.interaction_types)} interactions
5. Include error handling and edge cases
6. Provide installation and setup instructions
7. Suggest validation tests

Structure your response as a JSON object with the following fields:
- lua_code: The complete Lua script
- description: Detailed description of functionality
- components: List of Roblox services/components used
- installation_steps: Step-by-step installation guide
- learning_integration: How this supports learning objectives
- estimated_complexity: beginner/intermediate/advanced
- dependencies: Required assets or additional scripts
- validation_tests: Suggested tests to verify functionality

Ensure the code is production-ready and educationally valuable."""
    
    async def _parse_generation_response(self, response: str, spec: RobloxContentSpec) -> RobloxScriptResult:
        """Parse LLM response into structured result"""
        try:
            # Try to parse as JSON first
            if response.strip().startswith('{'):
                data = json.loads(response)
                return RobloxScriptResult(**data)
            
            # If not JSON, extract code and create structured response
            lua_code = self._extract_lua_code(response)
            
            return RobloxScriptResult(
                lua_code=lua_code,
                description=f"Generated {spec.content_type} for {spec.subject} education",
                components=self._extract_roblox_components(lua_code),
                installation_steps=[
                    "Open Roblox Studio",
                    "Create new ServerScript or LocalScript",
                    "Copy and paste the provided code",
                    "Configure any dependencies",
                    "Test in Studio"
                ],
                learning_integration={
                    "objectives": spec.learning_objectives,
                    "alignment": "Code implements interactive learning mechanics"
                },
                estimated_complexity="intermediate",
                dependencies=[],
                validation_tests=[
                    "Test script execution without errors",
                    "Verify educational interactions work as expected",
                    "Check performance on different devices"
                ]
            )
        
        except Exception as e:
            logger.error(f"Error parsing generation response: {e}")
            # Fallback to basic parsing
            return self._create_fallback_result(response, spec)
    
    def _extract_lua_code(self, text: str) -> str:
        """Extract Lua code from text response"""
        # Look for code blocks
        import re
        
        # Try to find code between ```lua and ```
        lua_pattern = r'```lua\s*\n(.*?)\n```'
        match = re.search(lua_pattern, text, re.DOTALL)
        if match:
            return match.group(1).strip()
        
        # Try to find code between ``` and ```
        code_pattern = r'```\s*\n(.*?)\n```'
        match = re.search(code_pattern, text, re.DOTALL)
        if match:
            return match.group(1).strip()
        
        # If no code blocks found, return the text as-is
        return text.strip()
    
    def _extract_roblox_components(self, lua_code: str) -> List[str]:
        """Extract Roblox services and components from code"""
        components = []
        for service in self.supported_services:
            if service in lua_code:
                components.append(service)
        return components
    
    def _create_fallback_result(self, response: str, spec: RobloxContentSpec) -> RobloxScriptResult:
        """Create fallback result when parsing fails"""
        return RobloxScriptResult(
            lua_code=self._extract_lua_code(response),
            description=f"Educational {spec.content_type} for {spec.subject}",
            components=["Workspace"],
            installation_steps=[
                "Open Roblox Studio",
                "Insert script and paste code",
                "Test functionality"
            ],
            learning_integration={
                "objectives": spec.learning_objectives,
                "grade_level": spec.grade_level
            },
            estimated_complexity="intermediate"
        )
    
    async def _enhance_and_validate_result(self, result: RobloxScriptResult, spec: RobloxContentSpec) -> RobloxScriptResult:
        """Enhance and validate the generated result"""
        # Validate Lua syntax
        syntax_valid = await self._validate_lua_syntax(result.lua_code)
        if not syntax_valid:
            logger.warning("Generated Lua code has syntax issues")
        
        # Check Roblox services usage
        service_validation = await self._check_roblox_services(result.lua_code)
        
        # Generate additional comments if needed
        if result.lua_code and len(result.lua_code.split('\n')) > 20:
            enhanced_code = await self._generate_comments(result.lua_code)
            if enhanced_code != result.lua_code:
                result.lua_code = enhanced_code
        
        # Add performance suggestions
        performance_notes = await self._optimize_performance(result.lua_code)
        if performance_notes:
            result.validation_tests.extend(performance_notes)
        
        return result
    
    # Tool implementations
    def _validate_lua_syntax(self, code: str) -> bool:
        """Basic Lua syntax validation"""
        try:
            # Basic checks for common Lua syntax patterns
            lines = code.split('\n')
            
            # Check for balanced parentheses, brackets, and braces
            parens = brackets = braces = 0
            
            for line in lines:
                # Skip comments
                if '--' in line:
                    line = line[:line.find('--')]
                
                parens += line.count('(') - line.count(')')
                brackets += line.count('[') - line.count(']')
                braces += line.count('{') - line.count('}')
            
            return parens == 0 and brackets == 0 and braces == 0
        
        except Exception:
            return False
    
    def _check_roblox_services(self, code: str) -> Dict[str, Any]:
        """Validate Roblox services and APIs"""
        used_services = []
        for service in self.supported_services:
            if service in code:
                used_services.append(service)
        
        return {
            "valid_services": used_services,
            "total_services": len(used_services),
            "coverage_score": min(len(used_services) / 3, 1.0)  # Up to 3 services is good
        }
    
    def _generate_comments(self, code: str) -> str:
        """Add comprehensive comments to Lua code"""
        # This is a simplified implementation
        # In production, you might use an LLM to generate better comments
        lines = code.split('\n')
        commented_lines = []
        
        for i, line in enumerate(lines):
            commented_lines.append(line)
            
            # Add comments for key patterns
            if 'function' in line and '--' not in line:
                commented_lines.insert(-1, '-- Function definition: ' + line.strip())
            elif 'game:GetService' in line and '--' not in line:
                commented_lines.insert(-1, '-- Getting Roblox service')
        
        return '\n'.join(commented_lines)
    
    def _optimize_performance(self, code: str) -> List[str]:
        """Analyze code for performance optimization opportunities"""
        suggestions = []
        
        if 'while true' in code:
            suggestions.append("Consider using RunService.Heartbeat for game loops")
        
        if code.count('wait()') > 3:
            suggestions.append("Multiple wait() calls detected - consider using coroutines")
        
        if 'FindFirstChild' in code and 'WaitForChild' not in code:
            suggestions.append("Use WaitForChild() for reliability in loading scenarios")
        
        return suggestions
    
    async def generate_educational_script(self, 
                                        subject: str,
                                        grade_level: int,
                                        learning_objectives: List[str],
                                        script_type: str = "interactive") -> TaskResult:
        """Generate educational Roblox script"""
        context = {
            "subject": subject,
            "grade_level": grade_level,
            "learning_objectives": learning_objectives,
            "content_type": "script",
            "script_type": script_type,
            "duration_minutes": 20
        }
        
        return await self.execute(f"Generate educational {script_type} script for {subject}", context)
    
    async def create_learning_environment(self,
                                        theme: str,
                                        grade_level: int,
                                        interactive_elements: List[str]) -> TaskResult:
        """Create an educational environment in Roblox"""
        context = {
            "subject": theme,
            "grade_level": grade_level,
            "content_type": "environment",
            "learning_objectives": [f"Explore {theme} concepts", "Interactive learning"],
            "interaction_types": interactive_elements,
            "duration_minutes": 30
        }
        
        return await self.execute(f"Create educational environment for {theme}", context)
    
    async def optimize_for_mobile(self, existing_script: str) -> TaskResult:
        """Optimize existing script for mobile devices"""
        context = {
            "content_type": "optimization",
            "target_platform": "mobile",
            "existing_code": existing_script,
            "optimization_type": "mobile_performance"
        }
        
        return await self.execute("Optimize script for mobile devices", context)
    
    def get_roblox_status(self) -> Dict[str, Any]:
        """Get Roblox agent-specific status"""
        base_status = self.get_status()
        base_status.update({
            "supported_services": len(self.supported_services),
            "sparc_components": {
                "state_manager": "active" if self.state_manager else "inactive",
                "context_tracker": "active" if self.context_tracker else "inactive",
                "policy_engine": "active" if self.policy_engine else "inactive"
            },
            "specialization": "roblox_content_generation"
        })
        return base_status


# WebSocket integration for real-time content generation
class RobloxWebSocketHandler:
    """Handle WebSocket communication for Roblox content generation"""
    
    def __init__(self, agent: RobloxContentAgent):
        self.agent = agent
        self.active_sessions = {}
    
    async def handle_content_request(self, websocket, message: Dict[str, Any]):
        """Handle real-time content generation request"""
        try:
            session_id = message.get("session_id")
            request_type = message.get("type", "generate_script")
            
            # Send acknowledgment
            await websocket.send_json({
                "type": "request_received",
                "session_id": session_id,
                "status": "processing"
            })
            
            # Process request based on type
            if request_type == "generate_script":
                result = await self._handle_script_generation(websocket, message)
            elif request_type == "create_environment":
                result = await self._handle_environment_creation(websocket, message)
            elif request_type == "optimize_mobile":
                result = await self._handle_mobile_optimization(websocket, message)
            else:
                raise ValueError(f"Unknown request type: {request_type}")
            
            # Send final result
            await websocket.send_json({
                "type": "generation_complete",
                "session_id": session_id,
                "result": result.output if isinstance(result.output, dict) else result.output.__dict__,
                "success": result.success,
                "execution_time": result.execution_time
            })
            
        except Exception as e:
            logger.error(f"WebSocket handler error: {e}")
            await websocket.send_json({
                "type": "error",
                "session_id": message.get("session_id"),
                "error": str(e)
            })
    
    async def _handle_script_generation(self, websocket, message: Dict[str, Any]) -> TaskResult:
        """Handle script generation request"""
        params = message.get("parameters", {})
        
        # Send progress updates
        await websocket.send_json({
            "type": "progress",
            "session_id": message.get("session_id"),
            "stage": "analyzing_requirements",
            "progress": 25
        })
        
        result = await self.agent.generate_educational_script(
            subject=params.get("subject", "General"),
            grade_level=params.get("grade_level", 5),
            learning_objectives=params.get("learning_objectives", ["Learn through play"]),
            script_type=params.get("script_type", "interactive")
        )
        
        await websocket.send_json({
            "type": "progress",
            "session_id": message.get("session_id"),
            "stage": "generation_complete",
            "progress": 100
        })
        
        return result
    
    async def _handle_environment_creation(self, websocket, message: Dict[str, Any]) -> TaskResult:
        """Handle environment creation request"""
        params = message.get("parameters", {})
        
        await websocket.send_json({
            "type": "progress",
            "session_id": message.get("session_id"),
            "stage": "designing_environment",
            "progress": 30
        })
        
        result = await self.agent.create_learning_environment(
            theme=params.get("theme", "Science Lab"),
            grade_level=params.get("grade_level", 5),
            interactive_elements=params.get("interactive_elements", ["click", "movement"])
        )
        
        return result
    
    async def _handle_mobile_optimization(self, websocket, message: Dict[str, Any]) -> TaskResult:
        """Handle mobile optimization request"""
        params = message.get("parameters", {})
        existing_script = params.get("existing_script", "")
        
        if not existing_script:
            raise ValueError("Existing script required for optimization")
        
        await websocket.send_json({
            "type": "progress",
            "session_id": message.get("session_id"),
            "stage": "optimizing_for_mobile",
            "progress": 50
        })
        
        result = await self.agent.optimize_for_mobile(existing_script)
        
        return result


# Export main classes
__all__ = [
    'RobloxContentAgent',
    'RobloxContentSpec',
    'RobloxScriptResult',
    'RobloxWebSocketHandler'
]
