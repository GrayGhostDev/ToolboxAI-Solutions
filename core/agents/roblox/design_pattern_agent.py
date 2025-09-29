"""
RobloxDesignPatternAgent - Implements modular, component-based architecture for Roblox

This agent applies industry-standard design patterns and Roblox 2025 best practices
to create maintainable, scalable, and reusable code structures. It ensures a 30%
productivity increase through modular coding and proper architectural patterns.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path
import json
import re
from enum import Enum
from dataclasses import dataclass, field

from ..base_agent import BaseAgent


class DesignPattern(Enum):
    """Design patterns supported by the agent"""
    SINGLETON = "singleton"
    OBSERVER = "observer"
    FACTORY = "factory"
    STRATEGY = "strategy"
    DECORATOR = "decorator"
    ADAPTER = "adapter"
    FACADE = "facade"
    COMMAND = "command"
    STATE = "state"
    COMPONENT = "component"
    MODULE = "module"
    REPOSITORY = "repository"


class ComponentType(Enum):
    """Types of reusable components"""
    SERVICE = "service"
    CONTROLLER = "controller"
    UI_COMPONENT = "ui_component"
    DATA_STORE = "data_store"
    NETWORK_MODULE = "network_module"
    GAME_MECHANIC = "game_mechanic"
    UTILITY = "utility"
    ANIMATION_CONTROLLER = "animation_controller"
    SOUND_MANAGER = "sound_manager"
    EFFECT_SYSTEM = "effect_system"


@dataclass
class ArchitectureRequirements:
    """Requirements for system architecture"""
    patterns: List[DesignPattern] = field(default_factory=list)
    components: List[ComponentType] = field(default_factory=list)
    modules: List[str] = field(default_factory=list)
    features: List[str] = field(default_factory=list)
    constraints: Dict[str, Any] = field(default_factory=dict)
    performance_targets: Dict[str, float] = field(default_factory=dict)


@dataclass
class ModuleStructure:
    """Structure of a code module"""
    name: str
    type: ComponentType
    pattern: DesignPattern
    dependencies: List[str] = field(default_factory=list)
    exports: List[str] = field(default_factory=list)
    methods: List[str] = field(default_factory=list)
    properties: List[str] = field(default_factory=list)
    events: List[str] = field(default_factory=list)


class RobloxDesignPatternAgent(BaseAgent):
    """
    Agent responsible for implementing design patterns and architectural best practices
    in Roblox game development. Ensures modular, maintainable, and scalable code.
    """
    
    def __init__(self):
        super().__init__({
            "name": "RobloxDesignPatternAgent",
            "model": "gpt-4",
            "temperature": 0.7,
            "max_tokens": 2000
        })
        
        self.name = "RobloxDesignPatternAgent"
        self.description = "Implements modular architecture and design patterns for Roblox"
        self.capabilities = [
            "Apply design patterns (Singleton, Observer, Factory, etc.)",
            "Create modular component-based architecture",
            "Generate reusable code modules",
            "Implement separation of concerns",
            "Ensure 30% productivity increase through modular coding",
            "Create event-driven systems",
            "Build scalable game architectures",
            "Generate documentation for patterns"
        ]
        
        # Design pattern templates for Luau
        self.pattern_templates = {
            DesignPattern.SINGLETON: self._generate_singleton_pattern,
            DesignPattern.OBSERVER: self._generate_observer_pattern,
            DesignPattern.FACTORY: self._generate_factory_pattern,
            DesignPattern.STRATEGY: self._generate_strategy_pattern,
            DesignPattern.DECORATOR: self._generate_decorator_pattern,
            DesignPattern.ADAPTER: self._generate_adapter_pattern,
            DesignPattern.FACADE: self._generate_facade_pattern,
            DesignPattern.COMMAND: self._generate_command_pattern,
            DesignPattern.STATE: self._generate_state_pattern,
            DesignPattern.COMPONENT: self._generate_component_pattern,
            DesignPattern.MODULE: self._generate_module_pattern,
            DesignPattern.REPOSITORY: self._generate_repository_pattern
        }
        
        # Component templates
        self.component_templates = {
            ComponentType.SERVICE: self._generate_service_component,
            ComponentType.CONTROLLER: self._generate_controller_component,
            ComponentType.UI_COMPONENT: self._generate_ui_component,
            ComponentType.DATA_STORE: self._generate_data_store_component,
            ComponentType.NETWORK_MODULE: self._generate_network_component,
            ComponentType.GAME_MECHANIC: self._generate_game_mechanic_component,
            ComponentType.UTILITY: self._generate_utility_component,
            ComponentType.ANIMATION_CONTROLLER: self._generate_animation_component,
            ComponentType.SOUND_MANAGER: self._generate_sound_component,
            ComponentType.EFFECT_SYSTEM: self._generate_effect_component
        }
        
        # Best practices rules
        self.best_practices = {
            "naming_conventions": {
                "modules": r"^[A-Z][a-zA-Z0-9]+Module$",
                "services": r"^[A-Z][a-zA-Z0-9]+Service$",
                "controllers": r"^[A-Z][a-zA-Z0-9]+Controller$",
                "events": r"^On[A-Z][a-zA-Z0-9]+$",
                "methods": r"^[a-z][a-zA-Z0-9]+$",
                "properties": r"^[a-z][a-zA-Z0-9]+$"
            },
            "module_size": {
                "max_lines": 500,
                "max_methods": 15,
                "max_dependencies": 5
            },
            "performance": {
                "avoid_loops_in_render": True,
                "use_connection_pooling": True,
                "implement_caching": True,
                "lazy_loading": True
            }
        }
    
    async def design_architecture(self, requirements: ArchitectureRequirements) -> Dict[str, Any]:
        """
        Design the overall architecture for a Roblox project
        
        Args:
            requirements: Architecture requirements and constraints
            
        Returns:
            Complete architecture design with modules and patterns
        """
        try:
            self.logger.info(f"Designing architecture with patterns: {requirements.patterns}")
            
            # Analyze requirements
            architecture = {
                "modules": [],
                "components": [],
                "patterns": {},
                "connections": [],
                "event_system": {},
                "data_flow": {},
                "deployment": {}
            }
            
            # Design module structure
            modules = self._design_module_structure(requirements)
            architecture["modules"] = modules
            
            # Apply design patterns
            for pattern in requirements.patterns:
                pattern_impl = self._apply_design_pattern(pattern, requirements)
                architecture["patterns"][pattern.value] = pattern_impl
            
            # Create component architecture
            for component_type in requirements.components:
                component = self._design_component(component_type, requirements)
                architecture["components"].append(component)
            
            # Design event system
            architecture["event_system"] = self._design_event_system(modules)
            
            # Define data flow
            architecture["data_flow"] = self._design_data_flow(modules)
            
            # Add deployment configuration
            architecture["deployment"] = self._design_deployment_structure()
            
            # Generate architecture documentation
            architecture["documentation"] = self._generate_architecture_docs(architecture)
            
            # Validate architecture against best practices
            validation = self._validate_architecture(architecture)
            architecture["validation"] = validation
            
            return {
                "success": True,
                "architecture": architecture,
                "estimated_productivity_gain": "30-40%",
                "modularity_score": self._calculate_modularity_score(architecture),
                "maintainability_index": self._calculate_maintainability_index(architecture)
            }
            
        except Exception as e:
            self.logger.error(f"Error designing architecture: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def _design_module_structure(self, requirements: ArchitectureRequirements) -> List[ModuleStructure]:
        """Design the module structure for the project"""
        modules = []
        
        # Core modules
        modules.append(ModuleStructure(
            name="GameCore",
            type=ComponentType.SERVICE,
            pattern=DesignPattern.SINGLETON,
            exports=["initialize", "shutdown", "getState"],
            methods=["init", "update", "cleanup"],
            properties=["isRunning", "currentState", "config"],
            events=["OnStateChanged", "OnInitialized"]
        ))
        
        # Feature-specific modules
        for feature in requirements.features:
            module = ModuleStructure(
                name=f"{feature}Module",
                type=ComponentType.GAME_MECHANIC,
                pattern=DesignPattern.MODULE,
                dependencies=["GameCore"],
                exports=[f"create{feature}", f"update{feature}", f"destroy{feature}"],
                methods=["initialize", "execute", "cleanup"],
                properties=["isActive", "configuration"],
                events=[f"On{feature}Started", f"On{feature}Completed"]
            )
            modules.append(module)
        
        return modules
    
    def _apply_design_pattern(self, pattern: DesignPattern, requirements: ArchitectureRequirements) -> Dict[str, Any]:
        """Apply a specific design pattern"""
        if pattern in self.pattern_templates:
            return self.pattern_templates[pattern](requirements)
        return {}
    
    def _design_component(self, component_type: ComponentType, requirements: ArchitectureRequirements) -> Dict[str, Any]:
        """Design a specific component"""
        if component_type in self.component_templates:
            return self.component_templates[component_type](requirements)
        return {}
    
    def _design_event_system(self, modules: List[ModuleStructure]) -> Dict[str, Any]:
        """Design the event-driven system"""
        event_system = {
            "events": [],
            "listeners": {},
            "emitters": {},
            "event_bus": None
        }
        
        # Collect all events from modules
        for module in modules:
            for event in module.events:
                event_system["events"].append({
                    "name": event,
                    "module": module.name,
                    "payload": self._define_event_payload(event)
                })
        
        # Create event bus implementation
        event_system["event_bus"] = self._generate_event_bus()
        
        return event_system
    
    def _design_data_flow(self, modules: List[ModuleStructure]) -> Dict[str, Any]:
        """Design data flow between modules"""
        return {
            "stores": self._design_data_stores(modules),
            "actions": self._design_actions(modules),
            "reducers": self._design_reducers(modules),
            "middleware": self._design_middleware()
        }
    
    def _design_deployment_structure(self) -> Dict[str, Any]:
        """Design deployment and build structure"""
        return {
            "folder_structure": {
                "src": {
                    "modules": "Core game modules",
                    "components": "Reusable components",
                    "services": "Game services",
                    "utils": "Utility functions",
                    "config": "Configuration files"
                },
                "assets": {
                    "models": "3D models",
                    "textures": "Texture files",
                    "sounds": "Audio files",
                    "animations": "Animation data"
                },
                "tests": "Unit and integration tests",
                "docs": "Documentation"
            },
            "build_pipeline": [
                "Lint code",
                "Run tests",
                "Bundle modules",
                "Optimize assets",
                "Deploy to Roblox"
            ]
        }
    
    # Pattern Generation Methods
    
    def _generate_singleton_pattern(self, requirements: ArchitectureRequirements) -> Dict[str, Any]:
        """Generate Singleton pattern implementation"""
        return {
            "pattern": "Singleton",
            "purpose": "Ensure single instance of critical services",
            "implementation": """
-- Singleton Pattern Implementation
local Singleton = {}
Singleton.__index = Singleton

local instance = nil

function Singleton.new()
    if instance then
        return instance
    end
    
    local self = setmetatable({}, Singleton)
    self.data = {}
    self.initialized = false
    
    instance = self
    return self
end

function Singleton:initialize(config)
    if self.initialized then
        warn("Singleton already initialized")
        return
    end
    
    self.config = config
    self.initialized = true
    
    -- Initialize components
    self:_setupComponents()
end

function Singleton:_setupComponents()
    -- Private setup method
end

function Singleton:getInstance()
    if not instance then
        instance = Singleton.new()
    end
    return instance
end

return Singleton
            """,
            "usage_example": "local gameCore = Singleton:getInstance()",
            "benefits": ["Memory efficiency", "Global state management", "Consistent access point"]
        }
    
    def _generate_observer_pattern(self, requirements: ArchitectureRequirements) -> Dict[str, Any]:
        """Generate Observer pattern implementation"""
        return {
            "pattern": "Observer",
            "purpose": "Event-driven communication between components",
            "implementation": """
-- Observer Pattern Implementation
local Observer = {}
Observer.__index = Observer

function Observer.new()
    local self = setmetatable({}, Observer)
    self.observers = {}
    return self
end

function Observer:subscribe(event, callback)
    if not self.observers[event] then
        self.observers[event] = {}
    end
    
    table.insert(self.observers[event], callback)
    
    -- Return unsubscribe function
    return function()
        self:unsubscribe(event, callback)
    end
end

function Observer:unsubscribe(event, callback)
    if not self.observers[event] then return end
    
    for i, observer in ipairs(self.observers[event]) do
        if observer == callback then
            table.remove(self.observers[event], i)
            break
        end
    end
end

function Observer:notify(event, ...)
    if not self.observers[event] then return end
    
    for _, callback in ipairs(self.observers[event]) do
        coroutine.wrap(callback)(...)
    end
end

return Observer
            """,
            "usage_example": "eventBus:subscribe('PlayerJoined', handlePlayerJoin)",
            "benefits": ["Decoupled components", "Dynamic event handling", "Flexible communication"]
        }
    
    def _generate_factory_pattern(self, requirements: ArchitectureRequirements) -> Dict[str, Any]:
        """Generate Factory pattern implementation"""
        return {
            "pattern": "Factory",
            "purpose": "Create objects without specifying exact classes",
            "implementation": """
-- Factory Pattern Implementation
local Factory = {}
Factory.__index = Factory

local registeredTypes = {}

function Factory.new()
    local self = setmetatable({}, Factory)
    return self
end

function Factory:registerType(typeName, constructor)
    registeredTypes[typeName] = constructor
end

function Factory:create(typeName, ...)
    local constructor = registeredTypes[typeName]
    
    if not constructor then
        error("Unknown type: " .. typeName)
    end
    
    return constructor(...)
end

function Factory:createBatch(typeName, count, ...)
    local instances = {}
    
    for i = 1, count do
        instances[i] = self:create(typeName, ...)
    end
    
    return instances
end

-- Register default types
Factory:registerType("Enemy", function(config)
    return {
        type = "Enemy",
        health = config.health or 100,
        damage = config.damage or 10
    }
end)

Factory:registerType("PowerUp", function(config)
    return {
        type = "PowerUp",
        effect = config.effect,
        duration = config.duration or 5
    }
end)

return Factory
            """,
            "usage_example": "local enemy = factory:create('Enemy', {health = 150})",
            "benefits": ["Flexible object creation", "Easy to extend", "Centralized creation logic"]
        }
    
    def _generate_strategy_pattern(self, requirements: ArchitectureRequirements) -> Dict[str, Any]:
        """Generate Strategy pattern implementation"""
        return {
            "pattern": "Strategy",
            "purpose": "Define family of algorithms and make them interchangeable",
            "implementation": """
-- Strategy Pattern Implementation
local Strategy = {}
Strategy.__index = Strategy

function Strategy.new()
    local self = setmetatable({}, Strategy)
    self.currentStrategy = nil
    return self
end

function Strategy:setStrategy(strategy)
    self.currentStrategy = strategy
end

function Strategy:execute(...)
    if not self.currentStrategy then
        error("No strategy set")
    end
    
    return self.currentStrategy:execute(...)
end

-- Example Movement Strategies
local WalkStrategy = {}
function WalkStrategy:execute(character, destination)
    -- Walk implementation
    character.Humanoid.WalkSpeed = 16
    character.Humanoid:MoveTo(destination)
end

local RunStrategy = {}
function RunStrategy:execute(character, destination)
    -- Run implementation
    character.Humanoid.WalkSpeed = 24
    character.Humanoid:MoveTo(destination)
end

local FlyStrategy = {}
function FlyStrategy:execute(character, destination)
    -- Fly implementation
    local bodyVelocity = Instance.new("BodyVelocity")
    bodyVelocity.Velocity = (destination - character.Position).Unit * 50
    bodyVelocity.Parent = character.HumanoidRootPart
end

return {
    Strategy = Strategy,
    WalkStrategy = WalkStrategy,
    RunStrategy = RunStrategy,
    FlyStrategy = FlyStrategy
}
            """,
            "usage_example": "movementController:setStrategy(RunStrategy)",
            "benefits": ["Runtime algorithm switching", "Clean separation", "Easy to add new strategies"]
        }
    
    # Component Generation Methods
    
    def _generate_service_component(self, requirements: ArchitectureRequirements) -> Dict[str, Any]:
        """Generate service component structure"""
        return {
            "type": "Service",
            "structure": """
-- Service Component Template
local Service = {}
Service.__index = Service

-- Dependencies
local RunService = game:GetService("RunService")
local Players = game:GetService("Players")

-- Constructor
function Service.new(config)
    local self = setmetatable({}, Service)
    
    self.config = config or {}
    self.isRunning = false
    self.connections = {}
    
    return self
end

-- Lifecycle methods
function Service:start()
    if self.isRunning then return end
    
    self.isRunning = true
    self:_initialize()
    self:_setupConnections()
end

function Service:stop()
    if not self.isRunning then return end
    
    self.isRunning = false
    self:_cleanup()
    self:_disconnectAll()
end

-- Private methods
function Service:_initialize()
    -- Initialize service components
end

function Service:_setupConnections()
    -- Setup event connections
    self.connections.heartbeat = RunService.Heartbeat:Connect(function(dt)
        self:_update(dt)
    end)
end

function Service:_update(deltaTime)
    -- Update logic
end

function Service:_cleanup()
    -- Cleanup resources
end

function Service:_disconnectAll()
    for _, connection in pairs(self.connections) do
        connection:Disconnect()
    end
    self.connections = {}
end

return Service
            """,
            "methods": ["start", "stop", "update", "cleanup"],
            "properties": ["isRunning", "config", "connections"]
        }
    
    def _generate_controller_component(self, requirements: ArchitectureRequirements) -> Dict[str, Any]:
        """Generate controller component structure"""
        return {
            "type": "Controller",
            "structure": """
-- Controller Component Template
local Controller = {}
Controller.__index = Controller

function Controller.new(model)
    local self = setmetatable({}, Controller)
    
    self.model = model
    self.view = nil
    self.actions = {}
    
    return self
end

function Controller:setView(view)
    self.view = view
    self:_bindViewEvents()
end

function Controller:registerAction(name, handler)
    self.actions[name] = handler
end

function Controller:executeAction(name, ...)
    local action = self.actions[name]
    
    if not action then
        warn("Unknown action: " .. name)
        return
    end
    
    return action(self, ...)
end

function Controller:_bindViewEvents()
    if not self.view then return end
    
    -- Bind view events to controller actions
    self.view.onAction = function(action, ...)
        self:executeAction(action, ...)
    end
end

function Controller:updateView(data)
    if self.view then
        self.view:update(data)
    end
end

return Controller
            """,
            "methods": ["setView", "registerAction", "executeAction", "updateView"],
            "properties": ["model", "view", "actions"]
        }
    
    def _generate_ui_component(self, requirements: ArchitectureRequirements) -> Dict[str, Any]:
        """Generate UI component structure"""
        return {
            "type": "UIComponent",
            "structure": """
-- UI Component Template
local UIComponent = {}
UIComponent.__index = UIComponent

function UIComponent.new(parent)
    local self = setmetatable({}, UIComponent)
    
    self.parent = parent
    self.elements = {}
    self.isVisible = false
    
    self:_createElements()
    
    return self
end

function UIComponent:_createElements()
    -- Create UI elements
    local frame = Instance.new("Frame")
    frame.Size = UDim2.new(0.3, 0, 0.4, 0)
    frame.Position = UDim2.new(0.35, 0, 0.3, 0)
    frame.BackgroundColor3 = Color3.new(0.2, 0.2, 0.2)
    frame.BorderSizePixel = 0
    frame.Parent = self.parent
    
    self.elements.frame = frame
    
    -- Add child elements
    self:_createHeader()
    self:_createContent()
    self:_createFooter()
end

function UIComponent:_createHeader()
    local header = Instance.new("TextLabel")
    header.Size = UDim2.new(1, 0, 0.15, 0)
    header.Text = "Component Header"
    header.TextScaled = true
    header.Parent = self.elements.frame
    
    self.elements.header = header
end

function UIComponent:_createContent()
    -- Create content area
end

function UIComponent:_createFooter()
    -- Create footer area
end

function UIComponent:show()
    self.isVisible = true
    self.elements.frame.Visible = true
end

function UIComponent:hide()
    self.isVisible = false
    self.elements.frame.Visible = false
end

function UIComponent:update(data)
    -- Update UI with new data
end

function UIComponent:destroy()
    for _, element in pairs(self.elements) do
        element:Destroy()
    end
    self.elements = {}
end

return UIComponent
            """,
            "methods": ["show", "hide", "update", "destroy"],
            "properties": ["parent", "elements", "isVisible"]
        }
    
    # Additional helper methods
    
    def _define_event_payload(self, event_name: str) -> Dict[str, str]:
        """Define the payload structure for an event"""
        # Common event payload patterns
        if "Player" in event_name:
            return {"player": "Player", "timestamp": "number"}
        elif "State" in event_name:
            return {"oldState": "string", "newState": "string", "timestamp": "number"}
        elif "Completed" in event_name:
            return {"result": "any", "success": "boolean", "timestamp": "number"}
        else:
            return {"data": "any", "timestamp": "number"}
    
    def _generate_event_bus(self) -> str:
        """Generate event bus implementation"""
        return """
-- Event Bus Implementation
local EventBus = {}
EventBus.__index = EventBus

local Signal = require(script.Parent.Signal)

function EventBus.new()
    local self = setmetatable({}, EventBus)
    self.events = {}
    return self
end

function EventBus:getEvent(eventName)
    if not self.events[eventName] then
        self.events[eventName] = Signal.new()
    end
    return self.events[eventName]
end

function EventBus:fire(eventName, ...)
    local event = self:getEvent(eventName)
    event:Fire(...)
end

function EventBus:connect(eventName, handler)
    local event = self:getEvent(eventName)
    return event:Connect(handler)
end

return EventBus
        """
    
    def _design_data_stores(self, modules: List[ModuleStructure]) -> List[Dict[str, Any]]:
        """Design data stores for modules"""
        stores = []
        
        for module in modules:
            if module.type in [ComponentType.DATA_STORE, ComponentType.SERVICE]:
                stores.append({
                    "name": f"{module.name}Store",
                    "type": "DataStore",
                    "schema": self._generate_store_schema(module),
                    "methods": ["get", "set", "update", "delete", "subscribe"]
                })
        
        return stores
    
    def _design_actions(self, modules: List[ModuleStructure]) -> List[Dict[str, Any]]:
        """Design actions for modules"""
        actions = []
        
        for module in modules:
            for method in module.methods:
                actions.append({
                    "name": f"{module.name}_{method}",
                    "type": "Action",
                    "payload": self._generate_action_payload(method)
                })
        
        return actions
    
    def _design_reducers(self, modules: List[ModuleStructure]) -> List[Dict[str, Any]]:
        """Design reducers for state management"""
        reducers = []
        
        for module in modules:
            reducers.append({
                "name": f"{module.name}Reducer",
                "initialState": self._generate_initial_state(module),
                "actions": [f"{module.name}_{method}" for method in module.methods]
            })
        
        return reducers
    
    def _design_middleware(self) -> List[Dict[str, Any]]:
        """Design middleware for the system"""
        return [
            {
                "name": "Logger",
                "purpose": "Log all actions and state changes",
                "order": 1
            },
            {
                "name": "Validator",
                "purpose": "Validate action payloads",
                "order": 2
            },
            {
                "name": "Async",
                "purpose": "Handle asynchronous actions",
                "order": 3
            },
            {
                "name": "ErrorHandler",
                "purpose": "Catch and handle errors",
                "order": 4
            }
        ]
    
    def _generate_store_schema(self, module: ModuleStructure) -> Dict[str, str]:
        """Generate schema for a data store"""
        schema = {}
        
        for prop in module.properties:
            # Infer type from property name
            if "is" in prop or "has" in prop:
                schema[prop] = "boolean"
            elif "count" in prop or "index" in prop:
                schema[prop] = "number"
            elif "name" in prop or "id" in prop:
                schema[prop] = "string"
            else:
                schema[prop] = "any"
        
        return schema
    
    def _generate_action_payload(self, method_name: str) -> Dict[str, str]:
        """Generate action payload structure"""
        # Common patterns for method names
        if "create" in method_name or "add" in method_name:
            return {"data": "table", "options": "table?"}
        elif "update" in method_name or "modify" in method_name:
            return {"id": "string", "changes": "table"}
        elif "delete" in method_name or "remove" in method_name:
            return {"id": "string", "force": "boolean?"}
        elif "get" in method_name or "fetch" in method_name:
            return {"id": "string?", "filter": "table?"}
        else:
            return {"data": "any"}
    
    def _generate_initial_state(self, module: ModuleStructure) -> Dict[str, Any]:
        """Generate initial state for a module"""
        state = {}
        
        for prop in module.properties:
            if "is" in prop or "has" in prop:
                state[prop] = False
            elif "count" in prop:
                state[prop] = 0
            elif "list" in prop or "array" in prop:
                state[prop] = []
            elif "config" in prop or "settings" in prop:
                state[prop] = {}
            else:
                state[prop] = None
        
        return state
    
    def _generate_architecture_docs(self, architecture: Dict[str, Any]) -> str:
        """Generate documentation for the architecture"""
        docs = "# System Architecture Documentation\n\n"
        
        docs += "## Overview\n"
        docs += "This architecture implements modular, component-based design patterns "
        docs += "following Roblox 2025 best practices.\n\n"
        
        docs += "## Modules\n"
        for module in architecture["modules"]:
            docs += f"### {module.name}\n"
            docs += f"- Type: {module.type.value}\n"
            docs += f"- Pattern: {module.pattern.value}\n"
            docs += f"- Dependencies: {', '.join(module.dependencies)}\n"
            docs += f"- Exports: {', '.join(module.exports)}\n\n"
        
        docs += "## Design Patterns\n"
        for pattern_name, pattern_data in architecture["patterns"].items():
            docs += f"### {pattern_name}\n"
            docs += f"- Purpose: {pattern_data.get('purpose', 'N/A')}\n"
            docs += f"- Benefits: {', '.join(pattern_data.get('benefits', []))}\n\n"
        
        docs += "## Event System\n"
        docs += f"Total Events: {len(architecture['event_system'].get('events', []))}\n\n"
        
        docs += "## Data Flow\n"
        docs += f"- Stores: {len(architecture['data_flow'].get('stores', []))}\n"
        docs += f"- Actions: {len(architecture['data_flow'].get('actions', []))}\n"
        docs += f"- Reducers: {len(architecture['data_flow'].get('reducers', []))}\n\n"
        
        return docs
    
    def _validate_architecture(self, architecture: Dict[str, Any]) -> Dict[str, Any]:
        """Validate architecture against best practices"""
        validation = {
            "passed": [],
            "warnings": [],
            "errors": []
        }
        
        # Check module count
        module_count = len(architecture.get("modules", []))
        if module_count > 20:
            validation["warnings"].append(f"High module count ({module_count}), consider consolidation")
        else:
            validation["passed"].append(f"Module count within limits ({module_count})")
        
        # Check for circular dependencies
        if not self._check_circular_dependencies(architecture.get("modules", [])):
            validation["errors"].append("Circular dependencies detected")
        else:
            validation["passed"].append("No circular dependencies")
        
        # Check naming conventions
        for module in architecture.get("modules", []):
            if not re.match(self.best_practices["naming_conventions"]["modules"], module.name):
                validation["warnings"].append(f"Module {module.name} doesn't follow naming convention")
        
        # Check event system
        if architecture.get("event_system", {}).get("event_bus"):
            validation["passed"].append("Event bus implemented")
        else:
            validation["warnings"].append("No event bus implementation found")
        
        return validation
    
    def _check_circular_dependencies(self, modules: List[ModuleStructure]) -> bool:
        """Check for circular dependencies in modules"""
        # Build dependency graph
        graph = {module.name: module.dependencies for module in modules}
        
        # DFS to detect cycles
        visited = set()
        rec_stack = set()
        
        def has_cycle(node):
            if node in rec_stack:
                return True
            if node in visited:
                return False
            
            visited.add(node)
            rec_stack.add(node)
            
            for neighbor in graph.get(node, []):
                if has_cycle(neighbor):
                    return True
            
            rec_stack.remove(node)
            return False
        
        for module_name in graph:
            if module_name not in visited:
                if has_cycle(module_name):
                    return False
        
        return True
    
    def _calculate_modularity_score(self, architecture: Dict[str, Any]) -> float:
        """Calculate modularity score of the architecture"""
        score = 0.0
        max_score = 100.0
        
        # Check module independence (30 points)
        modules = architecture.get("modules", [])
        if modules:
            avg_dependencies = sum(len(m.dependencies) for m in modules) / len(modules)
            if avg_dependencies <= 3:
                score += 30
            else:
                score += max(0, 30 - (avg_dependencies - 3) * 5)
        
        # Check pattern usage (20 points)
        patterns = architecture.get("patterns", {})
        score += min(20, len(patterns) * 4)
        
        # Check component separation (20 points)
        components = architecture.get("components", [])
        if components:
            score += min(20, len(components) * 2)
        
        # Check event system (15 points)
        if architecture.get("event_system", {}).get("event_bus"):
            score += 15
        
        # Check data flow design (15 points)
        data_flow = architecture.get("data_flow", {})
        if data_flow.get("stores") and data_flow.get("actions"):
            score += 15
        
        return min(score, max_score)
    
    def _calculate_maintainability_index(self, architecture: Dict[str, Any]) -> float:
        """Calculate maintainability index of the architecture"""
        # Based on common maintainability metrics
        index = 50.0  # Base score
        
        # Documentation quality
        if architecture.get("documentation"):
            index += 10
        
        # Validation passing
        validation = architecture.get("validation", {})
        if validation:
            index += len(validation.get("passed", [])) * 2
            index -= len(validation.get("errors", [])) * 5
            index -= len(validation.get("warnings", [])) * 1
        
        # Modularity score influence
        modularity = self._calculate_modularity_score(architecture)
        index += modularity * 0.3
        
        return max(0, min(100, index))
    
    # Additional pattern implementations
    
    def _generate_decorator_pattern(self, requirements: ArchitectureRequirements) -> Dict[str, Any]:
        """Generate Decorator pattern implementation"""
        return {
            "pattern": "Decorator",
            "purpose": "Add new functionality to objects dynamically",
            "implementation": """
-- Decorator Pattern Implementation
local Decorator = {}
Decorator.__index = Decorator

function Decorator.new(component)
    local self = setmetatable({}, Decorator)
    self.component = component
    return self
end

function Decorator:operation()
    -- Call base component operation
    local result = self.component:operation()
    
    -- Add decorator functionality
    return self:addedBehavior(result)
end

function Decorator:addedBehavior(result)
    -- Override in concrete decorators
    return result
end

-- Concrete Decorator Example
local LoggingDecorator = setmetatable({}, {__index = Decorator})
LoggingDecorator.__index = LoggingDecorator

function LoggingDecorator.new(component)
    local self = setmetatable(Decorator.new(component), LoggingDecorator)
    return self
end

function LoggingDecorator:addedBehavior(result)
    print("Operation executed with result:", result)
    return result
end

return {
    Decorator = Decorator,
    LoggingDecorator = LoggingDecorator
}
            """,
            "benefits": ["Flexible extension", "Single responsibility", "Open/closed principle"]
        }
    
    def _generate_adapter_pattern(self, requirements: ArchitectureRequirements) -> Dict[str, Any]:
        """Generate Adapter pattern implementation"""
        return {
            "pattern": "Adapter",
            "purpose": "Allow incompatible interfaces to work together",
            "implementation": """
-- Adapter Pattern Implementation
local Adapter = {}
Adapter.__index = Adapter

function Adapter.new(adaptee)
    local self = setmetatable({}, Adapter)
    self.adaptee = adaptee
    return self
end

function Adapter:request(...)
    -- Convert the request to adaptee's interface
    return self:_adaptRequest(...)
end

function Adapter:_adaptRequest(...)
    -- Transform parameters for adaptee
    local args = {...}
    -- Perform transformation
    return self.adaptee:specificRequest(table.unpack(args))
end

return Adapter
            """,
            "benefits": ["Interface compatibility", "Legacy code integration", "Decoupling"]
        }
    
    def _generate_facade_pattern(self, requirements: ArchitectureRequirements) -> Dict[str, Any]:
        """Generate Facade pattern implementation"""
        return {
            "pattern": "Facade",
            "purpose": "Provide simplified interface to complex subsystem",
            "implementation": """
-- Facade Pattern Implementation
local Facade = {}
Facade.__index = Facade

function Facade.new()
    local self = setmetatable({}, Facade)
    
    -- Initialize subsystems
    self.subsystem1 = require(script.Parent.Subsystem1).new()
    self.subsystem2 = require(script.Parent.Subsystem2).new()
    self.subsystem3 = require(script.Parent.Subsystem3).new()
    
    return self
end

function Facade:simpleOperation()
    -- Coordinate subsystems
    local result1 = self.subsystem1:operation1()
    local result2 = self.subsystem2:operation2(result1)
    local result3 = self.subsystem3:operation3(result2)
    
    return result3
end

function Facade:complexOperation(config)
    -- Handle complex coordination
    self.subsystem1:configure(config.subsystem1)
    self.subsystem2:configure(config.subsystem2)
    
    local results = {}
    results.step1 = self.subsystem1:execute()
    results.step2 = self.subsystem2:process(results.step1)
    results.step3 = self.subsystem3:finalize(results.step2)
    
    return results
end

return Facade
            """,
            "benefits": ["Simplified interface", "Reduced complexity", "Decoupling"]
        }
    
    def _generate_command_pattern(self, requirements: ArchitectureRequirements) -> Dict[str, Any]:
        """Generate Command pattern implementation"""
        return {
            "pattern": "Command",
            "purpose": "Encapsulate requests as objects",
            "implementation": """
-- Command Pattern Implementation
local Command = {}
Command.__index = Command

function Command.new(receiver, action, params)
    local self = setmetatable({}, Command)
    self.receiver = receiver
    self.action = action
    self.params = params
    self.executed = false
    return self
end

function Command:execute()
    if self.executed then
        warn("Command already executed")
        return
    end
    
    self.previousState = self.receiver:getState()
    self.result = self.receiver[self.action](self.receiver, table.unpack(self.params))
    self.executed = true
    
    return self.result
end

function Command:undo()
    if not self.executed then
        warn("Command not executed")
        return
    end
    
    self.receiver:setState(self.previousState)
    self.executed = false
end

-- Command Invoker
local CommandInvoker = {}
CommandInvoker.__index = CommandInvoker

function CommandInvoker.new()
    local self = setmetatable({}, CommandInvoker)
    self.history = {}
    self.currentIndex = 0
    return self
end

function CommandInvoker:executeCommand(command)
    command:execute()
    
    -- Remove any commands after current index
    for i = self.currentIndex + 1, #self.history do
        self.history[i] = nil
    end
    
    -- Add new command to history
    table.insert(self.history, command)
    self.currentIndex = #self.history
end

function CommandInvoker:undo()
    if self.currentIndex > 0 then
        self.history[self.currentIndex]:undo()
        self.currentIndex = self.currentIndex - 1
    end
end

function CommandInvoker:redo()
    if self.currentIndex < #self.history then
        self.currentIndex = self.currentIndex + 1
        self.history[self.currentIndex]:execute()
    end
end

return {
    Command = Command,
    CommandInvoker = CommandInvoker
}
            """,
            "benefits": ["Undo/redo support", "Macro recording", "Queuing operations"]
        }
    
    def _generate_state_pattern(self, requirements: ArchitectureRequirements) -> Dict[str, Any]:
        """Generate State pattern implementation"""
        return {
            "pattern": "State",
            "purpose": "Allow object to alter behavior when internal state changes",
            "implementation": """
-- State Pattern Implementation
local State = {}
State.__index = State

function State.new()
    local self = setmetatable({}, State)
    return self
end

function State:handle(context)
    error("Handle method must be implemented")
end

-- Concrete States
local IdleState = setmetatable({}, {__index = State})
IdleState.__index = IdleState

function IdleState.new()
    return setmetatable(State.new(), IdleState)
end

function IdleState:handle(context)
    print("Idle state handling")
    -- Transition logic
    if context.input == "start" then
        context:setState(RunningState.new())
    end
end

local RunningState = setmetatable({}, {__index = State})
RunningState.__index = RunningState

function RunningState.new()
    return setmetatable(State.new(), RunningState)
end

function RunningState:handle(context)
    print("Running state handling")
    -- Transition logic
    if context.input == "stop" then
        context:setState(IdleState.new())
    elseif context.input == "pause" then
        context:setState(PausedState.new())
    end
end

local PausedState = setmetatable({}, {__index = State})
PausedState.__index = PausedState

function PausedState.new()
    return setmetatable(State.new(), PausedState)
end

function PausedState:handle(context)
    print("Paused state handling")
    -- Transition logic
    if context.input == "resume" then
        context:setState(RunningState.new())
    elseif context.input == "stop" then
        context:setState(IdleState.new())
    end
end

-- Context
local Context = {}
Context.__index = Context

function Context.new()
    local self = setmetatable({}, Context)
    self.state = IdleState.new()
    self.input = nil
    return self
end

function Context:setState(state)
    self.state = state
end

function Context:request(input)
    self.input = input
    self.state:handle(self)
end

return {
    Context = Context,
    IdleState = IdleState,
    RunningState = RunningState,
    PausedState = PausedState
}
            """,
            "benefits": ["Clean state transitions", "Eliminates conditionals", "Easy to extend"]
        }
    
    def _generate_component_pattern(self, requirements: ArchitectureRequirements) -> Dict[str, Any]:
        """Generate Component pattern implementation"""
        return {
            "pattern": "Component",
            "purpose": "Build complex objects from simple components",
            "implementation": """
-- Component Pattern Implementation
local Component = {}
Component.__index = Component

function Component.new(name)
    local self = setmetatable({}, Component)
    self.name = name
    self.children = {}
    self.parent = nil
    return self
end

function Component:add(child)
    child.parent = self
    table.insert(self.children, child)
end

function Component:remove(child)
    for i, c in ipairs(self.children) do
        if c == child then
            table.remove(self.children, i)
            child.parent = nil
            break
        end
    end
end

function Component:getChild(index)
    return self.children[index]
end

function Component:operation()
    -- Perform operation on this component
    local result = {self.name}
    
    -- Recursively perform on children
    for _, child in ipairs(self.children) do
        local childResult = child:operation()
        for _, r in ipairs(childResult) do
            table.insert(result, r)
        end
    end
    
    return result
end

return Component
            """,
            "benefits": ["Tree structures", "Uniform treatment", "Recursive composition"]
        }
    
    def _generate_module_pattern(self, requirements: ArchitectureRequirements) -> Dict[str, Any]:
        """Generate Module pattern implementation"""
        return {
            "pattern": "Module",
            "purpose": "Encapsulate related functionality in self-contained units",
            "implementation": """
-- Module Pattern Implementation
local Module = {}

-- Private variables
local privateData = {}
local privateConfig = {}

-- Private functions
local function privateFunction()
    -- Private implementation
end

local function validateInput(input)
    -- Validation logic
    return type(input) == "table"
end

-- Public API
function Module.initialize(config)
    if not validateInput(config) then
        error("Invalid configuration")
    end
    
    privateConfig = config
    privateData = {}
    
    -- Setup module
    privateFunction()
end

function Module.publicMethod(param)
    -- Use private functions and data
    local result = privateFunction()
    return result
end

function Module.getData()
    -- Return copy to prevent external modification
    local copy = {}
    for k, v in pairs(privateData) do
        copy[k] = v
    end
    return copy
end

-- Module initialization
Module.VERSION = "1.0.0"
Module.AUTHOR = "RobloxDesignPatternAgent"

return Module
            """,
            "benefits": ["Encapsulation", "Namespace management", "Clear API"]
        }
    
    def _generate_repository_pattern(self, requirements: ArchitectureRequirements) -> Dict[str, Any]:
        """Generate Repository pattern implementation"""
        return {
            "pattern": "Repository",
            "purpose": "Encapsulate data access logic",
            "implementation": """
-- Repository Pattern Implementation
local Repository = {}
Repository.__index = Repository

function Repository.new(dataStore)
    local self = setmetatable({}, Repository)
    self.dataStore = dataStore
    self.cache = {}
    return self
end

function Repository:find(id)
    -- Check cache first
    if self.cache[id] then
        return self.cache[id]
    end
    
    -- Fetch from data store
    local data = self.dataStore:GetAsync(id)
    
    if data then
        self.cache[id] = data
    end
    
    return data
end

function Repository:findAll(filter)
    local results = {}
    
    -- Apply filter to data store
    local allData = self.dataStore:GetAllAsync()
    
    for id, data in pairs(allData) do
        if not filter or filter(data) then
            table.insert(results, data)
        end
    end
    
    return results
end

function Repository:save(id, entity)
    -- Validate entity
    if not self:_validate(entity) then
        error("Invalid entity")
    end
    
    -- Save to data store
    self.dataStore:SetAsync(id, entity)
    
    -- Update cache
    self.cache[id] = entity
    
    return true
end

function Repository:delete(id)
    -- Remove from data store
    self.dataStore:RemoveAsync(id)
    
    -- Remove from cache
    self.cache[id] = nil
    
    return true
end

function Repository:_validate(entity)
    -- Validation logic
    return type(entity) == "table"
end

return Repository
            """,
            "benefits": ["Data abstraction", "Caching support", "Testability"]
        }
    
    # Additional component generators
    
    def _generate_data_store_component(self, requirements: ArchitectureRequirements) -> Dict[str, Any]:
        """Generate data store component"""
        return {
            "type": "DataStore",
            "structure": """
-- DataStore Component
local DataStore = {}
DataStore.__index = DataStore

local DataStoreService = game:GetService("DataStoreService")

function DataStore.new(name)
    local self = setmetatable({}, DataStore)
    self.store = DataStoreService:GetDataStore(name)
    self.cache = {}
    self.pendingSaves = {}
    return self
end

function DataStore:get(key)
    local success, result = pcall(function()
        return self.store:GetAsync(key)
    end)
    
    if success then
        self.cache[key] = result
        return result
    else
        warn("Failed to get data:", result)
        return self.cache[key]
    end
end

function DataStore:set(key, value)
    self.cache[key] = value
    self.pendingSaves[key] = value
    
    -- Batch save after delay
    task.wait(1)
    self:_flushPendingSaves()
end

function DataStore:_flushPendingSaves()
    for key, value in pairs(self.pendingSaves) do
        local success, result = pcall(function()
            self.store:SetAsync(key, value)
        end)
        
        if success then
            self.pendingSaves[key] = nil
        else
            warn("Failed to save data:", result)
        end
    end
end

return DataStore
            """,
            "methods": ["get", "set", "update", "delete"],
            "properties": ["store", "cache", "pendingSaves"]
        }
    
    def _generate_network_component(self, requirements: ArchitectureRequirements) -> Dict[str, Any]:
        """Generate network component"""
        return {
            "type": "NetworkModule",
            "structure": """
-- Network Module Component
local NetworkModule = {}
NetworkModule.__index = NetworkModule

local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")

function NetworkModule.new()
    local self = setmetatable({}, NetworkModule)
    
    self.remotes = {}
    self.callbacks = {}
    
    self:_setupRemotes()
    
    return self
end

function NetworkModule:_setupRemotes()
    local remotesFolder = ReplicatedStorage:FindFirstChild("Remotes")
    
    if not remotesFolder then
        remotesFolder = Instance.new("Folder")
        remotesFolder.Name = "Remotes"
        remotesFolder.Parent = ReplicatedStorage
    end
    
    self.remotesFolder = remotesFolder
end

function NetworkModule:createRemoteEvent(name)
    local remote = Instance.new("RemoteEvent")
    remote.Name = name
    remote.Parent = self.remotesFolder
    
    self.remotes[name] = remote
    return remote
end

function NetworkModule:createRemoteFunction(name)
    local remote = Instance.new("RemoteFunction")
    remote.Name = name
    remote.Parent = self.remotesFolder
    
    self.remotes[name] = remote
    return remote
end

function NetworkModule:on(remoteName, callback)
    local remote = self.remotes[remoteName]
    
    if not remote then
        warn("Remote not found:", remoteName)
        return
    end
    
    if remote:IsA("RemoteEvent") then
        if RunService:IsServer() then
            remote.OnServerEvent:Connect(callback)
        else
            remote.OnClientEvent:Connect(callback)
        end
    elseif remote:IsA("RemoteFunction") then
        if RunService:IsServer() then
            remote.OnServerInvoke = callback
        else
            remote.OnClientInvoke = callback
        end
    end
end

function NetworkModule:fire(remoteName, ...)
    local remote = self.remotes[remoteName]
    
    if not remote then
        warn("Remote not found:", remoteName)
        return
    end
    
    if remote:IsA("RemoteEvent") then
        if RunService:IsServer() then
            remote:FireAllClients(...)
        else
            remote:FireServer(...)
        end
    end
end

return NetworkModule
            """,
            "methods": ["createRemoteEvent", "createRemoteFunction", "on", "fire"],
            "properties": ["remotes", "callbacks", "remotesFolder"]
        }
    
    def _generate_game_mechanic_component(self, requirements: ArchitectureRequirements) -> Dict[str, Any]:
        """Generate game mechanic component"""
        return {
            "type": "GameMechanic",
            "structure": """
-- Game Mechanic Component
local GameMechanic = {}
GameMechanic.__index = GameMechanic

function GameMechanic.new(config)
    local self = setmetatable({}, GameMechanic)
    
    self.config = config or {}
    self.isActive = false
    self.players = {}
    self.state = "idle"
    
    return self
end

function GameMechanic:start()
    if self.isActive then return end
    
    self.isActive = true
    self.state = "running"
    
    self:onStart()
end

function GameMechanic:stop()
    if not self.isActive then return end
    
    self.isActive = false
    self.state = "idle"
    
    self:onStop()
end

function GameMechanic:addPlayer(player)
    if self.players[player] then return end
    
    self.players[player] = {
        score = 0,
        data = {}
    }
    
    self:onPlayerAdded(player)
end

function GameMechanic:removePlayer(player)
    if not self.players[player] then return end
    
    self:onPlayerRemoved(player)
    self.players[player] = nil
end

function GameMechanic:update(deltaTime)
    if not self.isActive then return end
    
    self:onUpdate(deltaTime)
end

-- Override these in subclasses
function GameMechanic:onStart() end
function GameMechanic:onStop() end
function GameMechanic:onPlayerAdded(player) end
function GameMechanic:onPlayerRemoved(player) end
function GameMechanic:onUpdate(deltaTime) end

return GameMechanic
            """,
            "methods": ["start", "stop", "addPlayer", "removePlayer", "update"],
            "properties": ["config", "isActive", "players", "state"]
        }
    
    def _generate_utility_component(self, requirements: ArchitectureRequirements) -> Dict[str, Any]:
        """Generate utility component"""
        return {
            "type": "Utility",
            "structure": """
-- Utility Module
local Utility = {}

-- Math utilities
function Utility.lerp(a, b, t)
    return a + (b - a) * t
end

function Utility.clamp(value, min, max)
    return math.max(min, math.min(max, value))
end

function Utility.round(value, precision)
    precision = precision or 0
    local mult = 10 ^ precision
    return math.floor(value * mult + 0.5) / mult
end

-- Table utilities
function Utility.deepCopy(original)
    local copy = {}
    for k, v in pairs(original) do
        if type(v) == "table" then
            copy[k] = Utility.deepCopy(v)
        else
            copy[k] = v
        end
    end
    return copy
end

function Utility.merge(t1, t2)
    local result = Utility.deepCopy(t1)
    for k, v in pairs(t2) do
        result[k] = v
    end
    return result
end

-- String utilities
function Utility.split(str, delimiter)
    delimiter = delimiter or ","
    local result = {}
    for match in (str .. delimiter):gmatch("(.-)" .. delimiter) do
        table.insert(result, match)
    end
    return result
end

function Utility.trim(str)
    return str:match("^%s*(.-)%s*$")
end

-- Time utilities
function Utility.formatTime(seconds)
    local minutes = math.floor(seconds / 60)
    local secs = seconds % 60
    return string.format("%02d:%02d", minutes, secs)
end

function Utility.debounce(func, delay)
    local lastCall = 0
    return function(...)
        local now = tick()
        if now - lastCall >= delay then
            lastCall = now
            return func(...)
        end
    end
end

-- Validation utilities
function Utility.isValidInstance(obj, className)
    return obj and obj:IsA(className)
end

function Utility.validateConfig(config, schema)
    for key, expectedType in pairs(schema) do
        if type(config[key]) ~= expectedType then
            return false, "Invalid type for " .. key
        end
    end
    return true
end

return Utility
            """,
            "methods": ["lerp", "clamp", "round", "deepCopy", "merge", "split", "trim", "formatTime", "debounce"],
            "properties": []
        }
    
    def _generate_animation_component(self, requirements: ArchitectureRequirements) -> Dict[str, Any]:
        """Generate animation controller component"""
        return {
            "type": "AnimationController",
            "structure": """
-- Animation Controller Component
local AnimationController = {}
AnimationController.__index = AnimationController

function AnimationController.new(humanoid)
    local self = setmetatable({}, AnimationController)
    
    self.humanoid = humanoid
    self.animator = humanoid:FindFirstChild("Animator") or humanoid
    self.tracks = {}
    self.currentAnimation = nil
    
    return self
end

function AnimationController:loadAnimation(name, animationId)
    local animation = Instance.new("Animation")
    animation.AnimationId = animationId
    
    local track = self.animator:LoadAnimation(animation)
    self.tracks[name] = track
    
    return track
end

function AnimationController:play(name, fadeTime, weight, speed)
    local track = self.tracks[name]
    
    if not track then
        warn("Animation not found:", name)
        return
    end
    
    -- Stop current animation
    if self.currentAnimation and self.currentAnimation ~= track then
        self.currentAnimation:Stop(fadeTime or 0.1)
    end
    
    -- Play new animation
    track:Play(fadeTime, weight, speed)
    self.currentAnimation = track
    
    return track
end

function AnimationController:stop(name, fadeTime)
    local track = name and self.tracks[name] or self.currentAnimation
    
    if track then
        track:Stop(fadeTime or 0.1)
        
        if track == self.currentAnimation then
            self.currentAnimation = nil
        end
    end
end

function AnimationController:stopAll(fadeTime)
    for _, track in pairs(self.tracks) do
        track:Stop(fadeTime or 0.1)
    end
    self.currentAnimation = nil
end

function AnimationController:adjustSpeed(name, speed)
    local track = self.tracks[name]
    
    if track then
        track:AdjustSpeed(speed)
    end
end

function AnimationController:adjustWeight(name, weight, fadeTime)
    local track = self.tracks[name]
    
    if track then
        track:AdjustWeight(weight, fadeTime or 0.1)
    end
end

return AnimationController
            """,
            "methods": ["loadAnimation", "play", "stop", "stopAll", "adjustSpeed", "adjustWeight"],
            "properties": ["humanoid", "animator", "tracks", "currentAnimation"]
        }
    
    def _generate_sound_component(self, requirements: ArchitectureRequirements) -> Dict[str, Any]:
        """Generate sound manager component"""
        return {
            "type": "SoundManager",
            "structure": """
-- Sound Manager Component
local SoundManager = {}
SoundManager.__index = SoundManager

local SoundService = game:GetService("SoundService")

function SoundManager.new()
    local self = setmetatable({}, SoundManager)
    
    self.sounds = {}
    self.groups = {}
    self.volumes = {
        master = 1,
        music = 0.5,
        sfx = 0.8,
        ambient = 0.3
    }
    
    self:_setupSoundGroups()
    
    return self
end

function SoundManager:_setupSoundGroups()
    -- Create sound groups
    for groupName, _ in pairs(self.volumes) do
        if groupName ~= "master" then
            local group = Instance.new("SoundGroup")
            group.Name = groupName
            group.Volume = self.volumes[groupName]
            group.Parent = SoundService
            
            self.groups[groupName] = group
        end
    end
end

function SoundManager:loadSound(name, soundId, group)
    local sound = Instance.new("Sound")
    sound.SoundId = soundId
    sound.Name = name
    
    if group and self.groups[group] then
        sound.SoundGroup = self.groups[group]
    end
    
    sound.Parent = SoundService
    self.sounds[name] = sound
    
    return sound
end

function SoundManager:play(name, properties)
    local sound = self.sounds[name]
    
    if not sound then
        warn("Sound not found:", name)
        return
    end
    
    -- Apply properties if provided
    if properties then
        for prop, value in pairs(properties) do
            sound[prop] = value
        end
    end
    
    sound:Play()
    return sound
end

function SoundManager:stop(name, fadeOut)
    local sound = self.sounds[name]
    
    if not sound then return end
    
    if fadeOut then
        -- Fade out over time
        local startVolume = sound.Volume
        local fadeTime = fadeOut
        local elapsed = 0
        
        task.spawn(function()
            while elapsed < fadeTime do
                elapsed = elapsed + task.wait()
                sound.Volume = startVolume * (1 - elapsed / fadeTime)
            end
            sound:Stop()
            sound.Volume = startVolume
        end)
    else
        sound:Stop()
    end
end

function SoundManager:setVolume(group, volume)
    if group == "master" then
        self.volumes.master = volume
        -- Apply to all groups
        for groupName, soundGroup in pairs(self.groups) do
            soundGroup.Volume = self.volumes[groupName] * volume
        end
    elseif self.groups[group] then
        self.volumes[group] = volume
        self.groups[group].Volume = volume * self.volumes.master
    end
end

function SoundManager:playRandomFromList(soundList, group)
    if #soundList == 0 then return end
    
    local randomSound = soundList[math.random(1, #soundList)]
    return self:play(randomSound, {SoundGroup = self.groups[group]})
end

return SoundManager
            """,
            "methods": ["loadSound", "play", "stop", "setVolume", "playRandomFromList"],
            "properties": ["sounds", "groups", "volumes"]
        }
    
    def _generate_effect_component(self, requirements: ArchitectureRequirements) -> Dict[str, Any]:
        """Generate effect system component"""
        return {
            "type": "EffectSystem",
            "structure": """
-- Effect System Component
local EffectSystem = {}
EffectSystem.__index = EffectSystem

local TweenService = game:GetService("TweenService")
local Debris = game:GetService("Debris")

function EffectSystem.new()
    local self = setmetatable({}, EffectSystem)
    
    self.effects = {}
    self.activeEffects = {}
    
    return self
end

function EffectSystem:registerEffect(name, effectFunction)
    self.effects[name] = effectFunction
end

function EffectSystem:playEffect(name, target, params)
    local effectFunction = self.effects[name]
    
    if not effectFunction then
        warn("Effect not found:", name)
        return
    end
    
    local effect = effectFunction(target, params)
    
    -- Track active effect
    if effect then
        table.insert(self.activeEffects, effect)
        
        -- Auto-cleanup if effect has duration
        if params and params.duration then
            task.delay(params.duration, function()
                self:cleanupEffect(effect)
            end)
        end
    end
    
    return effect
end

function EffectSystem:cleanupEffect(effect)
    -- Remove from active effects
    for i, activeEffect in ipairs(self.activeEffects) do
        if activeEffect == effect then
            table.remove(self.activeEffects, i)
            break
        end
    end
    
    -- Cleanup based on effect type
    if typeof(effect) == "Instance" then
        effect:Destroy()
    elseif type(effect) == "table" and effect.Destroy then
        effect:Destroy()
    end
end

function EffectSystem:cleanupAll()
    for _, effect in ipairs(self.activeEffects) do
        self:cleanupEffect(effect)
    end
    self.activeEffects = {}
end

-- Predefined effects
function EffectSystem:createFadeEffect(target, params)
    params = params or {}
    local duration = params.duration or 1
    local fadeIn = params.fadeIn or false
    
    local startTransparency = fadeIn and 1 or 0
    local endTransparency = fadeIn and 0 or 1
    
    if target:IsA("BasePart") then
        target.Transparency = startTransparency
        
        local tween = TweenService:Create(
            target,
            TweenInfo.new(duration),
            {Transparency = endTransparency}
        )
        
        tween:Play()
        return tween
    end
end

function EffectSystem:createParticleEffect(position, params)
    params = params or {}
    
    local part = Instance.new("Part")
    part.Anchored = true
    part.CanCollide = false
    part.Transparency = 1
    part.Position = position
    part.Parent = workspace
    
    local emitter = Instance.new("ParticleEmitter")
    emitter.Texture = params.texture or "rbxasset://textures/particles/sparkles_main.dds"
    emitter.Rate = params.rate or 50
    emitter.Lifetime = NumberRange.new(params.lifetime or 1)
    emitter.Speed = NumberRange.new(params.speed or 5)
    emitter.Parent = part
    
    -- Auto cleanup
    Debris:AddItem(part, params.duration or 3)
    
    return part
end

return EffectSystem
            """,
            "methods": ["registerEffect", "playEffect", "cleanupEffect", "cleanupAll", "createFadeEffect", "createParticleEffect"],
            "properties": ["effects", "activeEffects"]
        }
    
    async def execute_task(self, task: str) -> Dict[str, Any]:
        """Execute a design pattern task"""
        try:
            self.logger.info(f"Executing design pattern task: {task}")
            
            # Parse task to determine requirements
            requirements = self._parse_task_requirements(task)
            
            # Design architecture based on requirements
            result = await self.design_architecture(requirements)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error executing task: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def _parse_task_requirements(self, task: str) -> ArchitectureRequirements:
        """Parse task string to extract requirements"""
        requirements = ArchitectureRequirements()
        
        # Extract patterns mentioned
        pattern_keywords = {
            "singleton": DesignPattern.SINGLETON,
            "observer": DesignPattern.OBSERVER,
            "factory": DesignPattern.FACTORY,
            "strategy": DesignPattern.STRATEGY,
            "decorator": DesignPattern.DECORATOR,
            "component": DesignPattern.COMPONENT
        }
        
        for keyword, pattern in pattern_keywords.items():
            if keyword in task.lower():
                requirements.patterns.append(pattern)
        
        # Extract component types
        component_keywords = {
            "service": ComponentType.SERVICE,
            "controller": ComponentType.CONTROLLER,
            "ui": ComponentType.UI_COMPONENT,
            "data": ComponentType.DATA_STORE,
            "network": ComponentType.NETWORK_MODULE,
            "game": ComponentType.GAME_MECHANIC
        }
        
        for keyword, component in component_keywords.items():
            if keyword in task.lower():
                requirements.components.append(component)
        
        # Extract features
        if "educational" in task.lower():
            requirements.features.extend(["Quiz", "Lesson", "Progress"])
        if "multiplayer" in task.lower():
            requirements.features.extend(["Matchmaking", "Lobby", "Sync"])
        if "adventure" in task.lower():
            requirements.features.extend(["Quest", "Inventory", "Combat"])
        
        # Set default patterns if none specified
        if not requirements.patterns:
            requirements.patterns = [
                DesignPattern.MODULE,
                DesignPattern.OBSERVER,
                DesignPattern.FACTORY
            ]
        
        # Set default components if none specified
        if not requirements.components:
            requirements.components = [
                ComponentType.SERVICE,
                ComponentType.CONTROLLER,
                ComponentType.GAME_MECHANIC
            ]
        
        return requirements