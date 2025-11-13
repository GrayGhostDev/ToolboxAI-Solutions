"""
User Repository with SQLAlchemy 2.0 (2025 Standards)

Provides user-specific database operations with:
- Authentication helpers
- Profile management
- Session tracking
- Caching support

Reference: https://docs.sqlalchemy.org/en/20/
"""

from datetime import datetime, timedelta
from typing import List, Optional
from uuid import UUID

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from database.cache_modern import cache_result, invalidate_cache
from database.models.user_modern import User, UserProfile, UserRole, UserSession, UserStatus
from database.repositories.base_repository import BaseRepository


class UserRepository(BaseRepository[User]):
    """
    Repository for User model operations.

    Extends base repository with user-specific functionality.
    """

    def __init__(self):
        """Initialize user repository."""
        super().__init__(User)

    @cache_result(prefix="user:email", expire=300)
    async def get_by_email(
        self,
        session: AsyncSession,
        email: str,
        organization_id: UUID,
    ) -> Optional[User]:
        """
        Get user by email within organization.

        Args:
            session: Async database session
            email: User email address
            organization_id: Organization UUID

        Returns:
            User instance or None if not found
        """
        stmt = (
            select(User)
            .where(
                and_(
                    User.email == email.lower(),
                    User.organization_id == organization_id,
                    User.deleted_at.is_(None),
                )
            )
            .options(selectinload(User.profile))
        )

        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    @cache_result(prefix="user:username", expire=300)
    async def get_by_username(
        self,
        session: AsyncSession,
        username: str,
        organization_id: UUID,
    ) -> Optional[User]:
        """
        Get user by username within organization.

        Args:
            session: Async database session
            username: Username
            organization_id: Organization UUID

        Returns:
            User instance or None if not found
        """
        stmt = (
            select(User)
            .where(
                and_(
                    User.username == username,
                    User.organization_id == organization_id,
                    User.deleted_at.is_(None),
                )
            )
            .options(selectinload(User.profile))
        )

        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_active_users(
        self,
        session: AsyncSession,
        organization_id: UUID,
        role: Optional[UserRole] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[User]:
        """
        Get active users, optionally filtered by role.

        Args:
            session: Async database session
            organization_id: Organization UUID
            role: Optional role filter
            skip: Pagination offset
            limit: Maximum results

        Returns:
            List of active users
        """
        stmt = (
            select(User)
            .where(
                and_(
                    User.organization_id == organization_id,
                    User.status == UserStatus.ACTIVE,
                    User.deleted_at.is_(None),
                )
            )
            .offset(skip)
            .limit(limit)
        )

        if role is not None:
            stmt = stmt.where(User.role == role)

        result = await session.execute(stmt)
        return list(result.scalars().all())

    @invalidate_cache(prefix="user")
    async def create_user_with_profile(
        self,
        session: AsyncSession,
        organization_id: UUID,
        email: str,
        username: str,
        hashed_password: str,
        full_name: Optional[str] = None,
        role: UserRole = UserRole.STUDENT,
        **profile_data,
    ) -> User:
        """
        Create user with profile in single transaction.

        Args:
            session: Async database session
            organization_id: Organization UUID
            email: User email
            username: Username
            hashed_password: Pre-hashed password
            full_name: Full name
            role: User role
            **profile_data: Additional profile fields

        Returns:
            Created user with profile
        """
        # Create user
        user = User(
            organization_id=organization_id,
            email=email.lower(),
            username=username,
            hashed_password=hashed_password,
            full_name=full_name,
            role=role,
            status=UserStatus.PENDING,
        )

        session.add(user)
        await session.flush()

        # Create profile
        profile = UserProfile(
            organization_id=organization_id,
            user_id=user.id,
            **profile_data,
        )

        session.add(profile)
        await session.flush()

        # Refresh to get relationships
        await session.refresh(user, ["profile"])

        return user

    async def verify_email(
        self,
        session: AsyncSession,
        user_id: UUID,
    ) -> bool:
        """
        Verify user email and activate account.

        Args:
            session: Async database session
            user_id: User UUID

        Returns:
            True if successful, False if user not found
        """
        user = await self.get_by_id(session, user_id)
        if user is None:
            return False

        user.verify_email()
        user.status = UserStatus.ACTIVE

        await session.flush()
        return True

    async def record_login(
        self,
        session: AsyncSession,
        user_id: UUID,
        ip_address: str,
        user_agent: str,
        token_jti: str,
        expires_at: datetime,
    ) -> Optional[UserSession]:
        """
        Record successful login and create session.

        Args:
            session: Async database session
            user_id: User UUID
            ip_address: Client IP address
            user_agent: Client user agent
            token_jti: JWT token ID
            expires_at: Token expiration time

        Returns:
            Created session or None if user not found
        """
        user = await self.get_by_id(session, user_id)
        if user is None:
            return None

        # Update user login tracking
        user.record_login(ip_address)

        # Create session
        user_session = UserSession(
            organization_id=user.organization_id,
            user_id=user_id,
            token_jti=token_jti,
            ip_address=ip_address,
            user_agent=user_agent,
            expires_at=expires_at,
        )

        session.add(user_session)
        await session.flush()

        return user_session

    async def record_failed_login(
        self,
        session: AsyncSession,
        user_id: UUID,
    ) -> bool:
        """
        Record failed login attempt.

        Args:
            session: Async database session
            user_id: User UUID

        Returns:
            True if account is now locked, False otherwise
        """
        user = await self.get_by_id(session, user_id)
        if user is None:
            return False

        is_locked = user.record_failed_login()
        await session.flush()

        return is_locked

    async def get_active_sessions(
        self,
        session: AsyncSession,
        user_id: UUID,
    ) -> List[UserSession]:
        """
        Get all active sessions for user.

        Args:
            session: Async database session
            user_id: User UUID

        Returns:
            List of active sessions
        """
        stmt = (
            select(UserSession)
            .where(
                and_(
                    UserSession.user_id == user_id,
                    UserSession.is_active == True,
                    UserSession.expires_at > datetime.utcnow(),
                    UserSession.deleted_at.is_(None),
                )
            )
            .order_by(UserSession.created_at.desc())
        )

        result = await session.execute(stmt)
        return list(result.scalars().all())

    async def invalidate_user_sessions(
        self,
        session: AsyncSession,
        user_id: UUID,
    ) -> int:
        """
        Invalidate all active sessions for user.

        Args:
            session: Async database session
            user_id: User UUID

        Returns:
            Number of sessions invalidated
        """
        sessions = await self.get_active_sessions(session, user_id)

        for sess in sessions:
            sess.invalidate()

        await session.flush()
        return len(sessions)

    async def cleanup_expired_sessions(
        self,
        session: AsyncSession,
        before_date: Optional[datetime] = None,
    ) -> int:
        """
        Cleanup expired sessions.

        Args:
            session: Async database session
            before_date: Delete sessions expired before this date
                        Defaults to now

        Returns:
            Number of sessions deleted
        """
        if before_date is None:
            before_date = datetime.utcnow()

        stmt = select(UserSession).where(
            and_(
                UserSession.expires_at < before_date,
                UserSession.deleted_at.is_(None),
            )
        )

        result = await session.execute(stmt)
        sessions = result.scalars().all()

        for sess in sessions:
            sess.soft_delete()

        await session.flush()
        return len(sessions)

    async def get_user_statistics(
        self,
        session: AsyncSession,
        organization_id: UUID,
    ) -> dict:
        """
        Get user statistics for organization.

        Args:
            session: Async database session
            organization_id: Organization UUID

        Returns:
            Dictionary with user statistics
        """
        # Total users
        total_stmt = (
            select(func.count())
            .select_from(User)
            .where(
                and_(
                    User.organization_id == organization_id,
                    User.deleted_at.is_(None),
                )
            )
        )
        total_result = await session.execute(total_stmt)
        total_users = total_result.scalar_one()

        # Active users
        active_stmt = (
            select(func.count())
            .select_from(User)
            .where(
                and_(
                    User.organization_id == organization_id,
                    User.status == UserStatus.ACTIVE,
                    User.deleted_at.is_(None),
                )
            )
        )
        active_result = await session.execute(active_stmt)
        active_users = active_result.scalar_one()

        # Users by role
        role_stmt = (
            select(User.role, func.count())
            .where(
                and_(
                    User.organization_id == organization_id,
                    User.deleted_at.is_(None),
                )
            )
            .group_by(User.role)
        )
        role_result = await session.execute(role_stmt)
        users_by_role = {role.value: count for role, count in role_result.all()}

        # Recent signups (last 30 days)
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        recent_stmt = (
            select(func.count())
            .select_from(User)
            .where(
                and_(
                    User.organization_id == organization_id,
                    User.created_at >= thirty_days_ago,
                    User.deleted_at.is_(None),
                )
            )
        )
        recent_result = await session.execute(recent_stmt)
        recent_signups = recent_result.scalar_one()

        return {
            "total_users": total_users,
            "active_users": active_users,
            "users_by_role": users_by_role,
            "recent_signups_30d": recent_signups,
        }


# Export repository
__all__ = ["UserRepository"]
