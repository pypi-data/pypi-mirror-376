"""Log job command with state synchronization."""

from __future__ import annotations

from coterie_agents.utils.state_store import reconcile_job_state

from ._cli import has_unknown_flags, print_help, wants_help

COMMAND = "log_job"
DESCRIPTION = "Log/start a job for a crew member with state synchronization."
USAGE = f"{COMMAND} <member_name> <task_description> [--help]"


def run(argv: list[str] | None = None, _ctx: object = None) -> int:
    argv = argv or []
    known_flags = {"--help", "-h"}

    if wants_help(argv):
        print_help(COMMAND, DESCRIPTION, USAGE)
        print("\nExamples:")
        print(f"  {COMMAND} Jet 'Rig wash and detail'")
        print(f"  {COMMAND} Mixie 'Final inspection'")
        print("\nThis command synchronizes both crew_status.json and command_log.json")
        return 0

    if has_unknown_flags(argv, known_flags):
        print("Not found")
        print_help(COMMAND, DESCRIPTION, USAGE)
        return 0

    if len(argv) < 2:
        print("[ERROR] Member name and task description required")
        print_help(COMMAND, DESCRIPTION, USAGE)
        return 1

    member_name = argv[0]
    task_description = " ".join(argv[1:])

    # Use state reconciliation to ensure sync
    try:
        reconcile_job_state(member_name, "start", task_description)
        print(f"[✅] Job logged for {member_name}: {task_description}")
        return 0
    except Exception as e:
        print(f"[❌] Failed to log job: {e}")
        return 1
