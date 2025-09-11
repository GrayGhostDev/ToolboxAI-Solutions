"""
Base models and mixins for database
"""

from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import DateTime, func, text
from datetime import datetime
from typing import Optional


class Base(DeclarativeBase):
    """Base class for all database models"""

    __tablename__ = None


class TimestampMixin:
    """Mixin to add created_at and updated_at timestamps to models"""

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # Add created_at and updated_at columns
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("CURRENT_TIMESTAMP"),
        nullable=False,
    )

    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        server_onupdate=text("CURRENT_TIMESTAMP"),
        nullable=True,
    )
