from __future__ import annotations

from ..authz import ROLE_ORDER
from ._cli import has_unknown_flags, print_help, wants_help

__all__ = ["run"]

COMMAND = "roles"
DESCRIPTION = "Show role hierarchy and command minimums."
USAGE = "deck roles"


def run(argv: list[str] | None = None, _ctx: dict | None = None) -> int:
    """Print permissions table from the router."""
    from coterie_agents.command_router import COMMAND_ROLES

    argv = argv or []
    known = {"-h", "--help"}
    if wants_help(argv):
        print_help(COMMAND, DESCRIPTION, USAGE)
        return 0
    if has_unknown_flags(argv, known):
        print("[ERROR] Unknown flag.")
        print_help(COMMAND, DESCRIPTION, USAGE)
        return 2

    print("Command         | Required Role")
    print("----------------|--------------")
    for cmd, role in sorted(COMMAND_ROLES.items()):
        print(f"{cmd:15} | {role}")
    print("\nRole hierarchy: " + " < ".join(ROLE_ORDER))
    return 0


if __name__ == "__main__":
    import sys

    exit(run(sys.argv[1:], None))
