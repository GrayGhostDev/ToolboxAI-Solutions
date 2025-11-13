"""
GraphQL context management for request-scoped dependencies
"""

from typing import Any

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from apps.backend.core.config import settings
from database.database_service import get_async_session

from .dataloaders import create_loaders


async def get_context(
    request: Request, db: AsyncSession = Depends(get_async_session)
) -> dict[str, Any]:
    """
    Create GraphQL context with request-scoped dependencies

    Args:
        request: FastAPI request object
        db: Database session

    Returns:
        Context dictionary with database, user, and other dependencies
    """

    # Get current user if authenticated
    user = None
    auth_header = request.headers.get("authorization")
    if auth_header:
        try:
            from apps.backend.api.auth.auth import decode_token

            token = auth_header.split(" ")[1] if " " in auth_header else auth_header
            user_data = decode_token(token)
            if user_data:
                # Load user from database
                from database.models import User

                user = await db.get(User, user_data.get("sub"))
        except Exception:
            pass  # Invalid token, continue without user

    # Create data loaders for batch loading
    loaders = create_loaders(db)

    # Build context
    context = {
        "request": request,
        "db": db,
        "user": user,
        "loaders": loaders,
        "settings": settings,
        "is_authenticated": user is not None,
    }

    return context
