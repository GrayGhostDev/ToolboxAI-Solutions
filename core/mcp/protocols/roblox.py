"""
Roblox-specific MCP Protocol Handlers

Handles Roblox Studio communication and context management.
"""

import json
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional

logger = logging.getLogger(__name__)


@dataclass
class RobloxContext:
    """Roblox-specific context information"""

    place_id: Optional[str]
    game_name: Optional[str]
    scripts: list[dict[str, str]]
    terrain_data: Optional[dict]
    ui_elements: list[dict]
    active_plugins: list[str]
    studio_version: Optional[str]


class RobloxProtocol:
    """
    Protocol handler for Roblox Studio integration.

    Manages:
    - Script generation context
    - Terrain configuration
    - UI element tracking
    - Plugin communication
    """

    def __init__(self):
        self.current_context = RobloxContext(
            place_id=None,
            game_name=None,
            scripts=[],
            terrain_data=None,
            ui_elements=[],
            active_plugins=[],
            studio_version=None,
        )
        self.script_history = []
        self.generation_cache = {}

    def process_studio_message(self, message: dict[str, Any]) -> dict[str, Any]:
        """Process incoming message from Roblox Studio"""
        message_type = message.get("type")

        handlers = {
            "studio_init": self._handle_studio_init,
            "script_request": self._handle_script_request,
            "terrain_request": self._handle_terrain_request,
            "ui_request": self._handle_ui_request,
            "context_update": self._handle_context_update,
            "error_report": self._handle_error_report,
            "plugin_register": self._handle_plugin_register,
        }

        handler = handlers.get(message_type)
        if handler:
            return handler(message)
        else:
            logger.warning(f"Unknown Roblox message type: {message_type}")
            return {"error": f"Unknown message type: {message_type}"}

    def _handle_studio_init(self, message: dict) -> dict:
        """Handle Roblox Studio initialization"""
        self.current_context.studio_version = message.get("studio_version")
        self.current_context.place_id = message.get("place_id")
        self.current_context.game_name = message.get("game_name")

        logger.info(f"Roblox Studio initialized: {self.current_context.game_name}")

        return {
            "type": "studio_init_response",
            "status": "connected",
            "capabilities": self.get_capabilities(),
        }

    def _handle_script_request(self, message: dict) -> dict:
        """Handle script generation request"""
        script_type = message.get("script_type", "ServerScript")
        purpose = message.get("purpose")
        requirements = message.get("requirements", {})

        # Generate cache key
        cache_key = f"{script_type}_{purpose}_{json.dumps(requirements, sort_keys=True)}"

        # Check cache
        if cache_key in self.generation_cache:
            logger.info(f"Returning cached script for: {purpose}")
            return self.generation_cache[cache_key]

        # Generate script based on type
        script_content = self._generate_script(script_type, purpose, requirements)

        # Store in context and history
        script_data = {
            "type": script_type,
            "purpose": purpose,
            "content": script_content,
            "timestamp": datetime.now().isoformat(),
        }

        self.current_context.scripts.append(script_data)
        self.script_history.append(script_data)

        response = {
            "type": "script_response",
            "script": script_content,
            "script_type": script_type,
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "purpose": purpose,
            },
        }

        # Cache response
        self.generation_cache[cache_key] = response

        return response

    def _handle_terrain_request(self, message: dict) -> dict:
        """Handle terrain generation request"""
        terrain_type = message.get("terrain_type")
        size = message.get("size", "medium")
        theme = message.get("theme")

        terrain_script = self._generate_terrain_script(terrain_type, size, theme)

        self.current_context.terrain_data = {
            "type": terrain_type,
            "size": size,
            "theme": theme,
            "script": terrain_script,
        }

        return {
            "type": "terrain_response",
            "script": terrain_script,
            "terrain_config": {"type": terrain_type, "size": size, "theme": theme},
        }

    def _handle_ui_request(self, message: dict) -> dict:
        """Handle UI element generation request"""
        ui_type = message.get("ui_type")
        properties = message.get("properties", {})

        ui_script = self._generate_ui_script(ui_type, properties)

        ui_element = {
            "type": ui_type,
            "properties": properties,
            "script": ui_script,
            "timestamp": datetime.now().isoformat(),
        }

        self.current_context.ui_elements.append(ui_element)

        return {"type": "ui_response", "script": ui_script, "ui_element": ui_element}

    def _handle_context_update(self, message: dict) -> dict:
        """Handle context update from Studio"""
        context_type = message.get("context_type")
        context_data = message.get("data")

        if context_type == "scripts":
            self.current_context.scripts = context_data
        elif context_type == "terrain":
            self.current_context.terrain_data = context_data
        elif context_type == "ui":
            self.current_context.ui_elements = context_data

        return {
            "type": "context_update_response",
            "status": "updated",
            "context_type": context_type,
        }

    def _handle_error_report(self, message: dict) -> dict:
        """Handle error reports from Studio"""
        error_type = message.get("error_type")
        error_message = message.get("error_message")
        script_context = message.get("script_context")

        logger.error(f"Roblox Studio error: {error_type} - {error_message}")

        # Analyze error and provide fix suggestion
        fix_suggestion = self._analyze_error(error_type, error_message, script_context)

        return {
            "type": "error_response",
            "fix_suggestion": fix_suggestion,
            "error_logged": True,
        }

    def _handle_plugin_register(self, message: dict) -> dict:
        """Handle plugin registration"""
        plugin_name = message.get("plugin_name")
        plugin_version = message.get("plugin_version")
        capabilities = message.get("capabilities", [])

        self.current_context.active_plugins.append(
            {
                "name": plugin_name,
                "version": plugin_version,
                "capabilities": capabilities,
                "registered_at": datetime.now().isoformat(),
            }
        )

        logger.info(f"Plugin registered: {plugin_name} v{plugin_version}")

        return {
            "type": "plugin_register_response",
            "status": "registered",
            "plugin_id": f"{plugin_name}_{plugin_version}",
        }

    def _generate_script(self, script_type: str, purpose: str, requirements: dict) -> str:
        """Generate Lua script based on requirements"""

        # Base template for different script types
        templates = {
            "ServerScript": """
-- Server Script: {purpose}
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")

-- Initialize
local function initialize()
    print("Initializing: {purpose}")
    {initialization_code}
end

-- Main logic
local function main()
    {main_code}
end

-- Event connections
{event_connections}

-- Start
initialize()
main()
""",
            "LocalScript": """
-- Local Script: {purpose}
local Players = game:GetService("Players")
local LocalPlayer = Players.LocalPlayer
local UserInputService = game:GetService("UserInputService")

-- Wait for character
local character = LocalPlayer.Character or LocalPlayer.CharacterAdded:Wait()

-- Main logic
local function main()
    {main_code}
end

-- Input handling
{input_handling}

-- Start
main()
""",
            "ModuleScript": """
-- Module Script: {purpose}
local Module = {}
Module.__index = Module

-- Constructor
function Module.new()
    local self = setmetatable({}, Module)
    {initialization_code}
    return self
end

-- Methods
{methods}

return Module
""",
        }

        template = templates.get(script_type, templates["ServerScript"])

        # Fill in template based on requirements
        script = template.format(
            purpose=purpose,
            initialization_code=requirements.get("init_code", "-- Initialization code here"),
            main_code=requirements.get("main_code", "-- Main logic here"),
            event_connections=requirements.get("events", "-- Event connections here"),
            input_handling=requirements.get("input", "-- Input handling here"),
            methods=requirements.get("methods", "-- Methods here"),
        )

        return script

    def _generate_terrain_script(self, terrain_type: str, size: str, theme: str) -> str:
        """Generate terrain generation script"""

        size_configs = {
            "small": {"x": 50, "y": 25, "z": 50},
            "medium": {"x": 100, "y": 50, "z": 100},
            "large": {"x": 200, "y": 100, "z": 200},
        }

        size_config = size_configs.get(size, size_configs["medium"])

        script = f"""
-- Terrain Generation: {theme}
local Terrain = workspace.Terrain

-- Define region
local region = Region3.new(
    Vector3.new(-{size_config['x']}, -10, -{size_config['z']}),
    Vector3.new({size_config['x']}, {size_config['y']}, {size_config['z']})
)
region = region:ExpandToGrid(4)

-- Clear existing terrain
Terrain:FillBall(Vector3.new(0, 0, 0), 10000, Enum.Material.Air)

-- Generate terrain based on theme
"""

        if theme == "ocean":
            script += """
-- Ocean theme
Terrain:FillBlock(region.CFrame, region.Size, Enum.Material.Sand)
local waterRegion = Region3.new(
    Vector3.new(-100, 0, -100),
    Vector3.new(100, 25, 100)
):ExpandToGrid(4)
Terrain:FillBlock(waterRegion.CFrame, waterRegion.Size, Enum.Material.Water)
"""
        elif theme == "forest":
            script += """
-- Forest theme
Terrain:FillBlock(region.CFrame, region.Size, Enum.Material.Grass)
-- Add hills
for i = 1, 10 do
    local pos = Vector3.new(
        math.random(-80, 80),
        10,
        math.random(-80, 80)
    )
    Terrain:FillBall(pos, math.random(15, 30), Enum.Material.LeafyGrass)
end
"""
        elif theme == "desert":
            script += """
-- Desert theme
Terrain:FillBlock(region.CFrame, region.Size, Enum.Material.Sand)
-- Add dunes
for i = 1, 8 do
    local pos = Vector3.new(
        math.random(-80, 80),
        5,
        math.random(-80, 80)
    )
    Terrain:FillBall(pos, math.random(20, 40), Enum.Material.Sand)
end
"""
        else:
            script += """
-- Default terrain
Terrain:FillBlock(region.CFrame, region.Size, Enum.Material.Grass)
"""

        script += "\nprint('Terrain generation complete!')"

        return script

    def _generate_ui_script(self, ui_type: str, properties: dict) -> str:
        """Generate UI creation script"""

        script = f"""
-- UI Creation: {ui_type}
local Players = game:GetService("Players")
local player = Players.LocalPlayer
local playerGui = player:WaitForChild("PlayerGui")

-- Create ScreenGui
local screenGui = Instance.new("ScreenGui")
screenGui.Name = "{ui_type}GUI"
screenGui.Parent = playerGui

"""

        if ui_type == "quiz":
            script += """
-- Quiz UI
local frame = Instance.new("Frame")
frame.Size = UDim2.new(0.4, 0, 0.6, 0)
frame.Position = UDim2.new(0.3, 0, 0.2, 0)
frame.BackgroundColor3 = Color3.fromRGB(240, 240, 240)
frame.Parent = screenGui

local questionLabel = Instance.new("TextLabel")
questionLabel.Size = UDim2.new(0.9, 0, 0.3, 0)
questionLabel.Position = UDim2.new(0.05, 0, 0.05, 0)
questionLabel.Text = "Question goes here"
questionLabel.TextScaled = true
questionLabel.Parent = frame

-- Answer buttons
for i = 1, 4 do
    local button = Instance.new("TextButton")
    button.Size = UDim2.new(0.9, 0, 0.12, 0)
    button.Position = UDim2.new(0.05, 0, 0.35 + (i-1) * 0.13, 0)
    button.Text = "Answer " .. i
    button.Parent = frame

    button.MouseButton1Click:Connect(function()
        print("Selected answer: " .. i)
    end)
end
"""
        elif ui_type == "menu":
            script += """
-- Menu UI
local frame = Instance.new("Frame")
frame.Size = UDim2.new(0.25, 0, 1, 0)
frame.Position = UDim2.new(0, 0, 0, 0)
frame.BackgroundColor3 = Color3.fromRGB(50, 50, 50)
frame.Parent = screenGui

-- Menu items
local menuItems = {"Dashboard", "Lessons", "Quizzes", "Progress", "Settings"}
for i, item in ipairs(menuItems) do
    local button = Instance.new("TextButton")
    button.Size = UDim2.new(0.9, 0, 0.08, 0)
    button.Position = UDim2.new(0.05, 0, 0.1 + (i-1) * 0.09, 0)
    button.Text = item
    button.Parent = frame

    button.MouseButton1Click:Connect(function()
        print("Menu selected: " .. item)
    end)
end
"""

        return script

    def _analyze_error(
        self, error_type: str, error_message: str, script_context: Optional[str]
    ) -> str:
        """Analyze error and provide fix suggestion"""

        suggestions = {
            "syntax": "Check for missing 'end' statements, unclosed strings, or typos",
            "nil_value": "Ensure the object exists before accessing its properties. Use :WaitForChild() or check if not nil",
            "infinite_loop": "Add a wait() statement inside loops or use RunService events",
            "permission": "This operation requires higher security context. Move to a ServerScript",
            "timeout": "Operation took too long. Consider breaking it into smaller chunks",
        }

        # Try to identify error type from message
        if "nil" in error_message.lower():
            return suggestions["nil_value"]
        elif "syntax" in error_message.lower():
            return suggestions["syntax"]
        elif "timeout" in error_message.lower():
            return suggestions["timeout"]
        else:
            return f"Error: {error_message}. Check the Roblox Developer documentation for more information."

    def get_capabilities(self) -> list[str]:
        """Get protocol capabilities"""
        return [
            "script_generation",
            "terrain_generation",
            "ui_creation",
            "error_analysis",
            "plugin_support",
            "context_management",
            "cache_optimization",
        ]

    def get_context_summary(self) -> dict[str, Any]:
        """Get summary of current Roblox context"""
        return {
            "place_id": self.current_context.place_id,
            "game_name": self.current_context.game_name,
            "script_count": len(self.current_context.scripts),
            "ui_element_count": len(self.current_context.ui_elements),
            "active_plugins": len(self.current_context.active_plugins),
            "has_terrain": self.current_context.terrain_data is not None,
            "studio_version": self.current_context.studio_version,
        }

    def export_scripts(self) -> list[dict[str, str]]:
        """Export all generated scripts"""
        return self.current_context.scripts

    def clear_cache(self):
        """Clear generation cache"""
        self.generation_cache.clear()
        logger.info("Roblox generation cache cleared")

    def format_terrain_data(self, terrain_data: dict) -> dict:
        """Format terrain data for Roblox Studio following Roblox Terrain API"""
        terrain_type = terrain_data.get("type", "grass")
        size = terrain_data.get("size", {"x": 100, "y": 50, "z": 100})
        material = terrain_data.get("material", "Grass")

        # Handle different size formats
        if isinstance(size, dict):
            size_x, size_y, size_z = (
                size.get("x", 100),
                size.get("y", 50),
                size.get("z", 100),
            )
        else:
            size_x, size_y, size_z = 100, 50, 100

        script = f"""-- Terrain Generation Script
local Terrain = workspace.Terrain
local Region3 = Region3.new(Vector3.new(0, 0, 0), Vector3.new({size_x}, {size_y}, {size_z}))
Region3 = Region3:ExpandToGrid(4)

-- Fill base terrain
Terrain:FillBall(Vector3.new({size_x/2}, {size_y/2}, {size_z/2}), 30, Enum.Material.{material})

-- Add terrain features based on type
if "{terrain_type}" == "mountain" then
    for i = 1, 5 do
        local pos = Vector3.new(math.random(0, {size_x}), 0, math.random(0, {size_z}))
        local height = math.random(20, 50)
        Terrain:FillWedge(CFrame.new(pos), Vector3.new(20, height, 20), Enum.Material.Rock)
    end
elseif "{terrain_type}" == "forest" then
    -- Add trees and foliage
    for i = 1, 10 do
        local pos = Vector3.new(math.random(10, {size_x-10}), 0, math.random(10, {size_z-10}))
        Terrain:FillCylinder(CFrame.new(pos), 5, 3, Enum.Material.Wood)
    end
end

print("Terrain generated: " .. "{terrain_type}")"""

        return {
            "terrain_script": script,
            "type": terrain_type,
            "material": material,
            "size": {"x": size_x, "y": size_y, "z": size_z},
        }

    def format_quiz_data(self, quiz_data: dict) -> dict:
        """Format quiz data for Roblox GUI using ScreenGui API"""
        question = quiz_data.get("question", "")
        options = quiz_data.get("options", [])
        correct = quiz_data.get("correct_answer", 0)
        explanation = quiz_data.get("explanation", "")

        script = f"""-- Quiz GUI Script
local Players = game:GetService("Players")
local player = Players.LocalPlayer
local playerGui = player:WaitForChild("PlayerGui")

-- Create ScreenGui
local screenGui = Instance.new("ScreenGui")
screenGui.Name = "QuizGui"
screenGui.ResetOnSpawn = false
screenGui.Parent = playerGui

-- Main Frame
local frame = Instance.new("Frame")
frame.Size = UDim2.new(0.5, 0, 0.6, 0)
frame.Position = UDim2.new(0.25, 0, 0.2, 0)
frame.BackgroundColor3 = Color3.new(0.2, 0.2, 0.2)
frame.BorderSizePixel = 2
frame.BorderColor3 = Color3.new(0.4, 0.4, 0.4)
frame.Parent = screenGui

-- Question Label
local questionLabel = Instance.new("TextLabel")
questionLabel.Text = "{question}"
questionLabel.Size = UDim2.new(1, -20, 0.3, 0)
questionLabel.Position = UDim2.new(0, 10, 0, 10)
questionLabel.TextScaled = true
questionLabel.TextColor3 = Color3.new(1, 1, 1)
questionLabel.BackgroundTransparency = 1
questionLabel.Font = Enum.Font.SourceSansBold
questionLabel.Parent = frame

-- Feedback Label
local feedbackLabel = Instance.new("TextLabel")
feedbackLabel.Text = ""
feedbackLabel.Size = UDim2.new(1, -20, 0.1, 0)
feedbackLabel.Position = UDim2.new(0, 10, 0.85, 0)
feedbackLabel.TextScaled = true
feedbackLabel.TextColor3 = Color3.new(1, 1, 1)
feedbackLabel.BackgroundTransparency = 1
feedbackLabel.Font = Enum.Font.SourceSans
feedbackLabel.Parent = frame
"""

        # Add option buttons
        for i, option in enumerate(options):
            script += f"""
-- Option {i+1}: {option}
local button{i} = Instance.new("TextButton")
button{i}.Text = "{option}"
button{i}.Size = UDim2.new(0.8, 0, 0.1, 0)
button{i}.Position = UDim2.new(0.1, 0, {0.4 + i*0.12}, 0)
button{i}.BackgroundColor3 = Color3.new(0.3, 0.3, 0.3)
button{i}.TextColor3 = Color3.new(1, 1, 1)
button{i}.Font = Enum.Font.SourceSans
button{i}.TextScaled = true
button{i}.Parent = frame

button{i}.MouseButton1Click:Connect(function()
    if {i} == {correct} then
        feedbackLabel.Text = "Correct! {explanation}"
        feedbackLabel.TextColor3 = Color3.new(0, 1, 0)
        button{i}.BackgroundColor3 = Color3.new(0, 0.6, 0)
    else
        feedbackLabel.Text = "Try again!"
        feedbackLabel.TextColor3 = Color3.new(1, 0, 0)
        button{i}.BackgroundColor3 = Color3.new(0.6, 0, 0)
    end
end)
"""

        script += """
-- Close button
local closeButton = Instance.new("TextButton")
closeButton.Text = "X"
closeButton.Size = UDim2.new(0, 30, 0, 30)
closeButton.Position = UDim2.new(1, -35, 0, 5)
closeButton.BackgroundColor3 = Color3.new(0.8, 0, 0)
closeButton.TextColor3 = Color3.new(1, 1, 1)
closeButton.Font = Enum.Font.SourceSansBold
closeButton.Parent = frame

closeButton.MouseButton1Click:Connect(function()
    screenGui:Destroy()
end)"""

        return {
            "quiz_gui": script,
            "question": question,
            "options": options,
            "correct_answer": correct,
        }

    def validate_place_id(self, place_id) -> bool:
        """Validate Roblox place ID"""
        if isinstance(place_id, int):
            return place_id > 0
        if isinstance(place_id, str):
            try:
                pid = int(place_id)
                return pid > 0
            except (ValueError, TypeError):
                return False
        return False

    def generate_remote_events(self, events: list[str]) -> str:
        """Generate RemoteEvent setup script following Roblox networking patterns"""
        script = """-- RemoteEvents Setup Script
local ReplicatedStorage = game:GetService("ReplicatedStorage")

-- Create RemoteEvents folder if it doesn't exist
local remoteEvents = ReplicatedStorage:FindFirstChild("RemoteEvents")
if not remoteEvents then
    remoteEvents = Instance.new("Folder")
    remoteEvents.Name = "RemoteEvents"
    remoteEvents.Parent = ReplicatedStorage
end

-- Create RemoteFunctions folder
local remoteFunctions = ReplicatedStorage:FindFirstChild("RemoteFunctions")
if not remoteFunctions then
    remoteFunctions = Instance.new("Folder")
    remoteFunctions.Name = "RemoteFunctions"
    remoteFunctions.Parent = ReplicatedStorage
end
"""

        for event in events:
            script += f"""
-- Create {event} RemoteEvent
local {event} = remoteEvents:FindFirstChild("{event}")
if not {event} then
    {event} = Instance.new("RemoteEvent")
    {event}.Name = "{event}"
    {event}.Parent = remoteEvents
end

-- Setup example server handler for {event}
{event}.OnServerEvent:Connect(function(player, ...)
    print("Received {event} from", player.Name)
    -- Handle event data here
end)
"""

        script += """
print("RemoteEvents initialized successfully")
return remoteEvents"""

        return script

    def handle_message(self, message: dict) -> dict:
        """Generic message handler for Roblox protocol messages"""
        message_type = message.get("type")

        # Map message types to handlers
        if message_type == "terrain_request":
            # Process as studio message
            return self.process_studio_message(message)
        elif message_type == "quiz_request":
            # Handle quiz generation
            quiz_data = message.get("data", {})
            formatted = self.format_quiz_data(quiz_data)
            return {"status": "success", "type": "quiz_response", "data": formatted}
        elif message_type == "validation_request":
            # Validate place ID
            place_id = message.get("place_id")
            is_valid = self.validate_place_id(place_id)
            return {
                "status": "success",
                "type": "validation_response",
                "valid": is_valid,
                "place_id": place_id,
            }
        else:
            # Default processing
            return {
                "status": "processed",
                "type": message_type,
                "message": f"Message type '{message_type}' processed",
            }
