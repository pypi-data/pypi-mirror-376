from ._cli import has_unknown_flags, print_help, safe_ctx_store, wants_help

COMMAND = "start_job"
DESCRIPTION = "Start a job for a crew member."
USAGE = f"{COMMAND} <name> <task> [--help]"


def run(argv: list[str] | None = None, ctx: object = None) -> int:
    argv = argv or []
    known_flags = {"--help", "-h"}

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

    name, task = argv[0], " ".join(argv[1:])
    store = safe_ctx_store(ctx)
    member = store.get(name)
    if not isinstance(member, dict):
        print("[ℹ️] No such member.")
        return 0
    member["tasks"] = [t for t in member.get("tasks", []) if str(t) != task]
    member["tasks"].insert(0, task)
    member["status"] = "busy"
    print(f"[🚀] Job started for {name}: {task}")
    return 0
