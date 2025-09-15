from __future__ import annotations

import contextlib
import json
import logging
import os
import smtplib
import traceback
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any

from ._cli import has_unknown_flags, print_help, wants_help

# Try to import config settings, fallback to empty dict
try:
    from config import settings as _settings

    if hasattr(_settings, "get"):
        settings = _settings
    else:
        # settings is an object, convert to dict access
        settings = {
            "SMTP_SERVER": getattr(_settings, "SMTP_SERVER", "localhost"),
            "SMTP_PORT": getattr(_settings, "SMTP_PORT", 587),
            "SMTP_USER": getattr(_settings, "SMTP_USER", ""),
            "SMTP_PASS": getattr(_settings, "SMTP_PASS", ""),
            "SENDER_EMAIL": getattr(_settings, "SENDER_EMAIL", "noreply@example.com"),
        }
except ImportError:
    settings = {}

__all__ = ["run"]

COMMAND = "email_summary"
DESCRIPTION = "Send/preview a daily/weekly summary email."
USAGE = "deck email_summary [--to <email>] [--since YYYY-MM-DD]"


def run(argv: list[str] | None = None, _ctx: dict | None = None) -> int:
    argv = argv or []
    known = {"-h", "--help", "--to", "--since", "--dry-run"}
    if wants_help(argv):
        print_help(COMMAND, DESCRIPTION, USAGE)
        return 0
    if has_unknown_flags(argv, known):
        print("[ERROR] Unknown flag.")
        print_help(COMMAND, DESCRIPTION, USAGE)
        return 2
    # TODO: call your actual implementation here
    # e.g., return _send_summary(argv, ctx)
    print("[DRY-RUN] email_summary executed.")
    return 0


if __name__ == "__main__":
    import sys

    exit(run(sys.argv[1:], None))


# SMTP via centralized settings (with fallbacks)
SMTP_SERVER: str = settings.get("SMTP_SERVER", "localhost")
SMTP_PORT: int = settings.get("SMTP_PORT", 587)
SMTP_USER: str = settings.get("SMTP_USER", "")
SMTP_PASS: str = settings.get("SMTP_PASS", "")
SENDER_EMAIL: str = settings.get("SENDER_EMAIL", "noreply@example.com")

# Paths to data files
CREW_FILE = "crew_status.json"
BOOKING_FILE = "bookings.json"
LOG_FILE = "command_log.jsonl"

COMMAND = "email_summary"
DESCRIPTION = "Send a scheduled email summary of crew, bookings, and weather."
USAGE = f"{COMMAND} <recipient_email> [--subject SUBJ] [--format html|text] [--days N] [--help]"


def run(argv: list[str] | None = None, ctx: object | None = None) -> int:
    _ = ctx
    argv = argv or []
    rc = 0
    try:
        flags = _parse_flags(argv)
        data = _collect(flags)
        summary = _summarize(data, flags)
        _output(summary, flags)
    except Exception as e:
        print(f"[❌] email_summary failed: {e}")
        rc = 1
    return rc


def _parse_flags(argv: list[str]) -> dict[str, Any]:
    """Parse command-line flags"""
    flags = {
        "recipient_email": argv[0] if argv else None,
        "subject": None,
        "format": "html",
        "days": 7,
    }
    i = 1
    while i < len(argv):
        if argv[i] == "--subject" and i + 1 < len(argv):
            flags["subject"] = argv[i + 1]
            i += 2
        elif argv[i] == "--format" and i + 1 < len(argv):
            flags["format"] = argv[i + 1]
            i += 2
        elif argv[i] == "--days" and i + 1 < len(argv):
            with contextlib.suppress(ValueError):
                flags["days"] = int(argv[i + 1])
            i += 2
        else:
            i += 1
    return flags


def _collect(flags: dict[str, Any]) -> dict[str, Any]:
    """Collect data for the summary"""
    recipient = flags["recipient_email"]
    days = flags["days"]

    # Validate SMTP configuration
    if not all([SMTP_SERVER, SMTP_USER, SMTP_PASS, SENDER_EMAIL]):
        print("[ERROR] Email configuration incomplete.")
        print("[ℹ️] Required: SMTP_SERVER, SMTP_USERNAME, SMTP_PASSWORD, SMTP_FROM in config.")
        print("[ℹ️] Current config:")
        print(f"  SMTP_SERVER: {SMTP_SERVER or 'Not set'}")
        print(f"  SMTP_USER: {'Set' if SMTP_USER else 'Not set'}")
        print(f"  SMTP_PASS: {'Set' if SMTP_PASS else 'Not set'}")
        print(f"  SENDER_EMAIL: {SENDER_EMAIL or 'Not set'}")
        return {}

    print(f"[📧] Generating email summary for {recipient}...")

    # Gather data
    crew_status: dict[str, Any] = {}
    try:
        if os.path.exists(CREW_FILE):
            with open(CREW_FILE) as f:
                crew_status = json.load(f)
    except Exception as e:
        logging.error(f"[❌] email_summary - load crew_status failed: {e}")

    bookings: list[dict[str, Any]] = []
    upcoming_bookings: list[dict[str, Any]] = []
    try:
        if os.path.exists(BOOKING_FILE):
            with open(BOOKING_FILE) as f:
                bookings = json.load(f)

            now = datetime.now()
            end = now + timedelta(days=days)
            for b in bookings:
                try:
                    dt = datetime.fromisoformat(b["datetime"])
                    if now <= dt <= end:
                        upcoming_bookings.append(b)
                except Exception:
                    logging.exception("Error occurred in bookings datetime parsing")
    except Exception as e:
        logging.error(f"[❌] email_summary - load bookings failed: {e}")

    import io
    import sys

    from coterie_agents.commands.notify import run as notify_run

    crew_alerts = ""
    try:
        old_stdout = sys.stdout
        notify_buffer = io.StringIO()
        sys.stdout = notify_buffer
        notify_run(["--soon", "60"])
        sys.stdout = old_stdout
        crew_alerts = notify_buffer.getvalue()
    except Exception as e:
        logging.error(f"[❌] email_summary - get crew alerts failed: {e}")
        crew_alerts = "Crew alerts unavailable"

    from coterie_agents.commands.weather_check import run as weather_run

    weather_summary = ""
    try:
        old_stdout = sys.stdout
        weather_buffer = io.StringIO()
        sys.stdout = weather_buffer
        weather_run(["--days", str(days)])
        sys.stdout = old_stdout
        weather_summary = weather_buffer.getvalue()
    except Exception as e:
        logging.error(f"[❌] email_summary - get weather summary failed: {e}")
        weather_summary = "Weather data unavailable"

    total_revenue = sum(b.get("total_price", 0) for b in upcoming_bookings)
    booking_count = len(upcoming_bookings)

    return {
        "recipient": recipient,
        "subject": flags["subject"],
        "format": flags["format"],
        "days": days,
        "crew_status": crew_status,
        "crew_alerts": crew_alerts,
        "bookings": upcoming_bookings,
        "weather_summary": weather_summary,
        "total_revenue": total_revenue,
        "booking_count": booking_count,
    }


def _summarize(data: dict[str, Any], flags: dict[str, Any]) -> str:
    """Summarize the data for output"""
    fmt = flags["format"]
    if fmt == "html":
        return build_html_email(
            data["subject"],
            data["crew_status"],
            data["crew_alerts"],
            data["bookings"],
            data["weather_summary"],
            data["total_revenue"],
            data["booking_count"],
            flags["days"],
        )
    else:
        return build_text_email(
            data["subject"],
            data["crew_status"],
            data["crew_alerts"],
            data["bookings"],
            data["weather_summary"],
            data["total_revenue"],
            data["booking_count"],
            flags["days"],
        )


def _output(summary: str, flags: dict[str, Any]) -> None:
    """Output the summary (send email)"""
    recipient = flags["recipient_email"]
    success = send_email(recipient, flags["subject"], summary, flags["format"])

    if success:
        print(f"[📧] ✅ Email summary sent to {recipient}")
        print(
            f"[📊] Included: {len(flags['crew_status'])} crew, {flags['booking_count']} bookings, weather alerts"
        )
    else:
        print(f"[❌] Failed to send email to {recipient}")


def build_html_email(
    subject: str,
    crew_status: dict[str, Any],
    crew_alerts: str,
    bookings: list[dict[str, Any]],
    weather_summary: str,
    total_revenue: float,
    booking_count: int,
    days: int,
) -> str:
    """Build HTML email with professional formatting"""
    now = datetime.now()
    html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }}
                .container {{ max-width: 800px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; text-align: center; }}
                .stats {{ display: flex; justify-content: space-around; margin: 20px 0; }}
                .stat-box {{ text-align: center; padding: 15px; background: #f8f9fa; border-radius: 8px; flex: 1; margin: 0 5px; }}
                .stat-number {{ font-size: 24px; font-weight: bold; color: #667eea; }}
                .stat-label {{ color: #666; font-size: 12px; text-transform: uppercase; }}
                .section {{ margin: 20px 0; padding: 15px; border-left: 4px solid #667eea; background: #f8f9fa; }}
                .section h3 {{ margin-top: 0; color: #333; }}
                .alert {{ background: #fff3cd; border: 1px solid #ffeaa7; padding: 10px; border-radius: 4px; margin: 10px 0; }}
                .booking-item {{ background: white; border: 1px solid #dee2e6; padding: 10px; margin: 5px 0; border-radius: 4px; }}
                .booking-header {{ font-weight: bold; color: #495057; }}
                .booking-details {{ color: #6c757d; font-size: 14px; }}
                .pre-formatted {{ background: #f8f9fa; padding: 10px; border-radius: 4px; font-family: monospace; font-size: 12px; white-space: pre-wrap; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🏢 Coterie Operations Summary</h1>
                    <p>{now.strftime("%A, %B %d, %Y at %I:%M %p")}</p>
                </div>

                <div class="stats">
                    <div class="stat-box">
                        <div class="stat-number">${total_revenue:,.0f}</div>
                        <div class="stat-label">{days}-Day Revenue</div>
                    </div>
                    <div class="stat-box">
                        <div class="stat-number">{booking_count}</div>
                        <div class="stat-label">Upcoming Bookings</div>
                    </div>
                    <div class="stat-box">
                        <div class="stat-number">{len(crew_status)}</div>
                        <div class="stat-label">Crew Members</div>
                    </div>
                </div>

                <div class="section">
                    <h3>👥 Crew Status & Alerts</h3>
                    <div class="pre-formatted">{crew_alerts}</div>
                </div>

                <div class="section">
                    <h3>📅 Upcoming Bookings ({days} days)</h3>
                    <p><strong>Total Revenue: ${total_revenue:,.2f}</strong></p>
        """

    if bookings:
        for booking in bookings[:10]:  # Show up to 10 bookings
            try:
                dt = datetime.fromisoformat(booking["datetime"])
                dt_str = dt.strftime("%a, %b %d at %I:%M %p")
                customer = booking.get("customer", "Unknown")
                location = booking.get("location", "")
                tier = booking.get("tier", "")
                price = booking.get("total_price", 0)

                html += f"""
                    <div class="booking-item">
                        <div class="booking-header">{customer} - {tier}</div>
                        <div class="booking-details">
                            📍 {location}<br>
                            📅 {dt_str}<br>
                            💰 ${price:,.2f}
                        </div>
                    </div>
                """
            except Exception:
                logging.exception("Error occurred in booking row rendering")

        if len(bookings) > 10:
            html += f"<p><em>...and {len(bookings) - 10} more bookings</em></p>"
    else:
        html += f'<div class="alert">No upcoming bookings in the next {days} days.</div>'

    html += f"""
            </div>

            <div class="section">
                <h3>🌤️ Weather Alerts & Conditions</h3>
                <div class="pre-formatted">{weather_summary}</div>
            </div>

            <div style="text-align: center; margin-top: 30px; padding-top: 20px; border-top: 1px solid #dee2e6; color: #6c757d;">
                <p>Generated by Coterie Command Deck • {now.strftime("%Y-%m-%d %H:%M:%S")}</p>
            </div>
        </div>
    </body>
    </html>
    """
    return html


def build_text_email(
    subject: str,
    crew_status: dict[str, Any],
    crew_alerts: str,
    bookings: list[dict[str, Any]],
    weather_summary: str,
    total_revenue: float,
    booking_count: int,
    days: int,
) -> str:
    """Build plain text email"""
    lines: list[str] = []
    lines.append(f"{subject}")
    lines.append("=" * len(subject))
    lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("")

    lines.append("KEY STATISTICS:")
    lines.append(f"  • {days}-Day Revenue: ${total_revenue:,.0f}")
    lines.append(f"  • Upcoming Bookings: {booking_count}")
    lines.append(f"  • Crew Members: {len(crew_status)}")
    lines.append("")

    lines.append("CREW STATUS & ALERTS:")
    lines.append("-" * 25)
    lines.append(crew_alerts if crew_alerts else "No crew alerts")
    lines.append("")

    lines.append(f"UPCOMING BOOKINGS ({days} days):")
    lines.append("-" * 30)
    if bookings:
        total_revenue = sum(b.get("total_price", 0) for b in bookings)
        lines.append(f"Total Revenue: ${total_revenue:,.2f}")
        lines.append("")
        for booking in bookings[:10]:
            try:
                dt = datetime.fromisoformat(booking["datetime"])
                dt_str = dt.strftime("%a, %b %d at %I:%M %p")
                customer = booking.get("customer", "Unknown")
                tier = booking.get("tier", "")
                size = booking.get("size", "")
                location = booking.get("location", "")
                vehicles = booking.get("vehicles", "")
                price = booking.get("total_price", 0)
                lines.append(f"• {customer} - {tier} ({size})")
                lines.append(f"  {dt_str} @ {location}")
                lines.append(f"  {vehicles} vehicle(s) | ${price:,.2f}")
                lines.append("")
            except Exception:
                logging.exception("Error occurred in booking row rendering")
    else:
        lines.append(f"No upcoming bookings in the next {days} days.")
        lines.append("")

    lines.append("WEATHER ALERTS:")
    lines.append("-" * 15)
    lines.append(weather_summary if weather_summary else "Weather data unavailable")

    lines.append("")
    lines.append("---")
    lines.append("Generated by Coterie Command Deck")
    return "\n".join(lines)


def send_email(recipient, subject, body, fmt):
    """Send email with error handling"""
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = SENDER_EMAIL
        msg["To"] = recipient

        if fmt == "html":
            msg.attach(MIMEText(body, "html"))
        else:
            msg.attach(MIMEText(body, "plain"))

        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SMTP_USER, SMTP_PASS)
        server.sendmail(SENDER_EMAIL, recipient, msg.as_string())
        server.quit()

        return True

    except Exception:
        logging.error(f"[❌] email_summary - send failed: {traceback.format_exc()}")
        return False
