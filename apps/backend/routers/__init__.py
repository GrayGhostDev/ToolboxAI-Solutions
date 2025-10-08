"""
Backend Routers Package

Contains all API routers for the backend application.
"""

from apps.backend.routers.courses import router as courses_router

__all__ = ["courses_router"]

