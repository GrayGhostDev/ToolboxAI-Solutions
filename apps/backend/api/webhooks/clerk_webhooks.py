"""
Clerk Webhook Handler for ToolboxAI (2025)
Handles user lifecycle events from Clerk
"""

import os
import logging
import hashlib
import hmac
from typing import Dict, Any
from datetime import datetime
from fastapi import APIRouter, Request, HTTPException, status
from pydantic import BaseModel

logger = logging.getLogger(__name__)

# Clerk webhook signing secret
WEBHOOK_SECRET = os.getenv("CLERK_WEBHOOK_SIGNING_SECRET", "whsec_yfJVjj0muO9lOYGyOEMH3cbVBXS7Znct")

router = APIRouter(
    prefix="/api/webhooks/clerk",
    tags=["webhooks"],
)


class ClerkWebhookEvent(BaseModel):
    """Clerk webhook event model"""

    data: Dict[str, Any]
    object: str
    type: str
    timestamp: int


def verify_webhook_signature(payload: bytes, signature: str, secret: str) -> bool:
    """
    Verify Clerk webhook signature using HMAC

    Args:
        payload: Raw request body
        signature: Signature from headers
        secret: Webhook signing secret

    Returns:
        True if signature is valid
    """
    try:
        # Clerk uses SHA256 HMAC
        expected_sig = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()

        # Compare signatures
        return hmac.compare_digest(expected_sig, signature.replace("sha256=", ""))
    except Exception as e:
        logger.error(f"Signature verification failed: {e}")
        return False


@router.post("")
async def handle_clerk_webhook(request: Request):
    """
    Handle Clerk webhook events

    Supported events:
    - user.created: New user registered
    - user.updated: User profile updated
    - user.deleted: User account deleted
    - session.created: User logged in
    - session.ended: User logged out
    - organization.created: New organization
    - organization.member.created: User joined organization
    """
    try:
        # Get raw body and signature
        body = await request.body()
        signature = request.headers.get("svix-signature", "")

        # Verify signature
        if not verify_webhook_signature(body, signature, WEBHOOK_SECRET):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid webhook signature"
            )

        # Parse event
        event_data = await request.json()
        event = ClerkWebhookEvent(**event_data)

        logger.info(f"Received Clerk webhook: {event.type}")

        # Handle different event types
        if event.type == "user.created":
            await handle_user_created(event.data)

        elif event.type == "user.updated":
            await handle_user_updated(event.data)

        elif event.type == "user.deleted":
            await handle_user_deleted(event.data)

        elif event.type == "session.created":
            await handle_session_created(event.data)

        elif event.type == "session.ended":
            await handle_session_ended(event.data)

        elif event.type == "organization.created":
            await handle_organization_created(event.data)

        elif event.type == "organization.member.created":
            await handle_organization_member_created(event.data)

        else:
            logger.info(f"Unhandled event type: {event.type}")

        return {"status": "success", "message": f"Processed {event.type}"}

    except Exception as e:
        logger.error(f"Webhook processing failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Webhook processing failed"
        )


async def handle_user_created(user_data: Dict[str, Any]):
    """
    Handle new user creation from Clerk

    Args:
        user_data: User data from Clerk
    """
    try:
        from database.models import User
        from database.connection import get_async_session
        from sqlalchemy import select
        from sqlalchemy.exc import IntegrityError

        user_id = user_data.get("id")
        if not user_id:
            logger.error("Missing user ID in webhook data")
            return

        email_addresses = user_data.get("email_addresses", [])
        email = email_addresses[0].get("email_address") if email_addresses else None

        if not email:
            logger.error(f"Missing email for user {user_id}")
            return

        username = user_data.get("username") or user_data.get("first_name", "User")

        # Extract role from public metadata with validation
        public_metadata = user_data.get("public_metadata", {})
        role = public_metadata.get("role", "student")

        # Validate role against allowed values
        allowed_roles = ["student", "teacher", "admin", "parent"]
        if role not in allowed_roles:
            logger.warning(f"Invalid role '{role}' for user {user_id}, defaulting to 'student'")
            role = "student"

        # Create user in local database using async session and ORM
        async with get_async_session() as session:
            # Check if user already exists using parameterized query
            stmt = select(User).where(User.clerk_id == user_id)
            result = await session.execute(stmt)
            existing_user = result.scalar_one_or_none()

            if existing_user:
                logger.info(f"User {user_id} already exists")
                return

            # Parse email verification status safely
            email_verified = False
            if email_addresses:
                verification = email_addresses[0].get("verification", {})
                email_verified = verification.get("status") == "verified"

            # Parse created_at timestamp safely
            created_at = None
            if user_data.get("created_at"):
                try:
                    created_at = datetime.fromisoformat(
                        user_data.get("created_at").replace("Z", "+00:00")
                    )
                except (ValueError, AttributeError) as e:
                    logger.warning(f"Failed to parse created_at: {e}")
                    created_at = datetime.utcnow()
            else:
                created_at = datetime.utcnow()

            # Create new user with validated data
            new_user = User(
                clerk_id=user_id,
                email=email,
                username=username,
                role=role,
                first_name=user_data.get("first_name", ""),
                last_name=user_data.get("last_name", ""),
                avatar=user_data.get("image_url", ""),
                is_active=True,
                email_verified=email_verified,
                created_at=created_at,
            )

            session.add(new_user)

            try:
                await session.commit()
                logger.info(f"Successfully created user {user_id} in local database")
            except IntegrityError as ie:
                await session.rollback()
                logger.error(f"Database integrity error creating user {user_id}: {ie}")
                raise

    except Exception as e:
        logger.error(f"Failed to create user: {e}", exc_info=True)
        raise


async def handle_user_updated(user_data: Dict[str, Any]):
    """
    Handle user update from Clerk

    Args:
        user_data: Updated user data from Clerk
    """
    try:
        from database.models import User
        from database.connection import get_async_session
        from sqlalchemy import select, update
        from datetime import datetime

        user_id = user_data.get("id")
        if not user_id:
            logger.error("Missing user ID in webhook data")
            return

        # Extract and validate data
        email_addresses = user_data.get("email_addresses", [])
        email = email_addresses[0].get("email_address") if email_addresses else None

        username = user_data.get("username", "")
        first_name = user_data.get("first_name", "")
        last_name = user_data.get("last_name", "")
        avatar = user_data.get("image_url", "")

        # Extract and validate role
        public_metadata = user_data.get("public_metadata", {})
        role = public_metadata.get("role", "student")

        # Validate role against allowed values
        allowed_roles = ["student", "teacher", "admin", "parent"]
        if role not in allowed_roles:
            logger.warning(f"Invalid role '{role}' for user {user_id}, keeping existing role")
            role = None  # Don't update if invalid

        async with get_async_session() as session:
            # Find user using parameterized query
            stmt = select(User).where(User.clerk_id == user_id)
            result = await session.execute(stmt)
            user = result.scalar_one_or_none()

            if not user:
                logger.warning(f"User {user_id} not found for update")
                return

            # Update user fields
            if email:
                user.email = email
            if username:
                user.username = username
            if first_name:
                user.first_name = first_name
            if last_name:
                user.last_name = last_name
            if avatar:
                user.avatar = avatar
            if role:
                user.role = role

            user.updated_at = datetime.utcnow()

            try:
                await session.commit()
                logger.info(f"Successfully updated user {user_id} in local database")
            except Exception as e:
                await session.rollback()
                logger.error(f"Database error updating user {user_id}: {e}")
                raise

    except Exception as e:
        logger.error(f"Failed to update user: {e}", exc_info=True)
        raise


async def handle_user_deleted(user_data: Dict[str, Any]):
    """
    Handle user deletion from Clerk

    Args:
        user_data: Deleted user data from Clerk
    """
    try:
        from database.models import User
        from database.connection import get_async_session
        from sqlalchemy import select
        from datetime import datetime

        user_id = user_data.get("id")
        if not user_id:
            logger.error("Missing user ID in webhook data")
            return

        async with get_async_session() as session:
            # Find user using parameterized query
            stmt = select(User).where(User.clerk_id == user_id)
            result = await session.execute(stmt)
            user = result.scalar_one_or_none()

            if not user:
                logger.warning(f"User {user_id} not found for deletion")
                return

            # Soft delete user
            user.is_active = False
            user.deleted_at = datetime.utcnow()

            try:
                await session.commit()
                logger.info(f"Successfully soft deleted user {user_id} in local database")
            except Exception as e:
                await session.rollback()
                logger.error(f"Database error deleting user {user_id}: {e}")
                raise

    except Exception as e:
        logger.error(f"Failed to delete user: {e}", exc_info=True)
        raise


async def handle_session_created(session_data: Dict[str, Any]):
    """
    Handle new session creation (user login)

    Args:
        session_data: Session data from Clerk
    """
    try:
        from database.models import User
        from database.connection import get_async_session
        from sqlalchemy import select
        from datetime import datetime

        user_id = session_data.get("user_id")
        session_id = session_data.get("id")

        if not user_id:
            logger.error("Missing user ID in session data")
            return

        logger.info(f"User {user_id} logged in with session {session_id}")

        # Update last_login timestamp in database
        async with get_async_session() as session:
            # Find user using parameterized query
            stmt = select(User).where(User.clerk_id == user_id)
            result = await session.execute(stmt)
            user = result.scalar_one_or_none()

            if user:
                user.last_login = datetime.utcnow()
                try:
                    await session.commit()
                    logger.info(f"Updated last_login for user {user_id}")
                except Exception as e:
                    await session.rollback()
                    logger.error(f"Failed to update last_login: {e}")
            else:
                logger.warning(f"User {user_id} not found when updating last_login")

    except Exception as e:
        logger.error(f"Failed to handle session creation: {e}", exc_info=True)


async def handle_session_ended(session_data: Dict[str, Any]):
    """
    Handle session end (user logout)

    Args:
        session_data: Session data from Clerk
    """
    try:
        user_id = session_data.get("user_id")
        session_id = session_data.get("id")

        # Log session end
        logger.info(f"User {user_id} logged out from session {session_id}")

    except Exception as e:
        logger.error(f"Failed to handle session end: {e}")


async def handle_organization_created(org_data: Dict[str, Any]):
    """
    Handle new organization creation

    Args:
        org_data: Organization data from Clerk
    """
    try:
        org_id = org_data.get("id")
        org_name = org_data.get("name")

        logger.info(f"New organization created: {org_name} ({org_id})")

        # Could create organization in local database if needed

    except Exception as e:
        logger.error(f"Failed to handle organization creation: {e}")


async def handle_organization_member_created(member_data: Dict[str, Any]):
    """
    Handle user joining organization

    Args:
        member_data: Member data from Clerk
    """
    try:
        user_id = member_data.get("user_id")
        org_id = member_data.get("organization_id")
        role = member_data.get("role")

        logger.info(f"User {user_id} joined organization {org_id} as {role}")

        # Could update user's organization in local database

    except Exception as e:
        logger.error(f"Failed to handle organization member creation: {e}")
