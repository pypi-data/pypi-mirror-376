from __future__ import annotations

from ._cli import has_unknown_flags, print_help, wants_help

COMMAND = "mark"
DESCRIPTION = "Mark a crew member with a flag (e.g., done/busy/attention)."
USAGE = f"{COMMAND} <member> <flag> [--help]"


def register():
    print("[✅] Loaded command: mark")


def run(argv: list[str] | None = None) -> int:
    import os
    import sys

    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../src")))
    try:
        from coterie_agents.utils.helper_funcs import (
            load_crew_status,
            log_command_to_json,
            resolve_crew_name,
            save_crew_status,
        )
    except ImportError:
        print("[ERROR] Could not import helper functions.")
        return 0
    argv = argv or []
    known_flags = {"--help", "-h"}

    # Dynamic import for helper functions
    import importlib

    helper_mod = None
    try:
        helper_mod = importlib.import_module("src.coterie_agents.utils.helper_funcs")
    except ModuleNotFoundError:
        try:
            helper_mod = importlib.import_module("coterie_agents.utils.helper_funcs")
        except ModuleNotFoundError:
            print("[ERROR] Could not import helper functions.")
            return 0

    load_crew_status = getattr(helper_mod, "load_crew_status", None)
    log_command_to_json = getattr(helper_mod, "log_command_to_json", None)
    resolve_crew_name = getattr(helper_mod, "resolve_crew_name", None)
    save_crew_status = getattr(helper_mod, "save_crew_status", None)
    if not all([load_crew_status, log_command_to_json, resolve_crew_name, save_crew_status]):
        print("[ERROR] Helper functions missing.")
        return 0

    if wants_help(argv):
        print_help(COMMAND, DESCRIPTION, USAGE)
        return 0
    if has_unknown_flags(argv, known_flags):
        print("Not found")
        print_help(COMMAND, DESCRIPTION, USAGE)
        return 0
    if len(argv) < 2:
        print_help(COMMAND, DESCRIPTION, USAGE)
        return 0

    crew_name = resolve_crew_name(argv[0])
    flag = " ".join(argv[1:]).strip()
    log_command_to_json(COMMAND, argv)
    crew_status = load_crew_status()
    if crew_name in crew_status:
        crew_status[crew_name]["flag"] = flag
        save_crew_status(crew_status)
        print(f"[🚩] {crew_name} flagged with {flag}")
    else:
        print(f"[⚠️] {crew_name} not found in crew status")
    return 0
