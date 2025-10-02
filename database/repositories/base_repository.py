"""
Base Repository Pattern (2025 Standards)

Provides generic repository with async SQLAlchemy 2.0 operations.
All specific repositories inherit from this base class.

Reference: https://docs.sqlalchemy.org/en/20/
"""

from typing import Generic, TypeVar, Type, Optional, List, Dict, Any, Sequence
from uuid import UUID

from sqlalchemy import select, update, delete, func, Select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError, NoResultFound

from database.models.base_modern import Base
from database.cache_modern import cache_result, invalidate_cache


# Type variable for model class
ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """
    Generic async repository for database operations.

    Provides CRUD operations with:
    - Type safety
    - Caching support
    - Tenant filtering
    - Pagination
    - Soft delete handling

    Type Parameters:
        ModelType: SQLAlchemy model class
    """

    def __init__(self, model: Type[ModelType]):
        """
        Initialize repository.

        Args:
            model: SQLAlchemy model class
        """
        self.model = model
        self._cache_prefix = model.__tablename__

    async def get_by_id(
        self,
        session: AsyncSession,
        id: UUID,
        include_deleted: bool = False,
    ) -> Optional[ModelType]:
        """
        Get single record by ID.

        Args:
            session: Async database session
            id: Record UUID
            include_deleted: Include soft-deleted records

        Returns:
            Model instance or None if not found
        """
        stmt = select(self.model).where(self.model.id == id)

        # Filter out deleted records unless requested
        if hasattr(self.model, "deleted_at") and not include_deleted:
            stmt = stmt.where(self.model.deleted_at.is_(None))

        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all(
        self,
        session: AsyncSession,
        skip: int = 0,
        limit: int = 100,
        include_deleted: bool = False,
    ) -> List[ModelType]:
        """
        Get all records with pagination.

        Args:
            session: Async database session
            skip: Number of records to skip
            limit: Maximum records to return
            include_deleted: Include soft-deleted records

        Returns:
            List of model instances
        """
        stmt = select(self.model).offset(skip).limit(limit)

        # Filter out deleted records unless requested
        if hasattr(self.model, "deleted_at") and not include_deleted:
            stmt = stmt.where(self.model.deleted_at.is_(None))

        result = await session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_field(
        self,
        session: AsyncSession,
        field_name: str,
        field_value: Any,
        include_deleted: bool = False,
    ) -> List[ModelType]:
        """
        Get records by field value.

        Args:
            session: Async database session
            field_name: Name of field to filter by
            field_value: Value to match
            include_deleted: Include soft-deleted records

        Returns:
            List of matching model instances
        """
        field = getattr(self.model, field_name)
        stmt = select(self.model).where(field == field_value)

        # Filter out deleted records unless requested
        if hasattr(self.model, "deleted_at") and not include_deleted:
            stmt = stmt.where(self.model.deleted_at.is_(None))

        result = await session.execute(stmt)
        return list(result.scalars().all())

    async def create(
        self,
        session: AsyncSession,
        **kwargs: Any,
    ) -> ModelType:
        """
        Create new record.

        Args:
            session: Async database session
            **kwargs: Field values for new record

        Returns:
            Created model instance

        Raises:
            IntegrityError: If unique constraint violated
        """
        instance = self.model(**kwargs)
        session.add(instance)

        try:
            await session.flush()
            await session.refresh(instance)
            return instance
        except IntegrityError:
            await session.rollback()
            raise

    async def create_many(
        self,
        session: AsyncSession,
        items: List[Dict[str, Any]],
    ) -> List[ModelType]:
        """
        Create multiple records in bulk.

        Args:
            session: Async database session
            items: List of dictionaries with field values

        Returns:
            List of created model instances
        """
        instances = [self.model(**item) for item in items]
        session.add_all(instances)

        try:
            await session.flush()
            for instance in instances:
                await session.refresh(instance)
            return instances
        except IntegrityError:
            await session.rollback()
            raise

    async def update(
        self,
        session: AsyncSession,
        id: UUID,
        **kwargs: Any,
    ) -> Optional[ModelType]:
        """
        Update record by ID.

        Args:
            session: Async database session
            id: Record UUID
            **kwargs: Fields to update

        Returns:
            Updated model instance or None if not found
        """
        # Get existing record
        instance = await self.get_by_id(session, id)
        if instance is None:
            return None

        # Update fields
        for field, value in kwargs.items():
            if hasattr(instance, field):
                setattr(instance, field, value)

        try:
            await session.flush()
            await session.refresh(instance)
            return instance
        except IntegrityError:
            await session.rollback()
            raise

    async def delete(
        self,
        session: AsyncSession,
        id: UUID,
        soft: bool = True,
        deleted_by_id: Optional[UUID] = None,
    ) -> bool:
        """
        Delete record by ID.

        Args:
            session: Async database session
            id: Record UUID
            soft: Use soft delete if available
            deleted_by_id: UUID of user performing deletion

        Returns:
            True if deleted, False if not found
        """
        instance = await self.get_by_id(session, id, include_deleted=True)
        if instance is None:
            return False

        # Use soft delete if supported and requested
        if soft and hasattr(instance, "soft_delete"):
            instance.soft_delete(deleted_by_id)
            await session.flush()
            return True

        # Hard delete
        await session.delete(instance)
        await session.flush()
        return True

    async def restore(
        self,
        session: AsyncSession,
        id: UUID,
    ) -> Optional[ModelType]:
        """
        Restore soft-deleted record.

        Args:
            session: Async database session
            id: Record UUID

        Returns:
            Restored model instance or None if not found
        """
        instance = await self.get_by_id(session, id, include_deleted=True)
        if instance is None or not hasattr(instance, "restore"):
            return None

        instance.restore()
        await session.flush()
        await session.refresh(instance)
        return instance

    async def count(
        self,
        session: AsyncSession,
        include_deleted: bool = False,
    ) -> int:
        """
        Count total records.

        Args:
            session: Async database session
            include_deleted: Include soft-deleted records

        Returns:
            Total count
        """
        stmt = select(func.count()).select_from(self.model)

        # Filter out deleted records unless requested
        if hasattr(self.model, "deleted_at") and not include_deleted:
            stmt = stmt.where(self.model.deleted_at.is_(None))

        result = await session.execute(stmt)
        return result.scalar_one()

    async def exists(
        self,
        session: AsyncSession,
        id: UUID,
    ) -> bool:
        """
        Check if record exists.

        Args:
            session: Async database session
            id: Record UUID

        Returns:
            True if exists, False otherwise
        """
        stmt = select(self.model.id).where(self.model.id == id).limit(1)

        if hasattr(self.model, "deleted_at"):
            stmt = stmt.where(self.model.deleted_at.is_(None))

        result = await session.execute(stmt)
        return result.scalar_one_or_none() is not None

    def _apply_filters(
        self,
        stmt: Select,
        filters: Optional[Dict[str, Any]] = None,
    ) -> Select:
        """
        Apply filters to query.

        Args:
            stmt: Base query statement
            filters: Dictionary of field:value filters

        Returns:
            Filtered query statement
        """
        if filters is None:
            return stmt

        for field, value in filters.items():
            if hasattr(self.model, field):
                column = getattr(self.model, field)
                if isinstance(value, (list, tuple)):
                    stmt = stmt.where(column.in_(value))
                else:
                    stmt = stmt.where(column == value)

        return stmt

    async def find(
        self,
        session: AsyncSession,
        filters: Optional[Dict[str, Any]] = None,
        skip: int = 0,
        limit: int = 100,
        order_by: Optional[str] = None,
        descending: bool = False,
        include_deleted: bool = False,
    ) -> List[ModelType]:
        """
        Find records with filters and ordering.

        Args:
            session: Async database session
            filters: Dictionary of field:value filters
            skip: Number of records to skip
            limit: Maximum records to return
            order_by: Field name to order by
            descending: Sort in descending order
            include_deleted: Include soft-deleted records

        Returns:
            List of matching model instances
        """
        stmt = select(self.model)

        # Apply filters
        stmt = self._apply_filters(stmt, filters)

        # Filter out deleted records unless requested
        if hasattr(self.model, "deleted_at") and not include_deleted:
            stmt = stmt.where(self.model.deleted_at.is_(None))

        # Apply ordering
        if order_by and hasattr(self.model, order_by):
            column = getattr(self.model, order_by)
            stmt = stmt.order_by(column.desc() if descending else column.asc())

        # Apply pagination
        stmt = stmt.offset(skip).limit(limit)

        result = await session.execute(stmt)
        return list(result.scalars().all())

    async def find_one(
        self,
        session: AsyncSession,
        filters: Dict[str, Any],
        include_deleted: bool = False,
    ) -> Optional[ModelType]:
        """
        Find single record matching filters.

        Args:
            session: Async database session
            filters: Dictionary of field:value filters
            include_deleted: Include soft-deleted records

        Returns:
            Model instance or None if not found
        """
        stmt = select(self.model)

        # Apply filters
        stmt = self._apply_filters(stmt, filters)

        # Filter out deleted records unless requested
        if hasattr(self.model, "deleted_at") and not include_deleted:
            stmt = stmt.where(self.model.deleted_at.is_(None))

        stmt = stmt.limit(1)

        result = await session.execute(stmt)
        return result.scalar_one_or_none()


# Export base repository
__all__ = ["BaseRepository"]
