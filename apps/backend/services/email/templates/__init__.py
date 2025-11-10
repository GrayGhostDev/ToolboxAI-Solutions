"""
Email Template Module

Jinja2-based email template engine with custom filters and template management.

Features:
- Template rendering with Jinja2
- Custom template filters
- Template caching
- Dynamic template loading
"""

from .engine import EmailTemplateEngine

__all__ = [
    "EmailTemplateEngine",
]
