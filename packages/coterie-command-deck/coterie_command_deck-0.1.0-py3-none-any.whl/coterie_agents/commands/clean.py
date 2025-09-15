# clean.py - Command module for 'clean'

from __future__ import annotations

from ._cli import has_unknown_flags, print_help, wants_help

COMMAND = "clean"
DESCRIPTION = "Clear the member's tasks list."
USAGE = f"{COMMAND} <member> [--help]"


def run(arg: dict | list | None = None) -> dict | int:
    """
    Dual API/CLI entrypoint:
    - If arg is a Crew dict, clear its 'tasks' and return it (API mode)
    - If arg is a list (CLI argv), run CLI logic and return int
    """
    if isinstance(arg, dict) and "tasks" in arg:
        # API mode: clear tasks and return mutated Crew
        arg["tasks"] = []
        return arg
    argv = arg or []
    known_flags = {"--help", "-h"}
    if wants_help(argv):
        print_help(COMMAND, DESCRIPTION, USAGE)
        return 0
    if has_unknown_flags(argv, known_flags):
        print("Not found")
        print_help(COMMAND, DESCRIPTION, USAGE)
        return 0
    print("[✅] Loaded command: clean")
    # CLI stub; actual cleaning logic would require context/member
    return 0
