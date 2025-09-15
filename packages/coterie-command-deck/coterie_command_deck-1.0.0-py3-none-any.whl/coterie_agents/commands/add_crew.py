# agents/commands/add_crew.py - Command module for 'add_crew'
from __future__ import annotations

from ._cli import has_unknown_flags, print_help, wants_help

COMMAND = "add_crew"
DESCRIPTION = "Add a new crew member to the system."
USAGE = "add_crew <name> <role>"


def run(argv: list[str] | None = None, ctx: object | None = None) -> int:
    _ = ctx  # ctx consumed for SonarLint compliance
    argv = argv or []
    rc = 0
    known = {"--help", "-h"}
    try:
        if wants_help(argv):
            print_help(COMMAND, DESCRIPTION, USAGE)
            return 0
        if has_unknown_flags(argv, known):
            print("Not found")
            print_help(COMMAND, DESCRIPTION, USAGE)
            return 0
        if len(argv) < 2:
            print(f"[!!] Usage: {USAGE}")
            return 1
        name = argv[0]
        role = argv[1]
        _crew = {
            "name": name,
            "role": role,
            "status": "idle",
            "tasks": [],
            "last_completed": None,
            "attachments": [],
            "flag": False,
        }
        # NOTE: Implement store logic (e.g., save to crew_status.json)
        print(f"[✅] Crew member added: {name} ({role})")
    except Exception as e:
        print(f"[❌] add_crew failed: {e}")
        rc = 1
    return rc
