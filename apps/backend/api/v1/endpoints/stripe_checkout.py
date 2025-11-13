"""
Stripe Checkout Session endpoints (hosted Checkout)

Creates a Checkout session to keep PCI scope at SAQ A. Do not handle card data in the app.
"""

from __future__ import annotations

import logging
import os
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/v1/payments/stripe", tags=["Payments"])

logger = logging.getLogger(__name__)

try:
    import stripe  # type: ignore

    STRIPE_AVAILABLE = True
except Exception:  # pragma: no cover
    STRIPE_AVAILABLE = False


class CheckoutSessionRequest(BaseModel):
    price_id: str = Field(..., description="Stripe Price ID")
    quantity: int = Field(1, ge=1)
    mode: str = Field("payment", description="payment or subscription")
    success_url: str = Field(...)
    cancel_url: str = Field(...)


@router.post("/checkout-session")
async def create_checkout_session(payload: CheckoutSessionRequest) -> dict[str, Any]:
    if not STRIPE_AVAILABLE:
        raise HTTPException(status_code=503, detail="Stripe SDK not available")

    secret_key = os.getenv("STRIPE_SECRET_KEY", "").strip()
    if not secret_key:
        raise HTTPException(status_code=503, detail="Stripe not configured")

    stripe.api_key = secret_key

    try:
        session = stripe.checkout.Session.create(
            mode=payload.mode,
            line_items=[
                {
                    "price": payload.price_id,
                    "quantity": payload.quantity,
                }
            ],
            success_url=payload.success_url,
            cancel_url=payload.cancel_url,
            allow_promotion_codes=True,
            automatic_tax={"enabled": True},
        )
        # Return only necessary fields
        return {"id": session.get("id"), "url": session.get("url")}
    except Exception as e:
        logger.error(f"Stripe checkout creation failed: {e}")
        raise HTTPException(status_code=400, detail="Failed to create checkout session")
