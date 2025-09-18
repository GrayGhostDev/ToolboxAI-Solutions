"""
Base Error Handling Agent

Foundation for all error handling agents with specialized capabilities
for error detection, analysis, and resolution.
"""

import asyncio
import logging
import traceback
from typing import Dict, Any, Optional, List, TypedDict, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
import json
import re

from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_core.tools import Tool
from langchain.agents import AgentExecutor, create_react_agent
from langchain_core.prompts import PromptTemplate
from pydantic import BaseModel, Field

from core.agents.base_agent import BaseAgent, AgentConfig, AgentState, TaskResult
from core.sparc.state_manager import StateManager
from core.sparc.policy_engine import PolicyEngine
from core.sparc.reward_calculator import RewardCalculator

logger = logging.getLogger(__name__)


class ErrorType(Enum):
    """Types of errors that can be handled"""
    SYNTAX = "syntax_error"
    RUNTIME = "runtime_error"
    LOGIC = "logic_error"
    PERFORMANCE = "performance_issue"
    SECURITY = "security_vulnerability"
    DEPENDENCY = "dependency_error"
    INTEGRATION = "integration_error"
    CONFIGURATION = "configuration_error"
    TYPE_ERROR = "type_error"
    MEMORY_LEAK = "memory_leak"
    DEADLOCK = "deadlock"
    RACE_CONDITION = "race_condition"
    API_ERROR = "api_error"
    DATABASE_ERROR = "database_error"
    NETWORK_ERROR = "network_error"


class ErrorPriority(Enum):
    """Priority levels for error handling"""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4
    EMERGENCY = 5


class ErrorState(TypedDict):
    """State schema for error handling operations"""
    error_id: str
    error_type: ErrorType
    priority: ErrorPriority
    description: str
    stack_trace: Optional[str]
    file_path: Optional[str]
    line_number: Optional[int]
    context: Dict[str, Any]
    attempted_fixes: List[Dict[str, Any]]
    resolution_status: str
    timestamp: str
    affected_components: List[str]
    potential_impact: str
    recovery_strategy: Optional[str]
    metadata: Dict[str, Any]


class ErrorPattern(BaseModel):
    """Model for error patterns"""
    pattern_id: str = Field(description="Unique identifier for the pattern")
    regex: str = Field(description="Regular expression to match the error")
    error_type: ErrorType = Field(description="Type of error this pattern matches")
    priority: ErrorPriority = Field(description="Default priority for this pattern")
    suggested_fix: Optional[str] = Field(description="Suggested fix for this pattern")
    frequency: int = Field(default=0, description="How often this pattern has been seen")
    success_rate: float = Field(default=0.0, description="Success rate of suggested fix")
    last_seen: Optional[str] = Field(default=None, description="Last time this pattern was seen")


class ErrorContext(BaseModel):
    """Extended context for error analysis"""
    code_snippet: Optional[str] = Field(description="Code snippet around the error")
    dependencies: List[str] = Field(default_factory=list, description="Related dependencies")
    environment: Dict[str, str] = Field(default_factory=dict, description="Environment variables")
    recent_changes: List[str] = Field(default_factory=list, description="Recent git changes")
    system_state: Dict[str, Any] = Field(default_factory=dict, description="System state at error time")
    user_actions: List[str] = Field(default_factory=list, description="User actions leading to error")
    related_errors: List[str] = Field(default_factory=list, description="Related error IDs")


@dataclass
class ErrorAgentConfig(AgentConfig):
    """Configuration specific to error handling agents"""
    max_fix_attempts: int = 3
    auto_fix_enabled: bool = True
    pattern_learning_enabled: bool = True
    rollback_enabled: bool = True
    monitoring_interval: int = 60  # seconds
    error_history_limit: int = 1000
    pattern_database_path: str = "core/agents/error_handling/patterns.json"
    recovery_strategies_path: str = "core/agents/error_handling/recovery_strategies.json"


class BaseErrorAgent(BaseAgent):
    """
    Base class for all error handling agents.

    Provides specialized capabilities for:
    - Error detection and classification
    - Pattern recognition and learning
    - Recovery strategy selection
    - Rollback mechanisms
    - Integration with SPARC framework
    """

    def __init__(self, config: ErrorAgentConfig):
        super().__init__(config)
        self.error_config = config
        self.error_patterns: List[ErrorPattern] = []
        self.error_history: List[ErrorState] = []
        self.recovery_strategies: Dict[str, Any] = {}

        # Initialize SPARC components
        self.state_manager = StateManager()
        self.policy_engine = PolicyEngine()
        self.reward_system = RewardCalculator()

        # Load patterns and strategies
        self._load_error_patterns()
        self._load_recovery_strategies()

        # Initialize specialized tools
        self.tools = self._create_error_tools()

        logger.info(f"Initialized {self.name} error handling agent")

    def _get_default_system_prompt(self) -> str:
        """Get specialized system prompt for error handling"""
        return f"""You are {self.name}, an advanced error handling agent specialized in detecting, analyzing, and resolving software errors.

Your core responsibilities:
- Detect and classify errors accurately
- Analyze root causes of failures
- Suggest and implement fixes
- Learn from error patterns
- Coordinate with other agents for complex issues
- Ensure system stability and reliability

Key principles:
1. Safety first - never make changes that could worsen the situation
2. Document all actions for audit trail
3. Learn from each error to prevent recurrence
4. Escalate critical issues immediately
5. Maintain backward compatibility when fixing issues

You have access to specialized tools for error analysis and correction.
Always provide clear, actionable recommendations with risk assessments."""

    def _create_error_tools(self) -> List[Tool]:
        """Create specialized tools for error handling"""
        tools = []

        # Error detection tool
        tools.append(Tool(
            name="detect_error",
            description="Detect and classify errors in code or logs",
            func=self._detect_error_tool
        ))

        # Stack trace analyzer
        tools.append(Tool(
            name="analyze_stack_trace",
            description="Analyze stack trace to identify root cause",
            func=self._analyze_stack_trace_tool
        ))

        # Code fix suggester
        tools.append(Tool(
            name="suggest_fix",
            description="Suggest fixes for identified errors",
            func=self._suggest_fix_tool
        ))

        # Pattern matcher
        tools.append(Tool(
            name="match_pattern",
            description="Match error against known patterns",
            func=self._match_pattern_tool
        ))

        # Recovery strategy selector
        tools.append(Tool(
            name="select_recovery_strategy",
            description="Select appropriate recovery strategy",
            func=self._select_recovery_strategy_tool
        ))

        return tools

    def _load_error_patterns(self):
        """Load error patterns from database"""
        pattern_file = Path(self.error_config.pattern_database_path)
        if pattern_file.exists():
            try:
                with open(pattern_file, 'r') as f:
                    patterns_data = json.load(f)
                    self.error_patterns = [ErrorPattern(**p) for p in patterns_data]
                logger.info(f"Loaded {len(self.error_patterns)} error patterns")
            except Exception as e:
                logger.error(f"Failed to load error patterns: {e}")
                self.error_patterns = []
        else:
            # Initialize with default patterns
            self._initialize_default_patterns()

    def _initialize_default_patterns(self):
        """Initialize default error patterns"""
        default_patterns = [
            ErrorPattern(
                pattern_id="import_error",
                regex=r"(Import|Module).*not found",
                error_type=ErrorType.DEPENDENCY,
                priority=ErrorPriority.HIGH,
                suggested_fix="Check if module is installed and in PYTHONPATH"
            ),
            ErrorPattern(
                pattern_id="null_pointer",
                regex=r"(NoneType|null|undefined).*has no attribute",
                error_type=ErrorType.RUNTIME,
                priority=ErrorPriority.MEDIUM,
                suggested_fix="Add null check before accessing attributes"
            ),
            ErrorPattern(
                pattern_id="type_mismatch",
                regex=r"(TypeError|type mismatch|incompatible type)",
                error_type=ErrorType.TYPE_ERROR,
                priority=ErrorPriority.MEDIUM,
                suggested_fix="Check type annotations and ensure correct types are passed"
            ),
            ErrorPattern(
                pattern_id="memory_issue",
                regex=r"(MemoryError|out of memory|heap size)",
                error_type=ErrorType.MEMORY_LEAK,
                priority=ErrorPriority.CRITICAL,
                suggested_fix="Analyze memory usage and optimize data structures"
            ),
            ErrorPattern(
                pattern_id="connection_error",
                regex=r"(Connection|Socket|Network).*error",
                error_type=ErrorType.NETWORK_ERROR,
                priority=ErrorPriority.HIGH,
                suggested_fix="Check network connectivity and service availability"
            )
        ]
        self.error_patterns = default_patterns

    def _load_recovery_strategies(self):
        """Load recovery strategies from database"""
        strategy_file = Path(self.error_config.recovery_strategies_path)
        if strategy_file.exists():
            try:
                with open(strategy_file, 'r') as f:
                    self.recovery_strategies = json.load(f)
                logger.info(f"Loaded {len(self.recovery_strategies)} recovery strategies")
            except Exception as e:
                logger.error(f"Failed to load recovery strategies: {e}")
                self.recovery_strategies = {}
        else:
            # Initialize with default strategies
            self._initialize_default_strategies()

    def _initialize_default_strategies(self):
        """Initialize default recovery strategies"""
        self.recovery_strategies = {
            "retry_with_backoff": {
                "description": "Retry operation with exponential backoff",
                "max_attempts": 3,
                "initial_delay": 1,
                "applicable_to": [ErrorType.NETWORK_ERROR, ErrorType.API_ERROR]
            },
            "circuit_breaker": {
                "description": "Implement circuit breaker pattern",
                "threshold": 5,
                "timeout": 30,
                "applicable_to": [ErrorType.API_ERROR, ErrorType.DATABASE_ERROR]
            },
            "graceful_degradation": {
                "description": "Provide reduced functionality",
                "fallback_mode": "cached_data",
                "applicable_to": [ErrorType.INTEGRATION_ERROR, ErrorType.API_ERROR]
            },
            "rollback": {
                "description": "Rollback to previous working state",
                "checkpoint_required": True,
                "applicable_to": [ErrorType.CONFIGURATION_ERROR, ErrorType.RUNTIME]
            },
            "auto_fix": {
                "description": "Attempt automatic fix based on patterns",
                "confidence_threshold": 0.8,
                "applicable_to": [ErrorType.SYNTAX, ErrorType.TYPE_ERROR]
            }
        }

    async def detect_error(self, data: Dict[str, Any]) -> ErrorState:
        """
        Detect and classify an error from various sources.

        Args:
            data: Input data containing error information

        Returns:
            ErrorState with classified error information
        """
        # Extract error information
        error_msg = data.get("error_message", "")
        stack_trace = data.get("stack_trace", "")
        file_path = data.get("file_path")
        line_number = data.get("line_number")

        # Classify error type
        error_type = self._classify_error(error_msg, stack_trace)

        # Determine priority
        priority = self._determine_priority(error_type, data)

        # Extract affected components
        affected_components = self._extract_affected_components(stack_trace)

        # Create error state
        error_state: ErrorState = {
            "error_id": self._generate_error_id(),
            "error_type": error_type,
            "priority": priority,
            "description": error_msg,
            "stack_trace": stack_trace,
            "file_path": file_path,
            "line_number": line_number,
            "context": data.get("context", {}),
            "attempted_fixes": [],
            "resolution_status": "detected",
            "timestamp": datetime.now().isoformat(),
            "affected_components": affected_components,
            "potential_impact": self._assess_impact(error_type, priority),
            "recovery_strategy": None,
            "metadata": data.get("metadata", {})
        }

        # Add to history
        self.error_history.append(error_state)

        # Update SPARC state
        await self.state_manager.update_state({
            "current_error": error_state,
            "error_count": len(self.error_history)
        })

        return error_state

    def _classify_error(self, error_msg: str, stack_trace: str) -> ErrorType:
        """Classify error based on message and stack trace"""
        combined_text = f"{error_msg} {stack_trace}".lower()

        # Pattern-based classification
        classification_rules = {
            ErrorType.SYNTAX: ["syntaxerror", "unexpected token", "invalid syntax"],
            ErrorType.RUNTIME: ["runtimeerror", "exception", "error occurred"],
            ErrorType.TYPE_ERROR: ["typeerror", "type mismatch", "incompatible type"],
            ErrorType.DEPENDENCY: ["importerror", "modulenotfound", "cannot import"],
            ErrorType.MEMORY_LEAK: ["memoryerror", "out of memory", "heap"],
            ErrorType.NETWORK_ERROR: ["connection", "socket", "timeout", "network"],
            ErrorType.DATABASE_ERROR: ["database", "sql", "query failed"],
            ErrorType.SECURITY: ["security", "vulnerability", "unauthorized"],
            ErrorType.PERFORMANCE: ["timeout", "slow", "performance"],
            ErrorType.CONFIGURATION: ["config", "setting", "environment"]
        }

        for error_type, keywords in classification_rules.items():
            if any(keyword in combined_text for keyword in keywords):
                return error_type

        return ErrorType.RUNTIME  # Default

    def _determine_priority(self, error_type: ErrorType, data: Dict[str, Any]) -> ErrorPriority:
        """Determine error priority based on type and context"""
        # Critical types
        if error_type in [ErrorType.SECURITY, ErrorType.MEMORY_LEAK, ErrorType.DATABASE_ERROR]:
            return ErrorPriority.CRITICAL

        # Check for production environment
        if data.get("environment") == "production":
            return ErrorPriority.HIGH

        # Check error frequency
        frequency = data.get("frequency", 1)
        if frequency > 10:
            return ErrorPriority.HIGH
        elif frequency > 5:
            return ErrorPriority.MEDIUM

        # Default priorities by type
        priority_map = {
            ErrorType.SYNTAX: ErrorPriority.LOW,
            ErrorType.TYPE_ERROR: ErrorPriority.MEDIUM,
            ErrorType.RUNTIME: ErrorPriority.MEDIUM,
            ErrorType.DEPENDENCY: ErrorPriority.HIGH,
            ErrorType.NETWORK_ERROR: ErrorPriority.MEDIUM,
            ErrorType.PERFORMANCE: ErrorPriority.LOW,
            ErrorType.CONFIGURATION: ErrorPriority.MEDIUM
        }

        return priority_map.get(error_type, ErrorPriority.MEDIUM)

    def _extract_affected_components(self, stack_trace: str) -> List[str]:
        """Extract affected components from stack trace"""
        components = []

        # Extract file paths from stack trace
        file_pattern = r'File "([^"]+)"'
        files = re.findall(file_pattern, stack_trace)

        for file in files:
            # Extract component name from path
            if "/" in file:
                parts = file.split("/")
                # Look for key directories
                for i, part in enumerate(parts):
                    if part in ["core", "apps", "database", "scripts"]:
                        if i + 1 < len(parts):
                            components.append(f"{part}/{parts[i+1]}")
                        break

        return list(set(components))  # Remove duplicates

    def _assess_impact(self, error_type: ErrorType, priority: ErrorPriority) -> str:
        """Assess potential impact of the error"""
        impact_levels = {
            ErrorPriority.EMERGENCY: "System-wide failure imminent",
            ErrorPriority.CRITICAL: "Major functionality compromised",
            ErrorPriority.HIGH: "Significant feature degradation",
            ErrorPriority.MEDIUM: "Minor feature affected",
            ErrorPriority.LOW: "Minimal user impact"
        }

        base_impact = impact_levels.get(priority, "Unknown impact")

        # Add type-specific impact
        type_impacts = {
            ErrorType.SECURITY: " - Security breach possible",
            ErrorType.DATABASE_ERROR: " - Data integrity at risk",
            ErrorType.MEMORY_LEAK: " - System resources depleting",
            ErrorType.DEADLOCK: " - Process frozen",
            ErrorType.API_ERROR: " - External integrations failing"
        }

        if error_type in type_impacts:
            base_impact += type_impacts[error_type]

        return base_impact

    def _generate_error_id(self) -> str:
        """Generate unique error ID"""
        import uuid
        return f"ERR-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8]}"

    async def suggest_fix(self, error_state: ErrorState) -> Dict[str, Any]:
        """
        Suggest fix for the given error.

        Args:
            error_state: Current error state

        Returns:
            Dictionary containing suggested fixes and confidence levels
        """
        suggestions = []

        # Check against known patterns
        for pattern in self.error_patterns:
            if re.search(pattern.regex, error_state["description"], re.IGNORECASE):
                suggestions.append({
                    "fix": pattern.suggested_fix,
                    "confidence": pattern.success_rate,
                    "pattern_id": pattern.pattern_id,
                    "previous_success_rate": pattern.success_rate
                })

        # Add type-specific suggestions
        type_suggestions = self._get_type_specific_suggestions(error_state["error_type"])
        suggestions.extend(type_suggestions)

        # Sort by confidence
        suggestions.sort(key=lambda x: x.get("confidence", 0), reverse=True)

        return {
            "error_id": error_state["error_id"],
            "suggestions": suggestions[:5],  # Top 5 suggestions
            "recommended": suggestions[0] if suggestions else None,
            "recovery_strategy": self._select_recovery_strategy(error_state)
        }

    def _get_type_specific_suggestions(self, error_type: ErrorType) -> List[Dict[str, Any]]:
        """Get type-specific fix suggestions"""
        suggestions = []

        type_fixes = {
            ErrorType.SYNTAX: [
                {"fix": "Check for missing brackets, quotes, or semicolons", "confidence": 0.7},
                {"fix": "Verify indentation is consistent", "confidence": 0.6}
            ],
            ErrorType.TYPE_ERROR: [
                {"fix": "Add type checking before operations", "confidence": 0.8},
                {"fix": "Convert types explicitly", "confidence": 0.7}
            ],
            ErrorType.DEPENDENCY: [
                {"fix": "Run pip install for missing packages", "confidence": 0.9},
                {"fix": "Check virtual environment activation", "confidence": 0.8}
            ],
            ErrorType.NETWORK_ERROR: [
                {"fix": "Implement retry with exponential backoff", "confidence": 0.8},
                {"fix": "Check network connectivity and firewall rules", "confidence": 0.7}
            ]
        }

        return type_fixes.get(error_type, [])

    def _select_recovery_strategy(self, error_state: ErrorState) -> Optional[str]:
        """Select appropriate recovery strategy for the error"""
        error_type = error_state["error_type"]

        for strategy_name, strategy_info in self.recovery_strategies.items():
            if error_type in strategy_info.get("applicable_to", []):
                return strategy_name

        return None

    # Tool implementation methods
    def _detect_error_tool(self, input_str: str) -> str:
        """Tool for detecting errors in code or logs"""
        # Simplified implementation for tool
        return f"Detected error in: {input_str[:100]}..."

    def _analyze_stack_trace_tool(self, stack_trace: str) -> str:
        """Tool for analyzing stack traces"""
        components = self._extract_affected_components(stack_trace)
        return f"Affected components: {', '.join(components)}"

    def _suggest_fix_tool(self, error_description: str) -> str:
        """Tool for suggesting fixes"""
        # Match against patterns
        for pattern in self.error_patterns:
            if re.search(pattern.regex, error_description, re.IGNORECASE):
                return pattern.suggested_fix or "No specific fix available"
        return "No matching pattern found"

    def _match_pattern_tool(self, error_msg: str) -> str:
        """Tool for matching error patterns"""
        matches = []
        for pattern in self.error_patterns:
            if re.search(pattern.regex, error_msg, re.IGNORECASE):
                matches.append(pattern.pattern_id)
        return f"Matched patterns: {', '.join(matches)}" if matches else "No patterns matched"

    def _select_recovery_strategy_tool(self, error_type_str: str) -> str:
        """Tool for selecting recovery strategy"""
        try:
            error_type = ErrorType[error_type_str.upper()]
            for strategy_name, strategy_info in self.recovery_strategies.items():
                if error_type in strategy_info.get("applicable_to", []):
                    return f"Recommended strategy: {strategy_name} - {strategy_info['description']}"
        except KeyError:
            pass
        return "No specific recovery strategy recommended"

    async def learn_from_resolution(self, error_id: str, fix_applied: str, success: bool):
        """
        Learn from error resolution attempts.

        Args:
            error_id: ID of the error that was addressed
            fix_applied: Description of the fix that was applied
            success: Whether the fix was successful
        """
        # Find the error in history
        error_state = next((e for e in self.error_history if e["error_id"] == error_id), None)

        if not error_state:
            logger.warning(f"Error {error_id} not found in history")
            return

        # Update pattern success rates
        for pattern in self.error_patterns:
            if re.search(pattern.regex, error_state["description"], re.IGNORECASE):
                # Update frequency
                pattern.frequency += 1
                pattern.last_seen = datetime.now().isoformat()

                # Update success rate
                if success:
                    pattern.success_rate = (pattern.success_rate * (pattern.frequency - 1) + 1.0) / pattern.frequency
                else:
                    pattern.success_rate = (pattern.success_rate * (pattern.frequency - 1)) / pattern.frequency

        # Update error state
        error_state["attempted_fixes"].append({
            "fix": fix_applied,
            "success": success,
            "timestamp": datetime.now().isoformat()
        })

        if success:
            error_state["resolution_status"] = "resolved"

        # Update SPARC reward system
        reward = 1.0 if success else -0.5
        await self.reward_system.update_reward(
            action=f"fix_{error_state['error_type'].value}",
            reward=reward,
            context={"error_id": error_id, "fix": fix_applied}
        )

        # Save updated patterns
        self._save_patterns()

    def _save_patterns(self):
        """Save error patterns to database"""
        pattern_file = Path(self.error_config.pattern_database_path)
        pattern_file.parent.mkdir(parents=True, exist_ok=True)

        try:
            patterns_data = [p.model_dump() for p in self.error_patterns]
            with open(pattern_file, 'w') as f:
                json.dump(patterns_data, f, indent=2, default=str)
            logger.info(f"Saved {len(self.error_patterns)} error patterns")
        except Exception as e:
            logger.error(f"Failed to save error patterns: {e}")

    async def get_error_metrics(self) -> Dict[str, Any]:
        """Get metrics about error handling performance"""
        metrics = {
            "total_errors_handled": len(self.error_history),
            "patterns_learned": len(self.error_patterns),
            "resolution_rate": 0.0,
            "average_resolution_time": 0.0,
            "error_type_distribution": {},
            "priority_distribution": {},
            "top_patterns": [],
            "recovery_strategy_usage": {}
        }

        if self.error_history:
            # Calculate resolution rate
            resolved = sum(1 for e in self.error_history if e["resolution_status"] == "resolved")
            metrics["resolution_rate"] = resolved / len(self.error_history)

            # Calculate distributions
            for error in self.error_history:
                # Error type distribution
                error_type = error["error_type"].value
                metrics["error_type_distribution"][error_type] = \
                    metrics["error_type_distribution"].get(error_type, 0) + 1

                # Priority distribution
                priority = error["priority"].value
                metrics["priority_distribution"][priority] = \
                    metrics["priority_distribution"].get(priority, 0) + 1

                # Recovery strategy usage
                if error.get("recovery_strategy"):
                    strategy = error["recovery_strategy"]
                    metrics["recovery_strategy_usage"][strategy] = \
                        metrics["recovery_strategy_usage"].get(strategy, 0) + 1

            # Top patterns by frequency
            top_patterns = sorted(self.error_patterns, key=lambda p: p.frequency, reverse=True)[:5]
            metrics["top_patterns"] = [
                {
                    "pattern_id": p.pattern_id,
                    "frequency": p.frequency,
                    "success_rate": p.success_rate
                }
                for p in top_patterns
            ]

        return metrics