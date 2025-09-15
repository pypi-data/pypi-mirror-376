from __future__ import annotations

from ._cli import has_unknown_flags, print_help, wants_help

COMMAND = "remove_crew"
DESCRIPTION = "Remove a crew member from the in-memory store."
USAGE = f"{COMMAND} <member> [--save] [--help]"


def run(argv: list[str] | None = None, ctx: object | None = None) -> int:
    _ = ctx
    argv = argv or []
    rc = 0
    COMMAND = "remove_crew"
    DESCRIPTION = "Remove a crew member from the in-memory store."
    USAGE = "remove_crew <member> [--save] [--help]"
    try:
        known = {"--help", "-h"}
        if wants_help(argv):
            print_help(COMMAND, DESCRIPTION, USAGE)
            return 0
        if has_unknown_flags(argv, known):
            print("Not found")
            print_help(COMMAND, DESCRIPTION, USAGE)
            return 0
        print_help(COMMAND, DESCRIPTION, USAGE)
    except Exception as e:
        print(f"[❌] {COMMAND} failed: {e}")
        rc = 1
    return rc
