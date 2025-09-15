"""Process payments and invoicing with Stripe integration."""

from __future__ import annotations

import os

from ..services.payment_service import payment_service
from ._cli import has_unknown_flags, print_help, wants_help

COMMAND = "process_payment"
DESCRIPTION = "Process payments and generate invoices with Stripe integration."
USAGE = f"{COMMAND} <job_id> [--amount <amount>] [--method <card|cash|check>] [--customer <name>] [--email <email>] [--help]"


def run(argv: list[str] | None = None, _ctx: object = None) -> int:
    """CLI entrypoint for process_payment command."""
    argv = argv or []
    known_flags = {"--help", "-h", "--amount", "--method", "--customer", "--email"}

    if wants_help(argv):
        print_help(COMMAND, DESCRIPTION, USAGE)
        print("\nExamples:")
        print(f"  {COMMAND} JOB001 --amount 250.00 --method card --customer 'John Smith'")
        print(f"  {COMMAND} JOB002 --amount 150.00 --method cash")
        print(f"  {COMMAND} JOB003 --method card --email client@company.com")
        print("\nPayment Methods:")
        print("  • card: Creates Stripe payment link (default)")
        print("  • cash: Records cash payment")
        print("  • check: Records check payment")
        print("\nNOTE: Runs in DRY-RUN mode unless PAYMENTS_ENABLED=true")
        return 0

    if has_unknown_flags(argv, known_flags):
        print("Not found")
        print_help(COMMAND, DESCRIPTION, USAGE)
        return 0

    if not argv:
        print("[ERROR] Job ID is required")
        print_help(COMMAND, DESCRIPTION, USAGE)
        return 1

    job_id = argv[0]
    amount = None
    method = "card"  # default
    customer = None
    email = None

    # Parse flags
    i = 1
    while i < len(argv):
        if argv[i] == "--amount" and i + 1 < len(argv):
            try:
                amount = float(argv[i + 1])
                if amount <= 0:
                    print("[ERROR] Amount must be greater than 0")
                    return 1
            except ValueError:
                print(f"[ERROR] Invalid amount: {argv[i + 1]}")
                return 1
            i += 2
        elif argv[i] == "--method" and i + 1 < len(argv):
            method = argv[i + 1]
            i += 2
        elif argv[i] == "--customer" and i + 1 < len(argv):
            customer = argv[i + 1]
            i += 2
        elif argv[i] == "--email" and i + 1 < len(argv):
            email = argv[i + 1]
            i += 2
        else:
            i += 1

    if method not in {"card", "cash", "check"}:
        print(f"[ERROR] Unsupported payment method: {method}")
        print("Supported methods: card, cash, check")
        return 1

    # Use default amount if not provided
    if amount is None:
        amount = 200.00  # Default service amount
        print(f"[INFO] Using default amount: ${amount:.2f}")

    # Check if payments are enabled
    payments_enabled = os.getenv("PAYMENTS_ENABLED", "false").lower() == "true"

    if not payments_enabled:
        amount_str = f"${amount:.2f}"
        print("[DRY-RUN] Would process payment:")
        print(f"  Job ID: {job_id}")
        print(f"  Amount: {amount_str}")
        print(f"  Method: {method}")
        if customer:
            print(f"  Customer: {customer}")
        if email:
            print(f"  Email: {email}")
        print("  (Set PAYMENTS_ENABLED=true to process real payments)")
        return 0

    # Process payment based on method
    try:
        if method == "card":
            # Create invoice with Stripe payment link
            result = payment_service.create_invoice_with_payment(
                job_id=job_id,
                amount=amount,
                customer_name=customer,
                customer_email=email,
                description=f"Payment for job {job_id}",
            )

            if result["success"]:
                print(f"[✅] Payment invoice created: {result['invoice_id']}")

                if result["payment_success"]:
                    print(f"[💳] Payment link: {result['payment_link']}")
                    print("[💡] Share link with customer for payment")
                else:
                    print(f"[⚠️] Payment link: {result['payment_message']}")

                if email:
                    print(f"[📧] Send payment link to: {email}")

                return 0
            else:
                print(f"[❌] Payment processing failed: {result.get('error', 'Unknown error')}")
                return 1

        else:
            # For cash/check, create invoice and mark as paid
            result = payment_service.create_invoice_with_payment(
                job_id=job_id,
                amount=amount,
                customer_name=customer,
                customer_email=email,
                description=f"Payment for job {job_id} ({method})",
            )

            if result["success"]:
                invoice_id = result["invoice_id"]

                # Mark as paid immediately for cash/check
                update_result = payment_service.update_invoice_status(
                    invoice_id=invoice_id,
                    status="paid",
                    notes=f"Payment received via {method}",
                )

                if update_result["success"]:
                    print(f"[✅] Payment processed: {invoice_id}")
                    print(f"[💰] Method: {method.capitalize()}")
                    print(f"[💵] Amount: ${amount:.2f}")
                    if customer:
                        print(f"[👤] Customer: {customer}")
                else:
                    print(
                        f"[⚠️] Invoice created but status update failed: {update_result.get('error')}"
                    )

                return 0
            else:
                print(f"[❌] Payment processing failed: {result.get('error', 'Unknown error')}")
                return 1

    except Exception as e:
        print(f"[❌] Payment processing failed: {e}")
        return 1


def _process_payment(job_id: str, amount: float | None, method: str) -> None:
    """Legacy function - now integrated with payment service."""
    # This function is kept for backward compatibility but redirects to payment service
    result = payment_service.create_invoice_with_payment(
        job_id=job_id,
        amount=amount or 200.00,
        description=f"Payment for job {job_id} ({method})",
    )

    if not result["success"]:
        raise RuntimeError(result.get("error", "Payment processing failed"))
