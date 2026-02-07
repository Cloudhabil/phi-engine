"""
phi_engine.demo.webhook — Flask webhook server for Stripe events.

Pattern from sovereign-pio/docs/usecases/demos/stripe_webhook.py.
Runs on port 4242.
Requires: flask>=3.0, stripe>=7.0  (optional dependency [demo])
"""
from __future__ import annotations

import json
import os

try:
    import stripe
    from flask import Flask, jsonify, request
except ImportError:
    stripe = None  # type: ignore[assignment]
    Flask = None  # type: ignore[assignment,misc]

from .database import DemoDatabase

app = Flask(__name__) if Flask else None

WEBHOOK_SECRET = os.environ.get("STRIPE_WEBHOOK_SECRET", "")


def _get_db() -> DemoDatabase:
    return DemoDatabase()


if app is not None:

    @app.route("/health", methods=["GET"])
    def health():
        return jsonify({"status": "ok", "service": "phi-engine-webhook"})

    @app.route("/webhook", methods=["POST"])
    def stripe_webhook():
        """Receive and verify Stripe webhook events."""
        payload = request.data
        sig_header = request.headers.get("Stripe-Signature", "")

        # 1. Verify signature
        if WEBHOOK_SECRET:
            try:
                event = stripe.Webhook.construct_event(
                    payload, sig_header, WEBHOOK_SECRET
                )
            except ValueError:
                return jsonify({"error": "Invalid payload"}), 400
            except stripe.error.SignatureVerificationError:
                return jsonify({"error": "Invalid signature"}), 400
        else:
            # Local testing (no verification)
            event = json.loads(payload)

        event_type = event.get("type", "")
        db = _get_db()

        # 2. Checkout completed
        if event_type == "checkout.session.completed":
            session = event["data"]["object"]
            stripe_session_id = session.get("id", "")
            payment_status = session.get("payment_status", "")

            if payment_status == "paid":
                db.update_payment_status(stripe_session_id, "completed")

        # 3. Subscription renewed
        elif event_type == "invoice.payment_succeeded":
            pass  # Log renewal

        # 4. Subscription cancelled
        elif event_type == "customer.subscription.deleted":
            pass  # Revoke access

        return jsonify({"status": "success"}), 200


def main():
    """Run webhook server on port 4242."""
    if app is None:
        raise ImportError("flask required: pip install flask>=3.0")
    port = int(os.environ.get("WEBHOOK_PORT", "4242"))
    app.run(host="0.0.0.0", port=port)


if __name__ == "__main__":
    main()
