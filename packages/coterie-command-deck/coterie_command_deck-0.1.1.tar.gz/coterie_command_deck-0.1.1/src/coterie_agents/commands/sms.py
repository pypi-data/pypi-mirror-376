# agents/commands/sms.py


import os

from coterie_agents.services.sms_service import send_sms

from ._cli import has_unknown_flags, print_help, wants_help

# Try to load environment variables from a .env file if present
try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass  # dotenv not installed; expect env vars to be set externally

# Configuration via environment variables
SMTP_SERVER: str = os.getenv("SMTP_SERVER", "smtp.sendgrid.net")
SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))  # use 465 for SSL or 2525/587 for TLS
SMTP_USER: str | None = os.getenv("SMTP_USER")  # Your SendGrid SMTP username (usually 'apikey')
SMTP_PASS: str | None = os.getenv("SMTP_PASS", SMTP_USER)
SENDER_EMAIL: str | None = os.getenv("SENDER_EMAIL")  # Verified sender address
SMS_GATEWAY: str = os.getenv(
    "SMS_GATEWAY", "@vtext.com"
)  # Carrier domain; e.g. @txt.att.net, @tmomail.net


def _validate_sms_config() -> bool:
    if not SMTP_USER or not SENDER_EMAIL:
        print(
            "[ERROR] Missing SMS configuration. Ensure SMTP_USER and SENDER_EMAIL "
            "are set via env or .env file."
        )
        return False
    return True


def _send_sms(number: str, message: str) -> None:
    send_sms(number, message)


COMMAND = "sms"
DESCRIPTION = "Send an SMS using the sms_service wrapper."
USAGE = f"{COMMAND} <number> <message> [--help]"


def run(argv: list[str] | None = None) -> int:
    argv = argv or []
    known_flags = {"--help", "-h"}

    if wants_help(argv):
        print_help(COMMAND, DESCRIPTION, USAGE)
        return 0
    if has_unknown_flags(argv, known_flags):
        print("Not found")
        print_help(COMMAND, DESCRIPTION, USAGE)
        return 0
    if len(argv) < 2:
        print("[ERROR] Usage: sms <number> <message>")
        return 0
    number = argv[0]
    message = " ".join(argv[1:])
    _send_sms(number, message)
    return 0
