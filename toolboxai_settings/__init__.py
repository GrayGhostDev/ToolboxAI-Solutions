"""
ToolboxAI Settings Package

This module provides configuration settings for the ToolboxAI Educational Platform.
"""

from .settings import *
from .settings import settings, should_use_real_data, SERVICE_URLS

__version__ = "1.0.0"
__all__ = ['settings', 'should_use_real_data', 'SERVICE_URLS']