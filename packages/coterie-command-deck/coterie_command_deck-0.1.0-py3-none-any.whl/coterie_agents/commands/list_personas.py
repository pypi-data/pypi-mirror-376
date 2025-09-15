"""List and view crew member personas and profiles (DRY-RUN by default)."""

from __future__ import annotations

import os

from ._cli import has_unknown_flags, print_help, wants_help

COMMAND = "list_personas"
DESCRIPTION = "List and view crew member personas and profiles."
USAGE = f"{COMMAND} [<member_name>] [--skills <filter>] [--role <filter>] [--help]"


def run(argv: list[str] | None = None, _ctx: object = None) -> int:
    """CLI entrypoint for list_personas command."""
    argv = argv or []
    known_flags = {"--help", "-h", "--skills", "--role"}

    if wants_help(argv):
        print_help(COMMAND, DESCRIPTION, USAGE)
        print("\nExamples:")
        print(f"  {COMMAND}                    # List all personas")
        print(f"  {COMMAND} alice              # Show alice's persona")
        print(f"  {COMMAND} --role cleaner     # List all cleaners")
        print(f"  {COMMAND} --skills windows   # List members with window skills")
        print("\nNOTE: Runs in DRY-RUN mode unless PERSONAS_ENABLED=true")
        return 0

    if has_unknown_flags(argv, known_flags):
        print("Not found")
        print_help(COMMAND, DESCRIPTION, USAGE)
        return 0

    member_name, skills_filter, role_filter = _parse_list_args(argv)

    # Check if personas are enabled
    personas_enabled = os.getenv("PERSONAS_ENABLED", "false").lower() == "true"

    if not personas_enabled:
        print("[DRY-RUN] Would list personas:")
        if member_name:
            print(f"  Show details for: {member_name}")
        if skills_filter:
            print(f"  Filter by skills: {skills_filter}")
        if role_filter:
            print(f"  Filter by role: {role_filter}")
        if not (member_name or skills_filter or role_filter):
            print("  Show all personas")
        print("  (Set PERSONAS_ENABLED=true to view real personas)")
        return 0

    # Real persona listing would go here
    try:
        personas = _list_personas(member_name, skills_filter, role_filter)
        _display_personas(personas)
        return 0
    except Exception as e:
        print(f"[❌] Persona listing failed: {e}")
        return 1


def _parse_list_args(argv: list[str]) -> tuple[str | None, str | None, str | None]:
    """Parse list arguments from argv."""
    member_name = None
    skills_filter = None
    role_filter = None

    # Check if first arg is a member name (doesn't start with --)
    if argv and not argv[0].startswith("--"):
        member_name = argv[0]
        argv = argv[1:]

    i = 0
    while i < len(argv):
        if argv[i] == "--skills" and i + 1 < len(argv):
            skills_filter = argv[i + 1]
            i += 2
        elif argv[i] == "--role" and i + 1 < len(argv):
            role_filter = argv[i + 1]
            i += 2
        else:
            i += 1

    return member_name, skills_filter, role_filter


def _list_personas(
    member_name: str | None, skills_filter: str | None, role_filter: str | None
) -> list[dict[str, str]]:
    """List personas with optional filters (stub implementation)."""
    # In real implementation, would:
    # - Load persona data from storage
    # - Apply filters for skills and role
    # - Return matching persona objects
    raise NotImplementedError("Persona listing not implemented - configure persona storage system")


def _display_personas(personas: list[dict[str, str]]) -> None:
    """Display personas in a formatted way (stub implementation)."""
    # In real implementation, would:
    # - Format persona data in columns or cards
    # - Show skills, availability, performance metrics
    # - Provide summary statistics
    raise NotImplementedError("Persona display not implemented - configure persona formatting")
