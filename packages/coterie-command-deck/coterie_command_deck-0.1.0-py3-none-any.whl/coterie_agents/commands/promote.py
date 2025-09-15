# agents/commands/promote.py – Command module for 'promote'

from coterie_agents.utils.helper_funcs import (
    load_crew_status,
    log_command_to_json,
    resolve_crew_name,
    save_crew_status,
)

from ._cli import has_unknown_flags, print_help, wants_help

COMMAND = "promote"
DESCRIPTION = "Promote a crew member to a new status or rank."
USAGE = f"{COMMAND} <crew_member> --to <new_status>"


def run(argv: list[str] | None = None, ctx: object = None) -> int:
    argv = argv or []
    known_flags = {"--help", "-h", "--to"}

    if wants_help(argv):
        print_help(COMMAND, DESCRIPTION, USAGE)
        return 0

    if has_unknown_flags(argv, known_flags):
        print("Not found")
        print_help(COMMAND, DESCRIPTION, USAGE)
        return 0

    if not argv or len(argv) < 3 or "--to" not in argv:
        print_help(COMMAND, DESCRIPTION, USAGE)
        return 0

    try:
        name_idx = 0
        to_idx = argv.index("--to")
        raw_name = argv[name_idx]
        new_status = argv[to_idx + 1] if to_idx + 1 < len(argv) else ""
    except Exception:
        print_help(COMMAND, DESCRIPTION, USAGE)
        return 0

    log_command_to_json(COMMAND, argv)
    crew_name = resolve_crew_name(raw_name)
    crew_status = load_crew_status()

    if not crew_name or crew_name not in crew_status:
        print(f"[⚠️] {raw_name} not found in crew status.")
        return 0

    old_status = crew_status[crew_name].get("status", "UNKNOWN")
    crew_status[crew_name]["status"] = new_status.strip()
    save_crew_status(crew_status)
    print(f"[⬆️] Promoted {crew_name} from {old_status} to {new_status}")
    return 0
