from ._cli import has_unknown_flags, print_help, wants_help

COMMAND = "test_error"
DESCRIPTION = "Test error command for CLI discipline."
USAGE = f"{COMMAND} [--help]"


# agents/commands/test_error.py
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

    raise RuntimeError("👾 Intentional test error")
