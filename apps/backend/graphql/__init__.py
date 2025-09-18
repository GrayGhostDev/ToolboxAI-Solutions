"""
GraphQL module for ToolBoxAI Educational Platform
"""

from .app import graphql_app, setup_graphql
from .schema import schema

__all__ = ["graphql_app", "setup_graphql", "schema"]