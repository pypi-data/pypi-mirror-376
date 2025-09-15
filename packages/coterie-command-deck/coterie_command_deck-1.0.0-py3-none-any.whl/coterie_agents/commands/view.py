import json
import os
from datetime import datetime
from typing import Any

from ._cli import has_unknown_flags, print_help, wants_help

LOG_FILE = "command_log.json"

COMMAND = "view"
DESCRIPTION = "View detailed information for a specific log entry by ID."
USAGE = f"{COMMAND} <log_id> [--help]"


def _load_log_entries() -> list[dict[str, Any]]:
    """Load entries from command log file."""
    if not os.path.exists(LOG_FILE):
        return []

    try:
        with open(LOG_FILE) as f:
            data = json.load(f)

        # Handle both list and dict formats
        if isinstance(data, dict):
            entries = data.get("entries", [])
            return entries if isinstance(entries, list) else []
        elif isinstance(data, list):
            return data
        else:
            return []
    except Exception:
        return []


def _find_entry_by_id(entries: list[dict[str, Any]], log_id: str) -> dict[str, Any] | None:
    """Find a log entry by ID."""
    try:
        target_id = int(log_id)
    except ValueError:
        return None

    # Try to find by explicit ID field first
    for entry in entries:
        if entry.get("id") == target_id:
            return entry

    # Fallback: use 1-based index as ID
    if 1 <= target_id <= len(entries):
        return entries[target_id - 1]

    return None


def _format_timestamp(timestamp: Any) -> str:
    """Format timestamp for display."""
    try:
        if isinstance(timestamp, str):
            dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            return dt.strftime("%Y-%m-%d %H:%M:%S")
        else:
            return str(timestamp)
    except Exception:
        return str(timestamp) if timestamp else "unknown"


def _print_entry_detail(entry: dict[str, Any], entry_id: str) -> None:
    """Print detailed view of a log entry."""
    print(f"\n{'=' * 60}")
    print(f"📋 LOG ENTRY #{entry_id}")
    print(f"{'=' * 60}\n")

    # Core fields
    command = entry.get("command", "unknown")
    timestamp = entry.get("timestamp", "unknown")
    args = entry.get("args", [])

    print(f"🕐 Timestamp:  {_format_timestamp(timestamp)}")
    print(f"⚡ Command:    {command}")

    if args:
        print(f"📝 Arguments:  {' '.join(str(arg) for arg in args)}")

    # Additional fields
    additional_fields = {
        key: value
        for key, value in entry.items()
        if key not in ["command", "timestamp", "args", "id"]
    }

    if additional_fields:
        print("\n📊 Additional Fields:")
        for key, value in additional_fields.items():
            print(f"   {key}: {value}")

    # Raw JSON
    print("\n🔧 Raw JSON:")
    print("-" * 40)
    print(json.dumps(entry, indent=2, default=str))
    print("-" * 40)


def run(argv: list[str] | None = None, _ctx: object = None) -> int:
    argv = argv or []
    known_flags = {"--help", "-h"}

    if wants_help(argv):
        print_help(COMMAND, DESCRIPTION, USAGE)
        print("\nExamples:")
        print(f"  {COMMAND} 1     # View first log entry")
        print(f"  {COMMAND} 42    # View entry with ID 42")
        return 0

    if has_unknown_flags(argv, known_flags):
        print("Not found")
        print_help(COMMAND, DESCRIPTION, USAGE)
        return 0

    # Get log ID argument
    if not argv:
        print("[ERROR] Log ID is required")
        print_help(COMMAND, DESCRIPTION, USAGE)
        return 1

    log_id = argv[0]

    # Load log entries
    entries = _load_log_entries()
    if not entries:
        print("[ℹ️] No command log found.")
        return 0

    # Find the entry
    entry = _find_entry_by_id(entries, log_id)
    if not entry:
        print(f"[❌] No log entry found with ID: {log_id}")
        print(f"[ℹ️] Available entries: 1-{len(entries)}")
        return 1

    # Display the entry
    _print_entry_detail(entry, log_id)
    return 0
