"""
Database model exports.

Provides backwards-compatible imports such as
`from database.models import User`.
"""

# Export agent models
from .agent_models import AgentInstance  # noqa: F401

# Export modern content models
from .content_modern import EducationalContent  # noqa: F401

# Export session model (alias for backward compatibility)
from .models import *  # noqa: F401,F403
from .models import Notification, Session  # noqa: F401

# Export tenant models for multi-tenant testing
from .tenant import Organization  # noqa: F401
