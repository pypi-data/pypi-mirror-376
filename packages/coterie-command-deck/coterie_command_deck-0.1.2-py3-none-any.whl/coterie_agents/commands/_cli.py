from __future__ import annotations

from collections.abc import Iterable
from typing import Any

HELP_FLAGS = ("-h", "--help")


def wants_help(argv: Iterable[str] | None) -> bool:
    if not argv:
        return False
    return any(a in HELP_FLAGS for a in argv)


def print_help(command: str, description: str, usage: str | None = None) -> None:
    print(f"Help for '{command}':")
    if description:
        print(description)
    if usage:
        print("Usage:")
        print(usage)


def has_unknown_flags(argv: Iterable[str] | None, known: set[str]) -> bool:
    if not argv:
        return False
    return any(a.startswith("-") and a not in known for a in argv)


def safe_ctx_store(ctx: Any) -> dict[str, Any]:
    # Accept SimpleNamespace or dict; prefer ctx["store"] if present
    if isinstance(ctx, dict):
        if isinstance(ctx.get("store"), dict):
            return ctx["store"]
        return ctx
    # SimpleNamespace or other objects
    store = getattr(ctx, "store", None)
    return store if isinstance(store, dict) else {}
