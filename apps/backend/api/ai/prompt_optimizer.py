"""
GPT-4.1 Prompt Optimizer - Phase 4
Optimizes prompts for GPT-4.1's more literal and precise instruction following
"""

import hashlib
import logging
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class OptimizationType(Enum):
    """Types of prompt optimizations"""

    LITERAL_INSTRUCTION = "literal_instruction"
    REDUNDANCY_REMOVAL = "redundancy_removal"
    STRUCTURE_SIMPLIFICATION = "structure_simplification"
    TOKEN_REDUCTION = "token_reduction"
    TOOL_DESCRIPTION = "tool_description"
    FORMAT_STANDARDIZATION = "format_standardization"


@dataclass
class OptimizationResult:
    """Result of prompt optimization"""

    original: str
    optimized: str
    optimizations_applied: list[OptimizationType]
    tokens_saved: int
    complexity_score: float
    metadata: dict[str, Any] = field(default_factory=dict)


class GPT41PromptOptimizer:
    """
    Optimizes prompts for GPT-4.1's characteristics:
    - More literal instruction following
    - Better comprehension without redundant context
    - Improved structured output generation
    - Enhanced tool usage with API-field descriptions
    """

    def __init__(self):
        self.optimization_rules = self._load_optimization_rules()
        self.cache = {}

    def _load_optimization_rules(self) -> dict[str, list[tuple[str, str]]]:
        """Load optimization rules for GPT-4.1"""
        return {
            "redundant_phrases": [
                # Remove polite redundancies (GPT-4.1 doesn't need them)
                (r"Could you please\s+", ""),
                (r"Would you mind\s+", ""),
                (r"I would like you to\s+", ""),
                (r"Can you help me\s+", ""),
                (r"Please kindly\s+", ""),
                (r"If possible,?\s+", ""),
                (r"When you get a chance,?\s+", ""),
                # Remove verbose instructions
                (r"Please carefully\s+", ""),
                (r"Make sure to\s+", ""),
                (r"Remember to\s+", ""),
                (r"Don't forget to\s+", ""),
                (r"Be sure to\s+", ""),
                (r"It's important that you\s+", ""),
                (r"Take care to\s+", ""),
                (r"Pay attention to\s+", ""),
                # Remove explanatory redundancies
                (r"What I mean is\s+", ""),
                (r"In other words,?\s+", ""),
                (r"To clarify,?\s+", ""),
                (r"Let me explain:?\s+", ""),
                (r"Basically,?\s+", ""),
                (r"Essentially,?\s+", ""),
            ],
            "structure_simplifications": [
                # Simplify task descriptions
                (r"Your task is to\s+", "Task: "),
                (r"You need to\s+", ""),
                (r"Your job is to\s+", ""),
                (r"I need you to\s+", ""),
                (r"The goal is to\s+", "Goal: "),
                (r"The objective is to\s+", "Objective: "),
                # Simplify formatting instructions
                (r"Format your response as follows:\s*", "Format:\n"),
                (r"Provide your answer in the following format:\s*", "Format:\n"),
                (r"Structure your response like this:\s*", "Format:\n"),
                (r"Organize your answer as:\s*", "Format:\n"),
                (r"Please format as:\s*", "Format:\n"),
                # Simplify output instructions
                (r"Your output should be\s+", "Output: "),
                (r"The result should be\s+", "Result: "),
                (r"Return the following:\s*", "Return:\n"),
                (r"Provide the following information:\s*", "Provide:\n"),
            ],
            "instruction_clarifications": [
                # Make instructions more direct
                (r"Try to\s+", ""),
                (r"Attempt to\s+", ""),
                (r"See if you can\s+", ""),
                (r"If you can,?\s+", ""),
                # Remove hedging language
                (r"Maybe\s+", ""),
                (r"Perhaps\s+", ""),
                (r"Possibly\s+", ""),
                (r"You might want to\s+", ""),
                (r"Consider\s+", ""),
            ],
        }

    def optimize_prompt(
        self, prompt: str, context: dict[str, Any] | None = None
    ) -> OptimizationResult:
        """
        Optimize a prompt for GPT-4.1

        Args:
            prompt: The original prompt
            context: Optional context about the prompt usage

        Returns:
            OptimizationResult with optimized prompt and metrics
        """
        # Check cache
        cache_key = hashlib.md5(prompt.encode()).hexdigest()
        if cache_key in self.cache:
            return self.cache[cache_key]

        original = prompt
        optimized = prompt
        optimizations_applied = []

        # Apply literal instruction optimizations
        optimized, literal_count = self._apply_literal_optimizations(optimized)
        if literal_count > 0:
            optimizations_applied.append(OptimizationType.LITERAL_INSTRUCTION)

        # Remove redundancies
        optimized, redundancy_count = self._remove_redundancies(optimized)
        if redundancy_count > 0:
            optimizations_applied.append(OptimizationType.REDUNDANCY_REMOVAL)

        # Simplify structure
        optimized, structure_count = self._simplify_structure(optimized)
        if structure_count > 0:
            optimizations_applied.append(OptimizationType.STRUCTURE_SIMPLIFICATION)

        # Standardize format
        optimized = self._standardize_format(optimized)
        if optimized != original:
            optimizations_applied.append(OptimizationType.FORMAT_STANDARDIZATION)

        # Calculate metrics
        tokens_saved = self._estimate_tokens_saved(original, optimized)
        complexity_score = self._calculate_complexity(optimized)

        result = OptimizationResult(
            original=original,
            optimized=optimized,
            optimizations_applied=optimizations_applied,
            tokens_saved=tokens_saved,
            complexity_score=complexity_score,
            metadata={
                "original_length": len(original),
                "optimized_length": len(optimized),
                "reduction_percentage": (
                    round((1 - len(optimized) / len(original)) * 100, 1) if len(original) > 0 else 0
                ),
            },
        )

        # Cache result
        self.cache[cache_key] = result

        if tokens_saved > 0:
            logger.info(
                f"Prompt optimized: {tokens_saved} tokens saved, "
                f"{result.metadata['reduction_percentage']}% reduction"
            )

        return result

    def _apply_literal_optimizations(self, prompt: str) -> tuple[str, int]:
        """Apply optimizations for GPT-4.1's literal instruction following"""
        original = prompt
        count = 0

        # Remove polite/indirect language
        for pattern, replacement in self.optimization_rules["redundant_phrases"]:
            new_prompt, n = re.subn(pattern, replacement, prompt, flags=re.IGNORECASE)
            if n > 0:
                prompt = new_prompt
                count += n

        # Clean up extra whitespace
        prompt = " ".join(prompt.split())

        return prompt, count

    def _remove_redundancies(self, prompt: str) -> tuple[str, int]:
        """Remove redundant instructions and explanations"""
        count = 0

        # Remove repeated instructions
        lines = prompt.split("\n")
        seen_instructions = set()
        cleaned_lines = []

        for line in lines:
            # Normalize for comparison
            normalized = line.lower().strip()
            if normalized and normalized not in seen_instructions:
                cleaned_lines.append(line)
                seen_instructions.add(normalized)
            elif normalized:
                count += 1

        prompt = "\n".join(cleaned_lines)

        return prompt, count

    def _simplify_structure(self, prompt: str) -> tuple[str, int]:
        """Simplify prompt structure for clearer instructions"""
        count = 0

        for pattern, replacement in self.optimization_rules["structure_simplifications"]:
            new_prompt, n = re.subn(pattern, replacement, prompt, flags=re.IGNORECASE)
            if n > 0:
                prompt = new_prompt
                count += n

        # Convert lists to bullet points (GPT-4.1 handles these better)
        prompt = re.sub(r"(\d+)\.\s+", r"• ", prompt)

        return prompt, count

    def _standardize_format(self, prompt: str) -> str:
        """Standardize formatting for consistency"""
        # Ensure consistent spacing
        prompt = re.sub(r"\n{3,}", "\n\n", prompt)

        # Standardize section headers
        prompt = re.sub(r"^#+\s*", "", prompt, flags=re.MULTILINE)  # Remove markdown headers

        # Add clear section breaks
        sections = ["Task:", "Context:", "Format:", "Output:", "Examples:", "Constraints:"]
        for section in sections:
            prompt = re.sub(f"(?i){section}", section, prompt)

        return prompt.strip()

    def _estimate_tokens_saved(self, original: str, optimized: str) -> int:
        """Estimate tokens saved (rough approximation)"""
        # Rough estimate: 1 token ≈ 4 characters
        original_tokens = len(original) / 4
        optimized_tokens = len(optimized) / 4
        return max(0, int(original_tokens - optimized_tokens))

    def _calculate_complexity(self, prompt: str) -> float:
        """Calculate prompt complexity score (0.0 - 1.0)"""
        complexity = 0.0

        # Length factor
        length = len(prompt)
        if length < 100:
            complexity += 0.1
        elif length < 500:
            complexity += 0.3
        elif length < 1000:
            complexity += 0.5
        else:
            complexity += 0.7

        # Instruction complexity
        instruction_keywords = ["analyze", "compare", "evaluate", "synthesize", "create", "design"]
        for keyword in instruction_keywords:
            if keyword in prompt.lower():
                complexity += 0.05

        # Structure complexity
        if "\n" in prompt:
            complexity += 0.1
        if any(section in prompt for section in ["Format:", "Examples:", "Constraints:"]):
            complexity += 0.1

        return min(1.0, complexity)

    def optimize_tool_descriptions(self, tools: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """
        Optimize tool/function descriptions for GPT-4.1
        GPT-4.1 recommendation: Use API field descriptions exclusively
        """
        optimized_tools = []

        for tool in tools:
            optimized = tool.copy()

            # Convert function format to tool format (GPT-4.1 uses "tools")
            if "function" in optimized:
                optimized["type"] = "function"
                if "function" not in optimized:
                    optimized["function"] = {}

            # Optimize descriptions to be concise and literal
            if "description" in optimized.get("function", {}):
                desc = optimized["function"]["description"]
                # Remove redundant words
                desc = re.sub(r"\b(please|kindly|carefully)\b", "", desc, flags=re.IGNORECASE)
                desc = " ".join(desc.split())
                optimized["function"]["description"] = desc

            # Optimize parameter descriptions
            if "parameters" in optimized.get("function", {}):
                params = optimized["function"]["parameters"]
                if "properties" in params:
                    for param_name, param_def in params["properties"].items():
                        if "description" in param_def:
                            # Make descriptions concise
                            desc = param_def["description"]
                            desc = desc.replace("This parameter", "").strip()
                            desc = desc.replace("Used to", "").strip()
                            desc = desc[0].upper() + desc[1:] if desc else desc
                            param_def["description"] = desc

            optimized_tools.append(optimized)

        return optimized_tools

    def create_structured_prompt(
        self,
        task: str,
        context: str | None = None,
        format: str | None = None,
        examples: list[str] | None = None,
        constraints: list[str] | None = None,
    ) -> str:
        """
        Create a structured prompt optimized for GPT-4.1

        Args:
            task: Main task description
            context: Optional context information
            format: Optional output format specification
            examples: Optional examples
            constraints: Optional constraints or requirements

        Returns:
            Optimized structured prompt
        """
        sections = []

        # Task (required)
        sections.append(f"Task: {task}")

        # Context (optional)
        if context:
            sections.append(f"Context: {context}")

        # Format (optional)
        if format:
            sections.append(f"Format:\n{format}")

        # Examples (optional)
        if examples:
            examples_text = "\n".join(f"• {ex}" for ex in examples)
            sections.append(f"Examples:\n{examples_text}")

        # Constraints (optional)
        if constraints:
            constraints_text = "\n".join(f"• {c}" for c in constraints)
            sections.append(f"Constraints:\n{constraints_text}")

        # Join sections with appropriate spacing
        prompt = "\n\n".join(sections)

        # Apply optimizations
        result = self.optimize_prompt(prompt)

        return result.optimized

    def batch_optimize(self, prompts: list[str]) -> list[OptimizationResult]:
        """Optimize multiple prompts in batch"""
        results = []
        total_tokens_saved = 0

        for prompt in prompts:
            result = self.optimize_prompt(prompt)
            results.append(result)
            total_tokens_saved += result.tokens_saved

        logger.info(
            f"Batch optimization complete: {len(prompts)} prompts, "
            f"{total_tokens_saved} total tokens saved"
        )

        return results

    def analyze_prompt_patterns(self, prompts: list[str]) -> dict[str, Any]:
        """Analyze patterns in prompts to identify optimization opportunities"""
        patterns = {
            "common_redundancies": {},
            "average_complexity": 0.0,
            "total_tokens_saveable": 0,
            "optimization_recommendations": [],
        }

        complexities = []
        redundancy_counts = {}

        for prompt in prompts:
            result = self.optimize_prompt(prompt)
            complexities.append(result.complexity_score)
            patterns["total_tokens_saveable"] += result.tokens_saved

            # Track common redundancies
            for pattern, _ in self.optimization_rules["redundant_phrases"]:
                matches = re.findall(pattern, prompt, flags=re.IGNORECASE)
                if matches:
                    redundancy_counts[pattern] = redundancy_counts.get(pattern, 0) + len(matches)

        # Calculate statistics
        patterns["average_complexity"] = (
            sum(complexities) / len(complexities) if complexities else 0
        )
        patterns["common_redundancies"] = dict(
            sorted(redundancy_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        )

        # Generate recommendations
        if patterns["average_complexity"] > 0.7:
            patterns["optimization_recommendations"].append(
                "High complexity detected. Consider breaking prompts into smaller, focused tasks."
            )

        if patterns["total_tokens_saveable"] > len(prompts) * 20:
            patterns["optimization_recommendations"].append(
                "Significant token savings possible. Enable automatic prompt optimization."
            )

        return patterns


# Singleton instance
_optimizer: GPT41PromptOptimizer | None = None


def get_prompt_optimizer() -> GPT41PromptOptimizer:
    """Get or create prompt optimizer singleton"""
    global _optimizer
    if _optimizer is None:
        _optimizer = GPT41PromptOptimizer()
    return _optimizer


# Convenience functions
def optimize_prompt(prompt: str) -> str:
    """Quick function to optimize a single prompt"""
    optimizer = get_prompt_optimizer()
    result = optimizer.optimize_prompt(prompt)
    return result.optimized


def create_gpt41_prompt(
    task: str,
    context: str | None = None,
    format: str | None = None,
    examples: list[str] | None = None,
    constraints: list[str] | None = None,
) -> str:
    """Create an optimized structured prompt for GPT-4.1"""
    optimizer = get_prompt_optimizer()
    return optimizer.create_structured_prompt(task, context, format, examples, constraints)
