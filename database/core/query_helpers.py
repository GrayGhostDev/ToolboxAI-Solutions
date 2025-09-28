"""
Database Query Helpers - Safe query building with SQLAlchemy 2.0 best practices

Provides utilities for building safe, parameterized queries following 2025 best practices
for SQLAlchemy TextClause usage and SQL injection prevention.
"""

import re
import logging
from typing import Dict, Any, Optional, List, Type, Union
from sqlalchemy import text, Integer, String, Float, Boolean, DateTime, bindparam
from sqlalchemy.sql.elements import TextClause
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.engine import Result
from sqlalchemy.sql.type_api import TypeEngine

logger = logging.getLogger(__name__)


class QueryValidationError(Exception):
    """Raised when a query fails validation"""
    pass


class SafeQueryBuilder:
    """
    Safe query builder with TextClause validation following 2025 best practices.
    
    Features:
    - SQL injection prevention
    - Proper parameterization
    - Type hints for results
    - Async execution support
    """
    
    # Patterns that might indicate SQL injection attempts
    DANGEROUS_PATTERNS = [
        r';\s*(DROP|DELETE|TRUNCATE|ALTER|CREATE|INSERT|UPDATE)',  # Multiple statements
        r'--\s*',  # SQL comments
        r'\/\*.*\*\/',  # Multi-line comments
        r'(UNION|INTERSECT|EXCEPT)\s+(ALL\s+)?SELECT',  # Set operations
        r'(EXEC|EXECUTE)\s*\(',  # Dynamic SQL execution
        r'xp_cmdshell',  # SQL Server command execution
    ]
    
    @classmethod
    def validate_query(cls, query_str: str) -> bool:
        """
        Validate query for potential SQL injection patterns.
        
        Args:
            query_str: The SQL query string to validate
            
        Returns:
            bool: True if query is safe, False otherwise
            
        Raises:
            QueryValidationError: If dangerous patterns are detected
        """
        for pattern in cls.DANGEROUS_PATTERNS:
            if re.search(pattern, query_str, re.IGNORECASE):
                raise QueryValidationError(
                    f"Potentially dangerous SQL pattern detected: {pattern}"
                )
        return True
    
    @classmethod
    def build_text_clause(
        cls,
        query: str,
        params: Optional[Dict[str, Any]] = None,
        column_types: Optional[Dict[str, TypeEngine]] = None
    ) -> TextClause:
        """
        Build a properly parameterized TextClause following 2025 best practices.
        
        Args:
            query: SQL query with :param_name placeholders
            params: Dictionary of parameter values
            column_types: Dictionary of column names to SQLAlchemy types
            
        Returns:
            TextClause: Properly configured text clause
            
        Example:
            query = cls.build_text_clause(
                "SELECT * FROM users WHERE id = :user_id",
                {"user_id": 123},
                {"id": Integer, "name": String}
            )
        """
        # Validate the query
        cls.validate_query(query)
        
        # Create the text clause
        text_clause = text(query)
        
        # Add parameter bindings if provided
        if params:
            # Use bindparams for secure parameter binding (2025 best practice)
            bound_params = []
            for key, value in params.items():
                # Automatically detect type if not specified
                if value is None:
                    param_type = None
                elif isinstance(value, int):
                    param_type = Integer
                elif isinstance(value, str):
                    param_type = String
                elif isinstance(value, float):
                    param_type = Float
                elif isinstance(value, bool):
                    param_type = Boolean
                else:
                    param_type = None
                
                bound_params.append(bindparam(key, value=value, type_=param_type))
            
            text_clause = text_clause.bindparams(*bound_params)
        
        # Add column type information if provided
        if column_types:
            text_clause = text_clause.columns(**column_types)
        
        return text_clause
    
    @classmethod
    async def async_execute(
        cls,
        session: AsyncSession,
        query: str,
        params: Optional[Dict[str, Any]] = None,
        column_types: Optional[Dict[str, TypeEngine]] = None
    ) -> Result:
        """
        Execute a query asynchronously with proper error handling.
        
        Args:
            session: Async database session
            query: SQL query string
            params: Query parameters
            column_types: Column type hints
            
        Returns:
            Result: Query execution result
        """
        try:
            text_clause = cls.build_text_clause(query, params, column_types)
            result = await session.execute(text_clause)
            return result
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            logger.debug(f"Query: {query}")
            logger.debug(f"Params: {params}")
            raise
    
    @classmethod
    async def fetch_all(
        cls,
        session: AsyncSession,
        query: str,
        params: Optional[Dict[str, Any]] = None,
        column_types: Optional[Dict[str, TypeEngine]] = None
    ) -> List[Dict[str, Any]]:
        """
        Fetch all results as dictionaries.
        
        Args:
            session: Async database session
            query: SQL query string
            params: Query parameters
            column_types: Column type hints
            
        Returns:
            List of result dictionaries
        """
        result = await cls.async_execute(session, query, params, column_types)
        return [dict(row._mapping) for row in result]
    
    @classmethod
    async def fetch_one(
        cls,
        session: AsyncSession,
        query: str,
        params: Optional[Dict[str, Any]] = None,
        column_types: Optional[Dict[str, TypeEngine]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Fetch one result as a dictionary.
        
        Args:
            session: Async database session
            query: SQL query string
            params: Query parameters
            column_types: Column type hints
            
        Returns:
            Result dictionary or None
        """
        result = await cls.async_execute(session, query, params, column_types)
        row = result.first()
        return dict(row._mapping) if row else None
    
    @classmethod
    async def fetch_scalar(
        cls,
        session: AsyncSession,
        query: str,
        params: Optional[Dict[str, Any]] = None
    ) -> Any:
        """
        Fetch a single scalar value.
        
        Args:
            session: Async database session
            query: SQL query string
            params: Query parameters
            
        Returns:
            Scalar value or None
        """
        result = await cls.async_execute(session, query, params)
        return result.scalar()


class BatchQueryExecutor:
    """
    Execute multiple queries efficiently in a batch.
    
    Useful for bulk operations while maintaining safety.
    """
    
    @classmethod
    async def execute_batch(
        cls,
        session: AsyncSession,
        queries: List[tuple[str, Dict[str, Any]]]
    ) -> List[Result]:
        """
        Execute multiple queries in a single transaction.
        
        Args:
            session: Async database session
            queries: List of (query_string, params) tuples
            
        Returns:
            List of results
        """
        results = []
        
        try:
            for query_str, params in queries:
                text_clause = SafeQueryBuilder.build_text_clause(query_str, params)
                result = await session.execute(text_clause)
                results.append(result)
            
            await session.commit()
            return results
            
        except Exception as e:
            await session.rollback()
            logger.error(f"Batch execution failed: {e}")
            raise


def create_safe_insert(
    table_name: str,
    values: Dict[str, Any],
    returning: Optional[List[str]] = None
) -> tuple[str, Dict[str, Any]]:
    """
    Create a safe INSERT statement with proper parameterization.
    
    Args:
        table_name: Name of the table
        values: Dictionary of column:value pairs
        returning: Optional list of columns to return
        
    Returns:
        Tuple of (query_string, params)
    """
    # Validate table name (alphanumeric and underscore only)
    if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', table_name):
        raise QueryValidationError(f"Invalid table name: {table_name}")
    
    columns = list(values.keys())
    placeholders = [f":{col}" for col in columns]
    
    query = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({', '.join(placeholders)})"
    
    if returning:
        query += f" RETURNING {', '.join(returning)}"
    
    return query, values


def create_safe_update(
    table_name: str,
    values: Dict[str, Any],
    where_clause: str,
    where_params: Dict[str, Any]
) -> tuple[str, Dict[str, Any]]:
    """
    Create a safe UPDATE statement with proper parameterization.
    
    Args:
        table_name: Name of the table
        values: Dictionary of column:value pairs to update
        where_clause: WHERE clause with :param placeholders
        where_params: Parameters for WHERE clause
        
    Returns:
        Tuple of (query_string, params)
    """
    # Validate table name
    if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', table_name):
        raise QueryValidationError(f"Invalid table name: {table_name}")
    
    set_clauses = [f"{col} = :set_{col}" for col in values.keys()]
    
    # Prefix value parameters to avoid conflicts with where parameters
    prefixed_values = {f"set_{k}": v for k, v in values.items()}
    
    query = f"UPDATE {table_name} SET {', '.join(set_clauses)} WHERE {where_clause}"
    
    # Combine all parameters
    all_params = {**prefixed_values, **where_params}
    
    return query, all_params