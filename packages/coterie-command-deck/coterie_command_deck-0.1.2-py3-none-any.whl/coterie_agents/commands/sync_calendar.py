from __future__ import annotations

import os
from collections.abc import Callable
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

try:
    from googleapiclient.discovery import build
except ImportError:
    build = None  # type: ignore

from coterie_agents.utils import helper_funcs as _log

from ._cli import has_unknown_flags, print_help, wants_help

COMMAND = "sync_calendar"
DESCRIPTION = "Sync calendar events (dry-run only; no network calls)."
USAGE = f"{COMMAND} [--clear] [--help]"


def _noop_debug_log(*_args: Any, **_kwargs: Any) -> None:
    return None


debug_log: Callable[..., None] = getattr(_log, "debug_log", _noop_debug_log)

BOOKING_FILE = "bookings.json"
TOKEN_PATH = Path(
    os.environ.get("COTERIE_TOKEN_FILE", "~/.config/coterie/token.pickle")
).expanduser()
CALENDAR_ID = "primary"  # Or specify a calendar ID


def run(argv: list[str] | None = None, ctx: object | None = None) -> int:
    _ = ctx
    argv = argv or []
    rc = 0
    try:
        known = {"--help", "-h", "--clear"}
        if wants_help(argv):
            print_help(COMMAND, DESCRIPTION, USAGE)
            return 0
        if has_unknown_flags(argv, known):
            print("Not found")
            print_help(COMMAND, DESCRIPTION, USAGE)
            return 0

        clear = "--clear" in argv
        bookings = _load_bookings()
        _dry_run_sync(bookings, clear)
    except Exception as e:
        print(f"[❌] {COMMAND} failed: {e}")
        rc = 1
    return rc


def _load_bookings() -> list[dict[str, Any]]:
    # Minimal local JSON loader to replace missing _read_json
    import json

    try:
        with open(BOOKING_FILE, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def _dry_run_sync(bookings: list[dict[str, Any]], clear: bool) -> None:
    if clear:
        print("[DRY-RUN] Would clear events for next 30 days.")
    TZ = "UTC"
    for b in bookings:
        start = datetime.fromisoformat(b["datetime"])
        end = start + timedelta(hours=1)
        print(
            f"[DRY-RUN] Would create '{b['customer']} ({b['tier']})' "
            f"{start.isoformat()}  {end.isoformat()} ({TZ})"
        )
