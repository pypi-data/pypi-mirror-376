from __future__ import annotations

from ..authz import CONFIG_PATHS, resolve_actor, role_of
from ._cli import has_unknown_flags, print_help, wants_help

__all__ = ["run"]

COMMAND = "whoami"
DESCRIPTION = "Show current actor and role."
USAGE = "deck whoami"


def run(argv: list[str] | None = None, _ctx: dict | None = None) -> int:
    """Print current actor, role, and config path used."""
    argv = argv or []
    known = {"-h", "--help"}
    if wants_help(argv):
        print_help(COMMAND, DESCRIPTION, USAGE)
        return 0
    if has_unknown_flags(argv, known):
        print("[ERROR] Unknown flag.")
        print_help(COMMAND, DESCRIPTION, USAGE)
        return 2

    actor = resolve_actor()
    role = role_of(actor)
    config_path = next((str(p) for p in CONFIG_PATHS if p.exists()), str(CONFIG_PATHS[0]))
    print(f"Actor: {actor}\nRole: {role}\nConfig: {config_path}")
    return 0


if __name__ == "__main__":
    import sys

    exit(run(sys.argv[1:], None))
