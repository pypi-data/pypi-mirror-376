from __future__ import annotations

from collections.abc import Iterable

from ._cli import has_unknown_flags, print_help, wants_help


def _desc_map(avail: Iterable[tuple[str, str]]) -> dict[str, str]:
    try:
        return dict(avail)
    except Exception:
        return {}


def run(argv: list[str] | None = None, ctx: object | None = None) -> int:
    _ = ctx
    argv = argv or []
    rc = 0
    COMMAND = "help_cmd"
    DESCRIPTION = "Show help for available commands."
    USAGE = "help_cmd [--help]"
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
