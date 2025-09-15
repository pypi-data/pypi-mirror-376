from __future__ import annotations

from typing import Any

__all__ = ["handle_command", "main"]


from coterie_agents import command_router
from coterie_agents.logging_config import configure as configure_logging
from coterie_agents.runtime_guard import configure_deprecation_handling
from coterie_agents.types import CommandMap
from coterie_agents.utils.helper_funcs import interactive_loop

try:
    from importlib.metadata import version as _version_fn
except Exception:
    _version_fn = None  # type: ignore[assignment]

configure_deprecation_handling()
configure_logging()
router: CommandMap = command_router.COMMANDS


def get_pkg_version(dist: str) -> str:
    """Return installed package version or 'unknown' if unavailable."""
    if _version_fn is None:
        return "unknown"
    try:
        return _version_fn(dist)
    except Exception:
        return "unknown"


def dispatch(cmd: str, args: list[str], context: dict[str, Any]) -> Any:
    """Find and execute a command from the router mapping."""
    func = router.get(cmd)
    if func is None:
        print(f"[ERROR] Unknown command: {cmd}")
        print("[INFO] Type 'help' to see available commands.")
        return None
    return func(args, context)


def handle_command(cmd: str) -> str:
    # narrow import avoids cycles
    from coterie_agents.command_router import route

    return route(cmd)


def main() -> int:
    print("[OK] Command Deck ready. Type 'help' or 'exit'.")
    interactive_loop(handle_command)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
