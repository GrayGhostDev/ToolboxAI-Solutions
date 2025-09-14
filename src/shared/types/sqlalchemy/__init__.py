# CLAUDE: Complete SQLAlchemy implementation - 2025-09-13
from typing import Any, Generic, TypeVar
from sqlalchemy import (
    String as SQLString,
    Integer as SQLInteger,
    DateTime as SQLDateTime,
    Boolean as SQLBoolean,
    Text as SQLText,
    JSON as SQLJSON,
    Float as SQLFloat,
    Enum as SQLEnum,
    MetaData,
    Table,
    Column as SQLColumn,
    Result,
    ColumnClause,
    ColumnCollection
)
from sqlalchemy.orm import Session, Query
from sqlalchemy.ext.asyncio import AsyncSession

from .orm import (
    BinaryExpression,
    Column,
    ColumnElement,
    Mapped,
    mapped_column,
    relationship,
)

T = TypeVar("T")

# Re-export SQLAlchemy types with proper typing
String = SQLString
Integer = SQLInteger
DateTime = SQLDateTime
Boolean = SQLBoolean
Text = SQLText
JSON = SQLJSON
Float = SQLFloat
Enum = SQLEnum

# Runtime helpers
SQLCoreOperations: Any = Any
ExpressionElement: Any = Any
TypedColumnsClauseRole: Any = Any
FileDescriptorOrPath: Any = Any

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
