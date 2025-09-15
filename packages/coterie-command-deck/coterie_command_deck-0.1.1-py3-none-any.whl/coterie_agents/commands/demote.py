from __future__ import annotations

from typing import cast

from coterie_agents.utils import helper_funcs as _log

from ._cli import has_unknown_flags, print_help, wants_help


def _noop_debug_log(*_a, **_k):
    return None


debug_log = getattr(_log, "debug_log", _noop_debug_log)
load_crew_status = getattr(_log, "load_crew_status", lambda: {})
log_command_to_json = getattr(_log, "log_command_to_json", lambda *a, **k: None)
resolve_crew_name = getattr(_log, "resolve_crew_name", lambda x: x)
save_crew_status = getattr(_log, "save_crew_status", lambda x: None)

COMMAND = "demote"
DESCRIPTION = "Demote a crew member to a lower status/rank."
USAGE = f"{COMMAND} <crew_member> --to <new_status> [--help]"


def run(argv: list[str] | None = None) -> int:
    argv = argv or []
    known_flags = {"--help", "-h"}
    if wants_help(argv):
        print_help(COMMAND, DESCRIPTION, USAGE)
        return 0
    if has_unknown_flags(argv, known_flags):
        print("Not found")
        print_help(COMMAND, DESCRIPTION, USAGE)
        return 1
    if not argv or "--to" not in argv:
        print_help(COMMAND, DESCRIPTION, USAGE)
        return 1
    try:
        idx = argv.index("--to")
        raw_name = argv[0] if argv else ""
        new_status = argv[idx + 1] if len(argv) > idx + 1 else ""
    except Exception:
        print_help(COMMAND, DESCRIPTION, USAGE)
        return 1
    log_command_to_json(COMMAND, argv)
    crew_name = resolve_crew_name(raw_name)
    crew_status = cast(dict[str, dict], load_crew_status())
    if not crew_name or crew_name not in crew_status:
        print(f"[⚠️] {raw_name} not found in crew status.")
        return 1
    old_status = crew_status[crew_name].get("status", "UNKNOWN")
    crew_status[crew_name]["status"] = new_status.strip()
    save_crew_status(crew_status)
    print(f"[⬇️] Demoted {crew_name} from {old_status} to {new_status}")
    debug_log(f"[demote] {crew_name} demoted from {old_status} to {new_status}")
    return 0
