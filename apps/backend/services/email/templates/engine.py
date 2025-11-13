"""
Email Template Engine
Provides template rendering with Jinja2, custom filters, and template management
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from jinja2 import (
    Environment,
    FileSystemLoader,
    Template,
    TemplateError,
    TemplateNotFound,
    select_autoescape,
)
from markdown import markdown

from apps.backend.config import settings

logger = logging.getLogger(__name__)


class EmailTemplateEngine:
    """
    Advanced email template engine with Jinja2

    Features:
    - Template inheritance and composition
    - Custom filters for email formatting
    - Template caching for performance
    - Markdown support for content
    - Multi-language support
    - Template validation
    """

    def __init__(self, template_dir: str | None = None):
        """
        Initialize template engine

        Args:
            template_dir: Directory containing templates
        """
        # Set template directory
        if template_dir:
            self.template_dir = Path(template_dir)
        else:
            # Default to apps/backend/templates/emails
            self.template_dir = Path(__file__).parent.parent.parent / "templates" / "emails"

        # Ensure directory exists
        self.template_dir.mkdir(parents=True, exist_ok=True)

        # Initialize Jinja2 environment
        self.env = Environment(
            loader=FileSystemLoader(str(self.template_dir)),
            autoescape=select_autoescape(["html", "xml"]),
            enable_async=True,  # Enable async template rendering
            cache_size=100,  # Cache compiled templates
        )

        # Add custom filters
        self._register_filters()

        # Add global variables
        self._register_globals()

        # Template cache
        self.template_cache: dict[str, Template] = {}

        logger.info(f"Email template engine initialized with directory: {self.template_dir}")

    def _register_filters(self):
        """Register custom Jinja2 filters"""

        # Date formatting
        def format_date(value, format="%B %d, %Y"):
            """Format datetime object"""
            if isinstance(value, str):
                value = datetime.fromisoformat(value)
            return value.strftime(format) if value else ""

        # Currency formatting
        def format_currency(value, currency="$"):
            """Format currency values"""
            try:
                return f"{currency}{float(value):,.2f}"
            except (ValueError, TypeError):
                return f"{currency}0.00"

        # Markdown rendering
        def render_markdown(text):
            """Convert markdown to HTML"""
            return markdown(text, extensions=["extra", "codehilite"])

        # URL encoding
        def urlencode(value):
            """URL encode a string"""
            from urllib.parse import quote

            return quote(str(value))

        # Truncate text
        def truncate_text(value, length=100, suffix="..."):
            """Truncate text to specified length"""
            if len(value) <= length:
                return value
            return value[:length].rsplit(" ", 1)[0] + suffix

        # Phone number formatting
        def format_phone(value):
            """Format phone numbers"""
            # Remove non-digits
            digits = "".join(filter(str.isdigit, str(value)))
            if len(digits) == 10:
                return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
            return value

        # Register filters
        self.env.filters["format_date"] = format_date
        self.env.filters["format_currency"] = format_currency
        self.env.filters["markdown"] = render_markdown
        self.env.filters["urlencode"] = urlencode
        self.env.filters["truncate"] = truncate_text
        self.env.filters["format_phone"] = format_phone

    def _register_globals(self):
        """Register global variables available in all templates"""
        self.env.globals.update(
            {
                "app_name": settings.APP_NAME,
                "app_url": settings.APP_URL,
                "support_email": settings.SUPPORT_EMAIL,
                "company_name": getattr(settings, "COMPANY_NAME", "ToolboxAI"),
                "current_year": datetime.now().year,
                "environment": settings.ENVIRONMENT,
            }
        )

    async def render_template(
        self, template_name: str, context: dict[str, Any], language: str = "en"
    ) -> str:
        """
        Render email template with context

        Args:
            template_name: Name of template (without .html extension)
            context: Template context variables
            language: Language code for multi-language support

        Returns:
            Rendered HTML string

        Raises:
            TemplateNotFound: If template doesn't exist
            TemplateError: If template rendering fails
        """
        try:
            # Add .html extension if not present
            if not template_name.endswith(".html"):
                template_name = f"{template_name}.html"

            # Check for language-specific template
            if language != "en":
                localized_name = template_name.replace(".html", f".{language}.html")
                if (self.template_dir / localized_name).exists():
                    template_name = localized_name

            # Get template from cache or load
            if template_name not in self.template_cache:
                template = self.env.get_template(template_name)
                self.template_cache[template_name] = template
            else:
                template = self.template_cache[template_name]

            # Merge with default context
            full_context = {**self._get_default_context(), **context}

            # Render template
            html = await template.render_async(**full_context)

            return html

        except TemplateNotFound:
            logger.error(f"Template not found: {template_name}")
            raise
        except TemplateError as e:
            logger.error(f"Template rendering error: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error rendering template: {e}")
            raise TemplateError(f"Failed to render template: {str(e)}")

    def render_template_sync(
        self, template_name: str, context: dict[str, Any], language: str = "en"
    ) -> str:
        """
        Synchronous version of render_template

        Args:
            template_name: Name of template
            context: Template context
            language: Language code

        Returns:
            Rendered HTML string
        """
        try:
            if not template_name.endswith(".html"):
                template_name = f"{template_name}.html"

            # Check for language-specific template
            if language != "en":
                localized_name = template_name.replace(".html", f".{language}.html")
                if (self.template_dir / localized_name).exists():
                    template_name = localized_name

            # Get template
            template = self.env.get_template(template_name)

            # Merge context
            full_context = {**self._get_default_context(), **context}

            # Render
            return template.render(**full_context)

        except Exception as e:
            logger.error(f"Error rendering template: {e}")
            raise

    def _get_default_context(self) -> dict[str, Any]:
        """Get default context for all templates"""
        return {
            "timestamp": datetime.utcnow(),
            "year": datetime.now().year,
            "unsubscribe_url": f"{settings.APP_URL}/unsubscribe",
            "privacy_url": f"{settings.APP_URL}/privacy",
            "terms_url": f"{settings.APP_URL}/terms",
        }

    def list_templates(self, pattern: str = "*.html") -> list[str]:
        """
        List available templates

        Args:
            pattern: Glob pattern for filtering

        Returns:
            List of template names
        """
        templates = []
        for file_path in self.template_dir.glob(pattern):
            if file_path.is_file():
                templates.append(file_path.stem)
        return sorted(set(templates))

    def validate_template(
        self, template_name: str, sample_context: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """
        Validate a template

        Args:
            template_name: Template to validate
            sample_context: Sample context for validation

        Returns:
            Validation results
        """
        results = {"valid": False, "errors": [], "warnings": [], "info": {}}

        try:
            # Check if template exists
            if not template_name.endswith(".html"):
                template_name = f"{template_name}.html"

            template_path = self.template_dir / template_name
            if not template_path.exists():
                results["errors"].append(f"Template not found: {template_name}")
                return results

            # Try to load template
            try:
                template = self.env.get_template(template_name)
            except TemplateError as e:
                results["errors"].append(f"Template syntax error: {str(e)}")
                return results

            # Try to render with sample context
            if sample_context:
                try:
                    rendered = template.render(**sample_context)
                    results["info"]["rendered_length"] = len(rendered)

                    # Check for common issues
                    if "{{" in rendered or "}}" in rendered:
                        results["warnings"].append("Unresolved variables found in rendered output")

                    if "localhost" in rendered or "127.0.0.1" in rendered:
                        results["warnings"].append("Development URLs found in template")

                except Exception as e:
                    results["errors"].append(f"Rendering error: {str(e)}")
                    return results

            # Extract template variables
            template_source = template_path.read_text()
            import re

            variables = re.findall(r"\{\{\s*(\w+)", template_source)
            results["info"]["variables"] = list(set(variables))

            # Check for required variables
            required_vars = ["app_name", "app_url"]
            missing_required = [v for v in required_vars if v not in self.env.globals]
            if missing_required:
                results["warnings"].append(f"Missing required globals: {missing_required}")

            results["valid"] = len(results["errors"]) == 0

        except Exception as e:
            results["errors"].append(f"Validation error: {str(e)}")

        return results

    def create_template(self, name: str, content: str, overwrite: bool = False) -> bool:
        """
        Create a new template

        Args:
            name: Template name
            content: Template content
            overwrite: Whether to overwrite existing

        Returns:
            Success status
        """
        try:
            if not name.endswith(".html"):
                name = f"{name}.html"

            template_path = self.template_dir / name

            if template_path.exists() and not overwrite:
                logger.warning(f"Template already exists: {name}")
                return False

            # Write template
            template_path.write_text(content)

            # Clear cache
            if name in self.template_cache:
                del self.template_cache[name]

            logger.info(f"Template created: {name}")
            return True

        except Exception as e:
            logger.error(f"Error creating template: {e}")
            return False

    def delete_template(self, name: str) -> bool:
        """
        Delete a template

        Args:
            name: Template name

        Returns:
            Success status
        """
        try:
            if not name.endswith(".html"):
                name = f"{name}.html"

            template_path = self.template_dir / name

            if not template_path.exists():
                logger.warning(f"Template not found: {name}")
                return False

            # Delete file
            template_path.unlink()

            # Clear cache
            if name in self.template_cache:
                del self.template_cache[name]

            logger.info(f"Template deleted: {name}")
            return True

        except Exception as e:
            logger.error(f"Error deleting template: {e}")
            return False

    def clear_cache(self):
        """Clear template cache"""
        self.template_cache.clear()
        logger.info("Template cache cleared")

    def get_template_info(self, name: str) -> dict[str, Any]:
        """
        Get information about a template

        Args:
            name: Template name

        Returns:
            Template information
        """
        info = {
            "name": name,
            "exists": False,
            "path": None,
            "size": 0,
            "modified": None,
            "variables": [],
            "extends": None,
            "blocks": [],
        }

        try:
            if not name.endswith(".html"):
                name = f"{name}.html"

            template_path = self.template_dir / name

            if template_path.exists():
                info["exists"] = True
                info["path"] = str(template_path)
                info["size"] = template_path.stat().st_size
                info["modified"] = datetime.fromtimestamp(template_path.stat().st_mtime).isoformat()

                # Parse template content
                content = template_path.read_text()

                # Extract variables
                import re

                info["variables"] = list(set(re.findall(r"\{\{\s*(\w+)", content)))

                # Check for extends
                extends_match = re.search(r'\{%\s*extends\s*["\']([^"\']+)["\']', content)
                if extends_match:
                    info["extends"] = extends_match.group(1)

                # Extract blocks
                info["blocks"] = re.findall(r"\{%\s*block\s+(\w+)", content)

        except Exception as e:
            logger.error(f"Error getting template info: {e}")

        return info


# Create singleton instance
template_engine = EmailTemplateEngine()


# Convenience functions
async def render_email_template(
    template_name: str, context: dict[str, Any], language: str = "en"
) -> str:
    """Render email template"""
    return await template_engine.render_template(template_name, context, language)


def render_email_template_sync(
    template_name: str, context: dict[str, Any], language: str = "en"
) -> str:
    """Render email template synchronously"""
    return template_engine.render_template_sync(template_name, context, language)
