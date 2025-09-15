"""Stripe payments integration (minimal, test-mode, optional)."""

import os
from pathlib import Path

STRIPE_ENABLED = os.getenv("PAYMENTS_ENABLED", "false").lower() == "true" and os.getenv(
    "STRIPE_API_KEY"
)
INVOICE_DIR = Path("invoices")
INVOICE_DIR.mkdir(exist_ok=True)


class PaymentResult:
    def __init__(self, success: bool, url: str = "", message: str = ""):
        self.success = success
        self.url = url
        self.message = message


def create_payment_link(client: str, amount: float, memo: str) -> PaymentResult:
    if not STRIPE_ENABLED:
        msg = "[DRY-RUN] Payment link not generated. Enable PAYMENTS_ENABLED and STRIPE_API_KEY."
        print(msg)
        return PaymentResult(False, "", msg)
    try:
        import stripe

        stripe.api_key = os.getenv("STRIPE_API_KEY")
        link = stripe.PaymentLink.create(
            line_items=[
                {
                    "price_data": {
                        "currency": "usd",
                        "product_data": {"name": client},
                        "unit_amount": int(amount * 100),
                    },
                    "quantity": 1,
                }
            ],
            after_completion={
                "type": "redirect",
                "redirect": {"url": "https://example.com/thanks"},
            },
            metadata={"memo": memo},
        )
        url = link.url
        fname = INVOICE_DIR / f"{client.replace(' ', '_')}_{amount:.2f}.txt"
        fname.write_text(f"Payment Link: {url}\nMemo: {memo}\n")
        print(f"Payment link generated: {url}")
        return PaymentResult(True, url, "Payment link generated.")
    except Exception as e:
        print(f"Payment link failed: {e}")
        return PaymentResult(False, "", f"Payment link failed: {e}")
