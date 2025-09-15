from ._cli import has_unknown_flags, print_help, safe_ctx_store, wants_help

COMMAND = "log"
DESCRIPTION = "Log a message for a crew member."
USAGE = f"{COMMAND} <member> <message> [--help]"


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

    store = safe_ctx_store(ctx)
    member_name = argv[0] if argv else None
    message = " ".join(argv[1:]) if len(argv) > 1 else ""

    if not member_name or member_name not in store:
        print("Nope: not found")
        return 0

    member = store[member_name]
    display = member.get("name", member_name)
    print(f"{display}: {message}")
    return 0
