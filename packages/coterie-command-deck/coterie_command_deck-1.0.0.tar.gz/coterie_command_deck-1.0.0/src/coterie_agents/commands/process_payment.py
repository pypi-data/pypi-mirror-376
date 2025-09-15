"""Process payments and invoicing (DRY-RUN by default)."""

from __future__ import annotations

import os

from ._cli import has_unknown_flags, print_help, wants_help

COMMAND = "process_payment"
DESCRIPTION = "Process payments and generate invoices."
USAGE = f"{COMMAND} <job_id> [--amount <amount>] [--method <card|cash|check>] [--help]"


def run(argv: list[str] | None = None, _ctx: object = None) -> int:
    """CLI entrypoint for process_payment command."""
    argv = argv or []
    known_flags = {"--help", "-h", "--amount", "--method"}

    if wants_help(argv):
        print_help(COMMAND, DESCRIPTION, USAGE)
        print("\nExamples:")
        print(f"  {COMMAND} JOB001 --amount 250.00 --method card")
        print(f"  {COMMAND} JOB002 --amount 150.00 --method cash")
        print(f"  {COMMAND} JOB003 --method check  # Amount from booking")
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

    # Parse flags
    i = 1
    while i < len(argv):
        if argv[i] == "--amount" and i + 1 < len(argv):
            try:
                amount = float(argv[i + 1])
            except ValueError:
                print(f"[ERROR] Invalid amount: {argv[i + 1]}")
                return 1
            i += 2
        elif argv[i] == "--method" and i + 1 < len(argv):
            method = argv[i + 1]
            i += 2
        else:
            i += 1

    if method not in {"card", "cash", "check"}:
        print(f"[ERROR] Unsupported payment method: {method}")
        print("Supported methods: card, cash, check")
        return 1

    # Check if payments are enabled
    payments_enabled = os.getenv("PAYMENTS_ENABLED", "false").lower() == "true"

    if not payments_enabled:
        amount_str = f"${amount:.2f}" if amount else "(amount from booking)"
        print("[DRY-RUN] Would process payment:")
        print(f"  Job ID: {job_id}")
        print(f"  Amount: {amount_str}")
        print(f"  Method: {method}")
        print("  (Set PAYMENTS_ENABLED=true to process real payments)")
        return 0

    # Real payment processing would go here
    try:
        _process_payment(job_id, amount, method)
        amount_str = f"${amount:.2f}" if amount else "(from booking)"
        print(f"[✅] Payment processed: {job_id} - {amount_str} via {method}")
        return 0
    except Exception as e:
        print(f"[❌] Payment processing failed: {e}")
        return 1


def _process_payment(job_id: str, amount: float | None, method: str) -> None:
    """Process payment (stub implementation)."""
    # In real implementation, would integrate with:
    # - Stripe/Square/PayPal for card processing
    # - QuickBooks/Xero for invoicing
    # - Banking APIs for ACH/check processing
    raise NotImplementedError(
        f"Payment processing not implemented - configure payment provider for {method}"
    )
