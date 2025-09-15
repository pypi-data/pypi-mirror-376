"""Generate invoices for completed jobs (DRY-RUN by default)."""

from __future__ import annotations

import os

from ._cli import has_unknown_flags, print_help, wants_help

COMMAND = "generate_invoice"
DESCRIPTION = "Generate invoices for completed jobs."
USAGE = f"{COMMAND} <job_id> [--customer <customer_name>] [--email <email>] [--help]"


def _parse_invoice_args(argv: list[str]) -> tuple[str | None, str | None, str | None]:
    """Parse job_id, customer, and email from argv."""
    if not argv:
        return None, None, None

    job_id = argv[0]
    customer = None
    email = None

    i = 1
    while i < len(argv):
        if argv[i] == "--customer" and i + 1 < len(argv):
            customer = argv[i + 1]
            i += 2
        elif argv[i] == "--email" and i + 1 < len(argv):
            email = argv[i + 1]
            i += 2
        else:
            i += 1

    return job_id, customer, email


def run(argv: list[str] | None = None, _ctx: object = None) -> int:
    """CLI entrypoint for generate_invoice command."""
    argv = argv or []
    known_flags = {"--help", "-h", "--customer", "--email"}

    if wants_help(argv):
        print_help(COMMAND, DESCRIPTION, USAGE)
        print("\nExamples:")
        print(f"  {COMMAND} JOB001 --customer 'John Smith' --email john@example.com")
        print(f"  {COMMAND} JOB002 --customer 'ABC Corp'")
        print("\nNOTE: Runs in DRY-RUN mode unless PAYMENTS_ENABLED=true")
        return 0

    if has_unknown_flags(argv, known_flags):
        print("Not found")
        print_help(COMMAND, DESCRIPTION, USAGE)
        return 0

    job_id, customer, email = _parse_invoice_args(argv)

    if not job_id:
        print("[ERROR] Job ID is required")
        print_help(COMMAND, DESCRIPTION, USAGE)
        return 1

    # Check if payments are enabled
    payments_enabled = os.getenv("PAYMENTS_ENABLED", "false").lower() == "true"

    if not payments_enabled:
        print("[DRY-RUN] Would generate invoice:")
        print(f"  Job ID: {job_id}")
        if customer:
            print(f"  Customer: {customer}")
        if email:
            print(f"  Email to: {email}")
        print("  (Set PAYMENTS_ENABLED=true to generate real invoices)")
        return 0

    # Real invoice generation would go here
    try:
        invoice_path = _generate_invoice(job_id, customer, email)
        print(f"[✅] Invoice generated: {invoice_path}")
        if email:
            print(f"[📧] Invoice emailed to: {email}")
        return 0
    except Exception as e:
        print(f"[❌] Invoice generation failed: {e}")
        return 1


def _generate_invoice(job_id: str, customer: str | None, email: str | None) -> str:
    """Generate invoice (stub implementation)."""
    # In real implementation, would:
    # - Look up job details and pricing
    # - Generate PDF invoice with proper formatting
    # - Store in invoices directory
    # - Email if address provided
    # - Update accounting system
    raise NotImplementedError(
        "Invoice generation not implemented - configure invoice template and PDF generator"
    )
