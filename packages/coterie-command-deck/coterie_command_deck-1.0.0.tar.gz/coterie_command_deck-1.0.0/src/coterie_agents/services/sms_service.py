from __future__ import annotations

import os

TWILIO_ENABLED = os.getenv("COMMS_ENABLED", "false").lower() == "true" and all(
    os.getenv(k) for k in ["TWILIO_ACCOUNT_SID", "TWILIO_AUTH_TOKEN", "TWILIO_FROM"]
)


class SMSResult:
    def __init__(self, success: bool, message: str):
        self.success = success
        self.message = message


def send_sms(number: str, message: str) -> SMSResult:
    if not TWILIO_ENABLED:
        print("[DRY-RUN] SMS not sent. Enable COMMS_ENABLED and TWILIO_* envs.")
        return SMSResult(False, "[DRY-RUN] SMS not sent. Enable COMMS_ENABLED and TWILIO_* envs.")
    try:
        from twilio.rest import Client

        client = Client(os.getenv("TWILIO_ACCOUNT_SID"), os.getenv("TWILIO_AUTH_TOKEN"))
        msg = client.messages.create(body=message, from_=os.getenv("TWILIO_FROM"), to=number)
        print(f"SMS sent: SID {msg.sid}")
        return SMSResult(True, f"SMS sent: SID {msg.sid}")
    except Exception as e:
        print(f"SMS failed: {e}")
        return SMSResult(False, f"SMS failed: {e}")
