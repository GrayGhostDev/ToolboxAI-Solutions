"""
Custom scalar type definitions for GraphQL
"""

import json
import uuid
from datetime import datetime
from typing import Any

from ariadne import ScalarType

# DateTime scalar
datetime_scalar = ScalarType("DateTime")


@datetime_scalar.serializer
def serialize_datetime(value: datetime) -> str:
    """Serialize datetime to ISO format string"""
    if isinstance(value, datetime):
        return value.isoformat()
    return str(value)


@datetime_scalar.value_parser
def parse_datetime_value(value: str) -> datetime:
    """Parse ISO format string to datetime"""
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        raise ValueError(f"Invalid datetime format: {value}")


@datetime_scalar.literal_parser
def parse_datetime_literal(ast, _variables=None):
    """Parse datetime from GraphQL literal"""
    return parse_datetime_value(ast.value)


# UUID scalar
uuid_scalar = ScalarType("UUID")


@uuid_scalar.serializer
def serialize_uuid(value: uuid.UUID) -> str:
    """Serialize UUID to string"""
    if isinstance(value, uuid.UUID):
        return str(value)
    return str(value)


@uuid_scalar.value_parser
def parse_uuid_value(value: str) -> uuid.UUID:
    """Parse string to UUID"""
    try:
        return uuid.UUID(value)
    except (ValueError, AttributeError):
        raise ValueError(f"Invalid UUID format: {value}")


@uuid_scalar.literal_parser
def parse_uuid_literal(ast, _variables=None):
    """Parse UUID from GraphQL literal"""
    return parse_uuid_value(ast.value)


# JSON scalar
json_scalar = ScalarType("JSON")


@json_scalar.serializer
def serialize_json(value: Any) -> Any:
    """Serialize JSON value"""
    if isinstance(value, str):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return value
    return value


@json_scalar.value_parser
def parse_json_value(value: Any) -> Any:
    """Parse JSON value"""
    return value


@json_scalar.literal_parser
def parse_json_literal(ast, _variables=None):
    """Parse JSON from GraphQL literal"""
    return ast.value


# Email scalar
email_scalar = ScalarType("Email")


@email_scalar.serializer
def serialize_email(value: str) -> str:
    """Serialize email address"""
    return str(value).lower()


@email_scalar.value_parser
def parse_email_value(value: str) -> str:
    """Parse and validate email address"""
    import re

    email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"

    if not isinstance(value, str):
        raise ValueError(f"Email must be a string, got {type(value)}")

    value = value.lower().strip()

    if not re.match(email_pattern, value):
        raise ValueError(f"Invalid email format: {value}")

    return value


@email_scalar.literal_parser
def parse_email_literal(ast, _variables=None):
    """Parse email from GraphQL literal"""
    return parse_email_value(ast.value)


# URL scalar
url_scalar = ScalarType("URL")


@url_scalar.serializer
def serialize_url(value: str) -> str:
    """Serialize URL"""
    return str(value)


@url_scalar.value_parser
def parse_url_value(value: str) -> str:
    """Parse and validate URL"""
    from urllib.parse import urlparse

    if not isinstance(value, str):
        raise ValueError(f"URL must be a string, got {type(value)}")

    try:
        result = urlparse(value)
        if not all([result.scheme, result.netloc]):
            raise ValueError(f"Invalid URL format: {value}")
    except Exception:
        raise ValueError(f"Invalid URL format: {value}")

    return value


@url_scalar.literal_parser
def parse_url_literal(ast, _variables=None):
    """Parse URL from GraphQL literal"""
    return parse_url_value(ast.value)
