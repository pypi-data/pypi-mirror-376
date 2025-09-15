"""SMTP Email integration (DRY-RUN by default)."""

import os
import smtplib
from email.message import EmailMessage

SMTP_ENABLED = os.getenv("COMMS_ENABLED", "false").lower() == "true" and all(
    os.getenv(k) for k in ["SMTP_HOST", "SMTP_PORT", "SMTP_USER", "SMTP_PASS", "SMTP_FROM"]
)


class EmailResult:
    def __init__(self, success: bool, message: str):
        self.success = success
        self.message = message


def send_email(to: str, subject: str, body: str) -> EmailResult:
    if not SMTP_ENABLED:
        print("[DRY-RUN] Email not sent. Enable COMMS_ENABLED and SMTP_* envs.")
        return EmailResult(False, "[DRY-RUN] Email not sent. Enable COMMS_ENABLED and SMTP_* envs.")
    try:
        msg = EmailMessage()
        msg["From"] = os.getenv("SMTP_FROM")
        msg["To"] = to
        msg["Subject"] = subject
        msg.set_content(body)
        with smtplib.SMTP(os.getenv("SMTP_HOST"), int(os.getenv("SMTP_PORT"))) as server:
            server.starttls()
            server.login(os.getenv("SMTP_USER"), os.getenv("SMTP_PASS"))
            server.send_message(msg)
        print("Email sent successfully.")
        return EmailResult(True, "Email sent successfully.")
    except Exception as e:
        print(f"Email failed: {e}")
        return EmailResult(False, f"Email failed: {e}")
