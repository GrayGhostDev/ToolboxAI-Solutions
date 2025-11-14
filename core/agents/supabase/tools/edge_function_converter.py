"""Edge Function converter tool for migrating FastAPI endpoints to Supabase Edge Functions."""

import ast
import json
import logging
import os
import re
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Optional

import aiofiles

logger = logging.getLogger(__name__)


class ConversionStatus(Enum):
    """Conversion status types."""

    SUCCESS = "success"
    PARTIAL = "partial"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class EndpointInfo:
    """Information about a FastAPI endpoint."""

    path: str
    method: str
    function_name: str
    parameters: list[dict[str, Any]]
    dependencies: list[str]
    middleware: list[str]
    auth_required: bool
    response_model: Optional[str]
    source_code: str
    file_path: str


@dataclass
class ConversionResult:
    """Result of endpoint conversion."""

    endpoint: EndpointInfo
    status: ConversionStatus
    edge_function_code: Optional[str]
    deployment_script: Optional[str]
    environment_variables: list[str]
    issues: list[str]
    suggestions: list[str]


class EdgeFunctionConverterTool:
    """
    Tool for converting FastAPI endpoints to Supabase Edge Functions.

    Features:
    - FastAPI endpoint analysis
    - TypeScript/Deno conversion
    - Function deployment scripts
    - Environment variable mapping
    - Dependency resolution
    """

    def __init__(self):
        """Initialize the Edge Function converter."""
        self.python_to_ts_types = {
            "str": "string",
            "int": "number",
            "float": "number",
            "bool": "boolean",
            "list": "Array",
            "dict": "Record<string, any>",
            "Any": "any",
            "Optional": "| null",
            "Union": "|",
            "List": "Array",
            "Dict": "Record",
        }

        self.unsupported_patterns = [
            "multipart/form-data",
            "file upload",
            "background tasks",
            "websocket",
            "server-sent events",
            "streaming response",
        ]

    async def analyze_fastapi_project(
        self,
        project_path: str,
        include_patterns: Optional[list[str]] = None,
        exclude_patterns: Optional[list[str]] = None,
    ) -> list[EndpointInfo]:
        """
        Analyze FastAPI project to extract endpoint information.

        Args:
            project_path: Path to FastAPI project
            include_patterns: File patterns to include
            exclude_patterns: File patterns to exclude

        Returns:
            List of endpoint information
        """
        logger.info(f"Analyzing FastAPI project: {project_path}")

        if include_patterns is None:
            include_patterns = ["*.py"]

        if exclude_patterns is None:
            exclude_patterns = ["test_*.py", "*_test.py", "__pycache__"]

        endpoints = []

        # Find all Python files
        python_files = self._find_python_files(project_path, include_patterns, exclude_patterns)

        for file_path in python_files:
            try:
                file_endpoints = await self._analyze_python_file(file_path)
                endpoints.extend(file_endpoints)
            except Exception as e:
                logger.warning(f"Failed to analyze {file_path}: {str(e)}")

        logger.info(f"Found {len(endpoints)} endpoints")
        return endpoints

    async def convert_endpoint(
        self, endpoint: EndpointInfo, target_directory: str, dry_run: bool = False
    ) -> ConversionResult:
        """
        Convert a single FastAPI endpoint to Edge Function.

        Args:
            endpoint: Endpoint information
            target_directory: Directory for generated files
            dry_run: If True, don't write files

        Returns:
            Conversion result
        """
        logger.info(f"Converting endpoint: {endpoint.method} {endpoint.path}")

        try:
            # Check if endpoint is convertible
            compatibility_check = self._check_compatibility(endpoint)
            if not compatibility_check["convertible"]:
                return ConversionResult(
                    endpoint=endpoint,
                    status=ConversionStatus.SKIPPED,
                    edge_function_code=None,
                    deployment_script=None,
                    environment_variables=[],
                    issues=compatibility_check["issues"],
                    suggestions=compatibility_check["suggestions"],
                )

            # Generate Edge Function code
            edge_function_code = await self._generate_edge_function(endpoint)

            # Generate deployment script
            deployment_script = await self._generate_deployment_script(endpoint)

            # Extract environment variables
            env_vars = self._extract_environment_variables(endpoint)

            # Write files if not dry run
            if not dry_run:
                await self._write_edge_function_files(
                    endpoint, target_directory, edge_function_code, deployment_script
                )

            return ConversionResult(
                endpoint=endpoint,
                status=ConversionStatus.SUCCESS,
                edge_function_code=edge_function_code,
                deployment_script=deployment_script,
                environment_variables=env_vars,
                issues=[],
                suggestions=[],
            )

        except Exception as e:
            logger.error(f"Conversion failed for {endpoint.path}: {str(e)}")
            return ConversionResult(
                endpoint=endpoint,
                status=ConversionStatus.FAILED,
                edge_function_code=None,
                deployment_script=None,
                environment_variables=[],
                issues=[f"Conversion error: {str(e)}"],
                suggestions=[],
            )

    async def convert_project(
        self,
        project_path: str,
        target_directory: str,
        dry_run: bool = False,
        progress_callback: Optional[callable] = None,
    ) -> dict[str, ConversionResult]:
        """
        Convert entire FastAPI project to Edge Functions.

        Args:
            project_path: Path to FastAPI project
            target_directory: Directory for generated files
            dry_run: If True, don't write files
            progress_callback: Optional progress callback

        Returns:
            Dictionary of conversion results
        """
        logger.info(f"Converting FastAPI project: {project_path}")

        # Analyze project
        endpoints = await self.analyze_fastapi_project(project_path)

        if not endpoints:
            logger.warning("No endpoints found in project")
            return {}

        # Convert each endpoint
        results = {}

        for i, endpoint in enumerate(endpoints):
            try:
                result = await self.convert_endpoint(endpoint, target_directory, dry_run)

                endpoint_key = f"{endpoint.method}_{endpoint.path.replace('/', '_')}"
                results[endpoint_key] = result

                if progress_callback:
                    await progress_callback(
                        {
                            "endpoint": endpoint.path,
                            "progress": (i + 1) / len(endpoints),
                            "status": result.status.value,
                        }
                    )

            except Exception as e:
                logger.error(f"Failed to convert endpoint {endpoint.path}: {str(e)}")

        # Generate project-level files
        if not dry_run:
            await self._generate_project_files(target_directory, results)

        return results

    def _find_python_files(
        self,
        project_path: str,
        include_patterns: list[str],
        exclude_patterns: list[str],
    ) -> list[str]:
        """Find Python files matching patterns."""
        python_files = []
        project_root = Path(project_path)

        for pattern in include_patterns:
            for file_path in project_root.rglob(pattern):
                if file_path.is_file():
                    # Check exclude patterns
                    excluded = False
                    for exclude_pattern in exclude_patterns:
                        if file_path.match(exclude_pattern):
                            excluded = True
                            break

                    if not excluded:
                        python_files.append(str(file_path))

        return python_files

    async def _analyze_python_file(self, file_path: str) -> list[EndpointInfo]:
        """Analyze a Python file for FastAPI endpoints."""
        endpoints = []

        try:
            async with aiofiles.open(file_path, encoding="utf-8") as f:
                content = await f.read()

            # Parse AST
            tree = ast.parse(content)

            # Find FastAPI app instances
            app_names = self._find_fastapi_apps(tree)

            # Find route decorators
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    endpoint_info = self._extract_endpoint_info(node, content, file_path, app_names)
                    if endpoint_info:
                        endpoints.append(endpoint_info)

        except Exception as e:
            logger.error(f"Failed to analyze file {file_path}: {str(e)}")

        return endpoints

    def _find_fastapi_apps(self, tree: ast.AST) -> set[str]:
        """Find FastAPI app variable names."""
        app_names = set()

        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                # Look for FastAPI() instantiation
                if isinstance(node.value, ast.Call):
                    if hasattr(node.value.func, "id") and node.value.func.id == "FastAPI":
                        for target in node.targets:
                            if isinstance(target, ast.Name):
                                app_names.add(target.id)

                    # Look for APIRouter() instantiation
                    elif hasattr(node.value.func, "id") and node.value.func.id == "APIRouter":
                        for target in node.targets:
                            if isinstance(target, ast.Name):
                                app_names.add(target.id)

        return app_names

    def _extract_endpoint_info(
        self,
        func_node: ast.FunctionDef,
        file_content: str,
        file_path: str,
        app_names: set[str],
    ) -> Optional[EndpointInfo]:
        """Extract endpoint information from function node."""
        # Look for route decorators
        route_info = None

        for decorator in func_node.decorator_list:
            route_info = self._parse_route_decorator(decorator, app_names)
            if route_info:
                break

        if not route_info:
            return None

        # Extract function source code
        source_lines = file_content.split("\n")
        func_start = func_node.lineno - 1
        func_end = func_node.end_lineno if hasattr(func_node, "end_lineno") else len(source_lines)
        source_code = "\n".join(source_lines[func_start:func_end])

        # Extract parameters
        parameters = self._extract_parameters(func_node)

        # Extract dependencies
        dependencies = self._extract_dependencies(func_node, file_content)

        # Check auth requirements
        auth_required = self._check_auth_requirements(func_node, dependencies)

        return EndpointInfo(
            path=route_info["path"],
            method=route_info["method"],
            function_name=func_node.name,
            parameters=parameters,
            dependencies=dependencies,
            middleware=[],  # TODO: Extract middleware
            auth_required=auth_required,
            response_model=route_info.get("response_model"),
            source_code=source_code,
            file_path=file_path,
        )

    def _parse_route_decorator(
        self, decorator: ast.expr, app_names: set[str]
    ) -> Optional[dict[str, Any]]:
        """Parse route decorator to extract method and path."""
        # Handle @app.get(), @app.post(), etc.
        if isinstance(decorator, ast.Call):
            if (
                isinstance(decorator.func, ast.Attribute)
                and isinstance(decorator.func.value, ast.Name)
                and decorator.func.value.id in app_names
            ):
                method = decorator.func.attr.upper()
                path = None
                response_model = None

                # Extract path from first argument
                if decorator.args:
                    if isinstance(decorator.args[0], ast.Str):
                        path = decorator.args[0].s
                    elif isinstance(decorator.args[0], ast.Constant):
                        path = decorator.args[0].value

                # Extract response_model from keywords
                for keyword in decorator.keywords:
                    if keyword.arg == "response_model":
                        if isinstance(keyword.value, ast.Name):
                            response_model = keyword.value.id

                if path:
                    return {
                        "method": method,
                        "path": path,
                        "response_model": response_model,
                    }

        return None

    def _extract_parameters(self, func_node: ast.FunctionDef) -> list[dict[str, Any]]:
        """Extract function parameters and their types."""
        parameters = []

        for arg in func_node.args.args:
            param_info = {
                "name": arg.arg,
                "type": "any",
                "required": True,
                "source": "path",  # Default assumption
            }

            # Extract type annotation
            if arg.annotation:
                param_info["type"] = self._ast_to_string(arg.annotation)

            parameters.append(param_info)

        return parameters

    def _extract_dependencies(self, func_node: ast.FunctionDef, file_content: str) -> list[str]:
        """Extract function dependencies."""
        dependencies = []

        # Look for Depends() in function parameters
        for arg in func_node.args.args:
            if arg.annotation and isinstance(arg.annotation, ast.Call):
                if (
                    isinstance(arg.annotation.func, ast.Name)
                    and arg.annotation.func.id == "Depends"
                ):
                    if arg.annotation.args:
                        dep_name = self._ast_to_string(arg.annotation.args[0])
                        dependencies.append(dep_name)

        return dependencies

    def _check_auth_requirements(self, func_node: ast.FunctionDef, dependencies: list[str]) -> bool:
        """Check if endpoint requires authentication."""
        auth_indicators = [
            "current_user",
            "get_current_user",
            "auth",
            "authenticate",
            "jwt",
            "token",
        ]

        # Check function parameters
        for arg in func_node.args.args:
            if any(indicator in arg.arg.lower() for indicator in auth_indicators):
                return True

        # Check dependencies
        for dep in dependencies:
            if any(indicator in dep.lower() for indicator in auth_indicators):
                return True

        return False

    def _ast_to_string(self, node: ast.expr) -> str:
        """Convert AST node to string representation."""
        try:
            return ast.unparse(node)
        except:
            # Fallback for older Python versions
            if isinstance(node, ast.Name):
                return node.id
            elif isinstance(node, ast.Constant):
                return str(node.value)
            elif isinstance(node, ast.Str):
                return node.s
            else:
                return "any"

    def _check_compatibility(self, endpoint: EndpointInfo) -> dict[str, Any]:
        """Check if endpoint can be converted to Edge Function."""
        issues = []
        suggestions = []
        convertible = True

        # Check for unsupported patterns
        source_lower = endpoint.source_code.lower()
        for pattern in self.unsupported_patterns:
            if pattern in source_lower:
                issues.append(f"Unsupported pattern: {pattern}")
                convertible = False

        # Check for complex dependencies
        if len(endpoint.dependencies) > 5:
            issues.append("Too many dependencies - consider simplification")
            suggestions.append("Break down into smaller functions")

        # Check for database operations
        if any(keyword in source_lower for keyword in ["session", "db.", "query", "commit"]):
            suggestions.append("Consider using Supabase client for database operations")

        return {
            "convertible": convertible,
            "issues": issues,
            "suggestions": suggestions,
        }

    async def _generate_edge_function(self, endpoint: EndpointInfo) -> str:
        """Generate TypeScript/Deno Edge Function code."""
        # Convert function signature
        ts_params = self._convert_parameters_to_typescript(endpoint.parameters)

        # Generate request handler
        handler_code = f"""// Edge Function: {endpoint.function_name}
// Converted from: {endpoint.method} {endpoint.path}

import {{ serve }} from 'https://deno.land/std@0.168.0/http/server.ts'
import {{ createClient }} from 'https://esm.sh/@supabase/supabase-js@2'

interface RequestBody {{
{ts_params}
}}

interface ResponseData {{
  success: boolean;
  data?: any;
  error?: string;
}}

serve(async (req: Request): Promise<Response> => {{
  // CORS headers
  const corsHeaders = {{
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
  }}

  // Handle CORS preflight
  if (req.method === 'OPTIONS') {{
    return new Response('ok', {{ headers: corsHeaders }})
  }}

  try {{
    // Initialize Supabase client
    const supabaseUrl = Deno.env.get('SUPABASE_URL')!
    const supabaseKey = Deno.env.get('SUPABASE_ANON_KEY')!
    const supabase = createClient(supabaseUrl, supabaseKey)

    // Get authorization header
    const authHeader = req.headers.get('Authorization')
    if (authHeader) {{
      const {{ data: {{ user }}, error }} = await supabase.auth.getUser(
        authHeader.replace('Bearer ', '')
      )
      if (error || !user) {{
        return new Response(
          JSON.stringify({{ success: false, error: 'Unauthorized' }}),
          {{
            status: 401,
            headers: {{ ...corsHeaders, 'Content-Type': 'application/json' }}
          }}
        )
      }}
    }}

    // Parse request body
    const body: RequestBody = await req.json()

    // TODO: Implement your business logic here
    // This is where you would convert the original Python logic

    const result = {{
      success: true,
      data: {{ message: 'Function converted successfully' }}
    }}

    return new Response(
      JSON.stringify(result),
      {{
        headers: {{ ...corsHeaders, 'Content-Type': 'application/json' }}
      }}
    )

  }} catch (error) {{
    return new Response(
      JSON.stringify({{
        success: false,
        error: error.message
      }}),
      {{
        status: 500,
        headers: {{ ...corsHeaders, 'Content-Type': 'application/json' }}
      }}
    )
  }}
}})

// Original Python code (for reference):
/*
{endpoint.source_code}
*/
"""

        return handler_code

    def _convert_parameters_to_typescript(self, parameters: list[dict[str, Any]]) -> str:
        """Convert Python parameters to TypeScript interface."""
        ts_fields = []

        for param in parameters:
            param_name = param["name"]
            param_type = param.get("type", "any")

            # Convert Python type to TypeScript
            ts_type = self.python_to_ts_types.get(param_type, "any")

            # Handle optional parameters
            optional_suffix = "?" if not param.get("required", True) else ""

            ts_fields.append(f"  {param_name}{optional_suffix}: {ts_type};")

        return "\n".join(ts_fields)

    async def _generate_deployment_script(self, endpoint: EndpointInfo) -> str:
        """Generate deployment script for the Edge Function."""
        function_name = f"{endpoint.method.lower()}_{endpoint.function_name}"

        script = f"""#!/bin/bash

# Deployment script for Edge Function: {function_name}
# Generated from: {endpoint.method} {endpoint.path}

set -e

echo "Deploying Edge Function: {function_name}"

# Check if Supabase CLI is installed
if ! command -v supabase &> /dev/null; then
    echo "Supabase CLI is not installed. Please install it first:"
    echo "npm install -g supabase"
    exit 1
fi

# Check if logged in
if ! supabase projects list &> /dev/null; then
    echo "Please log in to Supabase CLI first:"
    echo "supabase login"
    exit 1
fi

# Deploy the function
echo "Deploying function..."
supabase functions deploy {function_name} --project-ref ${{SUPABASE_PROJECT_REF}}

# Set environment variables if needed
if [ ! -z "${{DATABASE_URL}}" ]; then
    supabase secrets set DATABASE_URL="${{DATABASE_URL}}" --project-ref ${{SUPABASE_PROJECT_REF}}
fi

echo "Deployment completed successfully!"
echo "Function URL: https://${{SUPABASE_PROJECT_REF}}.functions.supabase.co/{function_name}"
"""

        return script

    def _extract_environment_variables(self, endpoint: EndpointInfo) -> list[str]:
        """Extract environment variables from endpoint code."""
        env_vars = []

        # Look for common environment variable patterns
        env_patterns = [
            r'os\.environ\.get\([\'"]([^\'\"]+)[\'"]',
            r'os\.getenv\([\'"]([^\'\"]+)[\'"]',
            r"settings\.([A-Z_]+)",
            r"config\.([A-Z_]+)",
        ]

        for pattern in env_patterns:
            matches = re.findall(pattern, endpoint.source_code)
            env_vars.extend(matches)

        # Remove duplicates and sort
        return sorted(list(set(env_vars)))

    async def _write_edge_function_files(
        self,
        endpoint: EndpointInfo,
        target_directory: str,
        edge_function_code: str,
        deployment_script: str,
    ):
        """Write Edge Function files to disk."""
        function_name = f"{endpoint.method.lower()}_{endpoint.function_name}"

        # Create function directory
        func_dir = Path(target_directory) / "functions" / function_name
        func_dir.mkdir(parents=True, exist_ok=True)

        # Write Edge Function code
        async with aiofiles.open(func_dir / "index.ts", "w") as f:
            await f.write(edge_function_code)

        # Write deployment script
        deploy_script_path = func_dir / "deploy.sh"
        async with aiofiles.open(deploy_script_path, "w") as f:
            await f.write(deployment_script)

        # Make deployment script executable
        os.chmod(deploy_script_path, 0o755)

        logger.info(f"Generated Edge Function files in {func_dir}")

    async def _generate_project_files(
        self, target_directory: str, results: dict[str, ConversionResult]
    ):
        """Generate project-level files."""
        target_path = Path(target_directory)
        target_path.mkdir(parents=True, exist_ok=True)

        # Generate summary report
        summary = {
            "total_endpoints": len(results),
            "successful_conversions": len(
                [r for r in results.values() if r.status == ConversionStatus.SUCCESS]
            ),
            "failed_conversions": len(
                [r for r in results.values() if r.status == ConversionStatus.FAILED]
            ),
            "skipped_conversions": len(
                [r for r in results.values() if r.status == ConversionStatus.SKIPPED]
            ),
            "results": {
                k: {
                    "status": v.status.value,
                    "issues": v.issues,
                    "suggestions": v.suggestions,
                }
                for k, v in results.items()
            },
        }

        async with aiofiles.open(target_path / "conversion_summary.json", "w") as f:
            await f.write(json.dumps(summary, indent=2))

        # Generate deployment script for all functions
        all_functions = [
            f"{r.endpoint.method.lower()}_{r.endpoint.function_name}"
            for r in results.values()
            if r.status == ConversionStatus.SUCCESS
        ]

        deploy_all_script = f"""#!/bin/bash

# Deploy all converted Edge Functions
set -e

echo "Deploying all Edge Functions..."

{chr(10).join([f'echo "Deploying {func}..."' for func in all_functions])}
{chr(10).join([f'supabase functions deploy {func} --project-ref ${{SUPABASE_PROJECT_REF}}' for func in all_functions])}

echo "All functions deployed successfully!"
"""

        async with aiofiles.open(target_path / "deploy_all.sh", "w") as f:
            await f.write(deploy_all_script)

        os.chmod(target_path / "deploy_all.sh", 0o755)

        logger.info(f"Generated project files in {target_directory}")

    def generate_migration_guide(self, results: dict[str, ConversionResult]) -> str:
        """Generate migration guide documentation."""
        successful = [r for r in results.values() if r.status == ConversionStatus.SUCCESS]
        failed = [r for r in results.values() if r.status == ConversionStatus.FAILED]
        skipped = [r for r in results.values() if r.status == ConversionStatus.SKIPPED]

        guide = f"""# FastAPI to Supabase Edge Functions Migration Guide

## Conversion Summary

- **Total Endpoints**: {len(results)}
- **Successfully Converted**: {len(successful)}
- **Failed Conversions**: {len(failed)}
- **Skipped**: {len(skipped)}

## Successfully Converted Functions

"""

        for result in successful:
            guide += f"### {result.endpoint.method} {result.endpoint.path}\n"
            guide += f"- **Function**: `{result.endpoint.function_name}`\n"
            guide += f"- **Auth Required**: {result.endpoint.auth_required}\n"
            guide += f"- **Environment Variables**: {', '.join(result.environment_variables)}\n\n"

        if failed:
            guide += "## Failed Conversions\n\n"
            for result in failed:
                guide += f"### {result.endpoint.method} {result.endpoint.path}\n"
                guide += f"**Issues:**\n"
                for issue in result.issues:
                    guide += f"- {issue}\n"
                guide += "\n"

        if skipped:
            guide += "## Skipped Conversions\n\n"
            for result in skipped:
                guide += f"### {result.endpoint.method} {result.endpoint.path}\n"
                guide += f"**Reasons:**\n"
                for issue in result.issues:
                    guide += f"- {issue}\n"
                if result.suggestions:
                    guide += f"**Suggestions:**\n"
                    for suggestion in result.suggestions:
                        guide += f"- {suggestion}\n"
                guide += "\n"

        guide += """## Next Steps

1. Review the generated Edge Functions in the `functions/` directory
2. Update environment variables in your Supabase project
3. Test each function individually
4. Update your frontend to call the new Edge Function endpoints
5. Gradually migrate traffic from FastAPI to Edge Functions

## Deployment

Run the generated deployment scripts:

```bash
# Deploy individual functions
cd functions/[function-name]
./deploy.sh

# Or deploy all functions at once
./deploy_all.sh
```

## Environment Variables

Make sure to set the following environment variables in your Supabase project:

- `SUPABASE_URL`
- `SUPABASE_ANON_KEY`
- `SUPABASE_SERVICE_ROLE_KEY`
- Any custom environment variables found in your FastAPI code
"""

        return guide
