# Minimal typing shim for SQLAlchemy used to reduce pyright noise.
from typing import Any

"""Permissive SQLAlchemy stubs to reduce static-checker noise.

This file intentionally maps commonly-used SQLAlchemy symbols to 'Any'.
It's a pragmatic shim to avoid large numbers of false-positive type errors
in code that mixes runtime SQLAlchemy model attributes with plain Python values.

Refine these definitions later where precise typing is useful.
"""

from .orm import (
    BinaryExpression,
    Column,
    ColumnElement,
    Mapped,
    mapped_column,
    relationship,
)

# Keep a permissive fallback for names that are not modelled precisely in this
# stub. We want to provide useful hints for the most common ORM symbols while
# leaving other runtime helpers as Any.
SQLCoreOperations: Any
ExpressionElement: Any
TypedColumnsClauseRole: Any
FileDescriptorOrPath: Any

# Common SQL types often imported from `sqlalchemy` (permissive)
String: Any
Integer: Any
DateTime: Any
Boolean: Any
Text: Any
JSON: Any
Float: Any
Enum: Any

# Runtime helpers / commonly referenced names (permissive)
Result: Any
Session: Any
AsyncSession: Any
Table: Any
MetaData: Any
Query: Any
ColumnClause: Any
ColumnCollection: Any

__all__ = [
    "Column",
    "ColumnElement",
    "BinaryExpression",
    "Result",
    "AsyncSession",
    "Session",
    "Table",
    "MetaData",
    "Query",
    "ColumnClause",
    "ColumnCollection",
    "SQLCoreOperations",
    "ExpressionElement",
    "TypedColumnsClauseRole",
    "FileDescriptorOrPath",
    "String",
    "Integer",
    "DateTime",
    "Boolean",
    "Text",
    "JSON",
    "Float",
    "Enum",
    "Mapped",
    "mapped_column",
    "relationship",
]
