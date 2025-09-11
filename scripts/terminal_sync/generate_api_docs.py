#!/usr/bin/env python3
"""
Generate comprehensive API documentation from FastAPI application
Extracts all endpoints and generates OpenAPI 3.0 specification
"""

import json
import yaml
import sys
import os
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "ToolboxAI-Roblox-Environment"))

def generate_openapi_spec():
    """Generate complete OpenAPI specification from FastAPI app"""
    try:
        # Import FastAPI app
        from server.main import app
        
        # Get OpenAPI schema from FastAPI
        openapi_schema = app.openapi()
        
        # Enhance the schema with additional metadata
        openapi_schema["info"] = {
            "title": "ToolBoxAI Educational Platform API",
            "version": "2.0.0",
            "description": "Comprehensive API for educational content generation, gamification, and learning management",
            "contact": {
                "name": "ToolBoxAI Solutions",
                "email": "support@toolboxai.com",
                "url": "https://toolboxai.com"
            },
            "license": {
                "name": "Proprietary",
                "url": "https://toolboxai.com/license"
            }
        }
        
        # Add servers
        openapi_schema["servers"] = [
            {
                "url": "http://localhost:8008",
                "description": "FastAPI Development Server"
            },
            {
                "url": "http://localhost:5001", 
                "description": "Flask Bridge Server"
            },
            {
                "url": "http://localhost:8001",
                "description": "Dashboard Backend Server"
            },
            {
                "url": "https://api.toolboxai.com",
                "description": "Production API Server"
            }
        ]
        
        # Add security schemes
        if "components" not in openapi_schema:
            openapi_schema["components"] = {}
            
        openapi_schema["components"]["securitySchemes"] = {
            "bearerAuth": {
                "type": "http",
                "scheme": "bearer",
                "bearerFormat": "JWT",
                "description": "JWT authentication token"
            },
            "apiKey": {
                "type": "apiKey",
                "in": "header",
                "name": "X-API-Key",
                "description": "API key authentication"
            }
        }
        
        # Add tags for better organization
        openapi_schema["tags"] = [
            {"name": "System", "description": "System health and monitoring endpoints"},
            {"name": "Authentication", "description": "User authentication and authorization"},
            {"name": "Content", "description": "Educational content generation and management"},
            {"name": "Users", "description": "User profile and management"},
            {"name": "Classes", "description": "Class and classroom management"},
            {"name": "Lessons", "description": "Lesson creation and tracking"},
            {"name": "Assessments", "description": "Quiz and assessment management"},
            {"name": "Analytics", "description": "Learning analytics and insights"},
            {"name": "Reports", "description": "Report generation and management"},
            {"name": "Messages", "description": "Messaging and notifications"},
            {"name": "Dashboard", "description": "Dashboard data and metrics"},
            {"name": "Gamification", "description": "Gamification features and leaderboards"},
            {"name": "Admin", "description": "Administrative functions"},
            {"name": "LMS", "description": "Learning Management System integration"},
            {"name": "Schools", "description": "School management"},
            {"name": "Compliance", "description": "Compliance and regulatory features"},
            {"name": "Agents", "description": "AI agent system"},
            {"name": "WebSocket", "description": "Real-time WebSocket connections"}
        ]
        
        # Count endpoints
        endpoint_count = len(openapi_schema.get("paths", {}))
        
        # Add metadata
        openapi_schema["x-metadata"] = {
            "generated_at": datetime.now().isoformat(),
            "total_endpoints": endpoint_count,
            "api_versions": ["v1", "v2"],
            "documentation_status": "complete"
        }
        
        return openapi_schema
        
    except Exception as e:
        print(f"Error generating OpenAPI spec: {e}")
        return None


def save_openapi_spec(spec: Dict[str, Any], output_dir: Path):
    """Save OpenAPI specification in multiple formats"""
    if not spec:
        return False
        
    # Create output directory if it doesn't exist
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save as YAML (primary format)
    yaml_path = output_dir / "openapi-spec.yaml"
    with open(yaml_path, 'w') as f:
        yaml.dump(spec, f, default_flow_style=False, sort_keys=False)
    print(f"✅ Saved OpenAPI spec to {yaml_path}")
    
    # Save as JSON (alternative format)
    json_path = output_dir / "openapi-spec.json"
    with open(json_path, 'w') as f:
        json.dump(spec, f, indent=2)
    print(f"✅ Saved OpenAPI spec to {json_path}")
    
    # Generate summary
    summary_path = output_dir / "api-summary.md"
    generate_api_summary(spec, summary_path)
    
    return True


def generate_api_summary(spec: Dict[str, Any], output_path: Path):
    """Generate markdown summary of API endpoints"""
    summary = ["# API Endpoint Summary\n"]
    summary.append(f"Generated: {datetime.now().isoformat()}\n")
    summary.append(f"Total Endpoints: {spec.get('x-metadata', {}).get('total_endpoints', 0)}\n\n")
    
    # Group endpoints by tag
    endpoints_by_tag = {}
    for path, methods in spec.get("paths", {}).items():
        for method, details in methods.items():
            if method in ["get", "post", "put", "delete", "patch"]:
                tags = details.get("tags", ["Uncategorized"])
                for tag in tags:
                    if tag not in endpoints_by_tag:
                        endpoints_by_tag[tag] = []
                    endpoints_by_tag[tag].append({
                        "method": method.upper(),
                        "path": path,
                        "summary": details.get("summary", ""),
                        "description": details.get("description", "")
                    })
    
    # Write endpoints by category
    for tag in sorted(endpoints_by_tag.keys()):
        summary.append(f"## {tag}\n\n")
        for endpoint in sorted(endpoints_by_tag[tag], key=lambda x: x["path"]):
            summary.append(f"- **{endpoint['method']} {endpoint['path']}**")
            if endpoint['summary']:
                summary.append(f" - {endpoint['summary']}")
            summary.append("\n")
        summary.append("\n")
    
    # Write summary file
    with open(output_path, 'w') as f:
        f.write(''.join(summary))
    print(f"✅ Saved API summary to {output_path}")


def main():
    """Main execution"""
    print("🚀 Starting API documentation generation...")
    
    # Set output directory
    output_dir = project_root / "Documentation" / "03-api"
    
    # Generate OpenAPI specification
    spec = generate_openapi_spec()
    
    if spec:
        # Save specifications
        if save_openapi_spec(spec, output_dir):
            print(f"\n✨ Successfully generated API documentation!")
            print(f"📊 Total endpoints documented: {spec.get('x-metadata', {}).get('total_endpoints', 0)}")
        else:
            print("❌ Failed to save API documentation")
            sys.exit(1)
    else:
        print("❌ Failed to generate OpenAPI specification")
        sys.exit(1)


if __name__ == "__main__":
    main()