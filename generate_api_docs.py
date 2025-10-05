#!/usr/bin/env python3
"""
Generate API Documentation for ToolboxAI

This script extracts API endpoint information from the codebase
and generates comprehensive documentation.
"""

import os
import re
import json
from pathlib import Path
from typing import Dict, List, Set, Tuple
from datetime import datetime

def find_api_endpoints(directory: Path) -> List[Dict]:
    """Find all API endpoints in Python files"""
    endpoints = []

    # Patterns to match FastAPI route decorators
    patterns = [
        r'@app\.(get|post|put|delete|patch)\s*\(\s*["\']([^"\']+)["\']',
        r'@router\.(get|post|put|delete|patch)\s*\(\s*["\']([^"\']+)["\']',
    ]

    # Walk through all Python files
    for py_file in directory.rglob("*.py"):
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                content = f.read()

            for pattern in patterns:
                matches = re.findall(pattern, content)
                for method, path in matches:
                    # Extract function name and docstring
                    func_info = extract_function_info(content, method, path)

                    endpoints.append({
                        'method': method.upper(),
                        'path': path,
                        'file': str(py_file.relative_to(directory)),
                        'function': func_info.get('name', 'unknown'),
                        'description': func_info.get('docstring', ''),
                    })
        except Exception as e:
            print(f"Error processing {py_file}: {e}")

    return endpoints

def extract_function_info(content: str, method: str, path: str) -> Dict:
    """Extract function name and docstring for an endpoint"""
    info = {}

    # Find the function definition after the decorator
    escaped_path = re.escape(path)
    pattern = rf'@\w+\.{method}\s*\(\s*["\']' + escaped_path + r'["\'][^\)]*\)\s*(?:async\s+)?def\s+(\w+)\s*\([^)]*\):\s*(?:"""([^"]*)""")?'

    match = re.search(pattern, content, re.MULTILINE | re.DOTALL)
    if match:
        info['name'] = match.group(1)
        if match.group(2):
            info['docstring'] = match.group(2).strip()

    return info

def categorize_endpoints(endpoints: List[Dict]) -> Dict[str, List[Dict]]:
    """Categorize endpoints by their path prefix"""
    categories = {}

    for endpoint in endpoints:
        path = endpoint['path']

        # Determine category based on path
        if '/auth' in path or '/login' in path or '/register' in path:
            category = 'Authentication'
        elif '/users' in path or '/profile' in path:
            category = 'Users'
        elif '/classes' in path:
            category = 'Classes'
        elif '/lessons' in path:
            category = 'Lessons'
        elif '/assessments' in path:
            category = 'Assessments'
        elif '/roblox' in path:
            category = 'Roblox Integration'
        elif '/pusher' in path or '/realtime' in path:
            category = 'Real-time Communication'
        elif '/content' in path:
            category = 'Content Generation'
        elif '/agents' in path:
            category = 'AI Agents'
        elif '/analytics' in path or '/reports' in path:
            category = 'Analytics & Reporting'
        elif '/messages' in path:
            category = 'Messages'
        elif '/gamification' in path or '/badges' in path or '/leaderboard' in path:
            category = 'Gamification'
        elif '/health' in path or '/metrics' in path:
            category = 'System Health'
        elif '/compliance' in path or '/privacy' in path:
            category = 'Compliance & Privacy'
        elif '/payment' in path or '/stripe' in path:
            category = 'Payments'
        else:
            category = 'Other'

        if category not in categories:
            categories[category] = []
        categories[category].append(endpoint)

    return categories

def generate_markdown_docs(categories: Dict[str, List[Dict]]) -> str:
    """Generate Markdown documentation from categorized endpoints"""
    doc = f"""# ToolboxAI API Documentation

**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Version**: 1.0.0
**Base URL**: `http://localhost:8009`

## Overview

This document provides a comprehensive reference for all API endpoints in the ToolboxAI Educational Platform.

## Authentication

All authenticated endpoints require a JWT token in the Authorization header:
```
Authorization: Bearer <token>
```

## Rate Limiting

API endpoints are rate-limited to prevent abuse:
- Default: 100 requests per minute per IP
- Authenticated: 1000 requests per minute per user

## Response Format

All API responses follow this format:
```json
{{
    "status": "success|error",
    "data": {{}},
    "message": "...",
    "metadata": {{}}
}}
```

## Endpoints by Category

"""

    # Generate table of contents
    doc += "### Table of Contents\n\n"
    for category in sorted(categories.keys()):
        count = len(categories[category])
        doc += f"- [{category}](#{category.lower().replace(' ', '-').replace('&', '')}) ({count} endpoints)\n"

    doc += "\n---\n\n"

    # Generate detailed endpoint documentation
    for category in sorted(categories.keys()):
        endpoints = categories[category]
        doc += f"## {category}\n\n"
        doc += f"**Total Endpoints**: {len(endpoints)}\n\n"

        # Sort endpoints by path
        endpoints.sort(key=lambda x: (x['path'], x['method']))

        for endpoint in endpoints:
            doc += f"### `{endpoint['method']}` {endpoint['path']}\n\n"

            if endpoint['description']:
                doc += f"{endpoint['description']}\n\n"

            doc += f"**Function**: `{endpoint['function']}`\n"
            doc += f"**File**: `{endpoint['file']}`\n\n"

            # Add example request/response (template)
            doc += "#### Request\n\n"
            doc += "```http\n"
            doc += f"{endpoint['method']} {endpoint['path']}\n"
            doc += "Authorization: Bearer <token>\n"

            if endpoint['method'] in ['POST', 'PUT', 'PATCH']:
                doc += "Content-Type: application/json\n\n"
                doc += "{\n  // Request body\n}\n"

            doc += "```\n\n"

            doc += "#### Response\n\n"
            doc += "```json\n"
            doc += "{\n"
            doc += '  "status": "success",\n'
            doc += '  "data": {},\n'
            doc += '  "message": "Operation successful"\n'
            doc += "}\n"
            doc += "```\n\n"

            doc += "---\n\n"

    # Add statistics
    total_endpoints = sum(len(endpoints) for endpoints in categories.values())
    doc += f"\n## Statistics\n\n"
    doc += f"- **Total Endpoints**: {total_endpoints}\n"
    doc += f"- **Categories**: {len(categories)}\n"

    method_counts = {}
    for endpoints in categories.values():
        for endpoint in endpoints:
            method = endpoint['method']
            method_counts[method] = method_counts.get(method, 0) + 1

    doc += f"- **Methods**:\n"
    for method in sorted(method_counts.keys()):
        doc += f"  - {method}: {method_counts[method]}\n"

    return doc

def generate_openapi_spec(categories: Dict[str, List[Dict]]) -> Dict:
    """Generate OpenAPI 3.0 specification"""
    spec = {
        "openapi": "3.0.0",
        "info": {
            "title": "ToolboxAI Educational Platform API",
            "version": "1.0.0",
            "description": "AI-Powered Educational Platform with Roblox Integration",
            "contact": {
                "name": "ToolboxAI Support",
                "email": "support@toolboxai.com"
            }
        },
        "servers": [
            {
                "url": "http://localhost:8009",
                "description": "Development server"
            },
            {
                "url": "https://api.toolboxai.com",
                "description": "Production server"
            }
        ],
        "components": {
            "securitySchemes": {
                "bearerAuth": {
                    "type": "http",
                    "scheme": "bearer",
                    "bearerFormat": "JWT"
                }
            }
        },
        "security": [
            {
                "bearerAuth": []
            }
        ],
        "paths": {}
    }

    # Generate paths from endpoints
    for category, endpoints in categories.items():
        for endpoint in endpoints:
            path = endpoint['path']
            method = endpoint['method'].lower()

            if path not in spec['paths']:
                spec['paths'][path] = {}

            operation = {
                "tags": [category],
                "summary": endpoint['function'],
                "description": endpoint['description'] or f"Endpoint: {endpoint['function']}",
                "responses": {
                    "200": {
                        "description": "Successful operation",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "status": {"type": "string"},
                                        "data": {"type": "object"},
                                        "message": {"type": "string"}
                                    }
                                }
                            }
                        }
                    },
                    "401": {
                        "description": "Unauthorized"
                    },
                    "500": {
                        "description": "Internal server error"
                    }
                }
            }

            # Add request body for POST/PUT/PATCH
            if method in ['post', 'put', 'patch']:
                operation['requestBody'] = {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object"
                            }
                        }
                    }
                }

            spec['paths'][path][method] = operation

    return spec

def main():
    """Main execution"""
    print("🔍 Scanning for API endpoints...")

    # Get project root
    project_root = Path(__file__).parent
    backend_dir = project_root / "apps" / "backend"

    # Find all endpoints
    endpoints = find_api_endpoints(backend_dir)
    print(f"✅ Found {len(endpoints)} endpoints")

    # Categorize endpoints
    categories = categorize_endpoints(endpoints)
    print(f"📊 Organized into {len(categories)} categories")

    # Generate Markdown documentation
    print("📝 Generating Markdown documentation...")
    markdown_doc = generate_markdown_docs(categories)

    # Save Markdown documentation
    docs_dir = project_root / "docs" / "api"
    docs_dir.mkdir(parents=True, exist_ok=True)

    with open(docs_dir / "API_REFERENCE.md", "w") as f:
        f.write(markdown_doc)
    print(f"✅ Saved to {docs_dir / 'API_REFERENCE.md'}")

    # Generate OpenAPI specification
    print("🔧 Generating OpenAPI specification...")
    openapi_spec = generate_openapi_spec(categories)

    # Save OpenAPI JSON
    with open(project_root / "openapi.json", "w") as f:
        json.dump(openapi_spec, f, indent=2)
    print(f"✅ Saved to {project_root / 'openapi.json'}")

    # Save OpenAPI YAML
    try:
        import yaml
        with open(project_root / "openapi.yaml", "w") as f:
            yaml.dump(openapi_spec, f, default_flow_style=False)
        print(f"✅ Saved to {project_root / 'openapi.yaml'}")
    except ImportError:
        print("⚠️ PyYAML not installed, skipping YAML generation")

    # Print summary
    print("\n📊 API Documentation Summary:")
    print(f"  - Total Endpoints: {len(endpoints)}")
    print(f"  - Categories: {len(categories)}")

    for category in sorted(categories.keys()):
        print(f"  - {category}: {len(categories[category])} endpoints")

if __name__ == "__main__":
    main()