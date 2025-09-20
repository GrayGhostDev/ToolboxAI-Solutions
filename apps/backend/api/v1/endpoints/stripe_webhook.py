"""
Stripe Webhook Endpoint

- Verifies Stripe signatures using STRIPE_WEBHOOK_SECRET
- Processes minimal events (checkout.session.completed) as a placeholder
- Logs securely without exposing PII

Enable by setting STRIPE_WEBHOOK_SECRET and adding this route to the app.
"""
from __future__ import annotations

import json
import logging
import os
from typing import Any, Dict

from fastapi import APIRouter, Header, HTTPException, Request, status

router = APIRouter(prefix="/api/v1/payments/stripe", tags=["Payments"])

logger = logging.getLogger(__name__)

try:
    import stripe  # type: ignore
    STRIPE_AVAILABLE = True
except Exception:  # pragma: no cover
    STRIPE_AVAILABLE = False


@router.post("/webhook", status_code=status.HTTP_200_OK)
async def stripe_webhook(
    request: Request,
    stripe_signature: str | None = Header(None, alias="Stripe-Signature"),
) -> Dict[str, Any]:
    if not STRIPE_AVAILABLE:
        raise HTTPException(status_code=503, detail="Stripe SDK not available")

    webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET", "").strip()
    if not webhook_secret:
        raise HTTPException(status_code=503, detail="Stripe webhook not configured")

    if not stripe_signature:
        raise HTTPException(status_code=400, detail="Missing Stripe-Signature header")

    payload = await request.body()

    try:
        event = stripe.Webhook.construct_event(
            payload=payload,
            sig_header=stripe_signature,
            secret=webhook_secret,
        )
    except stripe.error.SignatureVerificationError:
        logger.warning("Stripe signature verification failed")
        raise HTTPException(status_code=400, detail="Invalid signature")
    except Exception as e:
        logger.error(f"Stripe webhook error: {e}")
        raise HTTPException(status_code=400, detail="Invalid payload")

    # Minimal event handling (expand as needed)
    event_type = event.get("type")

    if event_type == "checkout.session.completed":
        # Avoid logging raw PII
        session_id = event.get("data", {}).get("object", {}).get("id")
        logger.info(
            "Stripe checkout completed",
            extra={"event_type": event_type, "session_id": session_id},
        )
        # TODO: fulfill order / update license / provision service

    else:
        logger.info("Stripe event received", extra={"event_type": event_type})

    return {"received": True}
