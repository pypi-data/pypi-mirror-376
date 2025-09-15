"""Authorization and role-based access control for coterie command deck."""

from __future__ import annotations

import getpass
import json
import os
from collections.abc import Callable
from functools import wraps
from pathlib import Path
from typing import Any, Literal, TypeVar

Role = Literal["viewer", "tech", "lead", "owner"]
ROLE_ORDER: list[Role] = ["viewer", "tech", "lead", "owner"]

CONFIG_PATHS = [
    Path(os.getcwd()) / "config" / "users.json",
    Path.home() / ".coterie" / "users.json",
]

F = TypeVar("F", bound=Callable[..., Any])


def _load_users() -> dict[str, list[str]]:
    """Load users configuration from available config paths."""
    for p in CONFIG_PATHS:
        if p.exists():
            try:
                with p.open("r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as exc:
                # Config file exists but is invalid, skip and try next path
                print(f"[AUTHZ] Warning: Failed to load {p}: {exc}")
                continue
    return {"owner": [], "lead": [], "tech": [], "viewer": []}


USERS = _load_users()


def resolve_actor(cli_override: str | None = None) -> str:
    """Resolve the current actor from CLI override, environment, or OS user.

    Priority: CLI `--as` override > $DECK_USER > OS user
    """
    return (cli_override or os.getenv("DECK_USER") or getpass.getuser()).lower()


def role_of(user: str) -> Role:
    """Get the role of a user. Returns 'viewer' if not found in any role."""
    for role in ROLE_ORDER[::-1]:  # Check from owner to viewer
        if user in (u.lower() for u in USERS.get(role, [])):
            return role
    return "viewer"


def has_at_least(user: str, required: Role) -> bool:
    """Check if user has at least the required role level."""
    user_role = role_of(user)
    return ROLE_ORDER.index(user_role) >= ROLE_ORDER.index(required)


def require_role(required: Role) -> Callable[[F], F]:
    """Decorator to require a minimum role for command execution."""

    def deco(fn: F) -> F:
        @wraps(fn)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            actor_override = kwargs.pop("_actor", None)
            as_user = kwargs.get("as_user")
            actor = resolve_actor(actor_override or (as_user if isinstance(as_user, str) else None))
            if not has_at_least(actor, required):
                print(f"[AUTHZ] '{actor}' lacks role '{required}'. Command blocked.")
                return 2
            return fn(*args, **kwargs)

        return wrapper  # type: ignore[return-value]

    return deco
