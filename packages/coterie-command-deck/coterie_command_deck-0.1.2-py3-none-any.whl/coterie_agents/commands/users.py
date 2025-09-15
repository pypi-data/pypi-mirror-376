from __future__ import annotations

from ..authz import ROLE_ORDER, USERS
from ._cli import has_unknown_flags, print_help, wants_help

__all__ = ["run"]

COMMAND = "users"
DESCRIPTION = "List configured users by role."
USAGE = "deck users"


def run(argv: list[str] | None = None, _ctx: dict | None = None) -> int:
    """List configured users by role."""
    argv = argv or []
    known = {"-h", "--help"}
    if wants_help(argv):
        print_help(COMMAND, DESCRIPTION, USAGE)
        return 0
    if has_unknown_flags(argv, known):
        print("[ERROR] Unknown flag.")
        print_help(COMMAND, DESCRIPTION, USAGE)
        return 2

    for role in ROLE_ORDER[::-1]:
        users = USERS.get(role, [])
        print(f"{role.title():7}: {', '.join(users) if users else '(none)'}")
    return 0


if __name__ == "__main__":
    import sys

    exit(run(sys.argv[1:], None))
