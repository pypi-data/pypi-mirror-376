"""Send notifications via SMS, email, or other channels (DRY-RUN by default)."""

from __future__ import annotations

import os

from ._cli import has_unknown_flags, print_help, wants_help

COMMAND = "notify"
DESCRIPTION = "Send notifications via SMS, email, or other channels."
USAGE = f"{COMMAND} <message> --to <recipient> [--channel <sms|email|slack>] [--help]"


def _parse_arguments(argv: list[str]) -> tuple[str | None, str | None, str]:
    """Parse message, recipient, and channel from argv."""
    if not argv:
        return None, None, "sms"

    message = argv[0]
    recipient = None
    channel = "sms"  # default

    i = 1
    while i < len(argv):
        if argv[i] == "--to" and i + 1 < len(argv):
            recipient = argv[i + 1]
            i += 2
        elif argv[i] == "--channel" and i + 1 < len(argv):
            channel = argv[i + 1]
            i += 2
        else:
            i += 1

    return message, recipient, channel


def _send_notification(message: str, recipient: str, channel: str) -> None:
    """Send notification via specified channel."""
    if channel == "sms":
        _send_sms(message, recipient)
    elif channel == "email":
        _send_email(message, recipient)
    elif channel == "slack":
        _send_slack(message, recipient)


def run(argv: list[str] | None = None, _ctx: object = None) -> int:
    """CLI entrypoint for notify command."""
    argv = argv or []
    known_flags = {"--help", "-h", "--to", "--channel"}

    if wants_help(argv):
        print_help(COMMAND, DESCRIPTION, USAGE)
        print("\nExamples:")
        print(f"  {COMMAND} 'Job completed' --to +1850XXXXXXX --channel sms")
        print(f"  {COMMAND} 'Alert: Server down' --to admin@company.com --channel email")
        print(f"  {COMMAND} 'Daily report ready' --to #general --channel slack")
        print("\nNOTE: Runs in DRY-RUN mode unless COMMS_ENABLED=true")
        return 0

    if has_unknown_flags(argv, known_flags):
        print("Not found")
        print_help(COMMAND, DESCRIPTION, USAGE)
        return 0

    # Parse arguments
    message, recipient, channel = _parse_arguments(argv)

    if not message:
        print("[ERROR] Message is required")
        print_help(COMMAND, DESCRIPTION, USAGE)
        return 1

    if not recipient:
        print("[ERROR] Recipient (--to) is required")
        print_help(COMMAND, DESCRIPTION, USAGE)
        return 1

    if channel not in {"sms", "email", "slack"}:
        print(f"[ERROR] Unsupported channel: {channel}")
        print("Supported channels: sms, email, slack")
        return 1

    # Check if comms are enabled
    comms_enabled = os.getenv("COMMS_ENABLED", "false").lower() == "true"

    if not comms_enabled:
        print(f"[DRY-RUN] Would send {channel} to {recipient}:")
        print(f"  Message: {message}")
        print("  (Set COMMS_ENABLED=true to send real notifications)")
        return 0

    # Real communication would go here
    try:
        _send_notification(message, recipient, channel)
        print(f"[✅] {channel.upper()} sent to {recipient}")
        return 0
    except Exception as e:
        print(f"[❌] Failed to send {channel}: {e}")
        return 1


def _send_sms(message: str, phone: str) -> None:
    """Send SMS message (stub implementation)."""
    # In real implementation, would use Twilio, AWS SNS, etc.
    raise NotImplementedError("SMS sending not implemented - configure COMMS provider")


def _send_email(message: str, email: str) -> None:
    """Send email message (stub implementation)."""
    # In real implementation, would use SMTP, SendGrid, etc.
    raise NotImplementedError("Email sending not implemented - configure COMMS provider")


def _send_slack(message: str, channel: str) -> None:
    """Send Slack message (stub implementation)."""
    # In real implementation, would use Slack API
    raise NotImplementedError("Slack sending not implemented - configure COMMS provider")
