"""Stripe payment integration (test mode by default)."""

import os
from typing import Any

STRIPE_ENABLED = (
    os.getenv("PAYMENTS_ENABLED", "false").lower() == "true"
    and os.getenv("STRIPE_SECRET_KEY")
    and os.getenv("STRIPE_PUBLISHABLE_KEY")
)

STRIPE_TEST_MODE = os.getenv("STRIPE_TEST_MODE", "true").lower() == "true"


class PaymentResult:
    """Result of a payment operation."""

    def __init__(self, success: bool, message: str, data: dict[str, Any] | None = None):
        self.success = success
        self.message = message
        self.data = data or {}


def create_payment_link(
    amount: float,
    description: str,
    invoice_id: str,
    customer_email: str | None = None,
) -> PaymentResult:
    """Create a Stripe payment link for an invoice."""

    if not STRIPE_ENABLED:
        link_url = f"https://example.com/payment/dry-run/{invoice_id}"
        print("[DRY-RUN] Payment link not created. Enable PAYMENTS_ENABLED and STRIPE_* envs.")
        print(f"[DRY-RUN] Would create payment link: {link_url}")
        print(f"[DRY-RUN] Amount: ${amount:.2f}, Description: {description}")

        return PaymentResult(
            success=False,
            message="[DRY-RUN] Payment link not created. Enable PAYMENTS_ENABLED and STRIPE_* envs.",
            data={"url": link_url, "test_mode": True},
        )

    try:
        import stripe

        stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

        # Convert amount to cents (Stripe expects integer cents)
        amount_cents = int(amount * 100)

        # Create payment link
        payment_link = stripe.PaymentLink.create(
            line_items=[
                {
                    "price_data": {
                        "currency": "usd",
                        "product_data": {
                            "name": f"Invoice {invoice_id}",
                            "description": description,
                        },
                        "unit_amount": amount_cents,
                    },
                    "quantity": 1,
                }
            ],
            metadata={
                "invoice_id": invoice_id,
                "test_mode": str(STRIPE_TEST_MODE),
            },
            customer_creation="if_required" if customer_email else "always",
            **({"invoice_creation": {"enabled": True}} if customer_email else {}),
        )

        mode_indicator = " (TEST MODE)" if STRIPE_TEST_MODE else " (LIVE MODE)"
        print(f"✅ Payment link created: {payment_link.url}{mode_indicator}")

        return PaymentResult(
            success=True,
            message=f"Payment link created successfully{mode_indicator}",
            data={
                "url": payment_link.url,
                "id": payment_link.id,
                "amount": amount,
                "test_mode": STRIPE_TEST_MODE,
            },
        )

    except ImportError:
        return PaymentResult(
            success=False,
            message="Stripe library not installed. Install with: pip install stripe",
        )
    except Exception as e:
        return PaymentResult(
            success=False,
            message=f"Payment link creation failed: {e}",
        )


def get_payment_status(payment_link_id: str) -> PaymentResult:
    """Get the status of a payment link."""

    if not STRIPE_ENABLED:
        print("[DRY-RUN] Cannot check payment status. Enable PAYMENTS_ENABLED and STRIPE_* envs.")
        return PaymentResult(
            success=False,
            message="[DRY-RUN] Cannot check payment status",
            data={"status": "dry_run"},
        )

    try:
        import stripe

        stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

        payment_link = stripe.PaymentLink.retrieve(payment_link_id)

        return PaymentResult(
            success=True,
            message="Payment link status retrieved",
            data={
                "id": payment_link.id,
                "url": payment_link.url,
                "active": payment_link.active,
                "test_mode": STRIPE_TEST_MODE,
            },
        )

    except ImportError:
        return PaymentResult(
            success=False,
            message="Stripe library not installed",
        )
    except Exception as e:
        return PaymentResult(
            success=False,
            message=f"Failed to get payment status: {e}",
        )


def store_payment_link(invoice_id: str, payment_data: dict[str, Any]) -> bool:
    """Store payment link data to invoices directory."""

    import json
    from pathlib import Path

    try:
        # Create invoices directory if it doesn't exist
        invoices_dir = Path("invoices")
        invoices_dir.mkdir(exist_ok=True)

        # Store payment link data
        invoice_file = invoices_dir / f"{invoice_id}_payment.json"

        payment_record = {
            "invoice_id": invoice_id,
            "created_at": payment_data.get("created_at"),
            "payment_link": {
                "id": payment_data.get("id"),
                "url": payment_data.get("url"),
                "amount": payment_data.get("amount"),
                "test_mode": payment_data.get("test_mode", STRIPE_TEST_MODE),
            },
            "metadata": payment_data.get("metadata", {}),
        }

        with open(invoice_file, "w") as f:
            json.dump(payment_record, f, indent=2)

        print(f"💾 Payment link stored: {invoice_file}")
        return True

    except Exception as e:
        print(f"❌ Failed to store payment link: {e}")
        return False
