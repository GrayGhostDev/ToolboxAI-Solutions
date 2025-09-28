"""
Custom GraphQL directives for authentication and rate limiting
"""

import time
from typing import Any, Dict, Optional
from functools import wraps

from ariadne import SchemaDirectiveVisitor
from graphql import GraphQLError, default_field_resolver


class AuthDirective(SchemaDirectiveVisitor):
    """
    Authentication directive to protect fields

    Usage: @auth(requires: Role)
    """

    def visit_field_definition(self, field, object_type):
        """Apply authentication check to field resolver"""

        original_resolver = field.resolve or default_field_resolver
        requires_role = self.args.get("requires", "USER")

        def resolve_with_auth(obj, info, **kwargs):
            # Get user from context
            user = info.context.get("user")

            if not user:
                raise GraphQLError(
                    "Authentication required", extensions={"code": "UNAUTHENTICATED"}
                )

            # Check role if specified
            if requires_role and requires_role != "USER":
                user_role = getattr(user, "role", None)

                # Convert role enum to string for comparison
                if hasattr(user_role, "value"):
                    user_role = user_role.value.upper()
                elif user_role:
                    user_role = str(user_role).upper()

                required_role = str(requires_role).upper()

                # Check role hierarchy
                role_hierarchy = {"STUDENT": 0, "PARENT": 1, "TEACHER": 2, "ADMIN": 3}

                user_level = role_hierarchy.get(user_role, -1)
                required_level = role_hierarchy.get(required_role, 999)

                if user_level < required_level:
                    raise GraphQLError(
                        f"Insufficient permissions. Required role: {required_role}",
                        extensions={"code": "FORBIDDEN"},
                    )

            return original_resolver(obj, info, **kwargs)

        field.resolve = resolve_with_auth
        return field


class RateLimitDirective(SchemaDirectiveVisitor):
    """
    Rate limiting directive to prevent abuse

    Usage: @rateLimit(max: 10, window: "1h")
    """

    # Simple in-memory rate limit storage
    # In production, use Redis or similar
    _rate_limits: Dict[str, Dict[str, Any]] = {}

    def visit_field_definition(self, field, object_type):
        """Apply rate limiting to field resolver"""

        original_resolver = field.resolve or default_field_resolver
        max_requests = self.args.get("max", 100)
        window = self.args.get("window", "1h")

        # Parse window to seconds
        window_seconds = self._parse_window(window)

        def resolve_with_rate_limit(obj, info, **kwargs):
            # Get user identifier
            user = info.context.get("user")
            if user:
                user_id = str(user.id)
            else:
                # Use IP address for anonymous users
                request = info.context.get("request")
                user_id = request.client.host if request else "unknown"

            # Create rate limit key
            field_name = f"{object_type.name}.{field.name}"
            rate_limit_key = f"{user_id}:{field_name}"

            # Check rate limit
            current_time = time.time()

            if rate_limit_key not in self._rate_limits:
                self._rate_limits[rate_limit_key] = {"count": 0, "window_start": current_time}

            rate_data = self._rate_limits[rate_limit_key]

            # Reset window if expired
            if current_time - rate_data["window_start"] > window_seconds:
                rate_data["count"] = 0
                rate_data["window_start"] = current_time

            # Check if limit exceeded
            if rate_data["count"] >= max_requests:
                remaining_time = window_seconds - (current_time - rate_data["window_start"])
                raise GraphQLError(
                    f"Rate limit exceeded. Try again in {int(remaining_time)} seconds",
                    extensions={
                        "code": "RATE_LIMITED",
                        "max": max_requests,
                        "window": window,
                        "retry_after": int(remaining_time),
                    },
                )

            # Increment counter
            rate_data["count"] += 1

            return original_resolver(obj, info, **kwargs)

        field.resolve = resolve_with_rate_limit
        return field

    def _parse_window(self, window: str) -> int:
        """Parse window string to seconds"""

        # Simple parser for formats like "1h", "30m", "60s"
        unit_multipliers = {"s": 1, "m": 60, "h": 3600, "d": 86400}

        # Extract number and unit
        import re

        match = re.match(r"(\d+)([smhd])", window.lower())

        if not match:
            # Default to 1 hour if parsing fails
            return 3600

        number = int(match.group(1))
        unit = match.group(2)

        return number * unit_multipliers.get(unit, 3600)
