from __future__ import annotations

from ._cli import has_unknown_flags, print_help, wants_help

COMMAND = "msg"
DESCRIPTION = "Send a message to a crew member."
USAGE = f'{COMMAND} <crew_member> "<message>" [--help]'


def register():
    print("[✅] Loaded command: msg")


def run(argv: list[str] | None = None, ctx: object | None = None) -> int:
    _ = ctx
    argv = argv or []
    rc = 0
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
