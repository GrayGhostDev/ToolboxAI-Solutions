"""
GraphQL application setup using Ariadne
"""

import logging
import os
from pathlib import Path
from typing import Any, Dict, Optional

from ariadne import (
    load_schema_from_path,
    make_executable_schema,
    snake_case_fallback_resolvers,
    upload_scalar,
)
from ariadne.asgi import GraphQL
from ariadne.explorer import ExplorerGraphiQL
from fastapi import FastAPI, Depends, Request
from starlette.middleware.cors import CORSMiddleware

from apps.backend.core.config import settings
from .resolvers import query, mutation, subscription
from .directives import AuthDirective, RateLimitDirective
from .context import get_context
from .scalars import datetime_scalar, uuid_scalar, json_scalar, email_scalar, url_scalar

logger = logging.getLogger(__name__)

# Path to GraphQL schema files
SCHEMA_PATH = Path(__file__).parent.parent.parent.parent / "schema"


def load_graphql_schema():
    """Load GraphQL schema from .graphql files"""
    try:
        # Load all .graphql files from schema directory
        type_defs = load_schema_from_path(str(SCHEMA_PATH))
        logger.info(f"GraphQL schema loaded from {SCHEMA_PATH}")
        return type_defs
    except Exception as e:
        logger.error(f"Failed to load GraphQL schema: {e}")
        raise


def create_graphql_schema():
    """Create executable GraphQL schema with resolvers and directives"""

    # Load schema definitions
    type_defs = load_graphql_schema()

    # Create executable schema with all resolvers and custom scalars
    schema = make_executable_schema(
        type_defs,
        # Query, Mutation, and Subscription resolvers
        query,
        mutation,
        subscription,
        # Custom scalar resolvers
        datetime_scalar,
        uuid_scalar,
        json_scalar,
        email_scalar,
        url_scalar,
        upload_scalar,
        # Default resolver for snake_case to camelCase conversion
        snake_case_fallback_resolvers,
        # Custom directives
        directives={
            "auth": AuthDirective,
            "rateLimit": RateLimitDirective,
        },
    )

    logger.info("GraphQL schema created successfully")
    return schema


def error_formatter(error: Exception, debug: bool = False) -> Dict[str, Any]:
    """Format GraphQL errors for response"""
    formatted = {
        "message": str(error),
        "extensions": {"code": getattr(error, "code", "INTERNAL_ERROR")},
    }

    if debug:
        import traceback

        formatted["extensions"]["traceback"] = traceback.format_exc()

    return formatted


# Create the GraphQL schema
schema = create_graphql_schema()

# Create GraphQL ASGI application
graphql_app = GraphQL(
    schema,
    debug=settings.DEBUG,
    # Use GraphQL Playground in development
    explorer=ExplorerGraphiQL() if settings.DEBUG else None,
    context_value=get_context,
    logger=logger,
    error_formatter=lambda err, debug: error_formatter(err, settings.DEBUG),
    # Enable introspection in development only
    introspection=settings.DEBUG,
    # Validation rules can be added here
    validation_rules=None,
)


def setup_graphql(app: FastAPI):
    """
    Mount GraphQL endpoint on FastAPI application

    Args:
        app: FastAPI application instance
    """

    # Mount GraphQL app at /graphql endpoint
    app.mount("/graphql", graphql_app)

    # Add GraphQL-specific CORS configuration if needed
    if settings.DEBUG:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["http://localhost:5179", "http://localhost:5173"],  # Frontend URLs
            allow_methods=["POST", "OPTIONS"],
            allow_headers=["*"],
            allow_credentials=True,
        )

    logger.info("GraphQL endpoint mounted at /graphql")

    # Log GraphQL Playground availability
    if settings.DEBUG:
        logger.info("GraphQL Playground available at http://localhost:8009/graphql")
