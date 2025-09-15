from __future__ import annotations

# stdlib
import os
from collections.abc import Callable
from pathlib import Path
from typing import Any

# first-party
from ._cli import has_unknown_flags, print_help, wants_help


def _noop_debug_log(*_a: Any, **_k: Any) -> None:
    return None


debug_log: Callable[..., None] = _noop_debug_log

COMMAND = "calendar_auth"
DESCRIPTION = "Show calendar auth token status (dry-run; no network)."
USAGE = f"{COMMAND} [--help]"

# Env override; defaults to user config dir
TOKEN_PATH = Path(
    os.environ.get("COTERIE_TOKEN_FILE", "~/.config/coterie/token.pickle")
).expanduser()


def run(argv: list[str] | None = None, ctx: Any | None = None) -> int:
    argv = argv or []
    known_flags = {"--help", "-h"}

    if wants_help(argv):
        print_help(COMMAND, DESCRIPTION, USAGE)
        return 0

    if has_unknown_flags(argv, known_flags):
        print("Not found")
        print_help(COMMAND, DESCRIPTION, USAGE)
        return 0

    # Dry-run status: no network, no pickle loads; just show the path.
    exists = TOKEN_PATH.exists()
    print("🗓️  Calendar Authorization (dry-run)")
    print(f"Path : {TOKEN_PATH}")
    print(f"State: {'present' if exists else 'missing'}")
    if not exists:
        print("Hint: set COTERIE_TOKEN_FILE to a local token path if needed.")
    debug_log(f"[calendar_auth] token at {TOKEN_PATH} exists={exists}")
    return 0
