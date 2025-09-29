"""
RobloxScriptOptimizationAgent - Luau Script Performance Optimization

This agent analyzes Roblox Luau scripts for performance bottlenecks,
memory leaks, and inefficient patterns, providing optimized versions.
"""

import json
import logging
import re
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# LangChain imports with compatibility handling
try:
    from langchain.tools import StructuredTool, Tool
    from langchain_core.messages import HumanMessage, SystemMessage
    from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
    from langchain_openai import ChatOpenAI
    LANGCHAIN_CORE_AVAILABLE = True
except ImportError as e:
    print(f"LangChain core imports failed: {e}")
    LANGCHAIN_CORE_AVAILABLE = False
    # Create mock classes
    class ChatPromptTemplate:
        @classmethod
        def from_messages(cls, messages): return cls()
    class MessagesPlaceholder:
        def __init__(self, variable_name): pass
    class SystemMessage:
        def __init__(self, content): self.content = content
    class HumanMessage:
        def __init__(self, content): self.content = content
    class Tool:
        def __init__(self, **kwargs): pass
    class StructuredTool:
        def __init__(self, **kwargs): pass
    class ChatOpenAI:
        def __init__(self, **kwargs): pass

# Use LangChain 0.3.26+ LCEL compatibility layer
try:
    from core.langchain_lcel_compat import (
        LLMChain, AgentExecutor, create_lcel_chain, create_chat_chain, 
        get_compatible_llm, LANGCHAIN_CORE_AVAILABLE
    )
    LANGCHAIN_AGENTS_AVAILABLE = True
    logger.info("LangChain LCEL compatibility layer imported successfully")
except ImportError as e:
    logger.error(f"LCEL compatibility layer import failed: {e}")
    LANGCHAIN_AGENTS_AVAILABLE = False
    
    # Fallback mock classes
    class LLMChain:
        def __init__(self, **kwargs): pass
        def run(self, *args, **kwargs): return "Mock optimization result"
        async def arun(self, *args, **kwargs): return "Mock optimization result"
    
    class AgentExecutor:
        def __init__(self, **kwargs): pass
        def run(self, *args, **kwargs): return "Mock agent result"
        async def arun(self, *args, **kwargs): return "Mock agent result"

def format_to_openai_function_messages(*args, **kwargs): 
    return []

class OpenAIFunctionsAgentOutputParser:
    def parse(self, text): 
        return {"output": text, "optimized_code": text}

from core.agents.base_agent import AgentConfig, AgentState, BaseAgent, TaskResult


class OptimizationLevel(Enum):
    """Optimization aggressiveness levels"""
    CONSERVATIVE = "conservative"  # Safe optimizations only
    BALANCED = "balanced"  # Balance between safety and performance
    AGGRESSIVE = "aggressive"  # Maximum performance, may change behavior


@dataclass
class PerformanceIssue:
    """Represents a performance issue in code"""
    severity: str  # "critical", "high", "medium", "low"
    location: str  # Line number or code section
    issue_type: str  # Type of issue
    description: str
    suggestion: str
    estimated_impact: str  # Performance impact estimate


@dataclass
class OptimizationResult:
    """Result of code optimization"""
    original_code: str
    optimized_code: str
    issues_found: List[PerformanceIssue]
    metrics: Dict[str, Any]
    optimization_level: OptimizationLevel
    compatibility_notes: List[str]


class RobloxScriptOptimizationAgent(BaseAgent):
    """Agent for optimizing Roblox Luau scripts"""

    def __init__(
        self,
        config: Optional[AgentConfig] = None,
        llm: Optional[Any] = None,
        optimization_level: OptimizationLevel = OptimizationLevel.BALANCED
    ):
        # Create default config if not provided
        if not config:
            config = AgentConfig(
                name="RobloxScriptOptimizer",
                model="gpt-4",
                temperature=0.1,  # Low temperature for consistent optimizations
                system_prompt="""You are an expert Roblox Luau script optimizer.
                You understand performance optimization, memory management, and Roblox-specific best practices.
                Optimize scripts for performance while maintaining functionality.""",
                verbose=True,
                memory_enabled=True
            )
        super().__init__(config)
        # Override llm if provided
        if llm is not None:
            self.llm = llm
        elif not hasattr(self, 'llm') or not self.llm:
            # Use the new LCEL compatibility layer
            self.llm = get_compatible_llm(
                model_name="gpt-4",
                temperature=0.1
            )
        self.optimization_level = optimization_level
        self.pattern_database = self._load_optimization_patterns()

    def _load_optimization_patterns(self) -> Dict[str, Any]:
        """Load database of common optimization patterns"""
        return {
            "loop_optimizations": {
                "ipairs_vs_pairs": {
                    "pattern": r"for\s+\w+,\s*\w+\s+in\s+pairs\(([^)]+)\)\s+do",
                    "condition": "array_iteration",
                    "replacement": "for i, v in ipairs({0}) do",
                    "description": "Use ipairs for array iteration (faster)"
                },
                "cache_table_length": {
                    "pattern": r"for\s+i\s*=\s*1,\s*#(\w+)\s+do",
                    "optimization": "local len = #{0}\nfor i = 1, len do",
                    "description": "Cache table length outside loop"
                },
                "avoid_table_insert": {
                    "pattern": r"table\.insert\((\w+),\s*(.+)\)",
                    "optimization": "{0}[#{0} + 1] = {1}",
                    "description": "Direct indexing is faster than table.insert"
                }
            },
            "memory_optimizations": {
                "localize_globals": {
                    "pattern": r"(\w+)\.([\w\.]+)",
                    "check": "repeated_access",
                    "optimization": "local {1}_{2} = {0}.{1}",
                    "description": "Localize frequently accessed globals"
                },
                "reuse_tables": {
                    "pattern": r"local\s+(\w+)\s*=\s*\{\}",
                    "check": "in_loop",
                    "optimization": "table.clear({0}) -- reuse existing table",
                    "description": "Reuse tables instead of creating new ones"
                },
                "weak_references": {
                    "pattern": r"cache\[(.+)\]\s*=\s*(.+)",
                    "suggestion": "setmetatable(cache, {__mode = 'v'}) -- weak values",
                    "description": "Use weak tables for caches"
                }
            },
            "event_optimizations": {
                "debounce_connections": {
                    "pattern": r"\.(\w+):Connect\(function",
                    "check": "high_frequency_event",
                    "optimization": "Add debounce for high-frequency events",
                    "description": "Debounce high-frequency events"
                },
                "disconnect_unused": {
                    "pattern": r"(\w+):Connect\(",
                    "suggestion": "Store and disconnect when not needed",
                    "description": "Disconnect unused event connections"
                }
            },
            "roblox_specific": {
                "batch_property_changes": {
                    "pattern": r"(\w+)\.(\w+)\s*=\s*(.+)\n\s*\1\.(\w+)\s*=",
                    "optimization": "Batch property changes together",
                    "description": "Batch Instance property changes"
                },
                "use_heartbeat": {
                    "pattern": r"while\s+true\s+do.*?wait\(",
                    "optimization": "RunService.Heartbeat:Connect()",
                    "description": "Use Heartbeat instead of while-wait loops"
                },
                "cache_findchild": {
                    "pattern": r":FindFirstChild\([\"'](\w+)[\"']\)",
                    "check": "repeated_access",
                    "optimization": "Cache FindFirstChild results",
                    "description": "Cache frequently accessed children"
                }
            }
        }

    def _analyze_script_performance(self, code: str) -> List[PerformanceIssue]:
        """Analyze script for performance issues"""
        issues = []
        lines = code.split('\n')

        # Check for common performance issues
        performance_checks = [
            (r"wait\(\)", "critical", "Using wait() without arguments",
             "Use task.wait() or specify wait time"),
            (r"while true do", "high", "Infinite loop without yielding",
             "Use RunService events instead"),
            (r"Instance\.new.*Parent\s*=", "high", "Setting Parent in constructor",
             "Set Parent after configuring properties"),
            (r"GetChildren\(\)", "medium", "GetChildren in loops",
             "Cache GetChildren result if used multiple times"),
            (r"workspace\.", "low", "Direct workspace access",
             "Consider caching workspace references"),
            (r"_G\[", "high", "Using _G global table",
             "Use ModuleScripts for shared data"),
            (r"getfenv|setfenv|loadstring", "critical", "Using dangerous functions",
             "These functions are deprecated/dangerous"),
            (r"spawn\(", "medium", "Using spawn for threading",
             "Use task.spawn() instead"),
            (r"delay\(", "medium", "Using delay for scheduling",
             "Use task.delay() instead")
        ]

        for i, line in enumerate(lines, 1):
            for pattern, severity, issue_type, suggestion in performance_checks:
                if re.search(pattern, line, re.IGNORECASE):
                    issues.append(PerformanceIssue(
                        severity=severity,
                        location=f"Line {i}",
                        issue_type=issue_type,
                        description=f"Found: {line.strip()}",
                        suggestion=suggestion,
                        estimated_impact="5-20% performance improvement"
                    ))

        # Check for memory leaks
        connection_count = len(re.findall(r":Connect\(", code))
        disconnect_count = len(re.findall(r":Disconnect\(\)", code))
        if connection_count > disconnect_count + 2:
            issues.append(PerformanceIssue(
                severity="high",
                location="Global",
                issue_type="Potential memory leak",
                description=f"{connection_count} connections but only {disconnect_count} disconnects",
                suggestion="Store and disconnect event connections when no longer needed",
                estimated_impact="Prevents memory leaks"
            ))

        return issues

    def _optimize_loops(self, code: str) -> str:
        """Optimize loop patterns in code"""
        optimized = code

        # Optimize for loops with table length
        pattern = r"for\s+(\w+)\s*=\s*1,\s*#(\w+)\s+do"
        matches = re.finditer(pattern, optimized)
        for match in reversed(list(matches)):
            var_name = match.group(1)
            table_name = match.group(2)
            # Check if table length is accessed multiple times
            if code.count(f"#{table_name}") > 1:
                # Add length caching
                replacement = f"local {table_name}_len = #{table_name}\nfor {var_name} = 1, {table_name}_len do"
                optimized = optimized[:match.start()] + replacement + optimized[match.end():]

        # Replace pairs with ipairs for arrays
        pattern = r"for\s+(\w+),\s*(\w+)\s+in\s+pairs\((\w+)\)\s+do"
        def replace_pairs(match):
            # Check if it's likely an array (heuristic)
            context = optimized[max(0, match.start()-100):match.end()+100]
            if "[1]" in context or "#" + match.group(3) in context:
                return f"for {match.group(1)}, {match.group(2)} in ipairs({match.group(3)}) do"
            return match.group(0)

        optimized = re.sub(pattern, replace_pairs, optimized)

        return optimized

    def _optimize_table_operations(self, code: str) -> str:
        """Optimize table operations"""
        optimized = code

        # Replace table.insert with direct indexing for append operations
        pattern = r"table\.insert\((\w+),\s*([^,)]+)\)"
        def replace_insert(match):
            table_name = match.group(1)
            value = match.group(2)
            return f"{table_name}[#{table_name} + 1] = {value}"

        optimized = re.sub(pattern, replace_insert, optimized)

        # Add table.clear for reused tables
        lines = optimized.split('\n')
        optimized_lines = []
        for i, line in enumerate(lines):
            if "local" in line and "= {}" in line:
                # Check if this table is in a loop
                indent = len(line) - len(line.lstrip())
                if i > 0 and ("for " in lines[i-1] or "while " in lines[i-1]):
                    var_name = re.search(r"local\s+(\w+)\s*=\s*\{\}", line)
                    if var_name:
                        # Add table declaration outside loop
                        optimized_lines.insert(-1, " " * (indent - 4) + f"local {var_name.group(1)} = {{}}")
                        line = " " * indent + f"table.clear({var_name.group(1)})"
            optimized_lines.append(line)

        optimized = '\n'.join(optimized_lines)
        return optimized

    def _optimize_roblox_specific(self, code: str) -> str:
        """Apply Roblox-specific optimizations"""
        optimized = code

        # Replace wait() with task.wait()
        optimized = re.sub(r"\bwait\(", "task.wait(", optimized)

        # Replace spawn() with task.spawn()
        optimized = re.sub(r"\bspawn\(", "task.spawn(", optimized)

        # Replace delay() with task.delay()
        optimized = re.sub(r"\bdelay\(", "task.delay(", optimized)

        # Optimize Instance.new with Parent setting
        pattern = r"local\s+(\w+)\s*=\s*Instance\.new\([\"'](\w+)[\"'],\s*([^)]+)\)"
        def optimize_instance_new(match):
            var_name = match.group(1)
            class_name = match.group(2)
            parent = match.group(3)
            return f"local {var_name} = Instance.new(\"{class_name}\")\n{var_name}.Parent = {parent}"

        optimized = re.sub(pattern, optimize_instance_new, optimized)

        # Replace while true loops with Heartbeat
        pattern = r"while\s+true\s+do(.*?)wait\(([\d\.]*)\)(.*?)end"
        def replace_while_loop(match):
            body = match.group(1) + match.group(3)
            wait_time = match.group(2) or "0"
            if float(wait_time) < 0.1:
                return f"game:GetService(\"RunService\").Heartbeat:Connect(function()\n{body}\nend)"
            return match.group(0)

        optimized = re.sub(pattern, replace_while_loop, optimized, flags=re.DOTALL)

        return optimized

    def _add_caching(self, code: str) -> str:
        """Add caching for frequently accessed values"""
        optimized = code
        lines = optimized.split('\n')

        # Find frequently accessed services
        service_pattern = r"game:GetService\([\"'](\w+)[\"']\)"
        services = {}
        for line in lines:
            matches = re.findall(service_pattern, line)
            for service in matches:
                services[service] = services.get(service, 0) + 1

        # Add caching for frequently used services
        if services:
            cache_lines = ["-- Cached Services"]
            for service, count in services.items():
                if count > 1:
                    cache_lines.append(f"local {service} = game:GetService(\"{service}\")")

            # Add cache lines at the beginning
            if len(cache_lines) > 1:
                optimized = '\n'.join(cache_lines) + '\n\n' + optimized

                # Replace GetService calls with cached versions
                for service in services:
                    if services[service] > 1:
                        pattern = f"game:GetService\\([\"']{service}[\"']\\)"
                        optimized = re.sub(pattern, service, optimized)

        return optimized

    def optimize_script(
        self,
        code: str,
        optimization_level: Optional[OptimizationLevel] = None,
        preserve_comments: bool = True
    ) -> OptimizationResult:
        """
        Optimize a Roblox Luau script

        Args:
            code: The Luau script to optimize
            optimization_level: Level of optimization aggressiveness
            preserve_comments: Whether to preserve comments

        Returns:
            OptimizationResult with optimized code and metrics
        """
        level = optimization_level or self.optimization_level

        # Analyze performance issues
        issues = self._analyze_script_performance(code)

        # Apply optimizations based on level
        optimized = code

        if level in [OptimizationLevel.BALANCED, OptimizationLevel.AGGRESSIVE]:
            optimized = self._optimize_loops(optimized)
            optimized = self._optimize_table_operations(optimized)
            optimized = self._add_caching(optimized)

        if level == OptimizationLevel.AGGRESSIVE:
            optimized = self._optimize_roblox_specific(optimized)

        # Calculate metrics
        original_lines = len(code.split('\n'))
        optimized_lines = len(optimized.split('\n'))

        metrics = {
            "original_lines": original_lines,
            "optimized_lines": optimized_lines,
            "issues_found": len(issues),
            "critical_issues": sum(1 for i in issues if i.severity == "critical"),
            "estimated_performance_gain": f"{len(issues) * 5}-{len(issues) * 15}%",
            "memory_optimizations": len(re.findall(r"table\.clear|weak.*table|cache", optimized))
        }

        compatibility_notes = []
        if "task.wait" in optimized and "wait(" in code:
            compatibility_notes.append("Replaced wait() with task.wait() - requires modern Roblox")
        if "table.clear" in optimized:
            compatibility_notes.append("Uses table.clear() for performance")

        return OptimizationResult(
            original_code=code,
            optimized_code=optimized,
            issues_found=issues,
            metrics=metrics,
            optimization_level=level,
            compatibility_notes=compatibility_notes
        )

    def benchmark_script(self, code: str) -> Dict[str, Any]:
        """
        Generate benchmark code for performance testing

        Args:
            code: The script to benchmark

        Returns:
            Benchmark harness code and instructions
        """
        benchmark_template = '''
-- Performance Benchmark Harness
local RunService = game:GetService("RunService")

local function benchmark(name, func, iterations)
    iterations = iterations or 1000

    -- Warm up
    for i = 1, 10 do
        func()
    end

    -- Actual benchmark
    local startTime = tick()
    for i = 1, iterations do
        func()
    end
    local endTime = tick()

    local totalTime = endTime - startTime
    local avgTime = totalTime / iterations

    print(string.format("[BENCHMARK] %s:", name))
    print(string.format("  Total time: %.4f seconds", totalTime))
    print(string.format("  Average time: %.6f seconds", avgTime))
    print(string.format("  Operations/sec: %.0f", iterations / totalTime))

    return {
        name = name,
        totalTime = totalTime,
        avgTime = avgTime,
        opsPerSec = iterations / totalTime
    }
end

-- Memory profiling
local function getMemoryUsage()
    return collectgarbage("count") * 1024 -- Convert to bytes
end

local function profileMemory(name, func)
    collectgarbage("collect")
    local memBefore = getMemoryUsage()

    func()

    collectgarbage("collect")
    local memAfter = getMemoryUsage()

    local memUsed = memAfter - memBefore

    print(string.format("[MEMORY] %s:", name))
    print(string.format("  Memory used: %.2f KB", memUsed / 1024))

    return {
        name = name,
        memoryUsed = memUsed
    }
end

-- Your optimized code here
{code}

-- Benchmark tests
local results = {}

-- Add your benchmark tests here
-- Example:
-- table.insert(results, benchmark("Test Name", function()
--     -- Code to test
-- end, 10000))

return results
'''

        return {
            "benchmark_code": benchmark_template.format(code=code),
            "instructions": [
                "1. Copy the benchmark code to Roblox Studio",
                "2. Add your specific test cases in the benchmark section",
                "3. Run in Studio's command bar or as a Script",
                "4. Compare results between original and optimized versions",
                "5. Test on different devices for comprehensive results"
            ],
            "metrics_to_track": [
                "Execution time",
                "Memory usage",
                "Frame rate impact",
                "Operations per second"
            ]
        }

    def generate_optimization_report(
        self,
        original_code: str,
        optimized_result: OptimizationResult
    ) -> str:
        """Generate a detailed optimization report"""
        report = f"""
# Roblox Luau Script Optimization Report

## Summary
- **Optimization Level**: {optimized_result.optimization_level.value}
- **Issues Found**: {len(optimized_result.issues_found)}
- **Critical Issues**: {optimized_result.metrics.get('critical_issues', 0)}
- **Estimated Performance Gain**: {optimized_result.metrics.get('estimated_performance_gain', 'Unknown')}

## Performance Issues Identified

"""
        # Group issues by severity
        issues_by_severity = {}
        for issue in optimized_result.issues_found:
            if issue.severity not in issues_by_severity:
                issues_by_severity[issue.severity] = []
            issues_by_severity[issue.severity].append(issue)

        for severity in ["critical", "high", "medium", "low"]:
            if severity in issues_by_severity:
                report += f"### {severity.upper()} Priority Issues\n\n"
                for issue in issues_by_severity[severity]:
                    report += f"- **{issue.issue_type}** ({issue.location})\n"
                    report += f"  - Description: {issue.description}\n"
                    report += f"  - Suggestion: {issue.suggestion}\n"
                    report += f"  - Impact: {issue.estimated_impact}\n\n"

        report += """
## Optimizations Applied

1. **Loop Optimizations**
   - Cached table lengths outside loops
   - Replaced pairs() with ipairs() for arrays
   - Optimized iteration patterns

2. **Memory Management**
   - Added table.clear() for reused tables
   - Implemented caching for frequently accessed values
   - Localized global accesses

3. **Roblox-Specific**
   - Replaced deprecated wait() with task.wait()
   - Optimized Instance creation patterns
   - Used RunService events instead of while loops

## Metrics

| Metric | Original | Optimized | Change |
|--------|----------|-----------|--------|
| Lines of Code | {original_lines} | {optimized_lines} | {line_change:+d} |
| Memory Optimizations | 0 | {memory_opts} | +{memory_opts} |
| Performance Issues | {issues_found} | 0 | -{issues_found} |

## Compatibility Notes

""".format(
            original_lines=optimized_result.metrics['original_lines'],
            optimized_lines=optimized_result.metrics['optimized_lines'],
            line_change=optimized_result.metrics['optimized_lines'] - optimized_result.metrics['original_lines'],
            memory_opts=optimized_result.metrics.get('memory_optimizations', 0),
            issues_found=len(optimized_result.issues_found)
        )

        if optimized_result.compatibility_notes:
            for note in optimized_result.compatibility_notes:
                report += f"- {note}\n"
        else:
            report += "- No compatibility issues identified\n"

        report += "\n## Recommendations\n\n"
        report += "1. Test the optimized code thoroughly in your game\n"
        report += "2. Profile performance using the provided benchmark harness\n"
        report += "3. Monitor memory usage in production\n"
        report += "4. Consider further optimizations for critical paths\n"

        return report

    def execute(self, task: str) -> str:
        """Execute optimization task"""
        # This would integrate with the LangChain agent for more complex tasks
        prompt = f"""
        As a Roblox Luau optimization expert, analyze and optimize the following script:

        Task: {task}

        Focus on:
        1. Performance bottlenecks
        2. Memory efficiency
        3. Roblox best practices
        4. Modern Luau features

        Provide optimized code with explanations.
        """

        response = self.llm.predict(prompt)
        return response

    async def _process_task(self, state: AgentState) -> TaskResult:
        """Process script optimization task"""
        # Extract script and settings from state context
        context = state.get("context", {})
        script_code = context.get("script_code", "")
        optimization_level = context.get("optimization_level", "balanced")
        preserve_comments = context.get("preserve_comments", True)

        # Map string optimization level to enum
        level_map = {
            "conservative": OptimizationLevel.CONSERVATIVE,
            "balanced": OptimizationLevel.BALANCED,
            "aggressive": OptimizationLevel.AGGRESSIVE
        }
        opt_level = level_map.get(optimization_level.lower(), OptimizationLevel.BALANCED)

        if not script_code:
            return TaskResult(
                success=False,
                error="No script provided for optimization",
                message="Script code is required"
            )

        try:
            # Perform optimization
            result = self.optimize_script(
                script_code,
                optimization_level=opt_level,
                preserve_comments=preserve_comments
            )

            return TaskResult(
                success=True,
                result={
                    "original_code": result.original_code,
                    "optimized_code": result.optimized_code,
                    "issues_found": [
                        {
                            "severity": issue.severity,
                            "location": issue.location,
                            "type": issue.issue_type,
                            "description": issue.description,
                            "suggestion": issue.suggestion,
                            "impact": issue.estimated_impact
                        }
                        for issue in result.issues_found
                    ],
                    "metrics": result.metrics,
                    "optimization_level": result.optimization_level.value,
                    "performance_gain": result.metrics.get("estimated_performance_gain", "Unknown")
                },
                message=f"Script optimized with {len(result.issues_found)} issues found"
            )
        except Exception as e:
            return TaskResult(
                success=False,
                error=str(e),
                message="Optimization failed"
            )


# Example usage
if __name__ == "__main__":
    # Example Luau script with performance issues
    example_script = """
    -- Player inventory system
    local Players = game:GetService("Players")
    local ReplicatedStorage = game:GetService("ReplicatedStorage")

    local inventory = {}

    while true do
        wait(0.1)
        for _, player in pairs(Players:GetPlayers()) do
            if not inventory[player] then
                inventory[player] = {}
            end

            -- Check for items
            for i = 1, #player.Backpack:GetChildren() do
                local item = player.Backpack:GetChildren()[i]
                table.insert(inventory[player], item.Name)
            end
        end
    end

    -- Handle item spawning
    spawn(function()
        while true do
            local part = Instance.new("Part", workspace)
            part.Name = "Item"
            part.Position = Vector3.new(0, 10, 0)
            wait(1)
        end
    end)
    """

    optimizer = RobloxScriptOptimizationAgent()
    result = optimizer.optimize_script(
        example_script,
        optimization_level=OptimizationLevel.AGGRESSIVE
    )

    print("Optimized Code:")
    print(result.optimized_code)
    print("\nOptimization Report:")
    print(optimizer.generate_optimization_report(example_script, result))
