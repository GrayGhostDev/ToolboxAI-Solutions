#!/usr/bin/env python3
"""Simple MCP server runner for development."""

import asyncio
import logging
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from core.mcp.server import MCPServer

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def main():
    """Run the MCP server."""
    server = MCPServer(
        host=os.getenv("MCP_HOST", "0.0.0.0"), port=int(os.getenv("MCP_PORT", "9877"))
    )

    logger.info("Starting MCP Server on port 9877...")
    try:
        await server.start()
    except KeyboardInterrupt:
        logger.info("Shutting down MCP Server...")
    except Exception as e:
        logger.error(f"MCP Server error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
