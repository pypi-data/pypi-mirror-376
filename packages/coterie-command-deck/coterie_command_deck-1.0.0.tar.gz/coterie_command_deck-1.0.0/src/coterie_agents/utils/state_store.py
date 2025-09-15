"""State store utilities for idempotent log and crew synchronization."""

from __future__ import annotations

import json
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any

CREW_STATUS_FILE = "crew_status.json"
COMMAND_LOG_FILE = "command_log.json"

LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / "coterie.log"
MAX_LOG_SIZE = 5 * 1024 * 1024  # 5MB
MAX_LOG_DAYS = 7

SCHEMA_VERSION = 1

BACKUP_DIR = Path.home() / ".coterie" / "backups"
BACKUP_DIR.mkdir(parents=True, exist_ok=True)


def migrate_crew_status(data: dict[str, Any]) -> dict[str, Any]:
    """Migrate crew status to latest schema version."""
    if data.get("schema_version") != SCHEMA_VERSION:
        # Example migration logic (expand as needed)
        data["schema_version"] = SCHEMA_VERSION
    return data


def load_crew_status() -> dict[str, Any]:
    """Load crew status from JSON file."""
    if not os.path.exists(CREW_STATUS_FILE):
        return {"crew": {}, "jobs": [], "schema_version": SCHEMA_VERSION}
    try:
        with open(CREW_STATUS_FILE) as f:
            data = json.load(f)
        # Ensure required structure
        if not isinstance(data, dict):
            return {"crew": {}, "jobs": [], "schema_version": SCHEMA_VERSION}
        data.setdefault("crew", {})
        data.setdefault("jobs", [])
        data = migrate_crew_status(data)
        return data
    except Exception:
        return {"crew": {}, "jobs": [], "schema_version": SCHEMA_VERSION}


def save_crew_status(data: dict[str, Any]) -> bool:
    """Save crew status to JSON file."""
    try:
        data = migrate_crew_status(data)
        with open(CREW_STATUS_FILE, "w") as f:
            json.dump(data, f, indent=2)
        return True
    except Exception:
        return False


def load_command_log() -> list[dict[str, Any]]:
    """Load command log entries."""
    if not os.path.exists(COMMAND_LOG_FILE):
        return []

    try:
        with open(COMMAND_LOG_FILE) as f:
            data = json.load(f)

        # Handle both list and dict formats
        if isinstance(data, dict):
            return data.get("entries", [])
        elif isinstance(data, list):
            return data
        else:
            return []
    except Exception:
        return []


def save_command_log(entries: list[dict[str, Any]]) -> bool:
    """Save command log entries."""
    try:
        with open(COMMAND_LOG_FILE, "w") as f:
            json.dump(entries, f, indent=2)
        return True
    except Exception:
        return False


def add_log_entry(command: str, args: list[str], **kwargs: Any) -> dict[str, Any]:
    """Add a new log entry and return it."""
    entry = {
        "timestamp": datetime.now().isoformat(),
        "command": command,
        "args": args,
        **kwargs,
    }

    # Load existing entries
    entries = load_command_log()

    # Add ID if not present
    if "id" not in entry:
        entry["id"] = len(entries) + 1

    # Add new entry
    entries.append(entry)

    # Save back
    save_command_log(entries)

    return entry


def update_crew_member(name: str, updates: dict[str, Any]) -> dict[str, Any] | None:
    """Update crew member status and return the updated member."""
    crew_data = load_crew_status()

    if name not in crew_data["crew"]:
        # Create new member
        crew_data["crew"][name] = {
            "name": name,
            "role": "crew",
            "status": "idle",
            "tasks": [],
            "last_updated": datetime.now().isoformat(),
        }

    # Apply updates
    member = crew_data["crew"][name]
    for key, value in updates.items():
        member[key] = value

    member["last_updated"] = datetime.now().isoformat()

    # Save back
    save_crew_status(crew_data)

    return member


def reconcile_job_state(member_name: str, action: str, task: str | None = None) -> None:
    """Reconcile crew status and command log for job state changes."""

    if action == "start":
        # Update crew member
        updates = {
            "status": "active",
        }
        if task:
            member = update_crew_member(member_name, {})
            if member:  # Ensure member is not None
                current_tasks = member.get("tasks", [])
                if task not in current_tasks:
                    current_tasks.insert(0, task)  # Add to front as primary task
                updates["tasks"] = current_tasks

        update_crew_member(member_name, updates)

        # Add log entry
        args = [member_name]
        if task:
            args.append(task)
        add_log_entry("start_job", args, assignee=member_name, task=task)

    elif action == "end":
        # Get current member state
        crew_data = load_crew_status()
        member = crew_data["crew"].get(member_name, {})
        current_tasks = member.get("tasks", [])

        # Complete primary task
        completed_task = current_tasks[0] if current_tasks else task

        updates = {
            "status": "idle",
            "tasks": current_tasks[1:] if current_tasks else [],
        }
        if completed_task:
            updates["last_completed"] = completed_task

        update_crew_member(member_name, updates)

        # Add log entry
        add_log_entry(
            "end_job",
            [member_name],
            assignee=member_name,
            completed_task=completed_task,
        )


def ensure_idempotent_end_job(member_name: str) -> bool:
    """Safely end job, returns True if state changed."""
    crew_data = load_crew_status()
    member = crew_data["crew"].get(member_name, {})

    # If already idle with no primary task, no-op
    if member.get("status") == "idle" and not member.get("tasks"):
        print(f"[ℹ️] {member_name} is already idle with no active tasks.")
        return False

    # If has active task, complete it
    if member.get("tasks"):
        reconcile_job_state(member_name, "end")
        print(f"[✅] Job ended for {member_name}")
        return True

    # Just mark as idle if was active but no tasks
    if member.get("status") != "idle":
        update_crew_member(member_name, {"status": "idle"})
        print(f"[✅] {member_name} marked as idle")
        return True

    return False


def rotate_logs():
    """Rotate JSONL logs daily and by size, keep last N days."""
    if LOG_FILE.exists() and LOG_FILE.stat().st_size > MAX_LOG_SIZE:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        rotated = LOG_DIR / f"coterie_{ts}.log"
        shutil.move(str(LOG_FILE), str(rotated))
    # Remove old logs
    logs = sorted(LOG_DIR.glob("coterie_*.log"), key=lambda p: p.stat().st_mtime, reverse=True)
    for old in logs[MAX_LOG_DAYS:]:
        old.unlink()


def backup_nightly():
    """Backup crew_status.json and logs to ~/.coterie/backups/ (run nightly)."""
    ts = datetime.now().strftime("%Y%m%d")
    # Backup crew_status.json
    src = Path(CREW_STATUS_FILE)
    if src.exists():
        shutil.copy2(str(src), str(BACKUP_DIR / f"crew_status_{ts}.json"))
    # Backup logs
    for log in LOG_DIR.glob("*.log"):
        shutil.copy2(str(log), str(BACKUP_DIR / f"{log.stem}_{ts}.log"))
