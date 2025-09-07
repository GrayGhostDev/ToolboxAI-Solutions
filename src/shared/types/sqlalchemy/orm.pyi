"""Lightweight, pragmatic typing stub for sqlalchemy.orm used by the project.

This stub models the common, ergonomic surface the codebase uses:
- `Mapped[T]` is a descriptor that yields `T` when accessed on an instance.
- `Column[T]` is a subclass of `Mapped[T]` so class-level assignments like
  `foo: Mapped[str] = Column(String)` are accepted, while instance access
  `obj.foo` is typed as `str` (the desired behavior for static checking).

The goal is to reduce false-positive errors in the type checker while
remaining intentionally permissive. Further refinement is possible if needed.
"""

from typing import Any, Generic, TypeVar

T = TypeVar("T")

# Declarative base (opaque to the checker)
DeclarativeBase: Any

class Mapped(Generic[T]):
    """Descriptor used for ORM mapped attributes.

    When accessed on an instance, a Mapped[T] returns T. When used at the
    class level it acts as a descriptor target (e.g. assigned to Column(...)).
    """

    def __get__(self, instance: Any, owner: Any) -> T: ...
    def __set__(self, instance: Any, value: T) -> None: ...
    def __delete__(self, instance: Any) -> None: ...

class Column(Mapped[T], Generic[T]):
    """Represents a Column[...] object (class-level). Subclasses Mapped so
    assignments like `field: Mapped[int] = Column(...)` type-check.
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None: ...

class ColumnElement(Generic[T]):
    """Expression/element class used in SQLAlchemy expression APIs.

    We keep this permissive but distinct from bool/str so the checker can
    flag accidental truthiness checks on expressions.
    """

    ...

class BinaryExpression(ColumnElement[bool]): ...

def mapped_column(*args: Any, **kwargs: Any) -> Column[Any]: ...
def relationship(arg: Any = ..., **kwargs: Any) -> Any: ...

__all__ = [
    "DeclarativeBase",
    "Mapped",
    "Column",
    "ColumnElement",
    "BinaryExpression",
    "mapped_column",
    "relationship",
]
