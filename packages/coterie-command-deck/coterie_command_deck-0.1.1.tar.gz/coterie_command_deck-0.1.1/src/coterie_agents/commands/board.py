from __future__ import annotations

import json
import os
import shutil
from typing import Any

from ._cli import has_unknown_flags, print_help, wants_help

CREW_STATUS_FILE = "crew_status.json"

COMMAND = "board"
DESCRIPTION = "Show crew/task board grouped by status columns."
USAGE = f"{COMMAND} [--help]"


def _load_crew_status() -> dict[str, Any]:
    """Load crew status from JSON file."""
    if not os.path.exists(CREW_STATUS_FILE):
        return {}

    try:
        with open(CREW_STATUS_FILE) as f:
            return json.load(f)
    except Exception:
        return {}


def _get_terminal_width() -> int:
    """Get terminal width, default to 80 if unable to detect."""
    try:
        return shutil.get_terminal_size().columns
    except Exception:
        return 80


def _organize_by_status(crew_data: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    """Organize crew/jobs by status columns."""
    columns = {"Queued": [], "In-Progress": [], "Done": []}

    # Process crew members
    crew = crew_data.get("crew", {})
    for name, member in crew.items():
        status = member.get("status", "unknown")
        tasks = member.get("tasks", [])

        item = {
            "type": "crew",
            "name": name,
            "details": member.get("role", ""),
            "tasks": len(tasks),
            "primary_task": tasks[0] if tasks else None,
        }

        # Map status to column
        if status.lower() in ["idle", "available", "waiting"]:
            columns["Queued"].append(item)
        elif status.lower() in ["active", "working", "busy"]:
            columns["In-Progress"].append(item)
        elif status.lower() in ["done", "finished", "completed"]:
            columns["Done"].append(item)
        else:
            columns["Queued"].append(item)  # Default fallback

    # Process open jobs if they exist
    jobs = crew_data.get("jobs", [])
    for job in jobs:
        status = job.get("status", "unknown")

        item = {
            "type": "job",
            "name": job.get("title", job.get("name", "Untitled Job")),
            "details": job.get("assignee", "unassigned"),
            "tasks": 1,
            "primary_task": job.get("description", ""),
        }

        # Map job status to column
        if status.lower() in ["pending", "new", "open", "queued"]:
            columns["Queued"].append(item)
        elif status.lower() in ["active", "in-progress", "working"]:
            columns["In-Progress"].append(item)
        elif status.lower() in ["done", "finished", "completed", "closed"]:
            columns["Done"].append(item)
        else:
            columns["Queued"].append(item)  # Default fallback

    return columns


def _print_board_narrow(columns: dict[str, list[dict[str, Any]]]) -> None:
    """Print board in narrow format (< 80 columns)."""
    for status, items in columns.items():
        count = len(items)
        print(f"\n📋 {status} ({count}):")
        print("-" * 20)

        if not items:
            print("  (none)")
            continue

        for item in items:
            icon = "👤" if item["type"] == "crew" else "📝"
            name = item["name"][:15]  # Truncate for narrow display
            details = item["details"][:10] if item["details"] else ""

            line = f"  {icon} {name}"
            if details:
                line += f" ({details})"
            print(line)


def _print_board_wide(columns: dict[str, list[dict[str, Any]]], width: int) -> None:
    """Print board in wide columnar format (>= 80 columns)."""
    col_width = min((width - 4) // 3, 25)  # 3 columns with padding

    # Header
    header = f"{'Queued':<{col_width}} | {'In-Progress':<{col_width}} | {'Done':<{col_width}}"
    print(header)
    print("=" * len(header))

    # Get max items across columns
    max_items = max(len(items) for items in columns.values())

    # Print rows
    for i in range(max_items):
        row_parts = []

        for status in ["Queued", "In-Progress", "Done"]:
            items = columns[status]
            if i < len(items):
                item = items[i]
                icon = "👤" if item["type"] == "crew" else "📝"
                name = item["name"][: col_width - 4]  # Leave room for icon and padding
                cell = f"{icon} {name}"[:col_width]
            else:
                cell = ""

            row_parts.append(f"{cell:<{col_width}}")

        print(" | ".join(row_parts))

    # Footer with counts
    footer_parts = []
    for status in ["Queued", "In-Progress", "Done"]:
        count = len(columns[status])
        footer_parts.append(f"({count})")

    print("=" * len(header))
    footer = " | ".join(f"{part:^{col_width}}" for part in footer_parts)
    print(footer)


def run(argv: list[str] | None = None, _ctx: object = None) -> int:
    argv = argv or []
    known_flags = {"--help", "-h"}

    if wants_help(argv):
        print_help(COMMAND, DESCRIPTION, USAGE)
        print("\nShows crew members and jobs organized by status:")
        print("  Queued     - Available/idle crew and pending jobs")
        print("  In-Progress - Active crew and jobs in progress")
        print("  Done       - Completed crew tasks and finished jobs")
        return 0

    if has_unknown_flags(argv, known_flags):
        print("Not found")
        print_help(COMMAND, DESCRIPTION, USAGE)
        return 0

    # Load crew status data
    crew_data = _load_crew_status()
    if not crew_data:
        print("[ℹ️] No crew status data found.")
        print("(Create crew_status.json with crew and job information)")
        return 0

    # Organize data by status
    columns = _organize_by_status(crew_data)

    # Get terminal width and choose display format
    width = _get_terminal_width()

    print("\n📋 CREW & TASK BOARD")
    print("=" * min(width, 60))

    if width < 80:
        _print_board_narrow(columns)
    else:
        _print_board_wide(columns, width)

    # Summary
    total_items = sum(len(items) for items in columns.values())
    print(f"\nTotal: {total_items} items")

    return 0
