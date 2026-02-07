"""
phi_engine.demo.payment — Stripe payment integration.

Pattern from sovereign-pio/docs/usecases/demos/stripe_payment.py.
Requires: stripe>=7.0, streamlit (optional dependency [demo])
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

try:
    import stripe
except ImportError:
    stripe = None  # type: ignore[assignment]

from .database import DemoDatabase


# ---------------------------------------------------------------------------
# Payment plans
# ---------------------------------------------------------------------------
class PaymentPlan(Enum):
    """Phi-Engine payment tiers."""

    FREE = ("free", "Free Tier", 0, "none")
    PRO_MONTHLY = ("pro_monthly", "Pro — Unlimited Transforms", 4900, "monthly")
    ENTERPRISE_MONTHLY = (
        "enterprise_monthly",
        "Enterprise — Custom Adapters",
        49900,
        "monthly",
    )

    def __init__(self, product_id: str, label: str, price_cents: int, billing: str):
        self.product_id = product_id
        self.label = label
        self.price_cents = price_cents
        self.billing = billing

    @property
    def price_usd(self) -> str:
        if self.price_cents == 0:
            return "Free"
        return f"${self.price_cents / 100:.2f}"


# Free-tier limits
FREE_TRANSFORMS_PER_DAY = 10
FREE_ANALYSES_PER_DAY = 3


@dataclass
class PaymentResult:
    success: bool
    checkout_url: str = ""
    session_id: str = ""
    error: str = ""


# ---------------------------------------------------------------------------
# Stripe payment class
# ---------------------------------------------------------------------------
class StripePayment:
    """Stripe Checkout integration for phi-engine demos."""

    def __init__(self) -> None:
        if stripe is None:
            raise ImportError("stripe package required: pip install stripe>=7.0")
        self.secret_key = os.environ.get("STRIPE_SECRET_KEY", "")
        self.publishable_key = os.environ.get("STRIPE_PUBLISHABLE_KEY", "")
        if self.secret_key:
            stripe.api_key = self.secret_key
        self.test_mode = self.secret_key.startswith("sk_test_")

    def create_checkout_session(
        self,
        plan: PaymentPlan,
        customer_email: str,
        success_url: str,
        cancel_url: str,
        session_id: str = "",
        metadata: dict | None = None,
    ) -> PaymentResult:
        """Create a Stripe Checkout session and log to database."""
        if not self.secret_key:
            return PaymentResult(success=False, error="STRIPE_SECRET_KEY not configured")

        meta = metadata or {}
        meta["session_id"] = session_id
        meta["plan_id"] = plan.product_id

        line_items: list[dict] = []
        price_data: dict = {
            "currency": "usd",
            "product_data": {"name": plan.label},
            "unit_amount": plan.price_cents,
        }
        if plan.billing == "monthly":
            price_data["recurring"] = {"interval": "month"}

        line_items.append({"price_data": price_data, "quantity": 1})

        mode = "subscription" if plan.billing == "monthly" else "payment"

        try:
            session = stripe.checkout.Session.create(
                line_items=line_items,
                mode=mode,
                success_url=success_url + "?session_id={CHECKOUT_SESSION_ID}",
                cancel_url=cancel_url,
                customer_email=customer_email,
                metadata=meta,
                expires_at=int(datetime.now().timestamp()) + 1800,
            )
        except Exception as exc:
            return PaymentResult(success=False, error=str(exc))

        # Log to database
        db = DemoDatabase()
        db.log_payment_initiated(
            session_id=session_id,
            stripe_session_id=session.id,
            customer_email=customer_email,
            plan_id=plan.product_id,
            plan_name=plan.label,
            amount_cents=plan.price_cents,
            billing_type=plan.billing,
            metadata=meta,
        )

        return PaymentResult(
            success=True,
            checkout_url=session.url,
            session_id=session.id,
        )

    def verify_payment(self, stripe_session_id: str) -> dict:
        """Verify a Stripe Checkout session was paid."""
        try:
            session = stripe.checkout.Session.retrieve(stripe_session_id)
            return {
                "paid": session.payment_status == "paid",
                "amount": session.amount_total,
                "currency": session.currency,
                "customer_email": getattr(
                    session.customer_details, "email", None
                ),
                "metadata": dict(session.metadata) if session.metadata else {},
            }
        except Exception as exc:
            return {"paid": False, "error": str(exc)}


# ---------------------------------------------------------------------------
# Rate-limit helpers
# ---------------------------------------------------------------------------
def check_rate_limit(
    email: str,
    action: str = "transform",
    has_paid: bool = False,
) -> dict:
    """Check if user can perform action under free-tier limits.

    Returns: {"allowed": bool, "remaining": int, "limit": int}
    """
    if has_paid:
        return {"allowed": True, "remaining": 999999, "limit": 999999}

    db = DemoDatabase()
    user = db.get_or_create_user(email)

    if action == "transform":
        used = user.get("transforms_today", 0)
        limit = FREE_TRANSFORMS_PER_DAY
    else:
        used = user.get("analyses_today", 0)
        limit = FREE_ANALYSES_PER_DAY

    return {
        "allowed": used < limit,
        "remaining": max(0, limit - used),
        "limit": limit,
    }
