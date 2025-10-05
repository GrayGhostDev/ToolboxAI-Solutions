"""
Swagger UI Configuration for ToolboxAI API

This module configures and serves Swagger UI for interactive API documentation.
Uses the generated OpenAPI specification for comprehensive API exploration.
"""

import json
from pathlib import Path
from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
from fastapi.responses import HTMLResponse

def setup_swagger(app: FastAPI) -> None:
    """
    Configure Swagger UI with custom settings and branding

    Args:
        app: FastAPI application instance
    """

    # Custom OpenAPI schema generator
    def custom_openapi():
        if app.openapi_schema:
            return app.openapi_schema

        # Load our generated OpenAPI spec as base
        openapi_file = Path(__file__).parent.parent.parent.parent / "openapi.json"
        if openapi_file.exists():
            with open(openapi_file, 'r') as f:
                base_schema = json.load(f)
        else:
            # Fallback to auto-generated schema
            base_schema = get_openapi(
                title="ToolboxAI Educational Platform API",
                version="1.0.0",
                description="""
                ## 🚀 AI-Powered Educational Platform with Roblox Integration

                ### Features
                - 🤖 AI-powered content generation
                - 🎮 Roblox game integration
                - 👥 Multi-role support (Admin, Teacher, Student, Parent)
                - 📊 Real-time analytics
                - 🏆 Gamification system
                - 🔒 Enterprise-grade security

                ### Authentication
                All endpoints require JWT authentication unless marked as public.
                Use the `/api/v1/auth/login` endpoint to obtain a token.

                ### Rate Limiting
                - Public endpoints: 100 requests/minute
                - Authenticated: 1000 requests/minute

                ### Support
                For issues or questions, contact support@toolboxai.com
                """,
                routes=app.routes,
            )

        # Enhance with additional metadata
        base_schema["servers"] = [
            {"url": "http://localhost:8009", "description": "Development server"},
            {"url": "http://localhost:5179/api", "description": "Through dashboard proxy"},
            {"url": "https://api.toolboxai.com", "description": "Production server"},
        ]

        base_schema["components"]["securitySchemes"] = {
            "BearerAuth": {
                "type": "http",
                "scheme": "bearer",
                "bearerFormat": "JWT",
                "description": "Enter your JWT token obtained from /api/v1/auth/login"
            },
            "ApiKeyAuth": {
                "type": "apiKey",
                "in": "header",
                "name": "X-API-Key",
                "description": "API key for service-to-service authentication"
            }
        }

        # Tag descriptions for better organization
        base_schema["tags"] = [
            {"name": "Authentication", "description": "User authentication and authorization"},
            {"name": "Users", "description": "User management operations"},
            {"name": "Content Generation", "description": "AI-powered content creation"},
            {"name": "Classes", "description": "Class management for educators"},
            {"name": "Lessons", "description": "Lesson creation and management"},
            {"name": "Assessments", "description": "Assessment and quiz management"},
            {"name": "Roblox Integration", "description": "Roblox game synchronization"},
            {"name": "Real-time", "description": "Pusher and WebSocket endpoints"},
            {"name": "Analytics", "description": "Analytics and reporting"},
            {"name": "Gamification", "description": "Badges, XP, and leaderboards"},
            {"name": "System", "description": "Health checks and monitoring"},
        ]

        app.openapi_schema = base_schema
        return app.openapi_schema

    app.openapi = custom_openapi

    # Custom Swagger UI configuration
    @app.get("/docs", include_in_schema=False)
    async def custom_swagger_ui_html():
        return HTMLResponse(content=f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>ToolboxAI API Documentation</title>
            <link rel="stylesheet" type="text/css" href="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui.css">
            <style>
                body {{
                    margin: 0;
                    padding: 0;
                }}
                .swagger-ui .topbar {{
                    display: none;
                }}
                .swagger-ui .info {{
                    margin: 20px 0;
                }}
                .swagger-ui .info .title {{
                    font-size: 36px;
                    color: #3b82f6;
                }}
                .swagger-ui .scheme-container {{
                    background: #f3f4f6;
                    padding: 15px;
                    border-radius: 8px;
                    margin: 20px 0;
                }}
                /* Custom color scheme */
                .swagger-ui .btn.authorize {{
                    background-color: #3b82f6;
                    color: white;
                }}
                .swagger-ui .btn.authorize:hover {{
                    background-color: #2563eb;
                }}
                .swagger-ui .opblock.opblock-post .tab-header h4 span::after {{
                    background: #10b981;
                }}
                .swagger-ui .opblock.opblock-get .tab-header h4 span::after {{
                    background: #3b82f6;
                }}
                .swagger-ui .opblock.opblock-put .tab-header h4 span::after {{
                    background: #f59e0b;
                }}
                .swagger-ui .opblock.opblock-delete .tab-header h4 span::after {{
                    background: #ef4444;
                }}
            </style>
        </head>
        <body>
            <div id="swagger-ui"></div>
            <script src="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js"></script>
            <script>
            window.onload = function() {{
                SwaggerUIBundle({{
                    url: "/openapi.json",
                    dom_id: '#swagger-ui',
                    deepLinking: true,
                    persistAuthorization: true,
                    displayRequestDuration: true,
                    filter: true,
                    layout: "BaseLayout",
                    presets: [
                        SwaggerUIBundle.presets.apis,
                        SwaggerUIBundle.SwaggerUIStandalonePreset
                    ],
                    plugins: [
                        SwaggerUIBundle.plugins.DownloadUrl
                    ],
                    onComplete: function() {{
                        console.log("Swagger UI loaded successfully");
                    }}
                }});
            }};
            </script>
        </body>
        </html>
        """)

    # Redoc alternative documentation
    @app.get("/redoc", include_in_schema=False)
    async def redoc_html():
        return HTMLResponse(content=f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>ToolboxAI API Reference</title>
            <meta charset="utf-8"/>
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>
                body {{
                    margin: 0;
                    padding: 0;
                }}
            </style>
        </head>
        <body>
            <redoc spec-url="/openapi.json"></redoc>
            <script src="https://cdn.jsdelivr.net/npm/redoc@latest/bundles/redoc.standalone.js"></script>
        </body>
        </html>
        """)

    # Health check for API documentation
    @app.get("/docs/health", tags=["System"])
    async def docs_health():
        """Check if API documentation is accessible"""
        return {
            "status": "healthy",
            "documentation": {
                "swagger": "/docs",
                "redoc": "/redoc",
                "openapi": "/openapi.json"
            }
        }