from coterie_agents.utils.state_store import ensure_idempotent_end_job

from ._cli import has_unknown_flags, print_help, wants_help

COMMAND = "end_job"
DESCRIPTION = "End a job for a crew member (idempotent operation)."
USAGE = f"{COMMAND} <name> [--help]"


def run(argv: list[str] | None = None, _ctx: object = None) -> int:
    """CLI entrypoint for end_job command with state synchronization."""
    argv = argv or []
    known_flags = {"--help", "-h"}

    if wants_help(argv):
        print_help(COMMAND, DESCRIPTION, USAGE)
        print("\nThis command is idempotent - safe to run multiple times.")
        print("Synchronizes both crew_status.json and command_log.json")
        return 0

    if has_unknown_flags(argv, known_flags):
        print("Not found")
        print_help(COMMAND, DESCRIPTION, USAGE)
        return 0

    if not argv:
        print("[ERROR] Member name is required")
        print_help(COMMAND, DESCRIPTION, USAGE)
        return 1

    member_name = argv[0]

    try:
        # Use idempotent end job logic
        ensure_idempotent_end_job(member_name)
        return 0
    except Exception as e:
        print(f"[❌] Failed to end job: {e}")
        return 1
