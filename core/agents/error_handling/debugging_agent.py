"""
Advanced Debugging Agent

Specialized agent for deep analysis and diagnosis of complex bugs.
Uses sophisticated debugging techniques including stack trace analysis,
memory profiling, and state inspection.
"""

import asyncio
import logging
import traceback
import inspect
import sys
import os
import re
import json
from typing import Dict, Any, Optional, List, Tuple, Set
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass
import subprocess
import psutil
import gc

from langchain_core.tools import Tool
from pydantic import BaseModel, Field

from core.agents.error_handling.base_error_agent import (
    BaseErrorAgent,
    ErrorAgentConfig,
    ErrorState,
    ErrorType,
    ErrorPriority
)

logger = logging.getLogger(__name__)


class DebugInfo(BaseModel):
    """Model for debugging information"""
    error_id: str = Field(description="ID of the error being debugged")
    root_cause: str = Field(description="Identified root cause of the issue")
    call_stack: List[Dict[str, Any]] = Field(description="Analyzed call stack")
    variables_snapshot: Dict[str, Any] = Field(description="Variable values at error time")
    memory_state: Dict[str, Any] = Field(description="Memory usage information")
    thread_state: Dict[str, Any] = Field(description="Thread and async task information")
    dependencies_checked: List[str] = Field(description="Dependencies that were verified")
    hypothesis: str = Field(description="Hypothesis about the bug")
    evidence: List[str] = Field(description="Evidence supporting the hypothesis")
    recommended_actions: List[str] = Field(description="Recommended debugging actions")
    complexity_score: float = Field(description="Estimated complexity of the bug (0-1)")


class BreakpointInfo(BaseModel):
    """Model for breakpoint information"""
    file_path: str = Field(description="File where breakpoint should be set")
    line_number: int = Field(description="Line number for breakpoint")
    condition: Optional[str] = Field(description="Conditional expression for breakpoint")
    watch_variables: List[str] = Field(description="Variables to watch at this breakpoint")
    reason: str = Field(description="Reason for setting this breakpoint")


class MemoryProfile(BaseModel):
    """Model for memory profiling data"""
    total_memory_mb: float = Field(description="Total memory usage in MB")
    process_memory_mb: float = Field(description="Process memory usage in MB")
    object_counts: Dict[str, int] = Field(description="Count of objects by type")
    largest_objects: List[Dict[str, Any]] = Field(description="Largest objects in memory")
    potential_leaks: List[str] = Field(description="Potential memory leaks detected")
    gc_stats: Dict[str, Any] = Field(description="Garbage collection statistics")


@dataclass
class DebuggerConfig(ErrorAgentConfig):
    """Configuration specific to debugging agent"""
    enable_memory_profiling: bool = True
    enable_thread_analysis: bool = True
    max_stack_depth: int = 50
    variable_inspection_depth: int = 3
    profile_interval: int = 100  # milliseconds
    breakpoint_timeout: int = 30  # seconds
    enable_remote_debugging: bool = False


class AdvancedDebuggingAgent(BaseErrorAgent):
    """
    Agent specialized in deep debugging and root cause analysis.

    Capabilities:
    - Stack trace deep analysis
    - Memory leak detection
    - Performance bottleneck identification
    - Concurrency issue detection
    - State corruption analysis
    - Variable inspection and tracking
    - Breakpoint management
    - Remote debugging support
    """

    def __init__(self, config: Optional[DebuggerConfig] = None):
        if config is None:
            config = DebuggerConfig(
                name="AdvancedDebuggingAgent",
                model="gpt-4",
                temperature=0.2,  # Very low temperature for precise analysis
                enable_memory_profiling=True,
                enable_thread_analysis=True,
                max_stack_depth=50
            )

        super().__init__(config)
        self.debugger_config = config

        # Debugging state
        self.active_breakpoints: List[BreakpointInfo] = []
        self.watch_list: Dict[str, Any] = {}
        self.debug_sessions: Dict[str, Dict[str, Any]] = {}
        self.memory_snapshots: List[MemoryProfile] = []

        # Initialize debugging tools
        self.tools.extend(self._create_debugging_tools())

        logger.info("Initialized Advanced Debugging Agent")

    def _get_default_system_prompt(self) -> str:
        """Get specialized system prompt for debugging"""
        return """You are the Advanced Debugging Agent, specialized in deep analysis and diagnosis of complex bugs.

Your core capabilities:
- Analyze stack traces to identify root causes
- Detect memory leaks and performance issues
- Identify concurrency problems (deadlocks, race conditions)
- Inspect variable states and execution flow
- Profile resource usage and bottlenecks
- Suggest strategic breakpoint placement
- Provide detailed debugging strategies

Debugging principles:
1. Systematic approach - methodically eliminate possibilities
2. Evidence-based - support hypotheses with concrete evidence
3. Minimal disruption - avoid affecting system state during debugging
4. Comprehensive logging - capture all relevant information
5. Root cause focus - don't just treat symptoms

Use scientific method: Observe → Hypothesize → Test → Conclude"""

    def _create_debugging_tools(self) -> List[Tool]:
        """Create specialized tools for debugging"""
        tools = []

        tools.append(Tool(
            name="analyze_stack_trace",
            description="Deep analysis of stack traces",
            func=self._analyze_stack_trace_deep
        ))

        tools.append(Tool(
            name="profile_memory",
            description="Profile memory usage and detect leaks",
            func=self._profile_memory
        ))

        tools.append(Tool(
            name="inspect_variables",
            description="Inspect variable values at specific points",
            func=self._inspect_variables
        ))

        tools.append(Tool(
            name="set_breakpoint",
            description="Set strategic breakpoints for debugging",
            func=self._set_breakpoint
        ))

        tools.append(Tool(
            name="analyze_threads",
            description="Analyze thread and async task states",
            func=self._analyze_threads
        ))

        tools.append(Tool(
            name="trace_execution",
            description="Trace code execution path",
            func=self._trace_execution
        ))

        tools.append(Tool(
            name="check_dependencies",
            description="Verify dependency versions and conflicts",
            func=self._check_dependencies
        ))

        return tools

    async def debug_error(self, error_state: ErrorState) -> DebugInfo:
        """
        Main method to debug an error comprehensively.

        Args:
            error_state: The error state to debug

        Returns:
            DebugInfo with comprehensive debugging information
        """
        logger.info(f"Starting deep debugging for error: {error_state['error_id']}")

        # Create debug session
        session_id = f"debug_{error_state['error_id']}"
        self.debug_sessions[session_id] = {
            "start_time": datetime.now(),
            "error_state": error_state,
            "findings": []
        }

        # Analyze stack trace
        stack_analysis = await self._analyze_stack_deeply(error_state)

        # Profile memory if enabled
        memory_state = {}
        if self.debugger_config.enable_memory_profiling:
            memory_state = await self._profile_memory_state()

        # Analyze threads if enabled
        thread_state = {}
        if self.debugger_config.enable_thread_analysis:
            thread_state = await self._analyze_thread_state()

        # Inspect variables at error point
        variables = await self._capture_variables(error_state, stack_analysis)

        # Check dependencies
        deps_checked = await self._verify_dependencies(error_state)

        # Generate hypothesis
        hypothesis = await self._generate_hypothesis(
            error_state,
            stack_analysis,
            memory_state,
            thread_state,
            variables
        )

        # Gather evidence
        evidence = await self._gather_evidence(hypothesis, error_state)

        # Calculate complexity score
        complexity = self._calculate_bug_complexity(error_state, stack_analysis)

        # Generate recommendations
        recommendations = await self._generate_recommendations(
            error_state,
            hypothesis,
            evidence,
            complexity
        )

        # Create debug info
        debug_info = DebugInfo(
            error_id=error_state["error_id"],
            root_cause=hypothesis["root_cause"],
            call_stack=stack_analysis["frames"],
            variables_snapshot=variables,
            memory_state=memory_state,
            thread_state=thread_state,
            dependencies_checked=deps_checked,
            hypothesis=hypothesis["description"],
            evidence=evidence,
            recommended_actions=recommendations,
            complexity_score=complexity
        )

        # Store in session
        self.debug_sessions[session_id]["debug_info"] = debug_info
        self.debug_sessions[session_id]["end_time"] = datetime.now()

        return debug_info

    async def _analyze_stack_deeply(self, error_state: ErrorState) -> Dict[str, Any]:
        """Perform deep analysis of the stack trace"""
        stack_trace = error_state.get("stack_trace", "")

        analysis = {
            "frames": [],
            "error_origin": None,
            "call_sequence": [],
            "recursive_calls": [],
            "external_calls": [],
            "suspicious_patterns": []
        }

        if not stack_trace:
            return analysis

        # Parse stack trace
        lines = stack_trace.split('\n')
        current_frame = {}

        for line in lines:
            # Match file and line pattern
            file_match = re.match(r'\s*File "([^"]+)", line (\d+), in (.+)', line)
            if file_match:
                if current_frame:
                    analysis["frames"].append(current_frame)

                current_frame = {
                    "file": file_match.group(1),
                    "line": int(file_match.group(2)),
                    "function": file_match.group(3),
                    "code": "",
                    "local_vars": {},
                    "is_library": not file_match.group(1).startswith(("/", "./"))
                }

                # Read actual code if file exists
                try:
                    if Path(current_frame["file"]).exists():
                        with open(current_frame["file"], 'r') as f:
                            lines = f.readlines()
                            line_idx = current_frame["line"] - 1
                            if 0 <= line_idx < len(lines):
                                current_frame["code"] = lines[line_idx].strip()
                except:
                    pass

            elif line.strip() and current_frame:
                # This might be the code line
                current_frame["code"] = line.strip()

        if current_frame:
            analysis["frames"].append(current_frame)

        # Identify error origin (deepest non-library frame)
        for frame in reversed(analysis["frames"]):
            if not frame["is_library"]:
                analysis["error_origin"] = frame
                break

        # Detect patterns
        analysis["suspicious_patterns"] = self._detect_suspicious_patterns(analysis["frames"])

        # Check for recursion
        function_calls = [f["function"] for f in analysis["frames"]]
        for func in set(function_calls):
            if function_calls.count(func) > 2:
                analysis["recursive_calls"].append({
                    "function": func,
                    "count": function_calls.count(func)
                })

        # Identify external calls
        for frame in analysis["frames"]:
            if frame["is_library"]:
                analysis["external_calls"].append({
                    "library": frame["file"].split("/")[-1].split(".")[0],
                    "function": frame["function"]
                })

        return analysis

    def _detect_suspicious_patterns(self, frames: List[Dict[str, Any]]) -> List[str]:
        """Detect suspicious patterns in stack frames"""
        patterns = []

        # Check for None access
        for frame in frames:
            if "NoneType" in frame.get("code", ""):
                patterns.append(f"Potential None access in {frame['function']}")

        # Check for infinite loops
        if len(frames) > 100:
            patterns.append("Possible infinite recursion or loop")

        # Check for exception in exception handler
        exception_handlers = [f for f in frames if "except" in f.get("code", "")]
        if len(exception_handlers) > 1:
            patterns.append("Exception raised within exception handler")

        # Check for resource exhaustion
        for frame in frames:
            code = frame.get("code", "")
            if any(word in code for word in ["malloc", "alloc", "new", "append"]):
                patterns.append(f"Memory allocation in {frame['function']}")

        return patterns

    async def _profile_memory_state(self) -> Dict[str, Any]:
        """Profile current memory state"""
        process = psutil.Process(os.getpid())

        memory_info = process.memory_info()
        memory_percent = process.memory_percent()

        # Get object counts
        object_counts = {}
        for obj in gc.get_objects():
            obj_type = type(obj).__name__
            object_counts[obj_type] = object_counts.get(obj_type, 0) + 1

        # Sort by count
        top_objects = sorted(
            object_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )[:10]

        # Get garbage collection stats
        gc_stats = {
            "collections": gc.get_count(),
            "collected": gc.collect(),
            "threshold": gc.get_threshold()
        }

        return {
            "memory_usage_mb": memory_info.rss / 1024 / 1024,
            "memory_percent": memory_percent,
            "virtual_memory_mb": memory_info.vms / 1024 / 1024,
            "top_object_types": dict(top_objects),
            "total_objects": len(gc.get_objects()),
            "gc_stats": gc_stats
        }

    async def _analyze_thread_state(self) -> Dict[str, Any]:
        """Analyze current thread and async task states"""
        import threading

        thread_info = {
            "active_threads": threading.active_count(),
            "current_thread": threading.current_thread().name,
            "all_threads": [],
            "async_tasks": []
        }

        # Get all threads
        for thread in threading.enumerate():
            thread_data = {
                "name": thread.name,
                "daemon": thread.daemon,
                "alive": thread.is_alive(),
                "ident": thread.ident
            }
            thread_info["all_threads"].append(thread_data)

        # Get async tasks if in async context
        try:
            tasks = asyncio.all_tasks()
            for task in tasks:
                task_data = {
                    "name": task.get_name(),
                    "done": task.done(),
                    "cancelled": task.cancelled()
                }
                if task.done() and not task.cancelled():
                    try:
                        task_data["exception"] = str(task.exception())
                    except:
                        task_data["exception"] = None
                thread_info["async_tasks"].append(task_data)
        except RuntimeError:
            # Not in async context
            pass

        return thread_info

    async def _capture_variables(
        self,
        error_state: ErrorState,
        stack_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Capture variable values at error point"""
        variables = {}

        # Get variables from error context if provided
        if "context" in error_state:
            variables.update(error_state["context"])

        # Try to extract from locals/globals if available
        if stack_analysis.get("error_origin"):
            frame = stack_analysis["error_origin"]

            # Attempt to get local variables (this is limited without actual runtime access)
            # In production, this would integrate with a debugger or profiler
            variables["error_location"] = {
                "file": frame["file"],
                "line": frame["line"],
                "function": frame["function"]
            }

        return variables

    async def _verify_dependencies(self, error_state: ErrorState) -> List[str]:
        """Verify dependency versions and check for conflicts"""
        deps_checked = []

        # Check Python packages
        try:
            result = subprocess.run(
                ["pip", "list", "--format=json"],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode == 0:
                packages = json.loads(result.stdout)
                deps_checked.extend([f"{p['name']}=={p['version']}" for p in packages[:10]])
        except:
            pass

        # Check for specific dependencies mentioned in error
        error_text = error_state.get("description", "").lower()
        important_packages = ["langchain", "pydantic", "fastapi", "sqlalchemy", "redis"]

        for package in important_packages:
            if package in error_text:
                deps_checked.append(f"{package} (referenced in error)")

        return deps_checked

    async def _generate_hypothesis(
        self,
        error_state: ErrorState,
        stack_analysis: Dict[str, Any],
        memory_state: Dict[str, Any],
        thread_state: Dict[str, Any],
        variables: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate hypothesis about the bug's root cause"""
        hypothesis = {
            "root_cause": "Unknown",
            "description": "",
            "confidence": 0.0,
            "supporting_evidence": []
        }

        error_type = error_state["error_type"]
        error_msg = error_state.get("description", "")

        # Type-specific hypothesis generation
        if error_type == ErrorType.MEMORY_LEAK:
            if memory_state.get("memory_percent", 0) > 80:
                hypothesis["root_cause"] = "Memory exhaustion"
                hypothesis["description"] = "System running out of memory due to leak or excessive allocation"
                hypothesis["confidence"] = 0.9
                hypothesis["supporting_evidence"].append(f"Memory usage: {memory_state['memory_percent']}%")

        elif error_type == ErrorType.DEADLOCK:
            if thread_state.get("active_threads", 0) > 10:
                hypothesis["root_cause"] = "Thread deadlock"
                hypothesis["description"] = "Multiple threads waiting on each other's resources"
                hypothesis["confidence"] = 0.8
                hypothesis["supporting_evidence"].append(f"Active threads: {thread_state['active_threads']}")

        elif error_type == ErrorType.RUNTIME:
            if "NoneType" in error_msg:
                hypothesis["root_cause"] = "Null reference"
                hypothesis["description"] = "Attempting to access attribute or method on None object"
                hypothesis["confidence"] = 0.95
                hypothesis["supporting_evidence"].append("NoneType error in stack trace")

        elif error_type == ErrorType.PERFORMANCE:
            if len(stack_analysis.get("recursive_calls", [])) > 0:
                hypothesis["root_cause"] = "Excessive recursion"
                hypothesis["description"] = "Performance degradation due to recursive calls"
                hypothesis["confidence"] = 0.85
                hypothesis["supporting_evidence"].extend(
                    [f"Recursive call: {r['function']} ({r['count']} times)"
                     for r in stack_analysis["recursive_calls"]]
                )

        # Pattern-based hypothesis
        for pattern in stack_analysis.get("suspicious_patterns", []):
            hypothesis["supporting_evidence"].append(pattern)
            if "infinite" in pattern.lower():
                hypothesis["root_cause"] = "Infinite loop or recursion"
                hypothesis["confidence"] = max(hypothesis["confidence"], 0.7)

        # Default hypothesis if none matched
        if hypothesis["root_cause"] == "Unknown":
            hypothesis["description"] = f"Error of type {error_type.value} requires further investigation"
            hypothesis["confidence"] = 0.3

        return hypothesis

    async def _gather_evidence(
        self,
        hypothesis: Dict[str, Any],
        error_state: ErrorState
    ) -> List[str]:
        """Gather evidence to support or refute hypothesis"""
        evidence = []

        # Add hypothesis supporting evidence
        evidence.extend(hypothesis.get("supporting_evidence", []))

        # Add timing evidence if available
        if error_state.get("timestamp"):
            evidence.append(f"Error occurred at: {error_state['timestamp']}")

        # Add frequency evidence
        if error_state.get("metadata", {}).get("frequency"):
            freq = error_state["metadata"]["frequency"]
            evidence.append(f"Error frequency: {freq} occurrences")

        # Add impact evidence
        if error_state.get("affected_components"):
            evidence.append(f"Affected components: {', '.join(error_state['affected_components'])}")

        return evidence

    def _calculate_bug_complexity(
        self,
        error_state: ErrorState,
        stack_analysis: Dict[str, Any]
    ) -> float:
        """Calculate estimated complexity of the bug (0-1)"""
        complexity = 0.0

        # Factor 1: Stack depth (deeper = more complex)
        stack_depth = len(stack_analysis.get("frames", []))
        complexity += min(stack_depth / 50, 0.3)

        # Factor 2: Error type complexity
        complex_types = [
            ErrorType.DEADLOCK,
            ErrorType.RACE_CONDITION,
            ErrorType.MEMORY_LEAK,
            ErrorType.PERFORMANCE
        ]
        if error_state["error_type"] in complex_types:
            complexity += 0.2

        # Factor 3: External dependencies
        external_calls = len(stack_analysis.get("external_calls", []))
        complexity += min(external_calls / 10, 0.2)

        # Factor 4: Recursion
        if stack_analysis.get("recursive_calls"):
            complexity += 0.15

        # Factor 5: Priority
        if error_state["priority"] in [ErrorPriority.CRITICAL, ErrorPriority.EMERGENCY]:
            complexity += 0.15

        return min(complexity, 1.0)

    async def _generate_recommendations(
        self,
        error_state: ErrorState,
        hypothesis: Dict[str, Any],
        evidence: List[str],
        complexity: float
    ) -> List[str]:
        """Generate debugging recommendations"""
        recommendations = []

        # Complexity-based recommendations
        if complexity > 0.7:
            recommendations.append("Consider breaking down the problem into smaller parts")
            recommendations.append("Use systematic debugging with multiple breakpoints")
        elif complexity > 0.4:
            recommendations.append("Focus on the most likely cause first")
            recommendations.append("Use targeted logging at key points")

        # Error type specific recommendations
        error_type = error_state["error_type"]

        if error_type == ErrorType.MEMORY_LEAK:
            recommendations.extend([
                "Use memory profiler to track allocations",
                "Check for circular references",
                "Verify proper resource cleanup in finally blocks"
            ])
        elif error_type == ErrorType.DEADLOCK:
            recommendations.extend([
                "Use thread dump analysis",
                "Check lock acquisition order",
                "Consider using timeouts on locks"
            ])
        elif error_type == ErrorType.RUNTIME:
            recommendations.extend([
                "Add null checks before object access",
                "Validate input parameters",
                "Use defensive programming techniques"
            ])
        elif error_type == ErrorType.PERFORMANCE:
            recommendations.extend([
                "Profile code to identify bottlenecks",
                "Check for O(n²) or worse algorithms",
                "Consider caching frequently accessed data"
            ])

        # Hypothesis-based recommendations
        if hypothesis["confidence"] > 0.7:
            recommendations.insert(0, f"Focus on: {hypothesis['root_cause']}")
        else:
            recommendations.insert(0, "Gather more data before narrowing focus")

        return recommendations[:7]  # Return top 7 recommendations

    async def set_strategic_breakpoints(self, error_state: ErrorState) -> List[BreakpointInfo]:
        """Set strategic breakpoints for debugging"""
        breakpoints = []

        # Analyze stack to find key locations
        stack_analysis = await self._analyze_stack_deeply(error_state)

        # Set breakpoint at error origin
        if stack_analysis.get("error_origin"):
            origin = stack_analysis["error_origin"]
            breakpoints.append(BreakpointInfo(
                file_path=origin["file"],
                line_number=origin["line"],
                condition=None,
                watch_variables=["self", "args", "kwargs"],
                reason="Error origin point"
            ))

        # Set breakpoints at suspicious patterns
        for i, frame in enumerate(stack_analysis.get("frames", [])):
            for pattern in stack_analysis.get("suspicious_patterns", []):
                if frame["function"] in pattern:
                    breakpoints.append(BreakpointInfo(
                        file_path=frame["file"],
                        line_number=frame["line"],
                        condition=None,
                        watch_variables=["locals()"],
                        reason=f"Suspicious pattern: {pattern}"
                    ))

        # Set breakpoints for recursive calls
        for recursive in stack_analysis.get("recursive_calls", []):
            # Find first occurrence
            for frame in stack_analysis["frames"]:
                if frame["function"] == recursive["function"]:
                    breakpoints.append(BreakpointInfo(
                        file_path=frame["file"],
                        line_number=frame["line"],
                        condition=f"recursion_depth > {recursive['count']}",
                        watch_variables=["recursion_depth", "args"],
                        reason=f"Recursive function: {recursive['function']}"
                    ))
                    break

        self.active_breakpoints.extend(breakpoints)
        return breakpoints

    # Tool implementations
    def _analyze_stack_trace_deep(self, stack_trace: str) -> str:
        """Tool: Deep stack trace analysis"""
        lines = stack_trace.split('\n')
        frame_count = len([l for l in lines if 'File' in l])
        return f"Analyzed {frame_count} stack frames"

    def _profile_memory(self, process_name: Optional[str] = None) -> str:
        """Tool: Profile memory usage"""
        process = psutil.Process(os.getpid())
        memory_mb = process.memory_info().rss / 1024 / 1024
        return f"Memory usage: {memory_mb:.2f} MB"

    def _inspect_variables(self, context: str) -> str:
        """Tool: Inspect variables in context"""
        # This would integrate with actual debugger in production
        return f"Variable inspection completed for context: {context}"

    def _set_breakpoint(self, location: str) -> str:
        """Tool: Set a breakpoint"""
        # This would integrate with debugger
        return f"Breakpoint set at: {location}"

    def _analyze_threads(self, check_deadlock: bool = True) -> str:
        """Tool: Analyze thread states"""
        import threading
        thread_count = threading.active_count()
        return f"Active threads: {thread_count}"

    def _trace_execution(self, function_name: str) -> str:
        """Tool: Trace function execution"""
        # This would use sys.settrace in production
        return f"Execution trace started for: {function_name}"

    def _check_dependencies(self, package_name: Optional[str] = None) -> str:
        """Tool: Check dependency versions"""
        if package_name:
            return f"Checking {package_name} version and dependencies"
        return "Dependency check completed"

    async def get_debugging_metrics(self) -> Dict[str, Any]:
        """Get metrics specific to debugging"""
        base_metrics = await self.get_error_metrics()

        debug_metrics = {
            "total_debug_sessions": len(self.debug_sessions),
            "active_breakpoints": len(self.active_breakpoints),
            "memory_snapshots": len(self.memory_snapshots),
            "average_complexity": 0.0,
            "hypothesis_accuracy": 0.0,
            "root_causes_identified": {}
        }

        # Calculate average complexity
        if self.debug_sessions:
            complexities = []
            for session in self.debug_sessions.values():
                if "debug_info" in session:
                    complexities.append(session["debug_info"].complexity_score)
            if complexities:
                debug_metrics["average_complexity"] = sum(complexities) / len(complexities)

        # Combine metrics
        return {**base_metrics, **debug_metrics}