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


def verify_webhook_signature(
    payload: bytes,
    signature: str,
    secret: str
) -> bool:
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
        expected_sig = hmac.new(
            secret.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()

        # Compare signatures
        return hmac.compare_digest(
            expected_sig,
            signature.replace("sha256=", "")
        )
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
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid webhook signature"
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
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Webhook processing failed"
        )


async def handle_user_created(user_data: Dict[str, Any]):
    """
    Handle new user creation from Clerk

    Args:
        user_data: User data from Clerk
    """
    try:
        from database.models import User
        from database.connection import get_session

        user_id = user_data.get("id")
        email = user_data.get("email_addresses", [{}])[0].get("email_address")
        username = user_data.get("username") or user_data.get("first_name", "User")

        # Extract role from public metadata
        role = user_data.get("public_metadata", {}).get("role", "student")

        # Create user in local database
        async with get_session() as session:
            # Check if user already exists
            existing = await session.execute(
                f"SELECT id FROM users WHERE clerk_id = '{user_id}'"
            )
            if existing.scalar():
                logger.info(f"User {user_id} already exists")
                return

            # Create new user
            new_user = User(
                clerk_id=user_id,
                email=email,
                username=username,
                role=role,
                first_name=user_data.get("first_name", ""),
                last_name=user_data.get("last_name", ""),
                avatar=user_data.get("image_url", ""),
                is_active=True,
                email_verified=user_data.get("email_addresses", [{}])[0].get("verification", {}).get("status") == "verified",
                created_at=datetime.fromisoformat(user_data.get("created_at").replace("Z", "+00:00")),
            )

            session.add(new_user)
            await session.commit()

            logger.info(f"Created user {user_id} in local database")

    except Exception as e:
        logger.error(f"Failed to create user: {e}")
        raise


async def handle_user_updated(user_data: Dict[str, Any]):
    """
    Handle user update from Clerk

    Args:
        user_data: Updated user data from Clerk
    """
    try:
        from database.connection import get_session

        user_id = user_data.get("id")

        async with get_session() as session:
            # Update user in local database
            result = await session.execute(
                f"""
                UPDATE users
                SET
                    email = '{user_data.get("email_addresses", [{}])[0].get("email_address", "")}',
                    username = '{user_data.get("username", "")}',
                    first_name = '{user_data.get("first_name", "")}',
                    last_name = '{user_data.get("last_name", "")}',
                    avatar = '{user_data.get("image_url", "")}',
                    role = '{user_data.get("public_metadata", {}).get("role", "student")}',
                    updated_at = NOW()
                WHERE clerk_id = '{user_id}'
                """
            )
            await session.commit()

            logger.info(f"Updated user {user_id} in local database")

    except Exception as e:
        logger.error(f"Failed to update user: {e}")
        raise


async def handle_user_deleted(user_data: Dict[str, Any]):
    """
    Handle user deletion from Clerk

    Args:
        user_data: Deleted user data from Clerk
    """
    try:
        from database.connection import get_session

        user_id = user_data.get("id")

        async with get_session() as session:
            # Soft delete user in local database
            result = await session.execute(
                f"""
                UPDATE users
                SET is_active = FALSE, deleted_at = NOW()
                WHERE clerk_id = '{user_id}'
                """
            )
            await session.commit()

            logger.info(f"Soft deleted user {user_id} in local database")

    except Exception as e:
        logger.error(f"Failed to delete user: {e}")
        raise


async def handle_session_created(session_data: Dict[str, Any]):
    """
    Handle new session creation (user login)

    Args:
        session_data: Session data from Clerk
    """
    try:
        user_id = session_data.get("user_id")
        session_id = session_data.get("id")

        # Log session creation
        logger.info(f"User {user_id} logged in with session {session_id}")

        # Could update last_login timestamp in database
        from database.connection import get_session

        async with get_session() as session:
            await session.execute(
                f"""
                UPDATE users
                SET last_login = NOW()
                WHERE clerk_id = '{user_id}'
                """
            )
            await session.commit()

    except Exception as e:
        logger.error(f"Failed to handle session creation: {e}")


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