from __future__ import annotations

from coterie_agents.utils.helper_funcs import (  # type: ignore[attr-defined]
    load_crew_status,
    log_command_to_json,
    resolve_crew_name,
    save_crew_status,
    set_primary_task,
)

from ._cli import has_unknown_flags, print_help, wants_help

COMMAND = "edit_task"
DESCRIPTION = "Edit an existing assigned task for a crew member."
USAGE = "edit_task <crew_member> <old_task> <new_task>"


def run(argv: list[str] | None = None, ctx: object | None = None) -> int:
    argv = argv or []
    known_flags = {"--help", "-h"}

    if wants_help(argv):
        print_help(COMMAND, DESCRIPTION, USAGE)
        return 0

    if has_unknown_flags(argv, known_flags):
        print("Not found")
        print_help(COMMAND, DESCRIPTION, USAGE)
        return 0

    if len(argv) < 3:
        print(f"[!!] Usage: {USAGE}")
        return 1

    raw_name = argv[0]
    old_task = argv[1]
    new_task = " ".join(argv[2:]).strip()

    log_command_to_json(COMMAND, argv)
    crew_name = resolve_crew_name(raw_name)  # type: ignore
    crew_status = load_crew_status()  # type: ignore

    if not crew_name or crew_name not in crew_status:
        print(f"[⚠️] {raw_name} not found in crew status.")
        return 1

    current_task = (
        crew_status[crew_name].get("tasks", [""])[0]  # type: ignore
        if crew_status[crew_name].get("tasks")  # type: ignore
        else ""
    )
    if isinstance(current_task, str) and current_task.lower() != old_task.lower():
        print(
            f"[⚠️] Current task for {crew_name} is '{current_task}', not '{old_task}'. Overwriting anyway."
        )

    set_primary_task(crew_status[crew_name], new_task)  # type: ignore
    save_crew_status(crew_status)  # type: ignore
    print(f"[✏️] Updated task for {crew_name}: '{new_task}'")
    return 0
