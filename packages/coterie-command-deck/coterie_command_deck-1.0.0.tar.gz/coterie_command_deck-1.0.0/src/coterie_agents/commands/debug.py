import json

from ._cli import has_unknown_flags, print_help, wants_help

COMMAND = "debug"
DESCRIPTION = "Dump the current context and loaded commands for debugging."
USAGE = "debug [--help]"


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
    context_dict = ctx if isinstance(ctx, dict) else {}
    router = context_dict.get("router") if context_dict else None
    if not router:
        print("[❗] Router not found in context.")
        return 0
    context_serializable = {}
    for k, v in context_dict.items():
        if k == "router":
            context_serializable[k] = "<CommandRouter instance>"
        else:
            try:
                json.dumps(v)
                context_serializable[k] = v
            except (TypeError, OverflowError):
                context_serializable[k] = str(v)
    state = {
        "context": context_serializable,
        "commands": getattr(router, "get_available_commands", lambda: [])(),
    }
    print("[🛠️] DEBUG DUMP:")
    print(json.dumps(state, indent=2, default=str))
    return 0
