# agents/bots/reminder_bot.py

import json
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

# Path to the reminders file (each line is a JSON object)
REMINDERS_PATH = Path(__file__).parents[2] / "reminders.jsonl"
TZ_SUFFIX = "+00:00"


def load_reminders() -> list[dict[str, Any]]:
    """
    Load all reminders from the reminders.jsonl file.
    Each reminder should be a JSON object with keys:
      - time: ISO timestamp string (UTC)
      - message: the reminder text
      - id: optional unique identifier
    """
    reminders = []
    if REMINDERS_PATH.exists():
        with open(REMINDERS_PATH, encoding="utf-8") as f:
            for line_num, line in enumerate(f, 1):
                try:
                    obj = json.loads(line.strip())
                    if "time" in obj and "message" in obj:
                        reminders.append(obj)
                    else:
                        print(f"[⚠️] ReminderBot: Skipped invalid reminder on line {line_num}")
                except json.JSONDecodeError as e:
                    print(f"[⚠️] ReminderBot: Skipped malformed JSON on line {line_num}: {e}")
    return reminders


def save_reminders(reminders: list[dict[str, Any]]) -> None:
    """
    Overwrite the reminders file with the given list of reminders.
    """
    try:
        REMINDERS_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(REMINDERS_PATH, "w", encoding="utf-8") as f:
            for r in reminders:
                f.write(json.dumps(r) + "\n")
    except Exception as e:
        print(f"[❌] ReminderBot: Failed to save reminders: {e}")


def format_time_until(target_time: datetime) -> str:
    """
    Format how much time until the reminder is due.
    """
    now = datetime.now(UTC)
    delta = target_time - now
    if delta.total_seconds() < 0:
        return "overdue"
    days = delta.days
    hours, remainder = divmod(delta.seconds, 3600)
    minutes, _ = divmod(remainder, 60)
    if days > 0:
        return f"{days}d {hours}h {minutes}m"
    elif hours > 0:
        return f"{hours}h {minutes}m"
    else:
        return f"{minutes}m"


def run(argv: list[str] | None = None, ctx: object | None = None) -> int:
    # CLI entrypoint (stub)
    _ = ctx
    argv = argv or []
    print("[ReminderBot] CLI mode not implemented.")
    return 0


def run_reminder_bot(check_interval: int = 60) -> None:
    """
    Start ReminderBot: checks every minute for due reminders,
    prints them, and removes them from the list once triggered.
    """
    import logging

    log = logging.getLogger(__name__)

    def process_reminders(
        reminders: list[dict[str, Any]], now: datetime
    ) -> tuple[list[dict[str, Any]], int]:
        pending: list[dict[str, Any]] = []
        triggered_count = 0
        for r in reminders:
            try:
                time_str = r["time"]
                if time_str.endswith("Z"):
                    time_str = time_str[:-1] + TZ_SUFFIX
                ts = datetime.fromisoformat(time_str)
                if now >= ts:
                    message = r.get("message", "No message")
                    reminder_id = r.get("id", "")
                    scheduled_time = ts.strftime("%Y-%m-%d %H:%M:%S UTC")
                    print(f"\n[⏰] REMINDER: {message}")
                    print(f"    Scheduled: {scheduled_time}")
                    if reminder_id:
                        print(f"    ID: {reminder_id}")
                    print()
                    triggered_count += 1
                else:
                    pending.append(r)
            except Exception as e:
                print(f"[⚠️] ReminderBot: Skipped invalid reminder: {e}")
        return pending, triggered_count

    def show_next_reminder(pending: list[dict[str, Any]], log: Any, check_interval: int) -> None:
        if pending and check_interval >= 60:
            next_reminder = min(pending, key=lambda r: r["time"])
            try:
                next_time_str = next_reminder["time"]
                if next_time_str.endswith("Z"):
                    next_time_str = next_time_str[:-1] + TZ_SUFFIX
                next_time = datetime.fromisoformat(next_time_str)
                time_until = format_time_until(next_time)
                print(f"[📅] Next reminder in {time_until}: {next_reminder['message'][:50]}...")
            except Exception as exc:
                log.warning(
                    "ReminderBot: failed to parse next reminder time: %s",
                    exc,
                    exc_info=False,
                )

    while True:
        now = datetime.now(UTC)
        reminders: list[dict[str, Any]] = load_reminders()
        if not reminders:
            time.sleep(check_interval)
            continue
        pending, triggered_count = process_reminders(reminders, now)
        if triggered_count > 0:
            save_reminders(pending)
            print(
                f"[✅] ReminderBot: Triggered {triggered_count} reminder(s), {len(pending)} remaining"
            )
        show_next_reminder(pending, log, check_interval)
        time.sleep(check_interval)
