"""
ToolboxAI Roblox Environment Server Package

This package provides the complete server implementation for the ToolboxAI Roblox Environment,
including FastAPI main server, Flask bridge server, and all supporting components.

Key Components:
- FastAPI main application (port 8008)
- Flask bridge server for Roblox Studio (port 5001)
- LangChain tools for educational content generation
- WebSocket support for real-time updates
- Authentication and authorization
- LMS integration capabilities

Author: ToolboxAI Solutions
Version: 1.0.0
"""

import os
import sys
import logging
from pathlib import Path

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Ensure logs directory exists before configuring logging
os.makedirs(PROJECT_ROOT / "logs", exist_ok=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(PROJECT_ROOT / "logs" / "server.log", mode='a')
    ]
)

logger = logging.getLogger(__name__)

# Version info
__version__ = "1.0.0"
__author__ = "ToolboxAI Solutions"
__description__ = "AI-Powered Educational Roblox Environment Server"

# Export main components
from .main import app as fastapi_app
from .roblox_server import app as flask_app
from .tools import ALL_TOOLS
from .models import *
from .config import settings

__all__ = [
    "fastapi_app",
    "flask_app", 
    "ALL_TOOLS",
    "settings",
    "__version__",
    "__author__",
    "__description__"
]

logger.info(f"ToolboxAI Roblox Environment Server v{__version__} initialized")