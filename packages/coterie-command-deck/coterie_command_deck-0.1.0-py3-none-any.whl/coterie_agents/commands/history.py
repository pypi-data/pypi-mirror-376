import json
import os
from datetime import datetime
from typing import Any

from ._cli import has_unknown_flags, print_help, wants_help

LOG_FILE = "command_log.json"


def _parse_date(date_str: str) -> datetime | None:
    """Parse date string in various formats."""
    formats = [
        "%Y-%m-%d",
        "%Y-%m-%dT%H:%M",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%Y-%m-%d %H:%M:%S",
    ]

    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    return None


def _filter_entries(
    entries: list[dict[str, Any]],
    since: str | None,
    assignee: str | None,
    contains: str | None,
) -> list[dict[str, Any]]:
    """Filter entries based on criteria."""
    filtered = entries

    # Filter by date
    if since:
        since_dt = _parse_date(since)
        if since_dt:
            filtered = []
            for entry in filtered:
                entry_dt = _parse_date(str(entry.get("timestamp", "")))
                if entry_dt and entry_dt >= since_dt:
                    filtered.append(entry)

    # Filter by assignee
    if assignee:
        filtered = [
            entry
            for entry in filtered
            if assignee.lower() in str(entry.get("assignee", "")).lower()
            or assignee.lower() in str(entry.get("assignees", [])).lower()
            or assignee.lower() in str(entry.get("args", [])).lower()
        ]

    # Filter by contains
    if contains:
        filtered = [entry for entry in filtered if contains.lower() in json.dumps(entry).lower()]

    return filtered


def _parse_args(argv: list[str]) -> tuple[int, str | None, str | None, str | None]:
    """Parse command line arguments."""
    limit = 10
    since = None
    assignee = None
    contains = None

    i = 0
    while i < len(argv):
        arg = argv[i]
        if arg == "--limit" and i + 1 < len(argv):
            try:
                limit = int(argv[i + 1])
                i += 2
            except ValueError:
                i += 1
        elif arg == "--since" and i + 1 < len(argv):
            since = argv[i + 1]
            i += 2
        elif arg == "--assignee" and i + 1 < len(argv):
            assignee = argv[i + 1]
            i += 2
        elif arg == "--contains" and i + 1 < len(argv):
            contains = argv[i + 1]
            i += 2
        else:
            i += 1

    return limit, since, assignee, contains


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


def run(argv: list[str] | None = None, _ctx: object = None) -> int:
    argv = argv or []
    known_flags = {"--help", "-h", "--limit", "--since", "--assignee", "--contains"}

    COMMAND = "history"
    DESCRIPTION = "Show past command history from logs with filtering options."
    USAGE = f"{COMMAND} [--limit N] [--since YYYY-MM-DD] [--assignee NAME] [--contains TEXT]"

    if wants_help(argv):
        print_help(COMMAND, DESCRIPTION, USAGE)
        print("\nExamples:")
        print(f"  {COMMAND} --limit 10")
        print(f"  {COMMAND} --since 2025-09-01 --assignee Jet --contains wash")
        return 0

    if has_unknown_flags(argv, known_flags):
        print("Not found")
        print_help(COMMAND, DESCRIPTION, USAGE)
        return 0

    # Parse arguments
    limit, since, assignee, contains = _parse_args(argv)

    # Load entries
    entries = _load_log_entries()
    if not entries:
        print("[ℹ️] No command log found.")
        return 0

    try:
        # Apply filters
        filtered_entries = _filter_entries(entries, since, assignee, contains)

        # Apply limit
        recent = filtered_entries[-limit:] if limit > 0 else filtered_entries

        # Display results
        filter_parts: list[str] = []
        if since:
            filter_parts.append(f"since {since}")
        if assignee:
            filter_parts.append(f"assignee '{assignee}'")
        if contains:
            filter_parts.append(f"contains '{contains}'")

        filter_info = f" ({', '.join(filter_parts)})" if filter_parts else ""
        print(f"\n[📜] Command History - {len(recent)} entries{filter_info}:\n")

        if not recent:
            print("(no matching entries)")
            return 0

        # Print header
        print(f"{'#':<4} {'Time':<12} {'Command':<15} {'Details'}")
        print("─" * 60)

        # Print entries
        for i, entry in enumerate(recent, 1):
            timestamp = entry.get("timestamp", "unknown")
            command = entry.get("command", "unknown")
            args_list = entry.get("args", [])

            # Format timestamp
            try:
                if isinstance(timestamp, str):
                    dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                    time_str = dt.strftime("%H:%M:%S")
                else:
                    time_str = str(timestamp)[:8]
            except Exception:
                time_str = str(timestamp)[:8] if timestamp else "unknown"

            # Format args
            args_str = " ".join(str(arg) for arg in args_list[:3])  # Limit args display
            if len(args_list) > 3:
                args_str += "..."

            print(f"{i:<4} {time_str:<12} {command:<15} {args_str}")

        return 0

    except Exception as e:
        print(f"[❌] Error reading log file: {e}")
        return 1
