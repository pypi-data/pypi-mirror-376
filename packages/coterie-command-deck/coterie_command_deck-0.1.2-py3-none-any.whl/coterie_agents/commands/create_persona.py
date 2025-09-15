"""Manage crew member personas and profiles (DRY-RUN by default)."""

from __future__ import annotations

import os

from ._cli import has_unknown_flags, print_help, wants_help

COMMAND = "create_persona"
DESCRIPTION = "Create or update crew member personas and profiles."
USAGE = f"{COMMAND} <member_name> [--role <role>] [--skills <skills>] [--availability <schedule>] [--help]"


def run(argv: list[str] | None = None, _ctx: object = None) -> int:
    """CLI entrypoint for create_persona command."""
    argv = argv or []
    known_flags = {"--help", "-h", "--role", "--skills", "--availability"}

    if wants_help(argv):
        print_help(COMMAND, DESCRIPTION, USAGE)
        print("\nExamples:")
        print(f"  {COMMAND} alice --role cleaner --skills 'deep-clean,windows'")
        print(f"  {COMMAND} bob --role runner --availability 'M-F 9-5'")
        print(f"  {COMMAND} carol --role supervisor --skills 'training,quality-check'")
        print("\nNOTE: Runs in DRY-RUN mode unless PERSONAS_ENABLED=true")
        return 0

    if has_unknown_flags(argv, known_flags):
        print("Not found")
        print_help(COMMAND, DESCRIPTION, USAGE)
        return 0

    member_name, role, skills, availability = _parse_persona_args(argv)

    if not member_name:
        print("[ERROR] Member name is required")
        print_help(COMMAND, DESCRIPTION, USAGE)
        return 1

    # Check if personas are enabled
    personas_enabled = os.getenv("PERSONAS_ENABLED", "false").lower() == "true"

    if not personas_enabled:
        print("[DRY-RUN] Would create/update persona:")
        print(f"  Member: {member_name}")
        if role:
            print(f"  Role: {role}")
        if skills:
            print(f"  Skills: {skills}")
        if availability:
            print(f"  Availability: {availability}")
        print("  (Set PERSONAS_ENABLED=true to manage real personas)")
        return 0

    # Real persona management would go here
    try:
        _create_persona(member_name, role, skills, availability)
        print(f"[✅] Persona created/updated for {member_name}")
        return 0
    except Exception as e:
        print(f"[❌] Persona creation failed: {e}")
        return 1


def _parse_persona_args(
    argv: list[str],
) -> tuple[str | None, str | None, str | None, str | None]:
    """Parse persona arguments from argv."""
    if not argv:
        return None, None, None, None

    member_name = argv[0]
    role = None
    skills = None
    availability = None

    i = 1
    while i < len(argv):
        if argv[i] == "--role" and i + 1 < len(argv):
            role = argv[i + 1]
            i += 2
        elif argv[i] == "--skills" and i + 1 < len(argv):
            skills = argv[i + 1]
            i += 2
        elif argv[i] == "--availability" and i + 1 < len(argv):
            availability = argv[i + 1]
            i += 2
        else:
            i += 1

    return member_name, role, skills, availability


def _create_persona(
    member_name: str, role: str | None, skills: str | None, availability: str | None
) -> None:
    """Create or update persona (stub implementation)."""
    # In real implementation, would:
    # - Store persona data in database or JSON file
    # - Update crew_status.json with new attributes
    # - Generate skill matrices and availability calendars
    # - Set up role-based task assignment preferences
    # - Create performance tracking baselines
    raise NotImplementedError(
        "Persona management not implemented - configure persona storage system"
    )
