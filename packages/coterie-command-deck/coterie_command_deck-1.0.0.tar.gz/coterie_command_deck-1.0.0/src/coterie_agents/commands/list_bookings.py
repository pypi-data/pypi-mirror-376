from __future__ import annotations

import json
import os
from collections.abc import Callable
from datetime import datetime
from typing import Any

from coterie_agents.utils import helper_funcs as _log

from ._cli import has_unknown_flags, print_help, wants_help

COMMAND = "list_bookings"
DESCRIPTION = "List upcoming bookings with full details."
USAGE = f"{COMMAND} [--limit N] [--all] [--help]"


def _noop_debug_log(*args: Any, **kwargs: Any) -> None:
    return None


debug_log: Callable[..., None] = getattr(_log, "debug_log", _noop_debug_log)

BOOKING_FILE = "bookings.json"


def run(argv: list[str] | None = None) -> int:
    """
    List upcoming bookings with full details.
    Usage: list_bookings [--limit N] [--all]
    """
    argv = argv or []
    known_flags = {"--help", "-h"}
    if wants_help(argv):
        print_help(COMMAND, DESCRIPTION, USAGE)
        return 0
    if has_unknown_flags(argv, known_flags):
        print("Not found")
        print_help(COMMAND, DESCRIPTION, USAGE)
        return 0

    def parse_args(argv: list[str]):
        limit = 10
        show_all = False
        if "--limit" in argv:
            try:
                idx = argv.index("--limit")
                if idx + 1 < len(argv):
                    limit = int(argv[idx + 1])
            except Exception as e:
                debug_log(f"[❌] list_bookings - bad limit arg: {argv} error: {e}")
        if "--all" in argv:
            show_all = True
        return limit, show_all

    def filter_bookings(
        bookings: list[dict[str, Any]], show_all: bool
    ) -> tuple[list[tuple[datetime, dict[str, Any]]], datetime]:
        valid: list[tuple[datetime, dict[str, Any]]] = []
        now = datetime.now()
        for b in bookings:
            try:
                dt_str: str = b.get("datetime", "")
                dt = datetime.fromisoformat(dt_str)
                if show_all or dt >= now:
                    valid.append((dt, b))
            except Exception:
                debug_log(f"[❌] list_bookings - bad datetime: {b.get('datetime')}")
        return valid, now

    limit, show_all = parse_args(argv)
    if not os.path.exists(BOOKING_FILE):
        print("[ℹ️] No bookings found.")
        return 0
    try:
        with open(BOOKING_FILE) as f:
            bookings: list[dict[str, Any]] = json.load(f)
    except Exception as e:
        debug_log(f"[❌] list_bookings - could not read bookings: {e}")
        print("[ERROR] Failed to load bookings.")
        return 0
    valid, now = filter_bookings(bookings, show_all)
    if not valid:
        status = "bookings" if show_all else "upcoming bookings"
        print(f"[ℹ️] No valid {status} to display.")
        return 0
    valid.sort(key=lambda x: x[0])
    display_bookings: list[tuple[datetime, dict[str, Any]]] = (
        valid[:limit] if not show_all else valid
    )
    status_text = (
        f"All Bookings ({len(display_bookings)})"
        if show_all
        else f"Upcoming Bookings (next {len(display_bookings)})"
    )
    print(f"\n📅 {status_text}:\n")
    header = f"{'Date/Time':<20} {'Customer':<20} {'Tier':<12} {'Size':<8} {'#':<4} {'Location':<15} {'Total':<8}"
    separator = "-" * len(header)
    print(header)
    print(separator)
    for dt, b in display_bookings:
        customer = b.get("customer", "Unknown")[:19]
        tier = b.get("tier", "")
        size = b.get("size", "")
        vehicles = str(b.get("vehicles", ""))
        location = b.get("location", "")[:14]
        total = b.get("total_price", 0)
        days_away = (dt - now).days
        time_str = dt.strftime("%Y-%m-%d %H:%M")
        if not show_all:
            if days_away == 0:
                time_str = dt.strftime("%Y-%m-%d %H:%M") + "*"
            elif days_away == 1:
                time_str = dt.strftime("%Y-%m-%d %H:%M") + "+"
        price_str = f"${total}" if total > 0 else "Quote"
        print(
            f"{time_str:<20} {customer:<20} {tier:<12} {size:<8} {vehicles:<4} {location:<15} {price_str:<8}"
        )
    if not show_all:
        print(f"\n[ℹ️] Showing next {len(display_bookings)} upcoming bookings.")
        print("[ℹ️] Use 'list_bookings --all' to see all bookings or '--limit N' to change count.")
        print("[ℹ️] * = today, + = tomorrow")
    else:
        print(f"\n[ℹ️] Total bookings: {len(display_bookings)}")
    return 0
