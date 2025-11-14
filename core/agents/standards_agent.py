"""
Standards Agent - Coding standards verification and DSA consistency

Ensures code quality, standards compliance, and best practices.
"""

import ast
import json
import logging
import re
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from .base_agent import AgentConfig, AgentState, BaseAgent, TaskResult

logger = logging.getLogger(__name__)


class StandardsType:
    """Standards check types"""

    PEP8 = "pep8"
    TYPING = "typing"
    DOCSTRINGS = "docstrings"
    NAMING = "naming"
    IMPORTS = "imports"
    COMPLEXITY = "complexity"
    SECURITY = "security"
    BEST_PRACTICES = "best_practices"
    DSA_PATTERNS = "dsa_patterns"
    PROJECT_CONVENTIONS = "project_conventions"


class StandardsAgent(BaseAgent):
    """
    Agent responsible for code standards verification and enforcement.

    Capabilities:
    - PEP8 compliance checking
    - Type hint verification
    - Docstring completeness
    - Naming convention enforcement
    - Import organization
    - Complexity analysis
    - Security pattern detection
    - DSA consistency checks
    - Project-specific conventions
    """

    def __init__(self, config: Optional[AgentConfig] = None):
        if not config:
            config = AgentConfig(
                name="StandardsAgent",
                model="gpt-3.5-turbo",
                temperature=0.1,
                system_prompt=self._get_standards_prompt(),
            )
        super().__init__(config)

        self.violations = []
        self.metrics = {
            "files_checked": 0,
            "violations_found": 0,
            "critical_issues": 0,
            "auto_fixed": 0,
            "compliance_score": 100.0,
        }

        # Project-specific standards
        self.project_standards = {
            "max_line_length": 120,
            "max_complexity": 10,
            "min_coverage": 80,
            "required_docstring": True,
            "type_hints_required": True,
            "naming_convention": "snake_case",
            "import_order": ["standard", "third_party", "local"],
        }

        # DSA patterns to verify
        self.dsa_patterns = {
            "singleton": r"class\s+\w+.*:\s*\n\s*_instance\s*=\s*None",
            "factory": r"def\s+create_\w+\s*\(",
            "observer": r"def\s+(subscribe|notify|update)\s*\(",
            "strategy": r"class\s+\w+Strategy.*:\s*\n\s*@abstractmethod",
            "decorator": r"def\s+\w+\s*\(.*\):\s*\n\s*def\s+wrapper",
            "async_patterns": r"async\s+def\s+\w+.*await",
            "error_handling": r"try:.*except.*finally:",
            "context_manager": r"def\s+__enter__.*def\s+__exit__",
        }

    def _get_standards_prompt(self) -> str:
        """Get specialized standards prompt"""
        return """You are a Standards Agent specialized in code quality and standards enforcement.

Your responsibilities:
- Verify PEP8 compliance
- Check type hints and annotations
- Ensure proper documentation
- Enforce naming conventions
- Organize imports properly
- Analyze code complexity
- Detect security issues
- Verify DSA pattern implementation
- Maintain project conventions
- Suggest improvements

Always enforce high code quality standards and best practices.
"""

    async def _process_task(self, state: AgentState) -> Any:
        """Process standards checking tasks"""
        state["task"]
        context = state["context"]

        # Determine check type
        check_type = context.get("check_type", StandardsType.PEP8)
        target_path = context.get("target_path", ".")

        # Execute appropriate check
        if check_type == StandardsType.PEP8:
            return await self._check_pep8_compliance(target_path, context)
        elif check_type == StandardsType.TYPING:
            return await self._check_type_hints(target_path, context)
        elif check_type == StandardsType.DOCSTRINGS:
            return await self._check_docstrings(target_path, context)
        elif check_type == StandardsType.COMPLEXITY:
            return await self._check_complexity(target_path, context)
        elif check_type == StandardsType.SECURITY:
            return await self._check_security_patterns(target_path, context)
        elif check_type == StandardsType.DSA_PATTERNS:
            return await self._check_dsa_patterns(target_path, context)
        else:
            return await self._comprehensive_standards_check(target_path, context)

    async def _check_pep8_compliance(
        self, target_path: str, context: dict[str, Any]
    ) -> dict[str, Any]:
        """Check PEP8 compliance using flake8"""
        logger.info(f"Checking PEP8 compliance in {target_path}")

        violations = []

        try:
            # Run flake8
            result = subprocess.run(
                ["flake8", "--max-line-length=120", "--format=json", target_path],
                capture_output=True,
                text=True,
                timeout=60,
            )

            if result.stdout:
                # Parse flake8 JSON output
                try:
                    flake8_output = json.loads(result.stdout)
                    for file_path, file_violations in flake8_output.items():
                        for violation in file_violations:
                            violations.append(
                                {
                                    "file": file_path,
                                    "line": violation.get("line_number"),
                                    "column": violation.get("column_number"),
                                    "code": violation.get("code"),
                                    "message": violation.get("text"),
                                    "severity": "warning",
                                }
                            )
                except json.JSONDecodeError:
                    # Fallback to text parsing
                    lines = result.stdout.split("\n")
                    for line in lines:
                        if line and ":" in line:
                            parts = line.split(":")
                            if len(parts) >= 4:
                                violations.append(
                                    {
                                        "file": parts[0],
                                        "line": parts[1],
                                        "column": parts[2],
                                        "message": ":".join(parts[3:]),
                                        "severity": "warning",
                                    }
                                )

            # Auto-fix with black if requested
            if context.get("auto_fix", False):
                fixed_count = await self._auto_fix_formatting(target_path)
                self.metrics["auto_fixed"] += fixed_count

        except subprocess.TimeoutExpired:
            logger.error("PEP8 check timed out")
            return {"error": "Check timed out"}
        except FileNotFoundError:
            logger.warning("flake8 not found, using alternative check")
            violations = await self._check_pep8_manual(target_path)

        self.violations.extend(violations)
        self.metrics["violations_found"] += len(violations)
        self.metrics["files_checked"] += self._count_python_files(target_path)

        return {
            "check_type": "pep8",
            "violations_count": len(violations),
            "violations": violations[:50],  # First 50
            "auto_fixed": self.metrics["auto_fixed"],
            "compliance_score": self._calculate_compliance_score(violations),
        }

    async def _check_type_hints(self, target_path: str, context: dict[str, Any]) -> dict[str, Any]:
        """Check type hints using mypy"""
        logger.info(f"Checking type hints in {target_path}")

        violations = []

        try:
            # Run mypy
            result = subprocess.run(
                ["mypy", "--json-report", "-", target_path],
                capture_output=True,
                text=True,
                timeout=120,
            )

            if result.stdout:
                lines = result.stdout.split("\n")
                for line in lines:
                    if line and ":" in line:
                        parts = line.split(":")
                        if len(parts) >= 3:
                            violations.append(
                                {
                                    "file": parts[0],
                                    "line": parts[1],
                                    "message": ":".join(parts[2:]),
                                    "type": "typing",
                                    "severity": "error" if "error" in line.lower() else "warning",
                                }
                            )

        except subprocess.TimeoutExpired:
            logger.error("Type checking timed out")
        except FileNotFoundError:
            logger.warning("mypy not found, using AST analysis")
            violations = await self._check_type_hints_ast(target_path)

        self.violations.extend(violations)
        self.metrics["violations_found"] += len(violations)

        # Calculate typing coverage
        typing_coverage = await self._calculate_typing_coverage(target_path)

        return {
            "check_type": "typing",
            "violations_count": len(violations),
            "violations": violations[:50],
            "typing_coverage": typing_coverage,
            "requires_type_stubs": self._identify_missing_stubs(violations),
        }

    async def _check_docstrings(self, target_path: str, context: dict[str, Any]) -> dict[str, Any]:
        """Check docstring completeness"""
        logger.info(f"Checking docstrings in {target_path}")

        violations = []
        path = Path(target_path)

        for py_file in path.rglob("*.py"):
            if "venv" in str(py_file) or "__pycache__" in str(py_file):
                continue

            try:
                with open(py_file) as f:
                    tree = ast.parse(f.read())

                for node in ast.walk(tree):
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                        docstring = ast.get_docstring(node)

                        if not docstring:
                            violations.append(
                                {
                                    "file": str(py_file),
                                    "line": node.lineno,
                                    "name": node.name,
                                    "type": "missing_docstring",
                                    "message": f"{node.__class__.__name__} '{node.name}' missing docstring",
                                    "severity": "warning",
                                }
                            )
                        elif len(docstring) < 10:
                            violations.append(
                                {
                                    "file": str(py_file),
                                    "line": node.lineno,
                                    "name": node.name,
                                    "type": "incomplete_docstring",
                                    "message": f"{node.__class__.__name__} '{node.name}' has incomplete docstring",
                                    "severity": "info",
                                }
                            )

                        # Check parameter documentation for functions
                        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                            if docstring and node.args.args:
                                for arg in node.args.args:
                                    if arg.arg != "self" and arg.arg not in docstring:
                                        violations.append(
                                            {
                                                "file": str(py_file),
                                                "line": node.lineno,
                                                "name": node.name,
                                                "type": "undocumented_parameter",
                                                "message": f"Parameter '{arg.arg}' not documented",
                                                "severity": "info",
                                            }
                                        )

            except Exception as e:
                logger.warning(f"Error checking {py_file}: {e}")

        self.violations.extend(violations)
        self.metrics["violations_found"] += len(violations)

        return {
            "check_type": "docstrings",
            "violations_count": len(violations),
            "violations": violations[:50],
            "coverage": self._calculate_docstring_coverage(violations, path),
        }

    async def _check_complexity(self, target_path: str, context: dict[str, Any]) -> dict[str, Any]:
        """Check code complexity"""
        logger.info(f"Checking code complexity in {target_path}")

        complex_functions = []

        try:
            # Use radon for complexity analysis
            result = subprocess.run(
                ["radon", "cc", "-j", target_path],
                capture_output=True,
                text=True,
                timeout=60,
            )

            if result.stdout:
                complexity_data = json.loads(result.stdout)

                for file_path, file_data in complexity_data.items():
                    for func_data in file_data:
                        if func_data["complexity"] > self.project_standards["max_complexity"]:
                            complex_functions.append(
                                {
                                    "file": file_path,
                                    "function": func_data["name"],
                                    "complexity": func_data["complexity"],
                                    "rank": func_data["rank"],
                                    "line": func_data["lineno"],
                                }
                            )

        except (subprocess.TimeoutExpired, FileNotFoundError, json.JSONDecodeError):
            logger.warning("Radon not available, using AST analysis")
            complex_functions = await self._check_complexity_ast(target_path)

        if complex_functions:
            self.metrics["critical_issues"] += len(complex_functions)

        return {
            "check_type": "complexity",
            "complex_functions": complex_functions,
            "max_complexity": (
                max([f["complexity"] for f in complex_functions]) if complex_functions else 0
            ),
            "average_complexity": (
                sum([f["complexity"] for f in complex_functions]) / len(complex_functions)
                if complex_functions
                else 0
            ),
            "threshold": self.project_standards["max_complexity"],
        }

    async def _check_security_patterns(
        self, target_path: str, context: dict[str, Any]
    ) -> dict[str, Any]:
        """Check for security issues"""
        logger.info(f"Checking security patterns in {target_path}")

        security_issues = []

        # Common security patterns to check
        security_patterns = {
            "hardcoded_password": r'password\s*=\s*["\'].*["\']',
            "eval_usage": r"\beval\s*\(",
            "exec_usage": r"\bexec\s*\(",
            "pickle_usage": r"pickle\.(load|loads)\s*\(",
            "sql_injection": r'".+?\s+(SELECT|INSERT|UPDATE|DELETE).+?\s+.*"\s*%',
            "os_command": r"os\.(system|popen)\s*\(",
            "insecure_random": r"random\.\w+\s*\(",
            "hardcoded_key": r'(api_key|secret|token)\s*=\s*["\'][\w\d]+["\']',
        }

        path = Path(target_path)

        for py_file in path.rglob("*.py"):
            if "venv" in str(py_file) or "__pycache__" in str(py_file):
                continue

            try:
                with open(py_file) as f:
                    content = f.read()
                    lines = content.split("\n")

                for pattern_name, pattern in security_patterns.items():
                    matches = re.finditer(pattern, content, re.IGNORECASE)
                    for match in matches:
                        line_num = content[: match.start()].count("\n") + 1
                        security_issues.append(
                            {
                                "file": str(py_file),
                                "line": line_num,
                                "type": pattern_name,
                                "code": (
                                    lines[line_num - 1].strip() if line_num <= len(lines) else ""
                                ),
                                "severity": (
                                    "critical"
                                    if pattern_name in ["hardcoded_password", "sql_injection"]
                                    else "warning"
                                ),
                            }
                        )

            except Exception as e:
                logger.warning(f"Error checking {py_file}: {e}")

        if security_issues:
            self.metrics["critical_issues"] += sum(
                1 for i in security_issues if i["severity"] == "critical"
            )

        return {
            "check_type": "security",
            "issues_found": len(security_issues),
            "critical_count": sum(1 for i in security_issues if i["severity"] == "critical"),
            "issues": security_issues[:50],
            "recommendations": self._generate_security_recommendations(security_issues),
        }

    async def _check_dsa_patterns(
        self, target_path: str, context: dict[str, Any]
    ) -> dict[str, Any]:
        """Check DSA pattern implementation"""
        logger.info(f"Checking DSA patterns in {target_path}")

        pattern_usage = {pattern: [] for pattern in self.dsa_patterns}
        path = Path(target_path)

        for py_file in path.rglob("*.py"):
            if "venv" in str(py_file) or "__pycache__" in str(py_file):
                continue

            try:
                with open(py_file) as f:
                    content = f.read()

                for pattern_name, pattern_regex in self.dsa_patterns.items():
                    if re.search(pattern_regex, content):
                        pattern_usage[pattern_name].append(str(py_file))

            except Exception as e:
                logger.warning(f"Error checking {py_file}: {e}")

        # Analyze pattern consistency
        consistency_analysis = await self._analyze_pattern_consistency(pattern_usage, path)

        return {
            "check_type": "dsa_patterns",
            "patterns_found": {k: len(v) for k, v in pattern_usage.items()},
            "pattern_files": {k: v[:10] for k, v in pattern_usage.items()},  # First 10 files
            "consistency_analysis": consistency_analysis,
            "recommendations": self._generate_dsa_recommendations(pattern_usage),
        }

    async def _comprehensive_standards_check(
        self, target_path: str, context: dict[str, Any]
    ) -> dict[str, Any]:
        """Run all standards checks"""
        logger.info(f"Running comprehensive standards check in {target_path}")

        results = {}

        # Run all checks
        checks = [
            ("pep8", self._check_pep8_compliance),
            ("typing", self._check_type_hints),
            ("docstrings", self._check_docstrings),
            ("complexity", self._check_complexity),
            ("security", self._check_security_patterns),
            ("dsa_patterns", self._check_dsa_patterns),
        ]

        for check_name, check_func in checks:
            try:
                result = await check_func(target_path, context)
                results[check_name] = result
            except Exception as e:
                logger.error(f"Error in {check_name}: {e}")
                results[check_name] = {"error": str(e)}

        # Calculate overall compliance score
        overall_score = self._calculate_overall_compliance(results)

        # Generate improvement plan
        improvement_plan = await self._generate_improvement_plan(results)

        return {
            "check_type": "comprehensive",
            "checks": results,
            "overall_score": overall_score,
            "total_violations": self.metrics["violations_found"],
            "critical_issues": self.metrics["critical_issues"],
            "improvement_plan": improvement_plan,
            "metrics": self.metrics,
        }

    async def _auto_fix_formatting(self, target_path: str) -> int:
        """Auto-fix formatting issues with black"""
        try:
            result = subprocess.run(
                ["black", "--line-length=120", target_path],
                capture_output=True,
                text=True,
                timeout=60,
            )

            # Count fixed files from black output
            if "reformatted" in result.stdout:
                import re

                match = re.search(r"(\d+) files? reformatted", result.stdout)
                if match:
                    return int(match.group(1))

        except Exception as e:
            logger.warning(f"Auto-fix failed: {e}")

        return 0

    async def _check_pep8_manual(self, target_path: str) -> list[dict[str, Any]]:
        """Manual PEP8 checking using AST"""
        violations = []
        path = Path(target_path)

        for py_file in path.rglob("*.py"):
            if "venv" in str(py_file) or "__pycache__" in str(py_file):
                continue

            try:
                with open(py_file) as f:
                    lines = f.readlines()

                for i, line in enumerate(lines, 1):
                    # Check line length
                    if len(line.rstrip()) > self.project_standards["max_line_length"]:
                        violations.append(
                            {
                                "file": str(py_file),
                                "line": i,
                                "message": f"Line too long ({len(line.rstrip())} > {self.project_standards['max_line_length']})",
                                "severity": "warning",
                            }
                        )

                    # Check trailing whitespace
                    if line.rstrip() != line.rstrip("\n").rstrip("\r"):
                        violations.append(
                            {
                                "file": str(py_file),
                                "line": i,
                                "message": "Trailing whitespace",
                                "severity": "info",
                            }
                        )

            except Exception as e:
                logger.warning(f"Error checking {py_file}: {e}")

        return violations

    async def _check_type_hints_ast(self, target_path: str) -> list[dict[str, Any]]:
        """Check type hints using AST"""
        violations = []
        path = Path(target_path)

        for py_file in path.rglob("*.py"):
            if "venv" in str(py_file) or "__pycache__" in str(py_file):
                continue

            try:
                with open(py_file) as f:
                    tree = ast.parse(f.read())

                for node in ast.walk(tree):
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        # Check return type hint
                        if not node.returns and node.name != "__init__":
                            violations.append(
                                {
                                    "file": str(py_file),
                                    "line": node.lineno,
                                    "message": f"Function '{node.name}' missing return type hint",
                                    "severity": "warning",
                                }
                            )

                        # Check parameter type hints
                        for arg in node.args.args:
                            if arg.arg != "self" and not arg.annotation:
                                violations.append(
                                    {
                                        "file": str(py_file),
                                        "line": node.lineno,
                                        "message": f"Parameter '{arg.arg}' in '{node.name}' missing type hint",
                                        "severity": "warning",
                                    }
                                )

            except Exception as e:
                logger.warning(f"Error checking {py_file}: {e}")

        return violations

    async def _check_complexity_ast(self, target_path: str) -> list[dict[str, Any]]:
        """Check complexity using AST"""
        complex_functions = []
        path = Path(target_path)

        for py_file in path.rglob("*.py"):
            if "venv" in str(py_file) or "__pycache__" in str(py_file):
                continue

            try:
                with open(py_file) as f:
                    tree = ast.parse(f.read())

                for node in ast.walk(tree):
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        complexity = self._calculate_cyclomatic_complexity(node)

                        if complexity > self.project_standards["max_complexity"]:
                            complex_functions.append(
                                {
                                    "file": str(py_file),
                                    "function": node.name,
                                    "complexity": complexity,
                                    "line": node.lineno,
                                }
                            )

            except Exception as e:
                logger.warning(f"Error checking {py_file}: {e}")

        return complex_functions

    def _calculate_cyclomatic_complexity(self, node: ast.AST) -> int:
        """Calculate cyclomatic complexity of a function"""
        complexity = 1  # Base complexity

        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1

        return complexity

    def _count_python_files(self, target_path: str) -> int:
        """Count Python files in directory"""
        path = Path(target_path)
        return len(list(path.rglob("*.py")))

    def _calculate_compliance_score(self, violations: list[dict[str, Any]]) -> float:
        """Calculate compliance score"""
        if not violations:
            return 100.0

        # Deduct points based on severity
        score = 100.0
        for violation in violations:
            severity = violation.get("severity", "info")
            if severity == "critical":
                score -= 5
            elif severity == "error":
                score -= 3
            elif severity == "warning":
                score -= 1
            else:
                score -= 0.5

        return max(0, score)

    async def _calculate_typing_coverage(self, target_path: str) -> float:
        """Calculate typing coverage percentage"""
        total_functions = 0
        typed_functions = 0

        path = Path(target_path)
        for py_file in path.rglob("*.py"):
            if "venv" in str(py_file) or "__pycache__" in str(py_file):
                continue

            try:
                with open(py_file) as f:
                    tree = ast.parse(f.read())

                for node in ast.walk(tree):
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        total_functions += 1
                        if node.returns or any(arg.annotation for arg in node.args.args):
                            typed_functions += 1

            except Exception:
                pass

        return (typed_functions / total_functions * 100) if total_functions > 0 else 0

    def _identify_missing_stubs(self, violations: list[dict[str, Any]]) -> list[str]:
        """Identify missing type stubs"""
        missing_stubs = set()

        for violation in violations:
            if "import" in violation.get("message", "").lower():
                # Extract module name
                import_match = re.search(r"import\s+(\w+)", violation.get("message", ""))
                if import_match:
                    missing_stubs.add(import_match.group(1))

        return list(missing_stubs)

    def _calculate_docstring_coverage(self, violations: list[dict[str, Any]], path: Path) -> float:
        """Calculate docstring coverage"""
        total_items = 0
        missing_docstrings = sum(1 for v in violations if v.get("type") == "missing_docstring")

        # Count total functions and classes
        for py_file in path.rglob("*.py"):
            if "venv" in str(py_file) or "__pycache__" in str(py_file):
                continue

            try:
                with open(py_file) as f:
                    tree = ast.parse(f.read())

                for node in ast.walk(tree):
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                        total_items += 1
            except Exception:
                pass

        if total_items == 0:
            return 100.0

        return ((total_items - missing_docstrings) / total_items) * 100

    def _generate_security_recommendations(self, issues: list[dict[str, Any]]) -> list[str]:
        """Generate security recommendations"""
        recommendations = []

        issue_types = set(i["type"] for i in issues)

        if "hardcoded_password" in issue_types:
            recommendations.append("Use environment variables for passwords")
        if "sql_injection" in issue_types:
            recommendations.append("Use parameterized queries to prevent SQL injection")
        if "eval_usage" in issue_types:
            recommendations.append(
                "Replace ast.literal_eval() with ast.literal_eval() or safer alternatives"
            )
        if "insecure_random" in issue_types:
            recommendations.append("Use secrets module for cryptographic randomness")

        return recommendations

    def _generate_dsa_recommendations(self, pattern_usage: dict[str, list[str]]) -> list[str]:
        """Generate DSA pattern recommendations"""
        recommendations = []

        if not pattern_usage["singleton"]:
            recommendations.append("Consider implementing Singleton pattern for shared resources")
        if not pattern_usage["factory"]:
            recommendations.append("Use Factory pattern for complex object creation")
        if not pattern_usage["error_handling"]:
            recommendations.append("Implement comprehensive error handling patterns")
        if not pattern_usage["async_patterns"]:
            recommendations.append("Consider async/await for I/O operations")

        return recommendations

    async def _analyze_pattern_consistency(
        self, pattern_usage: dict[str, list[str]], path: Path
    ) -> dict[str, Any]:
        """Analyze pattern consistency across codebase"""
        return {
            "singleton_consistency": len(pattern_usage["singleton"]) <= 3,  # Should be limited
            "factory_usage": len(pattern_usage["factory"]) > 0,
            "async_coverage": len(pattern_usage["async_patterns"])
            / max(1, self._count_python_files(str(path)))
            * 100,
            "error_handling_coverage": len(pattern_usage["error_handling"]) > 5,
        }

    def _calculate_overall_compliance(self, results: dict[str, Any]) -> float:
        """Calculate overall compliance score"""
        scores = []

        if "pep8" in results and "compliance_score" in results["pep8"]:
            scores.append(results["pep8"]["compliance_score"])

        if "typing" in results and "typing_coverage" in results["typing"]:
            scores.append(results["typing"]["typing_coverage"])

        if "docstrings" in results and "coverage" in results["docstrings"]:
            scores.append(results["docstrings"]["coverage"])

        if "complexity" in results:
            # Inverse score for complexity
            max_complexity = results["complexity"].get("max_complexity", 0)
            if max_complexity > 0:
                complexity_score = max(0, 100 - (max_complexity - 10) * 10)
                scores.append(complexity_score)

        if "security" in results:
            # Deduct for security issues
            critical_count = results["security"].get("critical_count", 0)
            security_score = max(0, 100 - critical_count * 20)
            scores.append(security_score)

        return sum(scores) / len(scores) if scores else 0

    async def _generate_improvement_plan(self, results: dict[str, Any]) -> list[dict[str, Any]]:
        """Generate improvement plan based on results"""
        plan = []

        # Prioritize critical issues
        if results.get("security", {}).get("critical_count", 0) > 0:
            plan.append(
                {
                    "priority": "critical",
                    "action": "Fix security vulnerabilities",
                    "details": "Address hardcoded passwords and SQL injection risks",
                }
            )

        # High complexity functions
        if results.get("complexity", {}).get("max_complexity", 0) > 15:
            plan.append(
                {
                    "priority": "high",
                    "action": "Refactor complex functions",
                    "details": "Break down functions with complexity > 15",
                }
            )

        # Missing type hints
        if results.get("typing", {}).get("typing_coverage", 100) < 50:
            plan.append(
                {
                    "priority": "medium",
                    "action": "Add type hints",
                    "details": "Improve typing coverage to at least 80%",
                }
            )

        # Missing docstrings
        if results.get("docstrings", {}).get("coverage", 100) < 70:
            plan.append(
                {
                    "priority": "low",
                    "action": "Add documentation",
                    "details": "Document all public functions and classes",
                }
            )

        return plan

    async def enforce_standards(self, target_path: str, fix: bool = False) -> TaskResult:
        """Enforce coding standards on target path"""
        logger.info(f"Enforcing standards on {target_path}")

        # Run comprehensive check
        context = {"auto_fix": fix}
        result = await self._comprehensive_standards_check(target_path, context)

        # Generate report
        report = {
            "path": target_path,
            "timestamp": datetime.now().isoformat(),
            "overall_score": result["overall_score"],
            "violations": self.metrics["violations_found"],
            "critical_issues": self.metrics["critical_issues"],
            "auto_fixed": self.metrics["auto_fixed"] if fix else 0,
            "improvement_plan": result["improvement_plan"],
        }

        return TaskResult(
            success=result["overall_score"] >= 70,
            output=report,
            metadata={"agent": self.name, "enforcement": True},
        )
