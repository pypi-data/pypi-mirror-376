from __future__ import annotations

import json
import os
from collections.abc import Callable
from typing import Any

from coterie_agents.utils import helper_funcs as _log

from ._cli import has_unknown_flags, print_help, wants_help


def _noop_debug_log(*args: Any, **kwargs: Any) -> None:
    return None


debug_log: Callable[..., None] = getattr(_log, "debug_log", _noop_debug_log)
primary_task = getattr(_log, "primary_task", lambda *a, **k: None)


COMMAND = "status"
CREW_FILE = "crew_status.json"
DESCRIPTION = "Display formatted table of crew member status."
USAGE = f"{COMMAND} [--help]"


def run(argv: list[str] | None = None, ctx: object | None = None) -> int:
    argv = argv or []
    known_flags = {"--help", "-h"}
    COMMAND = "status"
    DESCRIPTION = "Display formatted table of crew member status."
    USAGE = "status [--help]"
    if wants_help(argv):
        print_help(COMMAND, DESCRIPTION, USAGE)
        argv = argv or []
        known_flags = {"--help", "-h"}
        _ = ctx  # unused context for CLI/test compatibility
        if wants_help(argv):
            print_help(COMMAND, DESCRIPTION, USAGE)
            return 0
        if has_unknown_flags(argv, known_flags):
            print("Not found")
            print_help(COMMAND, DESCRIPTION, USAGE)
            return 0
        if not os.path.exists(CREW_FILE):
            print("[⚠️] No crew_status.json file found.")
            return 0
        try:
            with open(CREW_FILE) as f:
                crew_data = json.load(f)
        except Exception as e:
            debug_log(f"[❌] status - could not load crew_status: {e}")
            print("[ERROR] Failed to load crew status.")
            return 0
        if not crew_data:
            print("[ℹ️] No crew members found.")
            return 0
        header = f"{'Name':<15} {'Current Task':<30} {'Last Completed':<30} {'Status'}"
        separator = "-" * len(header)
        print("\n👥 Coterie Crew Status\n")
        print(header)
        print(separator)
        for member in crew_data:
            name = member.get("name", "")
            current_task = member.get("current_task", "")
            last_completed = member.get("last_completed", "")
            status = member.get("status", "")
            print(f"{name:<15} {current_task:<30} {last_completed:<30} {status}")
        return 0  # always return int for lint/type compliance
