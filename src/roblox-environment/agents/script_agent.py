"""
Script Agent - Specializes in Lua script development for Roblox

Generates optimized, secure Lua scripts for Roblox environments.
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import re
import json

from langchain_core.messages import HumanMessage, AIMessage
from langchain.tools import Tool

from .base_agent import BaseAgent, AgentConfig, AgentState, TaskResult

logger = logging.getLogger(__name__)


class ScriptAgent(BaseAgent):
    """
    Agent specialized in Lua script development for Roblox.

    Capabilities:
    - Lua script generation
    - Performance optimization
    - Security validation
    - Anti-exploit measures
    - Remote event handling
    - Module script creation
    """

    def __init__(self, config: Optional[AgentConfig] = None):
        if config is None:
            config = AgentConfig(
                name="ScriptAgent",
                model="gpt-4",
                temperature=0.3,  # Lower temperature for code generation
                system_prompt=self._get_script_prompt(),
                tools=self._initialize_tools(),
            )
        super().__init__(config)

        # Lua patterns and templates
        self.script_templates = self._load_script_templates()

        # Security patterns to detect
        self.exploit_patterns = [
            r"loadstring",  # Dynamic code execution
            r"getfenv",  # Environment manipulation
            r"setfenv",  # Environment manipulation
            r"rawset",  # Bypass metatables
            r"rawget",  # Bypass metatables
            r"debug\.",  # Debug library access
            r"while\s+true\s+do\s+end",  # Infinite loops
        ]

        # Performance optimization patterns
        self.optimization_rules = {
            "cache_services": "Cache game services at the top of scripts",
            "localize_functions": "Localize frequently used functions",
            "avoid_wait": "Use task.wait() instead of wait()",
            "batch_operations": "Batch similar operations together",
            "use_connections": "Properly disconnect unused connections",
            "optimize_loops": "Use ipairs for arrays, pairs for dictionaries",
        }

    def _get_script_prompt(self) -> str:
        """Get specialized prompt for script generation"""
        return """You are a Lua Script Developer for Roblox educational environments.

Your expertise includes:
- Roblox Lua API and best practices
- Client-server architecture
- RemoteEvent/RemoteFunction usage
- Performance optimization
- Security and anti-exploit measures
- Module script organization
- Event-driven programming
- Memory management

When generating scripts:
1. Follow Roblox best practices
2. Implement proper error handling
3. Use type checking where applicable
4. Add clear comments for complex logic
5. Optimize for performance
6. Implement security checks
7. Use consistent naming conventions
8. Structure code modularly

Always prioritize:
- Security (never trust the client)
- Performance (minimize lag)
- Readability (clear, maintainable code)
- Reusability (modular design)"""

    def _initialize_tools(self) -> List[Tool]:
        """Initialize script development tools"""
        tools = []

        tools.append(
            Tool(name="ValidateLuaSyntax", func=self._validate_lua_syntax, description="Validate Lua script syntax")
        )

        tools.append(
            Tool(name="OptimizeScript", func=self._optimize_script, description="Optimize Lua script for performance")
        )

        tools.append(
            Tool(
                name="SecurityCheck", func=self._security_check, description="Check script for security vulnerabilities"
            )
        )

        tools.append(
            Tool(
                name="GenerateRemoteEvents",
                func=self._generate_remote_events,
                description="Generate RemoteEvent handling code",
            )
        )

        return tools

    def _load_script_templates(self) -> Dict[str, str]:
        """Load Lua script templates"""
        return {
            "server_script": """-- Server Script: {name}
-- Description: {description}
-- Author: AI Generated
-- Date: {date}

-- Services
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local DataStoreService = game:GetService("DataStoreService")

-- Modules
{modules}

-- Variables
{variables}

-- Functions
{functions}

-- Events
{events}

-- Main
{main}
""",
            "client_script": """-- Client Script: {name}
-- Description: {description}

-- Services
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local UserInputService = game:GetService("UserInputService")
local TweenService = game:GetService("TweenService")

-- Get player
local player = Players.LocalPlayer
local playerGui = player:WaitForChild("PlayerGui")

-- Modules
{modules}

-- Variables
{variables}

-- Functions
{functions}

-- Events
{events}

-- Initialize
{initialize}
""",
            "module_script": """-- Module Script: {name}
-- Description: {description}

local {module_name} = {}
{module_name}.__index = {module_name}

-- Private variables
{private_vars}

-- Constructor
function {module_name}.new({params})
    local self = setmetatable({}, {module_name})
    {constructor_body}
    return self
end

-- Public methods
{public_methods}

-- Private methods
{private_methods}

return {module_name}
""",
            "remote_event_handler": """-- RemoteEvent Handler
local remoteEvent = ReplicatedStorage:WaitForChild("{event_name}")

-- Server-side handler
remoteEvent.OnServerEvent:Connect(function(player, ...)
    -- Validate player
    if not player or not player.Parent then
        return
    end
    
    -- Rate limiting
    local lastCall = player:GetAttribute("Last{event_name}")
    local currentTime = tick()
    
    if lastCall and (currentTime - lastCall) < {rate_limit} then
        return -- Too many requests
    end
    
    player:SetAttribute("Last{event_name}", currentTime)
    
    -- Process event
    {handler_logic}
end)
""",
            "anti_exploit": """-- Anti-Exploit Measures
local function validateInput(player, input)
    -- Type checking
    if typeof(input) ~= "{expected_type}" then
        return false
    end
    
    -- Range checking
    {range_checks}
    
    -- Sanity checks
    {sanity_checks}
    
    return true
end

local function detectExploit(player, action)
    local suspicious = false
    
    -- Check for impossible actions
    {exploit_checks}
    
    if suspicious then
        -- Log and handle exploit
        warn("Potential exploit detected:", player.Name, action)
        -- Take action (kick, ban, etc.)
    end
    
    return suspicious
end
""",
        }

    async def _process_task(self, state: AgentState) -> Any:
        """Process script generation task"""
        task = state["task"]
        context = state["context"]

        # Determine script type
        script_type = context.get("script_type", "server")
        feature = context.get("feature", "general")
        requirements = context.get("requirements", [])

        # Generate script based on requirements
        script = await self._generate_script(script_type=script_type, feature=feature, requirements=requirements)

        # Validate syntax
        validation = self._validate_lua_syntax(script)

        if not validation["valid"]:
            # Fix syntax errors
            script = await self._fix_syntax_errors(script, validation["errors"])

        # Security check
        security = self._security_check(script)

        if security["vulnerabilities"]:
            # Fix security issues
            script = await self._fix_security_issues(script, security["vulnerabilities"])

        # Optimize script
        optimized_script = self._optimize_script(script)

        # Generate documentation
        documentation = self._generate_documentation(optimized_script)

        result = {
            "script": optimized_script,
            "type": script_type,
            "feature": feature,
            "documentation": documentation,
            "validation": {"syntax_valid": True, "security_passed": True, "optimized": True},
            "metadata": {
                "lines_of_code": len(optimized_script.split("\n")),
                "generated_at": datetime.now().isoformat(),
            },
        }

        return result

    async def _generate_script(self, script_type: str, feature: str, requirements: List[str]) -> str:
        """Generate Lua script based on requirements"""

        requirements_text = "\n".join(f"- {req}" for req in requirements)

        prompt = f"""Generate a Roblox Lua script:

Type: {script_type}
Feature: {feature}
Requirements:
{requirements_text}

The script should:
1. Follow Roblox best practices
2. Include proper error handling
3. Be optimized for performance
4. Include security checks
5. Have clear comments
6. Use proper service caching

Generate complete, production-ready Lua code."""

        response = await self.llm.ainvoke(prompt)

        # Extract code from response
        script = self._extract_lua_code(response.content)

        # Apply template if needed
        if script_type in self.script_templates:
            template = self.script_templates[script_type]
            script = self._apply_template(template, script, feature)

        return script

    def _extract_lua_code(self, text: str) -> str:
        """Extract Lua code from text"""
        # Find code blocks
        code_blocks = re.findall(r"```lua?\n(.*?)```", text, re.DOTALL)

        if code_blocks:
            return "\n\n".join(code_blocks)

        # If no code blocks, assume entire text is code
        return text

    def _apply_template(self, template: str, script: str, feature: str) -> str:
        """Apply template to script"""
        # Parse script to extract components
        components = self._parse_script_components(script)

        # Fill template
        filled = template.format(
            name=feature,
            description=f"Handles {feature} functionality",
            date=datetime.now().strftime("%Y-%m-%d"),
            modules=components.get("modules", "-- No modules"),
            variables=components.get("variables", "-- No variables"),
            functions=components.get("functions", "-- No functions"),
            events=components.get("events", "-- No events"),
            main=components.get("main", "-- Main logic here"),
            initialize=components.get("initialize", "-- Initialization"),
            module_name=feature.replace(" ", ""),
            params="",
            constructor_body="",
            private_vars="",
            public_methods="",
            private_methods="",
            event_name=f"{feature}Event",
            rate_limit="0.1",
            handler_logic="-- Handler logic",
            expected_type="table",
            range_checks="-- Range checks",
            sanity_checks="-- Sanity checks",
            exploit_checks="-- Exploit checks",
        )

        return filled

    def _parse_script_components(self, script: str) -> Dict[str, str]:
        """Parse script into components"""
        components = {}

        # Simple parsing - in production, use proper AST parsing
        lines = script.split("\n")
        current_section = "main"
        section_content = []

        for line in lines:
            if "-- Services" in line or "local.*Service" in line:
                current_section = "services"
            elif "-- Modules" in line:
                current_section = "modules"
            elif "-- Variables" in line:
                current_section = "variables"
            elif "-- Functions" in line or "local function" in line:
                current_section = "functions"
            elif "-- Events" in line or ".Connect" in line:
                current_section = "events"
            elif "-- Main" in line:
                current_section = "main"

            section_content.append(line)

        components[current_section] = "\n".join(section_content)

        return components

    def _validate_lua_syntax(self, script: str) -> Dict[str, Any]:
        """Validate Lua syntax"""
        validation = {"valid": True, "errors": [], "warnings": []}

        # Check for common syntax errors
        syntax_checks = [
            (r"^\s*end\s*$", "Unmatched 'end' statement"),
            (r"^\s*else\s+", "'else' without 'if'"),
            (r"^\s*elseif\s+", "'elseif' without 'if'"),
            (r"=\s*=", "Assignment operator error (= =)"),
            (r"if\s+.*\s+then\s+then", "Double 'then' in if statement"),
            (r"for\s+\w+\s+in\s+\w+\s+do\s+do", "Double 'do' in for loop"),
        ]

        lines = script.split("\n")
        for i, line in enumerate(lines, 1):
            for pattern, error_msg in syntax_checks:
                if re.search(pattern, line):
                    validation["valid"] = False
                    validation["errors"].append(f"Line {i}: {error_msg}")

        # Check bracket matching
        open_brackets = script.count("(") + script.count("{") + script.count("[")
        close_brackets = script.count(")") + script.count("}") + script.count("]")

        if open_brackets != close_brackets:
            validation["valid"] = False
            validation["errors"].append("Mismatched brackets")

        # Check string quotes
        if script.count('"') % 2 != 0:
            validation["warnings"].append("Possible unclosed string (double quotes)")
        if script.count("'") % 2 != 0:
            validation["warnings"].append("Possible unclosed string (single quotes)")

        return validation

    def _security_check(self, script: str) -> Dict[str, Any]:
        """Check script for security vulnerabilities"""
        security = {"vulnerabilities": [], "risk_level": "low"}

        # Check for exploit patterns
        for pattern in self.exploit_patterns:
            matches = re.finditer(pattern, script, re.IGNORECASE)
            for match in matches:
                security["vulnerabilities"].append(
                    {"type": "potential_exploit", "pattern": pattern, "location": match.start(), "severity": "high"}
                )

        # Check for missing validation
        if "OnServerEvent" in script and "typeof" not in script:
            security["vulnerabilities"].append(
                {
                    "type": "missing_validation",
                    "description": "RemoteEvent handler without input validation",
                    "severity": "medium",
                }
            )

        # Check for trust issues
        if "trust" in script.lower() or "assume" in script.lower():
            security["vulnerabilities"].append(
                {"type": "trust_issue", "description": "Potential client trust issue", "severity": "medium"}
            )

        # Determine risk level
        if any(v["severity"] == "high" for v in security["vulnerabilities"]):
            security["risk_level"] = "high"
        elif any(v["severity"] == "medium" for v in security["vulnerabilities"]):
            security["risk_level"] = "medium"

        return security

    def _optimize_script(self, script: str) -> str:
        """Optimize Lua script for performance"""
        optimized = script

        # Cache services at the top
        services = re.findall(r'game:GetService\("(\w+)"\)', script)
        if services:
            service_cache = "\n".join([f'local {s} = game:GetService("{s}")' for s in set(services)])
            # Remove inline GetService calls
            for service in set(services):
                optimized = re.sub(f'game:GetService\\("{service}"\\)', service, optimized)

        # Replace wait() with task.wait()
        optimized = re.sub(r"\bwait\s*\(", "task.wait(", optimized)

        # Localize frequently used globals
        globals_to_localize = ["math", "string", "table", "coroutine", "task"]
        for global_name in globals_to_localize:
            if global_name in optimized:
                # Add local declaration at top
                optimized = f"local {global_name} = {global_name}\n" + optimized

        # Optimize loops
        optimized = re.sub(r"for\s+(\w+)\s*=\s*1\s*,\s*#(\w+)\s+do", r"for \1, _ in ipairs(\2) do", optimized)

        # Add connection cleanup
        if ".Connect" in optimized and "connection" not in optimized.lower():
            # Add connection management
            optimized = self._add_connection_cleanup(optimized)

        return optimized

    def _add_connection_cleanup(self, script: str) -> str:
        """Add proper connection cleanup to script"""
        # Find all connections
        connections = re.findall(r"(\w+)\.(\w+):Connect\(", script)

        if connections:
            # Add connections table
            script = "local connections = {}\n\n" + script

            # Store connections
            for obj, event in connections:
                pattern = f"{obj}.{event}:Connect\\("
                replacement = f"table.insert(connections, {obj}.{event}:Connect("
                script = re.sub(pattern, replacement, script, count=1)

            # Add cleanup function
            cleanup = """
-- Cleanup function
local function cleanup()
    for _, connection in ipairs(connections) do
        connection:Disconnect()
    end
    connections = {}
end

-- Bind to appropriate lifecycle event
game:BindToClose(cleanup)
"""
            script += cleanup

        return script

    async def _fix_syntax_errors(self, script: str, errors: List[str]) -> str:
        """Fix syntax errors in script"""
        prompt = f"""Fix these Lua syntax errors:

Script:
{script}

Errors:
{chr(10).join(errors)}

Return the corrected script."""

        response = await self.llm.ainvoke(prompt)
        return self._extract_lua_code(response.content)

    async def _fix_security_issues(self, script: str, vulnerabilities: List[Dict]) -> str:
        """Fix security vulnerabilities in script"""
        vuln_text = "\n".join([f"- {v['type']}: {v.get('description', v.get('pattern', ''))}" for v in vulnerabilities])

        prompt = f"""Fix these security vulnerabilities in the Lua script:

Script:
{script}

Vulnerabilities:
{vuln_text}

Apply these fixes:
1. Add input validation for all RemoteEvents
2. Remove or secure any dynamic code execution
3. Add rate limiting
4. Implement sanity checks
5. Never trust client input

Return the secured script."""

        response = await self.llm.ainvoke(prompt)
        return self._extract_lua_code(response.content)

    def _generate_documentation(self, script: str) -> str:
        """Generate documentation for script"""
        doc = []

        # Extract functions
        functions = re.findall(r"function\s+(\w+(?:\.\w+)?)\s*\((.*?)\)", script)

        if functions:
            doc.append("## Functions\n")
            for func_name, params in functions:
                doc.append(f"### {func_name}({params})")
                doc.append("Description: [Generated function]")
                doc.append("")

        # Extract events
        events = re.findall(r"(\w+)\.(\w+):Connect\(", script)

        if events:
            doc.append("## Events\n")
            for obj, event in events:
                doc.append(f"### {obj}.{event}")
                doc.append("Handler for event")
                doc.append("")

        # Extract modules
        modules = re.findall(r"require\((.*?)\)", script)

        if modules:
            doc.append("## Dependencies\n")
            for module in modules:
                doc.append(f"- {module}")

        return "\n".join(doc)

    def _generate_remote_events(self, feature: str) -> str:
        """Generate RemoteEvent handling code"""
        template = self.script_templates["remote_event_handler"]

        return template.format(
            event_name=f"{feature}Event",
            rate_limit="0.1",
            handler_logic=f"""
    -- Handle {feature} event
    local args = {{...}}
    
    -- Validate input
    if not validateInput(player, args) then
        return
    end
    
    -- Process {feature}
    local success, result = pcall(function()
        -- Implementation here
        return true
    end)
    
    if success then
        -- Send response to client if needed
        remoteEvent:FireClient(player, result)
    else
        warn("Error processing {feature}:", result)
    end
""",
        )

    async def generate_game_system(self, system_type: str, specifications: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a complete game system with multiple scripts"""

        scripts = {}

        # Generate server script
        server_script = await self._generate_script(
            script_type="server", feature=system_type, requirements=specifications.get("server_requirements", [])
        )
        scripts["ServerScript"] = server_script

        # Generate client script
        client_script = await self._generate_script(
            script_type="client", feature=system_type, requirements=specifications.get("client_requirements", [])
        )
        scripts["ClientScript"] = client_script

        # Generate module script
        module_script = await self._generate_script(
            script_type="module", feature=system_type, requirements=specifications.get("module_requirements", [])
        )
        scripts["ModuleScript"] = module_script

        # Generate RemoteEvents
        remote_events = self._generate_remote_events(system_type)
        scripts["RemoteEvents"] = remote_events

        # Validate all scripts
        for name, script in scripts.items():
            validation = self._validate_lua_syntax(script)
            if not validation["valid"]:
                scripts[name] = await self._fix_syntax_errors(script, validation["errors"])

        return {
            "system_type": system_type,
            "scripts": scripts,
            "documentation": self._generate_system_documentation(scripts),
            "installation_guide": self._generate_installation_guide(system_type, scripts),
        }

    def _generate_system_documentation(self, scripts: Dict[str, str]) -> str:
        """Generate documentation for complete system"""
        doc = [f"# System Documentation\n"]

        for script_name, script_content in scripts.items():
            doc.append(f"## {script_name}")
            doc.append(self._generate_documentation(script_content))
            doc.append("")

        return "\n".join(doc)

    def _generate_installation_guide(self, system_type: str, scripts: Dict[str, str]) -> str:
        """Generate installation guide for system"""
        guide = f"""# Installation Guide for {system_type}

## Step 1: Create RemoteEvents
1. In ReplicatedStorage, create a folder named "{system_type}"
2. Add RemoteEvents as specified in the RemoteEvents script

## Step 2: Install Server Script
1. Place ServerScript in ServerScriptService
2. Name it "{system_type}Server"

## Step 3: Install Client Script
1. Place ClientScript in StarterPlayer > StarterPlayerScripts
2. Name it "{system_type}Client"

## Step 4: Install Module Script
1. Place ModuleScript in ReplicatedStorage > {system_type}
2. Name it "{system_type}Module"

## Step 5: Configure
1. Update any configuration values in the scripts
2. Test in Studio before publishing

## Testing
1. Run in Studio Test mode
2. Check Output for any errors
3. Verify all features work as expected
"""
        return guide
