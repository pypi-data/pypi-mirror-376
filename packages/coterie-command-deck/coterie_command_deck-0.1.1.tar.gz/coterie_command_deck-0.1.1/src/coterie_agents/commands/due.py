"""
due.py – Command module for 'due'
"""

import json
import os
from datetime import datetime

from ._cli import has_unknown_flags, print_help, wants_help


# Fallback debug_log function
def debug_log(message: str) -> None:
    """Fallback debug logging when helper_funcs is not available."""
    print(f"DEBUG: {message}")


CREW_FILE = "crew_status.json"
LOG_FILE = "command_log.jsonl"


def run(argv: list[str] | None = None) -> int:
    """
    CLI entrypoint for the 'due' command.
    Usage: due <crew_member> <due_time> [--help]
    """
    COMMAND = "due"
    DESCRIPTION = "Set a due time for a crew member's current task."
    USAGE = "due <crew_member> <due_time> [--help]"
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
        print("[ERROR] Usage: due <crew_member> <due_time>")
        return 1

    member = argv[0]
    raw_due = " ".join(argv[1:])

    # Minimal due time parsing (ISO only)
    try:
        due_dt = datetime.fromisoformat(raw_due)
    except Exception:
        print("[ERROR] Could not parse due_time. Use ISO format.")
        return 1

    # Load and update crew status
    try:
        if not os.path.exists(CREW_FILE):
            print("[ERROR] No crew_status.json file found.")
            return 1

        with open(CREW_FILE) as f:
            crew_data = json.load(f)

        member_data = crew_data.get(member)
        if not member_data or "task" not in member_data:
            print(f"[ERROR] No active task for {member}.")
            return 1

        member_data["due_time"] = due_dt.isoformat()

        with open(CREW_FILE, "w") as f:
            json.dump(crew_data, f, indent=2)

    except Exception as e:
        debug_log(f"[❌] due - could not update crew_status: {e}")
        print("[ERROR] Failed to set due time.")
        return 1

    # Log the command
    log_entry = {
        "command": "due",
        "member": member,
        "due_time": due_dt.isoformat(),
        "timestamp": datetime.now().isoformat(),
    }

    try:
        with open(LOG_FILE, "a") as f:
            f.write(json.dumps(log_entry) + "\n")
    except Exception as e:
        debug_log(f"[❌] due - could not write log: {e}")

    print(f"[✅] Due time for {member}'s task set to {due_dt.strftime('%Y-%m-%d %H:%M')}.")
    return 0
