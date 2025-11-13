"""Base factory configuration for test data generation."""

import uuid
from datetime import datetime, timezone

import factory
from faker import Faker

fake = Faker()


class BaseFactory(factory.Factory):
    """Base factory with common configuration."""

    class Meta:
        abstract = True

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        """Create an instance with proper ID generation."""
        if "id" not in kwargs:
            kwargs["id"] = str(uuid.uuid4())
        if "created_at" not in kwargs and hasattr(model_class, "created_at"):
            kwargs["created_at"] = datetime.now(timezone.utc)
        if "updated_at" not in kwargs and hasattr(model_class, "updated_at"):
            kwargs["updated_at"] = datetime.now(timezone.utc)
        return super()._create(model_class, *args, **kwargs)


class DictFactory(BaseFactory):
    """Factory that produces dictionaries instead of objects."""

    class Meta:
        abstract = True

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        """Return a dictionary instead of an object."""
        if "id" not in kwargs:
            kwargs["id"] = str(uuid.uuid4())
        if "created_at" not in kwargs:
            kwargs["created_at"] = datetime.now(timezone.utc).isoformat()
        if "updated_at" not in kwargs:
            kwargs["updated_at"] = datetime.now(timezone.utc).isoformat()
        return kwargs


class AsyncMixin:
    """Mixin for factories that need async creation."""

    @classmethod
    async def create_async(cls, **kwargs):
        """Create an instance asynchronously."""
        instance = cls.build(**kwargs)
        # Here you would save to async database
        return instance

    @classmethod
    async def create_batch_async(cls, size: int, **kwargs):
        """Create multiple instances asynchronously."""
        return [await cls.create_async(**kwargs) for _ in range(size)]
