from ._cli import has_unknown_flags, print_help, wants_help


def run(argv: list[str] | None = None, ctx: object | None = None):
    argv = argv or []
    known_flags = {"--help", "-h"}
    COMMAND = "exit"
    DESCRIPTION = "Exit the Command Deck gracefully."
    USAGE = "exit [--help]"
    if wants_help(argv):
        print_help(COMMAND, DESCRIPTION, USAGE)
        return 0
    if has_unknown_flags(argv, known_flags):
        print("Not found")
        print_help(COMMAND, DESCRIPTION, USAGE)
        return 0
    """
    Exits the Command Deck gracefully.
    """
    print("[👋] Exiting Command Deck.")
    exit(0)
