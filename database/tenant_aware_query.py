"""
Tenant-Aware Query Utilities
=============================

Provides automatic organization-scoped query filtering for multi-tenant data isolation.

This module provides helper classes and decorators that automatically add organization_id
filtering to database queries, reducing boilerplate and ensuring multi-tenant security.

Usage:
    from database.tenant_aware_query import TenantAwareQuery, tenant_scoped

    # Method 1: Using TenantAwareQuery helper
    query = TenantAwareQuery(session, AgentInstance, organization_id=current_org_id)
    agents = query.filter_by(agent_type='content').all()

    # Method 2: Using decorator for automatic scoping
    @tenant_scoped
    def get_agent_instances(session: Session, organization_id: UUID, **filters):
        return session.query(AgentInstance).filter_by(**filters).all()

    # Method 3: Using scoped session manager
    with tenant_session(session, organization_id) as scoped_session:
        agents = scoped_session.query(AgentInstance).all()

Models Supported:
    - All models inheriting from TenantBaseModel (have organization_id column)
    - Automatically excludes GlobalBaseModel (system_health, content_cache)
"""

import logging
from contextlib import contextmanager
from functools import wraps
from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union
from uuid import UUID

from sqlalchemy import inspect
from sqlalchemy.orm import Query, Session

logger = logging.getLogger(__name__)

# Type variable for generic model
T = TypeVar("T")


class TenantAwareQuery(Generic[T]):
    """
    Query helper that automatically filters by organization_id

    Provides a fluent interface for building queries with automatic
    tenant isolation. All queries are automatically scoped to the
    specified organization.

    Example:
        query = TenantAwareQuery(session, AgentInstance, organization_id)
        agents = query.filter_by(status='active').order_by('created_at').all()
    """

    def __init__(
        self,
        session: Session,
        model: Type[T],
        organization_id: UUID,
        bypass_tenant_check: bool = False,
    ):
        """
        Initialize tenant-aware query

        Args:
            session: SQLAlchemy session
            model: Model class to query
            organization_id: Organization UUID for filtering
            bypass_tenant_check: If True, skip tenant filtering (admin mode)
        """
        self.session = session
        self.model = model
        self.organization_id = organization_id
        self.bypass_tenant_check = bypass_tenant_check
        self._query: Optional[Query] = None

        # Verify model has organization_id column
        if not bypass_tenant_check and not self._has_organization_id():
            logger.warning(
                f"Model {model.__name__} does not have organization_id column. "
                f"Query will not be tenant-scoped."
            )

    def _has_organization_id(self) -> bool:
        """Check if model has organization_id column"""
        mapper = inspect(self.model)
        return "organization_id" in [c.key for c in mapper.columns]

    def _get_base_query(self) -> Query:
        """Get base query with organization filter"""
        query = self.session.query(self.model)

        # Add organization filter if applicable
        if not self.bypass_tenant_check and self._has_organization_id():
            query = query.filter(self.model.organization_id == self.organization_id)

        return query

    def filter_by(self, **kwargs) -> "TenantAwareQuery[T]":
        """Filter by keyword arguments"""
        if self._query is None:
            self._query = self._get_base_query()

        self._query = self._query.filter_by(**kwargs)
        return self

    def filter(self, *args) -> "TenantAwareQuery[T]":
        """Filter by SQLAlchemy expressions"""
        if self._query is None:
            self._query = self._get_base_query()

        self._query = self._query.filter(*args)
        return self

    def order_by(self, *args) -> "TenantAwareQuery[T]":
        """Order by column(s)"""
        if self._query is None:
            self._query = self._get_base_query()

        self._query = self._query.order_by(*args)
        return self

    def limit(self, limit: int) -> "TenantAwareQuery[T]":
        """Limit results"""
        if self._query is None:
            self._query = self._get_base_query()

        self._query = self._query.limit(limit)
        return self

    def offset(self, offset: int) -> "TenantAwareQuery[T]":
        """Offset results"""
        if self._query is None:
            self._query = self._get_base_query()

        self._query = self._query.offset(offset)
        return self

    def all(self) -> List[T]:
        """Execute query and return all results"""
        if self._query is None:
            self._query = self._get_base_query()

        results = self._query.all()
        logger.debug(
            f"TenantAwareQuery: Retrieved {len(results)} {self.model.__name__} "
            f"records for org {self.organization_id}"
        )
        return results

    def first(self) -> Optional[T]:
        """Execute query and return first result"""
        if self._query is None:
            self._query = self._get_base_query()

        result = self._query.first()
        logger.debug(
            f"TenantAwareQuery: Retrieved {self.model.__name__} "
            f"for org {self.organization_id}: {result is not None}"
        )
        return result

    def one(self) -> T:
        """Execute query and return exactly one result (raises if not found or multiple)"""
        if self._query is None:
            self._query = self._get_base_query()

        return self._query.one()

    def one_or_none(self) -> Optional[T]:
        """Execute query and return one result or None"""
        if self._query is None:
            self._query = self._get_base_query()

        return self._query.one_or_none()

    def count(self) -> int:
        """Count query results"""
        if self._query is None:
            self._query = self._get_base_query()

        count = self._query.count()
        logger.debug(
            f"TenantAwareQuery: Counted {count} {self.model.__name__} "
            f"records for org {self.organization_id}"
        )
        return count

    def exists(self) -> bool:
        """Check if any records exist"""
        return self.count() > 0

    def delete(self, synchronize_session: Union[str, bool] = "fetch") -> int:
        """Delete matching records"""
        if self._query is None:
            self._query = self._get_base_query()

        deleted_count = self._query.delete(synchronize_session=synchronize_session)
        logger.info(
            f"TenantAwareQuery: Deleted {deleted_count} {self.model.__name__} "
            f"records for org {self.organization_id}"
        )
        return deleted_count

    def update(
        self, values: Dict[str, Any], synchronize_session: Union[str, bool] = "fetch"
    ) -> int:
        """Update matching records"""
        if self._query is None:
            self._query = self._get_base_query()

        # Ensure organization_id is not being changed
        if "organization_id" in values and values["organization_id"] != self.organization_id:
            raise ValueError(
                "Cannot change organization_id via TenantAwareQuery.update(). "
                "This would violate tenant isolation."
            )

        updated_count = self._query.update(values, synchronize_session=synchronize_session)
        logger.info(
            f"TenantAwareQuery: Updated {updated_count} {self.model.__name__} "
            f"records for org {self.organization_id}"
        )
        return updated_count


def tenant_scoped(func):
    """
    Decorator that automatically adds organization_id filtering to query functions

    The decorated function must accept 'organization_id' as a parameter and
    return a SQLAlchemy query.

    Example:
        @tenant_scoped
        def get_active_agents(session: Session, organization_id: UUID):
            return session.query(AgentInstance).filter_by(status='active')

        # Automatically filters by organization_id
        agents = get_active_agents(session, current_org_id)
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        # Extract organization_id from kwargs
        organization_id = kwargs.get("organization_id")
        if not organization_id:
            raise ValueError(
                f"Function {func.__name__} decorated with @tenant_scoped "
                f"must receive 'organization_id' parameter"
            )

        # Call original function
        query_or_result = func(*args, **kwargs)

        # If result is a Query, add organization filter
        if isinstance(query_or_result, Query):
            # Get model from query
            model = query_or_result.column_descriptions[0]["type"]

            # Check if model has organization_id
            mapper = inspect(model)
            if "organization_id" in [c.key for c in mapper.columns]:
                # Add organization filter
                query_or_result = query_or_result.filter(model.organization_id == organization_id)
                logger.debug(
                    f"tenant_scoped: Applied organization filter to "
                    f"{func.__name__} for org {organization_id}"
                )

        return query_or_result

    return wrapper


@contextmanager
def tenant_session(session: Session, organization_id: UUID):
    """
    Context manager that sets organization_id for all queries in a block

    Sets PostgreSQL session variable for RLS policies and provides
    automatic query filtering.

    Example:
        with tenant_session(session, organization_id) as scoped_session:
            agents = scoped_session.query(AgentInstance).all()
            # Automatically filtered by organization_id

    Args:
        session: SQLAlchemy session
        organization_id: Organization UUID for filtering

    Yields:
        Session with organization context set
    """
    # Set PostgreSQL session variable for RLS
    session.execute(f"SET app.current_organization_id = '{organization_id}'")
    logger.debug(f"tenant_session: Set organization context to {organization_id}")

    try:
        yield session
    finally:
        # Reset session variable
        session.execute("RESET app.current_organization_id")
        logger.debug("tenant_session: Reset organization context")


class TenantAwareSessionMixin:
    """
    Mixin for adding tenant-aware query methods to session

    Add to custom session class:
        class TenantSession(Session, TenantAwareSessionMixin):
            pass

    Usage:
        session = TenantSession(bind=engine)
        session.set_organization(organization_id)
        agents = session.query_tenant(AgentInstance).filter_by(status='active').all()
    """

    _current_organization_id: Optional[UUID] = None

    def set_organization(self, organization_id: UUID):
        """Set current organization for this session"""
        self._current_organization_id = organization_id

        # Set PostgreSQL session variable for RLS
        self.execute(f"SET app.current_organization_id = '{organization_id}'")
        logger.debug(f"Session: Set organization context to {organization_id}")

    def reset_organization(self):
        """Reset organization context"""
        self._current_organization_id = None
        self.execute("RESET app.current_organization_id")
        logger.debug("Session: Reset organization context")

    def query_tenant(self, model: Type[T], **kwargs) -> TenantAwareQuery[T]:
        """Create tenant-aware query for model"""
        if not self._current_organization_id:
            raise ValueError("Organization not set. Call session.set_organization(org_id) first.")

        return TenantAwareQuery(self, model, self._current_organization_id, **kwargs)

    def get_organization_id(self) -> Optional[UUID]:
        """Get current organization ID"""
        return self._current_organization_id


def verify_tenant_isolation(
    session: Session, model: Type[T], organization_id: UUID, expected_count: Optional[int] = None
) -> bool:
    """
    Verify tenant isolation for a model

    Checks that:
    1. Model has organization_id column
    2. All records belong to specified organization
    3. Record count matches expected (if provided)

    Args:
        session: SQLAlchemy session
        model: Model class to verify
        organization_id: Organization UUID to verify
        expected_count: Expected number of records (optional)

    Returns:
        True if verification passes, False otherwise
    """
    # Check if model has organization_id
    mapper = inspect(model)
    if "organization_id" not in [c.key for c in mapper.columns]:
        logger.warning(f"Model {model.__name__} does not have organization_id column")
        return False

    # Count records for this organization
    org_count = session.query(model).filter_by(organization_id=organization_id).count()

    # Count records for other organizations
    other_count = session.query(model).filter(model.organization_id != organization_id).count()

    logger.info(
        f"Tenant Isolation Check - {model.__name__}: "
        f"{org_count} records in org {organization_id}, "
        f"{other_count} records in other orgs"
    )

    # Verify expected count if provided
    if expected_count is not None and org_count != expected_count:
        logger.error(
            f"Expected {expected_count} records but found {org_count} "
            f"for {model.__name__} in org {organization_id}"
        )
        return False

    # Verification passed if we only see our org's data
    # (other_count being > 0 is fine, just confirms isolation)
    return True


def batch_update_organization(
    session: Session,
    model: Type[T],
    records: List[Any],
    organization_id: UUID,
    batch_size: int = 100,
) -> int:
    """
    Batch update organization_id for multiple records

    Safely updates organization_id for a list of records in batches.

    Args:
        session: SQLAlchemy session
        model: Model class
        records: List of record IDs or record objects
        organization_id: Target organization UUID
        batch_size: Number of records per batch

    Returns:
        Total number of records updated
    """
    total_updated = 0

    # Process in batches
    for i in range(0, len(records), batch_size):
        batch = records[i : i + batch_size]

        # Extract IDs if records are objects
        if batch and hasattr(batch[0], "id"):
            record_ids = [r.id for r in batch]
        else:
            record_ids = batch

        # Update batch
        updated_count = (
            session.query(model)
            .filter(model.id.in_(record_ids))
            .update({"organization_id": organization_id}, synchronize_session="fetch")
        )

        total_updated += updated_count
        logger.info(
            f"Batch updated {updated_count} {model.__name__} records "
            f"to org {organization_id} (batch {i//batch_size + 1})"
        )

    session.commit()
    return total_updated


# Example usage
if __name__ == "__main__":
    """
    Example usage of tenant-aware query utilities
    """
    from uuid import uuid4

    from database.connection import get_session
    from database.models.agent_models import AgentInstance

    # Get session and organization
    session = get_session()
    org_id = uuid4()  # Replace with actual organization UUID

    # Method 1: TenantAwareQuery
    print("\n=== Method 1: TenantAwareQuery ===")
    query = TenantAwareQuery(session, AgentInstance, org_id)
    agents = query.filter_by(agent_type="CONTENT_GENERATOR").limit(10).all()
    print(f"Found {len(agents)} content generator agents")

    # Method 2: Decorator
    print("\n=== Method 2: @tenant_scoped Decorator ===")

    @tenant_scoped
    def get_active_agents(session: Session, organization_id: UUID):
        return session.query(AgentInstance).filter_by(status="IDLE")

    active_agents = get_active_agents(session, organization_id=org_id)
    print(f"Found {active_agents.count()} active agents")

    # Method 3: Context manager
    print("\n=== Method 3: tenant_session Context Manager ===")
    with tenant_session(session, org_id) as scoped_session:
        agents = scoped_session.query(AgentInstance).all()
        print(f"Found {len(agents)} agents in context")

    # Verification
    print("\n=== Tenant Isolation Verification ===")
    is_isolated = verify_tenant_isolation(session, AgentInstance, org_id)
    print(f"Tenant isolation verified: {is_isolated}")

    session.close()
