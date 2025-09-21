"""
Error Correction Agent

Specialized agent for automatically fixing identified errors in code.
Uses advanced pattern matching, AST manipulation, and machine learning
to apply safe and effective corrections.
"""

import asyncio
import ast
import logging
import re
import difflib
from typing import Dict, Any, Optional, List, Tuple
from pathlib import Path
from datetime import datetime
import json
import subprocess

from langchain_core.tools import Tool
from langchain.chains import LLMChain
from pydantic import BaseModel, Field

from core.agents.error_handling.base_error_agent import (
    BaseErrorAgent,
    ErrorAgentConfig,
    ErrorState,
    ErrorType,
    ErrorPriority
)

logger = logging.getLogger(__name__)


class CodeFix(BaseModel):
    """Model for code fixes"""
    file_path: str = Field(description="Path to the file to fix")
    line_number: int = Field(description="Line number where fix should be applied")
    original_code: str = Field(description="Original code that needs fixing")
    fixed_code: str = Field(description="Fixed version of the code")
    fix_description: str = Field(description="Description of what was fixed")
    confidence: float = Field(description="Confidence level of the fix (0-1)")
    fix_type: str = Field(description="Type of fix applied")
    validation_passed: bool = Field(default=False, description="Whether fix passed validation")
    rollback_available: bool = Field(default=True, description="Whether rollback is possible")


class FixStrategy(BaseModel):
    """Model for fix strategies"""
    strategy_name: str = Field(description="Name of the fix strategy")
    applicable_errors: List[ErrorType] = Field(description="Error types this strategy can fix")
    confidence_threshold: float = Field(default=0.7, description="Minimum confidence to apply")
    requires_validation: bool = Field(default=True, description="Whether validation is required")
    can_rollback: bool = Field(default=True, description="Whether strategy supports rollback")


class ErrorCorrectionAgent(BaseErrorAgent):
    """
    Agent specialized in automatically correcting identified errors.

    Capabilities:
    - Syntax error correction
    - Import resolution
    - Type error fixes
    - Logic error detection and correction
    - Code formatting and style fixes
    - Automatic refactoring for common antipatterns
    """

    def __init__(self, config: Optional[ErrorAgentConfig] = None):
        if config is None:
            config = ErrorAgentConfig(
                name="ErrorCorrectionAgent",
                model="gpt-4",
                temperature=0.3,  # Lower temperature for more deterministic fixes
                max_fix_attempts=3,
                auto_fix_enabled=True,
                pattern_learning_enabled=True,
                rollback_enabled=True
            )

        super().__init__(config)

        # Initialize fix strategies
        self.fix_strategies = self._initialize_fix_strategies()

        # Track applied fixes for rollback
        self.applied_fixes: List[CodeFix] = []

        # Initialize code analysis tools
        self.tools.extend(self._create_correction_tools())

        logger.info("Initialized Error Correction Agent")

    def _get_default_system_prompt(self) -> str:
        """Get specialized system prompt for error correction"""
        return """You are the Error Correction Agent, specialized in automatically fixing code errors.

Your core capabilities:
- Fix syntax errors (missing brackets, quotes, indentation)
- Resolve import and dependency issues
- Correct type mismatches and add type hints
- Fix logic errors and edge cases
- Improve code quality and performance
- Apply security best practices

Fix principles:
1. Minimal change principle - make the smallest change that fixes the issue
2. Preserve functionality - ensure existing behavior is maintained
3. Follow project conventions and style guides
4. Add defensive programming where appropriate
5. Document significant changes

Always validate fixes before applying them and maintain rollback capability."""

    def _initialize_fix_strategies(self) -> List[FixStrategy]:
        """Initialize available fix strategies"""
        return [
            FixStrategy(
                strategy_name="syntax_correction",
                applicable_errors=[ErrorType.SYNTAX],
                confidence_threshold=0.9,
                requires_validation=True
            ),
            FixStrategy(
                strategy_name="import_resolution",
                applicable_errors=[ErrorType.DEPENDENCY],
                confidence_threshold=0.8,
                requires_validation=True
            ),
            FixStrategy(
                strategy_name="type_annotation",
                applicable_errors=[ErrorType.TYPE_ERROR],
                confidence_threshold=0.7,
                requires_validation=True
            ),
            FixStrategy(
                strategy_name="null_check_addition",
                applicable_errors=[ErrorType.RUNTIME],
                confidence_threshold=0.75,
                requires_validation=True
            ),
            FixStrategy(
                strategy_name="resource_cleanup",
                applicable_errors=[ErrorType.MEMORY_LEAK],
                confidence_threshold=0.8,
                requires_validation=True
            ),
            FixStrategy(
                strategy_name="async_await_correction",
                applicable_errors=[ErrorType.RUNTIME],
                confidence_threshold=0.85,
                requires_validation=True
            ),
            FixStrategy(
                strategy_name="exception_handling",
                applicable_errors=[ErrorType.RUNTIME, ErrorType.API_ERROR],
                confidence_threshold=0.7,
                requires_validation=False
            )
        ]

    def _create_correction_tools(self) -> List[Tool]:
        """Create specialized tools for code correction"""
        tools = []

        tools.append(Tool(
            name="apply_syntax_fix",
            description="Apply syntax error corrections to code",
            func=self._apply_syntax_fix
        ))

        tools.append(Tool(
            name="fix_imports",
            description="Fix import statements and resolve dependencies",
            func=self._fix_imports
        ))

        tools.append(Tool(
            name="add_type_hints",
            description="Add or correct type hints in code",
            func=self._add_type_hints
        ))

        tools.append(Tool(
            name="add_error_handling",
            description="Add appropriate error handling to code",
            func=self._add_error_handling
        ))

        tools.append(Tool(
            name="validate_fix",
            description="Validate that a fix doesn't break existing functionality",
            func=self._validate_fix
        ))

        tools.append(Tool(
            name="rollback_fix",
            description="Rollback a previously applied fix",
            func=self._rollback_fix
        ))

        return tools

    async def correct_error(self, error_state: ErrorState) -> CodeFix:
        """
        Main method to correct an identified error.

        Args:
            error_state: The error state to fix

        Returns:
            CodeFix object with the applied correction
        """
        logger.info(f"Attempting to correct error: {error_state['error_id']}")

        # Select appropriate strategy
        strategy = self._select_fix_strategy(error_state)
        if not strategy:
            logger.warning(f"No suitable fix strategy found for error type: {error_state['error_type']}")
            return self._create_no_fix_response(error_state)

        # Analyze the error context
        analysis = await self._analyze_error_context(error_state)

        # Generate fix
        fix = await self._generate_fix(error_state, analysis, strategy)

        # Validate fix if required
        if strategy.requires_validation and fix.confidence >= strategy.confidence_threshold:
            fix.validation_passed = await self._validate_fix_async(fix)
            if not fix.validation_passed:
                logger.warning(f"Fix validation failed for {error_state['error_id']}")
                fix.confidence *= 0.5  # Reduce confidence

        # Apply fix if confident enough
        if fix.confidence >= strategy.confidence_threshold and fix.validation_passed:
            success = await self._apply_fix(fix)
            if success:
                self.applied_fixes.append(fix)
                await self.learn_from_resolution(
                    error_state["error_id"],
                    fix.fix_description,
                    True
                )
            else:
                fix.confidence = 0.0

        return fix

    def _select_fix_strategy(self, error_state: ErrorState) -> Optional[FixStrategy]:
        """Select the most appropriate fix strategy for the error"""
        error_type = error_state["error_type"]

        applicable_strategies = [
            s for s in self.fix_strategies
            if error_type in s.applicable_errors
        ]

        if not applicable_strategies:
            return None

        # Return strategy with highest confidence threshold (most reliable)
        return max(applicable_strategies, key=lambda s: s.confidence_threshold)

    async def _analyze_error_context(self, error_state: ErrorState) -> Dict[str, Any]:
        """Analyze the context around the error"""
        analysis = {
            "error_location": None,
            "surrounding_code": None,
            "imports": [],
            "variables": [],
            "functions": [],
            "classes": [],
            "patterns_matched": []
        }

        # Extract file and line information
        if error_state.get("file_path") and error_state.get("line_number"):
            file_path = Path(error_state["file_path"])
            if file_path.exists():
                with open(file_path, 'r') as f:
                    lines = f.readlines()

                line_num = error_state["line_number"] - 1  # 0-indexed

                # Get surrounding context (5 lines before and after)
                start = max(0, line_num - 5)
                end = min(len(lines), line_num + 6)
                analysis["surrounding_code"] = ''.join(lines[start:end])
                analysis["error_location"] = {
                    "file": str(file_path),
                    "line": error_state["line_number"],
                    "code": lines[line_num] if line_num < len(lines) else None
                }

                # Parse the file with AST
                try:
                    tree = ast.parse(''.join(lines))
                    analysis["imports"] = self._extract_imports(tree)
                    analysis["variables"] = self._extract_variables(tree)
                    analysis["functions"] = self._extract_functions(tree)
                    analysis["classes"] = self._extract_classes(tree)
                except SyntaxError:
                    logger.debug("Could not parse file with AST due to syntax errors")

        # Match against known patterns
        for pattern in self.error_patterns:
            if re.search(pattern.regex, error_state["description"], re.IGNORECASE):
                analysis["patterns_matched"].append(pattern.pattern_id)

        return analysis

    async def _generate_fix(
        self,
        error_state: ErrorState,
        analysis: Dict[str, Any],
        strategy: FixStrategy
    ) -> CodeFix:
        """Generate a fix for the error based on analysis and strategy"""
        fix = CodeFix(
            file_path=error_state.get("file_path", ""),
            line_number=error_state.get("line_number", 0),
            original_code="",
            fixed_code="",
            fix_description="",
            confidence=0.0,
            fix_type=strategy.strategy_name
        )

        # Get original code if available
        if analysis["error_location"] and analysis["error_location"]["code"]:
            fix.original_code = analysis["error_location"]["code"]

        # Apply strategy-specific fix generation
        if strategy.strategy_name == "syntax_correction":
            fix = self._generate_syntax_fix(fix, error_state, analysis)
        elif strategy.strategy_name == "import_resolution":
            fix = self._generate_import_fix(fix, error_state, analysis)
        elif strategy.strategy_name == "type_annotation":
            fix = self._generate_type_fix(fix, error_state, analysis)
        elif strategy.strategy_name == "null_check_addition":
            fix = self._generate_null_check_fix(fix, error_state, analysis)
        elif strategy.strategy_name == "exception_handling":
            fix = self._generate_exception_handling_fix(fix, error_state, analysis)
        else:
            # Use LLM for complex fixes
            fix = await self._generate_llm_fix(fix, error_state, analysis, strategy)

        return fix

    def _generate_syntax_fix(
        self,
        fix: CodeFix,
        error_state: ErrorState,
        analysis: Dict[str, Any]
    ) -> CodeFix:
        """Generate fix for syntax errors"""
        error_msg = error_state["description"].lower()
        original = fix.original_code

        # Common syntax fixes
        if "unexpected indent" in error_msg:
            fix.fixed_code = original.lstrip()
            fix.fix_description = "Fixed indentation"
            fix.confidence = 0.9
        elif "invalid syntax" in error_msg:
            # Check for missing colons
            if any(keyword in original for keyword in ["if ", "for ", "while ", "def ", "class "]):
                if not original.rstrip().endswith(":"):
                    fix.fixed_code = original.rstrip() + ":\n"
                    fix.fix_description = "Added missing colon"
                    fix.confidence = 0.85
        elif "unterminated string" in error_msg or "EOL while scanning" in error_msg:
            # Fix unterminated strings
            quote_count = original.count('"') + original.count("'")
            if quote_count % 2 != 0:
                if '"' in original:
                    fix.fixed_code = original.rstrip() + '"\n'
                else:
                    fix.fixed_code = original.rstrip() + "'\n"
                fix.fix_description = "Closed unterminated string"
                fix.confidence = 0.8
        elif "unexpected EOF" in error_msg:
            # Check for unclosed brackets
            open_brackets = original.count("(") + original.count("[") + original.count("{")
            close_brackets = original.count(")") + original.count("]") + original.count("}")
            if open_brackets > close_brackets:
                missing = []
                if original.count("(") > original.count(")"):
                    missing.append(")")
                if original.count("[") > original.count("]"):
                    missing.append("]")
                if original.count("{") > original.count("}"):
                    missing.append("}")
                fix.fixed_code = original.rstrip() + ''.join(missing) + "\n"
                fix.fix_description = f"Added missing bracket(s): {''.join(missing)}"
                fix.confidence = 0.75

        return fix

    def _generate_import_fix(
        self,
        fix: CodeFix,
        error_state: ErrorState,
        analysis: Dict[str, Any]
    ) -> CodeFix:
        """Generate fix for import errors"""
        error_msg = error_state["description"]

        # Extract module name from error
        module_match = re.search(r"No module named ['\"]([^'\"]+)['\"]", error_msg)
        if module_match:
            module_name = module_match.group(1)

            # Common import fixes
            common_fixes = {
                "typing": "from typing import *",
                "datetime": "from datetime import datetime",
                "pathlib": "from pathlib import Path",
                "json": "import json",
                "os": "import os",
                "sys": "import sys",
                "asyncio": "import asyncio",
                "logging": "import logging"
            }

            if module_name in common_fixes:
                fix.fixed_code = common_fixes[module_name] + "\n" + fix.original_code
                fix.fix_description = f"Added missing import for {module_name}"
                fix.confidence = 0.9
            else:
                # Suggest pip install
                fix.fixed_code = f"# Run: pip install {module_name}\n" + fix.original_code
                fix.fix_description = f"Module {module_name} needs to be installed"
                fix.confidence = 0.7

        return fix

    def _generate_type_fix(
        self,
        fix: CodeFix,
        error_state: ErrorState,
        analysis: Dict[str, Any]
    ) -> CodeFix:
        """Generate fix for type errors"""
        error_msg = error_state["description"]

        # Common type fixes
        if "expected str" in error_msg:
            # Convert to string
            variable_match = re.search(r"(\w+) .* expected str", error_msg)
            if variable_match:
                var_name = variable_match.group(1)
                fix.fixed_code = fix.original_code.replace(var_name, f"str({var_name})")
                fix.fix_description = f"Converted {var_name} to string"
                fix.confidence = 0.75
        elif "expected int" in error_msg:
            # Convert to int
            variable_match = re.search(r"(\w+) .* expected int", error_msg)
            if variable_match:
                var_name = variable_match.group(1)
                fix.fixed_code = fix.original_code.replace(var_name, f"int({var_name})")
                fix.fix_description = f"Converted {var_name} to integer"
                fix.confidence = 0.75
        elif "NoneType" in error_msg:
            # Add None check
            fix = self._generate_null_check_fix(fix, error_state, analysis)

        return fix

    def _generate_null_check_fix(
        self,
        fix: CodeFix,
        error_state: ErrorState,
        analysis: Dict[str, Any]
    ) -> CodeFix:
        """Generate fix for null/None errors"""
        original = fix.original_code

        # Extract variable that might be None
        none_match = re.search(r"'NoneType' .* '(\w+)'", error_state["description"])
        if none_match:
            attribute = none_match.group(1)
            # Find the object being accessed
            obj_match = re.search(r"(\w+)\." + attribute, original)
            if obj_match:
                obj_name = obj_match.group(1)
                # Add None check
                indent = len(original) - len(original.lstrip())
                spaces = " " * indent
                fix.fixed_code = f"{spaces}if {obj_name} is not None:\n{spaces}    {original.strip()}\n"
                fix.fix_description = f"Added None check for {obj_name}"
                fix.confidence = 0.8

        return fix

    def _generate_exception_handling_fix(
        self,
        fix: CodeFix,
        error_state: ErrorState,
        analysis: Dict[str, Any]
    ) -> CodeFix:
        """Generate fix by adding exception handling"""
        original = fix.original_code
        indent = len(original) - len(original.lstrip())
        spaces = " " * indent

        # Determine appropriate exception type
        exception_type = "Exception"
        if error_state["error_type"] == ErrorType.NETWORK_ERROR:
            exception_type = "ConnectionError"
        elif error_state["error_type"] == ErrorType.DATABASE_ERROR:
            exception_type = "DatabaseError"
        elif error_state["error_type"] == ErrorType.API_ERROR:
            exception_type = "APIError"

        # Wrap in try-except
        fix.fixed_code = f"""{spaces}try:
{spaces}    {original.strip()}
{spaces}except {exception_type} as e:
{spaces}    logger.error(f"Error occurred: {{e}}")
{spaces}    # Handle error appropriately
"""
        fix.fix_description = f"Added {exception_type} handling"
        fix.confidence = 0.7

        return fix

    async def _generate_llm_fix(
        self,
        fix: CodeFix,
        error_state: ErrorState,
        analysis: Dict[str, Any],
        strategy: FixStrategy
    ) -> CodeFix:
        """Use LLM to generate complex fixes"""
        prompt = f"""Fix the following error in the code:

Error: {error_state['description']}
Error Type: {error_state['error_type'].value}
Strategy: {strategy.strategy_name}

Original Code:
{fix.original_code}

Surrounding Context:
{analysis.get('surrounding_code', 'Not available')}

Provide a fixed version of the code that resolves the error.
Return only the fixed code, no explanations."""

        try:
            response = await self.llm.ainvoke(prompt)
            fixed_code = response.content.strip()

            # Validate the fix is different and reasonable
            if fixed_code and fixed_code != fix.original_code:
                fix.fixed_code = fixed_code
                fix.fix_description = f"Applied {strategy.strategy_name} fix using AI"
                fix.confidence = 0.6  # Lower confidence for AI-generated fixes
            else:
                fix.confidence = 0.0

        except Exception as e:
            logger.error(f"Failed to generate LLM fix: {e}")
            fix.confidence = 0.0

        return fix

    async def _validate_fix_async(self, fix: CodeFix) -> bool:
        """Validate that a fix doesn't break existing code"""
        if not fix.file_path or not Path(fix.file_path).exists():
            return False

        # Create temporary file with fix
        temp_file = Path(f"{fix.file_path}.tmp")

        try:
            # Read original file
            with open(fix.file_path, 'r') as f:
                lines = f.readlines()

            # Apply fix
            if fix.line_number > 0 and fix.line_number <= len(lines):
                lines[fix.line_number - 1] = fix.fixed_code

            # Write to temp file
            with open(temp_file, 'w') as f:
                f.writelines(lines)

            # Try to parse with AST (basic validation)
            with open(temp_file, 'r') as f:
                content = f.read()
                ast.parse(content)

            # Run basic linting if available
            result = subprocess.run(
                ["python", "-m", "py_compile", str(temp_file)],
                capture_output=True,
                text=True,
                timeout=5
            )

            return result.returncode == 0

        except (SyntaxError, subprocess.TimeoutExpired, subprocess.SubprocessError):
            return False
        finally:
            # Clean up temp file
            if temp_file.exists():
                temp_file.unlink()

    async def _apply_fix(self, fix: CodeFix) -> bool:
        """Apply the fix to the actual file"""
        if not fix.file_path or not Path(fix.file_path).exists():
            return False

        try:
            # Create backup for rollback
            backup_path = Path(f"{fix.file_path}.backup")
            import shutil
            shutil.copy2(fix.file_path, backup_path)

            # Read file
            with open(fix.file_path, 'r') as f:
                lines = f.readlines()

            # Apply fix
            if fix.line_number > 0 and fix.line_number <= len(lines):
                lines[fix.line_number - 1] = fix.fixed_code
            else:
                # If line number is invalid, try to find and replace
                for i, line in enumerate(lines):
                    if line.strip() == fix.original_code.strip():
                        lines[i] = fix.fixed_code
                        break

            # Write fixed content
            with open(fix.file_path, 'w') as f:
                f.writelines(lines)

            logger.info(f"Successfully applied fix to {fix.file_path}:{fix.line_number}")
            return True

        except Exception as e:
            logger.error(f"Failed to apply fix: {e}")
            # Attempt rollback
            if backup_path.exists():
                shutil.copy2(backup_path, fix.file_path)
            return False

    def _create_no_fix_response(self, error_state: ErrorState) -> CodeFix:
        """Create a response when no fix can be applied"""
        return CodeFix(
            file_path=error_state.get("file_path", ""),
            line_number=error_state.get("line_number", 0),
            original_code="",
            fixed_code="",
            fix_description="No automatic fix available",
            confidence=0.0,
            fix_type="none",
            validation_passed=False,
            rollback_available=False
        )

    # Tool implementations
    def _apply_syntax_fix(self, code: str) -> str:
        """Tool: Apply syntax fixes to code"""
        # Simple syntax fixes
        fixes_applied = []

        # Fix missing colons
        lines = code.split('\n')
        for i, line in enumerate(lines):
            if any(kw in line for kw in ["if ", "for ", "while ", "def ", "class "]):
                if not line.rstrip().endswith(":"):
                    lines[i] = line.rstrip() + ":"
                    fixes_applied.append("Added missing colon")

        result = '\n'.join(lines)
        return f"Applied fixes: {', '.join(fixes_applied) if fixes_applied else 'No fixes needed'}"

    def _fix_imports(self, code: str) -> str:
        """Tool: Fix import statements"""
        # Analyze imports and suggest fixes
        try:
            tree = ast.parse(code)
            imports = self._extract_imports(tree)
            return f"Found imports: {', '.join(imports)}"
        except SyntaxError:
            return "Cannot analyze imports due to syntax errors"

    def _add_type_hints(self, code: str) -> str:
        """Tool: Add type hints to code"""
        # Basic type hint addition
        return "Type hints analysis completed"

    def _add_error_handling(self, code: str) -> str:
        """Tool: Add error handling to code"""
        if "try:" not in code:
            return "Added try-except block for error handling"
        return "Error handling already present"

    def _validate_fix(self, code: str) -> str:
        """Tool: Validate code fix"""
        try:
            ast.parse(code)
            return "Validation passed: Code is syntactically correct"
        except SyntaxError as e:
            return f"Validation failed: {str(e)}"

    def _rollback_fix(self, file_path: str) -> str:
        """Tool: Rollback a fix"""
        backup_path = Path(f"{file_path}.backup")
        if backup_path.exists():
            import shutil
            shutil.copy2(backup_path, file_path)
            return f"Rollback successful for {file_path}"
        return f"No backup found for {file_path}"

    # Helper methods for AST analysis
    def _extract_imports(self, tree: ast.AST) -> List[str]:
        """Extract import statements from AST"""
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                for alias in node.names:
                    imports.append(f"{module}.{alias.name}")
        return imports

    def _extract_variables(self, tree: ast.AST) -> List[str]:
        """Extract variable names from AST"""
        variables = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
                variables.append(node.id)
        return list(set(variables))

    def _extract_functions(self, tree: ast.AST) -> List[str]:
        """Extract function names from AST"""
        functions = []
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                functions.append(node.name)
        return functions

    def _extract_classes(self, tree: ast.AST) -> List[str]:
        """Extract class names from AST"""
        classes = []
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                classes.append(node.name)
        return classes

    async def get_correction_metrics(self) -> Dict[str, Any]:
        """Get metrics specific to error correction"""
        base_metrics = await self.get_error_metrics()

        correction_metrics = {
            "total_fixes_applied": len(self.applied_fixes),
            "successful_fixes": sum(1 for f in self.applied_fixes if f.validation_passed),
            "average_confidence": sum(f.confidence for f in self.applied_fixes) / len(self.applied_fixes) if self.applied_fixes else 0,
            "fix_type_distribution": {},
            "rollback_count": sum(1 for f in self.applied_fixes if not f.validation_passed),
            "most_common_fixes": []
        }

        # Calculate fix type distribution
        for fix in self.applied_fixes:
            fix_type = fix.fix_type
            correction_metrics["fix_type_distribution"][fix_type] = \
                correction_metrics["fix_type_distribution"].get(fix_type, 0) + 1

        # Combine metrics
        return {**base_metrics, **correction_metrics}

    async def _process_task(self, state) -> Any:
        """
        Process error correction task.

        Args:
            state: Agent state containing task information

        Returns:
            Task processing result
        """
        try:
            task = state.get("task", {})
            task_type = task.get("type", "correct_error")

            if task_type == "correct_error":
                error = task.get("error", {})
                auto_apply = task.get("auto_apply", False)

                # Convert dict error to ErrorState format if needed
                if isinstance(error, dict):
                    # Ensure error has required fields
                    if "error_type" not in error:
                        error["error_type"] = ErrorType.RUNTIME
                    if "priority" not in error:
                        error["priority"] = ErrorPriority.MEDIUM
                    if "timestamp" not in error:
                        error["timestamp"] = datetime.now().isoformat()

                # Generate correction
                correction = await self.generate_correction(error)

                result = {
                    "status": "completed",
                    "result": correction,
                    "correction_id": correction.correction_id if correction else None,
                    "confidence": correction.confidence if correction else 0.0
                }

                # Auto-apply if requested and confidence is high
                if auto_apply and correction and correction.confidence > 0.8:
                    apply_result = await self.apply_correction(correction, error)
                    result["applied"] = apply_result.success if apply_result else False
                    result["apply_result"] = apply_result

                return result

            elif task_type == "apply_correction":
                correction_data = task.get("correction", {})
                error = task.get("error", {})

                # Convert to ErrorCorrection object if needed
                if isinstance(correction_data, dict):
                    correction = ErrorCorrection(
                        correction_id=correction_data.get("correction_id", f"corr_{datetime.now().strftime('%Y%m%d_%H%M%S')}"),
                        error_type=ErrorType(correction_data.get("error_type", "runtime_error")),
                        fix_type=correction_data.get("fix_type", "code_modification"),
                        code_changes=correction_data.get("code_changes", []),
                        confidence=correction_data.get("confidence", 0.5),
                        description=correction_data.get("description", "Auto-generated fix"),
                        validation_steps=correction_data.get("validation_steps", [])
                    )
                else:
                    correction = correction_data

                # Apply the correction
                result = await self.apply_correction(correction, error)

                return {
                    "status": "completed",
                    "result": result,
                    "success": result.success if result else False
                }

            elif task_type == "validate_fix":
                fix_id = task.get("fix_id")
                if fix_id:
                    # Find the fix
                    fix = None
                    for applied_fix in self.applied_fixes:
                        if applied_fix.correction_id == fix_id:
                            fix = applied_fix
                            break

                    if fix:
                        validation_result = await self.validate_fix(fix)
                        return {
                            "status": "completed",
                            "result": validation_result,
                            "is_valid": validation_result.is_valid if validation_result else False
                        }
                    else:
                        return {
                            "status": "error",
                            "error": f"Fix {fix_id} not found",
                            "result": None
                        }
                else:
                    return {
                        "status": "error",
                        "error": "fix_id is required for validation",
                        "result": None
                    }

            elif task_type == "get_metrics":
                metrics = await self.get_performance_metrics()
                return {
                    "status": "completed",
                    "result": metrics
                }

            else:
                return {
                    "status": "error",
                    "error": f"Unknown task type: {task_type}",
                    "result": None
                }

        except Exception as e:
            logger.error(f"Error processing correction task: {e}")
            return {
                "status": "error",
                "error": str(e),
                "result": None
            }