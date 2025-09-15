"""Audit trail support for command deck operations."""

from __future__ import annotations

from typing import Any

from .authz import resolve_actor, role_of


def audit_fields(cli_override: str | None = None) -> dict[str, str]:
    """Generate audit fields for logging with actor and role information.

    Args:
        cli_override: Optional CLI --as override for actor resolution

    Returns:
        Dictionary with 'actor' and 'role' fields for audit trail
    """
    actor = resolve_actor(cli_override)
    return {
        "actor": actor,
        "role": role_of(actor),
    }


def audit_entry(payload: dict[str, Any], cli_override: str | None = None) -> dict[str, Any]:
    """Create an audit-enhanced entry by merging payload with audit fields.

    Args:
        payload: The base data to be logged/stored
        cli_override: Optional CLI --as override for actor resolution

    Returns:
        Enhanced dictionary with audit fields merged in
    """
    return {**payload, **audit_fields(cli_override)}
