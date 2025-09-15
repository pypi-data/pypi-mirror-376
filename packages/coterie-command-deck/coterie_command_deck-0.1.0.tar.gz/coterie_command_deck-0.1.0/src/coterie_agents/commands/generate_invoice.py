"""Generate invoices for completed jobs with Stripe payment integration."""

from __future__ import annotations

import contextlib
import os

from ..services.payment_service import payment_service
from ._cli import has_unknown_flags, print_help, wants_help

COMMAND = "generate_invoice"
DESCRIPTION = "Generate invoices for completed jobs with payment links."
USAGE = f"{COMMAND} <job_id> [--customer <name>] [--email <email>] [--amount <amount>] [--help]"


def _parse_invoice_args(
    argv: list[str],
) -> tuple[str | None, str | None, str | None, float | None]:
    """Parse job_id, customer, email, and amount from argv."""
    if not argv:
        return None, None, None, None

    job_id = argv[0]
    customer = None
    email = None
    amount = None

    i = 1
    while i < len(argv):
        if argv[i] == "--customer" and i + 1 < len(argv):
            customer = argv[i + 1]
            i += 2
        elif argv[i] == "--email" and i + 1 < len(argv):
            email = argv[i + 1]
            i += 2
        elif argv[i] == "--amount" and i + 1 < len(argv):
            with contextlib.suppress(ValueError):
                amount = float(argv[i + 1])
            i += 2
        else:
            i += 1

    return job_id, customer, email, amount


def run(argv: list[str] | None = None, _ctx: object = None) -> int:
    """CLI entrypoint for generate_invoice command."""
    argv = argv or []
    known_flags = {"--help", "-h", "--customer", "--email", "--amount"}

    if wants_help(argv):
        print_help(COMMAND, DESCRIPTION, USAGE)
        print("\nExamples:")
        print(
            f"  {COMMAND} JOB001 --customer 'John Smith' --email john@example.com --amount 250.00"
        )
        print(f"  {COMMAND} JOB002 --customer 'ABC Corp' --amount 150.00")
        print(f"  {COMMAND} JOB003 --email client@company.com")
        print("\nFeatures:")
        print("  • Creates Stripe payment links automatically")
        print("  • Stores invoice records with payment tracking")
        print("  • Supports test mode and live payments")
        print("\nNOTE: Runs in DRY-RUN mode unless PAYMENTS_ENABLED=true")
        return 0

    if has_unknown_flags(argv, known_flags):
        print("Not found")
        print_help(COMMAND, DESCRIPTION, USAGE)
        return 0

    job_id, customer, email, amount = _parse_invoice_args(argv)

    if not job_id:
        print("[ERROR] Job ID is required")
        print_help(COMMAND, DESCRIPTION, USAGE)
        return 1

    # Validate amount if provided
    if len(argv) > 1:
        for i, arg in enumerate(argv):
            if arg == "--amount" and i + 1 < len(argv):
                try:
                    amount = float(argv[i + 1])
                    if amount <= 0:
                        print("[ERROR] Amount must be greater than 0")
                        return 1
                except ValueError:
                    print(f"[ERROR] Invalid amount: {argv[i + 1]}")
                    return 1

    # Use default amount if not provided
    if amount is None:
        amount = 200.00  # Default service amount
        print(f"[INFO] Using default amount: ${amount:.2f}")

    # Check if payments are enabled
    payments_enabled = os.getenv("PAYMENTS_ENABLED", "false").lower() == "true"

    if not payments_enabled:
        print("[DRY-RUN] Would generate invoice:")
        print(f"  Job ID: {job_id}")
        print(f"  Amount: ${amount:.2f}")
        if customer:
            print(f"  Customer: {customer}")
        if email:
            print(f"  Email to: {email}")
        print("  (Set PAYMENTS_ENABLED=true to generate real invoices)")
        return 0

    # Generate invoice with payment integration
    try:
        result = payment_service.create_invoice_with_payment(
            job_id=job_id,
            amount=amount,
            customer_name=customer,
            customer_email=email,
            description=f"Services for job {job_id}",
        )

        if result["success"]:
            print(f"[✅] Invoice generated: {result['invoice_id']}")
            print(f"[📄] Invoice file: {result['invoice_file']}")

            if result["payment_success"]:
                print(f"[💳] Payment link: {result['payment_link']}")
                print("[💡] Customer can pay via the link above")
            else:
                print(f"[⚠️] Payment link creation: {result['payment_message']}")

            if email:
                print(f"[📧] Send payment link to: {email}")

            # Show invoice summary
            print("\n📋 INVOICE SUMMARY")
            print(f"   Job ID: {job_id}")
            print(f"   Amount: ${amount:.2f}")
            if customer:
                print(f"   Customer: {customer}")
            if email:
                print(f"   Email: {email}")

            return 0
        else:
            print(f"[❌] Invoice generation failed: {result.get('error', 'Unknown error')}")
            return 1

    except Exception as e:
        print(f"[❌] Invoice generation failed: {e}")
        return 1


def _generate_invoice(job_id: str, customer: str | None, email: str | None) -> str:
    """Legacy function - now integrated with payment service."""
    # This function is kept for backward compatibility but redirects to payment service
    result = payment_service.create_invoice_with_payment(
        job_id=job_id,
        amount=200.00,  # Default amount
        customer_name=customer,
        customer_email=email,
    )

    if result["success"]:
        return result["invoice_file"]
    else:
        raise RuntimeError(result.get("error", "Invoice generation failed"))
