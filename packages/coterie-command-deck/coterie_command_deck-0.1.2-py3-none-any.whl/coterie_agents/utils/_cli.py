"""CLI utility functions for command modules."""


def wants_help(argv: list[str]) -> bool:
    """Check if user wants help."""
    return not argv or "--help" in argv or "-h" in argv


def has_unknown_flags(argv: list[str], known_flags: list[str]) -> bool:
    """Check if there are unknown flags in argv."""
    if not argv:
        return False

    return any(arg.startswith("-") and arg not in known_flags for arg in argv)


def print_help(command_name: str, usage: str) -> None:
    """Print help message for a command."""
    print(f"Usage: {command_name} {usage}")


def debug_log(message: str) -> None:
    """Simple debug logging fallback."""
    print(f"[DEBUG] {message}")
