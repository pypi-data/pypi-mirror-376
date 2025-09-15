"""Replay command - re-run commands from history log."""

from __future__ import annotations

import json
import os
from typing import Any

from ._cli import has_unknown_flags, print_help, wants_help

LOG_FILE = "command_log.json"

COMMAND = "replay"
DESCRIPTION = "Replay a command from history by log ID."
USAGE = f"{COMMAND} <log_id> [--force] [--help]"

# Commands that modify state and require --force
STATE_CHANGING_COMMANDS = {
    "book",
    "assign",
    "log_job",
    "end_job",
    "update_status",
    "add_crew",
    "edit_task",
    "start_job",
    "notify",
}


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


def _sanitize_args(args: list[Any]) -> list[str]:
    """Sanitize command arguments for safe replay."""
    sanitized = []
    for arg in args:
        # Convert to string and basic sanitization
        arg_str = str(arg).strip()

        # Skip potentially dangerous arguments
        if arg_str.startswith("--") and "token" in arg_str.lower():
            continue
        if arg_str.startswith("--") and "password" in arg_str.lower():
            continue
        if arg_str.startswith("--") and "key" in arg_str.lower():
            continue

        sanitized.append(arg_str)

    return sanitized


def _is_state_changing(command: str) -> bool:
    """Check if a command modifies state."""
    return command.lower() in STATE_CHANGING_COMMANDS


def _execute_command(command: str, args: list[str]) -> int:
    """Execute a command with the given arguments."""
    # Import the command router to execute the command
    try:
        from coterie_agents.command_router import COMMANDS

        # Find the command function
        command_func = COMMANDS.get(command)
        if not command_func:
            print(f"[❌] Command not found: {command}")
            return 1

        # Execute the command
        print(f"[🔄] Replaying: {command} {' '.join(args)}")
        result = command_func(args)
        return result if isinstance(result, int) else 0

    except Exception as e:
        print(f"[❌] Failed to replay command: {e}")
        return 1


def run(argv: list[str] | None = None, _ctx: object = None) -> int:
    argv = argv or []
    known_flags = {"--help", "-h", "--force"}

    if wants_help(argv):
        print_help(COMMAND, DESCRIPTION, USAGE)
        print("\nReplays a command from the history log.")
        print("State-changing commands require --force flag for safety.")
        print(f"\nState-changing commands: {', '.join(sorted(STATE_CHANGING_COMMANDS))}")
        print("\nExamples:")
        print(f"  {COMMAND} 5              # Replay log entry #5 (if read-only)")
        print(f"  {COMMAND} 5 --force      # Replay log entry #5 (even if state-changing)")
        return 0

    if has_unknown_flags(argv, known_flags):
        print("Not found")
        print_help(COMMAND, DESCRIPTION, USAGE)
        return 0

    # Parse arguments
    if not argv or argv[0].startswith("--"):
        print("[ERROR] Log ID is required")
        print_help(COMMAND, DESCRIPTION, USAGE)
        return 1

    log_id = argv[0]
    force = "--force" in argv

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

    # Extract command details
    command = entry.get("command", "")
    raw_args = entry.get("args", [])

    if not command:
        print(f"[❌] No command found in log entry {log_id}")
        return 1

    # Sanitize arguments
    args = _sanitize_args(raw_args)

    # Check if command is state-changing
    if _is_state_changing(command) and not force:
        print(f"[⚠️] Command '{command}' modifies state and requires --force flag")
        print(f"[ℹ️] Original command: {command} {' '.join(str(arg) for arg in raw_args)}")
        print(f"[ℹ️] Use: {COMMAND} {log_id} --force")
        return 1

    # Show what we're about to replay
    print(f"[📋] Replaying log entry #{log_id}:")
    print(f"    Original: {command} {' '.join(str(arg) for arg in raw_args)}")
    print(f"    Sanitized: {command} {' '.join(args)}")

    if _is_state_changing(command):
        print("[⚠️] This command may modify system state!")

    # Execute the command
    return _execute_command(command, args)
